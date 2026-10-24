from __future__ import unicode_literals

import os
import platform
import re
import shutil
import sys
import tempfile

import yt_dlp
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

from youtube2mp3.options import parser


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
            'postprocessor_hooks': [self._postprocessor_hook],
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

    @staticmethod
    def _download_hook(d):
        if d.get('status') == 'finished':
            print('Done downloading, now converting ...')
            print(d.get('filename'))

    def _postprocessor_hook(self, d):
        # MoveFiles(AfterDownload) is the last postprocessor, filepath points to the final mp3
        if d.get('status') == 'finished' and str(d.get('postprocessor')).startswith('MoveFiles'):
            info = d.get('info_dict') or {}
            if info.get('filepath'):
                self.downloaded_files.append((info['filepath'], info))

    @staticmethod
    def _get_tagging_params(info):
        artist = info.get('artist') or info.get('creator')
        title = info.get('track')
        if artist and title:
            return artist.strip(), title.strip()
        video_title = info.get('title') or ''
        match = re.match(r'^\s*(?P<artist>.+?)\s+[-–—]\s+(?P<title>.+?)\s*$', video_title)
        if match:
            return match.group('artist'), match.group('title')
        return (artist or info.get('uploader') or info.get('channel') or '').strip(), video_title.strip()

    def _set_id3(self, dest_dir):
        for filepath, info in self.downloaded_files:
            if not os.path.isfile(filepath):
                print('[info]: file not found: %s' % filepath)
                continue
            try:
                artist, title = self._get_tagging_params(info)
                print("[tagging]: %s" % os.path.basename(filepath))
                try:
                    id3_file = EasyID3(filepath)
                except ID3NoHeaderError:
                    id3_file = EasyID3()
                if title:
                    id3_file['title'] = title
                if artist:
                    id3_file['artist'] = artist
                id3_file.save(filepath)
            except Exception:
                print('[info]: not able to tag file %s' % os.path.basename(filepath))
            shutil.move(filepath, os.path.join(dest_dir, os.path.basename(filepath)))


def main():
    options, _args = parser.parse_args()
    y2mp3 = Youtube2mp3()
    y2mp3.run(options.directory, options.youtube_url)


if __name__ == '__main__':
    main()
