"""R2318 closeout: state, export, heartbeat, board, queue floors.

This window was a VERIFICATION window: the R2317 battery came back red,
its four root causes were repaired at their birth sites, and the retry
battery on the committed repair tree read green. Nothing product-facing
changed, so the successor is the product face the debt register already
named.

ASCII source; the Chinese CEO face lives in docs/status-export.json.

Usage: python src/os/close_R2318.py
"""

import datetime
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402
import state_fold as SF  # noqa: E402
import state_io as SIO  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEART = os.path.join(ROOT, "heartbeat.txt")
BOARD = os.path.join(ROOT, "src", "os", "backlog.md")

NOW = datetime.datetime.now().astimezone()
NOW_ISO = NOW.isoformat(timespec="seconds")
DUE = (NOW + datetime.timedelta(hours=44)).isoformat(timespec="seconds")

ROUND_LOG = (
    "2026-11-01 R2318 verification window (five-silence scan clean at open: "
    "empty git status --short and no index.lock; decisions.md carried 84 "
    "non-empty rows equal to the stored baseline and the token diff read 57 "
    "tokens with ZERO new, so no decision row is owed; the group ledger carried "
    "the same three @BigDomain patrol rows already paid off, the last one "
    "P-20261026-0930 acked at R2311, with zero unreplied numbered handoffs; the "
    "group orders tail was unchanged at the 2026-10-31 18:23 baseline; "
    "benchmarks refreshed 2026-10-29 inside the seven-day gate). The debt gate "
    "named product-face-R2318 and its note matched the board top: run the "
    "battery on the committed R2317 tree with zero product edits until green "
    "(the R2168 mixed-tree rule). FIRST RUN ON c41ad61b WAS RED: 462/466 suites "
    "green, 5 failed assertions, criteria total 3772 in 776.8s (qa/reconcile-"
    "all-R2318.log kept as the red leg). Four root causes, all real and none of "
    "them in product code: (1) the lobby suite hardcoded a November row and a "
    "'2026-11' read while its world rows are stamped by the wall clock, so on "
    "the first day of November the hardcoded month stopped being the month with "
    "no other activity (AC-S52/AC-S53); (2) the ledger datasub coverage gate "
    "suite did the same thing on the record-time window axis (AC-CVGG7); (3) "
    "the R2317 fold 616 moved the R2302 and R2303 log blocks into the archive, "
    "so both rounds became live residue with no triage entry (AC-RTR6, the "
    "known fold-creates-residue law from R2311); (4) the R2316 correction-rerun "
    "evidence pair appeared to the identity audit as an undischarged byte claim "
    "(AC-RID8). REPAIRS, all at their birth sites and committed alone as "
    "a6377a07: both fixtures now derive the quiet month from the world own "
    "record stamps (the criterion intent is untouched - one month carries the "
    "live rows, the adjacent month carries none), the residue declaration "
    "carried 187 -> 189 entries naming R2302 and R2303 off their live DELIVERED "
    "reading with the fold as the reason (32378B -> 33107B, predicted equal to "
    "measured, atomic replace, read-back proof), and the R2316 pair was "
    "disclosed in the identity baseline rather than renamed (1630B -> 2173B, "
    "2 -> 3 known bases). All four suites then read green individually. RETRY "
    "BATTERY on the committed repair tree a6377a07 with an empty git status = "
    "RUNNER PASS 466/466 suites green plus controls 7/7 in 749.0s with "
    "birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy zero failed zero "
    "(qa/reconcile-all-R2318-retry.log, 785400B, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), criteria total 3772 - "
    "exactly the pre-registered +1 suite / +6 criteria against R2316 "
    "(465/3766) from the R2317 os-gate-decl-retire suite, so the prediction "
    "matched the measurement with no correction. Four follow-up sections ran "
    "through src/os/battery_followup.py: the matrix section FAILED first on the "
    "stale doc (on-disk=44685B regenerated=44771B) and did NOT rewrite it, which "
    "is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 466 suites / 3772 criteria (44771B) and the "
    "re-run read all four sections PASS, VERDICT R2318 PASS. Zero product code "
    "changed, so this window honestly scores 0 product points."
)

TOKENS_LOG = (
    "R2318 tokens: local=~26k api=0 api_reason=verification-only window that "
    "turned into a repair - two full reconcile batteries (the red first leg and "
    "the green retry on the committed repair tree), four single-suite re-runs "
    "while locating root causes, one four-section follow-up twice plus one "
    "matrix regeneration, two bookkeeping repairs through one helper with "
    "predicted byte deltas and read-back proofs, and the state/board/export/"
    "heartbeat closeout; zero cloud calls and zero external API touches; the "
    "product face resumes at R2319"
)

