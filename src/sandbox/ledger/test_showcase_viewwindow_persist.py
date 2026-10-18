"""Acceptance suite: showcase_view_window month-window slice
cross-restart persistence example window (BigDomain R2038;
canon = the explore-queue showcase_view_window persist line,
the R2036 reseed FIFO head). The R1996 windowed-view face slices
the display state by the record-time month law: an item appears
in a month window iff its latest window-recorded event is a
place. The R2036 gate suite pinned the bad-window gate family;
this successor pins the persistence of the window-scoped read
itself: the full window-scoped read family (the cur-month and
the out-of-range month views on a populated showcase, both
forms on an eventless showcase, the all-time view, the
chronicle, the tour) stays byte-identical across a full-stack
close/reopen on the same database paths, and post-restart real
writes keep the window views alive: a new place on the
eventless showcase enters its own record-month window read, a
new retract empties its record-month window read and the
all-time view agrees, the untouched-showcase family stays
byte-frozen across every write, the append-only event record
grows 3 -> 5, and the liveness writes survive a second
full-stack restart onto a third instance. Every month is
derived from the stored event rows (never hardcoded - the
zero-wall-clock law), and a month-boundary straddle is read
honestly per the record-time law instead of assumed away.

Asserts the pre-registered criteria AC-SVWP1..AC-SVWP7 from the
R2038 claim annotation in state/queue/explore.md (criteria were
registered before this code existed; honesty law).

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_showcase_viewwindow_persist.py
"""

import hashlib
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

DISCLAIMER = ("sandbox stand-in disclaimer: the showcase window"
              " view is a display feature, not investment advice")

VIEW_KEYS = {"showcase_id", "title", "slot_cap", "ai_label",
             "displayed", "disclaimer"}
VIEWWIN_KEYS = {"showcase_id", "window", "title", "slot_cap",
                "ai_label", "displayed", "disclaimer"}
OUT_WINDOW = "2099-01"

# The window-scoped read family is split into per-showcase key
# groups so a write on one showcase can be proven byte-frozen on
# the other (cross-showcase write isolation).
A_KEYS = ("a_cur", "a_zero", "a_all", "a_chron", "a_tour")
B_KEYS = ("b_cur", "b_zero")

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


def cur_of(view):
    """Derive the window month from a stored place event (the
    displayed[0] item's placed_utc prefix) - zero wall-clock."""
    return view["displayed"][0]["placed_utc"][:7]


def subfam(fam, keys):
    return dict((k, fam[k]) for k in keys)


def famwin(sh, cur):
    """The window-scoped read family serialized: the populated
    showcase at the cur month and the out-of-range month, the
    eventless showcase at both, plus the all-time view, the
    chronicle and the tour of the populated showcase."""
    out = {"a_cur": dumps(sh.showcase_view_window("sh-a", cur)),
           "a_zero": dumps(sh.showcase_view_window(
               "sh-a", OUT_WINDOW)),
           "b_cur": dumps(sh.showcase_view_window("sh-b", cur)),
           "b_zero": dumps(sh.showcase_view_window(
               "sh-b", OUT_WINDOW)),
           "a_all": dumps(sh.showcase_view("sh-a")),
           "a_chron": dumps(sh.chronicle("sh-a")),
           "a_tour": dumps(sh.chronicle_tour("sh-a"))}
    return out


def table_counts(shconn, ledconn):
    return {"showcases": int(shconn.execute(
                "SELECT COUNT(*) FROM showcases").fetchone()[0]),
            "exhibit_events": int(shconn.execute(
                "SELECT COUNT(*) FROM exhibit_events").fetchone()[0]),
            "collectibles": int(ledconn.execute(
                "SELECT COUNT(*) FROM collectibles").fetchone()[0])}


