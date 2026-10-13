"""Acceptance suite: ledger showcase read faces (showcase_view /
chronicle / chronicle_tour) cross-restart persistence example
(BigDomain R1925 tech-queue claim; seed = the R1921 reseed, claimed
after the R1920 lobby room_message_board row was closed as an
in-book duplicate). The three read faces (R1750) are pure-derived
over showcase.db (own file, latest-action-per-item displayed law,
event_id-ascending chronicle, stop-numbered tour). Their derived
purity across a full-stack instance restart had no pinned example
(R1889..R1923 persist family judgment reference; test_showcase.py
is single-instance, test_curation_hotpersist.py pins the curation
hot board only).

Asserts the pre-registered criteria AC-SHVP1..AC-SHVP7 from the
R1925 claim line in state/queue/tech.md (criteria were registered
before this code existed; honesty law). Claim rulings (three,
registered at claim time):
1. restart carrier = the full stack: ShowcaseFace close ->
   Ledger close, then a fresh Ledger (same db_path, same cfg
   bytes) + stateless SecGate + ShowcaseFace (same sh_path)
   reopen - the ledger dock reconnect is proven too (stronger
   than a face-only restart).
2. world = frozen-clock true product path: S._now_utc holder
   patch with an incrementing fixed-stamp sequence (finally
   restored, probe-checked); four avatars, seven certificates,
   four showcases cap 3, seven places + one retract + one
   re-place (the chronicle chain carries place/retract/place
   actions and the displayed latest-action law lives).
3. comparison face = dumps(sort_keys=True) byte equality on
   the eight enumerated read shapes (showcase_view x4,
   chronicle global, chronicle per-showcase, chronicle_tour x2)
   plus manual-SQL second-derivation cross-checks.

Snapshot-set note: the pre-registered enumeration (showcase_view
x4 + chronicle global + per-showcase + tour x2) is the eight-shape
set this suite walks; the enumeration governs.

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_showcase_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta

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

DISCLAIMER = ("sandbox stand-in disclaimer: showcase windows are a"
              " display feature, not investment advice")

PRODUCT_FILES = [
    os.path.join(BASE, "showcase.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

VIEW_KEYS = {"showcase_id", "title", "slot_cap", "ai_label",
             "displayed", "disclaimer"}
ITEM_KEYS = {"cl_id", "owner_id", "caption", "ai_label",
             "placed_utc"}
EVENT_KEYS = {"event_id", "showcase_id", "cl_id", "owner_id",
              "caption", "ai_label", "action", "acted_utc"}
TOUR_KEYS = {"showcase_id", "slot_cap", "stops", "disclaimer"}
STOP_KEYS = {"stop", "cl_id", "owner_id", "caption", "ai_label",
             "placed_utc"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def manual_displayed(conn, showcase_id):
    """Second derivation path: the latest-action-per-item law
    straight from a bare read-only connection."""
    rows = conn.execute(
        "SELECT cl_id, owner_id, caption, ai_label, acted_utc FROM"
        " exhibit_events WHERE event_id IN (SELECT MAX(event_id)"
        " FROM exhibit_events GROUP BY cl_id)"
        " AND action = 'place' AND showcase_id = ?"
        " ORDER BY event_id", (showcase_id,)).fetchall()
    return [{"cl_id": int(r[0]), "owner_id": r[1], "caption": r[2],
             "ai_label": int(r[3]), "placed_utc": r[4]}
            for r in rows]


def manual_events(conn, showcase_id=None):
    sql = ("SELECT event_id, showcase_id, cl_id, owner_id, caption,"
           " ai_label, action, acted_utc FROM exhibit_events")
    args = ()
    if showcase_id is not None:
        sql += " WHERE showcase_id = ?"
        args = (showcase_id,)
    sql += " ORDER BY event_id"
    return [{"event_id": int(r[0]), "showcase_id": r[1],
             "cl_id": int(r[2]), "owner_id": r[3], "caption": r[4],
             "ai_label": int(r[5]), "action": r[6],
             "acted_utc": r[7]}
            for r in conn.execute(sql, args).fetchall()]


def table_counts(shconn, ledconn):
    return {
        "showcases": int(shconn.execute(
            "SELECT COUNT(*) FROM showcases").fetchone()[0]),
        "exhibit_events": int(shconn.execute(
            "SELECT COUNT(*) FROM exhibit_events").fetchone()[0]),
        "collectibles": int(ledconn.execute(
            "SELECT COUNT(*) FROM collectibles").fetchone()[0]),
    }


def shapes(sh):
    """The eight enumerated read shapes."""
    return {
        "v1": dumps(sh.showcase_view("sh-one")),
        "v2": dumps(sh.showcase_view("sh-two")),
        "v3": dumps(sh.showcase_view("sh-three")),
        "v4": dumps(sh.showcase_view("sh-four")),
        "cg": dumps(sh.chronicle()),
        "cf": dumps(sh.chronicle("sh-one")),
        "t1": dumps(sh.chronicle_tour("sh-one")),
        "t4": dumps(sh.chronicle_tour("sh-four")),
    }


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    clock = {"seq": [
        (datetime(2026, 10, 15, 8, 0, 0)
         + timedelta(seconds=i)).strftime(
            "%Y-%m-%dT%H:%M:%S.%f") + "Z"
        for i in range(64)]}

    def frozen_now():
        seq = clock["seq"]
        return seq.pop(0) if len(seq) > 1 else seq[0]

    orig_now = S._now_utc
    S._now_utc = frozen_now

    tmp = tempfile.mkdtemp(prefix="ledger-showcasepersist-")
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    hyg = {}
    led = sh = led2 = sh2 = sh3 = led3 = None
    shconn = ledconn = None
    try:
        led = L.Ledger(db_path, cfg)
        cf = C.CollectiblesFace(led)
        gate = SecGate.from_config(lobby_cfg)
        sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)

        # ---- world: four avatars + seven certs + four showcases --
        for acct, avatar in (("usr:alice", "alice"),
                            ("usr:bob", "bob"),
                            ("usr:carol", "carol"),
                            ("usr:dave", "dave")):
            led.ensure_account(acct, census_avatar_id=avatar)
        specs = (
            ("a", "usr:alice", "evt-tower", "tower-cert"),
            ("b", "usr:bob", "evt-bridge", "bridge-cert"),
            ("c", "usr:carol", "evt-harbor", "harbor-cert"),
            ("d", "usr:dave", "evt-lamp", "lamp-cert"),
            ("e", "usr:alice", "evt-gate", "gate-cert"),
            ("f", "usr:bob", "evt-mill", "mill-cert"),
            ("g", "usr:carol", "evt-arch", "arch-cert"),
        )
        cl = {k: cf.issue_certificate(acct, ev, kind)["cl_id"]
              for k, acct, ev, kind in specs}
        for sid in ("sh-one", "sh-two", "sh-three", "sh-four"):
            sh.register_showcase(sid, sid + " window", 3, False)
        sh.place_exhibit("usr:alice", "sh-one", cl["a"],
                         "tower light")
        sh.place_exhibit("usr:bob", "sh-one", cl["b"],
                         "bridge arch")
        sh.place_exhibit("usr:carol", "sh-two", cl["c"],
                         "harbor lamp")
        sh.place_exhibit("usr:dave", "sh-three", cl["d"],
                         "lamp glow")
        sh.place_exhibit("usr:alice", "sh-three", cl["e"],
                         "gate relief")
        sh.place_exhibit("usr:bob", "sh-four", cl["f"],
                         "mill wheel")
        sh.place_exhibit("usr:carol", "sh-four", cl["g"],
                         "arch band")
        sh.retract_exhibit("usr:bob", "sh-one", cl["b"])
        sh.place_exhibit("usr:bob", "sh-four", cl["b"],
                         "bridge arch two")

        shconn = sqlite3.connect(sh_path)
        ledconn = sqlite3.connect(db_path)

        # ---- AC-SHVP1: world + pre-close eight-shape snapshot ---
        snap = shapes(sh)
        v1 = json.loads(snap["v1"])
        v4 = json.loads(snap["v4"])
        cg = json.loads(snap["cg"])
        t1 = json.loads(snap["t1"])
        t4 = json.loads(snap["t4"])
        ok1 = []
        ok1.append(set(v1.keys()) == VIEW_KEYS
                   and set(v4.keys()) == VIEW_KEYS)
        ok1.append(all(set(r.keys()) == ITEM_KEYS
                       for r in v1["displayed"] + v4["displayed"]))
        ok1.append(v1["displayed"]
                   == manual_displayed(shconn, "sh-one")
                   and v4["displayed"]
                   == manual_displayed(shconn, "sh-four"))
        ok1.append(v4["slot_cap"] == 3
                   and len(v4["displayed"]) == 3)
        ok1.append(set(cg.keys()) == {"events", "disclaimer"}
                   and all(set(r.keys()) == EVENT_KEYS
                           for r in cg["events"]))
        ok1.append(cg["events"] == manual_events(shconn))
        ok1.append([r["event_id"] for r in cg["events"]]
                   == list(range(1, 10)))
        ok1.append([r["action"] for r in cg["events"]][7] == "retract"
                   and [r["action"] for r in cg["events"]][8] == "place")
        ok1.append(set(t1.keys()) == TOUR_KEYS
                   and set(t4.keys()) == TOUR_KEYS
                   and all(set(r.keys()) == STOP_KEYS
                           for r in t1["stops"] + t4["stops"]))
        ok1.append([r["stop"] for r in t4["stops"]] == [1, 2, 3]
                   and [r["cl_id"] for r in t4["stops"]]
                   == [cl["f"], cl["g"], cl["b"]])
        ok1.append([r["stop"] for r in t1["stops"]] == [1]
                   and t1["stops"][0]["cl_id"] == cl["a"])
        cf_sh_one = json.loads(snap["cf"])
        ok1.append(cf_sh_one["events"]
                   == manual_events(shconn, "sh-one")
                   and all(r["showcase_id"] == "sh-one"
                           for r in cf_sh_one["events"]))
        ok1.append(v1["disclaimer"] == DISCLAIMER
                   and cg["disclaimer"] == DISCLAIMER)
        record("AC-SHVP1", all(ok1),
               "view-keys=%s item-keys=%s manual-displayed=%s "
               "sh-four cap 3/3=%s chronicle==mirror event_id "
               "1..9=%s retract/re-place chain=%s tour-stops "
               "renumber=%s filter-purity=%s disclaimer-standing=%s"
               % (set(v1.keys()) == VIEW_KEYS,
                  all(set(r.keys()) == ITEM_KEYS
                      for r in v1["displayed"] + v4["displayed"]),
                  v1["displayed"]
                  == manual_displayed(shconn, "sh-one"),
                  len(v4["displayed"]) == 3 and v4["slot_cap"] == 3,
                  [r["event_id"] for r in cg["events"]]
                  == list(range(1, 10)),
                  [r["action"] for r in cg["events"]][7:] ==
                  ["retract", "place"],
                  [r["stop"] for r in t4["stops"]] == [1, 2, 3],
                  all(r["showcase_id"] == "sh-one"
                      for r in cf_sh_one["events"]),
                  v1["disclaimer"] == DISCLAIMER))

        # ---- AC-SHVP2: cross-restart eight-shape byte identity ---
        sh.close()
        led.close()
        sh = led = None
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
        snap2 = shapes(sh2)
        double2 = (dumps(sh2.showcase_view("sh-one"))
                   == snap2["v1"]
                   and dumps(sh2.chronicle()) == snap2["cg"])
        record("AC-SHVP2", snap2 == snap and double2,
               "full-stack close (sh -> led) then rebuild on same "
               "paths: eight shapes byte-identical=%s double-read "
               "self=%s" % (snap2 == snap, double2))

        # ---- AC-SHVP3: post-restart place/retract -> recompute ---
        ev_base = len(json.loads(snap2["cg"])["events"])
        sh2.retract_exhibit("usr:alice", "sh-three", cl["e"])
        sh2.place_exhibit("usr:alice", "sh-two", cl["e"],
                          "gate relief two")
        sh2.retract_exhibit("usr:alice", "sh-one", cl["a"])
        snap3 = shapes(sh2)
        v2_3 = json.loads(snap3["v2"])
        v1_3 = json.loads(snap3["v1"])
        cg3 = json.loads(snap3["cg"])
        old_rows = {r["event_id"]: r
                    for r in json.loads(snap2["cg"])["events"]}
        new_rows = {r["event_id"]: r for r in cg3["events"]}
        frozen_old = all(dumps(new_rows[k]) == dumps(old_rows[k])
                         for k in old_rows)
        record("AC-SHVP3",
               snap3 != snap2
               and len(v2_3["displayed"]) == 2
               and [r["cl_id"] for r in v2_3["displayed"]]
               == [cl["c"], cl["e"]]
               and len(v1_3["displayed"]) == 0
               and [r["event_id"] for r in cg3["events"]]
               == list(range(1, ev_base + 4))
               and frozen_old
               and json.loads(snap3["t1"])["stops"] == [],
               "recompute zero-cache: sh-two 1->2 carried cl_e=%s, "
               "sh-one 1->0 tour empty=%s, event_id continuity "
               "%d..%d=%s old-events frozen=%s"
               % ([r["cl_id"] for r in v2_3["displayed"]]
                  == [cl["c"], cl["e"]],
                  json.loads(snap3["t1"])["stops"] == [],
                  ev_base + 1, ev_base + 3,
                  [r["event_id"] for r in cg3["events"]]
                  == list(range(1, ev_base + 4)),
                  frozen_old))

        # ---- AC-SHVP4: re-place chain + fail-closed gates survive -
        sh2.place_exhibit("usr:alice", "sh-one", cl["a"],
                          "tower light two")
        ghost_refused = False
        try:
            sh2.showcase_view("sh-ghost")
        except S.ShowcaseError as exc:
            ghost_refused = (getattr(exc, "code", None)
                             == "E_SH_UNKNOWN_SHOWCASE")
        ghost_chron = False
        try:
            sh2.chronicle("sh-ghost")
        except S.ShowcaseError as exc:
            ghost_chron = (getattr(exc, "code", None)
                           == "E_SH_UNKNOWN_SHOWCASE")
        cf_two = json.loads(dumps(sh2.chronicle("sh-two")))
        snap4 = shapes(sh2)
        v1_4 = json.loads(snap4["v1"])
        record("AC-SHVP4",
               len(v1_4["displayed"]) == 1
               and v1_4["displayed"][0]["cl_id"] == cl["a"]
               and v1_4["displayed"][0]["caption"]
               == "tower light two"
               and ghost_refused and ghost_chron
               and all(r["showcase_id"] == "sh-two"
                       for r in cf_two["events"])
               and len(cf_two["events"]) == 2,
               "retract-then-re-place legal (sh-one re-carries cl_a "
               "with new caption)=%s; unknown-showcase fail-closed "
               "survives restart (view=%s chronicle=%s); per-window "
               "filter purity=%s"
               % (len(v1_4["displayed"]) == 1
                  and v1_4["displayed"][0]["cl_id"] == cl["a"],
                  ghost_refused, ghost_chron,
                  all(r["showcase_id"] == "sh-two"
                      for r in cf_two["events"])))

        # ---- AC-SHVP5: third instance sequential reads ----------
        counts_before = table_counts(shconn, ledconn)
        sh2.close()
        led2.close()
        sh2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_path)
        snap5 = shapes(sh3)
        seq5 = (dumps(sh3.showcase_view("sh-one")) == snap5["v1"]
                and dumps(sh3.chronicle()) == snap5["cg"]
                and dumps(sh3.chronicle_tour("sh-four"))
                == snap5["t4"])
        oct_frozen = all(
            dumps(new_rows[k]) == dumps(old_rows[k]) for k in old_rows)
        counts_after = table_counts(shconn, ledconn)
        record("AC-SHVP5",
               snap5 == snap4 and seq5 and oct_frozen
               and counts_before == counts_after,
               "third instance == second-instance final state "
               "byte-identical=%s sequential double-read self=%s "
               "october anchor events still == pre-close=%s "
               "counts-flat=%s"
               % (snap5 == snap4, seq5, oct_frozen,
                  counts_before == counts_after))

        # ---- AC-SHVP6: pure-read law ------------------------------
        battery = [dumps(sh3.showcase_view(s))
                  for s in ("sh-one", "sh-two", "sh-three",
                            "sh-four")]
        battery += [dumps(sh3.chronicle()),
                   dumps(sh3.chronicle("sh-one")),
                   dumps(sh3.chronicle_tour("sh-one")),
                   dumps(sh3.chronicle_tour("sh-four"))]
        battery += battery[:5]
        pair = battery[0] == battery[8] and battery[1] == battery[9]
        counts_b = table_counts(shconn, ledconn)
        record("AC-SHVP6", counts_b == counts_after and pair,
               "read battery left showcases/exhibit_events/"
               "collectibles counts constant (%s); repeat-read "
               "pair identical=%s"
               % (json.dumps(counts_b, sort_keys=True), pair))
        sh3.close()
        led3.close()
        sh3 = led3 = None

        # ---- AC-SHVP7: hygiene -----------------------------------
        with open(os.path.join(BASE, "showcase.py"),
                  encoding="utf-8") as handle:
            src = handle.read()
        segs_ok = True
        for seg_name in ("def showcase_view", "def chronicle",
                         "def chronicle_tour"):
            s = src.find(seg_name)
            e = src.find("\n    def ", s + 10)
            if s < 0:
                segs_ok = False
                continue
            if e == -1:
                e = len(src)          # final method: scan to EOF
            seg = src[s:e]
            segs_ok = segs_ok and not re.search(
                r"\bINSERT\b|\bUPDATE\b|\bDELETE\b", seg)
        with open(os.path.abspath(__file__), "rb") as handle:
            own_bytes = handle.read()
        ascii_ok = all(b < 128 for b in own_bytes)
        net_ok = True
        for line in own_bytes.decode("ascii").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith(
                    "from "):
                if any(w in stripped for w in ("urllib", "requests",
                                               "socket", "http")):
                    net_ok = False
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ("ledger-showcaseview-persist" in reg_src
                  and "test_showcase_persist.py" in reg_src)
        expected_ok = len(RESULTS) == EXPECTED - 1
        hyg = {"segs_ok": segs_ok, "ascii_ok": ascii_ok,
               "net_ok": net_ok, "reg_ok": reg_ok,
               "expected_ok": expected_ok}
    finally:
        S._now_utc = orig_now
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

    restore_ok = S._now_utc is orig_now
    post_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    sha_ok = pre_sha == post_sha
    record("AC-SHVP7",
           hyg.get("segs_ok") and hyg.get("ascii_ok")
           and hyg.get("net_ok") and hyg.get("reg_ok")
           and hyg.get("expected_ok") and restore_ok and sha_ok,
           "read-face-segments-strip=%s ascii=%s net-clean=%s "
           "registry-wired=%s clock-restored=%s product-sha-stable=%s"
           % (hyg.get("segs_ok"), hyg.get("ascii_ok"),
              hyg.get("net_ok"), hyg.get("reg_ok"), restore_ok,
              sha_ok))

    ok_all = len(RESULTS) == EXPECTED and all(
        ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                              sum(1 for _a, ok in RESULTS if ok),
                              EXPECTED), flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
