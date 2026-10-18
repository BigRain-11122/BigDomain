"""Zero-earn boundary world cross-restart window for the
multi-year combined honor yearbook read face (BigDomain R2027;
canon = the explore-queue honorcert zero-earn boundary claim
row, criteria AC-HYZB1..AC-HYZB7 pre-registered in that row
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any
FAIL.

Suite-only round: the shipped yearbooks_combined face is NOT
touched. The window pins the zero-earn boundary semantics the
content-world persist and subset-axis suites left open: a real
product-path world where the ledger and collectibles domains
hold data (four ensured accounts, two registered behaviors, one
unrelated festival-namespace certificate) while the earn axis
is empty (civic_earns zero rows, zero civic-honor certificates)
must return an honest empty combined envelope across the whole
request family, survive a full three-piece stack restart
byte-identical, keep every front-door gate enforcing before any
referenced read, and continue with zero phantom after the
restart's first earn and first grant (the earner joins the
board, the grantee enters the yearbook, the festival
certificate never leaks into a block).

Usage: python test_honorcert_yearbook_zeroboundarypersist.py
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
FAM = (("2028", "2026", "2025", "2027"),
       ("2026",),
       ("2025", "2028"))
ENV_KEYS = {"years", "yearbooks", "totals", "disclaimer"}
BLOCK_KEYS = {"year", "yearbook", "certified_count", "board_size"}
TOTALS_KEYS = {"years_count", "certified_count", "board_size",
               "distinct_accounts"}


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


def block_map(res):
    return dict((b["year"], b) for b in res["yearbooks"])


def build_world(led_path, cv_path, cfg):
    """Zero-earn boundary world (R2010 zero-registration posture):
    the ledger and collectibles domains hold data - four ensured
    accounts, two registered behaviors, one festival-namespace
    certificate - while the earn axis is empty: zero civic_earns
    rows and zero civic-honor certificates. The boundary isolates
    the earn axis, not the whole stack."""
    led = L.Ledger(led_path, cfg)
    for acct in ACCOUNTS:
        led.ensure_account(acct, census_avatar_id=acct[4:])
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl = CL.CollectiblesFace(led)
    cv.register_behavior("city-poll", "Community Poll", 5, 20, False)
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


def main():
    tmp = tempfile.mkdtemp(prefix="honorcert-ybzero-")
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

    # -- AC-HYZB1 zero-earn control anchor --------------------------
    fam_reads = [hc.yearbooks_combined(years) for years in FAM]
    fam_dumps = [dump(res) for res in fam_reads]
    r_all = fam_reads[0]
    bmap = block_map(r_all)
    ok_keys = (set(r_all.keys()) == ENV_KEYS
               and all(set(b.keys()) == BLOCK_KEYS
                       for b in r_all["yearbooks"])
               and set(r_all["totals"].keys()) == TOTALS_KEYS)
    ok_vals = (
        r_all["years"] == ["2025", "2026", "2027", "2028"]
        and [(b["year"], b["yearbook"], b["certified_count"],
              b["board_size"]) for b in r_all["yearbooks"]] == [
            ("2025", [], 0, 0), ("2026", [], 0, 0),
            ("2027", [], 0, 0), ("2028", [], 0, 0)]
        and r_all["totals"] == {"years_count": 4,
                                "certified_count": 0,
                                "board_size": 0,
                                "distinct_accounts": 0}
        and fam_reads[1]["totals"] == {"years_count": 1,
                                       "certified_count": 0,
                                       "board_size": 0,
                                       "distinct_accounts": 0}
        and fam_reads[2]["totals"] == {"years_count": 2,
                                       "certified_count": 0,
                                       "board_size": 0,
                                       "distinct_accounts": 0})
    cnt0 = table_counts(led_path, cv_path)
    ok_fest = (cnt0["collectibles"] == 1
               and all(b["yearbook"] == []
                       for res in fam_reads
                       for b in res["yearbooks"]))
    g_empty = hc.grant_year_honors("2026", 2, ITEM26)
    cnt_after_grant = table_counts(led_path, cv_path)
    ok_grant = (g_empty["granted"] == 0
                and g_empty["already"] == 0
                and g_empty["honorees"] == []
                and cnt_after_grant["collectibles"] == 1)
    fam_replay = [dump(hc.yearbooks_combined(years))
                  for years in FAM]
    ok_double = all(fam_replay[i] == fam_dumps[i]
                    for i in range(len(FAM)))
    ok1 = (ok_keys and ok_vals and ok_fest and ok_grant
           and ok_double)
    record("AC-HYZB1", ok1, "zero-earn boundary control anchor:"
          " all %d request forms return honest empty blocks"
          " (per-block yearbook==[], certified_count==0,"
          " board_size==0; four-year family pinned block values"
          " %s with totals=%s) and the envelope/block/totals key"
          " sets stay exactly the family contract; the"
          " festival-namespace certificate stays in the"
          " collectibles domain (rows=%d) and leaks into zero"
          " blocks (namespace isolation); the empty-board grant"
          " probe returns granted=0/already=0 with zero new"
          " certificate rows (no phantom award); every family"
          " read replays byte-identical (sha16=%s)"
          % (len(FAM),
             [(b["year"], b["yearbook"], b["certified_count"],
               b["board_size"]) for b in r_all["yearbooks"]],
             r_all["totals"], cnt0["collectibles"],
             sha16(fam_dumps[0])))

    # -- AC-HYZB2 gate family before any read -----------------------
    gate = HC.HonorCertFace(CountingCivic(cv), cl, DISCLAIMER)
    rejects = [
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
        expect_hc_error(gate.grant_year_honors, "20x6", 2, ITEM26),
        expect_hc_error(gate.grant_year_honors, "2026", True,
                       ITEM26),
        expect_hc_error(gate.grant_year_honors, "2026", 0, ITEM26),
        expect_hc_error(gate.grant_year_honors, "2026", -1,
                       ITEM26),
        expect_hc_error(gate.grant_year_honors, "2026", 2, "   "),
    ]
    all_rejected = all(code == HC.E_HC_BAD_ARGS
                       for code in rejects)
    zero_calls = gate.civic.calls == 0
    gate.yearbooks_combined(("2026",))
    control_calls = gate.civic.calls == 1
    cnt_gate = table_counts(led_path, cv_path)
    ok2 = (all_rejected and zero_calls and control_calls
           and cnt_gate == cnt_after_grant)
    record("AC-HYZB2", ok2, "front-door gate family enforces"
          " before any read on the empty earn axis: %d reject"
          " probes (non-iterable int/None, bare str, bytes,"
          " duplicate year, bad element years alpha/int/None/"
          "unicode-digits on yearbooks_combined; bad year, bool"
          "/zero/negative top_n, blank item_id on"
          " grant_year_honors) all raise HonorCertError"
          " E_HC_BAD_ARGS with zero referenced honor_board calls"
          " (counter=%d before the positive control, then exactly"
          " %d on the one valid request - the counter is live);"
          " the probe batch leaves every table count identical"
          " (rejects carry zero side effects)"
          % (len(rejects),
             0 if zero_calls else gate.civic.calls,
             gate.civic.calls))

    # -- AC-HYZB3 three-piece stack restart -------------------------
    fam_second = [dump(hc.yearbooks_combined(years))
                  for years in FAM]
    self_stable = all(fam_second[i] == fam_dumps[i]
                      for i in range(len(FAM)))
    cl.close()
    cv.close()
    led.close()
    led2, cv2, cl2, hc2 = rebuild(led_path, cv_path, cfg)
    fam_restarted = [dump(hc2.yearbooks_combined(years))
                     for years in FAM]
    byte_same = all(fam_restarted[i] == fam_dumps[i]
                    for i in range(len(FAM)))
    fam_restart2 = [dump(hc2.yearbooks_combined(years))
                    for years in FAM]
    self_stable2 = all(fam_restart2[i] == fam_restarted[i]
                       for i in range(len(FAM)))
    ok3 = (self_stable and byte_same and self_stable2)
    record("AC-HYZB3", ok3, "three-piece stack restart on the"
          " zero-earn world: pre-close family dumps are"
          " self-stable (%s), the close runs cl -> cv -> led and"
          " the same-path same-config rebuild replays all %d"
          " request forms byte-identical to the pre-close"
          " snapshots (sha16=%s for the four-year form) with the"
          " second read self-stable - the read-time derivation"
          " carries zero in-memory drift across the restart"
          % ("yes" if self_stable else "NO", len(FAM),
             sha16(fam_restarted[0])))

    # -- AC-HYZB4 post-restart first earn continuation ---------------
    cv2.earn_civic("usr:alice", "city-poll", "2026-10-05",
                   "a-poll-1")
    r_live = hc2.yearbooks_combined(FAM[0])
    live_dumps = [dump(hc2.yearbooks_combined(years))
                  for years in FAM]
    bmap_live = block_map(r_live)
    blk26 = bmap_live["2026"]
    frozen = all(dump(bmap_live[y]) == dump(bmap[y])
                 for y in ("2025", "2027", "2028"))
    moved = live_dumps[0] != fam_dumps[0]
    ok_live = (blk26["yearbook"] == []
               and blk26["certified_count"] == 0
               and blk26["board_size"] == 1
               and r_live["totals"] == {"years_count": 4,
                                        "certified_count": 0,
                                        "board_size": 1,
                                        "distinct_accounts": 0})
    cvconn = sqlite3.connect(cv_path)
    earn_rows = int(cvconn.execute(
        "SELECT COUNT(*) FROM civic_earns WHERE at_day LIKE"
        " '2026-%'").fetchone()[0])
    earn_grp = cvconn.execute(
        "SELECT account_id, SUM(points), COUNT(*) FROM"
        " civic_earns WHERE at_day LIKE '2026-%' GROUP BY"
        " account_id").fetchall()
    cvconn.close()
    board = cv2.honor_board("2026")["honor_board"]
    ok_board = (board == [{"rank": 1, "account_id": "usr:alice",
                           "points": 5, "events": 1}]
                and earn_rows == 1
                and earn_grp == [("usr:alice", 5, 1)])
    ok_fest2 = all(b["yearbook"] == []
                   for res in [r_live]
                   for b in res["yearbooks"])
    live_replay = [dump(hc2.yearbooks_combined(years))
                   for years in FAM]
    ok_dbl = all(live_replay[i] == live_dumps[i]
                 for i in range(len(FAM)))
    ok4 = (ok_live and frozen and moved and ok_board
           and ok_fest2 and ok_dbl)
    record("AC-HYZB4", ok4, "post-restart first earn"
          " continuation with zero phantom: the real-path earn on"
          " instance 2 moves the 2026 block to board_size=1"
          " (earner on the board) while yearbook stays [] and"
          " certified_count stays 0 (no certificate, no roster"
          " row - zero phantom), totals=%s; the 2025/2027/2028"
          " blocks stay byte-frozen against the pre-restart"
          " snapshots and the live envelope differs from the"
          " pre-restart empty snapshot (zero-cache liveness);"
          " manual SQL cross: civic_earns 2026-prefix rows=%d"
          " group=%s, honor_board==[(1, usr:alice, 5, 1)]; the"
          " festival certificate still leaks into zero blocks;"
          " family reads replay byte-identical"
          % (r_live["totals"], earn_rows, earn_grp))

    # -- AC-HYZB5 post-restart first grant continuation --------------
    g_first = hc2.grant_year_honors("2026", 2, ITEM26)
    r_cert = hc2.yearbooks_combined(FAM[0])
    cert_dumps = [dump(hc2.yearbooks_combined(years))
                  for years in FAM]
    bmap_cert = block_map(r_cert)
    blk26c = bmap_cert["2026"]
    ok_cert = (g_first["granted"] == 1
               and g_first["already"] == 0
               and g_first["honorees"] == [
                   {"rank": 1, "account_id": "usr:alice",
                    "points": 5, "status": "granted"}]
               and blk26c["yearbook"] == [
                   {"board_rank": 1, "account_id": "usr:alice",
                    "points": 5, "item_id": ITEM26}]
               and blk26c["certified_count"] == 1
               and blk26c["board_size"] == 1
               and r_cert["totals"] == {"years_count": 4,
                                        "certified_count": 1,
                                        "board_size": 1,
                                        "distinct_accounts": 1})
    ledconn = sqlite3.connect(led_path)
    honor_rows = int(ledconn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE event_ref ="
        " 'civic-honor:2026'").fetchone()[0])
    fest_rows = int(ledconn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE event_ref ="
        " ?" , (FEST_REF,)).fetchone()[0])
    ledconn.close()
    g_replay = hc2.grant_year_honors("2026", 2, ITEM26)
    ledconn = sqlite3.connect(led_path)
    honor_rows2 = int(ledconn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE event_ref ="
        " 'civic-honor:2026'").fetchone()[0])
    ledconn.close()
    ok_idem = (g_replay["granted"] == 0
               and g_replay["already"] == 1
               and honor_rows2 == honor_rows)
    ok_fest3 = (fest_rows == 1 and honor_rows == 1
                and all(row["account_id"] != "usr:carol"
                        for b in r_cert["yearbooks"]
                        for row in b["yearbook"]))
    cert_replay = [dump(hc2.yearbooks_combined(years))
                   for years in FAM]
    ok_dbl2 = all(cert_replay[i] == cert_dumps[i]
                  for i in range(len(FAM)))
    ok5 = (ok_cert and ok_idem and ok_fest3 and ok_dbl2)
    record("AC-HYZB5", ok5, "post-restart first grant"
          " continuation with isolation: grant on instance 2"
          " returns granted=1/already=0 and the 2026 block"
          " becomes yearbook=[(1, usr:alice, 5, %s)] with"
          " certified_count=1, board_size=1, totals=%s; manual"
          " SQL cross: civic-honor:2026 certificate rows=%d and"
          " festival certificate rows=%d (the festival holder"
          " usr:carol never enters any block - namespace"
          " isolation survives the restart); the re-grant is"
          " idempotent (granted=0/already=1, zero new rows - the"
          " duplicate law internalizes and a batch interrupted"
          " mid-way heals on re-run); family reads replay"
          " byte-identical"
          % (ITEM26, r_cert["totals"], honor_rows, fest_rows))

    # -- AC-HYZB6 second restart stability + pure-read law ----------
    term_snaps = [dump(hc2.yearbooks_combined(years))
                  for years in FAM]
    before = table_counts(led_path, cv_path)
    storm = []
    for _ in range(2):
        for years in FAM:
            storm.append(dump(hc2.yearbooks_combined(years)))
    after = table_counts(led_path, cv_path)
    cl2.close()
    cv2.close()
    led2.close()
    led3, cv3, cl3, hc3 = rebuild(led_path, cv_path, cfg)
    third = [dump(hc3.yearbooks_combined(years)) for years in FAM]
    third2 = [dump(hc3.yearbooks_combined(years)) for years in FAM]
    ok_third = (all(third[i] == term_snaps[i]
                    for i in range(len(FAM)))
                and all(third2[i] == third[i]
                        for i in range(len(FAM)))
                and all(third[i] == term_snaps[i]
                        for i in range(len(FAM))))
    storm_ok = (before == after
                and before["ledger_tx"] == 0
                and before["ledger_entries"] == 0
                and all(storm[i] == term_snaps[i % len(FAM)]
                        for i in range(len(storm))))
    ok6 = (ok_third and storm_ok)
    record("AC-HYZB6", ok6, "second restart stability +"
          " pure-read law: the instance-2 read storm (two full"
          " family rounds) leaves every table count constant"
          " (%d counters frozen, ledger_tx=%d and"
          " ledger_entries=%d - the whole window is zero-token:"
          " ensure, earn and certificate axes all bypass the"
          " token ledger); closing instance 2 and rebuilding a"
          " third instance on the same paths replays all %d"
          " request forms byte-identical to the terminal state"
          " with repeat reads self-identical (replay purity)"
          % (len(before), before["ledger_tx"],
             before["ledger_entries"], len(FAM)))

    # -- AC-HYZB7 hygiene + sha proofs + delivery --------------------
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in NETWORK_LIBS)]
    method_src = inspect.getsource(
        HC.HonorCertFace.yearbooks_combined)
    write_hits = [t for t in ("INSERT", "UPDATE ", "DELETE")
                  if t in method_src]
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
    record("AC-HYZB7", ok7, "hygiene: shipped files untouched"
          " (config.json + honorcert/civicpoints/collectibles"
          " sha16 stable=%s); suite source pure ASCII (%d"
          " non-ascii chars), zero network imports (%d hits);"
          " yearbooks_combined method source carries zero write"
          " statements (hits=%s); world tmp outside repo (%s);"
          " criteria registered=%d"
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
