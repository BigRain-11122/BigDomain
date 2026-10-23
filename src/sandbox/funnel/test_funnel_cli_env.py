"""Acceptance suite for the funnel CLI external-environment
independence window (FUNNEL-LOOP v0.1, R2064).

Pre-registered criteria AC-FCW1..AC-FCW8 live in state/queue/tech.md
(the R2064 claim row) and were written BEFORE this suite or the
default_paths() product face existed (honesty law). The gap under
test is the one the R2056 reseed row named: the CLI carried its
default carrier as inline string joins inside main(), so nothing
pinned that (a) the defaults follow the module and not the caller's
working directory, and (b) an ambient PYTHONIOENCODING=cp936 shell
still yields the same ASCII stdout and evidence bytes.

The law now under test: default_paths() is the single module-anchored
source for all carrier defaults (pure read, zero disk artifacts), so a
run from any cwd lands on the same repo-root state/funnel carrier and
produces byte-identical stdout/evidence; explicitly passed paths stay
the caller's own (cwd-relative strings are honoured as given).

The CLI is exercised as a real subprocess (that is the whole point:
cwd and environment are process-level facts). Pure ASCII source.
"""

import ast
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(BASE, "funnel_daily.py")
REPO = os.path.normpath(os.path.join(BASE, "..", "..", ".."))
DAY = "2026-10-24"

sys.path.insert(0, BASE)

import funnel_daily as fd  # noqa: E402


def _env(extra=None):
    env = os.environ.copy()
    for key in ("PYTHONIOENCODING", "PYTHONUTF8", "PYTHONLEGACYWINDOWSSTDIO"):
        env.pop(key, None)
    if extra:
        env.update(extra)
    return env


def _world(root, seed=True):
    paths = {
        "root": root,
        "db": os.path.join(root, "carrier", "funnel.db"),
        "leads": os.path.join(root, "inbox", "leads"),
        "orders": os.path.join(root, "inbox", "orders"),
        "flows": os.path.join(root, "inbox", "flows"),
        "evidence": os.path.join(root, "ev", "evidence.log"),
    }
    for d in (paths["leads"], paths["orders"], paths["flows"]):
        os.makedirs(d, exist_ok=True)
    if seed:
        _put(paths["leads"], [{"lead_id": "L1", "source": "s",
                               "text": "game demo level request"}])
        _put(paths["orders"], [{"order_id": "O1", "sku": "pack-19.9",
                                "amount_cent": 1990}])
        _put(paths["flows"], [
            {"flow_id": "F1", "account": "u1", "kind": "grant",
             "amount": 100},
            {"flow_id": "F2", "account": "u1", "kind": "spend",
             "amount": 30},
        ])
    return paths


def _put(d, rows):
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)


def _argv(w, evidence=True, config=None):
    argv = ["--day", DAY, "--db", w["db"],
            "--leads-inbox", w["leads"],
            "--orders-inbox", w["orders"],
            "--flows-inbox", w["flows"],
            "--config", config or fd.DEFAULT_CONFIG]
    if evidence:
        argv += ["--evidence", w["evidence"]]
    return argv


