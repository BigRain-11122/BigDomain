"""Suite for the claims census: the numbers this company writes get a reader.

THREE criteria, AC-CLAIM1..3, pre-registered in the R3225 backlog PIN row
BEFORE this file and tools/claim_census.py existed.

R3224 measured the hole: the board wrote `LEDGER OK rows=2` while the ledger as
that round's own commit recorded it held one row, and nothing read the number
back - the probe for R3225 counted 307 `rows=<n>` tokens on the three faces and
found five of seven round-tagged claims disagreeing with their own commit.

AC-CLAIM1 grades the classification on a private world: a claim is captured
only when a landed file its own line names carries the same token, contradicted
when that citation carries the same shape with a different number or when the
line speaks about the live ledger and the number is not the ledger's, and
uncaptured when the line names nothing that could speak for it (prose, named,
never deleted and never counted as a measurement).

AC-CLAIM2 grades that the reader reads only: no writes to the three faces or the
ledger, the counts add up to the claims, one ledger parser (`qa_log`), and the
module stays ASCII.

AC-CLAIM3 grades the consumer: the closeout gate prints one CLAIMS row, carries
the counts as values, publishes them on a seventh named face, and still passes a
world whose prose contradicts itself - a written sentence is not a gate.

Usage: python test_claim_census.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TOOLS = os.path.join(REPO, "tools")
MODULE = os.path.join(TOOLS, "claim_census.py")
GATE = os.path.join(TOOLS, "closeout_gate.py")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
ROW = "claim-census"

sys.path.insert(0, TOOLS)
import claim_census as CC  # noqa: E402
import closeout_gate as CG  # noqa: E402

RESULTS = []

LEDGER_ROW = {"event": "REPLACED", "name": "inner.log", "new_bytes": 12,
              "new_sha16": "0123456789abcdef", "old_bytes": 3,
              "old_sha16": "fedcba9876543210", "ts": "2026-11-22T00:00:00Z"}


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def world(root, board_lines, ledger_rows=1, cited=()):
    """A private world: three faces, a ledger and the qa files it may name."""
    write(os.path.join(root, "src", "os", "backlog.md"), "\n".join(board_lines))
    write(os.path.join(root, "src", "os", "state.json"), '{"log": []}\n')
    write(os.path.join(root, "docs", "status-export.json"), '{"chain": {}}\n')
    rows = [dict(LEDGER_ROW) for _ in range(ledger_rows)]
    write(os.path.join(root, "state", "qa_replacements.jsonl"),
          "".join(json.dumps(row) + "\n" for row in rows))
    for name, text in cited:
        write(os.path.join(root, "qa", name), text)


def statuses(root, board_lines):
    found = []
    for line in board_lines:
        found.extend(CC.classify(root, line, ledger_rows_of(root)))
    return found


def ledger_rows_of(root):
    import qa_log as QL
    return QL.ledger_report(os.path.join(root, "state", QL.LEDGER_NAME),
                            evidence_dir=os.path.join(root, "qa"))["rows"]


def main():
    root = tempfile.mkdtemp(prefix="claims-")
    try:
        # ---- AC-CLAIM1: the five shapes of a written number. --------------
        bad1 = []
        cited_hit = ("inner.log",
                     "LEDGER OK rows=3 names=3 bad=0 stale=0 missing=0 broken=0\n")
        cited_off = ("other.log",
                     "LEDGER OK rows=2 names=2 bad=0 stale=0 missing=0 broken=0\n")
        citations = (cited_hit, cited_off, ("silent.log", "SUITE PASS 2/2\n"))
        board = [
            # a: names the live ledger and agrees with it -> captured
            "- live agrees LEDGER OK rows=1 names=1 bad=0 path=state/qa_replacements.jsonl",
            # b: names the live ledger and disagrees -> contradicted
            "- live lies LEDGER OK rows=9 names=9 bad=0 path=state/qa_replacements.jsonl",
            # c: cites a landed file that carries the same token -> captured
            "- cited twice LEDGER OK rows=3 bad=0 (qa/inner.log)",
            # d: cites a landed file carrying the same shape, other number
            "- cited wrong LEDGER OK rows=4 bad=0 (qa/other.log)",
            # e: bare prose, nothing to speak for it -> uncaptured
            "- prose only rows=7 in a sentence nobody can check",
            # f: cites a landed file with no rows shape at all -> uncaptured
            "- cites silence rows=5 (qa/silent.log)",
        ]
        world(root, board, ledger_rows=1, cited=citations)
        got = statuses(root, board)
        want = ["captured", "contradicted", "captured", "contradicted",
                "uncaptured", "uncaptured"]
        if [item["status"] for item in got] != want:
            bad1.append("statuses=%s" % [item["status"] for item in got])
        # The citation that does not exist must not be trusted either.
        ghost = ["- ghost citation LEDGER OK rows=3 bad=0 (qa/never-written.log)"]
        if [item["status"] for item in statuses(root, ghost)] != ["uncaptured"]:
            bad1.append("unlanded-citation-counted")
        # Derived, not declared: changing the ledger moves the live reading.
        world(root, board, ledger_rows=9, cited=citations)
        if [i["status"] for i in statuses(root, board)][:2] != ["contradicted",
                                                              "captured"]:
            bad1.append("live-count-not-derived")
        report("AC-CLAIM1", bool(bad1), ",".join(bad1))

        # ---- AC-CLAIM2: reads only, one parser, and the counts add up. ----
        bad2 = []
        world(root, board, ledger_rows=1, cited=citations)
        watched = [os.path.join(root, "src", "os", "backlog.md"),
                   os.path.join(root, "src", "os", "state.json"),
                   os.path.join(root, "docs", "status-export.json"),
                   os.path.join(root, "state", "qa_replacements.jsonl")]
        before = [(os.path.getsize(p), os.path.getmtime(p)) for p in watched]
        result = CC.census(root)
        after = [(os.path.getsize(p), os.path.getmtime(p)) for p in watched]
        if before != after:
            bad2.append("wrote-what-it-read")
        if result["claimed"] != (result["captured"] + result["contradicted"]
                                 + result["uncaptured"]):
            bad2.append("counts-do-not-add-up-%s" % result["claimed"])
        if result["claimed"] != len(board):
            bad2.append("claims=%d expected=%d" % (result["claimed"], len(board)))
        raw = io.open(MODULE, "rb").read()
        if any(byte > 126 or byte == 13 for byte in raw):
            bad2.append("not-ascii-lf")
        text = raw.decode("ascii")
        if text.count("ledger_report(") != 1:
            bad2.append("second-parser-%d" % text.count("ledger_report("))
        if "read_ledger(" in text or "json.loads" in text:
            bad2.append("own-parser")
        if CC.census_row(result).count("rows=") != 1:
            bad2.append("row-shape")
        report("AC-CLAIM2", bool(bad2), ",".join(bad2))

        # ---- AC-CLAIM3: the consumer reads, prints and never refuses. -----
        bad3 = []
        world(root, board, ledger_rows=1, cited=citations)
        reading = {}
        ok, row = CG.check_claims(root, reading=reading)
        if ok is not True:
            bad3.append("face-refused")
        if not row.startswith("CLAIMS "):
            bad3.append("row-prefix")
        census = CC.census(root)
        for key in ("claimed", "captured", "contradicted", "uncaptured", "rows"):
            if reading.get(key) != census[key]:
                bad3.append("reading-%s-%r" % (key, reading.get(key)))
        if "contradicted=0" in row:
            bad3.append("fixture-did-not-contradict")
        gate_text = io.open(GATE, encoding="utf-8").read()
        if gate_text.count('_timed(face_ms, "claims", check_claims') != 1:
            bad3.append("wiring")
        if gate_text.count('verdict["claims"] = dict(claims_reading)') != 1:
            bad3.append("publish")
        if '"claims"' not in gate_text.split("INFORMATIONAL_FACES")[1][:120]:
            bad3.append("not-named-informational")
        with io.open(REGISTRY, encoding="utf-8") as handle:
            reg = handle.read()
        found = re.search(r'test_claim_census\.py"\)\s*,\s*(\d+)', reg)
        if not found or int(found.group(1)) != 3:
            bad3.append("registry-count-%s" % (found.group(1) if found else "-"))
        if len(RESULTS) != 2:
            bad3.append("results-before-this-arm-%d" % len(RESULTS))
        report("AC-CLAIM3", bool(bad3), ",".join(bad3))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
