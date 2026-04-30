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
    # handles both SSH and HTTPS remote formats
    for pattern in [
        r"gitlab.is.adyen.com[:/](.*?)(?:\.git)?$",
    ]:
        import re
        match = re.search(pattern, remote)
        if match:
            return match.group(1)
    return None

def strip_to_relative(path, repo_root_name):
    """
    Given an absolute path, strip everything up to and including the repo root dir.
    e.g. /Users/dillion/adyen-main/ui/vue/src/Foo.vue -> ui/vue/src/Foo.vue
    """
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
    box_line(f"❌ {msg}")
    box_bottom()
    sys.exit(1)

def main():
    BASE_URL, REPO_MAP, REPO_ROOTS = load_meta()
    if not BASE_URL:
        error("LAB_META is not set or invalid. Add it to your .zshrc.")

    args = sys.argv[1:]

    ignore_check = False
    if "-i" in args:
        ignore_check = True
        args = [a for a in args if a != "-i"]

    repo = None
    branch = None
    filepath = None
    idx = 0

    # resolve repo alias from first arg
    if args and args[0] in REPO_MAP:
        repo = REPO_MAP[args[0]]
        idx += 1

    # resolve repo from git remote if not specified
    if not repo:
        repo = get_repo_from_remote()

    if not repo:
        error("No repo specified and no git remote found.")

    repo_root_name = REPO_ROOTS.get(repo, repo.split("/")[-1])

    # next arg: branch or filepath?
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
        # else treat as filepath below

    if not branch:
        branch = get_default_branch()

    # remaining arg is the filepath
    if idx < len(args):
        filepath = args[idx]

    if not filepath:
        # no path — just open repo root
        url = f"{BASE_URL}/{repo}/-/tree/{branch}"
        box_top()
        box_line("🔗 Opening GitLab")
        box_line(f"   {url}")
        box_bottom()
        open_url(url)
        return

    # -i flag: skip all checks, open exact path as-is
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

    if not os.path.exists(abs_path):
        cwd = os.getcwd()
        if os.path.isabs(filepath):
            error(f"Path does not exist: {abs_path}")
        else:
            error(f"Path does not exist: {cwd}/{filepath}")

    # strip repo root from path
    relative = strip_to_relative(abs_path, repo_root_name)
    if not relative:
        error(f"Path is not inside repo root '{repo_root_name}': {abs_path}")

    url = f"{BASE_URL}/{repo}/-/blob/{branch}/{relative}"
    box_top()
    box_line("🔗 Opening GitLab")
    box_line(f"   {url}")
    box_bottom()
    open_url(url)

if __name__ == "__main__":
    main()