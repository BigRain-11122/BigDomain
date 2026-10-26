"""Double-run identity dialect (R2153; AC-RID1..AC-RID8 pre-registered in
state/queue/tech.md BEFORE this code existed - honesty law).

Every suite in this repo ships two evidence runs so a reviewer can ask
"did the second run agree with the first?". Until now that question was
answered in two incompatible dialects:

  bytes        two files identical byte for byte (given as sha16)
  conclusions  the per-criterion PASS/FAIL lines identical while the
               detail payloads differ, because a seeded world stamps its
               own wall-clock every run (disclosed in R2143)

Both are legitimate answers, but a suite that SAYS "byte-identical"
while its files differ is a false claim, and a suite whose criteria
flipped is red no matter which word it used. This module makes the
dialect explicit, verifies every claim against the files, and audits a
whole evidence directory for unverified claims.

Two rules are load-bearing:

  1. normalize() only does three disclosed things (drop BOM, unify
     CRLF and bare CR to LF, end with exactly one newline). It never
     scrubs timestamps, paths or digests - that would hide drift.
  2. bytes identity implies conclusions identity and NEVER the other
     way round; the comparator never upgrades one mode into the other.

Stdlib only, ASCII source, zero network, read-only.
"""

import io
import json
import os
import re
import sys

MODE_BYTES = "bytes"
MODE_CONCLUSIONS = "conclusions"
MODES = (MODE_BYTES, MODE_CONCLUSIONS)

VERDICT_RE = re.compile(r"^(PASS|FAIL)\s+([A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)\b")
SUITE_RE = re.compile(r"^SUITE\s+(PASS|FAIL)\s+(\d+)\s*/\s*(\d+)")
ID_DIGIT_RE = re.compile(r"\d")
DIGEST_RE = re.compile(r"sha16\s+([0-9A-Fa-f]{16})", re.IGNORECASE)

BYTES_CLAIM_RE = re.compile(
    r"byte-identical|bytes identical|byte identical", re.IGNORECASE)
CONCL_CLAIM_RE = re.compile(
    r"criterion[^\n]{0,40}identical|criteria[^\n]{0,40}identical"
    r"|conclusions? identical"
    r"|\u5224\u636e\u884c[^\n]{0,20}\u540c\u4e00"
    r"|\u5224\u636e\u7ed3\u8bba\u540c\u4e00")
RUN_LINE_RE = re.compile(
    r"RUN1\s+rc=(-?\d+)\s+sha16=([0-9A-Fa-f]{16})"
    r"(?:\s+RUN2\s+rc=(-?\d+)\s+sha16=([0-9A-Fa-f]{16}))?"
    r"(?:\s+identical=(True|False))?")

NET_IMPORTS = ("urllib", "http.client", "requests", "socket", "httpx")

PAIR_SUFFIXES = (
    ("-verifya", "-verifyb"),
    ("-a", "-b"),
    ("-run2", ""),
)


class IdentityError(ValueError):
    """Raised with a machine-readable .code."""

    def __init__(self, code, message):
        ValueError.__init__(self, "%s: %s" % (code, message))
        self.code = code
        self.message = message


def normalize(text):
    """The only allowed normalization (see the module docstring)."""
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    while text.endswith("\n\n"):
        text = text[:-1]
    if text and not text.endswith("\n"):
        text += "\n"
    return text


def digest16(text):
    """sha256 hex[:16] lowercase over the normalized UTF-8 bytes."""
    import hashlib

    data = normalize(text).encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:16]


