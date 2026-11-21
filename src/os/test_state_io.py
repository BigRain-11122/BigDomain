"""State write-canon suite (R2246; criteria AC-SIO1..AC-SIO8 were
pre-registered in state/queue/tech.md as this window's claim BEFORE the code
existed - honesty law).

What this proves: the layout of state.json is measured from real bytes instead
of eyeballed (AC-SIO1), the canonical rewrite is payload-preserving (AC-SIO2),
every malformed document is refused before a write (AC-SIO3), a write can
never change the payload (AC-SIO4), the write is atomic with a read-back proof
and no temp residue (AC-SIO5), the plan predicts the exact post bytes and only
the execute path lands them (AC-SIO6), the CLI codes and --json keys are
stable and a second fix is a no-op (AC-SIO7), and the module is pure ASCII,
stdlib, offline and wired into the battery (AC-SIO8).

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import hashlib
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402

EXPECTED_CRITERIA = 10
MODULE = os.path.join(BASE, "state_io.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-state-io"
# The drift sample must sit OFF the canon indent, so derive it from the
# module own value: hardcoding it made the drift leg vanish the moment
# ITEM_INDENT became that same number (R2692 change, caught by R2693 battery).
DRIFT_INDENT = SIO.ITEM_INDENT + 2

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


def tmpdir():
    return tempfile.mkdtemp(prefix="sio_R2246_")


def sample_text(eol="\n", indent=2):
    body = json.dumps({"tick": 7, "note": "x", "log": ["one", "two"]},
                      indent=2)
    lines = body.split("\n")
    fixed = []
    inside = False
    for line in lines:
        if line.strip().startswith('"log": ['):
            inside = True
            fixed.append(line)
            continue
        if inside and line.strip() == "]":
            inside = False
            fixed.append(line)
            continue
        if inside and line.strip().startswith('"'):
            # Always apply the requested indent: json.dumps parks log items at
            # 4 spaces, so skipping this when indent==2 silently produced a
            # "clean" sample that was off the canon indent.
            fixed.append(" " * indent + line.strip())
            continue
        fixed.append(line)
    out = fixed
    return eol.join(out) + eol


def write_sample(folder, text, name="state.json"):
    path = os.path.join(folder, name)
    with open(path, "wb") as handle:
        handle.write(text.encode("utf-8"))
    return path


def ac_sio1():
    folder = tmpdir()
    good = write_sample(folder, sample_text("\r\n", SIO.ITEM_INDENT), "good.json")
    bad = write_sample(folder, sample_text("\n", DRIFT_INDENT), "bad.json")
    measured_good = SIO.report(good)
    measured_bad = SIO.report(bad)
    ok = (
        measured_good["layout_ok"] is True
        and measured_good["eol_ok"] is True
        and measured_good["crlf"] > 0
        and measured_good["bare_lf"] == 0
        and measured_good["log_items"] == 2
        and measured_good["log_len"] == 2
        and measured_good["items_off_indent"] == 0
        and measured_bad["layout_ok"] is False
        and measured_bad["eol_ok"] is False
        and measured_bad["bare_lf"] > 0
        and measured_bad["items_off_indent"] == 2
        and measured_bad["count_ok"] is True
    )
    live = os.path.join(BASE, "state.json")
    if os.path.exists(live):
        measured_live = SIO.report(live)
        ok = ok and measured_live["bytes"] == len(SIO.read_raw(live))
    check(ok, "AC-SIO1 layout measured from bytes (clean vs drift, live size)")


def ac_sio2():
    folder = tmpdir()
    bad = write_sample(folder, sample_text("\n", DRIFT_INDENT), "bad.json")
    text = SIO.decode(SIO.read_raw(bad))
    out = SIO.canon(text)
    data_ok = SIO.parse(out) == SIO.parse(text)
    crumbs_lf = out.count("\n") - out.count("\r\n")
    indents = [line for line in out.split("\r\n")
               if line.strip().startswith('"') and not line.strip().startswith('"log"')]
    ok = (data_ok and crumbs_lf == 0 and out.count("\r\n") > 0
          and all((len(line) - len(line.lstrip(" "))) == SIO.ITEM_INDENT
                  for line in out.split("\r\n")
                  if line.strip() in ('"one",', '"two"')))
    check(ok, "AC-SIO2 canon forces CRLF and the canon indent, payload unchanged")


def ac_sio3():
    folder = tmpdir()
    # Valid JSON, two log entries on ONE line: the parsed log length and the
    # item-line count disagree, which is the layout defect the law names.
    mismatched = ('{\r\n  "tick": 7,\r\n  "log": [\r\n'
                  + " " * SIO.ITEM_INDENT + '"one", "two"\r\n  ]\r\n}\r\n')
    path = write_sample(folder, mismatched, "mismatch.json")
    first = None
    try:
        SIO.canon(SIO.decode(SIO.read_raw(path)))
    except SIO.StateIOError as exc:
        first = exc.code
    broken = write_sample(folder, "{not json", "broken.json")
    second = None
    try:
        SIO.canon(SIO.decode(SIO.read_raw(broken)))
    except SIO.StateIOError as exc:
        second = exc.code
    untouched = SIO.read_raw(path) == mismatched.encode("utf-8")
    check(first == "E_SIO_LAYOUT" and second == "E_SIO_JSON" and untouched,
          "AC-SIO3 bad item count and bad JSON refused, nothing written")


def ac_sio4():
    folder = tmpdir()
    path = write_sample(folder, sample_text("\n", 2), "state.json")
    before = SIO.read_raw(path)
    changed = sample_text("\r\n", SIO.ITEM_INDENT).replace('"tick": 7',
                                                           '"tick": 8')
    code = None
    try:
        SIO.write_canon(path, changed)
    except SIO.StateIOError as exc:
        code = exc.code
    after = SIO.read_raw(path)
    check(code == "E_SIO_JSON" and before == after,
          "AC-SIO4 payload change refused, old bytes byte-identical")


def ac_sio5():
    folder = tmpdir()
    path = write_sample(folder, sample_text("\n", 2), "state.json")
    text = SIO.decode(SIO.read_raw(path))
    written = SIO.write_canon(path, SIO.canon(text))
    residue = [name for name in os.listdir(folder)
               if name.startswith(".state_io_")]
    back = SIO.read_raw(path)
    ok = (written["written"] == len(back) and residue == []
          and SIO.report(path)["layout_ok"] is True
          and written["previous"] > 0)
    check(ok, "AC-SIO5 atomic write, read-back proof, zero temp residue")


def ac_sio6():
    folder = tmpdir()
    path = write_sample(folder, sample_text("\n", 2), "state.json")
    before = SIO.read_raw(path)
    plan = SIO.fix(path, execute=False)
    dry_untouched = SIO.read_raw(path) == before
    landed = SIO.fix(path, execute=True)
    after = SIO.read_raw(path)
    ok = (plan["verdict"] == "CANON-DRIFT" and plan["written"] == 0
          and dry_untouched and landed["verdict"] == "CANON-FIXED"
          and landed["written"] == plan["predicted_bytes"]
          and len(after) == plan["predicted_bytes"]
          and landed["after"]["layout_ok"] is True)
    check(ok, "AC-SIO6 dry plan writes nothing, execute lands on prediction")


def ac_sio7():
    import subprocess
    root = tmpdir()
    os.makedirs(os.path.join(root, "src", "os"))
    write_sample(os.path.join(root, "src", "os"),
                 sample_text("\n", 2), "state.json")

    def run(args, use_root=True):
        cmd = [sys.executable, MODULE]
        if use_root:
            cmd += ["--root", root]
        proc = subprocess.run(cmd + args, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        return proc.returncode, proc.stdout.decode("utf-8", "replace")
    rc_drift, _ = run(["--check"])
    rc_json, body_json = run(["--check", "--json"])
    payload = json.loads(body_json)
    keys_ok = set(["verdict", "before", "predicted_bytes", "written",
                   "execute"]).issubset(set(payload.keys()))
    rc_fix, _ = run(["--fix", "--execute"])
    rc_clean, _ = run(["--check"])
    rc_second, _ = run(["--fix", "--execute"])
    rc_bad, _ = run(["--nonsense"])
    missing = os.path.join(root, "gone")
    proc = subprocess.run([sys.executable, MODULE, "--root", missing],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ok = (rc_drift == 2 and rc_json == 2 and keys_ok and rc_fix == 0
          and rc_clean == 0 and rc_second == 0 and rc_bad == 2
          and proc.returncode == 3)
    check(ok, "AC-SIO7 CLI codes 0/2/3, pinned --json keys, second fix no-op")


def ac_sio8():
    raw = open(MODULE, "rb").read()
    ascii_ok = all(byte < 128 for byte in raw)
    text = raw.decode("ascii", "replace")
    banned = ["import urllib", "import requests", "import socket",
              "import subprocess", "http://", "https://"]
    clean = not any(token in text for token in banned)
    wiring = ""
    if os.path.exists(RUNNER):
        wiring = open(RUNNER, "rb").read().decode("utf-8", "replace")
    wired = (LABEL in wiring) and ("test_state_io.py" in wiring)
    check(ascii_ok and clean and wired,
          "AC-SIO8 ASCII, stdlib-only, offline, wired as %s" % LABEL)


def ac_sio9():
    """Same layout law as the shipped carrier gate (R3179).

    The two faces used to disagree on the live file: state_io called a
    16-space canon drifted while logs_toolkit called it clean, so a repair
    through this module would have written a shape the gate flags.
    """
    import logs_toolkit as LT

    def agrees(text):
        measured = SIO.layout(text)
        gate = LT.eol_profile(text.encode("utf-8"))
        return measured["layout_ok"] == (gate["layout_ok"]
                                         and gate["indent_ok"])

    verdicts = []
    live = os.path.join(BASE, "state.json")
    if os.path.exists(live):
        verdicts.append(agrees(SIO.decode(SIO.read_raw(live))))
    folder = tmpdir()
    mixed = sample_text("\r\n", 16).replace(" " * 16 + '"two"',
                                            " " * 8 + '"two"')
    shapes = (("legacy2.json", sample_text("\r\n", 2), True),
              ("canon16.json", sample_text("\r\n", 16), True),
              ("mixed.json", mixed, False),
              ("barelf.json", sample_text("\n", 16), False))
    for name, text, want in shapes:
        write_sample(folder, text, name)
        verdicts.append(agrees(text) and SIO.layout(text)["layout_ok"] is want)
    check(len(verdicts) == (5 if os.path.exists(live) else 4)
          and all(verdicts),
          "AC-SIO9 state_io and the carrier gate agree on the same file")


def ac_sio10():
    """Every writer publishes the fold door own reading (R3180).

    R3179 closed the caliber split between this module and the carrier gate,
    but nothing at a write site said whether the bytes just landed are
    readable by the fold. The face names both answers separately instead of
    merging them, and the write contract is unchanged.
    """
    import logs_toolkit as LT

    folder = tmpdir()
    clean = sample_text("\r\n", SIO.ITEM_INDENT)
    path = write_sample(folder, clean, "clean.json")

    # a) the raw door publishes the face on the bytes it just landed
    written = SIO.write_canon(path, SIO.canon(clean))
    face = written["carrier"]
    arm_a = (face.get("layout_ok") is True and face.get("indent_ok") is True
             and face.get("gate_layout_ok") is True
             and face.get("gate_indent_ok") is True
             and face.get("fold_readable") is True
             and face.get("agree") is True
             and written["written"] == len(clean.encode("utf-8"))
             and "previous" in written)

    # b) the new-payload door face equals a recomputation on the written bytes
    payload = {"tick": 9, "note": "x", "log": ["one", "two"]}
    doc = SIO.write_document(path, payload)
    arm_b = (doc["carrier"] == SIO.carrier_face(SIO.read_raw(path))
             and doc["carrier"]["agree"] is True
             and doc["carrier"]["fold_readable"] is True)

    # c) the repair path publishes the face on both states
    clean_plan = SIO.fix(path, execute=False)
    drift_path = write_sample(folder, sample_text("\n", SIO.ITEM_INDENT),
                              "drift.json")
    drift_plan = SIO.fix(drift_path, execute=False)
    drift_done = SIO.fix(drift_path, execute=True)
    arm_c = (clean_plan["verdict"] == "CANON-CLEAN"
             and clean_plan["carrier"]["agree"] is True
             and drift_plan["carrier"].get("fold_readable") is False
             and drift_done["verdict"] == "CANON-FIXED"
             and drift_done["carrier"]["fold_readable"] is True
             and drift_done["carrier"] == SIO.carrier_face(
                 SIO.read_raw(drift_path)))

    # d) decisive arm: two answers stay two answers. A uniform two-space
    # document is healthy here while the fold door reads only its own
    # caliber, and the face must publish that instead of averaging it away.
    legacy_path = write_sample(folder, sample_text("\r\n", 2), "legacy.json")
    legacy_face = SIO.carrier_face(SIO.read_raw(legacy_path))
    legacy_text = SIO.decode(SIO.read_raw(legacy_path))
    want_fold = LT.split_ps_layout(legacy_text, 2) is not None
    arm_d = (legacy_face["layout_ok"] is True
             and legacy_face["fold_readable"] is want_fold
             and "indent_ok" in legacy_face
             and "fold_readable" in legacy_face)

    # e) the write contract is untouched: same error codes, payload change
    # still refused with the old bytes intact, and the new-payload door still
    # refuses a shape its own gate calls drifted.
    source = open(MODULE, "r", encoding="utf-8").read()
    found = set()
    for token in source.replace('"', " ").replace("'", " ").split():
        if token.startswith("E_SIO_"):
            found.add(token.strip("(),:;"))
    codes = set(("E_SIO_BOM", "E_SIO_UTF8", "E_SIO_JSON", "E_SIO_LAYOUT",
                 "E_SIO_BACK", "E_SIO_PREDICT", "E_SIO_READ"))
    refuse_path = write_sample(folder, clean, "refuse.json")
    refuse_before = SIO.read_raw(refuse_path)
    payload_refused = False
    try:
        SIO.write_canon(refuse_path, SIO.canon(clean).replace('"one"',
                                                              '"uno"'))
    except SIO.StateIOError as exc:
        payload_refused = exc.code == "E_SIO_JSON"
    intact = SIO.read_raw(refuse_path) == refuse_before
    shape_refused = False
    saved = SIO.ITEM_INDENT
    try:
        SIO.ITEM_INDENT = 8
        try:
            SIO.write_document(write_sample(folder, clean, "shape.json"),
                               payload)
        except SIO.StateIOError as exc:
            shape_refused = exc.code == "E_SIO_LAYOUT"
    finally:
        SIO.ITEM_INDENT = saved
    arm_e = (found == codes and payload_refused and intact and shape_refused)

    # f) hygiene and the live carrier
    ascii_ok = True
    try:
        SIO.read_raw(MODULE).decode("ascii")
    except UnicodeDecodeError:
        ascii_ok = False
    offline = not any(token in source for token in
                      ("import urllib", "import requests", "import socket",
                       "import subprocess", "http://", "https://"))
    live = os.path.join(BASE, "state.json")
    live_ok = False
    if os.path.exists(live):
        live_face = SIO.carrier_face(SIO.read_raw(live))
        live_ok = (live_face.get("agree") is True
                   and live_face.get("fold_readable") is True)
    arm_f = ascii_ok and offline and live_ok
    check(arm_a and arm_b and arm_c and arm_d and arm_e and arm_f,
          "AC-SIO10 writers publish both readings (a%s b%s c%s d%s e%s f%s)"
          % tuple("+" if arm else "-" for arm in
                  (arm_a, arm_b, arm_c, arm_d, arm_e, arm_f)))


def main():
    ac_sio1()
    ac_sio2()
    ac_sio3()
    ac_sio4()
    ac_sio5()
    ac_sio6()
    ac_sio7()
    ac_sio8()
    ac_sio9()
    ac_sio10()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria=%d"
          % ("PASS" if FAILS == 0 and total == EXPECTED_CRITERIA else "FAIL",
             PASSES, total, EXPECTED_CRITERIA), flush=True)
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(main())