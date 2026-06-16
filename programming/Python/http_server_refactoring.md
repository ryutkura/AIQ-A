# [[Python]]の[[HTTP]]サーバ機能の役割分割と拡張メソッドについて

## 質問
今研修で[[Python]]で[[HTTP]]サーバを立てて送受信の内容をjsonファイルに入れて保存する内容のコード書いています。
機能を役割で分けたいですが、どうしたらいいか分かりません。
イメージはクラスを親クラス子クラスで分けてメソッドをオーバーロードする事ですが、単なる数字や文字列の変数でなく、通信のアレコレを受け取って起動するメソッドなのでクラスを分けるのが難しいです。
調べた感じだと「拡張メソッド」があるっぽいですが、それがなんなのか分からないので手が止まっています。対策や提案をお願いします。

## 回答
[[HTTP]]サーバのような「通信処理」と「ファイル保存処理」が混ざったプログラムを綺麗に分けるのは、オブジェクト指向の設計の良い練習になりますね！
現状の悩みと解決策について整理しました。

### 1. 「拡張メソッド」について
まず結論から言うと、**今回のケースでは「拡張メソッド」は使わなくて大丈夫です。**
拡張メソッド（Extension Method）は主に[[C#]]などの言語にある機能で、「既存のクラス（例えばString型など）のソースコードを書き換えることなく、外側から新しいメソッドを後付けで追加する」機能です。
[[Python]]には言語仕様としての「拡張メソッド」は存在しません（似たような事をする手法として「モンキーパッチ」や「デコレータ」がありますが、設計を綺麗にする目的で初心者が多用するのはおすすめしません）。

通信のアレコレ（リクエストオブジェクトなど）を受け渡すのが難しいため拡張メソッドを探したのだと思いますが、もっと王道で簡単な解決策があります。

### 2. 対策と提案：どうやって役割を分けるか？
クラスの分け方として「継承（親クラス・子クラス）」をイメージされていましたが、今回のように**「違う種類の仕事（通信とファイル保存）」を分ける場合は、「委譲（コンポジション）」という手法を使うのが一般的で最も簡単です。**

#### 提案：役割ごとにクラスを完全に分け、内部で呼び出す（委譲）
「[[HTTP]]通信を担当するクラス」と「JSONの保存を担当するクラス」を別々に作り、[[HTTP]]担当クラスの中にJSON保存担当クラスを持たせます。

以下は標準ライブラリの `http.server` を使った具体的なイメージです。

```python
import json
from http.server import Base[[HTTP]]RequestHandler, [[HTTPS]]erver

# 役割1: データをJSONに保存する専門のクラス（通信のことは一切知らない）
class JsonLogger:
    def __init__(self, filepath):
        self.filepath = filepath

    def save_request_data(self, method, path, headers_dict):
        # 通信の複雑なオブジェクトではなく、文字列や辞書だけを受け取るようにする
        data = {
            "method": method,
            "path": path,
            "headers": headers_dict
        }
        with open(self.filepath, 'a', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            f.write('\n')

# 役割2: [[HTTP]]通信を担当するクラス
class MyHttpRequestHandler(Base[[HTTP]]RequestHandler):
    # handlerはインスタンス化されるタイミングが特殊なので、
    # クラス変数としてLoggerを持たせるか、処理の中でインスタンス化します。
    logger = JsonLogger("server_log.json")

    def do_[[GET]](self):
        # 1. リクエストの情報を抽出する（通信処理）
        headers_dict = dict(self.headers)
        
        # 2. 記録は JsonLogger クラスにお任せする（ここで役割分担！）
        # 通信のオブジェクト(self)を丸ごと渡すのではなく、必要な情報だけを取り出して渡すのがコツです。
        self.logger.save_request_data(self.command, self.path, headers_dict)

        # 3. クライアントへレスポンスを返す（通信処理）
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"OK")

def run(server_class=[[HTTPS]]erver, handler_class=MyHttpRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting httpd on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
```

### 設計のコツ
1. **情報を抽出してから渡す**: 通信の複雑なオブジェクト（`self.request`など）を別のクラスに渡すから難しくなります。[[HTTP]]を担当するクラスの中で「メソッド名(文字列)」や「ヘッダー(辞書)」など、**単なる文字列や辞書のデータに変換してから**保存用のクラスに渡してあげると、クラス同士が疎結合になり綺麗に分かれます。
2. **継承（親・子）の使い所**: 「親クラス・子クラス（継承）」は、「動物・犬」のように**「AはBの一種である」**という関係の時に使います。今回のように「[[HTTP]]サーバ」と「ファイル保存」は別物なので、継承ではなく「AがBの機能を使う（委譲）」という関係で設計するのがベターです。

まずは上記のように「JSONに保存するクラス」を独立させて作ってみてください！
