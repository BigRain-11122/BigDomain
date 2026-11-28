"""qa_log - one canonical writer for window evidence logs (R2776, AC-QAL1..7).

Why this exists: the R2775 artifact qa/index-newest-band-R2775.log was healthy in
content and wrong in dialect - UTF-16LE with a FF FE BOM and CRLF endings, which
is what PowerShell redirection produces by default. The writer census flagged it,
the daily census gate failed the day, and the battery suite reconcile-daily-census
went red on cd7. That was the third artifact of the class (R2768 re-encoded two),
so the repair is a birth site, not another re-encode by hand.

Usage:
  python tools/qa_log.py NAME.log                 # read stdin, write qa/NAME.log
  python tools/qa_log.py NAME.log --from FILE     # read FILE (any dialect), write qa/NAME.log
  python tools/qa_log.py --check NAME             # read-only dialect verdict, rc=2 = red
  python tools/qa_log.py --ledger-check [PATH]    # read-only replacement ledger verdict,
                                                  # default state/qa_replacements.jsonl
  python tools/qa_log.py --selftest               # fixtures in a temp dir, nothing in qa/

Contract (AC-QAL1..7):
  AC-QAL1 any readable source (utf-8, utf-8-BOM, utf-16 BOM, gb18030 fallback) is
          written as UTF-8 without BOM, LF only, one trailing newline.
  AC-QAL2 the write is proven by reading it back: no BOM, no CR, decodable,
          non-empty, trailing newline; on any failure rc=2 and no half file.
  AC-QAL3 atomic: tmp file in the destination dir then os.replace; no .tmp left.
  AC-QAL4 --check NAME is read-only and refuses UTF-16/BOM/CR/undecodable files.
  AC-QAL5 the archived R2775 sample replays to the exact bytes already in the repo.
  AC-QAL6 a name holding a path separator, a drive colon, or nothing is refused.
  AC-QAL7 the selftest never touches qa/, this source is ASCII, and it imports no
          network or subprocess module.

R2807 (AC-QALB8): a source that still carries NUL after decoding is REFUSED
rather than stored - BOM-less UTF-16 used to be written as a NUL-riddled file
with VERDICT PASS and read back as the healthy utf-8/lf dialect by this tool and
by the writer census. --check names such a file nul-bytes.
R3203 (AC-QAL9): a generator's carrier proof line is not a relogged file's
proof. The preview generator prints "LOG OK path=<p> bytes=<n> lines=<n>
sha16=<h>" on stdout, proving the file it just wrote; storing that whole stdout
through this writer kept the line verbatim inside a new file whose own sha16 was
a different number (measured: 761 bytes, carried 271ba9eb7b2d1230, own
4210a333be0b1d92) while both dialect faces stayed green. Such a line is now
prefixed CARRIED, so no reader can take it for this log's proof; a near-miss
shape is left untouched, and the line is never dropped. This is the writer's
job because --from (and stdin) is the only door through which one file's bytes
become another file's evidence.

R3204 (AC-QAL10): --check now names the count instead of leaving it to the eye.
Measured before this change: files holding 0, 1 and 2 CARRIED lines all read
rc=0 with the same QA-LOG OK line naming only dialect and bytes, the writer
census answered class=tee for all three, and the pre-commit gate refused none
of them - it reads row["class"] only. Zero files in the tree parse that text,
so the OK line gained carried=<n> at its tail with the old fields untouched.
The count is exact shapes only (a near miss is not counted), and it is not a
verdict: it says this file quotes N proofs of other files, not that the
quoted text is right and not that this file is wrong. A RED line never gains
the field, because a red dialect means the body was never judged.

R3205 (AC-QAL11): the other direction - an UNMARKED proof line was invisible.
Measured before this change: three files holding 0, 1 and 2 bare proof lines
all answered rc=0 with text that differed only in bytes=, the writer census
answered class=tee for all three, and the pre-commit gate compares the dialect
class only, never the body. A bare line can only be born one way today:
battery_shard.stream_evidence writes progress in place without going through
do_write (measured: one bare proof line landed unmarked, 102 bytes), while the
real qa/ tree holds zero bare lines across 4617 files. So --check now also
names bare_proofs=<n>, exact shapes only, old fields byte for byte the same.
It is a count, not a verdict: the line proves another file, and a RED line
still gains no field because its body was never judged. The name avoids a
prefix clash - bare_lf= and rows==bare= already exist elsewhere.

R3213 (AC-QAL12): the writer's own NAME face could create a file that no
reader enumerates. Measured before this guard (read-only probe over the
shipped tree): fifty-five shipped enumerations filter on endswith(".log") -
the writer census at three sites, the pre-commit evidence gate at one, and
the closeout `files=` count which reads the census line - so a file written
as qa/NAME without the suffix landed in the healthy dialect, was skipped by
every one of them, and could not even be found by `--check NAME.log`. The
cost of closing it was measured first: every documented invocation in the
repo names a .log file, tools/battery_shard.py passes its --evidence name
through evidence_name() unchanged, and qa/ holds exactly one log-shaped
suffixless artifact (round-R2835-closeout, written before this guard). The
refusal is on the WRITE face only: do_check still reads any flat name, so
that existing artifact stays readable. The fix is at birth, not at the reader.

R3214 (AC-QALB18): the sibling in-place door was reopened and then guarded.
battery_shard.stream_evidence writes progress while a leg is still running, so
it cannot use do_write - but it took a FULL path and asked neither question the
write face asks. Measured before the guard over a private temp tree: a
suffixless qa/NAME landed in the healthy dialect (invisible to the census, the
pre-commit gate and the closeout files= count), and a path outside qa/ landed
the same bytes anywhere on disk. It now requires the parent directory to be
QA_DIR and the name to pass check_name plus check_log_suffix, both read at call
time so a suite can point the door at a private directory. Nothing shipped
changes: every call site passes os.path.join(QA_DIR, evidence_name(...)), and
the in-place write with its fsync stays, so a killed leg still leaves a
readable RUNNING file.

R3215 (AC-QALB21): the destination had no law either. do_write and write_atomic
take a `directory` and accept any of them, so "evidence may leave qa/" was held
only by caller discipline: every reader enumerates qa/*.log (the writer census,
the pre-commit evidence gate, the closeout files= count), so a .log written
inside the repo but outside qa/ lands in the healthy dialect and is never
judged. Measured first (AST census of every call site, plus decisive arms in a
private temp world and one repo-internal arm removed again): the repo has
exactly one production call site that passes a directory at all
(tools/battery_shard.py passes QA_DIR itself), the rest of the shipped writer
calls omit it, and every test world passes a tempfile.mkdtemp path outside the
repo. So the law is drawn where it costs nothing: the destination must be, after
realpath, the qa/ dir or something outside the repo. A repo path that is not
qa/ is refused with E_DEST_INSIDE_REPO and lands nothing. The default is now
resolved at call time (directory=None), because a default bound at import time
would keep pointing at the real qa/ inside a suite that has pointed QA at a
private world.

R3216 (AC-QALB24): a same-name rewrite used to be silent. write_atomic replaces
the whole file with os.replace and the only receipt named the NEW bytes, so the
evidence that existed a moment earlier survived nowhere - not in stdout, not in
the read-back proof, and not in the census. Measured first (private temp world,
then the shipped history): writing the same name twice with different bodies
answered rc=0 both times, printed only the second sha16, and read back clean
both times while the census answered class=tee for both versions; 72 rewrite
events over 69 shipped *.log paths exist in git history, and the live
qa/suite-logs-toolkit-R3212.log has carried at least two different bodies under
one name. A refusal was measured too expensive (it would have blocked all 72
re-lands, including the repair re-land workflows the closeout gate itself
demands), so the door now ANNOUNCES: when the target already exists, one
QA-LOG REPLACED line names old_bytes, old_sha16, new_bytes and new_sha16, read
before and after the replace. The old hash is captured before the write because
after it the old bytes are gone from disk. An identical-bytes rewrite prints the
line too, so "nothing changed" is visible rather than assumed, and a brand-new
name prints none.

R3217 (AC-QALB27): that announcement lived only in stdout. Measured first: of
fourteen executable faces naming this writer, thirteen print to the screen and
one captures, so by contract nobody was obliged to keep the line; and the one
capture path re-lands the text as evidence body, where another file's old hash
reads like this file's own. The record therefore moved into the writer: after a
replacement it appends one JSON line (name, old_bytes, old_sha16, new_bytes,
new_sha16, ts) to a ledger that is not evidence - state/qa_replacements.jsonl
for the live qa/ dir, and a sibling file in the destination dir for any other
world, so a suite never records into the live ledger. A failed append names
itself and answers rc=2: the file landed, the record did not. Evidence bytes are
untouched - the ledger is a separate append.

R3218 (AC-QALB30..32): that ledger was write-only. Measured first: exactly one
file in the tree names it and that file is this writer, so a ledger that is
corrupt, stale or absent answered nothing to anyone - the dialect face, the
read-back proof and the writer census all return the same output either way.
--ledger-check [PATH] is the missing read: read-only, default the live ledger,
one line with rows/names/bad/stale/missing and one detail line per defect. A
missing ledger is rows=0 (no rewrite yet, not a defect); a bad JSON line or a
row whose latest new_sha16 no longer matches the file on disk is RED; a row
whose file is gone is counted as missing, because a deletion is another event.

Stdlib only, ASCII source, zero network, zero shell.
"""

