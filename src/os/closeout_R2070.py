import io
import json
import os
import re
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
DEC = r"C:\Users\sjs20\Desktop\FluxGroup\docs\decisions.md"
STATE = os.path.join(ROOT, "src", "os", "state.json")

text = io.open(STATE, encoding="utf-8", newline="").read()
doc = json.loads(text)

raw = io.open(DEC, encoding="utf-8").read()
found = set(re.findall(r"\b[DC]-\d{8}-\d{1,3}\b", raw))
baseline = set(doc["last_dec_tokens"].split(","))
new = sorted(found - baseline)
rows = len(raw.splitlines())
table_rows = len([l for l in raw.splitlines()
                  if l.strip().startswith("| 2026-")])
print("new_tokens=%r rows_now=%d table_rows=%d" % (new, rows, table_rows))
if new:
    sys.exit("FATAL: unjudged decision tokens %r" % (new,))

NARRATIVE = (
    "2026-10-24 R2070 (P3 explore-queue FIFO head claim; seed = R2042"
    " idem_expired_rebilling_cases; the earlier heads stay non-claimable:"
    " the merchant-account payment row is a physical-item wait, the OSS"
    " 72h harvest row was consumed by the 10-24 skill-scan slice, and the"
    " honorcert already-granted row would duplicate R2029 AC-HYGG1..7),"
    " the lobby chat mute / idempotency boundary family. Five-silence"
    " scan clean: decisions.md zero new content-addressed tokens against"
    " the baseline, ledger zero new @BigDomain rows, the group orders"
    " tail row judged (the 2026-10-24 06:5x row is the decision-round"
    " receipt for D-20261024-05, whose five-line research delivery"
    " already carries our skill-scan slice, so the orders baseline"
    " advances to 2026-10-24 06:5x), benchmarks refreshed 2026-10-20"
    " (inside 7 days), tree clean, no index.lock. Claimed the explore row"
    " with AC-CMI1..AC-CMI8 pre-registered in the queue row BEFORE the"
    " suite existed (AC-CMI prefix git grep zero-occupancy verified)."
    " Finding pinned: in handle_chat the identity/room/empty/content"
    " gates run first, then the idempotency gate, then the rate/mute"
    " gate, so inside a mute window an in-TTL (client_msg_id, text)"
    " replay still answers chat.duplicate (no budget, no violation, no"
    " store row) while an EXPIRED replay falls through into the mute"
    " refusal; and the idem cache is lobby-scoped rather than"
    " connection-scoped, so a second connection can seed a key that a"
    " muted connection replays to a duplicate. Delivered"
    " src/sandbox/lobby/test_chatmute_idem.py: a deterministic fake"
    " clock replaces the server module's time binding (this binding"
    " only, restored on exit) so the 5/10s window, the 60s mute and the"
    " idem TTL all move without sleeps, and the shipped config is read"
    " from disk then only TTL-compressed in memory to 5s (data only) so"
    " an expired replay lands inside one saturated rate window. Verified:"
    " the saturated window answers a replay with the ORIGINAL evt_id and"
    " leaves rows/budget/violations/cache untouched; three expired"
    " rebills answer err.rate_limit, err.rate_limit, then sec.reject"
    " E_RATE_LIMIT 'muted for 60 seconds (3 consecutive violations)'"
    " with violations 1->2->0 and muted_until == now+60; a fresh send"
    " inside the mute answers 'temporarily muted' with the wall-clock"
    " mirror echoed and zero side effects; the cross-connection in-TTL"
    " replay answers chat.duplicate with the seeded evt_id while the mute"
    " state, violations, rows and cache size stay frozen; mute expiry"
    " resumes the connection (rows +1, window pruned to one send); the"
    " whole battery leaves exactly seven chat.broadcast rows with seven"
    " distinct evt_ids (zero rows from any refusal path); and the five"
    " orthogonal refusals (not resident, unknown room, empty text, gate-1"
    " word, gate-2 word) each answer their own code with the mute"
    " counters at zero (mute accounting belongs to the rate gate alone)."
    " SUITE PASS 8/8 double-run identical (stdout sha16"
    " f7f1249d64c40c47); wired lobby-chat-mute-idem (8) into"
    " reconcile_all SUITES; full battery RUNNER PASS 278/278 suites +"
    " controls 7/7 217.5s = qa/reconcile-all-R2070.log; suite-matrix"
    " regenerated 278 suites / 2332 criteria, --check byte-identical"
    " (26939 bytes); live census DRIFT-CLEAN after the dialect repair"
    " below. Honest notes: (a) the first battery run failed exactly one"
    " suite - reconcile-daily-census cd7 - because the R2069 evidence log"
    " qa/funnel-sku-top-rank-R2069.log carried a mixed dialect (9 CRLF"
    " lines against 31 LF); it was normalised to LF with content bytes"
    " proven equal (1331 -> 1322 bytes, zero non-newline change) and the"
    " re-run is green (same family as the R2068 CRLF leftover); (b)"
    " AC-CMI8 first failed on its own detector literals self-matching"
    " (the R1678 self-reference lesson); the check was rewritten as an"
    " import-line scan that names the banned modules instead of scanning"
    " raw substrings; (c) the tech queue still stands at 4 open rows,"
    " under the >=10 baseline, carried forward for reseeding from real"
    " gaps next round (no manufactured seeds); explore open goes 6 -> 5,"
    " main open unchanged at 6 (all blocked on CEO physical items)."
    " Score 2."
)

