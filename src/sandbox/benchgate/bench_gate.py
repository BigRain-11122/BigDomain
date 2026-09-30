"""BigDomain line gate for group decision D-20260930-36 (global benchmark rules).

Implements the BigDomain slice of the audit deliverable
docs/audits/global-benchmark-and-check-rules-20260930.md (section 5):
machine criteria for rules R-D1 / R-D2 / R-D3, each outputting
pass/fail + evidence pointers (decision clause 3: one machine
criterion per rule, merged into the company-line gate).

Criteria are pre-registered in criteria.json (backlog R691 claim row,
registered before implementation - honesty law).

Exit codes:
  0 = all rules PASS
  1 = one or more rules FAIL (incl. blocked-on-CEO-physicals) - honest red
  3 = preview/ directory missing (SKIP)

Standalone by design (see criteria.json "runner_integration"): the
verdict may stay red while CEO physical items (server/domain/ICP
filing) are pending; the gate is the single point that flips green
mechanically once bootstrap fills the registries.

Usage:
  python bench_gate.py [--preview DIR] [--log PATH] [--json PATH]
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, "..", "..", ".."))

MARKERS = ["AIGC", "msgSecCheck", "投顾", "19.9"]
EXTERNAL_REF_TOKENS = ["http://", "https://"]


def load_criteria():
    with open(os.path.join(BASE, "criteria.json"), encoding="utf-8") as fh:
        return json.load(fh)


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
            print(line.encode(enc, "replace").decode(enc, "replace"), flush=True)

    def close(self):
        if self.file:
            self.file.close()


def find_fronts(preview_dir):
    """HTML fronts passing the real-front test (doc/sandbox substitutes rejected)."""
    fronts = []
    if not os.path.isdir(preview_dir):
        return fronts
    for name in sorted(os.listdir(preview_dir)):
        if not name.lower().endswith(".html"):
            continue
        path = os.path.join(preview_dir, name)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        size_ok = os.path.getsize(path) >= 4096
        markers_ok = all(m in text for m in MARKERS)
        external_refs = [t for t in EXTERNAL_REF_TOKENS if t in text]
        if size_ok and markers_ok and not external_refs:
            fronts.append(path)
    return fronts


def check_rd1(preview_dir):
    """R-D1: north-star = accessible front count (>=1, no doc/sandbox substitute)."""
    fronts = find_fronts(preview_dir)
    passed = len(fronts) >= 1
    return {
        "rule": "R-D1",
        "status": "PASS" if passed else "FAIL",
        "fronts": len(fronts),
        "detail": ("accessible fronts=%d (local file:// era; external reachability "
                   "face is R-D2)" % len(fronts)),
        "evidence": fronts + [
            "qa/deliverable-metrics-R683.json (group probe: BigDomain accessible_fronts 0 -> 1)"],
    }


def check_rd2(preview_dir, fronts):
    """R-D2: every front needs an external/tunnel URL + one real click capture."""
    registry = os.path.join(preview_dir, "front-urls.json")
    if not os.path.exists(registry):
        return {
            "rule": "R-D2",
            "status": "FAIL",
            "reason": "blocked-on-CEO-physicals",
            "detail": ("no front-urls.json registry; server/domain/ICP-filing are "
                       "CEO physical items (backlog bootstrap row); current front "
                       "is local file:// only"),
            "evidence": ["src/os/backlog.md bootstrap row",
                         "criteria.json R-D2 future_wiring"],
        }
    with open(registry, encoding="utf-8") as fh:
        entries = json.load(fh)
    missing = []
    for front in fronts:
        rel = os.path.relpath(front, REPO).replace("\\", "/")
        ent = None
        for e in (entries if isinstance(entries, list) else entries.get("fronts", [])):
            if isinstance(e, dict) and e.get("front", "").replace("\\", "/") == rel:
                ent = e
                break
        if ent is None:
            missing.append(rel + " (no registry entry)")
            continue
        url = str(ent.get("url", ""))
        if not url.startswith(("http://", "https://")):
            missing.append(rel + " (url not http/https)")
        cast = ent.get("clickcast_evidence", "")
        if not cast or not os.path.exists(os.path.join(REPO, cast)):
            missing.append(rel + " (clickcast_evidence missing on disk)")
    if missing:
        return {"rule": "R-D2", "status": "FAIL", "reason": "registry gaps",
                "detail": "; ".join(missing), "evidence": [registry]}
    return {"rule": "R-D2", "status": "PASS",
            "detail": "all fronts carry external URL + clickcast evidence",
            "evidence": [registry]}


def check_rd3(preview_dir):
    """R-D3: one external-person closed loop (register -> produce -> be seen)."""
    loop = os.path.join(preview_dir, "external-loop.json")
    if not os.path.exists(loop):
        return {
            "rule": "R-D3",
            "status": "FAIL",
            "reason": "blocked-on-CEO-physicals",
            "detail": ("no external-loop.json; the loop needs an externally "
                       "reachable front (R-D2 dependency); sandbox ugc loop "
                       "exists but rule text forbids sandbox substitution"),
            "evidence": ["src/sandbox/ugc/ (sandbox - NOT a substitute)",
                         "src/os/backlog.md bootstrap row"],
        }
    with open(loop, encoding="utf-8") as fh:
        data = json.load(fh)
    stages = data.get("stages", data) if isinstance(data, dict) else {}
    need = ["register", "produce", "be_seen"]
    missing = [s for s in need
               if not (isinstance(stages.get(s), dict) and stages[s].get("external_participant"))]
    if missing:
        return {"rule": "R-D3", "status": "FAIL", "reason": "stages not external",
                "detail": "missing/external=false: " + ", ".join(missing),
                "evidence": [loop]}
    return {"rule": "R-D3", "status": "PASS",
            "detail": "one external-person closed loop complete",
            "evidence": [loop]}


def run_gate(preview_dir, rep):
    if not os.path.isdir(preview_dir):
        rep.say("SKIP: preview dir missing: %s" % preview_dir)
        return None, 3
    crit = load_criteria()
    rep.say("D-20260930-36 BigDomain line gate (criteria pre-registered %s)"
            % crit["registered"])
    fronts = find_fronts(preview_dir)
    verdicts = [check_rd1(preview_dir), check_rd2(preview_dir, fronts),
                check_rd3(preview_dir)]
    for v in verdicts:
        rep.say("[%s] %s - %s" % (v["rule"], v["status"], v.get("detail", "")))
        if v.get("reason"):
            rep.say("    reason: %s" % v["reason"])
        for ev in v.get("evidence", []):
            rep.say("    evidence: %s" % ev)
    all_pass = all(v["status"] == "PASS" for v in verdicts)
    rep.say("VERDICT: %s" % ("PASS" if all_pass else "FAIL"))
    return verdicts, (0 if all_pass else 1)


def main(argv=None):
    ap = argparse.ArgumentParser(description="D-20260930-36 BigDomain line gate")
    ap.add_argument("--preview", default=os.path.join(REPO, "preview"))
    ap.add_argument("--log", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    rep = Report(args.log)
    try:
        verdicts, code = run_gate(args.preview, rep)
        if args.json and verdicts is not None:
            with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
                json.dump({"gate": "D-20260930-36 BigDomain line",
                           "verdicts": verdicts,
                           "overall": "PASS" if code == 0 else "FAIL"},
                          fh, ensure_ascii=False, indent=2)
                fh.write("\n")
        return code
    finally:
        rep.close()


if __name__ == "__main__":
    sys.exit(main())
