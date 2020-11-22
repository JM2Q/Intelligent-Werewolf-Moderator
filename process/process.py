from collections import Counter, deque

"""hard code"""
posture_digit = ('nohand', 'one', 'two', 'three', 'four', 'five')  # 使用索引大小翻译手势的含义
posture_thumb = ('nohand', 'thumbs-down', 'thumbs-up')  # 1反对/2同意
eye_label = ('closeeye', 'openeye')  # 使用索引代表眼睛


class Processor(object):
    def __init__(self):
        self.hand_digit = {}  # 集成结果 - {id: 手势对应的数字}
        self.hand_thumb = {}  # 集成结果 - {id: prosture_thumb索引}
        self.eyes = {}  # 集成结果 - {id: 眼睛索引}
        self.canopen_list = []  # 可以睁眼的id
        self.flag_assign = False  # flag-是否开始赋予角色
        self.accumulate_deque = deque(maxlen=3)  # 存储前后两帧手势用于比较
        print('################\n初始化processor成功\n################')

    # self.concat

    def concat_eyes(self, eye_status_host, eye_status_slave):
        """
        拼接不同device的translator结果
        1. 拼接不同设备的结果(目前仅支持两台)
        2. noeyes当做closeeye
        :param eye_status_host: from host translator
        :param eye_status_slave: from slave translator,0为没有结果
        :return:
        """

        for player_id, eye in eye_status_host.items():
            if eye == 'noeye':  # 没有检测到眼睛
                self.eyes[player_id] = 0  # 当做闭眼
            elif eye in eye_label:
                self.eyes[player_id] = eye_label.index(eye)

        if eye_status_slave == 0:  # 不拼接
            pass
        else:  # 拼接
            for player_id, eye in eye_status_slave.items():
                if eye == 'noeye':  # 没有检测到眼睛
                    self.eyes[player_id] = 0  # 当做闭眼
                elif eye in eye_label:
                    self.eyes[player_id] = eye_label.index(eye)
        # print('eye: ', self.eyes)

    def get_hand(self, id_hand_status_host, id_hand_status_slave):
        """
        将双手手势数字相加
        获取translator 大拇指结果
        :param id_hand_status_host: host translator 结果
        :param id_hand_status_slave: slave translator 结果, 0为不拼接
        """

        for player_id, hand_status in id_hand_status_host.items():
            if hand_status[0] in posture_digit and hand_status[1] in posture_digit:  # 双手都是数字手势
                self.hand_digit[player_id] = posture_digit.index(hand_status[0]) + posture_digit.index(
                    hand_status[1])
            elif hand_status[0] in posture_digit:  # 左手数字手势
                self.hand_digit[player_id] = posture_digit.index(hand_status[0])
            elif hand_status[1] in posture_digit:  # 右手数字手势
                self.hand_digit[player_id] = posture_digit.index(hand_status[1])
            else:  # 没有数字手势
                self.hand_digit[player_id] = 0

            if hand_status[0] in posture_thumb:  # 只取左手或一只手
                self.hand_thumb[player_id] = posture_thumb.index(hand_status[0])
            else:  # 没有则=no hand
                self.hand_thumb[player_id] = 0

        # 是否拼接
        if id_hand_status_slave == 0:
            pass
        else:
            for player_id, hand_status in id_hand_status_slave.items():
                if hand_status[0] in posture_digit and hand_status[1] in posture_digit:  # 双手都是数字手势
                    self.hand_digit[player_id] = posture_digit.index(hand_status[0]) + posture_digit.index(
                        hand_status[1])
                elif hand_status[0] in posture_digit:  # 左手数字手势
                    self.hand_digit[player_id] = posture_digit.index(hand_status[0])
                elif hand_status[1] in posture_digit:  # 右手数字手势
                    self.hand_digit[player_id] = posture_digit.index(hand_status[1])
                else:  # 没有数字手势
                    self.hand_digit[player_id] = 0

                if hand_status[0] in posture_thumb:  # 只取左手或一只手
                    self.hand_thumb[player_id] = posture_thumb.index(hand_status[0])
                else:  # 没有则=no hand
                    self.hand_thumb[player_id] = 0
        # print('hand_thumb: ', self.hand_thumb)
        # print('hang_digit: ', self.hand_digit)

    def get_thumbs(self, idlist):
        """
        获取对应索引的大拇指信息,如果是0返回不确定
        :param idlist: 是一个列表
        :return:
        """
        if len(idlist) == 1:
            if idlist[0] == 0:
                return 0
            else:
                # print('thumb: ', self.hand_thumb[idlist[0]])
                return self.hand_thumb[idlist[0]]
        else:
            voting = []
            for voting_id in idlist:  # 获取所有人的数字手势
                voting.append(self.hand_thumb[voting_id])
            return Counter(voting).most_common()[0][0]

    def add_posture(self, posture_index):
        """
        添加手势的索引编号到deque
        :param posture_index: 手势的索引编号
        """
        self.accumulate_deque.append(posture_index)

    def accumulate_pro(self):
        """
        是否确认累积
        :return:
        """
        if Counter(self.accumulate_deque).most_common(1)[0][0] == 0:  # 0不能算
            return False
        else:
            if Counter(self.accumulate_deque).most_common(1)[0][1] == self.accumulate_deque.maxlen:  # 所有帧的手势都相同
                return True
            else:
                return False

    def get_voting_digit(self, voting_idlist):
        """
        获取当前帧投票结果
        不可用作白天公投
        :param voting_idlist: 可投票人对应id表
        :return: int: voting digit:
        """
        if voting_idlist == [0]:  # 玩家不存在
            return 0  # 返回手势0
        # 加：平票的话
        else:
            voting = []
            for voting_id in voting_idlist:  # 获取所有人的数字手势
                voting.append(self.hand_digit[voting_id])
            if Counter(voting).most_common(1)[0][0] == 0 and Counter(voting).most_common(1)[0][1] == len(
                    voting):  # 所有人弃票
                voting_res = 0  # 不投票
            elif Counter(voting).most_common(1)[0][0] == 0 and Counter(voting).most_common(1)[0][1] < len(
                    voting):  # 大部分人弃票
                voting_res = Counter(voting).most_common(2)[1][0]  # 取第二高的
            else:
                voting_res = Counter(voting).most_common(1)[0][0]
            # print('voting res: ', voting)
            # print('return voting res: ', Counter(voting).most_common(1)[0][0])
        return voting_res

    def voting_day(self, voting_idlist):
        """
        获取白天投票结果
        :param voting_idlist:
        :return:
        """
        voting = []
        for voting_id in voting_idlist:  # 获取所有人的数字手势
            voting.append(self.hand_digit[voting_id])

        if len(Counter(voting).most_common()) == 1:  # 只有一个结果
            return Counter(voting).most_common()[0][0]  # 返回该结果
        elif len(Counter(voting).most_common()) == 2:  # 有两个结果
            if Counter(voting).most_common()[0][0] == 0:  # 第一个结果是0
                return Counter(voting).most_common()[1][0]  # 取第二个的
            elif Counter(voting).most_common()[0][1] == Counter(voting).most_common()[1][1]:  # 1,2结果相同
                return -1  # 重新投票
            else:
                return Counter(voting).most_common()[0][0]  # 取第一个结果
        else:  # 超过2个结果
            if Counter(voting).most_common()[0][0] == 0:  # 第一个结果是0
                if Counter(voting).most_common()[1][1] == Counter(voting).most_common()[2][1]:  # 2,3平票
                    return -1
                else:
                    return Counter(voting).most_common()[1][0]  # 返回第二个结果
            elif Counter(voting).most_common()[0][1] == Counter(voting).most_common()[1][1]:  # 1,2结果相同
                return -1  # 重新投票
            else:
                return Counter(voting).most_common()[0][0]  # 取第一个结果

    def confirm_thumb(self):
        pass

    def check_cheat(self):
        """
        作弊检测(仅支持单机)
        :param self.canopen_list: [0]为所有玩家都要闭眼, 否则传递可以睁眼的id列表 -> [id,id]
        :return: 0为游戏继续, 其他数字为不应该睁眼的玩家id
        """
        for player_id, eye in self.eyes.items():
            if eye == 0:  # 闭眼
                pass
            elif eye == 1:
                if player_id in self.canopen_list:  # 该玩家可以睁眼
                    pass
                elif player_id not in self.canopen_list:
                    # 测试输出
                    print('有人作弊!：', player_id, '号玩家')
                    return player_id
        return 0  # 游戏继续
