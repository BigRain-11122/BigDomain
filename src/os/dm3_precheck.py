r"""dm3_precheck - engine-semantics empirical pin for the R1846
sqlite_sequence VACUUM scan-order stability probe section.

dm2_precheck (R1844) pinned the duplicate-row world WITHOUT
VACUUM: beside a duplicate the allocator consults the FIRST row
(allocates 27+1 == 28, the 99 sentinel never surfaces) and its
post-alloc UPDATE touches only that first row; cleanup wipes all
bookkeeping rows and restores one honest row at the consumed
high-water.

This precheck adds the VACUUM plane (R1846): VACUUM rebuilds the
database file, and whether the duplicate sqlite_sequence rows
SURVIVE the rebuild, whether the FIRST-ROW scan order (the plain
fetchone the allocator consults) CHANGES across the rebuild, and
whether the allocator behavior DRIFTS are engine facts to be
read here, not assumed (R1704 law - dm_precheck R1838 /
hw_precheck R1823 / tp_precheck R1832 / dm2_precheck R1844
precedents).

G0  Base state mirrors the probe [23] end state: ids 1..14
    live, ids 15..28 consumed then deleted, one honest
    bookkeeping row at high-water 28. A second connection idles
    open the whole time (the probe world keeps a live pipeline
    / journal connection) - VACUUM must succeed beside it.
G1  Inject the duplicate (99 sentinel), take the pre-VACUUM
    readings (COUNT / plain fetchone / fetchall), then VACUUM:
    duplicate-row SURVIVAL (COUNT == 2 post) and the post-VACUUM
    first-row read are pinned pre-vs-post - scan-order stability
    is the fact being pinned; a flip is a legal finding.
G2  Allocator retest after VACUUM with the duplicate present:
    the next INSERT's allocated id and both rows' post-alloc seq
    values are pinned (which row the allocator consults
    post-rebuild; whether the post-alloc UPDATE touches one or
    both rows).
G3  Cleanup recovery + re-arm: delete the allocated row, wipe
    ALL bookkeeping rows for the name, re-insert one honest row
    at the pinned allocated id (consume-no-retreat law), then the
    next INSERT allocates honest-seq+1 and the delete keeps the
    advanced high-water.

Pure stdlib, pure ASCII, temp-dir only, zero repo writes.
"""

import os
import sqlite3
import tempfile


def main():
    workdir = tempfile.mkdtemp(prefix="dm3_precheck_")
    db = os.path.join(workdir, "dm3.db")
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE t (id INTEGER PRIMARY KEY"
        " AUTOINCREMENT, v TEXT)")
    # assign ids 1..28 in operation order, consume 15..28
    # (probe [23] end state: live 1..14, high-water 28)
    for i in range(1, 29):
        conn.execute("INSERT INTO t (v) VALUES (?)", ("x%d" % i,))
    for i in range(15, 29):
        conn.execute("DELETE FROM t WHERE id = ?", (i,))
    conn.commit()

    # idle second connection kept open for the whole precheck -
    # the probe world keeps a live journal connection open
    idle = sqlite3.connect(db)
    idle.execute("SELECT COUNT(*) FROM t").fetchone()

    # G0: base state matches the probe [23] end state and VACUUM
    # succeeds beside the idle open connection
    g0_seq = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    g0_live = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    g0_rows = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    vacuum_ok = True
    try:
        conn.execute("VACUUM")
        conn.commit()
    except sqlite3.Error:
        vacuum_ok = False
    g0 = (g0_seq == 28 and g0_live == 14 and g0_rows == 1
          and vacuum_ok)

    # G1: construct the duplicate (99 sentinel), pin pre-VACUUM
    # readings, VACUUM, pin post-VACUUM readings - survival and
    # first-row scan order across the rebuild
    conn.execute(
        "INSERT INTO sqlite_sequence (name, seq)"
        " VALUES ('t', 99)")
    conn.commit()
    g1_rows_pre = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    g1_first_pre = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    g1_all_pre = [r[0] for r in conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
        " ORDER BY seq")]
    conn.execute("VACUUM")
    conn.commit()
    g1_rows_post = conn.execute(
        "SELECT COUNT(*) FROM sqlite_sequence"
        " WHERE name = 't'").fetchone()[0]
    g1_first_post = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
    ).fetchone()[0]
    g1_all_post = [r[0] for r in conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
        " ORDER BY seq")]
    g1 = (g1_rows_pre == 2 and g1_first_pre == 28
          and g1_all_pre == [28, 99]
          and g1_rows_post == 2
          and g1_all_post == [28, 99])
    # scan-order stability verdict is a pinned reading, not an
    # assumption: g1_order_stable records whether the plain
    # first-row read survived the rebuild unchanged
    g1_order_stable = (g1_first_post == g1_first_pre)

    # G2: allocator retest after VACUUM with the duplicate
    # present - allocated id and both rows' post-alloc seq
    # values are engine facts pinned here
    conn.execute("INSERT INTO t (v) VALUES ('vac-alloc')")
    g2_alloc_id = conn.execute(
        "SELECT last_insert_rowid()").fetchone()[0]
    g2_live = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    g2_all = [r[0] for r in conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 't'"
        " ORDER BY seq")]
    conn.commit()
    g2 = (isinstance(g2_alloc_id, int) and g2_live == 15
          and len(g2_all) >= 1)

    # G3: cleanup recovery - delete the allocated row, wipe ALL
    # bookkeeping rows for the name, one honest row back at the
    # pinned allocated id (consume-no-retreat), then re-arm
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
    g3 = (g3_live == 14 and g3_zero == 0 and g3_rows == 1
          and g3_seq == g2_alloc_id)
    g4 = (g4_alloc == g2_alloc_id + 1
          and g4_live == 14 and g4_seq == g4_alloc)

    idle.close()
    conn.close()

    checks = [
        ("G0 base-state-28/14/1+vacuum-ok", g0),
        ("G1 dup-survives-vacuum", g1),
        ("G2 allocator-post-vacuum", g2),
        ("G3 cleanup-single-honest-row", g3),
        ("G4 rearm-seq+1-keeps-high-water", g4),
    ]
    print("DM3-PRECHECK (sqlite %s)" % sqlite3.sqlite_version)
    for name, ok in checks:
        print("  %-34s %s" % (name, "PASS" if ok else "FAIL"))
    print("  pinned: pre-vacuum first=%s all=%s"
          % (g1_first_pre, g1_all_pre))
    print("  pinned: post-vacuum first=%s all=%s order-stable=%s"
          % (g1_first_post, g1_all_post, g1_order_stable))
    print("  pinned: post-vacuum-alloc-id=%s"
          " post-alloc-seq-rows=%s" % (g2_alloc_id, g2_all))
    print("  pinned: cleanup-seq=%s rearm-id=%s"
          % (g3_seq, g4_alloc))
    verdict = "PASS" if all(ok for _, ok in checks) else "FAIL"
    print("DM3-PRECHECK VERDICT: %s" % verdict)
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
