"""R2114 closeout: decisions watermark v2 four-tuple (D-20261025-08).

Updates src/os/state.json (tick, log, decision baseline) and refreshes
docs/status-export.json from the measured round facts. ASCII source.
"""

import datetime
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

NEW_TOKENS = ["D-20261025-05", "D-20261025-06", "D-20261025-07",
              "D-20261025-08"]

LOG_LINES = [
    "2026-10-25 R2114 (five-silence scan: decisions.md carries FOUR new"
    " content-addressed tokens D-20261025-05..08 against the stored"
    " baseline - D-05 is the orders archive-threshold restructure, D-06"
    " the 27 UNEXPECTED-DISABLED task whitelist triage and D-07 the MV V5"
    " withdrawal, all three other seats' execution faces, while D-08"
    " (watermark v2 four-tuple, every company aligned by 2026-10-26 06:00)"
    " is OURS - so this window executed D-08 instead of seeding a new"
    " explore row; the assistive UTF-8 row count is re-anchored to the"
    " measured 209; ledger zero new @BigDomain transfer rows; group orders"
    " baseline unchanged at 2026-10-24 12:17; benchmarks refreshed"
    " 2026-10-24 inside 7 days; tree clean, no index.lock; both daily"
    " standing rows for 2026-10-25 were already stamped by R2105 so"
    " neither was re-run) - the source anchor the decisions watermark"
    " never had. The five-silence baseline advanced from a bare content"
    " hash, which cannot tell 'the content changed' from 'history was"
    " rewritten' or 'I read an unmerged local ref' - exactly the ghost-sha"
    " failure D-08 cites. Product: src/os/dec_watermark.py (pure stdlib,"
    " ASCII, git the only external tool) with resolve() observing the"
    " four-tuple {repo, commit_sha, blob_bytes, sha256}, repo_identity()"
    " preferring the origin URL so a fork can never look like the same"
    " source, classify() comparing in the pinned order"
    " repo -> commit_sha -> blob_bytes -> sha256 and returning"
    " new/legacy/unchanged/moved/stale, build_entry() attaching a"
    " reproducible fetch command, write_atomic() (full serialize then"
    " temp + os.replace) and the record/check subcommands with exit codes"
    " 0/2/3/4; a stale source never advances the watermark and leaves the"
    " file byte-identical. Suite src/os/test_dec_watermark.py SUITE PASS"
    " 8/8 with criterion lines byte-identical across the double run"
    " (qa/decwatermark-R2114.log + -run2, sha16 27a758e6da378422, ASCII"
    " LF, temp repos only); wired os-decwatermark (8) into reconcile_all,"
    " full battery RUNNER PASS 319/319 suites plus controls 7/7 in 503.9s"
    " (qa/reconcile-all-R2114.log) and the matrix regenerated to 319"
    " suites / 2660 criteria with --check byte-identical."
    " Shipped state/dec_watermark.json anchors the group FluxGroup"
    " docs/decisions.md at HEAD 4cf327b9 / 222683 bytes / sha256"
    " f94a284c.. with a fetch command that reproduces it. Two honest"
    " disclosures: (a) the criteria row was landed in state/queue/tech.md"
    " AFTER the module existed in this window - a birth-station deviation,"
    " recorded as such rather than claimed as pre-registration; (b) the"
    " group repo's origin/main lags its HEAD by three commits (the origin"
    " blob is 215741 bytes and does NOT contain the D-20261025-05..08 rows"
    " this window consumed), so the watermark anchors HEAD, the source"
    " actually read; a check against origin/main reports moved and, under"
    " D-08's 'a differing source is stale, never consumed' rule, the next"
    " window must re-check after the group pushes rather than trusting the"
    " older origin blob.",
    "R2114 tokens: local=~45k api=0 api_reason=five-silence scan + four"
    " new decision tokens judged (three other seats, one ours) + watermark"
    " v2 module and 8-criteria suite double-run + full battery + matrix"
    " regen/check + state/export closeout, zero cloud calls",
]

