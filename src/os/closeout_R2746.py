"""closeout_R2746 - record the R2746 window and refresh the CEO face.

State goes through the canonical writer state_io.write_document; the export is
re-derived for the fields this window can actually measure (tick row, ceo face,
outs) and left alone everywhere else.
"""

import datetime
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
TICK = 2746

LINES = [
    "2026-11-15 R2746 MONITORED-WAIT window that built a runnable caliber face, "
    "zero product bytes because reconcile-battery-R2742 is still OPEN and its leg "
    "is still LIVE. Five readings at open: git status EMPTY at HEAD 1f56f0f1 equal "
    "to origin/main with no index.lock; ZERO @BigDomain rows in the group ledger; "
    "the content-addressed decisions face read tokens_on_disk=67 against a baseline "
    "of 267 with new=0; the group orders tail is the carried 2026-11-14 00:30 "
    "main-control row, older than the 01:3x baseline and therefore knowledge-only; "
    "benchmarks_refreshed 2026-11-14 inside the seven-day gate. debt_gate read "
    "CLAIM-FIRST item=reconcile-battery-R2742 first=1 open=11 and queue_head read "
    "tech line=713 prefix AC-LKNF1 claimable=10, so product bytes stayed frozen.",

    "R2746 THE LEG WAS PROBED BY THE KERNEL AND NOT BY A PID FILE: OpenProcess plus "
    "WaitForSingleObject read pid 64528 ALIVE, and the stream measured 649 PASS suite "
    "rows with 5 FAIL rows and NO closing BATTERY rc= line at open, then 651 PASS "
    "with the same 5 FAIL at closeout. The five red rows are the ONE ledger family "
    "R2745 repaired mid-leg, so under the R2738 precedent they are not evidence "
    "about the repaired tree and the adopting window must re-run them rather than "
    "read this leg green on them. Nothing was adopted, nothing was relaunched and no "
    "evidence path was touched.",

    "R2746 THE FOLD CALIBER DEFECT HAS A THIRD MEASURED FACE, and this is the "
    "window product value: on the REAL canonical state.json the log array closes "
    "with '  ],' because a sibling key follows, while both shipped gates compare "
    "strip() == ']' - so logs_toolkit.split_ps_layout never sees the close and "
    "refuses with E_STATE_LAYOUT, and eol_profile never breaks either, which is why "
    "it reported log_item_lines=99 on a 98-item log. Measured read-only on the real "
    "file: caliber=2 indents=[2] items=98, the shipped gate answers accepts=False "
    "indent-gate-16, and the prescribed gate answers accepts=True caliber-2. Shipped "
    "tools/fold_caliber_check.py (pure functions plus a --check CLI, no write path, "
    "no clock, no network, no shell) which derives the caliber FROM THE DOCUMENT, "
    "accepts the canonical two-space block and the legacy sixteen-space block, and "
    "still refuses an eight-space or mixed block so AC-LF1 and AC-FI5 keep gating. "
    "It landed in tools/ and NOT in src/os/ for one measured reason: the live leg has "
    "not yet run os-logs-toolkit and a new src/os byte is visible to the corpus probe "
    "suites, so patching there now would make this leg ambiguous rather than clean.",

    "R2746 PROOF ON A PRIVATE WORLD, 15/15 PASS (qa/fold-caliber-R2746.log): the "
    "real document reads caliber 2 healthy and foldable; the SHIPPED tool was "
    "actually executed against a private copy of that document and refused with "
    "'E_STATE_LAYOUT: PS item-line layout mismatch (refusing)', which reproduces the "
    "defect in the carriage and not only in the mirror; a legacy sixteen-space world "
    "is accepted by BOTH gates; an eight-space world and a mixed world are both "
    "refused with their own codes; and the summary literal carries the measured "
    "caliber instead of a hardcoded sixteen. The first private world was invalid JSON "
    "because a close line ending '],' with no sibling key cannot happen in a real "
    "document - the builder was repaired to carry a following key, and that "
    "correction is what made the shipped-refusal check pass on the second run.",

    "R2746 honest disclosures: (a) ZERO product points by the Executive Protocol "
    "scale - a runnable caliber face and a fifteen-check private-world proof are "
    "tooling and evidence, not something a CEO can newly open, and every P-47 "
    "business face still waits on CEO physical pieces (merchant id, mini-program "
    "appid/secret); (b) the face is a READ SIDE only: it measures and refuses, it "
    "does not yet rewire logs_toolkit, so the fold stays blocked until a window runs "
    "after the leg and patches the two call sites onto these functions; (c) "
    "state.json stands at 91193B pre-closeout against the 78500B waterline, so both "
    "the waterline and that gap stay RED and declared; (d) the dead per-round export "
    "hook in src/os/export_R2431.py is STILL OWED and overdue by ELEVEN windows; (e) "
    "the leg five red rows are left for the adopting window by design and this window "
    "claims no battery green; (f) src/os still carries hundreds of one-off closeout "
    "scripts, pre-existing bloat this window neither created nor cleaned, and this "
    "window added exactly one closeout script plus one tool under tools/; (g) tasks.md "
    "was not touched, it is the P-47 canonical board; (h) Docker is absent on this "
    "host; (i) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED "
    "shell for its S4U re-registration (carried ceo-pending physical item "
    "loop-s4u-reconcile).",

    "R2746 tokens: local=~13k api=0 api_reason=monitored-wait plus one tooled repair "
    "prototype - one five-silence scan with the debt gate, the queue head and the "
    "ledger face, one kernel liveness probe plus two stream measurements, three "
    "root-cause reads of the shipped gates, one caliber face with six pure functions "
    "and a CLI, one private-world driver and three repair iterations on it, one "
    "fifteen-check proof landed as evidence, one move out of src/os to keep the live "
    "leg clean, and the state/export closeout; zero cloud calls and zero external API "
    "touches",
]

