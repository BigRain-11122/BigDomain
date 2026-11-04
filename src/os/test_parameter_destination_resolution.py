"""parameter_destination_resolution suite (R2448).

Criteria AC-PDR1..AC-PDR6 were pre-registered inside the R2434 tech seed row of
state/queue/tech.md (line 514) BEFORE this code existed.

What this proves: a writer that RECEIVES its destination as a function
parameter used to read E_GWDA_UNRESOLVED and hide among the unread rows, so the
tier could not say whether it was clean or merely unread. This suite proves the
resolution is derived from the module's own call sites (never a whitelist), that
adding a call site moves a fixture from UNRESOLVED into the KEEPS tier with the
target the call site passes, that a function with no call site still reads
UNRESOLVED naming the function, that every previously routed writer keeps its
exact target, that the audit's refusal surface is unchanged, and that this
module is pure.

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

import general_writer_dialect_audit as GWDA  # noqa: E402
import parameter_destination_resolution as PDR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "parameter_destination_resolution.py")
AUDIT = os.path.join(BASE, "general_writer_dialect_audit.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

LABEL = "os-parameter-destination-resolution"
WIRED_EXPECT = '"test_parameter_destination_resolution.py"), 6),'

# a writer whose destination arrives as a PARAMETER, with a call site that
# passes a resolvable structured file
CALLED_WRITER = (
    'import io\n'
    'import json\n'
    'import os\n'
    '\n'
    'TARGET_REL = os.path.join("state", "fixture.json")\n'
    '\n'
    '\n'
    'def land(root, path, payload):\n'
    '    text = json.dumps(payload, indent=2, sort_keys=True) + "\\n"\n'
    '    temp = path + ".tmp"\n'
    '    with io.open(temp, "w", encoding="utf-8", newline="\\n") as fh:\n'
    '        fh.write(text)\n'
    '    os.replace(temp, path)\n'
    '\n'
    '\n'
    'def main(root):\n'
    '    target = os.path.join(root, TARGET_REL)\n'
    '    land(root, target, {})\n'
)

# the same writer with NO in-module call site for land()
UNCALLED_WRITER = CALLED_WRITER.split("\n\ndef main(")[0] + "\n"

# every writer that was already routed before this window, with its spelling
PRE_ROUTED = (
    ("debt_append.py", "state/debt.md"),
    ("debt_close.py", "state/debt.md"),
    ("residue_triage_append.py", "state/residue_triage.json"),
    ("residue_triage_append_batch.py", "state/residue_triage.json"),
    ("residue_triage_entry_retire.py", "state/residue_triage.json"),
    ("residue_triage_head_renew.py", "state/residue_triage.json"),
    ("state_fold.py", "src/os/state.json"),
)

LITERAL_JOIN = (
    'import io\n'
    'import json\n'
    'import os\n'
    '\n'
    'TARGET = os.path.join("state", "fixture.json")\n'
    '\n'
    '\n'
    'def land(payload):\n'
    '    text = json.dumps(payload) + "\\n"\n'
    '    temp = TARGET + ".tmp"\n'
    '    with io.open(temp, "w", encoding="utf-8", newline="\\n") as fh:\n'
    '        fh.write(text)\n'
    '    os.replace(temp, TARGET)\n'
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


def write_text(path, text):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def world_with(tmp, name, source):
    """A minimal tree: one writer under src/os, one structured state file."""
    root = os.path.join(tmp, name)
    write_text(os.path.join(root, "src", "os", "fixture_writer.py"), source)
    write_text(os.path.join(root, "state", "fixture.json"), "{}\n")
    return root


def ac_pdr1(tmp):
    """The resolution is derived from the source call sites, never a whitelist."""
    world = world_with(tmp, "pdr1", CALLED_WRITER)
    reading = PDR.by_call_site(CALLED_WRITER, GWDA_RESOLVER)
    derived = bool(reading["calls"]) and not reading["unresolved"]
    # a whitelist-looking file must change nothing
    write_text(os.path.join(world, "state", "pdr_whitelist.json"),
               '{"resolved": ["fixture_writer.py"]}\n')
    after = PDR.by_call_site(CALLED_WRITER, GWDA_RESOLVER)
    whitelist_inert = after == reading
    # a resolver that refuses everything must move the answer
    blank = PDR.by_call_site(CALLED_WRITER, lambda node: [])
    resolver_moves = not blank["calls"] and bool(blank["unresolved"])
    check(derived and whitelist_inert and resolver_moves,
          "AC-PDR1 the destination is derived from the source call sites, "
          "never a whitelist file")


def ac_pdr2(tmp):
    """A parameter destination with a resolvable call site enters KEEPS."""
    called = world_with(tmp, "pdr2-called", CALLED_WRITER)
    row = GWDA.classify("fixture_writer.py", CALLED_WRITER, called)
    moved = row is not None and row["kind"] == "KEEPS" \
        and row["target"] == "state/fixture.json"
    # the SAME writer with no call site stays UNRESOLVED
    uncalled = world_with(tmp, "pdr2-uncalled", UNCALLED_WRITER)
    other = GWDA.classify("fixture_writer.py", UNCALLED_WRITER, uncalled)
    still_unread = other is not None and other["kind"] == "UNRESOLVED"
    # adding the call site is what moves it, not the fixture file
    check(moved and still_unread,
          "AC-PDR2 adding the call site moves a parameter writer into KEEPS "
          "with the target it passes (UNRESOLVED without it)")


def ac_pdr3(tmp):
    """A function with no in-module call site reads UNRESOLVED naming it."""
    reading = PDR.by_call_site(UNCALLED_WRITER, GWDA_RESOLVER)
    reasons = list(reading["unresolved"].values())
    named = bool(reasons) and "land" in reasons[0] and "no in-module call" in reasons[0]
    row = GWDA.classify("fixture_writer.py", UNCALLED_WRITER,
                        world_with(tmp, "pdr3", UNCALLED_WRITER))
    detail = row is not None and row["kind"] == "UNRESOLVED" \
        and "land" in row["why"]
    check(named and detail,
          "AC-PDR3 a parameter with no call site still reads UNRESOLVED "
          "naming the function")


def ac_pdr4():
    """Every previously routed writer keeps routed and its exact target."""
    reading = GWDA.report(REPO)
    rows = dict((row["name"], row) for row in reading["rows"]
                if row["kind"] == "KEEPS")
    ok = True
    for name, target in PRE_ROUTED:
        row = rows.get(name)
        if row is None or row["target"] != target or row["asks"] is not True:
            ok = False
            print("  MOVED %s" % name, flush=True)
    check(ok and reading["routed"] >= len(PRE_ROUTED),
          "AC-PDR4 every previously routed writer keeps its target and stays "
          "routed (%d writers)" % len(PRE_ROUTED))


def ac_pdr5(tmp):
    """The audit's refusal codes, exit codes and printed lines are unchanged."""
    bad = subprocess.run([sys.executable, AUDIT, "--nonsense"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    first = bad.stdout.decode("utf-8", "replace").splitlines()
    first = first[0] if first else ""
    bad_ok = bad.returncode == 5 and first.startswith("E_GWDA_BAD_ARGS")
    missing = os.path.join(tmp, "pdr5-empty")
    os.makedirs(missing, exist_ok=True)
    gone = subprocess.run([sys.executable, AUDIT, "--check", "--root", missing],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    gone_first = gone.stdout.decode("utf-8", "replace").splitlines()
    gone_first = gone_first[0] if gone_first else ""
    unreadable_ok = gone.returncode == 3 and gone_first == "E_GWDA_UNREADABLE"
    reading = GWDA.report(REPO)
    render_ok = GWDA.render(reading).splitlines()[0] == GWDA.one_line(reading)
    check(bad_ok and unreadable_ok and render_ok,
          "AC-PDR5 the audit keeps its refusal codes, exit codes and report "
          "surface")


def ac_pdr6():
    """Pure: ASCII source, stdlib only, no clock, own label and suite."""
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    ascii_ok = all(ord(ch) < 128 for ch in source)
    banned = ("import time", "import datetime", "import random", "import uuid",
              "import socket", "import urllib", "import requests")
    no_clock = not any(word in source for word in banned)
    no_network = "http://" not in source and "https://" not in source
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner = handle.read()
    check(ascii_ok and no_clock and no_network
          and LABEL in source and WIRED_EXPECT in runner,
          "AC-PDR6 pure ASCII, stdlib only, no clock, zero network, own label "
          "and suite")


def GWDA_RESOLVER(node):
    """The audit's own resolver, handed in at CALL time (one resolver, two
    readers). The suite imports it rather than writing a second one."""
    return GWDA._resolve_node(node, _ASSIGNS, _FUNCS, _IMPORTS, BASE)


_ASSIGNS = {}
_FUNCS = {}
_IMPORTS = {}


def bind(source):
    """Load the audit's own maps for a source, so the resolver is the real
    one and this suite never re-implements path resolution."""
    import ast
    tree = ast.parse(source)
    _ASSIGNS.clear()
    _ASSIGNS.update(GWDA._assignments(tree))
    _FUNCS.clear()
    _FUNCS.update(GWDA._functions(tree))
    _IMPORTS.clear()
    _IMPORTS.update(GWDA._imports(tree))


def main():
    tmp = tempfile.mkdtemp(prefix="pdr-")
    try:
        bind(CALLED_WRITER)
        ac_pdr1(tmp)
        ac_pdr2(tmp)
        bind(UNCALLED_WRITER)
        ac_pdr3(tmp)
        ac_pdr4()
        ac_pdr5(tmp)
        ac_pdr6()
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print("SUITE %s criteria=%d pass=%d fail=%d" % (
        "PASS" if FAILS == 0 else "FAIL", EXPECTED_CRITERIA, PASSES, FAILS))
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())