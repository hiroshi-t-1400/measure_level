# サーバーと同期してUNIX時間を現実時間に校正
from machine import RTC
import time

rtc = RTC()
# 日本標準時JSTに修正するための変数
JST_OFFSET_SECONDS = 9 * 3600

def sync_rtc(server_unix_time):

    # Jst Unix Time
    jut = utime.localtime(server_unix_time + JST_OFFSET_SECONDS)
    JST_UNIX_TIME = (jut[0], jut[1], jut[2], jut[6], jut[3], jut[4], jut[5], 0)
    rtc.datetime(JST_UNIX_TIME)

    tm = rtc.datetime()
    print(f"RTC設定後の時刻: {tm[0]}-{tm[1]:02d}-{tm[2]:02d} {tm[4]:02d}:{tm[5]:02d}:{tm[6]:02d}")

    return

