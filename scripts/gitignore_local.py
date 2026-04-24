#!/usr/bin/env python3
# gitignore_local.py — manage local git ignores via .git/info/exclude

import os
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

def get_exclude_path(git_root):
    return os.path.join(git_root, ".git", "info", "exclude")

def read_entries(exclude_path):
    if not os.path.exists(exclude_path):
        return []
    with open(exclude_path) as f:
        lines = f.read().splitlines()
    return [l for l in lines if l.strip() and not l.startswith("#")]

def list_entries(exclude_path):
    entries = read_entries(exclude_path)
    box_top()
    if not entries:
        box_line("No local ignores set.")
    else:
        box_line("📋 Local ignores (.git/info/exclude):")
        box_line()
        for entry in entries:
            box_line(f"   {entry}")
    box_bottom()

def add_entry(exclude_path, path):
    entries = read_entries(exclude_path)
    if path in entries:
        box_top()
        box_line(f"⚠️  Already ignored: {path}")
        box_bottom()
        return

    with open(exclude_path, "a") as f:
        # ensure file ends with newline before appending
        f.seek(0, 2)
        if f.tell() > 0:
            f.seek(f.tell() - 1)
            last_char = f.read(1)
            if last_char != "\n":
                f.write("\n")
        f.write(f"{path}\n")

    box_top()
    box_line(f"✅  Added to local ignore: {path}")
    box_bottom()

def remove_entry(exclude_path, path):
    entries = read_entries(exclude_path)
    if path not in entries:
        box_top()
        box_line(f"⚠️  Not found in local ignores: {path}")
        box_bottom()
        return

    # rewrite file preserving comments and blank lines, just removing the target
    with open(exclude_path) as f:
        lines = f.readlines()

    with open(exclude_path, "w") as f:
        for line in lines:
            if line.strip() != path:
                f.write(line)
        # ensure trailing newline
        if lines and not lines[-1].endswith("\n"):
            f.write("\n")

    box_top()
    box_line(f"🗑️  Removed from local ignore: {path}")
    box_bottom()

def print_usage():
    box_top()
    box_line("Usage:")
    box_line()
    box_line("   ignore -l          list all local ignores")
    box_line("   ignore <path>      add path to local ignores")
    box_line("   ignore -r <path>   remove path from local ignores")
    box_bottom()

def main():
    git_root = find_git_root()
    if git_root is None:
        box_top()
        box_line("❌ No .git directory found.")
        box_bottom()
        sys.exit(1)

    exclude_path = get_exclude_path(git_root)
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print_usage()
        return

    if args[0] == "-l":
        list_entries(exclude_path)

    elif args[0] == "-r":
        if len(args) < 2:
            box_top()
            box_line("❌ Specify a path to remove. Usage: ignore -r <path>")
            box_bottom()
            sys.exit(1)
        remove_entry(exclude_path, args[1])

    else:
        add_entry(exclude_path, args[0])

if __name__ == "__main__":
    main()