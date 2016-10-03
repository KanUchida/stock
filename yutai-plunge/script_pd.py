# coding: utf-8

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import glob
import csv
plt.style.use('ggplot')

"""
気になること（IMnewsで掲載する）
    移動平均の日数毎に分布を書いて、良い周期毎の違いをみてあげる
    移動平均の期間を過ぎた場合は、売買を終わらせる。（３日移動平均なら、市場インから３日を過ぎたら、利確）パフォーマンスの違いを見る
    INの時にsellとbuyのどっちが多いのか
"""


def plot_each(ccode, span=None):
    """
        指定した銘柄の全体をプロット
        同時に95%棄却域・50%内側 などもプロットする
    引数
        ccode: 分析したいccode
        span: 状況をみたいとしを指定する(特定)

    """

    # 6379の2008年でfeatureしてやる
    df_prices = pd.read_csv('./prices/' + str(ccode) + '.csv', names=['date', 'start', 'high', 'low', 'end', 'volume', 'adj_end'])
    df_prices['date'] = pd.to_datetime(df_prices['date'])
    df_prices['kairi'] = 100 * (df_prices['adj_end'] - df_prices['adj_end'].rolling(window=7).mean()) / df_prices['adj_end'].rolling(window=7).mean()
    df_prices['outline'] = 1.96 * df_prices['kairi'].std() + df_prices['kairi'].mean()  # 95%信頼区間の値
    df_prices['inline'] = 0.67 * df_prices['kairi'].std() + df_prices['kairi'].mean()
    df_prices['negative_outline'] = -1 * 1.96 * df_prices['kairi'].std() + df_prices['kairi'].mean()
    df_prices['negative_inline'] = -1 * 0.67 * df_prices['kairi'].std() + df_prices['kairi'].mean()

    # 限定
    if span:
        df_prices = df_prices[df_prices['date'].dt.year == span]
    df_prices = df_prices.set_index('date')
    df_prices = df_prices[::-1]

    df_prices['adj_end'].plot(label='prices', color='b')
    plt.title(ccode + ' Prices Movement')
    plt.show()

    # 必要な行だけ取り出す
    df_prices = df_prices[['kairi', 'outline', 'negative_outline', 'inline', 'negative_inline']]


    print df_prices.head()
    # prices/ccode.csv の情報をプロットする
    ax = df_prices['kairi'].plot(label=u'kairiRate', color='blue')
    df_prices[['outline', 'negative_outline']].plot(label='95%_line', color='red', ax=ax)
    df_prices[['inline', 'negative_inline']].plot(label=u'50%_line', color='green', ax=ax)


    # plot
    plt.title(str(ccode) + '\'s Kairi Rate Movement')
    plt.xlabel('Date')
    plt.ylabel('Kairi Rate')
    plt.show()





def plot_rimawari_yearly(path):
    df = pd.read_csv(path)

    # 日付データがstring だからそれをタイムスタンプに変える
    df['in_date'] = pd.to_datetime(df['in_date'])
    df['out_date'] = pd.to_datetime(df['out_date'])

    # それをout_dateを用いてyearだけでgroupbyする（新しいdfを作成する）

    df_rimawari_yearly = df.copy()
    df_rimawari_yearly = df_rimawari_yearly.groupby([df_rimawari_yearly['out_date'].dt.year]).sum()

    # 最後のカラムにその年までのmaxを入れてあげる（利回りの分母になるやつ）
    data = {}
    for i in df_rimawari_yearly.index:
        data[i] = df['in_price'][df['out_date'].dt.year <= i].max()
    data = pd.Series(data=data)
    df_rimawari_yearly['max_for_rimawari'] = data

    # それらのデータを使って年間の利回りを計算してreturn
    df_rimawari_yearly['rimawari'] = df_rimawari_yearly['profit'] / df_rimawari_yearly['max_for_rimawari'] * 100
    return df_rimawari_yearly['rimawari']


