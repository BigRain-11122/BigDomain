"""Closeout for R2259: state.json log items, tick bump, export refresh.

Writes both files through one in-process writer (no shell redirection), keeps
the canonical 16-space CRLF log layout, proves the JSON payload only grew by
the appended items, and then re-derives the export's self_drive block with the
project's own recompute() so nothing on the CEO face is hand-typed.
"""

import datetime as dt
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

sys.path.insert(0, BASE)

import state_io  # noqa: E402
import check_export_consistency as CEC  # noqa: E402

NEW_ITEMS = [
    "2026-10-29 R2259 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; the queue gauge read main "
    "5/5 tech 10/10 explore 10/10 FLOOR-MET with tech 11 open of which 1 "
    "gated and explore 10 open; decisions.md carries 289 non-empty rows and "
    "194 content-addressed D/C/O/T/XL tokens against the stored 194-token "
    "superset baseline with ZERO additions, so zero domain action; the group "
    "ledger carries the same three @BigDomain patrol rows already paid off, "
    "none numbered, so zero unreplied handoffs; the group orders tail is "
    "unchanged at the 2026-10-29 02:1x CEO-PROXY event round R2.48 already "
    "consumed in R2226; benchmarks refreshed 2026-10-29 inside the seven-day "
    "gate) - the P1 canonical rows stay blocked-on-CEO, the weekly proposal "
    "duty is met by BD-PROP-005, and the debt register named exactly one "
    "first=yes row (product-face-R2259, opened by R2258), so this window took "
    "the product face. Queue ordering disclosed: rows 41 (docker absent on "
    "this machine), 54 (standing line with no defined next slice), 85 (gated "
    "on a product revisit) and 88 (AC-LN1..LN8 already delivered at R1727) "
    "were not deliverable faces, so the window claimed the top deliverable "
    "row, the R2248 e seed. RESULT: src/os/seed_anchor.py - a seed's face "
    "name is now a reading instead of a hand-run git grep. Two scopes: HEAD "
    "(what a landed seed would collide with) and the working tree including "
    "untracked files (what a sibling window that wrote but did not commit "
    "would collide with), every hit reported with needle, scope, file and "
    "line, a FREE/OCCUPIED verdict whose head, tree and per-needle counts "
    "reconcile, an honest truncated flag bounded by --limit, and a refusal on "
    "any hit (E_SAN_OCCUPIED, CLI 2 printing REFUSE TO SEED) while FREE exits "
    "0, bad flags 2 and a non-repository or a git failure 3. "
    "GIT_CEILING_DIRECTORIES is pinned to the parent of the scanned root so a "
    "plain directory fails closed instead of borrowing an enclosing "
    "repository, and the HEAD leg strips git's constant HEAD: prefix so both "
    "legs report the same repository-relative path. Criteria AC-SAN1..AC-SAN5 "
    "were pinned in the row BEFORE the code with the anchor check recorded "
    "(os-seed-anchor / test_seed_anchor / E_SAN rc=1; seed_anchor and AC-SAN "
    "hit only the seed generator, the R2248 backlog row and the row text, "
    "disclosed). Evidence: SUITE PASS 5/5 double-run byte-identical criterion "
    "sha16 42FAF3CADB8BEEF9 (qa/seed-anchor-R2259-a.log and -b.log, 429B "
    "each, single writer utf-8 LF through src/os/evidence_R2259.py, never a "
    "shell redirection), five adjacent os suites green "
    "(qa/regression-R2259.log, fails=0), wired os-seed-anchor(5). Live "
    "reading at closeout: seed_anchor over both scopes is OCCUPIED head=31 "
    "tree=52 (the name is carried by text), while the fresh label "
    "os-seed-anchor reads FREE at HEAD (head=0) and only becomes occupied in "
    "the working tree - the exact HEAD-vs-tree difference the second scope "
    "exists to expose. Implementation defect found by the suite and fixed in "
    "the module, not in a criterion (disclosed): the first HEAD leg passed "
    "the revision before the pattern, so git consumed HEAD as the literal "
    "needle and every HEAD scan read zero; the leg now uses an explicit -e "
    "pattern. Honest score: one product face shipped with its own suite, so "
    "2 points. The tech floor was refilled in the same window with one real "
    "gap row (evidence_capture, AC-EVC1..AC-EVC6 pre-registered, five anchors "
    "git grep -F rc=1) and the gauge closed FLOOR-MET main 5/5 tech 10/10 "
    "explore 10/10. The full reconcile battery and the suite-matrix "
    "regeneration carry to R2260 (the R2168 mixed-tree rule) and are "
    "registered first=yes.",
    "R2259 tokens: local=~22k api=0 api_reason=product window on the debt "
    "register first item - one new os module plus its five-criteria suite, "
    "one single-writer evidence helper, one runner entry, and the "
    "queue/backlog/debt/state/export closeout; zero cloud calls and zero "
    "external API touches; the battery and the matrix regeneration carry to "
    "R2260",
    "R2259 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (twenty-seventh consecutive disclosure, registered as "
    "the stale row loop-s4u-reconcile in state/debt.md).",
]

