# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 15:06:46 2020

@author: 58275
"""

from PyQt5 import QtWidgets, QtCore, QtMultimedia
import sys
import time
import asyncio
import wave
import contextlib
import os


class Audio(object):
    def __init__(self, volume):
        self.volume = volume
        # self.file_path =  file_path
        self.loop = asyncio.get_event_loop()
        self.player = QtMultimedia.QMediaPlayer()
        self.player2 = QtMultimedia.QMediaPlayer()

    def aud_time(self):
        with contextlib.closing(wave.open(self.path, 'r')) as f:
            frame = f.getnframes()
            rate = f.getframerate()
            duration = frame / float(rate)
        return duration

    @asyncio.coroutine
    def play_aud(self, file_name, wait_time):
        url = QtCore.QUrl.fromLocalFile('.\\audio\\' + str(file_name) + '.wav')
        content = QtMultimedia.QMediaContent(url)
        self.player.setMedia(content)
        self.player.setVolume(self.volume)
        yield from asyncio.sleep(wait_time)
        self.player.play()

    @asyncio.coroutine
    def play_aud2(self, file_name, wait_time):
        url = QtCore.QUrl.fromLocalFile('.\\audio\\' + str(file_name) + '.wav')
        content = QtMultimedia.QMediaContent(url)
        self.player2.setMedia(content)
        self.player2.setVolume(self.volume)
        yield from asyncio.sleep(wait_time)
        self.player2.play()

    def play_aud_dirc(self, file_name):
        url = QtCore.QUrl.fromLocalFile('.\\audio\\' + str(file_name) + '.wav')
        content = QtMultimedia.QMediaContent(url)
        self.player.setMedia(content)
        self.player.setVolume(self.volume)
        self.player.play()

    def play_aud_merge(self, file_name1, file_name2, wait_time1=0, wait_time2=2):
        task = [self.play_aud(file_name1, wait_time1), self.play_aud2(file_name2, wait_time2)]
        self.loop.run_until_complete(asyncio.wait(task))
        self.loop.close

    def aud_info(self):
        file_floder = './audio'
        file_path = os.listdir(file_floder)
        aud_dic = {}
        num = 0
        for i in range(len(file_path)):
            aud_dic[file_path[i]] = num
            num = num + 1
        print(aud_dic)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    audio = Audio(50)
    audio2 = Audio(50)

    flag = True
    while True:
        if flag is True:
            # audio2.play_aud_dirc('bgm')
            audio.play_aud_merge('1', 'assign_close')
            flag = False

    sys.exit(app.exec())
