#!/usr/bin/env python3

# File: configset_yaml.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-08-11
# Description: 
# License: MIT

# general
import re
from pathlib import Path
from typing import Any, List
import os
import yaml

# configset_error
try:
    from . configset_error import ConfigurationError  # type: ignore
except:
    try:
        from configset_error import ConfigurationError  # type: ignore
    except:
        from configset.configset_error import ConfigurationError  # type: ignore

# general
try:
    from . general import _flatten_keys, load_default, format_value, get_default  # type: ignore
except:
    try:
        from general import _flatten_keys, load_default, format_value, get_default  # type: ignore
    except:
        from configset.configset_general import _flatten_keys, load_default, format_value, get_default  # type: ignore

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
    - When a debug mode helper (is_debug) is enabled, diagnostic messages are
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
    
    def __init__(self, yaml_file: str = '', config_file: str = '', default:Any = None, **kwargs):
        self.yaml_file = yaml_file or config_file
        self.file = self.yaml_file
        self.kwargs = kwargs
        self.yaml = self._load_config()

        self.default_config = {}
        if default:
            self.default_config = load_default(default)
        self.default = self.default_config

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
                if is_debug():
                    _print(f"\n:cross_mark: [white on red]Invalid YAML input:[/] [white on blue]{yaml_file}[/]")
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
        if is_debug():
            _print(f"\n:gear: [white on blue]Loading YAML config:[/] [white on blue]{source}[/]")
            _print(f":mag: [white on blue]YAML File is File:[/] [white on blue]{os.path.isfile(source)}[/]")
        try:
            if os.path.isfile(source):
                with open(source, "r", encoding="utf-8") as f:
                    self.yaml = yaml.safe_load(f)
                    if is_debug():
                        _print(f":white_check_mark: (1) [white on green]YAML config loaded successfully from file.[/]")
                        _print(f":gear: [white on blue] (1) YAML data type:[/] [white on blue]{type(self.yaml)}[/]")
            else:
                self.yaml = yaml.safe_load(source)  # Fix: was yaml.save_load
                if is_debug():
                        _print(f":white_check_mark: (2) [white on green]YAML config loaded successfully from file.[/]")
                        _print(f":gear: [white on blue] (2) YAML data type:[/] [white on blue]{type(self.yaml)}[/]")
            if self.yaml is None:
                self.yaml = {}
            return self.yaml
        except FileNotFoundError:
            if is_debug():
                _print(f"[:cross_mark: [white on red]Config file not found:[/] [white on blue]{source}[/]")
            logger.warning(f"Config file not found: {source}")
            # Create empty config or use defaults
        except PermissionError:
            if is_debug():
                _print(f":cross_mark: [white on red]Permission denied accessing:[/] [white on blue]{source}[/]")
            logger.error(f"Permission denied accessing: {source}")
            raise ConfigurationError(f"Cannot access config file: {source}")
        except UnicodeDecodeError as e:
            if is_debug:
                _print(f":cross_mark: [white on red]Invalid encoding in config file:[/] [white on blue]{e}[/]")
            logger.error(f"Invalid encoding in config file: {e}")
            raise ConfigurationError(f"Config file has invalid encoding: {e}")
        except yaml.YAMLError as e:
            # tolerate YAML parse errors in production: log and fallback to empty mapping
            logger.warning("Invalid YAML content in %s: %s", source, e)
            if is_debug():
                _print(f":cross_mark: [white on red]Invalid YAML content:[/] [white on blue]{e}[/]")
            self.yaml = {}
            return self.yaml
        except Exception as e:
            if is_debug:
                _print(f":cross_mark: [white on red]Unexpected error loading config:[/] [white on blue]{e}[/]")
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
            if is_debug():
                _print(f":cross_mark: [white on red]Error saving YAML config:[/] [white on blue]{e}[/]")
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
            _print(self.yaml)
        elif HAS_MAKE_COLORS and make_colors:
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
    
    def print_all_config(self):
        """
        Print all configuration settings.
        The function `print_all_config` prints all configuration settings using the `show` method.
        :return: The `print_all_config` method is returning the result of calling the `show` method on
        the object itself.
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
    def configfile(self):
        """
        Get the configuration name (alias for filename).
        The `configfilename` function returns the configuration name, which is an alias for the filename.
        :return: The method `configfilename` is returning the value of `self.filename`, which is the
        configuration name or alias for the filename.
        """
        
        return self.filename
    
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
            _print("\n:cross_mark: [white on red]Invalid YAML File ![/]")  # Fix: was Json File
            return False
    
    # def get_config(self, *keys, default=None, force_write = False):
    #     """
    #     Get configuration value of YAML by nested keys (YAML backend).

    #     Usage:
    #         get_config('a')                     -> top-level key 'a'
    #         get_config('a', 'b', 'c')           -> nested access a.b.c
    #         get_config('a.b.c')                 -> single composite key (dot or :;| separators supported)
    #         get_config(['a','b','c'])           -> list/tuple of keys
    #         get_config(...)                     -> returns `default` if key path not found

    #     This method mirrors ConfigSetJson.get_config: accepts mixed positional arguments
    #     and composite keys containing separators. Any argument that contains separators
    #     will be split into segments and injected in-place (e.g. get_config('k1', 'k2.k3:k4', 'k5')
    #     becomes ['k1','k2','k3','k4','k5']).
    #     """
        
    #     default = format_value(default)
    #     if not keys:
    #         return default
        
    #     try:
    #         # Handle single list/tuple argument (legacy callers)
    #         if len(keys) == 1 and isinstance(keys[0], (list, tuple)):
    #             keys = keys[0]
    #             if is_debug(): _print(f"🗝 [bold #00FFFF]keys[/]=[bold #FFFF00]{keys}[/]")
    #         # Build flattened list of path segments
    #         parts: List[str] = _flatten_keys(keys)
    #         if not parts:
    #             return default

    #         # Ensure YAML root is a mapping
    #         if not isinstance(self.yaml, dict):
    #             try:
    #                 self._load_config()
    #             except Exception as e:
    #                 if is_debug():
    #                     tprint()
    #                 else:
    #                     _print(f":cross_mark: [white on red]ERROR:[/] [white on blue]{e}[/]")
    #                 self.yaml = {}

    #         if self.yaml is None:
    #             self.yaml = {}

    #         # Traverse the YAML structure safely
    #         current = self.yaml
            
    #         for seg in parts:
    #             if isinstance(current, dict) and seg in current:
    #                 current = current[seg]
    #                 # if not current and default:
    #                 #     return default
    #                 # elif not current and isinstance(default, bool):
    #                 #     return default
    #                 # elif current and str(current).isdigit():
    #                 #     return int(current)
    #             # else:
    #             #     if is_debug():
    #             #         _print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{seg}[/]")
    #             #     return default

    #         if current == self.yaml:
    #             current = None
    #             if self.default: current = get_default(*keys, default=self.default)    

    #         current = format_value(current)
    #         if is_debug(): _print(f"🗝 [bold #00FFFF]current[/]=[bold #FFFF00]{current}[/]")
    #         if is_debug(): _print(f"🧰 [bold #00FFFF]key[/]=[bold #FFFF00]{keys}[/]")

    #         # If the value is empty and there is a default, treat it according to the flag
    #         if current is None or current == "":
    #             if (default is not None and auto_write) or force_write:
    #                 self.write_config(*parts, value=default if default is not None else "")    
    #                 return default
    #             elif key and self.default and self.default.get(key):
    #                 return self.default.get(key)
            
    #         if default is not None:
    #             return default

    #         return current

    #     except Exception as e:
    #         if is_debug():
    #             _print(f"\n:cross_mark: [white on red]Error getting config:[/] [white on blue]{e}[/]")
    #         return default

    def get_config(
        self,
        *keys: Any,
        default: Any = None,
        auto_write: bool = False,
        force_write: bool = False,
    ) -> Any:
        """Get configuration value from YAML by nested keys.

        Supports mixed positional arguments, single tuple/lists, and composite keys
        with separators (e.g. 'a.b.c', 'a:b', 'a', 'b', 'c').
        """
        if not keys:
            return format_value(default)

        # 1. Normalize and flatten positional keys
        if len(keys) == 1 and isinstance(keys[0], (list, tuple)):
            keys = keys[0] # Type "list[Unknown] | tuple[Unknown, ...]" is not assignable to declared type "tuple[Any, ...]"
            # Type "list[Unknown] | tuple[Unknown, ...]" is not assignable to type "tuple[Any, ...]"
            # "list[Unknown]" is not assignable to "tuple[Any, ...]" (Pyright[reportAssignmentType])

        parts: List[str] = _flatten_keys(keys)
        if not parts:
            return format_value(default)

        try:
            # 2. Ensure configuration mapping is loaded
            if not isinstance(getattr(self, 'yaml', None), dict):
                try:
                    self._load_config()
                except Exception as e:
                    if is_debug():
                        tprint()
                    else:
                        _print(
                            f":cross_mark: [white on red]ERROR:[/] [white on"
                            f" blue]{e}[/]"
                        )
                    self.yaml = {}

            if self.yaml is None:
                self.yaml = {}

            # 3. Traverse nested YAML mapping safely
            current = self.yaml
            found = True

            for seg in parts:
                if isinstance(current, dict) and seg in current:
                    current = current[seg]
                else:
                    found = False
                    break

            # 4. Process retrieved value or resolve fallback
            if found:
                formatted_val = format_value(current)
                # Return value if valid (not None or empty string)
                if formatted_val is not None and formatted_val != "":
                    if is_debug():
                        _print(f"🗝 [bold #00FFFF]found[/]=[bold #FFFF00]{formatted_val}[/]")
                    return formatted_val

            # 5. Handle fallback default when key is missing or empty
            fallback = default
            if fallback is None and hasattr(self, "default") and isinstance(self.default, dict):
                # Attempt lookup in self.default dictionary using primary key segment
                fallback = self.default.get(parts[0])

            formatted_fallback = format_value(fallback)

            # 6. Perform auto-write if requested
            should_write = force_write or (
                auto_write or getattr(self, "_auto_write", False)
            )
            if should_write and formatted_fallback is not None:
                if hasattr(self, "write_config"):
                    self.write_config(*parts, value=formatted_fallback)

            return formatted_fallback

        except Exception as e:
            if is_debug():
                _print(
                    f"\n:cross_mark: [white on red]Error getting config:[/] [white"
                    f" on blue]{e}[/]"
                )
            return format_value(default)

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
    #             if is_debug():
    #                 _print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
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
    #         if is_debug():
    #             _print(f"\n:cross_mark: [white on red]Error writing config:[/] [white on blue]{e}[/]")
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
                if is_debug():
                    _print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            # Normalize iterable (support single list/tuple arg or multiple args)
            if len(parts_src) == 1 and isinstance(parts_src[0], (list, tuple)):
                iterable = parts_src[0]
            else:
                iterable = parts_src

            # Flatten and split by separators using shared helper
            parts: List[str] = _flatten_keys(iterable)
            if not parts:
                if is_debug():
                    _print("\n:cross_mark: [bold #FFFF00]No key ![/]")
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
            if is_debug():
                _print(f"\n:cross_mark: [white on red]Error writing YAML config:[/] [white on blue]{e}[/]")
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
        
        from collections import deque

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
                if is_debug():
                    _print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
                return False

            # Normalize iterable (support single list/tuple arg or multiple args)
            if len(parts_src) == 1 and isinstance(parts_src[0], (list, tuple)):
                iterable = parts_src[0]
            else:
                iterable = parts_src

            # Flatten keys (split composite segments) using module helper
            parts: List[str] = _flatten_keys(iterable)
            if not parts:
                if is_debug():
                    _print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
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
            if is_debug():
                _print(f"\n:cross_mark: [white on red]Error removing config:[/] [white on blue]{e}[/]")
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
                if is_debug():
                    msg = "No key!"
                    _print(f"\n:cross_mark: [bold #FFFF00]{msg}[/]") if HAS_RICH else print(msg)
                return False

            d = self.yaml  # Fix: was self.json
            for k in keys[:-1]:
                if k in d and isinstance(d[k], dict):
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

            del d[last_key]
            self._save_config()
            return True

        except Exception as e:
            if is_debug():
                msg = f"Error removing key: {e}"
                _print(f"\n:cross_mark: [white on red]{msg}[/]") if HAS_RICH else print(msg)
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
                if is_debug():
                    _print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
                return {}

            d = self.yaml
            for k in keys[:-1]:
                if isinstance(d, dict) and k in d:
                    d = d[k]
                else:
                    if is_debug():
                        _print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{k}[/]")
                    return {}

            last_key = keys[-1]
            
            if isinstance(d, dict) and last_key in d:
                found = d[last_key]
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
        
