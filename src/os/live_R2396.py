"""R2396 live capture: the tool argument on the REAL tree, one writer, utf-8 LF.

Measures, not asserts:
  STEP1 a BARE real log name is placed in the pile it lives in, and the
        argument handed to the tool is that pile plus the basename
  STEP2 the same name WITH a directory is handed through byte for byte
  STEP3 both halves resolve to the SAME file, and the bare name alone does
        not resolve under the root (the R2386 defect, measured)
  STEP4 a name that lives nowhere refuses at exit 2 before any tool call
  STEP5 the guard reads the real pile at its published verdict
  STEP6 the module digest is unchanged before and after the readings

Stdlib only, ASCII source, no clock, no network. Writes one evidence file.
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import followup_section_foreign_wire as FSFW  # noqa: E402
import matrix_evidence_pile_consistency as MEPC  # noqa: E402

REPO = os.path.dirname(os.path.dirname(BASE))
BARE = "reconcile-all-R2394-retry.log"
NAMED = "qa/" + BARE
MODULE = os.path.join(BASE, "matrix_evidence_pile_consistency.py")
OUT = os.path.join(REPO, "qa", "matrix-evidence-pile-consistency-live-R2396.log")


def digest():
    import hashlib
    with open(MODULE, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


def call(cmd):
    proc = subprocess.run(cmd, cwd=REPO, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def cli(args):
    return call([sys.executable, MODULE] + args)


def main():
    before = digest()
    lines = []

    placed = MEPC.placement(BARE, REPO)
    lines.append("STEP1 evidence=%s pile=%s argument=%s verdict=%s"
                 % (BARE, placed["pile"], placed["argument"],
                    placed["verdict"]))

    named = MEPC.tool_argument(NAMED, REPO)
    lines.append("STEP2 evidence=%s argument=%s unchanged=%s"
                 % (NAMED, named, named == NAMED))

    tool_side = os.path.normpath(os.path.join(REPO, placed["argument"]))
    old_side = os.path.normpath(os.path.join(REPO, BARE))
    lines.append("STEP3 same_file=%s tool_exists=%s bare_at_root=%s"
                 % (placed["same_file"], os.path.isfile(tool_side),
                    os.path.isfile(old_side)))

    rc_missing, out_missing = cli(["--check", "reconcile-all-R0000.log",
                                  "--root", REPO])
    lines.append("STEP4 missing_rc=%d code_line=%s"
                 % (rc_missing,
                    (out_missing.strip().splitlines() or ["-"])[-1]))

    guard = FSFW.guard(REPO, placed["pile"])
    rc_placed, out_placed = cli(["--check", BARE, "--root", REPO])
    lines.append("STEP5 cli_rc=%d guard=%s reading=%s"
                 % (rc_placed, guard["verdict"],
                    (out_placed.strip().splitlines() or ["-"])[0]))

    after = digest()
    lines.append("STEP6 digest_before=%s digest_after=%s unchanged=%s"
                 % (before, after, before == after))

    ok = (placed["verdict"] == MEPC.PLACED
          and placed["pile"] == "qa"
          and placed["argument"] == os.path.join("qa", BARE)
          and placed["same_file"] is True
          and os.path.isfile(tool_side)
          and not os.path.isfile(old_side)
          and named == NAMED
          and rc_missing == 2
          and MEPC.E_MEPC_UNPLACEABLE not in out_missing
          and rc_placed == 0
          and guard["code"] == ""
          and before == after)
    lines.append("VERDICT LIVE-%s" % ("ALIGNED" if ok else "MISMATCH"))
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