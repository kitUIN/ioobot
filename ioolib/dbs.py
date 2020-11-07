import json
import pathlib
import sys
from botoy import Action, Botoy
from loguru import logger
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
try:
    pathlib.Path('db').mkdir()
    logger.success('数据库创建成功')
except FileExistsError:
    logger.info('数据库目录已存在')
try:
    with open('config.json', 'r', encoding='utf-8') as f:  # 从json读配置
        config = json.loads(f.read())
        logger.success('加载配置文件成功~')
except Exception as e:  # FileNotFoundError
    logger.error('配置文件加载失败,请检查配置~'+str(e))
    sys.exit()
group_config = TinyDB('./db/group_config.json')
friend_config = TinyDB('./db/friend_config.json')
tag_db = TinyDB('./db/tag.json')
status = TinyDB('./db/status.json')
db_tmp = TinyDB(storage=MemoryStorage)
Q = Query()
bot = Botoy(qq=config['BotQQ'], host=config['host'], port=config['port'], use_plugins=config['use_plugins'],
            log=config['log'], log_file=config['log_file'])
action = Action(qq=config['BotQQ'])
