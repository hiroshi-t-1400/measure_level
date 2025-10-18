# Loraモジュール　親機(raspberry Pi Pico W)
# https://ushiken.net/micropython-prvtlora

######################################
#
# モジュールの読み込み
#
######################################

from gpiozero import DigitalInputDevice, DigitalOutputDevice # GPIO zeroライブラリからデジタル入出力クラスをインポート
import serial   # Raspberry Pi 3B+ でシリアル通信するためのライブラリ
import time    # timeライブラリをインポート
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

#  子機:0x00,0x00  親機:0x00,0x01 (0x00000001)
#  子機:0  親機:0
# LOW_ADRS_SEL = DigitalInputDevice(28) # 子機のみGPIO28をGNDに接続する設計にしておくと、システムを起動した時点でデバイス自身が子機か親機かを判別できる
# これは親機なので:1
LOW_ADRS_SEL = 0x01

######################################
#
# Raspberry Piの基板上LEDを設定
#
######################################

# led = Pin("LED", Pin.OUT)


######################################
#
# モジュールのピン設定
#
######################################

AUX = 25
M0 = 24
M1 = 23

TXD = 15 # Lora TXD <-> Pi UART RXD
RXD = 14 # Lora RXD <-> Pi UART TXD

# AUX pin
LR_AUX = DigitalInputDevice(AUX)
# M0 pin
LR_M0 = DigitalOutputDevice(M0)
# M1 pin
LR_M1 = DigitalOutputDevice(M1)


######################################
#
# モジュール初期設定
#
######################################

def lora_initst():
    ### 設定レジスタパラメータを設定 ###
    ## Config/DeepSleepモード（mode3）に設定
    # モジュールのアイドル状態を確認
    while LR_AUX.value == 0:
        time.sleep(0.010)

    LR_M0.on()
    LR_M1.on()

    # UARTの設定と初期化
    uart = serial.Serial(
        # port='/dev/ttyS0',
        port='/dev/serial0',
        baudrate=9600,
        bytesize=serial.EIGHTBITS, # bytesize(8)
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1.0 # 読み取り時のタイムアウトを1秒に設定
    )

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

    # 書き込みパケットを作成する
    # ヘッダー::書き込みコマンド:0xC0 スタートアドレス:0x00 書き込み数:0x08
    CMD = bytearray(b'\xC0\x00\x08')

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

    # add PARAM to command header
    CMD[len(CMD):] = bytes([ADR_H, ADR_L, REG0, REG1, REG2, REG3, CRYPT_H, CRYPT_L])

    ## 書き込み処理
    # 受信バッファクリア
    time.sleep(0.1) # モード設定後のインターバルを少し長くする
    if uart.in_waiting > 0: # ラズパイUART受信バッファが残っていれば全て読み込みして解消する
        data = uart.read(uart.in_waiting)
        print(f"設定前に受信バッファに残っていたバイト数{len(data)}")
        print(f"設定前に受信バッファに残っていたデータ{data}") # 同じ数字が出る？
        uart.reset_input_buffer() # 受信バッファを空にする

    # モジュールのアイドル状態を確認
    while LR_AUX.value == 0: # LoraモジュールのAUXがnot LOWはビジー状態なので解消するまで待つ
        time.sleep(0.01)

    # 書き込みを実行
    print("設定を書き込み中...")
    print(f"設定値: {CMD}")
    uart.write(CMD)
    
    ## 初期設定終了処理
    # パラメータを読み込み,Loraモジュールの設定レジスタに書き込みを行うと結果を送り返してくるので受信する
    while uart.in_waiting == 0:
        print("モジュールからのレスポンスを待っています")
        time.sleep(0.1)
    else:
        rspns = uart.read(uart.in_waiting)
        print(f"設定のレスポンスバイト数： {len(rspns)}")
        print(f"設定のレスポンスデータ： {rspns}")

    # モジュールのアイドル状態を確認
    while LR_AUX.value == 0:
        time.sleep(0.01)

    # 通常送受信モードに設定
    LR_M0.off()
    LR_M1.off()

    time.sleep(0.200)

    print("モジュールの設定完了")

    return uart


######################################
#
#   送信
#
######################################

def lora_transmission(uart,txdt):
    
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
    time.sleep(0.2)
    if uart.in_waiting > 0:
        uart.reset_input_buffer()
    
    # モジュールのアイドル状態を確認
    while LR_AUX.value == 0:
        time.sleep(0.01)
    
    # 送信
    uart.write(payload)
    print(f"送信データ:{payload}")

    # モジュールのアイドル状態を確認
    while LR_AUX.value == 0:
        time.sleep(0.01)

    return


######################################
#
#   送信,子機へのRTC同期
#
######################################

def lora_ensync_rtc(uart):
    
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
    # 4byte
    format_string = '>I'
    
    payload += struct.pack(format_string, int(time.time()))
    
    # 受信バッファをクリア
    time.sleep(0.2)
    if uart.in_waiting > 0:
        uart.reset_input_buffer()
    
    # モジュールのアイドル状態を確認
    while LR_AUX.value == 0:
        time.sleep(0.01)
    
    # 送信
    uart.write(payload)
    print(f"送信データ:{payload}")

    # モジュールのアイドル状態を確認
    while LR_AUX.value == 0:
        time.sleep(0.01)

    return


######################################
#
#   受信
#
######################################

def lora_receive(uart):
    print("受信中......")
    payload = bytes()
    rcv_data = bytes()
    rssi = 0

    # データ受信待ち (LR_AUXがLOWになるのを待つ)
    # LR_AUXがLOWになるのを待つ（データ受信開始の合図）
    while LR_AUX.value == 1:
        time.sleep(0.01)
        # CPU負荷を軽減するため、短いスリープを入れます
        pass
    
    print("データ受信開始")

    # データ受信完了待ち (LR_AUXがHIGHに戻るまでループ)
    while LR_AUX.value == 0:
        if uart.in_waiting > 0:
            payload += uart.read(uart.in_waiting)
        time.sleep(0.01) # CPU負荷を軽減

    # ループを抜けた直後の取りこぼしを防ぐ
    if uart.in_waiting > 0:
        payload += uart.read(uart.in_waiting)

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

    #rcv_data = rcv_data.decode("utf-8")
#    format_string = 'B B B I I I I I B'
#    format_string = 'I I I I I'
    format_string = '>IIIII'
    rcv_data = struct.unpack(format_string, rcv_data)

    # 受信処理のクールダウン待ち
    time.sleep(0.1)

    return rcv_data, rssi


######################################
#
#   メイン
#
######################################


# モジュールの初期設定を実行
uart = lora_initst()

time.sleep(2)

while True:
    # 受信
    rcv_data, rssi = lora_receive(uart)

    # ローカル時刻設定
    lcl_tm = time.localtime()
    tm = ("%2d:%02d:%02d" % (lcl_tm[3:6]))
    print(f"受信: {tm}")

    #print(f"受信データ: {rcv_data}")

    (timestamp, d1, d2, d3, d4) = rcv_data
    final_distances = [d1 / 10.0, d2 / 10.0, d3 / 10.0, d4 / 10.0]


    print(f"Time: {time.ctime(timestamp)}")
    print(f"Distances (cm): {final_distances}")
    print(f"RSSI: {rssi}dBm")

    time.sleep(0.5)
    # UNIX時間を送信、子機のRTCを同期
    lora_ensync_rtc(uart)

    time.sleep(10)

