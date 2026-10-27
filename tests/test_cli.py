import glob
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import yt_dlp
from mutagen.easyid3 import EasyID3

from youtube2mp3 import __version__, cli
from youtube2mp3.cli import CollectFilesPP, Youtube2mp3

NETWORK_TESTS = os.environ.get('YOUTUBE2MP3_NETWORK_TESTS') == '1'
HAS_FFMPEG = shutil.which('ffmpeg') is not None


class BaseTestCase(unittest.TestCase):
    def setUp(self):
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


class TestCollectFilesPP(unittest.TestCase):
    def test_hands_over_final_file(self):
        y = Youtube2mp3()
        info = {'filepath': '/tmp/a.mp3', 'title': 'a'}
        CollectFilesPP(y._add_file).run(info)
        self.assertEqual([('/tmp/a.mp3', info)], y.downloaded_files)

    def test_keeps_info_when_yt_dlp_clears_it(self):
        y = Youtube2mp3()
        info = {'filepath': '/tmp/a.mp3', 'title': 'a'}
        CollectFilesPP(y._add_file).run(info)
        info.clear()
        self.assertEqual('a', y.downloaded_files[0][1]['title'])

    def test_ignores_info_without_filepath(self):
        y = Youtube2mp3()
        CollectFilesPP(y._add_file).run({'title': 'a'})
        self.assertEqual([], y.downloaded_files)


class TestSetId3(BaseTestCase):
    def test_tags_file(self):
        path = self.create_mp3('Foo - Bar [abc123].mp3')
        y = Youtube2mp3()
        y.downloaded_files = [(path, {'title': 'Foo - Bar'})]
        y._set_id3()

        tags = EasyID3(path)
        self.assertEqual(['Foo'], tags['artist'])
        self.assertEqual(['Bar'], tags['title'])

    def test_continues_when_tagging_fails(self):
        first = self.create_mp3('Starchild [abc123].mp3')
        second = self.create_mp3('Foo - Bar [abc123].mp3')
        y = Youtube2mp3()
        y.downloaded_files = [(first, {'title': 'Starchild'}), (second, {'title': 'Foo - Bar'})]
        with mock.patch.object(Youtube2mp3, '_get_tagging_params', side_effect=[ValueError, ('Foo', 'Bar')]):
            y._set_id3()
        self.assertEqual(['Bar'], EasyID3(second)['title'])

    def test_skips_missing_file(self):
        path = self.create_mp3('Foo - Bar [abc123].mp3')
        y = Youtube2mp3()
        y.downloaded_files = [(os.path.join(self.src_dir, 'missing.mp3'), {}), (path, {'title': 'Foo - Bar'})]
        y._set_id3()
        self.assertEqual(['Bar'], EasyID3(path)['title'])


class TestRun(BaseTestCase):
    def run_with_mocked_ydl(self, youtube_url, retcode=0):
        with mock.patch.object(yt_dlp, 'YoutubeDL') as ydl_cls:
            ydl = ydl_cls.return_value.__enter__.return_value
            ydl.download.return_value = retcode
            result = Youtube2mp3().run(self.dest_dir, youtube_url)
        return result, ydl_cls, ydl

    def test_passes_all_urls_from_file_in_one_call(self):
        url_file = os.path.join(self.src_dir, 'urls.txt')
        with open(url_file, 'w', encoding='utf-8') as f:
            f.write('https://example.com/a\n\n  https://example.com/b  \n')
        _result, _ydl_cls, ydl = self.run_with_mocked_ydl(url_file)
        ydl.download.assert_called_once_with(['https://example.com/a', 'https://example.com/b'])

    def test_downloads_into_target_directory(self):
        _result, ydl_cls, _ydl = self.run_with_mocked_ydl('https://example.com/v')
        self.assertEqual(self.dest_dir, ydl_cls.call_args.args[0]['paths']['home'])

    def test_returns_0_on_success(self):
        result, _ydl_cls, _ydl = self.run_with_mocked_ydl('https://example.com/v')
        self.assertEqual(0, result)

    def test_returns_1_on_failed_download(self):
        result, _ydl_cls, _ydl = self.run_with_mocked_ydl('https://example.com/v', retcode=1)
        self.assertEqual(1, result)