def plot_yahoolike(path):
    """図をかく"""
    ccode = path[-8:-4]

    # PATHたちの定義
    PATH_TRADEHISTORY = './' + ccode + '_tradeHistory.csv'
    col_tradehistory = ['heikin_day', 'in_date', 'in_order', 'in_price', 'out_date', 'out_order' , 'out_price', 'profit']

    heikin_day = 7
    # カラム名たちの定義
    kairi = str(heikin_day)
    outline = kairi + '_1.96*std'
    inline = kairi + '_0.67*std'
    negative_outline = '-' + kairi + '_1.96*std'
    negative_inline = '-' + kairi + '_0.67*std'

    # 株価データを取得
    df = get_df(path)
    df[kairi] = 100 * (df['adj_end'] - df['adj_end'].rolling(window=heikin_day).mean()) / df['adj_end'].rolling(window=heikin_day).mean()  # 乖離率計算
    df[outline] = 1.96 * df[kairi].std()  # 95%信頼区間の値
    df[inline] = 0.67 * df[kairi].std()
    df[negative_outline] = -1 * 1.96 * df[kairi].std()
    df[negative_inline] = -1 * 0.67 * df[kairi].std()
    # 取引履歴を取得
    # trade_df = pd.read_csv(PATH_TRADEHISTORY, names=col_tradehistory)

    # プロットの用意
    ax = df[kairi].plot(legend=True, color='blue', title=ccode)
    df[[outline, negative_outline]].plot(legend=True, color='red', ax=ax)
    df[[inline, negative_inline]].plot(legend=True, color='green', ax=ax)
    plt.show()


def save_trade_history(ccode, heikin_days=[7]):
    """プロットするやつ"""
    
    PATH_PRICES = './prices/' + ccode + '.csv'  # inputデータのパス
    PATH_SAVE = './tradeHistory/' + ccode + '_tradeHistory.csv'  # output先のパス

    # 取引履歴の用意
    df = get_df(PATH_PRICES)
    df_trade_history = get_trade_history(df, heikin_days)

    # 保存処理
    df_trade_history.to_csv(PATH_SAVE, index=False)


def get_df(path):
    """
    全体で使っている形のdfを返す
    """
    df = pd.read_csv(path, index_col=0, names=prices_col)
    df.index = pd.to_datetime(df.index)
    df = df.iloc[::-1]
    return df


def cal_rimawari(trade_df, span='year'):
    """
    trade履歴から、年間の利回りを計算する関数
    利回りを出すやつ
    
    引数
        span = year
        span = total
    未だわからないところ
        日時の操作の部分
            http://sinhrks.hatenablog.com/entry/2014/10/30/233606　こいつが優秀
    """

    # 年間の利益をここで求めて挙げられる
    tmp_df = trade_df.copy()
    if span == 'year':
        tmp_df.index = pd.to_datetime(tmp_df['out_date']).dt.year
        bumbo = tmp_df.groupby(tmp_df.index, sort=False)['in_price'].max()  # 利回りの分母取得のためにインデックスでグルーピングしてin_priceのマックス取得
        tmp_df = tmp_df.groupby(tmp_df.index).sum()  # 年ごとに利益の話を求めるためのグルーピング
        tmp_df['rimawari'] = tmp_df['profit'] / bumbo  # 利回りの計算
    elif span == 'total':
        bumbo = tmp_df['in_price'].max()
        tmp_df['rimawari'] = tmp_df['profit'].sum() / bumbo
    else:
        raise 'the span is not supported'
 
    return tmp_df


