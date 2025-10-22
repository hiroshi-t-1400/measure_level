# Lora通信モジュール制御
# LoRaモジュール評価ボード E220-900T22S(JP)-EV1

from machine import Pin, UART
import utime    # timeライブラリをインポート
import struct   # MicroPython組み込みモジュール structライブラリをインポート
# データ型の操作など

######################################
#
# グローバル変数
#
######################################

#RSSIバイト (1:有効, 2:無効)
GLBL_RSSI_BYTE = 1

######################################
#
# モジュール自アドレス選択(下位アドレス)
#
######################################

# 子機:0x00,0x00  親機:0x00,0x01 (0x00000001)
LOW_ADRS_SEL = 0x00 # 子機

######################################
#
# モジュールのピン設定
#
######################################

# ピンの設定
AUX = 2
M0 = 3
M1 = 4

TXD = 1 # Lora TXD <-> Pi UART0 RXD
RXD = 0 # Lora RXD <-> Pi UART0 TXD

# ピンの割り当て
LR_AUX = Pin(AUX, Pin.IN) 
LR_M0 = Pin(M0, Pin.OUT)
LR_M1 = Pin(M1, Pin.OUT)


######################################
#
# UARTモジュール初期設定
#
######################################


# UARTの設定と初期化
uart = UART(0, baudrate=9600, tx=Pin(RXD), rx=Pin(TXD))
uart.init(9600, bits=8, parity=None, stop=1, timeout=1000)


# 設定レジスタにパラメータを設定
## 行末尾はレジスタアドレス (00H等
# 自デバイスアドレス=0x0001(親機), 0x0000(子機) (00H,01H
# baud_rate=9600bps (02H
# bw=125kHz (02H
# sf=9 (02H
# ペイロード長=64byte (03H
# RSSI環境ノイズ=無効 (03H
# 送信出力13dBm (03H
# 待ち受け周波数チャンネル=0 (04H
# RSSIバイト出力=有効 (05H
# 送信方法=通常送信モード (05H
# 低電圧動作(L22限定)=無効 (05H
# WORサイクル=3000ms (005
# 暗号化キー=0x0000 (06H,007H

# 00H ADDH
ADR_H = 0x00
# 01H ADDL
ADR_L = LOW_ADRS_SEL
# 02H REG0
REG0 = 0x70
# 03H REG1
REG1 = 0x81
# 04H REG2
REG2 = 0x00
# 05H REG3
REG3 = 0xC5
# 06H CRYPT_H
CRYPT_H = 0x00
# 07H CRYPT_L
CRYPT_L = 0x00


def lora_initst():
    ### 設定レジスタパラメータを設定 ###
    ## Config/DeepSleepモード（mode3）に設定
    # モジュールのアイドル状態を確認
    while LR_AUX.value() == 0:
        utime.sleep_ms(10)

    # mode3 M0:0 M1:0
    LR_M0.value(1)
    LR_M1.value(1)

    # 書き込みパケットを作成する
    # ヘッダー::書き込みコマンド:0xC0 スタートアドレス:0x00 書き込み数:0x08
    CMD = bytearray(b'\xC0\x00\x08')

    # add PARAM to command header
    CMD[len(CMD):] = bytes([ADR_H, ADR_L, REG0, REG1, REG2, REG3, CRYPT_H, CRYPT_L])

    ## 書き込み処理
    # 受信バッファクリア
    utime.sleep(0.1) # モード設定後のインターバルを少し長くする
    if uart.any() > 0:
        data = uart.read()
        print(f"設定前に受信バッファに残っていたデータ{data}") # 同じ数字が出る？

    # モジュールのアイドル状態を確認
    while LR_AUX.value() == 0: # LoraモジュールのAUXがnot LOWはビジー状態なので解消するまで待つ
        utime.sleep_ms(10)

    # 書き込みを実行
    print("設定を書き込み中...")
    print(f"設定値: {CMD}")
    uart.write(CMD)
    
    ## 初期設定終了処理
    # パラメータを読み込み,Loraモジュールの設定レジスタに書き込みを行うと結果を送り返してくるので受信する
    while uart.any() == 0:
        print("モジュールからのレスポンスを待っています")
        utime.sleep(0.1)
    else:
        rspns = uart.read()
        print(f"設定のレスポンスデータ： {rspns}")

    # モジュールのアイドル状態を確認
    while LR_AUX.value() == 0:
        utime.sleep(0.01)

    # 通常送受信モードに設定
    LR_M0.value(0)
    LR_M1.value(0)

    utime.sleep(0.2)

    print("モジュールの設定完了")

    return uart


