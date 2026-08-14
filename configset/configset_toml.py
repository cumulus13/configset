#!/usr/bin/env python3

# File: configset_toml.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-08-12
# Description: TOML-backed configuration backend, mirroring ConfigSetYaml / ConfigSetJson.
# License: MIT

# general
import re
from pathlib import Path
from typing import Any, List
import os

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
    from . general import _flatten_keys, load_default, format_value  # type: ignore
except:
    try:
        from general import _flatten_keys, load_default, format_value  # type: ignore
    except:
        from configset.configset_general import _flatten_keys, load_default, format_value  # type: ignore

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
    from . debugger import is_debug, logger  # type: ignore
except:
    try:
        from debugger import is_debug, logger  # type: ignore
    except:
        from configset.debugger import is_debug, logger  # type: ignore

# --- TOML read/write backend detection -------------------------------------------------
# Reading: stdlib `tomllib` (Python 3.11+, read-only) preferred, falls back to the
#          `tomli` backport for older interpreters, and finally the pure-python `toml`
#          package if neither of the above is installed.
# Writing: TOML has no read/write module in the stdlib. `tomli_w` is preferred (pairs
#          naturally with tomllib/tomli), falling back to the `toml` package, which can
#          both read and write. If nothing is available, write operations raise a clear
#          ConfigurationError telling the user what to install; read-only usage still
#          works fine in that case.
HAS_TOMLLIB = False
HAS_TOMLI = False
HAS_TOMLI_W = False
HAS_TOML = False

_toml_loads = None   # callable(str) -> dict
_toml_dumps = None   # callable(dict) -> str

try:
    import tomllib as _tomllib  # type: ignore
    HAS_TOMLLIB = True
    _toml_loads = _tomllib.loads
except ImportError:
    try:
        import tomli as _tomli  # type: ignore
        HAS_TOMLI = True
        _toml_loads = _tomli.loads
    except ImportError:
        pass

try:
    import tomli_w as _tomli_w  # type: ignore
    HAS_TOMLI_W = True
    _toml_dumps = _tomli_w.dumps
except ImportError:
    pass

if _toml_loads is None or _toml_dumps is None:
    try:
        import toml as _toml  # type: ignore
        HAS_TOML = True
        if _toml_loads is None:
            _toml_loads = _toml.loads
        if _toml_dumps is None:
            _toml_dumps = _toml.dumps
    except ImportError:
        pass


