"""
Enhanced Configuration Management Library
Provides easy-to-use configuration file handling with INI, JSON, and YAML support.
"""

from __future__ import annotations
import warnings
import sys
import argparse
import os
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
# from pydebugger.debug import debug
# Python 2/3 compatibility
if sys.version_info.major == 2:
    import ConfigParser
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
    from rich import traceback as rich_traceback
    _console = Console()
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

    rich_traceback.install(show_locals=False, width=os.get_terminal_size()[0], theme='fruity')

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
__contact__ = "licface@yahoo.com"
__all__ = ["ConfigSet", "CONFIG", "MultiOrderedDict", "__version__", "get_version", "ConfigSetIni", "ConfigSetYaml", "ConfigSetJson", "detect_file_type", "_validate_file_path", "ConfigMeta"]

def _debug_enabled() -> bool:
    """Check if debug mode is enabled via environment variables."""
    return (os.getenv('DEBUG', '').lower() in ['1', 'true', 'yes'] or
            os.getenv('DEBUG_SERVER', '').lower() in ['1', 'true', 'yes'])

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
    """Validate and sanitize file path."""
    try:
        path = Path(file_path).resolve()
        # Basic path traversal protection
        if '..' in str(path) or str(path).startswith('/'):
            raise ValueError("Potentially unsafe path detected")
        return path
    except (ValueError, OSError) as e:
        raise ConfigurationError(f"Invalid file path: {e}")
    
class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass

