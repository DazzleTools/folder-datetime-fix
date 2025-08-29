from setuptools import setup, find_packages
import os
import sys

# Add the package directory to path to import version
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_datetime_fix'))
from version import get_pip_version

# Read the README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="folder-datetime-fix",
    version=get_pip_version(),  # Use PEP 440 compliant version for pip
    description="Fix folder timestamps corrupted by system files like thumbs.db on Windows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dustin",
    author_email="6962246+djdarcy@users.noreply.github.com",
    url="https://github.com/djdarcy/modified_datetime_fix",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "folder-datetime-fix=folder_datetime_fix.cli:main",
            "mod_fldr_dt=folder_datetime_fix.cli:main",  # Keep for backward compatibility
        ],
    },
    install_requires=[
        # No external dependencies for core functionality
        # unctools will be added later for enhanced UNC support
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "unc": [
            "unctools>=0.1.0",  # Optional for enhanced UNC path support
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Environment :: Console",
    ],
    python_requires=">=3.7",
    keywords="windows folder timestamp thumbs.db desktop.ini filesystem utilities",
    project_urls={
        "Bug Reports": "https://github.com/djdarcy/modified_datetime_fix/issues",
        "Source": "https://github.com/djdarcy/modified_datetime_fix",
    },
)