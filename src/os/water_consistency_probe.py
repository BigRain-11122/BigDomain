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


R1817 extension (delta JSON engine-side integrity): the [13]
section rode json_each with CAST(je.value AS INTEGER) - safe only
while every delta is well-formed JSON whose leaf values are all
integers. This section enforces that structural premise
engine-side on the 14-row baseline world (json_valid across all
rows + json_tree non-root leaf types all 'integer' + a three-way
leaf-count cross: json_tree non-root nodes == json_each rows ==
the product-side sum of len(delta dict) over the whole board),
then proves the detection faces with two injected negative paths
(the tamper posture of R1809/R1801, PRAGMA ignore_check_constraints
direct INSERT, month-abstract ts on the -21T hour so the row
never collides with the drift/ghost -11T tie window):
a malformed-JSON row caught both ways (SQL json_valid=0
engine-side point-name vs the product cell_totals() json.loads
fail-closed crash - two detection faces on the same injected
row), then a non-integer-leaf row (valid JSON, a text leaf - the
CAST premise broken on both sides: json_tree non-root non-integer
leaf count engine-side vs the product sum-stage TypeError). Each
injected row is deleted by its window_id right after its two
faces are recorded, the board returns to 14 rows and the
integrity face re-reads green (valid0=0, non-integer leaves=0,
product cell_totals() total back to the whole-board registered
value). Measurement face, R1727 precedent, not registered into
SUITES. Zero product files touched.


R1818 extension (per-row delta literal conservation): the [14]
section enforced the structural premise; this section pins the
per-row literal plane on the clean 14-row world. Three paths per
row - the product board delta dict (the json.loads route, the
reference), the SQL json_extract per-key route (per-key value
equality plus the json_type 'integer' premise plus the
json_quote leaf-literal face: the engine's quoted text of the
extracted value equals the product json.dumps of that value;
key-set closure rides the [14] three-way leaf-count cross, not
repeated), and the SQL json(delta) re-parse route (the engine
canonical text json.loads-ed back must equal the row dict). Two
literal laws: the engine canonical text equals the product
compact serialization (json.dumps sort_keys=True with tight
separators) byte for byte, and the stored write-format text is a
fixed point of the writer's own serialization law (the
default-separator json.dumps sort_keys=True of the record()
face) - the write-read literal round trip. The injected
negative-path faces stay in [14] (in-book, not repeated).
Measurement face, R1727 precedent, not registered into SUITES.
Zero product files touched.


R1819 extension (ts_utc engine-side format integrity): the
[14]/[15] sections pinned the delta column; this section pins
the ts_utc column - the structural premise of the month-window
predicate substr(ts_utc,1,7) and the ORDER BY ts_utc sort key.
Premise correction, honest note: the seed text said a 26-char
fixed form; the product record() rides strftime %f (always
six-digit microseconds), so the real fixed length is 27 - the
judgment runs on 27 throughout. Baseline face (clean 14-row
world): LENGTH(ts_utc)=27 on every row (violator count 0, the
distinct length set exactly {27}), the fixed digit-shape GLOB
pattern matches every row, and julianday(ts_utc) parses every
row (no NULLs). Month-predicate three-face consistency: the
SQL DISTINCT substr(ts_utc,1,7) month set == the product
monthly_flow() row month set == the board row ts_utc[:7]
prefix set - the prefix-is-a-real-month-key law the window
filter leans on. Two injected negative paths (ts_utc carries
no CHECK constraint, kind rides inside the closed set - a
plain INSERT, no PRAGMA posture needed; month-abstract ts
derived from cur_w, the R1813 law): a short-day shape (26
chars, GLOB miss, julianday NULL - caught by every face) and
a bad-calendar shape (27 chars, GLOB passes, julianday NULL -
the calendar face is its sole detector, so the shape faces and
the calendar face stay independent). The honest product-side
note: the pure-prefix month predicate validates nothing - both
bad-ts rows still flow into the current-month window (board
total 11->13, flow windows 11->13), so the format premise is
enforced on this probe face, not in the product. DELETE
restore: both rows removed by window_id, the board back to 14
rows, all three faces green again, the month-set cross back to
the baseline set, the product whole-board total back to the
registered 11. Measurement face, R1727 precedent, not
registered into SUITES. Zero product files touched.


R1820 extension (ts lexicographic == chronological total
order): the [16] section pinned the fixed 27-char shape; this
section pins the sort-key semantics - over a well-formed world
the text order (ORDER BY ts_utc, window_id) equals the
chronological order (ORDER BY julianday(ts_utc), window_id)
row by row, and the product board read (ORDER BY ts_utc DESC,
window_id DESC, reversed to ascending) carries the same
sequence - the fixed-length ISO form makes the lexicographic
order a chronological order. Tie window: the drift/ghost pair
shares one ts; the product order falls to the window_id
tiebreak and the full-board read shows drift (kind submit,
injected in [4]) before ghost (legacy-ghost, injected in [7])
at adjacent positions - the [10] in-register order re-proven
on the whole-board read. Negative path: one bad-calendar row
(27 chars, GLOB passes, julianday NULL - the [16] B shape,
month-abstract ts) is an incomparable key - the chronological
order is no longer total (SQLite floats the NULL row first in
ASC), while the text order stays total: a valid hour starts
with 0/1/2, the -99T hour starts with 9, so the bad row
always sorts last in ascending text order (a constructive
position, wall-clock independent), and the product read
places it last - the pure text order does not depend on
parseability (honest note; the enforcement face lives on
this probe). DELETE restore: the row removed by window_id,
every face back to the 14-row registered values. Measurement
face, R1727 precedent, not registered into SUITES. Zero
product files touched.

R1821 extension (kind CHECK constraint engine-side enforcement):
the [7] ghost injection rode PRAGMA ignore_check_constraints -
indirect evidence the kind column CHECK exists. This section
proves the constraint body face on the engine: a default-posture
out-of-domain kind plain INSERT raises sqlite3.IntegrityError
carrying the CHECK message and lands zero rows; the pragma switch
is a reversible dual state (ON lands the very same INSERT, OFF
on the same connection restores the rejection of a second
out-of-domain kind); and the positive closed set holds - all
five legal kinds INSERT cleanly, so the constraint is exactly
the closed set, never over-restrictive. Positive rows carry an
empty delta and total_delta 0 (the value faces stay untouched
while the count faces move: kind_tally(cur_w) gains +1 per legal
kind). DELETE restore by window_id: the row count returns to 14,
cell_totals total returns to the registered 11, and the
whole-board and current-window tallies return to their
pre-injection dicts - the R1820 world state intact. Measurement
face, R1727 precedent, not registered into SUITES. Zero
product files touched.

R1822 extension (kind CHECK constraint schema-text readback):
the [18] section proved the constraint on behavior (IntegrityError
/ pragma dual state / positive closed set); this section reads the
constraint body text face, engine-side and product-side. The engine
archives the executed CREATE TABLE statement in sqlite_master - the
probe reads it back through a mode=ro connection and asserts: the
water_windows row is exactly one (the honest table-set reading also
lists sqlite_sequence, the AUTOINCREMENT bookkeeping table, not a
product table); the stored sql carries the CHECK clause verbatim
with each of the five kind values present; the stored sql is
byte-identical to the product WJ.SCHEMA constant after the
verified engine normalization (strip the "IF NOT EXISTS " marker,
outer whitespace and the trailing semicolon - single source of
truth: the module constant the constructor executes is the very
text the engine archived); and PRAGMA table_info pins the
five-column metadata (kind is TEXT NOT NULL, non-pk; window_id is
the INTEGER pk). Pure readback - zero injections, zero deletes,
the row count stays 14 throughout; the [18] behavior face stays
in-register, not repeated. Measurement face, R1727 precedent,
not registered into SUITES. Zero product files touched.

R1823 extension (sqlite_sequence AUTOINCREMENT high-water
bookkeeping readback): the [19] honest table set already listed
sqlite_sequence, the AUTOINCREMENT bookkeeping table - this
section reads its body. The ever-max assigned id (seq) is a
structural constant of the probe world: ids 1..25 were all
assigned in operation order (nine real windows, the drift row 10,
three fixture rows 11..13, the ghost row 14, then the
inject-then-delete rounds consumed 15..25), so at the [19] end
state seq is 25 while the live MAX(window_id) is 14 - the
no-reuse guarantee read directly: deleted ids never return. The
engine semantics were pinned empirically before this section
landed (R1704 law; hw_precheck, SQLite 3.50.4: high-water never
retreats across deletes; a fresh insert consumes seq+1). The
section then demonstrates the consume-and-restore round: a fresh
closed-set INSERT (delta '{}', total_delta 0 - the value faces
stay untouched while the count face moves) consumes seq+1 == 26
and advances the bookkeeping row to 26; deleting that row returns
the 14-row world with the product faces back at their registered
dicts while seq stays at 26 - the high-water never retreats, the
no-reuse semantics read end to end. Measurement face, R1727
precedent, not registered into SUITES. Zero product files
touched.

R1832 extension (sqlite_sequence bookkeeping tamper id-reuse
negative path): the [20] section read the high-water bookkeeping
row as the no-reuse guarantee (seq 26 over live max 14, deleted
ids never return). This section proves the guarantee's single
point of dependence: SQLite allows a direct UPDATE on the
sqlite_sequence bookkeeping row, and the bookkeeping table
carries no constraint protecting it. Rolling seq back to 0 while
deleted ids 15..26 sit above the live max breaks the guarantee -
the next INSERT allocates max(seq, live max)+1 == 15, the id of
a row that was already used and deleted ([20] census). Engine
semantics were pinned empirically before this section landed
(R1704 law; tp_precheck, SQLite 3.50.4: after the rollback a
fresh INSERT reuses the deleted id and the bookkeeping row
re-anchors at the wrong lower watermark). The tamper-reuse-
restore round: rollback seq to 0 (product rows untouched, value
faces at their registered dicts), prove the reused id 15
surfaces in the product count faces (journal_board(cur_w)
total 11->12, COUNT 14->15 - the value face stays untouched:
delta '{}', total_delta 0), restore the high-water 26, then
delete the reused row by window_id - the 14-row world returns
with the product faces back at their registered dicts while seq
stays at 26 (deletion never touches the bookkeeping row, [20]
AC-HW4 law). Measurement face, R1727 precedent, not registered
into SUITES. Zero product files touched.


