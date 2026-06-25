# boxprint.py — reusable terminal box printing utilities

import re
import shutil
import sys

try:
    from wcwidth import wcswidth
except ImportError:
    def wcswidth(s):
        return len(s)

WIDTH = shutil.get_terminal_size().columns - 2

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

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

def visual_len(text):
    stripped = _ANSI_RE.sub("", text)       # strip ANSI codes first
    stripped = _EMOJI_RE.sub("", stripped)
    stripped = _VARIATION_SELECTOR_RE.sub("", stripped)
    w = wcswidth(stripped)
    return w if w >= 0 else len(stripped)


def detect_indent(text):
    """Return the leading whitespace of a string."""
    return len(text) - len(text.lstrip(" "))


def wrap_text(text, max_visual):
    """
    Wrap text to fit within max_visual characters per line.
    Subsequent lines inherit the indentation of the first line.
    Returns a list of lines.
    """
    if visual_len(text) <= max_visual:
        return [text]

    indent_count = detect_indent(text)
    indent = " " * indent_count

    lines = []
    current_chars = []
    current_len = 0
    first_line = True
    budget = max_visual

    def flush():
        nonlocal current_chars, current_len, first_line, budget
        lines.append("".join(current_chars))
        current_chars = []
        current_len = 0
        if first_line:
            first_line = False
            budget = max_visual - indent_count
            current_chars = list(indent)
            current_len = indent_count

    words = re.split(r'(?<=\S) ', text)
    for word in words:
        space = 1 if (current_chars and current_len > indent_count) else 0
        word_len = visual_len(word)

        if current_len + space + word_len <= budget:
            # fits on current line
            if space:
                current_chars.append(" ")
                current_len += 1
            current_chars.extend(list(word))
            current_len += word_len
        elif word_len > budget:
            # word itself is too long — force break character by character
            if space and current_len > indent_count:
                current_chars.append(" ")
                current_len += 1
            for ch in word:
                ch_w = visual_len(ch)
                if current_len + ch_w > budget:
                    flush()
                current_chars.append(ch)
                current_len += ch_w
        else:
            # word fits but not on current line — wrap to next
            flush()
            current_chars.extend(list(word))
            current_len += word_len

    if current_chars:
        lines.append(indent + "".join(current_chars))

    return lines


def box_top(width=WIDTH):
    print("+" + "-" * width + "+")
    sys.stdout.flush()


def box_bottom(width=WIDTH):
    print("+" + "-" * width + "+")
    sys.stdout.flush()


def box_line(text="", width=WIDTH):
    max_text = width - 5  # account for "|  " prefix and " |" suffix (with ANSI jump)
    lines = wrap_text(text, max_text)
    for line in lines:
        print(f"|  {line}\033[{width + 2}G|")
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
            msg = " ".join(sys.argv[1:])
            box_top()
            box_line(msg)
            box_bottom()
    else:
        box_top()
        box_line()
        box_bottom()