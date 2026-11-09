"""Delivery delay on CoreWeave's clocks (methodology Section 4.7.2). Report only.

Assumptions (analyst, not from the filing):
1. The share of RPO that waits for unbuilt sites equals the share of rent on signed leases not yet started (`f`).
   The rest of RPO runs on built sites and does not move.
2. The tenant's signed leases not yet started move with delivery. Debt, interest, leases in force, and purchases do not.
3. Reserve = balance sheet cash. Window = 5 years, before the 2031 to 2032 debt wall.
4. Contract cash = RPO x the EBITDAR margin. Capex is not in the cost clock, so each need is a lower bound and each
   tolerance an upper bound (Section 4.7 rule 5).

Run from the repo root: SEC_USER_AGENT="Name email" PYTHONPATH=. python3 scripts/clock_delay_case.py
"""
import sys
sys.path.insert(0, ".")
from scripts.clock_case import build_case, RAW, OVERRIDES, _v
from hy.sources import clock_inputs as ci
from hy import clocks
inp = ci.derive_inputs("CRWV", RAW, str(OVERRIDES), None)
case = build_case(inp)
res = case["_res"]
print("as_of", case["as_of"], "margin", round(case["metrics"]["ebitdar_margin"], 3))
from scripts.clock_case import open_view
import pandas as pd
view = open_view(pd.Timestamp(_v(inp, "available_at")))
q = view.balance_sheet(view.issuer("CRWV"), _v(inp, "q"))
cash, rcf = q.cash, q.revolver_capacity
print("cash", cash, "revolver", rcf)
margin = case["metrics"]["ebitdar_margin"]
ob = res.obligations  # annual grids
rev = clocks.rpo(_v(inp, "rpo_total"), _v(inp, "rpo_windows"), _v(inp, "rpo_tail_years"))
lease_new = ob["Signed leases not yet started"].sum(); lease_all = lease_new + ob["Leases in force"].sum()
f = lease_new / lease_all
print(f"share of rent on unbuilt sites f = {f:.2f}")
SH = ("Signed leases not yet started",)
def run(frac, reserve, credit=0.0, shift=SH):
    obs = dict(ob)
    if frac < 1:
        live = [clocks.Bucket(b.start, b.length, -margin * b.amount * (1 - frac)) for b in rev]
        obs["live contract cash"] = live  # cash from built sites: does not move
    late = [clocks.Bucket(b.start, b.length, b.amount * frac) for b in rev]
    return clocks.delay_tolerance(obs, late, margin, reserve, shift=shift, rent_credit_ratio=credit, window_years=5)
for label, frac, reserve, credit, shift in [
    ("base: f of RPO late, cash only", f, cash, 0.0, SH),
    ("credits 1:1", f, cash, 1.0, SH),
    ("upper bound: all RPO late", 1.0, cash, 0.0, SH),
    ("as if landlord (rent does not move)", f, cash, 0.0, ()),
]:
    r = run(frac, reserve, credit, shift)
    en = r.extra_need
    print(f"{label:38s} need0={r.metrics['peak_need_0']:>8,.0f} tol={r.metrics['delay_tolerance_months']} "
          f"extra 6m={en[6]:>7,.0f} 12m={en[12]:>7,.0f} 24m={en[24]:>7,.0f}")
