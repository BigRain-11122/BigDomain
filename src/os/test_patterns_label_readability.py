"""patterns_label_readability suite (R2502).

Criteria AC-PLR1..AC-PLR6 were pinned in state/queue/tech.md:538 at R2494,
the seed row, BEFORE this code existed.

What this proves: a reader that decodes suite_matrix_patterns.json through
the platform default code page prints one label as Cyrillic and replacement
characters while its siblings read as Chinese, and suite_matrix renders every
label VERBATIM into docs/sandbox-suite-matrix.md and into the evidence logs.
Nothing in the tree asked whether a label is readable text.

MEASURED HONESTY: on the shipped tree at this round the patterns file reads
CLEAN on every label - the mojibake in the R2494 note was a console decode
artifact, not a damaged byte on disk. So the SUSPECT detection is proved on
FIXTURES built from the real file, never claimed as a live catch, and the
live reading is what the artifact itself is asked with.

Proofs are measured on real calls of the shipped module and on a real render
of the shipped suite_matrix, not on stubs.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import patterns_label_readability as PLR  # noqa: E402
import matrix_stamp_provenance_line as MSPL  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "patterns_label_readability.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_EXPECT = 'os.path.join("..", "os", "test_patterns_label_readability.py"), 6),'
MOJIBAKE = "\u04e1\ufffd\ufffd\ufffd\ufffd\u04d4"


def check(ok, label):
    if ok:
        print("  PASS %s" % label)
    else:
        print("  FAIL %s" % label)
    return ok


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def digest(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()


def patterns():
    return json.loads(read_text(PATTERNS_PATH))


def world_copy(root, mutate=None):
    """A real copy of the shipped patterns file, optionally doctored."""
    document = patterns()
    if mutate is not None:
        mutate(document["labels"])
    path = os.path.join(root, "patterns.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(document, ensure_ascii=False, indent=2,
                                sort_keys=True) + "\n")
    return path


def cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args, cwd=REPO,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def verdicts(rows):
    return dict((row["label"], row["verdict"]) for row in rows)


def ac_plr1(world):
    """The reading is derived from the patterns file at CALL time."""
    document = patterns()
    labels = document["labels"]
    string_keys = sorted(k for k, v in labels.items() if isinstance(v, str))
    rows = PLR.reading(labels)
    ok = check(sorted(row["label"] for row in rows) == string_keys,
               "AC-PLR1 every string label in the file is read (%d)"
               % len(string_keys))

    path = world_copy(world)
    loaded = json.loads(read_text(path))["labels"]
    clean = verdicts(PLR.reading(loaded))
    ok = check(clean.get("stamp_from") == PLR.CLEAN,
               "AC-PLR1 the shipped copy reads CLEAN on stamp_from") and ok

    loaded["stamp_from"] = MOJIBAKE
    suspect = verdicts(PLR.reading(loaded))
    ok = check(suspect.get("stamp_from") == PLR.SUSPECT,
               "AC-PLR1 the same call on an edited copy reads SUSPECT") and ok
    restored = verdicts(PLR.reading(json.loads(read_text(path))["labels"]))
    ok = check(restored.get("stamp_from") == PLR.CLEAN,
               "AC-PLR1 the reading follows the bytes, not a cache") and ok

    source = read_text(MODULE)
    literal_keys = [key for key in string_keys if '"%s"' % key in source]
    ok = check(not literal_keys,
               "AC-PLR1 no label key is spelled in the module (%r)"
               % literal_keys) and ok
    return ok


def ac_plr2(world):
    """A label outside its siblings' scripts is named with exact codepoints."""
    labels = json.loads(read_text(world_copy(world)))["labels"]
    labels["stamp_from"] = MOJIBAKE
    rows = PLR.reading(labels)
    row = [r for r in rows if r["label"] == "stamp_from"][0]
    points = [cp["codepoint"] for cp in row["suspects"]]
    ok = check(points == ["U+04E1", "U+FFFD", "U+FFFD", "U+FFFD", "U+FFFD",
                          "U+04D4"],
               "AC-PLR2 the exact codepoints are printed (%r)" % points)
    reasons = [cp["reason"] for cp in row["suspects"]]
    ok = check(reasons[0] == "SCRIPT-NOT-IN-SIBLINGS"
               and reasons[1] == "BROKEN-CODEPOINT",
               "AC-PLR2 each codepoint carries the law it broke (%r)"
               % reasons[:2]) and ok
    index = [cp["index"] for cp in row["suspects"]]
    ok = check(index == [0, 1, 2, 3, 4, 5],
               "AC-PLR2 the position in the label is named (%r)" % index) and ok
    siblings = [r for r in rows if r["label"] != "stamp_from"]
    ok = check(all(r["verdict"] == PLR.CLEAN for r in siblings),
               "AC-PLR2 the sibling labels are not tarred with it") and ok
    return ok


