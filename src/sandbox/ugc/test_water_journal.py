"""Acceptance suite: completed-window water journal (R1800).

Asserts the pre-registered criteria AC-WJ1..AC-WJ7 from the R1800 claim
line in state/queue/tech.md (seed: R1799 five-window wiring - the
single _last_water slot loses history on restart; this ledger is the
append-only observability answer). Chinese probe words come from
config.json (data file) per the encoding discipline; this source is
pure ASCII.

Usage: python test_water_journal.py
"""

import hashlib
import importlib.util
import inspect
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import pipeline as P  # noqa: E402
import store as UGC  # noqa: E402
import water_journal as WJ  # noqa: E402

EXPECTED = 7
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


def journal_count(journal_db):
    conn = sqlite3.connect(journal_db)
    try:
        return conn.execute("SELECT COUNT(*) FROM water_windows").fetchone()[0]
    finally:
        conn.close()


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


class OfflineGate(object):
    """Deterministic runtime-failure stub: every check raises the
    gate-offline family (AC-SU5 precedent); the batch face degrades
    the text into the persistent queue - queued receipt = completed
    window with honest zero water cells."""

    def check_text(self, text):
        raise P.GateOfflineError("journal suite offline stub")


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-wj-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    frozen = {rel: sha256_file(os.path.join(BASE, rel))
              for rel in ("config.json", "store.py", "sec_batch.py")}
    db = os.path.join(tmp, "ugc.db")
    journal_db = os.path.join(tmp, "water_journal.db")
    lobby = load_lobby_store()
    ls = lobby.EventStore(db)
    gw = cfg["gate"]["gray_words"][0]
    fw = cfg["gate"]["forbidden_words"][0]
    disc = cfg["compliance"]["disclaimer"]
    env_susp = {"pool_water_delta": {"review.suspended": 1}, "total_delta": 1,
                "disclaimer": disc, "persistent": True}
    env_zero = {"pool_water_delta": {}, "total_delta": 0,
                "disclaimer": disc, "persistent": True}
    env_pass = {"pool_water_delta": {"review.suspended": -1,
                                     "review.verdicted.pass": 1},
                "total_delta": -1, "disclaimer": disc, "persistent": True}
    env_risky = {"pool_water_delta": {"review.suspended": -1,
                                      "review.verdicted.risky": 1},
                 "total_delta": -1, "disclaimer": disc, "persistent": True}

    def idea(actor, text):
        ls.append(lobby.utc_now_iso(), "idea.submit", actor, "cocreate",
                  text, payload={"text": text, "pool": "proposal-queue-stub"})

    pipe = P.UGCPipeline(cfg, db)
    try:
        # ---- AC-WJ1: module face + storage --------------------------
        reject_hits = []
        for bad in (None, "", "   ", 123):
            try:
                WJ.WaterJournalFace(os.path.join(tmp, "wj-reject.db"), bad)
                reject_hits.append("none")
            except ValueError:
                reject_hits.append("ValueError")
        reject_ok = reject_hits == ["ValueError"] * 4
        probe_db = os.path.join(tmp, "wj-probe.db")
        jf = WJ.WaterJournalFace(probe_db, disc)
        tables = [r[0] for r in sqlite3.connect(probe_db).execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        schema_ok = "water_windows" in tables
        bad_calls = []
        for kind, env in (("nope", env_zero),
                          ("submit", {"total_delta": 0}),
                          ("submit", {"pool_water_delta": {},
                                      "total_delta": True}),
                          ("submit", {"pool_water_delta": {},
                                      "total_delta": "0"})):
            try:
                jf.record(kind, env)
                bad_calls.append("none")
            except ValueError:
                bad_calls.append("ValueError")
        bad_ok = bad_calls == ["ValueError"] * 4
        with open(os.path.join(BASE, "water_journal.py"),
                  encoding="utf-8") as handle:
            wj_src = handle.read()
        no_update_ok = "UPDATE" not in wj_src and "DELETE" not in wj_src
        jf.close()
        wiring_ok = os.path.exists(journal_db)
        ugc_tables = [r[0] for r in sqlite3.connect(db).execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        touch_ok = "water_windows" not in ugc_tables
        kinds_ok = WJ.KINDS == ("ingest", "batch", "drain", "submit", "verdict")
        record("AC-WJ1",
               reject_ok and schema_ok and bad_ok and no_update_ok
               and wiring_ok and touch_ok and kinds_ok,
               "disclaimer-rejects=%s schema=%s bad-args=%s "
               "append-only-source=%s pipeline-wired=%s "
               "ugc-schema-untouched=%s kinds=%s"
               % (",".join(reject_hits), schema_ok, ",".join(bad_calls),
                  no_update_ok, wiring_ok, touch_ok, kinds_ok))

        # ---- AC-WJ2: one row per completed window -------------------
        board0 = pipe.journal.journal_board()
        zero_ok = board0["total"] == 0 and board0["journal_board"] == []
        rec1 = pipe.submit("avatar_intake", "A-wj2a", "gray probe one " + gw)
        r_submit = pipe.journal.journal_board()["journal_board"][-1]
        submit_ok = (r_submit["kind"] == "submit"
                    and r_submit["delta"] == {"review.suspended": 1}
                    and r_submit["total_delta"] == 1)
        idea("C-70001", "clean journal idea probe")
        pipe.ingest_lobby()
        r_ingest = pipe.journal.journal_board()["journal_board"][-1]
        ingest_ok = (r_ingest["kind"] == "ingest"
                     and r_ingest["delta"] == {}
                     and r_ingest["total_delta"] == 0)
        pipe.submit_batch("avatar_intake", "A-wj2b",
                          ["clean journal batch probe"])
        r_batch = pipe.journal.journal_board()["journal_board"][-1]
        batch_ok = r_batch["kind"] == "batch" and r_batch["delta"] == {}
        pipe.drain_recover()
        r_drain = pipe.journal.journal_board()["journal_board"][-1]
        drain_ok = (r_drain["kind"] == "drain" and r_drain["delta"] == {}
                    and r_drain["total_delta"] == 0)
        pipe.review_verdict(rec1["evt_id"], "pass")
        r_verdict = pipe.journal.journal_board()["journal_board"][-1]
        verdict_ok = (r_verdict["kind"] == "verdict"
                      and r_verdict["delta"] == env_pass["pool_water_delta"]
                      and r_verdict["total_delta"] == -1)
        five_kinds = [r["kind"] for r in
                      pipe.journal.journal_board()["journal_board"][:5]]
        kinds_seq_ok = (five_kinds
                        == ["submit", "ingest", "batch", "drain", "verdict"])
        n_mid = journal_count(journal_db)
        pipe.submit_batch("avatar_intake", "A-wj2c", [])
        empty_ok = journal_count(journal_db) == n_mid + 1
        last_empty = pipe.journal.journal_board()["journal_board"][-1]
        empty_row_ok = (last_empty["kind"] == "batch"
                        and last_empty["delta"] == {}
                        and last_empty["total_delta"] == 0)
        real_gate = pipe.batch.gate
        pipe.batch.gate = OfflineGate()
        try:
            rec_q = pipe.submit("avatar_intake", "A-wj2q",
                                "clean degraded journal probe")
        finally:
            pipe.batch.gate = real_gate
        n_deg = journal_count(journal_db)
        deg_row = pipe.journal.journal_board()["journal_board"][-1]
        degraded_ok = (isinstance(rec_q, dict) and rec_q.get("queued") is True
                       and n_deg == n_mid + 2
                       and deg_row["kind"] == "submit"
                       and deg_row["delta"] == {}
                       and deg_row["total_delta"] == 0)
        pipe.grant_entrance_sandbox("A-wj2r")
        for i in range(5):  # fill the direct rate window (5 per 10s)
            pipe.submit("direct", "A-wj2r", "rate probe %d" % (i + 1))
        n_pre = journal_count(journal_db)
        reject_codes = []

        def try_reject(fn):
            try:
                fn()
                reject_codes.append("none")
            except UGC.PipelineError as exc:
                reject_codes.append(exc.code)

        try_reject(lambda: pipe.submit("bogus_source", "A-wj2x", "bad source"))
        try_reject(lambda: pipe.submit("direct", "A-noent", "no entrance probe"))
        try_reject(lambda: pipe.submit("direct", "A-wj2r", "rate probe six"))
        try_reject(lambda: pipe.submit("avatar_intake", "A-wj2b", "   "))
        try_reject(lambda: pipe.submit("avatar_intake", "A-wj2f",
                                       "forbidden probe " + fw))
        ref_zero = journal_count(journal_db) == n_pre
        codes_ok = (reject_codes == [UGC.E_BAD_SOURCE, UGC.E_ENTRANCE_REQUIRED,
                                     UGC.E_RATE_LIMIT, UGC.E_BAD_FRAME,
                                     UGC.E_CONTENT_REJECTED])
        rec2 = pipe.submit("avatar_intake", "A-wj2v", "gray probe two " + gw)
        n_v = journal_count(journal_db)
        try_reject(lambda: pipe.review_verdict(rec2["evt_id"], "maybe"))
        try_reject(lambda: pipe.review_verdict("no-such-evt", "pass"))
        try_reject(lambda: pipe.review_verdict(rec1["evt_id"], "pass"))
        verdict_refusals_zero = journal_count(journal_db) == n_v
        try:
            pipe.review_verdict(rec2["evt_id"], "risky")
        except UGC.PipelineError:
            pass
        risky_row = pipe.journal.journal_board()["journal_board"][-1]
        risky_ok = (journal_count(journal_db) == n_v + 1
                    and risky_row["kind"] == "verdict"
                    and risky_row["delta"] == env_risky["pool_water_delta"]
                    and risky_row["total_delta"] == -1)
        record("AC-WJ2",
               zero_ok and submit_ok and ingest_ok and batch_ok and drain_ok
               and verdict_ok and kinds_seq_ok and empty_ok and empty_row_ok
               and degraded_ok and ref_zero and codes_ok
               and verdict_refusals_zero and risky_ok,
               "zero=%s five-kinds=%s empty=%s degraded=%s "
               "submit-refusals-zero=%s codes=%s verdict-refusals-zero=%s "
               "risky-row=%s"
               % (zero_ok, kinds_seq_ok, empty_row_ok, degraded_ok,
                  ref_zero, ",".join(reject_codes),
                  verdict_refusals_zero,
                  json.dumps(risky_row["delta"], sort_keys=True)))

        # ---- AC-WJ3: journal_board read-face contract ---------------
        rec3 = pipe.submit("avatar_intake", "A-wj3a", "gray probe three " + gw)
        board = pipe.journal.journal_board()
        env_keys_ok = set(board) == {"journal_board", "total",
                                     "ai_generated", "disclaimer",
                                     "persistent"}
        comp_ok = (board["ai_generated"] == 0
                   and board["disclaimer"] == disc
                   and board["persistent"] is True)
        rows = board["journal_board"]
        row_keys_ok = all(set(r) == {"window_id", "kind", "delta",
                                     "total_delta", "ts_utc"}
                          for r in rows)
        ids = [r["window_id"] for r in rows]
        id_order_ok = all(b > a for a, b in zip(ids, ids[1:]))
        ts_order_ok = all(a["ts_utc"] <= b["ts_utc"]
                          for a, b in zip(rows, rows[1:]))
        total_ok = board["total"] == len(rows) == journal_count(journal_db)
        last_row = rows[-1]
        roundtrip_ok = (last_row["kind"] == "submit"
                        and last_row["delta"]
                        == pipe.last_water_delta()["pool_water_delta"]
                        and pipe.last_water_delta() == env_susp
                        and rec3["suspended"] is True)
        record("AC-WJ3",
               env_keys_ok and comp_ok and row_keys_ok and id_order_ok
               and ts_order_ok and total_ok and roundtrip_ok,
               "envelope-keys=%s compliance=%s row-keys=%s id-ascending=%s "
               "ts-ascending=%s total=%s delta-roundtrip=%s"
               % (env_keys_ok, comp_ok, row_keys_ok, id_order_ok,
                  ts_order_ok, total_ok, roundtrip_ok))

        # ---- AC-WJ4: manual SQL cross-validation --------------------
        conn = sqlite3.connect(journal_db)
        manual = []
        for window_id, kind, delta, total_delta, ts_utc in conn.execute(
                "SELECT window_id, kind, delta, total_delta, ts_utc "
                "FROM water_windows ORDER BY ts_utc, window_id"):
            manual.append({"window_id": window_id, "kind": kind,
                           "delta": json.loads(delta),
                           "total_delta": total_delta, "ts_utc": ts_utc})
        conn.close()
        board_b = pipe.journal.journal_board()
        cross_ok = (manual == board_b["journal_board"]
                    and len(manual) == board_b["total"])
        record("AC-WJ4", cross_ok,
               "rows=%d dual-path-identical=%s kinds=%s"
               % (len(manual), cross_ok,
                  ",".join(r["kind"] for r in manual)))

        # ---- AC-WJ5: pure-read law + liveness -----------------------
        method_src = inspect.getsource(WJ.WaterJournalFace.journal_board)
        src_clean = ("INSERT" not in method_src
                    and "UPDATE" not in method_src
                    and "DELETE" not in method_src)
        static_a = five_table_counts(db)
        j_a = journal_count(journal_db)
        b1 = pipe.journal.journal_board()
        b2 = pipe.journal.journal_board()
        static_b = five_table_counts(db)
        j_b = journal_count(journal_db)
        pure_ok = (src_clean and static_a == static_b and j_a == j_b
                   and json.dumps(b1, sort_keys=True)
                   == json.dumps(b2, sort_keys=True))
        total_before = b2["total"]
        pipe.submit("avatar_intake", "A-wj5a", "gray probe four " + gw)
        live_ok = pipe.journal.journal_board()["total"] == total_before + 1
        record("AC-WJ5", pure_ok and live_ok,
               "read-method-clean=%s counts-stable=%s double-call-identical=%s "
               "liveness-plus-one=%s"
               % (src_clean, static_a == static_b and j_a == j_b,
                  json.dumps(b1, sort_keys=True)
                  == json.dumps(b2, sort_keys=True), live_ok))

        # ---- AC-WJ6: restart persistence (core value) ----------------
        rows_snapshot = pipe.journal.journal_board()["journal_board"]
        n_before = len(rows_snapshot)
        pipe.close()
        ls.close()
        pipe = P.UGCPipeline(cfg, db)  # fresh instance, same dbs
        ls = lobby.EventStore(db)
        slot_none_ok = pipe.last_water_delta() is None
        board_r = pipe.journal.journal_board()
        persist_ok = (board_r["total"] == n_before
                      and board_r["journal_board"] == rows_snapshot)
        rec4 = pipe.submit("avatar_intake", "A-wj6a", "gray probe five " + gw)
        resume_rows = pipe.journal.journal_board()["journal_board"]
        resume_ok = (resume_rows[-1]["window_id"] == n_before + 1
                     and resume_rows[-1]["kind"] == "submit"
                     and rec4["suspended"] is True)
        record("AC-WJ6", slot_none_ok and persist_ok and resume_ok,
               "slot-after-restart=None:%s rows-persisted=%s/%s "
               "window-id-monotonic=%s"
               % (slot_none_ok, board_r["total"], n_before,
                  resume_rows[-1]["window_id"]))

        # ---- AC-WJ7: hygiene + best-effort swallow + delivery --------
        class SqliteErrStub(object):
            def record(self, kind, envelope):
                raise sqlite3.OperationalError("ledger down")

        class ValErrStub(object):
            def record(self, kind, envelope):
                raise ValueError("wiring bug")

        real_journal = pipe.journal
        n_stub = journal_count(journal_db)
        pipe.journal = SqliteErrStub()
        try:
            rec_s = pipe.submit("avatar_intake", "A-wj7a",
                                "gray probe six " + gw)
            swallow_ok = (rec_s["suspended"] is True
                          and pipe.last_water_delta() == env_susp)
        finally:
            pipe.journal = real_journal
        swallow_zero = journal_count(journal_db) == n_stub
        pipe.journal = ValErrStub()
        propagate = "none"
        try:
            pipe.submit("avatar_intake", "A-wj7b", "gray probe seven " + gw)
        except ValueError:
            propagate = "ValueError"
        finally:
            pipe.journal = real_journal
        prop_ok = propagate == "ValueError"
        ascii_ok = True
        for rel in ("pipeline.py", "water_journal.py", os.path.basename(__file__)):
            with open(os.path.join(BASE, rel), "rb") as handle:
                ascii_ok = ascii_ok and max(handle.read()) < 128
        net_ok = True
        for rel in ("pipeline.py", "water_journal.py", os.path.basename(__file__)):
            with open(os.path.join(BASE, rel), encoding="utf-8") as handle:
                for line in handle:
                    s = line.strip()
                    if s.startswith("import ") or s.startswith("from "):
                        if any(w in s for w in ("urllib", "requests",
                                                "socket", "http")):
                            net_ok = False
        frozen_ok = all(sha256_file(os.path.join(BASE, rel)) == sha
                        for rel, sha in frozen.items())
        reg_path = os.path.normpath(os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ('"ugc-water-journal"' in reg_src
                  and "test_water_journal.py" in reg_src)
        record("AC-WJ7",
               swallow_ok and swallow_zero and prop_ok and ascii_ok
               and net_ok and frozen_ok and reg_ok,
               "sqlite-swallow=%s/%s valueerror-propagates=%s "
               "pure-ascii=%s import-lines-clean=%s frozen-bytes=%s "
               "registry-wired=%s"
               % (swallow_ok, swallow_zero, prop_ok, ascii_ok, net_ok,
                  frozen_ok, reg_ok))
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
