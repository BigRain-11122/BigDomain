r"""Water journal x store live-levels consistency probe (R1806, seed:
water_journal.py R1805 cell_totals).

The five completed-window water wiring (R1794..R1800) archives one
delta row per completed window in the append-only journal, and every
delta derives from the single store face (two live pool_water_levels
snapshots around the window). From a shared empty start (journal and
store both born empty, zero preexisting rows) the telescoping sum of
the archived per-cell deltas is structurally equal to the store's
current pool levels - this probe is the end-to-end invariant check
the family never had.

Measurement face only (R1727 qa_mtime_probe precedent): not in the
SUITES registry, zero product-file writes - the probe builds its own
shared-birth world in a system temp dir, drives real flows through
all five window kinds, then cross-checks journal cell_totals against
the store's live levels cell by cell (four families: noise.total,
noise.by_reason.*, review.suspended, review.verdicted.*). A drift
injection (direct fake journal row, the R1776/R1801 tamper posture)
must be detected and named - detection is the probe's positive path,
never a silent green.

R1807 extension (month-window three-face cross): the same
shared-birth world additionally cross-checks the three
window-filtered journal read faces against each other -
cell_totals(W) cells vs the per-cell sum of journal_board(W) row
deltas, monthly_flow(W) windows vs the board row count, and
monthly_flow(W) total_delta vs the summed total_delta column vs
cell_totals(W).total - on a historical fixture month (direct
INSERT, the R1730 family precedent: fixture rows have no store
backing and stay out of the [3]/[4] journal-vs-store crosses,
which run first), the current flow month, an honest empty future
month, and a malformed window that all three faces must reject
with the shared E_WJ_BAD_WINDOW code before any read.

R1808 extension (by-kind month-window count cross): the count-only
sibling of the R1807 value cross - kind_tally(W) five-kind dense
counts vs the hand-grouped kind counts of journal_board(W) rows vs
monthly_flow(W).windows, on the same historical fixture month
(submit x1 + verdict x2), the current flow month, and an honest
empty future month. The telescoping law runs in its general form:
every observed month passes the three-face count cross and the
per-kind sum across months equals the whole-board tally (this
reduces to all-minus-historical==current in the probe's two-month
world). kind_tally joins the malformed-window reject ring so the
bad-window family check covers all four window-parameterized read
faces. Count cross only - the value cross stays in [5]; zero
product files touched (measurement face, R1727 precedent).

R1809 extension (ghost-kind observation-row negative path): the
five-kind closed set never hides an out-of-set observation row
(R1801 product-face law: dense five first, foreign keys appended
sorted). This probe injects one ghost row (kind='legacy-ghost',
direct INSERT under PRAGMA ignore_check_constraints - the R1801
tamper posture, ts derived from the current flow month so it is
wall-clock-month independent) and re-proves the three-face count
cross on it: kind_tally(W) appended key == board hand-group
appended key == flow windows count. A hidden-face demonstration
shows the cross has detection power (pre-injection tally vs
post-injection hand-group differ by exactly the ghost key - any
face that hid the row would break the cross and fail the probe,
fail-closed by construction), the malformed-window reject ring
stays intact in the tampered world, the ghost row attributes to
its own month only (historical/future windows stay clean), and
the store stays byte-identical across the injection (ghost rows
have no store backing; the [3]/[4] journal-vs-store crosses run
first and close pre-tamper - the R1807 fixture law).

Encoding discipline: this source stays pure ASCII (the emoji probe
text rides \U escapes); the output stays deterministic (no
timestamps, no temp paths) so double runs compare byte-identical.

R1810 extension (ghost-kind value-plane cross): the R1809 count
plane proved the ghost observation row stays visible in every
counting face; the value plane now proves its delta cells aggregate
into every value face. On the ghost-present world the month_cross
re-proof holds (cell_totals(cur_w) cells equal the per-cell hand
sum of board(cur_w) row deltas, ghost row included), the pre-vs-post
cell diff is exactly the ghost delta cells (a value face that hid
the ghost delta would break the diff - constructive detection
power, fail-closed), the composition law holds with the ghost +1
inside (total == noise.total + suspended, verdicted cells excluded,
R1785 law), and the flow value attribution chain binds all three
value totals equal with the ghost in (flow total_delta == net_delta
== cells total, each exactly pre + 1). The store stays
byte-identical across the value reads (ghost rows have no store
backing; the [3]/[4] crosses closed pre-tamper - the R1807/R1809
fixture law) and the read faces stay pure (row count constant).


R1811 extension (monthly net-flow value telescoping): the
value-plane sibling of the [6] count telescoping - for every
observed month the window-filtered monthly_flow(W).total_delta
sums (with the window counts) to the whole-board cell_totals
total, the whole-board monthly_flow net_delta, and the
hand-summed total_delta column of all board rows (three
derivations of one world). The observed-month set derives from
board row timestamps and cross-checks against the month column
of the whole-board flow rows. The ghost row's +1 rides inside
the telescoping sum (out-of-set kind direct query - a
month-agnostic attribution path; the [8] pre-ghost baseline
re-proves the current-month value), the historical fixture
month keeps its registered -1 net, and the honest empty future
month stays at zero: zero penetration re-proof on the
ghost-present world. Zero product files touched (measurement
face, R1727 precedent).


Usage: python water_consistency_probe.py
Exit 0 = consistent world + drift detected; 2 = any unexpected
mismatch (fail-closed).
"""

