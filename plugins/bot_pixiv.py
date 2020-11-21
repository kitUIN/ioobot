import datetime
import os
import re

import botoy.decorators as deco
from botoy import FriendMsg, GroupMsg
from loguru import logger
from pixivpy3 import *

from plugins.ioolib.dbs import config, pixiv_db, Q
from plugins.ioolib.send import Send

_USERNAME = config["netease_username"]
_PASSWORD = config["netease_password"]
sendMsg = Send()
pixiv_pattern = '#p?(|ixiv) ?(|d) (.+)'


class Pixiv:  # todo pixiv图片信息，已下载查询

    def __init__(self, username, password, id, ctx):
        self.username = username
        self.password = password
        self.id = id
        self.ctx = ctx
        self.path = os.getcwd() + '/pixiv'
        self.filename = self.path + '/' + str(self.id) + '.jpg'
        _REQUESTS_KWARGS = {
            'proxies': {
                'https': 'http://127.0.0.1:10809',  # 代理
            },
            'verify': True,  # PAPI use https, an easy way is disable requests SSL verify
        }
        self.api = AppPixivAPI(**_REQUESTS_KWARGS)

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
            tags.append(data[x]['name'])
        return tags

    @staticmethod
    def _get_urls(data):
        urls = list()
        if data['page_count'] == 1:
            urls.append(data['meta_single_page']['original_image_url'])
        else:
            for x in data['meta_pages']:
                urls.append(data['meta_pages'][x]['original'])
        return urls

    def _get_details(self, data) -> dict:
        details = dict()
        details['id']: str = self.id  # id
        details['title']: str = data['title']  # 标题
        details['type']: str = data['type']  # 种类
        details['caption']: str = data['caption']  # 说明
        details['create_date']: str = data['create_date']  # 创建日期
        details['page_count']: str = data['page_count']  # 页数
        details['user']: dict = self._get_user(data['user'])
        details['tags']: list = self._get_tags(data['tags'])  # tag
        details['urls']: list = self._get_urls(data)
        return details

    def get_illust(self):
        pixiv_raw = pixiv_db.search(Q['illust_id'] == self.id)
        if pixiv_raw:
            details = pixiv_raw['details']
        else:
            self.api.login(self.username, self.password)
            json_result = self.api.illust_detail(self.id)
            illust = json_result.illust
            if illust is None:  # 错误报告
                logger.error(json_result['error'])
            details = self._get_details(illust)
            logger.info('ID{}导入到数据库'.format(self.id))
            pixiv_db.insert({'illust_id': self.id, 'details': details,
                             'time': datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')})
        msg = '标题:{}(id{})(类型:{})\r\n作者:{}(id{})\r\n作品说明:{}\r\n发布日期:{}\r\n' \
              '标签:{}\r\n页码:{}(使用#p d {}下载图片)'.format(details['title'], self.id, details['type'],
                                                     details['user']['name'], details['user']['id'], details['caption'],
                                                     details['tags'],
                                                     details['create_date'], details['page_count'], self.id)
        sendMsg.send_text(self.ctx,msg)

    def _download_illust(self):
        # self.api.download(self.get_illust(), path=self.path, fname=self.id + '.jpg')
        pass

    def _search(self):
        pass

    def send_original(self):
        pixiv_raw = pixiv_db.search(Q['illust_id'] == self.id)
        if pixiv_raw:
            details = pixiv_raw['details']
            for x in details['urls']:
                sendMsg.send_pic(self.ctx,picUrl=details['urls'][x])
        else:
            sendMsg.send_text(self.ctx,'请先使用#p {}'.format(self.id))
        # time.sleep(3)
        # os.remove(pic_path)


@deco.in_content('#')
def receive_friend_msg(ctx: FriendMsg):
    pixiv_info = re.match(pixiv_pattern, ctx.Content)
    logger.info(pixiv_info)
    if pixiv_info:
        if config['pixiv']:
            try:
                if pixiv_info[3]:
                    id = int(pixiv_info[3])
                    Pixiv(_USERNAME, _PASSWORD, id, ctx).get_illust()
                elif pixiv_info[2]:
                    Pixiv(_USERNAME, _PASSWORD, id, ctx).send_original()
            except Exception as e:
                logger.error(e)
        else:
            logger.error('配置文件未开启pixiv下载功能')


@deco.in_content('#')
def receive_group_msg(ctx: GroupMsg):
    pixiv_info = re.match(pixiv_pattern, ctx.Content)
    if pixiv_info:
        if config['pixiv']:
            try:
                id = int(pixiv_info[2])
                Pixiv(_USERNAME, _PASSWORD, id, ctx).get_illust()
            except Exception as e:
                logger.error(e)
        else:
            logger.error('配置文件未开启pixiv下载功能')
