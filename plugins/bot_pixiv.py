import datetime
import json
import os
import re

import botoy.decorators as deco
from botoy import FriendMsg, GroupMsg
from loguru import logger
from pixivpy3 import *

from plugins.ioolib.dbs import config, pixiv_db, Q
from plugins.ioolib.send import Send

_USERNAME = config["pixiv_username"]
_PASSWORD = config["pixiv_password"]
sendMsg = Send()
pixiv_pattern = '#p?(|ixiv) ?(|d) (.+)'


class Pixiv:

    def __init__(self, username, password, id, ctx):
        self.username = username
        self.password = password
        self.id = id
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
    def _get_user(uers):
        user = dict()
        user['id'] = uers['id']
        user['name'] = uers['name']
        return user

    @staticmethod
    def _get_tags(data):
        tags = list()
        for x in data:
            tags.append(x['name'])
        return tags

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

    def get_illust(self):
        pixiv_raw = pixiv_db.search(Q['illust_id'] == self.id)
        if pixiv_raw:
            details = pixiv_raw[0]['details']
        else:
            self.api.login(self.username, self.password)
            json_result = self.api.illust_detail(self.id)
            illust = json_result.illust
            if illust is None:  # 错误报告
                logger.error(json_result['error'])
            details = self._get_details(illust)
            logger.info('ID{}导入到数据库'.format(str(self.id)))
            pixiv_db.insert({'illust_id': self.id, 'details': details,
                             'time': datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')})
        msg = '标题:{}\r\nid {}\r\n类型:{}\r\n作者:{}\r\nid {}\r\n作品说明:{}\r\n发布日期:{}\r\n' \
              '标签:{}\r\n页码:{}\r\n下载图片指令使用：#p d {}'.format(details['title'], str(self.id), details['type'],
                                                         details['user']['name'], details['user']['id'],
                                                         details['caption'],
                                                         details['create_date'], details['tags'],
                                                         details['page_count'], str(self.id))
        sendMsg.send_text(self.ctx, msg)
        for x in range(len(details['urls'])):
            self.api.download(details['urls'][x], path=self.path, fname=str(self.id) + '_' + str(x) + '.jpg')

    def send_original(self):
        pixiv_raw = pixiv_db.search(Q['illust_id'] == self.id)
        if pixiv_raw:
            details = pixiv_raw[0]['details']
            for x in range(len(details['urls'])):
                sendMsg.send_pic(self.ctx, picPath=self.path + '/' + str(self.id) + '_' + str(x) + '.jpg')
        else:
            self.get_illust()
        # time.sleep(3)
        # os.remove(pic_path)


@deco.queued_up
def receive_friend_msg(ctx: FriendMsg):
    pixiv_info = re.match(pixiv_pattern, ctx.Content)
    if pixiv_info:
        if config['pixiv']:
            try:
                if pixiv_info[2]:
                    logger.info('开始搜索')
                    id = int(pixiv_info[3])
                    Pixiv(_USERNAME, _PASSWORD, id, ctx).send_original()
                elif pixiv_info[3]:
                    logger.info('开始下载')
                    id = int(pixiv_info[3])
                    Pixiv(_USERNAME, _PASSWORD, id, ctx).get_illust()
            except Exception as e:
                logger.error(e)
        else:
            logger.error('配置文件未开启pixiv下载功能')
    return


@deco.queued_up
def receive_group_msg(ctx: GroupMsg):
    pixiv_info = re.match(pixiv_pattern, ctx.Content)
    if pixiv_info:
        if config['pixiv']:
            try:
                if pixiv_info[2]:
                    logger.info('开始搜索')
                    id = int(pixiv_info[3])
                    Pixiv(_USERNAME, _PASSWORD, id, ctx).send_original()
                elif pixiv_info[3]:
                    logger.info('开始下载')
                    id = int(pixiv_info[3])
                    Pixiv(_USERNAME, _PASSWORD, id, ctx).get_illust()
            except Exception as e:
                logger.error(e)
        else:
            logger.error('配置文件未开启pixiv下载功能')
    return
