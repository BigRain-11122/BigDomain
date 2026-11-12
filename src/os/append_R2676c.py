import io, json, os, sys

P = "src/os/state.json"
d = json.load(io.open(P, encoding="utf-8"))
if d.get("tick") != 2666:
    print("REFUSED tick=%r" % (d.get("tick"),))
    sys.exit(2)
before = os.path.getsize(P)

items = [
"2026-11-12 R2676 THE LEG FINISHED RED AND IS KEPT AS EVIDENCE, MEASURED NOT GLOSSED: the process chain was gone by command line, logs/battery-R2676.stream closed on RUNNER FAIL (2 failed assertions) and BATTERY rc=1 3504.1s, and qa/reconcile-all-R2676.log read 1112916B, utf-8, bom=False, crlf=0, lone_cr=0, nul=0, 8740 lines, 654 PASS suite rows with 654 unique names against exactly ONE FAIL suite row, and an INDEPENDENT criteria recount summing to EXACTLY 4906 - the pre-registered target met on both axes, so the leg is complete and the red is real rather than a truncated run.",
"2026-11-12 R2676 ROOT CAUSE READ OFF THE FAILING CRITERION AND REPAIRED AT ITS BIRTH SITE (commit 63fdd254, repair plus red leg committed ALONE before any retry): os-export-driver-self-drive-health AC-EDSH2 requires a window holding a tokens line to count MORE window lines than substantive lines. Measured live: log_lines_in_window=16 while substantive_non_idle_mention_lines=16, so the premise could not hold. The cause is in check_export_consistency.recompute, not in the assertion - it placed a log line in the window by that line own date prefix, and MEASURED this window 52 log lines split into 16 dated and 36 undated, every one of the 7 tokens lines undated, so the substantive count could never differ from the line count and the health term had lost exactly the discrimination it exists to give. A line now belongs to the round line it follows; the counter reads 51 window lines against 16 substantive with idle=0 nop=0, AC-EDSH2 reads SUITE PASS 6/6, and check_export_consistency reads 21/21 VERDICT PASS after the export was re-derived to 405179B. The write-sensitive set was re-run on the final tree and read ELEVEN suites green by rc (export trio, ledger coverage, six readability suites, both health suites).",
"2026-11-12 R2676 A FRESH RETRY LEG WAS LAUNCHED DETACHED ON THE COMMITTED REPAIR TREE AND IS LIVE AT CLOSEOUT, DISCLOSED RATHER THAN PRESENTED AS GREEN: pid 79940 through src/os/battery_stream.py with the stream and the pid in SEPARATE files under logs/ (battery-R2676-retry.stream, battery-R2676-retry.pid) and the evidence path qa/reconcile-all-R2676-retry.log reserved for the single utf-8 LF writer, target refused-unless 655 suites / 4906 criteria / 655 unique names / 655 unique paths re-measured by import. A full leg measured 3504.1s here, so reconcile-battery-R2675 STAYS OPEN and the next window adopts this leg; NO successor battery is owed beyond it because this round moved no product src byte and the registry is unmoved at 655/4906.",
"R2676 tokens (second half): local=~10k api=0 api_reason=verification window continuation - two bounded progress polls then six long waits on the live leg through to its closing BATTERY line, one evidence measurement on bytes with an independent criteria recount, one failing criterion reproduced ALONE twice, one counter birth site read and its blast radius measured before the change, one repair with a live re-measure and the eleven write-sensitive suites re-run green, one export re-derivation and one consistency pass, one red leg plus repair committed alone, one fresh detached leg launched with its stream and pid in separate files and the one-off launcher DELETED before the commit, and the state/board/heartbeat/export closeout; zero cloud calls and zero external API touches",
]
d["log"].extend(items)
d["tick"] = 2667
out = json.dumps(d, ensure_ascii=False, indent=1).replace("\n", "\r\n")
tmp = P + ".tmp"
with io.open(tmp, "w", encoding="utf-8", newline="") as f:
    f.write(out)
back = json.load(io.open(tmp, encoding="utf-8"))
if back["tick"] != 2667 or len(back["log"]) != len(d["log"]):
    print("REFUSED readback")
    sys.exit(3)
os.replace(tmp, P)
print("APPENDED before=%d after=%d predicted=%d log=%d tick=%d" % (
    before, os.path.getsize(P), len(out.encode("utf-8")), len(d["log"]), d["tick"]))
