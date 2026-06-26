#!/usr/bin/env python3
# help.py — self-documenting cheatsheet of custom dotfiles commands

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from boxprint import box_top, box_bottom, box_line, WIDTH, visual_len
from colors import C

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCRIPT_DIR)
FUNCTIONS = os.path.join(REPO, "functions.zsh")
ZSHRC = os.path.join(REPO, ".zshrc")

DASH = "\u2014"  # em dash

FUNC_RE = re.compile(r"^\s*(?:function\s+)?([\w-]+)\s*(?:\(\))?\s*\{")
ALIAS_RE = re.compile(r"^\s*alias\s+([\w-]+)=(.+)$")
SCRIPT_REF_RE = re.compile(r"scripts/(?:[\w-]+/)?([\w-]+\.py)")
HEADER_RE = re.compile(r"^#\s*[\w.-]+\s*" + DASH + r"\s*(.+)$")
HELP_TITLE_RE = re.compile(r"""box_line\(\s*[a-z]*["']([^"']*""" + DASH + r"""[^"']*)["']""")
USAGE_RE = re.compile(r"""box_line\(\s*[a-z]*["']([^"']*Usage:[^"']*)["']""")


def read_lines(path):
    try:
        with open(path) as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []


_script_cache = {}


def find_script(name):
    if name in _script_cache:
        return _script_cache[name]
    found = None
    for root, _, files in os.walk(SCRIPT_DIR):
        if name in files:
            found = os.path.join(root, name)
            break
    _script_cache[name] = found
    return found


def script_meta(name):
    """Return (description, usage_lines) for a backing python script."""
    path = find_script(name)
    if not path:
        return "", []
    try:
        with open(path) as f:
            text = f.read()
    except OSError:
        return "", []

    desc = ""
    for line in text.splitlines()[:6]:
        m = HEADER_RE.match(line)
        if m:
            desc = m.group(1).strip()
            break
    if not desc:
        m = HELP_TITLE_RE.search(text)
        if m:
            desc = m.group(1).split(DASH, 1)[-1].strip()
    if not desc:
        desc = top_comment_block(text)

    usage = [u.strip() for u in USAGE_RE.findall(text)]
    return desc, usage


def top_comment_block(text):
    """First meaningful line of a script's leading comment block."""
    for line in text.splitlines():
        if line.startswith("#!"):
            continue
        stripped = line.strip()
        if stripped.startswith("#"):
            c = stripped.lstrip("#").strip()
            if c and not re.fullmatch(r"[\w.-]+\.py", c):
                return c
        elif stripped:
            break
    return ""


def leading_comment(lines, idx):
    out = []
    j = idx - 1
    while j >= 0 and lines[j].strip().startswith("#"):
        c = lines[j].strip().lstrip("#").strip()
        if c:
            out.append(c)
        j -= 1
    out.reverse()
    return " ".join(out)


def parse_functions():
    lines = read_lines(FUNCTIONS)
    cmds = []
    for i, line in enumerate(lines):
        m = FUNC_RE.match(line)
        if not m:
            continue
        name = m.group(1)
        backing = None
        for k in range(i + 1, len(lines)):
            body = lines[k]
            if body.strip() == "}" or FUNC_RE.match(body):
                break
            sm = SCRIPT_REF_RE.search(body)
            if sm:
                backing = sm.group(1)
                break
        desc, usage = ("", [])
        if backing:
            desc, usage = script_meta(backing)
        if not desc:
            desc = leading_comment(lines, i)
        cmds.append({
            "name": name, "desc": desc, "usage": usage,
            "backing": backing, "src": f"functions.zsh:{i + 1}",
        })
    return cmds


def parse_aliases():
    lines = read_lines(ZSHRC)
    cmds = []
    for i, line in enumerate(lines):
        m = ALIAS_RE.match(line)
        if not m:
            continue
        name, rest = m.group(1), m.group(2)
        comment = ""
        if " #" in rest:
            rest, comment = rest.split(" #", 1)
            comment = comment.strip()
        value = rest.strip().strip("'\"")
        desc, usage = ("", [])
        sm = SCRIPT_REF_RE.search(value)
        if sm:
            desc, usage = script_meta(sm.group(1))
        if not desc:
            desc = comment or value
        cmds.append({
            "name": name, "desc": desc, "usage": usage,
            "backing": sm.group(1) if sm else None,
            "src": f".zshrc:{i + 1}", "value": value,
        })
    return cmds


def truncate(text, budget):
    if budget <= 1:
        return ""
    if visual_len(text) <= budget:
        return text
    out = ""
    for ch in text:
        if visual_len(out) + 1 >= budget:
            break
        out += ch
    return out.rstrip() + "\u2026"


def render_concise(title, cmds):
    if not cmds:
        return
    box_line(C.color(title, C.BOLD))
    box_line()
    namew = min(max((visual_len(c["name"]) for c in cmds), default=0), 14)
    budget = WIDTH - namew - 7
    for c in cmds:
        name = C.color(c["name"].ljust(namew), C.CYAN)
        desc = C.color(truncate(c["desc"], budget), C.DIM)
        box_line(f"  {name}  {desc}")
    box_line()


def render_long(title, cmds):
    if not cmds:
        return
    box_line(C.color(title, C.BOLD))
    box_line()
    for c in cmds:
        box_line(f"  {C.color(c['name'], C.CYAN)}  {C.color(c['src'], C.DIM)}")
        if c["desc"]:
            box_line(f"     {c['desc']}")
        for u in c.get("usage", []):
            box_line(C.color(f"     {u}", C.DIM))
        box_line()


def main():
    args = sys.argv[1:]

    if any(a in ("--help", "-h") for a in args):
        box_top()
        box_line("help " + DASH + " cheatsheet of your custom commands")
        box_line()
        box_line("   Usage: help [query]      concise list (optional filter)")
        box_line("          help -l [query]   long output with usage & source")
        box_bottom()
        return

    long = "-l" in args
    query = " ".join(a for a in args if a != "-l").strip().lower()

    funcs = parse_functions()
    aliases = parse_aliases()

    if query:
        def keep(c):
            return query in c["name"].lower() or query in c["desc"].lower()
        funcs = [c for c in funcs if keep(c)]
        aliases = [c for c in aliases if keep(c)]

    render = render_long if long else render_concise

    box_top()
    if not funcs and not aliases:
        box_line(f"🔍 No commands matching: {query}")
        box_bottom()
        return
    render("Commands", funcs)
    render("Aliases", aliases)
    if not long:
        box_line(C.color("  help -l   show usage & source", C.DIM))
    box_bottom()


if __name__ == "__main__":
    main()