def ac_plr3(world):
    """A SUSPECT label refuses publication; a CLEAN file keeps today's bytes."""
    labels = json.loads(read_text(world_copy(world)))["labels"]
    labels["stamp_from"] = MOJIBAKE
    named = []
    try:
        PLR.publish(labels, lambda: named.append("rendered"))
    except PLR.LabelRefused as exc:
        refused = exc
    else:
        refused = None
    ok = check(refused is not None and refused.code == PLR.E_SUSPECT,
               "AC-PLR3 a suspect file raises its own refusal code")
    ok = check(refused is not None and refused.label == "stamp_from",
               "AC-PLR3 the refusal names the label key") and ok
    ok = check(refused is not None
               and refused.codepoints == ["U+04E1", "U+FFFD", "U+FFFD",
                                          "U+FFFD", "U+FFFD", "U+04D4"],
               "AC-PLR3 the refusal carries the codepoints") and ok
    ok = check(not named, "AC-PLR3 render never ran on a refused file") and ok

    shipped = patterns()
    doc_text = read_text(DOC)
    evidence = SM.doc_evidence_face(doc_text, shipped)
    if evidence is None:
        raise SystemExit("FAIL setup: shipped doc records no evidence path")
    evidence_path = os.path.abspath(os.path.join(REPO, evidence))
    status, run = SM.parse_evidence(evidence_path)
    stamp = SM.doc_stamp(doc_text, shipped)
    fresh = PLR.publish(
        shipped["labels"],
        lambda: SM.render(shipped, evidence_path, status, run, stamp,
                          stamp_from=MSPL.recorded_source(
                              doc_text, shipped["labels"])))
    ok = check(fresh == doc_text,
               "AC-PLR3 a clean file renders the artifact byte-identically"
               " (%d bytes)" % len(doc_text.encode("utf-8"))) and ok
    return ok


def ac_plr4(world):
    """No label is rewritten and the patterns digest is unchanged."""
    before = digest(PATTERNS_PATH)
    shipped = patterns()
    PLR.reading(shipped["labels"])
    PLR.gate(shipped["labels"])
    PLR.publish(shipped["labels"], lambda: None)
    rc_clean, _ = cli(["--patterns", PATTERNS_PATH])
    bad = world_copy(world, lambda labels: labels.update(stamp_from=MOJIBAKE))
    rc_bad, _ = cli(["--patterns", bad])
    after = digest(PATTERNS_PATH)
    ok = check(before == after,
               "AC-PLR4 the shipped patterns digest is unchanged (%s)"
               % before[:12])
    ok = check(rc_clean == 0 and rc_bad == 2,
               "AC-PLR4 both CLI paths ran (%d/%d)" % (rc_clean, rc_bad)) and ok
    ok = check(patterns()["labels"]["stamp_from"] != MOJIBAKE,
               "AC-PLR4 no label string was rewritten in the file") and ok
    ok = check(digest(bad) != after,
               "AC-PLR4 the doctored copy is a different file, not the"
               " shipped one") and ok
    return ok


def ac_plr5(world):
    """CLI exits 0/2/3/5 with a byte-stable --json over pinned keys."""
    rc_clean, out_clean = cli(["--patterns", PATTERNS_PATH, "--json"])
    rc_clean2, out_clean2 = cli(["--patterns", PATTERNS_PATH, "--json"])
    ok = check(rc_clean == 0 and rc_clean2 == 0,
               "AC-PLR5 a clean file exits 0 (%d/%d)"
               % (rc_clean, rc_clean2))
    ok = check(out_clean == out_clean2,
               "AC-PLR5 --json is byte-stable across runs") and ok
    try:
        row = json.loads(out_clean.decode("utf-8"))
    except ValueError:
        row = None
    ok = check(isinstance(row, dict) and sorted(row) == [
        "code", "labels", "publishable", "refused_codepoints",
        "refused_label", "tool"],
        "AC-PLR5 --json keys are the pinned six (%r)"
        % (sorted(row) if isinstance(row, dict) else None)) and ok

    bad = world_copy(world, lambda labels: labels.update(stamp_from=MOJIBAKE))
    rc_bad, out_bad = cli(["--patterns", bad, "--json"])
    ok = check(rc_bad == 2 and b"E_PLR_SUSPECT" in out_bad,
               "AC-PLR5 a suspect file exits 2 with the code") and ok
    rc_missing, _ = cli(["--patterns", os.path.join(world, "nope.json")])
    ok = check(rc_missing == 3, "AC-PLR5 a missing file exits 3") and ok
    rc_label, _ = cli(["--patterns", PATTERNS_PATH, "--label", "no-such-key"])
    ok = check(rc_label == 5, "AC-PLR5 an unknown label exits 5") and ok
    return ok


def ac_plr6(world):
    """Pure ASCII, stdlib only, zero network, no clock, read-only, own label
    and own suite."""
    raw = read_bytes(MODULE)
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    source = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", source))
    ok = check(ascii_only, "AC-PLR6 the module source is pure ASCII")
    ok = check(imports <= {"argparse", "json", "sys", "unicodedata"},
               "AC-PLR6 imports are stdlib only (%r)" % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime"}),
               "AC-PLR6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-PLR6 zero network imports") and ok
    ok = check('"w"' not in source and "'w'" not in source
               and "os.replace" not in source and "os.remove" not in source
               and "shutil" not in source,
               "AC-PLR6 the module holds no write primitive") and ok
    ok = check(PLR.LABEL == "os-patterns-label-readability",
               "AC-PLR6 the module carries its own reconcile label") and ok
    ok = check(WIRED_EXPECT in read_text(RUNNER),
               "AC-PLR6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PLR6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("PATTERNS LABEL READABILITY suite (R2502, %d criteria)"
          % EXPECTED_CRITERIA)
    world = tempfile.mkdtemp(prefix="plr-suite-")
    try:
        results = [ac_plr1(world), ac_plr2(world), ac_plr3(world),
                   ac_plr4(world), ac_plr5(world), ac_plr6(world)]
    finally:
        shutil.rmtree(world, ignore_errors=True)
    passed = sum(1 for row in results if row)
    print("SUITE %s exit=%d pass-lines=%d fail-lines=%d criteria=%d"
          % ("PASS" if passed == len(results) else "FAIL",
             0 if passed == len(results) else 1, passed,
             len(results) - passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())