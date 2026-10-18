"""Zero-earn boundary gate-family cross-restart same-code window
for the multi-year combined honor yearbook read face (BigDomain
R2028; canon = the explore-queue zero-earn boundary gate-family
claim row, criteria AC-HYZG1..AC-HYZG7 pre-registered in that
row before this code existed; honesty law). Each criterion
prints PASS/FAIL with evidence; the process exits non-zero on
any FAIL.

Suite-only round: the shipped yearbooks_combined and
grant_year_honors faces are NOT touched. The window pins the
gate-family cross-restart semantics the zero-earn boundary
persist suite left open: the 14-probe front-door rejection
battery (the R2027 AC-HYZB2 probe face) must reject with the
same code vector on the pre-close instance and on both
full-stack restart instances; the CountingCivic wrapper keeps
its per-instance zero-calls-on-rejects / one-call-on-control
semantics across restarts; the empty-board grant probe returns
the same granted=0/already=0 receipt on every instance with
zero phantom awards (the festival certificate stays the only
collectibles row); the honest empty envelope stays
byte-identical across the whole window; and the window is
zero-token end to end.

Usage: python test_honorcert_yearbook_zeroboundarygatepersist.py
"""

import hashlib
import inspect
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402 (P-47-2b core)
import civicpoints as CV              # noqa: E402 (R1752 face)
import collectibles as CL             # noqa: E402 (R619 face)
import honorcert as HC                # noqa: E402 (R1755 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the multi-year honor"
              " yearbook is a platform recognition roster, not"
              " investment advice, and carries no monetary value")
NETWORK_LIBS = ("urllib", "requests", "socket", "http")
CIVIC_TABLES = ("civic_behaviors", "civic_earns", "civic_rewards",
                "civic_redeems", "civic_grants")
ACCOUNTS = ("usr:alice", "usr:bob", "usr:carol", "usr:dave")
ITEM26 = "civic-honor-2026"
FEST_REF = "festival:opening-2026"
FEST_ITEM = "fest-opening-medal"
FAM_ALL = ("2028", "2026", "2025", "2027")
ENV_KEYS = {"years", "yearbooks", "totals", "disclaimer"}
BLOCK_KEYS = {"year", "yearbook", "certified_count", "board_size"}
TOTALS_KEYS = {"years_count", "certified_count", "board_size",
               "distinct_accounts"}
PINNED_BLOCKS = [("2025", [], 0, 0), ("2026", [], 0, 0),
                 ("2027", [], 0, 0), ("2028", [], 0, 0)]
PINNED_TOTALS = {"years_count": 4, "certified_count": 0,
                 "board_size": 0, "distinct_accounts": 0}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def table_counts(led_path, cv_path):
    out = {}
    conn = sqlite3.connect(led_path)
    out["collectibles"] = int(conn.execute(
        "SELECT COUNT(*) FROM collectibles").fetchone()[0])
    out["ledger_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    out["ledger_entries"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_entries").fetchone()[0])
    conn.close()
    cvconn = sqlite3.connect(cv_path)
    for table in CIVIC_TABLES:
        out[table] = int(cvconn.execute(
            "SELECT COUNT(*) FROM " + table).fetchone()[0])
    cvconn.close()
    return out


def build_world(led_path, cv_path, cfg):
    """Zero-earn boundary world (R2027 posture): the ledger and
    collectibles domains hold data - four ensured accounts, two
    registered behaviors, one festival-namespace certificate -
    while the earn axis stays empty for the whole window. The
    boundary isolates the earn axis, not the whole stack."""
    led = L.Ledger(led_path, cfg)
    for acct in ACCOUNTS:
        led.ensure_account(acct, census_avatar_id=acct[4:])
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl = CL.CollectiblesFace(led)
    cv.register_behavior("city-poll", "Community Poll", 5, 20,
                         False)
    cv.register_behavior("street-clean", "Street Cleanup", 2, 20,
                         True)
    cl.issue_certificate("usr:carol", FEST_REF, FEST_ITEM)
    return led, cv, cl


def rebuild(led_path, cv_path, cfg):
    led = L.Ledger(led_path, cfg)
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl = CL.CollectiblesFace(led)
    hc = HC.HonorCertFace(cv, cl, DISCLAIMER)
    return led, cv, cl, hc