class MultiOrderedDict(OrderedDict):
    """OrderedDict that extends lists when duplicate keys are encountered."""
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set item, extending lists if key already exists."""
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super().__setitem__(key, value)

class ConfigSetJson(JSONDecoder, JSONEncoder):
    """Enhanced configuration file manager supporting JSON format."""
    
    def __init__(self, *, json_file: Any = None, config_file: Any = None, 
                 object_hook: Callable[[dict[str, Any]], Any] = None, 
                 parse_float: Callable[[str], Any] = None, 
                 parse_int: Callable[[str], Any] = None, 
                 parse_constant: Callable[[str], Any] = None, 
                 strict: bool = True, 
                 object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] = None) -> None:
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
        """Load JSON data from file."""
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
    
    def _load_config(self, json_file=None):
        """Load configuration from file with error handling."""
        source = json_file or self.json_file
        try:
            if os.path.isfile(source):
                with open(source, "r", encoding="utf-8") as f:
                    self.json = json.load(f)
            else:
                self.json = json.loads(source)
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
            raise ConfigurationError(f"Failed to load configuration: {e}")
        self.json = {}
        return self.json
    
    def loads(self, json_file=None):
        """Alias for _load_config."""
        return self._load_config(json_file)
    
    def read(self, json_file=None):
        return self._load_config(json_file)

    def _save_config(self, json_file=None) -> None:
        """Save current configuration to file."""
        # source = json_file or self.json_file
        # try:
        #     self._load_config(source)

        #     with open(self.json_file, "w", encoding="utf-8") as f:
        #         json.dump(self.json, f, indent=2)

        # except Exception as e:
        #     if _debug_enabled():
        #         _console.print(f":cross_mark: [white on red]Error saving JSON config:[/] [white on blue]{e}[/]")
        target = json_file or self.json_file
        if not target:
            raise ConfigurationError("No JSON file configured for saving")
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

                
    def dump(self, *args, **kwargs):
        """Dump JSON data to file."""
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(self.json, f, *args, **kwargs)
        return self.json

    def dumps(self, *args, **kwargs):
        """Save configuration (alias for _save_config)."""
        return self._save_config(*args, **kwargs)
    
    def show(self):
        """Display JSON configuration with colored output if available."""
        if HAS_JSONCOLOR:
            jprint(self.json)
        elif HAS_RICH:
            _console.print_json(data=self.json)
        elif HAS_MAKECOLOR:
            print(make_colors(self.json, 'lc'))
        else:
            print(json.dumps(self.json, indent=2))
            
    def print(self):
        """Alias for show method."""
        return self.show()
    
    @property
    def filename(self):
        """Get the filename of the JSON configuration file."""
        return str(self.json_file)
    
    @property
    def config_file(self):
        """Get the configuration name (alias for filename)."""
        return self.filename
    
    @property
    def configname(self):
        """Get the configuration name (alias for filename)."""
        return self.filename
    
    def set_config_file(self, config_file: str) -> bool:
        """Set a new configuration file path."""
        # if os.path.isfile(config_file):
        #     self.json_file = config_file 
        #     self._load_config()
        #     return True
        # else:
        #     _console.print("\n:cross_mark: [white on red]Invalid Json File ![/]")
        #     return False
        # allow setting a new file path (create if necessary)
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
    
    def get_config(self, key):
        """Get configuration value by key."""
        if isinstance(self.json, dict):
            return self.json.get(key, None)
        else:
            if HAS_RICH:
                _console.print(f"\n:cross_mark: [white on red]Invalid Json File ![/]")
            return None
    
    def get(self, key):
        """Alias for get_config."""
        return self.get_config(key)
    
    def read_config(self, key):
        """Alias for get_config."""
        return self.get_config(key)
    
    def write_config(self, key, value: str = '') -> bool:
        """Write configuration value to nested key."""
        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]

            if not keys:
                if _debug_enabled():
                    if HAS_RICH:
                        _console.print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    else:
                        _console.print("[bold #FFFF00]No key ![/]")
                return False

            d = self.json
            if len(keys) > 1:
                # Traverse self.json for nested keys
                for k in keys[:-1]:
                    if k not in d or not isinstance(d[k], dict):
                        d[k] = {}
                    d = d[k]
                d[keys[-1]] = value
            else:
                self.json[keys[0]] = value

            self._save_config()
            return True

        except Exception as e:
            if _debug_enabled():
                if HAS_RICH:
                    _console.print(f"\n:cross_mark: [white on red]Error writing config:[/] [white on blue]{e}[/]")
                else:
                    _console.print(f":cross_mark: [white on red]Error writing config:[/] [white on blue]{e}[/]")
            return False
        
    def set(self, key, value: str = ''):
        """Alias for write_config."""
        return self.write_config(key, value)
    
    def remove_value_anywhere(self, value):
        """Remove all occurrences of a value from the JSON structure."""
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
    
    def remove_config(self, key: str = '', value: str = '') -> bool:
        """Remove configuration key or value."""
        if value and not key:
            return self.remove_value_anywhere(value)
        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]
            if not keys:
                if _debug_enabled():
                    if HAS_RICH:
                        _console.print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    else:
                        _console.print(":warning: [bold #FFFF00]No key ![/]")
                return False

            d = self.json
            # Traverse to parent dict
            for k in keys[:-1]:
                if k in d and isinstance(d[k], dict):
                    d = d[k]
                else:
                    if _debug_enabled():
                        if HAS_RICH:
                            _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{k}[/]")
                        else:
                            _console.print(f":warning: [bold #FFFF00]Key not found:[/] [bold #00FFFF]{k}[/]")
                    return False

            last_key = keys[-1]
            if last_key not in d:
                if _debug_enabled():
                    if HAS_RICH:
                        _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{last_key}[/]")
                    else:
                        _console.print(f":warning: [bold #FFFF00]Key not found:[/] [bold #00FFFF]{last_key}[/]")
                return False

            if value is None:
                del d[last_key]
            else:
                # If dict value matches exactly → remove
                if d[last_key] == value:
                    del d[last_key]
                # Or if it's a list → remove item value
                elif isinstance(d[last_key], list) and value in d[last_key]:
                    d[last_key].remove(value)
                else:
                    # Value mismatch
                    return False

            self._save_config()
            return True
        except Exception as e:
            if _debug_enabled():
                _console.print(f"\n:cross_mark: [white on red]Error removing config:[/] [white on blue]{e}[/]")
            return False

    def remove_key(self, key: str) -> bool:
        """Remove key and its children (supports nested keys)."""
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
        """Alias for remove_key."""
        return self.remove_key(key)

    def find(self, key: str, value=None):
        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]
            # print(">>> KEYS =", keys)
            # print(">>> JSON ROOT KEYS =", list(self.json.keys())[:10], "...")  # tampilkan sebagian saja
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
            
            # print(">>> LAST KEY =", last_key)
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

class ConfigSetYaml:
    def __init__(self, yaml_file: str = '', config_file: str = '', **kwargs):
        self.yaml_file = yaml_file or config_file
        self.file = self.yaml_file
        self.kwargs = kwargs
        self.yaml = self._load_config()

    def load(self, yaml_file=None):
        """Load YAML data from file."""
        return self._load_config(yaml_file)
    
    def loads(self, yaml_file: str = ''):
        # if os.path.isfile(yaml_file):
        #     return self._load_config(yaml_file)
        # else:
        #     if isinstance(yaml_file, str):
        #         self.yaml = yaml.safe_load(yaml_file)
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
        return self.loads(yaml_file)

    def _load_config(self, yaml_file=None):
        """Load configuration from file with error handling."""
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
        """Save the current YAML configuration to the file."""
        # yaml_file = self.yaml_file
        # if yaml_file and self.yaml:
        #     with open(yaml_file, "w", encoding="utf-8") as f:
        #         yaml.safe_dump(yaml, f)
        # target = yaml_file or self.yaml_file
        # if not target or self.yaml is None:
        #     return
        # try:
        #     with open(target, "w", encoding="utf-8") as f:
        #         # write the YAML data (self.yaml), not the yaml module
        #         yaml.safe_dump(self.yaml, f)
        # except Exception as e:
        #     if _debug_enabled():
        #         _console.print(f":cross_mark: [white on red]Error saving YAML config:[/] [white on blue]{e}[/]")
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
        """Dump the current YAML configuration."""
        with open(self.yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.yaml, f, *args, **kwargs)
        return self.yaml

    def dumps(self, *args, **kwargs):
        """Dump the current YAML configuration to a string."""
        return yaml.safe_dump(self.yaml, *args, **kwargs)

    def show(self):
        """Show the current YAML configuration."""
        if HAS_JSONCOLOR:
            jprint(self.yaml)
        elif HAS_RICH:
            _console.print(self.yaml)
        elif HAS_MAKECOLOR:
            print(make_colors(self.yaml, 'lc'))
        else:
            print(yaml.safe_dump(self.yaml))

    def print(self):
        return self.show()
    
    @property
    def filename(self):
        """Get the filename of the YAML configuration file."""
        return str(self.yaml_file)
    
    @property
    def config_file(self):
        """Get the configuration name (alias for filename)."""
        return self.filename
    
    @property
    def configname(self):
        """Get the configuration name (alias for filename)."""
        return self.filename
    
    def set_config_file(self, config_file: str) -> bool:
        """Set a new configuration file path."""
        if os.path.isfile(config_file):
            self.yaml_file = config_file  # Fix: was self.json_file
            self._load_config()
            return True
        else:
            _console.print("\n:cross_mark: [white on red]Invalid YAML File ![/]")  # Fix: was Json File
            return False
    
    def get_config(self, key):
        """Get configuration value by key."""
        if _debug_enabled():
            _console.print(f"\n:question: [bold #FFFF00]Getting config for key:[/] [bold cyan]{key}[/]")
            _console.print(f"\n:gear: [white on blue]Current YAML data type:[/] [white on blue]{type(self.yaml)}[/]")
        if not isinstance(self.yaml, dict):  # Fix: was self.json
            self._load_config()
        if isinstance(self.yaml, dict):  # Second try
            return self.yaml.get(key, None)  # Fix: was self.json
        else:
            _console.print(f"\n:cross_mark: [white on red]Invalid YAML File ![/]")  # Fix: was Json File
            return None

    def get(self, key):
        """Get configuration value by key."""
        return self.get_config(key)
    
    def read_config(self, key):
        """Read configuration value by key."""
        return self.get_config(key)
    
    def write_config(self, key, value: str = '') -> bool:
        """Write configuration value to nested key."""
        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]

            if not keys:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
                return False

            d = self.yaml
            if len(keys) > 1:
                # Traverse self.yaml for nested keys
                for k in keys[:-1]:
                    if k not in d or not isinstance(d[k], dict):
                        d[k] = {}
                    d = d[k]
                d[keys[-1]] = value
            else:
                self.yaml[keys[0]] = value

            self._save_config()
            return True

        except Exception as e:
            if _debug_enabled():
                _console.print(f"\n:cross_mark: [white on red]Error writing config:[/] [white on blue]{e}[/]")
            return False
        
    def set(self, key, value: str = ''):
        """Set configuration value by key."""
        return self.write_config(key, value)
    
    def remove_value_anywhere(self, value):
        """Remove all occurrences of a value from the YAML structure."""
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
    
    def remove_config(self, key: str = '', value: str = '') -> bool:
        """Remove configuration key or value."""
        if value and not key:
            return self.remove_value_anywhere(value)
        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]
            if not keys:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                return False

            d = self.yaml  # Fix: was self.json
            # Traverse to parent dict
            for k in keys[:-1]:
                if k in d and isinstance(d[k], dict):
                    d = d[k]
                else:
                    if _debug_enabled():
                        _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{k}[/]")
                    return False

            last_key = keys[-1]
            if last_key not in d:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{last_key}[/]")
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
            if _debug_enabled():
                _console.print(f"\n:cross_mark: [white on red]Error removing config:[/] [white on blue]{e}[/]")
            return False

    def remove_key(self, key: str) -> bool:
        """Remove key and its children (supports nested keys)."""
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
        """Alias for remove_key."""
        return self.remove_key(key)
    
    def find(self, key: str, value=None):
        """Find all keys that have the specified value."""
        try:
            keys = re.split(r"[:;|]", key)
            keys = [i.strip() for i in keys if i.strip()]
            # print(">>> KEYS =", keys)
            # print(">>> JSON ROOT KEYS =", list(self.yaml.keys())[:10], "...")  # tampilkan sebagian saja
            if not keys:
                if _debug_enabled():
                    _console.print(f"\n:cross_mark: [bold #FFFF00]No key ![/]")
                    
                return {}

            d = self.yaml
            for k in keys[:-1]:
                # print(">>> Traverse check:", k, "in", type(d))
                if isinstance(d, dict) and k in d:
                    d = d[k]
                else:
                    if _debug_enabled():
                        _console.print(f"\n:cross_mark: [white on red]Key not found:[/] [white on blue]{k}[/]")
                    return {}

            last_key = keys[-1]
            
            # print(">>> LAST KEY =", last_key)
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
        """Get absolute path of config file."""
        return str(self._config_file_path)
    
    @property
    def config_file(self) -> str:
        """Get absolute path of config file."""
        return str(self._config_file_path)
    @property
    def configname(self) -> str:
        """Get absolute path of config file."""
        return str(self._config_file_path)

    def set_config_file(self, config_file: str) -> None:
        """Change the configuration file and reload."""
        if config_file and Path(config_file).exists():
            self._config_file_path = Path(config_file).resolve()  # Fix: use _config_file_path
            self._load_config()
        else:
            _console.print(f":warning: [#FFFF00]Config file not found:[/] [#00FFFF]{config_file}[/]")
            raise FileNotFoundError(f"Config file not found: {config_file}")

    def _load_config(self) -> None:
        """Load configuration from file with specific error handling."""
        # try:
        #     self.read(str(self._config_file_path), encoding='utf-8')  # Fix: use _config_file_path
        # except Exception as e:
        #     if _debug_enabled():
        #         _console.print(f":cross_mark: [white on red]Error loading config:[/] [white on blue]{e}[/]")   
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
        """Print all configuration in a formatted way."""
        _console.print(f":japanese_symbol_for_beginner: [bold #FFFF00]CONFIG FILE:[/] [bold #00FFFF]{self._config_file_path}[/]")  # Fix: use _config_file_path
        
        data = []

        if not str(self._config_file_path).endswith(".json"):  # Fix: use _config_file_path
            _console.print(f":japanese_symbol_for_beginner: [bold #FFFF00]CONFIG INI:[/]")
            data = self.get_all_config(sections)
            
            for section_name, section_data in data:
                self._print_colored(f"[{section_name}]", 'section')
                for option, value in section_data.items():
                    self._print_colored(f"  {option} = {value}", 'option', value)
            
            print()
        
        elif str(self._config_file_path).endswith(".json"):  # Fix: use _config_file_path
            _console.print(f":llama: [bold #00FFFF]CONFIG JSON:[/] [#bold #FFFF00]{self._config_file_path}[/]")
            with open(self._config_file_path, 'r') as json_file:  # Fix: use _config_file_path
                try:
                    data = json.loads(json_file.read())
                    if HAS_JSONCOLOR:
                        jprint(data)
                    elif HAS_RICH:
                        print_json(data=data)
                except Exception as e:
                    if HAS_RICH:
                        _console.print_exception(word_wrap=True, theme='fruity', show_locals=False, width=os.get_terminal_size()[0])
                    else:
                        print(traceback.format_exc())
                
        return data

    def get_config(self, section: str, option: str, 
                  default: Any = None, auto_write: bool = False) -> Any:
        """
        Get configuration value with automatic type conversion.
        
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
        return self.get_config(*args, **kwargs)
    
    def write_config(self, section: str, option: str, value: Any = '') -> Any:
        """
        Write configuration value to file.
        
        Args:
            section: Configuration section name
            option: Configuration option name
            value: Value to write
            
        Returns:
            The written value
        """
        if not self.has_section(section):
            self.add_section(section)
            
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
        return self.remove_config(section)
    
    def get_config_as_list(self, section: str, option: str, 
                          default: Union[str, List] = None) -> List[Any]:
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
                          default: Dict = None) -> Dict[str, Any]:
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
        
        return len(found) > 0
    
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
        """Convert string value to appropriate Python type."""
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
        file_type = detect_file_type(file_path)
        if file_type == 'json':
            return ConfigSetJSON(json_file=file_path, **kwargs)
        if file_type in ('yaml', 'yml'):
            return ConfigSetYAML(yaml_file=file_path, **kwargs)
        return ConfigSetINI(config_file=file_path, auto_write=auto_write, config_dir=config_dir, config_name=config_name, **kwargs)

