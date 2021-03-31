import os
from setuptools import setup


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name = "comics-py",
    version = "1.0",
    author = "Philipp Glaum",
    author_email = "p@pglaum.de",
    description = ("A comic downloader"),
    license = "MIT",
    keywords = "comic download",
    url = "https://git.sr.ht/~pglaum/comics.py",
    packages=['comics-py'],
    install_requires=[
        'bs4',
        'click',
        'cloudscraper',
        'img2pdf',
        'requests',
        'tqdm',
        'yaml-1.3'
    ],
    long_description=read('README.md'),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
)
