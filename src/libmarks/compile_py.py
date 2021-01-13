#!/usr/bin/env python3

import os
import fnmatch
import py_compile
import pathlib


def compile(source_dir, dest_dir):

    source_dir = pathlib.Path(source_dir).resolve()
    dest_dir = pathlib.Path(dest_dir).resolve()

    for filepath in source_dir.rglob("*.py"):
        relpath = filepath.relative_to(source_dir)
        reldir = relpath.parent

        (source_dir / reldir).mkdir(exist_ok=True)
        py_compile.compile(str(filepath), str(dest_dir / relpath) + "c")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        sys.exit("Usage: compile_py.py source_dir dest_dir")

    source_dir = sys.argv[1]
    dest_dir = sys.argv[2]
    compile(source_dir, dest_dir)
