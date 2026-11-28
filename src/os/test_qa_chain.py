"""Replacement-ledger chain suite (R3371; criteria AC-QCH1..AC-QCH6 were
pre-registered in src/os/backlog.md as the R3371 PIN before the code landed).

What this proves: the progress sentinel is read from the bytes, never guessed
(AC-QCH1); the writer records WHAT it replaced and the row says so (AC-QCH2);
the chain face excuses a break only on the later row's own declaration, and an
unlabelled row stays broken (AC-QCH3); a row that carries a lawful-looking but
illegal declaration is a named bad row (AC-QCH4); the diagnosis classifies the
live ledger on shipped facts and reddens on a break no shipped writer explains
(AC-QCH5); and the tool is ASCII, stdlib only, zero network and writes nothing
(AC-QCH6).

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import hashlib
import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, os.path.join(REPO, "tools"))

import qa_log as QL  # noqa: E402
import qa_chain_diagnose as QCD  # noqa: E402

EXPECTED_CRITERIA = 11
MODULE = os.path.join(REPO, "tools", "qa_chain_diagnose.py")
LABEL = "os-qa-chain"

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("  PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("  FAIL %s" % label, flush=True)


def world():
    return tempfile.mkdtemp(prefix="qach-")


def drop(path):
    shutil.rmtree(path, ignore_errors=True)


def live_ledger():
    return os.path.join(REPO, "state", QL.LEDGER_NAME)


def write_name(directory, name, text):
    return QL.do_write(name, text.encode("utf-8"), directory=directory)


def plant(directory, name, text):
    """An unrecorded in-place writer, the shape the shard streamer has."""
    with io.open(os.path.join(directory, name), "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write(text)


def run():
    sentinel = QL.PROGRESS_SENTINEL

    # AC-QCH1: the sentinel is read off the first line, whatever the EOL.
    check(QL.previous_kind((sentinel + "\nbody\n").encode("utf-8"))
          == QL.PREV_KIND_PROGRESS
          and QL.previous_kind((sentinel + "\r\nbody\r\n").encode("utf-8"))
          == QL.PREV_KIND_PROGRESS
          and QL.previous_kind(b"SHARD row os-x rc=0\n") == QL.PREV_KIND_EVIDENCE
          and QL.previous_kind(b"") == QL.PREV_KIND_EVIDENCE
          and QL.previous_kind((sentinel + " not the first line\n")
                               .encode("utf-8")) == QL.PREV_KIND_EVIDENCE
          and all(ord(ch) < 128 for ch in sentinel),
          "AC-QCH1 the progress sentinel is read from the first line only, "
          "CRLF tolerated, and the sentinel itself is ASCII")

    # AC-QCH2: the row records what it replaced.
    world_a = world()
    try:
        write_name(world_a, "qa-a.log", "one\n")
        write_name(world_a, "qa-a.log", "two\n")
        plant(world_a, "qa-a.log", sentinel + "\npartial\n")
        partial_bytes = io.open(os.path.join(world_a, "qa-a.log"),
                                "rb").read()
        write_name(world_a, "qa-a.log", "three\n")
        located, bad = QL.read_ledger_located(
            os.path.join(world_a, QL.LEDGER_NAME))
        rows = [r for _n, r in located if r["name"] == "qa-a.log"]
        check(len(rows) == 2 and not bad
              and rows[0].get("prev_kind") == QL.PREV_KIND_EVIDENCE
              and rows[1].get("prev_kind") == QL.PREV_KIND_PROGRESS
              and rows[1]["old_bytes"] == len(partial_bytes)
              and rows[1]["old_sha16"]
              == hashlib.sha256(partial_bytes).hexdigest()[:16],
              "AC-QCH2 a replacement over a progress partial records "
              "prev_kind=progress and the partial's own identity, while an "
              "ordinary rewrite records evidence")
    finally:
        drop(world_a)

    # AC-QCH3: a declared progress break is excused; an unlabelled one is not.
    world_b = world()
    try:
        ledger = os.path.join(world_b, QL.LEDGER_NAME)
        write_name(world_b, "battery-shard-x.log", "first\n")
        write_name(world_b, "battery-shard-x.log", "second\n")
        plant(world_b, "battery-shard-x.log", sentinel + "\npartial\n")
        write_name(world_b, "battery-shard-x.log", "third\n")
        plant(world_b, "battery-shard-x.log", "silent revert\n")
        write_name(world_b, "battery-shard-x.log", "fourth\n")
        report = QL.ledger_report(ledger, evidence_dir=world_b)
        check(len(report["excused"]) == 1 and len(report["broken"]) == 1
              and report["excused"][0][0] == "battery-shard-x.log"
              and report["broken"][0][0] == "battery-shard-x.log",
              "AC-QCH3 the chain face excuses only the row that declares it "
              "replaced a progress partial, and an unlabelled revert stays "
              "broken")
    finally:
        drop(world_b)

    # AC-QCH4: an illegal declaration is a named bad row.
    base = {"ts": "2026-11-24T00:00:00Z", "event": "REPLACED",
            "name": "x.log", "old_bytes": 1, "old_sha16": "a" * 16,
            "new_bytes": 2, "new_sha16": "b" * 16}
    absent = QL.ledger_row_problem(dict(base))
    lawful = [QL.ledger_row_problem(dict(base, prev_kind=kind))
              for kind in QL.PREV_KINDS]
    illegal = QL.ledger_row_problem(dict(base, prev_kind="guess"))
    check(absent is None and lawful == [None, None] and illegal == "prev_kind",
          "AC-QCH4 prev_kind is optional, both lawful values pass, and any "
          "other value is a named bad row")

    # AC-QCH5: the live reading is classified on shipped facts; an
    # unexplained break reddens the verdict.
    live = QCD.report()
    kinds = set(entry["kind"] for entry in live["breaks"])
    shard_names = all(QCD.SHARD_EVIDENCE.match(entry["name"])
                      for entry in live["breaks"])
    live_ok = (live["verdict"] == "OK" and not live["unexplained"]
                and not live["bad"] and shard_names
                and kinds <= {QCD.KIND_DECLARED, QCD.KIND_PARTIAL}
                and live["shipped_progress_writer"] is True)
    world_c = world()
    try:
        write_name(world_c, "ordinary.log", "first\n")
        write_name(world_c, "ordinary.log", "second\n")
        plant(world_c, "ordinary.log", "silent revert\n")
        write_name(world_c, "ordinary.log", "third\n")
        red = QCD.report(os.path.join(world_c, QL.LEDGER_NAME))
        red_ok = (red["verdict"] == "RED" and len(red["unexplained"]) == 1
                  and red["unexplained"][0]["name"] == "ordinary.log")
    finally:
        drop(world_c)
    check(live_ok and red_ok,
          "AC-QCH5 every live break is a shard-evidence progress partial on "
          "shipped facts, and a break no shipped writer explains reddens")

    # AC-QCH6: ASCII, stdlib only, zero network, and genuinely read-only.
    with io.open(MODULE, "rb") as fh:
        raw = fh.read()
    text_mod = raw.decode("utf-8")
    ascii_ok = all(ord(ch) < 128 for ch in text_mod)
    banned = ("import socket", "import ssl", "import http", "import urllib",
              "import requests", "from http", "from urllib",
              "subprocess", "os.remove", "os.rename")
    net_ok = not any(b in text_mod for b in banned)
    before = None
    if os.path.isfile(live_ledger()):
        before = hashlib.sha256(io.open(live_ledger(), "rb").read()).hexdigest()
    QCD.report()
    after = None
    if os.path.isfile(live_ledger()):
        after = hashlib.sha256(io.open(live_ledger(), "rb").read()).hexdigest()
    check(ascii_ok and net_ok and before == after
          and "read_ledger_located" in text_mod,
          "AC-QCH6 the diagnosis is ASCII, stdlib only, zero network, reuses "
          "the shipped parser and leaves the ledger byte-identical")

    # AC-QCHL1..AC-QCHL4: the chain's excuse must still be the file on disk.
    world_d = world()
    ledger_d = os.path.join(world_d, QL.LEDGER_NAME)
    evidence_d = os.path.join(world_d, "qa")
    os.makedirs(evidence_d)
    name_d = "battery-shard-lands.log"
    try:
        write_name(world_d, name_d, "first\n")
        write_name(world_d, name_d, "second\n")
        plant(world_d, name_d, sentinel + "\npartial\n")
        write_name(world_d, name_d, "third\n")
        os.replace(os.path.join(world_d, name_d),
                   os.path.join(evidence_d, name_d))
        landed = QCD.report(ledger_d, evidence_dir=evidence_d)
        match_ok = (landed["verdict"] == "OK"
                    and len(landed["breaks"]) == 1
                    and landed["breaks"][0]["landed"] == QCD.LANDED_MATCH
                    and not landed["rewritten"])
    finally:
        drop(world_d)
    check(match_ok,
          "AC-QCHL1 a break whose last row still describes the evidence file "
          "reads landed=match and never reddens")

    live = QCD.report()
    live_landed = [entry["landed"] for entry in live["breaks"]]
    check(live["verdict"] == "OK" and live_landed
          and all(state == QCD.LANDED_MATCH for state in live_landed)
          and not live["rewritten"],
          "AC-QCHL2 every live break is verified against the file on disk in "
          "the same window, not against a measurement from months ago")

    world_e = world()
    ledger_e = os.path.join(world_e, QL.LEDGER_NAME)
    evidence_e = os.path.join(world_e, "qa")
    os.makedirs(evidence_e)
    name_e = "battery-shard-silent.log"
    try:
        write_name(world_e, name_e, "first\n")
        write_name(world_e, name_e, "second\n")
        plant(world_e, name_e, sentinel + "\npartial\n")
        write_name(world_e, name_e, "third\n")
        os.replace(os.path.join(world_e, name_e),
                   os.path.join(evidence_e, name_e))
        with io.open(os.path.join(evidence_e, name_e), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write("silent rewrite\n")
        silent = QCD.report(ledger_e, evidence_dir=evidence_e)
        silent_ok = (silent["verdict"] == "RED"
                     and len(silent["rewritten"]) == 1
                     and silent["breaks"][0]["landed"] == QCD.LANDED_MISMATCH)
        os.remove(os.path.join(evidence_e, name_e))
        gone = QCD.report(ledger_e, evidence_dir=evidence_e)
        gone_ok = (gone["verdict"] == "OK"
                   and gone["breaks"][0]["landed"] == QCD.LANDED_MISSING
                   and not gone["rewritten"])
    finally:
        drop(world_e)
    check(silent_ok,
          "AC-QCHL3 an unrecorded rewrite of the evidence file leaves the "
          "chain's last row describing bytes that are gone, so it reads "
          "landed=mismatch and the verdict turns RED")
    check(gone_ok,
          "AC-QCHL4 a pruned evidence file reads landed=missing and is not "
          "called damage, so retention alone never reddens a lawful break")

    # AC-QCHL5: the reading is on the printed face, not only in the dict.
    buffer = io.StringIO()
    stdout = sys.stdout
    try:
        sys.stdout = buffer
        rc = QCD.do_check()
    finally:
        sys.stdout = stdout
    text_out = buffer.getvalue()
    head = [line for line in text_out.splitlines() if line.startswith("QA-CHAIN ")][0]
    rows = [line for line in text_out.splitlines()
            if line.startswith("QA-CHAIN break ")]
    check(rc == 0 and "landed_ok=%d" % len(rows) in head
          and "rewritten=0" in head
          and rows and all(" landed=" in line for line in rows),
          "AC-QCHL5 the printed face carries landed_ok, rewritten and one "
          "landed= token per break")


if __name__ == "__main__":
    run()
    print("SUITE %s %d/%d" % (
        "PASS" if FAILS == 0 else "FAIL", PASSES + FAILS, EXPECTED_CRITERIA),
        flush=True)
    sys.exit(0 if FAILS == 0 else 2)
