"""Acceptance suite for the apidev audit_lineage capped-windowed
read restart-persistence example window (BigDomain R1896; canon =
the tech-queue "apidev audit_lineage capped-windowed read restart
persistence example window" row, the R1891 seed, claimed from the
tech-lane FIFO oldest claimable row). Asserts the pre-registered
criteria AC-LG23..AC-LG29 from the R1896 claim note (criteria
were registered in state/queue/tech.md before this code ran;
honesty law). Each criterion prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL.

Covered semantics: the derived purity of the audit_lineage read
faces across an instance restart -- the three-piece stack
(Ledger -> MeteredFace -> DevKeyFace) closes fully and reopens on
the same db path and config; the October capped-windowed lineage
envelope (window echo + overflow block) must replay byte-identical
from the fresh instance (zero in-memory drift in the derived
face); a November revoke on an isolated lone key must recalculate
the default capped read (zero cache) while the October windowed
reads stay byte-frozen (key_events rows are record-time immutable
and the injected key lives outside the October chain's key
domain; the claim note's orthogonal-key-domain ruling); a third
instance replays the post-injection state byte-identically
(two-instance sequential reads).

The metered face is the real product injected by reference (no
copy); this suite never touches the billing ring (the lineage
face moves zero tokens, so the suite needs no funding). This test
source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_lineagepersist.py
"""

import datetime
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

import ledger as L                      # noqa: E402 (P-47-2b core)
import metered as M                     # noqa: E402 (R626 product)
import apidev as D                      # noqa: E402 (R1700+ face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the open API is a compute"
             " + visualization interface, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)
NEW_WIN = "2026-11"

# exact envelope contracts (the R1825/R1887/R1888 pin lists,
# reused verbatim: this suite adds zero keys to any read face)
LINEAGE_KEYS = sorted([
    "api_key", "dev_account", "key_name", "key_id", "chain",
    "chain_size", "queried_index", "disclaimer"])
WINDOWED_KEYS = sorted(LINEAGE_KEYS + ["window"])
CAPPED_KEYS = sorted(LINEAGE_KEYS
                     + ["limit", "total", "returned", "truncated"])
CAPPED_WIN_KEYS = sorted(CAPPED_KEYS + ["window"])


