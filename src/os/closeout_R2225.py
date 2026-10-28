"""R2225 closeout: bump the tick, append the round narrative plus the token
ledger line to src/os/state.json by text surgery (layout preserved), stamp
heartbeat.txt, refresh docs/status-export.json, and mark the fold claim rows
done in src/os/backlog.md and state/queue/tech.md. Verify-then-write.
ASCII source, ASCII log text.
"""
import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
HEART = os.path.join(ROOT, "heartbeat.txt")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
TECHQ = os.path.join(ROOT, "state", "queue", "tech.md")

ROUND_LINE = (
    "2026-10-29 R2225 (five-silence scan at open: state.json carried 3 bare-LF "
    "lines from the R2224 closeout, repaired first with logs_toolkit.py eol "
    "--fix --execute (written, json_eq true, post_bare_lf 0) and --fix-indent "
    "--execute (232 item lines re-indented, post_indent_ok true, zero content "
    "change); the group ledger carries the same three @BigDomain patrol rows "
    "already paid off; decisions.md 363 rows / 180 content-addressed tokens with "
    "ZERO new against the stored baseline; the group orders baseline is unchanged "
    "at the 2026-10-29 00:52 CEO-PROXY fleet event round, acknowledged as a fleet "
    "dispatcher face with zero domain action; benchmarks refreshed 2026-10-29 "
    "inside the seven-day gate; tree clean, no index.lock) - this window claimed "
    "the P2 tech fold row that R2223 and R2224 both carried, because R2224 made "
    "the ledger coverage law archive-aware and that is exactly what the surgery "
    "needed. AC-FLD1..AC-FLD8 were registered in state/queue/tech.md BEFORE the "
    "surgery. Execution, with one self-corrected mistake disclosed: the first "
    "attempt folded window 1:200, which split the R2211 narrative from its own "
    "ledger line, so the live face reported rounds_without_ledger=2211; "
    "state.json was restored byte-exact from logs/state-preop-R2225.bak "
    "(410064B), the archive section that attempt had appended was trimmed back "
    "to 4264954B, and the fold was redone on the pair-aligned window 1:201. "
    "Final fold 591: 410064B -> 55509B, predicted_eq_actual true, token_missing "
    "[] with the tool PAT catalog (436 tokens) named in full in the one-line "
    "summary, appendix 354807B appended verbatim; gauge then reads log_lines 32, "
    "margin_bytes 22991, fold_needed False, and census reads section integrity "
    "pass=True with zero unknown mismatches. The exemption list landed the "
    "R2224 design at last, and its premise was PROVEN rather than assumed: the "
    "archive carries both 'R2090 tokens:' and 'R2095 tokens:' lines, so the two "
    "long-standing live gaps were a window-truncation artefact, not real gaps - "
    "state/ledger_gaps.json is now empty, and AC-LGR8 / AC-LGB8 were re-pinned "
    "to the folded reality (live gap set empty, exemption list empty, the two "
    "folded rounds present as ledger lines in the archive). Both ledger faces "
    "read VERDICT CLEAN: live ledger=13 round=18, scoped live+archive ledger=241 "
    "round=1773. Regression: os-ledger-lines 8/8, os-ledger-baseline 8/8, "
    "os-ledger-closeout 8/8. Verification on the folded tree: the first battery "
    "launch was cancelled by the five-minute no-output rule because its output "
    "was piped through a truncating selector - the ownership check found no "
    "surviving reconcile child and no evidence file (zero loss, nothing to "
    "clean) - so it was re-run as a direct stream and came back RUNNER PASS "
    "412/412 suites green plus reconcile controls 7/7 in 958.8s "
    "(qa/reconcile-all-R2225.log, single-writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), with the birth-site "
    "tmp sweep inside the same battery window reclaiming candidates=910 "
    "removed=910 busy=0 failed=0 reclaimed=320.12 MiB. The four post-battery "
    "sections then all passed in the new src/os/battery_followup_R2225.py and "
    "were appended to the same log: the suite matrix regenerated to 412 suites / "
    "3419 criteria (docs/sandbox-suite-matrix.md, 40141 bytes, green=412/412) and "
    "read back byte-identical, the baseline fingerprint chain CLEAN over five "
    "domains, the runner profile --daily --check PASS, and the qa writer census "
    "re-frozen then read DRIFT-CLEAN. So the waterline is unblocked for the first "
    "time since R2223 measured the conflict: 55KB state with 22KB of headroom "
    "instead of 410KB against a 78.5KB gate."
)

