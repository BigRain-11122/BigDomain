"""stamp_exempt_prune suite (R2329; criteria AC-SEPR1..AC-SEPR6 were pinned in
state/queue/tech.md as the R2307 seed row BEFORE this code existed).

What this proves: stamp_exempt_append lets the accepted-stamp declaration grow
and stamp_exempt_review names the two ways it rots, but nothing could retire an
entry - so a MISSING entry and an EXPIRED entry stayed in the file forever and
the list could only grow. This suite pins the treatment: a retire set derived
from the two shipped readings (never a second join), a plan that names every
entry it would drop, span surgery that leaves every surviving entry
byte-identical and in order, validation through the shipped reader, and one
atomic replace proved by read-back with no temp residue.

Stdlib only, ASCII source, zero network, no clock read. Exit 0 = all green.
"""

import io
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import queue_done_stamp as QDS  # noqa: E402
import queue_done_stamp_exempt as SEX  # noqa: E402
import stamp_exempt_append as SEPA  # noqa: E402
import stamp_exempt_prune as SPR  # noqa: E402
import stamp_exempt_review as SER  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "stamp_exempt_prune.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-stamp-exempt-prune"
WIRED_EXPECT = '"test_stamp_exempt_prune.py"), 6),'

PASSES = 0
FAILS = 0

ROW_TECH = "- [x] P2 tech item R2200 with no stamp at all"
ROW_MAIN = "- [x] P2 main item R2210 also carrying no stamp"
ROW_EXPLORE = "- [x] P3 explore item R2222 with no stamp either"

HEADER = {"main": "### main\n\n", "tech": "### tech\n\n",
          "explore": "### explore\n\n"}


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def identity(line):
    """The identity the gate derives: from the ASCII excerpt of the row."""
    return SEX.identity_of(QDS.excerpt(line))


def entry(queue, ident, declared="R2280", reason="accepted as it stands",
          until=None):
    row = {"queue": queue, "identity": ident, "declared": declared,
           "reason": reason}
    if until is not None:
        row["until"] = until
    return row


def one_line_declaration(entries, note="accepted rows"):
    """The shipped declaration layout: one entry per line inside the array."""
    body = ['{', '  "note": %s,' % json.dumps(note, ensure_ascii=True),
            '  "exemptions": [']
    lines = ["    " + json.dumps(item, ensure_ascii=True, sort_keys=False)
             for item in entries]
    body.append(",\n".join(lines))
    body.append("  ]")
    body.append("}")
    return "\n".join(body) + "\n"


def pretty_declaration(entries):
    """The same entries, pretty-printed, to prove span surgery is layout-blind."""
    return json.dumps({"note": "accepted rows", "exemptions": entries},
                      indent=2) + "\n"


