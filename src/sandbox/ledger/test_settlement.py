"""Acceptance suite for the cross-subsidiary settlement manifest
protocol face (BigDomain explore queue item, round R601). Asserts the
pre-registered criteria AC-ST1..AC-ST7 from the R601 backlog row
(criteria were registered before this code existed; honesty law).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Usage: python test_settlement.py
"""

import copy
import hashlib
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import settlement as ST  # noqa: E402  (R601 protocol face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_error(fn, code):
    try:
        fn()
    except ST.SettlementError as exc:
        return exc.code == code, exc.code
    return False, "no-error-raised"


SALES = [{"amount_cent": 1990}, {"amount_cent": 3990},
         {"amount_cent": 990}]
USAGE = [{"units": 12}, {"units": 3}]
PARTIES = ("bigdomain-product", "bigmoney-engine", "bigcompute-outlet")
# fixture values only - canonical split ratios stay [needs-CEO]
WEIGHTS = {"bigdomain-product": 55, "bigmoney-engine": 30,
           "bigcompute-outlet": 15}


def fresh(period):
    face = ST.SettlementFace()
    manifest = face.build_manifest(period, SALES, USAGE, PARTIES,
                                   WEIGHTS)
    return face, manifest


def main():
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, "rb") as handle:
        sha_before = hashlib.sha256(handle.read()).hexdigest()

    # ---------- AC-ST1: conservation law ----------
    face, manifest = fresh("2026-10-01/P1D")
    parts = manifest["apportioned_cent"]
    total = manifest["sales_total_cent"]
    ok1 = sum(parts.values()) == total == 6970
    odd = ST.SettlementFace().build_manifest(
        "2026-10-02/P1D", [{"amount_cent": 199}], [],
        ("a", "b", "c"), {"a": 55, "b": 30, "c": 15})
    ok1 = ok1 and sum(odd["apportioned_cent"].values()) == 199
    zero = ST.SettlementFace().build_manifest(
        "2026-10-03/P1D", [], USAGE, PARTIES, WEIGHTS)
    ok1 = ok1 and sum(zero["apportioned_cent"].values()) == 0
    record("AC-ST1", ok1,
           "fen totals preserved exactly: %s == %d; odd 199 -> %s;"
           " zero-window -> 0" % (parts, total,
                                 odd["apportioned_cent"]))

    # ---------- AC-ST2: determinism ----------
    _, manifest_a = fresh("2026-10-04/P1D")
    _, manifest_b = fresh("2026-10-04/P1D")
    ok2 = ST.canonical(manifest_a) == ST.canonical(manifest_b)
    ok2 = ok2 and manifest_a["id"] == manifest_b["id"]
    record("AC-ST2", ok2,
           "two independent faces build identical canonical"
           " manifests, id=%s..." % manifest_a["id"][:16])

    # ---------- AC-ST3: manifest hash + chain ----------
    body = {key: value for key, value in manifest_a.items()
            if key != "id"}
    ok3 = manifest_a["id"] == ST.digest(ST.canonical(body))
    chain_face = ST.SettlementFace()
    first = chain_face.build_manifest("2026-10-05/P1D", SALES, USAGE,
                                      PARTIES, WEIGHTS)
    second = chain_face.build_manifest("2026-10-06/P1D", SALES, USAGE,
                                       PARTIES, WEIGHTS)
    ok3 = ok3 and second["prev_id"] == first["id"]
    tampered = copy.deepcopy(manifest_a)
    tampered["apportioned_cent"]["bigdomain-product"] += 1
    ok3b, code3 = expect_error(
        lambda: ST.SettlementFace().verify_manifest(tampered, SALES,
                                                    USAGE),
        ST.E_ST_TAMPER)
    record("AC-ST3", ok3 and ok3b,
           "id recomputes; prev chain links (%s->%s); amount tamper"
           " rejected (%s)" % (first["id"][:12],
                               second["prev_id"][:12], code3))

    # ---------- AC-ST4: verify cross ----------
    face4, manifest4 = fresh("2026-10-07/P1D")
    ok4 = face4.verify_manifest(manifest4, SALES, USAGE) is True
    t_amount = copy.deepcopy(manifest4)
    t_amount["apportioned_cent"]["bigcompute-outlet"] += 100
    ok4a, _ = expect_error(
        lambda: face4.verify_manifest(t_amount, SALES, USAGE),
        ST.E_ST_TAMPER)
    t_party = copy.deepcopy(manifest4)
    t_party["parties"] = list(PARTIES) + ["ghost"]
    ok4b, _ = expect_error(
        lambda: face4.verify_manifest(t_party, SALES, USAGE),
        ST.E_ST_TAMPER)
    record("AC-ST4", ok4 and ok4a and ok4b,
           "genuine verify True; amount-tamper and party-tamper both"
           " rejected E_ST_TAMPER")

    # ---------- AC-ST5: window idempotency + claim gate ----------
    face5, manifest5 = fresh("2026-10-08/P1D")
    ok5, code5 = expect_error(
        lambda: face5.build_manifest("2026-10-08/P1D", SALES, USAGE,
                                     PARTIES, WEIGHTS),
        ST.E_ST_PERIOD_DUP)
    ok5 = ok5 and face5.window_count() == 1
    claim = face5.claim("2026-10-08/P1D", "bigdomain-product",
                        manifest5["apportioned_cent"]["bigdomain-product"])
    ok5 = ok5 and claim["manifest_id"] == manifest5["id"]
    ok5b, code5b = expect_error(
        lambda: face5.claim("2026-10-08/P1D", "bigdomain-product", 1),
        ST.E_ST_PERIOD_DUP)
    ok5c, code5c = expect_error(
        lambda: face5.claim("2026-10-08/P1D", "bigmoney-engine",
                            10 ** 9),
        ST.E_ST_BAD_INPUT)
    record("AC-ST5", ok5 and ok5b and ok5c,
           "dup window %s (windows=%d); dup claim %s; over-limit"
           " claim %s" % (code5, face5.window_count(), code5b, code5c))

    # ---------- AC-ST6: red-line source scan ----------
    with open(os.path.join(BASE, "settlement.py"), "rb") as handle:
        src = handle.read()
    text = src.decode("ascii")
    tokens = ["se" + "ll", "re" + "fund", "ex" + "change",
              "with" + "draw", "trans" + "fer", "m" + "int"]
    hits = [tok for tok in tokens if tok in text]
    with open(cfg_path, "rb") as handle:
        sha_mid = hashlib.sha256(handle.read()).hexdigest()
    ok6 = (not hits) and all(byte < 128 for byte in src) \
        and ("import random" not in text) and (sha_mid == sha_before)
    record("AC-ST6", ok6,
           "banned-verb hits=%s; pure-ascii %dB; random-import absent;"
           " config.json sha unchanged" % (hits, len(src)))

    # ---------- AC-ST7: adoption face ----------
    with open(cfg_path, encoding="utf-8") as handle:
        cfg = json.load(handle)
    doc = ST.__doc__ or ""
    ok7 = ("settlement" not in cfg) \
        and (not hasattr(ST, "DEFAULT_RATIOS")) \
        and (not hasattr(ST, "CANONICAL_RATIOS")) \
        and ("BigMoney" in doc) and ("BigCompute" in doc) \
        and ("D-20260924-10" in doc)
    record("AC-ST7", ok7,
           "no settlement key in shipped config; no canonical ratio"
           " constant; engine/outlet reference anchors present in"
           " module docstring")

    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s %d/%d criteria" % ("PASS" if not failed else "FAIL",
                                       len(RESULTS) - len(failed),
                                       len(RESULTS)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
