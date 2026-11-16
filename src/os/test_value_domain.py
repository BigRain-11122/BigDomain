"""Battery suite for tools/value_domain.py - criteria AC-VDB1..AC-VDB8.

WHY (D-20261116-13, deadline 2026-11-17 12:00): every --check that reads green
must carry at least one VALUE-DOMAIN assertion - a price, entitlement, period or
quota compared against the catalog - and the four price faces must get it from
ONE reusable module rather than four copies. R2816 measured three faces printing
PASS over a landed price_cent=1990 against a config reading 990.

WHAT IS PROVED HERE, and how: each criterion is driven in this process against
the REAL catalog (read-only) and against TAMPERED copies held in memory, so a
red path is measured rather than asserted. The per-face leg uses each face's
OWN landed document, so the teeth are shown on production bytes even though no
face is re-run with a tampered artifact inside this budget.

Read-only. ASCII source. No network.
"""
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TOOLS = os.path.join(ROOT, "tools")
MATRIX = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
sys.path.insert(0, TOOLS)

import value_domain as VD  # noqa: E402

DECLARED = 9

FACES = [
    ("payment_gate_report.py", os.path.join(ROOT, "preview", "payment-gate-report.json")),
    ("money_path_demo.py", os.path.join(ROOT, "preview", "money-path-demo.json")),
    ("membership_face.py", os.path.join(ROOT, "preview", "membership-face.json")),
    ("membership_benefit_report.py",
     os.path.join(ROOT, "preview", "membership-benefit-report.json")),
]

results = []


def record(cid, ok, detail):
    results.append((cid, bool(ok), detail))


def snap(path):
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as fh:
        data = fh.read()
    return (len(data), hashlib.sha256(data).hexdigest()[:16])


