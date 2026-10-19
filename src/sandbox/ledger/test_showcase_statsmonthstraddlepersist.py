"""Acceptance suite: stats_board month-window cross-month
STRADDLE-pair net-flow identity exception example window
(BigDomain R2043; canon = the R2021-reseed FIFO head, the
statsmonth family straddle successor). The family register so
far: the month-window face (R2015, AC-SSM) pinned the
record-time slicing laws incl. the straddle honest-read note;
the persist window (R2016, AC-SSMP) pinned the PLACE
live-state persistence; the zero-registration boundary window
(R2017, AC-SSMZ) pinned the empty-world restart family; the
retract window (R2018, AC-SSMR) pinned the retraction-state
persistence; the re-place bounce window (R2019, AC-SSMRP)
pinned the bounced-state persistence; the re-retraction window
(R2021, AC-SSMRR) pinned the cycle-closing state. The remaining
gap = the straddle pair the R2018/R2019 claim rulings kept OUT
of those worlds: an item placed in a PREVIOUS month (fixture
law, R1730 explicit stamp) and retracted through the REAL path
in the CURRENT month. In the current-month window that item's
row reads {places 0, retracts 1, displayed_now 0} and the
month-window net-flow identity displayed_now == places -
retracts does NOT hold (0 != 0 - 1) - the honest exception
this suite pins dead, while the FULL board keeps the identity
per row ({3,1,2}: 2 == 3 - 1) because the full board pairs the
cross-month events the window cannot see. After a restart the
freed slot re-places through the real path and the current
window row becomes {1,1,1} - the leading-retract variant of
the same window exception (1 != 1 - 1) - while the full board
still holds per row ({4,1,3}: 3 == 4 - 1): the identity stays a
full-board law, never a month-window law, in both exception
shapes. The old-month window stays byte-frozen through both
mutations, the view/chronicle/tour faces continue (view_cur
goes [] -> [tower]; chronicle grows [p,p,p,r] -> [p,p,p,r,p];
tour shrinks then re-joins at the tail), and both live states
persist byte-identically across two full-stack restarts.

World shape (registered in the R2043 claim line): alpha-gal =
three previous-month fixture places + the straddle retraction
(the exception showcase); beta-gal = two current-month
real-path places (the place-first contrast where every window
identity keeps holding - exception specificity); mu-gal = the
zero-event honest-zero row riding every board form.

Asserts the pre-registered criteria AC-SMST1..AC-SMST7 from
the R2043 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law).

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline. The double-run stdout
byte-identity face is carried by the external evidence harness
(the R1880 family law).

Usage: python test_showcase_statsmonthstraddlepersist.py
"""

import datetime
import hashlib
import inspect
import json
import os
import shutil
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
CAP_KEYS = {"showcase_stats_board", "disclaimer", "limit",
            "total", "returned", "truncated"}
WIN_KEYS = {"showcase_stats_board", "disclaimer", "window"}
WINCAP_KEYS = CAP_KEYS | {"window"}

