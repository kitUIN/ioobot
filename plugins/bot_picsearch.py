import botoy.decorators as deco
from botoy import FriendMsg, GroupMsg

from plugins.ioolib.picsearch import Send, PicSearch

sendMsg = Send()


def cmd_picsearch(ctx):
    if ctx.PicContent == '#以图搜图':
        pic = PicSearch(ctx)
        if ctx.PicUrl != '':
            pic.pic_search(ctx.PicUrl)
        else:
            sendMsg.send_text(ctx, '缺少图片呢')
    elif ctx.PicContent == '#以图搜番':
        pic = PicSearch(ctx)
        if ctx.PicUrl != '':
            pic.anime_search(ctx.PicUrl)
        else:
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