class ConfigSetToml:
    """
    ConfigSetToml
    =============
    A lightweight TOML-backed configuration helper mirroring ConfigSetYaml / ConfigSetJson.
    Designed to be tolerant of missing files and invalid TOML content (falls back to an
    empty mapping) and to support nested key access with flexible key separators.

    Initialization
    --------------
    ConfigSetToml(toml_file: str = '', config_file: str = '', **kwargs)
    - toml_file / config_file: Path to a TOML file or raw TOML text. If both are empty,
        an instance with an empty configuration is created and can be populated and saved
        later.
    - kwargs: Reserved for future extensions; stored on the instance.

    Backend requirements
    ---------------------
    - Reading requires one of: stdlib `tomllib` (Python 3.11+), `tomli`, or `toml`.
    - Writing requires one of: `tomli_w` or `toml`.
    - If no reader is available, `_load_config` logs a warning and falls back to an
        empty mapping rather than raising, matching the YAML/JSON backends' tolerance for
        missing optional dependencies.
    - If no writer is available, any method that would persist to disk
        (`write_config`, `remove_config`, `remove_key`, `dump`, `dumps`, ...) raises
        `ConfigurationError` with an actionable install hint.

    Key behaviors
    -------------
    - Loading:
        - load(toml_file=None) / read(toml_file=None): Load configuration from a file path
            or from a TOML string (delegates to _load_config / loads).
        - loads(toml_file): Accepts a path, TOML string, bytes, or a dict. If given a path
            that exists, file is read; else attempts TOML parsing. Raises TypeError for
            unsupported input types.
        - _load_config(toml_file=None): Internal loader with robust error handling:
            FileNotFound -> logs warning and returns {}, PermissionError -> raises
            ConfigurationError, UnicodeDecodeError -> raises ConfigurationError,
            TOML parse errors -> logs warning and returns {}.
    - Saving:
        - _save_config(toml_file=''): Internal helper that writes TOML to disk. Ensures
            parent directories exist and raises ConfigurationError when no target file is
            provided or no TOML writer backend is installed.
        - dump(...): Writes current configuration to the configured file (self.toml_file)
            and returns the in-memory mapping.
        - dumps(...): Returns a TOML string representation of the current configuration.
    - Inspection and display:
        - show(): Pretty-prints the configuration using optional helpers (jsoncolor, rich,
            makecolor) and falls back to plain TOML/text dump.
        - print(): Alias for show().
        - filename / config_file / configname: Properties returning the current filename.
    - Accessing values:
        - get_config(*keys, default=None): Retrieve nested values using flexible key forms
            (multiple positional keys, single composite key with '.', ':', ';', '|'
            separators, or a single list/tuple of keys). Returns `default` if the path is
            not found or an error occurs.
        - get / read_config: Convenience wrappers around get_config.
    - Mutating values:
        - write_config(*keys, value=None) -> bool: Write a value to a nested path. Supports
            the same flexible key formats as get_config. If the last positional argument is
            the value (and `value` kw is omitted), it is accepted. Creates intermediate
            mappings as needed. Persists changes to disk via _save_config. Returns True on
            success, False on error.
        - set: Alias to write_config.
    - Removing values/keys:
        - remove_value_anywhere(value) -> bool: Recursively scans the entire configuration
            and removes all occurrences of the provided value (from dictionary values and
            list items). Persists if any removal occurs.
        - remove_config(*keys, value=None) -> bool: Remove a key at a nested path or remove
            a specific value from a keyed list. If called with only value=..., delegates to
            remove_value_anywhere.
        - remove_key(key: str) -> bool and remove_section(key: str): Remove a key and its
            children. `key` may be a nested key using separators (":", ";", "|").
    - Finding values:
        - find(*keys, value=None): Similar to get_config but returns {} when not found.
        - find1(key: str, value=None): Backward-compatible single-string-key helper.

    Notes
    -----
    - TOML has no native representation for `None`/null. Writing a value of `None`
        removes the key instead of writing it, to avoid a TypeError from the writer
        backend; this mirrors how most TOML writers behave and is called out explicitly
        so it isn't a silent surprise.
    - Key splitting and flattening logic is implemented via the shared `_flatten_keys`
        helper which understands separators (., :, ;, |).

    Examples
    --------
    Basic usage:
            cfg = ConfigSetToml('config.toml')
            value = cfg.get_config('section', 'option', default=42)
    Write and persist:
            cfg.write_config('servers', 'web', value={'host': 'example', 'port': 80})
            cfg.set('servers.web.host', value='example')
    Remove operations:
            cfg.remove_config('section', 'option')
            cfg.remove_config('section', 'list', value=3)
            cfg.remove_config(value='unwanted')
    """

    def __init__(self, toml_file: str = '', config_file: str = '', default: Any = None, **kwargs):
        self.toml_file = toml_file or config_file
        self.file = self.toml_file
        self.kwargs = kwargs
        self.toml = self._load_config()

        self.default_config = {}
        if default:
            self.default_config = load_default(default)
        self.default = self.default_config

    def _require_reader(self):
        if _toml_loads is None:
            msg = ("No TOML reader available. Install one of: 'tomli' (pip install tomli) "
                   "or 'toml' (pip install toml). On Python 3.11+ the stdlib 'tomllib' "
                   "should already provide this.")
            raise ConfigurationError(msg)

    def _require_writer(self):
        if _toml_dumps is None:
            msg = ("No TOML writer available. Install one of: 'tomli-w' (pip install tomli-w) "
                   "or 'toml' (pip install toml) to enable saving TOML configuration.")
            raise ConfigurationError(msg)

    def load(self, toml_file=None):
        """
        Load TOML data from file.

        :param toml_file: Path to a TOML file to load. If omitted, uses self.toml_file.
        """

        return self._load_config(toml_file)

    def loads(self, toml_file: str = ''):
        """
        Load TOML configuration from a file path, raw TOML string, bytes, or dict.

        :param toml_file: A path to an existing TOML file, raw TOML text, bytes, or a
            dict. If a path that exists is given, the file is read; otherwise the value
            is parsed directly. Raises TypeError for unsupported input types.
        """

        if not toml_file:
            return self._load_config(toml_file)
        if isinstance(toml_file, str) and os.path.isfile(toml_file):
            return self._load_config(toml_file)
        else:
            self._require_reader()
            if isinstance(toml_file, str):
                self.toml = _toml_loads(toml_file)
            elif isinstance(toml_file, bytes):
                self.toml = _toml_loads(toml_file.decode("utf-8"))
            elif isinstance(toml_file, dict):
                self.toml = toml_file
            else:
                if is_debug():
                    _print(f"\n:cross_mark: [white on red]Invalid TOML input:[/] [white on blue]{toml_file}[/]")
                raise TypeError(f"Invalid TOML input: {type(toml_file)}")
            return self.toml

    def read(self, toml_file: str = ''):
        """Read and load a TOML file (alias for loads)."""

        return self.loads(toml_file)

    def _load_config(self, toml_file=None):
        """
        Load configuration from file with error handling.

        :param toml_file: Path to the TOML configuration file. If omitted, falls back to
            self.toml_file.
        :return: The loaded TOML configuration data as a dict, or {} on tolerated errors
            (missing file, parse error, missing optional dependency).
        """

        source = toml_file or self.toml_file
        if is_debug():
            _print(f"\n:gear: [white on blue]Loading TOML config:[/] [white on blue]{source}[/]")
            _print(f":mag: [white on blue]TOML File is File:[/] [white on blue]{os.path.isfile(source) if source else False}[/]")

        if not source:
            self.toml = {}
            return self.toml

        if _toml_loads is None:
            logger.warning("No TOML reader available (install 'tomli' or 'toml'); "
                            "falling back to an empty configuration.")
            if is_debug():
                _print(":warning: [white on red]No TOML reader available — "
                       "install 'tomli' or 'toml'.[/]")
            self.toml = {}
            return self.toml

        try:
            if os.path.isfile(source):
                with open(source, "r", encoding="utf-8") as f:
                    text = f.read()
                self.toml = _toml_loads(text)
                if is_debug():
                    _print(":white_check_mark: (1) [white on green]TOML config loaded successfully from file.[/]")
                    _print(f":gear: [white on blue] (1) TOML data type:[/] [white on blue]{type(self.toml)}[/]")
            else:
                self.toml = _toml_loads(source)
                if is_debug():
                    _print(":white_check_mark: (2) [white on green]TOML config loaded successfully from string.[/]")
                    _print(f":gear: [white on blue] (2) TOML data type:[/] [white on blue]{type(self.toml)}[/]")
            if self.toml is None:
                self.toml = {}
            return self.toml
        except FileNotFoundError:
            if is_debug():
                _print(f"[:cross_mark: [white on red]Config file not found:[/] [white on blue]{source}[/]")
            logger.warning(f"Config file not found: {source}")
        except PermissionError:
            if is_debug():
                _print(f":cross_mark: [white on red]Permission denied accessing:[/] [white on blue]{source}[/]")
            logger.error(f"Permission denied accessing: {source}")
            raise ConfigurationError(f"Cannot access config file: {source}")
        except UnicodeDecodeError as e:
            if is_debug():
                _print(f":cross_mark: [white on red]Invalid encoding in config file:[/] [white on blue]{e}[/]")
            logger.error(f"Invalid encoding in config file: {e}")
            raise ConfigurationError(f"Config file has invalid encoding: {e}")
        except Exception as e:
            # Covers tomllib.TOMLDecodeError / tomli.TOMLDecodeError / toml.TomlDecodeError
            # without importing any of them by name (whichever backend is active).
            logger.warning("Invalid TOML content in %s: %s", source, e)
            if is_debug():
                _print(f":cross_mark: [white on red]Invalid TOML content:[/] [white on blue]{e}[/]")
            self.toml = {}
            return self.toml

        self.toml = {}
        return self.toml

    def _strip_none(self, data):
        """Recursively drop keys whose value is None (TOML has no null type)."""

        if isinstance(data, dict):
            return {k: self._strip_none(v) for k, v in data.items() if v is not None}
        if isinstance(data, list):
            return [self._strip_none(v) for v in data if v is not None]
        return data

    def _save_config(self, toml_file: str = ''):
        """
        Save the current TOML configuration to the file.

        :param toml_file: Path where the current TOML configuration will be saved. If
            omitted, uses self.toml_file.
        """

        target = toml_file or self.toml_file
        if not target:
            raise ConfigurationError("No TOML file configured for saving")
        self._require_writer()
        if self.toml is None:
            self.toml = {}
        try:
            p = Path(target)
            if not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
            text = _toml_dumps(self._strip_none(self.toml))
            with open(target, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            logger.error("Error saving TOML config: %s", e)
            if is_debug():
                _print(f":cross_mark: [white on red]Error saving TOML config:[/] [white on blue]{e}[/]")
            raise

    def dump(self, *args, **kwargs):
        """
        Write the current TOML configuration to self.toml_file and return the mapping.
        """

        self._require_writer()
        with open(self.toml_file, "w", encoding="utf-8") as f:
            f.write(_toml_dumps(self._strip_none(self.toml)))
        return self.toml

    def dumps(self, *args, **kwargs):
        """Return the current TOML configuration as a string."""

        self._require_writer()
        return _toml_dumps(self._strip_none(self.toml))

    def show(self):
        """Show the current TOML configuration using the best available printer."""

        if HAS_JSONCOLOR:
            jprint(self.toml)
        elif HAS_RICH:
            _print(self.toml)
        elif HAS_MAKE_COLORS and make_colors:
            print(make_colors(self.toml, 'lc'))
        else:
            if _toml_dumps is not None:
                print(_toml_dumps(self._strip_none(self.toml)))
            else:
                print(self.toml)

    def print(self):
        """Alias for show()."""

        return self.show()

    def print_all_config(self):
        """Alias for show()."""

        return self.show()

    @property
    def filename(self):
        """Get the filename of the TOML configuration file."""

        return str(self.toml_file)

    @property
    def configfile(self):
        """Alias for filename."""

        return self.filename

    @property
    def config_file(self):
        """Alias for filename."""

        return self.filename

    @property
    def configname(self):
        """Alias for filename."""

        return self.filename

    def exists(self, key):
        """Check if a top-level configuration key exists."""

        if isinstance(self.toml, dict):
            return key in self.toml
        return False

    def get_config_file(self):
        """Get the filename of the TOML configuration file."""

        return str(self.toml_file)

    def set_config_file(self, config_file: str) -> bool:
        """
        Set a new configuration file path and load it if it exists.

        :param config_file: Path to the new TOML configuration file.
        :return: True if the new configuration file path was set and loaded/initialized,
            False if config_file is empty or an error occurred.
        """

        if os.path.isfile(config_file):
            self.toml_file = config_file
            self._load_config()
            return True
        else:
            _print("\n:cross_mark: [white on red]Invalid TOML File ![/]")
            return False

    def get_config(self, *keys, default=None):
        """
        Get configuration value of TOML by nested keys.

        Usage:
            get_config('a')                     -> top-level key 'a'
            get_config('a', 'b', 'c')           -> nested access a.b.c
            get_config('a.b.c')                 -> single composite key (dot or :;| separators supported)
            get_config(['a','b','c'])           -> list/tuple of keys
            get_config(...)                     -> returns `default` if key path not found
        """

        if not keys:
            return format_value(default)

        if len(keys) == 1 and isinstance(keys[0], (list, tuple)):
            keys = keys[0]
            if is_debug():
                _print(f"🗝 [bold #00FFFF]keys[/]=[bold #FFFF00]{keys}[/]")

        parts: List[str] = _flatten_keys(keys)
        if not parts:
            return format_value(default)

        try:
            if not isinstance(getattr(self, 'toml', None), dict):
                try:
                    self._load_config()
                except Exception as e:
                    if is_debug():
                        _print(f":cross_mark: [white on red]ERROR:[/] [white on blue]{e}[/]")
                    self.toml = {}

            if self.toml is None:
                self.toml = {}

            # Traverse the nested mapping, tracking whether the full path was found so a
            # partially-missing path (e.g. 'server' exists but 'server.port' doesn't)
            # correctly falls through to `default` instead of returning the last dict
            # reached along the way.
            current = self.toml
            found = True
            for seg in parts:
                if isinstance(current, dict) and seg in current:
                    current = current[seg]
                else:
                    found = False
                    break

            if found:
                formatted_val = format_value(current)
                if formatted_val is not None and formatted_val != "":
                    if is_debug():
                        _print(f"🗝 [bold #00FFFF]found[/]=[bold #FFFF00]{formatted_val}[/]")
                    return formatted_val

            fallback = default
            if fallback is None and self.default and isinstance(self.default, dict):
                fallback = self.default.get(parts[0])

            return format_value(fallback)

        except Exception as e:
            if is_debug():
                _print(f"\n:cross_mark: [white on red]Error getting config:[/] [white on blue]{e}[/]")
            return format_value(default)

    def get(self, *keys, default=None):
        """Get configuration value by key (alias for get_config)."""

        return self.get_config(*keys, default=default)

    def get_document(self, *keys, default=None):
        """Get document configuration value by key (alias for get_config)."""

        return self.get_config(*keys, default=default)

    def read_config(self, *keys, default=None):
        """Read configuration value by key (alias for get_config)."""

        return self.get_config(*keys, default=default)

    def write_config(self, *keys, value: Any = None) -> bool:
        """
        Write configuration value by nested keys (TOML backend).

        Accepts:
          - write_config('a.b.c', 'value')
          - write_config('a','b','c', value='value')
          - write_config('a','b','c','value')  (last positional becomes value if value kw not used)

        Behavior:
          - flexible key formats: dotted or separators (.,:,;,|)
          - supports mixed positional args where any arg containing separators is split in-place
          - normalizes root to a dict if None or not a mapping
          - a value of None removes the key instead of writing it (TOML has no null type)
          - returns True on success, False on error
        """

        try:
            parts_src = list(keys)

            if value is None and len(parts_src) >= 2:
                value = parts_src.pop(-1)

            if not parts_src:
                if is_debug():
                    _print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            if len(parts_src) == 1 and isinstance(parts_src[0], (list, tuple)):
                iterable = parts_src[0]
            else:
                iterable = parts_src

            parts: List[str] = _flatten_keys(iterable)
            if not parts:
                if is_debug():
                    _print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            if not isinstance(self.toml, dict):
                self.toml = {}

            d = self.toml
            for k in parts[:-1]:
                if k not in d or not isinstance(d[k], dict):
                    d[k] = {}
                d = d[k]

            if value is None:
                d.pop(parts[-1], None)
            else:
                d[parts[-1]] = value

            self._save_config()
            return True

        except Exception as e:
            if is_debug():
                _print(f"\n:cross_mark: [white on red]Error writing TOML config:[/] [white on blue]{e}[/]")
            return False

    def set(self, *keys, value: Any = None):
        """Set configuration value by key (alias for write_config)."""

        return self.write_config(*keys, value=value)

    def remove_value_anywhere(self, value):
        """
        Remove all occurrences of a value from the TOML structure.

        :return: True if the value was found and removed at least once, False otherwise.
        """

        from collections import deque

        q = deque([self.toml])
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
        Remove configuration key or value (TOML backend).

        Usage:
          - remove_config('a:b:c')                      -> remove key c under a.b
          - remove_config('a','b','c')                  -> same as above (remove key c)
          - remove_config('a','b','c', value='v')       -> remove specific value or list item
          - remove_config(value='v')                    -> remove value anywhere (delegates)

        Note: unlike write_config, the LAST positional argument is never inferred as a
        `value` filter here. remove_config('section', 'option') removes the 'option'
        key — it does not treat 'option' as a value to search for. Pass `value=` explicitly
        if you want to remove a specific value or list item instead of the key itself.
        (The sibling YAML/JSON backends currently infer the last positional as `value`
        whenever 2+ positional args are given with no `value=` kwarg, which means their
        most natural call form, remove_config('section', 'option'), silently does nothing
        and returns False. That inference is intentionally not replicated here.)
        """

        if not keys and value is not None:
            return self.remove_value_anywhere(value)

        try:
            parts_src = list(keys)

            if not parts_src:
                if is_debug():
                    _print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            if len(parts_src) == 1 and isinstance(parts_src[0], (list, tuple)):
                iterable = parts_src[0]
            else:
                iterable = parts_src

            parts: List[str] = _flatten_keys(iterable)
            if not parts:
                if is_debug():
                    _print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            if not isinstance(self.toml, dict):
                try:
                    self._load_config()
                except Exception:
                    self.toml = {}
            if self.toml is None:
                self.toml = {}

            d = self.toml
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
        Remove key and its children (supports nested keys via ':' ';' '|' separators).
        """

        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]
            if not keys:
                if is_debug():
                    msg = "No key!"
                    _print(f"\n:cross_mark: [bold #FFFF00]{msg}[/]") if HAS_RICH else print(msg)
                return False

            d = self.toml
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
        """Alias for remove_key."""

        return self.remove_key(key)

    def find1(self, key: str, value=None):
        """
        Find a value by a single ':' ';' '|'-separated composite key string.

        :return: The found value, or {} if the key or value is not found.
        """

        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]
            if not keys:
                if is_debug():
                    _print("\n:cross_mark: [bold #FFFF00]No key ![/]")
                return {}

            d = self.toml
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
        except Exception:
            if is_debug():
                _print(f"\n:cross_mark: [white on red]Error finding key:[/] [white on blue]{key}[/]")
            return {}

    def find(self, *keys, value=None):
        """
        Find a value by nested keys (TOML backend).

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

            if not isinstance(self.toml, dict):
                try:
                    self._load_config()
                except Exception:
                    self.toml = {}
            d = self.toml or {}

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


class ConfigSetTOML(ConfigSetToml):
    """Alias for ConfigSetToml with uppercase naming."""
    pass


class configsettoml(ConfigSetToml):
    """Alias for ConfigSetToml with lowercase naming."""
    pass
