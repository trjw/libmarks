#!/usr/bin/env python3
import argparse
import sys


def print_hello_world(args):
    msg = "HELLO world"
    outfile = sys.stdout

    if args.lower:
        msg = msg.lower()
    if args.stderr:
        outfile = sys.stderr

    print(msg, file=outfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tests different aspects of libmarks")
    parser.add_argument(
        "--lower", action="store_true", help="Prints output as lowercase"
    )
    parser.add_argument(
        "--timeout",
        action="store_true",
        help="Makes the program hang indefinitely without printing",
    )
    parser.add_argument(
        "--stderr", action="store_true", help="Prints to stderr instead"
    )
    parser.add_argument(
        "--returncode", type=int, help="Exits with the given code after printing"
    )

    args = parser.parse_args()
    if args.timeout:
        while True:
            continue

    print_hello_world(args)
    exit(args.returncode)