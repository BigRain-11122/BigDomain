"""R2722 one-off: re-run the write-sensitive suites INDIVIDUALLY on the final
committed tree, through the shipped runner invocation dialect.

Why this exists: the R2721 launch window left no receipt line, so the R2614
discipline is OWED. A green battery verdict is admissible only beside an
individual re-run of the suites that write the very artifacts this window
touches.

Invocation is NOT reinvented: the modules are launched by the shipped
reconcile_all.run_cmd (PYTHONIOENCODING=utf-8 child pipes, utf-8 decode,
cwd=src/sandbox, per-suite timeout cap), and the names are looked up in the
shipped registry rather than typed as paths.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, SANDBOX)

import reconcile_all as R  # noqa: E402

NAMES = [
    "os-matrix-stamp-compare",
    "os-matrix-stamp-provenance-line",
    "os-matrix-stamp-from-liveness",
    "os-matrix-evidence-pile-consistency",
    "os-suite-matrix-reconcile",
    "os-suite-matrix-reconcile-evidence-face",
    "os-export-consistency-queue-face",
    "os-closeout-export-parity-text-binding",
    "os-single-append-status-face",
    "os-state-seq-archive",
    "os-state-io",
    "os-ledger-line-shape-guard",
    "os-ledger-lines",
    "os-queue-head-delivered",
    "os-queue-floor",
]

EVIDENCE = os.path.join(ROOT, "qa", "write-sensitive-R2722.log")

HEADER = [
    "WRITE-SENSITIVE RERUN R2722",
    "leg: battery-R2721 (RUNNER PASS 671/671, 3961.6s), adopted at R2722",
    "commits under the leg: the R2720 closeout 691f66e8, the R2721 launch "
    "closeout a2b37732 and this window own befed0ed",
    "tree: final committed tree at HEAD befed0ed (measured after the closeout "
    "commit)",
    "suites: 15, the same set R2709 pinned",
    "",
]


def main():
    table = {t[0]: t[1] for t in R.SUITES}
    missing = [n for n in NAMES if n not in table]
    if missing:
        print("REFUSED missing_from_registry=%r" % (missing,))
        return 3

    out_lines = list(HEADER)
    rows = []
    for name in NAMES:
        rel = table[name]
        path = os.path.abspath(os.path.join(SANDBOX, rel))
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
    with io.open(EVIDENCE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out_lines))
        fh.write("\nSUMMARY %s green=%d red=%d verdict=%s\n"
                 % ("PASS", len(rows) - len(bad), len(bad),
                    "PASS" if not bad else "FAIL"))
    for name, rc, npass, nfail in rows:
        print("SUITE %-45s rc=%d pass=%d fail=%d"
              % (name, rc, npass, nfail))
    print("EVIDENCE %s bytes=%d"
          % (os.path.basename(EVIDENCE), os.path.getsize(EVIDENCE)))
    print("SUMMARY %s green=%d red=%d"
          % ("PASS" if not bad else "FAIL", len(rows) - len(bad), len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
