# SZMetro_weibo_monitor
监控深圳地铁的微博，当出现延误新闻时通过bark实时推送通知到移动端

需要修改BARK_URL（若自建消息推送端）和BARK_KEY两个信息

---

使用方法：

1. 修改linux的crontab，设置为 `* * * * * python3 main.py >> /var/log/weibo.log`

2. 修改main.py中main函数内的执行时间，默认情况下是在每日的7、8、17、18时期间每5分钟进行一次轮训，查询深圳地铁的新发微博是否有“延误”两个词，存在则进行推送。

3. 数据保存在脚本同级目录的weibo.db中，采用sqlite3数据库存储
