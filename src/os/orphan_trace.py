"""orphan_trace (R2323; criteria AC-OTR1..AC-OTR6 were pinned inside the
R2302 seed row of state/queue/tech.md:379 BEFORE this code existed).

evidence_variants reports each non-canonical evidence leg as ORPHAN when no
`reconcile-all-R<nnnn>.log` exists for its round. ORPHAN is honest about the
missing canonical name but says nothing about the trace: a round whose only
legs are `-b` and `-c` reads exactly the same whether one of those legs
actually ran a battery to a verdict (recoverable by a rename) or whether none
of them ever carried a runner line (the trace is genuinely missing).

This module is a READ-ONLY resolver over that same one evidence directory.
For every ORPHAN round it reports:

  - the orphan list, the round and the leg-to-round pairing all asked of
    evidence_variants (AC-OTR1: the law keeps one owner, so a patched reading
    flows straight through this module);
  - TRACE-EXISTS naming EVERY leg that carries a RUNNER line with that leg's
    own RUNNER token, its own VERDICT token and its digest, and naming the
    standing-in leg as the FIRST such leg in name order (AC-OTR2);
  - NO-TRACE when none of the round's legs carries a runner line, and
    NO-ORPHAN over an empty orphan list (AC-OTR3);
  - a refusal with its own code when a leg cannot be decoded, rather than
    counting it as carrying no verdict (AC-OTR4).

It writes nothing, reads no clock and opens no network connection (AC-OTR5,
AC-OTR6). The decoding ladder is followup_history.decode via read_log, and the
RUNNER/VERDICT line shape is followup_history.parse: no second decoder and no
second parser exist here.

Pure stdlib, pure-ASCII source, zero network.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import evidence_variants as EV
import followup_history as FH

REPORT_KEYS = ("dir", "counts", "rounds", "verdict")
ROUND_KEYS = ("round", "status", "standing_in", "legs")
LEG_KEYS = ("name", "runner", "verdict", "digest")
COUNT_KEYS = ("rounds", "legs", "trace_exists", "no_trace")

E_OTR_BAD_ARGS = "E_OTR_BAD_ARGS"
E_OTR_NO_EVIDENCE = "E_OTR_NO_EVIDENCE"
E_OTR_BAD_NAME = "E_OTR_BAD_NAME"
E_OTR_UNREADABLE = "E_OTR_UNREADABLE"
E_OTR_UNDECODABLE = "E_OTR_UNDECODABLE"

_DECODE_MAP = {
    EV.E_EVR_NO_EVIDENCE: E_OTR_NO_EVIDENCE,
    EV.E_EVR_UNREADABLE: E_OTR_UNREADABLE,
    EV.E_EVR_BAD_NAME: E_OTR_BAD_NAME,
}


class OrphanTraceError(Exception):
    """A reading that must not guess, carrying its own token."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code + (" " + detail if detail else ""))
        self.code = code
        self.detail = detail


def evidence_path(root, directory="qa"):
    """The one directory this reader opens, resolved the caller's way."""
    path = directory
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    if not os.path.isdir(path):
        raise OrphanTraceError(E_OTR_NO_EVIDENCE, directory)
    return path


def verdict_of(text):
    """The battery's own VERDICT token, in either of the two forms written.

    followup_history.parse answers the follow-up section form, where the line
    always carries a round label (`VERDICT R2311 PASS`); the battery logs carry
    the bare form (`VERDICT PASS`, and `VERDICT: PASS` in one legacy family),
    so the label is not required here. The token vocabulary stays pinned to
    PASS/FAIL, and any other word is not a verdict.
    """
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        head = raw.strip().split()
        if not head or head[0] not in ("VERDICT", "VERDICT:"):
            continue
        for token in head[1:]:
            word = token.strip(":")
            if word in ("PASS", "FAIL"):
                return word
    return None


def read_legs(path, rows):
    """One leg's own trace: runner token, verdict token, digest (AC-OTR4)."""
    legs = []
    for row in sorted(rows, key=lambda item: item["name"]):
        leg_path = os.path.join(path, row["name"])
        try:
            text, _encoding = FH.read_log(leg_path)
        except FH.FollowupHistoryError as exc:
            # A leg that cannot be decoded is a refusal, never an empty leg.
            raise OrphanTraceError(E_OTR_UNDECODABLE,
                                   "%s %s" % (row["name"], exc.code))
        # The RUNNER token is asked of the shared parser; only the bare
        # VERDICT form needs the scan above.
        _runs, _verdict, runner = FH.parse(text)
        verdict = verdict_of(text)
        try:
            digest = EV.digest_of(leg_path)
        except EV.EvidenceVariantsError as exc:
            raise OrphanTraceError(E_OTR_UNREADABLE, row["name"])
        legs.append({"name": row["name"], "runner": runner,
                     "verdict": verdict, "digest": digest})
    return legs


