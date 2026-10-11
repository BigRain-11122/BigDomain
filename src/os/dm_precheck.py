r"""dm_precheck - engine-semantics empirical pin for the R1838
sqlite_sequence bookkeeping-row DELETE missing-state probe section.

Mirrors the probe world end state left by [21] (R1832): ids 1..14
live, ids 15..26 consumed then deleted, sqlite_sequence.seq at 26.
The phases below replay the probe section's fixed operation order
with the same structural constants (reused id 15, re-armed id 27,
high-water 26 -> 27).

Facts to pin (R1704 law: engine semantics pinned empirically before
the probe section lands - hw_precheck R1823 / tp_precheck R1832
precedents):

F1  A direct DELETE evaporates the bookkeeping row; live rows are
    untouched and the missing state is observable (COUNT == 0).
F2  With the row missing, AUTOINCREMENT degrades to the plain
    rowid rule: the next INSERT allocates max(rowid)+1 == 15 - a
    reuse of the already-used-and-deleted id 15 (the same
    lost-guard construction as the [21] UPDATE rollback, via the
    second single point of failure), NOT seq+1 == 27.
F3  That INSERT self-rebuilds the bookkeeping row carrying the
    newly allocated value (seq == 15).
F4  After the rebuild the only correct restore at that point is an
    UPDATE on the rebuilt row (15 -> 26); the allocator only sees
    the row, so the re-armed allocation proof of F6 covers this
    same post-restore state.
F5  A naive re-INSERT while the rebuilt row exists is a hazard:
    sqlite_sequence.name carries no UNIQUE, so a second row is
    created and the plain ro fetchone keeps reading the first
    (old) row - the first precheck draft's restore ruling,
    falsified empirically here and amended in tech.md before any
    probe code landed (pinned at the final state with a 99
    sentinel: two rows, fetchone still the old one).
F6  A direct re-INSERT while the row is truly missing (no INSERT
    in between, so no self-rebuild yet) is a legal restore: the
    row lands at the true high-water 26, zero ids consumed, and
    the next INSERT allocates 27 == seq+1 - the no-reuse guarantee
    re-armed by a pure bookkeeping write.
F7  Deleting a table row never touches the bookkeeping row (the
    seq high-water never retreats, [20] AC-HW4 law); a consuming
    INSERT advances it (26 -> 27) and the delete keeps 27.

Pure stdlib, pure ASCII, temp-dir only, zero repo writes.
"""

import os
import sqlite3
import tempfile


