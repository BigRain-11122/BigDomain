"""pycrdt dual-package wiring prereq A+D live slice (radar window-6 claim, R1847).

Pre-registered acceptance criteria AC-YC1..YC6 live in src/os/backlog.md
(this row was written BEFORE this code ran - honesty law).
Single-command rerun: python src/sandbox/pycrdt-poc/wire_poc.py
Evidence: qa/pycrdt-wire-R1847.log (written by this run, pure ascii).
Opponent piece reused read-only from src/sandbox/ygo-poc (js/node_modules
yjs@13.6.33 + data/fixtures). Hygiene: vendor/ pip target is gitignored,
zero system-env pollution, zero network imports in shipped test code.
"""

import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(BASE, "vendor")
OUT = os.path.join(BASE, "out")
FIX = os.path.normpath(os.path.join(BASE, "..", "ygo-poc", "data", "fixtures"))
QA = os.path.normpath(os.path.join(BASE, "..", "..", "..", "qa"))
LOG = os.path.join(QA, "pycrdt-wire-R1847.log")

LINES = []
FAILURES = []


def log(line=""):
    LINES.append(line)
    print(line)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ((" " + detail) if detail else ""))
    if not ok:
        FAILURES.append(name)


def flush_log():
    with open(LOG, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(LINES) + "\n")


