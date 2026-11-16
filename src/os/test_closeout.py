"""closeout suite (R2835; criteria AC-COUT1..AC-COUT7 were pinned in the R2835
row of src/os/backlog.md BEFORE this file - the pin row was committed ahead of
the code).

What this proves: closing a round used to be TWO commands in TWO processes, and
nothing made one depend on the other. A face is derived FROM state, so a face
written while the state write failed describes a round the state never got -
which is the R2831 defect with a different trigger. closeout.py makes the order
a law: the state step is a hard, re-read precondition for the face step, both
writes stay in the vehicles that already own them, and a refusal always names
which step failed.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import closeout as CO  # noqa: E402

EXPECTED_CRITERIA = 7
MODULE = os.path.join(BASE, "closeout.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-closeout"
ROUND = 9100

PASSES = 0
FAILS = 0

NET_IMPORTS = ("urllib", "http.client", "requests", "socket", "httpx")


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def read(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def fingerprint(path):
    if not os.path.isfile(path):
        return ("absent", 0, 0)
    with io.open(path, "rb") as handle:
        raw = handle.read()
    return (hashlib.sha256(raw).hexdigest(), len(raw),
            os.path.getmtime(path))


def tick_label():
    import check_export_consistency as cec
    return cec._load_patterns().get("tick_row_label")


def world(tick=ROUND, drop_tick_row=False):
    """A private world carrying just the inputs the two vehicles read."""
    folder = tempfile.mkdtemp(prefix="cout-")
    label = tick_label()
    write(os.path.join(folder, "src", "os", "backlog.md"),
          read(os.path.join(ROOT, "src", "os", "backlog.md")))
    write(os.path.join(folder, "src", "os", "state.json"),
          json.dumps({"tick": tick,
                      "benchmarks_refreshed": "2026-11-16",
                      "log": ["2026-11-15 R%d SOMETHING MEASURED IN A PAST "
                              "WINDOW" % (tick - 1)]},
                     ensure_ascii=False, indent=2) + "\n")
    for name in ("main.md", "tech.md", "explore.md"):
        src = os.path.join(ROOT, "state", "queue", name)
        if os.path.isfile(src):
            write(os.path.join(folder, "state", "queue", name), read(src))
    prev = os.path.join(ROOT, "preview")
    for name in os.listdir(prev):
        if name.endswith(".html") or name.endswith(".json"):
            write(os.path.join(folder, "preview", name),
                  read(os.path.join(prev, name)))
    write(os.path.join(folder, "preview", "zz-cout-face.html"),
          "<!DOCTYPE html>\n")
    write(os.path.join(folder, "preview", "zz-cout-face.json"), "{}\n")
    rows = [["1", "a past row"], ["2", "another past row"]]
    if not drop_tick_row:
        rows.append([str(tick), label])
    face = {"results": rows, "outs": ["x"], "do": "x",
            "ceo_face": {"current": "x", "latest_artifact": "x",
                         "next_milestone": "x",
                         "next_milestone_due": "x"},
            "self_drive": {}}
    write(os.path.join(folder, "docs", "status-export.json"),
          json.dumps(face, ensure_ascii=False, indent=2) + "\n")
    return folder


def cleanup(folder):
    shutil.rmtree(folder, ignore_errors=True)


def run_cli(argv):
    buf = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(buf):
        with contextlib.redirect_stderr(err):
            try:
                code = CO.main(argv)
            except SystemExit as exc:
                code = exc.code
    return code, buf.getvalue(), err.getvalue()


def ticks(folder):
    data = json.loads(read(os.path.join(folder, "src", "os", "state.json")))
    return int(data.get("tick", 0)), data.get("log") or []


def face(folder):
    return json.loads(read(os.path.join(folder, "docs", "status-export.json")))


def ac_cout1():
    """AC-COUT1: one vehicle, and it only delegates the two writes."""
    source = io.open(MODULE, encoding="utf-8").read()
    delegates = ("SA.run(" in source and "ER.write(" in source)
    owns_no_write = not any(token in source for token in
                            ("json.dump(", "tempfile.mkstemp(", "os.replace(",
                             "fsync("))
    roots = set()
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            roots.add(stripped[len("import "):].split(",")[0].split(" ")[0]
                      .split(".")[0])
        elif stripped.startswith("from ") and " import " in stripped:
            roots.add(stripped[len("from "):].split(" ")[0].split(".")[0])
    no_net = not (roots & set(NET_IMPORTS))
    with io.open(MODULE, "rb") as handle:
        ascii_only = all(byte < 128 for byte in handle.read())
    code, out, _ = run_cli(["--help"])
    ok = (delegates and owns_no_write and no_net and ascii_only and code == 0
          and "closeout.py" in out)
    if not ok:
        print("  measured: delegates=%r owns_no_write=%r roots=%r ascii=%r "
              "help=%r" % (delegates, owns_no_write, sorted(roots), ascii_only,
                           code), flush=True)
    check(ok, "AC-COUT1 the closeout delegates both writes to state_append and "
          "export_round, owns no serialisation of its own, is ASCII with no "
          "net, and answers --help")


def ac_cout2():
    """AC-COUT2: the state step is a hard precondition for the face step."""
    folder = world()
    face_path = os.path.join(folder, "docs", "status-export.json")
    try:
        before = fingerprint(face_path)
        code, out, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                "--line",
                                "R%d PRODUCT: the prefix was forgotten" % ROUND,
                                "--tick"])
        after = fingerprint(face_path)
        state_tick, _ = ticks(folder)
        ok = (code == 2 and "E_CO_NO_STATE" in out and "step=state" in out
              and before == after and state_tick == ROUND)
        if not ok:
            print("  measured: code=%r out=%r face_same=%r state_tick=%r"
                  % (code, out.strip()[:200], before == after, state_tick),
                  flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-COUT2 an undated round line reads E_CO_NO_STATE with rc=2, "
          "the face keeps its exact bytes and mtime, and the state did not "
          "move - so a face describing a round the state never got is "
          "unreachable")


def ac_cout3():
    """AC-COUT3: a face failure is named AND says the state already landed."""
    folder = world(drop_tick_row=True)
    try:
        code, out, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                "--line",
                                "2026-11-16 R%d PRODUCT: state landed first"
                                % ROUND,
                                "--tick"])
        state_tick, log = ticks(folder)
        ok = (code == 2 and "E_CO_NO_FACE" in out and "step=face" in out
              and "state=WRITTEN" in out and state_tick == ROUND + 1
              and len(log) == 2)
        if not ok:
            print("  measured: code=%r out=%r state_tick=%r log=%d"
                  % (code, out.strip()[:200], state_tick, len(log)),
                  flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-COUT3 a face that cannot be derived reads E_CO_NO_FACE, "
          "names the face step, states face=state was already WRITTEN, and the "
          "state on disk really carries the new tick and line")


def ac_cout4():
    """AC-COUT4: one command, both writes, one tick."""
    folder = world()
    try:
        tick_before, log_before = ticks(folder)
        code, out, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                "--line",
                                "2026-11-16 R%d PRODUCT: both writes landed"
                                % ROUND,
                                "--tokens", "local=~1k api=0 api_reason=test",
                                "--tick"])
        tick_after, log_after = ticks(folder)
        data = face(folder)
        cur = str((data.get("ceo_face") or {}).get("current") or "")
        label = tick_label()
        stamped = [row for row in data.get("results") or []
                   if isinstance(row, list) and len(row) >= 2
                   and row[1] == label]
        ok = (code == 0 and "CLOSEOUT OK" in out
              and tick_after == tick_before + 1
              and len(log_after) == len(log_before) + 2
              and cur.startswith("R%d" % tick_after)
              and len(stamped) == 1
              and str(stamped[0][0]) == str(tick_after)
              and "face=WRITTEN" in out)
        if not ok:
            print("  measured: code=%r out=%r tick=%r log=%r cur=%r stamped=%r"
                  % (code, out.strip()[:200], tick_after, len(log_after),
                     cur[:40], stamped), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-COUT4 one closeout call moves the state by one tick and two "
          "lines and publishes a face whose current line and tick row both "
          "name the new tick")


def ac_cout5():
    """AC-COUT5: --check is read-only on both files."""
    folder = world()
    state_path = os.path.join(folder, "src", "os", "state.json")
    face_path = os.path.join(folder, "docs", "status-export.json")
    try:
        before = (fingerprint(state_path), fingerprint(face_path))
        code, out, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                "--line",
                                "2026-11-16 R%d PRODUCT: dry run only" % ROUND,
                                "--tick", "--check"])
        after = (fingerprint(state_path), fingerprint(face_path))
        undated_code, undated_out, _ = run_cli(
            ["--root", folder, "--round", str(ROUND),
             "--line", "R%d PRODUCT: undated dry run" % ROUND, "--check"])
        undated_after = (fingerprint(state_path), fingerprint(face_path))
        ok = (code == 0 and "CLOSEOUT CHECK" in out
              and "face=NOT-MEASURED" in out
              and before == after == undated_after
              and undated_out.strip()[:40].startswith("CLOSEOUT FAIL"))
        if not ok:
            print("  measured: code=%r out=%r same=%r undated=%r"
                  % (code, out.strip()[:160], before == after,
                     undated_out.strip()[:80]), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-COUT5 --check writes zero bytes to the state AND the face, "
          "prints the state dry-run verdict, and does not invent a face "
          "verdict it cannot derive")


def ac_cout6():
    """AC-COUT6: a replay must not masquerade as a refreshed face."""
    folder = world()
    face_path = os.path.join(folder, "docs", "status-export.json")
    line = "2026-11-16 R%d PRODUCT: written exactly once" % ROUND
    try:
        first_code, _, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                    "--line", line, "--tick"])
        face_once = fingerprint(face_path)
        tick_once, log_once = ticks(folder)
        code, out, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                "--line", line, "--tick"])
        face_twice = fingerprint(face_path)
        tick_twice, log_twice = ticks(folder)
        ok = (first_code == 0 and code == 0
              and "E_CO_DUPLICATE" in out and "face=NOT-WRITTEN" in out
              and face_once == face_twice
              and tick_once == tick_twice
              and len(log_once) == len(log_twice))
        if not ok:
            print("  measured: codes=%r/%r out=%r face_same=%r tick=%r/%r"
                  % (first_code, code, out.strip()[:160],
                     face_once == face_twice, tick_once, tick_twice),
                  flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-COUT6 replaying the same closeout reads E_CO_DUPLICATE with "
          "rc=0, leaves the face byte-identical and the state untouched, so a "
          "no-op cannot pass for a refresh")


def ac_cout7():
    """AC-COUT7: registered with this exact criteria count."""
    runner_text = io.open(RUNNER, encoding="utf-8").read()
    pattern = re.compile(
        r"\(" + json.dumps(LABEL) + r",\s*\n\s*os\.path\.join\([^)]*\),\s*"
        r"(\d+)\)")
    match = pattern.search(runner_text)
    registered = match is not None
    declared = int(match.group(1)) if registered else -1
    ok = registered and declared == EXPECTED_CRITERIA
    if not ok:
        print("  measured: registered=%r declared=%r expected=%r"
              % (registered, declared, EXPECTED_CRITERIA), flush=True)
    check(ok, "AC-COUT7 the registry declares this suite at %d criteria"
          % EXPECTED_CRITERIA)


def main():
    print("closeout suite (expected criteria %d)" % EXPECTED_CRITERIA,
          flush=True)
    ac_cout1()
    ac_cout2()
    ac_cout3()
    ac_cout4()
    ac_cout5()
    ac_cout6()
    ac_cout7()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
