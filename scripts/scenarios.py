"""Live macro paths and issuer scenarios under each path (methodology Sections 5.1 to 5.4, 7.5; framework F4, F6).

Shared by scripts/clocks_report.py and scripts/rv_pair.py.
1. `live_paths`: forecast registry from the public sources, the TRACE spread level, the F6 phase from the
   indicators that have data (TRACE spread and distress snapshots, SLOOS), and five macro paths.
2. `issuer_start`: the scenario engine's starting point from the issuer's filings and point-in-time quarters.
3. `issuer_scenarios`: every F6 case under every path; leverage, refinancing risk, and expected alpha by path.

Every input that the data does not give is a v0 default in `V0`, listed on the decision page
docs/decisions/2026-10-22-issuer-scenario-defaults.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from hy import alpha, forward, macro, rv
from hy.sources import clock_inputs as ci
from hy.sources import forecast_sources as fs
from hy.sources import schedules as sc
from hy.sources import trace_bonds as tb
from hy.sources import treasury as tr
from hy.sources import xbrl_instance as xi

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
H = 8

V0 = {  # v0 defaults (decision page); each one is a stated assumption until calibrated
    "beta_sector": {"A2": 0.3, "A4": 1.5, "A5": 1.0, "A6": 0.5, "A7": 1.2},
    "trend_gdp": 0.018,
    "recession": {"A2": (-0.05, -0.02), "A4": (-0.20, -0.10), "A5": (-0.15, -0.05), "A6": (-0.10, -0.03),
                  "A7": (-0.20, -0.05)},
    "trough_margin_share": 0.8,
    "refi_open_spread_multiple": 1.5,   # F4 point 5: market open while the path's HY spread < 1.5 x today
    "rating_proxy_spread": 0.07,        # F4 point 1 without ratings: inside 700 bp (the F4 distress line) stands in
                                        # for B- or better
    # F4 score 0..6 -> p_refi_access (v0): an open market plus one more point refinances with p >= 0.8.
    # Calibrate from realised refinancings by score and market state (F4).
    "refi_score_to_p": (0.20, 0.50, 0.80, 0.92, 0.97, 0.99, 0.995),
    "lgd": 0.6, "rho_q": 0.85, "bid_ask_bp": 20.0, "h_years": 0.5,
    "kappa": 2.0,                       # market price of risk: spread / expected loss (v0; decision page)
    "p_default_given_refi_fail": 0.5,   # a failed refinancing defaults within a year half the time (v0)
    "p_default_given_liq_short": 0.5,   # same for a liquidity shortfall inside 8 quarters (v0)
    "coupon_fallback": 0.06, "growth_bounds_q": (-0.05, 0.08),
    "days_bounds": (0.0, 120.0),        # payables can include capex payables; clip working-capital days
}


# ---------------------------------------------------------------------------------------------------------------
# 1. Macro paths
# ---------------------------------------------------------------------------------------------------------------


def _bench_level(con, end: pd.Timestamp) -> tuple[float, float, str]:
    """TRACE HY benchmark median G-spread across buckets, and the share of bonds above 1,000 bp, at `end`."""
    b = tb.hy_benchmark(con, end.strftime("%Y-%m-%d"), cache_root=RAW)
    curve = tr.curve_on(end, cache_root=RAW)
    s = tb.g_spread(b["yield"], b["maturity"], end, curve) if "yield" in b else tb.g_spread(b["yield_vw"], b["maturity"], end, curve)
    s = pd.Series(np.asarray(s, dtype=float))
    s = s[(s > 0) & (s < 0.25)]
    return float(s.median()), float((s > 0.10).mean()), f"TRACE HY benchmark {end:%Y-%m-%d}"


def phase_indicators(con, end: pd.Timestamp, registry) -> tuple[dict, pd.DataFrame]:
    """F6 indicators with data: hy_oas and distress_ratio from TRACE snapshots (now, 3 months ago, and once a
    year for five years), sloos_tightening from the registry. PMI, default forecast, issuance quality: none."""
    rows = []
    for k, when in [("now", end), ("3m", end - pd.DateOffset(months=3))] + \
                   [(f"{y}y", end - pd.DateOffset(years=y)) for y in range(1, 6)]:
        try:
            lvl, dist, src = _bench_level(con, pd.Timestamp(when))
            rows.append({"snapshot": k, "date": pd.Timestamp(when).date(), "hy_spread": lvl, "distress": dist})
        except Exception as e:  # a snapshot with no data is skipped, and the table says so
            rows.append({"snapshot": k, "date": pd.Timestamp(when).date(), "hy_spread": np.nan, "distress": np.nan,
                         "error": type(e).__name__})
    t = pd.DataFrame(rows)
    now, m3 = t.iloc[0], t.iloc[1]
    hist = t[t["snapshot"].str.endswith("y") | (t["snapshot"] == "now")]
    ind = {
        "hy_oas": {"level": now["hy_spread"], "median_5y": hist["hy_spread"].median(),
                   "change_3m": now["hy_spread"] - m3["hy_spread"]},
        "distress_ratio": {"level": now["distress"], "median_5y": hist["distress"].median()},
    }
    # Two quarters of SLOOS need two vintages; `as_of` keeps only the newest, so filter the history by release.
    allrows = registry.frame()
    sl = allrows[(allrows["variable"] == "sloos_tightening")
                 & (pd.to_datetime(allrows["available_at"]) <= pd.Timestamp(end) + pd.Timedelta(1, unit="D"))]
    sl = sl.sort_values("vintage").drop_duplicates("vintage", keep="last")
    if len(sl) >= 2:
        ind["sloos_tightening"] = list(sl["point"].iloc[-2:])
    return ind, t


@dataclass
class Macro:
    paths: macro.PathSet
    registry: object
    snapshots: pd.DataFrame
    s_index_now: float
    decision: pd.Timestamp


def live_paths(con, decision: pd.Timestamp, trace_end: pd.Timestamp) -> Macro:
    """Registry with every live source (TRACE benchmark through `con`), phase from data, five paths."""
    reg = fs.load_all(decision.to_pydatetime(), RAW, options={"trace_hy_benchmark": {"con": con}})
    ind, snaps = phase_indicators(con, trace_end, reg)
    ps = macro.build_paths(reg, decision.to_pydatetime(), phase_indicators=ind)
    return Macro(ps, reg, snaps, float(snaps.iloc[0]["hy_spread"]), decision)


# ---------------------------------------------------------------------------------------------------------------
# 2. Issuer start
# ---------------------------------------------------------------------------------------------------------------


def _nz(x, d=0.0):
    return float(x) if x is not None and x == x else d


def issuer_start(inputs: dict, case: dict, decision: pd.Timestamp) -> tuple[forward.IssuerStart, dict, dict]:
    """IssuerStart and base drivers from the point-in-time quarters and the filing (Section 5.1 starting point).

    Debt lines: each debt-ladder bucket that falls due inside 8 quarters is one line with that maturity quarter;
    the rest is one line with no maturity inside the horizon. Coupon = the derived cash interest rate. All lines
    fixed (the filings do not split fixed and floating in a standard tag; stated). Revolver: undrawn capacity tag.
    """
    v = ci.values(inputs)
    quarters, _ = ci.loader_quarters(v["ticker"], v.get("gvkey"), RAW, decision)
    q4 = ci.last_four(quarters) or sorted(quarters, key=lambda r: r.as_of)[-4:]
    last = q4[-1]
    eb = [_nz(r.ebitda_adj_company, np.nan) for r in q4]
    fill = np.nanmean(eb)
    eb = tuple(float(x) if x == x else float(fill) for x in eb)
    intr = tuple(_nz(r.cash_interest, 0.0) for r in q4)
    rev = _nz(last.revenue)
    cogs = _nz(last.cogs, np.nan)
    v_ratio = cogs / rev if rev and cogs == cogs else 0.5
    margin = sum(eb) / sum(_nz(r.revenue) for r in q4) if all(_nz(r.revenue) for r in q4) else eb[-1] / rev
    a_ratio = max(0.0, 1 - margin - v_ratio)
    lo, hi = V0["days_bounds"]
    inv_d = float(np.clip(_nz(last.inventory) / cogs * 91 if cogs == cogs and cogs else 0.0, lo, hi))
    rec_d = float(np.clip(_nz(last.receivables) / rev * 91 if rev else 0.0, lo, hi))
    pay_d = float(np.clip(_nz(last.payables) / cogs * 91 if cogs == cogs and cogs else 0.0, lo, hi))
    old = sorted(quarters, key=lambda r: r.as_of)[-8:-4]
    g = 0.005
    if len(old) == 4 and all(_nz(r.revenue) for r in old):
        g = (sum(_nz(r.revenue) for r in q4) / sum(_nz(r.revenue) for r in old)) ** 0.25 - 1
    g = float(np.clip(g, *V0["growth_bounds_q"]))
    rate = v.get("interest_rate") or V0["coupon_fallback"]

    q = xi.load_instance(v["cik"], v["q"], cache_root=RAW)
    lad = case["ladders"]["debt"]
    first = case["ladders"]["debt_first_length"] or 1.0
    lines, t_end = [], 0.0
    for i, amt in enumerate(lad or []):
        length = first if i == 0 else 1.0
        t_end += length if i < len(lad) - 1 else 0.0
        mq = int(round(t_end * 4))
        if amt and i < len(lad) - 1 and 1 <= mq <= H:
            lines.append(forward.DebtLine(f"due_q{mq}", face=float(amt), coupon=rate, maturity_q=mq))
    inside = sum(l.face for l in lines)
    total = _nz(sc.balance_sheet_debt(q)[0], sum(lad or []))
    if total - inside > 0:
        lines.append(forward.DebtLine("later", face=float(total - inside), coupon=rate))
    cap = 0.0
    for tag in ("LineOfCreditFacilityRemainingBorrowingCapacity", "LineOfCreditFacilityMaximumBorrowingCapacity"):
        hit = q[(q["concept"].str.split(":").str[-1] == tag) & (q["n_dims"] == 0)]
        if len(hit):
            cap = float(hit["value"].iloc[0]) / 1e6
            break
    start = forward.IssuerStart(
        revenue_q0=rev, ebitda_hist=eb, interest_hist=intr, cash0=_nz(last.cash), debt_lines=tuple(lines),
        revolver_commitment=cap, inventory_days0=inv_d, receivable_days0=rec_d, payable_days0=pay_d,
        cogs_ratio0=v_ratio, da_q=_nz(last.depreciation), min_cash=0.02 * rev)
    # Framework F4.7: the cases fund maintenance capex; depreciation is the floor for A4 and A5. Growth capex is
    # cuttable and, for these issuers, financed by its own facilities, so it stays out of the recursion (v0, stated).
    capex_total = _nz(last.capex_total)
    dep = _nz(last.depreciation, np.nan)
    capex = min(capex_total, dep) if dep == dep and dep > 0 else 0.3 * capex_total
    drivers = dict(g=g, v=v_ratio, a=a_ratio, inventory_days=inv_d, receivable_days=rec_d, payable_days=pay_d,
                   capex=capex)
    info = {"margin_ltm": margin, "g_q": g, "rate": rate, "capex_total_q": capex_total, "capex_case_q": capex, "revolver_capacity": cap, "debt_total": total,
            "maturing_in_8q": inside, "quarters_used": f"{q4[0].as_of:%b-%Y}..{q4[-1].as_of:%b-%Y}"}
    return start, drivers, info


# ---------------------------------------------------------------------------------------------------------------
# 3. Scenarios under paths
# ---------------------------------------------------------------------------------------------------------------


def refi_points(s_now: float, longest: dict | None, recent_raise: bool) -> dict:
    """Issuer-level points of the F4 refinance access score that do not depend on the path."""
    return {"rating_proxy": s_now < V0["rating_proxy_spread"], "recent_raise": bool(recent_raise),
            "longest_spread": (longest or {}).get("g_spread"), "longest_price": (longest or {}).get("price"),
            "unencumbered": False, "sponsor": False}


def refi_score(points: dict, path, q: int, S_now: float, s_now: float) -> int:
    """F4 score under a path: points 1, 2, 3, 6 from `points`; point 4 (longest bond above 90 and inside 700 bp)
    re-read with its spread scaled by the path; point 5 (primary market open) from the path's HY spread."""
    S_q = float(path.index_spread[min(q, H) - 1])
    n = int(points["rating_proxy"]) + int(points["recent_raise"]) + int(points["unencumbered"]) + int(points["sponsor"])
    # Point 4 on spread only: a low-coupon long bond trades below 90 because of rates, not credit (v0, stated).
    ls = points.get("longest_spread")
    if ls is not None and ls == ls:
        n += int(ls * S_q / S_now < 0.07)
    n += int(S_q < V0["refi_open_spread_multiple"] * S_now)
    return n


