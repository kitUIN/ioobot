import datetime
import random
import re
import time

import botoy.decorators as deco
import cpuinfo
import psutil
import requests
from botoy import FriendMsg, GroupMsg, EventMsg

from plugins.ioolib.dbs import *
from plugins.ioolib.send import Send

action = Action(qq=config['BotQQ'])
renping = {}  # 人品记录
sendMsg = Send()
# ------------------正则------------------
pattern_command = '#(.*?)'
black_list = '#p'  # 防止与bot_pixiv.py重冲突


class Sysinfo:
    def __init__(self):
        pass

    @staticmethod
    def _get_cpu_info():  # 获取cpu信息
        info = cpuinfo.get_cpu_info()  # 获取CPU型号等
        cpu_count = psutil.cpu_count(logical=False)  # 1代表单核CPU，2代表双核CPU
        xc_count = psutil.cpu_count()  # 线程数，如双核四线程
        cpu_percent = round((psutil.cpu_percent()), 2)  # cpu使用率
        try:
            model = info['hardware_raw']  # cpu型号
        except:
            model = info['brand_raw']  # cpu型号
        try:  # 频率
            freq = info['hz_actual_friendly']
        except:
            freq = 'null'
        cpu_info = (model, freq, info['arch'], cpu_count, xc_count, cpu_percent)
        return cpu_info

    @staticmethod
    def _get_memory_info():  # 获取内存信息
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        total_nc = round((float(memory.total) / 1024 / 1024 / 1024), 3)  # 总内存
        used_nc = round((float(memory.used) / 1024 / 1024 / 1024), 3)  # 已用内存
        available_nc = round((float(memory.available) / 1024 / 1024 / 1024), 3)  # 空闲内存
        percent_nc = memory.percent  # 内存使用率
        swap_total = round((float(swap.total) / 1024 / 1024 / 1024), 3)  # 总swap
        swap_used = round((float(swap.used) / 1024 / 1024 / 1024), 3)  # 已用swap
        swap_free = round((float(swap.free) / 1024 / 1024 / 1024), 3)  # 空闲swap
        swap_percent = swap.percent  # swap使用率
        men_info = (total_nc, used_nc, available_nc, percent_nc, swap_total, swap_used, swap_free, swap_percent)
        return men_info

    @staticmethod
    def _uptime():  # 时间
        now = time.time()
        boot = psutil.boot_time()
        boottime = datetime.datetime.fromtimestamp(boot).strftime("%Y-%m-%d %H:%M:%S")
        nowtime = datetime.datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")
        up_time = str(
            datetime.datetime.utcfromtimestamp(now).replace(microsecond=0) - datetime.datetime.utcfromtimestamp(
                boot).replace(microsecond=0))
        alltime = (boottime, nowtime, up_time)
        return alltime

    def sysinfo(self):  # 获取系统信息
        cpu_info = self._get_cpu_info()
        mem_info = self._get_memory_info()
        up_time = self._uptime()
        full_meg = '运行状况\r\n线程：{}\r\n负载:{}%\r\n总内存:{}G\r\n已用内存:{}G\r\n空闲内存:{}G\r\n内存使用率:{}%\r\n' \
                   'swap:{}G\r\n已用swap:{}G\r\n空闲swap:{}G\r\nswap使用率:{}%\r\n' \
                   '开机时间:{}\r\n当前时间:{}\r\n已运行时间:{}'.format(
            cpu_info[4], cpu_info[5], mem_info[0], mem_info[1], mem_info[2], mem_info[3], mem_info[4], mem_info[5],
            mem_info[6], mem_info[7], up_time[0], up_time[1], up_time[2])
        return full_meg


