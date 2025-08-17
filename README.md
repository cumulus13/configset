# 📋 ConfigSet - Enhanced Configuration Management Library

[![Python Version](https://img.shields.io/badge/python-2.7%2B%20%7C%203.6%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)](https://github.com)

> 🚀 **A powerful and flexible configuration management library that supports both INI and JSON formats with automatic type conversion, list/dictionary parsing, and class-based interfaces.**

---

## 📖 Table of Contents

- [✨ Features](#-features)
- [📦 Installation](#-installation)
- [🚀 Quick Start](#-quick-start)
- [📚 Documentation](#-documentation)
- [🎯 Usage Examples](#-usage-examples)
- [🖥️ Command Line Interface](#️-command-line-interface)
- [🏗️ Advanced Usage](#️-advanced-usage)
- [🔧 Configuration](#-configuration)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

| Feature | Description | Icon |
|---------|-------------|------|
| **INI Support** | Full INI file configuration management | 📄 |
| **JSON Support** | JSON configuration with attribute-based access | 🗂️ |
| **Auto Type Conversion** | Automatic string to bool/int/float conversion | 🔄 |
| **List Parsing** | Parse comma-separated, newline-separated, and JSON arrays | 📝 |
| **Dictionary Parsing** | Parse key:value pairs and JSON objects | 🗝️ |
| **Class-based Interface** | Metaclass-powered configuration classes | 🏛️ |
| **CLI Interface** | Command-line tool for configuration management | 💻 |
| **Search Functionality** | Find sections and options with case sensitivity control | 🔍 |
| **Pretty Printing** | Enhanced output with optional color support | 🎨 |
| **Python 2/3 Compatible** | Works with both Python 2.7+ and Python 3.6+ | 🐍 |

---

## 📦 Installation

### 📋 Basic Installation
```bash
# Install from PyPI
pip install configset

# Or clone the repository
git clone https://github.com/cumulus13/configset.git
cd configset

# Install the package in editable/development mode
pip install -e .

# Or install the latest development version directly from GitHub
pip install git+https://github.com/cumulus13/configset.git
```


### 🎨 With Optional Dependencies (Recommended)

```bash
# Install with enhanced output support
pip install -e .[full]

# Or install dependencies manually
pip install rich jsoncolor make-colors
```

### 📋 Requirements

- **Python 2.7+ or Python 3.6+**
- **Optional**: `rich`, `jsoncolor`, `make-colors` for enhanced output

---

## 🚀 Quick Start

### 📄 Basic INI Configuration

```python
from configset import ConfigSet
# or from configset import configset
# Create configuration instance
config = ConfigSet('myapp.ini')
# or config = configset('myapp.ini')

# Write configuration
config.write_config('database', 'host', 'localhost')
config.write_config('database', 'port', 5432)
config.write_config('database', 'ssl', True)

# Read configuration (with automatic type conversion)
host = config.get_config('database', 'host')        # Returns: 'localhost'
port = config.get_config('database', 'port')        # Returns: 5432 (int)
ssl = config.get_config('database', 'ssl')          # Returns: True (bool)
```

### 🏛️ Class-based Configuration

```python
from configset import CONFIG

class AppConfig(CONFIG):
    CONFIGFILE = 'myapp.ini'

# Use as class methods
AppConfig.write_config('api', 'endpoint', 'https://api.example.com')
endpoint = AppConfig.get_config('api', 'endpoint')

# JSON-style attribute access
config = AppConfig()
config.api_key = 'secret123'
config.debug_mode = True
print(f"API Key: {config.api_key}")  # Output: API Key: secret123
```

---

## 📚 Documentation

### 🔧 ConfigSet Class

The main class for INI file configuration management.

#### 📝 Constructor

```python
ConfigSet(config_file='', auto_write=True, **kwargs)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config_file` | `str` | `''` | Path to configuration file |
| `auto_write` | `bool` | `True` | Auto-create missing files/sections |
| `**kwargs` | `dict` | `{}` | Additional ConfigParser arguments |

#### 🔑 Key Methods

| Method | Description | Return Type |
|--------|-------------|-------------|
| `get_config(section, option, default=None)` | Get config value with type conversion | `Any` |
| `write_config(section, option, value)` | Write config value to file | `Any` |
| `remove_config(section, option=None)` | Remove section or specific option | `bool` |
| `get_config_as_list(section, option, default=None)` | Parse value as list | `List[Any]` |
| `get_config_as_dict(section, option, default=None)` | Parse value as dictionary | `Dict[str, Any]` |
| `find(query, case_sensitive=True, verbose=False)` | Search sections/options | `bool` |
| `print_all_config(sections=None)` | Print all configuration | `List[Tuple]` |

---

## 🎯 Usage Examples

### 📋 List Configuration

```python
config = ConfigSet('servers.ini')

# Write list data (multiple formats supported)
config.write_config('cluster', 'servers', 'server1.com, server2.com, server3.com')
config.write_config('cluster', 'ports', '[8080, 8081, 8082]')
config.write_config('cluster', 'features', '''
    load_balancer
    ssl_support
    monitoring
''')

# Read as lists (automatic parsing)
servers = config.get_config_as_list('cluster', 'servers')
# Returns: ['server1.com', 'server2.com', 'server3.com']

ports = config.get_config_as_list('cluster', 'ports')
# Returns: [8080, 8081, 8082]

features = config.get_config_as_list('cluster', 'features')
# Returns: ['load_balancer', 'ssl_support', 'monitoring']
```

### 🗝️ Dictionary Configuration

```python
config = ConfigSet('settings.ini')

# Write dictionary data
config.write_config('limits', 'quotas', 'users:1000, files:5000, bandwidth:100')
config.write_config('features', 'enabled', '{"auth": true, "cache": false, "debug": true}')

# Read as dictionaries
quotas = config.get_config_as_dict('limits', 'quotas')
# Returns: {'users': 1000, 'files': 5000, 'bandwidth': 100}

features = config.get_config_as_dict('features', 'enabled')
# Returns: {'auth': True, 'cache': False, 'debug': True}
```

### 🔍 Search and Remove

```python
config = ConfigSet('myapp.ini')

# Search for sections/options
found = config.find('database')  # Returns: True if found
config.find('host', verbose=True)  # Print found items

# Remove operations
config.remove_config('old_section')              # Remove entire section
config.remove_config('database', 'old_option')   # Remove specific option
```

---

## 🖥️ Command Line Interface

The ConfigSet library includes a powerful CLI for configuration management.

### 📋 Basic Commands

```bash
# Show help
python -m configset --help

# Read all configuration
python -m configset myapp.ini --all

# Read specific value
python -m configset myapp.ini --read --section database --option host

# Write configuration
python -m configset myapp.ini --write --section database --option host --value localhost

# Remove section
python -m configset myapp.ini --delete --section old_section

# Remove specific option
python -m configset myapp.ini --delete --section database --option password
```

### 🎛️ Advanced CLI Usage

```bash
# Parse as list
python -m configset myapp.ini --read --section cluster --option servers --list

# Parse as dictionary
python -m configset myapp.ini --read --section limits --option quotas --dict

# Enable debug mode
DEBUG=1 python -m configset myapp.ini --all
```

---

## 🏗️ Advanced Usage

### 🎨 Custom Configuration Classes

```python
from configset import CONFIG, ConfigSet

class DatabaseConfig(CONFIG):
    CONFIGFILE = 'database.ini'
    
    @classmethod
    def get_connection_string(cls):
        host = cls.get_config('database', 'host')
        port = cls.get_config('database', 'port')
        db = cls.get_config('database', 'name')
        return f"postgresql://{host}:{port}/{db}"

class APIConfig(CONFIG):
    CONFIGFILE = 'api.ini'
    
    def __init__(self):
        super().__init__()
        # Set default values
        if not hasattr(self, 'timeout'):
            self.timeout = 30
        if not hasattr(self, 'retries'):
            self.retries = 3

# Usage
db_config = DatabaseConfig()
connection = db_config.get_connection_string()

api_config = APIConfig()
api_config.endpoint = 'https://api.example.com'
print(f"Timeout: {api_config.timeout}")  # Output: Timeout: 30
```

### 🔄 Configuration Migration

```python
def migrate_config_v1_to_v2(old_config_file, new_config_file):
    """Migrate configuration from v1 to v2 format."""
    old_config = ConfigSet(old_config_file)
    new_config = ConfigSet(new_config_file)
    
    # Copy all sections and options
    for section_name, section_data in old_config.get_all_config():
        for option, value in section_data.items():
            # Apply any transformations needed
            if section_name == 'database' and option == 'ssl':
                value = 'enabled' if value else 'disabled'
            
            new_config.write_config(section_name, option, value)
    
    print(f"✅ Migration completed: {old_config_file} → {new_config_file}")

# Usage
migrate_config_v1_to_v2('old_app.ini', 'new_app.ini')
```

### 🧪 Configuration Validation

```python
from configset import ConfigSet

class ValidatedConfig(ConfigSet):
    """Configuration with validation rules."""
    
    REQUIRED_SECTIONS = ['database', 'api', 'logging']
    REQUIRED_OPTIONS = {
        'database': ['host', 'port', 'name'],
        'api': ['endpoint', 'key'],
        'logging': ['level', 'file']
    }
    
    def validate(self):
        """Validate configuration against rules."""
        errors = []
        
        # Check required sections
        for section in self.REQUIRED_SECTIONS:
            if not self.has_section(section):
                errors.append(f"❌ Missing required section: [{section}]")
                continue
            
            # Check required options
            required_opts = self.REQUIRED_OPTIONS.get(section, [])
            for option in required_opts:
                if not self.has_option(section, option):
                    errors.append(f"❌ Missing required option: [{section}] {option}")
        
        if errors:
            print("\n".join(errors))
            return False
        
        print("✅ Configuration validation passed!")
        return True

# Usage
config = ValidatedConfig('validated_app.ini')
if config.validate():
    # Proceed with application
    pass
```

---

## 🔧 Configuration

### 🌍 Environment Variables

| Variable | Description | Values |
|----------|-------------|--------|
| `DEBUG` | Enable debug output | `1`, `true`, `yes` |
| `DEBUG_SERVER` | Enable server debug mode | `1`, `true`, `yes` |
| `SHOW_CONFIGNAME` | Show config file path | `1`, `true`, `yes` |

### 🎨 Optional Dependencies

```bash
# Enhanced output with colors and formatting
pip install rich           # Rich text and tables
pip install jsoncolor      # JSON syntax highlighting  
pip install make-colors    # Terminal color support
```

---

## 🔄 Migration Guide

### 📈 From v1.x to v2.x

**Breaking Changes:**
- Removed redundant methods (`read_config2`, `read_config3`, etc.)
- Simplified method signatures
- Enhanced type conversion

**Migration Steps:**
```python
# Old v1.x code
config.read_config2('section', 'option')

# New v2.x code  
config.get_config_as_list('section', 'option')
```

### 🔧 Configuration File Format

**INI Format Example:**
```ini
[database]
host = localhost
port = 5432
ssl = true
features = load_balancer, ssl_support, monitoring

[api]
endpoint = https://api.example.com
timeout = 30
headers = {"Content-Type": "application/json", "Accept": "application/json"}
```

**JSON Format Example:**
```json
{
    "database_host": "localhost",
    "database_port": 5432,
    "api_key": "secret123",
    "debug_mode": true,
    "feature_flags": ["auth", "cache", "monitoring"]
}
```

---

## 🧪 Testing

### 🚀 Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=configset tests/

# Run specific test file
pytest tests/test_configset.py -v
```

### 📝 Test Example

```python
import pytest
from configset import ConfigSet
import tempfile
import os

def test_config_basic_operations():
    """Test basic configuration operations."""
    with tempfile.NamedTemporaryFile(suffix='.ini', delete=False) as f:
        config_file = f.name
    
    try:
        config = ConfigSet(config_file)
        
        # Test write and read
        config.write_config('test', 'key', 'value')
        assert config.get_config('test', 'key') == 'value'
        
        # Test type conversion
        config.write_config('test', 'number', '42')
        assert config.get_config('test', 'number') == 42
        assert isinstance(config.get_config('test', 'number'), int)
        
        # Test boolean
        config.write_config('test', 'flag', 'true')
        assert config.get_config('test', 'flag') is True
        
    finally:
        os.unlink(config_file)
```

---

## 🤝 Contributing

We welcome contributions! 🎉

### 📋 Development Setup

```bash
# Clone repository
git clone https://github.com/cumulus13/configset.git
cd configset

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .[dev]
pip install pytest pytest-cov black isort mypy
```

### 🔧 Code Standards

```bash
# Format code
black configset/
isort configset/

# Type checking
mypy configset/

# Run tests
pytest tests/ --cov=configset
```

### 📝 Contributing Guidelines

1. 🍴 **Fork** the repository
2. 🌟 **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. ✅ **Add tests** for your changes
4. 📝 **Update documentation** if needed
5. 🎯 **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. 📤 **Push** to the branch (`git push origin feature/amazing-feature`)
7. 🔄 **Open** a Pull Request

---

## 📊 Changelog

### 🎉 v1.56 (Latest)

- ✨ **New Features:**
  - Enhanced type conversion system
  - List and dictionary parsing
  - Class-based configuration interface
  - Improved CLI with delete operations
  - Search functionality
  - Pretty printing with colors

- 🔧 **Improvements:**
  - Better error handling
  - Python 2/3 compatibility
  - Comprehensive documentation
  - Unit tests coverage
  - Type hints support

- 🗑️ **Removed:**
  - Deprecated methods (`read_config2`, `read_config3`, etc.)
  - Redundant functionality

### 📚 v1.x (Legacy)

- Basic INI file support
- Simple read/write operations
- Limited type conversion

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Hadi Cahyadi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- 🐍 **Python ConfigParser** - Foundation for INI file handling
- 🎨 **Rich Library** - Enhanced terminal output
- 🌈 **Make Colors** - Terminal color support
- 🎯 **JSONColor** - JSON syntax highlighting
- 👥 **Contributors** - Thank you to all contributors!

---

## 📞 Support & Contact

- 📧 **Email**: licface@yahoo.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/cumulus13/configset/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/cumulus13/configset/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/cumulus13/configset/wiki)

---

<div align="center">

**⭐ If you find ConfigSet useful, please consider giving it a star! ⭐**

Made with ❤️ by developers, for developers.

[🔝 Back to Top](#-configset---enhanced-configuration-management-library)

</div>


## Support

*   Python 2.7+, 3.x+
*   Windows, Linux, Mac

## author
[Hadi Cahyadi](mailto:cumulus13@gmail.com)
    

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/cumulus13)

[![Donate via Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/cumulus13)

[Support me on Patreon](https://www.patreon.com/cumulus13)

[Medium](https://medium.com/@cumulus13/configset-a-powerful-python-configuration-management-library-that-actually-makes-sense-67bd622d059f)