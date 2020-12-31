import json
import pathlib
import sys

from botoy import Action, Botoy
from loguru import logger
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

# ------------------文件夹------------------
try:
    pathlib.Path('db').mkdir()
    logger.success('数据库创建成功')
except FileExistsError:
    logger.info('数据库目录已存在')
try:
    pathlib.Path('pixiv').mkdir()
    logger.success('Pixiv存储库创建成功')
except FileExistsError:
    logger.info('Pixiv存储库已存在')

# ------------------配置------------------
config = dict()


def load_config():
    global config
    update = False
    new = list()
    old = list()
    try:
        with open('config.json', 'r', encoding='utf-8') as v:  # 从json读配置
            config = json.loads(v.read())
            for y in config:
                old.append(y)
            config_new = config
            logger.success('加载配置文件成功~')
        with open('config_example.json', 'r', encoding='utf-8') as ex:
            config_example = json.loads(ex.read())
            for x in config_example:
                new.append(x)
            for i in new:
                if i not in old:
                    update = True
                    config_new[i] = config_example[i]
        try:
            if update:
                logger.warning('Σ(ﾟдﾟ；)检测到新的配置文件版本')
                with open('config.json', 'w', encoding='utf-8') as f:
                    f.write(json.dumps(config_new, ensure_ascii=False, indent=4))
                logger.success('(￣▽￣)ノ配置文件更新成功，请注意填写新的条目')
        except Exception as e:  # FileNotFoundError找不到文件
            logger.error('_(：3 」∠ )_配置文件更新失败' + str(e))
    except Exception as e:  # FileNotFoundError找不到文件
        logger.error('_(：3 」∠ )_配置文件加载失败,请检查配置~' + str(e))
        sys.exit()


def create_config():
    with open('config_example.json', 'r', encoding='utf-8') as f:  # 从json读配置
        config_example = json.loads(f.read())
        with open('config.json', 'w', encoding='utf-8') as g:
            g.write(json.dumps(config_example, ensure_ascii=False, indent=4))
    file_dir = pathlib.Path("./config.json").exists()
    if file_dir:
        logger.success('(￣▽￣)ノ配置文件已创建，请填写配置文件')
    else:
        logger.error('_(：3 」∠ )_配置文件创建失败')
        sys.exit()


file = pathlib.Path("./config.json").exists()
if file:
    load_config()
else:
    logger.info('未检测到配置文件_(┐「ε:)_')
    create_config()
if config["BotQQ"] == 0 or config["superAdmin"] == 0:
    logger.error('_(┐「ε:)_配置文件未填写,请检查配置文件中"BotQQ"与"superAdmin"~')
    sys.exit()
# ------------------数据库------------------
group_config = TinyDB('./db/group_config.json')
friend_config = TinyDB('./db/friend_config.json')
tag_db = TinyDB('./db/tag.json')
status = TinyDB('./db/status.json')
pixiv_db = TinyDB('./db/pixiv.json')
rank = TinyDB('./db/rank.json')
db_tmp = TinyDB(storage=MemoryStorage)
Q = Query()
# ------------------bot启动参数------------------
bot = Botoy(qq=config['BotQQ'], host=config['host'], port=config['port'], use_plugins=config['use_plugins'],
            log=config['log'], log_file=config['log_file'])
action = Action(qq=config['BotQQ'])
