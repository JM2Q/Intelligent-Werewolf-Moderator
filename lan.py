import socket
import pickle
import time
import os


class Ani:
    def __init__(self, action, move):
        self.action = action
        self.move = move


# 创建一个客户端的socket类
class Lan(object):
    def __init__(self, type, host, port):
        self.socketserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.type = type  # 主机从机 - {1从 ； 0主}
        self.host = host  # 服务端的ip地址
        self.port = port  # 设置端口
        if self.type == 1:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.host, self.port))
        else:
            self.socketserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socketserver.bind((self.host, self.port))
            self.socketserver.listen(5)
            self.clientsocket, self.addr = self.socketserver.accept()
        print('################\n端口初始化成功\n################')

    @staticmethod
    def get_ip():
        hostname = socket.gethostname()
        host = socket.gethostbyname(hostname)
        os.system('arp -a > IP_Info.txt')
        fp = open('IP_Info.txt').readlines()
        for i in range(len(fp)):
            if fp[i][0:2] == '接口' and fp[i][4:14] == '192.168.1.':
                line = fp[i][4:17]
                return line

    def receive(self):
        if self.type == 1:
            data = self.client.recv(1024)
        else:
            data = self.clientsocket.recv(1024)
        recemsg = pickle.loads(data)
        # print(recemsg)
        return recemsg

    def send(self, sendmsg):
        data = pickle.dumps(sendmsg)
        if self.type == 1:
            self.client.send(data)
        if self.type == 0:
            self.clientsocket.send(data)
        # print('Sent')

    def close(self):
        if self.type == 1:
            self.client.close()
        else:
            self.socketserver.close()

    def info(self):
        if self.addr[0] != None:
            print('The ID of host：', self.host, 'The ID of slave: ', self.addr[0])
            return self.host, self.addr[0]
        else:
            print('The ID of host：', self.host)
            return self.host


if __name__ == '__main__':
    ip_ads = Lan.get_ip()
    print(ip_ads)
    # while循环是为了保证能持续进行对话
    # lan = Lan(0,str(ip_ads))
    lan = Lan(0, '192.168.1.36',6000)
    tiger = Ani('tiger', 'run')

    while True:
        # lan.receive()
        # lan.info()
        time.sleep(1)
        lan.send(tiger)

    # 关闭客户端
    lan.close()
    pass
