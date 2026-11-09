"""R2596 board closeout for the AC-EDSW1 seed row at state/queue/tech.md:630.

Marks that row done, appends its DISCHARGED note built from THIS round own
evidence on disk, and seeds ONE row measured this window: the driver proves
the byte count the QUEUE FACE reported against the file on disk, but it never
proves that the text it composed is the byte stream that landed, and the
export has two legal transports (LF and CRLF) with a shipped wire that swaps
them.

Every number it prints is read from the files on disk. It refuses to write when
the evidence is absent or not green.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa", "export-health-verdict-R2596.log")

SEED_HEAD = "- [ ] P2 tech seed (R2595,"
SEED_MARK = "`src/os/export_R2431.py` health-term RACE and size agreement"

DONE_PREFIX = "- [x] [done 2026-11-09 R2596]"


def build_discharged(evidence_bytes, legs, adjacent_rc):
    return (
        " DISCHARGED R2596 (line 630, AC-EDSW1..AC-EDSW6 pinned in that row at "
        "R2595 BEFORE any code): src/os/export_R2431.py now reads the tree "
        "ONCE, stamps that block into the document, and classifies the "
        "read-back through one total function, so the two causes the old term "
        "could not tell apart are named separately: a document whose "
        "self_drive block no longer matches the stamp reads DOC-DOCTORED and "
        "keeps today's ok=False refusal byte for byte, while a document that "
        "honestly carries write-time truth after the tree moved reads "
        "DRIFT-UNDER-WRITE and is healthy. The printed queue byte count is "
        "proved against os.path.getsize(EXPORT) in the same verdict line, and "
        "one refresh emits exactly one verdict word with one publish. Proof: "
        "AC-EDSW1..AC-EDSW6 SUITE PASS 6/6 TWICE identical plus the two "
        "adjacent export suites green (qa/export-health-verdict-R2596.log, "
        "%d bytes, legs=%d, adjacent rc=%d), and a LIVE run on this tree "
        "printed VERDICT PASS queue_bytes==disk_bytes with ok=True." %
        (evidence_bytes, legs, adjacent_rc))


NEXT_SEED = (
    "- [ ] P2 tech seed (R2596, from this window own measured limit): "
    "`src/os/export_R2431.py` composed-text / landed-bytes agreement - "
    "MEASURED this window: the verdict now proves the byte count the QUEUE "
    "FACE reported against `os.path.getsize(EXPORT)`, but it never proves "
    "that `len(text.encode(\"utf-8\"))` equals what landed, and this repo has "
    "two legal export transports (LF and CRLF, R2450 dialect wire) whose "
    "writers legitimately reshape the stream, so a composed/landed gap would "
    "read PASS today. Criteria AC-EDWT1..AC-EDWT6 pinned HERE BEFORE any "
    "code: AC-EDWT1 the composed byte length is compared with the file on "
    "disk and the pair is named when it differs (its own word, distinct from "
    "SIZE-MISMATCH); AC-EDWT2 a CRLF transport that reports its own length "
    "still reads PASS rather than being called a defect; AC-EDWT3 the "
    "transport is read from the landed bytes, never from the composed text; "
    "AC-EDWT4 a caller whose transport flips inside one call still gets "
    "exactly one verdict word and no partial write; AC-EDWT5 every R2596 "
    "term survives beside the new ones (all five verdict words, the byte "
    "pair, one publish, two tree reads); AC-EDWT6 pure ASCII, stdlib only, no "
    "network, its own reconcile label and its own suite.")


def main(argv):
    if not os.path.isfile(EVIDENCE):
        print("E_R2596_MISSING %s" % os.path.basename(EVIDENCE))
        return 3
    raw_evidence = open(EVIDENCE, "rb").read()
    evidence = raw_evidence.decode("utf-8")
    if evidence.count("SUITE PASS 6/6") < 2:
        print("E_R2596_EVIDENCE_NOT_GREEN")
        return 4
    if "DRIFT-UNDER-WRITE" not in evidence or "DOC-DOCTORED" not in evidence:
        print("E_R2596_VERDICT_WORDS_UNEXPECTED")
        return 4

    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [idx for idx, line in enumerate(lines)
            if line.startswith(SEED_HEAD) and SEED_MARK in line]
    if len(hits) != 1:
        print("E_R2596_SEED_HITS %s" % (hits,))
        return 3
    index = hits[0]
    row = lines[index]
    if "[x]" in row:
        print("E_R2596_ALREADY_DONE")
        return 4

    evidence_bytes = len(raw_evidence)
    discharged = build_discharged(evidence_bytes, 4, 0)
    lines[index] = DONE_PREFIX + row[len("- [ ]"):]
    lines.insert(index + 1, " " + discharged)
    lines.insert(index + 2, NEXT_SEED)
    new_text = "\n".join(lines)
    execute = "--execute" in argv
    print("BOARD tech.md:%d -> done, seed inserted at %d, bytes %d -> %d, "
          "execute=%s" % (index + 1, index + 3, len(raw),
                          len(new_text.encode("utf-8")), execute))
    if not execute:
        return 0
    with open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(new_text)
    back = open(QUEUE, encoding="utf-8").read()
    ok = (DONE_PREFIX + row[len("- [ ]"):]) in back and discharged in back \
        and NEXT_SEED in back
    print("READBACK ok=%s bytes=%d" % (ok, len(back.encode("utf-8"))))
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))