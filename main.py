#!/usr/bin/env python3
"""THE WORLD IN ONE DAY - Friday 20 November 2026.

Runtime entrypoint for make.fun: a pure copy program.

The image itself is drawn at build time by draw.py (Pillow + DejaVu
fonts) and the resulting entry.png is committed in this repo next to
this file. The official grader image does not ship those fonts, so
drawing at runtime would crash there; copying cannot.

This program therefore uses only the Python standard library: it
copies the committed entry.png into the make.fun output directory
(MAKEFUN_OUTPUT_DIR, default /output) as entry.png. The output
directory itself is never deleted; only entry.png inside it is
written.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


def main():
    # Fail loudly if the committed image is missing: a silent empty
    # output would look like success to the grader's file checks.
    if not os.path.isfile(SRC):
        raise FileNotFoundError(
            "committed image not found: entry.png (expected at "
            + SRC
            + "); fix: run draw.py at build time to regenerate "
            "entry.png and commit it next to main.py"
        )
    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "entry.png")
    try:
        shutil.copyfile(SRC, dest)
    except OSError as exc:
        raise OSError(
            "failed to copy entry.png from " + SRC + " to " + dest
            + ": " + str(exc)
        ) from exc


if __name__ == "__main__":
    main()
