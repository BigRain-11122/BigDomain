"""Capture the R2525 evidence in one callable (suite twice, live leg).

Writes ASCII/LF evidence files with an explicit newline and a read-back, so
the bytes a later battery reads are the bytes this window measured.
"""

import hashlib
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QA = os.path.join(REPO, "qa")
SUITE = os.path.join(BASE, "test_probe_seam_annotated_constant_scope.py")
LIVE = os.path.join(BASE, "probe_seam_annotated_constant_scope.py")
ADJACENT = ("test_probe_seam_local_constant_scope.py",
            "test_probe_seam_dynamic_import_scope.py",
            "test_probe_seam_registry.py")
SUITE_EVIDENCE = os.path.join(QA, "probe-seam-annotated-constant-scope-R2525.log")
LIVE_EVIDENCE = os.path.join(
    QA, "probe-seam-annotated-constant-scope-live-R2525.log")


def run(args):
    proc = subprocess.run([sys.executable] + args, cwd=REPO,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def land(path, text):
    body = text.replace("\r\n", "\n").replace("\r", "\n")
    if not body.endswith("\n"):
        body += "\n"
    data = body.encode("utf-8")
    with open(path, "wb") as handle:
        handle.write(data)
    with open(path, "rb") as handle:
        back = handle.read()
    assert back == data, "read-back mismatch at %s" % path
    return len(data)


def main():
    if not os.path.isdir(QA):
        os.makedirs(QA)
    lines = []
    code1, out1 = run([SUITE])
    digest1 = hashlib.sha256(out1.encode("utf-8")).hexdigest()
    code2, out2 = run([SUITE])
    digest2 = hashlib.sha256(out2.encode("utf-8")).hexdigest()
    legs = [(code1, out1), (code2, out2)]
    identical = code1 == code2 and digest1 == digest2
    adjacent = []
    for name in ADJACENT:
        code, out = run([os.path.join(BASE, name)])
        tail = [line for line in out.strip().splitlines() if line.strip()][-1:]
        adjacent.append((name, code, tail[0] if tail else ""))
    lines.append("PROBE SEAM ANNOTATED CONSTANT SCOPE EVIDENCE R2525")
    lines.append("legs=2 identical=%s fails=%d adjacent=%d"
                 % (identical,
                    sum(1 for code, _out in legs if code != 0),
                    sum(1 for _n, code, _t in adjacent if code != 0)))
    with open(SUITE_EVIDENCE, "w", encoding="ascii", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    blocks = []
    for index, (code, out) in enumerate(legs, start=1):
        blocks.append("--- LEG %d exit=%d digest=%s ---\n%s"
                      % (index, code,
                         hashlib.sha256(out.encode("utf-8")).hexdigest(), out))
    for name, code, tail in adjacent:
        blocks.append("--- ADJACENT %s exit=%d tail=%s ---"
                      % (name, code, tail))
    body = "\n".join(lines) + "\n" + "".join(blocks)
    size = land(SUITE_EVIDENCE, body)
    print("SUITE-EVIDENCE %s bytes=%d legs=2 identical=%s fails=%d "
          "adjacent_fails=%d"
          % (SUITE_EVIDENCE, size, identical,
             sum(1 for code, _out in legs if code != 0),
             sum(1 for _n, code, _t in adjacent if code != 0)))

    live = []
    code, out = run([LIVE, "--root", BASE])
    live.append("LIVE real-tree exit=%d" % code)
    live.append(out.strip())
    code2b, out2b = run([LIVE, "--root", os.path.join(BASE, "no-such-root")])
    live.append("LIVE missing-root exit=%d" % code2b)
    live.append(out2b.strip())
    live.extend(_stale_leg())
    live_size = land(LIVE_EVIDENCE, "\n".join(live))
    print("LIVE-EVIDENCE %s bytes=%d real_tree_exit=%d missing_root_exit=%d"
          % (LIVE_EVIDENCE, live_size, code, code2b))
    return 0


def _stale_leg():
    """One annotated probe against a partial helper, on the real reader."""
    import shutil
    import tempfile
    sys.path.insert(0, BASE)
    sys.path.insert(0, os.path.join(REPO, "src", "sandbox"))
    import probe_seam_annotated_constant_scope as PLAC
    import suite_matrix as SM
    seams = PLAC.seam_names(SM)
    root = tempfile.mkdtemp(prefix="plac-live-")
    try:
        with open(os.path.join(root, "plac_live_helper.py"), "w",
                  encoding="ascii", newline="\n") as handle:
            handle.write('QUIETED = (%s,)\n'
                         % ", ".join('"%s"' % name for name in seams[1:]))
        with open(os.path.join(root, "plac_live_probe.py"), "w",
                  encoding="ascii", newline="\n") as handle:
            handle.write('import importlib\n\n'
                         'NAME: str = "plac_live_helper"\n\n'
                         'def run():\n'
                         '    return importlib.import_module(NAME).QUIETED\n')
        report = PLAC.audit(root, SM)
        row = [item for item in report["probes"]
               if item["file"] == "plac_live_probe.py"][0]
        return ["LIVE annotated fixture verdict=%s missing=%s dynamic=%s"
                % (row["verdict"], ",".join(row["missing"]),
                   ",".join(row["dynamic"])),
                "LIVE annotated fixture world=%s" % report["verdict"]]
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())