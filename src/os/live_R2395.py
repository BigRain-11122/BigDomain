"""Live capture for runner_suite_timeout_headroom on the REAL tree (R2395).

Read-only by construction: the module under test opens evidence for reading.
This script proves the reading on today's qa pile, the byte-stability of the
--json face, that the band fires on a REAL measured suite when the cap is
tightened, the two refusal exits, and that the module bytes did not move.

One writer, utf-8, LF, never a shell redirection.
"""

import hashlib
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
MODULE = os.path.join(BASE, "runner_suite_timeout_headroom.py")
OUT = os.path.join(REPO, "qa", "runner-suite-timeout-headroom-live-R2395.log")


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run(args):
    proc = subprocess.Popen([sys.executable, MODULE] + args,
                            cwd=REPO,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _err = proc.communicate()
    text = out.decode("utf-8", "replace").replace("\r\n", "\n")
    return proc.returncode, text


def main():
    lines = ["LIVE runner_suite_timeout_headroom R2395"]
    before = digest(MODULE)

    rc, body = run(["--check", "--root", REPO])
    tail = [line for line in body.splitlines() if line.startswith("VERDICT")]
    lines.append("STEP1 real pile rc=%d %s"
                 % (rc, tail[0] if tail else "NO VERDICT"))

    rc_json_a, json_a = run(["--check", "--root", REPO, "--json"])
    rc_json_b, json_b = run(["--check", "--root", REPO, "--json"])
    lines.append("STEP2 json rc=%d/%d stable=%s bytes=%d"
                 % (rc_json_a, rc_json_b, json_a == json_b,
                    len(json_a.encode("utf-8"))))

    rc_tight, tight = run(["--check", "--root", REPO, "--cap", "200"])
    band = [line for line in tight.splitlines()
            if line.startswith("BAND ") and " 60%" not in line]
    lines.append("STEP3 tightened cap=200 band_lines=%d named=%s"
                 % (len(band), band[0] if band else "NONE"))

    rc_reg, _body = run(["--check", "--root", REPO,
                         "--runner", os.path.join(REPO, "no-such-runner.py")])
    rc_flag, flag_body = run(["--check", "--nope"])
    first_flag = flag_body.splitlines()[0] if flag_body else ""
    lines.append("STEP4 refusals registry_rc=%d flag_rc=%d flag_code=%s"
                 % (rc_reg, rc_flag, first_flag.split(":")[0]))

    after = digest(MODULE)
    lines.append("STEP5 module_digest_unchanged=%s" % (before == after))
    lines.append("VERDICT LIVE-READONLY" if before == after else
                 "VERDICT LIVE-MUTATED")

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")
    print("\n".join(lines))
    print("evidence=%s bytes=%d" % (os.path.basename(OUT),
                                    os.path.getsize(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())