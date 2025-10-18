# 防水超音波モジュール JSN-SR04T / AJ-SR04M

from machine import Pin
import utime

# GPIOの設定
TRIG_PIN = 16
ECHO_PIN = 17

# 音速の設定(cm/s)
# 33768 10℃ 
# 34065 15℃
speed_of_sound = 33887 # 12℃

# ピンの割り当て
TRIG = Pin(TRIG_PIN, Pin.OUT)
ECHO = Pin(ECHO_PIN, Pin.IN)


def measure_distance():

    # Tirgピンを10usだけHIGHにしてモジュールを起動、測定実行
    TRIG.value(1)
    utime.sleep_us(10)
    TRIG.value(0)

    while ECHO.value() == 0:
        pass
    t1 = utime.ticks_us() # 超音波発振時刻

    while ECHO.value() == 1:
        pass
    t2 = utime.ticks_us() # 超音波受信時刻

    td_s = utime.ticks_diff(t2, t1) / 1000000 # 超音波の往復飛行時間(s)

    distance_cm = (td_s * speed_of_sound) / 2 # 距離計算(cm)

    # クールダウンを待機。連続して観測しようとするとスタックする
    utime.sleep(1)

    return distance_cm
