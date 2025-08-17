# #import imp
# try:
# 	from . import __version__ as version
# except:
# 	import __version__ as version
# __version__ 	= version.version
# __email__		= "licface@yahoo.com"
# __author__		= "licface@yahoo.com"

# from .configset import *

"""
ConfigSet - Enhanced Configuration Management Library

A powerful and flexible configuration management library that supports both INI and JSON formats
with automatic type conversion, list/dictionary parsing, and class-based interfaces.

Key Features:
- INI file configuration with automatic type conversion
- JSON configuration support for attribute-based access
- List and dictionary parsing from configuration values
- Class-based configuration interface with metaclass
- Command-line interface for configuration management
- Search functionality across sections and options
- Pretty printing with optional color support
- Python 2/3 compatibility

Example Usage:
    Basic INI Configuration:
        >>> from configset import ConfigSet
        >>> config = ConfigSet('myapp.ini')
        >>> config.write_config('database', 'host', 'localhost')
        >>> host = config.get_config('database', 'host')
        
    List and Dictionary Parsing:
        >>> servers = config.get_config_as_list('cluster', 'servers')
        >>> settings = config.get_config_as_dict('app', 'features')
        
    Class-based Interface:
        >>> from configset import CONFIG
        >>> class MyConfig(CONFIG):
        ...     CONFIGFILE = 'myapp.ini'
        >>> MyConfig.write_config('section', 'option', 'value')
        
    JSON-style Attribute Access:
        >>> config = MyConfig()
        >>> config.api_key = 'secret123'
        >>> print(config.api_key)

Author: licface@yahoo.com
Version: see __version__.py
Platform: all
License: MIT
"""
import sys
import os
import traceback
from pathlib import Path

from .configset import (
    ConfigSet,
    CONFIG, 
    MultiOrderedDict,
    ConfigMeta,
    create_argument_parser,
    main,
    _debug_enabled
)


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
__author__ = "licface@yahoo.com" 
__email__ = "licface@yahoo.com"
__license__ = "MIT"
__platform__ = "all"
__status__ = "Production"

__all__ = [
    # Main classes
    'ConfigSet',
    'CONFIG',
    'MultiOrderedDict',
    'ConfigMeta',
    
    # Utility functions
    'create_argument_parser',
    'main',
    '_debug_enabled',
    
    # Package metadata
    '__version__',
    '__author__',
    '__email__',
    '__license__',
    '__platform__',
    '__status__'
]

# Package-level convenience functions
def create_config(config_file: str = '', auto_write: bool = True) -> ConfigSet:
    """
    Create a new ConfigSet instance.
    
    Args:
        config_file: Path to configuration file
        auto_write: Whether to automatically create missing files/sections
        
    Returns:
        ConfigSet instance
    """
    return ConfigSet(config_file=config_file, auto_write=auto_write)


def load_config(config_file: str) -> ConfigSet:
    """
    Load an existing configuration file.
    
    Args:
        config_file: Path to existing configuration file
        
    Returns:
        ConfigSet instance
        
    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    return ConfigSet(config_file=config_file, auto_write=False)


# Module-level configuration for backward compatibility
_default_config = None

def get_default_config() -> ConfigSet:
    """Get or create the default module-level configuration instance."""
    global _default_config
    if _default_config is None:
        _default_config = ConfigSet()
    return _default_config


def set_default_config_file(config_file: str):
    """Set the default configuration file for module-level operations."""
    global _default_config
    _default_config = ConfigSet(config_file)


# Backward compatibility aliases
configset = ConfigSet  # For lowercase class name compatibility

# Export convenience functions
__all__.extend([
    'create_config',
    'load_config', 
    'get_default_config',
    'set_default_config_file',
    'configset'
])

# Package initialization
def _init_package():
    """Initialize package-level settings."""
    
    # Set debug mode if environment variable is set
    if _debug_enabled():
        print(f"ConfigSet v{__version__} - Debug mode enabled")
    
    # Check for optional dependencies and warn if missing
    try:
        import rich
    except ImportError:
        if _debug_enabled():
            print("Optional dependency 'rich' not found - enhanced output disabled")
    
    try:
        import jsoncolor
    except ImportError:
        if _debug_enabled():
            print("Optional dependency 'jsoncolor' not found - JSON coloring disabled")
    
    try:
        import make_colors
    except ImportError:
        if _debug_enabled():
            print("Optional dependency 'make_colors' not found - color output disabled")

# Run package initialization
_init_package()


# Version compatibility check
def check_python_version():
    """Check Python version compatibility and warn if needed."""
    
    if sys.version_info < (2, 7):
        import warnings
        warnings.warn(
            "ConfigSet requires Python 2.7 or higher. "
            "Some features may not work correctly on older versions.",
            UserWarning,
            stacklevel=2
        )
    elif sys.version_info < (3, 6):
        import warnings
        warnings.warn(
            "ConfigSet works best with Python 3.6+. "
            "Consider upgrading for better performance and features.",
            UserWarning,
            stacklevel=2
        )

# Perform version check on import
check_python_version()


# CLI entry point for package
def cli():
    """Entry point for command-line interface when installed as package."""
    
    if len(sys.argv) < 2:
        print("Usage: python -m configset <config_file> [options...]")
        print("Run 'python -m configset --help' for more information.")
        return
    
    main()


# Package metadata for setuptools
PACKAGE_INFO = {
    'name': 'configset',
    'version': __version__,
    'author': __author__,
    'author_email': __email__,
    'description': 'Enhanced Configuration Management Library',
    'long_description': __doc__,
    'license': __license__,
    'platform': __platform__,
    'status': __status__,
    'keywords': [
        'configuration', 'config', 'ini', 'json', 'settings',
        'configparser', 'management', 'file', 'parser'
    ],
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ],
    'python_requires': '>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*'
}

# Export package info for setup.py
__all__.append('PACKAGE_INFO')