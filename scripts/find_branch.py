#!/usr/bin/env python3
# find_branch.py — fuzzy find local git branches by name

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
    if not args:
        box_top()
        box_line("❌ No search term provided.")
        box_line()
        box_line("   Usage: gfb <search>")
        box_bottom()
        sys.exit(1)

    query = args[0]

    result = subprocess.run(
        ["git", "branch", "--list", f"*{query}*"],
        capture_output=True, text=True
    )

    branches = [
        line.strip().lstrip("* ").strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    box_top()
    if not branches:
        box_line(f"🔍 No branches found matching: {query}")
        box_bottom()
        return

    if len(branches) == 1:
        branch = branches[0]
        box_line(f"🔍 Found one branch: {branch}")
        box_line()
        box_line(f"   Running checkout...")
        box_bottom()
        subprocess.run(["git", "checkout", branch])
        return

    box_line(f"🔍 {len(branches)} branches matching \"{query}\":")
    box_line()
    for branch in branches:
        box_line(f"   {branch}")
    box_bottom()

if __name__ == "__main__":
    main()