# fold_R1981.py - compose fold R524 summary line (token catalog
# mechanically extracted, zero hand transcription; PAT imported
# single-source from logs_toolkit per gen523 precedent) and drive
# the toolkit fold dry-run then execute. Pure ASCII source; CJK
# template lives in fold_summary_R1981.json (data file law).
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
TPL = os.path.join(HERE, "fold_summary_R1981.json")
SUMMARY = os.path.join(os.environ["TEMP"], "fold-summary-R1981.txt")

TAIL = 6
ROUND = "R1981"
FOLD_NO = "524"
DESC = "R1978 round + tokens, R1979 round + tokens," \
       " R1980 round + tokens"


def main():
    st = json.loads(io.open(STATE, encoding="utf-8").read())
    window = st["log"][-TAIL:]
    assert len(window) == TAIL, "log shorter than window"
    toks = set()
    for line in window:
        toks |= set(LT.PAT.findall(line))
    win_bytes = sum(len(x.encode("utf-8")) for x in window)
    tpl = json.loads(io.open(TPL, encoding="utf-8").read())["template"]
    summary = (tpl
               .replace("%%WINBYTES%%", str(win_bytes))
               .replace("%%TOKCOUNT%%", str(len(toks)))
               .replace("%%TOKENS%%", "|".join(sorted(toks))))
    # exactly one non-empty line, no embedded newline
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
                                % (p2.returncode,
                                   out2.encode("ascii", "replace")
                                   .decode("ascii")[-400:]))
    new_size = os.path.getsize(STATE)
    assert new_size == plan["predicted_bytes"], (
        "post==predicted violated: %d != %d"
        % (new_size, plan["predicted_bytes"]))
    print("FOLD-EXECUTED post==predicted %dB archive=%s backup=%s"
          % (new_size, plan["archive_file"], plan["backup_path"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
