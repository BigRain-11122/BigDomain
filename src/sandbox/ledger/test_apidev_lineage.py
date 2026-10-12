"""Acceptance suite for the apidev rotation lineage audit read
face (BigDomain R1825; canon = tech-queue "apidev lifecycle
one-shot lineage read face" row, the R1824 lifecycle_trace
successor, claimed from the tech-lane top open row per the FIFO
law) and its R1887 explicit-month-window lens (canon = the
"apidev audit_lineage explicit month window" tech-queue row,
the R1875 lifecycle_trace window successor) and its R1888
read-cap window (canon = the "apidev audit_lineage read cap"
tech-queue row, the R1887 successor seed). Asserts the
pre-registered criteria AC-LG1..AC-LG7 from the R1825 claim
note plus AC-LG8..AC-LG15 from the R1887 claim note plus
AC-LG16..AC-LG22 from the R1888 claim note (criteria
were registered before this code ran; honesty law). Each
criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

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
WINDOWED_KEYS = sorted(LINEAGE_KEYS + ["window"])
MEMBER_KEYS = sorted([
    "key_id", "dev_account", "key_name", "status",
    "rotated_from_key_id", "rotated_to_key_id", "events",
    "total"])
EVENT_KEYS = sorted(["event_id", "event", "pair_key_id", "event_utc"])
# bad window forms, the R1856 family tuple (11 base + 3 trailing)
BADS14 = ("2026-13", "2026-00", "2026-1", "2026/10", "2026",
          "202610", "abcd", "", 2026, True, 2.5, "2026-10\n",
          "2026-10 ", "2026-10\r")
# five bad limit forms (the R1840 dev_board read-cap family)
BAD_LIMIT5 = (-1, True, "2", 2.5, None)
# capped envelope key sets (the R1888 overflow block)
CAPPED_KEYS = sorted(LINEAGE_KEYS
                     + ["limit", "total", "returned", "truncated"])
CAPPED_WIN_KEYS = sorted(CAPPED_KEYS + ["window"])
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

    # -- R1887 window lens: explicit month window on the lineage ---
    # (AC-LG8..AC-LG15 pre-registered in the tech-queue claim
    # note before this suite code ran; honesty law)

    # -- AC-LG8 default fidelity -------------------------------------
    five_apis = [fk["api_key"], rk["api_key"], ka["api_key"],
                 kb["api_key"], kc["api_key"]]
    five_defaults = [lg_fk, lg_rk, lg_ka2, lg_kb2, lg_kc2]
    fidelity = all(
        json.dumps(dk.audit_lineage(k, window=None),
                   sort_keys=True)
        == json.dumps(d, sort_keys=True)
        for k, d in zip(five_apis, five_defaults))
    default_keys_ok = all(
        sorted(d.keys()) == LINEAGE_KEYS
        for d in five_defaults)
    lg8 = fidelity and default_keys_ok
    record("AC-LG8", lg8,
           "default call == window=None call byte-identical on"
           " all 5 queried keys=%s, default envelope keys exact"
           " %d (zero window key)=%s"
           % (fidelity, len(LINEAGE_KEYS), default_keys_ok))

    # -- AC-LG9 bad window fail-closed --------------------------------
    keys_b9 = _count(conn, "api_dev_keys")
    ev_b9 = _count(lcconn, "key_events")
    bad_rejects = []
    for bad in BADS14:
        try:
            dk.audit_lineage(fk["api_key"], bad)
            bad_rejects.append(bad)
        except D.ApiDevError as exc:
            if exc.code != D.E_AD_BAD_ARGS:
                bad_rejects.append(bad)
    ok_unk_win, code_unk_win = expect_unknown(
        lambda: dk.audit_lineage("sk-nonexistent", "2026-99"))
    keys_a9 = _count(conn, "api_dev_keys")
    ev_a9 = _count(lcconn, "key_events")
    lg9 = (len(bad_rejects) == 0 and ok_unk_win
           and keys_a9 == keys_b9 and ev_a9 == ev_b9)
    record("AC-LG9", lg9,
           "14 bad forms all reject E_AD_BAD_ARGS (audit-family"
           " code) rejects=%d, key gate first: unknown+bad"
           " window -> %s, pure read: keys %d==%d events %d==%d"
           % (len(bad_rejects), code_unk_win, keys_a9, keys_b9,
              ev_a9, ev_b9))

    # -- AC-LG10 window lens semantics + cross-face lock -------------
    # month-abstraction law (R1813): W derives from a real
    # event's record-time prefix, never hardcoded
    lg_cur = dk.audit_lineage(kc["api_key"])
    W = lg_cur["chain"][2]["events"][-1]["event_utc"][:7]
    win_reads = {k: dk.audit_lineage(k, W) for k in five_apis}
    lens_ok = all(
        m["total"] == len(m["events"])
        and sorted(m.keys()) == MEMBER_KEYS
        and all(e["event_utc"][:7] == W
                for e in m["events"])
        for w in win_reads.values()
        for m in w["chain"])
    env_ok10 = all(
        sorted(w.keys()) == WINDOWED_KEYS and w["window"] == W
        for w in win_reads.values())
    cross_ok = True
    for w in win_reads.values():
        for m in w["chain"]:
            api = conn.execute(
                "SELECT api_key FROM api_dev_keys"
                " WHERE key_id = ?", (m["key_id"],)).fetchone()
            trace = dk.lifecycle_trace(api[0], W)
            if (m["events"] != trace["events"]
                    or m["total"] != trace["total"]):
                cross_ok = False
    lg10 = lens_ok and env_ok10 and cross_ok
    record("AC-LG10", lg10,
           "window=%s lens: member events all in-month=%s,"
           " member keys exact=%s, envelope adds exactly window"
           " key=%s, member events/total == lifecycle_trace"
           "(member, window) cross-face=%s"
           % (W, lens_ok, lens_ok, env_ok10, cross_ok))

    # -- AC-LG11 key attributes not sliced ---------------------------
    facts_ok = True
    for k in five_apis:
        d = dk.audit_lineage(k)
        w = win_reads[k]
        if (_ids(d) != _ids(w) or _names(d) != _names(w)
                or d["chain_size"] != w["chain_size"]
                or d["queried_index"] != w["queried_index"]):
            facts_ok = False
        for md, mw in zip(d["chain"], w["chain"]):
            if (md["status"] != mw["status"]
                    or md["rotated_from_key_id"]
                    != mw["rotated_from_key_id"]
                    or md["rotated_to_key_id"]
                    != mw["rotated_to_key_id"]):
                facts_ok = False
    july = dk.audit_lineage(kb["api_key"], "2026-07")
    july_facts = (_ids(july) == _ids(dk.audit_lineage(kb["api_key"]))
                  and july["chain_size"] == 3
                  and july["queried_index"] == 1)
    lg11 = facts_ok and july_facts
    record("AC-LG11", lg11,
           "windowed vs default reads: chain ids/order/names/"
           "sizes/queried_index/member status + pair links all"
           " identical on 5 queried keys=%s, zero-event window"
           " keeps full chain shape=%s"
           % (facts_ok, july_facts))

    # -- AC-LG12 historical month window (fixture direct INSERT) -----
    # (R1730 family precedent: fixture rows injected directly,
    # noted here -- production rows carry their own record time)
    id_rk = _key_id(conn, rk["api_key"])
    hist_ts = "2026-08-15T00:00:00.000000Z"
    lcconn.execute(
        "INSERT INTO key_events (key_id, event, pair_key_id,"
        " event_utc) VALUES (?, 'revoke', NULL, ?)",
        (id_rk, hist_ts))
    lcconn.commit()
    lg_hist = dk.audit_lineage(rk["api_key"], "2026-08")
    hist_block = lg_hist["chain"][0]
    hist_ok = (lg_hist["chain_size"] == 1
               and hist_block["total"] == 1
               and hist_block["status"] == "revoked"
               and hist_block["events"][0]["event_utc"] == hist_ts
               and hist_block["events"][0]["event"] == "revoke")
    cur_w_rk = dk.audit_lineage(rk["api_key"], W)
    cur_isolated = (cur_w_rk["chain"][0]["total"] == 1
                    and cur_w_rk["chain"][0]["events"][0]
                    ["event_utc"][:7] == W)
    no_leak = all(
        e["event_utc"][:7] != "2026-08"
        for w in win_reads.values()
        for m in w["chain"] for e in m["events"])
    lg_def = dk.audit_lineage(rk["api_key"])
    full_trail = (lg_def["chain"][0]["total"] == 2
                  and lg_def["chain"][0]["events"][0]
                  ["event_utc"] == hist_ts
                  and lg_def["chain"][0]["events"][1]
                  ["event_utc"][:7] == W)
    lg_fut = dk.audit_lineage(kb["api_key"], "2026-12")
    fut_ok = all(m["total"] == 0 and m["events"] == []
                 for m in lg_fut["chain"])
    lg12 = hist_ok and cur_isolated and no_leak and full_trail \
        and fut_ok
    record("AC-LG12", lg12,
           "injected historical revoke (2026-08) reads in that"
           " window=%s, current window isolated=%s, no"
           " cross-month leak=%s, default full trail keeps both"
           " rows=%s, future window honest empty=%s"
           % (hist_ok, cur_isolated, no_leak, full_trail, fut_ok))

    # -- AC-LG13 pair integrity under the window ----------------------
    w_kb = win_reads[kb["api_key"]]
    both_sides = (
        any(e["event"] == "rotate_out"
            for e in w_kb["chain"][0]["events"])
        and any(e["event"] == "rotate_in"
                for e in w_kb["chain"][1]["events"]))
    july_kb = dk.audit_lineage(kb["api_key"], "2026-07")
    links_stay = (july_kb["chain"][0]["rotated_to_key_id"] == id_b
                  and july_kb["chain"][1]["rotated_from_key_id"]
                  == id_a
                  and july_kb["chain"][0]["events"] == []
                  and july_kb["chain"][1]["events"] == [])
    # single-side tamper demo (production unreachable: pairs
    # land in one transaction at one timestamp; direct INSERT
    # builds the honest single-side display case)
    july_ts = "2026-07-15T00:00:00.000000Z"
    lcconn.execute(
        "INSERT INTO key_events (key_id, event, pair_key_id,"
        " event_utc) VALUES (?, 'rotate_in', NULL, ?)",
        (id_rk, july_ts))
    lcconn.commit()
    lg_side = dk.audit_lineage(rk["api_key"], "2026-07")
    side_block = lg_side["chain"][0]
    single_side = (lg_side["chain_size"] == 1
                   and side_block["total"] == 1
                   and side_block["events"][0]["event"]
                   == "rotate_in"
                   and side_block["status"] == "revoked"
                   and side_block["key_id"] == id_rk)
    lg13 = both_sides and links_stay and single_side
    record("AC-LG13", lg13,
           "current window shows rotate pair on both member"
           " blocks=%s, zero-event window drops both sides while"
           " pair links stay=%s, single-side tamper displayed"
           " honestly + chain walk unchanged=%s"
           % (both_sides, links_stay, single_side))

    # -- AC-LG14 pure-read law + determinism --------------------------
    keys_b14 = _count(conn, "api_dev_keys")
    ev_b14 = _count(lcconn, "key_events")
    for k in five_apis:
        for w in (None, W, "2026-07", "2026-08", "2026-12"):
            dk.audit_lineage(k, w)
    keys_a14 = _count(conn, "api_dev_keys")
    ev_a14 = _count(lcconn, "key_events")
    det_ok = all(
        json.dumps(dk.audit_lineage(kb["api_key"], w),
                   sort_keys=True)
        == json.dumps(dk.audit_lineage(kb["api_key"], w),
                      sort_keys=True)
        for w in (W, "2026-08"))
    lg14 = (keys_a14 == keys_b14 and ev_a14 == ev_b14
            and det_ok)
    record("AC-LG14", lg14,
           "25 window reads move zero rows: keys %d==%d events"
           " %d==%d, double-call byte-identical=%s"
           % (keys_a14, keys_b14, ev_a14, ev_b14, det_ok))

    # -- AC-LG15 hygiene face -----------------------------------------
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes_end15 = handle.read()
    sig_ok = re.search(
        r"def audit_lineage\(self, api_key, window=None,"
        r" limit=0\)", source) is not None
    view_pin = sorted(dk.key_view(fk["api_key"]).keys()) \
        == KEY_VIEW_KEYS
    board_pin = sorted(dk.dev_board("usr:ada").keys()) \
        == BOARD_KEYS
    row_pin = sorted(dk.dev_board("usr:ada")["keys"][0].keys()) \
        == BOARD_ROW_KEYS
    ascii15 = all(ord(ch) < 128 for ch in source)
    lg15 = (cfg_bytes_end15 == cfg_bytes and sig_ok and view_pin
            and board_pin and row_pin and ascii15)
    record("AC-LG15", lg15,
           "config.json byte-stable=%s, signature window=None"
           " present=%s, embedded faces exact-pin (key_view %d"
           "/ board %d / row %d keys)=%s, source pure-ASCII=%s"
           % (cfg_bytes_end15 == cfg_bytes, sig_ok,
              len(KEY_VIEW_KEYS), len(BOARD_KEYS),
              len(BOARD_ROW_KEYS),
              view_pin and board_pin and row_pin, ascii15))

    # -- AC-LG16..AC-LG22 read-cap window (R1888 claim note) -----
    # extend the world to a five-member chain X->D->E->F->G so a
    # real truncation case exists. First-run amendment (honest
    # note): extending the A->B->C fixture chain by two more
    # rotations is impossible -- AC-LG5 already revoked C into
    # a terminal key, so rotate_key(C) rejects E_AD_ALREADY. A
    # new seed key on usr:lin plus four rotations builds the
    # five-member chain instead (X rotated-out oldest, G active
    # newest; the A->B->C chain stays untouched for the already
    # recorded criteria above).
    kx = dk.issue_key("usr:lin", "chain-x", 5, ["backtest"], True)
    kd = dk.rotate_key(kx["api_key"], "chain-d")
    ke = dk.rotate_key(kd["api_key"], "chain-e")
    kf2 = dk.rotate_key(ke["api_key"], "chain-f")
    kg = dk.rotate_key(kf2["api_key"], "chain-g")
    id_x = _key_id(conn, kx["api_key"])
    id_d = _key_id(conn, kd["api_key"])
    id_e = _key_id(conn, ke["api_key"])
    id_f = _key_id(conn, kf2["api_key"])
    id_g = _key_id(conn, kg["api_key"])

    # AC-LG16: default + explicit zero stay byte-stable
    lg_def_g = dk.audit_lineage(kg["api_key"])
    lg16 = (sorted(lg_def_g.keys()) == LINEAGE_KEYS
            and lg_def_g["chain_size"] == 5
            and _ids(lg_def_g) == [id_x, id_d, id_e, id_f, id_g]
            and lg_def_g["queried_index"] == 4)
    lg_exp0 = dk.audit_lineage(kg["api_key"], None, 0)
    lg16 = lg16 and json.dumps(lg_exp0, sort_keys=True) \
        == json.dumps(lg_def_g, sort_keys=True)
    record("AC-LG16", lg16,
           "default read keeps exact LINEAGE_KEYS on the"
           " five-member chain=%s, explicit limit=0 read"
           " byte-identical to default=%s"
           % (sorted(lg_def_g.keys()) == LINEAGE_KEYS,
              json.dumps(lg_exp0, sort_keys=True)
              == json.dumps(lg_def_g, sort_keys=True)))

    # AC-LG17: five bad limit forms fail-closed E_AD_BAD_LIMIT
    keys_b17 = _count(conn, "api_dev_keys")
    ev_b17 = _count(lcconn, "key_events")
    bad_codes = []
    for bad in BAD_LIMIT5:
        try:
            dk.audit_lineage(kg["api_key"], None, bad)
            bad_codes.append("no-error")
        except D.ApiDevError as exc:
            bad_codes.append(exc.code)
    ok_unk_lim = expect_unknown(
        lambda: dk.audit_lineage("sk-nope", None, -1))
    try:
        dk.audit_lineage(kg["api_key"], "2026-13", -1)
        code_both = "no-error"
    except D.ApiDevError as exc:
        code_both = exc.code
    keys_a17 = _count(conn, "api_dev_keys")
    ev_a17 = _count(lcconn, "key_events")
    lg17 = (bad_codes == [D.E_AD_BAD_LIMIT] * 5
            and ok_unk_lim[0] and code_both == D.E_AD_BAD_LIMIT
            and keys_a17 == keys_b17 and ev_a17 == ev_b17)
    record("AC-LG17", lg17,
           "five bad limits all reject %s codes=%s, key gate"
           " first (unknown+bad limit -> %s), limit gate before"
           " window gate (bad limit+bad window -> %s), zero"
           " rows moved %d==%d %d==%d"
           % (D.E_AD_BAD_LIMIT, sorted(set(bad_codes)),
              ok_unk_lim[1], code_both, keys_a17, keys_b17,
              ev_a17, ev_b17))

    # AC-LG18: cap semantics + overflow block + key-facts law
    lg_cap2 = dk.audit_lineage(kg["api_key"], None, 2)
    slice_ok = json.dumps(lg_cap2["chain"], sort_keys=True) \
        == json.dumps(lg_def_g["chain"][-2:], sort_keys=True)
    block_ok = (lg_cap2["limit"] == 2 and lg_cap2["total"] == 5
                and lg_cap2["returned"] == 2
                and lg_cap2["truncated"] is True)
    shape_ok = (sorted(lg_cap2.keys()) == CAPPED_KEYS
                and lg_cap2["chain_size"] == 2
                and lg_cap2["queried_index"] == 4
                == lg_def_g["queried_index"])
    lg_cap_old = dk.audit_lineage(kx["api_key"], None, 2)
    old_ok = (_ids(lg_cap_old) == [id_f, id_g]
              and lg_cap_old["queried_index"] == 0
              and lg_cap_old["truncated"] is True
              and lg_cap_old["total"] == 5
              and lg_cap_old["returned"] == 2
              and id_x not in _ids(lg_cap_old))
    lg18 = slice_ok and block_ok and shape_ok and old_ok
    record("AC-LG18", lg18,
           "limit=2 tail slice byte-identical to full read"
           " tail=%s, overflow block {limit=%s,total=%s,"
           "returned=%s,truncated=%s}=%s, envelope+queried_index"
           " stay full-chain facts=%s, oldest-key query slice"
           " [F,G] excludes the queried key with honest"
           " truncated=%s"
           % (slice_ok, lg_cap2["limit"], lg_cap2["total"],
              lg_cap2["returned"], lg_cap2["truncated"],
              block_ok, shape_ok, old_ok))

    # AC-LG19: window x cap orthogonality
    lg_win_only = dk.audit_lineage(kg["api_key"], W)
    lg_cap_win = dk.audit_lineage(kg["api_key"], W, 2)
    orth_slice = json.dumps(lg_cap_win["chain"],
                            sort_keys=True) \
        == json.dumps(lg_win_only["chain"][-2:], sort_keys=True)
    orth_ok = (lg_cap_win["total"] == 5
               and lg_win_only["chain_size"] == 5
               and lg_cap_win["window"] == W
               and sorted(lg_cap_win.keys())
               == CAPPED_WIN_KEYS)
    lg_cap_july = dk.audit_lineage(kg["api_key"], "2026-07", 2)
    july_total = (lg_cap_july["total"] == 5
                  and lg_cap_july["returned"] == 2
                  and lg_cap_july["truncated"] is True
                  and all(m["total"] == 0
                          for m in lg_cap_july["chain"]))
    lg19 = orth_slice and orth_ok and july_total
    record("AC-LG19", lg19,
           "capped+windowed slice == windowed read tail=%s,"
           " total==windowed chain_size==5 with window echo +"
           " block additive=%s, zero-event window keeps total=5"
           " with empty trails=%s"
           % (orth_slice, orth_ok, july_total))

    # AC-LG20: honest non-truncating block + dead-key cap read
    lg_fresh1 = dk.audit_lineage(fk["api_key"], None, 1)
    lg_fresh5 = dk.audit_lineage(fk["api_key"], None, 5)
    fresh_ok = (lg_fresh1["limit"] == 1
                and lg_fresh1["total"] == 1
                and lg_fresh1["returned"] == 1
                and lg_fresh1["truncated"] is False
                and lg_fresh5["limit"] == 5
                and lg_fresh5["total"] == 1
                and lg_fresh5["returned"] == 1
                and lg_fresh5["truncated"] is False)
    lg_dead_cap = dk.audit_lineage(rk["api_key"], None, 1)
    dead_ok = (lg_dead_cap["total"] == 1
               and lg_dead_cap["returned"] == 1
               and lg_dead_cap["truncated"] is False
               and lg_dead_cap["chain"][0]["status"]
               == "revoked")
    lg20 = fresh_ok and dead_ok
    record("AC-LG20", lg20,
           "single-member chain cap reads carry the honest"
           " block (limit=1 and oversized limit=5 both"
           " truncated=False)=%s, revoked dead-key cap read"
           " stays open=%s" % (fresh_ok, dead_ok))

    # AC-LG21: pure-read law + determinism under the cap
    keys_b21 = _count(conn, "api_dev_keys")
    ev_b21 = _count(lcconn, "key_events")
    for k in (kg["api_key"], kx["api_key"], fk["api_key"],
              rk["api_key"]):
        for w, lmt in ((None, 2), (W, 2), (None, 0), (None, 1)):
            dk.audit_lineage(k, w, lmt)
    keys_a21 = _count(conn, "api_dev_keys")
    ev_a21 = _count(lcconn, "key_events")
    det21 = all(
        json.dumps(dk.audit_lineage(kg["api_key"], w, l),
                   sort_keys=True)
        == json.dumps(dk.audit_lineage(kg["api_key"], w, l),
                      sort_keys=True)
        for w, l in ((None, 2), (W, 2), (None, 0)))
    lg21 = (keys_a21 == keys_b21 and ev_a21 == ev_b21
            and det21)
    record("AC-LG21", lg21,
           "16 capped reads move zero rows: keys %d==%d events"
           " %d==%d, double-call byte-identical on three cap"
           " forms=%s" % (keys_a21, keys_b21, ev_a21, ev_b21,
                         det21))

    # AC-LG22: hygiene face
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes_end22 = handle.read()
    sig_ok22 = re.search(
        r"def audit_lineage\(self, api_key, window=None,"
        r" limit=0\)", source) is not None
    view_pin22 = sorted(dk.key_view(fk["api_key"]).keys()) \
        == KEY_VIEW_KEYS
    board_pin22 = sorted(dk.dev_board("usr:ada").keys()) \
        == BOARD_KEYS
    imports_ok22 = all(
        not re.search(r"\b(urllib|requests|socket|http)\b", ln)
        for ln in source.splitlines()
        if ln.startswith(("import ", "from ")))
    with open(os.path.abspath(__file__), "rb") as handle:
        me_bytes = handle.read()
    me_ascii = all(b < 128 for b in me_bytes)
    ascii22 = all(ord(ch) < 128 for ch in source)
    lg22 = (cfg_bytes_end22 == cfg_bytes and sig_ok22
            and view_pin22 and board_pin22 and imports_ok22
            and me_ascii and ascii22)
    record("AC-LG22", lg22,
           "config.json byte-stable=%s, new signature pin=%s,"
           " embedded faces exact-pin=%s, product imports"
           " network-free=%s, sources pure-ASCII (suite=%s"
           " product=%s)"
           % (cfg_bytes_end22 == cfg_bytes, sig_ok22,
              view_pin22 and board_pin22, imports_ok22,
              me_ascii, ascii22))

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
