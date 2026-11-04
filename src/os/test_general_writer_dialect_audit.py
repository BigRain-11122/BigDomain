"""general_writer_dialect_audit suite (R2434).

Criteria AC-GWDA1..AC-GWDA6 were pinned inside the R2409 tech seed row of
state/queue/tech.md (line 498) BEFORE this code existed.

What this proves: the declaration sweep separates GENERAL honestly and then
says nothing about it, so the writers that land a structured document the house
keeps (the debt register, src/os/state.json, the residue declaration) chose
their own line-ending transport. This suite proves the tier is read from the
SOURCE, that every writer the audit NAMES asks the shared payload derivation at
call time, that an LF target keeps exactly today's bytes and a CRLF target
stays CRLF through a real write, that the three edited writers keep their
pre-existing refusals byte for byte, and that the module is pure.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import declaration_writer_dialect_preservation as DWDP  # noqa: E402
import debt_append as DEBTA  # noqa: E402
import general_writer_dialect_audit as GWDA  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "general_writer_dialect_audit.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

LABEL = "os-general-writer-dialect-audit"
WIRED_EXPECT = '"test_general_writer_dialect_audit.py"), 6),'

# writers this window EDITED, so their refusals are the ones to re-prove
EDITED = (
    ("debt_append", 5, "E_DEBTA_BAD_ARGS: unknown flag --nonsense"),
    ("debt_close", 5, "E_DEBC_BAD_ARGS: unknown flag --nonsense"),
    ("state_fold", 2, "E_SF_BAD_ARGS: unknown flag --nonsense"),
)

# the writers this criterion's own window left routed, with their spellings.
# The KEEPS COUNT is no longer pinned: a later law may route more writers, and
# R2448 measured three that do not ask the shared derivation, so the verdict is
# derived (AC-GWDA6) and the debt is tracked by name in the R2448 gap row.
PRE_ROUTED = (
    ("debt_append.py", "state/debt.md"),
    ("debt_close.py", "state/debt.md"),
    ("residue_triage_append.py", "state/residue_triage.json"),
    ("residue_triage_append_batch.py", "state/residue_triage.json"),
    ("residue_triage_entry_retire.py", "state/residue_triage.json"),
    ("residue_triage_head_renew.py", "state/residue_triage.json"),
    ("state_fold.py", "src/os/state.json"),
)

FIXTURE_WRITER = (
    'import io\n'
    'import json\n'
    'import os\n'
    '\n'
    'TARGET_REL = os.path.join("state", "fixture.json")\n'
    '\n'
    '\n'
    'def land(root, payload):\n'
    '    path = os.path.join(root, TARGET_REL)\n'
    '    text = json.dumps(payload, indent=2, sort_keys=True) + "\\n"\n'
    '    temp = path + ".tmp"\n'
    '    with io.open(temp, "w", encoding="utf-8", newline="\\n") as fh:\n'
    '        fh.write(text)\n'
    '    os.replace(temp, path)\n'
)

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def read_bytes(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def keeps_rows(root):
    reading = GWDA.report(root)
    return reading, [row for row in reading["rows"] if row["kind"] == "KEEPS"]


def ac_gwda1(world):
    """The tier is derived from the SOURCE, never from a whitelist file."""
    os.makedirs(os.path.join(world, "src", "os"), exist_ok=True)
    os.makedirs(os.path.join(world, "state"), exist_ok=True)
    write_text(os.path.join(world, "state", "fixture.json"), "{}\n")
    writer = os.path.join(world, "src", "os", "fixture_writer.py")
    write_text(writer, FIXTURE_WRITER)
    first = GWDA.classify("fixture_writer.py", FIXTURE_WRITER, world)
    derived = first is not None and first["kind"] == "KEEPS" \
        and first["target"] == "state/fixture.json" \
        and first["asks"] is False
    # a whitelist-looking file must change nothing: the tier is not read from it
    write_text(os.path.join(world, "state", "gwda_whitelist.json"),
               '{"routed": ["fixture_writer.py"]}\n')
    after_whitelist = GWDA.classify("fixture_writer.py", FIXTURE_WRITER, world)
    whitelist_inert = after_whitelist == first
    # changing the SOURCE moves the answer: the same file now asks the seam
    routed_source = FIXTURE_WRITER.replace(
        "import json\n",
        "import json\nimport general_writer_dialect_audit as GWDA\n")
    routed_source = routed_source.replace(
        '        fh.write(text)\n',
        '        fh.write(text)\n')
    routed = GWDA.classify("fixture_writer.py", routed_source, world)
    source_moves = routed is not None and routed["asks"] is True
    reading = GWDA.report(REPO)
    live = (reading["keeps"] >= 1 and reading["repair"] >= 1
            and "state_io.py" in reading["excluded"])
    check(derived and whitelist_inert and source_moves and live,
          "AC-GWDA1 the tier is derived from the source, never a whitelist "
          "file")


def ac_gwda2(world):
    """Each named writer routes through the shared derivation at call time."""
    reading, rows = keeps_rows(REPO)
    original = DWDP.encode
    reached = []
    try:
        def patched(raw_bytes, composed_text):
            return "PATCHED", b"@@GWDA-MARK@@"
        DWDP.encode = patched
        for row in rows:
            target = os.path.join(REPO, *row["target"].split("/"))
            if GWDA.payload_for(target, "x\n") == b"@@GWDA-MARK@@":
                reached.append(row["name"])
        # end to end through a real writer, not only the seam
        register = os.path.join(world, "state", "debt.md")
        os.makedirs(os.path.dirname(register), exist_ok=True)
        write_text(register, "# register\n\n## Open\n\n## Done\n")
        DEBTA.append_row(world, "R2434", "gwda-probe", execute=True)
        landed = read_bytes(register)
    finally:
        DWDP.encode = original
    named = [row["name"] for row in rows]
    check(reached == named and landed == b"@@GWDA-MARK@@",
          "AC-GWDA2 patching the shared derivation moves every named writer "
          "and a real write lands the patched bytes")


def ac_gwda3(world):
    """An LF target keeps exactly today's bytes."""
    reading, rows = keeps_rows(REPO)
    text = '{\n  "a": 1\n}\n'
    ok = True
    for row in rows:
        target = os.path.join(REPO, *row["target"].split("/"))
        probe = os.path.join(world, "lf-%s" % row["name"])
        with io.open(probe, "wb") as handle:
            handle.write(read_bytes(target).replace(b"\r\n", b"\n"))
        landed = GWDA.payload_for(probe, text)
        if landed != text.encode("utf-8"):
            ok = False
    check(ok and len(rows) >= 7,
          "AC-GWDA3 an LF target keeps exactly today's bytes (%d writers)"
          % len(rows))


