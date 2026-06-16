# 巨大なクラスメソッド（Fat Method）の安全な分割・リファクタリング手法

## 質問
関数を分けたいですが分けられません！
もらったサーバー用のコードが、1個の関数（メソッド）で全てを動かしてしまっています。しかもクラスメソッドなので変数の扱いなどがめんどくさいです。
上手いことやれる関数の分け方を教えてください。

## 回答
「他人が書いた巨大な1つのメソッド（通称：Fat Method、神メソッド）」を解きほぐすのは、実務で誰もがぶつかる壁ですね！
クラスのメソッドとして書かれていると、`self`（インスタンス変数）がそこら中で使われていて、単純に関数を外に出そうとするとエラーになりがちです。

巨大なメソッドを「安全に」「綺麗に」分割するための**3つのステップ（王道のリファクタリング手法）**を解説します。

---

### ステップ1：まずは「同じクラスの中」で小さなメソッドに切り出す
一番安全な方法は、関数の外に飛び出すのではなく、**同じクラスの中に「ヘルパーメソッド」を作る**ことです。
同じクラス内であれば `self` をそのまま使えるため、既存の変数が壊れるリスクが最も低いです。

**【リファクタリング前（巨大なメソッド）】**
```python
class MyServer:
    def process_all(self, payload):
        # 1. データの解析処理（ここだけで30行あるとする）
        mac = payload.get("mac")
        val = payload.get("val")
        # ...色々な処理...

        # 2. [[データベース]]保存処理（ここだけで50行あるとする）
        # self.db_connection を使っているから外に出しづらい
        self.db.save(mac, val)
        # ...色々な処理...
```

**【リファクタリング後（内部メソッドへの切り出し）】**
処理の塊ごとに、名前の先頭に `_`（アンダースコア）を付けた内部用メソッドを作って呼び出します。
```python
class MyServer:
    def process_all(self, payload):
        # メインの関数は「指揮者」になる。処理の流れだけを書く。
        parsed_data = self._parse_payload(payload)
        self._save_to_db(parsed_data)

    def _parse_payload(self, payload):
        # 解析処理だけをここに移動
        mac = payload.get("mac")
        val = payload.get("val")
        return {"mac": mac, "val": val}

    def _save_to_db(self, parsed_data):
        # DB処理だけをここに移動（selfもそのまま使える！）
        self.db.save(parsed_data["mac"], parsed_data["val"])
```
まずはこのように、巨大な関数を「目次（指揮者）」に変えてしまうのが第一歩です。

### ステップ2：通信（[[HTTP]]）と処理（ビジネスロジック）を切り離す
ステップ1で「目次」ができたら、次は「[[HTTP]]の通信に関するアレコレ（ヘッダーを読む、レスポンスを返すなど）」と、「純粋なデータ処理（JSONの中身を計算する等）」を完全に切り離します。

**コツは、「[[HTTP]]のリクエストオブジェクト（self.requestなど）をそのまま別の関数に渡さない」ことです。**
文字列や辞書（dict）などの純粋な[[Python]]のデータに変換してから、別の関数に渡します。

### ステップ3：アダプター（分岐）を組み込む
今回のように「ボタン」と「センサー」という違う処理を混ぜる場合は、ステップ1で作った「指揮者」のメソッドの中で分岐させます。

```python
class MyServer:
    def do_[[POST]](self): # <- 巨大だったメソッド
        # 1. 通信データを辞書(dict)に変換する
        payload = self._get_json_payload()
        mac = payload.get("mac")

        # 2. 種類を判定する
        if self._is_button(mac):
            # ボタン用の小さなメソッドへ
            self._handle_button(payload)
        else:
            # センサー用の小さなメソッドへ
            self._handle_sensor(payload)
            
        # 3. レスポンスを返す
        self._send_success_response()

    # --- 以下、切り出した小さなメソッド群 ---
    def _handle_button(self, payload):
        val = payload.get("value")
        self._save_entry_exit(payload["mac"], val) # 既存の処理

    def _handle_sensor(self, payload):
        # ここで新しく作った「アダプター（状態管理）」を呼び出す
        result = self.sensor_monitor.check(payload["mac"])
        if result == "入場":
            self._save_entry_exit(payload["mac"], 1) # 1に翻訳して既存の処理へ
        elif result == "退場":
            self._save_entry_exit(payload["mac"], 0) # 0に翻訳して既存の処理へ
```

### まとめ：上手な分け方のコツ
1. **いきなりクラスの外に出さない**：まずは同じクラス内の `def _メソッド名(self):` として切り出し、エラーなく動くことを確認する。
2. **関数名で「何をしているか」を語る**：抽出したメソッド名は `_handle_sensor` や `_save_to_db` のように、中身を見なくてもやっていることが分かる名前にする。
3. **メイン関数は「指揮者」にする**：元の巨大な関数は、具体的な計算は一切せず「君はこれをやって、次に君はこれをして」と指示を出すだけの状態（数十行程度）にする。

この手順で進めれば、`self` の呪縛に悩まされることなく、既存の複雑なコードを安全に解体できます！
