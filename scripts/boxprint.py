# boxprint.py — reusable terminal box printing utilities

import re
import sys

try:
    from wcwidth import wcswidth
except ImportError:
    def wcswidth(s):
        return len(s)

WIDTH = 80

_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001F9FF"
    "\U00002600-\U000027BF"
    "\U0001F000-\U0001FAFF"
    "\U0000231A-\U0000231B"
    "\U000023E9-\U000023F3"
    "\U000023F8-\U000023FA]"
    "[\U0000FE00-\U0000FE0F]?"
)

_VARIATION_SELECTOR_RE = re.compile("[\U0000FE00-\U0000FE0F]")


def visual_len(text):
    stripped = _EMOJI_RE.sub("", text)
    stripped = _VARIATION_SELECTOR_RE.sub("", stripped)
    w = wcswidth(stripped)
    return w if w >= 0 else len(stripped)


def truncate(text, max_visual):
    ellipsis = "..."
    budget = max_visual - visual_len(ellipsis)
    result = []
    used = 0
    for ch in text:
        ch_w = visual_len(ch)
        if used + ch_w > budget:
            break
        result.append(ch)
        used += ch_w
    return "".join(result) + ellipsis


def box_top(width=WIDTH):
    print("+" + "-" * width + "+")
    sys.stdout.flush()


def box_bottom(width=WIDTH):
    print("+" + "-" * width + "+")
    sys.stdout.flush()


def box_line(text="", width=WIDTH):
    max_text = width - 5
    if visual_len(text) > max_text:
        text = truncate(text, max_text)
    print(f"|  {text}\033[{width + 2}G|")
    sys.stdout.flush()


class Box:
    """Context manager for a box block."""
    def __init__(self, width=WIDTH):
        self.width = width

    def __enter__(self):
        box_top(self.width)
        return self

    def __exit__(self, *_):
        box_bottom(self.width)

    def line(self, text=""):
        box_line(text, self.width)


def box_stdin(width=WIDTH):
    box_top(width)
    for line in sys.stdin:
        box_line(line.rstrip("\n"), width)
    box_bottom(width)


if __name__ == "__main__":
    if not sys.stdin.isatty():
        box_stdin()
    elif len(sys.argv) > 1:
        cmd = sys.argv[1]
        msg = " ".join(sys.argv[2:])

        if cmd == "start":
            box_top()
            box_line(msg)
        elif cmd == "end":
            box_line(msg)
            box_bottom()
        elif cmd == "line":
            box_line(msg)
        else:
            # no subcommand, treat all args as message
            msg = " ".join(sys.argv[1:])
            box_top()
            box_line(msg)
            box_bottom()
    else:
        box_top()
        box_line()
        box_bottom()