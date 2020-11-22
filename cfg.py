"""
全部设备共享变量
"""
qsize = 15  # 稳定器长度
slave_ip = ""
host_ip = ""

"""
本机变量
"""
num_devices = 0  # 总设备数量, 最大支持2
device_id = -1  # 初始值为-1,主机为0, 从机为1
num_players_indevice = 0  # 本机检测玩家数,初始值为0
start_id = 1  # 默认值是1,translator检测的起始id
flag_config = False  # 默认值是False
flag_startgame = False

"""
主机变量
"""
num_players = 0  # 总游戏人数,初始值是0：配置游戏阶段
day = 1  # 游戏轮次
flag_audio_start = True  # 开始语音标志位
flag_audio_end = True  # 结束语音标志位
flag_audio_cheat = True  # 作弊语音标志位
flag_audio_background = True  # 背景音标志位


assign_id = 1  # 当前赋予玩家角色id，初始值为1

# GUI页面元素变量
countdown_pro = 100
countdown_rate = 1
countdown_thres = 100  # 倒计时初始值

confirm_pro = 0  # 确认pro:初始为0
comfirm_rate = 3  # 确认pro累积速率
comfirm_thres = 100  # 确认阈值
flag_confirm = False  # 玩家确认标志位，保证只有时间走完才进行下一个流程

stage = 0  # 默认是0: 游戏流程 0.赋予角色流程 1.晚上：狼人行动 2.晚上：预言家验人 3.女巫救人 4.女巫毒人
# flag_seer = False  # 预言家验人状态
flag_jump = True  # 页面跳转标志位




# seer_res = 2  # 预言家验人结果,1为好人，2为坏人 默认2为不确定
