"""Event-ticket audit-board month-set telescoping cross probe
(BigDomain R1834 tech-queue row; seed = eventtickets.py
event_audit_board window parameterization R1826).

Measurement face per the R1727 qa_mtime_probe / R1806
water_consistency_probe precedent: NOT in the reconcile_all
SUITES registry, zero RUNNER/matrix surface, zero product
bytes written. The probe builds a fresh shared-birth world in
a temp dir - real product-API rows stamped in the current
month plus test-side direct fixture rows pinned into two past
months (the R1730 family precedent, noted here: the product
gates are bypassed on purpose so the history months pin
deterministically; the injected rows respect the temporal
order the product flow enforces - a check-in row only exists
with its purchase month at or before it).

Pre-registered criteria AC-MC1..AC-MC5 live in the R1834
tech.md claim row (registered before this code existed;
honesty law):

  - AC-MC1 observed-month set three-way: engine-side
    DISTINCT union of the two record-time prefixes == the
    planted month-abstract set (all months derived by
    pushing the wall clock back - zero hardcoded months, the
    R1813 law); the future month is absent; the current
    month carries real-API rows on both faces; every
    observed-month windowed read walks zero-reject.
  - AC-MC2 flow-face telescoping (core): for every session
    and for the board totals, the sum of the per-month
    windowed reads equals the full-window read for all three
    flow faces (sold / admitted / revenue); a manual SQL
    third path cross-checks every month x session cell.
  - AC-MC3 no_show snapshot face: no_show is an
    end-of-window cumulative snapshot, NOT additive - the
    sum of monthly no_show values is honestly shown to
    differ from the full-window no_show (the R1826 AC-EAW4
    verdict carried in-probe as the in-register note);
    every windowed no_show still equals the manual
    cumulative SQL and stays >= 0.
  - AC-MC4 dense axis preservation: all five reads (default
    + m1 + m2 + cur + fut) return the identical
    registry-driven session_key axis in ascending order, the
    future window showing all-zero cells with the full axis.
  - AC-MC5 pure-read + determinism + hygiene: three-table
    counts flat across every read (mode=ro side); windowed
    double-call byte-identical; probe source pure ASCII with
    zero network imports; four product files sha-frozen
    before/after; the probe filename absent from
    reconcile_all.py (measurement face stays out of the
    SUITES registry).

  R1843 read-cap x month-window orthogonal combination
  (AC-MC6..AC-MC9; the L133 tech-queue seed, criteria
  pre-registered in the R1843 claim row before this code
  existed): every window shape (None + m1 + m2 + cur + fut)
  crossed with every cap shape (1, 2, 4, 50) checks the
  capped read against the tail-N subsequence of that
  window's full read element-wise, the mirror SQL
  DESC-LIMIT reversal third path, the four-key overflow
  block value alignment (total = the in-window full count
  == the registry COUNT, never the post-truncation count -
  the dense registry axis is window-invariant), the
  window-key coexistence law, and the zero-registration
  sub-world honest-empty capped read (the only zero-row
  shape a registry-driven board can produce). Measurement
  face stays out of the SUITES registry (R1727 precedent).

Single-source law ("lock the source"): the observed-month set
and every cross-check derive from the product faces and the
engine rows themselves - zero hardcoded month rosters, zero
second aggregation engine.

This probe source stays pure ASCII per the encoding
discipline. Usage: python eventtickets_monthcross_probe.py
"""

import datetime
import hashlib
import json
import os
import sqlite3
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_LEDGER_DIR = os.path.join(os.path.dirname(_HERE), "sandbox",
                          "ledger")
for _p in (_HERE, _LEDGER_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ledger as L                       # noqa: E402
import eventtickets as T                 # noqa: E402

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: virtual event"
              " tickets grant admission only, not investment"
              " advice")

SESSION_KEYS = ("alpha-gala", "zulu-empty", "xmonth-cross",
                "inmonth-full")

ROW_KEYS = frozenset((
    "session_key", "title", "ai_label", "sold", "admitted",
    "no_show", "revenue", "admission_rate"))


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def _prev_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m -= 1
    if m == 0:
        y, m = y - 1, 12
    return "%04d-%02d" % (y, m)


