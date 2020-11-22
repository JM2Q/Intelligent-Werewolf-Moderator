import cfg


class Broadcast(object):
    def __init__(self):
        self.assign_id = 1  # 当前赋予玩家角色id，初始值为1
        self.countdown_pro = 100
        self.confirm_pro = 0  # 确认pro:初始为0
        self.stage = 0  # 默认是0: 游戏流程 0.赋予角色流程 1.晚上：狼人行动 2.晚上：预言家验人 3.女巫救人 4.女巫毒人
        self.flag_jump = True  # 页面跳转标志位

    def update_guires(self):
        """更新GUI结果"""
        self.assign_id = cfg.assign_id  # 当前赋予玩家角色id，初始值为1
        self.countdown_pro = cfg.countdown_pro
        self.confirm_pro = cfg.confirm_pro  # 确认pro:初始为0
        self.stage = cfg.stage  # 默认是0: 游戏流程 0.赋予角色流程 1.晚上：狼人行动 2.晚上：预言家验人 3.女巫救人 4.女巫毒人
        self.flag_jump = cfg.flag_jump  # 页面跳转标志位
