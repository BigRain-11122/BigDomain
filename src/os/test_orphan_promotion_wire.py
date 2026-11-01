"""orphan_promotion_wire suite (R2356; criteria AC-OPW1..AC-OPW6 were
pre-registered inside the R2342 seed row of state/queue/tech.md:400 BEFORE this
code existed).

What this proves: the promotion writer now asks the ledger before it copies.
The ledger's own reader, validator, file listing and five-class judgement are
imported (patching the declaration reader moves this wire), a RECORDED claim
refuses naming the round, the canonical name, the declaring round and the round
the judgement runs until, a STALE claim refuses naming both digests, a lapsed
judgement permits the copy and names the until it supersedes, an UNRECORDED
canonical file and a LIVE record whose file is gone each refuse, every refusal
leaves the evidence directory listing-identical and digest-identical with no
.part residue, the CLI keeps orphan_promote's codes, and the wire holds no
write primitive of its own.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import evidence_variants as EV  # noqa: E402
import orphan_promote as OP  # noqa: E402
import orphan_promotion_ledger as OPL  # noqa: E402
import orphan_promotion_wire as OW  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "orphan_promotion_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-orphan-promotion-wire"

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


def body(runner, verdict="PASS"):
    """One battery-shaped leg: runner token, verdict token, sections."""
    lines = ["RUNNER %s" % runner]
    lines.append("SECTION matrix %s" % verdict)
    lines.append("SECTION fingerprint %s" % verdict)
    lines.append("SECTION profile %s" % verdict)
    lines.append("SECTION census %s" % verdict)
    lines.append("VERDICT %s" % verdict)
    return "\n".join(lines) + "\n"


def entry(round_label, canonical, digest, declared_by, until, size=0,
          source="", reason="test fixture"):
    """One declaration entry in the pinned shape orphan_promotion_ledger pins."""
    return OPL.render_entry(round_label, canonical, source, size, digest,
                            declared_by, until, reason)


def make_world(legs, canonical=None, canonical_text=None, entries=None,
               since="R9000", directory="qa", declaration=True):
    """A temp root with an evidence directory and (optionally) a ledger."""
    world = tempfile.mkdtemp(prefix="bigdomain-opw-")
    path = os.path.join(world, directory)
    os.makedirs(path)
    for name in sorted(legs):
        with io.open(os.path.join(path, name), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write(legs[name])
    if canonical is not None:
        text = canonical_text if canonical_text is not None else body("PASS")
        with io.open(os.path.join(path, canonical), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write(text)
    if declaration:
        state = os.path.join(world, "state")
        os.makedirs(state)
        rows = entries or []
        if rows:
            text = '{"since_round": "%s",\n "entries": [\n' % since
            text += ",\n".join("  " + json.dumps(row, ensure_ascii=True,
                                                 sort_keys=False)
                               for row in rows)
            text += "\n ]}\n"
        else:
            text = '{"since_round": "%s",\n "entries": [\n ]}\n' % since
        with io.open(os.path.join(state, "orphan_promotions.json"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return world


def listing(world, directory="qa"):
    return sorted(os.listdir(os.path.join(world, directory)))


def digests(world, directory="qa"):
    path = os.path.join(world, directory)
    out = {}
    for name in sorted(os.listdir(path)):
        full = os.path.join(path, name)
        if os.path.isfile(full):
            with open(full, "rb") as handle:
                out[name] = hashlib.sha256(handle.read()).hexdigest()
    return out


def digest_of_bytes(payload):
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def digest_of_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run_cli(args):
    proc = subprocess.Popen([sys.executable, MODULE] + args,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def refusal(call):
    """Run one call and return (code, detail), or (None, "") on success."""
    try:
        call()
    except OW.OrphanPromotionWireError as exc:
        return exc.code, exc.detail
    return None, ""


class Patched(object):
    """Swap the ledger's declaration reader for one criterion."""

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.saved = None

    def __enter__(self):
        self.saved = getattr(OPL, self.name)
        setattr(OPL, self.name, self.value)
        return self

    def __exit__(self, *exc):
        setattr(OPL, self.name, self.saved)
        return False


