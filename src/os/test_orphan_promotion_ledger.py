"""orphan_promotion_ledger suite (R2342; criteria AC-OPL1..AC-OPL6 were
pre-registered inside the R2339 seed row of state/queue/tech.md:388 BEFORE this
code existed).

What this proves: a canonical evidence file that this house's own writer
produced can no longer be mistaken for one that was always there. The ledger is
read against the live evidence directory and every canonical file lands in
exactly one of five disjoint readings; a record whose bytes moved reads STALE
with both digests named rather than RECORDED; the canonical name law is asked
of orphan_promote and the evidence directory of orphan_trace, so patching
either moves this reader; an append is raw text with one atomic replace that
leaves every neighbour entry byte-identical and refuses a duplicate by naming
the recorded entry; and the reader itself never writes.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import orphan_promotion_ledger as OPL  # noqa: E402
import orphan_promote as OP  # noqa: E402
import orphan_trace as OT  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "orphan_promotion_ledger.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-orphan-promotion-ledger"

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


def leg(verdict="PASS"):
    return "RUNNER %s\nVERDICT %s\n" % (verdict, verdict)


def source_text():
    return io.open(MODULE, "r", encoding="utf-8").read()


def empty_declaration(since="R9000"):
    return ('{\n  "since_round": "%s",\n  "entries": [\n  ]\n}\n' % since)


def make_world(evidence=None, declaration=None, directory="qa"):
    """A temp root with one evidence directory and an optional declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-opl-")
    path = os.path.join(world, directory)
    os.makedirs(path)
    for name in sorted(evidence or {}):
        with io.open(os.path.join(path, name), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write(evidence[name])
    if declaration is not None:
        os.makedirs(os.path.join(world, "state"))
        with io.open(os.path.join(world, OPL.DECL_REL), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write(declaration)
    return world


def digest_of(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def tree_digest(root):
    """Every file under root with its digest, in a stable order."""
    rows = []
    for base, _dirs, names in os.walk(root):
        for name in sorted(names):
            path = os.path.join(base, name)
            rows.append((os.path.relpath(path, root).replace(os.sep, "/"),
                         digest_of(path)))
    rows.sort()
    return rows


def run_cli(args):
    proc = subprocess.Popen([sys.executable, MODULE] + args,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace")


def refusal(call):
    """Run one call and return (code, detail), or (None, "") on success."""
    try:
        call()
    except OPL.OrphanPromotionLedgerError as exc:
        return exc.code, exc.detail
    return None, ""


class Patched(object):
    """Swap one module attribute for the duration of one criterion."""

    def __init__(self, module, name, value):
        self.module = module
        self.name = name
        self.value = value
        self.saved = None

    def __enter__(self):
        self.saved = getattr(self.module, self.name)
        setattr(self.module, self.name, self.value)
        return self

    def __exit__(self, *exc):
        setattr(self.module, self.name, self.saved)
        return False


def ac_opl1():
    """The canonical law is orphan_promote's and the directory orphan_trace's."""
    source = source_text()
    imported = ("import orphan_promote as OP" in source
                and "import orphan_trace as OT" in source
                and "OP.canonical_name" in source
                and "OT.evidence_path" in source
                and "re.compile" not in source
                and "canonical_prefix" not in source)
    evidence = {"reconcile-all-R9001.log": leg(), "notes.txt": "x\n"}
    world = make_world(evidence, empty_declaration())
    try:
        _path, real = OPL.canonical_files(world)
        moved = (lambda number: "round-%s.log" % number)
        with Patched(OP, "canonical_name", moved):
            _patched_path, files = OPL.canonical_files(world)
        ok = imported and real == {"R9001": "reconcile-all-R9001.log"} \
            and files == {}
        if not ok:
            print("  measured: imported=%r real=%r patched=%r"
                  % (imported, real, files), flush=True)
        check(ok, "AC-OPL1 canonical law imported from orphan_promote")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_opl2():
    """Five disjoint readings; every canonical file lands in exactly one."""
    evidence = {
        "reconcile-all-R9001.log": leg(),
        "reconcile-all-R9002.log": leg(),
        "reconcile-all-R9003.log": leg(),
        "reconcile-all-R9004.log": leg(),
        "reconcile-all-R9009a.log": leg("FAIL"),
    }
    world = make_world(evidence, empty_declaration())
    try:
        path = os.path.join(world, "qa")
        for round_no in (9001, 9002, 9003):
            OPL.add(world, "R%d" % round_no, "R2342", "R2400",
                    reason="fixture", execute=True)
        target = os.path.join(path, "reconcile-all-R9002.log")
        with io.open(target, "a", encoding="utf-8", newline="\n") as handle:
            handle.write("later bytes\n")
        text, entries = OPL.read_declaration(world)
        gone = os.path.join(path, "reconcile-all-R9003.log")
        os.remove(gone)
        reported = OPL.check(world, round_no="R2342")
        classes = [row["class"] for row in reported["rows"]]
        file_rows = [row for row in reported["rows"]
                     if row["class"] != OPL.MISSING]
        ok = (reported["canonical"] == 3
              and reported["entries"] == 3
              and reported["recorded"] == 1
              and reported["stale"] == 1
              and reported["missing"] == 1
              and reported["unrecorded"] == 1
              and reported["expired"] == 0
              and len(file_rows) == reported["canonical"]
              and set(classes) == {OPL.RECORDED, OPL.STALE, OPL.MISSING,
                                   OPL.UNRECORDED}
              and reported["verdict"] == "LEDGER-DEBT")
        if not ok:
            print("  measured: %r" % (reported,), flush=True)
        check(ok, "AC-OPL2 four file-side readings are disjoint and complete")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_opl3():
    """A moved digest reads STALE naming both digests, never RECORDED."""
    evidence = {"reconcile-all-R9010.log": leg()}
    world = make_world(evidence, empty_declaration())
    try:
        planned = OPL.add(world, "R9010", "R2342", "R2400", reason="fixture",
                          execute=True)
        recorded = planned["digest"]
        first = OPL.check(world, round_no="R2342")
        path = os.path.join(world, "qa", "reconcile-all-R9010.log")
        with io.open(path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write("one more line\n")
        live = digest_of(path)
        second = OPL.check(world, round_no="R2342")
        stale = [row for row in second["rows"] if row["class"] == OPL.STALE]
        ok = (first["verdict"] == "CLEAN"
              and first["recorded"] == 1
              and second["stale"] == 1
              and second["recorded"] == 0
              and second["verdict"] == "LEDGER-DEBT"
              and len(stale) == 1
              and recorded[:12] in stale[0]["detail"]
              and live[:12] in stale[0]["detail"]
              and recorded != live)
        if not ok:
            print("  measured: first=%r second=%r" % (first, second),
                  flush=True)
        check(ok, "AC-OPL3 a moved digest reads STALE with both digests named")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_opl4():
    """Raw-text append, one atomic replace, duplicate refused, neighbours kept."""
    evidence = {
        "reconcile-all-R9020.log": leg(),
        "reconcile-all-R9021.log": leg("FAIL"),
    }
    world = make_world(evidence, empty_declaration())
    try:
        target = os.path.join(world, OPL.DECL_REL)
        before = io.open(target, "rb").read()
        OPL.add(world, "R9020", "R2342", "R2400", source="x-c.log",
                reason="first", execute=True)
        first_bytes = io.open(target, "rb").read()
        prefix_kept = first_bytes.startswith(before[:-len(b"\n  ]\n}\n")])
        report = OPL.add(world, "R9021", "R2342", "R2400", reason="second",
                         execute=True)
        second_bytes = io.open(target, "rb").read()
        _text, _payload = OPL.read_declaration(world)
        entries = OPL.declaration_entries(_text)
        code, detail = refusal(lambda: OPL.add(world, "R9020", "R2342",
                                              "R2400", reason="again"))
        residue = [name for name in os.listdir(os.path.dirname(target))
                   if name.endswith(OPL.TEMP_SUFFIX)]
        ok = (report["wrote"] is True
              and report["read_back_ok"] is True
              and prefix_kept
              and len(entries) == 2
              and entries[0]["source"] == "x-c.log"
              and entries[0]["reason"] == "first"
              and entries[1]["reason"] == "second"
              and code == OPL.E_OPL_DUP
              and "R9020" in detail
              and "reconcile-all-R9020.log" in detail
              and "R2342" in detail
              and residue == []
              and io.open(target, "rb").read() == second_bytes)
        if not ok:
            print("  measured: code=%r detail=%r entries=%r residue=%r"
                  % (code, detail, entries, residue), flush=True)
        check(ok, "AC-OPL4 append keeps neighbours, duplicate names the entry")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_opl5():
    """CLI 0/2/3/5, byte-stable --json, and the reader never writes."""
    evidence = {"reconcile-all-R9030.log": leg()}
    clean_world = make_world(evidence, empty_declaration())
    bare_world = make_world(evidence, None)
    try:
        OPL.add(clean_world, "R9030", "R2342", "R2400", reason="fixture",
                execute=True)
        digest_before = tree_digest(clean_world)
        first = run_cli(["--check", "--round", "R2342", "--root", clean_world])
        second = run_cli(["--check", "--round", "R2342", "--root",
                          clean_world])
        as_json = run_cli(["--check", "--round", "R2342", "--root",
                           clean_world, "--json"])
        debt = run_cli(["--check", "--round", "R2500", "--root", clean_world])
        bare = run_cli(["--check", "--round", "R2342", "--root", bare_world])
        bad_flags = run_cli(["--check", "--root", clean_world])
        bad_round = run_cli(["--add", "nope", "--declared-by", "R2342",
                             "--root", clean_world])
        parsed = json.loads(as_json[1])
        ok = (first[0] == 0 and second[0] == 0
              and first[1] == second[1]
              and as_json[0] == 0
              and json.loads(run_cli(["--check", "--round", "R2342", "--root",
                                      clean_world, "--json"])[1]) == parsed
              and tuple(parsed.keys()) == OPL.REPORT_KEYS
              and debt[0] == 2 and "LEDGER-DEBT" in debt[1]
              and bare[0] == 3 and OPL.E_OPL_NO_DECL in bare[1]
              and bad_flags[0] == 5
              and bad_round[0] == 5
              and tree_digest(clean_world) == digest_before)
        if not ok:
            print("  measured: first=%r debt=%r bare=%r flags=%r round=%r"
                  % (first[0], debt[0], bare[0], bad_flags[0], bad_round[0]),
                  flush=True)
        check(ok, "AC-OPL5 CLI codes, byte-stable json, zero writes")
    finally:
        shutil.rmtree(clean_world, ignore_errors=True)
        shutil.rmtree(bare_world, ignore_errors=True)


def ac_opl6():
    """Pure ASCII, stdlib only, zero network, no clock, plus its own label."""
    source = source_text()
    ascii_only = all(ord(char) < 128 for char in source)
    stdlib_ok = True
    for raw in source.split("\n"):
        line = raw.strip()
        if not line.startswith("import "):
            continue
        name = line.split()[1]
        if name in ("json", "os", "sys", "io", "hashlib", "subprocess"):
            continue
        # Every other import must be a sibling module of this directory,
        # never a third-party package.
        if not os.path.isfile(os.path.join(BASE, name + ".py")):
            stdlib_ok = False
    stdlib = stdlib_ok
    no_clock = ("import time" not in source and "import datetime" not in source
                and "time.time" not in source and "now()" not in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source.replace("http://", ""))
    no_shell = ("subprocess" not in source and "os.system" not in source)
    wiring = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"os-orphan-promotion-ledger"' in wiring
             and '"test_orphan_promotion_ledger.py"' in wiring)
    ok = (ascii_only and stdlib and no_clock and no_net and no_shell
          and wired and OPL.SUITE_LABEL == LABEL)
    if not ok:
        print("  measured: ascii=%r stdlib=%r clock=%r net=%r shell=%r "
              "wired=%r" % (ascii_only, stdlib, no_clock, no_net, no_shell,
                            wired), flush=True)
    check(ok, "AC-OPL6 pure ASCII, stdlib only, no clock, wired")


CRITERIA = (
    ("AC-OPL1", ac_opl1),
    ("AC-OPL2", ac_opl2),
    ("AC-OPL3", ac_opl3),
    ("AC-OPL4", ac_opl4),
    ("AC-OPL5", ac_opl5),
    ("AC-OPL6", ac_opl6),
)


def main():
    if len(CRITERIA) != EXPECTED_CRITERIA:
        print("FAIL suite carries %d criteria, expected %d"
              % (len(CRITERIA), EXPECTED_CRITERIA), flush=True)
        return 1
    for name, function in CRITERIA:
        try:
            function()
        except Exception as exc:  # a crashing criterion is a red, not a pass
            print("FAIL %s raised %s: %s"
                  % (name, type(exc).__name__, exc), flush=True)
            globals()["FAILS"] += 1
    print("SUITE %s %d/%d"
          % ("PASS" if FAILS == 0 else "FAIL", PASSES, PASSES + FAILS),
          flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())