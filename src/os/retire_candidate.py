# retire_candidate.py - is a declared evidence copy a retirement candidate?
# Criteria AC-RET1..AC-RET6 were pre-registered in state/queue/tech.md (the
# R2308 seed row) BEFORE this file existed.
#
# Why this exists: three readers each hold one third of the retirement
# question and nothing joins them. evidence_output_map says who declares what
# and where two scripts collide, evidence_parity says whether a copy still
# performs the whole ritual, and evidence_output_audit says whether the
# declaration is still true on disk. Deciding to delete a file today means
# reading all three by hand and holding the conjunction in one head, which is
# exactly how a file another author still owns gets deleted.
#
# This module is that conjunction, and nothing else: it takes the audit rows,
# the map collisions and the parity verdicts from their own readers (imported,
# never recomputed) and answers RETIRE-READY only when every condition holds
# at once. Otherwise the script reads OWNED with the ONE reason that blocks
# it, so a blocker can be worked instead of guessed. It never runs a script
# and never writes.
#
# Blocker precedence is pinned and documented: DECLARATION-STALE first,
# because an unresolved declaration is the one case where deleting the copy
# also deletes the only record of what it wrote (AC-RET3); PARITY-DEBT second,
# because a copy that has lost the ritual is the reason to keep the file, not
# to drop the record of it; COLLISION last, because it is the broadest fact
# and the one a human resolves by hand.
#
# Stdlib only, ASCII source, zero network, no clock, no write path.

import json
import os
import sys

import evidence_output_audit as EOA
import evidence_output_map as EOM
import evidence_parity as EVP

PATTERN = EOM.PATTERN
QA_DEFAULT = EOA.QA_DEFAULT

REASONS = ("DECLARATION-STALE", "PARITY-DEBT", "COLLISION")
READY = "RETIRE-READY"
OWNED = "OWNED"

ROW_KEYS = ("script", "verdict", "reason", "detail", "audit_status",
            "audit_reason", "parity", "parity_legs_missing")
REPORT_KEYS = ("dir", "qa", "pattern", "scripts", "retire_ready", "owned",
               "stale", "parity_debt", "collision", "audit_verdict",
               "map_verdict", "parity_verdict", "rows", "verdict")

USAGE = ("usage: retire_candidate.py [--dir PATH] [--pattern GLOB]\n"
         "       [--qa PATH] [--root PATH] [--json]\n"
         "exit 0 = at least one RETIRE-READY candidate and no input refused,\n"
         "2 = nothing is retirable, 3 = unreadable or absent input,\n"
         "5 = bad flags\n")


class RetireError(Exception):
    """A refused reading: the code names why, detail names the input."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def read_audit(root, directory, qa=QA_DEFAULT, pattern=PATTERN):
    """The audit reading, asked of its own reader (AC-RET1)."""
    return EOA.audit(root, directory, qa=qa, pattern=pattern)


def read_map(root, directory, pattern=PATTERN):
    """The declaration map, asked of its own reader (AC-RET1)."""
    return EOM.build(root, directory, pattern=pattern)


def read_parity(root, directory, pattern=PATTERN):
    """The parity scan, asked of its own reader (AC-RET1)."""
    return EVP.scan(root, directory, pattern=pattern)


def _audit_rows(report):
    return dict((row["script"], row) for row in report.get("rows") or [])


def _parity_rows(report):
    return dict((row["script"], row) for row in report.get("rows") or [])


def _collisions(report):
    """Per script: its first collision, ordered by declared path."""
    found = {}
    for item in report.get("collisions") or []:
        owners = item.get("scripts") or []
        for owner in owners:
            other = [entry for entry in owners
                     if entry.get("script") != owner.get("script")]
            if owner["script"] in found or not other:
                continue
            found[owner["script"]] = {"path": item.get("path", ""),
                                      "other": other[0]}
    return found


def _missing_legs(row):
    """The legs that are not PRESENT, in the reader's own pinned order."""
    names = []
    for leg in row.get("legs") or []:
        if leg.get("verdict") != "PRESENT":
            names.append(leg.get("name", ""))
    return names


