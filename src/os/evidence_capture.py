"""evidence_capture - the per-round evidence ritual as one callable (R2261).

Every product window writes a per-round single-writer script
(`evidence_R2241.py` .. `evidence_R2259.py`, eighty-eight of them at the R2260
closeout) that all do the same five things: run the suite twice, digest the
criterion lines, write one utf-8 LF body through a single writer, run a batch
of adjacent suites and append a live gate line. Each copy was typed by hand, so
a defect fixed in one round's copy can stay broken in the next and the pile
grows by one file per window.

This module owns the ritual instead. It refuses rather than inventing: a red
leg, a red adjacent suite or a digest that is not identical across the two legs
raises before any file is created, so a half-written evidence file cannot land.

Criteria AC-EVC1..AC-EVC6 were pinned in state/queue/tech.md as the R2259 seed
row BEFORE this code existed. Stdlib only, ASCII source, zero network.
"""

import hashlib
import json
import os
import re
import subprocess
import sys

LEGS = 2
MARKERS = ("PASS ", "FAIL ")
ROUND_RE = re.compile(r"^R[0-9]+$")

REPORT_KEYS = ("round", "suite", "legs", "digest", "identical",
               "adjacent", "fails", "offending", "evidence", "bytes",
               "verdict")
ADJACENT_KEYS = ("name", "rc", "suite_line")

USAGE = ("usage: evidence_capture.py --round R<n> --suite PATH "
         "[--adjacent a.py,b.py] [--evidence PATH] [--root PATH] [--json]\n")


