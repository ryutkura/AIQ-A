# concepts/ スタブの定義ソース
#
#   書式:  語 | tags(カンマ区切り) | 定義（1〜2行）
#   `#` で始まる行はコメント。
#
#   make_concepts.py がこのファイルを読み、2ファイル以上から参照されている
#   キーワードについて concepts/<語>.md を生成します。
#   既存ファイルは絶対に上書きしません（育てた内容は保護されます）。

# --- 数学 ---------------------------------------------------
線形代数 | math | ベクトルと行列を扱う数学の分野。線形変換と連立方程式が中心にある。
行列 | math, linear-algebra | 数を長方形に並べたもの。線形変換を表現するための道具。
ベクトル | math, linear-algebra | 大きさと向きを持つ量。数の並びとして表現される。
確率 | math, statistics | ある事象の起こりやすさを 0〜1 の数値で表したもの。
LU分解 | math, linear-algebra | 行列を下三角行列 L と上三角行列 U の積に分解すること。連立方程式を繰り返し解く際に効く。
ガウスの消去法 | math, linear-algebra | 行の基本変形で連立一次方程式を上三角形に整理し、後退代入で解く手法。

# --- プログラミング言語 -------------------------------------
Python | programming, language | インタプリタ型の汎用プログラミング言語。可読性の高さとライブラリの豊富さが特徴。
Java | programming, language | JVM 上で動くオブジェクト指向言語。「一度書けばどこでも動く」が設計思想。
C言語 | programming, language | メモリを直接扱える低水準寄りの手続き型言語。OS や組み込みの基盤になっている。
C# | programming, language | Microsoft が開発したオブジェクト指向言語。.NET 上で動作する。
TypeScript | programming, language | JavaScript に静的な型付けを加えた言語。実行前に型の誤りを検出できる。

# --- プログラミングの基礎概念 -------------------------------
オブジェクト指向 | programming, paradigm | データと振る舞いをオブジェクトにまとめて設計する考え方。
継承 | programming, oop | 既存のクラスの性質を引き継いで新しいクラスを定義する仕組み。
アルゴリズム | programming, fundamentals | 問題を解くための手順を、有限のステップで明確に定めたもの。
データ構造 | programming, fundamentals | データを効率よく格納・アクセスするための組み立て方。
ハッシュ | programming, fundamentals | 任意のデータを固定長の値へ変換する仕組み。辞書の高速な検索や、改ざん検出に使う。
スレッド | programming, fundamentals | プロセス内で並行に走る実行の単位。メモリを共有するため、競合状態に注意が要る。
値渡し | programming, fundamentals | 引数として値のコピーを渡す方式。呼び出し先での変更は呼び出し元に影響しない。
参照渡し | programming, fundamentals | 引数として変数の在り処を渡す方式。呼び出し先での変更が呼び出し元に反映される。
ポインタ | programming, memory | メモリ上のアドレスを値として保持する変数。
アドレス | programming, memory | メモリ上の位置を示す番号。ポインタが保持している値そのもの。
参照外し | programming, memory | ポインタが指す先の実体にアクセスすること（デリファレンス）。

# --- Web / MVC ----------------------------------------------
MVC | architecture, web | アプリを Model（データ）・View（表示）・Controller（制御）の3役に分割する設計パターン。
Model | architecture, web | MVC で、データとビジネスロジックを担当する役。
View | architecture, web | MVC で、ユーザーに見せる画面を組み立てる役。
Controller | architecture, web | MVC で、リクエストを受け取り Model と View を仲介する役。処理の交通整理を担当する。
ルーティング | web | 受け取った URL をどの処理（Controller や関数）に割り当てるかを決める仕組み。
HTTP | web, network | Web ブラウザとサーバがやりとりするためのプロトコル。
HTTPS | web, network, security | HTTP を TLS で暗号化した通信。盗聴と改ざんを防ぐ。
GET | web, http | HTTP メソッドの一つ。サーバの状態を変えずに情報を取得する。
POST | web, http | HTTP メソッドの一つ。サーバの状態を変更する送信に使う。
URL | web, network | ネット上のリソースの所在を示す文字列。
HTML | web | Web ページの構造を記述するマークアップ言語。
JSON | data, web | キーと値の組でデータを表現する軽量なテキスト形式。
API | programming, web | ソフトウェアが外部に公開する呼び出し口の取り決め。

# --- データ -------------------------------------------------
データベース | data | データを構造化して永続的に保存・検索するための仕組み。
SQL | data | リレーショナルデータベースを操作するための問い合わせ言語。

# --- インフラ / Linux ---------------------------------------
Docker | infra, container | アプリを環境ごとコンテナにまとめて実行する仮想化技術。
コンテナ | infra, container | OS のカーネルを共有しつつプロセスを隔離する軽量な実行環境。
Linux | infra, os | オープンソースの UNIX 系 OS。サーバや Raspberry Pi で広く使われる。
カーネル | infra, os | OS の中核。ハードウェアとプロセスの仲介、資源の割り当てを担う。
シェル | infra, linux | ユーザーが入力したコマンドを解釈して OS に渡すプログラム。
SSH | infra, network, security | 暗号化された通信路でリモートのマシンを操作するプロトコル。
公開鍵 | security | 公開鍵暗号で、誰に見られてもよい方の鍵。暗号化や署名検証に使う。
AWS | infra, cloud | Amazon が提供するクラウドサービス群。
GitHub | infra, vcs | Git リポジトリのホスティングサービス。Issue や Pull Request による共同作業の場でもある。
LLM | ai, llm | 大規模言語モデル。膨大なテキストで訓練され、次の語を予測する形で文章生成や推論を行う。
IoT | infra | モノをネットワークに繋いでデータを収集・制御する仕組み。
Raspberry Pi | infra, hardware | 手のひらサイズの小型コンピュータ。IoT や学習用途で広く使われる。

# --- ソフトウェア工学 ---------------------------------------
アーキテクチャ | software-engineering, design | システム全体の構造と、構成要素の分け方・繋ぎ方の設計。
要件定義 | software-engineering, requirements | 作るべきシステムが満たすべき条件を、関係者と合意して言語化する工程。
ヒアリング | software-engineering, requirements | 利害関係者から要求や課題を聞き出す活動。要件定義の入口。
ユースケース | software-engineering, requirements | システムがユーザーに提供する、目的達成までの一連のやりとり。
狩野モデル | software-engineering, requirements | 品質要素を当たり前品質・一元的品質・魅力的品質などに分類し、顧客満足との関係を整理するモデル。
エンティティ | software-engineering, design | 業務上、識別して管理する必要のあるモノや概念。
ロバストネス分析 | software-engineering, design | ユースケースを Boundary・Control・Entity の3種に分解し、設計の抜けを洗い出す手法。
シーケンス図 | software-engineering, uml | オブジェクト間のメッセージのやりとりを時系列で表す UML 図。
