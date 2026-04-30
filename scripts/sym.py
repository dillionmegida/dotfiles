#!/usr/bin/env python3
# sym.py — create symlinks, single or multiple

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from boxprint import box_top, box_bottom, box_line
from colors import C


def resolve(path):
    """Convert relative or absolute path to absolute."""
    return os.path.abspath(os.path.expanduser(path))


def create_symlink(target, link):
    """Create a single symlink.
    Returns (status, message).
    status: 'ok' | 'already_linked' | 'already_linked_elsewhere' | 'exists_file' | 'error'
    """
    if not os.path.exists(target):
        return "error", f"Target does not exist: {target}"

    if os.path.islink(link):
        existing = os.readlink(link)
        if existing == target:
            return "already_linked", f"{link} already linked to {target}"
        return "already_linked_elsewhere", f"{link} is linked to {existing}, not {target}"

    if os.path.exists(link):
        return "exists_file", f"{link} exists as a regular file, not a symlink"

    # ensure parent directory exists
    parent = os.path.dirname(link)
    if parent:
        os.makedirs(parent, exist_ok=True)

    os.symlink(target, link)
    return "ok", f"{link} → {target}"


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        box_top()
        box_line("Usage:")
        box_line()
        box_line("   sym [target] [link]")
        box_line("   sym -m [targetDir] [linkDir]")
        box_line()
        box_line("   target/link can be relative or absolute paths.")
        box_line("   -m symlinks every entry in targetDir into linkDir.")
        box_bottom()
        return

    multiple = False
    if args[0] == "-m":
        multiple = True
        args = args[1:]

    if len(args) < 2:
        box_top()
        box_line(C.color("❌ Please provide both target and link.", C.RED))
        box_bottom()
        sys.exit(1)

    target_raw, link_raw = args[0], args[1]
    target = resolve(target_raw)
    link = resolve(link_raw)

    box_top()

    if multiple:
        if not os.path.isdir(target):
            box_line(C.color("❌ Target is not a directory:", C.RED), target)
            box_bottom()
            sys.exit(1)

        if not os.path.exists(link):
            os.makedirs(link, exist_ok=True)

        if not os.path.isdir(link):
            box_line(C.color("❌ Link destination is not a directory:", C.RED), link)
            box_bottom()
            sys.exit(1)

        entries = sorted(os.listdir(target))
        if not entries:
            box_line(C.color("⚠️  Target directory is empty:", C.YELLOW), target)
            box_bottom()
            return

        box_line(C.color(f"🔗 Symlinking {len(entries)} entries:", C.BLUE))
        box_line(C.color(f"   {target} → {link}", C.CYAN))
        box_line()

        ok = skipped = skipped_file = failed = 0

        for entry in entries:
            entry_target = os.path.join(target, entry)
            entry_link = os.path.join(link, entry)
            status, msg = create_symlink(entry_target, entry_link)

            if status == "ok":
                box_line(C.color(f"   ✅  {entry}", C.GREEN))
                ok += 1
            elif status == "already_linked":
                box_line(C.color("   ⚠️  already linked", C.YELLOW))
                skipped += 1
            elif status == "already_linked_elsewhere":
                existing = os.readlink(entry_link)
                box_line(C.color(f"   ⚠️  already linked elsewhere:{entry} (linked elsewhere → {existing})", C.YELLOW))
                skipped += 1
            elif status == "exists_file":
                box_line(C.color(f"   📄  {entry} (exists as regular file, not a symlink)", C.YELLOW))
                skipped_file += 1
            else:
                box_line(C.color(f"   ❌  {entry} — {msg}", C.RED))
                failed += 1

        box_line()
        box_line(f"   {ok} linked · {skipped} skipped · {skipped_file} exist as files · {failed} failed")

    else:
        box_line("🔗 Creating symlink:")
        box_line()
        status, msg = create_symlink(target, link)

        if status == "ok":
            box_line(C.color(f"   ✅  {msg}", C.GREEN))
        elif status == "already_linked":
            box_line(C.color(f"   ⏭️   Already linked: {link} → {target}", C.YELLOW))
        elif status == "already_linked_elsewhere":
            existing = os.readlink(link)
            box_line(C.color(f"   ⚠️   Already linked elsewhere: {link} → {existing}", C.YELLOW))
        elif status == "exists_file":
            box_line(C.color(f"   📄  Exists as regular file, not a symlink: {link}", C.YELLOW))
        else:
            box_line(C.color(f"   ❌  {msg}", C.RED))

    box_bottom()


if __name__ == "__main__":
    main()