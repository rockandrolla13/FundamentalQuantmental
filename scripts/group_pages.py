"""Bar charts for the group pages of docs/writeup/combined_framework.tex (one chart per S14 bucket).

Reads data/raw/process/<T>.json (step 14 outputs) and writes docs/writeup/fig_bucket_<bucket>.tex: one TikZ chart of
the bucket's alpha per issuer, in bp a year before cost, with the estimate that moves each bar most named beside it.
Run: python scripts/group_pages.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TICKERS = ("CRWV", "ORCL", "HCA", "THC", "CCL", "NCLH", "MGM", "WYNN")
WIDTH_CM = 4.2  # half width: the largest absolute value in the chart reaches this far from zero


def load() -> dict[str, dict]:
    return {t: json.loads((ROOT / f"data/raw/process/{t}.json").read_text())["steps"]["14"]["outputs"]["groups"]
            for t in TICKERS}


def driver(rows: list[dict]) -> str:
    """The estimate with the largest absolute weighted contribution, e.g. 'E10 +1289'."""
    rows = [r for r in rows if r["weight"] > 0]
    if len(rows) < 2:
        return ""
    r = max(rows, key=lambda r: abs(r["contribution"]))
    return f"{r['estimate']} {r['alpha_bp_yr']:+.0f}"


def chart(bucket: str, data: dict[str, dict]) -> str:
    vals = {t: data[t][bucket]["alpha_bp_yr"] for t in TICKERS}
    top = max(abs(v) for v in vals.values()) or 1.0
    k = WIDTH_CM / top
    out = [r"\begin{tikzpicture}[x=1cm,y=0.42cm,font=\scriptsize]",
           rf"\draw[gray!60] (0,0.6) -- (0,{-len(TICKERS) + 0.4});",
           rf"\node[gray,anchor=south] at (0,0.6) {{0}};"]
    for i, t in enumerate(TICKERS):
        v, y = vals[t], -i
        x = v * k
        col = "good" if v > 0 else ("bad" if v < 0 else "gray")
        out.append(rf"\node[anchor=east] at ({-WIDTH_CM - 1.0:.2f},{y}) {{\textbf{{{t}}}}};")
        if v != 0:
            out.append(rf"\fill[{col}!70] (0,{y - 0.32:.2f}) rectangle ({x:.3f},{y + 0.32:.2f});")
        side = "west" if v >= 0 else "east"
        nudge = 0.08 if v >= 0 else -0.08
        out.append(rf"\node[anchor={side}] at ({x + nudge:.3f},{y}) {{{v:+.0f}}};")
        d = driver(data[t][bucket]["rows"])
        if d:
            out.append(rf"\node[anchor=west,gray] at ({WIDTH_CM + 0.9:.2f},{y}) {{{d}}};")
    out.append(rf"\node[anchor=north,gray] at (0,{-len(TICKERS) + 0.3}) {{bucket alpha, bp a year before cost}};")
    if any(driver(data[t][bucket]["rows"]) for t in TICKERS):
        out.append(rf"\node[anchor=west,gray,font=\scriptsize\itshape] at ({WIDTH_CM + 0.9:.2f},0.9) {{largest driver}};")
    out.append(r"\end{tikzpicture}")
    return "\n".join(out) + "\n"


def main() -> None:
    data = load()
    for bucket in ("G1", "G2C", "G2", "G3", "G4"):
        p = ROOT / f"docs/writeup/fig_bucket_{bucket}.tex"
        p.write_text(chart(bucket, data))
        print(p.relative_to(ROOT))


if __name__ == "__main__":
    main()
