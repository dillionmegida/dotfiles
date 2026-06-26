#!/usr/bin/env python3
# uncommit.py — soft-undo N commits, with optional undo

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
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
    return result.stdout.strip()

def main():
    git_root = find_git_root()
    if git_root is None:
        box_top()
        box_line("❌ No .git directory found.")
        box_bottom()
        sys.exit(1)

    STASH_REF_FILE = os.path.join(git_root, ".git", ".uncommit_restore_sha")

    args = sys.argv[1:]

    if args and args[0] in ("--help", "-h"):
        box_top()
        box_line("uncommit — soft-undo the last N commits")
        box_line()
        box_line("   Usage: uncommit [N]      undo N commits (default: 1)")
        box_line("          uncommit undo     restore the last uncommit")
        box_bottom()
        return

    box_top()

    if args and args[0] == "undo":
        try:
            with open(STASH_REF_FILE) as f:
                sha = f.read().strip()
        except FileNotFoundError:
            box_line("❌ No uncommit to undo — no restore point found.")
            box_bottom()
            sys.exit(1)

        run(["git", "reset", "--soft", sha])
        box_line(f"↩️ Undid uncommit — restored to {sha[:7]}")
        box_bottom()
        os.remove(STASH_REF_FILE)
        return

    n = 1
    if args:
        try:
            n = int(args[0])
            if n < 1:
                raise ValueError
        except ValueError:
            box_line(f"❌ Invalid number: {args[0]}")
            box_bottom()
            sys.exit(1)

    current_sha = run(["git", "rev-parse", "HEAD"])
    commit_msg = run(["git", "log", "-1", "--format=%s", current_sha])
    commit_author = run(["git", "log", "-1", "--format=%an", current_sha])
    commit_date = run(["git", "log", "-1", "--format=%ar", current_sha])
    changed_files = run(["git", "diff-tree", "--no-commit-id", "-r", "--name-status", current_sha])

    with open(STASH_REF_FILE, "w") as f:
        f.write(current_sha)

    run(["git", "reset", "--soft", f"HEAD~{n}"])

    box_line(f"↩️ Uncommitted {n} commit{'s' if n > 1 else ''}:")
    box_line()
    box_line(f"   {current_sha[:7]}  {commit_msg}")
    box_line(f"   {commit_author} · {commit_date}")
    box_line()
    if changed_files:
        for line in changed_files.splitlines():
            status, _, filename = line.partition("\t")
            icon = {"A": "🟢", "M": "🟡", "D": "🔴"}.get(status, "⚪")
            box_line(f"   {icon}  {filename}")
    box_line()
    box_line("   Run 'uncommit undo' to undo this.")
    box_bottom()

if __name__ == "__main__":
    main()