def issuer_scenarios(start, drivers: dict, archetype: str, mac: Macro, s_now: float, s_fair_now: float,
                     spread_duration: float, points: dict | None = None, loss_given_default: float | None = None,
                     capex_committed_q: float | None = None) -> dict:
    """Every F6 case under every path; per-path leverage, refinancing risk, and expected alpha (Sections 5.4, 7.5).

    Fair spread under path m: s_fair_now x S(m) / S_now, with S(m) the path's mean HY spread over 4 quarters.
    Expected loss consistent with spread: PD(m) x LGD = s_fair(m) / kappa; the index's is S(m) / kappa.
    Hedge: spread-proportional, beta = s_now / S_now, so carry nets out and the hedge earns the index's loss.
    Then alpha comes from mispricing only: (s - s_fair) through convergence and through expected loss.
    The engine raises PD where refinancing or liquidity fails: PD(m) >= 0.5 x need x (1 - p_refi_access(m))
    + 0.5 x p_liq_short_8(m), with `need` the share of debt that falls due inside 8 quarters.
    All are v0 rules (decision page).
    `loss_given_default` replaces LGD on face in the alpha's own default loss (mapping C3: loss on the purchase price,
    with recovery discounted for delay); the spread anchor and the hedge keep V0["lgd"].
    The output also carries the case-weighted quarterly FCF per path and the severe case's (for the funding gap).
    `capex_committed_q` (all capex per quarter, growth included) runs the severe case a second time on the likely path
    with that capex (spec K14: the cases fund maintenance capex only; quote the shorter runway of the two runs).
    """
    S = mac.s_index_now
    paths = mac.paths.paths
    rec = V0["recession"].get(archetype, V0["recession"]["A4"])
    base = forward.base_scenario(H, **drivers)
    tmpl = {"annual": rec, "recovery_shape": "u", "trough_margin": V0["trough_margin_share"] * (1 - drivers["v"] - drivers["a"])}
    cases = forward.f6_cases(base, archetype, (), tmpl)

    def s_fair_path(path, q):
        return s_fair_now * float(path.index_spread[min(q, H) - 1]) / S

    pts = points or refi_points(s_now, None, False)

    def p_access(path, q):
        return V0["refi_score_to_p"][refi_score(pts, path, q, S, s_now)]

    def fwd_t(path, q, tenor):
        y2, y10 = float(path.y2[min(q, H) - 1]), float(path.y10[min(q, H) - 1])
        return y2 + (y10 - y2) * (min(max(tenor, 2), 10) - 2) / 8

    beta = V0["beta_sector"].get(archetype, 1.0)
    grid = forward.run_grid(start, cases, paths, betas={"g": beta}, trend=V0["trend_gdp"],
                            forecast_rows=mac.paths.sources, s_fair_fn=s_fair_path, p_refi_access_fn=p_access,
                            forward_treasury_fn=fwd_t)
    w = forward.case_weights_by_path(paths, mac.paths.phase, archetype)
    feats = forward.forward_features_by_path(grid, paths, w, start)
    by = []
    k, lgd = V0["kappa"], V0["lgd"]
    fpath = feats.set_index("macro_path")
    for p in paths:
        S_m = float(np.mean(p.index_spread[:4]))
        sf = s_fair_now * S_m / S
        pd_spread = 1 - np.exp(-sf / (k * lgd))
        fr = fpath.loc[p.name]
        # Default risk the cases add: the share of debt that must refinance inside the horizon, times the chance
        # the market is shut to this issuer on the path, times the chance a failed refinancing defaults; plus the
        # liquidity shortfall channel. Probability, not the F6.3 cliff (the cliff still drives the claims view).
        need = sum(l.face for l in start.debt_lines if l.maturity_q) / max(1e-9, sum(l.face for l in start.debt_lines))
        p_shut = 1.0 - V0["refi_score_to_p"][refi_score(pts, p, 4, S, s_now)]
        pd_engine = (V0["p_default_given_refi_fail"] * need * p_shut
                     + V0["p_default_given_liq_short"] * float(fr.get("p_liq_short_8", 0.0)))
        pd12 = float(np.clip(max(pd_spread, pd_engine), 0.0005, 0.9))
        # Hedged convergence: the spread hedge removes the systematic move, so the bond converges on its own
        # residual scaled by the path, (s - s_fair_now) x S(m) / S. Express it as an effective target for hy.alpha.
        target = s_now - (s_now - s_fair_now) * S_m / S
        by.append({"macro_path": p.name, "p_path": p.prob, "s_fair": target, "s_fair_path": sf, "pd_12m": pd12,
                   "pd_source": "engine" if pd_engine > pd_spread else "spread", "index_el": S_m / k})
    by = pd.DataFrame(by)
    bond = alpha.BondInputs("5y", oas=s_now, spread_duration=spread_duration, rho_q=V0["rho_q"], beta_mkt=s_now / S,
                            index_spread=S, lgd=lgd if loss_given_default is None else loss_given_default,
                            bid_ask_bp=V0["bid_ask_bp"])
    a = alpha.expected_alpha(bond, by, h_years=V0["h_years"])
    f = feats.set_index("macro_path")
    table = by.set_index("macro_path").join(
        a["by_path"].set_index("macro_path")[["carry", "converge", "loss", "alpha"]]).join(
        f[[c for c in ("lev_fwd_4", "lev_fwd_8", "lev_fwd_sd", "lev_peak_down", "liq_min_down", "p_refi_4",
                       "refi_fail_share", "p_liq_short_8") if c in f]])
    wrow = f.loc["weighted"] if "weighted" in f.index else None
    # Case statistics on the most likely path (framework F6.8): drivers, peak leverage, lowest liquidity, the first
    # quarter with a liquidity shortfall, the first refinance failure, and wall cover at 4 quarters.
    modal = max(paths, key=lambda p: p.prob).name
    case_stats = []
    for cname, scn in cases.items():
        sp = grid.get((cname, modal))
        if sp is None:
            continue
        liq = np.asarray(sp.liquidity, dtype=float)
        short = np.nonzero(liq < 0)[0]
        case_stats.append({
            "case": cname, "weight": float(w[modal].get(cname, 0.0)) if hasattr(w[modal], "get") else float(dict(w[modal]).get(cname, 0.0)),
            "growth_q": float(np.mean(scn.g)), "cost_ratio": float(np.mean(scn.v + scn.a)), "capex_q": float(np.mean(scn.capex)),
            "lev_4": float(sp.leverage[3]), "lev_peak": float(np.nanmax(sp.leverage)), "liq_min": float(np.nanmin(liq)),
            "first_shortfall_q": int(short[0] + 1) if len(short) else None,
            "first_refi_fail_q": getattr(sp, "refi_fail_q", None),
            "wall_cover_4": float(sp.wall_cover[3]) if np.isfinite(sp.wall_cover[3]) else None,
            "ebitda_4": float(np.sum(sp.ebitda[:4])),
        })
    promoted = {m: bool(getattr(w[m], "promoted", False)) for m in w}
    severe_full = None
    if capex_committed_q is not None and "down_severe" in cases:
        from dataclasses import replace as _replace
        sev = cases["down_severe"]
        # Same severe drivers; capex scaled so that its base level is the committed capex instead of maintenance capex.
        ratio = capex_committed_q / drivers["capex"] if drivers["capex"] else 1.0
        sev_full = _replace(sev, name="down_severe_full_capex", capex=np.asarray(sev.capex, dtype=float) * ratio)
        mp = [p for p in paths if p.name == modal]
        g2 = forward.run_grid(start, {"down_severe_full_capex": sev_full}, mp, betas={"g": beta}, trend=V0["trend_gdp"],
                              forecast_rows=mac.paths.sources, s_fair_fn=s_fair_path, p_refi_access_fn=p_access,
                              forward_treasury_fn=fwd_t)
        sp = g2.get(("down_severe_full_capex", modal))
        if sp is not None:
            liq = np.asarray(sp.liquidity, dtype=float)
            short = np.nonzero(liq < 0)[0]
            severe_full = {"first_shortfall_q": int(short[0] + 1) if len(short) else None,
                           "liq_min": float(np.nanmin(liq)), "capex_q": float(np.mean(sev_full.capex))}
    fcf_by_path, fcf_severe = {}, {}
    for p in paths:
        wm = dict(w[p.name])
        acc = np.zeros(H)
        for cname in cases:
            sp = grid.get((cname, p.name))
            if sp is not None:
                acc += float(wm.get(cname, 0.0)) * np.asarray(sp.fcf, dtype=float)
        fcf_by_path[p.name] = (acc / max(1e-12, sum(float(wm.get(c, 0.0)) for c in cases if (c, p.name) in grid))).tolist()
        sev = grid.get(("down_severe", p.name))
        if sev is not None:
            fcf_severe[p.name] = np.asarray(sev.fcf, dtype=float).tolist()
    return {"table": table.reset_index(), "weighted": wrow, "alpha": {k: v for k, v in a.items() if k != "by_path"},
            "phase": mac.paths.phase, "archetype": archetype, "promoted": promoted, "refi_points": pts,
            "modal_path": modal, "case_stats": case_stats,
            "refi_score_by_path": {p.name: refi_score(pts, p, 4, S, s_now) for p in paths},
            "case_weights": {m: dict(w[m]) for m in w}, "fcf_by_path": fcf_by_path, "fcf_severe_by_path": fcf_severe,
            "severe_full_capex": severe_full}


