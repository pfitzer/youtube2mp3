import glob
import unittest
import os
import tempfile

from youtube2mp3.cli import Youtube2mp3
from youtube2mp3.options import options

TEST_ROOT = os.path.join(tempfile.gettempdir(), 'youtube2mp2')
if not os.path.isdir(TEST_ROOT):
    os.mkdir(TEST_ROOT)

setattr(options, 'directory', TEST_ROOT)



class TestCase(unittest.TestCase):
    def test_download(self):
        setattr(options, 'youtube_url', 'https://www.youtube.com/watch?v=XPudIeRotdI')
        y = Youtube2mp3()
        y.run()
        file_name = os.path.join(TEST_ROOT, 'EDX - Stay-XPudIeRotdI.mp3')
        self.assertEqual(True, os.path.isfile(file_name))

    def test_download_with_file(self):
        setattr(options, 'youtube_url', os.path.join(os.path.dirname(__file__), 'test.txt'))
        y = Youtube2mp3()
        y.run()
        files = glob.glob(TEST_ROOT + '/*.mp3')
        self.assertEqual(2, len(files))

    def tearDown(self) -> None:
        files = glob.glob(TEST_ROOT + '/*.mp3')
        for file in files:
            os.remove(file)

if __name__ == '__main__':
    unittest.main()
