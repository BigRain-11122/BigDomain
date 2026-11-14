"""R2730 closeout: board lines, state log + tick, export face, heartbeat."""

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
BACKLOG = os.path.join(HERE, "backlog.md")

BOARD = [
    "- [x] [done 2026-11-14 R2730] PRODUCT face on AC-EPTYP1..AC-EPTYP6 "
    "(state/queue/tech.md:697, pinned at R2725 BEFORE any code): shipped "
    "src/os/evidence_capture_precedence_shape_typing.py plus its six-criteria "
    "suite. MEASURED before any byte on the shipped face: with one refusal law "
    "patched to answer E_EBOM_UTF16, the R2725 report publishes code "
    "E_EBOM_UTF16 INSIDE the shape list (shapes [E_EBOM_UTF16, nul, utf8, "
    "tail]) and CODES[shapes[0]] raises KeyError on exactly the payload that "
    "face exists to refuse; this face keeps every list names-only, carries the "
    "code in its own unknown_code field and returns every six-known-shape "
    "answer unchanged. SUITE PASS 6/6 twice, identical digest 11835F727853560A "
    "(qa/evidence-capture-precedence-shape-typing-R2730b.log, 899B, utf-8 LF, "
    "landed BY the shipped capture callable), five adjacent suites green, live "
    "leg ACCEPT on qa/reconcile-all-R2725.log on BOTH readers; wired "
    "os-evidence-capture-precedence-shape-typing(6), registry 673 suites / "
    "5014 criteria -> 674 / 5020 measured by import, matrix restamped "
    "stamp-aligned at 674 rows after the designed ROWS-MISMATCH read 673 "
    "against 674 with no byte written.",
    "- [ ] [R2730] next window: THE BATTERY the debt gate names first "
    "(reconcile-battery-R2730, pre-registered 674 suites / 5020 criteria at "
    "R2730), owed BEFORE any product byte because R2730 moved product src "
    "(src/os/evidence_capture_precedence_shape_typing.py plus its six-criteria "
    "suite) and one registry row from 673 / 5014 to 674 / 5020. Re-measure the "
    "target by import before the launch and name any larger delta rather than "
    "sweeping it; run it on a CLEAN committed tree at exactly 674 / 5020; "
    "launch detached through src/os/battery_stream.py with the stream and the "
    "pid in SEPARATE files under logs/ and never a shell redirection into qa/; "
    "adopt it by its evidence path and NEVER relaunch it, settling any stall by "
    "a kernel liveness probe plus a child pid read rather than an empty WMI "
    "CommandLine list. On green: the four follow-up sections through "
    "src/os/battery_followup.py in the designed order (designed matrix FAIL "
    "first with NO byte written, then a stamp-aligned regeneration from THAT "
    "round own green leg, then the verdict append), close reconcile-battery-"
    "R2730 through the shipped debtor, and restamp docs/sandbox-suite-matrix.md "
    "from that leg. R2614 IS PRE-NAMED: if the leg is launched BEFORE the "
    "closeout commit, the fifteen write-sensitive suites must be re-run on the "
    "FINAL committed tree through src/os/verify_writesensitive.py --leg "
    "battery-R2730 --head <sha> --evidence qa/write-sensitive-R2730.log before "
    "any verdict. Then take queue head state/queue/tech.md:702 prefix "
    "AC-CEPB1 (claimable 12, floor FLOOR-MET 5/5 12/10 10/10) with criteria "
    "AC-CEPB1..AC-CEPB6 already pinned in that row at R2501 BEFORE any code: "
    "twelve closeout scripts hand their own composed text straight to "
    "closeout_export_parity_wire.publish and not one of them asks the binding, "
    "so the caller set must be DERIVED from the tree at call time and each "
    "caller reported BOUND / UNBOUND / OUT-OF-SCOPE. Carried: Docker is absent "
    "on this host; tasks.md is the P-47 canonical board and is not ours to "
    "edit; BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED "
    "shell for its S4U re-registration (ceo-pending physical item "
    "loop-s4u-reconcile).",
]

