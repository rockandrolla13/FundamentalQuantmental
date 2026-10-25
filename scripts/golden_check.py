"""Golden check for the data-module migration (design: data module, step 1 to 7).

`snapshot` runs the 8-issuer process and the peer-line backtest once and keeps their outputs in
data/raw/golden/. `check` reruns both into a scratch folder and compares every value: numbers to a relative
tolerance of 1e-9, strings and keys exactly. Run `check` after each migration step; only step 5 may change numbers,
and then by a recorded decision.

    PYTHONPATH=.:scripts python3 scripts/golden_check.py snapshot
    PYTHONPATH=.:scripts python3 scripts/golden_check.py check

Another machine picks its own issuers at the snapshot (`--tickers`, `--pairs`, `--end`); `check` reuses the ones
the snapshot saved in `golden/_args.json`. The backtest subprocess gets the run's HY_* settings.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hy.data.config import CONFIG  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
GOLDEN = CONFIG.path("golden")
TICKERS = ["CRWV", "ORCL", "HCA", "THC", "CCL", "NCLH", "MGM", "WYNN"]
PAIRS = [("CRWV", "ORCL"), ("HCA", "THC"), ("CCL", "NCLH"), ("MGM", "WYNN")]
END = "2026-09-17"
BACKTEST_JSON = CONFIG.path("backtest", "summary_peer_line_ex_distressed_cost15.json")


# Settings the backtest subprocess must share with this process, so both read the same source and data root.
PASSED_ENV = ("HY_SOURCE", "HY_OFFLINE", "SEC_USER_AGENT")


def run_outputs(out: Path, tickers=TICKERS, pairs=PAIRS, end: str = END) -> None:
    """The process for the issuers into `out/process`, and the peer-line backtest summary into `out`."""
    import os  # noqa: PLC0415
    import process  # noqa: PLC0415 - scripts/ is on the path only here

    process.run(list(tickers), end, [tuple(p) for p in pairs], out_dir=out / "process", figures=False)
    # The caller's PYTHONPATH stays after the repo root, so a source module named in HY_SOURCE imports there too.
    path = os.pathsep.join(p for p in (str(ROOT), os.environ.get("PYTHONPATH", "")) if p)
    env = {"PYTHONPATH": path, "PATH": "/usr/bin:/bin", "HOME": str(Path.home()), "HY_DATA_ROOT": str(CONFIG.root),
           **{k: os.environ[k] for k in PASSED_ENV if k in os.environ}}
    subprocess.run([sys.executable, str(ROOT / "scripts" / "backtest_peer_line.py"), "--cost-bp", "15"], check=True,
                   cwd=ROOT, env=env, capture_output=True)
    shutil.copy(BACKTEST_JSON, out / BACKTEST_JSON.name)


def diff(a, b, path: str = "", out: list | None = None, rel: float = 1e-9) -> list[str]:
    """Every place where `a` and `b` differ, as readable paths."""
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: key only in {'new' if k in b else 'golden'}")
            else:
                diff(a[k], b[k], f"{path}/{k}", out, rel)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} -> {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, f"{path}[{i}]", out, rel)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if not (math.isclose(a, b, rel_tol=rel, abs_tol=1e-12) or (a != a and b != b)):
            out.append(f"{path}: {a} -> {b}")
    elif a != b:
        out.append(f"{path}: {str(a)[:60]!r} -> {str(b)[:60]!r}")
    return out


def compare(golden: Path, new: Path) -> list[str]:
    problems = []
    for g in sorted(golden.rglob("*.json")):
        if g.name == "_args.json":  # the snapshot's settings, not an output
            continue
        n = new / g.relative_to(golden)
        if not n.exists():
            problems.append(f"{g.relative_to(golden)}: missing in the new run")
            continue
        d = diff(json.loads(g.read_text()), json.loads(n.read_text()))
        problems += [f"{g.relative_to(golden)}{x}" for x in d]
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["snapshot", "check"])
    ap.add_argument("--tickers", nargs="+", default=TICKERS, help="snapshot only (check reuses the snapshot's)")
    ap.add_argument("--pairs", nargs="*", default=[f"{x}:{y}" for x, y in PAIRS], help="as A:B; snapshot only")
    ap.add_argument("--end", default=END, help="last trade day; snapshot only")
    a = ap.parse_args()
    args_file = GOLDEN / "_args.json"
    if a.what == "snapshot":
        if GOLDEN.exists():
            shutil.rmtree(GOLDEN)
        GOLDEN.mkdir(parents=True)
        run = {"tickers": [t.upper() for t in a.tickers], "pairs": [p.upper().split(":") for p in a.pairs], "end": a.end}
        run_outputs(GOLDEN, **run)
        args_file.write_text(json.dumps(run))  # after the run, so compare() reads only the run's outputs
        print(f"golden snapshot in {GOLDEN}: {len(list(GOLDEN.rglob('*.json'))) - 1} JSON files")
        return
    run = json.loads(args_file.read_text()) if args_file.exists() else {"tickers": TICKERS, "pairs": PAIRS, "end": END}
    with tempfile.TemporaryDirectory() as tmp:
        run_outputs(Path(tmp), **run)
        problems = compare(GOLDEN, Path(tmp))
    if problems:
        print(f"GOLDEN CHECK FAILED: {len(problems)} difference(s)")
        for p in problems[:40]:
            print("  " + p)
        sys.exit(1)
    print("golden check passed: outputs identical to the snapshot")


if __name__ == "__main__":
    main()
