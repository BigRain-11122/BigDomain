"""Acceptance suite for the apidev rotation lineage audit read
face (BigDomain R1825; canon = tech-queue "apidev lifecycle
one-shot lineage read face" row, the R1824 lifecycle_trace
successor, claimed from the tech-lane top open row per the FIFO
law). Asserts the pre-registered criteria AC-LG1..AC-LG7 from
the R1825 tech-queue claim note (criteria were registered before
this code ran; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Covered semantics: audit_lineage(api_key) is the pure-read
one-shot lineage face over the append-only key_events store --
rotate_in walked upward level by level plus rotate_out walked
downward, one ordered chain (oldest ancestor first, queried key
in the middle, newest descendant last), every member block
carrying the member's own id/name/status/pair links/events (the
exact derivation lifecycle_trace performs per key, so the two
faces cannot drift), member blocks exposing zero foreign raw
api_keys, dead keys fully readable, embedded faces untouched.

The metered face is the real product injected by reference (no
copy); this suite never touches the billing ring (the lineage
face moves zero tokens, so the suite needs no funding). This
test source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_lineage.py
"""

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
import apidev as D                      # noqa: E402 (R1700+R1711+R1824+R1825)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the open API is a compute"
             " + visualization interface, not investment advice")

# exact embedded-face envelope contracts (the AC-RJW4 law pins --
# same pin lists as the R1824 lifecycle-trace suite: this round
# adds zero keys to key_view / dev_board)
KEY_VIEW_KEYS = sorted([
    "api_key", "dev_account", "key_name", "metered_client",
    "window_cap", "enabled_kinds", "ai_label", "minute_cap",
    "status", "rotated_from_key_id", "window", "quota_used",
    "quota_remaining", "minute_window", "minute_used",
    "reject_tally", "usage_kind_tally", "disclaimer"])
BOARD_KEYS = sorted([
    "dev_account", "keys", "window", "reject_tally_total",
    "usage_kind_tally_total", "disclaimer"])
BOARD_ROW_KEYS = sorted([
    "key_name", "api_key", "metered_client", "window_cap",
    "enabled_kinds", "ai_label", "minute_cap", "status",
    "rotated_from_key_id", "quota_used", "minute_window",
    "minute_used", "reject_tally", "usage_kind_tally", "billing"])
LINEAGE_KEYS = sorted([
    "api_key", "dev_account", "key_name", "key_id", "chain",
    "chain_size", "queried_index", "disclaimer"])
MEMBER_KEYS = sorted([
    "key_id", "dev_account", "key_name", "status",
    "rotated_from_key_id", "rotated_to_key_id", "events",
    "total"])
EVENT_KEYS = sorted(["event_id", "event", "pair_key_id", "event_utc"])
# AC-LG3 lock fields: shared by a lineage member block and a
# lifecycle_trace envelope
LOCK_FIELDS = ["dev_account", "key_name", "status",
               "rotated_from_key_id", "rotated_to_key_id",
               "events", "total"]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_unknown(fn):
    try:
        fn()
    except D.ApiDevError as exc:
        return exc.code == D.E_AD_UNKNOWN_KEY, exc.code
    return False, "no-error-raised"


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _key_id(conn, api_key):
    return conn.execute(
        "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
        (api_key,)).fetchone()[0]


def _names(lineage):
    return [m["key_name"] for m in lineage["chain"]]


