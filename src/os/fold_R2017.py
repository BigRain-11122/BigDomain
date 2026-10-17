# fold_R2017.py - compose fold R547 summary line (token catalog
# mechanically extracted via LT.PAT, window heads asserted from
# the actual tail-3 lines - zero hand transcription) and drive
# the toolkit fold dry-run then execute. Window = tail 3 (fold
# R546 rolling line + R2016 round line + R2016 tokens line).
# Pure ASCII source; CJK template lives in
# fold_summary_R2017.json (data file law).
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import logs_toolkit as LT  # noqa: E402 (PAT single source)

STATE = os.path.join(ROOT, "src", "os", "state.json")
TPL = os.path.join(HERE, "fold_summary_R2017.json")
SUMMARY = os.path.join(os.environ.get("TEMP", HERE),
                       "fold-summary-R2017.txt")

TAIL = 3
ROUND = "R2017"
FOLD_NO = "547"
DESC = ("fold R546 rolling line + R2016 round line + R2016 "
        "tokens line (R2016 = showcase statsmonth persist "
        "example-window delivery round; R2017 is the 34th-"
        "case takeover closeout that lands the crashed "
        "round's statsmonth zero-registry boundary persist "
        "suite with personal green re-verification)")


def main():
    st = json.loads(io.open(STATE, encoding="utf-8").read())
    window = st["log"][-TAIL:]
    assert len(window) == TAIL, "log shorter than window"
    heads = ("fold R546",
             u"R2016\uff08\u4e94\u9759\u68c0\u51fa",
             "R2016 tokens:")
    for line, head in zip(window, heads):
        assert head in line, ("window head mismatch:"
                              " %r not found" % head)
    sizes = [len(x.encode("utf-8")) for x in window]
    for line, sz in zip(window, sizes):
        assert sz > 100, ("window line suspiciously small %d"
                          % sz)

    toks = set()
    for line in window:
        toks |= set(LT.PAT.findall(line))
    win_bytes = sum(sizes)
    tpl = json.loads(io.open(TPL, encoding="utf-8").read())[
        "template"]
    summary = (tpl
               .replace("%%WINBYTES%%", str(win_bytes))
               .replace("%%TOKCOUNT%%", str(len(toks)))
               .replace("%%TOKENS%%", "|".join(sorted(toks))))
    assert "\n" not in summary, "summary must be one line"
    with io.open(SUMMARY, "w", encoding="utf-8",
                 newline="\n") as fh:
        fh.write(summary + "\n")

    base = [sys.executable, os.path.join(HERE,
            "logs_toolkit.py"), "fold", "--round", ROUND,
            "--fold-no", FOLD_NO, "--desc", DESC,
            "--window-tail", str(TAIL), "--summary-file",
            SUMMARY, "--allow-create"]
    p1 = subprocess.run(base + [], capture_output=True)
    out1 = p1.stdout.decode("utf-8", "replace")
    plan = json.loads(out1)
    assert plan.get("mode") == "dry-run", "dry-run plan not found"
    assert plan["token_ok"], ("token_missing=%s"
                              % plan["token_missing"])
    assert plan["gate_ok"], ("gate exceeded: predicted=%d"
                             " reserve=%d"
                             % (plan["predicted_bytes"],
                                plan["reserve_bytes"]))
    assert plan["window_lines"] == TAIL
    print("DRY-RUN-OK predicted=%d window_bytes=%d tokens=%d"
          % (plan["predicted_bytes"],
             plan["window_content_bytes"], len(toks)))
    p2 = subprocess.run(base + ["--execute"], capture_output=True)
    out2 = p2.stdout.decode("utf-8", "replace")
    done_line = [ln for ln in out2.splitlines()
                 if ln.startswith("FOLD ")]
    print((done_line[-1] if done_line else "no-done-line")
          .encode("ascii", "replace").decode("ascii"))
    assert p2.returncode == 0, ("fold execute failed rc=%d"
                                " out=%s"
                                % (p2.returncode, out2[-400:]))

    st2 = json.loads(io.open(STATE, encoding="utf-8").read())
    sz = os.path.getsize(STATE)
    print("POST-FOLD state bytes=%d log-items=%d"
          % (sz, len(st2["log"])))
    assert sz < 78500, "post-fold over the line"
    return 0


if __name__ == "__main__":
    sys.exit(main())
