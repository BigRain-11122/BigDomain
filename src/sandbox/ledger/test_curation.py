"""Acceptance suite for the city showcase curation theme face
(BigDomain R1751; canon = explore-queue curation line: themed
curation = multi-showcase grouping + themed tour ordering; pure
read grouping, zero token face, zero UPDATE carried over).
Asserts the pre-registered criteria AC-CU1..CU7 from the R1751
explore-queue row (criteria were registered before this code
existed; honesty law) plus the R1753 theme heat board criteria
AC-HB1..HB5 (hot_board pure-read derived ranking, registered
before the face existed) plus the R1770 board rank-change diff
criteria AC-HD1..HD7 (hot_board_delta movement face over two
caller-held snapshots, registered before the face existed).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Usage: python test_curation.py
"""

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
import collectibles as C              # noqa: E402 (R619 owner face)
import showcase as S                  # noqa: E402 (R1750 parent face)
import curation as CU                 # noqa: E402 (R1751 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, ref)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the themed curation is a"
              " display feature, not investment advice")

BANNED_VERBS = ("trade", "sell", "buy", "auction", "swap", "gift")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_cu_error(fn, *codes):
    try:
        fn()
    except CU.CurationError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="curation-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    cu_path = os.path.join(tmp, "curation.db")

    led = L.Ledger(db_path, cfg)
    cf = C.CollectiblesFace(led)
    gate = SecGate.from_config(lobby_cfg)
    sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
    cu = CU.CurationFace(sh, DISCLAIMER, cu_path)

    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    cl_a = cf.issue_certificate("usr:alice", "evt-tower",
                                "tower-cert")["cl_id"]
    cl_b = cf.issue_certificate("usr:bob", "evt-bridge",
                                "bridge-cert")["cl_id"]
    cl_c = cf.issue_certificate("usr:carol", "evt-harbor",
                                "harbor-cert")["cl_id"]
    cl_a2 = cf.issue_certificate("usr:alice", "evt-lamp",
                                 "lamp-cert")["cl_id"]
    sh.register_showcase("city-hall", "City Hall Window", 3, False)
    sh.register_showcase("east-wing", "East Wing Window", 3, True)
    sh.place_exhibit("usr:alice", "city-hall", cl_a, "tower lamp")
    sh.place_exhibit("usr:bob", "city-hall", cl_b, "bridge arch")
    sh.place_exhibit("usr:carol", "east-wing", cl_c, "harbor light")
    conn = sqlite3.connect(db_path)
    shconn = sqlite3.connect(sh_path)
    cuconn = sqlite3.connect(cu_path)

    # -- AC-CU1 curation registry face --------------------------------------
    r1 = cu.register_curation("heritage-route", "Heritage Route",
                             ["city-hall", "east-wing"], False)
    ok_dup, code_dup = expect_cu_error(
        lambda: cu.register_curation("heritage-route", "Again",
                                     ["city-hall"], False),
        CU.E_CU_DUP_CURATION)
    rows1 = cuconn.execute(
        "SELECT position, showcase_id FROM curation_members WHERE"
        " curation_id = ? ORDER BY position",
        ("heritage-route",)).fetchall()
    bad1 = []
    raised1 = True
    for label, fn in (
            ("empty id", lambda: cu.register_curation(
                "  ", "t", ["city-hall"], False)),
            ("empty title", lambda: cu.register_curation(
                "k1", "  ", ["city-hall"], False)),
            ("str not list", lambda: cu.register_curation(
                "k2", "t", "city-hall", False)),
            ("empty list", lambda: cu.register_curation(
                "k3", "t", [], False)),
            ("dup entries", lambda: cu.register_curation(
                "k4", "t", ["city-hall", "city-hall"], False)),
            ("empty member id", lambda: cu.register_curation(
                "k5", "t", ["city-hall", "  "], False)),
            ("non-bool ai flag", lambda: cu.register_curation(
                "k6", "t", ["city-hall"], "yes"))):
        ok_one, got = expect_cu_error(fn, CU.E_CU_BAD_ARGS)
        if ok_one:
            bad1.append("%s=%s" % (label, got))
        else:
            bad1.append("%s NOT-RAISED(%s)" % (label, got))
            raised1 = False
    n_cu1 = _count(cuconn, "curations")
    n_mem1 = _count(cuconn, "curation_members")
    ok1 = (r1["curation_id"] == "heritage-route"
           and r1["showcase_ids"] == ["city-hall", "east-wing"]
           and r1["ai_label"] == 0
           and r1["disclaimer"] == DISCLAIMER
           and ok_dup and code_dup == CU.E_CU_DUP_CURATION
           and rows1 == [(1, "city-hall"), (2, "east-wing")]
           and raised1 and n_cu1 == 1 and n_mem1 == 2)
    record("AC-CU1", ok1, "register writes one registry row + member"
          " rows in registered order %s; dup refused %s; all %d bad"
          " args rejected (%s); counts curations=%d members=%d"
          % (rows1, code_dup, len(bad1), "; ".join(bad1),
             n_cu1, n_mem1))

    # -- AC-CU2 member existence gate (fail-closed) --------------------------
    n_sh_before = _count(shconn, "showcases")
    n_cu_before = _count(cuconn, "curations")
    ok_unk, code_unk = expect_cu_error(
        lambda: cu.register_curation("bad-route", "Bad Route",
                                     ["city-hall", "no-such-window"],
                                     False),
        CU.E_CU_UNKNOWN_SHOWCASE)
    n_cu_after = _count(cuconn, "curations")
    n_mem_after = _count(cuconn, "curation_members")
    bad_members = cuconn.execute(
        "SELECT COUNT(*) FROM curation_members WHERE curation_id ="
        " 'bad-route'").fetchone()[0]
    r_night = cu.register_curation("night-route", "Night Route",
                                   ["east-wing"], True)
    n_sh_check = _count(shconn, "showcases")
    ok2 = (ok_unk and code_unk == CU.E_CU_UNKNOWN_SHOWCASE
           and n_cu_after == n_cu_before and n_mem_after == n_mem1
           and bad_members == 0
           and n_sh_check == n_sh_before
           and r_night["curation_id"] == "night-route")
    record("AC-CU2", ok2, "unknown showcase member refuses the whole"
          " registration %s with zero rows (curations %d==%d,"
          " members for bad-route=%d); showcase rows untouched"
          " (%d==%d); later valid registration succeeds (night-route)"
          % (code_unk, n_cu_after, n_cu_before, bad_members,
             n_sh_check, n_sh_before))

    # -- AC-CU3 themed tour with global stop numbering -----------------------
    n_tx0 = _count(conn, "ledger_tx")
    tour1 = cu.curation_tour("heritage-route")
    n_tx1 = _count(conn, "ledger_tx")
    stops1 = [(s["stop"], s["showcase_id"], s["cl_id"])
              for s in tour1["stops"]]
    sh.place_exhibit("usr:alice", "east-wing", cl_a2,
                     "ai authored lamp")
    tour2 = cu.curation_tour("heritage-route")
    n_tx2 = _count(conn, "ledger_tx")
    stops2 = [(s["stop"], s["showcase_id"], s["cl_id"])
              for s in tour2["stops"]]
    tour_sh1 = sh.chronicle_tour("city-hall")
    tour_sh2 = sh.chronicle_tour("east-wing")
    expected2 = ([(i + 1, "city-hall", s["cl_id"])
                  for i, s in enumerate(tour_sh1["stops"])]
                 + [(len(tour_sh1["stops"]) + i + 1, "east-wing",
                     s["cl_id"])
                    for i, s in enumerate(tour_sh2["stops"])])
    ok3 = (stops1 == [(1, "city-hall", cl_a), (2, "city-hall", cl_b),
                      (3, "east-wing", cl_c)]
           and len(tour2["stops"]) == len(tour1["stops"]) + 1
           and stops2 == expected2
           and n_tx0 == n_tx1 == n_tx2
           and all(s.get("ai_label") in (0, 1)
                   for s in tour2["stops"]))
    record("AC-CU3", ok3, "tour walks member showcases in registered"
          " order with GLOBAL stop numbering 1..N across showcases"
          " %s; live derivation: a placement registered after the"
          " curation appears on the next tour (%d -> %d stops); pure"
          " read zero token movement (ledger_tx %d==%d==%d)"
          % (stops1, len(tour1["stops"]), len(tour2["stops"]),
             n_tx0, n_tx1, n_tx2))

    # -- AC-CU4 immutable grouping (append-only, no mutation API) ------------
    no_mutation_api = all(not hasattr(cu, m) for m in
                          ("remove_member", "reorder_members",
                           "update_curation", "delete_curation"))
    rows4 = cuconn.execute(
        "SELECT position, showcase_id FROM curation_members WHERE"
        " curation_id = ? ORDER BY position",
        ("heritage-route",)).fetchall()
    with open(os.path.join(BASE, "curation.py"), "rb") as h:
        cu_src = h.read().decode("ascii")
    update_hits = [w for w in ("UPDATE curations",
                               "UPDATE curation_members")
                   if w in cu_src]
    ok4 = (no_mutation_api
           and rows4 == [(1, "city-hall"), (2, "east-wing")]
           and not update_hits)
    record("AC-CU4", ok4, "no member-removal/reorder/update/delete"
          " API on the face (%s); membership immutable after all"
          " operations %s; zero UPDATE surface in source (%s)"
          % (no_mutation_api, rows4, update_hits))

    # -- AC-CU5 AIGC label + resident disclaimer -----------------------------
    ok_nd, code_nd = expect_cu_error(
        lambda: CU.CurationFace(sh, "  ", os.path.join(
            tmp, "curation-nodisclaimer.db")),
        CU.E_CU_NO_DISCLAIMER)
    r_ai = cu.register_curation("ai-route", "AI Route",
                                ["city-hall"], True)
    ai_row = cuconn.execute(
        "SELECT ai_label FROM curations WHERE curation_id ="
        " 'ai-route'").fetchone()
    label_rejected = []
    try:
        cuconn.execute(
            "INSERT INTO curations VALUES ('x','t',2,'t')")
        cuconn.commit()
    except sqlite3.IntegrityError:
        cuconn.rollback()
        label_rejected.append(True)
    else:
        label_rejected.append(False)
    view5 = cu.curation_view("heritage-route")
    board5 = cu.active_curations()
    envelopes = (r1, r_night, r_ai, tour2, view5, board5)
    all_disclaimer = all(e.get("disclaimer") == DISCLAIMER
                         for e in envelopes)
    ok5 = (ok_nd and code_nd == CU.E_CU_NO_DISCLAIMER
           and r_ai["ai_label"] == 1
           and ai_row is not None and int(ai_row[0]) == 1
           and view5["ai_label"] == 0
           and all_disclaimer and all(label_rejected))
    record("AC-CU5", ok5, "empty disclaimer refuses construction %s;"
          " declared ai_label persists (%d on row, shown in register"
          " and view envelopes); every envelope (register/view/tour/"
          "board) carries the resident disclaimer (%s); direct SQL"
          " ai_label=2 refused by the CHECK (%s)"
          % (code_nd, int(ai_row[0]), all_disclaimer,
             label_rejected))

    # -- AC-CU6 read faces ----------------------------------------------------
    n_cu6a, n_mem6a = _count(cuconn, "curations"), _count(
        cuconn, "curation_members")
    view6 = cu.curation_view("heritage-route")
    board6 = cu.active_curations()
    ok_unk_view, code_uv = expect_cu_error(
        lambda: cu.curation_view("no-such-curation"),
        CU.E_CU_UNKNOWN_CURATION)
    ok_unk_tour, code_ut = expect_cu_error(
        lambda: cu.curation_tour("no-such-curation"),
        CU.E_CU_UNKNOWN_CURATION)
    n_cu6b, n_mem6b = _count(cuconn, "curations"), _count(
        cuconn, "curation_members")
    members6 = [(m["position"], m["showcase_id"], m["on_display"])
                for m in view6["members"]]
    board_ids = [b["curation_id"] for b in board6["curations"]]
    board_counts = [b["member_count"] for b in board6["curations"]]
    ok6 = (members6 == [(1, "city-hall", 2), (2, "east-wing", 2)]
           and view6["title"] == "Heritage Route"
           and board_ids == ["heritage-route", "night-route",
                             "ai-route"]
           and board_counts == [2, 1, 1]
           and ok_unk_view and code_uv == CU.E_CU_UNKNOWN_CURATION
           and ok_unk_tour and code_ut == CU.E_CU_UNKNOWN_CURATION
           and n_cu6a == n_cu6b and n_mem6a == n_mem6b)
    record("AC-CU6", ok6, "view lists members with live on-display"
          " counts %s; board lists all curations %s with member"
          " counts %s; unknown curation refused on view %s and tour"
          " %s; all reads pure (rows %d==%d, %d==%d)"
          % (members6, board_ids, board_counts, code_uv, code_ut,
             n_cu6a, n_cu6b, n_mem6a, n_mem6b))

    # -- AC-CU7 hard laws: bad args, hygiene, zero-write posture -------------
    counts0 = (_count(cuconn, "curations"),
               _count(cuconn, "curation_members"))
    bad7 = []
    raised7 = True
    for label, fn, code in (
            ("unknown curation register member", lambda:
             cu.register_curation("k7", "t", ["city-hall",
                                              "ghost-window"], False),
             CU.E_CU_UNKNOWN_SHOWCASE),
            ("unknown curation view", lambda: cu.curation_view(
                "ghost-route"), CU.E_CU_UNKNOWN_CURATION),
            ("unknown curation tour", lambda: cu.curation_tour(
                "ghost-route"), CU.E_CU_UNKNOWN_CURATION)):
        ok_one, got = expect_cu_error(fn, code)
        if ok_one:
            bad7.append("%s=%s" % (label, got))
        else:
            bad7.append("%s NOT-RAISED(%s)" % (label, got))
            raised7 = False
    counts1 = (_count(cuconn, "curations"),
               _count(cuconn, "curation_members"))
    non_ascii = sum(1 for ch in cu_src if ord(ch) > 127)
    net_imports = [ln for ln in cu_src.splitlines()
                   if (ln.startswith("import ") or ln.startswith("from "))
                   and any(w in ln for w in
                           ("urllib", "requests", "socket", "http"))]
    banned_hits = [w for w in BANNED_VERBS if w in cu_src]
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_after = h.read()
    ok7 = (raised7 and counts0 == counts1 and non_ascii == 0
           and not net_imports and not banned_hits
           and not update_hits and "random" not in cu_src
           and cfg_after == cfg_bytes)
    record("AC-CU7", ok7, "all %d fault paths rejected (%s); zero side"
          " effects (rows %s unchanged); module pure ASCII (%d"
          " non-ascii); zero network imports (%d); zero banned"
          " circulation verbs in source (%s); zero UPDATE surface"
          " (%s); zero RNG; shipped config.json byte-stable"
          % (len(bad7), "; ".join(bad7), counts0, non_ascii,
             len(net_imports), banned_hits, update_hits))

    # -- AC-HB1..HB5 theme heat board (R1753) -------------------------------
    cu_empty = CU.CurationFace(sh, DISCLAIMER, os.path.join(
        tmp, "curation-hb-empty.db"))
    empty_board = cu_empty.hot_board()
    cu_empty.close()
    ok_hb_empty = empty_board == {"hot_board": [],
                                  "disclaimer": DISCLAIMER}

    sh.register_showcase("west-wing", "West Wing Window", 3, False)
    cu.register_curation("zeta-route", "Zeta Route",
                         ["west-wing"], False)
    cu.register_curation("alpha-route", "Alpha Route",
                         ["west-wing"], True)
    board0 = cu.hot_board()
    rows0 = [(b["rank"], b["curation_id"], b["displayed_total"])
             for b in board0["hot_board"]]
    key_ok = all(set(b.keys()) == {"rank", "curation_id", "title",
                                   "ai_label", "member_count",
                                   "displayed_total"}
                 for b in board0["hot_board"])
    ok_hb1 = (ok_hb_empty and set(board0.keys()) ==
              {"hot_board", "disclaimer"} and key_ok
              and rows0 == [(1, "heritage-route", 4),
                            (2, "ai-route", 2),
                            (3, "night-route", 2),
                            (4, "alpha-route", 0),
                            (5, "zeta-route", 0)])
    record("AC-HB1", ok_hb1, "hot board lists every curation ranked"
          " by member on-display totals %s with a fixed row key set;"
          " envelope carries only hot_board + disclaimer; a face"
          " over an empty registry returns an honest empty board"
          " (%s)" % (rows0, ok_hb_empty))

    board0b = cu.hot_board()
    dump_a = json.dumps(board0, sort_keys=True, ensure_ascii=True)
    dump_b = json.dumps(board0b, sort_keys=True, ensure_ascii=True)
    ok_hb2 = (dump_a == dump_b
              and [r[1] for r in rows0] == [
                  "heritage-route", "ai-route", "night-route",
                  "alpha-route", "zeta-route"]
              and [r[2] for r in rows0] == [4, 2, 2, 0, 0])
    record("AC-HB2", ok_hb2, "deterministic sort key (-displayed"
          "_total, curation_id): heat DESC with curation_id ASC"
          " tie-break (ai-route before night-route at heat 2;"
          " alpha-route before zeta-route at heat 0 although zeta"
          " was registered first - zero insertion-order keys); two"
          " calls serialize byte-identical (%s)"
          % ("identical" if dump_a == dump_b else "DRIFT"))

    manual = {
        "heritage-route": (
            len(sh.showcase_view("city-hall")["displayed"])
            + len(sh.showcase_view("east-wing")["displayed"])),
        "ai-route": len(sh.showcase_view("city-hall")["displayed"]),
        "night-route": len(
            sh.showcase_view("east-wing")["displayed"]),
        "alpha-route": len(
            sh.showcase_view("west-wing")["displayed"]),
        "zeta-route": len(
            sh.showcase_view("west-wing")["displayed"])}
    cross0 = all(b["displayed_total"] == manual[b["curation_id"]]
                 for b in board0["hot_board"])
    led.ensure_account("usr:dave", census_avatar_id="dave")
    cl_d1 = cf.issue_certificate("usr:dave", "evt-gate",
                                 "gate-cert-1")["cl_id"]
    cl_d2 = cf.issue_certificate("usr:dave", "evt-bell",
                                 "gate-cert-2")["cl_id"]
    cl_d3 = cf.issue_certificate("usr:dave", "evt-sign",
                                 "gate-cert-3")["cl_id"]
    sh.place_exhibit("usr:dave", "west-wing", cl_d1, "gate lamp")
    sh.place_exhibit("usr:dave", "west-wing", cl_d2, "gate bell")
    sh.place_exhibit("usr:dave", "west-wing", cl_d3, "gate sign")
    board1 = cu.hot_board()
    rows1 = [(b["rank"], b["curation_id"], b["displayed_total"])
             for b in board1["hot_board"]]
    sh.retract_exhibit("usr:dave", "west-wing", cl_d2)
    board2 = cu.hot_board()
    rows2 = [(b["rank"], b["curation_id"], b["displayed_total"])
             for b in board2["hot_board"]]
    ok_hb3 = (cross0
              and rows1 == [(1, "heritage-route", 4),
                            (2, "alpha-route", 3),
                            (3, "zeta-route", 3),
                            (4, "ai-route", 2),
                            (5, "night-route", 2)]
              and rows2 == [(1, "heritage-route", 4),
                            (2, "ai-route", 2),
                            (3, "alpha-route", 2),
                            (4, "night-route", 2),
                            (5, "zeta-route", 2)])
    record("AC-HB3", ok_hb3, "heat equals the manual ShowcaseFace"
          " on-display sums per curation (cross-module check %s);"
          " live derivation with zero cached counters: placements"
          " lift alpha/zeta 0 -> 3 and reorder the board %s; one"
          " retraction drops them back to 2 and the four-way tie"
          " re-resolves by id %s" % (cross0, rows1, rows2))

    counts_a = (_count(conn, "ledger_tx"),
                _count(cuconn, "curations"),
                _count(cuconn, "curation_members"),
                _count(shconn, "showcases"),
                _count(shconn, "exhibit_events"))
    board3 = cu.hot_board()
    board4 = cu.hot_board()
    counts_b = (_count(conn, "ledger_tx"),
                _count(cuconn, "curations"),
                _count(cuconn, "curation_members"),
                _count(shconn, "showcases"),
                _count(shconn, "exhibit_events"))
    hb_seg = cu_src[cu_src.index("def hot_board"):]
    write_words = [w for w in ("INSERT INTO", "UPDATE ", "DELETE ")
                   if w in hb_seg]
    ok_hb4 = (counts_a == counts_b and not write_words
              and board3 == board4)
    record("AC-HB4", ok_hb4, "pure read: repeated board reads leave"
          " ledger_tx and every showcase/curation row count"
          " unchanged %s == %s; the hot_board method body carries"
          " zero write statements (%s)"
          % (counts_a, counts_b, write_words))

    labels = {b["curation_id"]: b["ai_label"]
              for b in board4["hot_board"]}
    expected_labels = {"heritage-route": 0, "ai-route": 1,
                       "night-route": 1, "alpha-route": 1,
                       "zeta-route": 0}
    non_ascii_hb = sum(1 for ch in cu_src if ord(ch) > 127)
    banned_hits_hb = [w for w in BANNED_VERBS if w in cu_src]
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_final = h.read()
    ok_hb5 = (labels == expected_labels
              and board4["disclaimer"] == DISCLAIMER
              and non_ascii_hb == 0 and not net_imports
              and not banned_hits_hb and "random" not in cu_src
              and cfg_final == cfg_bytes)
    record("AC-HB5", ok_hb5, "board rows carry the registered"
          " ai_label persistently %s; envelope disclaimer resident;"
          " module stays pure ASCII (%d non-ascii chars), zero"
          " network imports, zero circulation verbs, zero RNG, zero"
          " UPDATE surface, shipped config.json byte-stable"
          % (labels, non_ascii_hb))

    # -- AC-HD1..HD7 board rank-change diff (R1770) --------------------------
    snap1 = cu.hot_board()
    counts_hd0 = (_count(conn, "ledger_tx"),
                  _count(cuconn, "curations"),
                  _count(cuconn, "curation_members"),
                  _count(shconn, "showcases"),
                  _count(shconn, "exhibit_events"))
    bad_hd1 = []
    raised_hd1 = True
    for label, payload in (
            ("str input", "a board"),
            ("int input", 42),
            ("None input", None),
            ("envelope missing hot_board", {"title": "x"}),
            ("envelope hot_board not list", {"hot_board": "x"}),
            ("row not dict", ["x"]),
            ("row missing curation_id", [{"rank": 1}]),
            ("row empty curation_id", [{"curation_id": "  ",
                                        "rank": 1}]),
            ("row non-str curation_id", [{"curation_id": 7,
                                          "rank": 1}]),
            ("row rank bool", [{"curation_id": "x", "rank": True}]),
            ("row rank zero", [{"curation_id": "x", "rank": 0}]),
            ("row rank negative", [{"curation_id": "x",
                                   "rank": -1}]),
            ("row rank str", [{"curation_id": "x", "rank": "1"}]),
            ("row rank missing", [{"curation_id": "x"}]),
            ("duplicate prev ids", [{"curation_id": "x", "rank": 1},
                                     {"curation_id": "x",
                                      "rank": 2}])):
        ok_one, got = expect_cu_error(
            lambda p=payload: cu.hot_board_delta(p), CU.E_CU_BAD_ARGS)
        if ok_one:
            bad_hd1.append("%s=%s" % (label, got))
        else:
            bad_hd1.append("%s NOT-RAISED(%s)" % (label, got))
            raised_hd1 = False
    counts_hd1 = (_count(conn, "ledger_tx"),
                  _count(cuconn, "curations"),
                  _count(cuconn, "curation_members"),
                  _count(shconn, "showcases"),
                  _count(shconn, "exhibit_events"))
    ok_hd1 = (raised_hd1 and counts_hd0 == counts_hd1)
    record("AC-HD1", ok_hd1, "all %d bad prev-board forms rejected"
          " with %s (%s); zero side effects across the battery"
          " (counts %s unchanged)" % (len(bad_hd1),
                                      CU.E_CU_BAD_ARGS,
                                      "; ".join(bad_hd1),
                                      counts_hd0))

    # world actions between snapshots: one placement (moves heat)
    # plus one fresh registration (board entry)
    led.ensure_account("usr:erin", census_avatar_id="erin")
    cl_e = cf.issue_certificate("usr:erin", "evt-moon",
                               "moon-cert")["cl_id"]
    sh.place_exhibit("usr:erin", "west-wing", cl_e, "moon lamp")
    cu.register_curation("newest-route", "Newest Route",
                         ["city-hall"], True)
    counts_hdA = (_count(conn, "ledger_tx"),
                  _count(cuconn, "curations"),
                  _count(cuconn, "curation_members"),
                  _count(shconn, "showcases"),
                  _count(shconn, "exhibit_events"))
    delta1 = cu.hot_board_delta(snap1)
    delta1b = cu.hot_board_delta(snap1)
    delta1_list = cu.hot_board_delta(snap1["hot_board"])
    delta1_tuple = cu.hot_board_delta(tuple(snap1["hot_board"]))
    ghost_rows = snap1["hot_board"] + [
        {"curation_id": "ghost-route", "rank": 3, "ai_label": 1},
        {"curation_id": "ghost-plain", "rank": 4},
        {"curation_id": "ghost-badlabel", "rank": 5,
         "ai_label": "x"}]
    delta_ghost = cu.hot_board_delta({"hot_board": ghost_rows})
    snap_now = cu.hot_board()
    delta_steady = cu.hot_board_delta(snap_now)
    delta_empty = cu.hot_board_delta({"hot_board": []})
    counts_hdB = (_count(conn, "ledger_tx"),
                  _count(cuconn, "curations"),
                  _count(cuconn, "curation_members"),
                  _count(shconn, "showcases"),
                  _count(shconn, "exhibit_events"))

    def _row(cid, ai, state, prank, crank, dlt):
        return {"curation_id": cid, "ai_label": ai, "state": state,
                "prev_rank": prank, "current_rank": crank,
                "delta": dlt}

    expected1 = [
        _row("alpha-route", 1, "rise", 3, 2, 1),
        _row("zeta-route", 0, "rise", 5, 3, 2),
        _row("ai-route", 1, "fall", 2, 4, -2),
        _row("night-route", 1, "fall", 4, 6, -2),
        _row("newest-route", 1, "entered", None, 5, None)]
    keys_hd = {"curation_id", "ai_label", "state", "prev_rank",
               "current_rank", "delta"}
    key_ok_hd = all(set(r.keys()) == keys_hd
                    for r in delta1["hot_board_delta"]
                    + delta_ghost["hot_board_delta"]
                    + delta_empty["hot_board_delta"])
    steady_ok = delta_steady == {"hot_board_delta": [],
                                 "disclaimer": DISCLAIMER}
    omitted_ok = ("heritage-route" not in
                  [r["curation_id"]
                   for r in delta1["hot_board_delta"]])
    expected_ghost = expected1 + [
        _row("ghost-route", 1, "dropped", 3, None, None),
        _row("ghost-plain", None, "dropped", 4, None, None),
        _row("ghost-badlabel", None, "dropped", 5, None, None)]
    expected_empty = [
        _row("heritage-route", 0, "entered", None, 1, None),
        _row("alpha-route", 1, "entered", None, 2, None),
        _row("zeta-route", 0, "entered", None, 3, None),
        _row("ai-route", 1, "entered", None, 4, None),
        _row("newest-route", 1, "entered", None, 5, None),
        _row("night-route", 1, "entered", None, 6, None)]
    ok_hd2 = (delta1 == {"hot_board_delta": expected1,
                         "disclaimer": DISCLAIMER}
              and delta_ghost == {"hot_board_delta": expected_ghost,
                                  "disclaimer": DISCLAIMER}
              and delta_empty == {"hot_board_delta": expected_empty,
                                  "disclaimer": DISCLAIMER}
              and key_ok_hd and steady_ok and omitted_ok)
    record("AC-HD2", ok_hd2, "four-state diff over the live tie"
          " world: rise rows %s; fall rows %s; entered row newest-"
          "route; ghost snapshot rows derive dropped (in-world"
          " registry is append-only so a drop needs a caller"
          " cross-world snapshot - honest derivation, zero"
          " fabrication); steady heritage-route omitted; fully-"
          "steady world returns an honest empty delta (%s); row"
          " key set exact" % (
              [(r["curation_id"], r["prev_rank"], r["current_rank"],
                r["delta"]) for r in expected1 if r["state"] in
               ("rise", "fall")][:2],
              [(r["curation_id"], r["prev_rank"], r["current_rank"],
                r["delta"]) for r in expected1 if r["state"] ==
               "fall"],
              steady_ok))

    live_pre = cu.hot_board()
    live_map = {b["curation_id"]: b for b in live_pre["hot_board"]}
    cross_hd = True
    for row in (delta1["hot_board_delta"]
                + delta_ghost["hot_board_delta"]
                + delta_empty["hot_board_delta"]):
        cid = row["curation_id"]
        if row["state"] == "dropped":
            if cid in live_map:
                cross_hd = False
            continue
        if (row["current_rank"] != live_map[cid]["rank"]
                or row["ai_label"] != live_map[cid]["ai_label"]):
            cross_hd = False
        if row["state"] in ("rise", "fall"):
            if row["delta"] != (row["prev_rank"]
                                - row["current_rank"]):
                cross_hd = False
    src_hd = inspect.getsource(CU.CurationFace.hot_board_delta)
    single_source = ("self.hot_board()" in src_hd
                     and "showcase_view" not in src_hd
                     and "displayed" not in src_hd)
    ok_hd3 = cross_hd and single_source
    record("AC-HD3", ok_hd3, "every current-side delta row matches"
          " the live hot_board re-derivation (rank + ai_label) and"
          " rise/fall delta == prev_rank - current_rank (%s); the"
          " method body carries the self.hot_board() call and zero"
          " direct showcase reads (%s) - no second aggregation"
          " engine" % (cross_hd, single_source))

    sh.retract_exhibit("usr:erin", "west-wing", cl_e)
    delta2 = cu.hot_board_delta(snap1)
    delta2b = cu.hot_board_delta(snap1)
    counts_hdC = (_count(conn, "ledger_tx"),
                  _count(cuconn, "curations"),
                  _count(cuconn, "curation_members"),
                  _count(shconn, "showcases"),
                  _count(shconn, "exhibit_events"))
    delta2c = cu.hot_board_delta(snap1)
    counts_hdD = (_count(conn, "ledger_tx"),
                  _count(cuconn, "curations"),
                  _count(cuconn, "curation_members"),
                  _count(shconn, "showcases"),
                  _count(shconn, "exhibit_events"))
    live_post = cu.hot_board()
    post_map = {b["curation_id"]: b
                for b in live_post["hot_board"]}
    expected2 = [
        _row("night-route", 1, "fall", 4, 5, -1),
        _row("zeta-route", 0, "fall", 5, 6, -1),
        _row("newest-route", 1, "entered", None, 4, None)]
    flip = None
    for row in delta2["hot_board_delta"]:
        if row["curation_id"] == "zeta-route":
            flip = row["delta"]
    states_ghost = [r["state"]
                    for r in delta_ghost["hot_board_delta"]]
    order_ok = (states_ghost == ["rise", "rise", "fall", "fall",
                                 "entered", "dropped", "dropped",
                                 "dropped"]
                and [r["current_rank"] for r in
                     delta_ghost["hot_board_delta"]
                     if r["state"] == "rise"]
                == sorted(r["current_rank"] for r in
                          delta_ghost["hot_board_delta"]
                          if r["state"] == "rise")
                and [r["current_rank"] for r in
                     delta_ghost["hot_board_delta"]
                     if r["state"] == "fall"]
                == sorted(r["current_rank"] for r in
                          delta_ghost["hot_board_delta"]
                          if r["state"] == "fall")
                and [r["prev_rank"] for r in
                     delta_ghost["hot_board_delta"]
                     if r["state"] == "dropped"]
                == sorted(r["prev_rank"] for r in
                          delta_ghost["hot_board_delta"]
                          if r["state"] == "dropped"))
    dump_d1 = json.dumps(delta1, sort_keys=True, ensure_ascii=True)
    dump_d1b = json.dumps(delta1b, sort_keys=True,
                          ensure_ascii=True)
    dump_d1l = json.dumps(delta1_list, sort_keys=True,
                          ensure_ascii=True)
    dump_d1t = json.dumps(delta1_tuple, sort_keys=True,
                          ensure_ascii=True)
    dump_d2 = json.dumps(delta2, sort_keys=True, ensure_ascii=True)
    dump_d2b = json.dumps(delta2b, sort_keys=True,
                          ensure_ascii=True)
    ok_hd4 = (dump_d1 == dump_d1b == dump_d1l == dump_d1t
              and dump_d2 == dump_d2b
              and delta2 == {"hot_board_delta": expected2,
                            "disclaimer": DISCLAIMER}
              and flip == -1 and order_ok
              and all(r["current_rank"] == post_map[
                  r["curation_id"]]["rank"]
                  for r in delta2["hot_board_delta"]
                  if r["state"] != "dropped"))
    record("AC-HD4", ok_hd4, "live derivation: after the retraction"
          " the same prev snapshot re-reads a changed board - zeta-"
          "route flips rise(+2) to fall(%s) and alpha/ai return to"
          " steady-omitted; two calls serialize byte-identical and"
          " the envelope/bare-list/tuple input forms agree; row"
          " order = state groups rise->fall->entered->dropped with"
          " ascending rank inside each group (%s)"
          % (flip, order_ok))

    write_words_hd = [w for w in ("INSERT INTO", "UPDATE ",
                                  "DELETE ") if w in src_hd]
    tables_hd = set(r[0] for r in cuconn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall())
    ok_hd5 = (counts_hdA == counts_hdB and counts_hdC == counts_hdD
              and not write_words_hd
              and tables_hd == {"curations", "curation_members"})
    record("AC-HD5", ok_hd5, "pure read: the full delta battery"
          " leaves ledger_tx and every curation/showcase row count"
          " unchanged (%s == %s; %s == %s); method source carries"
          " zero write statements (%s); zero new tables - the"
          " curation.db table set stays %s (zero-storage face)"
          % (counts_hdA, counts_hdB, counts_hdC, counts_hdD,
             write_words_hd, sorted(tables_hd)))

    envelopes_hd = (delta1, delta1_list, delta_ghost, delta_steady,
                    delta_empty, delta2)
    all_disclaimer_hd = all(e.get("disclaimer") == DISCLAIMER
                            for e in envelopes_hd)
    dropped_rows = [r for r in delta_ghost["hot_board_delta"]
                    if r["state"] == "dropped"]
    label_map = {r["curation_id"]: r["ai_label"]
                 for r in delta1["hot_board_delta"]}
    ok_hd6 = (all_disclaimer_hd
              and label_map == {"alpha-route": 1, "zeta-route": 0,
                                "ai-route": 1, "night-route": 1,
                                "newest-route": 1}
              and dropped_rows == [
                  _row("ghost-route", 1, "dropped", 3, None, None),
                  _row("ghost-plain", None, "dropped", 4, None,
                       None),
                  _row("ghost-badlabel", None, "dropped", 5, None,
                       None)])
    record("AC-HD6", ok_hd6, "every delta envelope carries the"
          " resident disclaimer (%s); current-side rows carry the"
          " registered ai_label %s; dropped rows carry the prev"
          " row's int ai_label and fall back to an honest None for"
          " missing/non-int labels %s"
          % (all_disclaimer_hd, label_map,
             [(r["curation_id"], r["ai_label"])
              for r in dropped_rows]))

    non_ascii_hd = sum(1 for ch in cu_src if ord(ch) > 127)
    banned_hits_hd = [w for w in BANNED_VERBS if w in cu_src]
    update_hits_hd = [w for w in ("UPDATE curations",
                                  "UPDATE curation_members")
                      if w in cu_src]
    no_snapshot_api = all(not hasattr(cu, m) for m in
                          ("store_board", "save_snapshot",
                           "snapshot"))
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_hd = h.read()
    ok_hd7 = (non_ascii_hd == 0 and not banned_hits_hd
              and not update_hits_hd and "random" not in cu_src
              and not net_imports and cfg_hd == cfg_bytes
              and no_snapshot_api)
    record("AC-HD7", ok_hd7, "hard laws carry over: module pure"
          " ASCII (%d non-ascii), zero UPDATE surface (%s), zero"
          " RNG, zero circulation verbs (%s), zero network"
          " imports, shipped config.json byte-stable, zero"
          " snapshot-persistence API on the face (%s)"
          % (non_ascii_hd, update_hits_hd, banned_hits_hd,
             no_snapshot_api))

    conn.close()
    shconn.close()
    cuconn.close()
    cu.close()
    sh.close()
    cf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
