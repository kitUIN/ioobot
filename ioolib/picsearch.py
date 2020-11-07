import base64

from PicImageSearch import SauceNAO, TraceMoe
from loguru import logger
from .message import Send

SendMsg = Send()


class PicSearch:
    def __init__(self, ctx):
        self.ctx = ctx

    @staticmethod
    def _base_64(filename):
        with open(filename, 'rb') as f:
            coding = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
            # print('本地base64转码~')
            return coding.decode()

    def anime_search(self, url):  # 以图搜番
        try:
            t = TraceMoe()
            t.search(url)
            if t.similarity > 0.87:
                msg = '缩略图展示↑↑↑\r\n番名:{}({},{})\r\n发布日期：{}\r\n第{}集\r\nR18：{}\r\n搜索时间：{}s\r\n'.format(t.title_chinese,
                                                                                                     t.anime, t.title,
                                                                                                     t.season,
                                                                                                     t.episode,
                                                                                                     t.is_adult,
                                                                                                     t.trial)
                SendMsg.send_pic(self.ctx, msg, t.thumbnail, False, True)
                return
            else:
                msg = '找不到了呢'
                SendMsg.send_pic(self.ctx, msg, '', False, True, self._base_64('look/ex01.jpg'))
                return
        except Exception as e:
            logger.error(e)

    def pic_search(self, url):  # 以图搜图
        try:
            saucenao = SauceNAO(numres=1)
            res = saucenao.search(url)
            raw = res.raw[0]
            if raw.similarity > 80:
                msg = '缩略图展示↑↑↑\r\n标题:{}\r\n作者：{}\r\n作者id：https://www.pixiv.net/users/{}\r\n作品id：{}\r\n直通车：{}\r\n'.format(
                    raw.title, raw.author, raw.member_id, raw.pixiv_id, raw.url)
                SendMsg.send_pic(self.ctx, msg, raw.thumbnail, False, True)
                return
            else:
                msg = '找不到了呢'
                SendMsg.send_pic(self.ctx, msg, '', False, True, self._base_64('look/ex01.jpg'))
                return
        except Exception as e:
            logger.error(e)
