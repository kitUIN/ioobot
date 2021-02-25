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

from plugins.ioolib.dbs import Q, db_tmp, config, group_config, friend_config, Action, pixiv_db, rank
from plugins.ioolib.send import Send

# 本插件基于yuban10703改编 https://github.com/yuban10703/OPQ-SetuBot
# 由于yuban10703咕了很久，本人进行了大量魔改
# ------------------正则------------------
pattern_setu = '来(.*?)[点丶份张幅](.*?)的?(|r18)[色瑟涩🐍][图圖🤮]'
# ---------------------------------------
action = Action(qq=config['BotQQ'])
if config['pixiv'] and config["pixiv_username"] != '' and config["pixiv_password"] != '':
    _USERNAME = config["pixiv_username"]
    _PASSWORD = config["pixiv_password"]
sendMsg = Send()


# ---------------------------------------
class pixivsetu:
    def __init__(self,
                 username,
                 password,
                 ctx
                 ):
        self.username = username
        self.password = password
        self.id = 0
        self.ctx = ctx
        self.path = os.getcwd() + '/pixiv'
        if config['pixiv_proxy']:
            _REQUESTS_KWARGS = {
                'proxies': {
                    'https': config['proxy'],  # 'http://127.0.0.1:10809'  代理
                },
                'verify': True,  # PAPI use https, an easy way is disable requests SSL verify
            }
        else:
            _REQUESTS_KWARGS = {}
        self.refresh_token = config['refresh_token']
        self.access_token = config['access_token']
        self.now = datetime.datetime.now()
        self.api = AppPixivAPI(**_REQUESTS_KWARGS)
        if self.access_token == '' and self.refresh_token == '':  # 保存token
            self.api.login(self.username, self.password)
            logger.info('pixiv——账号登陆')
            if self.api.refresh_token != config['refresh_token'] or self.api.access_token != config['access_token']:
                # 查重
                with open('config.json', 'w', encoding='utf-8') as f:
                    config['refresh_token'] = self.api.refresh_token
                    config['access_token'] = self.api.access_token
                    f.write(json.dumps(config))
                    f.close()
                logger.success('PixivToken重载成功~')
        else:
            self.api.set_auth(config['access_token'], config['refresh_token'])
            logger.info('pixiv——token登陆')

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

    @staticmethod
    def _get_urls(data):
        urls = list()
        if data['page_count'] == 1:
            urls.append(data['meta_single_page']['original_image_url'])
        else:
            for x in data['meta_pages']:
                urls.append(x['image_urls']['original'])
        return urls

    def _get_details(self, data) -> dict:
        details = dict()
        details['id']: str = self.id  # id
        details['title']: str = data['title']  # 标题
        details['type']: str = data['type']  # 种类
        details['caption']: str = data['caption']  # 说明
        details['create_date']: str = data['create_date']  # 创建日期
        details['page_count']: str = data['page_count']  # 页数
        details['user']: dict = self._get_user(data['user'])  # 作者
        details['tags']: list = self._get_tags(data['tags'])  # tag
        details['urls']: list = self._get_urls(data)  # 地址
        return details

    @staticmethod
    def _get_id(illust: list) -> dict:  # 用于查重
        ids = dict()
        try:
            for x in range(len(illust)):
                ids[x] = illust[x]['id']
            return ids
        except:
            pass

    def inform_build(self, date):  # 储存排行榜数据
        json_result = self.api.illust_ranking(mode='day', date=date)

        illusts1 = json_result.illusts
        if illusts1:
            rank.insert({'date': date, 'r18': False, 'illusts': illusts1})
        else:
            logger.error('排行榜加载错误，请检查')
        json_result = self.api.illust_ranking(mode='day_r18', date=date)
        illusts2 = json_result.illusts
        if illusts2:
            rank.insert({'date': date, 'r18': True, 'illusts': illusts2})
        else:
            logger.error('排行榜加载错误，请检查')
    def rank_build(self, num=1):  # 获取排行榜
        now = self.now - datetime.timedelta(days=1)
        date = now.strftime('%Y-%m-%d')
        while num > 0:
            pixiv_raw = rank.search(Q['date'] == date)
            if pixiv_raw:
                now = now - datetime.timedelta(days=1)
                date = now.strftime('%Y-%m-%d')
                logger.info('{}已存在,跳过'.format(date))
            else:
                self.inform_build(date)
                logger.info('{}排行榜导入数据库'.format(date))
                now = now - datetime.timedelta(days=1)
                date = now.strftime('%Y-%m-%d')
                num -= 1

    def illusts_build(self, illusts, retry, r18, flag=False):  # 建立发送数据
        response = list()
        data = dict()
        if r18 >= 1:
            mode = True
        else:
            mode = False
        while len(response) != retry:
            ids = self._get_id(illusts)
            for i in ids:
                pixiv_raw = db_tmp.table('pixivlist').search(Q['illust_id'] == ids[i])
                if pixiv_raw:
                    continue
                else:
                    self.id = ids[i]
                    pic = illusts[i]['image_urls']['square_medium']
                    self.api.download(pic, path=self.path, fname=str(self.id) + '.jpg')
                    details = self._get_details(illusts[i])
                    if r18 < 1 and 'R-18' in details['tags']:
                        continue
                    msg = '标题:{}\r\nid {}\r\n作者:{}\r\nid {}\r\n标签:{}\r\n下载原图指令使用：\r\n#p d {}'.format(
                        details['title'], str(self.id), details['user']['name'], details['user']['id'], details['tags'],
                        str(self.id))
                    data['msg'] = msg
                    data['picPath'] = self.path + '/' + str(self.id) + '.jpg'
                    response.append(data)
                    logger.info('ID{}导入到数据库'.format(str(self.id)))
                    db_tmp.table('pixivlist').insert({'illust_id': self.id, 'details': details,
                                                      'time': datetime.datetime.strftime(self.now,
                                                                                         '%Y-%m-%d %H:%M:%S')})
                    pixiv_db.insert({'illust_id': self.id, 'details': details,
                                     'time': datetime.datetime.strftime(self.now, '%Y-%m-%d %H:%M:%S')})
                    if len(response) == retry:
                        return response
            if flag:
                now = self.now - datetime.timedelta(days=1)
                date = now.strftime('%Y-%m-%d')
                illust = rank.search((Q['date'] == date) & (Q['r18'] == mode))
                illusts = illust[0]['illusts']
                self.rank_build()
        return response

    def retry_send1(self, tag, retry, r18):  # 发送主体1(循环)
        if r18 >= 1:
            tag += ' R-18'
        logger.debug('搜索标签:{}'.format(tag))
        json_result = self.api.search_illust(tag, search_target='exact_match_for_tags')
        illusts = json_result.illusts
        if illusts is None:  # 错误报告
            logger.error(json_result['error'])
            return
        return self.illusts_build(illusts, retry, r18)

    def retry_send2(self, retry, r18):  # 发送主体2(循环)
        if r18 >= 1:
            mode = True
        else:
            mode = False
        now = self.now - datetime.timedelta(days=1)
        date = now.strftime('%Y-%m-%d')
        illust = rank.search((Q['date'] == date) & (Q['r18'] == mode))
        if illust:
            illusts = illust[0]['illusts']
            response = self.illusts_build(illusts, retry, r18, True)
            return response
        elif illust is not None:
            self.rank_build()
            illust = rank.search((Q['date'] == date) & (Q['r18'] == mode))
            illusts = illust[0]['illusts']
            return self.illusts_build(illusts, retry, r18, True)

    def send_pixiv(self, tags=None, r18=0, retry=1):
        logger.debug(tags)
        tag = ''
        if tags:  # 有标签
            for x in tags:
                tag += x + ' '
            tag = tag[:len(tag) - 1]
            logger.debug(tags)
            logger.debug('tags:' + tag)
            data = self.retry_send1(tag, retry, r18)
        else:
            data = self.retry_send2(retry, r18)
        return data


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

    def build_msg(self,
                  level,
                  title='',
                  artworkid=0,
                  author='',
                  artistid=0,
                  page=1,
                  url_original=''):
        if level == 'api0':  # yande.re
            msg = '标题:{title}\r\n作者:{author}\r\n原图:{url_original}\r\n(需要科学上网)'.format(
                title=title,
                author=author,
                url_original=url_original
            )
        else:
            msg = 'msg配置错误,请联系管理员'
            return msg
        if self.db_config['type'] == 'group':
            if self.db_config['revoke']:  # 群聊并且开启撤回
                msg += '\r\nREVOKE[{}]'.format(self.db_config['revoke'])
            if self.db_config['at']:
                return '\r\n' + msg
        return msg

    def if_sent(self, id):  # 判断是否发送过
        data = db_tmp.table('sentlist').search((Q['id'] == self.db_config['callid']) & (Q['pic_id'] == id))
        if data:  # 如果有数据
            if time.time() - data[0]['time'] <= self.db_config['clearSentTime']:  # 发送过
                logger.info('群{},id:{}发送过~'.format(self.db_config['callid'], id))
                return True
            else:
                db_tmp.table('sentlist').update({'time': time.time()},
                                                (Q['id'] == self.db_config['callid']) & (Q['pic_id'] == id))
                return False
        else:  # 没数据
            db_tmp.table('sentlist').insert({'id': self.db_config['callid'], 'time': time.time(), 'pic_id': id})
            return False

    def api_0(self):  # https://yande.re/ 速度极其慢，不建议使用
        url = 'https://yande.re/post.json'
        if config['yanre_proxy']:
            _REQUESTS_KWARGS = {
                'proxies': {
                    'https': config['proxy'],  # 'http://127.0.0.1:10809'  代理
                }
            }
        else:
            _REQUESTS_KWARGS = dict()
        if len(self.tag) > 0:
            tag_switch = 1
        else:
            tag_switch = 0
        params = {'api_version': 2,
                  'tags': self.tag,
                  'limit': self.num,
                  'include_tags': tag_switch,
                  'filter': 1}
        if self.num > 10:  # api限制不能大于10
            params['num'] = 10
        try:
            res = requests.get(url, params, **_REQUESTS_KWARGS)
            setu_data = res.json()
        except Exception as e:
            logger.error('api0 boom~')
            logger.error(e)
        else:
            if res.status_code == 200:
                for data in setu_data['posts']:
                    id = data['id']
                    file_url = data['file_url']
                    if self.if_sent(id):  # 判断是否发送过
                        continue
                    url_original = data['source']
                    msg = self.build_msg(level='api0', title=data['tags'], author=data['author'],
                                         url_original=url_original)
                    with requests.get(file_url, **_REQUESTS_KWARGS) as resp:
                        with open('./tmp.jpg', 'wb') as fd:
                            fd.write(resp.content)
                    sendMsg.send_pic(self.ctx, msg, picPath='./tmp.jpg')
                    self.api_0_realnum += 1
                # else:
                #     logger.warning('api0:{}'.format(res.status_code))
            logger.info(
                '从yandeのapi获取到{}张setu  实际发送{}张'.format(len(setu_data['posts']), self.api_0_realnum))  # 打印获取到多少条

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

    def api_2(self):  # pixiv
        self.api_pixiv_toget_num = self.num - self.api_0_realnum - self.api_1_realnum  # 兼容api1 兼容api0
        if self.api_pixiv_toget_num <= 0:
            return
        if self.setu_level == 1:
            r18 = 0
        elif self.setu_level == 3:
            r18 = random.choice([0, 1])
        elif self.setu_level == 2:
            r18 = 1
        else:
            r18 = 0
        if not config['pixiv']:
            return
        api2 = pixivsetu(_USERNAME, _PASSWORD, self.ctx)
        if len(self.tag) != 1 or (len(self.tag[0]) != 0 and not self.tag[0].isspace()):  # 如果tag不为空(字符串字数不为零且不为空)
            tags = self.tag
        else:
            tags = []
        logger.debug(tags)
        data = api2.send_pixiv(tags, r18, self.api_pixiv_toget_num)
        if data:
            for i in data:
                if self.db_config['type'] == 'group':
                    if self.db_config['revoke']:  # 群聊并且开启撤回
                        i['msg'] += '\r\nREVOKE[{}]'.format(self.db_config['revoke'])
                    if self.db_config['at']:
                        i['msg'] = '\r\n' + i['msg']
                sendMsg.send_pic(self.ctx, text=i['msg'], picPath=i['picPath'], atUser=self.db_config['at'])
                self.api_pixiv_realnum += 1
        else:
            logger.error('无返回数据')
        logger.info('向Pixivのapi请求发送{}张,实际发送{}'.format(self.api_pixiv_toget_num, self.api_pixiv_realnum))

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
                'setuDefaultLevel': 3,
                'original': False,
                'clearSentTime': 36000,
                'at': False,
                'at_warning': False,  # @
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
        if config["yanre_switch"]:
            self.api_0()
        if config['Lolicon_switch'] and len(self.tag) == 1:
            self.api_1()
        self.api_2()
        if self.api_0_realnum == 0 and self.api_1_realnum == 0 and self.api_pixiv_realnum == 0:
            sendMsg.send_text(self.ctx, self.db_config['msg_notFind'], self.db_config['at_warning'])
            return
        return


