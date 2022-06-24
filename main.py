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
        noti_count TEXT,
        scheme TEXT);
        """
        count = """CREATE TABLE IF NOT EXISTS count
        (count TEXT,
        date TEXT);"""
        conn.execute(content)
        conn.execute(count)
        return True
    except Error:
        print(Error)
        return False


def get_sz_metro(flag):
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
                scheme = i['scheme']
                sql = "select * from content where id = %s and edit_count = %s" % (
                    str(id), str(edit_count))
                cur.execute(sql)
                if cur.fetchone():
                    # 有记录，不进行通知
                    print("已有该条记录，ID为：%s" % str(id))
                else:
                    insert_sql = "insert into content values ('%s', '%s', '%s', '0', '%s')" % (
                        id, text, edit_count, scheme)
                    conn.execute(insert_sql)
                    conn.commit()
                    print("%s-%s-%s" % (str(id), text, str(edit_count)))
                    if flag:
                        bark_notification(id)
    else:
        return False


def bark_notification(id):
    sql = "select text,scheme from content where id = %s" % str(id)
    cur = conn.cursor()
    cur.execute(sql)
    text = cur.fetchone()
    cur.close()
    url = "%s/%s/地铁延误通知/%s?url=%s" % (BARK_URL, BARK_KEY,
                                      quote_plus(text[0]), quote_plus(text[1]))
    response = requests.get(url=url)
    if response.status_code == 200:
        count_sql = "insert into count values ('1','%s')" % str(
            datetime.date.today().isoformat())
        conn.execute(count_sql)
        conn.commit()


def happy():
    sql = "select * from count where date = '%s'" % str(datetime.date.today().isoformat())
    cur = conn.cursor()
    cur.execute(sql)
    if len(cur.fetchall()) == 0:
        requests.get("%s/%s/地铁延误通知/暂无延误消息，快乐出行！" % (BARK_URL, BARK_KEY))
    else:
        print("已经发过延误消息了")
    cur.close()


if __name__ == "__main__":
    create_table()
    # 时间仅在早上7:01-8:59执行，晚上5:01-6:59执行
    now = datetime.datetime.now()
    now_hour = now.__getattribute__('hour')
    now_minute = now.__getattribute__('minute')
    if str(now_hour) in ('7', '8', '17', '18'):
        if(int(now_minute) % 5 == 0):
            if get_sz_metro(True):
                print("ok")
        else:
            print("未到执行时间")
    else:
        if(int(now_minute) == 0 and int(now_hour) % 2 == 0):
            # 剩余的时间每2个小时的采集一次信息
            # 防止在非运行时间段修改了之前的延误信息，会导致到下次开始的时候再推送
            get_sz_metro(False)
    # 8:15和18:15推送是否有延误的通知信息
    if str(now_hour) in ('8', '18') and str(now_minute) == "15":
        happy()
    conn.close()
