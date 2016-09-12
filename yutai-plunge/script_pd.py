# coding: utf8

import pandas as pd
import glob

"""
現状できること
    取引履歴の取得・を取ることが可能

次に何をするか
    その日数を使って分析して、年間の利回りを銘柄毎に求める（groupby使えば多分余裕）
        インデックスに階層をつけてmonth / year 毎の利回りを１つのDataFrameに入れてあげるのが理想

気になること（IMnewsで掲載する）
    移動平均の日数毎に分布を書いて、良い周期毎の違いをみてあげる
    移動平均の期間を過ぎた場合は、売買を終わらせる。（３日移動平均なら、市場インから３日を過ぎたら、利確）パフォーマンスの違いを見る
    INの時にsellとbuyのどっちが多いのか
"""


def cal_rimawari(df,):
    """
    trade履歴から、年間の利回りを計算する関数
    利回りを出すやつ
    
    未だわからないところ
        日時の操作の部分
            http://sinhrks.hatenablog.com/entry/2014/10/30/233606　こいつが優秀
    """

    # 年間の利益をここで求めて挙げられる
    df.index = df.groupby(pd.to_datetime(df.index).year)
    df_profit_yearly = df['profit'].groupby(df.index).sum()


def cal_profit(df, kairi, outlier, inner, col, heikin_day):
    """
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
    state = ''
    for i in range(len(df)):
        if flag == 0:
            if df.iloc[i][outlier] and df.iloc[i][kairi] > 0:
                row.append(df.index[i].strftime('%Y-%m-%d'))
                row.append('sell')
                row.append(df.iloc[i, 5])
                state = 'sell'
                flag = 1
            elif df.iloc[i][outlier] and df.iloc[i][kairi] < 0:
                row.append(df.index[i].strftime('%Y-%m-%d'))
                row.append('buy')
                row.append(-1 * df.iloc[i, 5])
                state = 'buy'
                flag = 1
        elif flag == 1:
            if df.iloc[i][inner] and state == 'sell':
                row.append(df.index[i].strftime('%Y-%m-%d'))
                row.append('buy')
                row.append(-1 * df.iloc[i, 5])
                row.append(row[3] + row[6])  # 損益の計算
                df_result.loc[i] = row
                state = ''
                flag = 0
                row = [heikin_day]
            elif df.iloc[i][inner] and state == 'buy':
                row.append(df.index[i].strftime('%Y-%m-%d'))
                row.append('sell')
                row.append(df.iloc[i, 5])
                row.append(row[3] + row[6])  # 損益の計算
                df_result.loc[i] = row
                state = ''
                flag = 0
                row = [heikin_day]
    return df_result


def cal_profit_2(df, kairi, outlier, inner, col, heikin_day):
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


def cal_best_heikinday(trade_df):
    """
    trade_dfを heikin_days = range(25)とかでやって
    trade_df の 合計の損益が一番高いところを探す
    新しい列をtrade_dfに作って、その'profit'の高い順位を1位〜20位でいれる
        heikindayでグループ buy
    """
    tmp_df = trade_df.groupby('heikin_day').sum().sort_values(by='profit', ascending=False)
    tmp_df['rank'] = range(1, len(tmp_df) + 1)
    tmp_df.reset_index(level=0, inplace=True)
    trade_df = pd.merge(trade_df, tmp_df.loc[:, ['heikin_day', 'rank']], on='heikin_day')
    trade_df.to_excel('trade_history.xlsx', index=False)
    # return trade_df.groupby('heikin_day').sum()


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

        # カラムの作成
        df[kairi] = 100 * (df['adj_end'] - df['adj_end'].rolling(window=heikin_day).mean()) / df['adj_end'].rolling(window=heikin_day).mean()  # 乖離率計算
        df[outline] = 1.96 * df[kairi].std()  # 95%信頼区間の値
        df[outlier] = abs(df[kairi] - df[kairi].mean()) > 1.96 * df[kairi].std()  # 外側かどうか
        df[inner] = abs(df[kairi] - df[kairi].mean()) < 0.67 * df[kairi].std()  # 50% 範囲内に入るかどうか

        # return_dfにしまう作業
        tmp_df = cal_profit(df, kairi, outlier, inner, col, heikin_day)
        return_df = pd.concat([return_df, tmp_df])
    return return_df

PATH = './prices/1330.csv'

# csvファイルを古い順に読み込む
df = pd.read_csv(PATH, index_col=0, names=['date', '　start', 'high', 'low', 'end', 'volume', 'adj_end'])
df.index = pd.to_datetime(df.index)
df = df.iloc[::-1]  # 上下反転させる

# 取引履歴をゲットしてあげる
heikin_days = range(20)
trade_df = get_trade_history(df, heikin_days)
trade_df.to_excel('cal.xlsx', index=False)

# 移動平均の日数で制度の良い物事にランク付けをする
cal_best_heikinday(trade_df)

# XX日移動平均乖離率のXXによる違いを調べたいなら
# print trade_df.groupby('heikin_day').sum()

# order(sell / buy の数を数えたいなら)
# print trade_df['in_order'].value_counts()

# エクセルに吐き出したいなら
# trade_df.to_excel('trade.xlsx', index=False)
