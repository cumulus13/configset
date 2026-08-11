#!/usr/bin/env python3

# File: printer.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-06-29
# Description: Custom Rich & Fallback Printing System
# License: MIT

import traceback
import re
import sys

HAS_MAKE_COLORS = False
HAS_RICH = False
HAS_JSONCOLOR = False
Syntax = None
Console = None
make_colors = None
print_exception = None

# Save Python's real built-in print
__builtin_print__ = print

try:
    from rich.console import Console
    from rich.syntax import Syntax
    from rich import traceback as rich_traceback

    console = Console()  # type: ignore
    print_exception = console.print_exception
    HAS_RICH = True
except:
    try:
        from make_colors import make_colors, print_exception  # type: ignore
        HAS_MAKE_COLORS = True
    except:
        pass

    try:
        # Make sure the pattern is there
        TAG_PATTERN = globals().get("TAG_PATTERN", re.compile(r'\[.*?\]'))
        EMOJI_PATTERN = globals().get("EMOJI_PATTERN", re.compile(r':.*?:'))

        class console:  # type: ignore  
            @staticmethod
            def print(*args, **kwargs):
                cleaned = []
                for arg in args:
                    if isinstance(arg, str):
                        arg = TAG_PATTERN.sub("", arg)
                        arg = EMOJI_PATTERN.sub("", arg)
                    cleaned.append(arg)
                __builtin_print__(*cleaned, **kwargs)

            @staticmethod
            def print_exception(*args, **kwargs):
                if HAS_MAKE_COLORS and make_colors:
                    exc_type, exc_value, exc_tb = sys.exc_info()
                    # Get the traceback as a list of strings
                    tb_list = traceback.format_exception(exc_type, exc_value, exc_tb)
                    for line in tb_list:
                        if line.strip().startswith("File"):
                            print(make_colors(line, 'lc')) 
                        elif line.strip().startswith(exc_type.__name__):  # type: ignore
                            print(make_colors(line.strip(), 'lw', 'r')) 
                        else:
                            print(make_colors(line.strip(), 'b', 'ly')) 
                            
                else:
                    # Or print full exception
                    return traceback.print_exc()
            
            @staticmethod
            def input(message, *args, **kwargs):
                if HAS_MAKE_COLORS and make_colors:
                    message = make_colors(message, *args, **kwargs)

                return input(message)

            def print_json(*args, **kwargs):
                import json
                print(json.dumps(args[0], indent=2) if args else "")

    except:
        if not HAS_MAKE_COLORS: make_colors = lambda text, *args, **kwargs: text
        class console:
            @staticmethod
            def print(*args, **kwargs):
                return __builtin_print__(*args, **kwargs)

            @staticmethod
            def print_exception():
                exc_type, exc_value, exc_tb = sys.exc_info()
                return traceback.print_exception(exc_type, exc_value, exc_tb)

            @staticmethod
            def input(message):
                return input(message)

    class rich_traceback:
        @staticmethod
        def install(*args, **kwargs):
            import traceback, sys
            def excepthook(exc_type, exc_value, tb):
                traceback.print_exception(exc_type, exc_value, tb)
            sys.excepthook = excepthook



# jsoncolor
try:
    from jsoncolor import jprint
    HAS_JSONCOLOR = True
except Exception as e:
    if HAS_RICH:
        from rich import print_json
        jprint = print_json  # type: ignore
    else:
        try:
            def print_json(*args, **kwargs):
                import json
                print(json.dumps(args[0], indent=2) if args else "")
        except:
            jprint = print  # type: ignore


def _print(*args, **kwargs):
    """Safely print using Rich Console or fallback printers without type conflicts."""
    if HAS_RICH:
        return console.print(*args, **kwargs)

    if HAS_MAKE_COLORS and make_colors:
        colored_args = [make_colors(a) if isinstance(a, str) else a for a in args]
        return __builtin_print__(*colored_args, **kwargs)

    return __builtin_print__(*args, **kwargs)
