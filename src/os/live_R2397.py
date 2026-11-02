"""Live capture for the R2397 parity-consumer wire (single utf-8 LF writer).

Runs the shipped consumer CLI and the acting path on the REAL tree, then the
same consumer on two fixture worlds (a blind one and a splitting one), and
writes every line through one writer. Writes nothing else.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
OUT = os.path.join(REPO, "qa",
                   "review-window-guard-parity-consumer-wire-live-R2397.log")

MODULE = os.path.join(BASE, "review_window_guard_parity_consumer_wire.py")
EXEMPT = os.path.join(BASE, "exempt_review.py")


def run(args):
    proc = subprocess.run([sys.executable] + args, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    body = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, body.replace("\r\n", "\n").replace("\r", "\n")


def blind_world():
    world = tempfile.mkdtemp(prefix="bigdomain-rwpc-live-")
    os.makedirs(os.path.join(world, "state"))
    with io.open(os.path.join(world, "state", "review_window.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write("{not json")
    return world


def clean_world():
    world = tempfile.mkdtemp(prefix="bigdomain-rwpc-live-")
    os.makedirs(os.path.join(world, "state", "queue"))
    body = {
        "window": 20,
        "declared_by": "R2300",
        "reason": "pinned",
        "declarations": [{"window": 20, "declared_by": "R2300",
                          "reason": "pinned"}],
    }
    with io.open(os.path.join(world, "state", "review_window.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(body, indent=2))
    with io.open(os.path.join(world, "state", "queue",
                              "prefix_exempt.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"exemptions": [
            {"queue": "tech", "identity": "seed-a", "declared": "R2290",
             "reason": "accepted as it stands"}]}, indent=2))
    return world


def main():
    lines = []
    worlds = []

    rc, body = run([MODULE, "--check"])
    lines.append("[1] real tree consumer --check rc=%d" % rc)
    lines.append(body.rstrip())

    rc, body = run([EXEMPT, "--round", "R2397", "--window-from-declaration"])
    lines.append("[2] real tree exempt_review --window-from-declaration "
                 "rc=%d" % rc)
    lines.append(body.rstrip())

    blind = blind_world()
    worlds.append(blind)
    rc, body = run([MODULE, "--check", "--root", blind])
    lines.append("[3] blind fixture (unreadable declaration) rc=%d" % rc)
    lines.append(body.rstrip())

    clean = clean_world()
    worlds.append(clean)
    rc, body = run([MODULE, "--check", "--root", clean])
    lines.append("[4] clean fixture (informed agreement) rc=%d" % rc)
    lines.append(body.rstrip())

    rc, body = run([EXEMPT, "--root", clean, "--round", "R2397",
                    "--window-from-declaration"])
    lines.append("[5] clean fixture through the acting path rc=%d" % rc)
    lines.append(body.rstrip())

    rc, body = run([MODULE, "--check", "--json"])
    lines.append("[6] real tree --json rc=%d" % rc)
    lines.append(body.rstrip())

    for world in worlds:
        shutil.rmtree(world, ignore_errors=True)

    text = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    raw = open(OUT, "rb").read()
    sys.stdout.write("WROTE %s bytes=%d crlf=%d bare_cr=%d\n"
                     % (OUT, len(raw), raw.count(b"\r\n"),
                        raw.count(b"\r") - raw.count(b"\r\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())