R1838 extension (sqlite_sequence bookkeeping-row DELETE missing
state): the [21] section proved the no-reuse guarantee fails when
the bookkeeping row is tampered (UPDATE rollback); this section
proves the second failure face - SQLite also allows a direct
DELETE of the bookkeeping row. With the row gone the AUTOINCREMENT
allocator degrades to the plain rowid rule: the next INSERT
allocates max(rowid)+1 == 15, reusing the id of a row that was
already used and deleted (the same lost-guard construction as
[21], reached without touching a single product row value), and
that INSERT self-rebuilds the bookkeeping row carrying the wrong
lower watermark (seq == 15). Engine semantics were pinned
empirically before this section landed (R1704 law; dm_precheck,
SQLite 3.50.4 - which also falsified the first restore ruling:
sqlite_sequence.name carries no UNIQUE, so a naive re-INSERT
beside the self-rebuilt row creates a duplicate row while the
plain read keeps returning the old one; the post-consume restore
is therefore an UPDATE on the rebuilt row, and the direct
re-INSERT is legal only while the row is truly missing). The
missing-reuse-restore round: evaporate the bookkeeping row
(product rows untouched), prove the degraded allocation reuses
id 15 and surfaces in the count faces (journal_board(cur_w)
11->12, value faces untouched: delta '{}', total_delta 0),
restore the high-water 26 by UPDATE on the self-rebuilt row,
delete the reused row - the 14-row world returns at seq 26.
Second missing round: re-evaporate and restore by direct
re-INSERT while truly missing (zero ids consumed), then prove
the re-arm - a fresh INSERT allocates 27 == seq+1, not 15 - and
delete it, leaving the honest final state (14 rows, seq 27: the
consume advanced the high-water and the delete never retreats
it). Measurement face, R1727 precedent, not registered into
SUITES. Zero product files touched.


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

        # ---- [14] delta JSON engine-side integrity (R1817) ------
        # The [13] section rode json_each with CAST(je.value AS
        # INTEGER) - safe only while every delta is well-formed
        # JSON whose leaf values are all integers. This section
        # enforces that structural premise engine-side and proves
        # the detection faces with two injected negative paths
        # (tamper posture of R1809/R1801, month-abstract ts on the
        # -21T hour so the rows never collide with the drift/ghost
        # -11T tie window). Each injected row is deleted by its
        # window_id right after its faces are recorded, the board
        # returns to 14 rows and the integrity face re-reads green.
        ji_ro = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        ji_base_rows = ji_ro.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        ji_base_valid0 = ji_ro.execute(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE json_valid(delta) <> 1").fetchone()[0]
        ji_base_bad_leaves = ji_ro.execute(
            "SELECT COUNT(*) FROM water_windows,"
            " json_tree(water_windows.delta) jt"
            " WHERE jt.parent IS NOT NULL"
            " AND jt.type <> 'integer'").fetchone()[0]
        ji_tree_leaves = ji_ro.execute(
            "SELECT COUNT(*) FROM water_windows,"
            " json_tree(water_windows.delta) jt"
            " WHERE jt.parent IS NOT NULL").fetchone()[0]
        ji_each_total = ji_ro.execute(
            "SELECT COUNT(*) FROM water_windows,"
            " json_each(water_windows.delta) je").fetchone()[0]
        ji_ro.close()
        board_all = pipe.journal.journal_board()
        ji_product_leaves = sum(len(r["delta"])
                                for r in board_all["journal_board"])
        ji1_ok = (ji_base_rows == 14
                  and ji_base_valid0 == 0
                  and ji_base_bad_leaves == 0
                  and ji_tree_leaves == ji_each_total
                  == ji_product_leaves)

        # negative path 1: malformed JSON row, caught both ways
        ji_inject_ts = cur_w + "-21T00:00:00.000000Z"
        ji_conn = sqlite3.connect(journal_db)
        ji_conn.execute("PRAGMA ignore_check_constraints = ON")
        ji_conn.execute(
            "INSERT INTO water_windows (kind, delta, total_delta,"
            " ts_utc) VALUES (?, ?, ?, ?)",
            ("submit", "not-json{", 0, ji_inject_ts))
        ji_conn.commit()
        ji_conn.execute("PRAGMA ignore_check_constraints = OFF")
        ji_conn.close()
        ji_ro2 = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        ji_bad_valid0 = ji_ro2.execute(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE json_valid(delta) <> 1").fetchone()[0]
        ji_bad_wid, ji_bad_delta = ji_ro2.execute(
            "SELECT window_id, delta FROM water_windows"
            " WHERE json_valid(delta) <> 1").fetchone()
        ji_ro2.close()
        try:
            pipe.journal.cell_totals()
            ji_bad_crash = None
        except ValueError as exc:
            ji_bad_crash = type(exc).__name__
        ji2_ok = (ji_bad_valid0 == 1
                  and ji_bad_delta == "not-json{"
                  and ji_bad_crash is not None)

        ji_conn2 = sqlite3.connect(journal_db)
        ji_conn2.execute(
            "DELETE FROM water_windows WHERE window_id = ?",
            (ji_bad_wid,))
        ji_conn2.commit()
        ji_conn2.close()

        # negative path 2: valid JSON, non-integer leaf - the
        # CAST premise broken on both sides
        ji_conn3 = sqlite3.connect(journal_db)
        ji_conn3.execute("PRAGMA ignore_check_constraints = ON")
        ji_conn3.execute(
            "INSERT INTO water_windows (kind, delta, total_delta,"
            " ts_utc) VALUES (?, ?, ?, ?)",
            ("submit", '{"noise.total":"five"}', 0, ji_inject_ts))
        ji_conn3.commit()
        ji_conn3.execute("PRAGMA ignore_check_constraints = OFF")
        ji_conn3.close()
        ji_ro3 = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        ji_leaf_bad = ji_ro3.execute(
            "SELECT COUNT(*) FROM water_windows,"
            " json_tree(water_windows.delta) jt"
            " WHERE jt.parent IS NOT NULL"
            " AND jt.type <> 'integer'").fetchone()[0]
        ji_leaf_wid, ji_leaf_type = ji_ro3.execute(
            "SELECT window_id, jt.type FROM water_windows,"
            " json_tree(water_windows.delta) jt"
            " WHERE jt.parent IS NOT NULL"
            " AND jt.type <> 'integer'").fetchone()
        ji_ro3.close()
        try:
            pipe.journal.cell_totals()
            ji_leaf_crash = None
        except (TypeError, ValueError) as exc:
            ji_leaf_crash = type(exc).__name__
        ji3_ok = (ji_leaf_bad == 1
                  and ji_leaf_type == "text"
                  and ji_leaf_crash is not None)

        ji_conn4 = sqlite3.connect(journal_db)
        ji_conn4.execute(
            "DELETE FROM water_windows WHERE window_id = ?",
            (ji_leaf_wid,))
        ji_conn4.commit()
        ji_conn4.close()

        # restore face: board back to 14 rows, integrity re-reads
        # green, product total back to the whole-board registered
        # value
        ji_ro4 = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        ji_rest_rows = ji_ro4.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        ji_rest_valid0 = ji_ro4.execute(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE json_valid(delta) <> 1").fetchone()[0]
        ji_rest_bad_leaves = ji_ro4.execute(
            "SELECT COUNT(*) FROM water_windows,"
            " json_tree(water_windows.delta) jt"
            " WHERE jt.parent IS NOT NULL"
            " AND jt.type <> 'integer'").fetchone()[0]
        ji_ro4.close()
        ji_rest_env = pipe.journal.cell_totals()
        ji4_ok = (ji_rest_rows == 14
                  and ji_rest_valid0 == 0
                  and ji_rest_bad_leaves == 0
                  and int(ji_rest_env["total"]) == 11)

        sections.append("[14] delta JSON engine-side integrity:")
        sections.append("    baseline: rows=%d valid0=%d"
                        " non-integer-leaves=%d leaf-count"
                        " tree=%d each=%d product=%d %s"
                        % (ji_base_rows, ji_base_valid0,
                           ji_base_bad_leaves, ji_tree_leaves,
                           ji_each_total, ji_product_leaves,
                           "OK" if ji1_ok else "DRIFT"))
        sections.append("    bad-json row: sql-valid0=%d"
                        " window_id=%d delta=%r product-crash=%s %s"
                        % (ji_bad_valid0, ji_bad_wid,
                           ji_bad_delta, ji_bad_crash,
                           "OK" if ji2_ok else "DRIFT"))
        sections.append("    non-integer leaf row: bad-leaves=%d"
                        " window_id=%d type=%s product-crash=%s %s"
                        % (ji_leaf_bad, ji_leaf_wid, ji_leaf_type,
                           ji_leaf_crash,
                           "OK" if ji3_ok else "DRIFT"))
        sections.append("    restore: rows=%d valid0=%d"
                        " non-integer-leaves=%d product-total=%d"
                        " %s"
                        % (ji_rest_rows, ji_rest_valid0,
                           ji_rest_bad_leaves,
                           int(ji_rest_env["total"]),
                           "OK" if ji4_ok else "DRIFT"))
        fail = fail or not (ji1_ok and ji2_ok and ji3_ok and ji4_ok)

        # ---- [15] per-row delta literal three-way + round-trip
        # conservation (R1818) ---------------------------------------
        # The [14] section enforced the structural premise; this
        # section pins the per-row literal plane on the clean 14-row
        # world. Three paths per row: the product board delta dict
        # (json.loads route, the reference), the SQL json_extract
        # per-key route (value equality + json_type 'integer' +
        # json_quote leaf-literal face - key-set closure rides the
        # [14] three-way leaf-count cross, not repeated), and the
        # SQL json(delta) re-parse route. Two literal laws: the
        # engine canonical text equals the product compact
        # serialization byte for byte, and the stored write-format
        # text is a fixed point of the writer's own serialization
        # law (record() rides json.dumps sort_keys=True with the
        # default separators). Negative injection faces stay in
        # [14] (in-book, not repeated).
        lc_ro = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        lc_cnt_before = lc_ro.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        lc_rows = lc_ro.execute(
            "SELECT window_id, delta, json(delta)"
            " FROM water_windows ORDER BY window_id").fetchall()
        board_map = {r["window_id"]: r["delta"]
                     for r in pipe.journal.journal_board()
                     ["journal_board"]}
        lc_three_ok = True
        lc_engine_ok = True
        lc_write_ok = True
        lc_key_face_total = 0
        lc_empty_rows = 0
        for wid, raw, canon in lc_rows:
            row_delta = board_map.get(wid)
            if not isinstance(row_delta, dict):
                lc_three_ok = False
                continue
            if not row_delta:
                lc_empty_rows += 1
            for key in sorted(row_delta):
                path = '$."' + key + '"'
                if '"' in key or "\\" in key:
                    lc_three_ok = False
                    continue
                val, jtype, quoted = lc_ro.execute(
                    "SELECT json_extract(delta, ?),"
                    " json_type(delta, ?),"
                    " json_quote(json_extract(delta, ?))"
                    " FROM water_windows WHERE window_id = ?",
                    (path, path, path, wid)).fetchone()
                if (val is None
                        or val != row_delta[key]
                        or jtype != "integer"
                        or quoted != json.dumps(row_delta[key])):
                    lc_three_ok = False
                lc_key_face_total += 1
            if json.loads(canon) != row_delta:
                lc_three_ok = False
            if canon != json.dumps(row_delta, sort_keys=True,
                                   separators=(",", ":")):
                lc_engine_ok = False
            if raw != json.dumps(json.loads(raw), sort_keys=True):
                lc_write_ok = False
        lc_cnt_after = lc_ro.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        lc_ro.close()
        lc1_ok = (len(lc_rows) == 14 and lc_three_ok)
        lc2_ok = lc_engine_ok
        lc3_ok = lc_write_ok
        lc4_ok = (lc_cnt_before == lc_cnt_after == 14
                  and set(board_map)
                  == set(wid for wid, _, _ in lc_rows))

        sections.append("[15] delta literal three-way + round-trip:")
        sections.append("    rows=%d keys-checked=%d"
                        " empty-delta-rows=%d"
                        % (len(lc_rows), lc_key_face_total,
                           lc_empty_rows))
        sections.append("    three-path per-row (extract/type/"
                        "quote + json() re-parse): %s"
                        % ("OK" if lc1_ok else "DRIFT"))
        sections.append("    engine-canonical == product-compact"
                        " (sort_keys, tight separators): %s"
                        % ("OK" if lc2_ok else "DRIFT"))
        sections.append("    write-format fixed point"
                        " (default-separator sort_keys): %s"
                        % ("OK" if lc3_ok else "DRIFT"))
        sections.append("    pure-read: rows %d==%d==14"
                        " board-map==sql-wids %s"
                        % (lc_cnt_before, lc_cnt_after,
                           "OK" if lc4_ok else "DRIFT"))
        fail = fail or not (lc1_ok and lc2_ok and lc3_ok
                            and lc4_ok)

        # ---- [16] ts_utc engine-side format integrity (R1819) ----
        # The [14]/[15] sections pinned the delta column; this
        # section pins the ts_utc column - the structural
        # premise of the month-window predicate substr(ts_utc,
        # 1,7) and the ORDER BY ts_utc sort key. Premise
        # correction, honest note: the seed said 26 chars; the
        # product record() rides strftime %f (always six-digit
        # microseconds), so the fixed length is 27 - the
        # judgment runs on 27 throughout (R1704 precedent).
        TZ_LEN = 27
        TZ_GLOB = ('[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                   'T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]'
                   '.[0-9][0-9][0-9][0-9][0-9][0-9]Z')

        def tz_format_faces(ro):
            rows = ro.execute(
                "SELECT COUNT(*) FROM water_windows").fetchone()[0]
            len_bad = ro.execute(
                "SELECT COUNT(*) FROM water_windows"
                " WHERE LENGTH(ts_utc) <> ?",
                (TZ_LEN,)).fetchone()[0]
            len_set = sorted({r[0] for r in ro.execute(
                "SELECT DISTINCT LENGTH(ts_utc)"
                " FROM water_windows")})
            glob_bad = ro.execute(
                "SELECT COUNT(*) FROM water_windows"
                " WHERE ts_utc NOT GLOB ?",
                (TZ_GLOB,)).fetchone()[0]
            jd_null = ro.execute(
                "SELECT COUNT(*) FROM water_windows"
                " WHERE julianday(ts_utc) IS NULL").fetchone()[0]
            jd_ok = ro.execute(
                "SELECT COUNT(*) FROM water_windows"
                " WHERE julianday(ts_utc) IS NOT NULL").fetchone()[0]
            return (rows, len_bad, len_set, glob_bad,
                    jd_null, jd_ok)

        def tz_month_faces(ro):
            sql_months = [r[0] for r in ro.execute(
                "SELECT DISTINCT substr(ts_utc, 1, 7)"
                " FROM water_windows ORDER BY 1")]
            flow_months = [r["month"] for r in
                           pipe.journal.monthly_flow()
                           ["monthly_flow"]]
            board_months = sorted({r["ts_utc"][:7] for r in
                                   pipe.journal.journal_board()
                                   ["journal_board"]})
            return sql_months, flow_months, board_months

        tz_ro = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        (tz_base_rows, tz_base_len_bad, tz_base_len_set,
         tz_base_glob_bad, tz_base_jd_null,
         tz_base_jd_ok) = tz_format_faces(tz_ro)
        tz1_ok = (tz_base_rows == 14
                  and tz_base_len_bad == 0
                  and tz_base_len_set == [27]
                  and tz_base_glob_bad == 0
                  and tz_base_jd_null == 0
                  and tz_base_jd_ok == 14)
        (tz_sql_months, tz_flow_months,
         tz_board_months) = tz_month_faces(tz_ro)
        # month-abstract expected set: the fixture month is a
        # hardcoded 2026-08 row face, the second member derives
        # from the live flow month (the R1813 abstraction law)
        tz_exp_months = sorted(set(["2026-08", cur_w]))
        tz2_ok = (tz_sql_months == tz_flow_months
                  == tz_board_months == tz_exp_months)
        tz_ro.close()

        # negative paths: the ts_utc column carries no CHECK
        # constraint and the kind rides inside the closed set -
        # a plain INSERT, no PRAGMA posture needed (honest
        # note); the ts derives from cur_w so both rows ride the
        # real flow month (the R1813 abstraction law)
        tz_n_pre = pipe.journal.journal_board(
            window=cur_w)["total"]
        tz_conn = sqlite3.connect(journal_db)
        tz_conn.execute(
            "INSERT INTO water_windows (kind, delta, total_delta,"
            " ts_utc) VALUES (?, ?, ?, ?)",
            ("submit", '{"noise.total":1}', 1,
             cur_w + "-1T00:00:00.000000Z"))
        tz_conn.execute(
            "INSERT INTO water_windows (kind, delta, total_delta,"
            " ts_utc) VALUES (?, ?, ?, ?)",
            ("submit", '{"noise.total":1}', 1,
             cur_w + "-99T99:99:99.999999Z"))
        tz_conn.commit()
        tz_conn.close()
        tz_ro2 = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        (tz_bad_rows, tz_bad_len_bad, tz_bad_len_set,
         tz_bad_glob_bad, tz_bad_jd_null,
         tz_bad_jd_ok) = tz_format_faces(tz_ro2)
        tz_len_wids = [r[0] for r in tz_ro2.execute(
            "SELECT window_id FROM water_windows"
            " WHERE LENGTH(ts_utc) <> ? ORDER BY window_id",
            (TZ_LEN,))]
        tz_glob_wids = [r[0] for r in tz_ro2.execute(
            "SELECT window_id FROM water_windows"
            " WHERE ts_utc NOT GLOB ? ORDER BY window_id",
            (TZ_GLOB,))]
        tz_jd_wids = [r[0] for r in tz_ro2.execute(
            "SELECT window_id FROM water_windows"
            " WHERE julianday(ts_utc) IS NULL"
            " ORDER BY window_id")]
        tz_ro2.close()
        # face independence: the bad-calendar row passes both
        # shape faces (length + GLOB) - the calendar face is its
        # sole detector
        tz_shape_wids = set(tz_len_wids) | set(tz_glob_wids)
        tz_b_only = [w for w in tz_jd_wids
                     if w not in tz_shape_wids]
        # product pure-prefix passthrough: the month predicate
        # validates nothing - both bad-ts rows still flow into
        # the current-month window (the premise-enforcement
        # honest note; the enforcement face lives on this probe)
        tz_n_post = pipe.journal.journal_board(
            window=cur_w)["total"]
        tz_flow_windows_post = pipe.journal.monthly_flow(
            window=cur_w)["monthly_flow"][0]["windows"]
        tz3_ok = (tz_bad_rows == 16
                  and tz_bad_len_bad == 1
                  and tz_bad_glob_bad == 1
                  and tz_bad_jd_null == 2
                  and tz_len_wids == tz_glob_wids
                  and len(tz_b_only) == 1
                  and tz_n_pre == 11
                  and tz_n_post == 13
                  and tz_flow_windows_post == 13)

        # restore: both rows removed by window_id, every face
        # back to green, the month-set cross back to the
        # baseline set, the product total back to the
        # registered whole-board value
        tz_conn2 = sqlite3.connect(journal_db)
        for wid in tz_jd_wids:
            tz_conn2.execute(
                "DELETE FROM water_windows WHERE window_id = ?",
                (wid,))
        tz_conn2.commit()
        tz_conn2.close()
        tz_ro3 = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        (tz_rest_rows, tz_rest_len_bad, tz_rest_len_set,
         tz_rest_glob_bad, tz_rest_jd_null,
         tz_rest_jd_ok) = tz_format_faces(tz_ro3)
        tz_rest_months = tz_month_faces(tz_ro3)
        tz_ro3.close()
        tz_rest_total = int(
            pipe.journal.cell_totals()["total"])
        tz4_ok = (tz_rest_rows == 14
                  and tz_rest_len_bad == 0
                  and tz_rest_len_set == [27]
                  and tz_rest_glob_bad == 0
                  and tz_rest_jd_null == 0
                  and tz_rest_jd_ok == 14
                  and tz_rest_months[0] == tz_rest_months[1]
                  == tz_rest_months[2] == tz_exp_months
                  and tz_rest_total == 11)

        sections.append("[16] ts_utc engine-side format"
                        " integrity:")
        sections.append("    baseline: rows=%d len-bad=%d"
                        " len-set=%s glob-bad=%d jd-null=%d"
                        " jd-ok=%d %s"
                        % (tz_base_rows, tz_base_len_bad,
                           tz_base_len_set, tz_base_glob_bad,
                           tz_base_jd_null, tz_base_jd_ok,
                           "OK" if tz1_ok else "DRIFT"))
        sections.append("    month-set three-face: sql=%s"
                        " flow=%s board=%s %s"
                        % (tz_sql_months, tz_flow_months,
                           tz_board_months,
                           "OK" if tz2_ok else "DRIFT"))
        sections.append("    tampered: rows=%d len-bad=%d"
                        " glob-bad=%d jd-null=%d len-wids=%s"
                        " glob-wids=%s jd-wids=%s"
                        " calendar-only=%s %s"
                        % (tz_bad_rows, tz_bad_len_bad,
                           tz_bad_glob_bad, tz_bad_jd_null,
                           tz_len_wids, tz_glob_wids,
                           tz_jd_wids, tz_b_only,
                           "OK" if tz3_ok else "DRIFT"))
        sections.append("    prefix-passthrough (product month"
                        " predicate validates nothing):"
                        " board(cur) %d->%d flow-windows=%d %s"
                        % (tz_n_pre, tz_n_post,
                           tz_flow_windows_post,
                           "OK" if (tz_n_post == 13
                                    and tz_flow_windows_post
                                    == 13) else "DRIFT"))
        sections.append("    restore: rows=%d len-bad=%d"
                        " glob-bad=%d jd-null=%d months=%s"
                        " product-total=%d %s"
                        % (tz_rest_rows, tz_rest_len_bad,
                           tz_rest_glob_bad, tz_rest_jd_null,
                           tz_rest_months[0], tz_rest_total,
                           "OK" if tz4_ok else "DRIFT"))
        fail = fail or not (tz1_ok and tz2_ok and tz3_ok
                            and tz4_ok)

        # ---- [17] ts lexicographic == chronological total
        # order (R1820) ---------------------------------------
        # The [16] section pinned the fixed 27-char shape; this
        # section pins the sort-key semantics the board reads
        # lean on: over a well-formed world the text order
        # equals the chronological order row by row (the
        # fixed-length ISO form makes ORDER BY ts_utc a total
        # chronological order), the product board read (ORDER BY
        # ts_utc DESC, window_id DESC, reversed to ascending)
        # carries the same sequence, and a ts tie falls to the
        # window_id tiebreak - drift (kind submit, injected in
        # [4]) before ghost (legacy-ghost, injected in [7]),
        # the [10] in-register order. Negative path: one
        # bad-calendar row (27 chars, GLOB passes, julianday
        # NULL - the [16] B shape, month-abstract ts) is an
        # incomparable key: the chronological order is no
        # longer total (SQLite floats the NULL row first in
        # ASC), while the text order stays total - a valid
        # hour starts with 0/1/2, the -99T hour starts with 9,
        # so the bad row always sorts last in ascending text
        # order (a constructive position, wall-clock
        # independent), and the product read places it last -
        # the pure text order does not depend on parseability
        # (honest note; the enforcement face lives on this
        # probe). DELETE restore by window_id, every face back
        # to the 14-row registered values.

        def lo_lex_seq(ro):
            return [r[0] for r in ro.execute(
                "SELECT ts_utc FROM water_windows"
                " ORDER BY ts_utc, window_id")]

        def lo_jd_seq(ro):
            return [r[0] for r in ro.execute(
                "SELECT ts_utc FROM water_windows"
                " WHERE julianday(ts_utc) IS NOT NULL"
                " ORDER BY julianday(ts_utc), window_id")]

        def lo_jd_seq_all(ro):
            return [r[0] for r in ro.execute(
                "SELECT ts_utc FROM water_windows"
                " ORDER BY julianday(ts_utc), window_id")]

        lo_ro = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        lo_lex = lo_lex_seq(lo_ro)
        lo_jd = lo_jd_seq(lo_ro)
        lo_prod = [r["ts_utc"] for r in
                   pipe.journal.journal_board()["journal_board"]]
        lo1_ok = (len(lo_lex) == 14 and len(lo_jd) == 14
                  and lo_lex == lo_jd and lo_prod == lo_lex)

        # tie window: the drift/ghost pair shares one ts; the
        # product order falls to the window_id tiebreak
        lo_tie_ts = drift_w + "-11T00:00:00.000000Z"
        lo_board_full = pipe.journal.journal_board()[
            "journal_board"]
        lo_tie_ids_prod = [r["window_id"] for r in lo_board_full
                           if r["ts_utc"] == lo_tie_ts]
        lo_tie_kinds = [r["kind"] for r in lo_board_full
                        if r["ts_utc"] == lo_tie_ts]
        lo_tie_ids_sql = [r[0] for r in lo_ro.execute(
            "SELECT window_id FROM water_windows"
            " WHERE ts_utc = ? ORDER BY window_id",
            (lo_tie_ts,))]
        lo_drift_pos = lo_prod.index(lo_tie_ts)
        lo2_ok = (len(lo_tie_ids_prod) == 2
                  and lo_tie_ids_prod == lo_tie_ids_sql
                  == sorted(lo_tie_ids_prod)
                  and lo_tie_kinds == ["submit", "legacy-ghost"]
                  and lo_prod[lo_drift_pos + 1] == lo_tie_ts
                  and drift_w == cur_w)

        # negative path: inject the [16] B-shape bad-calendar
        # row (27 chars, GLOB passes, julianday NULL)
        lo_bad_ts = cur_w + "-99T99:99:99.999999Z"
        lo_pre_total = pipe.journal.journal_board(
            window=cur_w)["total"]
        lo_conn = sqlite3.connect(journal_db)
        lo_conn.execute(
            "INSERT INTO water_windows (kind, delta, total_delta,"
            " ts_utc) VALUES (?, ?, ?, ?)",
            ("submit", '{"noise.total":1}', 1, lo_bad_ts))
        lo_conn.commit()
        lo_bad_wid = lo_conn.execute(
            "SELECT window_id FROM water_windows"
            " WHERE ts_utc = ?", (lo_bad_ts,)).fetchone()[0]
        lo_conn.close()
        lo_ro2 = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        lo_lex2 = lo_lex_seq(lo_ro2)
        lo_jd2 = lo_jd_seq(lo_ro2)
        lo_jd_all2 = lo_jd_seq_all(lo_ro2)
        lo_prod2 = [r["ts_utc"] for r in
                    pipe.journal.journal_board()["journal_board"]]
        lo_valid_n = lo_ro2.execute(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE julianday(ts_utc) IS NOT NULL").fetchone()[0]
        lo_null_n = lo_ro2.execute(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE julianday(ts_utc) IS NULL").fetchone()[0]
        lo_post_total = pipe.journal.journal_board(
            window=cur_w)["total"]
        lo3_ok = (len(lo_lex2) == 15
                  and lo_lex2 == lo_lex + [lo_bad_ts]
                  and lo_prod2 == lo_lex2
                  and lo_prod2[-1] == lo_bad_ts
                  and len(lo_jd2) == 14 and lo_jd2 == lo_jd
                  and len(lo_jd_all2) == 15
                  and lo_jd_all2[0] == lo_bad_ts
                  and lo_valid_n == 14 and lo_null_n == 1
                  and lo_pre_total == 11 and lo_post_total == 12)
        lo_ro2.close()

        # restore: the bad row removed by window_id, every
        # face back to the 14-row registered values
        lo_conn2 = sqlite3.connect(journal_db)
        lo_conn2.execute(
            "DELETE FROM water_windows WHERE window_id = ?",
            (lo_bad_wid,))
        lo_conn2.commit()
        lo_conn2.close()
        lo_ro3 = sqlite3.connect(
            "file:" + journal_db.replace(os.sep, "/") + "?mode=ro",
            uri=True)
        lo_lex3 = lo_lex_seq(lo_ro3)
        lo_jd3 = lo_jd_seq(lo_ro3)
        lo_prod3 = [r["ts_utc"] for r in
                    pipe.journal.journal_board()["journal_board"]]
        lo_ro3.close()
        lo_ro.close()
        lo_rest_total = int(
            pipe.journal.cell_totals()["total"])
        lo4_ok = (len(lo_lex3) == 14 and lo_lex3 == lo_lex
                  and lo_jd3 == lo_jd and lo_prod3 == lo_lex3
                  and lo_rest_total == 11)

        sections.append("[17] ts lexicographic =="
                        " chronological total order:")
        sections.append("    clean-world: rows=%d lex==jd=%s"
                        " prod==lex=%s %s"
                        % (len(lo_lex), lo_lex == lo_jd,
                           lo_prod == lo_lex,
                           "OK" if lo1_ok else "DRIFT"))
        sections.append("    tie window: drift-pos=%d ids=%s"
                        " kinds=%s adjacent=%s %s"
                        % (lo_drift_pos, lo_tie_ids_prod,
                           lo_tie_kinds,
                           lo_prod[lo_drift_pos + 1] == lo_tie_ts,
                           "OK" if lo2_ok else "DRIFT"))
        sections.append("    tampered: rows=%d bad-wid=%d"
                        " bad-last=%s jd-valid=%d jd-null=%d"
                        " jd-first-is-bad=%s board(cur) %d->%d %s"
                        % (len(lo_lex2), lo_bad_wid,
                           lo_prod2[-1] == lo_bad_ts,
                           lo_valid_n, lo_null_n,
                           lo_jd_all2[0] == lo_bad_ts,
                           lo_pre_total, lo_post_total,
                           "OK" if lo3_ok else "DRIFT"))
        sections.append("    restore: rows=%d lex==jd=%s"
                        " prod==lex=%s total=%d %s"
                        % (len(lo_lex3), lo_lex3 == lo_jd3,
                           lo_prod3 == lo_lex3, lo_rest_total,
                           "OK" if lo4_ok else "DRIFT"))
        fail = fail or not (lo1_ok and lo2_ok and lo3_ok
                            and lo4_ok)

        # ---- [18] kind CHECK constraint engine-side enforcement
        # (R1821) ----------------------------------------------
        # The [7] ghost injection rode PRAGMA
        # ignore_check_constraints - indirect evidence the kind
        # column CHECK exists. This section proves the constraint
        # body face on the engine: a default-posture out-of-domain
        # kind plain INSERT raises sqlite3.IntegrityError carrying
        # the CHECK message and lands zero rows; the pragma switch
        # is a reversible dual state (ON lands the very same
        # INSERT, OFF on the same connection restores the rejection
        # of a second out-of-domain kind); and the positive closed
        # set holds - all five legal kinds INSERT cleanly, so the
        # constraint is exactly the closed set, never
        # over-restrictive. Positive rows carry an empty delta and
        # total_delta 0 (the value faces stay untouched while the
        # count faces move: kind_tally(cur_w) gains +1 per legal
        # kind). DELETE restore by window_id: the row count returns
        # to 14, cell_totals total returns to the registered 11,
        # and the whole-board and current-window tallies return to
        # their pre-injection dicts - the R1820 world state intact.

        ck_bad_kind = "check-probe-kind"

        def ck_ro_scalar(sql, args=()):
            ck_ro = sqlite3.connect(
                "file:" + journal_db.replace(os.sep, "/")
                + "?mode=ro", uri=True)
            val = ck_ro.execute(sql, args).fetchone()[0]
            ck_ro.close()
            return val

        ck_pre_n = ck_ro_scalar(
            "SELECT COUNT(*) FROM water_windows")
        ck_tally_pre_all = pipe.journal.kind_tally()[
            "kind_tally"]
        ck_tally_pre_cur = pipe.journal.kind_tally(
            window=cur_w)["kind_tally"]

        # AC-CK1: default posture rejects, zero rows landed
        ck_exc1 = None
        ck_msg1 = None
        ck_conn1 = sqlite3.connect(journal_db)
        try:
            ck_conn1.execute(
                "INSERT INTO water_windows (kind, delta,"
                " total_delta, ts_utc) VALUES (?, ?, ?, ?)",
                (ck_bad_kind, "{}", 0,
                 cur_w + "-21T00:00:00.000000Z"))
            ck_conn1.commit()
        except sqlite3.IntegrityError as exc:
            ck_exc1 = type(exc).__name__
            ck_msg1 = str(exc)
        ck_conn1.close()
        ck_bad_n = ck_ro_scalar(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE kind = ?", (ck_bad_kind,))
        ck_msg_hit1 = (isinstance(ck_msg1, str)
                       and "CHECK constraint failed" in ck_msg1
                       and "kind IN" in ck_msg1)
        ck1_ok = (ck_exc1 == "IntegrityError"
                  and ck_msg_hit1 and ck_bad_n == 0
                  and ck_ro_scalar(
                      "SELECT COUNT(*) FROM water_windows")
                  == ck_pre_n == 14)

        # AC-CK2: pragma switch dual state and reversibility
        ck_conn2 = sqlite3.connect(journal_db)
        ck_conn2.execute("PRAGMA ignore_check_constraints = ON")
        ck_conn2.execute(
            "INSERT INTO water_windows (kind, delta,"
            " total_delta, ts_utc) VALUES (?, ?, ?, ?)",
            (ck_bad_kind, "{}", 0,
             cur_w + "-21T00:00:00.000000Z"))
        ck_conn2.commit()
        ck_on_wid = ck_conn2.execute(
            "SELECT window_id FROM water_windows"
            " WHERE kind = ?", (ck_bad_kind,)).fetchone()[0]
        ck_conn2.execute("PRAGMA ignore_check_constraints = OFF")
        ck_exc2 = None
        ck_msg2 = None
        try:
            ck_conn2.execute(
                "INSERT INTO water_windows (kind, delta,"
                " total_delta, ts_utc) VALUES (?, ?, ?, ?)",
                ("check-probe-kind-2", "{}", 0,
                 cur_w + "-21T00:00:00.000000Z"))
            ck_conn2.commit()
        except sqlite3.IntegrityError as exc:
            ck_exc2 = type(exc).__name__
            ck_msg2 = str(exc)
        ck_conn2.close()
        ck_on_n = ck_ro_scalar(
            "SELECT COUNT(*) FROM water_windows")
        ck_bad2_n = ck_ro_scalar(
            "SELECT COUNT(*) FROM water_windows"
            " WHERE kind = 'check-probe-kind-2'")
        ck_tally_mid = pipe.journal.kind_tally(
            window=cur_w)["kind_tally"]
        ck_msg_hit2 = (isinstance(ck_msg2, str)
                       and "CHECK constraint failed" in ck_msg2
                       and "kind IN" in ck_msg2)
        ck2_ok = (ck_on_wid is not None
                  and ck_on_n == ck_pre_n + 1
                  and ck_exc2 == "IntegrityError"
                  and ck_msg_hit2 and ck_bad2_n == 0
                  and ck_tally_mid.get(ck_bad_kind) == 1)

        # AC-CK3: positive closed set - the five legal kinds all
        # pass; the count faces follow each kind +1 (baseline =
        # the post-CK2 state, whose switched row stays visible
        # as an appended tally key - the R1801 never-hide law;
        # the pre-registered 11->16 arithmetic missed the CK2
        # row landing in the same month - honest correction,
        # 12+5=17 with the appended key in evidence)
        ck_pos_wids = []
        ck_conn3 = sqlite3.connect(journal_db)
        for ck_k in ("ingest", "batch", "drain", "submit",
                     "verdict"):
            ck_cur = ck_conn3.execute(
                "INSERT INTO water_windows (kind, delta,"
                " total_delta, ts_utc) VALUES (?, ?, ?, ?)",
                (ck_k, "{}", 0,
                 cur_w + "-21T00:00:00.000000Z"))
            ck_conn3.commit()
            ck_pos_wids.append(ck_cur.lastrowid)
        ck_conn3.close()
        ck_tally_post_env = pipe.journal.kind_tally(
            window=cur_w)
        ck_tally_post = ck_tally_post_env["kind_tally"]
        ck_want = {}
        for ck_k in ck_tally_mid:
            ck_want[ck_k] = ck_tally_mid[ck_k] + (
                1 if ck_k in ("ingest", "batch", "drain",
                              "submit", "verdict") else 0)
        ck3_ok = (ck_tally_post == ck_want
                  and ck_tally_post_env["total"]
                  == sum(ck_want.values()) == 17
                  and len(ck_pos_wids) == 5
                  and ck_ro_scalar(
                      "SELECT COUNT(*) FROM water_windows")
                  == ck_pre_n + 6)

        # AC-CK4: DELETE restore - the R1820 world state intact
        ck_conn4 = sqlite3.connect(journal_db)
        for ck_wid in [ck_on_wid] + list(ck_pos_wids):
            ck_conn4.execute(
                "DELETE FROM water_windows WHERE window_id = ?",
                (ck_wid,))
        ck_conn4.commit()
        ck_conn4.close()
        ck_rest_n = ck_ro_scalar(
            "SELECT COUNT(*) FROM water_windows")
        ck_rest_total = int(
            pipe.journal.cell_totals()["total"])
        ck_rest_tally_all = pipe.journal.kind_tally()[
            "kind_tally"]
        ck_rest_tally_cur = pipe.journal.kind_tally(
            window=cur_w)["kind_tally"]
        ck4_ok = (ck_rest_n == ck_pre_n
                  and pipe.journal.journal_board()["total"]
                  == ck_pre_n
                  and ck_rest_total == 11
                  and ck_rest_tally_all == ck_tally_pre_all
                  and ck_rest_tally_cur == ck_tally_pre_cur)

        sections.append("[18] kind CHECK enforcement:")
        sections.append("    default-reject: exc=%s msg-hit=%s"
                        " rows=%d bad-rows=%d %s"
                        % (ck_exc1, ck_msg_hit1, ck_pre_n,
                           ck_bad_n,
                           "OK" if ck1_ok else "DRIFT"))
        sections.append("    pragma-dual-state: on-wid=%d"
                        " rows=%d off-exc=%s off-rows=%d"
                        " tally-vis=%s %s"
                        % (ck_on_wid, ck_on_n, ck_exc2,
                           ck_bad2_n,
                           ck_tally_mid.get(ck_bad_kind),
                           "OK" if ck2_ok else "DRIFT"))
        sections.append("    positive-closed-set: wids=%s"
                        " tally-follow=%s total=%d %s"
                        % (ck_pos_wids,
                           ck_tally_post == ck_want,
                           ck_tally_post_env["total"],
                           "OK" if ck3_ok else "DRIFT"))
        sections.append("    restore: rows=%d total=%d"
                        " tally-all-ok=%s tally-cur-ok=%s %s"
                        % (ck_rest_n, ck_rest_total,
                           ck_rest_tally_all == ck_tally_pre_all,
                           ck_rest_tally_cur == ck_tally_pre_cur,
                           "OK" if ck4_ok else "DRIFT"))
        fail = fail or not (ck1_ok and ck2_ok and ck3_ok
                            and ck4_ok)

        # ---- [19] kind CHECK constraint schema-text readback
        # (R1822) ------------------------------------------------
        # The [18] section proved the constraint behaviorally
        # (IntegrityError / pragma dual state / positive closed
        # set); this section reads the constraint body text face.
        # The engine archives the executed CREATE TABLE statement
        # in sqlite_master; the readback rides a mode=ro
        # connection (the [18] ck_ro_scalar law). The engine
        # normalization is verified empirically (R1822 pre-check):
        # the stored sql is the product WJ.SCHEMA constant with
        # the "IF NOT EXISTS " marker, outer whitespace and the
        # trailing semicolon stripped - byte-identical otherwise,
        # so the module constant the constructor executes is the
        # very text the engine archived (single source of truth).
        # The honest table-set reading lists sqlite_sequence too
        # (the AUTOINCREMENT bookkeeping table, not a product
        # table - read, not filtered). PRAGMA table_info pins the
        # five-column metadata (kind TEXT NOT NULL non-pk,
        # window_id INTEGER pk). Pure readback: zero injections,
        # zero deletes, the row count stays 14 throughout.

        def sk_ro_rows(sql, args=()):
            sk_ro = sqlite3.connect(
                "file:" + journal_db.replace(os.sep, "/")
                + "?mode=ro", uri=True)
            got = list(sk_ro.execute(sql, args))
            sk_ro.close()
            return got

        sk_pre_n = sk_ro_rows(
            "SELECT COUNT(*) FROM water_windows")[0][0]
        sk_name_rows = sk_ro_rows(
            "SELECT name, sql FROM sqlite_master"
            " WHERE type='table' AND name='water_windows'")
        sk_table_set = [r[0] for r in sk_ro_rows(
            "SELECT name FROM sqlite_master"
            " WHERE type='table' ORDER BY name")]
        # AC-SK1: exactly one water_windows row, name located,
        # sql non-empty; honest table set includes the
        # AUTOINCREMENT bookkeeping table.
        sk1_ok = (len(sk_name_rows) == 1
                  and sk_name_rows[0][0] == "water_windows"
                  and isinstance(sk_name_rows[0][1], str)
                  and sk_name_rows[0][1].strip() != ""
                  and sk_table_set == ["sqlite_sequence",
                                       "water_windows"])

        # AC-SK2: CHECK clause verbatim + each of the five kind
        # values present in the constraint body text.
        sk_sql = sk_name_rows[0][1]
        sk_clause = ("CHECK (kind IN "
                     "('ingest','batch','drain','submit',"
                     "'verdict'))")
        sk_values = ("'ingest'", "'batch'", "'drain'",
                     "'submit'", "'verdict'")
        sk_hits = {v: sk_sql.count(v) for v in sk_values}
        sk2_ok = ("CHECK" in sk_sql and "kind IN" in sk_sql
                  and sk_clause in sk_sql
                  and all(n >= 1 for n in sk_hits.values()))

        # AC-SK3: product-source identity - the engine-stored
        # statement equals the module constant after the
        # verified normalization (strip marker + outer ws +
        # trailing semicolon).
        sk_norm = (WJ.SCHEMA.replace("IF NOT EXISTS ", "")
                   .strip().rstrip(";"))
        sk3_ok = (sk_sql == sk_norm
                  and sk_clause in WJ.SCHEMA)

        # AC-SK4: five-column metadata pinned row by row.
        sk_info = sk_ro_rows(
            "PRAGMA table_info(water_windows)")
        sk_want_info = [
            (0, "window_id", "INTEGER", 0, None, 1),
            (1, "kind", "TEXT", 1, None, 0),
            (2, "delta", "TEXT", 1, None, 0),
            (3, "total_delta", "INTEGER", 1, None, 0),
            (4, "ts_utc", "TEXT", 1, None, 0)]
        sk_kind_row = [r for r in sk_info if r[1] == "kind"]
        sk4_ok = (len(sk_info) == 5
                  and sk_info == sk_want_info
                  and len(sk_kind_row) == 1
                  and sk_kind_row[0][2] == "TEXT"
                  and sk_kind_row[0][3] == 1
                  and sk_kind_row[0][5] == 0)

        # AC-SK5: pure-read law - the row count never moved.
        sk_post_n = sk_ro_rows(
            "SELECT COUNT(*) FROM water_windows")[0][0]
        sk5_ok = (sk_pre_n == 14 and sk_post_n == 14)

        sections.append("[19] schema text readback:")
        sections.append("    table-locate: rows=%d name=%s"
                        " table-set=%s %s"
                        % (len(sk_name_rows),
                           sk_name_rows[0][0] if sk_name_rows
                           else None, sk_table_set,
                           "OK" if sk1_ok else "DRIFT"))
        sections.append("    check-clause: verbatim=%s hits=%s %s"
                        % (sk_clause in sk_sql, sk_hits,
                           "OK" if sk2_ok else "DRIFT"))
        sections.append("    product-source: norm-eq=%s %s"
                        % (sk_sql == sk_norm,
                           "OK" if sk3_ok else "DRIFT"))
        sections.append("    table-info: rows=%d kind-row=%s %s"
                        % (len(sk_info), sk_kind_row,
                           "OK" if sk4_ok else "DRIFT"))
        sections.append("    pure-read: rows=%d->%d %s"
                        % (sk_pre_n, sk_post_n,
                           "OK" if sk5_ok else "DRIFT"))
        fail = fail or not (sk1_ok and sk2_ok and sk3_ok
                            and sk4_ok and sk5_ok)

        # ---- [20] sqlite_sequence AUTOINCREMENT high-water
        # bookkeeping readback (R1823; AC-HW1..HW5) --------------
        # The [19] honest table set already lists sqlite_sequence
        # (the AUTOINCREMENT bookkeeping table); this section reads
        # its body. The ever-max assigned id (seq) is a structural
        # constant of this probe world: ids 1..25 were all assigned
        # in operation order (nine real windows, drift row 10,
        # three fixture rows 11..13, ghost row 14, then the
        # inject-then-delete rounds consumed 15..25), so at the
        # [19] end state seq is 25 while the live MAX(window_id)
        # is 14 - the no-reuse guarantee read directly (deleted
        # ids never return). Engine semantics pinned empirically
        # before this section landed (R1704 law; hw_precheck,
        # SQLite 3.50.4: high-water never retreats across deletes,
        # a fresh insert consumes seq+1). The consume-and-restore
        # round: a fresh closed-set INSERT (delta '{}',
        # total_delta 0 - value faces untouched, count face moves)
        # consumes seq+1 == 26 and advances the bookkeeping row;
        # deleting it returns the 14-row world, product faces back
        # at their registered dicts, while seq stays at 26 - the
        # high-water never retreats.

        def hw_ro_rows(sql, args=()):
            hw_ro = sqlite3.connect(
                "file:" + journal_db.replace(os.sep, "/")
                + "?mode=ro", uri=True)
            got = list(hw_ro.execute(sql, args))
            hw_ro.close()
            return got

        hw_pre_n = hw_ro_rows(
            "SELECT COUNT(*) FROM water_windows")[0][0]
        hw_seq_rows = hw_ro_rows(
            "SELECT name, seq FROM sqlite_sequence")
        hw_max_id = hw_ro_rows(
            "SELECT MAX(window_id) FROM water_windows")[0][0]
        HW_SEQ_CONST = 25
        # AC-HW1: exactly one bookkeeping row, right name, int seq.
        hw1_ok = (len(hw_seq_rows) == 1
                  and hw_seq_rows[0][0] == "water_windows"
                  and isinstance(hw_seq_rows[0][1], int))
        hw_seq = hw_seq_rows[0][1] if hw_seq_rows else None
        # AC-HW2: high-water vs live max - ever-max 25 > live 14.
        hw2_ok = (hw_seq == HW_SEQ_CONST and hw_max_id == 14
                  and hw_seq > hw_max_id)

        # product faces before the consume-restore round
        hw_tally_pre = dict(
            pipe.journal.kind_tally()["kind_tally"])
        hw_tally_cur_pre = dict(
            pipe.journal.kind_tally(cur_w)["kind_tally"])
        hw_total_pre = pipe.journal.cell_totals()["total"]

        # AC-HW3: fresh closed-set INSERT consumes seq+1 == 26 and
        # advances the bookkeeping row to 26 (ts month-derived from
        # cur_w, R1813 law; -22T avoids the deleted -11T/-21T
        # slots - same-clock legality per R1821 note).
        hw_conn = sqlite3.connect(journal_db)
        hw_conn.execute(
            "INSERT INTO water_windows (kind, delta,"
            " total_delta, ts_utc) VALUES ('submit', '{}',"
            " 0, ?)",
            (cur_w + "-22T00:00:00.000000Z",))
        hw_new_id = hw_conn.execute(
            "SELECT last_insert_rowid()").fetchone()[0]
        hw_seq_mid = hw_conn.execute(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        hw_conn.commit()
        hw3_ok = (hw_new_id == HW_SEQ_CONST + 1
                  and hw_seq_mid == HW_SEQ_CONST + 1)

        # AC-HW4: delete by window_id - the 14-row world returns,
        # product faces return to the registered dicts, while seq
        # stays at 26 (high-water never retreats).
        hw_conn.execute(
            "DELETE FROM water_windows WHERE window_id = ?",
            (hw_new_id,))
        hw_conn.commit()
        hw_post_n = hw_conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        hw_seq_post = hw_conn.execute(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        hw_conn.close()
        hw_tally_post = dict(
            pipe.journal.kind_tally()["kind_tally"])
        hw_tally_cur_post = dict(
            pipe.journal.kind_tally(cur_w)["kind_tally"])
        hw_total_post = pipe.journal.cell_totals()["total"]
        hw4_ok = (hw_post_n == 14
                  and hw_seq_post == HW_SEQ_CONST + 1
                  and hw_tally_post == hw_tally_pre
                  and hw_tally_cur_post == hw_tally_cur_pre
                  and hw_total_post == hw_total_pre)

        # AC-HW5: pure-read law on the readback face - the row
        # count never moved across the ro reads; the [1]..[19]
        # zero-regression rides the whole-probe verdict.
        hw_post_n_ro = hw_ro_rows(
            "SELECT COUNT(*) FROM water_windows")[0][0]
        hw5_ok = (hw_pre_n == 14 and hw_post_n_ro == 14)

        sections.append("[20] sqlite_sequence high-water readback:")
        sections.append("    bookkeeping-row: rows=%d name=%s"
                        " seq=%s %s"
                        % (len(hw_seq_rows),
                           hw_seq_rows[0][0] if hw_seq_rows
                           else None, hw_seq,
                           "OK" if hw1_ok else "DRIFT"))
        sections.append("    high-water-vs-live: seq=%s max-id=%s"
                        " no-reuse=%s %s"
                        % (hw_seq, hw_max_id,
                           hw_seq > hw_max_id,
                           "OK" if hw2_ok else "DRIFT"))
        sections.append("    consume: new-id=%d seq-mid=%d %s"
                        % (hw_new_id, hw_seq_mid,
                           "OK" if hw3_ok else "DRIFT"))
        sections.append("    restore-no-retreat: rows=%d seq=%d"
                        " total=%s tallies-eq=%s %s"
                        % (hw_post_n, hw_seq_post, hw_total_post,
                           hw_tally_post == hw_tally_pre
                           and hw_tally_cur_post == hw_tally_cur_pre,
                           "OK" if hw4_ok else "DRIFT"))
        sections.append("    pure-read: rows=%d->%d %s"
                        % (hw_pre_n, hw_post_n_ro,
                           "OK" if hw5_ok else "DRIFT"))
        fail = fail or not (hw1_ok and hw2_ok and hw3_ok
                            and hw4_ok and hw5_ok)

        # ---- [21] sqlite_sequence bookkeeping tamper
        # id-reuse negative path (R1832; AC-TP1..TP5) ---------
        # The [20] section read the high-water bookkeeping row
        # as the no-reuse guarantee. This section proves the
        # guarantee's single point of dependence: SQLite allows
        # a direct UPDATE on the sqlite_sequence row and the
        # bookkeeping table carries no constraint protecting it.
        # Rolling seq back to 0 while deleted ids 15..26 sit
        # above the live max breaks the guarantee - the next
        # INSERT allocates max(seq, live max)+1 == 15, the id of
        # a row that was already used and deleted ([20] census).
        # Engine semantics pinned empirically before this
        # section landed (R1704 law; tp_precheck, SQLite 3.50.4).
        # The tamper-reuse-restore round: rollback, prove the
        # reused id surfaces in the product count faces (value
        # faces untouched: delta '{}', total_delta 0), restore
        # the high-water 26, then delete the reused row - the
        # 14-row world returns while seq stays at 26 (deletion
        # never touches the bookkeeping row, [20] AC-HW4 law).

        def tp_ro_scalar(sql, args=()):
            tp_ro = sqlite3.connect(
                "file:" + journal_db.replace(os.sep, "/")
                + "?mode=ro", uri=True)
            got = tp_ro.execute(sql, args).fetchone()
            tp_ro.close()
            return got[0] if got else None

        tp_pre_n = tp_ro_scalar(
            "SELECT COUNT(*) FROM water_windows")
        tp_seq_pre = tp_ro_scalar(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'")
        # product faces before the tamper round
        tp_tally_pre = dict(
            pipe.journal.kind_tally()["kind_tally"])
        tp_tally_cur_pre = dict(
            pipe.journal.kind_tally(cur_w)["kind_tally"])
        tp_total_pre = pipe.journal.cell_totals()["total"]
        tp_board_cur_pre = pipe.journal.journal_board(
            cur_w)["total"]

        # AC-TP1: bookkeeping row is writable - rollback to 0
        tp_conn = sqlite3.connect(journal_db)
        tp_conn.execute(
            "UPDATE sqlite_sequence SET seq = 0"
            " WHERE name = 'water_windows'")
        tp_conn.commit()
        tp_seq_zero = tp_conn.execute(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        tp_rows_zero = tp_conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        tp_total_zero = pipe.journal.cell_totals()["total"]
        tp1_ok = (tp_seq_pre == 26 and tp_seq_zero == 0
                  and tp_rows_zero == 14
                  and tp_total_zero == tp_total_pre)

        # AC-TP2: id reuse - fresh INSERT reuses deleted id 15
        tp_conn.execute(
            "INSERT INTO water_windows (kind, delta,"
            " total_delta, ts_utc) VALUES ('submit', '{}',"
            " 0, ?)",
            (cur_w + "-23T00:00:00.000000Z",))
        tp_reuse_id = tp_conn.execute(
            "SELECT last_insert_rowid()").fetchone()[0]
        tp_seq_mid = tp_conn.execute(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        tp_conn.commit()
        tp_rows_mid = tp_conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        tp_board_cur_mid = pipe.journal.journal_board(
            cur_w)["total"]
        tp2_ok = (tp_reuse_id == 15 and tp_seq_mid == 15
                  and tp_rows_mid == 15
                  and tp_board_cur_mid == tp_board_cur_pre + 1)

        # AC-TP3: restore the bookkeeping high-water 26
        tp_conn.execute(
            "UPDATE sqlite_sequence SET seq = 26"
            " WHERE name = 'water_windows'")
        tp_conn.commit()
        tp_seq_restored = tp_conn.execute(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        tp_rows_restored = tp_conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        tp3_ok = (tp_seq_restored == 26
                  and tp_rows_restored == 15)

        # AC-TP4: world re-green - delete the reused row
        tp_conn.execute(
            "DELETE FROM water_windows"
            " WHERE window_id = ?", (tp_reuse_id,))
        tp_conn.commit()
        tp_rows_post = tp_conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        tp_seq_final = tp_conn.execute(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        tp_conn.close()
        tp_tally_post = dict(
            pipe.journal.kind_tally()["kind_tally"])
        tp_tally_cur_post = dict(
            pipe.journal.kind_tally(cur_w)["kind_tally"])
        tp_total_post = pipe.journal.cell_totals()["total"]
        tp_board_cur_post = pipe.journal.journal_board(
            cur_w)["total"]
        tp4_ok = (tp_rows_post == 14 and tp_seq_final == 26
                  and tp_tally_post == tp_tally_pre
                  and tp_tally_cur_post == tp_tally_cur_pre
                  and tp_total_post == tp_total_pre
                  and tp_board_cur_post == tp_board_cur_pre)

        # AC-TP5: pure-read law - the ro face never moved rows
        tp_post_n_ro = tp_ro_scalar(
            "SELECT COUNT(*) FROM water_windows")
        tp5_ok = (tp_pre_n == 14 and tp_post_n_ro == 14)

        sections.append("[21] seq-bookkeeping tamper id-reuse:")
        sections.append("    tamper-rollback: seq %s->%d rows=%d"
                        " total=%s %s"
                        % (tp_seq_pre, tp_seq_zero, tp_rows_zero,
                           tp_total_zero,
                           "OK" if tp1_ok else "DRIFT"))
        sections.append("    id-reuse: new-id=%d seq-mid=%d"
                        " rows=%d board-cur=%d->%d %s"
                        % (tp_reuse_id, tp_seq_mid, tp_rows_mid,
                           tp_board_cur_pre, tp_board_cur_mid,
                           "OK" if tp2_ok else "DRIFT"))
        sections.append("    restore: seq=%d rows=%d %s"
                        % (tp_seq_restored, tp_rows_restored,
                           "OK" if tp3_ok else "DRIFT"))
        sections.append("    re-green: rows=%d seq=%d"
                        " total=%s tallies-eq=%s board-cur=%d %s"
                        % (tp_rows_post, tp_seq_final,
                           tp_total_post,
                           tp_tally_post == tp_tally_pre
                           and tp_tally_cur_post
                           == tp_tally_cur_pre,
                           tp_board_cur_post,
                           "OK" if tp4_ok else "DRIFT"))
        sections.append("    pure-read: rows=%d->%d %s"
                        % (tp_pre_n, tp_post_n_ro,
                           "OK" if tp5_ok else "DRIFT"))
        fail = fail or not (tp1_ok and tp2_ok and tp3_ok
                            and tp4_ok and tp5_ok)

        # ---- [22] sqlite_sequence bookkeeping-row DELETE
        # missing state (R1838; AC-SQD1..SQD5) ------------------
        # The [21] section proved the no-reuse guarantee's
        # single point of dependence against an UPDATE tamper;
        # this section proves the second failure face - the
        # bookkeeping row can also be DELETEd outright. With
        # the row missing the AUTOINCREMENT allocator degrades
        # to the plain rowid rule max(rowid)+1, so the next
        # INSERT reuses the deleted id 15 (the same lost-guard
        # construction as [21] without touching a product value)
        # and self-rebuilds the bookkeeping row at the wrong
        # lower watermark. Engine semantics pinned empirically
        # before this section landed (R1704 law; dm_precheck,
        # SQLite 3.50.4 - which also falsified the naive
        # re-INSERT restore beside a rebuilt row: name carries
        # no UNIQUE, duplicate row, stale first read; the
        # post-consume restore is an UPDATE, the direct
        # re-INSERT is legal only while truly missing).

        def sqd_ro_scalar(sql, args=()):
            sqd_ro = sqlite3.connect(
                "file:" + journal_db.replace(os.sep, "/")
                + "?mode=ro", uri=True)
            got = sqd_ro.execute(sql, args).fetchone()
            sqd_ro.close()
            return got[0] if got else None

        sqd_pre_n = sqd_ro_scalar(
            "SELECT COUNT(*) FROM water_windows")
        sqd_seq_rows_pre = sqd_ro_scalar(
            "SELECT COUNT(*) FROM sqlite_sequence"
            " WHERE name = 'water_windows'")
        sqd_seq_pre = sqd_ro_scalar(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'")
        sqd_live_max_pre = sqd_ro_scalar(
            "SELECT MAX(window_id) FROM water_windows")
        # product faces before the missing round
        sqd_tally_pre = dict(
            pipe.journal.kind_tally()["kind_tally"])
        sqd_tally_cur_pre = dict(
            pipe.journal.kind_tally(cur_w)["kind_tally"])
        sqd_total_pre = pipe.journal.cell_totals()["total"]
        sqd_board_cur_pre = pipe.journal.journal_board(
            cur_w)["total"]

        # AC-SQD1: evaporate the bookkeeping row - missing state
        sqd_conn = sqlite3.connect(journal_db)
        sqd_conn.execute(
            "DELETE FROM sqlite_sequence"
            " WHERE name = 'water_windows'")
        sqd_conn.commit()
        sqd_missing_n = sqd_conn.execute(
            "SELECT COUNT(*) FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        sqd_rows_missing = sqd_conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        sqd_total_missing = pipe.journal.cell_totals()["total"]
        sqd1_ok = (sqd_seq_pre == 26
                   and sqd_seq_rows_pre == 1
                   and sqd_missing_n == 0
                   and sqd_rows_missing == 14
                   and sqd_live_max_pre == 14
                   and sqd_total_missing == sqd_total_pre)

        # AC-SQD2: degraded allocation reuses deleted id 15 and
        # self-rebuilds the bookkeeping row at the wrong
        # watermark (NOT seq+1 == 27)
        sqd_conn.execute(
            "INSERT INTO water_windows (kind, delta,"
            " total_delta, ts_utc) VALUES ('submit', '{}',"
            " 0, ?)",
            (cur_w + "-24T00:00:00.000000Z",))
        sqd_reuse_id = sqd_conn.execute(
            "SELECT last_insert_rowid()").fetchone()[0]
        sqd_rows_mid = sqd_conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        sqd_rebuilt = sqd_conn.execute(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()
        sqd_conn.commit()
        sqd_board_cur_mid = pipe.journal.journal_board(
            cur_w)["total"]
        sqd2_ok = (sqd_reuse_id == 15 and sqd_rows_mid == 15
                   and sqd_rebuilt is not None
                   and sqd_rebuilt[0] == 15
                   and sqd_board_cur_mid == sqd_board_cur_pre + 1)

        # AC-SQD3: restore by UPDATE on the self-rebuilt row
        sqd_conn.execute(
            "UPDATE sqlite_sequence SET seq = 26"
            " WHERE name = 'water_windows'")
        sqd_conn.commit()
        sqd_seq_up = sqd_conn.execute(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        sqd_seq_up_rows = sqd_conn.execute(
            "SELECT COUNT(*) FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        sqd_rows_up = sqd_conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        sqd3_ok = (sqd_seq_up == 26 and sqd_seq_up_rows == 1
                   and sqd_rows_up == 15)

        # AC-SQD4: world re-green - delete the reused row
        sqd_conn.execute(
            "DELETE FROM water_windows"
            " WHERE window_id = ?", (sqd_reuse_id,))
        sqd_conn.commit()
        sqd_rows_post = sqd_conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        sqd_seq_post = sqd_conn.execute(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        sqd_tally_post = dict(
            pipe.journal.kind_tally()["kind_tally"])
        sqd_tally_cur_post = dict(
            pipe.journal.kind_tally(cur_w)["kind_tally"])
        sqd_total_post = pipe.journal.cell_totals()["total"]
        sqd_board_cur_post = pipe.journal.journal_board(
            cur_w)["total"]
        sqd4_ok = (sqd_rows_post == 14 and sqd_seq_post == 26
                   and sqd_tally_post == sqd_tally_pre
                   and sqd_tally_cur_post == sqd_tally_cur_pre
                   and sqd_total_post == sqd_total_pre
                   and sqd_board_cur_post == sqd_board_cur_pre)

        # AC-SQD5: second missing round - direct re-INSERT
        # restore while truly missing (zero ids consumed),
        # then the re-arm proof (fresh INSERT allocates
        # seq+1 == 27, NOT the reused 15), then delete; the
        # honest final state is 14 rows at seq 27 (the consume
        # advanced the high-water, the delete never retreats).
        sqd_conn.execute(
            "DELETE FROM sqlite_sequence"
            " WHERE name = 'water_windows'")
        sqd_conn.commit()
        sqd_missing2 = sqd_conn.execute(
            "SELECT COUNT(*) FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        sqd_conn.execute(
            "INSERT INTO sqlite_sequence (name, seq)"
            " VALUES ('water_windows', 26)")
        sqd_conn.commit()
        sqd_ri_rows = sqd_conn.execute(
            "SELECT COUNT(*) FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        sqd_ri_seq = sqd_conn.execute(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        sqd_ri_live = sqd_conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        sqd_conn.execute(
            "INSERT INTO water_windows (kind, delta,"
            " total_delta, ts_utc) VALUES ('submit', '{}',"
            " 0, ?)",
            (cur_w + "-25T00:00:00.000000Z",))
        sqd_rearm_id = sqd_conn.execute(
            "SELECT last_insert_rowid()").fetchone()[0]
        sqd_conn.commit()
        sqd_rearm_ok = (sqd_missing2 == 0 and sqd_ri_rows == 1
                        and sqd_ri_seq == 26
                        and sqd_ri_live == 14
                        and sqd_rearm_id == 27)
        sqd_conn.execute(
            "DELETE FROM water_windows"
            " WHERE window_id = ?", (sqd_rearm_id,))
        sqd_conn.commit()
        sqd_rows_final = sqd_conn.execute(
            "SELECT COUNT(*) FROM water_windows").fetchone()[0]
        sqd_seq_final = sqd_conn.execute(
            "SELECT seq FROM sqlite_sequence"
            " WHERE name = 'water_windows'").fetchone()[0]
        sqd_conn.close()
        sqd_post_n_ro = sqd_ro_scalar(
            "SELECT COUNT(*) FROM water_windows")
        sqd5_ok = (sqd_rearm_ok
                   and sqd_rows_final == 14
                   and sqd_seq_final == 27
                   and sqd_post_n_ro == 14
                   and sqd_pre_n == 14)

        sections.append("[22] seq-row-delete missing state:")
        sections.append("    evaporated: seq-rows %d->%d"
                        " rows=%d total=%s %s"
                        % (sqd_seq_rows_pre, sqd_missing_n,
                           sqd_rows_missing, sqd_total_missing,
                           "OK" if sqd1_ok else "DRIFT"))
        sections.append("    degraded-reuse: new-id=%d rows=%d"
                        " rebuilt-seq=%s board-cur=%d->%d %s"
                        % (sqd_reuse_id, sqd_rows_mid,
                           sqd_rebuilt[0] if sqd_rebuilt
                           else None,
                           sqd_board_cur_pre, sqd_board_cur_mid,
                           "OK" if sqd2_ok else "DRIFT"))
        sections.append("    update-restore: seq=%d seq-rows=%d"
                        " water-rows=%d %s"
                        % (sqd_seq_up, sqd_seq_up_rows,
                           sqd_rows_up,
                           "OK" if sqd3_ok else "DRIFT"))
        sections.append("    re-green: rows=%d seq=%d"
                        " total=%s tallies-eq=%s board-cur=%d %s"
                        % (sqd_rows_post, sqd_seq_post,
                           sqd_total_post,
                           sqd_tally_post == sqd_tally_pre
                           and sqd_tally_cur_post
                           == sqd_tally_cur_pre,
                           sqd_board_cur_post,
                           "OK" if sqd4_ok else "DRIFT"))
        sections.append("    reinsert-rearm: mid-missing=%d"
                        " ri-rows=%d ri-seq=%d ri-live=%d"
                        " rearm-id=%d final-rows=%d"
                        " final-seq=%d %s"
                        % (sqd_missing2, sqd_ri_rows,
                           sqd_ri_seq, sqd_ri_live,
                           sqd_rearm_id, sqd_rows_final,
                           sqd_seq_final,
                           "OK" if sqd5_ok else "DRIFT"))
        sections.append("    pure-read: rows=%d->%d %s"
                        % (sqd_pre_n, sqd_post_n_ro,
                           "OK" if (sqd_pre_n == 14
                                    and sqd_post_n_ro == 14)
                           else "DRIFT"))
        fail = fail or not (sqd1_ok and sqd2_ok and sqd3_ok
                            and sqd4_ok and sqd5_ok)

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
        sections.append("[23] hygiene: probe-ascii=%s import-lines-clean=%s "
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
