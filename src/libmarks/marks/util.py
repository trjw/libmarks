import os

# Maximum length for a string representation of an object.
_MAX_LENGTH = 80


def strclass(cls):
    """Generate a class name string, including module path.

    Remove module '__main__' from the ID, as it is not useful in most cases.
    """
    if cls.__module__ == "__main__":
        return cls.__name__
    return f"{cls.__module__}.{cls.__name__}"


def safe_repr(obj, length=None):
    """Safely generate a string representation of an object."""
    if length is None:
        length = _MAX_LENGTH
    try:
        result = repr(obj)
    except Exception:
        result = object.__repr__(obj)
    if len(result) <= length:
        return result
    return result[:length] + " [truncated]..."


# Colours for terminal text
# Based on Termcolor by Konstantin Lepa <konstantin.lepa@gmail.com>

# Copyright (c) 2008-2011 Volvox Development Team
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Author: Konstantin Lepa <konstantin.lepa@gmail.com>

COLOUR_FORMAT = "\033[{0}m{1}"

COLOURS = ("grey", "red", "green", "yellow", "blue", "magenta", "cyan", "white")

BACKGROUND = dict(list(zip(COLOURS, list(range(40, 48)))))

FOREGROUND = dict(list(zip(COLOURS, list(range(30, 38)))))

ATTRIBUTES = dict(
    list(
        zip(
            ("bold", "dark", "", "underline", "blink", "", "reverse", "concealed"),
            list(range(1, 9)),
        )
    )
)
del ATTRIBUTES[""]

RESET = "\033[0m"


def coloured_text(text, colour=None, background=None, attrs=None):
    """Add ANSI colours and attributes to text.

    Available foreground and background colors:
        red, green, yellow, blue, magenta, cyan, white.

    Available attributes:
        bold, dark, underline, blink, reverse, concealed.
    """
    if os.getenv("ANSI_COLORS_DISABLED") is None:
        if colour is not None:
            # Add foreground colour to the text.
            text = COLOUR_FORMAT.format(FOREGROUND[colour], text)

        if background is not None:
            # Add background colour to the text.
            text = COLOUR_FORMAT.format(BACKGROUND[background], text)

        if attrs is not None:
            # Add attributes to the text.
            for attr in attrs:
                text = COLOUR_FORMAT.format(ATTRIBUTES[attr], text)

        # Set the text back to normal.
        text += RESET
    return text