class EvidenceError(Exception):
    """A refused capture: the code names why and detail names the leg."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def resolve(root, name):
    """A suite or evidence name is relative to the scanned root, not the CWD."""
    if os.path.isabs(name):
        return name
    return os.path.join(root, name)


def run_suite(root, path):
    """One suite run: (returncode, decoded body). Body may carry wall clock."""
    proc = subprocess.run([sys.executable, path], cwd=root,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def criteria_digest(body):
    """The sha16 of the joined PASS/FAIL lines - the only comparable face."""
    lines = [line for line in body.splitlines()
             if line.startswith(MARKERS)]
    joined = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()[:16].upper()


def suite_line(body):
    """The last SUITE line of a body, or an honest NO SUITE LINE."""
    lines = [line for line in body.splitlines() if line.startswith("SUITE")]
    return lines[-1] if lines else "NO SUITE LINE"


def _flat(text):
    """utf-8 with LF only and exactly one trailing newline."""
    body = text.replace("\r\n", "\n").replace("\r", "\n")
    return body.rstrip("\n") + "\n"


def _write_once(path, text):
    """Create the file as utf-8 LF, refuse an existing path, no partial left."""
    data = _flat(text).encode("utf-8")
    try:
        handle = open(path, "xb")
    except FileExistsError:
        raise EvidenceError("E_EVC_EXISTS", path)
    except (IOError, OSError):
        raise EvidenceError("E_EVC_BADDIR", path)
    try:
        handle.write(data)
        handle.close()
    except (IOError, OSError):
        try:
            handle.close()
        except (IOError, OSError):
            pass
        try:
            os.unlink(path)
        except (IOError, OSError):
            pass
        raise EvidenceError("E_EVC_WRITE", path)
    with open(path, "rb") as back:
        landed = back.read()
    if landed != data:
        try:
            os.unlink(path)
        except (IOError, OSError):
            pass
        raise EvidenceError("E_EVC_WRITE", path)
    return len(data)


def capture(root, round_no, suite, adjacent=None, evidence=None):
    """Run the whole ritual and return the pinned report.

    Refuses (raises EvidenceError) before writing anything when a leg is red,
    when the two legs disagree on their criterion lines, or when an adjacent
    suite is red. Writes exactly one evidence file otherwise.
    """
    if not isinstance(round_no, str) or not ROUND_RE.match(round_no or ""):
        raise EvidenceError("E_EVC_BAD_ROUND", str(round_no))
    suite_path = resolve(root, suite)
    if not os.path.isfile(suite_path):
        raise EvidenceError("E_EVC_NO_SUITE", suite_path)

    legs = []
    for _ in range(LEGS):
        code, body = run_suite(root, suite_path)
        legs.append((code, body, criteria_digest(body)))

    if legs[0][0] != 0 or legs[1][0] != 0:
        raise EvidenceError("E_EVC_RED", os.path.basename(suite_path))
    if legs[0][2] != legs[1][2]:
        raise EvidenceError("E_EVC_DRIFT",
                            "%s/%s" % (legs[0][2], legs[1][2]))

    rows = []
    for name in list(adjacent or []):
        path = resolve(root, name)
        if not os.path.isfile(path):
            raise EvidenceError("E_EVC_NO_SUITE", path)
        code, body = run_suite(root, path)
        rows.append({"name": name, "rc": code,
                     "suite_line": suite_line(body)})
        if code != 0:
            raise EvidenceError("E_EVC_RED", name)

    if evidence is None:
        evidence = os.path.join("qa", "evidence-%s.log" % round_no)
    evidence_path = resolve(root, evidence)
    directory = os.path.dirname(evidence_path) or "."
    if not os.path.isdir(directory) or not os.access(directory, os.W_OK):
        raise EvidenceError("E_EVC_BADDIR", directory)

    parts = ["EVIDENCE CAPTURE round=%s suite=%s legs=%d\n"
             % (round_no, suite, LEGS)]
    for index, (code, body, digest) in enumerate(legs):
        parts.append("== LEG %s rc=%d digest=%s\n"
                     % ("AB"[index], code, digest))
        parts.append(body)
    parts.append("== ADJACENT %d\n" % len(rows))
    for row in rows:
        parts.append("== %s rc=%d %s\n"
                     % (row["name"], row["rc"], row["suite_line"]))
    parts.append("EVIDENCE identical=%r adjacent=%d fails=0 digest=%s\n"
                 % (legs[0][2] == legs[1][2], len(rows), legs[0][2]))

    size = _write_once(evidence_path, "".join(parts))
    return {"round": round_no,
            "suite": suite,
            "legs": LEGS,
            "digest": legs[0][2],
            "identical": legs[0][2] == legs[1][2],
            "adjacent": rows,
            "fails": 0,
            "offending": None,
            "evidence": evidence,
            "bytes": size,
            "verdict": "CAPTURED"}


def render(report):
    return ("EVIDENCE CAPTURE round=%s suite=%s legs=%d identical=%r "
            "adjacent=%d fails=%d offending=%r evidence=%s bytes=%d "
            "verdict=%s"
            % (report["round"], report["suite"], report["legs"],
               report["identical"], len(report["adjacent"]),
               report["fails"], report["offending"], report["evidence"],
               report["bytes"], report["verdict"]))


def to_json(report):
    ordered = {}
    for key in REPORT_KEYS:
        value = report[key]
        if key == "adjacent":
            value = [dict((name, row[name]) for name in ADJACENT_KEYS)
                     for row in value]
        ordered[key] = value
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


EXIT_BY_CODE = {"E_EVC_RED": 2, "E_EVC_DRIFT": 2,
                "E_EVC_NO_SUITE": 3, "E_EVC_BADDIR": 3, "E_EVC_WRITE": 3,
                "E_EVC_EXISTS": 4,
                "E_EVC_BAD_ROUND": 5, "E_EVC_BAD_ARGS": 5}


def main(argv):
    round_no = None
    suite = None
    adjacent = []
    evidence = None
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            as_json = True
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg in ("--round", "--suite", "--adjacent", "--evidence",
                     "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_EVC_BAD_ARGS: %s needs a value\n" % arg)
                return 5
            value = argv[index]
            if arg == "--round":
                round_no = value
            elif arg == "--suite":
                suite = value
            elif arg == "--evidence":
                evidence = value
            elif arg == "--root":
                root = value
            else:
                adjacent = [item for item in value.split(",") if item]
        else:
            sys.stdout.write("E_EVC_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not round_no or not suite:
        sys.stdout.write("E_EVC_BAD_ARGS: --round and --suite are required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = capture(root, round_no, suite, adjacent=adjacent,
                         evidence=evidence)
    except EvidenceError as exc:
        sys.stdout.write("%s %s\n" % (exc.code, exc.detail))
        sys.stdout.write("REFUSE TO CAPTURE\n")
        return EXIT_BY_CODE.get(exc.code, 2)
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))