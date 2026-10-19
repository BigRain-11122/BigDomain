# fold_R2045.py - compose fold R573 summary line (token catalog
# mechanically extracted via LT.PAT from the actual tail-5
# window lines, narrative read from
# logs/tmp-gen573-narrative.txt per the encoding law) and
# drive the toolkit fold dry-run then execute.
# Window = tail 5 (fold R572 rolling line + R2043 round +
# R2043 tokens + R2044 round + R2044 tokens; fold R572
# carries the R2041/R2042 spectrum over the fold R571
# carrying domain).
# Pure ASCII source.
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normcase(os.path.normpath(
    os.path.join(HERE, "..", "..")))
sys.path.insert(0, HERE)

import logs_toolkit as LT                     # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
NARRATIVE = os.path.join(ROOT, "logs",
                         "tmp-gen573-narrative.txt")
SUMMARY = os.path.join(os.environ["TEMP"],
                       "fold-summary-R2045.txt")

TAIL = 5
ROUND = "R2045"
FOLD_NO = "573"
DESC = ("fold R572 rolling line + R2043 round+tokens + R2044 "
        "round+tokens (the R2043/R2044 statsmonth straddle "
        "product rounds; fold R572 carries the R2041/R2042 "
        "spectrum)")

HEAD_ASSERTS = ("fold R572", "2026-10-19 R2043",
                "R2043 tokens:", "2026-10-19 R2044",
                "R2044 tokens:")


def main():
    st = json.loads(io.open(STATE, encoding="utf-8").read())
    window = st["log"][-TAIL:]
    assert len(window) == TAIL, "log shorter than window"
    for line, head in zip(window, HEAD_ASSERTS):
        assert head in line, "window head mismatch: %s" % head
    sizes = [len(x.encode("utf-8")) for x in window]
    for line, sz in zip(window, sizes):
        assert sz > 100, "window line suspiciously small %d" % sz

    toks = []
    seen = set()
    for line in window:
        for tok in LT.PAT.findall(line):
            if tok not in seen:
                seen.add(tok)
                toks.append(tok)
    win_bytes = sum(sizes)
    with io.open(NARRATIVE, encoding="utf-8") as fh:
        narrative = fh.read().strip()
    summary = narrative + "\u2014\u2014catalog: " + "|".join(toks)
    assert "\n" not in summary, "summary must be one line"
    with io.open(SUMMARY, "w", encoding="utf-8",
                 newline="\n") as fh:
        fh.write(summary + "\n")

    base = [sys.executable, os.path.join(HERE, "logs_toolkit.py"),
            "fold", "--round", ROUND, "--fold-no", FOLD_NO,
            "--desc", DESC, "--window-tail", str(TAIL),
            "--summary-file", SUMMARY, "--allow-create"]
    p1 = subprocess.run(base + [], capture_output=True)
    out1 = p1.stdout.decode("utf-8", "replace")
    plan = json.loads(out1)
    assert plan.get("mode") == "dry-run", "dry-run plan not found"
    assert plan["token_ok"], ("token_missing=%s"
                              % plan["token_missing"])
    assert plan["gate_ok"], ("gate exceeded: predicted=%d "
                             "reserve=%d"
                             % (plan["predicted_bytes"],
                                plan["reserve_bytes"]))
    assert plan["window_lines"] == TAIL
    print("DRY-RUN-OK predicted=%d window_bytes=%d tokens=%d "
          "summary_bytes=%d"
          % (plan["predicted_bytes"],
             plan["window_content_bytes"], len(toks),
             len(summary.encode("utf-8"))))
    p2 = subprocess.run(base + ["--execute"], capture_output=True)
    out2 = p2.stdout.decode("utf-8", "replace")
    done_line = [ln for ln in out2.splitlines()
                 if ln.startswith("FOLD ")]
    print((done_line[-1] if done_line else "no-done-line")
          .encode("ascii", "replace").decode("ascii"))
    assert p2.returncode == 0, ("fold execute failed rc=%d out=%s"
                                % (p2.returncode, out2[-400:]))

    st2 = json.loads(io.open(STATE, encoding="utf-8").read())
    sz = os.path.getsize(STATE)
    print("POST-FOLD state bytes=%d log-items=%d"
          % (sz, len(st2["log"])))
    assert sz < 78500, "post-fold over the line"
    return 0


if __name__ == "__main__":
    sys.exit(main())