import hashlib
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile

OS_BASE = os.path.dirname(os.path.abspath(__file__))
UGCDIR = os.path.normpath(os.path.join(OS_BASE, "..", "sandbox", "ugc"))
sys.path.insert(0, UGCDIR)

import pipeline as P  # noqa: E402  (product: referenced, not copied)
import water_journal as WJ  # noqa: E402

FROZEN = ("pipeline.py", "store.py", "water_journal.py", "config.json")
EMOJI_A = "\U0001F389"  # pure-emoji probe texts (emoji_only cell)
EMOJI_B = "\U0001F38A"
EMOJI_C = "\U0001F389\U0001F38A"
SHORT = "ab!"  # emoji-stripped len 3 < min 4 (too_short cell)


def sha16(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


def load_lobby_store():
    path = os.path.normpath(os.path.join(UGCDIR, "..", "lobby", "store.py"))
    spec = importlib.util.spec_from_file_location("lobby_store_probe", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def flatten_store(levels_env):
    """Flatten the store levels envelope into journal cell-key shape
    (noise.total / noise.by_reason.<r> / review.suspended /
    review.verdicted.<v>) so both sides compare under one key space."""
    lv = levels_env["pool_water_levels"]
    flat = {"noise.total": int(lv["noise"]["total"]),
            "review.suspended": int(lv["review"]["suspended"])}
    for reason, n in lv["noise"]["by_reason"].items():
        flat["noise.by_reason." + str(reason)] = int(n)
    for verdict, n in lv["review"]["verdicted"].items():
        flat["review.verdicted." + str(verdict)] = int(n)
    return flat


def cross(journal_env, levels_env):
    """Per-cell cross: union of journal cell keys and store keys, a
    missing journal cell reads as zero (store by_reason cells stay
    sparse-observed, store dense cells never miss). Returns
    (all_match, per-cell report rows, composition_ok)."""
    jc = journal_env["cell_totals"]
    sf = flatten_store(levels_env)
    rows = []
    all_match = True
    for key in sorted(set(jc) | set(sf)):
        j_val = int(jc.get(key, 0))
        s_val = int(sf.get(key, 0))
        match = j_val == s_val
        all_match = all_match and match
        rows.append("cell %-28s journal=%-3d store=%-3d %s"
                    % (key, j_val, s_val, "OK" if match else "DRIFT"))
    comp_left = int(journal_env["total"])
    comp_right = int(jc.get("noise.total", 0)) + int(jc.get("review.suspended", 0))
    store_total = int(levels_env["total"])
    composition_ok = comp_left == comp_right == store_total
    return all_match, rows, (comp_left, comp_right, store_total), composition_ok


def hand_sum_cells(board_rows):
    """Third path (AC-JC3): per-cell hand sum over the journal_board
    row deltas - must equal the cell_totals face read."""
    cells = {}
    for row in board_rows:
        for key, value in row["delta"].items():
            cells[key] = cells.get(key, 0) + int(value)
    return cells


class OfflineGate(object):
    """Deterministic runtime-failure stub (suite precedent): every
    check raises the gate-offline family so the text degrades into
    the persistent queue - the queued receipt is a completed submit
    window with honest zero water cells."""

    def check_text(self, text):
        raise P.GateOfflineError("consistency probe offline stub")


def main():
    frozen_before = {rel: sha16(os.path.join(UGCDIR, rel))
                     for rel in FROZEN}
    tmp = tempfile.mkdtemp(prefix="wc-probe-")
    with open(os.path.join(UGCDIR, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    gw = str(cfg["gate"]["gray_words"][0])
    db = os.path.join(tmp, "ugc.db")
    journal_db = os.path.join(tmp, "water_journal.db")
    lobby = load_lobby_store()
    ls = lobby.EventStore(db)
    pipe = P.UGCPipeline(cfg, db)
    sections = []
    fail = False
    try:
        # ---- AC-JC1: shared-birth zero-start proofs ------------------
        lv0 = pipe.store.pool_water_levels()
        z_levels = (lv0["pool_water_levels"]["noise"]["total"] == 0
                    and lv0["pool_water_levels"]["noise"]["by_reason"] == {}
                    and lv0["pool_water_levels"]["review"]["suspended"] == 0
                    and lv0["pool_water_levels"]["review"]["verdicted"]
                    == {"pass": 0, "risky": 0}
                    and lv0["total"] == 0)
        board0 = pipe.journal.journal_board()
        z_board = board0["total"] == 0 and board0["journal_board"] == []
        tally0 = pipe.journal.kind_tally()
        z_tally = (tally0["kind_tally"]
                   == {"batch": 0, "drain": 0, "ingest": 0,
                       "submit": 0, "verdict": 0}
                   and tally0["total"] == 0)
        sections.append("[1] shared-birth zero-start: levels=%s board=%s "
                       "tally=%s"
                       % (z_levels, z_board, z_tally))
        fail = fail or not (z_levels and z_board and z_tally)

        # ---- AC-JC2: real-flow world across the five window kinds ---
        def idea(actor, text):
            ls.append(lobby.utc_now_iso(), "idea.submit", actor, "cocreate",
                      text, payload={"text": text,
                                     "pool": "proposal-queue-stub"})

        rec_gray = pipe.submit("avatar_intake", "A-jc1",
                               "gray submit probe " + gw)
        rec_emoji = pipe.submit("avatar_intake", "A-jc2", EMOJI_A)
        rec_short = pipe.submit("avatar_intake", "A-jc3", SHORT)
        idea("C-80001", "clean ingest probe idea")
        idea("C-80002", "gray ingest probe idea " + gw)
        idea("C-80003", EMOJI_B)
        pipe.ingest_lobby()
        batch_receipts = pipe.submit_batch(
            "avatar_intake", "A-jc4",
            ["clean batch probe text", "gray batch probe " + gw,
             EMOJI_C])
        real_gate = pipe.batch.gate
        pipe.batch.gate = OfflineGate()
        try:
            rec_queued = pipe.submit("avatar_intake", "A-jc5",
                                     "gray drain probe " + gw)
        finally:
            pipe.batch.gate = real_gate
        drain_receipt = pipe.drain_recover()
        rec_batch_gray = next(r for r in batch_receipts
                             if isinstance(r, dict) and r.get("suspended"))
        pipe.review_verdict(rec_gray["evt_id"], "pass")
        try:
            pipe.review_verdict(rec_batch_gray["evt_id"], "risky")
        except P.UGC.PipelineError as exc:
            if exc.code != P.UGC.E_CONTENT_REJECTED:
                raise
        tally = pipe.journal.kind_tally()
        kinds_ok = all(tally["kind_tally"][k] >= 1
                       for k in ("ingest", "batch", "drain", "submit", "verdict"))
        queued_ok = isinstance(rec_queued, dict) and rec_queued.get("queued") is True
        sections.append("[2] world account: kind_tally=%s five-kinds>=1=%s "
                       "degraded-queued=%s drain=%s"
                       % (json.dumps(tally["kind_tally"], sort_keys=True),
                          kinds_ok, queued_ok,
                          json.dumps({k: drain_receipt[k]
                                      for k in sorted(drain_receipt)
                                      if k in ("drained", "passed", "rejected",
                                               "recovered")},
                                     sort_keys=True)))
        fail = fail or not (kinds_ok and queued_ok)

        # ---- AC-JC3: end-to-end invariant cross (core) ---------------
        journal_env = pipe.journal.cell_totals()
        levels_env = pipe.store.pool_water_levels()
        all_match, rows, comp, composition_ok = cross(journal_env, levels_env)
        hand = hand_sum_cells(pipe.journal.journal_board()["journal_board"])
        hand_ok = all(int(hand.get(k, 0)) == int(v)
                      for k, v in journal_env["cell_totals"].items()) \
            and set(hand) == set(journal_env["cell_totals"])
        sections.append("[3] journal-vs-store cross:")
        sections.extend("    " + r for r in rows)
        sections.append("    composition journal_total=%d noise+susp=%d "
                       "store_total=%d %s"
                       % (comp[0], comp[1], comp[2],
                          "OK" if composition_ok else "DRIFT"))
        sections.append("    third-path hand-sum=%s"
                       % ("OK" if hand_ok else "DRIFT"))
        fail = fail or not (all_match and composition_ok and hand_ok)

        # ---- AC-JC4: drift injection negative path -------------------
        conn = sqlite3.connect(journal_db)
        conn.execute(
            "INSERT INTO water_windows (kind, delta, total_delta, ts_utc) "
            "VALUES ('submit', ?, 5, '2026-10-11T00:00:00.000000Z')",
            (json.dumps({"noise.total": 5}, sort_keys=True),))
        conn.commit()
        conn.close()
        drift_env = pipe.journal.cell_totals()
        drift_match, drift_rows, drift_comp, drift_comp_ok = cross(
            drift_env, levels_env)
        named = [r for r in drift_rows if "DRIFT" in r]
        drift_named = any("noise.total" in r for r in named)
        sections.append("[4] drift injection: rows=%d named=%d "
                       "noise.total-named=%s verdict=DRIFT-DETECTED"
                       % (len(named), len(named), drift_named))
        sections.extend("    " + r for r in named)
        sections.append("    drift composition journal_total=%d "
                       "noise+susp=%d store_total=%d %s"
                       % (drift_comp[0], drift_comp[1], drift_comp[2],
                          "OK" if drift_comp_ok else "DRIFT"))
        fail = fail or not (not drift_match and drift_named)

        # ---- [5] month-window three-face cross (R1807) ---------------
        conn = sqlite3.connect(journal_db)
        for kind, delta, total, ts in (
                ("submit", {"noise.total": 1,
                            "noise.by_reason.too_short": 1}, 1,
                 "2026-08-05T00:00:00.000000Z"),
                ("verdict", {"review.suspended": -1,
                             "review.verdicted.pass": 1}, -1,
                 "2026-08-20T00:00:00.000000Z"),
                ("verdict", {"review.suspended": -1,
                             "review.verdicted.risky": 1}, -1,
                 "2026-08-28T00:00:00.000000Z")):
            conn.execute(
                "INSERT INTO water_windows (kind, delta, total_delta,"
                " ts_utc) VALUES (?, ?, ?, ?)",
                (kind, json.dumps(delta, sort_keys=True), total, ts))
        conn.commit()
        c1 = conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        conn.close()

        def month_cross(w):
            cells_env = pipe.journal.cell_totals(w)
            board_env = pipe.journal.journal_board(w)
            flow_env = pipe.journal.monthly_flow(w)
            hand = hand_sum_cells(board_env["journal_board"])
            n_rows = len(board_env["journal_board"])
            cells_ok = (cells_env["cell_totals"] == hand
                        and board_env["total"] == n_rows)
            flow_rows = flow_env["monthly_flow"]
            if n_rows:
                row_sum = sum(r["total_delta"]
                              for r in board_env["journal_board"])
                flow_ok = (len(flow_rows) == 1
                           and flow_rows[0]["month"] == w
                           and flow_rows[0]["windows"] == n_rows
                           and flow_env["total"] == n_rows
                           and flow_env["net_delta"]
                           == flow_rows[0]["total_delta"])
                sums_ok = (flow_rows[0]["total_delta"] == row_sum
                           == cells_env["total"])
            else:
                flow_ok = (flow_rows == [] and flow_env["total"] == 0
                           and flow_env["net_delta"] == 0)
                sums_ok = cells_env["total"] == 0
            return (cells_ok and flow_ok and sums_ok,
                    cells_env["cell_totals"], n_rows, cells_env["total"])

        hist_ok, hist_cells, hist_n, hist_total = month_cross("2026-08")
        tail = pipe.journal.journal_board()["journal_board"][-1]
        cur_w = tail["ts_utc"][:7]
        cur_ok, cur_cells, cur_n, cur_total = month_cross(cur_w)
        fut_ok, fut_cells, fut_n, fut_total = month_cross("2026-12")
        bad = "2026-10\n"
        rejects = []
        for face in (pipe.journal.cell_totals,
                     pipe.journal.journal_board,
                     pipe.journal.monthly_flow):
            try:
                face(window=bad)
                rejects.append("NO-RAISE")
            except ValueError as exc:
                rejects.append("E_WJ_BAD_WINDOW"
                               if "E_WJ_BAD_WINDOW" in str(exc)
                               else "OTHER")
        conn = sqlite3.connect(journal_db)
        c2 = conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        conn.close()
        rejects_ok = (rejects == ["E_WJ_BAD_WINDOW"] * 3 and c1 == c2)
        sections.append("[5] month-window three-face cross:")
        sections.append("    hist 2026-08: rows=%d total=%d cells=%s %s"
                        % (hist_n, hist_total,
                           json.dumps(hist_cells, sort_keys=True),
                           "OK" if hist_ok else "DRIFT"))
        sections.append("    cur %s: rows=%d total=%d cells=%s %s"
                        % (cur_w, cur_n, cur_total,
                           json.dumps(cur_cells, sort_keys=True),
                           "OK" if cur_ok else "DRIFT"))
        sections.append("    fut 2026-12: rows=%d total=%d %s"
                        % (fut_n, fut_total,
                           "OK" if fut_ok else "DRIFT"))
        sections.append("    bad-window passthrough: %s rows %d==%d %s"
                        % (",".join(rejects), c1, c2,
                           "OK" if rejects_ok else "DRIFT"))
        fail = fail or not (hist_ok and cur_ok and fut_ok and rejects_ok)

        # ---- [6] by-kind month-window count cross (R1808) -----------
        def hand_group_kinds(rows):
            grouped = {}
            for row in rows:
                grouped[row["kind"]] = grouped.get(row["kind"], 0) + 1
            dense = {}
            rest = dict(grouped)
            for kind in sorted(WJ.KINDS):
                dense[kind] = int(rest.pop(kind, 0))
            for kind in sorted(rest):
                dense[kind] = rest[kind]
            return dense

        def kind_count_cross(w, dense_expect=None):
            tally_env = pipe.journal.kind_tally(w)
            board_env = pipe.journal.journal_board(w)
            flow_env = pipe.journal.monthly_flow(w)
            dense = hand_group_kinds(board_env["journal_board"])
            tally = dict(tally_env["kind_tally"])
            keys_ok = set(tally) == set(dense)
            counts_ok = tally == dense
            n_rows = len(board_env["journal_board"])
            flow_rows = flow_env["monthly_flow"]
            if n_rows:
                flow_ok = (len(flow_rows) == 1
                           and flow_rows[0]["month"] == w
                           and flow_rows[0]["windows"] == n_rows
                           and flow_env["total"] == n_rows)
                sum_ok = (flow_rows[0]["windows"] == sum(tally.values())
                          == tally_env["total"])
            else:
                flow_ok = (flow_rows == [] and flow_env["total"] == 0
                           and flow_env["net_delta"] == 0)
                sum_ok = sum(tally.values()) == 0 == tally_env["total"]
            expect_ok = True
            if dense_expect is not None:
                expect_ok = tally == dense_expect
            return (keys_ok and counts_ok and flow_ok and sum_ok
                    and expect_ok), tally, n_rows

        hist_ok, hist_tally, hist_rows = kind_count_cross(
            "2026-08",
            dense_expect={"batch": 0, "drain": 0, "ingest": 0,
                          "submit": 1, "verdict": 2})
        months = [r["month"] for r in
                  pipe.journal.monthly_flow()["monthly_flow"]]
        tele_ok = True
        per_kind_sum = {}
        for month in months:
            m_ok, m_tally, _ = kind_count_cross(month)
            tele_ok = tele_ok and m_ok
            for kind, n in m_tally.items():
                per_kind_sum[kind] = per_kind_sum.get(kind, 0) + int(n)
        all_tally = dict(pipe.journal.kind_tally()["kind_tally"])
        tele_ok = tele_ok and per_kind_sum == all_tally
        cur_ok, cur_tally, cur_rows = kind_count_cross(cur_w)
        fut_ok, fut_tally, fut_rows = kind_count_cross("2026-12")
        conn = sqlite3.connect(journal_db)
        rows_bk_before = conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        conn.close()
        try:
            pipe.journal.kind_tally(window=bad)
            bk_reject = "NO-RAISE"
        except ValueError as exc:
            bk_reject = ("E_WJ_BAD_WINDOW"
                         if "E_WJ_BAD_WINDOW" in str(exc) else "OTHER")
        conn = sqlite3.connect(journal_db)
        rows_bk_after = conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        conn.close()
        bk_ok = (bk_reject == "E_WJ_BAD_WINDOW"
                 and rows_bk_before == rows_bk_after)
        sections.append("[6] by-kind month-window count cross:")
        sections.append("    hist 2026-08: rows=%d tally=%s %s"
                        % (hist_rows,
                           json.dumps(hist_tally, sort_keys=True),
                           "OK" if hist_ok else "DRIFT"))
        sections.append("    months=%s telescoping(sum==all)=%s %s"
                        % (",".join(months),
                           json.dumps(all_tally, sort_keys=True),
                           "OK" if tele_ok else "DRIFT"))
        sections.append("    cur %s: rows=%d tally=%s %s"
                        % (cur_w, cur_rows,
                           json.dumps(cur_tally, sort_keys=True),
                           "OK" if cur_ok else "DRIFT"))
        sections.append("    fut 2026-12: rows=%d tally=%s %s"
                        % (fut_rows,
                           json.dumps(fut_tally, sort_keys=True),
                           "OK" if fut_ok else "DRIFT"))
        sections.append("    bad-window kind_tally: %s rows %d==%d %s"
                        % (bk_reject, rows_bk_before, rows_bk_after,
                           "OK" if bk_ok else "DRIFT"))
        fail = fail or not (hist_ok and tele_ok and cur_ok and fut_ok
                            and bk_ok)

        # ---- [7] ghost-kind cross (R1809) ----------------------------
        # Out-of-set observation row (R1801 product-face tamper law):
        # every counting face must keep it visible. Store snapshot and
        # pre-injection faces are captured first (zero store backing;
        # the [3]/[4] crosses already closed on the pre-tamper world).
        store_pre = json.dumps(pipe.store.pool_water_levels(),
                               sort_keys=True)
        pre_tally = dict(pipe.journal.kind_tally(cur_w)["kind_tally"])
        pre_cells_env = pipe.journal.cell_totals(cur_w)
        pre_cells = dict(pre_cells_env["cell_totals"])
        pre_flow_env = pipe.journal.monthly_flow(cur_w)
        pre_flow = pre_flow_env["monthly_flow"]
        ghost_absent = "legacy-ghost" not in pre_tally
        conn = sqlite3.connect(journal_db)
        conn.execute("PRAGMA ignore_check_constraints = ON")
        conn.execute(
            "INSERT INTO water_windows (kind, delta, total_delta, ts_utc) "
            "VALUES ('legacy-ghost', ?, 1, ?)",
            (json.dumps({"noise.total": 1}, sort_keys=True),
             cur_w + "-11T00:00:00.000000Z"))
        conn.commit()
        conn.execute("PRAGMA ignore_check_constraints = OFF")
        ghost_rows = conn.execute(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE kind = 'legacy-ghost'").fetchone()[0]
        conn.close()
        gk_ok, gk_tally, gk_rows = kind_count_cross(cur_w)
        key_order_ok = list(gk_tally) == sorted(WJ.KINDS) + ["legacy-ghost"]
        gk1_ok = (ghost_absent and ghost_rows == 1 and gk_ok
                  and key_order_ok and gk_tally.get("legacy-ghost") == 1)

        # hidden-face detection power: pre vs post differ by exactly
        # the ghost key - a face that hid the row breaks the cross.
        diff_keys = set(gk_tally) ^ set(pre_tally)
        diff_only_ghost = (diff_keys == {"legacy-ghost"}
                           and all(int(gk_tally[k]) == int(v)
                                   for k, v in pre_tally.items()))
        conn = sqlite3.connect(journal_db)
        rows_g1 = conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        conn.close()
        try:
            pipe.journal.kind_tally(window=bad)
            gk_reject = "NO-RAISE"
        except ValueError as exc:
            gk_reject = ("E_WJ_BAD_WINDOW"
                         if "E_WJ_BAD_WINDOW" in str(exc) else "OTHER")
        conn = sqlite3.connect(journal_db)
        rows_g2 = conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        conn.close()
        gk2_ok = (diff_only_ghost and gk_reject == "E_WJ_BAD_WINDOW"
                  and rows_g1 == rows_g2)

        # month attribution: ghost lands in its own month only.
        hist_tally2 = dict(pipe.journal.kind_tally("2026-08")
                           ["kind_tally"])
        hist_clean = (hist_tally2 == {"batch": 0, "drain": 0, "ingest": 0,
                                      "submit": 1, "verdict": 2})
        fut_ok2, fut_tally2, fut_rows2 = kind_count_cross("2026-12")
        fut_clean = (fut_ok2 and sum(fut_tally2.values()) == 0
                     and "legacy-ghost" not in fut_tally2)
        post_flow_env = pipe.journal.monthly_flow(cur_w)
        post_flow = post_flow_env["monthly_flow"]
        attr_ok = (len(pre_flow) == 1 and len(post_flow) == 1
                   and post_flow[0]["month"] == pre_flow[0]["month"] == cur_w
                   and post_flow[0]["windows"]
                   == pre_flow[0]["windows"] + 1
                   and post_flow[0]["total_delta"]
                   == pre_flow[0]["total_delta"] + 1
                   and post_flow_env["net_delta"]
                   == pre_flow_env["net_delta"] + 1)
        gk3_ok = hist_clean and fut_clean and attr_ok

        # zero store background: injection touched the journal only.
        store_post = json.dumps(pipe.store.pool_water_levels(),
                                sort_keys=True)
        gk4_ok = store_pre == store_post
        sections.append("[7] ghost-kind cross:")
        sections.append("    injected=%d absent-pre=%s tally=%s %s"
                        % (ghost_rows, ghost_absent,
                           json.dumps(gk_tally, sort_keys=False),
                           "OK" if gk1_ok else "DRIFT"))
        sections.append("    hidden-face detection: diff-keys=%s "
                       "other-cells-equal=%s %s"
                        % (",".join(sorted(diff_keys)) or "(none)",
                           diff_only_ghost,
                           "OK" if diff_only_ghost else "DRIFT"))
        sections.append("    bad-window with ghost: %s rows %d==%d %s"
                        % (gk_reject, rows_g1, rows_g2,
                           "OK" if (gk_reject == "E_WJ_BAD_WINDOW"
                                    and rows_g1 == rows_g2) else "DRIFT"))
        sections.append("    month attribution: hist-2026-08-clean=%s "
                       "fut-2026-12-zero=%s flow %s windows=%d->%d "
                       "total_delta=%d->%d net_delta=%d->%d %s"
                        % (hist_clean, fut_clean, cur_w,
                           pre_flow[0]["windows"], post_flow[0]["windows"],
                           pre_flow[0]["total_delta"],
                           post_flow[0]["total_delta"],
                           pre_flow_env["net_delta"],
                           post_flow_env["net_delta"],
                           "OK" if gk3_ok else "DRIFT"))
        sections.append("    store zero-background: identical=%s "
                       "([3]/[4] closed pre-tamper)"
                        % gk4_ok)
        fail = fail or not (gk1_ok and gk2_ok and gk3_ok and gk4_ok)

        # ---- [8] ghost value-plane cross (R1810) ----------------------
        # The count plane (R1809) proved the ghost row stays visible
        # in every counting face; the value plane now proves its delta
        # cells aggregate into every value face: the month_cross
        # re-proof on the ghost-present world, the composition law
        # with the ghost +1 inside, and the flow value attribution
        # chain - all three value totals equal with the ghost in. A
        # value face that hid the ghost delta would break the
        # pre/post cell diff (exactly the ghost delta cells) - the
        # constructive detection proof, fail-closed by construction.
        conn = sqlite3.connect(journal_db)
        rows_v1 = conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        conn.close()
        post_cells_env = pipe.journal.cell_totals(cur_w)
        post_cells = dict(post_cells_env["cell_totals"])
        gv_month_ok, gv_cells, gv_n, gv_total = month_cross(cur_w)
        cells_ghost_vis = (int(post_cells.get("noise.total", 0))
                          == int(pre_cells.get("noise.total", 0)) + 1)
        diff_cells = {}
        for key in sorted(set(post_cells) | set(pre_cells)):
            delta = int(post_cells.get(key, 0)) - int(pre_cells.get(key, 0))
            if delta:
                diff_cells[key] = delta
        diff_only_ghost_delta = diff_cells == {"noise.total": 1}
        gv1_ok = (gv_month_ok and cells_ghost_vis and diff_only_ghost_delta)

        comp_total = int(post_cells_env["total"])
        comp_rhs = (int(post_cells.get("noise.total", 0))
                    + int(post_cells.get("review.suspended", 0)))
        gv2_ok = (comp_total == comp_rhs
                  and comp_total == int(pre_cells_env["total"]) + 1)

        flow_env_v = pipe.journal.monthly_flow(cur_w)
        flow_rows_v = flow_env_v["monthly_flow"]
        pre_flow_total = int(pre_flow_env["monthly_flow"][0]["total_delta"])
        pre_flow_net = int(pre_flow_env["net_delta"])
        gv3_ok = (len(flow_rows_v) == 1
                  and flow_rows_v[0]["total_delta"] == comp_total
                  == flow_env_v["net_delta"]
                  and flow_rows_v[0]["total_delta"] == pre_flow_total + 1
                  and flow_env_v["net_delta"] == pre_flow_net + 1)

        store_post_v = json.dumps(pipe.store.pool_water_levels(),
                                  sort_keys=True)
        conn = sqlite3.connect(journal_db)
        rows_v2 = conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        conn.close()
        gv4_ok = (store_post_v == store_pre and rows_v1 == rows_v2)
        sections.append("[8] ghost value-plane cross:")
        sections.append("    month-cross-reproof %s: rows=%d total=%d %s"
                        % (cur_w, gv_n, gv_total,
                           "OK" if gv_month_ok else "DRIFT"))
        sections.append("    ghost-cell visibility: noise.total %d->%d "
                       "diff=%s %s"
                        % (int(pre_cells.get("noise.total", 0)),
                           int(post_cells.get("noise.total", 0)),
                           json.dumps(diff_cells, sort_keys=True),
                           "OK" if (cells_ghost_vis
                                    and diff_only_ghost_delta) else "DRIFT"))
        sections.append("    composition-with-ghost: total=%d "
                       "noise.total+susp=%d pre+1=%d %s"
                        % (comp_total, comp_rhs,
                           int(pre_cells_env["total"]) + 1,
                           "OK" if gv2_ok else "DRIFT"))
        sections.append("    flow value attribution: total_delta=%d "
                       "net_delta=%d (pre %d/%d) %s"
                        % (flow_rows_v[0]["total_delta"],
                           flow_env_v["net_delta"], pre_flow_total,
                           pre_flow_net,
                           "OK" if gv3_ok else "DRIFT"))
        sections.append("    store zero-background+pure-read: "
                       "identical=%s rows %d==%d %s"
                        % (store_post_v == store_pre, rows_v1, rows_v2,
                           "OK" if gv4_ok else "DRIFT"))
        fail = fail or not (gv1_ok and gv2_ok and gv3_ok and gv4_ok)

        # ---- [9] monthly net-flow value telescoping (R1811) --------
        # The count plane ([6]) proved per-month by-kind sums equal
        # the whole-board tally; the value plane proves the per-month
        # net-flow telescoping: each observed month's window-filtered
        # monthly_flow(W).total_delta, summed across months, equals
        # the whole-board cell_totals total, the whole-board
        # monthly_flow net_delta, and the hand-summed total_delta
        # column of all board rows (three derivations of one world).
        # The ghost row's +1 rides inside the sum (month-agnostic
        # attribution via the out-of-set kind direct query), the
        # historical fixture month keeps its registered -1 net, and
        # the honest empty future month stays at zero.
        board_full = pipe.journal.journal_board()["journal_board"]
        months_board = sorted({r["ts_utc"][:7] for r in board_full})
        flow_full_env = pipe.journal.monthly_flow()
        flow_full_rows = flow_full_env["monthly_flow"]
        months_flow = [r["month"] for r in flow_full_rows]
        months_ok = months_board == months_flow
        per_month = []
        sum_flow = 0
        sum_windows = 0
        months_read_ok = True
        for month in months_board:
            m_env = pipe.journal.monthly_flow(month)
            m_rows = m_env["monthly_flow"]
            ok_m = (len(m_rows) == 1 and m_rows[0]["month"] == month
                    and int(m_env["total"]) == int(m_rows[0]["windows"])
                    and int(m_env["net_delta"])
                    == int(m_rows[0]["total_delta"]))
            months_read_ok = months_read_ok and ok_m
            per_month.append("%s:%+d/%dw"
                            % (month, int(m_rows[0]["total_delta"]),
                               int(m_rows[0]["windows"])))
            sum_flow += int(m_rows[0]["total_delta"])
            sum_windows += int(m_rows[0]["windows"])
        cells_full_env = pipe.journal.cell_totals()
        cells_full_total = int(cells_full_env["total"])
        flow_net = int(flow_full_env["net_delta"])
        hand_col = sum(int(r["total_delta"]) for r in board_full)
        tl2_ok = (months_read_ok
                  and sum_flow == cells_full_total == flow_net == hand_col
                  and sum_windows == len(board_full)
                  and sum(int(r["windows"]) for r in flow_full_rows)
                  == len(board_full))
        ghost_col = sum(int(r["total_delta"]) for r in board_full
                        if r["kind"] == "legacy-ghost")
        non_ghost_col = sum(int(r["total_delta"]) for r in board_full
                            if r["kind"] != "legacy-ghost")
        cur_flow_env_t = pipe.journal.monthly_flow(cur_w)
        cur_flow_rows_t = cur_flow_env_t["monthly_flow"]
        cur_ride = (len(cur_flow_rows_t) == 1
                    and int(cur_flow_rows_t[0]["total_delta"])
                    == int(pre_cells_env["total"]) + 1)
        ghost_ride = (ghost_col == 1
                      and sum_flow == non_ghost_col + ghost_col
                      and cur_ride)
        hflow_env = pipe.journal.monthly_flow("2026-08")
        hflow_rows = hflow_env["monthly_flow"]
        hflow_ok = (len(hflow_rows) == 1
                    and int(hflow_rows[0]["windows"]) == 3
                    and int(hflow_rows[0]["total_delta"]) == -1)
        hcells_total = int(pipe.journal.cell_totals("2026-08")["total"])
        fflow_env = pipe.journal.monthly_flow("2026-12")
        fcells_env = pipe.journal.cell_totals("2026-12")
        fut_zero = (fflow_env["monthly_flow"] == []
                    and int(fflow_env["total"]) == 0
                    and int(fflow_env["net_delta"]) == 0
                    and fcells_env["cell_totals"] == {}
                    and int(fcells_env["total"]) == 0)
        fut_absent = "2026-12" not in months_board
        tl3_ok = (ghost_ride and hflow_ok and hcells_total == -1
                  and fut_zero and fut_absent)
        sections.append("[9] monthly net-flow value telescoping:")
        sections.append("    months=%s (board==flow sets %s)"
                        % (",".join(months_board), months_ok))
        sections.append("    per-month flow: %s" % " ".join(per_month))
        sections.append("    telescoping: sum=%+d cells=%d flow-net=%d "
                        "hand-col=%d windows %d==%d %s"
                        % (sum_flow, cells_full_total, flow_net, hand_col,
                           sum_windows, len(board_full),
                           "OK" if (months_ok and tl2_ok) else "DRIFT"))
        sections.append("    ghost ride: ghost-col=%+d non-ghost=%+d "
                        "cur %s=%+d==pre %+d +1 %s"
                        % (ghost_col, non_ghost_col, cur_w,
                           int(cur_flow_rows_t[0]["total_delta"]),
                           int(pre_cells_env["total"]),
                           "OK" if ghost_ride else "DRIFT"))
        sections.append("    zero penetration: hist-2026-08=%+d cells=%+d "
                        "fut-2026-12 zero=%s absent=%s %s"
                        % (int(hflow_rows[0]["total_delta"]), hcells_total,
                           fut_zero, fut_absent,
                           "OK" if tl3_ok else "DRIFT"))
        fail = fail or not (months_ok and tl2_ok and tl3_ok)

        # ---- AC-JC5: hygiene -----------------------------------------
        with open(os.path.abspath(__file__), "rb") as handle:
            self_bytes = handle.read()
        ascii_ok = max(self_bytes) < 128
        net_ok = True
        with open(os.path.abspath(__file__), encoding="utf-8") as handle:
            for line in handle:
                s = line.strip()
                if s.startswith("import ") or s.startswith("from "):
                    if any(w in s for w in ("urllib", "requests",
                                            "socket", "http")):
                        net_ok = False
        frozen_after = {rel: sha16(os.path.join(UGCDIR, rel))
                        for rel in FROZEN}
        frozen_ok = frozen_before == frozen_after
        sections.append("[10] hygiene: probe-ascii=%s import-lines-clean=%s "
                       "frozen=%s (%s)"
                       % (ascii_ok, net_ok, frozen_ok,
                          " ".join("%s:%s" % (rel, sha)
                                   for rel, sha in sorted(
                                       frozen_after.items()))))
        fail = fail or not (ascii_ok and net_ok and frozen_ok)
    finally:
        pipe.close()
        ls.close()

    verdict = "CONSISTENT+DETECTING" if not fail else "PROBE-FAIL"
    print("\n".join(sections))
    print("PROBE VERDICT: %s" % verdict)
    return 0 if not fail else 2


if __name__ == "__main__":
    sys.exit(main())
