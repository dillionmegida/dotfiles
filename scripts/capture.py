#!/usr/bin/env python3
import subprocess
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from boxprint import box_top, box_bottom, box_line


def main():
    args = sys.argv[1:]
    
    if not args:
        box_top()
        box_line("❌ Error: No arguments provided")
        box_line()
        box_line("   Usage: capture [-f] <file> <command> [args...]")
        box_bottom()
        sys.exit(1)
    
    force = "-f" in args
    if force:
        args = [arg for arg in args if arg != "-f"]
    
    if len(args) < 2:
        box_top()
        box_line("❌ Error: Missing required arguments")
        box_line()
        box_line("   Usage: capture [-f] <file> <command> [args...]")
        box_bottom()
        sys.exit(1)
    
    output_file = Path(args[0])
    command = args[1:]
    
    if output_file.exists() and not force:
        box_top()
        box_line(f"❌ Error: '{output_file}' already exists")
        box_line()
        box_line("   Run with -f to overwrite")
        box_bottom()
        sys.exit(1)
    
    cmd_str = " ".join(command)
    
    box_top()
    box_line(f"📝 Capturing: {cmd_str}")
    
    try:
        with open(output_file, "w") as f:
            result = subprocess.run(
                ["zsh", "-i", "-c", cmd_str],
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True
            )
        
        file_size = output_file.stat().st_size
        box_line()
        box_line(f"   Output saved to '{output_file}' ({file_size} bytes)")
        box_bottom()
        
        if result.returncode != 0:
            sys.exit(result.returncode)
            
    except FileNotFoundError:
        box_top()
        box_line(f"❌ Error: Command not found: {command[0]}")
        box_bottom()
        sys.exit(127)
    except Exception as e:
        box_top()
        box_line(f"❌ Error: {e}")
        box_bottom()
        sys.exit(1)


if __name__ == "__main__":
    main()
