import re

import botoy.decorators as deco
from botoy import Action, FriendMsg, GroupMsg, EventMsg

from plugins.ioolib.command import Command

# ------------------正则------------------
pattern_command = '#(.*?)'


# ----------------------------------------

@deco.queued_up
@deco.ignore_botself
def receive_friend_msg(ctx: FriendMsg):  # 修改指令 前往ioobot/plugins/ioolib/command.py
    if re.match(pattern_command, ctx.Content):
        Command(ctx).main()


@deco.queued_up
@deco.ignore_botself
def receive_group_msg(ctx: GroupMsg):
    if re.match(pattern_command, ctx.Content):
        Command(ctx).main()


def receive_events(ctx: EventMsg):
    Action(ctx.CurrentQQ)
