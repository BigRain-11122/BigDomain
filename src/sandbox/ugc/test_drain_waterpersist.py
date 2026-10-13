"""Acceptance suite: drain_recover recovery-window water read faces
cross-restart persistence example (BigDomain R1913 tech-queue FIFO
head claim; seed = the R1908 reseed - the recovery water delta
itself is in-book (R1797 AC-DR1..AC-DR6, three-window co-residency
single slot) while the recovery-window water READ faces' derived
purity across a full pipeline-stack restart had no pinned example.
R1905 boardpersist pinned the journal face in isolation with
synthetic record() calls; this suite walks the REAL product path -
degraded rows queue through the offline-gate stub, real
drain_recover() windows complete through _complete_water, the
journal archives them - across UGCPipeline.close() -> fresh
UGCPipeline same-db same-config reopen (store + batch + journal
all reopen together).

Asserts the pre-registered criteria AC-DR7..AC-DR13 from the R1913
claim line in state/queue/tech.md (criteria were registered before
this code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Claim rulings (three, registered in the tech.md claim line):
1. restart carrier = the full pipeline stack: UGCPipeline.close()
   then a fresh UGCPipeline on the same config bytes and db path
   (the queue and journal files ride next to ugc.db, so one db
   path = one stack; R1889+ persist family law).
2. world = frozen-clock real record path: two October drain windows
   (a mixed 3-row window, then a 1-row window), a pipeline restart,
   then one November window seeded by NEW degraded rows on the
   fresh instance (clock +23d via the water_journal._utc_now_iso
   holder patch, R1864 roll-suite law, finally-restored).
3. comparison face = dumps(sort_keys=True) byte equality on the
   four read shapes (October explicit window read / default
   whole-board read / store levels envelope / single-slot
   last_water_delta) plus a manual SQL window-slice cross-check.

Zero product bytes change: the persistence semantics already live
in the store/journal/pipeline faces; this suite only pins them
(suite-only round). This source stays pure ASCII per the encoding
discipline.

Usage: python test_drain_waterpersist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import pipeline as P                     # noqa: E402 (face under test)
import water_journal as WJ               # noqa: E402 (clock holder patch)
from sec_gate import GateOfflineError    # noqa: E402 (offline stub family)

EXPECTED = 7
RESULTS = []

OCT_TS = "2026-10-15T12:00:00.000000Z"
NOV_TS = "2026-11-07T12:00:00.000000Z"

FIVE_TABLES = ("ugc_events", "ugc_items", "review_queue",
               "ugc_ingest_log", "gate_receipts")

PRODUCT_FILES = ("config.json", "pipeline.py", "water_journal.py",
                "store.py", "sec_batch.py")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def five_table_counts(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return {t: conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
                for t in FIVE_TABLES}
    finally:
        conn.close()


def journal_count(journal_db, month=None):
    conn = sqlite3.connect(journal_db)
    try:
        if month is None:
            return conn.execute(
                "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        return conn.execute(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE substr(ts_utc, 1, 7) = ?",
            (month,)).fetchone()[0]
    finally:
        conn.close()


def queue_count(db_path):
    conn = sqlite3.connect(os.path.join(
        os.path.dirname(os.path.abspath(db_path)), "sec_degraded.db"))
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM sec_degraded_queue").fetchone()[0]
    finally:
        conn.close()


class OfflineGate(object):
    """Deterministic runtime-failure stub: every check raises the
    gate-offline family (swapped into pipe.batch.gate, AC-BW5 /
    R1797 precedent). Queueing rides this stub: the ungated texts
    land in the persistent queue, never passed, never lost."""

    def check_text(self, text):
        raise GateOfflineError("offline probe")


def queue_texts(pipe, rows):
    """Degrade texts straight into the persistent queue via the
    offline-gate stub (R1797 pattern); one call per row so each
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


