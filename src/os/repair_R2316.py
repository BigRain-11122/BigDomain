"""R2316 battery repair: two real defects the R2315 tree carried.

(a) The R2315 reader-wire evidence was written through a shell
redirection, so all three files landed in the pwsh-capture dialect and
the qa writer census flagged them (suite reconcile-daily-census,
criterion cd7-live-real-tree exit=2 DRIFT-FLAG, 3 flags). This runner
re-executes the very same suite twice and the very same live reading,
and rewrites the three files through ONE python writer, utf-8 LF, no
BOM - regenerated, never transcoded, zero product/criteria change.

(b) The residue triage declaration pinned at R2310 covers 186 rounds
while the live stamp residue reads 187: round R2300 was carried as
untriaged debt (suite os-residue-triage AC-RTR6 FAIL). R2300 delivered
the gate_drift row (state/queue/tech.md:366 [done 2026-11-01 R2300],
commit b6bf3a38 read it green), so the entry is appended with that
evidence, until R2330, as a minimal text insertion that leaves every
existing entry and the file format byte-intact.

Usage: python src/os/repair_R2316.py
"""

import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
QA = os.path.join(ROOT, "qa")
SUITE = os.path.join("src", "os", "test_gate_decl_identity_wire.py")
WIRE = os.path.join("src", "os", "gate_decl_identity_wire.py")

A_LOG = "gate-decl-identity-wire-R2315-a.log"
B_LOG = "gate-decl-identity-wire-R2315-b.log"
LIVE_LOG = "gate-decl-identity-wire-live-R2315.log"

DECL = os.path.join(ROOT, "state", "residue_triage.json")


def run(argv):
    proc = subprocess.run([sys.executable] + argv, cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def write_once(path, text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip("\n") + "\n")


def criteria(text):
    return [line for line in text.splitlines()
            if line.startswith("PASS ") or line.startswith("FAIL ")]


def facts(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    return {"bytes": len(raw),
            "bom": raw.startswith(b"\xef\xbb\xbf"),
            "crlf": raw.count(b"\r\n"),
            "sha16": hashlib.sha256(raw).hexdigest()[:16].upper()}


def repair_evidence(out):
    bodies = []
    rcs = []
    for name in (A_LOG, B_LOG):
        rc, text = run([SUITE])
        rcs.append(rc)
        bodies.append(criteria(text))
        write_once(os.path.join(QA, name), text)
    same = bodies[0] == bodies[1]
    digest = hashlib.sha256(
        "\n".join(bodies[0]).encode("utf-8")).hexdigest()[:16].upper()
    out.append("SUITE rc=%s criteria=%d identical=%r sha16=%s"
               % (rcs, len(bodies[0]), same, digest))

    live = [WIRE, "--identity", "-", "--capability", "docker",
            "--reason", "R2316 re-read of the R2314 finding",
            "--declared-by", "R2316"]
    parts = []
    for argv in (live, live + ["--json"]):
        rc, text = run(argv)
        parts.append("rc=%d\n%s" % (rc, text.rstrip("\n")))
    write_once(os.path.join(QA, LIVE_LOG), "\n\n".join(parts))

    for name in (A_LOG, B_LOG, LIVE_LOG):
        out.append("%s %s" % (name, facts(os.path.join(QA, name))))
    return rcs, same


def triage(round_no, out):
    with open(DECL, "r", encoding="utf-8") as handle:
        text = handle.read()
    data = json.loads(text)
    rounds = [entry["round"] for entry in data["entries"]]
    if round_no in rounds:
        out.append("TRIAGE present round=%d no write" % round_no)
        return False
    body = json.dumps({
        "round": round_no,
        "status": "DELIVERED",
        "declared_by": "R2316",
        "reason": ("read at R2316 off the board: state/queue/tech.md:366 "
                   "carries [done 2026-11-01 R2300] for the gate_drift row "
                   "and commit b6bf3a38 ran the R2301 battery green on that "
                   "committed tree, so the round delivered; the accepted "
                   "stamp simply sat on a row that has since closed"),
        "until": 2330,
    }, ensure_ascii=False, indent=2)
    block = "\n".join("    " + line for line in body.splitlines())
    marker = "\n    }\n  ]\n}"
    tail = "\n" if text.endswith("\n") else ""
    body_text = text[:-1] if tail else text
    assert body_text.endswith(marker), "unexpected declaration tail"
    new = (body_text[:-len(marker)] + "\n    },\n" + block
           + "\n  ]\n}" + tail)
    with open(DECL, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(new)
    again = json.loads(new)
    out.append("TRIAGE appended round=%d entries %d->%d readback=%r"
               % (round_no, len(data["entries"]), len(again["entries"]),
                  again["entries"][-1]["round"] == round_no))
    return True


def main(argv=None):
    out = []
    rcs, same = repair_evidence(out)
    triage(2300, out)
    for line in out:
        print(line)
    ok = all(rc == 0 for rc in rcs) and same
    print("REPAIR %s" % ("OK" if ok else "RED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())