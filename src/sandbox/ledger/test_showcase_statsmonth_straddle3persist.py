"""Acceptance suite: stats_board month-window post-closure
retract THIRD-shape exception window (BigDomain R2071; canon =
the R2070-successor explore-queue FIFO head, the statsmonth
family straddle successor after the R2044 double-straddle
closure). Family register: the month-window slicing laws
(R2015 AC-SSM); the live-state and cycle persistence windows
R2016..R2021; the single-straddle exception pair (R2043
AC-SMST, shapes {0,1,0} and {1,1,1}); the double-straddle
deepening (R2044 AC-SMDS, shapes {0,2,0} -> {1,2,1} ->
{2,2,2} with the full board holding {3,2,1}/{4,2,2}/{5,2,3}).
This suite grows the ladder by the POST-CLOSURE RETRACT shape:
from the closed-yet-still-broken terminal window {2,2,2}, ONE
current-month re-placed exhibit is retracted again through the
real path and the current-month window reads {2,3,1} - the
third shape of the exception, where the identity breaks with a
NEGATIVE right-hand side (1 != 2 - 3 = -1). The full board
keeps the identity at this step too ({5,3,2}: 2 == 5 - 3), and
one more re-place bounces the window to {3,3,2} (2 != 3 - 3),
the fourth shape pinned honestly in passing. The old-month
window stays byte-frozen, the view/chronicle/tour faces follow
the retract-and-return order, and every live state persists
byte-identically across two full-stack restarts.

World shape (registered in the R2071 claim line): alpha-gal =
three previous-month fixture places + the double straddle +
closure + post-closure retract + bounce (the exception
showcase); beta-gal = two current-month real-path places (the
place-first contrast whose window identity always holds);
mu-gal = the zero-event honest-zero row riding every form.

Asserts the pre-registered criteria AC-SMTR1..AC-SMTR7 from the
R2071 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law).

Suite-only round: zero product bytes change. Pure ASCII source
per the encoding discipline. The double-run stdout byte-identity
face is carried by the external evidence harness.

Usage: python test_showcase_statsmonth_straddle3persist.py
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
    """The thirteen-form read family, all serialized: seven board
    forms plus the two windowed display views of the straddle
    showcase, the beta current-window view, the two per-showcase
    chronicle walks and the all-time tour."""
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
    retracts. The shipped per-row law of the FULL board."""
    for r in rows:
        if int(r["displayed_now"]) != (int(r["places"])
                                       - int(r["retracts"])):
            return False
    return bool(rows)


def broken_rows(board_text):
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


