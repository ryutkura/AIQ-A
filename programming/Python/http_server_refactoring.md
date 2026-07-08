# [[Python]]の[[HTTP]]サーバ機能の役割分割と拡張[[メソッド]]について

## 質問
今研修で[[Python]]で[[HTTP]]サーバを立てて送受信の内容をjsonファイルに入れて保存する内容のコード書いています。
機能を役割で分けたいですが、どうしたらいいか分かりません。
イメージは[[クラス]]を親[[クラス]]子[[クラス]]で分けて[[メソッド]]をオーバーロードする事ですが、単なる数字や文字列の[[変数]]でなく、通信のアレコレを受け取って起動する[[メソッド]]なので[[クラス]]を分けるのが難しいです。
調べた感じだと「拡張[[メソッド]]」があるっぽいですが、それがなんなのか分からないので手が止まっています。対策や提案をお願いします。

## 回答
[[HTTP]]サーバのような「通信処理」と「ファイル保存処理」が混ざったプログラムを綺麗に分けるのは、[[オブジェクト指向]]の[[設計]]の良い練習になりますね！
現状の悩みと解決策について整理しました。

### 1. 「拡張[[メソッド]]」について
まず結論から言うと、**今回のケースでは「拡張[[メソッド]]」は使わなくて大丈夫です。**
拡張[[メソッド]]（Extension Method）は主に[[C#]]などの言語にある機能で、「既存の[[クラス]]（例えばString[[型]]など）のソースコードを書き換えることなく、外側から新しい[[メソッド]]を後付けで追加する」機能です。
[[Python]]には言語仕様としての「拡張[[メソッド]]」は存在しません（似たような事をする手法として「モンキーパッチ」や「デコレータ」がありますが、[[設計]]を綺麗にする目的で初心者が多用するのはおすすめしません）。

通信のアレコレ（リクエストオブジェクトなど）を受け渡すのが難しいため拡張[[メソッド]]を探したのだと思いますが、もっと王道で簡単な解決策があります。

### 2. 対策と提案：どうやって役割を分けるか？
[[クラス]]の分け方として「[[継承]]（親[[クラス]]・子[[クラス]]）」をイメージされていましたが、今回のように**「違う種類の仕事（通信とファイル保存）」を分ける場合は、「委譲（コンポジション）」という手法を使うのが一般的で最も簡単です。**

#### 提案：役割ごとに[[クラス]]を完全に分け、内部で呼び出す（委譲）
「[[HTTP]]通信を担当する[[クラス]]」と「[[JSON]]の保存を担当する[[クラス]]」を別々に作り、[[HTTP]]担当[[クラス]]の中に[[JSON]]保存担当[[クラス]]を持たせます。

以下は標準ライブラリの `http.server` を使った具体的なイメージです。

```python
import json
from http.server import Base[[HTTP]]RequestHandler, [[HTTPS]]erver

# 役割1: データを[[JSON]]に保存する専門の[[クラス]]（通信のことは一切知らない）
class JsonLogger:
    def __init__(self, filepath):
        self.filepath = filepath

    def save_request_data(self, method, path, headers_dict):
        # 通信の複雑なオブジェクトではなく、文字列や[[辞書]]だけを受け取るようにする
        data = {
            "method": method,
            "path": path,
            "headers": headers_dict
        }
        with open(self.filepath, 'a', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            f.write('\n')

# 役割2: [[HTTP]]通信を担当する[[クラス]]
class MyHttpRequestHandler(Base[[HTTP]]RequestHandler):
    # handlerは[[インスタンス]]化されるタイミングが特殊なので、
    # [[クラス]][[変数]]としてLoggerを持たせるか、処理の中で[[インスタンス]]化します。
    logger = JsonLogger("server_log.json")

    def do_[[GET]](self):
        # 1. リクエストの情報を抽出する（通信処理）
        headers_dict = dict(self.headers)
        
        # 2. 記録は JsonLogger [[クラス]]にお任せする（ここで役割分担！）
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

### [[設計]]のコツ
1. **情報を抽出してから渡す**: 通信の複雑なオブジェクト（`self.request`など）を別の[[クラス]]に渡すから難しくなります。[[HTTP]]を担当する[[クラス]]の中で「[[メソッド]]名(文字列)」や「ヘッダー([[辞書]])」など、**単なる文字列や[[辞書]]のデータに変換してから**保存用の[[クラス]]に渡してあげると、[[クラス]]同士が疎結合になり綺麗に分かれます。
2. **[[継承]]（親・子）の使い所**: 「親[[クラス]]・子[[クラス]]（[[継承]]）」は、「動物・犬」のように**「AはBの一種である」**という関係の時に使います。今回のように「[[HTTP]]サーバ」と「ファイル保存」は別物なので、[[継承]]ではなく「AがBの機能を使う（委譲）」という関係で[[設計]]するのがベターです。

まずは上記のように「[[JSON]]に保存する[[クラス]]」を独立させて作ってみてください！
