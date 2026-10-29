"""State-fold suite (R2245; criteria AC-SF1..AC-SF6 were pre-registered in
state/queue/tech.md as the R2240-b seed BEFORE this code existed - honesty
law).

What this proves: the fold is a decision the code makes once, not a surgical
habit repeated by hand. The waterline is read from the disk size (AC-SF1), a
window moves verbatim and its tokens survive in the summary (AC-SF2), the
archive grows by append and never by rewrite (AC-SF3), --check writes nothing
(AC-SF4), the same plan run twice equals itself and every bad plan is refused
before any write (AC-SF5), and the module is pure ASCII, stdlib, no network
and wired into the battery (AC-SF6).

Stdlib only, ASCII source, zero network. Exit 0 = all green.
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

import state_fold as SF  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "state_fold.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-state-fold"

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


def state_text(log_lines, indent=16, newline="\r\n"):
    items = []
    for index, line in enumerate(log_lines):
        literal = " " * indent + json.dumps(line, ensure_ascii=False)
        if index < len(log_lines) - 1:
            literal += ","
        items.append(literal)
    lines = (["{", '  "tick": 1,', '  "log": ['] + items + ["  ]", "}"])
    return newline.join(lines)


def make_world(log_lines, indent=16, newline="\r\n"):
    world = tempfile.mkdtemp(prefix="bigdomain-sf-")
    os.makedirs(os.path.join(world, "src", "os"))
    os.makedirs(os.path.join(world, "logs"))
    with io.open(os.path.join(world, "src", "os", "state.json"), "w",
                 encoding="utf-8", newline="") as handle:
        handle.write(state_text(log_lines, indent, newline))
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def digest_tree(world):
    parts = []
    for folder in ("src/os", "logs"):
        root = os.path.join(world, *folder.split("/"))
        if not os.path.isdir(root):
            continue
        for leaf in sorted(os.listdir(root)):
            path = os.path.join(root, leaf)
            if os.path.isfile(path):
                with io.open(path, "rb") as handle:
                    blob = handle.read()
                parts.append((folder + "/" + leaf, len(blob),
                              hashlib.sha256(blob).hexdigest()[:16]))
    return tuple(parts)


def run_cli(args, cwd=REPO):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=cwd)
    return (proc.returncode, proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def read_bytes(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def run():
    # AC-SF1: the waterline law, read from the real disk size.
    at_gate = SF.measure(SF.GATE)
    over = SF.measure(SF.GATE + 1)
    under = SF.measure(SF.GATE - 1)
    world = make_world(["line one", "line two"])
    try:
        report = SF.check(world)
        keys_ok = sorted(report.keys()) == sorted(SF.CHECK_KEYS)
        live_real = report["bytes"] == os.path.getsize(
            os.path.join(world, "src", "os", "state.json"))
        ok = (at_gate["margin"] == 0 and at_gate["fold_needed"] is False
              and at_gate["verdict"] == "FOLD-CLEAR"
              and over["margin"] == -1 and over["fold_needed"] is True
              and over["verdict"] == "FOLD-DUE"
              and under["fold_needed"] is False
              and set(SF.VERDICTS) == {"FOLD-CLEAR", "FOLD-DUE"}
              and keys_ok and live_real and report["log_lines"] == 2
              and report["verdict"] == "FOLD-CLEAR")
        check(ok, "AC-SF1 waterline verdict from the disk size, margin exact, "
                  "closed verdict set and pinned report keys")
    finally:
        drop_world(world)

    # AC-SF2: verbatim window plus token coverage, suffix intact.
    window_lines = ["R2201 work with AC-SF1 and D-20261001-01 tokens",
                    "R2202 more work with AC-SF2 token"]
    keep = ["R2199 older round", "R2203 newer round AC-SF3"]
    log_lines = [keep[0]] + window_lines + [keep[1]]
    world = make_world(log_lines)
    try:
        path = os.path.join(world, "src", "os", "state.json")
        raw = read_bytes(path)
        state = json.loads(raw.decode("utf-8"))
        summary = ("carry-forward R2201..R2202 (AC-SF1, AC-SF2, "
                   "D-20261001-01 folded)")
        plan, folded = SF.plan_fold(raw, state, 2, 3, summary)
        expected_bytes = sum(len(line.encode("utf-8"))
                             for line in window_lines)
        folded_state = json.loads(folded)
        ok = (sorted(plan.keys()) == sorted(SF.PLAN_KEYS)
              and plan["window_lines"] == 2
              and plan["window_content_bytes"] == expected_bytes
              and plan["tokens_total"] == 3
              and plan["tokens_missing"] == []
              and plan["token_ok"] is True
              and plan["predicted_bytes"] == len(folded.encode("utf-8"))
              and plan["folded_log_len"] == 3
              and plan["token_ok"] and plan["gate_ok"]
              and folded_state["log"][0] == keep[0]
              and folded_state["log"][1] == summary
              and folded_state["log"][2] == keep[1]
              and len(folded_state["log"]) == 3)
        check(ok, "AC-SF2 window moves verbatim with byte sum, tokens covered, "
                  "prefix and suffix intact and the plan keys pinned")
    finally:
        drop_world(world)

    # AC-SF3: archive grows by append, verbatim, byte verified.
    world = make_world(["x"])
    try:
        archive = os.path.join(world, "logs", "state-log-archive-2026-10.md")
        header = "# --- R2245 fold append (2026-10-29, 2 lines verbatim: log " \
                 "window, fold 594 window, pre-op sha16 abcdef0123456789)"
        with io.open(archive, "wb") as handle:
            handle.write(b"# existing archive\nno trailing newline")
        before = read_bytes(archive)
        lines = ["R2201 window line one", "R2202 window line two"]
        first = SF.append_archive(archive, header, lines)
        after_first = read_bytes(archive)
        appendix = (header + "\n" + "\n".join(lines) + "\n").encode("utf-8")
        prefix_ok = after_first == before + b"\n" + appendix
        second = SF.append_archive(archive, header, lines)
        after_second = read_bytes(archive)
        twice_ok = (after_second == after_first + appendix
                    and second["prefix_intact"] is True)
        keys_ok = sorted(first.keys()) == sorted(SF.ARCHIVE_KEYS)
        created_path = os.path.join(world, "logs", "new-archive.md")
        created = SF.append_archive(created_path, header, lines,
                                   allow_create=True)
        created_blob = read_bytes(created_path)
        create_ok = (created["created"] is True
                     and created_blob.endswith(appendix)
                     and created_blob.startswith(b"# logs/new-archive.md"))
        refused = False
        try:
            SF.append_archive(os.path.join(world, "logs", "absent.md"),
                              header, lines)
        except SF.StateFoldError as exc:
            refused = exc.code == "E_SF_ARCHIVE_MISSING"
        check(prefix_ok and twice_ok and keys_ok and create_ok and refused,
              "AC-SF3 verbatim appendix, old bytes a strict prefix, second "
              "append stacks, create only on demand, missing fails closed")
    finally:
        drop_world(world)

    # AC-SF4: --check writes nothing and reports the closed exit codes.
    world = make_world(["small line"])
    try:
        before = digest_tree(world)
        code, out, err = run_cli(["--check", "--root", world])
        after = digest_tree(world)
        json_code, json_out, _ = run_cli(["--check", "--root", world,
                                         "--json"])
        parsed = json.loads(json_out) if json_code == 0 else {}
        big_log = ["z" * 79000]
        big_world = make_world(big_log)
        try:
            due_before = digest_tree(big_world)
            due_code, due_out, _ = run_cli(["--check", "--root", big_world])
            due_after = digest_tree(big_world)
        finally:
            drop_world(big_world)
        bad_code, bad_out, _ = run_cli(["--check", "--nope"])
        missing_code, _, _ = run_cli(["--check", "--root",
                                      os.path.join(world, "nowhere")])
        ok = (code == 0 and before == after
              and "verdict=FOLD-CLEAR" in out
              and json_code == 0
              and sorted(parsed.keys()) == sorted(SF.CHECK_KEYS)
              and parsed["fold_needed"] is False
              and due_code == 2 and "FOLD-DUE" in due_out
              and due_before == due_after
              and bad_code == 2 and "usage: state_fold.py" in bad_out
              and missing_code == 3)
        check(ok, "AC-SF4 --check is byte-for-byte read-only with exit 0 clear "
                  "/ 2 due or bad flags / 3 unreadable")
    finally:
        drop_world(world)

    # AC-SF5: same plan twice, bad plans refused before any write, and one
    # execute run lands exactly on its own prediction.
    window_lines = ["R2201 with AC-SF1", "R2202 with AC-SF5"]
    log_lines = ["R2199 older", "R2200 older two"] + window_lines \
        + ["R2203 newer"]
    world = make_world(log_lines)
    try:
        path = os.path.join(world, "src", "os", "state.json")
        raw, state = SF.read_state(path)
        summary = "carry-forward R2201..R2202 (AC-SF1, AC-SF5 folded)"
        plan_a, folded_a = SF.plan_fold(raw, state, 3, 4, summary)
        plan_b, folded_b = SF.plan_fold(raw, state, 3, 4, summary)
        deterministic = plan_a == plan_b and folded_a == folded_b
        bounds_refused = False
        try:
            SF.plan_fold(raw, state, 4, 99, summary)
        except SF.StateFoldError as exc:
            bounds_refused = exc.code == "E_SF_WINDOW"
        pre = read_bytes(path)
        lost = SF.fold(world, "RTEST", 594, 3, 4, "summary without tokens",
                       execute=True)
        lost_ok = (lost["would_fail"] == ["token-missing"]
                   and lost["mode"] == "execute"
                   and read_bytes(path) == pre
                   and not os.path.exists(
                       os.path.join(world, "logs", "state-preop-RTEST.bak")))
        airtight = SF.fold(world, "RTEST", 594, 3, 4, summary, execute=True,
                           gate=100)
        airtight_ok = (airtight["would_fail"] == ["gate-exceed"]
                       and read_bytes(path) == pre)
        result = SF.fold(world, "RTEST", 594, 3, 4, summary, execute=True)
        post = read_bytes(path)
        backup = read_bytes(os.path.join(world, "logs",
                                         "state-preop-RTEST.bak"))
        archive = read_bytes(SF.default_archive(world))
        post_state = json.loads(post.decode("utf-8"))
        landed = (result["mode"] == "execute"
                  and result["would_fail"] == []
                  and result["predicted_eq_actual"] is True
                  and result["post_bytes"] == result["predicted_bytes"]
                  and post_state["log"] == [log_lines[0], log_lines[1],
                                            summary, log_lines[4]]
                  and backup == pre
                  and ("\n".join(window_lines)).encode("utf-8") in archive
                  and result["archive"]["created"] is True)
        recheck = SF.check(world)
        check(deterministic and bounds_refused and lost_ok and airtight_ok
              and landed and recheck["verdict"] == "FOLD-CLEAR"
              and recheck["log_lines"] == 4,
              "AC-SF5 plan idempotent, bounds/token/gate refusals write "
              "nothing, one execute lands on its prediction and re-checks "
              "clear")
    finally:
        drop_world(world)

    # AC-SF6: purity - ASCII source, stdlib, zero network, single owner, wired.
    with io.open(MODULE, "rb") as handle:
        blob = handle.read()
    ascii_ok = all(byte < 128 for byte in blob)
    source = blob.decode("ascii", "replace")
    forbidden = ("import socket", "import urllib", "import http",
                 "import requests", "import logs_toolkit",
                 "from logs_toolkit")
    clean = all(needle not in source for needle in forbidden)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner = handle.read()
    needle = '"%s"' % LABEL
    wired = False
    if needle in runner:
        window = runner[runner.find(needle):][:400]
        wired = "test_state_fold.py" in window and ", 6)" in window
    check(ascii_ok and clean and wired and "AC-SF" in source,
          "AC-SF6 source ASCII, stdlib only, no network, predicate single "
          "owned and wired as os-state-fold(6)")


if __name__ == "__main__":
    run()
    print("SUITE %s %d/%d" % (
        "PASS" if FAILS == 0 else "FAIL", PASSES + FAILS, EXPECTED_CRITERIA),
        flush=True)
    sys.exit(0 if FAILS == 0 else 2)