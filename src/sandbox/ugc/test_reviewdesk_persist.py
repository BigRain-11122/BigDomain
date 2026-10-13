"""Acceptance suite: review-desk read faces (pool_query +
chronicle_query) cross-restart persistence example (BigDomain R1917
tech-queue FIFO head claim; seed = the R1913 reseed). Both review-desk
read faces derive from the same ugc.db the pipeline owns, while their
derived purity across a full pipeline-stack restart had no pinned
example (R1889..R1916 persist family judgment reference). This suite
walks the REAL product path - clean submits through the public
avatar_intake face (no entrance grant), rule-template drafts, the
small-idea L0 adopt path, the landfall-keyword needs_ceo path with
the CEO approval receipt, and a reject that lands in the city
chronicle through export() - across UGCPipeline.close() -> fresh
UGCPipeline same-db same-config reopen (store + batch + journal all
reopen together; R1913 drainpersist carrier law).

Asserts the pre-registered criteria AC-RDP1..AC-RDP7 from the R1917
claim line in state/queue/tech.md (criteria were registered before
this code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Claim rulings (three, registered in the tech.md claim line):
1. restart carrier = the full pipeline stack: UGCPipeline.close()
   then a fresh UGCPipeline on the same config bytes and db path.
2. world = frozen-clock real record path: UGC.utc_now_iso holder
   patch with an incrementing fixed-stamp sequence (unique per-row
   ts -> ORDER BY i.ts_utc is a total order; avoids the AC-OS4 style
   tie-order implementation-defined gap). October window = six items
   (two ever-pooled anchors on two lines, one standing drafted body,
   one small-idea adopt, one reject -> chronicled, one landfall
   needs_ceo adopt); November window on the restarted instance =
   one new standing draft + one new small-idea adopt.
3. comparison face = dumps(sort_keys=True) byte equality on the
   four read shapes (pool whole / pool line-filtered x2 / chronicle
   whole) plus manual-SQL id-set cross-checks.

Zero product bytes change (suite-only round). This source stays pure
ASCII per the encoding discipline (Chinese copy lives in config.json,
the data file).

Usage: python test_reviewdesk_persist.py
"""

import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import pipeline as P                     # noqa: E402 (face under test)
import store as UGC                       # noqa: E402 (clock holder patch)

EXPECTED = 7
RESULTS = []

SEVEN_TABLES = ("ugc_events", "ugc_items", "review_queue",
                "ugc_ingest_log", "gate_receipts", "ugc_drafts",
                "ceo_receipts")
PRODUCT_FILES = ("pipeline.py", "store.py")
EXPORT_REL = "export-ac-rdp"