def main():
    log("--- AC-YC1 pip install (prereq D live) ---")
    log("cmd: python -m pip install --target <pycrdt-poc>/vendor pycrdt pycrdt-websocket")
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--target", VENDOR,
         "pycrdt", "pycrdt-websocket"],
        capture_output=True, text=True,
    )
    out_text = (proc.stdout or "") + (proc.stderr or "")
    for line in [l for l in out_text.splitlines() if l.strip()][-8:]:
        log("pip| " + line)
    src_build = ("Building wheel" in out_text) or ("building wheel" in out_text)
    check("AC-YC1 install", proc.returncode == 0 and not src_build,
          "returncode=%d source_build=%s" % (proc.returncode, "yes" if src_build else "no"))
    if proc.returncode != 0 or src_build:
        log("VERDICT prereq-D negative: install not wheel-clean; task row stays open")
        flush_log()
        return 2

    sys.path.insert(0, VENDOR)
    import pycrdt
    from pycrdt import Array, Doc, Map, Text

    log("pycrdt version=%s" % getattr(pycrdt, "__version__", "unknown"))

    def read_fixture(name):
        with open(os.path.join(FIX, name), "rb") as f:
            return f.read()

    def get_root(doc, name, t):
        attempts = [
            ("doc.get(name,T)", lambda: doc.get(name, t)),
            ("doc.get(name,type=T)", lambda: doc.get(name, type=t)),
            ("doc[name]", lambda: doc[name]),
            ("T(doc=doc,name=name)", lambda: t(doc=doc, name=name)),
        ]
        last = None
        for label, fn in attempts:
            try:
                v = fn()
                if v is not None:
                    return v, label
            except Exception as e:
                last = e
        raise RuntimeError("cannot bind root %r: %r" % (name, last))

    def deep(v):
        if isinstance(v, Map):
            try:
                keys = list(v.keys())
            except Exception:
                keys = list(v)
            return {k: deep(v[k]) for k in keys}
        if isinstance(v, Array):
            return [deep(x) for x in list(v)]
        if isinstance(v, Text):
            return str(v)
        if isinstance(v, dict):
            return {k: deep(x) for k, x in v.items()}
        if isinstance(v, list):
            return [deep(x) for x in v]
        return v

    def snapshot(doc):
        m, msrc = get_root(doc, "settings", Map)
        a, _ = get_root(doc, "chatlog", Array)
        t, _ = get_root(doc, "canvas", Text)
        snap = {"map": deep(m), "array": deep(a), "text": str(t)}
        return snap, msrc

    # --- AC-YC2 control anchor: pycrdt self roundtrip ---
    log("--- AC-YC2 control anchor (pycrdt self roundtrip) ---")
    d1 = Doc()
    t1 = Text()
    d1["canvas"] = t1
    try:
        t1.insert(0, "hello bigdomain wire")
    except Exception:
        t1 += "hello bigdomain wire"
    try:
        u1 = d1.get_update()
    except TypeError:
        u1 = d1.get_update(d1.get_state_vector())
    d2 = Doc()
    d2.apply_update(u1)
    t2, bindsrc = get_root(d2, "canvas", Text)
    check("AC-YC2 anchor roundtrip", str(t2) == "hello bigdomain wire",
          "text=%r bind=%s" % (str(t2), bindsrc))
    if str(t2) != "hello bigdomain wire":
        log("VERDICT anchor failed; other readings not trusted")
        flush_log()
        return 2

    # --- AC-YC3 forward: yjs@13 fixtures -> pycrdt ---
    log("--- AC-YC3 forward yjs@13 fixtures -> pycrdt ---")
    with open(os.path.join(FIX, "fx1-expected.json"), encoding="utf-8") as f:
        exp1 = json.load(f)
    with open(os.path.join(FIX, "fx-merge-expected.json"), encoding="utf-8") as f:
        expm = json.load(f)

    def apply_first_format(v1name, v2name):
        for label, fname in (("v1", v1name), ("v2", v2name)):
            doc = Doc()
            try:
                doc.apply_update(read_fixture(fname))
            except Exception as e:
                log("apply %s raised: %r" % (label, e))
                continue
            snap, src = snapshot(doc)
            if snap.get("text") or snap.get("map"):
                return doc, label, snap, src
            log("apply %s: no readable roots, snap=%r" % (label, snap))
        return None, None, None, None

    doc_fx, fmt, snap_fx, bind_fx = apply_first_format("fx1-v1.bin", "fx1-v2.bin")
    check("AC-YC3 fx1 single-client", doc_fx is not None and snap_fx == exp1,
          "format=%s bind=%s" % (fmt, bind_fx))
    if doc_fx is not None:
        log("fx1 snap=%s" % json.dumps(snap_fx, sort_keys=True))
        other = "fx1-v2.bin" if fmt == "v1" else "fx1-v1.bin"
        probe = Doc()
        try:
            probe.apply_update(read_fixture(other))
            psnap, _ = snapshot(probe)
            log("other-format probe (%s): readable=%s" % (other, bool(psnap.get("text"))))
        except Exception as e:
            log("other-format probe (%s): raised %r" % (other, e))

        # concurrent two-client pair merged state
        d_m = Doc()
        d_m.apply_update(read_fixture("fxA-%s.bin" % fmt))
        d_m.apply_update(read_fixture("fxB-%s.bin" % fmt))
        snap_m, _ = snapshot(d_m)
        check("AC-YC3 concurrent merge fxA+fxB", snap_m == expm,
              "snap=%s" % json.dumps(snap_m, sort_keys=True))

        # state-vector diff probe (sv-a.bin, 5 bytes)
        try:
            sv = read_fixture("sv-a.bin")
            diff = d_m.get_update(sv)
            log("sv probe: sv_len=%d diff_len=%d" % (len(sv), len(diff)))
            check("AC-YC3 sv diff probe", isinstance(diff, (bytes, bytearray)))
        except Exception as e:
            log("sv probe raised: %r" % e)
            check("AC-YC3 sv diff probe", False, "raised")

    # --- AC-YC4 reverse: pycrdt -> yjs@13 live ---
    log("--- AC-YC4 reverse pycrdt -> yjs@13 live ---")
    d3 = Doc()
    m3 = Map()
    d3["settings"] = m3
    m3["theme"] = "light"
    m3["x"] = 2.5
    m3["count"] = 3
    prof = Map()
    m3["profile"] = prof
    prof["level"] = 2
    prof["title"] = "core"
    a3 = Array()
    d3["chatlog"] = a3
    try:
        a3.append("a1")
        a3.append("b2")
    except Exception:
        try:
            a3.insert(0, ["a1", "b2"])
        except Exception:
            a3.insert(0, "a1")
            a3.insert(1, "b2")
    t3 = Text()
    d3["canvas"] = t3
    try:
        t3.insert(0, "pycrdt wire ok")
    except Exception:
        t3 += "pycrdt wire ok"
    u3 = d3.get_update()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "pycrdt-update-v1.bin"), "wb") as f:
        f.write(u3)
    rev2 = None
    if hasattr(d3, "get_update_v2"):
        try:
            rev2 = d3.get_update_v2()
            with open(os.path.join(OUT, "pycrdt-update-v2.bin"), "wb") as f:
                f.write(rev2)
        except Exception:
            rev2 = None
    py_side, _ = snapshot(d3)
    log("py side snap=%s update_len=%d" % (json.dumps(py_side, sort_keys=True), len(u3)))

    def run_node(fname, flag):
        return subprocess.run(
            ["node", os.path.join(BASE, "apply_in_yjs.mjs"),
             os.path.join(OUT, fname), flag],
            capture_output=True, text=True, cwd=BASE)

    node = run_node("pycrdt-update-v1.bin", "--v1")
    used_label = "v1"
    if node.returncode != 0 and rev2 is not None:
        log("v1 leg failed (%s); retrying with v2" % (node.stderr or node.stdout).strip()[:160])
        node = run_node("pycrdt-update-v2.bin", "--v2")
        used_label = "v2"
    if node.returncode != 0:
        check("AC-YC4 reverse wire-compat", False,
              (node.stderr or node.stdout).strip()[:200])
    else:
        js_side = json.loads(node.stdout.strip().splitlines()[-1])
        check("AC-YC4 reverse wire-compat", js_side == py_side,
              "format=%s py=%s js=%s" % (used_label, json.dumps(py_side, sort_keys=True),
                                          json.dumps(js_side, sort_keys=True)))

    # --- verdict ---
    log("--- verdict ---")
    if FAILURES:
        log("VERDICT wire-compat FAIL failing=%s (honest negative, pool entry gets a downgrade note)"
            % ",".join(FAILURES))
        flush_log()
        return 2
    log("VERDICT wire-compat PASS both directions closed (yjs@13.6.33 <-> pycrdt, prereq A core met; prereq D wheel verified)")
    flush_log()
    return 0


if __name__ == "__main__":
    sys.exit(main())
