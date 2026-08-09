# -*- coding: utf-8 -*-
"""
Obsidian キーワードリンク管理ツール（安全版）

旧版の問題を修正したもの:
  1. コードブロック / インラインコード / frontmatter を保護する
  2. 既存の [[...]] を再置換しない（[[P[[OS]]T]] のような破壊を防ぐ）
  3. ASCII キーワードに単語境界を付ける（Goal → [[Go]]al を防ぐ）
  4. 1ファイル1キーワードにつき初出のみリンク化（可読性）
  5. 既定では書き込まない。--write を明示した時だけファイルを更新する

使い方:
    python tools/link_keywords.py                     # 現状診断（書き込みなし）
    python tools/link_keywords.py --repair            # 修復のプレビュー
    python tools/link_keywords.py --repair   --write  # 修復を実行
    python tools/link_keywords.py --link     --write  # 新規リンク付与を実行
    python tools/link_keywords.py --prune    --write  # 降格した語のリンクを解除
    python tools/link_keywords.py --headings --write  # 見出し行のリンクを解除
"""

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYWORD_FILE = Path(__file__).resolve().parent / "keywords.txt"

# 走査から除外: 生成物（moc）・データ置き場（tools）・投稿用（publish）は
# 他のツールに書き換えさせない
EXCLUDE_DIRS = {
    ".git", ".obsidian", "node_modules", "__pycache__",
    "publish", "templates", "tools", "moc",
}

SENTINEL = "\x00"


# ==============================================================
# キーワード読み込み
# ==============================================================
def load_keywords():
    if not KEYWORD_FILE.exists():
        sys.exit(f"キーワード定義が見つかりません: {KEYWORD_FILE}")
    words = []
    for line in KEYWORD_FILE.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#"):
            continue  # コメント行
        # 行末コメントのみ除去（C# のような語を壊さないよう空白を必須にする）
        line = re.sub(r"\s+#.*$", "", line).strip()
        if line:
            words.append(line)
    # 長い語から処理して部分一致の誤爆を防ぐ
    return sorted(set(words), key=len, reverse=True)


def keyword_pattern(kw):
    """ASCII 英数で始まる/終わる語には単語境界を付ける。"""
    left = r"(?<![A-Za-z0-9_])" if (kw[0].isascii() and kw[0].isalnum()) else ""
    right = r"(?![A-Za-z0-9_])" if (kw[-1].isascii() and kw[-1].isalnum()) else ""
    return re.compile(left + re.escape(kw) + right)


# ==============================================================
# 保護（マスク）
# ==============================================================
INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)*?\1")
WIKILINK = re.compile(r"\[\[[^\[\]]*\]\]")
MD_LINK = re.compile(r"!?\[[^\]\n]*\]\([^)\n]*\)")
BARE_URL = re.compile(r"https?://\S+")
HTML_TAG = re.compile(r"</?[A-Za-z][^>\n]*>")


def is_system_doc(text):
    """frontmatter が type: system のファイル（README等）はリンク対象外。

    取扱説明書がグラフのノードとして概念に繋がると、
    知識の関係ではなく「文書がどの単語を含むか」が可視化されてしまう。
    """
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    return bool(m and re.search(r"^type:\s*system\s*$", m.group(1), re.M))


def link_target(wikilink, known=()):
    """[[表示名|リンク先#見出し]] からリンク先ノート名を取り出す。

    C# のように語自体に # を含むキーワードを壊さないため、
    既知の語と完全一致する場合はアンカー分割を行わない。
    """
    inner = wikilink[2:-2].split("|")[0].strip()
    if inner in known:
        return inner
    return inner.split("#")[0].strip()


