"""Replacement-ledger chain diagnosis (R3371; criteria AC-QCH1..AC-QCH6 were
pre-registered in src/os/backlog.md as the R3371 PIN BEFORE this file existed).

What this is for: state/qa_replacements.jsonl records every rewrite of a qa/
evidence file as (old identity -> new identity), and the chain face asks that
consecutive rows for one name link. Five rows do not link, and this window was
asked to decide, per break, whether a record was LOST or the break is a SHAPE
of the shipped writers.

The answer, measured rather than guessed: tools/battery_shard.py
stream_evidence publishes a RUNNING partial IN PLACE while a leg is still
running (a documented second writer). A same-window re-run therefore replaces
its own partial, and the later row's old identity is a transient that lands
nowhere - measured at R3371: the intermediate blob of every one of the five
breaks exists in no commit of its path, and the committed artifact is the
later row's new identity in all five.

So this tool reports, never repairs: it names each break, says what it
replaced where the row declares it, and classifies a break as progress-partial
ONLY on a conjunction of shipped facts (shard evidence name, no prev_kind
field, the in-place streamer still present in the shipped source). Anything
else is unexplained and the verdict is RED. The five historical breaks are
carried by name, not hand-edited away.

Read-only. Stdlib only, ASCII source, zero network. Exit 0 = no unexplained
break, 2 = at least one.
"""

import hashlib
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import qa_log  # noqa: E402

SHARD_SOURCE = os.path.join(BASE, "battery_shard.py")
SHARD_EVIDENCE = re.compile(r"^battery-shard-[A-Za-z0-9._-]+\.log$")
EVIDENCE_DIR = os.path.join(REPO, "qa")
LOCAL_EVIDENCE = re.compile(r"^[A-Za-z0-9._-]+\.log$")
KIND_DECLARED = "progress-declared"
KIND_PARTIAL = "progress-partial"
KIND_UNEXPLAINED = "unexplained"
LANDED_MATCH = "match"
LANDED_MISSING = "missing"
LANDED_MISMATCH = "mismatch"
LANDED_UNCHECKED = "unchecked"


def shipped_progress_writer():
    """True while the shipped shard runner still publishes a partial in place."""
    try:
        text = io.open(SHARD_SOURCE, "r", encoding="utf-8").read()
    except OSError:
        return False
    return ("PROGRESS_SENTINEL" in text
            and 'open(path, "w"' in text
            and "def stream_evidence(" in text)


def links(prev_record, record):
    """AC-QCH5: the chain law, stated once."""
    return (record.get("old_sha16") == prev_record.get("new_sha16")
            and record.get("old_bytes") == prev_record.get("new_bytes"))


def classify(name, prev_record, record, shipped):
    """AC-QCH5/AC-QCH6: what a break is, on shipped facts only."""
    declared = record.get("prev_kind")
    if declared == qa_log.PREV_KIND_PROGRESS:
        return KIND_DECLARED, "the row declares it replaced a progress partial"
    if declared is not None:
        return (KIND_UNEXPLAINED,
                "the row declares prev_kind=%s and an unlinked evidence row is "
                "a lost record" % declared)
    if not SHARD_EVIDENCE.match(name):
        return (KIND_UNEXPLAINED,
                "not a shard evidence name, so no in-place progress writer "
                "explains the gap")
    if not shipped:
        return (KIND_UNEXPLAINED,
                "the shipped streamer no longer publishes a partial in place, "
                "so the historical explanation no longer holds")
    return (KIND_PARTIAL,
            "shard evidence name, row predates prev_kind, and the shipped "
            "streamer still writes the partial in place")


