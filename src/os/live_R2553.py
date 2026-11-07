"""R2553 live leg: the real tree in one reading, plus one fixture on BOTH readers.

The real-tree audit is bounded to this repository own probe modules by reading
`src/os` (measured at about 133s on this host). The fixture comparison writes a
private temporary world and asks the shipped arm-mixed face and this face the
same question, so the closed gap is measured on both readers rather than quoted.

One UTF-8 LF writer, no shell redirection.
"""

import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
SANDBOX = os.path.join(ROOT, "src", "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_name_binding_arm_mixed_residual_naming as PNDQ  # noqa: E402
import probe_seam_name_binding_nested_arm_mixed_scope as PNDP  # noqa: E402
import suite_matrix as SM  # noqa: E402

EVIDENCE = os.path.join(
    ROOT, "qa",
    "probe-seam-name-binding-arm-mixed-residual-naming-live-R2553.log")

HELPER = "pndq_live_helper"

FIXTURE = ('D = {"a": {"b": ("%s",), "z": ("%s",)}}\n'
           'if a1:\n'
           '    if a2:\n'
           '        KEY = "b"\n'
           '    else:\n'
           '        KEY = "b"\n'
           '    if a3:\n'
           '        KEY = "b"\n'
           '    else:\n'
           '        KEY = "b"\n'
           'else:\n'
           '    KEY = "b"\n'
           'for name in D["a"][KEY]:\n'
           '    pass\n' % (HELPER, HELPER))

WAS_FIXTURE = ('with open("x") as WK:\n'
               '    pass\n'
               'for name in ("a",):\n'
               '    pass\n')


def write_ascii(path, text):
    with open(path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(text)


def main():
    lines = []
    world = tempfile.mkdtemp(prefix="pndq-live-root-")
    try:
        src_dir = os.path.join(ROOT, "src", "os")
        names = sorted(name for name in os.listdir(src_dir)
                       if name.startswith("probe_seam_") and
                       name.endswith(".py"))
        for name in names:
            with open(os.path.join(src_dir, name), "rb") as handle:
                data = handle.read()
            with open(os.path.join(world, name), "wb") as handle:
                handle.write(data)
        report = PNDQ.reading(world, SM)
        counts = report["counts"]
        covered = [row for row in report["probes"]
                   if row["verdict"] == PNDQ.COVERED]
        folded = 0
        named = 0
        for row in covered:
            for loop in row.get("residual_loops") or []:
                folded += len(loop["resolved_by_residual"])
                named += len(loop["named_with_as"]) + len(
                    loop["named_name_mixed"])
        lines.append("BOUNDED REAL TREE files=%d verdict=%s probes=%d "
                     "covered=%d out_of_scope=%d historical=%d missing=%d "
                     "folded=%d named=%d"
                     % (len(names), report["verdict"], len(report["probes"]),
                        len(covered), counts[PNDQ.OUT_OF_SCOPE],
                        counts[PNDQ.HISTORICAL], counts[PNDQ.MISSING_SEAM],
                        folded, named))
        yes = [row["file"] for row in covered]
        lines.append("COVERED PROBES %s"
                     % (", ".join(yes) if yes else "(none)"))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    world = tempfile.mkdtemp(prefix="pndq-live-")
    try:
        seams = PNDQ.seam_names(SM)
        write_ascii(os.path.join(world, HELPER + ".py"),
                    'QUIETED = (%s,)\n'
                    % ", ".join('"%s"' % name for name in seams))
        write_ascii(os.path.join(world, "pndq_live_probe.py"),
                    'import importlib\n'
                    + FIXTURE.replace('    pass\n',
                                      '    importlib.import_module(name)'
                                      '.QUIETED\n'))
        mine = PNDQ.residual_report(
            open(os.path.join(world, "pndq_live_probe.py"),
                 encoding="utf-8").read())["loops"][-1]
        base = PNDP.arm_report(
            open(os.path.join(world, "pndq_live_probe.py"),
                 encoding="utf-8").read())["loops"][-1]
        lines.append("SAME FIXTURE residual followed=%r resolved=%r "
                     "folded=%r base_arm_mixed_refused=%r"
                     % (mine["followed"], mine["resolved_by_residual"],
                        mine["groups_folded"].get("KEY"),
                        base["refused"]))
        entry = PNDQ.residual_entry("WK", WAS_FIXTURE, "module", 3)
        lines.append("SAME FIXTURE with-as residual=%r base=%r"
                     % (entry["reason"], entry["base_arm_mixed_reason"]))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    body = "\n".join(lines) + "\n"
    with io.open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    back = open(EVIDENCE, "rb").read()
    print("LIVE written=%s bytes=%d crlf=%d bom=%s lf_only=%s"
          % (os.path.basename(EVIDENCE), len(back), back.count(b"\r\n"),
             back[:3] == b"\xef\xbb\xbf", back.count(b"\r") == 0))
    sys.stdout.write(body)
    return 0 if report["verdict"] == PNDQ.SEAMS_RESIDUAL_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())