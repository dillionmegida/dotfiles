#!/usr/bin/env python3
# timer.py — wraps any command and prints elapsed time at the end

import subprocess
import sys
import time

def format_duration(seconds):
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.2f}s"

def main():
    if len(sys.argv) < 2:
        print("Usage: timer <command> [args...]")
        sys.exit(1)

    cmd = sys.argv[1:]
    start = time.perf_counter()

    result = subprocess.run(cmd)

    elapsed = time.perf_counter() - start
    print(f"\n⏱  Finished in {format_duration(elapsed)}")
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()