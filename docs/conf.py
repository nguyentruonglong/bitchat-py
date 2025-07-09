# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from bitchat import __version__

# Add the parent directory of 'docs' to sys.path to find the 'bitchat' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Bitchat Python Library"
copyright = "2025, Nguyen Truong Long"
author = "Nguyen Truong Long"
release = __version__  # Use package version from bitchat/__init__.py
version = __version__  # Short version (can be major.minor, but using full version for simplicity)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Generate documentation from docstrings
    "sphinx.ext.napoleon",  # Support Google and NumPy style docstrings
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Autodoc configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

autodoc_member_order = "bysource"  # Order members by source code order
autodoc_default_options = {
    "members": True,  # Include all members
    "undoc-members": True,  # Include members without docstrings
    "show-inheritance": True,  # Show inheritance information
}