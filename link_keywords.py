import os
import re
import glob

# ディレクトリ以下のすべての .md ファイルを取得
directory = "C:/Users/ryutk/デスクトップ/AIQandA"
md_files = glob.glob(os.path.join(directory, '**/*.md'), recursive=True)

# 重要なキーワードのリスト (文字数の多い順にソートして、部分一致の誤爆を防ぐ)
keywords = [
    "HTTPリクエスト", "ロバストネス分析", "段階的提案", "問題領域", "解決領域", "エンティティ", 
    "要件定義", "ユースケース", "狩野モデル", "ヒアリング",
    "参照渡し", "参照外し", "値渡し", "ポインタ", "アドレス", 
    "C言語", "Python", "Java", "C#",
    "ルーティング", "コントローラー", "Controller", 
    "ビュー", "View", "モデル", "Model", "データベース", "Database", "DAO", "MVC",
    "GET", "POST"
]
# ソート（長いものから置換するため）
keywords = sorted(keywords, key=len, reverse=True)

for filepath in md_files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        for keyword in keywords:
            # すでに [[keyword]] になっている場合や、Markdownのリンク [keyword](...) の中身、
            # 画像リンク ![...](...) の中身などを避けるための正規表現
            # 完璧なパースは難しいが、単純なケースに対応
            
            # 正規表現で置換
            # 1. 既に [[...]] で囲まれている場合は除外
            # 2. Markdownのリンクなどの中にある場合は一旦無視するのが難しいので、
            #    単純に (?<!\[\[) と (?!\]\]) で挟まれていないものを置換する。
            
            # pythonのreは可変長の戻り読みをサポートしないので、単純な方法を使用
            # 手順：
            # A. まず、特定の一時文字列に退避させるのは複雑。
            # B. (?<!\[\[)(?<!\[)キーワード(?!\]\])(?!\]) で置換する。
            # ただ、これだと [keyword] という既存の括弧があった場合に対応できない。
            # 今回は「一切の内容変更は認めない」ので安全側に倒す。
            
            pattern = r'(?<!\[)(?<!\[\[)(' + re.escape(keyword) + r')(?!\]\])(?!\])'
            content = re.sub(pattern, r'[[\1]]', content)

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

print("Done.")