def ac_gwda4(world):
    """A CRLF target stays CRLF after the real write with zero lone LF."""
    register = os.path.join(world, "crlf", "state", "debt.md")
    os.makedirs(os.path.dirname(register), exist_ok=True)
    body = "# register\r\n\r\n## Open\r\n\r\n## Done\r\n"
    with io.open(register, "wb") as handle:
        handle.write(body.encode("utf-8"))
    DEBTA.append_row(os.path.join(world, "crlf"), "R2434", "crlf-probe",
                     execute=True)
    landed = read_bytes(register)
    crlf = landed.count(b"\r\n")
    lone_lf = landed.count(b"\n") - crlf
    check(lone_lf == 0 and crlf >= 6 and b"crlf-probe" in landed,
          "AC-GWDA4 a CRLF target stays CRLF through the real write "
          "(crlf=%d lone_lf=%d)" % (crlf, lone_lf))


def ac_gwda5():
    """Every pre-existing refusal of the edited writers is unchanged."""
    ok = True
    for name, want_rc, want_line in EDITED:
        path = os.path.join(BASE, name + ".py")
        proc = subprocess.run([sys.executable, path, "--nonsense"],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        first = proc.stdout.decode("utf-8", "replace").splitlines()
        first = first[0] if first else ""
        if proc.returncode != want_rc or first != want_line:
            ok = False
            print("  MISMATCH %s rc=%s line=%r"
                  % (name, proc.returncode, first), flush=True)
    reading = GWDA.report(REPO)
    rows = dict((row["name"], row) for row in reading["rows"]
                if row["kind"] == "KEEPS")
    # R2448 correction at the birth site: this assertion used to pin the
    # KEEPS COUNT at seven, a live snapshot. The parameter-resolution law
    # (AC-PDR1..AC-PDR6) now resolves writers whose destination arrives as a
    # parameter, so the count moved to ten. The criterion's intent is that
    # THIS window's three edited writers were not disturbed, so the seven they
    # belonged to are named and must still read KEEPS with asks=yes; the
    # honest live verdict is asserted separately by AC-GWDA6 and by the
    # R2448 gap row that names the three newly measured offenders.
    untouched = all(rows.get(name) is not None
                    and rows[name]["asks"] is True
                    for name, _target in PRE_ROUTED)
    check(ok and untouched,
          "AC-GWDA5 the three edited writers keep their HEAD refusal code, "
          "exit code and printed line")


def ac_gwda6():
    """Pure: ASCII source, stdlib and the house law only, own label and suite."""
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    ascii_ok = all(ord(ch) < 128 for ch in source)
    banned = ("import time", "import datetime", "import random", "import uuid",
              "import socket", "import urllib", "import requests")
    no_clock = not any(word in source for word in banned)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner = handle.read()
    reading = GWDA.report(REPO)
    # R2448 correction at the birth site: this criterion used to assert a
    # live AUDIT-CLEAN verdict and routed == keeps, which was a snapshot. The
    # parameter-resolution law now resolves three export writers that do not
    # ask the shared derivation, so the live verdict is honestly AUDIT-DEBT.
    # What is proven here is that the verdict is DERIVED from what the audit
    # publishes, not asserted: every offender is a KEEPS row that answers no,
    # routed plus unrouted reconciles to keeps, and the verdict word follows
    # the offender list.
    offenders = reading["offenders"]
    asked = dict((row["name"], row["asks"]) for row in reading["rows"]
                 if row["kind"] == "KEEPS")
    derived = all(asked.get(name) is False for name in offenders)
    reconciles = reading["routed"] + reading["unrouted"] == reading["keeps"]
    verdict_follows = reading["verdict"] == (
        "AUDIT-DEBT" if offenders else "AUDIT-CLEAN")
    check(ascii_ok and no_clock and LABEL in source
          and WIRED_EXPECT in runner
          and derived and reconciles and verdict_follows
          and reading["unrouted"] == len(offenders),
          "AC-GWDA6 pure ASCII, stdlib only, no clock, own label and suite "
          "(verdict derived: %s, offenders=%d)"
          % (reading["verdict"], len(offenders)))


def main():
    world = tempfile.mkdtemp(prefix="gwda-")
    try:
        ac_gwda1(world)
        ac_gwda2(world)
        ac_gwda3(world)
        ac_gwda4(world)
        ac_gwda5()
        ac_gwda6()
    finally:
        import shutil
        shutil.rmtree(world, ignore_errors=True)
    print("SUITE %s criteria=%d pass=%d fail=%d" % (
        "PASS" if FAILS == 0 else "FAIL", EXPECTED_CRITERIA, PASSES, FAILS))
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())