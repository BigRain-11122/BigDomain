"""Sandbox suite-matrix doc generator (BigDomain P2 tech-queue head,
R1683; seed = council case C-20261009-02 "substantively stalled, zero
billable" - this CLI is the machine-derived reconciliation/billable
visibility face for the local sandbox).

Single sources of truth, zero hardcoding (F3 law):
  * suite registry + expected criteria -> imported live from
    reconcile_all.SUITES (the runner IS the registry; import, never
    copy - no-reinvent-wheel law, zero registry drift)
  * per-domain billable/config faces   -> the five product config.json
    files, extracted through the declarative pattern file
    suite_matrix_patterns.json (R563 data-externalization precedent;
    every Chinese doc label lives in that data file, not here - the
    encoding law keeps this source pure ASCII)
  * per-suite last-run status           -> parsed from a regression
    evidence log (--evidence PATH; default = the newest eligible
    qa/*.log: exactly one RUNNER PASS plus a complete consistent
    suite block, R1695 naming-gap fix). A suite absent from the
    evidence is labeled no-evidence - fail-closed, never fabricated.

Usage:
    python suite_matrix.py                    # write the doc
    python suite_matrix.py --check           # stale-doc detector
    python suite_matrix.py --evidence qa/sec-batch-R1681.log

--check recomputes the matrix reusing the on-disk doc's generation
stamp (content-only comparison) and byte-compares against the doc on
disk; any drift or missing doc exits 2. A patterns file the shipped
readability gate refuses exits 4 with FAIL readability naming the gate
own code and the label key, and writes no artifact byte.

Pre-registered criteria AC-MX1..AC-MX7: state/queue/tech.md R1683
claim row, registered BEFORE this code (honesty law).
Evidence: qa/suite-matrix-R1683.log.
"""

import argparse
import json
import os
import re
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
QA_DIR = os.path.join(ROOT, "qa")
PATTERNS = os.path.join(BASE, "suite_matrix_patterns.json")
DEFAULT_OUT = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")

sys.path.insert(0, BASE)
import reconcile_all as RA  # suite registry single source of truth

# R2442 (AC-MSPL1..AC-MSPL6, criteria pinned in state/queue/tech.md:508 at
# R2418 BEFORE the code): a render told to follow another document's stamp
# must record that fact inside the artifact. The whole line law - label,
# flag and the read-back that --check uses - lives in one src/os module, so
# writing and parsing cannot drift apart; an ordinary render gets None and
# keeps its bytes byte for byte.
OS_DIR = os.path.join(os.path.dirname(BASE), "os")
if OS_DIR not in sys.path:
    sys.path.insert(0, OS_DIR)
import matrix_stamp_provenance_line as MSPL  # noqa: E402

# R2502 seed, AC-PLRC1..AC-PLRC6 (pinned in state/queue/tech.md:540 BEFORE the
# code): the readability gate shipped at R2502 only protected callers that
# chose publish(), while this tool read the patterns file with json.load and
# interpolated every label straight into the artifact. The render path now
# asks that ONE gate through its consumer seam, which carries the gate own
# refusal code - no second classifier exists here.
import patterns_label_readability_render_consumer as PLRC  # noqa: E402

# R2505 seed, AC-PNLT1..AC-PNLT6 (pinned in state/queue/tech.md:542 BEFORE the
# code): the R2502/R2503 gate reads patterns["labels"] only, while this render
# interpolates header_note, response_text, every caption and every face label.
# The second statement of render asks ONE reading over every string the render
# actually reads, through the same shipped per-codepoint law - no second
# classifier is added here either.
import patterns_non_label_text_readability as PNLT  # noqa: E402

SUITE_RE = re.compile(
    r"(?m)^(PASS|FAIL) suite (\S+) exit=(\d+) pass-lines=(\d+)"
    r" fail-lines=(\d+) criteria=(\d+) (-?[0-9.]+)s")
