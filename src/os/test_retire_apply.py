"""retire_apply suite (R2348; criteria AC-RAP1..AC-RAP6 were pre-registered
inside the R2333 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: an accepted retirement finally has an ACTING step, and the
step is a MOVE. The class and the live verdict are imported from retire_accept
and retire_candidate (patching either moves the verdict, and this module
carries no second declaration reader), the dry run is the default and proves
it moved nothing by a whole-tree digest, only an ACCEPTED entry is movable
while every other class refuses by class with the reason the acceptance reader
gave, an executed apply is one os.replace whose per-file digest map shows
exactly two changed paths with the destination bytes equal to the source
bytes, the CLI codes are pinned, and the module carries no delete path at all.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
import os
import re
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import retire_apply as AP  # noqa: E402
import retire_accept as RA  # noqa: E402
import retire_candidate as RC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "retire_apply.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-retire-apply"

EVIDENCE = "retire-apply-world-9001.log"

# One copy that performs the whole evidence ritual, so a fixture world can
# carry a REAL RETIRE-READY row: the CLI legs then read it through the live
# resolver instead of a patched one.
RITUAL = '''LEGS = 2
import hashlib
import subprocess
ADJACENT = "qa/retire-apply-world-9001.log"


def run_suite(path):
    return subprocess.run([path])


def emit(out, body):
    with open(out, "wb") as handle:
        handle.write(body.encode("utf-8"))
    line = "SUITE PASS"
    if line.startswith("SUITE"):
        print("LIVE reading")
    return "--check"


def check(line, body):
    for tag in ("a", "b"):
        if body.startswith("PASS"):
            pass
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    subprocess.run(["echo", digest])
    newline = "\\n"
    return digest
'''

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


def decl_text(entries, declared_by="R2333"):
    body = ",\n    ".join(json.dumps(entry, ensure_ascii=True,
                                     sort_keys=False) for entry in entries)
    if entries:
        return ('{\n  "declared_by": "%s",\n  "entries": [\n    %s\n  ]\n}\n'
                % (declared_by, body))
    return '{\n  "declared_by": "%s",\n  "entries": [\n  ]\n}\n' % (declared_by,)


def make_world(entries=None, tick=2347, scripts=None, ritual=False,
               extra=None):
    """A throwaway tree with a declaration, a state counter and real files."""
    root = tempfile.mkdtemp(prefix="retire-apply-")
    os.makedirs(os.path.join(root, "state", "queue"))
    os.makedirs(os.path.join(root, "src", "os"))
    for rel, body in (scripts or {}).items():
        path = os.path.join(root, *rel.split("/"))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "wb") as handle:
            handle.write(body.encode("utf-8"))
    for rel, body in (extra or {}).items():
        path = os.path.join(root, *rel.split("/"))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "wb") as handle:
            handle.write(body.encode("utf-8"))
    if ritual:
        with open(os.path.join(root, "src", "os", "evidence_R9001.py"), "wb") \
                as handle:
            handle.write(RITUAL.encode("utf-8"))
        os.makedirs(os.path.join(root, "qa"))
        with open(os.path.join(root, "qa", EVIDENCE), "wb") as handle:
            handle.write(b"evidence body\n")
    if entries is not None:
        with open(os.path.join(root, "state", "queue", "retire_accept.json"),
                  "wb") as handle:
            handle.write(decl_text(entries).encode("utf-8"))
    with open(os.path.join(root, "src", "os", "state.json"), "wb") as handle:
        handle.write(json.dumps({"tick": tick}).encode("utf-8"))
    return root


def entry(script="src/os/evidence_R9001.py", until="R2400", declared="R2333"):
    return {"script": script, "declared": declared,
            "reason": "superseded by evidence_capture", "until": until}


def ready_row(name):
    return {"script": name, "verdict": RC.READY, "reason": "", "detail": ""}


def owned_row(name, reason="PARITY-DEBT", detail="single-writer missing=x"):
    return {"script": name, "verdict": RC.OWNED, "reason": reason,
            "detail": detail}


def live(rows):
    return {"rows": rows, "scripts": len(rows), "retire_ready": len(rows),
            "owned": 0, "stale": 0, "parity_debt": 0, "collision": 0,
            "audit_verdict": "CLEAN", "map_verdict": "CLEAN",
            "parity_verdict": "ALL-PRESENT", "verdict": "CANDIDATES"}


class Patched(object):
    """Swap RC.resolve for the duration of one reading."""

    def __init__(self, report):
        self.report = report

    def __enter__(self):
        self.saved = RC.resolve
        RC.resolve = lambda *a, **k: self.report
        return self

    def __exit__(self, *exc):
        RC.resolve = self.saved
        return False


def run_cli(args, world=None):
    argv = [sys.executable, MODULE] + list(args)
    if world is not None:
        argv += ["--root", world]
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def file_map(root):
    """Relative path -> bytes, so 'every other file identical' is measurable."""
    out = {}
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(dirs)
        for name in sorted(names):
            path = os.path.join(folder, name)
            out[os.path.relpath(path, root).replace(os.sep, "/")] = \
                open(path, "rb").read()
    return out


def refuse(callable_, *args, **kwargs):
    """Run a refusing call and hand back its code, or None if it did not."""
    try:
        callable_(*args, **kwargs)
    except AP.RetireApplyError as exc:
        return exc.code
    except Exception as exc:  # noqa: BLE001 - a wrong error is not a refusal
        return "WRONG:" + type(exc).__name__
    return None


def ac_rap1():
    """The class and the live verdict are imported, never re-derived."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_second_reader = ("retire_accept.json" not in source
                       and "DECL_REL" not in source
                       and "json.loads" not in source
                       and "import retire_candidate" not in source
                       and "import evidence_output" not in source
                       and "import retire_accept" in source)
    world = make_world([entry()], scripts={"src/os/evidence_R9001.py": "x = 1\n"})
    with Patched(live([ready_row("src/os/evidence_R9001.py")])):
        planned = AP.plan(world, "src/os/evidence_R9001.py")
        stale = refuse(AP.plan, world, "src/os/evidence_R9001.py")
        with Patched(live([owned_row("src/os/evidence_R9001.py")])):
            stale = refuse(AP.plan, world, "src/os/evidence_R9001.py")
    # patching retire_accept itself moves the verdict too
    saved = RA.check
    RA.check = lambda root, rnd=None: {"round": "R2348", "rows": [
        {"script": "src/os/evidence_R9001.py", "class": RA.EXPIRED,
         "until": "R2348", "detail": "until R2348", "live_verdict": RC.READY}]}
    try:
        patched = refuse(AP.plan, world, "src/os/evidence_R9001.py")
    finally:
        RA.check = saved
    check(no_second_reader
          and planned["verdict"] == AP.PLANNED
          and planned["class"] == RA.ACCEPTED
          and stale == "E_RAP_CLASS_STALE_DECISION"
          and patched == "E_RAP_CLASS_EXPIRED", "AC-RAP1 imports")