CEO_CURRENT = (
    "R2746 监控等待窗：R2742 全量电池腿内核探针实测仍在跑（651/676·5 红为 R2745 已修的账目族），"
    "产品字节按混合树律冻结；本轮交付可运行口径判据件 tools/fold_caliber_check.py，"
    "并实测出折叠口径冲突的第三面（canonical 收尾行 '  ],' 令两处 gate 永远读不到收尾）"
)
CEO_LATEST = (
    "tools/fold_caliber_check.py（口径实测器·--check 可跑）＋ qa/fold-caliber-R2746.log"
    "（私有世界 15/15 全绿·含 shipped 工具对私有副本的真实拒绝）（2026-11-15 本窗实测）"
)
CEO_NEXT = (
    "下窗：等电池腿收尾后按证据路径采纳（5 红需在修好树上重跑）→ 再把 logs_toolkit 两处调用点"
    "接到已交付的口径函数上并重折叠；窗 ≤48h"
)


def write_export(now_iso):
    with io.open(EXPORT, encoding="utf-8") as handle:
        payload = json.load(handle)
    payload["export_ts"] = now_iso
    payload["do"] = CEO_CURRENT
    face = payload.get("ceo_face") or {}
    face["current"] = CEO_CURRENT
    face["latest_artifact"] = CEO_LATEST
    face["next_milestone"] = CEO_NEXT
    payload["ceo_face"] = face
    rows = payload.get("results") or []
    hit = False
    for row in rows:
        if isinstance(row, list) and len(row) == 2 and str(row[0]) == "2745":
            row[0] = str(TICK)
            hit = True
    if not hit:
        rows.append([str(TICK), "OSLoop 执行 tick"])
    payload["results"] = rows
    outs = payload.get("outs") or []
    payload["outs"] = [CEO_LATEST] + [x for x in outs if x != CEO_LATEST][:9]
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    with io.open(EXPORT, "wb") as handle:
        handle.write(text.replace("\n", "\r\n").encode("utf-8"))
    return hit


def main():
    raw = state_io.read_raw(STATE)
    data = state_io.parse(state_io.decode(raw))
    before = len(data["log"])
    data["log"].extend(LINES)
    data["tick"] = TICK
    state_io.write_document(STATE, data)
    back = json.load(io.open(STATE, encoding="utf-8"))
    ok = (back.get("tick") == TICK
          and len(back.get("log") or []) == before + len(LINES)
          and back["log"][-len(LINES):] == LINES)
    now_iso = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    tick_hit = write_export(now_iso)
    exported = json.load(io.open(EXPORT, encoding="utf-8"))
    export_ok = (exported.get("export_ts") == now_iso
                 and any(str(r[0]) == str(TICK)
                         for r in exported.get("results") or []
                         if isinstance(r, list) and len(r) == 2))
    sys.stdout.write(
        "APPENDED tick=%s log %d->%d ok=%s | export tick_row_moved=%s ok=%s ts=%s\n"
        % (back.get("tick"), before, len(back.get("log") or []), ok,
           tick_hit, export_ok, now_iso))
    return 0 if ok and export_ok else 2


if __name__ == "__main__":
    sys.exit(main())
