#!/usr/bin/env python3

import os
import fnmatch
import py_compile


def compile(source_dir, dest_dir):
    for root, dirs, files in os.walk(source_dir):
        # Get path to file, relative to source_dir
        curr_dir = os.path.relpath(root, source_dir)
        if curr_dir == '.':
            curr_dir = ''

        # Ignore hidden directories (starting with .)
        if curr_dir.startswith('.'):
            continue

        # Filter for Python files
        py_files = fnmatch.filter(files, '*.py')
        if len(py_files) == 0:
           continue

        # Directory contains Python files, so create in destination
        try:
            os.mkdir(os.path.join(dest_dir, curr_dir))
        except OSError:
            # Directory already exists
            pass

        # Compile all py files and put them in dest_dir
        for f in py_files:
            py_compile.compile(
                os.path.join(root, f),
                os.path.join(dest_dir, curr_dir, f + 'c'))

        # Create all dirs within dest_dir
        # for d in dirs:
        #    try:
        #        os.mkdir(os.path.join(dest_dir, curr_dir, d))
        #    except OSError:
        #        # Directory already exists
        #        pass


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        sys.exit("Usage: compile_py.py source_dir dest_dir")

    source_dir = sys.argv[1]
    dest_dir = sys.argv[2]
    compile(source_dir, dest_dir)
