from __future__ import unicode_literals

import os
import shutil
import sys
import re
import tempfile
import platform

import youtube_dl
from mutagen.easyid3 import EasyID3

from youtube2mp3.options import options

class Youtube2mp3(object):
    FILES = []

    def __init__(self):
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

    def _get_tagging_params(self, name):
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
                except Exception:
                    continue
                try:
                    (artist, title, code) = self._get_tagging_params(name)
                    print("[tagging]: %s" % name + '.mp3')
                    file = EasyID3(name + '.mp3')
                    file['title'] = title
                    file['artist'] = artist
                    file.save()
                except Exception as e:
                    print('[info]: not able to tag file. naming problem')
                    pass
                shutil.move(name + '.mp3', os.path.join(options.directory, name + '.mp3'))


def main():
    y2mp3 = Youtube2mp3()
    y2mp3.run()


if __name__ == '__main__':
    main()
