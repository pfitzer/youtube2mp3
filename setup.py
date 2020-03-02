from codecs import open
from os.path import abspath, dirname, join
from setuptools import setup, find_packages
from youtube2mp3 import __version__, __author__

this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='youtube2mp3',
    version=__version__,
    description='Commandline tool to convert youtube videos to tagged mp3 files',
    long_description=long_description,
    url='https://github.com/pfitzer/youtube2mp3.git',
    author=__author__,
    author_email='michael@mp-development.de',
    license='MIT',
    install_requires=['youtube-dl>=2020.3.1', 'mutagen>=1.44.0'],
    keywords='youtube mp3',
    packages=find_packages(),
    python_requires='~=3.6, <4',
    entry_points={
        'console_scripts': [
            'youtube2mp3=youtube2mp3.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Multimedia :: Video :: Conversion'
    ]
)
