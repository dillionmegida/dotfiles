#!/usr/bin/env python3
# stale-branches.py
# Finds (and optionally deletes) local branches whose changes are already in master.
# --cherry     uses git cherry (fast, but misses branches where files drifted after landing)
# --long       uses stripped diff hashing (context-independent, survives rebase bots)
# --no-remote  lists all local branches with no upstream tracking ref set

import hashlib
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from wcwidth import wcswidth
except ImportError:
    def wcswidth(s):
        return len(s)

WIDTH = 80
BATCH_SIZE = 50

_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001F9FF"
    "\U00002600-\U000027BF"
    "\U0001F000-\U0001FAFF"
    "\U0000231A-\U0000231B"
    "\U000023E9-\U000023F3"
    "\U000023F8-\U000023FA]"
    "[\U0000FE00-\U0000FE0F]?"
)

_VARIATION_SELECTOR_RE = re.compile("[\U0000FE00-\U0000FE0F]")


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def emoji_count(text):
    return len(_EMOJI_RE.findall(text))


def visual_len(text):
    stripped = _EMOJI_RE.sub("", text)
    stripped = _VARIATION_SELECTOR_RE.sub("", stripped)  # catch any orphaned variation selectors
    w = wcswidth(stripped)
    return w if w >= 0 else len(stripped)


# ── box helpers ──────────────────────────────────────────────────────────────

def box_top():
    print("+" + "-" * WIDTH + "+")
    sys.stdout.flush()


def box_bottom():
    print("+" + "-" * WIDTH + "+")
    sys.stdout.flush()


def truncate(text, max_visual):
    ellipsis = "..."
    budget = max_visual - visual_len(ellipsis)
    result = []
    used = 0
    for ch in text:
        ch_w = visual_len(ch)
        if used + ch_w > budget:
            break
        result.append(ch)
        used += ch_w
    return "".join(result) + ellipsis


def box_line(text=""):
    max_text = WIDTH - 5
    if visual_len(text) > max_text:
        text = truncate(text, max_text)
    print(f"|  {text}\033[{WIDTH + 2}G|")
    sys.stdout.flush()


# ── diff hashing ─────────────────────────────────────────────────────────────

def get_stripped_diff_hash(sha):
    """
    For a given SHA, extract only the changed lines (+ and -) per file,
    ignoring context lines entirely. Hash filename + changed lines together
    so two commits touching different files don't collide.
    Returns a frozenset of hashes, one per file touched in the commit.
    """
    result = subprocess.run(
        ["git", "show", "--format=", "-p", "--no-color", sha],
        capture_output=True
    )
    raw = result.stdout.decode(errors="replace")

    file_hashes = set()
    current_file = None
    current_lines = []

    for line in raw.splitlines():
        if line.startswith("diff --git "):
            # flush previous file
            if current_file and current_lines:
                content = current_file + "\n" + "\n".join(current_lines)
                file_hashes.add(hashlib.sha256(content.encode()).hexdigest())
            current_file = line
            current_lines = []
        elif line.startswith(("--- ", "+++ ")):
            continue  # skip file headers
        elif line.startswith("+") or line.startswith("-"):
            current_lines.append(line)

    # flush last file
    if current_file and current_lines:
        content = current_file + "\n" + "\n".join(current_lines)
        file_hashes.add(hashlib.sha256(content.encode()).hexdigest())

    return frozenset(file_hashes)


def get_diff_hashes_for_shas(shas):
    """
    Returns a set of frozensets — one frozenset per commit.
    Each frozenset represents the stripped diff fingerprint of that commit.
    """
    if not shas:
        return set()

    result = set()
    for i in range(0, len(shas), BATCH_SIZE):
        batch = shas[i:i + BATCH_SIZE]
        for sha in batch:
            h = get_stripped_diff_hash(sha)
            if h:  # skip empty commits
                result.add(h)
    return result


# ── modes ────────────────────────────────────────────────────────────────────

def check_branch_cherry(branch, main_branch):
    """Uses git cherry — fast but can miss branches where files drifted after landing."""
    result = run(["git", "cherry", main_branch, branch])
    unpicked = sum(1 for line in result.stdout.splitlines() if line.startswith("+"))
    return branch, unpicked == 0


def build_master_diff_hashes(main_branch, since, author):
    """Compute stripped diff hashes for your commits on origin/master in the time window."""
    log = run([
        "git", "log", "--format=%H",
        f"--since={since}",
        f"--author={author}",
        "--no-merges",
        f"origin/{main_branch}"
    ])
    shas = log.stdout.strip().splitlines()
    return shas, get_diff_hashes_for_shas(shas)


def get_branch_diff_hashes(branch, main_branch):
    """Compute stripped diff hashes for commits on the branch not in origin/master."""
    log = run([
        "git", "log", "--format=%H", "--no-merges",
        branch, f"^origin/{main_branch}"
    ])
    shas = log.stdout.strip().splitlines()
    return shas, get_diff_hashes_for_shas(shas)