def parse_verdicts(text):
    """Return (criteria, suite) parsed from one evidence file.

    criteria - ordered list of {"id", "verdict"}
    suite    - {"verdict", "passed", "total"} or None

    The same id may be asserted by several legs (AC-TMP1 has an
    "anchors" leg and an "age" leg). That is legal as long as every leg
    agrees; conflicting verdicts for one id are E_DUP_ID.
    """
    criteria = []
    seen = {}
    suite = None
    for raw in normalize(text).split("\n"):
        line = raw.strip()
        if not line:
            continue
        match = SUITE_RE.match(line)
        if match:
            if suite is not None:
                raise IdentityError("E_MULTI_SUITE",
                                    "two SUITE verdict lines")
            suite = {"verdict": match.group(1),
                     "passed": int(match.group(2)),
                     "total": int(match.group(3))}
            continue
        match = VERDICT_RE.match(line)
        if not match:
            continue
        crit_id = match.group(2)
        if not ID_DIGIT_RE.search(crit_id):
            continue
        verdict = match.group(1)
        if crit_id in seen:
            if seen[crit_id] != verdict:
                raise IdentityError(
                    "E_DUP_ID",
                    "criterion %s contradicts itself" % crit_id)
            continue
        seen[crit_id] = verdict
        criteria.append({"id": crit_id, "verdict": verdict})
    return criteria, suite


def body_lines(text):
    """Lines that are NOT criterion or suite verdict lines.

    A criterion detail such as "PASS AC-AMBM7: ... byte-identical=True"
    asserts something about the PRODUCT (three instances agree), not
    about the pair of evidence files. Only the surrounding body can
    declare the evidence dialect.
    """
    keep = []
    for raw in normalize(text).split("\n"):
        line = raw.strip()
        if not line:
            continue
        if SUITE_RE.match(line) or VERDICT_RE.match(line):
            continue
        keep.append(line)
    return keep


def parse_run_line(text):
    """Parse the driver verdict line, e.g.

    RUN1 rc=0 sha16=0B3398051DD02331 RUN2 rc=0 sha16=0B3398051DD02331
    identical=True

    Returns {"run1": {"rc", "sha16"}, "run2": {...}, "identical": bool}
    or None. The digests are lowercased.
    """
    match = RUN_LINE_RE.search(normalize(text))
    if not match:
        return None
    row = {"run1": {"rc": int(match.group(1)),
                    "sha16": match.group(2).lower()},
           "run2": None,
           "identical": None}
    if match.group(3) is not None:
        row["run2"] = {"rc": int(match.group(3)),
                       "sha16": match.group(4).lower()}
    if match.group(5) is not None:
        row["identical"] = (match.group(5) == "True")
    return row


def claim_mode(text):
    """Which dialect does this evidence file claim? None when silent."""
    body = "\n".join(body_lines(text))
    if BYTES_CLAIM_RE.search(body):
        return MODE_BYTES
    if CONCL_CLAIM_RE.search(body):
        return MODE_CONCLUSIONS
    row = parse_run_line(text)
    if row is not None and row["identical"] is True:
        return MODE_BYTES
    return None


def payload_digest(text):
    """digest16 of the file with driver verdict lines dropped.

    The historical convention has two forms: a digest of the whole
    evidence file (rounds that never append a verdict line) and a
    digest of the suite stdout (rounds whose driver appends its own
    RUN1/RUN2 line afterwards). Both are reproducible from the file -
    the second one only after dropping the driver's own line - so a
    declared digest is accepted against either form.
    """
    kept = [line for line in normalize(text).split("\n")
            if line.strip() and not RUN_LINE_RE.search(line)]
    return digest16("\n".join(kept) + "\n" if kept else "")


def declared_digest(text):
    """The file-level declared sha16 (the RUN1 field), or None.

    Scoped digests such as "SUITE-SHA16 <x>" or "CRITERIA LINE sha16
    <x>" hash the criterion block, not the evidence file, so they are
    deliberately NOT accepted here - reading them as file digests would
    manufacture a false accusation.
    """
    row = parse_run_line(text)
    if row is not None:
        return row["run1"]["sha16"]
    return None


