# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


import os
import sys
from dotenv import load_dotenv

# Load the .env file from the project root
load_dotenv(os.path.abspath('../../.env'))

# Your existing path setup
sys.path.insert(0, os.path.abspath('../../../'))

project = 'final_project'
copyright = '2026, Nataliia'
author = 'Nataliia'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon", # Optional: provides better support for Google-style docstrings
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# --- Options for HTML output ---
# You can change the theme here (e.g., 'nature', 'alabaster', or 'furo')
html_theme = 'nature'
html_static_path = ['_static']
