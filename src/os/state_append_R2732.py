"""R2732 monitored-wait + verified debt sweep closeout: state, export, heartbeat."""

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

NEW_DEC_TOKENS = ["D-20261114-01", "D-20261114-02", "D-20261114-03"]

LINES = [
    "2026-11-14 R2732 WINDOW: the R2731 battery leg was measured live at open "
    "through the shipped reader and was NOT adopted, because it is still "
    "running: src/os/leg_status.py read LEG-ALIVE-NO-EVIDENCE pid=59208 "
    "bytes=580037 lines=3963 pass=331 fail=0 remaining=343 target=674, and the "
    "pid chain was confirmed by command line (battery_stream 59208 -> "
    "reconcile_all 61200 -> the running suite child), not by the pid file "
    "alone. THREE SAMPLES showed the tail is where the wall clock goes: 330 "
    "suite rows at 18:26, 331 at 18:28, 333 at 18:38, i.e. the 331-suite "
    "mean of 6.69s projects 38 minutes for the remainder but the last two "
    "completed rows measured 296.4s and 151.5s, so the honest reading is that "
    "the remainder carries the heavy apimarket block and CANNOT be judged "
    "inside a 25 minute window. No relaunch, no second launch, no evidence "
    "path touched.",
    "R2732 FIVE-SILENCE SCAN, on content addressing rather than row counts: "
    "[LEDGER] zero @BigDomain rows in the group evolution ledger (atbd_lines=0, "
    "unreplied_groups=0); [ORD] the group orders tail is still the 2026-11-14 "
    "00:30 main-control row, older than the carried 01:3x baseline; [BENCH] "
    "benchmarks_refreshed=2026-11-14, inside the seven day gate; [GIT] empty "
    "git status at HEAD b87984d1 with no index.lock; [DEC] THREE new ids, and "
    "all three were read in full and judged NON-SURFACE for this company, so "
    "each is acknowledged and none is executed: D-20261114-01 reverses the "
    "BigLife PARKED state and fixes the main-control park criterion for "
    "OSLoop-driven lines (BigLife/BigHouse surface), D-20261114-02 dispatches "
    "the FluxVerse life-event supply repair (FluxVerse surface), "
    "D-20261114-03 registers bm-a's 68/22 sync lag and explicitly says the "
    "closeout order is NOT re-dispatched (bm-a machine surface). Baseline "
    "carried forward by union: last_dec_tokens 263 -> 266.",
    "R2732 THE DEBT REGISTER WAS SWEPT BY VERIFICATION, NOT BY GUESS, because "
    "R2731 carried the 50 stale product-face rows as a declared gap for "
    "exactly this: a window that can verify the rows. Method, applied to all "
    "52 open rows: parse the queue path, line number, prefix and face module "
    "each row names in its own note, re-read that queue line NOW, and require "
    "(a) the line reads [x], (b) the line carries NO superseded and NO carried "
    "marker, and (c) the face module named in the note exists on disk WITH its "
    "test file. 17 rows passed all three and were closed through the shipped "
    "writer src/os/debt_close.py --round R2732, every one reading wrote=yes "
    "readback=ok: R2511 R2513 R2515 R2517 R2522 R2523 R2524 R2525 R2526 R2531 "
    "R2533 R2649 R2714 R2716 R2718 R2720 R2723. Independent readback: rows 420, "
    "open 52 -> 35, and exactly 17 rows carry closed=R2732. The 33 excluded "
    "rows were NOT closed and are named here for the next window rather than "
    "silently dropped: 8 name no parseable queue line, 25 either point at a "
    "queue line still open or at one whose text carries a superseded/carried "
    "marker, which is the hazard that made a blind batch sweep unsafe.",
    "R2732 THE GATE SIGNAL IS CLEANER AND NOT MISREAD: debt_gate --check still "
    "reads CLAIM-FIRST item=reconcile-battery-R2730 first=1, now against open=35 "
    "instead of 52, and the note is unchanged because the battery rule is "
    "unchanged. This window moved NO product src byte and NO registry row, so "
    "the registry stays at 674 suites / 5020 criteria measured by import this "
    "window (674 unique names), and no successor battery is owed on top of the "
    "one already open. The queue head was re-read and remains "
    "state/queue/tech.md:702 prefix AC-CEPB1 with claimable=12.",
    "R2732 honest disclosures: (a) ZERO product points by the Executive "
    "Protocol scale - a verified debt sweep is bookkeeping even when every row "
    "is checked, this window shipped no artifact a CEO can newly open, and "
    "every P-47 business face still waits on CEO physical pieces (merchant id, "
    "mini-program appid/secret); (b) this window is a monitored wait, which "
    "the abolished idle-fast path does NOT excuse: work was pulled from a "
    "named chronic gap instead of re-scanning the same waiting object, and no "
    "claimable product byte was skipped because product bytes are frozen by "
    "the R2168 mixed-tree rule until this very battery is green; (c) the 17 "
    "discharge notes carry the round only, not the verification method - the "
    "method and the exact item list are in the two log lines above, disclosed "
    "so a reader of state/debt.md alone does not over-read them; (d) the "
    "remaining 35 open rows include 33 product-face rows this sweep "
    "deliberately did not touch, so DEBT-STALE will keep reading on until a "
    "later window verifies those; (e) Docker is absent on this host; (f) "
    "tasks.md was not touched, it is the P-47 canonical board; (g) "
    "BigDomain-OSLoop was re-read this window and still reads "
    "InteractiveToken/Limited, which the 2026-09-29 machine law forbids for "
    "lane tasks, and the fix still needs an ELEVATED shell (carried "
    "ceo-pending physical item loop-s4u-reconcile).",
    "R2732 tokens: local=~16k api=0 api_reason=monitored-wait plus verified "
    "sweep - one five-silence scan on tokens and tails, three rounds of "
    "three new decision rows read and judged, one shipped-reader liveness "
    "reading plus a command-line pid chain probe, three bounded progress "
    "samples with a per-suite duration projection, one register parse with a "
    "three-part verification rule over 52 rows, seventeen shipped-writer "
    "closes with an independent readback, one gate re-read and one queue head "
    "re-read, and the state/export/heartbeat closeout; zero cloud calls and "
    "zero external API touches",
]


