"""Acceptance suite for the city showcase curation theme face
(BigDomain R1751; canon = explore-queue curation line: themed
curation = multi-showcase grouping + themed tour ordering; pure
read grouping, zero token face, zero UPDATE carried over).
Asserts the pre-registered criteria AC-CU1..CU7 from the R1751
explore-queue row (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Usage: python test_curation.py
"""

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
