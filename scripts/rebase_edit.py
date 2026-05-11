#!/usr/bin/env python3
# rebase_edit.py — interactively rebase and mark the first commit as edit

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

def main():
    git_root = find_git_root()
    if git_root is None:
        box_top()
        box_line("❌ No .git directory found.")
        box_bottom()
        sys.exit(1)

    args = sys.argv[1:]
    n = 2
    if args:
        if not args[0].isdigit():
            box_top()
            box_line(f"❌ Invalid argument: {args[0]}")
            box_line()
            box_line("   Usage: rebase-edit [n]")
            box_line("   n — number of commits to include (default: 2)")
            box_bottom()
            sys.exit(1)
        n = int(args[0])

    # get the first commit message (oldest in the range, which gets marked as edit)
    log_result = subprocess.run(
        ["git", "log", "--format=%s", f"HEAD~{n}..HEAD"],
        capture_output=True, text=True, cwd=git_root
    )
    commits = [line.strip() for line in log_result.stdout.splitlines() if line.strip()]
    first_commit = commits[-1] if commits else None

    box_top()
    box_line(f"✏️ Rebasing HEAD~{n}, marking this commit as edit:")
    if first_commit:
        box_line(f'   "{first_commit}"')
    box_bottom()

    env = os.environ.copy()
    env["GIT_SEQUENCE_EDITOR"] = "sed -i '' '1s/pick/edit/'"

    subprocess.run(
        ["git", "rebase", "-i", f"HEAD~{n}"],
        env=env,
        cwd=git_root
    )

if __name__ == "__main__":
    main()