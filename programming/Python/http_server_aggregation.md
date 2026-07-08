# 複数マイコンからのデータ受信と集約・連携戦略（[[HTTP]]サーバ）

## 質問
もっと具体的にお話しします。マイコンから信号を受け取って[[Python]]の[[HTTP]]レシーバーで[[JSON]]処理して[[MVC]]の[[View]]に流すプログラムです。
マイコンからは1機から受け取る時もあれば、2機から受け取って集約処理をして[[View]]に流す用に[[JSON]]を作成する必要があります。そのため[[メソッド]]が長く、冗長になる可能性があるのが怖いです。
しかも違うMAC[[アドレス]]からの機器をどうやって結び付けていけばいいのかが分からないため悩んでいます。

## 回答
具体的な背景が見えてきました！これは[[IoT]]システムの中継サーバ（エッジゲートウェイ等）で非常によく発生する、**「非同期データの待ち合わせと集約（Aggregation）」**という[[設計]]の腕の見せ所となる課題です。

[[HTTP]]通信そのものは「ステートレス（状態を持たない）」なので、バラバラに来るマイコンからのデータをサーバ側で上手く記憶し、結びつける仕組み（[[アーキテクチャ]]）を作る必要があります。[[メソッド]]が長くなるのを防ぐ役割分担と、機器の紐付け方について解説します。

---

### 1. 違うMAC[[アドレス]]の機器をどうやって結びつけるか？（紐付け戦略）
バラバラのマイコン（MAC[[アドレス]]AとMAC[[アドレス]]B）から来たデータを「これは同じグループのデータだ」と判断するには、以下の2パターンのどちらかを採用します。

* **パターンA：設定ファイル（Config）で事前にペアを定義しておく（おすすめ）**
  サーバ側に「MAC-A と MAC-B は『グループ1』である」というマッピング表を持たせておきます。
  ```python
  # サーバ側の事前設定のイメージ
  DEVICE_GROUPS = {
      "MAC-A": "group_1",
      "MAC-B": "group_1",
      "MAC-C": "group_2"
  }
  ```
  データが来たら、MAC[[アドレス]]からグループIDを引き当てて、同じグループIDのデータとして集約します。

* **パターンB：マイコン側から共通の「セッションID」や「ジョブID」を送ってもらう**
  もしマイコン同士が通信できたり、同じ作業ロットを処理しているなら、マイコンからの[[HTTPリクエスト]]の[[JSON]]に `{"job_id": "job_001", "mac": "MAC-A", ...}` のように共通のIDを含めて送信させます。サーバは `job_001` というキーでデータを結合します。

### 2. [[メソッド]]が長くならないための「役割分割」（[[設計]]方針）
このシステムを1つの巨大な `do_[[P[[OS]]T]]()` [[メソッド]]の中に書くと、確実にスパゲッティコード（巨大で読めないコード）になります。以下のように**[[クラス]]（役割）を4つに分割**します。

1. **Receiver（[[HTTP]]ハンドラ）**: [[HTTP]]を受信し、[[JSON]]を取り出して `Aggregator` に渡すだけ。
2. **Aggregator（集約係）**: データを受け取り、メモリ上（またはDB/Redis）に一時保存する。全員揃ったかを判定する。
3. **DataProcessor（変換係）**: 揃ったデータを元に、[[View]]用の複雑な[[JSON]]フォーマットに変換する。
4. **[[View]]Notifier（送信係）**: [[View]]側にデータを流す。

#### 実装イメージ（[[Python]]）