LINES = [
    "2026-11-14 R2730 PRODUCT window on AC-EPTYP1..AC-EPTYP6 "
    "(state/queue/tech.md:697, pinned at R2725 BEFORE any code): shipped "
    "src/os/evidence_capture_precedence_shape_typing.py plus "
    "src/os/test_evidence_capture_precedence_shape_typing.py. Five readings at "
    "open: git status EMPTY at HEAD fa8c67d6 equal to origin/main with no "
    "index.lock; ZERO @BigDomain rows in the group ledger; the "
    "content-addressed decisions face read cur=77 base=263 new=0 (the four "
    "raw hits were substring cuts of already-carried B- tokens); the group "
    "orders tail is the 2026-11-14 00:30 main-control row OLDER than the "
    "carried baseline; benchmarks_refreshed 2026-11-14 inside the seven-day "
    "gate. debt_gate read CLAIM-FIRST item=product-face-R2729, queue_head read "
    "tech line=697 prefix AC-EPTYP1 claimable=13, queue_floor read FLOOR-MET "
    "5/5 13/10 10/10.",
    "R2730 THE DEFECT WAS RE-MEASURED ON A PRIVATE WORLD BEFORE ANY BYTE, not "
    "taken from the queue note: with the shipped BOM-guard law patched to "
    "answer E_EBOM_UTF16 for a byte-order-marked payload, the R2725 face "
    "published code E_EBOM_UTF16 beside shapes ['E_EBOM_UTF16','nul','utf8',"
    "'tail'] and EPD.CODES[shapes[0]] raised KeyError 'E_EBOM_UTF16', and on a "
    "payload earning ONLY that shape the list was the code alone and raised "
    "the same KeyError - so a names-only consumer breaks on exactly the bytes "
    "the face exists to refuse, while shape_codes stayed well typed. This face "
    "publishes NAMES ONLY, carries the code no name can place in its own "
    "unknown_code field, and returns every six-known-shape answer unchanged "
    "(the R2725 report dict is returned as-is when its first code is placed in "
    "its own list).",
    "R2730 PROOF: AC-EPTYP1..AC-EPTYP6 SUITE PASS 6/6 twice through its own "
    "process with an IDENTICAL digest 11835F727853560A "
    "(qa/evidence-capture-precedence-shape-typing-R2730b.log, 899B, utf-8, "
    "bom=False, crlf=0, lone_cr=0, nul=0, legs=2 identical=True adjacent=5 "
    "fails=0), and the log itself was landed BY the shipped capture callable so "
    "a red capture could not become an artifact. Adjacent green: "
    "test_evidence_capture_precedence_unknown_shape, _derived, "
    "_compound_refusal, _tail_guard and _utf8_capture_bom_guard, all 6/6. The "
    "bounded live leg measured the SAME fixture on BOTH readers: "
    "qa/reconcile-all-R2725.log (1227962B) reads ACCEPT on the R2725 face and "
    "ACCEPT on this face.",
    "R2730 REGISTRY, BOARD AND MATRIX: one runner row "
    "os-evidence-capture-precedence-shape-typing(6) wired after the "
    "unknown-shape row; docs/sandbox-suite-matrix.md read ROWS-MISMATCH first "
    "(doc-rows 673 against registry 674 at 5020 criteria) with NO byte "
    "written, and was then restamped stamp-aligned at 674 rows, 71388 bytes, "
    "--check DOC-CURRENT; tech row 697 was closed with its discharge note and "
    "the queue head is now state/queue/tech.md:702 prefix AC-CEPB1 with "
    "claimable 12 and queue_floor still FLOOR-MET 5/5 12/10 10/10 (no seed was "
    "needed: 12 sits above the 10 floor). Registry 673 suites / 5014 criteria "
    "-> 674 / 5020 measured by import at 674 unique names and 674 unique "
    "paths.",
    "R2730 DEBT THROUGH THE SHIPPED WRITERS: product-face-R2729 was closed at "
    "line 436 (open 51->50, done 367->368, 235537B -> 235540B, readback ok), "
    "product-face-R2730 was appended first=no at 235540B -> 236062B naming "
    "queue head state/queue/tech.md:702 prefix AC-CEPB1 with claimable 12 and "
    "criteria AC-CEPB1..AC-CEPB6 pinned there at R2501 BEFORE any code, and "
    "reconcile-battery-R2730 was appended first=yes at 236062B -> 236687B "
    "because this window moved product src bytes and one registry row, so the "
    "R2168 mixed-tree rule puts the FULL battery on the committed tree BEFORE "
    "the next product byte. debt_gate now reads CLAIM-FIRST "
    "item=reconcile-battery-R2730 at 674 suites / 5020 criteria.",
    "R2730 TWO OWN DEFECTS WERE BORN HERE AND EACH WAS REPAIRED AT ITS BIRTH "
    "SITE, disclosed rather than smoothed: (1) the first evidence leg landed "
    "with VERDICT RED even though both suite legs were green, because the "
    "driver tested 'SUITE PASS' against the wrong list index (its own header "
    "line) - the red file qa/evidence-capture-precedence-shape-typing-R2730.log "
    "is KEPT as evidence, the verdict expression was repaired to read the "
    "per-leg tails, and the corrected log was landed at a NEW path ending "
    "R2730b rather than relaunching over the same one (the capture guard "
    "refuses an existing target anyway); (2) the suite own AC-EPTYP6 import "
    "scanner counted a docstring continuation line beginning 'from the shipped "
    "chain ...' as an import, so the scanner now requires ' import ' on a "
    "'from' line and the criterion was NOT loosened.",
    "R2730 honest disclosures: (a) ONE product point by the Executive Protocol "
    "scale - a runnable typing face with a green six-criteria suite, five "
    "adjacent suites green and a live reading on both readers - but nothing a "
    "CEO can newly open, and every P-47 business face still waits on CEO "
    "physical pieces (merchant id, mini-program appid/secret); (b) this window "
    "DID NOT run a battery and claims none: it moved product src bytes and one "
    "registry row, so reconcile-battery-R2730 is registered first=yes and the "
    "matrix green line is one leg behind BY DESIGN until that battery lands; "
    "(c) the matrix was restamped at 674 rows citing the R2725 leg (673 "
    "suites), the same stamp-aligned pattern R2725 used, and the mismatch "
    "between cited-leg rows and document rows is named here rather than left "
    "for a reader to discover; (d) src/os still carries hundreds of one-off "
    "closeout scripts, pre-existing bloat this window neither created nor "
    "cleaned, and this window added three files (face, suite, evidence driver) "
    "plus one board-closing script; (e) tasks.md was not touched, it is the "
    "P-47 canonical board; (f) Docker is absent on this host; (g) "
    "BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell "
    "for its S4U re-registration (carried ceo-pending physical item "
    "loop-s4u-reconcile).",
    "R2730 tokens: local=~15k api=0 api_reason=product window - one "
    "five-silence scan with the debt gate, the queue head, the queue floor and "
    "the ledger face, one private-world probe of the shape-typing defect "
    "before any byte, one face plus one suite shipped, one suite run twice "
    "with an identical digest and five adjacent suites, one red evidence leg "
    "and one over-broad import scanner each repaired at its birth site, one "
    "registry count by import on four axes, one designed matrix ROWS-MISMATCH "
    "then one stamp-aligned regeneration checked DOC-CURRENT, one board close, "
    "one debt close and two debt appends with readback, and the "
    "state/export/heartbeat closeout; zero cloud calls and zero external API "
    "touches",
]