import datetime
import hashlib
import io
import json
import os
import re
import sys
import tempfile

import hashlib
import io
import os
import re
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
QA = os.path.join(REPO, "qa")

BOM_UTF8 = b"\xef\xbb\xbf"
BOM_16LE = b"\xff\xfe"
BOM_16BE = b"\xfe\xff"

LEDGER_NAME = "qa_replacements.jsonl"
LEDGER = os.path.join(REPO, "state", LEDGER_NAME)


def ledger_path(directory):
    """R3217: where the replacement record goes for this destination.

    The live qa/ dir owns one tracked ledger in state/; every other world keeps
    its ledger inside itself, so a suite that points the writer at a temp dir
    records into that dir and never appends to the live file. The live anchor is
    REPO/qa rather than the module-level QA, because suites reassign QA and the
    ledger must not follow them into the repo.
    """
    dest = os.path.normcase(os.path.realpath(directory))
    live = os.path.normcase(os.path.realpath(os.path.join(REPO, "qa")))
    if dest == live:
        return LEDGER
    return os.path.join(directory, LEDGER_NAME)


# R3371 (AC-QCH1/AC-QCH2): the ledger has never been the only writer on
# qa/*.log. tools/battery_shard.py stream_evidence publishes a RUNNING partial
# IN PLACE while a leg is still running, and that partial is legitimately
# unrecorded - it is a placeholder, not evidence. A same-window re-run then
# replaces its own partial, so the later row's `old` identity is a transient
# that never lands anywhere. Measured at R3371: five such rows read as chain
# breaks (battery-shard-{ledger,smallfamilies,os,sxf,qfe}-*.log) and each
# intermediate blob exists in no commit. The partial now declares itself with
# this sentinel as its first line, and the row records what was replaced.
PROGRESS_SENTINEL = "# --- PROGRESS PARTIAL (not evidence)"
PREV_KIND_EVIDENCE = "evidence"
PREV_KIND_PROGRESS = "progress"
PREV_KINDS = (PREV_KIND_EVIDENCE, PREV_KIND_PROGRESS)


