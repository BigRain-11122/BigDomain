"""Battery suite for tools/crawl_runner.py (R2991).

WHY: R2990 landed the record face, and nothing ever wrote a record except the
suite grading the writer - the daily-crawl limb stayed an honest red that no
executor could fill. crawl_runner is that executor, and this suite grades the
two things a crawl executor can be wrong about: the JUDGEMENT (is this page the
same page?) and the DECLARATION (does a failure never look like a crawl?).

PINNED BEFORE THE CODE: AC-RUN1..AC-RUN4 were written into src/os/backlog.md in
this same window, BEFORE crawl_runner.py existed (in-window pre-registration,
disclosed as such). AC-RUN5/AC-RUN6 followed at R2992 and AC-RUN7/AC-RUN8 at
R2993, each pinned in the same board file before the function or arm it grades.
AC-RUN7 grades the failure side channel's first READER (summarize_failures and
`--failures`); AC-RUN8 grades the launcher block offline, since R2992 disclosed
that "the one part no arm covers" was exactly that block. AC-RUN9/AC-RUN10
(R2994) grade the daily failure HISTORY (one row per day, rewritten in place)
and its reader, plus the launcher's --root $Project anchor - all offline.
AC-RUN11/AC-RUN12 (R2995) grade the TREND line that joins the history with the
side channel (today / previous day / mean / delta / worst day / recurrence) and
the launcher's flag ORDER (the snapshot must follow the write), both offline:
nothing here writes a file outside a temp directory and no launcher is started.
AC-RUN13 (R2996) grades the trend's EVIDENCE label (side / history / none) and
the failure CLASS bucket it carries, so a pruned side channel cannot read like
a source that never failed - also offline, temp directories only.
AC-RUN14 (R2997) grades the recurrence WEIGHT (recur=<sources>:<failures>, and
none rather than 0:0 once the side channel is gone) and the single shared
failure_kind() bucket that both --failures and the trend line now read.
AC-RUN16 (R2999) grades the SIZE face --failures gained: the file's own bytes
and physical line count, so `lines - (total+bad)` crosses the reader against the
file, plus a DISPLAY-ONLY size_gate percentage whose denominator (100MB, the
group water table's single-jsonl line) is printed on the same row. The arm that
pins the absence of a verdict deliberately does NOT build a 100MB file; it reads
the summary's key set and the emitted tokens instead, and says so.
AC-RUN17 (R3000) grades the same size face on the HISTORY file, which is the
half of the retention exemption the header argued for it. bytes only - `lines`
was measured to equal days after any beat rewrite, so it would restate the row -
and the above-reference print path is pinned as a pure function rather than by
constructing a 100MB file, which this suite therefore never does.
AC-RUN18 (R3001) grades the trend's FAILURE IDENTITY: newest_src names the last
source by largest failed_at (not by file order) and since_ok answers
yes/no/unmeasured by reading the crawl record for a LATER row of that source -
UNMEASURED, not "no", once the side channel or the record face is gone. Every
arm writes only inside a per-run temp directory; no socket and no clock.
AC-RUN19 (R3002) grades REPAIR STABILITY: flips= counts success -> failure
transitions for the newest source, so a stable repair (fail, ok) and a source
fixed, broken again and fixed again (fail, ok, fail, ok) stop reading the same
- both answer since_ok=yes, and only flips separates them. It also pins that
flips is UNMEASURED (never 0) without a record file or a side channel, that a
same-second success and failure are not ordered into an invented flip, and that
recur keeps answering its own question (same-day flapping is one flip and
recur=0:0 at once).
AC-RUN20 (R3003) grades RECORD COVERAGE: rcov= names how far the crawl record
itself reaches (first..last day of its usable rows), so since_ok=no standing on
a record that stopped before the failure stops reading like a record that
looked afterwards. It also pins that cov= (history face) and rcov= (record face)
are read from different files in the same world, and that malformed rows can
neither widen nor invent a span.
AC-RUN21 (R3004) grades the VERDICT SPLIT: since_ok may say 'no' only when the
record is shown to reach strictly past the failure stamp, so a zero-byte file, a
file whose newest row predates the failure, a file of only malformed rows and a
success stamped in the same second all answer 'unmeasured' - "we never looked"
is not "we looked and it is still broken". It also pins the deliberate split
from flips: a flip is a pair of events already on disk, so since_ok=unmeasured
may sit beside flips=1 without either field lying. AC-RUN20's pre-failure arm
was rewritten to the new verdict on purpose - the contract moved, and an arm
that keeps the old reading would hide it.
AC-RUN22 (R3005) grades WINDOW BREADTH: newest_src/since_ok answer for the one
source that failed last, so three failing pages left two of them without a
verdict. pending=<no>/<judged> counts, over the whole window and each source's
own latest failure, the sources shown looked-at and never back over the sources
that could be judged at all - an unmeasured source is in neither number, because
a since_ok != 'yes' numerator was measured to count a source nobody ever looked
after as pending. It also pins that recur= and pending= answer different
questions in both directions, and that a multi-source window still prints one
line (per-source lines were refused, not forgotten).
AC-RUN23 (R3006) grades NAMING ONE: pending= answered how many sources were
still gone and never which one, so a person still guessed where to start. The
row now carries pending_src=, the pending source waiting longest (its own latest
failure stamp smallest, ties by url ascending), none when nothing is pending. An
unjudged=<n> field was refused on measurement - it always equals sources minus
the pending denominator (0, 1 and 2 in three probe worlds), so it would only
restate two keys already on the line - and the earlier premise that
pending=none and "all came back" read the same was measured false ('none' versus
'0/2'). An unmeasured source is never named.
AC-RUN24 (R3007) grades HOW LONG: the name said where to start, never how long
the wait had been, so a source gone five minutes and one gone a week read the
same. The row now carries pending_age_d=, whole days from the NAMED source's own
latest failure to the window day, taken on the record writer's ten-character day
prefix and no clock of its own. It is deliberately not the failure summary's
newest_at, which is measured across ALL sources (the probe world had it naming a
different source's stamp than pending_src). It reads None - never 0 - when
nothing is named, a date is unusable, or the stamp is later than the reference
day. The other pending sources remain counts: their number is the numerator
minus one (refused as arithmetic) and their names need one line per source
(refused). Six existing key-set arms were widened by this one key, disclosed as
criteria moving with the field rather than being relaxed.
AC-RUN25 (R3008) grades the OTHER END: one age described the source waiting
longest and said nothing about the rest, so with several pending sources a burst
that just started read exactly like a long tail (measured: three pending sources
aged 0/2/4 days read pending_age_d=4 with the 0-day one absent from all 24
keys). The row now also carries pending_age_min_d=, whole days from the NEWEST
pending source's own latest failure to the window day - the same ten-character
day prefix and the same None rules as pending_age_d. Together the two are the
AGE SPAN of the pending set. A pending_age_max_d field was measured and refused:
the named source is by construction the oldest, so a max would restate
pending_age_d. With one pending source, or several sharing one stamp, the two
ages coincide - pinned as a fact so it is never silently 'fixed' into a None.
Seven existing key-set arms were widened by this key (the six above plus
AC-RUN24's own), disclosed as criteria moving with the field.
AC-RUN26 (R3009) grades the MIDDLE: two ends described the span and left
everything between them silent, so "a burst that just started" and "an old tail
with one new arrival" printed the same row (measured: ages 5/3/0 and 5/1/0 were
identical on all 25 keys, and so were 5/5/5/0/0 and 5/0/0/0/0). The row now also
carries pending_age_med_d=, the middle element of the pending set sorted by age,
taking the one nearer the OLD end when the count is even. This is not the max
refused in R3008 - a max equalled pending_age_d by construction in every world,
while the middle coincides with an end only at N<=2 or when the mass piles on
one end, which is the reading it adds. Pointing the reader at the failure-day
file was measured and refused as an alternative (that file carries a urls=
COUNT and no per-source identity or age). Eight existing key-set arms were
widened by this key (the seven above plus AC-RUN25's own), disclosed as criteria
moving with the field.
AC-RUN27 (R3010) grades the OUTSIDE of the window: the window decides who is
counted, so a source whose own latest failure fell before the window start left
every key - measured, a still-broken old source and a repaired one differed only
through rcov, and a side channel trimmed to the window read identical to a
healthy world on all 26 keys. The row now also carries pending_old=<n>/<judged>
over sources whose own latest failure is strictly before the window start: a
third count with its own denominator, so pending= keeps meaning what sources=
names (rewriting pending= to count both was measured and refused - it would
report more judged sources than that population contains). judged==0 answers
None, never 0/0: a trimmed side channel, an empty outside face and a record that
stops before the old failure all mean "nothing was looked at out there". Nine
existing key-set arms were widened by this key (the eight above plus AC-RUN26's
own), disclosed as criteria moving with the field.
AC-RUN28 (R3011) grades the COVERAGE OF THE SIDE CHANNEL: pending_old= counts
over the failure side channel but never said how far back that channel reaches -
measured, two worlds whose channels reached one day and ninety-one days were
identical on all 27 keys (the extra row was an earlier failure of the SAME
source, so every judged fact matched). The row now also carries
fcov=<first>..<last>, the channel's own first and last usable failure day, on
the same day law as cov= and rcov= and following the FILE rather than the window
(measured: same span at 7 and 14 days while pending_old= changed). Every
coverage reading now names its own file: cov= the failure-day history, wcov=
that history's fill inside the window, rcov= the crawl record (success
evidence), fcov= the failure side channel pending_old= judges on. Absent, empty
and all-unusable channels read none, never an empty string; malformed rows never
widen the span. Ten existing key-set arms were widened by this key (the nine
above plus AC-RUN27's own), disclosed as criteria moving with the field.
AC-RUN29 (R3012) grades the AGE OF THE OLD WAITERS: pending_old= names a
fraction but never how long the sources behind it have been gone - measured,
fcov.first= is the oldest failure in the FILE and can belong to a source that
was repaired (probe world: fcov 2026-08-20..2026-11-10 where the failure still
unrepaired was 2026-11-10). The row now also carries pending_old_age_d=<days>,
the still-pending out-of-window source that waited longest, on the same day law
and None rules as the three in-window ages. None when nothing outside was
judged AND none when every judged old source came back - never 0, because a
clean outside population and a waiter aged zero must not print the same digit.
What R3010 refused stays refused (per-source naming, one line per source). Eleven
existing key-set arms were widened by this key (the ten above plus AC-RUN28's
own), disclosed as criteria moving with the field.
AC-RUN30 (R3013) grades the OTHER END OF THE OLD TAIL: one age described only the
longest old wait, so with two old waiters the other was invisible - measured, a
second waiter that failed 90 days ago and one that failed 9 days ago read
IDENTICAL on all 29 keys, including the same file span. The row now also carries
pending_old_age_min_d=<days>, the YOUNGEST still-pending out-of-window source, on
the same day law and the same None rules as the age beside it. A MIDDLE reading
was measured and refused: with two waiters - the count the board itself named -
the middle nearer the old end restates the longest age in both worlds, and at
three or more reading the shape needs one line per source, which the contract
refuses. Pointing a reader at the failure file was refused by measurement too:
with the file byte-identical, one extra record row moved the old fraction from
2/3 to 1/3. With one old waiter the two ages coincide, pinned as a truth rather
than turned into none. Eleven existing key-set arms were widened by this key
(the eleven above, each at its baseB set), disclosed as criteria moving with the
field.

AC-RUN33 (R3016) grades CHANNEL LIVENESS on the old-waiter list: the header
said why the table was empty and how far the evidence reached, never WHEN the
channel was last written. Measured before the pin (qa/probe-R3016.log): a last
failure at 00:05 and one at 23:50 on the SAME day read the same dictionary and
the same header, because fcov= is a pair of days - while the board's own pair
(stopped yesterday versus written this minute) had ALREADY been separated by
that span, which this criterion measures so the round does not take credit for
an existing capability. The header now carries last_at=<YYYY-MM-DDTHH:MM>, the
writer's own characters echoed from the rows this call already loaded, or
last_at=none with no usable row. No age is printed: a day age over that stamp
was measured to equal the age of fcov's last day in every probed world, and an
hour age would need a clock this module never reads.

AC-RUN34 (R3017) grades EVIDENCE QUALITY on the same list: the dictionary
carried `bad` (unusable lines on the side channel) and the header never printed
it. Measured before the pin (qa/probe-R3017.log): the same usable rows plus two
malformed lines moved bad 0 -> 2 while fcov, last_at and pending_old stayed
byte-identical and the two headers were equal - and the strongest shape is the
empty table, where a channel holding only broken lines read exactly like an
absent channel. The header now carries bad=<n>, ALWAYS printed including 0,
from the single read_failures call this face already makes. It is not folded
into reason=: measured, a populated table carries bad=2 with reason None, so
folding it in would put an excuse on a non-empty list.

AC-RUN36 (R3019) grades the SAME BLIND SPOT ON THE OTHER FILE: CRAWL-FAILURE-DAYS
printed bad=<n> for the daily history and nothing could name one, because
read_failure_days carried its own loop with no numbering. Measured before the
change (qa/probe-R3019.log - the pre-change shape is read from the HEAD revision
through git show rather than remembered): no shared parse law, no numbering, no
day-bad reader, four reject branches and none of them named. The same numbering
law would have applied anyway (non-blank physical lines, blank skipped, count ==
rows + bad), so the loops were unified into _json_lines(path, kind_of_row) while
each file keeps its OWN reject taxonomy - the history names json/shape/day/on_day
instead of collapsing four different repairs into the side channel's one word.
One further measured fact shapes the face: snapshot_failure_day rewrites the file
from validated rows, so a history bad line is gone on the next beat, while an
appended side-channel line keeps its number; the face is therefore read-only with
no advice. --pending-old-bad keeps its shipped name and header (AC-RUN35 arm 1
pins the text); the new subcommand is --failure-days-bad.

AC-RUN37 (R3020) grades WHAT THE REWRITE ITSELF EATS. The row written by
snapshot_failure_day carried bad=, which is the SIDE channel's unusable count,
so a beat silently removing four malformed history lines still read bad=0
(measured, qa/probe-R3020.log). The day row now also carries dropped= - this
file's own lines discarded by rewrites that stamped the same day - accumulated
rather than per-rewrite, because the ten-minute beat would overwrite a
per-rewrite number before it could be read (the transience AC-RUN36 pinned).
Two further measured facts fixed the shape: the day row's key set was pinned
verbatim nowhere (0 exact assertions) while the series dict IS pinned exactly,
and the discard count was already in hand under the name `_ignored`, so no new
read was needed. Old rows are never backfilled (their drops were not measured),
and neither the series nor the trend row gains the field (summing a key that
older rows lack would print unmeasured as zero).

AC-RUN39 (R3022) grades THE WRITER'S OWN HEADER. AC-RUN38 gave the eaten-lines
count a reader, but the snapshot beat - the face a person watches every ten
minutes - printed day/on_day/total/recent/bad/urls and said nothing about the
lines its rewrite had just eaten; measured on this checkout (qa/probe-R3022.log
P1f), the header printed bad=0 urls=0 while the row it wrote carried dropped=0.
Both print sites now end with dropped=, the row's own value. Measured before the
change: 0 exact-equality assertions on CRAWL-FAILURE-DAY (only substring arms),
and a fresh row always carries the key as an int, so `none` never belongs on
this face (it stays the DAYS word for a pre-field row). The token is appended so
the five older positions keep working, and deliberately not put between bad=
and urls= where two different facts would read as one; the per-day LIST of
dropped values was measured as per-row rather than a sum (two .get sites, no
cross-row addition) and is left for a later round. Arms 1/2/3/5/6/7 exercise the
shipped standalone snapshot path, which stamps the machine's day - no assertion
here depends on which day that is.

AC-RUN40 (R3023) grades EVERY DAY, NOT JUST THE LAST. R3021 gave the DAYS header
the last row's eaten count, so any earlier day still meant opening the jsonl.
Measured before the change (qa/probe-R3023.log): that header prints exactly one
line (P3a) and nothing pins the flag set or the help text (P1a/P1b), so the list
lives in its own subcommand `--failure-days-dropped` - header
CRAWL-FAILURE-DAYS-DROPPED then one DAY-DROPPED line per usable row in FILE
order. A row written before the field carries no key at all (P2c), the same day
can appear twice on disk (P2e), and the reader already yields file order (P2a),
so the listing reports what is there: no sort, no de-duplication, no sum, no
maximum, no backfill. `none` is the word for an unmeasured row; 0 means that
day really ate nothing. The DAYS face, the (day, on_day) pairs and the 30-key
trend row are untouched and arm 6 checks them in the same world.

AC-RUN41 (R3024) grades the WINDOW that listing lacked. It printed every row
with no bound, so its length grew with the file while the DAYS series had a
`--days` limit since R3000. Measured before the change (qa/probe-R3024.log): the
unwindowed header is pinned by two exact-equality arms (P2a), `--days` already
has seven other readers (Q3b), and nothing reads `days=` as the printed-line
count (Q2a/Q2c) - so the window is OPT-IN (`--failure-days-dropped-window N`)
and the default face keeps its exact shape. The head day is the file's OWN last
usable row, and the threshold comes from the one window law `_window_start`
(R3014): no clock, so a 2001 history windows against itself (arm 7). Rows older
than the threshold are counted into `hidden` and the header says
truncated=<0|1>, because a shortened list with no token would read exactly like
a file that never had those days. `days=` keeps its own meaning (usable rows in
the file) and `shown=` is what this run printed; a same day twice stays twice.

AC-RUN43 (R3026) grades the DAY WINDOW the series itself lacked. Measured before
the change (qa/probe-R3026.log): the tail printed a day sixty days outside the
window while saying nothing, one suite arm pins the header's tail by exact
equality, and --days carries nine readers in main - so the window arrives as its
own opt-in flag (`--series-days N`) and the default face is byte-identical.
Two quantities stay two words: the window picks which rows qualify, the row
limit (--days) caps how many print, and the header now carries
`series_window=N` beside the four counts R3025 added. The head day is the file's
OWN newest row, so a 2001 history windows against itself (arm 6), and the three
counts are 0 rather than an invented window when there is no history (arm 5).

AC-RUN44 (R3027) grades the GAPS that window could not name. Measured before the
change (qa/probe-R3027.log): a seven-day window over four rows on two distinct
days left five calendar days silent and the line said nothing, a measured zero
already prints as :0 in the pairs, the trend face already reads a day nobody
snapshotted as 'absent', and five arms assert a 2-tuple in the pairs - so the
gaps travel as their OWN opt-in token (`--series-absent`, refused with rc=2
unless `--failure-days --series-days N` are both given). The pairs and the four
counts keep their meanings; `series_absent=<n|none>` counts calendar days in
the window with no row and `absent=<day,...|none>` names them ascending. A day
holding three rows is one present day, not three (arm 4), an unusable head
answers none rather than a zero that would read like "every day was recorded"
(arm 7), and a 2001 history windows against itself (arm 6).

AC-RUN45 (R3028) grades the TOTAL that naming every gap still left as a comma
count. Measured before the change (qa/probe-R3028.log): no face put "days that
hold a row" beside the window width, `window_rows=` counts rows and not days
(four rows on two days), and a `days_absent=` token would break the one arm
counting the literal `absent=` twice. So `--series-absent` now also prints
`days_present=<n|none>` from `series_presence_counts()`: DISTINCT calendar days
inside the window holding at least one row, with the invariant present + gap =
series_window (arms 1/3/7). A repeated day is one present day (arm 2), an
unusable head answers none for both counts (arm 5), a 2001 history windows
against itself (arm 6), and the default face stays byte-identical with no new
token (arm 4). A `window_days=` token was refused because it could only repeat
`series_window=` (arm 8 keeps the older absent= count intact).

AC-RUN46 (R3029) grades the DIFFERENCE those two numbers left as homework.
Measured before the change (qa/probe-R3029.log): `window_rows=` counts rows and
`days_present=` counts days, so four rows on two days print 4 beside 2 with
nothing on the line saying the extra two are the same days again; no token in
the module or the suite carried that difference, the three byte-pinned
endswith() tails are all on the DEFAULT face, and the ten len(tokens)==N arms
belong to the trend faces rather than this tail. So `series_presence_counts()`
also returns `repeat` (= rows inside the window beyond the first on each day
holding a row) and `--series-absent` prints `repeat_rows=<n|none>` after
`days_present=`, giving `days_present + repeat_rows = window_rows` beside the
older present+gap=window invariant (arm 1). One row per day answers a measured
zero (arm 2), an unusable head answers none rather than zero (arm 3), a 2001
history windows against itself (arm 4), the default face stays byte-identical
with no new token (arm 5), and the refused names plus the older absent= count
survive (arm 6). Stated honestly: `repeat_rows` is a subtraction of two numbers
already printed, not a new measurement; its only value is that the two
invariants become checkable by eye.

AC-RUN47 (R3030) grades WHAT a same-day repeat is. Measured before the change
(qa/probe-R3030.log): `on_day` is the number of that day's failure rows at
write time (a count, not a clock), no shipped face compares two rows of the
same day, and every on_day reader either prints the pair or takes int()/max().
So `series_presence_counts()` also returns `retry` - repeated rows whose on_day
is not greater than the previous row of the SAME day - and the flagged tail
prints `retry_rows=<n|none>` after `repeat_rows=`, giving `retry_rows <=
repeat_rows` (arm 1). Equal on_day counts as a re-recording (arm 2), a growing
day answers a measured zero (arm 3), an unusable head answers none (arm 4), a
2001 history windows against itself (arm 5), the default face stays
byte-identical (arm 6), and the refused names plus the older absent= count
survive (arm 7). Stated honestly: retry is an INFERENCE from a counter that
did not grow, not proof that a run was interrupted.

AC-RUN49 (R3032) grades the SILENT-DAY LIST CAP. Measured before the change
(qa/probe-R3032.log): `absent=` printed one name per silent day at exactly
11.00 bytes each, so the line grew with the window - this checkout's one-row
history printed 364 names (4310 bytes) at width 365 and 11296 bytes at 1000 -
while `series_limit` caps only the series pairs, not this list; the name count
always equalled `series_absent` (eight worlds), no arm pinned the whole line,
and a byte budget is not a law a reader can predict from the window. So the
pure function takes `limit` with a module constant `ABSENT_LIST_LIMIT = 31`,
returns `named` and `truncated` beside the unchanged `count` (the FULL total),
and the flagged tail prints `absent_named=<n|none>` (a name that does not
contain the substring `absent=`, so the four arms counting it twice stay
green). A seven-day window is complete and prints named=5 of 5 (arm 1); a
sixty-day window names its first 31 silent days from the window start and
stops while the total stays 58 (arm 2); 31 gaps fit and 32 print one short
(arm 3); the total never shrinks to the printed count (arm 4); a 2001 history
caps against its own last row with no clock (arm 5); the default face stays
byte-identical (arm 6); and at width 1000 the line stays under 1000 bytes with
the older absent= pair intact and no byte written (arm 7).

AC-RUN48 (R3031) grades the WINDOW START. This paragraph was missing until
R3033 disclosed and repaired it - the criterion shipped without a doc-head
entry, so a reader of this header could not know it existed. Measured before
that change (qa/probe-R3031.log): nine `_window_start` call sites share one
literal-day string, membership is `threshold <= day <= head` (so a calendar day
is wholly in or wholly out and `repeat`/`retry` are exact), and `window_from`
had zero hits anywhere. The opt-in tail prints `window_from=<day|none>` and the
arms pin: every width 1..10 splits no day (arm 1), the start equals the real
threshold and moves a whole day when the window narrows (arm 2), a day at the
edge stays out whole (arm 3), an unusable head answers none rather than an
invented date (arm 4), a 2001 history opens from its own last row (arm 5), the
default face stays byte-identical (arm 6), and no refused token appears (arm 7).

AC-RUN50 (R3033) grades the OPT-IN ESCAPE HATCH from that cap. Measured before
the change (qa/probe-R3033.log): two private worlds with the same window,
`days_present=10`, `series_absent=50` and `absent_named=31` - differing only in
three HIDDEN row days - printed BYTE-IDENTICAL lines, so the 19 unnamed silent
days are not recoverable from the line; the premise that they are unprintable
ANYWHERE in the repo measured FALSE (`--failure-days-dropped` prints every
usable row's day, so a set subtraction gets them), and that correction is
stated rather than dropped. An opt-in flag collided with nothing: six arms
count `absent=` twice, one counts `absent_named=` once, zero whole-line
equality arms carry `absent=`, and the default face is 214 bytes. So
`--series-absent-limit <N|all>` is opt-in with the default still 31: `all`
prints the full ascending list with `absent_named == series_absent` (arm 2), a
small N caps and leaves the total full (arm 3), an N larger than the gap count
invents no name (arm 4), zero/negative/non-numeric are refused with rc=2 (arm
5), the flag without `--series-absent` is refused (arm 6), a complete window
answers byte-identically under `all` and under the default (arm 7), and the
default run writes no byte and prints no verdict (arm 1/8).

AC-RUN51 (R3034) grades the PRICE TAG on that escape hatch. Measured before the
change (qa/probe-R3034.log): a silent-day name is exactly 10 characters, so the
list costs 11n-1 bytes (31 names 340B, 50 names 549B); everything else on the
line is BYTE-IDENTICAL at every cap (base without the `absent=` token: 401B
under both 31 and all), so the whole line length is arithmetically exact in
advance; no shipped face estimated an OUTPUT length (`size_gate_pct` measures
the INPUT file against a 100MB water line); and a new token named
`absent_all_bytes=` contains neither `absent=` nor `absent_named=`, so the
eight arms counting the former twice and the two counting the latter once stay
green, while the eight endswith() tails are all on the no-flag default face.
The opt-in tail now also prints `absent_all_bytes=<n|none>` - the byte length
of this line if every silent day were named, counting its own digits as a fixed
point. Arms: the default face carries no price token (arm 1); the price on the
capped line equals the REAL byte length of the line an `all` run prints, and
that run names its full total (arm 2); every cap quotes the same price because
the number describes the full list, not the list in hand (arm 3); a window
whose gaps all fit prices itself (arm 4); an unusable head answers none rather
than a free zero (arm 5); and nothing is written, no verdict prints, the pinned
counts survive, and a 2001 history prices its own window with no clock (arm 6).

AC-RUN52 (R3035) grades the PRICE OF THE MULTI-LINE BLOCK that the window
truncates. Measured before the change (qa/probe-R3035.log): on one four-row
world the four `DAY-DROPPED` lines measured 39/36/36/41 characters wide,
because `day=` is a fixed 10 characters while `dropped=` changes width; two
worlds with the SAME counts (days=4) printed 156B vs 148B, so the block size is
not derivable from the header's numbers; the board's premise that the reader
cannot tell how many LINES measured FALSE for this face (`days` is the whole
file, `shown` is this run) and that correction is stated rather than dropped;
no shipped face estimated a multi-line output total; and exactly one arm pinned
the windowed header by whole-line equality, which is EXTENDED here rather than
deleted. The windowed header therefore also prints `rows_all_bytes=<n>`: the
UTF-8 bytes of the block for every usable row, newlines included - what
dropping the window would cost. Arms: the price equals the block the
unwindowed run really prints on the same file (arm 1, a cross-run invariant
rather than self-arithmetic); the number does not move with the window because
it prices the file, not the window (arm 2); two worlds with equal counts but
different `dropped` widths price differently and each price is exact (arm 3);
an empty history prices 0 with no rows and no raise (arm 4); the unwindowed
face keeps its bytes and carries no token (arm 5); and nothing is written, no
verdict prints and the two pinned `absent=` counts survive (arm 6).

AC-RUN53 (R3036) grades the PRICE OF THE WHOLE WINDOWED RUN, header included.
Measured before the change (qa/probe-R3036.log): one six-row file printed
112/113/114-byte headers and a 236/354/355-byte stdout at N=3/30/365, while the
block stayed 240B at both N=30 and N=365 - the header's width moves with the
digit counts of window/shown/hidden and the block's with truncation, so neither
half is derivable from the other and no shipped face composed them (three
candidate tokens, zero code hits). The windowed header therefore also prints
`output_bytes=<n>`: the UTF-8 bytes this run prints in total, its own token
included, solved as a fixed point over the one header renderer rather than
estimated. Arms: the number equals the real byte length of that run's stdout,
read off the output itself (arm 1); it decomposes into header + newline +
printed block (arm 2); two windows on one file each price their own shape and
the untruncated one costs more (arm 3); an empty history prices exactly its
bare header with no day line (arm 4); the unwindowed face stays byte-identical
and gains no token (arm 5); and nothing is written, no verdict prints and the
two pinned `absent=` counts survive (arm 6). Honest boundary, measured by the
visible demo rather than assumed: the number counts the printed text with one
LF per line, and a Windows text-mode stdout translates each LF to CRLF, so a
console or pipe there receives two more bytes per printed line; the slice is
left on the LF law because `rows_all_bytes` already is, and the delta is
stated instead of papered over. Second boundary: this prices THIS window -
another N must be run to be priced.

AC-RUN54 (R3037) grades BOTH HALVES of that total. Measured before the change
(qa/probe-R3037.log): the only subtraction on the face,
`output_bytes - rows_all_bytes`, read 132 (= header + 1) unwindowed but 13 at
N=3 and -24 at N=2 against a 130-byte header, because `rows_all_bytes` prices
the whole FILE rather than this run's block; no shipped key priced the block a
windowed run prints (six candidate tokens, zero hits under tools/ and src/),
and `shown_bytes` collides with zero suite arms. The windowed header therefore
also prints `shown_bytes=<n>`: the UTF-8 bytes of the DAY-DROPPED block this
run prints, each line with its newline, read off the same rows and the same
renderer the printer uses. Both halves are then readable as
`output_bytes - 1 - shown_bytes` = the header's own width, truncated or not.
Arms: the block price equals that run's own printed block (arm 1); the
subtraction above equals the real header width on a truncated window (arm 2);
a narrow window prices a smaller block than a wide one while the full-file
price is identical, and the old subtraction is pinned as unequal to the header
(arm 3); an empty history prices a zero block with a bare-header total (arm
4); the unwindowed face stays byte-identical and gains neither token (arm 5);
and nothing is written, no verdict prints and the two pinned `absent=` counts
survive (arm 6). Boundary: both counts are on the LF law, and Windows
text-mode stdout adds one byte per printed line outside both numbers - a CRLF
face was refused because the consuming end is unknowable here.

AC-RUN55 (R3038) grades THE HEADER'S OWN WIDTH ON THE HEADER. Measured before
the change (qa/probe-R3038.log): splitting the total still required an
unwritten newline constant - on one six-day world `output_bytes - c -
shown_bytes` equals the real header width only at c=1 (223-1-78=144 and
379-1-231=147), no printed integer key equals that width (a reader assuming
nothing reads 145 against a real 144), and `header_bytes`/`newline_bytes` had
zero hits across 2599 python files while `lines=` on the DAYS face had already
been refused by the R3000 noise law (pinned by AC-RUN17). The windowed header
therefore appends `header_bytes=<n>` after `output_bytes=`, solved in ONE
fixed point with the total because each token's digits move the other's width.
The first shape of this ruling excluded the header's newline and its own arm 2
read RED: `header_bytes + shown_bytes + printed_lines` over-counts by exactly
`shown` bytes, because the block's newlines already sit inside `shown_bytes`.
The shipped shape includes the newline in `header_bytes`, so the total breaks
into exactly two halves with no constant assumed. Arms: the number equals that
run's real header line width plus its newline (arm 1); the two halves add up
exactly - `header_bytes + shown_bytes == output_bytes` (arm 2); two windows on
one file each price their own header exactly while the full-file block price
stays put (arm 3); an empty history prices its bare header, total = that same
number, with no day line (arm 4);
the unwindowed face stays byte-identical and gains no token (arm 5); and
nothing is written, no verdict prints and the two pinned `absent=` counts
survive (arm 6).

AC-RUN56 (R3039) grades THE SILENT-DAY LINE PRICING ITSELF. Measured before
the change (qa/probe-R3039.log, 20 runs over window 3/7/30/60/365 x cap
default/5/31/all): `absent_all_bytes` equalled the real line width in exactly
the eight runs that named every gap, and on the wide-window default (win=60
685B against 993B all; win=365 688B against 4352B) no printed integer key
equalled it. The opt-in tail therefore appends `line_bytes=<n>
output_bytes=<m>` before `absent_all_bytes=`, solved in one fixed point, so
`line_bytes + 1 == output_bytes` prints the trailing newline instead of
leaving it as an unwritten constant. Arms: the two numbers equal that run's
real line width and real LF stdout bytes on a truncated wide window (arm 1);
with every gap named the projection IS the line (equal), and on the truncated
run it is strictly larger by at least eleven bytes per unnamed gap - a lower
bound, since wider numbers add digits of their own (arm 2); two windows each
price their own width and the two differ (arm 3); an empty history prices its
bare line and answers `absent_all_bytes=none` (arm 4); the unwindowed default
face carries neither token and two runs are byte-identical (arm 5); and
nothing is written, no verdict prints, and both pinned `absent=` counts
survive (arm 6).

AC-RUN57 (R3040) grades THE PAIRS SEGMENT PRICING ITSELF. Measured before the
change (qa/probe-R3040.log, six private worlds, no socket, no clock): every
neighbour had learned to price itself but `series=<day:on,...>` carried no
number, and its width is decided by three things at once - the stored day
string (an ISO row prints `2026-11-10T09:00:00:1`, so "a day is always ten
characters" is false), each on_day's digit count (same shown=2 measured 25B
against 31B), and shown-1 commas - so a reader cannot reproduce it from
`series_shown=`. Five candidate token names had zero hits across tools/ and
src/, and NONE of the line's thirteen integer keys equalled the segment on any
world (`equal_keys=NONE`), the empty history included. The `--series-days`
tail therefore appends `series_bytes=<n>` after `series_window=`: the UTF-8
bytes of the `series=` key and the pairs behind it, eleven - not zero - when
the line prints `series=none`. With `--series-absent` on, the value rides
inside the one fixed point with `line_bytes`/`output_bytes`/
`absent_all_bytes`. Arms: a ten-character day world prices the real segment
(arm 1); the same shown with wider counts prices differently, both exact (arm
2); an ISO-stamped history prices its longer day strings (arm 3); an empty
history answers eleven for `series=none` (arm 4); the unwindowed default face
gains no token and does not drift (arm 5); with `--series-absent` the line
still prices itself exactly while the segment is strictly smaller, and a
fully named projection still equals the line (arm 6); and nothing is written,
no verdict prints, and both pinned `absent=` counts and the single
`series_window=` token survive (arm 7). Boundary: the count follows the LF law
like its neighbours, and nothing here refuses a long series.

AC-RUN58 (R3041) grades the pairs segment NAMING WHICH SOURCE ATE ITS WIDTH.
Measured before the change (qa/probe-R3041.log, four private worlds, no
socket, no clock): one price cannot say why the segment is wide - swapping only
the days for ISO stamps moved `series_bytes` 32 -> 50 (+18 = two days x nine
extra characters) while swapping only the counts for four digits moved it
32 -> 38 (+6 = two counts x three extra digits). Neither side had a printed key
(`equal_keys_days=NONE` on every non-empty world; the on total matched
`series_shown` only where two one-digit pairs happened to equal it), and every
candidate token name had zero hits across tools/ and src/. The `--series-days`
tail therefore also prints `series_day_bytes=<n>` (the UTF-8 bytes of every
printed pair's stored day string) and `series_on_bytes=<m>` (the decimal digits
of every printed on_day), and the arithmetic is pinned rather than implied:
`series_bytes == series_day_bytes + series_on_bytes + 2*series_shown + 6` while
pairs exist, both zeros with `series=none` at eleven otherwise. The frame
remainder is NOT printed because it is a pure function of `series_shown` (the
R3000 noise law) and every byte of it is visible on the row. Arms: both sides
equal what the row itself says and the identity holds (arm 1); ISO days leave
the count side untouched and put the whole eighteen-byte delta on the day side
(arm 2); four-digit counts do the same with six bytes on the count side (arm
3); an empty history answers zero on both sides rather than a missing key (arm
4); the unwindowed default face gains neither token and does not drift (arm 5);
with `--series-absent` both totals ride the one fixed point while the line
still prices itself and a fully named projection still equals it (arm 6); and
nothing is written, no verdict prints, and every pinned count survives (arm 7).
Boundary: these are measurements of printed text, not a verdict about a wide
series, and nothing here refuses one.

R3042 - the pairs a `--days` cap drops now have a price. Measured before the
token existed (qa/probe-R3042.log): `--days` caps how many pairs print and
`series_outside=` is 0 by construction on this face, so the dropped pairs had
no number anywhere; on a five-day world capped at two the printed pairs are a
suffix of the in-window set and rebuilding the full segment from the FILE
reproduced the printed price to the byte (32 == 32), which is what makes the
projection non-circular. The `--series-days` tail therefore also prints
`series_all_bytes=<n>`: the segment the day window would price with no cap, on
the same law as `series_bytes` (so the two are equal exactly when the cap drops
nothing - a measured equality). The dropped count stays derivable
(`window_rows - series_shown`), so no count token was added (the R3000 noise
law). Arms: a capped world prices the full segment rebuilt from the file (arm
1); the increment decomposes into dropped day bytes, dropped digit bytes and
two separators per dropped pair (arm 2); the uncapped run reads equal on both
prices (arm 3); an ISO-stamped history prices the longer stored days and puts
the lift cost mostly on the day side (arm 4); an empty history answers eleven
on both (arm 5); the unwindowed default face gains no token and does not drift
(arm 6); and nothing is written, no verdict prints, the new token appears once
and no increment twin exists (arm 7).

R3043 - the cap now says WHICH DAY it cut back to. Measured first
(qa/probe-R3043.log): both prices were on the row but nothing named the dropped
side, so the order of operations (window first, then the tail) had to be known
by heart. The printed pairs are a suffix of the in-window set, so the cut lands
on the older end - but on rows 11-10,11-10,11-11,11-11 capped at three, the
dropped row shares its day with the first kept one, so a worded claim like
"every older row was dropped" would be false. The `--series-days` tail
therefore also prints `series_dropped_from=<day|none>`: the day of the OLDEST
dropped pair, none when nothing was dropped (empty history included). The lift
increment (`series_all_bytes - series_bytes`) and the dropped count
(`window_rows - series_shown`) stay derivable and are still refused as tokens
(the R3000 noise law). Arms: the day equals the file-side projection and is
strictly older than the first kept pair (arm 1); a day straddling the cap still
names that day and that day is the first kept pair's day, pinning the narrow
reading (arm 2); an uncapped run answers none and two runs agree byte for byte
(arm 3); an empty history answers none without raising (arm 4); the unwindowed
default face gains nothing and does not drift (arm 5); and the silent-day face
still prices its own line to the byte while the refused increment twin stays
absent and the new marker appears exactly once (arm 6).

Scope, stated honestly: no arm here fetches a real page except the one failure
arm against loopback, which is meant to fail. The judgement is graded on saved
fixtures, so this suite never depends on a network being up and never writes
into qa/ - every record lands in a per-run temp directory.

Stdlib only, ASCII source, no clock of its own (fetched_at is passed in).
"""
import contextlib
import datetime
import hashlib
import io
import json
import os
import shutil
import socket
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import crawl_record as CR
import crawl_runner as RUN

FAILS = []
CHECKS = []
TODAY = '2026-11-19'
# R3047: the faces that join a saved history to "today" do read a clock,
# so every such call below names the day it runs at instead of inheriting
# the wall clock. Without this ten arms went red at 2026-11-20 00:00 while
# every one of them was still right about the world it built.
AT = TODAY + 'T23:59:00+08:00'
PAGE_A = ('<html><head><style>.x{color:red}</style>'
          '<script>var hidden="SCRIPTTEXT";</script></head>'
          '<body><h1>Period charge</h1><p>The merchant must notify the user '
          'before the charge.</p></body></html>')
URL = 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682'


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def world():
    return tempfile.mkdtemp(prefix='bd_crawlrun_')


def main():
    roots = []

    # AC-RUN1: normalisation drops noise and formatting, and keeps meaning.
    text = RUN.normalize(PAGE_A)
    ok('AC-RUN1', 'SCRIPTTEXT' not in text and 'color:red' not in text
       and 'before the charge' in text, 'noise blocks never reach the body')
    reformatted = ('<html>\r\n<body>\n\n  <h1> Period charge </h1>\r\n'
                   '<p>The merchant must notify the user before the   charge.'
                   '</p>\n</body></html>')
    ok('AC-RUN1', RUN.digest(RUN.normalize(PAGE_A)) == RUN.digest(
        RUN.normalize(reformatted)),
       'indentation, blank lines and CRLF collapse to one digest')
    edited = PAGE_A.replace('before the charge', 'after the charge')
    ok('AC-RUN1', RUN.digest(RUN.normalize(PAGE_A)) != RUN.digest(
        RUN.normalize(edited)), 'one real sentence change moves the digest')

    # AC-RUN2: the three verdicts, from a pure function.
    first = RUN.evaluate(URL, PAGE_A, {})
    ok('AC-RUN2', first['verdict'] == 'new-source',
       'an empty store reads new-source, never no-drift')
    store = {URL: {'digest': first['digest']}}
    ok('AC-RUN2', RUN.evaluate(URL, PAGE_A, store)['verdict'] == 'no-drift',
       'the same page reads no-drift against its own digest')
    ok('AC-RUN2', RUN.evaluate(URL, edited, store)['verdict'] == 'drift',
       'a changed page reads drift')
    ok('AC-RUN2', RUN.evaluate(URL, PAGE_A, {URL: {}})['verdict'] == 'new-source',
       'an entry with no digest cannot mean nothing changed')

    # AC-RUN3: the record lands through the shipped writer, and a failed
    # retrieval lands nothing at all.
    root = world(); roots.append(root)
    out = RUN.run(URL, root, body=PAGE_A, fetched_at=TODAY + 'T08:00:00+08:00',
                  write=True)
    path = CR.record_path(root)
    rows, bad = CR.read_records(path)
    ok('AC-RUN3', out['ok'] and len(rows) == 1 and bad == 0
       and rows[0]['verdict'] == 'new-source'
       and rows[0]['fetched_at'][:10] == TODAY,
       'one usable record, three fields, the caller\'s own day')
    bpath = RUN.baseline_path(root)
    store = RUN.load_baselines(bpath)
    ok('AC-RUN3', os.path.isfile(bpath) and URL in store
       and store[URL]['digest'] == RUN.digest(RUN.normalize(PAGE_A)),
       'the baseline store holds this url and its digest')
    again = RUN.run(URL, root, body=PAGE_A, fetched_at=TODAY + 'T09:00:00+08:00',
                    write=True)
    rows2, bad2 = CR.read_records(path)
    ok('AC-RUN3', again['verdict'] == 'no-drift' and len(rows2) == 2
       and bad2 == 0 and rows2[-1]['verdict'] == 'no-drift',
       'a second pass reads the stored baseline back as no-drift')
    dead = 'http://127.0.0.1:9/never'
    fail = RUN.run(dead, root, fetched_at=TODAY + 'T10:00:00+08:00',
                   timeout=3, write=True)
    rows3, bad3 = CR.read_records(path)
    ok('AC-RUN3', fail['ok'] is False and bool(fail['error']) and fail['row'] is None,
       'a failed retrieval answers ok=False with a named error')
    ok('AC-RUN3', len(rows3) == len(rows2) and bad3 == 0
       and dead not in RUN.load_baselines(RUN.baseline_path(root)),
       'a failed fetch writes no record and no baseline')
    same = RUN.evaluate(URL, edited, RUN.load_baselines(RUN.baseline_path(root)))
    third = RUN.run(URL, root, body=edited, fetched_at=TODAY + 'T11:00:00+08:00',
                    write=True)
    rows4, _ = CR.read_records(path)
    ok('AC-RUN3', third['verdict'] == same['verdict'] == 'drift'
       and rows4[-1]['verdict'] == same['verdict'],
       'the record carries the same verdict the judgement produced')

    # AC-RUN4: the dry path cannot touch a socket, and the network lives in one
    # function only.
    root2 = world(); roots.append(root2)
    real_socket = socket.socket

    def refuse(*_a, **_k):
        raise AssertionError('E_SOCKET a dry judgement opened a socket')

    socket.socket = refuse
    try:
        dry = RUN.run(URL, root2, body=PAGE_A, fetched_at=TODAY + 'T12:00:00+08:00')
    finally:
        socket.socket = real_socket
    ok('AC-RUN4', dry['ok'] and dry['verdict'] == 'new-source' and dry['dry'],
       'a fixture judgement answers with sockets refused')
    with open(os.path.join(ROOT, 'tools', 'crawl_runner.py'), 'r',
              encoding='utf-8') as fh:
        src = fh.read()
    ok('AC-RUN4', src.count('urlopen(') == 1
       and src.index('urlopen(') > src.index('def fetch(')
       and src.index('urlopen(') < src.index('def run('),
       'the one network call sits inside fetch(), above run()')

    # AC-RUN5: a failed retrieval leaves EVIDENCE and still lands no crawl.
    root3 = world(); roots.append(root3)
    fpath = RUN.failure_path(root3)
    ok('AC-RUN5', fpath != CR.record_path(root3)
       and os.path.basename(fpath) == 'crawl-failures.jsonl',
       'the side channel is its own path, not the record file')
    fail2 = RUN.run(dead, root3, fetched_at=TODAY + 'T13:00:00+08:00',
                    timeout=3, write=True)
    frows, fbad = RUN.read_failures(fpath)
    ok('AC-RUN5', fail2['ok'] is False and fail2['trace'] == fpath
       and len(frows) == 1 and fbad == 0
       and frows[0]['source_url'] == dead and frows[0]['failed_at'][:10] == TODAY
       and 'E_FETCH' in frows[0]['error'],
       'one traced line with url, day and a named E_FETCH error')
    rrows, rbad = CR.read_records(CR.record_path(root3))
    ok('AC-RUN5', rrows == [] and rbad == 0 and CR.today_summary(
        CR.record_path(root3), TODAY)['today'] == 0
       and not os.path.isfile(RUN.baseline_path(root3)),
       'the same failure writes nothing to the record file, not even a bad row')
    good = RUN.run(URL, root3, body=PAGE_A, fetched_at=TODAY + 'T14:00:00+08:00',
                   write=True)
    frows2, fbad2 = RUN.read_failures(fpath)
    ok('AC-RUN5', good['ok'] and good['verdict'] == 'new-source'
       and len(frows2) == 1 and fbad2 == 0,
       'a successful crawl writes nothing to the side channel')
    with open(fpath, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{not json\n')
        fh.write('{"source_url":"https://x","failed_at":"2026-11-19T00:00:00"}\n')
    frows3, fbad3 = RUN.read_failures(fpath)
    ok('AC-RUN5', len(frows3) == 1 and fbad3 == 2,
       'bad lines are counted, usable rows still readable')
    with open(os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan',
                           'scripts', 'scan_five_still.ps1'), 'r',
              encoding='utf-8', errors='replace') as fh:
        scan_src = fh.read()
    ok('AC-RUN5', 'crawl-failures' not in scan_src
       and 'crawl-log.jsonl' in scan_src,
       'the scanner reads the record and never the failure side channel')
    root4 = world(); roots.append(root4)
    with open(os.path.join(root4, 'qa'), 'w', encoding='utf-8') as fh:
        fh.write('not a directory')
    blind = RUN.run(dead, root4, fetched_at=TODAY + 'T15:00:00+08:00',
                    timeout=3, write=True)
    ok('AC-RUN5', blind['ok'] is False and blind['trace'] is None
       and 'E_FETCH' in blind['error'],
       'an unwritable trace leaves the failure answer intact, never raises')

    # AC-RUN6: the day gate makes a repeating beat idempotent.
    root5 = world(); roots.append(root5)
    CR.append_record(CR.record_path(root5), URL, TODAY + 'T06:00:00+08:00',
                     'no-drift', note='seeded')
    real_socket = socket.socket

    def refuse2(*_a, **_k):
        raise AssertionError('E_SOCKET the day gate opened a socket')

    socket.socket = refuse2
    try:
        due1 = RUN.run(URL, root5, fetched_at=TODAY + 'T16:00:00+08:00',
                       write=True, if_due=True)
    finally:
        socket.socket = real_socket
    rows5, _ = CR.read_records(CR.record_path(root5))
    ok('AC-RUN6', due1['ok'] and due1.get('skipped') is True
       and len(rows5) == 1 and not os.path.isfile(RUN.baseline_path(root5)),
       'a day already crawled answers skipped with no socket and no write')
    root6 = world(); roots.append(root6)
    fresh = RUN.run(URL, root6, body=PAGE_A, fetched_at=TODAY + 'T17:00:00+08:00',
                    write=True, if_due=True)
    ok('AC-RUN6', fresh.get('skipped') is False and fresh['verdict'] == 'new-source',
       'an empty day is due and is judged normally')
    root7 = world(); roots.append(root7)
    CR.append_record(CR.record_path(root7), URL, '2026-11-18T23:00:00+08:00',
                     'no-drift', note='yesterday')
    yday = RUN.run(URL, root7, body=PAGE_A, fetched_at=TODAY + 'T18:00:00+08:00',
                   write=True, if_due=True)
    ok('AC-RUN6', yday.get('skipped') is False,
       'yesterday\'s record does not cover today')
    root8 = world(); roots.append(root8)
    os.makedirs(os.path.join(root8, 'qa'))
    with open(CR.record_path(root8), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('{"source_url":"%s","fetched_at":"%sT05:00:00+08:00"}\n'
                 % (URL, TODAY))
    badrow = RUN.run(URL, root8, body=PAGE_A, fetched_at=TODAY + 'T19:00:00+08:00',
                     write=True, if_due=True)
    ok('AC-RUN6', badrow.get('skipped') is False,
       'a row with no verdict cannot stand in for a crawl')

    # AC-RUN7 (R2993): the failure side channel gets its first READER - the file
    # had a writer and no consumer outside this suite, which is evidence nobody
    # opens. Every arm below reads; none of them gates, retries or pages.
    root9 = world(); roots.append(root9)
    empty = RUN.summarize_failures(RUN.failure_path(root9), TODAY)
    ok('AC-RUN7', empty['total'] == 0 and empty['recent'] == 0
       and empty['bad'] == 0 and empty['urls'] == 0
       and empty['newest_at'] is None,
       'an absent side channel reads all zeroes, never an exception')
    fpath9 = RUN.failure_path(root9)
    RUN.append_failure(fpath9, 'https://a.example/1', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: today')
    RUN.append_failure(fpath9, 'https://b.example/2', '2026-11-16T02:00:00+08:00',
                       'E_FETCH URLError: three days ago')
    RUN.append_failure(fpath9, 'https://c.example/3', '2026-10-20T03:00:00+08:00',
                       'E_FETCH URLError: thirty days ago')
    with open(fpath9, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{oops\n')
    summ = RUN.summarize_failures(fpath9, TODAY)
    ok('AC-RUN7', summ['total'] == 3 and summ['recent'] == 2 and summ['bad'] == 1
       and summ['urls'] == 3
       and str(summ['newest_at'] or '').startswith(TODAY),
       'three usable rows (one inside the window pair), one bad line, three '
       'sources, newest names today')
    frows9, _ = RUN.read_failures(fpath9)
    newest_row = max(frows9, key=lambda r: str(r.get('failed_at') or ''))
    ok('AC-RUN7', summ['newest_error'] == newest_row['error']
       and summ['newest_at'] == newest_row['failed_at'],
       'the summary and read_failures name the same newest row')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc9 = RUN.main(['--failures', '--root', root9, '--at', AT])
    line9 = buf.getvalue().strip()
    ok('AC-RUN7', rc9 == 0 and 'CRAWL-FAILURES' in line9
       and 'total=3' in line9 and 'recent7=2' in line9
       and 'bad=1' in line9 and 'urls=3' in line9,
       'the CLI answers rc=0 with one line carrying every count')
    root10 = world(); roots.append(root10)
    RUN.append_failure(RUN.failure_path(root10), 'https://d.example/4',
                       TODAY + 'T04:00:00+08:00', 'E_FETCH URLError: solo')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc10 = RUN.main(['--failures', '--root', root10, '--at', AT])
    line10 = buf.getvalue().strip()
    ok('AC-RUN7', rc10 == 0 and 'total=1' in line10 and 'd.example' not in line10,
       '--root reads the world it is given, not the real checkout')
    root11 = world(); roots.append(root11)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc11 = RUN.main(['--failures', '--root', root11, '--at', AT])
    line11 = buf.getvalue().strip()
    ok('AC-RUN7', rc11 == 0 and 'total=0' in line11 and 'newest=none' in line11,
       'zero failures is an honest answer with rc=0, not an error code')

    # AC-RUN8 (R2993): the launcher block R2992 added described itself as
    # "the one part no arm covers". This arm reads it offline - no launcher is
    # started, no socket is opened, and the block's own behaviour is unchanged.
    loop_path = os.path.join(ROOT, 'src', 'os', 'iteration_loop.ps1')
    with open(loop_path, 'rb') as fh:
        loop_raw = fh.read()
    loop = loop_raw.decode('ascii')
    call = loop.find(r"'tools\crawl_runner.py') --if-due --write")
    ok('AC-RUN8', call > 0,
       'the launcher calls the runner with the day gate on the call line')
    try_at = loop.rfind('try {', 0, call) if call > 0 else -1
    catch_at = loop.find('catch', call) if call > 0 else -1
    ok('AC-RUN8', try_at > 0 and catch_at > call
       and 'exit' not in loop[try_at:catch_at]
       and 'throw' not in loop[try_at:catch_at],
       'the call sits inside a try/catch that neither exits nor throws')
    spawn_at = loop.find('Start-Process')
    ok('AC-RUN8', spawn_at > call > 0,
       'the crawl beat precedes the round spawn')
    ok('AC-RUN8', all(byte < 128 for byte in loop_raw)
       and b'\r' not in loop_raw,
       'the launcher stays pure ASCII with no CR bytes')
    ok('AC-RUN8', 'crawl-daily.log' in loop[try_at:catch_at],
       'the block logs its own evidence file')

    # AC-RUN9 (R2994): the failure face gains a HISTORY - one row per day, so
    # "is today worse than yesterday" has an answer instead of being re-typed.
    # A DISPLAY face only: no arm here turns a judgement green, and arm 6 pins
    # that the scanner never reads it.
    root12 = world(); roots.append(root12)
    empty_day = RUN.snapshot_failure_day(root12, TODAY + 'T20:00:00+08:00')
    drows0, dbad0 = RUN.read_failure_days(RUN.failure_day_path(root12))
    ok('AC-RUN9', empty_day['day'] == TODAY and empty_day['on_day'] == 0
       and empty_day['total'] == 0 and empty_day['recent'] == 0
       and empty_day['bad'] == 0 and empty_day['urls'] == 0
       and len(drows0) == 1 and dbad0 == 0,
       'an absent side channel still lands one honest zero row')
    f12 = RUN.failure_path(root12)
    RUN.append_failure(f12, 'https://a.example/1', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: today')
    RUN.append_failure(f12, 'https://b.example/2', '2026-11-16T02:00:00+08:00',
                       'E_FETCH URLError: three days ago')
    RUN.append_failure(f12, 'https://b.example/2', '2026-11-16T03:00:00+08:00',
                       'E_FETCH URLError: three days ago again')
    row2 = RUN.snapshot_failure_day(root12, TODAY + 'T20:05:00+08:00')
    ok('AC-RUN9', row2['on_day'] == 1 and row2['total'] == 3
       and row2['recent'] == 3,
       'three failures read on_day=1 total=3 recent7=3')
    dpath12 = RUN.failure_day_path(root12)
    seeded = {'day': '2026-11-18', 'on_day': 4, 'total': 9, 'recent': 4,
              'bad': 0, 'urls': 2, 'newest_at': '2026-11-18T01:00:00+08:00',
              'newest_error': 'E_FETCH URLError: seeded'}
    with open(dpath12, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps(seeded, sort_keys=True, separators=(',', ':')) + '\n')
        fh.write(json.dumps(row2, sort_keys=True, separators=(',', ':')) + '\n')
    RUN.append_failure(f12, 'https://c.example/3', TODAY + 'T04:00:00+08:00',
                       'E_FETCH URLError: later today')
    row3 = RUN.snapshot_failure_day(root12, TODAY + 'T21:00:00+08:00')
    drows3, dbad3 = RUN.read_failure_days(dpath12)
    ok('AC-RUN9', row3['on_day'] == 2 and len(drows3) == 2 and dbad3 == 0
       and [r['day'] for r in drows3] == ['2026-11-18', TODAY]
       and drows3[0]['on_day'] == 4,
       'a same-day snap rewrites its own row and leaves the seeded day as it was')
    with open(f12, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{oops\n')
    with open(dpath12, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{nope\n')
    drows_pre, dbad_pre = RUN.read_failure_days(dpath12)
    ok('AC-RUN9', dbad_pre == 1 and len(drows_pre) == 2,
       'a malformed history line is counted by the reader')
    row4 = RUN.snapshot_failure_day(root12, TODAY + 'T22:00:00+08:00')
    drows4, dbad4 = RUN.read_failure_days(dpath12)
    ok('AC-RUN9', row4['bad'] == 1 and row4['total'] == 4
       and len(drows4) == 2 and dbad4 == 0,
       'a malformed failure line is counted while the rewrite drops only the '
       'unusable history line')
    root13 = world(); roots.append(root13)
    RUN.append_failure(RUN.failure_path(root13), 'https://e.example/5',
                       '2026-11-18T10:00:00+08:00', 'E_FETCH URLError: yesterday')
    t_day = RUN.snapshot_failure_day(root13, TODAY + 'T20:00:00+08:00')
    y_day = RUN.snapshot_failure_day(root13, '2026-11-18T20:00:00+08:00')
    ok('AC-RUN9', t_day['on_day'] == 0 and y_day['on_day'] == 1,
       'the day is the literal first ten characters, on both sides')
    ok('AC-RUN9', RUN.failure_day_path(root13) != RUN.failure_path(root13)
       and RUN.failure_day_path(root13) != CR.record_path(root13)
       and 'crawl-failure-days' not in scan_src,
       'the history is its own path and the scanner never reads it')

    # AC-RUN10 (R2994): the history gets a READER and the launcher gets its
    # root anchor pinned. Both are offline: no socket, no launcher started.
    root14 = world(); roots.append(root14)
    real_day = RUN.failure_day_path(ROOT)
    real_before = (os.path.getmtime(real_day) if os.path.isfile(real_day)
                   else None)
    RUN.append_failure(RUN.failure_path(root14), 'https://f.example/6',
                       TODAY + 'T09:00:00+08:00', 'E_FETCH URLError: solo')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc14 = RUN.main(['--snapshot-failures', '--root', root14, '--at', AT])
    line14 = buf.getvalue().strip()
    real_after = (os.path.getmtime(real_day) if os.path.isfile(real_day)
                  else None)
    ok('AC-RUN10', rc14 == 0 and 'CRAWL-FAILURE-DAY' in line14
       and 'on_day=1' in line14 and os.path.isfile(RUN.failure_day_path(root14))
       and real_before == real_after,
       'the standalone snap answers on one line and writes in the world it '
       'was given')
    RUN.snapshot_failure_day(root14, '2026-11-18T20:00:00+08:00')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc15 = RUN.main(['--failure-days', '--root', root14])
    line15 = buf.getvalue().strip()
    ok('AC-RUN10', rc15 == 0 and 'CRAWL-FAILURE-DAYS' in line15
       and 'days=2' in line15 and ('2026-11-18:0' in line15)
       and (TODAY + ':1') in line15,
       'the reader names both days and their on_day counts')
    root15 = world(); roots.append(root15)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc16 = RUN.main(['--failure-days', '--root', root15])
    line16 = buf.getvalue().strip()
    ok('AC-RUN10', rc16 == 0 and 'days=0' in line16 and 'series=none' in line16,
       'an empty history is an honest answer with rc=0')
    snap_row14 = RUN.snapshot_failure_day(root14, TODAY + 'T23:00:00+08:00')
    drows14, _ = RUN.read_failure_days(RUN.failure_day_path(root14))
    last14 = drows14[-1]
    ok('AC-RUN10', last14 == snap_row14 and last14.get('day') == TODAY,
       'the last history row the reader sees is the row the writer returned')
    call_at10 = loop.find(r"'tools\crawl_runner.py')")
    line_end10 = loop.find('\n', call_at10)
    call_line10 = loop[call_at10:line_end10]
    ok('AC-RUN10', call_at10 > 0
       and '--if-due' in call_line10 and '--write' in call_line10
       and '--snapshot-failures' in call_line10
       and '--root $Project' in call_line10,
       'the launcher call line carries the day gate, the write, the snapshot '
       'and the root anchor')
    ok('AC-RUN10', try_at < call_at10 < spawn_at,
       'the anchored call stays inside the try and before the spawn')

    # AC-RUN11 (R2995): the history gains a TREND reader - two days side by side
    # plus whether the same source recurred. Display only: it reads the two
    # files that already exist and writes nothing.
    root16 = world(); roots.append(root16)
    h16 = RUN.failure_day_path(root16)
    f16 = RUN.failure_path(root16)
    empty_trend = RUN.summarize_failure_trend(h16, f16,
                                              TODAY + 'T20:00:00+08:00')
    ok('AC-RUN11', empty_trend['days'] == 0 and empty_trend['today'] == 'absent'
       and empty_trend['prev'] == 'none' and empty_trend['mean'] is None
       and empty_trend['delta'] == 'none'
       and empty_trend['worst'] == (None, None)
       and empty_trend['recurring'] == 0 and empty_trend['sources'] == 0,
       'two empty faces answer absent/none instead of raising')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc17 = RUN.main(['--failure-trend', '--root', root16, '--at', AT])
    line17 = buf.getvalue().strip()
    ok('AC-RUN11', rc17 == 0 and line17.startswith('CRAWL-FAILURE-TREND')
       and 'days=0 today=absent prev=none mean=none delta=none worst=none'
       in line17 and 'recurring=0 sources=0' in line17,
       'the CLI answers one line with every count on an empty world')
    os.makedirs(os.path.dirname(h16), exist_ok=True)
    with open(h16, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps({'day': '2026-11-18', 'on_day': 2, 'total': 2,
                             'recent': 2, 'bad': 0, 'urls': 1},
                            sort_keys=True, separators=(',', ':')) + '\n')
        fh.write(json.dumps({'day': TODAY, 'on_day': 1, 'total': 3,
                             'recent': 3, 'bad': 0, 'urls': 2},
                            sort_keys=True, separators=(',', ':')) + '\n')
    RUN.append_failure(f16, 'https://a.example/1',
                       '2026-11-18T01:00:00+08:00', 'E_FETCH A: one')
    RUN.append_failure(f16, 'https://a.example/1',
                       '2026-11-18T02:00:00+08:00', 'E_FETCH A: again')
    RUN.append_failure(f16, 'https://a.example/1', TODAY + 'T03:00:00+08:00',
                       'E_FETCH A: today')
    trend16 = RUN.summarize_failure_trend(h16, f16, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN11', trend16['today'] == 1 and trend16['prev'] == 2
       and trend16['delta'] == -1 and trend16['mean'] == 1.5
       and trend16['worst'] == ('2026-11-18', 2)
       and trend16['recurring'] == 1 and trend16['sources'] == 1,
       'two days read today=1 prev=2 delta=-1 mean=1.5, worst on the harder day')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc18 = RUN.main(['--failure-trend', '--root', root16, '--at', AT])
    line18 = buf.getvalue().strip()
    ok('AC-RUN11', rc18 == 0 and 'days=2' in line18 and 'mean=1.5' in line18
       and 'worst=2026-11-18:2' in line18 and 'recurring=1 sources=1' in line18,
       'the printed line names the harder day and the recurrence')
    root17 = world(); roots.append(root17)
    h17 = RUN.failure_day_path(root17)
    f17 = RUN.failure_path(root17)
    for hour in ('01', '02', '03'):
        RUN.append_failure(f17, 'https://b.example/2',
                           TODAY + 'T%s:00:00+08:00' % hour, 'E_FETCH B: same day')
    RUN.snapshot_failure_day(root17, TODAY + 'T20:00:00+08:00')
    t17 = RUN.summarize_failure_trend(h17, f17, TODAY + 'T21:00:00+08:00')
    ok('AC-RUN11', t17['today'] == 3 and t17['recurring'] == 0
       and t17['sources'] == 1 and t17['prev'] == 'none'
       and t17['delta'] == 'none',
       'three failures by one source on one day are no recurrence')
    t17b = RUN.summarize_failure_trend(h17, f17, '2026-11-21T09:00:00+08:00')
    ok('AC-RUN11', t17b['today'] == 'absent' and t17b['prev'] == 3
       and t17b['delta'] == 'none',
       'a day nobody snapshotted reads absent, never a fabricated zero')
    root18 = world(); roots.append(root18)
    h18 = RUN.failure_day_path(root18)
    f18 = RUN.failure_path(root18)
    os.makedirs(os.path.dirname(h18), exist_ok=True)
    with open(h18, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps({'day': '2026-11-09', 'on_day': 9},
                            sort_keys=True, separators=(',', ':')) + '\n')
        fh.write(json.dumps({'day': TODAY, 'on_day': 1},
                            sort_keys=True, separators=(',', ':')) + '\n')
    RUN.append_failure(f18, 'https://c.example/3', '2026-11-09T01:00:00+08:00',
                       'E_FETCH C: old day')
    RUN.append_failure(f18, 'https://c.example/3', TODAY + 'T01:00:00+08:00',
                       'E_FETCH C: today')
    wide = RUN.summarize_failure_trend(h18, f18, TODAY + 'T20:00:00+08:00', 14)
    narrow = RUN.summarize_failure_trend(h18, f18, TODAY + 'T20:00:00+08:00', 7)
    ok('AC-RUN11', wide['mean'] == 5.0
       and wide['worst'] == ('2026-11-09', 9) and wide['recurring'] == 1
       and narrow['mean'] == 1.0 and narrow['worst'] == (TODAY, 1)
       and narrow['recurring'] == 0,
       'the same bytes read two ways: a day outside the window leaves mean, '
       'worst and recurrence alone')
    with open(h18, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{oops\n')
    bad_trend = RUN.summarize_failure_trend(h18, f18, TODAY + 'T20:00:00+08:00',
                                            7)
    ok('AC-RUN11', bad_trend['bad'] == 1 and bad_trend['in_window'] == 1
       and bad_trend['days'] == 2,
       'a malformed history line is counted and never becomes a day')

    # AC-RUN12 (R2995): the snapshot must run AFTER the write on the same call
    # line, so the row it lands can see the failure this very beat produced.
    # Pure string order - no launcher started, no socket opened.
    write_at12 = call_line10.find('--write')
    snap_at12 = call_line10.find('--snapshot-failures')
    ok('AC-RUN12', write_at12 > 0 and snap_at12 > write_at12,
       'the snapshot flag sits after --write on the anchored call line')
    ok('AC-RUN12', 0 < call_line10.find('--if-due') < write_at12 < snap_at12
       and '--root $Project' in call_line10,
       'the order is day gate, write, snapshot, root anchor')
    ok('AC-RUN12', try_at < call_at10 < spawn_at
       and all(byte < 128 for byte in loop_raw) and b'\r' not in loop_raw,
       'the ordered line stays inside the try, before the spawn, pure ASCII')

    # AC-RUN13 (R2996): the trend line names its own EVIDENCE and the failure
    # CLASS it saw. The defect being graded: after the side channel was pruned,
    # 'recurring=0 sources=0' read exactly like a source that never failed.
    buckets = [RUN.failure_kind(x) for x in (
        'E_FETCH TimeoutError: slow', 'E_FETCH HTTPError: 403',
        'E_FETCH URLError: <urlopen error>', 'E_FETCH gaierror: dns',
        'E_FETCH ConnectionRefusedError: x', 'E_FETCH ValueError: x', '',
        None, 'socket.timeout')]
    ok('AC-RUN13',
       buckets == ['timeout', 'http', 'urlerror', 'dns', 'refused', 'other',
                   'other', 'other', 'timeout'],
       'the class token buckets to timeout/http/urlerror/dns/refused/other')
    root19 = world(); roots.append(root19)
    h19 = RUN.failure_day_path(root19)
    f19 = RUN.failure_path(root19)
    RUN.snapshot_failure_day(root19, TODAY + 'T09:00:00+08:00')
    RUN.append_failure(f19, 'https://d.example/4', TODAY + 'T10:00:00+08:00',
                       'E_FETCH TimeoutError: one')
    RUN.append_failure(f19, 'https://d.example/5', TODAY + 'T11:00:00+08:00',
                       'E_FETCH TimeoutError: two')
    RUN.append_failure(f19, 'https://d.example/6', TODAY + 'T12:00:00+08:00',
                       'E_FETCH HTTPError: 403')
    t19 = RUN.summarize_failure_trend(h19, f19, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t19['evidence'] == 'side' and t19['kind'] == 'timeout'
       and t19['kind_count'] == 2,
       'a side channel on disk reads evidence=side with the modal class')
    root20 = world(); roots.append(root20)
    h20 = RUN.failure_day_path(root20)
    f20 = RUN.failure_path(root20)
    RUN.append_failure(f20, 'https://e.example/7', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: x')
    RUN.append_failure(f20, 'https://e.example/8', TODAY + 'T02:00:00+08:00',
                       'E_FETCH HTTPError: 500')
    t20 = RUN.summarize_failure_trend(h20, f20, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t20['kind'] == 'http' and t20['kind_count'] == 1,
       'a tie breaks on the bucket name, so two readers cannot disagree')
    root21 = world(); roots.append(root21)
    h21 = RUN.failure_day_path(root21)
    f21 = RUN.failure_path(root21)
    for hour in range(5):
        RUN.append_failure(f21, 'https://f.example/9',
                           '2026-11-09T0%d:00:00+08:00' % hour,
                           'E_FETCH HTTPError: old')
    RUN.append_failure(f21, 'https://f.example/9', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: today')
    t21 = RUN.summarize_failure_trend(h21, f21, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t21['kind'] == 'timeout' and t21['kind_count'] == 1,
       'a day outside the window never sets the modal class')
    root22 = world(); roots.append(root22)
    h22 = RUN.failure_day_path(root22)
    f22 = RUN.failure_path(root22)
    os.makedirs(os.path.dirname(h22), exist_ok=True)
    with open(h22, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps({'day': '2026-11-18', 'on_day': 3, 'total': 3,
                             'newest_at': '2026-11-18T05:00:00+08:00',
                             'newest_error': 'E_FETCH TimeoutError: gone'},
                            sort_keys=True, separators=(',', ':')) + '\n')
    t22 = RUN.summarize_failure_trend(h22, f22, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t22['evidence'] == 'history' and t22['kind'] == 'timeout'
       and t22['kind_count'] == 1 and t22['sources'] == 0
       and t22['recurring'] == 0,
       'a pruned side channel is NAMED and its zero sources stay zero')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc22 = RUN.main(['--failure-trend', '--root', root22, '--at', AT])
    line22 = buf.getvalue().strip()
    ok('AC-RUN13', rc22 == 0 and 'evidence=history' in line22
       and 'kind=timeout:1' in line22,
       'the printed line carries the degraded label and its one sample')
    root23 = world(); roots.append(root23)
    t23 = RUN.summarize_failure_trend(RUN.failure_day_path(root23),
                                      RUN.failure_path(root23),
                                      TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t23['evidence'] == 'none' and t23['kind'] == 'none'
       and t23['kind_count'] == 0,
       'neither face answers none instead of raising')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc23 = RUN.main(['--failure-trend', '--root', root23, '--at', AT])
    line23 = buf.getvalue().strip()
    ok('AC-RUN13', rc23 == 0 and 'evidence=none kind=none' in line23,
       'the CLI prints both faces on an empty world')
    root24 = world(); roots.append(root24)
    RUN.snapshot_failure_day(root24, TODAY + 'T09:00:00+08:00')
    t24 = RUN.summarize_failure_trend(RUN.failure_day_path(root24),
                                      RUN.failure_path(root24),
                                      TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t24['evidence'] == 'history' and t24['kind'] == 'none'
       and t24['kind_count'] == 0 and t24['today'] == 0,
       'a history that exists and records nothing is evidence, not silence')

    # AC-RUN14 (R2997): the recurrence line carries WEIGHT, not just a source
    # count, and an unmeasurable recurrence is named rather than reported as 0.
    root25 = world(); roots.append(root25)
    h25 = RUN.failure_day_path(root25)
    f25 = RUN.failure_path(root25)
    RUN.snapshot_failure_day(root25, TODAY + 'T09:00:00+08:00')
    RUN.append_failure(f25, 'https://g.example/1', '2026-11-18T05:00:00+08:00',
                       'E_FETCH TimeoutError: a')
    RUN.append_failure(f25, 'https://g.example/1', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: b')
    RUN.append_failure(f25, 'https://g.example/1', TODAY + 'T02:00:00+08:00',
                       'E_FETCH TimeoutError: c')
    RUN.append_failure(f25, 'https://h.example/2', TODAY + 'T03:00:00+08:00',
                       'E_FETCH HTTPError: 403')
    t25 = RUN.summarize_failure_trend(h25, f25, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN14', t25['recur'] == (1, 3) and t25['recurring'] == 1
       and t25['sources'] == 2,
       'recur names the recurring source count AND its window failures')
    root26 = world(); roots.append(root26)
    h26 = RUN.failure_day_path(root26)
    f26 = RUN.failure_path(root26)
    for hour in range(3):
        RUN.append_failure(f26, 'https://i.example/3',
                           TODAY + 'T0%d:00:00+08:00' % hour,
                           'E_FETCH TimeoutError: x')
    t26 = RUN.summarize_failure_trend(h26, f26, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN14', t26['recur'] == (0, 0) and t26['recurring'] == 0
       and t26['sources'] == 1,
       'three failures on ONE day are not a recurrence')
    root27 = world(); roots.append(root27)
    h27 = RUN.failure_day_path(root27)
    os.makedirs(os.path.dirname(h27), exist_ok=True)
    with open(h27, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps({'day': '2026-11-18', 'on_day': 2, 'total': 2,
                             'newest_at': '2026-11-18T05:00:00+08:00',
                             'newest_error': 'E_FETCH TimeoutError: gone'},
                            sort_keys=True, separators=(',', ':')) + '\n')
    t27 = RUN.summarize_failure_trend(h27, RUN.failure_path(root27),
                                      TODAY + 'T20:00:00+08:00')
    ok('AC-RUN14', t27['recur'] is None and t27['evidence'] == 'history',
       'a pruned side channel answers recur=None, never a fabricated 0:0')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc27 = RUN.main(['--failure-trend', '--root', root27, '--at', AT])
    line27 = buf.getvalue().strip()
    ok('AC-RUN14', rc27 == 0 and 'recur=none' in line27,
       'the printed line spells the unmeasured recurrence as none')
    root28 = world(); roots.append(root28)
    f28 = RUN.failure_path(root28)
    RUN.append_failure(f28, 'https://j.example/4', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: slow')
    s28 = RUN.summarize_failures(f28, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN14', s28['newest_kind'] == RUN.failure_kind(s28['newest_error'])
       and s28['newest_kind'] == 'timeout',
       '--failures reads the SAME bucket function as the trend line')
    root29 = world(); roots.append(root29)
    f29 = RUN.failure_path(root29)
    RUN.append_failure(f29, 'https://k.example/5', TODAY + 'T01:00:00+08:00',
                       'E_FETCH HTTPError: old')
    RUN.append_failure(f29, 'https://k.example/5', TODAY + 'T05:00:00+08:00',
                       'E_FETCH TimeoutError: new')
    s29 = RUN.summarize_failures(f29, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN14', s29['newest_kind'] == 'timeout',
       'the bucket follows the NEWEST failure, not the first one seen')
    root30 = world(); roots.append(root30)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc30a = RUN.main(['--failures', '--root', root30, '--at', AT])
    line30a = buf.getvalue().strip()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc30b = RUN.main(['--failure-trend', '--root', root30, '--at', AT])
    line30b = buf.getvalue().strip()
    ok('AC-RUN14', rc30a == 0 and rc30b == 0 and 'kind=none' in line30a
       and 'recur=none' in line30b,
       'an empty world answers none on both faces without raising')

    # AC-RUN15 (R2998): the trend names how much history it actually had. A
    # trimmed file used to read exactly like a repo that had just started
    # recording; the coverage fields are the only place the difference shows.
    week = ['2026-11-13', '2026-11-14', '2026-11-15', '2026-11-16',
            '2026-11-17', '2026-11-18', TODAY]
    root31 = world(); roots.append(root31)
    h31 = RUN.failure_day_path(root31)
    os.makedirs(os.path.dirname(h31), exist_ok=True)
    with open(h31, 'w', encoding='utf-8', newline='\n') as fh:
        for day in week:
            fh.write(json.dumps({'day': day, 'on_day': 1, 'total': 1},
                                sort_keys=True,
                                separators=(',', ':')) + '\n')
    t31 = RUN.summarize_failure_trend(h31, RUN.failure_path(root31),
                                      TODAY + 'T20:00:00+08:00', 7)
    ok('AC-RUN15', t31['wcov'] == (7, 7) and t31['cov'] == (week[0], TODAY),
       'a complete seven-day history reads wcov=7/7 with its own first day')

    root32 = world(); roots.append(root32)
    h32 = RUN.failure_day_path(root32)
    os.makedirs(os.path.dirname(h32), exist_ok=True)
    with open(h32, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps({'day': TODAY, 'on_day': 1, 'total': 1},
                            sort_keys=True, separators=(',', ':')) + '\n')
    t32 = RUN.summarize_failure_trend(h32, RUN.failure_path(root32),
                                      TODAY + 'T20:00:00+08:00', 7)
    ok('AC-RUN15', t32['wcov'] == (1, 7) and t32['days'] == 1
       and t32['today'] == 1 and t32['mean'] == 1.0,
       'a trimmed history answers wcov=1/7 while today/mean stay unchanged')

    t31b = RUN.summarize_failure_trend(h31, RUN.failure_path(root31),
                                       TODAY + 'T20:00:00+08:00', 3)
    ok('AC-RUN15', t31b['wcov'] == (3, 3),
       'a three-day window over seven rows of history reads wcov=3/3')

    root33 = world(); roots.append(root33)
    h33 = RUN.failure_day_path(root33)
    os.makedirs(os.path.dirname(h33), exist_ok=True)
    with open(h33, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('{not json\n')
        fh.write(json.dumps({'day': TODAY, 'on_day': 0, 'total': 0},
                            sort_keys=True, separators=(',', ':')) + '\n')
    t33 = RUN.summarize_failure_trend(h33, RUN.failure_path(root33),
                                      TODAY + 'T20:00:00+08:00', 7)
    ok('AC-RUN15', t33['wcov'] == (1, 7) and t33['bad'] == 1,
       'a malformed row is not a covered day')

    root34 = world(); roots.append(root34)
    buf34 = io.StringIO()
    with contextlib.redirect_stdout(buf34):
        rc34 = RUN.main(['--failure-trend', '--root', root34, '--at', AT])
    line34 = buf34.getvalue().strip()
    ok('AC-RUN15', rc34 == 0 and 'cov=none' in line34 and 'wcov=0/7' in line34,
       'a missing history answers cov=none wcov=0/7 without raising')

    buf35 = io.StringIO()
    with contextlib.redirect_stdout(buf35):
        rc35 = RUN.main(['--failure-trend', '--root', root31, '--days', '7', '--at', AT])
    line35 = buf35.getvalue().strip()
    scan_src = ''
    scan_path = os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan',
                             'scripts', 'scan_five_still.ps1')
    if os.path.isfile(scan_path):
        with open(scan_path, 'r', encoding='utf-8', errors='replace') as fh:
            scan_src = fh.read()
    ok('AC-RUN15', rc35 == 0
       and ('cov=%s..%s' % (week[0], TODAY)) in line35
       and 'wcov=7/7' in line35 and 'wcov' not in scan_src
       and 'crawl-failure-days' not in scan_src,
       'the CLI carries both coverage fields and stays outside the gate face')

    # AC-RUN16 (R2999): the retention exemption argued with numbers nobody
    # could check from the product. --failures now carries the file's own BODY
    # (bytes / lines) plus a DISPLAY-ONLY percentage of the group water line.
    root36 = world(); roots.append(root36)
    f36 = RUN.failure_path(root36)
    RUN.append_failure(f36, 'https://a.example/1', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: a')
    RUN.append_failure(f36, 'https://b.example/2', TODAY + 'T02:00:00+08:00',
                       'E_FETCH HTTPError: b')
    with open(f36, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{broken\n')
        fh.write('\n')
    s36 = RUN.summarize_failures(f36, TODAY)
    ok('AC-RUN16', s36['bytes'] == os.path.getsize(f36) and s36['lines'] == 4
       and s36['total'] == 2 and s36['bad'] == 1,
       'bytes equal the file on disk; lines count physical rows, malformed and blank included')
    ok('AC-RUN16', s36['lines'] - (s36['total'] + s36['bad']) == 1,
       'lines minus (total+bad) is exactly the blank-row count, so the two counts are independent')

    root37 = world(); roots.append(root37)
    s37 = RUN.summarize_failures(RUN.failure_path(root37), TODAY)
    ok('AC-RUN16', s37['bytes'] == 0 and s37['lines'] == 0
       and s37['size_gate'] == 0.0 and s37['present'] is False,
       'a missing side channel answers zero bytes and zero lines without raising')
    buf37 = io.StringIO()
    with contextlib.redirect_stdout(buf37):
        rc37 = RUN.main(['--failures', '--root', root37, '--at', AT])
    line37 = buf37.getvalue().strip()
    ok('AC-RUN16', rc37 == 0 and 'bytes=0' in line37 and 'lines=0' in line37,
       'the CLI answers rc=0 with zero size on a world that has no side channel')

    root38 = world(); roots.append(root38)
    f38 = RUN.failure_path(root38)
    os.makedirs(os.path.dirname(f38), exist_ok=True)
    target38 = RUN.SIZE_REFERENCE_BYTES // 100  # exactly one percent
    head38 = json.dumps({'source_url': 'https://p.example/1',
                         'failed_at': TODAY + 'T03:00:00+08:00',
                         'error': 'E_FETCH TimeoutError: pad'},
                        sort_keys=True, separators=(',', ':')) + '\n'
    with open(f38, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(head38)
        fh.write('x' * (target38 - len(head38) - 1) + '\n')
    s38 = RUN.summarize_failures(f38, TODAY)
    ok('AC-RUN16', s38['bytes'] == target38 and s38['size_gate'] == 1.0
       and s38['gate_ref_mb'] == 100,
       'a file padded to one hundredth of the reference line reads size_gate=1.0 against gate_ref=100MB')

    keys38 = set(s38.keys())
    buf38 = io.StringIO()
    with contextlib.redirect_stdout(buf38):
        rc38 = RUN.main(['--failures', '--root', root38, '--at', AT])
    line38 = buf38.getvalue().strip()
    ok('AC-RUN16', rc38 == 0
       and 'bytes=' in line38 and 'lines=' in line38
       and 'size_gate=' in line38 and 'gate_ref=100MB' in line38
       and not (keys38 & set(['pass', 'flag', 'verdict', 'ok', 'gate_ok']))
       and 'PASS' not in line38 and 'FLAG' not in line38,
       'one row carries size, row count and the named denominator, and carries no verdict '
       '(a file above the reference line was NOT built this arm)')

    scan_src16 = ''
    scan_path16 = os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan',
                               'scripts', 'scan_five_still.ps1')
    if os.path.isfile(scan_path16):
        with open(scan_path16, 'r', encoding='utf-8', errors='replace') as fh:
            scan_src16 = fh.read()
    census_src16 = ''
    census_path16 = os.path.join(ROOT, 'src', 'os', 'qa_writer_census.py')
    if os.path.isfile(census_path16):
        with open(census_path16, 'r', encoding='utf-8', errors='replace') as fh:
            census_src16 = fh.read()
    ok('AC-RUN16', 'crawl-failure' not in scan_src16
       and 'crawl-failure' not in census_src16
       and 'endswith(".log")' in census_src16,
       'neither the scanner nor the writer census reads either failure file')

    # AC-RUN17 (R3000): the retention exemption's OTHER half - the history file's
    # own body - finally has a face. bytes only; `lines` was measured to restate
    # days after any beat rewrite, and the >100% path is pinned as a pure
    # function instead of by building a 100MB file.
    def day_row(day, n):
        return {'day': day, 'on_day': n, 'total': n, 'recent': n, 'bad': 0,
                'urls': 1, 'newest_at': None, 'newest_error': None}

    def write_days(path, rows, junk=()):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')) + '\n')
            for text in junk:
                fh.write(text + '\n')

    root39 = world(); roots.append(root39)
    h39 = RUN.failure_day_path(root39)
    write_days(h39, [day_row('2026-11-17', 2), day_row('2026-11-18', 0),
                     day_row('2026-11-19', 1)], junk=['{broken', ''])
    s39 = RUN.summarize_failure_days(h39)
    ok('AC-RUN17', s39['bytes'] == os.path.getsize(h39)
       and s39['days'] == 3 and s39['bad'] == 1 and s39['present'] is True,
       'bytes equal the history file on disk while days counts only usable rows')

    root40 = world(); roots.append(root40)
    s40 = RUN.summarize_failure_days(RUN.failure_day_path(root40))
    buf40 = io.StringIO()
    with contextlib.redirect_stdout(buf40):
        rc40 = RUN.main(['--failure-days', '--root', root40])
    line40 = buf40.getvalue().strip()
    ok('AC-RUN17', rc40 == 0 and s40['bytes'] == 0 and s40['days'] == 0
       and s40['size_gate'] == 0.0 and s40['present'] is False
       and 'bytes=0' in line40,
       'a missing history answers zero bytes without raising, and the CLI prints it')

    root41 = world(); roots.append(root41)
    h41 = RUN.failure_day_path(root41)
    target41 = RUN.SIZE_REFERENCE_BYTES // 100  # exactly one percent
    head41 = json.dumps(day_row('2026-11-19', 0), sort_keys=True,
                        separators=(',', ':')) + '\n'
    write_days(h41, [day_row('2026-11-19', 0)])
    with open(h41, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('x' * (target41 - len(head41) - 1) + '\n')
    s41 = RUN.summarize_failure_days(h41)
    ok('AC-RUN17', os.path.getsize(h41) == target41
       and s41['size_gate'] == 1.0
       and s41['size_gate'] == RUN.size_gate_pct(os.path.getsize(h41)),
       'the history percentage is the same helper the side channel uses, not a second formula')

    ref42 = RUN.SIZE_REFERENCE_BYTES
    ok('AC-RUN17', RUN.size_gate_pct(2 * ref42) == 200.0
       and RUN.size_gate_pct(ref42) == 100.0
       and RUN.size_gate_pct(ref42 - 2000) < 100.0
       and RUN.size_gate_pct(ref42 // 1000) == 0.1,
       'the above-reference print path is pinned by a pure function; no 100MB file is built')

    root43 = world(); roots.append(root43)
    h43 = RUN.failure_day_path(root43)
    write_days(h43, [day_row('2026-11-13', 0), day_row('2026-11-14', 1),
                     day_row('2026-11-15', 0), day_row('2026-11-16', 0),
                     day_row('2026-11-17', 3), day_row('2026-11-18', 2),
                     day_row('2026-11-19', 1)])
    s43 = RUN.summarize_failure_days(h43, 3)
    ok('AC-RUN17', set(s43.keys()) == set(['days', 'bad', 'first', 'last',
                                           'dropped', 'series', 'present',
                                           'bytes', 'size_gate', 'gate_ref_mb'])
       and s43['dropped'] is None
       and s43['days'] == 7 and s43['bad'] == 0
       and s43['first'] == '2026-11-13' and s43['last'] == '2026-11-19'
       and len(s43['series']) == 3
       and s43['bytes'] == os.path.getsize(h43),
       'the added fields are purely additive and bytes covers the whole file, not the printed tail')

    scan_src17 = ''
    scan_path17 = os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan',
                               'scripts', 'scan_five_still.ps1')
    if os.path.isfile(scan_path17):
        with open(scan_path17, 'r', encoding='utf-8', errors='replace') as fh:
            scan_src17 = fh.read()
    buf43 = io.StringIO()
    with contextlib.redirect_stdout(buf43):
        rc43 = RUN.main(['--failure-days', '--root', root43, '--days', '7'])
    line43 = buf43.getvalue().strip()
    ok('AC-RUN17', rc43 == 0 and 'bytes=' in line43 and 'size_gate=' in line43
       and 'gate_ref=100MB' in line43 and 'lines=' not in line43
       and 'PASS' not in line43 and 'FLAG' not in line43
       and 'verdict' not in line43
       and 'crawl-failure' not in scan_src17,
       'one row carries body size and the named denominator, carries no physical line count, no verdict, and stays outside the scanner '
       '(the CRAWL-FAILURE-DAYS label itself contains FAIL, so that token is not the anchor)')

    root44 = world(); roots.append(root44)
    h44 = RUN.failure_day_path(root44)
    write_days(h44, [day_row('2026-11-18', 1)], junk=['{broken', ''])
    RUN.snapshot_failure_day(root44, TODAY)
    ok('AC-RUN17', (RUN.failure_file_stats(h44)['lines']
                    == RUN.summarize_failure_days(h44)['days']),
       'after one beat rewrite the physical line count equals days - the measured reason lines= is not printed')

    # AC-RUN18 (R3001): the trend could count failures and repeat them, but it
    # could not NAME the last source nor say whether that source was seen
    # succeeding since. Identity lives only in the side channel (the history row
    # stores urls=<count> on purpose), so a pruned side channel answers
    # UNMEASURED rather than "no page failed".
    def two_failures(root, first_url, first_at, second_url, second_at):
        fp = RUN.failure_path(root)
        RUN.append_failure(fp, first_url, first_at, 'E_FETCH TimeoutError: a')
        RUN.append_failure(fp, second_url, second_at, 'E_FETCH HTTPError: b')
        return fp

    rootA1 = world(); roots.append(rootA1)
    two_failures(rootA1, 'https://a.example/1', TODAY + 'T08:00:00+08:00',
                 'https://b.example/2', TODAY + 'T10:00:00+08:00')
    tA1 = RUN.summarize_failure_trend(RUN.failure_day_path(rootA1),
                                      RUN.failure_path(rootA1), TODAY,
                                      record_path=CR.record_path(rootA1))
    ok('AC-RUN18', tA1['newest_src'] == 'https://b.example/2'
       and tA1['since_ok'] == 'unmeasured',
       'the latest failure by time names its source; no record face means the repair question is UNMEASURED')

    rootA2 = world(); roots.append(rootA2)
    two_failures(rootA2, 'https://a.example/1', TODAY + 'T08:00:00+08:00',
                 'https://b.example/2', TODAY + 'T10:00:00+08:00')
    CR.append_record(CR.record_path(rootA2), 'https://b.example/2',
                     TODAY + 'T11:00:00+08:00', 'no-drift')
    tA2 = RUN.summarize_failure_trend(RUN.failure_day_path(rootA2),
                                      RUN.failure_path(rootA2), TODAY,
                                      record_path=CR.record_path(rootA2))
    ok('AC-RUN18', tA2['newest_src'] == 'https://b.example/2'
       and tA2['since_ok'] == 'yes',
       'a later successful row for that source reads since_ok=yes')

    rootA3 = world(); roots.append(rootA3)
    two_failures(rootA3, 'https://a.example/1', TODAY + 'T08:00:00+08:00',
                 'https://b.example/2', TODAY + 'T10:00:00+08:00')
    CR.append_record(CR.record_path(rootA3), 'https://b.example/2',
                     TODAY + 'T09:00:00+08:00', 'no-drift')
    tA3 = RUN.summarize_failure_trend(RUN.failure_day_path(rootA3),
                                      RUN.failure_path(rootA3), TODAY,
                                      record_path=CR.record_path(rootA3))
    ok('AC-RUN18', tA3['since_ok'] == 'unmeasured'
       and tA3['rcov'] == (TODAY, TODAY),
       'a success only BEFORE the last failure is not a repair - and R3004 makes it UNMEASURED rather than "no", because the record never looked after that failure')

    rootA4 = world(); roots.append(rootA4)
    two_failures(rootA4, 'https://a.example/1', TODAY + 'T08:00:00+08:00',
                 'https://b.example/2', TODAY + 'T10:00:00+08:00')
    tA4 = RUN.summarize_failure_trend(
        RUN.failure_day_path(rootA4), RUN.failure_path(rootA4), TODAY,
        record_path=os.path.join(rootA4, 'nope.jsonl'))
    ok('AC-RUN18', tA4['newest_src'] == 'https://b.example/2'
       and tA4['since_ok'] == 'unmeasured',
       'a missing record file answers UNMEASURED while identity still comes from the side channel')

    rootA5 = world(); roots.append(rootA5)
    write_days(RUN.failure_day_path(rootA5), [day_row('2026-11-19', 0)])
    tA5 = RUN.summarize_failure_trend(RUN.failure_day_path(rootA5),
                                      RUN.failure_path(rootA5), TODAY,
                                      record_path=CR.record_path(rootA5))
    base_keys = set(['days', 'in_window', 'bad', 'today', 'prev', 'mean',
                     'delta', 'worst', 'recurring', 'sources', 'recur', 'cov',
                     'wcov', 'evidence', 'kind', 'kind_count', 'window_days'])
    ok('AC-RUN18', tA5['newest_src'] is None and tA5['since_ok'] == 'unmeasured'
       and set(tA5.keys()) == base_keys | set(['newest_src', 'since_ok', 'flips',
                                               'pending', 'pending_src',
                                               'pending_age_d',
                                               'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
       and tA5['evidence'] == 'history' and tA5['today'] == 0,
       'a pruned side channel answers none/unmeasured and leaves every existing field where it was')

    rootA6 = world(); roots.append(rootA6)
    fpA6 = RUN.failure_path(rootA6)
    RUN.append_failure(fpA6, 'https://b.example/2', TODAY + 'T10:00:00+08:00',
                       'E_FETCH HTTPError: new first in file')
    RUN.append_failure(fpA6, 'https://a.example/1', TODAY + 'T08:00:00+08:00',
                       'E_FETCH TimeoutError: old second in file')
    tA6 = RUN.summarize_failure_trend(RUN.failure_day_path(rootA6), fpA6, TODAY,
                                      record_path=CR.record_path(rootA6))
    ok('AC-RUN18', tA6['newest_src'] == 'https://b.example/2',
       'the latest failure is chosen by time, not by the order rows sit in the file')

    bufA7 = io.StringIO()
    with contextlib.redirect_stdout(bufA7):
        rcA7 = RUN.main(['--failure-trend', '--root', rootA2, '--at', AT])
    lineA7 = bufA7.getvalue().strip()
    scan_src18 = ''
    scan_path18 = os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan',
                               'scripts', 'scan_five_still.ps1')
    if os.path.isfile(scan_path18):
        with open(scan_path18, 'r', encoding='utf-8', errors='replace') as fh:
            scan_src18 = fh.read()
    ok('AC-RUN18', rcA7 == 0 and 'newest_src=https://b.example/2' in lineA7
       and 'since_ok=yes' in lineA7
       and 'PASS' not in lineA7 and 'FLAG' not in lineA7
       and 'verdict' not in lineA7
       and 'crawl-failure' not in scan_src18,
       'one display row carries identity and the repair reading, carries no verdict, and stays outside the scanner')

    # AC-RUN19 (R3002): "is it fixed now" and "does it stay fixed" read the same
    # on the R3001 line - measured before the code: a stable repair (fail, ok)
    # and a source fixed, broken and fixed again (fail, ok, fail, ok) BOTH print
    # since_ok=yes with recur=(0,0). flips= counts success -> failure transitions
    # for the newest source on the merged timeline of the two faces already on
    # disk; it is display-only and unmeasured wherever since_ok is.
    def flips_world(fail_times, ok_times):
        root = world()
        roots.append(root)
        for when in fail_times:
            RUN.append_failure(RUN.failure_path(root), SRC19, TODAY + 'T' + when,
                               'E_FETCH TimeoutError: x')
        for when in ok_times:
            CR.append_record(CR.record_path(root), SRC19, TODAY + 'T' + when,
                             'no-drift')
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    SRC19 = 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682'

    _rB1, tB1 = flips_world(['08:00:00+08:00'], ['09:00:00+08:00'])
    ok('AC-RUN19', tB1['flips'] == 0 and tB1['since_ok'] == 'yes',
       'a stable repair (fail, ok) answers flips=0, never read as flapping')

    _rB2, tB2 = flips_world(['08:00:00+08:00', '10:00:00+08:00'],
                            ['09:00:00+08:00', '11:00:00+08:00'])
    ok('AC-RUN19', tB2['flips'] == 1 and tB2['since_ok'] == 'yes',
       'fixed, broken again and fixed again reads since_ok=yes AND flips=1 - the pair this round separates')

    _rB3, tB3 = flips_world(['08:00:00+08:00', '08:30:00+08:00'],
                            ['09:00:00+08:00'])
    ok('AC-RUN19', tB3['flips'] == 0 and tB3['since_ok'] == 'yes',
       'two failures before the first success never worked in between, so no flip is invented')

    _rB4, tB4 = flips_world(['08:00:00+08:00', '09:00:00+08:00'],
                            ['08:30:00+08:00'])
    ok('AC-RUN19', tB4['flips'] == 1 and tB4['recur'] == (0, 0)
       and tB4['recurring'] == 0,
       'same-day flapping is one flip while recur stays 0:0 - two different questions')

    _rB5, _t = flips_world(['08:00:00+08:00'], [])
    CR.append_record(CR.record_path(_rB5),
                     'https://other.example/page',
                     TODAY + 'T09:00:00+08:00', 'no-drift')
    tB5 = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rB5), RUN.failure_path(_rB5), TODAY,
        record_path=CR.record_path(_rB5))
    ok('AC-RUN19', tB5['flips'] == 0 and tB5['since_ok'] == 'no'
       and os.path.isfile(CR.record_path(_rB5)),
       'a record file that holds no row for the source answers 0, measured rather than missing')

    _rB6, tB6 = flips_world(['08:00:00+08:00', '10:00:00+08:00'], [])
    tB6b = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rB6), RUN.failure_path(_rB6), TODAY,
        record_path=os.path.join(_rB6, 'nope.jsonl'))
    sideB6 = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rB6), os.path.join(_rB6, 'no-side.jsonl'), TODAY,
        record_path=CR.record_path(_rB6))
    ok('AC-RUN19', tB6b['flips'] is None and tB6b['since_ok'] == 'unmeasured'
       and sideB6['flips'] is None and sideB6['since_ok'] == 'unmeasured',
       'a missing record file and a pruned side channel both answer UNMEASURED, never 0')

    _rB7, tB7 = flips_world(['10:00:00+08:00'], ['10:00:00+08:00'])
    ok('AC-RUN19', tB7['flips'] == 0 and tB7['since_ok'] == 'unmeasured',
       'a success and a failure on the same second are never ordered into an invented flip, and R3004 refuses to call the same second "looking afterwards" (unmeasured)')

    _rB8, tB8 = flips_world(['08:00:00+08:00', '10:00:00+08:00'],
                            ['09:00:00+08:00'])
    ok('AC-RUN19', tB8['flips'] == 1 and tB8['newest_src'] == SRC19
       and tB8['since_ok'] == 'unmeasured',
       'the newest failure is taken by time, so the flip before it still counts - and R3004 lets flips stay measured while the now-question is unmeasured')

    baseB = set(['days', 'in_window', 'bad', 'today', 'prev', 'mean', 'delta',
                 'worst', 'recurring', 'sources', 'recur', 'cov', 'wcov',
                 'evidence', 'kind', 'kind_count', 'newest_src', 'since_ok',
                 'window_days'])
    bufB9 = io.StringIO()
    with contextlib.redirect_stdout(bufB9):
        rcB9 = RUN.main(['--failure-trend', '--root', _rB2, '--at', AT])
    lineB9 = bufB9.getvalue().strip()
    ok('AC-RUN19', rcB9 == 0 and 'flips=1' in lineB9
       and 'since_ok=yes' in lineB9 and 'PASS' not in lineB9
       and 'FLAG' not in lineB9 and 'verdict' not in lineB9
       and 'crawl-failure' not in scan_src18
       and set(tB2.keys()) == baseB | set(['flips', 'pending', 'pending_src',
                                           'pending_age_d',
                                           'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov']),
       'one display row carries the stability count, adds exactly one key, and stays outside the scanner')

    # AC-RUN20 (R3003): the trend answered "was it seen working afterwards" but
    # never "how far did the record it read actually reach" - measured before
    # this existed: a record stopping BEFORE the failure and one covering the
    # days after (through another source) printed the SAME row. rcov= names the
    # span; the verdict itself is deliberately left where it was.
    def rcov_world(record_rows, failure_rows, history_rows):
        root = world()
        roots.append(root)
        for row in record_rows:
            CR.append_record(CR.record_path(root), row[0], row[1], row[2])
        for row in failure_rows:
            RUN.append_failure(RUN.failure_path(root), row[0], row[1], row[2])
        write_days(RUN.failure_day_path(root), history_rows)
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    SRC20 = 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682'
    OTHER20 = 'https://other.example/page'
    FAILED20 = '2026-11-18T09:00:00+08:00'

    # arm 1: a record covering the days after the failure
    _rC1, tC1 = rcov_world(
        [(SRC20, '2026-11-18T08:00:00+08:00', 'no-drift'),
         (OTHER20, '2026-11-19T10:00:00+08:00', 'no-drift')],
        [(SRC20, FAILED20, 'E_FETCH TimeoutError: x')],
        [day_row('2026-11-18', 1)])
    ok('AC-RUN20', tC1['rcov'] == ('2026-11-18', '2026-11-19'),
       'the span names both days the record actually reaches, sorted by day')

    # arm 2: the record STOPS before the failure - the span shows it, and R3004
    # makes the verdict unmeasured instead of claiming the source is still broken
    _rC2, tC2 = rcov_world(
        [(SRC20, '2026-11-17T10:00:00+08:00', 'no-drift')],
        [(SRC20, FAILED20, 'E_FETCH TimeoutError: x')],
        [day_row('2026-11-18', 1)])
    ok('AC-RUN20', tC2['rcov'] == ('2026-11-17', '2026-11-17')
       and tC2['since_ok'] == 'unmeasured',
       'a record ending before the failure shows a span that stops there, and since R3004 the verdict is unmeasured rather than a claim')

    # arm 3: no record file at all
    _rC3, tC3 = rcov_world(
        [],
        [(SRC20, FAILED20, 'E_FETCH TimeoutError: x')],
        [day_row('2026-11-18', 1)])
    ok('AC-RUN20', tC3['rcov'] is None and tC3['since_ok'] == 'unmeasured',
       'no record file answers none - a span from no rows would be invented')

    # arm 4: a zero-byte record file is present and still answers none
    _rC4, _tC4 = rcov_world([], [], [day_row('2026-11-18', 1)])
    open(CR.record_path(_rC4), 'w').close()
    tC4 = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rC4), RUN.failure_path(_rC4), TODAY,
        record_path=CR.record_path(_rC4))
    ok('AC-RUN20', tC4['rcov'] is None and os.path.isfile(CR.record_path(_rC4))
       and os.path.getsize(CR.record_path(_rC4)) == 0,
       'a present but empty record answers none - coverage is measured, not assumed from existence')

    # arm 5: malformed rows neither widen nor invent a span
    _rC5, _tC5 = rcov_world(
        [(SRC20, '2026-11-18T08:00:00+08:00', 'no-drift'),
         (OTHER20, '2026-11-19T10:00:00+08:00', 'no-drift')],
        [], [day_row('2026-11-18', 0)])
    with open(CR.record_path(_rC5), 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{"fetched_at":"2027-01-01T00:00:00+08:00",\n')
    tC5 = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rC5), RUN.failure_path(_rC5), TODAY,
        record_path=CR.record_path(_rC5))
    _rC5b, _tC5b = rcov_world([], [], [day_row('2026-11-18', 0)])
    with open(CR.record_path(_rC5b), 'w', encoding='utf-8',
              newline='\n') as fh:
        fh.write('not json at all\n')
    tC5b = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rC5b), RUN.failure_path(_rC5b), TODAY,
        record_path=CR.record_path(_rC5b))
    ok('AC-RUN20', tC5['rcov'] == ('2026-11-18', '2026-11-19')
       and tC5b['rcov'] is None,
       'a broken line cannot stretch the span, and a file of nothing but broken lines has no span')

    # arm 6: cov (history face) and rcov (record face) answer from different
    # files in the same world - neither reading may explain the other
    _rC6, tC6 = rcov_world(
        [(SRC20, '2026-11-19T10:00:00+08:00', 'no-drift')],
        [], [day_row('2026-11-13', 0), day_row('2026-11-19', 0)])
    ok('AC-RUN20', tC6['cov'] == ('2026-11-13', '2026-11-19')
       and tC6['rcov'] == ('2026-11-19', '2026-11-19'),
       'the history spans six days while the record spans one - two faces, two answers')

    # arm 7: one CLI row carries rcov=, adds exactly one key, stays outside the
    # scanner; a missing record prints none rather than dropping the field
    bufC7 = io.StringIO()
    with contextlib.redirect_stdout(bufC7):
        rcC7 = RUN.main(['--failure-trend', '--root', _rC1, '--at', AT])
    lineC7 = bufC7.getvalue().strip()
    bufC8 = io.StringIO()
    with contextlib.redirect_stdout(bufC8):
        rcC8 = RUN.main(['--failure-trend', '--root', _rC3, '--at', AT])
    lineC8 = bufC8.getvalue().strip()
    ok('AC-RUN20', rcC7 == 0 and 'rcov=2026-11-18..2026-11-19' in lineC7
       and rcC8 == 0 and 'rcov=none' in lineC8
       and 'PASS' not in lineC7 and 'FLAG' not in lineC7
       and 'verdict' not in lineC7
       and 'crawl-failure' not in scan_src18
       and set(tC1.keys()) == baseB | set(['flips', 'pending', 'pending_src',
                                           'pending_age_d',
                                           'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov']),
       'the row names the record span, or none, and adds exactly the one key it names')

    # AC-RUN21 (R3004): the verdict answered 'no' without ever having looked.
    # Measured before the code: a zero-byte record, a record whose newest row
    # predates the failure and a success in the SAME second all answered 'no',
    # so "we looked and it is still broken" and "we never looked" were one word.
    # The law now: 'no' requires the record to reach STRICTLY past the failure
    # stamp, through ANY source, because the pipeline fetching another page
    # afterwards is what proves the pipeline ran.
    SRC21 = 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682'
    OTHER21 = 'https://other.example/page'

    def trend21(record_rows, failure_rows, empty_record=False, junk=None):
        root = world()
        roots.append(root)
        for url, when, verdict in record_rows:
            CR.append_record(CR.record_path(root), url, when, verdict)
        for url, when, err in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        if empty_record:
            open(CR.record_path(root), 'w').close()
        if junk is not None:
            with open(CR.record_path(root), 'w', encoding='utf-8',
                      newline='\n') as fh:
                fh.write(junk + '\n')
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    FAIL10 = [(SRC21, TODAY + 'T10:00:00+08:00', 'E_FETCH TimeoutError: x')]

    _rD1, tD1 = trend21([], FAIL10, empty_record=True)
    ok('AC-RUN21', tD1['since_ok'] == 'unmeasured' and tD1['rcov'] is None
       and tD1['flips'] == 0 and os.path.getsize(CR.record_path(_rD1)) == 0,
       'a zero-byte record cannot answer "still broken": zero observations read unmeasured, and flips=0 stays a count rather than a verdict')

    _rD2, tD2 = trend21([(SRC21, TODAY + 'T08:00:00+08:00', 'no-drift')], FAIL10)
    ok('AC-RUN21', tD2['since_ok'] == 'unmeasured' and tD2['flips'] == 1
       and tD2['rcov'] == (TODAY, TODAY),
       'a record stopping before the failure answers unmeasured while flips stays measured - one flip was already on disk')

    _rD3, tD3 = trend21([(OTHER21, TODAY + 'T11:00:00+08:00', 'no-drift')],
                        FAIL10)
    ok('AC-RUN21', tD3['since_ok'] == 'no',
       'a record that fetched ANOTHER page after the failure proves the pipeline looked, so the source not coming back is finally a real "no"')

    _rD4, tD4 = trend21([(SRC21, TODAY + 'T10:00:00+08:00', 'no-drift')], FAIL10)
    ok('AC-RUN21', tD4['since_ok'] == 'unmeasured',
       'a success in the same second as the failure is not "looking afterwards" - unmeasured rather than an invented order')

    _rD5, tD5 = trend21([], FAIL10, junk='not json at all')
    ok('AC-RUN21', tD5['since_ok'] == 'unmeasured',
       'a record of nothing but malformed rows has zero usable observations, so it cannot claim the source is broken')

    # the split is a property of coverage, not of the outcome: the same world
    # gains ONE row for another source and the verdict moves unmeasured -> no
    _rD6, tD6 = trend21(
        [(SRC21, TODAY + 'T08:00:00+08:00', 'no-drift'),
         (OTHER21, TODAY + 'T11:00:00+08:00', 'no-drift')], FAIL10)
    ok('AC-RUN21', tD6['since_ok'] == 'no' and tD2['since_ok'] == 'unmeasured',
       'one extra row for another source moves the same source from unmeasured to no - measurability comes from the pipeline, not from luck')

    _rD7, tD7 = trend21([(SRC21, TODAY + 'T11:00:00+08:00', 'no-drift')], FAIL10)
    bufD7 = io.StringIO()
    with contextlib.redirect_stdout(bufD7):
        rcD7 = RUN.main(['--failure-trend', '--root', _rD3, '--at', AT])
    lineD7 = bufD7.getvalue().strip()
    ok('AC-RUN21', tD7['since_ok'] == 'yes' and rcD7 == 0
       and 'since_ok=no' in lineD7 and 'flips=' in lineD7
       and 'rcov=' in lineD7 and 'PASS' not in lineD7
       and 'FLAG' not in lineD7 and 'verdict' not in lineD7
       and 'crawl-failure' not in scan_src18
       and set(tD3.keys()) == baseB | set(['flips', 'pending', 'pending_src',
                                           'pending_age_d',
                                           'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov']),
       'a real repair still reads yes, the CLI carries all three readings, and R3004 adds NO key - the row shape is unchanged')

    # AC-RUN22 (R3005): newest_src/since_ok answer for ONE source - the latest
    # failure in the window - so with three failing pages the other two were
    # counts without a verdict (measured: A repaired, B and C gone, the row
    # named only C). pending=<no>/<judged> answers for the whole window; it
    # counts only sources the record shows were looked at and never came back,
    # over only those that could be judged at all. Printing one line per source
    # was refused: the one-line contract is what the CLI and its arms rest on.
    SRC22A = 'https://a.example/page'
    SRC22B = 'https://b.example/page'
    SRC22C = 'https://c.example/page'
    OTHER22 = 'https://other.example/page'

    def trend22(record_rows, failure_rows):
        root = world()
        roots.append(root)
        for url, when in record_rows:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when, err in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    # arm 1: three sources, three different repair states
    rE1, tE1 = trend22(
        [(SRC22A, TODAY + 'T09:30:00+08:00'),
         (OTHER22, TODAY + 'T11:30:00+08:00')],
        [(SRC22A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
         (SRC22B, TODAY + 'T10:00:00+08:00', 'E_FETCH HTTPError: b'),
         (SRC22C, TODAY + 'T11:00:00+08:00', 'E_FETCH URLError: c')])
    ok('AC-RUN22', tE1['pending'] == (2, 3) and tE1['newest_src'] == SRC22C
       and tE1['since_ok'] == 'no' and tE1['sources'] == 3,
       'three failing sources: pending counts the two shown looked-at and never back over the three judged, while newest_src still answers for one')

    # arm 2: an UNMEASURED source is in neither number - the not-yes rule is
    # measured to be wrong here, not argued about
    rE2, tE2 = trend22(
        [(SRC22A, TODAY + 'T10:00:00+08:00')],
        [(SRC22A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
         (SRC22B, TODAY + 'T12:00:00+08:00', 'E_FETCH HTTPError: b')])
    notyes22 = [RUN._since_ok(CR.record_path(rE2), s, w) for s, w in
                ((SRC22A, TODAY + 'T09:00:00+08:00'),
                 (SRC22B, TODAY + 'T12:00:00+08:00'))]
    notyes22 = sum(1 for v in notyes22 if v != 'yes')
    ok('AC-RUN22', tE2['pending'] == (0, 1) and notyes22 == 1,
       'a source whose newest failure is later than every record row is UNMEASURED, so it is neither pending nor judged - the since_ok != yes numerator would have counted it as 1 pending here')

    # arm 3: recur and pending answer different questions (direction one)
    rE3, tE3 = trend22(
        [(OTHER22, TODAY + 'T11:00:00+08:00')],
        [(SRC22A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')])
    ok('AC-RUN22', tE3['recur'] == (0, 0) and tE3['pending'] == (1, 1),
       'one source failing on one day is no recurrence (recur=(0,0)) yet it is one judged source that never came back - two readings, two answers')

    # arm 4: and the other direction - recurrence without anything pending
    rE4, tE4 = trend22(
        [(SRC22A, TODAY + 'T09:30:00+08:00'),
         (SRC22B, TODAY + 'T10:30:00+08:00'),
         (OTHER22, TODAY + 'T11:00:00+08:00')],
        [(SRC22A, '2026-11-18T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
         (SRC22A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
         (SRC22B, '2026-11-18T10:00:00+08:00', 'E_FETCH HTTPError: b'),
         (SRC22B, TODAY + 'T10:00:00+08:00', 'E_FETCH HTTPError: b')])
    ok('AC-RUN22', tE4['recur'] == (2, 4) and tE4['pending'] == (0, 2),
       'two sources failing on two days each is recur=(2,4), and with both seen working again nothing is pending - recurrence is not repair')

    # arm 5: each source is judged on its OWN latest failure, so a repair
    # before today failure cannot be reported as today repair
    rE5, tE5 = trend22(
        [(SRC22A, '2026-11-18T12:00:00+08:00')],
        [(SRC22A, '2026-11-18T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
         (SRC22A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')])
    ok('AC-RUN22', tE5['pending'] is None
       and tE5['rcov'] == ('2026-11-18', '2026-11-18'),
       'judging yesterday recovery as today answer would invent a repair: the record stops before the newest failure, so nothing is judged and pending=none')

    # arm 6: no judgement anywhere reads none, never 0/0
    rE6, tE6 = trend22([], [(SRC22A, TODAY + 'T09:00:00+08:00',
                             'E_FETCH TimeoutError: a')])
    junk_root = world()
    roots.append(junk_root)
    RUN.append_failure(RUN.failure_path(junk_root),
                       SRC22A, TODAY + 'T09:00:00+08:00',
                       'E_FETCH TimeoutError: a')
    write_days(RUN.failure_day_path(junk_root), [])
    with open(CR.record_path(junk_root), 'w', encoding='utf-8',
              newline='\n') as fh:
        fh.write('not json at all\n')
    tE6b = RUN.summarize_failure_trend(
        RUN.failure_day_path(junk_root), RUN.failure_path(junk_root), TODAY,
        record_path=CR.record_path(junk_root))
    empty_root = world()
    roots.append(empty_root)
    tE6s = RUN.summarize_failure_trend(
        RUN.failure_day_path(empty_root), RUN.failure_path(empty_root), TODAY,
        record_path=CR.record_path(empty_root))
    ok('AC-RUN22', tE6['pending'] is None and tE6b['pending'] is None
       and tE6s['pending'] is None and tE6s['evidence'] == 'none',
       'an absent record, a record of nothing but malformed rows and a pruned side channel all answer none - a zero-of-zero would read like "nothing is pending"')

    # arm 7: the one-line contract, the exact key set, and the scanner
    bufE7 = io.StringIO()
    with contextlib.redirect_stdout(bufE7):
        rcE7 = RUN.main(['--failure-trend', '--root', rE1, '--at', AT])
    linesE7 = [n for n in bufE7.getvalue().splitlines() if n.strip()]
    lineE7 = linesE7[0] if linesE7 else ''
    ok('AC-RUN22', rcE7 == 0 and len(linesE7) == 1
       and 'pending=2/3' in lineE7
       and 'PASS' not in lineE7 and 'FLAG' not in lineE7
       and 'verdict' not in lineE7 and 'crawl-failure' not in scan_src18
       and set(tE1.keys()) == baseB | set(['flips', 'pending', 'pending_src',
                                           'pending_age_d',
                                           'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov']),
       'a multi-source window still prints ONE line carrying pending=, adds exactly one key, and stays outside the scanner - per-source lines were refused on purpose')

    # AC-RUN23 (R3006): pending=<n>/<judged> answers HOW MANY sources are still
    # gone and never WHICH one, so a person had to guess where to start. Two
    # candidate fixes were measured before the code: an unjudged=<n> field is
    # pure arithmetic (it always equals sources minus the pending denominator -
    # measured reading 0, 1 and 2 in three worlds), and the claim that
    # pending=none and "all came back" read the same was measured FALSE
    # ('none' versus '0/2'). What landed is one NAME: the pending source waiting
    # longest, ties by url ascending, none when nothing is pending. An
    # unmeasured source is never named.
    SRC23A = 'https://a.example/page'
    SRC23B = 'https://b.example/page'
    SRC23C = 'https://c.example/page'
    OTHER23 = 'https://other.example/page'

    def trend23(record_rows, failure_rows_batches):
        root = world()
        roots.append(root)
        for url, when in record_rows:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for batch in failure_rows_batches:
            for url, when, err in batch:
                RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    # arm 1: the pending source is NOT the newest failure - naming must not be a
    # by-product of newest_src (the R3006 probe shape, measured before the pin)
    rG1, tG1 = trend23(
        [(OTHER23, TODAY + 'T09:30:00+08:00'),
         (SRC23B, TODAY + 'T12:30:00+08:00')],
        [[(SRC23A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC23B, TODAY + 'T12:00:00+08:00', 'E_FETCH HTTPError: b')]])
    ok('AC-RUN23', tG1['pending'] == (1, 2) and tG1['pending_src'] == SRC23A
       and tG1['newest_src'] == SRC23B and tG1['since_ok'] == 'yes',
       'the source that is still gone is named even though the newest failure was repaired - a name, not a side effect of newest_src')

    # arm 2: two pending sources - the one waiting longest is named
    rG2, tG2 = trend23(
        [(OTHER23, TODAY + 'T13:00:00+08:00')],
        [[(SRC23A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC23B, TODAY + 'T12:00:00+08:00', 'E_FETCH HTTPError: b')]])
    ok('AC-RUN23', tG2['pending'] == (2, 2) and tG2['pending_src'] == SRC23A,
       'with two sources pending the one whose failure is oldest is named - start where the wait is longest')

    # arm 3: an equal stamp is broken by url, so two write orders agree
    _rG3a, tG3a = trend23(
        [(OTHER23, TODAY + 'T13:00:00+08:00')],
        [[(SRC23B, TODAY + 'T10:00:00+08:00', 'E_FETCH HTTPError: b')],
         [(SRC23A, TODAY + 'T10:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    _rG3b, tG3b = trend23(
        [(OTHER23, TODAY + 'T13:00:00+08:00')],
        [[(SRC23A, TODAY + 'T10:00:00+08:00', 'E_FETCH TimeoutError: a')],
         [(SRC23B, TODAY + 'T10:00:00+08:00', 'E_FETCH HTTPError: b')]])
    ok('AC-RUN23', tG3a['pending_src'] == tG3b['pending_src'] == SRC23A
       and tG3a['pending'] == (2, 2),
       'two sources stamped the same tick name the lexicographically smaller url on both write orders - no reader has to guess')

    # arm 4: nothing pending reads none in all three shapes
    _rG4a, tG4a = trend23(
        [(SRC23A, TODAY + 'T09:30:00+08:00'),
         (SRC23B, TODAY + 'T12:30:00+08:00')],
        [[(SRC23A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC23B, TODAY + 'T12:00:00+08:00', 'E_FETCH HTTPError: b')]])
    _rG4b, tG4b = trend23(
        [], [[(SRC23A, TODAY + 'T09:00:00+08:00',
               'E_FETCH TimeoutError: a')]])
    _rG4c, tG4c = trend23(
        [(OTHER23, TODAY + 'T09:30:00+08:00')],
        [[(SRC23C, TODAY + 'T12:00:00+08:00', 'E_FETCH URLError: c')]])
    ok('AC-RUN23', tG4a['pending'] == (0, 2) and tG4a['pending_src'] is None
       and tG4b['pending'] is None and tG4b['pending_src'] is None
       and tG4c['pending'] is None and tG4c['pending_src'] is None,
       'all repaired, nothing judged and nothing but an unmeasured source all read none - an empty name is never printed as an empty string')

    # arm 5: an unmeasured source is never named - the R3004 split survives
    _rG5, tG5 = trend23(
        [(OTHER23, TODAY + 'T09:30:00+08:00')],
        [[(SRC23A, TODAY + 'T12:00:00+08:00',
           'E_FETCH TimeoutError: a')]])
    ok('AC-RUN23', tG5['pending'] is None and tG5['pending_src'] is None
       and RUN._since_ok(CR.record_path(_rG5), SRC23A,
                         TODAY + 'T12:00:00+08:00') == 'unmeasured',
       'a source nobody looked at after its failure is unmeasured, so it is neither counted nor named - naming it would revive the conflation R3004 removed')

    # arm 6: the exact key set, and the refused field never appears
    rootG6 = world()
    roots.append(rootG6)
    RUN.append_failure(RUN.failure_path(rootG6), SRC23A,
                       TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')
    write_days(RUN.failure_day_path(rootG6), [])
    tG6 = RUN.summarize_failure_trend(
        RUN.failure_day_path(rootG6), RUN.failure_path(rootG6), TODAY,
        record_path=CR.record_path(rootG6))
    judged6 = tG6['pending'][1] if tG6['pending'] else 0
    ok('AC-RUN23', set(tG6.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src', 'pending_age_d',
                                                   'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
       and 'unjudged' not in tG6
       and tG6['sources'] - judged6 == 1,
       'the row grows by exactly one name and carries no unjudged field - the unjudged count is measurable as sources minus the denominator, so a field for it would only restate two keys')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufG7 = io.StringIO()
    with contextlib.redirect_stdout(bufG7):
        rcG7 = RUN.main(['--failure-trend', '--root', rG1, '--at', AT])
    linesG7 = [n for n in bufG7.getvalue().splitlines() if n.strip()]
    lineG7 = linesG7[0] if linesG7 else ''
    ok('AC-RUN23', rcG7 == 0 and len(linesG7) == 1
       and ('pending_src=%s' % SRC23A) in lineG7
       and 'pending=1/2' in lineG7
       and 'PASS' not in lineG7 and 'FLAG' not in lineG7
       and 'verdict' not in lineG7 and 'crawl-failure' not in scan_src18,
       'a multi-source window still prints ONE line carrying pending_src=, and the scanner still reads none of it')

    # AC-RUN24 (R3007): pending_src= answered WHICH source to start with and
    # never HOW LONG it had been gone, so a source broken five minutes ago and
    # one broken a week read the same. Measured before this was written: the
    # named source's own stamp was computed inside _pending_sources and
    # discarded (the helper returned three values), and the failure summary's
    # newest_at is taken across ALL sources - in the probe world it named a
    # different source's stamp than pending_src did. pending_age_d= is therefore
    # measured against the NAMED source's own latest failure and the window day,
    # never against newest_at. The other pending sources stay counts: their
    # number is the numerator minus one (arithmetic, refused as a field) and
    # their identities need one line per source (the one-line contract refuses).
    SRC24A = 'https://a.example/page'
    SRC24B = 'https://b.example/page'

    def trend24(record_rows, failure_rows_batches):
        root = world()
        roots.append(root)
        for url, when in record_rows:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for batch in failure_rows_batches:
            for url, when, err in batch:
                RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    # arm 1: the age follows the NAME, not the newest failure
    rH1, tH1 = trend24(
        [(SRC24B, TODAY + 'T12:30:00+08:00')],
        [[(SRC24A, '2026-11-15T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC24B, TODAY + 'T12:00:00+08:00', 'E_FETCH HTTPError: b')]])
    summaryH1 = RUN.summarize_failures(RUN.failure_path(rH1), TODAY)
    ok('AC-RUN24', tH1['pending_src'] == SRC24A and tH1['pending_age_d'] == 4
       and str(summaryH1['newest_at']).startswith(TODAY),
       'the age is the named source\'s own (2026-11-15 -> 4 days) while newest_at is today - a reader taking newest_at would answer 0')

    # arm 2: same stamp, two write orders - same name and same age
    rH2a, tH2a = trend24(
        [(SRC24B, TODAY + 'T08:00:00+08:00')],
        [[(SRC24A, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC24B, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: b')]])
    rH2b, tH2b = trend24(
        [(SRC24B, TODAY + 'T08:00:00+08:00')],
        [[(SRC24B, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: b'),
          (SRC24A, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN24', tH2a['pending_src'] == tH2b['pending_src'] == SRC24A
       and tH2a['pending_age_d'] == tH2b['pending_age_d'] == 2,
       'two equal stamps name the same source and the same age whichever order the rows landed in')

    # arm 3: everything repaired - age is none, never 0
    rH3, tH3 = trend24(
        [(SRC24A, TODAY + 'T09:30:00+08:00')],
        [[(SRC24A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN24', tH3['pending'] == (0, 1) and tH3['pending_src'] is None
       and tH3['pending_age_d'] is None,
       'no pending source reads none rather than 0, because 0 would name a source that is not there')

    # arm 4: an unmeasured-only world is none too (the R3004 split holds)
    rH4, tH4 = trend24(
        [('https://seen.example/page', '2026-11-18T08:00:00+08:00')],
        [[(SRC24A, TODAY + 'T12:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN24', tH4['pending'] is None and tH4['pending_src'] is None
       and tH4['pending_age_d'] is None,
       'a source nobody looked after is neither pending nor aged - the verdict split is not aggregated away')

    # arm 5: the pure function's edges - no invented age, no invented clock
    ok('AC-RUN24', RUN._day_age(TODAY, '2026-11-21T00:00:00+08:00') is None
       and RUN._day_age('not-a-day', TODAY + 'T00:00:00+08:00') is None
       and RUN._day_age(TODAY, '') is None
       and RUN._day_age(TODAY, TODAY + 'T23:59:00+08:00') == 0
       and RUN._day_age(TODAY, '2026-11-12T01:00:00+08:00') == 7,
       'a future stamp, a malformed day and an empty stamp all answer None; same day is 0 and a week is 7')

    # arm 6: exactly one new key, and the refused fields never grew
    ok('AC-RUN24', set(tH1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
       and 'pending_others' not in tH1 and 'unjudged' not in tH1,
       'the row grows by exactly one age key, and neither refused field (pending_others arithmetic, unjudged restatement) exists')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufH7 = io.StringIO()
    with contextlib.redirect_stdout(bufH7):
        rcH7 = RUN.main(['--failure-trend', '--root', rH1, '--at', AT])
    linesH7 = [n for n in bufH7.getvalue().splitlines() if n.strip()]
    lineH7 = linesH7[0] if linesH7 else ''
    bufH7b = io.StringIO()
    with contextlib.redirect_stdout(bufH7b):
        rcH7b = RUN.main(['--failure-trend', '--root', rH3, '--at', AT])
    linesH7b = [n for n in bufH7b.getvalue().splitlines() if n.strip()]
    lineH7b = linesH7b[0] if linesH7b else ''
    ok('AC-RUN24', rcH7 == 0 and len(linesH7) == 1 and 'pending_age_d=4' in lineH7
       and rcH7b == 0 and len(linesH7b) == 1 and 'pending_age_d=none' in lineH7b
       and 'PASS' not in lineH7 and 'FLAG' not in lineH7
       and 'verdict' not in lineH7 and 'crawl-failure' not in scan_src18,
       'one line carries pending_age_d= (a number, or none when nothing is pending), and the scanner still reads none of it')

    # AC-RUN25 (R3008): pending_age_d= described the source waiting LONGEST and
    # said nothing about the rest, so with several pending sources a person
    # could not tell a burst that just started from a long tail. Measured before
    # this was written (qa/probe-R3008.log): three pending sources aged 0/2/4
    # days read pending=(3,3) pending_age_d=4 and the 0-day source appeared in
    # none of the 24 keys. A pending_age_max_d field was measured and REFUSED -
    # the named source is by construction the oldest (raw recomputation agreed),
    # so a max would restate pending_age_d. pending_age_min_d= is the NEWEST
    # pending source's own age: together with pending_age_d= it is the AGE SPAN
    # of the pending set, and when one source (or one shared stamp) is pending
    # the two coincide as a fact.
    SRC25A = 'https://a.example/page'
    SRC25B = 'https://b.example/page'
    SRC25C = 'https://c.example/page'

    def trend25(record_rows, failure_rows_batches):
        root = world()
        roots.append(root)
        for url, when in record_rows:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for batch in failure_rows_batches:
            for url, when, err in batch:
                RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    # arm 1: three pending sources - the two ages are NOT the same number
    rI1, tI1 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC25A, '2026-11-15T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC25B, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: b'),
          (SRC25C, TODAY + 'T08:00:00+08:00', 'E_FETCH HTTPError: c')]])
    ok('AC-RUN25', tI1['pending'] == (3, 3) and tI1['pending_age_d'] == 4
       and tI1['pending_age_min_d'] == 0,
       'the oldest pending source reads 4 days and the youngest (broken today) reads 0 - the second end of the span is no longer blank')

    # arm 2: one pending source - the two ages coincide, and that is the truth
    rI2, tI2 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC25A, '2026-11-15T09:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN25', tI2['pending'] == (1, 1) and tI2['pending_age_d'] == 4
       and tI2['pending_age_min_d'] == 4,
       'with one pending source both ends read 4 - the coincidence is pinned as a fact so it is never silently turned into None')

    # arm 3: everything repaired - both ages are none, never 0
    rI3, tI3 = trend25(
        [(SRC25A, TODAY + 'T09:30:00+08:00')],
        [[(SRC25A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN25', tI3['pending'] == (0, 1) and tI3['pending_age_d'] is None
       and tI3['pending_age_min_d'] is None,
       'no pending source reads none at both ends, because 0 would name a source that is not there')

    # arm 4: an unmeasured-only world is none too (the R3004 split holds)
    rI4, tI4 = trend25(
        [('https://seen.example/page', '2026-11-18T08:00:00+08:00')],
        [[(SRC25A, TODAY + 'T12:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN25', tI4['pending'] is None and tI4['pending_age_d'] is None
       and tI4['pending_age_min_d'] is None,
       'a source nobody looked after is neither pending nor aged at either end - the verdict split is not aggregated away by a second age')

    # arm 5: two pending sources sharing a stamp - both ends coincide
    rI5, tI5 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC25A, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC25B, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: b')]])
    ok('AC-RUN25', tI5['pending'] == (2, 2) and tI5['pending_age_d'] == 2
       and tI5['pending_age_min_d'] == 2,
       'two pending sources that failed at the same moment read the same age at both ends')

    # arm 6: exactly one new key, and the refused fields never grew
    ok('AC-RUN25', set(tI1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
       and 'pending_age_max_d' not in tI1
       and 'pending_others' not in tI1 and 'unjudged' not in tI1,
       'the row grows by exactly one age key, and the refused max field (a restatement of pending_age_d, measured) plus the two older refusals never exist')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufI7 = io.StringIO()
    with contextlib.redirect_stdout(bufI7):
        rcI7 = RUN.main(['--failure-trend', '--root', rI1, '--at', AT])
    linesI7 = [n for n in bufI7.getvalue().splitlines() if n.strip()]
    lineI7 = linesI7[0] if linesI7 else ''
    bufI7b = io.StringIO()
    with contextlib.redirect_stdout(bufI7b):
        rcI7b = RUN.main(['--failure-trend', '--root', rI3, '--at', AT])
    linesI7b = [n for n in bufI7b.getvalue().splitlines() if n.strip()]
    lineI7b = linesI7b[0] if linesI7b else ''
    ok('AC-RUN25', rcI7 == 0 and len(linesI7) == 1
       and 'pending_age_d=4' in lineI7 and 'pending_age_min_d=0' in lineI7
       and rcI7b == 0 and len(linesI7b) == 1
       and 'pending_age_min_d=none' in lineI7b
       and 'PASS' not in lineI7 and 'FLAG' not in lineI7
       and 'verdict' not in lineI7 and 'crawl-failure' not in scan_src18,
       'one line carries both ends of the age span (numbers, or none when nothing is pending), and the scanner still reads none of it')


    # AC-RUN26 (R3009): the two ends described the span and left everything
    # between them silent, so "a burst that just started" and "an old tail with
    # one new arrival" printed the same row. Measured before this was written
    # (qa/probe-R3009.log): worlds with the same ends but different middles
    # (ages 5/3/0 versus 5/1/0) were identical on all 25 keys, and so were a
    # world with the mass old (5/5/5/0/0) and one with it new (5/0/0/0/0). A
    # pointer to the failure-day file was measured and REFUSED as the
    # alternative: that file carries a urls= COUNT and no per-source identity
    # or age. pending_age_med_d= is the middle of the pending set, nearer the
    # old end when the count is even - not the max refused in R3008, which
    # equalled pending_age_d by construction in every world.
    SRC26A = 'https://a.example/page'
    SRC26B = 'https://b.example/page'
    SRC26C = 'https://c.example/page'
    SRC26D = 'https://d.example/page'
    SRC26E = 'https://e.example/page'

    # arm 1: three pending sources - the middle is neither end's restatement
    rJ1, tJ1 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC26A, '2026-11-14T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC26B, '2026-11-16T09:00:00+08:00', 'E_FETCH TimeoutError: b'),
          (SRC26C, TODAY + 'T08:00:00+08:00', 'E_FETCH HTTPError: c')]])
    ok('AC-RUN26', tJ1['pending'] == (3, 3) and tJ1['pending_age_d'] == 5
       and tJ1['pending_age_min_d'] == 0
       and tJ1['pending_age_med_d'] == 3,
       'ages 5/3/0 read a middle of 3 while the ends read 5 and 0 - the middle is no longer blank and is neither end restated')

    # arm 2: same ends, opposite mass - the middle is what separates them
    rJ2a, tJ2a = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC26A, '2026-11-14T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC26B, '2026-11-14T10:00:00+08:00', 'E_FETCH TimeoutError: b'),
          (SRC26D, '2026-11-14T11:00:00+08:00', 'E_FETCH TimeoutError: d'),
          (SRC26E, TODAY + 'T07:00:00+08:00', 'E_FETCH TimeoutError: e'),
          (SRC26C, TODAY + 'T08:00:00+08:00', 'E_FETCH TimeoutError: c')]])
    rJ2b, tJ2b = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC26A, '2026-11-14T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC26B, TODAY + 'T05:00:00+08:00', 'E_FETCH TimeoutError: b'),
          (SRC26D, TODAY + 'T06:00:00+08:00', 'E_FETCH TimeoutError: d'),
          (SRC26E, TODAY + 'T07:00:00+08:00', 'E_FETCH TimeoutError: e'),
          (SRC26C, TODAY + 'T08:00:00+08:00', 'E_FETCH TimeoutError: c')]])
    ok('AC-RUN26', tJ2a['pending'] == tJ2b['pending'] == (5, 5)
       and tJ2a['pending_age_d'] == tJ2b['pending_age_d'] == 5
       and tJ2a['pending_age_min_d'] == tJ2b['pending_age_min_d'] == 0
       and tJ2a['pending_age_med_d'] == 5
       and tJ2b['pending_age_med_d'] == 0,
       'mass at the old end and mass at the new end are indistinguishable on the count and both ends, and the middle is exactly what tells them apart')

    # arm 3: two pending sources - the even count takes the one nearer the old
    # end, so the middle coincides with pending_age_d. Pinned as a fact.
    rJ3, tJ3 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC26A, '2026-11-14T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC26C, TODAY + 'T08:00:00+08:00', 'E_FETCH TimeoutError: c')]])
    ok('AC-RUN26', tJ3['pending'] == (2, 2) and tJ3['pending_age_d'] == 5
       and tJ3['pending_age_min_d'] == 0
       and tJ3['pending_age_med_d'] == 5,
       'with two pending sources the middle is the older one (the even-count rule), so it equals pending_age_d - the coincidence is pinned rather than silently turned into None')

    # arm 4: one pending source - all three ages coincide, which is the truth
    rJ4, tJ4 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC26A, '2026-11-14T09:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN26', tJ4['pending'] == (1, 1) and tJ4['pending_age_d'] == 5
       and tJ4['pending_age_min_d'] == 5
       and tJ4['pending_age_med_d'] == 5,
       'one pending source reads the same age at both ends and in the middle')

    # arm 5: nothing pending, and a source nobody looked after - all None
    rJ5a, tJ5a = trend25(
        [(SRC26A, TODAY + 'T09:30:00+08:00')],
        [[(SRC26A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    rJ5b, tJ5b = trend25(
        [('https://seen.example/page', '2026-11-18T08:00:00+08:00')],
        [[(SRC26A, TODAY + 'T12:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN26', tJ5a['pending'] == (0, 1)
       and tJ5a['pending_age_d'] is None
       and tJ5a['pending_age_min_d'] is None
       and tJ5a['pending_age_med_d'] is None
       and tJ5b['pending'] is None
       and tJ5b['pending_age_d'] is None
       and tJ5b['pending_age_min_d'] is None
       and tJ5b['pending_age_med_d'] is None,
       'a repaired set and an unmeasured-only set read None in the middle too - the R3004 split is not aggregated away by a third age')

    # arm 6: exactly one new key, and the refused shapes never grew
    ok('AC-RUN26', set(tJ1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
       and 'pending_age_max_d' not in tJ1
       and 'pending_hist' not in tJ1
       and 'pending_others' not in tJ1 and 'unjudged' not in tJ1,
       'the row grows by exactly one age key, and the refused max, histogram and the two older refusals never exist')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufJ7 = io.StringIO()
    with contextlib.redirect_stdout(bufJ7):
        rcJ7 = RUN.main(['--failure-trend', '--root', rJ1, '--at', AT])
    linesJ7 = [n for n in bufJ7.getvalue().splitlines() if n.strip()]
    lineJ7 = linesJ7[0] if linesJ7 else ''
    bufJ7b = io.StringIO()
    with contextlib.redirect_stdout(bufJ7b):
        rcJ7b = RUN.main(['--failure-trend', '--root', rJ5a, '--at', AT])
    linesJ7b = [n for n in bufJ7b.getvalue().splitlines() if n.strip()]
    lineJ7b = linesJ7b[0] if linesJ7b else ''
    ok('AC-RUN26', rcJ7 == 0 and len(linesJ7) == 1
       and 'pending_age_med_d=3' in lineJ7
       and 'pending_age_d=5' in lineJ7 and 'pending_age_min_d=0' in lineJ7
       and rcJ7b == 0 and len(linesJ7b) == 1
       and 'pending_age_med_d=none' in lineJ7b
       and 'PASS' not in lineJ7 and 'FLAG' not in lineJ7
       and 'verdict' not in lineJ7 and 'crawl-failure' not in scan_src18,
       'one line carries the middle (a number, or none when nothing is pending), and the scanner still reads none of it')

    # AC-RUN27 (R3010): the window decides who is counted, so a source whose
    # OWN latest failure fell before the window start left every key. Measured
    # before this was written (qa/probe-R3010.log): still-broken and repaired
    # differed only through rcov, and a side channel trimmed to the window read
    # identical to a healthy world on all 26 keys. pending_old=<n>/<judged>
    # counts only that OUTSIDE population, with its own denominator, so
    # pending= keeps meaning what sources= names; judged==0 answers None so a
    # trimmed side channel cannot read like a clean bill of health.
    SRC27A = 'https://a.example/page'
    SRC27B = 'https://b.example/page'
    SRC27K = 'https://keep.example/page'
    OLD27 = '2026-11-10T10:00:00+08:00'   # 9 days before TODAY: outside a 7-day window
    NEW27 = '2026-11-19T08:00:00+08:00'
    KEEP27 = '2026-11-19T09:00:00+08:00'

    def trend27(record_rows, failure_rows, window=7):
        root = world()
        roots.append(root)
        for url, when in record_rows:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when, err in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            window_days=window, record_path=CR.record_path(root))

    # arm 1: a still-broken source OUTSIDE the window is counted, while the
    # in-window fraction keeps its own population
    rK1, tK1 = trend27(
        [(SRC27K, KEEP27), (SRC27B, KEEP27)],
        [(SRC27A, OLD27, 'TimeoutError: t'), (SRC27B, NEW27, 'TimeoutError: t')])
    ok('AC-RUN27', tK1['pending_old'] == (1, 1)
       and tK1['pending'] == (0, 1) and tK1['sources'] == 1,
       'a source broken nine days ago and never fetched again is counted outside the window, and pending= still describes only the in-window population')

    # arm 2: the same history with that source repaired -> 0 is a MEASURED zero
    rK2, tK2 = trend27(
        [(SRC27K, KEEP27), (SRC27B, KEEP27), (SRC27A, '2026-11-11T09:00:00+08:00')],
        [(SRC27A, OLD27, 'TimeoutError: t'), (SRC27B, NEW27, 'TimeoutError: t')])
    ok('AC-RUN27', tK2['pending_old'] == (0, 1),
       'a repaired old source reads 0 of 1 judged - a measured zero, not None')

    # arm 3: side channel trimmed to the window -> nothing was looked at out
    # there, which must answer None rather than 0
    rK3, tK3 = trend27(
        [(SRC27K, KEEP27), (SRC27B, KEEP27)],
        [(SRC27B, NEW27, 'TimeoutError: t')])
    ok('AC-RUN27', tK3['pending_old'] is None,
       'a side channel holding nothing outside the window answers None, so deleting the evidence cannot read like a repair')

    # arm 4: the record stops before the old failure -> unmeasured, and the
    # R3004 split is not aggregated back by this third count
    rK4, tK4 = trend27(
        [(SRC27K, '2026-11-10T09:00:00+08:00')],
        [(SRC27A, OLD27, 'TimeoutError: t'), (SRC27B, NEW27, 'TimeoutError: t')])
    ok('AC-RUN27', tK4['pending_old'] is None,
       'an old failure nobody looked after is unmeasured, never pending, so it is in neither number')

    # arm 5: the window length is a parameter, not a constant - at 14 days the
    # same source is back INSIDE and the outside face is empty
    rK5, tK5 = trend27(
        [(SRC27K, KEEP27), (SRC27B, KEEP27)],
        [(SRC27A, OLD27, 'TimeoutError: t'), (SRC27B, NEW27, 'TimeoutError: t')],
        window=14)
    ok('AC-RUN27', tK5['pending'] == (1, 2) and tK5['pending_old'] is None,
       'with a 14-day window the same source is in-window (pending 1/2) and the outside count is None - the two fractions never overlap')

    # arm 6: exactly one new key, and no per-source face for the outside set
    ok('AC-RUN27', set(tK1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
       and 'pending_old_src' not in tK1,
       'the row grows by exactly one count key, and the refused per-source face (one line per source) never exists - R3012 later landed an AGGREGATE old age, which is the shape R3007 already allowed for the in-window population')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufK7 = io.StringIO()
    with contextlib.redirect_stdout(bufK7):
        rcK7 = RUN.main(['--failure-trend', '--root', rK1, '--at', AT])
    linesK7 = [n for n in bufK7.getvalue().splitlines() if n.strip()]
    lineK7 = linesK7[0] if linesK7 else ''
    bufK7b = io.StringIO()
    with contextlib.redirect_stdout(bufK7b):
        rcK7b = RUN.main(['--failure-trend', '--root', rK3, '--at', AT])
    linesK7b = [n for n in bufK7b.getvalue().splitlines() if n.strip()]
    lineK7b = linesK7b[0] if linesK7b else ''
    ok('AC-RUN27', rcK7 == 0 and len(linesK7) == 1
       and 'pending_old=1/1' in lineK7 and 'pending=0/1' in lineK7
       and rcK7b == 0 and len(linesK7b) == 1
       and 'pending_old=none' in lineK7b
       and 'PASS' not in lineK7 and 'FLAG' not in lineK7
       and 'verdict' not in lineK7 and 'crawl-failure' not in scan_src18,
       'one line carries pending_old= (a fraction, or none when nothing was judged), and the scanner still reads none of it')

    # AC-RUN28 (R3011): pending_old= counts over the failure side channel but
    # never said how far back that channel reaches. Measured before this was
    # written (qa/probe-R3011.log): a one-day channel and a ninety-one-day
    # channel were identical on all 27 keys - the extra row was an EARLIER
    # failure of the SAME source, so every judged fact matched. fcov=<first>..
    # <last> is the channel's own span, following the FILE and not the window.
    SRC28A = 'https://a.example/page'
    SRC28B = 'https://b.example/page'
    SRC28K = 'https://keep.example/page'
    FAR28 = '2026-08-20T10:00:00+08:00'    # 91 days before TODAY
    EDGE28 = '2026-11-12T10:00:00+08:00'   # just outside a 7-day window
    NEW28 = '2026-11-19T08:00:00+08:00'
    REC28 = [(SRC28K, '2026-11-19T09:00:00+08:00'),
             (SRC28B, '2026-11-19T09:00:00+08:00'),
             (SRC28A, '2026-11-12T12:00:00+08:00')]
    FAIL28 = [(SRC28B, NEW28, 'TimeoutError: t'),
              (SRC28A, EDGE28, 'TimeoutError: t')]

    def trend28(failure_rows, window=7, junk=()):
        root = world()
        roots.append(root)
        for url, when in REC28:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when, err in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when, err)
        if junk:
            with open(RUN.failure_path(root), 'a', encoding='utf-8',
                      newline='\n') as fh:
                for text in junk:
                    fh.write(text + '\n')
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            window_days=window, record_path=CR.record_path(root))

    # arm 1: same judged facts, different evidence length - only fcov= moves
    rL1, tL1 = trend28(FAIL28)
    rL2, tL2 = trend28(FAIL28 + [(SRC28A, FAR28, 'TimeoutError: t')])
    ok('AC-RUN28', tL1['pending_old'] == tL2['pending_old'] == (0, 1)
       and tL1['fcov'] == ('2026-11-12', '2026-11-19')
       and tL2['fcov'] == ('2026-08-20', '2026-11-19'),
       'two channels that read the same pending_old= are separated by how far back their evidence reaches')

    # arm 2: the window is a parameter; fcov follows the file, not the window
    rL2w, tL2w = trend28(FAIL28 + [(SRC28A, FAR28, 'TimeoutError: t')],
                         window=14)
    ok('AC-RUN28', tL2w['fcov'] == tL2['fcov']
       and tL2w['pending_old'] is None and tL2w['pending'] == (0, 2),
       'a 14-day window leaves fcov= byte-identical while pending_old= becomes none - it describes the file')

    # arm 3: a channel trimmed to the window narrows fcov too
    rL3, tL3 = trend28([(SRC28B, NEW28, 'TimeoutError: t')])
    ok('AC-RUN28', tL3['fcov'] == ('2026-11-19', '2026-11-19')
       and tL3['pending_old'] is None,
       'trimming the channel to the window narrows fcov= and empties the outside count')

    # arm 4: malformed rows never widen the span (they only raise the reader's
    # own bad count, which the row does NOT restate for this file)
    rL4, tL4 = trend28(
        FAIL28 + [(SRC28A, FAR28, 'TimeoutError: t')],
        junk=('garbage not json',
              json.dumps({'source_url': SRC28A,
                          'failed_at': '1999-01-01T00:00:00+08:00',
                          'error': ''})))
    bad4 = RUN.read_failures(RUN.failure_path(rL4))[1]
    ok('AC-RUN28', tL4['fcov'] == ('2026-08-20', '2026-11-19') and bad4 == 2,
       'a non-JSON line and an unusable stamp raise bad and leave the span untouched')

    # arm 5: absent, empty and all-unusable channels all answer none
    rL5 = world(); roots.append(rL5)                       # absent
    tL5 = RUN.summarize_failure_trend(RUN.failure_day_path(rL5),
                                      RUN.failure_path(rL5), TODAY,
                                      record_path=CR.record_path(rL5))
    rL6, tL6 = trend28([])                                 # empty
    rL7, tL7 = trend28([], junk=('{not json}',
                                 json.dumps({'source_url': SRC28A,
                                             'failed_at': 'nope',
                                             'error': 'x'})))
    ok('AC-RUN28', tL5['fcov'] is None and tL6['fcov'] is None
       and tL7['fcov'] is None,
       'a channel that is absent, empty or holds no usable row reads none - never an empty string or a zero-day span')

    # arm 6: exactly one new key, and no per-source reach face
    ok('AC-RUN28', set(tL1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old',
                                                   'pending_old_age_d', 'pending_old_age_min_d', 'fcov',
                                                   'rcov'])
       and 'fcov_src' not in tL1 and 'fcov_days' not in tL1,
       'the row grows by exactly one span key, and the refused per-source reach face never exists')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufL7 = io.StringIO()
    with contextlib.redirect_stdout(bufL7):
        rcL7 = RUN.main(['--failure-trend', '--root', rL2, '--at', AT])
    linesL7 = [n for n in bufL7.getvalue().splitlines() if n.strip()]
    lineL7 = linesL7[0] if linesL7 else ''
    bufL7b = io.StringIO()
    with contextlib.redirect_stdout(bufL7b):
        rcL7b = RUN.main(['--failure-trend', '--root', rL5, '--at', AT])
    linesL7b = [n for n in bufL7b.getvalue().splitlines() if n.strip()]
    lineL7b = linesL7b[0] if linesL7b else ''
    ok('AC-RUN28', rcL7 == 0 and len(linesL7) == 1
       and 'fcov=2026-08-20..2026-11-19' in lineL7
       and rcL7b == 0 and len(linesL7b) == 1
       and 'fcov=none' in lineL7b
       and 'PASS' not in lineL7 and 'FLAG' not in lineL7
       and 'verdict' not in lineL7 and 'crawl-failure' not in scan_src18,
       'one line carries fcov= (a span, or none when the channel has no usable row), and the scanner still reads none of it')

    # AC-RUN29 (R3012): pending_old= says how many sources outside the window
    # never came back, never how long they have been gone. Measured before this
    # was written (qa/probe-R3012.log): fcov.first= is the oldest failure in the
    # FILE and can belong to a source repaired long ago - a world with a
    # repaired failure on 2026-08-20 and one still gone since 2026-11-10 read
    # fcov 2026-08-20..2026-11-10, so a single age is not a restatement of it.
    # pending_old_age_d= is the still-pending old source that waited longest.
    SRC29X = 'https://x.example/page'
    SRC29Y = 'https://y.example/page'
    SRC29A = 'https://a.example/page'
    SRC29K = 'https://keep.example/page'
    OLD29 = '2026-08-20T10:00:00+08:00'    # 91 days before TODAY
    FIX29 = '2026-08-21T09:00:00+08:00'    # X repaired the next day
    MID29 = '2026-11-10T10:00:00+08:00'    # Y still gone, 9 days
    NEW29 = '2026-11-19T08:00:00+08:00'

    def trend29(failure_rows, window=7):
        root = world()
        roots.append(root)
        for url, when in ((SRC29X, FIX29), (SRC29K, '2026-11-19T09:00:00+08:00')):
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when, 'TimeoutError: t')
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            window_days=window, record_path=CR.record_path(root))

    # arm 1: the age follows the still-pending source, NOT fcov.first
    rM1, tM1 = trend29([(SRC29X, OLD29), (SRC29Y, MID29)])
    ok('AC-RUN29', tM1['pending_old'] == (1, 2)
       and tM1['pending_old_age_d'] == 9
       and tM1['fcov'] == ('2026-08-20', '2026-11-10')
       and RUN._day_age(TODAY, tM1['fcov'][0]) == 91,
       'a repaired older failure leaves fcov.first at 91 days while the source still gone reads 9 - the age is not that span restated')

    # arm 2: one old pending source - the coincidence is pinned as a fact
    rM2, tM2 = trend29([(SRC29A, OLD29)])
    ok('AC-RUN29', tM2['pending_old'] == (1, 1)
       and tM2['pending_old_age_d'] == 91
       and RUN._day_age(TODAY, '2026-08-20T10:00:00+08:00') == 91,
       'with one pending old source the age equals the only stamp it can come from - pinned rather than turned into none')

    # arm 3: every judged old source came back - none, never 0
    rM3, tM3 = trend29([(SRC29X, OLD29)])
    ok('AC-RUN29', tM3['pending_old'] == (0, 1)
       and tM3['pending_old_age_d'] is None,
       'an old population that is entirely repaired reads a zero fraction with a none age - nobody outside is pending is not a waiter aged zero')

    # arm 4: a channel trimmed to the window answers none, not zero
    rM4, tM4 = trend29([(SRC29Y, NEW29)])
    ok('AC-RUN29', tM4['pending_old'] is None
       and tM4['pending_old_age_d'] is None,
       'a channel that never recorded anything outside the window reads none, because nothing was looked at out there')

    # arm 5: the window is a parameter - a 14-day window moves Y back inside
    rM5, tM5 = trend29([(SRC29X, OLD29), (SRC29Y, MID29)], window=14)
    ok('AC-RUN29', tM5['pending_old'] == (0, 1)
       and tM5['pending_old_age_d'] is None
       and tM5['pending'] == (1, 1),
       'at fourteen days the newer old source is in-window pending while the outside population holds only a repaired one - the two populations do not overlap')

    # arm 6: exactly one new key, and none of the refused faces exist
    ok('AC-RUN29', set(tM1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old',
                                                   'pending_old_age_d', 'pending_old_age_min_d',
                                                   'fcov', 'rcov'])
       and 'pending_old_src' not in tM1
       and 'pending_old_age_med_d' not in tM1,
       'the row grows by exactly one age key, and the refused per-source and middle old faces never exist')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufM7 = io.StringIO()
    with contextlib.redirect_stdout(bufM7):
        rcM7 = RUN.main(['--failure-trend', '--root', rM1, '--at', AT])
    linesM7 = [n for n in bufM7.getvalue().splitlines() if n.strip()]
    lineM7 = linesM7[0] if linesM7 else ''
    bufM7b = io.StringIO()
    with contextlib.redirect_stdout(bufM7b):
        rcM7b = RUN.main(['--failure-trend', '--root', rM4, '--at', AT])
    linesM7b = [n for n in bufM7b.getvalue().splitlines() if n.strip()]
    lineM7b = linesM7b[0] if linesM7b else ''
    ok('AC-RUN29', rcM7 == 0 and len(linesM7) == 1
       and 'pending_old_age_d=9' in lineM7
       and rcM7b == 0 and len(linesM7b) == 1
       and 'pending_old_age_d=none' in lineM7b
       and 'PASS' not in lineM7 and 'FLAG' not in lineM7
       and 'verdict' not in lineM7 and 'crawl-failure' not in scan_src18,
       'one line carries pending_old_age_d= (a number, or none when nothing outside was pending), and the scanner still reads none of it')

    # AC-RUN30 (R3013): one age described only the longest old wait, so with two
    # old waiters the other was invisible. Measured before this was written
    # (qa/probe-R3013.log): a second waiter that failed 90 days ago and one that
    # failed 9 days ago read IDENTICAL on all 29 keys. A middle reading was
    # measured and refused - with two waiters it restates the longest age in
    # both worlds - so the row carries the YOUNGEST old waiter instead.
    SRC30A = 'https://a.example/page'
    SRC30B = 'https://b.example/page'
    SRC30C = 'https://c.example/page'
    SRC30E = 'https://e.example/page'
    SRC30K = 'https://keep.example/page'
    OLD30 = '2026-08-20T10:00:00+08:00'    # 91 days before TODAY
    NXT30 = '2026-08-21T10:00:00+08:00'    # 90 days
    MID30 = '2026-11-10T10:00:00+08:00'    # 9 days
    FIX30 = '2026-11-11T09:00:00+08:00'
    NEW30 = '2026-11-19T08:00:00+08:00'

    def trend30(failure_rows, window=7, extra_records=()):
        root = world()
        roots.append(root)
        rows = [(SRC30K, '2026-11-19T09:00:00+08:00', 'no-drift'),
                (SRC30E, FIX30, 'no-drift')] + list(extra_records)
        for url, when, verdict in rows:
            CR.append_record(CR.record_path(root), url, when, verdict)
        for url, when in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when,
                               'TimeoutError: t')
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            window_days=window, record_path=CR.record_path(root))

    # E is a repaired old row in both worlds, so fcov= is the same file span on
    # both sides and only the second waiter's own stamp differs.
    rN1, tN1 = trend30([(SRC30A, OLD30), (SRC30B, NXT30), (SRC30E, MID30)])
    rN2, tN2 = trend30([(SRC30A, OLD30), (SRC30C, MID30), (SRC30E, MID30)])

    # arm 1: the two worlds are identical except for the youngest old age
    ok('AC-RUN30', tN1['pending_old'] == tN2['pending_old'] == (2, 3)
       and tN1['pending_old_age_d'] == tN2['pending_old_age_d'] == 91
       and tN1['fcov'] == tN2['fcov']
       and tN1['pending_old_age_min_d'] == 90
       and tN2['pending_old_age_min_d'] == 9,
       'an old tail and an old tail plus a fresh dropout read the same fraction, the same longest age and the same file span - the youngest age is what separates them')

    # arm 2: three waiters - the youngest is still 9 and the middle is not a key
    rN3, tN3 = trend30([(SRC30A, OLD30), (SRC30B, NXT30), (SRC30C, MID30),
                        (SRC30E, MID30)])
    ok('AC-RUN30', tN3['pending_old'] == (3, 4)
       and tN3['pending_old_age_d'] == 91
       and tN3['pending_old_age_min_d'] == 9
       and 'pending_old_age_med_d' not in tN3,
       'with three old waiters the youngest reads the recent dropout while the middle would read 90 - and the refused middle key never exists')

    # arm 3: one old waiter - the two ages coincide, pinned as a fact
    rN4, tN4 = trend30([(SRC30A, OLD30)])
    ok('AC-RUN30', tN4['pending_old'] == (1, 1)
       and tN4['pending_old_age_d'] == 91
       and tN4['pending_old_age_min_d'] == 91,
       'with one pending old source both ages name the only waiter it can come from - pinned rather than turned into none')

    # arm 4: every shape with nothing outside reads none, never 0
    rN5, tN5 = trend30([(SRC30C, NEW30)])          # trimmed to the window
    rN6, tN6 = trend30([(SRC30E, MID30)])          # all judged old came back
    rN7 = world()
    roots.append(rN7)
    tN7 = RUN.summarize_failure_trend(
        RUN.failure_day_path(rN7), RUN.failure_path(rN7), TODAY,
        record_path=CR.record_path(rN7))
    ok('AC-RUN30', tN5['pending_old'] is None
       and tN5['pending_old_age_min_d'] is None
       and tN6['pending_old'] == (0, 1)
       and tN6['pending_old_age_min_d'] is None
       and tN7['pending_old_age_min_d'] is None,
       'a trimmed channel, a fully repaired old population and an absent channel all read none - nobody outside is pending is not a waiter aged zero')

    # arm 5: the window is a parameter - the recent dropout moves back inside
    rN8, tN8 = trend30([(SRC30A, OLD30), (SRC30C, MID30), (SRC30E, MID30)],
                       window=14)
    ok('AC-RUN30', tN8['pending_old'] == (1, 1)
       and tN8['pending_old_age_d'] == 91
       and tN8['pending_old_age_min_d'] == 91
       and tN8['pending'] == (1, 2),
       'at fourteen days the recent dropout is in-window pending while the outside population holds one waiter aged 91 - the two populations do not overlap')

    # arm 6: exactly one new key, and none of the refused faces exist
    ok('AC-RUN30', set(tN1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old',
                                                   'pending_old_age_d',
                                                   'pending_old_age_min_d',
                                                   'fcov', 'rcov'])
       and 'pending_old_age_med_d' not in tN1
       and 'pending_old_src' not in tN1
       and 'pending_old_hist' not in tN1,
       'the row grows by exactly one age key, and the refused middle, per-source and histogram faces never exist on the row')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufN7 = io.StringIO()
    with contextlib.redirect_stdout(bufN7):
        rcN7 = RUN.main(['--failure-trend', '--root', rN1, '--at', AT])
    linesN7 = [n for n in bufN7.getvalue().splitlines() if n.strip()]
    lineN7 = linesN7[0] if linesN7 else ''
    bufN7b = io.StringIO()
    with contextlib.redirect_stdout(bufN7b):
        rcN7b = RUN.main(['--failure-trend', '--root', rN7, '--at', AT])
    linesN7b = [n for n in bufN7b.getvalue().splitlines() if n.strip()]
    lineN7b = linesN7b[0] if linesN7b else ''
    ok('AC-RUN30', rcN7 == 0 and len(linesN7) == 1
       and 'pending_old_age_min_d=90' in lineN7
       and rcN7b == 0 and len(linesN7b) == 1
       and 'pending_old_age_min_d=none' in lineN7b
       and 'PASS' not in lineN7 and 'FLAG' not in lineN7
       and 'verdict' not in lineN7 and 'crawl-failure' not in scan_src18,
       'one line carries pending_old_age_min_d= (a number, or none when nothing outside is pending), and the scanner still reads none of it')

    # AC-RUN31 (R3014): with three old waiters the row gave two ends and a
    # count - "which ones" had no face. Measured before the pin
    # (qa/probe-R3014.log): two worlds whose second-oldest waiter was a
    # different source read IDENTICAL on all 30 keys, while the same computation
    # held all three witnesses and returned only the first and last. The list is
    # a SEPARATE read-only face over the SAME predicate.
    SRC31A = 'https://a.example/page'
    SRC31B = 'https://b.example/page'
    SRC31B2 = 'https://b2.example/page'
    SRC31C = 'https://c.example/page'
    SRC31D = 'https://d.example/page'
    SRC31K = 'https://keep.example/page'
    SRC31E = 'https://e.example/page'
    OLD31 = '2026-08-20T10:00:00+08:00'    # 91 days before TODAY
    NXT31 = '2026-08-21T10:00:00+08:00'    # 90 days
    MID31 = '2026-11-10T10:00:00+08:00'    # 9 days
    FIX31 = '2026-11-11T09:00:00+08:00'
    BASE31 = [(SRC31K, TODAY + 'T09:00:00+08:00', 'no-drift'),
              (SRC31E, FIX31, 'no-drift')]

    def world31(failures, records, window=7):
        root = world()
        roots.append(root)
        for url, when, verdict in records:
            CR.append_record(CR.record_path(root), url, when, verdict)
        for url, when in failures:
            RUN.append_failure(RUN.failure_path(root), url, when,
                               'TimeoutError: t')
        write_days(RUN.failure_day_path(root), [])
        trend31 = RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            window_days=window, record_path=CR.record_path(root))
        listed31 = RUN.list_pending_old(
            CR.record_path(root), RUN.failure_path(root), TODAY, window)
        return root, trend31, listed31

    def ages31(listed):
        return [w['age_d'] for w in listed['waiting']]

    def urls31(listed):
        return [w['source_url'] for w in listed['waiting']]

    def snapshot31(root):
        out = []
        for base, _dirs, files in os.walk(root):
            for name in files:
                p = os.path.join(base, name)
                out.append((os.path.relpath(p, root).replace('\\', '/'),
                            os.path.getsize(p)))
        out.sort()
        return out

    # arm 1: three waiters, all three named, oldest first - and the row keeps
    # only its two ends (the blindness this round closes)
    rW1, tW1, lW1 = world31([(SRC31A, OLD31), (SRC31B, NXT31), (SRC31C, MID31)],
                            BASE31)
    ok('AC-RUN31', urls31(lW1) == [SRC31A, SRC31B, SRC31C]
       and ages31(lW1) == [91, 90, 9]
       and tW1['pending_old'] == (3, 3)
       and tW1['pending_old_age_d'] == 91
       and tW1['pending_old_age_min_d'] == 9,
       'three old waiters are all named with their ages, while the row still carries only the two ends')

    # arm 2: the list and the row are ONE computation - same count, same ends
    rW3, tW3, lW3 = world31(
        [(SRC31A, OLD31), (SRC31B, NXT31),
         (SRC31D, '2026-09-05T10:00:00+08:00')],
        [(SRC31K, '2026-09-01T09:00:00+08:00', 'no-drift'),
         (SRC31B, '2026-08-22T09:00:00+08:00', 'no-drift')])
    ok('AC-RUN31', lW1['pending_old'] == tW1['pending_old']
       and ages31(lW1)[0] == tW1['pending_old_age_d']
       and ages31(lW1)[-1] == tW1['pending_old_age_min_d']
       and tW3['pending_old'] == (1, 2)
       and lW3['pending_old'] == (1, 2)
       and urls31(lW3) == [SRC31A],
       'the list reports the same fraction and the same two ends the row does - one predicate, not a second truth')

    # arm 3: two worlds the row cannot tell apart, separated by the middle name
    rW2, tW2, lW2 = world31([(SRC31A, OLD31), (SRC31B2, NXT31),
                             (SRC31C, MID31)], BASE31)
    ok('AC-RUN31', json.dumps(tW1, sort_keys=True) == json.dumps(
        tW2, sort_keys=True)
       and urls31(lW1)[1] == SRC31B and urls31(lW2)[1] == SRC31B2
       and ages31(lW1) == ages31(lW2),
       'two worlds identical on every row key are separated by which source the list names in the middle')

    # arm 4: a repaired old source and an unmeasured one are never listed
    rW4, tW4, lW4 = world31(
        [(SRC31B, NXT31)],
        [(SRC31K, TODAY + 'T09:00:00+08:00', 'no-drift'),
         (SRC31B, '2026-08-22T09:00:00+08:00', 'no-drift')])
    ok('AC-RUN31', tW4['pending_old'] == (0, 1)
       and lW4['pending_old'] == (0, 1) and lW4['waiting'] == []
       and SRC31B not in urls31(lW3) and SRC31D not in urls31(lW3),
       'a source that came back, and one the record never looked after, are both absent - judged is not the same as listed')

    # arm 5: no evidence out there answers none with ZERO rows, never 0/0
    rW5, tW5, lW5 = world31([(SRC31C, '2026-11-18T08:00:00+08:00')], BASE31)
    rW6 = world()
    roots.append(rW6)
    lW6 = RUN.list_pending_old(CR.record_path(rW6), RUN.failure_path(rW6),
                               TODAY)
    buf31b = io.StringIO()
    with contextlib.redirect_stdout(buf31b):
        rc31b = RUN.main(['--pending-old-list', '--root', rW6, '--at', AT])
    lines31b = [n for n in buf31b.getvalue().splitlines() if n.strip()]
    ok('AC-RUN31', tW5['pending_old'] is None and lW5['waiting'] == []
       and lW5['pending_old'] is None and lW6['waiting'] == []
       and rc31b == 0 and len(lines31b) == 1
       and 'pending_old=none' in lines31b[0],
       'a channel trimmed to the window and an absent channel both answer none with zero rows - and the CLI prints one header line, not a fabricated 0/0')

    # arm 6: deterministic order - same stamp breaks on url, two calls agree
    rW7, _tW7, lW7 = world31([(SRC31B, NXT31), (SRC31A, NXT31)], BASE31)
    lW7b = RUN.list_pending_old(CR.record_path(rW7),
                                RUN.failure_path(rW7), TODAY)
    ok('AC-RUN31', urls31(lW7) == [SRC31A, SRC31B]
       and ages31(lW7) == [90, 90]
       and json.dumps(lW7, sort_keys=True) == json.dumps(lW7b, sort_keys=True),
       'two sources sharing a stamp are ordered by url, and two calls over the same world agree byte for byte')

    # arm 7: a pure display - writes nothing, carries no verdict, and the row
    # still refuses the per-source key
    before31 = snapshot31(rW1)
    buf31 = io.StringIO()
    with contextlib.redirect_stdout(buf31):
        rc31 = RUN.main(['--pending-old-list', '--root', rW1, '--at', AT])
    after31 = snapshot31(rW1)
    lines31 = [n for n in buf31.getvalue().splitlines() if n.strip()]
    text31 = ''.join(lines31)
    ok('AC-RUN31', rc31 == 0 and before31 == after31
       and len(lines31) == 4
       and lines31[0].startswith('CRAWL-PENDING-OLD-LIST')
       and 'pending_old=3/3' in lines31[0]
       and all(n.startswith('PENDING-OLD ') for n in lines31[1:])
       and 'pending_old_src' not in tW1
       and 'PASS' not in text31 and 'FLAG' not in text31
       and 'verdict' not in text31
       and 'crawl-failure' not in scan_src18,
       'the face leaves the world byte-identical, prints a header plus one line per waiter, and neither the row nor the scanner learns a per-source key')

    # AC-RUN32 (R3015): the empty old table could not say WHY it was empty, and
    # the header could not say how far its evidence reached. Measured before the
    # pin (qa/probe-R3015.log): an absent channel, a channel trimmed to the
    # window and a channel holding an old row the record never looked after all
    # printed pending_old=none with zero rows, while a second read of the same
    # file drifted inside one call when a row was appended between reads. The
    # header now carries fcov= (the R3011 span, derived from the rows this call
    # already loaded) and, when the table is empty, reason=.
    SRC32A = 'https://a32.example/page'
    SRC32B = 'https://b32.example/page'
    SRC32C = 'https://c32.example/page'
    SRC32L = 'https://late32.example/page'
    SRC32K = 'https://keep32.example/page'
    OLD32 = '2026-08-20T10:00:00+08:00'   # 91 days
    EDGE32 = '2026-11-08T10:00:00+08:00'  # inside a 14-day window, outside 7
    MID32 = '2026-11-10T10:00:00+08:00'   # 9 days
    BASE32 = [(SRC32K, TODAY + 'T09:00:00+08:00')]

    def world32(failures, records=BASE32):
        root = world()
        roots.append(root)
        for url, when in records:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when in failures:
            RUN.append_failure(RUN.failure_path(root), url, when,
                               'TimeoutError: t')
        return root

    def listing32(root, window=7, day=TODAY):
        return RUN.list_pending_old(CR.record_path(root),
                                   RUN.failure_path(root), day, window)

    def head32(root, window=7):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--pending-old-list', '--root', root,
                           '--days', str(window), '--at', AT])
        lines = [n for n in buf.getvalue().splitlines() if n.strip()]
        return rc, lines

    def snapshot32(root):
        out = []
        for base, _dirs, files in os.walk(root):
            for name in files:
                p = os.path.join(base, name)
                out.append((os.path.relpath(p, root).replace('\\', '/'),
                            os.path.getsize(p)))
        out.sort()
        return out

    # arm 1: the header carries the channel's span - the same span a frozen
    # second read of the same file gives, and the FILE's span, not the window's
    rZ1 = world32([(SRC32A, OLD32), (SRC32B, EDGE32)])
    lZ1 = listing32(rZ1, 7)
    lZ1b = listing32(rZ1, 14)
    rcZ1, linesZ1 = head32(rZ1)
    ok('AC-RUN32', lZ1['fcov'] == lZ1b['fcov'] == ('2026-08-20', '2026-11-08')
       and lZ1['fcov'] == RUN._side_coverage(RUN.failure_path(rZ1))
       and lZ1['pending_old'] == (2, 2) and lZ1b['pending_old'] == (1, 1)
       and rcZ1 == 0 and 'fcov=2026-08-20..2026-11-08' in linesZ1[0],
       'the header names the side channel span, and that span follows the FILE (same at 7 and 14 days) while pending_old= moves')

    # arm 2: ONE read per call - a reader that appended between reads used to
    # be able to make the header claim evidence the list never judged
    rZ2 = world32([(SRC32A, OLD32), (SRC32B, EDGE32)])
    kept = {'n': 0}
    real_read = RUN.read_failures

    def reading32(path):
        rows = real_read(path)
        kept['n'] += 1
        if kept['n'] == 1:
            RUN.append_failure(path, SRC32L, TODAY + 'T08:00:00+08:00',
                               'TimeoutError: late')
        return rows

    RUN.read_failures = reading32
    try:
        lZ2 = listing32(rZ2)
    finally:
        RUN.read_failures = real_read
    late_on_disk = os.path.isfile(RUN.failure_path(rZ2)) and 'late32' in open(
        RUN.failure_path(rZ2), 'r', encoding='utf-8').read()
    ok('AC-RUN32', kept['n'] == 1 and late_on_disk
       and lZ2['fcov'] == ('2026-08-20', '2026-11-08')
       and SRC32L not in [w['source_url'] for w in lZ2['waiting']],
       'the header span comes from the rows this call loaded - an appended row on disk is never claimed and never judged')

    # arm 3: four empty shapes, each with its own name
    rE1 = world32([])
    rE2 = world32([(SRC32C, '2026-11-18T08:00:00+08:00')])
    rE3 = world32([(SRC32A, OLD32)], [(SRC32K, '2026-07-01T09:00:00+08:00')])
    rE4 = world32([(SRC32A, OLD32)],
                  BASE32 + [(SRC32A, '2026-08-21T09:00:00+08:00')])
    lE1, lE2 = listing32(rE1), listing32(rE2)
    lE3, lE4 = listing32(rE3), listing32(rE4)
    rcE4, linesE4 = head32(rE4)
    ok('AC-RUN32', lE1['reason'] == lE2['reason'] == 'no-coverage'
       and lE3['reason'] == 'unmeasured'
       and lE4['reason'] == 'all-repaired'
       and lE4['pending_old'] == (0, 1)
       and all(x['waiting'] == [] for x in (lE1, lE2, lE3, lE4))
       and rcE4 == 0 and 'reason=all-repaired' in linesE4[0],
       'nothing recorded, only-in-window and old-but-never-looked read differently now, and all-repaired keeps its 0/1')

    # arm 4: a NON-empty list carries no excuse - and its rows are unchanged
    rZ4 = world32([(SRC32A, OLD32), (SRC32B, '2026-08-21T10:00:00+08:00'),
                   (SRC32C, MID32)])
    lZ4 = listing32(rZ4)
    rcZ4, linesZ4 = head32(rZ4)
    ok('AC-RUN32', lZ4['reason'] is None
       and [w['age_d'] for w in lZ4['waiting']] == [91, 90, 9]
       and len(linesZ4) == 4 and 'reason=' not in linesZ4[0]
       and lZ4['pending_old'] == (3, 3),
       'a list with rows prints no reason, and the three waiters keep their names and ages')

    # arm 5: the row does not learn any of it
    tZ5 = RUN.summarize_failure_trend(RUN.failure_day_path(rZ4),
                                      RUN.failure_path(rZ4), TODAY,
                                      record_path=CR.record_path(rZ4))
    ok('AC-RUN32', len(tZ5) == 30 and 'reason' not in tZ5
       and 'pending_old_src' not in tZ5
       and tZ5['fcov'] == lZ4['fcov'],
       'the trend row keeps its 30 keys and learns neither reason nor a per-source key, while both faces read one span')

    # arm 6: still a pure display
    before32 = snapshot32(rZ4)
    rcZ6, linesZ6 = head32(rZ4)
    after32 = snapshot32(rZ4)
    textZ6 = ''.join(linesZ6)
    ok('AC-RUN32', rcZ6 == 0 and before32 == after32
       and 'PASS' not in textZ6 and 'FLAG' not in textZ6
       and 'verdict' not in textZ6
       and 'crawl-failure' not in scan_src18,
       'the face writes nothing, names no verdict, and the scanner still reads none of it')

    # arm 7: an unusable day is its own reason, never a fabricated 0/0
    rZ7 = world32([(SRC32A, OLD32)])
    lZ7 = RUN.list_pending_old(CR.record_path(rZ7), RUN.failure_path(rZ7),
                               '2026-13-40')
    lZ7b = RUN.list_pending_old(CR.record_path(rZ7), RUN.failure_path(rZ7),
                                '2026-13-40')
    ok('AC-RUN32', lZ7['reason'] == 'no-window'
       and lZ7['pending_old'] is None and lZ7['waiting'] == []
       and lZ7['fcov'] == ('2026-08-20', '2026-08-20')
       and json.dumps(lZ7, sort_keys=True) == json.dumps(lZ7b,
                                                         sort_keys=True),
       'an unusable day says no-window over a still-readable file span, twice the same, and never 0/0')

    # AC-RUN33 (R3016): the header described population and reach, never
    # liveness. Measured before the pin (qa/probe-R3016.log): a last failure at
    # 00:05 and one at 23:50 on the SAME day read the same dictionary and the
    # same header - while the board's own pair (stopped yesterday versus
    # written this minute) had ALREADY been separated by the day span, and a day
    # age over the newest stamp measured as a restatement of fcov's last day in
    # every probed world. So the header gains last_at (the writer's own
    # characters, to the minute, from the rows this call already loaded) and no
    # age at all.
    SRC33O = 'https://old33.example/page'
    SRC33K = 'https://keep33.example/page'
    OLD33 = '2026-08-20T10:00:00+08:00'
    PREV33 = '2026-11-18T23:50:00+08:00'
    EARLY33 = '2026-11-19T00:05:00+08:00'
    LATE33 = '2026-11-19T23:50:00+08:00'
    BASE33 = [(SRC33K, TODAY + 'T09:00:00+08:00')]

    def world33(failures, records=BASE33):
        root = world()
        roots.append(root)
        for url, when in records:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when in failures:
            RUN.append_failure(RUN.failure_path(root), url, when,
                               'TimeoutError: t')
        return root

    def listing33(root, window=7, day=TODAY):
        return RUN.list_pending_old(CR.record_path(root),
                                    RUN.failure_path(root), day, window)

    def head33(root, window=7):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--pending-old-list', '--root', root,
                           '--days', str(window), '--at', AT])
        lines = [n for n in buf.getvalue().splitlines() if n.strip()]
        return rc, lines

    def snapshot33(root):
        out = []
        for base, _dirs, files in os.walk(root):
            for name in files:
                p = os.path.join(base, name)
                out.append((os.path.relpath(p, root).replace('\\', '/'),
                            os.path.getsize(p)))
        out.sort()
        return out

    # arm 1: inside ONE day the two channels now read differently, and the
    # whole dictionary was identical apart from the new field
    rC33 = world33([(SRC33O, OLD33), ('https://c33.example/page', EARLY33)])
    rD33 = world33([(SRC33O, OLD33), ('https://d33.example/page', LATE33)])
    lC33, lD33 = listing33(rC33), listing33(rD33)
    rcC33, linesC33 = head33(rC33)
    rcD33, linesD33 = head33(rD33)
    bareC = dict(lC33)
    bareD = dict(lD33)
    bareC.pop('last_at', None)
    bareD.pop('last_at', None)
    ok('AC-RUN33', lC33['fcov'] == lD33['fcov'] == ('2026-08-20', '2026-11-19')
       and json.dumps(bareC, sort_keys=True) == json.dumps(bareD,
                                                           sort_keys=True)
       and lC33['last_at'] == '2026-11-19T00:05'
       and lD33['last_at'] == '2026-11-19T23:50'
       and rcC33 == rcD33 == 0 and linesC33[0] != linesD33[0]
       and 'last_at=2026-11-19T23:50' in linesD33[0],
       'two channels written 23h45m apart on the same day move last_at while every other key stays identical')

    # arm 2: a DIFFERENT day was already separated by the span - the old
    # capability is measured, not claimed as this round's
    rA33 = world33([(SRC33O, OLD33), ('https://a33.example/page', PREV33)])
    rB33 = world33([(SRC33O, OLD33), ('https://b33.example/page', LATE33)])
    lA33, lB33 = listing33(rA33), listing33(rB33)
    ok('AC-RUN33', lA33['fcov'] != lB33['fcov']
       and head33(rA33)[1][0] != head33(rB33)[1][0]
       and lA33['last_at'] == '2026-11-18T23:50'
       and lB33['last_at'] == '2026-11-19T23:50',
       'the cross-day pair was ALREADY separated by fcov - this field does not take credit for it')

    # arm 3: no age was invented, and the refusal stays a measured fact
    restated = all(
        RUN._day_age(TODAY, x['last_at']) == RUN._day_age(TODAY, x['fcov'][1])
        for x in (lA33, lB33, lC33, lD33))
    ok('AC-RUN33', 'wage_d' not in lD33 and 'wage_h' not in lD33
       and restated and all('wage' not in k for k in lD33),
       'no day or hour age is printed, and a day age over last_at still equals fcov last day in all four worlds')

    # arm 4: no usable row means none - never a fabricated day
    rE33 = world33([])
    rG33 = world()
    roots.append(rG33)  # no side channel at all
    rH33 = world33([])
    with open(RUN.failure_path(rH33), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('{not json}\n')
        fh.write('{"source_url": "", "failed_at": "x", "error": ""}\n')
    lE33, lG33, lH33 = listing33(rE33), listing33(rG33), listing33(rH33)
    rcH33, linesH33 = head33(rH33)
    ok('AC-RUN33', lE33['last_at'] is None and lG33['last_at'] is None
       and lH33['last_at'] is None
       and lE33['reason'] == lG33['reason'] == lH33['reason'] == 'no-coverage'
       and rcH33 == 0 and 'last_at=none' in linesH33[0],
       'empty, absent and malformed-only channels name no timestamp, keep their own reason, and print last_at=none')

    # arm 5: one header line, no excuse on a populated table, rows unchanged
    rZ33 = world33([(SRC33O, OLD33), ('https://b33b.example/page',
                                      '2026-08-21T10:00:00+08:00'),
                    ('https://c33b.example/page',
                     '2026-11-10T10:00:00+08:00')])
    lZ33 = listing33(rZ33)
    rcZ33, linesZ33 = head33(rZ33)
    ok('AC-RUN33', len(linesZ33) == 4 and 'reason=' not in linesZ33[0]
       and 'last_at=' in linesZ33[0] and lZ33['reason'] is None
       and [w['age_d'] for w in lZ33['waiting']] == [91, 90, 9]
       and lZ33['pending_old'] == (3, 3),
       'a populated table still prints one header plus three rows, no reason, and the same three ages')

    # arm 6: still ONE read per call - an append between reads is not claimed
    rS33 = world33([(SRC33O, OLD33), ('https://s33.example/page', EARLY33)])
    kept33 = {'n': 0}
    real_read33 = RUN.read_failures

    def reading33(path):
        rows = real_read33(path)
        kept33['n'] += 1
        if kept33['n'] == 1:
            RUN.append_failure(path, 'https://late33.example/page',
                               TODAY + 'T23:00:00+08:00', 'TimeoutError: late')
        return rows

    RUN.read_failures = reading33
    try:
        lS33 = listing33(rS33)
    finally:
        RUN.read_failures = real_read33
    late_on_disk33 = 'late33' in open(RUN.failure_path(rS33), 'r',
                                      encoding='utf-8').read()
    ok('AC-RUN33', kept33['n'] == 1 and late_on_disk33
       and lS33['last_at'] == '2026-11-19T00:05',
       'the stamp comes from the rows this call loaded - a row appended on disk is never claimed')

    # arm 7: pure display, the row learns nothing, and a date-only stamp is
    # echoed as a date rather than given an invented hour
    rQ33 = world33([(SRC33O, '2026-11-15')])
    lQ33 = listing33(rQ33)
    before33 = snapshot33(rZ33)
    rcZ33b, linesZ33b = head33(rZ33)
    after33 = snapshot33(rZ33)
    text33 = ''.join(linesZ33b)
    t33 = RUN.summarize_failure_trend(RUN.failure_day_path(rZ33),
                                      RUN.failure_path(rZ33), TODAY,
                                      record_path=CR.record_path(rZ33))
    ok('AC-RUN33', lQ33['last_at'] == '2026-11-15'
       and 'T' not in lQ33['last_at']
       and rcZ33b == 0 and before33 == after33
       and len(t33) == 30 and 'last_at' not in t33
       and 'PASS' not in text33 and 'FLAG' not in text33
       and 'verdict' not in text33
       and 'crawl-failure' not in scan_src18,
       'a date-only stamp stays a date, the face writes nothing, the trend row keeps its 30 keys, and the scanner reads none of it')

    # AC-RUN34 (R3017): the header carried population, reach and liveness, never
    # EVIDENCE QUALITY - `bad` sat in the dictionary from the start and the
    # header never printed it. Measured before the pin (qa/probe-R3017.log): the
    # same usable rows plus two malformed lines moved bad 0 -> 2 while fcov,
    # last_at and pending_old stayed identical and the two headers were
    # byte-equal; the strongest shape is the empty table, where a channel
    # holding only unusable lines read exactly like an absent channel. bad is
    # taken from the single read_failures call this face already makes and is
    # NOT folded into reason: measured, a populated table carries bad=2 with
    # reason None, so folding it in would force an excuse onto a non-empty list.
    SRC34O = 'https://old34.example/page'
    SRC34K = 'https://keep34.example/page'
    OLD34 = '2026-08-20T10:00:00+08:00'
    LATE34 = '2026-11-19T23:50:00+08:00'
    JUNK34 = ['{oops\n', '{"failed_at":"not-a-day","error":"x"}\n']
    BASE34 = [(SRC34K, TODAY + 'T09:00:00+08:00')]

    def world34(failures, junk=None, records=BASE34):
        root = world()
        roots.append(root)
        for url, when in records:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when in failures:
            RUN.append_failure(RUN.failure_path(root), url, when,
                               'TimeoutError: t')
        if junk:
            with open(RUN.failure_path(root), 'a', encoding='utf-8',
                      newline='\n') as fh:
                fh.write(''.join(junk))
        return root

    def listing34(root, window=7, day=TODAY):
        return RUN.list_pending_old(CR.record_path(root),
                                    RUN.failure_path(root), day, window)

    def head34(root, window=7):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--pending-old-list', '--root', root,
                           '--days', str(window), '--at', AT])
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    def snapshot34(root):
        out = []
        for base, _dirs, files in os.walk(root):
            for name in files:
                p = os.path.join(base, name)
                out.append((os.path.relpath(p, root).replace('\\', '/'),
                            os.path.getsize(p)))
        out.sort()
        return out

    # arm 1: the same usable rows, plus two unusable ones - ONLY bad moves
    rC34 = world34([(SRC34O, OLD34), ('https://c34.example/page', LATE34)])
    rX34 = world34([(SRC34O, OLD34), ('https://c34.example/page', LATE34)],
                   junk=JUNK34)
    lC34, lX34 = listing34(rC34), listing34(rX34)
    rcC34, linesC34 = head34(rC34)
    rcX34, linesX34 = head34(rX34)
    bareC34 = dict(lC34)
    bareX34 = dict(lX34)
    bareC34.pop('bad', None)
    bareX34.pop('bad', None)
    ok('AC-RUN34', lC34['bad'] == 0 and lX34['bad'] == 2
       and json.dumps(bareC34, sort_keys=True) == json.dumps(bareX34,
                                                             sort_keys=True)
       and lC34['fcov'] == lX34['fcov'] and lC34['last_at'] == lX34['last_at']
       and lC34['pending_old'] == lX34['pending_old']
       and rcC34 == rcX34 == 0
       and linesX34[0].replace('bad=2', 'bad=0') == linesC34[0]
       and linesX34[0] != linesC34[0],
       'two unusable lines move bad= alone on the header - span, stamp and population stay byte-identical')

    # arm 2: the strongest shape - a channel holding ONLY unusable lines used to
    # read exactly like an absent channel
    rN34 = world34([])
    rJ34 = world34([], junk=JUNK34)
    lN34, lJ34 = listing34(rN34), listing34(rJ34)
    rcN34, linesN34 = head34(rN34)
    rcJ34, linesJ34 = head34(rJ34)
    ok('AC-RUN34', lN34['bad'] == 0 and lJ34['bad'] == 2
       and lN34['fcov'] is None and lJ34['fcov'] is None
       and lN34['reason'] == lJ34['reason'] == 'no-coverage'
       and rcN34 == rcJ34 == 0
       and linesJ34[0].replace('bad=2', 'bad=0') == linesN34[0]
       and linesJ34[0] != linesN34[0]
       and 'reason=no-coverage' in linesJ34[0],
       'an absent channel and a channel of only broken lines now differ by bad= while both still say reason=no-coverage')

    # arm 3: ALWAYS printed, including zero - never an absence-to-zero inference
    toks34 = linesC34[0].split()
    ok('AC-RUN34', len(toks34) == 6 and 'bad=0' in toks34
       and linesC34[0].index('bad=') < linesC34[0].index('fcov=')
       and [t.split('=')[0] for t in toks34] ==
       ['CRAWL-PENDING-OLD-LIST', 'pending_old', 'days', 'bad', 'fcov',
        'last_at'],
       'a clean channel prints bad=0 explicitly, and the count sits before the evidence it qualifies')

    # arm 4: SAME read - a line appended on disk after the read is never claimed
    rS34 = world34([(SRC34O, OLD34), ('https://s34.example/page', LATE34)])
    kept34 = {'n': 0}
    real_read34 = RUN.read_failures

    def reading34(path):
        rows = real_read34(path)
        kept34['n'] += 1
        if kept34['n'] == 1:
            with open(path, 'a', encoding='utf-8', newline='\n') as fh:
                fh.write('{appended\n')
        return rows

    RUN.read_failures = reading34
    try:
        _rcS34, linesS34 = head34(rS34)
    finally:
        RUN.read_failures = real_read34
    on_disk34 = [n for n in open(RUN.failure_path(rS34), 'r',
                                encoding='utf-8').read().splitlines()
                 if n.strip()]
    ok('AC-RUN34', kept34['n'] == 1 and 'bad=0' in linesS34[0]
       and len(on_disk34) == 3,
       'the count comes from the rows this call loaded - a broken line appended on disk is never claimed')

    # arm 5: the reason law is untouched - populated tables still carry none
    rP34 = world34([(SRC34O, OLD34), ('https://p34.example/page', LATE34)],
                   junk=JUNK34)
    lP34 = listing34(rP34)
    rcP34, linesP34 = head34(rP34)
    values34 = {lC34['reason'], lN34['reason'], lJ34['reason'],
                lP34['reason']}
    ok('AC-RUN34', lP34['bad'] == 2 and lP34['reason'] is None
       and 'reason=' not in linesP34[0] and 'bad=2' in linesP34[0]
       and values34 <= {None, 'no-coverage', 'unmeasured', 'all-repaired',
                        'no-window'} and 'malformed' not in values34,
       'a populated table names two broken lines and still prints no reason - evidence quality is not population')

    # arm 6: the dictionary keeps its shape, and the trend row is untouched -
    # measured, the trend's own `bad` counts the failure DAY history, a
    # different file, so the header's count is not that number restated
    tC34 = RUN.summarize_failure_trend(
        RUN.failure_day_path(rC34), RUN.failure_path(rC34), TODAY, 7,
        record_path=CR.record_path(rC34))
    tX34 = RUN.summarize_failure_trend(
        RUN.failure_day_path(rX34), RUN.failure_path(rX34), TODAY, 7,
        record_path=CR.record_path(rX34))
    ok('AC-RUN34', len(lC34) == 8 and len(lX34) == 8
       and 'bad=0' in linesC34[0] and 'bad=2' in linesX34[0]
       and len(tX34) == 30 and 'bad' in tX34 and tX34['bad'] == 0
       and json.dumps(tX34, sort_keys=True) == json.dumps(tC34,
                                                          sort_keys=True),
       'the dictionary stays eight keys, and the trend row keeps its thirty untouched - its bad counts the day history, not this channel')

    # arm 7: pure display - nothing written, no verdict, scanner reads none of it
    before34 = snapshot34(rX34)
    rcX34b, linesX34b = head34(rX34)
    after34 = snapshot34(rX34)
    text34 = ''.join(linesX34b)
    ok('AC-RUN34', rcX34b == 0 and before34 == after34
       and 'PASS' not in text34 and 'FLAG' not in text34
       and 'verdict' not in text34
       and 'crawl-failure' not in scan_src18,
       'the count is display only: the world is untouched, no verdict is printed, and the scanner still reads none of it')

    # AC-RUN35 (R3018): `bad=<n>` said how many lines were unusable and never
    # WHICH, so finding one meant opening the side channel by hand. Measured
    # before the pin (qa/probe-R3018.log): the numbers were already recoverable
    # in the one pass read_failures makes; a blank line takes no number; an
    # append never moves an earlier number; and a rejected line's TEXT can carry
    # a url with a token, so the listing names line+reason and never echoes it.
    SRC35 = 'https://keep35.example/page'
    TOKEN35 = 'R3018TOKEN'
    JUNK35 = ['{"source_url":"https://leak.example/%s","failed_at":\n' % TOKEN35,
              '\n',
              '{"failed_at":"not-a-day","error":"x"}\n',
              '{"oops": 1\n']

    def world35(failures, junk=None, records=None):
        root = world()
        roots.append(root)
        for url, when in (records or [(SRC35, TODAY + 'T09:00:00+08:00')]):
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when in failures:
            RUN.append_failure(RUN.failure_path(root), url, when,
                               'TimeoutError: t')
        if junk:
            with open(RUN.failure_path(root), 'a', encoding='utf-8',
                      newline='\n') as fh:
                fh.write(''.join(junk))
        return root

    def bad35(root):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--pending-old-bad', '--root', root])
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    def list35(root):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--pending-old-list', '--root', root, '--at', AT])
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    def snap35(root):
        out = []
        for base, _dirs, files in os.walk(root):
            for name in files:
                p = os.path.join(base, name)
                out.append((os.path.relpath(p, root).replace('\\', '/'),
                            os.path.getsize(p)))
        out.sort()
        return out

    r35 = world35([(SRC35, TODAY + 'T08:00:00+08:00')], junk=JUNK35)
    rc35, lines35 = bad35(r35)
    named35 = RUN.read_failure_bad_lines(RUN.failure_path(r35))
    rows35, bad35n = RUN.read_failures(RUN.failure_path(r35))
    nums35 = [item['line'] for item in named35]

    # arm 1: two good lines plus three unusable ones - every one is named, in
    # ascending physical order, and the count agrees with the header's bad
    ok('AC-RUN35', rc35 == 0 and bad35n == 3 and len(named35) == 3
       and nums35 == [2, 4, 5] and nums35 == sorted(nums35)
       and lines35[0] == 'CRAWL-PENDING-OLD-BAD bad=3'
       and len(rows35) == 1,
       'three unusable lines are named 2/4/5 in order, and the named count is the same number read_failures reports')

    # arm 2: the two kinds stay distinguishable at their own numbers
    kinds35 = {item['line']: item['why'] for item in named35}
    ok('AC-RUN35', kinds35 == {2: 'json', 4: 'fields', 5: 'json'}
       and 'BAD-LINE n=2 why=json' in lines35
       and 'BAD-LINE n=4 why=fields' in lines35
       and 'BAD-LINE n=5 why=json' in lines35,
       'a line that did not parse and a line that parsed but is not a usable row carry different reasons at their own numbers')

    # arm 3: a blank line is skipped and takes no number
    ok('AC-RUN35', 3 not in nums35 and bad35n == 3
       and all('n=3 ' not in n for n in lines35),
       'the blank line on the channel is not a bad line and holds no number')

    # arm 4: the TEXT of a rejected line is never echoed - only its number
    text35 = '\n'.join(lines35)
    ok('AC-RUN35', TOKEN35 not in text35
       and 'leak.example' not in text35 and 'oops' not in text35
       and text35.count('BAD-LINE') == 3,
       'a rejected line can carry a url with a token in it - the listing names the line and never prints what it holds')

    # arm 5: the list face is untouched - R3014's boundary still holds
    rcL35, linesL35 = list35(r35)
    lst35 = RUN.list_pending_old(CR.record_path(r35),
                                 RUN.failure_path(r35),
                                 TODAY + 'T12:00:00+08:00', 7)
    toks35 = linesL35[0].split()
    ok('AC-RUN35', rcL35 == 0 and len(lst35) == 8 and 'bad=3' in linesL35[0]
       and [t.split('=')[0] for t in toks35[:6]] ==
       ['CRAWL-PENDING-OLD-LIST', 'pending_old', 'days', 'bad', 'fcov',
        'last_at']
       and (len(toks35) == 6
            or (len(toks35) == 7 and toks35[6].startswith('reason=')))
       and not any('BAD-LINE' in n for n in linesL35),
       'the old-waiter list still carries six header tokens and no BAD-LINE row - source rows describe sources, bad lines describe the channel')

    # arm 6: no bad line means no number at all - a clean channel and an absent
    # one both answer bad=0 and print no BAD-LINE row (never a fabricated one)
    rClean35 = world35([(SRC35, TODAY + 'T08:00:00+08:00')])
    rcC35, linesC35 = bad35(rClean35)
    rcA35, linesA35 = bad35(world35([]))
    emptyFile35 = os.path.join(rClean35, 'no-such-channel.jsonl')
    ok('AC-RUN35', rcC35 == rcA35 == 0
       and linesC35 == ['CRAWL-PENDING-OLD-BAD bad=0']
       and linesA35 == ['CRAWL-PENDING-OLD-BAD bad=0']
       and RUN.read_failure_bad_lines(emptyFile35) == [],
       'a clean channel and an absent one both answer bad=0 with no line named, and a missing file reads as an empty list rather than an error')

    # arm 7: pure display, and an append never moves an earlier number
    before35 = snap35(r35)
    rc35b, lines35b = bad35(r35)
    after35 = snap35(r35)
    with open(RUN.failure_path(r35), 'a', encoding='utf-8',
              newline='\n') as fh:
        fh.write('{later\n')
    later35 = [item['line'] for item in
               RUN.read_failure_bad_lines(RUN.failure_path(r35))]
    text35b = '\n'.join(lines35b)
    ok('AC-RUN35', rc35b == 0 and before35 == after35
       and 'PASS' not in text35b and 'FLAG' not in text35b
       and 'verdict' not in text35b
       and 'crawl-failure' not in scan_src18
       and later35[:3] == [2, 4, 5] and later35[-1] == 6,
       'the listing writes nothing and prints no verdict, and a line appended after the read leaves every earlier number where it was')

    # AC-RUN36 (R3019): the daily history printed bad=<n> and could name
    # nothing, because read_failure_days carried its own loop with no numbering.
    # Measured before the change (qa/probe-R3019.log): the pre-change shape is
    # read from the HEAD revision through git show rather than remembered -
    # _failure_lines False, enumerate False, no day-bad reader, four reject
    # branches and no reason named; numbering would have been the same law
    # anyway (non-blank physical numbers, blank skipped, count == rows + bad).
    # A second measured fact shapes the face: snapshot_failure_day rewrites the
    # file from validated rows, so days bad 1 -> 0 on the next beat, while an
    # appended side-channel line keeps its number. Hence read-only, no advice.
    DAY_OK36 = json.dumps({'day': '2026-11-18', 'on_day': 2, 'total': 3,
                           'recent': 1, 'bad': 0, 'urls': 1,
                           'newest_at': '2026-11-18T09:00:00+08:00',
                           'newest_error': 'TimeoutError: t'},
                          ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'))
    SRC36 = 'https://keep36.example/page'
    JUNK36 = ['{"oops": 1\n',
              '\n',
              '{"day":"not-a-day","on_day":1}\n',
              '{"day":"2026-11-17","on_day":"two"}\n',
              '[1,2,3]\n']

    def days36(junk=None, side38rows=(), side_junk=None):
        root = world()
        roots.append(root)
        path = RUN.failure_day_path(root)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(DAY_OK36 + '\n')
            if junk:
                fh.write(''.join(junk))
        for url, when in side38rows:
            RUN.append_failure(RUN.failure_path(root), url, when,
                               'TimeoutError: t')
        if side_junk:
            with open(RUN.failure_path(root), 'a', encoding='utf-8',
                      newline='\n') as fh:
                fh.write(''.join(side_junk))
        return root

    def days_bad36(root):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--failure-days-bad', '--root', root])
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    def side_bad36(root):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--pending-old-bad', '--root', root])
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    def snap36(root):
        out = []
        for base, _dirs, files in os.walk(root):
            for name in files:
                p = os.path.join(base, name)
                out.append((os.path.relpath(p, root).replace('\\', '/'),
                            os.path.getsize(p)))
        out.sort()
        return out

    r36 = days36(JUNK36)
    rc36, lines36 = days_bad36(r36)
    named36 = RUN.read_failure_day_bad_lines(RUN.failure_day_path(r36))
    rows36, bad36 = RUN.read_failure_days(RUN.failure_day_path(r36))
    nums36 = [item['line'] for item in named36]

    # arm 1: every unusable line named in order, and the count is the same
    # number read_failure_days reports (one pass, not two parsers)
    ok('AC-RUN36', rc36 == 0 and bad36 == 4 and len(named36) == 4
       and nums36 == [2, 4, 5, 6] and nums36 == sorted(nums36)
       and lines36[0] == 'CRAWL-FAILURE-DAYS-BAD bad=4'
       and len(rows36) == 1,
       'four unusable history lines are named 2/4/5/6 in order and the named count is the same number read_failure_days reports')

    # arm 2: four different repairs stay four different words
    kinds36 = {item['line']: item['why'] for item in named36}
    ok('AC-RUN36', kinds36 == {2: 'json', 4: 'day', 5: 'on_day', 6: 'shape'}
       and 'BAD-LINE n=2 why=json' in lines36
       and 'BAD-LINE n=4 why=day' in lines36
       and 'BAD-LINE n=5 why=on_day' in lines36
       and 'BAD-LINE n=6 why=shape' in lines36,
       'a line that did not parse, a bad day, a non-integer on_day and a non-object line each carry their own reason at their own number')

    # arm 3: a blank line takes no number, and an append never moves one
    with open(RUN.failure_day_path(r36), 'a', encoding='utf-8',
              newline='\n') as fh:
        fh.write('{later\n')
    later36 = [item['line'] for item in
               RUN.read_failure_day_bad_lines(RUN.failure_day_path(r36))]
    ok('AC-RUN36', 3 not in nums36 and later36[:4] == [2, 4, 5, 6]
       and later36[-1] == 7,
       'the blank line on line 3 takes no number, and a line appended later becomes 7 without moving 2/4/5/6')

    # arm 4: the two files never cross - a dirty history leaves the side
    # channel's shipped header byte-identical, and a dirty side channel does
    # not inflate the history's count
    rA36 = days36(JUNK36, side38rows=[(SRC36, TODAY + 'T08:00:00+08:00')])
    rcSide36, linesSide36 = side_bad36(rA36)
    rcDaysA36, linesDaysA36 = days_bad36(rA36)
    rB36 = days36(None, side38rows=[(SRC36, TODAY + 'T08:00:00+08:00')],
                  side_junk=['{oops\n'])
    rcDaysB36, linesDaysB36 = days_bad36(rB36)
    rcSideB36, linesSideB36 = side_bad36(rB36)
    ok('AC-RUN36', rcSide36 == 0
       and linesSide36 == ['CRAWL-PENDING-OLD-BAD bad=0']
       and linesDaysA36[0] == 'CRAWL-FAILURE-DAYS-BAD bad=4'
       and linesDaysB36 == ['CRAWL-FAILURE-DAYS-BAD bad=0']
       and linesSideB36[0] == 'CRAWL-PENDING-OLD-BAD bad=1'
       and len(linesSideB36) == 2
       and 'BAD-LINE n=2 why=json' in linesSideB36
       and not any('BAD-LINE' in n for n in linesDaysB36),
       'a dirty history leaves the side-channel header text unchanged and a dirty side channel leaves the history at bad=0 - the two faces read their own files')

    # arm 5: one parse law, and a file of blanks produces no number anywhere
    src36 = open(RUN.__file__, 'r', encoding='utf-8').read()
    seg36 = src36.split('def read_failure_days(')[1].split('\ndef ')[0]
    rC36 = world()
    roots.append(rC36)
    blankPath36 = RUN.failure_day_path(rC36)
    os.makedirs(os.path.dirname(blankPath36), exist_ok=True)
    with open(blankPath36, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n\n   \n\n')
    ok('AC-RUN36', '_json_lines(' in seg36 and 'enumerate(' not in seg36
       and RUN.read_failure_days(blankPath36) == ([], 0)
       and RUN.read_failure_day_bad_lines(blankPath36) == [],
       'the history reader delegates to the shared parse law instead of iterating itself, and a file of only blank lines reads as zero rows and zero bad lines')

    # arm 6: absent and clean both answer bad=0 and name nothing
    rClean36 = days36()
    rcClean36, linesClean36 = days_bad36(rClean36)
    rAbsent36 = world()
    roots.append(rAbsent36)
    rcAbsent36, linesAbsent36 = days_bad36(rAbsent36)
    ok('AC-RUN36', rcClean36 == rcAbsent36 == 0
       and linesClean36 == ['CRAWL-FAILURE-DAYS-BAD bad=0']
       and linesAbsent36 == ['CRAWL-FAILURE-DAYS-BAD bad=0']
       and RUN.read_failure_day_bad_lines(
           os.path.join(rAbsent36, 'no-such-history.jsonl')) == []
       and RUN.read_failure_days(
           os.path.join(rAbsent36, 'no-such-history.jsonl')) == ([], 0),
       'a clean history and an absent one both answer bad=0 with no line named, and a missing file reads as an empty list rather than an error')

    # arm 7: pure display - nothing written, no verdict, outside the scanner
    before36 = snap36(r36)
    rc36b, lines36b = days_bad36(r36)
    after36 = snap36(r36)
    text36 = '\n'.join(lines36b)
    ok('AC-RUN36', rc36b == 0 and before36 == after36
       and 'PASS' not in text36 and 'FLAG' not in text36
       and 'verdict' not in text36
       and 'crawl-failure' not in scan_src18,
       'the listing writes nothing and prints no verdict, and the scanner still reads none of it')

    # AC-RUN37 (R3020): a rewrite keeps validated rows only, so the beat ate
    # malformed history lines and left no trace, while the row it wrote carried
    # bad= - the SIDE channel's unusable count. Measured before this existed
    # (qa/probe-R3020.log): a healthy side channel over a four-line dirty
    # history writes bad=0 while the rewrite eats 4; the day row's key set was
    # pinned verbatim NOWHERE (0 exact assertions) while the series dict is
    # pinned exactly, and the count was already in hand under the name
    # `_ignored`. Hence dropped= on the day row only, accumulated across the
    # same day's rewrites (a per-rewrite number would be overwritten by the
    # next ten-minute beat), never backfilled onto older rows.
    def hist37(root):
        path = RUN.failure_day_path(root)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def days_head37(root):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--failure-days', '--root', root])
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    r37 = world()
    roots.append(r37)
    p37 = hist37(r37)
    with open(p37, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(DAY_OK36 + '\n' + ''.join(JUNK36))
    named_before37 = RUN.read_failure_day_bad_lines(p37)
    row37 = RUN.snapshot_failure_day(r37, TODAY + 'T10:00:00+08:00')
    rows_after37, bad_after37 = RUN.read_failure_days(p37)

    # arm 1: the eaten lines leave a number behind, attributable to this file
    ok('AC-RUN37', len(named_before37) == 4 and row37.get('dropped') == 4
       and row37.get('bad') == 0 and bad_after37 == 0
       and len(rows_after37) == 2,
       'four unusable history lines are eaten by the rewrite and the row it writes carries dropped=4 while bad=0 names the healthy side channel')

    # arm 2: it survives the next beats instead of being rewritten to 0
    row37b = RUN.snapshot_failure_day(r37, TODAY + 'T10:10:00+08:00')
    row37c = RUN.snapshot_failure_day(r37, TODAY + 'T10:20:00+08:00')
    ok('AC-RUN37', row37b.get('dropped') == 4 and row37c.get('dropped') == 4
       and row37b.get('bad') == 0,
       'the number is accumulated per day, so two later beats over a clean history keep dropped=4 instead of erasing it')

    # arm 3: a dirty side channel moves bad= and leaves dropped= alone
    r37d = world()
    roots.append(r37d)
    p37d = hist37(r37d)
    with open(p37d, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(DAY_OK36 + '\n')
    with open(RUN.failure_path(r37d), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('{oops\n')
    row37d = RUN.snapshot_failure_day(r37d, TODAY + 'T11:00:00+08:00')
    ok('AC-RUN37', row37d.get('bad') == 1 and row37d.get('dropped') == 0,
       'one unusable side-channel line writes bad=1 and leaves dropped=0 - the two numbers describe different files')

    # arm 4: rows written before this field are never backfilled
    r37e = world()
    roots.append(r37e)
    p37e = hist37(r37e)
    old_a = json.dumps({'day': '2026-11-17', 'on_day': 1, 'total': 1,
                        'recent': 1, 'bad': 0, 'urls': 1,
                        'newest_at': None, 'newest_error': None},
                       ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'))
    old_b = json.dumps({'day': '2026-11-18', 'on_day': 2, 'total': 2,
                        'recent': 2, 'bad': 0, 'urls': 2,
                        'newest_at': None, 'newest_error': None},
                       ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'))
    with open(p37e, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(old_a + '\n' + old_b + '\n')
    RUN.snapshot_failure_day(r37e, TODAY + 'T12:00:00+08:00')
    text37e = open(p37e, 'r', encoding='utf-8').read().splitlines()
    old37e = [json.loads(ln) for ln in text37e[:2]]
    new37e = json.loads(text37e[-1])
    ok('AC-RUN37', text37e[0] == old_a and text37e[1] == old_b
       and 'dropped' not in old37e[0] and 'dropped' not in old37e[1]
       and new37e.get('dropped') == 0 and new37e.get('day') == TODAY,
       'two rows written before the field stay byte-identical with no invented zero, and only the row this rewrite writes carries the key')

    # arm 5: exactly one new key on the day row, and no aggregate face grew
    keys37 = set(row37b.keys())
    base37 = set(['bad', 'day', 'newest_at', 'newest_error', 'on_day', 'recent',
                  'total', 'urls'])
    series37 = RUN.summarize_failure_days(p37)
    trend37 = RUN.summarize_failure_trend(p37, RUN.failure_path(r37), TODAY)
    ok('AC-RUN37', keys37 == base37 | set(['dropped'])
       and set(series37.keys()) == set(['bad', 'bytes', 'days', 'first',
                                        'dropped', 'gate_ref_mb', 'last',
                                        'present', 'series', 'size_gate'])
       and all(isinstance(p, tuple) and len(p) == 2
               for p in series37['series'])
       and 'dropped' not in trend37
       and series37['dropped'] == row37b.get('dropped'),
       'the day row grows by exactly one named key, the series carries the '
       'last row\'s own value (R3021 face; the R3020 absence pin is retired by '
       'design, disclosed in the board PIN), and the trend row gains nothing')

    # arm 6: one history read per snapshot, and the written number is its count
    r37f = world()
    roots.append(r37f)
    p37f = hist37(r37f)
    with open(p37f, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(DAY_OK36 + '\n{"late": 1\n')
    calls37 = []
    real_read_days = RUN.read_failure_days

    def counting_read_days(path):
        out = real_read_days(path)
        calls37.append(out[1])
        if len(calls37) == 1:
            with open(path, 'a', encoding='utf-8', newline='\n') as fh:
                fh.write('{appended\n')
        return out

    RUN.read_failure_days = counting_read_days
    try:
        row37f = RUN.snapshot_failure_day(r37f, TODAY + 'T13:00:00+08:00')
    finally:
        RUN.read_failure_days = real_read_days
    ok('AC-RUN37', len(calls37) == 1 and calls37[0] == 1
       and row37f.get('dropped') == 1
       and RUN.read_failure_days(p37f)[1] == 0,
       'a snapshot reads the history exactly once and writes that read\'s count, so a line appended after the read neither inflates the number nor survives the rewrite')

    # arm 7: pure display - the shipped header is unchanged, nothing is written
    before37 = snap36(r37f)
    rc37, lines37 = days_head37(r37f)
    after37 = snap36(r37f)
    text37 = '\n'.join(lines37)
    ok('AC-RUN37', rc37 == 0 and before37 == after37
       and lines37 and lines37[0].startswith('CRAWL-FAILURE-DAYS days=')
       and 'dropped=' in text37
       and 'PASS' not in text37 and 'FLAG' not in text37
       and 'verdict' not in text37
       and 'crawl-failure' not in scan_src18,
       'the day listing writes nothing and prints no verdict; the header now '
       'carries the R3021 dropped= token (this arm\'s R3020 absence pin is '
       'retired by design), and the scanner still reads none of it')

    # AC-RUN38 (R3021): the eaten-lines count R3020 wrote down had no face - a
    # reader had to open the jsonl - and it cannot be attributed to the day an
    # eaten line belonged to (measured, qa/probe-R3021.log: every rejected line
    # is handed over as row=None even when its text carries a usable day, and a
    # rewrite renumbers). So the ONE thing that can be shown without inventing a
    # number is the LAST day row's own value, with none for a row that predates
    # the field. Arms 5 and 7 of AC-RUN37 were retired by design (they pinned
    # the field's absence from the series and the header); disclosed there.
    def put_days(path, rows):
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            for r in rows:
                fh.write(json.dumps(r, sort_keys=True,
                                    separators=(',', ':')) + '\n')

    def plain_day(day, n, dropped=None):
        out = {'bad': 0, 'day': day, 'newest_at': None, 'newest_error': None,
               'on_day': n, 'recent': 0, 'total': 0, 'urls': 0}
        if dropped is not None:
            out['dropped'] = dropped
        return out

    # arm 1: a beat that ate lines now says so on the header a person reads
    r38 = world()
    roots.append(r38)
    p38 = hist37(r38)
    with open(p38, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(DAY_OK36 + '\n' + ''.join(JUNK36))
    row38 = RUN.snapshot_failure_day(r38, TODAY + 'T11:00:00+08:00')
    rc38, lines38 = days_head37(r38)
    head38 = lines38[0]
    ok('AC-RUN38', rc38 == 0 and row38.get('dropped') == 4
       and ('last=%s dropped=4' % TODAY) in head38,
       'four lines eaten by the rewrite now read dropped=4 on the header, right '
       'after the last= row they belong to')

    # arm 2: a beat that ate nothing prints an explicit zero
    r38b = world()
    roots.append(r38b)
    p38b = hist37(r38b)
    put_days(p38b, [plain_day('2026-11-18', 1)])
    RUN.snapshot_failure_day(r38b, TODAY + 'T11:10:00+08:00')
    rc38b, lines38b = days_head37(r38b)
    ok('AC-RUN38', rc38b == 0 and 'dropped=0' in lines38b[0],
       'a clean rewrite prints dropped=0 - the token is always printed rather '
       'than inferred from its absence')

    # arm 3: a row written before the field is none, never an invented zero
    r38c = world()
    roots.append(r38c)
    p38c = hist37(r38c)
    put_days(p38c, [plain_day('2026-11-18', 2)])
    rc38c, lines38c = days_head37(r38c)
    s38c = RUN.summarize_failure_days(p38c)
    ok('AC-RUN38', rc38c == 0 and 'dropped=none' in lines38c[0]
       and s38c['dropped'] is None and s38c['last'] == '2026-11-18',
       'a pre-field row reads dropped=none and the dict answers None - never '
       'zero, which would be an invented measurement')

    # arm 4: it is that row's own number, not a sum over the file
    r38d = world()
    roots.append(r38d)
    p38d = hist37(r38d)
    put_days(p38d, [plain_day('2026-11-18', 0, dropped=5),
                    plain_day(TODAY, 0, dropped=0)])
    rc38d, lines38d = days_head37(r38d)
    ok('AC-RUN38', rc38d == 0 and 'dropped=0' in lines38d[0]
       and 'dropped=5' not in lines38d[0],
       'a 5 on an older row and a 0 on the last row print 0 - no sum and no '
       'maximum, so a day that ate nothing cannot inherit another day\'s loss')

    # arm 5: one read per call, and the number comes from that read
    r38e = world()
    roots.append(r38e)
    p38e = hist37(r38e)
    put_days(p38e, [plain_day('2026-11-18', 0),
                    plain_day(TODAY, 0, dropped=2)])
    calls38 = []
    real_read_days38 = RUN.read_failure_days

    def counting_read_days38(path):
        out = real_read_days38(path)
        calls38.append(len(out[0]))
        if len(calls38) == 1:
            put_days(path, [plain_day('2026-11-18', 0),
                            plain_day(TODAY, 0, dropped=9)])
        return out

    RUN.read_failure_days = counting_read_days38
    try:
        s38e = RUN.summarize_failure_days(p38e)
    finally:
        RUN.read_failure_days = real_read_days38
    ok('AC-RUN38', calls38 == [2] and s38e['dropped'] == 2,
       'the header value comes from the same single read as days/last - a '
       'rewrite after that read moves neither the number nor the call count')

    # arm 6: exactly one new key, payload shapes and the trend untouched
    trend38 = RUN.summarize_failure_trend(p38d, RUN.failure_path(r38d), TODAY)
    ok('AC-RUN38', set(RUN.summarize_failure_days(p38d).keys()) == set(
        ['bad', 'bytes', 'days', 'dropped', 'first', 'gate_ref_mb', 'last',
         'present', 'series', 'size_gate'])
       and all(isinstance(p, tuple) and len(p) == 2
               and len(p) == 2 for p in RUN.summarize_failure_days(
                   p38d)['series'])
       and len(trend38) == 30 and 'dropped' not in trend38,
       'the dict grows by one named key, series stays (day, on_day) pairs, and '
       'the 30-key trend row gains nothing')

    # arm 7: pure display - nothing written, no verdict, outside the scanner
    def tree_bytes(root):
        out = []
        for base, _dirs, files in os.walk(root):
            for f in sorted(files):
                full = os.path.join(base, f)
                with open(full, 'rb') as fh:
                    out.append((os.path.relpath(full, root),
                                hashlib.sha256(fh.read()).hexdigest()))
        return sorted(out)

    before38 = tree_bytes(r38d)
    rc38f, lines38f = days_head37(r38d)
    after38 = tree_bytes(r38d)
    text38 = '\n'.join(lines38f)
    ok('AC-RUN38', rc38f == 0 and before38 == after38
       and 'PASS' not in text38 and 'FLAG' not in text38
       and 'verdict' not in text38
       and 'crawl-failure' not in scan_src18,
       'the listing writes no byte, prints no verdict, and the scanner still '
       'reads none of it')

    # AC-RUN39 (R3022): the step that writes the eaten-lines count never said it
    # on its own header - the snapshot beat printed day/on_day/total/recent/bad/
    # urls while the row it had just written carried dropped= (measured,
    # qa/probe-R3022.log P1f). Both print sites now end with dropped=, the row's
    # own value. A fresh row always carries it (int, never none), so the token is
    # always printed; `none` stays a DAYS-face word for a pre-field row. The
    # per-day LIST was measured but not built: it is per-row, not a sum.
    def snap39(root):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--snapshot-failures', '--root', root, '--at', AT])
        return rc, buf.getvalue().strip()

    def tail39(head):
        """dropped=<n> from the END of the header, or None when absent."""
        tok = head.split()
        if not tok or not tok[-1].startswith('dropped='):
            return None
        try:
            return int(tok[-1].split('=', 1)[1])
        except ValueError:
            return None

    # arm 1: a rewrite that eats four lines says so on the beat's own header,
    # and the five older tokens keep their positions (the new one is appended)
    r39 = world()
    roots.append(r39)
    p39 = hist37(r39)
    with open(p39, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(DAY_OK36 + '\n' + ''.join(JUNK36))
    rc39, head39 = snap39(r39)
    tok39 = head39.split()
    ok('AC-RUN39', rc39 == 0 and tail39(head39) == 4
       and len(tok39) == 8
       and tok39[0] == 'CRAWL-FAILURE-DAY'
       and tok39[1].startswith('day=') and tok39[2].startswith('on_day=')
       and tok39[3].startswith('total=') and tok39[4].startswith('recent')
       and tok39[5].startswith('bad=') and tok39[6].startswith('urls='),
       'the beat that ate four lines now ends its own header with dropped=4, '
       'and the five older tokens sit in their original order')

    # arm 2: a beat that ate nothing prints an explicit zero
    r39b = world()
    roots.append(r39b)
    p39b = hist37(r39b)
    put_days(p39b, [plain_day('2026-11-18', 1)])
    rc39b, head39b = snap39(r39b)
    ok('AC-RUN39', rc39b == 0 and tail39(head39b) == 0,
       'a clean rewrite prints dropped=0 on the header - always printed, never '
       'inferred from absence')

    # arm 3: the carry is visible - a second beat with nothing left to eat still
    # reports the day's accumulated number, and it equals the row on disk
    r39c = world()
    roots.append(r39c)
    p39c = hist37(r39c)
    put_days(p39c, [plain_day(TODAY, 0, dropped=4)])
    rc39c, head39c = snap39(r39c)
    rows39c, _ = RUN.read_failure_days(p39c)
    onrow39c = rows39c[-1].get('dropped')
    ok('AC-RUN39', rc39c == 0 and tail39(head39c) == 4 and onrow39c == 4,
       'a beat with nothing to eat still says 4 (the day carry), and the number '
       'on the header is the number on the row')

    # arm 4: both print sites are the same face, and none is not a snapshot word
    with open(RUN.__file__, 'r', encoding='utf-8') as fh:
        mod_src39 = fh.read()
    ok('AC-RUN39', mod_src39.count("urls=%d dropped=%d") == 2
       and 'dropped=none' not in mod_src39,
       'the standalone snapshot and the after-write snapshot share one header '
       'shape (two sites), and none never appears on this face - a fresh row '
       'always measures an int')

    # arm 5: the DAYS face is untouched in the same world
    rc39d, lines39d = days_head37(r39)
    s39d = RUN.summarize_failure_days(p39)
    trend39d = RUN.summarize_failure_trend(p39, RUN.failure_path(r39), TODAY)
    ok('AC-RUN39', rc39d == 0 and lines39d[0].startswith('CRAWL-FAILURE-DAYS days=')
       and 'dropped=4' in lines39d[0]
       and all(isinstance(p, tuple) and len(p) == 2 for p in s39d['series'])
       and len(trend39d) == 30 and 'dropped' not in trend39d,
       'the day listing keeps its own header, its (day, on_day) pairs and the '
       '30-key trend row - the new token lives only on the snapshot header')

    # arm 6: an older day's drops do not compete - today's own number is printed
    r39e = world()
    roots.append(r39e)
    p39e = hist37(r39e)
    eaten39e = ['{"oops": 1\n',
                '{"day":"not-a-day","on_day":1}\n',
                '[1,2,3]\n']
    put_days(p39e, [plain_day('2026-11-17', 0, dropped=5)])
    with open(p39e, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write(''.join(eaten39e))
    rc39e, head39e = snap39(r39e)
    ok('AC-RUN39', rc39e == 0 and tail39(head39e) == 3,
       "an older day's dropped=5 neither shows up nor adds in: the header "
       'prints the three lines this beat ate (3, not 5 and not 8)')

    # arm 7: the only byte this face moves is the history row it names, no
    # verdict is printed, and the scanner still reads none of it
    before39f = dict(tree_bytes(r39))
    rc39f, head39f = snap39(r39)
    after39f = dict(tree_bytes(r39))
    moved39f = sorted(k for k in set(before39f) | set(after39f)
                      if before39f.get(k) != after39f.get(k))
    ok('AC-RUN39', rc39f == 0
       and all(k == os.path.join('qa', 'crawl-failure-days.jsonl')
               for k in moved39f)
       and 'PASS' not in head39f and 'FLAG' not in head39f
       and 'verdict' not in head39f
       and 'crawl-failure' not in scan_src18,
       'the beat moves no byte outside the history row it names (an unchanged '
       'row moves none at all), prints no verdict, and the scanner still reads '
       'none of it')

    # AC-RUN40 (R3023): only the LAST day row's eaten count had a face (R3021),
    # so any earlier day still meant opening the jsonl. Measured before this was
    # written (qa/probe-R3023.log): the DAYS header prints exactly one line
    # (P3a) and nothing pins the flag set or the help text (P1a/P1b), so the
    # list is a SEPARATE subcommand. A pre-field row carries no key at all
    # (P2c), duplicates are real on disk (P2e), and file order is what the
    # reader already yields (P2a) - so the listing reports, never de-duplicates.
    def dd40(root):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--failure-days-dropped', '--root', root])
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    def rows40(lines):
        out = []
        for line in lines:
            if not line.startswith('DAY-DROPPED '):
                continue
            tok = dict(part.split('=', 1) for part in line.split()[1:])
            out.append((tok['day'], tok['dropped']))
        return out

    def day_line40(row):
        return json.dumps(row, sort_keys=True, separators=(',', ':'))

    # arm 1: three day rows print three lines in file order, and none/0/5 are
    # three different answers rather than one inherited number
    r40 = world()
    roots.append(r40)
    p40 = hist37(r40)
    put_days(p40, [plain_day('2026-11-15', 1),
                   plain_day('2026-11-16', 2, dropped=0),
                   plain_day('2026-11-17', 3, dropped=5)])
    rc40, lines40 = dd40(r40)
    ok('AC-RUN40', rc40 == 0
       and lines40[0] == 'CRAWL-FAILURE-DAYS-DROPPED days=3 bad=0'
       and rows40(lines40) == [('2026-11-15', 'none'),
                               ('2026-11-16', '0'),
                               ('2026-11-17', '5')],
       'three day rows print three DAY-DROPPED lines in file order - none, 0 '
       'and 5 stay three different answers')

    # arm 2: a row written before the field is none in the line AND in the dict
    r40b = world()
    roots.append(r40b)
    p40b = hist37(r40b)
    put_days(p40b, [plain_day('2026-11-16', 2)])
    rc40b, lines40b = dd40(r40b)
    lst40b = RUN.list_failure_days_dropped(p40b)
    ok('AC-RUN40', rc40b == 0 and rows40(lines40b) == [('2026-11-16', 'none')]
       and lst40b['rows'][0]['dropped'] is None,
       'a row written before the field reads none in both the printed line and '
       'the dict - zero would be an invented measurement')

    # arm 3: per row, never a sum or a maximum, and no aggregate on the header
    r40c = world()
    roots.append(r40c)
    p40c = hist37(r40c)
    put_days(p40c, [plain_day('2026-11-16', 1, dropped=5),
                    plain_day('2026-11-17', 2),
                    plain_day(TODAY, 3, dropped=0)])
    rc40c, lines40c = dd40(r40c)
    ok('AC-RUN40', rc40c == 0
       and [v for _d, v in rows40(lines40c)] == ['5', 'none', '0']
       and 'dropped=' not in lines40c[0],
       'a 5, an unmeasured row and a 0 print 5/none/0 - no sum, no maximum, '
       'and the header carries no aggregate to inherit')

    # arm 4: the same day twice is reported twice - a de-duplicated listing
    # would hide a row that is really on disk
    r40d = world()
    roots.append(r40d)
    p40d = hist37(r40d)
    put_days(p40d, [plain_day('2026-11-17', 1, dropped=5),
                    plain_day('2026-11-17', 2, dropped=1)])
    rc40d, lines40d = dd40(r40d)
    ok('AC-RUN40', rc40d == 0
       and rows40(lines40d) == [('2026-11-17', '5'), ('2026-11-17', '1')]
       and len(lines40d) == 3,
       'one day written twice is reported twice (5 and 1) rather than summed '
       'or collapsed into one row')

    # arm 5: a malformed line is counted and never listed - no number shifts
    # onto a day that does not exist
    r40e = world()
    roots.append(r40e)
    p40e = hist37(r40e)
    with open(p40e, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(day_line40(plain_day('2026-11-16', 1, dropped=2)) + '\n')
        fh.write('{"oops": 1\n')
        fh.write(day_line40(plain_day('2026-11-17', 2)) + '\n')
    rc40e, lines40e = dd40(r40e)
    ok('AC-RUN40', rc40e == 0
       and lines40e[0] == 'CRAWL-FAILURE-DAYS-DROPPED days=2 bad=1'
       and rows40(lines40e) == [('2026-11-16', '2'),
                                ('2026-11-17', 'none')],
       'the one unusable line is counted as bad=1 and listed nowhere, so no '
       'number lands on a day the file does not contain')

    # arm 6: in the same world the DAYS face keeps its single line, its pairs
    # and the 30-key trend row - the new face is a subcommand, not a token on
    # somebody else's header
    rc40f, lines40f = days_head37(r40)
    s40f = RUN.summarize_failure_days(p40)
    t40f = RUN.summarize_failure_trend(p40, RUN.failure_path(r40), TODAY)
    ok('AC-RUN40', rc40f == 0 and len(lines40f) == 1
       and lines40f[0].startswith('CRAWL-FAILURE-DAYS days=')
       and 'DAY-DROPPED' not in lines40f[0]
       and all(isinstance(p, tuple) and len(p) == 2 for p in s40f['series'])
       and len(t40f) == 30 and 'dropped' not in t40f,
       'the DAYS face keeps one line, (day, on_day) pairs and the 30-key trend '
       'row while the per-day list lives in its own subcommand')

    # arm 7: pure display - no byte written, no verdict, outside the scanner
    before40 = tree_bytes(r40)
    rc40g, lines40g = dd40(r40)
    after40 = tree_bytes(r40)
    text40g = '\n'.join(lines40g)
    ok('AC-RUN40', rc40g == 0 and before40 == after40
       and 'PASS' not in text40g and 'FLAG' not in text40g
       and 'verdict' not in text40g
       and 'crawl-failure' not in scan_src18,
       'the listing writes no byte, prints no verdict, and the scanner still '
       'reads none of it')

    # AC-RUN41 (R3024): the per-day list printed every row with no window, so
    # its length grew with the file while the DAYS series had a --days limit
    # since R3000. Measured before this arm set existed (qa/probe-R3024.log):
    # the unwindowed header is pinned by two exact-equality arms (P2a), --days
    # already has seven other readers (Q3b), nothing reads days= as the printed
    # line count (Q2a/Q2c), and duplicates really sit on disk (P4f). So the
    # window is opt-in, the default face stays byte-identical, and truncation is
    # a token rather than a missing row.
    def dd41(root, extra=None):
        argv = ['--failure-days-dropped', '--root', root]
        if extra is not None:
            argv = ['--failure-days-dropped',
                    '--failure-days-dropped-window', str(extra),
                    '--root', root]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(argv)
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    def day_rows_41(lines):
        out = []
        for line in lines:
            if not line.startswith('DAY-DROPPED '):
                continue
            tok = dict(part.split('=', 1) for part in line.split()[1:])
            out.append(tok['day'])
        return out

    span41 = ['2026-10-%02d' % d for d in range(2, 32)] + \
             ['2026-11-%02d' % d for d in range(1, 11)]

    # arm 1: with no window asked for, the dict is exactly the old shape - the
    # new keys never leak into the default face
    r41 = world()
    roots.append(r41)
    p41 = hist37(r41)
    put_days(p41, [plain_day(d, 0, dropped=0) for d in span41])
    lst41 = RUN.list_failure_days_dropped(p41)
    ok('AC-RUN41', sorted(lst41.keys()) == ['bad', 'days', 'rows']
       and sorted(lst41['rows'][0].keys()) == ['day', 'dropped']
       and lst41['days'] == 40 and len(lst41['rows']) == 40,
       'an unwindowed call answers exactly {days,bad,rows} with {day,dropped} '
       'rows - the window keys do not leak into the default shape')

    # arm 2: 40 days asked for as 7 keeps the last 7 in file order and says so
    lst41b = RUN.list_failure_days_dropped(p41, 7)
    ok('AC-RUN41', lst41b['days'] == 40 and lst41b['window'] == 7
       and lst41b['shown'] == 7 and lst41b['truncated'] is True
       and lst41b['hidden'] == 33 and lst41b['head'] == span41[-1]
       and [r['day'] for r in lst41b['rows']] == span41[-7:],
       'a 7-day window over a 40-day history keeps the last seven rows in file '
       'order and reports shown=7 truncated=True hidden=33 head=<last day>')

    # arm 3: a same day twice inside the window stays twice - a window is a
    # filter, never a de-duplicator
    r41c = world()
    roots.append(r41c)
    p41c = hist37(r41c)
    put_days(p41c, [plain_day('2026-11-08', 5, dropped=5),
                    plain_day('2026-11-09', 1, dropped=1),
                    plain_day('2026-11-09', 2, dropped=3),
                    plain_day('2026-11-10', 0, dropped=0)])
    lst41c = RUN.list_failure_days_dropped(p41c, 3)
    ok('AC-RUN41', [r['day'] for r in lst41c['rows']] == ['2026-11-08',
                                                         '2026-11-09',
                                                         '2026-11-09',
                                                         '2026-11-10']
       and [r['dropped'] for r in lst41c['rows']] == [5, 1, 3, 0]
       and lst41c['shown'] == 4 and lst41c['truncated'] is False,
       'one day written twice inside the window is listed twice with its own '
       'values - filtering by day never collapses rows')

    # arm 4: the threshold is inclusive on both ends, the one window law's own
    # arithmetic rather than a second copy
    r41d = world()
    roots.append(r41d)
    p41d = hist37(r41d)
    put_days(p41d, [plain_day('2026-11-03', 1, dropped=9),
                    plain_day('2026-11-04', 1, dropped=1),
                    plain_day('2026-11-10', 1, dropped=0)])
    lst41d = RUN.list_failure_days_dropped(p41d, 7)
    ok('AC-RUN41', [(r['day'], r['dropped']) for r in lst41d['rows']]
       == [('2026-11-04', 1), ('2026-11-10', 0)]
       and lst41d['hidden'] == 1
       and lst41d['truncated'] is True,
       'a row exactly on the threshold is kept and the day before it is '
       'counted into hidden - the boundary is inclusive, and the dropped 9 '
       'does not land on a day that stayed')

    # arm 5: a window wider than the file truncates nothing
    r41e = world()
    roots.append(r41e)
    p41e = hist37(r41e)
    put_days(p41e, [plain_day('2026-11-08', 1, dropped=2),
                    plain_day('2026-11-09', 1, dropped=1),
                    plain_day('2026-11-10', 1, dropped=0)])
    lst41e = RUN.list_failure_days_dropped(p41e, 30)
    ok('AC-RUN41', lst41e['shown'] == 3 and lst41e['days'] == 3
       and lst41e['truncated'] is False and lst41e['hidden'] == 0
       and [r['day'] for r in lst41e['rows']]
       == ['2026-11-08', '2026-11-09', '2026-11-10'],
       'a window larger than the file reports shown=days truncated=False '
       'hidden=0 and leaves the rows untouched')

    # arm 6: an absent history with a window is still an honest zero, not a
    # raise and not an invented head day
    missing41 = os.path.join(world(), 'nope.jsonl')
    lst41f = RUN.list_failure_days_dropped(missing41, 5)
    # R3036 added the total-print key to the windowed shape, stated here
    # instead of hiding it: the rest of the dict is still pinned key-for-key,
    # and the new number's exact value is pinned against real stdout by
    # AC-RUN53 arm 4 rather than restated twice.
    # R3037 adds the block price the same way: named here, pinned exactly by
    # AC-RUN54 arm 4, so the rest of the dict stays key-for-key.
    out41f = lst41f.pop('output_bytes', None)
    shown41f = lst41f.pop('shown_bytes', None)
    # R3038 adds this line's own width the same way: named here, pinned
    # exactly by AC-RUN55 arm 4, so the rest of the dict stays key-for-key.
    head41f = lst41f.pop('header_bytes', None)
    ok('AC-RUN41', lst41f == {'days': 0, 'bad': 0, 'rows': [], 'window': 5,
                              'head': None, 'shown': 0, 'truncated': False,
                              'hidden': 0, 'all_bytes': 0}
       and isinstance(out41f, int) and out41f > 0
       and shown41f == 0
       and isinstance(head41f, int) and head41f > 0,
       'an absent history under a window answers days=0 shown=0 head=None '
       'truncated=False without raising (R3035 added the price key, R3036 the '
       'total, R3037 the block price, R3038 the header width, all stated)')

    # arm 7: no clock - the head is the file's own newest row, so a 2001
    # history windows against itself instead of against today
    r41g = world()
    roots.append(r41g)
    p41g = hist37(r41g)
    put_days(p41g, [plain_day('2001-03-01', 1, dropped=1),
                    plain_day('2001-03-02', 1, dropped=2),
                    plain_day('2001-03-05', 1, dropped=3)])
    lst41g = RUN.list_failure_days_dropped(p41g, 3)
    ok('AC-RUN41', lst41g['head'] == '2001-03-05'
       and lst41g['shown'] == 1 and lst41g['hidden'] == 2
       and [r['day'] for r in lst41g['rows']] == ['2001-03-05'],
       'a 2001 history windows back from its own last row, so the window never '
       'reads the wall clock and an old file is not silently emptied')

    # arm 8: two CLI runs over one world - the default header stays byte-equal
    # to the shape two older arms pin, and the windowed header carries the
    # truncation tokens on the same single line
    rc41h, lines41h = dd41(r41)
    rc41i, lines41i = dd41(r41, 3)
    # R3035 extended this arm instead of deleting it: the windowed header keeps
    # every token it already carried and now also prices the block it truncates,
    # read off the unwindowed run in this same arm (a cross-run invariant).
    # R3036 extends it again: the header also carries output_bytes, and the
    # number must equal the real byte length of what this run printed - the
    # text below is the measured artifact, not a re-derivation of the law.
    # R3037 extends it once more: shown_bytes prices the block THIS run prints,
    # read off the same run's own output.
    # R3038 extends it again: header_bytes prices this very line, read off the
    # line the run actually printed (the equality below is the artifact).
    blk41 = ''.join(n + '\n' for n in lines41h
                    if n.startswith('DAY-DROPPED '))
    blk41i = ''.join(n + '\n' for n in lines41i
                     if n.startswith('DAY-DROPPED '))
    raw41 = '\n'.join(lines41i) + '\n'
    ok('AC-RUN41', rc41h == 0
       and lines41h[0] == 'CRAWL-FAILURE-DAYS-DROPPED days=40 bad=0'
       and len(day_rows_41(lines41h)) == 40
       and rc41i == 0
       and lines41i[0] == ('CRAWL-FAILURE-DAYS-DROPPED days=40 bad=0 window=3 '
                           'shown=3 truncated=1 hidden=37 head=%s '
                           'rows_all_bytes=%d shown_bytes=%d output_bytes=%d '
                           'header_bytes=%d'
                           % (span41[-1], len(blk41.encode('utf-8')),
                              len(blk41i.encode('utf-8')),
                              len(raw41.encode('utf-8')),
                              len(lines41i[0].encode('utf-8')) + 1))
       and day_rows_41(lines41i) == span41[-3:],
       'the unwindowed header is unchanged byte for byte while the windowed '
       'run names window/shown/truncated/hidden/head/rows_all_bytes/shown_bytes '
       'and prints the last three rows in file order, with output_bytes equal '
       'to the real byte length of that output and header_bytes equal to the '
       'width of the very line that carries it')

    # AC-RUN42 (R3025): the same --days is a DAY window on the failure face and
    # a ROW tail on the DAYS face. Measured before this arm set existed
    # (qa/probe-R3025.log): a history whose newest day holds three rows plus one
    # sixty days back printed that old day in series= under the default seven
    # while the window held four rows, and --days 2 printed two of the four rows
    # inside the two-day window - the header said neither. --days has seven
    # readers, so the tail keeps its shape and the two laws are named on the
    # line: series_limit= (the row limit applied), series_shown= (the pairs
    # printed), series_outside= (printed pairs before the window threshold) and
    # window_rows= (usable rows the window holds).
    def days42(root, extra=None):
        argv = ['--failure-days', '--root', root]
        if extra is not None:
            argv = ['--failure-days', '--days', str(extra), '--root', root]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(argv)
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    def toks42(line):
        return dict(part.split('=', 1) for part in line.split()[1:])

    r42 = world()
    roots.append(r42)
    p42 = hist37(r42)
    put_days(p42, [plain_day('2026-09-20', 5), plain_day('2026-11-18', 1),
                   plain_day('2026-11-19', 3), plain_day('2026-11-19', 1),
                   plain_day('2026-11-19', 2)])
    rc42, lines42 = days42(r42)
    t42 = toks42(lines42[0]) if lines42 else {}
    ok('AC-RUN42', rc42 == 0
       and t42.get('series_limit') == '7'
       and t42.get('series_shown') == '5'
       and t42.get('series_outside') == '1'
       and t42.get('window_rows') == '4'
       and '2026-09-20:5' in t42.get('series', '')
       and RUN.series_window_counts(RUN.read_failure_days(p42)[0], 7, 7)
       == {'limit': 7, 'shown': 5, 'outside': 1, 'window_rows': 4},
       'a tail that prints a day sixty days outside the window now says so: '
       'limit=7 shown=5 outside=1 window_rows=4, and the tail itself still '
       'prints all five pairs including the old day')

    # arm 2: the nine old tokens keep their order and meaning - the markers are
    # appended after gate_ref=, and the prefix is byte-identical to the old line
    s42 = RUN.summarize_failure_days(p42, 7, RUN.read_failure_days(p42))
    pairs42 = ','.join('%s:%s' % (d, n) for d, n in s42['series'])
    old_prefix42 = ('CRAWL-FAILURE-DAYS days=%d bad=%d first=%s last=%s '
                    'dropped=%s series=%s bytes=%d size_gate=%.4f%% '
                    'gate_ref=%dMB'
                    % (s42['days'], s42['bad'], s42['first'] or 'none',
                       s42['last'] or 'none',
                       'none' if s42['dropped'] is None else s42['dropped'],
                       pairs42 or 'none', s42['bytes'], s42['size_gate'],
                       s42['gate_ref_mb']))
    ok('AC-RUN42', lines42 and lines42[0].startswith(old_prefix42)
       and lines42[0][len(old_prefix42):]
       == (' series_limit=7 series_shown=5 series_outside=1 window_rows=4'
           ' window_head=2026-11-19'),
       'the old nine tokens sit in the same order with the same values and the '
       'four R3025 markers plus the R3046 window anchor follow gate_ref= - '
       'nothing was moved or redefined')

    # arm 3: the other direction - the tail printed two of the four rows inside
    # the window, and days= still counts the file rather than the printed pairs
    rc42b, lines42b = days42(r42, 2)
    t42b = toks42(lines42b[0]) if lines42b else {}
    ok('AC-RUN42', rc42b == 0
       and t42b.get('series_limit') == '2'
       and t42b.get('series_shown') == '2'
       and t42b.get('series_outside') == '0'
       and t42b.get('window_rows') == '4'
       and t42b.get('days') == '5'
       and t42b.get('series') == '2026-11-19:1,2026-11-19:2',
       'under --days 2 the window holds four rows while the tail prints two '
       'and days= still reads five - a short series no longer looks like a '
       'short window')

    # arm 4: a history shorter than the limit truncates nothing
    r42c = world()
    roots.append(r42c)
    p42c = hist37(r42c)
    put_days(p42c, [plain_day('2026-11-17', 0), plain_day('2026-11-18', 1),
                    plain_day('2026-11-19', 2)])
    rc42c, lines42c = days42(r42c)
    t42c = toks42(lines42c[0]) if lines42c else {}
    ok('AC-RUN42', rc42c == 0
       and t42c.get('series_limit') == '7'
       and t42c.get('series_shown') == '3'
       and t42c.get('series_outside') == '0'
       and t42c.get('window_rows') == '3'
       and t42c.get('series')
       == '2026-11-17:0,2026-11-18:1,2026-11-19:2',
       'a file smaller than the limit reports shown=window_rows=3 outside=0 '
       'and prints every pair')

    # arm 5: an absent history answers honest zeros and invents no window
    r42d = world()
    roots.append(r42d)
    os.makedirs(os.path.join(r42d, 'qa'), exist_ok=True)
    rc42d, lines42d = days42(r42d)
    t42d = toks42(lines42d[0]) if lines42d else {}
    ok('AC-RUN42', rc42d == 0 and t42d.get('series') == 'none'
       and t42d.get('days') == '0'
       and t42d.get('series_limit') == '7'
       and t42d.get('series_shown') == '0'
       and t42d.get('series_outside') == '0'
       and t42d.get('window_rows') == '0'
       and RUN.series_window_counts([], 7, 7)
       == {'limit': 7, 'shown': 0, 'outside': 0, 'window_rows': 0},
       'no history answers series=none with shown=outside=window_rows=0 '
       'without raising and without claiming a window opened')

    # arm 6: no clock - a 2001 history windows back from its own last row
    r42e = world()
    roots.append(r42e)
    p42e = hist37(r42e)
    put_days(p42e, [plain_day('2001-01-01', 0), plain_day('2001-03-01', 1),
                    plain_day('2001-03-05', 2)])
    rc42e, lines42e = days42(r42e, 2)
    t42e = toks42(lines42e[0]) if lines42e else {}
    ok('AC-RUN42', rc42e == 0
       and t42e.get('series_limit') == '2'
       and t42e.get('series_shown') == '2'
       and t42e.get('series_outside') == '1'
       and t42e.get('window_rows') == '1'
       and t42e.get('last') == '2001-03-05',
       'a two-day window over a 2001 history opens at 2001-03-04, so the '
       'printed 2001-03-01 counts as outside and the window holds one row - '
       'reading the wall clock would report every row outside today')

    # arm 7: days= is not redefined into the printed pair count
    ok('AC-RUN42', t42b.get('days') == '5'
       and t42b.get('series_shown') == '2'
       and t42b.get('days') != t42b.get('series_shown')
       and RUN.summarize_failure_days(p42, 2, RUN.read_failure_days(p42))['days']
       == 5,
       'days= still means usable rows in the file while series_shown= means '
       'pairs printed; the two numbers are visible as different on one line')

    # arm 8: pure display - no byte written, no verdict, outside the scanner
    before42 = tree_bytes(r42)
    rc42f, lines42f = days42(r42)
    after42 = tree_bytes(r42)
    text42 = '\n'.join(lines42f)
    ok('AC-RUN42', rc42f == 0 and before42 == after42
       and 'PASS' not in text42 and 'FLAG' not in text42
       and 'verdict' not in text42
       and 'crawl-failure' not in scan_src18,
       'the header writes no byte, prints no verdict, and the scanner still '
       'reads none of the daily history')

    # ===== AC-RUN43 (R3026): the series can be asked for by DAY WINDOW =====
    # AC-RUN43 was pinned in src/os/backlog.md BEFORE series_days_window
    # existed (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3026.log): world A holds five rows over three days, the
    # default tail prints all five with one of them sixty days outside the
    # window, --days carries nine readers in main, and one suite arm pins the
    # header's tail by exact equality - so the window arrives as its own
    # opt-in flag and the default face stays byte-identical.
    def days43(root, extra):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--failure-days'] + list(extra) + ['--root', root])
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    r43 = world()
    roots.append(r43)
    p43 = hist37(r43)
    put_days(p43, [plain_day('2026-09-20', 5), plain_day('2026-11-18', 1),
                   plain_day('2026-11-19', 3), plain_day('2026-11-19', 1),
                   plain_day('2026-11-19', 2)])

    # arm 1: the window selects the pairs - the old day is simply not printed
    rc43, lines43 = days43(r43, ['--series-days', '7'])
    t43 = toks42(lines43[0]) if lines43 else {}
    ok('AC-RUN43', rc43 == 0
       and t43.get('series_window') == '7'
       and t43.get('series_shown') == '4'
       and t43.get('series_outside') == '0'
       and t43.get('window_rows') == '4'
       and t43.get('series')
       == '2026-11-18:1,2026-11-19:3,2026-11-19:1,2026-11-19:2'
       and '2026-09-20' not in t43.get('series', ''),
       'a seven-day window prints the four rows inside it and drops the day '
       'sixty days back, with outside=0 the marker that the window applied')

    # arm 2: the default face is byte-identical - the marker is opt-in only
    s43 = RUN.summarize_failure_days(p43, 7, RUN.read_failure_days(p43))
    pairs43 = ','.join('%s:%s' % (d, n) for d, n in s43['series'])
    old_prefix43 = ('CRAWL-FAILURE-DAYS days=%d bad=%d first=%s last=%s '
                    'dropped=%s series=%s bytes=%d size_gate=%.4f%% '
                    'gate_ref=%dMB'
                    % (s43['days'], s43['bad'], s43['first'] or 'none',
                       s43['last'] or 'none',
                       'none' if s43['dropped'] is None else s43['dropped'],
                       pairs43 or 'none', s43['bytes'], s43['size_gate'],
                       s43['gate_ref_mb']))
    rc43b, lines43b = days43(r43, [])
    ok('AC-RUN43', rc43b == 0 and lines43b
       and lines43b[0].startswith(old_prefix43)
       and lines43b[0][len(old_prefix43):]
       == (' series_limit=7 series_shown=5 series_outside=1 window_rows=4'
           ' window_head=2026-11-19'),
       'without the flag the header keeps every old token and its only '
       'addition is the R3046 window anchor - the opt-in markers still appear '
       'only when they are asked for')

    # arm 3: the row limit still caps inside the window
    rc43c, lines43c = days43(r43, ['--series-days', '7', '--days', '2'])
    t43c = toks42(lines43c[0]) if lines43c else {}
    ok('AC-RUN43', rc43c == 0
       and t43c.get('series_shown') == '2'
       and t43c.get('window_rows') == '4'
       and t43c.get('series_outside') == '0'
       and t43c.get('days') == '5'
       and t43c.get('series') == '2026-11-19:1,2026-11-19:2',
       'the row limit still caps how many pairs print while window_rows counts '
       'the whole window - two quantities, two words, both visible')

    # arm 4: the window boundary is named, not rounded
    rc43d, lines43d = days43(r43, ['--series-days', '60'])
    t43d = toks42(lines43d[0]) if lines43d else {}
    ok('AC-RUN43', rc43d == 0
       and t43d.get('series_window') == '60'
       and t43d.get('series_shown') == '4'
       and t43d.get('window_rows') == '4'
       and '2026-09-20' not in t43d.get('series', ''),
       'a sixty-day window opens at 2026-09-21 from a 2026-11-19 head, so the '
       '2026-09-20 row stays out by exactly one day - the boundary is named '
       'rather than rounded')

    # arm 5: no history answers zeros and invents no window
    r43e = world()
    roots.append(r43e)
    os.makedirs(os.path.join(r43e, 'qa'), exist_ok=True)
    rc43e, lines43e = days43(r43e, ['--series-days', '7'])
    t43e = toks42(lines43e[0]) if lines43e else {}
    ok('AC-RUN43', rc43e == 0 and t43e.get('series') == 'none'
       and t43e.get('series_shown') == '0'
       and t43e.get('series_outside') == '0'
       and t43e.get('window_rows') == '0'
       and t43e.get('series_window') == '7'
       and RUN.series_days_window([], 7, 7) == {
           'rows': [], 'limit': 7, 'shown': 0, 'outside': 0,
           'window_rows': 0, 'window': 7},
       'an absent history answers series=none and four zeros without '
       'inventing a window and without raising')

    # arm 6: no clock - a 2001 history windows back from its own last row
    r43f = world()
    roots.append(r43f)
    p43f = hist37(r43f)
    put_days(p43f, [plain_day('2001-01-01', 0), plain_day('2001-03-01', 1),
                    plain_day('2001-03-05', 2)])
    rc43f, lines43f = days43(r43f, ['--series-days', '2'])
    t43f = toks42(lines43f[0]) if lines43f else {}
    ok('AC-RUN43', rc43f == 0
       and t43f.get('series_window') == '2'
       and t43f.get('series_shown') == '1'
       and t43f.get('window_rows') == '1'
       and t43f.get('series') == '2001-03-05:2',
       'a two-day window over a 2001 history opens at 2001-03-04 from the '
       'file own last row, so no wall clock is read')

    # arm 7: the pure selection and the header speak from the same numbers
    sel43 = RUN.series_days_window(RUN.read_failure_days(p43)[0], 7, 7)
    ok('AC-RUN43', sel43['rows']
       == [('2026-11-18', 1), ('2026-11-19', 3), ('2026-11-19', 1),
           ('2026-11-19', 2)]
       and sel43['limit'] == 7 and sel43['shown'] == 4
       and sel43['outside'] == 0 and sel43['window_rows'] == 4
       and sel43['window'] == 7
       and t43.get('days') == '5' and t43.get('series_shown') == '4',
       'the pure selection reports the same four counts the header prints, and '
       'days= still means usable rows in the file rather than printed pairs')

    # arm 8: pure display - no byte written, no verdict, marker exactly once
    before43 = tree_bytes(r43)
    rc43g, lines43g = days43(r43, ['--series-days', '7'])
    after43 = tree_bytes(r43)
    text43 = '\n'.join(lines43g)
    ok('AC-RUN43', rc43g == 0 and before43 == after43
       and 'PASS' not in text43 and 'FLAG' not in text43
       and 'verdict' not in text43
       and lines43g[0].count('series_window=') == 1,
       'the window flag writes no byte, prints no verdict, and names itself '
       'exactly once on the line')

    # ===== AC-RUN44 (R3027): a day with NO row gets a name, not a zero =====
    # AC-RUN44 was pinned in src/os/backlog.md BEFORE series_absent_days
    # existed (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3027.log): a seven-day window over world A holds four rows on
    # two distinct days, so five calendar days are silent and the line said
    # nothing; a MEASURED zero already prints as :0 in the pairs, so a gap
    # printed as 0 would be indistinguishable; the trend face already reads a
    # day nobody snapshotted as 'absent'; and five arms assert a 2-tuple in the
    # pairs, so the gaps travel as their own token.
    def days44(root, extra, want_stderr=False):
        buf = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = RUN.main(list(extra) + ['--root', root])
        lines = [n for n in buf.getvalue().splitlines() if n.strip()]
        if want_stderr:
            return rc, lines, err.getvalue()
        return rc, lines

    def toks44(line):
        return dict(part.split('=', 1) for part in line.split()[1:])

    r44 = world()
    roots.append(r44)
    p44 = hist37(r44)
    put_days(p44, [plain_day('2026-09-20', 5), plain_day('2026-11-18', 1),
                   plain_day('2026-11-19', 3), plain_day('2026-11-19', 1),
                   plain_day('2026-11-19', 2)])
    gaps44 = '2026-11-13,2026-11-14,2026-11-15,2026-11-16,2026-11-17'

    # arm 1: the five silent days are named, the pairs are untouched
    rc44, lines44 = days44(r44, ['--failure-days', '--series-days', '7',
                                 '--series-absent'])
    t44 = toks44(lines44[0]) if lines44 else {}
    ok('AC-RUN44', rc44 == 0
       and t44.get('series_window') == '7'
       and t44.get('series_absent') == '5'
       and t44.get('absent') == gaps44
       and t44.get('series')
       == '2026-11-18:1,2026-11-19:3,2026-11-19:1,2026-11-19:2'
       and t44.get('series_shown') == '4'
       and t44.get('window_rows') == '4',
       'a seven-day window prints its four pairs unchanged and names the five '
       'calendar days that hold no row at all')

    # arm 2: without the flag the tail is the same line R3026 shipped
    rc44b, lines44b = days44(r44, ['--failure-days'])
    ok('AC-RUN44', rc44b == 0 and lines44b
       and lines44b[0].endswith(
           ' series_limit=7 series_shown=5 series_outside=1 window_rows=4'
           ' window_head=2026-11-19')
       and 'series_absent' not in lines44b[0]
       and 'absent=' not in lines44b[0],
       'without the flag no absence token appears - the marker is opt-in only '
       'and the default tail stays byte-identical')

    # arm 3: a genuinely quiet week prints a measured zero, not 'none'
    r44c = world()
    roots.append(r44c)
    p44c = hist37(r44c)
    put_days(p44c, [plain_day('2026-11-%02d' % d, 1) for d in range(13, 20)])
    rc44c, lines44c = days44(r44c, ['--failure-days', '--series-days', '7',
                                    '--series-absent'])
    t44c = toks44(lines44c[0]) if lines44c else {}
    ok('AC-RUN44', rc44c == 0 and t44c.get('series_absent') == '0'
       and t44c.get('absent') == 'none'
       and t44c.get('window_rows') == '7',
       'a window where every day has a row answers zero gaps - a zero that was '
       'actually measured, which is why it may print as a number')

    # arm 4: three rows on one day are one present day, not three
    pure44 = RUN.series_absent_days(RUN.read_failure_days(p44)[0], 7)
    ok('AC-RUN44', pure44['count'] == 5
       and pure44['head'] == '2026-11-19'
       and pure44['window'] == 7
       and '2026-11-19' not in pure44['days']
       and '2026-11-18' not in pure44['days']
       and len(set(pure44['days'])) == 5,
       'a day holding three rows counts as one present day: five gaps came '
       'from seven days and two present days, not from seven minus four rows')

    # arm 5: a wide window names its boundary and its 58 gaps
    rc44d, lines44d = days44(r44, ['--failure-days', '--series-days', '60',
                                   '--series-absent'])
    t44d = toks44(lines44d[0]) if lines44d else {}
    gaps44d = (t44d.get('absent') or '').split(',')
    ok('AC-RUN44', rc44d == 0
       and t44d.get('series_absent') == '58'
       and '2026-09-21' in gaps44d
       and '2026-09-20' not in gaps44d
       and '2026-11-18' not in gaps44d,
       'a sixty-day window opens at 2026-09-21 and names 58 silent days while '
       'the two days that hold rows - including the old one - are not gaps')

    # arm 6: no clock - a 2001 history names its own missing day
    r44e = world()
    roots.append(r44e)
    p44e = hist37(r44e)
    put_days(p44e, [plain_day('2001-01-01', 0), plain_day('2001-03-01', 1),
                    plain_day('2001-03-05', 2)])
    rc44e, lines44e = days44(r44e, ['--failure-days', '--series-days', '2',
                                    '--series-absent'])
    t44e = toks44(lines44e[0]) if lines44e else {}
    ok('AC-RUN44', rc44e == 0 and t44e.get('absent') == '2001-03-04'
       and t44e.get('series_absent') == '1'
       and t44e.get('series') == '2001-03-05:2',
       'a two-day window over a 2001 history opens at 2001-03-04 from the file '
       'own last row, so the one silent day is named without a wall clock')

    # arm 7: an absent history cannot report zero gaps
    r44f = world()
    roots.append(r44f)
    os.makedirs(os.path.join(r44f, 'qa'), exist_ok=True)
    rc44f, lines44f = days44(r44f, ['--failure-days', '--series-days', '7',
                                    '--series-absent'])
    t44f = toks44(lines44f[0]) if lines44f else {}
    empty44 = RUN.series_absent_days([], 7)
    ok('AC-RUN44', rc44f == 0 and t44f.get('series_absent') == 'none'
       and t44f.get('absent') == 'none' and t44f.get('series') == 'none'
       and empty44['count'] is None and empty44['days'] == []
       and empty44['head'] is None,
       'no history at all answers none rather than zero - not measurable is '
       'never printed as no gaps, and it does not raise')

    # arm 8: the flag alone is refused, and so is asking it of another face
    rc44g, lines44g, err44g = days44(r44, ['--failure-days', '--series-absent'],
                                     want_stderr=True)
    rc44h, lines44h, err44h = days44(r44, ['--failures', '--series-days', '7',
                                           '--series-absent'], want_stderr=True)
    ok('AC-RUN44', rc44g == 2 and rc44h == 2
       and not lines44g and not lines44h
       and 'series_absent' in err44g and 'series_absent' in err44h,
       'the flag without its day window, and the flag on a face that has no '
       'series, both fail closed with rc=2 and print no header at all')

    # arm 9: pure display - no byte written, no verdict, both tokens once
    before44 = tree_bytes(r44)
    rc44i, lines44i = days44(r44, ['--failure-days', '--series-days', '7',
                                   '--series-absent'])
    after44 = tree_bytes(r44)
    text44 = '\n'.join(lines44i)
    t44i = toks44(lines44i[0]) if lines44i else {}
    named44 = (t44i.get('absent') or '').split(',')
    ok('AC-RUN44', rc44i == 0 and before44 == after44
       and 'PASS' not in text44 and 'FLAG' not in text44
       and 'verdict' not in text44
       and lines44i[0].count('series_absent=') == 1
       and lines44i[0].count('absent=') == 2
       and len(named44) == int(t44i.get('series_absent') or 0),
       'the absence token writes no byte, prints no verdict, appears once, and '
       'the number of named days equals the count printed beside it')

    # ===== AC-RUN45 (R3028): the gap gets a total =====
    # AC-RUN45 was pinned in src/os/backlog.md BEFORE series_presence_counts
    # existed (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3028.log): no face put "days that hold a row" beside the window
    # width, window_rows counts ROWS (4) and not days (2) on world A, and a
    # days_absent= token would break the one arm that counts 'absent=' twice.
    def days45(root, extra):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(list(extra) + ['--root', root])
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    def toks45(line):
        return dict(part.split('=', 1) for part in line.split()[1:])

    r45 = world()
    roots.append(r45)
    p45 = hist37(r45)
    put_days(p45, [plain_day('2026-09-20', 5), plain_day('2026-11-18', 1),
                   plain_day('2026-11-19', 3), plain_day('2026-11-19', 1),
                   plain_day('2026-11-19', 2)])
    rc45, lines45 = days45(r45, ['--failure-days', '--series-days', '7',
                                 '--series-absent'])
    t45 = toks45(lines45[0]) if lines45 else {}

    # arm 1: two present days beside five silent days, summing to the window
    ok('AC-RUN45', rc45 == 0
       and t45.get('days_present') == '2'
       and t45.get('series_absent') == '5'
       and t45.get('series_window') == '7'
       and int(t45['days_present']) + int(t45['series_absent']) == 7
       and t45.get('series')
       == '2026-11-18:1,2026-11-19:3,2026-11-19:1,2026-11-19:2',
       'the header says two days hold a record beside five silent days, and '
       'present plus gap lands on the seven-day window')

    # arm 2: a repeated day is ONE present day but still counts as rows
    ok('AC-RUN45', t45.get('days_present') == '2'
       and t45.get('window_rows') == '4'
       and t45.get('days_present') != t45.get('window_rows'),
       'three rows on one day make window_rows 4 while days_present stays 2 - '
       'the two numbers answer different questions and both stay visible')

    # arm 3: a genuinely recorded week
    r45c = world()
    roots.append(r45c)
    p45c = hist37(r45c)
    put_days(p45c, [plain_day('2026-11-%02d' % d, 1) for d in range(13, 20)])
    rc45c, lines45c = days45(r45c, ['--failure-days', '--series-days', '7',
                                    '--series-absent'])
    t45c = toks45(lines45c[0]) if lines45c else {}
    ok('AC-RUN45', rc45c == 0 and t45c.get('days_present') == '7'
       and t45c.get('series_absent') == '0'
       and t45c.get('series_window') == '7',
       'a week where every day holds a row answers present=7 gap=0, and the '
       'sum still lands on the window width')

    # arm 4: the default face is byte-identical and carries no new token
    rc45d, lines45d = days45(r45, ['--failure-days'])
    ok('AC-RUN45', rc45d == 0 and lines45d
       and lines45d[0].endswith(
           ' series_limit=7 series_shown=5 series_outside=1 window_rows=4'
           ' window_head=2026-11-19')
       and 'days_present' not in lines45d[0],
       'without the flag the tail is the same line R3026/R3027 shipped and no '
       'presence token appears')

    # arm 5: not measurable is not zero
    r45e = world()
    roots.append(r45e)
    os.makedirs(os.path.join(r45e, 'qa'), exist_ok=True)
    rc45e, lines45e = days45(r45e, ['--failure-days', '--series-days', '7',
                                    '--series-absent'])
    t45e = toks45(lines45e[0]) if lines45e else {}
    empty45 = RUN.series_presence_counts([], 7)
    ok('AC-RUN45', rc45e == 0 and t45e.get('days_present') == 'none'
       and t45e.get('series_absent') == 'none'
       and t45e.get('series') == 'none'
       and empty45['present'] is None and empty45['rows'] == 0
       and empty45['head'] is None,
       'no history answers none for both counts rather than an invented zero, '
       'and nothing raises')

    # arm 6: no clock - a 2001 history windows against itself
    r45f = world()
    roots.append(r45f)
    p45f = hist37(r45f)
    put_days(p45f, [plain_day('2001-01-01', 0), plain_day('2001-03-01', 1),
                    plain_day('2001-03-05', 2)])
    rc45f, lines45f = days45(r45f, ['--failure-days', '--series-days', '2',
                                    '--series-absent'])
    t45f = toks45(lines45f[0]) if lines45f else {}
    pure45 = RUN.series_presence_counts(RUN.read_failure_days(p45f)[0], 2)
    ok('AC-RUN45', rc45f == 0 and t45f.get('days_present') == '1'
       and t45f.get('series_absent') == '1'
       and pure45['head'] == '2001-03-05'
       and pure45['present'] == 1 and pure45['rows'] == 1,
       'a two-day window over a 2001 history holds one present day and one '
       'gap, measured from the file own last row with no wall clock')

    # arm 7: the wide-window boundary, where the old row falls outside
    rc45g, lines45g = days45(r45, ['--failure-days', '--series-days', '60',
                                   '--series-absent'])
    t45g = toks45(lines45g[0]) if lines45g else {}
    gaps45g = (t45g.get('absent') or '').split(',')
    ok('AC-RUN45', rc45g == 0 and t45g.get('days_present') == '2'
       and t45g.get('series_absent') == '58'
       and int(t45g['days_present']) + int(t45g['series_absent']) == 60
       and gaps45g[0] == '2026-09-21',
       'a sixty-day window counts two present days and 58 gaps: the row one '
       'day before the threshold is neither present nor a gap')

    # arm 8: the refused name and the guard arms it would have broken
    before45 = tree_bytes(r45)
    rc45h, lines45h = days45(r45, ['--failure-days', '--series-days', '7',
                                   '--series-absent'])
    after45 = tree_bytes(r45)
    text45 = '\n'.join(lines45h)
    ok('AC-RUN45', rc45h == 0 and before45 == after45
       and lines45h and 'days_absent=' not in lines45h[0]
       and lines45h[0].count('absent=') == 2
       and lines45h[0].count('days_present=') == 1
       and 'PASS' not in text45 and 'FLAG' not in text45
       and 'verdict' not in text45,
       'the new token writes no byte, never uses the counted-out days_absent= '
       'name, and keeps the two absent= occurrences the older arm counts')

    # ===== AC-RUN46 (R3029): the row/day difference gets its own name =====
    # AC-RUN46 was pinned in src/os/backlog.md BEFORE the 'repeat' key existed
    # (qa/probe-R3029.log): rows and days printed side by side, no token said
    # why they differ, and every byte-pinned tail sits on the default face.
    def days46(root, extra):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(list(extra) + ['--root', root])
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    def toks46(line):
        return dict(part.split('=', 1) for part in line.split()[1:])

    r46 = world()
    roots.append(r46)
    p46 = hist37(r46)
    put_days(p46, [plain_day('2026-09-20', 5), plain_day('2026-11-18', 1),
                   plain_day('2026-11-19', 3), plain_day('2026-11-19', 1),
                   plain_day('2026-11-19', 2)])
    rc46, lines46 = days46(r46, ['--failure-days', '--series-days', '7',
                                 '--series-absent'])
    t46 = toks46(lines46[0]) if lines46 else {}
    pure46 = RUN.series_presence_counts(RUN.read_failure_days(p46)[0], 7)

    # arm 1: two repeat rows on top of two present days, and the pairs untouched
    ok('AC-RUN46', rc46 == 0
       and t46.get('days_present') == '2'
       and t46.get('repeat_rows') == '2'
       and t46.get('window_rows') == '4'
       and int(t46['days_present']) + int(t46['repeat_rows']) == 4
       and pure46['repeat'] == 2 and pure46['repeat'] == pure46['rows'] - pure46['present']
       and t46.get('series')
       == '2026-11-18:1,2026-11-19:3,2026-11-19:1,2026-11-19:2',
       'four window rows on two present days name two repeat rows, the rows '
       'split sums to window_rows, and the pairs keep the shape R3028 shipped')

    # arm 2: one row per day is a measured zero, not a missing reading
    r46b = world()
    roots.append(r46b)
    p46b = hist37(r46b)
    put_days(p46b, [plain_day('2026-11-%02d' % d, 1) for d in range(13, 20)])
    rc46b, lines46b = days46(r46b, ['--failure-days', '--series-days', '7',
                                    '--series-absent'])
    t46b = toks46(lines46b[0]) if lines46b else {}
    ok('AC-RUN46', rc46b == 0 and t46b.get('repeat_rows') == '0'
       and t46b.get('days_present') == '7' and t46b.get('window_rows') == '7'
       and int(t46b['days_present']) + int(t46b['repeat_rows']) == 7,
       'a week of one row per day answers repeat_rows=0 beside present=7 - a '
       'measured zero, and the split still lands on all seven rows')

    # arm 3: not measurable is not zero
    r46c = world()
    roots.append(r46c)
    os.makedirs(os.path.join(r46c, 'qa'), exist_ok=True)
    rc46c, lines46c = days46(r46c, ['--failure-days', '--series-days', '7',
                                    '--series-absent'])
    t46c = toks46(lines46c[0]) if lines46c else {}
    empty46 = RUN.series_presence_counts([], 7)
    ok('AC-RUN46', rc46c == 0 and t46c.get('repeat_rows') == 'none'
       and t46c.get('days_present') == 'none'
       and empty46['repeat'] is None and empty46['rows'] == 0,
       'no history answers none for the difference as well as for the counts, '
       'and the pure function invents no zero')

    # arm 4: no clock - a 2001 history windows against itself
    r46d = world()
    roots.append(r46d)
    p46d = hist37(r46d)
    put_days(p46d, [plain_day('2001-01-01', 0), plain_day('2001-03-01', 1),
                    plain_day('2001-03-05', 2)])
    rc46d, lines46d = days46(r46d, ['--failure-days', '--series-days', '2',
                                    '--series-absent'])
    t46d = toks46(lines46d[0]) if lines46d else {}
    pure46d = RUN.series_presence_counts(RUN.read_failure_days(p46d)[0], 2)
    ok('AC-RUN46', rc46d == 0 and t46d.get('repeat_rows') == '0'
       and t46d.get('days_present') == '1'
       and t46d.get('series_absent') == '1'
       and pure46d['head'] == '2001-03-05' and pure46d['repeat'] == 0,
       'a two-day window over a 2001 history holds one row on one day: the '
       'difference is zero and the head is the file own last day')

    # arm 5: the default face is byte-identical and carries no new token
    rc46e, lines46e = days46(r46, ['--failure-days'])
    ok('AC-RUN46', rc46e == 0 and lines46e
       and lines46e[0].endswith(
           ' series_limit=7 series_shown=5 series_outside=1 window_rows=4'
           ' window_head=2026-11-19')
       and 'repeat_rows' not in lines46e[0],
       'without the flag the tail is the same line R3026/R3027/R3028 shipped')

    # arm 6: refused names, the counted absent= pair, and no byte written
    before46 = tree_bytes(r46)
    rc46f, lines46f = days46(r46, ['--failure-days', '--series-days', '7',
                                   '--series-absent'])
    after46 = tree_bytes(r46)
    text46 = '\n'.join(lines46f)
    ok('AC-RUN46', rc46f == 0 and before46 == after46 and lines46f
       and lines46f[0].count('repeat_rows=') == 1
       and 'repeat_days=' not in lines46f[0]
       and 'rows_per_day=' not in lines46f[0]
       and lines46f[0].count('absent=') == 2
       and 'PASS' not in text46 and 'FLAG' not in text46
       and 'verdict' not in text46,
       'the difference appears once under its own name, the refused ratio and '
       'days names never appear, the older absent= pair still counts two, and '
       'no byte is written')

    # ===== AC-RUN47 (R3030): a same-day repeat says what it is =====
    # AC-RUN47 was pinned in src/os/backlog.md BEFORE the 'retry' key existed
    # (qa/probe-R3030.log): on_day is a count that does not grow for a
    # re-recording, no face compares two rows of one day, and the flagged tail
    # is read through token dicts rather than full-line equality.
    def days47(root, extra):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(list(extra) + ['--root', root])
        return rc, [n for n in buf.getvalue().splitlines() if n.strip()]

    def toks47(line):
        return dict(part.split('=', 1) for part in line.split()[1:])

    r47 = world()
    roots.append(r47)
    p47 = hist37(r47)
    put_days(p47, [plain_day('2026-09-20', 5), plain_day('2026-11-18', 1),
                   plain_day('2026-11-19', 3), plain_day('2026-11-19', 1),
                   plain_day('2026-11-19', 2)])
    rc47, lines47 = days47(r47, ['--failure-days', '--series-days', '7',
                                 '--series-absent'])
    t47 = toks47(lines47[0]) if lines47 else {}
    pure47 = RUN.series_presence_counts(RUN.read_failure_days(p47)[0], 7)

    # arm 1: the 3 -> 1 step is a re-recording, the 1 -> 2 step grew
    ok('AC-RUN47', rc47 == 0
       and t47.get('retry_rows') == '1'
       and t47.get('repeat_rows') == '2'
       and t47.get('days_present') == '2'
       and t47.get('window_rows') == '4'
       and pure47['retry'] == 1
       and int(pure47['retry']) <= int(pure47['repeat'])
       and int(t47['retry_rows']) <= int(t47['repeat_rows']),
       'a three-row day whose on_day falls then rises splits one re-recording '
       'from one grown reading, and retry never exceeds repeat')

    # arm 2: an equal on_day is also a re-recording
    r47b = world()
    roots.append(r47b)
    p47b = hist37(r47b)
    put_days(p47b, [plain_day('2026-11-18', 2), plain_day('2026-11-18', 2)])
    rc47b, lines47b = days47(r47b, ['--failure-days', '--series-days', '7',
                                    '--series-absent'])
    t47b = toks47(lines47b[0]) if lines47b else {}
    ok('AC-RUN47', rc47b == 0 and t47b.get('retry_rows') == '1'
       and t47b.get('repeat_rows') == '1'
       and t47b.get('days_present') == '1',
       'two rows of one day carrying the same on_day read as one '
       're-recording of the same evidence')

    # arm 3: a day that grew carries a measured zero
    r47c = world()
    roots.append(r47c)
    p47c = hist37(r47c)
    put_days(p47c, [plain_day('2026-11-19', 1), plain_day('2026-11-19', 4)])
    rc47c, lines47c = days47(r47c, ['--failure-days', '--series-days', '7',
                                    '--series-absent'])
    t47c = toks47(lines47c[0]) if lines47c else {}
    ok('AC-RUN47', rc47c == 0 and t47c.get('retry_rows') == '0'
       and t47c.get('repeat_rows') == '1',
       'a repeat whose on_day grew answers retry_rows=0 - a measured zero, '
       'not a missing reading')

    # arm 4: not measurable is not zero
    r47d = world()
    roots.append(r47d)
    os.makedirs(os.path.join(r47d, 'qa'), exist_ok=True)
    rc47d, lines47d = days47(r47d, ['--failure-days', '--series-days', '7',
                                    '--series-absent'])
    t47d = toks47(lines47d[0]) if lines47d else {}
    empty47 = RUN.series_presence_counts([], 7)
    ok('AC-RUN47', rc47d == 0 and t47d.get('retry_rows') == 'none'
       and t47d.get('repeat_rows') == 'none'
       and empty47['retry'] is None,
       'no history answers none for the split as well, and the pure function '
       'invents no re-recording')

    # arm 5: no clock - a 2001 history windows against itself
    r47e = world()
    roots.append(r47e)
    p47e = hist37(r47e)
    put_days(p47e, [plain_day('2001-01-01', 0), plain_day('2001-03-01', 1),
                    plain_day('2001-03-05', 2)])
    rc47e, lines47e = days47(r47e, ['--failure-days', '--series-days', '2',
                                    '--series-absent'])
    t47e = toks47(lines47e[0]) if lines47e else {}
    pure47e = RUN.series_presence_counts(RUN.read_failure_days(p47e)[0], 2)
    ok('AC-RUN47', rc47e == 0 and t47e.get('retry_rows') == '0'
       and t47e.get('days_present') == '1'
       and pure47e['head'] == '2001-03-05' and pure47e['retry'] == 0,
       'a two-day window over a 2001 history holds one row on one day: no '
       'repeat, no inferred retry, and the head is the file own last day')

    # arm 6: the default face is byte-identical and carries no new token
    rc47f, lines47f = days47(r47, ['--failure-days'])
    ok('AC-RUN47', rc47f == 0 and lines47f
       and lines47f[0].endswith(
           ' series_limit=7 series_shown=5 series_outside=1 window_rows=4'
           ' window_head=2026-11-19')
       and 'retry_rows' not in lines47f[0],
       'without the flag the tail is the same line R3026..R3029 shipped')

    # arm 7: refused names, the counted absent= pair, and no byte written
    before47 = tree_bytes(r47)
    rc47g, lines47g = days47(r47, ['--failure-days', '--series-days', '7',
                                   '--series-absent'])
    after47 = tree_bytes(r47)
    text47 = '\n'.join(lines47g)
    ok('AC-RUN47', rc47g == 0 and before47 == after47 and lines47g
       and lines47g[0].count('retry_rows=') == 1
       and 'reading_rows=' not in lines47g[0]
       and 'same_day=' not in lines47g[0]
       and 'new_rows=' not in lines47g[0]
       and lines47g[0].count('absent=') == 2
       and 'PASS' not in text47 and 'FLAG' not in text47
       and 'verdict' not in text47,
       'the split appears once under its own name, the restatement and synonym '
       'names never appear, the older absent= pair still counts two, and no '
       'byte is written')

    # ===== AC-RUN48 (R3031): the window edge cannot cut a day in half =====
    # AC-RUN48 was pinned in src/os/backlog.md BEFORE 'start' existed
    # (qa/probe-R3031.log): membership is decided by the row's own date, so a
    # calendar day is wholly inside or wholly outside, repeat/retry are exact,
    # and what was genuinely unprinted is the day the window starts on.

    def splits48(rows, width):
        head, usable, threshold = RUN._window_start(
            str(rows[-1].get('day') or ''), width)
        if not usable:
            return []
        pre = set(str(r.get('day') or '')[:10] for r in rows
                  if str(r.get('day') or '')[:10] < threshold)
        inside = set(str(r.get('day') or '')[:10] for r in rows
                     if threshold <= str(r.get('day') or '')[:10] <= head)
        return sorted(pre & inside)

    # arm 1: no width 1..10 splits a day, in order or with a stale append
    split_rows48 = [plain_day('2026-11-13', 5), plain_day('2026-11-13', 5),
                    plain_day('2026-11-19', 1), plain_day('2026-11-19', 2),
                    plain_day('2026-11-20', 1)]
    stale48 = [plain_day('2026-11-19', 1), plain_day('2026-11-13', 5),
               plain_day('2026-11-19', 2)]
    widths48 = [splits48(split_rows48, w) for w in range(1, 11)]
    stale_splits48 = [splits48(stale48, w) for w in range(1, 11)]
    ok('AC-RUN48', all(s == [] for s in widths48)
       and all(s == [] for s in stale_splits48),
       'no window width 1..10 can place one calendar day on both sides of the '
       'threshold, in file order or with a stale row appended last')

    # arm 2: the printed start IS the threshold the one window law applied
    r48 = world()
    roots.append(r48)
    p48 = hist37(r48)
    put_days(p48, [plain_day('2026-09-20', 5), plain_day('2026-11-18', 1),
                   plain_day('2026-11-19', 3)])
    rc48, lines48 = days47(r48, ['--failure-days', '--series-days', '7',
                                 '--series-absent'])
    t48 = toks47(lines48[0]) if lines48 else {}
    rc48b, lines48b = days47(r48, ['--failure-days', '--series-days', '6',
                                   '--series-absent'])
    t48b = toks47(lines48b[0]) if lines48b else {}
    pure48 = RUN.series_presence_counts(RUN.read_failure_days(p48)[0], 7)
    head48, _u48, th48 = RUN._window_start('2026-11-19', 7)
    ok('AC-RUN48', rc48 == 0 and rc48b == 0
       and t48.get('window_from') == '2026-11-13'
       and t48.get('window_from') == th48
       and pure48['start'] == '2026-11-13'
       and t48b.get('window_from') == '2026-11-14',
       'the window start is printed and equals the threshold the window law '
       'applied; widening the width moves it one whole day, not one row')

    # arm 3: a day sitting exactly on the cut is wholly in, then wholly out
    r48c = world()
    roots.append(r48c)
    p48c = hist37(r48c)
    put_days(p48c, [plain_day('2026-11-13', 5), plain_day('2026-11-19', 1)])
    rc48c, lines48c = days47(r48c, ['--failure-days', '--series-days', '7',
                                    '--series-absent'])
    rc48d, lines48d = days47(r48c, ['--failure-days', '--series-days', '6',
                                    '--series-absent'])
    t48c = toks47(lines48c[0]) if lines48c else {}
    t48d = toks47(lines48d[0]) if lines48d else {}
    ok('AC-RUN48', rc48c == 0 and rc48d == 0
       and t48c.get('days_present') == '2'
       and t48c.get('repeat_rows') == '0'
       and t48d.get('days_present') == '1'
       and t48d.get('repeat_rows') == '0',
       'the day on the cut counts wholly inside at width 7 and wholly outside '
       'at width 6, and it is never half-counted as a repeat')

    # arm 4: not measurable is not a date
    r48e = world()
    roots.append(r48e)
    os.makedirs(os.path.join(r48e, 'qa'), exist_ok=True)
    rc48e, lines48e = days47(r48e, ['--failure-days', '--series-days', '7',
                                    '--series-absent'])
    t48e = toks47(lines48e[0]) if lines48e else {}
    empty48 = RUN.series_presence_counts([], 7)
    ok('AC-RUN48', rc48e == 0 and t48e.get('window_from') == 'none'
       and t48e.get('days_present') == 'none'
       and empty48['start'] is None,
       'no history answers none for the window start too, and the pure '
       'function invents no date')

    # arm 5: no clock - a 2001 history windows against itself
    r48f = world()
    roots.append(r48f)
    p48f = hist37(r48f)
    put_days(p48f, [plain_day('2001-01-01', 0), plain_day('2001-03-01', 1),
                    plain_day('2001-03-05', 2)])
    rc48f, lines48f = days47(r48f, ['--failure-days', '--series-days', '2',
                                    '--series-absent'])
    t48f = toks47(lines48f[0]) if lines48f else {}
    pure48f = RUN.series_presence_counts(RUN.read_failure_days(p48f)[0], 2)
    ok('AC-RUN48', rc48f == 0 and t48f.get('window_from') == '2001-03-04'
       and pure48f['head'] == '2001-03-05' and pure48f['start'] == '2001-03-04',
       'a two-day window over a 2001 history starts on 2001-03-04 - the file '
       'own last day minus one, no wall clock')

    # arm 6: the default face is byte-identical and carries no new token
    rc48g, lines48g = days47(r47, ['--failure-days'])
    ok('AC-RUN48', rc48g == 0 and lines48g
       and lines48g[0].endswith(
           ' series_limit=7 series_shown=5 series_outside=1 window_rows=4'
           ' window_head=2026-11-19')
       and 'window_from' not in lines48g[0],
       'without the flag the tail is the same line R3026..R3030 shipped')

    # arm 7: refused names, the counted absent= pair, and no byte written
    before48 = tree_bytes(r48)
    rc48h, lines48h = days47(r48, ['--failure-days', '--series-days', '7',
                                   '--series-absent'])
    after48 = tree_bytes(r48)
    text48 = '\n'.join(lines48h)
    ok('AC-RUN48', rc48h == 0 and before48 == after48 and lines48h
       and lines48h[0].count('window_from=') == 1
       and 'edge_rows=' not in lines48h[0]
       and 'split_rows=' not in lines48h[0]
       and 'window_edge=' not in lines48h[0]
       and 'window_start=' not in lines48h[0]
       and lines48h[0].count('absent=') == 2
       and int(toks47(lines48h[0])['retry_rows'])
       <= int(toks47(lines48h[0])['repeat_rows'])
       and 'PASS' not in text48 and 'FLAG' not in text48
       and 'verdict' not in text48,
       'the window start appears once under its own name, the refused edge and '
       'function names never appear, the older absent= pair still counts two, '
       'retry still never exceeds repeat, and no byte is written')

    # ===== AC-RUN49 (R3032): the name list is capped, the total is not =====
    # AC-RUN49 was pinned in src/os/backlog.md BEFORE the cap existed
    # (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3032.log): the absent= list cost exactly 11.00 bytes per name
    # and grew with the window - this checkout's one-row history printed 364
    # names (4310 bytes) on one line at width 365 and 11296 bytes at 1000. The
    # name count always equalled series_absent (8 worlds), no arm pinned the
    # whole line, and a byte budget is not predictable from the window the way
    # "the first 31 silent days" is.
    r49 = world()
    roots.append(r49)
    p49 = hist37(r49)
    put_days(p49, [plain_day('2026-09-20', 5), plain_day('2026-11-18', 1),
                   plain_day('2026-11-19', 3), plain_day('2026-11-19', 1),
                   plain_day('2026-11-19', 2)])

    # arm 1: a seven-day window is complete, so named equals the count
    rc49, lines49 = days47(r49, ['--failure-days', '--series-days', '7',
                                 '--series-absent'])
    t49 = toks47(lines49[0]) if lines49 else {}
    pure49 = RUN.series_absent_days(RUN.read_failure_days(p49)[0], 7)
    ok('AC-RUN49', rc49 == 0 and t49.get('series_absent') == '5'
       and t49.get('absent_named') == '5'
       and len((t49.get('absent') or '').split(',')) == 5
       and pure49['named'] == 5 and pure49['count'] == 5
       and pure49['truncated'] is False,
       'a seven-day window names all five silent days, and the printed named '
       'count equals the printed total so no truncation is implied')

    # arm 2: a sixty-day window names one month and counts the rest
    rc49b, lines49b = days47(r49, ['--failure-days', '--series-days', '60',
                                   '--series-absent'])
    t49b = toks47(lines49b[0]) if lines49b else {}
    named49b = (t49b.get('absent') or '').split(',')
    pure49b = RUN.series_absent_days(RUN.read_failure_days(p49)[0], 60)
    ok('AC-RUN49', rc49b == 0 and t49b.get('series_absent') == '58'
       and t49b.get('absent_named') == '31'
       and len(named49b) == 31
       and named49b[0] == t49b.get('window_from')
       and named49b[-1] == '2026-10-21'
       and '2026-10-22' not in named49b
       and pure49b['count'] == 58 and pure49b['named'] == 31
       and pure49b['truncated'] is True,
       'a sixty-day window names its first 31 silent days from the window '
       'start and stops, while series_absent keeps the full 58')

    # arm 3: the boundary is the 32nd day - 31 gaps fit, 32 do not
    r49c = world()
    roots.append(r49c)
    p49c = hist37(r49c)
    put_days(p49c, [plain_day('2026-11-19', 0)])
    rc49c, lines49c = days47(r49c, ['--failure-days', '--series-days', '32',
                                    '--series-absent'])
    t49c = toks47(lines49c[0]) if lines49c else {}
    rc49d, lines49d = days47(r49c, ['--failure-days', '--series-days', '33',
                                    '--series-absent'])
    t49d = toks47(lines49d[0]) if lines49d else {}
    ok('AC-RUN49', rc49c == 0 and t49c.get('series_absent') == '31'
       and t49c.get('absent_named') == '31'
       and rc49d == 0 and t49d.get('series_absent') == '32'
       and t49d.get('absent_named') == '31',
       'thirty-one gaps print whole and thirty-two print one short - the cap '
       'sits on the name count, not on the window width')

    # arm 4: under truncation the total never shrinks to the printed count
    rc49e, lines49e = days47(r49, ['--failure-days', '--series-days', '365',
                                   '--series-absent'])
    t49e = toks47(lines49e[0]) if lines49e else {}
    named49e = (t49e.get('absent') or '').split(',')
    ok('AC-RUN49', rc49e == 0
       and int(t49e['series_absent']) == 362
       and int(t49e.get('absent_named')) == 31
       and len(named49e) == 31
       and t49e['series_absent'] != t49e.get('absent_named'),
       'a year-wide window keeps the full 362 gaps (365 days, three holding '
       'rows) as the total and prints 31 names - a truncated list never reads '
       'as few gaps')

    # arm 5: no clock - a 2001 history is capped against its own last row
    r49f = world()
    roots.append(r49f)
    p49f = hist37(r49f)
    put_days(p49f, [plain_day('2001-01-01', 0), plain_day('2001-03-01', 1),
                    plain_day('2001-03-05', 2)])
    rc49f, lines49f = days47(r49f, ['--failure-days', '--series-days', '90',
                                    '--series-absent'])
    t49f = toks47(lines49f[0]) if lines49f else {}
    pure49f = RUN.series_absent_days(RUN.read_failure_days(p49f)[0], 90)
    ok('AC-RUN49', rc49f == 0 and t49f.get('window_from') == '2000-12-06'
       and t49f.get('absent_named') == '31'
       and int(t49f['series_absent']) == 87
       and pure49f['head'] == '2001-03-05'
       and t49f.get('absent').startswith('2000-12-06'),
       'a ninety-day window over a 2001 history opens from the file own last '
       'row and caps at 31 of its 87 names with no wall clock')

    # arm 6: without the flag the tail is byte-identical and carries no token
    rc49g, lines49g = days47(r49, ['--failure-days'])
    ok('AC-RUN49', rc49g == 0 and lines49g
       and lines49g[0].endswith(
           ' series_limit=7 series_shown=5 series_outside=1 window_rows=4'
           ' window_head=2026-11-19')
       and 'absent_named' not in lines49g[0],
       'without the flag the tail is the same line R3026..R3031 shipped and '
       'the new token does not appear')

    # arm 7: pure display, bounded width, and the older absent= pair intact
    before49 = tree_bytes(r49)
    rc49h, lines49h = days47(r49, ['--failure-days', '--series-days', '1000',
                                   '--series-absent'])
    after49 = tree_bytes(r49)
    text49 = '\n'.join(lines49h)
    t49h = toks47(lines49h[0]) if lines49h else {}
    ok('AC-RUN49', rc49h == 0 and before49 == after49 and lines49h
       and len(lines49h[0]) < 1000
       and lines49h[0].count('absent_named=') == 1
       and lines49h[0].count('absent=') == 2
       and int(t49h.get('absent_named'))
       <= int(t49h['series_absent'])
       and 'PASS' not in text49 and 'FLAG' not in text49
       and 'verdict' not in text49,
       'a thousand-day window still prints under 1000 bytes, the new token '
       'appears once and never exceeds the total, the older absent= pair '
       'still counts two, no verdict prints, and no byte is written')

    # ===== AC-RUN50 (R3033): the silent-day list can be asked for in full =====
    # AC-RUN50 was pinned in src/os/backlog.md BEFORE the flag existed
    # (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3033.log): two private worlds that differ only in three HIDDEN
    # row days printed BYTE-IDENTICAL lines (days_present=10, series_absent=50,
    # absent_named=31), so the 19 unnamed silent days are not recoverable from
    # the line; the premise "unprintable anywhere" measured FALSE because
    # --failure-days-dropped prints every usable row's day (one invocation plus
    # a set subtraction); and an opt-in flag collides with nothing (6 arms count
    # absent= twice, 1 counts absent_named= once, 0 whole-line equality arms
    # carry absent=, the default face is 214 bytes).

    def days50(root, extra):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = RUN.main(list(extra) + ['--root', root])
        return (rc, [n for n in out.getvalue().splitlines() if n.strip()],
                err.getvalue())

    r50 = world()
    roots.append(r50)
    p50 = hist37(r50)
    put_days(p50, [plain_day('2026-09-01', 1),
                   plain_day('2026-10-25', 21), plain_day('2026-10-26', 22),
                   plain_day('2026-10-27', 23)]
             + [plain_day('2026-11-%02d' % d, d - 8) for d in range(13, 20)])
    base50 = ['--failure-days', '--series-days', '60', '--series-absent']

    # arm 1: the default face is unchanged - one month of names, no new token
    rc50, lines50, err50 = days50(r50, base50)
    t50 = toks47(lines50[0]) if lines50 else {}
    names50 = (t50.get('absent') or '').split(',')
    ok('AC-RUN50', rc50 == 0 and lines50
       and t50.get('series_absent') == '50'
       and t50.get('absent_named') == '31'
       and len(names50) == 31 and names50[-1] == '2026-10-21'
       and lines50[0].count('absent=') == 2
       and lines50[0].count('absent_named=') == 1
       and 'limit=' not in lines50[0].replace('series_limit=', ''),
       'without the flag a sixty-day window still names one month of its 50 '
       'silent days and prints no new token')

    # arm 2: all names the whole set, and the total is still the total
    rc50b, lines50b, _e = days50(r50, base50 + ['--series-absent-limit', 'all'])
    t50b = toks47(lines50b[0]) if lines50b else {}
    names50b = (t50b.get('absent') or '').split(',')
    ok('AC-RUN50', rc50b == 0 and t50b.get('absent_named') == '50'
       and t50b.get('series_absent') == '50'
       and len(names50b) == 50 and len(set(names50b)) == 50
       and names50b[0] == t50b.get('window_from') == '2026-09-21'
       and names50b[-1] == '2026-11-12'
       and lines50b[0].count('absent=') == 2,
       'all prints every one of the 50 silent days once, ascending, from the '
       'window start, and named equals the full total')

    # arm 3: a small cap names that many and never shrinks the total
    rc50c, lines50c, _e = days50(r50, base50 + ['--series-absent-limit', '5'])
    t50c = toks47(lines50c[0]) if lines50c else {}
    ok('AC-RUN50', rc50c == 0 and t50c.get('absent_named') == '5'
       and t50c.get('series_absent') == '50'
       and len((t50c.get('absent') or '').split(',')) == 5,
       'a cap of five names five days while series_absent stays 50 - the cap '
       'never edits the count')

    # arm 4: a cap wider than the gap count invents nothing
    rc50d, lines50d, _e = days50(r50, base50 + ['--series-absent-limit', '100'])
    t50d = toks47(lines50d[0]) if lines50d else {}
    names50d = (t50d.get('absent') or '').split(',')
    ok('AC-RUN50', rc50d == 0 and t50d.get('absent_named') == '50'
       and len(names50d) == 50 and len(set(names50d)) == 50,
       'asking for more names than there are gaps prints the 50 real days and '
       'no invented ones')

    # arm 5: zero, negative and non-numeric caps are refused, not coerced
    refused50 = []
    for bad in ('0', '-1', 'abc'):
        rc50e, lines50e, err50e = days50(
            r50, base50 + ['--series-absent-limit', bad])
        refused50.append(rc50e == 2 and not lines50e
                         and '--series-absent-limit' in err50e)
    ok('AC-RUN50', all(refused50),
       'a zero cap (which would read as "no silent days"), a negative one and '
       'a word are all refused with rc=2 and nothing printed')

    # arm 6: the flag alone is refused rather than silently ignored
    rc50f, lines50f, err50f = days50(
        r50, ['--failure-days', '--series-days', '60',
              '--series-absent-limit', 'all'])
    ok('AC-RUN50', rc50f == 2 and not lines50f
       and '--series-absent' in err50f,
       'the limit without --series-absent is refused, so a person cannot '
       'believe a cap applied to a list that was not asked for')

    # arm 7: on a complete window the flag changes nothing at all
    r50b = world()
    roots.append(r50b)
    p50b = hist37(r50b)
    put_days(p50b, [plain_day('2026-11-19', 0)])
    short50 = ['--failure-days', '--series-days', '32', '--series-absent']
    rc50g, lines50g, _e = days50(r50b, short50)
    rc50h, lines50h, _e = days50(r50b, short50 + ['--series-absent-limit', 'all'])
    ok('AC-RUN50', rc50g == 0 and rc50h == 0 and lines50g == lines50h
       and toks47(lines50h[0]).get('absent_named') == '31',
       'a window whose gaps all fit prints byte-identically with and without '
       'all, so the cap only acts where it really truncates')

    # arm 8: pure display, and the parser refuses without a process
    before50 = tree_bytes(r50)
    rc50i, lines50i, _e = days50(r50, base50)
    after50 = tree_bytes(r50)
    text50 = '\n'.join(lines50i)
    t50i = toks47(lines50i[0]) if lines50i else {}
    pure50 = [RUN.parse_absent_limit(None)[0] == RUN.ABSENT_LIST_LIMIT,
              RUN.parse_absent_limit('all') == (None, None),
              RUN.parse_absent_limit('7') == (7, None),
              all(RUN.parse_absent_limit(b)[1] is not None
                  for b in ('0', '-1', 'abc'))]
    ok('AC-RUN50', rc50i == 0 and before50 == after50
       and int(t50i.get('absent_named')) <= int(t50i['series_absent'])
       and all(pure50)
       and 'PASS' not in text50 and 'FLAG' not in text50
       and 'verdict' not in text50,
       'the honest parser answers the default, all, a number and three '
       'refusals, the shown count never exceeds the total, no verdict prints '
       'and no byte is written')

    # ===== AC-RUN51 (R3034): the price of all is readable before asking =====
    # AC-RUN51 was pinned in src/os/backlog.md BEFORE absent_all_bytes existed
    # (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3034.log): a name is exactly 10 characters, so the list costs
    # 11n-1 bytes (31 names 340B, 50 names 549B); the base line without the
    # absent= token is byte-identical at every cap (401B); the capped line was
    # 748B and the all line 957B (delta 209, exactly the list delta); no shipped
    # face estimated an OUTPUT length; and the new token contains neither
    # pinned substring.

    def price51(root, extra):
        rc, lines, err = days50(root, extra)
        return rc, (toks47(lines[0]) if lines else {}), lines

    r51 = world()
    roots.append(r51)
    p51 = hist37(r51)
    put_days(p51, [plain_day('2026-09-01', 1),
                   plain_day('2026-10-25', 21), plain_day('2026-10-26', 22),
                   plain_day('2026-10-27', 23)]
             + [plain_day('2026-11-%02d' % d, d - 8) for d in range(13, 20)])
    base51 = ['--failure-days', '--series-days', '60', '--series-absent']

    # arm 1: the default face carries no price token at all
    rc51a, lines51a, _e = days50(r51, ['--failure-days'])
    plain51 = RUN.series_window_counts(RUN.read_failure_days(p51)[0], 7, 7)
    tail51 = (' series_limit=%d series_shown=%d series_outside=%d '
              'window_rows=%d window_head=%s'
              % (plain51['limit'], plain51['shown'], plain51['outside'],
                 plain51['window_rows'],
                 RUN._day_face_head(RUN.read_failure_days(p51)[0])))
    ok('AC-RUN51', rc51a == 0 and lines51a
       and 'absent_all_bytes' not in lines51a[0]
       and 'series_absent' not in lines51a[0]
       and lines51a[0].endswith(tail51),
       'without the flag the default tail keeps the unflagged four-count shape '
       'plus the R3046 window anchor, and no price token appears')

    # arm 2: the price printed by the CAPPED run equals the real all-run length
    rc51b, t51b, _l = price51(r51, base51)
    rc51c, t51c, lines51c = price51(r51, base51 + ['--series-absent-limit', 'all'])
    ok('AC-RUN51', rc51b == 0 and rc51c == 0
       and (t51b.get('absent_all_bytes') or '').isdigit()
       and t51b.get('absent_all_bytes') == str(len(lines51c[0].encode('utf-8')))
       and t51c.get('absent_named') == t51c.get('series_absent') == '50',
       'the price read on the capped line equals the byte length of the line a '
       'person gets by asking for all, and that line names its full total - a '
       'real invariant, not self-assertion')

    # arm 3: the ask does not move the target - every cap quotes one price
    rc51d, t51d, _l = price51(r51, base51 + ['--series-absent-limit', '5'])
    ok('AC-RUN51', rc51d == 0
       and t51d.get('absent_all_bytes') == t51b.get('absent_all_bytes')
       and t51d.get('absent_named') == '5'
       and t51d.get('series_absent') == '50',
       'a cap of five quotes the same price as the default cap - the number '
       'describes the full list, not the list in hand')

    # arm 4: on a complete window the price equals the line that prints
    r51b = world()
    roots.append(r51b)
    p51b = hist37(r51b)
    put_days(p51b, [plain_day('2026-11-%02d' % d, d - 8) for d in range(13, 20)]
             + [plain_day('2026-11-15', 9)])
    rc51e, lines51e, _e = days50(r51b, ['--failure-days', '--series-days', '7',
                                       '--series-absent'])
    t51e = toks47(lines51e[0]) if lines51e else {}
    ok('AC-RUN51', rc51e == 0 and lines51e
       and t51e.get('absent_all_bytes') == str(len(lines51e[0].encode('utf-8')))
       and t51e.get('absent_named') == t51e.get('series_absent'),
       'a window whose gaps all fit prices itself, so the number equals the '
       'line the reader is already holding')

    # arm 5: an unusable head answers none rather than an invented zero
    r51c = world()
    roots.append(r51c)
    put_days(hist37(r51c), [])
    rc51f, lines51f, _e = days50(r51c, ['--failure-days', '--series-days', '7',
                                       '--series-absent'])
    t51f = toks47(lines51f[0]) if lines51f else {}
    ok('AC-RUN51', rc51f == 0 and t51f.get('absent_all_bytes') == 'none'
       and t51f.get('absent_named') == 'none',
       'an empty history prices nothing rather than a zero that would read as '
       'a free line')

    # arm 6: pure display, pinned counts intact, 2001 history, no clock
    before51 = tree_bytes(r51)
    rc51g, lines51g, _e = days50(r51, base51)
    after51 = tree_bytes(r51)
    text51 = '\n'.join(lines51g)
    r51d = world()
    roots.append(r51d)
    p51d = hist37(r51d)
    put_days(p51d, [plain_day('2001-03-04', 1), plain_day('2001-03-05', 2)])
    rc51h, lines51h, _e = days50(r51d, ['--failure-days', '--series-days', '7',
                                       '--series-absent'])
    t51h = toks47(lines51h[0]) if lines51h else {}
    ok('AC-RUN51', rc51g == 0 and before51 == after51 and lines51g
       and lines51g[0].count('absent=') == 2
       and lines51g[0].count('absent_named=') == 1
       and 'PASS' not in text51 and 'FLAG' not in text51
       and 'verdict' not in text51
       and rc51h == 0 and lines51h
       and t51h.get('absent_all_bytes') == str(len(lines51h[0].encode('utf-8')))
       and t51h.get('window_from') == '2001-02-27',
       'no byte is written, no verdict prints, the two pinned counts hold, and '
       'a 2001 history prices its own window with no wall clock')

    # ===== AC-RUN52 (R3035): the price of the full block is on the header =====
    # AC-RUN52 was pinned in src/os/backlog.md BEFORE rows_all_bytes existed
    # (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3035.log): day lines measured 39/36/36/41 characters on one
    # four-row world (day= fixed 10, dropped= variable), two worlds with the
    # same counts printed 156B vs 148B, no shipped face estimated a multi-line
    # total, and one arm pinned the windowed header by equality (extended).
    def blk52(lines):
        return sum(len((n + '\n').encode('utf-8')) for n in lines
                   if n.startswith('DAY-DROPPED '))

    r52 = world()
    roots.append(r52)
    p52 = hist37(r52)
    put_days(p52, [plain_day('2026-11-05', 1),
                   plain_day('2026-11-06', 1, dropped=0),
                   plain_day('2026-11-07', 1, dropped=7),
                   plain_day('2026-11-08', 1, dropped=123456)])

    # arm 1: the price equals the block an unwindowed run really prints
    rc52a, l52a = dd41(r52)
    rc52b, l52b = dd41(r52, 2)
    t52b = toks47(l52b[0]) if l52b else {}
    full52 = blk52(l52a)
    ok('AC-RUN52', rc52a == 0 and rc52b == 0 and full52 > 0
       and t52b.get('truncated') == '1' and t52b.get('shown') == '2'
       and t52b.get('rows_all_bytes') == str(full52)
       and blk52(l52b) < full52,
       'the windowed header prices the whole block and that number equals the '
       'bytes the unwindowed run of the same file really prints')

    # arm 2: the price does not move with the window - it prices the file
    rc52c, l52c = dd41(r52, 30)
    t52c = toks47(l52c[0]) if l52c else {}
    ok('AC-RUN52', rc52c == 0 and t52c.get('truncated') == '0'
       and t52c.get('rows_all_bytes') == t52b.get('rows_all_bytes')
       and t52c.get('rows_all_bytes') == str(full52),
       'a window that truncates nothing quotes the same price, so the number '
       'describes the file rather than the window in hand')

    # arm 3: equal counts, different dropped widths - the price is not counts
    r52d = world()
    roots.append(r52d)
    put_days(hist37(r52d), [plain_day('2026-11-05', 1, dropped=1),
                            plain_day('2026-11-06', 1, dropped=1),
                            plain_day('2026-11-07', 1, dropped=1),
                            plain_day('2026-11-08', 1, dropped=1)])
    rc52d, l52d = dd41(r52d)
    rc52e, l52e = dd41(r52d, 2)
    t52e = toks47(l52e[0]) if l52e else {}
    narrow52 = blk52(l52d)
    ok('AC-RUN52', rc52d == 0 and rc52e == 0
       and t52e.get('rows_all_bytes') == str(narrow52)
       and narrow52 != full52
       and blk52(l52e) < narrow52,
       'two files with the same counts but different dropped widths price '
       'differently, and each price is exact - the number is bytes, not rows')

    # arm 4: an empty history prices 0, prints no row and does not raise
    r52f = world()
    roots.append(r52f)
    put_days(hist37(r52f), [])
    rc52f, l52f = dd41(r52f, 5)
    t52f = toks47(l52f[0]) if l52f else {}
    ok('AC-RUN52', rc52f == 0 and l52f and t52f.get('rows_all_bytes') == '0'
       and len(day_rows_41(l52f)) == 0,
       'an empty history under a window prices zero bytes with no day line, '
       'which is the same absence-is-zero law the reader already uses')

    # arm 5: the unwindowed face keeps its bytes and carries no price token
    ok('AC-RUN52', rc52a == 0 and l52a[0] == 'CRAWL-FAILURE-DAYS-DROPPED '
       'days=4 bad=0' and 'rows_all_bytes' not in l52a[0]
       and len(day_rows_41(l52a)) == 4,
       'the default face is byte-identical to its two pinned arms and gains no '
       'token - a full listing needs no forecast')

    # arm 6: pure display, no verdict, and the pinned absent= counts survive
    before52 = tree_bytes(r52)
    rc52g, l52g = dd41(r52, 2)
    after52 = tree_bytes(r52)
    text52 = '\n'.join(l52g)
    rc52h, l52h, _e = days50(r52, ['--failure-days', '--series-days', '7',
                                   '--series-absent'])
    ok('AC-RUN52', rc52g == 0 and before52 == after52
       and 'PASS' not in text52 and 'FLAG' not in text52
       and 'verdict' not in text52
       and rc52h == 0 and l52h and l52h[0].count('absent=') == 2
       and l52h[0].count('absent_named=') == 1,
       'no byte is written, no verdict prints, and the two counts the silent '
       'faces pin still hold on the same world')

    for root in roots:
        shutil.rmtree(root, ignore_errors=True)

    # ===== AC-RUN53 (R3036): the whole output's price is on its own header ====
    # PINNED in src/os/backlog.md BEFORE dropped_output_bytes existed
    # (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3036.log): one 6-row file printed 112/113/114-byte headers and
    # a 236/354/355-byte stdout at N=3/30/365 while the block stayed 240B at
    # both N=30 and N=365, no shipped face composed header + block (three
    # candidate tokens, zero code hits), and exactly one whole-line equality
    # arm (AC-RUN41 arm 8) had to be extended.
    def blk53(lines):
        return sum(len((n + '\n').encode('utf-8')) for n in lines
                   if n.startswith('DAY-DROPPED '))

    def dd53(root, window=None):
        argv = ['--failure-days-dropped', '--root', root]
        if window is not None:
            argv = ['--failure-days-dropped',
                    '--failure-days-dropped-window', str(window),
                    '--root', root]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(argv)
        text = buf.getvalue()
        return rc, [n for n in text.splitlines() if n.strip()], text

    r53 = world()
    roots.append(r53)
    put_days(hist37(r53), [plain_day('2026-11-05', 1),
                           plain_day('2026-11-06', 1, dropped=0),
                           plain_day('2026-11-07', 1, dropped=7),
                           plain_day('2026-11-08', 1, dropped=123456)])

    # arm 1: the number equals the real byte length of this run's stdout
    rc53a, l53a, raw53a = dd53(r53, 2)
    t53a = toks47(l53a[0]) if l53a else {}
    ok('AC-RUN53', rc53a == 0 and l53a
       and t53a.get('output_bytes') == str(len(raw53a.encode('utf-8')))
       and int(t53a.get('output_bytes')) > 0,
       'the windowed header prices the whole run and that number equals the '
       'LF text bytes the run really printed, measured from the output itself')

    # arm 2: the number decomposes into header + one newline + printed block
    head53 = len(l53a[0].encode('utf-8')) + 1
    ok('AC-RUN53', rc53a == 0 and l53a
       and int(t53a.get('output_bytes')) == head53 + blk53(l53a),
       'the total is exactly the header line plus the block this run prints, '
       'so a reader can see what each half costs')

    # arm 3: two windows on one file each price their own shape, and the
    # truncated one costs less - widening really does print more
    rc53b, l53b, raw53b = dd53(r53, 365)
    t53b = toks47(l53b[0]) if l53b else {}
    ok('AC-RUN53', rc53b == 0 and l53b and t53a and t53b
       and t53b.get('truncated') == '0'
       and t53b.get('output_bytes') == str(len(raw53b.encode('utf-8')))
       and int(t53b.get('output_bytes')) > int(t53a.get('output_bytes')),
       'a window that hides nothing prices its own larger total exactly, so '
       'the width of the printed listing is what the number tracks')

    # arm 4: an empty history under a window prices its bare header exactly
    r53c = world()
    roots.append(r53c)
    put_days(hist37(r53c), [])
    rc53c, l53c, raw53c = dd53(r53c, 5)
    t53c = toks47(l53c[0]) if l53c else {}
    ok('AC-RUN53', rc53c == 0 and l53c
       and t53c.get('output_bytes') == str(len(raw53c.encode('utf-8')))
       and len(day_rows_41(l53c)) == 0 and t53c.get('head') == 'none',
       'an empty history prices exactly the header it prints, with no day line '
       'and no raise - absence is still zero')

    # arm 5: the default face keeps its bytes and carries no total token
    rc53d, l53d, raw53d = dd53(r53)
    ok('AC-RUN53', rc53d == 0 and l53d
       and l53d[0] == 'CRAWL-FAILURE-DAYS-DROPPED days=4 bad=0'
       and 'output_bytes' not in l53d[0]
       and len(day_rows_41(l53d)) == 4,
       'the unwindowed face is byte-identical and gains no token - a full '
       'listing needs no price')

    # arm 6: pure display, no verdict, and the pinned absent= counts survive
    before53 = tree_bytes(r53)
    rc53e, l53e, _raw53e = dd53(r53, 2)
    after53 = tree_bytes(r53)
    text53 = '\n'.join(l53e)
    rc53f, l53f, _e53 = days50(r53, ['--failure-days', '--series-days', '7',
                                     '--series-absent'])
    ok('AC-RUN53', rc53e == 0 and before53 == after53
       and 'PASS' not in text53 and 'FLAG' not in text53
       and 'verdict' not in text53
       and rc53f == 0 and l53f and l53f[0].count('absent=') == 2
       and l53f[0].count('absent_named=') == 1,
       'no byte is written, no verdict prints, and the two counts the silent '
       'faces pin still hold on the same world')

    for root in roots:
        shutil.rmtree(root, ignore_errors=True)

    # ===== AC-RUN54 (R3037): both halves of the total are on the header =======
    # PINNED in src/os/backlog.md BEFORE shown_bytes existed (in-window
    # pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3037.log): on one 6-row file `output_bytes - rows_all_bytes`
    # read 132 (= header+1) unwindowed but 13 at N=3 and -24 at N=2 against a
    # 130-byte header, because rows_all_bytes prices the whole FILE; no shipped
    # key priced this run's own block (six candidate tokens, zero hits under
    # tools/ and src/), and `shown_bytes` collides with zero suite arms.
    r54 = world()
    roots.append(r54)
    put_days(hist37(r54), [plain_day('2026-11-05', 1),
                           plain_day('2026-11-06', 1, dropped=0),
                           plain_day('2026-11-07', 1, dropped=7),
                           plain_day('2026-11-08', 1, dropped=123456)])

    rc54a, l54a, _raw54a = dd53(r54, 2)
    t54a = toks47(l54a[0]) if l54a else {}
    head54 = len(l54a[0].encode('utf-8')) if l54a else 0

    # arm 1: the block price equals the block this very run printed
    ok('AC-RUN54', rc54a == 0 and l54a and t54a.get('shown_bytes') == str(
        blk53(l54a)) and int(t54a.get('shown_bytes')) > 0,
       'the windowed header prices the block this run prints, and the number is '
       'measured off that run\'s own output rather than re-derived')

    # arm 2: with both halves on the line, the header's own cost is subtraction
    ok('AC-RUN54', rc54a == 0 and l54a
       and int(t54a.get('output_bytes')) - 1 - int(t54a.get('shown_bytes'))
       == head54,
       'output_bytes minus one newline minus shown_bytes equals the real header '
       'width, so a truncated window\'s two halves are readable without a '
       'second run')

    # arm 3: the two windows price different blocks while the full-file price
    # stays put, and the old subtraction is pinned as WRONG on a truncation
    rc54b, l54b, _raw54b = dd53(r54, 365)
    t54b = toks47(l54b[0]) if l54b else {}
    ok('AC-RUN54', rc54b == 0 and l54b and t54b.get('truncated') == '0'
       and t54a.get('shown_bytes') and t54b.get('shown_bytes')
       and int(t54a.get('shown_bytes')) < int(t54b.get('shown_bytes'))
       and t54a.get('rows_all_bytes') == t54b.get('rows_all_bytes')
       and int(t54a.get('output_bytes')) - int(t54a.get('rows_all_bytes'))
       != head54,
       'a narrow window prices a smaller block than a wide one while the '
       'full-file price is identical in both, which is exactly why '
       'output_bytes - rows_all_bytes cannot stand in for the header cost')

    # arm 4: an empty history under a window prices a zero block
    r54c = world()
    roots.append(r54c)
    put_days(hist37(r54c), [])
    rc54c, l54c, _raw54c = dd53(r54c, 5)
    t54c = toks47(l54c[0]) if l54c else {}
    ok('AC-RUN54', rc54c == 0 and l54c and t54c.get('shown_bytes') == '0'
       and int(t54c.get('output_bytes'))
       == len(l54c[0].encode('utf-8')) + 1
       and len(day_rows_41(l54c)) == 0,
       'an empty history prices a zero block and its total is exactly the bare '
       'header plus one newline - absence is still zero on both halves')

    # arm 5: the default face keeps its bytes and gains neither new token
    rc54d, l54d, _raw54d = dd53(r54)
    ok('AC-RUN54', rc54d == 0 and l54d
       and l54d[0] == 'CRAWL-FAILURE-DAYS-DROPPED days=4 bad=0'
       and 'shown_bytes' not in l54d[0] and 'output_bytes' not in l54d[0]
       and len(day_rows_41(l54d)) == 4,
       'the unwindowed face is byte-identical and carries neither price token - '
       'a full listing needs no forecast')

    # arm 6: pure display, no verdict, and the pinned absent= counts survive
    before54 = tree_bytes(r54)
    rc54e, l54e, _raw54e = dd53(r54, 2)
    after54 = tree_bytes(r54)
    text54 = '\n'.join(l54e)
    rc54f, l54f, _e54 = days50(r54, ['--failure-days', '--series-days', '7',
                                     '--series-absent'])
    ok('AC-RUN54', rc54e == 0 and before54 == after54
       and 'PASS' not in text54 and 'FLAG' not in text54
       and 'verdict' not in text54
       and rc54f == 0 and l54f and l54f[0].count('absent=') == 2
       and l54f[0].count('absent_named=') == 1,
       'no byte is written, no verdict prints, and the two counts the silent '
       'faces pin still hold on the same world')

    for root in roots:
        shutil.rmtree(root, ignore_errors=True)

    # ===== AC-RUN55 (R3038): the header prices its own width =================
    # PINNED in src/os/backlog.md BEFORE header_bytes existed (in-window
    # pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3038.log): `output_bytes - c - shown_bytes` equals the real
    # header width only at c=1 on two windows, no printed integer key equals
    # that width, and header_bytes/newline_bytes had zero hits over 2599
    # python files while `lines=` was already refused on the DAYS face (R3000).
    r55 = world()
    roots.append(r55)
    put_days(hist37(r55), [plain_day('2026-11-05', 1, dropped=1),
                           plain_day('2026-11-06', 1, dropped=0),
                           plain_day('2026-11-07', 1, dropped=7),
                           plain_day('2026-11-08', 1, dropped=123456)])

    rc55a, l55a, _raw55a = dd53(r55, 2)
    t55a = toks47(l55a[0]) if l55a else {}
    head55 = (len(l55a[0].encode('utf-8')) + 1) if l55a else 0

    # arm 1: the header's half equals the real line it came from, newline in
    ok('AC-RUN55', rc55a == 0 and l55a
       and t55a.get('header_bytes') == str(head55) and head55 > 1,
       'the windowed header prices its own slice of the total - the line that '
       'run actually printed plus its newline')

    # arm 2: the two halves add up exactly, so no constant is assumed anywhere
    ok('AC-RUN55', rc55a == 0 and l55a
       and int(t55a.get('header_bytes')) + int(t55a.get('shown_bytes'))
       == int(t55a.get('output_bytes')),
       'header_bytes + shown_bytes equals output_bytes, so the reader splits '
       'the total with no unwritten newline constant')

    # arm 3: two windows price their own header exactly; the file price is fixed
    rc55b, l55b, _raw55b = dd53(r55, 365)
    t55b = toks47(l55b[0]) if l55b else {}
    head55b = (len(l55b[0].encode('utf-8')) + 1) if l55b else 0
    ok('AC-RUN55', rc55b == 0 and l55b and t55b.get('truncated') == '0'
       and t55a.get('header_bytes') and t55b.get('header_bytes')
       and t55b.get('header_bytes') == str(head55b)
       and int(t55a.get('header_bytes')) != int(t55b.get('header_bytes'))
       and t55a.get('rows_all_bytes') == t55b.get('rows_all_bytes'),
       'each window prices its own header exactly - the widths differ because '
       'the window token itself is wider - while the full-file block price '
       'stays identical in both')

    # arm 4: an empty history prices its bare header exactly
    r55c = world()
    roots.append(r55c)
    put_days(hist37(r55c), [])
    rc55c, l55c, _raw55c = dd53(r55c, 5)
    t55c = toks47(l55c[0]) if l55c else {}
    ok('AC-RUN55', rc55c == 0 and l55c
       and t55c.get('header_bytes') == str(len(l55c[0].encode('utf-8')) + 1)
       and int(t55c.get('output_bytes')) == int(t55c.get('header_bytes'))
       and len(day_rows_41(l55c)) == 0,
       'an empty history prices its bare header, and the total equals that '
       'number exactly with no day line')

    # arm 5: the default face keeps its bytes and gains no token
    rc55d, l55d, _raw55d = dd53(r55)
    ok('AC-RUN55', rc55d == 0 and l55d
       and l55d[0] == 'CRAWL-FAILURE-DAYS-DROPPED days=4 bad=0'
       and 'header_bytes' not in l55d[0]
       and len(day_rows_41(l55d)) == 4,
       'the unwindowed face is byte-identical and carries no header price')

    # arm 6: pure display, no verdict, and the pinned absent= counts survive
    before55 = tree_bytes(r55)
    rc55e, l55e, _raw55e = dd53(r55, 2)
    after55 = tree_bytes(r55)
    text55 = '\n'.join(l55e)
    rc55f, l55f, _e55 = days50(r55, ['--failure-days', '--series-days', '7',
                                     '--series-absent'])
    ok('AC-RUN55', rc55e == 0 and before55 == after55
       and 'PASS' not in text55 and 'FLAG' not in text55
       and 'verdict' not in text55
       and rc55f == 0 and l55f and l55f[0].count('absent=') == 2
       and l55f[0].count('absent_named=') == 1,
       'no byte is written, no verdict prints, and the two counts the silent '
       'faces pin still hold on the same world')

    # ===== AC-RUN56 (R3039): the silent-day line prices itself =====
    # AC-RUN56 was pinned in src/os/backlog.md BEFORE absent_line_prices took
    # its second prefix (in-window pre-registration, disclosed). Measured
    # before the pin (qa/probe-R3039.log, 20 runs over window 3/7/30/60/365 x
    # cap default/5/31/all): `absent_all_bytes` equalled the real line width in
    # exactly the eight runs that named every gap, and on the wide-window
    # DEFAULT (win=60: 685B vs 993B all; win=365: 688B vs 4352B) no printed
    # integer key equalled it.
    def sd56(root, extra):
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = RUN.main(['--failure-days'] + list(extra) + ['--root', root])
        text = buf.getvalue()
        return rc, [n for n in text.splitlines() if n.strip()], text

    r56 = world()
    roots.append(r56)
    p56 = hist37(r56)
    put_days(p56, [plain_day('2026-11-19', 3), plain_day('2026-11-19', 1)])

    def lf56(text):
        return len(text.replace('\r\n', '\n').encode('utf-8'))

    # arm 1: on the wide-window default the line prices itself, exactly
    rc56a, l56a, raw56a = sd56(r56, ['--series-days', '60',
                                     '--series-absent'])
    t56a = toks42(l56a[0]) if l56a else {}
    real56a = len(l56a[0].encode('utf-8')) if l56a else -1
    ok('AC-RUN56', rc56a == 0 and t56a.get('line_bytes') == str(real56a)
       and t56a.get('output_bytes') == str(lf56(raw56a))
       and int(t56a.get('line_bytes') or -1) + 1
       == int(t56a.get('output_bytes') or -2)
       and t56a.get('absent_named') != t56a.get('series_absent'),
       'line_bytes reads the real width of the line it sits on and '
       'output_bytes the real stdout bytes, so the trailing newline is the '
       'printed difference rather than an assumed 1 - on the truncated default '
       'where no other key came close')

    # arm 2: the pair of prices - all-names equal, truncated strictly larger
    rc56b, l56b, _raw56b = sd56(r56, ['--series-days', '60',
                                      '--series-absent',
                                      '--series-absent-limit', 'all'])
    t56b = toks42(l56b[0]) if l56b else {}
    gap56 = (int(t56a.get('absent_all_bytes') or -1)
             - int(t56a.get('line_bytes') or -1))
    lost56 = (int(t56a.get('series_absent') or 0)
              - int(t56a.get('absent_named') or 0))
    ok('AC-RUN56', rc56b == 0
       and t56b.get('absent_all_bytes') == t56b.get('line_bytes')
       and int(t56a.get('absent_all_bytes') or -1)
       > int(t56a.get('line_bytes') or -1)
       and gap56 >= 11 * lost56,
       'with every gap named the projection IS this line (equal), and on the '
       'truncated run it is strictly larger by at least eleven bytes per '
       'silently dropped name - a lower bound, since the wider numbers can add '
       'digits of their own')

    # arm 3: two windows, two different widths, both exact
    rc56c, l56c, _raw56c = sd56(r56, ['--series-days', '7',
                                      '--series-absent'])
    t56c = toks42(l56c[0]) if l56c else {}
    ok('AC-RUN56', rc56c == 0
       and t56c.get('line_bytes') == str(len(l56c[0].encode('utf-8')))
       and t56a.get('line_bytes') == str(real56a)
       and t56c.get('line_bytes') != t56a.get('line_bytes'),
       'the same file at window 7 and window 60 reports each own width and '
       'they differ - the number is measured per run, not a constant copied '
       'from one face')

    # arm 4: an empty history still prices its own bare line
    r56d = world()
    roots.append(r56d)
    os.makedirs(os.path.join(r56d, 'qa'), exist_ok=True)
    rc56d, l56d, _raw56d = sd56(r56d, ['--series-days', '7',
                                       '--series-absent'])
    t56d = toks42(l56d[0]) if l56d else {}
    ok('AC-RUN56', rc56d == 0 and len(l56d) == 1
       and t56d.get('line_bytes') == str(len(l56d[0].encode('utf-8')))
       and int(t56d.get('line_bytes') or -1) + 1
       == int(t56d.get('output_bytes') or -2)
       and t56d.get('absent_all_bytes') == 'none',
       'no history names no gaps (absent_all_bytes=none) but the line still '
       'says how wide it is, without raising')

    # arm 5: the unwindowed default face gains no token and does not drift
    rc56e, l56e, _raw56e = sd56(r56, [])
    rc56f, l56f, _raw56f = sd56(r56, [])
    ok('AC-RUN56', rc56e == 0 and l56e and l56f
       and ' line_bytes=' not in l56e[0]
       and ' output_bytes=' not in l56e[0]
       and l56e[0] == l56f[0],
       'without --series-absent the line carries neither new token and two '
       'runs print the identical bytes')

    # arm 6: pure display, no verdict, and the pinned absent= counts survive
    before56 = tree_bytes(r56)
    rc56g, l56g, _raw56g = sd56(r56, ['--series-days', '60',
                                      '--series-absent'])
    after56 = tree_bytes(r56)
    text56 = '\n'.join(l56g)
    ok('AC-RUN56', rc56g == 0 and before56 == after56
       and 'PASS' not in text56 and 'FLAG' not in text56
       and 'verdict' not in text56
       and l56g[0].count('absent=') == 2
       and l56g[0].count('absent_named=') == 1,
       'the opt-in line writes no byte, prints no verdict, and both pinned '
       'counts still hold with the two new numbers on it')

    # ===== AC-RUN57 (R3040): the pairs segment prices itself =====
    # AC-RUN57 was pinned in src/os/backlog.md BEFORE series_segment_bytes
    # existed (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3040.log, six private worlds, no socket, no clock): the width
    # is decided by three things at once - the stored day string (an ISO row
    # prints `2026-11-10T09:00:00:1`, so "a day is always ten characters" is
    # false), each on_day's digit count (same shown=2 measured 25B against
    # 31B) and shown-1 commas; five candidate token names had zero hits across
    # tools/ and src/; and NONE of the line's thirteen integer keys equalled
    # the segment on any world (equal_keys=NONE), the empty history included.
    # The token lands on the --series-days face only, because AC-RUN42 arm 2
    # pins the unwindowed tail by equality and that line has not moved by a
    # byte since R3025.
    def sd57(root, extra):
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = RUN.main(['--failure-days'] + list(extra) + ['--root', root])
        text = buf.getvalue()
        return rc, [n for n in text.splitlines() if n.strip()], text

    def toks57(line):
        return dict(part.split('=', 1) for part in line.split()[1:])

    def real_seg57(line):
        for part in line.split():
            if part.startswith('series='):
                return len(part.encode('utf-8'))
        return -1

    r57 = world()
    roots.append(r57)
    p57 = hist37(r57)
    put_days(p57, [plain_day('2026-11-10', 1), plain_day('2026-11-11', 2),
                   plain_day('2026-11-12', 3), plain_day('2026-11-13', 4),
                   plain_day('2026-11-14', 5)])

    # arm 1: a ten-character day world - the number is the real segment width
    rc57a, l57a, _raw57a = sd57(r57, ['--series-days', '7', '--days', '5'])
    t57a = toks57(l57a[0]) if l57a else {}
    ok('AC-RUN57', rc57a == 0 and l57a
       and t57a.get('series_bytes') == str(real_seg57(l57a[0]))
       and t57a.get('series_bytes') == str(
           len(('series=%s' % t57a.get('series')).encode('utf-8'))),
       'on a ten-character day world series_bytes reads the real UTF-8 width '
       'of the series= segment on the row it sits on, its key included')

    # arm 2: same shown, different on_day digits -> two prices, both exact
    def two57(rows):
        root = world()
        roots.append(root)
        put_days(hist37(root), rows)
        return sd57(root, ['--series-days', '7', '--days', '2'])

    rc57b, l57b, _ = two57([plain_day('2026-11-10', 3),
                            plain_day('2026-11-11', 4)])
    rc57c, l57c, _ = two57([plain_day('2026-11-10', 3000),
                            plain_day('2026-11-11', 4000)])
    t57b = toks57(l57b[0]) if l57b else {}
    t57c = toks57(l57c[0]) if l57c else {}
    ok('AC-RUN57', rc57b == 0 and rc57c == 0 and l57b and l57c
       and t57b.get('series_shown') == t57c.get('series_shown') == '2'
       and t57b.get('series_bytes') == str(real_seg57(l57b[0]))
       and t57c.get('series_bytes') == str(real_seg57(l57c[0]))
       and t57b.get('series_bytes') != t57c.get('series_bytes'),
       'the same series_shown=2 prices differently when the counts grow '
       'digits, so the width is not a constant a reader can assume from '
       'the count')

    # arm 3: the day string is not assumed to be ten characters
    r57d = world()
    roots.append(r57d)
    put_days(hist37(r57d),
             [{'day': '2026-11-10T09:00:00', 'on_day': 1},
              {'day': '2026-11-11T10:00:00', 'on_day': 2}])
    rc57d, l57d, _ = sd57(r57d, ['--series-days', '7', '--days', '2'])
    t57d = toks57(l57d[0]) if l57d else {}
    ok('AC-RUN57', rc57d == 0 and l57d
       and 'T09:00:00' in (t57d.get('series') or '')
       and t57d.get('series_bytes') == str(real_seg57(l57d[0])),
       'an ISO-stamped history prices its own longer day strings instead of '
       'a ten-character assumption')

    # arm 4: no pairs still prices the segment it prints - series=none is 11
    r57e = world()
    roots.append(r57e)
    os.makedirs(os.path.join(r57e, 'qa'), exist_ok=True)
    rc57f, l57f, _ = sd57(r57e, ['--series-days', '7'])
    t57f = toks57(l57f[0]) if l57f else {}
    ok('AC-RUN57', rc57f == 0 and l57f
       and t57f.get('series') == 'none'
       and t57f.get('series_bytes') == '11'
       and t57f.get('series_bytes') == str(real_seg57(l57f[0])),
       'an empty history prints series=none and prices it at eleven bytes '
       'rather than inventing a zero, without raising')

    # arm 5: the unwindowed default face gains no token and does not drift
    rc57g, l57g, _ = sd57(r57, [])
    rc57h, l57h, _ = sd57(r57, [])
    ok('AC-RUN57', rc57g == 0 and l57g and l57h
       and ' series_bytes=' not in l57g[0]
       and l57g[0] == l57h[0],
       'without --series-days the line carries no new token and two runs '
       'print identical bytes - the default face did not move')

    # arm 6: with --series-absent the value rides the R3039 fixed point
    rc57i, l57i, raw57i = sd57(r57, ['--series-days', '7', '--series-absent'])
    t57i = toks57(l57i[0]) if l57i else {}
    real57i = len(l57i[0].encode('utf-8')) if l57i else -1
    ok('AC-RUN57', rc57i == 0 and l57i
       and t57i.get('line_bytes') == str(real57i)
       and int(t57i.get('line_bytes') or -1) + 1
       == int(t57i.get('output_bytes') or -2)
       and t57i.get('series_bytes') == str(real_seg57(l57i[0]))
       and int(t57i.get('series_bytes') or -1)
       < int(t57i.get('line_bytes') or -1)
       and t57i.get('absent_all_bytes') == t57i.get('line_bytes'),
       'with --series-absent the new number sits inside the one fixed point: '
       'the line still prices itself exactly, the segment is strictly smaller '
       'than the line, and a fully named projection still equals it')

    # arm 7: pure display - no byte written, no verdict, pinned counts hold
    before57 = tree_bytes(r57)
    rc57j, l57j, _ = sd57(r57, ['--series-days', '7', '--series-absent'])
    after57 = tree_bytes(r57)
    text57 = '\n'.join(l57j)
    ok('AC-RUN57', rc57j == 0 and before57 == after57
       and 'PASS' not in text57 and 'FLAG' not in text57
       and 'verdict' not in text57
       and l57j[0].count('series_window=') == 1
       and l57j[0].count('absent=') == 2
       and l57j[0].count('absent_named=') == 1,
       'the priced line writes no byte, prints no verdict, and both pinned '
       'absent counts and the single series_window token still hold')

    # ===== AC-RUN58 (R3041): the pairs segment names WHICH source ate it =====
    # AC-RUN58 was pinned in src/os/backlog.md BEFORE series_source_bytes
    # existed (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3041.log, four private worlds, no socket, no clock): one price
    # cannot say why the segment is wide - swapping only the days for ISO
    # stamps moved series_bytes 32 -> 50 (+18 = two days x nine extra chars)
    # while swapping only the counts for four digits moved it 32 -> 38 (+6 =
    # two counts x three extra digits). Neither side had a printed key
    # (equal_keys_days=NONE on every non-empty world; on matched series_shown
    # only by the two-pairs coincidence), and every candidate token name had
    # zero hits across tools/ and src/. The frame remainder (7 key bytes, one
    # colon per pair, shown-1 commas) is a pure function of series_shown, so it
    # is NOT printed - the R3000 noise law - and the identity is pinned here.
    def split58(series_text):
        if not series_text or series_text == 'none':
            return 0, 0, 0
        days = ons = 0
        parts = series_text.split(',')
        for part in parts:
            _d, n = part.rsplit(':', 1)
            days += len(_d.encode('utf-8'))
            ons += len(n)
        return days, ons, len(parts)

    def two58(rows):
        root = world()
        roots.append(root)
        put_days(hist37(root), rows)
        rc, lines, _raw = sd57(root, ['--series-days', '7', '--days', '2'])
        return rc, lines, toks57(lines[0]) if lines else {}

    def derived58(t):
        return split58(t.get('series'))

    r58 = world()
    roots.append(r58)
    put_days(hist37(r58), [plain_day('2026-11-10', 3),
                           plain_day('2026-11-11', 4)])

    # arm 1: both sides price themselves, and the identity holds on the row
    rc58a, l58a, _ = sd57(r58, ['--series-days', '7', '--days', '5'])
    t58a = toks57(l58a[0]) if l58a else {}
    d58a, o58a, n58a = derived58(t58a)
    ok('AC-RUN58', rc58a == 0 and l58a
       and t58a.get('series_day_bytes') == str(d58a)
       and t58a.get('series_on_bytes') == str(o58a)
       and t58a.get('series_shown') == str(n58a)
       and int(t58a.get('series_bytes') or -1)
       == d58a + o58a + 2 * n58a + 6,
       'on a ten-character day world both source totals equal what the row '
       'itself says, and series_bytes equals them plus the frame the reader '
       'can see (key, colons, commas) with no unwritten byte')

    # arm 2: only the days grow - the delta lands entirely on the day side
    iso58 = two58([{'bad': 0, 'day': '2026-11-10T09:00:00', 'newest_at': None,
                    'newest_error': None, 'on_day': 3, 'recent': 0,
                    'total': 0, 'urls': 0},
                   {'bad': 0, 'day': '2026-11-11T09:00:00', 'newest_at': None,
                    'newest_error': None, 'on_day': 4, 'recent': 0,
                    'total': 0, 'urls': 0}])
    base58 = two58([plain_day('2026-11-10', 3), plain_day('2026-11-11', 4)])
    ti58 = iso58[2]
    tb58 = base58[2]
    ok('AC-RUN58', iso58[0] == 0 and base58[0] == 0 and iso58[1]
       and tb58
       and ti58.get('series_on_bytes') == tb58.get('series_on_bytes')
       and int(ti58.get('series_day_bytes') or -1)
       == int(tb58.get('series_day_bytes') or -2) + 2 * 9
       and int(ti58.get('series_bytes') or -1)
       - int(tb58.get('series_bytes') or -2) == 2 * 9,
       'an ISO-stamped history leaves the count side untouched, adds exactly '
       'two days times nine characters on the day side, and the whole segment '
       'delta is that same eighteen bytes')

    # arm 3: only the counts grow - the delta lands entirely on the count side
    wide58 = two58([plain_day('2026-11-10', 3000),
                    plain_day('2026-11-11', 4000)])
    tw58 = wide58[2]
    ok('AC-RUN58', wide58[0] == 0 and wide58[1] and tw58
       and tw58.get('series_day_bytes') == tb58.get('series_day_bytes')
       and int(tw58.get('series_on_bytes') or -1)
       == int(tb58.get('series_on_bytes') or -2) + 2 * 3
       and int(tw58.get('series_bytes') or -1)
       - int(tb58.get('series_bytes') or -2) == 2 * 3,
       'four-digit counts leave the day side untouched, add exactly two counts '
       'times three digits on the count side, and account for the whole six-'
       'byte segment delta - the two causes no longer read the same')

    # arm 4: an empty history answers zero on both sides, not a missing key
    r58e = world()
    roots.append(r58e)
    os.makedirs(os.path.join(r58e, 'qa'), exist_ok=True)
    rc58d, l58d, _ = sd57(r58e, ['--series-days', '7'])
    t58d = toks57(l58d[0]) if l58d else {}
    ok('AC-RUN58', rc58d == 0 and l58d
       and t58d.get('series') == 'none'
       and t58d.get('series_day_bytes') == '0'
       and t58d.get('series_on_bytes') == '0'
       and t58d.get('series_bytes') == '11',
       'an empty history prints both source totals as zero - an honest '
       'measurement of nothing, not an absent key - and the segment stays '
       'eleven for series=none without raising')

    # arm 5: the unwindowed default face gains neither token and does not drift
    rc58e, l58e, _ = sd57(r58, [])
    rc58f, l58f, _ = sd57(r58, [])
    ok('AC-RUN58', rc58e == 0 and l58e and l58f
       and ' series_day_bytes=' not in l58e[0]
       and ' series_on_bytes=' not in l58e[0]
       and l58e[0] == l58f[0],
       'without --series-days neither source token appears and two runs print '
       'identical bytes - the default face did not move by a byte')

    # arm 6: with --series-absent the new numbers ride the same fixed point
    rc58g, l58g, _raw58g = sd57(r58, ['--series-days', '7',
                                      '--series-absent'])
    t58g = toks57(l58g[0]) if l58g else {}
    real58g = len(l58g[0].encode('utf-8')) if l58g else -1
    d58g, o58g, n58g = derived58(t58g)
    ok('AC-RUN58', rc58g == 0 and l58g
       and t58g.get('line_bytes') == str(real58g)
       and int(t58g.get('line_bytes') or -1) + 1
       == int(t58g.get('output_bytes') or -2)
       and t58g.get('series_bytes') == str(real_seg57(l58g[0]))
       and t58g.get('series_day_bytes') == str(d58g)
       and t58g.get('series_on_bytes') == str(o58g)
       and int(t58g.get('series_bytes') or -1)
       == d58g + o58g + 2 * n58g + 6
       and t58g.get('absent_all_bytes') == t58g.get('line_bytes'),
       'with --series-absent both source totals sit inside the one fixed '
       'point: the line still prices itself to the byte, the identity still '
       'holds on the longer row, and a fully named projection still equals it')

    # arm 7: pure display - no byte written, no verdict, pinned counts hold
    before58 = tree_bytes(r58)
    rc58h, l58h, _ = sd57(r58, ['--series-days', '7', '--series-absent'])
    after58 = tree_bytes(r58)
    text58 = '\n'.join(l58h)
    ok('AC-RUN58', rc58h == 0 and before58 == after58
       and 'PASS' not in text58 and 'FLAG' not in text58
       and 'verdict' not in text58
       and l58h[0].count('series_window=') == 1
       and l58h[0].count('absent=') == 2
       and l58h[0].count('absent_named=') == 1,
       'the two new numbers write no byte, print no verdict, and every pinned '
       'count on the opt-in line still holds')

    # ===== AC-RUN59 (R3042): the pairs a --days cap drops now have a price =====
    # AC-RUN59 was pinned in src/os/backlog.md BEFORE series_full_pairs existed
    # (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3042.log, private worlds, no socket, no clock): on a five-day
    # world capped at two, the printed pairs are a suffix of the in-window set,
    # rebuilding the full segment from the FILE reproduced the printed price to
    # the byte (32 == 32) so the projection is not self-circular, and with n
    # pairs the segment is day bytes + on digits + 2*n + 6 - so the lift cost
    # is (day_dropped + on_dropped + 2*(window_rows - shown)). The dropped
    # COUNT is derivable from two printed tokens, so no count token is added.
    def seg59(pairs):
        text = ','.join('%s:%s' % (d, n) for d, n in pairs)
        return len(('series=' + (text or 'none')).encode('utf-8'))

    def full59(root, width=7):
        rows, _bad59 = RUN.read_failure_days(hist37(root))
        head59, usable59, thr59 = RUN._window_start(
            str(rows[-1]['day']) if rows else '', width)
        if not usable59:
            return []
        return [(r['day'], r['on_day']) for r in rows
                if thr59 <= str(r['day'])[:10] <= head59]

    def sides59(pairs):
        return (sum(len(str(d).encode('utf-8')) for d, _n in pairs),
                sum(len(str(n)) for _d, n in pairs))

    r59 = world()
    roots.append(r59)
    p59 = hist37(r59)
    five59 = [plain_day('2026-11-10', 1), plain_day('2026-11-11', 2),
              plain_day('2026-11-12', 3), plain_day('2026-11-13', 4),
              plain_day('2026-11-14', 5)]
    put_days(p59, five59)

    # arm 1: the capped world prices the whole day window from the file
    rc59a, l59a, _ = sd57(r59, ['--series-days', '7', '--days', '2'])
    t59a = toks57(l59a[0]) if l59a else {}
    f59a = full59(r59)
    ok('AC-RUN59', rc59a == 0 and l59a and len(f59a) == 5
       and t59a.get('window_rows') == '5' and t59a.get('series_shown') == '2'
       and t59a.get('series_all_bytes') == str(seg59(f59a))
       and int(t59a.get('series_all_bytes') or -1)
       > int(t59a.get('series_bytes') or -1),
       'on a five-day window capped at two, series_all_bytes equals the full '
       'segment rebuilt from the file itself and is strictly larger than the '
       'capped segment - the dropped pairs are priced, not counted')

    # arm 2: the increment is exactly the dropped day bytes, their digit bytes
    # and two separators per dropped pair (sides from the file projection, the
    # counts and prices read off the row)
    _fday59, _fon59 = sides59(f59a)
    _pday59, _pon59 = sides59(f59a[-2:])
    k59 = 5 - int(t59a.get('series_shown') or 0)
    ok('AC-RUN59', int(t59a.get('window_rows') or 0) - k59
       == int(t59a.get('series_shown') or 0)
       and int(t59a.get('series_all_bytes') or -1)
       - int(t59a.get('series_bytes') or -2)
       == (_fday59 - _pday59) + (_fon59 - _pon59) + 2 * k59,
       'the lift cost decomposes exactly into the dropped day strings, the '
       'dropped digit counts and two separators per dropped pair, and the '
       'dropped count is window_rows minus series_shown rather than a token')

    # arm 3: the same file with no cap - the cap costs nothing, measurably
    rc59b, l59b, _ = sd57(r59, ['--series-days', '7'])
    t59b = toks57(l59b[0]) if l59b else {}
    ok('AC-RUN59', rc59b == 0 and l59b
       and t59b.get('window_rows') == t59b.get('series_shown')
       and t59b.get('series_all_bytes') == t59b.get('series_bytes')
       and t59b.get('series_all_bytes') == str(seg59(full59(r59))),
       'without the cap window_rows equals series_shown and series_all_bytes '
       'equals series_bytes - the equality is measured, not a restatement')

    # arm 4: an ISO-stamped world - the lift cost follows the stored day strings
    r59i = world()
    roots.append(r59i)
    put_days(hist37(r59i), [
        {'bad': 0, 'day': '2026-11-10T09:00:00', 'newest_at': None,
         'newest_error': None, 'on_day': 3000, 'recent': 0, 'total': 0,
         'urls': 0},
        {'bad': 0, 'day': '2026-11-11T09:00:00', 'newest_at': None,
         'newest_error': None, 'on_day': 4, 'recent': 0, 'total': 0,
         'urls': 0},
        {'bad': 0, 'day': '2026-11-12T09:00:00', 'newest_at': None,
         'newest_error': None, 'on_day': 5, 'recent': 0, 'total': 0,
         'urls': 0},
        {'bad': 0, 'day': '2026-11-13T09:00:00', 'newest_at': None,
         'newest_error': None, 'on_day': 6, 'recent': 0, 'total': 0,
         'urls': 0}])
    rc59c, l59c, _ = sd57(r59i, ['--series-days', '7', '--days', '2'])
    t59c = toks57(l59c[0]) if l59c else {}
    f59c = full59(r59i)
    fd59, fo59 = sides59(f59c)
    pd59, po59 = sides59(f59c[-2:])
    ok('AC-RUN59', rc59c == 0 and l59c and len(f59c) == 4
       and t59c.get('series_all_bytes') == str(seg59(f59c))
       and int(t59c.get('series_all_bytes') or -1)
       - int(t59c.get('series_bytes') or -2)
       == (fd59 - pd59) + (fo59 - po59) + 2 * (4 - 2)
       and (fd59 - pd59) > (fo59 - po59),
       'an ISO-stamped history prices the longer stored days, and the lift '
       'cost lands mostly on the day side - a ten-character assumption would '
       'read short here')

    # arm 5: an empty history prices the segment it actually prints
    r59e = world()
    roots.append(r59e)
    os.makedirs(os.path.join(r59e, 'qa'), exist_ok=True)
    rc59d, l59d, _ = sd57(r59e, ['--series-days', '7'])
    t59d = toks57(l59d[0]) if l59d else {}
    ok('AC-RUN59', rc59d == 0 and l59d
       and t59d.get('series') == 'none'
       and t59d.get('series_all_bytes') == '11'
       and t59d.get('series_all_bytes') == t59d.get('series_bytes'),
       'an empty history answers eleven on both prices, matching the '
       'series=none segment it actually prints, without raising')

    # arm 6: the unwindowed default face gains no token and does not drift
    rc59e, l59e, _ = sd57(r59, [])
    rc59f, l59f, _ = sd57(r59, [])
    ok('AC-RUN59', rc59e == 0 and l59e and l59f
       and ' series_all_bytes=' not in l59e[0]
       and l59e[0] == l59f[0],
       'without --series-days the token is absent and two runs print identical '
       'bytes - the default face did not move')

    # arm 7: pure display - no byte written, no verdict, pinned counts hold
    before59 = tree_bytes(r59)
    rc59g, l59g, _ = sd57(r59, ['--series-days', '7', '--days', '2',
                                '--series-absent'])
    after59 = tree_bytes(r59)
    text59 = '\n'.join(l59g)
    ok('AC-RUN59', rc59g == 0 and before59 == after59
       and 'PASS' not in text59 and 'FLAG' not in text59
       and 'verdict' not in text59
       and l59g[0].count('series_window=') == 1
       and l59g[0].count('absent=') == 2
       and l59g[0].count('absent_named=') == 1
       and l59g[0].count('series_all_bytes=') == 1
       and 'series_dropped_bytes=' not in text59
       and 'dropped_pair_bytes=' not in text59,
       'the priced line writes no byte, prints no verdict, every pinned count '
       'survives, the new token appears once and no increment twin was added')

    # ===== AC-RUN60 (R3043): the cap says WHICH DAY it cut back to ==========
    # Measured first (qa/probe-R3043.log, private worlds, no socket, no clock):
    # on a five-day world capped at two the printed pairs are a suffix of the
    # in-window set and the dropped end is the older one (dropped_from 11-10 <
    # first kept 11-13); on rows 11-10,11-10,11-11,11-11 capped at three the
    # dropped row shares its day with the first kept one, so "everything older
    # was dropped" is FALSE and the criterion may only pin the oldest dropped
    # DAY. The lift increment and the dropped count stay derivable, not tokens.
    def dropped60(root, width=7, cap=2):
        rows, _bad60 = RUN.read_failure_days(hist37(root))
        full60 = RUN.series_full_pairs(rows, width)
        win60 = RUN.series_days_window(rows, cap, width)
        return full60, win60['rows']

    r60 = world()
    roots.append(r60)
    p60 = hist37(r60)
    put_days(p60, [plain_day('2026-11-10', 1), plain_day('2026-11-11', 2),
                   plain_day('2026-11-12', 3), plain_day('2026-11-13', 4),
                   plain_day('2026-11-14', 5)])

    # arm 1: the day the cap cut back to, projected from the file itself
    rc60a, l60a, _ = sd57(r60, ['--series-days', '7', '--days', '2'])
    t60a = toks57(l60a[0]) if l60a else {}
    full60a, kept60a = dropped60(r60)
    oldest_dropped60 = full60a[:len(full60a) - len(kept60a)][0][0]
    ok('AC-RUN60', rc60a == 0 and l60a and len(full60a) == 5
       and t60a.get('series_dropped_from') == oldest_dropped60
       and oldest_dropped60 < str(kept60a[0][0]),
       'on a five-day window capped at two, series_dropped_from names the '
       'oldest dropped day rebuilt from the file, and it is strictly older '
       'than the first printed pair')

    # arm 2: a day that straddles the cap - the token names the DAY, and that
    # day also appears in the kept segment, so no "older" claim is printed
    r60b = world()
    roots.append(r60b)
    put_days(hist37(r60b), [
        {'bad': 0, 'day': '2026-11-10', 'newest_at': None, 'newest_error': None,
         'on_day': 1, 'recent': 0, 'total': 0, 'urls': 0},
        {'bad': 0, 'day': '2026-11-10', 'newest_at': None, 'newest_error': None,
         'on_day': 2, 'recent': 0, 'total': 0, 'urls': 0},
        {'bad': 0, 'day': '2026-11-11', 'newest_at': None, 'newest_error': None,
         'on_day': 3, 'recent': 0, 'total': 0, 'urls': 0},
        {'bad': 0, 'day': '2026-11-11', 'newest_at': None, 'newest_error': None,
         'on_day': 4, 'recent': 0, 'total': 0, 'urls': 0}])
    rc60b, l60b, _ = sd57(r60b, ['--series-days', '7', '--days', '3'])
    t60b = toks57(l60b[0]) if l60b else {}
    seg60b = str(t60b.get('series') or '')
    ok('AC-RUN60', rc60b == 0 and l60b
       and t60b.get('series_dropped_from') == '2026-11-10'
       and t60b.get('series_shown') == '3'
       and seg60b.split(':', 1)[0] == t60b.get('series_dropped_from'),
       'a day straddling the cap still names the oldest dropped day, and that '
       'same day is the first kept pair - the row says which day, never that '
       'every older row went')

    # arm 3: no cap - nothing was dropped and the marker says so
    rc60c, l60c, _ = sd57(r60, ['--series-days', '7'])
    rc60d, l60d, _ = sd57(r60, ['--series-days', '7'])
    t60c = toks57(l60c[0]) if l60c else {}
    ok('AC-RUN60', rc60c == 0 and rc60d == 0 and l60c and l60d
       and t60c.get('window_rows') == t60c.get('series_shown')
       and t60c.get('series_dropped_from') == 'none'
       and l60c[0] == l60d[0],
       'without the cap window_rows equals series_shown, the marker answers '
       'none, and two runs print identical bytes')

    # arm 4: an empty history answers none without raising
    r60e = world()
    roots.append(r60e)
    os.makedirs(os.path.join(r60e, 'qa'), exist_ok=True)
    rc60e, l60e, _ = sd57(r60e, ['--series-days', '7'])
    t60e = toks57(l60e[0]) if l60e else {}
    ok('AC-RUN60', rc60e == 0 and l60e
       and t60e.get('series') == 'none'
       and t60e.get('series_dropped_from') == 'none',
       'an empty history answers series=none with series_dropped_from=none, '
       'rc=0 and no exception')

    # arm 5: the unwindowed default face gains nothing and does not drift
    rc60f, l60f, _ = sd57(r60, [])
    rc60g, l60g, _ = sd57(r60, [])
    ok('AC-RUN60', rc60f == 0 and l60f and l60g
       and ' series_dropped_from=' not in l60f[0]
       and l60f[0] == l60g[0],
       'without --series-days the marker is absent and two runs print '
       'identical bytes - the default face did not move')

    # arm 6: with --series-absent the joint fixed point still holds and the
    # refused increment twin is still absent
    before60 = tree_bytes(r60)
    rc60h, l60h, _ = sd57(r60, ['--series-days', '7', '--days', '2',
                                '--series-absent'])
    after60 = tree_bytes(r60)
    t60h = toks57(l60h[0]) if l60h else {}
    text60 = '\n'.join(l60h)
    real60 = len(l60h[0].encode('utf-8')) if l60h else -1
    ok('AC-RUN60', rc60h == 0 and before60 == after60
       and t60h.get('line_bytes') == str(real60)
       and t60h.get('output_bytes') == str(real60 + 1)
       and 'series_dropped_bytes=' not in text60
       and l60h[0].count('series_window=') == 1
       and l60h[0].count('absent=') == 2
       and l60h[0].count('absent_named=') == 1
       and l60h[0].count('series_dropped_from=') == 1,
       'the silent-day face still prices its own line to the byte, the '
       'increment twin stays absent, and the new marker appears exactly once')

    # ===== AC-RUN61 (R3044): the cap cuts in DAY order and names the day it
    # cut INSIDE ==============================================================
    # AC-RUN61 was pinned in src/os/backlog.md BEFORE either window function
    # sorted and BEFORE series_dropped_shared existed (in-window
    # pre-registration, disclosed here). Measured first (qa/probe-R3044.log and
    # the S1/S2 supplement): on a day-ordered history that drops an older day
    # AND a row of the boundary day, the same-day count is 1 while the row's own
    # window_rows - series_shown subtraction answers 2 - so the count is NOT a
    # restatement (the PIN's first ruling was amended in the same window after
    # that measurement, and the amendment is kept verbatim on the board).
    def put_rows(path, days):
        put_days(path, [
            {'bad': 0, 'day': d, 'newest_at': None, 'newest_error': None,
             'on_day': n, 'recent': 0, 'total': 0, 'urls': 0}
            for d, n in days])

    def shared_from_file(root, cap, width=7):
        rows61, _bad61 = RUN.read_failure_days(hist37(root))
        full61 = RUN.series_full_pairs(rows61, width)
        kept61 = RUN.series_days_window(rows61, cap, width)['rows']
        return full61, kept61, RUN.series_dropped_shared(full61, kept61)

    # arm 1: a day-ordered history prints the same segment, and a clean cut
    # between days answers 0
    r61 = world()
    roots.append(r61)
    put_rows(hist37(r61), [('2026-11-10', 1), ('2026-11-11', 2),
                           ('2026-11-12', 3), ('2026-11-13', 4),
                           ('2026-11-14', 5)])
    rc61a, l61a, _ = sd57(r61, ['--series-days', '7', '--days', '2'])
    t61a = toks57(l61a[0]) if l61a else {}
    _f61a, _k61a, s61a = shared_from_file(r61, 2)
    ok('AC-RUN61', rc61a == 0 and l61a
       and t61a.get('series') == '2026-11-13:4,2026-11-14:5'
       and t61a.get('window_rows') == '5' and t61a.get('series_shown') == '2'
       and t61a.get('series_dropped_from') == '2026-11-10'
       and t61a.get('series_dropped_shared') == '0' and s61a == 0,
       'a day-ordered history keeps the segment it printed before the sort, and '
       'a cap that cuts between days answers series_dropped_shared=0')

    # arm 2: a hand-edited history whose days are out of order - the cap now
    # drops the OLDEST day rather than the oldest file row
    r61b = world()
    roots.append(r61b)
    put_rows(hist37(r61b), [('2026-11-11', 1), ('2026-11-10', 2),
                            ('2026-11-12', 3)])
    before61 = tree_bytes(r61b)
    rc61b, l61b, _ = sd57(r61b, ['--series-days', '7', '--days', '2'])
    after61 = tree_bytes(r61b)
    t61b = toks57(l61b[0]) if l61b else {}
    seg61b = [p.split(':', 1)[0]
              for p in str(t61b.get('series') or '').split(',')]
    ok('AC-RUN61', rc61b == 0 and l61b and before61 == after61
       and seg61b == sorted(seg61b)
       and t61b.get('series') == '2026-11-11:1,2026-11-12:3'
       and t61b.get('series_dropped_from') == '2026-11-10'
       and t61b.get('series_dropped_from') < seg61b[0]
       and t61b.get('series_dropped_shared') == '0',
       'on a history whose days are out of order the printed pairs are in day '
       'order, dropped_from is strictly older than the first printed day, and '
       'nothing is written - the cap no longer drops a day newer than one it '
       'prints')

    # arm 3: the straddle the PIN first got wrong - one row of the boundary day
    # is cut while an older day is cut too, so the count is NOT the subtraction
    r61c = world()
    roots.append(r61c)
    put_rows(hist37(r61c), [('2026-11-10', 1), ('2026-11-11', 2),
                            ('2026-11-11', 3), ('2026-11-12', 4)])
    rc61c, l61c, _ = sd57(r61c, ['--series-days', '7', '--days', '2'])
    t61c = toks57(l61c[0]) if l61c else {}
    _f61c, _k61c, s61c = shared_from_file(r61c, 2)
    ok('AC-RUN61', rc61c == 0 and l61c
       and t61c.get('series') == '2026-11-11:3,2026-11-12:4'
       and t61c.get('series_dropped_shared') == '1' and s61c == 1
       and int(t61c.get('window_rows') or 0)
       - int(t61c.get('series_shown') or 0) == 2,
       'a day that straddles the cap with an older day also dropped answers '
       'series_dropped_shared=1 while window_rows - series_shown is 2 - the '
       'count is not a restatement of the subtraction already on the row')

    # arm 4: every dropped row on an older day - the coincidence that hid the
    # difference above answers 0, not a count
    r61d = world()
    roots.append(r61d)
    put_rows(hist37(r61d), [('2026-11-10', 1), ('2026-11-10', 2),
                            ('2026-11-11', 3), ('2026-11-11', 4),
                            ('2026-11-11', 5)])
    rc61d, l61d, _ = sd57(r61d, ['--series-days', '7', '--days', '3'])
    t61d = toks57(l61d[0]) if l61d else {}
    _f61d, _k61d, s61d = shared_from_file(r61d, 3)
    ok('AC-RUN61', rc61d == 0 and l61d
       and t61d.get('series') == '2026-11-11:3,2026-11-11:4,2026-11-11:5'
       and t61d.get('series_dropped_shared') == '0' and s61d == 0
       and int(t61d.get('window_rows') or 0)
       - int(t61d.get('series_shown') or 0) == 2,
       'a window whose dropped rows all sit on an older day answers 0 even '
       'though two rows were dropped - the subtraction answered 2, which is '
       'exactly the coincidence the first PIN ruling rested on')

    # arm 5: no cap - nothing was dropped, the count is 0, two runs agree
    rc61e, l61e, _ = sd57(r61, ['--series-days', '7'])
    rc61f, l61f, _ = sd57(r61, ['--series-days', '7'])
    t61e = toks57(l61e[0]) if l61e else {}
    ok('AC-RUN61', rc61e == 0 and rc61f == 0 and l61e and l61f
       and t61e.get('window_rows') == t61e.get('series_shown')
       and t61e.get('series_dropped_from') == 'none'
       and t61e.get('series_dropped_shared') == '0'
       and l61e[0] == l61f[0],
       'without the cap window_rows equals series_shown, dropped_from answers '
       'none, the count answers 0, and two runs print identical bytes')

    # arm 6: an empty history answers zeros without raising
    r61g = world()
    roots.append(r61g)
    os.makedirs(os.path.join(r61g, 'qa'), exist_ok=True)
    rc61g, l61g, _ = sd57(r61g, ['--series-days', '7'])
    t61g = toks57(l61g[0]) if l61g else {}
    ok('AC-RUN61', rc61g == 0 and l61g
       and t61g.get('series') == 'none'
       and t61g.get('series_dropped_from') == 'none'
       and t61g.get('series_dropped_shared') == '0',
       'an empty history answers series=none, dropped_from=none and a zero '
       'count, rc=0 and no exception')

    # arm 7: with --series-absent the joint fixed point still holds and the new
    # count appears exactly once
    before61h = tree_bytes(r61c)
    rc61h, l61h, _ = sd57(r61c, ['--series-days', '7', '--days', '2',
                                 '--series-absent'])
    after61h = tree_bytes(r61c)
    t61h = toks57(l61h[0]) if l61h else {}
    real61 = len(l61h[0].encode('utf-8')) if l61h else -1
    ok('AC-RUN61', rc61h == 0 and before61h == after61h
       and t61h.get('line_bytes') == str(real61)
       and t61h.get('output_bytes') == str(real61 + 1)
       and l61h[0].count('series_window=') == 1
       and l61h[0].count('absent=') == 2
       and l61h[0].count('absent_named=') == 1
       and l61h[0].count('series_dropped_shared=') == 1,
       'the silent-day face still prices its own line to the byte and the new '
       'count appears exactly once on it')

    # ===== AC-RUN62 (R3045): the day window opens from the newest day the
    # record knows, and the line says when the file is not in day order =====
    # AC-RUN62 was pinned in src/os/backlog.md BEFORE _day_face_head existed
    # (in-window pre-registration, disclosed). Measured before the pin
    # (qa/probe-R3045.log + qa/probe-R3045b.log): the day faces described their
    # head as "the file's OWN newest usable row" and read rows[-1], which is
    # that only for a writer-sorted file - on days 11-10,11-14,11-12,11-13,11-11
    # the window anchored on the last row (11-11) and three newer days were
    # filtered out as "outside" while series_outside=0 looked clean (576 of
    # 1800 permuted cap/width runs never reached the newest day). The board's
    # premise - a segment printing AFTER last= - measured FALSE (0 of 1800 runs,
    # the <= head_day bound forbids it), and making first=/last= day-based was
    # refused because the default face prints a file-order tail (measured: the
    # contradiction would move there). So: one head for six day faces, plus one
    # marker naming a file whose row order is not day order.

    # arm 1: a day-ordered history keeps every byte it printed before
    r62 = world()
    roots.append(r62)
    put_rows(hist37(r62), [('2026-11-10', 1), ('2026-11-11', 2),
                           ('2026-11-12', 3), ('2026-11-13', 4),
                           ('2026-11-14', 5)])
    before62 = tree_bytes(r62)
    rc62a, l62a, _ = sd57(r62, ['--series-days', '7', '--days', '2'])
    after62 = tree_bytes(r62)
    t62a = toks57(l62a[0]) if l62a else {}
    ok('AC-RUN62', rc62a == 0 and l62a and before62 == after62
       and t62a.get('series') == '2026-11-13:4,2026-11-14:5'
       and t62a.get('window_rows') == '5'
       and t62a.get('series_shown') == '2'
       and t62a.get('series_dropped_from') == '2026-11-10'
       and t62a.get('series_dropped_shared') == '0'
       and t62a.get('series_file_order') == 'day',
       'a writer-sorted history prints the same segment and counts it printed '
       'before this round, and the marker asserts day order on it')

    # arm 2: a hand-edited file whose LAST row is mid-history - the window now
    # opens from the newest day, so no newer day vanishes as "outside"
    r62b = world()
    roots.append(r62b)
    put_rows(hist37(r62b), [('2026-11-10', 1), ('2026-11-14', 5),
                            ('2026-11-12', 3), ('2026-11-13', 4),
                            ('2026-11-11', 2)])
    rc62b, l62b, _ = sd57(r62b, ['--series-days', '7', '--days', '2'])
    t62b = toks57(l62b[0]) if l62b else {}
    ok('AC-RUN62', rc62b == 0 and l62b
       and t62b.get('window_rows') == '5'
       and t62b.get('series') == '2026-11-13:4,2026-11-14:5'
       and t62b.get('series') == t62a.get('series')
       and t62b.get('series_file_order') == 'mixed',
       'on a file whose last row is 11-11 the seven-day window still holds all '
       'five rows and reaches 11-14, and the marker names the file order as '
       'mixed - the same days print as on the sorted file')

    # arm 3: the refused rewrite stays refused - first=/last= are the FILE ends
    # and the default face's pairs are still the file-order tail
    rc62c, l62c, _ = sd57(r62b, [])
    t62c = toks57(l62c[0]) if l62c else {}
    seg62b = [p.split(':', 1)[0]
              for p in str(t62b.get('series') or '').split(',')]
    ok('AC-RUN62', rc62c == 0 and l62c
       and t62c.get('first') == '2026-11-10'
       and t62c.get('last') == '2026-11-11'
       and t62b.get('first') == '2026-11-10'
       and t62b.get('last') == '2026-11-11'
       and seg62b[-1] > t62b.get('last')
       and t62c.get('series') == ('2026-11-10:1,2026-11-14:5,2026-11-12:3,'
                                  '2026-11-13:4,2026-11-11:2')
       and 'series_file_order' not in t62c,
       'first=/last= still name the file ends, the windowed segment may end '
       'later than last= (which the marker makes readable), and the default '
       'face still prints the file-order tail with no new token - the day-based '
       'rewrite was measured to relocate the contradiction here and refused')

    # arm 4: a same-day duplicate is still day order, and the marker appears
    # exactly once on the windowed line
    r62d = world()
    roots.append(r62d)
    put_rows(hist37(r62d), [('2026-11-10', 1), ('2026-11-11', 2),
                            ('2026-11-11', 3), ('2026-11-12', 4)])
    rc62d, l62d, _ = sd57(r62d, ['--series-days', '7', '--days', '2'])
    t62d = toks57(l62d[0]) if l62d else {}
    ok('AC-RUN62', rc62d == 0 and l62d
       and t62d.get('series_file_order') == 'day'
       and l62d[0].count('series_file_order=') == 1
       and RUN.series_file_order(RUN.read_failure_days(
           hist37(r62d))[0]) == 'day',
       'a duplicate day is non-decreasing rather than mixed, the marker is on '
       'the line exactly once, and the pure function agrees with the row')

    # arm 5: an empty history answers none - never "ordered"
    r62e = world()
    roots.append(r62e)
    os.makedirs(os.path.join(r62e, 'qa'), exist_ok=True)
    rc62e, l62e, _ = sd57(r62e, ['--series-days', '7'])
    t62e = toks57(l62e[0]) if l62e else {}
    ok('AC-RUN62', rc62e == 0 and l62e
       and t62e.get('series') == 'none'
       and t62e.get('window_rows') == '0'
       and t62e.get('series_file_order') == 'none'
       and RUN.series_file_order([]) == 'none'
       and RUN._day_face_head([]) == '',
       'an absent history answers series_file_order=none rather than claiming '
       'day order, and both pure functions answer empty without raising')

    # arm 6: no clock, and the head is the newest DAY rather than the last row
    r62f = world()
    roots.append(r62f)
    put_rows(hist37(r62f), [('2001-01-01', 0), ('2001-03-01', 1),
                            ('2001-03-05', 2)])
    rc62f, l62f, _ = sd57(r62f, ['--series-days', '2'])
    rc62g, l62g, _ = sd57(r62f, ['--series-days', '2'])
    t62f = toks57(l62f[0]) if l62f else {}
    scrambled = [{'day': '2026-11-12'}, {'day': '2026-11-14'},
                 {'day': '2026-11-11'}]
    ok('AC-RUN62', rc62f == 0 and rc62g == 0 and l62f and l62f == l62g
       and t62f.get('series') == '2001-03-05:2'
       and t62f.get('window_rows') == '1'
       and RUN._day_face_head(scrambled) == '2026-11-14'
       and RUN.series_file_order(scrambled) == 'mixed',
       'a 2001 history windows back from its own newest day (no wall clock), '
       'two runs print identical bytes, and the pure head picks the newest day '
       'out of a scrambled list instead of the last one')

    # arm 7: the whole day family shares the one head - the silent-day face and
    # the dropped listing follow it, and the joint fixed point still holds
    before62h = tree_bytes(r62b)
    rc62h, l62h, _ = sd57(r62b, ['--series-days', '7', '--days', '2',
                                 '--series-absent'])
    after62h = tree_bytes(r62b)
    t62h = toks57(l62h[0]) if l62h else {}
    real62 = len(l62h[0].encode('utf-8')) if l62h else -1
    lst62 = RUN.list_failure_days_dropped(hist37(r62b), 7)
    ok('AC-RUN62', rc62h == 0 and before62h == after62h
       and t62h.get('line_bytes') == str(real62)
       and t62h.get('output_bytes') == str(real62 + 1)
       and l62h[0].count('series_window=') == 1
       and l62h[0].count('absent=') == 2
       and l62h[0].count('absent_named=') == 1
       and l62h[0].count('series_file_order=') == 1
       and t62h.get('window_from') == '2026-11-08'
       and t62h.get('absent') == '2026-11-08,2026-11-09'
       and lst62.get('head') == '2026-11-14',
       'the silent-day window_from, the absent names and the dropped listing '
       'head all open from 2026-11-14 (the newest day) instead of the file last '
       'row, while the line still prices itself to the byte')

    # ===== AC-RUN63 (R3046): the DEFAULT face names the day its window opens
    # AC-RUN63 was pinned in src/os/backlog.md BEFORE window_head existed
    # (in-window pre-registration, disclosed), and the probe ran BEFORE the pin
    # (qa/probe-R3046.log): on a hand-edited history
    # (11-10,11-14,11-12,11-13,11-11) the printed pairs are the FILE order,
    # window_rows counts by day from the NEWEST day (11-14), and nothing on the
    # line named that anchor - with --days 1 the only printed pair sat outside a
    # one-day window and the line still never said which day it opened at. Two
    # candidate repairs were measured and refused: a "pairs are file order"
    # marker restates what the printed pairs already show (R3000 noise law), and
    # day-sorting the default pairs would end the segment at 11-14, i.e. AFTER
    # last=11-11, moving the contradiction instead of removing it.
    r63 = world()
    roots.append(r63)
    p63 = hist37(r63)
    put_days(p63, [plain_day('2026-11-17', 0), plain_day('2026-11-18', 1),
                   plain_day('2026-11-19', 3), plain_day('2026-11-19', 1),
                   plain_day('2026-11-19', 2)])
    before63 = tree_bytes(r63)
    rc63, l63 = days42(r63)
    t63 = toks42(l63[0]) if l63 else {}
    ok('AC-RUN63', rc63 == 0 and t63.get('window_head') == '2026-11-19'
       and t63.get('window_head') == t63.get('last')
       and l63[0].count('window_head=') == 1
       and tree_bytes(r63) == before63,
       'a writer-shaped history names the day its window opens at, the token '
       'equals last= there because the writer sorts, appears exactly once and '
       'writes no byte')

    r63b = world()
    roots.append(r63b)
    p63b = hist37(r63b)
    mixed63 = [plain_day('2026-11-10', 2, dropped=7),
               plain_day('2026-11-14', 4, dropped=2),
               plain_day('2026-11-12', 1, dropped=5),
               plain_day('2026-11-13', 3, dropped=1),
               plain_day('2026-11-11', 6, dropped=9)]
    put_days(p63b, mixed63)
    rc63b, l63b = days42(r63b)
    t63b = toks42(l63b[0]) if l63b else {}
    file_order63 = ','.join('%s:%s' % (r['day'], r['on_day']) for r in mixed63)
    day_sorted63 = ','.join('%s:%s' % (r['day'], r['on_day'])
                            for r in sorted(mixed63, key=lambda x: x['day']))
    ok('AC-RUN63', rc63b == 0
       and t63b.get('window_head') == '2026-11-14'
       and t63b.get('last') == '2026-11-11'
       and t63b.get('window_rows') == '5'
       and t63b.get('series_outside') == '0'
       and t63b.get('series') == file_order63
       and t63b.get('series') != day_sorted63,
       'a hand-edited history names the newest day as the anchor while the '
       'pairs stay in file order - the refused day-sort is pinned as a '
       'reading, since its segment would end at 2026-11-14, after last=')

    rc63c, l63c = days42(r63b, 1)
    t63c = toks42(l63c[0]) if l63c else {}
    ok('AC-RUN63', rc63c == 0 and t63c.get('series') == '2026-11-11:6'
       and t63c.get('series_outside') == '1'
       and t63c.get('window_rows') == '1'
       and t63c.get('window_head') == '2026-11-14',
       'with a one-row cap on a mixed history the printed pair sits outside '
       'the one-day window and the line says where that window opened - the '
       'case the pairs alone cannot state')

    ok('AC-RUN63', t63b.get('dropped') == '9'
       and [r['dropped'] for r in mixed63
            if r['day'] == '2026-11-14'][-1] == 2
       and t63b.get('dropped') != '2',
       'dropped= still describes the row last= names (9 on 11-11), never the '
       'newest day (2 on 11-14) - the third repair is refused with its '
       'numbers on the line, because dropped and last are the same row')

    r63e = world()
    roots.append(r63e)
    os.makedirs(os.path.join(r63e, 'qa'), exist_ok=True)
    rc63e, l63e = days42(r63e)
    rc63f, l63f = days42(r63e)
    t63e = toks42(l63e[0]) if l63e else {}
    ok('AC-RUN63', rc63e == 0 and rc63f == 0
       and t63e.get('window_head') == 'none'
       and t63e.get('series') == 'none'
       and l63e == l63f,
       'no history answers window_head=none with series=none, raises nothing '
       'and prints identical bytes twice')

    buf63 = io.StringIO()
    with contextlib.redirect_stdout(buf63):
        rc63g = RUN.main(['--failure-days', '--series-days', '7',
                          '--root', r63b])
    l63g = [n for n in buf63.getvalue().splitlines() if n.strip()]
    t63g = toks42(l63g[0]) if l63g else {}
    pairs63 = [p.split(':')[0] for p in (t63g.get('series') or '').split(',')
               if p]
    ok('AC-RUN63', rc63g == 0 and 'window_head' not in t63g
       and bool(pairs63) and pairs63[-1] == '2026-11-14'
       and t63g.get('series_file_order') == 'mixed',
       'the day face does not carry the anchor because its sorted pairs '
       'already end on it, and it still names the hand edit')

    # AC-RUN64 (R3047): the four faces that join a saved history to "today"
    # read a clock, and until now that clock was hidden state - which is why
    # ten arms of this suite went red at 2026-11-20 00:00 while every one of
    # them was still right about the world it built (measured: stashing the
    # R3046 files and rerunning still read the same ten red). The day is now an
    # input (--at), and this arm pins both halves: given a day the faces run at
    # it, and the suite itself never inherits the wall clock.
    r64 = world()
    roots.append(r64)
    f64 = RUN.failure_path(r64)
    RUN.append_failure(f64, 'https://a.example/1', TODAY + 'T01:00:00+08:00',
                       'E_FETCH URLError: today')
    RUN.append_failure(f64, 'https://b.example/2', '2026-08-20T10:00:00+08:00',
                       'E_FETCH URLError: old')

    def trend64(extra):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--failure-trend', '--root', r64] + list(extra))
        return rc, buf.getvalue().strip()

    # Two usable days sit inside a seven-day window that ends on TODAY, and a
    # third day sits ninety-one days back, so moving the stamp moves the window
    # and nothing else.
    RUN.snapshot_failure_day(r64, '2026-11-18T20:00:00+08:00')
    RUN.snapshot_failure_day(r64, TODAY + 'T20:00:00+08:00')
    rc64a, line64a = trend64(['--at', AT])
    t64a = toks57(line64a) if line64a else {}
    rc64b, line64b = trend64(['--at', '2026-11-22T23:59:00+08:00'])
    t64b = toks57(line64b) if line64b else {}
    rc64c0, line64c0 = trend64(['--at', '2026-11-29T10:00:00+08:00'])
    t64c0 = toks57(line64c0) if line64c0 else {}
    ok('AC-RUN64', rc64a == 0 and rc64b == 0 and rc64c0 == 0
       and t64a.get('today') == '1' and t64a.get('wcov') == '2/7'
       and t64b.get('today') == 'absent' and t64b.get('wcov') == '2/7'
       and t64c0.get('wcov') == '0/7',
       'the same world read at three named days moves one day at a time: the '
       'stamped day carries its own count, three days later it no longer names '
       'a today and ten days later the window is empty - the clock is an '
       'input, not hidden state')

    real_at = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    rc64c, line64c = trend64([])
    rc64c2, line64c2 = trend64(['--at', real_at])
    ok('AC-RUN64', rc64c == 0 and rc64c2 == 0 and line64c == line64c2,
       'with no stamp the face still reads the local clock - naming this very '
       'moment explicitly prints the same line, so the default was never lost')

    # The pure series faces never read a clock, so the new flag must change
    # nothing there: a day history is written once at the stamped day, then the
    # same face is read twice with and without it.
    RUN.snapshot_failure_day(r64, AT)

    def days64(extra):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main(['--failure-days', '--root', r64] + list(extra))
        return rc, buf.getvalue()

    rc64d, text64d = days64([])
    rc64e, text64e = days64(['--at', '2026-12-31T00:00:00+08:00'])
    ok('AC-RUN64', rc64d == 0 and rc64e == 0 and text64d == text64e
       and bool(text64d.strip()),
       'the pure series face ignores the stamp: the same history prints the '
       'same bytes whatever day it is asked about')

    before64 = tree_bytes(r64)
    rc64f, text64f = days64(['--at', AT])
    after64 = tree_bytes(r64)
    ok('AC-RUN64', rc64f == 0 and text64f == text64d and before64 == after64,
       'reading it again at a named day is byte-identical and writes no byte')

    # The rot itself, pinned at the source: no call in this suite may reach a
    # clock face without naming the day. A future arm that forgets reads red
    # here instead of on whatever night the wall clock happens to move.
    with io.open(os.path.abspath(__file__), 'r', encoding='utf-8') as fh:
        own = fh.read()
    missing64 = []
    pos64 = 0
    faces64 = ("'--failures'", "'--failure-trend'", "'--snapshot-failures'",
               "'--pending-old-list'")
    while True:
        j64 = own.find('RUN.main(', pos64)
        if j64 < 0:
            break
        k64 = own.find('(', j64)
        depth64 = 0
        while k64 < len(own):
            if own[k64] == '(':
                depth64 += 1
            elif own[k64] == ')':
                depth64 -= 1
                if depth64 == 0:
                    break
            k64 += 1
        span64 = own[j64:k64]
        # A helper that forwards list(extra) takes its stamp from its caller;
        # arms 1-4 above are that caller and read green only when it is named.
        if ('list(extra)' not in span64
                and any(f in span64 for f in faces64)
                and "'--at'" not in span64):
            missing64.append(own.count('\n', 0, j64) + 1)
        pos64 = k64
    ok('AC-RUN64', not missing64,
       'every clock-face call in this suite names its day (unpinned lines: %s)'
       % (missing64 or 'none'))

    # AC-RUN65 (R3048): a stamp names an INSTANT, but every clock face read its
    # day by cutting the first ten characters of the text - so one moment
    # written two legal ways was two different days (measured on one two-day
    # world: trend today=1 vs 3, recent7=3 vs 2, a snapshot under 11-20 vs
    # 11-19, qa/probe-R3048.log). The day is now the local calendar day of the
    # instant, because every `day` on disk is written by a writer stamping
    # datetime.now().astimezone(). The three notations below are ONE moment.
    r65 = world()
    roots.append(r65)
    f65 = RUN.failure_path(r65)
    RUN.append_failure(f65, 'https://a.example/1', '2026-11-19T09:00:00+08:00',
                       'E_FETCH URLError: a')
    RUN.append_failure(f65, 'https://b.example/2', '2026-11-19T10:00:00+08:00',
                       'E_FETCH URLError: b')
    RUN.append_failure(f65, 'https://a.example/1', '2026-11-20T02:00:00+08:00',
                       'E_FETCH URLError: a')
    RUN.snapshot_failure_day(r65, '2026-11-19T09:00:00+08:00')
    RUN.snapshot_failure_day(r65, '2026-11-20T02:00:00+08:00')

    ONE65 = ['2026-11-20T04:00:00+08:00', '2026-11-19T20:00:00+00:00',
             '2026-11-20T04:00:00']

    def face65(flag, at):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RUN.main([flag, '--root', r65, '--at', at])
        return rc, buf.getvalue().strip()

    trend65 = [face65('--failure-trend', at) for at in ONE65]
    fails65 = [face65('--failures', at) for at in ONE65]
    ok('AC-RUN65',
       all(rc == 0 for rc, _l in trend65 + fails65)
       and trend65[0][1] == trend65[1][1] == trend65[2][1]
       and fails65[0][1] == fails65[1][1] == fails65[2][1]
       and 'today=1' in trend65[0][1] and 'wcov=2/7' in trend65[0][1],
       'one instant written as +08:00, as +00:00 and with no offset reads ONE '
       'day on both faces: the three lines are byte-identical and the day they '
       'name is the local one (11-20, today=1 wcov=2/7)')

    days65 = [RUN._day_of(at) for at in ONE65] + [RUN._day_of('2026-11-20')]
    ok('AC-RUN65', days65 == ['2026-11-20'] * 4,
       'the day of a stamp is the instant\'s local day, and a day string is '
       'already a day - the +08:00 and never-offset stamps the rest of this '
       'suite passes keep the day they always had')

    win65 = RUN._window_start('2026-11-20', 7)
    win65b = RUN._window_start('2026-11-19T20:00:00+00:00', 7)
    ok('AC-RUN65', win65 == win65b == ('2026-11-20', True, '2026-11-14'),
       'rows carry day strings and are fed back into the window law, so the '
       'day must be idempotent: the row day and the UTC stamp of the same '
       'local day open the same seven-day window')

    junk65 = [RUN._day_of(''), RUN._day_of('nope'), RUN._day_of('2026-13-45')]
    head65, usable65, thr65 = RUN._window_start('nope', 7)
    ok('AC-RUN65',
       junk65 == ['', 'nope', '2026-13-45'] and usable65 is False
       and head65 == 'nope' and thr65 == 'nope',
       'a stamp that is not a timestamp falls back to its first ten characters '
       'and answers an unusable window rather than raising - a display face '
       'must never die over the value it was asked to display')

    r65c = world()
    roots.append(r65c)
    page65 = b'<html><body><p>steady page for the day gate</p></body></html>'
    first65 = RUN.run('https://c.example/1', r65c, body=page65,
                      fetched_at='2026-11-20T03:00:00+08:00', write=True)
    beat65 = RUN.run('https://c.example/1', r65c, body=page65,
                     fetched_at='2026-11-19T20:00:00+00:00', if_due=True)
    ok('AC-RUN65', first65.get('ok') and beat65.get('skipped') is True,
       'the day gate lives in the same frame: a record written at 11-20 local '
       'time and a beat arriving as the same moment in UTC agree the day is '
       'covered, so the beat stays a no-op instead of crawling twice')

    r65d = world()
    roots.append(r65d)
    buf65 = io.StringIO()
    with contextlib.redirect_stdout(buf65):
        rc65 = RUN.main(['--snapshot-failures', '--root', r65d,
                         '--at', '2026-11-19T20:00:00+00:00'])
    line65 = buf65.getvalue().strip()
    rows65, _bad65 = RUN.read_failure_days(RUN.failure_day_path(r65d))
    ok('AC-RUN65', rc65 == 0 and 'day=2026-11-20' in line65
       and [r.get('day') for r in rows65] == ['2026-11-20'],
       'the CLI snapshot takes a stamp and writes the day of that instant: a '
       'UTC stamp of a 11-20 local moment lands a 11-20 history row')

    with io.open(os.path.join(ROOT, 'tools', 'crawl_runner.py'),
                 'r', encoding='utf-8') as fh:
        src65 = fh.read()

    def body65(name):
        i65 = src65.find('def %s(' % name)
        j65 = src65.find('\ndef ', i65 + 1)
        return src65[i65:j65 if j65 > 0 else len(src65)]

    ok('AC-RUN65',
       '_day_of(' in body65('_window_start')
       and '_day_of(' in body65('snapshot_failure_day')
       and '_day_of(stamp)' in body65('run')
       and 'stamp[:10]' not in src65 and 'now[:10]' not in src65,
       'the stamp-to-day conversion is one helper used by the window law, the '
       'snapshot writer and the day gate, and no face cuts a stamp by hand any '
       'more (a future face that reintroduces the cut reads red here)')

    for root in roots:
        shutil.rmtree(root, ignore_errors=True)

    total = len(CHECKS)
    acs = set()
    for name in CHECKS:
        token = name.split(' ', 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    print('suite: %d assertions over %d criteria' % (total, len(acs)))
    if FAILS:
        print('FAILED: ' + ', '.join(FAILS))
        print('SUITE FAIL %d/%d' % (total - len(FAILS), total))
        return 1
    print('SUITE PASS %d/%d' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
