import sys
from optparse import OptionParser
from youtube2mp3 import __version__


def show_version(option, opt, value, parser):
    print("Version: %s" % __version__)
    sys.exit(0)


usage = "usage: %prog [options] arg1 arg2"
parser = OptionParser(usage=usage)
parser.add_option("-d", "--directory", dest="directory", help="directory to store the files")
parser.add_option("-y", "--youtube-url", dest="youtube_url", help="link to a youtube video or playlist. Or path to a file with yt urls.")
parser.add_option("-V", "--version", dest="version", help="show version and exit", action="callback",
                  callback=show_version)
(options, args) = parser.parse_args()
