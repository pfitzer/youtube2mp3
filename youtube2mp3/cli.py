import os
import re
import tempfile

import yt_dlp
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from yt_dlp.postprocessor import PostProcessor

from youtube2mp3.options import parser


class CollectFilesPP(PostProcessor):
    """Runs after the files are moved to the target directory and hands the final mp3 to a callback."""

    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    def run(self, info):
        if info.get('filepath'):
            # yt-dlp clears the info dict after processing, hand over a copy
            self._callback(info['filepath'], dict(info))
        return [], info


class Youtube2mp3:
    def __init__(self):
        self.downloaded_files = []

    def run(self, directory, youtube_url):
        """Download, convert and tag, returns 0 on success and 1 if a download failed."""
        os.makedirs(directory, exist_ok=True)
        if os.path.isfile(youtube_url):
            with open(youtube_url, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
        else:
            urls = [youtube_url]
        with tempfile.TemporaryDirectory() as tempdir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'paths': {'home': directory, 'temp': tempdir},
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [self._download_hook],
                # skip broken urls, failures are reported through the return code
                'ignoreerrors': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.add_post_processor(CollectFilesPP(self._add_file), when='after_move')
                retcode = ydl.download(urls)
        self._set_id3()
        return 1 if retcode else 0

    @staticmethod
    def _download_hook(d):
        if d.get('status') == 'finished':
            print('Done downloading, now converting ...')
            print(d.get('filename'))

    def _add_file(self, filepath, info):
        self.downloaded_files.append((filepath, info))

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

    def _set_id3(self):
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


def main(argv=None):
    args = parser.parse_args(argv)
    return Youtube2mp3().run(args.directory, args.youtube_url)


if __name__ == '__main__':
    raise SystemExit(main())
