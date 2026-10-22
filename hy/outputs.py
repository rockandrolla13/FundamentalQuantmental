"""Output layer: the five table schemas and the no-look-ahead check (methodology Section 10).

Field names match Section 10 exactly. A field written `name[]` in the
methodology is a list column named `name`; `q_vector[10]` is a list of ten.
Every table carries `date` and `available_at` (Section 10, first paragraph),
so `validate_frame` can refuse a row that the market could not see on its date.

`bond_daily` and `issuer_state` carry one row per macro path and one row named
"weighted" per entity and date (Section 5.4; Section 9.2). `p_path` on the path
rows is the posterior path probability and sums to one per entity and date.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from hy.inputs import LookAheadError

WEIGHTED = "weighted"
PATH_TOL = 1e-6

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "data" / "schemas"


class SchemaError(ValueError):
    """Raised when a frame misses a required column of its Section 10 table."""


@dataclass(frozen=True)
class TableSpec:
    """One Section 10 table: name, grain, key columns, and every column in order."""

    name: str
    section: str
    grain: str
    keys: tuple[str, ...]
    columns: tuple[str, ...]
    weighted_row: bool = False


def _cols(*groups: tuple[str, ...]) -> tuple[str, ...]:
    out: list[str] = []
    for g in groups:
        for c in g:
            if c not in out:
                out.append(c)
    return tuple(out)


STAMP = ("date", "available_at")

BOND_DAILY = TableSpec(
    "bond_daily",
    "10.1",
    "one row per bond per day",
    ("date", "cusip", "macro_path"),
    _cols(
        STAMP,
        ("date", "cusip", "issuer_id", "tranche_id", "macro_path", "p_path"),
        ("price_mid", "oas", "ytw", "spread_duration", "mod_duration", "bid_ask_bp", "adv"),
        ("s_el", "kappa_t", "s_anchor", "eta_sector_t", "s_fair"),
        ("resid_bp", "resid_log", "sigma_x", "z", "q_alpha_t", "flag_cheap", "flag_rich",
         "rho", "half_life", "exp_conv_ret_h", "event_contaminated"),
        ("alpha_h_years", "alpha_carry", "alpha_converge", "alpha_loss", "alpha_event", "alpha_cost",
         "exp_alpha", "exp_alpha_bp_ann", "alpha_sd", "info_ratio", "passes_g3"),
        ("s1", "s2", "s3", "s4", "s5", "s6", "s7", "composite", "force_rank", "replaces_position"),
        ("beta_mkt", "beta_g", "beta_p", "sdv01_per_mm", "rdv01_eff_per_mm"),
        ("pd_12m", "pd_5y", "lgd_k_adj", "recovery_price_k", "jtd_per_mm", "el_h"),
        ("next_event_type", "next_event_date", "event_var_alpha", "worst_outcome_pnl"),
    ),
    weighted_row=True,
)

ISSUER_STATE = TableSpec(
    "issuer_state",
    "10.2",
    "one row per issuer per filing or re-estimate",
    ("date", "issuer_id", "macro_path"),
    _cols(
        ("date", "issuer_id", "filing_date", "available_at", "forecast_source"),
        ("macro_path", "p_path", "w_down", "phase", "forecast_vintage"),
        ("ebitda_adj_analyst", "addback_gap", "covenant_gap", "margin", "margin_trend", "margin_peer_gap",
         "organic_growth", "book_to_bill", "surprise", "eq_flags_sum"),
        ("fcf", "fcf_conversion", "fcf_to_debt", "cash_cycle", "payable_days_trend", "liquidity_L", "runway_q",
         "wall_cover_4", "wall_cover_8", "capex_flex", "refi_access"),
        ("lev_adj_total", "net_lev", "coverage", "lev_lease_adj", "debt_adj"),
        ("q_vector", "q_score", "mgmt_change", "sponsor_behavior"),
        ("rating_agency", "rating_model", "gap_rating", "H_t", "test_date", "rp_capacity", "debt_capacity",
         "lien_capacity", "investment_capacity"),
        ("lev_fwd_4", "lev_fwd_8", "delev_4", "lev_fwd_sd_4", "lev_peak_down", "liq_min_down", "p_breach_4",
         "p_liq_short_8", "p_refi_4", "fcf_debt_fwd", "cov_fwd_4", "rev_lev", "gap_consensus", "gap_mgmt", "w_down"),
        ("lev_fwd_sd", "refi_fail_share", "pd_12m", "s_fair"),
        ("tev_low", "tev_mid", "tev_high", "tev_default", "v_sigma", "lme_score", "pi_lme"),
    ),
    weighted_row=True,
)

TRANCHE_STATE = TableSpec(
    "tranche_state",
    "10.3",
    "one row per tranche per issuer update",
    ("date", "tranche_id"),
    _cols(
        STAMP,
        ("tranche_id", "rank", "tranche_type", "issuer_entity"),
        ("lev_face_k", "lev_mkt_k", "ltv_k_low", "ltv_k_mid", "ltv_k_high"),
        ("recovery_k", "recovery_k_adj", "lgd_k_adj", "recovery_price_k"),
        ("spt_observed", "spt_model", "s4_pairs"),
        ("coc_put_price", "coc_fall_away", "call_state", "lme_score_k"),
    ),
)

EVENT_MATRIX = TableSpec(
    "event_matrix",
    "10.4",
    "one row per position, event, outcome, and macro path",
    ("date", "position_id", "event_id", "outcome", "macro_path"),
    _cols(
        STAMP,
        ("date", "position_id", "cusip"),
        ("event_id", "event_type", "event_date", "date_confirmed"),
        ("outcome", "macro_path"),
        ("p_path", "p_outcome_given_path"),
        ("dspread_bp", "dpnl"),
        ("dy_growth", "dy_policy", "ds_sys"),
        ("features_delta",),
    ),
)

PORTFOLIO_RISK = TableSpec(
    "portfolio_risk",
    "10.5",
    "one row per day",
    ("date",),
    _cols(
        STAMP,
        ("gross", "net", "sdv01_total", "rdv01_eff_total", "beta_mkt_net", "beta_g", "beta_p"),
        ("jtd_by_issuer", "jtd_by_sector_driver", "el_h_total"),
        ("pnl_by_macro_path", "event_var_alpha", "worst_event_pnl", "worst_event_id"),
        ("cdx_notional", "sector_basket_notional", "tsy_futures_dv01", "residual_basis"),
        ("jtd_limit_utilisation", "wall_limit_utilisation", "correlated_event_utilisation", "band_gate_scale"),
        ("cycle_phase", "w_down_universe_mean", "kappa_t", "q_alpha_t_mean"),
    ),
)

TABLES: dict[str, TableSpec] = {t.name: t for t in (BOND_DAILY, ISSUER_STATE, TRANCHE_STATE, EVENT_MATRIX, PORTFOLIO_RISK)}

# JSON types. Every column not listed is a nullable number.
_DATETIME = {"date", "available_at", "filing_date", "test_date", "event_date", "next_event_date", "forecast_vintage"}
_STRING = {
    "cusip", "issuer_id", "tranche_id", "replaces_position", "next_event_type", "forecast_source", "sponsor_behavior",
    "rating_agency", "rating_model", "tranche_type", "issuer_entity", "call_state", "position_id", "event_id",
    "event_type", "outcome", "macro_path", "worst_event_id", "cycle_phase", "phase",
}
_BOOLEAN = {"flag_cheap", "flag_rich", "event_contaminated", "date_confirmed", "coc_fall_away", "mgmt_change"}
_INTEGER = {"force_rank", "rank"}
_NUM_ARRAY = {"q_vector", "spt_observed", "spt_model", "s4_pairs", "features_delta", "sector_basket_notional"}
_NUM_MAP = {"jtd_by_issuer", "jtd_by_sector_driver", "pnl_by_macro_path"}


def _json_type(col: str) -> dict:
    if col in _DATETIME:
        return {"type": ["string", "null"], "format": "date-time"}
    if col in _STRING:
        return {"type": ["string", "null"]}
    if col in _BOOLEAN:
        return {"type": ["boolean", "null"]}
    if col in _INTEGER:
        return {"type": ["integer", "null"]}
    if col in _NUM_ARRAY:
        spec: dict = {"type": ["array", "null"], "items": {"type": ["number", "null"]}}
        if col == "q_vector":
            spec |= {"minItems": 10, "maxItems": 10}
        return spec
    if col in _NUM_MAP:
        return {"type": ["object", "null"], "additionalProperties": {"type": "number"}}
    return {"type": ["number", "null"]}


def json_schema(table: str) -> dict:
    """JSON Schema (draft 2020-12) for one Section 10 table. Intuition: a reader traces each field to its formula by name."""
    t = TABLES[table]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"hy/{t.name}.json",
        "title": t.name,
        "description": f"Methodology Section {t.section}: {t.grain}. Rule: available_at <= date.",
        "type": "object",
        "properties": {c: _json_type(c) for c in t.columns},
        "required": list(t.columns),
        "x-keys": list(t.keys),
        "additionalProperties": True,
    }


def write_json_schemas(out_dir: Path | str = SCHEMA_DIR) -> list[Path]:
    """Write data/schemas/<table>.json for the five Section 10 tables. Returns the paths written.

    Intuition: schemas live in git; vendor data does not (CLAUDE.md engineering rules).
    """
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in TABLES:
        p = d / f"{name}.json"
        p.write_text(json.dumps(json_schema(name), indent=2) + "\n")
        paths.append(p)
    return paths


def _check_path_rows(df: pd.DataFrame, t: TableSpec) -> None:
    """Check the macro path rows of a per-path table (Section 5.4; Section 9.2).

    For each entity key and date: exactly one row has macro_path == "weighted", and
    sum over the other rows of p_path = 1 within PATH_TOL. Groups with no macro_path
    value at all are single-path rows from before the path set; the check skips them.
    A group that mixes empty and named macro_path values fails.
    Intuition: the weighted row is the expectation over the paths, so it needs exactly one
    copy, and the path weights under it must be a distribution.
    """
    ent = [k for k in t.keys if k != "macro_path"]
    for key, g in df.groupby(ent, dropna=False, sort=False):
        mp = g["macro_path"]
        if mp.isna().all():
            continue
        if mp.isna().any():
            raise SchemaError(f"{t.name}: {dict(zip(ent, key))} mixes empty and named macro_path rows")
        n_w = int((mp == WEIGHTED).sum())
        if n_w != 1:
            raise SchemaError(f"{t.name}: {dict(zip(ent, key))} has {n_w} weighted rows, need exactly 1")
        paths = g.loc[mp != WEIGHTED]
        if paths.empty:
            raise SchemaError(f"{t.name}: {dict(zip(ent, key))} has a weighted row but no path rows")
        if paths["macro_path"].duplicated().any():
            raise SchemaError(f"{t.name}: {dict(zip(ent, key))} repeats a macro path")
        p = pd.to_numeric(paths["p_path"], errors="coerce")
        if p.isna().any() or (p < -PATH_TOL).any() or abs(float(p.sum()) - 1.0) > PATH_TOL:
            raise SchemaError(f"{t.name}: {dict(zip(ent, key))} p_path sums to {float(p.sum())}, not 1")


def _check_event_paths(df: pd.DataFrame) -> None:
    """Check sum_m p(m) = 1 per (date, position, event, outcome) in event_matrix (Section 10.4).

    Rows with an empty p_path are skipped. Intuition: each outcome row set spans the whole path distribution.
    """
    p = pd.to_numeric(df["p_path"], errors="coerce")
    if p.isna().all():
        return
    s = p.groupby([df["date"], df["position_id"], df["event_id"], df["outcome"]], dropna=False).sum(min_count=1).dropna()
    bad = s[(s - 1.0).abs() > PATH_TOL]
    if not bad.empty:
        raise SchemaError(f"event_matrix: p_path does not sum to 1 for {bad.index.tolist()[:5]}")


def validate_frame(df: pd.DataFrame, table: str) -> pd.DataFrame:
    """Check required columns, available_at <= date on every row, and the macro path rows (Section 10; Section 11, Inputs row).

    Raises SchemaError on a missing column, LookAheadError on a row the market could not see on its date,
    and SchemaError when a per-path table has a missing or duplicate weighted row or a p_path leak.
    Returns the frame unchanged. Intuition: an output stamped before its inputs existed is a backtest that lies.
    """
    if table not in TABLES:
        raise SchemaError(f"unknown table {table!r}; known: {sorted(TABLES)}")
    t = TABLES[table]
    missing = [c for c in t.columns if c not in df.columns]
    if missing:
        raise SchemaError(f"{table}: missing columns {missing}")
    date = pd.to_datetime(df["date"])
    avail = pd.to_datetime(df["available_at"])
    if avail.isna().any() or date.isna().any():
        raise SchemaError(f"{table}: date and available_at must be set on every row")
    late = avail > date
    if late.any():
        rows = df.index[late.to_numpy()].tolist()
        raise LookAheadError(f"{table}: available_at after date on rows {rows[:10]}")
    if t.weighted_row:
        _check_path_rows(df, t)
    elif table == "event_matrix":
        _check_event_paths(df)
    return df


if __name__ == "__main__":
    for p in write_json_schemas():
        print(p)
