# coding: utf-8

import csv


def save_bairitsu(span, path, cond, heikin_day=None):
    # 関数説明
    #   基準化した値を、fileに保存する
    # 引数について
    #   span : 優待日を基準にした、分析するスパン
    #   file : 保存するfile名を教えてあげる
    #   cond : 何を条件に取得するかの条件。
    #       0 -> 日経平均の変化率で基準化された値
    #       1 -> 乖離率。中心が優待日
    f1 = open('./all_prices.csv', 'rU')
    all_prices = csv.reader(f1)
    dates_all_prices = next(all_prices)
    dates_all_prices.pop(0)
    f1.close()

    f2 = open('./yutai_dates.csv', 'rU')
    yutai_dates = csv.reader(f2)

    f3 = open(path, 'w')
    c = csv.writer(f3)

    for dates in yutai_dates:
        ccode = dates.pop(0)
        save_lst = [ccode]

        for date in dates:
            index_of_yutai_day = dates_all_prices.index(date)
            lst = get_yutai_row(ccode)
            if 30 < index_of_yutai_day <= len(lst) - 31:
                norm = []
                if cond == 0:
                    norm = get_values_normed_by_nikkei_change_rate(span,  index_of_yutai_day, lst)
                elif cond == 1:
                    norm = get_kairi_rate(heikin_day, span, index_of_yutai_day, lst)
                else:
                    assert u'該当する条件はまだ存在しません！'
                # 保存用の文字列に
                norm_str = map(str, norm)
                bairitsu = '|'.join(norm_str)
                save_lst.append(bairitsu)
            else:
                pass
        c.writerow(save_lst)
        print 'done' + str(ccode)
    f3.close()
    print 'done' + str(span)


def get_yutai_row(ccode):
    # 優待のある銘柄が記載されている列を返す
    # 該当行を取得するやつ
    reader = csv.reader(open('./all_prices.csv', 'rU'))
    row = []
    for r in reader:
        code = str(ccode)
        if code == r[0]:
            row = r[1:]
            break
        else:
            pass
    return row

# get_normed_value() , get_normed_nikkei_heikin を呼び出して、変化率で基準化してリストを返す
def get_values_normed_by_nikkei_change_rate(span, index_of_yutai_day, lst):
    normed_value = get_normed_value(span, index_of_yutai_day, lst)
    normed_nikkei = get_normed_nikkei_heikin(span, index_of_yutai_day)
    tmp_lst = [round(float(x) / float(y), 2) for (x, y) in zip(normed_value, normed_nikkei)]
    return tmp_lst

# values_lst : values_lstを投げる
def get_normed_value(span, index_of_yutai_day, lst):
    lst = map(float, lst[index_of_yutai_day - span:index_of_yutai_day + span + 1])#必要な期間だけのリストを切り取る
#    print span
    values_normed_by_sp = [round(1.0 + float(i - lst[0]) / float(lst[0]), 2) for i in lst] # 基準化
    return values_normed_by_sp


def get_normed_nikkei_heikin(span, index_of_yutai_day):
    nikkei_heikin_row = get_yutai_row(1330)
    nikkei_heikin_row = nikkei_heikin_row[1:] # 先頭のccodeを削除する
    nikkei_around_yutai = map(float, nikkei_heikin_row[index_of_yutai_day - span:index_of_yutai_day + span + 1]) #必要な期間の日経平均
    nikkei_normed_by_sp = [round(1.0 + float(i - nikkei_around_yutai[0]) / float(nikkei_around_yutai[0]), 2) for i in nikkei_around_yutai] # spanで基準化
    return nikkei_normed_by_sp


def get_kairi_rate(heikin_day, span, index_of_yutai_day, lst):
    # 優待日を中心にspan分の、X日移動平均乖離率を求めてリストに入れるやつ
    # heikin_day : X日移動平均のXの部分
    # index_of_yutai_day : 優待の日のindex
    # lst : all_pricesから取得した注目銘柄の行
    start = index_of_yutai_day - span - heikin_day
    end = index_of_yutai_day + span + 1
    tmp_lst = map(float, lst[start:end])
    idou_heikin = [round(sum(tmp_lst[i:i + heikin_day]) / heikin_day, 2) for i in range(span * 2 + 1)]
    values = tmp_lst[heikin_day:]
    kairi_rates = [round((x - y) / y * 100, 2) for (x, y) in zip(values, idou_heikin)]
    return kairi_rates


def end_month_date():
    # 独立してるやつ
    # 優待日を yutai_dates.csv に保存する
    # f1から割当基準月をゲット
    # f2から割当基準日に該当する年月日を全てゲット
    # f3に全て保存しておく
    f1 = open('./yutai_info.csv', 'rU')
    f2 = open('./all_prices.csv', 'rU')
    f3 = open('./yutai_dates.csv', 'a')
    years = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016]

    yutai_info = csv.reader(f1)
    next(yutai_info) # header を取り除く。

    all_prices = csv.reader(f2) # 市場が開いている日をここに保存する。
    open_days = next(all_prices)  # 市場が開いてる日をopen_daysにいれる。
    f2.close # 不要だから閉じておく。

    c = csv.writer(f3)
    for yutai in yutai_info:
        months = map(int, yutai[4].split('|'))
        data_to_save_yutai_dates = []
        data_to_save_yutai_dates.append(yutai[0])  # ccodeをまずは保存
        # yearを順番に見る
        for year in years:
            # monthを取る
            for month in months:
                # open_days は１行のcsvファイルにしておく
                # 一個ずつとってチェックする
                # 優待月末（降順に日付がはいってるから、１個目が月末のはずだから）
                condition = ''
                if month in range(1, 10):
                    condition = str(year) + '-0' + str(month)
                elif month in range(10, 13):
                    condition = str(year) + '-' + str(month)
                print condition
                for open_day in open_days:
                    if condition in open_day:
                        data_to_save_yutai_dates.append(open_day)
                        print 'successfully through condition'
                        break
                    else:
                        pass
        print data_to_save_yutai_dates
        c.writerow(data_to_save_yutai_dates)
    f2.close()
    f3.close()