class Masker:
    """保護したい部分をトークンに退避し、あとで復元する。"""

    def __init__(self):
        self.store = []

    def _sub(self, m):
        self.store.append(m.group(0))
        return f"{SENTINEL}{len(self.store) - 1}{SENTINEL}"

    def mask(self, text):
        # 順序が重要: コード → 既存リンク → Markdownリンク → URL → HTMLタグ
        for pat in (INLINE_CODE, WIKILINK, MD_LINK, BARE_URL, HTML_TAG):
            text = pat.sub(self._sub, text)
        return text

    def unmask(self, text):
        def restore(m):
            return self.store[int(m.group(1))]

        pat = re.compile(f"{SENTINEL}(\\d+){SENTINEL}")
        # 入れ子復元のため変化がなくなるまで繰り返す
        for _ in range(10):
            new = pat.sub(restore, text)
            if new == text:
                break
            text = new
        return text


def iter_lines_with_context(text):
    """(行, 種別) を返す。種別: 'frontmatter' | 'fence' | 'code' | 'text'"""
    lines = text.split("\n")
    in_fm = False
    in_fence = False
    fence_marker = None

    if lines and lines[0].strip() == "---":
        in_fm = True
        yield lines[0], "frontmatter"
        lines = lines[1:]
        offset = 1
    else:
        offset = 0

    for line in lines:
        if in_fm:
            yield line, "frontmatter"
            if line.strip() == "---":
                in_fm = False
            continue

        m = re.match(r"^\s*(```+|~~~+)", line)
        if m:
            if not in_fence:
                in_fence = True
                fence_marker = m.group(1)[:3]
                yield line, "fence"
                continue
            elif m.group(1)[:3] == fence_marker:
                in_fence = False
                fence_marker = None
                yield line, "fence"
                continue

        yield line, ("code" if in_fence else "text")


# ==============================================================
# 修復
# ==============================================================
NESTED = re.compile(r"\[\[([^\[\]]*)\[\[([^\[\]]+)\]\]([^\[\]]*)\]\]")


def unnest(text):
    """[[P[[OS]]T]] → [[POST]]"""
    n = 0
    for _ in range(10):
        text, k = NESTED.subn(r"[[\1\2\3]]", text)
        n += k
        if k == 0:
            break
    return text, n


def strip_links(text):
    """[[X]] → X（コード文脈でリンク記法を剥がす）"""
    return WIKILINK.sub(lambda m: m.group(0)[2:-2], text)


# 単語の途中に食い込んだリンク: My[[SQL]] / [[Go]]al / [[View]]Factory
BOUNDARY_BAD = re.compile(
    r"(?:(?<=[A-Za-z0-9_])\[\[([A-Za-z0-9_][^\[\]]*)\]\])"
    r"|(?:\[\[([^\[\]]*[A-Za-z0-9_])\]\](?=[A-Za-z0-9_]))"
)


def fix_boundaries(text):
    """ASCII 語が単語の途中でリンク化されているものを解除する。"""
    n = 0
    for _ in range(5):
        text, k = BOUNDARY_BAD.subn(lambda m: m.group(1) or m.group(2), text)
        n += k
        if k == 0:
            break
    return text, n


def repair_file(text):
    """コード文脈のリンクを剥がし、入れ子リンクを直す。"""
    stats = {"nested": 0, "boundary": 0, "code": 0, "fence": 0, "inline": 0}

    text, stats["nested"] = unnest(text)

    out = []
    for line, kind in iter_lines_with_context(text):
        if kind == "text":
            line, k = fix_boundaries(line)
            stats["boundary"] += k
        if kind in ("code", "fence", "frontmatter"):
            n = len(WIKILINK.findall(line))
            if n:
                stats["code" if kind == "code" else ("fence" if kind == "fence" else "code")] += n
                line = strip_links(line)
        else:
            def fix_inline(m):
                span = m.group(0)
                n = len(WIKILINK.findall(span))
                if n:
                    stats["inline"] += n
                    return strip_links(span)
                return span

            line = INLINE_CODE.sub(fix_inline, line)
        out.append(line)

    return "\n".join(out), stats


