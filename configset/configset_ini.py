#!/usr/bin/env python3

# File: configset_ini.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-08-11
# Description: 
# License: MIT

from json import JSONDecodeError
import json
import ast
import warnings
from pathlib import Path
import os
import sys
import re
from typing import Any, List, Tuple, Dict, Union

import configparser

_UNSET = object()

# printer
try:
    from . printer import _print, HAS_RICH, HAS_MAKE_COLORS, make_colors, Syntax  # type: ignore
except:
    try:
        from printer import _print, HAS_RICH, HAS_MAKE_COLORS, make_colors, Syntax  # type: ignore
    except:
        from configset.printer import _print, HAS_RICH, HAS_MAKE_COLORS, make_colors, Syntax  # type: ignore

# icons
try:
    from . icons import Icons  # type: ignore
except:
    try:
        from icons import Icons  # type: ignore
    except:
        from configset.icons import Icons  # type: ignore

# configset_hash
try:
    from . configset_hash import Hash  # type: ignore
except:
    try:
        from configset_hash import Hash  # type: ignore
    except:
        from configset.configset_hash import Hash  # type: ignore

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
    from . general import load_default, _update_file_snapshot, _get_mtime  # type: ignore
except:
    try:
        from general import load_default, _update_file_snapshot, _get_mtime  # type: ignore
    except:
        from configset.configset_general import load_default, _update_file_snapshot, _get_mtime  # type: ignore

# configset_error
try:
    from . configset_error import ConfigurationError  # type: ignore
except:
    try:
        from configset_error import ConfigurationError  # type: ignore
    except:
        from configset.configset_error import ConfigurationError  # type: ignore

