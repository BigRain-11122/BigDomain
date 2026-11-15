"""closeout_R2779 - state.json + backlog marks for the ship-checklist window."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")

NEW_DEC = ["D-20261115-06", "D-20261115-07", "D-20261115-08",
           "D-20261115-09", "D-20261115-10", "D-20261115-11",
           "D-20261115-12"]

LINES = [
    "2026-11-15 R2779 PRODUCT: the ship checklist stopped being prose and became an "
    "object the CEO can open and tick - preview/ship-checklist.html (9182B) + .json (4983B), "
    "rendered in one command by tools/ship_checklist.py. Eleven rows in three sections: eight "
    "SELF rows whose readiness is RECOMPUTED FROM DISK at render time (BLUEPRINT.md carries AIGC "
    "and msgSecCheck, docs/global-benchmarks.md carries the filing playbook and the pre-approval "
    "categories, preview/*.json carries the four shipped faces), and three CEO rows that are never "
    "presented as ready. Criteria AC-SCL1..AC-SCL8 were pinned in src/os/backlog.md BEFORE the tool "
    "existed. --check reads VERDICT PASS 8/8 items=11 ready=8 open=0 blocked=3 html=9182B json=4983B; "
    "AC-SCL6 measured --check leaves both files byte- and mtime-identical; AC-SCL7 control removed "
    "preview/platform-live-report.json and read VERDICT FAIL 1 rc=2, restored to PASS 8/8 rc=0. "
    "tools/deliverable_index.py re-rendered the CEO entry page (band rows 27->28, newest=ship-checklist.json) "
    "and its own gate reads PASS 14/14. Evidence qa/ship-checklist-R2779.log 1314B written through "
    "tools/qa_log.py (dialect utf-8/lf, --check OK).",

    "R2779 ADOPTION BY EVIDENCE PATH, NOT BY PID: reconcile-battery-R2775 had CLOSED before open - "
    "pid 44264 kernel GONE, logs/battery-R2775.stream ends 'RUNNER FAIL (3 failed assertions) BATTERY rc=1 "
    "3432.1s', evidence qa/reconcile-all-R2775.log 1252998B utf-8 bom=False crlf=0. tools/adoption_preflight "
    "read VERDICT NOT-READY gates=14 failed=3 (closing-rc-zero, zero-unattributed-fail-rows, evidence-closing-line) "
    "with 676 suite rows, 676 unique names, 676 registry names equal, and an INDEPENDENT criteria recount of "
    "EXACTLY 5032 - the leg is kept as RED evidence and was NOT relaunched. The two attributed red suites were "
    "re-run on the FINAL tree: src/sandbox/test_reconcile_daily_census.py SUITE PASS 8/8 (the R2776-repaired "
    "UTF-16 dialect row) and src/os/test_ledger_closeout.py SUITE PASS 8/8. A successor full battery is launched "
    "detached after the closeout commit for the next window to adopt by its own closing row.",

    "R2779 DECISIONS FACE: seven new content-addressed tokens appeared and every one of them is a group audit "
    "finding on another line's execution surface (visual workcell executor idle, delivery workcell fork 301/182, "
    "a stale BLOCKED submission card, the drama line stalled 689.5h, the BigLife ring-batch criterion, the fourth "
    "MiniGame feedback gap, and the notification-boundary order conflict). None names BigDomain work, so each is "
    "recorded as knowledge-only with no action, and the baseline is advanced to the current token set. No new "
    "order and no new @BigDomain ledger dispatch row exists today; the ledger conflict=1 flag stays a scanner-side "
    "signal as R2778 measured it.",

    "R2779 honest disclosures: (a) this is the first round in three windows that ships a PRODUCT point by the "
    "Executive Protocol scale - a page the CEO can open offline and tick - but it is a DERIVED surface: it invents "
    "no new facts and every ready row points back at a file already on disk, so it earns 2 points as usable and "
    "0 as new knowledge; (b) the three CEO rows are deliberately untickable and show the blocker census from "
    "preview/ceo-blockers.json rather than any claim of progress; (c) every P-47 business face still waits on CEO "
    "physical pieces (server / domain / filing+ICP / merchant id, plus the miniprogram appid+secret); (d) the R2775 "
    "leg stays RED and this window claims no battery green - the two individual re-runs are evidence about the tree, "
    "not a verdict on the leg; (e) the round-aligned state.json fold is STILL OWED and state.json now reads 179147B "
    "against the 78500B waterline, the largest gap on record; (f) the dead per-round export hook "
    "src/os/export_R2431.py is STILL OWED; (g) src/sandbox/reconcile_all.py still does not register "
    "tools/ship_checklist.py, so its 8 criteria are unguarded by any battery until src/ registration happens; "
    "(h) tasks.md was not touched - it is the P-47 canonical board, not ours; (i) Docker is absent on this host; "
    "(j) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell for its S4U re-registration "
    "(carried ceo-pending physical item loop-s4u-reconcile).",

    "R2779 tokens: local=~30k api=0 api_reason=one five-silence scan, one adoption preflight plus a fail-row census "
    "over a 1.25MB evidence file, two targeted suite re-runs, one tool with eleven derived rows and eight criteria, "
    "one render plus one gate plus two controls (read-only and negative), one entry-page re-render with its 14-check "
    "gate, one evidence log through the birth-site writer, and the state/export closeout; zero cloud calls and zero "
    "external API touches",
]

BACKLOG_DONE = [
    "- [x] [done 2026-11-15 R2779 - PRODUCT: 上线前置清单从散文变成 CEO 能打开、能勾的实物] "
    "preview/ship-checklist.html 9182B + ship-checklist.json 4983B，一条命令 `python tools/ship_checklist.py` 派生。"
    "十一行三档：八条本司行**在渲染那一刻从盘上实测**（BLUEPRINT.md 载 AIGC 与 msgSecCheck、"
    "docs/global-benchmarks.md 载备案指引与前置审批类目、preview/*.json 载四个已上线面），"
    "三条 CEO 行一律不可勾且现况取自 preview/ceo-blockers.json 的 physical 计数。判据 AC-SCL1..8 先落本板再写码。"
    "`--check` = VERDICT PASS 8/8；AC-SCL6 实测前后字节+mtime 全等；AC-SCL7 反控（删 platform-live-report.json）"
    "→ FAIL 1 rc=2，复原 → PASS 8/8 rc=0。入口页重渲染后带子 27→28 行、AC-DIX 全门 PASS 14/14。"
    "证据 qa/ship-checklist-R2779.log 1314B 由 tools/qa_log.py 写出（utf-8/lf，`--check` OK）。",
    "- [x] [done 2026-11-15 R2779 - 采纳不靠 pid 而靠证据路径：R2775 腿已闭合，两条红套件在最终树上复跑均绿] "
    "pid 44264 kernel GONE，流末 `RUNNER FAIL (3 failed assertions) BATTERY rc=1 3432.1s`，"
    "证据件 1252998B。adoption_preflight = NOT-READY 3/14 门（含 closing-rc-zero），"
    "676 行/676 唯一名/判据独立重算 5032——腿按红灯留档、**不重启不覆盖**。"
    "复跑：test_reconcile_daily_census 8/8（R2776 已修的方言行）、test_ledger_closeout 8/8。"
    "继任整腿在收账 commit 之后 detached 启动，交下窗按自己的 closing 行采纳。",
    "- [x] [done 2026-11-15 R2779 - 决策面七条新行全部判为知悉不动作] "
    "D-20261115-06..12 逐条实读：视觉工位执行器闲置／交付工位分叉 301-182／提审清单 BLOCKED 过期／"
    "漫剧线停滞 689.5h／BigLife 年轮批判据／MiniGame 反馈面第四缺口／通知边界令与主控令冲突——"
    "七条均在**兄弟线执行面**，无一条点名 BigDomain 工作，故一条不动、基线推进到当前 token 集；"
    "今日无新司令、无新 @BigDomain 派工行（R2778 已实测 conflict=1 属扫描侧信号）。",
]

NEXT = (
    "- [ ] [R2779] next window: (1) ADOPT reconcile-battery-R2779 by its OWN closing `BATTERY rc=` row via "
    "`tools/adoption_preflight.py` - it was launched detached AFTER this closeout commit, so it is the first leg "
    "in several rounds with no later write of mine landing under it; if it still measures red on tree-sensitive "
    "suites, attribute by name rather than verdict. (2) REGISTER tools/ship_checklist.py (8 criteria) in "
    "`src/sandbox/reconcile_all.py` - src/ is unfrozen now that the R2775 leg is closed, and its criteria are "
    "unguarded by any battery until then. (3) CLOSE the largest measured debt on record: the round-aligned "
    "state.json fold (179147B against the 78500B waterline) - the caliber patch landed at R2747, so measure whether "
    "`python src/os/logs_toolkit.py fold` now accepts the canonical two-space block before assuming it does. "
    "(4) The three R2778 carried items stand: the second through ninth chapters of 网络数据安全管理条例, the "
    "P-47 item-3 pre-submission tick list beyond the checklist page, and BD-PROP-005 promotion. (5) Still owed: the "
    "dead per-round export hook `src/os/export_R2431.py`, AC-VAC1..6 in `src/sandbox/ledger/reconcile.py`, the "
    "`scan_five_still.py` token-boundary narrowing for the phantom D-20261114-0, and the queue head "
    "`state/queue/tech.md` prefix AC-LKNF1."
)


def main():
    doc = json.load(io.open(STATE, encoding="utf-8"))
    doc["tick"] = int(doc.get("tick", 0)) + 1
    log = doc.get("log") or []
    log.extend(LINES)
    doc["log"] = log
    have = set(doc.get("last_dec_tokens") or [])
    for tok in NEW_DEC:
        have.add(tok)
    doc["last_dec_tokens"] = sorted(have)
    doc["last_decision_rows"] = 193
    state_io.write_document(STATE, doc)

    bl = os.path.join(BASE, "backlog.md")
    text = io.open(bl, encoding="utf-8").read()
    marker = "- [ ] [R2779 criteria PINNED BEFORE the checklist page exists]"
    idx = text.index(marker)
    insert = "\n".join(BACKLOG_DONE) + "\n" + NEXT + "\n"
    text = text[:idx] + insert + text[idx:]
    text = text.replace("- [ ] [R2778] next window:", "- [-] [R2778] next window (superseded by R2779, item 2 done):")
    io.open(bl, "w", encoding="utf-8", newline="\n").write(text)

    back = json.load(io.open(STATE, encoding="utf-8"))
    print("TICK %s log=%d dec_tokens=%d" % (back["tick"], len(back["log"]),
                                            len(back["last_dec_tokens"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
