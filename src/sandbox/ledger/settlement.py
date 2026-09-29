"""Cross-subsidiary settlement manifest protocol face (BigDomain
explore queue item "cross-subsidiary settlement protocol", round
R601). Ownership anchors per the BLUEPRINT observation-payment note
(D-20260924-10): the 19.9 compute-pack family belongs to BigDomain
as the product owner; fulfillment engine = BigMoney (reference
only, never copied or rebuilt here); collection outlet = BigCompute
(reference only); the revenue split leaves the product side the
larger share - exact ratios are a needs-CEO approval face and are
NEVER encoded in this module or its shipped config.

Executable protocol contract (design-as-code):
  - a settlement window is a period string ("2026-10-01/P1D"
    style); exactly one manifest per period - window idempotent;
  - build_manifest() sums the window's settled sales rows (integer
    fen, non-negative) and fulfillment usage rows (integer units,
    claim inputs supplied by the engine face), then apportioned the
    sales total across parties by integer weights: floor division
    plus input-order remainder (deterministic, zero rounding loss -
    same integer law as the incentive allocator);
  - the manifest carries a sha256 id over its canonical payload
    plus the previous manifest id (hash chain), so a tamper of any
    field is detectable by verify_manifest();
  - claims are per (period, party), bounded by the apportioned
    amount, and bound to the manifest id - duplicate claims are
    rejected.

Red lines: this module never moves money or tokens (settlement
execution lives on the engine/outlet faces per the ownership note);
stdlib only, zero network, zero RNG, pure ASCII source.
Pre-registered criteria: AC-ST1..AC-ST7 = src/os/backlog.md R601 row.
"""

import hashlib
import json

E_ST_PERIOD_DUP = "E_ST_PERIOD_DUP"
E_ST_TAMPER = "E_ST_TAMPER"
E_ST_BAD_INPUT = "E_ST_BAD_INPUT"
SCHEMA = "bigdomain.settlement/1"


class SettlementError(Exception):
    """Protocol error with a stable machine code."""

    def __init__(self, code, detail=""):
        super().__init__("%s %s" % (code, detail))
        self.code = code
        self.detail = detail


def canonical(obj):
    """Deterministic JSON text: sorted keys, tight separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def digest(payload):
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def _rows_total(rows, key):
    total = 0
    for row in rows:
        if not isinstance(row, dict):
            raise SettlementError(E_ST_BAD_INPUT, "row must be a dict")
        value = row.get(key, 0)
        if not isinstance(value, int) or isinstance(value, bool) \
                or value < 0:
            raise SettlementError(E_ST_BAD_INPUT, "bad %s value" % key)
        total += value
    return total


def _apportion(total, parties, weights):
    """Integer split: floor + input-order remainder, zero loss."""
    weight_sum = 0
    for name in parties:
        weight = weights.get(name)
        if not isinstance(weight, int) or isinstance(weight, bool) \
                or weight < 0:
            raise SettlementError(E_ST_BAD_INPUT, "bad weight")
        weight_sum += weight
    if weight_sum <= 0:
        raise SettlementError(E_ST_BAD_INPUT,
                               "weight sum must be positive")
    out = {}
    for name in parties:
        out[name] = (total * weights[name]) // weight_sum
    remainder = total - sum(out.values())
    for name in parties:
        if remainder <= 0:
            break
        if weights[name] > 0:
            out[name] += 1
            remainder -= 1
    return out


def _build(period, sales_rows, usage_rows, parties, weights, prev_id):
    if not isinstance(period, str) or not period:
        raise SettlementError(E_ST_BAD_INPUT, "bad period")
    if not parties:
        raise SettlementError(E_ST_BAD_INPUT, "empty parties")
    sales_total = _rows_total(sales_rows, "amount_cent")
    usage_total = _rows_total(usage_rows, "units")
    manifest = {
        "schema": SCHEMA,
        "period": period,
        "sales_total_cent": sales_total,
        "usage_total_units": usage_total,
        "parties": list(parties),
        "weights": {name: weights[name] for name in parties},
        "apportioned_cent": _apportion(sales_total, parties, weights),
        "prev_id": prev_id,
    }
    manifest["id"] = digest(canonical(manifest))
    return manifest


class SettlementFace(object):
    """Per-window manifest builder + verifier + claim gate."""

    def __init__(self):
        self._windows = {}
        self._claims = {}
        self._last_id = None

    def build_manifest(self, period, sales_rows, usage_rows, parties,
                       weights):
        if period in self._windows:
            raise SettlementError(E_ST_PERIOD_DUP, period)
        manifest = _build(period, sales_rows, usage_rows, parties,
                          weights, self._last_id)
        self._windows[period] = manifest
        self._last_id = manifest["id"]
        return json.loads(json.dumps(manifest))  # handed-out copy

    def verify_manifest(self, manifest, sales_rows, usage_rows):
        if not isinstance(manifest, dict) or "id" not in manifest:
            raise SettlementError(E_ST_TAMPER, "manifest missing id")
        body = {key: value for key, value in manifest.items()
                if key != "id"}
        if manifest["id"] != digest(canonical(body)):
            raise SettlementError(E_ST_TAMPER, "id mismatch")
        rebuilt = _build(manifest.get("period"), sales_rows, usage_rows,
                         manifest.get("parties") or [],
                         manifest.get("weights") or {},
                         manifest.get("prev_id"))
        rebuilt_body = {key: value for key, value in rebuilt.items()
                        if key != "id"}
        if canonical(body) != canonical(rebuilt_body):
            raise SettlementError(E_ST_TAMPER, "rebuild mismatch")
        return True

    def claim(self, period, party, amount_cent):
        manifest = self._windows.get(period)
        if manifest is None:
            raise SettlementError(E_ST_BAD_INPUT, "unknown period")
        key = (period, party)
        if key in self._claims:
            raise SettlementError(E_ST_PERIOD_DUP,
                                  "%s/%s" % (period, party))
        apportioned = manifest["apportioned_cent"]
        if party not in apportioned:
            raise SettlementError(E_ST_BAD_INPUT, "unknown party")
        if not isinstance(amount_cent, int) \
                or isinstance(amount_cent, bool) or amount_cent < 0 \
                or amount_cent > apportioned[party]:
            raise SettlementError(E_ST_BAD_INPUT, "claim out of bounds")
        self._claims[key] = amount_cent
        return {"period": period, "party": party,
                "amount_cent": amount_cent, "manifest_id": manifest["id"]}

    def window_count(self):
        return len(self._windows)