class TestMain(BaseTestCase):
    def test_main_passes_options_to_run(self):
        with mock.patch.object(Youtube2mp3, 'run', return_value=0) as run:
            self.assertEqual(0, cli.main(['-d', self.dest_dir, '-y', 'https://example.com/v']))
        run.assert_called_once_with(self.dest_dir, 'https://example.com/v')

    def test_main_returns_exit_code_of_run(self):
        with mock.patch.object(Youtube2mp3, 'run', return_value=1):
            self.assertEqual(1, cli.main(['-d', self.dest_dir, '-y', 'https://example.com/v']))

    def test_missing_directory_exits(self):
        with self.assertRaises(SystemExit) as cm, redirect_stderr(io.StringIO()):
            cli.main(['-y', 'https://example.com/v'])
        self.assertEqual(2, cm.exception.code)

    def test_missing_url_exits(self):
        with self.assertRaises(SystemExit) as cm, redirect_stderr(io.StringIO()):
            cli.main(['-d', self.dest_dir])
        self.assertEqual(2, cm.exception.code)

    def test_version(self):
        out = io.StringIO()
        with self.assertRaises(SystemExit) as cm, redirect_stdout(out):
            cli.main(['-V'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn(__version__, out.getvalue())


class FileUrlYoutubeDL(yt_dlp.YoutubeDL):
    def __init__(self, params=None, *args, **kwargs):
        params = dict(params or {}, enable_file_urls=True, quiet=True, noprogress=True)
        super().__init__(params, *args, **kwargs)


@unittest.skipUnless(HAS_FFMPEG, 'ffmpeg is required')
class TestPipeline(BaseTestCase):
    def create_webm(self, name):
        source = os.path.join(self.src_dir, name)
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'sine=d=1',
                        '-c:a', 'libopus', source], check=True)
        return 'file://' + source.replace(' ', '%20')

    def test_local_file_is_converted_and_tagged(self):
        url = self.create_webm('Daft Punk - Around the World.webm')
        with mock.patch.object(yt_dlp, 'YoutubeDL', FileUrlYoutubeDL):
            self.assertEqual(0, Youtube2mp3().run(self.dest_dir, url))

        files = self.dest_files()
        self.assertEqual(1, len(files))
        tags = EasyID3(files[0])
        self.assertEqual(['Daft Punk'], tags['artist'])
        self.assertEqual(['Around the World'], tags['title'])

    def test_relative_paths_are_resolved_against_cwd(self):
        url = self.create_webm('Daft Punk - Around the World.webm')
        url_file = os.path.join(self.dest_dir, 'urls.txt')
        with open(url_file, 'w', encoding='utf-8') as f:
            f.write(url + '\n')
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.dest_dir)
        with mock.patch.object(yt_dlp, 'YoutubeDL', FileUrlYoutubeDL):
            Youtube2mp3().run('Musik', 'urls.txt')
        self.assertEqual(1, len(glob.glob(os.path.join(self.dest_dir, 'Musik', '*.mp3'))))

    def test_missing_target_directory_is_created(self):
        url = self.create_webm('Daft Punk - Around the World.webm')
        target = os.path.join(self.dest_dir, 'does', 'not', 'exist')
        with mock.patch.object(yt_dlp, 'YoutubeDL', FileUrlYoutubeDL):
            Youtube2mp3().run(target, url)
        self.assertEqual(1, len(glob.glob(os.path.join(target, '*.mp3'))))

    def test_failed_download_returns_error(self):
        url = 'file://' + os.path.join(self.src_dir, 'missing.webm')
        with mock.patch.object(yt_dlp, 'YoutubeDL', FileUrlYoutubeDL):
            self.assertEqual(1, Youtube2mp3().run(self.dest_dir, url))


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
