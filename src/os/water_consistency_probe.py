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


R1812 extension (board read-cap x month-window orthogonal
combination): the R1804 product face journal_board(window,
limit) has had both parameters proven separately (the window
filter cross in [5], the read-cap law in the R1804 suite) but
the orthogonal combination is unmeasured in the probe world.
On the ghost-present world: the current-month window x limit=3
tail truncation equals the tail-3 subsequence of that window's
full row list position by position (mirror-SQL law), the
envelope adds exactly the three keys {limit, returned,
truncated} (additive over the no-limit envelope), total reports
the full in-window count (never the truncated one - a
truncated board never lies about its size, and the ghost+drift
rows stay inside that count), the cap semantics cover all
three states (truncating 3 < window count / loose 99 >= window
count with the loose row set carrying the ghost row - a loose
read never hides the tamper row / honest empty future month),
the bad-limit reject ring stays unweakened in the tampered
world (four malformed shapes plus the both-bad gate order:
E_WJ_BAD_LIMIT fires before the window gate; the bad-window
ring fires through a good limit), and the reads stay pure
(store snapshot byte-identical, row count constant). Zero
product files touched (measurement face, R1727 precedent).


R1813 extension (drift-row wall-clock-month abstraction): the [4]
drift row used a hardcoded ts, which was the probe world's only
live-month coupling (R1806 onwards) - run in any month other than
2026-10 the row fell into a foreign month and broke the [10]
n_cur==11 structural constant (a month coupling that R1812 had
just introduced). The ts now derives from the pre-injection board
tail row month (the R1809 ghost-row method), so the drift row
always rides the real flow month and the count readings become
month-independent structural constants. The abstracted ts ties
the ghost ts (same month, same -11T00:00:00.000000Z clock), so the
board order falls to the window_id tiebreak: drift (injected in
[4]) before ghost (injected in [7]) - the prior order carried
forward, asserted in [10]. Known family boundary, not extended
here: a run inside calendar 2026-12 turns the "future window"
into the current month (the R1807/R1808/R1811 fut-2026-12 honest
empty reads then exercise the current-month path instead). Zero
product files touched (measurement face, R1727 precedent).


R1814 extension (mirror-SQL third path for capped reads): the
[10] tail-truncation face compared two paths over the product
connection (the cap read vs the full-read tail subsequence). This
section adds the independent third path: a raw read-only SQL
connection (file URI mode=ro) running the product's mirror
clause verbatim - window predicate first, then ORDER BY ts_utc
DESC, window_id DESC LIMIT N, reversed back to board order. The
global cap, the month-window combination and the loose cap each
equal their product reads position by position (five fields);
the SQL in-window COUNT equals the envelope total law (n_cur);
the ghost and drift tamper rows stay visible on the raw path (a
third path that never hides them); the honest-empty future month
reads zero rows and the historical fixture stays visible (count
3, capped read positional). The read-only connection rejects a
write attempt at the connection level (behavioral proof, zero
mutation: the row count stays 14). The global-cap == window-cap
equality rides on the world shape (the historical fixture month
always precedes the flow month; the fut-2026-12 family boundary
note applies unchanged). Zero product files touched (measurement
face, R1727 precedent).


R1815 extension (aggregate mirror-SQL third path): the [6]/[9]
sections proved the product aggregation faces (kind_tally,
monthly_flow) against hand-grouped / hand-summed derivations;
this section adds the independent third path for the two
aggregation faces - a fresh read-only SQL connection (file URI
mode=ro, the [11] law) running the window-predicate GROUP BY
aggregates: kind_tally(W) dense dict vs "GROUP BY kind COUNT(*)"
and monthly_flow(W) row vs "GROUP BY substr(ts_utc,1,7)
COUNT(*)/SUM(total_delta)", on every observed month. The
whole-board month set rides the same law without the WHERE
clause (per-month rows month-ascending, all keys positional);
the historical fixture month keeps its count-3 reading and the
honest-empty future month reads zero rows (no leak, no
penetration). The connection opens fresh (the [11] connection
closed after its behavioral write-reject proof), stays
read-only, and the row count stays 14 across the section (pure
read, zero mutation). Registration-time criteria fix, honest
note: the pre-registered AG2 wording named net_delta as a row
key - the product row keys exactly {month, windows,
total_delta}; net_delta is an envelope key, so the cross checks
the three row keys positionally plus the envelope total/net
pair against the SQL COUNT/SUM. Zero product files touched
(measurement face, R1727 precedent).


