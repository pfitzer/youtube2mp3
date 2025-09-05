from __future__ import unicode_literals

import os
import platform
import re
import shutil
import sys
import tempfile

import yt_dlp
from mutagen.easyid3 import EasyID3

from youtube2mp3.options import options


# noinspection PyBroadException,PyBroadException
class Youtube2mp3(object):
    def __init__(self):
        self.downloaded_files = []
        tempdir = '/tmp' if platform.system() == 'Darwin' else tempfile.gettempdir()
        os.chdir(tempdir)

    def run(self, directory, youtube_url):
        if not directory:
            print('a directory "-d" where to save the files must be set!')
            sys.exit(1)
        if not youtube_url:
            print('the youtube url "-y" is missing!')
            sys.exit(1)
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [self._download_hook],
            'ignoreerrors': True,  # Fügt diese Option hinzu
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                if os.path.isfile(youtube_url):
                    with open(youtube_url, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f if line.strip()]
                    for line in lines:
                        try:
                            ydl.download([line])
                        except Exception as e:
                            print(f'Fehler beim Download von {line}: {str(e)}')
                else:
                    ydl.download([youtube_url])
            except (yt_dlp.utils.DownloadError,
                    yt_dlp.utils.ContentTooShortError,
                    yt_dlp.utils.ExtractorError) as e:
                print(str(e))
                sys.exit(1)
        self._set_id3(directory)

    def _download_hook(self, d):
        if d.get('status') == 'finished':
            filename = d.get('filename')
            if filename:
                self.downloaded_files.append(filename)
                print('Done downloading, now converting ...')
                print(filename)

    @staticmethod
    def _get_tagging_params(name):
        regex = r'(?=-)'
        if len(re.findall(regex, name)) > 2:
            name = re.sub('-', '', name, 1)
        artist, title, code = name.split('-', 2)
        return artist.strip(), title.strip(), code.strip()

    def _set_id3(self, dest_dir):
        if not self.downloaded_files:
            return
        for filename in self.downloaded_files:
            try:
                base = os.path.basename(str(filename))
                name = os.path.splitext(base)[0]
            except Exception:
                continue
            try:
                artist, title, _code = self._get_tagging_params(name)
                print("[tagging]: %s" % (name + '.mp3'))
                id3_file = EasyID3(name + '.mp3')
                id3_file['title'] = title
                id3_file['artist'] = artist
                id3_file.save()
            except Exception:
                print('[info]: not able to tag file. naming problem')
                continue
            shutil.move(name + '.mp3', os.path.join(dest_dir, name + '.mp3'))


def main():
    y2mp3 = Youtube2mp3()
    y2mp3.run()


if __name__ == '__main__':
    main()
