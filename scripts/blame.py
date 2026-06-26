#!/usr/bin/env python3
# blame.py — open a file's blame view on GitLab, optionally at a line

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from boxprint import box_top, box_bottom, box_line
from lab import (
    load_meta,
    find_git_root,
    get_repo_from_remote,
    get_default_branch,
    open_url,
)


def error(msg):
    box_top()
    box_line(f"❌  {msg}")
    box_bottom()
    sys.exit(1)


def current_branch():
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True
    )
    branch = result.stdout.strip()
    if result.returncode != 0 or not branch or branch == "HEAD":
        return None
    return branch


def split_line(target, line):
    """Allow file:line or file#line as a single token."""
    if line is not None:
        return target, line
    for sep in (":", "#"):
        head, found, tail = target.rpartition(sep)
        if found and tail.isdigit() and head:
            return head, tail
    return target, None


def main():
    args = sys.argv[1:]

    if any(a in ("--help", "-h") for a in args):
        box_top()
        box_line("blame — open a file's blame on GitLab")
        box_line()
        box_line("   Usage: blame [repo] <file>[:line] [line]")
        box_line()
        box_line("   repo aliases & base_url come from $LAB_META (JSON).")
        box_line("   Defaults to the origin remote and the current branch.")
        box_line("   line anchors to that line in the blame view.")
        box_bottom()
        return

    base_url, repo_map, _ = load_meta()
    if not base_url:
        error("LAB_META is not set or invalid. Add it to your .zshrc.")

    repo = None
    if args and args[0] in repo_map:
        repo = repo_map[args[0]]
        args = args[1:]

    if not args:
        error("Usage: blame [repo] <file>[:line] [line]")

    target = args[0]
    line = args[1] if len(args) > 1 else None
    if line is not None and not str(line).isdigit():
        error(f"Line must be a number: {line}")

    target, line = split_line(target, line)

    if not repo:
        repo = get_repo_from_remote()
    if not repo:
        error("No repo specified and no git remote found.")

    git_root = find_git_root()
    if not git_root:
        error("Not inside a git repo.")

    branch = current_branch() or get_default_branch()

    abs_path = os.path.abspath(os.path.expanduser(target))
    relative = os.path.relpath(abs_path, git_root)
    if relative.startswith(".."):
        error(f"Path is not inside the repo: {target}")

    on_disk = os.path.exists(abs_path)
    in_branch = subprocess.run(
        ["git", "cat-file", "-e", f"{branch}:{relative}"],
        capture_output=True, cwd=git_root
    ).returncode == 0
    if not on_disk and not in_branch:
        error(f"Path not found on disk or in branch '{branch}': {relative}")

    url = f"{base_url}/{repo}/-/blame/{branch}/{relative}"
    if line:
        url += f"#L{line}"

    box_top()
    box_line(f"🔎 Blame: {relative}" + (f" :{line}" if line else ""))
    box_line(f"   {url}")
    box_bottom()
    open_url(url)


if __name__ == "__main__":
    main()