def read_round(label, path, rows):
    """One orphan round: TRACE-EXISTS with its standing-in leg, or NO-TRACE."""
    legs = read_legs(path, rows)
    carrying = [leg["name"] for leg in legs if leg["runner"] is not None]
    if carrying:
        status = "TRACE-EXISTS"
        standing_in = carrying[0]
    else:
        status = "NO-TRACE"
        standing_in = None
    return {"round": label, "status": status, "standing_in": standing_in,
            "legs": legs}


def traces(root, directory="qa"):
    """Read every ORPHAN round of one evidence directory. Writes nothing."""
    path = evidence_path(root, directory)
    try:
        report = EV.variants(root, directory)
    except EV.EvidenceVariantsError as exc:
        raise OrphanTraceError(_DECODE_MAP.get(exc.code, E_OTR_UNREADABLE),
                               exc.detail)
    grouped = {}
    for row in report["variants"]:
        if row["status"] != "ORPHAN":
            continue
        grouped.setdefault(row["round"], []).append(row)
    rounds = []
    for label in sorted(grouped, key=lambda name: int(name[1:])):
        rounds.append(read_round(label, path, grouped[label]))
    counts = {"rounds": len(rounds), "legs": 0, "trace_exists": 0,
              "no_trace": 0}
    for item in rounds:
        counts["legs"] += len(item["legs"])
        if item["status"] == "TRACE-EXISTS":
            counts["trace_exists"] += 1
        else:
            counts["no_trace"] += 1
    if not rounds:
        verdict = "NO-ORPHAN"
    elif counts["no_trace"]:
        verdict = "TRACE-MISSING"
    else:
        verdict = "TRACE-FOUND"
    return {"dir": directory.replace(os.sep, "/"), "rounds": rounds,
            "counts": counts, "verdict": verdict}


def render(report):
    """One line per orphan round, every runner-carrying leg named."""
    counts = report["counts"]
    out = ["ORPHAN TRACE dir=%s rounds=%d legs=%d trace_exists=%d "
           "no_trace=%d verdict=%s"
           % (report["dir"], counts["rounds"], counts["legs"],
              counts["trace_exists"], counts["no_trace"], report["verdict"])]
    for item in report["rounds"]:
        out.append("  %s status=%s standing_in=%s"
                   % (item["round"], item["status"],
                      item["standing_in"] or "-"))
        for leg in item["legs"]:
            out.append("    leg=%s runner=%s verdict=%s digest=%s"
                       % (leg["name"], leg["runner"] or "-",
                          leg["verdict"] or "-", leg["digest"][:12]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        if key == "counts":
            counts = {}
            for name in COUNT_KEYS:
                counts[name] = report["counts"][name]
            ordered["counts"] = counts
        elif key == "rounds":
            pinned = []
            for item in report["rounds"]:
                row = {}
                for name in ROUND_KEYS:
                    if name != "legs":
                        row[name] = item[name]
                legs = []
                for leg in item["legs"]:
                    pinned_leg = {}
                    for name in LEG_KEYS:
                        pinned_leg[name] = leg[name]
                    legs.append(pinned_leg)
                row["legs"] = legs
                pinned.append(row)
            ordered["rounds"] = pinned
        else:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: orphan_trace.py --trace [DIR] [--root PATH] [--json]\n"
         "  DIR defaults to qa\n"
         "  exit 0 = no orphan round, or every orphan round carries a trace\n"
         "  exit 2 = an orphan round carries no runner line at all\n"
         "  exit 3 = evidence absent, unreadable or undecodable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    operation = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    directory = "qa"
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--trace":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_OTR_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_OTR_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            directory = arg
        index += 1
    if not operation:
        sys.stdout.write("E_OTR_BAD_ARGS: --trace is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = traces(root, directory)
    except OrphanTraceError as exc:
        sys.stdout.write("%s\n" % str(exc))
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "TRACE-MISSING":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))