"""R2075 closeout: state.json tick+log, export face refresh, queue and
backlog done marks, derived queue counters. Pure ASCII source."""

import datetime
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(HERE, "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
QUEUE = os.path.join(ROOT, "state", "queue", "explore.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

ROUND = (
    "2026-10-24 R2075 (five-silence scan clean: decisions.md 222 rows with "
    "zero new content-addressed tokens against the baseline, zero "
    "@BigDomain ledger rows, group orders baseline unchanged at 2026-10-24 "
    "06:5x, benchmarks refreshed 2026-10-20 inside 7 days, tree clean, no "
    "index.lock; both standing daily rows for 2026-10-24 were already on "
    "disk so neither was re-run) - two queue heads were gated, so this "
    "window first closed the overdue OSS 72h harvest row (last consumption "
    "R2037 on 10-19; two new slices arrived: OH-20261020-bigmoney.md with "
    "12 quant candidates / 2 adopt and OH-20261020-bigcompute.md; full-text "
    "search found ZERO @BigDomain hits in either, so zero-claim is the "
    "legitimate verdict under the R1154/R1155 precedent and the revenue "
    "lens agrees neither is a commercialisation/growth-domain fit) and then "
    "claimed a newly seeded P3 row with AC-LGM1..AC-LGM8 pre-registered in "
    "the queue row BEFORE the suite existed (AC-LGM prefix, suite name and "
    "runner label all git-grep zero-occupancy rc=1). Delivered "
    "src/sandbox/liveroom/test_liveroom_minorguard_persist.py: the R939 "
    "minor-guard wiring seat had only pinned single refusals, so this suite "
    "pins the front-door ORDER on a counting-guard proxy - the five cheap "
    "doors (empty session, empty room, unattended form, empty risk-control "
    "reference, missing opener id) all reject without ever touching "
    "check_live (0 calls), while the three guard-bearing forms (minor, "
    "unregistered resident, adult) reach it exactly once each - plus the "
    "law that a refused session id stays unused (the adult then opens the "
    "same id and the world holds exactly one row with zero cohort), zero "
    "token movement, the minor live ban and the unregistered-resident "
    "refusal surviving TWO full-stack restarts (guard hydrated from its own "
    "sqlite store, residents readout byte-identical across all three "
    "instances), read faces byte-identical across the three instances with "
    "the disclaimer spine first and last, and a guard-free legacy face "
    "keeping the old behaviour on its own db. SUITE PASS 8/8 double-run "
    "identical stdout sha16 18b56de00d27a767; wired as "
    "liveroom-minorguard-persist(8); battery RUNNER PASS 283/283 suites "
    "green + controls 7/7 in 229.7s; suite-matrix regenerated to 283 suites "
    "/ 2370 criteria and --check byte-identical. Evidence = "
    "qa/liveroom-minorguard-R2075.log + qa/reconcile-all-R2075.log. "
    "Score 2 (runnable suite artifact)."
)
TOKENS = (
    "R2075 tokens: local=~95k api=0 api_reason=five-silence scan + overdue "
    "OSS 72h harvest review (two slices, zero-claim) + minor-guard "
    "front-door suite 8/8 double-run + battery 283/283 + matrix regen/check "
    "+ evidence log + state/export closeout, zero cloud calls"
)
RESULT = (
    "R2075 overdue OSS 72h row closed (two new slices, zero @BigDomain "
    "hits, zero-claim) plus a new liveroom minor-guard front-door suite: "
    "the five cheap doors reject with zero check_live calls while the three "
    "guard-bearing forms reach it once each, a refused session id stays "
    "unused, the minor live ban survives two full-stack restarts, read "
    "faces stay byte-identical and the guard-free face is unchanged. "
    "AC-LGM1..AC-LGM8 pre-registered; 8/8 double-run sha16 "
    "18b56de00d27a767; RUNNER 283/283 + controls 7/7 229.7s; matrix "
    "283/2370 --check byte-identical."
)

with io.open(STATE, "r", encoding="utf-8") as f:
    st = json.load(f)
if int(st["tick"]) == 2074:
    st["tick"] = 2075
    st["last_decision_rows"] = 222
    st["log"].append(ROUND)
    st["log"].append(TOKENS)
else:
    assert int(st["tick"]) == 2075, st["tick"]
    assert st["log"][-2] == ROUND and st["log"][-1] == TOKENS
with io.open(STATE, "w", encoding="utf-8", newline="") as f:
    json.dump(st, f, ensure_ascii=False, indent=4)
    f.write("\n")

qtext = io.open(QUEUE, encoding="utf-8").read()

oss_head = "- [ ] 开源借力持续收获面"
oss_done = "- [x] 开源借力持续收获面"
assert qtext.count(oss_head) + qtext.count(oss_done) == 1, qtext.count(
    oss_head)
oss_note = (
    "〔done 2026-10-24 R2075：72h 收获窗超期收口（末次消费 10-19 R2037）"
    "——新到两切片过目毕=OH-20261020-bigmoney.md（量化候选 12 件·adopt 2）"
    "与 OH-20261020-bigcompute.md；两片 @BigDomain 命中全文实测 0 →零认领"
    "合法（R1154/R1155 口径）·收益透镜照判两片均非本司商业化/增长域契合；"
    "两窗未领时钟维持清零·滚动线按新片落库日 10-20 顺延至 10-23 到期续候〕")
qtext = qtext.replace(oss_head, "- [x] 开源借力持续收获面")
lines = qtext.splitlines(True)
if oss_note not in qtext:
    for i, l in enumerate(lines):
        if l.startswith("- [x] 开源借力持续收获面"):
            lines[i] = l.rstrip("\n") + oss_note + "\n"
            break
qtext = "".join(lines)

lgm_head = "- [ ] liveroom 开播面 minor-guard"
lgm_done = "- [x] liveroom 开播面 minor-guard"
assert qtext.count(lgm_head) + qtext.count(lgm_done) == 1
qtext = qtext.replace(lgm_head, "- [x] liveroom 开播面 minor-guard")
lgm_note = (
    "〔done 2026-10-24 R2075：AC-LGM1..AC-LGM8 全过——八形门序向量三实例"
    "逐位钉死（五形廉价门 check_live 调用数恒 0·三形守卫门各恰 1 次·"
    "E_LIVE_UNATTENDED 先于守卫且不遮蔽）；被拒 session id s-kid 由 adult "
    "再开成功且世界恰 1 行·拒绝零残留；全电池 ledger_tx/cohort/danmaku/"
    "conversions 四表全 0（开播面不动钱）；两次全栈重启后 kid 仍 "
    "E_MG_LIVE_BAN、ghost 仍 E_MG_UNKNOWN、amy 照常开播（实例②2 行·"
    "实例③3 行）·residents_readout 三实例逐字节同一（封禁由守卫库 "
    "hydrate）；s-kid/s2 两场 funnel+transcript+conversion_ledger 跨三实例"
    "逐字节同一且 disclaimer 首尾脊柱成立；无 guard 的 legacy face 缺 "
    "opener 仍可开（own db 1 行·主库 3 行不被写入）；套件 8/8 双跑 stdout "
    "sha16 18b56de00d27a767·接线 liveroom-minorguard-persist(8)·电池 "
    "RUNNER PASS 283/283+controls 7/7 229.7s·矩阵 283/2370 --check "
    "byte-identical·证据 qa/liveroom-minorguard-R2075.log〕")
qtext = qtext.rstrip("\n") + "\n" + lgm_note + "\n" if lgm_note not in qtext else qtext
io.open(QUEUE, "w", encoding="utf-8", newline="").write(qtext)

btext = io.open(BACKLOG, encoding="utf-8").read()
row = (
    "- [x] P3 explore 队头双件（R2075）：OSS 72h 超期收口（两新片零 "
    "@BigDomain 命中→零认领）＋liveroom minor-guard 前置门序跨重启持久例窗"
    "——[done 2026-10-24 R2075]（判据 AC-LGM1..AC-LGM8 预注册先于代码·"
    "五廉价门零 check_live+三守卫门各 1 次+拒绝不占 id+零 token+两重启封禁"
    "仍在+读面三实例字节同一+无 guard 旧路不变；套件 8/8 双跑同一 sha16 "
    "18b56de00d27a767·电池 283/283·矩阵 283/2370 --check byte-identical；"
    "详见 state/queue/explore.md 同名行 done 注）\n")
rows_inserted = False
if "P3 explore 队头双件（R2075）" not in btext:
    lines = btext.splitlines(True)
    for i, l in enumerate(lines):
        if l.startswith("- [ ] tech 队列 R2059 四行 sku_top"):
            lines.insert(i, row)
            rows_inserted = True
            break
    if not rows_inserted:
        lines.insert(0, row)
    io.open(BACKLOG, "w", encoding="utf-8", newline="").write("".join(lines))

d = json.load(io.open(EXPORT, encoding="utf-8"))
d["export_ts"] = datetime.datetime.now().astimezone().replace(
    microsecond=0).isoformat()
d["ceo_face"]["current"] = (
    "R2075: the live-room opening face now pins its minor-guard front-door "
    "order - the five cheap doors reject without ever consulting the guard, "
    "the three guard-bearing forms reach it exactly once each, a refused "
    "session id stays unused, and the minor live ban survives two full "
    "restarts from the guard's own store.")
d["ceo_face"]["latest_artifact"] = (
    "src/sandbox/liveroom/test_liveroom_minorguard_persist.py + "
    "qa/liveroom-minorguard-R2075.log (SUITE PASS 8/8 double-run identical "
    "stdout sha16 18b56de00d27a767; RUNNER PASS 283/283 suites + controls "
    "7/7 229.7s = qa/reconcile-all-R2075.log; suite-matrix 283 suites / "
    "2370 criteria byte-identical, 2026-10-24)")
d["ceo_face"]["next_milestone"] = (
    "2026-10-25: the nine-company automation build plan (funnel four-ring "
    "spec + 72h self-continuation acceptance to 10-31) goes to the council "
    "three-in-one submission; P-47 design sets stay gated on the CEO "
    "merchant/server physical parts.")
_OUT_TEXT = (
    "开播面 minor-guard 前置门序+跨重启封禁持久件（R2075）："
    "src/sandbox/liveroom/test_liveroom_minorguard_persist.py 8 判据全绿"
    "（SUITE 8/8 双跑同一 sha16 18b56de00d27a767·电池 283/283·矩阵 "
    "283/2370 --check byte-identical·证据 qa/liveroom-minorguard-R2075.log）"
    "——五廉价门零 check_live、三守卫门各 1 次、拒绝不占 session id、零 "
    "token、两次全栈重启封禁仍在、读面跨实例字节同一、无 guard 旧路不变")
if not any(isinstance(o, list) and len(o) > 1 and "R2075" in str(o[1])
           for o in d["outs"]):
    d["outs"].append(["2", _OUT_TEXT])
for _stray in ("window", "window_days", "log_lines_in_window",
               "idle_fast_mention_lines", "no_pullable_mention_lines",
               "substantive_non_idle_mention_lines", "proposals_total",
               "proposals_open", "queue_main_open", "queue_tech_open",
               "queue_explore_open"):
    if _stray in d and "self_drive" in d:
        d.pop(_stray, None)
if not any(isinstance(r, list) and len(r) > 1 and r[1] == "R2075"
           or (isinstance(r, list) and r and r[0] == "R2075")
           for r in d["results"]):
    d["results"].append(["R2075", RESULT])
for r in d["results"]:
    if isinstance(r, list) and len(r) > 1 and r[1] == "OSLoop \u6267\u884c tick":
        r[0] = "2075"
import sys
sys.path.insert(0, HERE)
import check_export_consistency as C
derived = C.recompute()[0]
for key in ("window", "window_days", "log_lines_in_window",
            "idle_fast_mention_lines", "no_pullable_mention_lines",
            "substantive_non_idle_mention_lines", "proposals_total",
            "proposals_open", "queue_main_open", "queue_tech_open",
            "queue_explore_open"):
    d["self_drive"][key] = derived[key]
io.open(EXPORT, "w", encoding="utf-8", newline="").write(
    json.dumps(d, ensure_ascii=False, indent=2) + "\n")
print("CLOSEOUT-OK tick=%d results=%d outs=%d explore_open=%d tech_open=%d"
      % (st["tick"], len(d["results"]), len(d["outs"]),
         d["self_drive"]["queue_explore_open"],
         d["self_drive"]["queue_tech_open"]))