TOKEN_LINE = (
    "R2225 tokens: local=~48k api=0 api_reason=five-silence scan with an EOL and "
    "indent repair, one fold executed twice (the first window boundary split a "
    "round pair, reverted byte-exact and redone), the exemption list emptied with "
    "archive proof, two live-gate criteria re-pinned, three gate suites re-run, a "
    "cancelled battery attempt plus the full 412-suite battery and the "
    "four-section follow-up, and the state/export/queue closeout - all local, zero "
    "cloud calls"
)

with io.open(STATE, "rb") as handle:
    raw = handle.read()
text = raw.decode("utf-8")
assert "\r\n" in text
lines = text.split("\r\n")

tick_rows = [i for i, ln in enumerate(lines)
             if re.match(r'^\s*"tick"\s*:\s*\d+,\s*$', ln)]
assert len(tick_rows) == 1, tick_rows
old_tick = int(re.match(r'^\s*"tick"\s*:\s*(\d+),',
                        lines[tick_rows[0]]).group(1))
lines[tick_rows[0]] = re.sub(r'(\d+)', str(old_tick + 1),
                             lines[tick_rows[0]], count=1)

log_start = [i for i, ln in enumerate(lines)
             if ln.strip().startswith('"log"') and ln.strip().endswith("[")]
assert len(log_start) == 1
log_start = log_start[0]
items = []
close_idx = None
for j in range(log_start + 1, len(lines)):
    if lines[j].strip() == "]":
        close_idx = j
        break
    items.append(j)
assert close_idx is not None
indent = re.match(r'^( *)', lines[items[0]]).group(1)

before = json.loads(text)
assert len(before["log"]) == len(items)

lines[items[-1]] = lines[items[-1]] + ","
new_items = ['%s%s,' % (indent, json.dumps(ROUND_LINE, ensure_ascii=False)),
             '%s%s' % (indent, json.dumps(TOKEN_LINE, ensure_ascii=False))]
lines[close_idx:close_idx] = new_items
out = "\r\n".join(lines)
after = json.loads(out)
assert after["tick"] == old_tick + 1
assert after["log"][:-2] == before["log"]
assert after["log"][-2] == ROUND_LINE
assert after["log"][-1] == TOKEN_LINE

with io.open(STATE, "wb") as handle:
    handle.write(out.encode("utf-8"))
with io.open(HEART, "w", encoding="ascii", newline="\n") as handle:
    handle.write("tick %d\n" % (old_tick + 1))

# ---- status export -------------------------------------------------------
with io.open(EXPORT, "r", encoding="utf-8") as handle:
    ex = json.load(handle)
