#!/usr/bin/env python3
# stale-branches.py
# Finds (and optionally deletes) local branches whose changes are already in master.
# -c/--cherry     uses git cherry (fast, but misses branches where files drifted after landing)
# -l/--long       uses stripped diff hashing (context-independent, survives rebase bots)
# -r/--no-remote  lists all local branches with no upstream tracking ref set

import hashlib
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))
from boxprint import box_top, box_bottom, box_line

BATCH_SIZE = 50


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


# ── diff hashing ─────────────────────────────────────────────────────────────

def get_stripped_diff_hash(sha):
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
            if current_file and current_lines:
                content = current_file + "\n" + "\n".join(current_lines)
                file_hashes.add(hashlib.sha256(content.encode()).hexdigest())
            current_file = line
            current_lines = []
        elif line.startswith(("--- ", "+++ ")):
            continue
        elif line.startswith("+") or line.startswith("-"):
            current_lines.append(line)

    if current_file and current_lines:
        content = current_file + "\n" + "\n".join(current_lines)
        file_hashes.add(hashlib.sha256(content.encode()).hexdigest())

    return frozenset(file_hashes)


def get_diff_hashes_for_shas(shas):
    if not shas:
        return set()

    result = set()
    for i in range(0, len(shas), BATCH_SIZE):
        batch = shas[i:i + BATCH_SIZE]
        for sha in batch:
            h = get_stripped_diff_hash(sha)
            if h:
                result.add(h)
    return result


# ── modes ────────────────────────────────────────────────────────────────────

def check_branch_cherry(branch, main_branch):
    result = run(["git", "cherry", main_branch, branch])
    unpicked = sum(1 for line in result.stdout.splitlines() if line.startswith("+"))
    return branch, unpicked == 0


def build_master_diff_hashes(main_branch, since, author):
    log = run([
        "git", "log", "--format=%H",
        f"--since={since}",
        f"--author={author}",
        f"origin/{main_branch}"
    ])
    shas = log.stdout.strip().splitlines()
    return shas, get_diff_hashes_for_shas(shas)


def get_branch_diff_hashes(branch, main_branch):
    log = run([
        "git", "log", "--format=%H", "--no-merges",
        branch, f"^origin/{main_branch}"
    ])
    shas = log.stdout.strip().splitlines()
    return shas, get_diff_hashes_for_shas(shas)


def check_branch_long(branch, main_branch, master_diff_hashes, verbose):
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
    start = time.perf_counter()

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
        elif arg in ("--show", "-s"):
            delete = False
        elif arg in ("--cherry", "-c"):
            mode = "cherry"
        elif arg in ("--long", "-l"):
            mode = "long"
        elif arg in ("--no-remote", "-r"):
            mode = "no-remote"
        elif arg in ("--verbose", "-v"):
            verbose = True
        elif arg in ("--help", "-h"):
            print("Usage: python stale-branches.py [main-branch] -c|-l|-r [-s|-d] [-v]")
            print()
            print("  main-branch         Branch to compare against (default: master)")
            print("  -c, --cherry        Fast check using git cherry")
            print("  -l, --long          Accurate check using stripped diff hashing")
            print("  -r, --no-remote     List branches with no upstream tracking ref")
            print("  -s, --show          Show matching branches (default)")
            print("  -d, --delete        Delete the matching branches")
            print("  -v, --verbose       Print progress for each branch")
            print()
            print("Examples:")
            print("  python stale-branches.py -c")
            print("  python stale-branches.py -l -v")
            print("  python stale-branches.py main -l -d")
            print("  python stale-branches.py -r")
            print("  python stale-branches.py -r -d")
            sys.exit(0)
        else:
            main_branch = arg

    if mode is None:
        print("Please specify a mode: -c/--cherry, -l/--long, or -r/--no-remote")
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
        if verbose:
            for branch in branches:
                box_line(f"🔎 Checking {branch}")
                _, landed = check_branch_cherry(branch, main_branch)
                if landed:
                    found += 1
                    if delete:
                        run(["git", "branch", "-D", branch])
                        box_line(f"🗑️  Deleted: {branch}")
                    else:
                        box_line(f"✅  {branch}")
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(check_branch_cherry, b, main_branch): b
                    for b in branches
                }
                for future in as_completed(futures):
                    branch, landed = future.result()
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
                futures = {
                    executor.submit(check_branch_long, b, main_branch, master_diff_hashes, False): b
                    for b in branches
                }
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
            if result.returncode != 0:
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
        box_line("Run with -d/--delete to remove these branches.")

    elapsed = time.perf_counter() - start
    mins = int(elapsed // 60)
    secs = elapsed % 60
    duration = f"{mins}m {secs:.2f}s" if mins else f"{elapsed:.2f}s"
    box_line("--")
    box_line(f"⏱  Finished in {duration}")
    box_bottom()


if __name__ == "__main__":
    main()