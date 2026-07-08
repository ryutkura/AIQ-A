# 入退室の重複（ON/OFFの連続）を考慮した稼働時間の計算

「ON, ON, OFF, ON, ON, OFF, OFF, OFF」のように、途中退室がありながらも「誰かが部屋にいる状態（全体の稼働状態）」が継続している場合、おっしゃる通り**「現在の入場人数（滞在者数）をカウントする[[変数]]」を持たせるのが大正解**です。

これはプログラミングにおいて**「参照カウント（Reference Counting）」**とよく似た考え方です。
「人数が `0` から `1` になった瞬間」を稼働開始とし、「人数が `1` から `0` になった瞬間」を稼働終了として判定することで、途中での出入りに影響されずトータルの時間を取得できます。

## [[Python]] (Pandas) を使った実装例

前回のコードをベースに、人数カウント（`current_visitors`）の仕組みを組み込んだ実装例です。

### コード例

```python
import [[pandas]] as pd

def calculate_occupied_time(input_file, output_file):
    """
    入場人数の増減をカウントし、誰かが滞在していたトータルの時間を計算して出力する
    """
    df = pd.read_csv(input_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 処理が狂わないよう、必ず時系列順に並び替える
    df = df.sort_values('timestamp')
    
    results = []
    start_time = None
    
    # 【追加】現在部屋にいる人数を保持する[[インスタンス]][[変数]]（カウンター）
    current_visitors = 0
    
    for index, row in df.iterrows():
        current_flag = row['flag']
        current_time = row['timestamp']
        
        if current_flag == 'ON':
            # 誰もいなかった部屋に、1人目が入った瞬間に「開始」とみなす
            if current_visitors == 0:
                start_time = current_time
            
            # 入場したので人数を+1
            current_visitors += 1
            
        elif current_flag == 'OFF':
            # エラー防止：何らかのログの欠損で0人未満にならないようにガード
            if current_visitors > 0:
                # 退室したので人数を-1
                current_visitors -= 1
                
            # 人数が減った結果「0人」になった場合、そこを「終了」とみなす
            if current_visitors == 0 and start_time is not None:
                end_time = current_time
                
                # 稼働時間（時間単位）の計算
                duration_hours = (end_time - start_time).total_seconds() / 3600.0
                
                results.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_hours': duration_hours
                })
                
                # 次の入室に備えて開始時間をリセット
                start_time = None

    # ※補足：1日の終わりに動作させた際、まだ「退室していない（OFFがない）人」がいる場合の警告
    if current_visitors > 0 and start_time is not None:
        print(f"【警告】ファイルの末尾に到達しましたが、まだ {current_visitors} 人が滞在中の状態です。")
        print(f"最後に記録された開始時間: {start_time}")
        # 必要に応じて、23:59:59を強制的な終了時間に設定するなどの処理をここに追加できます

    # 集計結果のCSV出力
    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"集計成功：{len(result_df)}件の稼働記録を {output_file} に出力しました。")
    else:
        print("有効な稼働区間が見つかりませんでした。")

# 実行例
if __name__ == "__main__":
    calculate_occupied_time('origin_data.csv', 'occupied_time_summary.csv')
```

### この実装のポイント
1. **人数のカウント (`current_visitors`)**
   [[変数]]を1つ用意し、ONで `+1`、OFFで `-1` を行います。「日次バッチ処理」として1日の終わりに実行する場合、処理が終わればこの[[変数]]は破棄されるため、仰る通り[[データベース]]などに常時保存しておく必要はありません。
2. **開始と終了のトリガー**
   「ONが来たから」ではなく、**「ONが来て人数が `0` から `1` に変わったから」**開始時間を記録します。同様に、**「OFFが来て人数が `1` から `0` に変わったから」**終了時間を記録します。これで途中の入退室は単なる「人数の増減」として処理され、稼働時間の計算には影響しなくなります。
3. **データ不整合への対策**
   センサーエラーやログの取りこぼしで、ONがないのにOFFだけが記録された場合、マイナス人数になると計算がおかしくなります。そのため `if current_visitors > 0:` の時だけマイナスする（0未満にはしない）という防波堤を入れています。
