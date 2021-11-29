# --------------------------------------------
# Setup file for the package
#
# Tomáš Bouška (c) 2021
# --------------------------------------------

import os
from setuptools import setup, find_packages


def read_file(fname):
    "Read a local file"

    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="mkdocs-zettelkasten",
    version="0.1.5",
    description="Add Zettelkasten features to MkDocs",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    keywords="mkdocs python markdown zettelkasten",
    url="https://github.com/tbouska/mkdocs-zettelkasten",
    author="Tomáš Bouška",
    author_email="tomas@buvis.net",
    license="MIT",
    python_requires=">=3.8",
    install_requires=[
        "mkdocs>=1.1",
        "jinja2",
        "gitpython",
        "pymdown-extensions",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={},
    entry_points={
        "mkdocs.plugins": ["zettelkasten = plugin.plugin:ZettelkastenPlugin"],
        "mkdocs.themes": [
            "zettelkasten-solarized-light = themes.solarized_light",
        ],
    },
)