SELF_HEAL = (
    "R2318 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply it, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window (eightieth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md)."
)

HONEST = (
    "R2318 honest disclosures: (a) the red leg is kept on disk and named: 5 "
    "failed assertions across 4 suites, criteria total 3772, in 776.8s, and none "
    "of the four causes was a product defect. (b) Two of the four were the same "
    "class: a suite that hardcodes a calendar month which its own world stamps "
    "from the wall clock silently stops meaning what the criterion says the "
    "moment the clock rolls into that month - this was not a one-day accident, "
    "it was waiting for 2026-11-01, and the repair removes the dependency "
    "instead of moving the literal forward. (c) The residue and identity repairs "
    "are bookkeeping, not product: the declaration grew 187 -> 189 entries on a "
    "live DELIVERED reading and the identity baseline grew 2 -> 3 known bases, "
    "both with predicted byte deltas that matched the writes and both with "
    "read-back proofs and no temp residue. (d) The retry evidence is named "
    "-retry, not -run2, following the R2238 forward convention this window had "
    "just disclosed; both legs stay in the file (1889B FAIL then 1950B PASS) and "
    "the FAIL leg is the designed first use of the matrix section, which refuses "
    "to rewrite the stale doc. (e) This window shipped no product code and "
    "scored 0 product points; the tech queue was not touched, so claimable stays "
    "11 against its floor of 10. (f) tasks.md was left untouched: it is the P-47 "
    "canonical board and carries no row for this tech slice, disclosed rather "
    "than silently skipped."
)

EXPORT_DO = (
    "R2318 验证轮：R2317 留下的对账电池先红后绿。首次在已提交树上跑出 462/466 "
    "套件绿、5 处失败断言，四处根因全部落在夹具与记账件而非产品代码：两处套件把"
    "「没有活动的月份」写成日历字面量，而世界行按真实时钟落戳，跨月当天字面量失效；"
    "R2317 折叠把 R2302/R2303 日志块移入归档，两轮变成未裁决残留；R2316 的纠错重跑"
    "证据对在身份审计里读成未销账字节声称。四处均在出生站修复并单独提交（a6377a07）："
    "夹具改为从世界自身记录戳推导安静月份（判据语义不变），残留声明按实读"
    "DELIVERED 携带 187→189 条，身份基线如实披露该证据对 2→3 条。修复树上复跑"
    "全量电池：466/466 套件绿 + 控制 7/7，749.0 秒，判据 3772 与预注册完全一致。"
)

EXPORT_CURRENT = (
    "R2318 验证轮完成：红电池的四处根因全部在出生站修好并单独落库，修复树上全量"
    "电池 466/466 套件绿 + 控制 7/7（749.0s，判据 3772 = 预注册值），四段随访在"
    "矩阵重生成后全 PASS；红腿证据 qa/reconcile-all-R2318.log 与绿腿 "
    "qa/reconcile-all-R2318-retry.log 均在盘；产品代码零改动（本轮 0 产品分），"
    "技术队列可认领仍 11（地板 10）。"
)

EXPORT_ARTIFACT = (
    "qa/reconcile-all-R2318-retry.log（785400B·466/466 + 控制 7/7·判据 3772）与 "
    "qa/reconcile-all-R2318.log（红腿·5 断言），2026-11-01"
)

EXPORT_NEXT = (
    "R2319 回到产品面：取债务闸与队列头点名的门声明退役接线 "
    "src/os/gate_decl_retire_wire.py（AC-GDRTW1..AC-GDRTW6 已预注册在 "
    "state/queue/tech.md:377）：退役写手必须先问身份读面，UNMATCHED 才可退役，"
    "MATCHED/AMBIGUOUS 在动任何字节之前拒绝并点名全部承载行"
)

BOARD_DONE = (
    " [done 2026-11-01 R2318 - BATTERY RED THEN GREEN on the committed tree: "
    "first run 462/466 suites with 5 failed assertions in the lobby (AC-S52/"
    "AC-S53), ledger-datasub-coveragegatepersist (AC-CVGG7), os-residue-triage "
    "(AC-RTR6) and os-run-identity (AC-RID8) suites; four root causes and no "
    "product defect - two suites hardcoded a calendar month their world stamps "
    "from the wall clock (both now derive the quiet month from the world own "
    "record stamps, criterion intent unchanged), the R2317 fold left R2302/R2303 "
    "untriaged (declaration 187->189 off the live DELIVERED reading, 32378B -> "
    "33107B predicted equal to measured), and the R2316 correction-rerun pair "
    "was disclosed in the identity baseline (1630B -> 2173B); repairs committed "
    "alone as a6377a07; RETRY on the committed repair tree = RUNNER PASS 466/466 "
    "plus controls 7/7 in 749.0s, criteria total 3772 exactly as pre-registered, "
    "TMP RECLAIM 932/932 worlds 326.59 MiB, four follow-up sections PASS after "
    "the matrix was regenerated 466/3772 (44771B); zero product code changed, "
    "0 product points; evidence qa/reconcile-all-R2318.log (red leg) and "
    "qa/reconcile-all-R2318-retry.log]"
)

