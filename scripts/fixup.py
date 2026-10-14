#!/usr/bin/env python3
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from boxprint import box_top, box_bottom, box_line


def run(cmd, **kwargs):
    return subprocess.run(cmd, text=True, **kwargs)


def get_commit_sha(n):
    """Resolve HEAD~n to a short sha + subject line."""
    result = run(
        ["git", "log", "-1", "--format=%h %s", f"HEAD~{n}"],
        capture_output=True,
    )
    if result.returncode != 0:
        return None, None
    line = result.stdout.strip()
    sha, _, subject = line.partition(" ")
    return sha, subject


def get_staged_diff_stat():
    result = run(["git", "diff", "--cached", "--stat"], capture_output=True)
    return result.stdout.strip()


def has_staged_changes():
    result = run(["git", "diff", "--cached", "--quiet"])
    return result.returncode != 0


def main():
    args = sys.argv[1:]

    if args and args[0] in ("--help", "-h"):
        box_top()
        box_line("fixup — fixup staged changes into an earlier commit")
        box_line()
        box_line("   Usage: fixup <N> [-y]")
        box_line()
        box_line("   N=1 is the latest commit, N=2 the second-to-last, etc.")
        box_line("   -y    skip the confirmation prompt")
        box_line("   Creates a --fixup commit then autosquashes via rebase.")
        box_bottom()
        return

    yes = "-y" in args
    args = [a for a in args if a != "-y"]

    if not args:
        box_top()
        box_line("❌ Error: No commit offset provided")
        box_line()
        box_line("   Usage: fixup <N>")
        box_line("   N=1 is the latest commit, N=2 is second-to-last, etc.")
        box_bottom()
        sys.exit(1)

    try:
        n = int(args[0])
        if n < 1:
            raise ValueError
    except ValueError:
        box_top()
        box_line(f"❌ Error: '{args[0]}' is not a valid positive integer")
        box_bottom()
        sys.exit(1)

    # N is 1-indexed from the top: N=1 is the latest commit (HEAD),
    # N=2 is the second-to-last (HEAD~1), and so on.
    offset = n - 1

    # 1. Check staging area first
    if not has_staged_changes():
        box_top()
        box_line("❌ Error: No staged changes")
        box_line()
        box_line("   Stage your changes first with 'git add'")
        box_bottom()
        sys.exit(1)

    # 2. Show the staged diff and confirm
    diff_stat = get_staged_diff_stat()
    box_top()
    box_line("📋 Staged changes:")
    box_line()
    for line in diff_stat.splitlines():
        box_line(f"   {line}")
    box_bottom()

    if yes:
        answer = "y"
    else:
        answer = input("Proceed with these changes? [y/N] ").strip().lower()
    if answer != "y":
        box_top()
        box_line("🚫 Aborted — no changes made")
        box_bottom()
        sys.exit(0)

    # 3. Resolve target commit
    sha, subject = get_commit_sha(offset)
    if sha is None:
        box_top()
        box_line(f"❌ Error: Could not resolve commit at position {n}")
        box_line()
        box_line("   Does the repo have that many commits?")
        box_bottom()
        sys.exit(1)

    box_top()
    box_line(f"🎯 Target: N={n} → {sha} {subject}")
    box_bottom()

    # 4. Create the fixup commit
    result = run(["git", "commit", "--fixup", sha])
    if result.returncode != 0:
        box_top()
        box_line("❌ Error: Failed to create fixup commit")
        box_bottom()
        sys.exit(result.returncode)

    # 5. Autosquash rebase — base must be BEFORE the target commit.
    # After the fixup commit lands, HEAD has shifted by 1, so the target
    # (originally HEAD~offset) is now at HEAD~(offset+1). The rebase range
    # needs to start one further back than that so the target is replayed.
    base_n = offset + 2
    check = run(["git", "rev-parse", f"HEAD~{base_n}"], capture_output=True)
    rebase_base = f"HEAD~{base_n}" if check.returncode == 0 else "--root"
    box_top()
    box_line(f"🔁 Running: git rebase -i --autosquash {rebase_base}")
    box_bottom()

    env = os.environ.copy()
    env["GIT_SEQUENCE_EDITOR"] = "true"  # accept the autosquash plan as-is, no editor
    result = run(["git", "rebase", "-i", "--autosquash", rebase_base], env=env)

    box_top()
    if result.returncode == 0:
        box_line(f"✅ Fixup squashed into {sha} {subject}")
    else:
        box_line("❌ Rebase failed or hit a conflict")
        box_line()
        box_line("   Resolve conflicts, then:")
        box_line("   git rebase --continue")
    box_bottom()

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()