def ac_opw1():
    """The ledger reading is imported, and a patched one flows through."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    imported = ("import orphan_promotion_ledger as OPL" in source
                and "OPL.read_declaration(" in source
                and "OPL.declaration_entries(" in source
                and "OPL.canonical_files(" in source
                and "OPL.judge(" in source
                and "re.compile" not in source
                and "os.listdir" not in source)
    canonical = "reconcile-all-R9001.log"
    world = make_world({"reconcile-all-R9001b.log": body("PASS")},
                       canonical=canonical)
    try:
        live_digest = digest_of_file(os.path.join(world, "qa", canonical))
        before = OW.audit(world, "R9001")
        fabricated = {"since_round": "R9000",
                      "entries": [entry("R9001", canonical, live_digest,
                                        "R2342", "R9999")]}
        with Patched("read_declaration",
                     lambda root: (json.dumps(fabricated), fabricated)):
            after = OW.audit(world, "R9001")
        ok = (imported
              and before["ledger"] == OPL.UNRECORDED
              and before["decision"] == OW.REFUSE
              and after["ledger"] == OPL.RECORDED
              and after["decision"] == OW.REFUSE
              and "R2342" in after["detail"]
              and "R9999" in after["detail"])
        if not ok:
            print("  measured: imported=%r before=%r after=%r detail=%r"
                  % (imported, before["ledger"], after["ledger"],
                     after["detail"]), flush=True)
        check(ok, "AC-OPW1 ledger reading imported, patched reading honoured")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_opw2():
    """A recorded canonical target refuses naming its claim, copies nothing."""
    canonical = "reconcile-all-R9002.log"
    text = body("PASS")
    world = make_world({"reconcile-all-R9002b.log": body("PASS")},
                       canonical=canonical, canonical_text=text,
                       entries=[entry("R9002", canonical,
                                      digest_of_bytes(text), "R2342",
                                      "R9999")])
    try:
        before = listing(world)
        canonical_path = os.path.join(world, "qa", canonical)
        before_digest = digest_of_file(canonical_path)
        code, detail = refusal(
            lambda: OW.promote(world, "R9002", execute=True))
        ok = (code == "E_OPW_RECORDED"
              and "R9002" in detail
              and canonical in detail
              and "R2342" in detail
              and "R9999" in detail
              and listing(world) == before
              and digest_of_file(canonical_path) == before_digest
              and not any(name.endswith(OP.PART_SUFFIX)
                          for name in listing(world)))
        if not ok:
            print("  measured: code=%r detail=%r tree=%r"
                  % (code, detail, listing(world)), flush=True)
        check(ok, "AC-OPW2 recorded target refuses naming its claim")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_opw3():
    """A STALE entry refuses naming the recorded and the on-disk digest."""
    canonical = "reconcile-all-R9003.log"
    text = "RUNNER PASS\nVERDICT PASS\n"
    recorded = digest_of_bytes("bytes the record remembers\n")
    world = make_world({"reconcile-all-R9003b.log": body("PASS")},
                       canonical=canonical, canonical_text=text,
                       entries=[entry("R9003", canonical, recorded, "R2342",
                                      "R9999")])
    try:
        before = listing(world)
        reading = OW.audit(world, "R9003")
        live = digest_of_file(os.path.join(world, "qa", canonical))
        code, detail = refusal(
            lambda: OW.promote(world, "R9003", execute=True))
        ok = (reading["ledger"] == OPL.STALE
              and reading["decision"] == OW.REFUSE
              and reading["recorded_digest"] == recorded
              and reading["live_digest"] == live
              and code == "E_OPW_STALE"
              and recorded in detail
              and live in detail
              and listing(world) == before)
        if not ok:
            print("  measured: ledger=%r code=%r detail=%r digests=%r/%r"
                  % (reading["ledger"], code, detail,
                     reading["recorded_digest"], reading["live_digest"]),
                  flush=True)
        check(ok, "AC-OPW3 stale gives up both digests and copies nothing")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_opw4():
    """An expired judgement permits the copy and names the lapsed until."""
    lapsed = "reconcile-all-R9600.log"
    world = make_world({"reconcile-all-R9600b.log": body("PASS")},
                       entries=[entry("R9600", lapsed,
                                      digest_of_bytes("gone\n"), "R9300",
                                      "R9500")])
    present = "reconcile-all-R9700.log"
    present_text = body("PASS")
    holds = make_world({"reconcile-all-R9700b.log": body("PASS")},
                       canonical=present, canonical_text=present_text,
                       entries=[entry("R9700", present,
                                      digest_of_bytes(present_text), "R9300",
                                      "R9650")])
    try:
        reading = OW.audit(world, "R9600")
        done = OW.promote(world, "R9600", execute=True)
        target = os.path.join(world, "qa", lapsed)
        source = os.path.join(world, "qa", "reconcile-all-R9600b.log")
        reading_present = OW.audit(holds, "R9700")
        gate_present = OW.gate(holds, "R9700")
        ok = (reading["ledger"] == OW.LAPSED
              and reading["decision"] == OW.ALLOW
              and "R9500" in reading["detail"]
              and "R9300" in reading["detail"]
              and done["wrote"] is True
              and done["verdict"] == "PROMOTED"
              and os.path.isfile(target)
              and digest_of_file(target) == digest_of_file(source)
              and reading_present["ledger"] == OW.LAPSED
              and reading_present["decision"] == OW.ALLOW
              and "R9650" in reading_present["detail"]
              and gate_present["decision"] == OW.ALLOW)
        if not ok:
            print("  measured: reading=%r done=%r present=%r"
                  % (reading, done["verdict"], reading_present), flush=True)
        check(ok, "AC-OPW4 expired judgement permits and names its until")
    finally:
        for item in (world, holds):
            shutil.rmtree(item, ignore_errors=True)


def ac_opw5():
    """The refusal leaves evidence untouched, no residue, codes as pinned."""
    canonical = "reconcile-all-R9007.log"
    text = body("PASS")
    refuse_world = make_world({"reconcile-all-R9007b.log": body("PASS")},
                              canonical=canonical, canonical_text=text,
                              entries=[entry("R9007", canonical,
                                             digest_of_bytes(text), "R2342",
                                             "R9999")])
    clean_world = make_world({
        "reconcile-all-R9008a.log": body("FAIL", "FAIL"),
        "reconcile-all-R9008b.log": body("PASS"),
    })
    blind_world = make_world({"reconcile-all-R9009b.log": body("PASS")},
                             declaration=False)
    try:
        before = digests(refuse_world)
        code_refuse, out_refuse, _ = run_cli(
            ["--promote", "R9007", "qa", "--root", refuse_world])
        untouched = (digests(refuse_world) == before
                     and not any(name.endswith(OP.PART_SUFFIX)
                                 for name in listing(refuse_world)))
        code_plan, out_plan, _ = run_cli(
            ["--plan", "R9008", "qa", "--root", clean_world])
        code_promote, _, _ = run_cli(
            ["--promote", "R9008", "qa", "--root", clean_world])
        code_again, _, _ = run_cli(
            ["--promote", "R9008", "qa", "--root", clean_world])
        code_blind, out_blind, _ = run_cli(
            ["--plan", "R9009", "qa", "--root", blind_world])
        code_bad, _, _ = run_cli(["--plan", "R9008", "--nope"])
        code_none, _, _ = run_cli([])
        ok = (code_refuse == 2 and "E_OPW_RECORDED" in out_refuse
              and untouched
              and code_plan == 0 and "ORPHAN PROMOTION WIRE action=PLAN"
              in out_plan
              and code_promote == 0 and code_again == 2
              and code_blind == 3 and "E_OPW_NO_DECL" in out_blind
              and code_bad == 5 and code_none == 5)
        if not ok:
            print("  measured: refuse=%r untouched=%r plan=%r promote=%r "
                  "again=%r blind=%r/%r bad=%r none=%r"
                  % (code_refuse, untouched, code_plan, code_promote,
                     code_again, code_blind, out_blind.strip(), code_bad,
                     code_none), flush=True)
        check(ok, "AC-OPW5 refusal is byte-identical, codes stay as pinned")
    finally:
        for item in (refuse_world, clean_world, blind_world):
            shutil.rmtree(item, ignore_errors=True)


def ac_opw6():
    """Pure ASCII, stdlib only, zero network, no clock, no write primitive."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    imports = re.findall(r"^import (\w+)", source, re.MULTILINE)
    stdlib_only = sorted(set(imports)) == ["evidence_variants", "json",
                                           "orphan_promote",
                                           "orphan_promotion_ledger", "os",
                                           "sys"]
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    writes = (source.count("os.replace(") + source.count('"wb"')
              + source.count("os.remove(") + source.count("os.unlink(")
              + source.count("shutil.rmtree"))
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_orphan_promotion_wire.py" in runner)
    ok = (ascii_only and no_net and stdlib_only and no_clock and writes == 0
          and wired)
    if not ok:
        print("  measured: ascii=%r net=%r imports=%r clock=%r writes=%d "
              "wired=%r"
              % (ascii_only, no_net, sorted(set(imports)), no_clock, writes,
                 wired), flush=True)
    check(ok, "AC-OPW6 ASCII, stdlib only, no write primitive, wired")


def main():
    print("orphan_promotion_wire suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_opw1()
    ac_opw2()
    ac_opw3()
    ac_opw4()
    ac_opw5()
    ac_opw6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())