def previous_kind(raw):
    """AC-QCH1: what the bytes being replaced were, read from the bytes.

    A progress partial is recognised by its own first line, never by a size, a
    name or a guess: the sentinel is written by the shipped streamer, and a
    file without it is evidence whatever it is called. CRLF is tolerated
    because the sentinel is compared after the line break is stripped.
    """
    first = raw.split(b"\n", 1)[0]
    if first.rstrip(b"\r") == PROGRESS_SENTINEL.encode("ascii"):
        return PREV_KIND_PROGRESS
    return PREV_KIND_EVIDENCE


def record_replacement(directory, name, previous, proof,
                       prev_kind=PREV_KIND_EVIDENCE):
    """R3217 (AC-QALB27): the replacement record survives the process.

    One JSON line per rewrite, appended with a flush and an fsync, so the old
    identity is readable by a machine after the window that replaced it is gone.
    The ledger is not evidence: it is a different file with a different name,
    and the evidence bytes it describes are not touched here.

    R3371 (AC-QCH2): the row also says WHAT it replaced. Rows written before
    this field existed carry no declaration and are never excused by it.
    """
    path = ledger_path(directory)
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    stamp = datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = {
        "ts": stamp,
        "event": "REPLACED",
        "name": name,
        "old_bytes": previous[0],
        "old_sha16": previous[1],
        "new_bytes": proof["bytes"],
        "new_sha16": proof["sha256"],
        "prev_kind": prev_kind,
    }
    line = json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n"
    with io.open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    return path


def ledger_row_problem(obj):
    """R3218 (AC-QALB30/31): what a record must be before it can be believed."""
    if not isinstance(obj, dict):
        return "not-object"
    if obj.get("event") != "REPLACED":
        return "event"
    name = obj.get("name")
    if (not isinstance(name, str) or not name or name in (".", "..")
            or "/" in name or "\\" in name):
        return "name"
    for key in ("old_bytes", "new_bytes"):
        value = obj.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return key
    for key in ("old_sha16", "new_sha16"):
        value = obj.get(key)
        if not isinstance(value, str) or len(value) != 16:
            return key
        if any(ch not in "0123456789abcdef" for ch in value):
            return key
    # R3371 (AC-QCH4): an optional declaration, but a row that carries one
    # must carry a lawful one - a typo would otherwise excuse or accuse
    # silently. Absent is legal: every row written before R3371 lacks it.
    if "prev_kind" in obj and obj["prev_kind"] not in PREV_KINDS:
        return "prev_kind"
    return None


def read_ledger_located(path):
    """R3220: parse a ledger and keep the line each record came from.

    Still ONE parser: `read_ledger` renders this for callers that only want the
    records, and the chain face needs the line numbers to name a gap. Blank
    lines carry no claim and are skipped; an undecodable file is one bad line 0,
    because nothing below it can be judged.
    """
    if not os.path.isfile(path):
        return [], []
    raw = io.open(path, "rb").read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return [], [(0, "undecodable")]
    records = []
    bad = []
    for number, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            bad.append((number, "json"))
            continue
        problem = ledger_row_problem(obj)
        if problem:
            bad.append((number, problem))
            continue
        records.append((number, obj))
    return records, bad


def read_ledger(path):
    """R3218: parse a ledger without ever writing it.

    Returns (records, bad), where bad is a list of (line number, reason).
    """
    located, bad = read_ledger_located(path)
    return [obj for _number, obj in located], bad


