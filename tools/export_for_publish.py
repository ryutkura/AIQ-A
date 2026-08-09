# -*- coding: utf-8 -*-
"""
Vault のノートを Qiita / Zenn に投稿できる体裁に変換して publish/drafts/ に出す。

なぜ変換が必要か:
  * Qiita も Zenn も Obsidian のリンク記法（二重角括弧）を**レンダリングしません**。
    そのまま貼ると本文に記号がむき出しで出ます。
  * frontmatter の仕様が両者でまったく違います。
  * 画像の扱いが違います（後述の警告を参照）。

正本は Vault 側です。publish/ は書き出し先と割り切ってください。
（同じ内容が2箇所にあるとグラフが濁るため、publish/ はリンク走査から除外済み）

使い方:
    python tools/export_for_publish.py math/LinearAlgebra/LU_decomposition.md
    python tools/export_for_publish.py <path> --target qiita
    python tools/export_for_publish.py <path> --write
"""

import argparse
import datetime
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
OUT_DIR = ROOT / "publish" / "drafts"

_spec = importlib.util.spec_from_file_location("lk", TOOLS / "link_keywords.py")
lk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lk)

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def parse_frontmatter(text):
    m = FRONTMATTER.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).split("\n"):
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        meta[k.strip()] = v
    return meta, text[m.end():]


def strip_wikilinks(text):
    """[[表示名|リンク先]] → 表示名 / [[語]] → 語（コード部分は触らない）"""
    n = 0

    def repl(m):
        nonlocal n
        n += 1
        inner = m.group(0)[2:-2]
        # 別名があれば別名（表示文字列）を優先
        return inner.split("|")[-1].split("#")[0].strip() if "|" in inner else inner.split("#")[0]

    out = []
    for line, kind in lk.iter_lines_with_context(text):
        if kind == "text":
            line = lk.WIKILINK.sub(repl, line)
        out.append(line)
    return "\n".join(out), n


def title_of(text, fallback):
    for line in text.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def to_topics(tags, limit=5):
    """Zenn の topics は英数字のみ。ハイフン等を落とす。"""
    out = []
    for t in tags:
        s = re.sub(r"[^0-9a-zA-Z぀-ヿ一-鿿]", "", str(t))
        if s and s not in out:
            out.append(s)
    return out[:limit]


def build_zenn(title, tags, body):
    topics = to_topics(tags)
    fm = [
        "---",
        f'title: "{title}"',
        'emoji: "📝"',
        'type: "tech"      # tech（技術記事） か idea（アイデア）',
        f"topics: [{', '.join(f'{chr(34)}{t}{chr(34)}' for t in topics)}]",
        "published: false  # 公開する時に true にする",
        "---",
        "",
    ]
    return "\n".join(fm) + body


def build_qiita(title, tags, body):
    fm = ["---", f'title: "{title}"', "tags:"]
    for t in tags[:5] or ["未設定"]:
        fm.append(f"  - {t}")
    fm += [
        "private: true     # 限定共有。公開する時に false にする",
        'updated_at: ""',
        "id: null",
        "organization_url_name: null",
        "slide: false",
        "ignorePublish: false",
        "---",
        "",
    ]
    return "\n".join(fm) + body


def main():
    ap = argparse.ArgumentParser(description="Qiita / Zenn 用に書き出す")
    ap.add_argument("path", help="Vault 内のノートのパス")
    ap.add_argument("--target", choices=["zenn", "qiita"], default="zenn")
    ap.add_argument("--write", action="store_true", help="実際に書き出す")
    args = ap.parse_args()

    src = (ROOT / args.path).resolve()
    if not src.exists():
        sys.exit(f"ファイルがありません: {args.path}")

    raw = src.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    body, n_links = strip_wikilinks(body)

    title = title_of(body, src.stem)
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    images = IMAGE.findall(body)

    out = (build_zenn if args.target == "zenn" else build_qiita)(title, tags, body)
    dest = OUT_DIR / f"{args.target}_{src.stem}.md"

    print("=" * 62)
    print(f" {args.target.upper()} 用に書き出し")
    print("=" * 62)
    print(f"  元ノート    : {args.path}")
    print(f"  タイトル    : {title}")
    print(f"  タグ        : {tags}")
    print(f"  リンク解除  : {n_links} 件（二重角括弧を除去）")
    print(f"  出力先      : publish/drafts/{dest.name}")

    if images:
        print("-" * 62)
        print(f"  ⚠ 画像 {len(images)} 件は手作業が必要です")
        for alt, path in images:
            print(f"      {path}")
        if args.target == "qiita":
            print("      → Qiita はローカル画像を使えません。")
            print("        Qiita のエディタに画像をアップロードし、発行されたURLに置き換えてください。")
        else:
            print("      → Zenn は zenn リポジトリの /images/ に置いたものを")
            print("        `/images/ファイル名` で参照します。画像をコピーしてパスを直してください。")

    print("=" * 62)
    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        dest.write_text(out, encoding="utf-8")
        print(f"  書き出しました。編集して各サービスの CLI で投稿してください。")
    else:
        print("※ まだ書き出していません。--write を付けると出力されます。")


if __name__ == "__main__":
    main()
