"""R2472 repair: three R2471 evidence captures were written as PowerShell
UTF-16 (class=ps-utf16) instead of one UTF-8 LF single writer.

The repair is dialect only: each file is decoded, its line set is proved
identical to the decoded original through run_identity.normalize, and the
file is rewritten as UTF-8 LF with one atomic os.replace plus a byte
read-back. No criterion and no census baseline is widened.

Usage:
  python src/os/repair_R2472.py            (dry run, writes nothing)
  python src/os/repair_R2472.py --execute  (writes)
"""
import argparse
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import run_identity  # noqa: E402

QA = os.path.join(REPO, "qa")
FILES = [
    "hub-ledger-R2471-a.log",
    "hub-ledger-R2471-b.log",
    "hub-ledger-live-R2471.log",
]


def plan_one(path):
    raw = open(path, "rb").read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16")
        dialect = "utf-16-bom"
    elif b"\x00" in raw[:400]:
        text = raw.decode("utf-16-le")
        dialect = "utf-16-no-bom"
    else:
        text = raw.decode("utf-8-sig")
        dialect = "utf-8"
    normalised = run_identity.normalize(text)
    orig_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while orig_lines and orig_lines[-1] == "":
        orig_lines.pop()
    norm_lines = normalised.split("\n")
    while norm_lines and norm_lines[-1] == "":
        norm_lines.pop()
    same_payload = orig_lines == norm_lines
    return {
        "path": path,
        "dialect": dialect,
        "before": len(raw),
        "after": len(normalised.encode("utf-8")),
        "payload_equal": same_payload,
        "text": normalised,
        "lines": len(normalised.splitlines()),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args(argv)

    plans = []
    bad = 0
    for name in FILES:
        p = os.path.join(QA, name)
        if not os.path.exists(p):
            print("MISSING %s" % name)
            bad += 1
            continue
        plan = plan_one(p)
        plans.append(plan)
        print("PLAN %s dialect=%s before=%dB after=%dB lines=%d payload_equal=%s"
              % (name, plan["dialect"], plan["before"], plan["after"],
                 plan["lines"], plan["payload_equal"]))
        if not plan["payload_equal"]:
            bad += 1

    if bad:
        print("REFUSED payload not provably equal on %d file(s)" % bad)
        return 3
    if not args.execute:
        print("DRY-RUN wrote=no files=%d" % len(plans))
        return 0

    for plan in plans:
        tmp = plan["path"] + ".tmp"
        payload = plan["text"].encode("utf-8")
        with open(tmp, "wb") as fh:
            fh.write(payload)
        os.replace(tmp, plan["path"])
        back = open(plan["path"], "rb").read()
        ok = back == payload
        crlf = back.count(b"\r\n")
        print("WROTE %s bytes=%d readback=%s crlf=%d"
              % (os.path.basename(plan["path"]), len(back), ok, crlf))
        if not ok or crlf:
            print("FAILED read-back proof")
            return 3
    print("EXECUTED files=%d" % len(plans))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())