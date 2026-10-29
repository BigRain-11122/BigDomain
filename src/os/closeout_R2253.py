# closeout_R2253.py - one-shot closeout for the R2253 window.
# Writes: the tech queue claim row (done) + one honest seed row, a backlog
# done row at the top, state.json (tick, log, canonical layout) and the
# status export face. Every reader is verified after the write.
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

TECH = os.path.join(ROOT, "state", "queue", "tech.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

OLD_HEAD = ("- [ ] P2 tech seed (R2248 b): `src/os/queue_row.py` - a seed "
            "exists so its criteria are registered BEFORE the code")

NEW_ROW = (
    "- [x] [done 2026-10-29 R2253] P2 tech seed claim (R2248 b; Criteria "
    "prefix AC-QROW, pre-registered in this row BEFORE the code; anchor "
    "check at HEAD 2026-10-29: `os-queue-row` git grep -F zero-occupancy "
    "rc=1 and `AC-QROW` only in the seed row text and its generator - "
    "disclosed name collision, queue_floor.py already ships a FUNCTION "
    "named queue_row, so this module imports that file's row law instead "
    "of writing a second one): delivered src/os/queue_row.py - the "
    "pre-registration gate. A claimable open row must name its criteria "
    "prefix and only two forms are accepted: FORM-1 `Criteria prefix "
    "AC-<TOKEN>` and FORM-2 `Criteria AC-<TOKEN><n>`; a row naming no "
    "prefix is a violation and a row carrying a gate marker is exempt but "
    "still reported, so a queue of pure gates reads as debt rather than as "
    "stock. Every refusal carries file, line and an ASCII excerpt. "
    "Disclosed refinement over the seed wording: the seed asked only for "
    "the literal `Criteria prefix AC-` phrase, and that alone would have "
    "flagged rows that DO pre-register (the R2248 seeds write `Criteria "
    "AC-QROW1..6`), which is a false negative for the gate's purpose - so "
    "FORM-2 was accepted as a second pinned form, not as a relaxation of "
    "the requirement. Evidence: SUITE PASS 6/6 double-run byte-identical "
    "criterion sha16 FEA1FEEF8476A141 (qa/queue-row-R2253-a.log / -b.log, "
    "453B each, single writer utf-8 LF through src/os/evidence_R2253.py, "
    "never a shell redirection); wired os-queue-row(6) in "
    "src/sandbox/reconcile_all.py; five adjacent os suites green "
    "(qa/regression-R2253.log, fails=0). Live reading at closeout: "
    "QUEUE ROW GATE claimable=25 prefixed=16 gated=2 violations=9 "
    "verdict=GATE-DEBT (main 5 violations, tech 3, explore 1) - the gate "
    "reports real legacy debt instead of exempting itself into a pass. "
    "The full reconcile battery and the suite-matrix regeneration were NOT "
    "run in this 25-minute window (the R2168 mixed-tree rule) and are "
    "registered as first=yes in state/debt.md.")

SEED_ROW = (
    "- [ ] P2 tech seed (R2253): `src/os/queue_row_exempt.py` - the "
    "pre-registration gate shipped this window reports 9 undeclared "
    "claimable rows on the live queues, and every one of them predates the "
    "law. There is currently no way to record an accepted exemption, so "
    "the reading can never go green except by rewriting history it should "
    "not rewrite. One declared exemption file (state/queue/prefix_"
    "exempt.json) with a dated reason per row, keyed by a stable row "
    "identity rather than a line number, consulted by the gate and "
    "reported as exempt_today against still_debt. Criteria prefix AC-QRX1.."
    "AC-QRX6 pre-registered here BEFORE any code (exemption file law, "
    "stable row identity, dated reason required, expired exemption reads "
    "as debt again, gate integration, purity).")

BACKLOG_ROW = (
    "- [x] [done 2026-10-29 R2253] P2 tech head claim (R2248 b seed; "
    "Criteria prefix AC-QROW pre-registered in that queue row BEFORE the "
    "code): src/os/queue_row.py - pre-registration becomes a gate. The row "
    "law is imported from queue_floor (no second wheel), two declaration "
    "forms are accepted and only those two, gated rows are exempt but "
    "still reported, and every refusal carries file/line/excerpt. Suite "
    "6/6 double-run byte-identical sha16 FEA1FEEF8476A141, five adjacent "
    "os suites green, wired os-queue-row(6). Live gate: 25 claimable, 16 "
    "prefixed, 9 violations (GATE-DEBT) - reported, not hidden. Debt: the "
    "full battery and the matrix regeneration carry to R2254.\n")

ROUND = (
    "2026-10-29 R2253 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; the queue gauge read main "
    "5/5 tech 10/10 explore 10/10 FLOOR-MET with tech carrying 11 open "
    "rows of which 1 gated and explore 10 open; decisions.md carries 187 "
    "content-addressed D/C tokens against the stored 194-token superset "
    "baseline, so the diff is ZERO additions - the seven apparent losses "
    "are the known group-side rotation and truncation artefacts and the "
    "baseline stays a superset so a later-restored token cannot "
    "masquerade as a new decision - hence zero domain action; the group "
    "ledger carries the same three @BigDomain patrol rows already paid "
    "off, none numbered, so zero unreplied handoffs; the group orders tail "
    "reads 2026-10-29 00:52, earlier than the stored 02:1x baseline, so no "
    "new command; benchmarks refreshed 2026-10-29 inside the seven-day "
    "gate) - the P1 canonical rows stay blocked-on-CEO and the weekly "
    "proposal duty is met by BD-PROP-005, and the four top tech rows are "
    "all gated (docker host absent, the logs toolkit in standing "
    "maintenance, the member refunded schema product-gated, the live-mtime "
    "row waiting on a real normalized-mtime event), so this window claimed "
    "the first real row of the R2248 seed family. Product: "
    "src/os/queue_row.py, the pre-registration gate the R2248-b seed "
    "asked for. Pain: a seed row is supposed to register its criteria "
    "before any code, but nothing enforced it - a window could append a "
    "claimable row with no criteria and the floor gauge would count it as "
    "stock. Now a claimable open row must name its criteria prefix, in one "
    "of two pinned forms, with gated rows exempt but still reported and "
    "every refusal carrying file, line and an ASCII excerpt. The row law "
    "is imported from queue_floor rather than re-implemented, which is "
    "also how the disclosed name collision (that module already ships a "
    "FUNCTION called queue_row) stays harmless. Two suite runs were red on "
    "this-window test defects - a sorted() over None prefixes and a "
    "miscounted violation line - and both were fixed in the test, with no "
    "criterion widened and no product behaviour changed for the test's "
    "sake. Live reading at closeout: claimable=25 prefixed=16 gated=2 "
    "violations=9 verdict=GATE-DEBT, i.e. the nine legacy rows that "
    "predate the law are reported as real debt rather than exempted into a "
    "pass; that reading opened its own follow-up seed (queue_row_exempt). "
    "The full reconcile battery and the matrix regeneration are deferred "
    "and registered as first=yes in state/debt.md.")

TOKENS = (
    "R2253 tokens: local=~17k api=0 api_reason=product window on the P2 "
    "tech head - one gate module with its six pre-registered criteria, two "
    "suite runs to green with two real test-side defects fixed, one "
    "single-writer double-run evidence pair, five adjacent os regressions, "
    "one live reading that honestly reports nine legacy violations, one "
    "seeded follow-up row, and the queue/backlog/debt/state/export "
    "closeout; zero cloud calls and zero external API touches; the battery "
    "and the matrix regeneration carry to R2254")

SELF_HEAL = (
    "R2253 self-heal check: BigDomain-OSLoop is registered and its "
    "principal still reads LogonType=InteractiveToken, which the "
    "2026-09-29 machine law forbids for every lane task; "
    "src/os/register_loop_task.ps1 already passes an explicit S4U "
    "principal and needs an elevated shell to apply it, and this session "
    "runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(twenty-second consecutive disclosure, registered as the stale row "
    "loop-s4u-reconcile in state/debt.md).")


def fail(code, detail=""):
    print("%s %s" % (code, detail))
    return 1


def edit_queue():
    text = io.open(TECH, encoding="utf-8", newline="").read()
    if text.count(OLD_HEAD) != 1:
        return fail("E_TECH_HEAD", str(text.count(OLD_HEAD)))
    start = text.index(OLD_HEAD)
    end = text.index("\n", start)
    new = text[:start] + NEW_ROW + text[end:] + "\n" + SEED_ROW + "\n"
    io.open(TECH, "w", encoding="utf-8", newline="").write(new)
    check = io.open(TECH, encoding="utf-8", newline="").read()
    print("TECH open=%d done_has_row=%r seed=%r"
          % (len([ln for ln in check.split("\n")
                  if ln.startswith("- [ ]")]),
             "R2253" in check, "queue_row_exempt" in check))
    return 0


def edit_backlog():
    text = io.open(BACKLOG, encoding="utf-8", newline="").read()
    lines = text.split("\n")
    at = 0
    for index, line in enumerate(lines):
        if line.startswith("- ["):
            at = index
            break
    lines.insert(at, BACKLOG_ROW.rstrip("\n"))
    io.open(BACKLOG, "w", encoding="utf-8", newline="").write(
        "\n".join(lines))
    return 0


def edit_state():
    doc = json.load(io.open(STATE, encoding="utf-8"))
    doc["tick"] = int(doc.get("tick", 0)) + 1
    log = doc.get("log") or []
    for line in (ROUND, TOKENS, SELF_HEAL):
        if line not in log:
            log.append(line)
    doc["log"] = log
    text = json.dumps(doc, ensure_ascii=False, indent=2)
    text = state_io.canon(text)
    data = text.encode("utf-8")
    with open(STATE, "wb") as handle:
        handle.write(data)
    read_back = json.load(io.open(STATE, encoding="utf-8"))
    layout = state_io.layout(io.open(STATE, encoding="utf-8",
                                     newline="").read())
    ok = (read_back["tick"] == doc["tick"] and read_back["log"] == log)
    print("STATE tick=%d bytes=%d layout_ok=%r items=%d ok=%r"
          % (read_back["tick"], len(data), layout.get("layout_ok"),
             len(log), ok))
    return 0 if ok else 1


def edit_export():
    doc = json.load(io.open(EXPORT, encoding="utf-8"))
    doc["export_ts"] = "2026-10-29T13:40:00+08:00"
    doc["do"] = (
        "product window R2253: the queue gains a pre-registration gate - "
        "src/os/queue_row.py refuses a claimable open row that names no "
        "criteria prefix (two pinned forms, gated rows exempt but "
        "reported), suite 6/6 double-run byte-identical, live reading "
        "claimable=25 prefixed=16 violations=9 GATE-DEBT")
    face = doc.get("ceo_face") or {}
    face["current"] = (
        "R2253 产品窗：队列预注册闸上线——可认领的开行必须写明判据前缀，"
        "闸读活队列 25 可认领 / 16 已声明 / 9 条历史欠账（如实报红不豁免）")
    face["latest_artifact"] = (
        "src/os/queue_row.py + qa/queue-row-R2253-a.log（453B·单写者 "
        "UTF-8 LF·SUITE PASS 6/6 双跑逐字节同一 sha16 FEA1FEEF8476A141）"
        "·2026-10-29 R2253")
    face["next_milestone"] = (
        "R2254：先清验证欠账（全量电池 + 套件矩阵再生，含新接线的 "
        "os-queue-row(6)），再按队列闸自己报出的欠账补一条豁免登记面")
    face["next_milestone_due"] = "2026-10-31T13:40:00+08:00"
    face["last_artifact"] = (
        "src/os/queue_row.py + qa/queue-row-R2253-a.log（R2253·2026-10-29）")
    doc["ceo_face"] = face
    results = doc.get("results") or []
    entry = ["2253", "OSLoop 执行 tick"]
    if entry not in results:
        results.append(entry)
    doc["results"] = results
    outs = doc.get("outs") or []
    outs.append([
        "queue pre-registration gate (R2253)",
        "on",
        "src/os/queue_row.py: a claimable open queue row must name its "
        "criteria prefix, so pre-registration is a gate instead of a "
        "habit. Two pinned forms (Criteria prefix AC-<TOKEN>, Criteria "
        "AC-<TOKEN><n>), the row law imported from queue_floor rather "
        "than re-implemented, gated rows exempt but still reported, every "
        "refusal carrying file/line/excerpt. Suite 6/6 double-run "
        "byte-identical sha16 FEA1FEEF8476A141 through the single-writer "
        "evidence script, wired as os-queue-row(6). Live reading: 25 "
        "claimable, 16 prefixed, 9 legacy violations reported as debt.",
    ])
    doc["outs"] = outs
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    io.open(EXPORT, "w", encoding="utf-8", newline="").write(text)
    back = json.load(io.open(EXPORT, encoding="utf-8"))
    print("EXPORT ts=%s results=%d outs=%d ok=%r"
          % (back["export_ts"], len(back["results"]), len(back["outs"]),
             back["ceo_face"] == face))
    return 0


def main():
    for step in (edit_queue, edit_backlog, edit_state, edit_export):
        code = step()
        if code:
            return code
    print("CLOSEOUT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())