BOARD_TOP = (
    "- [ ] R2318 first item: BACK TO THE PRODUCT FACE on the row the reader "
    "names. `python src/os/queue_head.py --head tech` reads state/queue/tech.md"
    ":377 prefix AC-GDRTW1 (claimable=11) - the gate_decl_retire_wire seed, "
    "whose AC-GDRTW1..AC-GDRTW6 criteria are already pinned INSIDE that row "
    "BEFORE the code. Run a fresh zero-occupancy anchor check at HEAD "
    "(`git grep -F`, expecting rc 1) before writing anything, ship one product "
    "face with its suite (the retire writer must ask gate_decl_identity FIRST, "
    "so MATCHED and AMBIGUOUS refuse before any byte with the reader state and "
    "every carrier line named while only an UNMATCHED identity reaches "
    "gate_decl_retire.plan - the same shape gate_decl_identity_wire already "
    "gives the append path), refill the tech floor with one real gap row if the "
    "claim drops claimable to 10, and commit BEFORE any battery (the R2168 "
    "mixed-tree rule) - the battery is then the successor row. Also open and "
    "needing an ELEVATED shell: BigDomain-OSLoop reads "
    "LogonType=InteractiveToken (eightieth consecutive disclosure; carried as "
    "loop-s4u-reconcile in state/debt.md).\n"
)


def write_text(path, text):
    data = text.encode("utf-8")
    temp = path + ".r2318-tmp"
    with io.open(temp, "wb") as handle:
        handle.write(data)
    os.replace(temp, path)
    with io.open(path, "rb") as handle:
        if handle.read() != data:
            raise SystemExit("E_CLOSE_READBACK %s" % path)


def block_ends(state):
    starts = []
    for index, item in enumerate(state["log"], 1):
        if re.match(r"^(\d{4}-\d{2}-\d{2} )?R\d+ ", item):
            starts.append(index)
    ends = [start - 1 for start in starts[1:]]
    ends.append(len(state["log"]))
    return [end for end in ends if end >= 3]


def maybe_fold(state, delta):
    raw = open(STATE, "rb").read()
    disk = len(raw)
    if disk + delta <= SF.GATE - 1500:
        print("fold: not due (%dB + %dB against gate %d)"
              % (disk, delta, SF.GATE))
        return False
    chosen = None
    for end in block_ends(state):
        window = state["log"][2:end]
        tokens = set()
        for line in window:
            tokens |= set(SF.PAT.findall(line))
        summary = ("Fold R2318: log lines 3..%d (whole round blocks) moved "
                   "verbatim to the archive; window tokens: %s"
                   % (end, " ".join(sorted(tokens))))
        plan, _text = SF.plan_fold(raw, state, 3, end, summary,
                                   reserve=delta, gate=SF.GATE)
        if plan["gate_ok"] and plan["margin"] - delta >= 1500:
            chosen = (end, summary, plan)
            break
    if chosen is None:
        raise SystemExit("E_CLOSE_NO_FOLD_WINDOW")
    end, summary, plan = chosen
    report = SF.fold(ROOT, "R2318", 617, 3, end, summary, reserve=delta,
                     execute=True)
    print("fold: 617 lines 3..%d predicted=%dB actual=%dB margin=%d "
          "tokens=%d missing=%r"
          % (end, report["predicted_bytes"],
             report.get("post_bytes", report["predicted_bytes"]),
             report.get("margin", 0), plan["tokens_total"],
             plan["tokens_missing"]))
    return True


def append_state():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    trial = json.loads(json.dumps(state))
    trial["tick"] = 2318
    trial["log"].extend([ROUND_LOG, TOKENS_LOG, SELF_HEAL, HONEST])
    rendered = json.dumps(trial, ensure_ascii=False, indent=2) + "\n"
    delta = len(rendered.replace("\n", "\r\n").encode("utf-8")) - \
        os.path.getsize(STATE)
    maybe_fold(state, delta)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2318
    state["log"].extend([ROUND_LOG, TOKENS_LOG, SELF_HEAL, HONEST])
    raw = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    write_text(STATE, raw.replace("\n", "\r\n"))
    SIO.fix(STATE, execute=True)
    report = SIO.report(STATE)
    if not report["layout_ok"]:
        raise SystemExit("E_CLOSE_LAYOUT %r" % report)
    print("state: tick=%d log=%d bytes=%d CANON-CLEAN"
          % (state["tick"], len(state["log"]), report["bytes"]))


