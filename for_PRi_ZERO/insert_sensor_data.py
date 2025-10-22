import pymysql
import time
import datetime

# --- データベース接続設定 ---
# 変更点: Dockerサービス名 'db' から Ubuntu PCのIPアドレス '192.168.11.20' へ変更
DB_HOST = '192.168.11.20'
DB_PORT = 3306
DB_DATABASE = 'home_db'
DB_USERNAME = 'home_user'
DB_PASSWORD = '12345678'
TABLE_NAME = 'sensors'

# --- 仮の観測データ ---
# タイムスタンプはUNIXタイム形式 (int)
OBSERVATION_TIMESTAMP = 1761131353
DATA_1 = 56.4
DATA_2 = 56.3
DATA_3 = 56.2
DATA_4 = 56.4


def insert_sensor_data():
    """
    MariaDBにセンサーデータを登録する関数
    """
    # データの平均値を計算
    average = (DATA_1 + DATA_2 + DATA_3 + DATA_4) / 4.0
    
    # データベースのDATETIME型用にUNIXタイムスタンプをDatetimeオブジェクトに変換
    # created_at, updated_at にも同じ値を設定
    dt_object = datetime.datetime.fromtimestamp(OBSERVATION_TIMESTAMP)
    
    # Laravelのマイグレーションで定義された created_at と updated_at フィールド用に現在時刻を取得
    # NOTE: Laravelは通常、DBレベルでこれらを自動で設定しますが、
    # 外部スクリプトからの挿入では明示的に指定する必要があります。
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = None # 接続オブジェクトを初期化
    try:
        # データベース接続の確立
        # Pi 3B+から 192.168.11.20 のMariaDBへ接続を試みる
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            # 挿入するSQLクエリ
            sql = f"""
            INSERT INTO {TABLE_NAME} 
            (observation_time, data1, data2, data3, data4, average, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # クエリに渡す値
            # observation_timeはDatetimeオブジェクトの形式で渡す
            values = (
                dt_object, 
                DATA_1, 
                DATA_2, 
                DATA_3, 
                DATA_4, 
                average, 
                now, 
                now
            )

            # クエリの実行
            cursor.execute(sql, values)
        
        # 変更をコミット（データベースに反映）
        conn.commit()
        print(f"✅ データ登録に成功しました。ID: {cursor.lastrowid}, 平均値: {average:.2f}")

    except pymysql.Error as e:
        print(f"❌ データベースエラーが発生しました: {e}")
        print("💡 以下の点を確認してください:")
        print("   - Ubuntu PC (192.168.11.20) のDockerコンテナが起動しているか。")
        print("   - DockerのMariaDBポート(3306)がホストOS(Ubuntu)に公開されているか。")
        print("   - MariaDBがPi 3B+からの接続を許可する設定になっているか。")

    finally:
        # 接続を閉じる
        if conn:
            conn.close()

if __name__ == '__main__':
    insert_sensor_data()
