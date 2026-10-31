# gate_drift.py - why an inert machine gate stopped matching, as a reading
# Criteria AC-GDR1..AC-GDR6 were pre-registered in state/queue/tech.md as the
# R2286 seed row BEFORE this file existed. Anchor check at HEAD 2026-11-01:
# "gate_drift", "AC-GDR", "E_GDR", "os-gate-drift" and "test_gate_drift" hit
# only prose and state files (the seed row that names them, this board,
# state.json, status-export.json, state/debt.md, heartbeat.txt and the
# R2286 closeout/export helpers); no code path existed. Disclosed here.
#
# Why this exists: machine_gate reports an INERT declaration as an identity
# that matches no claimable candidate, but it cannot say WHY it stopped
# matching. A row whose text was edited and a row that was deleted both read
# as the same inert entry, so an operator cannot tell "this blocker moved
# house" from "this blocker is gone" and has to grep the queue by hand to
# rebuild the declaration. This reader answers that one question.
#
# The gate reading and the declaration are IMPORTED from machine_gate, never
# re-derived: the inert list comes straight out of machine_gate.gate, so a
# patched reading flows through, which the suite proves. The row and prefix
# laws are imported too (queue_floor decides what a row is, queue_row decides
# its criteria prefix), so the queue carries exactly one row predicate.
#
# The split is binary, as the criteria row demands: every inert entry is
# either DRIFT (a row in the queue still carries its prefix) or GONE (no row
# carries it), never both. A DRIFT entry names the old identity, the new
# identity, both lines and the shared prefix, so an operator can rewrite the
# declaration in one step. "moved" is true when the two identities differ; a
# drift entry whose identity did NOT change is a row that is still verbatim
# in the queue but no longer claimable (for example a row that declares no
# criteria prefix), which is a fact worth naming rather than a repair.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.
#
# CLI: gate_drift.py --drift [QUEUE] [--root PATH] [--decl PATH] [--json]
#   exit 0 = NO-DRIFT (no inert entry) or STILL-PRESENT (every inert entry
#            still exists verbatim, so the declaration is not stale)
#   exit 2 = DRIFT (a declared row was edited) or GONE (a declared row no
#            longer exists) - both mean the declaration needs a rewrite
#   exit 3 = the declaration or the queue is missing / unreadable / malformed
#   exit 5 = bad flags

import io
import json
import os
import sys

import machine_gate as MG
import queue_floor as QF
import queue_head as QH
import queue_row as QR

VERDICTS = ("NO-DRIFT", "DRIFT", "GONE", "STILL-PRESENT")

REPORT_KEYS = ("queue", "path", "declaration", "declarations", "inert",
               "drift", "gone", "drift_count", "gone_count", "moved_count",
               "verdict")
DRIFT_KEYS = ("prefix", "old_identity", "old_line", "new_identity", "line",
              "moved", "match_count", "text")
GONE_KEYS = ("prefix", "old_identity", "old_line", "match_count")

# An identity is "<prefix>#<sha8>"; a row that declares no criteria prefix
# carries "-" as its key, which is the same placeholder machine_gate uses.
NO_PREFIX = "-"

EXCERPT_MAX = 120


