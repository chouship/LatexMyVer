#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计 LaTeX 论文的中文与英文词数。
用法:  python wordcount.py main.tex
"""

import re
import sys
from pathlib import Path

# 递归包含
INCLUDE_RE = re.compile(r'\\(?:include|input|subfile)\s*\{([^}]+)\}')
# 注释（保留转义的 \%）
COMMENT_RE = re.compile(r'(?<!\\)%.*$')
# 汉字（含扩展 A 区）
CJK_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')
# 英文单词（允许 don't / well-known 这种）
EN_WORD_RE = re.compile(r"[A-Za-z]+(?:['\-][A-Za-z]+)*")
# 英文字符
EN_CHAR_RE = re.compile(r'[A-Za-z]')

# 这些命令的参数不该算正文
SKIP_ARG_CMDS = re.compile(
    r'\\(?:label|ref|eqref|pageref|autoref|cref|Cref|'
    r'cite|citep|citet|nocite|'
    r'index|bibliography|bibliographystyle|'
    r'usepackage|documentclass|includegraphics|'
    r'href|url|input|include|subfile|'
    r'newcommand|renewcommand|providecommand|'
    r'def|let|setlength|addtolength|'
    r'vspace|hspace|vskip|hskip)\s*'
    r'(?:\[[^\]]*\])?\s*\{[^}]*\}',
    re.DOTALL,
)

MATH_DISPLAY_RE = re.compile(r'\$\$.*?\$\$|\\\[.*?\\\]', re.DOTALL)
MATH_INLINE_RE  = re.compile(r'\$[^$]*\$|\\\(.*?\\\)', re.DOTALL)
ENV_RE = re.compile(
    r'\\begin\{(equation|align|eqnarray|gather|math|displaymath|'
    r'figure|table|tabular|verbatim|lstlisting|minted|tikzpicture)\*?\}'
    r'.*?'
    r'\\end\{\1\*?\}',
    re.DOTALL,
)
CMD_RE = re.compile(r'\\[A-Za-z@]+\*?')


def strip_comments(text: str) -> str:
    return '\n'.join(COMMENT_RE.sub('', line) for line in text.splitlines())


def clean_latex(text: str) -> str:
    text = strip_comments(text)
    text = ENV_RE.sub(' ', text)
    text = MATH_DISPLAY_RE.sub(' ', text)
    text = MATH_INLINE_RE.sub(' ', text)
    text = SKIP_ARG_CMDS.sub(' ', text)
    text = CMD_RE.sub(' ', text)
    text = re.sub(r'[{}\[\]&~^_\\]', ' ', text)
    return text


def count(text: str):
    text = clean_latex(text)
    cjk = len(CJK_RE.findall(text))
    en_word = len(EN_WORD_RE.findall(text))
    en_char = len(EN_CHAR_RE.findall(text))
    return cjk, en_word, en_char


def collect(main_file: Path, seen=None):
    if seen is None:
        seen = set()
    main_file = main_file.resolve()
    if main_file in seen or not main_file.exists():
        return []
    seen.add(main_file)
    files = [main_file]
    raw = strip_comments(main_file.read_text(encoding='utf-8', errors='ignore'))
    for m in INCLUDE_RE.finditer(raw):
        inc = m.group(1).strip()
        if not inc.endswith('.tex'):
            inc += '.tex'
        for base in (main_file.parent, main_file.parent.parent):
            cand = base / inc
            if cand.exists():
                files.extend(collect(cand, seen))
                break
    return files


def main():
    main_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('main.tex')
    if not main_file.exists():
        print(f'找不到 {main_file}')
        sys.exit(1)

    files = collect(main_file)
    print(f'统计文件数: {len(files)}\n')

    total_cjk = total_enw = total_enc = 0
    for f in files:
        text = f.read_text(encoding='utf-8', errors='ignore')
        cjk, enw, enc = count(text)
        total_cjk += cjk
        total_enw += enw
        total_enc += enc
        try:
            rel = f.relative_to(main_file.parent)
        except ValueError:
            rel = f
        rel_str = str(rel)
        print(f'  {rel_str:<40s} 中文 {cjk:>6d}   英文 {enw:>6d} 词 / {enc:>7d} 字符')

    print()
    print(f'中文字符数 : {total_cjk}')
    print(f'英文单词数 : {total_enw}')
    print(f'英文字符数 : {total_enc}')
    print(f'中英合计   : {total_cjk + total_enw}')


if __name__ == '__main__':
    main()