def cal_rimawari_nikkei():
    """
    日経平均ETF(1330)を長期保有した場合のETFと比較するための
    1330の利回りを計算するやつ
    """
    PATH_NIKKEI = './prices/1330.csv'
    df_nikkei = pd.read_csv(PATH_NIKKEI, names=['date', 'start', 'high', 'low', 'end', 'volume', 'adj_end'])
    df_nikkei.index = pd.to_datetime(df_nikkei.date).dt.year  # インデックスを年に帰る(やるべきではない操作のはsず)
    years = df_nikkei.index.unique()  # for文回すためのシーケンス用意

    df_nikkei['rimawari'] = 1.0  # float のcolumnを定義するために一旦1.0を代入
    for year in years:
        start_price_yearly = df_nikkei[df_nikkei.index == year].iloc[0, 1]
        end_price_yearly =  df_nikkei[df_nikkei.index == year].iloc[-1, 4]
        rimawari = float(start_price_yearly - end_price_yearly) / start_price_yearly
        df_nikkei['rimawari'][df_nikkei.index == year] = rimawari
    return df_nikkei


def cal_profit(df, kairi, outlier, inner, col, heikin_day):
    """
    １との違い
        heikin_days 以上同じ領域に入っていたら逆注文を入れるスクリプトを書く
    理由
        購入した時の情報の入っていない移動平均を使っても、なんとなく効果がなさそう
    役割
        儲けの期待値を計算する関数
        outlier が True の時に買う
        そのあとに inner が True になったら利確する のコードを書く
        株を保有している状態を知らせるために ' state ' を用意してそこに前回の注文の状況を保存しておいてあげる
        flagは次に取引を行うのが利益確定のためかを表している（1なら次が利確）
    """
    df_result = pd.DataFrame(columns=col)
    # row = {}
    row = [heikin_day]
    flag = 0
    order = ''
    count = 0
    last_order = 'nothing'  # 始めは一個前などないのでnothing
    for i in range(len(df)):
        # 株を売買するところのロジック
        if flag == 0 and order == '':
            # 株購入の際のロジック
            if df.iloc[i][outlier] and df.iloc[i][kairi] > 0:
                # 移動平均乖離率プラスで95%
                row.append(df.index[i].strftime('%Y-%m-%d'))
                row.append('sell')
                row.append(df.iloc[i, 5])
                order = last_order = 'sell'
                flag = 1
                count = 0
            elif df.iloc[i][outlier] and df.iloc[i][kairi] < 0:
                # 移動平均乖離率マイナスで95%
                row.append(df.index[i].strftime('%Y-%m-%d'))
                row.append('buy')
                row.append(-1 * df.iloc[i, 5])
                order = last_order = 'buy'
                flag = 1
                count = 0
        elif flag == 1 and count < heikin_day:
            # 欲しい範囲に入ったから利益確定
            if df.iloc[i][inner] and order == 'sell':
                # 売りから入った時
                row.append(df.index[i].strftime('%Y-%m-%d'))
                row.append('buy')
                row.append(-1 * df.iloc[i, 5])
                row.append(row[3] + row[6])  # 損益の計算
                df_result.loc[i] = row
                order = ''
                flag = 0
                count = 0
                row = [heikin_day]
            elif df.iloc[i][inner] and order == 'buy':
                # 買いから入った時
                row.append(df.index[i].strftime('%Y-%m-%d'))
                row.append('sell')
                row.append(df.iloc[i, 5])
                row.append(row[3] + row[6])  # 損益の計算
                df_result.loc[i] = row
                order = ''
                flag = 0
                count = 0
                row = [heikin_day]
        elif count >= heikin_day:
            if order == 'sell':
                row.append(df.index[i].strftime('%Y-%m-%d'))
                row.append('buy')
                row.append(-1 * df.iloc[i, 5])
                row.append(row[3] + row[6])  # 損益の計算
                df_result.loc[i] = row
                order = last_order = ''
                flag = 0
                count = 0
                row = [heikin_day]
            elif order == 'buy':
                row.append(df.index[i].strftime('%Y-%m-%d'))
                row.append('sell')
                row.append(df.iloc[i, 5])
                row.append(row[3] + row[6])  # 損益の計算
                df_result.loc[i] = row
                order = last_order = ''
                flag = 0
                count = 0
                row = [heikin_day]
        # last_orderから変可能ない日数を計測
        if order != '' and order == last_order:
            count += 1
    return df_result


