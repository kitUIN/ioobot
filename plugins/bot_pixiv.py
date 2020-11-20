import os
import re

import botoy.decorators as deco
from botoy import FriendMsg, GroupMsg
from loguru import logger
from pixivpy3 import *

from plugins.ioolib.dbs import config
from plugins.ioolib.send import Send

_USERNAME = config["netease_username"]
_PASSWORD = config["netease_password"]
sendMsg = Send()
pixiv_pattern = '#p?(|ixiv) (.+)'


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

    def _get_illust(self):
        self.api.login(self.username, self.password)
        json_result = self.api.illust_detail(self.id)
        illust = json_result.illust
        if illust is None:
            logger.error(json_result['error'])
        return illust.meta_single_page['original_image_url']

    def _download_illust(self):
        self.api.download(self._get_illust(), path=self.path, fname=self.id + '.jpg')

    def _search(self):
        pass

    def send_original(self):
        sendMsg.send_pic(self.ctx, '', self._get_illust())
        # time.sleep(3)
        # os.remove(pic_path)


@deco.in_content('#')
def receive_friend_msg(ctx: FriendMsg):
    pixiv_info = re.match(pixiv_pattern, ctx.Content)
    if pixiv_info:
        if config['pixiv']:
            try:
                id = int(pixiv_info[2])
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
                Pixiv(_USERNAME, _PASSWORD, id, ctx).send_original()
            except Exception as e:
                logger.error(e)
        else:
            logger.error('配置文件未开启pixiv下载功能')
