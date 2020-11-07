from retrying import retry

from .dbs import *


class Getdata:
    @staticmethod
    def defaultdata(data):
        data['managers'] = []  # 所有的管理者(可以设置bot功能的)
        # -----------------------------------------------------
        data['setuDefaultLevel'] = {'group': 1, 'temp': 3}  # 默认等级 0:正常 1:性感 2:色情 3:All
        data['setuinfoLevel'] = {'group': 2, 'temp': 3}  # setu信息完整度(0:不显示图片信息)
        data['original'] = {'group': False, 'temp': False}  # 是否原图
        data['setu'] = {'group': True, 'temp': True}  # 色图功能开关
        data['r18'] = {'group': False, 'temp': True}  # 是否开启r18
        data['freq'] = 0  # 频率 (次)
        data['refreshTime'] = 60  # 刷新时间 (s)
        data['clearSentTime'] = 900  # 刷新sent时间 (s)
        data['maxnum'] = {'group': 3, 'temp': 10}  # 一次最多数量
        # data['MsgCount'] = {'text': 0, 'pic': 0, 'voice': 0}  # 消息数量
        data['revoke'] = {'group': 20, 'temp': 0}  # 撤回消息延时(0为不撤回)
        data['at'] = False  # @
        data['at_warning'] = False  # @
        data['showTag'] = True  # 显示tag
        data['msg_inputError'] = '必须是小于3的数字哦~'  # 非int
        data['msg_notFind'] = '淦 你的xp好奇怪啊'  # 没结果
        data['msg_tooMuch'] = '要这么多色图你怎么不冲死呢¿'  # 大于最大值
        data['msg_lessThan0'] = '¿¿¿'  # 小于0
        data['msg_setuClosed'] = 'setu已关闭~'
        data['msg_r18Closed'] = '未开启r18~'
        data['msg_insufficient'] = '关于{tag}的图片只获取到{num}张'
        data['msg_frequency'] = '本群每{time}s能调用{num}次,已经调用{num_call}次,离刷新还有{r_time}s'
        # data['msg_'] = ''
        # return data

    def _updateData(self, data, group_id):
        if group_config.search(Q['GroupId'] == group_id):
            logger.info('群:{}已存在,更新数据~'.format(group_id))
            group_config.update(data, Q['GroupId'] == group_id)
        else:
            self.defaultdata(data)
            logger.info('群:{}不存在,插入数据~'.format(group_id))
            group_config.insert(data)

    @retry(stop_max_attempt_number=3, wait_random_max=2000)
    def updateAllGroupData(self):
        logger.info('开始更新所有群数据~')
        data = action.getGroupList()
        allgroups_get = [x['GroupId'] for x in data]
        for group in data:
            del group['GroupNotice']  # 删除不需要的key
            admins = action.getGroupAdminList(group['GroupId'])
            admins_QQid = [i['MemberUin'] for i in admins]
            group['admins'] = admins_QQid  # 管理员列表
            self._updateData(group, group['GroupId'])
        allgroups_db = [i['GroupId'] for i in group_config.all()]
        extraGroup = list(set(allgroups_db).difference(set(allgroups_get)))
        if extraGroup:  # 多余的群
            logger.info('数据库中多余群:{}'.format(extraGroup))
            for groupid_del in extraGroup:
                group_config.remove(Q['GroupId'] == groupid_del)
                logger.info('已删除群:{}数据'.format(groupid_del))
        logger.success('更新群信息成功~')
        return

    @retry(stop_max_attempt_number=3, wait_random_max=2000)
    def updateGroupData(self, group_id: int):
        logger.info('开始刷新群:{}的数据'.format(group_id))
        data = action.getGroupList()
        for group in data:
            if group['GroupId'] == group_id:
                del group['GroupNotice']  # 删除不需要的key
                admins = action.getGroupAdminList(group_id)
                admins_QQid = [i['MemberUin'] for i in admins]
                group['admins'] = admins_QQid
                logger.info('群:{}的admins:{}'.format(group_id, admins_QQid))
                self._updateData(group, group['GroupId'])
                return
        logger.warning('群:{}不存在~'.format(group_id))
