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

import ast
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
import heartbeat as HB  # noqa: E402

EXPECTED_CRITERIA = 29
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


def set_face_current(folder, text):
    """Rewrite only ceo_face.current, leaving every other byte of the face."""
    path = os.path.join(folder, "docs", "status-export.json")
    data = json.loads(read(path))
    data.setdefault("ceo_face", {})["current"] = text
    write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def face_round(folder):
    cur = str((face(folder).get("ceo_face") or {}).get("current") or "")
    match = re.match(r"^(?:\d{4}-\d{2}-\d{2}\s+)?R(\d+)\b", cur)
    return int(match.group(1)) if match else None


def ac_coutb1():
    """AC-COUTB1: the detector fires on M < N only, measured, never assumed."""
    folder = world()
    try:
        tick = ticks(folder)[0]
        cases = []

        set_face_current(folder, "R%d PRODUCT: level" % tick)
        cases.append(("level", CO.face_behind(folder, "HELD")))

        set_face_current(folder, "R%d PRODUCT: ahead" % (tick + 1))
        cases.append(("ahead", CO.face_behind(folder, "HELD")))

        set_face_current(folder, "x")
        cases.append(("unparseable", CO.face_behind(folder, "HELD")))

        set_face_current(folder, "2026-11-16 R%d PRODUCT: anchored behind"
                         % (tick - 2))
        cases.append(("behind", CO.face_behind(folder, "HELD")))

        source = io.open(MODULE, encoding="utf-8").read()
        # Prose may cite rounds; the DETECTOR may not carry one as data.
        start = source.index("def measure_face")
        end = source.index("def _state_args")
        no_round_literal = not re.search(r"R\d{4}\b", source[start:end])
        quiet = [name for name, msg in cases[:3]]
        fires = [name for name, msg in cases[3:]]
        ok = (not any(cases[i][1] for i in range(3))
              and len(fires) == 1 and "E_CO_FACE_BEHIND" in cases[3][1]
              and "state_tick=%d" % tick in cases[3][1]
              and "face=R%d" % (tick - 2) in cases[3][1]
              and "behind_by=2" in cases[3][1]
              and no_round_literal)
        if not ok:
            print("  measured: quiet=%r fires=%r behind=%r literal=%r"
                  % (quiet, fires, cases[3][1], no_round_literal), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-COUTB1 E_CO_FACE_BEHIND fires only on a measured face round "
          "below the live state tick; level, ahead and unparseable faces stay "
          "silent, and the module carries no round literal")


def ac_coutb2():
    """AC-COUTB2: --check names the half-close and writes nothing at all."""
    folder = world()
    state_path = os.path.join(folder, "src", "os", "state.json")
    face_path = os.path.join(folder, "docs", "status-export.json")
    try:
        tick = ticks(folder)[0]
        set_face_current(folder, "R%d PRODUCT: still the previous round"
                         % (tick - 1))
        before = (fingerprint(state_path), fingerprint(face_path))
        code, out, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                "--line",
                                "2026-11-16 R%d PRODUCT: half close" % ROUND,
                                "--tick", "--check"])
        after = (fingerprint(state_path), fingerprint(face_path))
        ok = (code == 2 and "E_CO_FACE_BEHIND" in out and "step=face" in out
              and "state=HELD" in out and "face_lagging=1" in out
              and "python src/os/export_round.py" in out
              and before == after)
        if not ok:
            print("  measured: code=%r out=%r same=%r"
                  % (code, out.strip()[:220], before == after), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-COUTB2 --check on a lagging face exits 2 with "
          "E_CO_FACE_BEHIND, names the repair, and leaves both files' sha256 "
          "AND mtime untouched")


def ac_coutb3():
    """AC-COUTB3: the duplicate replay names the half-close instead of rc=0."""
    folder = world()
    line = "2026-11-16 R%d PRODUCT: written exactly once" % ROUND
    try:
        first_code, _, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                    "--line", line, "--tick"])
        level_code, level_out, _ = run_cli(["--root", folder, "--round",
                                            str(ROUND), "--line", line,
                                            "--tick"])
        tick = ticks(folder)[0]
        set_face_current(folder, "R%d PRODUCT: the face step died" % (tick - 1))
        behind_code, behind_out, _ = run_cli(["--root", folder, "--round",
                                              str(ROUND), "--line", line,
                                              "--tick"])
        ok = (first_code == 0
              and level_code == 0
              and "E_CO_DUPLICATE" in level_out
              and "face=NOT-WRITTEN" in level_out
              and "E_CO_FACE_BEHIND" not in level_out
              and behind_code == 2
              and "E_CO_FACE_BEHIND" in behind_out
              and "face_lagging=1" in behind_out)
        if not ok:
            print("  measured: codes=%r/%r/%r level=%r behind=%r"
                  % (first_code, level_code, behind_code,
                     level_out.strip()[:140], behind_out.strip()[:140]),
                  flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-COUTB3 a duplicate replay over a level face keeps the R2835 "
          "no-op at rc=0, and over a lagging face reads E_CO_FACE_BEHIND at "
          "rc=2 - so the half-close can no longer pass for a no-op")


def ac_coutb4():
    """AC-COUTB4: the repair the refusal names actually clears it."""
    folder = world()
    try:
        tick = ticks(folder)[0]
        set_face_current(folder, "R%d PRODUCT: stale" % (tick - 1))
        stale_code, stale_out, _ = run_cli(["--root", folder, "--round",
                                           str(ROUND), "--line",
                                           "2026-11-16 R%d PRODUCT: reopen"
                                           % ROUND, "--check"])
        import export_round as ER
        ok_write, _, proof = ER.write(
            folder, "2026-11-16T23:59:00+08:00")
        code, out, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                "--line",
                                "2026-11-16 R%d PRODUCT: reopened" % ROUND,
                                "--check"])
        ok = (stale_code == 2 and "E_CO_FACE_BEHIND" in stale_out
              and ok_write and proof.get("gate") == "CURRENT"
              and code == 0 and "CLOSEOUT CHECK" in out
              and "E_CO_FACE_BEHIND" not in out
              and face_round(folder) == ticks(folder)[0])
        if not ok:
            print("  measured: stale=%r/%r write=%r/%r after=%r/%r face=%r"
                  % (stale_code, stale_out.strip()[:80], ok_write,
                     proof.get("gate"), code, out.strip()[:120],
                     face_round(folder)), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-COUTB4 re-deriving the face clears E_CO_FACE_BEHIND and the "
          "same --check turns green - the refusal names a repair that works")


def ac_coutb5():
    """AC-COUTB5: registry and matrix both carry the grown criteria count."""
    runner_text = io.open(RUNNER, encoding="utf-8").read()
    pattern = re.compile(
        r"\(" + json.dumps(LABEL) + r",\s*\n\s*os\.path\.join\([^)]*\),\s*"
        r"(\d+)\)")
    match = pattern.search(runner_text)
    registered = int(match.group(1)) if match else -1
    matrix_path = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
    row = re.search(r"^\|\s*\d+\s*\|\s*%s\s*\|\s*[^|]*\|\s*(\d+)\s*\|"
                    % re.escape(LABEL), read(matrix_path), re.MULTILINE)
    declared = int(row.group(1)) if row else -1
    ok = registered == EXPECTED_CRITERIA and declared == EXPECTED_CRITERIA
    if not ok:
        print("  measured: registry=%r matrix=%r expected=%r"
              % (registered, declared, EXPECTED_CRITERIA), flush=True)
    check(ok, "AC-COUTB5 the registry and the suite matrix both declare this "
          "suite at %d criteria" % EXPECTED_CRITERIA)


def ac_oosw1():
    """AC-OOSW1: one call site, and the law is not re-implemented here."""
    source = io.open(MODULE, encoding="utf-8").read()
    calls = ("import one_off_round_scripts" in source
             and "OOR.audit(" in source)
    no_walk = "os.walk(" not in source
    no_shape = not re.search(r"re\.compile\([^)]*_R\\?\d", source)
    with io.open(MODULE, "rb") as handle:
        ascii_only = all(byte < 128 for byte in handle.read())
    ok = calls and no_walk and no_shape and ascii_only
    if not ok:
        print("  measured: calls=%r no_walk=%r no_shape=%r ascii=%r"
              % (calls, no_walk, no_shape, ascii_only), flush=True)
    check(ok, "AC-OOSW1 the closeout imports one_off_round_scripts and asks its "
          "audit(), owns no walk and no one-off shape regex of its own, and "
          "stays ASCII")