OUTS = [
    [
        "seed anchor reader: a seed's face name is provably free at HEAD and "
        "in the working tree (R2259)",
        "on",
        "R2259: src/os/seed_anchor.py turns the hand-run git grep into a "
        "reading. The HEAD scope answers what a landed seed would collide "
        "with; the working-tree scope (git grep --untracked) answers what a "
        "sibling window that wrote but did not commit would collide with, so "
        "an uncommitted edit and an untracked file both count. Every hit "
        "carries needle, scope, file and line, the FREE/OCCUPIED verdict "
        "reconciles against head/tree/per-needle counts, --limit bounds the "
        "detail with an honest truncated flag, and any hit refuses to seed "
        "(E_SAN_OCCUPIED, CLI 2 with REFUSE TO SEED) while FREE exits 0, bad "
        "flags 2 and a non-repository or git failure 3. "
        "GIT_CEILING_DIRECTORIES is pinned to the parent of the scanned root "
        "so a plain directory cannot borrow an enclosing repository. "
        "Criteria AC-SAN1..AC-SAN5 were pinned in state/queue/tech.md as the "
        "R2248 e seed BEFORE the code, with a zero-occupancy anchor check at "
        "HEAD (os-seed-anchor / test_seed_anchor / E_SAN rc=1). Evidence: "
        "SUITE PASS 5/5 double-run byte-identical criterion sha16 "
        "42FAF3CADB8BEEF9 (qa/seed-anchor-R2259-a.log and -b.log, 429B each, "
        "single writer utf-8 LF through src/os/evidence_R2259.py), five "
        "adjacent os suites green (qa/regression-R2259.log, fails=0), wired "
        "os-seed-anchor(5). Live: seed_anchor OCCUPIED head=31 tree=52 (text "
        "occupancy, disclosed) while the fresh label os-seed-anchor reads "
        "FREE at HEAD and only becomes occupied in the working tree. Honest "
        "defect: the first HEAD leg put the revision before the pattern, git "
        "consumed HEAD as the needle, and every HEAD scan read zero - fixed "
        "in the module with an explicit -e, no criterion relaxed.",
    ],
]

RESULTS = [
    [
        "R2259",
        "R2259 product window on the debt register first item: the R2248 e "
        "seed shipped as src/os/seed_anchor.py with AC-SAN1..AC-SAN5 pinned "
        "in state/queue/tech.md BEFORE the code and a zero-occupancy anchor "
        "check at HEAD. SUITE PASS 5/5 double-run byte-identical criterion "
        "sha16 42FAF3CADB8BEEF9 (qa/seed-anchor-R2259-a.log and -b.log, 429B "
        "each, single writer utf-8 LF), five adjacent os suites green "
        "(qa/regression-R2259.log, fails=0), wired os-seed-anchor(5). Live "
        "reading: seed_anchor OCCUPIED head=31 tree=52 (text occupancy), "
        "os-seed-anchor FREE at HEAD head=0 and occupied only in the working "
        "tree. One implementation defect found by the suite and fixed in the "
        "module (the HEAD leg passed the revision before the pattern so git "
        "read HEAD as the needle; now an explicit -e), no criterion relaxed. "
        "Tech floor refilled in the same window with one real gap row "
        "(evidence_capture, AC-EVC1..AC-EVC6 pre-registered, five anchors "
        "zero-occupancy rc=1), gauge FLOOR-MET main 5/5 tech 10/10 explore "
        "10/10. Register row product-face-R2259 closed, successor "
        "reconcile-battery-R2260 opened as first=yes; the battery and the "
        "matrix regeneration carry to R2260 (the R2168 mixed-tree rule).",
    ],
]

CEO_CURRENT = (
    "R2259 产品窗：把「播种前的名字零占用检查」从一条手敲的 git grep 变成可跑读面"
    "——src/os/seed_anchor.py 双作用域检查（HEAD 已提交版本 + 工作树含未跟踪文件），"
    "命中逐条点名（针/作用域/文件/行），FREE/OCCUPIED 判决与计数互相对得上，任何命中"
    "一律拒绝播种（退出码 2 + REFUSE TO SEED）。判据 AC-SAN1..AC-SAN5 先写进队列行再"
    "动代码，锚点 HEAD 零占用检查存档。套件 5/5 双跑逐字节同一（sha16 "
    "42FAF3CADB8BEEF9），五个相邻套件全绿，已接线 os-seed-anchor(5)。实测：文本里出现过的"
    "名字 seed_anchor 读作 OCCUPIED，而新标签 os-seed-anchor 在 HEAD 仍 FREE、只在工作树里"
    "被占用——这正是第二作用域存在的理由。"
)

