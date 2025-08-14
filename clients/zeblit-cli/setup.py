"""
Setup configuration for Zeblit CLI client.

*Version: 1.0.0*
*Author: Zeblit Development Team*
"""

from setuptools import setup, find_packages
import os

# Read version from file
def get_version():
    """Get version from version file."""
    version_file = os.path.join(os.path.dirname(__file__), 'src', 'zeblit_cli', 'version.py')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            content = f.read()
            # Extract version from __version__ = "x.x.x"
            for line in content.split('\n'):
                if line.startswith('__version__'):
                    return line.split('"')[1]
    return "1.0.0"

# Read long description from README
def get_long_description():
    """Get long description from README file."""
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements from file
def get_requirements():
    """Get requirements from requirements.txt."""
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Remove version constraints comments
                    if ';' in line:
                        line = line.split(';')[0].strip()
                    requirements.append(line)
    return requirements

setup(
    name="zeblit-cli",
    version=get_version(),
    author="Zeblit Development Team",
    author_email="dev@zeblit.com",
    description="Command-line client for the Zeblit AI Development Platform",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/zeblit/zeblit-cli",
    project_urls={
        "Bug Tracker": "https://github.com/zeblit/zeblit-cli/issues",
        "Documentation": "https://docs.zeblit.com/cli",
        "Source Code": "https://github.com/zeblit/zeblit-cli",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Tools",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "coverage>=7.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "coverage>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "zeblit=zeblit_cli.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai development platform cli command-line automation coding assistant",
)
