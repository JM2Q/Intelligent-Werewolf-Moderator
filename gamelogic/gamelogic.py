"""
游戏逻辑模块
"""

import random
from collections import Counter

"""
游戏角色配置表硬编码
"""
config_list = [{},  # 0
               {'Villager': 0, 'Seer': 0, 'Witch': 0, 'Hunter': 0, 'Werewolf': 1},  # 1
               {'Villager': 0, 'Seer': 0, 'Witch': 0, 'Hunter': 1, 'Werewolf': 1},  # 2
               {'Villager': 1, 'Seer': 0, 'Witch': 0, 'Hunter': 1, 'Werewolf': 1},  # 3
               {'Villager': 1, 'Seer': 0, 'Witch': 1, 'Hunter': 1, 'Werewolf': 1},  # 4
               {'Villager': 2, 'Seer': 0, 'Witch': 1, 'Hunter': 1, 'Werewolf': 1},  # 5
               {'Villager': 2, 'Seer': 1, 'Witch': 1, 'Hunter': 0, 'Werewolf': 2},  # 6
               {'Villager': 3, 'Seer': 1, 'Witch': 1, 'Hunter': 0, 'Werewolf': 2},  # 7
               {'Villager': 3, 'Seer': 1, 'Witch': 1, 'Hunter': 0, 'Werewolf': 3},  # 8
               {'Villager': 3, 'Seer': 1, 'Witch': 1, 'Hunter': 1, 'Werewolf': 3},  # 9
               {'Villager': 4, 'Seer': 1, 'Witch': 1, 'Hunter': 1, 'Werewolf': 3},  # 10
               ]


# 角色类
class Character(object):
    def __init__(self):
        self.status = "alive"  # alive, killed, poisoned, shot, voted


class Villager(Character):  # 村民
    def __init__(self):
        super().__init__()


class Seer(Character):  # 预言家
    def __init__(self):
        super().__init__()

    @staticmethod
    def see(player):
        return type(player).__name__


class Witch(Character):  # 女巫
    def __init__(self):
        super().__init__()
        self.have_poison = True  # 毒药
        self.have_elixir = True  # 解药

    def poison(self, player):
        if self.have_poison is True:  # 有毒药
            player.status = 'poisoned'
            self.have_poison = False
        elif self.have_poison is False:  # 没有毒药
            pass

    def save(self, player):
        if self.have_elixir is True:  # 有解药
            player.status = 'alive'
            self.have_elixir = False
        elif self.have_poison is False:  # 没有解药
            pass


class Hunter(Character):  # 猎人
    def __init__(self):
        super().__init__()


class Werewolf(Character):  # 狼人
    def __init__(self):
        super().__init__()

    # def boom(self): # 爆狼
    #     self.alive = False
    #     pass