def landed_state(name, final_record, evidence_dir=None):
    """AC-QCHL1: is the chain's last claim still the file on disk?

    A break whose later row still describes the file that is really there is
    history; a break whose later row describes bytes that are no longer on
    disk is the silent rewrite the ledger exists to catch. A file that is not
    there at all is not damage - retention may prune evidence - so it reads
    missing and never reddens on its own.
    """
    evidence_dir = EVIDENCE_DIR if evidence_dir is None else evidence_dir
    if not name or not LOCAL_EVIDENCE.match(name):
        return LANDED_UNCHECKED
    path = os.path.join(evidence_dir, name)
    try:
        with open(path, "rb") as handle:
            blob = handle.read()
    except OSError:
        return LANDED_MISSING
    if len(blob) != final_record.get("new_bytes"):
        return LANDED_MISMATCH
    if hashlib.sha256(blob).hexdigest()[:16] != final_record.get("new_sha16"):
        return LANDED_MISMATCH
    return LANDED_MATCH


def report(path=None, evidence_dir=None):
    """One reading of the ledger chain; the parser is qa_log's own."""
    path = qa_log.LEDGER if path is None else path
    located, bad = qa_log.read_ledger_located(path)
    shipped = shipped_progress_writer()
    previous = {}
    breaks = []
    for number, record in located:
        name = record.get("name")
        prev = previous.get(name)
        if prev is not None:
            prev_number, prev_record = prev
            if not links(prev_record, record):
                kind, why = classify(name, prev_record, record, shipped)
                breaks.append({"name": name, "prev_line": prev_number,
                               "line": number, "kind": kind, "why": why,
                               "prev_new_sha16": prev_record.get("new_sha16"),
                               "old_sha16": record.get("old_sha16"),
                               "old_bytes": record.get("old_bytes"),
                               "new_bytes": record.get("new_bytes")})
        previous[name] = (number, record)
    for entry in breaks:
        entry["landed"] = landed_state(
            entry["name"], previous[entry["name"]][1], evidence_dir)
    unexplained = [b for b in breaks if b["kind"] == KIND_UNEXPLAINED]
    rewritten = [b for b in breaks if b["landed"] == LANDED_MISMATCH]
    return {"path": path, "rows": len(located), "names": len(previous),
            "bad": bad, "breaks": breaks, "shipped_progress_writer": shipped,
            "unexplained": unexplained, "rewritten": rewritten,
            "verdict": "RED" if (bad or unexplained or rewritten) else "OK"}


def do_check(path=None):
    """AC-QCH5: read-only, names every break, writes nothing."""
    data = report(path)
    progress = len([b for b in data["breaks"] if b["kind"] != KIND_UNEXPLAINED])
    landed_ok = len([b for b in data["breaks"]
                     if b["landed"] == LANDED_MATCH])
    landed_missing = len([b for b in data["breaks"]
                          if b["landed"] == LANDED_MISSING])
    sys.stdout.write(
        "QA-CHAIN %s path=%s rows=%d names=%d bad=%d breaks=%d progress=%d "
        "unexplained=%d landed_ok=%d landed_missing=%d rewritten=%d "
        "evidence=%s\n"
        % (data["verdict"], data["path"], data["rows"], data["names"],
           len(data["bad"]), len(data["breaks"]), progress,
           len(data["unexplained"]), landed_ok, landed_missing,
           len(data["rewritten"]), EVIDENCE_DIR))
    for entry in data["breaks"]:
        sys.stdout.write(
            "QA-CHAIN break name=%s prev_line=%d line=%d kind=%s "
            "old_bytes=%d new_bytes=%d prev_new_sha16=%s old_sha16=%s "
            "landed=%s why=%s\n"
            % (entry["name"], entry["prev_line"], entry["line"], entry["kind"],
               entry["old_bytes"], entry["new_bytes"],
               entry["prev_new_sha16"], entry["old_sha16"], entry["landed"],
               entry["why"]))
    sys.stdout.write("QA-CHAIN source=%s progress_writer=%s\n"
                     % (SHARD_SOURCE, data["shipped_progress_writer"]))
    return 0 if data["verdict"] == "OK" else 2


def main(argv):
    args = list(argv[1:])
    if not args or args[0] != "--check":
        sys.stdout.write("usage: qa_chain_diagnose.py --check [LEDGER_PATH]\n")
        return 2
    if len(args) > 2:
        sys.stdout.write("QA-CHAIN REFUSED --check takes at most one path\n")
        return 2
    return do_check(args[1] if len(args) == 2 else None)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
