"""R2728 monitored-wait closeout: state log + tick, export face, heartbeat."""

import datetime
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import state_io  # noqa: E402
import check_export_consistency as X  # noqa: E402

PATH = os.path.join(HERE, "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEART = os.path.join(ROOT, "heartbeat.txt")

LINES = [
    "2026-11-14 R2728 MONITORED-WAIT window: the R2725 battery leg is STILL "
    "LIVE at closeout and was NOT relaunched, so reconcile-battery-R2725 "
    "STAYS OPEN and NO verdict is issued here. Measured rather than assumed: "
    "qa/reconcile-all-R2725.log is ABSENT, logs/battery-R2725.stream reads "
    "1101406B with 652 PASS suite rows, ZERO FAIL suite rows and no closing "
    "BATTERY rc= line, and pid 56016 answered a SYNCHRONIZE kernel probe "
    "(OpenProcess ok, WaitForSingleObject returned the timeout state) at 16:51 "
    "and again at 16:59, so a live leg was never misread as a dead one and a "
    "WMI CommandLine list was never consulted.",
    "R2728 five readings at open: git status EMPTY at HEAD 7089976d equal to "
    "origin/main with no index.lock; ZERO @BigDomain rows in the group ledger; "
    "the content-addressed decisions face read cur=64 base=263 new=0; the "
    "group orders tail is the 2026-11-14 00:30 main-control row OLDER than the "
    "carried baseline; benchmarks_refreshed 2026-11-14 inside the seven-day "
    "gate. Debt gate read CLAIM-FIRST item=reconcile-battery-R2725 open=51, "
    "queue_head read tech line=697 prefix AC-EPTYP1 claimable=13, explore "
    "line=3 prefix AC-SRFM1 claimable=10, main NO-HEAD with one row gated on "
    "CEO.",
    "R2728 THE ONE REAL ARTIFACT AND WHY THE QUEUES WERE LEFT ALONE, stated as "
    "a limit rather than a claim: src/os/verify_writesensitive.py consolidates "
    "the three per-window copies (R2620 carries 10 names, R2722 and R2724 the "
    "same 15 names measured equal) into one parameterised runner that IMPORTS "
    "the pinned selection from the shipped R2724 module instead of retyping "
    "it, refuses before firing when a name sits outside the shipped registry "
    "(rc=3), and writes one utf-8 LF evidence file whose header now takes the "
    "leg, the head and the commits as arguments; self-check reads names=15 "
    "missing=[] paths_ok=15 and the tool landed as 39483020. The tech head "
    "AC-EPTYP1 and the explore head AC-SRFM1 were NOT taken because both ship "
    "a suite and a registry row: the running leg froze its SUITES list at "
    "import so it cannot be corrupted by a mid-flight row, but the follow-up "
    "restamp and the verdict compare the leg criteria against the registry, so "
    "a row added now would have made the leg inadmissible at its pre-"
    "registered 673 suites / 5014 criteria - product bytes and registry rows "
    "are exactly what the R2168 mixed-tree rule forbids before this battery "
    "lands.",
    "R2728 honest disclosures: (a) ZERO product points by the Executive "
    "Protocol scale - no debt closed, no verdict, no matrix restamp, and the "
    "ONE artifact is tooling that removes three copies of a runner; every P-47 "
    "business face still waits on CEO physical pieces (merchant id, mini-"
    "program appid/secret); (b) the R2614 write-sensitive re-run was "
    "deliberately NOT fired: those fifteen suites write the very state, matrix "
    "and export artifacts the live battery is concurrently writing, so firing "
    "them now is the collision the discipline exists to prevent - it is owed "
    "on the FINAL committed tree before any verdict; (c) the registry was NOT "
    "re-measured by import here because no byte touched it, so a re-measurement "
    "would only re-quote the debt row; (d) the leg projection is arithmetic "
    "and not a promise: 652 of 673 suite rows at roughly one suite per two "
    "minutes, with several heavy audit suites holding the stream unwritten for "
    "minutes at a time; (e) src/os still carries hundreds of one-off closeout "
    "scripts, pre-existing bloat this window neither created nor cleaned, and "
    "this window added exactly one file; (f) tasks.md was not touched, it is "
    "the P-47 canonical board; (g) Docker is absent on this host; (h) "
    "BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell "
    "for its S4U re-registration (carried ceo-pending physical item loop-s4u-"
    "reconcile).",
    "R2728 tokens: local=~9k api=0 api_reason=monitored-wait window - one "
    "five-silence scan with the debt gate and three queue heads, one kernel "
    "liveness read plus three stream measurements, one consolidation of three "
    "per-window runners into one parameterised tool with a self-check, one "
    "commit, and the state/export/heartbeat closeout; zero cloud calls and "
    "zero external API touches",
]


def append_state():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + LINES
    expected["tick"] = tick + 1

    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)

    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    bumped = []
    old_tick = '"tick": %d' % tick
    new_tick = '"tick": %d' % (tick + 1)
    seen = 0
    for row in doc_lines:
        if row.strip().rstrip(",") == old_tick and not seen:
            bumped.append(row.replace(old_tick, new_tick))
            seen += 1
        else:
            bumped.append(row)
    if seen != 1:
        print("REFUSED tick line not found exactly once")
        return 3
    out = state_io.EOL.join(bumped[:end] + inserted + bumped[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2728p_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d"
          % (tick + 1, after["bytes"], after["log_len"]))
    return 0


def refresh_export():
    with io.open(EXPORT, encoding="utf-8") as fh:
        doc = json.load(fh)
    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.replace(microsecond=0).isoformat()
    face = doc.get("ceo_face") or {}
    face["current"] = (
        "R2725 电池腿（673 套件/5014 判据）仍在跑：652/673 套零 FAIL，本窗未重发、"
        "未验收；上一窗三件 W40 设计面在盘")
    face["latest_artifact"] = (
        "src/os/verify_writesensitive.py 参数化写敏感复验工具（2026-11-14 R2728·"
        "替代三份逐窗复制·自检 15 名全在册在盘）")
    face["last_artifact"] = (
        "docs/spec/payment-integration-spec.md §六之二 终端分列验证矩阵 + "
        "docs/spec/membership-spec.md §〇之二 订阅扣款分端表（2026-11-14 R2727）")
    face["next_milestone"] = (
        "下一窗：按证据路径验收 R2725 电池腿（qa/reconcile-all-R2725.log·673 套件/"
        "5014 判据）→ 四节 followup（矩阵先 FAIL 后重压）→ 关债 → R2614 十五条写敏感"
        "复验；随后开队头 AC-EPTYP1 产品面")
    face["next_milestone_due"] = "2026-11-15T22:00:00+08:00"
    face["updated_at"] = now.astimezone(
        datetime.timezone(datetime.timedelta(hours=8))).replace(
            microsecond=0).isoformat()
    doc["ceo_face"] = face
    doc["export_ts"] = stamp
    doc["do"] = (
        "2026-11-14 R2728 MONITORED-WAIT window: the R2725 battery leg is still "
        "live (652 of 673 suite rows, zero FAIL, no evidence file yet) and was "
        "not relaunched; the one artifact is src/os/verify_writesensitive.py, a "
        "parameterised consolidation of the three per-window write-sensitive "
        "runners. No debt closed and no verdict issued.")
    derived = X.recompute()
    if isinstance(derived, tuple):
        derived = derived[0]
    if isinstance(derived, dict) and "self_drive" in derived:
        doc["self_drive"] = derived["self_drive"]
    elif isinstance(derived, dict):
        doc["self_drive"] = derived
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("EXPORT ok ts=%s bytes=%d"
          % (stamp, os.path.getsize(EXPORT)))
    return 0


def append_heartbeat():
    with io.open(HEART, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("2026-11-14 %s tick 2724 R2728 wait on live R2725 leg, "
                 "write-sensitive runner consolidated\n"
                 % datetime.datetime.now().strftime("%H:%M:%S"))
    print("HEARTBEAT ok")
    return 0


if __name__ == "__main__":
    rc = append_state()
    if rc:
        sys.exit(rc)
    rc = refresh_export()
    if rc:
        sys.exit(rc)
    sys.exit(append_heartbeat())
