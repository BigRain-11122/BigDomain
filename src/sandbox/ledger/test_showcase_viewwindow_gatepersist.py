"""Acceptance suite: showcase_view_window bad-window gate
family cross-restart same-code example window (BigDomain R2036;
canon = the explore-queue showcase_view_window gate-family
cross-restart line, the R2035 reseed FIFO head). The R1996
windowed-view face gates the window parameter before any read
(dedicated family code E_SH_BAD_WINDOW; None is not accepted
here - the all-time form is the plain showcase_view face, the
windowed-face-only law). The R2035 stats gate suite pinned the
stats_board gate family; this successor pins the view-window
gate family: 15 bad window forms (non-str types and
non-strict YYYY-MM shapes) plus the window-before-showcase
order probe (bad window + unknown showcase must reject with
the window code first) and the good-window unknown-showcase
probe (the showcase gate still enforces behind the window gate)
as an ordered (probe, code) vector that stays byte-identical on
instances one/two/three across two full-stack restarts (the
R2035 AC-SGB / R1999 AC-HCWP4 gate-family cross-restart
same-code precedents). Unlike the R2010 zero-registry boundary
world, this suite runs against a populated registry axis (one
active showcase with a place+retract history, one eventless
showcase): the gates fire before any read against non-empty
data too, and every probe batch leaves the three table counts
unchanged on every instance. A post-restart liveness leg proves
the probe batch never wedges the face (a real write on a new
showcase grows the world while the touched-showcase reads stay
byte-frozen and the battery stays same-code), and the
third-instance leg adds the pure-read law. The cur window month
is derived from the stored place-event acted_utc prefix (never
hardcoded - zero-wall-clock law, robust across month
boundaries).

Asserts the pre-registered criteria AC-SVW1..AC-SVW7 from the
R2036 claim annotation in state/queue/explore.md (criteria were
registered before this code existed; honesty law).

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_showcase_viewwindow_gatepersist.py
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

# 15 bad window forms: the non-str types (None rejected on the
# windowed face per the all-time-form law, int, bool, float)
# and the non-strict YYYY-MM shapes (empty, alpha, year-only,
# one-digit month, month 13, month 00, slash separator,
# three-digit month, trailing newline, leading space, day
# segment).
BAD_WINDOW = (None, 2026, True, 2.5, "", "abcd", "2026",
              "2026-1", "2026-13", "2026-00", "2026/10",
              "2026-010", "2026-10\n", " 2026-10",
              "2026-10-05")

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


def family(sh, cur):
    """The touched-showcase read family serialized: all-time
    view, window view at the derived cur month, window view at
    the out-of-range month, the eventless showcase both forms,
    chronicle, tour."""
    out = {"view_active": dumps(sh.showcase_view("sh-active"))}
    out["viewwin_cur"] = dumps(
        sh.showcase_view_window("sh-active", cur))
    out["viewwin_zero"] = dumps(
        sh.showcase_view_window("sh-active", "2099-01"))
    out["view_empty"] = dumps(sh.showcase_view("sh-empty"))
    out["viewwin_empty_zero"] = dumps(
        sh.showcase_view_window("sh-empty", "2099-01"))
    out["chron_active"] = dumps(sh.chronicle("sh-active"))
    out["tour_active"] = dumps(sh.chronicle_tour("sh-active"))
    return out


def live_family(sh):
    """The post-liveness showcase read family (sh-live both
    forms + the out-of-range month)."""
    view = sh.showcase_view("sh-live")
    cur_live = cur_of(view)
    return {"live_view": dumps(view),
            "live_viewwin": dumps(
                sh.showcase_view_window("sh-live", cur_live)),
            "live_zero": dumps(
                sh.showcase_view_window("sh-live", "2099-01"))}


def battery(sh):
    """The 17-probe gate family battery as an ordered
    (probe-name, rejection-code) vector, JSON-serialized.
    Fifteen bad window forms on the populated showcase, the
    window-before-showcase order probe (bad window + unknown
    showcase rejects with the window code first), and the
    good-window unknown-showcase probe (the showcase gate
    enforces behind the window gate)."""
    out = []
    for i, bad in enumerate(BAD_WINDOW):
        try:
            sh.showcase_view_window("sh-active", bad)
            out.append(["win-%02d" % i, "no-raise"])
        except S.ShowcaseError as exc:
            out.append(["win-%02d" % i, exc.code])
    try:
        sh.showcase_view_window("sh-ghost", "2026-13")
        out.append(["order-badwin-ghost", "no-raise"])
    except S.ShowcaseError as exc:
        out.append(["order-badwin-ghost", exc.code])
    try:
        sh.showcase_view_window("sh-ghost", "2026-10")
        out.append(["goodwin-ghost", "no-raise"])
    except S.ShowcaseError as exc:
        out.append(["goodwin-ghost", exc.code])
    return json.dumps(out)


def want_vector():
    """The expected ordered code vector: 15 E_SH_BAD_WINDOW
    window forms, 1 E_SH_BAD_WINDOW order probe, 1
    E_SH_UNKNOWN_SHOWCASE good-window probe."""
    out = []
    for i in range(len(BAD_WINDOW)):
        out.append(["win-%02d" % i, S.E_SH_BAD_WINDOW])
    out.append(["order-badwin-ghost", S.E_SH_BAD_WINDOW])
    out.append(["goodwin-ghost", S.E_SH_UNKNOWN_SHOWCASE])
    return json.dumps(out)


def table_counts(shconn, ledconn):
    return {"showcases": int(shconn.execute(
                "SELECT COUNT(*) FROM showcases").fetchone()[0]),
            "exhibit_events": int(shconn.execute(
                "SELECT COUNT(*) FROM exhibit_events").fetchone()[0]),
            "collectibles": int(ledconn.execute(
                "SELECT COUNT(*) FROM collectibles").fetchone()[0])}


def build_world(led, gate):
    """Populated registry axis world: three accounts, three
    certificates, two showcases (one active with a place+retract
    history, one eventless). Returns (face, cert map)."""
    sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path[0])
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
    sh.register_showcase("sh-active", "Active Window", 4, False)
    sh.register_showcase("sh-empty", "Empty Window", 2, False)
    sh.place_exhibit("usr:ada", "sh-active", cl["lamp-cert"],
                     "", False)
    sh.place_exhibit("usr:bob", "sh-active", cl["bell-cert"],
                     "", False)
    sh.retract_exhibit("usr:ada", "sh-active", cl["lamp-cert"])
    return sh, cl


sh_path = [None]  # set in main (module-level for build_world)


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    tmp = tempfile.mkdtemp(prefix="showcase-viewwin-gate-")
    db_path = os.path.join(tmp, "ledger.db")
    sh_path[0] = os.path.join(tmp, "showcase.db")
    hyg = {}
    led = sh = led2 = sh2 = led3 = sh3 = None
    shconn = ledconn = None
    try:
        led = L.Ledger(db_path, cfg)
        gate = SecGate.from_config(lobby_cfg)
        sh, cl = build_world(led, gate)
        shconn = sqlite3.connect(sh_path[0])
        ledconn = sqlite3.connect(db_path)

        # -- AC-SVW1 populated-world control anchor -------------
        view1 = sh.showcase_view("sh-active")
        cur = cur_of(view1)
        fam = family(sh, cur)
        fam_b = family(sh, cur)
        disp = view1["displayed"]
        wcur = json.loads(fam["viewwin_cur"])
        wzero = json.loads(fam["viewwin_zero"])
        ok_disp = (len(disp) == 1
                   and disp[0]["cl_id"] == cl["bell-cert"])
        ok_win_disp = (wcur["displayed"] == disp
                       and wcur["window"] == cur)
        ok_keys = (set(view1.keys()) == VIEW_KEYS
                   and set(wcur.keys()) == VIEWWIN_KEYS)
        ok_zero = (wzero["displayed"] == []
                   and json.loads(
                       fam["viewwin_empty_zero"])["displayed"]
                   == [] and json.loads(
                       fam["view_empty"])["displayed"] == [])
        chron = json.loads(fam["chron_active"])["events"]
        tour = json.loads(fam["tour_active"])["stops"]
        ok_chron = (len(chron) == 3
                    and sorted(e["action"] for e in chron)
                    == ["place", "place", "retract"]
                    and all(e["showcase_id"] == "sh-active"
                            for e in chron))
        ok_tour = (len(tour) == 1
                   and tour[0]["cl_id"] == cl["bell-cert"])
        record("AC-SVW1",
               ok_disp and ok_win_disp and ok_keys and ok_zero
               and ok_chron and ok_tour and fam == fam_b,
               "populated world: all-time displayed exactly"
               " [bell-cert]=%s; viewwin(cur=%s) displayed =="
               " all-time=%s (window echo=%s); envelope keys"
               " view=%s viewwin=%s; out-of-range 2099-01 and"
               " eventless showcase honest empties=%s; chronicle"
               " 3 events (2 place + 1 retract)=%s; tour 1"
               " stop=%s; family double-read byte-identical=%s"
               % (ok_disp, cur, ok_win_disp,
                  wcur["window"] == cur,
                  set(view1.keys()) == VIEW_KEYS,
                  set(wcur.keys()) == VIEWWIN_KEYS, ok_zero,
                  ok_chron, ok_tour, fam == fam_b))

        # -- AC-SVW2 instance-one baseline battery --------------
        v1 = battery(sh)
        c0 = table_counts(shconn, ledconn)
        v1b = battery(sh)
        c1 = table_counts(shconn, ledconn)
        want = want_vector()
        record("AC-SVW2",
               v1 == want and c0 == c1 and v1 == v1b,
               "baseline battery: 17 probes (15 bad-window"
               " forms + window-before-showcase order probe +"
               " good-window unknown-showcase probe) all reject"
               " with the expected ordered code vector=%s;"
               " probe batch double-run byte-identical=%s;"
               " counts unchanged %s == %s (gates fire before"
               " any read on the populated face)"
               % (v1 == want, v1 == v1b, c0, c1))

        # -- AC-SVW3 cross-restart same-code (instance two) -----
        sh.close()
        led.close()
        sh = led = None
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path[0])
        fam2 = family(sh2, cur)
        c2a = table_counts(shconn, ledconn)
        v2 = battery(sh2)
        c2b = table_counts(shconn, ledconn)
        record("AC-SVW3",
               v2 == v1 and c2a == c2b and fam2 == fam,
               "full-stack close (sh -> led) then rebuild on"
               " same paths + same cfg bytes: battery vector"
               " byte-identical to baseline (same-code)=%s;"
               " instance-two probe batch zero side effects"
               " %s == %s; read family byte-identical across"
               " restart=%s"
               % (v2 == v1, c2a, c2b, fam2 == fam))

        # -- AC-SVW4 post-restart liveness ----------------------
        sh2.register_showcase("sh-live", "Live Window", 3,
                              False)
        sh2.place_exhibit("usr:carol", "sh-live",
                          cl["arch-cert"], "", False)
        view_live = sh2.showcase_view("sh-live")
        cur_live = cur_of(view_live)
        wlive = sh2.showcase_view_window("sh-live", cur_live)
        fam2b = family(sh2, cur)
        v2b = battery(sh2)
        ok_live = (len(view_live["displayed"]) == 1
                   and view_live["displayed"][0]["cl_id"]
                   == cl["arch-cert"]
                   and wlive["displayed"]
                   == view_live["displayed"]
                   and wlive["window"] == cur_live
                   and set(wlive.keys()) == VIEWWIN_KEYS)
        record("AC-SVW4",
               ok_live and fam2b == fam and v2b == v1,
               "post-restart liveness on instance two: real"
               " write path (register + place) -> viewwin"
               "(cur_live=%s) displayed exactly the placed"
               " cert=%s; touched-showcase family byte-frozen"
               " (cross-showcase isolation, write never moves"
               " other reads)=%s; battery stays same-code after"
               " the world growth=%s"
               % (cur_live, ok_live, fam2b == fam, v2b == v1))

        # -- AC-SVW5 third instance + pure-read law -------------
        lfam2 = live_family(sh2)
        counts5a = table_counts(shconn, ledconn)
        read_a = [dumps(sh2.showcase_view("sh-active")),
                  dumps(sh2.showcase_view_window(
                      "sh-active", cur)),
                  dumps(sh2.showcase_view_window(
                      "sh-live", cur_live)),
                  dumps(sh2.chronicle_tour("sh-active"))]
        read_b = [dumps(sh2.showcase_view("sh-active")),
                  dumps(sh2.showcase_view_window(
                      "sh-active", cur)),
                  dumps(sh2.showcase_view_window(
                      "sh-live", cur_live)),
                  dumps(sh2.chronicle_tour("sh-active"))]
        counts5b = table_counts(shconn, ledconn)
        fam2final = family(sh2, cur)
        v2final = battery(sh2)
        sh2.close()
        led2.close()
        sh2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_path[0])
        fam3 = family(sh3, cur)
        lfam3 = live_family(sh3)
        v3 = battery(sh3)
        record("AC-SVW5",
               v3 == v1 and fam3 == fam2final
               and lfam3 == lfam2
               and read_a == read_b and counts5a == counts5b
               and v2final == v1,
               "third instance: battery vector == baseline"
               " (same-code across the second restart)=%s; read"
               " family == instance-two final state (liveness"
               " write survives the restart)=%s; sh-live family"
               " == instance-two terminal=%s; pre-close read"
               " battery double-run byte-identical=%s; read"
               " battery leaves counts unchanged %s == %s"
               % (v3 == v1, fam3 == fam2final,
                  lfam3 == lfam2, read_a == read_b,
                  counts5a, counts5b))
        sh3.close()
        led3.close()
        sh3 = led3 = None

        # -- AC-SVW6 cross-instance vector identity -------------
        d6v = json.loads(fam["viewwin_cur"])
        d6l = json.loads(lfam2["live_viewwin"])
        keys_stable = (set(d6v.keys()) == VIEWWIN_KEYS
                       and set(d6l.keys()) == VIEWWIN_KEYS
                       and set(json.loads(
                           fam3["view_active"]).keys())
                       == VIEW_KEYS
                       and set(json.loads(
                           fam2b["view_active"]).keys())
                       == VIEW_KEYS)
        record("AC-SVW6",
               v1 == v2 == v2b == v3 and keys_stable,
               "cross-instance same-code summary: ordered probe"
               " vectors V1 == V2 == V2b == V3 byte-identical"
               "=%s (two full-stack restarts, three instances,"
               " liveness write included); envelope key sets"
               " constant across instances (view / viewwin)=%s"
               % (v1 == v2 == v2b == v3, keys_stable))

        # -- AC-SVW7 hygiene ------------------------------------
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
        reg_ok = ("ledger-showcase-viewwindow-gatepersist"
                  in reg_src
                  and "test_showcase_viewwindow_gatepersist.py"
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
    record("AC-SVW7",
           hyg.get("ascii_ok") and hyg.get("net_ok")
           and hyg.get("reg_ok") and hyg.get("expected_ok")
           and hyg.get("outside") and sha_ok,
           "suite pure ASCII=%s net-clean=%s registry-wired=%s"
           " expected-count=%s world outside repo=%s"
           " product-sha stable=%s"
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
