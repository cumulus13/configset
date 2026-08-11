#!/usr/bin/env python3

# File: configset_json.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-08-11
# Description: 
# License: MIT

import re
from pathlib import Path
import json
import os
from typing import Any, Callable, List, Tuple
from json import JSONDecoder, JSONEncoder

# configset_error
try:
    from . configset_error import ConfigurationError  # type: ignore
except:
    try:
        from configset_error import ConfigurationError  # type: ignore
    except:
        from configset.configset_error import ConfigurationError  # type: ignore

# printer
try:
    from . printer import _print, HAS_RICH, HAS_MAKE_COLORS, make_colors, HAS_JSONCOLOR, jprint  # type: ignore
except:
    try:
        from printer import _print, HAS_RICH, HAS_MAKE_COLORS, make_colors, HAS_JSONCOLOR, jprint  # type: ignore
    except:
        from configset.printer import _print, HAS_RICH, HAS_MAKE_COLORS, make_colors, HAS_JSONCOLOR, jprint  # type: ignore

# debugger
try:
    from . debugger import is_debug, tprint, logger  # type: ignore
except:
    try:
        from debugger import is_debug, tprint, logger  # type: ignore
    except:
        from configset.debugger import is_debug, tprint, logger  # type: ignore

# general
try:
    from . general import _flatten_keys, load_default, format_value, get_default  # type: ignore
