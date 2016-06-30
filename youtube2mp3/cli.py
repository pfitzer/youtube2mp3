from __future__ import unicode_literals
import youtube_dl
import os
from options import options
from mutagen.easyid3 import EasyID3

def main():
    if not options.directory:
        print "a directory where to save the files must be set!"
        return -1
    if not options.youtube_url:
        print "the youtube url is missing!"
        return -1


    os.chdir(options.directory)
    ydl_opts = {'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [download_hook],}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([options.youtube_url])

    set_id3()


def download_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')
        print(d['filename'])


def mp3gen():
    for root, dirs, files in os.walk(options.directory):
        for filename in files:
            if os.path.splitext(filename)[1] == ".mp3":
                yield os.path.join(root, filename)


def set_id3():
    for mp3file in mp3gen():
        base = os.path.basename(mp3file)
        (artist, title, code) = os.path.splitext(base)[0].split('-')
        file = EasyID3(mp3file)
        file['title'] = title
        file['artist'] = artist
        file.save()
