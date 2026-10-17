"""Acceptance suite: stats_board month-window post-retraction
current-month live state cross-restart persistence example window
(BigDomain R2018; canon = the R2017-reseed FIFO head, the
statsmonth family retract-persist successor). The family register
so far: the month-window face (R2015, AC-SSM) pinned the
record-time slicing laws incl. the straddle retract read; the
persist window (R2016, AC-SSMP) pinned the PLACE live-state
persistence across a full-stack restart; the zero-registration
boundary window (R2017, AC-SSMZ) pinned the empty-world restart
family. The remaining gap = the retraction-state successor:
after a retraction recorded in the CURRENT month, the current-
month window's live state must persist byte-identically across
restarts, the current-month net-flow identity
displayed_now == places - retracts must hold on the place-first
world shape (the identity is a full-board law, not a month-
window law in general - the straddle break face is already
R2015's register and is deliberately NOT re-probed here), and
the earlier-month window must stay byte-frozen across the
current-month retraction (the old-window freeze law).

World shape (registered in the R2018 claim line): one dense
showcase (alpha-gal) plus one zero-event showcase (mu-gal);
three previous-month places direct-inserted with explicit
stamps (the R1730 historical-month fixture law); two
current-month real-path places; a full-stack restart; then the
first post-restart retraction retires one current-month placed
item through the real path (proving the read-only ownership
dock reconnects, the R1992 law); a second full-stack restart
then re-reads every form.

Asserts the pre-registered criteria AC-SSMR1..AC-SSMR7 from
the R2018 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law).

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline. The double-run stdout
byte-identity face is carried by the external evidence harness
(the R1880 family law).

Usage: python test_showcase_statsmonthretractpersist.py
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
    """The eleven-form read family, all serialized: the R2016
    seven-form window family plus the two windowed display
    views, the full chronicle walk and the all-time tour."""
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
        "chronicle": dumps(sh.chronicle()),
        "tour": dumps(sh.chronicle_tour("alpha-gal")),
    }
    return fam


def rowmap(board_text):
    return {r["showcase_id"]: r for r in json.loads(board_text)
            ["showcase_stats_board"]}


def identity_ok(rows):
    """Net-flow identity per row: displayed_now == places -
    retracts. On the full board this is the shipped per-row law;
    on the month windows it holds on the place-first world shape
    (the claim-line ruling: the straddle break face belongs to
    the R2015 register and is not part of this world)."""
    for r in rows:
        if int(r["displayed_now"]) != (int(r["places"])
                                      - int(r["retracts"])):
            return False
    return bool(rows)


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
    # dense showcase first, then a zero-event showcase (the
    # honest-zero row rides every board form)
    sh.register_showcase("alpha-gal", "Alpha Gallery", 6, False)
    sh.register_showcase("mu-gal", "Mu Gallery", 3, True)
    # previous-month places: the R1730 fixture law (explicit
    # stamps, fully valid rows, real record path)
    for item, owner in (("tower-cert", "alice"),
                        ("bridge-cert", "bob"),
                        ("harbor-cert", "carol")):
        insert_hist(sh_path, "alpha-gal", cl[item], owner, prev_ts)
    # current-month real-path places (place-first chains)
    sh.place_exhibit("usr:dave", "alpha-gal", cl["gate-cert"],
                     "", False)
    sh.place_exhibit("usr:alice", "alpha-gal", cl["moon-cert"],
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

    tmp = tempfile.mkdtemp(prefix="showcase-statsmonthretract-")
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    outside = not os.path.normcase(os.path.abspath(tmp)).startswith(
        os.path.normcase(os.path.normpath(
            os.path.join(BASE, "..", "..", ".."))))
    hyg = {}
    led = sh = led2 = sh2 = led3 = sh3 = None
    try:
        led = L.Ledger(db_path, cfg)
        cf = C.CollectiblesFace(led)
        gate = SecGate.from_config(lobby_cfg)
        sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
        cl = {}
        build_world(led, cf, sh_path, sh, prev_ts, cl)

        # -- AC-SSMR1 pre-restart mixed-month anchors ------------
        fam1 = form_family(sh, prev, cur, hist)
        full1 = rowmap(fam1["full"])
        wprev1 = rowmap(fam1["wprev"])
        wcur1 = rowmap(fam1["wcur"])
        ok = (json.loads(fam1["full"]).keys() == FULL_KEYS
              and json.loads(fam1["cap2"]).keys() == CAP_KEYS
              and json.loads(fam1["wcur"]).keys() == WIN_KEYS
              and json.loads(fam1["wcap2"]).keys() == WINCAP_KEYS
              and full1["alpha-gal"] == {
                  "showcase_id": "alpha-gal",
                  "title": "Alpha Gallery", "ai_label": 0,
                  "places": 5, "retracts": 0, "displayed_now": 5}
              and full1["mu-gal"]["places"] == 0
              and full1["mu-gal"]["retracts"] == 0
              and full1["mu-gal"]["displayed_now"] == 0
              and identity_ok(list(full1.values()))
              and wprev1["alpha-gal"]["places"] == 3
              and wprev1["alpha-gal"]["retracts"] == 0
              and wprev1["alpha-gal"]["displayed_now"] == 3
              and identity_ok(list(wprev1.values()))
              and wcur1["alpha-gal"]["places"] == 2
              and wcur1["alpha-gal"]["retracts"] == 0
              and wcur1["alpha-gal"]["displayed_now"] == 2
              and identity_ok(list(wcur1.values()))
              and view_cls(fam1["view_prev"]) == [
                  cl["tower-cert"], cl["bridge-cert"],
                  cl["harbor-cert"]]
              and view_cls(fam1["view_cur"]) == [
                  cl["gate-cert"], cl["moon-cert"]]
              and chronicle_actions(fam1["chronicle"]) == [
                  "place"] * 5
              and tour_cls(fam1["tour"]) == [
                  cl["tower-cert"], cl["bridge-cert"],
                  cl["harbor-cert"], cl["gate-cert"],
                  cl["moon-cert"]])
        record("AC-SSMR1", ok,
               "mixed-month world anchors: full alpha"
               " {5,0,5} mu {0,0,0} identity=%s; wprev {3,0,3};"
               " wcur {2,0,2}; view prev=%s cur=%s; chronicle"
               " 5xplace; tour 5 stops"
               % (identity_ok(list(full1.values())),
                  view_cls(fam1["view_prev"]),
                  view_cls(fam1["view_cur"])))
        codes_pre = gate_codes(sh)

        # -- AC-SSMR2 first full-stack restart persistence -------
        sh.close()
        led.close()
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
        fam2 = form_family(sh2, prev, cur, hist)
        diff = [k for k in fam1 if fam1[k] != fam2[k]]
        record("AC-SSMR2", not diff,
               "restart #1 (same db/cfg/sh paths, fresh Ledger +"
               " stateless SecGate): 11/11 forms byte-identical"
               " drift=%s" % diff)

        # -- AC-SSMR3 first post-restart retraction: cur identity
        #    + old-window freeze --------------------------------
        sh2.retract_exhibit("usr:dave", "alpha-gal",
                            cl["gate-cert"])
        fam3 = form_family(sh2, prev, cur, hist)
        full3 = rowmap(fam3["full"])
        wcur3 = rowmap(fam3["wcur"])
        ok = (full3["alpha-gal"]["places"] == 5
              and full3["alpha-gal"]["retracts"] == 1
              and full3["alpha-gal"]["displayed_now"] == 4
              and identity_ok(list(full3.values()))
              and wcur3["alpha-gal"]["places"] == 2
              and wcur3["alpha-gal"]["retracts"] == 1
              and wcur3["alpha-gal"]["displayed_now"] == 1
              and identity_ok(list(wcur3.values()))
              and fam3["wprev"] == fam2["wprev"]
              and fam3["view_prev"] == fam2["view_prev"]
              and view_cls(fam3["view_cur"]) == [cl["moon-cert"]]
              and chronicle_actions(fam3["chronicle"]) == [
                  "place"] * 5 + ["retract"]
              and tour_cls(fam3["tour"]) == [
                  cl["tower-cert"], cl["bridge-cert"],
                  cl["harbor-cert"], cl["moon-cert"]])
        record("AC-SSMR3", ok,
               "post-restart first retract (real path, dock"
               " reconnected): wcur {2,1,1} identity=%s; full"
               " {5,1,4} identity=%s; wprev byte-frozen=%s;"
               " view_prev frozen=%s; view_cur=%s; chronicle"
               " 5xplace+retract; tour 4 stops"
               % (identity_ok(list(wcur3.values())),
                  identity_ok(list(full3.values())),
                  fam3["wprev"] == fam2["wprev"],
                  fam3["view_prev"] == fam2["view_prev"],
                  view_cls(fam3["view_cur"])))

        # -- AC-SSMR4 second full-stack restart: the retraction
        #    state persists --------------------------------------
        sh2.close()
        led2.close()
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_path)
        fam4 = form_family(sh3, prev, cur, hist)
        diff = [k for k in fam3 if fam3[k] != fam4[k]]
        record("AC-SSMR4", not diff,
               "restart #2 (third instance): 11/11 forms"
               " byte-identical vs post-retract snapshots"
               " drift=%s" % diff)

        # -- AC-SSMR5 pure-read law ------------------------------
        counts_a = db_counts(sh_path, db_path)
        fam5a = form_family(sh3, prev, cur, hist)
        fam5b = form_family(sh3, prev, cur, hist)
        counts_b = db_counts(sh_path, db_path)
        src = inspect.getsource(S.ShowcaseFace.stats_board)
        pure_src = ("INSERT" not in src and "UPDATE" not in src
                    and "DELETE" not in src)
        record("AC-SSMR5",
               counts_a == counts_b
               and counts_a["exhibit_events"] == 6
               and fam5a == fam5b == fam4 and pure_src,
               "read storm x2 on reopened instance: events"
               " constant=%s (%d rows), both passes byte-identical"
               " and equal to the restart-2 snapshots=%s, counts"
               " stable=%s, stats_board source zero writes=%s"
               % (counts_a["exhibit_events"] == 6,
                  counts_a["exhibit_events"],
                  fam5a == fam5b == fam4, counts_a == counts_b,
                  pure_src))

        # -- AC-SSMR6 gate family restart-stability --------------
        codes_post = gate_codes(sh3)
        win_codes = codes_post[:len(BAD_WINDOWS)]
        lim_codes = codes_post[len(BAD_WINDOWS):
                              len(BAD_WINDOWS) + len(BAD_LIMITS)]
        order_code = codes_post[-1]
        ok = (codes_pre == codes_post
              and all(c == S.E_SH_BAD_WINDOW
                      for c in win_codes)
              and all(c == S.E_SH_BAD_LIMIT
                      for c in lim_codes)
              and order_code == S.E_SH_BAD_LIMIT)
        record("AC-SSMR6", ok,
               "gate family identical pre/post restart=%s; %d bad"
               " windows -> E_SH_BAD_WINDOW=%s; %d bad limits ->"
               " E_SH_BAD_LIMIT=%s; limit-gate-first order"
               " probe=%s"
               % (codes_pre == codes_post, len(BAD_WINDOWS),
                  all(c == S.E_SH_BAD_WINDOW for c in win_codes),
                  len(BAD_LIMITS),
                  all(c == S.E_SH_BAD_LIMIT for c in lim_codes),
                  order_code))

        # -- AC-SSMR7 hygiene ------------------------------------
        post_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
        with open(os.path.abspath(__file__), "rb") as handle:
            own = handle.read()
        ascii_ok = all(b < 128 for b in own)
        net_tokens = ("soc" + "ket", "url" + "lib",
                      "htt" + "px", "reque" + "sts")
        net_ok = not any(t in own.decode("ascii", "ignore")
                         for t in net_tokens)
        sha_ok = post_sha == pre_sha
        record("AC-SSMR7",
               sha_ok and ascii_ok and net_ok and outside,
               "product sha stable=%s (showcase.py + both"
               " config.json); suite pure ASCII=%s; zero network"
               " imports=%s; world outside repo=%s; double-run"
               " face carried by the evidence harness"
               % (sha_ok, ascii_ok, net_ok, outside))
        hyg = {"pure_ok": pure_src, "ascii_ok": ascii_ok,
               "net_ok": net_ok, "outside": outside,
               "sha_ok": sha_ok}

        _ = hyg  # (kept for log-line symmetry with the family)
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