# ==============================================================
# リンク付与
# ==============================================================
def link_file(text, keywords, self_name, first_only=True):
    added = {}
    out = []

    # すでにリンク済みの語を初出扱いにする（実行のたびに1件ずつ増えるのを防ぐ）
    kwset = set(keywords)
    linked = {link_target(m.group(0), kwset) for m in WIKILINK.finditer(text)}

    for line, kind in iter_lines_with_context(text):
        if kind != "text" or line.lstrip().startswith("#"):
            out.append(line)
            continue

        masker = Masker()
        masked = masker.mask(line)

        for kw in keywords:
            if kw == self_name:
                continue
            if first_only and kw in linked:
                continue
            pat = keyword_pattern(kw)
            if not pat.search(masked):
                continue
            count = 1 if first_only else 0
            masked, n = pat.subn(lambda m: f"[[{m.group(0)}]]", masked, count=count)
            if n:
                added[kw] = added.get(kw, 0) + n
                linked.add(kw)
                # 付けたリンクを即マスクして再置換を防ぐ
                masked = WIKILINK.sub(masker._sub, masked)

        out.append(masker.unmask(masked))

    return "\n".join(out), added


def strip_heading_links(text):
    """見出し行のリンクを解除する（目次・アウトラインの可読性のため）。"""
    n = 0
    out = []
    for line, kind in iter_lines_with_context(text):
        if kind == "text" and line.lstrip().startswith("#"):
            k = len(WIKILINK.findall(line))
            if k:
                n += k
                line = strip_links(line)
        out.append(line)
    return "\n".join(out), n


def prune_file(text, keywords):
    """キーワード定義に無い語のリンクを解除する（降格の反映）。"""
    allowed = set(keywords)
    removed = {}

    def repl(m):
        inner = m.group(0)[2:-2]
        target = link_target(m.group(0), allowed)
        if target in allowed:
            return m.group(0)
        # concepts/ や実ノートとして存在するなら残す
        if list(ROOT.rglob(f"{target}.md")):
            return m.group(0)
        removed[target] = removed.get(target, 0) + 1
        return inner

    out = []
    for line, kind in iter_lines_with_context(text):
        out.append(WIKILINK.sub(repl, line) if kind == "text" else line)
    return "\n".join(out), removed


# ==============================================================
# 診断
# ==============================================================
def _pad(s, width):
    """全角文字を2幅として数えて左詰めする。"""
    import unicodedata

    w = sum(2 if unicodedata.east_asian_width(c) in "WFA" else 1 for c in s)
    return s + " " * max(0, width - w)


def diagnose(files, keywords):
    from collections import Counter

    link_files = Counter()   # リンク → 出現ファイル数
    total = Counter()
    ctx = Counter()
    nested = 0

    for fp in files:
        text = fp.read_text(encoding="utf-8")
        nested += len(NESTED.findall(text))
        seen = set()
        for line, kind in iter_lines_with_context(text):
            if kind in ("code", "fence"):
                ctx["コードブロック内"] += len(WIKILINK.findall(line))
                continue
            if kind == "frontmatter":
                continue
            for m in INLINE_CODE.finditer(line):
                ctx["インラインコード内"] += len(WIKILINK.findall(m.group(0)))
            plain = INLINE_CODE.sub("", line)
            if line.lstrip().startswith("#"):
                ctx["（うち見出し内）"] += len(WIKILINK.findall(plain))
            for m in WIKILINK.finditer(plain):
                name = m.group(0)[2:-2].split("|")[0]
                total[name] += 1
                seen.add(name)
        for name in seen:
            link_files[name] += 1

    names = set(total)
    resolved = {n for n in names if list(ROOT.rglob(f"{n}.md"))}

    print("=" * 62)
    print(" 現状診断")
    print("=" * 62)
    print(f"  ノート数                    : {len(files)}")
    print(f"  ユニークなリンク            : {len(names)}")
    print(f"  └ 実ノートに解決するもの   : {len(resolved)}")
    print(f"  └ 未解決（幽霊ノード）     : {len(names) - len(resolved)}")
    print()
    print("  【破損・汚染】")
    print(f"  {_pad('入れ子リンク [[P[[OS]]T]]', 26)}: {nested}")
    for k, v in ctx.items():
        print(f"  {_pad(k, 26)}: {v}")
    print()
    print("  【リンクが集中している語（出現ファイル数 上位10）】")
    for name, c in link_files.most_common(10):
        mark = "  ← concepts/ 作成 or 降格" if name not in resolved else ""
        print(f"    {_pad(name, 22)} {c:>3} ファイル / 計 {total[name]:>4} 回{mark}")
    print()
    print(f"  現在のキーワード定義: {len(keywords)} 語")
    print("=" * 62)


