# detector import
from __future__ import division, print_function, absolute_import
from yoloall import YOLOall
from timeit import time
import cv2
from PIL import Image
import tensorflow as tf
import os
# from tensorflow.compat.v1 import InteractiveSession
from tensorflow import InteractiveSession
from tensorflow import Session

from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import threading
from collections import Counter

# system import
from gamelogic import gamelogic
from process import translate, process, pack
import lan
from GUI import ui
from audio import audio
import cfg


def reset_flag():
    """
    跳转页面更新标志位,跳转到下一个页面
    """
    cfg.countdown_pro = cfg.countdown_thres  # 重置标志位
    cfg.confirm_pro = 0
    cfg.flag_confirm = False
    cfg.flag_audio_start = True  # 允许播放开始语音
    cfg.flag_jump = True  # 允许跳转页面
    cfg.flag_audio_cheat = True  # 允许播放作弊语音
    # gui.clean()  # 清屏
    cfg.stage += 1  # 下一个流程


def hostloop(yoloall):
    # init web cam
    fps = 0
    writer_fps = 25  # 保存帧率
    writeVideo_flag = False  # Save video flag
    video_capture = cv2.VideoCapture(0)
    # video_capture = cv2.VideoCapture(1)  # usb cam
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    w = int(video_capture.get(3))
    h = int(video_capture.get(4))
    print('Camera resolution:', (w, h))

    # 存储
    if writeVideo_flag:
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter('./output/output.avi', fourcc, writer_fps, (w, h))

    """main loop"""
    while True:
        # stream
        ret, frame = video_capture.read()
        frame = cv2.flip(frame, 180)  # 图像翻转，确定与真实方向一致
        if ret is not True:
            break
        t1 = time.time()  # for fps put text
        image = Image.fromarray(frame[..., ::-1])  # bgr to rgb 仅yolo使用

        """detector res"""
        boxs, confidence, class_names = yoloall.detect_image(image)

        """translator处理预测结果"""
        boxs_xyxy = translate.xywh2xyxy(boxs)  # 转换坐标
        translator.arrange_person(boxs_xyxy, confidence, class_names)  # person排列和过滤
        translator.assign_object2person(boxs_xyxy, confidence, class_names)  # hand和eye关联和过滤
        translator.voting()  # 稳定输出结果

        """
        单设备不需要
        socket 接收和发送结果 主机：
        发送：cfg -> GUI 显示结果, 游戏流程
        接受：translator 结果 {id：{hand,hand.eye}}
        """
        if cfg.num_devices == 1:
            pass
        else:
            translator_slave = lan_host.receive()  # 接受从机translator结果

        """processor集成所有结果"""
        if cfg.num_devices == 1:  # 单机结果
            processor.get_hand(translator.id_hand_status, 0)  # 将双手结果相加，thumbs只取左手或一只手的结果, 不拼接
            processor.concat_eyes(translator.id_eye_status, 0)  # 将眼睛结果传递, 不拼接
        else:  # 拼接
            processor.get_hand(translator.id_hand_status,
                               translator_slave.id_hand_status)  # 将双手结果相加，thumbs只取左手或一只手的结果, 拼接从机结果
            processor.concat_eyes(translator.id_eye_status, translator_slave.id_eye_status)  # 拼接从机结果

        # print(translator.id_hand_status)
        # print(translator_slave.id_hand_status)
        # print(processor.get_hand(translator.id_hand_status,translator_slave.id_hand_status))
        """lan2lan 接收和发送结果(发送translator结果)，单设备不需要"""

        if cfg.num_devices == 1:  # 单机结果
            pass
        else:  # 发送给从机
            send_data = {'stage': cfg.stage,
                         'flag_jump': cfg.flag_jump,
                         'assign_id': cfg.assign_id,
                         'assign_ch': type(
                             game.players[cfg.assign_id]).__name__ if cfg.assign_id <= cfg.num_players else "",
                         # assign ch不能大于人数
                         'countdown_pro': cfg.countdown_pro,
                         'gui_clean': cfg.flag_audio_start,
                         'werewolf_voting': str(processor.get_voting_digit(game.spec_id['Werewolf'])),
                         'confirm_pro': cfg.confirm_pro,
                         'flag_confirm': cfg.flag_confirm,
                         'seer_voting': str(processor.get_voting_digit(game.spec_id['Seer'])),
                         'seer_res': game.movement_seer(processor.get_voting_digit(game.spec_id['Seer'])) if (
                                                                                                                     processor.get_voting_digit(
                                                                                                                         game.spec_id[
                                                                                                                             'Seer']) <= cfg.num_players and cfg.confirm_pro >= cfg.comfirm_thres) or (
                                                                                                                     processor.get_voting_digit(
                                                                                                                         game.spec_id[
                                                                                                                             'Seer']) <= cfg.num_players and cfg.countdown_pro <= 0) else 2,
                         'kill_id': game.progress[cfg.day][0],
                         'witch_thumb': processor.get_thumbs(game.spec_id['Witch']),
                         'witch_digit': str(processor.get_voting_digit(game.spec_id['Witch'])),
                         'day': cfg.day,
                         'annouce_killed': game.announce_night(cfg.day)[0],
                         'annouce_poisoned': game.announce_night(cfg.day)[1],
                         'status_list': game.get_status_list(),
                         'voting_day': processor.voting_day(game.get_alive_idlist()),
                         'voting_hunter': str(processor.get_voting_digit(game.spec_id['Hunter'])),
                         'gameover': game.is_gameover(game.get_character_list()),
                         'end_game_list': game.get_status_list(),
                         'end_game_progress': game.progress,
                         }
            lan_host.send(send_data)

        """游戏流程"""
        if cfg.stage == 0:  # 0.赋予角色流程
            if cfg.flag_audio_background is True:  # 播放背景音频
                au_background.play_aud_dirc('bgm')
                cfg.flag_audio_background = False
            if cfg.flag_audio_start is True:
                time.sleep(3)  # 两个玩家之间等待一点时间
                au.play_aud_merge(str(cfg.assign_id), 'assign_open')  # 11:睁眼, 玩家id-1
                cfg.flag_audio_start = False

            processor.canopen_list = [cfg.assign_id]  # 被赋予角色的玩家可以睁眼
            if processor.check_cheat() == 0:  # 无人作弊
                gui.assign(str(cfg.assign_id), type(game.players[cfg.assign_id]).__name__, t=cfg.countdown_pro)
                app.processEvents()
                # 倒计时
                if cfg.countdown_pro > 0:
                    cfg.countdown_pro -= cfg.countdown_rate
                elif cfg.countdown_pro <= 0:  # 倒计时结束, 下一个玩家

                    cfg.countdown_pro = cfg.countdown_thres  # 重置倒计时
                    gui.clean()  # 清空页面
                    au.play_aud_merge(str(cfg.assign_id), 'assign_close')  # 播放语音
                    cfg.assign_id += 1  # 更新id
                    cfg.flag_audio_start = True  # 允许播放开始语音

                    if cfg.assign_id > cfg.num_players:  # 角色赋予流程结束，进行下一个步骤,更新页面跳转flag, 更新audio
                        time.sleep(5)  # 流程
                        reset_flag()
            elif processor.check_cheat() != 0:  # 有人睁眼
                # 加：提示页面和提示语音,如何加标志位更新??
                if cfg.flag_audio_cheat is True:
                    # 播放音频
                    # 清屏
                    au.play_aud_dirc('cheat')
                    gui.clean()
                    cfg.flag_audio_cheat = False
                pass

        elif cfg.stage == 1:  # 1.晚上：狼人行动
            if cfg.flag_jump is True:  # 跳转页面
                au_background.play_aud_dirc('bgm')
                au_background.player.setVolume(30)  # 背景乐开始播放
                gui.jump_werewolf()
                app.processEvents()
                cfg.flag_jump = False
            if cfg.flag_audio_start is True:  # 播放狼人开始提示音
                au.play_aud_dirc('werewolves_open')
                cfg.flag_audio_start = False

            processor.canopen_list = game.spec_id['Werewolf']  # 狼人可以睁眼
            if processor.check_cheat() == 0:  # 无人作弊
                """更新 or 锁定"""
                if cfg.flag_confirm is False:  # 玩家尚未确认, 更新页面
                    gui.update_werewolf(str(processor.get_voting_digit(game.spec_id['Werewolf'])),
                                        cfg.confirm_pro, cfg.countdown_pro, cfg.flag_confirm)
                    app.processEvents()

                    # 累积手势
                    processor.add_posture(processor.get_voting_digit(game.spec_id['Werewolf']))  # 添加当前帧结果
                    if processor.accumulate_pro() is True:  # 与上一帧比较相同
                        cfg.confirm_pro += cfg.comfirm_rate
                    else:
                        cfg.confirm_pro = 0  # 清空累积
                    # 倒计时
                    if cfg.countdown_pro > 0:
                        cfg.countdown_pro -= cfg.countdown_rate
                else:  # 锁定：保证流程走完再结束
                    gui.update_werewolf(str(processor.get_voting_digit(game.spec_id['Werewolf'])),
                                        cfg.confirm_pro, cfg.countdown_pro, cfg.flag_confirm)  # 锁定,只更新倒计时
                    app.processEvents()
                    if cfg.countdown_pro > 0:
                        cfg.countdown_pro -= cfg.countdown_rate

                """确认条件"""
                # 1.累积确认
                if cfg.confirm_pro >= cfg.comfirm_thres and cfg.flag_confirm is False:  # 确认杀人
                    if processor.get_voting_digit(game.spec_id['Werewolf']) <= cfg.num_players:  # 狼人要杀的人在玩家里面
                        game.movement_werewolf(cfg.day,
                                               killed_id=processor.get_voting_digit(game.spec_id['Werewolf']))  # 更新游戏逻辑
                        cfg.flag_confirm = True  # 继续倒计时
                    else:  # 没有杀人
                        gui.update_werewolf(str(0), cfg.confirm_pro, cfg.countdown_pro, cfg.flag_confirm)
                        app.processEvents()
                        game.movement_werewolf(cfg.day, killed_id=0)  # 更新游戏逻辑
                        cfg.flag_confirm = True  # 继续倒计时
                # 2.倒计时结束
                elif cfg.countdown_pro <= 0 and cfg.flag_confirm is False:  # 倒计时结束, 玩家尚未确认，取最后一帧的结果
                    if processor.get_voting_digit(game.spec_id['Werewolf']) <= cfg.num_players:  # 狼人要杀的人在玩家里面
                        game.movement_werewolf(cfg.day,
                                               killed_id=processor.get_voting_digit(game.spec_id['Werewolf']))  # 更新游戏逻辑
                        au.play_aud_dirc('werewolves_close')
                        reset_flag()
                    else:  # 没有杀人
                        gui.update_werewolf(str(0), cfg.confirm_pro, cfg.countdown_pro, cfg.flag_confirm)
                        app.processEvents()
                        game.movement_werewolf(cfg.day, killed_id=0)
                        au.play_aud_dirc('werewolves_close')
                        reset_flag()
                elif cfg.countdown_pro <= 0 and cfg.flag_confirm is True:  # 倒计时结束, 玩家确认
                    au.play_aud_dirc('werewolves_close')
                    reset_flag()
                else:
                    pass  # 继续循环
            elif processor.check_cheat() != 0:  # 有人睁眼
                # 加：提示页面和提示语音
                print('有人作弊！', processor.check_cheat())
                pass

        elif cfg.stage == 2:  # 2.晚上：预言家行动
            if cfg.flag_jump is True:  # 跳转页面
                gui.jump_seer()
                app.processEvents()
                cfg.flag_jump = False
            if cfg.flag_audio_start is True:  # 预言家睁眼提示音
                time.sleep(6)  # 等待上一段音频播放完成
                au.play_aud_dirc('seer_open')
                time.sleep(3)  # 等待语音播放一点
                cfg.flag_audio_start = False

            processor.canopen_list = game.spec_id['Seer']  # 预言家可以睁眼
            if processor.check_cheat() == 0:  # 无人作弊
                """更新 or 锁定"""
                if cfg.flag_confirm is False:  # 更新
                    gui.update_seer(str(processor.get_voting_digit(game.spec_id['Seer'])), 2, cfg.confirm_pro,
                                    cfg.countdown_pro, cfg.flag_confirm)  # 直到预言家确认才能给出验人状态
                    app.processEvents()

                    # 累积手势
                    processor.add_posture(processor.get_voting_digit(game.spec_id['Seer']))  # 添加当前帧结果
                    if processor.accumulate_pro() is True:  # 与上一帧比较相同
                        cfg.confirm_pro += cfg.comfirm_rate
                    else:
                        cfg.confirm_pro = 0  # 清空累积
                    # 倒计时
                    if cfg.countdown_pro > 0:
                        cfg.countdown_pro -= cfg.countdown_rate
                else:  # 锁定,冻结页面，预言家看到结果
                    gui.update_seer(str(processor.get_voting_digit(game.spec_id['Seer'])),
                                    game.movement_seer(processor.get_voting_digit(game.spec_id['Seer'])),
                                    cfg.confirm_pro,
                                    cfg.countdown_pro, cfg.flag_confirm)
                    app.processEvents()
                    # 倒计时
                    if cfg.countdown_pro > 0:
                        cfg.countdown_pro -= cfg.countdown_rate

                """确认条件"""
                # 1.累积确认
                if cfg.confirm_pro >= cfg.comfirm_thres and cfg.flag_confirm is False:  # 告诉预言家结果
                    if processor.get_voting_digit(game.spec_id['Seer']) <= cfg.num_players:  # 预言家验人结果再游戏玩家里面
                        gui.update_seer(str(processor.get_voting_digit(game.spec_id['Seer'])),
                                        game.movement_seer(processor.get_voting_digit(game.spec_id['Seer'])),
                                        cfg.confirm_pro,
                                        cfg.countdown_pro, cfg.flag_confirm)
                        app.processEvents()
                        cfg.flag_confirm = True  # 继续倒计时
                    else:  # 否则不验人
                        gui.update_seer(str(processor.get_voting_digit(game.spec_id['Seer'])),
                                        game.movement_seer(0), cfg.confirm_pro, cfg.countdown_pro,
                                        cfg.flag_confirm)  # 预测超过游戏id则不确定
                        app.processEvents()
                        cfg.flag_confirm = True  # 继续倒计时
                # 2.倒计时结束
                elif cfg.countdown_pro <= 0 and cfg.flag_confirm is False:  # 倒计时结束, 玩家尚未确认，取最后一帧的结果
                    if processor.get_voting_digit(game.spec_id['Seer']) <= cfg.num_players:  # 预言家验人结果再游戏玩家里面
                        gui.update_seer(str(processor.get_voting_digit(game.spec_id['Seer'])),
                                        game.movement_seer(processor.get_voting_digit(game.spec_id['Seer'])),
                                        cfg.confirm_pro,
                                        cfg.countdown_pro, cfg.flag_confirm)
                        app.processEvents()
                        au.play_aud_dirc('seer_close')
                        reset_flag()
                    else:  # 否则不验人
                        gui.update_seer(str(processor.get_voting_digit(game.spec_id['Seer'])),
                                        game.movement_seer(0), cfg.confirm_pro, cfg.countdown_pro,
                                        cfg.flag_confirm)  # 预测超过游戏id则不确定
                        app.processEvents()
                        au.play_aud_dirc('seer_close')
                        reset_flag()
                elif cfg.countdown_pro <= 0 and cfg.flag_confirm is True:  # 倒计时结束, 玩家确认
                    au.play_aud_dirc('seer_close')
                    reset_flag()
                else:
                    pass  # 跳出循环
            elif processor.check_cheat() != 0:  # 有人睁眼
                # 加：提示页面和提示语音
                print('有人作弊！', processor.check_cheat())
                pass

        elif cfg.stage == 3:  # 3.晚上:女巫救人
            if cfg.flag_jump is True:  # 跳转页面
                time.sleep(4)  # 等待预言家播放完音频
                gui.jump_witch_save()
                app.processEvents()
                cfg.flag_jump = False
            if cfg.flag_audio_start is True:
                # au_background.play_aud_dirc('bgm') # 再次播放背景音频
                au.play_aud_dirc('witch_save_open')
                cfg.flag_audio_start = False

            processor.canopen_list = game.spec_id['Witch']  # 女巫可以睁眼
            if processor.check_cheat() == 0:  # 无人作弊
                """更新 or 锁定"""
                if cfg.flag_confirm is False:  # 玩家尚未确认, 更新页面
                    gui.witch_save(game.progress[cfg.day][0], processor.get_thumbs(game.spec_id['Witch']),
                                   cfg.confirm_pro,
                                   cfg.countdown_pro, cfg.flag_confirm)
                    app.processEvents()

                    # 累积手势
                    processor.add_posture(processor.get_thumbs(game.spec_id['Witch']))  # 添加当前帧结果
                    if processor.accumulate_pro() is True:  # 与上一帧比较相同
                        cfg.confirm_pro += cfg.comfirm_rate
                    else:
                        cfg.confirm_pro = 0  # 清空累积
                    if cfg.countdown_pro > 0:  # 倒计时
                        cfg.countdown_pro -= cfg.countdown_rate
                else:  # 锁定：保证流程走完再结束
                    gui.witch_save(game.progress[cfg.day][0], processor.get_thumbs(game.spec_id['Witch']),
                                   cfg.confirm_pro,
                                   cfg.countdown_pro, cfg.flag_confirm)
                    app.processEvents()
                    if cfg.countdown_pro > 0:
                        cfg.countdown_pro -= cfg.countdown_rate

                """确认条件"""
                # 1.累积确认
                if cfg.confirm_pro >= cfg.comfirm_thres and cfg.flag_confirm is False:  # 确认杀人
                    gui.witch_save(game.progress[cfg.day][0], processor.get_thumbs(game.spec_id['Witch']),
                                   cfg.confirm_pro,
                                   cfg.countdown_pro, cfg.flag_confirm)
                    app.processEvents()
                    if processor.get_thumbs(game.spec_id['Witch']) == 2:  # 救人
                        game.movement_witch_save(cfg.day, 1)
                    else:  # 不确定或反对为不救人
                        game.movement_witch_save(cfg.day, 0)  # 不救人
                    cfg.flag_confirm = True  # 继续倒计时
                # 2.倒计时结束
                elif cfg.countdown_pro <= 0 and cfg.flag_confirm is False:  # 倒计时结束, 玩家尚未确认，取最后一帧的结果
                    # 冻结最后的结果
                    gui.witch_save(game.progress[cfg.day][0], processor.get_thumbs(game.spec_id['Witch']),
                                   cfg.confirm_pro,
                                   cfg.countdown_pro, cfg.flag_confirm)
                    app.processEvents()
                    if processor.get_thumbs(game.spec_id['Witch']) == 2:  # 救人
                        game.movement_witch_save(cfg.day, 1)
                    else:  # 不确定或反对为不救人
                        game.movement_witch_save(cfg.day, 0)  # 不救人
                    reset_flag()
                elif cfg.countdown_pro <= 0 and cfg.flag_confirm is True:  # 倒计时结束, 玩家确认
                    reset_flag()
                else:
                    pass
            elif processor.check_cheat() != 0:  # 有人睁眼
                # 加：提示页面和提示语音
                print('有人作弊！', processor.check_cheat())
                pass

        elif cfg.stage == 4:  # 4.晚上：女巫毒人
            if cfg.flag_jump is True:  # 跳转页面
                gui.jump_witch_poison()
                cfg.flag_jump = False
            if cfg.flag_audio_start is True:
                au.play_aud_dirc('witch_poison_open')
                cfg.flag_audio_start = False

            processor.canopen_list = game.spec_id['Witch']  # 女巫可以睁眼
            if processor.check_cheat() == 0:  # 无人作弊
                """更新 or 锁定"""
                if cfg.flag_confirm is False:  # 玩家尚未确认, 更新页面
                    gui.witch_poison(str(processor.get_voting_digit(game.spec_id['Witch'])), cfg.confirm_pro,
                                     cfg.countdown_pro, cfg.flag_confirm)
                    app.processEvents()

                    # 累积手势
                    processor.add_posture(processor.get_voting_digit(game.spec_id['Witch']))  # 添加当前帧结果
                    if processor.accumulate_pro() is True:  # 与上一帧比较相同
                        cfg.confirm_pro += cfg.comfirm_rate
                    else:
                        cfg.confirm_pro = 0  # 清空累积
                    if cfg.countdown_pro > 0:  # 倒计时
                        cfg.countdown_pro -= cfg.countdown_rate
                else:  # 锁定：保证流程走完再结束
                    gui.witch_poison(str(processor.get_voting_digit(game.spec_id['Witch'])), cfg.confirm_pro,
                                     cfg.countdown_pro, cfg.flag_confirm)
                    app.processEvents()
                    if cfg.countdown_pro > 0:
                        cfg.countdown_pro -= cfg.countdown_rate

                """确认条件"""
                # 1.累积确认
                if cfg.confirm_pro >= cfg.comfirm_thres and cfg.flag_confirm is False:  # 确认毒人
                    if processor.get_voting_digit(game.spec_id['Witch']) <= cfg.num_players:  # 女巫要毒的人在玩家里面
                        game.movement_witch_poison(cfg.day, processor.get_voting_digit(game.spec_id['Witch']))  # 更新游戏逻辑
                        cfg.flag_confirm = True  # 继续倒计时
                    else:  # 没有毒人
                        gui.witch_poison(str(0), cfg.confirm_pro, cfg.countdown_pro)
                        app.processEvents()
                        game.movement_witch_poison(cfg.day, 0)  # 不毒人
                        cfg.flag_confirm = True  # 继续倒计时
                # 2.倒计时结束
                elif cfg.countdown_pro <= 0 and cfg.flag_confirm is False:  # 倒计时结束, 玩家尚未确认，取最后一帧的结果
                    if processor.get_voting_digit(game.spec_id['Witch']) <= cfg.num_players:  # 女巫要毒的人在玩家里面
                        game.movement_witch_poison(cfg.day, processor.get_voting_digit(game.spec_id['Witch']))  # 更新游戏逻辑
                        au.play_aud_dirc('witch_close')
                        reset_flag()
                    else:  # 没有毒人
                        gui.witch_poison(str(0), cfg.confirm_pro, cfg.countdown_pro, cfg.flag_confirm)
                        app.processEvents()
                        game.movement_witch_poison(cfg.day, 0)  # 不毒人
                        au.play_aud_dirc('witch_close')
                        reset_flag()
                elif cfg.countdown_pro <= 0 and cfg.flag_confirm is True:  # 倒计时结束, 玩家确认
                    au.play_aud_dirc('witch_close')
                    reset_flag()
                else:
                    pass
            elif processor.check_cheat() != 0:  # 有人睁眼
                # 加：提示页面和提示语音
                print('有人作弊！', processor.check_cheat())
                pass

        elif cfg.stage == 5:  # 5.天亮，宣布死讯
            if cfg.flag_jump is True:  # 跳转页面
                gui.jump_announce_night()
                app.processEvents()
                cfg.flag_jump = False
            """宣布死讯"""  # 更新睁眼列表？不需要作弊检测
            # 播放音频
            if cfg.flag_audio_start is True:
                time.sleep(3)
                if game.announce_night(cfg.day)[0] == 0 and game.announce_night(cfg.day)[1] == 0:  # 平安夜
                    au.play_aud_dirc('report_nodied')
                elif game.announce_night(cfg.day)[0] == game.spec_id['Hunter'][0]:  # 猎人被杀
                    au.play_aud_dirc('report_hunterdied')
                else:  # 有人被杀
                    au.play_aud_dirc('report_somedied')
                cfg.flag_audio_start = False

            gui.announce_night(cfg.day, game.announce_night(cfg.day)[0], game.announce_night(cfg.day)[1])
            app.processEvents()
            time.sleep(10)  # 等待玩家看结果

            """判断游戏流程"""
            if game.announce_night(cfg.day)[0] == game.spec_id['Hunter'][0] and game.spec_id['Hunter'][
                0] != 0:  # 首先判断猎人有没有被杀 + 板子里面有猎人
                reset_flag()
                cfg.stage = 8  # 跳转到猎人
            elif game.is_gameover(game.get_character_list()) == 0:  # 游戏继续
                reset_flag()
            else:  # 游戏结束
                reset_flag()
                cfg.stage = 9

        elif cfg.stage == 6:  # 6.天亮：讨论
            if cfg.flag_jump is True:  # 跳转页面
                gui.jump_status()
                app.processEvents()
                cfg.flag_jump = False
            if cfg.flag_audio_start is True:
                au.play_aud_dirc('discussion')
                au_background.player.setVolume(0)  # 关闭背景乐
                cfg.flag_audio_start = False

            gui.status(game.get_status_list())  # 更新玩家状态表
            app.processEvents()
            """判断所有人的大拇指, 所有人大拇指向上则开始voting流程"""
            # 累积手势
            if processor.get_thumbs(game.get_alive_idlist()) == 2:  # 大部分人比大拇指
                cfg.confirm_pro += cfg.comfirm_rate
            else:
                cfg.confirm_pro = 0  # 清空累积

            """确认条件"""
            # 1.累积确认
            if cfg.confirm_pro >= cfg.comfirm_thres:  # 确认开始投票
                reset_flag()  # 下一个流程

        elif cfg.stage == 7:  # 7.天亮：投票
            if cfg.flag_jump is True:  # 跳转页面
                gui.jump_vote()
                app.processEvents()
                cfg.flag_jump = False
            if cfg.flag_audio_start is True:
                au.play_aud_dirc('vote')
                time.sleep(5)
                cfg.flag_audio_start = False

            """开始投票"""
            gui.vote(processor.voting_day(game.get_alive_idlist()), cfg.confirm_pro, cfg.countdown_pro)
            app.processEvents()

            # 累积手势
            processor.add_posture(processor.voting_day(game.get_alive_idlist()))  # 添加当前帧结果
            if processor.accumulate_pro() is True:  # 与上一帧比较相同
                cfg.confirm_pro += cfg.comfirm_rate
            else:
                cfg.confirm_pro = 0  # 清空累积
            # 倒计时
            if cfg.countdown_pro > 0:
                cfg.countdown_pro -= cfg.countdown_rate

            """确认条件"""
            # 1.累积确认 2.倒计时结束
            if cfg.confirm_pro >= cfg.comfirm_thres or cfg.countdown_pro <= 0:  # 确认投票
                if cfg.num_players >= processor.voting_day(game.get_alive_idlist()) >= 0:  # 要投的人在玩家里面 + 没有平票
                    game.voting(cfg.day, processor.voting_day(game.get_alive_idlist()))  # 更新游戏逻辑
                    if game.is_gameover(game.get_character_list()) == 0:  # 游戏继续
                        if processor.voting_day(game.get_alive_idlist()) == game.spec_id['Hunter'][0]:  # 猎人被投
                            reset_flag()
                            cfg.stage = 8  # 进入猎人流程
                        else:
                            au.play_aud_dirc('dark_close')  # 准备进入晚上
                            reset_flag()
                            cfg.stage = 1
                            cfg.day += 1
                            time.sleep(7)
                    else:  # 游戏结束
                        reset_flag()
                        cfg.stage = 9
                elif processor.voting_day(game.get_alive_idlist()) == -1:  # 有人平票
                    au.play_aud_dirc('vote_equal')
                    reset_flag()
                    cfg.stage = 7  # 重新投票
                    time.sleep(7)
            else:
                pass

        elif cfg.stage == 8:  # 8 特殊: 猎人开枪
            if cfg.flag_jump is True:  # 跳转页面
                gui.jump_hunter()
                app.processEvents()
                cfg.flag_jump = False
            if cfg.flag_audio_start is True:
                au.play_aud_dirc('hunter_open')
                time.sleep(3)
                cfg.flag_audio_start = False

            """更新"""
            gui.hunter(str(processor.get_voting_digit(game.spec_id['Hunter'])), cfg.confirm_pro, cfg.countdown_pro)
            app.processEvents()

            # 累积手势
            processor.add_posture(processor.get_voting_digit(game.spec_id['Hunter']))  # 添加当前帧结果
            if processor.accumulate_pro() is True:  # 与上一帧比较相同
                cfg.confirm_pro += cfg.comfirm_rate
            else:
                cfg.confirm_pro = 0  # 清空累积
            # 倒计时
            if cfg.countdown_pro > 0:
                cfg.countdown_pro -= cfg.countdown_rate

            """确认条件"""
            if cfg.confirm_pro >= cfg.comfirm_thres or cfg.countdown_pro <= 0:  # 确认开枪
                if cfg.num_players >= processor.voting_day(game.get_alive_idlist()):  # 要开枪的人在玩家里
                    game.movement_hunter(processor.get_voting_digit(game.spec_id['Hunter']))  # 更新游戏逻辑: 猎人开枪，0为不开枪
                    au.play_aud_dirc('hunter_end')
                    time.sleep(3)
                    if game.is_gameover(game.get_character_list()) == 0:  # 游戏继续
                        if game.players[game.spec_id['Hunter'][0]].status == 'killed':  # 猎人被杀
                            reset_flag()
                            cfg.stage = 6  # 白天讨论
                            time.sleep(1)
                        elif game.players[game.spec_id['Hunter'][0]].status == 'voted':  # 猎人被投票出局
                            au.play_aud_dirc('dark_close')  # 准备进入晚上
                            reset_flag()
                            cfg.stage = 1
                            cfg.day += 1
                            cfg.flag_audio_background = True  # 继续播放背景乐
                            time.sleep(7)
                        else:
                            print('error: 猎人还魂了！')
                            break
                    else:  # 游戏结束
                        reset_flag()
                        cfg.stage = 9
                else:
                    reset_flag()
                    cfg.stage = 6  # 白天讨论
                    time.sleep(1)
            else:
                pass

        elif cfg.stage == 9:  # 9. 结束：游戏结束
            if cfg.flag_jump is True:  # 跳转页面
                if game.is_gameover(game.get_character_list()) == 1:  # 好人获胜
                    gui.jump_gameover(1)
                elif game.is_gameover(game.get_character_list()) == 2:  # 坏人获胜
                    gui.jump_gameover(2)
                else:
                    print('error: 一个不存在的人获得了胜利')
                app.processEvents()
                cfg.flag_jump = False
            if cfg.flag_audio_start is True:
                if game.is_gameover(game.get_character_list()) == 1:  # 好人获胜
                    au.play_aud_dirc('villager_win')
                elif game.is_gameover(game.get_character_list()) == 2:  # 坏人获胜
                    au.play_aud_dirc('werewolf_win')
                else:
                    print('error: 一个不存在的人获得了胜利')
                cfg.flag_audio_start = False

            time.sleep(10)
            cfg.stage = -1

        elif cfg.stage == -1:  # 游戏结束：跳出程序
            if cfg.flag_audio_start is True:
                au.play_aud_dirc('thank')
                time.sleep(11)
                cfg.flag_audio_start = False
            print('alive list: ', game.get_status_list())
            print('this is the game progress{day: [killed_id, poisoned_id, flag_save,]:', game.progress)
            print('Thank you for playing our game!')
            break

        """GUI 刷新"""
        app.processEvents()  # GUI刷新

        # test visual img
        new_frame = yoloall.vis(frame, boxs, confidence, class_names)

        # 存储
        if writeVideo_flag:
            out.write(frame)

        """测试用：预测结果可视化输出"""
        fps = (fps + (1. / (time.time() - t1))) / 2
        cv2.putText(new_frame, "FPS: %f" % (fps), (int(20), int(40)), 0, 5e-3 * 200, (145, 145, 145), 2)
        cv2.namedWindow("YOLO4_Deep_SORT", 0)
        # cv2.resizeWindow('YOLO4_Deep_SORT', 1024, 768)
        cv2.resizeWindow('YOLO4_Deep_SORT', w, h)
        cv2.imshow('YOLO4_Deep_SORT', new_frame)

        # Press Q to stop!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # exit system
    if writeVideo_flag:
        out.release()
    cv2.destroyAllWindows()
    video_capture.release()


