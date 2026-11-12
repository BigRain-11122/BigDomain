import io, json, os, sys

P = "src/os/state.json"
raw = io.open(P, encoding="utf-8", newline="").read()
before = os.path.getsize(P)
d = json.loads(raw)
if d.get("tick") != 2665:
    print("REFUSED tick=%r" % (d.get("tick"),))
    sys.exit(2)

items = [
"2026-11-12 R2676 VERIFICATION window opened on the battery the debt gate names first (reconcile-battery-R2675, pre-registered 655 suites / 4906 criteria) because the R2675 product window moved product src bytes and one registry row (the R2168 mixed-tree rule). Five readings at open, all clean: git status EMPTY at HEAD 327f914f with no index.lock; ZERO unreplied @BigDomain rows (atbd_lines=0 unreplied_groups=0); the content-addressed decisions scan read rows=114 tokens=63 new=0; the group orders tail still the 2026-11-12 12:45 bm-a station ONBOARD row already carried as last_order and judged knowledge-only for this company; benchmarks_refreshed 2026-11-10 sitting two days inside the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2675 opened=R2675 first=1 open=45 and the target was RE-MEASURED BY IMPORT before the launch at 655 suites / 4906 criteria / 655 unique names / 655 unique paths, byte for byte the registered number.",
"2026-11-12 R2676 A CARRIED TOOLING DEFECT WAS REPAIRED AT ITS BIRTH SITE AND COMMITTED ALONE (20e9da4a) BEFORE the leg launched, so the battery runs on the final committed tree: src/os/scan_five_still.py died on every native GBK console at its first non-ASCII print, reproduced this window as UnicodeEncodeError 'gbk' codec can't encode character U+FEFF in position 10 at the [ORD-TOP] line, and the cause is the READER rather than that line - the group ledgers carry a U+FEFF byte order mark that a plain utf-8 decode keeps as a character. The reader now uses utf-8-sig AND strips every U+FEFF (a mark also sits mid-file, so the offset alone is not enough) and stdout is reconfigured to backslashreplace so no future unmappable character can kill a scan. MEASURED AFTER: python src/os/scan_five_still.py on the native console read EXIT=0 and printed the [ORD-TOP] title clean, with the source still 4528 bytes / ZERO non-ASCII bytes / no BOM. The workaround note carried in state line after state line is now closed rather than repeated.",
"2026-11-12 R2676 THE LEG WAS LAUNCHED DETACHED AND IS STILL RUNNING AT CLOSEOUT, DISCLOSED RATHER THAN DRESSED UP AS GREEN: a one-off launcher that refused on a moved target or an existing evidence file Popen-ed src/os/battery_stream.py with CREATE_NO_WINDOW|DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP and put the stream and the pid in SEPARATE files under logs/ (battery-R2676.stream, battery-R2676.pid, pid 97688 confirmed live by command line carrying the battery_stream argv), so qa/reconcile-all-R2676.log is written by the single utf-8 LF writer on completion and never by a shell redirection. MEASURED at open+45s the stream was 15735B carrying the runner own shell-capture notice, and at open+135s it read 33964B carrying 25 closed PASS suite rows and ZERO FAIL suite rows, the last being ledger-venue 7/7 at 0.4s. A full leg has measured roughly 1600-3300s in this repository against this window 25-minute budget, so reconcile-battery-R2675 STAYS OPEN at its registered 655/4906 and the next window ADOPTS this leg and closes the row (the R2671/R2673/R2674 precedent) instead of a green claim this window cannot make.",
"R2676 tokens: local=~8k api=0 api_reason=verification window - one five-silence scan actually run natively after the reader repair (ledger 0 rows, decisions new=0, orders tail carried as last_order, benchmarks inside the gate), one debt gate read naming the battery, one registry target re-measured by import on four axes, one carried console defect reproduced on the native console and repaired at its reader with a native re-run for proof, one one-off refusing launcher written, executed and DELETED before the commit, one detached leg launched with its stream and pid in separate files and two bounded progress polls, and the state/export/backlog closeout; zero cloud calls and zero external API touches",
"R2676 push and export: this line lands in the follow-up commit it describes. The export was refreshed AFTER the state append (the R2449/R2433 ordering law) through the shipped driver src/os/export_R2635.py with the three CEO-visible lines derived rather than typed, and state_fold --check read FOLD-CLEAR at 50660B against the 78500B gate before the append. The debt gate still names reconcile-battery-R2675 first=yes at the pre-registered 655 suites / 4906 criteria and that leg is LIVE at this closeout (pid 97688, stream growing past 33KB), so the row stays OPEN and the next window adopts it; NO successor battery is owed because this window moved no product src byte and the registry is unmoved at 655/4906, re-measured by import.",
]
d["log"].extend(items)
d["tick"] = 2666
out = json.dumps(d, ensure_ascii=False, indent=1)
out = out.replace("\n", "\r\n")
tmp = P + ".tmp"
with io.open(tmp, "w", encoding="utf-8", newline="") as f:
    f.write(out)
back = json.load(io.open(tmp, encoding="utf-8"))
if back["tick"] != 2666 or len(back["log"]) != len(d["log"]):
    print("REFUSED readback mismatch")
    sys.exit(3)
os.replace(tmp, P)
print("APPENDED before=%d after=%d predicted=%d items=%d tick=%d" % (
    before, os.path.getsize(P), len(out.encode("utf-8")) + 0, len(items), d["tick"]))
