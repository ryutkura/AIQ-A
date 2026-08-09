# -*- coding: utf-8 -*-
"""
concepts/ スタブ生成ツール

Obsidian は [[X]] を「X.md というファイル名」で解決します。
参照先のノートが無い限り、リンクは幽霊ノードのままでノート同士は繋がりません。
このツールは「複数のノートから参照されている語」だけを実ノート化し、
グラフに本物のハブを作ります。

方針:
  * 2ファイル以上から参照されている語だけを作る
    （1ファイルからしか参照されていない語は、作っても孤立ノードが増えるだけ）
  * 中身は定義1〜2行の最小スタブ。育てるのは必要になった時
  * 既存ファイルは絶対に上書きしない

使い方:
    python tools/make_concepts.py                  # プレビュー
    python tools/make_concepts.py --write          # 生成
    python tools/make_concepts.py --min-files 3    # しきい値を変える
"""

import argparse
import datetime
import importlib.util
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
CONCEPTS = ROOT / "concepts"
DEFS_FILE = TOOLS / "concept_defs.md"

# link_keywords.py の解析ロジックを再利用する
_spec = importlib.util.spec_from_file_location("lk", TOOLS / "link_keywords.py")
lk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lk)

INVALID_FILENAME = re.compile(r'[\\/:*?"<>|]')


def load_defs():
    """語 -> (tags, 定義) の辞書を返す。"""
    defs = {}
    if not DEFS_FILE.exists():
        return defs
    for raw in DEFS_FILE.read_text(encoding="utf-8").splitlines():
        if raw.lstrip().startswith("#") or not raw.strip():
            continue
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 3:
            continue
        word, tags, body = parts[0], parts[1], "|".join(parts[2:]).strip()
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        defs[word] = (tag_list, body)
    return defs


def count_references(keywords):
    """concepts/ を除いた実ノートで、各リンクが何ファイルから参照されているか数える。"""
    counter = Counter()
    for fp in lk.collect_files():
        if fp.is_relative_to(CONCEPTS):
            continue
        seen = set()
        for line, kind in lk.iter_lines_with_context(fp.read_text(encoding="utf-8")):
            if kind != "text":
                continue
            plain = lk.INLINE_CODE.sub("", line)
            for m in lk.WIKILINK.finditer(plain):
                name = lk.link_target(m.group(0), keywords)
                if name in keywords:
                    seen.add(name)
        for name in seen:
            counter[name] += 1
    return counter


def render(word, tags, body, today):
    tag_str = ", ".join(tags)
    return (
        "---\n"
        "type: concept\n"
        f"tags: [{tag_str}]\n"
        "status: seed\n"
        f"created: {today}\n"
        f"updated: {today}\n"
        "---\n\n"
        f"# {word}\n\n"
        f"{body}\n"
    )


def main():
    ap = argparse.ArgumentParser(description="concepts/ スタブ生成")
    ap.add_argument("--min-files", type=int, default=2, help="何ファイルから参照されていれば作るか（既定2）")
    ap.add_argument("--write", action="store_true", help="実際にファイルを生成する")
    args = ap.parse_args()

    keywords = set(lk.load_keywords())
    defs = load_defs()
    counts = count_references(keywords)

    targets = sorted(
        [(n, c) for n, c in counts.items() if c >= args.min_files],
        key=lambda x: (-x[1], x[0]),
    )

    today = datetime.date.today().isoformat()
    create, skip_exists, no_def, bad_name = [], [], [], []

    for word, c in targets:
        if INVALID_FILENAME.search(word):
            bad_name.append((word, c))
            continue
        path = CONCEPTS / f"{word}.md"
        if path.exists():
            skip_exists.append((word, c))
            continue
        if word not in defs:
            no_def.append((word, c))
            continue
        create.append((word, c, path, defs[word]))

    print("=" * 62)
    print(f" concepts/ 生成  （{args.min_files}ファイル以上から参照されている語が対象）")
    print("=" * 62)
    print(f"  対象語        : {len(targets)}")
    print(f"  新規作成      : {len(create)}")
    print(f"  既存のためskip: {len(skip_exists)}")
    print(f"  定義が無くskip: {len(no_def)}")
    if bad_name:
        print(f"  ファイル名不可: {len(bad_name)}  {[w for w, _ in bad_name]}")
    print("-" * 62)

    for word, c, path, (tags, body) in create:
        print(f"  + {lk._pad(word, 18)} {c:>2}ファイルから参照   [{', '.join(tags)}]")
        if args.write:
            CONCEPTS.mkdir(exist_ok=True)
            path.write_text(render(word, tags, body, today), encoding="utf-8")

    if no_def:
        print("-" * 62)
        print("  ↓ 参照されているが tools/concept_defs.md に定義が無い語")
        for word, c in no_def:
            print(f"  ? {lk._pad(word, 18)} {c:>2}ファイルから参照")

    print("=" * 62)
    if args.write:
        print(f"  {len(create)} 件を concepts/ に生成しました。")
    elif create:
        print("※ まだ生成していません。--write を付けると作成されます。")


if __name__ == "__main__":
    main()
