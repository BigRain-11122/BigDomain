"""Parameterised R2614 write-sensitive re-run (replaces the per-window copies).

Why this exists: R2620, R2722 and R2724 each carried their own verbatim copy of
the same runner to re-run the fifteen suites that write the very artifacts a
closeout touches, and only the header and the evidence path ever differed. The
suite SET is the thing that matters and it was already provenance-pinned by the
R2724 module, so this tool IMPORTS that set instead of retyping it: one
selection, one runner dialect, one evidence writer, and the window facts passed
on the command line.

The invocation is not reinvented either: suites are launched by the shipped
reconcile_all.run_cmd (utf-8 child pipes, cwd=src/sandbox, per-suite cap) and
their paths come from the shipped registry rather than being typed as paths.

Usage:
  python src/os/verify_writesensitive.py --leg battery-R2725 \
      --head <sha> --evidence qa/write-sensitive-R2725.log [--commits "..."]

Refusal contract: a name that the shipped registry does not carry stops the run
BEFORE any suite fires (rc=3), so a stale selection can never look green.
"""

import argparse
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, SANDBOX)
sys.path.insert(0, BASE)

import reconcile_all as R  # noqa: E402

# The pinned selection lives with the window that pinned it. Imported, not
# copied: a second list here would be a second truth.
from verify_writesensitive_R2724 import NAMES  # noqa: E402


def parse_args(argv):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--leg", required=True,
                    help="leg label, e.g. battery-R2725")
    ap.add_argument("--head", required=True,
                    help="committed tree sha the suites are re-run on")
    ap.add_argument("--evidence", required=True,
                    help="evidence path relative to the repo root")
    ap.add_argument("--commits", default="",
                    help="free text naming the commits that landed under the leg")
    return ap.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    table = {t[0]: t[1] for t in R.SUITES}
    missing = [n for n in NAMES if n not in table]
    if missing:
        print("REFUSED missing_from_registry=%r" % (missing,))
        return 3

    header = [
        "WRITE-SENSITIVE RERUN (%s)" % args.leg,
        "head: %s" % args.head,
        "commits under the leg: %s" % (args.commits or "not named"),
        "suites: %d, the set the shipped R2724 module pinned" % len(NAMES),
        "",
    ]

    out_lines = list(header)
    rows = []
    for name in NAMES:
        path = os.path.abspath(os.path.join(SANDBOX, table[name]))
        rc, out = R.run_cmd([sys.executable, path], cwd=SANDBOX,
                            timeout=R.suite_timeout(name))
        body = out if isinstance(out, str) else ""
        lines = body.splitlines()
        npass = sum(1 for l in lines if l.startswith("PASS "))
        nfail = sum(1 for l in lines if l.startswith("FAIL "))
        out_lines.append("=== SUITE %s rc=%d pass_lines=%d fail_lines=%d"
                         % (name, rc, npass, nfail))
        out_lines.extend(lines)
        out_lines.append("")
        rows.append((name, rc, npass, nfail))

    bad = [r for r in rows if r[1] != 0 or r[3] != 0]
    evidence = os.path.join(ROOT, args.evidence)
    with io.open(evidence, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out_lines))
        fh.write("\nSUMMARY %s green=%d red=%d verdict=%s\n"
                 % ("PASS", len(rows) - len(bad), len(bad),
                    "PASS" if not bad else "FAIL"))
    for name, rc, npass, nfail in rows:
        print("SUITE %-45s rc=%d pass=%d fail=%d"
              % (name, rc, npass, nfail))
    print("EVIDENCE %s bytes=%d" % (args.evidence, os.path.getsize(evidence)))
    print("SUMMARY %s green=%d red=%d"
          % ("PASS" if not bad else "FAIL", len(rows) - len(bad), len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