4. **日またぎ・退室忘れの考慮**
   ファイルの最後まで読み終わったのに `current_visitors` が0になっていない場合、誰かが退室を忘れています。バッチ処理の運用に合わせて、警告ログを出すだけに留めるか、強制的にその日の「23:59:59」を終了時間として算入するか、[[設計]]を工夫できる余地を残しています。

---

## 補足：よくある疑問とカスタマイズ

### `df.sort_values()` は昇順？降順？なぜ必要？
`df.sort_values('timestamp')` は、デフォルトで**「昇順（古い時間から新しい時間へ）」**でソート（並び替え）されます。
わざわざソートする理由は以下の通りです：
* **時系列の保証**: 今回のような「状態（人数の増減）」を追跡する[[アルゴリズム]]は、過去から未来へ順番にデータを処理していくことが大前提です。
* **データの乱れへの対応**: ネットワークの遅延や複数センサーからのデータ統合などにより、CSVファイル内の行が時間順に並んでいないケースは実務上非常によくあります。ソートを省くと「未来の退室処理の後に過去の入室処理が行われる」といった矛盾が生じ、計算結果が崩壊してしまいます。

### 別の指標を追加したい場合の適切なインデント（階層）
取得したい指標の性質によって、計算を挿入する最適な「インデント（コードの階層）」が変わります。以下を参考にしてください。

**1. 「その日全体の指標」を計算する場合（最大同時滞在人数、トータル入場者数など）**
全体のループの外側で[[変数]]を準備し、フラグごとの処理の直後などに配置します。
```python
    current_visitors = 0
    max_visitors = 0      # 全体指標の[[変数]]を用意
    total_entries = 0

    for index, row in df.iterrows():
        # ... (ON/OFFの判定処理) ...
        
        # 【このインデント(if/elif文の外、for文の直下)】
        # ここで最大人数の更新チェックを行うと一番確実です
        if current_visitors > max_visitors:
            max_visitors = current_visitors
```

**2. 「入室のタイミング」に紐づく指標（累計入室回数など）**
`if current_flag == 'ON':` のブロック内で処理します。
```python
        if current_flag == 'ON':
            if current_visitors == 0:
                start_time = current_time
            current_visitors += 1
            total_entries += 1 # 【このインデント】累計入室回数をカウント
```

**3. 「1回の稼働区間（ONからOFF）」ごとの指標（その区間の最大人数など）**
区間ごとの記録は、`results.append()` を行うブロック（`current_visitors == 0` になった瞬間）で集計し、その後リセットします。
```python
        elif current_flag == 'OFF':
            if current_visitors > 0:
                current_visitors -= 1
                
            if current_visitors == 0 and start_time is not None:
                end_time = current_time
                duration = (end_time - start_time).total_seconds() / 3600.0
                
                # 【このインデント】
                # 区間ごとの指標があれば、稼働時間と一緒に results.append() に追加します。
# 入退室の重複（ON/OFFの連続）を考慮した稼働時間の計算

「ON, ON, OFF, ON, ON, OFF, OFF, OFF」のように、途中退室がありながらも「誰かが部屋にいる状態（全体の稼働状態）」が継続している場合、おっしゃる通り**「現在の入場人数（滞在者数）をカウントする[[変数]]」を持たせるのが大正解**です。

これはプログラミングにおいて**「参照カウント（Reference Counting）」**とよく似た考え方です。
「人数が `0` から `1` になった瞬間」を稼働開始とし、「人数が `1` から `0` になった瞬間」を稼働終了として判定することで、途中での出入りに影響されずトータルの時間を取得できます。

## [[Python]] (Pandas) を使った実装例

前回のコードをベースに、人数カウント（`current_visitors`）の仕組みを組み込んだ実装例です。

### コード例

```python
import [[pandas]] as pd