# R2347 defect: the duration group refused a leading minus, so one suite the
# runner had just counted green (its wall time read -3.5s across a clock step)
# dropped out of the parse, the block stopped matching the runner count, and
# the whole 481-suite regression record became INELIGIBLE for default
# discovery - the matrix silently fell back to the previous round's log and
# the follow-up's two legs compared different evidence. The minus is accepted
# and CARRIED into the doc rather than dropped, so an odd duration stays
# visible instead of hiding a suite.
RUNNER_RE = re.compile(
    r"(?m)^RUNNER (PASS|FAIL) \((\d+)/(\d+) suites green,"
    r" reconcile controls (\d+)/(\d+), ([0-9.]+)s\)")
EVID_ROUND_RE = re.compile(r"R(\d+)")
NET_IMPORTS = ("urllib", "requests", "socket", "http", "ftplib",
               "xmlrpc", "smtplib", "asyncio")


def load_patterns():
    with open(PATTERNS, encoding="utf-8") as handle:
        return json.load(handle)


def _evidence_eligible(path):
    """Default-discovery eligibility (AC-SM2, four fail-closed checks;
    runner_profile AC-RP2 exactly-one precedent). Explicit --evidence
    stays lenient (absent suites are labeled no-evidence by design);
    only the default face requires a complete, consistent regression
    record, because picking a log that cannot back the matrix would
    degrade every suite row to no-evidence (live anchor: R1707's
    watermark-scale-recover log carries one RUNNER line but zero
    suite lines - the newest-by-mtime file is NOT the best evidence).
    """
    try:
        text = read_text(path)
    except (OSError, UnicodeDecodeError):
        # OSError = unreadable file; UnicodeDecodeError = a mixed-
        # dialect evidence file (UTF-16LE base with appended non-UTF16
        # sections, the R1683 writer-dialect lesson recurring at
        # R1774: lobby-roomboard-R1773.log bricks the walk otherwise).
        # A candidate that cannot be decoded is not evidence-eligible;
        # the discovery walk skips it and continues (fail-closed
        # semantics unchanged - never fabricate, never crash).
        return False
    runner = RUNNER_RE.findall(text)
    if len(runner) != 1 or runner[0][0] != "PASS":
        return False
    suites = SUITE_RE.findall(text)
    if not suites:
        return False
    labels = [row[1] for row in suites]
    if len(set(labels)) != len(labels):
        return False
    return len(suites) == int(runner[0][2])


def default_evidence():
    """Newest eligible evidence log under qa/, by mtime then name
    (R1695 naming-gap fix: the old face globbed reconcile-all-R*.log
    only, so the freshest regression record was invisible whenever it
    shipped inside a suite evidence log - R1695/R1703 both had to pass
    --evidence explicitly. The new face walks every qa/*.log newest-
    first, skipping this tool's own suite-matrix-* evidence files to
    avoid self-pointing, and takes the first one that parses as one
    RUNNER PASS + a complete consistent suite block."""
    names = [name for name in os.listdir(QA_DIR)
             if name.endswith(".log")
             and not name.startswith("suite-matrix-")]
    paths = [os.path.join(QA_DIR, name) for name in names]
    paths.sort(key=lambda path: (-os.path.getmtime(path),
                                 os.path.basename(path)))
    for path in paths:
        if _evidence_eligible(path):
            return path
    return None


def read_text(path):
    """Evidence logs on this machine come in two writer dialects: the
    runner's own utf-8 tee (no BOM) and PowerShell 5.1 `>` redirection
    (UTF-16LE with 0xFFFE BOM). Decode by BOM, fail-closed on the rest."""
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8", "replace")


def parse_evidence(path):
    text = read_text(path)
    status = {}
    for match in SUITE_RE.finditer(text):
        verdict, label, code, plines, flines, crit, secs = match.groups()
        status[label] = {"verdict": verdict, "exit": int(code),
                         "pass_lines": int(plines),
                         "fail_lines": int(flines),
                         "criteria": int(crit), "secs": secs}
    run = None
    match = RUNNER_RE.search(text)
    if match:
        run = {"verdict": match.group(1), "green": int(match.group(2)),
               "total": int(match.group(3)),
               "controls": "%s/%s" % (match.group(4), match.group(5)),
               "secs": match.group(6)}
    return status, run


