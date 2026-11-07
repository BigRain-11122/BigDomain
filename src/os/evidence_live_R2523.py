"""R2523 live leg: read the REAL src/os tree through the shipped writer law.

Prints, in one file: the shipped local-constant audit over src/os, the SAME
fixture read by BOTH readers (this face vs the shipped constant-binding face,
which reads only module-level constants), a stale local fixture read by this
face, and the digests of the module and the render before and after. Nothing is
written but this report; the caller names the path.
"""

import hashlib
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_constant_binding_scope as PCB  # noqa: E402
import probe_seam_local_constant_scope as PLC  # noqa: E402
import suite_matrix as SM  # noqa: E402


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def write_module(path, text):
    with open(path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(text)


def row_of(report, name):
    for row in report["probes"]:
        if row["file"] == name:
            return row
    return {}


def main(out_path):
    module = os.path.join(BASE, "probe_seam_local_constant_scope.py")
    render = os.path.join(SANDBOX, "suite_matrix.py")
    before = (digest(module), digest(render))
    report = PLC.audit(BASE, SM)
    lines = [PLC.render(report)]
    covered = [row for row in report["probes"]
               if row["verdict"] == PLC.COVERED]
    local = [row for row in covered if row["local_bindings"]]
    lines.append("LIVE local_rows=%d covered_probes=%d out_of_scope=%d "
                 "historical=%d read_only=%s"
                 % (len(local), len(covered),
                    report["counts"][PLC.OUT_OF_SCOPE],
                    report["counts"][PLC.HISTORICAL],
                    before == (digest(module), digest(render))))

    world = tempfile.mkdtemp(prefix="plc-live-")
    seams = PLC.seam_names(SM)
    write_module(os.path.join(world, "plc_live_helper.py"),
                 "QUIETED = (%s,)\n"
                 % ", ".join('"%s"' % name for name in seams))
    write_module(os.path.join(world, "plc_live_partial.py"),
                 "QUIETED = (%s,)\n" % ", ".join(
                     '"%s"' % name for name in seams[1:]))
    write_module(os.path.join(world, "plc_live_probe.py"),
                 'import importlib\n'
                 '\n'
                 'def run():\n'
                 '    name = "plc_live_helper"\n'
                 '    return importlib.import_module(name).QUIETED\n')
    write_module(os.path.join(world, "plc_live_stale.py"),
                 'import importlib\n'
                 '\n'
                 'def run():\n'
                 '    name = "plc_live_partial"\n'
                 '    return importlib.import_module(name).QUIETED\n')
    mine = PLC.audit(world, SM)
    theirs = PCB.audit(world, SM)
    mine_row = row_of(mine, "plc_live_probe.py")
    theirs_row = row_of(theirs, "plc_live_probe.py")
    lines.append("FIXTURE local-face=%s helpers=%s dynamic=%s local_bindings="
                 "%s | constant-binding-face=%s quieted=%d"
                 % (mine_row["verdict"], ",".join(mine_row["helpers"]),
                    ",".join(mine_row["dynamic"]),
                    ",".join(mine_row["local_bindings"]),
                    theirs_row["verdict"], len(theirs_row["quieted"])))
    stale_row = row_of(mine, "plc_live_stale.py")
    lines.append("STALE local-face=%s missing=%s world=%s"
                 % (stale_row["verdict"], ",".join(stale_row["missing"]),
                    mine["verdict"]))
    text = "\n".join(lines) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("LIVE bytes=%d utf8=True crlf=%d lf=%d"
          % (len(text.encode("utf-8")), text.count("\r\n"),
             text.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))