from __future__ import unicode_literals

import os
import platform
import re
import shutil
import sys
import tempfile

import youtube_dl
from mutagen.easyid3 import EasyID3

from youtube2mp3.options import options


# noinspection PyBroadException,PyBroadException
class Youtube2mp3(object):
    FILES = []

    def __init__(self):
        self.FILES = []
        tempdir = '/tmp' if platform.system() == 'Darwin' else tempfile.gettempdir()
        os.chdir(tempdir)

    def run(self):
        if not options.directory:
            print("a directory \"-d\" where to save the files must be set!")
            sys.exit(1)
        if not options.youtube_url:
            print("the youtube url \"-y\" is missing!")
            sys.exit(1)

        ydl_opts = {'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [self._download_hook], }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                if os.path.isfile(options.youtube_url):
                    file = open(options.youtube_url, 'r')
                    lines = file.readlines()
                    ydl.download(lines)
                    file.close()
                else:
                    ydl.download([options.youtube_url])
            except (youtube_dl.utils.DownloadError, youtube_dl.utils.ContentTooShortError,
                    youtube_dl.utils.ExtractorError) as e:
                print(e.message)
                sys.exit(1)

        self._set_id3()

    def _download_hook(self, d):
        if d['status'] == 'finished':
            self.FILES.append(d['filename'])
            print('Done downloading, now converting ...')
            print(d['filename'])

    @staticmethod
    def _get_tagging_params(name):
        regex = '(?=-)'
        if len(re.findall(regex, name)) > 2:
            name = re.sub('-', '', name, 1)
        (artist, title, code) = name.split('-')
        return artist, title, code

    def _set_id3(self):
        if self.FILES:
            for file in self.FILES:
                try:
                    base = os.path.basename(str(file))
                    name = os.path.splitext(base)[0]
                except Exception:  # noqa
                    continue
                try:
                    (artist, title, code) = self._get_tagging_params(name)
                    print("[tagging]: %s" % name + '.mp3')
                    file = EasyID3(name + '.mp3')
                    file['title'] = title
                    file['artist'] = artist
                    file.save()
                except Exception:
                    print('[info]: not able to tag file. naming problem')
                    pass
                shutil.move(name + '.mp3', os.path.join(options.directory, name + '.mp3'))


def main():
    y2mp3 = Youtube2mp3()
    y2mp3.run()


if __name__ == '__main__':
    main()