def ac_oosw2():
    """AC-OOSW2: a new one-off is refused before any byte is written."""
    folder = world()
    state_p = os.path.join(folder, "src", "os", "state.json")
    face_p = os.path.join(folder, "docs", "status-export.json")
    try:
        write(os.path.join(folder, "src", "os", "foo_R2839.py"),
              "print('a new one-off')\n")
        before = (fingerprint(state_p), fingerprint(face_p))
        code, out, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                "--line",
                                "2026-11-16 R%d PRODUCT: a healthy line"
                                % ROUND, "--tick"])
        after = (fingerprint(state_p), fingerprint(face_p))
        ok = (code == 2 and "E_CO_ONE_OFF" in out
              and "foo_R2839.py" in out and before == after
              and "state=NOT-WRITTEN" in out and "face=NOT-WRITTEN" in out)
        if not ok:
            print("  measured: code=%r out=%r state_same=%r face_same=%r"
                  % (code, out.strip()[:200], before[0] == after[0],
                     before[1] == after[1]), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-OOSW2 a one-off named at or above the freeze round reads "
          "E_CO_ONE_OFF at rc=2, is named file by file, and both the state "
          "and the face keep their exact bytes and mtime")


def ac_oosw3():
    """AC-OOSW3: a clean world still closes, and the live tree is not reddened."""
    folder = world()
    try:
        code, out, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                "--line",
                                "2026-11-16 R%d PRODUCT: a clean close"
                                % ROUND, "--tick"])
        live_code, live_out, _ = run_cli(["--root", ROOT, "--round",
                                          str(ROUND), "--line",
                                          "2026-11-16 R%d PRODUCT: live probe"
                                          % ROUND, "--check"])
        ok = (code == 0 and "CLOSEOUT OK" in out and "E_CO_ONE_OFF" not in out
              and "E_CO_ONE_OFF" not in live_out)
        if not ok:
            print("  measured: code=%r out=%r live=%r live_out=%r"
                  % (code, out.strip()[:160], live_code,
                     live_out.strip()[:160]), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-OOSW3 a world with no one-off at the freeze closes normally, "
          "and the live tree's --check carries no E_CO_ONE_OFF")


def ac_oosw4():
    """AC-OOSW4: --check asks the same law and still writes nothing."""
    folder = world()
    state_p = os.path.join(folder, "src", "os", "state.json")
    face_p = os.path.join(folder, "docs", "status-export.json")
    try:
        write(os.path.join(folder, "src", "os", "bar_R2999.py"),
              "print('another one-off')\n")
        before = (fingerprint(state_p), fingerprint(face_p))
        code, out, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                "--line",
                                "2026-11-16 R%d PRODUCT: checked" % ROUND,
                                "--check"])
        after = (fingerprint(state_p), fingerprint(face_p))
        ok = (code == 2 and "E_CO_ONE_OFF" in out and before == after)
        if not ok:
            print("  measured: code=%r out=%r state_same=%r face_same=%r"
                  % (code, out.strip()[:200], before[0] == after[0],
                     before[1] == after[1]), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-OOSW4 --check reddens on the same one-off with rc=2 and "
          "leaves both files' sha256 and mtime unchanged")


def ac_oosw5():
    """AC-OOSW5: the refusal quotes the law's own numbers, not a recount."""
    folder = world()
    try:
        write(os.path.join(folder, "src", "os", "zap_R3000b.py"),
              "print('a third one-off')\n")
        import one_off_round_scripts as OOR
        report, _ = OOR.audit(folder, OOR.DEFAULT_SCOPE, OOR.FREEZE_ROUND)
        code, out, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                "--line",
                                "2026-11-16 R%d PRODUCT: counted" % ROUND,
                                "--tick"])
        wanted = ("scanned=%d" % report["scanned"],
                  "one_offs=%d" % report["one_offs"],
                  "max_round=%d" % report["max_round"],
                  "freeze=%d" % report["freeze"])
        ok = code == 2 and all(token in out for token in wanted)
        if not ok:
            print("  measured: code=%r wanted=%r out=%r"
                  % (code, wanted, out.strip()[:220]), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-OOSW5 the refusal carries scanned / one_offs / max_round / "
          "freeze from the law's own report")


def ac_oosw6():
    """AC-OOSW6: a missing scope is named, not a traceback, and writes nothing."""
    folder = tempfile.mkdtemp(prefix="cout-scope-")
    try:
        code, out, err = run_cli(["--root", folder, "--round", str(ROUND),
                                  "--line",
                                  "2026-11-16 R%d PRODUCT: no scope" % ROUND,
                                  "--tick"])
        leftovers = sorted(os.listdir(folder))
        ok = (code == 2 and "E_CO_ONE_OFF_SCOPE" in out
              and "Traceback" not in (out + err) and leftovers == [])
        if not ok:
            print("  measured: code=%r out=%r err=%r leftovers=%r"
                  % (code, out.strip()[:160], err.strip()[:160], leftovers),
                  flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-OOSW6 a root with no src/os reads E_CO_ONE_OFF_SCOPE with "
          "rc=2, no traceback, and no file written")


def ac_oosw7():
    """AC-OOSW7: registered, and the gate really sits ahead of the state step."""
    runner_text = io.open(RUNNER, encoding="utf-8").read()
    pattern = re.compile(
        r"\(" + json.dumps(LABEL) + r",\s*\n\s*os\.path\.join\([^)]*\),\s*"
        r"(\d+)\)")
    match = pattern.search(runner_text)
    registered = int(match.group(1)) if match else -1
    matrix_path = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
    row = re.search(r"^\|\s*\d+\s*\|\s*%s\s*\|\s*[^|]*\|\s*(\d+)\s*\|"
                    % re.escape(LABEL), read(matrix_path), re.MULTILINE)
    declared = int(row.group(1)) if row else -1
    source = io.open(MODULE, encoding="utf-8").read()
    gate_at = source.find("one_off = one_off_refusal(root)")
    state_at = source.find("SA.run(")
    order_ok = gate_at != -1 and state_at != -1 and gate_at < state_at
    ok = (registered == EXPECTED_CRITERIA and declared == EXPECTED_CRITERIA
          and order_ok)
    if not ok:
        print("  measured: registry=%r matrix=%r expected=%r order=%r"
              % (registered, declared, EXPECTED_CRITERIA, order_ok), flush=True)
    check(ok, "AC-OOSW7 the registry and the suite matrix declare this suite at "
          "%d criteria, and the one-off gate is called before the state step"
          % EXPECTED_CRITERIA)


