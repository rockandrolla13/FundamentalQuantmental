"""Restore display equations in a PDF-to-markdown conversion from its LaTeX source.

The converter drops display maths as "picture intentionally omitted" and sometimes flattens one equation to text.
This script aligns the placeholders with the source's equation blocks in document order (the source context after
each block against the markdown text after each placeholder), allows the converter to have skipped blocks, and writes
each block back as $$ ... $$. Figures (placeholders followed by picture text) get a one-line note.
Run: python scripts/md_equations.py docs/writeup/combined_framework.tex docs/writeup/combined_framework.md
"""

from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

EQ = re.compile(r"\\begin\{(equation\*?|align\*?)\}(.*?)\\end\{\1\}|\\\[(.*?)\\\]", re.S)
PLACEHOLDER = "intentionally omitted"


def _plain(s: str) -> str:
    s = re.sub(r"\\(intu|sym|textbf|emph|code|fld)\{", "", s)
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = re.sub(r"[{}$\\_^~]", "", s)
    return re.sub(r"\s+", " ", s).strip()[:60]


def _ctx(md: list[str], i: int) -> str:
    out = []
    for j in range(i + 1, min(i + 6, len(md))):
        t = re.sub(r"[*_`]", "", md[j]).strip()
        if t and not re.fullmatch(r"\(?\d+\)?", t):
            out.append(t)
    return re.sub(r"\s+", " ", " ".join(out))[:60]


def _align(ctx: list[str], src: list[str]) -> list[int]:
    """Monotone alignment of placeholders to source blocks maximising total context similarity (dynamic program)."""
    n, m = len(ctx), len(src)
    sim = [[difflib.SequenceMatcher(None, ctx[i], src[j]).ratio() for j in range(m)] for i in range(n)]
    best = [[-1e9] * (m + 1) for _ in range(n + 1)]
    best[0] = [0.0] * (m + 1)
    for i in range(1, n + 1):
        for j in range(i, m + 1):
            best[i][j] = max(best[i][j - 1], best[i - 1][j - 1] + sim[i - 1][j - 1])
    out, j = [], m
    for i in range(n, 0, -1):
        while best[i][j] == best[i][j - 1]:
            j -= 1
        out.append(j - 1)
        j -= 1
    return out[::-1]


def restore(tex_path: Path, md_path: Path) -> dict:
    tex = tex_path.read_text()
    md = md_path.read_text().split("\n")
    blocks = [(re.sub(r"\\label\{[^}]*\}", "", (m.group(2) or m.group(3))).strip(), _plain(tex[m.end():m.end() + 300]))
              for m in EQ.finditer(tex)]
    ph = [i for i, l in enumerate(md) if PLACEHOLDER in l]
    eqs = [i for i in ph if not any("Start of picture text" in md[j] for j in range(i + 1, min(i + 4, len(md))))]
    idx = _align([_ctx(md, i) for i in eqs], [a for _, a in blocks])
    for i, k in zip(eqs, idx):
        md[i] = "$$\n" + blocks[k][0] + "\n$$"
    # A block the converter flattened to text: find the line that opens with its \text{...} lead and ends "(n)".
    for k in (k for k in range(len(blocks)) if k not in set(idx)):
        lead = re.match(r"\\text\{([^}]*)\}", blocks[k][0])
        if lead:
            for i, l in enumerate(md):
                if l.strip().startswith(lead.group(1).strip()) and re.search(r"\(\d+\)\s*$", l):
                    md[i] = "$$\n" + blocks[k][0] + "\n$$"
                    idx.append(k)
                    break
    figs = 0
    for i in ph:
        if i not in eqs:
            md[i] = "*(Figure: see the PDF.)*"
            figs += 1
    text = "\n".join(md)
    md_path.write_text(text)
    return {"equations_restored": len(eqs), "source_blocks": len(blocks), "figures": figs,
            "unmatched_source_blocks": [blocks[k][1] for k in range(len(blocks)) if k not in set(idx)]}


if __name__ == "__main__":
    print(restore(Path(sys.argv[1]), Path(sys.argv[2])))
