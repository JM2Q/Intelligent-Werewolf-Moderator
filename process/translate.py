import sys
from collections import deque, Counter

"""
hand / eye label 硬编码
"""
hand_labels = ['thumbs-up', 'thumbs-down', 'one', 'two', 'three', 'four', 'five']
eye_labels = ['openeye', 'closeeye']


def xywh2xyxy(boxs):
    """
    将嵌套列表的bounding box list 从xywh format 改成 xyxy format
    :param boxs: [[xywh],[],[]]
    :return: [[xyxy],[],[]]
    """
    xyxy = []
    for i in range(len(boxs)):
        temp = [0] * 4
        temp[0] = int(boxs[i][0])
        temp[1] = int(boxs[i][1])
        temp[2] = int(boxs[i][2] + boxs[i][0])
        temp[3] = int(boxs[i][3] + boxs[i][1])
        xyxy.append(temp)
    return xyxy


def xyxy2center_point(xyxy):
    """
    :param xyxy: [x_topleft, y_topleft, x_bottomright,y_bottomright]
    :return: [x_center, y_center]
    """
    return [(xyxy[0] + xyxy[2]) // 2, (xyxy[1] + xyxy[3]) // 2]


def manhattan_distance(xy1, xy2):
    """

    :param xy1:
    :param xy2:
    :return: xy1和xy2的曼哈顿距离
    """
    return abs(xy1[0] - xy2[0]) + abs(xy1[1] - xy2[1])


class Translator(object):
    def __init__(self, num_player_indevice, start_id,voting_fps):
        # self.id_range = None # id范围
        self.num_player_indevice = num_player_indevice  # 设备检测人数
        self.hand_constraint = 2  # 每个人有两只手
        self.eye_constraint = 1  # 每个人有一双眼睛
        self.persons = [[] for _ in range(num_player_indevice)]  # 从左到右的person边界框中心点坐标,
        # 稳定器
        self.id_hand_deque = {}
        self.id_eye_deque = {}
        # 初始化每个人的稳定器，编号从1开始
        for i in range(1, num_player_indevice + 1):
            self.id_hand_deque[i] = deque(maxlen=voting_fps)  # 长度为voting_fps
            self.id_eye_deque[i] = deque(maxlen=voting_fps)
        # 稳定输出存储器
        self.start_id  =start_id # 初始id值
        self.id_hand_status = {}  # {id: (hand_left,hand_right)}
        self.id_eye_status = {}  # {id:eye}

        # 打印初始化信息
        print('#################\n初始化Translator成功\n#################')
        print('本机设备限制人数：', self.num_player_indevice)
        # print('# of hands: ', self.hand_constraint)
        # print('# of eyes:', self.eye_constraint)print('# of hands: ', self.hand_constraint)
        # print('# of eyes:', self.eye_constraint)
        print('稳定器长度(帧): ', voting_fps)

    def arrange_person(self, boxs, conf, cls):
        """
        去除多检结果后, 将person的bounding box按照x_topleft从左到右存储到self.persons
        1. 多检结果会删除置信度低的
        2. 漏检会自动从上一次成功检测中补全
        :param boxs: detect res
        :param conf: detect res
        :param cls: detect res
        :return:
        """

        # print("------------------------------------------------------------------------------------------")
        # print(boxs, conf, cls)

        # 存储 person: [[conf,[center_point]],[],[]]
        person_boxandconf = []
        for i in range(len(cls)):
            if cls[i] == 'person':
                person_boxandconf.append([conf[i], xyxy2center_point(boxs[i])])

        # 测试输出
        # print('person boxandconf')
        # print(person_boxandconf)

        person_boxandconf.sort(key=lambda x: x[0], reverse=True)  # 对嵌套列表cof维度从大到小排序

        # 测试输出
        # print('person boxandconf order: ', person_boxandconf)

        if len(person_boxandconf) == 0:
            print('当前帧person数', len(person_boxandconf))
        elif len(person_boxandconf) > self.num_player_indevice:  # 出现多检测, 取device设备限制人数
            print('#################\n多检测person触发\n#################')
            print('当前帧person数', len(person_boxandconf))
            person_boxandconf = person_boxandconf[:self.num_player_indevice]
            person_boxandconf.sort(key=lambda x: x[1][0], reverse=False)  # 按照x_center从小到大排序
        elif self.num_player_indevice > len(person_boxandconf) > 0:  # 出现漏检测
            print('#################\n少检测person触发\n#################')
            print('当前帧person数', len(person_boxandconf))
            full_index = [x for x in range(self.num_player_indevice)]  # 完整的index list
            try:
                success_index = []  # 成功检测的person id list
                for i in range(len(person_boxandconf)):
                    index_shortest = None
                    shortest = sys.maxsize
                    for j in range(len(self.persons)):
                        distance = manhattan_distance(person_boxandconf[i][1], self.persons[j])
                        if distance < shortest:
                            index_shortest = j
                            shortest = distance
                    success_index.append(index_shortest)
                miss_index = list(set(full_index).difference(set(success_index)))  # 求差集
                print('漏检测id：', [i + 1 for i in miss_index])
                for i in miss_index:
                    person_boxandconf.append(self.persons[i])  # 从上一次检测的成功结果结果中补全
                person_boxandconf.sort(key=lambda x: x[1][0], reverse=False)  # 按照x_center从小到大排序
            except:
                print('process: 漏检测补全失败')
        else:  # 正确检测
            person_boxandconf.sort(key=lambda x: x[1][0], reverse=False)  # 按照x_center从小到大排序

        # 测试输出
        # print('person boxandconf output: ', person_boxandconf)

        # 更新persons
        for i in range(len(person_boxandconf)):
            self.persons[i] = person_boxandconf[i][1]

        # print('arrange persons: ', self.persons)

    def assign_object2person(self, boxs, conf, cls):
        """
        将 hand 和 eye的检测结果存储到deque
        1. 关联hand和eye->person_id
        2. 过滤多检
        :param boxs:
        :param conf:
        :param cls:
        :return:
        """
        # 存储 hand/eye: [[cls,conf,[center_point]],[],[]]
        hand_list = []
        eye_list = []
        # 按照personid-1 存储hand,eye结果 [[[cls,conf,[center_point]],[],[]],[],[]]
        final_handlist = [[] for _ in range(self.num_player_indevice)]
        final_eyelist = [[] for _ in range(self.num_player_indevice)]
        for i in range(len(cls)):
            if cls[i] in hand_labels:
                hand_list.append([cls[i], conf[i], xyxy2center_point(boxs[i])])
            elif cls[i] in eye_labels:
                eye_list.append([cls[i], conf[i], xyxy2center_point(boxs[i])])

        # 测试输出
        # print('original handlist:', hand_list)
        # print('original eyelist:', eye_list)

        # 关联hand
        try:
            for i in range(len(hand_list)):
                shortest = sys.maxsize
                index_shortest = None
                empty_time = 0
                for j in range(len(self.persons)):
                    try:
                        distance = manhattan_distance(hand_list[i][2], self.persons[j])
                        if distance < shortest:
                            index_shortest = j
                            shortest = distance
                    except:
                        empty_time += 1
                        print('process: hand为空集 / person 丢失', str(empty_time), '个')
                final_handlist[index_shortest].append(hand_list[i])
        except:
            print('process: 没有person可以和hand posture关联')

        # 关联eye
        try:
            for i in range(len(eye_list)):
                shortest = sys.maxsize
                index_shortest = None
                empty_time = 0
                for j in range(len(self.persons)):
                    try:
                        distance = manhattan_distance(eye_list[i][2], self.persons[j])
                        if distance < shortest:
                            index_shortest = j
                            shortest = distance
                    except:
                        empty_time += 1
                        print('process: eye为空集 / person 丢失', str(empty_time), '个')
                final_eyelist[index_shortest].append(eye_list[i])
        except:
            print('process: 没有person可以和eye关联')

        # 去重
        try:
            for i in range(len(final_handlist)):
                if len(final_handlist[i]) > self.hand_constraint:
                    final_handlist[i].sort(key=lambda x: x[1], reverse=True)  # 对嵌套列表cof维度从大到小排序
                    final_handlist[i] = final_handlist[i][:self.hand_constraint]
            for i in range(len(final_eyelist)):
                if len(final_eyelist[i]) > self.eye_constraint:
                    final_eyelist[i].sort(key=lambda x: x[1], reverse=True)  # 对嵌套列表cof维度从大到小排序
                    final_eyelist[i] = final_eyelist[i][:self.eye_constraint]
        except:
            print('process: 去重失败')

        # 手必须按照x_center排序否则影响结果
        for i in range(len(final_handlist)):
            final_handlist[i].sort(key=lambda x: x[2][0], reverse=False)  # 按照x_center从小到大排序

        # 测试输出
        # print('final_handlist: ', final_handlist)
        # print('final_eyelist: ', final_eyelist)

        # hand, eye进入deque(有列表，需要从0开始)
        for i in range(self.num_player_indevice):
            # hand
            if not final_handlist[i]:  # 没有手
                self.id_hand_deque[i + 1].append(('nohand', 'nohand'))
            elif len(final_handlist[i]) == 1:  # 有1只手
                self.id_hand_deque[i + 1].append((final_handlist[i][0][0], 'nohand'))
            elif len(final_handlist[i]) == 2:  # 有2只手
                self.id_hand_deque[i + 1].append((final_handlist[i][0][0], final_handlist[i][1][0]))
            # eye
            if not final_eyelist[i]:  # 空集
                self.id_eye_deque[i + 1].append('noeye')
            else:
                self.id_eye_deque[i + 1].append(final_eyelist[i][0][0])

        # print("hand deque: ", self.id_hand_deque)
        # print("eye deque: ", self.id_eye_deque)

    def voting(self):
        """
        将deque结果voting，稳定检测结果
        :return:
        """
        # 没有列表，从1开始,从start开始赋值
        for i in range(1, self.num_player_indevice + 1):
            self.id_hand_status[i+self.start_id-1] = Counter(self.id_hand_deque[i]).most_common(1)[0][0]
            self.id_eye_status[i+self.start_id-1] = Counter(self.id_eye_deque[i]).most_common(1)[0][0]

        # 测试输出
        # print('hand_status:', self.id_hand_status)
        # print('eye_status:', self.id_eye_status)
