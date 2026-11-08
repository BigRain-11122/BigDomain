"""Execute the live fold for R2567 through the shipped face (product proof)."""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402
import state_fold_run as FR  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(BASE))
PATH = SF.state_path(ROOT)
RAW, STATE = SF.read_state(PATH)
LOG = STATE["log"]

END = 0
SUMMARY = ""
TARGET = 73000
for end in range(30, len(LOG)):
    window = LOG[0:end]
    tokens = set()
    for line in window:
        tokens |= set(SF.PAT.findall(line))
    summary = ("R2567 fold of log lines 1..%d into the archive; all %d tokens "
               "preserved verbatim in this line: %s"
               % (end, len(tokens), " ".join(sorted(tokens))))
    plan, _ = SF.plan_fold(RAW, STATE, 1, end, summary, gate=SF.GATE)
    if plan["tokens_missing"] or plan["round_split"]:
        continue
    if plan["predicted_bytes"] <= TARGET:
        END, SUMMARY = end, summary
        break
assert END, "no window fits"

before = os.path.getsize(PATH)
report = FR.run(ROOT, "R2567", 1, 1, END, SUMMARY)
print(json.dumps(report, ensure_ascii=True, indent=1))
after = os.path.getsize(PATH)
check = SF.check(ROOT)
print("CHECK", json.dumps(check, ensure_ascii=True))
print("SIZES", before, "->", after, "verdict", check["verdict"])

lines = []
lines.append("state-fold-run-R2567 live fold through the shipped face")
lines.append("window=1..%d of %d log lines, tokens=%d, live_lines_after=%d"
             % (END, len(LOG), report["tokens_total"],
                report["live_lines_after"]))
lines.append("bytes %d -> %d, gate=%d, margin=%d, verdict=%s"
             % (before, after, check["gate"], check["margin"],
                check["verdict"]))
lines.append("archive=%s appendix_bytes=%d verified=%s"
             % (report["archive_path"], report["archive_appendix_bytes"],
                report["archive_verified"]))
lines.append("ledger_rounds %d -> %d, layout_agree=%s, field_set_same=%s"
             % (report["ledger_rounds_before"], report["ledger_rounds_after"],
                report["layout_agree"], report["field_set_same"]))
body = "\n".join(lines) + "\n"
with io.open(os.path.join(ROOT, "qa", "state-fold-live-R2567.log"),
             "wb") as handle:
    handle.write(body.encode("utf-8"))
print("evidence bytes", len(body.encode("utf-8")))