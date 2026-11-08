"""R2555 live leg: the real tree in one reading, plus fixtures on BOTH readers.

The real-tree audit is BOUNDED on purpose: a previous window measured that a
whole-tree walk costs minutes, so the reading is taken over a private copy of
this repository own probe_seam modules. Each fixture is then asked at the
shipped residual face and at this face, so every closed gap is measured on both
readers rather than quoted.

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

import probe_seam_name_binding_arm_mixed_residual_alias_chain as PNDR  # noqa
import probe_seam_name_binding_arm_mixed_residual_naming as PNDQ  # noqa
import suite_matrix as SM  # noqa: E402

EVIDENCE = os.path.join(
    ROOT, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-chain-live-R2555.log")

HELPER = "pndr_live_helper"

CONTAINER = ('D = {"a": {"b": ("%s",), "z": ("%s",)}}\n'
             % (HELPER, HELPER))
TAIL = 'for name in D["a"][KEY]:\n    pass\n'

TWO_HOP = (CONTAINER + 'A = "b"\nB = A\nif a1:\n    KEY = B\n'
                       'else:\n    KEY = B\n' + TAIL)

FUNC_CONST = (CONTAINER + 'def f():\n    C = "b"\n    if a1:\n'
                          '        KEY = C\n    else:\n        KEY = C\n'
                          '    ' + TAIL.replace("\n", "\n    ").rstrip()
              + "\n")

SEQ_DIFF = (CONTAINER + 'if a1:\n    if a2:\n        KEY = "b"\n'
                        '    else:\n        KEY = "b"\n    if a3:\n'
                        '        KEY = "b"\n    else:\n        KEY = "z"\n'
                        'else:\n    KEY = "b"\n' + TAIL)


def write_ascii(path, text):
    with open(path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(text)


def both(text):
    """This face and the shipped residual face on the same fixture."""
    row = PNDR.alias_report(text)["loops"][-1]
    mine = PNDR.alias_entry("KEY", text, row["scope"], row["line"])
    base = PNDQ.residual_entry("KEY", text, row["scope"], row["line"])
    return row, mine, base


def main():
    lines = []
    world = tempfile.mkdtemp(prefix="pndr-live-root-")
    report = None
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
        report = PNDR.reading(world, SM)
        counts = report["counts"]
        covered = [row for row in report["probes"]
                   if row["verdict"] == PNDR.COVERED]
        resolved = 0
        named = 0
        for row in covered:
            for loop in row.get("alias_loops") or []:
                resolved += len(loop["resolved_by_alias"])
                named += (len(loop["mixed"]) + len(loop["cycles"])
                          + len(loop["disagreeing"]))
        lines.append("BOUNDED REAL TREE files=%d verdict=%s probes=%d "
                     "covered=%d out_of_scope=%d historical=%d missing=%d "
                     "alias_resolved=%d alias_named=%d"
                     % (len(names), report["verdict"], len(report["probes"]),
                        len(covered), counts[PNDR.OUT_OF_SCOPE],
                        counts[PNDR.HISTORICAL], counts[PNDR.MISSING_SEAM],
                        resolved, named))
        yes = [row["file"] for row in covered]
        lines.append("COVERED PROBES %s"
                     % (", ".join(yes) if yes else "(none)"))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    for label, text in (("TWO_HOP", TWO_HOP), ("FUNC_CONST", FUNC_CONST),
                        ("SEQ_DIFF", SEQ_DIFF)):
        row, mine, base = both(text)
        if label == "SEQ_DIFF":
            lines.append(
                "SAME FIXTURE %s scope=%s this_state=%s this_reason=%s "
                "this_values=%s this_group=%s base_state=%s base_reason=%s"
                % (label, row["scope"], mine["state"], mine["reason"],
                   mine["values"], mine["disagreeing_group"],
                   base["state"], base["reason"]))
        else:
            lines.append(
                "SAME FIXTURE %s scope=%s this_state=%s this_value=%s "
                "this_chain=%s base_state=%s base_reason=%s"
                % (label, row["scope"], mine["state"], mine["value"],
                   mine["alias_chain"], base["state"], base["reason"]))

    body = "\n".join(lines) + "\n"
    with io.open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    back = open(EVIDENCE, "rb").read()
    print("LIVE written=%s bytes=%d crlf=%d bom=%s lf_only=%s"
          % (os.path.basename(EVIDENCE), len(back), back.count(b"\r\n"),
             back[:3] == b"\xef\xbb\xbf", back.count(b"\r") == 0))
    sys.stdout.write(body)
    return 0 if report and report["verdict"] == PNDR.SEAMS_ALIAS_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())