R1816 extension (cell-aggregate mirror-SQL third path): the [12]
section proved the scalar aggregation faces (kind_tally,
monthly_flow) against window-predicate GROUP BY counts/sums; this
section adds the independent third path for the per-cell
aggregation face cell_totals. The delta JSON expansion happens
engine-side via the json_each table value function (the product
face expands rows with Python json.loads - the two paths share no
expansion code), on the whole board, the historical fixture month,
the current flow month and the honest empty future month. The
envelope total cross-checks against SUM(total_delta) (an empty
filtered set makes SQL SUM return NULL, so the cross reads
COALESCE(SUM(total_delta), 0) - the honest zero, not a fabricated
value), the composition law re-proves on the SQL-side cells alone
(the verdicted cells ride inside the aggregate on every non-empty
window yet the arithmetic never adds them), and row-level filtered
aggregation shows each tamper row's cells with their month
attribution (ghost {noise.total:1} and drift {noise.total:5}, both
inside the current flow month, none inside the historical fixture
window) - the third path never hides the tamper rows at cell
level. Zero product files touched (measurement face, R1727
precedent).


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
        # R1813: drift ts derives from the pre-injection board tail row
        # month (the ghost-row R1809 method) so the injected row always
        # rides the real flow month; the old wall-clock-month-coupled
        # literal is gone and the [10] n_cur==11 count becomes a
        # month-independent structural constant.
        drift_w = pipe.journal.journal_board()["journal_board"][-1][
            "ts_utc"][:7]
        conn = sqlite3.connect(journal_db)
        conn.execute(
            "INSERT INTO water_windows (kind, delta, total_delta, ts_utc) "
            "VALUES ('submit', ?, 5, ?)",
            (json.dumps({"noise.total": 5}, sort_keys=True),
             drift_w + "-11T00:00:00.000000Z"))
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

        # ---- [10] board read-cap x month-window combo (R1812) ----
        # The R1804 product face journal_board(window, limit) has
        # had both parameters proven separately; this section proves
        # the orthogonal combination on the ghost-present world:
        # window filter first, mirror-SQL tail truncation second,
        # the envelope never lies about the window size, and the
        # reject ring stays unweakened across both gates.
        full_rl = pipe.journal.journal_board(cur_w)
        full_rows_rl = full_rl["journal_board"]
        n_cur = len(full_rows_rl)
        cap = pipe.journal.journal_board(cur_w, 3)
        cap_rows = cap["journal_board"]
        tail3 = full_rows_rl[-3:]
        pos_ok = all(a["window_id"] == b["window_id"]
                     and a["kind"] == b["kind"]
                     and a["delta"] == b["delta"]
                     and a["total_delta"] == b["total_delta"]
                     and a["ts_utc"] == b["ts_utc"]
                     for a, b in zip(cap_rows, tail3))
        rl1_ok = (n_cur == 11 and len(cap_rows) == 3
                  and cap["returned"] == 3 and pos_ok)

        keys_full = set(full_rl)
        keys_cap = set(cap)
        common_ok = all(full_rl[k] == cap[k]
                        for k in keys_full if k != "journal_board")
        rl2_ok = (keys_full <= keys_cap
                  and keys_cap - keys_full == {"limit", "returned",
                                               "truncated"}
                  and common_ok and cap["limit"] == 3
                  and cap["returned"] == 3 and cap["truncated"] is True)

        loose = pipe.journal.journal_board(cur_w, 99)
        loose_rows = loose["journal_board"]
        ghost_in_loose = any(r["kind"] == "legacy-ghost"
                             for r in loose_rows)
        futc = pipe.journal.journal_board("2026-12", 5)
        rl3_ok = (cap["total"] == full_rl["total"] == n_cur
                  and len(loose_rows) == n_cur
                  and loose["returned"] == n_cur
                  and loose["truncated"] is False
                  and loose["total"] == n_cur
                  and all(a["window_id"] == b["window_id"]
                          for a, b in zip(loose_rows, full_rows_rl))
                  and ghost_in_loose
                  and futc["journal_board"] == []
                  and futc["returned"] == 0
                  and futc["truncated"] is False
                  and futc["total"] == 0
                  and set(futc) - keys_full
                  == {"limit", "returned", "truncated"})

        rej_codes = []
        for bad in (-1, True, "3", 2.5):
            try:
                pipe.journal.journal_board(cur_w, bad)
                rej_codes.append("(none)")
            except ValueError as exc:
                rej_codes.append(str(exc).split("(")[-1].rstrip(")"))
        both_code = "(none)"
        try:
            pipe.journal.journal_board("bad-window", -1)
        except ValueError as exc:
            both_code = str(exc).split("(")[-1].rstrip(")")
        badwin_code = "(none)"
        try:
            pipe.journal.journal_board("2026-10\n", 3)
        except ValueError as exc:
            badwin_code = str(exc).split("(")[-1].rstrip(")")
        conn = sqlite3.connect(journal_db)
        rows_rl = conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        conn.close()
        rl4_ok = (rej_codes == ["E_WJ_BAD_LIMIT"] * 4
                  and both_code == "E_WJ_BAD_LIMIT"
                  and badwin_code == "E_WJ_BAD_WINDOW"
                  and rows_rl == 14)

        store_rl = json.dumps(pipe.store.pool_water_levels(),
                              sort_keys=True)
        rl5_ok = store_rl == store_pre
        # R1813 AC-DM3: month-abstracted drift ts ties the ghost ts
        # (same month, same -11T00:00:00.000000Z clock) so the board
        # order falls to the window_id tiebreak: drift row (injected
        # in [4]) precedes the ghost row (injected in [7]) - the
        # pre-R1813 order carried forward.
        drift_pos = next(i for i, r in enumerate(full_rows_rl)
                        if r["kind"] == "submit"
                        and r["total_delta"] == 5)
        ghost_pos = next(i for i, r in enumerate(full_rows_rl)
                         if r["kind"] == "legacy-ghost")
        ts_tie = (full_rows_rl[drift_pos]["ts_utc"]
                  == full_rows_rl[ghost_pos]["ts_utc"]
                  == drift_w + "-11T00:00:00.000000Z")
        tie_ok = (ts_tie and drift_pos < ghost_pos
                  and drift_w == cur_w)
        sections.append("[10] board read-cap x month-window combo:")
        sections.append("    tail-truncation: cur-rows=%d cap-rows=%d "
                       "positional=%s %s"
                        % (n_cur, len(cap_rows), pos_ok,
                           "OK" if rl1_ok else "DRIFT"))
        sections.append("    drift-month tie-order (R1813): "
                       "drift_w=%s==cur_w=%s ts-tie=%s "
                       "drift-pos=%d ghost-pos=%d %s"
                        % (drift_w, cur_w, ts_tie,
                           drift_pos, ghost_pos,
                           "OK" if tie_ok else "DRIFT"))
        sections.append("    envelope additive: diff-keys=%s "
                       "common-eq=%s limit=%s returned=%s "
                       "truncated=%s %s"
                        % (",".join(sorted(keys_cap - keys_full))
                           or "(none)", common_ok, cap["limit"],
                           cap["returned"], cap["truncated"],
                           "OK" if rl2_ok else "DRIFT"))
        sections.append("    total full-count: cap-total=%d "
                       "full-total=%d loose99 returned=%d "
                       "truncated=%s ghost-in-loose=%s "
                       "fut-2026-12 cap5 rows=%d returned=%d "
                       "truncated=%s total=%d %s"
                        % (cap["total"], full_rl["total"],
                           loose["returned"], loose["truncated"],
                           ghost_in_loose,
                           len(futc["journal_board"]), futc["returned"],
                           futc["truncated"], futc["total"],
                           "OK" if rl3_ok else "DRIFT"))
        sections.append("    bad-limit ring: codes=%s both-bad=%s "
                       "bad-window=%s rows %d==14 %s"
                        % ("/".join(rej_codes), both_code, badwin_code,
                           rows_rl,
                           "OK" if rl4_ok else "DRIFT"))
        sections.append("    store zero-background+pure-read: "
                       "identical=%s %s"
                        % (rl5_ok, "OK" if rl5_ok else "DRIFT"))
        fail = fail or not (rl1_ok and rl2_ok and rl3_ok and rl4_ok
                            and rl5_ok and tie_ok)

        # ---- [11] mirror-SQL third path for capped reads (R1814) --
        # The [10] tail-truncation face compared two paths over the
        # product connection (cap read vs full-read tail). This
        # section adds the independent third path: a raw read-only
        # SQL connection (file URI mode=ro) running the product's
        # mirror clause verbatim - window predicate first, then
        # ORDER BY ts_utc DESC, window_id DESC LIMIT N, reversed
        # back to board order. Every capped combination (global /
        # month-window / loose) equals its product read position by
        # position, the tamper rows stay visible on the raw path,
        # the honest-empty and historical windows keep their laws,
        # and the read-only connection rejects a write attempt at
        # the connection level (zero mutation, count constant).
        ro = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)

        def mirror_sql(window=None, limit=0):
            where = ""
            args = []
            if window is not None:
                where = " WHERE substr(ts_utc, 1, 7) = ?"
                args.append(window)
            sql = ("SELECT window_id, kind, delta, total_delta, ts_utc"
                   " FROM water_windows" + where)
            if limit > 0:
                order = " ORDER BY ts_utc DESC, window_id DESC LIMIT ?"
                fetched = [list(r) for r in
                           ro.execute(sql + order, args + [limit])]
                fetched.reverse()
            else:
                order = " ORDER BY ts_utc, window_id"
                fetched = [list(r) for r in
                           ro.execute(sql + order, args)]
            return [{"window_id": r[0], "kind": r[1],
                     "delta": json.loads(r[2]), "total_delta": r[3],
                     "ts_utc": r[4]} for r in fetched]

        def rows_equal5(a_rows, b_rows):
            return (len(a_rows) == len(b_rows)
                    and all(x["window_id"] == y["window_id"]
                            and x["kind"] == y["kind"]
                            and x["delta"] == y["delta"]
                            and x["total_delta"] == y["total_delta"]
                            and x["ts_utc"] == y["ts_utc"]
                            for x, y in zip(a_rows, b_rows)))

        glob_cap = pipe.journal.journal_board(limit=3)
        glob_rows = glob_cap["journal_board"]
        sq1_sql = mirror_sql(limit=3)
        glob_cnt = ro.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        sq1_ok = (rows_equal5(glob_rows, sq1_sql)
                  and rows_equal5(glob_rows, cap_rows)
                  and glob_cap["returned"] == len(sq1_sql) == 3
                  and glob_cap["truncated"] is True
                  and glob_cap["total"] == glob_cnt == 14)

        sq2_sql = mirror_sql(cur_w, 3)
        cur_cnt_sql = ro.execute(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE substr(ts_utc, 1, 7) = ?", (cur_w,)).fetchone()[0]
        sq2_ok = (rows_equal5(sq2_sql, cap_rows)
                  and cur_cnt_sql == n_cur == 11)

        sq3_sql = mirror_sql(cur_w, 99)
        ghost_sql_n = sum(1 for r in sq3_sql
                          if r["kind"] == "legacy-ghost")
        drift_sql_n = sum(1 for r in sq3_sql
                          if r["kind"] == "submit"
                          and r["total_delta"] == 5)
        sq3_ok = (rows_equal5(sq3_sql, loose_rows)
                  and len(sq3_sql) == n_cur
                  and ghost_sql_n == 1 and drift_sql_n == 1)

        sq4_fut = mirror_sql("2026-12", 5)
        hist_cnt_sql = ro.execute(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE substr(ts_utc, 1, 7) = ?",
            ("2026-08",)).fetchone()[0]
        hist_cap = pipe.journal.journal_board("2026-08", 3)
        hist_sql = mirror_sql("2026-08", 3)
        sq4_ok = (sq4_fut == [] and hist_cnt_sql == 3
                  and hist_cap["returned"] == 3
                  and rows_equal5(hist_sql, hist_cap["journal_board"]))

        ro_write_reject = "(none)"
        try:
            ro.execute("INSERT INTO water_windows (kind, delta,"
                       " total_delta, ts_utc) VALUES ('probe-read',"
                       " '{}', 0, '1970-01-01T00:00:00.000000Z')")
            ro.commit()
        except sqlite3.OperationalError:
            ro_write_reject = "OperationalError"
        ro_cnt = ro.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        ro.close()
        sq5_ok = (ro_write_reject == "OperationalError"
                  and ro_cnt == rows_rl == 14)

        sections.append("[11] mirror-SQL third path (capped reads):")
        sections.append("    global cap: sql-rows=%d pos-vs-product=%s"
                        " pos-vs-window-cap=%s returned=%d"
                        " truncated=%s total=%d==%d %s"
                        % (len(sq1_sql),
                           rows_equal5(glob_rows, sq1_sql),
                           rows_equal5(glob_rows, cap_rows),
                           glob_cap["returned"],
                           glob_cap["truncated"],
                           glob_cap["total"], glob_cnt,
                           "OK" if sq1_ok else "DRIFT"))
        sections.append("    month-window combo: sql-rows=%d"
                        " pos-vs-cap=%s win-count=%d==n_cur=%d %s"
                        % (len(sq2_sql),
                           rows_equal5(sq2_sql, cap_rows),
                           cur_cnt_sql, n_cur,
                           "OK" if sq2_ok else "DRIFT"))
        sections.append("    loose 99: sql-rows=%d pos-vs-product=%s"
                        " ghost=%d drift=%d %s"
                        % (len(sq3_sql),
                           rows_equal5(sq3_sql, loose_rows),
                           ghost_sql_n, drift_sql_n,
                           "OK" if sq3_ok else "DRIFT"))
        sections.append("    honest empty/hist: fut-rows=%d"
                        " hist-count=%d hist-cap-pos=%s %s"
                        % (len(sq4_fut), hist_cnt_sql,
                           rows_equal5(hist_sql,
                                       hist_cap["journal_board"]),
                           "OK" if sq4_ok else "DRIFT"))
        sections.append("    read-only: write-reject=%s rows"
                        " %d==%d==14 %s"
                        % (ro_write_reject, ro_cnt, rows_rl,
                           "OK" if sq5_ok else "DRIFT"))
        fail = fail or not (sq1_ok and sq2_ok and sq3_ok and sq4_ok
                            and sq5_ok)

        # ---- [12] aggregate mirror-SQL third path (R1815) -----------
        # The [6]/[9] sections proved the product aggregation faces
        # against hand-grouped / hand-summed derivations (path two).
        # This section adds the independent third path: a fresh
        # read-only SQL connection (the [11] connection closed after
        # its write-reject proof) running the window-predicate GROUP
        # BY aggregates - kind_tally(W) dense dict vs GROUP BY kind
        # COUNT(*), monthly_flow(W) row vs GROUP BY substr
        # COUNT(*)/SUM(total_delta), on every observed month, plus
        # the whole-board month set without the WHERE clause.
        # Registration-time criteria fix (honest note): AG2's
        # pre-registered wording named net_delta as a row key - the
        # product row keys exactly {month, windows, total_delta};
        # net_delta is an envelope key, so the cross checks the
        # three row keys positionally plus the envelope pair.
        agg_ro = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        agg_cnt_before = agg_ro.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]

        def sql_kind_counts(window):
            # Native SQL GROUP BY returns a sparse row set (observed
            # kinds only); the product face is dense (closed-set kinds
            # stay explicit at zero, foreign keys appended sorted -
            # the AC-KT1 dense grid law). The dense expansion below
            # is the probe-side interpretation layer mirroring the
            # [6] hand_group_kinds construction, so the cross
            # compares dense-vs-dense (first run honest fix: the
            # sparse-vs-dense dict compare drifted on the historical
            # fixture month, a probe wording flaw, not a product
            # defect - the historical window only observes
            # submit/verdict so the sparse SQL dict lacks the three
            # zero-count kinds).
            rows = agg_ro.execute(
                "SELECT kind, COUNT(*) FROM water_windows"
                " WHERE substr(ts_utc, 1, 7) = ? GROUP BY kind",
                (window,)).fetchall()
            observed = {k: int(n) for k, n in rows}
            dense = {}
            rest = dict(observed)
            for kind in sorted(WJ.KINDS):
                dense[kind] = int(rest.pop(kind, 0))
            for kind in sorted(rest):
                dense[kind] = rest[kind]
            return dense

        def sql_flow_rows(window=None):
            if window is None:
                grouped = agg_ro.execute(
                    "SELECT substr(ts_utc, 1, 7), COUNT(*),"
                    " SUM(total_delta) FROM water_windows"
                    " GROUP BY substr(ts_utc, 1, 7)"
                    " ORDER BY substr(ts_utc, 1, 7)").fetchall()
            else:
                grouped = agg_ro.execute(
                    "SELECT substr(ts_utc, 1, 7), COUNT(*),"
                    " SUM(total_delta) FROM water_windows"
                    " WHERE substr(ts_utc, 1, 7) = ?"
                    " GROUP BY substr(ts_utc, 1, 7)"
                    " ORDER BY substr(ts_utc, 1, 7)",
                    (window,)).fetchall()
            return [{"month": m, "windows": int(n),
                     "total_delta": int(s)} for m, n, s in grouped]

        ag1_ok = True
        ag1_detail = []
        for w in months:
            tally_env = pipe.journal.kind_tally(w)
            tally = dict(tally_env["kind_tally"])
            sql_kinds = sql_kind_counts(w)
            win_cnt = agg_ro.execute(
                "SELECT COUNT(*) FROM water_windows"
                " WHERE substr(ts_utc, 1, 7) = ?", (w,)).fetchone()[0]
            ghost_n = int(tally.get("legacy-ghost", 0))
            w_ok = (tally == sql_kinds
                    and int(tally_env["total"]) == win_cnt
                    and sum(sql_kinds.values()) == win_cnt
                    and ghost_n == (1 if w == cur_w else 0))
            ag1_ok = ag1_ok and w_ok
            ag1_detail.append(
                "%s tally==sql=%s total==cnt %d==%d ghost=%d %s"
                % (w, tally == sql_kinds,
                   int(tally_env["total"]), win_cnt, ghost_n,
                   "OK" if w_ok else "DRIFT"))

        ag2_ok = True
        ag2_detail = []
        for w in months:
            flow_env = pipe.journal.monthly_flow(w)
            flow_rows = flow_env["monthly_flow"]
            sql_rows = sql_flow_rows(w)
            r = flow_rows[0] if flow_rows else None
            q = sql_rows[0] if sql_rows else None
            f_ok = (r is not None and q is not None
                    and r["month"] == q["month"]
                    and int(r["windows"]) == q["windows"]
                    and int(r["total_delta"]) == q["total_delta"]
                    and int(flow_env["total"]) == q["windows"]
                    and int(flow_env["net_delta"]) == q["total_delta"])
            ag2_ok = ag2_ok and f_ok
            ag2_detail.append(
                "%s month=%s windows %d==%d total_delta %d==%d"
                " env total/net %d/%d %s"
                % (w,
                   r["month"] if r else "-",
                   int(r["windows"]) if r else -1,
                   q["windows"] if q else -1,
                   int(r["total_delta"]) if r else -999,
                   q["total_delta"] if q else -999,
                   int(flow_env["total"]), int(flow_env["net_delta"]),
                   "OK" if f_ok else "DRIFT"))

        board_flow_env = pipe.journal.monthly_flow()
        board_rows = board_flow_env["monthly_flow"]
        sql_board_rows = sql_flow_rows(None)
        ag3_ok = (board_rows == sql_board_rows
                  and [r["month"] for r in board_rows] == months
                  and int(board_flow_env["total"])
                  == sum(r["windows"] for r in sql_board_rows)
                  and int(board_flow_env["net_delta"])
                  == sum(r["total_delta"] for r in sql_board_rows))

        hist_cnt = agg_ro.execute(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE substr(ts_utc, 1, 7) = ?",
            ("2026-08",)).fetchone()[0]
        fut_cnt = agg_ro.execute(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE substr(ts_utc, 1, 7) = ?",
            ("2026-12",)).fetchone()[0]
        fut_env = pipe.journal.monthly_flow("2026-12")
        ag4_ok = (hist_cnt == 3 and fut_cnt == 0
                  and fut_env["monthly_flow"] == []
                  and sql_flow_rows("2026-12") == [])

        agg_cnt_after = agg_ro.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        agg_ro.close()
        ag5_ok = (agg_cnt_before == agg_cnt_after == rows_rl == 14)

        sections.append("[12] aggregate mirror-SQL third path:")
        for line in ag1_detail:
            sections.append("    kind_tally " + line)
        for line in ag2_detail:
            sections.append("    monthly_flow " + line)
        sections.append("    whole-board: months=%s rows==sql=%s"
                        " env total=%d net=%d %s"
                        % (",".join(months),
                           board_rows == sql_board_rows,
                           int(board_flow_env["total"]),
                           int(board_flow_env["net_delta"]),
                           "OK" if ag3_ok else "DRIFT"))
        sections.append("    zero penetration: hist-cnt=%d fut-cnt=%d"
                        " fut-env-empty=%s %s"
                        % (hist_cnt, fut_cnt,
                           fut_env["monthly_flow"] == [],
                           "OK" if ag4_ok else "DRIFT"))
        sections.append("    pure-read: rows %d==%d==14 %s"
                        % (agg_cnt_before, agg_cnt_after,
                           "OK" if ag5_ok else "DRIFT"))
        fail = fail or not (ag1_ok and ag2_ok and ag3_ok and ag4_ok
                            and ag5_ok)

        # ---- [13] cell-aggregate mirror-SQL third path (R1816) --
        # The [12] section proved the scalar aggregation faces
        # (kind_tally, monthly_flow) against window-predicate GROUP
        # BY counts/sums. This section adds the independent third
        # path for the per-cell aggregation face cell_totals: the
        # delta JSON expansion happens engine-side via the json_each
        # table value function (the product face expands rows with
        # Python json.loads - the two paths share no expansion
        # code), the window predicate rides the same substr clause,
        # the envelope total cross-checks against SUM(total_delta),
        # and the composition law re-proves on the SQL-side cells
        # alone. Registration-time honest note: an empty filtered
        # set makes SQL SUM return NULL, so the envelope cross reads
        # COALESCE(SUM(total_delta), 0) - the honest zero.
        cell_ro = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        cell_cnt_before = cell_ro.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]

        def sql_cell_aggregate(window=None):
            where = ""
            args = []
            if window is not None:
                where = " WHERE substr(ts_utc, 1, 7) = ?"
                args.append(window)
            cell_rows = cell_ro.execute(
                "SELECT je.key, SUM(CAST(je.value AS INTEGER))"
                " FROM water_windows, json_each(water_windows.delta) je"
                + where + " GROUP BY je.key ORDER BY je.key",
                args).fetchall()
            cells = {}
            for key, value in cell_rows:
                cells[str(key)] = int(value)
            sum_row = cell_ro.execute(
                "SELECT COALESCE(SUM(total_delta), 0)"
                " FROM water_windows" + where, args).fetchone()
            return cells, int(sum_row[0])

        def sql_row_cells(row_where, args):
            cell_rows = cell_ro.execute(
                "SELECT je.key, SUM(CAST(je.value AS INTEGER))"
                " FROM water_windows, json_each(water_windows.delta) je"
                " WHERE " + row_where +
                " GROUP BY je.key ORDER BY je.key", args).fetchall()
            return {str(k): int(v) for k, v in cell_rows}

        ca_windows = [("whole-board", None),
                      ("hist-2026-08", "2026-08"),
                      ("cur-" + cur_w, cur_w),
                      ("fut-2026-12", "2026-12")]
        ca1_ok = True
        ca2_ok = True
        ca2_verdicted = False
        ca1_detail = []
        ca2_detail = []
        for label, w in ca_windows:
            env = (pipe.journal.cell_totals(w) if w is not None
                   else pipe.journal.cell_totals())
            sql_cells, sql_total = sql_cell_aggregate(w)
            keys_ok = (list(env["cell_totals"]) == list(sql_cells)
                       == sorted(sql_cells))
            dict_ok = dict(env["cell_totals"]) == sql_cells
            total_ok = int(env["total"]) == sql_total
            comp_sum = (sql_cells.get("noise.total", 0)
                        + sql_cells.get("review.suspended", 0))
            comp_ok = sql_total == comp_sum
            verdicted_here = any(
                k.startswith("review.verdicted.") for k in sql_cells)
            ca2_verdicted = ca2_verdicted or (
                verdicted_here and comp_ok and sql_total != 0)
            ca1_ok = ca1_ok and keys_ok and dict_ok and total_ok
            ca2_ok = ca2_ok and comp_ok
            ca1_detail.append(
                "%s cells==sql=%s keys-asc=%s total %d==%d %s"
                % (label, dict_ok, keys_ok, int(env["total"]),
                   sql_total, "OK" if (keys_ok and dict_ok
                                       and total_ok) else "DRIFT"))
            ca2_detail.append(
                "%s total=%d noise.total=%d susp=%d comp=%d %s"
                % (label, sql_total,
                   sql_cells.get("noise.total", 0),
                   sql_cells.get("review.suspended", 0), comp_sum,
                   "OK" if comp_ok else "DRIFT"))
        ca2_ok = ca2_ok and ca2_verdicted

        ghost_cells = sql_row_cells("kind = 'legacy-ghost'", [])
        drift_cells = sql_row_cells(
            "kind = 'submit' AND total_delta = 5", [])
        tamper_cur = cell_ro.execute(
            "SELECT COUNT(*) FROM water_windows WHERE (kind ="
            " 'legacy-ghost' OR (kind = 'submit' AND total_delta"
            " = 5)) AND substr(ts_utc, 1, 7) = ?",
            (cur_w,)).fetchone()[0]
        tamper_hist = cell_ro.execute(
            "SELECT COUNT(*) FROM water_windows WHERE (kind ="
            " 'legacy-ghost' OR (kind = 'submit' AND total_delta"
            " = 5)) AND substr(ts_utc, 1, 7) = '2026-08'",
            ()).fetchone()[0]
        hist_cells_sql, hist_total_sql = sql_cell_aggregate("2026-08")
        ca3_ok = (ghost_cells == {"noise.total": 1}
                  and drift_cells == {"noise.total": 5}
                  and tamper_cur == 2 and tamper_hist == 0
                  and hist_cells_sql.get("noise.total") == 1
                  and hist_total_sql == -1)

        fut_env = pipe.journal.cell_totals("2026-12")
        fut_cells_sql, fut_total_sql = sql_cell_aggregate("2026-12")
        ca4_ok = (fut_env["cell_totals"] == {} and fut_cells_sql == {}
                  and int(fut_env["total"]) == 0
                  and fut_total_sql == 0)

        cell_cnt_after = cell_ro.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        cell_ro.close()
        ca5_ok = (cell_cnt_before == cell_cnt_after
                  == rows_rl == 14)

        sections.append("[13] cell-aggregate mirror-SQL third path:")
        for line in ca1_detail:
            sections.append("    cells " + line)
        for line in ca2_detail:
            sections.append("    composition " + line)
        sections.append("    verdicted-carried-excluded=%s (cells"
                        " carry review.verdicted.* keys on non-empty"
                        " windows; the arithmetic never adds them)"
                        % ca2_verdicted)
        sections.append("    tamper cells: ghost=%s drift=%s"
                        " cur-count=%d hist-count=%d"
                        " hist-noise.total=%d %s"
                        % (json.dumps(ghost_cells, sort_keys=True),
                           json.dumps(drift_cells, sort_keys=True),
                           tamper_cur, tamper_hist,
                           hist_cells_sql.get("noise.total", 0),
                           "OK" if ca3_ok else "DRIFT"))
        sections.append("    honest empty: fut-2026-12 cells=={}=%s"
                        " total 0==%d (empty SUM -> COALESCE 0) %s"
                        % (fut_cells_sql == {}, fut_total_sql,
                           "OK" if ca4_ok else "DRIFT"))
        sections.append("    pure-read: rows %d==%d==14 %s"
                        % (cell_cnt_before, cell_cnt_after,
                           "OK" if ca5_ok else "DRIFT"))
        fail = fail or not (ca1_ok and ca2_ok and ca3_ok and ca4_ok
                            and ca5_ok)

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
        sections.append("[14] hygiene: probe-ascii=%s import-lines-clean=%s "
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