def ac_cout8():
    """AC-COUT8: the tree the CEO face speaks for is judged before it publishes.

    Five arms, one criterion: a world with no tree closes and SAYS the gate was
    not asked; a world with a drifted census baseline is refused at step tree
    with the state already WRITTEN, the face byte-identical, and the gate's own
    line printed; the replay of that refused round names the half-close instead
    of exiting 0; --check asks the same tree face without writing; and the gate
    module is not imported at closeout.py's module level.
    """
    bare = world()
    drift = world()
    dry = world()
    try:
        code_b, out_b, _ = run_cli([
            "--root", bare, "--round", str(ROUND), "--line",
            "2026-11-16 R%d PRODUCT: a world with no tree" % ROUND, "--tick"])
        bare_ok = (code_b == 0 and "gate=NOT-ASKED" in out_b
                   and "CLOSEOUT GATE NOT-ASKED" in out_b
                   and "E_CO_GATE_NO_INPUTS" in out_b)

        # A tree the gate can read and that has DRIFTED: one baselined defect
        # dialect file, then a second one the baseline never saw.
        import qa_writer_census as cwc
        qa_dir = os.path.join(drift, "qa")
        if not os.path.isdir(qa_dir):
            os.makedirs(qa_dir)
        with io.open(os.path.join(qa_dir, "a.log"), "wb") as handle:
            handle.write(b"\xef\xbb\xbfA BOM PREFIXED LINE\r\n")
        cwc.write_baseline(qa_dir, os.path.join(qa_dir, cwc.BASELINE_NAME))
        with io.open(os.path.join(qa_dir, "b.log"), "wb") as handle:
            handle.write(b"\xef\xbb\xbfANOTHER BOM LINE\r\n")
        write(os.path.join(drift, "docs", "sandbox-suite-matrix.md"),
              "| x |\n")
        set_face_current(drift, "R%d a previous round" % (ROUND - 1))
        face_before = fingerprint(os.path.join(drift, "docs",
                                              "status-export.json"))
        code_d, out_d, _ = run_cli([
            "--root", drift, "--round", str(ROUND), "--line",
            "2026-11-16 R%d PRODUCT: the tree is drifted" % ROUND, "--tick"])
        face_after = fingerprint(os.path.join(drift, "docs",
                                             "status-export.json"))
        tick_d, _log_d = ticks(drift)
        refuse_ok = (code_d == 2 and "E_CO_TREE_RED" in out_d
                     and "step=tree" in out_d
                     and "state=WRITTEN" in out_d
                     and "face=NOT-WRITTEN" in out_d
                     and "tick=%d" % tick_d in out_d
                     and "repair=" in out_d
                     and face_before == face_after)
        if not refuse_ok:
            print("  measured drift: code=%r out=%r face_same=%r"
                  % (code_d, out_d.strip()[:300], face_before == face_after),
                  flush=True)

        code_p, out_p, _ = run_cli([
            "--root", drift, "--round", str(ROUND), "--line",
            "2026-11-16 R%d PRODUCT: the tree is drifted" % ROUND, "--tick"])
        replay_ok = (code_p == 2 and "E_CO_FACE_BEHIND" in out_p
                     and "repair=" in out_p and "face_lagging=1" in out_p)

        code_c, out_c, _ = run_cli([
            "--root", dry, "--round", str(ROUND), "--line",
            "2026-11-16 R%d PRODUCT: dry run" % ROUND, "--check"])
        state_fp = fingerprint(os.path.join(dry, "src", "os", "state.json"))
        dry_ok = (code_c == 0 and "CLOSEOUT CHECK" in out_c
                  and "gate=NOT-ASKED" in out_c
                  and state_fp == fingerprint(os.path.join(
                      dry, "src", "os", "state.json")))

        source = io.open(MODULE, encoding="utf-8").read()
        tree = ast.parse(source)
        top = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                top.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top.add(node.module.split(".")[0])
        lazy_ok = ("closeout_gate" not in top and "qa_writer_census" not in top
                   and "gate_at" not in top)
        order = source.find("tree_refusal(root)")
        # R3128: the call prefix, not the whole call - the writer now takes the
        # corpus reading as a second argument, and a literal that pins the
        # closing paren made an unchanged ORDER read as a missing call.
        face_at = source.find("ER.write(root, stamp")
        lazy_ok = lazy_ok and order != -1 and face_at != -1 and order < face_at

        ok = (bare_ok and refuse_ok and replay_ok and dry_ok and lazy_ok)
        if not ok:
            print("  measured: bare=%r refuse=%r replay=%r dry=%r lazy=%r "
                  "code_b=%r out_b=%r"
                  % (bare_ok, refuse_ok, replay_ok, dry_ok, lazy_ok, code_b,
                     out_b.strip()[:220]), flush=True)
    finally:
        cleanup(bare)
        cleanup(drift)
        cleanup(dry)
    check(ok, "AC-COUT8 the vehicle judges the tree it is about to speak for: "
          "a world with no tree reads gate=NOT-ASKED with its reason printed, "
          "a drifted census baseline is refused at step tree with the state "
          "WRITTEN and the face byte-identical, the replay names the "
          "half-close, --check asks the same face without writing, and the "
          "gate stays lazily imported ahead of the face step")


def ac_cout9():
    """AC-COUT9: a refusal that names only its headline is not actionable.

    Six arms, one criterion: the vehicle carries the gate's own fine print, so
    "census=FAIL" is no longer the last word when the truth is "this root has
    no registry to judge"; the flags face's rows arrive the same way; the dry
    run asks it too without writing; the live tree stays PASS with no detail;
    and the vehicle derives the lines instead of re-typing them.
    """
    import qa_writer_census as cwc

    def tree_world(flags=0):
        folder = world()
        qa_dir = os.path.join(folder, "qa")
        if not os.path.isdir(qa_dir):
            os.makedirs(qa_dir)
        write(os.path.join(qa_dir, "a.log"), "plain healthy line\n")
        cwc.write_baseline(qa_dir, os.path.join(qa_dir, cwc.BASELINE_NAME))
        write(os.path.join(folder, "docs", "sandbox-suite-matrix.md"), "| x |\n")
        for index in range(flags):
            with io.open(os.path.join(qa_dir, "bad%d.log" % index), "wb") as fh:
                fh.write(b"\xef\xbb\xbfA BOM LINE\r\n")
        return folder

    foreign = tree_world()
    drift = tree_world(flags=2)
    flood = tree_world(flags=12)
    dry = tree_world()
    try:
        word, line, verdict = CO.tree_refusal(foreign)
        detail = verdict.get("detail") or []
        a_ok = (word == "RED"
                and verdict.get("cause") == "E_CLG_FOREIGN_REGISTRY"
                and any(row.startswith("E_CLG_FOREIGN_REGISTRY face=census")
                        for row in detail)
                and any(os.path.basename(foreign) in row for row in detail)
                and "reason=E_CLG_CENSUS" in line and "census=FAIL" in line)

        set_face_current(foreign, "R%d a previous round" % (ROUND - 1))
        face_before = fingerprint(os.path.join(foreign, "docs",
                                               "status-export.json"))
        code_b, out_b, _ = run_cli([
            "--root", foreign, "--round", str(ROUND), "--line",
            "2026-11-16 R%d PRODUCT: the root carries no registry" % ROUND,
            "--tick"])
        face_after = fingerprint(os.path.join(foreign, "docs",
                                              "status-export.json"))
        tick_b, _log_b = ticks(foreign)
        b_ok = (code_b == 2 and "E_CO_TREE_RED" in out_b
                and "step=tree" in out_b and "state=WRITTEN" in out_b
                and "face=NOT-WRITTEN" in out_b
                and "E_CLG_FOREIGN_REGISTRY face=census" in out_b
                and tick_b > ROUND and face_before == face_after)

        code_c, out_c, _ = run_cli([
            "--root", drift, "--round", str(ROUND), "--line",
            "2026-11-16 R%d PRODUCT: two flagged files" % ROUND, "--tick"])
        c_ok = (code_c == 2 and "flags=2" in out_c
                and out_c.count("[flag]") == 2)

        state_fp = fingerprint(os.path.join(dry, "src", "os", "state.json"))
        code_d, out_d, _ = run_cli([
            "--root", dry, "--round", str(ROUND), "--line",
            "2026-11-16 R%d PRODUCT: dry run" % ROUND, "--check"])
        d_ok = (code_d == 2 and "CLOSEOUT CHECK RED" in out_d
                and "E_CLG_FOREIGN_REGISTRY face=census" in out_d
                and state_fp == fingerprint(os.path.join(
                    dry, "src", "os", "state.json")))

        live_word, live_line, live_verdict = CO.tree_refusal(ROOT)
        # R3109 JUDGED-CHANGED: a green tree now carries READING rows (the
        # baseline identity) in `detail`, so "no detail at all" is no longer
        # the right assertion. The arm's intent is kept: a PASS may never carry
        # the gate's REFUSAL fine print - no flag rows, no error codes, and no
        # cause - and the green headline is unchanged.
        live_detail = list(live_verdict.get("detail") or [])
        e_ok = (live_word == "PASS" and "census=PASS" in live_line
                and not [row for row in live_detail
                         if row.startswith("[flag]")]
                and not [row for row in live_detail
                         if row.split(" ", 1)[0].startswith("E_")]
                and not live_verdict.get("cause"))

        code_f, out_f, _ = run_cli([
            "--root", flood, "--round", str(ROUND), "--line",
            "2026-11-16 R%d PRODUCT: twelve flagged files" % ROUND, "--tick"])
        import closeout_gate as CG
        gate_lines, gate_code, _ = CG.evaluate(
            os.path.join(flood, "qa"),
            os.path.join(flood, "qa", CG.CENSUS.BASELINE_NAME), root=flood)
        expected_omitted = max(0, len(gate_lines) - 1 - CO.TREE_DETAIL_CAP)
        _fw, _fl, flood_verdict = CO.tree_refusal(flood)
        # DERIVATION, not a name: the vehicle's detail must be the gate's own
        # lines, byte for byte, so a re-typed copy would fail this arm.
        derived = (flood_verdict.get("detail") or []) == \
            gate_lines[1:1 + CO.TREE_DETAIL_CAP]
        source = io.open(MODULE, encoding="utf-8").read()
        f_ok = (gate_code == 2
                and out_f.count("[flag]") == CO.TREE_DETAIL_CAP
                and ("CLOSEOUT TREE detail-truncated omitted=%d"
                     % expected_omitted) in out_f
                and derived
                and source.find("import closeout_gate") > source.find(
                    "def tree_refusal"))

        ok = a_ok and b_ok and c_ok and d_ok and e_ok and f_ok
        if not ok:
            print("  measured: a=%r b=%r c=%r d=%r e=%r f=%r code_b=%r "
                  "out_b=%r code_c=%r out_c=%r"
                  % (a_ok, b_ok, c_ok, d_ok, e_ok, f_ok, code_b,
                     out_b.strip()[:260], code_c, out_c.strip()[:200]),
                  flush=True)
    finally:
        cleanup(foreign)
        cleanup(drift)
        cleanup(flood)
        cleanup(dry)
    check(ok, "AC-COUT9 the vehicle carries the gate's own fine print: a root "
          "with no registry reads cause=E_CLG_FOREIGN_REGISTRY with the "
          "registry and root named, the flags face's rows arrive, --check asks "
          "it without writing, the live tree stays PASS with no refusal fine "
          "print, and "
          "the lines are byte-identical to the gate's own (a re-typed copy "
          "would fail) with a named cap")