ex["export_ts"] = "2026-10-29T04:20:00+08:00"
ex["do"] = "水线折叠落地（R2225）"
ex["ceo_face"]["current"] = (
    "R2225：把卡了三轮的 state.json 水线折叠真正落了地。R2223 实测出「活日志 30/30 硬律」"
    "与「78500B 水位闸」互斥，R2224 把账本覆盖律改成归档感知，本轮就借这个修法动刀：折叠 591 "
    "把 200 行（R2209..R2224）逐字节追加进 10 月归档，原位留一条摘要行点名全部 436 个 token，"
    "state.json 从 410,064B 降到 55,509B，水位闸余量 22,991B、fold_needed=False，census 节段完整性 "
    "pass=True 零未知不符。中途一次自纠：首跑窗口 1:200 把 R2211 的叙事与账本行切开，活面报出 "
    "rounds_without_ledger=2211，已按备份逐字节回滚、裁掉误追加的归档节（回到 4,264,954B）并改 "
    "1:201 重做。顺带把两条历史豁免清空并证明其性质：归档里 R2090 与 R2095 各自的 tokens 账本行都在，"
    "旧基线属活窗截断假象而非真缺口，state/ledger_gaps.json 已清空。验证：三件账本门套件 8/8/8 全绿，"
    "全量电池 412/412 套件 + 控制 7/7（958.8s），矩阵 412 套件/3419 判据 byte-identical，指纹五域 CLEAN，"
    "证据方言普查 DRIFT-CLEAN。"
)
ex["ceo_face"]["latest_artifact"] = (
    "src/os/state.json 55,509B（折叠 591 后，水位闸余量 22,991B）+ logs/state-log-archive-2026-10.md "
    "新增 R2225 折叠节（200 行逐字节）+ qa/reconcile-all-R2225.log（749,755B 起，单写者 utf-8 LF）"
    "（2026-10-29）"
)
ex["ceo_face"]["next_milestone"] = (
    "R2226（≤48h）：水位闸已腾出约 23KB 余量，回到产品面——认领 explore 队头（商家号门控行之后的真种子）"
    "补产品增量；折叠工艺已可复用，下一次水位到期（约 20 轮后）按同一窗口律执行"
)
ex["outs"].insert(0, [
    "state.json waterline fold under the archive-aware coverage law (R2225)",
    "on",
    "R2223 measured that the waterline gate and the old live-gate law were mutually "
    "unsatisfiable and reverted the fold on evidence; R2224 made the coverage law "
    "archive-aware; this round finally executed the surgery it unblocked. Fold 591 "
    "moved log lines 1:201 (R2209..R2211 including the R2211 self-heal line, then "
    "R2212..R2224) verbatim into logs/state-log-archive-2026-10.md behind one "
    "summary line naming all 436 window tokens under the tool's own PAT, taking "
    "state.json from 410,064B to 55,509B with predicted_eq_actual true and "
    "token_missing empty. The first attempt on window 1:200 split the R2211 "
    "narrative from its ledger line and turned the live face red with "
    "rounds_without_ledger=2211, so it was reverted byte-exact from the pre-op "
    "backup, the archive section it had appended was trimmed back to 4,264,954B, "
    "and the fold was redone on the pair-aligned window - disclosed rather than "
    "hidden. The exemption list also fulfilled the R2224 design and its premise was "
    "proven rather than assumed: the archive carries both 'R2090 tokens:' and "
    "'R2095 tokens:' lines, so the two long-standing live gaps were a "
    "window-truncation artefact and state/ledger_gaps.json is now empty, with "
    "AC-LGR8 and AC-LGB8 re-pinned to the folded reality (live gap set empty, "
    "exemption list empty, folded rounds present as ledger lines in the archive). "
    "Both ledger faces read VERDICT CLEAN (live ledger=13 round=18; scoped "
    "live+archive ledger=241 round=1773), the three gate suites are 8/8/8, and the "
    "folded tree carries a full RUNNER PASS 412/412 suites plus controls 7/7 in "
    "958.8s with TMP RECLAIM 910/910 worlds and 320.12 MiB, matrix 412 suites / "
    "3419 criteria byte-identical, fingerprint CLEAN over five domains, profile "
    "PASS and census DRIFT-CLEAN."
])
ex["results"].insert(0, [
    "R2225",
    "R2225: five-silence scan found only an EOL/indent debt from the R2224 closeout "
    "(repaired first), zero new decision tokens, the same paid-off ledger rows, an "
    "unchanged orders baseline and fresh benchmarks. The window claimed the fold "
    "row R2223 and R2224 both carried and executed fold 591 on the pair-aligned "
    "window 1:201 after one disclosed self-correction (window 1:200 split the R2211 "
    "pair, reverted byte-exact and redone): state.json 410064B -> 55509B, "
    "token_missing [], gauge fold_needed False with 22991B of margin, census "
    "pass=True. The exemption list was emptied on proof - the archive carries both "
    "R2090 and R2095 ledger lines, so the old live gaps were a truncation artefact "
    "- and two live-gate criteria were re-pinned; three gate suites 8/8/8; full "
    "battery RUNNER PASS 412/412 plus controls 7/7 in 958.8s with TMP RECLAIM "
    "910/910 worlds and 320.12 MiB; follow-up matrix 412 suites / 3419 criteria "
    "byte-identical, fingerprint CLEAN five domains, profile PASS, census "
    "DRIFT-CLEAN. The waterline is unblocked for the first time since R2223 "
    "measured the conflict."
])
ex["self_drive"]["log_lines_in_window"] += 2
ex["self_drive"]["substantive_non_idle_mention_lines"] += 2

