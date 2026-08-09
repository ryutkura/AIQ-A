# -*- coding: utf-8 -*-
"""
MOC（Map of Content）と ダッシュボード を生成する。

MOC = 領域ごとの「入口ノート」。グラフに階層構造を与え、
「どこから読み始めればいいか」を作ります。

各 MOC が載せる概念は手で決め打ちせず、
**その領域のノートが実際に参照している concepts** から自動導出します。
そのためノートが増えれば MOC も勝手に育ちます。

生成物は再生成前提です（手で書き足した内容は上書きされます）。

使い方:
    python tools/make_moc.py            # プレビュー
    python tools/make_moc.py --write    # 生成
"""

import argparse
import collections
import datetime
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
MOC = ROOT / "moc"
CONCEPTS = ROOT / "concepts"

_spec = importlib.util.spec_from_file_location("lk", TOOLS / "link_keywords.py")
lk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lk)

# トップフォルダ → MOC の表示名
DOMAINS = {
    "math": "数学",
    "programming": "プログラミング",
    "machine_learning": "機械学習",
    "infrastructure": "インフラ",
    "linux": "Linux",
    "software_engineering": "ソフトウェア工学",
    "troubleshooting": "沼ログ",
}

FM = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def read_meta(path):
    m = FM.match(path.read_text(encoding="utf-8"))
    if not m:
        return {}
    meta = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta


def concept_names():
    return {p.stem for p in CONCEPTS.glob("*.md")} if CONCEPTS.exists() else set()


def scan():
    """ノートごとに (相対パス, 参照している concepts) を集める。"""
    kw = set(lk.load_keywords())
    concepts = concept_names()
    notes = []
    for fp in lk.collect_files():
        rel = fp.relative_to(ROOT)
        if rel.parts[0] in ("concepts", "moc") or len(rel.parts) == 1:
            continue
        refs = set()
        for line, kind in lk.iter_lines_with_context(fp.read_text(encoding="utf-8")):
            if kind != "text":
                continue
            for m in lk.WIKILINK.finditer(lk.INLINE_CODE.sub("", line)):
                t = lk.link_target(m.group(0), kw)
                if t in concepts:
                    refs.add(t)
        notes.append((rel, refs))
    return notes


def link_to(rel):
    """同名ファイルが複数あるためパス付きリンクにする。"""
    return f"[[{rel.with_suffix('').as_posix()}|{rel.stem}]]"


STATUS_MARK = {"solved": "解決", "workaround": "回避", "unsolved": "未解決"}


def build_troubleshoot_moc(mine, today):
    """沼ログはエラー文で引けることが命なので、通常のMOCとは別の形にする。"""
    lines = [
        "---",
        "type: moc",
        "tags: [troubleshooting]",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        "# 沼ログ",
        "",
        f"{len(mine)} 件",
        "",
        "> エラー文で引きたい時は、このページではなく **全文検索（Ctrl+Shift+F）** に",
        "> エラーメッセージをそのまま貼るのが速い。",
        "",
        "| 日付 | ノート | エラー | 状態 |",
        "| --- | --- | --- | --- |",
    ]
    rows = []
    for rel, _ in mine:
        meta = read_meta(ROOT / rel)
        rows.append((
            meta.get("created", ""),
            link_to(rel),
            (meta.get("error", "") or "—")[:50],
            STATUS_MARK.get(meta.get("status", ""), meta.get("status", "—")),
        ))
    for row in sorted(rows, reverse=True):
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def build_moc(domain, label, notes, today):
    mine = [(r, refs) for r, refs in notes if r.parts[0] == domain]
    if not mine:
        return None

    if domain == "troubleshooting":
        return build_troubleshoot_moc(mine, today)

    freq = collections.Counter()
    for _, refs in mine:
        for c in refs:
            freq[c] += 1

    lines = [
        "---",
        "type: moc",
        f"tags: [{domain.replace('_', '-')}]",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        f"# {label}",
        "",
        f"ノート {len(mine)} 件 / 参照している概念 {len(freq)} 件",
        "",
        "## 主要な概念",
        "",
    ]
    if freq:
        lines.append(
            " · ".join(f"[[{c}]]" for c, _ in freq.most_common())
        )
    else:
        lines.append("*まだ concepts への参照がありません。*")
    lines += ["", "## ノート", ""]

    by_sub = collections.defaultdict(list)
    for rel, _ in sorted(mine):
        sub = "/".join(rel.parts[1:-1]) or "（直下）"
        by_sub[sub].append(rel)

    for sub in sorted(by_sub):
        lines.append(f"### {sub}")
        lines.append("")
        for rel in by_sub[sub]:
            lines.append(f"- {link_to(rel)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_home(notes, today, made):
    total_concepts = len(concept_names())
    lines = [
        "---",
        "type: moc",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        "# ホーム",
        "",
        f"記事ノート {len(notes)} 件 / 概念 {total_concepts} 件",
        "",
        "## 領域",
        "",
    ]
    for domain, label in DOMAINS.items():
        if domain in made:
            n = sum(1 for r, _ in notes if r.parts[0] == domain)
            lines.append(f"- [[moc/{label}|{label}]] — {n} 件")
    lines += [
        "",
        "## ダッシュボード",
        "",
        "### まだ育っていないノート（status: seed）",
        "",
        "```query",
        '["status":"seed"]',
        "```",
        "",
        "### 最近さわったノート",
        "",
        "```query",
        "path:/ -path:concepts -path:moc",
        "```",
        "",
        "### 未解決の沼",
        "",
        "```query",
        'path:troubleshooting ["status":"unsolved"]',
        "```",
        "",
        "### 未整理（inbox）",
        "",
        "```query",
        "path:inbox",
        "```",
        "",
        "---",
        "",
        "> [!note] メンテナンス",
        "> このノートと `moc/` 配下は `python tools/make_moc.py --write` で再生成されます。",
        "> 手で書き足した内容は上書きされるので注意してください。",
    ]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="MOC / ダッシュボード生成")
    ap.add_argument("--write", action="store_true", help="実際に書き込む")
    args = ap.parse_args()

    today = datetime.date.today().isoformat()
    notes = scan()
    made = {}

    for domain, label in DOMAINS.items():
        body = build_moc(domain, label, notes, today)
        if body:
            made[domain] = (MOC / f"{label}.md", body)

    home = build_home(notes, today, made)

    print("=" * 62)
    print(" MOC / ダッシュボード生成")
    print("=" * 62)
    for domain, (path, body) in made.items():
        n = sum(1 for r, _ in notes if r.parts[0] == domain)
        print(f"  moc/{lk._pad(path.stem + '.md', 24)} ノート {n:>2} 件")
        if args.write:
            MOC.mkdir(exist_ok=True)
            path.write_text(body, encoding="utf-8")
    print(f"  moc/ホーム.md            （ダッシュボード）")
    if args.write:
        MOC.mkdir(exist_ok=True)
        (MOC / "ホーム.md").write_text(home, encoding="utf-8")
    print("=" * 62)
    if args.write:
        print(f"  {len(made) + 1} 件を生成しました。")
    else:
        print("※ まだ書き込んでいません。--write を付けると生成されます。")


if __name__ == "__main__":
    main()