def ac_cout10():
    """AC-COUT10: the not-asked line names all three inputs it did not find.

    Six arms, one criterion: a world with a qa dir and a document but no census
    baseline says baseline=0 instead of claiming the world has no tree; an
    empty world names all three; a world with a baseline but no document names
    the document; the missing set is DERIVED from the three printed readings
    (a re-typed list would fail); the code stays ONE token so the shipped
    substring arm still matches; and the live tree still reads PASS.
    """
    import re as _re
    import qa_writer_census as cwc

    def qa_doc(folder, baseline=None, doc=True):
        qa_dir = os.path.join(folder, "qa")
        if not os.path.isdir(qa_dir):
            os.makedirs(qa_dir)
        if baseline is not None:
            with io.open(os.path.join(qa_dir, cwc.BASELINE_NAME), "wb") as fh:
                fh.write(b'{"empty": true}\n')
        if doc:
            write(os.path.join(folder, "docs", "sandbox-suite-matrix.md"),
                  "| x |\n")
        return folder

    bare = world()
    with_qa_doc = qa_doc(world())
    with_baseline = qa_doc(world(), baseline=True, doc=False)
    tokens = _re.compile(r"qa=(\d) baseline=(\d) doc=(\d) missing=([a-z,]+)")


    def parse(line):
        found = tokens.search(line)
        return tuple(found.groups()) if found else None


    def derive(readings):
        names = ("qa", "baseline", "doc")
        return ",".join(name for name, bit in zip(names, readings)
                        if bit == "0")

    try:
        word_a, line_a, verdict_a = CO.tree_refusal(with_qa_doc)
        parsed_a = parse(line_a)
        a_ok = (word_a == "NOT-ASKED" and verdict_a == {}
                and parsed_a is not None and parsed_a[:3] == ("1", "0", "1")
                and parsed_a[3] == "baseline"
                and "builds no tree" not in line_a)

        word_b, line_b, _v_b = CO.tree_refusal(bare)
        parsed_b = parse(line_b)
        b_ok = (word_b == "NOT-ASKED" and parsed_b is not None
                and parsed_b[:3] == ("0", "0", "0")
                and parsed_b[3] == "qa,baseline,doc")

        word_c, line_c, _v_c = CO.tree_refusal(with_baseline)
        parsed_c = parse(line_c)
        c_ok = (word_c == "NOT-ASKED" and parsed_c is not None
                and parsed_c[:3] == ("1", "1", "0")
                and parsed_c[3] == "doc")

        # DERIVATION: recompute the missing set from the three printed bits.
        d_ok = all(parse(line)[3] == derive(parse(line)[:3])
                   for line in (line_a, line_b, line_c))

        code_e, out_e, _ = run_cli([
            "--root", with_qa_doc, "--round", str(ROUND), "--line",
            "2026-11-16 R%d PRODUCT: qa and doc but no baseline" % ROUND,
            "--tick"])
        e_ok = (code_e == 0 and "gate=NOT-ASKED" in out_e
                and "CLOSEOUT GATE NOT-ASKED" in out_e
                and "E_CO_GATE_NO_INPUTS qa=1 baseline=0 doc=1 missing=baseline"
                in out_e)

        live_word, live_line, _live_v = CO.tree_refusal(ROOT)
        f_ok = live_word == "PASS" and "census=PASS" in live_line

        ok = a_ok and b_ok and c_ok and d_ok and e_ok and f_ok
        if not ok:
            print("  measured: a=%r b=%r c=%r d=%r e=%r f=%r lines=%r"
                  % (a_ok, b_ok, c_ok, d_ok, e_ok, f_ok,
                     (line_a, line_b, line_c)), flush=True)
    finally:
        cleanup(bare)
        cleanup(with_qa_doc)
        cleanup(with_baseline)
    check(ok, "AC-COUT10 the not-asked line names all three gate inputs: a "
          "world with qa and a document but no baseline reads baseline=0 "
          "with missing=baseline instead of claiming a treeless world, an "
          "empty world names all three, a baseline without a document names "
          "the document, the missing set is derived from the printed bits, "
          "the code stays one token, and the live tree still reads PASS")


def ac_cout11():
    """AC-COUT11: the not-asked line says what else sits where the gate looked.

    Six arms, one criterion (R3108): a world with a FILE named qa and a world
    with no qa at all no longer print the same sentence; a baseline carrying
    another name is named instead of merely implied absent; a qa directory
    holding nothing near-name prints hint=none rather than a false lead; the
    hint is DERIVED from the disk (a second near-name file changes the printed
    count); the shipped parser and AC-COUT10's exact substring still match the
    longer line; and the live tree still reads PASS without a hint token.
    """
    import re as _re
    import qa_writer_census as cwc

    tokens = _re.compile(r"qa=(\d) baseline=(\d) doc=(\d) missing=([a-z,]+)")

    def build(folder, doc=True):
        for sub in ("qa", "docs"):
            path = os.path.join(folder, sub)
            if not os.path.isdir(path):
                os.makedirs(path)
        if doc:
            write(os.path.join(folder, "docs", "sandbox-suite-matrix.md"),
                  "| x |\n")
        return folder

    bare = world()
    qa_file = world()
    write(os.path.join(qa_file, "qa"), "not a directory\n")
    near = build(world())
    write(os.path.join(near, "qa", "baseline.json"), "{}\n")
    empty_qa = build(world())

    try:
        word_bare, line_bare, _v1 = CO.tree_refusal(bare)
        word_file, line_file, _v2 = CO.tree_refusal(qa_file)
        a_ok = (word_bare == word_file == "NOT-ASKED"
                and "hint=qa-is-file" in line_file
                and "hint=none" in line_bare
                and line_bare != line_file)

        word_near, line_near, _v3 = CO.tree_refusal(near)
        b_ok = (word_near == "NOT-ASKED" and tokens.search(line_near) is not None
                and tokens.search(line_near).group(4) == "baseline"
                and "near-baseline:1:qa/baseline.json" in line_near)

        word_empty, line_empty, _v4 = CO.tree_refusal(empty_qa)
        c_ok = word_empty == "NOT-ASKED" and "hint=none" in line_empty

        # DERIVATION: a second near-name file must move the printed count.
        write(os.path.join(near, "qa", "another-baseline.json"), "{}\n")
        _w, line_near2, _v5 = CO.tree_refusal(near)
        d_ok = ("near-baseline:2:" in line_near2
                and "qa/another-baseline.json" in line_near2)

        # ZERO COLLISION: the one shipped parser and AC-COUT10's substring.
        parsed = tokens.search(line_near)
        e_ok = (parsed is not None
                and parsed.groups() == ("1", "0", "1", "baseline")
                and "E_CO_GATE_NO_INPUTS qa=1 baseline=0 doc=1 "
                    "missing=baseline" in line_near
                and cwc.BASELINE_NAME not in line_near)

        live_word, live_line, _live_v = CO.tree_refusal(ROOT)
        f_ok = (live_word == "PASS" and "census=PASS" in live_line
                and "hint=" not in live_line)

        ok = a_ok and b_ok and c_ok and d_ok and e_ok and f_ok
        if not ok:
            print("  measured: a=%r b=%r c=%r d=%r e=%r f=%r lines=%r"
                  % (a_ok, b_ok, c_ok, d_ok, e_ok, f_ok,
                     (line_bare, line_file, line_near, line_near2)),
                  flush=True)
    finally:
        cleanup(bare)
        cleanup(qa_file)
        cleanup(near)
        cleanup(empty_qa)
    check(ok, "AC-COUT11 the not-asked line carries a derived hint: a file "
          "named qa no longer prints what an absent qa prints, a near-name "
          "baseline is named with its real count, an empty qa directory says "
          "hint=none, the hint is recomputed from the disk, the shipped "
          "parser and AC-COUT10's substring still match, and the live tree "
          "still reads PASS")


