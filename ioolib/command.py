import base64
import random
import re

from .dbs import *
from .message import Send
from .picsearch import PicSearch
from .sysinfo import *

renping = {}  # 人品记录
sendMsg = Send()
FuDu = 0
FuDuQQG = 0


def tobase64(filename):
    with open(filename, 'rb') as f:
        coding = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
        logger.info('本地base64转码~')
        return coding.decode()


def send_ver(mess):
    version = config['Version']
    versions = config['version']
    vers = '当前版本→' + version + '←' + '\r\n#----历史版本----#\r\n'
    for ve in versions:
        vers = vers + ve + ','
    vers = vers + '\r\n#----更新内容----#\r\n'
    if mess.Content == '#v1.0.0':
        vers = vers + versions['v1.0.0']
    elif mess.Content == '#v1.0.1':
        vers = vers + versions['v1.0.1']
    elif mess.Content == '#v1.1.0':
        vers = vers + versions['v1.1.0']
    elif mess.Content == '#v1.1.1':
        vers = vers + versions['v1.1.1']
    elif mess.Content == '#v1.1.2':
        vers = vers + versions['v1.1.2']
    else:
        vers = vers + versions[version]
    return vers


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

    def cmd_fudu(self):
        global FuDu
        global FuDuQQG
        if self.ctx.Content == '砸烂复读姬' and self.ctx.FromUserId != self.ctx.CurrentQQ and FuDu == 1:
            FuDuQQG = 0
            FuDu = 0
            tobase = tobase64('look/fudu1.jpg')
            sendMsg.send_pic(self.ctx, '', '', False, False, tobase)
            return
        elif self.ctx.Content == '砸烂复读姬' and FuDu == 0:
            tobase = tobase64('look/fudu2.jpg')
            sendMsg.send_pic(self.ctx, '', '', False, False, tobase)
            return
        elif (self.ctx.Content == '复读姬模式' or self.ctx.Content == '开启复读姬') and self.ctx.FromUserId != self.ctx.CurrentQQ:
            FuDu = 1
            FuDuQQG = self.ctx.FromGroupId
            tobase = tobase64('look/fudu0.jpg')
            sendMsg.send_pic(self.ctx, '', '', False, False, tobase)
            return
        elif FuDu == 1 and (self.ctx.FromUserId != self.ctx.CurrentQQ) and (self.ctx.Content != '复读姬模式') and (
                self.ctx.FromGroupId == FuDuQQG):
            msg = self.ctx.Content
            if self.ctx.MsgType == 'PicMsg':
                # try:
                msg = self.ctx.Content
                PicUrl = self.ctx.PicUrl
                sendMsg.send_pic(self.ctx, msg, PicUrl)
            else:
                sendMsg.send_text(self.ctx, msg)
            return

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
                            sendMsg.send_text(self.ctx, '无此命令')
                            return
                else:
                    sendMsg.send_text(self.ctx, '无此命令')
                    return

            # ------------------更新数据--------------------
            if ret != '':  # 如果有ret
                sendMsg.send_text(self.ctx, ret)
                group_config.update(self.db_raw, Q['GroupId'] == self.db['GroupId'])
            group_config.update(self.db_raw, Q['GroupId'] == self.db['GroupId'])
        else:
            #  if lv == 3:
            #  sendMsg.send_text(self.ctx, '¿没权限玩🐎呢¿')
            sendMsg.send_text(self.ctx, '找不到这个命令了，试试#帮助 吧')
            return

    def cmd(self, group, lv):  # todo 迁移 网易云识别，setu统计，
        if self.ctx.Content == '#sysinfo' or self.ctx.Content == '#运行状态' or self.ctx.Content == '#系统信息':  # 运行状态
            msg = sysinfo()
            sendMsg.send_text(self.ctx, msg)
            return
        elif self.ctx.Content == '#以图搜图':
            pic = PicSearch(self.ctx)
            if self.ctx.PicUrl != '':
                pic.pic_search(self.ctx.PicUrl)
            else:
                sendMsg.send_text(self.ctx, '缺少图片呢')
            return
        elif self.ctx.Content == '#以图搜番':
            pic = PicSearch(self.ctx)
            if self.ctx.PicUrl != '':
                pic.anime_search(self.ctx.PicUrl)
            else:
                sendMsg.send_text(self.ctx, '缺少图片呢')
            return
        elif self.ctx.Content[:2] == '#v':
            msg = send_ver(self.ctx)
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
            tobase = tobase64('look/ouhuang.jpg')
            sendMsg.send_pic(self.ctx, msg, '', False, False, tobase)
            return
        elif self.ctx.Content == '#打赏':
            tobase = tobase64('look/dashang.jpg')
            sendMsg.send_pic(self.ctx, '', '', False, False, tobase)
            tobase = tobase64('look/keai.jpg')
            sendMsg.send_pic(self.ctx, '', '', False, False, tobase)
            return
        elif self.ctx.Content[:3] == '#留言' or self.ctx.Content[:3] == '#ly':
            try:
                msg = '来自：(群{}){}，内容：{}'.format(str(self.ctx.FromGroupId), str(self.ctx.FromUserId), self.ctx.Content)
            except:
                msg = '来自：{}，内容：{}'.format(str(self.ctx.FromUin), self.ctx.Content)
            action.sendFriendText(config['superAdmin'], msg)
            return
        elif self.ctx.Content == '#help' or self.ctx.Content == '#帮助':
            sendMsg.send_pic(self.ctx, '', '', False, False, tobase64('look/help.png'))
            return
        elif group:
            self.cmd_group(lv)
        else:
            sendMsg.send_text(self.ctx, '找不到这个命令了，试试#帮助 吧')

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
