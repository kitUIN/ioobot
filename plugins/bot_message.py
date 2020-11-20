from botoy import FriendMsg, GroupMsg, EventMsg
from loguru import logger


# -----------------------消息显示--------------------------------------


def receive_friend_msg(ctx: FriendMsg):  # todo 完善xml，json，pic,event数据结构

    if ctx.MsgType == 'TextMsg':
        msg = '\r\n消息类型:{}[文本]\r\n发送人:{}\r\n内容:{}'.format(ctx.MsgType, ctx.FromUin, ctx.Content)
        logger.debug(msg)
    elif ctx.MsgType == 'PicMsg':
        msg = '\r\n消息类型:{}[图片]\r\n发送人:{}\r\n内容:{}\r\n图片:{}\r\nSeq:{}'.format(ctx.MsgType,
                                                                             ctx.FromUin,
                                                                             ctx.PicContent,
                                                                             ctx.PicUrl,
                                                                             ctx.MsgSeq)
        logger.debug(msg)


def receive_group_msg(ctx: GroupMsg):
    if ctx.MsgType == 'TextMsg':
        msg = '\r\n消息类型:{}[文本]\r\n发送人:{}({})\r\n来自群:{}({})\r\n内容:{}\r\nSeq:{}'.format(ctx.MsgType, ctx.FromNickName,
                                                                                      ctx.FromUserId,
                                                                                      ctx.FromGroupName,
                                                                                      ctx.FromGroupId,
                                                                                      ctx.Content,
                                                                                      ctx.MsgSeq)
        logger.debug(msg)
    elif ctx.MsgType == 'PicMsg':
        msg = '\r\n消息类型:{}[图片]\r\n发送人:{}({})\r\n来自群:{}({})\r\n内容:{}\r\n图片:{}\r\nSeq:{}'.format(ctx.MsgType,
                                                                                               ctx.FromNickName,
                                                                                               ctx.FromUserId,
                                                                                               ctx.FromGroupName,
                                                                                               ctx.FromGroupId,
                                                                                               ctx.PicContent,
                                                                                               ctx.PicUrl,
                                                                                               ctx.MsgSeq)
        logger.debug(msg)


def receive_events(ctx: EventMsg):
    msg = '\r\n事件名称:{}\r\n具体信息:{}\r\n基本信息:{}'.format(ctx.EventName, ctx.EventData, ctx.EventMsg)
    logger.debug(msg)
