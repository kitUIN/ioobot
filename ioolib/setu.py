import base64
import os
import random
import re
import time

import requests
from tinydb.operations import add

from .dbs import *
from .message import Send

sendMsg = Send()


class Setu:
    def __init__(self, ctx, tag, num, whether_r18):
        self.ctx = ctx
        self.num = num
        self.tag = [i for i in list(set(re.split(r',|，|\.|-| |_|/|\\', tag))) if i != '']  # 分割tag+去重+去除空元素
        # -----------------------------------
        self.setu_level = 1
        self.r18_OnOff_keyword = whether_r18  # 是否r18
        self.api_0_realnum = 0
        self.api_1_realnum = 0
        self.api_pixiv_realnum = 0
        self.api1_toget_num = 0
        self.api_pixiv_toget_num = 0
        self.db_config = {}

    def build_msg(self, title, artworkid, author, artistid, page, url_original):
        if self.db_config['setuinfoLevel'] == 0:
            msg = ''
        elif self.db_config['setuinfoLevel'] == 1:
            msg = '作品id:{}\r\n作者id:{}\r\nP:{}'.format(artworkid, artistid, page)
        elif self.db_config['setuinfoLevel'] == 2:
            msg = '作品:{}\r\n作者:{}\r\nP:{}\r\n原图:{}'.format(
                'www.pixiv.net/artworks/' + str(artworkid),
                'www.pixiv.net/users/' + str(artistid),
                page,
                url_original
            )
        elif self.db_config['setuinfoLevel'] == 3:
            msg = '标题:{title}\r\n{purl}\r\npage:{page}\r\n作者:{author}\r\n{uurl}\r\n原图:{url_original}'.format(
                title=title,
                purl='www.pixiv.net/artworks/' + str(artworkid),
                page=page,
                author=author,
                uurl='www.pixiv.net/users/' + str(artistid),
                url_original=url_original
            )
        else:
            msg = 'msg配置错误,请联系管理员'
            return msg
        if self.db_config['showTag'] and len(self.tag) >= 1:  # 显示tag
            msg += '\r\nTAG:{}'.format(self.tag)
        if self.db_config['type'] == 'group':
            if self.db_config['revoke']:  # 群聊并且开启撤回
                msg += '\r\nREVOKE[{}]'.format(self.db_config['revoke'])
            if self.db_config['at']:
                return '\r\n' + msg
        return msg

    def base_64(self, path):
        try:
            with open(path, 'rb') as f:
                code = base64.b64encode(f.read()).decode()  # 读取文件内容，转换为base64编码
                logger.info('本地base64转码~')
                return code
        except:
            logger.error('路径{} ,base64转码出错,检查图片路径~'.format(path))
            return

    def if_sent(self, url):  # 判断是否发送过
        filename = os.path.basename(url)
        data = db_tmp.table('sentlist').search((Q['id'] == self.db_config['callid']) & (Q['filename'] == filename))
        if data:  # 如果有数据
            if time.time() - data[0]['time'] <= self.db_config['clearSentTime']:  # 发送过
                logger.info('id:{},{}发送过~'.format(self.db_config['callid'], filename))
                return True
            else:
                db_tmp.table('sentlist').update({'time': time.time()},
                                                (Q['id'] == self.db_config['callid']) & (Q['filename'] == filename))
                return False
        else:  # 没数据
            db_tmp.table('sentlist').insert({'id': self.db_config['callid'], 'time': time.time(), 'filename': filename})
            return False

    def api_0(self):
        url = 'http://api.yuban10703.xyz:2333/setu_v4'
        params = {'level': self.setu_level,
                  'num': self.num,
                  'tag': self.tag}
        if self.num > 10:  # api限制不能大于10
            params['num'] = 10
        try:
            res = requests.get(url, params)
            setu_data = res.json()
        except Exception as e:
            logger.error('api0 boom~')
            logger.error(e)
        else:
            if res.status_code == 200:
                for data in setu_data['data']:
                    filename = data['filename']
                    if self.if_sent('https://cdn.jsdelivr.net/gh/laosepi/setu/pics_original/' + filename):  # 判断是否发送过
                        continue
                    url_original = 'https://cdn.jsdelivr.net/gh/laosepi/setu/pics_original/' + filename
                    msg = self.build_msg(data['title'], data['artwork'], data['author'], data['artist'],
                                         data['page'], url_original)
                    if config['path'] == '':
                        if self.db_config['original']:
                            sendMsg.send_pic(self.ctx, msg, url_original, False, self.db_config['at'])
                        else:
                            sendMsg.send_pic(self.ctx, msg, 'https://cdn.jsdelivr.net/gh/laosepi/setu/pics/' + filename,
                                             False, self.db_config['at'])
                    else:  # 本地base64
                        sendMsg.send_pic(self.ctx, msg, '', False, self.db_config['at'],
                                         self.base_64(config['path'] + filename))
                    self.api_0_realnum += 1
                # else:
                #     logger.warning('api0:{}'.format(res.status_code))
            logger.info(
                '从yubanのapi获取到{}张setu  实际发送{}张'.format(setu_data['count'], self.api_0_realnum))  # 打印获取到多少条

    def api_1(self):
        self.api1_toget_num = self.num - self.api_0_realnum
        # 兼容api0
        if self.api1_toget_num <= 0:
            return
        if self.setu_level == 1:
            r18 = 0
        elif self.setu_level == 3:
            r18 = random.choice([0, 1])
        elif self.setu_level == 2:
            r18 = 1
        else:
            r18 = 0
        url = 'https://api.lolicon.app/setu'
        params = {'r18': r18,
                  'apikey': config['LoliconAPIKey'],
                  'num': self.api1_toget_num,
                  'size1200': not bool(self.db_config['original'])}
        if len(self.tag) != 1 or (len(self.tag[0]) != 0 and not self.tag[0].isspace()):  # 如果tag不为空(字符串字数不为零且不为空)
            params['keyword'] = self.tag
        try:
            res = requests.get(url, params)
            setu_data = res.json()
        except Exception as e:
            logger.error('api1 boom~')
            logger.error(e)
        else:
            if res.status_code == 200:
                for data in setu_data['data']:
                    if self.if_sent(data['url']):  # 判断是否发送过
                        continue
                    msg = self.build_msg(data['title'], data['pid'], data['author'], data['uid'], data['p'], '无~')
                    logger.info(msg)
                    logger.info(data['url'])
                    sendMsg.send_pic(self.ctx, msg, data['url'], False, self.db_config['at'])
                    self.api_1_realnum += 1
                logger.info(
                    '从loliconのapi获取到{}张setu  实际发送{}张'.format(setu_data['count'], self.api_1_realnum))
                # 打印获取到多少条
            else:
                logger.warning('api1:{}'.format(res.status_code))

    def _freq(func):
        def wrapper(self, *args, **kwargs):
            if self.ctx.__class__.__name__ == 'GroupMsg':  # 群聊
                # ------------------------------------------------------------------------
                data_tmp = db_tmp.table('freq').search(Q['group'] == self.ctx.FromGroupId)
                if data_tmp:  # 如果有数据
                    if self.db_config['refreshTime'] != 0 and (
                            time.time() - data_tmp[0]['time'] >= self.db_config['refreshTime']):  # 刷新
                        db_tmp.table('freq').update({'time': time.time(), 'freq': 0},
                                                    Q['group'] == self.ctx.FromGroupId)
                    elif self.db_config['freq'] != 0 and self.num + data_tmp[0]['freq'] > self.db_config[
                        'freq']:  # 大于限制且不为0
                        logger.info('群:{}大于频率限制:{}次/{}s'.format(self.ctx.FromGroupId, self.db_config['freq'],
                                                                self.db_config['refreshTime']))
                        msg = self.db_config['msg_frequency'].format(
                            time=self.db_config['refreshTime'],
                            num=self.db_config['freq'],
                            num_call=data_tmp[0]['freq'],
                            r_time=round(self.db_config['refreshTime'] - (time.time() - data_tmp[0]['time']))
                        )
                        sendMsg.send_text(self.ctx, msg, self.db_config['at_warning'])
                        return
                    # 记录
                    db_tmp.table('freq').update(add('freq', self.num), Q['group'] == self.ctx.FromGroupId)
                else:  # 没数据
                    logger.info('群:{}第一次调用'.format(self.ctx.FromGroupId))
                    db_tmp.table('freq').insert(
                        {'group': self.ctx.FromGroupId, 'time': time.time(), 'freq': self.num})
            func(self, *args, **kwargs)

        return wrapper

    def processing_and_inspect(self):  # 处理消息+调用
        # -----------------------------------------------
        if self.num == '一' or self.num == '':
            self.num = 1
        elif self.num == '二' or self.num == '俩' or self.num == '两':
            self.num = 2
        elif self.num == '三':
            self.num = 3
        elif self.num != '':
            # 如果指定了数量
            try:
                self.num = int(self.num)
            except:  # 出错就说明不是数字
                sendMsg.send_text(self.ctx, self.db_config['msg_inputError'], self.db_config['at_warning'])
                return
            if self.num <= 0:  # ?????
                sendMsg.send_text(self.ctx, self.db_config['msg_lessThan0'], self.db_config['at_warning'])
                return
        else:  # 未指定默认1
            self.num = 1
        # -----------------------------------------------
        self.setu_level = self.db_config['setuDefaultLevel']  # 默认色图等级
        # -----------------------------------------------
        if self.db_config['type'] in ['group', 'temp']:
            if not self.db_config['setu']:
                sendMsg.send_text(self.ctx, self.db_config['msg_setuClosed'], self.db_config['at_warning'])
                return
            if self.num > self.db_config['maxnum']:
                sendMsg.send_text(self.ctx, self.db_config['msg_tooMuch'], self.db_config['at_warning'])
                return
            if self.r18_OnOff_keyword != '':
                if self.db_config['r18']:
                    self.setu_level = 2
                else:
                    sendMsg.send_text(self.ctx, self.db_config['msg_r18Closed'], self.db_config['at_warning'])
                    return
        elif self.db_config['type'] == 'friend':
            if self.r18_OnOff_keyword != '':
                self.setu_level = 2
        self.send()

    def group_or_temp(self):  # 读数据库+鉴权+判断开关
        if self.ctx.__class__.__name__ == 'GroupMsg':  # 群聊
            # group_id = self.ctx.FromGroupId
            self.db_config['type'] = 'group'
            self.db_config['callqq'] = self.ctx.FromUserId
            self.db_config['callid'] = self.ctx.FromGroupId
        elif self.ctx.MsgType == 'TempSessionMsg':  # 临时会话
            # group_id = self.ctx.TempUin
            self.db_config['callqq'] = self.ctx.FromUin
            self.db_config['callid'] = self.ctx.TempUin
            self.db_config['type'] = 'temp'
        data = group_config.search(Q['GroupId'] == self.db_config['callid'])
        if data:  # 查询group数据库数据
            for key, value in data[0].items():
                if type(value) == dict and key != 'MsgCount':
                    self.db_config[key] = value[self.db_config['type']]
                    continue
                self.db_config[key] = value
            # self.tag = TagMapping().replace_tags(self.db_config['callid'], self.db_config['callqq'], self.tag)  # 替换tag
            self.processing_and_inspect()
        else:
            sendMsg.send_text(self.ctx, '数据库无群:{}信息,请联系管理员~'.format(self.db_config['callid']))
            logger.error('数据库无群:{}信息'.format(self.db_config['callid']))
            return

    def friend(self):
        self.db_config['type'] = 'friend'
        self.db_config['callqq'] = self.ctx.FromUin
        self.db_config['callid'] = self.ctx.FromUin
        data = friend_config.search(Q['QQ'] == self.ctx.FromUin)
        if data:  # 该QQ如果自定义过
            self.db_config.update(data[0])
            self.processing_and_inspect()
        else:  # 如果没有自定义 就是默认行为
            # pass#
            self.db_config.update({
                'setuinfoLevel': 3,
                'original': False,
                'setuDefaultLevel': 1,
                'clearSentTime': 600,
                'at': False,
                'at_warning': False,  # @
                'showTag': True,
                'msg_inputError': '必须是小于3的数字哦~',  # 非int
                'msg_notFind': '淦 你的xp好奇怪啊',  # 没结果
                'msg_tooMuch': '要这么多色图你怎么不冲死呢¿',  # 大于最大值
                'msg_lessThan0': '¿¿¿',  # 小于0
                'msg_setuClosed': 'setu已关闭~',
                'msg_r18Closed': '未开启r18~',
                'msg_insufficient': '关于{tag}的图片只获取到{num}张'
            })
            self.processing_and_inspect()

    def main(self):  # 判断消息类型给对应函数处理
        if self.ctx.__class__.__name__ == 'GroupMsg' or self.ctx.MsgType == 'TempSessionMsg':  # 群聊or临时会话
            self.group_or_temp()
        else:  # 好友会话
            self.friend()

    @_freq  # 频率
    def send(self):  # 判断数量
        self.api_0()
        if len(self.tag) == 1:
            self.api_1()
        if self.api_0_realnum == 0 and self.api_1_realnum == 0 and self.api_pixiv_realnum == 0:
            sendMsg.send_text(self.ctx, self.db_config['msg_notFind'], self.db_config['at_warning'])
            return
        if self.api_pixiv_realnum < self.api_pixiv_toget_num:
            sendMsg.send_text(self.ctx, self.db_config['msg_insufficient'].format(
                tag=self.tag,
                num=self.api_0_realnum + self.api_1_realnum + self.api_pixiv_realnum
            ), self.db_config['at_warning'])
