#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from boxprint import box_bottom, box_line, box_top

VALID_ENVIRONMENTS = {"beta", "test", "live"}


def print_usage():
    box_top()
    box_line("dbc — connect to a Postgres database replica")
    box_line()
    box_line("Usage: dbc <db-name> <beta|test|live>")
    box_bottom()


def print_error(message):
    box_top()
    box_line(f"dbc: {message}")
    box_line()
    box_line("Usage: dbc <db-name> <beta|test|live>")
    box_bottom()


def build_command(db_name, environment):
    return [
        "db-connect",
        "--engine=pg",
        f"--environment={environment}",
        "--connection-type=replica",
        "--region=eu",
        f"--name={db_name}",
        "--dc=eu",
        "--use-vault=no",
    ]


def dbc(db_name, environment):
    if environment not in VALID_ENVIRONMENTS:
        print_error(f"invalid environment: {environment}")
        return 1

    if not sys.stdin.isatty():
        print_error("requires an interactive terminal because db-connect may prompt for your password")
        return 1

    if shutil.which("db-connect") is None:
        print_error("db-connect was not found in PATH")
        return 127

    box_top()
    box_line(f"Connecting to {db_name} in {environment}. You may be prompted for your password.")
    box_bottom()

    return subprocess.run(build_command(db_name, environment)).returncode


def main():
    args = sys.argv[1:]

    if len(args) == 1 and args[0] in ("-h", "--help"):
        print_usage()
        return 0

    if len(args) != 2:
        print_usage()
        return 1

    return dbc(args[0], args[1])


if __name__ == "__main__":
    sys.exit(main())