def ledger_report(path=None, evidence_dir=None):
    """R3219 (AC-QALB33): the ONE reading of a ledger, shared with the gate.

    AC-QALB30..32 shipped the printer; the closeout gate now asks the same
    question at every closeout, so the judgement moved here and the printer
    below renders this dict. A second parser in the gate would let the two
    faces disagree about what a bad row is.

    R3220 (AC-QALB34/35): `broken` counts the names whose adjacent rows do not
    link - the later row's `old_sha16/old_bytes` must be the earlier row's
    `new_sha16/new_bytes`. It is a READING, never a verdict: a break can be a
    lost record OR a lawful deletion-then-recreate, a direct in-place rewrite
    or a cross-machine writer, and this ledger never claimed to observe those.
    Refusing on a break would accuse the lawful cases.

    `evidence_dir` defaults to the shipped rule: the live ledger is read
    against REPO/qa, every other ledger against its own directory. A caller
    that knows the world (the gate) passes the dir it is judging.

    R3224 (AC-SXF26): `present` is whether the ledger FILE exists. Measured
    this window on three worlds - an absent ledger, an empty ledger and a
    one-row ledger - the first two answered identical `rows=0 bad=[]`, so a
    consumer could not tell "nothing to measure" from "measured empty": the
    counts alone carry no existence. One stat, published as a reading, never a
    verdict; an absent ledger is still OK and still rows=0.
    """
    path = LEDGER if path is None else path
    located, bad = read_ledger_located(path)
    latest = {}
    previous = {}
    broken = []
    excused = []
    for number, record in located:
        name = record["name"]
        prev = previous.get(name)
        if prev is not None:
            prev_number, prev_record = prev
            linked = (record["old_sha16"] == prev_record["new_sha16"]
                      and record["old_bytes"] == prev_record["new_bytes"])
            if not linked:
                # R3371 (AC-QCH3): a break is excused ONLY on the later row's
                # own declaration that what it replaced was a progress partial.
                # Rows that predate the field carry no declaration and stay
                # broken - absence is not a claim, and this ledger never
                # guesses one.
                if record.get("prev_kind") == PREV_KIND_PROGRESS:
                    excused.append((name, prev_number, number))
                else:
                    broken.append((name, prev_number, number,
                                   prev_record["new_sha16"],
                                   record["old_sha16"]))
        previous[name] = (number, record)
        latest[name] = record
    if evidence_dir is None:
        here = os.path.normcase(os.path.realpath(path))
        live = os.path.normcase(os.path.realpath(LEDGER))
        if here == live:
            evidence_dir = os.path.join(REPO, "qa")
        else:
            evidence_dir = os.path.dirname(os.path.abspath(path))
    stale = []
    missing = []
    for name in sorted(latest):
        target = os.path.join(evidence_dir, name)
        if not os.path.isfile(target):
            missing.append(name)
            continue
        disk = hashlib.sha256(io.open(target, "rb").read()).hexdigest()[:16]
        if disk != latest[name]["new_sha16"]:
            stale.append((name, disk, latest[name]["new_sha16"]))
    return {"verdict": "RED" if (bad or stale) else "OK",
            "path": path, "present": os.path.isfile(path),
            "rows": len(located), "names": len(latest),
            "bad": bad, "stale": stale, "missing": missing,
            "broken": broken, "excused": excused}


def chain_reading(path=None):
    """R3616 (AC-LADJ1..3): the break QUALIFICATION, asked of its owner.

    `ledger_report` publishes `broken` as a count and refuses to say what a
    break is (AC-QALB34). tools/qa_chain_diagnose.py owns that judgement
    (AC-QCH1..6) and reads the same ledger through this module's own parser.
    The count station therefore asks the qualification station in-process
    instead of letting a round quote a bare `broken=5` as if five records had
    been lost.

    Returns None when the adjudicator cannot be imported or read: "asked and
    got nothing" is published as UNADJUDICATED, never defaulted to OK.
    """
    try:
        if BASE not in sys.path:
            sys.path.insert(0, BASE)
        import qa_chain_diagnose as adjudicator
        data = adjudicator.report(path)
    except Exception:
        return None
    unexplained = len(data["unexplained"])
    partial = len([b for b in data["breaks"]
                   if b["kind"] == adjudicator.KIND_PARTIAL])
    # R3648 (AC-EXV2): the landed counts are DERIVED from the same report, not
    # measured here - `landed_state()` owns that comparison and lives in the
    # adjudicator. A second sha/byte check in this helper would let the CEO
    # face and the command-line station disagree about the same evidence.
    return {"verdict": data["verdict"],
            "partial": partial,
            "declared": len(data["breaks"]) - partial - unexplained,
            "unexplained": unexplained,
            "landed_ok": len([b for b in data["breaks"]
                              if b["landed"] == adjudicator.LANDED_MATCH]),
            "landed_missing": len(
                [b for b in data["breaks"]
                 if b["landed"] == adjudicator.LANDED_MISSING]),
            "rewritten": len(data["rewritten"])}