except:
    try:
        from general import _flatten_keys, load_default, format_value, get_default  # type: ignore
    except:
        from configset.configset_general import _flatten_keys, load_default, format_value, get_default  # type: ignore


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
    - When a global debug mode is enabled via the project's helper (is_debug()),
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
        _console, logger, ConfigurationError, and boolean flags HAS_RICH, HAS_JSONCOLOR, HAS_MAKE_COLORS.
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
                 object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] = None, default: Any=None) -> None: # type: ignore
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
        self.default_config = {}
        if default:
            self.default_config = load_default(default)
        self.default = self.default_config # Object of type `dict[Unknown, Unknown] | Unknown` is not assignable to attribute `default` of type `def default(self, o: Any) -> Any`
        #info: element `dict[Unknown, Unknown]` of union `dict[Unknown, Unknown] | Unknown` is not assignable to `def default(self, o: Any) -> Any` (ty[invalid-assignment])

        self.json_obj = self.json.copy() if self.json else {} # Attribute `copy` is not defined on `str & ~AlwaysFalsy` in union `(dict[Any, Any] & ~AlwaysFalsy) | (Any & ~AlwaysFalsy) | (str & ~AlwaysFalsy) | (dict[Any | str, Any] & ~AlwaysFalsy)` (ty[unresolved-attribute])
    
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
            _print(f"\n:cross_mark: [white on red]JSON file not found:[/] [white on blue]{json_file}[/]")
            raise FileNotFoundError(f"JSON file not found: {json_file}")
        return self.json
    
    def _load_config(self, json_file=None) -> dict[Any, Any] | Any | str | dict[Any | str, Any]:
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
        
        if is_debug():
            _print(f"🔎 [bold #00FF00]Loading JSON config from:[/] [white on blue]{source}[/]")
        
        try:
            if os.path.isfile(source):
                with open(source, "r", encoding="utf-8") as f:
                    if is_debug():
                        _print(f"{source} -> f.read(): {f.read()}")
                    data = f.read().strip()
                    if not data:
                        self.json = {}
                        return self.json
                    self.json = json.loads(data)
            elif isinstance(source, str) and "{" in source.strip():
                self.json = json.loads(source)
            elif isinstance(source, bytes):
                self.json = json.loads(source.decode())
            else:
                if os.path.isfile(self.json_file):
                    with open(self.json_file, "r", encoding="utf-8") as f:
                        self.json = json.dumps(f, ensure_ascii=False, indent=4)
            return self.json
        
        except FileNotFoundError:
            if is_debug():
                _print(f"❌ [white on red]Config file not found:[/] [white on blue]{source}[/]")
            logger.warning(f"⚠ Config file not found: {source}")
            # Create empty config or use defaults
        except PermissionError:
            if is_debug():
                _print(f":cross_mark: [white on red]Permission denied accessing:[/] [white on blue]{source}[/]")
            logger.error(f"❌ Permission denied accessing: {source}")
            raise ConfigurationError(f"Cannot access config file: {source}")
        except UnicodeDecodeError as e:
            if is_debug():
                _print(f":cross_mark: [white on red]Invalid encoding in config file:[/] [white on blue]{e}[/]")
            logger.error(f"❌ Invalid encoding in config file: {e}")
            raise ConfigurationError(f"Config file has invalid encoding: {e}")
        except Exception as e:
            if is_debug():
                _print(f":cross_mark: [white on red]Unexpected error loading config:[/] [white on blue]{e}[/]")
            logger.error(f"❌ Unexpected error loading config: {e}")
            if os.getenv('traceback') in ['1', 'true', 'True']:
                _console.print_exception() # type: ignore
                
            raise ConfigurationError(f"❌ Failed to load configuration: {e}")
        return {}
    
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

    def _save_config(self, data=None, force_write = False, **kwargs) -> List:
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
        # self.json = self._load_config(json_file)
        
        _self_json = {}

        if is_debug():
            _print(f":info: data = {data}, force_write = {force_write}, kwargs = {kwargs}")

        if not self.json_file:
            raise ConfigurationError("No JSON file configured for saving")
        if not self.json:
            with open(self.json_file, 'r', encoding="utf-8") as jf:
                self.json = json.load(jf)

        if data and Path(data).is_file():
            try:
                # ensure parent dir exists
                p = Path(data)
                if not p.parent.exists():
                    p.parent.mkdir(parents=True, exist_ok=True)
                # _data = json.
                with open(data, "r", encoding="utf-8") as f:
                    self.json.update(json.load(f))  # type: ignore
                    with open(self.json_file, "w", encoding="utf-8") as f:
                        json.dump(self.json if isinstance(self.json, (dict, list)) else {}, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error("Error saving config JSON from `file`: %s", e)
                if is_debug():
                    _print(f":cross_mark: [white on red]Error saving JSON config:[/] [white on blue]{e}[/]")
                raise
        elif data and isinstance(data, str or bytes) and "{" in data.strip():
            if isinstance(data, bytes): data = data.decode()

            try:
                _json = json.loads(data)
                _self_json.update(_json)
                # with open(self.json_file, "w", encoding="utf-8") as f:
                #     json.dump(self.json if isinstance(self.json, (dict, list)) else {}, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error("Error saving config JSON from `string`: %s", e)
                if is_debug():
                    _print(f":cross_mark: [white on red]Error parsing JSON string:[/] [white on blue]{e}[/]")
                raise
        elif data and isinstance(data, dict):
            try:
                _self_json.update(data)
                # self.json.update(data)
                # with open(self.json_file, "w", encoding="utf-8") as f:
                #     json.dump(self.json if isinstance(self.json, (dict, list)) else {}, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error("Error saving config JSON from `dict/json`: %s", e)
                if is_debug():
                    _print(f":cross_mark: [white on red]Error parsing JSON string:[/] [white on blue]{e}[/]")
                raise
        else:
            if self.default and force_write:
                logger.error("can't saving JSON config, use default config instead")    
                _self_json = self.default
            # else:
            #     logger.error(f"Error saving JSON config, data is not a valid object: {data}")
            #     if is_debug():
            #         _print(f":cross_mark: [white on red]Error saving JSON config, data is not a file or valid JSON string:[/] [white on blue]{data}[/]")
            #     raise

        if kwargs:
            # _self_json = self.json.copy()
            for i in kwargs:
                if not " " in i:
                    _self_json.update({i: kwargs.get(i)})  # type: ignore

        if _self_json:
            self.json.update(_self_json)  # type: ignore
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(self.json if isinstance(self.json, (dict, list)) else {}, f, indent=2, ensure_ascii=False)
        else:
            if self.json == self.json_obj:
                _print(f"⚠ no data to save !")
            else:
                with open(self.json_file, "w", encoding="utf-8") as f:
                    json.dump(self.json if isinstance(self.json, (dict, list)) else {}, f, indent=2, ensure_ascii=False)
        
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
            JSONDecodeError: If there is an error decoding the JSON data.
            IOError: If there is an error writing to the JSON file.
        """
        
        # self.json = self._load_config(json_file)
        if not self.json or not isinstance(self.json, (dict, list)):
            self.json = {}
        else:
            if json_file:
                with open(json_file, 'w', encoding='utf-8') as f:
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
        self._load_config()
        if HAS_JSONCOLOR:
            jprint(self.json)
        elif HAS_RICH:
            _console.print_json(data=self.json) # type: ignore
        elif HAS_MAKE_COLORS and make_colors:
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
    
    def print_all_config(self):
        """
        Print all configuration data (alias for show).
        The `print_all_config` function is an alias for the `show` function, which prints all
        configuration data.
        :return: The `print_all_config` method is returning the result of calling the `show` method.
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
    
    @property
    def configfile(self):
        """
        Get the configuration file name (alias for `self.filename`).
        The `configfile` function returns the configuration file name, which is an alias for the
        filename.
        :return: The method `configfile` is returning the value of `self.filename`, which is the
        configuration file name or alias for the filename.
        """
        
        return self.filename
    
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
            _print("\n:cross_mark: [white on red]Invalid Json File ![/]")
            return False
    
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
                    if is_debug():
                        _print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{seg}[/]")
                    return default

            return current

        except Exception as e:
            # Fail-safe: return default on unexpected error and optionally print debug info
            if is_debug():
                _print(f"\n:cross_mark: [white on red]Error getting config:[/] [white on blue]{e}[/]")
            return default

    def get_config(self, *keys, default=None, auto_write=False, force_write=False, json_file = None):
        """
        Get configuration value of JSON by nested keys.

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
        
        :param key: The `key` parameter in the `get` method is used to specify the configuration key for
        which you want to retrieve the value. It is the identifier or name of the configuration setting
        that you are interested in accessing
        :param auto_write: The `auto_write` parameter is a boolean flag that determines whether the
        method should automatically write the default value to the configuration if the specified key
        :param default: The `default` parameter in the `get` method is used to specify a default value 
        that will be
        :param force_write: The `force_write` parameter is a boolean flag that determines whether 
        default is None or not the method should automatically write the default value
        to the configuration
        
        :return: string
        
        return with `default` if the requested configuration key is not found. If the key does not exist in the config file.
        """

        key = None
        
        if self.json is None or json_file:
            self.json = self._load_config(json_file)

        if is_debug():
            _print(f"[cyan]get_config called[/] keys={keys}, default={default}, auto_write={auto_write}, force_write={force_write}")
            _print(f"self.json: {self.json}")
            _print(f"json_file: {json_file}")
            _print(f"default: {default}")
            _print(f"keys: {keys}")

        default = format_value(default)
        if not keys:
            return default

        try:
            # flatten keys
            if len(keys) == 1 and isinstance(keys[0], (list, tuple)):
                keys = keys[0]
                if is_debug(): _print(f"🗝 [bold #00FFFF]keys[/]=[bold #FFFF00]{keys}[/]")
            parts = _flatten_keys(keys)
            if is_debug(): _print(f"🧰 [bold #00FFFF]parts[/]=[bold #FFFF00]{parts}[/]")
            if not parts:
                return default

            # Ensure YAML root is a mapping
            if not isinstance(self.json, dict):
                try:
                    self._load_config()
                except Exception as e:
                    if is_debug():
                        tprint()
                    else:
                        _print(f":cross_mark: [white on red]ERROR:[/] [white on blue]{e}[/]")

                    self.json = {}
            if self.json is None:
                self.json = {}

            current = self.json
            for seg in parts:
                key = seg
                if isinstance(current, dict) and seg in current:
                    current = current[seg]
                # else:
                #     # Key hilang -> tulis default jika diizinkan
                #     if (auto_write and default is not None) or force_write:
                #         # self.write_config(*parts, value=default)
                #         self.write_config(*parts, value=default if default is not None else "")
                #     # elif force_write:
                #     #     self.write_config(*parts, value=default if default is not None else "")
                #     if is_debug(): _print(f"⭐ [bold #00FFFF]default[/]=[bold #FFFF00]{default}[/]")
                #     # return default
        
            if current == self.json:
                current = None
                if self.default: current = get_default(*keys, default=self.default)    

            current = format_value(current)
            if is_debug(): _print(f"🗝 [bold #00FFFF]current[/]=[bold #FFFF00]{current}[/]")
            if is_debug(): _print(f"🧰 [bold #00FFFF]key[/]=[bold #FFFF00]{key}[/]")

            # Jika value kosong dan ada default, perlakukan sesuai flag
            if current is None or current == "":
                if (default is not None and auto_write) or force_write:
                    self.write_config(*parts, value=default if default is not None else "")    
                    return default
                elif key and self.default and self.default.get(key):# Attribute `get` is not defined on `bound method Self@get_config.default(o: Any) -> Any` in union `(bound method Self@get_config.default(o: Any) -> Any) | (dict[Unknown, Unknown] & ~AlwaysFalsy) | (Unknown & ~AlwaysFalsy)` (ty[unresolved-attribute])
                    return self.default.get(key) # Attribute `get` is not defined on `bound method Self@get_config.default(o: Any) -> Any` in union `(bound method Self@get_config.default(o: Any) -> Any) | (dict[Unknown, Unknown] & ~AlwaysFalsy) | (Unknown & ~AlwaysFalsy)` (ty[unresolved-attribute])
            
            if default is not None:
                return default

            return current
        except Exception as e:
            # Fail-safe: return default on unexpected error and optionally print debug info
            if is_debug():
                tprint()
            else:
                _print(f"\n:cross_mark: [white on red]Error getting config:[/] [white on blue]{e}[/]")
            
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
        The function `get` is an alias for `get_config` in Python. but with auto_write=True.
        
        :param key: The `key` parameter in the `get` method is used to specify the configuration key for
        which you want to retrieve the value. It is the identifier or name of the configuration setting
        that you are interested in accessing
        :param auto_write: The `auto_write` parameter is a boolean flag that determines whether the
        method should automatically write the default value to the configuration if the specified key
        :param default: The `default` parameter in the `get` method is used to specify a default value that will be
        returned if the requested configuration key is not found. If the key does not exist in the
        :return: The `get_config` method is being called with the provided `key` and any additional
        keyword arguments, and the result of that method call is being returned.
        """
        
        return self.get_config(*keys, default=default, auto_write=True)#, force_write=False)

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

    def write_config(self, *keys, value: Any = None, **kwargs) -> bool:
        """
        Write configuration value by nested keys (JSON backend).

        Accepts:
          - write_config('a.b.c', 'value')
          - write_config('a','b','c', value='value')
          - write_config('a','b','c','value')  (last positional becomes value if value kw not used)
          - write_config(key=value)

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
                if is_debug():
                    _print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            # Normalize iterable (support single list/tuple arg or multiple args)
            # if len(parts_src) == 1 and isinstance(parts_src[0], (list, tuple)):
            #     iterable = parts_src[0]
            # else:
            #     iterable = parts_src

            # Flatten and split by separators using shared helper
            # parts: List[str] = _flatten_keys(iterable)
            parts: List[str] = _flatten_keys(parts_src)

            if not parts:
                if is_debug():
                    _print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            # ensure root is a mapping
            if not isinstance(self.json, dict):
                self.json = {}

            # Traverse and set nested value
            d = self.json
            # for k in parts[:-1]:
            for k in parts:
                if k not in d or not isinstance(d[k], dict):
                    d[k] = {}
                d = d[k]
            d[parts[-1]] = value

            self.json.update(d)
            
            self._save_config()
            
            return True

        except Exception as e:
            if is_debug():
                tprint()
            else:
                _print(f"\n:cross_mark: [white on red]Error writing config:[/] [white on blue]{e}[/]")
                
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
        
        from collections import deque

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
                if is_debug():
                    if HAS_RICH:
                        _print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    else:
                        _print(":warning: [bold #FFFF00]No key ![/]")
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
                if k in d and isinstance(d[k], dict): # Argument of type "Unknown | str" cannot be assigned to parameter "key" of type "SupportsIndex | slice[Any, Any, Any]" in function "__getitem__"
                # Type "Unknown | str" is not assignable to type "SupportsIndex | slice[Any, Any, Any]"
                # Type "str" is not assignable to type "SupportsIndex | slice[Any, Any, Any]"
                #   "str" is incompatible with protocol "SupportsIndex"
                #     "__index__" is not present
                #   "str" is not assignable to "slice[Any, Any, Any]" (Pyright[reportArgumentType])
                    d = d[k] # Method `__getitem__` of type `bound method str.__getitem__(key: SupportsIndex | slice[SupportsIndex | None, SupportsIndex | None, SupportsIndex | None], /) -> str` cannot be called with key of type `str` on object of type `str` (ty[invalid-argument-type])
                else:
                    if is_debug():
                        _print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{k}[/]")
                    return False

            last_key = parts[-1]
            if last_key not in d:
                if is_debug():
                    _print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{last_key}[/]")
                return False

            # Remove by key or by matching value
            if value is None:
                del d[last_key] # Cannot delete subscript on object of type `str` with no `__delitem__` method (ty[not-subscriptable])
            else:
                if d[last_key] == value: # Argument of type "Unknown | str" cannot be assigned to parameter "key" of type "SupportsIndex | slice[Any, Any, Any]" in function "__getitem__"
                # Type "Unknown | str" is not assignable to type "SupportsIndex | slice[Any, Any, Any]"
                # Type "str" is not assignable to type "SupportsIndex | slice[Any, Any, Any]"
                #   "str" is incompatible with protocol "SupportsIndex"
                #     "__index__" is not present
                #   "str" is not assignable to "slice[Any, Any, Any]" (Pyright[reportArgumentType])
                    del d[last_key] # Cannot delete subscript on object of type `str` with no `__delitem__` method (ty[not-subscriptable])
                elif isinstance(d[last_key], list) and value in d[last_key]:
                    d[last_key].remove(value)
                else:
                    return False

            self._save_config()
            return True

        except Exception as e:
            if is_debug():
                _print(f"\n:cross_mark: [white on red]Error removing config:[/] [white on blue]{e}[/]")
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
                if is_debug():
                    msg = "No key!"
                    _print(f"\n:cross_mark: [bold #FFFF00]{msg}[/]") if HAS_RICH else print(msg)
                return False

            d = self.json
            for k in keys[:-1]:  # Stop before last key
                if k in d and isinstance(d[k], dict): # Method `__getitem__` of type `bound method str.__getitem__(key: SupportsIndex | slice[SupportsIndex | None, SupportsIndex | None, SupportsIndex | None], /) -> str` cannot be called with key of type `str` on object of type `str` (ty[invalid-argument-type])
                    d = d[k]
                else:
                    if is_debug():
                        msg = f"Key not found: {k}"
                        _print(f"\n:cross_mark: [white on red]{msg}[/]") if HAS_RICH else print(msg)
                    return False

            last_key = keys[-1]
            if last_key not in d:
                if is_debug():
                    msg = f"Key not found: {last_key}"
                    _print(f"\n:cross_mark: [white on red]{msg}[/]") if HAS_RICH else print(msg)
                return False

            del d[last_key] # Cannot delete subscript on object of type `str` with no `__delitem__` method (ty[not-subscriptable])
            self._save_config()
            return True

        except Exception as e:
            if is_debug():
                msg = f"Error removing key: {e}"
                _print(f"\n:cross_mark: [white on red]{msg}[/]") if HAS_RICH else print(msg)
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
                if is_debug():
                    _print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
                return {}

            d = self.json
            for k in keys[:-1]:
                # print(">>> Traverse check:", k, "in", type(d))
                if isinstance(d, dict) and k in d:
                    d = d[k]
                else:
                    if is_debug():
                        _print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{k}[/]")
                    return {}

            last_key = keys[-1]
            
            if isinstance(d, dict) and last_key in d:
                found = d[last_key]
                # print(">>> FOUND =", repr(found))
                if value is not None:
                    return found if found == value else {}
                return found
            else:
                if is_debug():
                    _print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{last_key}[/]")
                return {}
        except Exception as e:
            if is_debug():
                _print(f"\n: cross_mark: [white on red]Error finding key:[/] [white on blue]{key}[/]")
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
                    if is_debug():
                        _print(f"\n:cross_mark: [white on red]Key not found while traversing:[/] [white on blue]{seg}[/]")
                    return {}

            last_key = parts[-1]
            if isinstance(d, dict) and last_key in d:
                found = d[last_key]
                if value is None:
                    return found
                return found if found == value else {}
            else:
                if is_debug():
                    _print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{last_key}[/]")
                return {}
        except Exception as e:
            if is_debug():
                _print(f"\n:cross_mark: [white on red]Error in find():[/] [white on blue]{e}[/]")
            return {}
        
