# live_R2402.py - one read-only live capture, one utf-8 LF writer.
# Reads the REAL tree through relative_import_publish_binding, proves the
# absolute face agrees with the parent law over the same files, and shows the
# relative spelling it now names on a fixture. Writes exactly one file.
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import export_publish_from_import_law as EPBW
import relative_import_publish_binding as RIPB

OUT = os.path.join(ROOT, "qa", "relative-import-publish-binding-live-R2402.log")
MODULE = os.path.join(BASE, "relative_import_publish_binding.py")

FIXTURE = (
    "import queue_floor_export_face as QFE\n"
    "import os\n"
    "\n"
    "EXPORT = os.path.join('docs', 'status-export.json')\n"
    "\n"
    "\n"
    "def flush(data):\n"
    "    QFE.apply(data, '.')\n"
    "    return publish('.', EXPORT, text='{}')\n"
)
RELATIVE_FIXTURE = "from .wire import publish\n" + FIXTURE


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


lines = []


def say(text):
    lines.append(text)


before = digest(MODULE)

report, code = RIPB.audit(SRC)
parent_report, parent_code = EPBW.audit(SRC)

say("RELATIVE IMPORT PUBLISH BINDING LIVE R2402")
say("real tree verdict=%s code=%d scanned=%d publishers=%d wire=%d "
    "foreign=%s unresolved=%s relative=%d no_publish=%d from_import=%d bare=%d"
    % (report["verdict"], code, report["scanned"], len(report["publishers"]),
       len(report["wire"]), ",".join(report["foreign"]) or "(none)",
       ",".join(report["unresolved"]) or "(none)", report["relative"],
       len(report["no_publish"]), report["from_import"], report["bare"]))
say("parent law over the same tree verdict=%s code=%d publishers=%d wire=%d "
    "foreign=%s unresolved=%s no_publish=%d from_import=%d bare=%d"
    % (parent_report["verdict"], parent_code,
       len(parent_report["publishers"]), len(parent_report["wire"]),
       ",".join(parent_report["foreign"]) or "(none)",
       ",".join(parent_report["unresolved"]) or "(none)",
       len(parent_report["no_publish"]), parent_report["from_import"],
       parent_report["bare"]))

world = tempfile.mkdtemp(prefix="ripb-live-")
path = os.path.join(world, "rel_pub.py")
with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(RELATIVE_FIXTURE)
fixture_report, fixture_code = RIPB.audit(world)
fixture_calls = RIPB.classify_script(RELATIVE_FIXTURE.splitlines(),
                                     "status-export.json",
                                     "closeout_export_parity_wire")
say("relative fixture verdict=%s code=%d publishers=%s relative=%d "
    "kind=%s module=%s state=%s line=%d"
    % (fixture_report["verdict"], fixture_code,
       ",".join(fixture_report["publishers"]) or "(none)",
       fixture_report["relative"], fixture_calls[0]["kind"],
       fixture_calls[0]["module"], fixture_calls[0]["state"],
       fixture_calls[0]["line"]))
parent_fixture, parent_fixture_code = EPBW.audit(world)
parent_calls = EPBW.classify_script(RELATIVE_FIXTURE.splitlines(),
                                    "status-export.json",
                                    "closeout_export_parity_wire")
say("same fixture through the parent law verdict=%s code=%d kind=%s state=%s"
    % (parent_fixture["verdict"], parent_fixture_code,
       parent_calls[0]["kind"], parent_calls[0]["state"]))

first = json.dumps(report, ensure_ascii=False)
second = json.dumps(RIPB.audit(SRC)[0], ensure_ascii=False)
say("json byte_stable=%s keys=%d" % (first == second, len(report)))
say("module digest before=%s after=%s unchanged=%s"
    % (before, digest(MODULE), before == digest(MODULE)))

body = "\n".join(lines).rstrip("\n") + "\n"
if os.path.exists(OUT):
    raise SystemExit("E_LIVE_OUTPUT_EXISTS %s" % OUT)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(body)
print("WROTE %s bytes=%d" % (OUT, len(body.encode("utf-8"))))
print(body, end="")
sys.exit(0 if code in (0, 2) and fixture_report["verdict"] == "RELATIVE"
         else 1)