def raise_code(fn):
    try:
        fn()
    except S.ShowcaseError as exc:
        return exc.code
    except Exception:                                # noqa: BLE001
        return "WRONG-EXC"
    return "NO-RAISE"


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
    sh.register_showcase("alpha-gal", "Alpha Gallery", 6, False)
    sh.register_showcase("beta-gal", "Beta Gallery", 3, True)
    sh.register_showcase("mu-gal", "Mu Gallery", 3, True)
    for item, owner in (("tower-cert", "alice"),
                        ("bridge-cert", "bob"),
                        ("harbor-cert", "carol")):
        insert_hist(sh_path, "alpha-gal", cl[item], owner, prev_ts)
    sh.place_exhibit("usr:dave", "beta-gal", cl["gate-cert"],
                     "", False)
    sh.place_exhibit("usr:alice", "beta-gal", cl["moon-cert"],
                     "", False)


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read())

    now = datetime.datetime.now(datetime.timezone.utc)
    cur = now.strftime("%Y-%m")
    prev_dt = now - datetime.timedelta(days=45)
    prev = prev_dt.strftime("%Y-%m")
    prev_ts = prev_dt.strftime("%Y-%m-%dT10:00:00Z")
    hist_dt = prev_dt - datetime.timedelta(days=35)
    hist = hist_dt.strftime("%Y-%m")

    tmp = tempfile.mkdtemp(prefix="showcase-statsmonthstraddle3-")
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
        codes_pre = gate_codes(sh)

        # -- AC-SMTR1 the ladder base: place-first anchors and
        #    the double-straddle shape -------------------------
        fam1 = form_family(sh, prev, cur, hist)
        full1 = rowmap(fam1["full"])
        wcur1 = rowmap(fam1["wcur"])
        wprev1 = rowmap(fam1["wprev"])
        base_ok = (json.loads(fam1["full"]).keys() == FULL_KEYS
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
                   and broken_rows(fam1["wcur"]) == []
                   and view_cls(fam1["view_prev"]) == [
                       cl["tower-cert"], cl["bridge-cert"],
                       cl["harbor-cert"]]
                   and view_cls(fam1["view_cur"]) == []
                   and view_cls(fam1["view_cur_beta"]) == [
                       cl["gate-cert"], cl["moon-cert"]]
                   and chronicle_actions(fam1["chron"]) == [
                       "place"] * 3
                   and tour_cls(fam1["tour"]) == [
                       cl["tower-cert"], cl["bridge-cert"],
                       cl["harbor-cert"]])
        counts1 = db_counts(sh_path, db_path)
        sh.retract_exhibit("usr:alice", "alpha-gal",
                           cl["tower-cert"])
        sh.retract_exhibit("usr:bob", "alpha-gal",
                           cl["bridge-cert"])
        counts2 = db_counts(sh_path, db_path)
        fam2 = form_family(sh, prev, cur, hist)
        full2 = rowmap(fam2["full"])
        wcur2 = rowmap(fam2["wcur"])
        straddle_break = (int(wcur2["alpha-gal"]["displayed_now"])
                          != int(wcur2["alpha-gal"]["places"])
                          - int(wcur2["alpha-gal"]["retracts"]))
        ok = (base_ok
              and counts1["exhibit_events"] == 5
              and counts2["exhibit_events"] == 7
              and counts1["ledger_tx"] == counts2["ledger_tx"] == 0
              and triple(wcur2["alpha-gal"]) == (0, 2, 0)
              and straddle_break
              and broken_rows(fam2["wcur"]) == ["alpha-gal"]
              and triple(full2["alpha-gal"]) == (3, 2, 1)
              and identity_ok(list(full2.values()))
              and identity_ok([wcur2["beta-gal"], wcur2["mu-gal"]])
              and fam2["wprev"] == fam1["wprev"]
              and fam2["view_prev"] == fam1["view_prev"]
              and view_cls(fam2["view_cur"]) == []
              and chronicle_actions(fam2["chron"]) == [
                  "place"] * 3 + ["retract"] * 2
              and tour_cls(fam2["tour"]) == [cl["harbor-cert"]])
        record("AC-SMTR1", ok,
               "ladder base: place-first anchors full alpha"
               " {3,0,3} beta {2,0,2} mu {0,0,0} identity=%s;"
               " wcur alpha {0,0,0} identity=%s zero-broken;"
               " double straddle -> wcur alpha {0,2,0}"
               " identity-BROKEN=%s broken=%s; full alpha"
               " {3,2,1} identity=%s (1==3-2); beta/mu wcur"
               " identity=%s; wprev view frozen=%s/%s;"
               " chronicle 3xplace+2xretract; tour=%s;"
               " events 5->%d; ledger_tx=%d"
               % (identity_ok(list(full1.values())),
                  identity_ok(list(wcur1.values())),
                  straddle_break, broken_rows(fam2["wcur"]),
                  identity_ok(list(full2.values())),
                  identity_ok([wcur2["beta-gal"], wcur2["mu-gal"]]),
                  fam2["wprev"] == fam1["wprev"],
                  fam2["view_prev"] == fam1["view_prev"],
                  tour_cls(fam2["tour"]),
                  counts2["exhibit_events"],
                  counts2["ledger_tx"]))

        # -- AC-SMTR2 the closure state: both cross-month -------
        #    pairs re-placed, window still broken ----------------
        sh.place_exhibit("usr:alice", "alpha-gal",
                         cl["tower-cert"], "", False)
        sh.place_exhibit("usr:bob", "alpha-gal",
                         cl["bridge-cert"], "", False)
        counts3 = db_counts(sh_path, db_path)
        fam3 = form_family(sh, prev, cur, hist)
        full3 = rowmap(fam3["full"])
        wcur3 = rowmap(fam3["wcur"])
        closed_break = (int(wcur3["alpha-gal"]["displayed_now"])
                        != int(wcur3["alpha-gal"]["places"])
                        - int(wcur3["alpha-gal"]["retracts"]))
        ok = (counts3["exhibit_events"] == 9
              and counts3["ledger_tx"] == 0
              and triple(wcur3["alpha-gal"]) == (2, 2, 2)
              and closed_break
              and broken_rows(fam3["wcur"]) == ["alpha-gal"]
              and triple(full3["alpha-gal"]) == (5, 2, 3)
              and identity_ok(list(full3.values()))
              and identity_ok([wcur3["beta-gal"], wcur3["mu-gal"]])
              and view_cls(fam3["view_cur"]) == [
                  cl["tower-cert"], cl["bridge-cert"]]
              and chronicle_actions(fam3["chron"]) == [
                  "place"] * 3 + ["retract"] * 2 + ["place"] * 2
              and tour_cls(fam3["tour"]) == [
                  cl["harbor-cert"], cl["tower-cert"],
                  cl["bridge-cert"]]
              and fam3["wprev"] == fam2["wprev"]
              and fam3["view_prev"] == fam2["view_prev"])
        record("AC-SMTR2", ok,
               "closure: wcur alpha {2,2,2} identity-BROKEN=%s"
               " (2 != 2-2 closed-yet-broken); broken=%s;"
               " full alpha {5,2,3} identity=%s (3==5-2);"
               " beta/mu wcur identity=%s; view_cur=%s;"
               " chronicle 3p+2r+2p; tour=%s; wprev frozen=%s;"
               " events=%d ledger_tx=%d"
               % (closed_break, broken_rows(fam3["wcur"]),
                  identity_ok(list(full3.values())),
                  identity_ok([wcur3["beta-gal"], wcur3["mu-gal"]]),
                  view_cls(fam3["view_cur"]),
                  tour_cls(fam3["tour"]),
                  fam3["wprev"] == fam2["wprev"],
                  counts3["exhibit_events"], counts3["ledger_tx"]))

        # -- AC-SMTR3 the third shape: post-closure retract ----
        #    of a CURRENT-month re-placed exhibit ----------------
        sh.retract_exhibit("usr:bob", "alpha-gal",
                           cl["bridge-cert"])
        counts4 = db_counts(sh_path, db_path)
        fam4 = form_family(sh, prev, cur, hist)
        full4 = rowmap(fam4["full"])
        wcur4 = rowmap(fam4["wcur"])
        third_row = wcur4["alpha-gal"]
        third_break = (int(third_row["displayed_now"])
                       != int(third_row["places"])
                       - int(third_row["retracts"]))
        third_rhs = (int(third_row["places"])
                     - int(third_row["retracts"]))
        ok = (counts4["exhibit_events"] == 10
              and counts4["ledger_tx"] == 0
              and triple(third_row) == (2, 3, 1)
              and third_break
              and third_rhs == -1
              and broken_rows(fam4["wcur"]) == ["alpha-gal"]
              and triple(full4["alpha-gal"]) == (5, 3, 2)
              and identity_ok(list(full4.values()))
              and identity_ok([wcur4["beta-gal"], wcur4["mu-gal"]])
              and fam4["wprev"] == fam3["wprev"]
              and fam4["view_prev"] == fam3["view_prev"]
              and view_cls(fam4["view_cur"]) == [cl["tower-cert"]]
              and chronicle_actions(fam4["chron"]) == [
                  "place"] * 3 + ["retract"] * 2 + ["place"] * 2
              + ["retract"]
              and tour_cls(fam4["tour"]) == [
                  cl["harbor-cert"], cl["tower-cert"]]
              and triple(rowmap(fam4["wcur"])["beta-gal"])
              == (2, 0, 2))
        record("AC-SMTR3", ok,
               "THIRD SHAPE: post-closure retract of the"
               " current-month re-placed bridge -> wcur alpha"
               " {2,3,1} identity-BROKEN=%s with rhs=%d"
               " (1 != 2-3 = -1, the negative-rhs third shape);"
               " broken=%s (alpha-specific); full alpha"
               " {5,3,2} identity=%s (2==5-3 held); beta/mu"
               " wcur identity=%s; wprev view byte-frozen=%s/%s;"
               " view_cur=%s; chronicle 3p+2r+2p+r; tour=%s;"
               " events=%d ledger_tx=%d"
               % (third_break, third_rhs,
                  broken_rows(fam4["wcur"]),
                  identity_ok(list(full4.values())),
                  identity_ok([wcur4["beta-gal"], wcur4["mu-gal"]]),
                  fam4["wprev"] == fam3["wprev"],
                  fam4["view_prev"] == fam3["view_prev"],
                  view_cls(fam4["view_cur"]),
                  tour_cls(fam4["tour"]),
                  counts4["exhibit_events"], counts4["ledger_tx"]))

        # -- AC-SMTR4 restart #1 at the third shape ------------
        sh.close()
        led.close()
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
        fam5 = form_family(sh2, prev, cur, hist)
        diff5 = [k for k in fam4 if fam4[k] != fam5[k]]
        counts5 = db_counts(sh_path, db_path)
        fam5b = form_family(sh2, prev, cur, hist)
        record("AC-SMTR4",
               not diff5 and fam5b == fam5 and counts5 == counts4,
               "restart #1 (same db/cfg/sh paths, fresh Ledger +"
               " stateless SecGate): 13/13 forms byte-identical"
               " vs the third-shape snapshots drift=%s; second"
               " read pass identical=%s; counts stable=%s"
               " (events=%d ledger_tx=%d)"
               % (diff5, fam5b == fam5, counts5 == counts4,
                  counts5["exhibit_events"], counts5["ledger_tx"]))

        # -- AC-SMTR5 the bounce: re-place after the third -----
        #    shape (the fourth shape pinned honestly) -----------
        probe_code = raise_code(
            lambda: sh2.place_exhibit("usr:alice", "alpha-gal",
                                      cl["tower-cert"], "", False))
        probe_counts = db_counts(sh_path, db_path)
        sh2.place_exhibit("usr:bob", "alpha-gal",
                          cl["bridge-cert"], "", False)
        counts6 = db_counts(sh_path, db_path)
        fam6 = form_family(sh2, prev, cur, hist)
        full6 = rowmap(fam6["full"])
        wcur6 = rowmap(fam6["wcur"])
        bounce_row = wcur6["alpha-gal"]
        bounce_break = (int(bounce_row["displayed_now"])
                        != int(bounce_row["places"])
                        - int(bounce_row["retracts"]))
        ok = (probe_code == S.E_SH_ALREADY_DISPLAYED
              and probe_counts == counts5
              and counts6["exhibit_events"] == 11
              and counts6["ledger_tx"] == 0
              and triple(bounce_row) == (3, 3, 2)
              and bounce_break
              and broken_rows(fam6["wcur"]) == ["alpha-gal"]
              and triple(full6["alpha-gal"]) == (6, 3, 3)
              and identity_ok(list(full6.values()))
              and identity_ok([wcur6["beta-gal"], wcur6["mu-gal"]])
              and view_cls(fam6["view_cur"]) == [
                  cl["tower-cert"], cl["bridge-cert"]]
              and chronicle_actions(fam6["chron"]) == [
                  "place"] * 3 + ["retract"] * 2 + ["place"] * 2
              + ["retract", "place"]
              and len(tour_cls(fam6["tour"])) == 3
              and fam6["wprev"] == fam4["wprev"]
              and fam6["view_prev"] == fam4["view_prev"])
        record("AC-SMTR5", ok,
               "bounce: already-displayed probe=%s zero-rows=%s;"
               " re-place bridge -> wcur alpha {3,3,2}"
               " identity-BROKEN=%s (2 != 3-3 = 0, the fourth"
               " shape pinned honestly); broken=%s; full alpha"
               " {6,3,3} identity=%s (3==6-3); beta/mu identity"
               "=%s; view_cur=%s; chronicle +retract+place;"
               " tour stops=%s; wprev frozen=%s; events=%d"
               % (probe_code == S.E_SH_ALREADY_DISPLAYED,
                  probe_counts == counts5, bounce_break,
                  broken_rows(fam6["wcur"]),
                  identity_ok(list(full6.values())),
                  identity_ok([wcur6["beta-gal"], wcur6["mu-gal"]]),
                  view_cls(fam6["view_cur"]),
                  tour_cls(fam6["tour"]),
                  fam6["wprev"] == fam4["wprev"],
                  counts6["exhibit_events"]))

        # -- AC-SMTR6 restart #2 + read storm + gates + purity --
        sh2.close()
        led2.close()
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_path)
        fam7 = form_family(sh3, prev, cur, hist)
        diff7 = [k for k in fam6 if fam6[k] != fam7[k]]
        counts_a = db_counts(sh_path, db_path)
        fam7a = form_family(sh3, prev, cur, hist)
        fam7b = form_family(sh3, prev, cur, hist)
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
        record("AC-SMTR6",
               not diff7 and counts_a == counts_b
               and counts_a["showcases"] == 3
               and counts_a["exhibit_events"] == 11
               and counts_a["ledger_tx"] == 0
               and fam7a == fam7b == fam7 and pure_src
               and gates_ok,
               "restart #2 (third instance): 13/13 forms"
               " byte-identical vs the bounce snapshots drift=%s"
               " (the {3,3,2} state persists); read storm x2:"
               " counts stable=%s (showcases=%d events=%d"
               " ledger_tx=%d), passes identical=%s; stats_board"
               " source zero writes=%s; gate family identical"
               " pre/post=%s; %d bad windows -> BAD_WINDOW=%s;"
               " %d bad limits -> BAD_LIMIT=%s; limit-first=%s"
               % (diff7, counts_a == counts_b,
                  counts_a["showcases"], counts_a["exhibit_events"],
                  counts_a["ledger_tx"], fam7a == fam7b == fam7,
                  pure_src, codes_pre == codes_post,
                  len(BAD_WINDOWS),
                  all(c == S.E_SH_BAD_WINDOW for c in win_codes),
                  len(BAD_LIMITS),
                  all(c == S.E_SH_BAD_LIMIT for c in lim_codes),
                  order_code))

        # -- AC-SMTR7 pure-read, honest zeros, hygiene ---------
        cross_code = raise_code(
            lambda: sh3.retract_exhibit("usr:dave", "alpha-gal",
                                        cl["gate-cert"]))
        cross_counts = db_counts(sh_path, db_path)
        wzero7 = rowmap(fam7["wzero"])
        whist7 = rowmap(fam7["whist"])
        post_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
        with open(os.path.abspath(__file__), "rb") as handle:
            own = handle.read()
        ascii_ok = all(b < 128 for b in own)
        net_tokens = ("soc" + "ket", "url" + "lib",
                      "htt" + "px", "reque" + "sts")
        net_ok = not any(t in own.decode("ascii", "ignore")
                         for t in net_tokens)
        ok = (cross_code == S.E_SH_NOT_DISPLAYED
              and cross_counts == counts_a
              and cross_counts["ledger_tx"] == 0
              and identity_ok(list(wzero7.values()))
              and identity_ok(list(whist7.values()))
              and triple(wzero7["alpha-gal"]) == (0, 0, 0)
              and triple(whist7["alpha-gal"]) == (0, 0, 0)
              and triple(rowmap(fam7["full"])["mu-gal"])
              == (0, 0, 0)
              and triple(rowmap(fam7["wcur"])["mu-gal"])
              == (0, 0, 0)
              and identity_ok([rowmap(fam7["wcur"])["mu-gal"]])
              and post_sha == pre_sha
              and ascii_ok and net_ok and outside
              and EXPECTED == 7)
        record("AC-SMTR7", ok,
               "pure-read law: cross-showcase not-displayed"
               " probe=%s (beta-displayed item refuses under"
               " alpha, zero rows, counts stable=%s); ledger_tx"
               "=%d across the whole suite (zero-token law);"
               " far window 2099-01 all-zero rows identity=%s;"
               " deep-history window all-zero identity=%s;"
               " mu-gal zero-event row holds in every form"
               " identity=%s; hygiene: product sha stable=%s,"
               " suite pure ASCII=%s, zero network imports=%s,"
               " world outside repo=%s, criteria==7=%s"
               % (cross_code == S.E_SH_NOT_DISPLAYED,
                  cross_counts == counts_a,
                  cross_counts["ledger_tx"],
                  identity_ok(list(wzero7.values())),
                  identity_ok(list(whist7.values())),
                  identity_ok([rowmap(fam7["wcur"])["mu-gal"]]),
                  post_sha == pre_sha, ascii_ok, net_ok,
                  outside, EXPECTED == 7))

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