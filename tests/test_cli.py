import glob
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import yt_dlp
from mutagen.easyid3 import EasyID3

from youtube2mp3 import cli
from youtube2mp3.cli import Youtube2mp3

NETWORK_TESTS = os.environ.get('YOUTUBE2MP3_NETWORK_TESTS') == '1'
HAS_FFMPEG = shutil.which('ffmpeg') is not None


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # Youtube2mp3() changes the working directory
        self.addCleanup(os.chdir, os.getcwd())
        self.src_dir = tempfile.mkdtemp()
        self.dest_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.src_dir, True)
        self.addCleanup(shutil.rmtree, self.dest_dir, True)

    def create_mp3(self, name):
        # EasyID3 only needs a file to write the tag into, valid audio is not required
        path = os.path.join(self.src_dir, name)
        with open(path, 'wb') as f:
            f.write(b'\xff\xfb\x90\x00' + b'\x00' * 413)
        return path

    def dest_files(self):
        return glob.glob(os.path.join(self.dest_dir, '*.mp3'))


class TestGetTaggingParams(unittest.TestCase):
    def test_artist_and_track_from_metadata(self):
        info = {'title': 'something else', 'artist': 'Daft Punk', 'track': 'Around the World'}
        self.assertEqual(('Daft Punk', 'Around the World'), Youtube2mp3._get_tagging_params(info))

    def test_artist_and_title_from_video_title(self):
        info = {'title': 'Daft Punk - Around the World'}
        self.assertEqual(('Daft Punk', 'Around the World'), Youtube2mp3._get_tagging_params(info))

    def test_splits_only_at_first_separator(self):
        info = {'title': 'Artist – Song - Remix'}
        self.assertEqual(('Artist', 'Song - Remix'), Youtube2mp3._get_tagging_params(info))

    def test_hyphen_without_spaces_is_not_a_separator(self):
        info = {'title': 'Jay-Z', 'channel': 'Some Channel'}
        self.assertEqual(('Some Channel', 'Jay-Z'), Youtube2mp3._get_tagging_params(info))

    def test_fallback_to_uploader(self):
        info = {'title': 'Starchild', 'uploader': 'Someone'}
        self.assertEqual(('Someone', 'Starchild'), Youtube2mp3._get_tagging_params(info))

    def test_empty_info(self):
        self.assertEqual(('', ''), Youtube2mp3._get_tagging_params({}))


class TestPostprocessorHook(BaseTestCase):
    def test_collects_final_file(self):
        y = Youtube2mp3()
        info = {'filepath': '/tmp/a.mp3', 'title': 'a'}
        y._postprocessor_hook({'status': 'finished', 'postprocessor': 'MoveFiles', 'info_dict': info})
        self.assertEqual([('/tmp/a.mp3', info)], y.downloaded_files)

    def test_ignores_other_postprocessors_and_states(self):
        y = Youtube2mp3()
        info = {'filepath': '/tmp/a.webm'}
        y._postprocessor_hook({'status': 'finished', 'postprocessor': 'ExtractAudio', 'info_dict': info})
        y._postprocessor_hook({'status': 'started', 'postprocessor': 'MoveFiles', 'info_dict': info})
        self.assertEqual([], y.downloaded_files)


class TestSetId3(BaseTestCase):
    def test_tags_and_moves_file(self):
        path = self.create_mp3('Foo - Bar [abc123].mp3')
        y = Youtube2mp3()
        y.downloaded_files = [(path, {'title': 'Foo - Bar'})]
        y._set_id3(self.dest_dir)

        target = os.path.join(self.dest_dir, 'Foo - Bar [abc123].mp3')
        self.assertFalse(os.path.exists(path))
        self.assertTrue(os.path.isfile(target))
        tags = EasyID3(target)
        self.assertEqual(['Foo'], tags['artist'])
        self.assertEqual(['Bar'], tags['title'])

    def test_moves_file_when_tagging_fails(self):
        path = self.create_mp3('Starchild [abc123].mp3')
        y = Youtube2mp3()
        y.downloaded_files = [(path, {'title': 'Starchild'})]
        with mock.patch.object(Youtube2mp3, '_get_tagging_params', side_effect=ValueError):
            y._set_id3(self.dest_dir)
        self.assertTrue(os.path.isfile(os.path.join(self.dest_dir, 'Starchild [abc123].mp3')))

    def test_skips_missing_file(self):
        path = self.create_mp3('Foo - Bar [abc123].mp3')
        y = Youtube2mp3()
        y.downloaded_files = [(os.path.join(self.src_dir, 'missing.mp3'), {}), (path, {'title': 'Foo - Bar'})]
        y._set_id3(self.dest_dir)
        self.assertEqual(1, len(self.dest_files()))


class TestRun(BaseTestCase):
    def test_missing_directory_exits(self):
        with self.assertRaises(SystemExit):
            Youtube2mp3().run(None, 'https://www.youtube.com/watch?v=hIkvQHk_sWM')

    def test_missing_url_exits(self):
        with self.assertRaises(SystemExit):
            Youtube2mp3().run(self.dest_dir, None)


class TestMain(BaseTestCase):
    def test_main_passes_options_to_run(self):
        argv = ['youtube2mp3', '-d', self.dest_dir, '-y', 'https://example.com/v']
        with mock.patch('sys.argv', argv), mock.patch.object(Youtube2mp3, 'run') as run:
            cli.main()
        run.assert_called_once_with(self.dest_dir, 'https://example.com/v')


class FileUrlYoutubeDL(yt_dlp.YoutubeDL):
    def __init__(self, params=None, *args, **kwargs):
        params = dict(params or {}, enable_file_urls=True, quiet=True, noprogress=True)
        super().__init__(params, *args, **kwargs)


@unittest.skipUnless(HAS_FFMPEG, 'ffmpeg is required')
class TestPipeline(BaseTestCase):
    def test_local_file_is_converted_tagged_and_moved(self):
        source = os.path.join(self.src_dir, 'Daft Punk - Around the World.webm')
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'sine=d=1',
                        '-c:a', 'libopus', source], check=True)

        with mock.patch.object(yt_dlp, 'YoutubeDL', FileUrlYoutubeDL):
            Youtube2mp3().run(self.dest_dir, 'file://' + source.replace(' ', '%20'))

        files = self.dest_files()
        self.assertEqual(1, len(files))
        tags = EasyID3(files[0])
        self.assertEqual(['Daft Punk'], tags['artist'])
        self.assertEqual(['Around the World'], tags['title'])


@unittest.skipUnless(NETWORK_TESTS and HAS_FFMPEG, 'set YOUTUBE2MP3_NETWORK_TESTS=1 to run, ffmpeg is required')
class TestYoutubeDownload(BaseTestCase):
    def test_download(self):
        Youtube2mp3().run(directory=self.dest_dir, youtube_url='https://www.youtube.com/watch?v=hIkvQHk_sWM')
        self.assertEqual(1, len(self.dest_files()))

    def test_download_with_file(self):
        url_file = os.path.join(os.path.dirname(__file__), 'test.txt')
        Youtube2mp3().run(directory=self.dest_dir, youtube_url=url_file)
        # broken urls are skipped (ignoreerrors), at least one download has to succeed
        self.assertGreaterEqual(len(self.dest_files()), 1)


if __name__ == '__main__':
    unittest.main()