def declared_run_digests(text):
    """(run1, run2) declared in the body, either may be None."""
    row = parse_run_line(text)
    if row is None:
        return (None, None)
    return (row["run1"]["sha16"],
            row["run2"]["sha16"] if row["run2"] else None)


def compare_runs(text_a, text_b, mode):
    """Compare two evidence runs under an explicit dialect.

    Returns a dict with a stable key set:
      mode, ok, criteria_a, criteria_b, suite_a, suite_b, differing,
      digest_a, digest_b, bytes_identical, conclusions_identical
    """
    if mode not in MODES:
        raise IdentityError("E_BAD_MODE", "unknown mode %r" % (mode,))
    crit_a, suite_a = parse_verdicts(text_a)
    crit_b, suite_b = parse_verdicts(text_b)
    map_a = dict((row["id"], row["verdict"]) for row in crit_a)
    map_b = dict((row["id"], row["verdict"]) for row in crit_b)
    differing = sorted(set(map_a) ^ set(map_b))
    differing += sorted(cid for cid in set(map_a) & set(map_b)
                        if map_a[cid] != map_b[cid])
    suite_same = ((suite_a is None and suite_b is None)
                  or (suite_a is not None and suite_b is not None
                      and suite_a["verdict"] == suite_b["verdict"]
                      and suite_a["total"] == suite_b["total"]))
    conclusions_same = (not differing and suite_same
                        and len(crit_a) == len(crit_b))
    digest_a = digest16(text_a)
    digest_b = digest16(text_b)
    bytes_same = digest_a == digest_b
    if mode == MODE_BYTES:
        ok = bytes_same
    else:
        ok = conclusions_same
    return {"mode": mode,
            "ok": ok,
            "criteria_a": len(crit_a),
            "criteria_b": len(crit_b),
            "suite_a": suite_a,
            "suite_b": suite_b,
            "differing": differing,
            "digest_a": digest_a,
            "digest_b": digest_b,
            "bytes_identical": bytes_same,
            "conclusions_identical": conclusions_same}


def _digest_agrees(declared, text, full_digest):
    """A declared digest is accepted against either disclosed form."""
    return declared in (full_digest, payload_digest(text))


def verify_pair(text_a, text_b, mode=None, require_claim=False):
    """Compare and verify the claim written inside the evidence.

    Honest boundaries: silence is E_NO_CLAIM only when the caller
    demands a claim (require_claim=True) - otherwise an unclaimed pair
    is verified in the weaker conclusions dialect and reported as
    "implicit", because conclusions identity is the most that can be
    checked without a claim. A byte claim that does not hold is
    E_FALSE_BYTE_CLAIM; a declared per-run digest that does not equal
    the corresponding file's digest16 is E_FALSE_DIGEST.
    """
    claimed = claim_mode(text_a) or claim_mode(text_b)
    implicit = False
    if mode is None:
        if claimed is None:
            if require_claim:
                raise IdentityError("E_NO_CLAIM",
                                    "evidence names no identity dialect")
            implicit = True
            mode = MODE_CONCLUSIONS
        else:
            mode = claimed
    result = compare_runs(text_a, text_b, mode)
    declared_a, declared_b = declared_run_digests(text_a)
    if declared_a is None and declared_b is None:
        declared_a, declared_b = declared_run_digests(text_b)
    result["claimed"] = claimed
    result["implicit"] = implicit
    result["declared"] = declared_a
    result["problems"] = []
    if claimed == MODE_BYTES and not result["bytes_identical"]:
        result["problems"].append("E_FALSE_BYTE_CLAIM")
    if declared_a is not None and not _digest_agrees(declared_a, text_a,
                                                     result["digest_a"]):
        result["problems"].append("E_FALSE_DIGEST")
    if declared_b is not None and not _digest_agrees(declared_b, text_b,
                                                     result["digest_b"]):
        if "E_FALSE_DIGEST" not in result["problems"]:
            result["problems"].append("E_FALSE_DIGEST")
    if not result["conclusions_identical"]:
        result["problems"].append("E_CONCLUSION_DRIFT")
    result["ok"] = result["ok"] and not result["problems"]
    return result


