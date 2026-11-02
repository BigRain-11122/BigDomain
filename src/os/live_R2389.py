"""live_R2389 - the read-only live capture for the declaration NOOP seam.

Runs on the REAL tree and writes its own evidence through one utf-8 LF writer.
Nothing here writes to a declaration: every leg is a reading, so the tree is
proved unchanged by a digest taken before and after.
"""

import hashlib
import io
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import declaration_writer_noop_parity as DWNP  # noqa: E402
import residue_triage as RT  # noqa: E402

OUT = os.path.join(ROOT, "qa", "declaration-writer-noop-parity-live-R2389.log")
DECL = os.path.join(ROOT, RT.DECLARATION_PATH)


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run(module, args):
    argv = [sys.executable, os.path.join(BASE, module)] + list(args)
    proc = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace").strip()


def main():
    before = digest(DECL)
    lines = []
    with io.open(DECL, "rb") as handle:
        raw = handle.read()
    report = DWNP.compare(DECL, raw)
    lines.append("STEP1 compare_the_declaration_with_its_own_bytes verdict=%s "
                 "dialect=%s raw_equal=%s"
                 % (report["verdict"], report["dialect"],
                    "yes" if report["raw_equal"] else "no"))
    lines.append(DWNP.one_line(report))
    rc, body = run("residue_triage_append.py",
                   ["--check", "--round", "R2389", "--json"])
    lines.append("STEP2 append_check rc=%d %s" % (rc, body.splitlines()[0]
                                                  if body else "-"))
    rc, body = run("residue_triage_head_renew.py",
                   ["--round", "R2389", "--json"])
    lines.append("STEP3 renew_dry_run rc=%d %s"
                 % (rc, body.splitlines()[0] if body else "-"))
    rc, body = run("residue_triage_entry_retire.py",
                   ["--round", "R2389", "--json"])
    lines.append("STEP4 retire_dry_run rc=%d %s"
                 % (rc, body.splitlines()[0] if body else "-"))
    rc, body = run("declaration_writer_noop_parity.py",
                   ["--compare", DECL, "--composed", DECL])
    lines.append("STEP5 cli_self_compare rc=%d %s" % (rc, body))
    after = digest(DECL)
    lines.append("STEP6 declaration_digest before=%s after=%s unchanged=%s"
                 % (before[:16], after[:16],
                    "yes" if before == after else "no"))
    lines.append("VERDICT LIVE-READ-ONLY" if before == after
                 else "VERDICT TREE-MOVED")
    body_text = "\n".join(lines).replace("\r\n", "\n").replace("\r", "\n")
    with io.open(OUT, "wb") as handle:
        handle.write((body_text.rstrip("\n") + "\n").encode("utf-8"))
    sys.stdout.write(body_text + "\n")
    return 0 if before == after else 2


if __name__ == "__main__":
    sys.exit(main())