def scenario_figure(name: str, ticker: str, sc_out: dict, path: Path) -> None:
    """Three panels by macro path: expected leverage in 4 quarters, refinancing risk, expected alpha (teaching)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = sc_out["table"]
    labels = [f"{m.replace('_', ' ')}\n({p:.0%})" for m, p in zip(t["macro_path"], t["p_path"])]
    x = np.arange(len(t))
    fig, ax = plt.subplots(1, 3, figsize=(13, 4.2))
    ax[0].bar(x, t["lev_fwd_4"], color="#4E79A7", yerr=t.get("lev_fwd_sd"), capsize=3)
    ax[0].set_title("Expected leverage in 4 quarters (x)\nbar = case-weighted mean; line = spread across cases", fontsize=9)
    ax[1].bar(x - 0.2, t["p_refi_4"], width=0.4, color="#F28E2B", label="Wall cover below 1 in 4 quarters")
    ax[1].bar(x + 0.2, t["refi_fail_share"], width=0.4, color="#B5403A", label="Refinance fails (F6.3)")
    ax[1].set_ylim(0, 1.05)
    ax[1].set_title("Refinancing risk (probability)", fontsize=9)
    ax[1].legend(fontsize=7, frameon=False)
    ann = t["alpha"] / V0["h_years"] * 1e4
    ax[2].bar(x, ann, color=np.where(ann >= 0, "#2E7D4F", "#B5403A"))
    ax[2].axhline(0, color="black", lw=0.6)
    wa = sc_out["alpha"]["alpha_net_bp_ann"]
    ax[2].axhline(wa, color="black", ls="--", lw=1)
    ax[2].text(len(t) - 0.5, wa, f" weighted, after cost: {wa:,.0f}", fontsize=8, va="bottom", ha="right")
    ax[2].set_title("Expected alpha, hedged 5-year bond (bp a year, before cost)\nconvergence to fair plus loss gap to the hedge", fontsize=9)
    for a_ in ax:
        a_.set_xticks(x)
        a_.set_xticklabels(labels, fontsize=7)
        a_.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"{name} ({ticker}) under each macro path; archetype {sc_out['archetype']}, phase {sc_out['phase']}",
                 x=0.01, ha="left", fontsize=11)
    fig.text(0.01, 0.005, "Paths: SPF, FOMC SEP, Treasury forwards, TRACE HY level. v0 rules for fair spread, PD, refi access: "
             "docs/decisions/2026-10-22-issuer-scenario-defaults.md", fontsize=7, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 0.94))
    fig.savefig(path, dpi=150)
    plt.close(fig)
