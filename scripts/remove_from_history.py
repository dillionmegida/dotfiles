#!/usr/bin/env python3
import sys
import subprocess
import os
import shlex


def box_call(cmd, msg):
    """Call boxprint.py directly via subprocess."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "boxprint.py")
    if cmd is None:
        full_cmd = [sys.executable, script_path, msg]
    else:
        full_cmd = [sys.executable, script_path, cmd, msg]
    try:
        subprocess.run(full_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Box command failed: {e}", file=sys.stderr)


def run_git(cmd, capture=False, check=True):
    """Run git command, return result."""
    try:
        kwargs = {'check': check}
        if capture:
            kwargs['capture_output'] = True
            kwargs['text'] = True
        result = subprocess.run(['git'] + shlex.split(cmd), **kwargs)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)
        sys.exit(1)


if len(sys.argv) == 2 and sys.argv[1] in ("--help", "-h"):
    box_call('start', "remove-from-history — purge a file from all git history")
    box_call('line', "Usage: remove-from-history <file-path>")
    box_call('line', "Runs filter-branch, expires reflog, and gc's the repo.")
    box_call('end', "⚠️  Rewrites history — requires a force-push afterward.")
    sys.exit(0)


if len(sys.argv) != 2:
    box_call(None, 'Usage: git remove-from-history <file-path>')
    sys.exit(1)


file_path = sys.argv[1]


# Box: Check history
box_call('start', f"Checking if '{file_path}' is in Git history...")
result = run_git(f"log -- '{file_path}'", capture=True, check=False)
if result.returncode != 0:
    box_call('line', f"File '{file_path}' not found in Git history. Nothing to remove.")
    box_call('end')
    sys.exit(1)


# Remove from history
box_call('line', f"Removing '{file_path}' from Git history...")
is_dir = os.path.isdir(file_path)
rm_flags = "-r " if is_dir else " "  # Note: space after flag
cmd = f"""filter-branch --force --index-filter '
  git rm --cached --ignore-unmatch {rm_flags}{shlex.quote(file_path)}
' --prune-empty --tag-name-filter cat -- --all"""
run_git(cmd)


# Clean up
box_call('line', "Cleaning up reflog and garbage...")
run_git("reflog expire --expire=now --all && git gc --prune=now --aggressive")


box_call('end', "✅ Done! Force-push with: git push --force-with-lease --all")