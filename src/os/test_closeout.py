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

EXPECTED_CRITERIA = 23
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
        face_at = source.find("ER.write(root, stamp)")
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
        e_ok = (live_word == "PASS" and "census=PASS" in live_line
                and not (live_verdict.get("detail") or [])
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
          "it without writing, the live tree stays PASS with no detail, and "
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
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
