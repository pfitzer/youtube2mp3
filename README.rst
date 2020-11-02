|image0| |image1| |image6| |image3| |image4|

youtube2mp3
===========
A wrapper to simplify youtube downloads with `youtube-dl <https://youtube-dl.org/>`_

Currently the `dev repository <https://github.com/ytdl-org/youtube-dl>`_ of youtube-dl is taken down due to `DMCA takedown notice by RIAA <https://github.com/github/dmca/blob/master/2020/10/2020-10-23-RIAA.md>`_, but downloads still work as usual.

Downloaded files will be tagged with `mutagen <https://pypi.python.org/pypi/mutagen>`_.

installation
------------
with pip
""""""""
::

    pip install youtube2mp3


usage
-----
::

    youtube2mp3 [options] arg1 arg2

see *youtube2mp3 -h* for more information
::

    Options:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory=DIRECTORY
                        directory to store the files
  -y YOUTUBE_URL, --youtube-url=YOUTUBE_URL
                        link to a youtube video or playlist. Or path to a file
                        with yt urls.
  -V, --version         show version and exit


development
-----------
Create a virtual environment
::

    python3 -m venv /path/to/new/virtual/environment

install dependencies
::

    pip install -r requirements.txt
    
|image5|


.. |image0| image:: https://img.shields.io/pypi/v/youtube2mp3.svg
     :target: https://pypi.python.org/pypi?name=youtube2mp3&:action=display
     :alt: pypi

.. |image1| image:: https://pyup.io/repos/github/pfitzer/youtube2mp3/shield.svg
     :target: https://pyup.io/repos/github/pfitzer/youtube2mp3/
     :alt: Updates
     
.. |image3| image:: https://img.shields.io/pypi/dm/youtube2mp3.svg
    :target: https://pypistats.org/packages/youtube2mp3
    :alt: PyPI - Downloads
    
.. |image4| image:: https://github.com/pfitzer/youtube2mp3/workflows/Unit%20Test/badge.svg?event=push
    :target: https://github.com/pfitzer/youtube2mp3/actions
    :alt: Unit Tests
    
.. |image5| image:: https://cdn.buymeacoffee.com/buttons/lato-orange.png
    :target: https://www.buymeacoffee.com/pfitzer
    :alt: Buy Me a Beer

.. |image6| image:: https://img.shields.io/pypi/pyversions/youtube2mp3.svg?logo=python&logoColor=FFE873
    :target: https://pypi.python.org/pypi?name=youtube2mp3&:action=display
    :alt: youtube2mp3 on pypi