def _ids(lineage):
    return [m["key_id"] for m in lineage["chain"]]


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-lg-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    lc_path = os.path.join(tmp, "api_lifecycle.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    conn = sqlite3.connect(db_path)
    lcconn = sqlite3.connect(lc_path)

    # fixture world (R1824 trace-suite world reused): one fresh
    # key, one plain-revoked key, one rotate chain A->B->C on a
    # second developer -- zero billing calls anywhere
    fk = dk.issue_key("usr:ada", "fresh-key", 5, ["backtest"], False)
    rk = dk.issue_key("usr:ada", "plain-revoked", 5, ["backtest"],
                      False)
    dk.revoke_key(rk["api_key"])
    ka = dk.issue_key("usr:lin", "chain-a", 5, ["backtest"], True)
    kb = dk.rotate_key(ka["api_key"], "chain-b")
    kc = dk.rotate_key(kb["api_key"], "chain-c")
    id_a = _key_id(conn, ka["api_key"])
    id_b = _key_id(conn, kb["api_key"])
    id_c = _key_id(conn, kc["api_key"])

    source = open(os.path.join(BASE, "apidev.py"), "r",
                  encoding="ascii").read()

    # -- AC-LG1 pure-read contract + key gate first ----------------
    keys_before = _count(conn, "api_dev_keys")
    ev_before = _count(lcconn, "key_events")
    ok_unk, code_unk = expect_unknown(
        lambda: dk.audit_lineage("sk-nonexistent"))
    ok_empty, code_empty = expect_unknown(
        lambda: dk.audit_lineage(""))
    lg_fk = dk.audit_lineage(fk["api_key"])
    lg_rk = dk.audit_lineage(rk["api_key"])
    lg_ka = dk.audit_lineage(ka["api_key"])
    lg_kb = dk.audit_lineage(kb["api_key"])
    lg_kc = dk.audit_lineage(kc["api_key"])   # pre-revoke C world
    keys_after = _count(conn, "api_dev_keys")
    ev_after = _count(lcconn, "key_events")
    env_ok = all(sorted(x.keys()) == LINEAGE_KEYS
                 for x in (lg_fk, lg_rk, lg_ka, lg_kb, lg_kc))
    lg1 = (ok_unk and ok_empty
           and keys_after == keys_before and ev_after == ev_before
           and env_ok
           and lg_kb["api_key"] == kb["api_key"]
           and lg_kb["dev_account"] == "usr:lin"
           and lg_kb["key_name"] == "chain-b"
           and lg_kb["key_id"] == id_b
           and lg_kb["disclaimer"] == DISCLAIMER)
    record("AC-LG1", lg1,
           "key gate first: unknown/empty reject %s/%s, pure read:"
           " api_dev_keys %d==%d, key_events %d==%d, envelope"
           " keys exact=%s, top-level api_key==queried=%s"
           % (code_unk, code_empty, keys_after, keys_before,
              ev_after, ev_before, env_ok,
              lg_kb["api_key"] == kb["api_key"]))

    # -- AC-LG2 lineage expansion body ------------------------------
    member_shapes = all(
        sorted(m.keys()) == MEMBER_KEYS
        and m["total"] == len(m["events"])
        and all(sorted(e.keys()) == EVENT_KEYS
               for e in m["events"])
        for lg in (lg_fk, lg_rk, lg_ka, lg_kb, lg_kc)
        for m in lg["chain"])
    zero_foreign_secrets = all(
        "api_key" not in m
        for lg in (lg_fk, lg_rk, lg_ka, lg_kb, lg_kc)
        for m in lg["chain"])
    chain_ok = all(
        lg["chain_size"] == 3 and _names(lg) ==
        ["chain-a", "chain-b", "chain-c"]
        for lg in (lg_ka, lg_kb, lg_kc))
    idx_ok = (lg_ka["queried_index"] == 0
              and lg_kb["queried_index"] == 1
              and lg_kc["queried_index"] == 2)
    ma, mb, mc = (lg_kb["chain"][0], lg_kb["chain"][1],
                  lg_kb["chain"][2])
    pair_close = (ma["rotated_to_key_id"] == id_b
                  and mb["rotated_from_key_id"] == id_a
                  and mb["rotated_to_key_id"] == id_c
                  and mc["rotated_from_key_id"] == id_b)
    same_dev = all(m["dev_account"] == "usr:lin"
                   for m in lg_kb["chain"])
    lg2 = (member_shapes and zero_foreign_secrets
           and chain_ok and idx_ok and pair_close and same_dev)
    record("AC-LG2", lg2,
           "A->B->C from any member: chain_size==3 and order"
           " [A,B,C]=%s, queried_index 0/1/2=%s, member keys"
           " exact=%s, zero foreign raw api_keys=%s, pair"
           " closure both directions=%s, single dev=%s"
           % (chain_ok, idx_ok, member_shapes,
              zero_foreign_secrets, pair_close, same_dev))

    # -- AC-LG3 zero-drift lock vs lifecycle_trace ------------------
    drift_ok = True
    for lg in (lg_fk, lg_rk, lg_ka, lg_kb, lg_kc):
        for m in lg["chain"]:
            api = conn.execute(
                "SELECT api_key FROM api_dev_keys"
                " WHERE key_id = ?", (m["key_id"],)).fetchone()
            trace = dk.lifecycle_trace(api[0])
            for field in LOCK_FIELDS:
                if m[field] != trace[field]:
                    drift_ok = False
    lg3 = drift_ok
    record("AC-LG3", lg3,
           "every member block vs lifecycle_trace(member) equal"
           " on all %d lock fields over every queried chain"
           " (fresh/revoked/A/B/C)=%s"
           % (len(LOCK_FIELDS), drift_ok))

    # -- AC-LG4 lone-key shapes -------------------------------------
    lg4 = (lg_fk["chain_size"] == 1
           and lg_fk["queried_index"] == 0
           and lg_fk["chain"][0]["key_id"] ==
           _key_id(conn, fk["api_key"])
           and lg_fk["chain"][0]["status"] == "active"
           and lg_fk["chain"][0]["events"] == []
           and lg_rk["chain_size"] == 1
           and lg_rk["chain"][0]["status"] == "revoked"
           and [e["event"] for e in
                lg_rk["chain"][0]["events"]] == ["revoke"])
    record("AC-LG4", lg4,
           "lone keys self-chain: fresh chain_size==1 active"
           " events=[], plain-revoked chain_size==1 revoked"
           " [revoke]=%s" % lg4)

    # -- AC-LG5 query-point independence + dead keys readable ------
    # double-terminal shape host: C was rotated in, now revoke it
    dk.revoke_key(kc["api_key"])
    lg_ka2 = dk.audit_lineage(ka["api_key"])
    lg_kb2 = dk.audit_lineage(kb["api_key"])
    lg_kc2 = dk.audit_lineage(kc["api_key"])
    point_indep = (_ids(lg_ka2) == _ids(lg_kb2) == _ids(lg_kc2)
                   == [id_a, id_b, id_c]
                   and _names(lg_kc2) ==
                   ["chain-a", "chain-b", "chain-c"])
    dead_readable = (
        lg_kc2["chain_size"] == 3
        and lg_kc2["chain"][2]["status"] == "revoked"
        and [e["event"] for e in
             lg_kc2["chain"][2]["events"]] ==
        ["rotate_in", "revoke"]
        and lg_ka2["chain"][0]["status"] == "rotated_out")
    lg5 = point_indep and dead_readable
    record("AC-LG5", lg5,
           "post-revoke world: member id sequence [A,B,C] equal"
           " from every query point=%s, dead members fully"
           " readable (rotated-out A + double-terminal revoked"
           " C with [rotate_in,revoke])=%s"
           % (point_indep, dead_readable))

    # -- AC-LG6 embedded faces untouched (AC-RJW4 law) --------------
    view_fk = dk.key_view(fk["api_key"])
    board_ada = dk.dev_board("usr:ada")
    row0 = board_ada["keys"][0]
    lg6 = (sorted(view_fk.keys()) == KEY_VIEW_KEYS
           and sorted(board_ada.keys()) == BOARD_KEYS
           and sorted(row0.keys()) == BOARD_ROW_KEYS)
    record("AC-LG6", lg6,
           "key_view keys exact (%d), dev_board keys exact (%d),"
           " board row keys exact (%d) -- zero lineage embedding=%s"
           % (len(KEY_VIEW_KEYS), len(BOARD_KEYS),
              len(BOARD_ROW_KEYS), lg6))

    # -- AC-LG7 hygiene face ----------------------------------------
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes_end = handle.read()
    imports_net = [line for line in source.splitlines()
                   if re.match(r"\s*(?:import|from)\s", line)
                   and re.search(r"urllib|requests|socket|http",
                                 line)]
    is_ascii = all(ord(ch) < 128 for ch in source)
    code_only = re.sub(r'"""[\s\S]*?"""', '""', source)
    code_only = "\n".join(re.sub(r"#.*$", "", line)
                          for line in code_only.splitlines())
    has_update = re.search(r"\bUPDATE\b", code_only) is not None
    has_rng = re.search(r"\brandom\b", source) is not None
    has_lineage = "def audit_lineage" in source
    lg7 = (cfg_bytes_end == cfg_bytes and is_ascii
           and not has_update and not has_rng
           and len(imports_net) == 0 and has_lineage)
    record("AC-LG7", lg7,
           "hygiene: config.json byte-stable=%s, source"
           " pure-ASCII=%s, zero UPDATE=%s, zero RNG=%s,"
           " net-imports=%d, audit_lineage present=%s"
           % (cfg_bytes_end == cfg_bytes, is_ascii, not has_update,
              not has_rng, len(imports_net), has_lineage))

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-lineage: %d/%d criteria pass"
          % (passed, total), flush=True)
    lcconn.close()
    conn.close()
    dk.close()
    metered.close()
    led.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