def get_trade_history(df, heikin_days):
    """
    売買タイミングを管理して、トレード一覧を返してくれるやつ
    引数
        df : prices 以下にあるやつをそのまま投げればよろしい
        heikin_days : 何日平均のものを出したいか（5,15,20 日平均が欲しいなら以下 [5, 15, 20]）
    """
    # 取引履歴とかを保存するやつ
    col = ['heikin_day', 'in_date', 'in_order', 'in_price', 'out_date', 'out_order', 'out_price', 'profit']
    return_df = pd.DataFrame(columns=col)

    # 移動平均乖離率の追加
    for heikin_day in heikin_days:
        # カラム名たちの定義
        kairi = str(heikin_day)
        outline = kairi + '_1.96*std'
        outlier = kairi + '_outlier'
        inner = kairi + '_inner50'

        # 取引タイミング決定のためのカラムの作成
        df[kairi] = 100 * (df['adj_end'] - df['adj_end'].rolling(window=heikin_day).mean()) / df['adj_end'].rolling(window=heikin_day).mean()  # 乖離率計算
        df[outline] = 1.96 * df[kairi].std()  # 95%信頼区間の値
        df[outlier] = abs(df[kairi] - df[kairi].mean()) > 1.96 * df[kairi].std()  # 外側かどうか
        df[inner] = abs(df[kairi] - df[kairi].mean()) < 0.67 * df[kairi].std()  # 50% 範囲内に入るかどうか

        # return_dfにしまう作業
        tmp_df = cal_profit(df, kairi, outlier, inner, col, heikin_day)  # 正確には、ここで取引履歴を計算している
        return_df = pd.concat([return_df, tmp_df])
    return return_df


def save_all_rank(heikin_days):
    """
    すべての銘柄を分析して、通算の利回りを計算する
    その通算の利回りでランク付けをして、トータルで利回りのいい銘柄を探す関数
    """
    # すべての銘柄でトータル利回りを算出
    # それを１つのranking_dfかなんかに入れ込んで、１つのdfとしてreturnする
    paths = glob.glob('./prices/*')

    for i, path in enumerate(paths):
        # df, 保存用の変数たちの用意
        ccode = path[-8:-4]
        tmp_df = get_df(path)
        tmp_trade_df = get_trade_history(tmp_df, heikin_days)  # profitとかはここに入っている
        tmp = cal_rimawari(tmp_trade_df, span='total')
        total_profit = tmp_trade_df['profit'].sum()
        volume_mean = tmp_df['volume'].mean()
        volume_std = tmp_df['volume'].std()

        # 保存用のリストの用意 [ccode, rimawari, trade_num, trade_num_year_ave, in_date, in_price, out_date, out_price, kairi_profit, volume_mean, volume_std]
        try:
            lst = [ccode]
            lst.append(tmp.rimawari.iloc[0])
            lst.append(len(tmp_trade_df))
            lst.append(tmp_trade_df.in_date.iloc[0])
            lst.append(tmp_trade_df.in_price.iloc[0])
            lst.append(tmp_trade_df.out_date.iloc[-1])
            lst.append(tmp_trade_df.out_price.iloc[-1])
            lst.append(total_profit)
            lst.append(volume_mean)
            lst.append(volume_std)

            with open('./rimawari.csv', 'a') as f:
                writer = csv.writer(f, lineterminator='\n')
                writer.writerow(lst)
            print lst[0]
        except IndexError:
            print lst[0], 'has strange format'