class GateDriftError(Exception):
    """Raised when the reader cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def prefix_of(identity):
    """The shared prefix part of a declaration identity."""
    if "#" in identity:
        return identity.rsplit("#", 1)[0]
    return identity


def excerpt(text):
    """A deterministic ASCII excerpt of a row, for the reading."""
    body = text.strip()
    if len(body) > EXCERPT_MAX:
        body = body[:EXCERPT_MAX] + "..."
    return body.encode("ascii", "replace").decode("ascii")


def queue_rows(root, name="tech"):
    """Every open and done row in file order, with the identity it carries.

    The row law is queue_floor's and the prefix law is queue_row's; the
    identity constructor is machine_gate's, so a row's identity here is the
    same string the declaration was keyed with.
    """
    rel = QH.queue_path(name)
    if rel is None:
        raise GateDriftError("E_GDR_BAD_QUEUE", "unknown queue %s" % name)
    full = os.path.join(root, rel)
    if not os.path.isfile(full):
        raise GateDriftError("E_GDR_NO_QUEUE", rel)
    try:
        text = QH.read_text(full)
    except QH.QueueHeadError as exc:
        raise GateDriftError("E_GDR_BAD_QUEUE", exc.detail)
    rows = []
    # Newline-based, exactly like machine_gate, so a line number means the
    # same thing in both readings.
    for index, line in enumerate(text.split("\n"), 1):
        if not (QF.is_open_row(line) or QF.is_done_row(line)):
            continue
        scanned = QR.scan_row(line)
        prefix = scanned["prefix"] if scanned["prefixed"] else None
        rows.append({"line": index,
                     "key": prefix if prefix else NO_PREFIX,
                     "prefix": prefix,
                     "identity": MG.identity_of(prefix, line),
                     "text": line})
    return rows


def review(root, name="tech", declaration=None):
    """Split every inert declaration into DRIFT or GONE; the closed report."""
    try:
        gate = MG.gate(root, name, declaration)
    except MG.MachineGateError as exc:
        raise GateDriftError(exc.code, exc.detail)
    rows = queue_rows(root, name)
    drift = []
    gone = []
    for entry in gate["inert"]:
        identity = entry["identity"]
        key = prefix_of(identity)
        # "-" is machine_gate's placeholder for a row that declares no
        # criteria prefix, NOT a prefix two rows can share. Matching it as a
        # prefix would attribute the declaration to whichever unprefixed row
        # sits first in the file (the live reading made exactly that mistake
        # and reported a drift against a row at line 7). With no prefix to
        # attribute by, the only honest key is the identity itself.
        if key == NO_PREFIX:
            matches = [row for row in rows if row["identity"] == identity]
        else:
            matches = [row for row in rows if row["key"] == key]
        if matches:
            best = matches[0]
            drift.append({"prefix": key,
                          "old_identity": identity,
                          "old_line": entry["line"],
                          "new_identity": best["identity"],
                          "line": best["line"],
                          "moved": best["identity"] != identity,
                          "match_count": len(matches),
                          "text": excerpt(best["text"])})
        else:
            gone.append({"prefix": key,
                         "old_identity": identity,
                         "old_line": entry["line"],
                         "match_count": len(matches)})
    moved = 0
    for item in drift:
        if item["moved"]:
            moved += 1
    if not gate["inert"]:
        verdict = "NO-DRIFT"
    elif gone and not moved:
        verdict = "GONE"
    elif moved:
        verdict = "DRIFT"
    else:
        verdict = "STILL-PRESENT"
    return {"queue": name,
            "path": gate["path"],
            "declaration": gate["declaration"],
            "declarations": gate["declarations"],
            "inert": len(gate["inert"]),
            "drift": drift,
            "gone": gone,
            "drift_count": len(drift),
            "gone_count": len(gone),
            "moved_count": moved,
            "verdict": verdict}


def one_line(report):
    """The single line an operator reads."""
    return ("GATE DRIFT %s declarations=%d inert=%d drift=%d gone=%d "
            "moved=%d verdict=%s"
            % (report["queue"], report["declarations"], report["inert"],
               report["drift_count"], report["gone_count"],
               report["moved_count"], report["verdict"]))


def render(report):
    """Full text rendering: the one line, then every inert entry named."""
    out = [one_line(report)]
    for item in report["drift"]:
        out.append("  DRIFT %s:%d prefix=%s old=%s new=%s moved=%s matches=%d"
                   % (report["path"], item["line"], item["prefix"],
                      item["old_identity"], item["new_identity"],
                      "yes" if item["moved"] else "no", item["match_count"]))
        out.append("    ROW %s" % item["text"])
    for item in report["gone"]:
        out.append("  GONE prefix=%s old=%s old_line=%s"
                   % (item["prefix"], item["old_identity"],
                      "none" if item["old_line"] is None else item["old_line"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    drift_out = []
    for item in report["drift"]:
        pinned = {}
        for key in DRIFT_KEYS:
            pinned[key] = item[key]
        drift_out.append(pinned)
    ordered["drift"] = drift_out
    gone_out = []
    for item in report["gone"]:
        pinned = {}
        for key in GONE_KEYS:
            pinned[key] = item[key]
        gone_out.append(pinned)
    ordered["gone"] = gone_out
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: gate_drift.py --drift [QUEUE] [--root PATH] [--decl PATH]"
         " [--json]\n"
         "  QUEUE defaults to tech (state/queue/<QUEUE>.md)\n"
         "  --decl defaults to machine_gate's declaration\n"
         "  exit 0 = NO-DRIFT, or STILL-PRESENT (declaration not stale)\n"
         "  exit 2 = DRIFT (row edited) or GONE (row deleted)\n"
         "  exit 3 = declaration or queue missing / unreadable / malformed\n"
         "  exit 5 = bad flags\n")


def main(argv):
    operation = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    name = "tech"
    declaration = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--drift":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--decl"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_GDR_BAD_ARGS: %s needs a path\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            else:
                declaration = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_GDR_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            name = arg
        index += 1
    if not operation:
        sys.stdout.write("E_GDR_BAD_ARGS: --drift is required\n")
        sys.stdout.write(USAGE)
        return 5
    if QH.queue_path(name) is None:
        sys.stdout.write("E_GDR_BAD_ARGS: unknown queue %s\n" % name)
        sys.stdout.write(USAGE)
        return 5
    try:
        report = review(root, name, declaration)
    except GateDriftError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] in ("DRIFT", "GONE"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))