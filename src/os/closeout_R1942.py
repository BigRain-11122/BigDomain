# -*- coding: utf-8 -*-
"""R1942 closeout: ledger props cross-restart persist delivery (the
props seat of the R1886 persist family; P2 tech FIFO head = the
R1941 closeout pointer). tech.md done-note + effects reseed,
state.json tick/log/round-line, heartbeat row, export refresh (F3
derived via consistency tool). All edits anchor-exact with
fail-fast asserts; EOL preserved per file.
Round scoring: 2 (runnable artifact, Executive Protocol v1.1)."""

import datetime as _dt
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))


def read_txt(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        raw = fh.read()
    return raw.decode("utf-8")


def write_txt(rel, text):
    with open(os.path.join(ROOT, rel), "wb") as fh:
        fh.write(text.encode("utf-8"))


def eol_of(text):
    return "\r\n" if "\r\n" in text else "\n"


def must_count(text, needle, n, what):
    c = text.count(needle)
    assert c == n, "anchor %r count=%d expected=%d (%s)" % (needle, c, n, what)


# ---------------------------------------------------------------- tech.md
P_TECH = "state/queue/tech.md"
tech = read_txt(P_TECH)
NL = eol_of(tech)
props_open_head = "- [ ] ledger props 道具/装扮经济面读面族跨重启持久化例窗（R1937 补种"
must_count(tech, props_open_head, 1, "props open row head")
tech = tech.replace(
    "- [ ] ledger props 道具/装扮经济面读面族跨重启持久化例窗（R1937 补种",
    "- [x] ledger props 道具/装扮经济面读面族跨重启持久化例窗（R1937 补种", 1)
done_row_head = "- [x] ledger props 道具/装扮经济面读面族跨重启持久化例窗（R1937 补种"
must_count(tech, done_row_head, 1, "props done row head")
done_note = (
    "——[done 2026-10-14 R1942]（执行注记：套件 test_props_persist.py "
    "SUITE 7/7 首跑 5/7〔AC-PSP3/PSP5 两败=套件探针取证口径 bug 非产品缺"
    "陷：①bad-ref 探针缺省 count=0 撞上产品验证序 count≥1 先检门〔props.py "
    "buy_prop 验证序=count 检先于 ref 检=行为正身〕→探针补 count=1 才达 "
    "ref 门〔判据注册文字不动·探针载体勘正〕②冻结比对误含 count_credits "
    "列〔row[:6] 切片〕→stack 行经产品动词合法移被误判漂移→冻结键集改排"
    "除 count_credits〔provenance 五键=inv_id/account/item/kind/bound_"
    "spend_tx/granted_utc·裁定③执法面〕→两修后复跑全绿·R1776 取证口径"
    "两修同族先例〕+双跑 stdout 逐字节同一 sha16 748340e88482cdb8〔rc "
    "0/0·掩码口径=16-hex tx 串+ISO ts 进证据 digest·全字段落位比较不掩"
    "码〕三实例世界真产品径〔Ledger+PropsFace 双件套·props_inventory 单"
    "表 WAL 零 schema 触碰=指纹哨兵 CLEAN domains=5〕——①锚世界〔四购买"
    "谱 alice cosmetic hat_gold@15+prop jetpack count=3@20+bob prop "
    "flare count=2@10〔consume 1→1〕+carol cosmetic scarf_silk@12 各"
    "绑真 spend tx〔SQL cross type=spend+debit 腿 4/4〕+读面电池〔inventory"
    " a/b/c+四余额 265/490/388/18857〕+表计数 props_inventory=4/spend-tx=4〕"
    "②pf.close→led.close→实例②同 db 同 cfg 重开→读面电池逐字节==关前快照"
    "〔inventory 复读存储值 bound_spend_tx/count_credits+balance 复读 "
    "ledger_entries=派生面零内存态漂移〕③八门探针跨重启全拒同码〔cosmetic-"
    "consume E_PROP_BAD_KIND/over-consume E_PROP_INSUFFICIENT/unknown-item "
    "E_PROP_UNKNOWN/持物 kind-drift E_PROP_BAD_KIND/unknown-kind E_PROP_"
    "BAD_KIND/bad-ref E_PROP_BAD_REF/count=0 E_PROP_BAD_AMOUNT+carol 超"
    "预算 E_NEGATIVE_BALANCE 零扣费零 grant〔拒先于 spend=零行律〕〕+探针"
    "批前后表计数冻结〔inv=4 spend_tx=4〕④真径续写〔carol 新 prop lantern "
    "count=4@25 绑真新 spend tx〔SQL cross〕+alice consume jetpack 2〔3→1〕"
    "再 buy count=1〔stack 1→2〕+bob consume flare 1〔1→0〕再 buy count=3"
    "〔stack 0→3〕→读面零缓存重算〔jetpack 2/flare 3/lantern 4+四余额 "
    "245/480/363/18912〕+表计数 inv 4→5/spend-tx 4→7〕⑤冻结面+dup 门跨"
    "重启〔锚四行 provenance 五键逐字节冻结跨重启×续写〔stack 行仅 "
    "count_credits 经产品动词移 jetpack 3→2/flare 1→3·bound_spend_tx/"
    "granted_utc 恒绑首购=stack 路径只 UPDATE count_credits 正身证〕+未触"
    "行 hat_gold/scarf_silk 全行冻结+dup 门 alice hat_gold 再 buy "
    "E_PROP_DUP 零扣费零新行〕⑥纯读律〔读批双调 json.dumps 逐字节同一+表"
    "计数恒定〕⑦实例③三开==实例②终态逐字节+config.json sha256 首尾零改动"
    "+套件源纯 ASCII〔0 non-ascii〕+真 import 行零网络+世界 tmp 仓外〕——"
    "RUNNER PASS 180/180 判据 1592→1599 controls 7/7 282.3s=qa/reconcile-"
    "all-R1942.log〔SUITES 179→180·ledger-props-persist 席·census "
    "DRIFT-CLEAN flags=0〔files=1371 tee=869 baselined=502〕·指纹 CLEAN "
    "domains=5〕+矩阵再生 180/1599 green --check byte-identical〔17547B〕"
    "——证据六节 qa/props-persist-R1942.log〔套件双跑+RUNNER tail+矩阵双跑"
    "+census+指纹+git 卫生〕·LF 归一单写者驱动=src/os/evidence_R1942.py"
    "〔R1932..R1941 模板族〕——tech consume 1 reseed 1〔queue_tech_open "
    "10→10：props done −1+ledger effects 特效面读面族 persist 补种 +1〔查"
    "重当日实跑：注册表零 effects-persist 位〔ledger-effects 基础席 7 判"
    "据在册〕+AC-EFP 全仓 git grep rc=1+test_effects.py close 六命中全为"
    "SQL 探针/收尾清理非重启例=真活候选〕·下轮 FIFO 队头=ledger identity "
    "城市身份面 persist〔R1938 补种·最老开项〕〕）")
v_idx = tech.find(done_row_head)
assert v_idx >= 0, "props done row not found"
v_end = tech.find(NL, v_idx)
assert v_end >= 0, "props row has no line end"
tech = tech[:v_end] + done_note + tech[v_end:]
reseed_row = (
    "- [ ] ledger effects 特效面读面族跨重启持久化例窗（R1942 补种·查重前"
    "置已过：注册表 label 全形扫描零 effects-persist 命名位变体〔ledger-"
    "effects 基础席 7 判据在册=套件存在锚〕+套件源面扫描 test_effects.py "
    "close 六命中全为 SQL 探针 conn.close()/收尾清理〔fx.close+led.close "
    "单实例〕非重启例=真活候选·AC-EFP 前缀全仓 git grep 零占用 2026-10-14"
    "〔rc=1〕·persist 例窗族 R1886 起谱系）")
apimarket_head = "- [ ] ledger apimarket 开发者 API 市场读面族跨重启持久化例窗（R1941 补种"
must_count(tech, apimarket_head, 1, "apimarket row head")
idx = tech.find(apimarket_head)
end = tech.find(NL, idx)
if end < 0:
    # apimarket row is the file tail without a trailing EOL
    tech = tech + NL + reseed_row + NL
else:
    tech = tech[:end + len(NL)] + reseed_row + tech[end + len(NL):]
write_txt(P_TECH, tech)
print("tech.md: props done-note + effects reseed ok")

# ------------------------------------------------------------- state.json
P_STATE = "src/os/state.json"
state = read_txt(P_STATE)
SNL = eol_of(state)
must_count(state, '"tick": 1941,', 1, "tick")
state = state.replace('"tick": 1941,', '"tick": 1942,', 1)
tok_anchor = "2026-10-14 R1941 tokens:"
must_count(state, tok_anchor, 1, "R1941 tokens anchor")
close_anchor = SNL + "    ]"
assert state.rstrip().endswith("}"), "state tail not }"
cidx = state.rfind(close_anchor)
assert cidx > state.find(tok_anchor), "log close before tokens anchor"
last_item_end = cidx
prefix = state[:last_item_end]
assert prefix.endswith('"'), "last log item does not end with quote"
round_line = (
    "2026-10-14 R1942 ledger props 道具/装扮经济面读面族跨重启持久化例窗"
    "交付轮（P2 tech FIFO=R1941 收账指针·轮计分 2=可跑实物）：五静面——"
    "GORD gord_new_rows=0·DEC 行基线 309 持平零新·LEDGER atbd=0·ORD 持平"
    "·BENCH 当日 10-14·QA 当日证据在盘零重跑·HB lag=0·TREE clean——判据 "
    "AC-PSP1..PSP7 预注册先于代码〔tech.md 认领行在册·本行即册〕：同轮勘"
    "正两枚=套件探针取证口径 bug 非产品缺陷〔①bad-ref 探针缺省 count=0 撞"
    "产品验证序 count≥1 先检门→补 count=1 才达 ref 门②冻结比对误含 "
    "count_credits 切片→改 provenance 五键集排除 count_credits·R1776 取"
    "证口径两修同族先例·首跑 5/7 两败→修后全绿〕——套件 test_props_"
    "persist.py SUITE 7/7+双跑 stdout 逐字节同一 sha16 748340e88482cdb8："
    "三实例世界真产品径〔①锚世界=四购买谱〔alice hat_gold@15+jetpack "
    "count=3@20+bob flare count=2@10〔consume→1〕+carol scarf_silk@12〕"
    "各绑真 spend tx〔SQL cross type=spend+debit 4/4〕+四余额 "
    "265/490/388/18857+表计数 inv=4/spend-tx=4②close→reopen 读面电池"
    "逐字节==关前〔派生面零内存态漂移〕③八门探针跨重启全拒同码+计数冻结"
    "〔含 carol 超预算 E_NEGATIVE_BALANCE 零扣费零 grant〕④真径续写=carol "
    "lantern count=4 新真 spend tx+alice jetpack consume 2→rebuy 1〔stack "
    "3→1→2〕+bob flare consume 1→rebuy 3〔stack 1→0→3〕→零缓存重算〔四"
    "余额 245/480/363/18912+inv 4→5/spend-tx 4→7〕⑤锚行 provenance 五键"
    "逐字节冻结跨重启×续写〔stack 只 UPDATE count_credits=bound_spend_tx/"
    "granted_utc 恒绑首购〕+dup 门 E_PROP_DUP 零扣费⑥纯读律双读同一⑦实"
    "例③==②终态+config sha 零改动+纯 ASCII+零网络+tmp 仓外〕——RUNNER "
    "PASS 180/180 判据 1592→1599 controls 7/7 282.3s=qa/reconcile-all-"
    "R1942.log〔SUITES 179→180·census DRIFT-CLEAN flags=0·指纹 CLEAN "
    "domains=5〕+矩阵再生 180/1599 green --check byte-identical〔17547B〕"
    "——证据六节 qa/props-persist-R1942.log·驱动=src/os/evidence_R1942.py"
    "〔R1932..R1941 模板族〕——tech consume 1 reseed 1〔queue_tech_open "
    "10→10：props done −1+ledger effects 特效面 persist 补种 +1〔查重当日"
    "实跑：注册表零 effects-persist 位+AC-EFP git grep rc=1+test_effects.py "
    "close 六命中全为清理非重启例=真活候选〕·下轮 FIFO 队头=ledger "
    "identity 城市身份面 persist〔R1938 补种·最老开项〕〕——收账后水位预"
    "测 ~79.6KB 越 78500B 线=fold R510 下轮轮首首测裁定兑现〔R1939 承传"
    "注记先例·开窗序=产品件先于 fold〕〕")
tokens_line = (
    "2026-10-14 R1942 tokens: local=unmeasured api=0 api_reason=纯本地进程件"
    "（五静扫描+套件双跑+RUNNER 全量回归+矩阵+census+指纹+收账手术全本地"
    "跑·零外部 API 触点·三问门未涉及）")
new_block = ("," + SNL + '                "' + round_line + '",' + SNL
             + '                "' + tokens_line + '"')
state = prefix + new_block + state[last_item_end:]
parsed = json.loads(state.encode("utf-8").decode("utf-8"))
assert parsed["tick"] == 1942
assert len(parsed["log"]) >= 2
assert parsed["log"][-2].startswith("2026-10-14 R1942 ledger props")
assert parsed["log"][-1].startswith("2026-10-14 R1942 tokens:")
write_txt(P_STATE, state)
print("state.json: tick 1942, +2 log lines,", len(state.encode("utf-8")),
      "bytes")

# ------------------------------------------------------------- heartbeat
P_HB = "heartbeat.txt"
hb = read_txt(P_HB)
HNL = eol_of(hb)
now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
hb_row = ("%s | BigDomain OSLoop alive | tick 1942 | R1942: ledger "
          "props cross-restart persist suite 7/7 double-run "
          "byte-identical (sha16 748340e88482cdb8) + RUNNER 180/180 "
          "criteria 1592->1599 (qa/reconcile-all-R1942.log) + matrix "
          "180/1599 --check identical (17547B) + census DRIFT-CLEAN + "
          "fingerprint CLEAN [via BigDomain-OSLoop]") % now
if not hb.endswith(HNL):
    hb += HNL
hb += hb_row + HNL
write_txt(P_HB, hb)
print("heartbeat row appended")

# ---------------------------------------------------------------- export
sys.path.insert(0, BASE)
import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1942, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = (
    "R1942：道具/装扮经济面（props）做了「关服务重开、库存与余额全复原、"
    "八道闸照常拦截、重启后新购物照样绑定真实扣款流水、重复购买照拒」的"
    "跨重启验证；总回归 180 套件全绿")
export_obj["ceo_face"]["latest_artifact"] = (
    "src/sandbox/ledger/test_props_persist.py + qa/props-persist-"
    "R1942.log + qa/reconcile-all-R1942.log，2026-10-14·180 套件 1599 判"
    "据 green·新增 ledger-props-persist·道具装扮读面族跨重启持久化例窗")
export_obj["ceo_face"]["next_milestone"] = (
    "下轮 R1943：tech 队列 FIFO=ledger identity 城市身份面读面族 persist "
    "认领（R1938 补种·最老开项）")
res_row = [
    "R1942",
    ("R1942 ledger props cross-restart persistence suite 7/7 (P2 "
     "tech FIFO head = the R1941 closeout pointer; criteria "
     "AC-PSP1..PSP7 pre-registered in tech.md before code, with two "
     "same-round suite-side probe-scope errata honestly noted: the "
     "bad-ref probe needed count=1 to actually reach the ref gate "
     "because the product validation order checks count>=1 before "
     "the ref, and the freeze comparison wrongly sliced "
     "count_credits into the provenance key set - fixed to the "
     "five provenance keys excluding count_credits; first run 5/7 "
     "-> fixed -> green; R1776 probe-scope precedent family). "
     "Double-run stdout byte-identical sha16 748340e88482cdb8. "
     "Three-instance world on the real product path (Ledger + "
     "PropsFace, props_inventory single table WAL, zero schema "
     "touch = fingerprint sentinel CLEAN domains=5): anchor (four "
     "purchase spectrum alice hat_gold@15 + jetpack count=3@20 + "
     "bob flare count=2@10 with consume to 1 + carol scarf_silk@12, "
     "each bound to a real spend tx with SQL cross type=spend + "
     "debit leg 4/4; balances 265/490/388/18857; counts inv=4 "
     "spend-tx=4) -> close/reopen byte-identical battery replay "
     "(inventory replays stored bound_spend_tx/count_credits, "
     "balance replays ledger_entries = zero in-memory drift) -> "
     "eight restart-surviving gate probes all-reject same codes "
     "with frozen counts (cosmetic-consume, over-consume, "
     "unknown-item, held-kind drift, unknown-kind, bad-ref, "
     "count=0, plus carol over-budget E_NEGATIVE_BALANCE zero "
     "charge zero grant) -> real-path continuation (carol new "
     "lantern count=4 bound to a new real spend tx; alice jetpack "
     "consume 2 then stack re-buy to 2; bob flare consume to 0 "
     "then stack re-buy to 3; zero-cache recompute with balances "
     "245/480/363/18912 and counts inv 4->5 spend-tx 4->7) -> "
     "frozen provenance faces (anchor rows' inv_id/account/item/"
     "kind/bound_spend_tx/granted_utc byte-frozen across restart x "
     "continuation; stack rows move count_credits only via product "
     "verbs = the stack path only UPDATEs count_credits, "
     "provenance stays first-purchase-bound) + dup gate "
     "E_PROP_DUP zero charge -> pure-read law -> third-instance "
     "stability + config sha unchanged + pure ASCII + zero network "
     "imports + world tmp outside repo. RUNNER PASS 180/180 "
     "criteria 1592->1599 controls 7/7 282.3s = qa/reconcile-all-"
     "R1942.log (ledger-props-persist seat; census DRIFT-CLEAN "
     "flags=0 files=1371 tee=869 baselined=502; fingerprint CLEAN "
     "domains=5); matrix 180/1599 green --check byte-identical "
     "(17547 bytes); evidence six-section qa/props-persist-"
     "R1942.log via src/os/evidence_R1942.py; tech consume 1 "
     "reseed 1 (effects persist seeded with same-day dedup scans: "
     "registry zero effects-persist seat + AC-EFP git-grep rc=1 + "
     "base-suite close hits all SQL-probe/cleanup non-restart = "
     "true-activity candidate; next FIFO head = ledger identity "
     "persist; post-closeout watermark ~79.6KB over the 78500B "
     "line = fold R510 adjudication due at next round start).")]
export_obj["results"].insert(0, res_row)
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per BD-PROP-001"
                " caliber (check_export_consistency.recompute)")
export_obj["self_drive"] = sd
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("export refreshed: queues=%d/%d/%d tick=%d"
      % (derived["queue_main_open"], derived["queue_tech_open"],
         derived["queue_explore_open"], state_obj["tick"]))
print("R1942 closeout complete")
