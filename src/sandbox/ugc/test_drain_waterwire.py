"""Acceptance suite: drain_recover recovery water-delta wiring (R1797).

Asserts the pre-registered criteria AC-DR1..AC-DR6 from the R1797 claim
line in state/queue/tech.md (seed: R1796 submit_batch water wiring -
recovery-flow symmetry gap; three-window co-residency single slot
pre-registered as AC-DR4). Chinese probe strings come from config.json
(data file) per the encoding discipline; the only non-ASCII literals
are unicode escapes for the emoji sample.

Usage: python test_drain_waterwire.py
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
from sec_batch import ST_DRAINED_REJ  # noqa: E402 (terminal verdict face)

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
    gate-offline family (swapped into pipe.batch.gate, AC-BW5
    precedent). Queueing rides this stub: the ungated texts land in the
    persistent queue, never passed, never lost."""

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
    two live level envelopes (AC-DR2 dual-path cross-check, AC-IW2 law)."""
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
    tmp = tempfile.mkdtemp(prefix="ugc-dr-")
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

    def queue_texts(rows):
        """Degrade texts straight into the persistent queue via the
        offline-gate stub (AC-BW5 pattern); one call per row so each
        queue row carries its own source/actor metadata. Returns the
        qids in submission order."""
        real_gate = pipe.batch.gate
        pipe.batch.gate = OfflineGate()
        try:
            qids = []
            for source, actor, text in rows:
                out = pipe.batch.check_batch([text], source=source,
                                             actor=actor)
                qids.extend(qid for qid, _landed in out["degraded"])
        finally:
            pipe.batch.gate = real_gate
        return qids

    pipe = P.UGCPipeline(cfg, db)
    try:
        # ---- AC-DR1: honest states (None + empty recovery window) --------
        none_before = pipe.last_water_delta() is None
        rec0 = pipe.drain_recover()
        env0 = pipe.last_water_delta()
        keys_ok = (isinstance(env0, dict)
                   and set(env0) == {"pool_water_delta", "total_delta",
                                     "disclaimer", "persistent"})
        empty_ok = (env0["pool_water_delta"] == {} and env0["total_delta"] == 0)
        disc_ok = (env0["disclaimer"] == disc and env0["persistent"] is True)
        receipt_keys = {"drained", "passed", "rejected", "still_queued",
                        "recovered", "skipped_existing", "failed_publish",
                        "disclaimer", "persistent"}
        receipt_ok = (set(rec0) == receipt_keys
                      and rec0["drained"] == 0 and rec0["passed"] == 0
                      and rec0["rejected"] == 0 and rec0["still_queued"] == 0
                      and rec0["recovered"] == [] and rec0["skipped_existing"] == 0
                      and rec0["failed_publish"] == 0)
        record("AC-DR1",
               none_before and keys_ok and empty_ok and disc_ok and receipt_ok,
               "pre-window None=%s envelope-keys=%s empty-zero=%s "
               "receipt-keys=%d zero-counts=%s"
               % (none_before,
                  sorted(env0) if isinstance(env0, dict) else None,
                  empty_ok, len(rec0), receipt_ok))

        # ---- mixed degraded queue: gray / emoji-only / clean / gate-word -
        mixed_rows = [
            ("avatar_intake", "A-dr3g", "gray probe " + gw),
            ("avatar_intake", "A-dr3e", emoji_text),
            ("avatar_intake", "A-dr3c", "clean recovery probe one"),
            ("avatar_intake", "A-dr3f", "forbidden probe " + fw),
        ]
        qids = queue_texts(mixed_rows)
        queued_ok = len(qids) == 4

        prev2 = pipe.store.pool_water_levels()  # test-side pre-recovery snapshot
        counts_a = five_table_counts(db)
        rec = pipe.drain_recover()
        cur2 = pipe.store.pool_water_levels()   # test-side post-recovery snapshot
        env = pipe.last_water_delta()
        counts_b = five_table_counts(db)
        manual, manual_total = flatten_delta(prev2, cur2)

        # ---- AC-DR2: dual-path cross-validation --------------------------
        dual_ok = (env["pool_water_delta"] == manual
                   and env["total_delta"] == manual_total)
        det_ok = (json.dumps(pipe.last_water_delta(), sort_keys=True)
                  == json.dumps(env, sort_keys=True))
        record("AC-DR2", dual_ok and det_ok,
               "face-cells=%s manual-cells=%s face-total=%s manual-total=%s "
               "double-call-identical=%s"
               % (json.dumps(env["pool_water_delta"], sort_keys=True),
                  json.dumps(manual, sort_keys=True),
                  env["total_delta"], manual_total, det_ok))

        # ---- AC-DR3: water-receipt alignment + fail-closed gate hit ------
        want_cells = {"noise.total": 1, "noise.by_reason.emoji_only": 1,
                      "review.suspended": 1}
        cells_ok = (env["pool_water_delta"] == want_cells
                    and env["total_delta"] == 2)
        counts_ok = (rec["drained"] == 4 and rec["passed"] == 3
                     and rec["rejected"] == 1 and rec["still_queued"] == 0
                     and len(rec["recovered"]) == 3
                     and rec["skipped_existing"] == 0
                     and rec["failed_publish"] == 0)
        rej_rows = pipe.batch.rows_by_status(ST_DRAINED_REJ)
        rej_ok = (len(rej_rows) == 1
                  and rej_rows[0][3] == mixed_rows[3][2])
        fw_evt = P.compute_evt_id(mixed_rows[3][0], mixed_rows[3][1],
                                  mixed_rows[3][2])
        fw_never = pipe.store.event_row(fw_evt) is None
        record("AC-DR3", queued_ok and cells_ok and counts_ok and rej_ok
               and fw_never,
               "queued=%d cells=%s total=%s receipt=%s "
               "drained_rejected=%d never-published=%s"
               % (len(qids), json.dumps(env["pool_water_delta"],
                                        sort_keys=True),
                  env["total_delta"], counts_ok, len(rej_rows), fw_never))

        # ---- AC-DR5: idempotency + five-table count ledger ----------------
        rec2 = pipe.drain_recover()
        counts_c = five_table_counts(db)
        env2 = pipe.last_water_delta()
        idem_ok = (rec2["drained"] == 0 and rec2["passed"] == 0
                   and rec2["rejected"] == 0 and rec2["still_queued"] == 0
                   and rec2["recovered"] == [] and rec2["skipped_existing"] == 3
                   and rec2["failed_publish"] == 0)
        steady_ok = counts_b == counts_c
        zero_win_ok = (env2["pool_water_delta"] == {} and env2["total_delta"] == 0)
        want_diff = {"ugc_events": 3, "ugc_items": 1, "review_queue": 1,
                     "ugc_ingest_log": 0, "gate_receipts": 0}
        ledger_ok = all(counts_b[t] - counts_a[t] == want_diff[t]
                        for t in FIVE_TABLES)
        record("AC-DR5", idem_ok and steady_ok and zero_win_ok and ledger_ok,
               "second-drain=%s tables-steady=%s zero-window=%s "
               "ledger=%s"
               % (idem_ok, steady_ok, zero_win_ok,
                  json.dumps({t: counts_b[t] - counts_a[t]
                              for t in FIVE_TABLES}, sort_keys=True)))

        # ---- AC-DR4: three-window co-residency (last writer wins) --------
        idea("C-50001", "gray probe " + gw)
        pipe.ingest_lobby()
        ingest_first_ok = pipe.last_water_delta() == env_susp
        queue_texts([("avatar_intake", "A-dr4g", "gray probe two " + gw)])
        pipe.drain_recover()
        drain_second_ok = pipe.last_water_delta() == env_susp
        pipe.submit_batch("avatar_intake", "A-dr4b",
                          ["clean co-resident probe"])
        batch_third_ok = pipe.last_water_delta() == env_zero
        pipe.drain_recover()  # empty recovery window still overwrites
        drain_fourth_ok = pipe.last_water_delta() == env_zero
        record("AC-DR4",
               ingest_first_ok and drain_second_ok
               and batch_third_ok and drain_fourth_ok,
               "slot-sequence=ingest:%s drain:%s batch:%s drain(empty):%s"
               % ("susp" if ingest_first_ok else "?",
                  "susp" if drain_second_ok else "?",
                  "zero" if batch_third_ok else "?",
                  "zero" if drain_fourth_ok else "?"))

        # ---- AC-DR6: hygiene + registry source check ----------------------
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
        reg_ok = ('"ugc-drain-water"' in reg_src
                  and "test_drain_waterwire.py" in reg_src)
        record("AC-DR6", ascii_ok and net_ok and reg_ok,
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
