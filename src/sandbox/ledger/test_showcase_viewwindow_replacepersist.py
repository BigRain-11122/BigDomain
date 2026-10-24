"""Acceptance suite: showcase window-view re-place bounce across
restart (BigDomain R2067; canon = the explore-queue
showcase_view_window re-place bounce persist line, the R2038
reseed FIFO head).

The R2038 suite pinned the window-scoped read family's
persistence over a live display state. The gap left open is the
retracted world: after a full retract history the window reads
are empty while the append-only chronicle stays full, and the
question is whether that state persists and whether a re-place
bounce after restart is picked up by the same month-window face.

This suite pins:
  * the retracted world as a control anchor (all-time empty,
    window-scoped read empty, chronicle 4 events, tour empty,
    bounce gates live, zero token movement);
  * the retracted world surviving a full-stack close/reopen
    byte-identically;
  * post-restart re-place liveness (the item returns to the
    all-time view, its record-month window view and the tour,
    the chronicle grows append-only, a second place while
    displayed rejects and leaves zero new rows);
  * a second retract -> re-place cycle (the bounce is
    repeatable, the chronicle keeps growing, the untouched
    showcase stays byte-frozen across every write);
  * the bounce final state surviving a second full-stack
    restart onto a third instance with the pure-read law held;
  * cross-instance vector identity and gate-code stability
    across restarts;
  * hygiene (suite-only round, zero product bytes change).

Asserts the pre-registered criteria AC-SVRP1..AC-SVRP7 from the
R2067 claim annotation in state/queue/explore.md (criteria were
registered before this code existed; honesty law).

This source stays pure ASCII per the encoding discipline.

Usage: python test_showcase_viewwindow_replacepersist.py
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

# Per-showcase key groups: a write on one showcase must stay
# byte-frozen on the other (cross-showcase write isolation).
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
    """Derive the window month from a stored place event - zero
    wall clock (the R2038 law)."""
    return view["displayed"][0]["placed_utc"][:7]


def subfam(fam, keys):
    return dict((k, fam[k]) for k in keys)


def famwin(sh, cur):
    """The window-scoped read family serialized."""
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
                "SELECT COUNT(*) FROM collectibles").fetchone()[0]),
            "ledger_tx": int(ledconn.execute(
                "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])}


def build_world(led, gate, sh_db):
    """Retracted-world build: two showcases, three certificates,
    then a full retract history on sh-a (place lamp, place bell,
    retract lamp, retract bell)."""
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
    sh.retract_exhibit("usr:bob", "sh-a", cl["bell-cert"])
    return sh, cl


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    tmp = tempfile.mkdtemp(prefix="showcase-viewwin-replace-")
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

        # -- AC-SVRP1 retracted-world control anchor -------------
        view1 = sh.showcase_view("sh-a")
        chron1 = sh.chronicle("sh-a")["events"]
        # The retracted world has an empty display, so the window
        # month is derived from the stored event record instead
        # (zero wall clock, the R2038 law).
        cur = chron1[0]["acted_utc"][:7]
        acts = [e["action"] for e in chron1]
        v1 = famwin(sh, cur)
        v1b = famwin(sh, cur)
        a_win = json.loads(v1["a_cur"])
        a_all = json.loads(v1["a_all"])
        tour = json.loads(v1["a_tour"])["stops"]
        ok_empty = (view1["displayed"] == []
                    and a_win["displayed"] == []
                    and a_win["window"] == cur
                    and len(tour) == 0)
        ok_keys = (set(a_all.keys()) == VIEW_KEYS
                   and set(a_win.keys()) == VIEWWIN_KEYS)
        ok_chron = (acts == ["place", "place", "retract", "retract"]
                    and len(chron1) == 4)
        ok_zero = (json.loads(v1["a_zero"])["displayed"] == []
                   and json.loads(v1["b_cur"])["displayed"] == []
                   and json.loads(v1["b_zero"])["displayed"] == [])
        gates = []
        for clid in (cl["bell-cert"], cl["lamp-cert"]):
            try:
                sh.retract_exhibit("usr:bob" if clid == cl["bell-cert"]
                                   else "usr:ada", "sh-a", clid)
                gates.append("no-raise")
            except S.ShowcaseError as exc:
                gates.append(str(exc.code))
        ok_gate = (gates == [S.E_SH_NOT_DISPLAYED,
                             S.E_SH_NOT_DISPLAYED]
                   and len(sh.chronicle("sh-a")["events"]) == 4
                   and table_counts(shconn, ledconn)["ledger_tx"] == 0)
        record("AC-SVRP1",
               ok_empty and ok_keys and ok_chron and ok_zero
               and ok_gate and v1 == v1b,
               "retracted world: all-time displayed empty=%s;"
               " window read (cur=%s) displayed empty=%s;"
               " envelope keys view=%s viewwin=%s; chronicle 4"
               " events [place,place,retract,retract]=%s;"
               " out-of-range %s and eventless showcase honest"
               " empties=%s; re-retract gates=%s (zero new"
               " events); ledger_tx==0=%s; family double-read"
               " byte-identical=%s"
               % (view1["displayed"] == [], cur,
                  a_win["displayed"] == [],
                  set(a_all.keys()) == VIEW_KEYS,
                  set(a_win.keys()) == VIEWWIN_KEYS, ok_chron,
                  OUT_WINDOW, ok_zero, gates, ok_gate,
                  v1 == v1b))

        # -- AC-SVRP2 first full-stack restart -------------------
        sh.close()
        led.close()
        sh = led = None
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_db)
        v2 = famwin(sh2, cur)
        record("AC-SVRP2",
               v2 == v1,
               "full-stack close (sh -> led) then rebuild on the"
               " same db paths + same cfg bytes: the"
               " window-scoped read family of the retracted"
               " world is byte-identical to the instance-one"
               " snapshot=%s (cur=%s, out-of-range=%s)"
               % (v2 == v1, cur, OUT_WINDOW))

        # -- AC-SVRP3 post-restart re-place bounce ---------------
        sh2.place_exhibit("usr:bob", "sh-a", cl["bell-cert"],
                          "", False)
        view_a = sh2.showcase_view("sh-a")
        pmonth = cur_of(view_a)
        wap = sh2.showcase_view_window("sh-a", pmonth)
        chron3 = sh2.chronicle("sh-a")["events"]
        tour3 = sh2.chronicle_tour("sh-a")["stops"]
        ok_place = (len(view_a["displayed"]) == 1
                    and view_a["displayed"][0]["cl_id"]
                    == cl["bell-cert"]
                    and wap["displayed"] == view_a["displayed"]
                    and wap["window"] == pmonth
                    and set(wap.keys()) == VIEWWIN_KEYS)
        ok_chain = ([e["action"] for e in chron3]
                    == ["place", "place", "retract", "retract",
                        "place"]
                    and len(tour3) == 1
                    and tour3[0]["cl_id"] == cl["bell-cert"])
        try:
            sh2.place_exhibit("usr:bob", "sh-a",
                              cl["bell-cert"], "", False)
            dup_code = "no-raise"
        except S.ShowcaseError as exc:
            dup_code = str(exc.code)
        ok_dup = (dup_code == S.E_SH_ALREADY_DISPLAYED
                  and len(sh2.chronicle("sh-a")["events"]) == 5)
        fam3 = famwin(sh2, cur)
        ok_frozen = subfam(fam3, B_KEYS) == subfam(v1, B_KEYS)
        record("AC-SVRP3",
               ok_place and ok_chain and ok_dup and ok_frozen,
               "post-restart re-place bounce: the retracted item"
               " returns to the all-time view=%s; window read of"
               " its record month (%s) shows it=%s; chronicle"
               " grew 4 -> 5 [p,p,r,r,p] and the tour shows 1"
               " stop=%s; second place while displayed rejects"
               " with %s and leaves zero new rows=%s; the"
               " untouched showcase family stays byte-frozen"
               " across the write=%s"
               % (ok_place, pmonth, ok_place, ok_chain, dup_code,
                  ok_dup, ok_frozen))

        # -- AC-SVRP4 second retract -> re-place cycle -----------
        sh2.retract_exhibit("usr:bob", "sh-a", cl["bell-cert"])
        mid_chron = len(sh2.chronicle("sh-a")["events"])
        mid_disp = sh2.showcase_view("sh-a")["displayed"]
        sh2.place_exhibit("usr:bob", "sh-a", cl["bell-cert"],
                          "", False)
        v_final = sh2.showcase_view("sh-a")
        fmonth = cur_of(v_final)
        wfin = sh2.showcase_view_window("sh-a", fmonth)
        chron4 = sh2.chronicle("sh-a")["events"]
        acts4 = [e["action"] for e in chron4]
        ok_cycle = (mid_chron == 6 and mid_disp == []
                    and acts4 == ["place", "place", "retract",
                                  "retract", "place", "retract",
                                  "place"]
                    and v_final["displayed"][0]["cl_id"]
                    == cl["bell-cert"]
                    and wfin["displayed"] == v_final["displayed"])
        fam4 = famwin(sh2, cur)
        ok_b4 = subfam(fam4, B_KEYS) == subfam(v1, B_KEYS)
        ok_tx = table_counts(shconn, ledconn)["ledger_tx"] == 0
        record("AC-SVRP4",
               ok_cycle and ok_b4 and ok_tx,
               "second retract -> re-place cycle: after the"
               " retract the display is empty and the chronicle"
               " holds 6 events (%s); the re-place brings the"
               " item back, its record-month window read (%s)"
               " follows the all-time view, and the chronicle"
               " holds 7 alternating events=%s; the untouched"
               " showcase family stays byte-frozen across both"
               " writes=%s; zero token movement throughout"
               " (ledger_tx==0)=%s"
               % (mid_chron == 6 and mid_disp == [], fmonth,
                  ok_cycle, ok_b4, ok_tx))

        # -- AC-SVRP5 second restart + third instance -------------
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
        v3b = famwin(sh3, cur)
        record("AC-SVRP5",
               read_a == read_b and counts5a == counts5b
               and v3 == v2final and v3b == v3,
               "second full-stack restart: the bounce final"
               " state crosses onto the third instance"
               " byte-identically=%s; third-instance double read"
               " identical=%s; the read battery leaves the four"
               " table counts unchanged %s == %s (pure-read law)"
               % (v3 == v2final, v3b == v3, counts5a, counts5b))

        # -- AC-SVRP6 cross-instance identity + gate stability ---
        gates3 = []
        try:
            sh3.place_exhibit("usr:bob", "sh-a", cl["bell-cert"],
                              "", False)
            gates3.append("no-raise")
        except S.ShowcaseError as exc:
            gates3.append(str(exc.code))
        sh3.retract_exhibit("usr:bob", "sh-a", cl["bell-cert"])
        try:
            sh3.retract_exhibit("usr:bob", "sh-a", cl["bell-cert"])
            gates3.append("no-raise")
        except S.ShowcaseError as exc:
            gates3.append(str(exc.code))
        keys_stable = (set(json.loads(v1["a_cur"]).keys())
                       == VIEWWIN_KEYS
                       and set(json.loads(v2["a_cur"]).keys())
                       == VIEWWIN_KEYS
                       and set(json.loads(v3["a_cur"]).keys())
                       == VIEWWIN_KEYS
                       and set(json.loads(
                           v2final["a_all"]).keys()) == VIEW_KEYS)
        record("AC-SVRP6",
               v1 == v2 and v2final == v3 and keys_stable
               and gates3[0] == S.E_SH_ALREADY_DISPLAYED
               and gates3[1] == S.E_SH_NOT_DISPLAYED,
               "cross-instance persistence summary: retracted"
               " world V1 == V2=%s and bounce final V2final == V3"
               "=%s (two full-stack restarts); envelope key sets"
               " constant across instances=%s; bounce gate codes"
               " stable on the third instance=%s (place-while-"
               "displayed then retract-when-absent, zero rows"
               " beyond the one probe retract)"
               % (v1 == v2, v2final == v3, keys_stable, gates3))
        sh3.close()
        led3.close()
        sh3 = led3 = None

        # -- AC-SVRP7 hygiene ------------------------------------
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
        reg_ok = ("ledger-showcase-viewwindow-replacepersist"
                  in reg_src
                  and "test_showcase_viewwindow_replacepersist.py"
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
    record("AC-SVRP7",
           hyg.get("ascii_ok") and hyg.get("net_ok")
           and hyg.get("reg_ok") and hyg.get("expected_ok")
           and hyg.get("outside") and sha_ok,
           "suite pure ASCII=%s net-clean=%s registry-wired=%s"
           " expected-count=%s world outside repo=%s product-sha"
           " stable=%s (suite-only round, zero product bytes"
           " change)"
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