"""live_R2382 - the LIVE capture for the repin NOOP parity (R2382).

Runs the parity and both CLIs over the REAL tree and writes one utf-8 LF
evidence body through a single writer (never a shell redirection). The live
declaration is only ever READ: its digest is taken before and after and the
body says so.

ASCII source, stdlib only, no clock, no network.
"""

import hashlib
import io
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import repin_noop_parity as RNP  # noqa: E402
import residue_triage as RT  # noqa: E402

QUEUE_RUN = "qa/repin-noop-parity-live-R2382.log"
ROUND = "R2382"
UNTIL = "R2400"
REASON = "live parity reading at R2382"


def digest(path):
    try:
        with io.open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()[:16]
    except (IOError, OSError):
        return "ABSENT"


def run(module, args):
    proc = subprocess.run([sys.executable, os.path.join(BASE, module)]
                          + list(args) + ["--root", REPO],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def main():
    decl = os.path.join(REPO, RT.DECLARATION_PATH)
    before = digest(decl)

    dry = RNP.check(REPO, ROUND, UNTIL, REASON)
    drop = RNP.check(REPO, ROUND, UNTIL, REASON, True)
    text_one = RNP.render(dry) + "\n"
    text_two = RNP.render(dry) + "\n"
    json_one = RNP.to_json(dry)
    json_two = RNP.to_json(dry)

    ship_rc, ship_out = run("residue_triage_repin.py", [
        "--round", ROUND, "--until", UNTIL, "--reason", REASON,
        "--drop-unmatched"])
    wire_rc, wire_out = run("residue_triage_repin_idempotent.py", [
        "--round", ROUND, "--until", UNTIL, "--reason", REASON,
        "--drop-unmatched"])
    cli_rc, cli_out = run("repin_noop_parity.py", [
        "--check", "--round", ROUND, "--until", UNTIL, "--reason", REASON])
    after = digest(decl)

    body = []
    body.append("LIVE repin noop parity round=%s until=%s" % (ROUND, UNTIL))
    body.append("STEP1 parity=%s first_diff=%s shipped=%s wire=%s"
                % (dry["verdict"], dry["first_diff"], dry["shipped"],
                   dry["wire"]))
    body.append("STEP2 shipped_code=%s wire_code=%s"
                % (dry["shipped_code"], dry["wire_code"]))
    body.append("STEP3 drop_unmatched parity=%s shipped=%s wire=%s"
                % (drop["verdict"], drop["shipped"], drop["wire"]))
    body.append("STEP4 shipped CLI rc=%d line=%s"
                % (ship_rc, ship_out.strip().splitlines()[0]
                   if ship_out.strip() else "(none)"))
    body.append("STEP5 wire CLI rc=%d line=%s"
                % (wire_rc, wire_out.strip().splitlines()[0]
                   if wire_out.strip() else "(none)"))
    body.append("STEP6 parity CLI rc=%d line=%s"
                % (cli_rc, cli_out.strip().splitlines()[0]
                   if cli_out.strip() else "(none)"))
    body.append("STEP7 text_stable=%s json_stable=%s"
                % (text_one == text_two, json_one == json_two))
    body.append("STEP8 declaration_digest %s -> %s unchanged=%s"
                % (before, after, before == after))
    body.append("STEP9 compact=%s"
                % json.dumps(json.loads(json_one), sort_keys=True))
    text = "\n".join(body) + "\n"

    path = os.path.join(REPO, QUEUE_RUN)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(path, "rb") as handle:
        raw = handle.read()
    print("WROTE %s bytes=%d crlf=%d readback=%s"
          % (QUEUE_RUN, len(raw), raw.count(b"\r\n"),
             raw.decode("utf-8") == text))
    print(text)
    return 0 if before == after and dry["verdict"] in RNP.VERDICTS else 1


if __name__ == "__main__":
    sys.exit(main())