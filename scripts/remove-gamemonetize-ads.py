#!/usr/bin/env python3
"""Remove GameMonetize SDK/advertising injections from Cosmic UGS HTML files.

Only script/resource blocks attributable to GameMonetize are removed. The game
runtime, canvas, asset paths, and unrelated game SDKs are left unchanged.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_RE = re.compile(r"(?is)<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>")
SELF_SCRIPT_RE = re.compile(r"(?is)<script\b(?P<attrs>[^>]*)/\s*>")
COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
IFRAME_RE = re.compile(r"(?is)<iframe\b(?P<attrs>[^>]*)>.*?</iframe\s*>")
RESOURCE_RE = re.compile(r"(?is)<(?:link|source|embed|img)\b[^>]*>")
MONETIZATION_CALL_RE = re.compile(r"(?i)\bgmonetize_(?:pause|resume)\s*\(\s*\)\s*;?")
MARKERS = (
    "gamemonetize",
    "gm-sdk-preload",
    "api.gamemonetize.com",
    "st39/sdk",
    "window.sdk_options",
    "sdk_options",
)


def is_monetization_block(value: str) -> bool:
    lower = value.lower()
    return any(marker in lower for marker in MARKERS)


def remove_gamemonetize(html: str) -> tuple[str, int]:
    """Return cleaned HTML and number of removed SDK/resource blocks."""
    removed = 0

    def clean_script(match: re.Match[str]) -> str:
        nonlocal removed
        block = match.group(0)
        if is_monetization_block(match.group("attrs") + "\n" + match.group("body")):
            removed += 1
            return ""
        return block

    html = SCRIPT_RE.sub(clean_script, html)

    def clean_self_script(match: re.Match[str]) -> str:
        nonlocal removed
        if is_monetization_block(match.group(0)):
            removed += 1
            return ""
        return match.group(0)

    html = SELF_SCRIPT_RE.sub(clean_self_script, html)

    def clean_iframe(match: re.Match[str]) -> str:
        nonlocal removed
        if is_monetization_block(match.group("attrs")):
            removed += 1
            return ""
        return match.group(0)

    html = IFRAME_RE.sub(clean_iframe, html)

    def clean_resource(match: re.Match[str]) -> str:
        nonlocal removed
        if is_monetization_block(match.group(0)):
            removed += 1
            return ""
        return match.group(0)

    html = RESOURCE_RE.sub(clean_resource, html)

    def clean_comment(match: re.Match[str]) -> str:
        nonlocal removed
        if is_monetization_block(match.group(0)):
            removed += 1
            return ""
        return match.group(0)

    html = COMMENT_RE.sub(clean_comment, html)
    html, call_count = MONETIZATION_CALL_RE.subn("", html)
    removed += call_count
    return html, removed


def html_files(root: Path):
    if root.is_file():
        if root.suffix.lower() in {".html", ".htm"}:
            yield root
        return
    yield from (p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".html", ".htm"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="HTML file(s) or directory(ies)")
    parser.add_argument("--check", action="store_true", help="fail if a GameMonetize injection remains; do not write files")
    args = parser.parse_args()

    scanned = changed = removed = 0
    offenders = []
    for root in args.paths:
        if not root.exists():
            print(f"Missing path: {root}", file=sys.stderr)
            return 2
        for path in html_files(root):
            scanned += 1
            try:
                before = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                print(f"Skipped non-UTF-8 HTML: {path}", file=sys.stderr)
                continue
            after, count = remove_gamemonetize(before)
            if after != before:
                changed += 1
                removed += count
                if args.check:
                    offenders.append(str(path))
                else:
                    path.write_text(after, encoding="utf-8")
    if args.check and offenders:
        print("GameMonetize injections remain in:", file=sys.stderr)
        print("\n".join(offenders[:100]), file=sys.stderr)
        if len(offenders) > 100:
            print(f"... and {len(offenders) - 100} more", file=sys.stderr)
        return 1
    action = "Audit clean" if args.check else "Cleanup complete"
    print(f"{action}: scanned {scanned} HTML files; " +
          (f"{changed} files still need cleanup." if args.check else
           f"updated {changed} files and removed {removed} ad/SDK blocks."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