######################################
#
#   送信
#
######################################

# def lora_transmission(uart,txdt):
def lora_transmission(txdt):
    
    # 送信上位アドレス(0x00)
    TX_ADR_H = 0x00

    # 送信アドレス選択(下位アドレス)
    if LOW_ADRS_SEL == 1:
        # 送信先下位アドレス(0x01)
        TX_ADR_L = 0x00
    else:
        # 送信先下位アドレス(0x00)
        TX_ADR_L = 0x01

    # 送信先チャンネル(0x01)
    CHNL = 0x00

    # 送信データにアドレスとチャンネルを設定、loraモジュールで通信用のヘッダーとして処理される
    payload = bytes([TX_ADR_H, TX_ADR_L, CHNL])

    # タイムスタンプ、測定データ４つのレジスタをパックする
    # 4byte , 4byte x4
    format_string = '>IIIII'
    
    payload += struct.pack(format_string, *txdt)

    # 受信バッファをクリア
    utime.sleep(0.2)
    if uart.any() > 0:
        uart.read()
        print("受信バッファをクリアしました")

    # モジュールのアイドル状態を確認
    while LR_AUX.value() == 0:
        utime.sleep(0.01)

    # 送信
    uart.write(payload)
    print(f"送信データ:{payload}")

    # モジュールのAUXの信号が変わるのを待つ、待たないとHIGHからビジーのLOWに変わってないことがある
    utime.sleep(0.5)
    # モジュールのアイドル状態を確認
    while LR_AUX.value() == 0:
        utime.sleep(0.01)

    return


######################################
#
#   子機専用受信、RTC校正用
#
######################################
# データ送信後に実行、２秒間待機し４バイトのUNIX時間を受け取る

def get_server_unixtime():
    print("RTC校正データ受信中...")
    payload = bytes()
    rcv_data = bytes()
    rssi = 0

    # データ受信待ち
    # RTC校正データは４バイトで短いためAUXの信号で動作を監視できない
    # 受信バッファの有無でモジュールの動作を監視する
    rcv_start_time = utime.time() # タイムアウト計測用
    while uart.any() == 0:
        utime.sleep(0.1)
        # ２秒間サーバーからの送信が無ければタイムアウトで抜ける、返り値-1でエラーを返す
        if utime.time() - rcv_start_time > 2:
            return -1
        pass

    # データの受信を確認、バッファ内のデータを取得
    while uart.any() > 0:
        payload += uart.read()
        utime.sleep_ms(10)

    # ループを抜けた直後の取りこぼしを防ぐ
    if uart.any() > 0:
        payload += uart.read()

    # 受信データ処理
    if len(payload) > 0:
        if GLBL_RSSI_BYTE == 1:
            # RSSIバイトが有効な場合、最後の1バイトはRSSI値
            if len(payload) > 1:
                rcv_data = payload[:-1]
                rssi = int(payload[-1]) - 256
            else:
                # データが1バイトしかなく、RSSIバイトのみの可能性がある
                rcv_data = bytes() # データ部は空
                rssi = int(payload[-1]) - 256
            # print(f"受信完了。RSSI: {rssi} dBm")
        else:
            # RSSIバイトが無効な場合、payloadすべてがデータ
            rcv_data = payload
            # print("受信完了。RSSIバイトは無効です。")
        # print(f"受信データ: {rcv_data}")
    else: # AUXが0で受信アクティブになったが受信バッファにデータ存在しなかった
        print("データを受信できませんでした。")

#    format_string = 'I I I I I'
    format_string = '>I'
    (unix_time, ) = struct.unpack(format_string, rcv_data)

    # 受信処理のクールダウン待ち
    utime.sleep(0.1)

    return unix_time, rssi
