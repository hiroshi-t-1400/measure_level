import utime
import machine


# ５９分間までは同じ設計でインターバルを変動できる
# 
# def schedule_5m_intervals(interval):
# wait_mins = interval - t_now[4] % interval
# wait_seconds += interval * 60

def schedule_mins_intervals():
    while True:
        t_now = utime.localtime()

        print(f"debug:utime.time(): {utime.time()}")
        print(f"debug:utime.localtime :{utime.localtime()}")
        print(f"debug:t_now[4]: {t_now[4]}")

        wait_mins = 5 - t_now[4] % 5 # 次の５分刻みの時刻までの分（秒は次で補正）
        adj_seconds = t_now[5]
        wait_seconds = wait_mins * 60 - adj_seconds # 次の五分刻みの時刻までの累計秒数

        # 測距モジュールのリセット待ち時間があり１サイクル１０回の測定に１５秒程度かかる。
        # 余裕をもってスリープ時間が３０秒未満になる場合は次の５分刻みの時刻に持ち越す。
        print(f"debug:３０未満スキップ前のwait_seconds: {wait_seconds}")
        if wait_seconds < 30:
            wait_seconds += 300
        print(f"debug:３０調整後のwait_seconds: {wait_seconds}")

        # wait_secondsがゼロまたは負の値になった場合のガード
        if wait_seconds <= 0:
            print("警告: 待ち時間がマイナスの値になりました。スケジュールを再設定します。")
            utime.sleep(1) # 1秒待って無限ループを避ける
            continue
        break
            

    # 待ち時間が十分に長い場合はlightsleepを使用
    if wait_seconds > 60:
        try:
            # 予定時刻５秒前までlightsleepし、最後５秒をsleepで待機する
            print(f"debug: lightsleepを実行します")
            print(f"debug: sleeptime: {int((wait_seconds - 5) * 1000)}")
#             machine.lightsleep(int((wait_seconds - 5) * 1000))
            utime.sleep(5)
        except Exception:
            # 例外処理：なんかのエラーなどでlightsleepが使えない
            utime.sleep(wait.seconds)
    else:
        # ６０秒よりも短ければsleepで待つ
        utime.sleep(wait_seconds)
        
while True:
    print("１０秒待機")
    utime.sleep(10)
    print("関数を実行します")
    schedule_mins_intervals()
    print("スリープから復帰しました")
        
#     print(f"予定時刻になったので距離測定を始めます")
