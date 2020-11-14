import os
import re
import time

from botoy import Action, FriendMsg, GroupMsg, EventMsg
from loguru import logger
from pikax import Pikax

from plugins.ioolib.dbs import config
from plugins.ioolib.send import Send, tobase64

_USERNAME = config["netease_username"]
_PASSWORD = config["netease_password"]
sendMsg = Send()
pixiv_pattern = '#p(|ixiv)(.*?)'


class Pixiv:

    def __init__(self, username, password, id, ctx):
        self.username = username
        self.password = password
        self.id = id
        self.ctx = ctx
        self.pixiv = Pikax()
        self.path = os.getcwd() + '/pixiv'

    def _download_illust(self):
        self.pixiv.login(self.username, self.password)
        self.pixiv.download(folder=self.path, illust_id=self.id)

    def _search(self):
        pass

    def send_original(self):
        self._download_illust()
        pic_path = self.path + '/' + os.listdir(self.path)[0]
        logger.info(pic_path)
        logger.info(self.path)
        sendMsg.send_pic(self.ctx, '', '', False, False, tobase64(pic_path))
        time.sleep(3)
        os.remove(pic_path)


def receive_friend_msg(ctx: FriendMsg):
    Action(ctx.CurrentQQ)


def receive_group_msg(ctx: GroupMsg):
    pixiv_info = re.search(pixiv_pattern, ctx.Content)
    logger.info(pixiv_info)
    if pixiv_info:
        if config['pixiv']:
            try:
                id = int(pixiv_info[2])
                Pixiv(_USERNAME, _PASSWORD, id, ctx).send_original()
            except Exception as e:
                logger.error(e)
        else:
            logger.error('配置文件未开启pixiv下载功能')


def receive_events(ctx: EventMsg):
    Action(ctx.CurrentQQ)
