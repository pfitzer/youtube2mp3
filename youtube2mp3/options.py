__author__ = 'micpfist'

from optparse import OptionParser

usage = "usage: %prog [options] arg1 arg2"
parser = OptionParser(usage=usage)
parser.add_option("-d", "--directory", dest="directory", help="directory to store the files")
parser.add_option("-y", "--youtube-url", dest="youtube_url", help="link to a youtube video or playlist")
(options, args) = parser.parse_args()