class Command:
    def __init__(self, ctx):
        self.ctx = ctx
        self.db_raw = {}  # 原始数据库
        self.db = {}

    def change_dict(self, dicta, lista, change, ret=''):
        x = dicta[lista[0]]
        ret += (str(lista[0]) + ' ')
        if len(lista) == 1:
            rt_befeore = dicta.copy()
            dicta[lista[0]] = change
            return '{}: {}\n↓↓↓↓\n{}: {}'.format(ret, rt_befeore[lista[0]], ret, dicta[lista[0]])
        lista.pop(0)
        return self.change_dict(x, lista, change, ret)

    def cmd_group(self, lv):
        ret = ''
        if lv <= 2:  # 控制命令
            if self.ctx.Content == '#开启群聊r18':
                ret = self.change_dict(self.db_raw, ['r18', 'group'], True)
            elif self.ctx.Content == '#关闭群聊r18':
                ret = self.change_dict(self.db_raw, ['r18', 'group'], False)
            elif self.ctx.Content == '#开启私聊r18':
                ret = self.change_dict(self.db_raw, ['r18', 'temp'], True)
            elif self.ctx.Content == '#关闭私聊r18':
                ret = self.change_dict(self.db_raw, ['r18', 'temp'], False)
            elif self.ctx.Content == '#开启私聊色图':
                ret = self.change_dict(self.db_raw, ['setu', 'temp'], True)
            elif self.ctx.Content == '#关闭私聊色图':
                ret = self.change_dict(self.db_raw, ['setu', 'temp'], False)
            elif self.ctx.Content == '#开启群聊色图':
                ret = self.change_dict(self.db_raw, ['setu', 'group'], True)
            elif self.ctx.Content == '#关闭群聊色图':
                ret = self.change_dict(self.db_raw, ['setu', 'group'], False)
            elif self.ctx.Content == '#关闭群聊撤回':
                ret = self.change_dict(self.db_raw, ['revoke', 'group'], 0)
            elif self.ctx.Content == '#开启群聊撤回':
                ret = self.change_dict(self.db_raw, ['revoke', 'group'], 25)  # 默认开启撤回为25s
            elif self.ctx.Content == '#关闭私聊撤回':
                ret = self.change_dict(self.db_raw, ['revoke', 'temp'], 0)
            elif self.ctx.Content == '#开启私聊撤回':
                ret = self.change_dict(self.db_raw, ['revoke', 'temp'], 25)  # 默认开启撤回为25s
            elif self.ctx.Content == '#开启群聊原图':
                ret = self.change_dict(self.db_raw, ['original', 'group'], True)
            elif self.ctx.Content == '#关闭群聊原图':
                ret = self.change_dict(self.db_raw, ['original', 'group'], False)
            elif self.ctx.Content == '#开启私聊原图':
                ret = self.change_dict(self.db_raw, ['original', 'temp'], True)
            elif self.ctx.Content == '#关闭私聊原图':
                ret = self.change_dict(self.db_raw, ['original', 'temp'], False)
            elif self.ctx.Content == '#开启色图@':
                ret = self.change_dict(self.db_raw, ['at'], True)
            elif self.ctx.Content == '#关闭色图@':
                ret = self.change_dict(self.db_raw, ['at'], False)
            elif self.ctx.Content == '#开启警告@':
                ret = self.change_dict(self.db_raw, ['at_warning'], True)
            elif self.ctx.Content == '#关闭警告@':
                ret = self.change_dict(self.db_raw, ['at_warning'], False)
            elif self.ctx.Content == '#开启tag显示':
                ret = self.change_dict(self.db_raw, ['showTag'], True)
            elif self.ctx.Content == '#关闭tag显示':
                ret = self.change_dict(self.db_raw, ['showTag'], False)
            else:
                if lv < 2:
                    if self.ctx.MsgType == 'AtMsg':
                        At_Content_front = re.sub(r'@.*', '', json.loads(self.ctx.Content)['Content'])  # @消息前面的内容
                        atqqs: list = json.loads(self.ctx.Content)['UserID']
                        if At_Content_front == '#增加管理员':
                            for qq in atqqs:
                                if qq in self.db['admins']:
                                    sendMsg.send_text(self.ctx, '{}已经是机器人管理员了'.format(qq))
                                    sendMsg.send_text(self.ctx, '增加机器人管理员失败')
                                    return
                                self.db['managers'].append(qq)
                            ret = '增加机器人管理员成功'

                        elif At_Content_front == '#删除管理员':
                            for qq in atqqs:
                                try:
                                    self.db['managers'].remove(qq)
                                except:
                                    sendMsg.send_text(self.ctx, '删除机器人管理员出错')
                                    return
                            ret = '删除机器人管理员成功'
                        else:
                            if self.ctx.Content[:2] not in black_list:
                                sendMsg.send_text(self.ctx, '无此命令')
                                return
                else:
                    if self.ctx.Content[:2] not in black_list:
                        sendMsg.send_text(self.ctx, '无此命令')
                        return

            # ------------------更新数据--------------------
            if ret != '':  # 如果有ret
                sendMsg.send_text(self.ctx, ret)
                group_config.update(self.db_raw, Q['GroupId'] == self.db['GroupId'])
            group_config.update(self.db_raw, Q['GroupId'] == self.db['GroupId'])
        else:
            #  if lv == 3:
            if self.ctx.Content[:2] not in black_list:
                sendMsg.send_text(self.ctx, '找不到这个命令了，试试#帮助 吧')
                return
            #  sendMsg.send_text(self.ctx, '¿没权限玩🐎呢¿')


    def cmd(self, group, lv):  # todo 迁移 网易云识别，setu统计，
        if self.ctx.Content == '#sysinfo' or self.ctx.Content == '#运行状态' or self.ctx.Content == '#系统信息':  # 运行状态
            msg = Sysinfo().sysinfo()
            sendMsg.send_text(self.ctx, msg)
            return
        elif self.ctx.Content == '#今日人品' or self.ctx.Content == '#jrrp':  # 今日人品
            if group:
                id = self.ctx.FromUserId
            else:
                id = self.ctx.FromUin
            if id in renping:
                math = renping[id]
            else:
                math = random.randint(0, 100)
                renping[id] = math
            msg = '欧吗？{}年寿命换的。'.format(math)

            sendMsg.send_pic(self.ctx, msg, '', 'look/ouhuang.jpg', False, False)
            return
        elif self.ctx.Content == '#打赏':
            sendMsg.send_pic(self.ctx, '', '', 'look/dashang.jpg', False, False)
            sendMsg.send_pic(self.ctx, '', '', 'look/keai.jpg', False, False)
            return
        elif self.ctx.Content[:3] == '#留言' or self.ctx.Content[:3] == '#ly':
            try:
                msg = '来自：QQ{}(群{})，内容：{}'.format(str(self.ctx.FromGroupId), str(self.ctx.FromUserId), self.ctx.Content)
            except:
                msg = '来自：{}，内容：{}'.format(str(self.ctx.FromUin), self.ctx.Content)
            action.sendFriendText(config['superAdmin'], msg)
            sendMsg.send_text(self.ctx, '已为您留言', True)
            return
        elif self.ctx.Content == '#help' or self.ctx.Content == '#帮助':
            sendMsg.send_pic(self.ctx, '', '', 'look/help.png', False, False)
            return
        elif self.ctx.Content[:5] == '#查看图片':  # 测试
            if self.ctx.Content[6:7] == '1':
                try:
                    sendMsg.send_pic(self.ctx, picUrl=self.ctx.Content[6:].strip())
                except:
                    logger.error('查看失败')
            elif self.ctx.Content[6:7] == '2':
                try:
                    _REQUESTS_KWARGS = {
                        'proxies': {
                            'https': config['proxy'],  # 'http://127.0.0.1:10809'  代理
                        },
                    }
                    url = self.ctx.Content[6:].strip()
                    res = requests.get(url, **_REQUESTS_KWARGS)
                    with open('pic.jpg', 'wb') as f:
                        f.write(res.content)
                    sendMsg.send_pic(self.ctx, picPath='pic.jpg')
                except:
                    logger.error('查看失败')
        elif group:
            self.cmd_group(lv)
        else:
            if self.ctx.Content[:2] not in black_list:
                sendMsg.send_text(self.ctx, '找不到这个命令了，试试#帮助 吧')
                return

    def group_or_temp(self):
        group_id = 0
        if self.ctx.__class__.__name__ == 'GroupMsg':  # 群聊
            group_id = self.ctx.FromGroupId
            self.db['type'] = 'group'
            self.db['callqq'] = self.ctx.FromUserId
        elif self.ctx.MsgType == 'TempSessionMsg':  # 临时会话
            group_id = self.ctx.TempUin
            self.db['callqq'] = self.ctx.FromUin
            self.db['type'] = 'temp'
        data = group_config.search(Q['GroupId'] == group_id)
        self.db_raw = data[0]
        self.db.update(data[0])  # 载入数据
        # -------------------权限等级分层-----------------------------------
        lv = 3  # 群友
        if self.db['callqq'] == config['superAdmin']:  # 鉴权(等级高的写前面)
            lv = 0  # root
        elif self.db['callqq'] in data[0]['admins']:
            lv = 1  # 机器人指定管理员
        elif self.db['callqq'] in data[0]['managers']:
            lv = 2  # 群管理员
        # ------------------------------------------------------
        if data:  # 查询group数据库数据
            self.cmd(True, lv)
        else:
            sendMsg.send_text(self.ctx, '数据库无群:{}信息,请联系管理员~'.format(group_id))
            logger.error('数据库无群:{}信息'.format(group_id))
            return

    def friend(self):
        self.cmd(False, 3)
        return

    def main(self):
        if self.ctx.__class__.__name__ == 'GroupMsg' or self.ctx.MsgType == 'TempSessionMsg':  # 群聊or临时会话
            self.group_or_temp()
        else:  # 好友会话
            self.friend()


# ----------------------------------------

@deco.queued_up
@deco.ignore_botself
def receive_friend_msg(ctx: FriendMsg):  # 修改指令 前往ioobot/plugins/ioolib/command.py
    if re.match(pattern_command, ctx.Content):
        Command(ctx).main()


@deco.queued_up
@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if re.match(pattern_command, ctx.Content):
        Command(ctx).main()


def receive_events(ctx: EventMsg):
    Action(ctx.CurrentQQ)
