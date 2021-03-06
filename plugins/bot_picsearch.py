import os

import botoy.decorators as deco
import requests
from PicImageSearch import SauceNAO, TraceMoe
from botoy import FriendMsg, GroupMsg
from loguru import logger

from plugins.ioolib.dbs import config
from plugins.ioolib.send import Send

sendMsg = Send()


class PicSearch:
    _REQUESTS_KWARGS = dict()
    if config['search_proxies']:
        _REQUESTS_KWARGS = {
            'proxies': {
                'https': config['proxy'],
            }
            # 如果需要代理
        }

    def __init__(self, ctx):
        self.ctx = ctx

    def anime_search(self, url):  # 以图搜番
        try:
            logger.info('开始搜索')
            tracemoe = TraceMoe(**self._REQUESTS_KWARGS)
            tac = tracemoe.search(url)
            t = tac.raw[0]
            if t.similarity > 0.87:
                msg = '缩略图展示↑↑↑\r\n番名:{}({},{})\r\n发布日期：{}\r\n第{}集\r\nR18：{}'.format(t.title_chinese,
                                                                                     t.anime, t.title,
                                                                                     t.season,
                                                                                     t.episode,
                                                                                     t.is_adult)
                logger.info('搜索成功')
                sendMsg.send_pic(self.ctx, msg, t.thumbnail)
                return
            else:
                msg = '找不到了呢'
                sendMsg.send_pic(self.ctx, msg, '', 'look/ex01.jpg')
                return
        except Exception as e:
            logger.error(e)

    def pic_search(self, url):  # 以图搜图
        try:
            if config['SauceNAOKEY'] == '':
                key = None
            else:
                key = config['SauceNAOKEY']
            logger.info('开始搜索')
            saucenao = SauceNAO(api_key=key, numres=1, testmode=1, **self._REQUESTS_KWARGS)
            res = saucenao.search(url)
            raw = res.raw[0]
            if raw.similarity > 80:
                msg = '缩略图展示↑↑↑\r\n标题:{}\r\n作者:{}\r\n作者id:{}\r\n作品id:{}\r\n直通车:{}'.format(
                    raw.title, raw.author, raw.member_id, raw.pixiv_id, raw.url)
                if raw.pixiv_id != '':
                    msg += '\r\n使用命令获得原图：#p d {}'.format(raw.pixiv_id)
                logger.debug(msg)
                logger.debug(raw.thumbnail)
                logger.info('搜索成功')
                if config['search_proxies']:  # 缩略图功能需要翻
                    res = requests.get(raw.thumbnail, **self._REQUESTS_KWARGS)
                    with open('example.jpg', 'wb') as f:
                        f.write(res.content)
                    sendMsg.send_pic(self.ctx, text=msg, picPath='example.jpg')
                else:
                    sendMsg.send_text(self.ctx, text=msg)
            else:
                msg = '找不到了呢'
                sendMsg.send_pic(self.ctx, msg, '', 'look/ex01.jpg')
                return
        except Exception as e:
            logger.error(e)


def cmd_picsearch(ctx):
    if ctx.PicContent == '#以图搜图':
        if ctx.PicUrl != '':
            pic = PicSearch(ctx)
            pic.pic_search(ctx.PicUrl)
    elif ctx.PicContent == '#以图搜番':
        if ctx.PicUrl != '':
            pic = PicSearch(ctx)
            pic.anime_search(ctx.PicUrl)
    elif ctx.Content == '#以图搜番' or ctx.Content == '#以图搜图':
        sendMsg.send_text(ctx, '缺少图片呢')
    return


@deco.queued_up
@deco.ignore_botself
def receive_friend_msg(ctx: FriendMsg):
    cmd_picsearch(ctx)


@deco.queued_up
@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    cmd_picsearch(ctx)