def do_ledger_check(path=None):
    """R3218 (AC-QALB30..32): read the replacement ledger back, read-only.

    One line says what the ledger holds, one detail line per defect. A ledger
    that is not there answers rows=0: no rewrite has happened yet, which is not
    a defect. A row whose latest record no longer matches the file on disk is
    named stale, because that is evidence changing with no record of it. A row
    whose file is gone is counted, not reddened - a deletion is another event,
    and this ledger never claimed the file would stay.
    """
    report = ledger_report(path)
    sys.stdout.write("QA-LEDGER %s path=%s rows=%d names=%d bad=%d stale=%d "
                     "missing=%d broken=%d excused=%d\n"
                     % (report["verdict"], report["path"], report["rows"],
                        report["names"], len(report["bad"]),
                        len(report["stale"]), len(report["missing"]),
                        len(report["broken"]), len(report["excused"])))
    for number, reason in report["bad"]:
        sys.stdout.write("QA-LEDGER detail bad line=%d reason=%s\n"
                         % (number, reason))
    for name, disk, wanted in report["stale"]:
        sys.stdout.write("QA-LEDGER detail stale name=%s disk_sha16=%s "
                         "ledger_sha16=%s\n" % (name, disk, wanted))
    for name in report["missing"]:
        sys.stdout.write("QA-LEDGER detail missing name=%s\n" % name)
    for name, prev_line, line, prev_sha, old_sha in report["broken"]:
        sys.stdout.write("QA-LEDGER detail chain name=%s prev_line=%d "
                         "line=%d prev_new_sha16=%s old_sha16=%s\n"
                         % (name, prev_line, line, prev_sha, old_sha))
    for name, prev_line, line in report["excused"]:
        sys.stdout.write("QA-LEDGER detail excused name=%s prev_line=%d "
                         "line=%d prev_kind=%s\n"
                         % (name, prev_line, line, PREV_KIND_PROGRESS))
    # R3616 (AC-LADJ1): a bare `broken=N` in this station is a count without
    # its qualification. The owner of that judgement answers it here, and its
    # verdict never moves this face's exit code (a reading, not a ruling).
    if report["broken"]:
        reading = chain_reading(path)
        if reading is None:
            sys.stdout.write("QA-LEDGER adjudication chain=UNADJUDICATED\n")
        else:
            sys.stdout.write(
                "QA-LEDGER adjudication chain=%s partial=%d declared=%d "
                "unexplained=%d source=qa_chain_diagnose\n"
                % (reading["verdict"], reading["partial"],
                   reading["declared"], reading["unexplained"]))
    return 0 if report["verdict"] == "OK" else 2