```python
from http.server import Base[[HTTP]]RequestHandler
import json
import time

# ---------------------------------------------------------
# 1. デバイスの紐付けと、データの集約を担当する[[クラス]]（Aggregator）
# ---------------------------------------------------------
class DataAggregator:
    def __init__(self):
        # グループごとにデータを一時保存する[[辞書]]
        self.temp_storage = {}
        # どのMAC[[アドレス]]がどのグループかという定義
        self.device_map = {
            "00:11:22:33:44:AA": "Line_A",
            "00:11:22:33:44:BB": "Line_A", # AAとBBは同じグループ(Line_A)
            "00:11:22:33:44:CC": "Line_B"  # CCは単独で動く(Line_B)
        }
        # グループごとに、何台のデータが揃ったら完了とするか
        self.required_counts = {
            "Line_A": 2, # AAとBBの2台揃ったら完了
            "Line_B": 1  # 1台だけで完了
        }

    def receive_data(self, mac_address, payload):
        group_id = self.device_map.get(mac_address)
        if not group_id:
            return None # 知らないデバイスは無視するかエラーにする
        
        # グループのストレージを初期化
        if group_id not in self.temp_storage:
            self.temp_storage[group_id] = {}
        
        # データを保存 (MAC[[アドレス]]をキーにして上書き/保存)
        self.temp_storage[group_id][mac_address] = payload

        # 必要な台数分データが揃ったかチェック！
        current_count = len(self.temp_storage[group_id])
        if current_count >= self.required_counts[group_id]:
            # 揃ったので、集約したデータを返して、ストレージを掃除する
            aggregated_data = self.temp_storage.pop(group_id)
            return group_id, aggregated_data
        else:
            # まだ揃っていないので待つ（Noneを返す）
            return None

# ---------------------------------------------------------
# 2. [[View]]用の複雑な[[JSON]]フォーマットを作成する専門[[クラス]]
# ---------------------------------------------------------
class [[View]]Formatter:
    @staticmethod
    def format_for_view(group_id, aggregated_data):
        # aggregated_data は {"MAC-A": {...}, "MAC-B": {...}} のような形になっている
        # ここで[[View]]が求める複雑な[[JSON]]の構造を組み立てる。
        # この処理を別の[[クラス]]・[[メソッド]]に切り出すことでコードがスッキリします。
        
        view_json = {
            "timestamp": time.time(),
            "target_line": group_id,
            "sensor_values": []
        }
        for mac, data in aggregated_data.items():
            view_json["sensor_values"].append({
                "device_mac": mac,
                "value": data.get("sensor_val", 0)
            })
        return view_json

# ---------------------------------------------------------
# 3. 全体を指揮する[[HTTP]]レシーバー（薄く保つ！）
# ---------------------------------------------------------
# Aggregatorは[[インスタンス]]化して使い回す（状態を保持するため）
global_aggregator = DataAggregator()

class MyReceiver(Base[[HTTP]]RequestHandler):
    def do_[[P[[OS]]T]](self):
        # 1. [[HTTP]]の受信と解析（薄い処理）
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length)
        payload = json.loads(body.decode('utf-8'))
        mac_address = payload.get("mac_address")

        # 2. Aggregatorにデータを丸投げする
        result = global_aggregator.receive_data(mac_address, payload)

        # 3. もしデータが規定数揃って返ってきたら、[[View]]の処理へ回す
        if result is not None:
            group_id, aggregated_data = result
            
            # [[View]]用の形式に変換（別の専門[[クラス]]に任せる！）
            view_data = [[View]]Formatter.format_for_view(group_id, aggregated_data)
            
            # TODO: ここで [[MVC]] の [[View]] や [[Controller]] へ view_data を送信する処理を書く
            print(f"[[View]]へデータを送信します: {view_data}")

        # レスポンスを返す
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')
```

### まとめ：[[メソッド]]を短く保つための秘訣
「受信する」「相手を判定する」「揃うまで待つ」「[[View]]の形式に整える」という別々の仕事を、すべて `do_[[P[[OS]]T]]` の中で `if` や `for` を使って書こうとすると破綻します。
上記のように、**「データをプールして揃ったか判定する（Aggregator）」**と、**「[[View]]向けの形に加工する（Formatter）」**という別の[[クラス]]を作り、処理を「お任せ（委譲）」することで、それぞれの[[メソッド]]は非常に短く、読みやすくなります。

まずは、MAC[[アドレス]]をグループ化する「[[辞書]]（マッピング表）」を作るところから[[設計]]を始めてみてください！