def ac_rap2():
    """The dry run is the default and moves nothing, proved by a digest."""
    body = "print('hello')\n"
    world = make_world([entry()], scripts={"src/os/evidence_R9001.py": body},
                       extra={"qa/keep.log": "keep\n"})
    before = AP.tree_digest(world)
    with Patched(live([ready_row("src/os/evidence_R9001.py")])):
        result = AP.plan(world, "evidence_R9001.py")
    after = AP.tree_digest(world)
    dest = os.path.join(world, "media", "quarantine", "R2348",
                        "evidence_R9001.py")
    check(result["wrote"] is False
          and result["read_back_ok"] is False
          and result["verdict"] == AP.PLANNED
          and result["source"] == "src/os/evidence_R9001.py"
          and result["destination"] == "media/quarantine/R2348/evidence_R9001.py"
          and result["class"] == RA.ACCEPTED
          and result["predicted_bytes"] == len(body.encode("utf-8"))
          and not os.path.exists(dest)
          and before == after == result["digest_after"],
          "AC-RAP2 dry run")


def ac_rap3():
    """Only ACCEPTED moves; every other class refuses by class, nothing moves."""
    body = "x = 1\n"
    cases = []
    # EXPIRED: until earlier than the live round
    world = make_world([entry(until="R2300")],
                       scripts={"src/os/evidence_R9001.py": body})
    with Patched(live([ready_row("src/os/evidence_R9001.py")])):
        cases.append(("expired", refuse(AP.plan, world, "src/os/evidence_R9001.py"),
                      AP.tree_digest(world)))
    # UNMATCHED: the live resolver has no row at all
    world = make_world([entry()], scripts={"src/os/evidence_R9001.py": body})
    with Patched(live([])):
        cases.append(("unmatched",
                      refuse(AP.plan, world, "src/os/evidence_R9001.py"),
                      AP.tree_digest(world)))
    # STALE-DECISION: the script reads owned again
    world = make_world([entry()], scripts={"src/os/evidence_R9001.py": body})
    with Patched(live([owned_row("src/os/evidence_R9001.py")])):
        cases.append(("stale", refuse(AP.plan, world, "src/os/evidence_R9001.py"),
                      AP.tree_digest(world)))
    # NOT-DECLARED: the declaration never mentions it
    world = make_world([], scripts={"src/os/evidence_R9001.py": body})
    with Patched(live([ready_row("src/os/evidence_R9001.py")])):
        cases.append(("undeclared",
                      refuse(AP.plan, world, "src/os/evidence_R9001.py"),
                      AP.tree_digest(world)))
    # NO-SOURCE: accepted, but the file is not on disk
    world = make_world([entry()], scripts={})
    with Patched(live([ready_row("src/os/evidence_R9001.py")])):
        cases.append(("nosource", refuse(AP.plan, world, "src/os/evidence_R9001.py"),
                      AP.tree_digest(world)))
    # DEST-EXISTS: an earlier copy already sits in the quarantine path
    world = make_world([entry()],
                       scripts={"src/os/evidence_R9001.py": body},
                       extra={"media/quarantine/R2348/evidence_R9001.py":
                              "earlier\n"})
    with Patched(live([ready_row("src/os/evidence_R9001.py")])):
        cases.append(("dest", refuse(AP.plan, world, "src/os/evidence_R9001.py"),
                      AP.tree_digest(world)))
    codes = dict((name, code) for name, code, _ in cases)
    ok = (codes["expired"] == "E_RAP_CLASS_EXPIRED"
          and codes["unmatched"] == "E_RAP_CLASS_UNMATCHED"
          and codes["stale"] == "E_RAP_CLASS_STALE_DECISION"
          and codes["undeclared"] == "E_RAP_NOT_DECLARED"
          and codes["nosource"] == "E_RAP_NO_SOURCE"
          and codes["dest"] == "E_RAP_DEST_EXISTS")
    # the refusal reason is the acceptance reader's own text, not a paraphrase
    world = make_world([entry(until="R2300")],
                       scripts={"src/os/evidence_R9001.py": body})
    reason = ""
    with Patched(live([ready_row("src/os/evidence_R9001.py")])):
        try:
            AP.plan(world, "src/os/evidence_R9001.py")
        except AP.RetireApplyError as exc:
            reason = exc.detail
    check(ok and "until R2300" in reason, "AC-RAP3 only ACCEPTED moves")