class CountingCivic:
    """Read-counting wrapper proving the front-door rejects
    perform zero referenced honor_board calls (R2025 AC-HYCP4
    counting-civic precedent)."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = 0

    def honor_board(self, year):
        self.calls += 1
        return self.inner.honor_board(year)


def expect_hc_error(func, *args):
    try:
        func(*args)
        return None
    except HC.HonorCertError as exc:
        return exc.code


def probe_battery(gate):
    """The 14-probe front-door rejection battery (the R2027
    AC-HYZB2 probe face): nine yearbooks_combined probes and
    five grant_year_honors probes, every one expected to raise
    E_HC_BAD_ARGS before any referenced read lands."""
    return [
        expect_hc_error(gate.yearbooks_combined, 2026),
        expect_hc_error(gate.yearbooks_combined, None),
        expect_hc_error(gate.yearbooks_combined, "2026"),
        expect_hc_error(gate.yearbooks_combined, b"2026"),
        expect_hc_error(gate.yearbooks_combined,
                        ("2026", "2026")),
        expect_hc_error(gate.yearbooks_combined, ("20x6",)),
        expect_hc_error(gate.yearbooks_combined, (2026,)),
        expect_hc_error(gate.yearbooks_combined, (None,)),
        expect_hc_error(gate.yearbooks_combined,
                        ("\uff12\uff10\uff12\uff16",)),
        expect_hc_error(gate.grant_year_honors, "20x6", 2,
                        ITEM26),
        expect_hc_error(gate.grant_year_honors, "2026", True,
                        ITEM26),
        expect_hc_error(gate.grant_year_honors, "2026", 0,
                        ITEM26),
        expect_hc_error(gate.grant_year_honors, "2026", -1,
                        ITEM26),
        expect_hc_error(gate.grant_year_honors, "2026", 2,
                        "   "),
    ]


def run_gate_face(cv, cl):
    """Fresh CountingCivic-wrapped gate + the 14-probe battery +
    the one valid control request. Returns (codes,
    reject_calls, control_calls)."""
    gate = HC.HonorCertFace(CountingCivic(cv), cl, DISCLAIMER)
    codes = probe_battery(gate)
    reject_calls = gate.civic.calls
    gate.yearbooks_combined(("2026",))
    control_calls = gate.civic.calls - reject_calls
    return codes, reject_calls, control_calls


def main():
    tmp = tempfile.mkdtemp(prefix="honorcert-ybgate-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    mod_sha_before = dict(
        (name, sha16(io_read(os.path.join(BASE, name + ".py"))))
        for name in ("honorcert", "civicpoints", "collectibles"))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    led_path = os.path.join(tmp, "ledger.db")
    cv_path = os.path.join(tmp, "civic.db")

    led, cv, cl = build_world(led_path, cv_path, cfg)
    hc = HC.HonorCertFace(cv, cl, DISCLAIMER)
    counts0 = table_counts(led_path, cv_path)

    # -- instance 1: pre-batch double read, battery, grant
    #    probe, post-batch read --------------------------------
    e1a = dump(hc.yearbooks_combined(FAM_ALL))
    r1 = hc.yearbooks_combined(FAM_ALL)
    e1b = dump(r1)
    codes1, rej1, ctl1 = run_gate_face(cv, cl)
    g_empty1 = hc.grant_year_honors("2026", 2, ITEM26)
    e1c = dump(hc.yearbooks_combined(FAM_ALL))
    counts1 = table_counts(led_path, cv_path)

    # -- AC-HYZG1 instance-1 gate vector baseline ------------------
    all_bad1 = all(code == HC.E_HC_BAD_ARGS for code in codes1)
    ok1 = (all_bad1 and rej1 == 0 and ctl1 == 1
           and counts1 == counts0)
    record("AC-HYZG1", ok1, "instance-1 gate vector baseline on"
          " the zero-earn boundary world: %d reject probes (nine"
          " yearbooks_combined faces: non-iterable int/None, bare"
          " str, bytes, duplicate year, bad alpha/int/None/"
          "unicode-digit element years; five grant_year_honors"
          " faces: bad year, bool/zero/negative top_n, blank"
          " item_id) all raise HonorCertError E_HC_BAD_ARGS; the"
          " counting wrapper sees zero honor_board calls across"
          " the whole reject batch (%d) and then exactly %d call"
          " on the one valid control request (per-instance"
          " counter is live); the probe batch leaves every table"
          " count identical (%d counters, rejects carry zero"
          " side effects); the code vector is recorded as the"
          " cross-restart baseline"
          % (len(codes1), rej1, ctl1, len(counts1)))

    # -- restart 1 -> instance 2 -----------------------------------
    cl.close()
    cv.close()
    led.close()
    led2, cv2, cl2, hc2 = rebuild(led_path, cv_path, cfg)
    e2a = dump(hc2.yearbooks_combined(FAM_ALL))
    e2b = dump(hc2.yearbooks_combined(FAM_ALL))
    codes2, rej2, ctl2 = run_gate_face(cv2, cl2)
    g_empty2 = hc2.grant_year_honors("2026", 2, ITEM26)
    e2c = dump(hc2.yearbooks_combined(FAM_ALL))
    counts2 = table_counts(led_path, cv_path)

    # -- AC-HYZG2 instance-2 same-code across the restart -----------
    same2 = codes2 == codes1
    ok2 = (same2 and rej2 == 0 and ctl2 == 1
           and counts2 == counts0)
    record("AC-HYZG2", ok2, "instance-2 same-code law: the"
          " three-piece close (cl -> cv -> led) and same-path"
          " same-config rebuild replay the %d-probe battery with"
          " the IDENTICAL code vector (%s, all E_HC_BAD_ARGS"
          " 14/14); the fresh counting wrapper keeps its"
          " per-instance semantics (%d reject-batch calls, %d"
          " control call - the counter is wrapper-local so each"
          " restart starts honest); the probe batch again leaves"
          " every table count identical"
          % (len(codes2),
             "byte-equal to the instance-1 baseline"
             if same2 else "DRIFTED",
             rej2, ctl2))

    # -- restart 2 -> instance 3 -----------------------------------
    cl2.close()
    cv2.close()
    led2.close()
    led3, cv3, cl3, hc3 = rebuild(led_path, cv_path, cfg)
    e3a = dump(hc3.yearbooks_combined(FAM_ALL))
    e3b = dump(hc3.yearbooks_combined(FAM_ALL))
    codes3, rej3, ctl3 = run_gate_face(cv3, cl3)
    g_empty3 = hc3.grant_year_honors("2026", 2, ITEM26)
    e3c = dump(hc3.yearbooks_combined(FAM_ALL))
    counts3 = table_counts(led_path, cv_path)

    # -- AC-HYZG3 instance-3 same-code across the second restart ---
    same3 = codes3 == codes1 and codes3 == codes2
    ok3 = (same3 and rej3 == 0 and ctl3 == 1
           and counts3 == counts0)
    record("AC-HYZG3", ok3, "instance-3 same-code law (second"
          " restart): the second three-piece close and rebuild"
          " replay the %d-probe battery with the identical code"
          " vector again (%s across all three instances); the"
          " counting wrapper keeps %d/%d semantics; the probe"
          " batch leaves every table count identical - the"
          " front-door gate family carries zero drift across"
          " both full-stack restarts"
          % (len(codes3),
             "byte-equal" if same3 else "DRIFTED",
             rej3, ctl3))

    # -- AC-HYZG4 empty-board grant probe same receipt --------------
    ledconn = sqlite3.connect(led_path)
    honor_rows = int(ledconn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE event_ref ="
        " 'civic-honor:2026'").fetchone()[0])
    fest_rows = int(ledconn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE event_ref = ?",
        (FEST_REF,)).fetchone()[0])
    all_rows = int(ledconn.execute(
        "SELECT COUNT(*) FROM collectibles").fetchone()[0])
    ledconn.close()
    same_grant = all(
        g["granted"] == 0 and g["already"] == 0
        and g["honorees"] == []
        for g in (g_empty1, g_empty2, g_empty3))
    ok4 = (same_grant and honor_rows == 0 and fest_rows == 1
           and all_rows == 1)
    record("AC-HYZG4", ok4, "empty-board grant probe returns the"
          " same receipt on all three instances: each"
          " grant_year_honors(2026, 2, %s) call answers"
          " granted=0/already=0/honorees=[] (%s across"
          " instances); manual SQL cross: civic-honor:2026"
          " certificate rows=%d (zero phantom awards), the"
          " festival certificate stays the only collectibles row"
          " (festival rows=%d, total=%d)"
          % (ITEM26,
             "identical" if same_grant else "DRIFTED",
             honor_rows, fest_rows, all_rows))

    # -- AC-HYZG5 probes never perturb the honest empty envelope ----
    ok_keys = (set(r1.keys()) == ENV_KEYS
               and all(set(b.keys()) == BLOCK_KEYS
                       for b in r1["yearbooks"])
               and set(r1["totals"].keys()) == TOTALS_KEYS)
    ok_vals = (r1["years"] == ["2025", "2026", "2027", "2028"]
               and [(b["year"], b["yearbook"],
                     b["certified_count"], b["board_size"])
                    for b in r1["yearbooks"]] == PINNED_BLOCKS
               and r1["totals"] == PINNED_TOTALS)
    ok_local = (e1a == e1b == e1c and e2a == e2b == e2c
                and e3a == e3b == e3c)
    ok_cross = (e1a == e2a == e3a and e1c == e2c == e3c)
    ok5 = (ok_keys and ok_vals and ok_local and ok_cross)
    record("AC-HYZG5", ok5, "probes never perturb the honest"
          " empty envelope: on every instance the four-year"
          " request form replays byte-identical before the"
          " probe batch, after it, and across the double read"
          " (per-instance %s); the envelope is byte-identical"
          " across all three instances (cross-instance %s); the"
          " pinned values hold - years=[2025..2028] ascending,"
          " every block yearbook==[]/certified_count==0/"
          " board_size==0, totals=%s, key sets exactly the"
          " family contract (sha16=%s)"
          % ("stable" if ok_local else "DRIFTED",
             "stable" if ok_cross else "DRIFTED",
             PINNED_TOTALS, sha16(e1c)))

    # -- AC-HYZG6 pure-read law + zero-token account -----------------
    storm = []
    for _ in range(2):
        storm.append(dump(hc3.yearbooks_combined(FAM_ALL)))
    counts4 = table_counts(led_path, cv_path)
    ok6 = (counts4 == counts0 and counts0["ledger_tx"] == 0
           and counts0["ledger_entries"] == 0
           and storm[0] == e3c and storm[1] == storm[0])
    record("AC-HYZG6", ok6, "pure-read law + zero-token account:"
          " the whole window (three instances x battery x grant"
          " probe x read storm) leaves every table count"
          " identical to the freshly-built world (%d counters"
          " frozen end-to-end) with ledger_tx=%d and"
          " ledger_entries=%d throughout - the ensure, reject,"
          " and certificate axes all bypass the token ledger; the"
          " instance-3 read storm replays the envelope"
          " byte-identical (replay purity)"
          % (len(counts4), counts0["ledger_tx"],
             counts0["ledger_entries"]))

    # -- AC-HYZG7 hygiene + sha proofs + delivery --------------------
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in NETWORK_LIBS)]
    method_srcs = (inspect.getsource(
        HC.HonorCertFace.yearbooks_combined)
        + inspect.getsource(
            HC.HonorCertFace.grant_year_honors))
    write_hits = [t for t in ("INSERT", "UPDATE ", "DELETE")
                  if t in method_srcs]
    sha_ok = all(
        sha16(io_read(os.path.join(BASE, name + ".py"))) == sha_b
        for name, sha_b in mod_sha_before.items())
    tmp_outside = (not os.path.realpath(tmp).startswith(repo_root)
                   and os.path.realpath(tmp).startswith(
                       os.path.realpath(tempfile.gettempdir())))
    prior = len(RESULTS)
    ok7 = (sha16(io_read(cfg_path)) == cfg_sha_before
           and sha_ok and non_ascii == 0 and not net_imports
           and not write_hits and tmp_outside and prior == 6)
    record("AC-HYZG7", ok7, "hygiene: shipped files untouched"
          " (config.json + honorcert/civicpoints/collectibles"
          " sha16 stable=%s); suite source pure ASCII (%d"
          " non-ascii chars), zero network imports (%d hits);"
          " yearbooks_combined AND grant_year_honors method"
          " sources carry zero write statements (hits=%s);"
          " world tmp outside repo (%s); criteria registered=%d"
          % (sha_ok, non_ascii, len(net_imports),
             write_hits or "none",
             "yes" if tmp_outside else "NO", prior + 1))

    cl3.close()
    cv3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