def check_branch_long(branch, main_branch, master_diff_hashes, verbose):
    """Check if all of the branch's stripped diffs exist in master's diff set."""
    if verbose:
        box_line(f"🔎 Checking {branch}")

    shas, branch_diff_hashes = get_branch_diff_hashes(branch, main_branch)

    if not shas:
        if verbose:
            box_line(f"   ↳ no unique commits, skipping")
        return branch, False

    if not branch_diff_hashes:
        if verbose:
            box_line(f"   ↳ no diffable content, skipping")
        return branch, False

    if verbose:
        box_line(f"   ↳ {len(shas)} commits, {len(branch_diff_hashes)} diff fingerprints")

    landed = branch_diff_hashes.issubset(master_diff_hashes)

    if verbose and not landed:
        box_line(f"   ↳ not fully landed")

    return branch, landed


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    main_branch = "master"
    delete = False
    mode = None
    verbose = False
    since = "1 year ago"
    workers = 8

    for arg in args:
        if arg in ("--delete", "-d"):
            delete = True
        elif arg == "--cherry":
            mode = "cherry"
        elif arg == "--long":
            mode = "long"
        elif arg == "--no-remote":
            mode = "no-remote"
        elif arg in ("--verbose", "-v"):
            verbose = True
        elif arg in ("--help", "-h"):
            print("Usage: python stale-branches.py [main-branch] --cherry|--long|--no-remote [--delete] [--verbose]")
            print()
            print("  main-branch     Branch to compare against (default: master)")
            print("  --cherry        Fast check using git cherry")
            print("  --long          Accurate check using stripped diff hashing")
            print("  --no-remote     List branches with no upstream tracking ref")
            print("  --delete, -d    Actually delete the stale branches")
            print("  --verbose, -v   Print progress for each branch")
            print()
            print("Examples:")
            print("  python stale-branches.py --cherry")
            print("  python stale-branches.py --long --verbose")
            print("  python stale-branches.py main --long --delete")
            print("  python stale-branches.py --no-remote")
            print("  python stale-branches.py --no-remote --delete")
            sys.exit(0)
        else:
            main_branch = arg

    if mode is None:
        print("Please specify a mode: --cherry, --long, or --no-remote")
        print("Run with --help for usage.")
        sys.exit(1)

    current = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    branches = run(["git", "branch", "--format=%(refname:short)"]).stdout.splitlines()
    branches = [b for b in branches if b and b != main_branch and b != current]

    if mode != "no-remote":
        if run(["git", "rev-parse", "--verify", f"origin/{main_branch}"]).returncode != 0:
            print(f"❌ Remote branch 'origin/{main_branch}' not found.")
            sys.exit(1)

    box_top()

    if mode == "cherry":
        mode_label = "git cherry"
    elif mode == "long":
        mode_label = f"stripped diff hashing (since {since})"
    else:
        mode_label = "no remote tracking branch"

    box_line(f"🔍 Checking {len(branches)} branches via {mode_label}...")
    box_line()

    found = 0

    if mode == "cherry":
        for branch in branches:
            if verbose:
                box_line(f"🔎 Checking {branch}")
            _, landed = check_branch_cherry(branch, main_branch)
            if landed:
                found += 1
                if delete:
                    run(["git", "branch", "-D", branch])
                    box_line(f"🗑️  Deleted: {branch}")
                else:
                    box_line(f"✅  {branch}")

    elif mode == "long":
        author = run(["git", "config", "user.name"]).stdout.strip()
        box_line(f"⏳ Indexing {main_branch} commits by {author}...")
        shas, master_diff_hashes = build_master_diff_hashes(main_branch, since, author)
        box_line(f"   {len(shas)} commits → {len(master_diff_hashes)} diff fingerprints")
        box_line()

        # verbose runs sequentially to avoid interleaved output from threads
        if verbose:
            for branch in branches:
                branch, landed = check_branch_long(branch, main_branch, master_diff_hashes, verbose)
                if landed:
                    found += 1
                    if delete:
                        run(["git", "branch", "-D", branch])
                        box_line(f"🗑️  Deleted: {branch}")
                    else:
                        box_line(f"✅  {branch}")
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(check_branch_long, b, main_branch, master_diff_hashes, False): b for b in branches}
                for future in as_completed(futures):
                    branch, landed = future.result()
                    if landed:
                        found += 1
                        if delete:
                            run(["git", "branch", "-D", branch])
                            box_line(f"🗑️  Deleted: {branch}")
                        else:
                            box_line(f"✅  {branch}")

    elif mode == "no-remote":
        for branch in branches:
            result = run(["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"])
            if result.returncode != 0:  # no upstream set
                found += 1
                if delete:
                    run(["git", "branch", "-D", branch])
                    box_line(f"🗑️  Deleted: {branch}")
                else:
                    box_line(f"🔀  {branch}")

    box_line()
    if found == 0:
        box_line("No matching branches found.")
    elif not delete:
        box_line("Run with --delete to remove these branches.")
    box_bottom()


if __name__ == "__main__":
    main()