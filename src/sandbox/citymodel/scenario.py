"""City commerce dual-track scenario model (sandbox, pure stdlib).

Runnable evidence face for docs/spec/city-commerce-plan-v0.md sec.3
(dual-track pricing benchmark, P1 [needs-CEO]). Audit anchors:
group silicon-city problem audit 2026-10-02 L76 "pricing model =
zero on file" + M4 Steam publishing pre-research; dispatch chain
P-2026-10-02-02 (BigDomain not in exec face -> self-driven response,
v0 skeleton by R849, this module lands it as a runnable artifact).

The model COMPUTES scenarios. It makes no pricing decision:
- Track A (buyout + DLC, C:S1-style reference): no in-canon price
  anchor exists, so prices are strictly caller-supplied; omitting
  them fails closed. No invented price defaults.
- Track B (city subscription band): the only default prices are the
  in-canon entry-tier band 9.9 / 19.9 / 29.9 CNY (C-20260927-01
  case A, BLUEPRINT sec.4 C2/N2 canon rows).

All other parameters (units, attach rate, churn, mix, rates) are
caller-supplied scenario assumptions, never decisions.
"""

from __future__ import annotations

# In-canon subscription band anchor (C-20260927-01 case A).
TIER_PRICES = (9.9, 19.9, 29.9)
TIER_NAMES = ("growth_archive", "compute_pack", "entry_card")


class ParamError(ValueError):
    """Fail-closed scenario parameter gate."""


def _pos(value, name):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ParamError("param %s must be numeric" % name)
    if value < 0:
        raise ParamError("param %s must be >= 0, got %r" % (name, value))
    return float(value)


def _frac(value, name):
    v = _pos(value, name)
    if v > 1.0:
        raise ParamError("param %s must be a fraction <= 1.0, got %r" % (name, v))
    return v


def validate(params):
    """Fail-closed gate: every field checked before any math runs."""
    if not isinstance(params, dict):
        raise ParamError("params must be a dict")
    ta = params.get("track_a")
    if not isinstance(ta, dict):
        raise ParamError("track_a must be a dict")
    # Track A prices are REQUIRED: no in-canon anchor -> caller supplies.
    for key in ("buyout_price", "dlc_price"):
        if key not in ta:
            raise ParamError("track_a.%s required (no in-canon anchor, "
                             "caller must supply)" % key)
        _pos(ta[key], "track_a." + key)
    _frac(ta.get("attach_rate", 0), "track_a.attach_rate")
    _pos(ta.get("units_per_month", 0), "track_a.units_per_month")
    tb = params.get("track_b")
    if not isinstance(tb, dict):
        raise ParamError("track_b must be a dict")
    prices = tuple(tb.get("tier_prices", TIER_PRICES))
    if len(prices) != 3:
        raise ParamError("track_b.tier_prices must have 3 tiers")
    for p in prices:
        _pos(p, "track_b.tier_prices")
    mix = tuple(tb.get("tier_mix", (0.5, 0.3, 0.2)))
    if len(mix) != 3:
        raise ParamError("track_b.tier_mix must have 3 shares")
    for m in mix:
        _frac(m, "track_b.tier_mix")
    if abs(sum(mix) - 1.0) > 1e-9:
        raise ParamError("track_b.tier_mix shares must sum to 1.0")
    _frac(tb.get("monthly_churn", 0), "track_b.monthly_churn")
    _pos(tb.get("new_subs_per_month", 0), "track_b.new_subs_per_month")
    _pos(tb.get("starting_subs", 0), "track_b.starting_subs")
    f = params.get("funnel")
    if not isinstance(f, dict):
        raise ParamError("funnel must be a dict")
    _pos(f.get("visitors", 0), "funnel.visitors")
    _frac(f.get("register_rate", 0), "funnel.register_rate")
    _frac(f.get("paid_rate", 0), "funnel.paid_rate")
    return True


def project_track_a(params, months):
    """Buyout + DLC monthly projection (C:S1-style reference track)."""
    validate(params)
    if not isinstance(months, int) or months < 1:
        raise ParamError("months must be an int >= 1")
    ta = params["track_a"]
    units = ta["units_per_month"]
    gross = units * ta["buyout_price"] + units * ta["attach_rate"] * ta["dlc_price"]
    rows, cum = [], 0.0
    for m in range(1, months + 1):
        cum = round(cum + gross, 2)
        rows.append({"month": m, "units": units, "gross": round(gross, 2),
                     "cumulative": cum})
    return {"rows": rows, "gross_total": cum}


