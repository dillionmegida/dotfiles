#!/usr/bin/env python3
# del_branches.py — delete one or more branches, soft (-d) or hard (-D)

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

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def read_stdin_branches():
    """Read branches from stdin if piped or multiline paste."""
    if not sys.stdin.isatty():
        return [l.strip() for l in sys.stdin.read().splitlines() if l.strip()]
    return []

def main():
    git_root = find_git_root()
    if git_root is None:
        box_top()
        box_line("❌ No .git directory found.")
        box_bottom()
        sys.exit(1)

    args = sys.argv[1:]
    hard = False
    branches = []

    for arg in args:
        if arg in ("--hard", "-h"):
            hard = True
        elif arg in ("--soft", "-s"):
            hard = False
        elif not arg.startswith("-"):
            for branch in arg.splitlines():
                for part in branch.split():  # split each line by whitespace too
                    part = part.strip()
                    if part:
                        branches.append(part)

    # also collect from stdin (multiline paste)
    branches += read_stdin_branches()

    # dedupe while preserving order
    seen = set()
    branches = [b for b in branches if not (b in seen or seen.add(b))]

    if not branches:
        box_top()
        box_line("❌ No branches specified.")
        box_line()
        box_line("   Usage: delb [--soft|--hard] branch1 branch2 ...")
        box_bottom()
        sys.exit(1)

    flag = "-D" if hard else "-d"
    mode = "hard 💥" if hard else "soft 🧹"

    current = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()

    box_top()
    box_line(f"🗑️  Deleting {len(branches)} branch{'es' if len(branches) > 1 else ''} ({mode})")
    box_line()

    for branch in branches:
        if branch == current:
            box_line(f"⚠️   {branch} — skipped (current branch)")
            continue

        result = run(["git", "branch", flag, branch])
        if result.returncode == 0:
            box_line(f"✅  {branch}")
        else:
            err = result.stderr.strip()
            if "not fully merged" in err:
                box_line(f"⚠️   {branch} — not fully merged, use --hard to force")
            else:
                box_line(f"❌  {branch} — {err}")

    box_bottom()

if __name__ == "__main__":
    main()