def _pair_suffixes(name):
    """Return [(base, left_suffix, right_suffix)] candidates for a name."""
    for left, right in PAIR_SUFFIXES:
        if not name.endswith(".log"):
            continue
        stem = name[:-4]
        if right and stem.endswith(right):
            yield stem[:-len(right)], left, right
        elif not right and stem.endswith(left):
            yield stem[:-len(left)], left, right


def find_pairs(directory):
    """Discover evidence pairs by base name. Sorted, never guessed."""
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        raise IdentityError("E_NO_DIR", "cannot list %r" % (directory,))
    present = set(names)
    pairs = []
    seen = set()
    for name in names:
        if not name.endswith(".log"):
            continue
        for base, left, right in _pair_suffixes(name):
            left_name = base + left + ".log"
            right_name = base + right + ".log"
            if left_name not in present or right_name not in present:
                continue
            if left_name == right_name:
                continue
            key = (left_name, right_name)
            if key in seen:
                continue
            seen.add(key)
            pairs.append({"base": base, "a": left_name, "b": right_name})
    pairs.sort(key=lambda row: (row["base"], row["a"], row["b"]))
    return pairs


def audit_pairs(directory, pairs=None):
    """Audit every discovered pair. Returns a stable report dict."""
    if pairs is None:
        pairs = find_pairs(directory)
    records = []
    for pair in pairs:
        path_a = os.path.join(directory, pair["a"])
        path_b = os.path.join(directory, pair["b"])
        text_a = read_text(path_a)
        text_b = read_text(path_b)
        try:
            result = verify_pair(text_a, text_b)
        except IdentityError as exc:
            records.append({"base": pair["base"], "a": pair["a"],
                            "b": pair["b"], "mode": None, "ok": False,
                            "problems": [exc.code],
                            "claimed": None, "declared": None,
                            "implicit": False, "differing": []})
            continue
        records.append({"base": pair["base"], "a": pair["a"],
                        "b": pair["b"], "mode": result["mode"],
                        "ok": result["ok"], "problems": result["problems"],
                        "claimed": result["claimed"],
                        "declared": result["declared"],
                        "implicit": result["implicit"],
                        "differing": result["differing"]})
    summary = {"pairs": len(records),
               "clean": sum(1 for row in records if row["ok"]),
               "bytes_mode": sum(1 for row in records
                                 if row["mode"] == MODE_BYTES),
               "conclusions_mode": sum(1 for row in records
                                       if row["mode"] == MODE_CONCLUSIONS),
               "unclaimed": sum(1 for row in records if row["implicit"]),
               "false_byte_claims": sum(1 for row in records
                                        if "E_FALSE_BYTE_CLAIM"
                                        in row["problems"]),
               "false_digests": sum(1 for row in records
                                    if "E_FALSE_DIGEST" in row["problems"]),
               "conclusion_drift": sum(1 for row in records
                                       if "E_CONCLUSION_DRIFT"
                                       in row["problems"])}
    return {"directory": directory, "summary": summary, "records": records}


def default_baseline_path():
    repo = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(repo, "state", "run_identity_baseline.json")


def load_baseline(path):
    """Load the shipped known-defect baseline.

    Shape: {"known": [{"base": <pair base>, "classes": [<code>...]}]}.
    Class granularity matters: baselining a byte-claim artifact must
    never mask a conclusion drift in the same pair.
    """
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (IOError, OSError, ValueError) as exc:
        raise IdentityError("E_BAD_BASELINE", "cannot read %r: %s"
                            % (path, exc))
    known = set()
    for entry in data.get("known", []):
        if not isinstance(entry, dict) or "base" not in entry:
            raise IdentityError("E_BAD_BASELINE", "bad entry %r" % (entry,))
        classes = entry.get("classes") or []
        if not isinstance(classes, list):
            raise IdentityError("E_BAD_BASELINE",
                                "classes not a list for %r" % (entry["base"],))
        for code in classes:
            known.add((entry["base"], code))
    return known