def face_node(cfg, dotted):
    node = cfg
    for part in dotted.split("."):
        node = node[part]
    return node


def billable_faces(patterns):
    rows = []
    for domain in patterns["domains"]:
        path = os.path.join(BASE, domain["dir"], "config.json")
        with open(path, encoding="utf-8") as handle:
            cfg = json.load(handle)
        for face in domain["faces"]:
            node = face_node(cfg, face["path"])
            if isinstance(node, dict):
                keys = [str(k) for k in node]
                rows.append((domain["key"], face["label"], len(keys),
                             ", ".join(keys) if keys else "-"))
            elif isinstance(node, list):
                items = [str(x) for x in node]
                rows.append((domain["key"], face["label"], len(items),
                             ", ".join(items) if items else "-"))
            else:
                rows.append((domain["key"], face["label"], 1, str(node)))
    return rows


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def suite_status(entry):
    if entry is None:
        return "no-evidence", "-"
    if entry["exit"] == 0:
        return "green", entry["secs"]
    return "FAIL(exit=%d)" % entry["exit"], entry["secs"]


def render(patterns, evidence_path, status, run, stamp, stamp_from=None):
    # AC-PLRC1: the refusal is the SHIPPED readability gate asked at CALL time
    # through its consumer seam, raised BEFORE a single artifact byte is
    # composed. A clean file is handed back untouched, so its bytes stay
    # exactly today's (AC-PLRC3).
    PLRC.guard(patterns["labels"])
    # AC-PNLT2: the non-label text this artifact interpolates (header_note,
    # response_text, every caption, every face label) is refused by field name
    # before a single artifact byte is composed. A clean file passes through
    # untouched, so the artifact keeps today's bytes (AC-PNLT3).
    PNLT.guard(patterns)
    labels = patterns["labels"]
    suites = RA.SUITES
    total_crit = sum(crit for _, _, crit in suites)
    counts = {"green": 0, "FAIL": 0, "no-evidence": 0}
    rows = []
    for index, (label, suite_path, crit) in enumerate(suites, 1):
        state, secs = suite_status(status.get(label))
        counts["FAIL" if state.startswith("FAIL")
               else state] = counts.get(state, 0) + 1
        rows.append((index, label, suite_path.replace(os.sep, "/"),
                     crit, state, secs))
    base = os.path.basename(evidence_path)
    rmatch = EVID_ROUND_RE.search(base)
    round_tag = ("R" + rmatch.group(1)) if rmatch else base
    runner_line = ("no-evidence"
                   if run is None else
                   "RUNNER %s %d/%d suites green, reconcile controls %s,"
                   " %ss" % (run["verdict"], run["green"], run["total"],
                             run["controls"], run["secs"]))

    out = []
    out.append(patterns["header_note"])
    out.append("# " + labels["title"])
    out.append("")
    out.append("- %s: %s%s"
               % (labels["stamp"], labels["stamp_prefix"], stamp))
    out.append("- %s: python src/sandbox/suite_matrix.py --evidence %s"
               % (labels["command"], rel(evidence_path)))
    # Pinned position: the borrow names itself directly under the command
    # line it qualifies, and its wording/prefix is owned by the patterns.
    provenance = MSPL.segment(labels, stamp_from)
    if provenance:
        out.append(provenance)
    out.append("- %s: %s (%s)" % (labels["evidence_line"], base,
                                  runner_line))
    out.append("- %s: %s" % (labels["response"], labels["response_text"]))
    out.append("")
    out.append(labels["summary_title"])
    out.append("")
    out.append("| " + " | ".join(labels["summary_cols"]) + " |")
    out.append("|---|---|---|---|")
    out.append("| %d | %d | %s | %s |"
               % (len(suites), total_crit,
                  ("%d/%d" % (run["green"], run["total"])
                   if run else "no-evidence"), round_tag))
    out.append("")
    out.append(labels["faces_title"])
    out.append("")
    out.append("| " + " | ".join(labels["faces_cols"]) + " |")
    out.append("|---|---|---|---|")
    for key, label, count, names in billable_faces(patterns):
        out.append("| %s | %s | %d | %s |" % (key, label, count, names))
    out.append("")
    out.append(labels["matrix_title"])
    out.append("")
    out.append("| " + " | ".join(labels["matrix_cols"]) + " |")
    out.append("|---|---|---|---|---|---|")
    for index, label, suite_path, crit, state, secs in rows:
        out.append("| %d | %s | %s | %d | %s | %s |"
                   % (index, label, suite_path, crit, state, secs))
    out.append("|  | %s |  | %d | green %d / FAIL %d / no-evidence %d |  |"
               % (labels["total_row"], total_crit, counts["green"],
                  counts.get("FAIL", 0), counts.get("no-evidence", 0)))
    out.append("")
    out.append(labels["provenance_title"])
    out.append("")
    out.append("- %s (%s)" % (base, rel(evidence_path)))
    out.append(labels["provenance_note"])
    out.append("")
    return "\n".join(out)