def project_track_b(params, months):
    """City subscription band: per-tier churn decay + new inflow."""
    validate(params)
    if not isinstance(months, int) or months < 1:
        raise ParamError("months must be an int >= 1")
    tb = params["track_b"]
    prices = tuple(tb.get("tier_prices", TIER_PRICES))
    mix = tuple(tb.get("tier_mix", (0.5, 0.3, 0.2)))
    churn = tb["monthly_churn"]
    newsubs = tb["new_subs_per_month"]
    subs = [tb["starting_subs"] * share for share in mix]
    rows, cum = [], 0.0
    for m in range(1, months + 1):
        subs = [s * (1.0 - churn) + newsubs * share for s, share in zip(subs, mix)]
        mrr = round(sum(s * p for s, p in zip(subs, prices)), 2)
        cum = round(cum + mrr, 2)
        rows.append({"month": m, "subs_total": round(sum(subs), 4),
                     "mrr": mrr, "cumulative": cum})
    return {"rows": rows, "mrr_total": cum,
            "tiers": [dict(name=n, price=p) for n, p in zip(TIER_NAMES, prices)]}


def funnel(params):
    """Free-layer conversion chain: visitors -> registered -> paid."""
    validate(params)
    f = params["funnel"]
    visitors = f["visitors"]
    registered = visitors * f["register_rate"]
    paid = registered * f["paid_rate"]
    # Identity is structural; assert it anyway (fail-closed hygiene).
    assert paid <= registered + 1e-9 <= visitors + 1e-9
    return {"visitors": visitors, "registered": round(registered, 2),
            "paid": round(paid, 2)}


def breakeven_month(projection, fixed_cost):
    """First month where cumulative revenue covers fixed_cost, else None."""
    cost = _pos(fixed_cost, "fixed_cost")
    for row in projection["rows"]:
        if row["cumulative"] - cost >= -1e-9:
            return row["month"]
    return None


def sensitivity_grid(params, months, price_steps):
    """Track A gross revenue vs buyout price steps (ceteris paribus)."""
    validate(params)
    steps = list(price_steps)
    if not steps:
        raise ParamError("price_steps must be non-empty")
    grid = []
    for price in steps:
        p = _pos(price, "price_step")
        alt = {**params, "track_a": {**params["track_a"], "buyout_price": p}}
        grid.append({"buyout_price": round(p, 2),
                     "gross_total": project_track_a(alt, months)["gross_total"]})
    for i in range(1, len(grid)):
        assert grid[i]["gross_total"] >= grid[i - 1]["gross_total"]
    return grid


COMPLIANCE_HEADER = (
    "== City Commerce Dual-Track Scenario (sandbox v0.1) ==\n"
    "[needs-CEO] pricing adjudication pending: model computes, never "
    "decides; all scenario prices are caller-supplied assumptions "
    "(Track B defaults cite in-canon band 9.9/19.9/29.9 CNY only).\n"
    "NON-INVESTMENT-ADVISORY: internal adjudication evidence only; "
    "not investment advice; figures are parameterized scenarios, not "
    "forecasts or commitments.\n"
    "AI-GENERATED LABEL: output of deterministic code; every "
    "presentation surface carrying this report must keep the AIGC "
    "label face (BLUEPRINT sec.5 compliance chain).\n"
)


def render_report(params, months):
    """Deterministic ASCII report; same inputs -> byte-identical text."""
    fa = project_track_a(params, months)
    fb = project_track_b(params, months)
    fu = funnel(params)
    lines = [COMPLIANCE_HEADER.rstrip("\n")]
    lines.append("horizon: %d months" % months)
    lines.append("track_a gross_total: %.2f" % fa["gross_total"])
    lines.append("track_b mrr_total: %.2f" % fb["mrr_total"])
    lines.append("track_b tiers: %s" % ", ".join(
        "%s=%.2f" % (t["name"], t["price"]) for t in fb["tiers"]))
    for row in fa["rows"]:
        lines.append("  A m%-3d units=%-8d gross=%-12.2f cum=%.2f"
                     % (row["month"], row["units"], row["gross"],
                        row["cumulative"]))
    for row in fb["rows"]:
        lines.append("  B m%-3d subs=%-12.4f mrr=%-10.2f cum=%.2f"
                     % (row["month"], row["subs_total"], row["mrr"],
                        row["cumulative"]))
    lines.append("funnel: visitors=%(visitors).2f registered=%(registered).2f "
                 "paid=%(paid).2f" % fu)
    lines.append("combined_gross: %.2f"
                 % round(fa["gross_total"] + fb["mrr_total"], 2))
    return "\n".join(lines) + "\n"
