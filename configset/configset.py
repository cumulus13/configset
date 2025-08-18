"""
Enhanced Configuration Management Library
Provides easy-to-use configuration file handling with INI and JSON support.
"""

from __future__ import annotations
import sys
import argparse
import os
import traceback
import re
import json
import ast
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from functools import wraps

# Python 2/3 compatibility
if sys.version_info.major == 2:
    import ConfigParser
    configparser = ConfigParser
else:
    import configparser

# Optional dependencies for enhanced output
try:
    from rich import print_json
    from rich.console import Console
    from rich import traceback as rich_traceback
    _console = Console()
    HAS_RICH = True
except ImportError:
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

    rich_traceback.install(show_locals = False, width=os.get_terminal_size()[0], theme = 'fruity')


def get_version():
    """
    Get the version.
    Version is taken from the __version__.py file if it exists.
    The content of __version__.py should be:
    version = "0.33"
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
            print(traceback.format_exc())
        else:
            print(f"ERROR: {e}")

    return "0.0.0"

__version__ = get_version()
__platform__ = "all"
__contact__ = "licface@yahoo.com"
__all__ = ["ConfigSet", "CONFIG", "MultiOrderedDict"]


def _debug_enabled() -> bool:
    """Check if debug mode is enabled via environment variables."""
    return (os.getenv('DEBUG', '').lower() in ['1', 'true', 'yes'] or
            os.getenv('DEBUG_SERVER', '').lower() in ['1', 'true', 'yes'])


class MultiOrderedDict(OrderedDict):
    """OrderedDict that extends lists when duplicate keys are encountered."""
    
    def __setitem__(self, key: str, value: Any) -> None:
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super().__setitem__(key, value)


class ConfigSet(configparser.RawConfigParser):
    """
    Enhanced configuration file manager supporting INI format with automatic
    file creation, type conversion, and various data parsing methods.
    """
    
    def __init__(self, config_file: str = '', auto_write: bool = True, config_dir: str = '', config_name: str = '', **kwargs):
        """
        Initialize ConfigSet instance.
        
        Args:
            config_file: Path to configuration file
            auto_write: Whether to automatically create missing files/sections
            **kwargs: Additional arguments passed to RawConfigParser
        """
        super().__init__(**kwargs)
        
        self.allow_no_value = True
        self.optionxform = str  # Preserve case sensitivity
        
        # Determine config file path
        if not config_file:
            # Default to script name with .ini extension
            script_path = sys.argv[0] if sys.argv else 'config'
            config_file = os.path.splitext(os.path.realpath(script_path))[0] + ".ini"
        
        # Ensure .ini extension
        if not config_file.endswith('.ini'):
            config_file += '.ini'
            
        self.config_file = Path(config_file).resolve()
        self.config_name = Path(config_name).resolve() if config_name else self.config_file
        self._auto_write = auto_write
        
        # Create file if it doesn't exist and auto_write is enabled
        if not self.config_file.exists() and auto_write:
            self.config_file.touch()
        
        if config_dir:
            # Ensure config directory exists
            config_dir_path = Path(config_dir).resolve()
            if not config_dir_path.exists():
                config_dir_path.mkdir(parents=True, exist_ok=True)
            self.config_file = config_dir_path / self.config_name.name  
                
        # Load existing configuration
        if self.config_file.exists():
            self._load_config()
            if os.getenv('SHOW_CONFIGNAME'):
                print(f"CONFIG FILE: {self.config_file}")
        
    def _load_config(self) -> None:
        """Load configuration from file with error handling."""
        try:
            self.read(str(self.config_file), encoding='utf-8')
        except Exception as e:
            if _debug_enabled():
                print(f"Error loading config: {e}")
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.write(f)
        except Exception as e:
            if _debug_enabled():
                print(f"Error saving config: {e}")
    
    @property
    def filename(self) -> str:
        """Get absolute path of config file."""
        return str(self.config_file)
    
    def set_config_file(self, config_file: str) -> None:
        """Change the configuration file and reload."""
        if config_file and Path(config_file).exists():
            self.config_file = Path(config_file).resolve()
            self._load_config()
        else:
            raise FileNotFoundError(f"Config file not found: {config_file}")
    
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
    
    def remove_config(self, section: str, option: str = None) -> bool:
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
        try:
            if option is None:
                # Remove entire section
                if self.has_section(section):
                    self.remove_section(section)
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
                        self.remove_option(section, option)
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
    
    def get_all_config(self, sections: List[str] = None) -> List[Tuple[str, Dict]]:
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
    
    def print_all_config(self, sections: List[str] = None) -> List[Tuple[str, Dict]]:
        """Print all configuration in a formatted way."""
        print(f"CONFIG FILE: {self.config_file}")
        
        data = self.get_all_config(sections)
        
        for section_name, section_data in data:
            self._print_colored(f"[{section_name}]", 'section')
            for option, value in section_data.items():
                self._print_colored(f"  {option} = {value}", 'option', value)
        
        print()  # Empty line at the end
        
        # Pretty print JSON if available
        if HAS_RICH:
            print_json(data=data)
        elif HAS_JSONCOLOR:
            jprint(data)
        
        return data
    
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
    
    def _print_colored(self, text: str, element_type: str, value: str = None) -> None:
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

class configset(ConfigSet):
    pass

class ConfigMeta(type):
    """Metaclass for creating class-based configuration interfaces."""
    
    def __new__(mcs, name, bases, attrs):
        # Initialize config instance
        config_file = attrs.get('CONFIGFILE') or attrs.get('configname')
        
        if 'config' in attrs and hasattr(attrs['config'], 'set_config_file'):
            config_instance = attrs['config']
            if config_file:
                config_instance.set_config_file(config_file)
        else:
            config_instance = ConfigSet(config_file)
        
        attrs['_config_instance'] = config_instance
        
        # Wrap methods to work as classmethods
        def make_classmethod(method):
            @wraps(method)
            def wrapper(cls, *args, **kwargs):
                return method(cls._config_instance, *args, **kwargs)
            return classmethod(wrapper)
        
        # Convert ConfigSet methods to classmethods
        for base in bases:
            for attr_name, attr_value in base.__dict__.items():
                if (callable(attr_value) and 
                    not attr_name.startswith('__') and 
                    attr_name not in attrs):
                    attrs[attr_name] = make_classmethod(attr_value)
        
        return super().__new__(mcs, name, bases, attrs)
    
    def __getattr__(cls, name):
        """Delegate attribute access to config instance."""
        if hasattr(cls._config_instance, name):
            attr = getattr(cls._config_instance, name)
            if callable(attr):
                return lambda *args, **kwargs: attr(*args, **kwargs)
            return attr
        
        if hasattr(cls, 'data') and name in cls.data:
            return cls.data[name]
            
        raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")
    
    def __setattr__(cls, name, value):
        """Handle attribute assignment."""
        if name in ['configname', 'CONFIGNAME', 'CONFIGFILE']:
            cls._config_instance.set_config_file(value)
        else:
            super().__setattr__(name, value)


class CONFIG(metaclass=ConfigMeta):
    """
    Class-based configuration interface providing both INI and JSON support.
    
    Usage:
        # Class-level access
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
                        print(f"Error loading JSON config: {e}")
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
                    print(f"Error saving JSON config: {e}")
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute from JSON data."""
        if name in self.data:
            return self.data[name]
        elif hasattr(self, '_json_file') and name not in self.data:
            # Auto-create empty value
            self.data[name] = ''
            self._save_json()
            return ''
        
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute in JSON data."""
        if name.startswith('_') or name in ['data', 'config', 'CONFIGFILE', 'INDENT']:
            super().__setattr__(name, value)
        else:
            self.data[name] = value
            if hasattr(self, '_json_file'):
                self._save_json()


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser for the configuration tool."""
    parser = argparse.ArgumentParser(
        description="Configuration file management tool",
        formatter_class=CustomRichHelpFormatter,
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
                       help='Configuration section name')
    parser.add_argument('-o', '--option',
                       help='Configuration option name')
    parser.add_argument('-v', '--value',
                       help='Value to write (for write operations)')
    parser.add_argument('--list',
                       action='store_true',
                       help='Parse value as list')
    parser.add_argument('--dict',
                       action='store_true', 
                       help='Parse value as dictionary')
    parser.add_argument('--all',
                       action='store_true',
                       help='Show all configuration')
    
    return parser


def main():
    """Main CLI interface function."""
    parser = create_argument_parser()
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    if not args.config_file:
        print("Error: Configuration file is required")
        parser.print_help()
        return
    
    try:
        config = ConfigSet(args.config_file)
        
        if args.all:
            config.print_all_config()
        elif args.read:
            if not (args.section and args.option):
                print("Error: Section and option required for read operation")
                return
            
            if args.list:
                value = config.get_config_as_list(args.section, args.option)
            elif args.dict:
                value = config.get_config_as_dict(args.section, args.option)
            else:
                value = config.get_config(args.section, args.option)
            
            print(f"[{args.section}] {args.option} = {value}")
            
        elif args.write:
            if not (args.section and args.option):
                print("Error: Section and option required for write operation")
                return
            
            value = args.value or ''
            result = config.write_config(args.section, args.option, value)
            print(f"Written: [{args.section}] {args.option} = {result}")
            
        elif args.delete:
            if not args.section:
                print("Error: Section required for delete operation")
                return
            
            if args.option:
                # Remove specific option
                success = config.remove_config(args.section, args.option)
                if success:
                    print(f"Removed: [{args.section}] {args.option}")
                else:
                    print(f"Not found: [{args.section}] {args.option}")
            else:
                # Remove entire section
                success = config.remove_config(args.section)
                if success:
                    print(f"Removed section: [{args.section}]")
                else:
                    print(f"Section not found: [{args.section}]")
            
        else:
            print("Error: Specify --read, --write, --delete, or --all")
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {e}")
        if _debug_enabled():
            traceback.print_exc()


if __name__ == '__main__':
    main()