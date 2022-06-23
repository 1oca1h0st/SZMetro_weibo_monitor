from ast import dump
from email import contentmanager
from operator import truediv
import sqlite3
from sqlite3 import Error
import datetime
from urllib import response
import requests
import json
from urllib.parse import quote, quote_plus
import os
import configparser
from black import main

current_dir = os.path.dirname(os.path.abspath(__file__))

conf = configparser.ConfigParser()
conf.read(os.path.join(current_dir, 'config.ini'))
BARK_URL = conf.get("BARK", "URL")
BARK_KEY = conf.get("BARK", "KEY")

try:
    conn = sqlite3.connect(os.path.join(current_dir, 'weibo.db'))
except Error:
    print(Error)
    exit()


def create_table():
    try:
        content = """CREATE TABLE IF NOT EXISTS content
        (id TEXT,
        text TEXT,
        edit_count TEXT,
        noti_count TEXT);
        """
        #total = """CREATE TABLE IF NOT EXISTS total (total TEXT)"""
        conn.execute(content)
        # conn.execute(total)
        return True
    except Error:
        print(Error)
        return False


def get_sz_metro():
    cur = conn.cursor()
    url = "https://m.weibo.cn/api/container/getIndex?uid=2311331195&t=0&luicode=10000011&lfid=100103type%3D1%26q%3D%E6%B7%B1%E5%9C%B3%E5%9C%B0%E9%93%81&containerid=1076032311331195"
    headers = {
        'authority': 'm.weibo.cn',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'referer': 'https://m.weibo.cn/u/2311331195?uid=2311331195&t=0&luicode=10000011&lfid=100103type%3D1%26q%3D%E6%B7%B1%E5%9C%B3%E5%9C%B0%E9%93%81',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
    }
    response = requests.get(url=url, headers=headers)
    if(response.status_code == 200):
        content = json.loads(response.text)
        for i in content['data']['cards']:
            if "延误" in i['mblog']['text']:
                id = i['mblog']['id']
                text = i['mblog']['text']
                try:
                    edit_count = i['mblog']['edit_count']
                except:
                    edit_count = 0
                sql = "select * from content where id = %s and edit_count = %s" % (
                    str(id), str(edit_count))
                cur.execute(sql)
                if cur.fetchone():
                    # 有记录，不进行通知
                    print("已有该条记录，ID为：%s" % str(id))
                else:
                    insert_sql = "insert into content values ('%s', '%s', '%s', '0')" % (
                        id, text, edit_count)
                    conn.execute(insert_sql)
                    conn.commit()
                    print("%s-%s-%s" % (str(id), text, str(edit_count)))
                    bark_notification(id)
    else:
        return False


def bark_notification(id):
    sql = "select text from content where id = %s" % str(id)
    cur = conn.cursor()
    cur.execute(sql)
    text = cur.fetchone()
    url = "%s/%s/地铁延误通知/%s" % (BARK_URL, BARK_KEY, quote_plus(text[0]))
    response = requests.get(url=url)
    print(response.status_code)


if __name__ == "__main__":
    # 时间仅在早上7:01-8:59执行，晚上5:01-6:59执行
    now = datetime.datetime.now()
    now_hour = now.__getattribute__('hour')
    now_minute = now.__getattribute__('minute')
    if str(now_hour) in ('7', '8', '17', '18'):
        if(int(now_minute) % 5 == 0):
            if create_table():
                if get_sz_metro():
                    print("ok")
        else:
            print("未到执行时间")
    conn.close()
