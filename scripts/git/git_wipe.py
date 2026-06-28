#!/usr/bin/env python3
# git_wipe.py — clear the working area: discard all changes (recoverable by default)

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from boxprint import box_top, box_bottom, box_line

def find_git_root():
    current = os.path.abspath(os.getcwd())
    while True:
        if os.path.isdir(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent

def run(cmd, check=True):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        box_line(f"❌ Error: {result.stderr.strip()}")
        box_bottom()
        sys.exit(1)
    return result.stdout

def icon_for(code):
    return {
        "??": "🆕",  # untracked
        "A": "🟢",   # added
        "M": "🟡",   # modified
        "D": "🔴",   # deleted
        "R": "🔵",   # renamed
        "C": "🔵",   # copied
        "U": "⚠️ ",  # unmerged
    }.get(code, "⚪")

def collect_changes():
    """Return a list of (icon, path) for every change in the working area."""
    out = run(["git", "status", "--porcelain"], check=False)
    changes = []
    for line in out.splitlines():
        if not line.strip():
            continue
        xy = line[:2]
        path = line[3:]
        code = "??" if xy == "??" else (xy.replace(" ", "") or "?")[:1]
        changes.append((icon_for(code), path))
    return changes

def main():
    git_root = find_git_root()
    if git_root is None:
        box_top()
        box_line("❌ No .git directory found.")
        box_bottom()
        sys.exit(1)

    RESTORE_FILE = os.path.join(git_root, ".git", ".wipe_restore_sha")
    args = sys.argv[1:]

    if args and args[0] in ("--help", "-h"):
        box_top()
        box_line("gw — clear the working area and remove all changes")
        box_line()
        box_line("   Usage: gw            stash everything (recoverable)")
        box_line("          gw undo       restore the last wipe")
        box_line("          gw --hard     reset --hard + clean (NO recovery)")
        box_line()
        box_line("   Default wipe stashes staged, unstaged and untracked")
        box_line("   files so you can bring them back with 'gw undo'.")
        box_bottom()
        return

    # ── undo ──────────────────────────────────────────────────────────────
    if args and args[0] == "undo":
        box_top()
        try:
            with open(RESTORE_FILE) as f:
                sha = f.read().strip()
        except FileNotFoundError:
            box_line("❌ No wipe to undo — no restore point found.")
            box_bottom()
            sys.exit(1)

        top = run(["git", "rev-parse", "stash@{0}"], check=False).strip()
        if top == sha:
            run(["git", "stash", "pop"])
        else:
            run(["git", "stash", "apply", sha])
            box_line("⚠️   Other stashes exist — applied without dropping.")
        os.remove(RESTORE_FILE)
        box_line(f"↩️ Restored wiped changes from {sha[:7]}")
        box_bottom()
        return

    hard = bool(args) and args[0] in ("--hard", "-H")

    changes = collect_changes()
    if not changes:
        box_top()
        box_line("✨ Working area already clean — nothing to wipe.")
        box_bottom()
        return

    # ── show everything that will be wiped ───────────────────────────────
    box_top()
    box_line(f"🧹 {len(changes)} change{'s' if len(changes) > 1 else ''} in the working area"
             + (" — HARD, no recovery 💥" if hard else ""))
    box_line()
    for icon, path in changes:
        box_line(f"   {icon}  {path}")
    box_line()
    box_line("   These are all the files. Are you sure? y/N")
    box_bottom()

    try:
        choice = input("   > ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        return

    if choice not in ("y", "yes"):
        box_top()
        box_line("🚫 Cancelled — nothing was changed.")
        box_bottom()
        return

    box_top()
    if hard:
        run(["git", "reset", "--hard", "HEAD"])
        run(["git", "clean", "-fd"])
        box_line(f"💥 Wiped {len(changes)} change{'s' if len(changes) > 1 else ''} — gone for good.")
        box_bottom()
        return

    # recoverable: stash tracked + untracked
    run(["git", "stash", "push", "--include-untracked", "-m", "wipe"])
    sha = run(["git", "rev-parse", "stash@{0}"], check=False).strip()
    with open(RESTORE_FILE, "w") as f:
        f.write(sha)

    box_line(f"🧹 Wiped {len(changes)} change{'s' if len(changes) > 1 else ''} — working area clean.")
    box_line()
    box_line("   Run 'gw undo' to bring them back.")
    box_bottom()

if __name__ == "__main__":
    main()
