"""Acceptance suite for the C-20260927-01 entry-tier canon supplement
(BigDomain price-catalog execution face, council decision 2026-09-29
12:00 roll-call 6/7, topic-3 option A: add the CNY 29.9 entry
subscription tier).

Pre-registered criteria (registered before this implementation edit;
honesty law). One PASS/FAIL line per criterion, evidence inline; the
process exits non-zero on any FAIL.

  AC-E1  sandbox entitlement face carries the patron tier (the C-08
         canon face + sku compliance map already landed; this suite pins
         the member catalog face, the last missing leg).
  AC-E2  premium narrative: patron monthly compute rebate strictly
         exceeds the 19.9 experience tier (design placeholder 5 > 3).
  AC-E3  seat-4 hard criterion: the patron tier owns at least one
         privilege the 19.9 experience tier does not grant.
  AC-E4  seat-6 anti-cannibalization guard: patron and experience
         privilege sets are separated both ways (experience keeps at
         least one privilege patron lacks, so the 19.9 main tier keeps
         a distinct value face).
  AC-E5  products entitlement map exposes the tier:patron read key and
         it resolves to the patron tier (pay_grants.entitlement face).
  AC-E6  CEO reserved face: patron copy carries the 29.9 price anchor
         and the [needs-CEO] marker (pricing confirmation power never
         self-served; BILLING GATE stays closed).
  AC-E7  params_status registry mentions the 29.9 entry tier decision
         provenance (four-tier pricing registry, not the old three).

Usage: python test_entry_tier.py
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import catalog as C  # noqa: E402  (wires the lobby sec_gate path itself)

FAILS = []


def record(ac, ok, evidence):
    line = "%s %s | %s" % ("PASS" if ok else "FAIL", ac, evidence)
    print(line)
    if not ok:
        FAILS.append(ac)


def main():
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    cat = C.Catalog.from_config(cfg)  # AC-M1 validation must accept

    # ---- AC-E1: patron tier present in the catalog face ----
    patron = cat.tiers.get("patron")
    record("AC-E1", patron is not None,
           "catalog tiers=%s" % ",".join(sorted(cat.tiers)))

    # ---- AC-E2: premium narrative, rebate above experience ----
    exp = cat.tiers["experience"]
    ok2 = patron is not None and patron.monthly_credits > exp.monthly_credits
    record("AC-E2", ok2,
           "patron monthly_credits=%s vs experience=%s"
           % (patron.monthly_credits if patron else "-",
              exp.monthly_credits))

    # ---- AC-E3: seat-4 exclusive privilege >= 1 ----
    pset = set(patron.privileges) if patron else set()
    eset = set(exp.privileges)
    excl = pset - eset
    record("AC-E3", len(excl) >= 1, "patron-exclusive=%s" % sorted(excl))

    # ---- AC-E4: seat-6 two-way separation ----
    exp_excl = eset - pset
    ok4 = len(excl) >= 1 and len(exp_excl) >= 1 and pset != eset
    record("AC-E4", ok4,
           "experience-exclusive=%s; sets differ=%s"
           % (sorted(exp_excl), pset != eset))

    # ---- AC-E5: products entitlement read key ----
    prod = cat.products.get("tier:patron")
    record("AC-E5", prod is patron,
           "tier:patron -> %s"
           % (prod.key if prod is not None else "missing"))

    # ---- AC-E6: CEO reserved pricing face ----
    copy = patron.copy if patron else ""
    ok6 = ("29.9" in copy) and ("[needs-CEO]" in copy)
    record("AC-E6", ok6,
           "price anchor 29.9=%s; needs-CEO marker=%s"
           % ("29.9" in copy, "[needs-CEO]" in copy))

    # ---- AC-E7: params_status four-tier registry provenance ----
    ps = str(cfg.get("params_status", ""))
    ok7 = ("29.9" in ps) and ("C-20260927-01" in ps)
    record("AC-E7", ok7,
           "params_status carries 29.9=%s + decision ref=%s"
           % ("29.9" in ps, "C-20260927-01" in ps))

    if FAILS:
        print("SUITE FAIL: %s" % ",".join(FAILS))
        return 1
    print("SUITE PASS: 7/7")
    return 0


if __name__ == "__main__":
    sys.exit(main())
