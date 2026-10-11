"""Acceptance suite: review_verdict verdict water-delta wiring (R1799).

Asserts the pre-registered criteria AC-VW1..AC-VW7 from the R1799 claim
line in state/queue/tech.md (seed: R1798 submit water wiring - verdict
face symmetry gap; five-window co-residency single slot pre-registered
as AC-VW4; risky-completed-window ruling = design clause 2). Chinese
probe words come from config.json (data file) per the encoding
discipline; this source is pure ASCII.

Usage: python test_verdict_waterwire.py
"""

import hashlib
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


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def flatten_delta(prev_env, cur_env):
    """Independent manual re-derivation of the pool-water delta map
    from two live level envelopes (AC-VW2 dual-path cross-check,
    AC-IW2/AC-BW2/AC-DR2/AC-SU2 law)."""
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
    tmp = tempfile.mkdtemp(prefix="ugc-vw-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    frozen = {rel: sha256_file(os.path.join(BASE, rel))
              for rel in ("config.json", "store.py", "sec_batch.py")}
    db = os.path.join(tmp, "ugc.db")
    lobby = load_lobby_store()
    ls = lobby.EventStore(db)
    gw = cfg["gate"]["gray_words"][0]
    disc = cfg["compliance"]["disclaimer"]
    env_zero = {"pool_water_delta": {}, "total_delta": 0,
                "disclaimer": disc, "persistent": True}
    env_susp = {"pool_water_delta": {"review.suspended": 1}, "total_delta": 1,
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
        # ---- AC-VW1: honest states + pass receipt shape --------------
        none_before = pipe.last_water_delta() is None
        rec_a = pipe.submit("avatar_intake", "A-vw1", "gray probe one " + gw)
        evt_a = rec_a["evt_id"]
        setup_ok = (pipe.last_water_delta() == env_susp
                    and rec_a["suspended"] is True)
        rec = pipe.review_verdict(evt_a, "pass")
        receipt_keys = {"received", "evt_id", "gate", "suspended", "pooled",
                        "noise", "line", "duplicate_of"}
        receipt_ok = (isinstance(rec, dict) and set(rec) == receipt_keys
                      and rec["received"] is True and rec["pooled"] is True
                      and rec["suspended"] is False and rec["noise"] is False)
        env = pipe.last_water_delta()
        keys_ok = (isinstance(env, dict)
                   and set(env) == {"pool_water_delta", "total_delta",
                                    "disclaimer", "persistent"})
        cells_ok = (env["pool_water_delta"]
                    == {"review.suspended": -1, "review.verdicted.pass": 1}
                    and env["total_delta"] == -1)
        disc_ok = (env["disclaimer"] == disc and env["persistent"] is True)
        record("AC-VW1",
               none_before and setup_ok and receipt_ok and keys_ok
               and cells_ok and disc_ok,
               "pre-any-window None=%s case-setup=susp:%s receipt-keys=%d "
               "envelope-keys=%s cells=%s total=%s disclaimer=%s"
               % (none_before, setup_ok, len(rec) if isinstance(rec, dict) else -1,
                  sorted(env) if isinstance(env, dict) else None,
                  json.dumps(env["pool_water_delta"], sort_keys=True)
                  if isinstance(env, dict) else None,
                  env.get("total_delta") if isinstance(env, dict) else None,
                  disc_ok))

        # ---- AC-VW2: dual-path cross-validation (pass + risky) -------
        rec_b = pipe.submit("avatar_intake", "A-vw2p", "gray probe two " + gw)
        prev2 = pipe.store.pool_water_levels()
        pipe.review_verdict(rec_b["evt_id"], "pass")
        cur2 = pipe.store.pool_water_levels()
        manual_p, manual_total_p = flatten_delta(prev2, cur2)
        env_p = pipe.last_water_delta()
        pass_ok = (env_p["pool_water_delta"] == manual_p
                   and env_p["total_delta"] == manual_total_p
                   and env_p == env_pass)
        rec_c = pipe.submit("avatar_intake", "A-vw2r", "gray probe three " + gw)
        prev2r = pipe.store.pool_water_levels()
        raised_r = "none"
        try:
            pipe.review_verdict(rec_c["evt_id"], "risky")
        except UGC.PipelineError as exc:
            raised_r = exc.code
        cur2r = pipe.store.pool_water_levels()
        manual_r, manual_total_r = flatten_delta(prev2r, cur2r)
        env_r = pipe.last_water_delta()
        risky_ok = (raised_r == UGC.E_CONTENT_REJECTED
                    and env_r["pool_water_delta"] == manual_r
                    and env_r["total_delta"] == manual_total_r
                    and env_r == env_risky)
        det_ok = (json.dumps(pipe.last_water_delta(), sort_keys=True)
                  == json.dumps(env_r, sort_keys=True))
        record("AC-VW2", pass_ok and risky_ok and det_ok,
               "pass-window cells=%s manual=%s/%s | risky-window "
               "raised=%s cells=%s manual=%s/%s double-call-identical=%s"
               % (json.dumps(env_p["pool_water_delta"], sort_keys=True),
                  json.dumps(manual_p, sort_keys=True), manual_total_p,
                  raised_r,
                  json.dumps(env_r["pool_water_delta"], sort_keys=True),
                  json.dumps(manual_r, sort_keys=True), manual_total_r,
                  det_ok))

        # ---- AC-VW3: water-receipt alignment (pass/noise/risky) ------
        rec_d = pipe.submit("avatar_intake", "A-vw3p", "gray probe four " + gw)
        pipe.review_verdict(rec_d["evt_id"], "pass")
        env_p2 = pipe.last_water_delta()
        law_p = env_p2 == env_pass
        for i in range(5):  # flood the actor window (5 per 60s)
            pipe.submit("avatar_intake", "A-vw3f", "flood probe %d" % (i + 1))
        rec_f = pipe.submit("avatar_intake", "A-vw3f", "gray probe five " + gw)
        rec_n = pipe.review_verdict(rec_f["evt_id"], "pass")
        noise_rec_ok = (isinstance(rec_n, dict)
                        and rec_n.get("noise") is True
                        and rec_n.get("noise_reason") == "flooding"
                        and rec_n.get("pooled") is False)
        noise_env = pipe.last_water_delta()
        noise_cells_ok = noise_env == env_pass  # zero noise cells, honest edge
        item_missing = pipe.store.item_row(rec_f["evt_id"]) is None
        rec_g = pipe.submit("avatar_intake", "A-vw3r", "gray probe six " + gw)
        raised_n = "none"
        try:
            pipe.review_verdict(rec_g["evt_id"], "risky")
        except UGC.PipelineError as exc:
            raised_n = exc.code
        trace_ok = pipe.desk.row(rec_g["evt_id"])["verdict"] == "risky"
        risky_env_ok = pipe.last_water_delta() == env_risky
        record("AC-VW3",
               law_p and noise_rec_ok and noise_cells_ok and item_missing
               and raised_n == UGC.E_CONTENT_REJECTED and trace_ok
               and risky_env_ok,
               "pass-clean=%s noise-receipt=%s noise-cells-zero=%s "
               "noise-no-item=%s risky-raised=%s trace-kept=%s "
               "risky-cells=%s"
               % (law_p, noise_rec_ok, noise_cells_ok, item_missing,
                  raised_n, trace_ok,
                  json.dumps(pipe.last_water_delta()["pool_water_delta"],
                             sort_keys=True)))

        # ---- AC-VW4: five-window co-residency (last writer wins) -----
        rec_h = pipe.submit("avatar_intake", "A-vw4a", "gray probe seven " + gw)
        s1_ok = pipe.last_water_delta() == env_susp
        idea("C-60001", "gray probe eight " + gw)
        pipe.ingest_lobby()
        s2_ok = pipe.last_water_delta() == env_susp
        pipe.submit_batch("avatar_intake", "A-vw4b",
                          ["clean co-resident probe"])
        s3_ok = pipe.last_water_delta() == env_zero
        pipe.drain_recover()
        s4_ok = pipe.last_water_delta() == env_zero
        pipe.review_verdict(rec_h["evt_id"], "pass")
        s5_ok = pipe.last_water_delta() == env_pass
        # reverse order: verdict -> drain -> batch -> ingest -> submit
        rec_i = pipe.submit("avatar_intake", "A-vw4c",
                            "gray probe nine " + gw)
        pipe.review_verdict(rec_i["evt_id"], "pass")
        r1_ok = pipe.last_water_delta() == env_pass
        pipe.drain_recover()
        r2_ok = pipe.last_water_delta() == env_zero
        pipe.submit_batch("avatar_intake", "A-vw4d",
                          ["clean co-resident probe two"])
        r3_ok = pipe.last_water_delta() == env_zero
        idea("C-60002", "clean idea co-resident probe")
        pipe.ingest_lobby()
        r4_ok = pipe.last_water_delta() == env_zero
        pipe.submit("avatar_intake", "A-vw4e", "gray probe ten " + gw)
        r5_ok = pipe.last_water_delta() == env_susp
        record("AC-VW4",
               s1_ok and s2_ok and s3_ok and s4_ok and s5_ok
               and r1_ok and r2_ok and r3_ok and r4_ok and r5_ok,
               "fwd submit:%s ingest:%s batch:%s drain:%s verdict:%s | "
               "rev verdict:%s drain:%s batch:%s ingest:%s submit:%s"
               % (s1_ok, s2_ok, s3_ok, s4_ok, s5_ok,
                  r1_ok, r2_ok, r3_ok, r4_ok, r5_ok))

        # ---- AC-VW5: refused paths keep slot + post-mutation guard ----
        rec_j = pipe.submit("avatar_intake", "A-vw5a", "gray probe eleven " + gw)
        v_ok = pipe.last_water_delta() == env_susp  # V established
        reject_codes = []

        def try_reject(fn):
            try:
                fn()
                reject_codes.append("none")
            except UGC.PipelineError as exc:
                reject_codes.append(exc.code)

        try_reject(lambda: pipe.review_verdict(rec_j["evt_id"], "maybe"))
        try_reject(lambda: pipe.review_verdict("no-such-evt", "pass"))
        try_reject(lambda: pipe.review_verdict(evt_a, "pass"))
        kept_ok = pipe.last_water_delta() == env_susp
        codes_ok = (reject_codes == [UGC.E_BAD_VERDICT, UGC.E_NOT_FOUND,
                                     UGC.E_REVIEW_DONE])
        rec_k = pipe.submit("avatar_intake", "A-vw5b", "gray probe twelve " + gw)
        conn = sqlite3.connect(db)  # fixture injection (R1730 precedent)
        conn.execute("DELETE FROM ugc_events WHERE evt_id = ?",
                     (rec_k["evt_id"],))
        conn.commit()
        conn.close()
        raised_g = "none"
        try:
            pipe.review_verdict(rec_k["evt_id"], "pass")
        except UGC.PipelineError as exc:
            raised_g = exc.code
        guard_ok = (raised_g == UGC.E_NOT_FOUND
                   and pipe.last_water_delta() == env_pass)
        record("AC-VW5",
               v_ok and kept_ok and codes_ok and guard_ok,
               "V=%s codes=%s slot-kept-after-rejects=%s "
               "post-mutation-guard raised=%s verdict-water-landed=%s"
               % (v_ok, ",".join(reject_codes), kept_ok, raised_g, guard_ok))

        # ---- AC-VW6: pure-read law + five-table count ledger ----------
        static_a = five_table_counts(db)
        lv1 = pipe.store.pool_water_levels()
        lv2 = pipe.store.pool_water_levels()
        delta_env = pipe.store.pool_water_delta(lv1)
        last1 = pipe.last_water_delta()
        last2 = pipe.last_water_delta()
        static_b = five_table_counts(db)
        pure_ok = (static_a == static_b and lv1 == lv2
                   and json.dumps(delta_env, sort_keys=True)
                   == json.dumps(pipe.store.pool_water_delta(lv2),
                                 sort_keys=True)
                   and json.dumps(last1, sort_keys=True)
                   == json.dumps(last2, sort_keys=True))
        counts_a = five_table_counts(db)
        rec_x = pipe.submit("avatar_intake", "A-vw6x", "gray probe thirteen " + gw)
        rec_y = pipe.submit("avatar_intake", "A-vw6y", "gray probe fourteen " + gw)
        pipe.review_verdict(rec_x["evt_id"], "pass")
        try:
            pipe.review_verdict(rec_y["evt_id"], "risky")
        except UGC.PipelineError:
            pass
        counts_b = five_table_counts(db)
        want_diff = {"ugc_events": 2, "ugc_items": 1, "review_queue": 2,
                     "ugc_ingest_log": 0, "gate_receipts": 0}
        ledger_ok = all(counts_b[t] - counts_a[t] == want_diff[t]
                        for t in FIVE_TABLES)
        record("AC-VW6", pure_ok and ledger_ok,
               "static-pure-read=%s ledger=%s"
               % (pure_ok, json.dumps({t: counts_b[t] - counts_a[t]
                                       for t in FIVE_TABLES}, sort_keys=True)))

        # ---- AC-VW7: hygiene + registry source check ------------------
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
        frozen_ok = all(sha256_file(os.path.join(BASE, rel)) == sha
                        for rel, sha in frozen.items())
        reg_path = os.path.normpath(os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ('"ugc-verdict-water"' in reg_src
                  and "test_verdict_waterwire.py" in reg_src)
        record("AC-VW7",
               ascii_ok and net_ok and frozen_ok and reg_ok,
               "pure-ascii=%s import-lines-clean=%s frozen-bytes=%s "
               "registry-wired=%s"
               % (ascii_ok, net_ok, frozen_ok, reg_ok))
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