# 游戏管理类
class Game(object):
    def __init__(self):
        self.players = {}  # 玩家id-实例表{id: Character}
        self.spec_id = {'Seer': [0], 'Witch': [0], 'Hunter': [0], 'Werewolf': []}  # 特殊角色位置
        self.progress = {}  # 游戏进程表 {day: [killed_id, poisoned_id, flag_save,voting]} ...voting
        for i in range(1, 10):
            self.progress[i] = [0, 0, 0, 0]  # 初始化游戏进程
        self.index_stage = None  # 游戏角色行动进度索引, 和stage_label对应
        self.protect = 0  # 首刀保护id
        self.num_players = 0  # 游戏人数

    def get_id_list(self):
        """
        获取id-character表
        :return: id_list
        """
        id_list = {}
        for player_id, player in self.players.items():
            id_list[player_id] = type(player).__name__
        return id_list

    def get_character_list(self):
        """
        获取当前游戏角色个数统计表
        :return: character_list
        """
        character_list = {'Villager': 0, 'Seer': 0, 'Witch': 0, 'Hunter': 0, 'Werewolf': 0}
        for player_id, player in self.players.items():
            if player.status == 'alive':
                if type(player).__name__ == 'Villager':
                    character_list['Villager'] += 1
                elif type(player).__name__ == 'Seer':
                    character_list['Seer'] += 1
                elif type(player).__name__ == 'Witch':
                    character_list['Witch'] += 1
                elif type(player).__name__ == 'Hunter':
                    character_list['Hunter'] += 1
                elif type(player).__name__ == 'Werewolf':
                    character_list['Werewolf'] += 1
                else:
                    return 0  # 角色统计列表返回失败
        return character_list

    def get_status_list(self):
        """
        获取id-status表 {id: status} status: alive, killed, poisoned
        :return: alive_list
        """
        status_list = {}
        for player_id, player in self.players.items():
            status_list[player_id] = player.status
        return status_list

    def get_alive_idlist(self):
        """
        获取存活玩家id表
        :return:
        """

        alive_idlist = []
        for player_id, player in self.players.items():
            if player.status == 'alive':
                alive_idlist.append(player_id)
        return alive_idlist

    def start_game(self, num_players):
        """
        游戏初始化
        :param num_players: 游戏人数
        :return:
        """
        # 根据狼人杀配置表初始化游戏
        self.num_players = num_players
        character_list = []  # id顺序的角色列表
        # 按照顺序赋予每个id一个初始角色
        for character, num_character in config_list[num_players].items():
            while num_character > 0:
                character_list.append(character)
                num_character -= 1

        random.shuffle(character_list)  # 洗乱角色

        id_index = 1
        # 角色实例化
        for character in character_list:
            if character == 'Villager':
                self.players[id_index] = Villager()
            elif character == 'Seer':
                self.players[id_index] = Seer()
            elif character == 'Witch':
                self.players[id_index] = Witch()
            elif character == 'Hunter':
                self.players[id_index] = Hunter()
            elif character == 'Werewolf':
                self.players[id_index] = Werewolf()
            else:
                return 0  # 角色实例化失败
            id_index += 1

        # 记录特殊角色位置, 如果没有则默认为0
        for player_id, player in self.players.items():
            if type(player).__name__ == 'Villager':
                pass
            elif type(player).__name__ == 'Seer':
                self.spec_id['Seer'] = [player_id]
            elif type(player).__name__ == 'Witch':
                self.spec_id['Witch'] = [player_id]
            elif type(player).__name__ == 'Hunter':
                self.spec_id['Hunter'] = [player_id]
            elif type(player).__name__ == 'Werewolf':
                self.spec_id['Werewolf'].append(player_id)
            else:
                print("error: 角色统计生成失败")
                return 0

        # 测试输出
        print('################\n初始化Game logic成功\n################')
        print('狼人杀游戏角色分配完成！')
        print('gamelogic id list: ', self.get_id_list())
        print('gamelogic spec list: ', self.spec_id)
        print('gamelogic character list: ', self.get_character_list())
        print('gamelogic status list: ', self.get_status_list())

    def movement_werewolf(self, day, killed_id):
        """
        狼人行动
        注意：狼人不能马上杀人，否则被杀的人夜晚无法执行行动
        :param day: 游戏轮次
        :param killed_id: 被杀者id，0为不杀人
        :return:
        """
        # 狼人杀人
        if killed_id == 0:  # 没有人被杀
            self.progress[day][0] = 0
        else:
            if self.players[killed_id].status == 'alive':  # 只有存活的人才能被杀
                # self.players[killed_id].status = 'killed' 不能马上结算
                self.progress[day][0] = killed_id  # 被杀的人存档
            else:
                self.progress[day][0] = 0

    def movement_seer(self, see_id):
        """
        预言家行动
        :param see_id: 被预测的玩家
        :return: 1为好人，0为坏人 2为不确定
        """

        if self.spec_id['Seer'][0] == 0 or self.players[self.spec_id['Seer'][0]].status != 'alive':  # 游戏板子没有预言家 / 预言家死亡
            return 2  # 不确定
        else:  # 游戏板子有预言家
            seer = self.players[self.spec_id['Seer'][0]]  # 找到预言家实例
            if seer.status == 'alive':  # 预言家存活
                if see_id == 0:  # 预言家不验人
                    return 2
                else:  # 预言家验人
                    if seer.see(self.players[see_id]) == 'Villager' or seer.see(
                            self.players[see_id]) == 'Seer' or seer.see(
                        self.players[see_id]) == 'Witch' or seer.see(self.players[see_id]) == 'Hunter':
                        return 1  # 好人
                    else:
                        return 0  # 坏人
            else:
                return 2

    def movement_witch_save(self, day, save):
        """
        女巫救人
        :param day: 游戏轮次
        :param save: 1为救人，0为不救
        :return:
        """

        if self.spec_id['Witch'][0] == 0 or self.players[
            self.spec_id['Witch'][0]].status != 'alive':  # 游戏板子没有女巫 / 女巫死亡
            self.progress[day][2] = 0  # 没有人被救
        else:
            witch = self.players[self.spec_id['Witch'][0]]  # 找到女巫实例

            # 救人条件：有解药 + 决定救人 + 有人被杀
            if witch.have_elixir is True and save != 0:
                if self.progress[day][0] == 0:  # 没有人被杀
                    self.progress[day][2] = 0  # 没有人被救
                else:  # 有人被杀
                    # witch.save(self.players[self.progress[day][0]])  # 不能马上救人
                    self.progress[day][2] = 1  # 救人存档
            else:
                self.progress[day][2] = 0  # 没有人被救

    def movement_witch_poison(self, day, poison_id):
        """
        女巫毒人
        :param day: 游戏轮次
        :param poison_id: 被毒的人id, 0为不毒
        :return:
        """
        if self.spec_id['Witch'][0] == 0 or poison_id > self.num_players or self.players[
            self.spec_id['Witch'][0]].status != 'alive':  # 游戏板子没有女巫 / 女巫死亡 / 毒人在场外
            self.progress[day][1] = 0  # 没有人被毒
        elif poison_id == 0: # 不毒人
            self.progress[day][1] = 0  # 没有人被毒
        else:
            witch = self.players[self.spec_id['Witch'][0]]  # 找到女巫实例

            # 毒人条件：有毒药 + 毒的人存活+选择毒人
            if witch.have_poison is True and self.players[poison_id].status == 'alive' and poison_id != 0:
                # witch.poison(self.players[poison_id])  # 不能马上毒人
                self.progress[day][1] = poison_id  # 被毒人存档
            else:
                self.progress[day][1] = 0  # 没有人被毒

    def movement_hunter(self, shoot_id):
        """
        猎人开枪(确保这个函数只触发一次)
        :param shoot_id: 要枪杀的人,0为不开枪
        :return:
        """
        if self.spec_id['Hunter'][0] == 0:  # 游戏板子没有猎人
            pass
        else:
            if shoot_id == 0:
                pass
            elif self.players[shoot_id].status == 'alive':
                self.players[shoot_id].status = 'shot'
            else:
                pass

    def announce_night(self, day):
        """
        统一结算，宣布晚上的结果
        :param day: 天数
        :return: [killed_id, poisoned_id] (0为无人)
        """
        announce = [0, 0]

        # 开始结算：
        # 1.女巫是否救人
        if self.progress[day][2] == 1:  # 女巫救人
            witch = self.players[self.spec_id['Witch'][0]]  # 找到女巫实例
            if announce[0] == 0: #没有人被杀
                pass
            else:# 有人被杀，救
                witch.save(self.players[announce[0]])
        else:  # 女巫没有救人
            if self.progress[day][0] == 0: # 狼人没有杀人
                announce[0] = 0  # 被杀的人没有死
            else:
                self.players[self.progress[day][0]].status = 'killed'  # 狼人杀人
                announce[0] = self.progress[day][0]

        # 2.女巫开始毒人
        if self.progress[day][1] == 0:  # 女巫没有毒人
            announce[1] = 0

        else:
            witch = self.players[self.spec_id['Witch'][0]]  # 找到女巫实例
            witch.poison(self.players[self.progress[day][1]])  # 女巫毒人
            announce[1] = self.progress[day][1]  # 添加到宣告结果
        return announce

    def voting(self, day, voting_id):
        """
        :param voting_id: 被投票的id,0为没有人被投
        :return:
        """
        if voting_id == 0:
            pass
        else:
            self.players[voting_id].status = 'voted'  # 投票出局
            self.progress[day][3] = voting_id  # 记录

    @staticmethod
    def is_gameover(character_list):
        """
        游戏结束判断
        :param character_list: 角色数量统计表
        :return: 0：游戏继续
                 1：好人获胜
                 2：狼人获胜
        """
        if character_list['Villager'] == 0 or character_list['Seer'] + character_list['Witch'] + character_list[
            'Hunter'] == 0:  # 屠边
            return 2
        elif character_list['Werewolf'] == (
                character_list['Villager'] + character_list['Seer'] + character_list['Witch'] + character_list[
            'Hunter']):  # 狼刀领先
            return 2
        elif character_list['Werewolf'] == 0:
            return 1
        else:
            return 0