def ac_rap4():
    """An executed apply is one move: two paths change, bytes are proved."""
    body = "print('move me')\n"
    world = make_world([entry()],
                       scripts={"src/os/evidence_R9001.py": body,
                                "src/os/other.py": "y = 2\n"},
                       extra={"qa/keep.log": "keep\n"})
    before = file_map(world)
    with Patched(live([ready_row("src/os/evidence_R9001.py")])):
        result = AP.plan(world, "src/os/evidence_R9001.py", execute=True)
    after = file_map(world)
    gone = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    shared = [rel for rel in set(before) & set(after) if before[rel] != after[rel]]
    leftover = sorted(rel for rel in after if ".tmp" in rel or rel.endswith(".part"))
    check(result["verdict"] == AP.APPLIED
          and result["wrote"] is True
          and result["read_back_ok"] is True
          and gone == ["src/os/evidence_R9001.py"]
          and added == ["media/quarantine/R2348/evidence_R9001.py"]
          and after["media/quarantine/R2348/evidence_R9001.py"] == \
          body.encode("utf-8")
          and not shared
          and not leftover
          and result["digest_after"] != result["digest_before"],
          "AC-RAP4 executed move")


def ac_rap5():
    """CLI codes are pinned and --json is byte-stable across two runs."""
    code5, out5, err5 = run_cli(["--nope"])
    code0_list, out_list, _ = run_cli(["--list"], world=make_world(entries=[],
                                                                 ritual=True))
    world = make_world([entry()], ritual=True)
    code0_plan, out_plan, _ = run_cli(
        ["--script", "src/os/evidence_R9001.py", "--json"], world=world)
    again, out_again, _ = run_cli(
        ["--script", "src/os/evidence_R9001.py", "--json"], world=world)
    body = json.loads(out_plan) if out_plan.strip() else {}
    code0_exec, out_exec, _ = run_cli(
        ["--script", "src/os/evidence_R9001.py", "--execute"], world=world)
    expired = make_world([entry(until="R2300")], ritual=True)
    code2, out2, err2 = run_cli(["--script", "src/os/evidence_R9001.py"],
                                world=expired)
    bare = tempfile.mkdtemp(prefix="retire-apply-bare-")
    code3, out3, err3 = run_cli(["--script", "src/os/evidence_R9001.py"],
                                world=bare)
    check(code5 == 5 and "E_RAP_BAD_ARGS" in err5
          and code0_list == 0 and "LISTED" in out_list
          and code0_plan == 0 and body.get("verdict") == AP.PLANNED
          and body.get("wrote") is False
          and again == 0 and out_again == out_plan
          and code0_exec == 0 and "APPLIED" in out_exec
          and code2 == 2 and "E_RAP_CLASS_EXPIRED" in err2
          and code3 == 3 and "E_RAP_NO_INPUT" in err3,
          "AC-RAP5 CLI codes")


