#!/usr/bin/env python3

# File: logger.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-07-01
# Description: 
# License: MIT

import sys
import os
import traceback
from textwrap import wrap

try:
    from .printer import _print, HAS_MAKE_COLORS, make_colors, HAS_RICH  # type: ignore
except:
    from printer import _print, HAS_MAKE_COLORS, make_colors, HAS_RICH  # type: ignore 

try:
    from . icons import Icons  # type: ignore
except:
    from icons import Icons  # type: ignore 

tprint = None  # type: ignore
print_exception = None  # type: ignore
os.environ['NO_LOGGING'] = "1"
exceptions = [
    "urllib",
    "urllib2",
    "urllib3",
    "comtypes",
    "pika",
    "PIL",
    "requests",
    "chardet",
    "idna",
    "httpcore",
    "httpx",
    "h11",
    "websockets",
    "asyncio",
    "watchdog",
]

LOG_LEVEL = os.getenv('LOG_LEVEL', "CRITICAL")
SHOW_LOG = False
if len(sys.argv) > 1 and any('--debug' == arg for arg in sys.argv[1:]):
    _print("🐞 Debug mode enabled \\[CONFIGSET]")
    os.environ["CONFIGSET_DEBUG"] = "1"
    os.environ['LOGGING'] = "1"
    os.environ.pop('NO_LOGGING', None)
    LOG_LEVEL = "DEBUG"
    SHOW_LOG = True

try:
    if (len(sys.argv) > 1 and any('--pydebugger' == arg for arg in sys.argv[1:])) or os.getenv("PYDEBUGGER", '0').lower() in ('1', 'true', 'ok', 'on', 'yes'):
        _print("[CONFIGSET] debug with'pydebugger' enable")
        from pydebugger.debug import debug as debugx

        if os.getenv("DEBUG_SERVER") == "1":
            def debug(*args, **kwargs):  # type: ignore  
                return debugx(*args, **kwargs)
        else:
            def debug(*args, **kwargs):  # type: ignore
                return debugx(*args, **kwargs, debug = 1)
        
    else:
        def debug(*args, **kwargs):
            pass

    # import richcolorlog
    try:
        from richcolorlog import setup_logging, print_exception as tprint  # type: ignore
        logger = setup_logging('animesail', exceptions=exceptions, level=LOG_LEVEL, show=SHOW_LOG)
    except:
        import logging

        for exc in exceptions:
            logging.getLogger(exc).setLevel(logging.CRITICAL)

        try:
            from .custom_logging import get_logger  # type: ignore
        except:
            from custom_logging import get_logger  # type: ignore

        LOG_LEVEL = getattr(logging, LOG_LEVEL.upper(), logging.CRITICAL)

        logger = get_logger('animesail', level=LOG_LEVEL)

except:
    # traceback.print_exc()
    try:
        if os.getenv('CONFIGSET_DEBUG', "0") in ("1", "yes", "ok", "on"):
            from richcolorlog import setup_logging  # type: ignore
            logger = setup_logging("animesail")
        
            def debug(*args, **kwargs):  # type: ignore
                args = ", ".join(args)
                kwargs = str(kwargs)
                return logger.debug(f"debug: {args}: {kwargs}")
        else:
            def debug(*args, **kwargs):  # type: ignore
                return

    except:
        try:
            import logging

            for exc in exceptions:
                logging.getLogger(exc).setLevel(logging.CRITICAL)

            try:
                from .custom_logging import get_logger  # type: ignore
            except:
                from custom_logging import get_logger

            LOG_LEVEL = getattr(logging, str(LOG_LEVEL).upper(), logging.CRITICAL)

            logger = get_logger('animesail', level=LOG_LEVEL)
        except:
            import logging
            logger = logging.getLogger("Animesail")
            logger.setLevel(getattr(logging, str(LOG_LEVEL).upper(), logging.CRITICAL))
            
            def debug(*args, **kwargs):
                return

if not tprint:
    def tprint(*args, **kwargs):
        traceback.print_exc()

def is_debug():
    os.environ.pop('TRACEBACK', '0')
    return str(os.getenv('CONFIGSET_DEBUG', '0')).lower() in ('1', 'true', 'yes', 'ok')

def is_verbose():
    return any(i for i in sys.argv[1:] if i in ['--verbose', '--debug'])

def set_debug():
    try:
        from pydebugger.debug import debug
    except:
        _print(f"{Icons.BUG} {Icons.ERROR} [bold #FFFF00]please install 'pydebugger' before ![/]")
        def debug(*args, **kwargs):
            return

def print_wrapped_error(prefix_msg, remotename, exception, prefix_len=None):
    """Helper function to print formatted error messages with proper wrapping"""
    if prefix_len is None:
        # Calculate space based on the actual printed length (excluding color codes)
        import re
        clean_prefix = re.sub(r'\[.*?\]', '', prefix_msg)
        prefix_len = len(clean_prefix) + len(remotename) + 7  # 7 for extra chars like ': '

    space = " " * prefix_len
    terminal_width = os.get_terminal_size()[0]
    _error_wrap = wrap(str(exception), terminal_width - prefix_len,
                       initial_indent=space, subsequent_indent=space)
    error = "\n".join(_error_wrap[1:]) if len(_error_wrap) > 1 else ""

    _print(f"{Icons.ERROR} {prefix_msg} '[bold #00FFFF]{remotename}[/]': ", end='')  
    if len(_error_wrap) > 1:
        _print(f"[bold #FF007F]{_error_wrap[0].strip()}[/]")  
    # else:
    #     _print("\n")  
    if error:
        _print(f"[bold #FF007F]{error}[/]")  

def dprint(text):
    if is_debug():
        import inspect
        # Get the caller's stack frame
        caller_frame = inspect.currentframe().f_back  # type: ignore
        filename = caller_frame.f_code.co_filename  # type: ignore
        line_no = caller_frame.f_lineno  # type: ignore

        lines = f"{filename}:{line_no}"

        _print(
          f"[bold #FFAA00]{Icons.BUG}[/] [bold #550000 on #FFAA00]{text}[/] [white on"
          f" blue]\\[{lines}][/]"
        )

if not print_exception:
    if HAS_MAKE_COLORS:
        from make_colors import make_colors  # type: ignore
        def print_exception(*args, **kwargs):
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_list = traceback.format_exception(exc_type, exc_value, exc_tb)
            for line in tb_list:
                if line.strip().startswith("File"):
                    _print(make_colors(line.rstrip(), 'lc'))  
                elif exc_type and line.strip().startswith(exc_type.__name__):
                    _print(make_colors(line.strip(), 'lw', 'r'))  
                else:
                    _print(make_colors(line.strip(), 'b', 'ly'))  
    elif HAS_RICH:
        from rich.console import Console
        console = Console()
        print_exception = console.print_exception
    else:
        def print_exception():
            exc_type, exc_value, exc_tb = sys.exc_info()
            return traceback.print_exception(exc_type, exc_value, exc_tb)
