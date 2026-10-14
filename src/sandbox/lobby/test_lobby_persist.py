"""Acceptance suite: lobby event-store residual read-face family
cross-restart persistence window (BigDomain R1966, R1958 seed).

Pins the pre-registered criteria AC-LBP1..AC-LBP7 (claim row in
state/queue/tech.md, pre-registered before any suite code).

Seat boundary (R1929 dedup-closure law): the two lobby board read
faces (room_message_board / idea_pool_board) already carry their
close -> reopen persist example in-book (R1891 AC-S32..S38 at the
store level, R1915 AC-S49..S54 at the protocol level) - this suite
does NOT re-prove them. The genuine residual gap this suite pins:
the remaining EventStore read faces - count(where-filter family),
census_lookup, export_day - plus the import_census whole-table
refresh semantics and the content-addressed append dedup gate, all
across a close -> reopen on the same database byte-identically;
post-restart real-path appends re-derive the counts (zero cache)
while pre-restart rows and old-day exports stay frozen; the read
battery is pure and double-run stable across two restarts; the
suite is ascii, offline and ships zero product changes.

Clock discipline: every ts_utc and census field is a fixed literal;
no real clock, no RNG, so a double run is byte-identical by
construction.

Usage: python test_lobby_persist.py
"""

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import store as S                                     # noqa: E402 (lobby product)

RESULTS = []
NOTICE = "city events board - informational only, not advice"
DAY1 = "2026-09-24"
DAY2 = "2026-09-25"
DAY3 = "2026-09-26"
EMPTY_DAY = "2030-01-01"

# Anchor world (AC-LBP1): eight events across two days, public append API.
EVENTS = [
    # day1: 3 lobby chats + 1 quant chat + 1 idea + 1 intake
    ("2026-09-24T09:00:00Z", "chat.broadcast", "res:amy", "lobby",
     "chat amy 1", {"text": "hello harbor"}),
    ("2026-09-24T09:01:00Z", "chat.broadcast", "res:ben", "lobby",
     "chat ben 1", {"text": "good morning city"}),
    ("2026-09-24T09:02:00Z", "chat.broadcast", "res:amy", "lobby",
     "chat amy 2", {"text": "the pier is bright"}),
    ("2026-09-24T09:03:00Z", "chat.broadcast", "res:cal", "quant",
     "chat cal q", {"text": "market chatter"}),
    ("2026-09-24T09:04:00Z", "idea.submit", "res:amy", "cocreate",
     "idea night lights", None),
    ("2026-09-24T09:05:00Z", "avatar.intake", "res:dan", "lobby",
     "intake dan", None),
    # day2: 1 lobby chat + 1 quant idea
    ("2026-09-25T10:00:00Z", "chat.broadcast", "res:erin", "lobby",
     "chat erin 1", {"text": "festival plan"}),
    ("2026-09-25T10:01:00Z", "idea.submit", "res:fin", "quant",
     "idea data fountain", None),
]

CENSUS_V1 = [
    {"id": "c-001", "name": "Amy", "tier": "mayor"},
    {"id": "c-002", "name": "Ben", "tier": "citizen"},
    {"id": "c-003", "name": "Cal", "tier": "citizen"},
    {"id": "", "name": "NoCid"},
]
CENSUS_V2 = [
    {"id": "c-002", "name": "Ben", "tier": "cocreator"},
    {"id": "c-009", "name": "Ivy", "tier": "citizen"},
]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def digest_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def sql_rows(db_path, sql):
    conn = sqlite3.connect(db_path)
    try:
        return [list(r) for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def sql_scalar(db_path, sql):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql).fetchone()[0]
    finally:
        conn.close()


def count_battery(st):
    """Five count faces: total + three where-filters + one day filter."""
    return [
        ("count:total", st.count()),
        ("count:chat", st.count("WHERE type = ?", ("chat.broadcast",))),
        ("count:idea", st.count("WHERE type = ?", ("idea.submit",))),
        ("count:zone-lobby", st.count("WHERE zone = ?", ("lobby",))),
        ("count:day1", st.count("WHERE substr(ts_utc, 1, 10) = ?", (DAY1,))),
    ]


def census_battery(st):
    return [
        ("census:c-001", json.dumps(st.census_lookup("c-001"),
                                    sort_keys=True)),
        ("census:c-002", json.dumps(st.census_lookup("c-002"),
                                    sort_keys=True)),
        ("census:c-003", json.dumps(st.census_lookup("c-003"),
                                    sort_keys=True)),
        ("census:c-404", json.dumps(st.census_lookup("c-404"),
                                    sort_keys=True)),
    ]


