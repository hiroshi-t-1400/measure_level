# サーバーと同期してUNIX時間を現実時間に校正
from machine import RTC
import time

rtc = RTC()

def sync_rtc(server_unix_time):

    rtc.datetime(time.ctime(server_unix_time))
    print(f"サーバーと時刻同期します: {time.ctime(server_unix_time)}")

    return

