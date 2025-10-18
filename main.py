import utime
import sr04
import data_processor
import lora_comm
import sync_rtc


lora_comm.lora_initst()


while True:

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
    
    print("１サイクル終了、５分間のインターバルに入ります")

    utime.sleep(300)
