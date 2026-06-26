#!/usr/bin/env python3
# git_add.py — fuzzy git add by filename pattern

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from boxprint import box_top, box_bottom, box_line


def get_changed_files():
    """Return list of files with uncommitted changes (modified, untracked, deleted)."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "-uall"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    files = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        filepath = line[3:].strip('"')
        if " -> " in filepath:
            filepath = filepath.split(" -> ")[-1].strip('"')
        files.append(filepath)
    return files


def find_matches(pattern, files):
    """Find files where pattern is a substring of the basename."""
    pattern_lower = pattern.lower()
    return [f for f in files if pattern_lower in os.path.basename(f).lower()]


def git_add(files):
    result = subprocess.run(["git", "add"] + files, capture_output=True, text=True)
    return result.returncode == 0


def main():
    args = sys.argv[1:]

    if args and args[0] in ("--help", "-h"):
        box_top()
        box_line("ga — fuzzy git add by filename pattern")
        box_line()
        box_line("   Usage: ga <pattern> [pattern2 ...]")
        box_line("          ga .                  add everything")
        box_line()
        box_line("   Matches changed files whose basename contains <pattern>.")
        box_line("   Flags and '.' are passed straight to 'git add'.")
        box_line()
        box_line("   ── git add --help ──")
        box_bottom()
        subprocess.run(["git", "add", "--help"])
        return

    if len(sys.argv) < 2:
        box_top()
        box_line("Usage: ga <pattern> [pattern2 ...]")
        box_line("       ga .         (add everything)")
        box_bottom()
        return

    # Pass through flags and special args directly to git add
    if any(a.startswith("-") or a == "." for a in args):
        subprocess.run(["git", "add"] + args)
        return

    changed_files = get_changed_files()

    if not changed_files:
        box_top()
        box_line("No changed files to add.")
        box_bottom()
        return

    to_add = []

    for pattern in args:
        # If it contains a slash, treat as a direct path
        if "/" in pattern:
            to_add.append(pattern)
            continue

        matches = find_matches(pattern, changed_files)

        if not matches:
            box_top()
            box_line(f"🔍 No changed files matching: {pattern}")
            box_bottom()
            continue

        if len(matches) == 1:
            to_add.append(matches[0])
            continue

        # Multiple matches — prompt
        box_top()
        box_line(f"🔍 {len(matches)} matches for \"{pattern}\":")
        box_line()
        for f in matches:
            box_line(f"   {f}")
        box_line()
        box_line("   Add all? y/N")
        box_bottom()

        try:
            choice = input("   > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            continue

        if choice == "y":
            to_add.extend(matches)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for f in to_add:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    to_add = unique

    if not to_add:
        return

    if git_add(to_add):
        box_top()
        box_line("✅ Added:")
        for f in to_add:
            box_line(f"   {f}")
        box_bottom()
    else:
        box_top()
        box_line("❌ git add failed")
        box_bottom()
        sys.exit(1)


if __name__ == "__main__":
    main()