def _run(argv, cwd, extra_env=None):
    proc = subprocess.run(
        [sys.executable, SCRIPT] + list(argv),
        cwd=cwd, env=_env(extra_env), capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr


def _tmpdir(tmp, name):
    root = os.path.join(tmp, name)
    os.makedirs(root)
    return root


def _bytes(path):
    with open(path, "rb") as h:
        return h.read()


def case_fcw1(tmp):
    """AC-FCW1: default_paths() is module-anchored - two different
    cwds derive identical absolute keys, all under the repo root, none
    under the foreign cwd."""
    code = ("import sys,json;sys.path.insert(0, %r);"
            "import funnel_daily as fd;"
            "print(json.dumps(fd.default_paths(), sort_keys=True))" % BASE)
    foreign = _tmpdir(tmp, "fcw1-foreign")
    out_a = subprocess.run([sys.executable, "-c", code], cwd=foreign,
                           env=_env(), capture_output=True)
    out_b = subprocess.run([sys.executable, "-c", code], cwd=REPO,
                           env=_env(), capture_output=True)
    assert out_a.returncode == 0 and out_b.returncode == 0, (
        "AC-FCW1 derivation must run cleanly")
    assert out_a.stdout == out_b.stdout, (
        "AC-FCW1 two cwds must derive identical defaults")
    data = json.loads(out_a.stdout.decode("utf-8"))
    assert data["config"] == fd.DEFAULT_CONFIG, "AC-FCW1 config anchor"
    for key in ("db", "leads_inbox", "orders_inbox", "flows_inbox",
                "state_face", "base"):
        value = data[key]
        assert os.path.isabs(value), (
            "AC-FCW1 %s must be absolute (%r)" % (key, value))
        assert os.path.normpath(value).startswith(REPO + os.sep), (
            "AC-FCW1 %s must sit under the repo root (%r)" % (key, value))
        assert not os.path.normpath(value).startswith(foreign + os.sep), (
            "AC-FCW1 %s must never follow the cwd (%r)" % (key, value))


def case_fcw2(tmp):
    """AC-FCW2: a full run is byte-identical from a foreign cwd and
    from the repo root (stdout, evidence bytes and exit code)."""
    foreign = _tmpdir(tmp, "fcw2-foreign")
    root = _tmpdir(tmp, "fcw2-world")
    w = _world(root)
    rc_a, out_a, err_a = _run(_argv(w), foreign)
    ev_a = _bytes(w["evidence"])
    os.remove(w["db"])
    for d in (w["leads"], w["orders"], w["flows"]):
        for name in os.listdir(d):
            os.remove(os.path.join(d, name))
    _world(root)
    rc_b, out_b, err_b = _run(_argv(w), REPO)
    assert rc_a == 0 and rc_b == 0, (
        "AC-FCW2 both runs exit 0 (%r/%r) %r" % (rc_a, rc_b, err_a))
    assert out_a == out_b, "AC-FCW2 stdout must be cwd-independent"
    # Delivery-time criterion repair: the child's stdout is text-mode on
    # Windows (print() emits CRLF), while the self-tee evidence file is
    # opened with newline="\n" by design. The law is content identity, so
    # the stdout line endings are normalised to LF before the comparison.
    assert ev_a == out_a.replace(b"\r\n", b"\n"), (
        "AC-FCW2 evidence self-tee from foreign cwd")
    assert _bytes(w["evidence"]) == out_b.replace(b"\r\n", b"\n"), (
        "AC-FCW2 evidence bytes must be cwd-independent")


def case_fcw3(tmp):
    """AC-FCW3: an ambient cp936 stdout encoding (PYTHONUTF8=0) does
    not change a single byte - the face is pure ASCII by construction."""
    foreign = _tmpdir(tmp, "fcw3-foreign")
    root = _tmpdir(tmp, "fcw3-world")
    w = _world(root)
    rc_a, out_a, _ = _run(_argv(w), foreign)
    ev_a = _bytes(w["evidence"])
    os.remove(w["db"])
    for d in (w["leads"], w["orders"], w["flows"]):
        for name in os.listdir(d):
            os.remove(os.path.join(d, name))
    _world(root)
    rc_b, out_b, err_b = _run(
        _argv(w), foreign,
        {"PYTHONIOENCODING": "cp936", "PYTHONUTF8": "0"})
    assert rc_a == 0 and rc_b == 0, (
        "AC-FCW3 cp936 run must stay green (%r/%r) %r" % (rc_a, rc_b,
                                                          err_b))
    assert out_b and all(b < 128 for b in out_b), (
        "AC-FCW3 cp936 stdout must be pure ASCII")
    assert out_a == out_b, (
        "AC-FCW3 ambient encoding must not change the stdout bytes")
    assert _bytes(w["evidence"]) == ev_a, (
        "AC-FCW3 ambient encoding must not change the evidence bytes")


def case_fcw4(tmp):
    """AC-FCW4: the default --config comes from the module, never the
    cwd; the state face is the repo-root one."""
    defaults = fd.default_paths()
    assert defaults["config"] == fd.DEFAULT_CONFIG, "AC-FCW4 config"
    assert os.path.dirname(defaults["db"]) == defaults["state_face"], (
        "AC-FCW4 db lives on the state face")
    assert defaults["state_face"] == os.path.join(REPO, "state", "funnel"), (
        "AC-FCW4 state face is repo-anchored")
    assert os.path.basename(defaults["db"]) == "funnel.db", (
        "AC-FCW4 carrier name is pinned")


def case_fcw5(tmp):
    """AC-FCW5: explicit relative paths stay cwd-relative (the second
    law) - the caller owns explicitly passed paths."""
    foreign = _tmpdir(tmp, "fcw5-foreign")
    rc, out, err = _run(
        ["--day", DAY, "--db", "rel/carrier.db",
         "--leads-inbox", "rel/leads", "--orders-inbox", "rel/orders",
         "--flows-inbox", "rel/flows",
         "--config", fd.DEFAULT_CONFIG,
         "--evidence", "rel/ev.log"], foreign)
    assert rc == 0, "AC-FCW5 relative explicit run exit 0 (%r) %r" % (
        rc, err)
    for rel in ("rel/carrier.db", "rel/leads", "rel/orders", "rel/flows",
                "rel/ev.log"):
        assert os.path.exists(os.path.join(foreign, rel)), (
            "AC-FCW5 %s must land under the caller cwd" % rel)


def case_fcw6(tmp):
    """AC-FCW6: default_paths() is a pure read - its body contains no
    creating call and a call leaves the state face untouched."""
    tree = ast.parse(open(SCRIPT, encoding="utf-8").read())
    fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "default_paths":
            fn = node
            break
    assert fn is not None, "AC-FCW6 default_paths must exist"
    forbidden = {"makedirs", "mkdir", "open", "touch", "write", "write_text",
                 "connect"}
    seen = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            seen.add(node.func.attr)
    assert not (seen & forbidden), (
        "AC-FCW6 default_paths must not create anything: %r"
        % (seen & forbidden))
    before = sorted(os.listdir(os.path.join(REPO, "state", "funnel")))
    fd.default_paths()
    after = sorted(os.listdir(os.path.join(REPO, "state", "funnel")))
    assert before == after, "AC-FCW6 no disk artifact may appear"


def case_fcw7(tmp):
    """AC-FCW7: hygiene - pure ASCII source, no network import line,
    shipped config untouched."""
    raw = _bytes(SCRIPT)
    assert all(b < 128 for b in raw), "AC-FCW7 source must stay ASCII"
    tree = ast.parse(raw.decode("ascii"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    banned = {"urllib", "requests", "socket", "http", "ftplib", "smtplib",
              "asyncio", "ssl"}
    assert not (names & banned), (
        "AC-FCW7 no network import may exist: %r" % (names & banned))
    cfg = _bytes(fd.DEFAULT_CONFIG)
    root = _tmpdir(tmp, "fcw7-world")
    w = _world(root)
    rc, _out, _err = _run(_argv(w), root)
    assert rc == 0, "AC-FCW7 run must exit 0"
    assert _bytes(fd.DEFAULT_CONFIG) == cfg, (
        "AC-FCW7 shipped config bytes must not change")


def case_fcw8(tmp):
    """AC-FCW8: the gate law is environment-independent - a PASS world
    exits 0, an injected banned word (flat) fails the zero-activity
    day closed with exit 2 and identical bytes under cp936."""
    root = _tmpdir(tmp, "fcw8-world")
    w = _world(root)
    rc_ok, out_ok, err_ok = _run(_argv(w), root)
    assert rc_ok == 0, "AC-FCW8 PASS world exit 0 (%r) %r" % (rc_ok, err_ok)
    assert b"gate=PASS" in out_ok, "AC-FCW8 PASS gate line"

    cfg = json.load(open(fd.DEFAULT_CONFIG, encoding="utf-8"))
    cfg["banned_words"] = list(cfg["banned_words"]) + ["flat"]
    bad_cfg = os.path.join(root, "cfg-bad.json")
    with open(bad_cfg, "w", encoding="utf-8") as h:
        json.dump(cfg, h, ensure_ascii=False)

    fail_root = _tmpdir(tmp, "fcw8-fail")
    fw = _world(fail_root, seed=False)
    rc_a, out_a, err_a = _run(_argv(fw, config=bad_cfg), fail_root)
    os.remove(fw["db"])
    for d in (fw["leads"], fw["orders"], fw["flows"]):
        for name in os.listdir(d):
            os.remove(os.path.join(d, name))
    _world(fail_root, seed=False)
    rc_b, out_b, err_b = _run(
        _argv(fw, config=bad_cfg), fail_root,
        {"PYTHONIOENCODING": "cp936", "PYTHONUTF8": "0"})
    assert rc_a == 2 and rc_b == 2, (
        "AC-FCW8 banned word must fail closed (%r/%r) %r"
        % (rc_a, rc_b, err_a))
    assert b"gate=FAIL" in out_a, "AC-FCW8 FAIL gate line"
    assert out_a == out_b, (
        "AC-FCW8 gate face must be byte-identical across encodings")


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-cli-env-")
    cases = [
        ("AC-FCW1 module-anchored defaults", case_fcw1),
        ("AC-FCW2 cwd-independent full run", case_fcw2),
        ("AC-FCW3 ambient cp936 byte identity", case_fcw3),
        ("AC-FCW4 module-derived config default", case_fcw4),
        ("AC-FCW5 explicit relative paths stay cwd-relative", case_fcw5),
        ("AC-FCW6 default_paths pure read", case_fcw6),
        ("AC-FCW7 hygiene", case_fcw7),
        ("AC-FCW8 gate law environment-independent", case_fcw8),
    ]
    failed = 0
    for name, fn in cases:
        try:
            fn(tmp)
        except AssertionError as exc:
            failed += 1
            print("FAIL %s: %s" % (name, exc))
        else:
            print("PASS %s" % name)
    print("SUITE %s %d/%d" % ("FAIL" if failed else "PASS",
                              len(cases) - failed, len(cases)))
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())