class configset(ConfigSet):
    pass

# class ConfigMeta1(type):
#     """Metaclass for creating class-based configuration interfaces."""
    
#     def __new__(mcs, name, bases, attrs):
#         # Initialize config instance
#         config_file = attrs.get('CONFIGFILE') or attrs.get('configname')
        
#         if 'config' in attrs and hasattr(attrs['config'], 'set_config_file'):
#             config_instance = attrs['config']
#             if config_file:
#                 config_instance.set_config_file(config_file)
#         else:
#             config_instance = ConfigSet(config_file)
        
#         attrs['_config_instance'] = config_instance
        
#         # Wrap methods to work as classmethods
#         def make_classmethod(method):
#             @wraps(method)
#             def wrapper(cls, *args, **kwargs):
#                 return method(cls._config_instance, *args, **kwargs)
#             return classmethod(wrapper)
        
#         # Convert ConfigSet methods to classmethods
#         for base in bases:
#             for attr_name, attr_value in base.__dict__.items():
#                 if (callable(attr_value) and 
#                     not attr_name.startswith('__') and 
#                     attr_name not in attrs):
#                     attrs[attr_name] = make_classmethod(attr_value)
        
#         return super().__new__(mcs, name, bases, attrs)
    
#     def __getattr__(cls, name):
#         """Delegate attribute access to config instance."""
#         if hasattr(cls._config_instance, name):
#             attr = getattr(cls._config_instance, name)
#             if callable(attr):
#                 return lambda *args, **kwargs: attr(*args, **kwargs)
#             return attr
        
