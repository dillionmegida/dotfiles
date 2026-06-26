#!/usr/bin/env python3
# git_checkout.py — smart git checkout with fuzzy branch matching

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from boxprint import box_top, box_bottom, box_line


def is_exact_ref(arg):
    """Check if arg is an exact branch name or commit hash (local ops only)."""
    # Check local branch
    r = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{arg}"],
        capture_output=True
    )
    if r.returncode == 0:
        return True

    # Check remote branch
    r = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{arg}"],
        capture_output=True
    )
    if r.returncode == 0:
        return True

    # Check commit hash / tag / any valid ref
    r = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", arg],
        capture_output=True
    )
    if r.returncode == 0:
        return True

    return False


def fuzzy_match_branches(query):
    """Find local branches matching the query (substring, case-insensitive)."""
    result = subprocess.run(
        ["git", "branch", "--list", f"*{query}*"],
        capture_output=True, text=True
    )
    return [
        line.strip().lstrip("* ").strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def main():
    args = sys.argv[1:]

    if args and args[0] in ("--help", "-h"):
        box_top()
        box_line("gc — smart git checkout with fuzzy branch matching")
        box_line()
        box_line("   Usage: gc <branch|hash|query>")
        box_line()
        box_line("   Exact refs are checked out directly. Otherwise does a")
        box_line("   case-insensitive substring match on local branches and")
        box_line("   prompts when multiple match. Flags pass through to git.")
        box_line()
        box_line("   ── git checkout --help ──")
        box_bottom()
        subprocess.run(["git", "checkout", "--help"])
        return

    if len(sys.argv) < 2:
        subprocess.run(["git", "checkout"])
        return

    # Pass through if any flags are present (e.g. -b, --, etc.)
    if any(a.startswith("-") for a in args):
        subprocess.run(["git", "checkout"] + args)
        return

    # Multiple args — pass through (e.g. gc branch -- file)
    if len(args) > 1:
        subprocess.run(["git", "checkout"] + args)
        return

    target = args[0]

    # 1. Exact ref — pass straight to git checkout
    if is_exact_ref(target):
        subprocess.run(["git", "checkout", target])
        return

    # 2. Fuzzy branch match
    branches = fuzzy_match_branches(target)

    if not branches:
        box_top()
        box_line(f"🔍 No branches found matching: {target}")
        box_bottom()
        return

    if len(branches) == 1:
        branch = branches[0]
        box_top()
        box_line(f"🔍 Found: {branch}")
        box_bottom()
        subprocess.run(["git", "checkout", branch])
        return

    # Multiple matches — prompt
    box_top()
    box_line(f"🔍 {len(branches)} branches matching \"{target}\":")
    box_line()
    for i, branch in enumerate(branches, 1):
        box_line(f"   {i:>2}.  {branch}")
    box_line()
    box_line("   Enter a number to checkout, or press Enter to cancel:")
    box_bottom()

    try:
        choice = input("   > ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return

    if not choice:
        return

    if not choice.isdigit() or not (1 <= int(choice) <= len(branches)):
        box_top()
        box_line("❌ Invalid selection.")
        box_bottom()
        sys.exit(1)

    selected = branches[int(choice) - 1]
    subprocess.run(["git", "checkout", selected])


if __name__ == "__main__":
    main()