# ==============================================================
def collect_files():
    out = []
    for p in ROOT.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in p.relative_to(ROOT).parts):
            continue
        out.append(p)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(description="Obsidian キーワードリンク管理（安全版）")
    ap.add_argument("--repair", action="store_true", help="コード内リンクの除去と入れ子リンクの修復")
    ap.add_argument("--link", action="store_true", help="キーワードへのリンクを付与")
    ap.add_argument("--headings", action="store_true", help="見出し行のリンクを解除")
    ap.add_argument("--prune", action="store_true", help="キーワード定義に無いリンクを解除")
    ap.add_argument("--write", action="store_true", help="実際にファイルへ書き込む（既定はプレビュー）")
    ap.add_argument("--all-occurrences", action="store_true", help="初出のみでなく全出現をリンク化")
    args = ap.parse_args()

    keywords = load_keywords()
    files = collect_files()

    if not (args.repair or args.link or args.prune or args.headings):
        diagnose(files, keywords)
        print("\n次の一手:  python tools/link_keywords.py --repair        # 修復プレビュー")
        print("           python tools/link_keywords.py --repair --write # 修復実行")
        return

    totals = {"nested": 0, "boundary": 0, "code": 0, "fence": 0, "inline": 0}
    heading_total = 0
    added_total = 0
    pruned_total = 0
    changed = []

    for fp in files:
        original = fp.read_text(encoding="utf-8")
        text = original
        detail = []

        if args.repair:
            text, st = repair_file(text)
            for k in totals:
                totals[k] += st[k]
            if any(st.values()):
                detail.append(
                    "修復 " + " ".join(f"{k}={v}" for k, v in st.items() if v)
                )

        if args.headings:
            text, n = strip_heading_links(text)
            heading_total += n
            if n:
                detail.append(f"見出しリンク解除 {n}件")

        if args.prune:
            text, removed = prune_file(text, keywords)
            n = sum(removed.values())
            pruned_total += n
            if n:
                detail.append(f"解除 {n}件 ({', '.join(sorted(removed))[:60]})")

        if args.link and not is_system_doc(original):
            text, added = link_file(
                text, keywords, fp.stem, first_only=not args.all_occurrences
            )
            n = sum(added.values())
            added_total += n
            if n:
                detail.append(f"付与 {n}件 ({', '.join(sorted(added))[:60]})")

        if text != original:
            changed.append((fp, detail))
            if args.write:
                fp.write_text(text, encoding="utf-8")

    mode = "書き込みました" if args.write else "プレビュー（--write で実行）"
    print("=" * 62)
    print(f" 対象 {len(files)} ファイル / 変更 {len(changed)} ファイル  [{mode}]")
    print("=" * 62)
    for fp, detail in changed:
        print(f"  {fp.relative_to(ROOT)}")
        for d in detail:
            print(f"      {d}")
    print("-" * 62)
    if args.repair:
        print(f"  入れ子リンク修復        : {totals['nested']}")
        print(f"  単語途中のリンクを解除  : {totals['boundary']}")
        print(f"  コードブロック内を解除  : {totals['code']}")
        print(f"  フェンス記号を修復      : {totals['fence']}")
        print(f"  インラインコード内を解除: {totals['inline']}")
    if args.headings:
        print(f"  見出しリンク解除        : {heading_total}")
    if args.prune:
        print(f"  リンク解除              : {pruned_total}")
    if args.link:
        print(f"  リンク付与              : {added_total}")
    print("=" * 62)
    if not args.write and changed:
        print("※ まだ何も書き換えていません。--write を付けると反映されます。")


if __name__ == "__main__":
    main()