def read_source(raw):
    """AC-QAL1: decode whatever the shell produced, without guessing silently.

    AC-QALB8 (R2807): a decoded NUL is never legitimate in an evidence log. It
    means the source was BOM-less UTF-16, the one encoding the old fallback
    could not tell from plain text - it used to be accepted as readable, land a
    NUL-riddled file, and report VERDICT PASS. Refusing is the honest face: the
    endianness cannot be verified without a BOM, so the writer names the
    corruption instead of storing it.
    """
    if raw.startswith(BOM_UTF8):
        text = raw[len(BOM_UTF8):].decode("utf-8")
    elif raw.startswith(BOM_16LE):
        text = raw[2:].decode("utf-16-le")
    elif raw.startswith(BOM_16BE):
        text = raw[2:].decode("utf-16-be")
    else:
        for enc in ("utf-8", "gb18030"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("undecodable source bytes")
    if "\x00" in text:
        raise ValueError("source carries NUL bytes (BOM-less UTF-16 is not "
                         "an evidence dialect)")
    return text


def normalize(text):
    """AC-QAL1: LF only, exactly one trailing newline."""
    out = text.replace("\r\n", "\n").replace("\r", "\n")
    out = out.rstrip("\n")
    return out + "\n"


def check_name(name):
    """AC-QAL6: one flat file name, never a path. AC-QAL8: never a flag."""
    if not name or not name.strip():
        raise ValueError("empty name")
    if "/" in name or "\\" in name or ":" in name:
        raise ValueError("name must be a flat file name, got %r" % name)
    if name in (".", "..") or name.startswith("."):
        raise ValueError("name must not start with a dot, got %r" % name)
    if name.startswith("-"):
        # AC-QAL8 (pinned at R2809 BEFORE this branch): a leading dash made
        # `python tools/qa_log.py --help` write qa/--help at 1 byte, twice -
        # R2808 recorded it and R2809 reproduced it. The pollution was silent
        # because a one-byte file lands in the healthy tee dialect, which the
        # writer census never flags. main() routes its three known flags
        # before a name reaches this guard, so nothing legitimate is blocked.
        raise ValueError("name must not start with a dash, got %r" % name)


def check_destination(directory):
    """R3215 (AC-QALB21): evidence written inside the repo but outside qa/ is
    not evidence.

    Measured before this guard: the writer took any destination, and the three
    readers enumerate qa/*.log only - so a .log landed in the healthy dialect at
    a repo path of the caller's choosing and no face ever judged it. The cost
    was measured before the law: exactly one production call site passes a
    directory (tools/battery_shard.py passes QA_DIR itself), the shipped writer
    calls omit it, and every test world passes a tempfile.mkdtemp path outside
    the repo, so nothing legitimate reddens.

    QA and REPO are read at call time, not captured at import, because a suite
    points QA at a private world; a default bound at import time would keep
    aiming at the real qa/ and the refusal would name the wrong thing.
    """
    if not directory:
        raise ValueError("E_DEST_INSIDE_REPO destination directory is required")
    dest = os.path.normcase(os.path.realpath(directory))
    qa = os.path.normcase(os.path.realpath(QA))
    repo = os.path.normcase(os.path.realpath(REPO))
    if dest == qa:
        return
    if dest == repo or dest.startswith(repo + os.sep):
        raise ValueError(
            "E_DEST_INSIDE_REPO destination must be the qa/ dir or a path "
            "outside the repo, got %r (the writer census, the pre-commit "
            "evidence gate and the closeout files= count enumerate qa/*.log "
            "only, so a .log written here would land in the healthy dialect "
            "and never be judged)" % directory)


def write_atomic(directory, name, text):
    """AC-QAL3: tmp in the destination dir, then one replace.

    AC-QALB21 (R3215): the destination is judged here, the single choke point
    both write faces pass through.
    """
    check_destination(directory)
    payload = text.encode("utf-8")
    final = os.path.join(directory, name)
    fd, tmp = tempfile.mkstemp(prefix=".qa_log_", suffix=".tmp", dir=directory)
    try:
        with io.open(fd, "wb", closefd=True) as handle:
            handle.write(payload)
        os.replace(tmp, final)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return final


def verify_written(path):
    """AC-QAL2: the file proves itself, so a bad write cannot be claimed good."""
    raw = io.open(path, "rb").read()
    if raw.startswith(BOM_UTF8) or raw.startswith(BOM_16LE) or raw.startswith(BOM_16BE):
        raise ValueError("BOM survived the write")
    if b"\r" in raw:
        raise ValueError("CR survived the write")
    if not raw:
        raise ValueError("empty file")
    if not raw.endswith(b"\n"):
        raise ValueError("missing trailing newline")
    text = raw.decode("utf-8")
    return {
        "bytes": len(raw),
        "lines": len(text.splitlines()),
        "sha256": hashlib.sha256(raw).hexdigest()[:16],
    }


def classify(raw):
    """AC-QAL4: name the dialect of an existing file, read-only.

    AC-QALB8 (R2807): a BOM-less UTF-16 file has no BOM to catch it and decodes
    as valid utf-8 once the NULs are ignored, so it used to be named utf-8/lf -
    the healthy dialect - by both this face and the writer census. NUL is the
    signature that catches it, and it is named here rather than absorbed.
    """
    if raw.startswith(BOM_16LE) or raw.startswith(BOM_16BE):
        return "ps-utf16"
    if raw.startswith(BOM_UTF8):
        return "utf-8-bom"
    if b"\x00" in raw:
        return "nul-bytes"
    if b"\r" in raw:
        return "crlf"
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return "undecodable"
    if raw and not raw.endswith(b"\n"):
        return "no-trailing-newline"
    return "utf-8/lf"


PROOF_LINE_RE = re.compile(
    r"^LOG OK path=(\S+) bytes=(\d+) lines=(\d+) sha16=([0-9a-f]{16})$")


def mark_carried_proofs(text):
    """R3203 (AC-QAL9): a proof line carried in by a relog is not this
    file's proof.

    Measured before this function existed: a generator that prints
    "LOG OK path=... bytes=... lines=... sha16=..." on stdout had its
    whole stdout stored through this writer, and the new file carried
    that line unchanged while its own sha16 was a different number
    (761 bytes, carried 271ba9eb7b2d1230, own 4210a333be0b1d92). The
    dialect faces cannot see it - classify() answered utf-8/lf and
    verify_written() read back clean - so the only reader who could
    catch it was a human comparing hashes.

    The line is kept, never dropped (the information is real: it proves
    another file), and prefixed with CARRIED so no reader can take it for
    this log's own proof. A line that does not match the exact shipped
    shape is left alone: guessing at a near miss would be a second guess
    on top of the first.
    """
    carried = 0
    out = []
    for line in text.split("\n"):
        if PROOF_LINE_RE.match(line):
            out.append("CARRIED " + line)
            carried += 1
        else:
            out.append(line)
    if not carried:
        return text, 0
    return "\n".join(out), carried


def count_carried_proofs(text):
    """R3204 (AC-QAL10): how many carried proofs a body quotes, exact shapes.

    A reader could see a CARRIED line but no machine face could count it:
    --check answered the same text for 0, 1 and 2 of them, and both the
    writer census and the pre-commit gate judge the dialect class only. So
    the count is named here. Exact shape after the prefix, same rule as
    mark_carried_proofs: a near miss is not a count.
    """
    carried = 0
    for line in text.split("\n"):
        if line.startswith("CARRIED ") and PROOF_LINE_RE.match(line[8:]):
            carried += 1
    return carried


def count_bare_proofs(text):
    """R3205 (AC-QAL11): how many UNMARKED proof lines a body carries.

    The same exact shape mark_carried_proofs marks, asked without the
    CARRIED prefix. A bare line proves some other file and reached this body
    without going through do_write - measured today the only such door is
    battery_shard.stream_evidence, which opens the file in place. Counting
    it is not a verdict about the body, only a name for what is in it.
    """
    bare = 0
    for line in text.split("\n"):
        if PROOF_LINE_RE.match(line):
            bare += 1
    return bare


def check_log_suffix(name):
    """R3213 (AC-QAL12): an evidence file no reader enumerates is not evidence.

    Measured before this guard (read-only probe over the shipped tree):
    fifty-five enumerations filter on endswith(".log") - qa_writer_census
    at three sites, tools/hooks/pre_commit_gate.py on the staged set, and
    the closeout `files=` count which reads the census line - so qa/NAME
    without the suffix landed in the healthy dialect, was skipped by every
    one of them, and `--check NAME.log` could not find it either. The cost
    was measured before the law landed: every documented invocation names a
    .log file and battery_shard's evidence_name() adds no suffix, so this
    refusal reddens no existing shipped call site.

    Write face only. do_check keeps reading any flat name, because the one
    existing suffixless artifact (round-R2835-closeout) must stay readable:
    the defect is born at the write, so that is where it is stopped.
    """
    if not name.endswith(".log"):
        raise ValueError(
            "name must end with .log, got %r (the writer census, the "
            "pre-commit evidence gate and the closeout files= count all "
            "enumerate only *.log, so this file would land and never be "
            "judged; --check still reads an existing suffixless file)" % name)


def do_write(name, source_bytes, directory=None):
    """AC-QALB21 (R3215): the default destination is QA resolved at call time.

    A default captured at import time would keep pointing at the real qa/ even
    after a suite points QA at a private world, so the guard would refuse the
    world the suite just asked for and the writer would aim somewhere else.
    """
    if directory is None:
        directory = QA
    check_name(name)
    check_log_suffix(name)
    text = normalize(read_source(source_bytes))
    text, carried = mark_carried_proofs(text)
    # AC-QALB24 (R3216): a same-name rewrite used to be silent - write_atomic
    # replaces the whole file and the only receipt named the NEW bytes, so the
    # evidence that existed before the write survived nowhere: not in stdout,
    # not in the read-back proof, not in the census (measured: 72 rewrite
    # events over 69 shipped *.log paths, old sha16 gone from disk). The old
    # identity is read here, before the replace, and announced below because
    # a refusal would have blocked that entire re-land workflow.
    previous = None
    prev_kind = PREV_KIND_EVIDENCE
    final = os.path.join(directory, name)
    if os.path.isfile(final):
        try:
            raw_prev = io.open(final, "rb").read()
            previous = (len(raw_prev), hashlib.sha256(raw_prev).hexdigest()[:16])
            prev_kind = previous_kind(raw_prev)
        except OSError:
            previous = None
    path = write_atomic(directory, name, text)
    proof = verify_written(path)
    if carried:
        sys.stdout.write(
            "QA-LOG CARRIED proofs=%d (a LOG OK line names another file, so "
            "it is marked CARRIED and is not this log's proof)\n" % carried)
    if previous is not None:
        sys.stdout.write(
            "QA-LOG REPLACED name=%s old_bytes=%d old_sha16=%s new_bytes=%d "
            "new_sha16=%s\n"
            % (name, previous[0], previous[1], proof["bytes"],
               proof["sha256"]))
    sys.stdout.write(
        "QA-LOG WROTE name=%s bytes=%d lines=%d sha256=%s dialect=utf-8/lf "
        "VERDICT PASS\n"
        % (name, proof["bytes"], proof["lines"], proof["sha256"]))
    if previous is not None:
        # R3217 (AC-QALB27/29): the announcement above is stdout only, so the
        # record goes into a machine-readable ledger as well. A ledger that
        # cannot be written still leaves the evidence on disk, but the round
        # must not read as clean: the failure is named and the rc is 2.
        try:
            record_replacement(directory, name, previous, proof, prev_kind)
        except (OSError, ValueError) as exc:
            sys.stdout.write(
                "QA-LOG REPLACEMENT-RECORD-FAILED name=%s reason=%s "
                "(the file landed, the record did not)\n" % (name, exc))
            return 2
    return 0


def do_check(name):
    check_name(name)
    path = os.path.join(QA, name)
    if not os.path.exists(path):
        sys.stdout.write("QA-LOG RED name=%s reason=missing\n" % name)
        return 2
    raw = io.open(path, "rb").read()
    dialect = classify(raw)
    if dialect != "utf-8/lf":
        sys.stdout.write("QA-LOG RED name=%s dialect=%s bytes=%d expected=utf-8/lf\n"
                         % (name, dialect, len(raw)))
        return 2
    body = raw.decode("utf-8")
    sys.stdout.write("QA-LOG OK name=%s dialect=utf-8/lf bytes=%d carried=%d "
                     "bare_proofs=%d\n"
                     % (name, len(raw), count_carried_proofs(body),
                        count_bare_proofs(body)))
    return 0


def selftest():
    """AC-QAL5 + AC-QAL7: fixtures only, and the R2775 sample must replay."""
    passes = 0
    fails = 0

    def check(ok, label):
        nonlocal passes, fails
        if ok:
            passes += 1
            sys.stdout.write("PASS %s\n" % label)
        else:
            fails += 1
            sys.stdout.write("FAIL %s\n" % label)

    tmp = tempfile.mkdtemp(prefix="qalog_")
    try:
        # ut16 + BOM + CRLF source becomes plain LF
        src16 = b"\xff\xfe" + "a\r\nb\r\n".encode("utf-16-le")
        text = normalize(read_source(src16))
        check(text == "a\nb\n", "qal1-utf16-bom-crlf-normalized")

        # a source without a trailing newline gains exactly one
        check(normalize(read_source(b"a\nb")) == "a\nb\n", "qal1-trailing-newline-added")

        # a read-back proof that fails is a refusal, not a claim
        p = write_atomic(tmp, "probe.log", "x\n")
        check(verify_written(os.path.join(tmp, p))["bytes"] == 2
              and verify_written(os.path.join(tmp, p))["lines"] == 1,
              "qal2-readback-proof")

        # no tmp survivor after a successful write
        leftovers = [n for n in os.listdir(tmp) if n.endswith(".tmp")]
        check(leftovers == [], "qal3-atomic-no-tmp-left")

        # an injected CR must be caught by the read-back proof
        bad = os.path.join(tmp, "bad.log")
        io.open(bad, "wb").write(b"a\r\nb\n")
        caught = False
        try:
            verify_written(bad)
        except ValueError:
            caught = True
        check(caught, "qal2-cr-refused")

        # the classifier must redden exactly the R2775 shape
        plant = os.path.join(tmp, "plant.log")
        io.open(plant, "wb").write(b"\xff\xfe" + "PASS x\r\n".encode("utf-16-le"))
        check(classify(io.open(plant, "rb").read()) == "ps-utf16",
              "qal4-utf16-classified-red")

        # AC-QAL6 name refusals
        refused = 0
        for name in ("", "sub/dir.log", "C:x.log", "..\\x.log"):
            try:
                check_name(name)
            except ValueError:
                refused += 1
        check(refused == 4, "qal6-bad-names-refused")

        # AC-QAL5 replay the archived original against the committed repair
        arch = os.path.join(REPO, "logs", "qa-encoding-preop-R2775",
                            "index-newest-band-R2775.log.utf16le")
        live = os.path.join(QA, "index-newest-band-R2775.log")
        if os.path.exists(arch) and os.path.exists(live):
            replayed = normalize(read_source(io.open(arch, "rb").read()))
            on_disk = io.open(live, "rb").read().decode("utf-8")
            check(replayed == on_disk, "qal5-r2775-sample-replays-byte-equal")
        else:
            sys.stdout.write("INFO qal5-sample-absent archive=%s live=%s\n"
                             % (os.path.exists(arch), os.path.exists(live)))

        # R3203 (AC-QAL9): a carried proof line is marked, never certified.
        # Measured before the repair: a relog of a generator's stdout kept
        # "LOG OK ... sha16=<other file>" verbatim inside a file whose own
        # sha16 was a different number.
        proof = (b"PASS one\n"
                 b"LOG OK path=qa/preview.log bytes=661 lines=9 "
                 b"sha16=271ba9eb7b2d1230\n")
        do_write("carried-qal9.log", proof, directory=tmp)
        first = io.open(os.path.join(tmp, "carried-qal9.log"), "rb").read()
        do_write("carried2-qal9.log", first, directory=tmp)
        second = io.open(os.path.join(tmp, "carried2-qal9.log"), "rb").read()
        plain = b"PASS x\n"
        do_write("plain-qal9.log", plain, directory=tmp)
        plain_out = io.open(os.path.join(tmp, "plain-qal9.log"), "rb").read()
        near = (b"LOG OK path=qa/preview.log bytes=six lines=9 "
                b"sha16=271ba9eb7b2d1230\n")
        do_write("near-qal9.log", near, directory=tmp)
        near_out = io.open(os.path.join(tmp, "near-qal9.log"), "rb").read()
        check(first.count(b"CARRIED LOG OK path=") == 1
              and b"\nLOG OK path=" not in first
              and second.count(b"CARRIED") == 1
              and plain_out == plain
              and near_out == near,
              "qal9-carried-proof-marked-once-and-only-exact-shapes")
    finally:
        for name in os.listdir(tmp):
            try:
                os.unlink(os.path.join(tmp, name))
            except OSError:
                pass
        try:
            os.rmdir(tmp)
        except OSError:
            pass

    total = passes + fails
    sys.stdout.write("VERDICT %s %d/%d qa_log selftest (qa/ untouched)\n"
                     % ("PASS" if fails == 0 else "FAIL", passes, total))
    return 0 if fails == 0 else 2


def main(argv):
    args = list(argv[1:])
    if not args:
        sys.stdout.write("usage: qa_log.py NAME [--from FILE] | --check NAME | "
                         "--ledger-check [PATH] | --selftest\n")
        return 2
    if args[0] == "--selftest":
        return selftest()
    if args[0] == "--check":
        if len(args) != 2:
            sys.stdout.write("QA-LOG REFUSED --check needs exactly one name\n")
            return 2
        return do_check(args[1])
    if args[0] == "--ledger-check":
        if len(args) > 2:
            sys.stdout.write("QA-LOG REFUSED --ledger-check takes at most one "
                             "path\n")
            return 2
        return do_ledger_check(args[1] if len(args) == 2 else None)
    name = args[0]
    source = None
    if "--from" in args:
        i = args.index("--from")
        if i + 1 >= len(args):
            sys.stdout.write("QA-LOG REFUSED --from needs a path\n")
            return 2
        source = io.open(args[i + 1], "rb").read()
    else:
        source = sys.stdin.buffer.read()
    try:
        return do_write(name, source)
    except (ValueError, OSError) as exc:
        sys.stdout.write("QA-LOG REFUSED name=%s reason=%s\n" % (name, exc))
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
