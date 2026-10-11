"""Acceptance suite: submit_batch batch water-delta wiring (R1796).

Asserts the pre-registered criteria AC-BW1..AC-BW6 from the R1796 claim
line in state/queue/tech.md (seed: R1794 ingest_lobby water wiring -
batch-face symmetry gap; single-slot co-residency law pre-registered
as AC-BW4). Chinese probe strings come from config.json (data file) per
the encoding discipline; the only non-ASCII literals are unicode
escapes for the emoji sample.

Usage: python test_batch_waterwire.py
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
from sec_gate import GateOfflineError  # noqa: E402 (offline stub family)

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


class OfflineGate(object):
    """Deterministic runtime-failure stub: every check raises the
    gate-offline family (swapped into pipe.batch.gate, test_ugc.py
    AC-PW3 precedent)."""

    def check_text(self, text):
        raise GateOfflineError("offline probe")


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
    two live level envelopes (AC-BW2 dual-path cross-check, AC-IW2 law)."""
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
    tmp = tempfile.mkdtemp(prefix="ugc-bw-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    db = os.path.join(tmp, "ugc.db")
    lobby = load_lobby_store()
    ls = lobby.EventStore(db)
    fw = cfg["gate"]["forbidden_words"][0]
    gw = cfg["gate"]["gray_words"][0]
    emoji_text = "\U0001F600\U0001F602\U0001F60E"
    disc = cfg["compliance"]["disclaimer"]
    env_zero = {"pool_water_delta": {}, "total_delta": 0,
                "disclaimer": disc, "persistent": True}
    env_susp = {"pool_water_delta": {"review.suspended": 1}, "total_delta": 1,
                "disclaimer": disc, "persistent": True}

    def idea(actor, text):
        ls.append(lobby.utc_now_iso(), "idea.submit", actor, "cocreate",
                  text, payload={"text": text, "pool": "proposal-queue-stub"})

    pipe = P.UGCPipeline(cfg, db)
    try:
        # ---- AC-BW1 part 1: honest states (None + empty batch) -----------
        none_before = pipe.last_water_delta() is None
        recs0 = pipe.submit_batch("avatar_intake", "A-bw1e", [])
        env0 = pipe.last_water_delta()
        keys_ok = (isinstance(env0, dict)
                   and set(env0) == {"pool_water_delta", "total_delta",
                                     "disclaimer", "persistent"})
        empty_ok = (recs0 == [] and env0["pool_water_delta"] == {}
                    and env0["total_delta"] == 0)
        disc_ok = (isinstance(env0, dict)
                   and env0["disclaimer"] == disc
                   and env0["persistent"] is True)

        # ---- mixed batch: clean / gray / emoji-only / forbidden / bad ----
        mixed_texts = ["clean batch probe one", "gray probe " + gw,
                       emoji_text, "forbidden probe " + fw, ""]
        prev2 = pipe.store.pool_water_levels()  # test-side pre-batch snapshot
        recs = pipe.submit_batch("avatar_intake", "A-bw1x", mixed_texts)
        cur2 = pipe.store.pool_water_levels()   # test-side post-batch snapshot
        env = pipe.last_water_delta()
        manual, manual_total = flatten_delta(prev2, cur2)

        # ---- AC-BW1 part 2: receipts list shape zero-drift --------------
        shape_ok = (len(recs) == len(mixed_texts)
                    and all(isinstance(r, dict) for r in recs)
                    and all(r.get("text_index") == i
                            for i, r in enumerate(recs)))
        r_clean, r_gray = recs[0], recs[1]
        r_noise, r_l1, r_bad = recs[2], recs[3], recs[4]
        kinds_ok = (r_clean.get("received") and r_clean.get("pooled")
                    and r_clean.get("evt_id")
                    and r_gray.get("received") and r_gray.get("suspended")
                    and r_gray.get("gate") == "review" and r_gray.get("evt_id")
                    and r_noise.get("received") and r_noise.get("noise")
                    and r_noise.get("noise_reason") == "emoji_only"
                    and r_noise.get("evt_id")
                    and r_l1.get("code") == UGC.E_CONTENT_REJECTED
                    and not r_l1.get("received")
                    and r_bad.get("code") == UGC.E_BAD_FRAME)
        record("AC-BW1",
               none_before and keys_ok and empty_ok and disc_ok
               and shape_ok and kinds_ok,
               "pre-batch None=%s envelope-keys=%s empty-batch=%s "
               "receipts=%d/%d shape=%s kinds=%s"
               % (none_before, sorted(env0) if isinstance(env0, dict) else None,
                  empty_ok, len(recs), len(mixed_texts), shape_ok, kinds_ok))

        # ---- AC-BW2: dual-path cross-validation --------------------------
        dual_ok = (env["pool_water_delta"] == manual
                   and env["total_delta"] == manual_total)
        det_ok = (json.dumps(pipe.last_water_delta(), sort_keys=True)
                  == json.dumps(env, sort_keys=True))
        record("AC-BW2", dual_ok and det_ok,
               "face-cells=%s manual-cells=%s face-total=%s manual-total=%s "
               "double-call-identical=%s"
               % (json.dumps(env["pool_water_delta"], sort_keys=True),
                  json.dumps(manual, sort_keys=True),
                  env["total_delta"], manual_total, det_ok))

        # ---- AC-BW3: water-receipt alignment + clean-only zero ------------
        want_cells = {"noise.total": 1, "noise.by_reason.emoji_only": 1,
                      "review.suspended": 1}
        cells_ok = (env["pool_water_delta"] == want_cells
                    and env["total_delta"] == 2)
        recs_c = pipe.submit_batch("avatar_intake", "A-bw3c",
                                   ["clean only probe one",
                                    "clean only probe two"])
        env_c = pipe.last_water_delta()
        clean_zero_ok = (len(recs_c) == 2
                         and all(r.get("pooled") for r in recs_c)
                         and env_c["pool_water_delta"] == {}
                         and env_c["total_delta"] == 0)
        record("AC-BW3", cells_ok and clean_zero_ok,
               "cells=%s total=%s clean-batch-delta=%s total=%s"
               % (json.dumps(env["pool_water_delta"], sort_keys=True),
                  env["total_delta"],
                  env_c["pool_water_delta"] if clean_zero_ok else None,
                  env_c["total_delta"] if clean_zero_ok else None))

        # ---- AC-BW5 part 1: L1-only batch, zero gate calls ----------------
        calls = {"n": 0}
        orig = pipe.batch.check_batch

        def counting(*a, **k):
            calls["n"] += 1
            return orig(*a, **k)

        pipe.batch.check_batch = counting
        try:
            recs_l1 = pipe.submit_batch(
                "avatar_intake", "A-bw5l",
                ["forbidden probe two " + fw, "forbidden probe three " + fw])
        finally:
            pipe.batch.check_batch = orig
        l1_ok = (len(recs_l1) == 2
                 and all(r.get("code") == UGC.E_CONTENT_REJECTED
                         for r in recs_l1)
                 and calls["n"] == 0
                 and pipe.last_water_delta()["pool_water_delta"] == {}
                 and pipe.last_water_delta()["total_delta"] == 0)

        # ---- AC-BW5 part 2: degraded batch, zero water cells --------------
        counts_a = five_table_counts(db)
        real_gate = pipe.batch.gate
        pipe.batch.gate = OfflineGate()
        try:
            recs_d = pipe.submit_batch(
                "avatar_intake", "A-bw5d",
                ["degraded batch probe one", "degraded batch probe two"])
        finally:
            pipe.batch.gate = real_gate
        counts_b = five_table_counts(db)
        env_d = pipe.last_water_delta()
        banner = pipe.degraded_banner()
        qids = {r.get("qid") for r in recs_d if r.get("queued")}
        deg_rows = [q for q in banner["queued"] if q["qid"] in qids]
        degraded_ok = (len(recs_d) == 2
                       and all(r.get("queued") and r.get("qid")
                               for r in recs_d)
                       and counts_a == counts_b
                       and env_d["pool_water_delta"] == {}
                       and env_d["total_delta"] == 0
                       and len(deg_rows) == 2
                       and all(q["reason"] == "gate_error"
                               for q in deg_rows))
        record("AC-BW5", l1_ok and degraded_ok,
               "l1-batch gate-calls=%d l1-receipts=%d "
               "degraded-queued=%d five-tables-steady=%s "
               "degraded-delta=%s queue-rows(gate_error)=%d"
               % (calls["n"], len(recs_l1), len(recs_d),
                  counts_a == counts_b, env_d["pool_water_delta"],
                  len(deg_rows)))

        # ---- AC-BW4: co-residency single-slot law (last writer wins) ------
        idea("C-30001", "gray probe " + gw)
        pipe.ingest_lobby()
        env_i1 = pipe.last_water_delta()
        ingest_first_ok = env_i1 == env_susp
        pipe.submit_batch("avatar_intake", "A-bw4a", ["clean co-resident probe"])
        batch_second_ok = pipe.last_water_delta() == env_zero
        pipe.submit_batch("avatar_intake", "A-bw4b", ["gray probe " + gw])
        batch_first_ok = pipe.last_water_delta() == env_susp
        pipe.ingest_lobby()  # empty window still overwrites the slot
        ingest_second_ok = pipe.last_water_delta() == env_zero
        record("AC-BW4",
               ingest_first_ok and batch_second_ok
               and batch_first_ok and ingest_second_ok,
               "ingest-then-batch=%s batch-then-ingest=%s "
               "slot-sequence=ingest:%s batch:%s batch:%s ingest:%s"
               % (ingest_first_ok and batch_second_ok,
                  batch_first_ok and ingest_second_ok,
                  "susp" if ingest_first_ok else "?",
                  "zero" if batch_second_ok else "?",
                  "susp" if batch_first_ok else "?",
                  "zero" if ingest_second_ok else "?"))

        # ---- AC-BW6: hygiene + registry source check ----------------------
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
        reg_ok = ('"ugc-batch-water"' in reg_src
                  and "test_batch_waterwire.py" in reg_src)
        record("AC-BW6", ascii_ok and net_ok and reg_ok,
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
