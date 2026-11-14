"""R2729 adoption closeout: state log + tick, export face, heartbeat."""

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
    "2026-11-14 R2729 ADOPTION window: reconcile-battery-R2725 was ADOPTED "
    "GREEN off its own evidence path and was NEVER relaunched. The leg was "
    "alive at open (pid 56016, 657 of 673 suite rows, zero FAIL) and three "
    "bounded polls were taken instead of a fourth monitored-wait handover; at "
    "17:25 the single-writer evidence file appeared. Measured through the tool "
    "this window shipped: qa/reconcile-all-R2725.log read 1225975B with 673 "
    "PASS suite rows, 673 UNIQUE names, ZERO FAIL rows, an INDEPENDENT criteria "
    "recount of EXACTLY 5014, bom=False crlf=0 lone_cr=0 nul=0, and the closing "
    "row reads RUNNER PASS (673/673 suites green, reconcile controls 7/7, "
    "6412.0s). The pid chain was then re-probed and read OPEN_FAIL, and the "
    "registry was re-measured BY IMPORT at 673 suites / 5014 criteria / 673 "
    "names / 673 paths, byte for byte the tuple debt row R2725 pre-registered.",
    "R2729 THE DESIGNED FIRST MEASUREMENT WAS RUN BEFORE ANY BYTE WAS WRITTEN: "
    "battery_followup --dry-run read SECTION matrix FAIL on-disk=71262B "
    "regenerated=71255B with NO byte written (the document still stamped the "
    "R2723 leg) beside fingerprint PASS CLEAN domains=5, profile PASS "
    "byte-identical and census PASS DRIFT-CLEAN. suite_matrix_reconcile --write "
    "--evidence qa/reconcile-all-R2725.log then restamped the document "
    "stamp-aligned from THIS round own green leg to 71255 bytes at 673 rows, "
    "--check read DOC-CURRENT, and the second dry-run read all four sections "
    "PASS with VERDICT reconcile-battery-R2725 PASS failing=none. The verdict "
    "block was appended to the evidence file through the shipped writer alone: "
    "APPENDED 1987B eol_ok=True, 1225975B -> 1227962B.",
    "R2729 ONE ARTIFACT SHIPPED, and it has a consumer inside this same window: "
    "src/os/leg_status.py is the single READ face that answers 'is the leg "
    "alive, how far is it, may I adopt it' with one verdict line and an exit "
    "code, replacing the same three readings typed by hand across R2726, "
    "R2727 and R2728 and the probe copy-pasted into eight per-round launchers. "
    "It writes nothing, signals nothing and never touches the evidence path; "
    "--self-check reads 10/10 green on private fixtures, including the R2724 "
    "trap pinned as an assertion (a bare 'PASS suite' prefix also matches the "
    "closing summary row 'PASS suites 673/673 green' and would report one "
    "suite too many). Its live reading is the adoption measurement quoted "
    "above.",
    "R2729 DEBT AND BOARD THROUGH THE SHIPPED WRITERS: reconcile-battery-R2725 "
    "was closed at line 435 (open 51->50, done 366->367, 234850B -> 234853B, "
    "readback ok) and product-face-R2729 was appended first=yes at 234853B -> "
    "235537B naming queue head state/queue/tech.md:697 prefix AC-EPTYP1 with "
    "claimable 13 and criteria AC-EPTYP1..AC-EPTYP6 pinned there at R2725 "
    "BEFORE any code. debt_gate --check now reads CLAIM-FIRST item=product-"
    "face-R2729. NO successor battery is owed: this window moved no product "
    "src byte and no registry row, so the registry is unmoved at 673 suites / "
    "5014 criteria.",
    "R2729 honest disclosures: (a) ZERO product points by the Executive "
    "Protocol scale - a green 673-suite battery, a restamped matrix, an "
    "appended verdict and a closed debt row are evidence and unblocking, not "
    "something a CEO can newly open, and every P-47 business face still waits "
    "on CEO physical pieces (merchant id, mini-program appid/secret); (b) this "
    "window ran past its 25 minute budget on purpose to hold one live leg to "
    "its own green instead of writing a fourth monitored-wait handover; (c) "
    "the evidence file measures 1227962B after the verdict block, exactly "
    "1987B more than the 1225975B this window measured on bytes first, named "
    "here so the next window does not read it as post-hoc drift; (d) the "
    "fifteen write-sensitive suites of R2614 were re-run on the FINAL "
    "committed tree through src/os/verify_writesensitive.py and their receipt "
    "is named in the backlog line, not assumed; (e) src/os still carries "
    "hundreds of one-off closeout scripts, pre-existing bloat this window "
    "neither created nor cleaned, and this window added exactly one file; (f) "
    "tasks.md was not touched, it is the P-47 canonical board; (g) Docker is "
    "absent on this host; (h) BigDomain-OSLoop still reads InteractiveToken "
    "and needs an ELEVATED shell for its S4U re-registration (carried "
    "ceo-pending physical item loop-s4u-reconcile).",
    "R2729 tokens: local=~16k api=0 api_reason=adoption window - one "
    "five-silence scan with the debt gate and the queue head, one shipped read "
    "tool with a ten-check self-check, three bounded progress polls and one "
    "kernel liveness probe on a live leg, one byte-level adoption measurement "
    "with an independent criteria recount of 5014, one designed matrix FAIL "
    "then one stamp-aligned regeneration checked DOC-CURRENT, one four-section "
    "follow-up with the verdict append, one debt close and one debt append "
    "with readback, one write-sensitive receipt on the final committed tree, "
    "and the state/export/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2729p_")
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
        "R2725 电池腿已按其证据路径验收全绿并关债（673 套件/5014 判据·零 FAIL·"
        "RUNNER PASS 6412s），矩阵已按本轮绿腿重压；下一步开队头 AC-EPTYP1 产品面")
    face["latest_artifact"] = (
        "src/os/leg_status.py 电池腿单一只读判读面（2026-11-14 R2729·一条判定行"
        "+退出码·自检 10/10 含 summary 行误计陷阱断言）")
    face["last_artifact"] = (
        "docs/sandbox-suite-matrix.md 按 R2725 绿腿重压至 673 行 71255B"
        "（2026-11-14 R2729·DOC-CURRENT）")
    face["next_milestone"] = (
        "下一窗：开队头 state/queue/tech.md:697 AC-EPTYP1 产品面（形状表把 CODE "
        "当 shape NAME → CODES[shapes[0]] 在该面本该拒的载荷上 KeyError），"
        "判据 AC-EPTYP1..AC-EPTYP6 已在册；该窗会动注册表，之后欠一条全量电池")
    face["next_milestone_due"] = "2026-11-15T22:00:00+08:00"
    face["updated_at"] = now.astimezone(
        datetime.timezone(datetime.timedelta(hours=8))).replace(
            microsecond=0).isoformat()
    doc["ceo_face"] = face
    doc["export_ts"] = stamp
    doc["do"] = (
        "2026-11-14 R2729 ADOPTION window: the R2725 reconcile battery was "
        "adopted green off qa/reconcile-all-R2725.log (673 suites, 5014 "
        "criteria, zero FAIL, RUNNER PASS 6412s), the matrix was restamped "
        "stamp-aligned from that leg, the verdict block was appended and the "
        "debt row was closed; one read-only leg-status tool shipped with a "
        "10/10 self-check.")
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
        fh.write("2026-11-14 %s tick 2725 R2729 R2725 battery adopted green "
                 "673/5014, matrix restamped, debt closed\n"
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
