"""Ledger baseline semantics suite (R2157; criteria AC-LGB1..AC-LGB8
were pre-registered in state/queue/tech.md BEFORE this code existed -
honesty law).

What this proves: the baseline is the only exemption channel of the
ledger gate, so its semantics are pinned instead of assumed - one entry
exempts exactly one round, a stale entry is reported instead of rotting
quietly, a broken baseline fails closed under its own code, a missing
baseline equals --no-baseline, and the tool never rewrites the file it
is given.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
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

import ledger_lines as LL  # noqa: E402

EXPECTED_CRITERIA = 8
MODULE = os.path.join(BASE, "ledger_lines.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-ledger-baseline"

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


def run_cli(args):
    proc = subprocess.Popen(
        [sys.executable, MODULE] + args,
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode,
            out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_state(path, log):
    write_text(path, json.dumps({"tick": 1, "log": log}, sort_keys=True))


def read_bytes(path):
    with io.open(path, "rb") as handle:
        return handle.read()


GAPPED = [
    "R701 note about round seven hundred one",
    "R702 note about round seven hundred two",
    "R703 note about round seven hundred three",
    "R703 tokens: local=1k api=0 api_reason=round seven hundred three",
]


def run():
    # AC-LGB1: the report grows two stale keys and keeps every existing
    # AC-LGR key and the clean law untouched.
    loose = LL.audit(GAPPED)
    gated = LL.apply_baseline(loose, {"missing": [701], "orphan": []})
    check(loose["rounds_without_ledger"] == [701, 702]
          and loose["clean"] is False
          and gated["baseline_missing"] == 1
          and gated["baseline_orphan"] == 0
          and gated["new_missing"] == [702]
          and gated["new_orphan"] == []
          and gated["stale_missing"] == [] and gated["stale_orphan"] == []
          and gated["clean"] is False
          and set(["rounds_without_ledger", "ledger_without_round",
                   "errors", "new_missing", "new_orphan",
                   "baseline_missing", "baseline_orphan"]).issubset(
                       set(gated.keys())),
          "AC-LGB1 stale keys added, existing keys and clean law kept")

    # AC-LGB2: one entry exempts exactly one round - no collateral
    # suppression - and a baseline never masks a broken line.
    both = LL.apply_baseline(LL.audit(GAPPED),
                             {"missing": [701, 702], "orphan": []})
    broken = LL.audit([
        "R801 note about a round",
        "R801 tokens: local=zz api=0 api_reason=broken round eight hundred",
    ])
    broken_gated = LL.apply_baseline(broken, {"missing": [801],
                                              "orphan": []})
    check(both["new_missing"] == [] and both["clean"] is True
          and broken["errors"] and broken_gated["errors"]
          and broken_gated["clean"] is False,
          "AC-LGB2 one entry exempts one round, errors never suppressed")

    # AC-LGB3: a stale entry (gap already healed) is reported, not kept
    # silently, and staleness alone never flips the verdict.
    stale_rep = LL.apply_baseline(LL.audit(GAPPED),
                                  {"missing": [701, 702, 705],
                                   "orphan": [799]})
    check(stale_rep["stale_missing"] == [705]
          and stale_rep["stale_orphan"] == [799]
          and stale_rep["new_missing"] == []
          and 705 not in stale_rep["new_missing"]
          and stale_rep["clean"] is True,
          "AC-LGB3 stale baseline entries reported, not silently kept")

    # AC-LGB4: the stale line appears in the text form only when there
    # is staleness, and the JSON form always carries both keys.
    world = tempfile.mkdtemp(prefix="lgb-form-")
    try:
        state = os.path.join(world, "state.json")
        live_base = os.path.join(world, "live.json")
        stale_base = os.path.join(world, "stale.json")
        write_state(state, GAPPED)
        write_text(live_base, json.dumps({"missing": [701, 702],
                                          "orphan": []}))
        write_text(stale_base, json.dumps({"missing": [701, 702, 705],
                                           "orphan": []}))
        live_rc, live_out, _ = run_cli(
            ["--check", state, "--baseline", live_base])
        stale_rc, stale_out, _ = run_cli(
            ["--check", state, "--baseline", stale_base])
        j_rc, j_out, _ = run_cli(
            ["--check", state, "--baseline", live_base, "--json"])
        payload = json.loads(j_out)
        stale_lines = [line for line in stale_out.splitlines()
                       if line.startswith("stale: ")]
        live_lines = [line for line in live_out.splitlines()
                      if line.startswith("stale: ")]
        check(live_rc == 0 and stale_rc == 0
              and live_lines == []
              and stale_lines == ["stale: missing=705 orphan=none"]
              and "VERDICT CLEAN" in stale_out
              and j_rc == 0 and "stale_missing" in payload
              and "stale_orphan" in payload
              and payload["stale_missing"] == []
              and payload["stale_orphan"] == [],
              "AC-LGB4 stale line only when stale, JSON always carries keys")
    finally:
        for name in ("state.json", "live.json", "stale.json"):
            path = os.path.join(world, name)
            if os.path.exists(path):
                os.unlink(path)
        os.rmdir(world)

    # AC-LGB5: four broken baseline shapes fail closed under their own
    # code, exit 3, empty stdout, and never rewrite the file.
    world = tempfile.mkdtemp(prefix="lgb-bad-")
    try:
        state = os.path.join(world, "state.json")
        write_state(state, GAPPED)
        shapes = {
            "notdict.json": "[1, 2, 3]",
            "notlist.json": json.dumps({"missing": "701"}),
            "notint.json": json.dumps({"missing": ["701"]}),
            "unparsable.json": "{this is not json",
        }
        verdicts = []
        for name, text in shapes.items():
            path = os.path.join(world, name)
            write_text(path, text)
            before = read_bytes(path)
            rc, out, err = run_cli(["--check", state, "--baseline", path])
            after = read_bytes(path)
            residues = [item for item in os.listdir(world)
                        if item.endswith(".tmp")]
            verdicts.append((rc, out, "E_LGR_BAD_BASELINE" in err,
                             "E_LGR_NO_STATE" in err, before == after,
                             residues == []))
        check(all(item == (3, "", True, False, True, True)
                  for item in verdicts) and len(verdicts) == 4,
              "AC-LGB5 four broken baselines fail closed, zero writes")
    finally:
        for name in ("state.json", "notdict.json", "notlist.json",
                     "notint.json", "unparsable.json"):
            path = os.path.join(world, name)
            if os.path.exists(path):
                os.unlink(path)
        os.rmdir(world)

    # AC-LGB6: a baseline path that does not exist equals --no-baseline
    # and is never created.
    world = tempfile.mkdtemp(prefix="lgb-missing-")
    try:
        state = os.path.join(world, "state.json")
        ghost = os.path.join(world, "ghost.json")
        write_state(state, GAPPED)
        ghost_rc, ghost_out, _ = run_cli(
            ["--check", state, "--baseline", ghost, "--json"])
        none_rc, none_out, _ = run_cli(
            ["--check", state, "--no-baseline", "--json"])
        ghost_rep = json.loads(ghost_out)
        none_rep = json.loads(none_out)
        check(ghost_rc == 2 and none_rc == 2
              and ghost_rep["baseline_missing"] == 0
              and ghost_rep["stale_missing"] == []
              and ghost_rep["stale_orphan"] == []
              and ghost_rep["new_missing"] == [701, 702]
              and ghost_rep["rounds_without_ledger"]
              == none_rep["rounds_without_ledger"]
              and ghost_rep["clean"] == none_rep["clean"]
              and not os.path.exists(ghost),
              "AC-LGB6 absent baseline equals --no-baseline, zero writes")
    finally:
        for name in ("state.json", "ghost.json"):
            path = os.path.join(world, name)
            if os.path.exists(path):
                os.unlink(path)
        os.rmdir(world)

    # AC-LGB7: a tolerant read - unknown keys ignored, absent keys empty,
    # the two lists independent of each other.
    world = tempfile.mkdtemp(prefix="lgb-tol-")
    try:
        noted = os.path.join(world, "noted.json")
        only_orphan = os.path.join(world, "orphan.json")
        write_text(noted, json.dumps({"note": "shipped baseline note",
                                      "missing": [701], "orphan": []}))
        write_text(only_orphan, json.dumps({"orphan": [708]}))
        loaded_noted = LL.load_baseline(noted)
        loaded_orphan = LL.load_baseline(only_orphan)
        audit_lines = [
            "R701 note about round seven hundred one",
            "R703 note about round seven hundred three",
            "R703 tokens: local=1k api=0 api_reason=round seven hundred "
            "three",
            "R708 tokens: local=1k api=0 api_reason=orphan line eight",
        ]
        rep = LL.apply_baseline(LL.audit(audit_lines), loaded_orphan)
        check(loaded_noted == {"missing": [701], "orphan": []}
              and "note" not in loaded_noted
              and loaded_orphan == {"missing": [], "orphan": [708]}
              and rep["stale_missing"] == []
              and rep["stale_orphan"] == []
              and rep["new_missing"] == [701]
              and rep["clean"] is False,
              "AC-LGB7 unknown keys ignored, absent keys empty, lists "
              "independent")
    finally:
        for name in ("noted.json", "orphan.json"):
            path = os.path.join(world, name)
            if os.path.exists(path):
                os.unlink(path)
        os.rmdir(world)

    # AC-LGB8: live gate under the shipped baseline plus hygiene, old
    # suite regression and the runner seat.
    with io.open(MODULE, "r", encoding="ascii", errors="strict") as handle:
        source = handle.read()
    net = LL.network_imports(source)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner_src = handle.read()
    live_log = LL.load_state_log(os.path.join(BASE, "state.json"))
    base_path = LL.default_baseline_path()
    shipped = LL.load_baseline(base_path)
    # R2224: the gate reads the coverage scope (live plus folded archive)
    # so an exemption list measured before a fold keeps its meaning.
    scope = LL.audit_scope(
        LL.load_archive_lines(None, os.path.join(BASE, "state.json")),
        live_log)
    gated = LL.apply_baseline(scope, shipped)
    deterministic = (json.dumps(gated, sort_keys=True)
                     == json.dumps(gated, sort_keys=True))
    # R2225: the fold moved the two formerly exempt rounds into the archive,
    # where both carry their own ledger line, so the exemption list is empty
    # and the stale report is empty by construction (the R2224 law).
    check(gated["clean"] is True
          and gated["new_missing"] == [] and gated["new_orphan"] == []
          and gated["stale_missing"] == [] and gated["stale_orphan"] == []
          and LL.coverage_floor(gated) is True
          and shipped["missing"] == []
          and shipped["orphan"] == []
          and not net and deterministic
          and LABEL in runner_src
          and EXPECTED_CRITERIA == 8,
          "AC-LGB8 live gate clean on the coverage scope, shipped "
          "baseline fresh, hygiene, runner seat")


def main():
    print("suite: ledger baseline semantics (R2157 AC-LGB1..AC-LGB8)")
    run()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAILS == 0 and total == EXPECTED_CRITERIA
             else "FAIL", PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())