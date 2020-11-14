#! /usr/bin/env python3
# coding=utf-8
import os
import pathlib
import threading

import botoy.decorators as deco
from botoy import GroupMsg
from botoy.refine import *
from loguru import logger

from plugins.bot_setu import Getdata
from plugins.ioolib import *

# ---------------------------------------------
botdata = Getdata()
SendMsg = Send()


# -----------------------ctx预加工------------------------------------------


@bot.group_context_use
def _Pic(ctx: GroupMsg):
    ctx.PicUrl = ''
    ctx.PicContent = ''
    if ctx.MsgType == 'PicMsg':
        ctx.PicUrl = refine_pic_group_msg(ctx).GroupPic[0].Url  # 图片地址

        ctx.PicContent = refine_pic_group_msg(ctx).Content  # 图片消息内容
    else:
        pass
    return ctx


# -----------------------指令-----------------------------------------------

@bot.on_group_msg
@deco.ignore_botself
@deco.equal_content('test')
def test(ctx):
    SendMsg.send_pic(ctx, '标题:水着メルトwww.pixiv.net/artworks/76508807page:0作者:PDXenwww.pixiv.net/users/11945252',
                     'https://cdn.jsdelivr.net/gh/laosepi/setu/pics_original/76508807_p0.png')
    # action.sendFriendText(ctx, ctx.master)


@deco.equal_content('#重置插件')
def plugin(ctx: GroupMsg):
    bot.reload_plugins()
    logger.info(bot.plugins)
'''
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
