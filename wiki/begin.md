# 如何开始
PS：测试环境:
- Ubuntu 18.04 LTS (GNU/Linux 3.18.22+ aarch64)  
- Python 3.6.5
- OPQBOT 6.0.0  

**1.下载项目或者克隆**  
- `git clone https://github.com/kitUIN/ioobot.git`
- 配置环境  
- `pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
**2.填写配置文件**  
文件`config.json`
```
{
  "BotQQ": 0,                   #[botoy]你的机器人号（必填）
  "host": "http://127.0.0.1",   #[botoy]连接地址
  "port": 8888,                 #[botoy]端口
  "use_plugins": false,         #[botoy]插件开关
  "log": false,                 #[botoy]日志
  "log_file": false,            #[botoy]日志输出
  "superAdmin": 0,              #[权限模块]超级管理员（必填）
  "path": "",                   #[setu模块]本地图片地址
  "LoliconAPIKey": "",          #[setu模块]LOLICON的apikey
  "SauceNAOKEY": "",            #[识图姬]SauceNAO的访问key
  "search_proxies": false,      #[识图姬]代理开关
  "proxy": "http://127.0.0.1:10809",#[识图姬][pixiv][setu模块]代理端口
  "netease": false,             #[网易云vip解析]开关
  "netease_username": "",       #[网易云vip解析]账号
  "netease_password": "",       #[网易云vip解析]密码
  "pixiv": false,               #[pixiv]开关(需要梯子)
  "pixiv_username": "",         #[pixiv]账号
  "pixiv_password": "",         #[pixiv]密码
  "refresh_token": "",          #[pixiv]token
  "access_token": "",           #[pixiv]token
  "bilibili": false,            #[bilibili]开关
  "bilibili_username": "",      #[bilibili]账号
  "bilibili_password": ""       #[bilibili]密码
  }
}
```
对botoy有更多要求的可以更改`botoy.json`

**3.启动插件**  
先确认OPQBOT正常运行
执行`./run.py`