def read_json(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def product_row_ids(doc):
    """The product rows this document carries, whatever it calls them."""
    for key in ("products", "catalogue", "product_rows"):
        rows = doc.get(key)
        if isinstance(rows, list) and rows:
            return rows
    return []


def tier_rows_of(doc):
    tiers = doc.get("tiers")
    if isinstance(tiers, dict) and tiers:
        return tiers
    facts = doc.get("facts")
    if isinstance(facts, dict):
        tiers = facts.get("tiers")
        if isinstance(tiers, dict) and tiers:
            return tiers
    return {}


def run():
    cat = VD.catalog(ROOT)
    products = cat["products"]
    tiers = cat["tiers"]

    # AC-VDB1 (AC-VD1): the shared module reads a real catalog, by value.
    record("AC-VDB1",
           "birthright_entry" in products and "tier_patron_30d" in products
           and int(products["birthright_entry"]["price_cent"]) !=
               int(products["tier_patron_30d"]["price_cent"])
           and (tiers.get("patron") or {}).get("period_days") == 30,
           "products=%d tiers=%d perm=%s month=%s period=%s" % (
               len(products), len(tiers),
               products.get("birthright_entry", {}).get("price_cent"),
               products.get("tier_patron_30d", {}).get("price_cent"),
               (tiers.get("patron") or {}).get("period_days")))

    # AC-VDB2 (AC-VD2): a wrong price is red and NAMES the product.
    rows = [{"id": pid, "price_cent": row["price_cent"]}
            for pid, row in sorted(products.items())]
    clean = VD.product_failures(rows, cat, ("price_cent",))
    tampered = [dict(r) for r in rows]
    victim = next(r for r in tampered if r["id"] == "birthright_entry")
    victim["price_cent"] = 1990
    dirty = VD.product_failures(tampered, cat, ("price_cent",))
    record("AC-VDB2",
           not clean and len(dirty) == 1 and "birthright_entry" in dirty[0],
           "clean=%d dirty=%d first=%s" % (
               len(clean), len(dirty), dirty[0] if dirty else "-"))

    # AC-VDB3 (AC-VD3): config drift reddens without any row being wrong.
    drift = VD.config_drift("0" * 64, cat, "pay_sha256")
    same = VD.config_drift(cat["pay_sha256"], cat, "pay_sha256")
    record("AC-VDB3",
           len(drift) == 1 and "config drift" in drift[0] and not same,
           "drift=%d same=%d" % (len(drift), len(same)))

    # AC-VDB4 (AC-VD4): period AND quota compared against the catalog.
    trows = {k: {"period_days": v["period_days"],
                 "monthly_credits": v["monthly_credits"],
                 "privileges": list(v["privileges"])}
             for k, v in sorted(tiers.items())}
    tclean = VD.tier_failures(trows, cat)
    tamp = json.loads(json.dumps(trows))
    tamp["patron"]["period_days"] = 99
    tdirty = VD.tier_failures(tamp, cat)
    tamp2 = json.loads(json.dumps(trows))
    tamp2["patron"]["privileges"] = ["free_money"]
    pdirty = VD.tier_failures(tamp2, cat)
    record("AC-VDB4",
           not tclean and len(tdirty) == 1 and "patron" in tdirty[0]
           and len(pdirty) == 1 and "privileges" in pdirty[0],
           "clean=%d period=%d priv=%d" % (len(tclean), len(tdirty), len(pdirty)))

    # AC-VDB5: structural green cannot pass - comparing nothing is RED.
    empty_required = VD.product_failures([], cat, ("price_cent",))
    empty_optional = VD.product_failures([], cat, ("price_cent",), require_one=False)
    record("AC-VDB5",
           len(empty_required) == 1 and "no product row was compared" in empty_required[0]
           and not empty_optional,
           "required=%d optional=%d" % (len(empty_required), len(empty_optional)))

    # AC-VDB6 (AC-VD6): each face's OWN landed document has teeth.
    seen, teeth = [], []
    for name, path in FACES:
        if not os.path.isfile(path):
            teeth.append("%s:MISSING" % name)
            continue
        doc = read_json(path)
        prows = product_row_ids(doc)
        if prows:
            live = [{"id": r.get("id"), "price_cent": r.get("price_cent")}
                    for r in prows if r.get("price_cent") is not None]
            bad = [dict(r) for r in live]
            if bad:
                bad[0]["price_cent"] = int(bad[0]["price_cent"]) + 7
                fails = VD.product_failures(bad, cat, ("price_cent",),
                                            require_one=False)
                seen.append("%s:p%d" % (name, len(live)))
                teeth.append("%s:%s" % (name, "RED" if fails else "GREEN"))
            else:
                teeth.append("%s:NOPRICE" % name)
        else:
            trows_l = tier_rows_of(doc)
            if trows_l:
                bad = json.loads(json.dumps(trows_l))
                first = sorted(bad)[0]
                bad[first]["period_days"] = int(bad[first].get("period_days") or 0) + 5
                fails = VD.tier_failures(bad, cat, require_one=False)
                seen.append("%s:t%d" % (name, len(trows_l)))
                teeth.append("%s:%s" % (name, "RED" if fails else "GREEN"))
            else:
                teeth.append("%s:NOROW" % name)
    record("AC-VDB6",
           len(seen) == 4 and all(t.endswith(":RED") for t in teeth),
           "seen=%s teeth=%s" % (",".join(seen), ",".join(teeth)))

    # AC-VDB7 (AC-VD7): ONE module, FOUR importers, each calling it.
    wiring = []
    for name, _ in FACES:
        path = os.path.join(TOOLS, name)
        text = io.open(path, encoding="utf-8", errors="replace").read()
        wired = ("import value_domain as VD" in text
                 and ("VD.product_failures" in text
                      or "VD.tier_failures" in text
                      or "VD.config_drift" in text))
        wiring.append("%s:%s" % (name, "OK" if wired else "NO"))
    record("AC-VDB7", all(w.endswith(":OK") for w in wiring), ",".join(wiring))

    # AC-VDB8: this suite is registered with the count it actually records.
    row = None
    if os.path.isfile(MATRIX):
        text = io.open(MATRIX, encoding="utf-8", errors="replace").read()
        for line in text.splitlines():
            if "test_value_domain.py" in line:
                row = line
                break
    record("AC-VDB8", row is not None and DECLARED == len(results) + 2,
           "matrix_row=%s declared=%d" % (bool(row), DECLARED))


def main():
    before = [snap(p) for _, p in FACES]
    root = tempfile.mkdtemp(prefix="vd-R2825-")
    try:
        run()
    finally:
        shutil.rmtree(root, ignore_errors=True)
    after = [snap(p) for _, p in FACES]
    record("ISOLATION", before == after, "four landed documents untouched")
    bad = [name for name, ok, _ in results if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not bad else "FAIL",
                              len(results) - len(bad), len(results)))
    for name, ok, detail in results:
        if not ok:
            print("  RED %s %s" % (name, detail))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
