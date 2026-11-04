import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, "src", "os"))

import comma_binding_identity_face_compare as PICIC  # noqa: E402
import export_publish_wire_identity as EPWI  # noqa: E402

env = dict(os.environ)
env["PYTHONIOENCODING"] = "utf-8"
done = subprocess.run(
    [sys.executable,
     os.path.join("src", "os", "comma_binding_identity_face_compare.py"),
     "--check", "--root", os.path.join("src", "os"), "--json"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
raw = done.stdout.decode("utf-8", "replace")
if not raw.strip():
    print("child rc=%d stderr=%s"
          % (done.returncode, done.stderr.decode("utf-8", "replace")[:400]))
    raise SystemExit(1)
data = json.loads(raw)

lines = ["LIVE R2444 real tree src/os rc=%d" % done.returncode]
lines.append("verdict=%s faces=%d differences=%d rows=%d"
             % (data["verdict"], len(data["faces"]),
                len(data["differences"]),
                sum(len(face["rows"]) for face in data["faces"])))
for face in data["faces"]:
    lines.append(
        "face=%s verdict=%s publishers=%d rows=%d keys=%d seams=%s"
        % (face["face"], face["verdict"], len(face["publishers"]),
           len(face["rows"]),
           len(face["rows"][0]) if face["rows"] else 0,
           ",".join("%s:%d" % (row["seam"], row["calls"])
                    for row in face["seams"]) or "(none)"))

original = EPWI.audit


def drifted(root, export_name, owner, wire_module):
    report, code = original(root, export_name, owner, wire_module)
    for row in report["detail"]:
        if row["state"] == "WIRE":
            row["module"] = "drifted_wire"
            break
    return report, code


EPWI.audit = drifted
try:
    probe, probe_code = PICIC.audit(os.path.join("src", "os"),
                                    "status-export.json",
                                    "queue_floor_export_face",
                                    "closeout_export_parity_wire")
finally:
    EPWI.audit = original
lines.append(
    "MEASURED LIMIT one identity row module rewritten to drifted_wire under "
    "an unchanged WIRE verdict reads verdict=%s rc=%d differences=%d - the "
    "compare reads verdicts and publisher sets, not per-line rows"
    % (probe["verdict"], probe_code, len(probe["differences"])))
text = "\n".join(lines) + "\n"
path = os.path.join("qa", "comma-binding-identity-face-compare-live-R2444.log")
io.open(path, "w", encoding="utf-8", newline="\n").write(text)
print(text)
print("bytes=%d crlf=%d" % (len(text.encode("utf-8")),
                            text.encode("utf-8").count(b"\r\n")))