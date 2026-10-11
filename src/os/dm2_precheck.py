r"""dm2_precheck - engine-semantics empirical pin for the R1844
sqlite_sequence duplicate-bookkeeping-row probe section.

dm_precheck (R1838) pinned the duplicate-row READ face (F5: name
carries no UNIQUE, second row lands, plain ro fetchone keeps
reading the first/old row) but the ALLOCATOR face with a second
row present was never pinned - the R1838 pin cleaned the hazard
up immediately without letting AUTOINCREMENT run beside it.

This precheck mirrors the probe world end state left by [22]
(R1838): ids 1..14 live, ids 15..26 consumed then deleted, one
rearm consume to 27 then deleted, bookkeeping row at high-water
27. Phases replay the R1844 section's fixed operation order.

Facts to pin (R1704 law: engine semantics pinned empirically
before the probe section lands - dm_precheck R1838 / hw_precheck
R1823 / tp_precheck R1832 precedents):

G1  Injecting a second bookkeeping row (same name, sentinel seq
    99) constructs the duplicate: COUNT == 2, the plain ro
    fetchone reads the first/old row (27, stale-read trap), and
    fetchall exposes both rows (the sentinel IS in the table -
    only the naive single-read misses it).
G2  With the duplicate present the AUTOINCREMENT allocator's
    next INSERT allocation and the post-INSERT bookkeeping-row
    values are engine facts to be read here, not assumed: the
    allocated id and both rows' seq values are pinned (which
    row the allocator consults; whether the post-alloc UPDATE
    touches one or both rows).
G3  Cleanup recovery: delete the allocated row (live face back
    to 14), delete ALL bookkeeping rows for the name, re-insert
    one honest row at the pinned allocated id (consume-no-
    retreat law: the allocated id was used, so the honest
    high-water is the allocated id, NOT the pre-section 27) ->
    COUNT == 1, seq == allocated id, live == 14.
G4  Re-arm proof: after the cleanup the next INSERT allocates
    seq+1 (the no-reuse guarantee restored by a pure
    bookkeeping write), then the delete keeps the advanced
    high-water.

Pure stdlib, pure ASCII, temp-dir only, zero repo writes.
"""

import os
import sqlite3
import tempfile


def main():
    workdir = tempfile.mkdtemp(prefix="dm2_precheck_")
    db = os.path.join(workdir, "dm2.db")
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE t (id INTEGER PRIMARY KEY"
        " AUTOINCREMENT, v TEXT)")
    # assign ids 1..27 in operation order, consume 15..27
    # (probe [22] end state: live 1..14, high-water 27)
    for i in range(1, 28):
        conn.execute("INSERT INTO t (v) VALUES (?)", ("x%d" % i,))
    for i in range(15, 28):
        conn.execute("DELETE FROM t WHERE id = ?", (i,))
    conn.commit()

    # G0: base state matches the probe [22] end state
    g0_seq = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    g0_live = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    g0_rows = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    g0 = (g0_seq == 27 and g0_live == 14 and g0_rows == 1)

    # G1: construct the duplicate (99 sentinel) - read-order trap
    conn.execute(
        "INSERT INTO sqlite_sequence (name, seq)"
        " VALUES ('t', 99)")
    conn.commit()
    g1_rows = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    g1_first = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    g1_all = [r[0] for r in conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'")]
    g1 = (g1_rows == 2 and g1_first == 27 and g1_all == [27, 99])

    # G2: allocator behavior with the duplicate present
    conn.execute("INSERT INTO t (v) VALUES ('dup-alloc')")
    g2_alloc_id = conn.execute(
        "SELECT last_insert_rowid()").fetchone()[0]
    g2_live = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    g2_all = [r[0] for r in conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'")]
    conn.commit()
    g2 = (isinstance(g2_alloc_id, int) and g2_live == 15
          and len(g2_all) >= 1)

    # G3: cleanup recovery - delete the allocated row, wipe ALL
    # bookkeeping rows for the name, one honest row back at the
    # pinned allocated id (consume-no-retreat: the allocated id
    # was used, honest high-water == allocated id)
    conn.execute("DELETE FROM t WHERE id = ?", (g2_alloc_id,))
    conn.commit()
    g3_live = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    conn.execute(
        "DELETE FROM sqlite_sequence WHERE name = 't'")
    g3_zero = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    conn.execute(
        "INSERT INTO sqlite_sequence (name, seq)"
        " VALUES ('t', ?)", (g2_alloc_id,))
    conn.commit()
    g3_rows = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    g3_seq = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    g3 = (g3_live == 14 and g3_zero == 0 and g3_rows == 1
          and g3_seq == g2_alloc_id)

    # G4: re-arm proof - next INSERT allocates seq+1, delete
    # keeps the advanced high-water
    conn.execute("INSERT INTO t (v) VALUES ('rearm')")
    g4_alloc = conn.execute(
        "SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.execute("DELETE FROM t WHERE id = ?", (g4_alloc,))
    conn.commit()
    g4_live = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    g4_seq = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    g4 = (g4_alloc == g2_alloc_id + 1
          and g4_live == 14 and g4_seq == g4_alloc)

    conn.close()

    checks = [
        ("G0 base-state 27/14/1", g0),
        ("G1 dup-row stale-first-read", g1),
        ("G2 allocator-beside-duplicate", g2),
        ("G3 cleanup-single-honest-row", g3),
        ("G4 rearm-seq+1-keeps-high-water", g4),
    ]
    print("DM2-PRECHECK (sqlite %s)" % sqlite3.sqlite_version)
    for name, ok in checks:
        print("  %-34s %s" % (name, "PASS" if ok else "FAIL"))
    print("  pinned: alloc-id=%s post-alloc-seq-rows=%s"
          % (g2_alloc_id, g2_all))
    print("  pinned: cleanup-seq=%s rearm-id=%s"
          % (g3_seq, g4_alloc))
    verdict = "PASS" if all(ok for _, ok in checks) else "FAIL"
    print("DM2-PRECHECK VERDICT: %s" % verdict)
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
