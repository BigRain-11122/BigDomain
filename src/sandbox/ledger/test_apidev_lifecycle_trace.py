"""Acceptance suite for the apidev lifecycle audit trace read
face (BigDomain R1824; canon = tech-queue "apidev lifecycle event
chain audit read face" row, the R1711 lifecycle-store successor,
claimed from the tech-lane top open row per the FIFO law).
Asserts the pre-registered criteria AC-TR1..AC-TR7 from the
R1824 tech-queue claim note (criteria were registered before
this code ran; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Covered semantics: lifecycle_trace(api_key) is the pure-read
audit-profile face over the append-only key_events store -- one
key's own event timeline (revoke / rotate_out / rotate_in with
pair links) in (event_utc, event_id) order, status and both pair
links derived from the same fetched rows key_view reads (zero
drift between the two faces), the rotation chain walkable in
both directions purely through traces, dead keys fully
readable, embedded faces (key_view, dev_board) untouched.

The metered face is the real product injected by reference (no
copy); this suite never touches the billing ring (the trace face
needs zero token movement, so the suite needs no funding). This
test source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_lifecycle_trace.py
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
import apidev as D                      # noqa: E402 (R1700+R1711+R1824)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the open API is a compute"
             " + visualization interface, not investment advice")

# exact embedded-face envelope contracts (the AC-RJW4 law pins:
# this round adds zero keys to key_view / dev_board -- any future
# change to those faces must consciously update these pins)
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
TRACE_KEYS = sorted([
    "api_key", "dev_account", "key_name", "key_id", "status",
    "rotated_from_key_id", "rotated_to_key_id", "events", "total",
    "disclaimer"])
EVENT_KEYS = sorted(["event_id", "event", "pair_key_id", "event_utc"])


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


def _brief(trace):
    return [(e["event"], e["pair_key_id"]) for e in trace["events"]]


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-tr-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    lc_path = os.path.join(tmp, "api_lifecycle.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    conn = sqlite3.connect(db_path)

    # fixture world: one fresh key, one plain-revoked key, one
    # rotate chain A->B->C on a second developer (no billing calls
    # anywhere -- the trace face moves zero tokens)
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

    # -- AC-TR1 pure-read contract -------------------------------
    lcconn = sqlite3.connect(lc_path)
    keys_before = _count(conn, "api_dev_keys")
    ev_before = _count(lcconn, "key_events")
    tr_fk = dk.lifecycle_trace(fk["api_key"])
    tr_rk = dk.lifecycle_trace(rk["api_key"])
    tr_ka = dk.lifecycle_trace(ka["api_key"])
    tr_kb = dk.lifecycle_trace(kb["api_key"])
    tr_kc = dk.lifecycle_trace(kc["api_key"])   # pre-revoke C
    keys_after = _count(conn, "api_dev_keys")
    ev_after = _count(lcconn, "key_events")
    ok_unk, code_unk = expect_unknown(
        lambda: dk.lifecycle_trace("sk-nonexistent"))
    ok_empty, code_empty = expect_unknown(
        lambda: dk.lifecycle_trace(""))
    tr1 = (ok_unk and ok_empty
           and keys_after == keys_before and ev_after == ev_before
           and sorted(tr_fk.keys()) == TRACE_KEYS
           and tr_fk["api_key"] == fk["api_key"]
           and tr_fk["dev_account"] == "usr:ada"
           and tr_fk["key_name"] == "fresh-key"
           and tr_fk["key_id"] == _key_id(conn, fk["api_key"])
           and tr_fk["disclaimer"] == DISCLAIMER)
    record("AC-TR1", tr1,
           "key gate first: unknown/empty reject %s/%s, pure read:"
           " api_dev_keys %d==%d, key_events %d==%d, envelope keys"
           " exact=%s"
           % (code_unk, code_empty, keys_after, keys_before,
              ev_after, ev_before,
              sorted(tr_fk.keys()) == TRACE_KEYS))

    # -- AC-TR2 event-timeline body and ordering law --------------
    shapes_ok = all(sorted(e.keys()) == EVENT_KEYS
                    for tr in (tr_fk, tr_rk, tr_ka, tr_kb, tr_kc)
                    for e in tr["events"])
    totals_ok = all(tr["total"] == len(tr["events"])
                    for tr in (tr_fk, tr_rk, tr_ka, tr_kb, tr_kc))
    ids_sorted = all(
        [e["event_id"] for e in tr["events"]] ==
        sorted(e["event_id"] for e in tr["events"])
        and [e["event_utc"] for e in tr["events"]] ==
        sorted(e["event_utc"] for e in tr["events"])
        for tr in (tr_rk, tr_ka, tr_kb, tr_kc))
    # same-second ordering pin: synthetic double event with one
    # shared event_utc injected in rotate_out-then-rotate_in order
    # (name sort would flip them; the event_id tiebreak must not)
    pk = dk.issue_key("usr:ada", "order-probe", 5, ["backtest"],
                      False)
    pk_id = _key_id(conn, pk["api_key"])
    same_utc = "2026-01-01T00:00:00Z"
    lcconn.execute(
        "INSERT INTO key_events (key_id, event, pair_key_id,"
        " event_utc) VALUES (?, 'rotate_out', NULL, ?)",
        (pk_id, same_utc))
    lcconn.execute(
        "INSERT INTO key_events (key_id, event, pair_key_id,"
        " event_utc) VALUES (?, 'rotate_in', NULL, ?)",
        (pk_id, same_utc))
    lcconn.commit()
    tr_pk = dk.lifecycle_trace(pk["api_key"])
    order_pinned = (
        _brief(tr_pk) == [("rotate_out", None), ("rotate_in", None)]
        and [e["event_utc"] for e in tr_pk["events"]] ==
        [same_utc, same_utc]
        and [e["event_id"] for e in tr_pk["events"]] ==
        sorted(e["event_id"] for e in tr_pk["events"]))
    tr2 = (shapes_ok and totals_ok and ids_sorted and order_pinned)
    record("AC-TR2", tr2,
           "event rows verbatim keys=%s, total==len=%s,"
           " (event_utc,event_id) ascending=%s, same-second"
           " tiebreak pin [rotate_out,rotate_in] insertion order"
           " kept (name-sort would flip)=%s"
           % (shapes_ok, totals_ok, ids_sorted, order_pinned))

    # -- AC-TR5 chain walk, dead keys readable (pre-revoke world
    #    captured above; the revoke below only adds to C) -------
    walk_ok = (
        _brief(tr_ka) == [("rotate_out", id_b)]
        and _brief(tr_kb) == [("rotate_in", id_a),
                              ("rotate_out", id_c)]
        and _brief(tr_kc) == [("rotate_in", id_b)]
        and tr_ka["rotated_to_key_id"] == id_b
        and tr_kb["rotated_from_key_id"] == id_a
        and tr_kb["rotated_to_key_id"] == id_c
        and tr_kc["rotated_from_key_id"] == id_b)

    # double-terminal shape host: C was rotated in, now revoke it
    dk.revoke_key(kc["api_key"])
    tr_kc2 = dk.lifecycle_trace(kc["api_key"])

    # -- AC-TR3 every event shape (incl. double-terminal) --------
    tr3 = (
        _brief(tr_fk) == [] and tr_fk["total"] == 0
        and tr_fk["status"] == "active"
        and tr_fk["rotated_from_key_id"] is None
        and tr_fk["rotated_to_key_id"] is None
        and _brief(tr_rk) == [("revoke", None)]
        and tr_rk["status"] == "revoked"
        and _brief(tr_ka) == [("rotate_out", id_b)]
        and tr_ka["status"] == "rotated_out"
        and _brief(tr_kb) == [("rotate_in", id_a),
                              ("rotate_out", id_c)]
        and _brief(tr_kc) == [("rotate_in", id_b)]
        and _brief(tr_kc2) == [("rotate_in", id_b), ("revoke", None)]
        and tr_kc2["status"] == "revoked"
        and tr_kc2["rotated_from_key_id"] == id_b
        and tr_kc2["rotated_to_key_id"] is None)
    record("AC-TR3", tr3,
           "shapes: fresh=[] active, revoked=[revoke],"
           " A=[rotate_out->B] rotated_out, B=[rotate_in<-A,"
           " rotate_out->C], C pre=[rotate_in<-B] / post=[rotate_in"
           " <-B, revoke] revoked (double-terminal) -- briefs"
           " %s/%s/%s/%s/%s/%s"
           % (_brief(tr_fk), _brief(tr_rk), _brief(tr_ka),
              _brief(tr_kb), _brief(tr_kc), _brief(tr_kc2)))

    # -- AC-TR5 record (dead-key readability proven by every
    #    trace above succeeding on revoked/rotated-out keys) -----
    tr5 = walk_ok
    record("AC-TR5", tr5,
           "dead keys fully readable (revoked rk + rotated-out"
           " A/B + revoked-rotated-in C all trace without"
           " raising), A->B->C walkable purely through traces:"
           " pairs close both directions (A<->B=%s, B<->C=%s)"
           % ((id_a, id_b), (id_b, id_c)))

    # -- AC-TR4 derived-face zero drift (post-revoke world) -----
    drift_ok = True
    for k in (fk, rk, ka, kb, kc):
        view = dk.key_view(k["api_key"])
        trace = dk.lifecycle_trace(k["api_key"])
        if (trace["status"] != view["status"]
                or trace["rotated_from_key_id"]
                != view["rotated_from_key_id"]):
            drift_ok = False
    tr4 = drift_ok
    record("AC-TR4", tr4,
           "trace vs key_view zero drift over the five key states"
           " (fresh/revoked/rotated-out/middle/successor-revoked,"
           " post-revoke world)=%s" % drift_ok)

    # -- AC-TR6 embedded faces untouched (AC-RJW4 law) -----------
    view_fk = dk.key_view(fk["api_key"])
    board_ada = dk.dev_board("usr:ada")
    row0 = board_ada["keys"][0]
    tr6 = (sorted(view_fk.keys()) == KEY_VIEW_KEYS
           and sorted(board_ada.keys()) == BOARD_KEYS
           and sorted(row0.keys()) == BOARD_ROW_KEYS)
    record("AC-TR6", tr6,
           "key_view keys exact (%d), dev_board keys exact (%d),"
           " board row keys exact (%d) -- zero trace embedding=%s"
           % (len(KEY_VIEW_KEYS), len(BOARD_KEYS),
              len(BOARD_ROW_KEYS), tr6))

    # -- AC-TR7 hygiene face --------------------------------------
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
    has_trace = "def lifecycle_trace" in source
    tr7 = (cfg_bytes_end == cfg_bytes and is_ascii
           and not has_update and not has_rng
           and len(imports_net) == 0 and has_trace)
    record("AC-TR7", tr7,
           "hygiene: config.json byte-stable=%s, source"
           " pure-ASCII=%s, zero UPDATE=%s, zero RNG=%s,"
           " net-imports=%d, lifecycle_trace present=%s"
           % (cfg_bytes_end == cfg_bytes, is_ascii, not has_update,
              not has_rng, len(imports_net), has_trace))

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-lifecycle-trace: %d/%d criteria pass"
          % (passed, total), flush=True)
    lcconn.close()
    conn.close()
    dk.close()
    metered.close()
    led.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
