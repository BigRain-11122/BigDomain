# live_R2400.py - the live leg for the from-import publish law (R2400).
# Read-only: it runs the two CLIs and one fixture world and writes ONE utf-8
# LF log through one writer. ASCII source, stdlib only, no clock, no network.
import io
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)
LOG = os.path.join(ROOT, "qa", "export-publish-from-import-law-live-R2400.log")
LAW = os.path.join(BASE, "export_publish_from_import_law.py")
IDENTITY = os.path.join(BASE, "export_publish_wire_identity.py")

FIXTURE = '''from closeout_export_parity_wire import publish
import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")


def flush(data):
    QFE.apply(data, ".")
    return publish(".", EXPORT, text="{}")
'''

FOREIGN = FIXTURE.replace("from closeout_export_parity_wire import publish",
                          "from some_other_wire import publish")


def run(argv):
    done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    body = done.stdout.decode("utf-8", "replace").rstrip("\r\n")
    err = done.stderr.decode("utf-8", "replace").rstrip("\r\n")
    head = "rc=%d" % done.returncode
    return head + ("\n" + body if body else "") + ("\n" + err if err else "")


def world(text):
    root = tempfile.mkdtemp(prefix="epbw-live-")
    with io.open(os.path.join(root, "publisher.py"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return root


def main():
    real = os.path.join("src", "os")
    fixture = world(FIXTURE)
    foreign = world(FOREIGN)
    parts = [
        "LIVE R2400 export_publish_from_import_law (read-only)",
        "== NEW LAW over the REAL tree (%s)" % real,
        run([sys.executable, LAW, "--check", "--root", real]),
        "== IDENTITY over the same tree (attribute reading must not move)",
        run([sys.executable, IDENTITY, "--check", "--root", real]),
        "== NEW LAW over a from-import fixture (must read WIRE)",
        run([sys.executable, LAW, "--check", "--root", fixture, "--json"]),
        "== NEW LAW over a from-import fixture bound to another module",
        run([sys.executable, LAW, "--check", "--root", foreign]),
        "== IDENTITY over the same foreign fixture (must now read FOREIGN)",
        run([sys.executable, IDENTITY, "--check", "--root", foreign]),
    ]
    body = "\n".join(parts) + "\n"
    with io.open(LOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())