PRODUCT_FILES = [
    os.path.join(BASE, "showcase.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

BAD_WINDOWS = ["2026-13", "2026-00", "26-10", "2026-1",
               " 2026-10", "2026-10 ", "", 2026, "2026-10-01"]
BAD_LIMITS = [-1, "2", 1.5, True]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def insert_hist(sh_path, sid, cl_id, owner, ts):
    """R1730 historical-month fixture law: direct INSERT of a
    fully valid event row with an explicit acted_utc stamp."""
    conn = sqlite3.connect(sh_path)
    conn.execute(
        "INSERT INTO exhibit_events (showcase_id, cl_id, owner_id,"
        " caption, ai_label, action, acted_utc) VALUES"
        " (?, ?, ?, '', 0, 'place', ?)",
        (sid, cl_id, "usr:" + owner, ts))
    conn.commit()
    conn.close()


def form_family(sh, prev, cur, hist):
    """The thirteen-form read family, all serialized: the seven
    board forms (full / cap2 / current / cap2-current /
    previous / deep-history / far-future windows) plus the two
    windowed display views of the straddle showcase, the beta
    current-window view, the two per-showcase chronicle walks
    and the all-time tour."""
    fam = {
        "full": dumps(sh.stats_board()),
        "cap2": dumps(sh.stats_board(2)),
        "wcur": dumps(sh.stats_board(window=cur)),
        "wcap2": dumps(sh.stats_board(2, cur)),
        "wprev": dumps(sh.stats_board(window=prev)),
        "whist": dumps(sh.stats_board(window=hist)),
        "wzero": dumps(sh.stats_board(window="2099-01")),
        "view_prev": dumps(sh.showcase_view_window(
            "alpha-gal", prev)),
        "view_cur": dumps(sh.showcase_view_window(
            "alpha-gal", cur)),
        "view_cur_beta": dumps(sh.showcase_view_window(
            "beta-gal", cur)),
        "chron": dumps(sh.chronicle("alpha-gal")),
        "chron_beta": dumps(sh.chronicle("beta-gal")),
        "tour": dumps(sh.chronicle_tour("alpha-gal")),
    }
    return fam


def rowmap(board_text):
    return {r["showcase_id"]: r for r in json.loads(board_text)
            ["showcase_stats_board"]}


def identity_ok(rows):
    """Net-flow identity per row: displayed_now == places -
    retracts. The shipped per-row law of the FULL board; used
    here only on boards where the claim says it must hold."""
    for r in rows:
        if int(r["displayed_now"]) != (int(r["places"])
                                       - int(r["retracts"])):
            return False
    return bool(rows)


def broken_rows(board_text):
    """The honest-exception detector: the showcase ids whose
    window row breaks the net-flow identity (straddle row)."""
    out = []
    for r in json.loads(board_text)["showcase_stats_board"]:
        if int(r["displayed_now"]) != (int(r["places"])
                                        - int(r["retracts"])):
            out.append(r["showcase_id"])
    return out


def triple(row):
    return (int(row["places"]), int(row["retracts"]),
            int(row["displayed_now"]))


def view_cls(view_text):
    return [int(d["cl_id"]) for d in json.loads(view_text)
            ["displayed"]]


def chronicle_actions(chron_text):
    return [e["action"] for e in json.loads(chron_text)["events"]]


def tour_cls(tour_text):
    return [int(s["cl_id"]) for s in json.loads(tour_text)
            ["stops"]]


def db_counts(sh_path, led_path):
    c1 = sqlite3.connect(sh_path)
    out = {"showcases": int(c1.execute(
               "SELECT COUNT(*) FROM showcases").fetchone()[0]),
           "exhibit_events": int(c1.execute(
               "SELECT COUNT(*) FROM exhibit_events").fetchone()[0])}
    c1.close()
    c2 = sqlite3.connect(led_path)
    out["ledger_tx"] = int(c2.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    c2.close()
    return out


def gate_codes(sh):
    codes = []
    for bad in BAD_WINDOWS:
        codes.append(raise_code(
            lambda b=bad: sh.stats_board(window=b)))
    for bad in BAD_LIMITS:
        codes.append(raise_code(
            lambda b=bad: sh.stats_board(b)))
    codes.append(raise_code(
        lambda: sh.stats_board(-1, "2026-13")))
    return codes


def raise_code(fn):
    try:
        fn()
    except S.ShowcaseError as exc:
        return exc.code
    except Exception:                                # noqa: BLE001
        return "WRONG-EXC"
    return "NO-RAISE"


def build_world(led, cf, sh_path, sh, prev_ts, cl):
    for who in ("alice", "bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    for who, ev, item in (
            ("alice", "evt-tower", "tower-cert"),
            ("bob", "evt-bridge", "bridge-cert"),
            ("carol", "evt-harbor", "harbor-cert"),
            ("dave", "evt-gate", "gate-cert"),
            ("alice", "evt-moon", "moon-cert")):
        cl[item] = cf.issue_certificate(
            "usr:" + who, ev, item)["cl_id"]
    # straddle showcase first, place-first contrast second,
    # zero-event showcase last (the honest-zero row rides
    # every board form)
    sh.register_showcase("alpha-gal", "Alpha Gallery", 6, False)
    sh.register_showcase("beta-gal", "Beta Gallery", 3, True)
    sh.register_showcase("mu-gal", "Mu Gallery", 3, True)
    # previous-month places in the straddle showcase: the
    # R1730 fixture law (explicit stamps, fully valid rows)
    for item, owner in (("tower-cert", "alice"),
                        ("bridge-cert", "bob"),
                        ("harbor-cert", "carol")):
        insert_hist(sh_path, "alpha-gal", cl[item], owner, prev_ts)
    # current-month real-path places in the contrast showcase
    sh.place_exhibit("usr:dave", "beta-gal", cl["gate-cert"],
                     "", False)
    sh.place_exhibit("usr:alice", "beta-gal", cl["moon-cert"],
                     "", False)


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

    tmp = tempfile.mkdtemp(prefix="showcase-statsmonthstraddle-")
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    outside = not os.path.normcase(os.path.abspath(tmp)).startswith(
        os.path.normcase(os.path.normpath(
            os.path.join(BASE, "..", "..", ".."))))
    led = sh = led2 = sh2 = led3 = sh3 = None
    try:
        led = L.Ledger(db_path, cfg)
        cf = C.CollectiblesFace(led)
        gate = SecGate.from_config(lobby_cfg)
        sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
        cl = {}
        build_world(led, cf, sh_path, sh, prev_ts, cl)

        # -- AC-SMST1 pre-straddle place-first anchors ------------
        fam1 = form_family(sh, prev, cur, hist)
        full1 = rowmap(fam1["full"])
        wcur1 = rowmap(fam1["wcur"])
        wprev1 = rowmap(fam1["wprev"])
        wzero1 = rowmap(fam1["wzero"])
        whist1 = rowmap(fam1["whist"])
        ok = (json.loads(fam1["full"]).keys() == FULL_KEYS
              and json.loads(fam1["cap2"]).keys() == CAP_KEYS
              and json.loads(fam1["wcur"]).keys() == WIN_KEYS
              and json.loads(fam1["wcap2"]).keys() == WINCAP_KEYS
              and triple(full1["alpha-gal"]) == (3, 0, 3)
              and triple(full1["beta-gal"]) == (2, 0, 2)
              and triple(full1["mu-gal"]) == (0, 0, 0)
              and identity_ok(list(full1.values()))
              and triple(wcur1["alpha-gal"]) == (0, 0, 0)
              and triple(wcur1["beta-gal"]) == (2, 0, 2)
              and identity_ok(list(wcur1.values()))
              and triple(wprev1["alpha-gal"]) == (3, 0, 3)
              and identity_ok(list(wprev1.values()))
              and identity_ok(list(whist1.values()))
              and identity_ok(list(wzero1.values()))
              and broken_rows(fam1["wcur"]) == []
              and view_cls(fam1["view_prev"]) == [
                  cl["tower-cert"], cl["bridge-cert"],
                  cl["harbor-cert"]]
              and view_cls(fam1["view_cur"]) == []
              and view_cls(fam1["view_cur_beta"]) == [
                  cl["gate-cert"], cl["moon-cert"]]
              and chronicle_actions(fam1["chron"]) == [
                  "place"] * 3
              and chronicle_actions(fam1["chron_beta"]) == [
                  "place"] * 2
              and tour_cls(fam1["tour"]) == [
                  cl["tower-cert"], cl["bridge-cert"],
                  cl["harbor-cert"]])
        record("AC-SMST1", ok,
               "place-first world anchors: full alpha"
               " {3,0,3} beta {2,0,2} mu {0,0,0} identity=%s;"
               " wcur alpha {0,0,0} beta {2,0,2} identity=%s"
               " zero-broken-rows; wprev {3,0,3}; view_prev=%s;"
               " view_cur alpha=%s beta=%s; chronicle 3xplace+"
               "2xplace; tour 3 stops; far/deep windows all-zero"
               " identity=%s/%s"
               % (identity_ok(list(full1.values())),
                  identity_ok(list(wcur1.values())),
                  view_cls(fam1["view_prev"]),
                  view_cls(fam1["view_cur"]),
                  view_cls(fam1["view_cur_beta"]),
                  identity_ok(list(whist1.values())),
                  identity_ok(list(wzero1.values()))))
        codes_pre = gate_codes(sh)

        # -- AC-SMST2 the straddle retraction: the exception ------
        counts_pre = db_counts(sh_path, db_path)
        sh.retract_exhibit("usr:alice", "alpha-gal",
                           cl["tower-cert"])
        counts_post = db_counts(sh_path, db_path)
        fam2 = form_family(sh, prev, cur, hist)
        full2 = rowmap(fam2["full"])
        wcur2 = rowmap(fam2["wcur"])
        straddle_row = wcur2["alpha-gal"]
        exception = (int(straddle_row["displayed_now"])
                     != int(straddle_row["places"])
                     - int(straddle_row["retracts"]))
        ok = (counts_pre["exhibit_events"] == 5
              and counts_post["exhibit_events"] == 6
              and counts_pre["ledger_tx"]
              == counts_post["ledger_tx"] == 0
              and triple(straddle_row) == (0, 1, 0)
              and exception
              and broken_rows(fam2["wcur"]) == ["alpha-gal"]
              and triple(full2["alpha-gal"]) == (3, 1, 2)
              and identity_ok(list(full2.values()))
              and triple(wcur2["beta-gal"]) == (2, 0, 2)
              and identity_ok([wcur2["beta-gal"],
                               wcur2["mu-gal"]])
              and fam2["wprev"] == fam1["wprev"]
              and fam2["view_prev"] == fam1["view_prev"]
              and view_cls(fam2["view_cur"]) == []
              and chronicle_actions(fam2["chron"]) == [
                  "place"] * 3 + ["retract"]
              and tour_cls(fam2["tour"]) == [
                  cl["bridge-cert"], cl["harbor-cert"]])
        record("AC-SMST2", ok,
               "straddle core: prev-place tower real-path"
               " retracted; wcur alpha row {0,1,0}"
               " identity-BROKEN=%s (0 != 0-1 honest exception"
               " pinned); broken rows=%s (straddle-specific);"
               " full alpha {3,1,2} identity=%s (2==3-1 full-"
               "board law held); beta/mu wcur identity=%s; wprev"
               " byte-frozen=%s; view_prev frozen=%s; view_cur"
               " alpha=%s; chronicle 3xplace+retract; tour=%s"
               " (tower leaves); events 5->%d; ledger_tx=%d"
               % (exception,
                  broken_rows(fam2["wcur"]),
                  identity_ok(list(full2.values())),
                  identity_ok([wcur2["beta-gal"],
                               wcur2["mu-gal"]]),
                  fam2["wprev"] == fam1["wprev"],
                  fam2["view_prev"] == fam1["view_prev"],
                  view_cls(fam2["view_cur"]),
                  tour_cls(fam2["tour"]),
                  counts_post["exhibit_events"],
                  counts_post["ledger_tx"]))

        # -- AC-SMST3 first full-stack restart persistence -------
        sh.close()
        led.close()
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
        fam3 = form_family(sh2, prev, cur, hist)
        diff = [k for k in fam2 if fam2[k] != fam3[k]]
        record("AC-SMST3", not diff,
               "restart #1 (same db/cfg/sh paths, fresh Ledger +"
               " stateless SecGate): 13/13 forms byte-identical"
               " vs the straddle snapshots (the exception row"
               " {0,1,0} persists) drift=%s" % diff)

        # -- AC-SMST4 post-restart re-place: the leading-retract
        #    variant of the same window exception ---------------
        probe_code = raise_code(
            lambda: sh2.place_exhibit("usr:bob", "alpha-gal",
                                      cl["bridge-cert"], "", False))
        probe_counts = db_counts(sh_path, db_path)
        sh2.place_exhibit("usr:alice", "alpha-gal",
                          cl["tower-cert"], "", False)
        after_counts = db_counts(sh_path, db_path)
        fam4 = form_family(sh2, prev, cur, hist)
        full4 = rowmap(fam4["full"])
        wcur4 = rowmap(fam4["wcur"])
        variant_row = wcur4["alpha-gal"]
        variant_break = (int(variant_row["displayed_now"])
                         != int(variant_row["places"])
                         - int(variant_row["retracts"]))
        ok = (probe_code == S.E_SH_ALREADY_DISPLAYED
              and probe_counts["exhibit_events"] == 6
              and after_counts["exhibit_events"] == 7
              and triple(variant_row) == (1, 1, 1)
              and variant_break
              and broken_rows(fam4["wcur"]) == ["alpha-gal"]
              and triple(full4["alpha-gal"]) == (4, 1, 3)
              and identity_ok(list(full4.values()))
              and fam4["wprev"] == fam2["wprev"]
              and fam4["view_prev"] == fam2["view_prev"]
              and view_cls(fam4["view_cur"]) == [cl["tower-cert"]]
              and chronicle_actions(fam4["chron"]) == [
                  "place"] * 3 + ["retract", "place"]
              and tour_cls(fam4["tour"]) == [
                  cl["bridge-cert"], cl["harbor-cert"],
                  cl["tower-cert"]])
        record("AC-SMST4", ok,
               "re-place closing the straddle: already-"
               "displayed probe=%s zero-rows=%s; wcur alpha row"
               " {1,1,1} identity-BROKEN=%s (1 != 1-1 the"
               " leading-retract variant of the same window"
               " exception); broken rows=%s; full alpha {4,1,3}"
               " identity=%s (3==4-1 full-board law held);"
               " wprev byte-frozen=%s; view_prev frozen=%s;"
               " view_cur alpha=%s (tower returns); chronicle"
               " 3xplace+retract+place; tour=%s (tail re-joins,"
               " R2019 law); events 6->%d"
               % (probe_code == S.E_SH_ALREADY_DISPLAYED,
                  probe_counts["exhibit_events"] == 4,
                  variant_break,
                  broken_rows(fam4["wcur"]),
                  identity_ok(list(full4.values())),
                  fam4["wprev"] == fam2["wprev"],
                  fam4["view_prev"] == fam2["view_prev"],
                  view_cls(fam4["view_cur"]),
                  tour_cls(fam4["tour"]),
                  after_counts["exhibit_events"]))

        # -- AC-SMST5 second full-stack restart: the closed
        #    straddle state persists -------------------------------
        sh2.close()
        led2.close()
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_path)
        fam5 = form_family(sh3, prev, cur, hist)
        diff5 = [k for k in fam4 if fam4[k] != fam5[k]]
        counts_a = db_counts(sh_path, db_path)
        fam5a = form_family(sh3, prev, cur, hist)
        fam5b = form_family(sh3, prev, cur, hist)
        counts_b = db_counts(sh_path, db_path)
        src = inspect.getsource(S.ShowcaseFace.stats_board)
        pure_src = ("INSERT" not in src and "UPDATE" not in src
                    and "DELETE" not in src)

        codes_post = gate_codes(sh3)
        win_codes = codes_post[:len(BAD_WINDOWS)]
        lim_codes = codes_post[len(BAD_WINDOWS):
                              len(BAD_WINDOWS) + len(BAD_LIMITS)]
        order_code = codes_post[-1]
        gates_ok = (codes_pre == codes_post
                    and all(c == S.E_SH_BAD_WINDOW
                            for c in win_codes)
                    and all(c == S.E_SH_BAD_LIMIT
                            for c in lim_codes)
                    and order_code == S.E_SH_BAD_LIMIT)
        record("AC-SMST5",
               not diff5
               and counts_a == counts_b
               and counts_a["showcases"] == 3
               and counts_a["exhibit_events"] == 7
               and counts_a["ledger_tx"] == 0
               and fam5a == fam5b == fam5 and pure_src
               and gates_ok,
               "restart #2 (third instance): 13/13 forms"
               " byte-identical vs the closed-straddle snapshots"
               " drift=%s (the {1,1,1} variant state persists);"
               " read storm x2: counts stable=%s"
               " (showcases=%d, events=%d, ledger_tx=%d), both"
               " passes byte-identical=%s; stats_board source"
               " zero writes=%s; gate family identical"
               " pre/post restart=%s; %d bad windows ->"
               " E_SH_BAD_WINDOW=%s; %d bad limits ->"
               " E_SH_BAD_LIMIT=%s; limit-gate-first order"
               " probe=%s"
               % (diff5,
                  counts_a == counts_b,
                  counts_a["showcases"],
                  counts_a["exhibit_events"],
                  counts_a["ledger_tx"],
                  fam5a == fam5b == fam5, pure_src,
                  codes_pre == codes_post, len(BAD_WINDOWS),
                  all(c == S.E_SH_BAD_WINDOW for c in win_codes),
                  len(BAD_LIMITS),
                  all(c == S.E_SH_BAD_LIMIT for c in lim_codes),
                  order_code))

        # -- AC-SMST6 pure-read law + zero-token + honest
        #    zero windows + cross-showcase gate probe --------------
        cross_code = raise_code(
            lambda: sh3.retract_exhibit("usr:dave", "alpha-gal",
                                        cl["gate-cert"]))
        cross_counts = db_counts(sh_path, db_path)
        wzero5 = rowmap(fam5["wzero"])
        whist5 = rowmap(fam5["whist"])
        ok = (cross_code == S.E_SH_NOT_DISPLAYED
              and cross_counts == counts_a
              and cross_counts["ledger_tx"] == 0
              and identity_ok(list(wzero5.values()))
              and identity_ok(list(whist5.values()))
              and triple(wzero5["alpha-gal"]) == (0, 0, 0)
              and triple(whist5["alpha-gal"]) == (0, 0, 0)
              and triple(rowmap(fam5["full"])["mu-gal"])
              == (0, 0, 0)
              and triple(rowmap(fam5["wcur"])["mu-gal"])
              == (0, 0, 0)
              and identity_ok([rowmap(fam5["wcur"])["mu-gal"]]))
        record("AC-SMST6", ok,
               "pure-read law: cross-showcase not-displayed"
               " probe=%s (beta-displayed item refuses under"
               " alpha, zero rows, counts stable=%s);"
               " ledger_tx=%d across the whole suite (zero-"
               "token law); far window 2099-01 all-zero rows"
               " identity=%s (0==0-0 trivially); deep-history"
               " window all-zero identity=%s; mu-gal zero-event"
               " row holds in every form identity=%s"
               % (cross_code == S.E_SH_NOT_DISPLAYED,
                  cross_counts == counts_a,
                  cross_counts["ledger_tx"],
                  identity_ok(list(wzero5.values())),
                  identity_ok(list(whist5.values())),
                  identity_ok([rowmap(fam5["wcur"])["mu-gal"]])))

        # -- AC-SMST7 hygiene -------------------------------------
        post_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
        with open(os.path.abspath(__file__), "rb") as handle:
            own = handle.read()
        ascii_ok = all(b < 128 for b in own)
        net_tokens = ("soc" + "ket", "url" + "lib",
                      "htt" + "px", "reque" + "sts")
        net_ok = not any(t in own.decode("ascii", "ignore")
                         for t in net_tokens)
        sha_ok = post_sha == pre_sha
        record("AC-SMST7",
               sha_ok and ascii_ok and net_ok and outside
               and EXPECTED == 7,
               "product sha stable=%s (showcase.py + both"
               " config.json); suite pure ASCII=%s; zero network"
               " imports=%s; world outside repo=%s; criteria"
               "== 7=%s; double-run face carried by the"
               " evidence harness"
               % (sha_ok, ascii_ok, net_ok, outside,
                  EXPECTED == 7))

    finally:
        for face in (sh, sh2, sh3):
            if face is not None:
                try:
                    face.close()
                except Exception:                    # noqa: BLE001
                    pass
        for core in (led, led2, led3):
            if core is not None:
                try:
                    core.close()
                except Exception:                    # noqa: BLE001
                    pass
        shutil.rmtree(tmp, ignore_errors=True)

    ok_all = len(RESULTS) == EXPECTED and all(
        ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                              sum(1 for _a, ok in RESULTS if ok),
                              EXPECTED), flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
