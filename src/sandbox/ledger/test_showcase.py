"""Acceptance suite for the city digital-collectibles public
showcase face (BigDomain R1750; canon = explore-queue showcase line:
public display windows + the chronicle walkthrough domain, inside the
collectibles no-trading hard law; seed = the R619 three-domain
collectibles face). Asserts the pre-registered criteria AC-SH1..SH7
from the R1750 explore-queue row (criteria were registered before
this code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

The content gate is the lobby SecGate product injected by reference
(no copy): its Chinese wordlists are data loaded from the lobby
config at runtime - this test source stays pure ASCII per the
encoding discipline.

Usage: python test_showcase.py
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
import showcase as S                  # noqa: E402 (R1750 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, ref)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the public showcase is a"
              " display feature, not investment advice")

BANNED_VERBS = ("trade", "sell", "buy", "auction", "swap", "gift")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_sh_error(fn, *codes):
    try:
        fn()
    except S.ShowcaseError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


class _FaultGate(object):
    """Runtime-fault gate stub: check_text always blows up (the face
    must map this to E_SH_GATE_ERROR and never silently pass - the
    AC-SH3 fail-closed posture)."""

    def check_text(self, text):
        raise RuntimeError("stub gate offline")


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="showcase-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    bad_word = lobby_cfg["gate"]["forbidden_words"][0]
    advisory_word = lobby_cfg["gate"]["advisory_ban_words"][0]
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    fault_path = os.path.join(tmp, "showcase-fault.db")

    led = L.Ledger(db_path, cfg)
    cf = C.CollectiblesFace(led)
    gate = SecGate.from_config(lobby_cfg)
    sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)

    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    a_cert = cf.issue_certificate("usr:alice", "evt-tower", "tower-cert")
    b_cert = cf.issue_certificate("usr:bob", "evt-bridge", "bridge-cert")
    c_cert = cf.issue_certificate("usr:carol", "evt-harbor", "harbor-cert")
    a2_cert = cf.issue_certificate("usr:alice", "evt-lamp", "lamp-cert")
    cl_a, cl_b = a_cert["cl_id"], b_cert["cl_id"]
    cl_c, cl_a2 = c_cert["cl_id"], a2_cert["cl_id"]
    conn = sqlite3.connect(db_path)
    shconn = sqlite3.connect(sh_path)
    n_cl0 = _count(conn, "collectibles")

    # -- AC-SH1 showcase registry face --------------------------------------
    r1 = sh.register_showcase("city-hall", "City Hall Window", 2, False)
    ok_dup, code_dup = expect_sh_error(
        lambda: sh.register_showcase("city-hall", "Again", 3, False),
        S.E_SH_DUP_SHOWCASE)
    n_sh1 = _count(shconn, "showcases")
    bad1 = []
    raised1 = True
    for label, fn in (
            ("empty id", lambda: sh.register_showcase(
                "  ", "t", 2, False)),
            ("empty title", lambda: sh.register_showcase(
                "k1", "  ", 2, False)),
            ("cap 0", lambda: sh.register_showcase("k2", "t", 0, False)),
            ("cap bool", lambda: sh.register_showcase(
                "k3", "t", True, False)),
            ("cap str", lambda: sh.register_showcase(
                "k4", "t", "2", False)),
            ("non-bool ai flag", lambda: sh.register_showcase(
                "k5", "t", 2, "yes"))):
        got = None
        try:
            fn()
        except S.ShowcaseError as exc:
            got = exc.code
        if got == S.E_SH_BAD_ARGS:
            bad1.append("%s=%s" % (label, got))
        else:
            bad1.append("%s NOT-RAISED(%s)" % (label, got))
            raised1 = False
    n_sh2 = _count(shconn, "showcases")
    ok_unk_v, code_uv = expect_sh_error(
        lambda: sh.showcase_view("nope"), S.E_SH_UNKNOWN_SHOWCASE)
    ok_unk_t, code_ut = expect_sh_error(
        lambda: sh.chronicle_tour("nope"), S.E_SH_UNKNOWN_SHOWCASE)
    row_label = shconn.execute(
        "SELECT ai_label FROM showcases WHERE showcase_id = ?",
        ("city-hall",)).fetchone()
    ok1 = (r1["ai_label"] == 0 and r1["slot_cap"] == 2
           and r1["disclaimer"] == DISCLAIMER and ok_dup
           and code_dup == S.E_SH_DUP_SHOWCASE and n_sh1 == 1
           and n_sh2 == 1 and raised1 and ok_unk_v and ok_unk_t
           and row_label is not None and int(row_label[0]) == 0)
    record("AC-SH1", ok1, "one registry row (%d) for a unique id;"
          " re-registration rejected %s with zero rows (%d==%d); all"
          " %d bad args rejected (%s); unknown-showcase reads"
          " rejected (%s view / %s tour); declared ai_label persists"
          " (%d) and rides the return envelope"
          % (n_sh1, code_dup, n_sh1, n_sh2, len(bad1),
             "; ".join(bad1), code_uv, code_ut, int(row_label[0])))

    # -- AC-SH2 ownership dock fail-closed ------------------------------------
    n_ev0 = _count(shconn, "exhibit_events")
    ok_unk, code_ui = expect_sh_error(
        lambda: sh.place_exhibit("usr:alice", "city-hall", 999,
                                 "clean"), S.E_SH_UNKNOWN_ITEM)
    ok_owner, code_ow = expect_sh_error(
        lambda: sh.place_exhibit("usr:alice", "city-hall", cl_b,
                                 "clean"), S.E_SH_NOT_OWNER)
    ok_svc, code_sv = expect_sh_error(
        lambda: sh.place_exhibit("pool:reserve", "city-hall", cl_a,
                                 "clean"), S.E_SH_BAD_ARGS)
    bad2 = []
    raised2 = True
    for label, fn in (
            ("bool cl id", lambda: sh.place_exhibit(
                "usr:alice", "city-hall", True, "c")),
            ("str cl id", lambda: sh.place_exhibit(
                "usr:alice", "city-hall", "x", "c")),
            ("cl id 0", lambda: sh.place_exhibit(
                "usr:alice", "city-hall", 0, "c"))):
        ok_one, got = expect_sh_error(fn, S.E_SH_BAD_ARGS)
        if ok_one:
            bad2.append("%s=%s" % (label, got))
        else:
            bad2.append("%s NOT-RAISED(%s)" % (label, got))
            raised2 = False
    n_ev1 = _count(shconn, "exhibit_events")
    n_cl1 = _count(conn, "collectibles")
    with open(os.path.join(BASE, "showcase.py"), encoding="utf-8") as h:
        sh_src = h.read()
    src_lines = sh_src.splitlines()
    dock_writes = []
    for i, ln in enumerate(src_lines):
        if "self._dock.execute" in ln:
            window = " ".join(src_lines[i:i + 3])
            if "SELECT" not in window:
                dock_writes.append(ln.strip())
    ok2 = (ok_unk and code_ui == S.E_SH_UNKNOWN_ITEM and ok_owner
           and code_ow == S.E_SH_NOT_OWNER and ok_svc
           and code_sv == S.E_SH_BAD_ARGS and raised2 and n_ev1 == n_ev0
           and n_cl1 == n_cl0 and not dock_writes)
    record("AC-SH2", ok2, "unknown cl_id rejected %s; bob's item"
          " under alice rejected %s; non-resident account rejected"
          " %s; %d bad cl_id forms rejected (%s); zero events"
          " stored (%d==%d); collectibles rows untouched (%d==%d);"
          " dock statements are SELECT-only (%d write lines)"
          % (code_ui, code_ow, code_sv, len(bad2), "; ".join(bad2),
             n_ev0, n_ev1, n_cl0, n_cl1, len(dock_writes)))

    # -- AC-SH3 msgSecCheck pre-gate -------------------------------------------
    n_ev2 = _count(shconn, "exhibit_events")
    ok_fw, code_fw = expect_sh_error(
        lambda: sh.place_exhibit("usr:alice", "city-hall", cl_a,
                                 "clean " + bad_word + " suffix"),
        S.E_SH_CONTENT_REJECTED)
    ok_adv, code_adv = expect_sh_error(
        lambda: sh.place_exhibit("usr:alice", "city-hall", cl_a,
                                 "clean " + advisory_word + " tail"),
        S.E_SH_CONTENT_REJECTED)
    n_ev3 = _count(shconn, "exhibit_events")
    ok_no_gate, code_ng = expect_sh_error(
        lambda: S.ShowcaseFace(led, None, DISCLAIMER, fault_path),
        S.E_SH_NO_GATE)
    fault_sh = S.ShowcaseFace(led, _FaultGate(), DISCLAIMER, fault_path)
    fault_sh.register_showcase("fault-win", "Fault Window", 2, False)
    ok_fault, code_fl = expect_sh_error(
        lambda: fault_sh.place_exhibit("usr:alice", "fault-win", cl_a,
                                       "clean"),
        S.E_SH_GATE_ERROR)
    fault_view = fault_sh.showcase_view("fault-win")
    clean_place = sh.place_exhibit("usr:alice", "city-hall", cl_a,
                                    "clean caption", False)
    n_ev4 = _count(shconn, "exhibit_events")
    ok3 = (ok_fw and code_fw == S.E_SH_CONTENT_REJECTED and ok_adv
           and code_adv == S.E_SH_CONTENT_REJECTED and n_ev3 == n_ev2
           and ok_no_gate and code_ng == S.E_SH_NO_GATE and ok_fault
           and code_fl == S.E_SH_GATE_ERROR
           and fault_view["displayed"] == []
           and n_ev4 == n_ev2 + 1 and clean_place["action"] == "place"
           and clean_place["disclaimer"] == DISCLAIMER)
    record("AC-SH3", ok3, "caption with a forbidden word rejected %s"
          " zero rows; caption with an advisory word rejected %s zero"
          " rows (%d==%d); unwired gate refuses construction %s;"
          " gate runtime fault mapped %s with zero rows (never a"
          " silent pass); exactly 1 clean place stored (%d==%d+1)"
          % (code_fw, code_adv, n_ev2, n_ev3, code_ng, code_fl,
             n_ev4, n_ev2))

    # -- AC-SH4 event-sourced display state + slot cap -------------------------
    n_tx0 = _count(conn, "ledger_tx")
    east = sh.register_showcase("east-wing", "East Wing Window", 2,
                                 True)
    ok_dup_place, code_dp = expect_sh_error(
        lambda: sh.place_exhibit("usr:alice", "city-hall", cl_a, "x"),
        S.E_SH_ALREADY_DISPLAYED)
    ok_cross, code_xw = expect_sh_error(
        lambda: sh.place_exhibit("usr:alice", "east-wing", cl_a, "x"),
        S.E_SH_ALREADY_DISPLAYED)
    p_b = sh.place_exhibit("usr:bob", "city-hall", cl_b, "", False)
    ok_full, code_fl2 = expect_sh_error(
        lambda: sh.place_exhibit("usr:carol", "city-hall", cl_c, "x"),
        S.E_SH_SHOWCASE_FULL)
    rt_b = sh.retract_exhibit("usr:bob", "city-hall", cl_b)
    ok_rt_dbl, code_rd = expect_sh_error(
        lambda: sh.retract_exhibit("usr:bob", "city-hall", cl_b),
        S.E_SH_NOT_DISPLAYED)
    p_c = sh.place_exhibit("usr:carol", "city-hall", cl_c, "", False)
    rt_c = sh.retract_exhibit("usr:carol", "city-hall", cl_c)
    p_b2 = sh.place_exhibit("usr:bob", "city-hall", cl_b, "again",
                            False)
    ok_rt_oth, code_ro = expect_sh_error(
        lambda: sh.retract_exhibit("usr:alice", "east-wing", cl_a),
        S.E_SH_NOT_DISPLAYED)
    n_tx1 = _count(conn, "ledger_tx")
    view4 = sh.showcase_view("city-hall")
    ok4 = (east["ai_label"] == 1 and ok_dup_place
           and code_dp == S.E_SH_ALREADY_DISPLAYED and ok_cross
           and code_xw == S.E_SH_ALREADY_DISPLAYED and p_b["action"]
           == "place" and ok_full
           and code_fl2 == S.E_SH_SHOWCASE_FULL
           and rt_b["action"] == "retract" and ok_rt_dbl
           and code_rd == S.E_SH_NOT_DISPLAYED and p_c["action"]
           == "place" and rt_c["action"] == "retract"
           and p_b2["action"] == "place" and ok_rt_oth
           and code_ro == S.E_SH_NOT_DISPLAYED and n_tx1 == n_tx0
           and [d["cl_id"] for d in view4["displayed"]]
           == [cl_a, cl_b])
    record("AC-SH4", ok4, "duplicate place in the same window"
          " rejected %s; cross-window place of an already-displayed"
          " item rejected %s (one item one window); cap-2 window"
          " third place rejected %s; retract ok; double retract"
          " rejected %s; slot freed after a retract (carol placed"
          " in); re-place after retract ok (new event row); retract"
          " of an item placed elsewhere rejected %s; derived"
          " displayed list == [%d, %d] in placement order; zero"
          " token rows across the whole cycle (%d==%d)"
          % (code_dp, code_xw, code_fl2, code_rd, code_ro, cl_a, cl_b,
             n_tx0, n_tx1))

    # -- AC-SH5 chronicle permanence + tour derivation ---------------------------
    hist = sh.chronicle("city-hall")
    all_hist = sh.chronicle()
    seq = [(e["cl_id"], e["action"]) for e in hist["events"]]
    tour = sh.chronicle_tour("city-hall")
    stops = [(s["stop"], s["cl_id"]) for s in tour["stops"]]
    view5 = sh.showcase_view("city-hall")
    ok5 = (seq == [(cl_a, "place"), (cl_b, "place"),
                   (cl_b, "retract"), (cl_c, "place"),
                   (cl_c, "retract"), (cl_b, "place")]
           and [e["event_id"] for e in hist["events"]]
           == sorted(e["event_id"] for e in hist["events"])
           and len(all_hist["events"]) == len(hist["events"])
           and stops == [(1, cl_a), (2, cl_b)]
           and [d["cl_id"] for d in view5["displayed"]]
           == [cl_a, cl_b]
           and all(e.get("ai_label") in (0, 1)
                  for e in hist["events"]))
    record("AC-SH5", ok5, "chronicle keeps the full event order"
          " place/place/retract/place/retract/place (%d events,"
          " ids strictly ascending); retracted items stay in the"
          " permanent record; unfiltered chronicle == filtered"
          " length (%d); tour stops == %s (displayed only,"
          " placement order, 1..N); view agrees with the tour"
          % (len(seq), len(all_hist["events"]), stops))

    # -- AC-SH6 AIGC label + resident disclaimer ----------------------------------
    ok_no_dis, code_nd = expect_sh_error(
        lambda: S.ShowcaseFace(led, gate, "  ", fault_path),
        S.E_SH_NO_DISCLAIMER)
    ai_place = sh.place_exhibit("usr:alice", "east-wing", cl_a2,
                                "ai authored caption", True)
    ev_row = shconn.execute(
        "SELECT ai_label FROM exhibit_events WHERE cl_id = ?"
        " AND action = 'place'", (cl_a2,)).fetchone()
    label_rejected = []
    for table, cols in (
            ("showcases", "('x','t',2,2,'t')"),
            ("exhibit_events",
             "(99,'x',1,'usr:alice','',2,'place','t')")):
        try:
            shconn.execute(
                "INSERT INTO %s VALUES %s" % (table, cols))
            shconn.commit()
        except sqlite3.IntegrityError:
            shconn.rollback()
            label_rejected.append(True)
        else:
            label_rejected.append(False)
    envelopes = (r1, clean_place, rt_b, view4, hist, tour)
    all_disclaimer = all(e.get("disclaimer") == DISCLAIMER
                         for e in envelopes)
    ok6 = (ok_no_dis and code_nd == S.E_SH_NO_DISCLAIMER
           and ai_place["disclaimer"] == DISCLAIMER
           and ev_row is not None and int(ev_row[0]) == 1
           and east["ai_label"] == 1 and all_disclaimer
           and all(label_rejected)
           and all(s.get("ai_label") in (0, 1) for s in tour["stops"]))
    record("AC-SH6", ok6, "empty disclaimer refuses construction %s;"
          " every envelope (register/place/retract/view/chronicle/"
          "tour) carries the resident disclaimer (%s); declared"
          " ai_label persists on the showcase row (%d) and the"
          " event row (%d); direct SQL ai_label=2 refused by the"
          " CHECK on both tables (%s)"
          % (code_nd, all_disclaimer, east["ai_label"],
             int(ev_row[0]), label_rejected))

    # -- AC-SH7 hard laws: bad args, hygiene, zero-write posture --------------
    counts0 = (_count(shconn, "showcases"),
               _count(shconn, "exhibit_events"))
    bad7 = []
    raised7 = True
    for label, fn, code in (
            ("empty showcase id place", lambda: sh.place_exhibit(
                "usr:alice", "  ", cl_a, "c"), S.E_SH_BAD_ARGS),
            ("empty showcase id retract", lambda: sh.retract_exhibit(
                "usr:alice", "  ", cl_a), S.E_SH_BAD_ARGS),
            ("non-str caption", lambda: sh.place_exhibit(
                "usr:alice", "city-hall", cl_a, 5), S.E_SH_BAD_ARGS),
            ("non-bool ai flag", lambda: sh.place_exhibit(
                "usr:alice", "east-wing", cl_a2, "c", 1),
             S.E_SH_BAD_ARGS),
            ("bad retract account", lambda: sh.retract_exhibit(
                "pool:reserve", "city-hall", cl_a), S.E_SH_BAD_ARGS)):
        ok_one, got = expect_sh_error(fn, code)
        if ok_one:
            bad7.append("%s=%s" % (label, got))
        else:
            bad7.append("%s NOT-RAISED(%s)" % (label, got))
            raised7 = False
    counts1 = (_count(shconn, "showcases"),
               _count(shconn, "exhibit_events"))
    src = sh_src
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    net_imports = [ln for ln in src.splitlines()
                   if (ln.startswith("import ") or ln.startswith("from "))
                   and any(w in ln for w in
                           ("urllib", "requests", "socket", "http"))]
    banned_hits = [w for w in BANNED_VERBS if w in src]
    update_hits = [w for w in ("UPDATE showcases", "UPDATE exhibit_")
                   if w in src]
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_after = h.read()
    ok7 = (raised7 and counts0 == counts1 and non_ascii == 0
           and not net_imports and not banned_hits
           and not update_hits and "random" not in src
           and cfg_after == cfg_bytes)
    record("AC-SH7", ok7, "all %d bad args rejected (%s); zero side"
          " effects (rows %s unchanged); module pure ASCII (%d"
          " non-ascii); zero network imports (%d); zero banned"
          " circulation verbs in source (%s); zero UPDATE surface"
          " (%s); zero RNG; shipped config.json byte-stable"
          % (len(bad7), "; ".join(bad7), counts0, non_ascii,
             len(net_imports), banned_hits, update_hits))

    conn.close()
    shconn.close()
    fault_sh.close()
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
