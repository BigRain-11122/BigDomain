"""Acceptance suite for repin_noop_eol_dialect (AC-RNED1..AC-RNED6).

Criteria were pinned inside the R2382 seed row of state/queue/tech.md BEFORE
this code existed. One criterion per subject, measured on throwaway worlds:

  AC-RNED1 a CRLF declaration carrying the composition reads NOOP, writes no
           byte and creates no temp;
  AC-RNED2 an LF declaration keeps today's readings (PLANNED/PINNED/NOOP) and
           the written bytes are the composition itself;
  AC-RNED3 a declaration that differs in CONTENT still reads PLANNED and is
           still rewritten;
  AC-RNED4 the shipped CLI and the wire agree over the CRLF declaration and
           neither reports a write;
  AC-RNED5 the normalisation lives in ONE place and a patched normaliser moves
           both faces;
  AC-RNED6 pure ASCII stdlib, no clock, no network, and its own reconcile
           label wired into the runner.
"""

import ast
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import repin_noop_eol_dialect as RNED  # noqa: E402
import repin_noop_parity as RNP  # noqa: E402
import residue_triage as RT  # noqa: E402
import residue_triage_repin as RTR  # noqa: E402
import residue_triage_repin_idempotent as RI  # noqa: E402

MODULE = os.path.join(BASE, "repin_noop_eol_dialect.py")
SHIPPED = os.path.join(BASE, "residue_triage_repin.py")
WIRE = os.path.join(BASE, "residue_triage_repin_idempotent.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-repin-noop-eol-dialect"
WIRED_EXPECT = '"test_repin_noop_eol_dialect.py"), 6),'

PIN_ROUND = "R2360"
PIN_UNTIL = "R2380"
PIN_REASON = "re-pinned at R2360 from one live reading"
HEADER = "# queue test world\n\nprose that never becomes a row\n\n"

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


def tech_rows(rounds=("R2300", "R2305", "R2348")):
    out = []
    for number in rounds:
        out.append("- [x] [done 2026-11-01 %s] a closed residue row\n"
                   % number)
    return "".join(out)


def seeded_declaration():
    rows = []
    for number, until in ((2300, 2350), (2305, 2350), (2348, 2360)):
        rows.append({
            "round": number,
            "status": "DELIVERED",
            "declared_by": 2331,
            "reason": "reviewed at R2331 at its live status",
            "until": until,
        })
    return {"declared_by": 2331, "reason": "reviewed at R2331",
            "entries": rows}


def make_world(no_decl=False, raw=None, rounds=("R2300", "R2305", "R2348")):
    world = tempfile.mkdtemp(prefix="rned-world-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    payload = {"tick": 2300, "log": ["R2200 a logged item"]}
    path = os.path.join(world, "src", "os", "state.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload))
    tech = tech_rows(rounds)
    for name, body in (("tech", tech), ("main", HEADER), ("explore", HEADER)):
        path = os.path.join(world, "state", "queue", name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    if no_decl:
        return world
    path = os.path.join(world, RT.DECLARATION_PATH)
    if raw is not None:
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(raw)
        return world
    body = json.dumps(seeded_declaration(), ensure_ascii=True, indent=2)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body + "\n")
    return world


def declaration_path(world):
    return os.path.join(world, RT.DECLARATION_PATH)


def digest_file(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def file_map(root):
    out = {}
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(dirs)
        for name in sorted(names):
            path = os.path.join(folder, name)
            out[os.path.relpath(path, root).replace(os.sep, "/")] = \
                open(path, "rb").read()
    return out


def run_cli(module, world, args, cli_flags=("--root",)):
    argv = [sys.executable, module] + list(cli_flags) + [world] + list(args)
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def pin(world, execute=True):
    """Fill the declaration through the SHIPPED writer, never by hand."""
    return RTR.plan(world, PIN_ROUND, PIN_UNTIL, PIN_REASON, False, execute)


def to_crlf(path):
    """Rewrite the file with CRLF endings, content otherwise identical."""
    with io.open(path, "rb") as handle:
        data = handle.read()
    with io.open(path, "wb") as handle:
        handle.write(data.replace(b"\n", b"\r\n"))


def code_only(text):
    body = re.sub(r'"""(?:.|\n)*?"""', '', text)
    body = re.sub(r"'''(?:.|\n)*?'''", '', body)
    return re.sub(r"#[^\n]*", "", body)


def ac_rned1():
    """A CRLF declaration carrying the composition reads NOOP, writes none."""
    world = make_world()
    try:
        first = pin(world)
        path = declaration_path(world)
        to_crlf(path)
        before_digest = digest_file(path)
        before_map = file_map(world)
        before_dialect = RNED.dialect_of(RNED.read_bytes(path))

        report = pin(world)
        after_map = file_map(world)
        temps = [name for name in after_map
                 if name.endswith(".tmp") or RTR.TEMP_SUFFIX in name]
        code, out, _ = run_cli(SHIPPED, world, [
            "--round", PIN_ROUND, "--until", PIN_UNTIL,
            "--reason", PIN_REASON, "--execute"])
        code_j, out_j, _ = run_cli(SHIPPED, world, [
            "--round", PIN_ROUND, "--until", PIN_UNTIL,
            "--reason", PIN_REASON, "--execute", "--json"])
        payload = json.loads(out_j) if out_j.strip() else {}
        ok = (first["verdict"] == "PINNED"
              and before_dialect == "CRLF"
              and report["verdict"] == "NOOP"
              and report["executed"] is False
              and digest_file(path) == before_digest
              and before_map == after_map
              and temps == []
              and RNED.dialect_of(RNED.read_bytes(path)) == "CRLF"
              and code == 0 and "NOOP" in out
              and code_j == 0 and payload.get("verdict") == "NOOP"
              and payload.get("executed") is False)
        if not ok:
            print("  measured: dialect=%r verdict=%r executed=%r "
                  "digest_same=%r temps=%r rc=%r out=%r"
                  % (before_dialect, report.get("verdict"),
                     report.get("executed"),
                     digest_file(path) == before_digest, temps, code,
                     out.strip()), flush=True)
        check(ok, "AC-RNED1 a CRLF declaration whose content equals the "
                  "composition reads NOOP on the module and on the shipped "
                  "CLI, writes no byte, creates no temp and keeps its CRLF "
                  "dialect")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rned2():
    """An LF declaration keeps today's readings and bytes."""
    world = make_world()
    try:
        dry = pin(world, execute=False)
        path = declaration_path(world)
        before = RNED.read_bytes(path)
        composed = dry["_text"].encode("utf-8")
        pinned = pin(world)
        after = RNED.read_bytes(path)
        second = pin(world)
        ok = (dry["verdict"] == "PLANNED" and dry["executed"] is False
              and dry["predicted_bytes"] == len(composed)
              and RNED.normalise_bytes(composed) == composed
              and RNED.dialect_of(composed) == "LF"
              and pinned["verdict"] == "PINNED" and pinned["executed"] is True
              and after == composed
              and b"\r" not in after
              and len(after) == pinned["predicted_bytes"]
              and second["verdict"] == "NOOP"
              and second["executed"] is False)
        if not ok:
            print("  measured: dry=%r/%r pinned=%r after_eq=%r cr=%r "
                  "len=%r/%r second=%r"
                  % (dry.get("verdict"), dry.get("executed"),
                     pinned.get("verdict"), after == composed,
                     b"\r" in after, len(after),
                     pinned.get("predicted_bytes"),
                     second.get("verdict")), flush=True)
        check(ok, "AC-RNED2 an LF declaration keeps today's readings "
                  "(PLANNED, PINNED, NOOP) and the written file is the "
                  "composition itself, LF only, at the predicted size")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rned3():
    """A content difference still reads PLANNED and is still rewritten."""
    world = make_world()
    try:
        pin(world)
        path = declaration_path(world)
        before_digest = digest_file(path)
        new_reason = "re-pinned at R2360 after a content-only change"
        report = RTR.plan(world, PIN_ROUND, PIN_UNTIL, new_reason,
                          False, False)
        measurement = RNED.compare(path, report["_text"])
        executed = RTR.plan(world, PIN_ROUND, PIN_UNTIL, new_reason,
                            False, True)
        after_digest = digest_file(path)
        after = RNED.read_bytes(path)
        ok = (report["verdict"] == "PLANNED"
              and report["executed"] is False
              and measurement["verdict"] == "PLANNED"
              and measurement["raw_equal"] is False
              and executed["verdict"] == "PINNED"
              and executed["executed"] is True
              and after_digest != before_digest
              and after == executed["_text"].encode("utf-8")
              and RNED.dialect_of(after) == "LF")
        if not ok:
            print("  measured: dry=%r compare=%r raw_equal=%r exec=%r "
                  "digest_changed=%r same=%r"
                  % (report.get("verdict"), measurement.get("verdict"),
                     measurement.get("raw_equal"), executed.get("verdict"),
                     after_digest != before_digest,
                     after == executed.get("_text", "").encode("utf-8")),
                  flush=True)
        check(ok, "AC-RNED3 a declaration that differs in CONTENT still "
                  "reads PLANNED, still rewrites, and ends on the new "
                  "composition - the normalisation is content-safe")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rned4():
    """The shipped CLI and the wire agree over the CRLF declaration."""
    world = make_world()
    try:
        pin(world)
        path = declaration_path(world)
        to_crlf(path)
        before_digest = digest_file(path)
        before_map = file_map(world)
        report = RNP.check(world, PIN_ROUND, PIN_UNTIL, PIN_REASON)
        after_map = file_map(world)
        temps = [name for name in after_map
                 if name.endswith(".tmp") or RTR.TEMP_SUFFIX in name]
        ok = (report["verdict"] == "AGREES"
              and report["shipped"] == "NOOP"
              and report["wire"] == "NOOP"
              and report["first_diff"] is None
              and report["shipped_code"] is None
              and report["wire_code"] is None
              and digest_file(path) == before_digest
              and before_map == after_map
              and temps == [])
        if not ok:
            print("  measured: %r" % (report,), flush=True)
        check(ok, "AC-RNED4 the parity reads AGREES over the CRLF "
                  "declaration with both faces on NOOP, no refusal code, "
                  "and neither reports a write")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rned5():
    """One normalisation, and a patched normaliser moves both faces."""
    world = make_world()
    saved = RNED.normalise_bytes
    try:
        pin(world)
        path = declaration_path(world)
        to_crlf(path)
        shipped_before = RTR.plan(world, PIN_ROUND, PIN_UNTIL, PIN_REASON)
        wire_before = RI.decide(world, PIN_ROUND, PIN_UNTIL, PIN_REASON)

        definitions = 0
        for name in sorted(os.listdir(BASE)):
            if not name.endswith(".py") or name.startswith("test_"):
                continue
            with io.open(os.path.join(BASE, name), encoding="utf-8") as f:
                text = f.read()
            # Count real DEFINITIONS, not prose: a one-off round script that
            # quotes the name inside a string must not read as a second law.
            # Re-anchored at R2389 after closeout_R2388.py was measured doing
            # exactly that; the criterion's intent - exactly one owner - is
            # unchanged and is now measured on the AST.
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) \
                        and node.name == "normalise_bytes":
                    definitions += 1

        RNED.normalise_bytes = lambda data: data
        try:
            shipped_after = RTR.plan(world, PIN_ROUND, PIN_UNTIL, PIN_REASON)
            wire_after = RI.decide(world, PIN_ROUND, PIN_UNTIL, PIN_REASON)
        finally:
            RNED.normalise_bytes = saved

        ok = (shipped_before["verdict"] == "NOOP"
              and wire_before["verdict"] == "NOOP"
              and shipped_after["verdict"] == "PLANNED"
              and wire_after["verdict"] == "PLANNED"
              and definitions == 1)
        if not ok:
            print("  measured: before=%r/%r after=%r/%r defs=%r"
                  % (shipped_before.get("verdict"), wire_before.get("verdict"),
                     shipped_after.get("verdict"), wire_after.get("verdict"),
                     definitions), flush=True)
        check(ok, "AC-RNED5 the normalisation is defined exactly once under "
                  "src/os and replacing it moves BOTH the shipped reader and "
                  "the wire from NOOP to PLANNED on the same CRLF world")
    finally:
        RNED.normalise_bytes = saved
        shutil.rmtree(world, ignore_errors=True)


def ac_rned6():
    """Pure ASCII stdlib, no clock, no network, own reconcile label."""
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    text = raw.decode("ascii")
    tree = ast.parse(text)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    body = code_only(text)
    with io.open(RUNNER, encoding="utf-8") as handle:
        runner = handle.read()
    ok = (all(byte < 128 for byte in raw)
          and imported <= {"json", "os", "sys"}
          and "socket" not in body and "urllib" not in body
          and "requests" not in body and "http" not in body
          and "time." not in body and "datetime" not in body
          and "def normalise_bytes" in body
          and WIRED_EXPECT in runner
          and ('"%s"' % LABEL) in runner)
    if not ok:
        print("  measured: ascii=%r imports=%r wired=%r label=%r"
              % (all(byte < 128 for byte in raw), sorted(imported),
                 WIRED_EXPECT in runner, ('"%s"' % LABEL) in runner),
              flush=True)
    check(ok, "AC-RNED6 the module is pure ASCII stdlib with no clock and no "
              "network, defines the one normalisation, and carries its own "
              "reconcile label wired into the runner")


def main():
    ac_rned1()
    ac_rned2()
    ac_rned3()
    ac_rned4()
    ac_rned5()
    ac_rned6()
    print("SUMMARY passes=%d fails=%d" % (PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())