# coding: utf-8

# 以下のリンクにまとめた内容で実装する
#      http://www.doryoku-1mm.tech/entry/2016/07/12/173430　
# 関数は以下のとおり（２つのクラスにしたほうがいいのかも）
#   - リターンインデックス（RI）をcsvファイルに保存する
#     - yutai_dates.csv から優待付きの日付情報をとってくる
#     - ””月末”” の情報を返してくれるやつ
#     - 月末の情報を元に、その前後30日分を取得する
#　　　- 取得した前後30日をRIの形に変える
#　　　- それをcsvファイルに保存
#       　-- ccode 優待日付 買うべき日 売るべき日　60日後RI 59日後RI , ... , X day, ... , 59日前RI, 60日前RI
#   - 「リターンの期待値・リターンの分散・買う日の分散・売る日の分散」を保存。各会社毎にもとめる
#     - リターンの期待値
#     - リターンの分散
#     - 買う日の分散
#     - 売る日の分散
#     - これらを保存する

import csv
years = [2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016]


# 完璧
# 優待日を yutai_dates.csv に保存する
def end_month_date():
    f1 = open('./yutai_info.csv', 'rU')
    f2 = open('./all_prices.csv', 'rU')
    f3 = open('./yutai_dates.csv', 'a')

    yutai_info = csv.reader(f1)
    next(yutai_info) # header を取り除く。

    all_prices = csv.reader(f2) # 市場が開いている日をここに保存する。
    open_days = next(all_prices)  #市場が開いてる日をopen_daysにいれる。
    f2.close # 不要だから閉じておく。

    c = csv.writer(f3)
    for yutai in yutai_info:
        months = map(int,yutai[4].split('|'))
        data_to_save_yutai_dates = []
        data_to_save_yutai_dates.append(yutai[0]) #ccodeをまずは保存
        # yearを順番に見る
        for year in years:
            # monthを取る
            for month in months:
                # open_days は１行のcsvファイルにしておく
                # 一個ずつとってチェックする
                # 優待月末（降順に日付がはいってるから、１個目が月末のはずだから）
                condition = ''
                if month in range(1,10):
                    condition = str(year)+'-0'+str(month)
                elif month in range(10,13):
                    condition = str(year)+'-'+str(month)
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

# 書き方が間違ってる。
# save_bairitsu と get_yutai_row で似たような処理があるのか、思ってるように呼び出されないよ
# 株主優待の日周辺の60日のデータを変化率にしてcsvファイルに保存
def save_before_and_after_30days():
    # 全ての市場のデータの取得
    all_prices = csv.reader(open('./all_prices.csv', 'rU'))
    market_open_days = next(all_prices)

    # 優待情報の取得ccodeを取らなきゃいけないから。。
    yutai_dates = csv.reader(open('./yutai_dates.csv', 'rU'))

    # この for で１つの証券番号を回す
    for yutai_date in yutai_dates:
        ccode = yutai_date.pop(0)
        price_around_yutai_day_lst = [ccode]
        row = get_yutai_row(ccode)
        price_around_yutai_day = ''
        print ccode
        save_bairitsu(row)

    return 'done'

# save_before_and_after_30days で
#優待のある銘柄が記載されている列を返す
def get_yutai_row(ccode):
    #該当行を取得するやつ
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

# save_before_and_after_30days で必要
# 数字のリストをheader情報を元に
def save_bairitsu(lst):
    f1 = open('./all_prices.csv', 'rU')
    all_prices = csv.reader(f1)
    header = next(all_prices)
    header.pop(0)
    f1.close()

    f2 = open('./yutai_dates.csv', 'rU')
    yutai_dates = csv.reader(f2)

    f3 = open('./test.csv', 'w')
#    f3 = open('./normed_yutai_values.csv', 'w')
    c = csv.writer(f3)

    for date in yutai_dates:
        ccode = date.pop(0)

        for d in date:
            norm = []
            norm_str = ''
            save_lst = [ccode]
            bairitsu = ''
            normed_value = []
            normed_nikkei = []
            date_index_all_prices = header.index(d)
#            try:
            if 30 < date_index_all_prices <= len(lst)-31:
                values_lst = map(int,lst[date_index_all_prices-30:date_index_all_prices+31])
                normed_value = [ round(1.0 + float(i-values_lst[30])/float(values_lst[30]),2) for i in values_lst ]
                normed_nikkei = get_nikkei_heikin_bairitsu(date_index_all_prices)
                norm = [round(float(x) / float(y),2) for (x,y) in zip(normed_value, normed_nikkei) ]# value / nikkei をそれぞれ割ったもの
                norm_str = map(str,norm)
                bairitsu = '|'.join(norm_str)
                save_lst.append(bairitsu)
                c.writerow(save_lst)
            else:
                print 'miss'
#                pass
#            except:
#                pass

def get_nikkei_heikin_bairitsu(date_index_all_prices):
    try:
        nikkei_heikin_row = get_yutai_row(1330)
        ccode = nikkei_heikin_row.pop(0)
        around_nikkei = map(int,nikkei_heikin_row[date_index_all_prices-30:date_index_all_prices+31])
        normed_nikkei = [ round(1.0 + float(i-around_nikkei[30])/float(around_nikkei[30]),2) for i in around_nikkei ]
    except:
        pass
    return normed_nikkei

def get_bigget_gap(self):

    return u'X day 前後で差が一番開いてる日にちを取得してリストで返す'

def expected_value(self):
    return u'期待値を返す'

def volatility(self):
    return u'ボラティリティ' 

def buy_date_volatility(self):
    return u'買う日の分散を返す'

def sell_date_volatility(self):
    return u'売る日の分散を返す'

def save_to_csv(self):
    return u'保存する'
