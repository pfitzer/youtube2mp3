import argparse

from youtube2mp3 import __version__

parser = argparse.ArgumentParser(prog='youtube2mp3',
                                 description='Download youtube videos and convert them to tagged mp3 files.')
parser.add_argument('-d', '--directory', required=True, help='directory to store the files')
parser.add_argument('-y', '--youtube-url', required=True,
                    help='link to a youtube video or playlist. Or path to a file with yt urls.')
parser.add_argument('-V', '--version', action='version', version='Version: %s' % __version__,
                    help='show version and exit')
