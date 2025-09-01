#!/usr/bin/env python
# -*- coding: utf-8 -*-
#author: Hadi Cahyadi <cumulus13@gmail.com>
#license: MIT
#source: https://github.com/cumulus13/configset

"""
Enhanced Configuration Management Library
Provides easy-to-use configuration file handling with INI, JSON, and YAML support.
"""

from __future__ import annotations
import warnings
import inspect
import sys
import argparse
import os
import ast
import traceback
import re
import json
from json import JSONDecoder, JSONDecodeError, JSONEncoder
from collections import deque
import yaml
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from functools import wraps
try:
    from pydebugger.debug import debug
except Exception as e:
    def debug(*args, **kwargs):
        return
# Python 2/3 compatibility
if sys.version_info.major == 2:
    import ConfigParser # type: ignore
    configparser = ConfigParser
else:
    import configparser

try:
    from richcolorlog import setup_logging
    logger = setup_logging(__name__)
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    
from dataclasses import dataclass

# Optional dependencies for enhanced output
HAS_RICH = False
HAS_JSONCOLOR = False
HAS_MAKECOLOR = False
jprint = print
def make_colors(data, *args, **kwargs):
    """Dummy function for make_colors, replace with actual implementation if available."""
    return str(data)  # Just return string representation for now
try:
    from rich import print_json
    from rich.console import Console
    from rich import traceback as rich_traceback # type: ignore
    from rich.syntax import Syntax
    _console = Console() # type: ignore
    HAS_RICH = True
except ImportError:
    # Regex untuk tag [bold], [/bold], [/#], [/], dll
    TAG_PATTERN = re.compile(r"\[(\/?[a-zA-Z0-9#=_\- ]*?)\]")
    # Regex untuk emoji-style :smile:, :rocket:, dll
    EMOJI_PATTERN = re.compile(r":[a-zA-Z0-9_+\-]+:")

    @dataclass
    class _console:
        @staticmethod
        def print(*args, **kwargs):
            cleaned = []
            for arg in args:
                if isinstance(arg, str):
                    arg = TAG_PATTERN.sub("", arg)     # hapus markup [..]
                    arg = EMOJI_PATTERN.sub("", arg)   # hapus emoji :..:
                cleaned.append(arg)
            print(*cleaned, **kwargs)

    def print_json(*args, **kwargs):
        import json
        print(json.dumps(args[0], indent=2) if args else "")

    class rich_traceback:
        @staticmethod
        def install(*args, **kwargs):
            import traceback, sys
            def excepthook(exc_type, exc_value, tb):
                traceback.print_exception(exc_type, exc_value, tb)
            sys.excepthook = excepthook

    HAS_RICH = False
    
    try:
        from jsoncolor import jprint
        HAS_JSONCOLOR = True
    except ImportError:
        HAS_JSONCOLOR = False
        try:
            from make_colors import make_colors
            HAS_MAKECOLOR = True
        except ImportError:
            HAS_MAKECOLOR = False

if HAS_RICH:
    try:
        from licface import CustomRichHelpFormatter
    except:
        CustomRichHelpFormatter = argparse.RawTextHelpFormatter

    # rich_traceback.install(show_locals=False, width=os.get_terminal_size()[0], theme='fruity')
    try:
        try:
            width = os.get_terminal_size()[0]
        except (OSError, ValueError):
            # fallback to shutil.get_terminal_size which supports a fallback param
            import shutil
            width = shutil.get_terminal_size(fallback=(80, 24)).columns
        rich_traceback.install(show_locals=False, width=width, theme='fruity')
    except Exception as e:
        # Do not propagate errors from optional pretty-traceback setup
        pass

def get_version():
    """
    Get the version from __version__.py file.
    The content of __version__.py should be: version = "0.33"
    """
    try:
        version_file = Path(__file__).parent / "__version__.py"
        if version_file.is_file():
            with open(version_file, "r") as f:
                for line in f:
                    if line.strip().startswith("version"):
                        parts = line.split("=")
                        if len(parts) == 2:
                            return parts[1].strip().strip('"').strip("'")
    except Exception as e:
        if os.getenv('TRACEBACK') and os.getenv('TRACEBACK') in ['1', 'true', 'True']:
            _console.print(f":biohazard_sign {traceback.format_exc()}")
        else:
            _console.print(f":cross_mark: [white on red]ERROR:[/] [white on blue]{e}[/]")

    return "0.0.0"

__version__ = get_version()
__platform__ = "all"
__contact__ = "cumulus13@gmail.com"
__author__ = "Hadi Cahyadi"
__all__ = ["ConfigSet", "CONFIG", "MultiOrderedDict", "__version__", "get_version", "ConfigSetIni", "ConfigSetYaml", "ConfigSetJson", "detect_file_type", "_validate_file_path", "ConfigMeta"]

def _debug_enabled() -> bool:
    """
    Check if debug mode is enabled via environment variables.
    The function `_debug_enabled()` checks if debug mode is enabled based on specific environment
    variables.
    :return: The function `_debug_enabled()` returns a boolean value indicating whether debug mode is
    enabled based on the values of the environment variables `DEBUG` and `DEBUG_SERVER`.
    """
    
    # return (os.getenv('DEBUG', '').lower() in ['1', 'true', 'yes'] or os.getenv('DEBUG_SERVER', '').lower() in ['1', 'true', 'yes'])
    return os.getenv('DEBUG', '').lower() in ['1', 'true', 'yes']

SEP_RE = re.compile(r'[.:;|]')

def _flatten_keys(keys) -> List[str]:
    """
    Flatten and split keys by separators. Accepts strings, bytes, lists, tuples.
    The `_flatten_keys` function flattens and splits keys by separators, handling strings, bytes, lists,
    and tuples.
    
    :param keys: The function `_flatten_keys` takes a parameter `keys`, which can be a string, bytes,
    list, or tuple. The function flattens and splits the keys by separators. If the `keys` parameter is
    a list or tuple containing multiple items, it treats each item as a separate key
    :return: The function `_flatten_keys(keys)` returns a list of strings that have been flattened and
    split by separators. The keys can be strings, bytes, lists, or tuples. The function processes the
    input keys, decodes bytes to strings if necessary, splits strings by separators, flattens nested
    lists/tuples, and converts non-string items to strings before returning the final list of segments.
    """
    
    parts: List[str] = []
    # If the caller passed exactly one list/tuple, treat its items as the keys
    if len(keys) == 1 and isinstance(keys[0], (list, tuple)):
        iterable = list(keys[0])
    else:
        iterable = list(keys)

    for item in iterable:
        if item is None:
            continue
        # if item is bytes, decode
        if isinstance(item, bytes):
            item = item.decode('utf-8')
        # For strings: split by separators into segments
        if isinstance(item, str):
            segs = [p for p in SEP_RE.split(item) if p != '']
            if segs:
                parts.extend(segs)
            else:
                # empty string -> skip
                continue
        elif isinstance(item, (list, tuple)):
            # nested list/tuple -> flatten and re-process
            for sub in item:
                if sub is None:
                    continue
                if isinstance(sub, bytes):
                    sub = sub.decode('utf-8')
                if isinstance(sub, str):
                    parts.extend([p for p in SEP_RE.split(sub) if p != ''])
                else:
                    parts.append(str(sub))
        else:
            # fallback: convert to string
            parts.append(str(item))

    return parts
    
def detect_file_type(content: str) -> Any:
    """
    Detect the file type based on content or file extension.
    
    Args:
        content: File path or content string
        
    Returns:
        File type: 'json', 'ini', 'yaml', or False if unable to detect
    """
    if not content:
        return False
    # Strip leading/trailing whitespace
    if os.path.isfile(content):
        # Check file extension first
        ext = Path(content).suffix.lower()
        if ext == '.json':
            return 'json'
        elif ext in ['.yaml', '.yml']:
            return 'yaml'
        elif ext == '.ini':
            return 'ini'
            
        # If extension doesn't help, read content
        # with open(content, 'r') as f:
        #     data = f.read().strip()
        try:
            with open(content, 'r', encoding='utf-8', errors='replace') as f:
                data = f.read().strip()
        except Exception:
            return False
    else:
        data = content.strip()

    # Try JSON detection
    if data.startswith(('{', '[', '"', "'")) or data[:4] in ("true", "null", "fals"):
        try:
            json.loads(data)
            return "json"
        except Exception:
            pass

    # Try YAML detection
    try:
        parsed = yaml.safe_load(data)
        # YAML can parse simple strings, so check if it's actually structured
        if isinstance(parsed, (dict, list)) or ':' in data:
            return "yaml"
    except Exception:
        pass

    # Try INI detection
    config = configparser.ConfigParser()
    try:
        config.read_string(data)
        if config.sections() or any("=" in line for line in data.splitlines()):
            return "ini"
    except Exception:
        pass

    return False

def _validate_file_path(file_path: Union[str, Path]) -> Path:
    """
    Validate and sanitize file path.
    The function `_validate_file_path` validates and sanitizes a file path, providing basic protection
    against path traversal vulnerabilities.
    
    :param file_path: The `file_path` parameter is expected to be a string or a `Path` object
    representing a file path. The function `_validate_file_path` takes this input and
    validates/sanitizes the file path to ensure it is safe to use. It resolves the path and checks for
    any potentially unsafe
    :type file_path: Union[str, Path]
    :return: The function `_validate_file_path` is returning a `Path` object after validating and
    sanitizing the input file path. If the file path is valid and safe, the resolved `Path` object is
    returned. If the file path contains potentially unsafe elements like '..', or starts with '/', a
    `ValueError` is raised with the message "Potentially unsafe path detected". If there are any other
    errors during
    """
    
    try:
        path = Path(file_path).resolve()
        # Basic path traversal protection
        if '..' in str(path) or str(path).startswith('/'):
            raise ValueError("Potentially unsafe path detected")
        return path
    except (ValueError, OSError) as e:
        raise ConfigurationError(f"Invalid file path: {e}")
    
# The `ConfigurationError` class is a custom exception in Python that can be raised for
# configuration-related errors.
class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass

