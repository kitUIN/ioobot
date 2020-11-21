import botoy.decorators as deco
from botoy import FriendMsg, GroupMsg

from plugins.ioolib.send import Send

sendMsg = Send()
Version = "v2.1.0"
version = {
    "v2.1.0": "(+)Pixiv R18解封，增加漫画下载\r\n（+）增加以图搜源代理模式",
    "v2.0.0": "(+)重构代码，改用botoy支持库\r\n(+)插件化\r\n(+)旧功能迁移完成\r\n(+)Pixiv原图下载(+)以图搜源拆分细化",
    "v1.2.0": "(+)支持网易云vip解析\r\n(+)添加今日人品\r\n(+)添加留言功能\r\n(+)bug修复&调整\r\n- 表情包更新\r\n- 复读姬bug修复",
    "v1.1.2": "(+)支持图片MD5监控\r\n(+)以图搜源优化\r\n- 修复无返回值bug\r\n- 修复因为图片位置不对无法识别的bug\r\n(+)logger日志升级\r\n(+)添加表情库\r\n(+)bug修复&调整\r\n- 修复统计图中文乱码\r\n- 美化统计图",
    "v1.1.1": "(+)bug修复&调整\r\n- 图片消息监控\r\n- 更新控制台日志输出\r\n- 修复sysinfo\r\n- 修复统计图\r\n- 本地图片发送修复\r\n(+)复读姬升级支持图片复读",
    "v1.1.0": "(+)添加以图搜源功能\r\n(+)日志输出调整",
    "v1.0.1": "(+)添加统计功能\r\n(+)添加帮助功能\r\n(+)添加复读姬功能\r\n(+)添加版本号功能",
    "v1.0.0": "(+)添加色图功能\r\n(感谢yuban10703提供代码与色图库)\r\n(感谢lolicon.app的色图库)\r\n(+)调整代码布局\r\n(+)添加权限功能"
}


def ver(ctx):
    vers = '当前版本→' + Version + '←' + '\r\n#----历史版本----#\r\n'
    for ve in version:
        vers = vers + ve + ','
    vers = vers + '\r\n#----更新内容----#\r\n'
    if ctx.Content == '#v1.0.0':
        vers = vers + version['v1.0.0']
    elif ctx.Content == '#v1.0.1':
        vers = vers + version['v1.0.1']
    elif ctx.Content == '#v1.1.0':
        vers = vers + version['v1.1.0']
    elif ctx.Content == '#v1.1.1':
        vers = vers + version['v1.1.1']
    elif ctx.Content == '#v1.1.2':
        vers = vers + version['v1.1.2']
    elif ctx.Content == '#v2.0.0':
        vers = vers + version['v2.0.0']
    else:
        vers = vers + version[Version]
    return vers


def send_ver(ctx):
    if ctx.Content[:2] == '#v':
        msg = ver(ctx)
        sendMsg.send_text(ctx, msg)
    return


@deco.queued_up
@deco.ignore_botself
@deco.in_content('#')
def receive_friend_msg(ctx: FriendMsg):
    send_ver(ctx)


@deco.queued_up
@deco.ignore_botself
@deco.in_content('#')
def receive_group_msg(ctx: GroupMsg):
    send_ver(ctx)
