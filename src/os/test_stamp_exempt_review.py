"""stamp_exempt_review suite (R2294; criteria AC-SER1..AC-SER6 were pinned in
state/queue/tech.md as the R2280 seed row BEFORE this code existed).

What this proves: queue_done_stamp_exempt joins one pinned declaration with the
live stamp gate and answers only "does this entry still match a debt row".
Nothing reports the accepted-stamp pair drifting apart in either direction - a
declared row annotated after the fact (its text digest moves) and a debt row
created after the declaration (no entry at all) both leave the acceptance
green while it rots. This suite pins the read-only reviewer that lists drift
BOTH ways and refuses to guess which side is stale.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import hashlib
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
import stamp_exempt_review as SER  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "stamp_exempt_review.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-stamp-exempt-review"
WIRED_EXPECT = '"test_stamp_exempt_review.py"), 6),'

PASSES = 0
FAILS = 0

# One closed row with no stamp at all: the gate reads it UNSTAMPED.
ROW_TECH = "- [x] P2 tech item R2200 with no stamp at all"
ROW_MAIN = "- [x] P2 main item R2210 also carrying no stamp"
ROW_EXPLORE = "- [x] P3 explore item R2222 with no stamp either"


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


def make_world(rows, entries, raw=None, omit=None):
    """Build a temp root with the three queue files and a declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-ser-")
    inner = os.path.join(world, "state", "queue")
    os.makedirs(inner)
    for name, body in rows.items():
        if omit == name:
            continue
        with io.open(os.path.join(inner, "%s.md" % name), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(body + "\n")
    if raw is not None or entries is not None:
        body = raw if raw is not None else json.dumps({"exemptions": entries},
                                                      indent=2)
        with io.open(os.path.join(inner, "stamp_exempt.json"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return world


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


HEADER = "### main\n\n"


def world_rows(tech=ROW_TECH, main=ROW_MAIN, explore=ROW_EXPLORE):
    return {"main": HEADER + main, "tech": "### tech\n\n" + tech,
            "explore": "### explore\n\n" + explore}


# AC-SER1: drift is listed in BOTH directions, each with its own locator - a
# declared entry that matches no live row (MISSING, with the declaration entry
# index) and a live debt row with no entry (UNDECLARED, with file and line).
world1 = make_world(world_rows(),
                    [entry("tech", identity(ROW_TECH)),
                     entry("main", "ghost#deadbeef", declared="R2270")])
rep1 = SER.audit(world1, 2294)
undeclared1 = rep1["undeclared"]
missing1 = rep1["missing"]
check(rep1["verdict"] == "DRIFT"
      and rep1["matched"] == 1
      and rep1["missing_count"] == 1 and rep1["undeclared_count"] == 2
      and missing1[0]["identity"] == "ghost#deadbeef"
      and missing1[0]["entry"] == 2
      and missing1[0]["declared"] == "R2270"
      and sorted(row["queue"] for row in undeclared1) == ["explore", "main"]
      and all(row["line"] >= 1 and row["file"].endswith(".md")
              for row in undeclared1)
      and identity(ROW_MAIN) in [row["identity"] for row in undeclared1],
      "AC-SER1 drift listed both ways with identities and lines")

# AC-SER2: the split reconciles with the reader own numbers before a verdict
# is issued, and a disagreement refuses instead of printing a wrong drift list.
reader2 = SEX.audit(world1, 2294)
reconciled = (rep1["matched"] == reader2["exempt_today"]
              + reader2["exempt_expired"]
              and rep1["missing_count"] == reader2["unmatched_count"])
original_audit = SEX.audit


def lying_audit(root, round_no):
    real = original_audit(root, round_no)
    real["unmatched_count"] = real["unmatched_count"] + 1
    return real


SEX.audit = lying_audit
try:
    count_code = None
    try:
        SER.audit(world1, 2294)
    except SER.StampExemptReviewError as exc:
        count_code = exc.code
finally:
    SEX.audit = original_audit
cli_count = run_cli(["--root", world1, "--check", "--round", "R2294"])
check(reconciled and count_code == "E_SER_COUNT" and cli_count[0] == 2
      and "verdict=DRIFT" in cli_count[1],
      "AC-SER2 counts reconcile with the reader own exempt and unmatched "
      "numbers, disagreement refuses")

# AC-SER3: a healthy declaration reads NO-DRIFT at exit 0 - every live debt
# row carries an entry and every entry matches a live row.
healthy = make_world(world_rows(),
                     [entry("tech", identity(ROW_TECH)),
                      entry("main", identity(ROW_MAIN)),
                      entry("explore", identity(ROW_EXPLORE))])
rep3 = SER.audit(healthy, 2294)
ok_code, ok_out, _err = run_cli(["--root", healthy, "--check",
                                 "--round", "R2294"])
check(rep3["verdict"] == "NO-DRIFT" and rep3["missing_count"] == 0
      and rep3["undeclared_count"] == 0 and rep3["matched"] == 3
      and rep3["violation_count"] == 3 and rep3["entries"] == 3
      and ok_code == 0 and "verdict=NO-DRIFT" in ok_out,
      "AC-SER3 healthy declaration reads NO-DRIFT at exit 0")

# AC-SER4: a stale declaration reads DRIFT at exit 2 and touches NEITHER file.
stale = make_world(world_rows(),
                   [entry("tech", identity(ROW_TECH)),
                    entry("main", "ghost#deadbeef")])
decl_path = os.path.join(stale, "state", "queue", "stamp_exempt.json")
queue_path = os.path.join(stale, "state", "queue", "main.md")
before_decl, before_queue = digest(decl_path), digest(queue_path)
stale_code, stale_out, _ = run_cli(["--root", stale, "--check",
                                    "--round", "R2294"])
after_decl, after_queue = digest(decl_path), digest(queue_path)
listing = sorted(os.listdir(os.path.join(stale, "state", "queue")))
check(stale_code == 2 and "verdict=DRIFT" in stale_out
      and "MISSING entry=2 main:ghost#deadbeef" in stale_out
      and "UNDECLARED" in stale_out and "explore.md" in stale_out
      and before_decl == after_decl and before_queue == after_queue
      and listing == ["explore.md", "main.md", "stamp_exempt.json",
                      "tech.md"],
      "AC-SER4 stale declaration reads DRIFT at exit 2 without touching "
      "either file")

# AC-SER5: malformed or missing input fails closed with its own code - an
# absent declaration, broken JSON, a missing queue file, and an ambiguous
# pair each refuse instead of reading as drift or as clean.
absent = make_world(world_rows(), None)
absent_code, absent_out, _ = run_cli(["--root", absent, "--check",
                                      "--round", "R2294"])
broken = make_world(world_rows(), None, raw="{not json")
broken_code, broken_out, _ = run_cli(["--root", broken, "--check",
                                      "--round", "R2294"])
no_queue = make_world(world_rows(), [entry("tech", identity(ROW_TECH))],
                      omit="explore")
queue_code, queue_out, _ = run_cli(["--root", no_queue, "--check",
                                    "--round", "R2294"])
dup = make_world(world_rows(tech=ROW_TECH + "\n" + ROW_TECH),
                 [entry("tech", identity(ROW_TECH))])
dup_code, dup_out, _ = run_cli(["--root", dup, "--check", "--round", "R2294"])
check(absent_code == 3 and "E_SER_UNPINNED" in absent_out
      and broken_code == 3 and "E_SER_BAD_DECL" in broken_out
      and queue_code == 3 and "E_SER_BAD_GATE" in queue_out
      and dup_code == 3 and "E_SER_AMBIGUOUS" in dup_out,
      "AC-SER5 missing declaration, broken JSON, missing queue and an "
      "ambiguous pair each fail closed with its own code")

# AC-SER6: purity, its own reconcile label, and a live read-only reading of the
# real 380-entry declaration (both real files unchanged by the reading).
with io.open(MODULE, "r", encoding="utf-8") as handle:
    module_source = handle.read()
non_ascii = [ch for ch in module_source if ord(ch) > 127]
imports = [line.strip() for line in module_source.splitlines()
           if line.strip().startswith("import ")
           or line.strip().startswith("from ")]
clock_hits = [line for line in imports
              if "time" in line or "datetime" in line]
net_hits = [line for line in imports
            if any(word in line for word in ("socket", "urllib", "requests",
                                             "http"))]
with io.open(RUNNER, "r", encoding="utf-8") as handle:
    runner = handle.read()
live_decl = os.path.join(REPO, "state", "queue", "stamp_exempt.json")
live_tech = os.path.join(REPO, "state", "queue", "tech.md")
live_before = (digest(live_decl), digest(live_tech))
live = SER.audit(REPO, 2294)
live_after = (digest(live_decl), digest(live_tech))
check(not non_ascii and not clock_hits and not net_hits
      and WIRED_EXPECT in runner and LABEL in runner
      and live_before == live_after
      and live["declaration"] == "PINNED"
      and live["entries"] == 380 and live["violation_count"] == 380
      and live["matched"] == 380
      and live["missing_count"] == 0 and live["undeclared_count"] == 0
      and live["verdict"] == "NO-DRIFT",
      "AC-SER6 pure ASCII, stdlib only, wired, live reading of 380 entries")

print("LIVE %s" % SER.one_line(live), flush=True)
print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                          PASSES, EXPECTED_CRITERIA), flush=True)
sys.exit(0 if FAILS == 0 else 1)