def save_conditioned_rimawari():
    df = pd.read_csv('./rimawari.csv')

    # convert string to datetime
    df['out_date'] = pd.to_datetime(df['out_date'])
    df['in_date'] = pd.to_datetime(df['in_date'])

    # add trade_num_ave
    df['trade_num_ave'] = df['trade_num'] / (df['out_date'].dt.year - df['in_date'].dt.year + 1)
    df['trade_num_ave'][(df['out_date'].dt.year - df['in_date'].dt.year) == 0] = df['trade_num'][(df['out_date'].dt.year - df['in_date'].dt.year) == 0]

    # save conditioned rimawari
    df = df[df['volume_mean'] >= 100000]  # 出来高の平均が10万以上
    df = df[df['trade_num_ave'] >= 6]

    df.to_csv('rimawari_conditioned.csv', index=False)
    print df
    print 'done funciton save_conditioned_rimawari'


PATH = './prices/1330.csv'
prices_col = ['date', 'start', 'high', 'low', 'end', 'volume', 'adj_end']

# csvファイルを古い順に読み込む
df = pd.read_csv(PATH, index_col=0, names=['date', 'start', 'high', 'low', 'end', 'volume', 'adj_end'])
df.index = pd.to_datetime(df.index)
df = df.iloc[::-1]  # 上下反転させる

# 取引履歴をゲットしてあげる
heikin_days = [7]
# trade_df = get_trade_history(df, heikin_days)

# 年間利回りがこれで出てくる
# rimawari_df = cal_rimawari(trade_df)

# 日経平均インデックスの利回りを計算できる
# nikkei_df = cal_rimawari_nikkei()

# 手数料計算に使うために、取引回数を求めておく
# trade_num = len(trade_df)

# 銘柄毎にトータルの利回りをランキングしたもの
# save_all_rank(heikin_days)

# 利回りの高い銘柄の取引履歴の保存
"""ccodes = ['1807', '6862', '8025', '1352', '1850', '6379']
for ccode in ccodes:
    save_trade_history(ccode)
"""

"""for ccode in ccodes:
    path = './prices/' + ccode + '.csv'
    plot_yahoolike(path)
plt.show()

#　利回りランキングの高い物の年間利回りを図示する

paths = glob.glob('./tradeHistory/*')
rimawari_df = pd.DataFrame()
for path in paths:
    rimawari_df[path[-21:-17]] = plot_rimawari_yearly(path)

font = {'family' : 'IPAPGothic'}
matplotlib.rc('font', **font)

# プロットの用意
ax = rimawari_df[paths[0][-21:-17]].plot(label=u'ccode:1807', color='blue')
rimawari_df[paths[1][-21:-17]].plot(label=u'ccode:6862', color='red', ax=ax)
rimawari_df[paths[2][-21:-17]].plot(label=u'ccode:8025', color='green', ax=ax)
rimawari_df[paths[3][-21:-17]].plot(label=u'ccode:1352', color='black', ax=ax)
rimawari_df[paths[4][-21:-17]].plot(label=u'ccode:1850', color='magenta', ax=ax)

plt.xlabel('Year')
plt.ylabel('Yield')
plt.legend()
plt.title('Yield top 5')
plt.show()

# 利回りランキングの高いものの年間利回りを図示する部分
"""

# 条件づけた利回りの保存
# save_conditioned_rimawari()

# 指定した銘柄のプロットをする
ccodes = ['1807', '6862', '8025', '1352', '1850']
for ccode in ccodes:
    plot_each(ccode)





# _______________以下、分析用の思考錯誤___________________

# 同じ日経平均を、乖離率に従って売ったり買ったりした時と、buy & hold した時の違い
# 利回りで比較 -> あまりわからない
# 分散は確実に
# print rimawari['rimawari'].unique()
# print 
# print nikkei_rimawari['rimawari'].unique()

# 利益の絶対値で比較
# 同じ銘柄同士で比較するならばこれで問題ない
# 1330でやったら圧倒的に優秀な結果になった
# print 'trade_num', trade_num
# print rimawari_df['profit'].sum()
# print rimawari_df['profit'].sum() * 100 - trade_num * 500
# print 
# print 100 * (df.iloc[-1, 3] - df.iloc[0, 0])