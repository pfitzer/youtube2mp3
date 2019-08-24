import unittest
import os

from youtube2mp3.cli import Youtube2mp3
from youtube2mp3.options import options

TEST_ROOT = os.path.dirname(os.path.abspath(__file__))

setattr(options, 'directory', TEST_ROOT)
setattr(options, 'youtube_url', 'https://www.youtube.com/watch?v=XPudIeRotdI')


class TestCase(unittest.TestCase):
    def test_download(self):
        y = Youtube2mp3()
        y.run()
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
