"""Xidudu operations-layer spec compliance gate (group order O-2026-0929-013).

Review object: the U294 operations-layer spec v1 of the GimmeAll
minigame (group repo gaming/MiniGame, cross-repo READ-ONLY). The
compliance-guardrail experience migrated here comes from this
company's own specs (payment-integration-spec.md and
membership-spec.md) plus the R231 pass-reachability red line.

Criteria XD1..XD10 are pre-registered in criteria.json (backlog R604
row, registered before implementation - honesty law). The gate
mechanically re-checks the criteria against the spec text so the
sibling team can re-run it on spec v2 after patching the note-level
gaps (exit 0 = all green).

Exit codes:
  0 = all criteria PASS
  1 = note-level GAPs found (advisory patches needed, no red line)
  2 = red-line FAIL (forbidden pattern present)
  3 = spec file missing / unreadable (SKIP)

Usage:
  python xidudu_ops_compliance_gate.py [--spec PATH] [--log PATH]
"""

import argparse
import hashlib
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))


def load_criteria():
    with open(os.path.join(BASE, "criteria.json"), encoding="utf-8") as fh:
        return json.load(fh)


def find_line(text, pattern):
    """First line (1-based) containing pattern, or None."""
    for idx, line in enumerate(text.splitlines(), 1):
        if pattern in line:
            return idx
    return None


class Report(object):
    """Console + utf-8 evidence log, cp936-console safe."""

    def __init__(self, log_path):
        self.file = None
        if log_path:
            self.file = open(log_path, "w", encoding="utf-8", newline="\n")

    def say(self, line):
        if self.file:
            self.file.write(line + "\n")
        try:
            print(line, flush=True)
        except UnicodeEncodeError:
            enc = getattr(sys.stdout, "encoding", None) or "ascii"
            print(line.encode(enc, "replace").decode(enc, "replace"),
                  flush=True)

    def close(self):
        if self.file:
            self.file.close()


def evaluate(crit, text, rep):
    """Return status string: PASS / GAP / FAIL."""
    missing = []
    evidence = []
    for pat in crit.get("require_all", []):
        line_no = find_line(text, pat)
        if line_no:
            evidence.append("require '%s' hit L%d" % (pat, line_no))
        else:
            missing.append(pat)
    for group in crit.get("require_any", []):
        hit_line = None
        hit_pat = None
        for pat in group:
            hit_line = find_line(text, pat)
            if hit_line:
                hit_pat = pat
                break
        if hit_line:
            evidence.append("any(%s) hit '%s' L%d"
                            % ("|".join(group), hit_pat, hit_line))
        else:
            missing.append("any(%s)" % "|".join(group))
    for item in crit.get("min_count", []):
        pat, need = item["pattern"], item["count"]
        got = text.count(pat)
        if got >= need:
            evidence.append("count '%s' %d>=%d" % (pat, got, need))
        else:
            missing.append("count '%s' %d<%d" % (pat, got, need))
    forbidden = None
    for pat in crit.get("forbid", []):
        line_no = find_line(text, pat)
        if line_no:
            forbidden = (pat, line_no)
            break

    if forbidden:
        status = "FAIL"
        evidence.insert(0, "FORBIDDEN '%s' found at L%d"
                        % (forbidden[0], forbidden[1]))
    elif missing:
        status = crit.get("on_missing", "GAP")
        evidence.append("missing: %s" % "; ".join(missing))
    else:
        status = "PASS"
    rep.say("%s %s %s" % (status, crit["id"], crit["desc"]))
    for ev in evidence:
        rep.say("  evidence: %s" % ev)
    return status


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", default=None,
                    help="path to the operations-layer spec markdown")
    ap.add_argument("--log", default=None, help="utf-8 evidence log path")
    args = ap.parse_args(argv)

    data = load_criteria()
    spec_path = args.spec or os.path.normpath(
        os.path.join(BASE, data["default_spec"]))
    rep = Report(args.log)

    if not os.path.isfile(spec_path):
        rep.say("SKIP spec file not found: %s" % spec_path)
        rep.say("VERDICT: exit=3 SPEC_MISSING")
        rep.close()
        return 3
    with open(spec_path, encoding="utf-8") as fh:
        text = fh.read()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    rep.say("SPEC: %s (%d bytes, sha256[:16]=%s)"
            % (spec_path, len(text.encode("utf-8")), digest))
    rep.say("GATE: criteria=%d, pre-registered in criteria.json "
            "(backlog R604 row, registered before implementation)"
            % len(data["criteria"]))

    counts = {"PASS": 0, "GAP": 0, "FAIL": 0}
    for crit in data["criteria"]:
        status = evaluate(crit, text, rep)
        counts[status] += 1

    rep.say("SUMMARY: PASS=%d GAP=%d FAIL=%d criteria=%d"
            % (counts["PASS"], counts["GAP"], counts["FAIL"],
               len(data["criteria"])))
    if counts["FAIL"]:
        verdict = "exit=2 RED_LINE_FAIL"
        code = 2
    elif counts["GAP"]:
        verdict = ("exit=1 NOTE_GAPS "
                   "(no red line; patch note-level gaps then re-run)")
        code = 1
    else:
        verdict = "exit=0 ALL_GREEN"
        code = 0
    rep.say("VERDICT: %s" % verdict)
    rep.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
