"""R2710 capture driver: the AC-PNAU suite through the SHIPPED capture
callable (two legs, identical criterion lines), the parent dialect guard
suites as adjacent readings, and one bounded live leg measuring the SAME
fixture on BOTH readers.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import evidence_capture as EC  # noqa: E402
import probe_seam_dialect_marker_escape_guard_scope as PNAU  # noqa: E402
import probe_seam_dialect_escape_guard_scope as PNAT  # noqa: E402

ROUND = "R2710"
SUITE = "src/os/test_probe_seam_dialect_marker_escape_guard_scope.py"
EVIDENCE = os.path.join(
    REPO, "qa", "probe-seam-dialect-marker-escape-guard-scope-R2710.log")
LIVE_EVIDENCE = os.path.join(
    REPO, "qa", "probe-seam-dialect-marker-escape-guard-scope-live-R2710.log")
ADJACENT = [
    "src/os/test_probe_seam_dialect_escape_guard_scope.py",
    "src/os/test_probe_seam_dialect_canonical_guard_scope.py",
    "src/os/test_probe_seam_dialect_shape_guard_scope.py",
    "src/os/test_probe_seam_dialect_tag_guard_scope.py",
    "src/os/test_probe_seam_unnameable_dialect_marker_scope.py",
]

MODULES = [
    "probe_seam_dialect_marker_escape_guard_scope.py",
    "probe_seam_dialect_escape_guard_scope.py",
    "probe_seam_dialect_canonical_guard_scope.py",
    "probe_seam_dialect_shape_guard_scope.py",
    "probe_seam_unnameable_dialect_marker_scope.py",
    "probe_seam_unnameable_part_joiner_escaped_scope.py",
]

B = chr(92)
FIXTURES = [
    ("marker-escaped", "dialect" + B + ":1+duplicate:2"),
    ("dup-illegal", "dialect:1+strict-prefix-of:ab+duplicate:a" + B + "2c"),
    ("dup-joiner", "dialect:1+duplicate:a" + B + "+2"),
    ("legacy-bare", "duplicate:2"),
    ("legacy-escape", "duplicate:a" + B + "2c"),
    ("plain-marked", "dialect:1+duplicate:2"),
]


def live_leg():
    lines = []
    loops = 0
    files = 0
    for name in sorted(set(MODULES)):
        path = os.path.join(BASE, name)
        with io.open(path, "rb") as handle:
            text = handle.read().decode("utf-8", "replace")
        files += 1
        for build in (PNAT.module_alias_report, PNAU.module_alias_report):
            report = build(text, BASE)
            loops += len(report.get("loops") or [])
    lines.append("LIVE files=%d loops=%d read_only=True"
                 % (files, loops))
    for label, word in FIXTURES:
        mine = PNAU.read_word(word)
        theirs = PNAT.read_word(word)
        lines.append("FIXTURE %s mine=%s theirs=%s"
                     % (label,
                        json.dumps({"refused": mine["refused"],
                                    "siblings": mine["siblings"],
                                    "duplicate": mine["duplicate"]},
                                   sort_keys=True),
                        json.dumps({"refused": theirs["refused"],
                                    "siblings": theirs["siblings"],
                                    "duplicate": theirs["duplicate"]},
                                   sort_keys=True)))
    with io.open(LIVE_EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    return len(lines)


def main():
    sys.stdout.write("CAPTURE start round=%s adjacent=%d\n"
                     % (ROUND, len(ADJACENT)))
    sys.stdout.flush()
    report = EC.capture(REPO, ROUND, SUITE, adjacent=ADJACENT,
                        evidence=EVIDENCE)
    print(json.dumps(report, sort_keys=True))
    print("LIVE-LINES %d" % (live_leg(),))
    return 0 if report.get("verdict") in ("PASS", "CAPTURED") else 2


if __name__ == "__main__":
    sys.exit(main())
