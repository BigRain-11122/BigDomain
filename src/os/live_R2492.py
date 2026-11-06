"""R2492 live leg: the seed defect reproduced end to end on a real tree."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MODULE = os.path.join(HERE, "relative_package_presence_refusal.py")
OUT = "qa/relative-package-presence-refusal-live-R2492.log"

PUB = '''from .nosuchmodule import publish
import queue_floor_export_face as QFE
import os

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
    return publish(".", EXPORT, text="{}")
'''

root = tempfile.mkdtemp(prefix="rmpp-live-")
lines = ["LIVE LEG round=R2492 module=relative_package_presence_refusal.py"]
try:
    os.makedirs(os.path.join(root, "mypkg"))
    for name in ("mypkg/__init__.py", "mypkg/wire.py"):
        io.open(os.path.join(root, name), "w", encoding="ascii").write("")
    io.open(os.path.join(root, "rel_pub.py"), "w",
            encoding="ascii").write(PUB)

    def run(package):
        done = subprocess.run(
            [sys.executable, MODULE, "--check", "--root", root,
             "--package", package, "--wire", "mypkg.wire", "--json"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return done.returncode, done.stdout.decode("utf-8").strip(), \
            done.stderr.decode("utf-8").strip()

    rc_bad, out_bad, err_bad = run("nosuchpkg")
    rc_ok, out_ok, err_ok = run("mypkg")
    absent = json.loads(out_bad)
    carried = json.loads(out_ok)
    lines.append("tree=%s" % root)
    lines.append("declared=nosuchpkg rc=%d verdict=%s presence=%s "
                 "presence_corpus=%d refusal=%s missing_rows=%d"
                 % (rc_bad, absent["verdict"], absent["presence"],
                    absent["presence_corpus"], absent["refusal"],
                    len(absent["missing"])))
    lines.append("declared=mypkg rc=%d verdict=%s presence=%s "
                 "presence_carriers=%d missing_rows=%d missing_modules=%s"
                 % (rc_ok, carried["verdict"], carried["presence"],
                    carried["presence_carriers"], len(carried["missing"]),
                    ",".join(carried["missing_modules"])))
    lines.append("stderr_empty=%s" % (not err_bad and not err_ok))
    lines.append("VERDICT %s"
                 % ("PASS" if (rc_bad == 2 and absent["verdict"] == "NO-PACKAGE"
                               and absent["missing"] == []
                               and absent["refusal"] == "E_RMPP_NO_PACKAGE"
                               and rc_ok == 2
                               and carried["presence"] == "PRESENT"
                               and carried["missing_modules"] == ["mypkg.nosuchmodule"])
                    else "FAIL"))
finally:
    shutil.rmtree(root, ignore_errors=True)

text = "\n".join(lines) + "\n"
io.open(os.path.join(ROOT, OUT), "w", encoding="utf-8", newline="\n").write(text)
print(text)