def calculate_occupied_time(input_file, output_file):
    """
    入場人数の増減をカウントし、誰かが滞在していたトータルの時間を計算して出力する
    """
    df = pd.read_csv(input_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 処理が狂わないよう、必ず時系列順に並び替える
    df = df.sort_values('timestamp')
    
    results = []
    start_time = None
    
    # 【追加】現在部屋にいる人数を保持する[[インスタンス]][[変数]]（カウンター）
    current_visitors = 0
    
    for index, row in df.iterrows():
        current_flag = row['flag']
        current_time = row['timestamp']
        
        if current_flag == 'ON':
            # 誰もいなかった部屋に、1人目が入った瞬間に「開始」とみなす
            if current_visitors == 0:
                start_time = current_time
            
            # 入場したので人数を+1
            current_visitors += 1
            
        elif current_flag == 'OFF':
            # エラー防止：何らかのログの欠損で0人未満にならないようにガード
            if current_visitors > 0:
                # 退室したので人数を-1
                current_visitors -= 1
                
            # 人数が減った結果「0人」になった場合、そこを「終了」とみなす
            if current_visitors == 0 and start_time is not None:
                end_time = current_time
                
                # 稼働時間（時間単位）の計算
                duration_hours = (end_time - start_time).total_seconds() / 3600.0
                
                results.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_hours': duration_hours
                })
                
                # 次の入室に備えて開始時間をリセット
                start_time = None

    # ※補足：1日の終わりに動作させた際、まだ「退室していない（OFFがない）人」がいる場合の警告
    if current_visitors > 0 and start_time is not None:
        print(f"【警告】ファイルの末尾に到達しましたが、まだ {current_visitors} 人が滞在中の状態です。")
        print(f"最後に記録された開始時間: {start_time}")
        # 必要に応じて、23:59:59を強制的な終了時間に設定するなどの処理をここに追加できます

    # 集計結果のCSV出力
    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"集計成功：{len(result_df)}件の稼働記録を {output_file} に出力しました。")
    else:
        print("有効な稼働区間が見つかりませんでした。")

# 実行例
if __name__ == "__main__":
    calculate_occupied_time('origin_data.csv', 'occupied_time_summary.csv')
```

### この実装のポイント
1. **人数のカウント (`current_visitors`)**
   [[変数]]を1つ用意し、ONで `+1`、OFFで `-1` を行います。「日次バッチ処理」として1日の終わりに実行する場合、処理が終わればこの[[変数]]は破棄されるため、仰る通り[[データベース]]などに常時保存しておく必要はありません。
2. **開始と終了のトリガー**
   「ONが来たから」ではなく、**「ONが来て人数が `0` から `1` に変わったから」**開始時間を記録します。同様に、**「OFFが来て人数が `1` から `0` に変わったから」**終了時間を記録します。これで途中の入退室は単なる「人数の増減」として処理され、稼働時間の計算には影響しなくなります。
3. **データ不整合への対策**
   センサーエラーやログの取りこぼしで、ONがないのにOFFだけが記録された場合、マイナス人数になると計算がおかしくなります。そのため `if current_visitors > 0:` の時だけマイナスする（0未満にはしない）という防波堤を入れています。
4. **日またぎ・退室忘れの考慮**
   ファイルの最後まで読み終わったのに `current_visitors` が0になっていない場合、誰かが退室を忘れています。バッチ処理の運用に合わせて、警告ログを出すだけに留めるか、強制的にその日の「23:59:59」を終了時間として算入するか、[[設計]]を工夫できる余地を残しています。

---

## 補足：よくある疑問とカスタマイズ

### `df.sort_values()` は昇順？降順？なぜ必要？
`df.sort_values('timestamp')` は、デフォルトで**「昇順（古い時間から新しい時間へ）」**でソート（並び替え）されます。
わざわざソートする理由は以下の通りです：
* **時系列の保証**: 今回のような「状態（人数の増減）」を追跡する[[アルゴリズム]]は、過去から未来へ順番にデータを処理していくことが大前提です。
* **データの乱れへの対応**: ネットワークの遅延や複数センサーからのデータ統合などにより、CSVファイル内の行が時間順に並んでいないケースは実務上非常によくあります。ソートを省くと「未来の退室処理の後に過去の入室処理が行われる」といった矛盾が生じ、計算結果が崩壊してしまいます。

### 別の指標を追加したい場合の適切なインデント（階層）
取得したい指標の性質によって、計算を挿入する最適な「インデント（コードの階層）」が変わります。以下を参考にしてください。

**1. 「その日全体の指標」を計算する場合（最大同時滞在人数、トータル入場者数など）**
全体のループの外側で[[変数]]を準備し、フラグごとの処理の直後などに配置します。
```python
    current_visitors = 0
    max_visitors = 0      # 全体指標の[[変数]]を用意
    total_entries = 0

    for index, row in df.iterrows():
        # ... (ON/OFFの判定処理) ...
        
        # 【このインデント(if/elif文の外、for文の直下)】
        # ここで最大人数の更新チェックを行うと一番確実です
        if current_visitors > max_visitors:
            max_visitors = current_visitors
