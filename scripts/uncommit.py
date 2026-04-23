#!/usr/bin/env python3
# uncommit.py — soft-undo N commits, with optional undo

import os
import subprocess
import sys

def find_git_root():
    current = os.path.abspath(os.getcwd())
    while True:
        if os.path.isdir(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:  # reached filesystem root
            return None
        current = parent

def run(cmd, check=True):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Error: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    git_root = find_git_root()
    if git_root is None:
        print("❌ No .git directory found.")
        sys.exit(1)

    STASH_REF_FILE = os.path.join(git_root, ".git", ".uncommit_restore_sha")

    args = sys.argv[1:]

    if args and args[0] == "undo":
        try:
            with open(STASH_REF_FILE) as f:
                sha = f.read().strip()
        except FileNotFoundError:
            print("❌ No uncommit to undo — no restore point found.")
            sys.exit(1)

        run(["git", "reset", "--soft", sha])
        print(f"↩️  Undid uncommit — restored to {sha[:7]}")
        os.remove(STASH_REF_FILE)
        return

    n = 1
    if args:
        try:
            n = int(args[0])
            if n < 1:
                raise ValueError
        except ValueError:
            print(f"❌ Invalid number: {args[0]}")
            sys.exit(1)

    current_sha = run(["git", "rev-parse", "HEAD"])
    commit_msg = run(["git", "log", "-1", "--format=%s", current_sha])
    commit_author = run(["git", "log", "-1", "--format=%an", current_sha])
    commit_date = run(["git", "log", "-1", "--format=%ar", current_sha])
    changed_files = run(["git", "diff-tree", "--no-commit-id", "-r", "--name-status", current_sha])

    with open(STASH_REF_FILE, "w") as f:
        f.write(current_sha)

    run(["git", "reset", "--soft", f"HEAD~{n}"])

    print(f"↩️  Uncommitted {n} commit{'s' if n > 1 else ''}:\n")
    print(f"   {current_sha[:7]}  {commit_msg}")
    print(f"   {commit_author} · {commit_date}\n")
    if changed_files:
        for line in changed_files.splitlines():
            status, _, filename = line.partition("\t")
            icon = {"A": "🟢", "M": "🟡", "D": "🔴"}.get(status, "⚪")
            print(f"   {icon}  {filename}")
    print(f"\n   Run 'uncommit undo' to undo this.")

if __name__ == "__main__":
    main()