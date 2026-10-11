"""Acceptance suite: ingest_lobby window water-delta wiring (R1794).

Asserts the pre-registered criteria AC-IW1..AC-IW6 from the R1794
claim line in state/queue/tech.md (seed: R1785 pool_water_delta
production wiring, explicit follow-up window). Chinese probe strings
come from config.json (data file) per the encoding discipline; the
only non-ASCII literals are unicode escapes for the emoji sample.

Usage: python test_ingest_waterwire.py
"""

import importlib.util
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import pipeline as P  # noqa: E402
import store as UGC  # noqa: E402

EXPECTED = 6
RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def load_lobby_store():
    path = os.path.normpath(os.path.join(BASE, "..", "lobby", "store.py"))
    spec = importlib.util.spec_from_file_location("lobby_store_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FIVE_TABLES = ("ugc_events", "ugc_items", "review_queue",
               "ugc_ingest_log", "gate_receipts")


def five_table_counts(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return {t: conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
                for t in FIVE_TABLES}
    finally:
        conn.close()


def flatten_delta(prev_env, cur_env):
    """Independent manual re-derivation of the pool-water delta map from
    two live level envelopes (AC-IW2 dual-path cross-check)."""
    manual = {}

    def cell(key, now, then):
        diff = int(now) - int(then)
        if diff != 0:
            manual[key] = diff

    prev = prev_env["pool_water_levels"]
    cur = cur_env["pool_water_levels"]
    cell("noise.total", cur["noise"]["total"], prev["noise"]["total"])
    for key in sorted(set(prev["noise"]["by_reason"]) | set(cur["noise"]["by_reason"])):
        cell("noise.by_reason." + key,
             cur["noise"]["by_reason"].get(key, 0),
             prev["noise"]["by_reason"].get(key, 0))
    cell("review.suspended", cur["review"]["suspended"], prev["review"]["suspended"])
    for key in sorted(set(prev["review"]["verdicted"]) | set(cur["review"]["verdicted"])):
        cell("review.verdicted." + key,
             cur["review"]["verdicted"].get(key, 0),
             prev["review"]["verdicted"].get(key, 0))
    total_delta = ((cur["noise"]["total"] + cur["review"]["suspended"])
                   - (prev["noise"]["total"] + prev["review"]["suspended"]))
    return manual, total_delta


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-iw-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    db = os.path.join(tmp, "ugc.db")
    lobby = load_lobby_store()
    ls = lobby.EventStore(db)
    fw = cfg["gate"]["forbidden_words"][0]
    gw = cfg["gate"]["gray_words"][0]
    kw = cfg["routing"]["rules"][1]["keywords"][0]
    emoji_text = "\U0001F600\U0001F602\U0001F60E"

    def idea(actor, text):
        ls.append(lobby.utc_now_iso(), "idea.submit", actor, "cocreate",
                  text, payload={"text": text, "pool": "proposal-queue-stub"})

    pipe = P.UGCPipeline(cfg, db)
    try:
        # ---- AC-IW1: contract + honest states -----------------------------
        none_before = pipe.last_water_delta() is None
        recs0 = pipe.ingest_lobby()  # empty window (zero lobby rows)
        env0 = pipe.last_water_delta()
        keys_ok = (isinstance(env0, dict)
                   and set(env0) == {"pool_water_delta", "total_delta",
                                     "disclaimer", "persistent"})
        empty_ok = (recs0 == [] and env0["pool_water_delta"] == {}
                    and env0["total_delta"] == 0)
        disc_ok = (isinstance(env0, dict)
                   and env0["disclaimer"] == cfg["compliance"]["disclaimer"])
        persist_ok = (isinstance(env0, dict)
                      and env0["persistent"] is True)  # store face contract (R1785)
        record("AC-IW1",
               none_before and keys_ok and empty_ok and disc_ok and persist_ok,
               "pre-window None=%s envelope-keys=%s empty-window delta=%s "
               "total_delta=%s disclaimer-wired=%s persistent=%s"
               % (none_before, sorted(env0) if isinstance(env0, dict) else None,
                  env0["pool_water_delta"] if isinstance(env0, dict) else None,
                  env0["total_delta"] if isinstance(env0, dict) else None,
                  disc_ok, persist_ok))

        # ---- mixed window: clean / gray / emoji-only / forbidden-L1 --------
        idea("C-20001", "lobby idea about " + kw)          # clean pooled
        idea("C-20002", "gray probe " + gw)                # review suspended
        idea("C-20003", emoji_text)                         # noise emoji_only
        idea("C-20004", "forbidden probe " + fw)           # L1 local catch
        prev2 = pipe.store.pool_water_levels()  # test-side pre-window snapshot
        recs = pipe.ingest_lobby()
        cur2 = pipe.store.pool_water_levels()   # test-side post-window snapshot
        env = pipe.last_water_delta()
        manual, manual_total = flatten_delta(prev2, cur2)

        # ---- AC-IW2: dual-path cross-validation ---------------------------
        dual_ok = (env["pool_water_delta"] == manual
                   and env["total_delta"] == manual_total)
        record("AC-IW2", dual_ok,
               "face-cells=%s manual-cells=%s face-total=%s manual-total=%s"
               % (json.dumps(env["pool_water_delta"], sort_keys=True),
                  json.dumps(manual, sort_keys=True),
                  env["total_delta"], manual_total))

        # ---- AC-IW3: water-receipt alignment ------------------------------
        want_cells = {"noise.total": 1, "noise.by_reason.emoji_only": 1,
                      "review.suspended": 1}
        cells_ok = env["pool_water_delta"] == want_cells and env["total_delta"] == 2
        r_clean = next(r for r in recs if r.get("pooled") and r.get("evt_id"))
        r_gray = next(r for r in recs if r.get("suspended"))
        r_noise = next(r for r in recs if r.get("noise"))
        r_l1 = next(r for r in recs if r.get("code") == UGC.E_CONTENT_REJECTED)
        shapes_ok = (r_noise.get("noise_reason") == "emoji_only"
                     and r_gray.get("gate") == "review"
                     and r_clean.get("gate") == "pass")
        record("AC-IW3", cells_ok and shapes_ok,
               "cells=%s total=%s clean=%s gray=%s noise=%s l1-reject=%s"
               % (json.dumps(env["pool_water_delta"], sort_keys=True),
                  env["total_delta"], r_clean.get("gate"), r_gray.get("gate"),
                  r_noise.get("noise_reason"),
                  r_l1.get("code") == UGC.E_CONTENT_REJECTED))

        # ---- AC-IW4: zero-drift face --------------------------------------
        rows_now = len(recs)
        one_per_row = all(isinstance(r, dict) for r in recs) and rows_now == 4
        marks_before = five_table_counts(db)["ugc_ingest_log"]
        # L1-only window: two forbidden rows, zero gate calls
        idea("C-20005", "forbidden probe two " + fw)
        idea("C-20006", "forbidden probe three " + fw)
        calls = {"n": 0}
        orig = pipe.batch.check_batch

        def counting(*a, **k):
            calls["n"] += 1
            return orig(*a, **k)

        pipe.batch.check_batch = counting
        try:
            recs_l1 = pipe.ingest_lobby()
        finally:
            pipe.batch.check_batch = orig
        marks_after = five_table_counts(db)["ugc_ingest_log"]
        l1_ok = (len(recs_l1) == 2
                 and all(r.get("code") == UGC.E_CONTENT_REJECTED for r in recs_l1)
                 and calls["n"] == 0
                 and marks_after - marks_before == 2)
        record("AC-IW4", one_per_row and l1_ok,
               "mixed receipts=%d one-per-row=%s l1-window gate-calls=%d "
               "l1-receipts=%d marks-delta=%d"
               % (rows_now, one_per_row, calls["n"], len(recs_l1),
                  marks_after - marks_before))

        # ---- AC-IW5: pure-read law on a static world ----------------------
        counts_a = five_table_counts(db)
        lv1 = pipe.store.pool_water_levels()
        d1 = pipe.store.pool_water_delta(lv1)
        lw1 = pipe.last_water_delta()
        lv2 = pipe.store.pool_water_levels()
        d2 = pipe.store.pool_water_delta(lv1)
        lw2 = pipe.last_water_delta()
        counts_b = five_table_counts(db)
        pure_ok = counts_a == counts_b
        det_ok = (json.dumps(lv1, sort_keys=True) == json.dumps(lv2, sort_keys=True)
                  and json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)
                  and json.dumps(lw1, sort_keys=True) == json.dumps(lw2, sort_keys=True))
        record("AC-IW5", pure_ok and det_ok,
               "five-tables-steady=%s double-call-json-identical=%s"
               % (pure_ok, det_ok))

        # ---- AC-IW6: hygiene + registry source check ----------------------
        ascii_ok = True
        for rel in ("pipeline.py", os.path.basename(__file__)):
            with open(os.path.join(BASE, rel), "rb") as handle:
                ascii_ok = ascii_ok and max(handle.read()) < 128
        net_ok = True
        for rel in ("pipeline.py", os.path.basename(__file__)):
            with open(os.path.join(BASE, rel), encoding="utf-8") as handle:
                for line in handle:
                    s = line.strip()
                    if s.startswith("import ") or s.startswith("from "):
                        if any(w in s for w in ("urllib", "requests",
                                               "socket", "http")):
                            net_ok = False
        reg_path = os.path.normpath(os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ('"ugc-ingest-waterwire"' in reg_src
                  and "test_ingest_waterwire.py" in reg_src)
        record("AC-IW6", ascii_ok and net_ok and reg_ok,
               "pure-ascii=%s import-lines-clean=%s registry-wired=%s"
               % (ascii_ok, net_ok, reg_ok))
    finally:
        pipe.close()
        ls.close()

    ok_all = len(RESULTS) == EXPECTED and all(ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                             sum(1 for _a, ok in RESULTS if ok), EXPECTED),
          flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