TOKENS = ("R2070 tokens: local=~120k api=0 api_reason=five-silence scan +"
          " mute/idempotency boundary suite 8/8 double-run + full battery"
          " 278/278 + matrix regen/check + census dialect repair +"
          " state/export closeout, zero cloud calls")

NL = "\r\n" if "\r\n" in text else "\n"
tail = '"' + NL + '    ]' + NL + '}' + NL
if not text.endswith(tail):
    sys.exit("FATAL: state tail anchor miss")
text = text[:-len(tail)] + '",' + NL + '        ' + json.dumps(
    NARRATIVE) + ',' + NL + '        ' + json.dumps(TOKENS) + NL + \
    '    ]' + NL + '}' + NL
text, n = re.subn(r'"tick": \d+', '"tick": %d' % (doc["tick"] + 1),
                  text, count=1)
if n != 1:
    sys.exit("FATAL: tick anchor miss")
new_set = ",".join(sorted(baseline | found))
text, n = re.subn(r'"last_dec_tokens": "(?:[^"\\\\]|\\\\.)*"',
                  lambda m: '"last_dec_tokens": "%s"' % new_set,
                  text, count=1)
if n != 1:
    sys.exit("FATAL: token baseline anchor miss")
text, n = re.subn(r'"last_decision_rows": \d+',
                  '"last_decision_rows": %d' % rows, text, count=1)
if n != 1:
    sys.exit("FATAL: rows anchor miss")
text, n = re.subn(r'"last_order": "(?:[^"\\\\]|\\\\.)*"',
                  '"last_order": "2026-10-24 06:5x"', text, count=1)
if n != 1:
    sys.exit("FATAL: last_order anchor miss")

doc2 = json.loads(text)
if doc2["tick"] != doc["tick"] + 1:
    sys.exit("FATAL: tick not applied")
if doc2["log"][-1] != TOKENS:
    sys.exit("FATAL: log tail not the tokens line")
io.open(STATE, "w", encoding="utf-8", newline="").write(text)

QP = os.path.join(ROOT, "state", "queue", "explore.md")
ql = io.open(QP, encoding="utf-8", newline="").read().split("\n")
hit = 0
for i, line in enumerate(ql):
    if line.startswith("- [ ] lobby chat idem_seen"):
        ql[i] = line.replace("- [ ] ", "- [x] ", 1) + (
            "〔done 2026-10-24 R2070：AC-CMI1..8 全过·套件 "
            "src/sandbox/lobby/test_chatmute_idem.py SUITE PASS 8/8 双跑"
            "同一（stdout sha16 f7f1249d64c40c47）·接线 "
            "lobby-chat-mute-idem(8)·电池 RUNNER PASS 278/278 suites+"
            "controls 7/7 217.5s=qa/reconcile-all-R2070.log·矩阵 278/2332 "
            "--check byte-identical·census DRIFT-CLEAN（R2069 证据件混行尾"
            "LF 归一如实注）·真相=idem 门先于静默门（肥默期 in-TTL 重放"
            "仍答 chat.duplicate）而 idem 缓存为大厅级非连接级（跨连接播种"
            "可被静默连接重放）·静默计数只归速率门（五正交拒绝零计）·证据 "
            "qa/lobby-chat-mute-idem-R2070.log〕")
        hit += 1
if hit != 1:
    sys.exit("FATAL: explore row hit=%d" % hit)
io.open(QP, "w", encoding="utf-8", newline="\n").write("\n".join(ql))

BP = os.path.join(ROOT, "src", "os", "backlog.md")
bl = io.open(BP, encoding="utf-8", newline="").read().split("\n")
done = (
    "- [x] P3 explore 队头认领（R2070）：lobby chat idem_seen 过期重发三连"
    "静默+静默期内 in-TTL 重放免疫例窗（R2042 AC-IDR 后继）——"
    "[done 2026-10-24 R2070]（判据 AC-CMI1..CMI8 预注册先于代码·假钟"
    "替换 server.time 单绑定（窗/静默/TTL 零睡眠推进）+config 仅内存 "
    "TTL 压到 5s（数据面零产品改动）·真相=idem 门先于静默门+idem 缓存"
    "大厅级非连接级+静默计数只归速率门·套件 8/8 双跑同一·电池 278/278+"
    "--check byte-identical；详见 state/queue/explore.md 同名行 done 注）")
idx = None
for i, line in enumerate(bl):
    if line.startswith("- ["):
        idx = i
        break
if idx is None:
    sys.exit("FATAL: backlog item list not found")
bl.insert(idx, done)
io.open(BP, "w", encoding="utf-8", newline="\n").write("\n".join(bl))

print("STATE-QUEUE-BACKLOG-OK tick=%d rows=%d new_tokens=%d"
      % (doc2["tick"], rows, len(new)))