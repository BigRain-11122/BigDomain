# fold_R1985.py - compose fold R527 summary line (token catalog
# mechanically extracted via LT.PAT, carried fold numbers pulled
# from the actual window line heads - zero hand transcription)
# and drive the toolkit fold dry-run then execute.
# Window = tail 5 (fold R520 + fold R523 + fold R526 rolling
# lines + R1984 round + R1984 tokens). Pure ASCII source; CJK
# template lives in fold_summary_R1985.json (data file law).
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import logs_toolkit as LT  # noqa: E402 (PAT single source)

STATE = os.path.join(ROOT, "src", "os", "state.json")
TPL = os.path.join(HERE, "fold_summary_R1985.json")
SUMMARY = os.path.join(os.environ["TEMP"], "fold-summary-R1985.txt")

TAIL = 5
ROUND = "R1985"
FOLD_NO = "527"
DESC = ("fold R520 rolling [R1940..R1968] + fold R523 rolling"
        " [R1969..R1977] + fold R526 rolling [R1982..R1983] +"
        " R1984 round + tokens")

HEAD_ASSERTS = ("R1940..R1968", "R1969..R1977", "R1982..R1983",
               "2026-10-15 R1984", "R1984 tokens:")


def main():
    st = json.loads(io.open(STATE, encoding="utf-8").read())
    window = st["log"][-TAIL:]
    assert len(window) == TAIL, "log shorter than window"
    for line, head in zip(window, HEAD_ASSERTS):
        assert head in line, "window head mismatch: %s" % head
    fnums = []
    for line in window:
        m = re.search(r"fold R(\d+)", line)
        fnums.append(m.group(0) if m else "-")
    assert len(fnums) == TAIL

    toks = set()
    for line in window:
        toks |= set(LT.PAT.findall(line))
    win_bytes = sum(len(x.encode("utf-8")) for x in window)
    tpl = json.loads(io.open(TPL, encoding="utf-8").read())["template"]
    summary = (tpl
               .replace("%%F13%%", fnums[0].replace("fold ", ""))
               .replace("%%F14%%", fnums[1].replace("fold ", ""))
               .replace("%%F15%%", fnums[2].replace("fold ", ""))
               .replace("%%WINBYTES%%", str(win_bytes))
               .replace("%%TOKCOUNT%%", str(len(toks)))
               .replace("%%TOKENS%%", "|".join(sorted(toks))))
    assert "\n" not in summary, "summary must be one line"
    with open(SUMMARY, "w", encoding="utf-8", newline="\n") as fh:
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

    st2 = json.loads(io.open(STATE, encoding="utf-8").read())
    assert st2["log"][-1].startswith("2026-10-15"), "tail line"
    sz = os.path.getsize(STATE)
    print("POST-FOLD state bytes=%d log-items=%d" % (sz, len(st2["log"])))
    assert sz < 78500, "post-fold over the line"
    return 0


if __name__ == "__main__":
    sys.exit(main())
