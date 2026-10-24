# fold_R2094.py - pre-closeout fold of the tail-3 window (R2092
# closeout round + R2093 product round pair). Token catalog is
# mechanically extracted through logs_toolkit.PAT; heads are read
# from the live tail, never hand transcribed. Pure ASCII source.
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
TPL = os.path.join(HERE, "fold_summary_R2094.json")
SUMMARY = os.path.join(os.environ["TEMP"], "fold-summary-R2094.txt")

TAIL = 7
ROUND = "R2094"
FOLD_NO = "586"
DESC = ("fold R585 rolling line + R2089/R2090/R2091 product"
        " pairs + R2092 closeout + R2093 rating-reply pair")


def main():
    st = json.loads(io.open(STATE, encoding="utf-8").read())
    window = st["log"][-TAIL:]
    assert len(window) == TAIL, "log shorter than window"
    sizes = [len(x.encode("utf-8")) for x in window]
    for line, sz in zip(window, sizes):
        assert sz > 100, "window line suspiciously small %d" % sz

    toks = set()
    for line in window:
        toks |= set(LT.PAT.findall(line))
    win_bytes = sum(sizes)
    tpl = json.loads(io.open(TPL, encoding="utf-8").read())["template"]
    summary = (tpl
               .replace("%%WINBYTES%%", str(win_bytes))
               .replace("%%TOKCOUNT%%", str(len(toks)))
               .replace("%%TOKENS%%", "|".join(sorted(toks))))
    assert "\n" not in summary, "summary must be one line"
    with io.open(SUMMARY, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(summary + "\n")

    base = [sys.executable, os.path.join(HERE, "logs_toolkit.py"),
            "fold", "--round", ROUND, "--fold-no", FOLD_NO,
            "--desc", DESC, "--window-tail", str(TAIL),
            "--summary-file", SUMMARY, "--allow-create"]
    p1 = subprocess.run(base, capture_output=True)
    plan = json.loads(p1.stdout.decode("utf-8", "replace"))
    assert plan.get("mode") == "dry-run", "dry-run plan not found"
    assert plan["token_ok"], "token_missing=%s" % plan["token_missing"]
    assert plan["gate_ok"], ("gate exceeded: predicted=%d reserve=%d"
                             % (plan["predicted_bytes"],
                                plan["reserve_bytes"]))
    assert plan["window_lines"] == TAIL
    print("DRY-RUN-OK predicted=%d window_bytes=%d tokens=%d"
          % (plan["predicted_bytes"], plan["window_content_bytes"],
             len(toks)))
    p2 = subprocess.run(base + ["--execute"], capture_output=True)
    out2 = p2.stdout.decode("utf-8", "replace")
    done_line = [ln for ln in out2.splitlines()
                 if ln.startswith("FOLD ")]
    print((done_line[-1] if done_line else "no-done-line")
          .encode("ascii", "replace").decode("ascii"))
    assert p2.returncode == 0, ("fold execute failed rc=%d out=%s"
                               % (p2.returncode, out2[-400:]))
    print("POST-FOLD state bytes=%d" % os.path.getsize(STATE))
    return 0


if __name__ == "__main__":
    sys.exit(main())