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
        "HTTPリクエスト", "ロバストネス分析", "段階的提案", "問題領域", "解決領域", "エンティティ", 
        "要件定義", "ユースケース", "狩野モデル", "ヒアリング", "クリップボード",
        "参照渡し", "参照外し", "値渡し", "ポインタ", "アドレス", 
        "C言語", "Python", "Java", "C#",
        "ルーティング", "コントローラー", "Controller", 
        "ビュー", "View", "モデル", "Model", "データベース", "Database", "DAO", "MVC",
        "GET", "POST","MACアドレス", "IPアドレス", "URL", "URI", "DNS", "TCP/IP", "HTTP", "HTTPS",
        "AI", "人工知能", "機械学習", "ディープラーニング", "自然言語処理", "NLP", "ニューラルネットワーク", "CNN", "RNN", "Transformer", "BERT", "GPT"
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
