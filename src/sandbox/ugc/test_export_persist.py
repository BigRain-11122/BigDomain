"""Acceptance suite: UGC export three-outflow faces (proposal_feed
per-line jsonl + chronicle.jsonl + hot_index.jsonl) same-instance
re-export determinism + chronicle-step migration idempotency +
cross-restart file-byte persistence example (BigDomain R1920 tech-
queue FIFO head claim; seed = the R1917 reseed). This suite adopts
the crashed round's orphan claim line (claim + AC-EXP1..EXP7 were
pre-registered in state/queue/tech.md before this code existed;
honesty law; R1919 orphan-adoption precedent). The export outflow
faces derive from the same ugc.db the pipeline owns, while their
FILE bytes across a same-instance re-export, a full pipeline-stack
restart and post-restart new data had no pinned example (R1889..
R1919 persist family judgment reference).

World = the R1917 October shape (two ever-pooled anchors on two
lines, one standing drafted body, one small-idea adopt, one reject
that lands in the city chronicle through the export-embedded
chronicle step, one landfall needs_ceo adopt) plus the claim's
designed score-tie pairs: W1/W2 pooled with runtime-equal content
lengths and W3/W8 adopted with twin 28-char contents. November
window on the restarted instance = one new standing draft + one
new small-idea adopt, stamped through a TWO-PHASE frozen clock
(holder patch on UGC.utc_now_iso; the October phase hands out
unique increasing Oct stamps, the November phase is armed right
before the November submits so the new rows carry true November
ts - unique per-row ts -> ORDER BY i.ts_utc is a total order, the
AC-OS4 tie-gap avoidance, R1917 carrier).

One claim-line criteria fix, honestly noted (R1918/R1919 suite-
dialect precedent): the claim's AC-EXP1 clause "the W6 feed row
carries the draft body" conflates the pool_query shape (which
carries the draft body) with the shipped feed face - feed rows
carry the draft MARKERS (state=drafted, producer=rule_template,
ai_generated=False, stamped at intake by insert_item) and never a
draft body; the suite-only zero-product-change law keeps the
shipped nine-key feed face as-is, so this suite pins the real
shape.

Zero product bytes change (suite-only round). This source stays
pure ASCII per the encoding discipline (Chinese copy lives in
config.json, the data file).

Usage: python test_export_persist.py
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

PRODUCT_FILES = ("pipeline.py", "store.py", "config.json")
ASCII_FILES = ("pipeline.py", "store.py")
EXPORT_REL = "export-ac-exp"
REPO_ROOT = os.path.realpath(os.path.join(BASE, "..", "..", ".."))

FEED_KEYS = {"evt_id", "line", "state", "producer", "ai_generated",
             "duplicate_of", "content", "ts_utc", "disclaimer"}
CHRON_KEYS = {"evt_id", "summary", "decision", "state",
              "signature_slot", "signature_eligible", "credit",
              "ts_utc", "disclaimer"}
HOT_KEYS = {"evt_id", "score", "line", "state", "summary", "ts_utc",
            "disclaimer"}
FX_REL = "proposal_feed/fluxverse.jsonl"
BD_REL = "proposal_feed/bigdomain.jsonl"
CH_REL = "chronicle.jsonl"
HOT_REL = "hot_index.jsonl"
FOUR = (FX_REL, BD_REL, CH_REL, HOT_REL)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def canon(row):
    return json.dumps(row, ensure_ascii=False, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def sql_scalar(db, sql, args=()):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql, args).fetchone()
    finally:
        conn.close()


def sql_ids(db, states, line=None):
    """Manual SQL cross face: same predicate + ORDER BY, read through
    a bare read-only connection (never the store face)."""
    conn = sqlite3.connect(db)
    try:
        sql = ("SELECT i.item_id FROM ugc_items i JOIN ugc_events e"
               " ON e.evt_id = i.item_id WHERE i.state IN (%s)"
               % ",".join("?" * len(states)))
        args = list(states)
        if line is not None:
            sql += " AND i.line = ?"
            args.append(line)
        sql += " ORDER BY i.ts_utc"
        return [r[0] for r in conn.execute(sql, args)]
    finally:
        conn.close()


def sql_state_rows(db, states):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(
            "SELECT i.item_id, i.ts_utc, e.summary FROM ugc_items i"
            " JOIN ugc_events e ON e.evt_id = i.item_id"
            " WHERE i.state IN (%s) ORDER BY i.ts_utc"
            % ",".join("?" * len(states)), list(states)).fetchall()
    finally:
        conn.close()


def hot_expectation(db, hot_min, factor):
    """Manual single-derivation expectation: SQL ts-ascending x the
    score>=hot_min filter x stable sort score desc (the tie law: the
    stable sort keeps the items_in_states ts-ascending order inside
    every equal-score segment)."""
    kept = [(iid, ts, content) for iid, ts, content
            in sql_state_rows(db, ("pooled", "drafted", "adopted"))
            if len(content) * factor >= hot_min]
    kept.sort(key=lambda r: len(r[2]) * factor, reverse=True)
    return [r[0] for r in kept]


def walk_rel(root):
    found = set()
    for dirpath, _dirs, names in os.walk(root):
        for name in names:
            found.add(os.path.relpath(
                os.path.join(dirpath, name), root).replace(os.sep, "/"))
    return found


def export_snap(pipe):
    """One export + full raw/sha/rows snapshot of every registry
    file (the comparison face: product-file original bytes)."""
    reg = pipe.export()
    snap = {}
    for rel, count in reg["files"].items():
        path = os.path.join(pipe.export_dir, rel)
        with open(path, "rb") as handle:
            raw = handle.read()
        rows = [json.loads(line) for line in
                raw.decode("utf-8").splitlines()]
        snap[rel] = {"sha": hashlib.sha256(raw).hexdigest(),
                     "raw": raw, "rows": rows, "count": count}
    return reg, snap


def iso_seq(base, n):
    """Deterministic fixed-stamp sequence (unique ts per row)."""
    return [(base + timedelta(seconds=i)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f") + "Z" for i in range(n)]


def row_by_id(rows, evt_id):
    return next(r for r in rows if r["evt_id"] == evt_id)


def snap_ok_full(s_a, s_b):
    return all(s_a[rel]["sha"] == s_b[rel]["sha"]
               and s_a[rel]["raw"] == s_b[rel]["raw"]
               and s_a[rel]["rows"] == s_b[rel]["rows"]
               for rel in FOUR)


def main():
    pre_sha = {f: sha256_file(os.path.join(BASE, f))
               for f in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as h:
        shipped = json.load(h)
    rules = shipped["routing"]["rules"]
    kw_fx = str(next(r for r in rules
                     if r["line"] == "fluxverse")["keywords"][0])
    kw_bd = str(next(r for r in rules
                     if r["line"] == "bigdomain")["keywords"][0])
    lk = str(shipped["approval"]["landfall_keywords"][0])
    disc = shipped["compliance"]["disclaimer"]
    hot_min = int(shipped["hot"]["min_score"])
    hot_factor = int(shipped["hot"]["score_len_factor"])
    cfg = dict(shipped)
    cfg["export"] = dict(shipped.get("export") or {})
    cfg["export"]["dir"] = EXPORT_REL          # gitignored residue dir
    export_dir = os.path.join(BASE, EXPORT_REL)

    clock = {"seq": []}

    def arm_clock(base, n):
        clock["seq"] = iso_seq(base, n)

    def frozen_now():
        seq = clock["seq"]
        return seq.pop(0) if len(seq) > 1 else seq[0]

    orig_now = UGC.utc_now_iso
    UGC.utc_now_iso = frozen_now
    arm_clock(datetime(2026, 10, 15, 8, 0, 0), 16)   # October phase

    shutil.rmtree(export_dir, ignore_errors=True)
    tmp = tempfile.mkdtemp(prefix="ugc-exp-")
    db = os.path.join(tmp, "ugc.db")
    hyg = {}
    cleaned = False
    pipe = pipe2 = pipe3 = None
    try:
        pipe = P.UGCPipeline(cfg, db)

        # ---- October world: six items through the real product path --
        w1 = pipe.submit("avatar_intake", "A-exp1",
                        "idea one about " + kw_fx)["evt_id"]
        w2 = pipe.submit("avatar_intake", "A-exp2",
                        "idea two about " + kw_bd)["evt_id"]
        w3 = pipe.submit("avatar_intake", "A-exp3",
                        "clean tiny idea number three")["evt_id"]
        w4 = pipe.submit("avatar_intake", "A-exp4",
                         "small idea four " + kw_fx)["evt_id"]
        w5 = pipe.submit("avatar_intake", "A-exp5",
                         "big plan five " + lk)["evt_id"]
        w6 = pipe.submit("avatar_intake", "A-exp6",
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

        # ---- AC-EXP1: first export + October face snapshots ----------
        reg1, s1 = export_snap(pipe)
        rej0 = sql_scalar(
            db, "SELECT COUNT(*) FROM ugc_items"
            " WHERE state='rejected'")[0]
        w4_state = sql_scalar(
            db, "SELECT state FROM ugc_items WHERE item_id=?",
            (w4,))[0]
        chron_ok_step = (rej0 == 0 and w4_state == "chronicled")
        reg_counts_ok = (reg1["files"]
                         == {FX_REL: 1, BD_REL: 2, CH_REL: 3,
                             HOT_REL: 5}
                         and walk_rel(export_dir) == set(FOUR)
                         and set(reg1["files"]) == set(FOUR)
                         and reg1["export_dir"] == pipe.export_dir
                         == os.path.realpath(export_dir))
        fx_ids = [r["evt_id"] for r in s1[FX_REL]["rows"]]
        bd_ids = [r["evt_id"] for r in s1[BD_REL]["rows"]]
        ch_ids = [r["evt_id"] for r in s1[CH_REL]["rows"]]
        hot_ids1 = [r["evt_id"] for r in s1[HOT_REL]["rows"]]
        ids_ok = (fx_ids == [w1] and bd_ids == [w2, w6]
                  and ch_ids == [w3, w4, w5]
                  and hot_ids1 == hot_expectation(
                      db, hot_min, hot_factor)
                  and len(hot_ids1) == 5)
        cross_ok = (sql_ids(db, ("pooled", "drafted"), "fluxverse")
                    == [w1]
                    and sql_ids(db, ("pooled", "drafted"), "bigdomain")
                    == [w2, w6]
                    and sql_ids(db, ("adopted", "chronicled"))
                    == [w3, w4, w5]
                    and set(hot_ids1) == set(hot_expectation(
                        db, hot_min, hot_factor)))
        canon_ok = True
        keymap = {FX_REL: FEED_KEYS, BD_REL: FEED_KEYS,
                  CH_REL: CHRON_KEYS, HOT_REL: HOT_KEYS}
        for rel in FOUR:
            lines = s1[rel]["raw"].decode("utf-8").splitlines()
            for line, row in zip(lines, s1[rel]["rows"]):
                canon_ok = (canon_ok and canon(row) == line
                            and set(row) == keymap[rel]
                            and row["disclaimer"] == disc)
        r1 = row_by_id(s1[FX_REL]["rows"], w1)
        r2 = row_by_id(s1[BD_REL]["rows"], w2)
        r6 = row_by_id(s1[BD_REL]["rows"], w6)
        w6row_ok = (r6["state"] == "drafted"
                    and r6["producer"] == "rule_template"
                    and r6["ai_generated"] is False
                    and set(r6) == FEED_KEYS)
        c3 = row_by_id(s1[CH_REL]["rows"], w3)
        c4 = row_by_id(s1[CH_REL]["rows"], w4)
        c5 = row_by_id(s1[CH_REL]["rows"], w5)
        mix_ok = (c3["state"] == "adopted"
                  and c3["credit"] == "named"
                  and c3["decision"] == "adopted"
                  and c3["signature_eligible"] is True
                  and c4["state"] == "chronicled"
                  and c4["credit"] == "record-only"
                  and c4["decision"] == "rejected"
                  and c4["signature_eligible"] is False
                  and c5["state"] == "adopted"
                  and c5["credit"] == "named"
                  and c5["decision"] == "adopted")
        h1 = row_by_id(s1[HOT_REL]["rows"], w1)
        h2 = row_by_id(s1[HOT_REL]["rows"], w2)
        tie_ok = (len(r1["content"]) == len(r2["content"])
                  and h1["score"] == h2["score"]
                  and hot_ids1.index(w1) < hot_ids1.index(w2)
                  and h1["score"] >= hot_min)
        record("AC-EXP1",
               chron_ok_step and reg_counts_ok and ids_ok and cross_ok
               and canon_ok and w6row_ok and mix_ok and tie_ok
               and fr3["state"] == "final_review"
               and fr5["state"] == "needs_ceo_review",
               "chron-step=%s registry=%s ids=%s sql-cross=%s "
               "canonical=%s w6-draft-markers=%s credit-mix=%s "
               "w1w2-score-tie=%s shas=%s"
               % (chron_ok_step, reg_counts_ok, ids_ok, cross_ok,
                  canon_ok, w6row_ok, mix_ok, tie_ok,
                  ",".join(s1[rel]["sha"][:6] for rel in FOUR)))

        # ---- AC-EXP2: same-instance re-export determinism -------------
        pre_ts = sql_scalar(
            db, "SELECT ts_utc FROM ugc_items WHERE item_id=?",
            (w4,))[0]
        reg2, s2 = export_snap(pipe)
        files_same = snap_ok_full(s2, s1)
        reg_same = dumps(reg2) == dumps(reg1)
        post_rej = sql_scalar(
            db, "SELECT COUNT(*) FROM ugc_items"
            " WHERE state='rejected'")[0]
        post_ts = sql_scalar(
            db, "SELECT ts_utc FROM ugc_items WHERE item_id=?",
            (w4,))[0]
        post_state = sql_scalar(
            db, "SELECT state FROM ugc_items WHERE item_id=?",
            (w4,))[0]
        mig_ok = (pre_ts == post_ts and post_rej == 0
                  and post_state == "chronicled")
        record("AC-EXP2", files_same and reg_same and mig_ok,
               "four-files-byte-same=%s registry-same=%s "
               "migration-idempotent=%s rejected=%d "
               "w4-ts-unchanged=%s w4-state=%s"
               % (files_same, reg_same, mig_ok, post_rej,
                  pre_ts == post_ts, post_state))
        pipe.close()
        pipe = None

        # ---- AC-EXP3: cross-restart file-byte persistence -------------
        pipe2 = P.UGCPipeline(cfg, db)
        reg3, s3 = export_snap(pipe2)
        replay3 = snap_ok_full(s3, s1)
        reg3_ok = dumps(reg3) == dumps(reg1)
        record("AC-EXP3", replay3 and reg3_ok,
               "four-files-replay=%s registry-eq=%s"
               % (replay3, reg3_ok))

        # ---- AC-EXP4: November data -> zero-cache recompute -----------
        arm_clock(datetime(2026, 11, 7, 9, 0, 0), 8)  # November phase
        w7 = pipe2.submit("avatar_intake", "A-exp7",
                          "idea seven around " + kw_bd)["evt_id"]
        pipe2.draft(w7)
        w8 = pipe2.submit("avatar_intake", "A-exp8",
                         "clean tiny idea number eight")["evt_id"]
        pipe2.draft(w8)
        pipe2.final_review(w8)
        pipe2.final_decide(w8, "adopt")
        reg4, s4 = export_snap(pipe2)
        r7 = row_by_id(s4[BD_REL]["rows"], w7)
        r8 = row_by_id(s4[CH_REL]["rows"], w8)
        # the shipped _write_jsonl writes text mode, so the on-disk
        # terminator is the platform default (CRLF here); the append
        # reconstruction follows the file's own terminator (zero
        # product change, the suite pins the shipped behavior)
        term = b"\r\n" if b"\r\n" in s1[BD_REL]["raw"] else b"\n"
        fx_frozen = s4[FX_REL]["raw"] == s1[FX_REL]["raw"]
        bd_append = (s4[BD_REL]["raw"]
                     == s1[BD_REL]["raw"]
                     + canon(r7).encode("utf-8") + term)
        ch_append = (s4[CH_REL]["raw"]
                     == s1[CH_REL]["raw"]
                     + canon(r8).encode("utf-8") + term)
        hot_ids4 = [r["evt_id"] for r in s4[HOT_REL]["rows"]]
        hot_changed = (s4[HOT_REL]["raw"] != s1[HOT_REL]["raw"]
                      and w7 in hot_ids4 and w8 in hot_ids4)
        nov_ok = (r7["ts_utc"].startswith("2026-11-07")
                  and r8["ts_utc"].startswith("2026-11-07"))
        cross4 = ([r["evt_id"] for r in s4[BD_REL]["rows"]]
                  == [w2, w6, w7]
                  and [r["evt_id"] for r in s4[CH_REL]["rows"]]
                  == [w3, w4, w5, w8]
                  and sql_ids(db, ("pooled", "drafted"), "bigdomain")
                  == [w2, w6, w7]
                  and sql_ids(db, ("adopted", "chronicled"))
                  == [w3, w4, w5, w8]
                  and set(hot_ids4) == set(hot_expectation(
                      db, hot_min, hot_factor)))
        shape4 = (r7["state"] == "drafted"
                  and r8["state"] == "adopted"
                  and r8["credit"] == "named"
                  and r8["signature_eligible"] is True)
        record("AC-EXP4",
               fx_frozen and bd_append and ch_append and hot_changed
               and nov_ok and cross4 and shape4,
               "fx-frozen=%s bd-append=%s chron-append=%s "
               "hot-recompute=%s nov-ts=%s sql-cross=%s shapes=%s"
               % (fx_frozen, bd_append, ch_append, hot_changed,
                  nov_ok, cross4, shape4))

        # ---- AC-EXP5: hot_index ordering determinism ------------------
        rows4 = s4[HOT_REL]["rows"]
        seq_ok = hot_ids4 == hot_expectation(db, hot_min, hot_factor)
        tie_idx = (hot_ids4.index(w1) < hot_ids4.index(w2)
                   and hot_ids4.index(w3) < hot_ids4.index(w8))
        len28 = (len(row_by_id(s4[CH_REL]["rows"], w3)["summary"]) == 28
                 and len(r8["summary"]) == 28
                 and row_by_id(rows4, w3)["score"]
                 == row_by_id(rows4, w8)["score"])
        generic_ok = True
        for i in range(1, len(rows4)):
            generic_ok = (generic_ok
                          and rows4[i - 1]["score"] >= rows4[i]["score"])
            if rows4[i - 1]["score"] == rows4[i]["score"]:
                generic_ok = (generic_ok
                              and rows4[i - 1]["ts_utc"]
                              < rows4[i]["ts_utc"])
        record("AC-EXP5", seq_ok and tie_idx and len28 and generic_ok,
               "observed==derivation=%s tie-pairs-ts-asc=%s "
               "w3w8-28char-tie=%s generic-segments=%s "
               "order=%s"
               % (seq_ok, tie_idx, len28, generic_ok,
                  ",".join(x[:6] for x in hot_ids4)))
        pipe2.close()
        pipe2 = None

        # ---- AC-EXP6: third instance, double-restart stability ---------
        pipe3 = P.UGCPipeline(cfg, db)
        reg5, s5 = export_snap(pipe3)
        replay5 = snap_ok_full(s5, s4)
        reg5_ok = dumps(reg5) == dumps(reg4)
        reg5b, s5b = export_snap(pipe3)
        double5 = snap_ok_full(s5b, s5)
        reg5b_ok = dumps(reg5b) == dumps(reg5)
        record("AC-EXP6",
               replay5 and reg5_ok and double5 and reg5b_ok,
               "inst3==inst2-final=%s registry-eq=%s "
               "in-inst3-double-export=%s"
               % (replay5 and reg5_ok, reg5_ok, double5 and reg5b_ok))
        pipe3.close()
        pipe3 = None
        shutil.rmtree(export_dir, ignore_errors=True)
        cleaned = not os.path.exists(export_dir)

        # ---- AC-EXP7: hygiene face --------------------------------------
        post_sha = {f: sha256_file(os.path.join(BASE, f))
                    for f in PRODUCT_FILES}
        sha_ok = pre_sha == post_sha
        with open(os.path.join(BASE, "pipeline.py"),
                  encoding="utf-8") as h:
            pl_src = h.read()
        s_seg = pl_src.find("    def export(self):")
        e_seg = pl_src.find("\n    def ", s_seg + 10)
        seg = pl_src[s_seg:e_seg]
        seg_ok = (s_seg >= 0 and e_seg > s_seg
                  and len(re.findall(r"\bUPDATE\b", seg)) == 1
                  and not re.search(r"\bINSERT\b|\bDELETE\b", seg))
        ascii_ok = True
        for path in ([os.path.join(BASE, f) for f in ASCII_FILES]
                     + [os.path.abspath(__file__)]):
            with open(path, "rb") as h:
                ascii_ok = ascii_ok and max(h.read()) < 128
        net_ok = True
        for path in ([os.path.join(BASE, f)
                      for f in ASCII_FILES]
                     + [os.path.abspath(__file__)]):
            with open(path, encoding="utf-8") as h:
                for line in h:
                    st = line.strip()
                    if st.startswith("import ") \
                            or st.startswith("from "):
                        if any(w in st for w in
                               ("urllib", "requests", "socket",
                                "http")):
                            net_ok = False
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as h:
            reg_src = h.read()
        reg_ok = ('"ugc-export-persist"' in reg_src
                  and "test_export_persist.py" in reg_src)
        world_ok = True
        try:
            world_ok = (os.path.commonpath(
                [REPO_ROOT, os.path.realpath(db)]) != REPO_ROOT)
        except ValueError:
            world_ok = False
        expected_ok = len(RESULTS) == EXPECTED - 1
        hyg = {"sha_ok": sha_ok, "seg_ok": seg_ok,
               "ascii_ok": ascii_ok, "net_ok": net_ok,
               "reg_ok": reg_ok, "world_ok": world_ok,
               "expected_ok": expected_ok}
    finally:
        UGC.utc_now_iso = orig_now
        if pipe is not None:
            pipe.close()
        if pipe2 is not None:
            pipe2.close()
        if pipe3 is not None:
            pipe3.close()
        shutil.rmtree(export_dir, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)

    restore_ok = UGC.utc_now_iso is orig_now
    record("AC-EXP7",
           hyg.get("sha_ok") and hyg.get("seg_ok")
           and hyg.get("ascii_ok") and hyg.get("net_ok")
           and hyg.get("reg_ok") and hyg.get("world_ok")
           and hyg.get("expected_ok")
           and restore_ok and cleaned,
           "product-sha-stable=%s export-seg-one-UPDATE=%s ascii=%s "
           "net-clean=%s registry-wired=%s world-db-outside-repo=%s "
           "clock-restored=%s export-residue-cleaned=%s "
           "criteria-drift=%s"
           % (hyg.get("sha_ok"), hyg.get("seg_ok"),
              hyg.get("ascii_ok"), hyg.get("net_ok"),
              hyg.get("reg_ok"), hyg.get("world_ok"),
              restore_ok, cleaned, hyg.get("expected_ok")))

    ok_all = len(RESULTS) == EXPECTED and all(ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                             sum(1 for _a, ok in RESULTS if ok),
                             EXPECTED), flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
