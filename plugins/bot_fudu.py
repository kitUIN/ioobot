import botoy.decorators as deco
from botoy import GroupMsg

from .ioolib.send import Send, tobase64

sendMsg = Send()
FuDu = 0
FuDuQQG = 0


def cmd_fudu(ctx):
    global FuDu
    global FuDuQQG
    if ctx.Content == '砸烂复读姬' and ctx.FromUserId != ctx.CurrentQQ and FuDu == 1:
        FuDuQQG = 0
        FuDu = 0
        tobase = tobase64('look/fudu1.jpg')
        sendMsg.send_pic(ctx, '', '', False, False, tobase)
        return
    elif ctx.Content == '砸烂复读姬' and FuDu == 0:
        tobase = tobase64('look/fudu2.jpg')
        sendMsg.send_pic(ctx, '', '', False, False, tobase)
        return
    elif (ctx.Content == '复读姬模式' or ctx.Content == '开启复读姬') and ctx.FromUserId != ctx.CurrentQQ:
        FuDu = 1
        FuDuQQG = ctx.FromGroupId
        tobase = tobase64('look/fudu0.jpg')
        sendMsg.send_pic(ctx, '', '', False, False, tobase)
        return
    elif FuDu == 1 and (ctx.FromUserId != ctx.CurrentQQ) and (ctx.Content != '复读姬模式') and (
            ctx.FromGroupId == FuDuQQG):
        msg = ctx.Content
        if ctx.MsgType == 'PicMsg':
            # try:
            msg = ctx.PicContent
            PicUrl = ctx.PicUrl
            sendMsg.send_pic(ctx, msg, PicUrl)
        else:
            sendMsg.send_text(ctx, msg)
        return


@deco.queued_up
@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    cmd_fudu(ctx)
