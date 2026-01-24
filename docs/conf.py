# Configuration file for the Sphinx documentation builder.
import os
import sys


# On remonte d'un niveau pour être dans 'MonProjet'
# On ajoute le chemin de 'MyProject' pour que Sphinx voie 'main.py' et les dossiers
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../MyProjects"))

# Ajoute aussi les sous-dossiers pour régler les erreurs d'import entre tes scripts
sys.path.insert(0, os.path.abspath("../MyProjects/Jeux"))
sys.path.insert(0, os.path.abspath("../MyProjects/Calculatrice"))
sys.path.insert(0, os.path.abspath("../MyProjects/Musique"))

# -- Project information -----------------------------------------------------
project = "Python Projects"
author = "Déclaira"
copyright = "2026, Déclaira" # Mis à jour selon ton main.py

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "myst_parser",
    "nbsphinx",
    "sphinx_copybutton",
    "sphinx_favicon",
    "sphinxarg.ext",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "fr"

# -- Options for HTML output -------------------------------------------------
html_theme = "pydata_sphinx_theme"

# On utilise ici le logo de ton application
html_logo = "_static/logo.png"
html_favicon = "_static/logo.png"

html_theme_options = {
    "navbar_align": "left",
    "logo": {
        "text": "Python Projects",
        "image_light": "_static/logo.png",
        "image_dark": "_static/logo.png",
    },
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/Declaira/Python-Projects.git",
            "icon": "fa-brands fa-github",
        },
    ],
    # Couleur d'accentuation pour correspondre à ton orange #ff6f00
    "surface_prop_styles": {
        "primary-color": "#ff6f00",
    },
}

# Ajout du CSS personnalisé pour les dégradés
html_static_path = ["_static"]
html_css_files = [
    "custom.css",
]

# -- Extension configurations ------------------------------------------------
autodoc_typehints = "signature"
autoclass_content = "both"
add_module_names = False
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}