def ac_cout12():
    """AC-COUT12: the closed round names the baseline its census face judged.

    Three arms, one criterion (R3109): the live PASS verdict carries the gate's
    derived identity row; the dry run PRINTS it (so an operator holding the
    round output can re-check the file); and a world that builds no tree has an
    empty detail, because nothing was judged and nothing may be implied.
    """
    live_word, live_line, live_verdict = CO.tree_refusal(ROOT)
    detail = list(live_verdict.get("detail") or [])
    ident = [row for row in detail if row.startswith("CENSUS-BASELINE ")]
    live_base = os.path.join(ROOT, "qa", "writer-census-baseline.json")
    want_sha = ""
    if os.path.isfile(live_base):
        with io.open(live_base, "rb") as handle:
            want_sha = hashlib.sha256(handle.read()).hexdigest()[:12]
    a_ok = (live_word == "PASS" and len(ident) == 1
            and ("sha256=%s" % want_sha) in ident[0]
            and "name=qa/writer-census-baseline.json" in ident[0])

    tick = int(ticks(ROOT)[0])
    code_b, out_b, _err_b = run_cli(
        ["--check", "--round", str(tick + 1),
         "--line", "2026-11-20 R%d SMOKE the dry run names the baseline it "
                   "judged" % (tick + 1)])
    b_ok = (code_b == 0 and "gate=PASS" in out_b
            and any(row.startswith("CENSUS-BASELINE ")
                    for row in out_b.splitlines()))

    bare = world()
    try:
        word_c, _line_c, verdict_c = CO.tree_refusal(bare)
        c_ok = (word_c in ("NOT-ASKED",)
                and not (verdict_c.get("detail") or []))
    finally:
        cleanup(bare)

    ok = a_ok and b_ok and c_ok
    if not ok:
        print("  measured: a=%r b=%r c=%r detail=%r out=%r"
              % (a_ok, b_ok, c_ok, detail, out_b[:400]), flush=True)
    check(ok, "AC-COUT12 the round output names the baseline its census face "
          "judged: the PASS verdict carries the derived identity row, the dry "
          "run prints it, and a world with no tree carries no detail")


def ac_cout13():
    """AC-COUT13: the closed round also aligns the heartbeat row.

    Six arms, one criterion (R3111): the row is DERIVED from the tick the round
    just proved on disk (a second closeout must write the new tick, not append
    to the old one), a duplicate replay leaves it byte-identical, a world whose
    heartbeat name is occupied is refused BY NAME with the face untouched, a
    dry run writes nothing and only READS the row, and the live tree's row
    equals its state tick.
    """
    folder = world()
    hb_path = os.path.join(folder, "heartbeat.txt")
    face_path = os.path.join(folder, "docs", "status-export.json")
    try:
        # a: from absent to the derived single line, with no temp file left.
        a_ok = HB.read_tick(folder) is None
        code_a, out_a, _ = run_cli(["--root", folder, "--round", str(ROUND),
                                    "--line",
                                    "2026-11-16 R%d PRODUCT: heartbeat lands"
                                    % ROUND, "--tick"])
        tick_a, _ = ticks(folder)
        with io.open(hb_path, "rb") as handle:
            raw_a = handle.read()
        leftovers = [name for name in os.listdir(folder)
                     if name.startswith(".heartbeat.tmp-")]
        a_ok = (a_ok and code_a == 0 and "hb=%d" % tick_a in out_a
                and raw_a == ("tick %d\n" % tick_a).encode("ascii")
                and not leftovers)

        # b: derivation - a second closeout writes the NEW tick, single line.
        code_b, out_b, _ = run_cli(["--root", folder, "--round",
                                    str(ROUND + 1), "--line",
                                    "2026-11-16 R%d PRODUCT: heartbeat moves"
                                    % (ROUND + 1), "--tick"])
        tick_b, _ = ticks(folder)
        with io.open(hb_path, "rb") as handle:
            raw_b = handle.read()
        b_ok = (code_b == 0 and tick_b == tick_a + 1
                and raw_b == ("tick %d\n" % tick_b).encode("ascii"))

        # c: a duplicate replay does not touch the row.
        before_c = fingerprint(hb_path)
        code_c, out_c, _ = run_cli(["--root", folder, "--round",
                                    str(ROUND + 1), "--line",
                                    "2026-11-16 R%d PRODUCT: heartbeat moves"
                                    % (ROUND + 1), "--tick"])
        c_ok = (code_c == 0 and "E_CO_DUPLICATE" in out_c
                and fingerprint(hb_path) == before_c)

        # d: an occupied name is refused by name, the face keeps its bytes.
        blocked = world(ROUND + 10)
        blocked_hb = os.path.join(blocked, "heartbeat.txt")
        blocked_face = os.path.join(blocked, "docs", "status-export.json")
        try:
            os.makedirs(blocked_hb)
            face_before = fingerprint(blocked_face)
            code_d, out_d, _ = run_cli(
                ["--root", blocked, "--round", str(ROUND + 10), "--line",
                 "2026-11-16 R%d PRODUCT: heartbeat blocked" % (ROUND + 10),
                 "--tick"])
            tick_d, _ = ticks(blocked)
            d_ok = (code_d == 2 and "E_CO_HB_UNPROVEN" in out_d
                    and "face=NOT-WRITTEN" in out_d
                    and fingerprint(blocked_face) == face_before
                    and tick_d == ROUND + 11 and os.path.isdir(blocked_hb))
        finally:
            cleanup(blocked)

        # e: a dry run writes nothing and only reads the row.
        dry = world(ROUND + 20)
        dry_hb = os.path.join(dry, "heartbeat.txt")
        dry_state = os.path.join(dry, "src", "os", "state.json")
        dry_face = os.path.join(dry, "docs", "status-export.json")
        try:
            before_e = (fingerprint(dry_state), fingerprint(dry_face))
            code_e, out_e, _ = run_cli(
                ["--root", dry, "--round", str(ROUND + 20), "--line",
                 "2026-11-16 R%d PRODUCT: dry run reads only" % (ROUND + 20),
                 "--tick", "--check"])
            after_e = (fingerprint(dry_state), fingerprint(dry_face))
            e_ok = (code_e == 0 and "hb=none" in out_e
                    and not os.path.exists(dry_hb) and before_e == after_e)
        finally:
            cleanup(dry)

        # f: the live tree's row equals its state tick.
        live_tick, _ = ticks(ROOT)
        f_ok = HB.read_tick(ROOT) == live_tick

        ok = a_ok and b_ok and c_ok and d_ok and e_ok and f_ok
        if not ok:
            print("  measured: a=%r b=%r c=%r d=%r e=%r f=%r raw_a=%r "
                  "raw_b=%r out_d=%r out_e=%r"
                  % (a_ok, b_ok, c_ok, d_ok, e_ok, f_ok, raw_a[:40],
                     raw_b[:40], out_d.strip()[:200], out_e.strip()[:160]),
                  flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-COUT13 the closed round derives the heartbeat row from the "
          "tick it just proved, a replay leaves it untouched, an occupied "
          "name is refused by name with the face intact, a dry run writes "
          "nothing, and the live row equals the live tick")


def ac_cout14():
    """AC-COUT14: the heartbeat line carries its judgment, not only its tick.

    Five arms, one criterion (R3114): R3113 published the reading and R3114
    measured that nothing consumed it, while `hb=` still printed a lagging row
    exactly like a fresh one. The OK path must say PASS (derived, not typed),
    a lagging private world must say FLAG with the debt reason, a world with no
    row must say FLAG with the missing reason, both token values are graded for
    shape, and the live dry run must agree with heartbeat.verify character for
    character.
    """
    folder = world(ROUND + 40)
    try:
        code_a, out_a, _ = run_cli(["--root", folder, "--round",
                                    str(ROUND + 40), "--line",
                                    "2026-11-21 R%d PRODUCT: verdict lands"
                                    % (ROUND + 40), "--tick"])
        a_ok = code_a == 0 and "hb_verdict=PASS" in out_a
    finally:
        cleanup(folder)

    lagging = world(ROUND + 50)
    try:
        HB.write_tick(lagging, ROUND + 47)
        code_b, out_b, _ = run_cli(
            ["--root", lagging, "--round", str(ROUND + 50), "--line",
             "2026-11-21 R%d PRODUCT: lagging dry run" % (ROUND + 50),
             "--tick", "--check"])
        b_ok = (code_b == 0 and "hb_verdict=FLAG" in out_b
                and "hb_reason=heartbeat_row_debt" in out_b)
    finally:
        cleanup(lagging)

    bare = world(ROUND + 60)
    try:
        code_c, out_c, _ = run_cli(
            ["--root", bare, "--round", str(ROUND + 60), "--line",
             "2026-11-21 R%d PRODUCT: no row dry run" % (ROUND + 60),
             "--tick", "--check"])
        c_ok = (code_c == 0 and "hb=none" in out_c
                and "hb_verdict=FLAG" in out_c
                and "hb_reason=heartbeat_missing_or_unparsed" in out_c)
    finally:
        cleanup(bare)

    shape = re.compile(r"hb_verdict=(PASS|FLAG)(?: hb_reason=([a-z_]+))?")
    seen = shape.findall(out_a) + shape.findall(out_b) + shape.findall(out_c)
    d_ok = (len(seen) == 3
            and all(reason == "" or re.match(r"^[a-z_]+$", reason)
                    for _status, reason in seen))

    live_tick, _ = ticks(ROOT)
    live = HB.verify(ROOT, live_tick)
    code_e, out_e, _ = run_cli(["--root", ROOT, "--round", str(live_tick + 1),
                                "--line",
                                "2026-11-21 R%d SMOKE the dry run prints the "
                                "heartbeat verdict it derived"
                                % (live_tick + 1), "--check"])
    if live.get("tick") is None:
        want = "hb=none hb_verdict=FLAG hb_reason=heartbeat_missing_or_unparsed"
    else:
        want = "hb=%d hb_verdict=%s" % (int(live["tick"]), live["status"])
        if live["status"] != "PASS":
            want += " hb_reason=%s" % live["reason"]
    e_ok = code_e == 0 and want in out_e

    ok = a_ok and b_ok and c_ok and d_ok and e_ok
    if not ok:
        print("  measured: a=%r b=%r c=%r d=%r e=%r out_a=%r out_b=%r "
              "out_c=%r want=%r"
              % (a_ok, b_ok, c_ok, d_ok, e_ok, out_a.strip()[:220],
                 out_b.strip()[:220], out_c.strip()[:220], want), flush=True)
    check(ok, "AC-COUT14 the heartbeat line carries its judgment: OK says "
          "PASS, a lagging row says FLAG with the debt reason, a missing row "
          "says FLAG with the missing reason, both tokens are shape-graded, "
          "and the live dry run agrees with heartbeat.verify")


