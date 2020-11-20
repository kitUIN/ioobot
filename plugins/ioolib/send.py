import base64

from botoy import Action

from .dbs import config

action = Action(qq=config['BotQQ'])


class Send:
    @staticmethod
    def _tobase64(filename):
        with open(filename, 'rb') as f:
            coding = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
            # logger.info('本地base64转码~')
            return coding.decode()

    @staticmethod
    def send_text(ctx, text, atUser: bool = False):
        if ctx.__class__.__name__ == 'GroupMsg':
            if atUser:
                action.sendGroupText(ctx.FromGroupId, text, ctx.FromUserId)
            else:
                action.sendGroupText(ctx.FromGroupId, text)
        else:
            if ctx.TempUin is None:  # None为好友会话
                action.sendFriendText(ctx.FromUin, text)
            else:  # 临时会话
                action.sendPrivateText(ctx.FromUin, text, ctx.TempUin)
        return

    def send_pic(self, ctx, text='', picUrl='', picPath='', flashPic=False, atUser: bool = False, fileMd5=''):
        if picPath != '':
            pic_path = self._tobase64(picPath)
        else:
            pic_path = ''
        if ctx.__class__.__name__ == 'GroupMsg':
            if atUser:
                action.sendGroupPic(ctx.FromGroupId, content=text, picUrl=picUrl, picBase64Buf=pic_path,
                                    fileMd5=fileMd5, flashPic=flashPic)
            else:
                action.sendGroupPic(ctx.FromGroupId, content=text, picUrl=picUrl, picBase64Buf=pic_path,
                                    fileMd5=fileMd5, flashPic=flashPic)
        else:
            if ctx.TempUin is None:
                action.sendFriendPic(ctx.FromUin, picUrl=picUrl, picBase64Buf=pic_path, fileMd5=fileMd5,
                                     content=text, flashPic=flashPic)
            else:
                action.sendPrivatePic(ctx.FromUin, ctx.FromGroupID, text, picUrl=picUrl,
                                      picBase64Buf=pic_path,
                                      fileMd5=fileMd5)
        return
