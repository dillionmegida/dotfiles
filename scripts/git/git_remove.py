#!/usr/bin/env python3
# git_remove.py — fuzzy git unstage by filename pattern

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from boxprint import box_top, box_bottom, box_line


def get_staged_files():
    """Return list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.splitlines() if f]


def find_matches(pattern, files):
    """Find files where pattern is a substring of the basename."""
    pattern_lower = pattern.lower()
    return [f for f in files if pattern_lower in os.path.basename(f).lower()]


def git_unstage(files):
    result = subprocess.run(["git", "reset", "HEAD", "--"] + files, capture_output=True, text=True)
    return result.returncode == 0


def main():
    args = sys.argv[1:]

    if args and args[0] in ("--help", "-h"):
        box_top()
        box_line("gr — fuzzy git unstage by filename pattern")
        box_line()
        box_line("   Usage: gr <pattern> [pattern2 ...]")
        box_line("          gr .                  unstage everything")
        box_line()
        box_line("   Matches staged files whose basename contains <pattern>.")
        box_line("   Flags and '.' pass straight to 'git reset HEAD'.")
        box_line()
        box_line("   ── git reset --help ──")
        box_bottom()
        subprocess.run(["git", "reset", "--help"])
        return

    if len(sys.argv) < 2:
        box_top()
        box_line("Usage: gr <pattern> [pattern2 ...]")
        box_line("       gr .         (unstage everything)")
        box_bottom()
        return

    # Pass through special args
    if any(a.startswith("-") or a == "." for a in args):
        subprocess.run(["git", "reset", "HEAD", "--"] + args)
        return

    staged_files = get_staged_files()

    if not staged_files:
        box_top()
        box_line("No staged files to remove.")
        box_bottom()
        return

    to_unstage = []

    for pattern in args:
        if "/" in pattern:
            to_unstage.append(pattern)
            continue

        matches = find_matches(pattern, staged_files)

        if not matches:
            box_top()
            box_line(f"🔍 No staged files matching: {pattern}")
            box_bottom()
            continue

        if len(matches) == 1:
            to_unstage.append(matches[0])
            continue

        # Multiple matches — prompt
        box_top()
        box_line(f"🔍 {len(matches)} matches for \"{pattern}\":")
        box_line()
        for f in matches:
            box_line(f"   {f}")
        box_line()
        box_line("   Remove all from staging? y/N")
        box_bottom()

        try:
            choice = input("   > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            continue

        if choice == "y":
            to_unstage.extend(matches)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for f in to_unstage:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    to_unstage = unique

    if not to_unstage:
        return

    if git_unstage(to_unstage):
        box_top()
        box_line("✅ Unstaged:")
        for f in to_unstage:
            box_line(f"   {f}")
        box_bottom()
    else:
        box_top()
        box_line("❌ git reset failed")
        box_bottom()
        sys.exit(1)


if __name__ == "__main__":
    main()
