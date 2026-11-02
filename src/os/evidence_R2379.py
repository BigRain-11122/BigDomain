# evidence_R2379.py - the live capture for the residue batch status face
# One utf-8 LF single writer with a read-back, no shell redirection.
# Pure ASCII, stdlib only, no clock, no network.

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)

FACE = os.path.join(BASE, "residue_batch_status_face.py")
BATCH = os.path.join(BASE, "residue_triage_append_batch.py")
EVIDENCE = os.path.join(REPO, "qa",
                        "residue-batch-status-face-live-R2379.log")


def run(module, args):
    proc = subprocess.Popen([sys.executable, module] + args,
                            cwd=REPO, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode, out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


def main():
    lines = ["LIVE R2379 residue_batch_status_face on the real tree"]

    rc_map, out_map, _ = run(FACE, ["--check"])
    first = out_map.splitlines()[0] if out_map else ""
    rounds = "-"
    for token in first.split():
        if token.startswith("rounds="):
            rounds = token.split("=", 1)[1]
    lines.append("STEP1 map rc=%d %s" % (rc_map, first))

    rc_json_a, out_a, _ = run(FACE, ["--check", "--json"])
    rc_json_b, out_b, _ = run(FACE, ["--check", "--json"])
    lines.append("STEP2 json rc=%d,%d byte_stable=%s"
                 % (rc_json_a, rc_json_b, "True" if out_a == out_b else
                    "False"))

    known = out_map.splitlines()[1].split()[1] if out_map else "-"
    rc_known, out_known, _ = run(FACE, ["--check", "--round", known])
    known_line = out_known.splitlines()[0] if out_known else ""
    lines.append("STEP3 known %s rc=%d %s"
                 % (known, rc_known, known_line))

    rc_absent, out_absent, _ = run(FACE, ["--check", "--round", "R9999"])
    absent_line = out_absent.splitlines()[0] if out_absent else ""
    lines.append("STEP4 absent rc=%d %s"
                 % (rc_absent, absent_line))

    rc_batch, out_batch, _ = run(BATCH, ["--check", "--round", "R2379"])
    batch_line = out_batch.splitlines()[0] if out_batch else ""
    carries = ("statuses=" in batch_line and "statuses=-" not in batch_line)
    lines.append("STEP5 batch-check rc=%d carries_statuses=%s"
                 % (rc_batch, "True" if carries else "False"))
    lines.append("STEP5 line %s" % batch_line[:400])

    verdict = "LIVE-FACE"
    if rc_map != 0 or out_a != out_b or rc_absent != 2 or not carries:
        verdict = "LIVE-INCOMPLETE"
    lines.append("VERDICT %s rounds=%s" % (verdict, rounds))

    body = "\n".join(lines) + "\n"
    payload = body.encode("utf-8")
    with open(EVIDENCE, "wb") as handle:
        handle.write(payload)
    with open(EVIDENCE, "rb") as handle:
        back = handle.read()
    readback = back == payload
    sys.stdout.write(body)
    sys.stdout.write("WROTE %s bytes=%d readback=%s crlf=%d\n"
                     % (EVIDENCE.replace(REPO + os.sep, "").replace(
                         os.sep, "/"), len(payload), "True" if readback else
                        "False", back.count(b"\r")))
    return 0 if readback and verdict == "LIVE-FACE" else 2


if __name__ == "__main__":
    sys.exit(main())