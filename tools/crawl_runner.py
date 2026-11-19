"""Crawl runner for the QA charter's daily-crawl face (R2991).

WHY: R2990 landed the record face (qa/crawl-log.jsonl via tools/crawl_record.py)
so the five-still scanner could stop judging a crawl by a smoke file's mtime -
but nothing ever WROTE a record except the suite that grades the writer. The
honest state on 2026-11-19 was [QA] FLAG crawl_today=0: the face was truthful
and still unfillable without a human typing a line. This module is the missing
executor: it fetches one source, judges it against a stored baseline, and lands
the result through the shipped writer.

HONEST SCOPE (unchanged from the record module): a record is a DECLARATION.
This runner really does fetch, so the declaration covers a real retrieval - but
it does not prove the fetched bytes are the page a human would see (scripts,
personalisation, A/B variants and CDN edges are outside it), and it does not
decide whether a drift matters. Drift means: the visible text I normalised
tonight differs from the visible text I normalised the last time I stored it.

TWO-FACE DESIGN (so the judgement can be graded offline):
  * fetch()    - the only network call in this file, one urlopen.
  * evaluate() - pure: normalised text + stored baseline -> {verdict, digest}.
A window that wants to grade the judgement hands evaluate() a saved page and no
socket is ever opened; AC-RUN4 pins exactly that.

VERDICT LAW: no stored baseline for the url -> new-source; same visible-text
digest -> no-drift; different digest -> drift. A failed retrieval is NOT a
crawl: run() answers ok=False and writes NOTHING to the record or the baseline -
a failed fetch landing a record would turn the scanner green on a day nobody
read the source.

FAILURE TRACE (R2992): writing nothing made "did not run" and "ran and failed"
the same on disk, because a headless round's stdout only reaches a gitignored
log. A failed retrieval now appends ONE line to qa/crawl-failures.jsonl
(source_url / failed_at / error). That file is a SIDE CHANNEL: the scanner does
not read it, it never feeds a verdict, and it is physically separate from the
record file, so it cannot turn any face green or red. A trace that cannot be
written is reported as trace=None and never replaces the failure answer.

R2993 gives that file its first product READER: summarize_failures() and the
`--failures` command answer "how many, how recently, from which sources, and
what was the last error" in ONE readable line. That is deliberately still not a
gate: the scanner is untouched (AC-RUN5 pins that it never reads this file), a
failure count can turn nothing green or red, and nothing here retries or pages.
Evidence that nobody opens has the same weight as no evidence - this only makes
it openable.

DAY GATE (R2992): if_due=True makes a beat idempotent without a scheduler of
its own - when a usable record already names today, run() answers skipped=True
BEFORE any socket is opened and writes nothing. That is what makes it safe to
call this from a ten-minute grid: at most one real retrieval per day.

FAILURE HISTORY (R2994): --failures answers "what is on disk right now", so
"is today worse than yesterday" had no answer and the same page failing three
days straight read exactly like one bad afternoon. snapshot_failure_day()
persists ONE row per day in qa/crawl-failure-days.jsonl (on_day, total, recent,
bad, urls, newest, dropped - R3020 added the last one), rewriting that day's row
in place so a ten-minute beat does not append duplicates. It is a DISPLAY face only: the scanner never reads it
(AC-RUN9 arm 6), the closeout census only classifies *.log, and nothing here
gates, retries or pages. A history write that fails prints its own line and
never changes the crawl's answer.

FAILURE TREND (R2995): a history row alone answered "what was that day" and
nothing compared two of them, and because a row carried only urls=<count> one
page failing three days straight read like three different pages failing once
each. summarize_failure_trend() joins the history (count series) with the side
channel (which source failed which day) into ONE display line: today, the day
before, the mean, the delta, the worst day, and how many sources recurred. The
history row's schema is untouched on purpose - the same fact in two files is two
places to drift - and the line gates nothing.

EVIDENCE FACE (R2996): the trend counted, but it could not say WHICH file it
counted from, so a pruned qa/crawl-failures.jsonl read exactly like a source
that never failed (recurring=0 sources=0 both ways). The line now names its own
evidence: evidence=side when the side channel is on disk, evidence=history when
it is gone and only the day history's newest_error survives (ONE sample, a
degraded read, labelled as such), evidence=none when neither face exists. It
also carries kind=<bucket>:<n>, the most common exception CLASS in the window -
only the class token of 'E_FETCH <ExceptionType>: <msg>' is read, never the
message body, so this is a label and NOT a cause judgement. Ties break on the
bucket name so two readers never disagree.

RECURRENCE WEIGHT + ONE BUCKET (R2997): recurring=<n> counted SOURCES, so a
source failing twice and one failing twelve times read the same; the line now
carries recur=<sources>:<failures> - the same recurring sources and how many
failures the window attributes to them. When the side channel is gone the
honest answer is recur=none (UNMEASURED), never 0:0, because 0:0 would claim
"no recurrence" from evidence that never arrived. The same failure_kind() also
classifies --failures' newest error (kind=<bucket>), so one error string has
exactly one reader.

BASELINE LAW: qa/crawl-baselines.json, one object keyed by url, holding digest /
bytes / fetched_at / excerpt. It is a product file (a person can read what the
page said last time), written atomically after the record is appended.

COVERAGE + THE RETENTION ANSWER (R2998): the group canon
cph4/resource-chain.md section 4.1 requires every append-only file to have a
rotation design (current segment + archive segment + retention). The failure
files are append-only, so that law covers them BY CATEGORY - and this repo has
no rotation design for them, which is stated rather than implied. The measured
reason it is not built here: qa/crawl-failure-days.jsonl is 107B per row, one
row per day, rewritten in place on a same-day beat, so a full year is ~38.1KB;
the side channel qa/crawl-failures.jsonl grows only when a crawl actually
fails, and its worst bound at every beat failing for a year is ~9.07MB - both
two orders of magnitude below the only per-file jsonl water line the group canon
actually states (cph4/resource-chain.md section 3.4, world/*.jsonl, 100MB).
CORRECTION R2999: this header previously divided those numbers by "the
repository's 20MB per-file pre-commit gate", and that gate does not exist in
this checkout - measured, Tools/hooks/pre-commit and Tools/hooks/pre_commit_gate.py
carry no byte threshold at all (they gate round-freeze and evidence dialect).
With no reusable rotation tool in the tree and no size pressure, a second
cleanup mechanism would be machinery without a problem - so the exemption is
numeric, anchored on a line the group canon really states, and written down
here instead of silently assumed. What IS fixed is the other
half: a trimmed history used to read exactly like a repo that had just started
recording, because the line reported rows in the file and never how much of the
requested window was observed. The trend line now carries cov=<first>..<last>
(the history's own usable coverage) and wcov=<covered>/<requested days>, so an
under-observed window answers "1/7" instead of pretending to be complete.
Neither field gates: nothing turns green or red because of them.

SIZE FACE (R2999): the retention exemption above was arithmetic nobody could
check from the product, because --failures printed counts and never the BODY of
the file it counted. That line now carries bytes= (os.path.getsize, 0 when the
file is absent - absence is an answer, never an exception), lines= (every
physical row splitlines() sees, so it includes malformed rows and blank rows),
size_gate= (bytes as a percentage of SIZE_REFERENCE_BYTES, printed with four
decimals) and gate_ref=100MB (the denominator, on the line, so no reader has to
guess which law the percentage divides by). lines - (total+bad) is the blank-row
count, which is why the field is counted from the file and not from the reader:
a reader that silently skips a row shape makes the two disagree.
DISPLAY ONLY: the percentage is not a verdict. Nothing here refuses a write,
pages anyone or turns the scanner - no PASS/FLAG token exists on this line, and
a file above the reference line still prints a number rather than a judgement.
The reference is the group canon's water table line for a single append-only
jsonl, NOT a threshold this repo enforces.

SIZE FACE ON THE HISTORY (R3000): the retention exemption above also argues
about qa/crawl-failure-days.jsonl ("~38.1KB per year"), and that file's reader
printed days / bad / first / last / series - no body size at all - so half the
exemption still required a person to run Get-Item. --failure-days now carries
bytes= (os.path.getsize of the WHOLE file, 0 when absent), size_gate= (the same
pure helper, so history and side channel cannot disagree) and gate_ref=100MB.
Deliberately NOT printed: lines=. Measured in the R3000 probe: a same-day beat
rewrites this file through snapshot_failure_day, which keeps only validated
rows, so malformed and blank rows are dropped and the physical line count
equals days on every live checkout - the field could only restate days. bad=
still reports the transient case. Also measured and stated rather than implied:
size_gate is rounded to four decimals, and 0.0001% of a 100MB reference is
~105B, so a file within about a hundred bytes BELOW the line also prints
100.0000% - the number is a display, and 100.0000 does not mean "at the line".
Nothing here gates, retries or pages.

EVIDENCE THIS FILE ITSELF EATS (R3020): the same rewrite keeps validated rows
only, so a beat that finds malformed rows silently removes them, and the row it
writes carried bad= (the SIDE channel's unusable count) - a fact about the other
file, never about its own loss. Measured before this was written
(qa/probe-R3020.log): a healthy side channel over a four-line dirty history
writes bad=0 while the rewrite eats 4 lines. The day row therefore also carries
dropped= - unusable lines of THIS file discarded by rewrites that stamped the
same day, accumulated rather than per-rewrite, because the ten-minute beat
would overwrite a per-rewrite number with 0 before a person could read it (the
transience R3019 measured for bad-line numbering). Blank lines are dropped too
and are not counted, the same law _json_lines follows. Rows written before this
field existed are not backfilled: their drops were never measured and 0 would be
invented. NOT added to the series or the trend row: those aggregate many days,
and summing a key that older rows do not carry would print unmeasured as zero.

NOT VISIBLE, NOT ATTRIBUTABLE (R3021): that count was written down but no face
printed it - a reader had to open the jsonl by hand - and it never says WHICH
day's lines were eaten. Measured (qa/probe-R3021.log): _json_lines hands over
row=None for every rejected line, even when the raw text carries a usable day
(an on_day reject whose text reads day='2026-11-16'), so attribution would mean
parsing or echoing text the readers already refused; line numbers cannot stand
in either, because a rewrite renumbers (5 physical lines -> 2). Attribution is
therefore NOT built, and this paragraph is the record rather than a guess. What
can be shown without inventing a number is the LAST day row's own value:
CRAWL-FAILURE-DAYS prints dropped= right after last=, where none means that row
was written before the field existed (NOT zero) and 0 means nothing was eaten.
It is that one row's number, never a sum: older rows without the key must not
be read as zero.

THE WRITER DID NOT SAY WHAT IT WROTE (R3022): R3021 gave that count a reader,
but the step that writes it - the snapshot beat, whose `CRAWL-FAILURE-DAY`
header a person watches every ten minutes - printed day/on_day/total/recent/
bad/urls and nothing about the lines its own rewrite had just eaten. Measured
(qa/probe-R3022.log): on this checkout the standalone snapshot printed
`bad=0 urls=0` while the row it wrote carried dropped=0, so the live face and
the row disagreed by omission. BOTH print sites now end with dropped=, the
value of the row just written, which always exists (snapshot_failure_day sets
it; a fresh row measures int, never none - `none` belongs to the DAYS header
reading a row written before the field). It is appended at the END so the five
older tokens keep their positions and a positional reader keeps working - and
deliberately NOT placed between bad= and urls=, where two different facts (the
side channel's unusable count and this file's eaten count) would read as one.
The per-day list of dropped values is still unbuilt: it is a per-row face, not
a sum (only two `.get('dropped')` sites exist and neither adds rows), and
R3017/R3020 refused sums, not lists.

EVERY DAY, NOT JUST THE LAST (R3023): R3021 answered for `last=` only, so an
earlier day's eaten count still meant opening the jsonl. Measured
(qa/probe-R3023.log): the DAYS face prints exactly ONE line, so a per-day list
cannot ride on its header without breaking that contract (P3a) - and the flag
set carries no help/set arm, so a separate subcommand is free (P1a/P1b). This
face is `--failure-days-dropped`: a header `CRAWL-FAILURE-DAYS-DROPPED days=<n>
bad=<n>` then one `DAY-DROPPED day=<day> dropped=<n|none>` per usable row.
Order is FILE order, never sorted and never de-duplicated - measured (P2e) a
history can hold one day twice, and a de-duplicated listing would hide a row
instead of reporting it. `dropped` is that row's own value and `none` when the
row predates the field or carries a non-int (type() not isinstance(): JSON true
passes isinstance). Refused here: putting the list on the DAYS header, adding
the key to the series pairs or the 30-key trend row, reading a missing key as
zero, summing or maxing across rows, and backfilling old rows.

A WINDOW THAT SAYS IT TRUNCATED (R3024): that listing printed every row with no
window, so its length grew with the file (one row per day, kept forever) while
the DAYS series had taken a `--days` limit since R3000. Measured before this
change (qa/probe-R3024.log): the unwindowed header is pinned by TWO
exact-equality arms (P2a), `--days` already has seven readers elsewhere and
this branch reads none of them (Q3b), and nothing anywhere reads `days=` as the
printed-line count (Q2a/Q2c). So the window is OPT-IN and the default face is
byte-identical: `--failure-days-dropped-window N` prints
`CRAWL-FAILURE-DAYS-DROPPED days=<n> bad=<n> window=<N> shown=<n>
truncated=<0|1> hidden=<n> head=<day|none>`, where `days` keeps its own meaning
(usable rows in the file) and `shown` is what this run printed. Truncation is
therefore a token on the same line rather than an absent row that a reader
would take for "that day ate nothing".

The window law is NOT re-derived here: `_window_start(head, N)` is the one
place it lives (R3014), and head is the file's OWN newest row - data-derived,
so no clock and no wall-day drift (AC-RUN41 arm 7 pins this with 2001 rows).
Only `day >= threshold` is kept: no sort, no de-duplication (a same day twice
stays twice, the R3023 law untouched), and rows below the threshold are counted
into `hidden` instead of vanishing silently. An empty history answers
head=none shown=0 truncated=0 - absence is still an honest zero.

TWO MEANINGS OF ONE NUMBER, NAMED (R3025): `--days` reaches this face as a ROW
limit (`rows[-limit:]`, since R3000) while the same number is a DAY window on
the failure face - and the two only coincide when the history holds exactly one
row per day. Measured (qa/probe-R3025.log): a history whose newest day holds
three rows plus one row sixty days back printed that old row in `series=` under
the default seven, while the seven-day window counted four rows and not five;
with `--days 2` the tail printed two of the four rows inside the two-day
window. The header said neither. The tail is NOT redefined (the printer and
five suite arms read its shape, and `--days` has seven readers across the
module), so `series_window_counts()` publishes what the line could not say:
`series_limit=` the row limit applied, `series_shown=` the pairs printed,
`series_outside=` how many of those fall before the window threshold, and
`window_rows=` how many usable rows the window actually holds. Head is the
file's OWN newest row, so an old history windows against itself and no clock
is read (2001 rows pinned by AC-RUN42 arm 6). `days=` keeps its meaning (usable
rows in the file) and can differ from `series_shown=` - which is the point.
Refused: reading `--days` as a day window here (seven readers would change
meaning at once), re-shaping the series tail, and reusing the bare
`shown/hidden/truncated` names R3024 built for a day window - one word, two
laws, is exactly the confusion this paragraph exists to prevent.

THE SERIES CAN BE ASKED FOR BY DAY (R3026/R3027): counting the tail only works
when every day holds exactly one row, so `--series-days N` selects the pairs by
the same inclusive day window the other faces use (`series_days_window`, head =
the file's own newest row, no clock) while `--days` still caps how many pairs
print - window first, then the tail of that selection, so `series_shown=`
counts printed pairs and `window_rows=` counts rows in the window. A day with
NO row used to be simply absent from the series, leaving "four quiet days" and
"four unrecorded days" the same shape; `--series-absent` (opt-in, refused with
rc=2 unless `--failure-days --series-days N` are both given) names them in a
SEPARATE token - `series_absent=<n|none> absent=<day,...|none>` - because a
measured zero already prints as :0 inside the pairs and five arms assert a
2-tuple there. When the head day is unusable nothing is measurable, so the
count answers none rather than a zero that would read like "every day was
recorded" (the R2994 absent-not-zero law, carried).

THE GAP HAS A TOTAL (R3028): naming every silent day still left "how many of
the last seven days hold a record at all" as a comma count, and `window_rows=`
cannot answer it - a day with three rows prints three (measured: four rows on
two days inside a seven-day window, qa/probe-R3028.log). So `--series-absent`
now also prints `days_present=<n|none>` from `series_presence_counts()`:
DISTINCT calendar days inside the window that hold at least one row, beside the
gap count, with the invariant `days_present + series_absent = series_window`.
A `window_days=` token was refused - it could only repeat `series_window=`,
which is the noise law this module already carries (R3000), and a
`days_absent=` name was refused because one arm counts the literal
`absent=` twice on the line, so a third such token would read red while every
number stayed right.

THE DIFFERENCE HAS A NAME (R3029): present and rows printed side by side still
left "who is bigger, and why" as a subtraction the reader performs - four rows
on two days shows 4 beside 2 and never says the extra two are the same days
again (measured: qa/probe-R3029.log). So the same opt-in tail now also carries
`repeat_rows=<n|none>`: window rows beyond the first on each day that holds a
row, so `days_present + repeat_rows = window_rows` sits beside the older
`days_present + series_absent = series_window`. It is stated as a subtraction
of two printed numbers rather than a new measurement, and it is not a
restatement of any other token - a `rows_per_day=` ratio and a `repeat_days=`
name were both refused (a ratio is not a count, and "days" would put a second
meaning on the word `days_present` already owns). Unusable head day answers
none, never an invented zero (the absent-not-zero law, carried).

R3030 (measured first - qa/probe-R3030.log): `repeat_rows=` counts same-day
second-and-later rows and leaves WHAT THEY ARE as homework. `on_day` is the
number of that day's failure rows at write time (a count, not a clock), so the
same opt-in tail now also carries `retry_rows=<n|none>`: repeated rows whose
on_day is not greater than the previous row of the same day - rows that carried
no more failure evidence than the row before them. `retry_rows <= repeat_rows`
holds by construction and the remainder grew between writes. It is an
inference, not proof of an interrupted run, and a pruned side channel also
fails to grow - stated in the function. A `reading_rows=` token was refused as
a restatement of `repeat_rows - retry_rows` (the R3000 noise law), and an
unusable head answers none rather than an invented zero.

R3031 (measured first - qa/probe-R3031.log): the board asked whether the window
edge could cut a DAY in half, leaving an in-window first row that is really a
continuation of rows outside the window (which would make `repeat_rows=` and
`retry_rows=` undercount). Measured: it cannot. Window membership is decided by
the row's OWN date (`str(day)[:10]` against one threshold), so a calendar day is
wholly inside or wholly outside - the split set reads empty on every existing
fixture and on every width 1..10. So `repeat` and `retry` are EXACT for the
window, not lower bounds, and an `edge_rows=`/`split_rows=` token was refused
rather than manufactured for a defect that cannot happen (and extending `retry`
across the edge was refused because it reads retry=1 against repeat=0, breaking
`retry_rows <= repeat_rows`). What WAS genuinely unprinted is the day the
window starts on: `series_window=7` gives a width and leaves the reader to
count backwards from the newest pair. The opt-in tail now also carries
`window_from=<day|none>` - the threshold `_window_start` actually applied, so
`window_from=2026-11-13 series_window=7` reads as 11-13..11-19 by eye. It is a
date, never an invented one: an unusable head day answers none.

THE SILENT-DAY LIST STOPS AT A MONTH, ITS COUNT DOES NOT (R3032, measured
first - qa/probe-R3032.log): `absent=` printed one name per silent day, so the
line grew with the window - 11.00 measured bytes per name, and this checkout's
single-row history printed 364 names (4310 bytes) on one line at width 365. The
cap is on NAMES, not bytes: a byte budget cannot be predicted from the window,
while "the first 31 silent days" can, and 11.00 bytes/name is a constant. The
opt-in tail now also prints `absent_named=<n|none>` beside the list;
`series_absent=` keeps the FULL total, so `absent_named < series_absent` is a
visible truncation rather than a list that reads short. Refused there: a byte
cap, a redefined `series_absent=` (its old meaning is the whole count), a
boolean-only marker (the omission count is not otherwise printed but a boolean
cannot say how many), and a `--series-absent-limit` flag - THAT refusal is
superseded below on measured grounds, not reversed by preference.

THE FULL LIST IS ONE OPT-IN FLAG AWAY (R3033, measured first -
qa/probe-R3033.log): the board asked whether the silent days past the 31st are
gone from the repo. Measured, in order. (1) From the ONE line they are not
recoverable: two private worlds with the same window, the same days_present=10,
series_absent=50 and absent_named=31, differing only in three HIDDEN row days
(10-25..27 vs 10-28..30), printed BYTE-IDENTICAL lines - so the 19 unnamed
silent days and the hidden row days are both unrecoverable from that line.
(2) The premise "nowhere in the repo" is FALSE and is named here rather than
quietly dropped: `--failure-days-dropped --failure-days-dropped-window N`
prints `DAY-DROPPED day=<day> dropped=<n|none>` for every usable row, so the
silent set is one invocation plus a set subtraction away (bad rows are excluded
from both faces, so both share that blind spot). (3) An opt-in flag collides
with nothing: measured 6 arms with count('absent=')==2 (none forbids a new
flag), 1 with count('absent_named=')==1, ZERO whole-line equality arms carrying
`absent=`, and the default face untouched at 214 bytes. What the flag buys is
stated plainly: the face that asks "which days are silent" answers it itself,
instead of the reader being taught to subtract a different subcommand's row
listing. `--series-absent-limit <N|all>` is therefore OPT-IN with the default
still 31, so no default line grows; `all` restores the full list (and the full
365-day line, which is the price of asking). `series_absent=` keeps the FULL
total under every setting.

FAILURE IDENTITY + REPAIR READING (R3001): the trend could say how many
sources failed and how often, but never WHICH source failed last, nor whether
that source had been seen succeeding since - so "same page again, and is it
fixed?" still needed a person watching a terminal. The line now carries
newest_src= (the source of the latest failure in the window, taken by largest
failed_at rather than by file order) and since_ok= (yes when the crawl record
holds a LATER row for that same source - a failed retrieval never reaches the
record, so a later row is honest evidence that a retrieval succeeded; no when
the record exists but holds no such row; unmeasured when there is no record
file, no source identity, or no timestamp). Identity lives ONLY in the side
channel because the history row stores urls=<count> on purpose - one fact in
one place - which is also why a pruned side channel answers newest_src=none and
since_ok=unmeasured rather than "no page failed". Both fields compare literal
ISO text on both sides (every writer stamps astimezone().isoformat()), stated
rather than parsed. NOT built, and named here so the answer is not implied: the
sandbox failure slot stays a SINGLE slot (tmp/live-sandbox-failed.json, 1287B
measured, gitignored, no reader outside its writer and its suite); keeping the
last N failures would create a new append-only face, and group canon
cph4/resource-chain.md section 4.1 requires a rotation design for every such
face - machinery for a problem that has not occurred. Neither field gates: no
PASS/FLAG token is emitted and the scanner still never reads these files.

REPAIR STABILITY (R3002): measured before this was written - a stable repair
(fail, ok) and a source that was fixed, broke again and was fixed again
(fail, ok, fail, ok) printed the SAME two readings, since_ok=yes and
recur=(0,0). "Is it fixed now?" and "does it stay fixed?" are different
questions, so the line also carries flips= - how many times THIS source was
observed working and then failing again, counted as success -> failure
transitions on the merged timeline of the two faces that already exist. recur=
is unchanged and answers a third question (sources failing on two or more
distinct days inside the window); flips uses every row on disk for that one
source and is not window-trimmed, which cov= already reports. A failure must
be STRICTLY later than the success it follows, so a same-second success and
failure are never ordered into an invented flip. unmeasured follows since_ok's
law (no record file, no identity, no side channel); a record that exists but
holds no row for the source answers 0, meaning it was never seen working in
between. A trimmed record can therefore undercount, exactly as since_ok=no
already could - stated, not patched. flips gates nothing: no PASS/FLAG token.

RECORD COVERAGE (R3003): measured before this was written - a record file that
STOPS before the failure and one that COVERS the days after it (through another
source) printed the SAME row, since_ok=no flips=1, so "we looked and it never
came back" and "we never looked after the failure" were one line. The record
face is the only file that can answer the repair question, so its own reach now
prints as rcov=<first day>..<last day> beside the answer it supports. THREE
SEPARATE FACES, named so they cannot be read as one: cov= and wcov= describe the
DAILY FAILURE HISTORY file (qa/crawl-failure-days.jsonl), while rcov= describes
the CRAWL RECORD file (qa/crawl-log.jsonl) - different files, and neither
reading may be explained by the other. rcov is DAY-granular (the first ten
characters the record writer already owns), so the literal cross-zone ordering
weakness the two stamp comparisons carry cannot leak into it, and an absent file
or a file with zero usable rows answers none rather than an invented span.
Display only: nothing gates on rcov, no PASS/FLAG token is emitted, and the
scanner still reads neither file. That window left the verdict itself alone on
purpose and named the cost: a record ending before the failure still read
since_ok=no beside flips=0.

LOOKED vs BROKEN (R3004): that named cost is paid here, and the probe measured
a rewrite set LARGER than the previous window's own estimate - five shipped
assertions pinned since_ok=='no' (one in AC-RUN18, three in AC-RUN19, one in
AC-RUN20) and four of six probe worlds move. The rule now: before since_ok may
answer 'no', the crawl record must be shown to reach STRICTLY past the failure
stamp (through ANY source, because the pipeline fetching another page afterwards
is what proves the pipeline ran). A zero-byte record, a record whose newest row
predates the failure, a record of nothing but malformed lines, and a success
stamped in the same second as the failure all answer unmeasured instead of
claiming the source is still broken. Strictness mirrors flips' own tie rule. The
row still carries rcov=, so a reader who sees unmeasured can see WHERE the
record stops and why the question went unanswered.
flips DOES NOT follow this and the split is deliberate: since_ok asks "is it
fixed now" and needs an observation after the newest failure; every flip is a
pair of events already on disk, so a record that stops before the newest failure
still answers a measured count. since_ok=unmeasured beside flips=1 is therefore
a truthful pair, not a contradiction. Neither field gates and no key was added.

WINDOW BREADTH (R3005): newest_src/since_ok answer for ONE source - the latest
failure in the window - so a window with three failing pages said nothing about
the other two. Measured before this was written: with A repaired, B still gone
and C still gone, the row named only C (since_ok=no) and A's yes / B's no
appeared in none of its 22 keys. The line now also carries
pending=<no>/<judged>: over the WHOLE window, each source judged on its OWN
latest failure, the numerator counts sources the record shows were looked at
afterwards and never came back (since_ok=='no'), the denominator counts sources
where that judgement could be made at all (yes or no). An unmeasured source is
in neither number - aggregating the verdict must not undo the R3004 split, and
it was measured rather than assumed: a since_ok != 'yes' numerator counts a
source whose newest failure is later than every record row as pending even
though nobody looked after it. pending=none (not 0/0) when nothing was judged:
zero-of-zero would read like "nothing is pending" when the truthful statement is
"nothing was judged". It answers a THIRD question, distinct from recur= (sources
failing on two or more distinct days - measured independent in both directions:
recur=(0,0) with pending 1/1, and recur=(2,4) with pending 0/2). Printing one
line per source was refused: the one-line contract is what the CLI, the arms and
the scanner's zero-consumption premise rest on. Display only, no PASS/FLAG.

NAMING ONE (R3006): pending=<n>/<judged> answers HOW MANY sources are still gone
and never WHICH one, so a person had to guess where to start. The row now also
carries pending_src= - the pending source WAITING LONGEST (its own latest failure
stamp smallest, ties broken by url ascending so two readers never disagree), or
none when nothing is pending. Two candidate fixes were measured before this was
written and one was REFUSED: an unjudged=<n> field is pure arithmetic, because
unjudged always equals sources minus the pending denominator (measured in three
worlds reading 0, 1 and 2), so it would only restate two fields already on the
line. The earlier premise that pending=none and "all sources came back" read the
same was also measured FALSE (the tokens read 'none' versus '0/2'), and is
recorded rather than repeated. What is NOT claimed: with several pending sources
only the first is named, and an unmeasured source is never named (the R3004
split holds - a source nobody looked after is not pending). Display only,
no PASS/FLAG.

HOW LONG (R3007): the name answered "start here", never "how long has this been
gone", so a source broken five minutes ago and one broken a week read the same.
The row now also carries pending_age_d= - whole days from the NAMED source's OWN
latest failure date to the window day, both taken as the literal first ten
characters of an ISO stamp (the record writer's day law). It is deliberately not
derived from the failure summary's newest_at: measured in the probe world, that
value is taken across ALL sources and named a different source's stamp than
pending_src did. It reads none - never 0 - when no source is named, when either
date is unusable, or when the stamp is LATER than the reference day (an age
cannot be invented from a future failure). Three coverage readings already on
the row answer different questions and are untouched: rcov= is how far the
crawl record reaches, cov=/wcov= are how much of the failure-day history is
covered, pending_age_d= is elapsed days for ONE named source. The other pending
sources are still counts, not names: their number is pending[0]-1 (arithmetic,
refused as a field) and their identities need one line per source (refused).
Display only, no PASS/FLAG.

AGE SPAN (R3008): one age described the source waiting LONGEST and said nothing
about the rest, so with several pending sources a person could not tell a burst
that just started from a long tail - measured, three pending sources aged 0/2/4
days read pending_age_d=4 and the source that broke TODAY appeared in none of
the 24 keys. The row now also carries pending_age_min_d= - whole days from the
NEWEST pending source's own latest failure to the window day, the same ten-
character day law and the same None rules as pending_age_d. Together the two
numbers are the AGE SPAN of the pending set: pending= answers HOW MANY,
pending_age_d= answers how long the OLDEST (the named one) has waited,
pending_age_min_d= answers how long the YOUNGEST has. A pending_age_max_d field
was measured and refused: the named source is by construction the oldest, so a
max would restate pending_age_d rather than say anything new. With one pending
source, or several sharing one stamp, the two ages coincide - that is the truth
and is pinned as such, not turned into a None. Display only, no PASS/FLAG.

MIDDLE (R3009): two ends described the span and nothing described what sat
between them, so the question a person actually asks - "is this a burst that
just started, or an old tail with one new arrival" - had no reading. Measured
before this changed: two worlds with the SAME ends but different middles (ages
5/3/0 versus 5/1/0) were identical on all 25 keys, and so were a world with the
mass at the old end (5/5/5/0/0) and one with it at the new end (5/0/0/0/0). The
row now also carries pending_age_med_d= - the middle element of the pending set
sorted by age, taking the one nearer the OLD end when the count is even (the
"second oldest" at N=4), on the same ten-character day law and the same None
rules as the other two ages. This is NOT the max field refused in R3008: a max
equalled pending_age_d by construction in every world, while the middle only
coincides with an end at N<=2 or when the mass piles on one end - which is
precisely the reading it adds. Pointing a reader at the failure-day file
instead was measured and refused: that file carries day-level counts with a
urls= COUNT and no per-source identity or age, so it cannot answer which source
waited how long. Four readings now divide the work: pending= is HOW MANY,
pending_age_d= is how long the OLDEST (the named one) waited, pending_age_min_d=
is how long the YOUNGEST waited, pending_age_med_d= is where the MIDDLE sits -
near pending_age_d when the mass is old, near pending_age_min_d when it is new.
Three scalars are still not a distribution: the per-source ages are not on this
line and a histogram is refused by the one-line contract. The window bounds
what any of these can say - with window_days=7 no age exceeds 6 and a failure
older than the window is not pending at all (measured). Display only, no
PASS/FLAG.

OUTSIDE THE WINDOW (R3010): the window decides who is counted, so a source whose
OWN latest failure fell before the window start left the row entirely - measured,
the same side channel read identical on all 26 keys whether that source was still
broken or had been repaired (only rcov moved, because the record gained a row),
and a side channel trimmed to the window read identical to a healthy world on
every key. "Still hanging" and "fixed long ago" must not be the same row. The
row now also carries pending_old=<n>/<judged>: over sources whose OWN latest
failure is STRICTLY before the window start, the numerator counts those the
record shows were looked at afterwards and never came back (since_ok=='no'), the
denominator counts those where that judgement could be made (yes or no). The two
fractions do not overlap: pending= covers the population INSIDE the window
(whose denominator is sources=), pending_old= covers the population outside it,
each with its own denominator. Rewriting pending= to count both was measured and
refused: the row would then report more judged sources than the sources= it
names in the same breath. judged==0 reads none - never 0/0 - because a side
channel trimmed to the window, a side channel that never recorded anything
outside it, and a record that stops before the old failure all mean "nothing was
looked at out there", not "nothing is pending out there". Display only,
no PASS/FLAG.

COVERAGE OF THE SIDE CHANNEL (R3011): pending_old= counts over the side channel
but never said how far back that channel reaches - measured, two worlds whose
side channels reached one day and ninety-one days read IDENTICAL on all 27 keys
(the only difference was one earlier failure row of the SAME source, whose own
latest failure - and so every pending_old= number - was unchanged). The row now
also carries fcov=<first>..<last>: the first and last usable failure day the
side channel itself holds, on the same ten-character day law and the same
de-duplicate-and-sort rule as cov= and rcov=. Every coverage reading now has its
own file, stated in the header so none can be read as another: cov= is the
FAILURE-DAY HISTORY file's span, wcov= is how many days inside the WINDOW have a
history row, rcov= is the CRAWL RECORD's span (success evidence), fcov= is the
FAILURE SIDE CHANNEL's span (the evidence pending_old= judges on). fcov= follows
the FILE, not the window: measured, the same file read the same span at a 7-day
and a 14-day window while pending_old= went from 0/1 to none. Absent, empty and
all-unusable side channels all read none - never an empty string or ('','') -
because a channel with no usable row is "no reach measured", not a span of zero
days. Malformed rows and unusable stamps never widen the span: measured, adding
a non-JSON line and a 'nope' stamp left the span byte-identical while bad grew.
It does NOT promise how far the channel reached BEFORE it was trimmed: fcov is
how far it can be read NOW. Display only, no PASS/FLAG.

AGE OF THE OLD WAITERS (R3012): pending_old= names a fraction, never how long the
sources behind it have been gone - measured, a one-day channel and a one-day
window edge read the same fraction, and fcov.first= is the oldest failure in the
FILE, which may belong to a source that was repaired long ago (measured: fcov
2026-08-20..2026-11-10 while the source still gone had failed on 2026-11-10 and
fcov.first belonged to a repaired one). The row now also carries
pending_old_age_d=<days>: the whole-day age of the still-pending out-of-window
source that has waited longest, on the same ten-character day law and the same
None rules as the three in-window ages. None when pending_old= is none (nothing
was looked at outside, or the channel was trimmed) and none - never 0 - when
every judged old source came back, because "nobody outside is pending" and "one
broke today" must not print the same digit. What R3010 refused stays refused:
naming an old source (pending_old_src) and one line per old source. This is a
single aggregate over the old population, the same shape as pending_age_d= over
the in-window population. Display only, no PASS/FLAG.

THE OTHER END OF THE OLD TAIL (R3013): one age described only the longest old
wait, so with two waiters the other was invisible - measured, a second waiter
that failed 90 days ago and one that failed 9 days ago read IDENTICAL on all 29
keys (qa/probe-R3013.log). The row now also carries
pending_old_age_min_d=<days>: the whole-day age of the YOUNGEST still-pending
out-of-window source, the second end of that population, on the same day law and
the same None rules as the age beside it (None when pending_old= is none, and
none - never 0 - when every judged old source came back). A MIDDLE reading was
measured and REFUSED: with two waiters - the only count the board itself named -
the middle nearer the old end IS the longest age in both worlds, so it would add
a digit and no information (it diverges only at three or more, where reading the
shape needs one line per source, which the contract refuses). Pointing a reader
at the failure file was also measured and refused: with the failure file
byte-identical, a single extra record row moved the old fraction from 2/3 to
1/3, because "is it still gone" is answered by the record and not by the file.
With one old waiter the two ages coincide - pinned as the truth it is, the same
way the in-window pair pins its own coincidence. Display only, no PASS/FLAG.

OLD WAITERS BY NAME (R3014): the row gave two ends and a count, so with three
old waiters the middle one had neither a name nor an age - measured
(qa/probe-R3014.log), two worlds whose second-oldest waiter was a different
source read IDENTICAL on all 30 keys. Naming them on this row is refused by the
one-line contract (R3010/R3013), so the list is a SEPARATE read-only face:
`--pending-old-list` prints one header line and then one line per still-pending
out-of-window source. It calls the SAME predicate the row uses
(_out_of_window_waiting), so the count, the two ends and the list cannot
disagree; it writes nothing, gates nothing and names no verdict. The R3010
sentence "Not a per-source face either" was scoped BY ITS OWN REASON to this
row's one-line contract, and that scope is stated here rather than left wide.

WHY AN EMPTY OLD TABLE IS EMPTY (R3015): the list could print
pending_old=none with zero rows, and three different shapes read exactly that
header - measured (qa/probe-R3015.log): an absent side channel, a channel
trimmed to the window, and a channel holding an old row that the record never
looked after. "Nothing outside was ever recorded" and "we recorded it and never
looked again" were the same line, and neither said how far the evidence under
them reached. The header now also carries fcov=<first>..<last> (R3011's span,
derived from the rows this call already loaded - a SECOND read was measured to
drift inside one call when a row was appended between reads, so the header
would have claimed evidence the list never judged) and, when the table is
empty, reason=<no-coverage|unmeasured|all-repaired|no-window>. The board named
two shapes; the measurement found three under none (all-repaired was already
readable as 0/n), so the third is named rather than folded into a false one.
A NON-empty list carries no reason: it answers "why empty" only. No row cap
was added: measured, a channel with thirty days of failures from three sources
(90 rows, 9540B) still lists three lines, because the list is bounded by the
DISTINCT SOURCES that ever failed - the configured crawl set - and not by days.

WHEN THE CHANNEL WAS LAST WRITTEN (R3016): the header described population and
reach, never liveness. Measured (qa/probe-R3016.log): a channel whose last
failure landed 00:05 and one whose last failure landed 23:50 the SAME day read
the same dictionary and the same header, because fcov= is a pair of days. The
board's own pair - stopped yesterday versus written this minute - had ALREADY
been separated by that span, so the measurement is kept beside the gain instead
of being sold as one. The header now carries last_at=<YYYY-MM-DDTHH:MM>, the
newest usable stamp echoed from the rows this call already loaded, and
last_at=none when there is no usable row. It is not an age: measured, a day age
over that stamp equals the age of fcov's last day in every probed world (a
restatement), and an hour age would need a clock this module never reads.
Display only, no PASS/FLAG.

HOW MANY LINES ON THE CHANNEL ARE UNUSABLE (R3017): the dictionary carried
`bad` from the beginning and the header never printed it, so a channel holding
two broken lines and a clean channel printed the same header - measured
(qa/probe-R3017.log): the same usable rows plus two malformed lines moved `bad`
0 -> 2 while fcov, last_at and pending_old stayed byte-identical, and the two
headers were equal. The strongest shape is the EMPTY table: a channel holding
only unusable lines read exactly like a channel that does not exist (both
fcov=none, bad 0 vs 2, identical header). The header now carries bad=<n>,
ALWAYS printed including 0, taken from the single read_failures call this face
already makes (measured: one call per invocation, so no second read). Position
is after days= and before fcov=, so the count sits with the evidence it
qualifies. NOT folded into reason=: reason answers "why is the table empty",
a broken line is evidence quality and unrelated to population - measured, a
populated table carries bad=2 with reason=None, so folding it in would force an
excuse onto a non-empty list and contradict AC-RUN32 arm 4 / AC-RUN33 arm 5.
No per-row bad=: PENDING-OLD rows describe a source, not the channel. The
CRAWL-FAILURES row in this same module already prints bad=, so this is one
convention applied to a second face rather than a new field law.

WHICH LINES ARE UNUSABLE (R3018): `bad=<n>` said how many and never which, so
finding one meant opening the side channel and trying lines by hand. Measured
(qa/probe-R3018.log): the numbers were already recoverable in the one pass
read_failures makes - a file with two usable and three unusable lines answers
(2, 3) today, and enumerating the same file yields [(2,'json'),(4,'fields'),
(5,'json')], len == bad; a blank line is skipped and takes no number; an
append-only write never moves an earlier number. Naming lives on a SEPARATE
read-only subcommand (`--pending-old-bad`), never on the one-line contract
(R3010/R3013) and never inside PENDING-OLD rows (R3014's boundary: those rows
describe a source). The TEXT IS NOT ECHOED on purpose: a rejected line is
untrusted bytes and can carry a url with a token (measured in the probe), so a
line number plus the reason (json = the line did not parse, fields = it parsed
but is not a usable failure row) is what a person needs to open it in an
editor. `_failure_lines` is the one parse law: bad's count and the named lines
cannot come from two parsers.

THE SAME BLIND SPOT ON THE OTHER FILE (R3019): `CRAWL-FAILURE-DAYS` prints
bad=<n> for the daily history, and nothing could name one. Measured
(qa/probe-R3019.log) before changing anything: read_failure_days carried its OWN
loop - it did not use _failure_lines, had no numbering, and no day-bad reader
existed (day_bad_naming_symbols=[]). Numbering would have been the same law
anyway (blank lines skip and take no number; the non-blank physical count equals
rows+bad on an interleaved file), so the two loops were unified into
_json_lines(path, kind_of_row) and each file supplies its own rejection
taxonomy. They are NOT the same taxonomy and are not forced into one: the side
channel answers json|fields, while the history has FOUR measured reject branches
and now names each - shape (the line is not an object), day (day unusable),
on_day (not an integer), json. Collapsing those to one word would have told a
reader to open a line without saying what to repair. The history's bad lines are
ALSO TRANSIENT, measured in the probe: snapshot_failure_day rewrites the file
from validated rows only, so days_bad went 1 -> 0 on the next snapshot, while an
appended side-channel line stays named across later appends (line 2 unchanged).
That is why this face is read-only and prints no advice - naming is useful only
until the next beat rewrites the file. `--pending-old-bad` keeps its shipped
name and header (AC-RUN35 arm 1 pins the text and the name predates the face
being per-file); the new subcommand is `--failure-days-bad`, so each flag names
the file it reads.

DATE LAW: the caller passes fetched_at; this module never invents a day for the
record. qa/crawl_record.py owns validation and the literal-first-ten-chars day.

Stdlib only. ASCII source. No shell.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import crawl_record as CR

BASELINE_DIR = 'qa'
BASELINE_NAME = 'crawl-baselines.json'
FAILURE_DIR = 'qa'
FAILURE_NAME = 'crawl-failures.jsonl'
FAILURE_DAY_DIR = 'qa'
FAILURE_DAY_NAME = 'crawl-failure-days.jsonl'
FAILURE_KINDS = ('timeout', 'http', 'urlerror', 'dns', 'refused', 'other')
# R2999: the denominator of the display-only size_gate percentage. It is the
# group canon's water-table line for a single append-only jsonl
# (cph4/resource-chain.md section 3.4: world/*.jsonl, 100MB), NOT a threshold
# this repository enforces - this checkout's hook has no byte limb at all.
SIZE_REFERENCE_BYTES = 100 * 1024 * 1024
EXCERPT_CHARS = 240
DEFAULT_URL = 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682'
UA = 'Mozilla/5.0 (compatible; BigDomain-Crawl/1.0)'

NOISE_RE = re.compile(r'(?is)<(script|style)\b.*?</\1\s*>')
TAG_RE = re.compile(r'(?s)<[^>]+>')
SPACE_RE = re.compile(r'\s+')


def baseline_path(repo_root):
    """Where the baseline store lives, derived from a repo root."""
    return os.path.join(repo_root, BASELINE_DIR, BASELINE_NAME)


def failure_path(repo_root):
    """Side channel for failed retrievals - deliberately NOT the record path."""
    return os.path.join(repo_root, FAILURE_DIR, FAILURE_NAME)


def failure_day_path(repo_root):
    """Daily failure-count history - a DISPLAY face, never a judgement input."""
    return os.path.join(repo_root, FAILURE_DAY_DIR, FAILURE_DAY_NAME)


def _usable_day(value):
    """True when value starts with a literal YYYY-MM-DD day (the record law)."""
    if not isinstance(value, str) or len(value) < 10:
        return False
    head = value[:10]
    if head[4] != '-' or head[7] != '-':
        return False
    return head[:4].isdigit() and head[5:7].isdigit() and head[8:10].isdigit()


def append_failure(path, source_url, failed_at, error):
    """Append one failure line; refuses a row no reader could use.

    Kept apart from CR.append_record on purpose: a failure must never be able to
    reach the record file, so this writer has its own path and its own fields.
    """
    row = {'source_url': source_url, 'failed_at': failed_at, 'error': error}
    bad = []
    if not isinstance(source_url, str) or not (
            source_url.startswith('http://') or source_url.startswith('https://')):
        bad.append('source_url')
    if not _usable_day(failed_at):
        bad.append('failed_at')
    if not (isinstance(error, str) and error.strip()):
        bad.append('error')
    if bad:
        raise ValueError('crawl failure refused, unusable fields: ' + ','.join(bad))
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    line = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    with open(path, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write(line + '\n')
    return row


def _json_lines(path, kind_of_row):
    """(lineno, why, row) for every non-blank physical line; why None = usable.

    R3019: both jsonl readers carried a copy of this loop, and the history's
    copy had no numbering at all - so "how many lines are unusable" and "which
    line" could only ever answer for the side channel. One generator now, with
    the field check passed in, so blank-line skipping and the physical 1-based
    number are the same law on both files by construction rather than by two
    parsers agreeing today.

    The number is the physical 1-based line as read - blank lines are skipped
    and take no number, and an append-only writer never moves an earlier number
    (measured, qa/probe-R3018.log P3/P9; the interleaved history shape measured
    the same in qa/probe-R3019.log P2).
    """
    if not os.path.isfile(path):
        return
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        for n, line in enumerate(fh, 1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except ValueError:
                yield n, 'json', None
                continue
            why = kind_of_row(row)
            if why:
                yield n, why, None
                continue
            yield n, None, row


def _failure_row_why(row):
    """Why a parsed side-channel line is not a usable row, or None if it is."""
    if (not isinstance(row, dict) or not _usable_day(row.get('failed_at'))
            or not str(row.get('error') or '').strip()):
        return 'fields'
    return None


def _failure_day_row_why(row):
    """Why a parsed history line is not a usable day row, or None if it is.

    R3019: four measured reject branches, each named rather than collapsed into
    the side channel's 'fields'. A reader told only "fields" still has to open
    the line and guess which of four repairs it needs; the reason is the point
    of naming a line at all.
    """
    if not isinstance(row, dict):
        return 'shape'
    if not _usable_day(row.get('day')):
        return 'day'
    if not isinstance(row.get('on_day'), int):
        return 'on_day'
    return None


def _failure_lines(path):
    """(lineno, kind, row) for the failure side channel; kind None = usable.

    R3018: the count (`bad`) and the identities must come from ONE parse pass,
    so a face that names bad lines cannot disagree with the header count. The
    pass itself is _json_lines (R3019), shared with the daily history so the two
    files cannot drift about blank lines or numbering.
    """
    return _json_lines(path, _failure_row_why)


def read_failures(path):
    """(rows, bad): usable failure rows, plus the count of unusable ones.

    Absence is zero rows, not an error - the same law as CR.read_records, so a
    reader can ask "what failed?" without a prior write. Both numbers come from
    _failure_lines, the one parse law (R3018).
    """
    rows = []
    bad = 0
    for _n, kind, row in _failure_lines(path):
        if kind is None:
            rows.append(row)
        else:
            bad += 1
    return rows, bad


def read_failure_bad_lines(path):
    """[{'line': n, 'why': 'json'|'fields'}] for unusable lines, ascending.

    WHY (R3018, measured before this existed - qa/probe-R3018.log): `bad=<n>`
    told a reader HOW MANY lines were unusable and never WHICH, so the only way
    to find one was to open the side channel and try each line by hand. The
    numbers were already recoverable in the single pass read_failures makes.

    TEXT IS NOT ECHOED, deliberately: an unusable line is text json.loads or the
    field check already rejected, and it can carry query strings from a failed
    fetch (measured: a probe line held a url with a token). Echoing it would put
    untrusted bytes on a screen; a line number plus the reason is what a person
    needs to look at it in an editor.

    DISPLAY ONLY: writes nothing, gates nothing, retries nothing. An absent file
    answers an empty list - the same "absence is zero" law as read_failures.
    """
    return [{'line': n, 'why': kind} for n, kind, _row in _failure_lines(path)
            if kind is not None]


def _window_start(day, window_days=7):
    """(head_day, usable, threshold) - the ONE place the window law lives.

    R3014: the summary and the trend builder each carried this arithmetic, and a
    third face (the old-waiter listing) would have made three copies of the law.
    One function, three call sites, so a list and a row cannot disagree about
    which day the window opens.
    """
    head_day = (day or '')[:10]
    usable = _usable_day(head_day)
    threshold = head_day
    if usable:
        try:
            start = datetime.date.fromisoformat(head_day) - datetime.timedelta(
                days=max(1, int(window_days)) - 1)
            threshold = start.isoformat()
        except ValueError:
            usable = False
    return head_day, usable, threshold


def _summary_from_rows(rows, bad, day, window_days=7):
    """Counts over already-validated rows; the one place the window law lives."""
    head_day, usable, threshold = _window_start(day, window_days)
    recent = 0
    urls = set()
    newest = None
    for row in rows:
        urls.add(row.get('source_url'))
        row_day = str(row.get('failed_at') or '')[:10]
        if usable and threshold <= row_day <= head_day:
            recent += 1
        if newest is None or str(row.get('failed_at') or '') > str(
                newest.get('failed_at') or ''):
            newest = row
    newest_error = (newest or {}).get('error')
    return {'total': len(rows), 'recent': recent, 'bad': bad,
            'urls': len(urls), 'window_days': window_days,
            'newest_at': (newest or {}).get('failed_at'),
            'newest_error': newest_error,
            # R2997: the same bucket function the trend line uses, so one
            # error string is classified in exactly one place.
            'newest_kind': failure_kind(newest_error) if newest_error else 'none'}


def failure_file_stats(path):
    """(present, bytes, lines) for one failure file; absence is 0/0, not a raise.

    WHY (R2999): the retention exemption argued with numbers nobody could check
    from the product. bytes is the file's own size on disk; lines counts every
    physical row splitlines() sees, so a malformed row and a blank row are both
    visible - which is what makes `lines - (total+bad)` a real cross-check of
    the reader rather than a restatement of its own count. A file that exists
    but cannot be opened keeps its measured bytes and answers lines=0: the size
    is a fact either way, and this is a reader, not a gate.
    """
    try:
        size = os.path.getsize(path)
    except OSError:
        return {'present': False, 'bytes': 0, 'lines': 0}
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            text = fh.read()
    except OSError:
        return {'present': True, 'bytes': size, 'lines': 0}
    return {'present': True, 'bytes': size, 'lines': len(text.splitlines())}


def size_gate_pct(nbytes):
    """bytes as a percentage of SIZE_REFERENCE_BYTES - DISPLAY ONLY (R2999).

    Nothing compares this number to 100 to decide anything: the value exists so
    a reader of one line can see how far the file sits from the water line the
    group canon states, instead of trusting a figure written in a header once.
    """
    return round(float(nbytes) * 100.0 / SIZE_REFERENCE_BYTES, 4)


def summarize_failures(path, day, window_days=7):
    """Readable answer to "did retrievals fail, and how recently?" (R2993).

    WHY: the side channel had a writer and NO reader outside its own suite, so
    evidence nobody opens is the same weight as no evidence. This turns the rows
    read_failures already validates into the one line a person can act on: how
    many failures in total, how many inside the window, how many unusable lines,
    how many distinct sources, and the newest failure. An absent file is zeroes,
    never an exception - "nothing failed" is an honest answer, not an error.

    The window is inclusive of `day` and `window_days` long, compared on the
    literal first ten characters of failed_at, the same day law the record face
    uses, so the summary and the writer cannot drift apart. Nothing here gates,
    retries or pages: this is a READER over evidence, not enforcement.
    """
    rows, bad = read_failures(path)
    out = _summary_from_rows(rows, bad, day, window_days)
    # R2999: the body of the file, so the retention exemption can be checked
    # from the product instead of from a number written in a header once.
    stats = failure_file_stats(path)
    out['present'] = stats['present']
    out['bytes'] = stats['bytes']
    out['lines'] = stats['lines']
    out['size_gate'] = size_gate_pct(stats['bytes'])
    out['gate_ref_mb'] = SIZE_REFERENCE_BYTES // (1024 * 1024)
    return out


def read_failure_days(path):
    """(rows, bad) for the daily history; a missing file is zero rows.

    R3019: this used to carry its own loop. It now delegates to _json_lines with
    the history's own field check, so its `bad` count and the lines named by
    read_failure_day_bad_lines come from one pass (the same law the side channel
    follows since R3018) instead of two parsers that could drift.
    """
    rows = []
    bad = 0
    for _n, why, row in _json_lines(path, _failure_day_row_why):
        if why is None:
            rows.append(row)
        else:
            bad += 1
    return rows, bad


def read_failure_day_bad_lines(path):
    """[{'line': n, 'why': 'json'|'shape'|'day'|'on_day'}] ascending.

    WHY (R3019, measured before this existed - qa/probe-R3019.log):
    `CRAWL-FAILURE-DAYS` prints bad=<n> for this file and nothing could name one
    - the same blind spot R3018 closed on the side channel, still open here.

    NAMED, NOT ECHOED, for the same reason as the side channel: a rejected line
    is text the reader already refused and may carry untrusted bytes. A line
    number plus which field failed is what a person needs in an editor.

    TRANSIENT BY NATURE, stated rather than implied: snapshot_failure_day
    rewrites this file from validated rows only, so the next beat drops every
    bad line (measured, qa/probe-R3019.log P4: bad 1 -> 0 across one snapshot).
    The listing is therefore read-only with no advice and no retry - it does not
    outlive the beat and does not pretend to.

    DISPLAY ONLY: writes nothing, gates nothing. An absent file answers [].
    """
    return [{'line': n, 'why': why}
            for n, why, _row in _json_lines(path, _failure_day_row_why)
            if why is not None]


def snapshot_failure_day(repo_root, day, window_days=7):
    """Persist today's failure counts as ONE row, replacing that day's own row.

    WHY (R2994): --failures answers "what is on disk now" and forgets the last
    time it was asked, so a page failing three days straight and one bad
    afternoon read the same. This writes the window counts down once per day so
    two days can be compared. Same-day re-runs REWRITE the row rather than
    appending: the beat fires every ten minutes, and a file that grows a row per
    beat would be noise rather than history. Only the days somebody actually
    snapshotted appear - a gap is an honest gap, not a zero.

    R3020: the row now also carries `dropped=` - unusable lines of THIS file
    that a rewrite discarded, accumulated over the same day's rewrites. It is a
    different fact from `bad=`, which counts the SIDE channel's unusable lines
    (measured: healthy side channel + dirty history writes bad=0 while four
    lines are eaten), and it is accumulated rather than per-rewrite because a
    per-rewrite number would be overwritten by the next ten-minute beat before
    it could be read. Old rows keep whatever they had - no backfill.
    """
    head_day = (day or '')[:10]
    if not _usable_day(head_day):
        raise ValueError('crawl failure day refused, unusable day: %r' % (day,))
    rows, bad = read_failures(failure_path(repo_root))
    summary = _summary_from_rows(rows, bad, head_day, window_days)
    on_day = 0
    for row in rows:
        if str(row.get('failed_at') or '')[:10] == head_day:
            on_day += 1
    row = {'day': head_day, 'on_day': on_day, 'total': summary['total'],
           'recent': summary['recent'], 'bad': summary['bad'],
           'urls': summary['urls'], 'newest_at': summary['newest_at'],
           'newest_error': summary['newest_error']}
    path = failure_day_path(repo_root)
    history, eaten = read_failure_days(path)
    # R3020: `eaten` is what this rewrite is about to discard, and until now it
    # was assigned to a name that said so - `_ignored`. The trace of a beat
    # eating evidence existed for one assignment and then vanished. It is NOT
    # the row's `bad`: that number is the SIDE channel's unusable count
    # (measured, qa/probe-R3020.log P3: a healthy side channel over a four-line
    # dirty history writes bad=0 while the rewrite eats 4 lines), so the same
    # word would have made two different facts read alike.
    #
    # ACCUMULATED into the day's own row, not reported per rewrite: the beat
    # rewrites this row every ten minutes, so a per-rewrite number would be
    # replaced by 0 before anyone could read it - the same transience R3019
    # measured for bad-line numbering. A blank line is dropped too and takes no
    # number here, the law _json_lines already follows. Rows written before
    # this field existed are NEVER backfilled: their drops were not measured,
    # and 0 would be an invented number rather than an answer.
    carry = 0
    for prior in history:
        if prior.get('day') == head_day:
            val = prior.get('dropped')
            if isinstance(val, int) and val > carry:
                carry = val
    row['dropped'] = carry + eaten
    kept = [r for r in history if r.get('day') != head_day]
    kept.append(row)
    kept.sort(key=lambda r: str(r.get('day') or ''))
    tmp = path + '.tmp'
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
        for item in kept:
            fh.write(json.dumps(item, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n')
    os.replace(tmp, path)
    return row


def summarize_failure_days(path, limit=7, read=None, series_days=None):
    """Readable series over the daily history; zero rows is an honest answer.

    R3000: the series answers "which days were how bad" and the retention
    exemption answers "how big does this get", but the second had no product
    face - the header's "~38.1KB per year" was arithmetic a reader had to take
    on faith for THIS file (the side channel got its own size face at R2999).
    bytes is therefore the file's own body, measured with the same helper the
    side channel uses, so the two faces cannot disagree about a file's size.

    WHY NO `lines`: measured (R3000 probe, disclosed in the board PIN) - a
    same-day beat REWRITES the history through snapshot_failure_day, which
    keeps only validated rows, so malformed and blank rows are dropped and the
    physical line count equals days on every live checkout. A field whose value
    can only restate another field on the same line is noise, so only bytes is
    printed here; the reader can still see bad= for the transient case. The
    retained tail (limit=) is a separate matter: bytes covers the WHOLE file,
    not the printed tail, which is what makes it comparable to the water line.

    R3021: `dropped` is the LAST row's own value - the row `last` names - and
    None when that row predates the field, so a reader can tell "nothing was
    eaten" (0) from "never measured" (None). It is computed from the same single
    read that produced `days`/`last`, and it is deliberately NOT a sum over
    rows: older rows carry no key and summing would print unmeasured as zero.
    Attribution of an eaten line to its OWN day is not derivable without parsing
    refused text (module header, qa/probe-R3021.log).

    R3025: `read` lets a caller that has already read the file hand the same
    `(rows, bad)` in, so the header and the series window counts cannot be
    computed from two reads that might see different files.

    R3026: `series_days` selects the printed pairs by a DAY window instead of a
    row tail, through series_days_window(). The row limit still caps how many
    pairs print - two separate quantities, two separate words - and the
    selection travels as `series_counts` so the header cannot recount it
    differently. Left None (the default), the tail law is untouched.
    """
    rows, bad = read_failure_days(path) if read is None else read
    counts = None
    if series_days is None:
        tail = rows[-max(1, int(limit)):]
        series = [(r.get('day'), r.get('on_day')) for r in tail]
    else:
        selection = series_days_window(rows, limit, series_days)
        series = selection['rows']
        counts = {key: selection[key] for key in
                  ('limit', 'shown', 'outside', 'window_rows')}
    out = {'days': len(rows), 'bad': bad,
           'first': (rows[0].get('day') if rows else None),
           'last': (rows[-1].get('day') if rows else None),
           'dropped': None,
           'series': series}
    if counts is not None:
        out['series_counts'] = counts
    if rows:
        last_dropped = rows[-1].get('dropped')
        # type() not isinstance(): a JSON true would pass isinstance(x, int).
        if type(last_dropped) is int:
            out['dropped'] = last_dropped
    stats = failure_file_stats(path)
    out['present'] = stats['present']
    out['bytes'] = stats['bytes']
    out['size_gate'] = size_gate_pct(stats['bytes'])
    out['gate_ref_mb'] = SIZE_REFERENCE_BYTES // (1024 * 1024)
    return out


def series_window_counts(rows, limit=7, window_days=7):
    """{limit, shown, outside, window_rows} for the printed DAYS series (R3025).

    WHY: `--days` is a ROW limit here (`rows[-limit:]`) and a DAY window on the
    failure face, so the header could print a day far outside the window while
    saying nothing, and could print fewer rows than the window holds while
    saying nothing either (measured both ways, qa/probe-R3025.log). The tail
    itself is NOT changed - its shape has a printer and five shape arms - so
    the two laws are named on the same line instead.

    head is the file's OWN newest usable row, so an old history windows against
    itself, two runs on one file agree, and no clock is read. When the head day
    is unusable (empty history) nothing can be measured, so outside and
    window_rows are 0 rather than an invented window.

    DISPLAY ONLY: writes nothing, gates nothing.
    """
    size = max(1, int(limit))
    shown = len(rows[-size:])
    head_day, usable, threshold = _window_start(
        (str(rows[-1].get('day') or '') if rows else ''), window_days)
    outside = 0
    window_rows = 0
    if usable:
        for row in rows[-size:]:
            if str(row.get('day') or '')[:10] < threshold:
                outside += 1
        for row in rows:
            row_day = str(row.get('day') or '')[:10]
            if threshold <= row_day <= head_day:
                window_rows += 1
    return {'limit': size, 'shown': shown, 'outside': outside,
            'window_rows': window_rows}


def series_days_window(rows, limit=7, window_days=7):
    """{rows, limit, shown, outside, window_rows, window} - series by DAY (R3026).

    WHY: the DAYS series was a ROW tail, so "how bad was each of the last seven
    days" had no answer a person could ask for; counting the tail only works
    when every day has exactly one row (measured both failure directions in
    qa/probe-R3025.log). R3025 named the two quantities on the line; this
    function lets the caller CHOOSE the day window for the pairs themselves.

    TWO QUANTITIES, NOT ONE: window_days picks which rows qualify, `limit` caps
    how many of them print (the same --days limit the tail has always used).
    The order of operations is fixed - window first, then the tail of that
    selection - so `window_rows` counts the whole window while `shown` counts
    what printed, and `outside` is 0 by construction: every printed row is
    inside the window now, which is what makes outside=0 the marker that the
    window really applied.

    head is the file's OWN newest usable row (same law as series_window_counts),
    so a 2001 history windows against itself and no clock is read. Rows keep
    file order and duplicates. When the head day is unusable (empty or absent
    history) nothing is measured: rows is empty and the three counts are 0
    rather than an invented window.

    DISPLAY ONLY: writes nothing, gates nothing.
    """
    size = max(1, int(limit))
    width = max(1, int(window_days))
    head_day, usable, threshold = _window_start(
        (str(rows[-1].get('day') or '') if rows else ''), width)
    if not usable:
        return {'rows': [], 'limit': size, 'shown': 0, 'outside': 0,
                'window_rows': 0, 'window': width}
    inside = [r for r in rows
              if threshold <= str(r.get('day') or '')[:10] <= head_day]
    tail = inside[-size:]
    return {'rows': [(r.get('day'), r.get('on_day')) for r in tail],
            'limit': size, 'shown': len(tail), 'outside': 0,
            'window_rows': len(inside), 'window': width}


# One month of silent days is named; a wider window names its first month and
# counts the rest. Measured (qa/probe-R3032.log): the name list costs exactly
# 11.00 bytes per day, so an uncapped list grows linearly without bound (a
# 365-day window over one real row printed 364 names on one 4310-byte line).
ABSENT_LIST_LIMIT = 31


def parse_absent_limit(value):
    """(limit, why) for --series-absent-limit; why is None when usable.

    R3033: the cap answers "a month of silent days", and a reader who wants the
    rest must be able to ASK for it on the same face. The accepted spellings are
    `all` (no cap) and a positive integer (cap at N). Anything else is refused
    with a reason instead of being coerced: a negative or zero cap would print
    an empty list beside a non-zero `series_absent=`, which reads exactly like
    "there are no silent days" - the absent-not-zero law this whole face exists
    to keep. Unset (None) is not an error: the caller applies the default cap.

    A pure function so the refusal branches are measurable without a process.
    """
    if value is None:
        return ABSENT_LIST_LIMIT, None
    text = str(value).strip().lower()
    if text == 'all':
        return None, None
    try:
        number = int(text)
    except (TypeError, ValueError):
        return None, 'expected all or a positive integer, got %r' % (value,)
    if number <= 0:
        return None, 'the cap must be positive (or all), got %d' % number
    return number, None


def series_absent_days(rows, window_days=7, limit=ABSENT_LIST_LIMIT):
    """{days, count, head, window, named, truncated} - calendar days the window
    never saw (R3027).

    WHY (measured before this existed - qa/probe-R3027.log): a day window could
    be asked for, but a day with NO row was simply missing from the series
    rather than named, so "the last seven days" printing three pairs left the
    reader unable to tell four quiet days from four unrecorded ones. The one
    word the repo already uses for that is `absent` (the trend face reads a day
    nobody snapshotted as today='absent'), so the gap gets a name instead of a
    fabricated 0 - a measured zero already prints as :0 in the pairs and would
    be indistinguishable (probe P2a).

    TWO FACES, NOT ONE: the pairs keep their (day, on_day) shape untouched
    (five arms assert a 2-tuple and the header joins pairs with %s:%s), so the
    gaps travel as their OWN token rather than as pairs with a word where a
    number belongs (probe P3a/P3b).

    LAW: the window is the same inclusive literal-day range the other faces use
    (`_window_start`), measured back from the file's OWN newest usable row, so a
    2001 history windows against itself and no clock is read. `days` lists the
    first `limit` calendar days in that range that hold no row, ascending (the
    cap is R3032, below); duplicates on a day that DOES have rows never create a
    gap (probe P1c). When the head day is
    unusable nothing is measurable, so count is None and days is empty rather
    than a zero that would read like "every day was recorded".

    DISPLAY ONLY: writes nothing, gates nothing.

    THE NAME LIST IS CAPPED, THE COUNT IS NOT (R3032, measured first -
    qa/probe-R3032.log): the list used to grow with the window - one name per
    silent day, 11.00 measured bytes each, so this checkout's one-row history
    printed 364 day names on a single 4310-byte line at width 365. The cap is
    on NAMES rather than whole-line bytes, because a byte budget is not a law a
    reader can predict from the window while "the first N silent days" is.
    `count` stays the FULL total under any truncation (a short list must never
    read as few gaps, the R2994 absent-not-zero law); `named` is how many of
    them this call returned and `truncated` says whether that is fewer. An
    unusable head day answers count None and an empty list, never a fabricated
    zero.

    R3033: the caller may pass another cap, or None for the full list (the CLI
    spellings are `<N>` and `all`, opt-in only, default ABSENT_LIST_LIMIT) -
    measured qa/probe-R3033.log shows the truncated names are otherwise only
    recoverable by subtracting a different subcommand's row listing.
    """
    width = max(1, int(window_days))
    head_day, usable, threshold = _window_start(
        (str(rows[-1].get('day') or '') if rows else ''), width)
    if not usable:
        return {'days': [], 'count': None, 'head': None, 'window': width,
                'named': 0, 'truncated': False}
    seen = set()
    for row in rows:
        row_day = str(row.get('day') or '')[:10]
        if threshold <= row_day <= head_day:
            seen.add(row_day)
    days = []
    cursor = datetime.date.fromisoformat(threshold)
    last = datetime.date.fromisoformat(head_day)
    while cursor <= last:
        key = cursor.isoformat()
        if key not in seen:
            days.append(key)
        cursor += datetime.timedelta(days=1)
    named = days if limit is None else days[:max(0, int(limit))]
    return {'days': named, 'count': len(days), 'head': head_day,
            'window': width, 'named': len(named),
            'truncated': len(named) < len(days)}


def series_presence_counts(rows, window_days=7):
    """{window, present, rows, repeat, head} - how many of the window's DAYS
    hold a row, and how many of its rows are repeats (R3028/R3029).

    WHY (measured before this existed - qa/probe-R3028.log): R3027 named the
    silent days one by one, but "how many of the last seven days have a record
    at all" still had to be counted off the commas in `absent=`, and
    `window_rows=` cannot answer it - a day holding three rows prints three
    (measured: world A holds four rows on two days inside a seven-day window).

    LAW: the window is the same inclusive literal-day range the other faces use
    (`_window_start`), measured back from the file's OWN newest usable row, so a
    2001 history windows against itself and no clock is read. `present` counts
    DISTINCT calendar days that hold at least one row; `rows` counts rows, so
    the two differ exactly when a day repeats. `present` plus the gap count from
    series_absent_days() equals `window` - one invariant, two faces, and neither
    restates the other's number (a `window_days=` token would only repeat
    `series_window=`).

    When the head day is unusable nothing is measurable: present is None and
    rows is 0 rather than a zero that would read like "nothing was recorded"
    (the R2994 absent-not-zero law, carried).

    THE DIFFERENCE HAS A NAME (R3029, measured first - qa/probe-R3029.log):
    present and rows could be read side by side and still left "who is bigger,
    and why" as a subtraction the reader performs - four rows on two days
    prints 4 beside 2 with nothing saying the extra two are the SAME days
    again. `repeat` is that difference: rows inside the window beyond the first
    on each day that holds at least one, so `present + repeat = rows` and
    `present + gap = window` are both checkable by eye. It is a subtraction of
    two numbers already printed, stated as such: the value is not a new
    measurement but the only printed face of "how many rows are second-and-
    later on a day already counted", and it is not a restatement of any other
    token (the R3000 noise law refused `window_days=` because it would repeat
    `series_window=`; this number appears nowhere else).

    A REPEAT IS NOT ONE THING (R3030, measured first - qa/probe-R3030.log):
    `repeat` counts same-day second-and-later rows, but the history can hold
    them for two different reasons - a re-recording of a day whose evidence had
    not grown, and a later reading of a day that grew between writes. `on_day`
    is the number of that day's failure rows at write time (it starts at 0 and
    increments once per side-channel row dated that day - it is a count, not a
    clock), so a repeated row whose on_day is NOT greater than the previous row
    of the SAME day carried no more evidence than that row. `retry` counts
    exactly those, and `retry <= repeat` holds by construction; the remainder
    are rows that grew. An equal on_day counts as a re-recording.

    HONEST BOUNDARY: `retry` is an INFERENCE, not proof - a non-increasing
    on_day says this row did not carry more failure evidence than the row
    before it, not that a process was interrupted, and a pruned side channel
    also fails to grow. A `reading_rows=` token was refused as a restatement of
    the difference between two printed numbers (the R3000 noise law).

    WINDS NOTHING BY DAY (R3031): the window is a day-keyed filter - a row is
    in or out by its own date - so a calendar day can never be split by the
    edge, and `repeat`/`retry` are EXACT for the window rather than lower
    bounds (measured over every width 1..10, qa/probe-R3031.log). `start` is the
    threshold the one window law applied, so the printed `window_from=` lets a
    reader name the first day of the window instead of counting backwards from
    the newest pair; an unusable head day answers `start` None rather than a
    date nobody measured (the absent-not-zero law, carried).

    DISPLAY ONLY: writes nothing, gates nothing.
    """
    width = max(1, int(window_days))
    head_day, usable, threshold = _window_start(
        (str(rows[-1].get('day') or '') if rows else ''), width)
    if not usable:
        return {'window': width, 'present': None, 'rows': 0, 'repeat': None,
                'retry': None, 'head': None, 'start': None}
    days = set()
    count = 0
    seen_on_day = {}
    retry = 0
    for row in rows:
        row_day = str(row.get('day') or '')[:10]
        if threshold <= row_day <= head_day:
            count += 1
            days.add(row_day)
            on_day = row.get('on_day')
            if row_day in seen_on_day and on_day <= seen_on_day[row_day]:
                retry += 1
            seen_on_day[row_day] = on_day
    return {'window': width, 'present': len(days), 'rows': count,
            'repeat': count - len(days), 'retry': retry, 'head': head_day,
            'start': threshold}


def list_failure_days_dropped(path, window_days=None):
    """Per-day eaten-lines listing; each row speaks only for itself.

    WHY (R3023, measured before this existed - qa/probe-R3023.log): R3021
    handed the LAST row's value to the DAYS header, so any earlier day's count
    could only be read by opening the jsonl. The DAYS face prints exactly one
    line (P3a), so the list lives in its own subcommand instead of on that
    header, and the series/trend shapes stay untouched (P3b/P3c).

    ROWS KEEP FILE ORDER AND DUPLICATES: measured (P2e) a history can hold the
    same day twice, and sorting or de-duplicating would hide one of them
    rather than report it. `bad` comes from the same single read that produced
    the rows, so the listing cannot disagree with the header about how many
    lines were refused.

    dropped is the row's OWN value; None when the row predates the field or
    carries a non-int - type() not isinstance(), because a JSON true passes
    isinstance(x, int). No sum, no maximum, no backfill: R3020/R3022 refused
    summing a key older rows do not carry, and 0 would be an invented number.

    R3024 WINDOW (opt-in, default None): the listing had no window, so it grew
    with the file. With `window_days` set, the head day is the file's OWN last
    usable row (data-derived - no clock, so two runs on the same file agree and
    an old history windows against itself), the threshold comes from the one
    window law `_window_start`, and rows older than it are COUNTED into
    `hidden` rather than dropped silently. `days` keeps its own meaning (usable
    rows in the file); `shown` is what this call returns. `truncated` is a
    boolean and `hidden` an int, so a truncated listing can never read like a
    short file. No sort, no de-duplication: a same day twice stays twice.

    DISPLAY ONLY: writes nothing, gates nothing. An absent file answers zero
    rows - the same "absence is zero" law as read_failure_days.
    """
    rows, bad = read_failure_days(path)
    listing = {'days': len(rows), 'bad': bad,
               'rows': [{'day': r.get('day'),
                         'dropped': (r.get('dropped')
                                     if type(r.get('dropped')) is int else None)}
                        for r in rows]}
    if window_days is None:
        return listing
    head = str(rows[-1].get('day') or '') if rows else ''
    head_day, usable, threshold = _window_start(head, window_days)
    if usable:
        kept = [r for r in listing['rows']
                if str(r.get('day') or '')[:10] >= threshold]
    else:
        # No usable head day (empty file): nothing can be windowed, and
        # claiming a window opened would invent a measurement.
        kept = []
    listing['window'] = window_days
    listing['head'] = head_day or None
    listing['shown'] = len(kept)
    listing['truncated'] = len(kept) < len(listing['rows'])
    listing['hidden'] = len(listing['rows']) - len(kept)
    listing['rows'] = kept
    return listing


def failure_kind(error):
    """Coarse bucket for one failure's exception CLASS - a label, not a cause.

    WHY (R2996): the trend could count failures but not say what KIND they
    were, so "TimeoutError" and "HTTPError" were the same event on the line.
    The writer's own shape is the input law - run() stores
    'E_FETCH <ExceptionType>: <msg>' - so only the class token is read. The
    message body is never inspected, which is what keeps this a DISPLAY label:
    two sources failing with one class are still two unexplained failures, and
    no reader may turn this into a verdict.
    """
    text = str(error or '').strip()
    if not text:
        return 'other'
    head = text
    if head.startswith('E_FETCH'):
        head = head[len('E_FETCH'):].lstrip()
    token = head.split(':', 1)[0].strip().lower()
    if 'timeout' in token:
        return 'timeout'
    if 'http' in token:
        return 'http'
    if 'url' in token:
        return 'urlerror'
    if 'dns' in token or 'gaierror' in token:
        return 'dns'
    if 'refused' in token or 'connect' in token:
        return 'refused'
    return 'other'


def _since_ok(record_path, source_url, failed_at):
    """yes / no / unmeasured for "was this source seen succeeding afterwards?"

    WHY (R3001): "did it ever come back" had no face. The crawl record is the
    only file that stores a SUCCESS (a failed retrieval never reaches it), so a
    row for the same source with a LATER stamp is the honest evidence that a
    retrieval succeeded after the failure. UNMEASURED, not 'no': no record file,
    no source identity, or no timestamp means the question was not answered -
    answering 'no' there would claim the source is still broken from evidence
    that never arrived.

    The comparison is LITERAL ISO text on both sides, because every writer on
    this machine stamps astimezone().isoformat() (same clock, same zone). This
    is stated rather than parsed: a corpus written in a different zone is
    outside what this arm promises.

    R3004 - 'no' NOW REQUIRES THE RECORD TO BE SHOWN LOOKING AFTER THE FAILURE.
    Measured before this changed: a zero-byte record, a record whose newest row
    predates the failure, and a success stamped in the same second as the
    failure all answered 'no', so "we looked and it is still broken" and "we
    never looked" printed the same verdict, with flips=0 (a count of zero
    observations) sitting beside it as if it were evidence. The record must now
    reach STRICTLY past the failure stamp - any source, because the pipeline
    fetching another page afterwards is what proves the pipeline ran - before
    'no' may be said. Until then the honest answer is 'unmeasured'. Strictness
    is the rule flips already used: an equal stamp cannot be ordered by these
    writers, so it does not count as looking afterwards.

    flips deliberately does NOT follow this. Every flip it counts is a pair of
    events already on disk, so a record that stops before the newest failure
    still yields a measured count. since_ok asks "is it fixed now"; flips asks
    "how often did it break after working" - different measurability, stated in
    both docstrings rather than left to be inferred.
    """
    if not source_url or not record_path or not os.path.isfile(record_path):
        return 'unmeasured'
    stamp = str(failed_at or '')
    if not stamp:
        return 'unmeasured'
    rows, _bad = CR.read_records(record_path)
    newest = ''
    for row in rows:
        got = str(row.get('fetched_at') or '')
        if got > newest:
            newest = got
    if not newest or newest <= stamp:
        return 'unmeasured'
    for row in rows:
        if row.get('source_url') != source_url:
            continue
        if str(row.get('fetched_at') or '') > stamp:
            return 'yes'
    return 'no'


def _flips(record_path, source_url, failures):
    """success -> failure transitions for ONE source, or None when unmeasured.

    WHY (R3002): measured before this existed - fail,ok (a stable repair) and
    fail,ok,fail,ok (fixed, broken again, fixed again) both printed since_ok=yes
    with recur=(0,0), so "fixed" and "fixed but flapping" were the same row. This
    counts the second question on the merged timeline of the two record faces
    that already exist; it never merges or rewrites them.

    UNMEASURED, not zero, without a record file or a source identity. R3004
    splits this from _since_ok on purpose: since_ok asks "is it fixed NOW" and
    therefore needs an observation AFTER the newest failure, while every flip
    counted here is a pair of events already on disk - so a record that stops
    before the newest failure still answers a measured count, and the two fields
    may legitimately disagree (since_ok=unmeasured beside flips=1). A record
    file that exists but carries no row for this source answers 0: it was never
    seen working in between, which is measured rather than missing. A trimmed
    record can undercount, the same honest boundary since_ok='no' already
    carried.

    A transition needs the failure to be STRICTLY later than the success before
    it; an equal stamp cannot be ordered by these writers, so ties are not
    invented into a flip (failures sort first at an equal stamp, which leaves
    the state working). Counted over every row on disk for the source, not
    window-trimmed - cov already reports how much history the answer rested on.
    """
    if not source_url or not record_path or not os.path.isfile(record_path):
        return None
    rows, _bad = CR.read_records(record_path)
    events = []
    for row in rows:
        if row.get('source_url') != source_url:
            continue
        stamp = str(row.get('fetched_at') or '')
        if stamp:
            events.append((stamp, 1))  # a record row is a success
    for row in failures or ():
        if row.get('source_url') != source_url:
            continue
        stamp = str(row.get('failed_at') or '')
        if stamp:
            events.append((stamp, 0))  # failures sort first at an equal stamp
    events.sort()
    flips = 0
    working = False
    for _stamp, kind in events:
        if kind == 1:
            working = True
        elif working:
            flips += 1
            working = False
    return flips


def _record_coverage(record_path):
    """(first_day, last_day) the crawl record actually reaches, or None.

    WHY (R3003): since_ok answers "was this source seen working afterwards?" by
    finding no later row - but no later row is also what a record that stopped
    being written yesterday produces, so "still broken" and "never observed"
    printed the same verdict. This is the reach of the evidence, printed beside
    the verdict it supports, not a new verdict.

    DAY granularity on purpose: the first ten characters the record writer
    already owns, deduplicated and sorted. An absent file and a file with zero
    usable rows both answer None - "no coverage measured" - because a span built
    from no rows would be invented. Malformed lines never widen the span:
    read_records already drops them and counts them bad.
    """
    if not record_path or not os.path.isfile(record_path):
        return None
    rows, _bad = CR.read_records(record_path)
    days = sorted({str(row.get('fetched_at') or '')[:10] for row in rows
                   if str(row.get('fetched_at') or '')})
    return (days[0], days[-1]) if days else None


def _side_coverage_rows(rows):
    """(first_day, last_day) over ALREADY-VALIDATED failure rows, or None.

    R3015: the span now has two callers - the trend row reads the file itself,
    the old-waiter list has the rows in hand. Both go through this one function,
    so a header and a row cannot describe the same file differently. MEASURED
    why the list must NOT re-read: the file was read, a row was appended, and a
    second read returned a later last day than the rows the list had judged -
    within one call, the header would have claimed evidence the list never saw.

    None - never an invented span - when there is no usable row.
    """
    days = sorted({str(row.get('failed_at') or '')[:10] for row in rows
                   if str(row.get('failed_at') or '')})
    return (days[0], days[-1]) if days else None


def _last_stamp_rows(rows):
    """The newest usable failure stamp among ALREADY-VALIDATED rows, or None.

    R3016: the old-waiter list could say why its table was empty and how far the
    channel reached, but not WHEN the channel was last written. Measured before
    this existed (qa/probe-R3016.log): a channel whose last failure landed at
    00:05 and one whose last failure landed at 23:50 the same day read the SAME
    dictionary and the SAME header, because the span is a pair of DAYS. The
    board's own example (stopped yesterday versus written this minute) had
    already been separated by the day span, so it is measured here and recorded
    rather than claimed as a gain.

    Same rows the list already loaded - never a second read, on the R3015 law
    that a header must not claim evidence this call never judged. None when
    there is no usable row: "no write seen", never a fabricated day.
    """
    stamps = [str(row.get('failed_at') or '') for row in rows
              if str(row.get('failed_at') or '')]
    return max(stamps) if stamps else None


def _stamp_echo(stamp):
    """The writer's own characters, to the minute when the stamp carries one.

    R3016: a literal echo, not a parsed value - the writer stamps
    isoformat(timespec='seconds'), so the first sixteen characters are
    YYYY-MM-DDTHH:MM. A stamp that stops at the date is printed as the date: an
    invented 'T00:00' would claim an hour nobody recorded, which is the same
    family of lie as an invented span.

    No clock is read and no age is subtracted: measured, a day age over this
    stamp is exactly the age of fcov.last day in every probed world, so printing
    it would restate a field already on the same line.
    """
    text = str(stamp or '')
    if (len(text) >= 16 and text[10] == 'T' and text[11:13].isdigit()
            and text[14:16].isdigit()):
        return text[:16]
    return text[:10]


def _side_coverage(failures_path):
    """(first_day, last_day) the failure side channel reaches, or None.

    WHY (R3011): pending_old= counts over this side channel and never said how
    far back the channel itself reaches - measured, a one-day channel and a
    ninety-day channel read identical on all 27 keys when the judged facts
    were the same, so "0 of 1" standing on the window's edge and the same 0 of 1
    standing on three months of history were the same row.

    A DIFFERENT FILE from cov= (the failure-day history), wcov= (that history's
    fill inside the window) and rcov= (the crawl record - successes). This is
    the failure side channel only, which is the evidence pending_old= reads.

    Follows the FILE, not the window: measured, the same channel read the same
    span at window_days 7 and 14 while pending_old= changed. DAY granularity on
    the ten-character prefix the writer owns; read_failures already drops
    malformed rows and unusable stamps, so they cannot widen the span. None -
    never an empty string or ('','') - when the file is absent, empty, or holds
    no usable row: "no reach measured", not a zero-day span.

    R3015: the arithmetic moved to _side_coverage_rows() so a reader holding
    rows does not have to read the file a second time to answer the same
    question.
    """
    if not failures_path or not os.path.isfile(failures_path):
        return None
    rows, _bad = read_failures(failures_path)
    return _side_coverage_rows(rows)


def _day_age(day, stamp):
    """Whole days from `stamp`'s date to `day`, or None.

    WHY (R3007): the row could name WHICH source was still gone but not HOW
    LONG, so a source broken five minutes ago and one broken a week read the
    same. Measured before this existed: the pending source's own stamp was
    computed inside _pending_sources and discarded, and the failure summary's
    newest_at is taken across ALL sources (it named a different source's stamp
    than pending_src in the probe world), so no existing field carried it.

    DAY granularity on purpose, on the same ten-character ISO prefix the record
    writer owns, and no clock: `day` is the caller's window day, so this module
    still reads one. None rather than 0 or a negative number when nothing can
    be said - no named source, an unusable date on either side, or a stamp LATER
    than the reference day (an age cannot be invented from a future failure).
    """
    head = str(day or '')[:10]
    tail = str(stamp or '')[:10]
    if len(head) != 10 or len(tail) != 10:
        return None
    try:
        first = datetime.date.fromisoformat(tail)
        last = datetime.date.fromisoformat(head)
    except ValueError:
        return None
    delta = (last - first).days
    return delta if delta >= 0 else None


def _pending_sources(record_path, in_window):
    """(not back, judged, longest, its stamp, newest stamp, middle stamp).

    WHY (R3005): newest_src/since_ok answer for ONE source - the latest failure
    in the window - so a window with three failing pages said nothing about the
    other two. Measured before this existed: with A repaired, B still gone and C
    still gone, the row named only C (since_ok=no) and A's yes / B's no appeared
    in none of its 22 keys.

    WHAT IT IS NOT: this is not "how many sources are broken". The numerator
    counts only sources whose OWN latest failure the record shows was looked at
    afterwards and never succeeded again (since_ok == 'no'); the denominator
    counts only sources where that judgement could be made at all (yes or no).
    An unmeasured source is in NEITHER number - the R3004 split is a property of
    the verdict, and aggregating it away would revive exactly the conflation
    that round removed: measured, one source whose newest failure is later than
    every record row would be counted as 'pending' by a since_ok != 'yes' rule
    even though nobody ever looked after it.

    Each source is judged on ITS OWN latest failure in the window, not on the
    first one - a source that was repaired yesterday and failed again today is
    today's question, and judging it on the earlier stamp would report a repair
    that the record does not support.

    The caller turns (0, 0) into None: "zero of zero judged" would read like
    "nothing is pending" when the honest statement is "nothing was judged".

    R3006 NAMES ONE OF THEM: the count said how many were still gone, never
    which one, so a person had to guess where to start. The third value is the
    PENDING SOURCE WAITING LONGEST - its own latest failure stamp is the
    smallest among the pending ones, ties broken by url ascending so two
    readers never disagree. None when nothing is pending. It is deliberately
    NOT every pending source: naming them all needs one line per source, which
    the one-line contract refuses. The count stays in pending=<n>/<judged>.

    R3007 KEEPS THE STAMP: the name alone could not say HOW LONG, because the
    stamp was computed here and thrown away, and the failure summary's
    newest_at is taken across ALL sources (measured: it named another source's
    stamp than pending_src's). The fourth value is the named source's OWN
    latest failure stamp, or None - the caller turns it into an age against its
    window day, so this module still reads no clock. The other pending sources
    are not returned: their count is already pending[0]-1 (arithmetic, refused
    as a field) and their names need the per-source lines the contract refuses.

    R3008 KEEPS THE OTHER END: one age described the source waiting LONGEST and
    said nothing about the rest, so with N>1 a person could not tell a burst
    that just started from a long tail - measured, three pending sources aged
    0/2/4 days read pending=(3,3) pending_age_d=4 with the 0-day one absent
    from all 24 keys. The fifth value is the NEWEST pending stamp (the largest
    one): the two ends together are the AGE SPAN of the pending set. A
    pending_age_max_d field was measured and REFUSED - the named source is by
    construction the oldest (raw recomputation agreed in every probe world), so
    the max would restate pending_age_d.     None when nothing is pending; when
    every pending source shares one stamp the two ends coincide, which is
    reported as it is rather than papered over.

    R3009 KEEPS THE MIDDLE: the two ends described the span and left everything
    between them silent - measured, ages 5/3/0 and 5/1/0 were identical on all
    25 keys, and so were 5/5/5/0/0 (mass old) and 5/0/0/0/0 (mass new), which
    is exactly the "burst or tail" question a person asks. The sixth value is
    the MIDDLE pending stamp: the list below is already ordered oldest-first,
    so the middle is index (n-1)//2 - the exact centre when n is odd, the one
    nearer the OLD end when n is even. None when nothing is pending. It is not
    the max refused in R3008: a max equalled the named stamp by construction,
    while the middle only coincides with an end at n<=2 or when the mass piles
    on one end - a coincidence reported as the truth, and the very reading that
    separates the two worlds the ends cannot tell apart.
    """

    latest = {}
    for row in in_window or ():
        src = row.get('source_url')
        stamp = str(row.get('failed_at') or '')
        if not src or not stamp:
            continue
        if src not in latest or stamp > latest[src]:
            latest[src] = stamp
    pending = 0
    judged = 0
    waiting = []
    for src, stamp in latest.items():
        verdict = _since_ok(record_path, src, stamp)
        if verdict == 'no':
            pending += 1
            judged += 1
            waiting.append((stamp, str(src)))
        elif verdict == 'yes':
            judged += 1
    waiting.sort()
    if not waiting:
        return (pending, judged, None, None, None, None)
    return (pending, judged, waiting[0][1], waiting[0][0], waiting[-1][0],
            waiting[(len(waiting) - 1) // 2][0])


def _out_of_window_waiting(record_path, rows, threshold):
    """(still, judged, waiting, old) - the out-of-window population, computed ONCE.

    waiting is [(stamp, src)] for the sources the record shows were never back,
    sorted stamp ascending then url, which is the order the two end values have
    always used. R3014 hoisted this out of _pending_out_of_window because that
    function kept only the first and last witness and dropped everything
    between - and a listing face built on its own copy of the predicate would
    have been a second truth (the measured gap: three waiters, two stamps
    returned, the middle one's identity gone).

    R3015 FOURTH VALUE - `old` counts every distinct source whose OWN latest
    failure fell before the window, judged or not. Measured (qa/probe-R3015.log):
    three empty-table shapes read the same header - an absent channel, a channel
    trimmed to the window, and a channel holding an old row the record never
    looked after - so a reason needs to tell "nothing old was ever recorded"
    from "old rows exist and could not be judged". Counting them here keeps that
    fact on the same `latest` map the population already builds instead of
    letting the list recompute it (a second truth by construction).
    """
    latest = {}
    for row in rows or ():
        src = row.get('source_url')
        stamp = str(row.get('failed_at') or '')
        if not src or not stamp:
            continue
        if src not in latest or stamp > latest[src]:
            latest[src] = stamp
    still = 0
    judged = 0
    old = 0
    waiting = []
    head = str(threshold or '')[:10]
    for src, stamp in latest.items():
        if str(stamp)[:10] >= head:
            continue
        old += 1
        verdict = _since_ok(record_path, src, stamp)
        if verdict == 'no':
            still += 1
            judged += 1
            waiting.append((str(stamp), str(src)))
        elif verdict == 'yes':
            judged += 1
    waiting.sort()
    return still, judged, waiting, old


def _pending_out_of_window(record_path, rows, threshold):
    """(still gone, judged) outside the window - or None when nothing was judged.

    WHY (R3010): the window decides who is counted, so a source whose OWN latest
    failure fell before the window start left the row entirely. Measured before
    this existed: the same side channel read identical on all 26 keys whether
    that source was still broken or had been repaired (only rcov moved, because
    the record gained a row), and a side channel trimmed to the window read
    identical to a healthy world on every key - so "an old tail is still
    hanging" and "it was fixed long ago" were the same row, and deleting the
    evidence looked exactly like a repair.

    WHAT IT IS NOT: not a widening of pending=. That fraction counts sources in
    the window and its denominator is the sources= the same line names; folding
    the old ones in would print more judged sources than that population
    contains (measured: one in-window source, one judged outside, so 2 judged
    over sources=1). Not a field on THIS ROW either: naming or aging every old
    source here needs one line per source, which the one-line contract refuses.
    R3014 later landed exactly that list as a SEPARATE read-only face
    (--pending-old-list), after measuring that this reason - and every arm that
    asserted a refusal - was scoped to this row; this row keeps its shape.

    Same split as pending=: only since_ok=='no' reaches the numerator, so an
    unmeasured source is in neither number (R3004's split is not aggregated
    away). `threshold` is the window's first day, compared on the literal first
    ten characters of the stamp; a source whose latest is inside the window is
    skipped because pending= already owns it.

    None - never (0, 0) - when nothing outside the window could be judged: a
    side channel trimmed to the window, one that never recorded anything older,
    or a record that stops before the old failure all mean "nothing was looked
    at out there" rather than "nothing is pending out there".

    R3012 THIRD VALUE: the third element is the stamp of the still-pending old
    source that has waited LONGEST (earliest own latest failure, ties broken by
    source url so two write orders agree), or None when every judged old source
    came back. It is a stamp, not a name - the row only derives a day age from
    it, and per-source naming stays refused by the one-line contract. Measured
    before this existed (qa/probe-R3012.log): a world whose older failure
    belonged to a REPAIRED source read fcov.first = 2026-08-20 while the source
    still gone had failed on 2026-11-10, so a single age over this population is
    NOT a restatement of fcov.first.

    R3013 FOURTH VALUE: one age described only the longest wait, so with two old
    waiters the other was invisible - measured (qa/probe-R3013.log), a world
    whose second waiter failed 90 days ago and one whose second waiter failed 9
    days ago read IDENTICAL on all 29 keys. A MIDDLE (nearer the old end) reading
    was measured and REFUSED: with two waiters it equals the longest age by
    construction in both worlds, so it would add a digit and no information at
    exactly the count the board named; it only diverges at three or more, and
    reading the shape at that size needs one line per source, which the
    one-line contract refuses. The fourth value is the YOUNGEST still-pending old
    stamp (largest own latest failure, ties broken by source url), the same
    second end the in-window pair already carries in pending_age_min_d. Pointing
    a reader at the failure file instead was measured and refused: with the
    failure file byte-identical, one extra record row proving a source came back
    moved the old fraction from (2,3) to (1,3), so the file cannot answer "is it
    still gone" on its own.
    """
    still, judged, waiting, _old = _out_of_window_waiting(record_path, rows,
                                                          threshold)
    if not judged:
        return None
    return (still, judged, waiting[0][0] if waiting else None,
            waiting[-1][0] if waiting else None)


def list_pending_old(record_path, failures_path, day, window_days=7):
    """The out-of-window still-gone sources BY NAME, one row each (R3014).

    WHY: measured before this existed (qa/probe-R3014.log) - with three old
    waiters the trend row reads pending_old=3/3 with the ends 91 and 9, and two
    worlds whose second-oldest waiter was a DIFFERENT source were identical on
    all 30 keys, so "which ones are hanging" had no face at all. The row keeps
    its shape (R3010/R3013 refusals stand for the row); this is a separate
    surface whose whole purpose is the list.

    SAME SOURCE, NOT A SECOND TRUTH: it calls _out_of_window_waiting(), the
    same predicate _pending_out_of_window uses, over the same loader - so the
    count, the two ages on the row and this list cannot disagree. The suite
    pins that agreement rather than this docstring promising it.

    DISPLAY ONLY: writes nothing, gates nothing, retries nothing. No evidence
    out there answers pending_old=None with an empty list - never (0, 0), which
    would read as "nothing is pending".

    R3015 SAYS WHY THE TABLE IS EMPTY, AND HOW FAR THE EVIDENCE REACHES.
    Measured before this existed (qa/probe-R3015.log): an absent channel, a
    channel trimmed to the window, and a channel holding an old row the record
    never looked after printed the SAME header (pending_old=none, zero rows); a
    reader could not tell "nothing outside was ever recorded" from "we recorded
    it and never looked again". The board guessed two shapes, the measurement
    found three under none (all-repaired was already readable as 0/n), so four
    reasons are named - each one a different human action:
      no-coverage   nothing usable outside the window is on the channel at all
                    (absent file, empty file, or rows that are all in-window)
      unmeasured    old rows exist, but the record never reaches past them
      all-repaired  every judged old source came back (pending_old=(0,n))
      no-window     the day itself is unusable, so no window could be formed
    `reason` is None on a NON-empty list: it answers "why empty", and a list
    with rows needs no excuse. `fcov` is the channel's own span from the rows
    already loaded (R3011's span, one function), so the header and the row
    describe the same file - and a concurrent append cannot make the header
    claim evidence this call never judged (measured: a second read drifted).

    R3016 ADDS `last_at` - WHEN the channel was last written. Measured before
    this existed (qa/probe-R3016.log): a last failure at 00:05 and one at 23:50
    on the SAME day read the same dictionary and the same header, because a span
    is a pair of days; the board's own "stopped yesterday versus written this
    minute" pair had already been separated by that span, which is recorded here
    rather than sold as a gain. `last_at` is the newest usable stamp among the
    rows already loaded, echoed to the minute (never a second read), and None
    when there is no usable row. It is NOT an age: a day age over this stamp was
    measured to equal the age of `fcov`'s last day in every probed world, so it
    would restate a digit on the same line, and an hour age would need a clock
    this module does not read.

    R3017 PRINTS `bad` - HOW MANY LINES ON THE CHANNEL ARE UNUSABLE. Measured
    before this existed (qa/probe-R3017.log): two worlds with the same usable
    rows, one of them carrying two malformed lines, moved `bad` 0 -> 2 while
    fcov, last_at and pending_old stayed identical and the two headers were
    byte-equal - and the strongest shape is the empty table, where a channel
    holding only broken lines read exactly like an absent channel. `bad` comes
    from the ONE read_failures call above (measured: one call per invocation),
    so printing it claims nothing this call did not judge. It is NOT part of
    `reason`: measured, a populated table carries bad=2 with reason None, and
    `reason` answers "why is the table empty" - evidence quality is not
    population, and folding it in would put an excuse on a non-empty list.
    """
    rows, bad = read_failures(failures_path)
    head_day, usable, threshold = _window_start(day, window_days)
    newest = _last_stamp_rows(rows)
    out = {'day': head_day, 'window_days': window_days, 'bad': bad,
           'pending_old': None, 'waiting': [],
           'fcov': _side_coverage_rows(rows),
           'last_at': None if newest is None else _stamp_echo(newest),
           'reason': None}
    if not usable:
        out['reason'] = 'no-window'
        return out
    still, judged, waiting, old = _out_of_window_waiting(record_path, rows,
                                                         threshold)
    if judged:
        out['pending_old'] = (still, judged)
        out['waiting'] = [{'source_url': src, 'failed_at': stamp,
                           'age_d': _day_age(head_day, stamp)}
                          for stamp, src in waiting]
        if not still:
            out['reason'] = 'all-repaired'
    elif old:
        out['reason'] = 'unmeasured'
    else:
        out['reason'] = 'no-coverage'
    return out


def summarize_failure_trend(history_path, failures_path, day, window_days=7,
                            record_path=None):
    """One line for "is today worse than the days before, and is it the same
    page each time?" (R2995).

    WHY: R2994 persisted one row per day, so the numbers were ON DISK - but
    nothing put two of them side by side, a person still compared rows by hand,
    and every row carried only urls=<count>, so one page failing three days
    straight read exactly like three different pages failing once each. This is
    a READER that joins the two faces that already exist: the day history gives
    the count series, the failure side channel gives per-failure source
    identity. Refusing to copy source names into the history row is deliberate -
    one fact stored twice is two places to drift, and the history would start
    looking like a second record face.

    DISPLAY ONLY: the five-still scanner never reads either file, nothing here
    gates, retries or pages, and no verdict changes because of this line.

    LAW: a day nobody snapshotted is ABSENT, not zero (carried from R2994), so
    today answers 'absent' rather than 0 when no row names it - and delta is
    'none' rather than a fabricated drop. recurring counts SOURCES that failed
    on two or more distinct days inside the window: one source failing many
    times on a single day is not a recurrence. The window is the same inclusive
    literal-day range the count summaries use.

    EVIDENCE (R2996): the answer also names WHERE the recurrence/kind facts came
    from, because 'recurring=0 sources=0' read the same whether the side channel
    said so or was simply deleted. evidence=side (side channel on disk),
    evidence=history (side channel gone but the day history is readable - its
    newest_error, when it has one, is a ONE-sample kind; the live repo's own
    shape is a history that exists and records nothing, which is evidence that
    nothing failed rather than no evidence), evidence=none (neither file). kind
    picks the most common exception bucket in the window; ties break on the
    bucket name so the answer is deterministic.
    """
    head_day, usable, threshold = _window_start(day, window_days)
    rows, hbad = read_failure_days(history_path)
    span = [r for r in rows
            if not usable
            or threshold <= str(r.get('day') or '')[:10] <= head_day]
    span.sort(key=lambda r: str(r.get('day') or ''))
    counts = [int(r.get('on_day') or 0) for r in span]
    today_row = None
    prev_row = None
    if usable:
        for row in span:
            row_day = str(row.get('day') or '')[:10]
            if row_day == head_day:
                today_row = row
            elif row_day < head_day:
                prev_row = row
    mean = None
    if counts:
        mean = round(float(sum(counts)) / len(counts), 2)
    today = int(today_row['on_day']) if today_row else (
        'absent' if usable else 'unmeasured')
    prev = int(prev_row['on_day']) if prev_row else (
        'none' if usable else 'unmeasured')
    delta = (today - prev) if (today_row and prev_row) else 'none'
    worst_row = None
    if span:
        worst_row = max(span, key=lambda r: (int(r.get('on_day') or 0),
                                             str(r.get('day') or '')))
    frows, _fbad = read_failures(failures_path)
    in_window = []
    for row in frows:
        fday = str(row.get('failed_at') or '')[:10]
        if usable and not (threshold <= fday <= head_day):
            continue
        in_window.append(row)
    days_by_source = {}
    for row in in_window:
        days_by_source.setdefault(row.get('source_url'), set()).add(
            str(row.get('failed_at') or '')[:10])
    recurring = sum(1 for days in days_by_source.values() if len(days) >= 2)
    kinds = {}
    for row in in_window:
        bucket = failure_kind(row.get('error'))
        kinds[bucket] = kinds.get(bucket, 0) + 1
    evidence = 'side' if os.path.isfile(failures_path) else 'none'
    kind = 'none'
    kind_count = 0
    if kinds:
        kind = sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        kind_count = kinds[kind]
    if evidence == 'none':
        # Degraded read (R2996): the day history keeps the last error it saw, so
        # a pruned side channel still answers. A history file that exists but
        # records nothing is evidence too - it says "nothing failed here", which
        # is a different statement from "no evidence at all" (the live repo's
        # own shape on 2026-11-19, measured before this branch was written).
        if os.path.isfile(history_path):
            evidence = 'history'
        for row in reversed(span):
            last_error = row.get('newest_error')
            if isinstance(last_error, str) and last_error.strip():
                kind = failure_kind(last_error)
                kind_count = 1
                break
    # R2997: "how many times did the recurring sources fail" - one source
    # failing 2 times and one failing 12 times read the same while the line
    # carried only recurring=<source count>. UNMEASURED, not zero: when the
    # side channel that carries per-source identity is gone, the honest answer
    # is None ('' = cannot be computed), because 0:0 would claim "no
    # recurrence" from evidence that never arrived.
    recur = None
    if evidence == 'side':
        recur_fails = 0
        for row in in_window:
            days = days_by_source.get(row.get('source_url')) or set()
            if len(days) >= 2:
                recur_fails += 1
        recur = (recurring, recur_fails)
    # R2998 COVERAGE: how much history the answer actually rested on. Measured
    # before this was written: a seven-day history trimmed down to today's one
    # row and a repo that started recording yesterday printed the SAME line,
    # because days= counts rows in the file, not the days a window was
    # observed. cov is the file's own first/last usable day; wcov is the days
    # inside the requested window that have a row over the days requested, so
    # an under-observed window is visible instead of silent.
    all_days = sorted({str(r.get('day') or '')[:10] for r in rows})
    cov = (all_days[0], all_days[-1]) if all_days else None
    win = max(1, int(window_days))
    wcov = None
    if usable:
        wcov = (len({str(r.get('day') or '')[:10] for r in span}), win)
    wday, wcount = (None, None)
    if worst_row is not None:
        wday = str(worst_row.get('day') or '')[:10]
        wcount = int(worst_row.get('on_day') or 0)
    # R3001 IDENTITY: the line could say HOW MANY sources failed and how often,
    # never WHICH source failed last, nor whether that source was seen
    # succeeding since - so "same page again, and is it fixed?" still needed a
    # person at a terminal. Identity lives ONLY in the side channel (the history
    # row stores urls=<count> on purpose: one fact in one place), so a missing
    # side channel answers UNMEASURED rather than "no page failed".
    newest_src = None
    since_ok = 'unmeasured'
    # R3002 STABILITY: since_ok answers "was it seen working afterwards", which a
    # source that was fixed, broke again and was fixed again answers YES to -
    # measured, both shapes read yes. flips counts how often that happened, over
    # the same two faces. R3004: flips no longer tracks since_ok's
    # measurability - since_ok needs an observation after the newest failure
    # before it may say 'no', while a flip is built from events already on
    # disk, so flips=1 beside since_ok=unmeasured is a truthful pair.
    flips = None
    if evidence == 'side' and in_window:
        newest = None
        for row in in_window:
            stamp = str(row.get('failed_at') or '')
            if newest is None or stamp > str(newest.get('failed_at') or ''):
                newest = row
        if newest is not None:
            newest_src = newest.get('source_url')
            since_ok = _since_ok(record_path, newest_src,
                                 newest.get('failed_at'))
            flips = _flips(record_path, newest_src, frows)
    # R3003 COVERAGE OF THE EVIDENCE FACE: the same row now names how far the
    # crawl record itself reaches, so since_ok=no standing on one day of record
    # cannot pass for a record that looked after the failure. A different file
    # from cov/wcov (which describe the failure-day history).
    # R3005 BREADTH OF THE REPAIR QUESTION: newest_src/since_ok answer for the
    # ONE source that failed last, so a window with several failing pages left
    # the others as counts without a verdict. pending=<n>/<judged> counts, over
    # the whole window and each source's OWN latest failure, how many were shown
    # looked-at and never back over how many could be judged at all. None (not
    # 0/0) when nothing was judged: zero-of-zero would read as "nothing to fix".
    pending = None
    pending_src = None
    # R3007 AGE OF THE NAMED SOURCE: the name answered "start here", never "how
    # long has this been broken" - so a source gone five minutes and one gone a
    # week read the same. The age is measured against the window day and the
    # NAMED source's own latest failure, never against the failure summary's
    # newest_at (measured: that one is taken across all sources and named a
    # different source's stamp). None when no source is named, so 0 can never
    # pass for "there is a named source and it just broke".
    pending_age_d = None
    # R3008 AGE SPAN OF THE PENDING SET: one age named the source waiting
    # LONGEST and left every other pending source with no age at all - measured,
    # three pending sources aged 0/2/4 days read pending_age_d=4 and the source
    # that broke TODAY appeared in none of the 24 keys, so a burst that just
    # started read exactly like a long tail. The second age is the NEWEST
    # pending source's own: the two ends are the span. A max field was refused
    # by measurement (the named source is by construction the oldest, so it
    # would restate pending_age_d); with one pending source, or with every
    # pending source sharing a stamp, the two numbers coincide - reported as the
    # truth it is, and pinned so nobody later 'fixes' the pair into one None.
    pending_age_min_d = None
    # R3009 WHERE THE MIDDLE SITS: the two ends left everything between them
    # silent - measured, two worlds with the same ends but different middles
    # (5/3/0 versus 5/1/0) were identical on all 25 keys, and so were a world
    # with the mass old (5/5/5/0/0) and one with it new (5/0/0/0/0). The third
    # age is the middle of the pending set, nearer the old end when the count is
    # even; it is not the max refused in R3008 (that one equalled pending_age_d
    # by construction in every world). A failure-day-file pointer was measured
    # and refused as an alternative: that file carries a urls= COUNT and no
    # per-source identity or age.
    pending_age_med_d = None
    # R3010 OUTSIDE THE WINDOW: the window decides who is counted, so a source
    # whose own latest failure fell before the window start vanished from every
    # key - measured, still-broken and repaired differed only through rcov, and
    # deleting the old failure row read identical to a healthy world. This third
    # count covers only that outside population and keeps its own denominator,
    # so pending= still means what sources= names. None (not 0/0) when nothing
    # out there could be judged - a trimmed side channel is not a clean bill.
    pending_old = None
    if evidence == 'side' and in_window:
        got = _pending_sources(record_path, in_window)
        if got[1]:
            pending = (got[0], got[1])
            # R3006: the count answers "how many", this answers "start here".
            # One name, the pending source waiting longest - never all of them,
            # because one line per source is what the contract refuses.
            pending_src = got[2]
            pending_age_d = _day_age(day, got[3])
            pending_age_min_d = _day_age(day, got[4])
            pending_age_med_d = _day_age(day, got[5])
    # R3012 AGE OF THE OLD WAITERS: pending_old= says how many sources outside
    # the window never came back, never how long they have been gone - measured,
    # fcov.first= belongs to whichever failure is oldest in the FILE, including
    # one repaired long ago (P2: fcov.first 2026-08-20 belonged to a repaired
    # source while the one still gone had failed on 2026-11-10). This age is the
    # still-pending old source that waited longest; None when nothing was judged
    # outside, and None (never 0) when every judged old source came back -
    # "nobody outside is pending" and "one broke today" must not read alike.
    pending_old = None
    pending_old_age_d = None
    # R3013 THE OTHER END OF THE OLD TAIL: one age described only the longest
    # wait - measured, two worlds with a 90-day and a 9-day second waiter read
    # identical on all 29 keys. The middle was refused by that measurement (it
    # equals the longest age when there are two waiters, which is the board's
    # own example); this is the YOUNGEST old waiter, the end that separates an
    # old tail from an old tail plus one that dropped out last week. Same None
    # rules as the age beside it - never 0 for "nobody outside is pending".
    pending_old_age_min_d = None
    if evidence == 'side' and usable:
        got = _pending_out_of_window(record_path, frows, threshold)
        if got is not None:
            pending_old = (got[0], got[1])
            pending_old_age_d = _day_age(day, got[2])
            pending_old_age_min_d = _day_age(day, got[3])
    rcov = _record_coverage(record_path)
    # R3011 COVERAGE OF THE SIDE CHANNEL: pending_old= names a fraction but not
    # the reach of the evidence under it - measured, a one-day channel and a
    # ninety-one-day channel read identical on all 27 keys when the judged
    # facts matched. fcov= is this channel's own first..last usable failure day,
    # following the FILE rather than the window (measured: same span at 7 and 14
    # days while pending_old= changed), and None when the channel is absent,
    # empty or holds no usable row.
    fcov = _side_coverage(failures_path)
    return {'days': len(rows), 'in_window': len(span), 'bad': hbad,
            'today': today, 'prev': prev, 'mean': mean, 'delta': delta,
            'worst': (None, None) if worst_row is None else (wday, wcount),
            'recurring': recurring, 'sources': len(days_by_source),
            'recur': recur, 'cov': cov, 'wcov': wcov,
            'evidence': evidence, 'kind': kind, 'kind_count': kind_count,
            'newest_src': newest_src, 'since_ok': since_ok,
            'flips': flips, 'pending': pending, 'pending_src': pending_src,
            'pending_age_d': pending_age_d,
            'pending_age_min_d': pending_age_min_d,
            'pending_age_med_d': pending_age_med_d,
            'pending_old': pending_old,
            'pending_old_age_d': pending_old_age_d,
            'pending_old_age_min_d': pending_old_age_min_d,
            'fcov': fcov,
            'rcov': rcov, 'window_days': window_days}


def crawled_today(repo_root, day):
    """True when a usable record already names `day` (the day gate's input)."""
    summary = CR.today_summary(CR.record_path(repo_root), day)
    return summary['today'] >= 1


def normalize(body):
    """Visible text of a page: noise blocks dropped, tags stripped, ws collapsed.

    Formatting-only edits (indentation, blank lines, attribute order) collapse to
    the same string on purpose, so a digest change means the text a reader sees
    changed rather than the markup around it.
    """
    if isinstance(body, bytes):
        body = body.decode('utf-8', 'replace')
    text = NOISE_RE.sub(' ', body)
    text = TAG_RE.sub(' ', text)
    for src, dst in (('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'),
                     ('&gt;', '>'), ('&quot;', '"'), ('&#39;', "'")):
        text = text.replace(src, dst)
    return SPACE_RE.sub(' ', text).strip()


def digest(text):
    """Stable id for a normalised page body."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def evaluate(url, body, baseline):
    """Pure judgement: (verdict, digest, excerpt) from a page and a stored store.

    `baseline` is the parsed store (url -> entry). A missing url is new-source,
    never no-drift - an empty store cannot mean "nothing changed".
    """
    text = normalize(body)
    dg = digest(text)
    prev = baseline.get(url) if isinstance(baseline, dict) else None
    if not isinstance(prev, dict) or not prev.get('digest'):
        verdict = 'new-source'
    elif prev.get('digest') == dg:
        verdict = 'no-drift'
    else:
        verdict = 'drift'
    return {'verdict': verdict, 'digest': dg, 'text': text,
            'excerpt': text[:EXCERPT_CHARS]}


def load_baselines(path):
    """Parsed store; an absent, unreadable or non-object file reads as empty."""
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return {}
    return doc if isinstance(doc, dict) else {}


def save_baselines(path, doc):
    """Atomic replace so a half-written store never becomes the next baseline."""
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(doc, fh, ensure_ascii=False, sort_keys=True, indent=1)
        fh.write('\n')
    os.replace(tmp, path)
    return path


def fetch(url, timeout=20):
    """The only network call here: one GET, decoded with replacement."""
    import urllib.request

    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status = getattr(resp, 'status', 200)
        body = resp.read()
    if int(status) != 200:
        raise IOError('E_HTTP status=%s' % status)
    return body


def run(url, repo_root, body=None, fetched_at=None, timeout=20, write=False,
        if_due=False):
    """Fetch-or-judge one url and (optionally) land a record.

    body given  -> dry run: no socket, no retrieval, judgement only.
    body None   -> real fetch; a failure answers ok=False, traces itself to the
                   side channel, and writes nothing to the record or baseline.
    if_due      -> when a usable record already names today, answer skipped=True
                   BEFORE any socket is opened and write nothing.
    """
    dry = body is not None
    stamp = fetched_at or datetime.datetime.now().astimezone().isoformat(
        timespec='seconds')
    if if_due and crawled_today(repo_root, stamp[:10]):
        # Idempotent beat: the day is already covered, so this call is a no-op
        # rather than a second retrieval that would only re-write the baseline.
        return {'ok': True, 'error': None, 'verdict': 'skip', 'digest': None,
                'row': None, 'record': None, 'baseline': None, 'trace': None,
                'dry': dry, 'skipped': True}
    if body is None:
        try:
            body = fetch(url, timeout=timeout)
        except Exception as exc:  # every network fault is one named answer
            # A retrieval that did not happen is not a crawl, so nothing is
            # written to the record: landing one here would let the scanner read
            # a failed day as green. It is still EVIDENCE, so it goes to the
            # side channel that no judgement face reads.
            error = 'E_FETCH %s: %s' % (type(exc).__name__, exc)
            trace = None
            try:
                trace = failure_path(repo_root)
                append_failure(trace, url, stamp, error)
            except Exception:
                trace = None  # evidence that cannot land never hides the failure
            return {'ok': False, 'error': error, 'verdict': None,
                    'row': None, 'record': None, 'baseline': None, 'trace': trace,
                    'dry': dry, 'skipped': False}
    bpath = baseline_path(repo_root)
    store = load_baselines(bpath)
    verdict = evaluate(url, body, store)
    note = 'bytes=%d digest=%s%s' % (
        len(body), verdict['digest'][:12], ' dry' if dry else '')
    row = {'source_url': url, 'fetched_at': stamp,
           'verdict': verdict['verdict'], 'note': note}
    record_path = None
    baseline_written = None
    if write:
        record_path = CR.append_record(CR.record_path(repo_root), url, stamp,
                                       verdict['verdict'], note=note)
        store[url] = {'digest': verdict['digest'], 'bytes': len(body),
                      'fetched_at': stamp, 'excerpt': verdict['excerpt']}
        baseline_written = save_baselines(bpath, store)
    return {'ok': True, 'error': None, 'verdict': verdict['verdict'],
            'digest': verdict['digest'], 'row': row, 'record': record_path,
            'baseline': baseline_written, 'trace': None, 'dry': dry,
            'skipped': False}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Fetch one source, judge it against the stored baseline, '
                    'and (with --write) land a record through the shipped writer.')
    ap.add_argument('--url', action='append', default=[],
                    help='source to fetch/judge; repeatable')
    ap.add_argument('--fixture', default='',
                    help='saved page to judge instead of fetching (dry run)')
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), help='repo root (default: this checkout)')
    ap.add_argument('--write', action='store_true',
                    help='append the record and update the baseline store')
    ap.add_argument('--if-due', dest='if_due', action='store_true',
                    help='no-op when a usable record already names today '
                         '(safe to call from a repeating beat)')
    ap.add_argument('--timeout', type=int, default=20)
    ap.add_argument('--failures', action='store_true',
                    help='print the failure side channel summary and exit '
                         '(a reader over evidence; carries bytes/lines and a '
                         'display-only size_gate percentage; gates nothing)')
    ap.add_argument('--failure-days', dest='failure_days', action='store_true',
                    help='print the daily failure-count history and exit '
                         '(a display series; gates nothing)')
    ap.add_argument('--failure-trend', dest='failure_trend', action='store_true',
                    help='print the count trend joined with per-day source '
                         'recurrence and exit (a display line; gates nothing)')
    ap.add_argument('--pending-old-list', dest='pending_old_list',
                    action='store_true',
                    help='print the out-of-window sources that never came '
                         'back, one line each (read-only display; writes and '
                         'gates nothing)')
    ap.add_argument('--pending-old-bad', dest='pending_old_bad',
                    action='store_true',
                    help='name the unusable lines on the failure channel by '
                         'line number and reason, never by text (read-only '
                         'display; writes and gates nothing)')
    ap.add_argument('--failure-days-bad', dest='failure_days_bad',
                    action='store_true',
                    help='name the unusable lines on the daily failure history '
                         'by line number and reason, never by text (read-only '
                         'display; writes and gates nothing)')
    ap.add_argument('--failure-days-dropped', dest='failure_days_dropped',
                    action='store_true',
                    help='list each usable day row\'s own eaten-lines count, '
                         'one line per row in file order, none for a row '
                         'written before the field (read-only display; writes '
                         'and gates nothing)')
    ap.add_argument('--failure-days-dropped-window', dest='dropped_window',
                    type=int, default=None,
                    help='keep only the last N days of that listing, measured '
                         'back from the file\'s own newest row; the header '
                         'then carries window=/shown=/truncated=/hidden=/head= '
                         'so a shortened list never reads like a short file '
                         '(read-only display; gates nothing)')
    ap.add_argument('--snapshot-failures', dest='snapshot_failures',
                    action='store_true',
                    help='persist today\'s failure counts as one history row '
                         '(same-day rows are rewritten, never duplicated)')
    ap.add_argument('--days', type=int, default=7,
                    help='window length in days for the failure faces (default 7)')
    ap.add_argument('--series-days', dest='series_days', type=int, default=None,
                    help='print only the daily-history pairs inside the last N '
                         'days, measured back from the file\'s own newest row; '
                         '--days still caps how many pairs print and the header '
                         'gains series_window=N (read-only display; gates '
                         'nothing)')
    ap.add_argument('--series-absent', dest='series_absent',
                    action='store_true',
                    help='alongside --series-days N, name the calendar days in '
                         'that window with no history row at all; the header '
                         'gains series_absent=<n|none> absent=<day,...|none> '
                         'absent_named=<n|none> days_present=<n|none> '
                         'repeat_rows=<n|none> '
                         'retry_rows=<n|none> and window_from=<day|none>, so a '
                         'silent day never reads like a measured zero, the '
                         'present/gap split sums to series_window, the '
                         'present/repeat split sums to window_rows, a '
                         'same-day repeat names whether it carried more '
                         'failure evidence than the row before it, the '
                         'first day of the window can be read instead of '
                         'counted backwards, and the named days stop at one '
                         'month (31) while series_absent keeps the full total, '
                         'so absent_named < series_absent is a visible '
                         'truncation; pass --series-absent-limit to name more '
                         '(read-only display; gates nothing)')
    ap.add_argument('--series-absent-limit', dest='series_absent_limit',
                    default=None, metavar='N|all',
                    help='how many silent days the absent= list may name with '
                         '--series-absent: a positive integer, or all for the '
                         'full list. Omit for the one-month default (31). The '
                         'count series_absent= stays the full total either way; '
                         'zero, negative and non-numeric values are refused '
                         '(read-only display; gates nothing)')
    args = ap.parse_args(argv)
    if args.series_absent and (args.series_days is None
                               or not args.failure_days):
        sys.stderr.write('series_absent applies only to --failure-days with '
                         '--series-days N\n')
        return 2
    if args.series_absent_limit is not None and not args.series_absent:
        sys.stderr.write('--series-absent-limit applies only with '
                         '--series-absent\n')
        return 2
    absent_limit, absent_why = parse_absent_limit(args.series_absent_limit)
    if absent_why is not None:
        sys.stderr.write('--series-absent-limit: %s\n' % absent_why)
        return 2
    if args.failures:
        stamp = datetime.datetime.now().astimezone().isoformat(
            timespec='seconds')
        summary = summarize_failures(failure_path(args.root), stamp, args.days)
        print('CRAWL-FAILURES total=%d recent%d=%d bad=%d urls=%d bytes=%d '
              'lines=%d size_gate=%.4f%% gate_ref=%dMB newest=%s error=%s '
              'kind=%s' % (summary['total'], summary['window_days'],
                           summary['recent'], summary['bad'], summary['urls'],
                           summary['bytes'], summary['lines'],
                           summary['size_gate'], summary['gate_ref_mb'],
                           summary['newest_at'] or 'none',
                           summary['newest_error'] or 'none',
                           summary['newest_kind']))
        return 0
    if args.failure_days:
        day_read = read_failure_days(failure_day_path(args.root))
        series = summarize_failure_days(failure_day_path(args.root), args.days,
                                        day_read, args.series_days)
        pairs = ','.join('%s:%s' % (d, n) for d, n in series['series'])
        if args.series_days is None:
            # Byte-identical to the shape AC-RUN42 arm 2 pins by equality.
            counts = series_window_counts(day_read[0], args.days, args.days)
            tail_markers = ''
        else:
            counts = series['series_counts']
            tail_markers = ' series_window=%d' % args.series_days
            if args.series_absent:
                gaps = series_absent_days(day_read[0], args.series_days,
                                          absent_limit)
                presence = series_presence_counts(day_read[0], args.series_days)
                tail_markers += ' series_absent=%s absent=%s absent_named=%s days_present=%s repeat_rows=%s retry_rows=%s window_from=%s' % (
                    'none' if gaps['count'] is None else gaps['count'],
                    ','.join(gaps['days']) or 'none',
                    'none' if gaps['count'] is None else gaps['named'],
                    'none' if presence['present'] is None
                    else presence['present'],
                    'none' if presence['repeat'] is None
                    else presence['repeat'],
                    'none' if presence['retry'] is None
                    else presence['retry'],
                    'none' if presence['start'] is None
                    else presence['start'])
        print('CRAWL-FAILURE-DAYS days=%d bad=%d first=%s last=%s '
              'dropped=%s series=%s bytes=%d size_gate=%.4f%% gate_ref=%dMB '
              'series_limit=%d series_shown=%d series_outside=%d '
              'window_rows=%d%s'
              % (series['days'], series['bad'], series['first'] or 'none',
                 series['last'] or 'none',
                 'none' if series['dropped'] is None else series['dropped'],
                 pairs or 'none', series['bytes'],
                 series['size_gate'], series['gate_ref_mb'],
                 counts['limit'], counts['shown'], counts['outside'],
                 counts['window_rows'], tail_markers))
        return 0
    if args.failure_days_dropped:
        listing = list_failure_days_dropped(failure_day_path(args.root),
                                            args.dropped_window)
        if args.dropped_window is None:
            # Byte-identical to the shape two suite arms pin by equality.
            print('CRAWL-FAILURE-DAYS-DROPPED days=%d bad=%d'
                  % (listing['days'], listing['bad']))
        else:
            print('CRAWL-FAILURE-DAYS-DROPPED days=%d bad=%d window=%d '
                  'shown=%d truncated=%d hidden=%d head=%s'
                  % (listing['days'], listing['bad'], listing['window'],
                     listing['shown'], 1 if listing['truncated'] else 0,
                     listing['hidden'], listing['head'] or 'none'))
        for item in listing['rows']:
            print('DAY-DROPPED day=%s dropped=%s'
                  % (item['day'],
                     'none' if item['dropped'] is None else item['dropped']))
        return 0
    if args.pending_old_bad:
        named = read_failure_bad_lines(failure_path(args.root))
        print('CRAWL-PENDING-OLD-BAD bad=%d' % len(named))
        for item in named:
            print('BAD-LINE n=%d why=%s' % (item['line'], item['why']))
        return 0
    if args.failure_days_bad:
        named = read_failure_day_bad_lines(failure_day_path(args.root))
        print('CRAWL-FAILURE-DAYS-BAD bad=%d' % len(named))
        for item in named:
            print('BAD-LINE n=%d why=%s' % (item['line'], item['why']))
        return 0
    if args.pending_old_list:
        stamp = datetime.datetime.now().astimezone().isoformat(
            timespec='seconds')
        lst = list_pending_old(CR.record_path(args.root),
                               failure_path(args.root), stamp, args.days)
        po = lst['pending_old']
        fcov_txt = ('none' if lst['fcov'] is None
                    else '%s..%s' % lst['fcov'])
        head = ('CRAWL-PENDING-OLD-LIST pending_old=%s days=%d bad=%d fcov=%s '
                'last_at=%s'
                % ('none' if po is None else '%d/%d' % po, args.days,
                   lst['bad'], fcov_txt,
                   'none' if lst['last_at'] is None else lst['last_at']))
        if not lst['waiting'] and lst['reason']:
            head += ' reason=%s' % lst['reason']
        print(head)
        for row in lst['waiting']:
            print('PENDING-OLD url=%s failed_at=%s age_d=%s'
                  % (row['source_url'], row['failed_at'],
                     'none' if row['age_d'] is None else row['age_d']))
        return 0
    if args.failure_trend:
        stamp = datetime.datetime.now().astimezone().isoformat(
            timespec='seconds')
        trend = summarize_failure_trend(failure_day_path(args.root),
                                        failure_path(args.root), stamp,
                                        args.days,
                                        record_path=CR.record_path(args.root))
        wday, wcount = trend['worst']
        worst_txt = 'none' if wday is None else '%s:%d' % (wday, wcount)
        mean_txt = 'none' if trend['mean'] is None else ('%g' % trend['mean'])
        kind_txt = ('none' if trend['kind'] == 'none'
                    else '%s:%d' % (trend['kind'], trend['kind_count']))
        recur_txt = ('none' if trend['recur'] is None
                     else '%d:%d' % trend['recur'])
        cov_txt = ('none' if trend['cov'] is None
                   else '%s..%s' % trend['cov'])
        wcov_txt = ('none' if trend['wcov'] is None
                    else '%d/%d' % trend['wcov'])
        rcov_txt = ('none' if trend['rcov'] is None
                    else '%s..%s' % trend['rcov'])
        pending_txt = ('none' if trend['pending'] is None
                       else '%d/%d' % trend['pending'])
        age_txt = ('none' if trend['pending_age_d'] is None
                   else '%d' % trend['pending_age_d'])
        age_min_txt = ('none' if trend['pending_age_min_d'] is None
                       else '%d' % trend['pending_age_min_d'])
        age_med_txt = ('none' if trend['pending_age_med_d'] is None
                       else '%d' % trend['pending_age_med_d'])
        old_txt = ('none' if trend['pending_old'] is None
                   else '%d/%d' % trend['pending_old'])
        old_age_txt = ('none' if trend['pending_old_age_d'] is None
                       else '%d' % trend['pending_old_age_d'])
        old_age_min_txt = ('none' if trend['pending_old_age_min_d'] is None
                           else '%d' % trend['pending_old_age_min_d'])
        fcov_txt = ('none' if trend['fcov'] is None
                    else '%s..%s' % trend['fcov'])
        print('CRAWL-FAILURE-TREND days=%d today=%s prev=%s mean=%s delta=%s '
              'worst=%s recurring=%d sources=%d bad=%d evidence=%s kind=%s '
              'recur=%s cov=%s wcov=%s newest_src=%s since_ok=%s flips=%s '
              'pending=%s pending_src=%s pending_age_d=%s '
              'pending_age_min_d=%s pending_age_med_d=%s pending_old=%s '
              'pending_old_age_d=%s pending_old_age_min_d=%s fcov=%s rcov=%s'
              % (trend['days'], trend['today'], trend['prev'], mean_txt,
                 trend['delta'], worst_txt, trend['recurring'],
                 trend['sources'], trend['bad'], trend['evidence'], kind_txt,
                 recur_txt, cov_txt, wcov_txt,
                 trend['newest_src'] or 'none', trend['since_ok'],
                 'unmeasured' if trend['flips'] is None else trend['flips'],
                 pending_txt, trend['pending_src'] or 'none', age_txt,
                 age_min_txt, age_med_txt, old_txt, old_age_txt,
                 old_age_min_txt, fcov_txt, rcov_txt))
        return 0
    standalone_snapshot = (args.snapshot_failures and not args.url
                           and not args.if_due)
    if standalone_snapshot:
        stamp = datetime.datetime.now().astimezone().isoformat(
            timespec='seconds')
        try:
            row = snapshot_failure_day(args.root, stamp[:10], args.days)
        except Exception as exc:  # a display write must never look like a crawl
            print('CRAWL-FAILURE-DAY error=%s: %s' % (type(exc).__name__, exc))
            return 3
        print('CRAWL-FAILURE-DAY day=%s on_day=%d total=%d recent%d=%d bad=%d '
              'urls=%d dropped=%d' % (row['day'], row['on_day'], row['total'],
                                      row['recent'], row['recent'], row['bad'],
                                      row['urls'], row['dropped']))
        return 0
    if not args.url and args.if_due:
        args.url = [DEFAULT_URL]
    if not args.url:
        print('E_NO_URL need at least one --url')
        return 2
    body = None
    if args.fixture:
        try:
            with open(args.fixture, 'r', encoding='utf-8', errors='replace') as fh:
                body = fh.read()
        except OSError as exc:
            print('E_FIXTURE %s' % exc)
            return 2
    rc = 0
    for url in args.url:
        out = run(url, args.root, body=body, timeout=args.timeout,
                  write=args.write, if_due=args.if_due)
        if out.get('skipped'):
            print('CRAWL url=%s ok=True skipped=1 why=already-crawled-today'
                  % url)
            continue
        if not out['ok']:
            print('CRAWL url=%s ok=False dry=%s error=%s trace=%s'
                  % (url, out['dry'], out['error'], out['trace'] or 'none'))
            rc = 3
            continue
        print('CRAWL url=%s ok=True dry=%s verdict=%s digest=%s record=%s '
              'baseline=%s' % (url, out['dry'], out['verdict'],
                               out['digest'][:12], out['record'] or 'none',
                               out['baseline'] or 'none'))
    if args.snapshot_failures:
        # Runs AFTER the retrieval on purpose: a failure this very beat must be
        # in the row that names today, not in tomorrow's.
        now = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
        try:
            row = snapshot_failure_day(args.root, now[:10], args.days)
            print('CRAWL-FAILURE-DAY day=%s on_day=%d total=%d recent%d=%d '
                  'bad=%d urls=%d dropped=%d' % (row['day'], row['on_day'],
                                                 row['total'], row['recent'],
                                                 row['recent'], row['bad'],
                                                 row['urls'], row['dropped']))
        except Exception as exc:
            # History is display: a broken display prints its own line and
            # never rewrites the crawl's answer.
            print('CRAWL-FAILURE-DAY error=%s: %s' % (type(exc).__name__, exc))
    return rc


if __name__ == '__main__':
    sys.exit(main())
