"""Acceptance suite for the reminder banner board (tech.md claim line
R1782; read-cap extension claim R1851).

Asserts the pre-registered criteria AC-BQ1..AC-BQ12 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Subject: ReminderFace.banner_board() - pure-read derived aggregation
over the persistent degraded in-app fallback journal: one board row per
avatar holding at least one skipped_* row, dense status/reason zero
grids, deterministic census-key ascending order, member-family
compliance envelope, zero writes, live derivation (no cache). The
R1851 read-cap extension adds the limit tail param (sentinel 0, bool
excluded, None refused) with a four-key additive overflow block
{limit, banner_board_total, returned, truncated} - the full-count key
is banner_board_total because the pre-existing total key is pinned to
the skipped-row count unit (AC-BQ1), a different aggregate.

Usage: python test_banner_board.py
"""

import hashlib
import inspect
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import reminder as RM                   # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 12
TS = "2030-06-01T00:00:00Z"             # frozen clock for row stamps
CFG_PATH = os.path.join(BASE, "config.json")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def q(db, sql, args=()):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def load_cfg(cap=None):
    with open(CFG_PATH, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if cap is not None:
        cfg = json.loads(json.dumps(cfg))
        cfg["reminder"]["daily_send_cap_default"] = cap
    return cfg


def fresh_face(tmp, name, cfg):
    db = os.path.join(tmp, name)
    return RM.ReminderFace(cfg, db), db


def main():
    tmp = tempfile.mkdtemp(prefix="banner-board-")
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()

    # ---- AC-BQ1: contract, dense honest empty, refusal family -------
    mcfg = load_cfg()
    face1, db1 = fresh_face(tmp, "bq1.db", mcfg)
    env = face1.banner_board()
    env_keys = set(env) == {"banner_board", "total", "by_status",
                            "by_reason", "ai_generated", "disclaimer",
                            "persistent"}
    dense = (env["by_status"] == {"skipped_no_budget": 0,
                                  "skipped_daily_cap": 0}
             and env["by_reason"] == {"first_service": 0,
                                      "renewal_due": 0})
    ok_empty = (env["banner_board"] == [] and env["total"] == 0
                and env["ai_generated"] == 0 and env["persistent"] is True
                and isinstance(env["disclaimer"], str)
                and env["disclaimer"].strip()
                and env["disclaimer"]
                == mcfg["compliance"]["disclaimer"])
    # refusal family: the probes are valid member configs (constructor
    # gates all pass) - only the resident compliance copy is tampered,
    # so the refusal is attributable to the face-call gate alone
    refusals = []
    probe_specs = [
        ("no-compliance",
         lambda c: c.pop("compliance", None)),
        ("empty", lambda c: c["compliance"].update(disclaimer="")),
        ("blank", lambda c: c["compliance"].update(disclaimer="   ")),
        ("non-str", lambda c: c["compliance"].update(disclaimer=123)),
        ("null", lambda c: c["compliance"].update(disclaimer=None)),
    ]
    for label, mutate in probe_specs:
        bad = json.loads(json.dumps(mcfg))
        mutate(bad)
        probe, _ = fresh_face(tmp, "bq1-probe-%s.db" % label, bad)
        try:
            probe.banner_board()
            refusals.append((label, "no-refusal"))
        except ValueError as exc:
            refusals.append((label,
                             RM.E_REM_NO_DISCLAIMER in str(exc)))
    face1.close()
    ok1 = (env_keys and dense and ok_empty
           and all(r[1] is True for r in refusals))
    record("AC-BQ1", ok1,
           "env-keys=%s dense=%s empty-board=%s refusals=%d/%d %s"
           % (env_keys, dense, ok_empty,
              sum(1 for r in refusals if r[1] is True), len(refusals),
              [r[0] for r in refusals if r[1] is True]))

    # ---- AC-BQ2: mixed world + manual SQL cross --------------------
    # cap=2: skipped_no_budget rows cost no cap (only sent rows do),
    # so budget-skips land first, then two sends exhaust the cap and
    # later attempts degrade as cap-skips - all four degraded combos
    # plus sent control rows in ONE world.
    capcfg = load_cfg(cap=2)
    face2, db2 = fresh_face(tmp, "bq2.db", capcfg)
    face2.grant_authorization("AV-A", "renewal_notice", "longterm")
    face2.grant_authorization("AV-D", "renewal_notice", "longterm")
    face2.grant_authorization("AV-E", "renewal_notice", "longterm")
    face2.grant_authorization("AV-F", "renewal_notice", "longterm")
    face2.attempt("AV-B", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-B")          # no budget
    face2.on_accept("AV-C", now=TS, auto_renewal=True)  # no budget
    face2.attempt("AV-A", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-A")          # sent (cap 1)
    face2.attempt("AV-D", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-D")          # sent (cap 2)
    face2.attempt("AV-E", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-E")          # cap skip
    face2.on_accept("AV-F", now=TS, auto_renewal=True)  # cap skip
    env2 = face2.banner_board()
    man_status = dict((r[0], r[1]) for r in q(
        db2, "SELECT status, COUNT(*) FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%' GROUP BY status"))
    man_reason = dict((r[0], r[1]) for r in q(
        db2, "SELECT reason, COUNT(*) FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%' GROUP BY reason"))
    man_total = q(db2, "SELECT COUNT(*) FROM member_reminder_log"
                  " WHERE status LIKE 'skipped_%'")[0][0]
    man_rows = {}
    for avatar, reason, n in q(
            db2, "SELECT census_avatar_id, reason, COUNT(*)"
            " FROM member_reminder_log WHERE status LIKE 'skipped_%'"
            " GROUP BY census_avatar_id, reason"):
        cell = man_rows.setdefault(avatar, {})
        cell[reason] = n
    board_ok = True
    for row in env2["banner_board"]:
        cell = man_rows.get(row["census_avatar_id"], {})
        if row["skipped"] != sum(cell.values()):
            board_ok = False
        for reason, n in cell.items():
            if row["by_reason"].get(reason) != n:
                board_ok = False
    seq = [r["census_avatar_id"] for r in env2["banner_board"]]
    row_keys = all(set(r) == {"census_avatar_id", "skipped",
                              "by_reason"}
                   for r in env2["banner_board"])
    ok2 = (env2["by_status"] == man_status
           and env2["by_reason"] == man_reason
           and env2["total"] == man_total == 4
           and board_ok and row_keys
           and seq == sorted(seq) == ["AV-B", "AV-C", "AV-E", "AV-F"]
           and len(man_rows) == len(seq))
    record("AC-BQ2", ok2,
           "by_status=%s by_reason=%s total=%d manual=%s rows-cross=%s"
           " order=%s" % (env2["by_status"], env2["by_reason"],
                          env2["total"], man_status == env2["by_status"],
                          board_ok, seq))
    face2.close()

    # ---- AC-BQ3: scope isolation (sent rows never counted) ----------
    log_all = q(db2, "SELECT COUNT(*) FROM member_reminder_log")[0][0]
    board_avatars = set(seq)
    skipped_avatars = set(r[0] for r in q(
        db2, "SELECT DISTINCT census_avatar_id FROM"
        " member_reminder_log WHERE status LIKE 'skipped_%'"))
    ok3 = (set(env2["by_status"]) == {"skipped_no_budget",
                                      "skipped_daily_cap"}
           and "sent" not in env2["by_status"]
           and env2["total"] == 4 < log_all == 6
           and board_avatars == skipped_avatars
           and "AV-A" not in board_avatars
           and "AV-D" not in board_avatars)
    record("AC-BQ3", ok3,
           "status-keys=%d total=%d < log=%d board==skipped-avatars=%s"
           " sent-avatars-absent=%s"
           % (len(env2["by_status"]), env2["total"], log_all,
              board_avatars == skipped_avatars,
              "AV-A" not in board_avatars
              and "AV-D" not in board_avatars))

    # ---- AC-BQ4: pure-read law --------------------------------------
    src = inspect.getsource(RM.ReminderFace.banner_board)
    dml = re.findall(r"\b(INSERT|UPDATE|DELETE)\b", src)
    face4, db4 = fresh_face(tmp, "bq4.db", load_cfg(cap=1))
    face4.attempt("AV-B", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-B")
    before = (q(db4, "SELECT COUNT(*) FROM member_reminder_log")[0][0],
              q(db4, "SELECT COUNT(*) FROM"
                " member_subscribe_grants")[0][0])
    first = face4.banner_board()
    second = face4.banner_board()
    after = (q(db4, "SELECT COUNT(*) FROM member_reminder_log")[0][0],
             q(db4, "SELECT COUNT(*) FROM"
               " member_subscribe_grants")[0][0])
    same = (json.dumps(first, sort_keys=True)
            == json.dumps(second, sort_keys=True))
    ok4 = (not dml) and before == after and same
    record("AC-BQ4", ok4,
           "dml-hits=%d counts-stable=%s double-call-identical=%s"
           % (len(dml), before == after, same))
    face4.close()

    # ---- AC-BQ5: live derivation (zero cache) -----------------------
    face5, db5 = fresh_face(tmp, "bq5.db", load_cfg())
    face5.attempt("AV-B", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-B")
    env5a = face5.banner_board()
    face5.attempt("AV-G", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-G")
    env5b = face5.banner_board()
    g_row = [r for r in env5b["banner_board"]
             if r["census_avatar_id"] == "AV-G"]
    ok5 = (env5a["total"] == 1
           and env5b["total"] == 2
           and env5b["by_status"]["skipped_no_budget"] == 2
           and len(g_row) == 1 and g_row[0]["skipped"] == 1
           and [r["census_avatar_id"] for r in env5b["banner_board"]]
           == ["AV-B", "AV-G"])
    record("AC-BQ5", ok5,
           "before=%d after=%d cell=%d new-row=%s order-follows=%s"
           % (env5a["total"], env5b["total"],
              env5b["by_status"]["skipped_no_budget"],
              len(g_row) == 1 and g_row[0]["skipped"] == 1,
              [r["census_avatar_id"] for r in env5b["banner_board"]]
              == ["AV-B", "AV-G"]))
    face5.close()

    # ---- AC-BQ6: hygiene ---------------------------------------------
    subjects = [os.path.join(BASE, "reminder.py"),
                os.path.abspath(__file__)]
    ascii_ok = True
    net_hits = []
    for path in subjects:
        data = open(path, "rb").read()
        if any(b > 127 for b in data):
            ascii_ok = False
        text = data.decode("ascii", "replace")
        for line in text.splitlines():
            stripped = line.strip()
            if (stripped.startswith("import ")
                    or stripped.startswith("from ")) and (
                    re.search(r"\b(urllib|requests|socket|http)\b",
                              stripped)):
                net_hits.append(stripped)
    cfg_sha_out = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    mod_src = inspect.getsource(RM)
    additive = (hasattr(RM.ReminderFace, "banner_board")
                and hasattr(RM.ReminderFace, "attempt")
                and hasattr(RM.ReminderFace, "scan")
                and hasattr(RM.ReminderFace, "on_accept")
                and hasattr(RM.ReminderFace, "banner_queue")
                and hasattr(RM.ReminderFace, "grant_authorization")
                and hasattr(RM.ReminderFace, "daily_sent_count")
                and hasattr(RM.ReminderFace,
                            "dual_timepoint_coverage")
                and 'self.disclaimer = comp.get("disclaimer")'
                in mod_src
                and mod_src.count("CREATE TABLE") == 2)
    ok6 = (ascii_ok and not net_hits
           and cfg_sha_in == cfg_sha_out and additive)
    record("AC-BQ6", ok6,
           "ascii=%s subjects=%d network-imports=%d cfg-sha-stable=%s"
           " additive=%s schema-tables=%d"
           % (ascii_ok, len(subjects), len(net_hits),
              cfg_sha_in == cfg_sha_out,
              additive, mod_src.count("CREATE TABLE")))

    # ---- AC-BQ7: delivery (registration self-check) ------------------
    reg_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    reg_src = open(reg_path, encoding="utf-8").read()
    registered = ('"member-banner-board"' in reg_src
                  and 'os.path.join("member", "test_banner_board.py"), 12'
                  in reg_src)
    ok7 = registered
    record("AC-BQ7", ok7,
           "suites-registry-row=%s criteria=12" % registered)

    # ---- AC-BQ8: read-cap contract + default fidelity ---------------
    face8, db8 = fresh_face(tmp, "bq8.db", load_cfg())
    face8.attempt("AV-B", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-B")
    face8.attempt("AV-G", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-G")
    plain = face8.banner_board()
    zeroed = face8.banner_board(limit=0)
    fid = (json.dumps(plain, sort_keys=True)
           == json.dumps(zeroed, sort_keys=True))
    seven = set(plain) == {"banner_board", "total", "by_status",
                           "by_reason", "ai_generated", "disclaimer",
                           "persistent"}
    capped = face8.banner_board(limit=1)
    new_keys = set(capped) - set(plain)
    ok8 = (fid and seven
           and new_keys == {"limit", "banner_board_total",
                            "returned", "truncated"}
           and capped["limit"] == 1
           and capped["banner_board_total"] == 2
           and capped["returned"] == 1
           and capped["truncated"] is True)
    record("AC-BQ8", ok8,
           "default-fidelity=%s seven-keys=%s new-keys=%s "
           "capped-envelope=%s"
           % (fid, seven, sorted(new_keys),
              [capped[k] for k in ("limit", "banner_board_total",
                                   "returned", "truncated")]))
    face8.close()

    # ---- AC-BQ9: bad limit params fail-closed ------------------------
    face9, db9 = fresh_face(tmp, "bq9.db", load_cfg())
    face9.attempt("AV-B", "renewal_notice", "renewal_due",
                  now=TS, period_key="PK-B")
    before9 = q(db9, "SELECT COUNT(*) FROM member_reminder_log")[0][0]
    rejects = []
    for bad in (-1, True, "2", 2.5, None):
        try:
            face9.banner_board(limit=bad)
            rejects.append((bad, "no-refusal"))
        except ValueError as exc:
            rejects.append((bad, RM.E_REM_BAD_LIMIT in str(exc)))
    after9 = q(db9, "SELECT COUNT(*) FROM member_reminder_log")[0][0]
    # dual-bad: missing resident compliance copy + bad limit -> the
    # compliance gate fires first (outermost face gate, order pinned)
    badc = json.loads(json.dumps(load_cfg()))
    badc.pop("compliance", None)
    face9b, _ = fresh_face(tmp, "bq9-probe.db", badc)
    try:
        face9b.banner_board(limit=-1)
        gate = "no-refusal"
    except ValueError as exc:
        gate = RM.E_REM_NO_DISCLAIMER in str(exc)
    ok9 = (all(r[1] is True for r in rejects)
           and before9 == after9 and gate is True)
    record("AC-BQ9", ok9,
           "rejects=%d/%d %s counts-stable=%s gate-order=%s"
           % (sum(1 for r in rejects if r[1] is True), len(rejects),
              [repr(r[0]) for r in rejects if r[1] is True],
              before9 == after9, gate))
    face9.close()
    face9b.close()

    # ---- AC-BQ10: tail-window truncation + mirror SQL ---------------
    # cap=2: two budgeted senders exhaust the daily cap first, then six
    # unbudgeted avatars all degrade as cap-skips; AV-B gets two rows
    # (distinct period keys) so total (7 skipped rows) and the avatar
    # -row count (6) provably differ - the two-unit distinction this
    # round's adjudication 1 exists for.
    face10, db10 = fresh_face(tmp, "bq10.db", load_cfg(cap=2))
    face10.grant_authorization("SE-1", "renewal_notice", "longterm")
    face10.grant_authorization("SE-2", "renewal_notice", "longterm")
    face10.attempt("SE-1", "renewal_notice", "renewal_due",
                   now=TS, period_key="SE-1")
    face10.attempt("SE-2", "renewal_notice", "renewal_due",
                   now=TS, period_key="SE-2")
    for av, keys in (("AV-A", ("PK-A",)),
                     ("AV-B", ("PK-B1", "PK-B2")),
                     ("AV-C", ("PK-C",)),
                     ("AV-D", ("PK-D",)),
                     ("AV-E", ("PK-E",)),
                     ("AV-F", ("PK-F",))):
        for pk in keys:
            face10.attempt(av, "renewal_notice", "renewal_due",
                           now=TS, period_key=pk)
    full = face10.banner_board()
    cap2 = face10.banner_board(limit=2)
    seq_full = [r["census_avatar_id"] for r in full["banner_board"]]
    seq_cap = [r["census_avatar_id"] for r in cap2["banner_board"]]
    mirror = [r[0] for r in q(
        db10, "SELECT census_avatar_id FROM member_reminder_log"
        " WHERE status LIKE 'skipped_%' GROUP BY census_avatar_id"
        " ORDER BY census_avatar_id DESC LIMIT 2")]
    mirror.reverse()
    row_keys = all(set(r) == {"census_avatar_id", "skipped",
                              "by_reason"}
                   for r in cap2["banner_board"])
    ok10 = (seq_full == ["AV-A", "AV-B", "AV-C", "AV-D", "AV-E",
                         "AV-F"]
            and full["total"] == 7
            and cap2["returned"] == 2 and cap2["truncated"] is True
            and cap2["banner_board_total"] == 6
            and cap2["total"] == 7
            and cap2["banner_board_total"] != cap2["total"]
            and seq_cap == seq_full[-2:] == ["AV-E", "AV-F"]
            and seq_cap == mirror
            and row_keys
            and cap2["by_status"] == full["by_status"]
            and cap2["by_reason"] == full["by_reason"])
    record("AC-BQ10", ok10,
           "seq-cap=%s mirror-match=%s board_total=%d total=%d "
           "units-differ=%s world-aggregates-stable=%s"
           % (seq_cap, seq_cap == mirror, cap2["banner_board_total"],
              cap2["total"],
              cap2["banner_board_total"] != cap2["total"],
              cap2["by_status"] == full["by_status"]))
    # face10 stays open: AC-BQ11 boundary states reuse this world

    # ---- AC-BQ11: boundary states (world carried from AC-BQ10) ------
    six = face10.banner_board(limit=6)
    over = face10.banner_board(limit=50)
    one = face10.banner_board(limit=1)
    face10.close()
    face11, db11 = fresh_face(tmp, "bq11.db", load_cfg())
    empty = face11.banner_board(limit=3)
    ok11 = (six["returned"] == 6 and six["truncated"] is False
            and six["banner_board_total"] == 6
            and [r["census_avatar_id"] for r in six["banner_board"]]
            == seq_full
            and over["returned"] == 6 and over["truncated"] is False
            and one["returned"] == 1 and one["truncated"] is True
            and [r["census_avatar_id"] for r in one["banner_board"]]
            == ["AV-F"]
            and empty["banner_board"] == [] and empty["returned"] == 0
            and empty["banner_board_total"] == 0
            and empty["truncated"] is False
            and empty["total"] == 0
            and set(empty) == {"banner_board", "total", "by_status",
                               "by_reason", "ai_generated",
                               "disclaimer", "persistent", "limit",
                               "banner_board_total", "returned",
                               "truncated"})
    record("AC-BQ11", ok11,
           "six=%s over=%s one=%s empty=%s keys=%d"
           % (six["returned"] == 6 and six["truncated"] is False,
              over["returned"] == 6 and over["truncated"] is False,
              one["returned"] == 1,
              empty["banner_board"] == [] and empty["returned"] == 0,
              len(set(empty))))
    face11.close()

    # ---- AC-BQ12: pure-read law, determinism, delivery ---------------
    face12, db12 = fresh_face(tmp, "bq12.db", load_cfg(cap=1))
    face12.grant_authorization("SE-9", "renewal_notice", "longterm")
    face12.attempt("SE-9", "renewal_notice", "renewal_due",
                   now=TS, period_key="SE-9")
    for av in ("AV-B", "AV-G", "AV-H"):
        face12.attempt(av, "renewal_notice", "renewal_due",
                       now=TS, period_key="PK-" + av)
    before12 = (q(db12, "SELECT COUNT(*) FROM"
                  " member_reminder_log")[0][0],
                q(db12, "SELECT COUNT(*) FROM"
                  " member_subscribe_grants")[0][0])
    r1 = face12.banner_board(limit=2)
    r2 = face12.banner_board(limit=2)
    after12 = (q(db12, "SELECT COUNT(*) FROM"
                 " member_reminder_log")[0][0],
               q(db12, "SELECT COUNT(*) FROM"
                 " member_subscribe_grants")[0][0])
    same12 = (json.dumps(r1, sort_keys=True)
              == json.dumps(r2, sort_keys=True))
    delivered = ('os.path.join("member", "test_banner_board.py"), 12'
                 in reg_src
                 and hasattr(RM, "E_REM_BAD_LIMIT")
                 and RM.E_REM_BAD_LIMIT == "E_REM_BAD_LIMIT")
    ok12 = (before12 == after12 and same12 and delivered)
    record("AC-BQ12", ok12,
           "counts-stable=%s double-call-identical=%s delivery=%s"
           % (before12 == after12, same12, delivered))
    face12.close()

    shutil.rmtree(tmp, ignore_errors=True)
    if len(RESULTS) != EXPECTED:
        print("SUITE FAIL: criteria drift %d != %d"
              % (len(RESULTS), EXPECTED))
        return 2
    failed = [ac for ac, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL: %s" % ",".join(failed))
        return 2
    print("SUITE PASS: %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
