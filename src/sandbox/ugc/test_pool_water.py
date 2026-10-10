"""Acceptance suite for the UGC noise/review pool water-level read
face (tech.md claim line R1777).

Asserts the pre-registered criteria AC-NP1..AC-NP7 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Subject: UGCStore.pool_water_levels() - pure-read derived water
levels for the two diverting pools of the intake pipeline:
  - noise pool: intake events whose payload carries a truthy noise
    flag (honest triage keeps the row, never pools it - AC-U5)
  - review pool: gray-zone cases parked at the review desk (verdict
    pending = suspended; decided cases stay visible in the
    verdicted tally)
Counts derive live on every call (zero stored counters, zero cache);
reasons sort ascending, the closed-set verdict tally keeps both zero
cells explicit. Envelope carries the standing non-advisory
disclaimer (resident face, R1773 store-envelope precedent).

Usage: python test_pool_water.py
"""

import inspect
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import pipeline as P                      # noqa: E402 (real-flow world)
import store as UGC                       # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7
TEST_DISCLAIMER = ("sandbox non-advisory standing disclaimer "
                   "(pool-water probe)")
TABLES = ("ugc_events", "ugc_items", "review_queue",
          "ugc_ingest_log", "gate_receipts")
EMOJI = "\U0001F44D\U0001F44D"


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def table_counts(db):
    conn = sqlite3.connect(db)
    try:
        return {t: int(conn.execute(
            "SELECT COUNT(*) FROM %s" % t).fetchone()[0]) for t in TABLES}
    finally:
        conn.close()


def sql_rows(db, sql):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def face_for(db):
    """Store read instance wired with the standing disclaimer."""
    return UGC.UGCStore(db, disclaimer=TEST_DISCLAIMER)


