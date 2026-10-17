"""Acceptance suite: stats_board month-window cross-restart
persistence example window (BigDomain R2016; canon = explore-queue
statsmonth-persist line, the R2015-reseed consume-1/reseed-1 head).
The month-window face (R2015) slices the per-showcase counts by
the exhibit_events record time (substr(acted_utc,1,7)) with an
honest dense registry axis and gate-before-read discipline. Its
derived purity across a full-stack instance restart had no pinned
example (persist family judgment reference R1889/R1900/R1902; the
R1992 sibling pinned the cap family alone).

Asserts the pre-registered criteria AC-SSMP1..AC-SSMP7 from the
R2016 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law). Claim rulings
(three, registered at claim time):
1. restart carrier = the full stack: ShowcaseFace close ->
   Ledger close, then a fresh Ledger (same db_path, same cfg
   bytes) + stateless SecGate + ShowcaseFace (same sh_path)
   reopen - the ledger dock reconnect is proven too (R1992).
2. world = the R2015 month-window shape (three showcases in
   mixed order, six certificates - five with events plus one
   spare for the post-restart historical fixture; current-month
   real-path churn, previous-month direct-INSERT fixture rows
   per the R1730 law, and a straddle pair) plus a third
   historical month hist = prev - 35d (guaranteed distinct from
   cur and prev).
3. comparison face = the seven-form window read family
   {full, cap2, wcur, wcap2, wprev, whist, wzero} compared by
   dumps(sort_keys=True) byte equality.

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline (the unicode look-alike
probe is written as escape sequences).

Usage: python test_showcase_statsmonthpersist.py
"""

import datetime
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

import ledger as L                     # noqa: E402 (P-47-2b core)
import collectibles as C               # noqa: E402 (owner face)
import showcase as S                   # noqa: E402 (face under test)
from sec_gate import SecGate           # noqa: E402 (lobby product)

EXPECTED = 7
RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the showcase stats"
              " month-window board is a display feature, not"
              " investment advice")

FULL_KEYS = {"showcase_stats_board", "disclaimer"}
CAP_KEYS = {"showcase_stats_board", "disclaimer", "limit", "total",
            "returned", "truncated"}
WIN_KEYS = {"showcase_stats_board", "disclaimer", "window"}
WINCAP_KEYS = CAP_KEYS | {"window"}
ROW_KEYS = {"showcase_id", "title", "ai_label", "places", "retracts",
            "displayed_now"}

