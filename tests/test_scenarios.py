import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import scenarios  # noqa: E402

from hy.events import MacroPath  # noqa: E402


def _path(spread):
    a = np.full(8, 0.04)
    return MacroPath("p", 1.0, a, a, a, a, np.full(8, 50.0), np.full(8, spread), np.full(8, 0.03))


def test_refi_score_counts_points_and_reacts_to_the_path():
    pts = scenarios.refi_points(0.05, {"g_spread": 0.06, "price": 82.0}, recent_raise=True)
    # rating proxy (500 bp < 700), recent raise, longest bond inside 700 bp (price ignored), market open
    assert scenarios.refi_score(pts, _path(0.017), 4, S_now=0.017, s_now=0.05) == 4
    # stress path: spreads x 2.2 -> market shut, longest bond scaled to 1,320 bp -> two points lost
    assert scenarios.refi_score(pts, _path(0.0374), 4, S_now=0.017, s_now=0.05) == 2


def test_access_map_is_monotone_and_open_plus_one_point_refinances():
    p = scenarios.V0["refi_score_to_p"]
    assert list(p) == sorted(p) and p[2] > 0.5 and len(p) == 7
