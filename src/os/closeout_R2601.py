"""R2601 closeout: queue row 633 closed with a DISCHARGED note plus one
measured successor seed, one backlog line, and the round log appended to
src/os/state.json. Every write is byte-measured and read back.

ASCII source. stdlib only. No clock, no network.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
STATE = os.path.join(ROOT, "src", "os", "state.json")

HEAD_PREFIX = b"- [ ] P2 tech seed (R2599,"
DISCHARGED = (
    b" [DISCHARGED R2601: src/os/suite_matrix_reconcile.py plus its"
    b" six-criteria suite shipped; the document was regenerated from the"
    b" CURRENT registry (64827 bytes, 635 rows, 4786 criteria, shipped check"
    b" PASS) and the six readability suites read 6/6 by measurement, so the"
    b" deadlock is gone at its birth site. AC-EDM1..AC-EDM6 SUITE PASS 6/6"
    b" twice identical plus 3 adjacent green]")

SEED = (
    b"- [ ] P2 tech seed (R2601, from this window own measured limit):"
    b" `src/os/suite_matrix_reconcile.py` - THREE limits MEASURED this window."
    b" (a) report(None, 'qa/reconcile-all-R2590.log') reads STALE-CONTENT even"
    b" though the leg IS RUNNER PASS, because the document records a different"
    b" leg; the honest word is an evidence-face mismatch naming BOTH legs, and"
    b" the shipped check face already prints one. (b) newest_pass_leg decodes"
    b" every qa/*.log until a PASS leg appears (measured 0.13s over the live"
    b" pile at R2601) with no bound and no count reported, so the reading cost"
    b" is invisible and grows with the pile. (c) a document that does not exist"
    b" reads NO-DOC under --write as well as --check (measured on a temp path),"
    b" so the face cannot bootstrap a document from an existing stamp source."
    b" Product: ONE reading that names the evidence-face difference apart from"
    b" a content difference, reports how many candidates it decoded, and can"
    b" compose a MISSING document from a --stamp-from source."
    b" Criteria AC-EDMB1..AC-EDMB6 pinned HERE BEFORE any code:"
    b" AC-EDMB1 an explicit RUNNER PASS leg that differs from the leg the"
    b" document records reads its own word naming BOTH legs (never a content"
    b" word), derived from the shipped doc_evidence_face at call time;"
    b" AC-EDMB2 the candidate walk reports how many files it decoded and stops"
    b" at the first PASS leg, and its cost is printed rather than hidden;"
    b" AC-EDMB3 a document that does not exist is composed from the"
    b" --stamp-from source when one is given, and still reads NO-DOC when none"
    b" is, with no byte written in that case;"
    b" AC-EDMB4 a document whose matrix table does not carry six cells per row"
    b" refuses with its own code naming the header shape instead of reading"
    b" zero rows;"
    b" AC-EDMB5 every R2601 answer survives beside the new ones (all five"
    b" verdict words, both counts, one verdict word on the CLI, the exit codes)"
    b" proved by a same-fixture comparison;"
    b" AC-EDMB6 pure ASCII, stdlib only, no clock, zero network, own reconcile"
    b" label and own suite.")

BACKLOG_LINE = (
    b"- [x] [done 2026-11-10 R2601] R2601 PRODUCT window on the queue head"
    b" state/queue/tech.md:633 prefix AC-EDM1 (criteria AC-EDM1..AC-EDM6 pinned"
    b" there at R2599 BEFORE any code). SHIPPED src/os/suite_matrix_reconcile.py"
    b" plus its six-criteria suite: report() asks the SHIPPED check face and"
    b" names ROWS-MISMATCH with BOTH counts, DOC-CURRENT, STALE-CONTENT,"
    b" RED-LEG (refused, nothing written) and NO-DOC; write() composes through"
    b" the shipped render keeping the document stamp and recorded provenance,"
    b" writes atomically with a read-back and a post-write shipped check, and"
    b" restores the previous bytes on failure. THE DEADLOCK WAS MEASURED AWAY:"
    b" a render from the newest PASS leg proved byte-identical on a temp path"
    b" before any byte of this window was written, then the REAL document was"
    b" regenerated from the CURRENT registry to 64827 bytes / 635 rows / 4786"
    b" criteria with the shipped check PASS and its evidence line naming the"
    b" newest PASS leg (630/630), and the six readability suites read 6/6 exit"
    b" 0 each by measurement. PROOF: AC-EDM1..AC-EDM6 SUITE PASS 6/6 TWICE"
    b" identical plus three adjacent suites green"
    b" (qa/suite-matrix-reconcile-R2601.log, 1650B, legs=2 identical=True"
    b" adjacent=3 fails=0) and a live reading"
    b" (qa/suite-matrix-reconcile-live-R2601.log, 279B, DOC-CURRENT, 635/4786)."
    b" REGISTRY 634/4780 -> 635/4786 recounted by import. HONEST: the battery"
    b" was NOT run (measured 4095.8s against a 25-minute window), so"
    b" reconcile-battery-R2596 stays OPEN with its target moved to 635/4786 and"
    b" the structural reds healed; three seeded limits were MEASURED this"
    b" window; Docker absent; the 19.9 debit and the real msgSecCheck still"
    b" wait on CEO physical items; tasks.md untouched.\n")

LOG = [
    "2026-11-10 R2601 PRODUCT window on the queue head the debt gate and the"
    " queue named (state/queue/tech.md:633 prefix AC-EDM1, criteria"
    " AC-EDM1..AC-EDM6 pinned in that row at R2599 BEFORE any code). Five"
    " readings at open: git status EMPTY at HEAD e5746104 equal to origin/main"
    " with no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the"
    " content-addressed decisions scan unmoved, benchmarks 2026-11-03 inside"
    " the seven-day gate; debt_gate read CLAIM-FIRST item=reconcile-battery-R2596"
    " open=37 first=1, queue_head named line 633 prefix AC-EDM1 claimable=15 and"
    " queue_floor read FLOOR-MET 5/5, 15/10, 10/10."
    " THE DEADLOCK WAS RE-MEASURED AND FOUND ESCAPABLE BEFORE ANY BYTE WAS"
    " WRITTEN: docs/sandbox-suite-matrix.md rendered 631 rows against a 634-row"
    " registry, and a render to a TEMP path from the newest RUNNER PASS leg"
    " (qa/reconcile-all-R2595-retry2.log) read byte-identical at 634 suites /"
    " 4780 criteria with its green line honestly reading 630/634 - so the"
    " R2599 statement that no document can move without a NEW green leg was a"
    " statement about a leg, not about the composition, and is named here"
    " rather than repeated.",
    "2026-11-10 R2601 SHIPPED src/os/suite_matrix_reconcile.py plus"
    " src/os/test_suite_matrix_reconcile.py. report() asks the SHIPPED check"
    " face (suite_matrix.main --check) and says one verdict word: DOC-CURRENT,"
    " ROWS-MISMATCH naming BOTH counts (the word this face adds), STALE-CONTENT,"
    " RED-LEG (refused at exit 3 with nothing written, and the shipped refusal"
    " proved unchanged byte for byte), NO-DOC. write() composes through the"
    " shipped render keeping the document own stamp and recorded --stamp-from"
    " provenance, writes the document atomically with a read-back, proves it"
    " through the shipped check face, and restores the previous bytes when"
    " either proof fails. PROOF measured not quoted: AC-EDM1..AC-EDM6 SUITE"
    " PASS 6/6 TWICE identical plus three adjacent suites green through the"
    " shipped capture callable (qa/suite-matrix-reconcile-R2601.log, 1650B,"
    " legs=2, identical=True, adjacent=3, fails=0), and a READ-ONLY live leg on"
    " the REAL tree (qa/suite-matrix-reconcile-live-R2601.log, 279B, utf-8,"
    " crlf=0, nul=0, bom=False) reading DOC-CURRENT at doc_rows=635 against"
    " registry_rows=635 / 4786 criteria on evidence leg 630/630. REGISTRY"
    " 634 suites / 4780 criteria -> 635 / 4786 by exactly one row, recounted by"
    " importing reconcile_all.SUITES. THE DOCUMENT WAS THEN REGENERATED FROM"
    " THE CURRENT REGISTRY through this window own face:"
    " docs/sandbox-suite-matrix.md 64827 bytes, 635 rows, 4786 criteria,"
    " shipped check PASS, evidence line naming the newest PASS leg and its own"
    " 630/630 suite count. THE SIX READABILITY SUITES THAT KEPT THE BATTERY RED"
    " ARE GREEN BY MEASUREMENT - all six read SUITE PASS 6/6 exit=0 individually"
    " (patterns label, patterns non-label, artifact disk text, evidence name,"
    " stamp text and the render consumer) - so the R2598 structural reds are"
    " healed at their birth site instead of being re-described.",
    "2026-11-10 R2601 honest disclosures: (a) TWO product points on the"
    " Executive Protocol scale - a runnable face with its own six-criteria"
    " suite AND a live document a maintainer can open - but no P-47 business"
    " surface moved, so every P-47 item still waits on CEO physical pieces;"
    " (b) THE BATTERY WAS NOT RUN: the last full leg measured 4095.8s against"
    " this window 25-minute budget, so reconcile-battery-R2596 stays OPEN and"
    " its target is moved to 635 events / 4786 criteria with the structural"
    " reds now healed, which is a smaller claim than a green battery and is not"
    " dressed up as one; (c) the successor seed names THREE limits MEASURED"
    " this window - an explicit RUNNER PASS leg older than the recorded one"
    " reads STALE-CONTENT rather than its own evidence-face word (0.04s),"
    " newest_pass_leg decodes the live pile in 0.13s with no bound and no count"
    " reported, and a missing document reads NO-DOC even under --write so the"
    " face cannot bootstrap from a stamp source; (d) the doc row counter counts"
    " SIX-cell rows only, so a future column layout would read zero rows - that"
    " is seeded rather than fixed; (e) Docker is absent on this host; (f) the"
    " real 19.9 debit and the real msgSecCheck still wait on CEO physical items"
    " (merchant id, mini-program appid/secret); (g) tasks.md was not touched,"
    " it is the P-47 canonical board; (h) BigDomain-OSLoop still needs an"
    " ELEVATED shell for its S4U re-registration (carried ceo-pending physical"
    " item loop-s4u-reconcile).",
    "R2601 tokens: local=~24k api=0 api_reason=product window - one five-silence"
    " scan with the debt gate, queue head and queue floor read, one deadlock"
    " re-measured on a temp path before any byte, one pre-registered face with"
    " its six criteria shipped plus its own suite, one suite green 6/6 twice"
    " identical plus three adjacent suites through the shipped capture callable,"
    " one read-only live leg on the real tree, one registry row recounted by"
    " import, one real document regenerated from the current registry and"
    " judged by the shipped check face, six readability suites re-run green"
    " individually, and the state/export closeout; zero cloud calls and zero"
    " external API touches",
]


def split_eol(raw):
    eol = b"\r\n" if b"\r\n" in raw else b"\n"
    return raw.split(eol), eol


def write_bytes(path, data):
    before = len(open(path, "rb").read())
    with open(path, "wb") as handle:
        handle.write(data)
    after = len(open(path, "rb").read())
    assert after == len(data), "E_WRITE_READBACK %s" % path
    print("  %s %dB -> %dB" % (os.path.basename(path), before, after))


def close_queue():
    raw = open(QUEUE, "rb").read()
    lines, eol = split_eol(raw)
    index = next(i for i, line in enumerate(lines)
                 if line.startswith(HEAD_PREFIX))
    row = lines[index]
    body = row[len(b"- [ ] "):]
    lines[index] = b"- [x] [done 2026-11-10 R2601] " + body + DISCHARGED
    lines.insert(index + 1, SEED)
    data = eol.join(lines)
    write_bytes(QUEUE, data)
    check = open(QUEUE, "rb").read().decode("utf-8")
    assert "done 2026-11-10 R2601" in check and "AC-EDMB1" in check
    print("  queue readback ok (done stamp + seed present)")


def backlog():
    raw = open(BACKLOG, "rb").read()
    write_bytes(BACKLOG, BACKLOG_LINE + raw)


def append_state():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    payload = json.loads(text)
    assert payload["tick"] == 2600, "E_TICK"
    marker = "\r\n ]\r\n}"
    assert text.endswith(marker), "E_LAYOUT"
    body = text[:-len(marker)]
    added = "".join(",\r\n" + " " * 16 + json.dumps(item)
                    for item in LOG)
    ticked = body.replace(' "tick": 2600,', ' "tick": 2601,', 1)
    assert ticked != body, "E_TICK_REPLACE"
    updated = ticked + added + marker
    check = json.loads(updated)
    assert check["tick"] == 2601
    assert check["log"][-len(LOG):] == LOG
    write_bytes(STATE, updated.encode("utf-8"))


if __name__ == "__main__":
    close_queue()
    backlog()
    append_state()
    print("PASS closeout R2601")