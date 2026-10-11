"""Acceptance suite: submit single-text water-delta wiring (R1798).

Asserts the pre-registered criteria AC-SU1..AC-SU7 from the R1798 claim
line in state/queue/tech.md (seed: R1797 drain_recover water wiring -
single-text face symmetry gap; four-window co-residency single slot
pre-registered as AC-SU4). Chinese probe strings come from config.json
(data file) per the encoding discipline; the only non-ASCII literals
are unicode escapes for the emoji sample.

Usage: python test_submit_waterwire.py
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
from sec_gate import GateOfflineError  # noqa: E402 (offline stub family)

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


class OfflineGate(object):
    """Deterministic runtime-failure stub: every check raises the
    gate-offline family (AC-BW5/AC-DR family precedent). Queueing
    rides this stub: the ungated text lands in the persistent queue,
    never passed, never lost."""

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


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def flatten_delta(prev_env, cur_env):
    """Independent manual re-derivation of the pool-water delta map
    from two live level envelopes (AC-SU2 dual-path cross-check,
    AC-IW2/AC-BW2/AC-DR2 law)."""
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
    tmp = tempfile.mkdtemp(prefix="ugc-su-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    frozen = {rel: sha256_file(os.path.join(BASE, rel))
              for rel in ("config.json", "store.py", "sec_batch.py")}
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
    env_emoji = {"pool_water_delta": {"noise.total": 1,
                                      "noise.by_reason.emoji_only": 1},
                 "total_delta": 1, "disclaimer": disc, "persistent": True}

    def idea(actor, text):
        ls.append(lobby.utc_now_iso(), "idea.submit", actor, "cocreate",
                  text, payload={"text": text, "pool": "proposal-queue-stub"})

    pipe = P.UGCPipeline(cfg, db)
    try:
        # ---- AC-SU1: honest states + clean-window receipt shape -------
        none_before = pipe.last_water_delta() is None
        rec = pipe.submit("avatar_intake", "A-su1", "clean single probe")
        rec_keys = {"received", "evt_id", "gate", "suspended", "pooled",
                    "noise", "line", "duplicate_of"}
        receipt_ok = (isinstance(rec, dict) and set(rec) == rec_keys
                      and rec["received"] is True and rec["gate"] == "pass"
                      and rec["suspended"] is False and rec["pooled"] is True
                      and rec["noise"] is False)
        env = pipe.last_water_delta()
        keys_ok = (isinstance(env, dict)
                   and set(env) == {"pool_water_delta", "total_delta",
                                     "disclaimer", "persistent"})
        empty_ok = (env["pool_water_delta"] == {} and env["total_delta"] == 0)
        disc_ok = (env["disclaimer"] == disc and env["persistent"] is True)
        record("AC-SU1",
               none_before and receipt_ok and keys_ok and empty_ok and disc_ok,
               "pre-window None=%s receipt-keys=%d envelope-keys=%s "
               "clean-zero=%s disclaimer=%s"
               % (none_before, len(rec) if isinstance(rec, dict) else -1,
                  sorted(env) if isinstance(env, dict) else None,
                  empty_ok, disc_ok))

        # ---- AC-SU2: dual-path cross-validation (two windows) ---------
        prev2 = pipe.store.pool_water_levels()
        rec_e = pipe.submit("avatar_intake", "A-su2e", emoji_text)
        cur2 = pipe.store.pool_water_levels()
        manual_e, manual_total_e = flatten_delta(prev2, cur2)
        env_e = pipe.last_water_delta()
        emoji_ok = (env_e["pool_water_delta"] == manual_e
                    and env_e["total_delta"] == manual_total_e
                    and env_e == env_emoji
                    and rec_e["noise"] is True
                    and rec_e["noise_reason"] == "emoji_only")
        prev2b = pipe.store.pool_water_levels()
        rec_g = pipe.submit("avatar_intake", "A-su2g", "gray probe " + gw)
        cur2b = pipe.store.pool_water_levels()
        manual_g, manual_total_g = flatten_delta(prev2b, cur2b)
        env_g = pipe.last_water_delta()
        gray_ok = (env_g["pool_water_delta"] == manual_g
                   and env_g["total_delta"] == manual_total_g
                   and env_g == env_susp
                   and rec_g["suspended"] is True)
        det_ok = (json.dumps(pipe.last_water_delta(), sort_keys=True)
                  == json.dumps(env_g, sort_keys=True))
        record("AC-SU2", emoji_ok and gray_ok and det_ok,
               "emoji-window cells=%s total=%s manual=%s/%s "
               "gray-window cells=%s total=%s manual=%s/%s "
               "double-call-identical=%s"
               % (json.dumps(env_e["pool_water_delta"], sort_keys=True),
                  env_e["total_delta"],
                  json.dumps(manual_e, sort_keys=True), manual_total_e,
                  json.dumps(env_g["pool_water_delta"], sort_keys=True),
                  env_g["total_delta"],
                  json.dumps(manual_g, sort_keys=True), manual_total_g,
                  det_ok))

        # ---- AC-SU3: water-receipt alignment over four states ---------
        pipe.submit("avatar_intake", "A-su3g", "gray probe two " + gw)
        susp_env = pipe.last_water_delta()
        pipe.submit("avatar_intake", "A-su3e", emoji_text)
        emoji_env = pipe.last_water_delta()
        pipe.submit("avatar_intake", "A-su3c", "clean alignment probe")
        clean_env = pipe.last_water_delta()
        law_ok = True
        for e in (susp_env, emoji_env, clean_env):
            cells = e["pool_water_delta"]
            law_ok = law_ok and (e["total_delta"]
                                 == cells.get("noise.total", 0)
                                 + cells.get("review.suspended", 0))
        try:
            pipe.submit("avatar_intake", "A-su3f", "forbidden probe " + fw)
            raised = "none"
        except UGC.PipelineError as exc:
            raised = exc.code
        reject_ok = (raised == UGC.E_CONTENT_REJECTED
                     and pipe.last_water_delta() == clean_env)
        record("AC-SU3",
               susp_env == env_susp and emoji_env == env_emoji
               and clean_env == env_zero and law_ok and reject_ok,
               "gray=susp:%s emoji=%s clean=zero:%s "
               "pool-total-law=%s reject-code=%s slot-kept=%s"
               % (susp_env == env_susp,
                  json.dumps(emoji_env["pool_water_delta"], sort_keys=True),
                  clean_env == env_zero, law_ok, raised,
                  pipe.last_water_delta() == clean_env))

        # ---- AC-SU4: four-window co-residency (last writer wins) ------
        pipe.submit("avatar_intake", "A-su4a", "gray probe three " + gw)
        s1_ok = pipe.last_water_delta() == env_susp
        idea("C-50002", "gray probe four " + gw)
        pipe.ingest_lobby()
        s2_ok = pipe.last_water_delta() == env_susp
        pipe.submit_batch("avatar_intake", "A-su4b",
                          ["clean co-resident probe"])
        s3_ok = pipe.last_water_delta() == env_zero
        pipe.drain_recover()
        s4_ok = pipe.last_water_delta() == env_zero
        pipe.submit("avatar_intake", "A-su4c", "gray probe five " + gw)
        s5_ok = pipe.last_water_delta() == env_susp
        # reverse order: submit -> drain -> batch -> ingest -> submit
        pipe.drain_recover()
        r1_ok = pipe.last_water_delta() == env_zero
        pipe.submit_batch("avatar_intake", "A-su4d",
                          ["clean co-resident probe two"])
        r2_ok = pipe.last_water_delta() == env_zero
        idea("C-50003", "gray probe six " + gw)
        pipe.ingest_lobby()
        r3_ok = pipe.last_water_delta() == env_susp
        pipe.submit("avatar_intake", "A-su4e", "gray probe seven " + gw)
        r4_ok = pipe.last_water_delta() == env_susp
        record("AC-SU4",
               s1_ok and s2_ok and s3_ok and s4_ok and s5_ok
               and r1_ok and r2_ok and r3_ok and r4_ok,
               "fwd submit:%s ingest:%s batch:%s drain:%s submit:%s | "
               "rev drain:%s batch:%s ingest:%s submit:%s"
               % (s1_ok, s2_ok, s3_ok, s4_ok, s5_ok,
                  r1_ok, r2_ok, r3_ok, r4_ok))

        # ---- AC-SU5: refused paths keep the slot; degraded overwrites -
        pipe.grant_entrance_sandbox("A-su5r")
        for i in range(5):  # fill the direct rate window (5 per 10s)
            pipe.submit("direct", "A-su5r", "rate probe %d" % (i + 1))
        pipe.submit("avatar_intake", "A-su5v", "gray probe eight " + gw)
        v_ok = pipe.last_water_delta() == env_susp  # V established
        reject_codes = []

        def try_reject(fn):
            try:
                fn()
                reject_codes.append("none")
            except UGC.PipelineError as exc:
                reject_codes.append(exc.code)

        try_reject(lambda: pipe.submit("bogus_source", "A-su5x", "bad source"))
        try_reject(lambda: pipe.submit("direct", "A-noent", "no entrance probe"))
        try_reject(lambda: pipe.submit("direct", "A-su5r", "rate probe six"))
        try_reject(lambda: pipe.submit("avatar_intake", "A-su5b", "   "))
        try_reject(lambda: pipe.submit("avatar_intake", "A-su5f",
                                       "forbidden probe two " + fw))
        kept_ok = pipe.last_water_delta() == env_susp
        codes_ok = (reject_codes == [UGC.E_BAD_SOURCE, UGC.E_ENTRANCE_REQUIRED,
                                     UGC.E_RATE_LIMIT, UGC.E_BAD_FRAME,
                                     UGC.E_CONTENT_REJECTED])
        real_gate = pipe.batch.gate
        pipe.batch.gate = OfflineGate()
        try:
            rec_q = pipe.submit("avatar_intake", "A-su5q",
                                "clean degraded probe")
        finally:
            pipe.batch.gate = real_gate
        degraded_ok = (isinstance(rec_q, dict) and rec_q.get("received") is False
                      and rec_q.get("queued") is True and "qid" in rec_q)
        over_ok = pipe.last_water_delta() == env_zero
        record("AC-SU5",
               v_ok and kept_ok and codes_ok and degraded_ok and over_ok,
               "V=%s codes=%s slot-kept-after-rejects=%s "
               "degraded-receipt=%s degraded-overwrite-zero=%s"
               % (v_ok, ",".join(reject_codes), kept_ok,
                  degraded_ok, over_ok))

        # ---- AC-SU6: pure-read law + five-table count ledger ----------
        static_a = five_table_counts(db)
        lv1 = pipe.store.pool_water_levels()
        lv2 = pipe.store.pool_water_levels()
        delta_env = pipe.store.pool_water_delta(lv1)
        static_b = five_table_counts(db)
        pure_ok = (static_a == static_b and lv1 == lv2
                   and json.dumps(delta_env, sort_keys=True)
                   == json.dumps(pipe.store.pool_water_delta(lv2),
                                 sort_keys=True)
                   and json.dumps(pipe.last_water_delta(), sort_keys=True)
                   == json.dumps(pipe.last_water_delta(), sort_keys=True))
        counts_a = five_table_counts(db)
        pipe.submit("avatar_intake", "A-su6g", "gray probe nine " + gw)
        pipe.submit("avatar_intake", "A-su6e", emoji_text)
        pipe.submit("avatar_intake", "A-su6c", "clean ledger probe")
        counts_b = five_table_counts(db)
        want_diff = {"ugc_events": 3, "ugc_items": 1, "review_queue": 1,
                     "ugc_ingest_log": 0, "gate_receipts": 0}
        ledger_ok = all(counts_b[t] - counts_a[t] == want_diff[t]
                        for t in FIVE_TABLES)
        record("AC-SU6", pure_ok and ledger_ok,
               "static-pure-read=%s ledger=%s"
               % (pure_ok, json.dumps({t: counts_b[t] - counts_a[t]
                                       for t in FIVE_TABLES}, sort_keys=True)))

        # ---- AC-SU7: hygiene + registry source check -------------------
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
        reg_ok = ('"ugc-submit-water"' in reg_src
                  and "test_submit_waterwire.py" in reg_src)
        record("AC-SU7",
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
