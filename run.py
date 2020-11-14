#! /usr/bin/env python3
# coding=utf-8
import os
import pathlib
import random
import re
import threading
import time

import botoy.decorators as deco
from botoy import FriendMsg, GroupMsg, EventMsg
from botoy.refine import *
from loguru import logger
from plugins.ioolib import *

pattern_command = '#(.*?)'
# ---------------------------------------------
botdata = event.Getdata()
SendMsg = Send()
bot.reload_plugins()


# ---------------------------ctx中间加工---------------------------

@bot.group_context_use
def Pic(ctx: GroupMsg):
    ctx.PicUrl = ''
    if ctx.MsgType == 'PicMsg':
        ctx.PicUrl = refine_pic_group_msg(ctx).GroupPic[0].Url  # 图片地址
        logger.info(ctx.PicUrl)
        ctx.PicContent = refine_pic_group_msg(ctx).Content  # 图片消息内容
        logger.info(ctx.Content)
    else:
        pass
    return ctx


# -----------------------消息显示--------------------------------------

@bot.on_group_msg
def group_msg(ctx: GroupMsg):
    # todo 完善xml，json，pic数据结构
    if ctx.MsgType == 'TextMsg':
        msg = '\r\n消息类型:{}[文本]\r\n发送人:{}({})\r\n来自群:{}({})\r\n内容:{}\r\n时间:{}'.format(ctx.MsgType, ctx.FromNickName,
                                                                                     ctx.FromUserId,
                                                                                     ctx.FromGroupName, ctx.FromGroupId,
                                                                                     ctx.Content,
                                                                                     ctx.MsgTime)
        logger.debug(msg)
    elif ctx.MsgType == 'PicMsg':
        msg = '\r\n消息类型:{}[图片]\r\n发送人:{}({})\r\n来自群:{}({})\r\n内容:{}\r\n图片:{}\r\n时间:{}'.format(ctx.MsgType,
                                                                                              ctx.FromNickName,
                                                                                              ctx.FromUserId,
                                                                                              ctx.FromGroupName,
                                                                                              ctx.FromGroupId,
                                                                                              ctx.Content, ctx.PicUrl,
                                                                                              ctx.MsgTime)
        logger.debug(msg)


@bot.on_friend_msg
def friend_msg(ctx: FriendMsg):
    msg = '\r\n消息类型:{}\r\n发送人:{}\r\n内容:{}'.format(ctx.MsgType, ctx.FromUin, ctx.Content)
    logger.debug(msg)


@bot.on_event
def events(ctx: EventMsg):
    msg = '\r\n事件名称:{}\r\n具体信息:{}\r\n基本信息:{}'.format(ctx.EventName, ctx.EventData, ctx.EventMsg)
    logger.debug(msg)


# -----------------------指令-----------------------------------------------
@bot.on_friend_msg
@deco.queued_up
@deco.ignore_botself
def receive_friend_msg(ctx: FriendMsg):  # 修改指令 前往/ioolib/command.py
    if re.match(pattern_command, ctx.Content):
        Command(ctx).main()


@bot.on_group_msg
@deco.queued_up
@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if re.match(pattern_command, ctx.Content):
        Command(ctx).main()
    else:
        Command(ctx).cmd_fudu()


@bot.on_group_msg
@deco.ignore_botself
@deco.equal_content('test')
def test(ctx: GroupMsg):
    SendMsg.send_pic(ctx, '标题:水着メルトwww.pixiv.net/artworks/76508807page:0作者:PDXenwww.pixiv.net/users/11945252',
                     'https://cdn.jsdelivr.net/gh/laosepi/setu/pics_original/76508807_p0.png')
    # action.sendFriendText(ctx, ctx.master)


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
    bot.run()
    # ---------------------------------------------------------------------------------
