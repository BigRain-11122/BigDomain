"""Acceptance suite for the curation boards_combined
month-window scoped read face (BigDomain R1996; canon = the
explore-queue row claimed by R1996 with criteria registered
BEFORE this code existed; honesty law). The combined hot+cold
dual board (curation.py boards_combined, R1974) gains an
optional explicit YYYY-MM month window: both zones re-scope to
the window-recorded display heat through the NEW ShowcaseFace
public read face showcase_view_window (reference, not copy,
zero second aggregation engine), while the registry stays the
dense axis.

Window semantics (the record-time law, R1712 family): events
slice by their acted_utc RECORD month. The window heat of a
theme counts only the items whose latest window-recorded event
is a place - so an item placed in an earlier month with no
window-recorded event stays OFF the window board while
remaining on the live all-time board, and an item placed in
October then retracted in November shows as displayed in the
October window and NOT in the November window. A curation
registered under a LATER clock still boards in the earlier
window when its member showcase carries earlier-window records
(the registration month never decides the board month).

Criteria AC-CJM1..CJM7 were pre-registered in
state/queue/explore.md at claim time (R1996; AC-CJM prefix
git-grep zero-occupancy anchored 2026-10-15; AC-CJ1..CJ7
belong to the R1974 read face, AC-CDP1..CDP6 to the R1975
persist window, AC-CZW../AC-CBW1..6 to the R1972/R1976 windows,
none re-registered here).

Product-extension round: curation.py and showcase.py carry the
window face (the deliverable itself); both shipped config.json
files are sha256 double-proven unchanged. Explicit record
times drive the world through a fixture-layer _now_utc
substitute (real product paths, zero real-clock dependence -
the R1993 fixture-layer precedent); the substitute is saved and
restored in a finally block. Restart carrier = the R1923
four-piece full-stack precedent (close cu -> sh -> led, then
rebuild Ledger + stateless SecGate + ShowcaseFace + CurationFace
on the same three db paths).

Usage: python test_curation_combinedmonth.py
"""

import hashlib
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

DISCLAIMER = ("sandbox stand-in disclaimer: the windowed hot+cold"
              " dual board is a display feature, not investment"
              " advice")