def prepend_board():
    text = io.open(BACKLOG, "rb").read().decode("utf-8")
    head = "\n".join(BOARD) + "\n"
    if text.startswith("- [x] [done 2026-11-14 R2730]"):
        print("BOARD already carries the R2730 lines")
        return 0
    payload = head + text
    io.open(BACKLOG, "wb").write(payload.encode("utf-8"))
    print("BOARD ok bytes=%d" % len(payload.encode("utf-8")))
    return 0


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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2730p_")
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
        "R2730 产品面已交付：形状列表只放形状名、放不进名字表的码进独立 "
        "unknown_code 字段（注册表 674 套件/5020 判据）；债务闸点名一条全量电池")
    face["latest_artifact"] = (
        "src/os/evidence_capture_precedence_shape_typing.py 形状类型面 + 六判据套件"
        "（2026-11-14 R2730·双腿同一摘要 11835F727853560A·证据 "
        "qa/evidence-capture-precedence-shape-typing-R2730b.log 899B·五邻域全绿）")
    face["last_artifact"] = (
        "docs/sandbox-suite-matrix.md 重压至 674 行 71388B"
        "（2026-11-14 R2730·先按设计读 ROWS-MISMATCH 673 对 674 零写入，再 DOC-CURRENT）")
    face["next_milestone"] = (
        "下一窗：在干净提交树上跑全量电池 674/5020（reconcile-battery-R2730），"
        "按其证据路径验收并重压矩阵；之后开队头 state/queue/tech.md:702 AC-CEPB1")
    face["next_milestone_due"] = "2026-11-15T23:00:00+08:00"
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
        "2026-11-14 R2730 PRODUCT window: shipped "
        "src/os/evidence_capture_precedence_shape_typing.py plus its "
        "six-criteria suite so every published shape list stays names-only and "
        "the code no shape name can place rides in its own unknown_code field; "
        "registry 673 suites / 5014 criteria -> 674 / 5020 measured by import, "
        "the matrix restamped stamp-aligned at 674 rows, one queue row closed "
        "and a full battery registered as owed before the next product byte.")
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
        fh.write("2026-11-14 %s tick 2726 R2730 shape typing face, registry "
                 "674/5020, battery owed\n"
                 % datetime.datetime.now().strftime("%H:%M:%S"))
    print("HEARTBEAT ok")
    return 0


if __name__ == "__main__":
    rc = prepend_board()
    if rc:
        sys.exit(rc)
    rc = append_state()
    if rc:
        sys.exit(rc)
    rc = refresh_export()
    if rc:
        sys.exit(rc)
    sys.exit(append_heartbeat())
