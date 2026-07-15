#!/usr/bin/env python3
# submit a patch merge request from master commits

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from boxprint import box_bottom, box_line, box_top


def print_help():
    box_top()
    box_line("patch - submit a patch merge request from master commits")
    box_line()
    box_line("   Usage: patch [options] <COMMITS>...")
    box_line()
    box_line("   Arguments:")
    box_line("      <COMMITS>...          one or more hash of commit from master")
    box_line()
    box_line("   Options:")
    box_line("      -p, --previous        sets RELEASE to one older than latest")
    box_line("      -r, --release=<REL>   release identifier, e.g. V1_234")
    box_line("      -h, --help            show this help message and exit")
    box_line("      -v, -V, --version     print version information and exit")
    box_bottom()


def print_error(message):
    box_top()
    box_line(f"patch: {message}")
    box_line()
    box_line("   Usage: patch [options] <COMMITS>...")
    box_line("   Run 'patch -h' for help.")
    box_bottom()


def parse_args(args):
    submit_args = []
    commits = []
    i = 0

    while i < len(args):
        arg = args[i]

        if arg in ("-h", "--help"):
            return "help", []
        if arg in ("-v", "-V", "--version"):
            return "version", ["--version"]
        if arg in ("-p", "--previous"):
            submit_args.append("--previous")
        elif arg in ("-r", "--release"):
            if i + 1 >= len(args) or args[i + 1].startswith("-"):
                raise ValueError(f"missing release value for {arg}")
            submit_args.append(f"--release={args[i + 1]}")
            i += 1
        elif arg.startswith("-r="):
            release = arg.split("=", 1)[1]
            if not release:
                raise ValueError("missing release value for -r")
            submit_args.append(f"--release={release}")
        elif arg.startswith("--release="):
            release = arg.split("=", 1)[1]
            if not release:
                raise ValueError("missing release value for --release")
            submit_args.append(f"--release={release}")
        elif arg.startswith("-"):
            raise ValueError(f"unknown option {arg}")
        else:
            commits.append(arg)

        i += 1

    if not commits:
        raise ValueError("at least one commit hash is required")

    return "submit", submit_args + commits


def run_submit(args):
    try:
        return subprocess.run(["git-mr-submit-patch"] + args).returncode
    except FileNotFoundError:
        print_error("git-mr-submit-patch was not found in PATH")
        return 127


def run_version():
    try:
        proc = subprocess.run(
            ["git-mr-submit-patch", "--version"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print_error("git-mr-submit-patch was not found in PATH")
        return 127

    box_top()
    for line in (proc.stdout + proc.stderr).splitlines():
        if line:
            box_line(line)
    box_bottom()
    return proc.returncode


def main():
    try:
        action, submit_args = parse_args(sys.argv[1:])
    except ValueError as exc:
        print_error(str(exc))
        return 1

    if action == "help":
        print_help()
        return 0

    if action == "version":
        return run_version()

    return run_submit(submit_args)


if __name__ == "__main__":
    sys.exit(main())
