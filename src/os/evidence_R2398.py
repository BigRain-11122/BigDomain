"""R2398 evidence: the suite ritual plus one read-only live capture."""

import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src", "os"))

import evidence_capture as EVC

report = EVC.capture(ROOT, "R2398",
                     "src/os/test_declaration_writer_dialect_preservation.py",
                     adjacent=["src/os/test_residue_triage_append.py",
                               "src/os/test_residue_triage_append_batch.py",
                               "src/os/test_declaration_writer_noop_parity.py"],
                     evidence="qa/declaration-writer-dialect-preservation-R2398.log")
sys.stdout.write(EVC.render(report) + "\n")

steps = [
    ("dialect", ["src/os/declaration_writer_dialect_preservation.py",
                 "--declaration", "state/residue_triage.json",
                 "--composed", "state/residue_triage.json"]),
    ("dialect-json", ["src/os/declaration_writer_dialect_preservation.py",
                      "--declaration", "state/residue_triage.json",
                      "--composed", "state/residue_triage.json", "--json"]),
    ("append-check", ["src/os/residue_triage_append.py", "--check",
                      "--round", "R2397"]),
    ("retire-refusal", ["src/os/residue_triage_entry_retire.py",
                        "--round", "R9999"]),
    ("renew-noop", ["src/os/residue_triage_head_renew.py", "--round",
                    "R2398"]),
]

lines = ["== LIVE CAPTURE R2398 (read-only on the real tree)\n"]
for name, args in steps:
    proc = subprocess.Popen([sys.executable] + args, cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    body = out.decode("utf-8", "replace")
    # one transport normalisation: a child's console stdout crosses a text
    # boundary, so CRLF is folded to LF and nothing else is touched
    body = body.replace("\r\n", "\n")
    lines.append("-- %s rc=%d\n%s" % (name, proc.returncode, body))
    if err:
        lines.append("-- %s stderr\n%s\n" % (name,
                                             err.decode("utf-8", "replace")))
with io.open(os.path.join(
        ROOT, "qa", "declaration-writer-dialect-preservation-live-R2398.log"),
        "w", encoding="utf-8", newline="\n") as handle:
    handle.write("".join(lines))
sys.stdout.write("live capture written\n")