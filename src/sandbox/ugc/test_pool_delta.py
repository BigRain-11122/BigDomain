"""Acceptance suite for the UGC pool water two-snapshot delta probe
(tech.md claim line R1785).

Asserts the pre-registered criteria AC-DW1..AC-DW7 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Subject: UGCStore.pool_water_delta(snapshot) - pure-read net-change
face over two water snapshots: the previous snapshot is caller-held
(zero storage: this module never persists a snapshot); the current
side derives from a single live pool_water_levels() call (single
derivation source, zero second aggregation engine - the R1770
board-movement precedent). Change-only semantics: steady cells are
omitted, a fully-steady world returns an honest empty map; prev-only
reason keys zeroed inside the window show as negative cells (union
of both sides).

Usage: python test_pool_delta.py
"""

import copy
import hashlib
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
import store as UGC                        # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7
TEST_DISCLAIMER = ("sandbox non-advisory standing disclaimer "
                   "(pool-delta probe)")
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


def face_for(db):
    """Store read instance wired with the standing disclaimer."""
    return UGC.UGCStore(db, disclaimer=TEST_DISCLAIMER)


def build_world(cfg, db):
    """Real-flow world through the pipeline (test_pool_water twin):
    all three noise reasons, gray suspended + both verdicts, clean
    pooled control rows."""
    wcfg = json.loads(json.dumps(cfg))
    wcfg["noise"] = dict(wcfg.get("noise") or {}, flood_max_submissions=2)
    wcfg["export"] = dict(wcfg.get("export") or {}, dir="export-dw-test")
    pipe = P.UGCPipeline(wcfg, db)
    gw = wcfg["gate"]["gray_words"][0]
    kw = wcfg["routing"]["rules"][0]["keywords"][0]

    out = {}
    out["emoji"] = pipe.submit("avatar_intake", "C-dw1", EMOJI)
    out["short"] = pipe.submit("avatar_intake", "C-dw2", "ab")
    out["f1"] = pipe.submit("avatar_intake", "C-dw3", "flood probe one")
    out["f2"] = pipe.submit("avatar_intake", "C-dw3", "flood probe two")
    out["flood"] = pipe.submit("avatar_intake", "C-dw3", "flood probe three")
    out["gray1"] = pipe.submit("avatar_intake", "C-dw4", "gray park " + gw)
    out["gray2"] = pipe.submit("avatar_intake", "C-dw5",
                               "gray risky " + gw + " park")
    try:
        pipe.review_verdict(out["gray2"]["evt_id"], "risky")
        out["risky"] = {"rejected": False}
    except UGC.PipelineError as exc:
        out["risky"] = {"rejected": exc.code == UGC.E_CONTENT_REJECTED}
    out["gray3"] = pipe.submit("avatar_intake", "C-dw6",
                               "gray pass " + gw + " park")
    out["repool"] = pipe.review_verdict(out["gray3"]["evt_id"], "pass")
    out["clean1"] = pipe.submit("avatar_intake", "C-dw7",
                                "clean idea about " + kw)
    out["clean2"] = pipe.submit("avatar_intake", "C-dw8",
                                "clean second idea about " + kw)
    return pipe, out


