# [[Python]]によるCSVデータの集計と出力

オリジナルのデータを格納したCSVファイルからデータを読み込み、集計（グループ化や合計など）を行って新しいCSVファイルに出力する処理は、データ処理において非常に頻繁に行われます。

[[Python]]でこれを行う場合、主に以下の2つのアプローチがあります。
1. **Pandasライブラリを使用する方法**（推奨・コードが短く直感的）
2. **標準ライブラリ `csv` を使用する方法**（外部ライブラリをインストールできない環境向け）

ここでは両方のコード例と解説を記載します。

## 1. Pandasを使用する方法（推奨）

[[Pandas]]はデータ分析のための強力なライブラリです。数行のコードで複雑な集計を行うことができます。
事前に `pip install pandas` でインストールが必要です。

### コード例

```python
import pandas as pd

def aggregate_csv_pandas(input_file, output_file):
    """
    Pandasを使用してCSVデータを集計し、新しいCSVに出力する
    """
    # 1. オリジンデータの読み込み
    # df (DataFrame) という表形式のデータ構造として読み込みます
    df = pd.read_csv(input_file, encoding='utf-8')

    # 2. データの集計
    # 例として、「Category」列でグループ化し、「Sales」列の合計を計算します
    # reset_index()を呼ぶことで、集計結果を再び綺麗な表形式に戻します
    summary_df = df.groupby('Category')['Sales'].sum().reset_index()

    # （オプション）列名をわかりやすく変更する場合
    summary_df.rename(columns={'Sales': 'Total_Sales'}, inplace=True)

    # 3. 集計結果を新しいCSVファイルに出力
    # index=Falseを指定することで、不要な行番号が出力されるのを防ぎます
    summary_df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"集計が完了しました。出力先: {output_file}")

# 実行例
if __name__ == "__main__":
    aggregate_csv_pandas('origin_data.csv', 'aggregated_data.csv')
```

### 解説
* `pd.read_csv()`: CSVファイルを読み込み、DataFrame（表形式のデータ）に変換します。
* `groupby('Category')`: 指定した列（この場合はCategory）の値が同じ行をグループにまとめます。
* `.sum()`: グループごとに合計値を計算します。（平均なら `.mean()`、件数なら `.count()` などを指定できます）
* `to_csv()`: DataFrameの内容をCSVとして保存します。

---

## 2. 標準ライブラリ `csv` を使用する方法

外部ライブラリを使わずに[[Python]]に標準で組み込まれている機能だけで完結させる方法です。

### コード例

```python
import csv
from collections import defaultdict

def aggregate_csv_standard(input_file, output_file):
    """
    標準ライブラリを使用してCSVデータを集計し、新しいCSVに出力する
    """
    # 集計用の辞書を用意（存在しないキーにアクセスした場合は0を返す）
    summary = defaultdict(int)

    # 1. オリジンデータの読み込みと集計
    with open(input_file, mode='r', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        for row in reader:
            category = row['Category']
            # 文字列として読み込まれるため、数値に変換してから加算
            sales = int(row['Sales'])
            summary[category] += sales

    # 2. 集計結果を新しいCSVファイルに出力
    with open(output_file, mode='w', encoding='utf-8', newline='') as f_out:
        writer = csv.writer(f_out)
        
        # ヘッダー（列名）を書き込む
        writer.writerow(['Category', 'Total_Sales'])
        
        # 集計結果を1行ずつ書き込む
        for category, total_sales in summary.items():
            writer.writerow([category, total_sales])

    print(f"集計が完了しました。出力先: {output_file}")

# 実行例
if __name__ == "__main__":
    aggregate_csv_standard('origin_data.csv', 'aggregated_data.csv')
```

### 解説
* `csv.DictReader()`: CSVの1行を、ヘッダーの列名をキーとした辞書（Dictionary）として読み込みます。どの列が何番目かを意識せずに名前でアクセスできるため安全です。
* `defaultdict(int)`: 通常の辞書とは異なり、まだ登録されていないカテゴリの売上を加算しようとした際に、自動的に初期値（0）を設定してくれます。集計処理に非常に便利です。
* `csv.writer()`: リスト（配列）のデータをCSV形式でファイルに書き込みます。`newline=''` を指定することで、Windows環境で余分な空行が挿入されるのを防ぎます。
