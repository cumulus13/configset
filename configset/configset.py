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
import sys
import argparse
import os
import traceback
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional

# printer
try:
    from . printer import HAS_RICH, rich_traceback, _print  # type: ignore
except:
    try:
        from printer import HAS_RICH, rich_traceback, _print  # type: ignore
    except:
        from configset.printer import HAS_RICH, rich_traceback, _print  # type: ignore

# debugger
try:
    from . debugger import debug  # type: ignore
except:
    try:
        from debugger import debug  # type: ignore
    except:
        from configset.debugger import debug  # type: ignore

try:
    from licface import CustomRichHelpFormatter
except:
    CustomRichHelpFormatter = argparse.RawTextHelpFormatter  # type: ignore

if HAS_RICH:    
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
            _print(f":biohazard_sign {traceback.format_exc()}")
        else:
            _print(f":cross_mark: [white on red]ERROR:[/] [white on blue]{e}[/]")

    return "0.0.0"

__version__ = get_version()
__platform__ = "all"
__contact__ = "cumulus13@gmail.com"
__author__ = "Hadi Cahyadi"
__all__ = ["ConfigSet", "CONFIG", "MultiOrderedDict", "__version__", "get_version", "ConfigSetIni", "ConfigSetYaml", "ConfigSetJson", "ConfigSetToml", "detect_file_type", "_validate_file_path", "ConfigMeta"]

# configset_general
try:
    from . configset_general import is_debug, detect_file_type, _validate_file_path  # type: ignore
except:
    try:
        from configset_general import is_debug, detect_file_type, _validate_file_path  # type: ignore
    except:
        from configset.configset_general import is_debug, detect_file_type, _validate_file_path  # type: ignore

# configset_ini
try:
    from . configset_ini import ConfigSetIni  # type: ignore
except:
    try:
        from configset_ini import ConfigSetIni  # type: ignore
    except:
        from configset.configset_ini import ConfigSetIni  # type: ignore

# configset_json
try:
    from . configset_json import ConfigSetJson  # type: ignore
except:
    try:
        from configset_json import ConfigSetJson  # type: ignore
    except:
        from configset.configset_json import ConfigSetJson  # type: ignore

# configset_yaml
try:
    from . configset_yaml import ConfigSetYaml  # type: ignore
except:
    try:
        from configset_yaml import ConfigSetYaml  # type: ignore
    except:
        from configset.configset_yaml import ConfigSetYaml  # type: ignore

# configset_toml
try:
    from . configset_toml import ConfigSetToml  # type: ignore
except:
    try:
        from configset_toml import ConfigSetToml  # type: ignore
    except:
        from configset.configset_toml import ConfigSetToml  # type: ignore


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

class ConfigSetTOML(ConfigSetToml):
    """Alias for ConfigSetToml with uppercase naming."""
    pass

class configsettoml(ConfigSetToml):
    """Alias for ConfigSetToml with lowercase naming."""
    pass

# small helper proxies for nicer dot-access with INI backend
class _IniSectionProxy:
    """Proxy for accessing INI file sections.

    Attributes:
        _backend(_IniBackend): Backend object for accessing INI data.
        _section(str): Name of the INI section.
    """
    def __init__(self, backend, section: str):
        """Initialize a new configuration manager instance.

        Args:
            self(ConfigurationManager): The ConfigurationManager instance.
            backend(Backend): The backend instance to use.
            section(str): The configuration section to manage.

        Returns:
            None: No return value.

        Raises:
            TypeError: Raised if the backend is not a valid Backend instance.
            ValueError: Raised if the section name is invalid.
        """
        self._backend = backend
        self._section = section

    def __getattr__(self, opt: str):
        """Get a configuration option value.

        Args:
            self(ConfigParser): The ConfigParser instance.
            opt(str): The name of the configuration option to retrieve.

        Returns:
            Union[str, None]: The value of the configuration option, or None if not found.

        Raises:
            AttributeError: Raised if the specified section or option doesn't exist.
            Exception: Raised if any other error occurs during configuration retrieval.
        """
        # return option value or default None
        try:
            return self._backend.get_config(self._section, opt)
        except Exception:
            raise AttributeError(f"Section '{self._section}' has no option '{opt}'")

    def items(self):
        """Retrieve items from a specific section.

        Args:
            self(self): Instance of the class.

        Returns:
            dict: A dictionary containing the items from the specified section. Returns an empty dictionary if the section is not found or is not a dictionary.

        Raises:
            KeyError: If the specified section does not exist in the backend.
            TypeError: If the retrieved section is not a dictionary.
        """
        sec = self._backend.get_section(self._section)
        return sec.get(self._section, {}) if isinstance(sec, dict) else {}

    def __repr__(self):
        """Returns an INI section proxy representation.

        Args:
            self(INIProxy): Instance of the INIProxy class.

        Returns:
            str: String representation of the INI section proxy.

        Raises:
            Exception: Generic exception during string representation.
        """
        return f"<INI section proxy {self._section}>"

