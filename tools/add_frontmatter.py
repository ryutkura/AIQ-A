# -*- coding: utf-8 -*-
"""
全ノートに frontmatter（Obsidian プロパティ）を付与する。

frontmatter が無いと、Obsidian の Properties / Bases / 検索での絞り込みが
一切効きません。「第二の脳」として再訪する仕組みの土台になります。

付与する項目:
    type    : qa | concept | troubleshoot | moc | system
    tags    : フォルダ構成から自動導出
    created : git 履歴の初回コミット日（無ければファイル作成日）
    updated : git 履歴の最終コミット日（無ければ更新日）
    status  : seed（育っていないノートを炙り出すため。育ったら evergreen に）

既に frontmatter があるファイルは触りません。

使い方:
    python tools/add_frontmatter.py            # プレビュー
    python tools/add_frontmatter.py --write    # 付与
"""

import argparse
import datetime
import importlib.util
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location("lk", TOOLS / "link_keywords.py")
lk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lk)

# ノートではなくシステム文書として扱うファイル
SYSTEM_FILES = {"README.md", "AI_INSTRUCTIONS.md", "CLAUDE.md", "MEMORY.md"}

# フォルダ名 → タグ名の例外指定
TAG_OVERRIDE = {
    "General": None,      # 汎用フォルダはタグにしない
    "CSharp": "csharp",
    "C": "c",
}


def folder_to_tag(name):
    if name in TAG_OVERRIDE:
        return TAG_OVERRIDE[name]
    s = name.replace("_", "-")
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", s)
    return s.lower()


def note_tags(rel_path):
    tags = []
    for part in rel_path.parts[:-1]:
        t = folder_to_tag(part)
        if t and t not in tags:
            tags.append(t)
    return tags


def note_type(rel_path):
    if rel_path.name in SYSTEM_FILES:
        return "system"
    top = rel_path.parts[0] if len(rel_path.parts) > 1 else ""
    return {"concepts": "concept", "troubleshooting": "troubleshoot", "moc": "moc"}.get(
        top, "qa"
    )


def git_dates():
    """1回の git log で「パス → (初回, 最終)コミット日」を作る。"""
    try:
        out = subprocess.run(
            ["git", "log", "--reverse", "--date=short",
             "--format=__C__%ad", "--name-only"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout
    except Exception:
        return {}

    dates = {}
    current = None
    for line in out.splitlines():
        if line.startswith("__C__"):
            current = line[5:].strip()
        elif line.strip() and current:
            path = line.strip()
            if path in dates:
                dates[path] = (dates[path][0], current)
            else:
                dates[path] = (current, current)
    return dates


def build(rel_path, dates):
    key = rel_path.as_posix()
    if key in dates:
        created, updated = dates[key]
    else:
        st = (ROOT / rel_path).stat()
        created = datetime.date.fromtimestamp(st.st_ctime).isoformat()
        updated = datetime.date.fromtimestamp(st.st_mtime).isoformat()

    t = note_type(rel_path)
    tags = note_tags(rel_path)

    lines = ["---", f"type: {t}"]
    if tags:
        lines.append(f"tags: [{', '.join(tags)}]")
    lines += [f"created: {created}", f"updated: {updated}"]
    if t not in ("system", "moc"):
        lines.append("status: seed")
    lines += ["---", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="frontmatter 付与")
    ap.add_argument("--write", action="store_true", help="実際に書き込む")
    args = ap.parse_args()

    dates = git_dates()
    targets, skipped = [], 0

    for fp in lk.collect_files():
        text = fp.read_text(encoding="utf-8")
        if text.lstrip().startswith("---"):
            skipped += 1
            continue
        rel = fp.relative_to(ROOT)
        targets.append((fp, rel, build(rel, dates), text))

    print("=" * 62)
    print(" frontmatter 付与")
    print("=" * 62)
    print(f"  対象           : {len(targets)}")
    print(f"  既にあるためskip: {skipped}")
    print("-" * 62)

    for fp, rel, fm, text in targets:
        head = " / ".join(x for x in fm.split("\n")[1:-2])
        print(f"  {lk._pad(str(rel), 52)}")
        print(f"      {head}")
        if args.write:
            fp.write_text(fm + text.lstrip("﻿"), encoding="utf-8")

    print("=" * 62)
    if args.write:
        print(f"  {len(targets)} 件に付与しました。")
    elif targets:
        print("※ まだ書き込んでいません。--write を付けると付与されます。")


if __name__ == "__main__":
    main()
