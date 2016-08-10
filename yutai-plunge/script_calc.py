# coding: utf-8

import csv
import pandas as pd
import numpy as np
import glob
"""
書きたいスクリプトたち

日経平均で基準化したやつ
    信用売りのケース™
        信用買い：翌日にしちゃう
        信用売り：優待日を含めた前５日で、「XX倍まであがるのか」と「その時のインデックス」を調べて保存。そのXXに接したところで売りを入れる

    現物買いのケース
        売り：信用売りのところで求めた、XXの部分
        買い：そのCSVファイルの起点から見ると、確実に一定倍になるXXが見つかったところのCSVファイル

    やること
        優待日前に[X-before]の５日前から、 を全て求める
"""


def save_format_data(input_path, output_path, cond, z_value=None, heikin_day=None, past_num=None, file=None):
    '''
        1   2   3     4    5     6    7   8    9    10    11   12   13   14   15   16   17  18   19   20  21 
        1.0|1.0|0.98|0.98|0.99|0.99|1.05|1.05|1.08|1.06|1.04|1.01|1.03|1.06|1.09|1.11|1.1|1.08|1.09|1.09|1.1

    保存される形
        ファイル名 : ccode.csv
        フォーマット : 
            [
            span,
            max_right_before|index_max_right_before|bairitsu, max_right_before|index_max_right_before|bairitsu, ...  
            ],
    '''
#     spans = [5, 7, 10, 14, 20, 21, 25, 30, 40]
    spans = [40]  # 今回は、一番長い移動平均のやつしかとらない

    for span in spans:
        f1 = open(input_path, 'rU')
        reader = csv.reader(f1)
        ccode = input_path[-8:-4]
        header = next(reader)

        if cond == 0:
            for row in reader:
                save_bairitsu(row, span, output_path, ccode)
        elif cond == 1:
            save_kairi(reader, span, output_path, ccode, z_value, heikin_day, past_num)
        else:
            assert u'一致する条件がありません'
        f1.close()


def save_bairitsu(row, span, output_path, ccode):
    '''
    役割
        優待前の日から最大値とそのインデックスを返す
    引数
        lst : valuesのリスト
        span : 優待前後の取得するスパン（片側で記入）
        output_path  : 保存先のパス
        ccode : ccode    
    戻り値
        [ max_right_before, index_max_right_before, bairitsu, ]
    '''
    for nums in row:
        save_lst = []
        save_lst.append(span)

        # リストから実際の分析に使う数値を出してあげる
        lst = map(float, nums.split('|'))
        before_yutai_days = lst[:span]  # get lst of half length of span
        before_yutai_days_half_reversed = lst[span / 2:span]
        before_yutai_days_half_reversed.reverse()

        yutai_day = lst[span]  # value on yutai date
        after_yutai_days = lst[-span:]  # value from days after yutai date

        max_right_before = max(before_yutai_days_half_reversed)
        tmp_index = before_yutai_days_half_reversed.index(max_right_before)
        index_max_right_before = span - tmp_index - 1

        # calc how much times the max values bigger than yutai_next_day
        bairitsu = round(max_right_before / after_yutai_days[0], 3)
        tmp_lst = [max_right_before, index_max_right_before, bairitsu]
        save_lst.extend(tmp_lst)
        print save_lst

        # 保存処理
        fn2 = output_path + ccode + '.csv'
        f2 = open(fn2, 'a')
        writer = csv.writer(f2)
        writer.writerow(save_lst)
        f2.close()


def save_kairi(reader, span, output_path, ccode, z_value, heikin_day, past_num):
    """
    引数
        reader : csv reader
        span : 優待前後の取得するスパン
        output_path : 出力先のパス
        ccode : ccode
        z_value : どれくらいの信頼区間を取るか
        year : 過去何個前までのデータの分散がとりたいか
    説明
        【75日平均, span40日】だけでいいので、求めた結果に該当する日にちがどれくらいあるのかを調べる。
        その値以上のものがどれくらいあるかを調べる。（正負分けて調べる。優待前と優待後でもそれぞれ求める）
    注意点
        負の値に注意。正負両方カウントする（絶対値？）
    保存する形
        [ccode, heikin_day, past_num, kairi_on_z_value, mean, std, b_over, a_over]
        説明
            past_num : 過去何回の優待付近のデータを使ったか
            kairi_on_z : Z%信頼点での値(90%なら1.645。正規分布を仮定してる)
            mean : 平均
            std : 標準偏差
            b_over : 優待前でkairi_on_z以上の日にちの個数
            a_over : 優待後でkairi_on_z以上の日にちの個数
    結果の評価
        いまいち
        乖離率は日によってばらつきが大きすぎて、正規分布を仮定したところで意味がない。
        グルーピングしてあげると少しはいい感じになるかも。。
    """

    # 75日平均、
    lst = []
    for row in reader:
        if row[0] == str(heikin_day) and row[1] == str(span):
            lst.append(map(float, row[2:]))

    for i in range(len(lst) - past_num):
        save_lst = [ccode, past_num, heikin_day]
        tmp_lst = []

        # 統計値求めるやつを１つにまとめるため
        for k in lst[i + 1:i + 1 + past_num]:
            tmp_lst.extend(map(float, k))

        data = np.array(tmp_lst)
        std = round(np.std(data), 2)
        mean = round(np.mean(data), 2)
        kairi_on_z = round(mean + std * z_value, 2)

        b_overs = filter(lambda x: abs(x) >= kairi_on_z, lst[i][:span])
        a_overs = filter(lambda x: abs(x) >= kairi_on_z, lst[i][span + 1:])

        num_b_over = len(b_overs)
        num_a_over = len(a_overs)

        save_lst.extend([kairi_on_z, mean, std, num_b_over, num_a_over])

        # 保存処理
        fn2 = output_path + 'kairi_result.csv'
        f2 = open(fn2, 'a')
        writer = csv.writer(f2)
        writer.writerow(save_lst)
        f2.close()
