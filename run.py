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
from .ioolib import *

# ------------------正则------------------
pattern_setu = '来(.*?)[点丶份张幅](.*?)的?(|r18)[色瑟涩🐍][图圖🤮]'
pattern_command = '#(.*?)'
# ------------------db-------------------------
# ---------------------------------------------
botdata = event.Getdata()


# ---------------------------ctx中间加工---------------------------

@bot.group_context_use
def Pic(ctx: GroupMsg):
    if ctx.MsgType == 'PicMsg':
        ctx.PicUrl = refine_pic_group_msg(ctx).GroupPic[0].Url  # 图片地址
        logger.info(ctx.PicUrl)
        ctx.Content = refine_pic_group_msg(ctx).Content  # 图片消息内容
        logger.info(ctx.Content)
    else:
        pass
    return ctx


# -----------------------消息显示--------------------------------------

@bot.on_group_msg
def receive_group_msg(ctx: GroupMsg):
    # todo 完善xml，json，pic数据结构
    msg = '\n消息类型:{}\n发送人:{}({})\n来自群:{}({})\n内容:{}\n时间:{}'.format(ctx.MsgType, ctx.FromNickName, ctx.FromUserId,
                                                                   ctx.FromGroupName, ctx.FromGroupId, ctx.Content,
                                                                   ctx.MsgTime)
    logger.debug(msg)


@bot.on_friend_msg()
def receive_friend_msg(ctx: FriendMsg):
    msg = '\n消息类型:{}\n发送人:{}\n内容:{}'.format(ctx.MsgType, ctx.FromUin, ctx.Content)
    logger.debug(msg)


@bot.on_event()
def receive_events(ctx: EventMsg):
    msg = '\n事件名称:{}\n具体信息:{}\n基本信息:{}'.format(ctx.EventName, ctx.EventData, ctx.EventMsg)
    logger.debug(msg)


# ---------------------------识图指令---------------------------
@bot.on_group_msg
@deco.queued_up
@deco.in_content('#以图搜番')
def group_setu(ctx: GroupMsg):
    pic = PicSearch(ctx)
    pic.anime_search(ctx.url)


@bot.on_friend_msg
@deco.queued_up
@deco.in_content('#以图搜图')
def friend_setu(ctx: FriendMsg):
    pic = PicSearch(ctx)
    pic.pic_search(ctx.url)


# ---------------------------setu指令---------------------------
@bot.on_group_msg
@deco.queued_up
@deco.with_pattern(pattern_setu)
def group_setu(ctx: GroupMsg):
    group_info = re.search(pattern_setu, ctx.Content)  # 提取关键字
    Setu(ctx, group_info[2], group_info[1], group_info[3]).main()


@bot.on_friend_msg
@deco.queued_up
@deco.with_pattern(pattern_setu)
def friend_setu(ctx: FriendMsg):
    friend_info = re.search(pattern_setu, ctx.Content)  # 提取关键字
    Setu(ctx, friend_info[2], friend_info[1], friend_info[3]).main()


@bot.on_group_msg
@deco.from_botself
@deco.in_content('(.*?)REVOKE(.*?)')
def receive_group_msg(ctx: GroupMsg):
    delay = re.findall(r'REVOKE[(d+)]', ctx.Content)
    if delay:
        delay = min(int(delay[0]), 90)
    else:
        delay = random.randint(30, 60)
    time.sleep(delay)
    action.revokeGroupMsg(ctx.FromGroupId, ctx.MsgSeq, ctx.MsgRandom)


# -----------------------指令-----------------------------------------------
@bot.on_friend_msg()
@deco.queued_up
def receive_friend_msg(ctx: FriendMsg):  # 修改指令 前往/ioolib/command.py
    if re.search(pattern_command, ctx.Content):
        Command(ctx).main()


@bot.on_group_msg
@deco.queued_up
def receive_group_msg(ctx: GroupMsg):
    if re.search(pattern_command, ctx.Content):
        Command(ctx).main()
    else:
        Command(ctx).cmd_fudu()


@bot.on_group_msg
@deco.ignore_botself
@deco.equal_content('test')
def test(ctx: GroupMsg):
    action.sendGroupPic(ctx.FromGroupId, content='',
                        picUrl='https://media.trace.moe/video/11887/%5BANK-Raws%26NatsuYuki%5D%20Kokoro%20Connect%20-%2005%20%28BDrip%201280x720%20x264%20AAC%29.mp4?t=1174.5&token=I7RtV-BVFDjvgwgPpUwFKw&mute')
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


# -----------------------权限信息通知-----------------------------------------------
@bot.on_event
def event(ctx: EventMsg):
    admin_info = refine_group_admin_event_msg(ctx)
    join_info = refine_group_join_event_msg(ctx)
    if admin_info:
        data_raw = group_config.search(Q['GroupId'] == admin_info.GroupID)
        if data_raw:
            if admin_info.Flag == 1:  # 变成管理员
                logger.info('群:{} QQ:{}成为管理员'.format(admin_info.GroupID, admin_info.UserID))
                if admin_info.UserID in data_raw[0]['managers']:  # 防止重叠
                    data_raw[0]['managers'].remove[admin_info.UserID]
                data_raw[0]['admins'].append(admin_info.UserID)
            else:
                logger.info('群:{} QQ:{}被取消管理员'.format(admin_info.GroupID, admin_info.UserID))
                try:
                    data_raw[0]['admins'].remove(admin_info.UserID)
                except Exception as e:  # 出错就说明群信息不正确,重新获取
                    logger.warning('从数据库删除管理员出错,尝试重新刷新群数据\r\n' + str(e))
                    botdata.updateGroupData(admin_info.GroupID)
                    return
            group_config.update({'admins': data_raw[0]['admins'],
                                 'managers': data_raw[0]['managers']},
                                Q['GroupId'] == admin_info.GroupID)
        else:  # 如果没数据就重新获取
            botdata.updateGroupData(admin_info.GroupID)
    elif join_info:
        if join_info.UserID == config['BotQQ']:
            logger.info('bot加入群{}'.format(join_info.FromUin))
            botdata.updateGroupData(join_info.FromUin)
        else:
            logger.info('{}:{}加入群{}'.format(join_info.UserName, join_info.UserID, join_info.FromUin))
    elif ctx.MsgType == 'ON_EVENT_GROUP_JOIN_SUCC':
        logger.info('bot加入群{}'.format(ctx.FromUin))
        botdata.updateGroupData(ctx.FromUin)


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