def self_checks():
    """Hygiene face (AC-MX6): pure-ASCII source scan + true import
    lines carry no network library (R1678 self-hit lesson: scan the
    real import statements, not the raw text)."""
    problems = []
    with open(os.path.abspath(__file__), "rb") as handle:
        raw = handle.read()
    for offset, byte in enumerate(raw):
        if byte > 127:
            problems.append("non-ascii byte %d at offset %d" % (byte,
                                                                 offset))
            break
    import_re = re.compile(r"(?m)^\s*(?:import|from)\s+([A-Za-z_][\w.]*)")
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        for match in import_re.finditer(handle.read()):
            root = match.group(1).split(".")[0]
            if root in NET_IMPORTS:
                problems.append("network import: %s" % match.group(1))
    return problems


def doc_stamp(text, patterns):
    """Extract the generation stamp from an existing doc so --check
    compares content only (the stamp line is the single volatile
    field)."""
    prefix = "- %s: %s" % (patterns["labels"]["stamp"],
                           patterns["labels"]["stamp_prefix"])
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):]
    return None


def doc_evidence_face(text, patterns):
    """Extract the doc-recorded evidence path from the generation
    command line (R1749 stale-face hardening, seed = R1739 anchor:
    a doc regenerated with an EXPLICIT --evidence file then checked
    under DEFAULT discovery failed stale twice on the very same run -
    same content, only the resolved path differed, and the bare
    'stale (registry/config/evidence drifted)' message gave the
    operator no way to tell that face-mismatch from real drift).
    Returns None when the doc carries no --evidence segment (honest
    unknown, never a guess)."""
    prefix = "- %s: " % patterns["labels"]["command"]
    for line in text.splitlines():
        if line.startswith(prefix):
            match = re.search(r"--evidence (\S+)", line)
            return match.group(1) if match else None
    return None


