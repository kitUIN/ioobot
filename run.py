#! /usr/bin/env python3
# coding=utf-8
import os
import pathlib
import threading

import botoy.decorators as deco
from botoy import GroupMsg, FriendMsg
from botoy.refine import *
from loguru import logger

from plugins.bot_setu import Getdata
from plugins.ioolib import *

# ---------------------------------------------
sendMsg = Send()
FuDu = 0
FuDuQQG = 0
botdata = Getdata()
SendMsg = Send()


def fudu(ctx):
    global FuDu
    global FuDuQQG
    if FuDu == 1 and (ctx.FromUserId != ctx.CurrentQQ) and (ctx.Content != '复读姬模式') and (
            ctx.FromGroupId == FuDuQQG) and (ctx.Content != '砸烂复读姬'):
        msg = ctx.Content
        if ctx.MsgType == 'PicMsg':
            # try:
            msg = ctx.PicContent
            PicUrl = ctx.PicUrl
            sendMsg.send_pic(ctx, msg, PicUrl)
        else:
            sendMsg.send_text(ctx, msg)

    elif ctx.Content == '砸烂复读姬' and ctx.FromUserId != ctx.CurrentQQ and FuDu == 1:
        FuDuQQG = 0
        FuDu = 0
        sendMsg.send_pic(ctx, '', '', 'look/fudu1.jpg', False, False)

    elif ctx.Content == '砸烂复读姬' and FuDu == 0:
        sendMsg.send_pic(ctx, '', '', 'look/fudu2.jpg', False, False)

    elif (ctx.Content == '复读姬模式' or ctx.Content == '开启复读姬') and ctx.FromUserId != ctx.CurrentQQ:
        FuDu = 1
        FuDuQQG = ctx.FromGroupId
        sendMsg.send_pic(ctx, '', '', 'look/fudu0.jpg', False, False)


# -----------------------ctx预加工------------------------------------------

@bot.friend_context_use
def _Friend_Pic(ctx: FriendMsg):
    ctx.PicUrl = ''
    ctx.PicContent = ''
    if ctx.MsgType == 'PicMsg':
        ctx.PicUrl = refine_pic_friend_msg(ctx).FriendPic[0].Url  # 图片地址
        ctx.PicContent = refine_pic_friend_msg(ctx).Content  # 图片消息内容
    else:
        pass
    return ctx


@bot.group_context_use
def _Group_Pic(ctx: GroupMsg):
    ctx.PicUrl = ''
    ctx.PicContent = ''
    if ctx.MsgType == 'PicMsg':
        ctx.PicUrl = refine_pic_group_msg(ctx).GroupPic[0].Url  # 图片地址
        ctx.PicContent = refine_pic_group_msg(ctx).Content  # 图片消息内容
    else:
        pass
    fudu(ctx)  # 复读
    return ctx


# -----------------------指令-----------------------------------------------

@bot.on_group_msg
@deco.in_content('#插件')
def plugin(ctx: GroupMsg, msg=''):
    if ctx.FromUserId == config['superAdmin']:
        if ctx.Content == '#插件列表':
            plugins = bot.plugins
            for i in range(len(plugins)):
                msg += plugins[i]
            sendMsg.send_text(ctx, msg)
        elif ctx.Content == '#插件重置':
            bot.reload_plugins()
            msg = '已重置\r\n当前插件：'
            plugins = bot.plugins
            for i in range(len(plugins)):
                msg += '\r\n' + plugins[i]
            sendMsg.send_text(ctx, msg)
        elif ctx.Content[:5] == '#插件禁用':
            remove = ctx.Content[6:]
            bot.remove_plugin(remove)
            bot.reload_plugins()
            msg = '已禁用{}\r\n当前插件：'.format(remove)
            plugins = bot.plugins
            for i in range(len(plugins)):
                msg += '\r\n' + plugins[i]
            sendMsg.send_text(ctx, msg)
    return


'''
@bot.on_group_msg
@deco.ignore_botself
@deco.equal_content('test')
def test(ctx):
    SendMsg.send_pic(ctx, '标题:水着メルトwww.pixiv.net/artworks/76508807page:0作者:PDXenwww.pixiv.net/users/11945252',
                     'https://cdn.jsdelivr.net/gh/laosepi/setu/pics_original/76508807_p0.png')
    # action.sendFriendText(ctx, ctx.master)
@bot.on_group_msg
@deco.ignore_botself
@deco.equal_content('test')
def test(ctx: GroupMsg):
    logger.info(ctx.master)
    # action.sendFriendText(ctx, ctx.master)
def group_mm(ctx: GroupMsg):
    action.sendGroupVoice(ctx.FromGroupId, voiceUrl='', voiceBase64Buf=tobase64('/home/android/pic/File0036.silk'))
    time.sleep(1.1)
    action.sendGroupVoice(ctx.FromGroupId, voiceUrl='', voiceBase64Buf=tobase64('/home/android/pic/File0040.silk'))
'''


# --------------------socket监听----------------
@bot.when_disconnected(every_time=True)
def disconnected():
    logger.warning('socket断开~')


@bot.when_connected(every_time=True)
def connected():
    logger.success('socket连接成功~')
    # botdata.updateAllGroupData()


if __name__ == '__main__':
    if os.path.isfile('.flag'):  # 有文件
        threading.Thread(target=botdata.updateAllGroupData, daemon=True).start()
    else:
        logger.info('第一次启动~')
        botdata.updateAllGroupData()
        pathlib.Path('.flag').touch()  # 创建flag文件
    # ---------------------------------------bot---------------------------------------
    bot.remove_plugin('example')
    bot.run()
    bot.load_plugins()
    # ---------------------------------------------------------------------------------