POOL_KEYS = {"item_id", "line", "state", "gate_status", "producer",
             "ai_generated", "needs_ceo", "duplicate_of", "decision",
             "ts_utc", "content", "author", "source", "evt_id", "draft"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def table_counts(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return {t: conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
                for t in SEVEN_TABLES}
    finally:
        conn.close()


def sql_ids(db_path, states, line=None):
    """Manual SQL cross-check face: same predicate + ORDER BY, read
    through a bare read-only connection (never the store face)."""
    conn = sqlite3.connect(db_path)
    try:
        sql = ("SELECT item_id FROM ugc_items WHERE state IN (%s)"
               % ",".join("?" * len(states)))
        args = list(states)
        if line is not None:
            sql += " AND line = ?"
            args.append(line)
        sql += " ORDER BY ts_utc"
        return [r[0] for r in conn.execute(sql, args)]
    finally:
        conn.close()


def iso_seq(base, n):
    """Deterministic fixed-stamp sequence (unique ts per row)."""
    return [(base + timedelta(seconds=i)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f") + "Z" for i in range(n)]


def by_id(env):
    return {i["evt_id"]: i for i in env["items"]}


def main():
    pre_sha = {f: sha256_file(os.path.join(BASE, f))
               for f in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as h:
        shipped = json.load(h)
    rules = shipped["routing"]["rules"]
    rule_fx = next(r for r in rules if r["line"] == "fluxverse")
    rule_bd = next(r for r in rules if r["line"] == "bigdomain")
    kw_fx = str(rule_fx["keywords"][0])
    kw_bd = str(rule_bd["keywords"][0])
    lk = str(shipped["approval"]["landfall_keywords"][0])
    labels = shipped["draft_template"]["labels"]
    chron_note = shipped["compliance"]["chronicle_note"]
    disc = shipped["compliance"]["disclaimer"]
    cfg = dict(shipped)
    cfg["export"] = dict(shipped.get("export") or {})
    cfg["export"]["dir"] = EXPORT_REL          # gitignored residue dir
    export_dir = os.path.join(BASE, EXPORT_REL)

    clock = {"seq": (iso_seq(datetime(2026, 10, 15, 8, 0, 0), 12)
                     + iso_seq(datetime(2026, 11, 7, 9, 0, 0), 8))}

    def frozen_now():
        seq = clock["seq"]
        return seq.pop(0) if len(seq) > 1 else seq[0]

    orig_now = UGC.utc_now_iso
    UGC.utc_now_iso = frozen_now

    tmp = tempfile.mkdtemp(prefix="ugc-rdp-")
    db = os.path.join(tmp, "ugc.db")
    snaps = {}
    fins = {}
    hyg = {}
    cleaned = False
    pipe = pipe2 = pipe3 = None
    try:
        pipe = P.UGCPipeline(cfg, db)

        # ---- October world: six items through the real product path --
        w1 = pipe.submit("avatar_intake", "A-rdp1",
                        "idea one about " + kw_fx)["evt_id"]
        w2 = pipe.submit("avatar_intake", "A-rdp2",
                        "idea two about " + kw_bd)["evt_id"]
        w3 = pipe.submit("avatar_intake", "A-rdp3",
                        "clean tiny idea number three")["evt_id"]
        w4 = pipe.submit("avatar_intake", "A-rdp4",
                         "small idea four " + kw_fx)["evt_id"]
        w5 = pipe.submit("avatar_intake", "A-rdp5",
                         "big plan five " + lk)["evt_id"]
        w6 = pipe.submit("avatar_intake", "A-rdp6",
                         "idea six around " + kw_bd)["evt_id"]
        pipe.draft(w3)
        pipe.draft(w4)
        pipe.draft(w5)
        pipe.draft(w6)
        fr3 = pipe.final_review(w3)
        pipe.final_decide(w3, "adopt")
        pipe.final_review(w4)
        pipe.final_decide(w4, "reject")
        fr5 = pipe.final_review(w5)
        pipe.record_ceo_decision(w5, "approved")
        pipe.final_decide(w5, "adopt")
        pipe.export()                      # rejected -> chronicled

        # ---- AC-RDP1: October world + pre-close four-shape snapshot --
        pool_env = pipe.pool_query()
        fx_env = pipe.pool_query(line="fluxverse")
        bd_env = pipe.pool_query(line="bigdomain")
        chron_env = pipe.chronicle_query()
        snaps = {"pool": dumps(pool_env), "fx": dumps(fx_env),
                 "bd": dumps(bd_env), "chron": dumps(chron_env)}
        pids = by_id(pool_env)
        ids_ok = ([i["evt_id"] for i in pool_env["items"]] == [w1, w2, w6]
                  and [i["evt_id"] for i in fx_env["items"]] == [w1]
                  and [i["evt_id"] for i in bd_env["items"]] == [w2, w6]
                  and [i["evt_id"] for i in chron_env["items"]]
                  == [w3, w4, w5])
        keys_ok = (set(pool_env) == {"items", "disclaimer", "persistent"}
                   and set(chron_env) == {"items", "disclaimer",
                                          "persistent", "note"}
                   and chron_env["note"] == chron_note
                   and pool_env["disclaimer"] == disc
                   and pool_env["persistent"] is True)
        row_w1 = pids[w1]
        row_w2 = pids[w2]
        row_w6 = pids[w6]
        rows_ok = (set(row_w1) == POOL_KEYS
                   and row_w1["state"] == "pooled"
                   and row_w1["draft"] is None
                   and row_w1["line"] == "fluxverse"
                   and row_w2["state"] == "pooled"
                   and row_w2["draft"] is None
                   and row_w2["line"] == "bigdomain"
                   and row_w6["state"] == "drafted"
                   and row_w6["draft"] is not None
                   and set(row_w6["draft"]) == {"title",
                                                str(labels["restated"]),
                                                str(labels["suggested_line"]),
                                                str(labels["matched_keywords"]),
                                                str(labels["risk_note"]),
                                                "producer", "ai_generated",
                                                "ai_label"}
                   and row_w6["draft"]["producer"] == "rule_template"
                   and row_w6["draft"]["ai_generated"] is False
                   and row_w6["draft"][str(labels["matched_keywords"])]
                   == [kw_bd]
                   and row_w6["draft"][str(labels["suggested_line"])]
                   == "bigdomain")
        cids = by_id(chron_env)
        chron_ok = (cids[w3]["state"] == "adopted"
                    and cids[w3]["signature_eligible"] is True
                    and cids[w3]["credit"] == "named"
                    and cids[w3]["decision"] == "adopted"
                    and cids[w3]["signature_slot"] == "A-rdp3"
                    and cids[w3]["summary"] == "clean tiny idea number three"
                    and cids[w4]["state"] == "chronicled"
                    and cids[w4]["signature_eligible"] is False
                    and cids[w4]["credit"] == "record-only"
                    and cids[w4]["decision"] == "rejected"
                    and cids[w5]["state"] == "adopted"
                    and cids[w5]["credit"] == "named"
                    and cids[w5]["decision"] == "adopted")
        cross_ok = (sql_ids(db, ("pooled", "drafted"))
                    == [i["evt_id"] for i in pool_env["items"]]
                    and sql_ids(db, ("pooled", "drafted"),
                                line="fluxverse")
                    == [w1]
                    and sql_ids(db, ("pooled", "drafted"),
                                line="bigdomain") == [w2, w6]
                    and sql_ids(db, ("adopted", "chronicled"))
                    == [w3, w4, w5])
        states_ok = (fr3["state"] == "final_review"
                     and fr3["needs_ceo"] is False
                     and fr5["state"] == "needs_ceo_review"
                     and fr5["needs_ceo"] is True)
        record("AC-RDP1",
               ids_ok and keys_ok and rows_ok and chron_ok
               and cross_ok and states_ok,
               "ids=%s keys=%s rows=%s chron-credit-mix=%s "
               "sql-cross=%s small-vs-landfall=%s"
               % (ids_ok, keys_ok, rows_ok, chron_ok, cross_ok,
                  states_ok))
        pipe.close()
        pipe = None

        # ---- AC-RDP2: cross-restart byte-identical four shapes -------
        pipe2 = P.UGCPipeline(cfg, db)
        r_pool = pipe2.pool_query()
        r_fx = pipe2.pool_query(line="fluxverse")
        r_bd = pipe2.pool_query(line="bigdomain")
        r_chron = pipe2.chronicle_query()
        replay_ok = (dumps(r_pool) == snaps["pool"]
                     and dumps(r_fx) == snaps["fx"]
                     and dumps(r_bd) == snaps["bd"]
                     and dumps(r_chron) == snaps["chron"])
        double_ok = (dumps(pipe2.pool_query()) == dumps(r_pool)
                    and dumps(pipe2.chronicle_query()) == dumps(r_chron))
        record("AC-RDP2", replay_ok and double_ok,
               "four-shape-replay=%s double-read-identical=%s"
               % (replay_ok, double_ok))

        # ---- AC-RDP3: new data post-restart -> recompute + freeze ----
        w7 = pipe2.submit("avatar_intake", "A-rdp7",
                          "idea seven around " + kw_bd)["evt_id"]
        pipe2.draft(w7)
        w8 = pipe2.submit("avatar_intake", "A-rdp8",
                          "clean tiny idea number eight")["evt_id"]
        pipe2.draft(w8)
        pipe2.final_review(w8)
        pipe2.final_decide(w8, "adopt")
        n_pool = pipe2.pool_query()
        n_fx = pipe2.pool_query(line="fluxverse")
        n_bd = pipe2.pool_query(line="bigdomain")
        n_chron = pipe2.chronicle_query()
        old_pool_rows = by_id(json.loads(snaps["pool"]))
        old_chron_rows = by_id(json.loads(snaps["chron"]))
        npr = by_id(n_pool)
        ncr = by_id(n_chron)
        recompute_ok = (dumps(n_pool) != snaps["pool"]
                        and [i["evt_id"] for i in n_pool["items"]]
                        == [w1, w2, w6, w7])
        bd_recompute = ([i["evt_id"] for i in n_bd["items"]]
                        == [w2, w6, w7]
                        and dumps(n_bd) != snaps["bd"])
        fx_freeze = dumps(n_fx) == snaps["fx"]
        rows_frozen = all(
            dumps(npr[key]) == dumps(old_pool_rows[key])
            for key in (w1, w2, w6))
        chron_recompute = ([i["evt_id"] for i in n_chron["items"]]
                           == [w3, w4, w5, w8]
                           and dumps(n_chron) != snaps["chron"]
                           and ncr[w8]["state"] == "adopted"
                           and ncr[w8]["credit"] == "named"
                           and ncr[w8]["signature_eligible"] is True)
        chron_frozen = all(
            dumps(ncr[key]) == dumps(old_chron_rows[key])
            for key in (w3, w4, w5))
        cross2_ok = (sql_ids(db, ("pooled", "drafted"))
                     == [w1, w2, w6, w7]
                     and sql_ids(db, ("pooled", "drafted"),
                                 line="bigdomain") == [w2, w6, w7]
                     and sql_ids(db, ("adopted", "chronicled"))
                     == [w3, w4, w5, w8])
        fins = {"pool": dumps(n_pool), "fx": dumps(n_fx),
                "bd": dumps(n_bd), "chron": dumps(n_chron)}
        record("AC-RDP3",
               recompute_ok and bd_recompute and fx_freeze
               and rows_frozen and chron_recompute and chron_frozen
               and cross2_ok,
               "pool-recompute=%s bd-recompute=%s fx-frozen=%s "
               "old-rows-frozen=%s chron-recompute=%s "
               "chron-rows-frozen=%s sql-cross=%s"
               % (recompute_ok, bd_recompute, fx_freeze, rows_frozen,
                  chron_recompute, chron_frozen, cross2_ok))

        # ---- AC-RDP4: filter semantics + honest empty + states -------
        empty = pipe2.pool_query(line="bigstream")
        pooled_only = pipe2.pool_query(states=("pooled",))
        drafted_only = pipe2.pool_query(states=("drafted",))
        empty_ok = (empty["items"] == []
                    and set(empty) == {"items", "disclaimer",
                                       "persistent"}
                    and empty["disclaimer"] == disc)
        states_ok2 = ([i["evt_id"] for i in pooled_only["items"]]
                      == [w1, w2]
                      and [i["evt_id"] for i in drafted_only["items"]]
                      == [w6, w7])
        record("AC-RDP4", empty_ok and states_ok2,
               "empty-line-honest=%s pooled-only=%s drafted-only=%s"
               % (empty_ok,
                  [i["evt_id"] for i in pooled_only["items"]] == [w1, w2],
                  states_ok2))
        pipe2.close()
        pipe2 = None

        # ---- AC-RDP5: third instance, double-restart stability --------
        pipe3 = P.UGCPipeline(cfg, db)
        t_pool = pipe3.pool_query()
        t_fx = pipe3.pool_query(line="fluxverse")
        t_bd = pipe3.pool_query(line="bigdomain")
        t_chron = pipe3.chronicle_query()
        replay3 = (dumps(t_pool) == fins["pool"]
                   and dumps(t_bd) == fins["bd"]
                   and dumps(t_chron) == fins["chron"])
        seq3 = (dumps(pipe3.pool_query()) == dumps(t_pool)
                and dumps(pipe3.pool_query(line="fluxverse"))
                == dumps(t_fx)
                and dumps(pipe3.pool_query(line="bigdomain"))
                == dumps(t_bd)
                and dumps(pipe3.chronicle_query()) == dumps(t_chron))
        oct_fx = dumps(pipe3.pool_query(line="fluxverse")) == snaps["fx"]
        record("AC-RDP5", replay3 and seq3 and oct_fx,
               "inst3==inst2-final=%s seq-double-read=%s "
               "fx==original-oct-snapshot=%s"
               % (replay3, seq3, oct_fx))

        # ---- AC-RDP6: pure-read law + hygiene evidence gathering -----
        before = table_counts(db)
        battery = [
            dumps(pipe3.pool_query()),
            dumps(pipe3.pool_query()),
            dumps(pipe3.pool_query(line="fluxverse")),
            dumps(pipe3.pool_query(line="bigstream")),
            dumps(pipe3.pool_query(states=("pooled",))),
            dumps(pipe3.pool_query(states=("drafted",))),
            dumps(pipe3.chronicle_query()),
            dumps(pipe3.chronicle_query()),
        ]
        battery_pair = (battery[0] == battery[1]
                        and battery[6] == battery[7])
        after = table_counts(db)
        pure_ok = before == after and battery_pair
        record("AC-RDP6", pure_ok,
               "seven-tables-stable=%s battery-pair=%s counts=%s"
               % (before == after, battery_pair,
                  ",".join("%s=%d" % (t, before[t])
                           for t in SEVEN_TABLES)))
        pipe3.close()
        pipe3 = None
        shutil.rmtree(export_dir, ignore_errors=True)
        cleaned = not os.path.exists(export_dir)

        with open(os.path.join(BASE, "pipeline.py"), encoding="utf-8") as h:
            pl_src = h.read()
        segs_ok = True
        for seg_name in ("def pool_query", "def _chronicle_row",
                         "def chronicle_query"):
            s = pl_src.find(seg_name)
            e = pl_src.find("\n    def ", s + 10)
            seg = pl_src[s:e]
            segs_ok = segs_ok and s >= 0 and e > s and not re.search(
                r"\bINSERT\b|\bUPDATE\b|\bDELETE\b", seg)
        with open(os.path.join(BASE, "store.py"), encoding="utf-8") as h:
            st_src = h.read()
        for seg_name in ("def items_in_states", "def draft_row"):
            s = st_src.find(seg_name)
            e = st_src.find("\n    def ", s + 10)
            seg = st_src[s:e]
            segs_ok = segs_ok and s >= 0 and e > s and not re.search(
                r"\bINSERT\b|\bUPDATE\b|\bDELETE\b", seg)
        ascii_ok = True
        for rel in ("pipeline.py", "store.py"):
            with open(os.path.join(BASE, rel), "rb") as h:
                ascii_ok = ascii_ok and max(h.read()) < 128
        with open(os.path.abspath(__file__), "rb") as h:
            ascii_ok = ascii_ok and max(h.read()) < 128
        net_ok = True
        for rel in ("pipeline.py", "store.py", os.path.abspath(__file__)):
            with open(rel if os.path.isabs(rel) else
                      os.path.join(BASE, rel), encoding="utf-8") as h:
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
        reg_ok = ('"ugc-reviewdesk-persist"' in reg_src
                 and "test_reviewdesk_persist.py" in reg_src)
        expected_ok = len(RESULTS) == EXPECTED - 1  # this one pending
        hyg = {"pure_ok": pure_ok, "segs_ok": segs_ok,
               "ascii_ok": ascii_ok, "net_ok": net_ok,
               "reg_ok": reg_ok, "expected_ok": expected_ok}
    finally:
        UGC.utc_now_iso = orig_now
        if pipe is not None:
            pipe.close()
        if pipe2 is not None:
            pipe2.close()
        if pipe3 is not None:
            pipe3.close()
        shutil.rmtree(export_dir, ignore_errors=True)

    restore_ok = UGC.utc_now_iso is orig_now
    post_sha = {f: sha256_file(os.path.join(BASE, f))
                for f in PRODUCT_FILES}
    sha_ok = pre_sha == post_sha
    record("AC-RDP7",
           hyg.get("pure_ok") and hyg.get("segs_ok")
           and hyg.get("ascii_ok") and hyg.get("net_ok")
           and hyg.get("reg_ok") and hyg.get("expected_ok")
           and restore_ok and sha_ok and cleaned,
           "pure-read=%s face-segments-strip=%s ascii=%s net-clean=%s "
           "registry-wired=%s clock-restored=%s product-sha-stable=%s "
           "export-residue-cleaned=%s"
           % (hyg.get("pure_ok"), hyg.get("segs_ok"),
              hyg.get("ascii_ok"), hyg.get("net_ok"),
              hyg.get("reg_ok"), restore_ok, sha_ok, cleaned))

    ok_all = len(RESULTS) == EXPECTED and all(ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                              sum(1 for _a, ok in RESULTS if ok),
                              EXPECTED), flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