PRODUCT_FILES = [
    os.path.join(BASE, "showcase.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def win_family(sh, cur, prev, hist):
    """The seven-form window read family, all serialized."""
    return {
        "full": dumps(sh.stats_board()),
        "cap2": dumps(sh.stats_board(2)),
        "wcur": dumps(sh.stats_board(window=cur)),
        "wcap2": dumps(sh.stats_board(2, cur)),
        "wprev": dumps(sh.stats_board(window=prev)),
        "whist": dumps(sh.stats_board(window=hist)),
        "wzero": dumps(sh.stats_board(window="2099-01")),
    }


def rowmap(board):
    return {r["showcase_id"]: r
            for r in board["showcase_stats_board"]}


def sql_counts_window(sh_path, window):
    uri = "file:" + sh_path.replace("\\", "/") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    counts = {}
    for sid, action, n in conn.execute(
            "SELECT showcase_id, action, COUNT(*) FROM"
            " exhibit_events WHERE substr(acted_utc, 1, 7) = ?"
            " GROUP BY showcase_id, action",
            (window,)).fetchall():
        slot = counts.setdefault(str(sid),
                                 {"place": 0, "retract": 0})
        slot[str(action)] = int(n)
    conn.close()
    return counts


def insert_hist(sh_path, sid, cl, owner, ts):
    """R1730 historical-month fixture law: direct INSERT of a
    fully valid event row with an explicit acted_utc stamp."""
    conn = sqlite3.connect(sh_path)
    conn.execute(
        "INSERT INTO exhibit_events (showcase_id, cl_id, owner_id,"
        " caption, ai_label, action, acted_utc) VALUES"
        " (?, ?, ?, '', 0, 'place', ?)",
        (sid, cl, "usr:" + owner, ts))
    conn.commit()
    conn.close()


def raise_code(fn):
    try:
        fn()
    except S.ShowcaseError as exc:
        return exc.code
    except Exception:                                # noqa: BLE001
        return "WRONG-EXC"
    return "NO-RAISE"


def table_counts(shconn, ledconn):
    return {"showcases": int(shconn.execute(
                "SELECT COUNT(*) FROM showcases").fetchone()[0]),
            "exhibit_events": int(shconn.execute(
                "SELECT COUNT(*) FROM exhibit_events").fetchone()[0]),
            "collectibles": int(ledconn.execute(
                "SELECT COUNT(*) FROM collectibles").fetchone()[0]),
            "ledger_tx": int(ledconn.execute(
                "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])}


def build_world(led, cf, sh, prev_ts):
    for who in ("alice", "bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    cl = {}
    for who, ev, item in (
            ("alice", "evt-tower", "tower-cert"),
            ("bob", "evt-bridge", "bridge-cert"),
            ("carol", "evt-harbor", "harbor-cert"),
            ("alice", "evt-bell", "bell-cert"),
            ("dave", "evt-gate", "gate-cert"),
            ("alice", "evt-moon", "moon-cert")):
        cl[item] = cf.issue_certificate(
            "usr:" + who, ev, item)["cl_id"]
    # registration order deliberately mixed (zeta, mu, alpha) -
    # zero insertion-order keys must survive every windowed order
    sh.register_showcase("zeta-gal", "Zeta Gallery", 3, False)
    sh.register_showcase("mu-gal", "Mu Gallery", 3, True)
    sh.register_showcase("alpha-gal", "Alpha Gallery", 3, False)
    # current-month real-path world (R2015 shape)
    sh.place_exhibit("usr:alice", "alpha-gal", cl["tower-cert"],
                     "", False)
    sh.retract_exhibit("usr:alice", "alpha-gal", cl["tower-cert"])
    sh.place_exhibit("usr:alice", "mu-gal", cl["tower-cert"],
                     "", False)
    sh.place_exhibit("usr:bob", "mu-gal", cl["bridge-cert"],
                     "", False)
    sh.retract_exhibit("usr:bob", "mu-gal", cl["bridge-cert"])
    sh.place_exhibit("usr:bob", "mu-gal", cl["bridge-cert"],
                     "", False)
    sh.place_exhibit("usr:carol", "alpha-gal", cl["harbor-cert"],
                     "", False)
    return cl


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    now = datetime.datetime.now(datetime.timezone.utc)
    cur = now.strftime("%Y-%m")
    prev_dt = now - datetime.timedelta(days=45)
    prev = prev_dt.strftime("%Y-%m")
    prev_ts = prev_dt.strftime("%Y-%m-%dT10:00:00Z")
    hist_dt = prev_dt - datetime.timedelta(days=35)
    hist = hist_dt.strftime("%Y-%m")
    hist_ts = hist_dt.strftime("%Y-%m-%dT08:30:00Z")

    tmp = tempfile.mkdtemp(prefix="showcase-statsmonthpersist-")
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    hyg = {}
    led = sh = led2 = sh2 = led3 = sh3 = None
    shconn = ledconn = None
    try:
        led = L.Ledger(db_path, cfg)
        cf = C.CollectiblesFace(led)
        gate = SecGate.from_config(lobby_cfg)
        sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
        cl = build_world(led, cf, sh, prev_ts)
        # prev-month fixtures + straddle pair (R2015 shape):
        # bell-cert displays in alpha-gal entirely inside the
        # previous month; gate-cert pairs its earlier-month place
        # with a current-month true-path retract
        insert_hist(sh_path, "alpha-gal", cl["bell-cert"],
                    "alice", prev_ts)
        insert_hist(sh_path, "mu-gal", cl["gate-cert"], "dave",
                    prev_ts)
        sh.retract_exhibit("usr:dave", "mu-gal", cl["gate-cert"])
        shconn = sqlite3.connect(sh_path)
        ledconn = sqlite3.connect(db_path)

        # -- AC-SSMP1 pre-close window family control anchor ------
        fam = win_family(sh, cur, prev, hist)
        full_env = json.loads(fam["full"])
        cap_env = json.loads(fam["cap2"])
        wcur = json.loads(fam["wcur"])
        wcap_env = json.loads(fam["wcap2"])
        wprev = json.loads(fam["wprev"])
        whist = json.loads(fam["whist"])
        wzero = json.loads(fam["wzero"])
        ok_env = (set(full_env.keys()) == FULL_KEYS
                  and set(cap_env.keys()) == CAP_KEYS
                  and "window" not in cap_env
                  and set(wcur.keys()) == WIN_KEYS
                  and wcur["window"] == cur
                  and set(wcap_env.keys()) == WINCAP_KEYS
                  and wcap_env["window"] == cur
                  and all(set(r.keys()) == ROW_KEYS
                          for r in wcur["showcase_stats_board"]))
        sql_cur = sql_counts_window(sh_path, cur)
        sql_prev = sql_counts_window(sh_path, prev)
        cross_cur = []
        for sid, row in rowmap(wcur).items():
            slot = sql_cur.get(sid, {"place": 0, "retract": 0})
            cross_cur.append(
                row["places"] == slot["place"]
                and row["retracts"] == slot["retract"]
                and row["displayed_now"]
                == len(sh._displayed_rows_window(sid, cur)))
        cross_prev = []
        for sid, row in rowmap(wprev).items():
            slot = sql_prev.get(sid, {"place": 0, "retract": 0})
            cross_prev.append(
                row["places"] == slot["place"]
                and row["retracts"] == slot["retract"]
                and row["displayed_now"]
                == len(sh._displayed_rows_window(sid, prev)))
        ok_cross = (all(cross_cur) and len(cross_cur) == 3
                    and all(cross_prev) and len(cross_prev) == 3)
        ok_tail = (wcap_env["showcase_stats_board"]
                   == wcur["showcase_stats_board"][-2:]
                   and wcap_env["total"] == 3
                   and wcap_env["returned"] == 2
                   and wcap_env["truncated"] is True)
        fam_double = win_family(sh, cur, prev, hist)
        ok_double = fam == fam_double
        order_code = raise_code(
            lambda: sh.stats_board(limit=-1, window=123))
        record("AC-SSMP1",
               ok_env and ok_cross and ok_tail and ok_double
               and order_code == "E_SH_BAD_LIMIT",
               "seven-form family envelopes pinned (full 2 keys,"
               " cap2 6 keys no window, wcur 3 keys with window"
               " echo, wcap2 7 keys)=%s; wcur/wprev rows all=="
               "independent SQL substr(acted_utc,1,7) recount and"
               " displayed_now==len(_displayed_rows_window) on 3"
               " rows each=%s; capped==windowed decisive tail"
               " slice with honest overflow (total=3 returned=2"
               " truncated=True)=%s; family double-call dumps"
               " byte-identical=%s; gate order probe bad limit +"
               " bad window -> E_SH_BAD_LIMIT fires first=%s"
               % (ok_env, ok_cross, ok_tail, ok_double,
                  order_code == "E_SH_BAD_LIMIT"))

        # -- AC-SSMP2 cross-restart byte identity ------------------
        sh.close()
        led.close()
        sh = led = None
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
        fam2 = win_family(sh2, cur, prev, hist)
        double2 = win_family(sh2, cur, prev, hist) == fam2
        record("AC-SSMP2", fam2 == fam and double2,
               "full-stack close (sh -> led) then rebuild on same"
               " paths + same cfg bytes: seven-form window family"
               " byte-identical=%s same-param double-read"
               " self-stable=%s (derived face zero in-memory drift"
               " across restart)"
               % (fam2 == fam, double2))

        # -- AC-SSMP3 post-restart current-month live recompute ----
        wcur2 = json.loads(fam2["wcur"])
        old_cur_rows = {r["showcase_id"]: dumps(r)
                        for r in wcur2["showcase_stats_board"]}
        sh2.place_exhibit("usr:dave", "zeta-gal",
                          cl["gate-cert"], "", False)
        wcur3 = sh2.stats_board(window=cur)
        zeta_row = rowmap(wcur3)["zeta-gal"]
        frozen_cur = all(
            dumps(rowmap(wcur3)[sid]) == old_cur_rows[sid]
            for sid in ("alpha-gal", "mu-gal"))
        sql_cur3 = sql_counts_window(sh_path, cur)
        zeta_sql = sql_cur3.get("zeta-gal",
                                {"place": 0, "retract": 0})
        fam3 = win_family(sh2, cur, prev, hist)
        frozen_old = (fam3["wprev"] == fam2["wprev"]
                      and fam3["whist"] == fam2["whist"]
                      and fam3["wzero"] == fam2["wzero"])
        record("AC-SSMP3",
               zeta_row["places"] == 1
               and zeta_row["retracts"] == 0
               and zeta_row["displayed_now"] == 1
               and zeta_sql["place"] == 1
               and frozen_cur and frozen_old,
               "post-restart current-month true-path place into"
               " the zero-activity showcase: zeta cur-window row"
               " recomputes zero-cache {places=1, retracts=0,"
               " displayed_now=1}=%s, SQL cross=%s, untouched"
               " alpha/mu cur rows byte-frozen=%s, prev/hist/"
               "2099 window boards byte-frozen=%s"
               % (zeta_row["places"] == 1
                  and zeta_row["displayed_now"] == 1,
                  zeta_sql["place"] == 1, frozen_cur,
                  frozen_old))

        # -- AC-SSMP4 post-restart new-month fixture recompute ------
        wcur_snap4 = dumps(sh2.stats_board(window=cur))
        wprev_snap4 = dumps(sh2.stats_board(window=prev))
        whist4a = sh2.stats_board(window=hist)
        insert_hist(sh_path, "mu-gal", cl["moon-cert"], "alice",
                    hist_ts)
        whist4b = sh2.stats_board(window=hist)
        mu_hist = rowmap(whist4b)["mu-gal"]
        sql_hist4 = sql_counts_window(sh_path, hist).get(
            "mu-gal", {"place": 0, "retract": 0})
        others_frozen = all(
            dumps(rowmap(whist4b)[sid])
            == dumps(rowmap(whist4a)[sid])
            for sid in ("alpha-gal", "zeta-gal"))
        cur_prev_frozen = (
            dumps(sh2.stats_board(window=cur)) == wcur_snap4
            and dumps(sh2.stats_board(window=prev))
            == wprev_snap4
            and dumps(sh2.stats_board(window="2099-01"))
            == fam3["wzero"])
        record("AC-SSMP4",
               rowmap(whist4a)["mu-gal"]["places"] == 0
               and mu_hist["places"] == 1
               and mu_hist["retracts"] == 0
               and mu_hist["displayed_now"] == 1
               and sql_hist4["place"] == 1
               and others_frozen and cur_prev_frozen,
               "post-restart new-month direct-INSERT fixture"
               " (R1730 law): hist-window mu row recomputes 0->1"
               " {places=1, retracts=0, displayed_now=1} by the"
               " record-time law=%s, SQL cross=%s, alpha/zeta"
               " hist rows byte-frozen=%s, cur/prev/2099 window"
               " boards byte-frozen=%s"
               % (mu_hist["places"] == 1
                  and mu_hist["displayed_now"] == 1,
                  sql_hist4["place"] == 1, others_frozen,
                  cur_prev_frozen))

        # -- AC-SSMP5 gate family cross-restart same-code -----------
        bad_forms = [
            ("int", 202610), ("bool", True), ("month-1-digit",
                                              "2026-1"),
            ("month-13", "2026-13"), ("month-00", "2026-00"),
            ("slash-sep", "2026/10"), ("no-sep", "202610"),
            ("trailing-space", "2026-10 "),
            ("unicode-digits",
             "\uff12\uff10\uff12\uff16" + "-" + "\uff11\uff10")]
        counts5a = table_counts(shconn, ledconn)
        codes = [(label, raise_code(
            lambda f=form: sh2.stats_board(window=f)))
            for label, form in bad_forms]
        lim_code1 = raise_code(
            lambda: sh2.stats_board(limit=-1, window=123))
        lim_code2 = raise_code(
            lambda: sh2.stats_board(limit=-1, window=cur))
        counts5b = table_counts(shconn, ledconn)
        ok5 = (all(code == "E_SH_BAD_WINDOW"
                   for _, code in codes)
               and len(codes) == 9
               and lim_code1 == "E_SH_BAD_LIMIT"
               and lim_code2 == "E_SH_BAD_LIMIT"
               and counts5a == counts5b)
        record("AC-SSMP5", ok5,
               "restarted instance rejects all %d malformed"
               " windows with the same E_SH_BAD_WINDOW code"
               " (%s); bad limit + bad window and bad limit +"
               " good window both refuse E_SH_BAD_LIMIT first"
               " (gate order preserved across restart); probe"
               " batch leaves all row counts unchanged %s == %s"
               % (len(codes), [c for c, _ in codes], counts5a,
                  counts5b))

        # -- AC-SSMP6 third instance stability ----------------------
        fam_final = win_family(sh2, cur, prev, hist)
        counts6 = table_counts(shconn, ledconn)
        sh2.close()
        led2.close()
        sh2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_path)
        fam3rd = win_family(sh3, cur, prev, hist)
        seq3rd = win_family(sh3, cur, prev, hist) == fam3rd
        counts6b = table_counts(shconn, ledconn)
        record("AC-SSMP6",
               fam3rd == fam_final and seq3rd
               and counts6 == counts6b,
               "third instance == second-instance final state"
               " byte-identical on all seven forms=%s sequential"
               " double-read self-stable=%s counts flat=%s"
               % (fam3rd == fam_final, seq3rd,
                  counts6 == counts6b))

        # -- AC-SSMP7 pure-read law + hygiene -----------------------
        counts7a = table_counts(shconn, ledconn)
        battery_a = [dumps(sh3.stats_board()),
                     dumps(sh3.stats_board(2)),
                     dumps(sh3.stats_board(window=cur)),
                     dumps(sh3.stats_board(2, cur)),
                     dumps(sh3.stats_board(window=prev)),
                     dumps(sh3.stats_board(window=hist)),
                     dumps(sh3.stats_board(window="2099-01"))]
        battery_b = [dumps(sh3.stats_board()),
                     dumps(sh3.stats_board(2)),
                     dumps(sh3.stats_board(window=cur)),
                     dumps(sh3.stats_board(2, cur)),
                     dumps(sh3.stats_board(window=prev)),
                     dumps(sh3.stats_board(window=hist)),
                     dumps(sh3.stats_board(window="2099-01"))]
        counts7b = table_counts(shconn, ledconn)
        method_src = inspect.getsource(S.ShowcaseFace.stats_board)
        write_hits = [w for w in ("INSERT", "DELETE", "UPDATE ",
                                  "CREATE ", "ALTER ")
                      if w in method_src]
        with open(os.path.abspath(__file__), "rb") as handle:
            own_bytes = handle.read()
        ascii_ok = all(b < 128 for b in own_bytes)
        net_ok = True
        for line in own_bytes.decode("ascii").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or \
                    stripped.startswith("from "):
                if any(w in stripped for w in
                       ("urllib", "requests", "socket", "http")):
                    net_ok = False
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ("ledger-showcase-statsmonth-persist" in reg_src
                  and "test_showcase_statsmonthpersist.py"
                  in reg_src)
        expected_ok = len(RESULTS) == EXPECTED - 1
        outside = tmp not in os.path.abspath(BASE)
        hyg = {"ascii_ok": ascii_ok, "net_ok": net_ok,
               "reg_ok": reg_ok, "expected_ok": expected_ok,
               "outside": outside}
        hyg["pure_ok"] = (counts7a == counts7b
                          and battery_a == battery_b
                          and not write_hits
                          and "random" not in method_src)
        sh3.close()
        led3.close()
        sh3 = led3 = None

    finally:
        for obj in (sh, led, sh2, led2, sh3, led3):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
        if shconn is not None:
            shconn.close()
        if ledconn is not None:
            ledconn.close()

    post_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    sha_ok = pre_sha == post_sha
    record("AC-SSMP7",
           hyg.get("pure_ok") and hyg.get("ascii_ok")
           and hyg.get("net_ok") and hyg.get("reg_ok")
           and hyg.get("expected_ok") and hyg.get("outside")
           and sha_ok,
           "seven-form read battery twice leaves counts unchanged"
           " with repeat pairs byte-identical, stats_board method"
           " source zero write statements zero RNG=%s; suite pure"
           " ASCII=%s net-clean=%s registry-wired=%s"
           " criteria-count=%s world outside repo=%s product-sha"
           " stable=%s (showcase.py + ledger config.json + lobby"
           " config.json)"
           % (hyg.get("pure_ok"), hyg.get("ascii_ok"),
              hyg.get("net_ok"), hyg.get("reg_ok"),
              hyg.get("expected_ok"), hyg.get("outside"),
              sha_ok))

    ok_all = len(RESULTS) == EXPECTED and all(
        ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                              sum(1 for _a, ok in RESULTS if ok),
                              EXPECTED), flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
