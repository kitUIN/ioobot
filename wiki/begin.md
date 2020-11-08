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
  "Version": "v2.0.0",          #版本
  "path": "",                   #[setu模块]本地图片
  "LoliconAPIKey": "",          #[setu模块]LOLICON的apikey
  "version": {                  #版本内容
  }
}
```
对botoy有更多要求的可以更改`botoy.json`

**3.启动插件**  
先确认OPQBOT正常运行
执行`./run.py`