#         if hasattr(cls, 'data') and name in cls.data:
#             return cls.data[name]
            
#         raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")
    
#     def __setattr__(cls, name, value):
#         """Handle attribute assignment."""
#         if name in ['configname', 'CONFIGNAME', 'CONFIGFILE']:
#             cls._config_instance.set_config_file(value)
#         else:
#             if os.getenv('DEBUG') in ['1', 'true', 'True']: print("Saving ....")
#             super().__setattr__(name, value)

#     def show(cls):
#         """Show current configuration."""
        
#         if hasattr(cls, '_config_instance'):
#             return cls._config_instance.print_all_config()
#         else:
#             _console.print(":cross_mark: [white on red]No config instance found.[/]")
#             return None

# ...existing code...
class ConfigMeta(type):
    """Metaclass for creating class-based configuration interfaces."""
    
    def __new__(mcs, name, bases, attrs):
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
        def make_classmethod_from_instance(method_name):
            def wrapper(cls, *args, **kwargs):
                inst = getattr(cls, '_config_instance')
                method = getattr(inst, method_name)
                return method(*args, **kwargs)
            wrapper.__name__ = method_name
            return classmethod(wrapper)

        # expose public callable attributes of the instance as classmethods
        for name in dir(config_instance):
            if name.startswith('_'):
                continue
            if name in attrs:
                continue
            try:
                attr = getattr(config_instance, name)
            except Exception:
                continue
            if callable(attr):
                attrs[name] = make_classmethod_from_instance(name)

        return super().__new__(mcs, name, bases, attrs)

    def __getattr__(cls, name):
        """Delegate attribute access to config instance (methods/properties)."""
        if hasattr(cls, '_config_instance') and hasattr(cls._config_instance, name):
            attr = getattr(cls._config_instance, name)
            if callable(attr):
                # return a wrapper that calls the instance method
                return lambda *args, **kwargs: attr(*args, **kwargs)
            return attr

        if hasattr(cls, 'data') and name in cls.data:
            return cls.data[name]
            
        raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")

    # def __setattr__(cls, name, value):
    #     """Handle attribute assignment."""
    #     if name in ['configname', 'CONFIGNAME', 'CONFIGFILE']:
    #         # delegate change of file to instance so backend can reload
    #         if hasattr(cls, '_config_instance') and hasattr(cls._config_instance, 'set_config_file'):
    #             cls._config_instance.set_config_file(value)
    #         else:
    #             super().__setattr__(name, value)
    #     else:
    #         if os.getenv('DEBUG') in ['1', 'true', 'True']:
    #             print("Saving ....")
    #         super().__setattr__(name, value)
    
    # ...existing code...
    def __setattr__(cls, name, value):
        """Handle attribute assignment."""
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

    def show(cls):
        """Show current configuration."""
        if hasattr(cls, '_config_instance'):
            # prefer unified method names if available
            inst = cls._config_instance
            if hasattr(inst, 'print_all_config'):
                return inst.print_all_config()
            if hasattr(inst, 'show'):
                return inst.show()
            if hasattr(inst, 'print'):
                return inst.print()
        else:
            _console.print(":cross_mark: [white on red]No config instance found.[/]")
            return None
        
