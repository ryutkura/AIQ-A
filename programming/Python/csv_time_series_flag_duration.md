# CSVのフラグとタイムスタンプから稼働時間を計算する方法

時系列データにおいて、「ON」フラグから「OFF」フラグまでの時間を計算し、その区間ごとの開始時間・終了時間・稼働時間（時間単位）を1行（1レコード）として新しいCSVに出力する処理の実装例です。

このような「状態（ステート）」をまたぐ計算を行う場合、データを1行ずつ確認しながら「ONになった時間」を一時的に記憶（保持）し、「OFF」が来たタイミングで計算して出力するアプローチが最も確実でわかりやすいです。

## [[Python]] (Pandas) を使った実装例

[[Python]]のデータ分析ライブラリである[[Pandas]]を使用し、状態を管理しながらループ処理を行うコード例です。

### コード例

```python
import pandas as pd

def calculate_operating_time(input_file, output_file):
    """
    ONからOFFまでの稼働時間を計算し、別のCSVに出力する
    """
    # 1. 元データの読み込み
    df = pd.read_csv(input_file)
    
    # タイムスタンプ文字列を日時(datetime)オブジェクトに変換
    # ※元の文字列フォーマットが特殊な場合は format='%Y-%m-%d %H:%M:%S' などを指定します
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 念のため、時間が古い順にソートしておく
    df = df.sort_values('timestamp')
    
    results = []        # 集計結果を格納するリスト
    start_time = None   # ONになった時間を一時記憶する変数

    # 2. データを1行ずつループ処理して状態を判定
    for index, row in df.iterrows():
        current_flag = row['flag']
        current_time = row['timestamp']
        
        if current_flag == 'ON':
            # まだON記録がない場合のみ記録する（連続でONが来た場合は最初のONを優先）
            if start_time is None:
                start_time = current_time
                
        elif current_flag == 'OFF':
            # 既にONが記録されている場合のみ計算を行う
            if start_time is not None:
                end_time = current_time
                
                # timedeltaオブジェクトから合計秒数を取得し、3600で割って「何時間か」に変換
                duration_seconds = (end_time - start_time).total_seconds()
                duration_hours = duration_seconds / 3600.0
                
                # 結果をリストに追加
                results.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_hours': duration_hours
                })
                
                # 次のONを待つためにリセット
                start_time = None

    # 3. 集計結果を新しいデータフレームに変換してCSV出力
    result_df = pd.DataFrame(results)
    
    if not result_df.empty:
        result_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"集計成功：{len(result_df)}件の稼働記録を {output_file} に出力しました。")
    else:
        print("ONからOFFになる有効な区間が見つかりませんでした。")

# 実行例
if __name__ == "__main__":
    # 入力ファイルと出力ファイルの名前を指定して実行
    calculate_operating_time('origin_data.csv', 'operating_time_summary.csv')
```

### ポイントの解説
1. **日時の変換 (`pd.to_datetime`)**
   CSVに「文字列」として格納されているタイムスタンプを、[[Python]]で引き算などの時間計算ができる日時データ（`datetime`）に変換します。
2. **状態の記憶 (`start_time = None`)**
   「ON」になった時間を保持するための箱を用意します。最初は空(`None`)にしておきます。
3. **時間の引き算と時間（Hour）への変換**
   `end_time - start_time` を行うと `timedelta` 型になり、`.total_seconds()` で秒数が取得できます。1時間は3600秒なので、3600で割ることで「確保していた時間（〇時間）」を浮動小数点数（例：1.5時間など）で表現できます。
4. **異常値のハンドリング**
   データに欠損などがあり「ON, ON, OFF」や「OFF, ON」のようなイレギュラーな順番でフラグが来てもエラーにならないよう、`if start_time is None:` などの条件分岐で堅牢（セキュア）な設計にしています。
