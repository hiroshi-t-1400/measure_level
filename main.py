import utime
import sr04
import data_processor
import lora_comm
import sync_rtc
import machine

# RTC校正用の変数定義、ただしループ１回目はリセットされていて誤った時刻が使われる＊できれば直す
rtc = machine.RTC()

# モジュールの初期設定を実行
lora_comm.lora_initst()

def rtc_drift_compensate(sleep_duration_ms):
    """
    lightsleepで停止したRTCを実時間に補正する
    前回のスリープ時間をsleep_duration_msで受け取る
    """
    if sleep_duration_ms <= 0:
        return
    
    # 現在のRTCを取得: tuple
    current_rtc_tuple = rtc.datetime()
    # unixシリアルと揃えるために並び替え
    utime_tuple = (
        current_rtc_tuple[0],
        current_rtc_tuple[1],
        current_rtc_tuple[2],
        current_rtc_tuple[4],
        current_rtc_tuple[5],
        current_rtc_tuple[6],
        current_rtc_tuple[3],
        0
        )
    current_unix = utime.mktime(utime_tuple)

    # ずれの補正 //は余りを省いた商
    cs_lcltm = current_unix + (sleep_duration_ms // 1000)

    # RTC.datetimeに並び替え(年, 月, 日, 曜日, 時, 分, 秒, subseconds)
    rtc_set_tuple = (
        cs_lcltm[0],
        cs_lcltm[1],
        cs_lcltm[2],
        cs_lcltm[6],
        cs_lcltm[3],
        cs_lcltm[4],
        cs_lcltm[5],
        0
    )

    rtc.datetime(rtc_set_tuple)
    print(f"RTCを {sleep_duration_ms} ミリ秒分補正しました。")


def schedule_5m_interval():
    """
    ５分に１度スリープを解除し測定、送信を行うメイン関数を間欠運転する
    """
    while True:
        ## メイン関数部
        get_data = []

        # 距離測定を１０回実行
        for loop in range(10):
            get_data.append(sr04.measure_distance())

        current_time = int(utime.time()) # 4バイト

        # データの成形
        txdt = data_processor.data_modify(get_data, current_time)

        # LoRaモジュールの送信
        lora_comm.lora_transmission(txdt)

        # サーバーとの時刻同期
        server_unix_time, rssi = lora_comm.get_server_unixtime()
        if server_unix_time != -1:
            sync_rtc.sync_rtc(server_unix_time)
        else:
            print("サーバーとの時刻同期に失敗しました")

        ## スリープ関数部
        t_now = utime.localtime()

        wait_mins = 5 - t_now[4] % 5 # 次の５分刻みの時刻までの分（秒は次で補正）
        current_seconds = t_now[5]
        wait_seconds = wait_mins * 60 - current_seconds # 次の五分刻みの時刻までの累計秒数

        # ガード処理:wait_secondsがゼロまたは負の値になった場合
        if wait_seconds <= 0:
            print("警告: 待ち時間がゼロかマイナスになりました。LIGHTSLEEPをスキップして測定を再開します")
            utime.sleep(1) # 1秒待って先頭のwhile最初まで戻る
            continue

        # スリープ移行が確定
        wait_ms = int(wait_seconds * 1000)

        # 待ち時間が十分に長い場合はlightsleepを使用
        if wait_seconds > 60:
            try:
                # 予定時刻５秒前までlightsleepし、最後５秒をsleepで待機する
                LS_time_ms = wait_ms - 5000
                if LS_time_ms > 0:
                    print(f"debug: lightsleepを実行します")
                    print(f"debug: sleeptime: {LS_time_ms}")
                    utime.sleep(0.3) # デバッグ用、待たないとシェルにprintが出力されない
                    machine.lightsleep(LS_time_ms)
                    sleep_duration_actual = LS_time_ms
                utime.sleep(5)
            except Exception:
                # 例外処理：なんかのエラーなどでlightsleepが使えない
                utime.sleep(wait_seconds)
        else:
            # ６０秒よりも短ければsleepで待つ
            utime.sleep(wait_seconds)

        # lightsleepから復帰度、RTCの補正を行う
        rtc_drift_compensate(sleep_duration_actual)

        # システムが安定するようにループ前にちょっと待つ
        utime.sleep(1)

schedule_5m_interval()


