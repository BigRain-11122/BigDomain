"""closeout_R2347 - append this window round to state.json (R2347).

The figures written here are the ones measured this window, not estimates: the
battery verdict and its pre-registered target, the four follow-up sections, the
tooling defect the matrix face exposed and its repair, and the carried product
head.

State text is edited in place on its own canon (CRLF, 16-space log items) and
then passed through state_io.canon with a read-back proof. Dry run by default;
--execute writes. Pure ASCII source, stdlib only.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

TICK = 2347
STAMP = "2026-11-01T22:20:00+08:00"
HEARTBEAT_LINE = (
    "R2347: battery on the committed R2346 tree read RUNNER PASS 481/481 "
    "suites plus controls 7/7 in 917.3s with criteria total 3862 exactly as "
    "pre-registered; the designed matrix FAIL exposed a real tooling defect - "
    "one suite reported a -3.5s wall time, the duration group refused the "
    "minus, that suite dropped out of the parse, and the whole 481-suite "
    "regression record became ineligible for default discovery, so the "
    "follow-up compared two different evidence files; the minus is now "
    "accepted and carried visibly, the record is eligible again, all four "
    "sections PASS at 46044B and VERDICT R2347 PASS\n"
)

sys.path.insert(0, BASE)
import state_io as SIO  # noqa: E402

ROUND_LINE = (
    "2026-11-01 R2347 verification window (five-silence scan clean at open: "
    "empty git status --short and no .git/index.lock at f13bcff2; the python "
    "twin reads LEDGER atbd_lines=0 unreplied_groups=0 and DEC rows=101 "
    "tokens=65 new=0, so no decision row was owed; the local orders board "
    "tail is unchanged; benchmarks refreshed 2026-11-01, inside the "
    "seven-day gate). FIRST ITEM, the debt gate carried: THE BATTERY ON THE "
    "COMMITTED R2346 TREE with an empty git status before the run (the R2168 "
    "mixed-tree rule), pre-registered at 481 suites / 3862 criteria - "
    "exactly +1 suite / +6 criteria against R2346 (480/3856) from the "
    "os-stamp-exempt-guard suite. MEASURED: RUNNER PASS 481/481 suites green "
    "plus controls 7/7 in 917.3s with birth-site TMP RECLAIM 932/932 worlds "
    "326.59 MiB busy=0 failed=0 (qa/reconcile-all-R2347.log, 797022B after the "
    "follow-up block, single writer utf-8 LF through src/os/battery_stream.py, "
    "never a shell redirection), criteria total 3862 - the prediction matched "
    "the measurement with no correction and no swept delta. THE FOLLOW-UP "
    "FAILED THREE TIMES AND THE FAILURES WERE A REAL TOOLING DEFECT, not a "
    "retry problem: the matrix section reported on-disk=45956B "
    "regenerated=46047B, and after a regeneration the byte counts matched "
    "while the tool's own --check still read stale. Root cause measured at "
    "the birth site: ledger-datasub-coveragedualpersist reported a NEGATIVE "
    "wall time (-3.5s) in this run, SUITE_RE's duration group was "
    "[0-9.]+ so the minus dropped that line, 480 of 481 suite lines parsed, "
    "len(suites) != runner green made the whole record INELIGIBLE for "
    "default discovery, suite_matrix silently fell back to the R2346 log "
    "(46045B) while the follow-up's regeneration used this round's log "
    "(46047B), and the two legs could therefore never agree. REPAIRED AT THE "
    "BIRTH SITE of the false negative in src/sandbox/suite_matrix.py: the "
    "duration group now accepts an optional leading minus and the odd value is "
    "CARRIED into the doc rather than dropped, with the defect recorded in a "
    "comment beside the regex. AFTER the repair: default discovery reads "
    "qa/reconcile-all-R2347.log again, 481 entries parse, the doc regenerates "
    "at 46044B with green=481/481, and all four follow-up sections read PASS "
    "(matrix byte-identical 46044B, fingerprint CLEAN 5 domains, profile "
    "--daily --check byte-identical, census DRIFT-CLEAN), closing VERDICT "
    "R2347 PASS with 1950B appended. NO PRODUCT FACE WAS SHIPPED: the queue "
    "head still reads state/queue/tech.md:393 prefix AC-RAP1 (retire_apply, "
    "claimable=10) and it is carried to the next window rather than "
    "half-built."
)

TOKENS_LINE = (
    "R2347 tokens: local=~13k api=0 api_reason=verification window that "
    "turned into one tooling repair - one full reconcile battery (481 suites, "
    "3862 criteria, 917.3s) with its streamed evidence file, three failed "
    "follow-up attempts that measured a real discovery defect, one birth-site "
    "regex repair in suite_matrix.py with its documenting comment, one matrix "
    "regeneration and one clean four-section re-run, one evidence-log repair "
    "of this window own duplicate blocks, and the state/export/heartbeat/board "
    "closeout; zero cloud calls and zero external API touches; the product "
    "face resumes at R2348 on AC-RAP1"
)

SELF_HEAL = (
    "R2347 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-seventh consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

DECISION_LINE = (
    "R2347 decision gate (D-20260930-19 step 2): the content-addressed diff "
    "of the group decisions.md against the stored baseline read NO new tokens "
    "(new=[] over 65 live tokens), and the evolution ledger carries no "
    "@BigDomain row, so nothing was executed, rejected or acknowledged this "
    "window and the baseline is unchanged."
)

DISCLOSURES = (
    "R2347 honest disclosures: (a) this window shipped NO product module and "
    "scores 0 product points; its work was the battery the register carried "
    "plus the repair that battery's own follow-up exposed. (b) The matrix "
    "repair WIDENS a parser and that is stated plainly rather than dressed as "
    "a green: the duration group now accepts a leading minus because the "
    "runner genuinely emitted -3.5s, and the negative value is carried into "
    "the doc so an odd duration stays visible. The underlying negative wall "
    "time itself was NOT repaired - it is a runner timing artefact across a "
    "clock step and is named here rather than silently absorbed. (c) THIS "
    "WINDOW DAMAGED ITS OWN EVIDENCE and repaired it: three failed follow-up "
    "attempts each appended a SECTION block, 6155B of duplicate verdict "
    "bodies inside qa/reconcile-all-R2347.log; the file was cut back to the "
    "pure battery body (795072B) before the single good run, and the final "
    "797022B therefore carries exactly one follow-up block. (d) The matrix doc "
    "was regenerated three times before it settled: 46045B against the "
    "fallback R2346 evidence, 46047B against this round's log through the "
    "unrepaired regex, and 46044B through the repaired one - the byte counts "
    "are named because they are how the defect was found. (e) The four "
    "follow-up sections were run against the repaired tool only once for the "
    "record; the earlier legs are disclosed here rather than kept as evidence "
    "files, because they measured a defect this window then fixed rather than "
    "a round outcome. (f) tasks.md was left untouched: it is the P-47 "
    "canonical board and carries no row for a verification window, disclosed "
    "rather than silently skipped."
)

BOARD_LINE = (
    "- [x] [done 2026-11-01 R2347] verification window: THE BATTERY ON THE "
    "COMMITTED R2346 TREE with an empty git status before the run - RUNNER "
    "PASS 481/481 suites green plus controls 7/7 in 917.3s with birth-site TMP "
    "RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 (qa/reconcile-all-"
    "R2347.log, 797022B, single utf-8 LF writer through "
    "src/os/battery_stream.py), criteria total 3862 EXACTLY as pre-registered "
    "against R2346 (480/3856). The designed matrix FAIL exposed a REAL "
    "TOOLING DEFECT rather than a stale doc: ledger-datasub-coveragedualpersist "
    "reported a negative wall time (-3.5s), SUITE_RE's [0-9.]+ duration group "
    "dropped that line, 480 of 481 suite lines parsed, the block no longer "
    "matched the runner count, and _evidence_eligible therefore rejected the "
    "whole record - so default discovery fell back to the R2346 log while the "
    "follow-up regenerated from R2347 and the two legs could never agree. "
    "Repaired at the birth site in src/sandbox/suite_matrix.py (optional "
    "leading minus, odd value carried visibly, defect documented beside the "
    "regex); after the repair discovery reads this round's log again, 481 "
    "entries parse, the doc regenerates at 46044B green=481/481, and all four "
    "follow-up sections PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile byte-identical, census DRIFT-CLEAN), VERDICT R2347 PASS. "
    "Zero product code, 0 product points; the queue head line 393 AC-RAP1 "
    "retire_apply is carried, not half-built."
)

EXPORT_CN = (
    "R2347 验证窗：已提交 R2346 树上的全量校准电池 481/481 套件全绿、3862 "
    "判据与预注册逐字吻合（917.3 秒）。跟进四段的矩阵段按设计先红，红的不是"
    "文档陈旧而是真缺陷：某套件本轮报出 -3.5 秒的负墙钟，矩阵的时长正则只收"
    "非负数，该行被丢掉，481 行只解析出 480 行，整份回归记录因此被判「不适格」"
    "而回退到上一轮日志，跟进的两条腿永远对不上。已在源头修复（允许负号且把"
    "异常时长写进文档可见处），修复后 481 行全解析、文档重生成 46044B、四段全过，"
    "VERDICT R2347 PASS。本轮无新产品面，队头 AC-RAP1 retire_apply 留到下轮。"
)

EXPORT_ARTIFACT = (
    "src/sandbox/suite_matrix.py 修复 + qa/reconcile-all-R2347.log（797022B，"
    "481/481 套件、3862 判据、单写者 UTF-8 LF）+ docs/sandbox-suite-matrix.md"
    "（46044B，green=481/481，由本轮日志生成）"
)

EXPORT_NEXT = (
    "R2348：先按债务闸跑全量电池（预注册 482 套件 / 3868 判据，即本轮补上的 "
    "os-retire-apply 套件；若该产品面未交付则维持 481/3862 并说明），再按队头 "
    "line 393 AC-RAP1 交付 retire_apply（把已接受的退役真正移入隔离目录，永不删除）"
)


def items():
    return [ROUND_LINE, TOKENS_LINE, SELF_HEAL, DECISION_LINE, DISCLOSURES]


def bump(text):
    """Edit the live state text in place: tick, then five log items appended."""
    old_tick = '"tick": %d,' % (TICK - 1)
    if text.count(old_tick) != 1:
        raise SystemExit("E_CLOSE_TICK: expected exactly one %r" % old_tick)
    text = text.replace(old_tick, '"tick": %d,' % TICK)
    head, tail = text.rsplit("\r\n  ]\r\n}\r\n", 1)
    if tail.strip():
        raise SystemExit("E_CLOSE_TAIL: unexpected tail %r" % tail[:40])
    pieces = []
    for item in items():
        body = json.dumps(item, ensure_ascii=True)
        pieces.append("\r\n                " + body)
    if not head.rstrip().endswith(","):
        head = head.rstrip() + ","
    return head + ",".join(pieces) + "\r\n  ]\r\n}\r\n"


def write_export(execute):
    with io.open(EXPORT, encoding="utf-8") as handle:
        doc = json.load(handle)
    doc["export_ts"] = STAMP
    doc["do"] = EXPORT_CN
    face = doc.setdefault("ceo_face", {})
    face["current"] = EXPORT_CN
    face["latest_artifact"] = EXPORT_ARTIFACT
    face["last_artifact"] = EXPORT_ARTIFACT
    face["next_milestone"] = EXPORT_NEXT
    face["next_milestone_due"] = "2026-11-03T22:20:00+08:00"
    face["updated_at"] = STAMP
    body = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    print("EXPORT keys=%d bytes=%d" % (len(doc), len(body.encode("utf-8"))))
    if execute:
        temp = EXPORT + ".closeout-tmp"
        with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
        os.replace(temp, EXPORT)


def main(argv):
    execute = "--execute" in argv
    with open(STATE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    new_text = bump(text)
    before = json.loads(text)
    after = json.loads(new_text)
    same = all(after[key] == before[key] for key in before
               if key not in ("log", "tick"))
    grew = len(after["log"]) == len(before["log"]) + len(items())
    canon = SIO.canon(new_text)
    print("CLOSEOUT R2347 tick=%d items=%d log=%d->%d fields_same=%s "
          "canon_bytes=%d"
          % (after["tick"], len(items()), len(before["log"]), len(after["log"]),
             same, len(canon.encode("utf-8"))))
    if not (same and grew and after["tick"] == TICK):
        print("E_CLOSE_SHAPE: refusing to write")
        return 2
    if not execute:
        print("DRY RUN: pass --execute to write")
        write_export(False)
        return 0
    if SIO.canon(canon) != canon:
        print("E_CLOSE_CANON: the text is not in the state canon")
        return 2
    temp = STATE + ".closeout-tmp"
    with open(temp, "wb") as handle:
        handle.write(canon.encode("utf-8"))
    os.replace(temp, STATE)
    written = len(canon.encode("utf-8"))
    with open(STATE, "rb") as handle:
        back = handle.read()
    ok = (back.decode("utf-8") == canon
          and json.loads(back.decode("utf-8"))["tick"] == TICK)
    print("WROTE %s bytes=%d READBACK ok=%s" % (STATE, written, ok))
    if not ok:
        return 2
    write_export(True)
    with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(HEARTBEAT_LINE)
    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        board = handle.read()
    # R2347 defect found while using it: the first guard used
    # BOARD_LINE.split("]")[0], which is just '- [x' and is always present, so
    # the run reported "already carries this row" while the row was nowhere on
    # the board. The key below is the round marker the row actually carries.
    if "[done 2026-11-01 R2347]" in board:
        print("BOARD already carries this row")
    else:
        with io.open(BACKLOG, "w", encoding="utf-8", newline="") as handle:
            handle.write(BOARD_LINE + "\n" + board)
        print("BOARD row prepended bytes=%d" % len(BOARD_LINE))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))