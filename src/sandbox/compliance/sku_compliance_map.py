"""SKU x compliance-obligation map gate (seat-7 rider, A-tier pre-launch gate).

Rider chain: C-20260927-02 guardrails + C-20260927-01 decision-3 (case A).
Before any A-tier SKU goes live, the paid-point x compliance-obligation
mapping table must pass five columns: AIGC marking / renewal-refund &
prepaid liability / minor limits / probability disclosure N8 /
advertising-law copy self-check. No billing before the table passes.
The BigCompute joint co-sign column stays pending until their side
signs (their dispatch: SKU + funnel quota + compliance column).

Data (UTF-8, Chinese text) lives in sku_compliance_map.json; this module
stays pure ASCII per the repo encoding law. Structural verification
passing here is NOT the table passing: the billing gate stays closed
while the co-sign column is pending.

Usage: python sku_compliance_map.py            -> verify + render (exit 0/2)
       python sku_compliance_map.py --render   -> render markdown table only
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "sku_compliance_map.json"

COSIGN_KEY = "bigcompute_cosign"
A_TIER_EXPECTED_IDS = ("C2-B", "C2-C")


class MapError(Exception):
    """Raised when the compliance map data is structurally invalid."""


def load_map():
    """Load and hydrate the JSON data (pending cells get default text)."""
    with open(DATA_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    default = data["meta"]["pending_cell_default"]
    cols = data["meta"]["column_keys"]
    for row in data["in_force_skus"]:
        for key in cols:
            cell = row["cells"][key]
            if cell.get("status") == "pending" and not cell.get("obligation"):
                cell["obligation"] = default
    return data


def _keywords(data, name):
    return data["meta"]["invariants"][name]


def verify_registry(data):
    """Check in-force registry completeness (keys, counts, uniqueness)."""
    problems = []
    meta = data["meta"]
    all_rows = data["in_force_skus"]
    if len(all_rows) != meta["in_force_count"]:
        problems.append("in-force count %d != declared %d"
                        % (len(all_rows), meta["in_force_count"]))
    ids = [row["id"] for row in all_rows]
    if len(ids) != len(set(ids)):
        problems.append("duplicate sku ids in registry")
    counts = {}
    for row in all_rows:
        counts[row["family"]] = counts.get(row["family"], 0) + 1
        if set(row["cells"].keys()) != set(meta["column_keys"]):
            problems.append("row %s: column key set mismatch" % row["id"])
        if COSIGN_KEY not in row:
            problems.append("row %s: missing cosign key" % row["id"])
        for key in meta["column_keys"]:
            cell = row["cells"][key]
            if cell.get("status") not in ("filled", "pending"):
                problems.append("row %s col %s: bad status" % (row["id"], key))
            if not str(cell.get("obligation", "")).strip():
                problems.append("row %s col %s: empty obligation"
                                % (row["id"], key))
    for family, expected in meta["family_counts"].items():
        if counts.get(family, 0) != expected:
            problems.append("family %s count %d != declared %d"
                            % (family, counts.get(family, 0), expected))
    return problems


def verify_a_tier(data):
    """Check A-tier rows: five columns filled + invariant keywords + cosign."""
    problems = []
    meta = data["meta"]
    a_ids = list(meta["a_tier_skus"])
    if sorted(a_ids) != sorted(A_TIER_EXPECTED_IDS):
        problems.append("a-tier id set mismatch: %s" % a_ids)
    by_id = {row["id"]: row for row in data["in_force_skus"]}
    pending_token = _keywords(data, "cosign_pending_token")
    for sku in a_ids:
        row = by_id.get(sku)
        if row is None:
            problems.append("a-tier sku %s missing from registry" % sku)
            continue
        for key in meta["column_keys"]:
            cell = row["cells"][key]
            if cell["status"] != "filled":
                problems.append("a-tier %s col %s not filled" % (sku, key))
        for key, kw_name, mode in (
            ("renewal_refund_prepaid", "a_tier_refund_keywords", "all"),
            ("aigc_mark", "a_tier_aigc_keywords_any", "any"),
            ("copy_56", "a_tier_copy_keywords_any", "any"),
        ):
            text = row["cells"][key]["obligation"]
            words = _keywords(data, kw_name)
            if mode == "all":
                missing = [word for word in words if word not in text]
            else:
                missing = [] if any(word in text for word in words) else words
            for word in missing:
                problems.append("a-tier %s col %s missing keyword %r"
                                % (sku, key, word))
        if row[COSIGN_KEY]["status"] != pending_token:
            problems.append("a-tier %s cosign status unexpected: %r"
                            % (sku, row[COSIGN_KEY]["status"]))
    return problems


def billing_gate_open(data):
    """Seat-7 rider enforcement: no billing until the table passes.

    Gate opens only when every A-tier row has all five columns filled
    AND the BigCompute co-sign column is signed (not the pending token).
    Returns (open: bool, reasons: list[str]).
    """
    meta = data["meta"]
    pending_token = _keywords(data, "cosign_pending_token")
    by_id = {row["id"]: row for row in data["in_force_skus"]}
    reasons = []
    for sku in meta["a_tier_skus"]:
        row = by_id.get(sku)
        if row is None:
            reasons.append("a-tier sku %s missing" % sku)
            continue
        for key in meta["column_keys"]:
            if row["cells"][key]["status"] != "filled":
                reasons.append("%s: column %s not filled" % (sku, key))
        if row[COSIGN_KEY]["status"] == pending_token:
            reasons.append("%s: BigCompute co-sign pending" % sku)
    return (not reasons), reasons


def render_markdown(data):
    """Render the human-facing mapping table (gate deliverable)."""
    meta = data["meta"]
    cols = meta["column_keys"]
    labels = meta["column_labels"]
    lines = []
    header = ["id", "paid point", "price ref"]
    header += [labels[key] for key in cols]
    header += [meta["cosign_label"]]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))
    for row in data["in_force_skus"]:
        cells = []
        for key in cols:
            cell = row["cells"][key]
            cells.append(cell["obligation"] if cell["status"] == "filled"
                         else "[%s] %s" % (cell["status"], cell["obligation"]))
        cells.append(row[COSIGN_KEY]["status"])
        first = [row["id"], row["name"], row["price_ref"]]
        lines.append("| " + " | ".join(first + cells) + " |")
    lines.append("")
    lines.append("## Pending pool (not in-force yet; no compliance row due)")
    for item in data["pending_pool"]:
        lines.append("- %s %s -- %s" % (item["id"], item["name"],
                                        item["status"]))
    open_, reasons = billing_gate_open(data)
    lines.append("")
    if open_:
        lines.append("BILLING GATE: OPEN")
    else:
        lines.append("BILLING GATE: CLOSED -- no billing before table pass")
        for reason in reasons:
            lines.append("- reason: %s" % reason)
    return "\n".join(lines)


def main(argv):
    data = load_map()
    if "--render" in argv:
        print(render_markdown(data))
        return 0
    problems = verify_registry(data) + verify_a_tier(data)
    if problems:
        print("VERIFY FAIL (%d problems):" % len(problems))
        for problem in problems:
            print("- %s" % problem)
        return 2
    open_, reasons = billing_gate_open(data)
    print("VERIFY PASS: registry=%d in-force rows, a-tier=%s"
          % (data["meta"]["in_force_count"],
             ",".join(data["meta"]["a_tier_skus"])))
    print("BILLING GATE: %s (%d blocking reasons)"
          % ("OPEN" if open_ else "CLOSED", len(reasons)))
    print("")
    print(render_markdown(data))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