def build_world(cfg, db):
    """Real-flow world through the pipeline: all three noise reasons,
    gray suspended + both verdicts, clean pooled control rows."""
    wcfg = json.loads(json.dumps(cfg))
    wcfg["noise"] = dict(wcfg.get("noise") or {}, flood_max_submissions=2)
    wcfg["export"] = dict(wcfg.get("export") or {}, dir="export-np-test")
    pipe = P.UGCPipeline(wcfg, db)
    gw = wcfg["gate"]["gray_words"][0]
    kw = wcfg["routing"]["rules"][0]["keywords"][0]

    out = {}
    out["emoji"] = pipe.submit("avatar_intake", "C-np1", EMOJI)
    out["short"] = pipe.submit("avatar_intake", "C-np2", "ab")
    out["f1"] = pipe.submit("avatar_intake", "C-np3", "flood probe one")
    out["f2"] = pipe.submit("avatar_intake", "C-np3", "flood probe two")
    out["flood"] = pipe.submit("avatar_intake", "C-np3", "flood probe three")
    out["gray1"] = pipe.submit("avatar_intake", "C-np4", "gray park " + gw)
    out["gray2"] = pipe.submit("avatar_intake", "C-np5",
                               "gray risky " + gw + " park")
    try:
        pipe.review_verdict(out["gray2"]["evt_id"], "risky")
        out["risky"] = {"rejected": False}
    except UGC.PipelineError as exc:
        out["risky"] = {"rejected": exc.code == UGC.E_CONTENT_REJECTED}
    out["gray3"] = pipe.submit("avatar_intake", "C-np6",
                               "gray pass " + gw + " park")
    out["repool"] = pipe.review_verdict(out["gray3"]["evt_id"], "pass")
    out["clean1"] = pipe.submit("avatar_intake", "C-np7",
                                "clean idea about " + kw)
    out["clean2"] = pipe.submit("avatar_intake", "C-np8",
                                "clean second idea about " + kw)
    return pipe, out


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-np-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    export_test_dir = os.path.join(BASE, "export-np-test")

    # ---- AC-NP1: contract, empty state, disclaimer gates ---------------
    empty_db = os.path.join(tmp, "empty.db")
    legacy = UGC.UGCStore(empty_db)                 # legacy constructor
    env0 = None
    legacy_refused = False
    try:
        legacy.pool_water_levels()
    except ValueError as exc:
        legacy_refused = "E_STORE_NO_DISCLAIMER" in str(exc)
    legacy.close()
    bad_construct = []
    for probe in ("", "   ", 123):
        try:
            UGC.UGCStore(os.path.join(tmp, "bad.db"), disclaimer=probe)
            bad_construct.append(probe)
        except ValueError:
            pass
    store = face_for(empty_db)
    env0 = store.pool_water_levels()
    env_keys = set(env0) == {"pool_water_levels", "total",
                             "disclaimer", "persistent"}
    levels = env0["pool_water_levels"]
    lvl_keys = set(levels) == {"noise", "review"}
    noise_keys = set(levels["noise"]) == {"total", "by_reason"}
    review_keys = set(levels["review"]) == {"suspended", "verdicted"}
    empty_ok = (env_keys and lvl_keys and noise_keys and review_keys
                and levels["noise"]["total"] == 0
                and levels["noise"]["by_reason"] == {}
                and levels["review"]["suspended"] == 0
                and levels["review"]["verdicted"] == {"pass": 0, "risky": 0}
                and env0["total"] == 0
                and env0["disclaimer"] == TEST_DISCLAIMER
                and env0["persistent"] is True)
    ok1 = empty_ok and legacy_refused and not bad_construct
    record("AC-NP1", ok1,
           "empty-state=%s legacy-refused=%s bad-construct=%s"
           % (empty_ok, legacy_refused, bad_construct))
    store.close()

    # ---- AC-NP2: dual-path cross-validation on the real-flow world ----
    db = os.path.join(tmp, "world.db")
    pipe, w = build_world(cfg, db)
    store = face_for(db)
    env2 = store.pool_water_levels()
    noise = env2["pool_water_levels"]["noise"]
    review = env2["pool_water_levels"]["review"]
    sql_noise = dict(sql_rows(
        db, "SELECT COALESCE(json_extract(payload_json,'$.noise_reason'),"
            "'unknown'), COUNT(*) FROM ugc_events"
            " WHERE json_extract(payload_json,'$.noise') = 1"
            " GROUP BY 1 ORDER BY 1"))
    sql_susp = int(sql_rows(
        db, "SELECT COUNT(*) FROM review_queue"
        " WHERE verdict IS NULL")[0][0])
    sql_verd = dict(sql_rows(
        db, "SELECT verdict, COUNT(*) FROM review_queue"
        " WHERE verdict IS NOT NULL GROUP BY verdict"))
    world_ok = (w["emoji"]["noise"] and w["short"]["noise"]
                and w["flood"]["noise"]
                and w["flood"]["noise_reason"] == "flooding"
                and w["emoji"]["noise_reason"] == "emoji_only"
                and w["short"]["noise_reason"] == "too_short"
                and w["gray1"]["suspended"] and w["risky"]["rejected"]
                and w["repool"]["pooled"] and w["clean1"]["pooled"])
    cross = (noise["total"] == sum(sql_noise.values())
             and noise["by_reason"] == sql_noise
             and review["suspended"] == sql_susp
             and review["verdicted"].get("pass") == sql_verd.get("pass", 0)
             and review["verdicted"].get("risky") == sql_verd.get("risky", 0)
             and noise["total"] == 3
             and noise["by_reason"] == {"emoji_only": 1, "flooding": 1,
                                         "too_short": 1}
             and review["suspended"] == 1
             and review["verdicted"] == {"pass": 1, "risky": 1}
             and env2["total"] == 4)
    ok2 = world_ok and cross
    record("AC-NP2", ok2,
           "world-ok=%s noise-sql-cross=%s review-sql-cross=%s total=%d"
           % (world_ok, noise["by_reason"] == sql_noise,
              review["suspended"] == sql_susp
              and review["verdicted"]["pass"] == sql_verd.get("pass", 0),
              env2["total"]))

    # ---- AC-NP3: scope isolation between the two pools -------------------
    events_n = table_counts(db)["ugc_events"]
    items_n = table_counts(db)["ugc_items"]
    gray_noise_sql = int(sql_rows(
        db, "SELECT COUNT(*) FROM ugc_events"
        " WHERE json_extract(payload_json,'$.noise') = 1"
        " AND json_extract(payload_json,'$.gate') = 'review'")[0][0])
    isolated = (events_n == 10 and items_n == 5
                and noise["total"] == 3
                and gray_noise_sql == 0
                and review["suspended"] == 1
                and review["verdicted"]["pass"] + review["verdicted"]["risky"] == 2
                and env2["total"] == noise["total"] + review["suspended"])
    ok3 = isolated
    record("AC-NP3", ok3,
           "events=%d items=%d noise=%d gray-in-noise=%d"
           " suspended=%d verdicted=2 total-invariant=%s"
           % (events_n, items_n, noise["total"], gray_noise_sql,
              review["suspended"],
              env2["total"] == noise["total"] + review["suspended"]))

    # ---- AC-NP4: pure-read law ------------------------------------------
    src = inspect.getsource(UGC.UGCStore.pool_water_levels)
    dml = re.findall(r"\b(INSERT|UPDATE|DELETE)\b", src)
    before = table_counts(db)
    first = store.pool_water_levels()
    second = store.pool_water_levels()
    after = table_counts(db)
    same = (json.dumps(first, sort_keys=True)
            == json.dumps(second, sort_keys=True))
    ok4 = (not dml) and before == after and same
    record("AC-NP4", ok4,
           "dml-hits=%d five-tables-stable=%s double-call-identical=%s"
           % (len(dml), before == after, same))

    # ---- AC-NP5: live derivation, zero caching ---------------------------
    env_a = store.pool_water_levels()
    pipe.submit("avatar_intake", "C-np9", EMOJI)          # +1 noise
    env_b = store.pool_water_levels()
    late_gray = pipe.submit("avatar_intake", "C-np10",
                            "late gray park " + cfg["gate"]["gray_words"][0])
    env_c = store.pool_water_levels()
    pipe.review_verdict(late_gray["evt_id"], "pass")
    env_d = store.pool_water_levels()
    nb = env_b["pool_water_levels"]["noise"]
    nc = env_c["pool_water_levels"]["review"]
    nd = env_d["pool_water_levels"]["review"]
    steps = (
        nb["total"] == env_a["pool_water_levels"]["noise"]["total"] + 1
        and nb["by_reason"]["emoji_only"] == 2
        and nc["suspended"] == env_b["pool_water_levels"]["review"]["suspended"] + 1
        and nd["suspended"] == nc["suspended"] - 1
        and nd["verdicted"]["pass"] == nc["verdicted"]["pass"] + 1
        and env_c["total"] == env_b["total"] + 1
        and env_d["total"] == env_c["total"] - 1)
    record("AC-NP5", steps,
           "noise %s->%s suspended %s->%s->%s verdict-pass %s->%s"
           % (env_a["pool_water_levels"]["noise"]["total"], nb["total"],
              env_b["pool_water_levels"]["review"]["suspended"],
              nc["suspended"], nd["suspended"],
              nc["verdicted"]["pass"], nd["verdicted"]["pass"]))
    pipe.close()
    store.close()

    # ---- AC-NP6: hygiene --------------------------------------------------
    subjects = [os.path.join(BASE, "store.py"), os.path.abspath(__file__)]
    ascii_ok = True
    net_hits = []
    for path in subjects:
        with open(path, "rb") as fh:
            data = fh.read()
        if any(b > 127 for b in data):
            ascii_ok = False
        text = data.decode("ascii", "replace")
        for line in text.splitlines():
            stripped = line.strip()
            if (stripped.startswith("import ")
                    or stripped.startswith("from ")) and (
                    re.search(r"\b(urllib|requests|socket|http)\b",
                              stripped)):
                net_hits.append(stripped)
    additive = all(hasattr(UGC.UGCStore, m) for m in (
        "pool_water_levels", "insert_event", "insert_item", "mark_ingest",
        "review_open", "review_set_verdict", "gate_receipts_count",
        "read", "read_one", "write", "write_tx", "close"))
    pipe_face_free = not hasattr(P.UGCPipeline, "pool_water_levels")
    with open(os.path.join(BASE, "pipeline.py"), encoding="utf-8") as fh:
        pipe_text = fh.read()
    pipe_untouched = "pool_water_levels" not in pipe_text
    ok6 = (ascii_ok and not net_hits and additive and pipe_face_free
           and pipe_untouched)
    record("AC-NP6", ok6,
           "ascii=%s subjects=%d network-imports=%d additive=%s"
           " pipeline-zero-touch=%s"
           % (ascii_ok, len(subjects), len(net_hits), additive,
              pipe_untouched and pipe_face_free))

    # ---- AC-NP7: delivery wiring -----------------------------------------
    all_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(all_path, encoding="utf-8") as fh:
        all_text = fh.read()
    wired = ('"ugc-pool-water"' in all_text
             and "test_pool_water.py" in all_text)
    prior = len(RESULTS)                      # six criteria before this one
    ok7 = wired and prior == EXPECTED - 1
    record("AC-NP7", ok7,
           "suites-registry-line=%s prior-criteria=%d expected=%d"
           % (wired, prior, EXPECTED))

    import shutil
    if os.path.isdir(export_test_dir):
        shutil.rmtree(export_test_dir, ignore_errors=True)
    shutil.rmtree(tmp, ignore_errors=True)
    if len(RESULTS) != EXPECTED:
        print("SUITE FAIL: criteria drift %d != %d"
              % (len(RESULTS), EXPECTED))
        return 2
    failed = [ac for ac, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL: %s" % ",".join(failed))
        return 2
    print("SUITE PASS: %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
