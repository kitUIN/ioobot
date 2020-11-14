# 仅模板插件，无实际用途
from botoy import Action, FriendMsg, GroupMsg, EventMsg
import botoy.decorators as deco
from botoy.refine import *
from loguru import logger
from plugins.ioolib import Send
sendMsg = Send()


def receive_friend_msg(ctx: FriendMsg):
    Action(ctx.CurrentQQ)


def receive_group_msg(ctx: GroupMsg):
    Action(ctx.CurrentQQ)


def receive_events(ctx: EventMsg):
    Action(ctx.CurrentQQ)
