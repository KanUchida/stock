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


def save_format_data(input_path, output_path, cond, z_value=None, heikin_day=None, past_num=None):
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


        # ここで一緒にインデックスもとってきて、保存する。
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


def save_return_kairi(input_path, output_path, span, heikin_days):
    """
    用途
        kairi_result.csv のデータを元にして、得られる額のリターンを求める。
    取得するべき値
        1 Z値を超えた日のインデックスをとる。 (index_yutai_day - 40(span) + index_tmp(超えた日のindex) )
        2 乖離率の符号が変わった日のインデックス 
        3 乖離率がmean から 「標準偏差のY倍」　の範囲に入った日のインデックス ( 優待前と後で分けてとる )
        4 3を満たすインデックスは１つでも取得できれば、その時点で次の処理へ進む
    計算するもの
        4 取得したインデックスを用いて、終値の値を取得。
        5 その終値の値から、得られる額の期待値を求める。
        6 その期待値は、kairi_result.csv に新しいレコードとして保存する
    """
    ccode = int(input_path[-8:-4])
    ccode = 2001
    # ある銘柄に対して、[ index_a, index_b, index_c, ...]
    indexes_yutai_day = get_yutai_index(ccode)

    lst = get_indexes_over_z(ccode, span, heikin_days, input_path)

    # これで、全体の中でのインデックスの位置がわかる
#     indexes_over_z = indexes_yutai_day - span + indexes_tmp

    #  indexes_over_z を使って、prices/ccode.csv から実際の値を取得して取引。


def get_indexes_over_z(ccode, span, heikin_days, input_path):
    """
        kairi_result.csv から、zの値をとってきて、
        KairiNormed/* の該当ファイルから、該当区間でそのZ値よりも大きい日のインデックス取得
        save_return_kairi の 3番 を計算して取得
    戻り値
        [
            # indexes_yutai_dayのaに対する、売る日t買う日のリスト
            # ここがsub_lst
            [
                [売る日, 買う日]   # こいつらはtmp_lstで
                [売る日, 買う日]
            ]
            # indexes_yutai_day の bに対する、、
            [
                [売る日, 買う日]
                [売る日, 買う日]
            ]
        ]

    これをpandasで書き直す
    """

    # 結果データを用意
    tmp_df_result = pd.read_csv('./KairiNormedFormated/kairi_result.csv')
    df_result = tmp_df_result[(tmp_df_result['ccode'] == ccode) & (tmp_df_result['heikin_day'].isin(heikin_days))]

    # これでdf_result と heikin_day が等しいものを行数の揃ったDataFrameになる
    tmp_df_kairi = pd.read_csv(input_path)
    df_kairi = tmp_df_kairi[(tmp_df_kairi['heikin_days'].isin(heikin_days)) & (tmp_df_kairi['span'] == 40)]

    # all_prices からデータを取得
    df_all = pd.read_csv('./prices/' + str(ccode) + '.csv', header=None)

#    past_nums = [5,6,7,8]
#    for heikin_day in heikin_days:
#        for past_num in past_nums:
            # df_kairiの該当箇所を取得して、そのインデックスを０スタートに直す

    past_num = 5
    heikin_day = 50

    tmp_len = len(df_result[(df_result['heikin_day'] == heikin_day) & (df_result['past_num'] == past_num)])
    df_kairi = df_kairi[df_kairi['heikin_days'] == heikin_day].iloc[:tmp_len, :]
    df_kairi.index = range(len(df_kairi))

    # df_result とdf_kairi の行数を揃え、そのインデックスを０スタートに直す
    df_result_needed = df_result[(df_result['heikin_day'] == 50) & (df_result['past_num'] == 8)][:len(df_kairi)]
    df_result_needed.index = range(len(df_result_needed))

    # df_kairiを絶対値に直して、計算しやすくしてる
    # これをやらなければ、if文で場合分けする必要がある
    # 場合分けしてあげたほうが、そのあとも使えるからいいかも
    df_kairi_over_z = df_kairi.sub(df_result_needed['kairi_on_z_value'], axis=0)
    df_kairi_over_z[df_kairi_over_z > 0] = 1

    tmp_df_kairi_rikaku = df_kairi.sub(df_result_needed['mean'], axis=0)
    df_kairi_rikaku = abs(tmp_df_kairi_rikaku)
    df_kairi_rikaku[df_kairi_rikaku.sub(df_result_needed['mean'] * 2 / 3, axis=0) <= 0] = 2

    tmp_df_trade = df_kairi_over_z.where(df_kairi_over_z == 1.00, df_kairi_rikaku)
    df_trade = tmp_df_trade.where((tmp_df_trade == 2.00) | (tmp_df_trade == 1.00), 0).iloc[:, 2:]
    for i in range(df_trade.shape[0]):
        try:
            for j in range(df_trade.shape[1]):
                cond = df_trade.iloc[i, j]
                cond_next = df_trade.iloc[i, j + 1]
                k = 1
                while cond == cond_next:
                    df_trade.iloc[i, j + k] = 0.0
                    k += 1
                    cond = df_trade.iloc[i, j + k]
        except IndexError:
            pass

    # 取引スタートのタイミング 1
    # 利確のタイミング 2
    # それ以外0の要素は0の行列(df_trade)の取得に成功！
    print df_trade

    # df_kairi_25_5 みたいなのをコピーして、それでZ以上なものを取得
    # これで、乖離率がZ以上のものを取得できる
    # と思ったら、全部Noneになっちゃう。なんで
    # インデックスが揃っているものでしか計算しない設計になっている。
    df_kairi_50_8.iloc[:, 2:][abs(df_kairi_50_8) > df_result['kairi_on_z_value'][(df_result['heikin_day'] == 50) & (df_result['past_num'] == 8)]]

#    print obj = Series([])
#    print df_kairi_50_8
    b =  df_result['kairi_on_z_value'][(df_result['heikin_day'] == 50) & (df_result['past_num'] == 8)][:len(df_kairi_50_8)]
    b.index = range(len(df_kairi_50_8))
#    print b

    c = abs(df_kairi_50_8)
    # これは動く
    # 比較相手がSeriesだと動かない
    # 多分、行方向のインデックスがあっないから
    df_kairi_50_8.index = range(len(df_kairi_50_8))
    d = c.sub(b, axis=0)

    # これで乖離値がZの値より大きいものがとれる
    print d[d > 0]


    return return_lst


def get_sell_index(row, x, k, mean, z):
    return_i = None
    if x < 0:
        for i, v in enumerate(row[k + 1:]):
            if float(v) >= mean:
                return_i = i
                break
            else:
                pass
    else:
        for i, v  in enumerate(row[k + 1:]):
            if float(v) <= mean:
                return_i = i
                break
            else:
                pass
    return return_i


def get_yutai_index(ccode):
    """
    株主優待の日のindexをリストで返すやつ。
    """
    f1 = open('./all_prices.csv', 'rU')
    all_prices = csv.reader(f1)
    dates_all_prices = next(all_prices)
    dates_all_prices.pop(0)
    f1.close()

    f2 = open('./yutai_dates.csv', 'rU')
    yutai_dates = csv.reader(f2)

    return_lst = []

    for dates in yutai_dates:
        row_ccode = dates.pop(0)
        ccode = str(ccode)
        if ccode == row_ccode:
            for date in dates:
                # 1 の作業中
                index_yutai_day = dates_all_prices.index(date)
                return_lst.append(index_yutai_day)
    # 優待日のindexがベストな順番で帰ってくる。
    return return_lst