def make_world(entries, raw=None, rows=None):
    rows = rows or {"main": ROW_MAIN, "tech": ROW_TECH,
                    "explore": ROW_EXPLORE}
    world = tempfile.mkdtemp(prefix="bigdomain-sepr-")
    inner = os.path.join(world, "state", "queue")
    os.makedirs(inner)
    for name, body in rows.items():
        with io.open(os.path.join(inner, "%s.md" % name), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(HEADER[name] + body + "\n")
    body = raw if raw is not None else one_line_declaration(entries)
    with io.open(os.path.join(inner, "stamp_exempt.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return world


def decl_path(world):
    return os.path.join(world, "state", "queue", "stamp_exempt.json")


def read_bytes(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def three_entries():
    """One matching row, one ghost entry (MISSING), one expired entry."""
    return [entry("tech", identity(ROW_TECH)),
            entry("main", "ghost#deadbeef", declared="R2270"),
            entry("explore", identity(ROW_EXPLORE), declared="R2200",
                  until="R2210")]


# AC-SEPR1: the retire set is derived from the two shipped readings - the
# reviewer own MISSING list (with its entry indices) and the reader own EXPIRED
# row status - and never from a second digest join in this module.
world1 = make_world(three_entries())
rep1 = SPR.plan(world1, 2300)
reasons1 = [(item["entry"], item["queue"], item["identity"], item["why"])
            for item in rep1["retire"]]
review1 = SER.audit(world1, 2300)
reader1 = SEX.audit(world1, 2300)
check(rep1["entries"] == 3 and rep1["missing"] == review1["missing_count"] == 1
      and rep1["expired"] == reader1["exempt_expired"] == 1
      and rep1["retire_count"] == 2 and rep1["keep_count"] == 1
      and reasons1 == [(2, "main", "ghost#deadbeef", "MISSING"),
                       (3, "explore", identity(ROW_EXPLORE), "EXPIRED")]
      and rep1["verdict"] == "PLAN",
      "AC-SEPR1 retire set derived from the reviewer MISSING and the reader "
      "EXPIRED readings")

# AC-SEPR2: a plan names every entry it would drop with its index, queue and
# identity, and a dry run is the default - the file is untouched and the CLI
# without --execute leaves identical bytes behind.
before2 = read_bytes(decl_path(world1))
dry_code, dry_out, _err = run_cli(["--root", world1, "--round", "R2300"])
after2 = read_bytes(decl_path(world1))
check(dry_code == 0 and "RETIRE entry=2 main:ghost#deadbeef" in dry_out
      and "why=MISSING" in dry_out
      and "RETIRE entry=3 explore:%s" % identity(ROW_EXPLORE) in dry_out
      and "why=EXPIRED" in dry_out
      and "verdict=PLAN" in dry_out and "wrote=no" in dry_out
      and [item["entry"] for item in rep1["retire"]] == [2, 3]
      and before2 == after2
      and not os.path.exists(decl_path(world1) + SPR.TEMP_SUFFIX),
      "AC-SEPR2 plan names every entry it would drop and dry run is the "
      "default")

# AC-SEPR3: the splice removes exactly those entries while every surviving
# entry keeps its exact bytes and its order - proved on the shipped one-line
# layout AND on a pretty-printed declaration, so the surgery is layout-blind.
text3 = one_line_declaration(three_entries())
spans3 = SPR.entry_spans(text3)
keep3 = SPR.surviving_texts(text3, spans3, {1, 2})
post3 = SPR.splice(text3, spans3, {1, 2})
post3_entries = [text3[a:b] for a, b in SPR.entry_spans(post3)]
pretty3 = pretty_declaration(three_entries())
spans3b = SPR.entry_spans(pretty3)
post3b = SPR.splice(pretty3, spans3b, {0, 2})
keep3b = SPR.surviving_texts(pretty3, spans3b, {0, 2})
post3b_entries = [post3b[a:b] for a, b in SPR.entry_spans(post3b)]
check(len(spans3) == 3 and keep3 == post3_entries and len(keep3) == 1
      and json.loads(keep3[0]) == three_entries()[0]
      and len(SPR.entry_spans(pretty3)) == 3
      and keep3b == post3b_entries and len(keep3b) == 1
      and json.loads(keep3b[0]) == three_entries()[1]
      and post3.count("\n") == text3.count("\n") - 2,
      "AC-SEPR3 splice keeps every surviving entry byte-identical and in "
      "order on both layouts")

# AC-SEPR4: the post text is validated by the shipped reader and must carry
# exactly the expected count - a reader that disagrees about the count refuses
# the plan instead of writing a list nobody verified.
original_entries = SEPA.declaration_entries


def short_entries(text):
    return original_entries(text)[:-1]


SEPA.declaration_entries = short_entries
try:
    count_code = None
    try:
        SPR.plan(world1, 2300)
    except SPR.StampExemptPruneError as exc:
        count_code = exc.code
finally:
    SEPA.declaration_entries = original_entries
cli4_code, _out4, _err4 = run_cli(["--root", world1, "--round", "R2300",
                                   "--execute"])
ok4 = (count_code == "E_SPR_COUNT"
       and cli4_code == 0
       and len(SEX.read_declaration(world1)["entries"]) == 1)
check(ok4, "AC-SEPR4 post text validated through read_declaration with the "
      "exact expected count")

# AC-SEPR5: an executed prune is ONE atomic replace proved by read-back with no
# temp residue, and a refused plan writes nothing at all.
world5 = make_world(three_entries())
exec_code, exec_out, _err5 = run_cli(["--root", world5, "--round", "R2300",
                                      "--execute"])
after5 = read_bytes(decl_path(world5))
leftovers = [name for name in os.listdir(os.path.join(world5, "state",
                                                      "queue"))
             if name.endswith(SPR.TEMP_SUFFIX)]
healthy5 = make_world([entry("tech", identity(ROW_TECH)),
                       entry("main", identity(ROW_MAIN)),
                       entry("explore", identity(ROW_EXPLORE))])
healthy_before = read_bytes(decl_path(healthy5))
healthy_rep = SPR.plan(healthy5, 2300, execute=True)
healthy_after = read_bytes(decl_path(healthy5))
check(exec_code == 0 and "wrote=yes" in exec_out
      and "read_back=yes" in exec_out
      and len(SEX.read_declaration(world5)["entries"]) == 1
      and len(SEX.read_declaration(world5)["entries"]) == 1
      and leftovers == []
      and healthy_rep["verdict"] == "NOTHING-TO-RETIRE"
      and healthy_rep["wrote"] is False
      and healthy_before == healthy_after
      and after5 != healthy_before,
      "AC-SEPR5 executed prune is one atomic replace with read-back and no "
      "temp residue, a refused plan writes nothing")

# AC-SEPR6: purity plus its own reconcile label - no clock, no network import,
# ASCII source, a stable JSON key order from the module own report, and one
# runner entry carrying the six criteria this suite just counted.
source6 = io.open(MODULE, "r", encoding="utf-8").read()
labels = repr(SPR.one_line(rep1))
json6 = json.loads(SPR.to_json(rep1))
wired = io.open(RUNNER, "r", encoding="utf-8").read()
check(all(token not in source6 for token in
          ("import time", "import datetime", "import socket", "import urllib",
           "import requests", "import http"))
      and "STAMP EXEMPT PRUNE round=R2300" in labels
      and list(json6.keys()) == list(SPR.PLAN_KEYS)
      and json6["retire_count"] == 2
      and ('("os-stamp-exempt-prune",' in wired)
      and (WIRED_EXPECT in wired)
      and PASSES + FAILS + 1 == EXPECTED_CRITERIA,
      "AC-SEPR6 purity, own reconcile label, stable JSON keys and one runner "
      "entry with six criteria")

print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL", PASSES,
                          PASSES + FAILS), flush=True)
sys.exit(0 if FAILS == 0 else 1)