def append_state():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))

    tokens = list(data.get("last_dec_tokens") or [])
    for item in NEW_DEC_TOKENS:
        if item not in tokens:
            tokens.append(item)

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + LINES
    expected["tick"] = tick + 1
    expected["last_dec_tokens"] = tokens

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

    # The tokens array is one id per line; append the three new ids in place so
    # the document keeps its own layout and the canonical-form checker stays
    # clean, rather than re-serialising the whole file.
    token_rows = []
    opener = None
    closer = None
    for index, row in enumerate(bumped):
        if row.strip() == '"last_dec_tokens": [':
            opener = index
        elif opener is not None and row.strip() == '],':
            closer = index
            break
    if opener is None or closer is None:
        print("REFUSED tokens block not found")
        return 3
    existing = set()
    for row in bumped[opener + 1:closer]:
        existing.add(row.strip().rstrip(",").strip('"'))
    add = [t for t in NEW_DEC_TOKENS if t not in existing]
    if add:
        last = closer - 1
        bumped[last] = bumped[last].rstrip().rstrip(",") + ","
        for index, item in enumerate(add):
            suffix = "," if index < len(add) - 1 else ""
            bumped.insert(closer + index, "    " + json.dumps(item) + suffix)
        shift = len(add)
        end += shift
    token_rows = bumped

    out = state_io.EOL.join(token_rows[:end] + inserted + token_rows[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2732p_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d tokens=%d"
          % (tick + 1, after["bytes"], after["log_len"], len(tokens)))
    return 0


def refresh_export():
    with io.open(EXPORT, encoding="utf-8") as fh:
        doc = json.load(fh)
    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.replace(microsecond=0).isoformat()
    face = doc.get("ceo_face") or {}
    face["current"] = (
        "R2732 监控等待窗：R2731 电池腿（674 套件/5020 判据）仍在跑——实测 "
        "333/674 全绿零 FAIL，尾部是 300 秒级重套件，本窗不验收也不重启；"
        "空档做了债务台账的可核验清理（52 开放 → 35）")
    face["latest_artifact"] = (
        "state/debt.md 17 条产品面陈旧行按三重核验销账（2026-11-14 R2732·"
        "队列行已勾选+无 superseded/carried 标记+指名脸与其测试均在盘）")
    face["last_artifact"] = (
        "src/os/state_append_R2732.py 收账脚本（日志 6 行+决策基线并集+"
        "tick 镜像防 drift·2026-11-14 R2732）")
    face["next_milestone"] = (
        "下一窗：按证据路径 qa/reconcile-all-R2731.log 验收电池（当前 333/674·"
        "尾部重套件·建议窗内先读 leg_status 再决定是否守候），绿则重压矩阵+"
        "追加 verdict+关 reconcile-battery-R2730，然后开队头 AC-CEPB1 产品面")
    face["next_milestone_due"] = "2026-11-15T22:00:00+08:00"
    face["updated_at"] = now.astimezone(
        datetime.timezone(datetime.timedelta(hours=8))).replace(
            microsecond=0).isoformat()
    doc["ceo_face"] = face
    with io.open(os.path.join(HERE, "export_consistency_patterns.json"),
                 encoding="utf-8") as fh:
        label = json.load(fh)["tick_row_label"]
    with io.open(PATH, encoding="utf-8") as fh:
        tick_now = str(json.load(fh)["tick"])
    rows = [r for r in (doc.get("results") or [])
            if isinstance(r, list) and len(r) >= 2 and r[1] == label]
    if len(rows) == 1:
        rows[0][0] = tick_now
    doc["export_ts"] = stamp
    doc["do"] = (
        "2026-11-14 R2732 monitored-wait window: the R2731 battery leg was "
        "read live through the shipped reader (333/674 rows, zero FAIL, heavy "
        "apimarket tail) and was neither adopted nor relaunched; the stale "
        "product-face rows of the debt register were swept by a three-part "
        "verification rule and 17 were closed through the shipped writer "
        "(open 52 -> 35); no product src byte and no registry row moved.")
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
        fh.write("2026-11-14 %s tick 2728 R2732 R2731 leg live 333/674 zero "
                 "FAIL, debt 17 rows verified-closed open 52->35\n"
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
