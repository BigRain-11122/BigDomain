"""R2521 live leg: read the REAL src/os tree through the shipped writer law.

Prints, in one file: the shipped constant-binding audit over src/os, the same
fixture read by BOTH readers (constant-binding face vs the shipped dynamic
face), and the digests of the module and the render taken before and after.
Nothing is written but this report; the caller names the path.
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
import probe_seam_dynamic_import_scope as PDI  # noqa: E402
import suite_matrix as SM  # noqa: E402


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(out_path):
    module = os.path.join(BASE, "probe_seam_constant_binding_scope.py")
    render = os.path.join(SANDBOX, "suite_matrix.py")
    before = (digest(module), digest(render))
    report = PCB.audit(BASE, SM)
    lines = [PCB.render(report)]
    covered = [row for row in report["probes"]
               if row["verdict"] == PCB.COVERED]
    bound = [row for row in covered if row["bindings"]]
    lines.append("LIVE bound_rows=%d covered_probes=%d out_of_scope=%d "
                 "historical=%d read_only=%s"
                 % (len(bound), len(covered),
                    report["counts"][PCB.OUT_OF_SCOPE],
                    report["counts"][PCB.HISTORICAL],
                    before == (digest(module), digest(render))))

    world = tempfile.mkdtemp(prefix="pcb-live-")
    seams = PCB.seam_names(SM)
    helper = os.path.join(world, "pcb_live_helper.py")
    with open(helper, "w", encoding="ascii", newline="\n") as handle:
        handle.write("QUIETED = (%s,)\n"
                     % ", ".join('"%s"' % name for name in seams))
    probe = os.path.join(world, "pcb_live_probe.py")
    with open(probe, "w", encoding="ascii", newline="\n") as handle:
        handle.write('import importlib\n'
                     'NAME = "pcb_live_helper"\n'
                     '\n'
                     'def run():\n'
                     '    return importlib.import_module(NAME).QUIETED\n')
    mine = PCB.audit(world, SM)
    theirs = PDI.audit(world, SM)
    mine_row = [row for row in mine["probes"]
                if row["file"] == "pcb_live_probe.py"][0]
    theirs_row = [row for row in theirs["probes"]
                  if row["file"] == "pcb_live_probe.py"][0]
    lines.append("FIXTURE constant-binding=%s dynamic=%s helpers=%s "
                 "dynamic_shapes=%s unresolved=%s | dynamic-face=%s quieted=%d"
                 % (mine_row["verdict"], theirs_row["verdict"],
                    ",".join(mine_row["helpers"]),
                    ",".join(mine_row["dynamic"]),
                    ",".join(mine_row["unresolved"]) or "-",
                    theirs_row["verdict"], len(theirs_row["quieted"])))
    text = "\n".join(lines) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("LIVE bytes=%d utf8=True crlf=%d lf=%d"
          % (len(text.encode("utf-8")), text.count("\r\n"),
             text.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))