def ac_cout15():
    """AC-COUT15: the stage sweep line is a display nothing parses, so this
    criterion is its only guard.

    MEASURED at R3120 before this arm existed: `stage_residue=` / `swept=` /
    `skipped=` appear in shipped code exactly twice, both as WRITERS
    (closeout.py:436 and :438); no shipped reader parses them. A display with no
    reader is exactly the line a refactor drops without a red test, so the four
    arms below pin the shape a person reads on the CEO face: the dry run counts
    and touches nothing, the OK path names swept and skipped, a suffix-named
    DIRECTORY is skipped rather than swept, and a missing module is a refusal
    with a name instead of a silent skip.
    """
    world = tempfile.mkdtemp(prefix="cout15-")
    face = os.path.join(world, "docs", "status-export.json")
    os.makedirs(os.path.dirname(face))
    with open(face, "w", encoding="utf-8", newline="\n") as handle:
        handle.write('{"export_ts": "2026-11-21T12:00:00+08:00"}\n')
    with open(face, "rb") as handle:
        before = handle.read()

    # R3122: the step now prints its own cost, and a millisecond reading can
    # never be byte-stable, so the count segment stays pinned EXACTLY while the
    # tail must be a number. This amendment was recorded on the board before
    # any evidence existed (R3122 PIN row).
    def counts_of(line):
        head, sep, tail = line.rpartition(" walk_ms=")
        return head if sep else line

    def walk_ms_ok(line):
        head, sep, tail = line.rpartition(" walk_ms=")
        return bool(sep) and tail.replace(".", "", 1).isdigit()
    planted = []
    for suffix in (".sxf-stage", ".parity-stage"):
        path = face + suffix
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write('{"partial')
        planted.append(path)

    dry = CO.stage_residue_face(world, dry_run=True)
    a_ok = (counts_of(dry) == "stage_residue=%d swept=0" % len(planted)
            and walk_ms_ok(dry)
            and all(os.path.isfile(p) for p in planted))
    if not a_ok:
        print("  measured dry=%r left=%r"
              % (dry, [os.path.isfile(p) for p in planted]), flush=True)

    done = CO.stage_residue_face(world)
    b_ok = (counts_of(done) == "stage_residue=%d swept=%d skipped=0"
            % (len(planted), len(planted))
            and walk_ms_ok(done)
            and not any(os.path.exists(p) for p in planted)
            and open(face, "rb").read() == before)
    if not b_ok:
        print("  measured done=%r left=%r"
              % (done, [os.path.exists(p) for p in planted]), flush=True)

    held = os.path.join(world, "docs", "held.gate-stage")
    os.makedirs(held)
    skipped_line = CO.stage_residue_face(world)
    c_ok = (counts_of(skipped_line) == "stage_residue=1 swept=0 skipped=1"
            and walk_ms_ok(skipped_line)
            and os.path.isdir(held))
    if not c_ok:
        print("  measured skipped=%r held=%s"
              % (skipped_line, os.path.isdir(held)), flush=True)

    saved = sys.modules.get("stage_residue")
    sys.modules["stage_residue"] = None
    try:
        refusal = CO.stage_residue_face(world)
    finally:
        if saved is None:
            sys.modules.pop("stage_residue", None)
        else:
            sys.modules["stage_residue"] = saved
    d_ok = refusal.startswith("E_CO_STAGE_UNAVAILABLE module=")

    # ---- R3121: a blind spot and an OS refusal get their own words. ------
    # The clean case above must stay byte-identical (arms a/b), so the new
    # tokens appear ONLY when they are non-zero; these two arms prove they do.
    blind = tempfile.mkdtemp(prefix="cout15b-")
    os.makedirs(os.path.join(blind, "docs"))
    blind_face = os.path.join(blind, "docs", "status-export.json")
    with open(blind_face, "w", encoding="utf-8", newline="\n") as handle:
        handle.write('{"export_ts": "2026-11-21T12:00:00+08:00"}\n')
    hidden = os.path.join(blind, "state", "denied")
    os.makedirs(hidden)
    real_listdir = os.listdir

    def blind_listdir(path, *args, **kwargs):
        if os.path.abspath(path) == os.path.abspath(hidden):
            raise PermissionError(13, "denied by the arm")
        return real_listdir(path, *args, **kwargs)

    os.listdir = blind_listdir
    try:
        unread_line = CO.stage_residue_face(blind, dry_run=True)
    finally:
        os.listdir = real_listdir
    e_ok = (unread_line.startswith(
        "stage_residue=0 swept=0 unreadable=1 dirs=state/denied:")
        and open(blind_face, "rb").read().startswith(b'{"export_ts"'))

    stuck = os.path.join(blind, "docs", "status-export.json.sxf-stage")
    with open(stuck, "w", encoding="utf-8", newline="\n") as handle:
        handle.write('{"partial')
    handle = open(stuck, "r", encoding="utf-8")
    try:
        failed_line = CO.stage_residue_face(blind)
    finally:
        handle.close()
    code = "winerror=32" if os.name == "nt" else "errno="
    f_ok = (failed_line.startswith(
        "stage_residue=1 swept=0 skipped=0 failed=1 "
        "names=docs/status-export.json.sxf-stage:")
        and code in failed_line and os.path.isfile(stuck))
    shutil.rmtree(blind, ignore_errors=True)

    # ---- R3122 arm g: the OK path walks the tree ONCE, not twice. -------
    # Measured before the arm existed (tmp/probe_R3122.py -> qa/probe-R3122.log):
    # one walk costs 910.9ms over 3482 directories and the step used to pay it
    # twice (scan_report, then sweep which scanned again).
    import stage_residue as SRG
    once = tempfile.mkdtemp(prefix="cout15c-")
    for name in ("docs", "logs", "state"):
        os.makedirs(os.path.join(once, name))
    with open(os.path.join(once, "docs", "status-export.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write('{"export_ts": "2026-11-21T12:00:00+08:00"}\n')
    with open(os.path.join(once, "docs", "status-export.json.sxf-stage"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write('{"partial')
    folders = SRG.scan_report(once)["folders"]
    walked = []
    plain_listdir = os.listdir

    def counting_listdir(path, *args, **kwargs):
        walked.append(path)
        return plain_listdir(path, *args, **kwargs)

    os.listdir = counting_listdir
    try:
        once_line = CO.stage_residue_face(once)
    finally:
        os.listdir = plain_listdir
    g_ok = (len(walked) == folders and folders > 0
            and counts_of(once_line) == "stage_residue=1 swept=1 skipped=0")
    if not g_ok:
        print("  measured g=%r walks=%d folders=%d line=%r"
              % (g_ok, len(walked), folders, once_line), flush=True)
    shutil.rmtree(once, ignore_errors=True)

    shutil.rmtree(world, ignore_errors=True)
    ok = a_ok and b_ok and c_ok and d_ok and e_ok and f_ok and g_ok
    if not ok:
        print("  measured: a=%r b=%r c=%r d=%r refusal=%r"
              % (a_ok, b_ok, c_ok, d_ok, refusal), flush=True)
    check(ok, "AC-COUT15 the sweep line names what it did on both paths: the "
          "dry run counts and touches nothing, the OK path names swept and "
          "skipped, a suffix-named directory is skipped rather than swept, a "
          "missing module is a named refusal, an unlistable directory is "
          "named rather than implied covered, an OS refusal is named with "
          "its own code, and the OK path walks the tree exactly once while "
          "printing its own walk_ms")


def ac_cout16():
    """AC-COUT16: every step of a closeout is paid for by a named reading.

    MEASURED at R3123 on the live tree before this criterion existed: one
    `--check` closeout made 3484 listdir calls (3482 of them the stage walk, 2
    the matrix leg scan), 2 scandir calls and 1 os.walk, and the printed
    readings summed to 2794.7ms against 2810.5ms of wall time. The WHOLE gap
    was step 0 - the one-off audit's walk of src/os, 14.8ms - which no token
    named on either path; the OK path additionally printed no reading for the
    export write, its largest unnamed step. Both are now measured and named.
    The arms pin the names, not the numbers: a millisecond can never be
    byte-stable, and the derivation (not the value) is what a refactor drops.
    """
    def ms_tokens(line):
        return dict(re.findall(r"\b([a-z_]+)_ms=(\d+(?:\.\d+)?)", line))

    folder = world()
    try:
        check_code, check_out, _ = run_cli(
            ["--root", folder, "--round", str(ROUND),
             "--line", "2026-11-21 R%d PRODUCT: measured dry run" % ROUND,
             "--check"])
        ok_code, ok_out, _ = run_cli(
            ["--root", folder, "--round", str(ROUND),
             "--line", "2026-11-21 R%d PRODUCT: measured close" % ROUND,
             "--tick"])
        check_line = [row for row in check_out.splitlines()
                      if row.startswith("CLOSEOUT CHECK")]
        ok_line = [row for row in ok_out.splitlines()
                   if row.startswith("CLOSEOUT OK")]
        check_bits = ms_tokens(check_line[0]) if check_line else {}
        ok_bits = ms_tokens(ok_line[0]) if ok_line else {}

        dry_named = {"state", "walk", "oneoff"}
        a_ok = (check_code == 0 and dry_named <= set(check_bits)
                and "export" not in check_bits)
        b_ok = (ok_code == 0 and {"oneoff", "export", "walk"} <= set(ok_bits))
        c_ok = (all(float(v) >= 0.0 for v in check_bits.values())
                and all(float(v) >= 0.0 for v in ok_bits.values()))
        if not (a_ok and b_ok and c_ok):
            print("  measured: codes=%r/%r check=%r ok=%r"
                  % (check_code, ok_code, sorted(check_bits), sorted(ok_bits)),
                  flush=True)

        # e: the four gate-face readings exist only where the gate is ASKED,
        # which the fixture world is not - so they are pinned on the live tree,
        # read-only, the same way AC-COUT9 and AC-COUT10 pin their live arms.
        live_code, live_out, _ = run_cli(
            ["--round", str(int(ticks(ROOT)[0]) + 1),
             "--line", "2026-11-21 R%d PRODUCT: live accounting arm"
                       % (int(ticks(ROOT)[0]) + 1),
             "--check"])
        live_bits = {}
        for row in live_out.splitlines():
            if row.startswith("CLOSEOUT CHECK"):
                live_bits = ms_tokens(row)
                break
        e_ok = (live_code == 0
                and {"flags", "round_main", "census", "matrix", "state",
                     "walk", "oneoff"} <= set(live_bits)
                and "export" not in live_bits)
        if not e_ok:
            print("  measured e=%r code=%r bits=%r"
                  % (e_ok, live_code, sorted(live_bits)), flush=True)

        # d: both readings are DERIVED from the clock, never typed. The arm
        # asks the source, because a hand-typed 0.0 passes every value test.
        src = read(MODULE)
        tree = ast.parse(src)
        derived = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id not in ("oneoff_ms", "export_ms"):
                    continue
                calls = [n for n in ast.walk(node.value)
                         if isinstance(n, ast.Call)
                         and isinstance(n.func, ast.Attribute)
                         and n.func.attr == "perf_counter"]
                subs = [n for n in ast.walk(node.value)
                        if isinstance(n, ast.BinOp)
                        and isinstance(n.op, ast.Sub)]
                derived[target.id] = bool(calls) and bool(subs)
        d_ok = (derived.get("oneoff_ms") and derived.get("export_ms")
                and "time.perf_counter" not in json.dumps(derived))
        if not d_ok:
            print("  measured d=%r" % (derived,), flush=True)
    finally:
        cleanup(folder)
    ok = a_ok and b_ok and c_ok and d_ok and e_ok
    check(ok, "AC-COUT16 the dry run names all seven timed steps it asks and "
          "no write step, the OK path names the export write it performed, "
          "every reading is a non-negative decimal, both new readings are "
          "derived from the clock rather than typed, and the live tree names "
          "the four gate faces alongside them")


def ac_cout17():
    """AC-COUT17: the tree gate's cost is on BOTH paths, and it is bytes.

    MEASURED at R3124 before this criterion existed (tmp/probe_R3124.py ->
    qa/probe-R3124.log): the `flags` face took 1186.3ms of a 2749.8ms dry run
    and its own breakdown was 13.7ms enumeration (1.2%), 831.6ms whole-blob
    read (69.9%, 582.6MB/s over 484.5MB) and 337.0ms classification (28.3%) -
    so the cost follows BYTES, not file names. The OK path printed oneoff_ms,
    export_ms and walk_ms and NOT ONE of the four face readings it had just
    paid ~1.75s for. The arms pin the visibility and the out-of-band ride, not
    the milliseconds: a reading never becomes a verdict.
    """
    def ms_tokens(line):
        return dict(re.findall(r"\b([a-z_]+)_ms=(\d+(?:\.\d+)?)", line))

    # a: the live dry run names the face AND the corpus it paid for.
    live_tick = int(ticks(ROOT)[0])
    code, out, _ = run_cli(["--round", str(live_tick + 1), "--line",
                            "2026-11-21 R%d PRODUCT: gate ledger arm"
                            % (live_tick + 1), "--check"])
    check_line = [row for row in out.splitlines()
                  if row.startswith("CLOSEOUT CHECK")]
    check_text = check_line[0] if check_line else ""
    files_hit = re.search(r"\bcorpus_files=(\d+)", check_text)
    mb_hit = re.search(r"\bcorpus_mb=(\d+(?:\.\d+)?)", check_text)
    a_ok = (code == 0 and "flags" in ms_tokens(check_text)
            and bool(files_hit) and int(files_hit.group(1)) > 0
            and bool(mb_hit) and float(mb_hit.group(1)) > 0.0)

    # b: a world that never asked the gate invents no readings.
    folder = world()
    try:
        ok_code, ok_out, _ = run_cli(
            ["--root", folder, "--round", str(ROUND),
             "--line", "2026-11-21 R%d PRODUCT: not-asked ledger" % ROUND,
             "--tick"])
        ok_line = [row for row in ok_out.splitlines()
                   if row.startswith("CLOSEOUT OK")]
        ok_text = ok_line[0] if ok_line else ""
        ok_bits = ms_tokens(ok_text)
        b_ok = (ok_code == 0 and "NOT-ASKED" in ok_text
                and "flags" not in ok_bits
                and "corpus_files=" not in ok_text
                and {"oneoff", "export", "walk"} <= set(ok_bits))
    finally:
        cleanup(folder)

    # c: the readings are DERIVED from the gate's verdict, never typed. The
    #    source is the evidence, because any hand-typed number passes arm a.
    src = read(MODULE)
    tree = ast.parse(src)
    helper = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_gate_bits":
            helper = node
    helper_src = ast.get_source_segment(src, helper) if helper else ""
    c_ok = (bool(helper) and '"face_ms"' in helper_src
            and '"corpus"' in helper_src and "def " in helper_src
            and '"flags_ms="' not in src
            and sum(1 for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "_gate_bits") >= 2)

    # d: the gate's published headline keeps its shipped token shape; the
    #    corpus rides in the verdict only, and its file count is the same
    #    number the headline publishes from the same scan.
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import closeout_gate as CG
    qa = os.path.join(ROOT, "qa")
    lines, gate_code, verdict = CG.evaluate(
        qa, os.path.join(qa, CG.CENSUS.BASELINE_NAME), root=ROOT)
    head = lines[0] if lines else ""
    head_files = re.search(r"\bfiles=(\d+)", head)
    corpus = verdict.get("corpus") or {}
    d_ok = (gate_code == 0 and "CLOSEOUT-GATE PASS" in head
            and "corpus" not in head and not re.search(r"[a-z_]+_ms=", head)
            and bool(head_files) and corpus.get("files") == int(head_files.group(1))
            and int(corpus.get("bytes") or 0) > 0)

    # e: the reading is not a verdict - byte volume moves, flags does not.
    import qa_writer_census as CENSUS
    small = tempfile.mkdtemp(prefix="cout17-")
    try:
        first = "qa=1 baseline=1 doc=1 missing=a\n"
        with open(os.path.join(small, "a.log"), "w", encoding="utf-8",
                  newline="\n") as handle:
            handle.write(first)
        base_path = os.path.join(small, CENSUS.BASELINE_NAME)
        _lines, write_code, _base = CENSUS.write_baseline(small, base_path)
        box1 = {}
        _l1, c1 = CENSUS.check_against_baseline(small, base_path, stats=box1)
        with open(os.path.join(small, "a.log"), "a", encoding="utf-8",
                  newline="\n") as handle:
            handle.write("extra healthy bytes on the same dialect\n" * 40)
        box2 = {}
        lines2, c2 = CENSUS.check_against_baseline(small, base_path, stats=box2)
        e_ok = (write_code == 0 and c1 == 0 and c2 == 0
                and box1.get("files") == 1 and box2.get("files") == 1
                and int(box2.get("bytes") or 0) > int(box1.get("bytes") or 0)
                and not any("corpus" in row for row in lines2))
        if not e_ok:
            print("  measured e=%r/%r bytes=%r/%r"
                  % (c1, c2, box1.get("bytes"), box2.get("bytes")), flush=True)
    finally:
        shutil.rmtree(small, ignore_errors=True)

    # f: R3126 - the published MB is DECIMAL and a corpus that could not read
    #    every candidate says so instead of describing itself as fully read.
    #    MEASURED before the pin (qa/probe-R3126.log): the live corpus is 4219
    #    entries / 508,066,256 bytes / zero unread, which is 508.1 MB under 1e6
    #    and 484.5 MiB under 1048576 - so the old number was a MiB count under
    #    an MB label and the "4.6% unread" reading was the unit, not a file.
    f_world = tempfile.mkdtemp(prefix="cout17f-")
    try:
        # a directory named *.log is unreadable on both Windows and POSIX
        os.makedirs(os.path.join(f_world, "klass.log"))
        with open(os.path.join(f_world, "big.log"), "wb") as handle:
            handle.write(b"a\n" * 1000000)      # exactly 2,000,000 bytes
        f_base = os.path.join(f_world, CENSUS.BASELINE_NAME)
        CENSUS.write_baseline(f_world, f_base)
        fbox = {}
        CENSUS.check_against_baseline(f_world, f_base, stats=fbox)
        f_line = CO._gate_bits({"face_ms": {}, "corpus": fbox})
        only = tempfile.mkdtemp(prefix="cout17g-")
        try:
            with open(os.path.join(only, "big.log"), "wb") as handle:
                handle.write(b"a\n" * 1000000)
            obase = os.path.join(only, CENSUS.BASELINE_NAME)
            CENSUS.write_baseline(only, obase)
            obox = {}
            CENSUS.check_against_baseline(only, obase, stats=obox)
            o_line = CO._gate_bits({"face_ms": {}, "corpus": obox})
        finally:
            shutil.rmtree(only, ignore_errors=True)
        f_ok = (fbox.get("files") == 2 and fbox.get("readable") == 1
                and int(fbox.get("bytes") or 0) == 2000000
                and "corpus_files=2" in f_line
                and "corpus_mb=2.0" in f_line      # MiB would print 1.9
                and "corpus_unread=1" in f_line
                and obox.get("files") == 1 and obox.get("readable") == 1
                and "corpus_mb=2.0" in o_line
                and "corpus_unread=" not in o_line)
        if not f_ok:
            print("  measured f=%r line=%r/%r" % (fbox, f_line, o_line),
                  flush=True)
    finally:
        shutil.rmtree(f_world, ignore_errors=True)

    # g: R3127 - the token has to answer "is the gate already covering this?".
    #    MEASURED before the pin (qa/probe-R3127.log): of 4222 shipped *.log
    #    only 2 carry a machine `corpus files=N readable=M bytes=B` line, zero
    #    of them diverge, the token appears in zero logs, and only 1 of 2307
    #    export-face revisions carries any corpus key - so the reading has
    #    never fired and is not on the published face. Driven against the
    #    SHIPPED census: an unbaselined unreadable candidate already reddens
    #    the flags face (new-dialect), and a name recorded in the baseline's
    #    other bucket that becomes unreadable is DRIFT-CLEAN - which is the
    #    one case only the token can witness.
    fresh_world = tempfile.mkdtemp(prefix="cout17j-")
    gone_world = tempfile.mkdtemp(prefix="cout17k-")
    try:
        os.makedirs(os.path.join(fresh_world, "klass.log"))
        with open(os.path.join(fresh_world, "ok.log"), "wb") as handle:
            handle.write(b"plain ascii\n")
        blank = dict((name, []) for name in CENSUS.BASELINE_CLASSES)
        fresh_base = os.path.join(tempfile.mkdtemp(prefix="cout17l-"),
                                  CENSUS.BASELINE_NAME)
        with open(fresh_base, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(blank, indent=1, sort_keys=True))
        nbox = {}
        nlines, ncode = CENSUS.check_against_baseline(fresh_world, fresh_base,
                                                      stats=nbox)
        n_line = CO._gate_bits({"face_ms": {}, "corpus": nbox})

        # a readable file that classifies as other (a utf-8 BOM lands there),
        # recorded by the shipped writer, then replaced by a directory of the
        # SAME name - the name never migrates, so no flag can see it
        with open(os.path.join(gone_world, "same.log"), "wb") as handle:
            handle.write(b"\xef\xbb\xbfplain ascii\n")
        with open(os.path.join(gone_world, "ok.log"), "wb") as handle:
            handle.write(b"plain ascii\n")
        gone_base = os.path.join(gone_world, CENSUS.BASELINE_NAME)
        _glines, gbcode, _gbase = CENSUS.write_baseline(gone_world, gone_base)
        with open(gone_base, "rb") as handle:
            recorded = json.loads(handle.read().decode("utf-8"))
        os.remove(os.path.join(gone_world, "same.log"))
        os.makedirs(os.path.join(gone_world, "same.log"))
        gbox = {}
        glines2, gcode = CENSUS.check_against_baseline(gone_world, gone_base,
                                                       stats=gbox)
        g_line = CO._gate_bits({"face_ms": {}, "corpus": gbox})
        g_ok = (gbcode == 0 and "same.log" in recorded.get("other", [])
                and ncode == 2
                and any("new-dialect" in row for row in nlines)
                and nbox.get("readable", 0) < nbox.get("files", 0)
                and "corpus_unread=1" in n_line
                and gcode == 0
                and not any(row.startswith("[flag]") for row in glines2)
                and gbox.get("files") == 2 and gbox.get("readable") == 1
                and "corpus_unread=1" in g_line)
        if not g_ok:
            print("  measured g fresh=%r/%r %r gone=%r/%r %r %r"
                  % (ncode, nbox, n_line, gcode, gbox, glines2[-2:], g_line),
                  flush=True)
    finally:
        shutil.rmtree(fresh_world, ignore_errors=True)
        shutil.rmtree(gone_world, ignore_errors=True)

    ok = a_ok and b_ok and c_ok and d_ok and e_ok and f_ok and g_ok
    if not ok:
        print("  measured: a=%r b=%r c=%r d=%r e=%r f=%r g=%r head=%r check=%r"
              % (a_ok, b_ok, c_ok, d_ok, e_ok, f_ok, g_ok, head[:120],
                 check_text[:200]), flush=True)
    check(ok, "AC-COUT17 the OK path prints the tree-gate ledger it paid for, "
          "the dry run publishes the corpus beside the milliseconds, a world "
          "that did not ask the gate prints no invented readings, the readings "
          "are derived from the gate's verdict rather than typed, the gate's "
          "published headline keeps its shipped shape, a byte change that "
          "moves the corpus does not move the verdict, and the published MB is "
          "decimal with unread candidates named only when they exist, and the "
          "one silent case is pinned: a new unreadable name already flags as "
          "new-dialect while a baselined other name that turns unreadable "
          "stays DRIFT-CLEAN and is witnessed by corpus_unread alone")


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
    ac_coutb1()
    ac_coutb2()
    ac_coutb3()
    ac_coutb4()
    ac_coutb5()
    ac_oosw1()
    ac_oosw2()
    ac_oosw3()
    ac_oosw4()
    ac_oosw5()
    ac_oosw6()
    ac_oosw7()
    ac_cout8()
    ac_cout9()
    ac_cout10()
    ac_cout11()
    ac_cout12()
    ac_cout13()
    ac_cout14()
    ac_cout15()
    ac_cout16()
    ac_cout17()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