def _next_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m += 1
    if m == 13:
        y, m = y + 1, 1
    return "%04d-%02d" % (y, m)


def _stamp(ym, day):
    return "%s-%02dT12:00:00Z" % (ym, day)


def _sha16(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


def _ro_conn(db_path):
    return sqlite3.connect(
        "file:" + db_path.replace("\\", "/") + "?mode=ro",
        uri=True)


def main():
    cur_m = datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m")
    m2 = _prev_month(cur_m)
    m1 = _prev_month(m2)
    fut = _next_month(cur_m)

    frozen = {}
    for rel in ("eventtickets.py", "ledger.py", "config.json"):
        frozen[rel] = _sha16(os.path.join(_LEDGER_DIR, rel))
    runner_path = os.path.join(os.path.dirname(_LEDGER_DIR),
                               "reconcile_all.py")
    frozen["reconcile_all.py"] = _sha16(runner_path)

    tmp = tempfile.mkdtemp(prefix="et-monthcross-")
    with open(os.path.join(_LEDGER_DIR, "config.json"),
              encoding="utf-8") as handle:
        cfg = json.load(handle)
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    tf = T.EventTicketFace(led, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 2000, "SETUP-MC-A",
                     "settlement")
    for who, amount, tag in (("alice", 100, "a"),
                             ("bob", 100, "b")):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag,
                   "probe funding " + who)

    # real-API world (rows stamped in the current month)
    s_gala = tf.register_session("alpha-gala", "Alpha Gala Night",
                                 10, 20, 5, 2, False)
    tf.register_session("zulu-empty", "Zulu Registered No Sales",
                        0, 5, 1, 1, True)
    tf.buy_ticket("usr:alice", s_gala["session_id"], 10,
                  "order:mc1")
    tf.buy_ticket("usr:alice", s_gala["session_id"], 15,
                  "order:mc2")
    tf.buy_ticket("usr:bob", s_gala["session_id"], 12,
                  "order:mc3")
    tf.admit("usr:alice", s_gala["session_id"], 12)

    # test-side fixture rows (R1730 family precedent): product
    # gates bypassed on purpose; temporal order respected.
    s_x = tf.register_session("xmonth-cross", "Cross Month Case",
                              0, 5, 3, 1, False)
    s_i = tf.register_session("inmonth-full",
                              "In Month Full Funnel", 0, 5, 4, 1,
                              False)
    wconn = sqlite3.connect(db_path)
    wconn.execute(
        "INSERT INTO ticket_purchases (session_id, buyer_id,"
        " purchase_ref, price_paid, spend_tx, purchase_window,"
        " purchased_utc) VALUES (?,?,?,?,?,?,?)",
        (s_x["session_id"], "usr:fx", "inject:fx1", 3,
         "inject:spend-x", 1, _stamp(m1, 5)))
    wconn.execute(
        "INSERT INTO ticket_checkins (session_id, account_id,"
        " at_window, checked_utc) VALUES (?,?,?,?)",
        (s_x["session_id"], "usr:fx", 2, _stamp(m2, 7)))
    wconn.execute(
        "INSERT INTO ticket_purchases (session_id, buyer_id,"
        " purchase_ref, price_paid, spend_tx, purchase_window,"
        " purchased_utc) VALUES (?,?,?,?,?,?,?)",
        (s_i["session_id"], "usr:fi", "inject:fi1", 4,
         "inject:spend-i", 1, _stamp(m2, 9)))
    wconn.execute(
        "INSERT INTO ticket_checkins (session_id, account_id,"
        " at_window, checked_utc) VALUES (?,?,?,?)",
        (s_i["session_id"], "usr:fi", 2, _stamp(m2, 21)))
    wconn.commit()
    wconn.close()

    ro = _ro_conn(db_path)

    def _table_counts():
        return tuple(
            ro.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
            for t in ("ticket_sessions", "ticket_purchases",
                      "ticket_checkins"))

    def _sid(key):
        return ro.execute(
            "SELECT session_id FROM ticket_sessions"
            " WHERE session_key = ?", (key,)).fetchone()[0]

    def _manual_flow(sid, w):
        s = ro.execute(
            "SELECT COUNT(*) FROM ticket_purchases"
            " WHERE session_id = ? AND"
            " substr(purchased_utc, 1, 7) = ?",
            (sid, w)).fetchone()[0]
        a = ro.execute(
            "SELECT COUNT(*) FROM ticket_checkins"
            " WHERE session_id = ? AND"
            " substr(checked_utc, 1, 7) = ?",
            (sid, w)).fetchone()[0]
        rev = ro.execute(
            "SELECT COALESCE(SUM(price_paid), 0) FROM"
            " ticket_purchases WHERE session_id = ? AND"
            " substr(purchased_utc, 1, 7) = ?",
            (sid, w)).fetchone()[0]
        return int(s), int(a), int(rev)

    def _manual_cumulative_noshow(sid, w):
        p = ro.execute(
            "SELECT COUNT(*) FROM ticket_purchases"
            " WHERE session_id = ? AND"
            " substr(purchased_utc, 1, 7) <= ?",
            (sid, w)).fetchone()[0]
        c = ro.execute(
            "SELECT COUNT(*) FROM ticket_checkins"
            " WHERE session_id = ? AND"
            " substr(checked_utc, 1, 7) <= ?",
            (sid, w)).fetchone()[0]
        return int(p) - int(c)

    observed_windows = (m1, m2, cur_m)
    all_windows = (None, m1, m2, cur_m, fut)

    boards = {}
    for w in all_windows:
        boards[w] = {r["session_key"]: r for r in
                     tf.event_audit_board(w)
                     ["event_audit_board"]}

    # -- [1] observed month set three-way ----------------------
    print("[1] month-set three-way", flush=True)
    sql_months = set()
    for (prefix,) in ro.execute(
            "SELECT DISTINCT substr(purchased_utc, 1, 7) FROM"
            " ticket_purchases"):
        sql_months.add(prefix)
    for (prefix,) in ro.execute(
            "SELECT DISTINCT substr(checked_utc, 1, 7) FROM"
            " ticket_checkins"):
        sql_months.add(prefix)
    planted = {m1, m2, cur_m}
    ok1_set = sql_months == planted
    ok1_fut = fut not in sql_months
    cur_buys = ro.execute(
        "SELECT COUNT(*) FROM ticket_purchases WHERE"
        " substr(purchased_utc, 1, 7) = ?",
        (cur_m,)).fetchone()[0]
    cur_checks = ro.execute(
        "SELECT COUNT(*) FROM ticket_checkins WHERE"
        " substr(checked_utc, 1, 7) = ?",
        (cur_m,)).fetchone()[0]
    ok1_real = cur_buys >= 1 and cur_checks >= 1
    ok1_walk = all(w in boards for w in observed_windows)
    record("AC-MC1", ok1_set and ok1_fut and ok1_real
           and ok1_walk,
           "engine DISTINCT union %s == planted month-abstract"
           " set %s = %s; future month absent = %s; cur-month"
           " real-API rows on both faces (buys=%d checks=%d)"
           " = %s; every observed-month windowed read walks"
           " zero-reject = %s"
           % (sorted(sql_months), sorted(planted), ok1_set,
              ok1_fut, cur_buys, cur_checks, ok1_real,
              ok1_walk))

    # -- [2] flow-face telescoping (core) -----------------------
    print("[2] flow-face telescoping", flush=True)
    full_rows = boards[None]
    ok2_session = True
    ok2_third = True
    trace2 = []
    for key in SESSION_KEYS:
        sid = _sid(key)
        s_sum = a_sum = r_sum = 0
        for w in observed_windows:
            row = boards[w][key]
            s_sum += row["sold"]
            a_sum += row["admitted"]
            r_sum += row["revenue"]
            ms, ma, mrev = _manual_flow(sid, w)
            ok2_third = ok2_third and (
                row["sold"] == ms
                and row["admitted"] == ma
                and row["revenue"] == mrev)
        fr = full_rows[key]
        ok2_session = ok2_session and (
            s_sum == fr["sold"] and a_sum == fr["admitted"]
            and r_sum == fr["revenue"])
        trace2.append("%s sum(s/a/r)=%d/%d/%d full=%d/%d/%d"
                      % (key, s_sum, a_sum, r_sum, fr["sold"],
                         fr["admitted"], fr["revenue"]))
    t_s = t_a = t_r = 0
    for w in observed_windows:
        rows = boards[w]
        t_s += sum(r["sold"] for r in rows.values())
        t_a += sum(r["admitted"] for r in rows.values())
        t_r += sum(r["revenue"] for r in rows.values())
    f_s = sum(r["sold"] for r in full_rows.values())
    f_a = sum(r["admitted"] for r in full_rows.values())
    f_r = sum(r["revenue"] for r in full_rows.values())
    ok2_board = (t_s == f_s and t_a == f_a and t_r == f_r)
    record("AC-MC2", ok2_session and ok2_board and ok2_third,
           "per-session telescoping sum(months) == full for"
           " sold/admitted/revenue [%s] = %s; board totals"
           " sum=%d/%d/%d full=%d/%d/%d = %s; manual SQL third"
           " path equal on every month x session cell = %s"
           % ("; ".join(trace2), ok2_session, t_s, t_a, t_r,
              f_s, f_a, f_r, ok2_board, ok2_third))

    # -- [3] no_show snapshot face (non-additive, in-register) ---
    print("[3] no_show snapshot face", flush=True)
    ok3_manual = True
    ok3_nonneg = True
    for w in (m1, m2, cur_m, fut):
        for key, row in boards[w].items():
            ok3_manual = ok3_manual and (
                row["no_show"] == _manual_cumulative_noshow(
                    _sid(key), w))
            ok3_nonneg = ok3_nonneg and row["no_show"] >= 0
    x_full = full_rows["xmonth-cross"]["no_show"]
    x_sum = sum(boards[w]["xmonth-cross"]["no_show"]
                for w in observed_windows)
    ns_full = sum(r["no_show"] for r in full_rows.values())
    ns_sum = sum(sum(r["no_show"] for r in boards[w].values())
                for w in observed_windows)
    ok3_nonadd = (x_sum != x_full) and (ns_sum != ns_full)
    record("AC-MC3", ok3_manual and ok3_nonneg and ok3_nonadd,
           "in-register note: no_show = end-of-window cumulative"
           " snapshot (R1826 AC-EAW4), NOT additive, excluded"
           " from the telescoping sum; honest non-additivity"
           " reading: xmonth-cross sum(months)=%d vs full=%d,"
           " board sum(months)=%d vs full=%d (differ = %s);"
           " every windowed no_show == manual cumulative SQL"
           " across %s + cur + fut = %s; no_show >= 0 = %s"
           % (x_sum, x_full, ns_sum, ns_full, ok3_nonadd,
              m1 + "/" + m2, ok3_manual, ok3_nonneg))

    # -- [4] dense axis preservation -----------------------------
    print("[4] dense axis preservation", flush=True)
    axis = list(SESSION_KEYS)
    ok4_axis = True
    ok4_order = True
    ok4_fut_zero = True
    for w in all_windows:
        env = tf.event_audit_board(w)
        rows = env["event_audit_board"]
        keys_now = [r["session_key"] for r in rows]
        ok4_axis = ok4_axis and sorted(keys_now) == sorted(axis)
        ok4_order = ok4_order and keys_now == sorted(axis)
        if w == fut:
            ok4_fut_zero = ok4_fut_zero and all(
                r["sold"] == 0 and r["admitted"] == 0
                and r["revenue"] == 0 for r in rows)
    record("AC-MC4", ok4_axis and ok4_order and ok4_fut_zero,
           "all five reads (default + %s + %s + cur + fut)"
           " carry the identical registry-driven session_key"
           " axis = %s; ascending order in every read = %s;"
           " future window all-zero cells with the full axis"
           " in place = %s"
           % (m1, m2, ok4_axis, ok4_order, ok4_fut_zero))

    # -- [5] pure-read + determinism + hygiene ------------------
    print("[5] pure-read + determinism + hygiene", flush=True)
    counts0 = _table_counts()
    for w in all_windows:
        tf.event_audit_board(w)
    counts1 = _table_counts()
    ok5_pure = counts0 == counts1
    det_a = json.dumps(tf.event_audit_board(m2), sort_keys=True)
    det_b = json.dumps(tf.event_audit_board(m2), sort_keys=True)
    ok5_det = det_a == det_b
    with open(os.path.abspath(__file__), encoding="utf-8") as h:
        own_src = h.read()
    non_ascii = sum(1 for ch in own_src if ord(ch) > 127)
    import_lines = [ln for ln in own_src.splitlines()
                    if ln.startswith("import ")
                    or ln.startswith("from ")]
    net_imports = [ln for ln in import_lines
                   if any(word in ln for word in
                          ("urllib", "requests", "socket",
                           "http"))]
    ok5_ascii = non_ascii == 0 and not net_imports
    ok5_frozen = all(
        _sha16(os.path.join(_LEDGER_DIR, rel)) == frozen[rel]
        for rel in ("eventtickets.py", "ledger.py",
                    "config.json"))
    ok5_frozen = ok5_frozen and (
        _sha16(runner_path) == frozen["reconcile_all.py"])
    with open(runner_path, encoding="utf-8") as h:
        runner_src = h.read()
    ok5_registry = ("eventtickets_monthcross_probe"
                    not in runner_src)
    record("AC-MC5", ok5_pure and ok5_det and ok5_ascii
           and ok5_frozen and ok5_registry,
           "three-table counts flat %s -> %s = %s; windowed"
           " double-call byte-identical = %s; probe source"
           " pure ASCII (%d non-ascii) with zero network"
           " imports (%d) = %s; four product files sha-frozen"
           " = %s; probe filename absent from reconcile_all.py"
           " SUITES registry (measurement face, R1727"
           " precedent) = %s"
           % (counts0, counts1, ok5_pure, ok5_det, non_ascii,
              len(net_imports), ok5_ascii, ok5_frozen,
              ok5_registry))

    # -- [6] read-cap x window orthogonal combination (R1843) ----
    print("[6] read-cap x window orthogonal combination",
          flush=True)
    caps = (1, 2, 4, 50)
    cap_windows = (None, m1, m2, cur_m, fut)
    sess_count = ro.execute(
        "SELECT COUNT(*) FROM ticket_sessions").fetchone()[0]
    counts6a = _table_counts()
    ok6_rows = True
    ok6_env = True
    ok6_wkey = True
    ok7_mirror = True
    combos = 0
    trunc_seen = 0
    full_seen = 0
    for w in cap_windows:
        full_rows_list = tf.event_audit_board(
            w)["event_audit_board"]
        for n in caps:
            env = tf.event_audit_board(w, n)
            rows = env["event_audit_board"]
            combos += 1
            expect = full_rows_list[-n:]
            ok6_rows = ok6_rows and (
                json.dumps(rows, sort_keys=True)
                == json.dumps(expect, sort_keys=True))
            ok6_rows = ok6_rows and all(
                frozenset(r) == ROW_KEYS for r in rows)
            ok6_env = ok6_env and (
                env.get("limit") == n
                and env.get("total") == len(full_rows_list)
                and env.get("total") == sess_count
                and env.get("returned") == len(rows)
                and env.get("truncated")
                == (len(rows) < len(full_rows_list)))
            if w is None:
                ok6_wkey = ok6_wkey and "window" not in env
            else:
                ok6_wkey = ok6_wkey and env.get("window") == w
            mirror = [r[0] for r in ro.execute(
                "SELECT session_key FROM ticket_sessions"
                " ORDER BY session_key DESC LIMIT ?",
                (n,)).fetchall()]
            mirror.reverse()
            ok7_mirror = ok7_mirror and (
                mirror == [r["session_key"] for r in rows])
            if len(rows) < len(full_rows_list):
                trunc_seen += 1
            else:
                full_seen += 1
    record("AC-MC6", ok6_rows and ok6_env and ok6_wkey,
           "combos=%d (5 window shapes x 4 caps): capped read"
           " == tail-N subsequence of that window's full read"
           " element-wise (json byte-identical + 8-key row"
           " field set) = %s; overflow block 4-key alignment"
           " {limit,total,returned,truncated} with total =="
           " in-window full count == registry COUNT(*)=%d"
           " (dense registry axis, window-invariant) = %s;"
           " window-key coexistence law (present == W / absent"
           " when None) = %s; truncation exercised in %d"
           " combos, full read carried in %d"
           % (combos, ok6_rows, sess_count, ok6_env, ok6_wkey,
              trunc_seen, full_seen))
    record("AC-MC7", ok7_mirror,
           "mirror SQL third path (ORDER BY session_key DESC"
           " LIMIT N, reversed back to ascending) == product"
           " row order on every one of the %d combos = %s"
           % (combos, ok7_mirror))

    # zero-registration sub-world: the only zero-row shape a
    # registry-driven board can produce (fresh db, zero
    # sessions, zero fixtures; the R1840 AC-ETL4 precedent).
    db2_path = os.path.join(tmp, "ledger-empty.db")
    led2 = L.Ledger(db2_path, cfg)
    tf2 = T.EventTicketFace(led2, DISCLAIMER)
    ro2 = _ro_conn(db2_path)
    ok8_empty = True
    ok8_env = True
    ok8_wkey = True
    ok8_mirror = True
    for w in (cur_m, None):
        env = tf2.event_audit_board(w, 2)
        rows = env["event_audit_board"]
        ok8_empty = ok8_empty and rows == []
        ok8_env = ok8_env and (
            env.get("limit") == 2 and env.get("total") == 0
            and env.get("returned") == 0
            and env.get("truncated") is False)
        if w is None:
            ok8_wkey = ok8_wkey and "window" not in env
        else:
            ok8_wkey = ok8_wkey and env.get("window") == w
        mirror = [r[0] for r in ro2.execute(
            "SELECT session_key FROM ticket_sessions"
            " ORDER BY session_key DESC LIMIT 2").fetchall()]
        mirror.reverse()
        ok8_mirror = ok8_mirror and mirror == []
    zero_counts = tuple(
        ro2.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
        for t in ("ticket_sessions", "ticket_purchases",
                  "ticket_checkins"))
    ok8_zero_rows = zero_counts == (0, 0, 0)
    record("AC-MC8", ok8_empty and ok8_env and ok8_wkey
           and ok8_mirror and ok8_zero_rows,
           "zero-registration sub-world: board(cur,2) and"
           " board(None,2) both honest empty truncated reads"
           " rows==[] with the 4-key block carried"
           " {limit=2,total=0,returned=0,truncated=False} ="
           " %s; window-key law in the zero world = %s; zero"
           " mirror SQL == [] = %s; three-table counts all"
           " zero %s = %s"
           % (ok8_empty and ok8_env, ok8_wkey, ok8_mirror,
              zero_counts, ok8_zero_rows))
    counts6b = _table_counts()
    det6a = json.dumps(tf.event_audit_board(m2, 2),
                       sort_keys=True)
    det6b = json.dumps(tf.event_audit_board(m2, 2),
                       sort_keys=True)
    ok9_counts = counts6a == counts6b
    ok9_det = det6a == det6b
    ok9_frozen = all(
        _sha16(os.path.join(_LEDGER_DIR, rel)) == frozen[rel]
        for rel in ("eventtickets.py", "ledger.py",
                    "config.json"))
    ok9_frozen = ok9_frozen and (
        _sha16(runner_path) == frozen["reconcile_all.py"])
    ok9_registry = ("eventtickets_monthcross_probe"
                    not in runner_src)
    record("AC-MC9", ok9_counts and ok9_det and ok9_frozen
           and ok9_registry,
           "main-world three-table counts flat %s -> %s across"
           " the %d capped reads = %s; representative combo"
           " (m2, 2) double-call byte-identical = %s; four"
           " product files sha-frozen after the whole"
           " section = %s; probe filename absent from the"
           " reconcile_all.py SUITES registry (measurement"
           " face, R1727 precedent) = %s"
           % (counts6a, counts6b, combos, ok9_counts, ok9_det,
              ok9_frozen, ok9_registry))
    ro2.close()
    tf2.close()
    led2.close()

    ro.close()
    tf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("PROBE VERDICT %s (%d/%d)" % (
        "CONSISTENT" if fail == 0 else "INCONSISTENT",
        len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