def slaveloop(yoloall):
    """从机的循环"""
    # init web cam
    fps = 0
    writer_fps = 25  # 保存帧率
    writeVideo_flag = False  # Save video flag
    video_capture = cv2.VideoCapture(0)
    # video_capture = cv2.VideoCapture(1)  # usb cam
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    w = int(video_capture.get(3))
    h = int(video_capture.get(4))
    print('Camera resolution:', (w, h))

    # 存储
    if writeVideo_flag:
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter('./output/output.avi', fourcc, writer_fps, (w, h))

    """main loop"""
    while True:
        # stream
        ret, frame = video_capture.read()
        frame = cv2.flip(frame, 180)  # 图像翻转，确定与真实方向一致
        if ret is not True:
            break
        t1 = time.time()  # for fps put text
        image = Image.fromarray(frame[..., ::-1])  # bgr to rgb 仅yolo使用

        """detector res"""
        boxs, confidence, class_names = yoloall.detect_image(image)

        """translator处理预测结果"""
        boxs_xyxy = translate.xywh2xyxy(boxs)  # 转换坐标
        translator.arrange_person(boxs_xyxy, confidence, class_names)  # person排列和过滤
        translator.assign_object2person(boxs_xyxy, confidence, class_names)  # hand和eye关联和过滤
        translator.voting()  # 稳定输出结果
        # print('translator.id_hand_status: ', translator.id_hand_status)
        # print('translator.id_eye_status: ', translator.id_eye_status)

        """
        socket 接收和发送结果 从机：
        发送：translator 结果 {id：{hand,hand.eye}}
        接受：cfg -> GUI [0]显示结果,[1]游戏逻辑变量 [2]processor结果
        """
        lan_slave.send(translator)
        receive = lan_slave.receive()

        """processor集成所有结果,从机不需要"""
        """游戏流程"""
        if receive['stage'] == 0:  # 0.赋予角色流程
            if receive['flag_jump'] is True:  # 跳转页面
                gui.stackedWidget.setCurrentIndex(4)
                app.processEvents()
            if receive['gui_clean'] is True:  # 清屏
                gui.clean()
                time.sleep(3)
            gui.assign(str(receive['assign_id']), receive['assign_ch'],
                       receive['countdown_pro'])
            app.processEvents()


        elif receive['stage'] == 1:  # 1.晚上：狼人行动
            if receive['flag_jump'] is True:  # 跳转页面
                gui.jump_werewolf()
                app.processEvents()
            gui.update_werewolf(receive['werewolf_voting'], receive['confirm_pro'], receive['countdown_pro'],
                                receive['flag_confirm'])
            app.processEvents()


        elif receive['stage'] == 2:  # 2.晚上：预言家行动
            if receive['flag_jump'] is True:  # 跳转页面
                gui.jump_seer()
                app.processEvents()

            gui.update_seer(receive['seer_voting'], receive['seer_res'], receive['confirm_pro'],
                            receive['countdown_pro'],
                            receive['flag_confirm'])  # 直到预言家确认才能给出验人状态
            app.processEvents()


        elif receive['stage'] == 3:  # 3.晚上:女巫救人
            if receive['flag_jump'] is True:  # 跳转页面
                time.sleep(3)
                gui.jump_witch_save()
                app.processEvents()
            gui.witch_save(receive['kill_id'], receive['witch_thumb'], receive['confirm_pro'], receive['countdown_pro'],
                           receive['flag_confirm'])
            app.processEvents()


        elif receive['stage'] == 4:  # 4.晚上：女巫毒人
            if receive['flag_jump'] is True:  # 跳转页面
                gui.jump_witch_poison()
                app.processEvents()
            gui.witch_poison(receive['witch_digit'], receive['confirm_pro'], receive['countdown_pro'],
                             receive['flag_confirm'])
            app.processEvents()

        elif receive['stage'] == 5:  # 5.天亮，宣布死讯
            if receive['flag_jump'] is True:  # 跳转页面
                gui.jump_announce_night()
                app.processEvents()
            gui.announce_night(receive['day'], receive['annouce_killed'], receive['annouce_poisoned'])
            app.processEvents()


        elif receive['stage'] == 6:  # 6.天亮：讨论
            if receive['flag_jump'] is True:  # 跳转页面
                gui.jump_status()
                app.processEvents()
            gui.status(receive['status_list'])  # 更新玩家状态表
            app.processEvents()

        elif receive['stage'] == 7:  # 7.天亮：投票
            if receive['flag_jump'] is True:  # 跳转页面
                gui.jump_vote()
                app.processEvents()
            gui.vote(receive['voting_day'], receive['confirm_pro'], receive['countdown_pro'])
            app.processEvents()


        elif receive['stage'] == 8:  # 8 特殊: 猎人开枪
            if receive['flag_jump'] is True:  # 跳转页面
                gui.jump_hunter()
                app.processEvents()
            gui.hunter(receive['voting_hunter'], receive['confirm_pro'], receive['countdown_pro'])
            app.processEvents()

        elif receive['stage'] == 9:  # 9. 结束：游戏结束
            if receive['flag_jump'] is True:  # 跳转页面
                if receive['gameover'] == 1:  # 好人获胜
                    gui.jump_gameover(1)
                elif receive['gameover'] == 2:  # 坏人获胜
                    gui.jump_gameover(2)
                else:
                    print('error: 一个不存在的人获得了胜利')
                app.processEvents()
                time.sleep(5)
        elif receive['stage'] == -1:  # 游戏结束：跳出程序
            print('alive list: ', receive['end_game_list'])
            print('this is the game progress{day: [killed_id, poisoned_id, flag_save,]:', receive['end_game_progress'])
            print('Thank you for playing our game!')
            break
        else:
            pass

        """GUI 刷新"""
        app.processEvents()  # GUI刷新

        # test visual img
        new_frame = yoloall.vis(frame, boxs, confidence, class_names)

        # 存储
        if writeVideo_flag:
            out.write(frame)

        """测试用：预测结果可视化输出"""
        fps = (fps + (1. / (time.time() - t1))) / 2
        cv2.putText(new_frame, "FPS: %f" % (fps), (int(20), int(40)), 0, 5e-3 * 200, (145, 145, 145), 2)
        cv2.namedWindow("YOLO4_Deep_SORT", 0)
        # cv2.resizeWindow('YOLO4_Deep_SORT', 1024, 768)
        cv2.resizeWindow('YOLO4_Deep_SORT', w, h)
        cv2.imshow('YOLO4_Deep_SORT', new_frame)

        # Press Q to stop!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # exit system
    if writeVideo_flag:
        out.release()
    cv2.destroyAllWindows()
    video_capture.release()


