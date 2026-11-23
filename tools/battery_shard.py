"""battery_shard - supervised slice runner over the battery registry (R2797).

AC-BSH1..AC-BSH8 were pinned in src/os/backlog.md BEFORE this file existed.

Why this exists: src/sandbox/reconcile_all.py is all-or-nothing. It carries no
label selector and no shard mode, so the only way to learn whether a FAMILY of
suites is green is a 4000-5900s leg that a window must supervise end to end.
Legs launched by windows that could not supervise them died truncated without a
closing row (R2779 pid 77376 gone mid-suite; R2780 refused the adoption by
measurement), which made "full battery owed" a structurally permanent debt.

This tool runs a NAMED SUBSET of the same registry rows with the SAME command
the battery uses, and prints its own closing SHARD row. It is deliberately not
a battery: its output can never be adopted as a full leg by
tools/adoption_preflight.py, which keys on a closing "BATTERY rc=" row.

Usage:
  python tools/battery_shard.py --match os-ledger --match ledger
  python tools/battery_shard.py --exact ledger --exact member --exact pay
  python tools/battery_shard.py --match os-lobby --dry
  python tools/battery_shard.py --match os-ledger --evidence battery-shard-R2797.log
  python tools/battery_shard.py --claim full        # refused, rc=2
  python tools/battery_shard.py --check --evidence battery-shard-R2797.log

Source discipline: pure ASCII, stdlib only, no clock literal, no network, no
shell (the only child processes are the selected suite files themselves).
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_REL = os.path.join("src", "sandbox", "reconcile_all.py")
QA_LOG_REL = os.path.join("tools", "qa_log.py")
QA_DIR = os.path.join(ROOT, "qa")
SUITE_LINE = re.compile(r"(?m)^SUITE\s+(PASS|FAIL)\s+(\d+)\s*/\s*(\d+)")
# A row may state its numbers without a verdict word ("SUITE 8/8"). The runner
# derives the verdict from p==t; "green" is NOT accepted, because it is not the
# law's vocabulary and guessing it would invent a word the suite never said.
SUITE_LINE_NUM = re.compile(
    r"(?m)^SUITE\s+(\d+)\s*/\s*(\d+)(?:\s+(PASS|FAIL))?\s*$")
# The same pair, joined by other punctuation: "SUITE PASS (7/7)",
# "SUITE PASS (6/6 criteria green)", "SUITE PASS: 7/7", "SUITE PASS - 19/19".
SUITE_LINE_PUNCT = re.compile(
    r"(?m)^SUITE\s+(PASS|FAIL)\s*[(:-]\s*(\d+)\s*/\s*(\d+)")
# A labelled pair names the suite instead of the verdict, so the verdict is
# derived from p==t exactly as the numbers-only row above: "SUITE apidev: 7/7".
# The lookahead keeps it off a verdict word, which the row above already reads.
SUITE_LINE_LABEL = re.compile(
    r"(?m)^SUITE\s+(?!PASS\b|FAIL\b)[A-Za-z0-9_.-]+:\s*(\d+)\s*/\s*(\d+)")
# A counter row states the verdict as counts: "SUITE RESULT passes=6 fails=0
# criteria=6", "SUITE PASS criteria=6 pass=6 fail=0", "SUITE PASS exit=0
# pass-lines=6 fail-lines=0 criteria=6", "SUITE x expected-criteria=6 pass=6
# fail=0". Field order varies, so each counter is read on its own; the verdict
# follows the FAIL count, never the word, because passes may be assertions
# rather than criteria and p>t must not be read as a red row.
COUNTER_TOTAL = re.compile(r"(?:expected-criteria|criteria)=(\d+)")
COUNTER_PASS = re.compile(r"(?:passes|pass-lines|pass)=(\d+)")
COUNTER_FAIL = re.compile(r"(?:fails|fail-lines|fail)=(\d+)")
# The same three counts without an equals sign: "SUITE PASS: 6 criteria,
# 6 pass, 0 fail". The words are the binding, so the count must precede them.
COUNTER_WORD_TOTAL = re.compile(r"(\d+)\s+criteria\b")
COUNTER_WORD_PASS = re.compile(r"(\d+)\s+pass\b")
COUNTER_WORD_FAIL = re.compile(r"(\d+)\s+fail\b")
# A suite may own TWO units: the checks it runs and the AC ids the registry
# counts. Two member-side suites already print that pair in one lowercase line
# ("suite: 21 assertions over 8 criteria"), so the
# comparison reads the DECLARED criteria when it is there and keeps the SUITE
# pair's total otherwise. A declaration may never move a verdict or an rc.
CRITERIA_UNIT = re.compile(
    r"(?m)^suite:\s*(\d+)\s+assertions over\s*(\d+)\s+criteria")
# AC-BSGB13: the declaration is normally printed through a format string, so
# this marker selects WHICH suites declare; the numbers are read at runtime.
DECL_PRINTER = re.compile(r"assertions over")
SUITE_ROW = re.compile(r"(?m)^SUITE\b[^\n]*$")
VERDICT_WORD = re.compile(r"^SUITE\s+(PASS|FAIL)\b")


def parse_criteria_unit(text):
    """The criteria count a suite declares about itself, or None."""
    match = CRITERIA_UNIT.search(text)
    return int(match.group(2)) if match else None


def parse_counter_unit(text):
    """The criteria count a SUITE row declares with a counter, or None.

    AC-BSGB22 (R3137): "SUITE PASS 34/34 arms=34 criteria=7" states which of
    its numbers counts what, yet the pair was read first and compared to the
    registry row, so the suite was graded as an undeclared disagreement and
    that leg went red on six consecutive windows. Only a row that starts with
    SUITE is read (SUITE_ROW, which carries the \\b boundary): R3137 measured a
    docstring line "SUITES wiring (... criteria=6)" in the tree, and a reader
    without the boundary would let a comment pass itself off as a declaration.
    """
    for row in SUITE_ROW.finditer(text):
        counter = COUNTER_TOTAL.search(row.group(0))
        if counter:
            return int(counter.group(1))
    return None


def _counter_row(line):
    """(verdict, passed, total) from a counter row, or None when incomplete.

    A row that states no FAIL count cannot say its verdict from counts, so it is
    refused rather than guessed ("SUITE PASS 7 checks" is that case).
    """
    if not line.startswith("SUITE"):
        return None
    total = COUNTER_TOTAL.search(line)
    passed = COUNTER_PASS.search(line)
    failed = COUNTER_FAIL.search(line)
    if not (total and passed and failed):
        total = COUNTER_WORD_TOTAL.search(line)
        passed = COUNTER_WORD_PASS.search(line)
        failed = COUNTER_WORD_FAIL.search(line)
    if not (total and passed and failed):
        return None
    word = VERDICT_WORD.match(line)
    if int(failed.group(1)) > 0:
        return "FAIL", int(passed.group(1)), int(total.group(1))
    if word and word.group(1) == "FAIL":
        return "FAIL", int(passed.group(1)), int(total.group(1))
    return "PASS", int(passed.group(1)), int(total.group(1))


def _paired(word, passed, total):
    """A verdict word beside a pair, except that a PASS word over p<t is a lie.

    A row that claims PASS while a criterion is missing is read FAIL: the pair
    is real evidence and reddening a contradictory row can never hide a red
    suite. The reverse (passes over criteria) is a counting-unit mismatch, not a
    failure, so it keeps its word.
    """
    if word == "PASS" and passed < total:
        return "FAIL", passed, total
    return word, passed, total


def parse_suite_row(text):
    """(verdict, passed, total) from a suite body, or None.

    An explicit verdict word always wins; a numbers-only row derives PASS when
    passed == total and FAIL otherwise. The other row skins the registry still
    carries are read here, at the one authority the runner, the audit and the
    census all ask, so a suite that names its verdict in its own dialect stops
    being invisible to every machine reader at once.
    """
    match = SUITE_LINE.search(text)
    if match:
        return _paired(match.group(1), int(match.group(2)), int(match.group(3)))
    found = []
    for match in SUITE_LINE_PUNCT.finditer(text):
        verdict, passed, total = _paired(match.group(1), int(match.group(2)),
                                         int(match.group(3)))
        found.append((match.start(), 2, verdict, passed, total))
    for match in SUITE_LINE_LABEL.finditer(text):
        passed, total = int(match.group(1)), int(match.group(2))
        found.append((match.start(), 1, "PASS" if passed == total else "FAIL",
                      passed, total))
    for match in SUITE_ROW.finditer(text):
        row = _counter_row(match.group(0))
        if row:
            found.append((match.start(), 3) + row)
    if found:
        _, _, verdict, passed, total = max(found)
        return verdict, passed, total
    rows = SUITE_LINE_NUM.findall(text)
    if not rows:
        return None
    passed, total, word = rows[-1]
    if word:
        return word, int(passed), int(total)
    return ("PASS" if passed == total else "FAIL"), int(passed), int(total)


class Refuse(Exception):
    """A named refusal that must reach the caller as rc=2, never as rc=1."""


def load_module(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def registry():
    """AC-BSH1: rows, criteria, base and caps come from the registry itself."""
    mod = load_module(os.path.join(ROOT, REGISTRY_REL), "_bs_registry")
    rows = []
    seen = set()
    for row in mod.SUITES:
        label = row[0]
        rel = row[1]
        try:
            crit = int(row[2])
        except (TypeError, ValueError, IndexError):
            crit = 0
        if label in seen:
            raise Refuse("E_DUP_LABEL %s" % label)
        seen.add(label)
        rows.append((label, rel, crit))
    base = getattr(mod, "BASE", os.path.join(ROOT, "src", "sandbox"))
    cap = int(getattr(mod, "SUITE_TIMEOUT_S", 600))
    overrides = dict(getattr(mod, "SUITE_TIMEOUT_OVERRIDES", None) or {})
    return rows, base, cap, overrides


def select(rows, prefixes, limit, exacts=()):
    """AC-BSH2: a case-sensitive label PREFIX test, in registry order.

    AC-EXL1/AC-EXL2 (R2843): labels may also be named EXACTLY. A prefix test
    cannot reach a bare label such as "ledger" without also dragging in every
    "ledger-*" suite (measured: 336 suites), and a family slice drawn by
    "does not start with ledger-/member-/pay-" excludes the bare labels too -
    so three suites totalling 43 criteria were reachable by no slice at all.
    Exact names are a union with the prefixes, never a second selection law:
    order stays the registry's, and an exact name the registry does not carry
    refuses by name rather than silently selecting nothing.
    """
    exacts = [e for e in (exacts or ()) if e]
    if prefixes or exacts:
        missing = [e for e in exacts if not any(r[0] == e for r in rows)]
        unmatched = [p for p in prefixes if not any(r[0].startswith(p) for r in rows)]
        if missing or unmatched:
            raise Refuse("E_NO_MATCH %s" % ",".join(missing + unmatched))
        wanted = set(exacts)
        picked = [r for r in rows
                  if r[0] in wanted or any(r[0].startswith(p) for p in prefixes)]
    else:
        picked = list(rows)
    if limit and limit > 0:
        picked = picked[:limit]
    return picked


DETAIL_LINE = re.compile(r"(?m)^[ \t]*(?:\|[ \t]*)?(PASS|FAIL)\b")


def run_one(base, label, rel, cap, overrides, leg_cap=None):
    """AC-BSH3: the battery's own invocation, byte for byte in behaviour.

    The cap law is the battery's own suite_timeout(): one declared override per
    suite LABEL, else the named constant. Override keys are labels, measured on
    the registry (one key today: ledger-apimarket-refundregister -> 900).

    AC-BTG1 (R2865): leg_cap is a LEG-level ceiling that can only LOWER the
    effective per-suite duration, never raise it - an override of 900 under a
    leg cap of 90 still runs 90. It exists because the deep os-probe-seam rows
    measured 160.1s and 257.3s inside a 600s cap (R2864), so a leg over them
    cannot fit a window while every row is allowed the full battery budget;
    a bounded leg grades a slow row as a NAMED timeout instead of leaving the
    family unmeasured.
    """
    path = os.path.join(base, rel)
    duration = int(overrides.get(label, cap))
    if leg_cap:
        duration = min(duration, int(leg_cap))
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    started = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, path], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8",
            errors="replace", cwd=os.path.dirname(path), timeout=duration,
            env=env)
        code, out = proc.returncode, proc.stdout or ""
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        out = (out or "").rstrip("\n")
        marker = "TIMEOUT suite exceeded the %ds per-suite cap" % duration
        code = 124
        out = (out + "\n" + marker) if out else marker
    return code, out, time.time() - started


def evidence_name(raw):
    """AC-BSH6: evidence lives under qa/ and nowhere else."""
    name = os.path.basename(str(raw))
    if not name or name != str(raw).replace("\\", "/").split("/")[-1]:
        raise Refuse("E_EVIDENCE_PATH %s" % raw)
    parent = os.path.dirname(str(raw).replace("\\", "/"))
    if parent not in ("", "qa"):
        raise Refuse("E_EVIDENCE_PATH %s" % raw)
    return name


_QA_LOG_CACHE = []


def qa_log_module():
    """The writer that owns the qa/ birth site, loaded once per process."""
    if not _QA_LOG_CACHE:
        _QA_LOG_CACHE.append(
            load_module(os.path.join(ROOT, QA_LOG_REL), "_bs_qa_log"))
    return _QA_LOG_CACHE[0]


def write_evidence(name, text):
    qa_log = qa_log_module()
    qa_log.do_write(name, text.encode("utf-8"), directory=QA_DIR)
    path = os.path.join(QA_DIR, name)
    proof = qa_log.verify_written(path)
    return proof


def _progress_name(path):
    """AC-QALB18 (R3214): the in-place progress door is still an evidence door.

    Measured before this guard (read-only probe over private temp): this door
    takes a FULL path and asked neither question its siblings ask - a suffixless
    qa/NAME landed in the healthy dialect where the writer census, the
    pre-commit gate and the closeout files= count all skip it by construction,
    and a path pointing outside qa/ landed the same bytes anywhere on disk.
    evidence_name() pins qa/ and the CLI already asks check_log_suffix before
    any suite runs, so this closes the door for a DIRECT caller; it costs no
    existing evidence a byte, because every shipped call site passes
    os.path.join(QA_DIR, evidence_name(...)). QA_DIR is read at call time so a
    suite can point the door at a private directory instead of the live tree.
    """
    directory = os.path.dirname(os.path.abspath(path))
    if (os.path.normcase(os.path.realpath(directory))
            != os.path.normcase(os.path.realpath(QA_DIR))):
        raise Refuse("E_STREAM_PATH %s" % path)
    name = os.path.basename(path)
    qa_log = qa_log_module()
    qa_log.check_name(name)
    qa_log.check_log_suffix(name)
    return name


def stream_evidence(path, text):
    """AC-BSGB15 (R2886): progress lands on disk while the leg is still running.

    Measured fact this exists for: the evidence file used to be written ONCE,
    after the last suite, so a leg killed for silence left ZERO evidence - two
    285-suite attempts died that way at R2885 with the file never created. This
    writes the partial form in place (header state=RUNNING plus every finished
    row) and fsyncs it; the final artifact still goes through write_evidence so
    the qa_log birth site keeps owning the shipped file.

    AC-QALB14 (R3206): this in-place door bypassed do_write, so it was the one
    place a qa/ file could grow an UNMARKED proof line - a line that proves
    some other file and looks self-certifying in this one. The same law now
    runs here: the text is marked before it lands. A progress body carries no
    proof shapes today, so every measured shape lands byte for byte as before;
    a body that does carry one gets the CARRIED prefix instead of a silent
    bare line. The mark is idempotent, and the write stays in place with its
    fsync so a killed leg still leaves a readable RUNNING file.
    """
    _progress_name(path)
    text, _carried = qa_log_module().mark_carried_proofs(text)
    # R3371 (AC-QCH1): the partial declares what it is, so the replacement row
    # it later causes can say prev_kind=progress instead of reading as a lost
    # record. The sentinel line is never part of the final artifact - that one
    # still goes through write_evidence and the qa_log birth site.
    sentinel = qa_log_module().PROGRESS_SENTINEL
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(sentinel + "\n")
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())


def do_check(name):
    """Read the evidence back and recompute its counts from its own rows."""
    path = os.path.join(QA_DIR, name)
    if not os.path.exists(path):
        print("SHARD-CHECK RED reason=missing name=%s" % name)
        return 2
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        print("SHARD-CHECK RED reason=undecodable name=%s" % name)
        return 2
    rows = [l for l in text.splitlines() if l.startswith("SHARD row ")]
    closing = [l for l in text.splitlines() if l.startswith("SHARD rc=")]
    battery = [l for l in text.splitlines() if l.startswith("BATTERY")]
    fails = []
    if not rows:
        fails.append("E_NO_ROWS")
    if len(closing) != 1:
        fails.append("E_CLOSING_ROWS=%d" % len(closing))
    if battery:
        fails.append("E_BATTERY_LINE=%d" % len(battery))
    executed = len(rows)
    green = len([l for l in rows if re.search(r"\brc=0\b", l)])
    if closing and not fails:
        announced = re.search(r"\bexecuted=(\d+)\b", closing[0])
        if not announced or int(announced.group(1)) != executed:
            fails.append("E_EXECUTED_MISMATCH")
        greens = re.search(r"\bgreen=(\d+)\b", closing[0])
        if not greens or int(greens.group(1)) != green:
            fails.append("E_GREEN_MISMATCH")
        verdict = re.search(r"\bSHARD rc=(\d+)\b", closing[0])
        expect = 0 if green == executed else 2
        if not verdict or int(verdict.group(1)) != expect:
            fails.append("E_VERDICT_MISMATCH")
    print("SHARD-CHECK name=%s rows=%d green=%d bytes=%dB"
          % (name, executed, green, len(raw)))
    if fails:
        print("SHARD-CHECK RED %s" % ",".join(fails))
        return 2
    print("SHARD-CHECK VERDICT PASS")
    return 0


def do_declared_only(rows, base, cap=600, overrides=None,
                     registry_total=None, leg_cap=None):
    """AC-BSGB13: grade every DECLARING suite without paying for a battery.

    Measured fact this mode exists for: a declaration is printed through a
    format string ("suite: %d assertions over %d criteria"), so no static scan
    can read its NUMBERS. What a static scan can read is which suites carry the
    printer at all, so that is the selector: the sweep runs exactly those
    suites and compares each one's own declared criteria against its registry
    row. A suite that carries the printer but prints no declaration is named as
    no-declaration rather than counted as agreeing; absence is never a pass.
    """
    overrides = overrides or {}
    carriers = []
    unreadable = []
    for label, rel, crit in rows:
        path = os.path.join(base, rel)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            unreadable.append(label)
            continue
        if DECL_PRINTER.search(text):
            carriers.append((label, rel, crit))
    lines = []
    print("DECL scope=SWEEP registry_suites=%d carriers=%d unreadable=%d"
          % (len(rows), len(carriers), len(unreadable)))
    checked = 0
    silent = []
    mismixed = []
    reds = []
    started = time.time()
    for label, rel, crit in carriers:
        code, out, secs = run_one(base, label, rel, cap, overrides, leg_cap)
        declared = parse_criteria_unit(out)
        if declared is None:
            silent.append(label)
            row = ("DECL row %s rc=%d suite=none declared=none registry=%d "
                   "no-declaration %.1fs" % (label, code, int(crit), secs))
            flex = "no-declaration"
        else:
            checked += 1
            ok = (declared == int(crit))
            flex = "ok" if ok else "mismatch"
            if not ok:
                mismixed.append("%s:%d!=%d" % (label, declared, int(crit)))
            row = ("DECL row %s rc=%d declared=%d registry=%d %s %.1fs"
                   % (label, code, declared, int(crit), flex, secs))
        if code != 0:
            reds.append("%s:rc=%d" % (label, code))
        print(row)
        lines.append(row)
    elapsed = time.time() - started
    rc = 1 if (mismixed or silent or reds) else 0
    total = len(rows) if registry_total is None else int(registry_total)
    closing = ("DECL-SWEEP rc=%d swept=%d registry_suites=%d carriers=%d "
               "declared=%d silent=%d mismatched=%d unreadable=%d red=%d "
               "elapsed=%.1fs"
               % (rc, len(carriers), total, len(carriers), checked,
                  len(silent), len(mismixed), len(unreadable), len(reds),
                  elapsed))
    print(closing)
    lines.insert(0, "DECL scope=SWEEP registry_suites=%d carriers=%d"
                 % (total, len(carriers)))
    lines.append(closing)
    if mismixed:
        print("DECL disclosure mismatched=%s" % ",".join(mismixed))
        lines.append("DECL disclosure mismatched=%s" % ",".join(mismixed))
    if silent:
        print("DECL disclosure no-declaration=%s" % ",".join(silent))
        lines.append("DECL disclosure no-declaration=%s" % ",".join(silent))
    if reds:
        print("DECL disclosure red=%s" % ",".join(reds))
        lines.append("DECL disclosure red=%s" % ",".join(reds))
    if unreadable:
        print("DECL disclosure unreadable=%s" % ",".join(unreadable))
        lines.append("DECL disclosure unreadable=%s" % ",".join(unreadable))
    return rc, "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--match", action="append", default=[])
    ap.add_argument("--exact", action="append", default=[])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--cap", type=int, default=0)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--declared-only", dest="declared_only",
                    action="store_true")
    ap.add_argument("--claim", default="")
    ap.add_argument("--evidence", default="")
    args = ap.parse_args(argv)
    try:
        return _round(args)
    except Refuse as exc:
        print(str(exc))
        return 2


def _round(args):
    # AC-BSH6: the evidence path is validated BEFORE any suite runs, including
    # in --dry mode, so a bad path can never be discovered after 10 minutes.
    # R3213 (AC-QAL12): the writer refuses a name that does not end with .log,
    # so the same law is asked here rather than discovered at write time; the
    # --check direction keeps reading the writer's existing suffixless artifact.
    if args.evidence:
        evidence_name(args.evidence)
        if not args.check:
            try:
                qa_log_module().check_log_suffix(evidence_name(args.evidence))
            except ValueError as exc:
                raise Refuse("E_EVIDENCE_SUFFIX %s" % exc)

    if args.claim and args.claim.strip().lower() == "full":
        print("E_NOT_FULL a shard cannot claim battery coverage; run the "
              "battery itself and adopt its closing row")
        return 2

    if args.check:
        if not args.evidence:
            print("E_NO_EVIDENCE --check needs --evidence")
            return 2
        return do_check(evidence_name(args.evidence))

    rows, base, cap, overrides = registry()
    # AC-BTG2: a leg cap may only lower the battery's own cap; asking for a
    # RAISE is not an error but a no-op, and the header prints the number
    # actually in force so a reader never has to trust the flag.
    leg_cap = 0
    if args.cap:
        if int(args.cap) < 1:
            raise Refuse("E_CAP --cap needs a positive second count")
        leg_cap = min(int(args.cap), cap)
    if args.declared_only:
        picked = select(rows, args.match, args.limit, args.exact)
        rc, text = do_declared_only(picked, base, cap, overrides, len(rows),
                                    leg_cap)
        if args.evidence:
            proof = write_evidence(evidence_name(args.evidence), text)
            print("DECL evidence name=%s bytes=%d lines=%d sha256=%s "
                  "dialect=utf-8/lf"
                  % (evidence_name(args.evidence), proof["bytes"],
                     proof["lines"], proof["sha256"]))
        return rc
    picked = select(rows, args.match, args.limit, args.exact)
    total_crit = sum(int(r[2]) for r in picked)
    ev_path = (os.path.join(QA_DIR, evidence_name(args.evidence))
               if args.evidence else "")
    # AC-BSGB15 (R2886): the header is printed BEFORE the first suite and it
    # carries the leg STATE, so a reader of a partial file can tell a running
    # leg from a finished one. `state` is appended LAST so every field-order
    # reader written before this round keeps parsing the fields it knows.
    header = ("SHARD scope=SHARD registry_suites=%d registry_criteria=%d "
              "selected=%d selected_criteria=%d cap=%ds leg_cap=%ds "
              "overrides=%d exact=%d state="
              % (len(rows), sum(int(r[2]) for r in rows), len(picked),
                 total_crit, cap, leg_cap, len(overrides), len(args.exact)))
    print(header + "RUNNING", flush=True)
    for label, rel, crit in picked:
        print("SHARD selected %s crit=%d path=%s" % (label, crit, rel),
              flush=True)
    stream = [header + "RUNNING"]
    if ev_path:
        stream_evidence(ev_path, "\n".join(stream) + "\n")
    if args.dry:
        print("SHARD rc=0 scope=SHARD dry=True executed=0 selected=%d" % len(picked))
        return 0

    lines = []
    executed = 0
    green = 0
    crit_run = 0
    crit_checked = 0
    unchecked = []
    mismatch = []
    undeclared = []
    reds = []
    started = time.time()
    for label, rel, crit in picked:
        code, out, secs = run_one(base, label, rel, cap, overrides, leg_cap)
        tokens = DETAIL_LINE.findall(out)
        passes = tokens.count("PASS")
        fails = tokens.count("FAIL")
        # AC-LF6C: absent detail is declared, never implied by a zero count.
        detail = "yes" if (passes + fails) else "none"
        parsed = parse_suite_row(out)
        suite = ("%s %d/%d" % parsed) if parsed else "none"
        # R2859: a suite that declares its own criteria count is compared in
        # the registry's unit; a suite that does not keeps the old reading.
        declared = parse_criteria_unit(out)
        counter = parse_counter_unit(out)
        if declared is not None:
            # AC-BSGB12 (R2859) pins this case deliberately: a suite that STATES
            # its criteria count is compared like-for-like, and a disagreement
            # there is graded by --declared-only. The shard keeps it a footnote
            # and does not move rc, exactly as that criterion requires.
            crit_checked += 1
            if declared != int(crit):
                mismatch.append("%s:%d!=%d" % (label, declared, crit))
        elif counter is not None:
            # AC-BSGB22 (R3137): a row that prints "criteria=<n>" beside its own
            # pair has already declared WHICH number counts what, so the pair's
            # total is no longer a blind spot - it is a different unit stated in
            # the same line. Graded exactly like the lowercase declaration (named
            # footnote, no rc), because AC-BSGB14's red is reserved for a row
            # that declares NOTHING and can therefore be read either way.
            crit_checked += 1
            if counter != int(crit):
                mismatch.append("%s:%d!=%d" % (label, counter, crit))
        elif parsed is not None:
            # AC-BSGB14 (R2881): an UNDECLARED suite whose printed total
            # disagrees with its registry row is the true blind spot - no reader
            # can say which number counts what, and no other mode reddens it.
            crit_checked += 1
            if parsed[2] != int(crit):
                mismatch.append("%s:%d!=%d" % (label, parsed[2], crit))
                undeclared.append("%s:%d!=%d" % (label, parsed[2], crit))
        else:
            # AC-BSGB17/18 (R2919): this row's registry criteria was never
            # compared against anything the suite printed, so a zero mismatch
            # count here is silence rather than agreement. Named, not counted.
            unchecked.append(label)
        executed += 1
        crit_run += int(crit)
        if code == 0:
            green += 1
        else:
            reds.append("%s:rc=%d" % (label, code))
        line = ("SHARD row %s rc=%d pass=%d fail=%d detail=%s suite=%s crit=%d %.1fs%s"
                % (label, code, passes, fails, detail, suite, crit, secs,
                   " timeout=yes" if code == 124 else ""))
        print(line, flush=True)
        lines.append(line)
        # AC-BSGB15: the row reaches disk as it lands, not at the leg's end.
        stream.append(line)
        if ev_path:
            stream_evidence(ev_path, "\n".join(stream) + "\n")
        if code != 0:
            for chunk in out.splitlines()[:40]:
                lines.append("SHARD detail %s %s" % (label, chunk))
    elapsed = time.time() - started
    # AC-BSGB14 (R2881): an UNDECLARED unit disagreement is a RED. It used to be
    # a disclosure only, so a suite whose printed total counts assertions read
    # exactly like a green leg with a footnote when its registry row counts
    # criteria - which is how thirteen labels sat as "carried debt" for
    # twenty-three windows while every one of them already declared the right
    # number. The DECLARED case is NOT touched here: AC-BSGB12 (R2859) pins it
    # to a footnote and --declared-only is the mode that reddens it, so the
    # first draft of this law, which reddened every mismatch, was narrowed on
    # that criterion rather than the criterion being adjusted to it.
    rc = 0 if (green == executed == len(picked)) and not undeclared else 2
    # AC-BSGB21 (R3081): crit_checked alone is a numerator with no denominator,
    # so a reader of this row saw "crit_mismatch=0 checked=4" and could not tell
    # whether the leg compared four rows out of four or four out of forty. The
    # unchecked population is the denominator's other half - every row is in
    # exactly one bucket, so checked+unchecked==executed, and a new field always
    # goes LAST (a positional reader has to move with it).
    closing = ("SHARD rc=%d scope=SHARD selected=%d executed=%d green=%d "
               "criteria=%d crit_mismatch=%d elapsed=%.1fs crit_checked=%d "
               "crit_unchecked=%d"
               % (rc, len(picked), executed, green, crit_run, len(mismatch),
                  elapsed, crit_checked, len(unchecked)))
    print(closing, flush=True)
    # AC-BSGB15: the closing row plus a COMPLETE header are what separate an
    # artifact from a progress note, so a killed leg keeps a truthful RUNNING
    # file and do_check can refuse it without a new field.
    lines.append(closing)
    if undeclared:
        # AC-BSGB14: named as a red, not only as a footnote, because rc=2 above
        # already refuses the leg and a reader must see WHY without diffing the
        # closing line's two numbers.
        print("SHARD red-unit undeclared=%s" % ",".join(undeclared), flush=True)
        lines.append("SHARD red-unit undeclared=%s" % ",".join(undeclared))
    if mismatch:
        print("SHARD disclosure crit_mismatch=%s" % ",".join(mismatch), flush=True)
        lines.append("SHARD disclosure crit_mismatch=%s" % ",".join(mismatch))
    if unchecked:
        # AC-BSGB18 (R2919): a leg whose rows print no criteria has compared
        # NOTHING, and "crit_mismatch=0" alone has been read as "all counts
        # agreed" for rounds. The unrefutable rows are named so the two numbers
        # cannot be read apart from the population they describe.
        print("SHARD disclosure crit_unchecked=%s" % ",".join(unchecked),
              flush=True)
        lines.append("SHARD disclosure crit_unchecked=%s" % ",".join(unchecked))
    if reds:
        print("SHARD red %s" % ",".join(reds), flush=True)
        lines.append("SHARD red %s" % ",".join(reds))
    if args.evidence:
        # AC-BSGB15: the shipped artifact still goes through the qa_log birth
        # site, now carrying the COMPLETE header that supersedes the RUNNING one.
        proof = write_evidence(evidence_name(args.evidence),
                               "\n".join([header + "COMPLETE"] + lines) + "\n")
        print("SHARD evidence name=%s bytes=%d lines=%d sha256=%s dialect=utf-8/lf"
              % (evidence_name(args.evidence), proof["bytes"], proof["lines"],
                 proof["sha256"]))
    return rc


if __name__ == "__main__":
    sys.exit(main())