RESULTS_TEXT = (
    "R2114: the decisions watermark gains the source anchor the group"
    " decision D-20261025-08 requires. The five-silence baseline advanced"
    " from a content hash alone, so it could not distinguish a content"
    " change from a rewritten history or an unmerged local read. New"
    " src/os/dec_watermark.py observes the four-tuple {repo, commit_sha,"
    " blob_bytes, sha256}, compares in the pinned order repo ->"
    " commit_sha -> blob_bytes -> sha256, never advances on a stale"
    " source, writes atomically and ships one reproducible fetch command;"
    " suite 8/8 double-run identical sha16 27a758e6da378422; wired"
    " os-decwatermark (8). Shipped state/dec_watermark.json anchors the"
    " group decisions.md at HEAD 4cf327b9 / 222683B / sha256 f94a284c."
    " Honest notes: the criteria row was landed after the code in this"
    " window (disclosed deviation), and origin/main lags HEAD by three"
    " commits, so a check against origin reports moved and must not be"
    " consumed until the group pushes.")

OUTS_TIMELINE = (
    "R2114：五静水位此前只存内容哈希，分不清「内容变了」与「历史被改写/读到未合入分支」"
    "（正是 D-08 描述的幽灵 sha 事故）。本窗落地集团水位键 v2 四元组工具"
    "（src/os/dec_watermark.py）：观察 {repo, commit_sha, blob_bytes, sha256}、"
    "按 repo→commit_sha→blob_bytes→sha256 固定序比对、判 new/legacy/unchanged/moved/stale、"
    "stale 一律不前进且文件字节不动、先全量序列化再 temp+os.replace 原子落盘、"
    "并附一条可复现取件命令；套件 8/8 双跑判据行同一；接线 os-decwatermark(8)；"
    "落仓水位件实锚集团 decisions.md（HEAD 4cf327b9·222683B·sha256 f94a284c）。"
    "诚实注两处：判据行在本窗代码之后落板（出生站偏差已披露）；"
    "集团 origin/main 落后 HEAD 三提交，故锚实际消费源 HEAD，对 origin 的 check 报 moved、按律不得据旧 blob 消费。")


def main():
    state = json.load(io.open(STATE, encoding="utf-8"))
    state["tick"] = int(state.get("tick", 0)) + 1
    state["last_order"] = "2026-10-24 12:17"
    state["last_decision_rows"] = 209
    tokens = [t for t in state.get("last_dec_tokens", "").split(",") if t]
    for tok in NEW_TOKENS:
        if tok not in tokens:
            tokens.append(tok)
    state["last_dec_tokens"] = ",".join(tokens)
    for line in LOG_LINES:
        state["log"].append(line)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, indent=1, ensure_ascii=False) + "\n")

    export = json.load(io.open(EXPORT, encoding="utf-8"))
    now = datetime.datetime.now().astimezone().replace(microsecond=0)
    export["export_ts"] = now.isoformat()
    export["ceo_face"]["current"] = (
        "R2114 集团决策水位升级：以前判断「集团有没有新决策」只看一个内容哈希，"
        "分不清是内容真变了、还是历史被改写、还是读到了没推送的分支（幽灵值）。"
        "本窗把水位改成带来源的四元组（仓库+提交+字节数+内容哈希）并附一条可复现取件命令，"
        "来源对不上就判 stale、绝不前进水位——这是集团 10-25 决议要求各司 10-26 06:00 前对齐的硬项。")
    export["ceo_face"]["latest_artifact"] = (
        "src/os/dec_watermark.py（四元组观察/固定序比对/原子落盘/取件命令，"
        "record+check 两子命令）+ src/os/test_dec_watermark.py（SUITE PASS 8/8，"
        "双跑判据行同一 sha16 27a758e6da378422）+ qa/decwatermark-R2114.log（与 -run2）"
        " + state/dec_watermark.json（实锚集团 decisions.md·HEAD 4cf327b9·222683B·"
        "sha256 f94a284c） + qa/reconcile-all-R2114.log（RUNNER PASS）")
    export["ceo_face"]["next_milestone"] = (
        "48 小时内：等集团把 HEAD 三提交推到 origin 后复检水位（check 应从 moved 转 "
        "unchanged/moved 再前进，禁据旧 origin blob 消费）；随后把水位检查接进轮首五静扫描，"
        "让「读到幽灵 sha」在扫描步就 fail-closed。")
    export["outs"].insert(0, [
        "集团决策水位键 v2 四元组（来源锚 + 可复现取件命令 + stale 不前进）",
        "on",
        OUTS_TIMELINE])
    export["results"].insert(0, ["R2114", RESULTS_TEXT])
    export["self_drive"]["log_lines_in_window"] = int(
        export["self_drive"].get("log_lines_in_window", 0)) + 2
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, indent=1, ensure_ascii=False) + "\n")
    print("closed tick=%s export=%s" % (state["tick"], export["export_ts"]))


if __name__ == "__main__":
    sys.exit(main())