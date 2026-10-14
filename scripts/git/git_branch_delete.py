#!/usr/bin/env python3
# git_branch_delete.py — fuzzy branch delete with soft/hard delete modes

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from boxprint import box_top, box_bottom, box_line


def get_local_branches():
    """Return list of all local branch names."""
    result = subprocess.run(
        ["git", "branch", "--list"],
        capture_output=True, text=True
    )
    return [
        line.strip().lstrip("* ").strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def fuzzy_match_branches(query, branches):
    """Find branches matching query (substring, case-insensitive)."""
    q = query.lower()
    return [b for b in branches if q in b.lower()]


def delete_branch(branch, hard=False):
    """Delete a branch. hard=True uses -D (force), False uses -d (safe)."""
    flag = "-D" if hard else "-d"
    result = subprocess.run(
        ["git", "branch", flag, branch],
        capture_output=True, text=True
    )
    return result.returncode == 0, result.stderr.strip()


def main():
    args = sys.argv[1:]

    if not args or args[0] == "--help":
        box_top()
        box_line("gbd — fuzzy git branch delete")
        box_line()
        box_line("   Usage: gbd [flags] <pattern> [pattern2 ...]")
        box_line()
        box_line("   Flags:")
        box_line("     -h       hard delete (git branch -D, skips merge check)")
        box_line("     -f       force — skip y/N confirmation prompt")
        box_line("     -hf/-fh  hard delete without confirmation")
        box_line()
        box_line("   Patterns are case-insensitive substring matches against")
        box_line("   local branch names. If a pattern matches multiple branches")
        box_line("   you will be notified and asked to confirm each.")
        box_line()
        box_line("   Soft delete (default) uses 'git branch -d' and will refuse")
        box_line("   to delete unmerged branches. Hard delete uses 'git branch -D'.")
        box_bottom()
        return

    # Parse flags
    hard = False
    force = False
    patterns = []

    for a in args:
        if a.startswith("-") and not a.startswith("--"):
            flags = a[1:]
            if "h" in flags:
                hard = True
            if "f" in flags:
                force = True
        else:
            patterns.append(a)

    if not patterns:
        box_top()
        box_line("Usage: gbd [flags] <pattern> [pattern2 ...]")
        box_line("       gbd --help for more info")
        box_bottom()
        return

    all_branches = get_local_branches()

    if not all_branches:
        box_top()
        box_line("No local branches found.")
        box_bottom()
        return

    # Resolve each pattern to a list of branches, collecting (pattern, [branches]) pairs
    resolved = []  # list of (pattern, [branch, ...])
    warned_multi = False

    for pattern in patterns:
        matches = fuzzy_match_branches(pattern, all_branches)

        if not matches:
            box_top()
            box_line(f"🔍 No branches found matching: {pattern}")
            box_bottom()
            continue

        if len(matches) > 1:
            warned_multi = True
            box_top()
            box_line(f"⚠️  Pattern \"{pattern}\" matched {len(matches)} branches:")
            box_line()
            for b in matches:
                box_line(f"   {b}")
            box_line()
            box_line("   Include all of them? y/N")
            box_bottom()

            try:
                choice = input("   > ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print()
                continue

            if choice == "y":
                resolved.append((pattern, matches))
        else:
            resolved.append((pattern, matches))

    # Flatten to unique branches, preserving order
    seen = set()
    to_delete = []
    for _pattern, branches in resolved:
        for b in branches:
            if b not in seen:
                seen.add(b)
                to_delete.append(b)

    if not to_delete:
        return

    delete_type = "hard" if hard else "soft"

    # Confirmation prompt (unless -f)
    if not force:
        box_top()
        box_line(f"🗑️  About to {delete_type} delete {len(to_delete)} branch{'es' if len(to_delete) != 1 else ''}:")
        box_line()
        for b in to_delete:
            box_line(f"   {b}")
        box_line()
        box_line(f"   Are you sure you want to {delete_type} delete? y/N")
        box_bottom()

        try:
            choice = input("   > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return

        if choice != "y":
            box_top()
            box_line("Cancelled.")
            box_bottom()
            return

    # Execute deletions
    succeeded = []
    failed = []

    for branch in to_delete:
        ok, err = delete_branch(branch, hard=hard)
        if ok:
            succeeded.append(branch)
        else:
            failed.append((branch, err))

    if succeeded:
        box_top()
        box_line(f"✅ Deleted ({delete_type}):")
        for b in succeeded:
            box_line(f"   {b}")
        box_bottom()

    if failed:
        box_top()
        box_line("❌ Failed to delete:")
        for b, err in failed:
            box_line(f"   {b}")
            if err:
                box_line(f"      {err}")
        box_bottom()
        sys.exit(1)


if __name__ == "__main__":
    main()
