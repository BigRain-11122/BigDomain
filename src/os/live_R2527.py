"""R2527 live leg for the seam constant-alias scope face.

Writes one utf-8 LF evidence file and nothing else. Read-only on the tree.
"""

import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_constant_alias_scope as PCAS  # noqa: E402
import probe_seam_annotated_constant_scope as PLAC  # noqa: E402
import suite_matrix as SM  # noqa: E402

HELPER = "pcas_live_helper"
FIXTURE = ('import importlib\n'
           '\n'
           'BASE_NAME = "%s"\n'
           'ALIAS: str = BASE_NAME\n'
           '\n'
           'def run():\n'
           '    return importlib.import_module(ALIAS).QUIETED\n' % HELPER)

REFUSED = ('import importlib\n'
           'import pcas_live_pkg\n'
           '\n'
           'def run():\n'
           '    return importlib.import_module('
           'pcas_live_pkg.FLAT.A.NAMES[1]).QUIETED\n')


def write(path, text):
    with open(path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(text)


def main():
    lines = []
    render_before = PCAS.digest(SM.__file__)
    module_before = PCAS.digest(PCAS.__file__)
    report = PCAS.reading(BASE, SM)
    counts = report["counts"]
    lines.append("LIVE real tree root=%s verdict=%s probes=%d covered=%d "
                 "out_of_scope=%d historical=%d unreadable=%d missing=%d"
                 % (BASE, report["verdict"], len(report["probes"]),
                    counts[PCAS.COVERED], counts[PCAS.OUT_OF_SCOPE],
                    counts[PCAS.HISTORICAL], counts[PCAS.UNREADABLE],
                    counts[PCAS.MISSING_SEAM]))
    for row in report["probes"]:
        if row["verdict"] == PCAS.COVERED and row["alias_chains"]:
            lines.append("  ALIASED %s chains=%s"
                         % (row["file"], ",".join(row["alias_chains"])))
    lines.append("DIGEST render_unchanged=%s module_unchanged=%s"
                 % (PCAS.digest(SM.__file__) == render_before,
                    PCAS.digest(PCAS.__file__) == module_before))

    world = tempfile.mkdtemp(prefix="pcas-live-")
    try:
        seams = PCAS.seam_names(SM)
        write(os.path.join(world, HELPER + ".py"),
              'QUIETED = (%s,)\n'
              % ", ".join('"%s"' % name for name in seams))
        write(os.path.join(world, "pcas_live_pkg.py"),
              'NAMES = ("pcas_unused", "%s")\n'
              'FLAT = {"A": "pcas_unused"}\n' % HELPER)
        write(os.path.join(world, "pcas_live_alias.py"), FIXTURE)
        write(os.path.join(world, "pcas_live_refused.py"), REFUSED)
        here = PCAS.audit(world, SM)
        there = PLAC.audit(world, SM)
        alias_row = [row for row in here["probes"]
                     if row["file"] == "pcas_live_alias.py"][0]
        annotated_row = [row for row in there["probes"]
                        if row["file"] == "pcas_live_alias.py"][0]
        lines.append("SAME FIXTURE alias_face=%s quieted=%d dynamic=%s"
                     % (alias_row["verdict"], len(alias_row["quieted"]),
                        ",".join(alias_row["dynamic"])))
        lines.append("SAME FIXTURE annotated_face=%s quieted=%d"
                     % (annotated_row["verdict"],
                        len(annotated_row["quieted"])))
        lines.append("CHAIN %s" % ",".join(alias_row["alias_chains"]))
        refused_row = [row for row in here["probes"]
                       if row["file"] == "pcas_live_refused.py"][0]
        lines.append("REFUSED %s shapes=%s refused=%s"
                     % (refused_row["verdict"],
                        ",".join(refused_row["shapes"]) or "-",
                        ",".join(refused_row["refused_chains"]) or "-"))
        lines.append("WORLD alias=%s annotated=%s"
                     % (here["verdict"], there["verdict"]))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    text = "\n".join(lines) + "\n"
    out = os.path.join(SRC, os.pardir, "qa",
                       "probe-seam-constant-alias-scope-live-R2527.log")
    with io.open(os.path.abspath(out), "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())