def hand_delta(prev_env, cur_env):
    """Test-side independent re-derivation of the flat cell delta."""
    cells = {}
    pn = prev_env["pool_water_levels"]["noise"]
    cn = cur_env["pool_water_levels"]["noise"]
    pr = prev_env["pool_water_levels"]["review"]
    cr = cur_env["pool_water_levels"]["review"]
    for key, now, then in (
            ("noise.total", cn["total"], pn["total"]),
            ("review.suspended", cr["suspended"], pr["suspended"])):
        if now - then:
            cells[key] = now - then
    for key in sorted(set(pn["by_reason"]) | set(cn["by_reason"])):
        diff = cn["by_reason"].get(key, 0) - pn["by_reason"].get(key, 0)
        if diff:
            cells["noise.by_reason." + key] = diff
    for key in sorted(set(pr["verdicted"]) | set(cr["verdicted"])):
        diff = cr["verdicted"].get(key, 0) - pr["verdicted"].get(key, 0)
        if diff:
            cells["review.verdicted." + key] = diff
    return {k: cells[k] for k in sorted(cells)}


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-dw-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg_sha = hashlib.sha256(
        open(os.path.join(BASE, "config.json"), "rb").read()
    ).hexdigest()[:16]
    export_test_dir = os.path.join(BASE, "export-dw-test")

    # ---- AC-DW1: contract, steady world, disclaimer gate ---------------
    empty_db = os.path.join(tmp, "empty.db")
    legacy = UGC.UGCStore(empty_db)                 # legacy constructor
    legacy_refused = False
    try:
        legacy.pool_water_delta({})
    except ValueError as exc:
        legacy_refused = "E_STORE_NO_DISCLAIMER" in str(exc)
    legacy.close()
    store = face_for(empty_db)
    snap0 = store.pool_water_levels()
    steady = store.pool_water_delta(snap0)
    env_keys = set(steady) == {"pool_water_delta", "total_delta",
                                "disclaimer", "persistent"}
    steady_ok = (steady["pool_water_delta"] == {}
                 and steady["total_delta"] == 0
                 and steady["disclaimer"] == TEST_DISCLAIMER
                 and steady["persistent"] is True)
    ok1 = env_keys and steady_ok and legacy_refused
    record("AC-DW1", ok1,
           "envelope-keys=%s steady-empty=%s legacy-refused=%s"
           % (env_keys, steady_ok, legacy_refused))
    store.close()

    # ---- AC-DW2: malformed snapshot fail-closed ------------------------
    db = os.path.join(tmp, "world.db")
    pipe, w = build_world(cfg, db)
    store = face_for(db)
    base_snap = store.pool_water_levels()
    V = {"pass": 0, "risky": 0}

    def lv(noise, review):
        return {"pool_water_levels": {"noise": noise, "review": review},
                "total": 0}

    good_noise = {"total": 0, "by_reason": {}}
    probes = [
        ("not-dict-none", None),
        ("not-dict-list", []),
        ("not-dict-str", "levels"),
        ("no-levels-key", {}),
        ("levels-not-dict", {"pool_water_levels": "x"}),
        ("noise-not-dict", lv("x", {"suspended": 0, "verdicted": V})),
        ("review-not-dict", lv(good_noise, "x")),
        ("by-reason-not-dict",
         lv({"total": 0, "by_reason": "x"},
            {"suspended": 0, "verdicted": V})),
        ("reason-key-not-str",
         lv({"total": 0, "by_reason": {1: 1}},
            {"suspended": 0, "verdicted": V})),
        ("reason-key-empty",
         lv({"total": 0, "by_reason": {"": 1}},
            {"suspended": 0, "verdicted": V})),
        ("reason-val-bool",
         lv({"total": 0, "by_reason": {"a": True}},
            {"suspended": 0, "verdicted": V})),
        ("reason-val-neg",
         lv({"total": 0, "by_reason": {"a": -1}},
            {"suspended": 0, "verdicted": V})),
        ("noise-total-missing",
         lv({"by_reason": {}}, {"suspended": 0, "verdicted": V})),
        ("noise-total-bool",
         lv({"total": True, "by_reason": {}},
            {"suspended": 0, "verdicted": V})),
        ("suspended-missing",
         lv(good_noise, {"verdicted": V})),
        ("verdicted-not-dict", lv(good_noise, {"suspended": 0})),
        ("verdicted-missing-pass",
         lv(good_noise, {"suspended": 0, "verdicted": {"risky": 0}})),
        ("verdicted-missing-risky",
         lv(good_noise, {"suspended": 0, "verdicted": {"pass": 0}})),
        ("verdicted-val-float",
         lv(good_noise, {"suspended": 0,
                         "verdicted": {"pass": 1.5, "risky": 0}})),
        ("envelope-total-missing",
         {"pool_water_levels": {"noise": good_noise,
                                "review": {"suspended": 0, "verdicted": V}}}),
        ("envelope-total-bool",
         {"pool_water_levels": {"noise": good_noise,
                                "review": {"suspended": 0, "verdicted": V}},
          "total": True}),
    ]
    before = table_counts(db)
    rejected = []
    for name, probe in probes:
        try:
            store.pool_water_delta(probe)
            rejected.append(name)
        except ValueError as exc:
            if "E_BAD_STATE" not in str(exc):
                rejected.append(name + ":wrong-code")
    after = table_counts(db)
    good_still = store.pool_water_delta(base_snap)["total_delta"] == 0
    ok2 = (not rejected) and before == after and good_still
    record("AC-DW2", ok2,
           "rejected=%d/%d leaked=%s five-tables-stable=%s"
           % (len(probes) - len(rejected), len(probes), rejected,
              before == after))

    # ---- AC-DW3: dual-path cross-validation ----------------------------
    snap_a = store.pool_water_levels()
    pipe.submit("avatar_intake", "C-dw9", EMOJI)          # +1 noise
    pipe.submit("avatar_intake", "C-dw10",
                "clean third idea about "
                + cfg["routing"]["rules"][0]["keywords"][0])
    snap_b = store.pool_water_levels()
    delta_b = store.pool_water_delta(snap_a)
    cross = delta_b["pool_water_delta"] == hand_delta(snap_a, snap_b)
    expected_b = {"noise.by_reason.emoji_only": 1, "noise.total": 1}
    changed_only = delta_b["pool_water_delta"] == expected_b
    steady_cells_absent = all(
        key not in delta_b["pool_water_delta"] for key in (
            "noise.by_reason.flooding", "noise.by_reason.too_short",
            "review.suspended", "review.verdicted.pass",
            "review.verdicted.risky"))
    # prev-only reason key (caller-held cross-world snapshot): ghost
    # reason count zeroed inside the window shows as a negative cell.
    ghost = copy.deepcopy(snap_b)
    ghost["pool_water_levels"]["noise"]["by_reason"]["ghost_reason"] = 2
    ghost["pool_water_levels"]["noise"]["total"] += 2
    ghost["total"] += 2
    delta_g = store.pool_water_delta(ghost)
    ghost_ok = (delta_g["pool_water_delta"]
                == {"noise.by_reason.ghost_reason": -2, "noise.total": -2}
                and delta_g["total_delta"] == -2)
    ok3 = cross and changed_only and steady_cells_absent and ghost_ok
    record("AC-DW3", ok3,
           "cross=%s changed-only=%s steady-omitted=%s ghost-union=%s"
           % (cross, changed_only, steady_cells_absent, ghost_ok))

    # ---- AC-DW4: window net-change on the real flow ---------------------
    prev = store.pool_water_levels()
    pipe.submit("avatar_intake", "C-dw11", EMOJI)         # +1 noise
    gray = pipe.submit("avatar_intake", "C-dw12",
                      "late gray park " + cfg["gate"]["gray_words"][0])
    pipe.review_verdict(gray["evt_id"], "pass")           # -1 suspended +1 pass
    delta_w = store.pool_water_delta(prev)
    cur = store.pool_water_levels()
    net_noise = (cur["pool_water_levels"]["noise"]["total"]
                 - prev["pool_water_levels"]["noise"]["total"])
    net_susp = (cur["pool_water_levels"]["review"]["suspended"]
                - prev["pool_water_levels"]["review"]["suspended"])
    window_ok = (delta_w["pool_water_delta"]
                 == {"noise.by_reason.emoji_only": 1, "noise.total": 1,
                     "review.verdicted.pass": 1}
                 and delta_w["total_delta"] == 1
                 and net_susp == 0
                 and "review.suspended" not in delta_w["pool_water_delta"])
    invariant = delta_w["total_delta"] == net_noise + net_susp
    ok4 = window_ok and invariant
    record("AC-DW4", ok4,
           "window-cells=%s suspended-net-zero-omitted=%s "
           "total-invariant=%s"
           % (window_ok, "review.suspended"
              not in delta_w["pool_water_delta"], invariant))
    pipe.close()
    store.close()

    # ---- AC-DW5: pure-read law ------------------------------------------
    store = face_for(db)
    sources = (inspect.getsource(UGC.UGCStore.pool_water_delta)
               + inspect.getsource(UGC.UGCStore._pw_prev_cells)
               + inspect.getsource(UGC.UGCStore._pw_count))
    dml = re.findall(r"\b(INSERT|UPDATE|DELETE)\b", sources)
    before = table_counts(db)
    snap_c = store.pool_water_levels()
    first = store.pool_water_delta(snap_c)
    second = store.pool_water_delta(snap_c)
    after = table_counts(db)
    same = (json.dumps(first, sort_keys=True)
            == json.dumps(second, sort_keys=True))
    ok5 = (not dml) and before == after and same
    record("AC-DW5", ok5,
           "dml-hits=%d five-tables-stable=%s double-call-identical=%s"
           % (len(dml), before == after, same))
    store.close()

    # ---- AC-DW6: hygiene --------------------------------------------------
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
        "pool_water_levels", "pool_water_delta", "_pw_prev_cells",
        "_pw_count", "insert_event", "insert_item", "mark_ingest",
        "review_open", "review_set_verdict", "gate_receipts_count",
        "read", "read_one", "write", "write_tx", "close"))
    with open(os.path.join(BASE, "pipeline.py"), encoding="utf-8") as fh:
        pipe_text = fh.read()
    # R1794 successor window (authorized by the R1788 seed line): the
    # pipeline now consumes the store delta face via delegation (the
    # window-end live delta in ingest_lobby, AC-IW1). Zero-touch is
    # superseded by the delegation law: no own delta engine on the
    # pipeline class (face-free) and consumption only through
    # self.store (R1732 contract-follow precedent).
    pipe_face_free = not hasattr(P.UGCPipeline, "pool_water_delta")
    pipe_delegates = "self.store.pool_water_delta(" in pipe_text
    cfg_sha_after = hashlib.sha256(
        open(os.path.join(BASE, "config.json"), "rb").read()
    ).hexdigest()[:16]
    ok6 = (ascii_ok and not net_hits and additive and pipe_face_free
           and pipe_delegates and cfg_sha == cfg_sha_after)
    record("AC-DW6", ok6,
           "ascii=%s subjects=%d network-imports=%d additive=%s "
           "pipeline-store-delegation=%s (face-free=%s) config-sha=%s"
           % (ascii_ok, len(subjects), len(net_hits), additive,
              pipe_delegates, pipe_face_free, cfg_sha == cfg_sha_after))

    # ---- AC-DW7: delivery wiring -----------------------------------------
    all_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(all_path, encoding="utf-8") as fh:
        all_text = fh.read()
    wired = ('"ugc-pool-delta"' in all_text
             and "test_pool_delta.py" in all_text)
    prior = len(RESULTS)                      # six criteria before this one
    ok7 = wired and prior == EXPECTED - 1
    record("AC-DW7", ok7,
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