def judge(audit, mapped, parity):
    """The join: three readings in, one verdict per script out. Pure."""
    audits = _audit_rows(audit)
    parities = _parity_rows(parity)
    collisions = _collisions(mapped)
    names = sorted(set(list(audits.keys()) + list(parities.keys())))
    rows = []
    for name in names:
        arow = audits.get(name)
        prow = parities.get(name)
        audit_status = arow.get("status") if arow else "NO-ROW"
        audit_reason = (arow.get("reason") or "") if arow else "NO-AUDIT-ROW"
        parity_verdict = prow.get("verdict") if prow else "NO-READING"
        missing = _missing_legs(prow) if prow else []
        reason = ""
        detail = ""
        if audit_status != "OK":
            reason = "DECLARATION-STALE"
            detail = audit_reason or "DECLARATION-UNRESOLVED"
        elif parity_verdict != "ALL-PRESENT":
            reason = "PARITY-DEBT"
            if missing:
                detail = "%s missing=%s" % (parity_verdict, ",".join(missing))
            else:
                detail = parity_verdict
        elif name in collisions:
            reason = "COLLISION"
            hit = collisions[name]
            detail = "shares %s with %s:%s" % (hit["path"],
                                               hit["other"].get("script", ""),
                                               hit["other"].get("line", ""))
        verdict = READY if not reason else OWNED
        rows.append({"script": name, "verdict": verdict, "reason": reason,
                     "detail": detail, "audit_status": audit_status,
                     "audit_reason": audit_reason,
                     "parity": parity_verdict,
                     "parity_legs_missing": missing})
    ready = [row for row in rows if row["verdict"] == READY]
    return {"scripts": len(rows),
            "retire_ready": len(ready),
            "owned": len(rows) - len(ready),
            "stale": sum(1 for row in rows
                         if row["reason"] == "DECLARATION-STALE"),
            "parity_debt": sum(1 for row in rows
                               if row["reason"] == "PARITY-DEBT"),
            "collision": sum(1 for row in rows
                             if row["reason"] == "COLLISION"),
            "audit_verdict": audit.get("verdict", ""),
            "map_verdict": mapped.get("verdict", ""),
            "parity_verdict": parity.get("verdict", ""),
            "rows": rows,
            "verdict": "CANDIDATES" if ready else "NOTHING"}


def resolve(root, directory, qa=QA_DEFAULT, pattern=PATTERN):
    """Read all three inputs through their own readers, then judge."""
    try:
        audit = read_audit(root, directory, qa=qa, pattern=pattern)
    except EOA.AuditError as exc:
        raise RetireError("E_RET_NO_INPUT", "%s %s" % (exc.code, exc.detail))
    try:
        mapped = read_map(root, directory, pattern=pattern)
    except EOM.OutputMapError as exc:
        raise RetireError("E_RET_NO_INPUT", "%s %s" % (exc.code, exc.detail))
    try:
        parity = read_parity(root, directory, pattern=pattern)
    except EVP.ParityError as exc:
        raise RetireError("E_RET_NO_INPUT", "%s %s" % (exc.code, exc.detail))
    for label, report in (("audit", audit), ("map", mapped),
                          ("parity", parity)):
        refused = report.get("unreadable") or []
        if refused:
            names = ",".join(str(item.get("script", item))
                             for item in refused[:4])
            raise RetireError("E_RET_UNREADABLE", "%s %s" % (label, names))
    report = judge(audit, mapped, parity)
    report["dir"] = directory
    report["qa"] = qa
    report["pattern"] = pattern
    return report


def render(report):
    """One header line plus one line per script, for a human reading stdout."""
    parts = ["RETIRE CANDIDATE dir=%s qa=%s pattern=%s scripts=%d "
             "retire_ready=%d owned=%d stale=%d parity_debt=%d collision=%d "
             "verdict=%s"
             % (report["dir"], report["qa"], report["pattern"],
                report["scripts"], report["retire_ready"], report["owned"],
                report["stale"], report["parity_debt"], report["collision"],
                report["verdict"])]
    for row in report["rows"]:
        parts.append("ROW %s %s reason=%s detail=%s"
                     % (row["script"], row["verdict"], row["reason"] or "-",
                        row["detail"] or "-"))
    return "\n".join(parts)


def to_json(report):
    """One byte-stable rendering over the pinned keys, in pinned order."""
    ordered = {}
    for key in REPORT_KEYS:
        if key in report:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, indent=2,
                      sort_keys=False) + "\n"


def parse_args(argv):
    """Pinned flags only; anything else is bad flags (exit 5)."""
    opts = {"dir": "src/os", "pattern": PATTERN, "qa": QA_DEFAULT,
            "root": None, "json": False}
    takes = {"--dir": "dir", "--pattern": "pattern", "--qa": "qa",
             "--root": "root"}
    flags = {"--json": "json"}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in flags:
            opts[flags[arg]] = True
            index += 1
        elif arg in takes:
            if index + 1 >= len(argv) or not argv[index + 1]:
                raise RetireError("E_RET_BAD_ARGS", arg + " needs a value")
            opts[takes[arg]] = argv[index + 1]
            index += 2
        else:
            raise RetireError("E_RET_BAD_ARGS", arg)
    if opts["root"] is None:
        opts["root"] = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", ".."))
    return opts


def main(argv):
    try:
        opts = parse_args(argv)
    except RetireError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5
    try:
        report = resolve(opts["root"], opts["dir"], qa=opts["qa"],
                         pattern=opts["pattern"])
    except RetireError as exc:
        sys.stderr.write("%s %s\n" % (exc.code, exc.detail))
        return 3
    if opts["json"]:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return 0 if report["retire_ready"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))