def export_battery(st, out_dir):
    faces = []
    for day in (DAY1, DAY2, EMPTY_DAY):
        path, n = st.export_day(day, out_dir)
        faces.append(("export:" + day, "%d:%s" % (n, digest_file(path))))
    return faces


def read_battery(st, out_dir):
    return (count_battery(st) + census_battery(st)
            + export_battery(st, out_dir))


def battery_same(a, b):
    return (len(a) == len(b)
            and all(x[0] == y[0] and x[1] == y[1] for x, y in zip(a, b)))


def table_counts(db_path):
    return {
        "events": sql_scalar(db_path, "SELECT COUNT(*) FROM events"),
        "census": sql_scalar(db_path, "SELECT COUNT(*) FROM census_cache"),
    }


def append_all(st, rows):
    return [st.append(*row) for row in rows]


def replay_refused(st):
    """Content-addressed dedup gate: the exact same event must refuse."""
    try:
        st.append(*EVENTS[0])
        return False
    except sqlite3.IntegrityError:
        return True


def main():
    frozen = {}
    for rel in ("store.py", "config.json"):
        with open(os.path.join(BASE, rel), "rb") as handle:
            frozen[rel] = handle.read()

    tmp = tempfile.mkdtemp(prefix="lobby-lbp-")
    db_path = os.path.join(tmp, "events.db")
    exp_a = os.path.join(tmp, "exp-a")
    exp_b = os.path.join(tmp, "exp-b")
    exp_c = os.path.join(tmp, "exp-c")
    st = S.EventStore(db_path, disclaimer=NOTICE)
    st2 = None
    st3 = None
    try:
        # AC-LBP1: anchor world + pre-restart battery -------------------
        ids = append_all(st, EVENTS)
        n_import = st.import_census(CENSUS_V1)
        battery1 = read_battery(st, exp_a)
        census_anchor = dict(census_battery(st))
        cross = table_counts(db_path)
        ok1 = (len(ids) == 8 and n_import == 3
               and cross == {"events": 8, "census": 3}
               and battery1[0] == ("count:total", 8)
               and battery1[1] == ("count:chat", 5)
               and battery1[2] == ("count:idea", 2)
               and battery1[3] == ("count:zone-lobby", 5)
               and battery1[4] == ("count:day1", 6)
               and battery1[9][1].startswith("6:")
               and battery1[10][1].startswith("2:")
               and battery1[11][1].startswith("0:")
               and json.loads(battery1[8][1]) is None)
        record("AC-LBP1", ok1,
               "ids=%d import=%d counts=%s day2-export=%s absent=%s"
               % (len(ids), n_import, cross, battery1[10][1][:11],
                  battery1[8][1]))

        # AC-LBP2: close -> reopen, residual faces byte-identical --------
        st.close()
        st2 = S.EventStore(db_path, disclaimer=NOTICE)
        battery2 = read_battery(st2, exp_b)
        c_pre = table_counts(db_path)
        ok2 = battery_same(battery2, battery1) and c_pre == cross
        record("AC-LBP2", ok2,
               "byte-identity=%s tables=%s"
               % (battery_same(battery2, battery1), c_pre))

        # AC-LBP3: post-restart real-path continuation (zero cache) ------
        cont = [
            ("2026-09-25T10:05:00Z", "chat.broadcast", "res:gil", "lobby",
             "chat gil 1", {"text": "late show"}),
            ("2026-09-26T11:00:00Z", "chat.broadcast", "res:gil", "lobby",
             "chat gil 2", {"text": "new day"}),
        ]
        append_all(st2, cont)
        counts_after = dict(count_battery(st2))
        census_after = dict(census_battery(st2))
        path_d2, n_d2 = st2.export_day(DAY2, exp_c)
        d2_reexport = "%d:%s" % (n_d2, digest_file(path_d2))
        d2_anchor = [v for k, v in battery1 if k == "export:" + DAY2][0]
        p_d1, n_d1 = st2.export_day(DAY1, exp_c)
        d1_reexport = "%d:%s" % (n_d1, digest_file(p_d1))
        d1_anchor = [v for k, v in battery1 if k == "export:" + DAY1][0]
        ok3 = (counts_after["count:total"] == 10
               and st2.count("WHERE substr(ts_utc, 1, 10) = ?", (DAY2,)) == 3
               and st2.count("WHERE substr(ts_utc, 1, 10) = ?", (DAY3,)) == 1
               and d2_reexport != d2_anchor
               and n_d2 == 3
               and d1_reexport == d1_anchor
               and census_after == census_anchor)
        record("AC-LBP3", ok3,
               "total=%d day2=%d day3=%d old-day-frozen=%s census-clean=%s"
               % (counts_after["count:total"],
                  st2.count("WHERE substr(ts_utc, 1, 10) = ?", (DAY2,)),
                  st2.count("WHERE substr(ts_utc, 1, 10) = ?", (DAY3,)),
                  d1_reexport == d1_anchor,
                  census_after == census_anchor))

        # AC-LBP4: census whole-table refresh across the restart ---------
        n_refresh = st2.import_census(CENSUS_V2)
        l1 = st2.census_lookup("c-001")
        l2 = st2.census_lookup("c-002")
        l9 = st2.census_lookup("c-009")
        c_events = sql_scalar(db_path, "SELECT COUNT(*) FROM events")
        ok4 = (n_refresh == 2 and l1 is None
               and l2 == {"id": "c-002", "name": "Ben",
                          "tier": "cocreator"}
               and l9 == {"id": "c-009", "name": "Ivy",
                          "tier": "citizen"}
               and c_events == 10)
        record("AC-LBP4", ok4,
               "refresh=%d dropped-None=%s kept-updated=%s new=%s"
               " events-untouched=%d"
               % (n_refresh, l1 is None,
                  l2 == {"id": "c-002", "name": "Ben",
                         "tier": "cocreator"},
                  l9 == {"id": "c-009", "name": "Ivy",
                         "tier": "citizen"},
                  c_events))

        # post-refresh state: the lens the remaining criteria reuse
        battery_mid = read_battery(st2, exp_c)
        census_rows_mid = sql_rows(db_path,
                                   "SELECT * FROM census_cache ORDER BY cid")
        events_anchor = sql_rows(db_path, "SELECT * FROM events"
                                         " ORDER BY rowid")
        c_mid = table_counts(db_path)

        # AC-LBP5: frozen prefix + replay gate across the restart ---------
        replay_ok2 = replay_refused(st2)
        c_after_replay = table_counts(db_path)
        ok5 = (c_after_replay == c_mid and replay_ok2
               and sql_rows(db_path, "SELECT * FROM events"
                            " ORDER BY rowid") == events_anchor
               and sql_rows(db_path, "SELECT * FROM census_cache"
                            " ORDER BY cid") == census_rows_mid)
        record("AC-LBP5", ok5,
               "replay-refused=%s rows-frozen=%s census-frozen=%s"
               % (replay_ok2,
                  sql_rows(db_path, "SELECT * FROM events"
                           " ORDER BY rowid") == events_anchor,
                  sql_rows(db_path, "SELECT * FROM census_cache"
                           " ORDER BY cid") == census_rows_mid))

        # AC-LBP6: pure-read law + determinism ----------------------------
        battery_rerun = read_battery(st2, exp_c)
        c_after_reads = table_counts(db_path)
        ok6 = (battery_same(battery_rerun, battery_mid)
               and c_after_reads == c_mid)
        record("AC-LBP6", ok6,
               "double-run=%s tables-stable=%s"
               % (battery_same(battery_rerun, battery_mid),
                  c_after_reads == c_mid))

        # AC-LBP7: second restart + hygiene -------------------------------
        st2.close()
        st3 = S.EventStore(db_path, disclaimer=NOTICE)
        battery3 = read_battery(st3, exp_c)
        replay_ok3 = replay_refused(st3)
        ok7_core = (battery_same(battery3, battery_mid)
                    and replay_ok3
                    and table_counts(db_path) == c_mid
                    and sql_rows(db_path, "SELECT * FROM events"
                                 " ORDER BY rowid") == events_anchor)
        st3.close()
    finally:
        for handle in (st, st2, st3):
            if handle is not None:
                try:
                    handle.close()
                except Exception:
                    pass
        shutil.rmtree(tmp, ignore_errors=True)

    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        own_src = handle.read()
    own_ascii = all(ord(ch) < 128 for ch in own_src)
    net_hits = [ln.strip() for ln in own_src.splitlines()
                if ln.strip().startswith(("import ", "from "))
                and any(w in ln for w in
                        ("urllib", "requests", "socket", "http"))]
    thawed = [rel for rel, blob in frozen.items()
              if open(os.path.join(BASE, rel), "rb").read() != blob]
    record("AC-LBP7", ok7_core and own_ascii and not net_hits and not thawed
           and len(RESULTS) == 6,
           "second-restart=%s replay3=%s ascii=%s net=%s thawed=%s"
           " results-so-far=%d"
           % (battery_same(battery3, battery_mid), replay_ok3,
              own_ascii, net_hits, thawed, len(RESULTS)))

    fails = [ac for ac, ok in RESULTS if not ok]
    print("---- lobby residual persist acceptance: %d/%d passed"
          % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails:
        print("FAILED: %s" % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
