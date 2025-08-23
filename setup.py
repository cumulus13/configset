#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script for ConfigSet - Enhanced Configuration Management Library
"""

import io
import os
import re
import sys
import traceback
from pathlib import Path
from setuptools import setup, find_packages

# Remove old version file if exists
try:
    version_file_in_package = os.path.join('configset', '__version__.py')
    if os.path.exists(version_file_in_package):
        os.remove(version_file_in_package)
except Exception:
    pass

# Copy version file to package
try:
    import shutil
    if os.path.exists('__version__.py'):
        shutil.copy2('__version__.py', 'configset/')
except Exception:
    pass

def get_version():
    """
    Get the version from __version__.py file or package.
    
    The __version__.py file should contain:
    version = "2.0.0"
    """
    version = "2.0.0"  # Fallback version
    
    # Try to read from root __version__.py first
    try:
        version_file = Path(__file__).parent / "__version__.py"
        if version_file.is_file():
            with open(version_file, "r", encoding='utf-8') as f:
                content = f.read()
                # Use regex to find version
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
    except Exception as e:
        if os.getenv('TRACEBACK', '').lower() in ['1', 'true']:
            print(f"Warning: Error reading __version__.py from root: {e}")
            print(traceback.format_exc())
    
    # Try to read from configset/__version__.py
    try:
        version_file = Path(__file__).parent / "configset" / "__version__.py"
        if version_file.is_file():
            with open(version_file, "r", encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
    except Exception as e:
        if os.getenv('TRACEBACK', '').lower() in ['1', 'true']:
            print(f"Warning: Error reading __version__.py from package: {e}")
            print(traceback.format_exc())
    
    # Try to read from configset/__init__.py
    try:
        init_file = Path(__file__).parent / "configset" / "__init__.py"
        if init_file.is_file():
            with open(init_file, "r", encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
    except Exception as e:
        if os.getenv('TRACEBACK', '').lower() in ['1', 'true']:
            print(f"Warning: Error reading version from __init__.py: {e}")
    
    print(f"Warning: Could not determine version, using fallback: {version}")
    return version

def get_long_description():
    """Read the README.md file for long description."""
    readme_file = Path(__file__).parent / "README.md"
    try:
        with io.open(readme_file, "rt", encoding="utf8") as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not read README.md: {e}")
        return "Enhanced Configuration Management Library for Python"

def get_requirements():
    """Get requirements based on Python version."""
    requirements = []
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "requirements.txt")
    with open(filename, "r", encoding="utf-8") as f:
        requirements.extend(line.strip() for line in f if line.strip() and not line.startswith("#"))

    # Only add configparser for Python 2.7
    if sys.version_info < (3, 0):
        requirements.append('configparser')
    
    # argparse is built-in for Python 2.7+ and 3.2+
    if sys.version_info < (2, 7):
        requirements.append('argparse')
    
    return requirements

def get_extras_require():
    """Define optional dependencies."""
    return {
        'full': [
            'rich>=10.0.0',
            'make-colors>=1.0.0',
            'json',
            'pyyaml',
            'licface',
            'jsoncolor>=0.2.0', 
            'richcolorlog',
            
        ],
        'colors': [
            'rich>=10.0.0',
            'make-colors>=1.0.0',
            'licface',
            'jsoncolor>=0.2.0', 
            'richcolorlog',
        ],
        'json': [
            'jsoncolor>=0.2.0'
        ],
        'dev': [
            'pytest>=4.0.0',
            'pytest-cov>=2.8.0',
            'black>=19.0.0',
            'isort>=4.3.0',
            'mypy>=0.700',
            'flake8>=3.7.0'
        ]
    }

# Get version
version = get_version()
print(f"Building ConfigSet version: {version}")

setup(
    name="configset",
    version=version,
    url="https://github.com/cumulus13/configset",
    project_urls={
        "Documentation": "https://github.com/cumulus13/configset/wiki",
        "Source Code": "https://github.com/cumulus13/configset",
        "Bug Tracker": "https://github.com/cumulus13/configset/issues",
        "Changelog": "https://github.com/cumulus13/configset/releases",
    },
    license="MIT",
    author="Hadi Cahyadi",
    author_email="cumulus13@gmail.com",
    maintainer="cumulus13",
    maintainer_email="cumulus13@gmail.com",
    description="A powerful and flexible configuration management library that supports both INI and JSON formats with automatic type conversion, list/dictionary parsing, and class-based interfaces.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    
    # Package discovery
    packages=find_packages(exclude=['tests*', 'examples*', 'docs*']),
    package_data={
        'configset': ['*.py'],
    },
    
    # Dependencies
    install_requires=get_requirements(),
    extras_require=get_extras_require(),
    
    # Python version support
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*",
    
    # Entry points
    entry_points={
        'console_scripts': [
            'configset=configset:main',
            'configset-cli=configset:main',
        ],
    },
    
    # Package classification
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",  # Fixed: was BSD License
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries",
        "Topic :: Text Processing :: General",
    ],
    
    # Keywords for PyPI search
    keywords=[
        "configuration", "config", "ini", "json", "settings", 
        "configparser", "management", "file", "parser", "setup"
    ],
    
    # Include additional files
    include_package_data=True,
    
    # Zip safety
    zip_safe=False,
    
    # Platform specific
    platforms=['any'],
)