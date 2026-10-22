"""Split docs/writeup/issuer_memos.pdf into one PDF per issuer: docs/writeup/memos/<ticker>.pdf.

    python3 scripts/split_memos.py     # run after latexmk and before `latexmk -c` (it reads the .aux labels)

scripts/memo.py puts \\label{memo-start-<ticker>} at the start of each memo. The .aux file gives each label's page;
an issuer's memo runs from its start page to the page before the next issuer's start (the last one to the end).
"""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
WRITEUP = ROOT / "docs" / "writeup"


def start_pages(aux: Path) -> list[tuple[str, int]]:
    """(ticker, first page) for each memo, in page order, from \\newlabel{memo-start-T}{{}{page}...} lines."""
    hits = re.findall(r"\\newlabel\{memo-start-([A-Z.]+)\}\{\{[^}]*\}\{(\d+)\}", aux.read_text())
    return sorted(((t, int(p)) for t, p in hits), key=lambda x: x[1])


def main() -> None:
    starts = start_pages(WRITEUP / "issuer_memos.aux")
    reader = PdfReader(str(WRITEUP / "issuer_memos.pdf"))
    out_dir = WRITEUP / "memos"
    out_dir.mkdir(exist_ok=True)
    n = len(reader.pages)
    for i, (t, p) in enumerate(starts):
        last = starts[i + 1][1] - 1 if i + 1 < len(starts) else n
        w = PdfWriter()
        for k in range(p - 1, last):
            w.add_page(reader.pages[k])
        with open(out_dir / f"{t}.pdf", "wb") as f:
            w.write(f)
        print(f"{t}: pages {p}-{last}")


if __name__ == "__main__":
    main()
