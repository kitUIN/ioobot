from botoy import Action, FriendMsg, GroupMsg, EventMsg


def receive_friend_msg(ctx: FriendMsg):
    Action(ctx.CurrentQQ)


def receive_group_msg(ctx: GroupMsg):
    Action(ctx.CurrentQQ)


def receive_events(ctx: EventMsg):
    Action(ctx.CurrentQQ)