class _IniOptionProxy:
    """Proxy for accessing INI-style configuration options.

    Attributes:
        _backend(object): Backend configuration object.
        _option(str): Name of the configuration option.
    """
    def __init__(self, backend, option: str):
        self._backend = backend
        self._option = option

    def __getattr__(self, section: str):
        """Get a configuration option value from a specific section.

        Args:
            self(Config): Instance of the Config class.
            section(str): Name of the configuration section.

        Returns:
            Any: Value of the configuration option if found; otherwise, raises AttributeError.

        Raises:
            AttributeError: Raised when the specified option is not found in the given section.
            Exception: Raised if any other error occurs during configuration retrieval.
        """
        # return value for this option under given section
        try:
            return self._backend.get_config(section, self._option)
        except Exception:
            raise AttributeError(f"Option '{self._option}' not found in section '{section}'")

    def find_all(self):
        """Find all values.

        Args:
            self(Any): The instance of the class.

        Returns:
            dict: A dictionary mapping section names to their values, where the option exists.

        Raises:
            Exception: If an error occurs during the find operation.
        """
        # return dict of section -> value where option exists
        return self._backend.find(self._option)

    def __repr__(self):
        """Return a string representation of the INI option proxy.

        Args:
            self(INIProxy): The INIProxy instance.

        Returns:
            str: A string representing the INI option proxy.

        Raises:
            Exception: Any exception raised during string formatting.
        """
        return f"<INI option proxy {self._option}>"

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
        
        if is_debug(): print(f"file_path [1]: {file_path}")
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
            import inspect
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

        if is_debug(): print(f"file_path [2]: {file_path}")
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
                elif ext == ".toml":
                    # "{}" is not valid TOML; an empty document is.
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
            "toml" if p.suffix.lower() == ".toml" else
            "ini" if p.suffix.lower() == ".ini" else
            "json"
        )
        if is_debug(): print(f"Detected file type for {p}: {file_type}")
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
            if is_debug():
                _print(f":warning: Skipping package __init__ file as config target: {p_resolved}")
            return None

        if is_debug():
            _print(f"Detected file type for {p_resolved}: {file_type}")
        
        if file_type == 'json':
            return ConfigSetJSON(json_file=file_path, **kwargs)
        if file_type in ('yaml', 'yml'):
            return ConfigSetYAML(yaml_file=file_path, **kwargs)
        if file_type == 'toml':
            return ConfigSetTOML(toml_file=file_path, **kwargs)
        if file_path.endswith(".toml"):
            return ConfigSetTOML(toml_file=file_path, **kwargs)
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
                from functools import wraps
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
        
        # INI: prefer section proxy (CONFIG.section.option), otherwise option proxy (CONFIG.option.section)
        elif hasattr(cls, '_config_instance') and isinstance(cls._config_instance, ConfigSetINI):
            inst = cls._config_instance
            # If the name is an existing INI section, return the concrete section mapping
            try:
                if inst.has_section(name):
                    # get_section returns {section: {option: value, ...}} or None
                    return inst.get_section(name)
            except Exception:
                # fallthrough to option lookup
                pass
            # Otherwise if the name matches an option somewhere, return an OptionProxy
            try:
                found = inst.find(name)
                if found:
                    return _IniOptionProxy(inst, name)
            except Exception:
                pass


        elif hasattr(cls, '_config_instance') and not str(name).isdigit() and isinstance(cls._config_instance, ConfigSetINI):
            if is_debug(): print('configsetini instance ...')
            if hasattr(cls._config_instance, 'get_section'):
                return cls._config_instance.get_section(name)

        elif hasattr(cls, '_config_instance') and not str(name).isdigit() and isinstance(cls._config_instance, ConfigSetJSON):
            if is_debug(): print('configsetjson instance ...')
            if hasattr(cls._config_instance, 'get_key'):
                return cls._config_instance.get_key(name)

        elif hasattr(cls, '_config_instance') and not str(name).isdigit() and isinstance(cls._config_instance, ConfigSetYAML):
            if is_debug(): print('configsetyaml instance ...')
            if hasattr(cls._config_instance, 'get_document'):
                return cls._config_instance.get_document(name)

        if hasattr(cls, 'data') and name in cls.data:
            return cls.data.get(name)
            
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
    #             return inst.print_all_config() 
    #         if hasattr(inst, 'show'):
    #             return inst.show()
    #         if hasattr(inst, 'print'):
    #             return inst.print()
    #     else:
    #         _print(":cross_mark: [white on red]No config instance found.[/]")
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
    - The class uses helper functions/objects such as is_debug() and _console
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
            JSONDecodeError: Raised if the JSON file is invalid.
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
        _print(f":cross_mark: [white on red]Attribute not found:[/] [white on blue]{name}[/]")
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
                self.config.set(name, value)  # type: ignore
            elif isinstance(self.config, ConfigSetIni):
                value = re.split(r"[:;| ]", value)
                if len(value) > 2:
                    self.config.set(name, dict(zip(value[::2], value[1::2])))  # type: ignore
                else:
                    self.config.set(name, value[0])  # type: ignore
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
        _print(":cross_mark: [white on redError:[/] [white on blue]Configuration file is required[/]")
        parser.print_help()
        return
    
    try:
        config = ConfigSet(args.config_file)
        
        # Determine the key to use (option or key)
        key = args.option or args.key
        
        if args.all or args.show:
            if hasattr(config, 'show'):
                config.show()  # type: ignore
            elif hasattr(config, 'print_all_config'):
                config.print_all_config() # type: ignore
            else:
                _print(f":cross_mark: [white on red]Configuration display not supported for this file type.[/]")

        elif args.read:
            # Handle different file types
            if hasattr(config, 'get_config') and args.section:
                # INI file with section and option
                if not key:
                    _print(":cross_mark: [white on red]Error:[/] [white on blue]Key/option required for INI read operation[/]")
                    return
                    
                if args.list:
                    value = config.get_config_as_list(args.section, key) # type: ignore
                elif args.dict:
                    value = config.get_config_as_dict(args.section, key) # type: ignore
                else:
                    value = config.get_config(args.section, key)  # type: ignore
                
                print(f"[{args.section}] {key} = {value}")
                
            elif hasattr(config, 'get_config') and not args.section:
                # JSON or YAML file with key only
                if not key:
                    _print(":cross_mark: [white on red]Error:[/] [white on blue]Key required for read operation[/]")
                    return
                    
                value = config.get_config(key) # type: ignore
                _print(f"{key} = {value}")
            else:
                _print(":cross_mark: [white on red]Error:[/] [white on blue]Unsupported read operation for this file type[/]")
                return
            
        elif args.write:
            # Handle different file types
            if hasattr(config, 'write_config') and args.section:
                # INI file with section and option
                if not key:
                    _print(":cross_mark: [white on red]Error:[/] [white on blue]Key/option required for INI write operation[/]")
                    return
                
                value = args.value or ''
                result = config.write_config(args.section, key, value)  # type: ignore
                _print(f":white_check_mark: [white on green]Written:[/] [white on blue][{args.section}] {key} = {result}[/]")
                
            elif hasattr(config, 'write_config') and not args.section:
                # JSON or YAML file with key only
                if not key:
                    _print(":cross_mark: [white on red]Error:[/] [white on blue]Key required for write operation[/]")
                    return
                
                value = args.value or ''
                success = config.write_config(key, value)  # type: ignore
                if success:
                    _print(f":white_check_mark: [white on green]Written:[/] [white on blue]{key} = {value}[/]")
                else:
                    _print(f":cross_mark: [white on red]Failed to write:[/] [white on blue]{key}[/]")
            else:
                _print(":cross_mark: [white on red]Error:[/] [white on blue]Unsupported write operation for this file type[/]")
                return
            
        elif args.delete:
            # Handle different file types
            if hasattr(config, 'remove_config') and args.section:
                # INI file
                if key:
                    # Remove specific option
                    success = config.remove_config(args.section, key)  # type: ignore
                    if success:
                        _print(f":white_check_mark: [white on green]Removed:[/] [white on blue][{args.section}] {key}[/]")
                    else:
                        _print(f":cross_mark: [white on red]Not found:[/] [white on blue][{args.section}] {key}[/]")
                else:
                    # Remove entire section
                    success = config.remove_config(args.section)  # type: ignore
                    if success:
                        _print(f":white_check_mark: [white on green]Removed section:[/] [white on blue][{args.section}][/]")
                    else:
                        _print(f":cross_mark: [white on red]Section not found:[/] [white on blue][{args.section}][/]")
            elif hasattr(config, 'remove_config') and not args.section:
                # JSON or YAML file
                if not key:
                    _print(":cross_mark: [white on red]Error:[/] [white on blue]Key required for delete operation[/]")
                    return
                    
                success = config.remove_config(key)  # type: ignore
                if success:
                    _print(f":white_check_mark: [white on green]Removed:[/] [white on blue]{key}[/]")
                else:
                    _print(f":cross_mark: [white on red]Key not found:[/] [white on blue]{key}[/]")
            else:
                _print(":cross_mark: [white on red]Error:[/] [white on blue]Unsupported delete operation for this file type[/]")
                return
            
        else:
            _print(":cross_mark: [white on red]Error:[/] [white on blue]Specify --read, --write, --delete, --all, or --show[/]")
            parser.print_help()
            
    except Exception as e:
        _print(f":cross_mark: [white on red]Error:[/] [white on blue]{e}[/]")
        if is_debug():
            traceback.print_exc()


if __name__ == '__main__':
    main()