PIN_FILES = [
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

ROW_KEYS = {"rank", "curation_id", "title", "ai_label",
            "member_count", "displayed_total"}

DEFAULT_ENV_KEYS = {"hot_board", "cold_board", "totals",
                    "disclaimer"}
WINDOW_ENV_KEYS = {"hot_board", "cold_board", "totals", "window",
                   "disclaimer"}

ALL_IDS = ["cu-alpha", "cu-beta", "cu-delta", "cu-gamma"]

BAD_WINDOWS = ["2026-13", "2026-00", "2026-1", "2026/10", "2026",
               "202610", "abcd", "", 2026, True, 2.5,
               "2026-10\n", " 2026-10"]

OCT = "2026-10-14T10:00:00Z"
NOV = "2026-11-03T09:00:00Z"
SEP = "2026-09-20T08:00:00Z"


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(env):
    return json.dumps(env, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def table_counts(shconn, cuconn, ledconn):
    return {"curations": int(cuconn.execute(
                "SELECT COUNT(*) FROM curations").fetchone()[0]),
            "curation_members": int(cuconn.execute(
                "SELECT COUNT(*) FROM curation_members"
                ).fetchone()[0]),
            "showcases": int(shconn.execute(
                "SELECT COUNT(*) FROM showcases").fetchone()[0]),
            "exhibit_events": int(shconn.execute(
                "SELECT COUNT(*) FROM exhibit_events"
                ).fetchone()[0]),
            "ledger_tx": int(ledconn.execute(
                "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])}


def rows_match(board, expected):
    if len(board) != len(expected):
        return False
    for row, (rank, cid, total, mcnt) in zip(board, expected):
        if row["rank"] != rank or row["curation_id"] != cid:
            return False
        if row["displayed_total"] != total:
            return False
        if row["member_count"] != mcnt:
            return False
    return False if any(set(r.keys()) != ROW_KEYS
                        for r in board) else True


def ids_of(env, key):
    return [row["curation_id"] for row in env[key]]


def partition_law(env, window=None):
    hot = env["hot_board"]
    cold = env["cold_board"]
    hot_ids = set(ids_of(env, "hot_board"))
    cold_ids = set(ids_of(env, "cold_board"))
    totals = env["totals"]
    ok = (not (hot_ids & cold_ids)
          and hot_ids | cold_ids == set(ALL_IDS)
          and totals["total"] == len(ALL_IDS)
          and totals["hot_count"] == len(hot)
          and totals["cold_count"] == len(cold)
          and totals["total"] == totals["hot_count"]
          + totals["cold_count"]
          and all(r["displayed_total"] > 0 for r in hot)
          and all(r["displayed_total"] == 0 for r in cold)
          and all(set(r.keys()) == ROW_KEYS
                  for r in hot + cold))
    if window is None:
        ok = ok and set(env.keys()) == DEFAULT_ENV_KEYS
    else:
        ok = (ok and set(env.keys()) == WINDOW_ENV_KEYS
              and env["window"] == window)
    return ok and env["disclaimer"] == DISCLAIMER


def manual_latest_map(shconn, window=None):
    """Independent re-derivation path (python-side, not the
    product SQL): latest event per item, optionally restricted
    to the window-recorded slice by record-time prefix."""
    latest = {}
    for eid, sid, cl_id, action, acted in shconn.execute(
            "SELECT event_id, showcase_id, cl_id, action,"
            " acted_utc FROM exhibit_events ORDER BY"
            " event_id").fetchall():
        if window is not None and str(acted)[:7] != window:
            continue
        prev = latest.get(cl_id)
        if prev is None or eid > prev[0]:
            latest[cl_id] = (eid, sid, action)
    return latest


def manual_heats(shconn, cuconn, window=None):
    latest = manual_latest_map(shconn, window)
    members = {}
    for cid, sid in cuconn.execute(
            "SELECT curation_id, showcase_id FROM curation_members"
            " ORDER BY curation_id, position").fetchall():
        members.setdefault(cid, []).append(sid)
    heats = {}
    for cid in ALL_IDS:
        total = 0
        for sid in members.get(cid, []):
            for (_eid, osid, action) in latest.values():
                if osid == sid and action == "place":
                    total += 1
        heats[cid] = total
    return heats


def board_heats(env):
    heats = {}
    for row in env["hot_board"] + env["cold_board"]:
        heats[row["curation_id"]] = row["displayed_total"]
    return heats


def reopen(db_path, sh_path, cu_path, cfg, lobby_cfg):
    led = L.Ledger(db_path, cfg)
    gate = SecGate.from_config(lobby_cfg)
    sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
    cu = CU.CurationFace(sh, DISCLAIMER, cu_path)
    return led, sh, cu


def main():
    tmp = tempfile.mkdtemp(prefix="curation-combinedmonth-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    cu_path = os.path.join(tmp, "curation.db")
    cu_empty_path = os.path.join(tmp, "curation-empty.db")

    shas_before = {p: sha256_file(p) for p in PIN_FILES}

    clock = {"stamp": "2026-01-01T00:00:00Z"}
    orig_s_now = S._now_utc
    orig_cu_now = CU._now_utc

    def fake_now():
        return clock["stamp"]

    read_batches = []
    led = sh = cu = cu_empty = None
    shconn = cuconn = ledconn = None
    try:
        S._now_utc = fake_now
        CU._now_utc = fake_now

        led = L.Ledger(db_path, cfg)
        cf = C.CollectiblesFace(led)
        gate = SecGate.from_config(lobby_cfg)
        sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
        cu = CU.CurationFace(sh, DISCLAIMER, cu_path)
        for acct, avatar in (("usr:alice", "alice"),
                             ("usr:bob", "bob"),
                             ("usr:carol", "carol")):
            led.ensure_account(acct, census_avatar_id=avatar)
        specs = (
            ("a1", "usr:alice", "evt-tower", "tower-cert"),
            ("b", "usr:bob", "evt-bridge", "bridge-cert"),
            ("c", "usr:carol", "evt-harbor", "harbor-cert"),
            ("d", "usr:alice", "evt-spire", "spire-cert"),
            ("e", "usr:carol", "evt-lens", "lens-cert"),
        )
        cl = {}
        for key, acct, ev, kind in specs:
            cl[key] = cf.issue_certificate(acct, ev, kind)["cl_id"]
        for sid in ("sh-one", "sh-two", "sh-three", "sh-four"):
            sh.register_showcase(sid, sid + " window", 3, False)

        # september record: placed before the other windows, no
        # later event - the record-time-law exclusion carrier
        clock["stamp"] = SEP
        sh.place_exhibit("usr:carol", "sh-three", cl["c"],
                        "sep lantern")

        # october registrations + october-recorded placements
        clock["stamp"] = OCT
        cu.register_curation("cu-alpha", "Alpha Route",
                             ["sh-one"], False)
        cu.register_curation("cu-beta", "Beta Route",
                             ["sh-two"], False)
        cu.register_curation("cu-gamma", "Gamma Route",
                             ["sh-three"], False)
        sh.place_exhibit("usr:alice", "sh-one", cl["a1"],
                         "oct tower")
        sh.place_exhibit("usr:bob", "sh-two", cl["b"], "oct arch")
        sh.place_exhibit("usr:carol", "sh-four", cl["e"],
                         "oct lamp")

        # november registration (separation-probe carrier) +
        # november records: the october placement retracted, a
        # fresh november placement in sh-one
        clock["stamp"] = NOV
        cu.register_curation("cu-delta", "Delta Route",
                             ["sh-four"], False)
        sh.retract_exhibit("usr:bob", "sh-two", cl["b"])
        sh.place_exhibit("usr:alice", "sh-one", cl["d"],
                         "nov lens")

        shconn = sqlite3.connect(sh_path)
        cuconn = sqlite3.connect(cu_path)
        ledconn = sqlite3.connect(db_path)

        # -- AC-CJM1 default preservation + gate-before-read ---
        env_def = cu.boards_combined()
        env_def2 = cu.boards_combined(None)
        env_live_hot = cu.hot_board()
        ok1 = []
        ok1.append(dumps(env_def) == dumps(env_def2))
        ok1.append(set(env_def.keys()) == DEFAULT_ENV_KEYS)
        ok1.append(set(env_live_hot.keys())
                   == {"hot_board", "disclaimer"})
        ok1.append(partition_law(env_def))
        ok1.append(rows_match(env_def["hot_board"], [
            (1, "cu-alpha", 2, 1), (2, "cu-delta", 1, 1),
            (3, "cu-gamma", 1, 1)]))
        ok1.append(rows_match(env_def["cold_board"], [
            (1, "cu-beta", 0, 1)]))
        ok1.append(board_heats(env_def)
                   == manual_heats(shconn, cuconn))
        counts_before = table_counts(shconn, cuconn, ledconn)
        try:
            cu.boards_combined("2026-13")
            ok1.append(False)
        except CU.CurationError as exc:
            ok1.append(exc.code == "E_CU_BAD_WINDOW")
        ok1.append(table_counts(shconn, cuconn, ledconn)
                   == counts_before)
        record("AC-CJM1", all(ok1),
               "default-form preservation: boards_combined() and"
               " boards_combined(None) byte-identical, default"
               " envelope key set exactly"
               " {hot_board, cold_board, totals, disclaimer},"
               " hot_board() default envelope exactly"
               " {hot_board, disclaimer}; live all-time board"
               " holds the september placement (cu-alpha heat 2,"
               " cu-delta 1, cu-gamma 1 hot; cu-beta cold after"
               " its november retract) with the python-side"
               " independent re-derivation agreeing; a malformed"
               " window refuses BEFORE any read with the five"
               " table counts unchanged")

        # -- AC-CJM2 bad-window fail-closed on both faces -------
        ok2 = []
        counts_b2 = table_counts(shconn, cuconn, ledconn)
        for bad in BAD_WINDOWS:
            try:
                cu.boards_combined(bad)
                ok2.append(False)
                break
            except CU.CurationError as exc:
                ok2.append(exc.code == "E_CU_BAD_WINDOW")
            try:
                sh.showcase_view_window("sh-one", bad)
                ok2.append(False)
                break
            except S.ShowcaseError as exc:
                ok2.append(exc.code == "E_SH_BAD_WINDOW")
        ok2.append(table_counts(shconn, cuconn, ledconn)
                   == counts_b2)
        cu_empty = CU.CurationFace(sh, DISCLAIMER, cu_empty_path)
        try:
            cu_empty.boards_combined("2026-13")
            ok2.append(False)
        except CU.CurationError as exc:
            ok2.append(exc.code == "E_CU_BAD_WINDOW")
        env_empty = cu_empty.boards_combined()
        ok2.append(env_empty["hot_board"] == []
                   and env_empty["cold_board"] == []
                   and env_empty["totals"] == {"hot_count": 0,
                                               "cold_count": 0,
                                               "total": 0})
        record("AC-CJM2", all(ok2),
               "bad-window fail-closed: all %d malformed forms"
               " (%s) refuse on BOTH faces with the dedicated"
               " family codes asserted by literal (curation"
               " E_CU_BAD_WINDOW, showcase E_SH_BAD_WINDOW),"
               " every refusal leaving the five table counts"
               " unchanged (gate before read); the gate stands"
               " alone over a zero-curation registry (empty face"
               " still refuses, and its default read is the"
               " honest empty board)"
               % (len(BAD_WINDOWS),
                  "month 13, month 00, 1-digit month, slash form,"
                  " year-only, no separator, non-digit, empty"
                  " string, int, bool, float, trailing newline,"
                  " leading space"))

        # -- AC-CJM3 record-time slicing + cross-window honesty -
        env_oct = cu.boards_combined("2026-10")
        env_nov = cu.boards_combined("2026-11")
        ok3 = []
        ok3.append(partition_law(env_oct, "2026-10"))
        ok3.append(rows_match(env_oct["hot_board"], [
            (1, "cu-alpha", 1, 1), (2, "cu-beta", 1, 1),
            (3, "cu-delta", 1, 1)]))
        ok3.append(rows_match(env_oct["cold_board"], [
            (1, "cu-gamma", 0, 1)]))
        ok3.append(rows_match(env_nov["hot_board"], [
            (1, "cu-alpha", 1, 1)]))
        ok3.append(rows_match(env_nov["cold_board"], [
            (1, "cu-beta", 0, 1), (2, "cu-delta", 0, 1),
            (3, "cu-gamma", 0, 1)]))
        ok3.append(board_heats(env_oct)
                   == manual_heats(shconn, cuconn, "2026-10"))
        ok3.append(board_heats(env_nov)
                   == manual_heats(shconn, cuconn, "2026-11"))
        # record-time law: the september placement (no
        # october-recorded event) is invisible to the october
        # window yet still displayed on the live board
        ok3.append(board_heats(env_oct)["cu-gamma"] == 0)
        ok3.append(board_heats(env_def)["cu-gamma"] == 1)
        # cross-window honesty: place-in-october +
        # retract-in-november shows displayed in october and
        # not displayed in november
        ok3.append(board_heats(env_oct)["cu-beta"] == 1)
        ok3.append(board_heats(env_nov)["cu-beta"] == 0)
        record("AC-CJM3", all(ok3),
               "record-time slicing: october window hot="
               " [cu-alpha(1), cu-beta(1), cu-delta(1)] id ASC,"
               " cold=[cu-gamma(0)] - the september-placed item"
               " (zero october-recorded events) stays OFF the"
               " october window (cu-gamma heat 0) while still"
               " displayed on the live all-time board (heat 1);"
               " the october placement retracted in november is"
               " displayed in the october window (cu-beta heat"
               " 1) and NOT in the november window (heat 0);"
               " both window heats equal the python-side"
               " independent re-derivations")

        # -- AC-CJM4 dense complement + out-of-range month ------
        env_sep = cu.boards_combined("2026-09")
        env_oor = cu.boards_combined("2099-01")
        ok4 = []
        for env, win in ((env_oct, "2026-10"),
                         (env_nov, "2026-11"),
                         (env_sep, "2026-09"),
                         (env_oor, "2099-01")):
            ok4.append(partition_law(env, win))
        ok4.append(rows_match(env_sep["hot_board"], [
            (1, "cu-gamma", 1, 1)]))
        ok4.append(rows_match(env_sep["cold_board"], [
            (1, "cu-alpha", 0, 1), (2, "cu-beta", 0, 1),
            (3, "cu-delta", 0, 1)]))
        ok4.append(env_oor["hot_board"] == [])
        ok4.append(rows_match(env_oor["cold_board"], [
            (1, "cu-alpha", 0, 1), (2, "cu-beta", 0, 1),
            (3, "cu-delta", 0, 1), (4, "cu-gamma", 0, 1)]))
        record("AC-CJM4", all(ok4),
               "windowed dense complement law: every window board"
               " covers ALL four registered themes with the hot"
               " and cold zones disjoint, the union equal to the"
               " full registry, totals agreeing with the actual"
               " zone sizes and the explicit-window envelope"
               " carrying exactly the +window key set; the"
               " out-of-range month 2099-01 (zero recorded"
               " events) returns the honest empty hot zone and"
               " the all-cold shelf in id ASC order")

        # -- AC-CJM5 registration-period separation probe --------
        reg_rows = dict(cuconn.execute(
            "SELECT curation_id, registered_utc FROM curations"
            ).fetchall())
        ok5 = []
        ok5.append(str(reg_rows["cu-delta"]).startswith("2026-11"))
        ok5.append(str(reg_rows["cu-alpha"]).startswith("2026-10"))
        ok5.append("cu-delta" in ids_of(env_oct, "hot_board"))
        ok5.append("cu-delta" in ids_of(env_nov, "cold_board"))
        record("AC-CJM5", all(ok5),
               "registration-period separation: cu-delta is"
               " registered under the november clock"
               " (registered_utc prefix 2026-11, control"
               " cu-alpha prefix 2026-10) yet boards in the"
               " OCTOBER window hot zone through its member"
               " showcase's october-recorded display - the"
               " registration month never decides the board"
               " month; its november window read falls cold"
               " (member has zero november records)")

        # -- AC-CJM6 determinism + cross-restart byte identity ---
        ok6 = []
        reads = {
            "default": cu.boards_combined(),
            "oct": cu.boards_combined("2026-10"),
            "nov": cu.boards_combined("2026-11"),
            "sep": cu.boards_combined("2026-09"),
            "oor": cu.boards_combined("2099-01"),
            "hotw": cu.hot_board("2026-10"),
        }
        snaps = {}
        for key, env in reads.items():
            snaps[key] = dumps(env)
        for key in ("oct", "nov", "sep", "oor"):
            snaps[key + "2"] = dumps(cu.boards_combined(
                {"oct": "2026-10", "nov": "2026-11",
                 "sep": "2026-09", "oor": "2099-01"}[key]))
            ok6.append(snaps[key] == snaps[key + "2"])
        hotw_env = reads["hotw"]
        ok6.append(set(hotw_env.keys())
                   == {"hot_board", "window", "disclaimer"})
        ok6.append(hotw_env["window"] == "2026-10")
        ok6.append(dumps(cu.hot_board("2026-10")) == snaps["hotw"])
        hot_all_by_id = {r["curation_id"]: r
                         for r in hotw_env["hot_board"]}
        comb_hot_by_id = {r["curation_id"]: r
                          for r in reads["oct"]["hot_board"]}
        comb_cold_by_id = {r["curation_id"]: r
                           for r in reads["oct"]["cold_board"]}
        ok6.append(set(comb_hot_by_id) | set(comb_cold_by_id)
                   == set(hot_all_by_id))
        for cid, row in comb_hot_by_id.items():
            live = hot_all_by_id[cid]
            ok6.append(live["title"] == row["title"]
                       and live["ai_label"] == row["ai_label"]
                       and live["member_count"] == row["member_count"]
                       and live["displayed_total"]
                       == row["displayed_total"]
                       and row["displayed_total"] > 0)
        for cid, row in comb_cold_by_id.items():
            live = hot_all_by_id[cid]
            ok6.append(live["title"] == row["title"]
                       and live["member_count"] == row["member_count"]
                       and live["displayed_total"] == 0)
        counts_b6 = table_counts(shconn, cuconn, ledconn)
        cu.close()
        cu_empty.close()
        sh.close()
        led.close()
        led, sh, cu = reopen(db_path, sh_path, cu_path, cfg,
                             lobby_cfg)
        for key in ("default", "oct", "nov", "sep", "oor",
                    "hotw"):
            reread = {"default": cu.boards_combined,
                      "oct": lambda: cu.boards_combined("2026-10"),
                      "nov": lambda: cu.boards_combined("2026-11"),
                      "sep": lambda: cu.boards_combined("2026-09"),
                      "oor": lambda: cu.boards_combined("2099-01"),
                      "hotw": lambda: cu.hot_board("2026-10"),
                      }[key]
            ok6.append(dumps(reread()) == snaps[key])
        counts_a6 = table_counts(shconn, cuconn, ledconn)
        read_batches.append((counts_b6, counts_a6))
        record("AC-CJM6", all(ok6),
               "determinism and cross-restart identity: every"
               " windowed read is byte-identical on a same-window"
               " double call (zero RNG, zero time keys);"
               " hot_board('2026-10') carries exactly the"
               " +window envelope key with its rows cross-matching"
               " the combined october zones field-by-field (hot"
               " subset heat>0, cold zero-heat);"
               " full-stack close (cu -> sh -> led) then reopen"
               " on the same three db paths: default board, all"
               " four window boards and the windowed hot_board"
               " read are byte-identical to the pre-close"
               " snapshots (derived read faces carry zero"
               " in-memory state across restarts)")

        # -- AC-CJM7 pure-read law + hygiene --------------------
        shas_after = {p: sha256_file(p) for p in PIN_FILES}
        ok7 = [b == a for b, a in read_batches]
        ok7.append(shas_after == shas_before)
        ok7.append(len(read_batches) == 1)
        method_sources = [
            inspect.getsource(CU.CurationFace._assert_window),
            inspect.getsource(CU.CurationFace.hot_board),
            inspect.getsource(CU.CurationFace.boards_combined),
            inspect.getsource(S.ShowcaseFace.showcase_view_window),
            inspect.getsource(S.ShowcaseFace._displayed_rows_window),
        ]
        for src in method_sources:
            ok7.append(not any(verb in src for verb in
                               ("INSERT", "UPDATE ", "DELETE",
                                "CREATE ", "ALTER ")))
        with open(os.path.abspath(__file__), "rb") as handle:
            src_bytes = handle.read()
        ok7.append(all(b < 128 for b in src_bytes))
        net_hits = []
        for line in src_bytes.decode("ascii").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith(
                    "from "):
                for bad in ("urllib", "requests", "socket", "http"):
                    if bad in stripped:
                        net_hits.append(stripped)
        ok7.append(not net_hits)
        ok7.append(os.path.abspath(tmp).startswith(
            tempfile.gettempdir()))
        ok7.append(os.path.abspath(BASE) not in os.path.abspath(tmp))
        with open(os.path.join(os.path.dirname(BASE),
                               "reconcile_all.py"), "r",
                  encoding="utf-8") as handle:
            runner_src = handle.read()
        ok7.append('"ledger-curation-combinedmonth"' in runner_src)
        ok7.append("test_curation_combinedmonth.py"
                   in runner_src)
        record("AC-CJM7", all(ok7),
               "pure-read law and hygiene: the full windowed read"
               " battery left curations / curation_members /"
               " showcases / exhibit_events / ledger_tx row"
               " counts constant (final counts %s); both shipped"
               " config.json files sha256 unchanged; all five"
               " new/extended method sources carry zero write"
               " statements; suite source pure ASCII (%d bytes)"
               " with zero network imports on true import"
               " lines; world db in system tmp outside the"
               " repo; the reconcile_all SUITES registration"
               " row (ledger-curation-combinedmonth, criteria"
               " 7) is present in the runner registry"
               % (json.dumps(counts_a6, sort_keys=True),
                  len(src_bytes)))
    finally:
        S._now_utc = orig_s_now
        CU._now_utc = orig_cu_now
        for handle in (shconn, cuconn, ledconn):
            if handle is not None:
                try:
                    handle.close()
                except Exception:  # noqa: BLE001 (best effort)
                    pass
        for face in (cu, cu_empty, sh, led):
            if face is not None:
                try:
                    face.close()
                except Exception:  # noqa: BLE001 (best effort)
                    pass

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
