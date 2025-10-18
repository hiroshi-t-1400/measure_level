# データの格納と成形

import utime    # timeライブラリをインポート

def data_modify(get_data, current_time):

    modified_data = []

    get_data.sort() # リストをソート**タプルは不可
    length_distance = len(get_data)

    get_data = get_data[3:length_distance-3] # 最大最小３つずつ捨てる

    for val in get_data:
        val = int(val * 10) # floatのデータを送信用4bitに変形
        modified_data.append(val)


    txdt = (current_time,) + tuple(modified_data)

#    txdt = (current_time, *tuple(modified_data))

    return txdt