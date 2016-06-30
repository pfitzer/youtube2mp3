__author__ = 'micpfist'

"""Packaging settings."""


from codecs import open
from os.path import abspath, dirname, join

from setuptools import setup

from youtube2mp3 import __version__, __author__


this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()

setup(
    name = 'youtube2mp3',
    version = __version__,
    description = 'Commandline tool to convert youtube videos to tagged mp3 files',
    long_description = long_description,
    url = 'https://github.com/pfitzer/youtube2mp3.git',
    author = __author__,
    author_email = 'pfitzer666@gmail.com',
    license = 'MIT',
    install_requires = ['youtube-dl', 'mutagen'],
    entry_points = {
        'console_scripts': [
            'youtube2mp3=youtube2mp3.cli:main',
        ],
    }
)