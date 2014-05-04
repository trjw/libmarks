#!/usr/bin/env python

import os
import fnmatch
import py_compile


def compile(source_dir, dest_dir):
    for root, dirs, files in os.walk(source_dir):
        # Get path to file, relative to source_dir
        curr_dir = os.path.relpath(root, source_dir)
        if curr_dir == '.':
            curr_dir = ''

        # Compile all py files and put them in dest_dir
        py_files = fnmatch.filter(files, '*.py')
        for f in py_files:
            py_compile.compile(
                os.path.join(root, f),
                os.path.join(dest_dir, curr_dir, f + 'c'))

        # Create all dirs within dest_dir
        for d in dirs:
            os.mkdir(os.path.join(dest_dir, curr_dir, d))


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        sys.exit("Usage: compile_py.py source_dir dest_dir")

    source_dir = sys.argv[1]
    dest_dir = sys.argv[2]
    compile(source_dir, dest_dir)
