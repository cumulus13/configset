#!/usr/bin/env python3

# File: configset_general.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-08-11
# Description: 
# License: MIT

import os
import re
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path

SEP_RE = re.compile(r'[.:;|]')

# debugger
try:
    from . debugger import is_debug, tprint  # type: ignore
except:
    try:
        from debugger import is_debug, tprint  # type: ignore
    except:
        from configset.debugger import is_debug, tprint  # type: ignore

# icons
try:
    from . icons import Icons  # type: ignore
except:
    try:
        from icons import Icons  # type: ignore
    except:
        from configset.icons import Icons  # type: ignore

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
    from . printer import _print  # type: ignore
except:
    try:
        from printer import _print  # type: ignore
    except:
        from configset.printer import _print  # type: ignore

def _debug_enabled() -> bool:
    """
    Check if debug mode is enabled via environment variables.
    The function `_debug_enabled()` checks if debug mode is enabled based on specific environment
    variables.
    :return: The function `_debug_enabled()` returns a boolean value indicating whether debug mode is
    enabled based on the values of the environment variables `CONFIGSET_DEBUG` 
    in ['1', 'true', 'yes', 'True', 'TRUE'].
    """
    
    # return (os.getenv('DEBUG', '').lower() in ['1', 'true', 'yes'] or os.getenv('DEBUG_SERVER', '').lower() in ['1', 'true', 'yes'])
    return str(os.getenv('CONFIGSET_DEBUG', '')).lower() in ('1', 'true', 'yes', 'true')

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

    import yaml
    import json

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
        elif ext == '.toml':
            return 'toml'
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

    # Try TOML detection (checked before YAML, since YAML's safe_load is permissive
    # enough to sometimes mis-parse TOML-flavored text)
    try:
        try:
            from . configset_toml import _toml_loads as _detect_toml_loads  # type: ignore
        except Exception:
            try:
                from configset_toml import _toml_loads as _detect_toml_loads  # type: ignore
            except Exception:
                from configset.configset_toml import _toml_loads as _detect_toml_loads  # type: ignore
        if _detect_toml_loads is not None and ('=' in data) and not data.lstrip().startswith(('{', '[')):
            _detect_toml_loads(data)
            return "toml"
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
    import configparser
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
        from . configset_error import ConfigurationError  # type: ignore
    except:
        try:
            from configset_error import ConfigurationError  # type: ignore
        except:
            from configset.configset_error import ConfigurationError  # type: ignore

    try:
        path = Path(file_path).resolve()
        # Basic path traversal protection
        if '..' in str(path) or str(path).startswith('/'):
            raise ValueError("Potentially unsafe path detected")
        return path
    except (ValueError, OSError) as e:
        raise ConfigurationError(f"Invalid file path: {e}")
    
def load_default(data=None, default_config=None):
    # type: (Any, Optional[Dict]) -> Dict[str, Any]
    """
    Load configuration data from various sources: dict, JSON/YAML/TOML/INI file paths or strings.
    
    Supports:
    - Dict input
    - File paths ending in .json/.yaml/.yml/.toml/.ini
    - Raw JSON/YAML/TOML/INI strings

    Note: the parameter annotations above are intentionally written as a comment-style
    type hint (rather than `data: Any | None = None`) so this module keeps importing on
    Python versions before 3.10, which don't support the `X | Y` union syntax in a
    default-value position without `from __future__ import annotations`.

    Returns:
    - A dictionary representation of the config.
    """

    import yaml
    import json

    if not data and default_config:
        return default_config if isinstance(default_config, dict) else {}

    valid_ext = (".ini", ".json", ".yaml", ".yml", ".toml")
    default_config = {}

    if isinstance(data, bytes):
        data = data.decode()

    if isinstance(data, dict):
        default_config = data
    elif isinstance(data, str):
        if os.path.isfile(data):
            ext = os.path.splitext(data)[1].lower()
            if ext in valid_ext:
                try:
                    if ext == ".json":
                        with open(data, 'r', encoding='utf-8') as f:
                            default_config = json.load(f)
                    elif ext in (".yaml", ".yml"):
                        with open(data, 'r', encoding='utf-8') as f:
                            default_config = yaml.safe_load(f)
                    elif ext == ".toml":
                        try:
                            from . configset_toml import _toml_loads  # type: ignore
                        except Exception:
                            try:
                                from configset_toml import _toml_loads  # type: ignore
                            except Exception:
                                from configset.configset_toml import _toml_loads  # type: ignore
                        if _toml_loads is None:
                            raise ConfigurationError(
                                "No TOML reader available (install 'tomli' or 'toml') "
                                "to load default config from a .toml file")
                        with open(data, 'r', encoding='utf-8') as f:
                            default_config = _toml_loads(f.read())
                    elif ext == ".ini":
                        import configparser
                        config = configparser.ConfigParser()
                        config.read(data, encoding='utf-8')
                        default_config = {section: dict(config.items(section)) for section in config.sections()}
                except Exception as e:
                    if is_debug():
                        tprint()
                    else:
                        _print(f"{Icons.ERROR} [white on red]{e}[/]")
            else:
                # Try to parse as raw string content
                try:
                    default_config = json.loads(data)
                except Exception:
                    try:
                        default_config = yaml.safe_load(data)
                    except Exception:
                        try:
                            import configparser
                            config = configparser.ConfigParser()
                            config.read_string(data)
                            default_config = {section: dict(config.items(section)) for section in config.sections()}
                        except Exception as e:
                            if is_debug():
                                tprint()
                            else:
                                _print(f"{Icons.ERROR} [white on red]{e}[/]")
        else:
            # Try to parse as raw string content
            try:
                default_config = json.loads(data)
            except Exception:
                try:
                    default_config = yaml.safe_load(data)
                except Exception:
                    try:
                        import configparser
                        config = configparser.ConfigParser()
                        config.read_string(data)
                        default_config = {section: dict(config.items(section)) for section in config.sections()}
                    except Exception as e:
                        if is_debug():
                            tprint()
                        else:
                            _print(f"{Icons.ERROR} [white on red]{e}[/]")
    elif isinstance(data, (tuple, list)):
        # Convert list/tuple to dict if needed
        default_config = dict(enumerate(data))
    else:
        return {}

    return default_config if isinstance(default_config, dict) else {}