def main():
    workdir = tempfile.mkdtemp(prefix="dm_precheck_")
    db = os.path.join(workdir, "dm.db")
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE t (id INTEGER PRIMARY KEY"
        " AUTOINCREMENT, v TEXT)")
    # assign ids 1..26 in operation order (probe census shape)
    for i in range(1, 27):
        conn.execute("INSERT INTO t (v) VALUES (?)", ("x%d" % i,))
    # inject-then-delete rounds consume 15..26 (live max back to 14)
    for i in range(15, 27):
        conn.execute("DELETE FROM t WHERE id = ?", (i,))
    conn.commit()

    # F0: base state matches the probe world end state
    seq_pre = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    live_n = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    live_max = conn.execute(
        "SELECT MAX(id) FROM t").fetchone()[0]
    f0 = (seq_pre == 26 and live_n == 14 and live_max == 14)

    # F1: evaporate the bookkeeping row (probe SQD1)
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 't'")
    conn.commit()
    seq_rows_missing = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    live_missing = conn.execute(
        "SELECT COUNT(*) FROM t").fetchone()[0]
    f1 = (seq_rows_missing == 0 and live_missing == 14)

    # F2 + F3: degraded allocation reuses id 15; self-rebuild
    # (probe SQD2)
    conn.execute("INSERT INTO t (v) VALUES ('reuse')")
    reuse_id = conn.execute(
        "SELECT last_insert_rowid()").fetchone()[0]
    live_mid = conn.execute(
        "SELECT COUNT(*) FROM t").fetchone()[0]
    rebuilt = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()
    conn.commit()
    f2 = (reuse_id == 15 and live_mid == 15)
    f3 = (rebuilt is not None and rebuilt[0] == 15)

    # F4: UPDATE on the rebuilt row restores the high-water
    # (probe SQD3)
    conn.execute(
        "UPDATE sqlite_sequence SET seq = 26 WHERE name = 't'")
    conn.commit()
    seq_up_rows = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    seq_up = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    live_up = conn.execute(
        "SELECT COUNT(*) FROM t").fetchone()[0]
    f4 = (seq_up_rows == 1 and seq_up == 26 and live_up == 15)

    # F7a: delete the reused row; world re-green, seq keeps 26
    # (probe SQD4)
    conn.execute("DELETE FROM t WHERE id = ?", (reuse_id,))
    conn.commit()
    live_green = conn.execute(
        "SELECT COUNT(*) FROM t").fetchone()[0]
    seq_green = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    f7a = (live_green == 14 and seq_green == 26)

    # F6: re-INSERT while truly missing = legal restore, zero
    # consume; next INSERT re-armed to 27 (probe SQD5)
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 't'")
    conn.commit()
    missing2 = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    conn.execute(
        "INSERT INTO sqlite_sequence (name, seq)"
        " VALUES ('t', 26)")
    conn.commit()
    ri_rows = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    ri_seq = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    ri_live = conn.execute(
        "SELECT COUNT(*) FROM t").fetchone()[0]
    conn.execute("INSERT INTO t (v) VALUES ('rearm')")
    rearm_id = conn.execute(
        "SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    f6 = (missing2 == 0 and ri_rows == 1 and ri_seq == 26
          and ri_live == 14 and rearm_id == ri_seq + 1 == 27)

    # F7b: delete the rearm row; seq keeps the advanced 27
    conn.execute("DELETE FROM t WHERE id = ?", (rearm_id,))
    conn.commit()
    live_final = conn.execute(
        "SELECT COUNT(*) FROM t").fetchone()[0]
    seq_final = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    f7b = (live_final == 14 and seq_final == 27)

    # F5: hazard pin at the final state - naive re-INSERT while
    # the row exists creates a duplicate (name has no UNIQUE)
    # and the plain ro fetchone keeps reading the first (old)
    # row; the 99 sentinel never surfaces.
    conn.execute(
        "INSERT INTO sqlite_sequence (name, seq)"
        " VALUES ('t', 99)")
    conn.commit()
    dup_rows = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    first_row_seq = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    f5 = (dup_rows == 2 and first_row_seq == 27)
    # hazard cleanup: both rows out, one honest row back at 27
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 't'")
    conn.execute(
        "INSERT INTO sqlite_sequence (name, seq)"
        " VALUES ('t', 27)")
    conn.commit()
    clean_rows = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    clean_seq = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    clean_live = conn.execute(
        "SELECT COUNT(*) FROM t").fetchone()[0]
    conn.close()
    f5_clean = (clean_rows == 1 and clean_seq == 27
                and clean_live == 14)

    checks = [
        ("F0 base-state 26/14/14", f0),
        ("F1 bookkeeping-evaporated", f1),
        ("F2 degraded-allocation-reuse-15", f2),
        ("F3 self-rebuild-with-new-value", f3),
        ("F4 update-restore-on-rebuilt", f4),
        ("F7a re-green-delete-keeps-26", f7a),
        ("F6 reinsert-while-missing-rearm-27", f6),
        ("F7b final-delete-keeps-27", f7b),
        ("F5 dup-row-hazard-stale-read", f5),
        ("F5 hazard-cleanup", f5_clean),
    ]
    print("DM-PRECHECK (sqlite %s)" % sqlite3.sqlite_version)
    for name, ok in checks:
        print("  %-34s %s" % (name, "PASS" if ok else "FAIL"))
    verdict = "PASS" if all(ok for _, ok in checks) else "FAIL"
    print("DM-PRECHECK VERDICT: %s" % verdict)
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