# ---- queue / backlog row marks ------------------------------------------
def mark(path, needle, note):
    with io.open(path, "r", encoding="utf-8") as handle:
        body = handle.read()
    idx = body.find(needle)
    if idx < 0:
        print("NOT FOUND in %s: %s" % (os.path.basename(path), needle[:60]))
        return None
    end = body.find("\n", idx)
    line = body[idx:end]
    if line.startswith("- [x]"):
        print("already done: %s" % needle[:50])
        return body
    assert line.startswith("- [ ]"), line[:12]
    new_line = "- [x]" + line[len("- [ ]"):] + note
    return body[:idx] + new_line + body[end:]

b = mark(BACKLOG,
         "- [ ] P2 tech head (R2223 first item, carried from R2222): **state.json "
         "waterline fold**",
         " [done 2026-10-29 R2225] Executed as fold 591 on the pair-aligned window "
         "1:201 after one disclosed self-correction (window 1:200 split the R2211 "
         "pair -> reverted byte-exact from logs/state-preop-R2225.bak, archive "
         "trimmed to 4264954B, redone): state.json 410064B -> 55509B, "
         "token_missing [], gauge fold_needed False with margin 22991B, census "
         "pass=True. The R2224 premise landed too - the archive carries both "
         "'R2090 tokens:' and 'R2095 tokens:', so state/ledger_gaps.json is now "
         "empty and AC-LGR8 / AC-LGB8 were re-pinned to the folded reality (live "
         "gap set empty, exemption list empty, folded rounds present in the "
         "archive). Gates VERDICT CLEAN both faces; three gate suites 8/8/8; full "
         "battery RUNNER PASS 412/412 plus controls 7/7 in 958.8s with TMP RECLAIM "
         "910/910 worlds and 320.12 MiB; matrix 412/3419 byte-identical, "
         "fingerprint CLEAN five domains, profile PASS, census DRIFT-CLEAN.")
if b is not None:
    with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(b)

t = mark(TECHQ,
         "- [ ] P2 tech head claim (R2225, the R2223/R2224 carried fold row",
         " [done 2026-10-29 R2225] AC-FLD1..AC-FLD8 all met: eol/indent clean "
         "pre-state; window 1:201 with 32 lines left live; 436-token summary with "
         "token_missing []; 55509B and fold_needed False with 22991B margin; "
         "archive section verbatim with census pass=True; scoped gate VERDICT "
         "CLEAN on both faces with live ledger=13 round=18 and scoped 241/1773; "
         "three gate suites 8/8/8; full battery 412/412 plus controls 7/7 in "
         "958.8s with matrix 412 suites / 3419 criteria byte-identical, "
         "fingerprint CLEAN five domains, profile PASS and census DRIFT-CLEAN. "
         "Honest note: the first window (1:200) split the R2211 narrative from its "
         "ledger line, so it was reverted byte-exact and redone on 1:201 rather "
         "than accepted.")
if t is not None:
    with io.open(TECHQ, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(t)

tech_open = 0
with io.open(TECHQ, "r", encoding="utf-8") as handle:
    for ln in handle:
        if ln.startswith("- [ ]"):
            tech_open += 1
ex["self_drive"]["queue_tech_open"] = tech_open
cross_open = 0
with io.open(os.path.join(ROOT, "state", "queue", "explore.md"),
             "r", encoding="utf-8") as handle:
    for ln in handle:
        if ln.startswith("- [ ]"):
            cross_open += 1
ex["self_drive"]["queue_explore_open"] = cross_open

with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(ex, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

with io.open(STATE, "rb") as handle:
    back = json.loads(handle.read().decode("utf-8"))
print("tick %d -> %d, log %d -> %d, bytes %d -> %d"
      % (old_tick, back["tick"], len(before["log"]), len(back["log"]),
         len(raw), os.path.getsize(STATE)))
print("tech_open=%d explore_open=%d" % (tech_open, cross_open))