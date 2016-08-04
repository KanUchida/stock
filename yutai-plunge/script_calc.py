# coding: utf-8

import csv
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


def save_format_data(input_path, output_path):
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
            [
            span,
            next,
            next
            ]
    '''

    spans = [5, 7, 10, 14, 20, 21, 25, 30, 40]

    for span in spans:
        fn1 = input_path + str(span) + '-before.csv'
        f1 = open(fn1, 'rU')
        reader = csv.reader(f1)

        for row in reader:
            ccode = row.pop(0)

            for nums in row:
                save_lst = []
                save_lst.append(span)

                lst = map(float, nums.split('|'))
                return_lst = calc_values(lst, span)
                save_lst.extend(return_lst)

                print save_lst
                fn2 = output_path + ccode + '.csv'
                f2 = open(fn2, 'a')
                writer = csv.writer(f2)
                writer.writerow(save_lst)
                f2.close()
        f1.close()


def calc_values(lst, span):
    '''
    役割
        優待前の日から最大値とそのインデックスを返す
    引数
        lst : valuesのリスト
        span : 優待前後の取得するスパン（片側で記入）
    戻り値
        [ max_right_before, index_max_right_before, bairitsu, ]
    '''
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
    return tmp_lst