def apply_baseline(report, known):
    """Subtract the shipped baseline: only NEW problems stay fatal."""
    new = []
    for row in report["records"]:
        for code in row["problems"]:
            if (row["base"], code) in known:
                continue
            new.append({"base": row["base"], "code": code})
    report["new"] = new
    report["gated_clean"] = not new
    return report


def read_text(path):
    if not os.path.isfile(path):
        raise IdentityError("E_NO_FILE", "missing %r" % (path,))
    with io.open(path, "rb") as handle:
        raw = handle.read()
    return raw.decode("utf-8", "replace")


def network_imports(source_text):
    found = []
    for line in source_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            for name in NET_IMPORTS:
                if stripped.split()[1].split(".")[0] == name:
                    found.append(name)
    return sorted(set(found))


def format_report(report):
    summary = report["summary"]
    lines = ["run identity audit: %s" % report["directory"],
             "pairs=%d clean=%d bytes=%d conclusions=%d unclaimed=%d"
             % (summary["pairs"], summary["clean"], summary["bytes_mode"],
                summary["conclusions_mode"], summary["unclaimed"]),
             "false_byte_claims=%d false_digests=%d conclusion_drift=%d"
             % (summary["false_byte_claims"], summary["false_digests"],
                summary["conclusion_drift"])]
    for row in report["records"]:
        if row["ok"]:
            continue
        lines.append("PROBLEM %s (%s vs %s) mode=%s %s"
                     % (row["base"], row["a"], row["b"], row["mode"],
                        ",".join(row["problems"])))
    if "new" in report:
        lines.append("new=%d gated_clean=%s"
                     % (len(report["new"]), report["gated_clean"]))
    return "\n".join(lines)


def _stderr(message):
    sys.stderr.write(message + "\n")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    want_json = "--json" in args
    if want_json:
        args.remove("--json")
    mode = None
    if "--mode" in args:
        index = args.index("--mode")
        if index + 1 >= len(args):
            _stderr("E_BAD_ARGS: --mode needs a value")
            return 2
        mode = args[index + 1]
        del args[index:index + 2]
        if mode not in MODES:
            _stderr("E_BAD_MODE: %s" % mode)
            return 2
    try:
        if len(args) == 2 and args[0] == "--digest":
            payload = {"file": args[1], "digest16": digest16(read_text(args[1]))}
            print(json.dumps(payload, sort_keys=True) if want_json
                  else payload["digest16"])
            return 0
        if len(args) == 3 and args[0] == "--pair":
            result = verify_pair(read_text(args[1]), read_text(args[2]), mode)
            print(json.dumps(result, sort_keys=True) if want_json
                  else "mode=%s ok=%s bytes=%s conclusions=%s differing=%s %s"
                  % (result["mode"], result["ok"],
                     result["bytes_identical"],
                     result["conclusions_identical"],
                     ",".join(result["differing"]) or "-",
                     ",".join(result["problems"]) or "-"))
            return 0 if result["ok"] else 2
        if len(args) == 2 and args[0] == "--audit":
            report = audit_pairs(args[1])
            try:
                apply_baseline(report, load_baseline(default_baseline_path()))
            except IdentityError:
                apply_baseline(report, [])
            print(json.dumps(report, indent=2, sort_keys=True) if want_json
                  else format_report(report))
            return 0 if report["gated_clean"] else 2
    except IdentityError as exc:
        _stderr(str(exc))
        return 3 if exc.code == "E_NO_FILE" else 2
    _stderr("usage: run_identity.py --digest FILE | --pair A B [--mode M]"
            " | --audit DIR [--json]")
    return 2


if __name__ == "__main__":
    sys.exit(main())