"""R2622 verification window: append the round block and move the tick.

Lines are the round narrative and the token ledger line, in the order the
window actually measured them. Tick belongs to the round, so this writer owns
it; the receipt after the push is a separate no-tick append.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    (
        "2026-11-11 R2622 VERIFICATION window on the battery the debt gate "
        "named FIRST (reconcile-battery-R2621, first=1, open=41, pre-registered "
        "642 suites / 4828 criteria at R2621 because that window moved product "
        "src bytes, one registry row and the matrix document). Five readings at "
        "open: git status EMPTY at HEAD 406ad940 equal to origin/main with no "
        "index.lock, ZERO @BigDomain rows in cph4/evolution-ledger.md, the "
        "content-addressed decisions scan read tokens=182 against its baseline "
        "with new=0 over 307 rows, the group orders tail unchanged at its "
        "2026-11-11 03:52 row so last_order stands, and benchmarks_refreshed "
        "2026-11-10 sits inside the seven-day gate. queue_floor read "
        "FLOOR-MET at 5/5, 15/10, 10/10. So the ONLY work this window owed was "
        "that battery, and this window could not finish it inside a 25-minute "
        "budget."
    ),
    (
        "2026-11-11 R2622 TARGET RE-MEASURED BY IMPORT TWICE BEFORE THE "
        "LAUNCH: reconcile_all.SUITES read 642 suites / 4828 criteria / 642 "
        "unique names / 642 unique paths - byte for byte the R2621 "
        "registration - and the launcher refuses on any drift rather than "
        "trusting the row."
    ),
    (
        "2026-11-11 R2622 THE LEG WAS LAUNCHED DETACHED AND IS STILL RUNNING "
        "AT CLOSEOUT, WHICH IS DISCLOSED RATHER THAN DRESSED UP AS GREEN: "
        "src/os/launch_battery_R2622.py measured the registry itself, refused "
        "if the target had moved or the evidence file already existed, "
        "Popen'ed src/os/battery_stream.py with CREATE_NO_WINDOW|"
        "DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP and put the stream and the "
        "pid in SEPARATE files under logs/ (battery-R2622.stream, "
        "battery-R2622.pid) so qa/ is written by the single writer and never "
        "by a shell redirection. pid 59736 with its battery_stream child was "
        "confirmed live by command line twice. A full leg has measured "
        "3500-4100s in this repository against this window 25-minute budget, "
        "so the debt row reconcile-battery-R2621 STAYS OPEN at its registered "
        "642/4828 and the next window adopts the leg and closes the row (the "
        "R2601/R2607 precedent) instead of a green claim this window cannot "
        "make."
    ),
    (
        "2026-11-11 R2622 PROPOSAL QUOTA DISCHARGED: the track owes one entry "
        "per week window and the last entry was BD-PROP-006 dated 2026-11-02 "
        "(window 11-01~11-07), so window 11-08~11-14 was short. BD-PROP-007 "
        "was appended through src/os/proposal_append_R2622.py (9809B -> "
        "11606B, refuses when the marker is already present): the battery leg "
        "costs ~60 minutes against a 25-minute window and the debt row records "
        "only WHAT is owed, never WHERE the leg stands, so adopting windows "
        "cannot tell a live leg from an abandoned one - the proposal asks the "
        "gate to carry the leg round, its pid and its evidence path as readback "
        "facts, with three pre-registered judgement questions."
    ),
    (
        "R2622 honest disclosures: (a) ZERO product points on the Executive "
        "Protocol scale - no product byte was written, because the debt gate "
        "puts the owed battery before any further product work and that leg "
        "is still running; (b) the battery is NOT green and is NOT claimed "
        "green - it is live at closeout with its evidence file not yet "
        "written, so the debt row stays open; (c) my own launcher's first run "
        "died on a wrong sys.path join (src/os/sandbox instead of "
        "src/sandbox) and was repaired BEFORE the launch, so no leg was wasted, "
        "which is named rather than smoothed; (d) src/os/scan_five_still.py "
        "crashed at its [ORD-TOP] print on a BOM character under the GBK "
        "console AFTER printing the ledger, decisions and orders readings this "
        "window needed - the three readings are used as printed, the crash is "
        "cosmetic and is named rather than hidden; (e) benchmarks at 2026-11-10 "
        "are one day inside the seven-day gate, so no refresh was due; (f) "
        "Docker is absent on this host so no containerised bring-up of the "
        "sandbox faces is claimed; (g) the real 19.9 debit and the real "
        "msgSecCheck still wait on CEO physical items (merchant id, "
        "mini-program appid/secret); (h) tasks.md was not touched, it is the "
        "P-47 canonical board; (i) BigDomain-OSLoop still needs an ELEVATED "
        "shell for its S4U re-registration (carried as the ceo-pending "
        "physical item loop-s4u-reconcile)."
    ),
    (
        "R2622 tokens: local=~11k api=0 api_reason=verification window - one "
        "five-silence scan with the content-addressed decisions scan, the group "
        "orders tail and the ledger face actually read, one queue floor read, "
        "one debt gate read naming the owed battery, one registry target "
        "re-measured by import on four axes, one detached battery launched "
        "through a refusing one-off launcher with its stream and pid in "
        "separate files and its liveness re-read twice, one weekly proposal "
        "appended through its own writer, and the state/export/heartbeat "
        "closeout; zero cloud calls and zero external API touches"
    ),
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["tick"] = int(data["tick"]) + 1
    expected["log"] = list(data["log"]) + list(LINES)
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    touched_tick = False
    for index in range(start):
        stripped = lines[index].strip()
        if stripped.startswith('"tick":'):
            lines[index] = ' "tick": %d,' % expected["tick"]
            touched_tick = True
    if not touched_tick:
        print("REFUSED no tick line")
        return 6
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    item_indent = None
    for line in lines[start + 1:end]:
        stripped = line.strip()
        if stripped.startswith('"'):
            item_indent = len(line) - len(line.lstrip(" "))
            break
    if item_indent is None:
        print("REFUSED no item line to measure the indent")
        return 6
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * item_indent +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2622_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d layout_ok=%s"
          % (expected["tick"], after["bytes"], after["log_len"],
             after["layout_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