def code_only(text):
    """The source with comments and docstrings removed.

    A docstring that NAMES a forbidden call is not a call: this module's own
    header says it contains no delete path, and a scan that reads prose as
    code would fail on the sentence that documents the promise (the R2346
    AC-SEG6 lesson). The assertion therefore reads executable text only.
    """
    without_docstrings = re.sub(r'"""(?:.|\n)*?"""', '', text)
    without_docstrings = re.sub(r"'''(?:.|\n)*?'''", '', without_docstrings)
    return re.sub(r"#[^\n]*", "", without_docstrings)


def ac_rap6():
    """Pure ASCII, stdlib only, no clock, no network, and NO delete path."""
    raw = io.open(MODULE, "rb").read()
    try:
        text = raw.decode("ascii")
        ascii_ok = True
    except (UnicodeDecodeError, ValueError):
        text = raw.decode("utf-8", "replace")
        ascii_ok = False
    code = code_only(text)
    imports = set(re.findall(r"^import (\w+)", code, re.M))
    forbidden = ("os.remove", "unlink", "rmtree", "socket", "urllib",
                 "http.client", "requests", "import time", "datetime",
                 "time.time")
    clean = [token for token in forbidden if token in code]
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('("%s"' % LABEL) in runner and "test_retire_apply.py" in runner
    check(ascii_ok
          and imports <= {"hashlib", "io", "json", "os", "sys",
                          "retire_accept"}
          and not clean
          and wired,
          "AC-RAP6 purity and wiring")


def main():
    for name in ("ac_rap1", "ac_rap2", "ac_rap3", "ac_rap4", "ac_rap5",
                 "ac_rap6"):
        globals()[name]()
    total = PASSES + FAILS
    verdict = "PASS" if FAILS == 0 and total == EXPECTED_CRITERIA else "FAIL"
    print("SUITE %s %d/%d" % (verdict, PASSES, total))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())