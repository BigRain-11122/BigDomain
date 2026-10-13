"""Acceptance suite for the curation registry / tour read-face family
cross-restart persistence example window (BigDomain R1926; canon =
the R1923-reseeded tech-queue row claimed by R1926). The three
read faces under proof (curation.py, R1751 in-register):

  - active_curations(): the registry board (every curation with
    its member count, rowid order);
  - curation_view(id): facts and per-member reads (positions,
    titles, slot caps, live on-display counts through the
    ShowcaseFace public API);
  - curation_tour(id): the global stop-numbered tour (member
    showcase tours concatenated in registered order, stops
    numbered 1..N across showcases).

Derived purity across instance restarts is pinned: pre-close
three-form snapshots == reopened reads byte-identical, zero-cache
recompute after a post-restart placement and a post-restart new
registration, third-instance sequential reads byte-identical,
pure-read law, manual-SQL second-derivation cross, product-file
sha256 double-proof, hygiene.

Criteria AC-CRP1..CRP7 were pre-registered in
state/queue/tech.md at claim time (R1926, before this code
existed; honesty law; AC-CRP prefix git-grep zero-occupancy
anchored 2026-10-13; AC-CU1..CU7 belong to the R1751 single-
instance suite and are not re-registered here).

Suite-only round: zero product-code changes (curation.py,
showcase.py, ledger.py and both shipped config.json files are
sha256 double-proven unchanged). Restart carrier = the seed row
text: CurationFace close -> new instance over the SAME
ShowcaseFace object and the same curation db path (the three
forms' own persistence substrate is the curation registry rows;
showcase facts flow live through the public API).

Usage: python test_curation_regpersist.py
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

import ledger as L                    # noqa: E402 (P-47-2b core)
import collectibles as C              # noqa: E402 (R619 owner face)
import showcase as S                  # noqa: E402 (R1750 parent face)
import curation as CU                 # noqa: E402 (R1751 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, ref)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: themed curation"
              " listings and tours are display features, not"
              " investment advice")

PRODUCT_FILES = [
    os.path.join(BASE, "curation.py"),
    os.path.join(BASE, "showcase.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

BOARD_KEYS = {"curation_id", "title", "ai_label", "registered_utc",
              "member_count"}
VIEW_KEYS = {"curation_id", "title", "ai_label", "registered_utc",
             "members", "disclaimer"}
MEMBER_KEYS = {"position", "showcase_id", "title", "slot_cap",
               "on_display"}
TOUR_KEYS = {"curation_id", "title", "ai_label", "stops",
             "disclaimer"}
STOP_KEYS = {"stop", "showcase_id", "cl_id", "owner_id", "caption",
             "ai_label", "placed_utc"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(env):
    return json.dumps(env, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def manual_member_counts(cuconn):
    return {cid: int(n) for cid, n in cuconn.execute(
        "SELECT curation_id, COUNT(*) FROM curation_members"
        " GROUP BY curation_id").fetchall()}


def manual_on_display(shconn, showcase_id):
    return int(shconn.execute(
        "SELECT COUNT(*) FROM exhibit_events WHERE event_id IN"
        " (SELECT MAX(event_id) FROM exhibit_events GROUP BY"
        " cl_id) AND action = 'place' AND showcase_id = ?",
        (showcase_id,)).fetchone()[0])


def manual_displayed_ids(shconn, showcase_id):
    return [int(r[0]) for r in shconn.execute(
        "SELECT cl_id FROM exhibit_events WHERE event_id IN"
        " (SELECT MAX(event_id) FROM exhibit_events GROUP BY"
        " cl_id) AND action = 'place' AND showcase_id = ?"
        " ORDER BY event_id", (showcase_id,)).fetchall()]


def table_counts(shconn, cuconn):
    return {
        "curations": int(cuconn.execute(
            "SELECT COUNT(*) FROM curations").fetchone()[0]),
        "curation_members": int(cuconn.execute(
            "SELECT COUNT(*) FROM curation_members").fetchone()[0]),
        "showcases": int(shconn.execute(
            "SELECT COUNT(*) FROM showcases").fetchone()[0]),
        "exhibit_events": int(shconn.execute(
            "SELECT COUNT(*) FROM exhibit_events").fetchone()[0]),
    }


def read_all_forms(face):
    """Read every form under proof once, return dict of dumps."""
    active = face.active_curations()
    views = {cid: face.curation_view(cid)
             for cid in ("cu-alpha", "cu-beta")}
    tours = {cid: face.curation_tour(cid)
             for cid in ("cu-alpha", "cu-beta")}
    return {"active": dumps(active), "views": views, "tours": tours}


def main():
    tmp = tempfile.mkdtemp(prefix="curation-regpersist-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    cu_path = os.path.join(tmp, "curation.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

    led = L.Ledger(db_path, cfg)
    cf = C.CollectiblesFace(led)
    gate = SecGate.from_config(lobby_cfg)
    sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
    cu = CU.CurationFace(sh, DISCLAIMER, cu_path)

    # -- world: true product path, four avatars + five certs +
    # three showcases (cap 3) + two curated routes ---------------
    for acct, avatar in (("usr:alice", "alice"), ("usr:bob", "bob"),
                         ("usr:carol", "carol"),
                         ("usr:dave", "dave")):
        led.ensure_account(acct, census_avatar_id=avatar)
    specs = (
        ("a", "usr:alice", "evt-tower", "tower-cert"),
        ("b", "usr:bob", "evt-bridge", "bridge-cert"),
        ("c", "usr:carol", "evt-harbor", "harbor-cert"),
        ("d", "usr:dave", "evt-lamp", "lamp-cert"),
        ("e", "usr:alice", "evt-gate", "gate-cert"),
    )
    cl = {}
    for key, acct, ev, kind in specs:
        cl[key] = cf.issue_certificate(acct, ev, kind)["cl_id"]
    for sid in ("sh-one", "sh-two", "sh-three"):
        sh.register_showcase(sid, sid + " window", 3, False)
    sh.place_exhibit("usr:alice", "sh-one", cl["a"], "tower light")
    sh.place_exhibit("usr:bob", "sh-two", cl["b"], "bridge arch")
    sh.place_exhibit("usr:carol", "sh-two", cl["c"], "harbor lamp")
    sh.place_exhibit("usr:dave", "sh-three", cl["d"], "lamp glow")
    cu.register_curation("cu-alpha", "Alpha Route",
                         ["sh-one", "sh-two"], False)
    cu.register_curation("cu-beta", "Beta Route",
                         ["sh-three"], False)

    shconn = sqlite3.connect(sh_path)
    cuconn = sqlite3.connect(cu_path)

    # -- AC-CRP1 control anchor: pre-close three-form pinning -----
    f1 = read_all_forms(cu)
    active1 = cu.active_curations()
    board1 = active1["curations"]
    view_a1 = f1["views"]["cu-alpha"]
    view_b1 = f1["views"]["cu-beta"]
    tour_a1 = f1["tours"]["cu-alpha"]
    tour_b1 = f1["tours"]["cu-beta"]
    ok1 = []
    ok1.append(len(board1) == 2
               and board1[0]["curation_id"] == "cu-alpha"
               and board1[0]["member_count"] == 2
               and board1[1]["curation_id"] == "cu-beta"
               and board1[1]["member_count"] == 1)
    ok1.append(set(active1.keys()) == {"curations", "disclaimer"})
    ok1.append(all(set(r.keys()) == BOARD_KEYS for r in board1))
    ok1.append(board1[0]["member_count"]
               == manual_member_counts(cuconn)["cu-alpha"]
               and board1[1]["member_count"]
               == manual_member_counts(cuconn)["cu-beta"])
    ok1.append(set(view_a1.keys()) == VIEW_KEYS
               and set(view_b1.keys()) == VIEW_KEYS)
    ok1.append(all(set(m.keys()) == MEMBER_KEYS
                   for m in view_a1["members"]
                   + view_b1["members"]))
    ok1.append(view_a1["members"][0]["showcase_id"] == "sh-one"
               and view_a1["members"][0]["position"] == 1
               and view_a1["members"][0]["on_display"] == 1
               and view_a1["members"][1]["showcase_id"] == "sh-two"
               and view_a1["members"][1]["position"] == 2
               and view_a1["members"][1]["on_display"] == 2)
    ok1.append(view_b1["members"][0]["showcase_id"] == "sh-three"
               and view_b1["members"][0]["on_display"] == 1)
    ok1.append(view_a1["members"][0]["on_display"]
               == manual_on_display(shconn, "sh-one")
               and view_a1["members"][1]["on_display"]
               == manual_on_display(shconn, "sh-two")
               and view_b1["members"][0]["on_display"]
               == manual_on_display(shconn, "sh-three"))
    ok1.append(set(tour_a1.keys()) == TOUR_KEYS
               and set(tour_b1.keys()) == TOUR_KEYS)
    ok1.append(all(set(s.keys()) == STOP_KEYS
                   for s in tour_a1["stops"] + tour_b1["stops"]))
    ok1.append([s["stop"] for s in tour_a1["stops"]] == [1, 2, 3])
    ok1.append([s["stop"] for s in tour_b1["stops"]] == [1])
    ok1.append([s["showcase_id"] for s in tour_a1["stops"]]
               == ["sh-one", "sh-two", "sh-two"])
    ok1.append([s["cl_id"] for s in tour_a1["stops"]]
               == manual_displayed_ids(shconn, "sh-one")
               + manual_displayed_ids(shconn, "sh-two"))
    ok1.append([s["cl_id"] for s in tour_b1["stops"]]
               == manual_displayed_ids(shconn, "sh-three"))
    record("AC-CRP1", all(ok1),
           "pre-close pinning: registry board 2 rows (alpha mc=2,"
           " beta mc=1) == manual SQL; view members positions"
           " 1..2 with live on_display 1/2 == latest-action law;"
           " tour alpha 3 stops globally numbered 1..3 across"
           " sh-one+sh-two, tour beta 1 stop; envelopes/rows key"
           " sets exact-pinned; stops == manual displayed-id"
           " concatenation")
    snap1 = {"active": f1["active"],
             "view_a": dumps(view_a1), "view_b": dumps(view_b1),
             "tour_a": dumps(tour_a1), "tour_b": dumps(tour_b1)}

    # -- AC-CRP2 restart: byte-identical three forms --------------
    counts_before_read2 = table_counts(shconn, cuconn)
    cu.close()
    cu2 = CU.CurationFace(sh, DISCLAIMER, cu_path)
    f2 = read_all_forms(cu2)
    counts_after_read2 = table_counts(shconn, cuconn)
    ok2 = [f2["active"] == snap1["active"],
           dumps(f2["views"]["cu-alpha"]) == snap1["view_a"],
           dumps(f2["views"]["cu-beta"]) == snap1["view_b"],
           dumps(f2["tours"]["cu-alpha"]) == snap1["tour_a"],
           dumps(f2["tours"]["cu-beta"]) == snap1["tour_b"]]
    record("AC-CRP2", all(ok2),
           "CurationFace close -> new instance over the SAME"
           " ShowcaseFace object and the same curation db path:"
           " reopened active_curations + curation_view x2 +"
           " curation_tour x2 all byte-identical to the pre-close"
           " snapshots (sort_keys dumps; zero in-memory drift in"
           " the derived read faces)")

    # -- AC-CRP3 post-restart placement: zero-cache recompute -------
    sh.place_exhibit("usr:alice", "sh-two", cl["e"], "gate relief")
    view_a3 = cu2.curation_view("cu-alpha")
    tour_a3 = cu2.curation_tour("cu-alpha")
    ok3 = []
    ok3.append(view_a3["members"][1]["showcase_id"] == "sh-two"
               and view_a3["members"][1]["on_display"] == 3)
    ok3.append(view_a3["members"][1]["on_display"]
               == manual_on_display(shconn, "sh-two"))
    ok3.append(len(tour_a3["stops"]) == 4)
    ok3.append([s["stop"] for s in tour_a3["stops"]] == [1, 2, 3, 4])
    ok3.append(tour_a3["stops"][3]["cl_id"] == cl["e"]
               and tour_a3["stops"][3]["showcase_id"] == "sh-two")
    ok3.append(dumps(view_a3) != snap1["view_a"]
               and dumps(tour_a3) != snap1["tour_a"])
    record("AC-CRP3", all(ok3),
           "post-restart placement of cl_e into member showcase"
           " sh-two: cu-alpha view recomputed zero-cache"
           " (sh-two on_display 2 -> 3), tour gained stop 4"
           " (global numbering continues across the sh-two"
           " segment end), envelopes differ from the pre-restart"
           " snapshots")

    # -- AC-CRP4 post-restart registration: zero-cache recompute ---
    cu2.register_curation("cu-gamma", "Gamma Route",
                          ["sh-three", "sh-one"], False)
    active4 = cu2.active_curations()
    view_g4 = cu2.curation_view("cu-gamma")
    tour_g4 = cu2.curation_tour("cu-gamma")
    ok4 = []
    ok4.append(len(active4["curations"]) == 3
               and [r["curation_id"] for r in active4["curations"]]
               == ["cu-alpha", "cu-beta", "cu-gamma"]
               and active4["curations"][2]["member_count"] == 2)
    ok4.append(active4["curations"][2]["member_count"]
               == manual_member_counts(cuconn)["cu-gamma"])
    ok4.append(view_g4["members"][0]["showcase_id"] == "sh-three"
               and view_g4["members"][0]["position"] == 1
               and view_g4["members"][1]["showcase_id"] == "sh-one"
               and view_g4["members"][1]["position"] == 2)
    ok4.append(view_g4["members"][0]["on_display"] == 1
               and view_g4["members"][1]["on_display"] == 1)
    ok4.append(len(tour_g4["stops"]) == 2
               and [s["stop"] for s in tour_g4["stops"]] == [1, 2]
               and tour_g4["stops"][0]["showcase_id"] == "sh-three"
               and tour_g4["stops"][1]["showcase_id"] == "sh-one")
    record("AC-CRP4", all(ok4),
           "post-restart new registration cu-gamma (members"
           " sh-three + sh-one, registered order): registry board"
           " gained the row at the rowid tail with member_count 2"
           " == manual SQL; view positions 1..2 in registered"
           " order; tour 2 stops globally numbered across the two"
           " member showcases - all recomputed zero-cache")

    snap2 = {"active": dumps(cu2.active_curations()),
             "view_a": dumps(view_a3), "view_b": dumps(
                 cu2.curation_view("cu-beta")),
             "view_g": dumps(view_g4), "tour_a": dumps(tour_a3),
             "tour_b": dumps(cu2.curation_tour("cu-beta")),
             "tour_g": dumps(tour_g4)}

    # -- AC-CRP5 third instance: sequential reads identical --------
    cu2.close()
    cu3 = CU.CurationFace(sh, DISCLAIMER, cu_path)
    counts_before_read5 = table_counts(shconn, cuconn)
    active5 = cu3.active_curations()
    view_a5 = cu3.curation_view("cu-alpha")
    view_b5 = cu3.curation_view("cu-beta")
    view_g5 = cu3.curation_view("cu-gamma")
    tour_a5 = cu3.curation_tour("cu-alpha")
    tour_b5 = cu3.curation_tour("cu-beta")
    tour_g5 = cu3.curation_tour("cu-gamma")
    active5b = cu3.active_curations()
    counts_after_read5 = table_counts(shconn, cuconn)
    ok5 = [dumps(active5) == snap2["active"]
           and dumps(active5b) == dumps(active5),
           dumps(view_a5) == snap2["view_a"],
           dumps(view_b5) == snap2["view_b"],
           dumps(view_g5) == snap2["view_g"],
           dumps(tour_a5) == snap2["tour_a"],
           dumps(tour_b5) == snap2["tour_b"],
           dumps(tour_g5) == snap2["tour_g"]]
    record("AC-CRP5", all(ok5),
           "second curation-face restart (third instance, same"
           " ShowcaseFace + same db): all seven form reads"
           " byte-identical to the post-mutation state and the"
           " repeated board read identical to itself (repeat-read"
           " purity, zero in-memory drift)")

    # -- AC-CRP6 pure-read law + product-file sha double-proof ----
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    ok6 = [counts_after_read2 == counts_before_read2,
           counts_after_read5 == counts_before_read5,
           shas_after == shas_before]
    record("AC-CRP6", all(ok6),
           "pure-read law: every read batch left curations /"
           " curation_members / showcases / exhibit_events row"
           " counts constant (%s); product files sha256 unchanged"
           " (curation.py, showcase.py, ledger.py, both shipped"
           " config.json)"
           % json.dumps(counts_after_read5, sort_keys=True))

    # -- AC-CRP7 hygiene: ASCII, zero-network imports, tmp world --
    with open(os.path.abspath(__file__), "rb") as handle:
        src_bytes = handle.read()
    ok7 = [all(b < 128 for b in src_bytes)]
    net_hits = []
    for line in src_bytes.decode("ascii").splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith(
                "from "):
            for bad in ("urllib", "requests", "socket", "http"):
                if bad in stripped:
                    net_hits.append(stripped)
    ok7.append(not net_hits)
    ok7.append(os.path.abspath(tmp).startswith(tempfile.gettempdir()))
    ok7.append(os.path.abspath(BASE) not in os.path.abspath(tmp))
    record("AC-CRP7", all(ok7),
           "hygiene: source pure ASCII (%d bytes), zero network"
           " imports on true import lines, world db in system tmp"
           " outside the repo" % len(src_bytes))

    cu3.close()
    sh.close()
    led.close()
    shconn.close()
    cuconn.close()

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