class CONFIG(metaclass=ConfigMeta):
    """
    Class-based configuration interface providing INI, JSON, and YAML support.
    
    Usage:
        # Class-level access for INI files
        CONFIG.write_config('section', 'option', 'value')
        value = CONFIG.get_config('section', 'option')
        
        # Instance-level access for JSON-like interface
        config = CONFIG()
        config.my_setting = 'value'
        print(config.my_setting)
    """
    
    CONFIGFILE: Optional[str] = None
    INDENT: int = 4
    
    config = ConfigSet()
    data: Dict[str, Any] = {}
    
    def __init__(self, config_file: str = None):
        """Initialize CONFIG instance with optional JSON file support."""
        if config_file:
            self.config = ConfigSet(config_file)
        
        # Setup JSON file for attribute-based access
        if self.CONFIGFILE:
            json_file = Path(self.CONFIGFILE).with_suffix('.json')
            self._json_file = json_file
            
            # Load existing JSON data
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        self.data = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    if _debug_enabled():
                        _console.print(f":cross_mark: [white on red]Error loading JSON config:[/] [white on blue]{e}[/]")
                    self.data = {}
            else:
                # Create empty JSON file
                self._save_json()
    
    def _save_json(self) -> None:
        """Save current data to JSON file."""
        if hasattr(self, '_json_file'):
            try:
                with open(self._json_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=self.INDENT, ensure_ascii=False)
            except IOError as e:
                if _debug_enabled():
                    _console.print(f":cross_mark: [white on red]Error saving JSON config:[/] [white on blue]{e}[/]")

    def __getattr__(self, name: str) -> Any:
        """Get attribute from JSON data."""
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
        """Set attribute in JSON data."""
        if name.startswith('_') or name in ['data', 'config', 'CONFIGFILE', 'INDENT']:
            super().__setattr__(name, value)
        else:
            self.data[name] = value
            if hasattr(self, '_json_file'):
                self._save_json()
            else:
                warnings.warn("This only supports JSON configuration file!", Warning)

def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser for the configuration tool."""
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
                config.print_all_config()
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
                    value = config.get_config_as_list(args.section, key)
                elif args.dict:
                    value = config.get_config_as_dict(args.section, key)
                else:
                    value = config.get_config(args.section, key)
                
                print(f"[{args.section}] {key} = {value}")
                
            elif hasattr(config, 'get_config') and not args.section:
                # JSON or YAML file with key only
                if not key:
                    _console.print(":cross_mark: [white on red]Error:[/] [white on blue]Key required for read operation[/]")
                    return
                    
                value = config.get_config(key)
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