class AttrDict(dict):
    """A dictionary-like object that allows attribute-style access.

    Attributes:
        name(str): Attribute name.
        value(object): Attribute value.
    """
    
    def __getattr__(self, name):
        """Get an attribute from the object. If the attribute is a dictionary, it will be converted to an AttrDict.

        Args:
            self(self): The object
            name(str): The name of the attribute.

        Returns:
            Union[Any, AttrDict]: The value of the attribute. If the attribute is a dictionary, it will be converted to an AttrDict. Otherwise, the original value is returned.

        Raises:
            AttributeError: Raised if the attribute is not found.
        """
        if name in self:
            val = self[name]
            if isinstance(val, dict):
                return AttrDict(val)
            return val
        raise AttributeError(f"{self.__class__.__name__!s} has no attribute {name!r}")

    def __setattr__(self, name, value):
        """Set an attribute of this object, creating nested AttrDicts as needed.

        Args:
            name(str): Name of the attribute to set.
            value(Any): Value to set the attribute to.

        Returns:
            None: No explicit return value.

        Raises:
            TypeError: If the attribute name is not a string or the value cannot be assigned.
        """
        self[name] = value
        # Automatically create nested AttrDicts for new dict values
        if isinstance(value, dict):
            self[name] = AttrDict(value)


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
        - optional helpers: _console, is_debug(), HAS_RICH, HAS_JSONCOLOR, HAS_MAKE_COLORS
        - optional utilities used for colored printing and pretty JSON printing.
    Replace or stub those dependencies when using the class in isolation.
    """
    
    def __init__(self, config_file: str = '', auto_write: bool = False, auto_reload: bool = True, config_dir: str = '', config_name: str = '', default:Any = None, **kwargs):
        super().__init__(**kwargs)
        
        self.allow_no_value = True

        # self.optionxform = str # Object of type `<class 'str'>` is not assignable to attribute `optionxform` of type `def optionxform(self, optionstr: str) -> str` (ty[invalid-assignment])
        self.default_config = {}
        self._loaded = False 

        # Determine config file path
        if not config_file:
            script_path = sys.argv[0] if sys.argv else 'config'
            config_file = os.path.splitext(os.path.realpath(script_path))[0] + ".ini"
        
        if not config_file.endswith('.ini'):
            config_file += '.ini'
            
        # Use _config_file_path to avoid property conflict
        self._config_file_path = Path(config_file).resolve()
        self._auto_reload = auto_reload
        self._last_mtime = None
        self._last_file_hash = None
        
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
            self._load_config(force=True)
            if os.getenv('SHOW_CONFIGNAME'):
                _print(f":japanese_symbol_for_beginner: [#FFFF00]CONFIG FILE:[/] [bold #00FFFF]{self._config_file_path}[/]")

        self.default_config = {}
        if default:
            self.default_config = load_default(default)
        self.default = self.default_config

    # In standard Python configparser source / typeshed:
    def optionxform(self, optionstr: str) -> str:
        return optionstr.lower()  # Default implementation lowercases keys

    def clear(self):
        """Clear in-memory sections only — never touches disk."""
        self._sections.clear()  # type: ignore
        self._proxies.clear()  # type: ignore
        self._proxies[self.default_section] = configparser.SectionProxy(self, self.default_section)  # type: ignore

    def write_default(self):
        """Write default configuration dictionary to INI, enforcing max 2 levels deep."""
        if self.default and isinstance(self.default, dict):
            for section, section_data in self.default.items():
                if isinstance(section_data, dict):
                    for opt, val in section_data.items():
                        self.write_config(section, opt, val)
                elif isinstance(section_data, (list, tuple)):
                    for item in section_data:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                self.write_config(section, k, v)
                        elif isinstance(item, (list, tuple)):
                            warnings.warn("Only accept 2 levels list/tuple", UserWarning)

    @property
    def filename(self) -> str:
        """Get absolute path of INI config file."""
        return str(self._config_file_path)
    
    @property
    def configfile(self) -> str:
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
    
    @property
    def path(self) -> str:
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
            _print(f":warning: [#FFFF00]Config file not found:[/] [#00FFFF]{config_file}[/]")
            raise FileNotFoundError(f"Config file not found: {config_file}")

    def _load_config(self, force=False):
        """
        The function `_load_config` loads configuration from a file with specific error handling.
        """

        def _load():
            if is_debug():
                _print(f"{Icons.WARNING} [bold #FFFF00]reloading .....[/]")
                print(f"{Icons.WARNING} Loading config from: {self._config_file_path}, IS_FILE: {os.path.isfile(self._config_file_path)}")
            
            try:
                # self.clear()
                self.read(str(self._config_file_path), encoding='utf-8')

                # self._loaded = True

                return True
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

        if getattr(self, '_in_load', False):
            return False
        self._in_load = True

        try:
            if is_debug():
                print(f"{Icons.BUG} [bold #FFFF00]force:[/] [bold #00FFFF]{force}[/]")
                print(f"{Icons.BUG} [bold #FFFF00]self._last_mtime == _get_mtime(self._config_file_path):[/] [bold #00FFFF]{self._last_mtime == _get_mtime(self._config_file_path)}[/]")
                print(f"{Icons.BUG} [bold #FFFF00]verify_hash(self._config_file_path):[/] [bold #00FFFF]{Hash.verify_hash(self._config_file_path)}[/]")

            if force:
                self.clear()
                if is_debug(): _print(f"{Icons.WARNING} [bold #FFFF00]loading \\[1] .....[/]")
                self._last_mtime = _get_mtime(self._config_file_path)
                Hash.update_hash(self._config_file_path)
                self._last_file_hash = Hash.get_hash(self._config_file_path)
            
                if is_debug():
                    _print(f"{Icons.BUG} [bold #FFFF00]self._last_mtime \\[2][/]: [bold #00FFFF]{self._last_mtime}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]_get_mtime(self._config_file_path) \\[2][/]: [bold #00FFFF]{_get_mtime(self._config_file_path)}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]self._last_file_hash \\[2][/]: [bold #00FFFF]{self._last_file_hash}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]get_hash \\[2][/]: [bold #00FFFF]{Hash.get_hash(self._config_file_path)}[/]")
            
                _load()
                if is_debug(): print("-"*os.get_terminal_size()[0])
                return True
            elif self._last_mtime != _get_mtime(self._config_file_path) or not Hash.verify_hash(self._config_file_path, True):
                self.clear()
                if is_debug():
                    _print(f"{Icons.WARNING} [bold #FFFF00]loading [2] .....[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]self._last_mtime \\[1]:[/] [bold #00FFFF]{self._last_mtime}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]_get_mtime(self._config_file_path) \\[1]:[/] [bold #00FFFF]{_get_mtime(self._config_file_path)}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]self._last_file_hash \\[1]:[/] [bold #00FFFF]{self._last_file_hash}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]get_hash \\[1]:[/] [bold #00FFFF]{Hash.get_hash(self._config_file_path)}[/]")

                self._last_mtime = _get_mtime(self._config_file_path)
                Hash.update_hash(self._config_file_path)
                self._last_file_hash = Hash.get_hash(self._config_file_path)
            
                if is_debug():
                    _print(f"{Icons.BUG} [bold #FFFF00]self._last_mtime \\[2]:[/] [bold #00FFFF]{self._last_mtime}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]_get_mtime(self._config_file_path) \\[2]:[/] [bold #00FFFF]{_get_mtime(self._config_file_path)}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]self._last_file_hash \\[2]:[/] [bold #00FFFF]{self._last_file_hash}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]get_hash \\[2]:[/] [bold #00FFFF]{Hash.get_hash(self._config_file_path)}[/]")
            
                _load()
                if is_debug(): print("-"*os.get_terminal_size()[0])
                return True
            elif self._last_file_hash != Hash.get_hash(self._config_file_path):
                self.clear()
                if is_debug():
                    _print(f"{Icons.WARNING} [bold #FFFF00]loading \\[3] .....[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]self._last_mtime \\[1]: [bold #00FFFF]{self._last_mtime}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]_get_mtime(self._config_file_path) \\[1]: [bold #00FFFF]{_get_mtime(self._config_file_path)}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]self._last_file_hash \\[1]: [bold #00FFFF]{self._last_file_hash}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]get_hash \\[1]: [bold #00FFFF]{Hash.get_hash(self._config_file_path)}[/]")

                self._last_mtime = _get_mtime(self._config_file_path)
                Hash.update_hash(self._config_file_path)
                self._last_file_hash = Hash.get_hash(self._config_file_path)
            
                if is_debug():
                    _print(f"{Icons.BUG} [bold #FFFF00]self._last_mtime \\[2]: [bold #00FFFF]{self._last_mtime}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]_get_mtime(self._config_file_path) \\[2]: [bold #00FFFF]{_get_mtime(self._config_file_path)}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]self._last_file_hash \\[2]: [bold #00FFFF]{self._last_file_hash}[/]")
                    _print(f"{Icons.BUG} [bold #FFFF00]get_hash \\[2]: [bold #00FFFF]{Hash.get_hash(self._config_file_path)}[/]")
            
                _load()
                if is_debug(): print("-"*os.get_terminal_size()[0])
                return True

            if is_debug(): print("-"*os.get_terminal_size()[0])
            return False
        except Exception as e:
            if is_debug(): _print(f":cross_mark: {e}")
            return False
        finally:
            self._in_load = False
        
    def _save_config(self) -> None:
        """Save current configuration to file."""
        if self._auto_reload: self._load_config()
        try:
            with open(self._config_file_path, 'w', encoding='utf-8') as f:  # Fix: use _config_file_path
                # self.write(f)
                super(ConfigSetIni, self).write(f)
            _last_mtime, _last_file_hash = _update_file_snapshot(self._config_file_path)   # <-- keep the reload snapshot in sync with our own writes
            self._last_mtime = _last_mtime if _last_mtime else self._last_mtime
            self._last_file_hash = _last_file_hash if _last_file_hash else self._last_file_hash
        except Exception as e:
            if is_debug():
                _print(f":cross_mark: [white on red]Error saving config:[/] [white on blue]{e}[/]")

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

        # if self._auto_reload: self._load_config()
        
        _print(f":japanese_symbol_for_beginner: [bold #FFFF00]CONFIG FILE:[/] [bold #00FFFF]{self._config_file_path}[/]")  # Fix: use _config_file_path
        
        _print(f":japanese_symbol_for_beginner: [bold #FFFF00]CONFIG INI:[/]")
        if is_debug():
            print(f"self.config_file: {self.config_file}, IS_FILE: {os.path.isfile(self.config_file)}")
        if HAS_RICH and self.config_file and Path(self.config_file).exists():
            with open(self._config_file_path, 'r') as ini_file:
                syntax = Syntax(ini_file.read(), lexer='ini', theme='fruity')  # type: ignore
                _print(syntax)
        else:
            data = self.get_all_config(sections)
            if is_debug(): print(f"data: {data}")

            for section_name, section_data in data:
                self._print_colored(f"[{section_name}]", 'section')
                for option, value in section_data.items():
                    self._print_colored(f"  {option} = {value}", 'option', value)
        
        # print()
        
        return self.get_all_config(sections)
    
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
        if self._auto_reload: self._load_config()
        return self.print_all_config(*args, **kwargs)
        
    def get_section(self, section: str):
        """
        Return all options and values in a section as {section: {option: value, ...}}.
        If section does not exist, print error and return None.
        """

        if self._auto_reload: self._load_config()

        if self.has_section(section):
            options = {opt: self.get_config(section, opt) for opt in self.options(section)}
            # return {section: options}
            return AttrDict(options)
        else:
            _print(f":x: [white on red]No section[/] [white on blue]'{section}'[/] [white on red]found ![/]")
            return None

    def print(self, section: str = '', option: str = '', default: str = '') -> Any:
        """
        Print configuration values to the configured console and return the requested data.
        """
        if getattr(self, '_auto_reload', False):
            self._load_config()

        # Case 1: Both section and option provided
        if section and option:
            value = self.get_config(section, option, default, False)
            _print(f"[{section}]\n  {option} = {value}")
            return value

        # Case 2: Only section provided
        elif section and not option:
            section_found = self.get_section(section)
            if section_found:
                for sec, opts in section_found.items():
                    _print(f"[{sec}]")
                    for opt, val in opts.items():
                        _print(f"  {opt} = {val}")
            return section_found

        # Case 3: Only option provided (Find mode)
        elif not section and option:
            raw_results = self.find(option)
            if not raw_results:
                return None

            # Convert list of tuples from find() into {section: {option: value}} map
            data_found: Dict[str, Dict[str, str]] = {}
            for item in raw_results:
                if len(item) == 3:
                    sec, opt, val = item
                    data_found.setdefault(sec, {})[opt] = val

            if data_found:
                for sec, opts in data_found.items():
                    _print(f"[{sec}]")
                    for opt, val in opts.items():
                        _print(f"  {opt} = {val}")
                return data_found
            return None

        # Case 4: Neither provided
        else:
            return None  # Matches docstring specification
        
    def get_config(self, section: str, option: str = '', 
                  default: Any = None, auto_write: bool = False, value: Any = None, _skip_reload=False) -> Any:
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

        if self._auto_reload: self._load_config()

        if auto_write is _UNSET:
            auto_write = self._auto_write

        if value is not None: default = value
        if not option and "." in section:
            section, option = section.split(".", 1)
        if section and not option:
            _print(f":cross_mark: [white on red]not option ![/]")
            return default

        # auto_write = auto_write or self._auto_write
            
        try:
            value = super().get(section, option)
            if is_debug(): _print(f"value: {value}")
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
        
    def get(self, section: str, option: str = '', 
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

    def _get(self, section, option, **kwargs):
        if self._auto_reload: self._load_config()
        return super().get(section, option, **kwargs)

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

    def write_config(self, section: str, option: str = '', value: Any = '', raw: bool = False) -> Any:
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

        if self._auto_reload: self._load_config()
        
        def _write(section, option, value):
            # Convert value to string for storage
            str_value = str(value) if value is not None else ''
            # super().set(section, option, str_value)
            if is_debug():
                print(f"section: {section}")
                print(f"option: {option}")
                print(f"value: {value}, type: {type(value)}")
            try:
                super(ConfigSetIni, self).set(section, option, str_value)
            except configparser.NoSectionError:
                super(ConfigSetIni, self).add_section(section)
                super(ConfigSetIni, self).set(section, option, str_value)
            except configparser.NoOptionError:
                super(ConfigSetIni, self).set(section, option, str_value)

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
        if isinstance(value, list) and not raw:
            value = " ".join(value)
            _write(section, option, value)
        elif isinstance(value, str) and value.strip().startswith("[") and value.strip().endswith("]") and not raw:
            try:
                value = ast.literal_eval(value)
                value = " ".join(value)
                _write(section, option, value)
            except Exception as e:
                if is_debug():
                    _print(f":warning: [bold #00FFFF]ConfigSetIni:[/] [white on red]Failed to parse list[/] [white on blue]{section}:{option}[/] -> [white on red]{e}[/]")
                warnings.warn(f"ConfigSetIni: Failed to parse list for INI value: {e}", UserWarning)
                _write(section, option, value)
                
        elif isinstance(value, str) and value.strip().startswith("{") and value.strip().endswith("}") and not raw:
            # Attempt to parse stringified dict
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict) and _dict_depth(parsed) == 1:
                    value = parsed
                    for key in value:
                        _write(section, key, value[key])
                elif isinstance(parsed, dict) and _dict_depth(parsed) > 1:
                    msg = "INI value must be a 1-level dict (no nested dicts)."
                    if is_debug():
                        _print(f":warning: [white on red]{msg}[/] [white on blue]{section}:{option}[/]")
                    warnings.warn(msg + ", write as it is", UserWarning)
                    for key in parsed:
                        _write(section, key, parsed[key])
                else:
                    msg = "INI value not a valid dictionary."
                    if is_debug():
                        _print(f":warning: [white on red]{msg}[/] [white on blue]{section}:{option}[/]")
                    warnings.warn(msg + ", write as it is", UserWarning)
                    _write(section, option, value)
            except JSONDecodeError:
                if is_debug():
                    _print(f":warning: [bold #00FFFF]ConfigSetIni:[/] [white on red]Failed to parse JSON[/] [white on blue]{section}:{option}[/]")
                warnings.warn("ConfigSetIni: Failed to parse JSON for INI value", UserWarning)
            except Exception as e:
                if is_debug():
                    _print(f":warning: [bold #00FFFF]ConfigSetIni:[/] [white on red]Failed to process value[/] [white on blue]{section}:{option}[/]")
                warnings.warn(f"ConfigSetIni: Failed to process INI value: {e}", UserWarning)
                
        elif isinstance(value, dict) and not raw:
            
            if _dict_depth(value) > 1:
                msg = "INI value must be a 1-level dict (no nested dicts)."
                if is_debug():
                    _print(f":warning: [white on red]{msg}[/] [white on blue]{section}:{option}[/]")
                warnings.warn(msg + ", write as it is", UserWarning)
                for key in value:
                    _write(section, key, value[key])
            else:
                for key in value:
                    _write(section, key, value[key])

        else:
            _write(section, option, str(value) if value else '')
            
        self._save_config()

        return self.get_config(section, option)
    
    def write(self, *args, **kwargs):
        """Public alias: cfg.write(section, option, value) behaves like write_config."""
        return self.write_config(*args, **kwargs)
        
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
    
    def _set(self, section, option, value):
        if self._auto_reload: self._load_config()
        return super().set(section, option, value)

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

        if self._auto_reload: self._load_config()

        # print(f"section: {section}, option: {option}")
        try:
            if option is None:
                # Remove entire section
                if self.has_section(section):
                    super().remove_section(section)
                    self._save_config()
                    if is_debug():
                        print(f"Removed section: [{section}]")
                    return True
                else:
                    if is_debug():
                        print(f"Section not found: [{section}]")
                    return False
            else:
                # Remove specific option from section
                if self.has_section(section):
                    if self.has_option(section, option):
                        super().remove_option(section, option)
                        self._save_config()
                        if is_debug():
                            print(f"Removed option: [{section}] {option}")
                        return True
                    else:
                        if is_debug():
                            print(f"Option not found: [{section}] {option}")
                        return False
                else:
                    if is_debug():
                        print(f"Section not found: [{section}]")
                    return False
        except Exception as e:
            if is_debug():
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
        return self.remove_config(section, None)
    
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
                except JSONDecodeError:
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
                except JSONDecodeError:
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
        
    def find(self, query: str, case_sensitive: bool = True, verbose: bool = False) -> List[Tuple]:
        """
        Search for sections, options, or values matching the query.

        Args:
            query: Search term
            case_sensitive: Whether to perform case-sensitive search
            verbose: Print found items

        Returns:
            List of found items (tuples indicating match type and details)
        """
        if getattr(self, '_auto_reload', False):
            self._load_config()

        if not query:
            return []

        found = []
        search_query = query if case_sensitive else query.lower()

        for section_name in self.sections():
            section_match = section_name if case_sensitive else section_name.lower()
            printed_section_header = False

            # Substring search for section name
            if search_query in section_match:
                found.append(('section', section_name))
                if verbose:
                    self._print_colored(f"[{section_name}]", 'section')
                    printed_section_header = True

            # Check options and values in section
            try:
                for option in self.options(section_name):
                    option_match = option if case_sensitive else option.lower()

                    # Fetch option value safely
                    value = str(super().get(section_name, option))
                    value_match = value if case_sensitive else value.lower()

                    # Substring search for options and values
                    option_matched = search_query in option_match
                    value_matched = search_query in value_match

                    if option_matched or value_matched:
                        found.append((section_name, option, value))

                        if verbose:
                            if not printed_section_header:
                                self._print_colored(f"[{section_name}]", 'section')
                                printed_section_header = True
                            self._print_colored(f"  {option} = {value}", 'option', value)

            except Exception as e:
                if is_debug():
                    tprint()
                else:
                    print(f"{Icons.ERROR} [white on red]Error searching section[/] [bold #FFFF00]{section_name}[/]: [white on blue]{e}[/]")

        return found

    
    def get_all_config(self, sections: List[str] = []) -> List[Tuple[str, Dict]]:
        """
        Get all configuration data, optionally filtered by sections.
        
        Args:
            sections: List of section names to include (None for all)
            
        Returns:
            List of (section_name, options_dict) tuples
        """

        # if self._auto_reload: self.check_and_reload()

        # result = []
        # target_sections = sections or self.sections()
        
        # for section_name in target_sections:
        #     if not self.has_section(section_name):
        #         continue
                
        #     section_data = {}
        #     # Snapshot option names to prevent iterator mutation errors during reload
        #     for option in list(self.options(section_name)):
        #         section_data[option] = self.get_config(section_name, option)
                
        #     result.append((section_name, section_data))
            
        # return result

        # if self._auto_reload: self._load_config()

        if self._auto_reload: self._load_config()

        result = []
        target_sections = sections or self.sections()
        for section_name in target_sections:
            if not self.has_section(section_name):
                continue
            section_data = {}
            for option in list(self.options(section_name)):
                section_data[option] = self.get_config(section_name, option, auto_write=False)
                # section_data[option] = self._get(section_name, option)
            result.append((section_name, section_data))
        return result
        
    # def _convert_value(self, value: str) -> Any:
    #     """Convert a string value to its appropriate type (bool, int, float, or str).

    #     Args:
    #         value(str): The string value to convert.

    #     Returns:
    #         Any: The converted value (bool, int, float, or str).

    #     Raises:
    #         ValueError: If the string cannot be converted to a float.
    #     """
        
        
    #     if not isinstance(value, str):
    #         return value
            
    #     value = value.strip()
        
    #     # Boolean conversion
    #     if value.lower() in ('true', 'yes', '1'):
    #         return True
    #     elif value.lower() in ('false', 'no', '0'):
    #         return False
        
    #     # Numeric conversion
    #     if value.isdigit():
    #         return int(value)
        
    #     # Try float conversion
    #     try:
    #         if '.' in value:
    #             return float(value)
    #     except ValueError:
    #         pass
        
    #     # Return as string
    #     return value
    
    # def _convert_value(self, value: Any) -> Any:
    #     """Convert string values into tuple, list, dict, bool, int, float, or str."""
    #     if not isinstance(value, str):
    #         return value

    #     val_trimmed = value.strip()
    #     if not val_trimmed:
    #         return ""

    #     # 1. Dictionaries: {...}
    #     if val_trimmed.startswith('{') and val_trimmed.endswith('}'):
    #         try:
    #             return json.loads(val_trimmed)
    #         except Exception:
    #             try:
    #                 parsed = ast.literal_eval(val_trimmed)
    #                 if isinstance(parsed, dict):
    #                     return parsed
    #             except Exception:
    #                 pass

    #     # 2. Parenthesized Tuples: (...)
    #     if val_trimmed.startswith('(') and val_trimmed.endswith(')'):
    #         try:
    #             parsed = ast.literal_eval(val_trimmed)
    #             if isinstance(parsed, tuple):
    #                 return parsed
    #         except Exception:
    #             pass
    #         inner = val_trimmed[1:-1].strip()
    #         if not inner:
    #             return ()
    #         items = re.split(r',\s*', inner)
    #         return tuple(self._convert_value(item.strip()) for item in items if item.strip())

    #     # 3. Bracketed Lists: [...]
    #     if val_trimmed.startswith('[') and val_trimmed.endswith(']'):
    #         try:
    #             return json.loads(val_trimmed)
    #         except Exception:
    #             try:
    #                 parsed = ast.literal_eval(val_trimmed)
    #                 if isinstance(parsed, list):
    #                     return parsed
    #             except Exception:
    #                 pass
    #         inner = val_trimmed[1:-1].strip()
    #         if not inner:
    #             return []
    #         items = re.split(r',\s*', inner)
    #         return [self._convert_value(item.strip()) for item in items if item.strip()]

    #     # 4. Unparenthesized Comma-Separated Values: 111, 222, 333 or '222', '333', '444'
    #     if ',' in val_trimmed:
    #         try:
    #             parsed = ast.literal_eval(val_trimmed)
    #             if isinstance(parsed, tuple):
    #                 return parsed
    #         except Exception:
    #             pass
    #         items = re.split(r',\s*', val_trimmed)
    #         if len(items) > 1:
    #             return tuple(self._convert_value(item.strip()) for item in items if item.strip())

    #     # 5. Space-Separated Sequences / Mixed Quoted Tokens: '888' 999 "000" or 777 888 999
    #     if ' ' in val_trimmed and not ('\n' in val_trimmed):
    #         try:
    #             import shlex
    #             tokens = shlex.split(val_trimmed)
    #             if len(tokens) > 1:
    #                 has_quotes = "'" in val_trimmed or '"' in val_trimmed
    #                 all_numeric = all(
    #                     t.isdigit() or (t.startswith('-') and t[1:].isdigit()) or t.replace('.', '', 1).isdigit()
    #                     for t in tokens
    #                 )
    #                 if has_quotes or all_numeric:
    #                     return [self._convert_value(t) for t in tokens]
    #         except Exception:
    #             pass

    #     # 6. Multiline values
    #     if '\n' in val_trimmed:
    #         items = re.split(r'\n+', val_trimmed)
    #         return [self._convert_value(item.strip()) for item in items if item.strip()]

    #     # 7. Key-Value pairs: k1: v1, k2: v2
    #     if ':' in val_trimmed and ',' in val_trimmed:
    #         pairs = re.split(r',\s*', val_trimmed)
    #         result_dict = {}
    #         valid_pair = False
    #         for pair in pairs:
    #             if ':' in pair:
    #                 k, v = pair.split(':', 1)
    #                 result_dict[k.strip()] = self._convert_value(v.strip())
    #                 valid_pair = True
    #         if valid_pair:
    #             return result_dict

    #     # 8. Booleans
    #     lowercased = val_trimmed.lower()
    #     if lowercased in ('true', 'yes', '1'):
    #         return True
    #     elif lowercased in ('false', 'no', '0'):
    #         return False

    #     # 9. Numerics (handling leading zeros as integers if unquoted)
    #     if val_trimmed.isdigit() or (val_trimmed.startswith('-') and val_trimmed[1:].isdigit()):
    #         return int(val_trimmed)

    #     try:
    #         if '.' in val_trimmed:
    #             return float(val_trimmed)
    #     except ValueError:
    #         pass

    #     # 10. Fallback string
    #     return value

    def _convert_value(self, value: Any) -> Any:
        """Convert string values into tuple, list, dict, bool, int, float, or str."""
        if not isinstance(value, str):
            return value

        val_trimmed = value.strip()
        if not val_trimmed:
            return ""

        # Helper: Bracket- and quote-aware top-level splitting
        def _smart_split(text: str, delimiter: str = ',') -> List[str]:
            tokens = []
            current = []
            in_single_quote = False
            in_double_quote = False
            bracket_depth = 0
            paren_depth = 0
            brace_depth = 0

            for char in text:
                if char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                    current.append(char)
                elif char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                    current.append(char)
                elif not in_single_quote and not in_double_quote:
                    if char == '[':
                        bracket_depth += 1
                    elif char == ']':
                        bracket_depth -= 1
                    elif char == '(':
                        paren_depth += 1
                    elif char == ')':
                        paren_depth -= 1
                    elif char == '{':
                        brace_depth += 1
                    elif char == '}':
                        brace_depth -= 1

                    if char == delimiter and bracket_depth == 0 and paren_depth == 0 and brace_depth == 0:
                        tokens.append("".join(current).strip())
                        current = []
                    else:
                        current.append(char)
                else:
                    current.append(char)

            if current:
                token = "".join(current).strip()
                if token:
                    tokens.append(token)
            return tokens

        # Helper: Evaluates literals safely after normalizing multiline INI whitespace
        def _eval_literal(val: str) -> Any:
            try:
                return json.loads(val)
            except Exception:
                pass
            try:
                return ast.literal_eval(val)
            except Exception:
                pass
            # Normalize multiline newlines and indentation from INI files
            normalized = re.sub(r'\s+', ' ', val)
            try:
                return json.loads(normalized)
            except Exception:
                pass
            try:
                return ast.literal_eval(normalized)
            except Exception:
                pass
            return None

        # 1. Dictionaries: {...}
        if val_trimmed.startswith('{') and val_trimmed.endswith('}'):
            parsed = _eval_literal(val_trimmed)
            if isinstance(parsed, dict):
                return parsed

        # 2. Parenthesized Tuples: (...)
        if val_trimmed.startswith('(') and val_trimmed.endswith(')'):
            parsed = _eval_literal(val_trimmed)
            if isinstance(parsed, tuple):
                return parsed
            inner = val_trimmed[1:-1].strip()
            if not inner:
                return ()
            items = _smart_split(inner, ',')
            return tuple(self._convert_value(item) for item in items if item)

        # 3. Bracketed Lists: [...] (Handles nested lists like `animes` and string lists like `movies`)
        if val_trimmed.startswith('[') and val_trimmed.endswith(']'):
            parsed = _eval_literal(val_trimmed)
            if isinstance(parsed, list):
                return parsed
            inner = val_trimmed[1:-1].strip()
            if not inner:
                return []
            items = _smart_split(inner, ',')
            return [self._convert_value(item) for item in items if item]

        # 4. Unparenthesized Comma-Separated Values: 111, 222, 333 or '222', '333', '444'
        if ',' in val_trimmed:
            parsed = _eval_literal(val_trimmed)
            if isinstance(parsed, tuple):
                return parsed
            items = _smart_split(val_trimmed, ',')
            if len(items) > 1:
                return tuple(self._convert_value(item) for item in items if item)

        # 5. Standalone Quoted Strings: 'text' or "text"
        if (val_trimmed.startswith("'") and val_trimmed.endswith("'")) or \
           (val_trimmed.startswith('"') and val_trimmed.endswith('"')):
            try:
                parsed = ast.literal_eval(val_trimmed)
                if isinstance(parsed, str):
                    return parsed
            except Exception:
                return val_trimmed[1:-1]

        # 6. Space-Separated Sequences / Mixed Quoted Tokens: '888' 999 "000" or 777 888 999
        if ' ' in val_trimmed and '\n' not in val_trimmed:
            try:
                tokens = shlex.split(val_trimmed)
                if len(tokens) > 1:
                    has_quotes = "'" in val_trimmed or '"' in val_trimmed
                    all_numeric = all(
                        t.isdigit() or (t.startswith('-') and t[1:].isdigit()) or t.replace('.', '', 1).isdigit()
                        for t in tokens
                    )
                    if has_quotes or all_numeric:
                        return [self._convert_value(t) for t in tokens]
            except Exception:
                pass

        # 7. Multiline Values
        if '\n' in val_trimmed:
            items = re.split(r'\n+', val_trimmed)
            return [self._convert_value(item.strip()) for item in items if item.strip()]

        # 8. Key-Value Pairs: k1: v1, k2: v2
        if ':' in val_trimmed and ',' in val_trimmed:
            pairs = _smart_split(val_trimmed, ',')
            result_dict = {}
            valid_pair = False
            for pair in pairs:
                if ':' in pair:
                    k, v = pair.split(':', 1)
                    result_dict[k.strip()] = self._convert_value(v.strip())
                    valid_pair = True
            if valid_pair:
                return result_dict

        # 9. Booleans
        lowercased = val_trimmed.lower()
        if lowercased in ('true', 'yes', '1'):
            return True
        elif lowercased in ('false', 'no', '0'):
            return False

        # 10. Numerics
        if val_trimmed.isdigit() or (val_trimmed.startswith('-') and val_trimmed[1:].isdigit()):
            return int(val_trimmed)

        try:
            if '.' in val_trimmed:
                return float(val_trimmed)
        except ValueError:
            pass

        # 11. Fallback Raw String
        return value

    def _print_colored(self, text: str, element_type: str, value: str = '') -> None:
        """Print text with colors if available."""
        if element_type == 'section':
            if HAS_RICH:
                _print(f"[bold cyan]{text}[/]")
            elif HAS_MAKE_COLORS and make_colors:
                print(make_colors(text, 'lc'))
            else:
                print(text)
        elif element_type == 'option':
            if HAS_RICH:
                _print(f"[yellow]{text}[/]")
            elif HAS_MAKE_COLORS and make_colors:
                print(make_colors(text, 'ly'))
            else:
                print(text)
        else:
            print(text)