class MultiOrderedDict(OrderedDict):
    """OrderedDict that extends lists when duplicate keys are encountered."""
    
    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set item, extending lists if key already exists.
        The function __setitem__ sets an item in a dictionary, extending lists if the key already
        exists.
        
        :param key: The `key` parameter in the `__setitem__` method represents the key of the item being
        set in the data structure. It is typically a string that is used to access or identify the value
        associated with it
        :type key: str
        :param value: The `value` parameter in the `__setitem__` method represents the value that you
        want to set for a specific key in the data structure. If the value is a list and the key already
        exists in the data structure, the method will extend the existing list with the new values.
        Otherwise
        :type value: Any
        """
        
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super().__setitem__(key, value)

# The class `ConfigSetJson` extends both `JSONDecoder` and `JSONEncoder` in Python.
class ConfigSetJson(JSONDecoder, JSONEncoder):
    """
    Enhanced configuration file manager supporting JSON format.
    ConfigSetJson: JSON-backed configuration manager with safe nested access, mutation and persistence.
    This class provides a high-level, resilient API for reading, querying, updating and saving
    configuration data stored in JSON. It combines JSON encoding/decoding behavior with
    convenience helpers for nested key access, flexible key path syntax, and robust file
    handling with helpful debug output when enabled.
    Key features
    - Load configuration from file or JSON string (load, loads/_load_config, read).
    - Save configuration to file (dump, dumps/_save_config).
    - Query nested keys with flexible path formats (get, get_config, get_config1, get_config_file, filename).
    - Write nested values, creating intermediate dictionaries as required (set, write_config).
    - Remove keys, sections or values (remove_key, remove_section, remove_config, remove_value_anywhere).
    - Find values with optional equality matching (find, find1).
    - Display configuration with optional color/rich formatting (show, print).
    - Helpers to check key existence (exists) and change the target file (set_config_file).
    Path and key formats
    - Accepts either multiple positional path elements or single composite strings.
    - Composite separators supported: ".", ":", ";", "|" (e.g. "a.b:c|d").
    - Single list/tuple of keys is accepted (e.g. get(['a','b','c'])).
    - When using mixed forms, any argument that contains separators will be split in-place,
        allowing inputs like: get('k1', 'k2.k3:k4', 'k5') -> ['k1','k2','k3','k4','k5'].
    Initialization
    - __init__(json_file=None, config_file=None, *, object_hook=None, parse_float=None,
                         parse_int=None, parse_constant=None, strict=True, object_pairs_hook=None)
        - json_file / config_file: path to JSON file or None to work in-memory. If a file path is
            provided, the class will attempt to load it during initialization.
        - JSON Decoder/Encoder hooks are forwarded to the base classes.
        - On initialization, the instance attribute `json` holds the loaded configuration (dict or list)
            or an empty dict when loading fails (depending on error).
    Persistence behavior
    - _save_config(json_file=None) / dumps(...) write the current `self.json` to disk ensuring
        parent directories exist. Saves JSON with indent=2 and ensure_ascii=False by default.
    - dump(...) writes to the configured json_file and returns the saved data.
    - Methods that mutate data (write_config / remove_config / remove_key / remove_value_anywhere)
        call _save_config() after a successful change.
    Error handling and debug
    - File operations surface FileNotFoundError for explicit file-not-found cases in load().
    - Permission, decoding, and unexpected IO errors are logged and optionally converted to
        ConfigurationError (a project-specific exception) where appropriate.
    - When a global debug mode is enabled via the project's helper (_debug_enabled()),
        user-friendly messages are printed to the configured console object (_console).
    - Many mutating methods return a boolean status (True on success, False on failure) to
        make usage in scripts straightforward.
    Important return semantics
    - get/get_config/get_config1/find: return the found value or `default` (for get*) / {} (for find)
        when not found or on error.
    - write_config/set: return True on success, False on error.
    - remove_config/remove_key/remove_section/remove_value_anywhere: return True when a deletion
        actually occurred, otherwise False.
    Usage examples
    - Basic load from file:
            cs = ConfigSetJson(json_file='config.json')
            # cs.json now holds the loaded data (dict or list)
    - Read or parse a JSON string:
            cs = ConfigSetJson(json_file='{"a":{"b":1}}')   # _load_config will parse the string
            cs.loads('{"x": 2}')
    - Get nested values:
            cs.get('a', 'b')                # -> 1
            cs.get('a.b')                   # -> 1
            cs.get(['a','b'])               # -> 1
            cs.get('missing', default=42)   # -> 42
    - Write nested values:
            cs.set('a.b.c', value=3)
            cs.write_config('x', 'y', 10)   # last positional is value
            cs.write_config(['p','q','r'], value='val')
    - Remove keys and values:
            cs.remove_config('a.b.c')                # remove key c
            cs.remove_config('a', 'b', 'c', value=5) # remove specific value or list item
            cs.remove_config(value='orphan')         # remove 'orphan' anywhere in structure
            cs.remove_key('section:sub')             # supports ":" ";" "|" separators
    - Find with optional equality:
            cs.find('a.b')                # returns value or {}
            cs.find('a.b', value=expected)  # returns expected or {}
    - File management:
            cs.set_config_file('new_config.json')  # sets new target, creates file if missing
            cs.filename                             # returns current filename as string
            cs.get_config_file()                    # alias for filename
    Notes and implementation details
    - The class expects helper functions/objects from the package: _flatten_keys, _debug_enabled,
        _console, logger, ConfigurationError, and boolean flags HAS_RICH, HAS_JSONCOLOR, HAS_MAKECOLOR.
        Ensure these exist in the runtime environment.
    - The `json` attribute may be a dict or list depending on the stored data. Many convenience
        methods assume a dict for nested-key semantics; where appropriate, the class normalizes
        `self.json` to a dict before writing nested values.
    - The class focuses on safety and predictable behavior: reads are tolerant, writes are atomic
        at the python level (open/write), and helpful debug output is available without throwing
        exceptions for simple misses (most "not found" cases return default/{} or False).
    This docstring is intended to be placed at the top of the ConfigSetJson class definition.
    """
    
    def __init__(self, *, json_file: Any = None, config_file: Any = None, 
                 object_hook: Callable[[dict[str, Any]], Any] = None,  # type: ignore
                 parse_float: Callable[[str], Any] = None,  # type: ignore
                 parse_int: Callable[[str], Any] = None,  # type: ignore
                 parse_constant: Callable[[str], Any] = None,  # type: ignore
                 strict: bool = True, 
                 object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] = None) -> None: # type: ignore
        """
        Initialize JSON configuration handler.
        
        Args:
            json_file: Path to JSON configuration file
            config_file: Alternative name for json_file
            object_hook: Custom object hook for JSON decoding
            parse_float: Custom float parser
            parse_int: Custom int parser
            parse_constant: Custom constant parser
            strict: Strict JSON parsing mode
            object_pairs_hook: Custom pairs hook for JSON decoding
        """
        super().__init__(object_hook=object_hook, parse_float=parse_float, 
                        parse_int=parse_int, parse_constant=parse_constant, 
                        strict=strict, object_pairs_hook=object_pairs_hook)
        self.json_file = json_file or config_file
        self.file = self.json_file    
        self.json = self._load_config()
        
    def load(self, json_file=None):
        """
        Load JSON data from file.
        The `load` function loads JSON data from a file and raises a `FileNotFoundError` if the file is
        not found.
        
        :param json_file: The `json_file` parameter in the `load` method is used to specify the path to
        the JSON file from which data will be loaded. If no `json_file` is provided when calling the
        method, it defaults to the value of `self.json_file`. The method then attempts to load JSON
        :return: The `load` method is returning the JSON data loaded from the file specified by
        `json_file`.
        """
        
        json_file = json_file or self.json_file
        # if os.path.isfile(json_file):
        #     with open(json_file, 'r') as f:
        #         self.json = json.load(f)
        if json_file and os.path.isfile(json_file):
            with open(json_file, 'r', encoding='utf-8', errors='strict') as f:
                self.json = json.load(f)
        else:
            _console.print(f"\n:cross_mark: [white on red]JSON file not found:[/] [white on blue]{json_file}[/]")
            raise FileNotFoundError(f"JSON file not found: {json_file}")
        return self.json
    
    def _load_config(self, json_file=None) -> dict:
        """
        Load configuration from file with error handling.
        The `_load_config` function loads configuration from a JSON file with error handling in Python.
        
        :param json_file: The `_load_config` method is responsible for loading configuration from a JSON
        file with error handling. The `json_file` parameter is a file path to the JSON configuration
        file that you want to load. If this parameter is not provided, the method will use the
        `json_file` attribute of the class
        :return: The method `_load_config` returns the loaded JSON configuration data or an empty
        dictionary if there was an error during the loading process.
        """
        
        source = json_file or self.json_file
        try:
            if os.path.isfile(source):
                with open(source, "r", encoding="utf-8") as f:
                    self.json = json.load(f)
            elif isinstance(source, str) and "{" in source.strip():
                self.json = json.loads(source)
            elif isinstance(source, bytes):
                self.json = json.loads(source.decode())
            else:
                with open(source, "w", encoding="utf-8") as f:
                    json.dump({}, f, ensure_ascii=False, indent=4)
                return {}
            return self.json
        # except Exception as e:
        #     self.json = {}
        #     if _debug_enabled():
        #         _console.print(f":cross_mark: [white on red]Error loading JSON config:[/] [white on blue]{e}[/]")
        except FileNotFoundError:
            if _debug_enabled():
                _console.print(f"[:cross_mark: [white on red]Config file not found:[/] [white on blue]{source}[/]")
            logger.warning(f"Config file not found: {source}")
            # Create empty config or use defaults
        except PermissionError:
            if _debug_enabled():
                _console.print(f":cross_mark: [white on red]Permission denied accessing:[/] [white on blue]{source}[/]")
            logger.error(f"Permission denied accessing: {source}")
            raise ConfigurationError(f"Cannot access config file: {source}")
        except UnicodeDecodeError as e:
            if _debug_enabled:
                _console.print(f":cross_mark: [white on red]Invalid encoding in config file:[/] [white on blue]{e}[/]")
            logger.error(f"Invalid encoding in config file: {e}")
            raise ConfigurationError(f"Config file has invalid encoding: {e}")
        except Exception as e:
            if _debug_enabled:
                _console.print(f":cross_mark: [white on red]Unexpected error loading config:[/] [white on blue]{e}[/]")
            logger.error(f"Unexpected error loading config: {e}")
            if os.getenv('traceback') in ['1', 'true', 'True']:
                if HAS_RICH:
                    _console.print_exception() # type: ignore
                else:
                    logger.error(f"TRACEBACK: {traceback.format_exc()}")
            raise ConfigurationError(f"Failed to load configuration: {e}")
        self.json = {}
        return self.json
    
    def loads(self, json_file=None):
        """
        Alias for _load_config.
        The function `loads` is an alias for `_load_config` and is used to load a JSON configuration
        file.
        
        :param json_file: The `json_file` parameter in the `loads` method is used to specify the path to
        a JSON file that contains configuration data to be loaded. If no `json_file` is provided, the
        method will use the default value of `None`
        :return: The `loads` method is returning the result of calling the `_load_config` method with
        the `json_file` parameter passed to it.
        """
        
        return self._load_config(json_file)
    
    def read(self, json_file=None):
        """
        The `read` function reads a JSON file and loads its configuration.
        
        :param json_file: The `json_file` parameter in the `read` method is used to specify the path to
        a JSON file that contains configuration data. If a `json_file` path is provided, the method will
        attempt to load the configuration data from that file. If no `json_file` path is provided (
        :return: The `read` method is returning the result of calling the `_load_config` method with the
        `json_file` parameter passed to the `read` method.
        """
        
        return self._load_config(json_file)

    def _save_config(self, json_file=None) -> List:
        """Saves the current configuration to a JSON file or parses a JSON string.
           The function `_save_config` saves the current configuration to a JSON file, handling
           exceptions and ensuring the parent directory exists.
        Args:
            `json_file`(str | None): Optional path to the JSON file. 
                                   If None, uses the default file path.
                                   this can be file path or dict

        Returns:
            list: The parsed JSON data (`self.json`), json configuration file (`self.json_file`)

        Raises:
            ConfigurationError: Raised if no JSON file is configured for saving.
            Exception: Raised if an error occurs during JSON saving or parsing.
        """
        
        target = json_file or self.json_file
        if not target:
            raise ConfigurationError("No JSON file configured for saving")
        if Path(target).is_file():
            try:
                # ensure parent dir exists
                p = Path(target)
                if not p.parent.exists():
                    p.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "w", encoding="utf-8") as f:
                    json.dump(self.json if isinstance(self.json, (dict, list)) else {}, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error("Error saving JSON config: %s", e)
                if _debug_enabled():
                    _console.print(f":cross_mark: [white on red]Error saving JSON config:[/] [white on blue]{e}[/]")
                raise
        elif isinstance(target, str or bytes) and "{" in target.strip():
            try:
                self.json = json.loads(target)
                with open(self.json_file, "w", encoding="utf-8") as f:
                    json.dump(self.json if isinstance(self.json, (dict, list)) else {}, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error("Error parsing JSON string: %s", e)
                if _debug_enabled():
                    _console.print(f":cross_mark: [white on red]Error parsing JSON string:[/] [white on blue]{e}[/]")
                raise
        else:
            logger.error("Error saving JSON config, target is not a file or valid JSON string: %s", target)
            if _debug_enabled():
                _console.print(f":cross_mark: [white on red]Error saving JSON config, target is not a file or valid JSON string:[/] [white on blue]{target}[/]")
            raise
        
        return [self.json, self.json_file]

    def dump(self, json_file = None, **kwargs):
        """Saves the current configuration to a JSON file.
        
        This function dumps JSON data to a file. if data is None or {} then run 
        `self._load_config` before.

        Args:
            json_file(str | None): Optional path to the JSON file. If provided, saves to this file; otherwise, saves to the default file path.
            **kwargs(dict): Additional keyword arguments to pass to `json.dump`.

        Returns:
            dict | None: The configuration dictionary from `json.dump` if successful, None if json_file is provided and saving fails.

        Raises:
            FileNotFoundError: If the default JSON file path is invalid.
            json.JSONDecodeError: If there is an error decoding the JSON data.
            IOError: If there is an error writing to the JSON file.
        """
        
        if not self.json:
            self.json = self._load_config(json_file)
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(self.json, f, **kwargs)
        return self.json

    def dumps(self, *args, **kwargs):
        """
        Save configuration (alias for _save_config).
        The `dumps` function is used to save configuration by calling the `_save_config` method with the
        provided arguments and keyword arguments.
        :return: The `dumps` method is returning the result of calling the `_save_config` method with
        the provided arguments `*args` and `**kwargs`.
        """
        
        return self._save_config(*args, **kwargs)
    
    def show(self):
        """
        Display JSON configuration with colored output if available.
        The function displays JSON configuration with colored output if available using different
        libraries.
        """
        
        if HAS_JSONCOLOR:
            jprint(self.json)
        elif HAS_RICH:
            _console.print_json(data=self.json) # type: ignore
        elif HAS_MAKECOLOR:
            print(make_colors(self.json, 'lc'))
        else:
            print(json.dumps(self.json, indent=2))
            
    def print(self):
        """
        Alias for show method.
        The function defines a method `print` that is an alias for the `show` method.
        :return: The `show` method is being called and its return value is being returned.
        """
        
        return self.show()
    
    @property
    def filename(self):
        """
        Get the filename of the JSON configuration file.
        This function returns the filename of the JSON configuration file as a string.
        :return: The `filename` method is returning the filename of the JSON configuration file as a
        string.
        """
        
        return str(self.json_file)
    
    def exists(self, key):
        """
        Check if a configuration key exists.
        The function checks if a given key exists in a configuration dictionary.
        
        :param key: The `exists` method is used to check if a configuration key exists in a JSON object
        stored in the `self.json` attribute of an object. The `key` parameter represents the key that
        you want to check for existence in the JSON object
        :return: The `exists` method is returning a boolean value. It returns `True` if the `key` exists
        in the dictionary `self.json`, and `False` otherwise.
        """
        
        if isinstance(self.json, dict):
            return key in self.json
        return False

    @property
    def config_file(self):
        """
        Get the configuration name (alias for `self.filename`).
        The `config_file` function returns the configuration name, which is an alias for the filename.
        :return: The method `config_file` is returning the value of `self.filename`, which is the
        configuration name or alias for the filename.
        """
        
        return self.filename
    
    @property
    def configname(self):
        """
        Get the configuration name (alias for `self.filename`).
        This function returns the configuration name, which is an alias for the filename.
        :return: The method `configname` is returning the value of `self.filename`, which is the
        configuration name.
        """
        
        return self.filename
    
    def set_config_file(self, config_file: str) -> bool:
        """
        Set a new configuration file path.
        The function `set_config_file` sets a new configuration file path, creating the file if it
        doesn't exist, and returns a boolean indicating success.
        
        :param config_file: The `config_file` parameter in the `set_config_file` method is a string that
        represents the path to a configuration file. This method is used to set a new configuration file
        path for the object. If the file exists, it loads the configuration from the file. If the file
        does not exist
        :type config_file: str
        :return: The `set_config_file` method returns a boolean value. It returns `True` if the new
        configuration file path is successfully set and either loaded or initialized, and it returns
        `False` if the provided `config_file` is empty or if there is an exception during the process.
        """
        
        if not config_file:
            return False
        self.json_file = config_file
        try:
            if os.path.isfile(self.json_file):
                self._load_config()
            else:
                # initialize empty json and save to create file
                self.json = {} 
                p = Path(self.json_file)
                if not p.parent.exists():
                    p.parent.mkdir(parents=True, exist_ok=True)
                self._save_config(self.json_file)
            return True
        except Exception:
            _console.print("\n:cross_mark: [white on red]Invalid Json File ![/]")
            return False
    
    # def get_config(self, key, **kwargs):
    #     """Get configuration value by key"""
    #     if isinstance(self.json, dict):
    #         return self.json.get(key, None)
    #     else:
    #         _console.print(f"\n:cross_mark: [white on red]Invalid Json File ![/]")
    #         return None
    
    def get_config1(self, *keys, default=None, **kwargs):
        """
        Get configuration value by nested keys.

        Usage:
            get_config('a')                     -> top-level key 'a'
            get_config('a', 'b', 'c')           -> nested access a.b.c
            get_config('a.b.c')                 -> single composite key (dot or :;| separators supported)
            get_config(['a','b','c'])           -> list/tuple of keys
            get_config(...)                     -> returns `default` if key path not found

        Returns the value found at the nested path or `default` when missing.
        """
        
        try:
            # No keys provided -> return default
            if not keys:
                return default

            # Build list of path segments from arguments
            if len(keys) == 1:
                first = keys[0]
                if isinstance(first, str):
                    # Accept separators: dot, colon, semicolon, pipe
                    parts = [p for p in re.split(r'[.:;|]', first) if p != '']
                elif isinstance(first, (list, tuple)):
                    parts = [str(p) for p in first if p is not None and str(p).strip() != ""]
                else:
                    # unsupported single-arg type
                    return default
            else:
                # multiple args -> each arg is a path segment
                parts = [str(p) for p in keys if p is not None and str(p).strip() != ""]

            if not parts:
                return default

            # Traverse the JSON structure safely
            current = self.json
            for seg in parts:
                if isinstance(current, dict) and seg in current:
                    current = current[seg]
                else:
                    if _debug_enabled():
                        _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{seg}[/]")
                    return default

            return current

        except Exception as e:
            # Fail-safe: return default on unexpected error and optionally print debug info
            if _debug_enabled():
                _console.print(f"\n:cross_mark: [white on red]Error getting config:[/] [white on blue]{e}[/]")
            return default
    
    def get_config(self, *keys, default=None):
        """
        Get configuration value by nested keys.

        Usage:
            get_config('a')                     -> top-level key 'a'
            get_config('a', 'b', 'c')           -> nested access a.b.c
            get_config('a.b.c')                 -> single composite key (dot or :;| separators supported)
            get_config(['a','b','c'])           -> list/tuple of keys
            get_config(...)                     -> returns `default` if key path not found

        This method accepts mixed forms: multiple positional keys and composite keys that contain
        separators. Any argument that contains separators will be split into segments and those
        segments are injected in-place, so e.g. get_config('k1', 'k2.k3:k4', 'k5') becomes
        ['k1','k2','k3','k4','k5'].
        """
        if default and isinstance(default, bytes):
            default = default.decode()
        
        if default and isinstance(default, str) and str(default).isdigit():
            default = int(default)
        
        if default and isinstance(default, str) and str(default).replace(".", "").isdigit():
            default = float(default)

        try:
            # No keys provided -> return default
            if not keys:
                return default
            
            # Handle single list/tuple argument
            if len(keys) == 1 and isinstance(keys[0], (list, tuple)):
                keys = keys[0]
        
            # Build list of path segments from provided arguments.
            # Support: multiple args, single composite string, list/tuple as single arg,
            # and mixed args containing separators.
            parts: List[str] = _flatten_keys(keys)

            if not parts:
                return default

            # Traverse the JSON structure safely
            current = self.json
            for seg in parts:
                if isinstance(current, dict) and seg in current:
                    current = current[seg]
                    if not current and default:
                        return default
                    elif not current and isinstance(default, bool):
                        return default
                    elif current and str(current).isdigit():
                        return int(current)
                else:
                    if _debug_enabled():
                        _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{seg}[/]")
                    return default

            return current

        except Exception as e:
            # Fail-safe: return default on unexpected error and optionally print debug info
            if _debug_enabled():
                _console.print(f"\n:cross_mark: [white on red]Error getting config:[/] [white on blue]{e}[/]")
            return default
        
    def get_config_file(self):
        """
        Get the filename of the JSON configuration file.
        This function returns the filename of the JSON configuration file as a string.
        :return: The method `get_config_file` returns the filename of the JSON configuration file as a
        string.
        """
        
        return str(self.json_file)    
    
    def get(self, *keys, default=None):
        """
        Alias for get_config.
        The function `get` is an alias for `get_config` in Python.
        
        :param key: The `key` parameter in the `get` method is used to specify the configuration key for
        which you want to retrieve the value. It is the identifier or name of the configuration setting
        that you are interested in accessing
        :return: The `get_config` method is being called with the provided `key` and any additional
        keyword arguments, and the result of that method call is being returned.
        """
        
        return self.get_config(*keys, default=default)

    def get_key(self, *keys, default=None):
        """
        Alias for get_config.
        The function `get` is an alias for `get_config` in Python.
        
        :param key: The `key` parameter in the `get` method is used to specify the configuration key for
        which you want to retrieve the value. It is the identifier or name of the configuration setting
        that you are interested in accessing
        :return: The `get_config` method is being called with the provided `key` and any additional
        keyword arguments, and the result of that method call is being returned.
        """
        
        return self.get_config(*keys, default=default)

    def get_all(self) -> dict:
        """
        Return the whole JSON-backed configuration as a mapping.

        This ensures callers can iterate over key/value pairs with .items().
        If the in-memory content is already a dict, return it unchanged.
        If the content is a non-mapping (e.g. list or scalar), return a single-key
        mapping under '_root' so .items() is always available.
        """
        # normalize None -> empty dict
        if self.json is None:
            return {}
        if isinstance(self.json, dict):
            return self.json
        # for lists/scalars, present a stable mapping
        return {"_root": self.json}
    
    def get_config_name(self):
        """
        This function returns the configuration name, which is an alias for the filename.
        :return: The method `get_config_name` is returning the value of `self.filename`, which is the
        configuration name.
        """
        
        return self.filename

    def read_config(self, *keys, default=None):
        """
        Alias for get_config.
        The `read_config` function is an alias for the `get_config` function in Python.
        
        :param key: The `key` parameter in the `read_config` method is used to specify the configuration
        key for which you want to retrieve the value from the configuration settings
        :return: The `read_config` method is returning the value associated with the specified `key`
        from the configuration settings. It is an alias for the `get_config` method.
        """
        
        return self.get_config(*keys, default=default)

    def write_config(self, *keys, value: Any = None) -> bool:
        """
        Write configuration value by nested keys (JSON backend).

        Accepts:
          - write_config('a.b.c', 'value')
          - write_config('a','b','c', value='value')
          - write_config('a','b','c','value')  (last positional becomes value if value kw not used)

        Behavior:
          - flexible key formats: dotted or separators (.,:,;,|)
          - supports mixed positional args where any arg containing separators is split in-place
            (e.g. write_config('k1', 'k2.k3:k4', 'k5', 'v') -> path ['k1','k2','k3','k4','k5'])
          - normalizes root to a dict if None or not a mapping
          - returns True on success, False on error
          
        This method accepts mixed forms: multiple positional keys and composite keys that contain
        separators. Any argument that contains separators will be split into segments and those
        segments are injected in-place, so e.g. get_config('k1', 'k2.k3:k4', 'k5') becomes
        ['k1','k2','k3','k4','k5'].
        """
        
        try:
            parts_src = list(keys)

            # If caller passed value as last positional and didn't use keyword
            if value is None and len(parts_src) >= 2:
                # last positional is treated as value
                value = parts_src.pop(-1)

            if not parts_src:
                if _debug_enabled():
                    _console.print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            # Normalize iterable (support single list/tuple arg or multiple args)
            if len(parts_src) == 1 and isinstance(parts_src[0], (list, tuple)):
                iterable = parts_src[0]
            else:
                iterable = parts_src

            # Flatten and split by separators using shared helper
            parts: List[str] = _flatten_keys(iterable)
            if not parts:
                if _debug_enabled():
                    _console.print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            # ensure root is a mapping
            if not isinstance(self.json, dict):
                self.json = {}

            # Traverse and set nested value
            d = self.json
            for k in parts[:-1]:
                if k not in d or not isinstance(d[k], dict):
                    d[k] = {}
                d = d[k]
            d[parts[-1]] = value

            self._save_config()
            return True

        except Exception as e:
            if _debug_enabled():
                if HAS_RICH:
                    _console.print(f"\n:cross_mark: [white on red]Error writing config:[/] [white on blue]{e}[/]")
                else:
                    _console.print(f":cross_mark: [white on red]Error writing config:[/] [white on blue]{e}[/]")
            return False
        
    def set(self, *keys, value: Any = None):
        """
        Alias for write_config.
        The function `set` is an alias for `write_config` and sets a key-value pair in the
        configuration.
        
        :param key: The `key` parameter in the `set` method is a string that represents the key for the
        configuration setting that you want to set or update
        :param value: The `value` parameter in the `set` method is a string type parameter with a
        default value of an empty string (''). This parameter represents the value that will be
        associated with the specified key in the configuration
        :type value: str
        :return: The `set` method is returning the result of calling the `write_config` method with the
        provided `key` and `value` parameters.
        """
        
        return self.write_config(*keys, value=value)

    def remove_value_anywhere(self, value):
        """
        Remove all occurrences of a value from the JSON structure.
        The function removes all occurrences of a specified value from a JSON structure.
        
        :param value: The `value` parameter in the `remove_value_anywhere` method represents the value
        that you want to remove from the JSON structure. This method will search through the JSON
        structure and remove all occurrences of this specified value
        :return: The `remove_value_anywhere` method returns a boolean value indicating whether the
        specified `value` was found and removed from the JSON structure. If the value was found and
        removed, the method also saves the updated configuration and returns `True`. If the value was
        not found in the JSON structure, it returns `False`.
        """
        
        q = deque([self.json])
        found = False
        while q:
            current = q.popleft()
            if isinstance(current, dict):
                for k in list(current.keys()):
                    # if current[k] == value:
                    #     del current[k]
                    #     found = True
                    # elif isinstance(current[k], dict):
                    #     q.append(current[k])
                    v = current.get(k)
                    if v == value:
                        del current[k]
                        found = True
                    elif isinstance(v, dict) or isinstance(v, list):
                        q.append(v)
            elif isinstance(current, list):
                # remove matching items and queue nested containers
                i = 0
                while i < len(current):
                    v = current[i]
                    if v == value:
                        current.pop(i)
                        found = True
                        continue
                    if isinstance(v, (dict, list)):
                        q.append(v)
                    i += 1
        if found:
            self._save_config()
        return found
    
    def remove_config(self, *keys, value: Any = None) -> bool:
        """
        Remove configuration key or value.

        Usage:
          - remove_config('a:b:c')                      -> remove key c under a.b
          - remove_config('a','b','c')                  -> same as above
          - remove_config('a','b','c', value='v')       -> remove specific value or list item
          - remove_config('a','b','c','v')              -> last positional treated as value
          - remove_config(value='v')                    -> remove value anywhere (delegates)
        """
        
        # If caller passed only a value (no keys) -> delegate to remove_value_anywhere
        if not keys and value is not None:
            return self.remove_value_anywhere(value)

        try:
            parts_src = list(keys)

            # Support last-positional-as-value (consistent with write_config)
            if value is None and len(parts_src) >= 2:
                value = parts_src.pop(-1)

            if not parts_src:
                if _debug_enabled():
                    if HAS_RICH:
                        _console.print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    else:
                        _console.print(":warning: [bold #FFFF00]No key ![/]")
                return False

            # Normalize iterable (support single list/tuple arg or multiple args)
            if len(parts_src) == 1 and isinstance(parts_src[0], (list, tuple)):
                iterable = parts_src[0]
            else:
                iterable = parts_src

            # Flatten keys (split composite segments)
            parts: List[str] = _flatten_keys(iterable)
            if not parts:
                return False

            d = self.json
            # Traverse to parent dict
            for k in parts[:-1]:
                if k in d and isinstance(d[k], dict):
                    d = d[k]
                else:
                    if _debug_enabled():
                        _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{k}[/]")
                    return False

            last_key = parts[-1]
            if last_key not in d:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{last_key}[/]")
                return False

            # Remove by key or by matching value
            if value is None:
                del d[last_key]
            else:
                if d[last_key] == value:
                    del d[last_key]
                elif isinstance(d[last_key], list) and value in d[last_key]:
                    d[last_key].remove(value)
                else:
                    return False

            self._save_config()
            return True

        except Exception as e:
            if _debug_enabled():
                _console.print(f"\n:cross_mark: [white on red]Error removing config:[/] [white on blue]{e}[/]")
            return False
        
    def remove_key(self, key: str) -> bool:
        """
        Remove key and its children (supports nested keys).
        This Python function removes a specified key and its children from a nested dictionary
        structure.
        
        :param key: The `remove_key` method takes a `key` parameter as input, which is a string
        representing the key to be removed along with its children. The method supports nested keys,
        meaning you can specify a key path using delimiters like `:`, `;`, or `|` to indicate nested
        :type key: str
        :return: The `remove_key` method returns a boolean value - `True` if the key and its children
        were successfully removed, and `False` if there was an error or if the key was not found.
        """
        
        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]
            if not keys:
                if _debug_enabled():
                    msg = "No key!"
                    _console.print(f"\n:cross_mark: [bold #FFFF00]{msg}[/]") if HAS_RICH else print(msg)
                return False

            d = self.json
            for k in keys[:-1]:  # Stop before last key
                if k in d and isinstance(d[k], dict):
                    d = d[k]
                else:
                    if _debug_enabled():
                        msg = f"Key not found: {k}"
                        _console.print(f"\n:cross_mark: [white on red]{msg}[/]") if HAS_RICH else print(msg)
                    return False

            last_key = keys[-1]
            if last_key not in d:
                if _debug_enabled():
                    msg = f"Key not found: {last_key}"
                    _console.print(f"\n:cross_mark: [white on red]{msg}[/]") if HAS_RICH else print(msg)
                return False

            del d[last_key]
            self._save_config()
            return True

        except Exception as e:
            if _debug_enabled():
                msg = f"Error removing key: {e}"
                _console.print(f"\n:cross_mark: [white on red]{msg}[/]") if HAS_RICH else print(msg)
            return False
    
    def remove_section(self, key: str):
        """
        Alias for remove_key.
        The function `remove_section` is an alias for `remove_key` in Python.
        
        :param key: The `key` parameter in the `remove_section` method is a string that represents the
        key of the section that you want to remove from the data structure
        :type key: str
        :return: The `remove_section` method is returning the result of calling the `remove_key` method
        with the `key` parameter passed to it.
        """
        
        return self.remove_key(key)

    def find1(self, key: str, value=None):
        """
        The function `find` searches for a specific key in a JSON object and returns its corresponding
        value.
        
        :param key: The `find` method you provided is used to search for a specific key in a JSON
        object. The `key` parameter is the key you are searching for in the JSON object. If you have a
        specific key in mind that you want to find in the JSON object, you can provide it here. The method 
        supports nested keys,
        meaning you can specify a key path using delimiters like `:`, `;`, or `|` to indicate nested
        :type key: str
        :param value: The `value` parameter in the `find` method is used to specify a value that you are
        looking for associated with the given key. If the key is found in the JSON data and the value
        matches the specified value, then the method will return the found value. Otherwise, it will
        return an empty dictionary.
        :return: The `find` method returns a dictionary containing the value associated with the
        specified key in the JSON data. If the key is not found or an error occurs during the process,
        an empty dictionary `{}` is returned.
        """
        
        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]
            if not keys:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
                return {}

            d = self.json
            for k in keys[:-1]:
                # print(">>> Traverse check:", k, "in", type(d))
                if isinstance(d, dict) and k in d:
                    d = d[k]
                else:
                    if _debug_enabled():
                        _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{k}[/]")
                    return {}

            last_key = keys[-1]
            
            if isinstance(d, dict) and last_key in d:
                found = d[last_key]
                # print(">>> FOUND =", repr(found))
                if value is not None:
                    return found if found == value else {}
                return found
            else:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{last_key}[/]")
                return {}
        except Exception as e:
            if _debug_enabled():
                _console.print(f"\n: cross_mark: [white on red]Error finding key:[/] [white on blue]{key}[/]")
            return {}

    def find(self, *keys, value=None):
        """
        Find a value by nested keys (JSON backend).

        This method accepts mixed forms: multiple positional keys and composite keys that contain
        separators. Any argument that contains separators will be split into segments and those
        segments are injected in-place, so e.g. find('k1', 'k2.k3:k4', 'k5') becomes
        ['k1','k2','k3','k4','k5'].

        Usage:
          - find('a') -> returns value at top-level key 'a' or {} if not found
          - find('a','b','c') -> nested access a.b.c
          - find('a.b.c') -> composite key string
          - find(['a','b','c']) -> list/tuple of keys
          - find(..., value=expected) -> returns matched value only when equal, otherwise {}
        """
        
        try:
            if not keys:
                return {}

            parts: List[str] = _flatten_keys(keys)
            if not parts:
                return {}

            d = self.json if isinstance(self.json, dict) else self.json or {}
            for seg in parts[:-1]:
                if isinstance(d, dict) and seg in d:
                    d = d[seg]
                else:
                    if _debug_enabled():
                        _console.print(f"\n:cross_mark: [white on red]Key not found while traversing:[/] [white on blue]{seg}[/]")
                    return {}

            last_key = parts[-1]
            if isinstance(d, dict) and last_key in d:
                found = d[last_key]
                if value is None:
                    return found
                return found if found == value else {}
            else:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{last_key}[/]")
                return {}
        except Exception as e:
            if _debug_enabled():
                _console.print(f"\n:cross_mark: [white on red]Error in find():[/] [white on blue]{e}[/]")
            return {}
        
class ConfigSetYaml:
    """
    ConfigSetYaml
    =============
    A lightweight YAML-backed configuration helper that provides safe loading, reading,
    writing, searching and removal of configuration values. Designed to be tolerant of
    missing files and invalid YAML content (falls back to an empty mapping) and to
    support nested key access with flexible key separators.
    Initialization
    --------------
    ConfigSetYaml(yaml_file: str = '', config_file: str = '', **kwargs)
    - yaml_file / config_file: Path to a YAML file or a YAML string. If both are empty,
        an instance with an empty configuration is created and can be populated and saved later.
    - kwargs: Reserved for future extensions; stored on the instance.
    Key behaviors
    -------------
    - Loading:
        - load(yaml_file=None) / read(yaml_file=None): Load configuration from a file path
            or from a YAML string (delegates to _load_config / loads).
        - loads(yaml_file): Accepts a path, YAML string, bytes, or a dict. If given a path
            that exists, file is read; else attempts YAML parsing. Raises TypeError for
            unsupported input types.
        - _load_config(yaml_file=None): Internal loader with robust error handling:
            FileNotFound -> logs warning and returns {}, PermissionError -> raises
            ConfigurationError, UnicodeDecodeError -> raises ConfigurationError,
            yaml.YAMLError -> logs warning and returns {}.
    - Saving:
        - _save_config(yaml_file=''): Internal helper that writes YAML to disk using
            safe_dump. Ensures parent directories exist and raises ConfigurationError when
            no target file is provided.
        - dump(...): Writes current configuration to the configured file (self.yaml_file)
            and returns the in-memory mapping.
        - dumps(...): Returns a YAML string representation of the current configuration.
    - Inspection and display:
        - show(): Pretty-prints the configuration using optional helpers (jsoncolor, rich,
            makecolor) and falls back to safe_dump.
        - print(): Alias for show().
        - filename / config_file / configname: Properties returning the current filename.
    - Accessing values:
        - get_config(*keys, default=None, **kwargs):
                Retrieve nested values using flexible key forms:
                    - Multiple positional keys: get_config('a', 'b', 'c')
                    - Single composite key: get_config('a.b:c|d')
                    - Single list/tuple: get_config(['a','b','c'])
                Missing or malformed roots cause a reload attempt; returns `default` if path
                not found or an error occurs.
        - get / read_config: Convenience wrappers around get_config.
    - Mutating values:
        - write_config(*keys, value=None) -> bool:
                Write a value to a nested path. Supports the same flexible key formats as
                get_config. If the last positional argument is the value (and `value` kw is
                omitted), it is accepted. Creates intermediate mappings as needed. Persists
                changes to disk via _save_config. Returns True on success, False on error.
        - set: Alias to write_config.
    - Removing values/keys:
        - remove_value_anywhere(value) -> bool:
                Recursively scans the entire configuration and removes all occurrences of
                the provided value (from dictionary values and list items). Persists if
                any removal occurs; returns True when at least one removal happened.
        - remove_config(*keys, value=None) -> bool:
                Remove a key at a nested path or remove a specific value from a keyed list.
                If called with only value=..., delegates to remove_value_anywhere.
                Supports flexible key formats and last-positional-as-value semantics.
        - remove_key(key: str) -> bool and remove_section(key: str):
                Remove a key and its children. `key` may be a nested key using separators
                (":", ";", "|"). Persists changes and returns True on success.
    - Finding values:
        - find(*keys, value=None):
                Similar to get_config but returns {} when not found. If `value` is provided,
                only returns the found value when it equals `value`.
        - find1(key: str, value=None):
                Backward-compatible single-string-key helper with optional value check.
    Error handling & debug
    ----------------------
    - The loader tolerates missing files and YAML parse errors by logging and returning
        empty mappings. Permission and decoding errors raise ConfigurationError.
    - When a debug mode helper (_debug_enabled) is enabled, diagnostic messages are
        written to a console helper (_console).
    - Internal exceptions during write/remove operations are caught and reported; most
        mutating methods return False on failure rather than raising.
    Examples
    --------
    Basic usage:
            cfg = ConfigSetYaml('config.yml')
            cfg.load()                     # load from file or fallback to empty mapping
            value = cfg.get_config('section', 'option', default=42)
    Write and persist:
            cfg.write_config('servers', 'web', value={'host': 'example', 'port': 80})
            # or
            cfg.set('servers.web.host', value='example')
    Flexible key forms:
            cfg.get_config('a.b:c|d')      # equivalent to cfg.get_config('a','b','c','d')
            cfg.write_config(['a','b','c'], value=123)
    Remove operations:
            cfg.remove_config('section', 'option')          # remove a key
            cfg.remove_config('section', 'list', value=3)   # remove a specific list item
            cfg.remove_config(value='unwanted')             # remove value anywhere
    Serialization:
            yaml_text = cfg.dumps(default_flow_style=False)
            cfg.dump()                       # writes current mapping to self.yaml_file
    Notes
    -----
    - This helper expects PyYAML (yaml) and uses yaml.safe_load / yaml.safe_dump.
    - The class manages an in-memory mapping (self.yaml). Callers should be aware that
        methods which mutate state will attempt to persist changes immediately.
    - Key splitting and flattening logic is implemented via a helper _flatten_keys which
        understands separators (., :, ;, |). When using composite keys prefer consistent
        separators to avoid ambiguity.
    """
    
    def __init__(self, yaml_file: str = '', config_file: str = '', **kwargs):
        self.yaml_file = yaml_file or config_file
        self.file = self.yaml_file
        self.kwargs = kwargs
        self.yaml = self._load_config()

    def load(self, yaml_file=None):
        """
        Load YAML data from file.
        This function is used to load data from a YAML file.
        
        :param yaml_file: The `load` method you provided seems to be incomplete. It looks like you were
        about to provide some information about the parameters, but it's missing. Could you please
        provide more details or let me know how I can assist you further?
        """
        
        return self._load_config(yaml_file)
    
    def loads(self, yaml_file: str = ''):
        """
        The function `loads` in the provided Python code snippet is responsible for loading a YAML
        configuration from a file, string, bytes, or dictionary input.
        
        :param yaml_file: The `yaml_file` parameter in the `loads` method is used to specify the YAML
        file that you want to load. It can be a string representing the path to a YAML file, the content
        of a YAML file as a string, a byte string, or a dictionary containing YAML data
        :type yaml_file: str
        :return: The method `loads` is returning the result of the `_load_config` method when
        `yaml_file` is empty or when it is a valid file path. If `yaml_file` is a string, bytes, or a
        dictionary, it sets the `yaml` attribute of the object accordingly. If none of these conditions
        are met, it raises a `TypeError` with an error message.
        """
        
        if not yaml_file:
            return self._load_config(yaml_file)
        if isinstance(yaml_file, str) and os.path.isfile(yaml_file):
            return self._load_config(yaml_file)
        else:
            if isinstance(yaml_file, str):
                self.yaml = yaml.safe_load(yaml_file)
            elif isinstance(yaml_file, bytes):
                self.yaml = yaml.safe_load(yaml_file.decode("utf-8"))
            elif isinstance(yaml_file, dict):
                self.yaml = yaml_file
            else:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [white on red]Invalid YAML input:[/] [white on blue]{yaml_file}[/]")
                raise TypeError(f"Invalid YAML input: {type(yaml_file)}")

    def read(self, yaml_file: str = ''):
        """
        The function reads and loads a YAML file.
        
        :param yaml_file: The `yaml_file` parameter in the `read` method is a string that represents the
        path to a YAML file that you want to read and load
        :type yaml_file: str
        :return: The `read` method is returning the result of calling the `loads` method on the
        `yaml_file` parameter.
        """
        
        return self.loads(yaml_file)

    def _load_config(self, yaml_file=None):
        """
        Load configuration from file with error handling.
        The `_load_config` function loads a YAML configuration file with error handling and returns the
        parsed configuration data.
        
        :param yaml_file: The `yaml_file` parameter in the `_load_config` method is used to specify the
        path to the YAML configuration file that needs to be loaded. If `yaml_file` is not provided, the
        method falls back to using the `yaml_file` attribute of the class instance
        :return: The `_load_config` method returns the loaded YAML configuration data stored in the
        `self.yaml` attribute of the class instance. If an exception is raised during the loading
        process, it handles the error accordingly and returns an empty dictionary `{}` as a fallback.
        """
        
        source = yaml_file or self.yaml_file
        if _debug_enabled():
            _console.print(f"\n:gear: [white on blue]Loading YAML config:[/] [white on blue]{source}[/]")
            _console.print(f":mag: [white on blue]YAML File is File:[/] [white on blue]{os.path.isfile(source)}[/]")
        try:
            if os.path.isfile(source):
                with open(source, "r", encoding="utf-8") as f:
                    self.yaml = yaml.safe_load(f)
                    if _debug_enabled():
                        _console.print(f":white_check_mark: (1) [white on green]YAML config loaded successfully from file.[/]")
                        _console.print(f":gear: [white on blue] (1) YAML data type:[/] [white on blue]{type(self.yaml)}[/]")
            else:
                self.yaml = yaml.safe_load(source)  # Fix: was yaml.save_load
                if _debug_enabled():
                        _console.print(f":white_check_mark: (2) [white on green]YAML config loaded successfully from file.[/]")
                        _console.print(f":gear: [white on blue] (2) YAML data type:[/] [white on blue]{type(self.yaml)}[/]")
            if self.yaml is None:
                self.yaml = {}
            return self.yaml
        except FileNotFoundError:
            if _debug_enabled():
                _console.print(f"[:cross_mark: [white on red]Config file not found:[/] [white on blue]{source}[/]")
            logger.warning(f"Config file not found: {source}")
            # Create empty config or use defaults
        except PermissionError:
            if _debug_enabled():
                _console.print(f":cross_mark: [white on red]Permission denied accessing:[/] [white on blue]{source}[/]")
            logger.error(f"Permission denied accessing: {source}")
            raise ConfigurationError(f"Cannot access config file: {source}")
        except UnicodeDecodeError as e:
            if _debug_enabled:
                _console.print(f":cross_mark: [white on red]Invalid encoding in config file:[/] [white on blue]{e}[/]")
            logger.error(f"Invalid encoding in config file: {e}")
            raise ConfigurationError(f"Config file has invalid encoding: {e}")
        except yaml.YAMLError as e:
            # tolerate YAML parse errors in production: log and fallback to empty mapping
            logger.warning("Invalid YAML content in %s: %s", source, e)
            if _debug_enabled():
                _console.print(f":cross_mark: [white on red]Invalid YAML content:[/] [white on blue]{e}[/]")
            self.yaml = {}
            return self.yaml
        except Exception as e:
            if _debug_enabled:
                _console.print(f":cross_mark: [white on red]Unexpected error loading config:[/] [white on blue]{e}[/]")
            logger.error(f"Unexpected error loading config: {e}")
            raise ConfigurationError(f"Failed to load configuration: {e}")
        
        self.yaml = {}
        return self.yaml
    
    def _save_config(self, yaml_file: str = ''):
        """
        Save the current YAML configuration to the file.
        The function `_save_config` saves the current YAML configuration to a specified file in Python.
        
        :param yaml_file: The `yaml_file` parameter in the `_save_config` method is a string that
        represents the file path where the current YAML configuration will be saved. If no `yaml_file`
        is provided when calling the method, it will default to the value stored in `self.yaml_file`
        :type yaml_file: str
        """
        
        target = yaml_file or self.yaml_file
        if not target:
            raise ConfigurationError("No YAML file configured for saving")
        if self.yaml is None:
            self.yaml = {}
        try:
            p = Path(target)
            if not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.yaml, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.error("Error saving YAML config: %s", e)
            if _debug_enabled():
                _console.print(f":cross_mark: [white on red]Error saving YAML config:[/] [white on blue]{e}[/]")
            raise

    def dump(self, *args, **kwargs):
        """
        Dump the current YAML configuration.
        The `dump` function writes the current YAML configuration to a file in YAML format and returns
        the YAML data.
        :return: The `dump` method is returning the YAML configuration stored in `self.yaml`.
        """
        
        with open(self.yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.yaml, f, *args, **kwargs)
        return self.yaml

    def dumps(self, *args, **kwargs):
        """
        Dump the current YAML configuration to a string.
        The `dumps` function in Python dumps the current YAML configuration to a string using safe YAML
        dumping.
        :return: The `dumps` method is returning the current YAML configuration as a string using
        `yaml.safe_dump` with the provided arguments and keyword arguments.
        """
        
        return yaml.safe_dump(self.yaml, *args, **kwargs)

    def show(self):
        """
        Show the current YAML configuration.
        The function `show` displays the current YAML configuration using different methods based on
        available libraries.
        """
        
        if HAS_JSONCOLOR:
            jprint(self.yaml)
        elif HAS_RICH:
            _console.print(self.yaml)
        elif HAS_MAKECOLOR:
            print(make_colors(self.yaml, 'lc'))
        else:
            print(yaml.safe_dump(self.yaml))

    def print(self):
        """
        The `print` function is defined to return the result of calling the `show` method on the object
        it is called with.
        :return: The `print` method is returning the result of calling the `show` method on the object
        itself.
        """
        
        return self.show()
    
    @property
    def filename(self):
        """
        Get the filename of the YAML configuration file.
        This function returns the filename of the YAML configuration file as a string.
        :return: The `filename` method is returning the filename of the YAML configuration file as a
        string.
        """
        
        return str(self.yaml_file)
    
    @property
    def config_file(self):
        """
        Get the configuration name (alias for filename).
        The `config_file` function returns the configuration name, which is an alias for the filename.
        :return: The method `config_file` is returning the value of `self.filename`, which is the
        configuration name or alias for the filename.
        """
        
        return self.filename
    
    @property
    def configname(self):
        """
        Get the configuration name (alias for filename).
        This function returns the configuration name, which is an alias for the filename.
        :return: The method `configname` is returning the value of `self.filename`, which is the
        configuration name.
        """
        
        return self.filename
    
    def exists(self, key):
        """
        Check if a configuration key exists.
        The function checks if a given key exists in a configuration dictionary.
        
        :param key: The `key` parameter in the `exists` method is the configuration key that you want to
        check for existence in the `yaml` dictionary. The method checks if the `key` exists in the
        `yaml` dictionary and returns `True` if it does, and `False` otherwise
        :return: The `exists` method is returning a boolean value. It returns `True` if the `key` exists
        in the dictionary `self.yaml`, and `False` otherwise.
        """
        
        if isinstance(self.yaml, dict):
            return key in self.yaml
        return False

    def get_config_file(self):
        """
        Get the filename of the YAML configuration file.
        This function returns the filename of the YAML configuration file as a string.
        :return: The filename of the YAML configuration file is being returned as a string.
        """
        
        return str(self.yaml_file)
    
    def set_config_file(self, config_file: str) -> bool:
        """
        Set a new configuration file path.

        The function `set_config_file` sets a new configuration file path if the file exists and loads
        the configuration.
        
        :param config_file: The `config_file` parameter is a string that represents the path to a
        configuration file. The function `set_config_file` is designed to set a new configuration file
        path by checking if the specified file exists and then loading the configuration from that file.
        If the file exists, it updates the `yaml
        :type config_file: str
        :return: The `set_config_file` method returns a boolean value - `True` if the provided
        `config_file` path is a valid file and the configuration is successfully loaded, and `False` if
        the `config_file` path is invalid.
        """
        
        if os.path.isfile(config_file):
            self.yaml_file = config_file  # Fix: was self.json_file
            self._load_config()
            return True
        else:
            _console.print("\n:cross_mark: [white on red]Invalid YAML File ![/]")  # Fix: was Json File
            return False
    
    def get_config(self, *keys, default=None):
        """
        Get configuration value by nested keys (YAML backend).

        Usage:
            get_config('a')                     -> top-level key 'a'
            get_config('a', 'b', 'c')           -> nested access a.b.c
            get_config('a.b.c')                 -> single composite key (dot or :;| separators supported)
            get_config(['a','b','c'])           -> list/tuple of keys
            get_config(...)                     -> returns `default` if key path not found

        This method mirrors ConfigSetJson.get_config: accepts mixed positional arguments
        and composite keys containing separators. Any argument that contains separators
        will be split into segments and injected in-place (e.g. get_config('k1', 'k2.k3:k4', 'k5')
        becomes ['k1','k2','k3','k4','k5']).
        """
        
        if default and isinstance(default, bytes):
            default = default.decode()
        
        if default and isinstance(default, str) and str(default).isdigit():
            default = int(default)
        
        if default and isinstance(default, str) and str(default).replace(".", "").isdigit():
            default = float(default)
        
        try:
            # No keys provided -> return default
            if not keys:
                return default

            # Handle single list/tuple argument (legacy callers)
            if len(keys) == 1 and isinstance(keys[0], (list, tuple)):
                keys = keys[0]

            # Build flattened list of path segments
            parts: List[str] = _flatten_keys(keys)
            if not parts:
                return default

            # Ensure YAML root is a mapping
            if not isinstance(self.yaml, dict):
                try:
                    self._load_config()
                except Exception:
                    self.yaml = {}
            if self.yaml is None:
                self.yaml = {}

            # Traverse the YAML structure safely
            current = self.yaml
            for seg in parts:
                if isinstance(current, dict) and seg in current:
                    current = current[seg]
                    if not current and default:
                        return default
                    elif not current and isinstance(default, bool):
                        return default
                    elif current and str(current).isdigit():
                        return int(current)
                else:
                    if _debug_enabled():
                        _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{seg}[/]")
                    return default

            return current

        except Exception as e:
            if _debug_enabled():
                _console.print(f"\n:cross_mark: [white on red]Error getting config:[/] [white on blue]{e}[/]")
            return default

    def get(self, *keys, default=None):
        """
        Get configuration value by key.
        The `get` function retrieves a configuration value by key.
        
        :param key: The `key` parameter in the `get` method is used to specify the configuration value
        that you want to retrieve from the configuration settings. When you call the `get` method with a
        specific `key`, it will return the corresponding configuration value associated with that key
        :return: The `get_config` method is being called with the `key` parameter, and the return value
        of this method is being returned.
        """
        
        return self.get_config(*keys, default=default)

    def get_document(self, *keys, default=None):
        """
        Get document configuration value by key.
        The `get_document` function retrieves a document configuration value by key.

        :param key: The `key` parameter in the `get_document` method is used to specify the document configuration value
        that you want to retrieve from the configuration settings. When you call the `get_document` method with a
        specific `key`, it will return the corresponding document configuration value associated with that key
        :return: The `get_config` method is being called with the `key` parameter, and the return value
        of this method is being returned.
        """

        return self.get_config(*keys, default=default)

    def read_config(self, *keys, default=None):
        """Read configuration value by key."""
        return self.get_config(*keys, default=default)
    
    # def write_config(self, key, value: str = '') -> bool:
    #     """Write configuration value to nested key."""
    #     try:
    #         keys = re.split(r"[:;|]", key)
    #         keys = [i.strip() for i in keys if i.strip()]

    #         if not keys:
    #             if _debug_enabled():
    #                 _console.print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
    #             return False

    #         d = self.yaml
    #         if len(keys) > 1:
    #             # Traverse self.yaml for nested keys
    #             for k in keys[:-1]:
    #                 if k not in d or not isinstance(d[k], dict):
    #                     d[k] = {}
    #                 d = d[k]
    #             d[keys[-1]] = value
    #         else:
    #             self.yaml[keys[0]] = value

    #         self._save_config()
    #         return True

    #     except Exception as e:
    #         if _debug_enabled():
    #             _console.print(f"\n:cross_mark: [white on red]Error writing config:[/] [white on blue]{e}[/]")
    #         return False
    
    def write_config(self, *keys, value: Any = None) -> bool:
        """
        Write configuration value by nested keys (YAML backend).

        Accepts:
          - write_config('a.b.c', 'value')
          - write_config('a','b','c', value='value')
          - write_config('a','b','c','value')  (last positional becomes value if value kw not used)

        Behavior:
          - flexible key formats: dotted or separators (.,:,;,|)
          - supports mixed positional args where any arg containing separators is split in-place
            (e.g. write_config('k1', 'k2.k3:k4', 'k5', 'v') -> path ['k1','k2','k3','k4','k5'])
          - normalizes root to a dict if None or not a mapping
          - returns True on success, False on error
        """
        
        try:
            parts_src = list(keys)

            # If caller passed value as last positional and didn't use keyword
            if value is None and len(parts_src) >= 2:
                # treat last positional as value
                value = parts_src.pop(-1)

            if not parts_src:
                if _debug_enabled():
                    _console.print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            # Normalize iterable (support single list/tuple arg or multiple args)
            if len(parts_src) == 1 and isinstance(parts_src[0], (list, tuple)):
                iterable = parts_src[0]
            else:
                iterable = parts_src

            # Flatten and split by separators using shared helper
            parts: List[str] = _flatten_keys(iterable)
            if not parts:
                if _debug_enabled():
                    _console.print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            # ensure root is a mapping
            if not isinstance(self.yaml, dict):
                self.yaml = {}

            # Traverse and set nested value
            d = self.yaml
            for k in parts[:-1]:
                if k not in d or not isinstance(d[k], dict):
                    d[k] = {}
                d = d[k]
            d[parts[-1]] = value

            # persist changes
            self._save_config()
            return True

        except Exception as e:
            if _debug_enabled():
                _console.print(f"\n:cross_mark: [white on red]Error writing YAML config:[/] [white on blue]{e}[/]")
            return False
        
    def set(self, *keys, value: Any = None):
        """
        Set configuration value by key.
        The function `set` sets a configuration value by key.
        
        :param value: The `value` parameter in the `set` method is used to specify the value that you
        want to set for the configuration key(s) provided as arguments. If no `value` is provided, it
        defaults to `None`
        :type value: Any
        :return: The `set` method is returning the result of calling the `write_config` method with the
        provided keys and value.
        """
        
        return self.write_config(*keys, value=value)

    def remove_value_anywhere(self, value):
        """
        Remove all occurrences of a value from the YAML structure.
        The function removes all occurrences of a specified value from a YAML structure.
        
        :param value: The code you provided is a method that removes all occurrences of a specified
        value from a YAML structure. The value to be removed is passed as an argument to the
        `remove_value_anywhere` method
        :return: The `remove_value_anywhere` method returns a boolean value indicating whether any
        occurrences of the specified `value` were found and removed from the YAML structure. If at least
        one occurrence was found and removed, the method returns `True`. Otherwise, it returns `False`.
        """
        
        # q = deque([self.yaml])  # Fix: was self.json
        # found = False
        # while q:
        #     current = q.popleft()
        #     if isinstance(current, dict):
        #         for k in list(current.keys()):
        #             if current[k] == value:
        #                 del current[k]
        #                 found = True
        #             elif isinstance(current[k], dict):
        #                 q.append(current[k])
        q = deque([self.yaml])
        found = False
        while q:
            current = q.popleft()
            if isinstance(current, dict):
                for k in list(current.keys()):
                    v = current.get(k)
                    if v == value:
                        del current[k]
                        found = True
                    elif isinstance(v, (dict, list)):
                        q.append(v)
            elif isinstance(current, list):
                i = 0
                while i < len(current):
                    v = current[i]
                    if v == value:
                        current.pop(i)
                        found = True
                        continue
                    if isinstance(v, (dict, list)):
                        q.append(v)
                    i += 1
        if found:
            self._save_config()
        return found
    
    def remove_config(self, *keys, value: Any = None) -> bool:
        """
        Remove configuration key or value (YAML backend).

        Usage:
          - remove_config('a:b:c')                      -> remove key c under a.b
          - remove_config('a','b','c')                  -> same as above
          - remove_config('a','b','c', value='v')       -> remove specific value or list item
          - remove_config('a','b','c','v')              -> last positional treated as value
          - remove_config(value='v')                    -> remove value anywhere (delegates)
          
        This method accepts mixed forms: multiple positional keys and composite keys that contain
        separators. Any argument that contains separators will be split into segments and those
        segments are injected in-place, so e.g. get_config('k1', 'k2.k3:k4', 'k5') becomes
        ['k1','k2','k3','k4','k5'].
        """
        
        # If caller passed only a value (no keys) -> delegate to remove_value_anywhere
        if not keys and value is not None:
            return self.remove_value_anywhere(value)

        try:
            parts_src = list(keys)

            # Support last-positional-as-value (consistent with write_config)
            if value is None and len(parts_src) >= 2:
                value = parts_src.pop(-1)

            if not parts_src:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
                return False

            # Normalize iterable (support single list/tuple arg or multiple args)
            if len(parts_src) == 1 and isinstance(parts_src[0], (list, tuple)):
                iterable = parts_src[0]
            else:
                iterable = parts_src

            # Flatten keys (split composite segments) using module helper
            parts: List[str] = _flatten_keys(iterable)
            if not parts:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
                return False

            # Ensure YAML root is a mapping
            if not isinstance(self.yaml, dict):
                try:
                    self._load_config()
                except Exception:
                    self.yaml = {}
            if self.yaml is None:
                self.yaml = {}

            d = self.yaml
            # Traverse to parent dict
            for k in parts[:-1]:
                if k in d and isinstance(d[k], dict):
                    d = d[k]
                else:
                    if _debug_enabled():
                        _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{k}[/]")
                    return False

            last_key = parts[-1]
            if last_key not in d:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{last_key}[/]")
                return False

            # Remove by key or by matching value
            if value is None:
                del d[last_key]
            else:
                if d[last_key] == value:
                    del d[last_key]
                elif isinstance(d[last_key], list) and value in d[last_key]:
                    d[last_key].remove(value)
                else:
                    return False

            self._save_config()
            return True

        except Exception as e:
            if _debug_enabled():
                _console.print(f"\n:cross_mark: [white on red]Error removing config:[/] [white on blue]{e}[/]")
            return False
        
    def remove_key(self, key: str) -> bool:
        """
        Remove key and its children (supports nested keys).
        
        This Python function removes a specified key and its children from a nested dictionary
        structure.
        
        :param key: The `key` parameter in the `remove_key` method is a string that represents the key
        to be removed along with its children. The method supports nested keys, meaning you can specify
        a key that includes multiple levels separated by `:`, `;`, or `|`. The method will split the
        :type key: str
        :return: The `remove_key` method returns a boolean value - `True` if the key and its children
        were successfully removed, and `False` if there was an error or if the key was not found.
        """
        
        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]
            if not keys:
                if _debug_enabled():
                    msg = "No key!"
                    _console.print(f"\n:cross_mark: [bold #FFFF00]{msg}[/]") if HAS_RICH else print(msg)
                return False

            d = self.yaml  # Fix: was self.json
            for k in keys[:-1]:
                if k in d and isinstance(d[k], dict):
                    d = d[k]
                else:
                    if _debug_enabled():
                        msg = f"Key not found: {k}"
                        _console.print(f"\n:cross_mark: [white on red]{msg}[/]") if HAS_RICH else print(msg)
                    return False

            last_key = keys[-1]
            if last_key not in d:
                if _debug_enabled():
                    msg = f"Key not found: {last_key}"
                    _console.print(f"\n:cross_mark: [white on red]{msg}[/]") if HAS_RICH else print(msg)
                return False

            del d[last_key]
            self._save_config()
            return True

        except Exception as e:
            if _debug_enabled():
                msg = f"Error removing key: {e}"
                _console.print(f"\n:cross_mark: [white on red]{msg}[/]") if HAS_RICH else print(msg)
            return False

    def remove_section(self, key: str):
        """
        The function `remove_section` is an alias for `remove_key` in Python.
        
        :param key: The `key` parameter in the `remove_section` method is a string that represents the
        key of the section that you want to remove from the data structure
        :type key: str
        :return: The `remove_section` method is returning the result of calling the `remove_key` method
        with the `key` parameter passed to the `remove_section` method.
        """
        
        return self.remove_key(key)
    
    def find1(self, key: str, value=None):
        """
        Find all keys that have the specified value.
        The function `find` searches for keys with a specified value in a dictionary-like structure and
        returns the corresponding key-value pair.
        
        :param key: The `find` method you provided is used to find all keys that have the specified
        value in a YAML structure. The `key` parameter is a string that represents the key or keys you
        want to search for in the YAML structure. It can be a single key or a combination of keys
        separated by
        :type key: str
        :param value: The `value` parameter in the `find` method is used to specify the value that you
        want to find within the keys. The method will search for keys that have this specified value and
        return those keys. If the `value` parameter is not provided, the method will return the value
        associated with
        :return: The `find` method returns a dictionary containing keys that have the specified value,
        or an empty dictionary if the key or value is not found.
        """
        
        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]
            if not keys:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
                return {}

            d = self.yaml
            for k in keys[:-1]:
                if isinstance(d, dict) and k in d:
                    d = d[k]
                else:
                    if _debug_enabled():
                        _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{k}[/]")
                    return {}

            last_key = keys[-1]
            
            if isinstance(d, dict) and last_key in d:
                found = d[last_key]
                if value is not None:
                    return found if found == value else {}
                return found
            else:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{last_key}[/]")
                return {}
        except Exception as e:
            if _debug_enabled():
                _console.print(f"\n: cross_mark: [white on red]Error finding key:[/] [white on blue]{key}[/]")
            return {}

    def find(self, *keys, value=None):
        """
        Find a value by nested keys (YAML backend).

        This method mirrors the JSON backend: it accepts mixed positional arguments and composite
        key strings which are split by separators into segments and injected in-place. Example:
        find('k1', 'k2.k3:k4', 'k5') -> ['k1','k2','k3','k4','k5'].

        Returns the found value or {} if not found. If `value` is provided, only returns the found
        value when it equals `value`, otherwise returns {}.
        
        Usage:
          - find('a') -> returns value at top-level key 'a' or {} if not found
          - find('a','b','c') -> nested access a.b.c
          - find('a.b.c') -> composite key string
          - find(['a','b','c']) -> list/tuple of keys
          - find(..., value=expected) -> returns matched value only when equal, otherwise {}
        """
        
        try:
            if not keys:
                return {}

            parts: List[str] = _flatten_keys(keys)
            if not parts:
                return {}

            # Ensure YAML root is available
            if not isinstance(self.yaml, dict):
                try:
                    self._load_config()
                except Exception:
                    self.yaml = {}
            d = self.yaml or {}

            for seg in parts[:-1]:
                if isinstance(d, dict) and seg in d:
                    d = d[seg]
                else:
                    if _debug_enabled():
                        _console.print(f"\n:cross_mark: [white on red]Key not found while traversing:[/] [white on blue]{seg}[/]")
                    return {}

            last_key = parts[-1]
            if isinstance(d, dict) and last_key in d:
                found = d[last_key]
                if value is None:
                    return found
                return found if found == value else {}
            else:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{last_key}[/]")
                return {}
        except Exception as e:
            if _debug_enabled():
                _console.print(f"\n:cross_mark: [white on red]Error in find():[/] [white on blue]{e}[/]")
            return {}
        
# This class likely extends or inherits from a class named ConfigSetYaml.
class ConfigSetYAML(ConfigSetYaml):
    """Alias for ConfigSetYaml with uppercase naming."""
    pass

class configsetyaml(ConfigSetYaml):
    """Alias for ConfigSetYaml with lowercase naming."""
    pass

# Aliases for different naming conventions
class ConfigSetJSON(ConfigSetJson):
    """Alias for ConfigSetJson with uppercase naming."""
    pass

class configsetjson(ConfigSetJson):
    """Alias for ConfigSetJson with lowercase naming."""
    pass

class ConfigSetIni(configparser.RawConfigParser): # type: ignore
    """
    ConfigSetIni
    ============
    Lightweight configuration manager built on configparser.RawConfigParser that
    adds convenient file handling, automatic type conversion, list/dict parsing,
    and auto-write behaviour.
    Key features
    ------------
    - Manages an INI-formatted configuration file (also recognizes .json for
        pretty-printing).
    - Automatically determines a default .ini file based on the running script
        name if no file is provided.
    - Optional auto-write: will create the config file and persist default values
        the first time they are accessed if requested.
    - Transparent type conversion for stored string values (booleans, ints,
        floats; preserves non-numeric strings).
    - Helpers to read values as lists or dictionaries from several textual forms,
        including JSON arrays/objects and common delimiters.
    - Convenience aliases for backwards compatibility: get/read_config, set/write_config,
        remove_section/remove_config.
    - Good error handling for file access (FileNotFoundError, PermissionError,
        UnicodeDecodeError) and logging integration.
    Initialization
    --------------
    ConfigSetIni(config_file: str = '', auto_write: bool = True,
                             config_dir: str = '', config_name: str = '', **kwargs)
    Parameters:
    - config_file: Path to the configuration file. If empty, defaults to an .ini
        file named after the running script. A trailing '.ini' will be added if
        omitted. Stored internally as a pathlib.Path in self._config_file_path.
    - auto_write: When True, missing options queried with auto-write enabled will
        be written to disk with the provided default value.
    - config_dir: If provided, used as a directory in which to place the
        configuration file. If the directory does not exist it will be created.
    - config_name: Optional name used when config_dir is supplied; otherwise the
        resolved config_file path/name is used.
    - **kwargs: Additional kwargs passed to RawConfigParser (e.g. interpolation
        settings).
    Properties / Attributes
    -----------------------
    - filename, config_file, configname: All return the absolute path of the
        current configuration file as a string (aliases).
    - _config_file_path (pathlib.Path): internal resolved path object.
    - config_name (pathlib.Path): resolved file name used when config_dir is set.
    - _auto_write (bool): instance-level default for write-on-read behavior.
    Primary methods
    ---------------
    - get_config(section: str, option: str, default: Any = None, auto_write: bool = False) -> Any
        Retrieve an option with automatic conversion. If the option or section does
        not exist and auto_write is True, writes the provided default (or empty
        string) to disk and returns it.
        Conversion rules:
            - 'true', 'yes', '1' -> True
            - 'false', 'no', '0' -> False
            - Digit-only -> int
            - Strings containing '.' -> float (if parseable)
            - Otherwise returns stripped string
    - get(section, option, default=None, auto_write=True) -> Any
        Alias for get_config for backwards compatibility.
    - read_config(*args, **kwargs)
        Alias forwarding to get_config (maintains some historical API).
    - write_config(section: str, option: str, value: Any = '') -> Any
        Write a value to the given section and option, create section if needed,
        persist to the configured file, and return the stored value (with conversion
        applied by get_config when re-read).
    - set(section: str, option: str, value: Any = '') -> Any
        Alias for write_config.
    - exists(section, option) -> bool
        Returns True if the option exists in the given section.
    - remove_config(section: str, option: str = '') -> bool
        Remove a specific option if option is provided, otherwise remove the entire
        section. Returns True if removal succeeded, False if the section/option was
        not found or an error occurred.
    - remove_section(section: str) -> bool
        Alias for remove_config(section) to remove an entire section.
    - get_config_as_list(section: str, option: str, default: Union[str, List] = None) -> List[Any]
        Parse a stored string value into a Python list. Supports:
            - JSON arrays (e.g. '["a", "b"]')
            - Comma-separated values: 'a, b, c'
            - Newline separated or whitespace separated tokens
            - Quoted tokens preserved as strings
        Each item is run through the same conversion rules as get_config.
    - get_config_as_dict(section: str, option: str, default: Dict = None) -> Dict[str, Any]
        Parse a stored string into a key:value mapping. Supports:
            - JSON objects (e.g. '{"k": "v"}')
            - Comma-separated key:value pairs, e.g. 'k1: v1, k2: v2'
        Values are converted via the standard conversion rules.
    - get_all_config(sections: List[str] = []) -> List[Tuple[str, Dict]]
        Return a list of (section_name, {option: converted_value, ...}) tuples for the
        requested sections or for all sections when no argument is provided.
    - find(query: str, case_sensitive: bool = True, verbose: bool = False) -> bool
        Search section names and option names for an exact match. If verbose is True
        matching items are printed (with color support when available). Returns True
        if any matches are found.
    Internal methods
    ----------------
    - _load_config() -> None
        Robust loader that calls RawConfigParser.read with utf-8 and handles:
        FileNotFoundError (logs warning), PermissionError (raises ConfigurationError),
        UnicodeDecodeError (raises ConfigurationError), and other unexpected errors.
    - _save_config() -> None
        Writes the in-memory configuration to the configured file path using utf-8.
        Errors are optionally printed when debug mode is enabled.
    - _convert_value(value: str) -> Any
        Centralized conversion routine used by getters to convert string values into
        booleans, integers, floats or leave as string.
    - _print_colored(text: str, element_type: str, value: str = '') -> None
        Helper to print colored output using rich or makecolor if available.
        Used by printing and verbose find/print_all_config flows.
    Error handling and logging
    --------------------------
    - Uses logger for warnings and errors around file operations.
    - Raises ConfigurationError (a custom exception expected to exist in the
        surrounding codebase) on critical failures that prevent accessing the file.
    - When attempting to set a non-existent config_file via set_config_file, a
        FileNotFoundError is raised after printing a warning.
    Behavioral notes
    ----------------
    - When initialized with auto_write=True the constructor will create the file
        if it does not exist. When auto_write is used on reads, missing entries will
        be written immediately (either as the provided default or as an empty string).
    - Option names preserve case (optionxform = str) and empty values are allowed
        (allow_no_value = True).
    - The class prefers to operate on an internally stored Path (self._config_file_path).
    - print_all_config has special JSON detection: if the file path ends with .json,
        it will attempt to pretty-print JSON data rather than INI contents.
    Examples
    --------
    Basic usage:
    >>> cfg = ConfigSetIni()                      # defaults to scriptname.ini
    >>> cfg.write_config('app', 'timeout', 30)
    >>> cfg.get_config('app', 'timeout')
    30
    Auto-write defaults on read:
    >>> cfg = ConfigSetIni(auto_write=True)
    >>> cfg.get_config('new_section', 'new_option', default='x')  # writes 'x' to disk
    'x'
    Lists and dicts:
    >>> cfg.set('data', 'hosts', '["a.example", "b.example"]')
    >>> cfg.get_config_as_list('data', 'hosts')
    ['a.example', 'b.example']
    >>> cfg.set('data', 'map', 'a:1, b:2')
    >>> cfg.get_config_as_dict('data', 'map')
    {'a': 1, 'b': 2}
    Searching and inspection:
    >>> cfg.find('app', case_sensitive=False)
    True
    >>> all_conf = cfg.get_all_config()
    >>> cfg.print_all_config()
    Integration notes
    -----------------
    - This class is intended to be included in applications that already provide:
        - logger (for logging warnings and errors)
        - ConfigurationError (for raising configuration-specific exceptions)
        - optional helpers: _console, _debug_enabled(), HAS_RICH, HAS_JSONCOLOR, HAS_MAKECOLOR
        - optional utilities used for colored printing and pretty JSON printing.
    Replace or stub those dependencies when using the class in isolation.
    """
    
    def __init__(self, config_file: str = '', auto_write: bool = True, config_dir: str = '', config_name: str = '', **kwargs):
        super().__init__(**kwargs)
        
        self.allow_no_value = True
        self.optionxform = str
        
        # Determine config file path
        if not config_file:
            script_path = sys.argv[0] if sys.argv else 'config'
            config_file = os.path.splitext(os.path.realpath(script_path))[0] + ".ini"
        
        if not config_file.endswith('.ini'):
            config_file += '.ini'
            
        # Use _config_file_path to avoid property conflict
        self._config_file_path = Path(config_file).resolve()
        self.config_name = Path(config_name).resolve() if config_name else self._config_file_path
        self._auto_write = auto_write
        
        # Create file if it doesn't exist and auto_write is enabled
        if not self._config_file_path.exists() and auto_write:
            self._config_file_path.touch()
        
        if config_dir:
            config_dir_path = Path(config_dir).resolve()
            if not config_dir_path.exists():
                config_dir_path.mkdir(parents=True, exist_ok=True)
            self._config_file_path = config_dir_path / self.config_name.name  
                
        # Load existing configuration
        if self._config_file_path.exists():
            self._load_config()
            if os.getenv('SHOW_CONFIGNAME'):
                _console.print(f":japanese_symbol_for_beginner: [#FFFF00]CONFIG FILE:[/] [bold #00FFFF]{self._config_file_path}[/]")

    @property
    def filename(self) -> str:
        """Get absolute path of INI config file."""
        return str(self._config_file_path)
    
    @property
    def config_file(self) -> str:
        """Get absolute path of INI config file."""
        return str(self._config_file_path)
    
    @property
    def configname(self) -> str:
        """Get absolute path of INI config file."""
        return str(self._config_file_path)
    
    def get_config_file(self):
        """Get the filename of the INI configuration file."""
        return str(self._config_file_path)

    def exists(self, section, option) -> bool:
        """Check if a configuration option exists."""
        return self.has_option(section, option)

    def set_config_file(self, config_file: str) -> None:
        """
        Change the configuration file and reload.
        
        The function `set_config_file` changes the configuration file path and reloads it if the file
        exists; otherwise, it raises a `FileNotFoundError`.
        
        :param config_file: The `config_file` parameter in the `set_config_file` method is a string that
        represents the path to the new configuration file that you want to set. This method is designed
        to change the configuration file to the specified one and then reload the configuration
        :type config_file: str
        """
        
        if config_file and Path(config_file).exists():
            self._config_file_path = Path(config_file).resolve()  # Fix: use _config_file_path
            self._load_config()
        else:
            _console.print(f":warning: [#FFFF00]Config file not found:[/] [#00FFFF]{config_file}[/]")
            raise FileNotFoundError(f"Config file not found: {config_file}")

    def _load_config(self) -> None:
        """
        The function `_load_config` loads configuration from a file with specific error handling.
        """

        if _debug_enabled():
            print(f"Loading config from: {self._config_file_path}, IS_FILE: {os.path.isfile(self._config_file_path)}")
            
        try:
            self.read(str(self._config_file_path), encoding='utf-8')
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self._config_file_path}")
            # Create empty config or use defaults
        except PermissionError:
            logger.error(f"Permission denied accessing: {self._config_file_path}")
            raise ConfigurationError(f"Cannot access config file: {self._config_file_path}")
        except UnicodeDecodeError as e:
            logger.error(f"Invalid encoding in config file: {e}")
            raise ConfigurationError(f"Config file has invalid encoding: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        
        try:
            with open(self._config_file_path, 'w', encoding='utf-8') as f:  # Fix: use _config_file_path
                self.write(f)
        except Exception as e:
            if _debug_enabled():
                _console.print(f":cross_mark: [white on red]Error saving config:[/] [white on blue]{e}[/]")

    def print_all_config(self, sections: List[str] = []) -> List[Tuple[str, Dict]]:
        """
        Print all configuration in a formatted way.
        
        Print the entire configuration in a human-readable, colorized format and return the parsed data.
        This method inspects the instance attribute self._config_file_path to determine the file
        type and prints the configuration to the console in a friendly way:
        - For INI-style files (anything not ending with ".ini"):
            - Calls self.get_all_config(sections) to obtain configuration as a list of
                (section_name, section_data) tuples.
            - Prints a header and each section using self._print_colored for consistent
                colorized formatting.
            - Returns the list of (section_name, section_data) tuples.
        Parameters
        ----------
        sections : List[str], optional
                A list of section names to pass to self.get_all_config when the configuration
                file is an INI-style file. Default is an empty list. Note: the default is a
                mutable list literal; callers who rely on avoiding shared-mutable defaults
                should pass an explicit list (or None and handle accordingly).
        Returns
        -------
        List[Tuple[str, Dict]] or Any
                - For INI files: a list of (section_name, section_data) tuples where
                    section_data is a mapping of option names to values.
                The exact returned type therefore depends on the configuration file format.
        Side effects
        ------------
        - Prints formatted output to the configured console (via _console and _print_colored).
        - May open and read the file located at self._config_file_path.
        - Calls self.get_all_config when handling INI files.
        Exceptions
        ----------
        - Other exceptions raised by helper methods (e.g. self.get_all_config or
            self._print_colored) may also propagate.
        Examples
        --------
        # Print entire INI config, limiting to specified sections:
        print_all_config(['default', 'logging'])
        """
        
        _console.print(f":japanese_symbol_for_beginner: [bold #FFFF00]CONFIG FILE:[/] [bold #00FFFF]{self._config_file_path}[/]")  # Fix: use _config_file_path
        
        _console.print(f":japanese_symbol_for_beginner: [bold #FFFF00]CONFIG INI:[/]")
        if _debug_enabled():
            print(f"self.config_file: {self.config_file}, IS_FILE: {os.path.isfile(self.config_file)}")
        if HAS_RICH and self.config_file and Path(self.config_file).exists():
            with open(self._config_file_path, 'r') as ini_file:
                syntax = Syntax(ini_file.read(), lexer='ini', theme='fruity')
                _console.print(syntax)
        else:
            data = self.get_all_config(sections)
            if _debug_enabled(): print(f"data: {data}")

            for section_name, section_data in data:
                self._print_colored(f"[{section_name}]", 'section')
                for option, value in section_data.items():
                    self._print_colored(f"  {option} = {value}", 'option', value)
        
        # print()
        
        return self.get_all_config()
    
    def show(self, *args, **kwargs):
        """Prints all configurations.

        Args:
            self(object): The object containing the configuration data.
            args(tuple): Additional positional arguments to be passed to print_all_config.
            kwargs(dict): Additional keyword arguments to be passed to print_all_config.

        Returns:
            None: This function does not return any value.

        Raises:
            Exception: Any exception raised by print_all_config will be propagated.
        """
        
        return self.print_all_config(*args, **kwargs)
        
    def get_section(self, section: str):
        """
        Return all options and values in a section as {section: {option: value, ...}}.
        If section does not exist, print error and return None.
        """
        if self.has_section(section):
            options = {opt: self.get_config(section, opt) for opt in self.options(section)}
            return {section: options}
        else:
            _console.print(f":x: [white on red]No section[/] [white on blue]'{section}'[/] [white on red]found ![/]")
            return None

    def print(self, section: str = '', option: str = '', default: str = '') -> Any:
        """
        Print configuration values to the configured console and return the requested data.

        Behavior:
        - If both `section` and `option` are provided:
            - Calls self.get_config(section, option, default, False).
            - Prints a single-line section header and the option/value pair:
                [<section>]
                  <option> = <value>
            - Returns the resolved value (or the `default` when get_config falls back).

        - If only `section` is provided:
            - Calls self.get_section(section) to retrieve all options for that section.
            - For each matching section (key) and its options (mapping), prints:
                [<section_key>]
                  <opt> = <val>
            - Returns the mapping returned by get_section (typically a dict of section -> {option: value}).
            - If no section is found, returns None and prints nothing.

        - If only `option` is provided:
            - Calls self.find(option) to locate that option across sections.
            - For each matching section (key) and its options (mapping), prints:
                [<section_key>]
                  <opt> = <val>
            - Returns the mapping returned by find (typically a dict of section -> {option: value}).
            - If nothing is found, returns None and prints nothing.

        - If neither `section` nor `option` is provided:
            - The method performs no action and returns None.

        Parameters
        - section (str): Name of the section to print or search within. Optional; default is ''.
        - option (str): Name of the option to print or search for. Optional; default is ''.
        - default (str): Fallback value used only when both section and option are provided and get_config cannot find a value.

        Returns
        - When both section and option are provided: the single configuration value (type depends on stored value).
        - When a section or an option search is performed: a dict mapping section names to option dictionaries, or None if nothing found.
        - None when nothing is requested (both parameters empty) or when no data is found for section/option queries.

        Notes
        - Output is written via the module's console object (internal _console.print) and formatted as shown above.
        - This method does not raise on missing data; it returns default (for get_config) or None for section/find misses.

        Examples
        1) Print a single option value (returns the value):
        >>> # Suppose get_config('database', 'host', 'localhost', False) -> 'db.example.com'
        >>> cfg.print('database', 'host')
        [database]
          host = db.example.com
        # Returns: 'db.example.com'

        2) Print all options for a section (returns a dict):
        >>> # Suppose get_section('logging') -> {'logging': {'level': 'INFO', 'file': '/var/log/app.log'}}
        >>> cfg.print('logging')
        [logging]
          level = INFO
          file = /var/log/app.log
        # Returns: {'logging': {'level': 'INFO', 'file': '/var/log/app.log'}}

        3) Find and print an option across all sections (returns a dict):
        >>> # Suppose find('timeout') -> {'network': {'timeout': '30'}, 'database': {'timeout': '60'}}
        >>> cfg.print(option='timeout')
        [network]
          timeout = 30
        [database]
          timeout = 60
        # Returns: {'network': {'timeout': '30'}, 'database': {'timeout': '60'}}

        4) Missing data behavior:
        >>> cfg.print('nosuch', 'key')
        # If get_config falls back to default 'x', prints:
        [nosuch]
          key = x
        # Returns: 'x'
        >>> cfg.print('no-section')
        # If get_section('no-section') returns None, prints nothing and returns None
        """
        
        if section and option:
            value = self.get_config(section, option, default, False)
            _console.print(f"[{section}]\n  {option} = {value}")
            return value
        elif section and not option:
            section_found = self.get_section(section)
            if section_found:
                for sec, opts in section_found.items():
                    _console.print(f"[{sec}]")
                    for opt, val in opts.items():
                        _console.print(f"  {opt} = {val}")
            return section_found
        elif not section and option:
            data_found = self.find(option)
            if data_found:
                for sec, opts in data_found.items():
                    _console.print(f"[{sec}]")
                    for opt, val in opts.items():
                        _console.print(f"  {opt} = {val}")
            return data_found
        else:
            return self.print_all_config()
        
    def get_config(self, section: str, option: str, 
                  default: Any = None, auto_write: bool = False) -> Any:
        """
        Get configuration value with automatic type conversion.
        This method retrieves a configuration value, applying type conversion as needed.

        Args:
            section: Configuration section name
            option: Configuration option name  
            default: Default value if option doesn't exist
            auto_write: Override instance auto_write setting, default `False`
            
        Returns:
            Configuration value with appropriate type conversion
        """
        
        if auto_write is None:
            auto_write = self._auto_write
            
        try:
            value = super().get(section, option)
            return self._convert_value(value)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if auto_write and default is not None:
                self.write_config(section, option, default)
                return default
            elif auto_write and default is None:
                # If no default is provided, write an empty value
                self.write_config(section, option, '')
                return ''
            return default
        
    def get(self, section: str, option: str, 
             default: Any = None, auto_write: bool = True) -> Any:
        """
        Alias for get_config to maintain compatibility with previous versions.
        this method defaults auto_write to True.
        
        Args:
            section: Configuration section name
            option: Configuration option name
            default: Default value if option doesn't exist
            auto_write: Override instance auto_write setting, default `True`
            
        Returns:
            Configuration value with appropriate type conversion
        """
        return self.get_config(section, option, default, auto_write)

    def read_config(self, *args, **kwargs):
        """Reads the configuration.

        Args:
            self(self): The instance of the class.
            args(tuple): Variable length argument list.
            kwargs(dict): Variable length keyword argument dictionary.

        Returns:
            dict: The configuration dictionary.

        Raises:
            FileNotFoundError: Raised when the configuration file is not found.
            ValueError: Raised when the configuration file is invalid.
        """
        return self.get_config(*args, **kwargs)

    def write_config(self, section: str, option: str = '', value: Any = '') -> Any:
        """
        Write or update a configuration value in the INI-backed ConfigSet.
        This method accepts a variety of input types and normalizes them before
        writing into the underlying INI-like configuration store. It guarantees the
        section exists, converts many Python types to appropriate string representations,
        and can expand dictionary values into multiple options.
        Behavior summary
        - Ensures the requested section exists (adds it if missing).
        - Converts bytes values to UTF-8 strings.
        - For list values (or string representations of lists), joins the elements by
            a single space and stores the result as a single option value.
        - For dict values (or JSON string representations of dicts), writes each dict
            key as a separate option in the same section (value becomes option value).
            Only 1-level dicts are supported; nested dicts trigger a warning but the
            top-level keys are still written individually.
        - For string values that look like a list (starts with "[" and ends with "]"),
            attempts ast.literal_eval() to parse into a list before joining.
        - For string values that look like a dict (starts with "{" and ends with "}"),
            attempts json.loads() to parse into a dict before expanding into multiple
            options.
        - None is treated as an empty string.
        - Any parsing failures emit UserWarning and (if enabled) debug console messages;
            the original value is written as-is when parsing fails.
        - The configuration is saved by calling self._save_config() before returning.
        - The method returns the stored value via self.get_config(section, option).
        Parameters
        - section (str): The INI section name to write into. If missing, it will be created.
        - option (str): The option name for single-value writes. When value is a dict
            (or parsed dict), this parameter is used only as the logical origin; each
            dict key becomes an option name under `section`.
        - value (Any, optional): Value to store. Supported types:
                - None -> written as empty string.
                - bytes -> decoded as UTF-8 string.
                - str -> stored as-is, except when it appears to be a serialized list or
                    JSON object (see rules above), in which case it will be parsed and
                    handled accordingly.
                - list -> elements joined by a single space and written as one option.
                - dict -> each top-level key/value pair becomes an option/value in `section`.
                    Nested dicts are not supported (depth > 1 triggers a warning but keys are
                    still written individually).
        Returns
        - Any: The value read back from the configuration using self.get_config(section, option).
            Note: when a dict was provided (or parsed) multiple options are written; the
            returned value corresponds to the provided `option` key (which may be absent
            if the dict did not include it).
        Warnings and side-effects
        - Emits UserWarning for parse failures, nested dicts, or other recoverable issues.
        - Option and section creation/modification are performed in-place.
        - Calls self._save_config() to persist changes.
        - Emits debug output via internal debug/console helpers when enabled.
        Examples
        - Write a simple string:
                >>> config.write_config('server', 'host', 'example.com')
        - Write a list (stored as space-separated string):
                >>> config.write_config('paths', 'modules', ['mod1', 'mod2', 'mod3'])
                # stored as: "mod1 mod2 mod3"
        - Write a stringified list (parsed and stored as above):
                >>> config.write_config('paths', 'modules', "['mod1', 'mod2']")
        - Write a single option with bytes:
                >>> config.write_config('auth', 'token', b'secret')
        - Write a dict (each key becomes an option in the section):
                >>> config.write_config('db', 'unused_option', {'host': 'localhost', 'port': 5432})
                # results: section [db] contains options host=localhost and port=5432
        - Write a JSON string representing a dict:
                >>> config.write_config('db', 'unused', '{"user":"alice","pwd":"s3cr3t"}')
        Notes
        - When passing a dict, the `option` argument is not used to group the dict;
            instead dict keys become option names. If you need to store a dict as a single
            option, serialize it yourself (e.g., as JSON) and provide it as a string value.
        - to ensure dict as valid section-option then use dict with 1 level instead of nested dict.
        """
        
        def _write(section, option, value):
            # Convert value to string for storage
            str_value = str(value) if value is not None else ''
            # super().set(section, option, str_value)
            try:
                super().set(section, option, str_value)
            except configparser.NoSectionError:
                super().add_section(section)
                super().set(section, option, str_value)
            except configparser.NoOptionError:
                super().set(section, option, str_value)
        
        # ensure dict is only 1-level deep
        def _dict_depth(d):
            if not isinstance(d, dict):
                return 0
            max_child = 0
            for v in d.values():
                if isinstance(v, dict):
                    max_child = max(max_child, _dict_depth(v))
            return 1 + max_child

        if not self.has_section(section):
            self.add_section(section)
        
        if value is None:
            value = ''
        
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        if isinstance(value, list):
            value = " ".join(value)
            _write(section, option, value)
        elif isinstance(value, str) and value.strip().startswith("[") and value.strip().endswith("]"):
            try:
                value = ast.literal_eval(value)
                value = " ".join(value)
                _write(section, option, value)
            except Exception as e:
                if _debug_enabled():
                    _console.print(f":warning: [bold #00FFFF]ConfigSetIni:[/] [white on red]Failed to parse list[/] [white on blue]{section}:{option}[/] -> [white on red]{e}[/]")
                warnings.warn(f"ConfigSetIni: Failed to parse list for INI value: {e}", UserWarning)
                _write(section, option, value)
                
        elif isinstance(value, str) and value.strip().startswith("{") and value.strip().endswith("}"):
            # Attempt to parse stringified dict
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict) and _dict_depth(parsed) == 1:
                    value = parsed
                    for key in value:
                        _write(section, key, value[key])
                elif isinstance(parsed, dict) and _dict_depth(parsed) > 1:
                    msg = "INI value must be a 1-level dict (no nested dicts)."
                    if _debug_enabled():
                        _console.print(f":warning: [white on red]{msg}[/] [white on blue]{section}:{option}[/]")
                    warnings.warn(msg + ", write as it is", UserWarning)
                    for key in parsed:
                        _write(section, key, parsed[key])
                else:
                    msg = "INI value not a valid dictionary."
                    if _debug_enabled():
                        _console.print(f":warning: [white on red]{msg}[/] [white on blue]{section}:{option}[/]")
                    warnings.warn(msg + ", write as it is", UserWarning)
                    _write(section, option, value)
            except json.JSONDecodeError:
                if _debug_enabled():
                    _console.print(f":warning: [bold #00FFFF]ConfigSetIni:[/] [white on red]Failed to parse JSON[/] [white on blue]{section}:{option}[/]")
                warnings.warn("ConfigSetIni: Failed to parse JSON for INI value", UserWarning)
            except Exception as e:
                if _debug_enabled():
                    _console.print(f":warning: [bold #00FFFF]ConfigSetIni:[/] [white on red]Failed to process value[/] [white on blue]{section}:{option}[/]")
                warnings.warn(f"ConfigSetIni: Failed to process INI value: {e}", UserWarning)
                
        elif isinstance(value, dict):
            
            if _dict_depth(value) > 1:
                msg = "INI value must be a 1-level dict (no nested dicts)."
                if _debug_enabled():
                    _console.print(f":warning: [white on red]{msg}[/] [white on blue]{section}:{option}[/]")
                warnings.warn(msg + ", write as it is", UserWarning)
                for key in value:
                    _write(section, key, value[key])
            else:
                for key in value:
                    _write(section, key, value[key])

        self._save_config()

        return self.get_config(section, option)
    
    def set(self, section: str, option: str, value: Any = '') -> Any:
        """
        Alias for write_config to maintain compatibility with previous versions.
        
        Args:
            section: Configuration section name
            option: Configuration option name
            value: Value to write
            
        Returns:
            The written value
        """
        return self.write_config(section, option, value)
    
    def remove_config(self, section: str, option: str = '') -> bool:
        """
        Remove configuration section or specific option.
        
        Args:
            section: Configuration section name
            option: Configuration option name (optional)
                   If None, removes entire section
                   If specified, removes only that option from section
                   
        Returns:
            True if successfully removed, False if section/option not found
        """
        # print(f"section: {section}, option: {option}")
        try:
            if option is None:
                # Remove entire section
                if self.has_section(section):
                    super().remove_section(section)
                    self._save_config()
                    if _debug_enabled():
                        print(f"Removed section: [{section}]")
                    return True
                else:
                    if _debug_enabled():
                        print(f"Section not found: [{section}]")
                    return False
            else:
                # Remove specific option from section
                if self.has_section(section):
                    if self.has_option(section, option):
                        super().remove_option(section, option)
                        self._save_config()
                        if _debug_enabled():
                            print(f"Removed option: [{section}] {option}")
                        return True
                    else:
                        if _debug_enabled():
                            print(f"Option not found: [{section}] {option}")
                        return False
                else:
                    if _debug_enabled():
                        print(f"Section not found: [{section}]")
                    return False
        except Exception as e:
            if _debug_enabled():
                print(f"Error removing config: {e}")
            return False

    def remove_section(self, section: str) -> bool:
        """Remove a specific section from the configuration.

        Args:
            self(ConfigManager): Instance of the ConfigManager class.
            section(str): Name of the section to remove.

        Returns:
            bool: True if the section was successfully removed, False otherwise.

        Raises:
            KeyError: If the specified section does not exist.
        """
        return self.remove_config(section)
    
    def get_config_as_list(self, section: str, option: str, 
                          default: Union[str, List] = None) -> List[Any]: # type: ignore
        """
        Get configuration value as a list, parsing various formats.
        
        Supports formats:
        - Comma-separated: item1, item2, item3
        - Newline-separated: item1\nitem2\nitem3
        - JSON arrays: ["item1", "item2", "item3"]
        - Mixed formats with type conversion
        
        Args:
            section: Configuration section name
            option: Configuration option name
            default: Default value if option doesn't exist
            
        Returns:
            List of parsed values with type conversion
        """
        if default is None:
            default = []
        elif isinstance(default, str):
            default = [default]
            
        raw_value = self.get_config(section, option, str(default), auto_write=False)
        if not raw_value:
            return default
            
        # Handle string representation of lists
        if isinstance(raw_value, str):
            # Try to parse as JSON first
            if raw_value.strip().startswith('[') and raw_value.strip().endswith(']'):
                try:
                    return json.loads(raw_value)
                except json.JSONDecodeError:
                    pass
            
            # Split by common delimiters
            items = re.split(r'\n|,\s*|\s+', raw_value)
            items = [item.strip() for item in items if item.strip()]
            
            # Convert types for each item
            result = []
            for item in items:
                # Handle quoted strings
                if (item.startswith('"') and item.endswith('"')) or \
                   (item.startswith("'") and item.endswith("'")):
                    result.append(item[1:-1])
                else:
                    result.append(self._convert_value(item))
            
            return result
        
        return default if isinstance(default, list) else [default]

    def get_config_as_dict(self, section: str, option: str,
                          default: Dict = None) -> Dict[str, Any]: # type: ignore
        """
        Get configuration value as dictionary, parsing key:value pairs.
        
        Supports formats:
        - key1:value1, key2:value2
        - JSON objects: {"key1": "value1", "key2": "value2"}
        
        Args:
            section: Configuration section name
            option: Configuration option name
            default: Default dictionary if option doesn't exist
            
        Returns:
            Dictionary with parsed key-value pairs
        """
        if default is None:
            default = {}
            
        raw_value = self.get_config(section, option, str(default), auto_write=False)
        if not raw_value:
            return default
            
        if isinstance(raw_value, str):
            # Try JSON first
            if raw_value.strip().startswith('{') and raw_value.strip().endswith('}'):
                try:
                    return json.loads(raw_value)
                except json.JSONDecodeError:
                    pass
            
            # Parse key:value pairs
            result = {}
            pairs = re.split(r',\s*', raw_value)
            
            for pair in pairs:
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    result[key] = self._convert_value(value)
            
            return result
        
        return default
    
    def find(self, query: str, case_sensitive: bool = True, 
             verbose: bool = False) -> bool:
        """
        Search for sections or options matching the query.
        
        Args:
            query: Search term
            case_sensitive: Whether to perform case-sensitive search
            verbose: Print found items
            
        Returns:
            True if any matches found, False otherwise
        """
        if not query:
            return False
            
        found = []
        search_query = query if case_sensitive else query.lower()
        
        for section_name in self.sections():
            section_match = section_name if case_sensitive else section_name.lower()
            
            # Check section name match
            if search_query == section_match:
                found.append(('section', section_name))
                if verbose:
                    self._print_colored(f"[{section_name}]", 'section')
            
            # Check options in section
            try:
                for option in self.options(section_name):
                    option_match = option if case_sensitive else option.lower()
                    if search_query == option_match:
                        found.append((section_name, option))
                        if verbose:
                            value = super().get(section_name, option)
                            self._print_colored(f"[{section_name}]", 'section')
                            self._print_colored(f"  {option} = {value}", 'option', value)
            except Exception:
                if _debug_enabled():
                    print(f"Error searching section {section_name}: {traceback.format_exc()}")
        
        return found
    
    def get_all_config(self, sections: List[str] = []) -> List[Tuple[str, Dict]]:
        """
        Get all configuration data, optionally filtered by sections.
        
        Args:
            sections: List of section names to include (None for all)
            
        Returns:
            List of (section_name, options_dict) tuples
        """
        result = []
        target_sections = sections or self.sections()
        
        for section_name in target_sections:
            if not self.has_section(section_name):
                continue
                
            section_data = {}
            for option in self.options(section_name):
                section_data[option] = self.get_config(section_name, option)
            
            result.append((section_name, section_data))
        
        return result
        
    def _convert_value(self, value: str) -> Any:
        """Convert a string value to its appropriate type (bool, int, float, or str).

        Args:
            value(str): The string value to convert.

        Returns:
            Any: The converted value (bool, int, float, or str).

        Raises:
            ValueError: If the string cannot be converted to a float.
        """
        
        
        if not isinstance(value, str):
            return value
            
        value = value.strip()
        
        # Boolean conversion
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False
        
        # Numeric conversion
        if value.isdigit():
            return int(value)
        
        # Try float conversion
        try:
            if '.' in value:
                return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _print_colored(self, text: str, element_type: str, value: str = '') -> None:
        """Print text with colors if available."""
        if element_type == 'section':
            if HAS_RICH:
                _console.print(f"[bold cyan]{text}[/]")
            elif HAS_MAKECOLOR:
                print(make_colors(text, 'lc'))
            else:
                print(text)
        elif element_type == 'option':
            if HAS_RICH:
                _console.print(f"[yellow]{text}[/]")
            elif HAS_MAKECOLOR:
                print(make_colors(text, 'ly'))
            else:
                print(text)
        else:
            print(text)

class ConfigSetINI(ConfigSetIni):
    """Alias for ConfigSetIni with uppercase naming."""
    pass

class configsetini(ConfigSetIni):
    """Alias for ConfigSetIni with lowercase naming."""
    pass

class ConfigSet:    
    def __new__(cls, config_file: str = '', auto_write: bool = True, config_dir: str = '', config_name: str = '', **kwargs):
        """
        Initialize ConfigSet instance.
        
        If no config_file provided, or provided path does not exist, create a default file
        next to the parent module that imported this package (caller). Default format is JSON
        (filename: <caller_stem>.json) unless extension provided.
        
        Args:
            config_file: Path to configuration file
            auto_write: Whether to automatically create missing files/sections
            config_dir: Directory for configuration files
            config_name: Name of the configuration file
            **kwargs: Additional arguments passed to the underlying config parser
        """
        # Determine the final path (the same logic as it is now)
        file_path = config_file or ''
        
        if config_dir:
            file_path = os.path.join(config_dir, config_name or config_file)
        
         # If no path provided, derive from caller module (the importer)
        # if not file_path:
        #     caller_file = None
        #     for frame_info in inspect.stack()[1:]:
        #         try:
        #             module = inspect.getmodule(frame_info.frame)
        #         except Exception:
        #             module = None
        #         # choose first frame outside this module
        #         if module and module.__name__ != __name__:
        #             caller_file = Path(frame_info.filename).resolve()
        #             break
        #     if caller_file:
        #         default_name = caller_file.stem + ".ini"
        #         file_path = str(caller_file.parent / default_name)
        #     else:
        #         # fallback to cwd/config.json
        #         file_path = str(Path.cwd() / "config.ini")
        
        if _debug_enabled(): print(f"file_path [1]: {file_path}")
        if not file_path:
            # Prefer explicit program name if available (main script)
            prog = None
            if sys.argv and sys.argv[0]:
                try:
                    prog_path = Path(sys.argv[0]).resolve()
                    if prog_path.exists() and prog_path.suffix:
                        prog = prog_path
                except Exception:
                    prog = None

            caller_file = None
            pkg_dir = Path(__file__).parent.resolve()
            # scan stack but skip frames inside site-packages/dist-packages and this package
            for frame_info in inspect.stack()[1:]:
                try:
                    filename = Path(frame_info.filename).resolve()
                except Exception:
                    continue
                parts = [p.lower() for p in filename.parts]
                # skip frames that are inside site-packages / dist-packages or inside this package dir
                if 'site-packages' in parts or 'dist-packages' in parts or pkg_dir in filename.parents:
                    continue
                # skip internal configset frames
                if filename == Path(__file__).resolve():
                    continue
                caller_file = filename
                break

            # prefer program path, then selected caller frame, else cwd fallback
            base = prog or caller_file or Path.cwd() / "config"
            default_name = base.stem + ".ini"
            file_path = str(base.parent / default_name)

        if _debug_enabled(): print(f"file_path [2]: {file_path}")
        # If given path is a directory, place config file inside it
        p = Path(file_path)
        if p.is_dir():
            name = config_name or (Path(sys.argv[0]).stem if sys.argv and sys.argv[0] else "config")
            p = p / f"{name}.json"
            file_path = str(p)

        # Ensure parent dir exists and create file if missing
        try:
            p = Path(file_path)
            if not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists():
                # create minimal content based on suffix
                ext = p.suffix.lower()
                if ext in (".yaml", ".yml"):
                    p.write_text("{}", encoding="utf-8")
                elif ext == ".ini":
                    p.write_text("", encoding="utf-8")
                else:
                    # default to JSON
                    p.write_text("{}", encoding="utf-8")
        except Exception:
            # ignore creation errors here, downstream code will raise if truly invalid
            pass

        # Detect file type (prefer content detection, fallback to extension, default json)
        
        file_type = detect_file_type(str(p)) or (
            "yaml" if p.suffix.lower() in (".yaml", ".yml") else
            "ini" if p.suffix.lower() == ".ini" else
            "json"
        )
        if _debug_enabled(): print(f"Detected file type for {p}: {file_type}")
        # if os.path.basename(file_path) == '__init__.ini':
        #     return None
        # avoid accidentally using package __init__ files (e.g. installed package paths)
        try:
            p_resolved = p.resolve()
        except Exception:
            p_resolved = p

        pkg_dir = Path(__file__).parent.resolve()
        # if target is an __init__ file that lives inside this package (or site-packages copy),
        # skip and return None to avoid creating/using a package __init__ as a config file.
        if p_resolved.stem == "__init__" and pkg_dir in p_resolved.parents:
            if _debug_enabled():
                _console.print(f":warning: Skipping package __init__ file as config target: {p_resolved}")
            return None

        if _debug_enabled():
            _console.print(f"Detected file type for {p_resolved}: {file_type}")
        
        if file_type == 'json':
            return ConfigSetJSON(json_file=file_path, **kwargs)
        if file_type in ('yaml', 'yml'):
            return ConfigSetYAML(yaml_file=file_path, **kwargs)
        if file_path.endswith(".json"):
            return ConfigSetJSON(json_file=file_path, **kwargs)
        if file_path.endswith((".yaml", ".yml")):
            return ConfigSetYAML(yaml_file=file_path, **kwargs)
        
        return ConfigSetINI(config_file=file_path, auto_write=auto_write, config_dir=config_dir, config_name=config_name, **kwargs)

class configset(ConfigSet):
    pass

class ConfigMeta(type):
    """
    ConfigMeta(metaclass)
    Metaclass that manages a backend configuration object (ConfigSet) and dynamically
    exposes that backend's public callable API as classmethods on classes that use
    this metaclass. It centralizes file-based backend selection (INI/JSON/YAML),
    delegates attribute access/assignment to the underlying backend when appropriate,
    and provides a small convenience "show" helper to print configuration.
    Behavior summary
    - On class creation (__new__):
        - Determines a configuration filename from class attributes in this order:
          CONFIGFILE, configname, CONFIGNAME (case-insensitive handling is up to
          the user code that sets those attributes).
        - If the class provides a pre-instantiated `config` object with a
          set_config_file method, that object is used (and the file is set if
          provided). Otherwise, a ConfigSet instance is created from the filename.
        - The backend instance is stored on the class as `_config_instance`.
        - All public callable attributes of the backend (names not starting with '_')
          that are not already present on the class are wrapped and attached as
          classmethods that forward calls to the backend instance.
    - Attribute access (__getattr__):
        - If `_config_instance` exists and has the requested name:
            - If the backend attribute is callable, returns a wrapper that calls it.
            - Otherwise returns the attribute value directly.
        - If the class has a `data` mapping (e.g. dict) and the name exists there,
          returns data[name].
        - Otherwise raises AttributeError.
    - Attribute assignment (__setattr__):
        - Assignments to CONFIGFILE, CONFIGNAME, configname trigger backend swap or
          reconfiguration:
            - If the new value is truthy, attempts to create a new ConfigSet(new_value)
              and replace `_config_instance` so the proper backend (INI/JSON/YAML) is
              used for the new filename.
            - If creation fails, falls back to calling `set_config_file` on the
              existing backend instance if that method exists.
            - If both approaches fail, the attribute is set on the class normally.
        - All other assignments are performed with the normal class attribute logic.
        - If the environment variable DEBUG is set to "1", "true" or "True",
          the metaclass prints a small "Saving ...." message on every non-config
          assignment (this is intended for debugging and can be noisy).
    - show():
        - Convenience method that calls the backend's available "print" helper in
          preference order: print_all_config -> show -> print.
        - If no backend exists, returns None (and optionally logs an error in the
          application console).
    Notes and recommendations
    - The metaclass expects a ConfigSet-like backend that implements methods such
      as set_config_file and some read/write API. It will introspect public
      callables and make them available as classmethods, allowing calls such as
      Config.get('key') or Config.set('key', 'value') without needing to
      instantiate ConfigSet in user code.
    - Because the metaclass stores a mutable backend instance on the class
      (`_config_instance`), be cautious about concurrent mutations in multi-threaded
      applications. Consider synchronization or using immutable patterns if needed.
    - Assignment to the config filename attribute aims to swap backend implementations
      automatically; errors during swap are caught and fallbacks are attempted,
      but callers should be prepared to handle cases where the file cannot be used
      or backends cannot be created.
    - The metaclass suppresses exceptions when probing attributes on the backend
      (for robustness during import), so failures can be silent; enable careful
      logging or tests if you need strict failure modes.
    Usage examples (illustrative)
    - Basic class definition:
        class AppConfig(metaclass=ConfigMeta):
            CONFIGFILE = "settings.yaml"
        # call backend methods as classmethods:
        AppConfig.load()        # forwarded to backend.load()
        AppConfig.get("key")    # forwarded to backend.get("key")
    - Provide an existing backend instance:
        backend = SomeConfigBackend()
        class AppConfig(metaclass=ConfigMeta):
            config = backend
            CONFIGFILE = "settings.json"  # will call backend.set_config_file if available
    - Change configuration file at runtime:
        AppConfig.CONFIGFILE = "other.conf"  # attempts to replace backend or call set_config_file
    - Inspect or print configuration:
        AppConfig.show()  # uses backend.print_all_config/show/print in that order
    Return types and errors
    - Methods forwarded from the backend return whatever the backend returns.
    - AttributeError is raised by __getattr__ when a name is not found on either the
      backend nor the class `data` mapping.
    - Swapping backends on __setattr__ may raise exceptions from the ConfigSet
      constructor; these are caught and a fallback path is attempted instead.
    
    Metaclass for configuration management, dynamically exposing configuration options as class methods.
    
    Attributes:
        _config_instance(ConfigSet): Instance of ConfigSet used for configuration.
        configname(str): Optional: Configuration file name (alternative to CONFIGFILE).
        CONFIGNAME(str): Optional: Configuration file name (case-insensitive).
        CONFIGFILE(str): Configuration file name.
    """
    
    def __new__(mcs, name, bases, attrs):
        """Metaclass method to create a ConfigSet-based configuration class.

        Args:
            mcs(type): Metaclass of the class being created.
            name(str): Name of the class being created.
            bases(tuple): Tuple of base classes.
            attrs(dict): Dictionary of class attributes.

        Returns:
            object: The newly created class.

        Raises:
            Exception: Generic exception during config file handling or attribute access.
        """
        # debug(attrs = attrs)
        # Determine config file name from class attributes (if provided)
        config_file = attrs.get('CONFIGFILE') or attrs.get('configname') or ''

        # If caller provided a pre-instantiated `config` object that supports set_config_file => use it
        if 'config' in attrs and hasattr(attrs['config'], 'set_config_file'):
            config_instance = attrs['config']
            if config_file:
                try:
                    config_instance.set_config_file(config_file)
                except Exception:
                    pass
        else:
            # let ConfigSet detect the proper backend (INI / JSON / YAML)
            config_instance = ConfigSet(config_file)

        # store instance for class and instance usage
        attrs['_config_instance'] = config_instance

        # helper to build a classmethod proxy to an instance method
        def make_classmethod_from_instance(method_name, original=None):
            """Create a classmethod that calls an instance method of a configuration instance.

            Args:
                method_name(str): Name of the instance method to convert into a classmethod.

            Returns:
                classmethod: A classmethod that calls the specified instance method on the configuration instance.

            Raises:
                AttributeError: Raised if the configuration instance or the specified method does not exist.
                TypeError: Raised if the method_name is not a string.
            """
            def wrapper(cls, *args, **kwargs):
                """Wraps a method call on a configuration instance.

                Args:
                    cls(type): The class containing the configuration instance.
                    *args(Any): Variable length argument list to be passed to the wrapped method.
                    **kwargs(Any): Arbitrary keyword arguments to be passed to the wrapped method.

                Returns:
                    Any: The return value of the wrapped method.

                Raises:
                    AttributeError: Raised if the class does not have a _config_instance attribute or if the instance does not have the specified method.
                    TypeError: Raised if the method call fails due to type mismatch or other type-related errors.
                """
                inst = getattr(cls, '_config_instance')
                method = getattr(inst, method_name)
                return method(*args, **kwargs)
            
            # attempt to use the original callable to copy metadata
            if original is None:
                try:
                    original = getattr(config_instance, method_name)
                except Exception:
                    original = None
            if original:
                wrapper = wraps(original)(wrapper)
                
            wrapper.__name__ = method_name
            return classmethod(wrapper)

        # expose public callable attributes of the instance as classmethods
        for name in dir(config_instance):
            # if name.startswith('_'):
            #     continue
            if name in attrs:
                continue
            try:
                attr = getattr(config_instance, name)
            except Exception:
                continue
            if callable(attr):
                attrs[name] = make_classmethod_from_instance(name, original=attr)

        return super().__new__(mcs, name, bases, attrs)

    def __getattr__(cls, name):
        """Get attribute from class or its config instance or data.

        Args:
            cls(type): Class object
            name(str): Attribute name

        Returns:
            Any: Attribute value or None if not found.

        Raises:
            AttributeError: Raised if the attribute is not found in the class, its config instance, or data.
        """
        
        debug(cls__config_instance = cls._config_instance)
        if hasattr(cls, '_config_instance') and hasattr(cls._config_instance, name):
            attr = getattr(cls._config_instance, name)
            debug(attr = attr)
            if callable(attr):
                # return a wrapper that calls the instance method
                return lambda *args, **kwargs: attr(*args, **kwargs)
            return attr

        elif hasattr(cls, '_config_instance') and not str(name).isdigit() and isinstance(cls._config_instance, ConfigSetINI):
            if _debug_enabled(): print('configsetini instance ...')
            if hasattr(cls._config_instance, 'get_section'):
                return cls._config_instance.get_section(name)

        elif hasattr(cls, '_config_instance') and not str(name).isdigit() and isinstance(cls._config_instance, ConfigSetJSON):
            if _debug_enabled(): print('configsetjson instance ...')
            if hasattr(cls._config_instance, 'get_key'):
                return cls._config_instance.get_key(name)

        elif hasattr(cls, '_config_instance') and not str(name).isdigit() and isinstance(cls._config_instance, ConfigSetYAML):
            if _debug_enabled(): print('configsetyaml instance ...')
            if hasattr(cls._config_instance, 'get_document'):
                return cls._config_instance.get_document(name)

        if hasattr(cls, 'data') and name in cls.data:
            return cls.data[name] # type: ignore
            
        raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")

    def __setattr__(cls, name, value):
        """Sets an attribute in the class, handling special cases for configuration file names.

        Args:
            cls(object): The class instance.
            name(str): The name of the attribute to set.
            value(Any): The value to set the attribute to.

        Returns:
            None: No value is explicitly returned.

        Raises:
            Exception: If an error occurs while creating a new ConfigSet instance or setting the configuration file in the existing instance.
        """
        
        if name in ['configname', 'CONFIGNAME', 'CONFIGFILE']:
            # When the class config filename changes, replace the backend instance
            # so the proper ConfigSet backend (INI/JSON/YAML) is used.
            if value:
                try:
                    new_inst = ConfigSet(value)
                    cls._config_instance = new_inst
                    return
                except Exception:
                    # Fall back to asking existing instance to change file if possible
                    inst = getattr(cls, '_config_instance', None)
                    if inst is not None and hasattr(inst, 'set_config_file'):
                        try:
                            inst.set_config_file(value)
                            return
                        except Exception:
                            pass
            # If all else fails, set attribute normally
            super().__setattr__(name, value)
            return

        if os.getenv('DEBUG') in ['1', 'true', 'True']:
            print("Saving ....")
        super().__setattr__(name, value)

    # def show(cls):
    #     """Show current configuration."""
    #     if hasattr(cls, '_config_instance'):
    #         # prefer unified method names if available
    #         inst = cls._config_instance
    #         if hasattr(inst, 'print_all_config'):
    #             return inst.print_all_config() # type: ignore
    #         if hasattr(inst, 'show'):
    #             return inst.show()
    #         if hasattr(inst, 'print'):
    #             return inst.print()
    #     else:
    #         _console.print(":cross_mark: [white on red]No config instance found.[/]")
    #         return None
        
class CONFIG(metaclass=ConfigMeta):
    """
    CONFIG class
    A lightweight configuration container with optional JSON-backed persistence and
    attribute-style access. Instances provide a dictionary-like storage in the
    `data` attribute while allowing access and assignment via normal attribute
    syntax (e.g. cfg.some_key). When a class-level CONFIGFILE is provided, the
    configuration is mirrored to a JSON file (CONFIGFILE with a .json suffix)
    and is loaded on initialization.
    Behavior summary
    - Initialization:
        - If `config_file` is provided to __init__, a ConfigSet is created with it.
        - If the class-level CONFIGFILE is set, a corresponding .json file is used
          as the persistent storage. Existing JSON content is loaded into `data`.
        - If the JSON file does not exist, an empty file is created.
        - JSON load/save errors are printed when debugging is enabled.
    - Attribute access:
        - __getattr__ first looks up the name in `data` and returns it if present.
        - If a JSON-backed file is enabled and the attribute name is missing,
          __getattr__ auto-creates the key with an empty string, persists the file,
          and returns the empty string.
        - If the attribute is not found and no JSON backing is configured,
          an AttributeError is raised.
    - Attribute assignment:
        - __setattr__ writes non-private, non-internal names (not starting with '_'
          and not in the internal set ['data','config','CONFIGFILE','INDENT']) into
          `data`. If a JSON file is enabled the value is immediately persisted.
        - Assignments to private/internal attributes behave as normal instance
          attribute assignments.
        - If no JSON backing is configured, a warning is emitted on writes.
    Public attributes
    - CONFIGFILE (Optional[str]): Class-level path used to derive the JSON filename
      (suffixed with .json) when persistence is desired.
    - INDENT (int): JSON indentation level used when writing the file (default 4).
    - config (ConfigSet): A ConfigSet instance used by the class; may be replaced
      by passing `config_file` to the constructor.
    - data (Dict[str, Any]): In-memory mapping for all configuration keys and values.
    Notes
    - The class uses helper functions/objects such as _debug_enabled() and _console
      for debug/error reporting if present in the environment.
    - JSON reading/writing uses UTF-8 and ensure_ascii=False to preserve Unicode.
    - The class intentionally treats attribute access as the primary API; keys in
      `data` are accessible as attributes and persisted when appropriate.
    Example usage
    - Basic in-memory usage (no class CONFIGFILE set):
        cfg = CONFIG()             # no JSON file backing
        cfg.some_value = 123       # stored in cfg.data but not persisted
        assert cfg.some_value == 123
            _ = cfg.nonexistent    # raises AttributeError if not present
        except AttributeError:
            pass
    - JSON-backed usage (set class-level CONFIGFILE before instantiation):
        class MyConfig(CONFIG):
            CONFIGFILE = "C:/PROJECTS/configset/configset/configset"  # .json will be used
        cfg = MyConfig()                           # loads or creates configset.json
        print(cfg.data)                            # the loaded JSON as a dict
        cfg.username = "alice"                     # persisted immediately to the JSON file
        print(cfg.username)                        # "alice"
        # Accessing a missing attribute auto-creates an empty string in the JSON:
        print(cfg.new_key)                         # "" and cfg.data["new_key"] == ""
    - Passing a config file to the constructor:
        cfg = CONFIG(config_file="path/to/some/config")
        # this will initialize `config` (ConfigSet) with the provided file while
        # JSON persistence still depends on CONFIGFILE.
    Threading and concurrency
    - The class does not implement any internal locking for concurrent file access.
      If multiple processes or threads may write the same JSON file concurrently,
      external synchronization is recommended.
    Exceptions and warnings
    - JSON decoding and IO errors are caught during load/save; when debugging is
      enabled they are reported to the console. Save failures do not raise but will
      issue debug output.
    - Assigning attributes without JSON backing emits a Python Warning to notify
      that persistence is not available.
    """
    
    CONFIGFILE: Optional[str] = None
    INDENT: int = 4
    
    config = ConfigSet()
    data: Dict[str, Any] = {}
    
    def __init__(self, config_file: str = None): # type: ignore
        """Initialize the configuration.

        Args:
            config_file(str | None): Path to the configuration file. If None, defaults to using environment variables.

        Returns:
            None: No return value.

        Raises:
            json.JSONDecodeError: Raised if the JSON file is invalid.
            IOError: Raised if there is an error reading the JSON file.
        """
        
        if config_file:
            self.config = ConfigSet(config_file)
        elif self.CONFIGFILE:
            self.config = ConfigSet(config_file)
            self.config_file = self.CONFIGFILE
        
    def __getattr__(self, name: str) -> Any:
        """Get an attribute from the object, creating it if it does not exist and is in the json file.

        Args:
            name(str): Name of the attribute to get.

        Returns:
            Any: Value of the attribute.

        Raises:
            AttributeError: Raised if the attribute is not found and cannot be created.
        """
        
        if name in self.data:
            return self.data[name]
        elif hasattr(self, '_json_file') and name not in self.data:
            # Auto-create empty value
            self.data[name] = ''
            self._save_json()
            return ''
        _console.print(f":cross_mark: [white on red]Attribute not found:[/] [white on blue]{name}[/]")
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Set an attribute in the object, saving to JSON if applicable.

        Args:
            name(str): Attribute name.
            value(Any): Attribute value.

        Returns:
            None: No explicit return value.

        Raises:
            Warning: Issued if the object is not configured to support JSON configuration files.
        """
        
        if name.startswith('_') or name in ['data', 'config', 'CONFIGFILE', 'INDENT']:
            super().__setattr__(name, value)
        else:
            print(f"type(self.config): {type(self.config)}")
            self.data[name] = value
            if isinstance(self.config, ConfigSetJson) or isinstance(self.config, ConfigSetYaml):
                self.config.set(name, value)
            elif isinstance(self.config, ConfigSetIni):
                value = re.split(r"[:;| ]", value)
                if len(value) > 2:
                    self.config.set(name, dict(zip(value[::2], value[1::2])))
                else:
                    self.config.set(name, value[0])
            # if hasattr(self, '_json_file'):
            #     self._save_json()
            # else:
            #     warnings.warn("This only supports JSON configuration file!", Warning)

def create_argument_parser() -> argparse.ArgumentParser:
    """Create an argument parser for the configuration file management tool.

    Args:
        config_file(str): Path to the configuration file.
        -r, --read(bool): Read configuration values.
        -w, --write(bool): Write configuration values.
        -d, --delete, --remove(bool): Remove configuration section or option.
        -s, --section(str): Configuration section name (for INI files).
        -k, --key(str): Configuration key name (supports dot notation for nested keys).
        -o, --option(str): Configuration option name (alias for --key).
        -v, --value(str): Value to write (for write operations).
        --list(bool): Parse value as list (INI format only).
        --dict(bool): Parse value as dictionary (INI format only).
        --all(bool): Show all configuration.
        --show(bool): Show configuration with syntax highlighting.

    Returns:
        argparse.ArgumentParser: An ArgumentParser object configured for the configset tool.

    Raises:
        SystemExit: If the parser encounters an error during argument parsing.
    """
    
    parser = argparse.ArgumentParser(
        description="Configuration file management tool supporting INI, JSON, and YAML formats",
        formatter_class=CustomRichHelpFormatter if HAS_RICH else argparse.RawTextHelpFormatter,
        prog='configset'
    )
    
    parser.add_argument('config_file', 
                       help='Configuration file path')
    parser.add_argument('-r', '--read',
                       action='store_true',
                       help='Read configuration values')
    parser.add_argument('-w', '--write',
                       action='store_true', 
                       help='Write configuration values')
    parser.add_argument('-d', '--delete', '--remove',
                       action='store_true',
                       help='Remove configuration section or option')
    parser.add_argument('-s', '--section',
                       help='Configuration section name (for INI files)')
    parser.add_argument('-k', '--key',
                       help='Configuration key name (supports dot notation for nested keys)')
    parser.add_argument('-o', '--option',
                       help='Configuration option name (alias for --key)')
    parser.add_argument('-v', '--value',
                       help='Value to write (for write operations)')
    parser.add_argument('--list',
                       action='store_true',
                       help='Parse value as list (INI format only)')
    parser.add_argument('--dict',
                       action='store_true', 
                       help='Parse value as dictionary (INI format only)')
    parser.add_argument('--all',
                       action='store_true',
                       help='Show all configuration')
    parser.add_argument('--show',
                       action='store_true',
                       help='Show configuration with syntax highlighting')
    
    return parser

def main():
    """Main CLI interface function."""
    parser = create_argument_parser()
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    if not args.config_file:
        _console.print(":cross_mark: [white on redError:[/] [white on blue]Configuration file is required[/]")
        parser.print_help()
        return
    
    try:
        config = ConfigSet(args.config_file)
        
        # Determine the key to use (option or key)
        key = args.option or args.key
        
        if args.all or args.show:
            if hasattr(config, 'show'):
                config.show()
            elif hasattr(config, 'print_all_config'):
                config.print_all_config() # type: ignore
            else:
                _console.print(f":cross_mark: [white on red]Configuration display not supported for this file type.[/]")

        elif args.read:
            # Handle different file types
            if hasattr(config, 'get_config') and args.section:
                # INI file with section and option
                if not key:
                    _console.print(":cross_mark: [white on red]Error:[/] [white on blue]Key/option required for INI read operation[/]")
                    return
                    
                if args.list:
                    value = config.get_config_as_list(args.section, key) # type: ignore
                elif args.dict:
                    value = config.get_config_as_dict(args.section, key) # type: ignore
                else:
                    value = config.get_config(args.section, key)
                
                print(f"[{args.section}] {key} = {value}")
                
            elif hasattr(config, 'get_config') and not args.section:
                # JSON or YAML file with key only
                if not key:
                    _console.print(":cross_mark: [white on red]Error:[/] [white on blue]Key required for read operation[/]")
                    return
                    
                value = config.get_config(key) # type: ignore
                _console.print(f"{key} = {value}")
            else:
                _console.print(":cross_mark: [white on red]Error:[/] [white on blue]Unsupported read operation for this file type[/]")
                return
            
        elif args.write:
            # Handle different file types
            if hasattr(config, 'write_config') and args.section:
                # INI file with section and option
                if not key:
                    _console.print(":cross_mark: [white on red]Error:[/] [white on blue]Key/option required for INI write operation[/]")
                    return
                
                value = args.value or ''
                result = config.write_config(args.section, key, value)
                _console.print(f":white_check_mark: [white on green]Written:[/] [white on blue][{args.section}] {key} = {result}[/]")
                
            elif hasattr(config, 'write_config') and not args.section:
                # JSON or YAML file with key only
                if not key:
                    _console.print(":cross_mark: [white on red]Error:[/] [white on blue]Key required for write operation[/]")
                    return
                
                value = args.value or ''
                success = config.write_config(key, value)
                if success:
                    _console.print(f":white_check_mark: [white on green]Written:[/] [white on blue]{key} = {value}[/]")
                else:
                    _console.print(f":cross_mark: [white on red]Failed to write:[/] [white on blue]{key}[/]")
            else:
                _console.print(":cross_mark: [white on red]Error:[/] [white on blue]Unsupported write operation for this file type[/]")
                return
            
        elif args.delete:
            # Handle different file types
            if hasattr(config, 'remove_config') and args.section:
                # INI file
                if key:
                    # Remove specific option
                    success = config.remove_config(args.section, key)
                    if success:
                        _console.print(f":white_check_mark: [white on green]Removed:[/] [white on blue][{args.section}] {key}[/]")
                    else:
                        _console.print(f":cross_mark: [white on red]Not found:[/] [white on blue][{args.section}] {key}[/]")
                else:
                    # Remove entire section
                    success = config.remove_config(args.section)
                    if success:
                        _console.print(f":white_check_mark: [white on green]Removed section:[/] [white on blue][{args.section}][/]")
                    else:
                        _console.print(f":cross_mark: [white on red]Section not found:[/] [white on blue][{args.section}][/]")
            elif hasattr(config, 'remove_config') and not args.section:
                # JSON or YAML file
                if not key:
                    _console.print(":cross_mark: [white on red]Error:[/] [white on blue]Key required for delete operation[/]")
                    return
                    
                success = config.remove_config(key)
                if success:
                    _console.print(f":white_check_mark: [white on green]Removed:[/] [white on blue]{key}[/]")
                else:
                    _console.print(f":cross_mark: [white on red]Key not found:[/] [white on blue]{key}[/]")
            else:
                _console.print(":cross_mark: [white on red]Error:[/] [white on blue]Unsupported delete operation for this file type[/]")
                return
            
        else:
            _console.print(":cross_mark: [white on red]Error:[/] [white on blue]Specify --read, --write, --delete, --all, or --show[/]")
            parser.print_help()
            
    except Exception as e:
        _console.print(f":cross_mark: [white on red]Error:[/] [white on blue]{e}[/]")
        if _debug_enabled():
            traceback.print_exc()


if __name__ == '__main__':
    main()