class _FrozenClock(object):
    """Deterministic UTC clock holder: _now_utc/_minute_utc/
    _window_utc are patched onto the apidev module so every
    lifecycle stamp and month window moves only when the suite
    advances the clock."""

    def __init__(self):
        self.dt = BASE_DT

    def now_utc(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def minute_utc(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M")

    def window_utc(self):
        return self.dt.strftime("%Y-%m")

    def advance(self, seconds):
        self.dt = self.dt + datetime.timedelta(seconds=seconds)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def snap(env):
    return json.dumps(env, sort_keys=True)


def _count(conn, table, extra="", args=()):
    return conn.execute(
        "SELECT COUNT(*) FROM " + table + extra,
        tuple(args)).fetchone()[0]


def _open_stack(db_path, cfg):
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    return led, metered, dk


def _close_stack(dk, metered, led):
    dk.close()
    metered.close()
    led.close()


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-lgp-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    lc_path = os.path.join(tmp, "api_lifecycle.db")

    product_path = os.path.join(BASE, "apidev.py")
    with open(product_path, "rb") as handle:
        product_pre = handle.read()
    product_pre_sha = hashlib.sha256(product_pre).hexdigest()

    clock = _FrozenClock()
    real_now = D._now_utc
    real_minute = D._minute_utc
    real_window = D._window_utc

    D._now_utc = clock.now_utc
    D._minute_utc = clock.minute_utc
    D._window_utc = clock.window_utc

    try:
        led, metered, dk = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)

        # -- AC-LG23 October anchor world + pre-close snapshots ----
        ka = dk.issue_key("usr:lgp", "chain-a", 5, ["backtest"], True)
        kb = dk.rotate_key(ka["api_key"], "chain-b")
        kc = dk.rotate_key(kb["api_key"], "chain-c")
        lx = dk.issue_key("usr:lx", "lone-x", 5, ["backtest"], False)

        def key_id_of(api_key):
            return conn.execute(
                "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
                (api_key,)).fetchone()[0]

        id_a = key_id_of(ka["api_key"])
        id_b = key_id_of(kb["api_key"])
        id_c = key_id_of(kc["api_key"])
        oct_events = _count(
            lcconn, "key_events",
            " WHERE substr(event_utc,1,7) = '2026-10'")
        # month-abstraction law (R1813): W derives from a real
        # event's record-time prefix, never hardcoded
        W = dk.audit_lineage(kc["api_key"])["chain"][2]["events"]\
            [-1]["event_utc"][:7]

        s_oct_capped = snap(dk.audit_lineage(kc["api_key"], W, 2))
        s_oct_bare = snap(dk.audit_lineage(kc["api_key"], W, 0))
        s_def_cap = snap(dk.audit_lineage(kc["api_key"], None, 2))
        s_default = snap(dk.audit_lineage(kc["api_key"]))
        s_lx_pre = snap(dk.audit_lineage(lx["api_key"], None, 1))

        lg23_shape = (
            oct_events == 4
            and W == "2026-10"
            and sorted(json.loads(s_oct_capped).keys())
            == CAPPED_WIN_KEYS
            and len(CAPPED_WIN_KEYS) == 13
            and sorted(json.loads(s_oct_bare).keys())
            == WINDOWED_KEYS
            and len(WINDOWED_KEYS) == 9
            and sorted(json.loads(s_def_cap).keys()) == CAPPED_KEYS
            and len(CAPPED_KEYS) == 12
            and sorted(json.loads(s_default).keys())
            == LINEAGE_KEYS
            and len(LINEAGE_KEYS) == 8)
        oc = json.loads(s_oct_capped)
        lg23_block = (
            oc["window"] == W and oc["limit"] == 2
            and oc["total"] == 3 and oc["returned"] == 2
            and oc["truncated"] is True
            and oc["chain_size"] == 2
            and [m["key_id"] for m in oc["chain"]]
            == [id_b, id_c]
            and oc["queried_index"] == 2
            and json.loads(s_default)["chain"][2]["status"]
            == "active")
        lx_pre = json.loads(s_lx_pre)
        lg23_lx = (lx_pre["chain"][0]["status"] == "active"
                   and lx_pre["chain"][0]["events"] == []
                   and lx_pre["truncated"] is False
                   and lx_pre["total"] == 1)
        lg23 = lg23_shape and lg23_block and lg23_lx
        record("AC-LG23", lg23,
               "October anchor: 4 lifecycle events record-time"
               " 2026-10 (SQL count==%d), W=%s from event prefix,"
               " four snapshots anchored (capped-win %d keys"
               " block l/t/r/tr=%s/%s/%s/%s tail [B,C] queried"
               " full-chain=%s; bare-win %d; default-cap %d;"
               " default %d), lone-x pre-close cap read"
               " active/empty=%s"
               % (oct_events, W, len(CAPPED_WIN_KEYS),
                  oc["limit"], oc["total"], oc["returned"],
                  oc["truncated"], oc["queried_index"],
                  len(WINDOWED_KEYS), len(CAPPED_KEYS),
                  len(LINEAGE_KEYS), lg23_lx))

        # -- AC-LG24 restart replay: capped-windowed envelope ------
        conn.close()
        lcconn.close()
        _close_stack(dk, metered, led)
        led2, metered2, dk2 = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)

        replay = snap(dk2.audit_lineage(kc["api_key"], W, 2))
        replay2 = snap(dk2.audit_lineage(kc["api_key"], W, 2))
        lg24 = (replay == s_oct_capped
                and replay2 == s_oct_capped)
        record("AC-LG24", lg24,
               "full stack close -> reopen same db/config: October"
               " capped-windowed envelope byte-identical to the"
               " pre-close snapshot=%s, second same-param read"
               " self-identical=%s"
               % (replay == s_oct_capped,
                  replay2 == s_oct_capped))

        # -- AC-LG25 default / bare-window / default-cap replay -----
        r_default = snap(dk2.audit_lineage(kc["api_key"]))
        r_oct_bare = snap(dk2.audit_lineage(kc["api_key"], W, 0))
        r_def_cap = snap(dk2.audit_lineage(kc["api_key"], None, 2))
        rd = json.loads(r_default)
        lg25 = (r_default == s_default
                and r_oct_bare == s_oct_bare
                and r_def_cap == s_def_cap
                and rd["chain_size"] == 3
                and [m["key_id"] for m in rd["chain"]]
                == [id_a, id_b, id_c]
                and rd["queried_index"] == 2
                and [m["status"] for m in rd["chain"]]
                == ["rotated_out", "rotated_out", "active"])
        record("AC-LG25", lg25,
               "default full-chain read replayed byte-identical=%s"
               " (chain [A,B,C] ids/names/queried_index/status"
               " facts stable), bare-window=%s, default-cap=%s"
               % (r_default == s_default,
                  r_oct_bare == s_oct_bare,
                  r_def_cap == s_def_cap))

        # -- AC-LG26 November revoke -> capped-read recalc face -----
        clock.advance(23 * 86400)
        dk2.revoke_key(lx["api_key"])
        nov_events = _count(
            lcconn, "key_events",
            " WHERE substr(event_utc,1,7) = '2026-11'")
        r_lx = json.loads(
            snap(dk2.audit_lineage(lx["api_key"], None, 1)))
        r_lx_nov = json.loads(
            snap(dk2.audit_lineage(lx["api_key"], NEW_WIN, 1)))
        r_lx_oct = json.loads(
            snap(dk2.audit_lineage(lx["api_key"], W, 1)))
        ev_names = [e["event"] for e in
                    r_lx["chain"][0]["events"]]
        ev_months = [e["event_utc"][:7] for e in
                     r_lx["chain"][0]["events"]]
        lg26 = (nov_events == 1
                and snap(r_lx) != s_lx_pre
                and r_lx["chain"][0]["status"] == "revoked"
                and ev_names == ["revoke"]
                and ev_months == [NEW_WIN]
                and r_lx["limit"] == 1 and r_lx["total"] == 1
                and r_lx["returned"] == 1
                and r_lx["truncated"] is False
                and r_lx_nov["window"] == NEW_WIN
                and [e["event"] for e in
                     r_lx_nov["chain"][0]["events"]] == ["revoke"]
                and r_lx_oct["chain"][0]["events"] == []
                and r_lx_oct["chain"][0]["status"] == "revoked")
        record("AC-LG26", lg26,
               "frozen clock +23d -> November revoke on the lone"
               " key (record-time 2026-11 SQL count==%d): default"
               " capped read recalculated (status revoked +"
               " [revoke@2026-11], byte-differs from the pre-close"
               " snapshot=%s = zero-cache), November windowed cap"
               " read carries the new event=%s, October windowed"
               " events axis stays empty (member status=revoked"
               " is a key-attribute evolution, not window"
               " slicing)=%s"
               % (nov_events, snap(r_lx) != s_lx_pre,
                  [e["event"] for e in
                   r_lx_nov["chain"][0]["events"]] == ["revoke"],
                  r_lx_oct["chain"][0]["events"] == []))

        # -- AC-LG27 old-window zero penetration ---------------------
        p_oct_capped = snap(dk2.audit_lineage(kc["api_key"], W, 2))
        p_oct_bare = snap(dk2.audit_lineage(kc["api_key"], W, 0))
        r_chain_nov = json.loads(
            snap(dk2.audit_lineage(kc["api_key"], NEW_WIN, 2)))
        total_events = _count(lcconn, "key_events")
        lg27 = (p_oct_capped == s_oct_capped
                and p_oct_bare == s_oct_bare
                and all(m["events"] == []
                        for m in r_chain_nov["chain"])
                and total_events == 5)
        record("AC-LG27", lg27,
               "after the November injection: October"
               " capped-windowed chain read still byte-identical"
               " to the pre-close snapshot=%s, bare-window=%s,"
               " chain November window carries zero events (all"
               " four lifecycle rows are October-stamped)=%s,"
               " key_events total %d == 4+1 (immutable rows"
               " never lost)"
               % (p_oct_capped == s_oct_capped,
                  p_oct_bare == s_oct_bare,
                  all(m["events"] == []
                      for m in r_chain_nov["chain"]),
                  total_events))

        # -- AC-LG28 two-instance sequential reads --------------------
        f2_a = snap(dk2.audit_lineage(kc["api_key"], W, 2))
        f2_b = snap(dk2.audit_lineage(kc["api_key"]))
        f2_c = snap(dk2.audit_lineage(lx["api_key"], None, 1))
        f2_d = snap(dk2.audit_lineage(lx["api_key"], NEW_WIN, 1))
        conn.close()
        lcconn.close()
        _close_stack(dk2, metered2, led2)
        led3, metered3, dk3 = _open_stack(db_path, cfg)
        f3_a = snap(dk3.audit_lineage(kc["api_key"], W, 2))
        f3_b = snap(dk3.audit_lineage(kc["api_key"]))
        f3_c = snap(dk3.audit_lineage(lx["api_key"], None, 1))
        f3_d = snap(dk3.audit_lineage(lx["api_key"], NEW_WIN, 1))
        lg28 = (f3_a == f2_a and f3_b == f2_b
                and f3_c == f2_c and f3_d == f2_d
                and f3_a == s_oct_capped)
        record("AC-LG28", lg28,
               "third instance on the same db: all four"
               " post-injection reads byte-identical to the"
               " second instance (%s/%s/%s/%s) and the October"
               " capped-windowed chain read still equals the"
               " original pre-close snapshot=%s (windowed read"
               " survives restart x new-data unscratched)"
               % (f3_a == f2_a, f3_b == f2_b, f3_c == f2_c,
                  f3_d == f2_d, f3_a == s_oct_capped))

        # -- AC-LG29 pure-read law + hygiene -------------------------
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)
        keys_before = _count(conn, "api_dev_keys")
        ev_before = _count(lcconn, "key_events")
        for k in (kc["api_key"], lx["api_key"]):
            for w, lmt in ((None, 0), (W, 2), (NEW_WIN, 1),
                           (None, 1), (W, 0)):
                dk3.audit_lineage(k, w, lmt)
        keys_after = _count(conn, "api_dev_keys")
        ev_after = _count(lcconn, "key_events")

        source = product_pre.decode("ascii")
        idx = source.find("def audit_lineage")
        seg_end = source.find("    def ", idx + 20)
        lineage_seg = source[idx:seg_end]
        # strip docstrings and comments before the write-keyword
        # scan (first-run amendment: the naive scan hit the
        # segment's own "zero UPDATE" hygiene sentence in the
        # docstring -- a scanner artifact, not a product defect;
        # the R1888 AC-LG7 code-strip precedent applied)
        code_seg = re.sub(r'"""[\s\S]*?"""', '""', lineage_seg)
        code_seg = "\n".join(re.sub(r"#.*$", "", line)
                            for line in code_seg.splitlines())
        write_kw = re.findall(
            r"\b(INSERT|UPDATE|DELETE|REPLACE|CREATE)\b",
            code_seg)
        with open(product_path, "rb") as handle:
            product_post = handle.read()
        product_post_sha = hashlib.sha256(product_post).hexdigest()
        with open(os.path.join(BASE, "config.json"), "rb") as handle:
            cfg_bytes_end = handle.read()
        with open(os.path.abspath(__file__), "rb") as handle:
            me_bytes = handle.read()
        me_ascii = all(b < 128 for b in me_bytes)
        imports_net = [
            line for line in source.splitlines()
            if re.match(r"\s*(?:import|from)\s", line)
            and re.search(r"urllib|requests|socket|http", line)]
        mine_net = [
            line for line in
            me_bytes.decode("ascii").splitlines()
            if re.match(r"\s*(?:import|from)\s", line)
            and re.search(r"urllib|requests|socket|http", line)]
        lg29 = (keys_after == keys_before
                and ev_after == ev_before
                and len(write_kw) == 0
                and product_post == product_pre
                and product_pre_sha == product_post_sha
                and cfg_bytes_end == cfg_bytes
                and me_ascii and len(imports_net) == 0
                and len(mine_net) == 0)
        record("AC-LG29", lg29,
               "pure read: 10 read calls on the third face move"
               " zero rows (keys %d==%d, events %d==%d), audit_lineage"
               " segment zero write keywords=%d, apidev.py"
               " sha256 stable=%s, config.json byte-stable=%s,"
               " sources pure-ASCII=%s, network imports 0/0=%s"
               % (keys_after, keys_before, ev_after, ev_before,
                  len(write_kw),
                  product_pre_sha == product_post_sha,
                  cfg_bytes_end == cfg_bytes, me_ascii,
                  len(imports_net) == 0 and len(mine_net) == 0))

        conn.close()
        lcconn.close()
        _close_stack(dk3, metered3, led3)

    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window

    restored = (D._now_utc is real_now
                and D._minute_utc is real_minute
                and D._window_utc is real_window)
    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-lineagepersist: %d/%d criteria pass"
          % (passed, total), flush=True)
    print("clock restore probe: %s" % restored, flush=True)
    return 0 if (passed == total and total == 7
                 and restored) else 1


if __name__ == "__main__":
    sys.exit(main())
