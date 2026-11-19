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
bad, urls, newest), rewriting that day's row in place so a ten-minute beat does
not append duplicates. It is a DISPLAY face only: the scanner never reads it
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


def read_failures(path):
    """(rows, bad): usable failure rows, plus the count of unusable ones.

    Absence is zero rows, not an error - the same law as CR.read_records, so a
    reader can ask "what failed?" without a prior write.
    """
    rows = []
    bad = 0
    if not os.path.isfile(path):
        return rows, bad
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except ValueError:
                bad += 1
                continue
            if (not isinstance(row, dict) or not _usable_day(row.get('failed_at'))
                    or not str(row.get('error') or '').strip()):
                bad += 1
                continue
            rows.append(row)
    return rows, bad


def _summary_from_rows(rows, bad, day, window_days=7):
    """Counts over already-validated rows; the one place the window law lives."""
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
    """(rows, bad) for the daily history; a missing file is zero rows."""
    rows = []
    bad = 0
    if not os.path.isfile(path):
        return rows, bad
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except ValueError:
                bad += 1
                continue
            if (not isinstance(row, dict) or not _usable_day(row.get('day'))
                    or not isinstance(row.get('on_day'), int)):
                bad += 1
                continue
            rows.append(row)
    return rows, bad


def snapshot_failure_day(repo_root, day, window_days=7):
    """Persist today's failure counts as ONE row, replacing that day's own row.

    WHY (R2994): --failures answers "what is on disk now" and forgets the last
    time it was asked, so a page failing three days straight and one bad
    afternoon read the same. This writes the window counts down once per day so
    two days can be compared. Same-day re-runs REWRITE the row rather than
    appending: the beat fires every ten minutes, and a file that grows a row per
    beat would be noise rather than history. Only the days somebody actually
    snapshotted appear - a gap is an honest gap, not a zero.
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
    history, _ignored = read_failure_days(path)
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


def summarize_failure_days(path, limit=7):
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
    """
    rows, bad = read_failure_days(path)
    tail = rows[-max(1, int(limit)):]
    out = {'days': len(rows), 'bad': bad,
           'first': (rows[0].get('day') if rows else None),
           'last': (rows[-1].get('day') if rows else None),
           'series': [(r.get('day'), r.get('on_day')) for r in tail]}
    stats = failure_file_stats(path)
    out['present'] = stats['present']
    out['bytes'] = stats['bytes']
    out['size_gate'] = size_gate_pct(stats['bytes'])
    out['gate_ref_mb'] = SIZE_REFERENCE_BYTES // (1024 * 1024)
    return out


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


def _side_coverage(failures_path):
    """(first_day, last_day) the failure side channel reaches, or None.

    WHY (R3011): pending_old= counts over this side channel and never said how
    far back the channel itself reaches - measured, a one-day channel and a
    ninety-one-day channel read identical on all 27 keys when the judged facts
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
    """
    if not failures_path or not os.path.isfile(failures_path):
        return None
    rows, _bad = read_failures(failures_path)
    days = sorted({str(row.get('failed_at') or '')[:10] for row in rows})
    return (days[0], days[-1]) if days else None


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
    over sources=1). Not a per-source face either: naming or aging an old
    source needs one line per source, which the one-line contract refuses.

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
    waiting = []
    head = str(threshold or '')[:10]
    for src, stamp in latest.items():
        if str(stamp)[:10] >= head:
            continue
        verdict = _since_ok(record_path, src, stamp)
        if verdict == 'no':
            still += 1
            judged += 1
            waiting.append((str(stamp), str(src)))
        elif verdict == 'yes':
            judged += 1
    if not judged:
        return None
    waiting.sort()
    return (still, judged, waiting[0][0] if waiting else None)


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
    if evidence == 'side' and usable:
        got = _pending_out_of_window(record_path, frows, threshold)
        if got is not None:
            pending_old = (got[0], got[1])
            pending_old_age_d = _day_age(day, got[2])
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
    ap.add_argument('--snapshot-failures', dest='snapshot_failures',
                    action='store_true',
                    help='persist today\'s failure counts as one history row '
                         '(same-day rows are rewritten, never duplicated)')
    ap.add_argument('--days', type=int, default=7,
                    help='window length in days for the failure faces (default 7)')
    args = ap.parse_args(argv)
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
        series = summarize_failure_days(failure_day_path(args.root), args.days)
        pairs = ','.join('%s:%s' % (d, n) for d, n in series['series'])
        print('CRAWL-FAILURE-DAYS days=%d bad=%d first=%s last=%s series=%s '
              'bytes=%d size_gate=%.4f%% gate_ref=%dMB'
              % (series['days'], series['bad'], series['first'] or 'none',
                 series['last'] or 'none', pairs or 'none', series['bytes'],
                 series['size_gate'], series['gate_ref_mb']))
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
        fcov_txt = ('none' if trend['fcov'] is None
                    else '%s..%s' % trend['fcov'])
        print('CRAWL-FAILURE-TREND days=%d today=%s prev=%s mean=%s delta=%s '
              'worst=%s recurring=%d sources=%d bad=%d evidence=%s kind=%s '
              'recur=%s cov=%s wcov=%s newest_src=%s since_ok=%s flips=%s '
              'pending=%s pending_src=%s pending_age_d=%s '
              'pending_age_min_d=%s pending_age_med_d=%s pending_old=%s '
              'pending_old_age_d=%s fcov=%s rcov=%s'
              % (trend['days'], trend['today'], trend['prev'], mean_txt,
                 trend['delta'], worst_txt, trend['recurring'],
                 trend['sources'], trend['bad'], trend['evidence'], kind_txt,
                 recur_txt, cov_txt, wcov_txt,
                 trend['newest_src'] or 'none', trend['since_ok'],
                 'unmeasured' if trend['flips'] is None else trend['flips'],
                 pending_txt, trend['pending_src'] or 'none', age_txt,
                 age_min_txt, age_med_txt, old_txt, old_age_txt, fcov_txt,
                 rcov_txt))
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
              'urls=%d' % (row['day'], row['on_day'], row['total'],
                           row['recent'], row['recent'], row['bad'],
                           row['urls']))
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
                  'bad=%d urls=%d' % (row['day'], row['on_day'], row['total'],
                                      row['recent'], row['recent'], row['bad'],
                                      row['urls']))
        except Exception as exc:
            # History is display: a broken display prints its own line and
            # never rewrites the crawl's answer.
            print('CRAWL-FAILURE-DAY error=%s: %s' % (type(exc).__name__, exc))
    return rc


if __name__ == '__main__':
    sys.exit(main())
