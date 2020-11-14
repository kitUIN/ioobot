import base64

from botoy import Action
from loguru import logger

from .dbs import config

action = Action(qq=config['BotQQ'])


def tobase64(filename):
    with open(filename, 'rb') as f:
        coding = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
        logger.info('本地base64转码~')
        return coding.decode()


class Send:
    def send_text(self, ctx, text, atUser: bool = False):
        if ctx.__class__.__name__ == 'GroupMsg':
            if atUser:
                action.sendGroupText(ctx.FromGroupId, text, ctx.FromUserId)
            else:
                action.sendGroupText(ctx.FromGroupId, text)
        else:
            if ctx.TempUin == None:  # None为好友会话
                action.sendFriendText(ctx.FromUin, text)
            else:  # 临时会话
                action.sendPrivateText(ctx.FromUin, text, ctx.TempUin)
        return

    def send_pic(self, ctx, text='', picUrl='', flashPic=False, atUser: bool = False, picBase64Buf='', fileMd5=''):
        if ctx.__class__.__name__ == 'GroupMsg':
            if atUser:
                action.sendGroupPic(ctx.FromGroupId, content=text, picUrl=picUrl, picBase64Buf=picBase64Buf,
                                    fileMd5=fileMd5, flashPic=flashPic)
            else:
                action.sendGroupPic(ctx.FromGroupId, content=text, picUrl=picUrl, picBase64Buf=picBase64Buf,
                                    fileMd5=fileMd5, flashPic=flashPic)
        else:
            if ctx.TempUin is None:
                action.sendFriendPic(ctx.FromUin, picUrl=picUrl, picBase64Buf=picBase64Buf, fileMd5=fileMd5,
                                     content=text, flashPic=flashPic)
            else:
                action.sendPrivatePic(ctx.FromUin, ctx.FromGroupID, text, picUrl=picUrl, picBase64Buf=picBase64Buf,
                                      fileMd5=fileMd5)
        return
