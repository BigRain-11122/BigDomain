"""R2380 live capture: the derived pile on the REAL tree, one writer, utf-8 LF.

Measures, not asserts:
  STEP1 the pile derived from the round own evidence path
  STEP2 the guarded section over the real evidence is byte-identical to the
        matrix core it guards (the normal path adds no wording)
  STEP3 an absolute path derives the same pile as the relative one
  STEP4 the wire CLI still reads the real pile at its published exit code

Stdlib only, ASCII source, no clock, no network. Writes one evidence file.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import battery_followup as BF  # noqa: E402
import followup_guard_evidence_scope as FGES  # noqa: E402
import followup_section_foreign_wire as FSFW  # noqa: E402

REPO = os.path.dirname(os.path.dirname(BASE))
EVIDENCE = "qa/reconcile-all-R2380.log"
OUT = os.path.join(REPO, "qa", "followup-guard-evidence-scope-live-R2380.log")


def call(cmd):
    import subprocess
    proc = subprocess.run(cmd, cwd=REPO, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def main():
    lines = []
    derived = FGES.evidence_dir(EVIDENCE)
    lines.append("STEP1 derived_dir=%s evidence=%s" % (derived, EVIDENCE))

    entry, body = FSFW.matrix_section(REPO, EVIDENCE, call)
    core_entry, core_body = BF.matrix_core(REPO, EVIDENCE, call)
    same = entry == core_entry and body == core_body
    lines.append("STEP2 section_verdict=%s identical_to_core=%s detail=%s"
                 % (entry["verdict"], same, entry["detail"]))

    absolute = os.path.join(REPO, EVIDENCE.replace("/", os.sep))
    abs_dir = FGES.evidence_dir(absolute)
    lines.append("STEP3 abs_dir=%s same_as_relative=%s"
                 % (abs_dir, abs_dir == derived))

    rc, out = call([sys.executable,
                    os.path.join(BASE, "followup_section_foreign_wire.py"),
                    "--check", derived, "--root", REPO])
    lines.append("STEP4 cli_rc=%d last=%s"
                 % (rc, (out.strip().splitlines() or [""])[-1]))

    ok = (derived == "qa" and same and abs_dir == derived and rc == 0)
    lines.append("VERDICT LIVE-%s" % ("DERIVED" if ok else "MISMATCH"))
    text = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(OUT, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    print("readback=%s bytes=%d" % (back == text, len(text.encode("utf-8"))))
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())