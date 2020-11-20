import base64

from PicImageSearch import SauceNAO, TraceMoe
from loguru import logger

from .dbs import config
from .send import Send

SendMsg = Send()


class PicSearch:
    def __init__(self, ctx):
        self.ctx = ctx

    def anime_search(self, url):  # 以图搜番
        try:
            tracemoe = TraceMoe()
            t = tracemoe.search(url).raw[0]
            logger.info('开始搜索')
            if t.similarity > 0.87:
                msg = '缩略图展示↑↑↑\r\n番名:{}({},{})\r\n发布日期：{}\r\n第{}集\r\nR18：{}\r\n搜索时间：{}s\r\n'.format(t.title_chinese,
                                                                                                     t.anime, t.title,
                                                                                                     t.season,
                                                                                                     t.episode,
                                                                                                     t.is_adult,
                                                                                                     t.trial)
                SendMsg.send_pic(self.ctx, msg, t.thumbnail, flashPic=False, atUser=True)
                return
            else:
                msg = '找不到了呢'
                SendMsg.send_pic(self.ctx, msg, '', 'look/ex01.jpg', False, True)
                return
        except Exception as e:
            logger.error(e)

    def pic_search(self, url):  # 以图搜图
        _REQUESTS_KWARGS = dict()
        if config['SauceNAO_proxies'] == True:
            _REQUESTS_KWARGS = {
                'proxies': {
                    'https': 'http://127.0.0.1:10809',
                }
                # 如果需要代理
            }
        try:
            if config['SauceNAOKEY'] == '':
                key = None
            else:
                key = config['SauceNAOKEY']
            saucenao = SauceNAO(api_key=key, numres=1, testmode=1, **_REQUESTS_KWARGS)
            logger.info('开始搜索')
            res = saucenao.search(url)
            raw = res.raw[0]
            if raw.similarity > 80:
                msg = '缩略图展示↑↑↑\r\n标题:{}\r\n作者:{}\r\n作者id:{}\r\n作品id:{}\r\n直通车:{}\r\n'.format(
                    raw.title, raw.author, raw.member_id, raw.pixiv_id, raw.url)
                SendMsg.send_pic(self.ctx, msg, raw.thumbnail, flashPic=False, atUser=True)
                logger.info('搜索成功')
                return
            else:
                msg = '找不到了呢'
                SendMsg.send_pic(self.ctx, msg, '', 'look/ex01.jpg', False, True)
                return
        except Exception as e:
            logger.error(e)
