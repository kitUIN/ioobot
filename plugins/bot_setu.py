import datetime
import json
import os
import random
import re
import time

import botoy.decorators as deco
import requests
from botoy import FriendMsg, GroupMsg, EventMsg
from botoy.refine import refine_group_admin_event_msg, refine_group_join_event_msg
from loguru import logger
from pixivpy3 import *
from retrying import retry
from tinydb.operations import add

from plugins.ioolib.dbs import Q, db_tmp, config, group_config, friend_config, Action, pixiv_db
from plugins.ioolib.send import Send

# ------------------正则------------------
pattern_setu = '来(.*?)[点丶份张幅](.*?)的?(|r18)[色瑟涩🐍][图圖🤮]'
# ---------------------------------------
sendMsg = Send()
action = Action(qq=config['BotQQ'])


# ---------------------------------------
class pixivsetu:
    def __init__(self, username, password, ctx, tags=None):
        if tags is None:
            tags = list()
        self.username = username
        self.password = password
        self.tags = tags
        self.id = 0
        self.ctx = ctx
        self.path = os.getcwd() + '/pixiv'
        if config['pixiv']:
            _REQUESTS_KWARGS = {
                'proxies': {
                    'https': config['proxy'],  # 'http://127.0.0.1:10809'  代理
                },
                'verify': True,  # PAPI use https, an easy way is disable requests SSL verify
            }
        else:
            _REQUESTS_KWARGS = {}
        self.api = AppPixivAPI(**_REQUESTS_KWARGS)
        if config['refresh_token'] in vars() or config['access_token'] in vars():  # 保存token
            try:
                self.api.set_auth(config['access_token'], config['refresh_token'])
                if not (config['refresh_token'] in vars() or config['access_token'] in vars()) or (
                        self.api.refresh_token != config['refresh_token'] or self.api.access_token != config[
                    'access_token']):
                    # 查重
                    with open('config.json', 'wr', encoding='utf-8') as f:
                        tmpc = json.loads(f.read())
                        tmpc['refresh_token'] = self.api.refresh_token
                        tmpc['access_token'] = self.api.access_token
                    f.write(tmpc)
                    logger.success('PixivToken保存成功~')
                f.close()
            except PixivError:
                self.api.login(self.username, self.password)
        else:
            self.api.login(self.username, self.password)

    @staticmethod
    def _get_tags(data):
        tags = list()
        for x in data:
            tags.append(x['name'])
        return tags

    @staticmethod
    def _get_user(uers):
        user = dict()
        user['id'] = uers['id']
        user['name'] = uers['name']
        return user

    def _get_details(self, data) -> dict:
        details = dict()
        details['id']: str = self.id  # id
        details['title']: str = data['title']  # 标题
        details['create_date']: str = data['create_date']  # 创建日期
        details['user']: dict = self._get_user(data['user'])  # 作者
        details['tags']: list = self._get_tags(data['tags'])  # tag
        return details

    @staticmethod
    def _get_id(illust: list) -> dict:  # 用于查重
        ids = dict()
        for x in range(len(illust)):
            ids[x] = illust[x]['id']
        return ids

    def send_pixiv(self):
        if self.tags != []:  # 有标签
            json_result = self.api.search_illust(self.tags)
            illusts = json_result.illusts
            if illusts is None:  # 错误报告
                logger.error(json_result['error'])
            ids = self._get_id(illusts)
            for i in ids:
                pixiv_raw = pixiv_db.search(Q['illust_id'] == ids[i])
                if pixiv_raw:
                    continue
                else:
                    self.id = int(ids[i])
                    pic = illusts[i]['image_urls']['square_medium']
                    self.api.download(pic, path=self.path, fname=str(self.id) + '.jpg')
                    details = self._get_details(illusts[i])
                    msg = '标题:{}\r\nid {}\r\n作者:{}\r\nid {}\r\n \'标签:{}\r\n下载图片指令使用：p d {}'.format(details['title'],
                                                                                                   str(self.id),
                                                                                                   details['user'][
                                                                                                       'name'],
                                                                                                   details['user'][
                                                                                                       'id'],
                                                                                                   details['tags'],
                                                                                                   str(self.id))

                    sendMsg.send_pic(self.ctx, text=msg, picPath=self.path + '/' + ids[i] + '.jpg')
                    logger.info('ID{}导入到数据库'.format(str(self.id)))
                    pixiv_db.insert({'illust_id': self.id, 'details': details,
                                     'time': datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')})
                    return


        else:
            # t =self.api.illust_ranking()
            # sendMsg.send_pic(self.ctx, picPath=self.path + '/' + str(self.id) + '.jpg')
            # todo rank
            pass


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
                            sendMsg.send_pic(self.ctx, msg, url_original, flashPic=False, atUser=self.db_config['at'])
                        else:
                            sendMsg.send_pic(self.ctx, msg, 'https://cdn.jsdelivr.net/gh/laosepi/setu/pics/' + filename,
                                             flashPic=False, atUser=self.db_config['at'])
                    else:  # 本地base64
                        sendMsg.send_pic(self.ctx, msg, '', config['path'] + filename, False,
                                         self.db_config['at'])
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
                    sendMsg.send_pic(self.ctx, msg, data['url'], flashPic=False, atUser=self.db_config['at'])
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


# ------------------------------权限db-------------
class Getdata:
    @staticmethod
    def defaultdata(data):
        data['managers'] = []  # 所有的管理者(可以设置bot功能的)
        # -----------------------------------------------------
        data['setuDefaultLevel'] = {'group': 1, 'temp': 3}  # 默认等级 0:正常 1:性感 2:色情 3:All
        data['setuinfoLevel'] = {'group': 2, 'temp': 3}  # setu信息完整度(0:不显示图片信息)
        data['original'] = {'group': False, 'temp': False}  # 是否原图
        data['setu'] = {'group': True, 'temp': True}  # 色图功能开关
        data['r18'] = {'group': False, 'temp': True}  # 是否开启r18
        data['freq'] = 0  # 频率 (次)
        data['refreshTime'] = 60  # 刷新时间 (s)
        data['clearSentTime'] = 900  # 刷新sent时间 (s)
        data['maxnum'] = {'group': 3, 'temp': 10}  # 一次最多数量
        # data['MsgCount'] = {'text': 0, 'pic': 0, 'voice': 0}  # 消息数量
        data['revoke'] = {'group': 20, 'temp': 0}  # 撤回消息延时(0为不撤回)
        data['at'] = False  # @
        data['at_warning'] = False  # @
        data['showTag'] = True  # 显示tag
        data['msg_inputError'] = '必须是小于3的数字哦~'  # 非int
        data['msg_notFind'] = '淦 你的xp好奇怪啊'  # 没结果
        data['msg_tooMuch'] = '要这么多色图你怎么不冲死呢¿'  # 大于最大值
        data['msg_lessThan0'] = '¿¿¿'  # 小于0
        data['msg_setuClosed'] = 'setu已关闭~'
        data['msg_r18Closed'] = '未开启r18~'
        data['msg_insufficient'] = '关于{tag}的图片只获取到{num}张'
        data['msg_frequency'] = '本群每{time}s能调用{num}次,已经调用{num_call}次,离刷新还有{r_time}s'
        # data['msg_'] = ''
        # return data

    def _updateData(self, data, group_id):
        if group_config.search(Q['GroupId'] == group_id):
            logger.info('群:{}已存在,更新数据~'.format(group_id))
            group_config.update(data, Q['GroupId'] == group_id)
        else:
            self.defaultdata(data)
            logger.info('群:{}不存在,插入数据~'.format(group_id))
            group_config.insert(data)

    @retry(stop_max_attempt_number=3, wait_random_max=2000)
    def updateAllGroupData(self):
        logger.info('开始更新所有群数据~')
        data = action.getGroupList()
        allgroups_get = [x['GroupId'] for x in data]
        for group in data:
            del group['GroupNotice']  # 删除不需要的key
            admins = action.getGroupAdminList(group['GroupId'])
            admins_QQid = [i['MemberUin'] for i in admins]
            group['admins'] = admins_QQid  # 管理员列表
            self._updateData(group, group['GroupId'])
        allgroups_db = [i['GroupId'] for i in group_config.all()]
        extraGroup = list(set(allgroups_db).difference(set(allgroups_get)))
        if extraGroup:  # 多余的群
            logger.info('数据库中多余群:{}'.format(extraGroup))
            for groupid_del in extraGroup:
                group_config.remove(Q['GroupId'] == groupid_del)
                logger.info('已删除群:{}数据'.format(groupid_del))
        logger.success('更新群信息成功~')
        return

    @retry(stop_max_attempt_number=3, wait_random_max=2000)
    def updateGroupData(self, group_id: int):
        logger.info('开始刷新群:{}的数据'.format(group_id))
        data = action.getGroupList()
        for group in data:
            if group['GroupId'] == group_id:
                del group['GroupNotice']  # 删除不需要的key
                admins = action.getGroupAdminList(group_id)
                admins_QQid = [i['MemberUin'] for i in admins]
                group['admins'] = admins_QQid
                logger.info('群:{}的admins:{}'.format(group_id, admins_QQid))
                self._updateData(group, group['GroupId'])
                return
        logger.warning('群:{}不存在~'.format(group_id))


# --------------指令-------------------------
@deco.queued_up
@deco.ignore_botself
def receive_friend_msg(ctx: FriendMsg):
    if not (ctx.Content is None):
        friend_info = re.search(pattern_setu, ctx.Content)  # 提取关键字
        if friend_info:
            Setu(ctx, friend_info[2], friend_info[1], friend_info[3]).main()


@deco.queued_up
@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    group_info = re.search(pattern_setu, ctx.Content)  # 提取关键字
    delay = re.search('REVOKE\[(.*?)\]', ctx.Content)
    if group_info:
        Setu(ctx, group_info[2], group_info[1], group_info[3]).main()
    if delay:
        delay = min(int(delay[1]), 90)
        time.sleep(delay)
        action.revokeGroupMsg(ctx.FromGroupId, ctx.MsgSeq, ctx.MsgRandom)


botdata = Getdata()


# -----------------------权限信息通知-----------------------------------------------
def receive_events(ctx: EventMsg):
    admin_info = refine_group_admin_event_msg(ctx)
    join_info = refine_group_join_event_msg(ctx)
    if admin_info:
        data_raw = group_config.search(Q['GroupId'] == admin_info.GroupID)
        if data_raw:
            if admin_info.Flag == 1:  # 变成管理员
                logger.info('群:{} QQ:{}成为管理员'.format(admin_info.GroupID, admin_info.UserID))
                if admin_info.UserID in data_raw[0]['managers']:  # 防止重叠
                    data_raw[0]['managers'].remove(admin_info.UserID)
                data_raw[0]['admins'].append(admin_info.UserID)
            else:
                logger.info('群:{} QQ:{}被取消管理员'.format(admin_info.GroupID, admin_info.UserID))
                try:
                    data_raw[0]['admins'].remove(admin_info.UserID)
                except Exception as e:  # 出错就说明群信息不正确,重新获取
                    logger.warning('从数据库删除管理员出错,尝试重新刷新群数据\r\n' + str(e))
                    botdata.updateGroupData(admin_info.GroupID)
                    return
            group_config.update({'admins': data_raw[0]['admins'],
                                 'managers': data_raw[0]['managers']},
                                Q['GroupId'] == admin_info.GroupID)
        else:  # 如果没数据就重新获取
            botdata.updateGroupData(admin_info.GroupID)
    elif join_info:
        if join_info.UserID == config['BotQQ']:
            logger.info('bot加入群{}'.format(join_info.FromUin))
            botdata.updateGroupData(join_info.FromUin)
        else:
            logger.info('{}:{}加入群{}'.format(join_info.UserName, join_info.UserID, join_info.FromUin))
    elif ctx.MsgType == 'ON_EVENT_GROUP_JOIN_SUCC':
        logger.info('bot加入群{}'.format(ctx.FromUin))
        botdata.updateGroupData(ctx.FromUin)
