#!/usr/bin/env python3

import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(__file__))
from boxprint import box_top, box_bottom, box_line


def kill_port(port):
    """Kill process running on the specified port."""
    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            box_top()
            box_line(f"Error: Port must be between 1 and 65535")
            box_bottom()
            sys.exit(1)
    except ValueError:
        box_top()
        box_line(f"Error: '{port}' is not a valid port number")
        box_bottom()
        sys.exit(1)

    result = subprocess.run(
        ['lsof', '-ti', f':{port}'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0 or not result.stdout.strip():
        box_top()
        box_line(f"No process found on port {port}")
        box_bottom()
        return

    pids = result.stdout.strip().split('\n')
    
    box_top()
    box_line(f"Found {len(pids)} process(es) on port {port}")
    for pid in pids:
        box_line(f"  PID: {pid}")
    box_bottom()

    for pid in pids:
        kill_result = subprocess.run(
            ['kill', '-9', pid],
            capture_output=True,
            text=True
        )
        
        if kill_result.returncode != 0:
            box_top()
            box_line(f"Error killing PID {pid}: {kill_result.stderr.strip()}")
            box_bottom()
            sys.exit(1)

    box_top()
    box_line(f"✓ Killed {len(pids)} process(es) on port {port}")
    box_bottom()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        box_top()
        box_line("kp — kill process on a port")
        box_line()
        box_line("Usage: kp <port> [port2] [port3] ...")
        box_line()
        box_line("Examples:")
        box_line("  kp 3000           # Kill process on port 3000")
        box_line("  kp 8080           # Kill process on port 8080")
        box_line("  kp 3000 8080 5173 # Kill processes on multiple ports")
        box_bottom()
        sys.exit(0 if len(sys.argv) > 1 else 1)

    ports = sys.argv[1:]
    for port in ports:
        kill_port(port)


if __name__ == '__main__':
    main()