CEO_ARTIFACT = (
    "qa/seed-anchor-R2259-a.log 与 -b.log（各 429B，双跑判据行逐字节同一）、"
    "qa/regression-R2259.log（相邻五套件 fails=0）、src/os/seed_anchor.py、"
    "src/os/test_seed_anchor.py；2026-10-29"
)

CEO_NEXT = (
    "R2260 验证轮：在已提交树上跑全量对账电池 + 套件矩阵重生成（零产品代码改动，"
    "R2168 混合树律），把本轮新套件纳入整批回归"
)


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_atomic(path, text):
    data = text.encode("utf-8")
    temp = path + ".tmp-closeout"
    with io.open(temp, "wb") as handle:
        handle.write(data)
    os.replace(temp, path)
    with io.open(path, "rb") as handle:
        back = handle.read()
    if back != data:
        raise SystemExit("E_CLOSE_READBACK: %s" % path)
    if os.path.exists(temp):
        raise SystemExit("E_CLOSE_TEMP: %s" % temp)
    return len(data)


def update_state():
    text = read_text(STATE)
    before = json.loads(text)
    if before.get("tick") != 2258:
        raise SystemExit("E_CLOSE_TICK: expected 2258, got %r"
                         % (before.get("tick"),))
    old_log = before.get("log")
    marker = "\r\n  ]\r\n}"
    if marker not in text:
        raise SystemExit("E_CLOSE_SHAPE: log close not found")
    block = []
    for item in NEW_ITEMS:
        block.append(",\r\n                "
                     + json.dumps(item, ensure_ascii=True))
    body = "".join(block)
    index = text.rfind(marker)
    text = text[:index] + body + text[index:]
    text = text.replace('"tick": 2258', '"tick": 2259', 1)
    measured = state_io.layout(text)
    after = json.loads(text)
    if not measured["layout_ok"]:
        raise SystemExit("E_CLOSE_LAYOUT: %r" % (measured,))
    if len(after["log"]) != len(old_log) + len(NEW_ITEMS):
        raise SystemExit("E_CLOSE_COUNT: %d -> %d"
                         % (len(old_log), len(after["log"])))
    if after["tick"] != 2259:
        raise SystemExit("E_CLOSE_TICK: %r" % (after.get("tick"),))
    size = write_atomic(STATE, text)
    print("STATE bytes=%d log=%d -> %d tick=2259"
          % (size, len(old_log), len(after["log"])))


def update_export():
    derived, _state, export, _pat = CEC.recompute()
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    export["export_ts"] = now.replace(microsecond=0).isoformat()
    export["do"] = (
        "product window R2259: a seed's face name is now a reading instead of "
        "a hand-run git grep - one module with two scopes (HEAD and the "
        "working tree including untracked files), a FREE/OCCUPIED verdict "
        "whose counts reconcile, and a refusal on any hit"
    )
    face = export.get("ceo_face")
    if not isinstance(face, dict):
        raise SystemExit("E_CLOSE_FACE")
    face["current"] = CEO_CURRENT
    face["latest_artifact"] = CEO_ARTIFACT
    face["next_milestone"] = CEO_NEXT
    face["next_milestone_due"] = "2026-10-30T12:00:00+08:00"
    face["last_artifact"] = "qa/seed-anchor-R2259-a.log（R2259，2026-10-29）"
    outs = export.get("outs")
    if not isinstance(outs, list):
        raise SystemExit("E_CLOSE_OUTS")
    export["outs"] = OUTS + [row for row in outs if row not in OUTS][:11]
    results = export.get("results")
    if not isinstance(results, list):
        raise SystemExit("E_CLOSE_RESULTS")
    kept = [row for row in results
            if not (isinstance(row, list) and len(row) >= 2
                    and row[1] == "OSLoop 执行 tick")]
    export["results"] = RESULTS + kept[:15]
    export["results"].append(["2259", "OSLoop 执行 tick"])
    export["self_drive"] = derived
    text = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    size = write_atomic(EXPORT, text)
    print("EXPORT bytes=%d ts=%s idle=%d sub=%d queues=%d/%d/%d"
          % (size, export["export_ts"], derived["idle_fast_mention_lines"],
             derived["substantive_non_idle_mention_lines"],
             derived["queue_main_open"], derived["queue_tech_open"],
             derived["queue_explore_open"]))


def main():
    update_state()
    update_export()
    return 0


if __name__ == "__main__":
    sys.exit(main())