def _print_evidence_face(recorded, resolved):
    """Evidence-face comparison + hint block for a stale --check
    (AC-EF2/AC-EF3; exit-code semantics unchanged - diagnostics
    only). The PASS path prints nothing here (byte-stable)."""
    if recorded is None:
        print("  evidence-face: doc-recorded=? (no --evidence line in"
              " doc) check-resolved=%s" % resolved)
        return
    if recorded == resolved:
        print("  evidence-face: doc-recorded=%s check-resolved=%s"
              " (faces agree - drift is in content, not the evidence"
              " face)" % (recorded, resolved))
        return
    print("  evidence-face: doc-recorded=%s check-resolved=%s"
          % (recorded, resolved))
    print("  hint: evidence face-mismatch - the doc was generated"
          " against a different evidence file than this check"
          " resolved; rerun: python src/sandbox/suite_matrix.py"
          " --evidence %s  then re-run --check to judge true drift"
          % resolved)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--check", action="store_true",
                        help="recompute and byte-compare against --out;"
                        " drift or missing doc exits 2")
    parser.add_argument("--stamp-from", default=None, metavar="DOC",
                        help="R2418 (AC-MSC1): render with the stamp line the"
                        " named document already carries, so a byte compare"
                        " between two minutes is content-only. The stamp is"
                        " read through doc_stamp - the same law --check uses -"
                        " and a document without one refuses E_SMX_STAMP_FROM"
                        " at exit 3 instead of inventing a stamp")
    args = parser.parse_args(argv[1:])

    problems = self_checks()
    for problem in problems:
        print("FAIL hygiene: %s" % problem)
    if problems:
        return 2

    patterns = load_patterns()
    evidence_path = args.evidence
    if evidence_path is None:
        evidence_path = default_evidence()
        if evidence_path is None:
            print("FAIL no default evidence found in qa/ (pass --evidence)")
            return 2
    evidence_path = os.path.abspath(evidence_path)
    status, run = parse_evidence(evidence_path)

    if args.check:
        if not os.path.exists(args.out):
            print("FAIL check: doc missing: %s" % rel(args.out))
            return 2
        with open(args.out, encoding="utf-8") as handle:
            current = handle.read()
        stamp = doc_stamp(current, patterns)
        if stamp is None:
            print("FAIL check: no stamp line found in %s" % rel(args.out))
            return 2
        try:
            fresh = render(patterns, evidence_path, status, run, stamp,
                           stamp_from=MSPL.recorded_source(
                               current, patterns["labels"]))
        except PLRC.RenderRefused as exc:
            # AC-PLRC4: a refusal is a READABILITY verdict, never drift - it
            # gets its own word and its own exit code so an operator cannot
            # mistake a mis-encoded label for a stale document.
            print("FAIL readability: %s label=%s" % (exc.code, exc.label))
            return 4
        except PNLT.NonLabelRefused as exc:
            # AC-PNLT2: a non-label field is refused by FIELD name, still as a
            # readability verdict (exit 4), never as drift.
            print("FAIL non-label: %s field=%s" % (exc.code, exc.field))
            return 4
        if fresh == current:
            print("PASS check: %s byte-identical (%d bytes, %d suites,"
                  " %d criteria)" % (rel(args.out), len(fresh.encode(
                      "utf-8")), len(RA.SUITES),
                      sum(c for _, _, c in RA.SUITES)))
            return 0
        print("FAIL check: %s stale (registry/config/evidence drifted)"
              % rel(args.out))
        _print_evidence_face(doc_evidence_face(current, patterns),
                             rel(evidence_path))
        return 2

    if args.stamp_from:
        if not os.path.exists(args.stamp_from):
            print("FAIL stamp-from: E_SMX_STAMP_FROM source missing: %s"
                  % rel(args.stamp_from))
            return 3
        with open(args.stamp_from, encoding="utf-8") as handle:
            source_doc = handle.read()
        stamp = doc_stamp(source_doc, patterns)
        if stamp is None:
            print("FAIL stamp-from: E_SMX_STAMP_FROM no stamp line found in"
                  " %s" % rel(args.stamp_from))
            return 3
    else:
        stamp = time.strftime("%Y-%m-%d %H:%M +08:00",
                              time.gmtime(time.time() + 8 * 3600))
    stamp_from_rel = rel(args.stamp_from) if args.stamp_from else None
    try:
        fresh = render(patterns, evidence_path, status, run, stamp,
                       stamp_from=stamp_from_rel)
    except PLRC.RenderRefused as exc:
        # AC-PLRC2: refusal lands before the file is opened, so the target
        # keeps every byte it had and no temp is left beside it.
        print("FAIL readability: %s label=%s" % (exc.code, exc.label))
        return 4
    except PNLT.NonLabelRefused as exc:
        # AC-PNLT2: no artifact byte is opened before this refusal, so the
        # target keeps every byte it had and no temp is left beside it.
        print("FAIL non-label: %s field=%s" % (exc.code, exc.field))
        return 4
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(fresh)
    green = sum(1 for label, _, _ in RA.SUITES
                if status.get(label, {}).get("exit") == 0)
    print("PASS generated %s (%d bytes) - registry suites=%d"
          " criteria=%d evidence=%s green=%d/%d"
          % (rel(args.out), len(fresh.encode("utf-8")), len(RA.SUITES),
             sum(c for _, _, c in RA.SUITES), rel(evidence_path), green,
             len(RA.SUITES)))
    print("PASS hygiene: pure-ascii source, zero network imports")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