def main():
    pre_sha = {f: sha256_file(os.path.join(BASE, f))
               for f in PRODUCT_FILES}
    tmp = tempfile.mkdtemp(prefix="ugc-drp-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as h:
        cfg = json.load(h)
    db = os.path.join(tmp, "ugc.db")
    journal_db = os.path.join(tmp, "water_journal.db")
    disc = cfg["compliance"]["disclaimer"]
    gw = cfg["gate"]["gray_words"][0]
    emoji_text = "\U0001F600\U0001F602\U0001F60E"

    env_w1 = {"pool_water_delta": {"noise.total": 1,
                                   "noise.by_reason.emoji_only": 1,
                                   "review.suspended": 1},
              "total_delta": 2, "disclaimer": disc, "persistent": True}
    env_w2 = {"pool_water_delta": {}, "total_delta": 0,
              "disclaimer": disc, "persistent": True}
    env_nov = {"pool_water_delta": {"review.suspended": 1},
               "total_delta": 1, "disclaimer": disc, "persistent": True}

    orig_now = WJ._utc_now_iso
    snap_oct = snap_default = snap_levels = snap_default2 = None
    hyg = {}
    pipe = pipe2 = pipe3 = None
    try:
        WJ._utc_now_iso = lambda: OCT_TS
        pipe = P.UGCPipeline(cfg, db)

        # ---- AC-DR7: October world + pre-close four-element snapshot --
        q1 = queue_texts(pipe, [
            ("avatar_intake", "A-dp7g", "gray probe " + gw),
            ("avatar_intake", "A-dp7e", emoji_text),
            ("avatar_intake", "A-dp7c", "clean recovery window one"),
        ])
        rec1 = pipe.drain_recover()
        slot1 = pipe.last_water_delta()
        q2 = queue_texts(pipe, [
            ("avatar_intake", "A-dp7d", "clean recovery window two"),
        ])
        rec2 = pipe.drain_recover()
        slot2 = pipe.last_water_delta()
        oct_read = pipe.journal.journal_board(window="2026-10")
        default_read = pipe.journal.journal_board()
        levels = pipe.store.pool_water_levels()
        keys_ok = (set(oct_read) == {"journal_board", "total",
                                     "ai_generated", "disclaimer",
                                     "persistent", "window"}
                   and oct_read["window"] == "2026-10"
                   and oct_read["ai_generated"] == 0
                   and oct_read["disclaimer"] == disc
                   and oct_read["persistent"] is True)
        rows_ok = (len(oct_read["journal_board"]) == 2
                   and all(r["kind"] == "drain"
                           for r in oct_read["journal_board"]))
        sql_oct = journal_count(journal_db, "2026-10")
        cross_ok = (sql_oct == oct_read["total"] == 2)
        rec1_ok = (len(q1) == 3 and rec1["drained"] == 3
                   and rec1["passed"] == 3 and rec1["rejected"] == 0
                   and rec1["still_queued"] == 0
                   and len(rec1["recovered"]) == 3
                   and rec1["skipped_existing"] == 0
                   and rec1["failed_publish"] == 0)
        rec2_ok = (len(q2) == 1 and rec2["drained"] == 1
                   and rec2["passed"] == 1 and len(rec2["recovered"]) == 1)
        slots_ok = (slot1 == env_w1 and slot2 == env_w2)
        snap_oct = dumps(oct_read)
        snap_default = dumps(default_read)
        snap_levels = dumps(levels)
        record("AC-DR7",
               keys_ok and rows_ok and cross_ok and rec1_ok
               and rec2_ok and slots_ok,
               "envelope-keys=%s rows-kind-drain=%s sql-oct=%d "
               "total=%d rec1=%s rec2=%s slot1-cells=%s "
               "slot2-zero=%s"
               % (keys_ok, rows_ok, sql_oct, oct_read["total"],
                  rec1_ok, rec2_ok,
                  dumps(slot1["pool_water_delta"]),
                  slot2["pool_water_delta"] == {}))
        pipe.close()
        pipe = None

        # ---- AC-DR8: cross-restart October window read byte-identical -
        pipe2 = P.UGCPipeline(cfg, db)
        r_a = pipe2.journal.journal_board(window="2026-10")
        r_b = pipe2.journal.journal_board(window="2026-10")
        record("AC-DR8",
               dumps(r_a) == snap_oct and dumps(r_a) == dumps(r_b),
               "oct-replay=%s double-read-identical=%s"
               % (dumps(r_a) == snap_oct, dumps(r_a) == dumps(r_b)))

        # ---- AC-DR9: default read + levels + single-slot restore -----
        d2 = pipe2.journal.journal_board()
        lv2 = pipe2.store.pool_water_levels()
        default_ok = dumps(d2) == snap_default
        levels_ok = dumps(lv2) == snap_levels
        slot_none = pipe2.last_water_delta() is None
        record("AC-DR9", default_ok and levels_ok and slot_none,
               "default-replay=%s levels-replay=%s "
               "fresh-slot-none=%s"
               % (default_ok, levels_ok, slot_none))

        # ---- AC-DR10: new degraded post-restart -> recompute + freeze -
        WJ._utc_now_iso = lambda: NOV_TS
        q3 = queue_texts(pipe2, [
            ("avatar_intake", "A-dp1g", "gray probe november " + gw),
            ("avatar_intake", "A-dp1c", "clean recovery november"),
        ])
        rec3 = pipe2.drain_recover()
        sql_nov = journal_count(journal_db, "2026-11")
        new_default = pipe2.journal.journal_board()
        new_oct = pipe2.journal.journal_board(window="2026-10")
        nov_read = pipe2.journal.journal_board(window="2026-11")
        slot3 = pipe2.last_water_delta()
        nov_slice = [r for r in new_default["journal_board"]
                     if r["ts_utc"].startswith("2026-11")]
        recompute_ok = (dumps(new_default) != snap_default)
        freeze_ok = (dumps(new_oct) == snap_oct)
        slot_ok = (slot3 == env_nov)
        slice_ok = (nov_read["journal_board"] == nov_slice)
        rec3_ok = (len(q3) == 2 and rec3["drained"] == 2
                   and rec3["passed"] == 2 and len(rec3["recovered"]) == 2)
        record("AC-DR10",
               sql_nov == 1 and recompute_ok and freeze_ok and slot_ok
               and slice_ok and rec3_ok,
               "sql-nov=%d default-recomputed=%s oct-frozen=%s "
               "slot-nov-cells=%s nov-slice=%s rec3=%s"
               % (sql_nov, recompute_ok, freeze_ok,
                  dumps(slot3["pool_water_delta"]), slice_ok, rec3_ok))
        snap_default2 = dumps(new_default)

        # ---- AC-DR11: November honesty + telescoping partition -------
        nov_rows_ok = (nov_read["total"] == 1
                       and all(r["kind"] == "drain"
                               for r in nov_read["journal_board"]))
        sql_nov_total = journal_count(journal_db, "2026-11")
        fut = pipe2.journal.journal_board(window="2026-12")
        tele_ok = (new_oct["total"] + nov_read["total"]
                   == new_default["total"])
        fut_ok = (fut["journal_board"] == [] and fut["total"] == 0
                  and fut["window"] == "2026-12")
        record("AC-DR11",
               nov_rows_ok and nov_read["total"] == sql_nov_total
               and tele_ok and fut_ok,
               "nov-rows-drain=%s nov-total==sql=%s "
               "telescope %d+%d==%d future-empty=%s"
               % (nov_rows_ok, nov_read["total"] == sql_nov_total,
                  new_oct["total"], nov_read["total"],
                  new_default["total"], fut_ok))
        pipe2.close()
        pipe2 = None

        # ---- AC-DR12: third instance, double-restart stability --------
        pipe3 = P.UGCPipeline(cfg, db)
        o3a = pipe3.journal.journal_board(window="2026-10")
        o3b = pipe3.journal.journal_board(window="2026-10")
        d3a = pipe3.journal.journal_board()
        d3b = pipe3.journal.journal_board()
        record("AC-DR12",
               dumps(o3a) == snap_oct and dumps(d3a) == snap_default2
               and dumps(o3a) == dumps(o3b)
               and dumps(d3a) == dumps(d3b),
               "oct==original=%s default==inst2-final=%s "
               "seq-oct=%s seq-default=%s"
               % (dumps(o3a) == snap_oct,
                  dumps(d3a) == snap_default2,
                  dumps(o3a) == dumps(o3b), dumps(d3a) == dumps(d3b)))

        # ---- AC-DR13: pure-read law + hygiene evidence gathering -----
        before = {"journal": journal_count(journal_db),
                  "queue": queue_count(db),
                  "tables": five_table_counts(db)}
        battery = [
            dumps(pipe3.journal.journal_board(window="2026-10")),
            dumps(pipe3.journal.journal_board(window="2026-11")),
            dumps(pipe3.journal.journal_board(window="2026-12")),
            dumps(pipe3.journal.journal_board()),
            dumps(pipe3.journal.journal_board()),
            dumps(pipe3.store.pool_water_levels()),
            dumps(pipe3.store.pool_water_levels()),
        ]
        battery_pair = (battery[0] == battery[0]
                        and battery[3] == battery[4]
                        and battery[5] == battery[6])
        after = {"journal": journal_count(journal_db),
                 "queue": queue_count(db),
                 "tables": five_table_counts(db)}
        pure_ok = (before == after and battery_pair)
        with open(os.path.join(BASE, "water_journal.py"),
                  encoding="utf-8") as h:
            wj_src = h.read()
        append_ok = (not re.search(r"\bUPDATE\b", wj_src)
                     and not re.search(r"\bDELETE\b", wj_src))
        with open(os.path.join(BASE, "pipeline.py"), encoding="utf-8") as h:
            pl_src = h.read()
        seg_start = pl_src.find("def drain_recover")
        seg_end = pl_src.find("\n    def ", seg_start + 10)
        seg = pl_src[seg_start:seg_end]
        seg_ok = (seg_start >= 0 and seg_end > seg_start
                  and not re.search(r"\bINSERT\b|\bUPDATE\b|\bDELETE\b",
                                    seg))
        ascii_ok = True
        # source files only - config.json is the Chinese data file
        # by the encoding discipline, it never joins the ascii scan
        for rel in ("pipeline.py", "water_journal.py", "store.py",
                    "sec_batch.py"):
            with open(os.path.join(BASE, rel), "rb") as h:
                ascii_ok = ascii_ok and max(h.read()) < 128
        with open(os.path.abspath(__file__), "rb") as h:
            ascii_ok = ascii_ok and max(h.read()) < 128
        net_ok = True
        for rel in ("pipeline.py", "water_journal.py"):
            with open(os.path.join(BASE, rel), encoding="utf-8") as h:
                for line in h:
                    s = line.strip()
                    if s.startswith("import ") or s.startswith("from "):
                        if any(w in s for w in ("urllib", "requests",
                                                "socket", "http")):
                            net_ok = False
        with open(__file__, encoding="utf-8") as h:
            for line in h:
                s = line.strip()
                if s.startswith("import ") or s.startswith("from "):
                    if any(w in s for w in ("urllib", "requests",
                                            "socket", "http")):
                        net_ok = False
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as h:
            reg_src = h.read()
        reg_ok = ('"ugc-drain-waterpersist"' in reg_src
                  and "test_drain_waterpersist.py" in reg_src)
        expected_ok = len(RESULTS) == EXPECTED - 1  # this criterion pending
        hyg = {"pure_ok": pure_ok, "append_ok": append_ok,
               "seg_ok": seg_ok, "ascii_ok": ascii_ok,
               "net_ok": net_ok, "reg_ok": reg_ok,
               "expected_ok": expected_ok}
    finally:
        WJ._utc_now_iso = orig_now
        if pipe is not None:
            pipe.close()
        if pipe2 is not None:
            pipe2.close()
        if pipe3 is not None:
            pipe3.close()

    restore_ok = WJ._utc_now_iso is orig_now
    post_sha = {f: sha256_file(os.path.join(BASE, f))
                for f in PRODUCT_FILES}
    sha_ok = pre_sha == post_sha
    record("AC-DR13",
           hyg.get("pure_ok") and hyg.get("append_ok")
           and hyg.get("seg_ok") and hyg.get("ascii_ok")
           and hyg.get("net_ok") and hyg.get("reg_ok")
           and hyg.get("expected_ok") and restore_ok and sha_ok,
           "pure-read=%s journal-append-only=%s segment-strip=%s "
           "ascii=%s net-clean=%s registry-wired=%s "
           "clock-restored=%s product-sha-stable=%s"
           % (hyg.get("pure_ok"), hyg.get("append_ok"),
              hyg.get("seg_ok"), hyg.get("ascii_ok"),
              hyg.get("net_ok"), hyg.get("reg_ok"),
              restore_ok, sha_ok))

    ok_all = len(RESULTS) == EXPECTED and all(ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                              sum(1 for _a, ok in RESULTS if ok),
                              EXPECTED), flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
