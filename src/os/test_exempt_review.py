"""exempt_review suite (R2292; criteria AC-EXR1..AC-EXR6 were pinned in
state/queue/tech.md as the R2276 seed row BEFORE this code existed).

What this proves: queue_row_exempt records an acceptance once and nothing ever
looks at it again, so a waiver granted while the world looked one way quietly
becomes permanent. This suite pins the read-only reviewer that ages every
declared entry against a round and names the ones that have gone unreviewed
for too long.

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

import exempt_review as ER  # noqa: E402
import queue_row_exempt as QRE  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "exempt_review.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-exempt-review"
WIRED_EXPECT = '"test_exempt_review.py"), 6),'

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


def entry(queue, identity, declared, reason="accepted as it stands",
          until=None):
    row = {"queue": queue, "identity": identity, "declared": declared,
           "reason": reason}
    if until is not None:
        row["until"] = until
    return row


def make_world(entries, raw=None):
    """Build a temp root carrying state/queue/prefix_exempt.json."""
    world = tempfile.mkdtemp(prefix="bigdomain-exr-")
    inner = os.path.join(world, "state", "queue")
    os.makedirs(inner)
    if raw is None:
        body = json.dumps({"exemptions": entries}, indent=2)
    else:
        body = raw
    with io.open(os.path.join(inner, "prefix_exempt.json"), "w",
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


# AC-EXR1: the declaration is read through queue_row_exempt.read_declaration
# and a patched reader flows straight through (no second parser here).
world = make_world([entry("tech", "seed-a", "R2290")])
base = ER.audit(world, "R2292")
original = QRE.read_declaration


def patched(root):
    return {"status": "PINNED", "path": "state/queue/prefix_exempt.json",
            "entries": [{"queue": "main", "identity": "seed-patched",
                         "declared": "R2200", "reason": "patched",
                         "until": None}], "note": None}


QRE.read_declaration = patched
try:
    through = ER.audit(world, "R2292", window=50)
finally:
    QRE.read_declaration = original
check(base["entries"][0]["identity"] == "seed-a"
      and through["entries"][0]["identity"] == "seed-patched"
      and through["stale_count"] == 1
      and len(through["entries"]) == 1,
      "AC-EXR1 declaration law is imported and a patched reader flows through")

# AC-EXR2: age = current - declared; at or beyond the window is STALE naming
# BOTH rounds; just inside the window is FRESH. The declared until round also
# ends an acceptance even when its age is short.
world2 = make_world([
    entry("tech", "boundary-in", "R2292"),
    entry("tech", "boundary-edge", "R2272"),
    entry("main", "fresh-short", "R2291"),
    entry("explore", "until-ended", "R2290", until="R2292"),
])
rep2 = ER.audit(world2, "R2292", window=20)
row_by_id = {row["identity"]: row for row in rep2["entries"]}
stale_ids = sorted(row["identity"] for row in rep2["stale"])
check(row_by_id["boundary-in"]["age"] == 0
      and row_by_id["boundary-in"]["status"] == "FRESH"
      and row_by_id["boundary-edge"]["age"] == 20
      and row_by_id["boundary-edge"]["status"] == "STALE"
      and row_by_id["boundary-edge"]["declared"] == "R2272"
      and row_by_id["fresh-short"]["age"] == 1
      and row_by_id["fresh-short"]["status"] == "FRESH"
      and row_by_id["until-ended"]["status"] == "STALE"
      and stale_ids == ["boundary-edge", "until-ended"]
      and rep2["stale_count"] == 2
      and rep2["verdict"] == "REVIEW-STALE"
      and "R2272" in ER.detail_line(row_by_id["boundary-edge"]),
      "AC-EXR2 age law, at-or-beyond window STALE naming both rounds, "
      "until round ends an acceptance")

# AC-EXR3: a declared round LATER than the round being checked is refused
# (a future acceptance cannot be aged to a negative number).
world3 = make_world([entry("tech", "future-one", "R2300")])
future_code = None
try:
    ER.audit(world3, "R2292")
except ER.ExemptReviewError as exc:
    future_code = exc.code
cli_code, cli_out, _err = run_cli(["--root", world3, "--round", "R2292"])
check(future_code == "E_EXR_FUTURE"
      and cli_code == 3
      and "REFUSE E_EXR_FUTURE" in cli_out
      and "R2300" in cli_out,
      "AC-EXR3 future declared round refused as E_EXR_FUTURE")

# AC-EXR4: the reader writes nothing and reads no clock.
world4 = make_world([entry("tech", "no-writes", "R2200")])
decl_path = os.path.join(world4, "state", "queue", "prefix_exempt.json")
before = digest(decl_path)
listing_before = sorted(os.listdir(os.path.join(world4, "state", "queue")))
rep4 = ER.audit(world4, "R2292", window=20)
after = digest(decl_path)
listing_after = sorted(os.listdir(os.path.join(world4, "state", "queue")))
with io.open(MODULE, "r", encoding="utf-8") as handle:
    module_source = handle.read()
imports = [line.strip() for line in module_source.splitlines()
           if line.strip().startswith("import ")
           or line.strip().startswith("from ")]
clock_hits = [line for line in imports
              if "time" in line or "datetime" in line]
check(before == after and listing_before == listing_after
      and rep4["stale_count"] == 1 and not clock_hits,
      "AC-EXR4 zero writes and zero clock (declaration digests identically)")

# AC-EXR5: CLI exits 0 clean / 2 stale / 3 unreadable / 5 bad flags, and the
# JSON is byte-stable over the pinned keys in the pinned order.
clean_world = make_world([entry("tech", "recent-one", "R2291")])
stale_world = make_world([entry("tech", "old-one", "R2200")])
ok_code, ok_out, _ = run_cli(["--root", clean_world, "--round", "R2292"])
stale_code, stale_out, _ = run_cli(["--root", stale_world, "--round", "R2292",
                                    "--window", "20"])
missing_code, missing_out, _ = run_cli(["--root",
                                        os.path.join(clean_world, "nope"),
                                        "--round", "R2292"])
bad_json_world = make_world(None, raw="{not json")
broken_code, broken_out, _ = run_cli(["--root", bad_json_world,
                                      "--round", "R2292"])
flags_code, flags_out, _ = run_cli(["--round", "2292"])
first = run_cli(["--root", stale_world, "--round", "R2292", "--window", "20",
                 "--json"])
second = run_cli(["--root", stale_world, "--round", "R2292", "--window", "20",
                  "--json"])
parsed = json.loads(first[1])
check(ok_code == 0 and "REVIEW-CLEAN" in ok_out
      and stale_code == 2 and "REVIEW-STALE" in stale_out
      and "STALE tech/old-one declared=R2200" in stale_out
      and missing_code == 0 and "declaration=UNPINNED" in missing_out
      and broken_code == 3 and "E_EXR_BAD_DECL" in broken_out
      and flags_code == 5 and "BAD FLAGS" in flags_out
      and first[1] == second[1]
      and tuple(parsed.keys()) == ER.REPORT_KEYS
      and parsed["stale_count"] == 1,
      "AC-EXR5 CLI 0/2/3/5 and byte-stable JSON over pinned keys")

# AC-EXR6: purity, wiring, and a live read-only reading of the real
# declaration (every entry declared R2276 must age honestly today).
non_ascii = [ch for ch in module_source if ord(ch) > 127]
net_hits = [line for line in imports
            if any(word in line for word in ("socket", "urllib", "requests",
                                             "http"))]
with io.open(RUNNER, "r", encoding="utf-8") as handle:
    runner = handle.read()
live_path = os.path.join(REPO, "state", "queue", "prefix_exempt.json")
live_before = digest(live_path)
live = ER.audit(REPO, "R2292")
live_after = digest(live_path)
check(not non_ascii and not net_hits
      and WIRED_EXPECT in runner and LABEL in runner
      and live_before == live_after
      and live["declaration"] == "PINNED"
      and len(live["entries"]) == 9
      and live["stale_count"] == len(live["stale"])
      and live["verdict"] in ER.VERDICTS,
      "AC-EXR6 pure ASCII, stdlib only, wired, live reading of nine entries")

print("LIVE %s" % ER.one_line(live), flush=True)
print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                          PASSES, EXPECTED_CRITERIA), flush=True)
sys.exit(0 if FAILS == 0 else 1)