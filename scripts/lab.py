#!/usr/bin/env python3
# lab.py — open files/paths on GitLab from terminal

import os
import subprocess
import sys, json

sys.path.insert(0, os.path.dirname(__file__))
from boxprint import box_top, box_bottom, box_line

def load_meta():
    raw = os.environ.get("LAB_META")
    if not raw:
        return None, {}, {}
    try:
        data = json.loads(raw)
        base_url = data.get("base_url", "https://gitlab.com")
        repos = data.get("repos", {})
        repo_map = {k: v["repo"] for k, v in repos.items()}
        repo_roots = {v["repo"]: v["root"] for v in repos.values()}
        return base_url, repo_map, repo_roots
    except (json.JSONDecodeError, KeyError):
        return None, {}, {}

def find_git_root():
    current = os.path.abspath(os.getcwd())
    while True:
        if os.path.isdir(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent

def get_default_branch():
    for branch in ("master", "main"):
        result = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
            capture_output=True
        )
        if result.returncode == 0:
            return branch
    return "master"

def get_repo_from_remote():
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    remote = result.stdout.strip()
    for pattern in [
        r"gitlab.is.adyen.com[:/](.*?)(?:\.git)?$",
    ]:
        import re
        match = re.search(pattern, remote)
        if match:
            return match.group(1)
    return None

def strip_to_relative(path, repo_root_name):
    parts = path.split(os.sep)
    try:
        idx = parts.index(repo_root_name)
        return "/".join(parts[idx + 1:])
    except ValueError:
        return None

def open_url(url):
    subprocess.run(["open", url])

def error(msg):
    box_top()
    box_line(f"❌  {msg}")
    box_bottom()
    sys.exit(1)

def is_commit_hash(s):
    import re
    return bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", s))

def search_and_open(query, git_root, repo, branch, base_url):
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True, text=True, cwd=git_root
    )
    if result.returncode != 0:
        error("git ls-files failed.")

    all_files = result.stdout.splitlines()
    matches = [f for f in all_files if query.lower() in f.lower()]

    if not matches:
        box_top()
        box_line(f"🔍 No files found matching: {query}")
        box_bottom()
        return

    if len(matches) == 1:
        url = f"{base_url}/{repo}/-/blob/{branch}/{matches[0]}"
        box_top()
        box_line(f"🔍 Found: {matches[0]}")
        box_line()
        box_line(f"   Opening GitLab...")
        box_line(f"   {url}")
        box_bottom()
        open_url(url)
        return

    box_top()
    box_line(f"🔍 {len(matches)} files matching \"{query}\":")
    box_line()
    for i, f in enumerate(matches, 1):
        box_line(f"   {i:>2}.  {f}")
    box_line()
    box_line("   Enter a number to open, or press Enter to cancel:")
    box_bottom()

    try:
        choice = input("   > ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return

    if not choice:
        return

    if not choice.isdigit() or not (1 <= int(choice) <= len(matches)):
        box_top()
        box_line("❌  Invalid selection.")
        box_bottom()
        sys.exit(1)

    selected = matches[int(choice) - 1]
    url = f"{base_url}/{repo}/-/blob/{branch}/{selected}"
    box_top()
    box_line(f"   Opening: {selected}")
    box_line(f"   {url}")
    box_bottom()
    open_url(url)

def main():
    BASE_URL, REPO_MAP, REPO_ROOTS = load_meta()
    if not BASE_URL:
        error("LAB_META is not set or invalid. Add it to your .zshrc.")

    args = sys.argv[1:]

    ignore_check = False
    search_mode = False

    if "-i" in args:
        ignore_check = True
        args = [a for a in args if a != "-i"]

    if "-s" in args:
        search_mode = True
        args = [a for a in args if a != "-s"]

    repo = None
    branch = None
    filepath = None
    idx = 0

    if args and args[0] in REPO_MAP:
        repo = REPO_MAP[args[0]]
        idx += 1

    if not repo:
        repo = get_repo_from_remote()

    if not repo:
        error("No repo specified and no git remote found.")

    repo_root_name = REPO_ROOTS.get(repo, repo.split("/")[-1])

    if idx < len(args):
        candidate = args[idx]
        ref_check = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{candidate}"],
            capture_output=True
        )
        ref_check2 = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{candidate}"],
            capture_output=True
        )
        if ref_check.returncode == 0 or ref_check2.returncode == 0:
            branch = candidate
            idx += 1

    if not branch:
        branch = get_default_branch()

    if idx < len(args):
        filepath = args[idx]

    # — Commit mode —
    if filepath and is_commit_hash(filepath):
        url = f"{BASE_URL}/{repo}/-/commit/{filepath}"
        box_top()
        box_line(f"🔀 Opening commit: {filepath}")
        box_line(f"   {url}")
        box_bottom()
        open_url(url)
        return

    # — Search mode —
    if search_mode:
        if not filepath:
            error("Usage: lab -s <query>")
        git_root = find_git_root()
        if not git_root:
            error("Not inside a git repo.")
        search_and_open(filepath, git_root, repo, branch, BASE_URL)
        return

    if not filepath:
        url = f"{BASE_URL}/{repo}/-/tree/{branch}"
        box_top()
        box_line("🔗 Opening GitLab")
        box_line(f"   {url}")
        box_bottom()
        open_url(url)
        return

    if ignore_check:
        url = f"{BASE_URL}/{repo}/-/blob/{branch}/{filepath.lstrip('/')}"
        box_top()
        box_line("🔗 Opening GitLab")
        box_line(f"   {url}")
        box_bottom()
        open_url(url)
        return

    # resolve path — absolute or relative
    if os.path.isabs(filepath):
        abs_path = filepath
    else:
        abs_path = os.path.join(os.getcwd(), filepath)

    abs_path = os.path.normpath(abs_path)

    # strip repo root from path
    relative = strip_to_relative(abs_path, repo_root_name)
    if not relative:
        error(f"Path is not inside repo root '{repo_root_name}': {abs_path}")

    # validate against the target branch in git, not the local filesystem
    git_root = find_git_root()
    if not git_root:
        error("Not inside a git repo.")

    check = subprocess.run(
        ["git", "cat-file", "-e", f"{branch}:{relative}"],
        capture_output=True,
        cwd=git_root
    )
    if check.returncode != 0:
        error(f"Path not found in branch '{branch}': {relative}")

    url = f"{BASE_URL}/{repo}/-/blob/{branch}/{relative}"
    box_top()
    box_line("🔗 Opening GitLab")
    box_line(f"   {url}")
    box_bottom()
    open_url(url)

if __name__ == "__main__":
    main()