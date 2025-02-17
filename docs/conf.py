"""
Configuration file for the Sphinx documentation builder.
"""

import os
import sys


import sphinx_bootstrap_theme

sys.path.append(os.path.abspath("./_ext"))

# -- Project information -----------------------------------------------------

project = "Python NillionClient"
copyright = "2024, Nillion"
author = "Nillion"
master_doc = "index"

# TODO
release = "0.1.0"  # nillion_client.version()  # pylint: disable=no-member
version = release

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_markdown_builder",
    "sphinx_autodoc_typehints",
    "nbsphinx",
    "nbsphinx_link",
    "myst_parser",
]

markdown_http_base = "https://docs.nillion.com/pydocs/client"
markdown_anchor_signatures = True

language = "en"

autosummary_generate = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
autosectionlabel_prefix_document = True

html_theme = "bootstrap"
html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()
html_static_path = ["_static"]

html_show_copyright = False
html_show_sourcelink = False
html_show_sphinx = False

html_favicon = "_static/nillion.ico"
html_logo = "_static/logo.png"

# Theme options are theme-specific and customize the look and feel of a
# theme further.
html_theme_options = {
    # Navigation bar title. (Default: ``project`` value)
    "navbar_title": "Nillion Python Client",
    # Tab name for entire site. (Default: "Site")
    "navbar_site_name": "Site",
    # A list of tuples containing pages or urls to link to.
    # Valid tuples should be in the following forms:
    #    (name, page)                 # a link to a page
    #    (name, "/aa/bb", 1)          # a link to an arbitrary relative url
    #    (name, "http://example.com", True) # arbitrary absolute url
    # Note the "1" or "True" value above as the third argument to indicate
    # an arbitrary url.
    "navbar_links": [
        ("About", "about"),
        ("Install", "install"),
        ("Tutorials", "tutorials"),
        ("Client Reference", "client"),
        ("GitHub", "https://github.com/NillionNetwork", True),
    ],
    # Render the next and previous page links in navbar. (Default: true)
    "navbar_sidebarrel": False,
    # Render the current pages TOC in the navbar. (Default: true)
    "navbar_pagenav": False,
    # Tab name for the current pages TOC. (Default: "Page")
    "navbar_pagenav_name": "Sections",
    # Global TOC depth for "site" navbar tab. (Default: 1)
    # Switching to -1 shows all levels.
    "globaltoc_depth": -1,
    # Include hidden TOCs in Site navbar?
    #
    # Note: If this is "false", you cannot have mixed ``:hidden:`` and
    # non-hidden ``toctree`` directives in the same page, or else the build
    # will break.
    #
    # Values: "true" (default) or "false"
    "globaltoc_includehidden": "false",
    # HTML navbar class (Default: "navbar") to attach to <div> element.
    # For black navbar, do "navbar navbar-inverse"
    "navbar_class": "navbar",
    # Fix navigation bar to top of page?
    # Values: "true" (default) or "false"
    "navbar_fixed_top": "true",
    # Location of link to source.
    # Options are "nav" (default), "footer" or anything else to exclude.
    "source_link_position": "nav",
    # Bootswatch (http://bootswatch.com/) theme.
    #
    # Options are nothing (default) or the name of a valid theme
    # such as "cosmo" or "sandstone".
    #
    # The set of valid themes depend on the version of Bootstrap
    # that"s used (the next config option).
    #
    # Currently, the supported themes are:
    # - Bootstrap 2: https://bootswatch.com/2
    # - Bootstrap 3: https://bootswatch.com/3
    # "bootswatch_theme": "yeti",
    "bootswatch_theme": "lumen",
    # Choose Bootstrap version.
    # Values: "3" (default) or "2" (in quotes)
    "bootstrap_version": "3",
}

nbsphinx_allow_errors = True
nbsphinx_execute = "never"


def skip_new_member(app, what, name, obj, skip, options):
    # pylint:disable=too-many-arguments,unused-argument,pointless-string-statement
    """don't create documents for the `new` method"""
    """as we've already documented this at the class level"""
    if name == "__new__":
        return True
    return skip


def setup(app):
    """initialize the doc builder"""
    app.connect("autodoc-skip-member", skip_new_member)
    app.add_css_file("css/max_width.css")
