import os
import re
import glob

def main():
    # ディレクトリ以下のすべての .md ファイルを取得
    # toolsフォルダなど、特定フォルダを除外することも可能ですが今回は全体を対象とします。
    directory = "C:/Users/ryutk/デスクトップ/AIQandA"
    md_files = glob.glob(os.path.join(directory, '**/*.md'), recursive=True)

    # 重要なキーワードのリスト (文字数の多い順にソートして、部分一致の誤爆を防ぐ)
    keywords = [
        # --- 既存のキーワード ---
        "HTTPリクエスト", "ロバストネス分析", "段階的提案", "問題領域", "解決領域", "エンティティ", 
        "要件定義", "ユースケース", "狩野モデル", "ヒアリング", "クリップボード",
        "参照渡し", "参照外し", "値渡し", "ポインタ", "アドレス", 
        "C言語", "Python", "Java", "C#",
        "ルーティング", "コントローラー", "Controller", 
        "ビュー", "View", "モデル", "Model", "データベース", "Database", "DAO", "MVC",
        "GET", "POST","MACアドレス", "IPアドレス", "URL", "URI", "DNS", "TCP/IP", "HTTP", "HTTPS",
        "AI", "人工知能", "機械学習", "ディープラーニング", "自然言語処理", "NLP", "ニューラルネットワーク", "CNN", "RNN", "Transformer", "BERT", "GPT",
        
        # --- 追加キーワード (プログラミング・言語・概念) ---
        "オブジェクト指向", "クラス", "インスタンス", "メソッド", "関数", "変数", "型", "スレッド", "非同期処理", "同期処理",
        "アルゴリズム", "データ構造", "配列", "リスト", "辞書", "ハッシュ", "例外処理", "ポリモーフィズム", "カプセル化", "継承",
        "コンパイル", "インタプリタ", "ビルド", "デバッグ", "デプロイ", "API", "JSON", "XML", "HTML", "CSS", "JavaScript",
        "TypeScript", "React", "Vue", "Angular", "Node.js", "SQL", "NoSQL", "Git", "GitHub", "GitLab",
        "C++", "Ruby", "PHP", "Go", "Rust", "Swift", "Kotlin", "シェルスクリプト",
        
        # --- 追加キーワード (Linux・インフラ・ネットワーク) ---
        "プロセス管理", "SSH", "公開鍵", "秘密鍵", "鍵認証", "ユーザー権限", "Raspberry Pi", "IoT", 
        "Docker", "Kubernetes", "コンテナ", "仮想化", "AWS", "GCP", "Azure", 
        "Linux", "Windows", "macOS", "OS", "カーネル", "シェル", "bash", "zsh", "コマンドライン", 
        "REST", "GraphQL", "WebSocket", "ファイアウォール", "ルーター", "スイッチ", "VLAN", "VPN",
        
        # --- 追加キーワード (機械学習・AI・データサイエンス) ---
        "教師あり学習", "教師なし学習", "強化学習", "深層学習", "メタヒューリスティクス", "遺伝的アルゴリズム", "焼きなまし法", 
        "コンピュータビジョン", "画像認識", "音声認識", "LLM", "大規模言語モデル", "生成AI", "プロンプトエンジニアリング", 
        "TensorFlow", "PyTorch", "scikit-learn", "pandas", "NumPy", "データサイエンス", 
        "過学習", "交差検証", "勾配降下法", "誤差逆伝播法",
        
        # --- 追加キーワード (数学・理論) ---
        "微積分", "微分", "積分", "複素解析", "グラフ理論", "情報理論", "線形代数", "行列", "ベクトル", "テンソル",
        "固有値", "固有ベクトル", "論理回路", "統計学", "確率", "分散", "標準偏差", "正規分布", "ガウス分布", "ポアソン分布", 
        "ベイズ推論", "最適化",
        
        # --- 追加キーワード (ソフトウェア工学・設計・テスト) ---
        "UML", "クラス図", "シーケンス図", "状態遷移図", "ユースケース図", "アクティビティ図", 
        "設計", "アーキテクチャ", "ソフトウェアアーキテクチャ", "アジャイル", "スクラム", "ウォーターフォール", 
        "CI/CD", "テスト", "単体テスト", "結合テスト", "システムテスト", "E2Eテスト", 
        "リファクタリング", "デザインパターン", "GoF", "SOLID原則", "DRY原則", "KISS原則", "YAGNI原則", 
        "マイクロサービス", "モノリス", "DDD", "ドメイン駆動設計", "TDD", "テスト駆動開発"
    ]
    # ソート（長いものから置換するため）
    keywords = sorted(keywords, key=len, reverse=True)

    for filepath in md_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            for keyword in keywords:
                # 既に [[keyword]] になっている場合や、Markdownのリンクの中身を避ける正規表現
                pattern = r'(?<!\[)(?<!\[\[)(' + re.escape(keyword) + r')(?!\]\])(?!\])'
                content = re.sub(pattern, r'[[\1]]', content)

            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated: {filepath}")
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    print("Keyword linking process finished.")

if __name__ == '__main__':
    main()