def get_default(*keys, default = None):
    parts = _flatten_keys(keys)
    _default = None
    if default:
        _default = load_default(default)
    if not _default:
        return None

    current = _default
    if current:
        for seg in parts:
            key = seg
            if isinstance(current, dict) and seg in current:
                current = current[seg]
            
        if current == _default:
            current = None

    return current

def format_value(value:Any):
    """Convert a value to its appropriate Python type.

    Args:
        value(Any): The value to format.

    Returns:
        Any: The formatted value.

    """

    if value is not None and isinstance(value, bytes):
        if is_debug():
            _print(f"\n:information: [black on #00FFFF]Decoding bytes value:[/] [white on blue]{value}[/]")
        value = value.decode()
    if value is not None and isinstance(value, str) and str(value).isdigit():
        if is_debug():
            _print(f"\n:information: [black on #00FFFF]Converting string to int:[/] [white on blue]{value}[/]")
        value = int(value)
    elif value is not None and isinstance(value, str) and str(value).replace(".", "").isdigit() and len(str(value).split(".")) == 2:
        if is_debug():
            _print(f"\n:information: [black on #00FFFF]Converting string to float:[/] [white on blue]{value}[/]")
        value = float(value)
    elif value is not None and str(value).lower() in ['true', 'false']:
        if is_debug():
            _print(f"\n:information: [black on #00FFFF]Converting string to bool:[/] [white on blue]{value}[/]")
        value = str(value).lower() == 'true'
    elif value is not None and str(value).lower() in ['null', 'none']:
        if is_debug():
            _print(f"\n:information: [black on #00FFFF]Converting string to None:[/] [white on blue]{value}[/]")
        value = None
    elif value is not None and isinstance(value, bool):
        if is_debug():
            _print(f"\n:information: [black on #00FFFF]Converting bool to string:[/] [white on blue]{value}[/]")
        value = str(value).lower()
    if is_debug():
        _print(f"\n:information: [black on #00FFFF]Formatted value:[/] [white on blue]{value}[/], type [white on blue]{type(value)}[/]")
    
    return value

def _get_mtime(file_path) -> Optional[float]:
    """Fetch file modification time without throwing exceptions."""
    try:
        return os.path.getmtime(file_path)
    except:
        raise SystemError("Faild to get mtime")
        # return None

def _update_file_snapshot(_config_file_path, Hash = None) -> Tuple:
    """Update internal mtime and hash snapshot to prevent self-triggered reloads."""
    try:
        _last_mtime = os.path.getmtime(_config_file_path)

        if not callable(Hash):
            # configset_hash
            try:
                from . configset_hash import Hash  # type: ignore
            except:
                try:
                    from configset_hash import Hash  # type: ignore
                except:
                    from configset.configset_hash import Hash  # type: ignore

        if callable(Hash):
            _last_file_hash = Hash._get_file_hash()  # type: ignore
        else:
            _last_file_hash = None
            try:
                import xwarning
                xwarning.warn("`Hash` undefinition !")
            except:
                import warnings
                warnings.warn("`Hash` undefinition !")
    except OSError:
        _last_mtime = None
        _last_file_hash = None

    return _last_mtime, _last_file_hash