def build_world(led, gate, sh_db):
    """Populated registry axis world: three accounts, three
    certificates, two showcases (sh-a with a place+retract
    history, sh-b eventless). Returns (face, cert map)."""
    sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_db)
    for who in ("ada", "bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    cf = C.CollectiblesFace(led)
    cl = {}
    for who, ev, item in (
            ("ada", "evt-lamp", "lamp-cert"),
            ("bob", "evt-bell", "bell-cert"),
            ("carol", "evt-arch", "arch-cert")):
        cl[item] = cf.issue_certificate(
            "usr:" + who, ev, item)["cl_id"]
    sh.register_showcase("sh-a", "Window A", 4, False)
    sh.register_showcase("sh-b", "Window B", 2, False)
    sh.place_exhibit("usr:ada", "sh-a", cl["lamp-cert"],
                     "", False)
    sh.place_exhibit("usr:bob", "sh-a", cl["bell-cert"],
                     "", False)
    sh.retract_exhibit("usr:ada", "sh-a", cl["lamp-cert"])
    return sh, cl


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    tmp = tempfile.mkdtemp(prefix="showcase-viewwin-persist-")
    db_path = os.path.join(tmp, "ledger.db")
    sh_db = os.path.join(tmp, "showcase.db")
    hyg = {}
    led = sh = led2 = sh2 = led3 = sh3 = None
    shconn = ledconn = None
    try:
        led = L.Ledger(db_path, cfg)
        gate = SecGate.from_config(lobby_cfg)
        sh, cl = build_world(led, gate, sh_db)
        shconn = sqlite3.connect(sh_db)
        ledconn = sqlite3.connect(db_path)

        # -- AC-SVWP1 populated-world control anchor -------------
        view1 = sh.showcase_view("sh-a")
        cur = cur_of(view1)
        v1 = famwin(sh, cur)
        v1b = famwin(sh, cur)
        disp = view1["displayed"]
        acur = json.loads(v1["a_cur"])
        aall = json.loads(v1["a_all"])
        ok_disp = (len(disp) == 1
                   and disp[0]["cl_id"] == cl["bell-cert"])
        ok_win = (acur["displayed"] == disp
                  and acur["window"] == cur)
        ok_keys = (set(aall.keys()) == VIEW_KEYS
                   and set(acur.keys()) == VIEWWIN_KEYS)
        ok_zero = (json.loads(v1["a_zero"])["displayed"] == []
                   and json.loads(v1["b_cur"])["displayed"] == []
                   and json.loads(v1["b_zero"])["displayed"]
                   == [])
        chron = json.loads(v1["a_chron"])["events"]
        tour = json.loads(v1["a_tour"])["stops"]
        ok_chron = (len(chron) == 3
                    and sorted(e["action"] for e in chron)
                    == ["place", "place", "retract"]
                    and all(e["showcase_id"] == "sh-a"
                            for e in chron))
        ok_tour = (len(tour) == 1
                   and tour[0]["cl_id"] == cl["bell-cert"])
        record("AC-SVWP1",
               ok_disp and ok_win and ok_keys and ok_zero
               and ok_chron and ok_tour and v1 == v1b,
               "populated world: all-time displayed exactly"
               " [bell-cert]=%s; viewwin(cur=%s) displayed =="
               " all-time (all events recorded in cur, the"
               " record-time law)=%s; envelope keys view=%s"
               " viewwin=%s; out-of-range %s and eventless"
               " showcase honest empties=%s; chronicle 3"
               " events (2 place + 1 retract)=%s; tour 1"
               " stop=%s; family double-read"
               " byte-identical=%s"
               % (ok_disp, cur, ok_win,
                  set(aall.keys()) == VIEW_KEYS,
                  set(acur.keys()) == VIEWWIN_KEYS, OUT_WINDOW,
                  ok_zero, ok_chron, ok_tour, v1 == v1b))

        # -- AC-SVWP2 cross-restart persistence (instance two) ----
        sh.close()
        led.close()
        sh = led = None
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_db)
        v2 = famwin(sh2, cur)
        record("AC-SVWP2",
               v2 == v1,
               "full-stack close (sh -> led) then rebuild on"
               " the same db paths + same cfg bytes: the"
               " window-scoped read family is byte-identical"
               " to the instance-one snapshot (cross-restart"
               " persistence)=%s (cur=%s, out-of-range=%s)"
               % (v2 == v1, cur, OUT_WINDOW))

        # -- AC-SVWP3 post-restart liveness: new place -----------
        sh2.place_exhibit("usr:carol", "sh-b", cl["arch-cert"],
                          "", False)
        view_b = sh2.showcase_view("sh-b")
        pmonth = cur_of(view_b)
        wbp = sh2.showcase_view_window("sh-b", pmonth)
        ok_place = (len(view_b["displayed"]) == 1
                    and view_b["displayed"][0]["cl_id"]
                    == cl["arch-cert"]
                    and wbp["displayed"] == view_b["displayed"]
                    and wbp["window"] == pmonth
                    and set(wbp.keys()) == VIEWWIN_KEYS)
        fam_place = famwin(sh2, cur)
        ok_frozen = (subfam(fam_place, A_KEYS)
                     == subfam(v1, A_KEYS))
        record("AC-SVWP3",
               ok_place and ok_frozen,
               "post-restart new place on the eventless"
               " showcase: the place is recorded in month"
               " %s and viewwin(sh-b, pmonth) displayed =="
               " the all-time view exactly [arch-cert]=%s"
               " (window liveness: a new event enters its own"
               " record-month window); sh-a family byte-frozen"
               " across the write (cross-showcase write"
               " isolation)=%s"
               % (pmonth, ok_place, ok_frozen))

        # -- AC-SVWP4 post-restart liveness: new retract ----------
        sh2.retract_exhibit("usr:bob", "sh-a", cl["bell-cert"])
        gchron = sh2.chronicle(None)["events"]
        rmonth = gchron[-1]["acted_utc"][:7]
        war = sh2.showcase_view_window("sh-a", rmonth)
        view_a2 = sh2.showcase_view("sh-a")
        ok_retract = (war["displayed"] == []
                      and view_a2["displayed"] == []
                      and len(gchron) == 5)
        fam_retract = famwin(sh2, cur)
        ok_bfrozen = (subfam(fam_retract, B_KEYS)
                      == subfam(fam_place, B_KEYS))
        acur_r = json.loads(fam_retract["a_cur"])
        if rmonth == cur:
            straddle_ok = acur_r["displayed"] == []
            straddle_note = ("same-month form (rmonth == cur):"
                             " the cur window read emptied with"
                             " the retract")
        else:
            straddle_ok = acur_r["displayed"] == disp
            straddle_note = ("month-boundary straddle read"
                             " honestly per the record-time law"
                             " (rmonth=%s != cur=%s): the cur"
                             " window still shows the earlier"
                             " -month place" % (rmonth, cur))
        record("AC-SVWP4",
               ok_retract and ok_bfrozen and straddle_ok,
               "post-restart new retract on the populated"
               " showcase: viewwin(sh-a, rmonth=%s) displayed"
               " == [] and the all-time view agrees=%s;"
               " append-only event record grew 3 -> 5"
               " (global chronicle: 3 world-build + liveness"
               " place + liveness retract)=%s; sh-b window"
               " family byte-frozen across the write (write"
               " never moves other reads)=%s; %s (assert=%s)"
               % (rmonth, ok_retract, len(gchron) == 5,
                  ok_bfrozen, straddle_note, straddle_ok))

        # -- AC-SVWP5 pure-read law + third instance -------------
        read_a = [dumps(sh2.showcase_view("sh-a")),
                  dumps(sh2.showcase_view_window("sh-a", cur)),
                  dumps(sh2.showcase_view("sh-b")),
                  dumps(sh2.chronicle(None)),
                  dumps(sh2.chronicle_tour("sh-a"))]
        counts5a = table_counts(shconn, ledconn)
        read_b = [dumps(sh2.showcase_view("sh-a")),
                  dumps(sh2.showcase_view_window("sh-a", cur)),
                  dumps(sh2.showcase_view("sh-b")),
                  dumps(sh2.chronicle(None)),
                  dumps(sh2.chronicle_tour("sh-a"))]
        counts5b = table_counts(shconn, ledconn)
        v2final = famwin(sh2, cur)
        sh2.close()
        led2.close()
        sh2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_db)
        v3 = famwin(sh3, cur)
        record("AC-SVWP5",
               read_a == read_b and counts5a == counts5b
               and v3 == v2final,
               "pure-read law: the pre-close read battery"
               " double-run byte-identical=%s and leaves the"
               " three table counts unchanged %s == %s; third"
               " instance (second full-stack restart on the"
               " same db): the window-scoped read family =="
               " the instance-two final state byte-identical"
               " (the liveness writes survive the second"
               " restart)=%s"
               % (read_a == read_b, counts5a, counts5b,
                  v3 == v2final))
        sh3.close()
        led3.close()
        sh3 = led3 = None

        # -- AC-SVWP6 cross-instance vector identity -------------
        keys_stable = (set(json.loads(v1["a_cur"]).keys())
                       == VIEWWIN_KEYS
                       and set(json.loads(v2["a_cur"]).keys())
                       == VIEWWIN_KEYS
                       and set(json.loads(v3["a_cur"]).keys())
                       == VIEWWIN_KEYS
                       and set(json.loads(
                           v2final["a_all"]).keys())
                       == VIEW_KEYS)
        record("AC-SVWP6",
               v1 == v2 and v2final == v3 and keys_stable,
               "cross-instance persistence summary: V1 == V2"
               " (restart-one persist)=%s and V2final == V3"
               " (restart-two persist after the liveness"
               " writes)=%s, two full-stack restarts, three"
               " instances, liveness writes included; envelope"
               " key sets constant across instances=%s"
               % (v1 == v2, v2final == v3, keys_stable))

        # -- AC-SVWP7 hygiene ------------------------------------
        with open(os.path.abspath(__file__), "rb") as handle:
            own_bytes = handle.read()
        ascii_ok = all(b < 128 for b in own_bytes)
        net_ok = True
        for line in own_bytes.decode("ascii").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith(
                    "from "):
                if any(w in stripped for w in
                       ("urllib", "requests", "socket", "http")):
                    net_ok = False
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ("ledger-showcase-viewwindow-persist"
                  in reg_src
                  and "test_showcase_viewwindow_persist.py"
                  in reg_src)
        expected_ok = len(RESULTS) == EXPECTED - 1
        outside = tmp not in os.path.abspath(BASE)
        hyg = {"ascii_ok": ascii_ok, "net_ok": net_ok,
               "reg_ok": reg_ok, "expected_ok": expected_ok,
               "outside": outside}
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
    record("AC-SVWP7",
           hyg.get("ascii_ok") and hyg.get("net_ok")
           and hyg.get("reg_ok") and hyg.get("expected_ok")
           and hyg.get("outside") and sha_ok,
           "suite pure ASCII=%s net-clean=%s registry-wired=%s"
           " expected-count=%s world outside repo=%s"
           " product-sha stable=%s (suite-only round, zero"
           " product bytes change)"
           % (hyg.get("ascii_ok"), hyg.get("net_ok"),
              hyg.get("reg_ok"), hyg.get("expected_ok"),
              hyg.get("outside"), sha_ok))

    ok_all = len(RESULTS) == EXPECTED and all(
        ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                              sum(1 for _a, ok in RESULTS if ok),
                              EXPECTED), flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