# ------------------------------权限db-------------
class Getdata:
    @staticmethod
    def defaultdata(data):
        data['managers'] = []  # 所有的管理者(可以设置bot功能的)
        # -----------------------------------------------------
        data['setuDefaultLevel'] = {'group': 1, 'temp': 3}  # 默认等级 0:正常 1:性感 2:色情 3:All
        data['original'] = {'group': False, 'temp': False}  # 是否原图
        data['setu'] = {'group': True, 'temp': True}  # 色图功能开关
        data['r18'] = {'group': False, 'temp': True}  # 是否开启r18
        data['freq'] = 0  # 频率 (次)
        data['refreshTime'] = 60  # 刷新时间 (s)
        data['clearSentTime'] = 36000  # 刷新sent时间 (s)
        data['maxnum'] = {'group': 3, 'temp': 10}  # 一次最多数量
        # data['MsgCount'] = {'text': 0, 'pic': 0, 'voice': 0}  # 消息数量
        data['revoke'] = {'group': 20, 'temp': 0}  # 撤回消息延时(0为不撤回)
        data['at'] = False  # @
        data['at_warning'] = False  # @
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
def receive_group_msg(ctx: GroupMsg):
    group_info = re.search(pattern_setu, ctx.Content)  # 提取关键字
    delay = re.search('REVOKE\[(.*?)\]', ctx.Content)
    if group_info:
        Setu(ctx, group_info[2], group_info[1], group_info[3]).main()
        logger.debug(group_info[2])
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