if __name__ == '__main__':
    """
    init system
    """
    # init detector
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    # session = InteractiveSession(config=config)
    session = Session(config=config)

    """init modules"""

    # init processor
    processor = process.Processor()

    # init game logic
    game = gamelogic.Game()

    # init gui
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    gui = ui.Ui_Form()
    gui.setupUi(Form)
    Form.show()

    """需要根据主机从机单机进行配置的实例"""
    # 游戏逻辑配置
    # game.start_game(cfg.num_players)
    # # init translator: 需要根据设备数量进行修改
    # translator = translate.Translator(start_id=2, num_player_indevice=cfg.num_players_indevice, voting_fps=cfg.qsize)

    """等待玩家配置主机从机"""
    while cfg.flag_config is False:
        app.processEvents()

    print('device_id: ', cfg.device_id)
    print('num_devices: ', cfg.num_devices)

    if cfg.num_devices == 1 or (cfg.num_devices == 2 and cfg.device_id == 0):  # 单机 or 主机
        """配置主机audio"""
        file_floder = './audio'
        file_path = os.listdir(file_floder)
        au = audio.Audio(100)
        au_background = audio.Audio(30)
        """配置主机的translator"""
        translator = translate.Translator(start_id=cfg.start_id, num_player_indevice=cfg.num_players_indevice,
                                          voting_fps=cfg.qsize)
        """配置主机的gamelogic"""
        game.start_game(cfg.num_players)

        """配置socket"""
        print("正在配置socket......")
        if cfg.num_devices == 1:  # 单机
            pass
        else:  # 联机
            lan_host = lan.Lan(0, cfg.host_ip, 7000)
            data_guires = pack.Broadcast()  # 打包GUI结果
            print('主机初始化成功！')

        hostloop(YOLOall())


    elif cfg.num_devices == 2 and cfg.device_id == 1:  # 1号从机
        """配置从机的translator"""
        translator = translate.Translator(start_id=cfg.start_id, num_player_indevice=cfg.num_players_indevice,
                                          voting_fps=cfg.qsize)
        """配置从机的socket"""
        lan_slave = lan.Lan(1, cfg.host_ip, 7000)
        slaveloop(YOLOall())
    else:
        print("error: 用户使用了未来才有的功能")

    # GUI 退出
    sys.exit(app.exec_())