```

**2. 「入室のタイミング」に紐づく指標（累計入室回数など）**
`if current_flag == 'ON':` のブロック内で処理します。
```python
        if current_flag == 'ON':
            if current_visitors == 0:
                start_time = current_time
            current_visitors += 1
            total_entries += 1 # 【このインデント】累計入室回数をカウント
```

**3. 「1回の稼働区間（ONからOFF）」ごとの指標（その区間の最大人数など）**
区間ごとの記録は、`results.append()` を行うブロック（`current_visitors == 0` になった瞬間）で集計し、その後リセットします。
```python
        elif current_flag == 'OFF':
            if current_visitors > 0:
                current_visitors -= 1
                
            if current_visitors == 0 and start_time is not None:
                end_time = current_time
                duration = (end_time - start_time).total_seconds() / 3600.0
                
                # 【このインデント】
                # 区間ごとの指標があれば、稼働時間と一緒に results.append() に追加します。
                results.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_hours': duration,
                    # 'session_max_visitors': session_max_visitors # 別の[[変数]]で集計しておいた場合
                })
                # 追加後、次の区間のために session_max_visitors などをリセットする
```

### 他の[[Python]]ファイルの[[クラス]][[メソッド]]を呼び出してフォルダを作成する場合
実務では、「他のスクリプトが持つ機能（[[クラス]][[メソッド]]等）を呼び出してフォルダを作成し、そこにCSVを出力する」という連携がよく行われます。

例えば、別ファイル `folder_manager.py` に以下のような[[クラス]][[メソッド]]があるとします。
```python
# folder_manager.py
import os

class FolderManager:
    @classmethod
    def create_output_folder(cls, folder_path):
        """指定されたパスにフォルダを作成する[[クラス]][[メソッド]]"""
        os.makedirs(folder_path, exist_ok=True)
        print(f"フォルダ作成確認: {folder_path}")
```

この機能を先ほどの集計スクリプトから呼び出す場合の記述は以下のようになります。

```python
import os
import [[pandas]] as pd
# 1. 別ファイル(folder_manager.py)から必要な[[クラス]]をインポートする
from folder_manager import FolderManager

def calculate_occupied_time(input_file, output_dir, output_filename):
    # (先ほどのデータの読み込みと集計処理...)
    # df = pd.read_csv(input_file)
    # ... 中略 ...
    # result_df = pd.DataFrame(results)
    
    if not result_df.empty:
        # 2. 出力直前に、インポートした別ファイルの[[クラス]][[メソッド]]を実行してフォルダを作成
        FolderManager.create_output_folder(output_dir)
        
        # 3. フォルダのパスとファイル名を結合して、最終的な出力先パスを作る
        output_path = os.path.join(output_dir, output_filename)
        
        # 4. 作成されたフォルダの中へCSVを出力
        result_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"出力完了: {output_path}")
    else:
        print("有効な稼働区間が見つかりませんでした。")
```

#### コードの解説
* **`from [ファイル名] import [クラス名]`**: 同じディレクトリ（またはパスが通っている場所）にある別の[[Python]]ファイル（拡張子 `.py` は不要）から、使いたい[[クラス]]を読み込みます。
* **[[クラス]][[メソッド]]の呼び出し (`FolderManager.create_output_folder()`)**: [[クラス]]を[[インスタンス]]化（`manager = FolderManager()` のような処理）しなくても、`@classmethod` 等で定義された[[メソッド]]は `[[クラス]]名.[[メソッド]]名()` の形で直接実行できます。
* **`os.path.join(ディレクトリ, ファイル名)`**: フォルダのパスとファイル名を[[OS]]に応じた正しい記号（[[Windows]]なら `\`、Mac/[[Linux]]なら `/`）で安全に結合してくれます。直接 `output_dir + "/" + output_filename` のように文字列を足し算するよりもバグが起きにくい推奨の書き方です。
