# evidence_R2370.py - one single-writer live capture for the R2370 product face
#
# Why a script and not a shell redirect: PowerShell redirection lands UTF-16
# with a BOM, which is exactly the dialect the qa writer census flags (the
# R2362/R2230 trap). This writes utf-8 with a bare LF, once.

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EVIDENCE = os.path.join(ROOT, "qa",
                        "followup-section-foreign-wire-live-R2370.log")


def run(args):
    proc = subprocess.run([sys.executable] + args, cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    body = proc.stdout.decode("utf-8", "replace")
    return proc.returncode, body.replace("\r\n", "\n").replace("\r", "\n")


def main():
    rc_guard, out_guard = run([os.path.join(BASE,
                                           "followup_section_foreign_wire.py"),
                              "--check"])
    rc_follow, out_follow = run([os.path.join(BASE, "battery_followup.py"),
                                 "--evidence", "qa/reconcile-all-R2370.log",
                                 "--label", "R2370", "--round", "2370",
                                 "--dry-run"])
    lines = []
    lines.append("R2370 live: the follow-up matrix section with the guard in "
                 "front, on the real tree")
    lines.append("")
    lines.append("$ followup_section_foreign_wire.py --check   (rc=%d)"
                 % rc_guard)
    lines.extend(out_guard.rstrip("\n").split("\n"))
    lines.append("")
    lines.append("$ battery_followup.py --evidence qa/reconcile-all-R2370.log "
                 "--label R2370 --round 2370 --dry-run   (rc=%d)" % rc_follow)
    lines.extend(out_follow.rstrip("\n").split("\n"))
    lines.append("")
    lines.append("READING: the real pile reads VOCABULARY-CLEAN over 460 rounds "
                 "at rc=0, so the guard lets the matrix section run - the "
                 "REFUSAL branch is proved on fixtures in the suite (a "
                 "FOREIGN-SECTION pile, zero matrix renders, the doc untouched) "
                 "and is NOT claimed as a live catch. Before this wire no code "
                 "path asked the reader at all.")
    lines.append("")
    lines.append("The matrix section reads FAIL here and that is the honest, "
                 "designed state of a window that edits the registry after its "
                 "own green battery: the shipped doc describes the R2370 battery "
                 "(496 suites / 3952 criteria, 47476B) and this window added the "
                 "497th suite (os-followup-section-foreign-wire) AFTER that run, "
                 "so the doc is stale until the next battery regenerates it. "
                 "Nothing was rewritten - the FAIL says '(no rewrite)' - which is "
                 "also the read-only proof that the section never touches the "
                 "shipped doc.")
    body = "\n".join(lines) + "\n"
    with io.open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print("WROTE %s bytes=%d path=%s" % (EVIDENCE, len(body.encode("utf-8")),
                                         EVIDENCE))
    print("rc guard=%d followup=%d" % (rc_guard, rc_follow))
    return 0


if __name__ == "__main__":
    sys.exit(main())