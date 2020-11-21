import requests
from bs4 import BeautifulSoup
def tizi():
    url = 'https://fly.catcottage.us/user'
    params = dict()
    params['cookie'] = '_ga=GA1.2.1410943729.1605321776; _gid=GA1.2.1845503948.1605860874; uid=2459; email=1455097289%40qq.com; key=cdbf58f46231e687b78fccde1b5b8f40587e55a0b9cb3; ip=1731b22c04065f17910068a46d26033d; expire_in=1606465685'
    params['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 Edg/86.0.622.69'
    res = requests.get(url,params=params)
    content = res.content
