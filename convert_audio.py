# -*- coding: utf-8 -*
"""
https://ffmpy.readthedocs.io/en/latest/index.html
Convert .m4a to .mp3, setup title, artist and album for mp3 files.

Created on 2022-3-5
@author: Ocean
"""

import sys
import os
import ffmpy

def main():
    '''main'''
    folder = '/Users/songyang/Desktop/audio'
    for root, dirs, files in os.walk(folder):
        for file in files:
            item = os.path.join(root, file)
            fmt = os.path.splitext(item)[-1]
            if fmt.lower() != '.m4a':
                continue
            else:
                output = os.path.join(root, 'mp3',file.replace('m4a','mp3'))
                ff = ffmpy.FFmpeg(
                    executable='/Users/songyang/Applications/ffmpeg',
                    inputs={item: None},
                    outputs={output: [
                        '-metadata', 'title=Gift for Cathy.',
                        '-metadata', 'artist=Ocean',
                        '-metadata', 'album=Story'
                    ]},
                )
                ff.run()


if __name__ == '__main__':
    main()