def update_export():
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        export = json.load(handle)
    export["export_ts"] = NOW_ISO
    export["do"] = EXPORT_DO
    face = export["ceo_face"]
    face["current"] = EXPORT_CURRENT
    face["latest_artifact"] = EXPORT_ARTIFACT
    face["last_artifact"] = EXPORT_ARTIFACT
    face["next_milestone"] = EXPORT_NEXT
    face["next_milestone_due"] = DUE
    export["outs"].insert(0, [
        "qa/reconcile-all-R2318-retry.log",
        "on",
        "R2318 verification window: the R2317 battery came back red on the "
        "committed tree (462/466 suites, 5 failed assertions) and all four root "
        "causes were repaired at their birth sites - two suites had hardcoded a "
        "calendar month their own world stamps from the wall clock, the R2317 "
        "fold left R2302/R2303 untriaged, and the R2316 correction-rerun pair "
        "read as an undischarged byte claim. The retry on the committed repair "
        "tree reads RUNNER PASS 466/466 plus controls 7/7 in 749.0s with "
        "criteria total 3772 exactly as pre-registered, and all four follow-up "
        "sections PASS after the matrix was regenerated to 466 suites / 3772 "
        "criteria.",
    ])
    export["results"].insert(0, [
        "R2318",
        "verification window that turned into a repair: the first battery was "
        "red on four suites, none of them a product defect; the two fixtures now "
        "derive the quiet month from the world own record stamps, the residue "
        "declaration grew 187 -> 189 on a live DELIVERED reading, and the "
        "identity baseline disclosed the R2316 rerun pair - all committed alone "
        "as a6377a07 before the retry. Retry battery 466/466 green plus controls "
        "7/7 in 749.0s, criteria 3772 matching the pre-registered target, "
        "follow-up 4/4 PASS after regeneration; zero product code changed.",
    ])
    derived, _state, _export, _pat = CEC.recompute()
    export["self_drive"] = derived
    raw = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    write_text(EXPORT, raw)
    print("export: refreshed, self_drive recomputed (%d keys)" % len(derived))


def update_heartbeat():
    line = ("tick 2318 2026-11-01 R2318 verification window: the R2317 battery "
            "was red on the committed tree (462/466 suites, 5 failed assertions "
            "in lobby AC-S52/S53, ledger-datasub-coveragegatepersist AC-CVGG7, "
            "os-residue-triage AC-RTR6 and os-run-identity AC-RID8) and every "
            "cause was repaired at its birth site - two clock-dependent fixtures "
            "now derive the quiet month from the world own record stamps, the "
            "R2317 fold residue R2302/R2303 were carried into the triage "
            "declaration (187 -> 189, predicted bytes equal to measured) and the "
            "R2316 correction-rerun pair was disclosed in the identity baseline "
            "(2 -> 3 known bases); repairs committed alone as a6377a07. RETRY = "
            "RUNNER PASS 466/466 plus controls 7/7 in 749.0s, criteria total "
            "3772 exactly as pre-registered, TMP RECLAIM 932/932 worlds 326.59 "
            "MiB, four follow-up sections PASS after the matrix was regenerated "
            "466/3772 (44771B). Zero product code changed, 0 product points; "
            "claimable tech stays 11 against a floor of 10.\n")
    with io.open(HEART, "r", encoding="utf-8") as handle:
        text = handle.read()
    if not text.endswith("\n"):
        text += "\n"
    write_text(HEART, text + line)
    print("heartbeat: appended tick 2318")


def update_board():
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    if not text.startswith("- [ ] R2317 first item"):
        raise SystemExit("E_CLOSE_BOARD_TOP")
    first_end = text.index(nl)
    head = text[:first_end]
    rest = text[first_end:]
    closed = "- [x]" + head[len("- [ ]"):] + BOARD_DONE
    text = closed + rest
    if not text.startswith(BOARD_TOP.split("\n")[0]):
        text = BOARD_TOP.replace("\n", nl) + text
    write_text(BOARD, text)
    print("board: R2317 row closed, R2318 first item inserted")


def main():
    append_state()
    update_export()
    update_heartbeat()
    update_board()


if __name__ == "__main__":
    main()