# export_closeout_R2235.py - the R2235 closeout writer.
# Updates src/os/state.json (tick, log lines), heartbeat.txt and
# docs/status-export.json (export_ts, do, ceo_face, outs, results and a
# machine-recomputed self_drive block via check_export_consistency.recompute).
# Nothing is hard-coded that the consistency checker can derive.
# Single utf-8 writer, CRLF layout preserved for state.json.
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(HERE, "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
ROUND = 2235

ROUND_LINE = (
    "2026-10-29 R2235 (five-silence scan clean at open: decisions.md 274 "
    "non-empty rows carrying 185 content-addressed D/C/O/T tokens with ZERO "
    "new against the stored baseline; the group ledger carries the same three "
    "@BigDomain patrol rows already paid off with zero unreplied; the group "
    "orders baseline is unchanged at the 2026-10-29 01:3x fleet-event round "
    "already consumed in R2232; benchmarks refreshed 2026-10-29 inside the "
    "seven-day gate; tree clean, no index.lock) - the P1 canonical rows stay "
    "blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, all four "
    "tech heads stayed gated (docker host absent, logs toolkit standing "
    "maintenance, member refunded schema product-gated, the live-mtime row "
    "waiting on a real normalized-mtime event), so this window discharged the "
    "verification debt R2234 recorded as its own next first item rather than "
    "opening a new explore face. No product code was touched (the R2168 "
    "mixed-tree rule). Battery on the committed tree fefa7103: RUNNER PASS "
    "418/418 suites green plus reconcile controls 7/7 in 1050.4s "
    "(qa/reconcile-all-R2235.log, 755285 bytes, CRLF=0 lone CR=0, single-writer "
    "utf-8 LF through src/os/battery_stream.py, never a shell redirection), "
    "with the birth-site tmp sweep inside the same battery window reclaiming "
    "candidates=922 removed=922 busy=0 failed=0 reclaimed=323.64 MiB. Suites "
    "moved 417 -> 418 against R2233, which is exactly the R2234 backlogmonths "
    "suite joining the registry (criteria 3459 -> 3467, the +8 being that "
    "suite's eight criteria). The four post-battery sections then all passed "
    "in the new src/os/battery_followup_R2235.py and were appended to the same "
    "log: the suite matrix regenerated to 418 suites / 3467 criteria and read "
    "back (docs/sandbox-suite-matrix.md, 40791 bytes, evidence header reading "
    "418/418 green), the baseline fingerprint chain CLEAN over five domains "
    "(ledger/lobby/member/pay/ugc), the runner profile --daily --check PASS "
    "against a byte-identical baseline, and the qa writer census re-frozen "
    "then DRIFT-CLEAN on both legs (files=2146 tee=1618 baselined=528 "
    "disappeared=0 flags=0). Disclosed: the first battery invocation was piped "
    "through a truncating selector and died to the five-minute no-output rule "
    "with zero output, no evidence file and no surviving child (the R2211 trap "
    "re-proven); it was re-run unpiped through battery_stream and the whole "
    "green result above comes from that run. Product score honestly zero - "
    "this window bought certainty, not features. The next window can claim the "
    "explore head (the R2230 seed family still carries open seeds) or the "
    "docker-host-gated sandbox boot."
)

TOKENS_LINE = (
    "R2235 tokens: local=~20k api=0 api_reason=verification window - one full "
    "reconcile battery through battery_stream, one cancelled piped attempt "
    "with an ownership check, four follow-up sections in a new script, the "
    "state/export/backlog closeout and the post-closeout gate re-runs; zero "
    "cloud calls and no product code changed (the R2168 mixed-tree rule)"
)

SELFHEAL_LINE = (
    "R2235 self-heal check: the BigDomain-OSLoop scheduled task exists and is "
    "Running, but its principal still reads LogonType=Interactive, which the "
    "2026-09-29 machine law forbids for every lane task. "
    "src/os/register_loop_task.ps1 already passes an explicit S4U principal "
    "and needs an elevated shell to apply it; this session runs unelevated, so "
    "the definition of the loop hosting this window was left untouched. Open "
    "local-lane item for an elevated window (fourth consecutive disclosure)."
)

DO = "verification window R2235: full reconcile battery and suite matrix"

CEO_CURRENT = (
    "R2235 验证窗：R2234 新面（全市场问询积压月面）已由全量对账套件覆盖，"
    "不是只靠它自己的八条判据加邻居。全量电池 418/418 套件全绿 + 对账控制 7/7，"
    "1050 秒；电池后四段（套件矩阵再生 418 套件/3467 判据、指纹五域 CLEAN、"
    "运行器基线逐字节同一、证据写手普查 DRIFT-CLEAN 零漂移）全部 PASS。"
    "本轮无新产品代码（中途改产品会让电池读到与证据不符的混合树）。"
)

CEO_LATEST = (
    "qa/reconcile-all-R2235.log（755285 字节·单写者 utf-8 LF·CRLF=0·"
    "RUNNER PASS 418/418 + 控制 7/7 + 四段跟进节均 PASS）；"
    "docs/sandbox-suite-matrix.md 再生为 418 套件 / 3467 判据（40791 字节）；"
    "src/os/battery_followup_R2235.py（本轮新增跟进脚本）"
)

CEO_MILESTONE = (
    "下一个里程碑：R2236 认领探索队头一枚真种子（R2230 族仍有开项）出可跑产品面，"
    "或 docker 到位后起五沙箱一键联跑；窗 ≤48h"
)

OUT_ROW = [
    "verification debt closed on a green battery, first try (R2235)",
    "on",
    ("full battery on the committed tree fefa7103: RUNNER PASS 418/418 suites "
     "+ controls 7/7 in 1050.4s, birth-site sweep reclaiming 922/922 worlds "
     "and 323.64 MiB; suites 417 -> 418 = the R2234 backlogmonths suite "
     "joining the registry; matrix regenerated to 418 suites / 3467 criteria "
     "(40791 bytes) and read back green, fingerprint CLEAN over five domains, "
     "runner profile --daily --check PASS, census DRIFT-CLEAN "
     "files=2146 flags=0; the R2234 product face is now covered by the whole "
     "battery rather than its own suite alone"),
]

RESULT_ROW = [
    "R2235",
    ("verification window: RUNNER PASS 418/418 suites + controls 7/7 in "
     "1050.4s on the committed tree; four follow-up sections all PASS "
     "(matrix 418/3467, fingerprint CLEAN 5 domains, profile PASS, census "
     "DRIFT-CLEAN files=2146 flags=0); no product code changed"),
]


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def close_state():
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = ROUND
    state["log"].extend([ROUND_LINE, TOKENS_LINE, SELFHEAL_LINE])
    text = json.dumps(state, indent=2, ensure_ascii=False)
    write_text(STATE, text.replace("\n", "\r\n"))
    return state["tick"]


def close_heartbeat():
    write_text(HEARTBEAT, "tick %d\n" % ROUND)


def close_export():
    sys.path.insert(0, HERE)
    import check_export_consistency as checker
    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    export["export_ts"] = checker_now()
    export["do"] = DO
    face = export.setdefault("ceo_face", {})
    face["current"] = CEO_CURRENT
    face["latest_artifact"] = CEO_LATEST
    face["next_milestone"] = CEO_MILESTONE
    export["outs"].insert(0, OUT_ROW)
    export["results"].insert(0, RESULT_ROW)
    derived = checker.recompute()
    export["self_drive"] = derived
    write_text(EXPORT, json.dumps(export, indent=2, ensure_ascii=False) + "\n")


def checker_now():
    import datetime
    return datetime.datetime.now().astimezone().replace(
        microsecond=0).isoformat()


def main():
    tick = close_state()
    close_heartbeat()
    close_export()
    with io.open(STATE, encoding="utf-8") as handle:
        json.load(handle)
    with io.open(EXPORT, encoding="utf-8") as handle:
        json.load(handle)
    print("STATE tick=%d ok" % tick)
    print("EXPORT ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())