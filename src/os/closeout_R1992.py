# closeout_R1992.py - R1992 (stats_board cap-window cross-restart
# persistence product round) closeout. State.json gets a BYTE-
# SURGICAL append this round (CRLF + 16-space indent preserved, the
# R1991 full-json.dumps-rewrite layout disease is fixed at the
# source: no whole-file re-serialization). Pure ASCII source;
# Chinese content only in the JSON data being written.
import io
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_HEART = os.path.join(ROOT, "heartbeat.txt")

L1 = (
    "2026-10-15 R1992（P3 explore FIFO 队头=统计榜截断帽窗跨重启持久化"
    "例窗交付轮（stats_board cap persist·AC-SSTP1..SSTP7 判据预注册先于"
    "代码〔explore.md 行内册·AC-SSTP 前缀全仓 git grep 零占用〕：R1990 "
    "同形世界 pre-close 帽窗读族 1/2/50 三帽+缺省全读〔信封键集钉死+缺"
    "省全读==直读+帽读==决序尾窗切片+镜像 SQL 第三径+total 诚实全量〕/"
    "全栈 close（sh→led）→同 db/cfg/sh 路径 rebuild 帽窗读族+缺省全读"
    "逐字节同一〔读时派生面跨重启零漂移〕/重启后新注册 zeta-win〔缺省全"
    "读 5→6 零事件诚实零行·帽读 total 5→6·帽（2）尾窗滑移 omega,delta"
    "→delta,zeta·五旧行字节冻结〕/重启后新收置零缓存重算〔alpha "
    "{p3,r2,dn1} 决序升首·净流恒等全行·未触行冻结〕/第三实例三开==实例"
    "②终态逐字节同一+表计数恒定/纯读律三表恒定+方法段零写语句零 RNG/卫生"
    "产品三件 sha 双证零改动——SUITE 7/7 首跑全绿+双跑逐字节同一 sha16 "
    "dfe5979260a651bf+RUNNER PASS 219/219 判据 1870→1877 controls 7/7 "
    "218.0s+矩阵再生 219/1877 green --check byte-identical+census "
    "DRIFT-CLEAN files=1483+指纹 CLEAN domains=5+runner_profile 基线重"
    "锚 R1992——fold R530 收账前置兑现〔轮首 gauge 78444B 必越线裁定·"
    "tail-6 窗 10523B 压 1 滚窗行 4771B·23 token 机械提取全字面嵌零丢失"
    " gen530·archive §R1992 节 6 行 verbatim+preop logs/state-preop-"
    "R1992.bak·post==predicted 72787B margin 5713B〕+R1991 closeout "
    "json.dump 全量重写布局病当窗检出〔LF+8 空格=R1710 病复发·诚实注〕"
    "→eol --fix+--fix-indent 工具链正法双修全绿〔content_eq/json_eq 双"
    "证·CRLF 30+缩进 16 空格 20/20〕+本轮 closeout 改字节外科追加〔禁 "
    "json.dump 全量重写纪律·布局病源头根治〕——explore 消费 1 补种 1 守"
    "恒 open=10〔统计榜零注册边界世界跨重启例窗种子入列〕·score 2 产品"
    "件交付）"
)
L2 = (
    "R1992 tokens: local=~900K api=0 api_reason=full product round "
    "all local (five-silence probe + queue pull + fold R530 gen/"
    "execute + EOL canonical repair + claim pre-registration + "
    "suite authoring + first-run + double-run + full RUNNER + "
    "matrix/census/fingerprint/profile re-anchor + byte-surgical "
    "closeout), zero cloud calls"
)
HB = (
    "2026-10-15 15:1x +08:00 | BigDomain OSLoop alive | tick 1992 | "
    "R1992: stats_board cap-window cross-restart persistence "
    "product round (explore FIFO head consume-1) - suite 7/7 x2 "
    "byte-identical sha16 dfe5979260a651bf, RUNNER PASS 219/219 "
    "criteria 1870->1877 controls 7/7 218.0s, matrix 219/1877 "
    "--check, census DRIFT-CLEAN, fingerprint CLEAN domains=5, "
    "profile re-anchored; fold R530 pre-closeout honored (tail-6 "
    "window 10523B -> 4771B rolling line, 23 tokens zero-loss, "
    "post==predicted 72787B); R1991 json.dumps layout drift caught "
    "at the fold gate and canonically repaired (eol --fix + "
    "--fix-indent, json_eq verified); this closeout is "
    "byte-surgical (no full rewrite) [via BigDomain-OSLoop]"
)
CEO_CUR = (
    "R1992: shipped a new product suite - the showcase stats "
    "cap-window read (tail slice + honest overflow block) is now "
    "pinned to survive full instance restarts byte-identically "
    "(7 pre-registered criteria all green; suite double-run "
    "byte-identical; full regression 219/219 suites green, "
    "criteria 1870->1877)."
)
CEO_ART = (
    "qa/showcase-statscappersist-R1992.log + qa/reconcile-all-"
    "R1992.log (RUNNER PASS 219/219) + src/sandbox/ledger/"
    "test_showcase_statscappersist.py"
)
CEO_NEXT = (
    "Next explore FIFO head within 48h: lobby-suite stdout "
    "determinism hardening seed (rtt/port/uuid non-determinism "
    "found in R1876); daily-profile observation-window ruling "
    "gates open 2026-10-16 governance window."
)
RES = (
    "R1992: stats_board cap-window cross-restart persistence "
    "example window delivered (P3 explore FIFO head, consume-1/"
    "reseed-1). AC-SSTP1..7 pre-registered in the claim line "
    "before code: R1990-shaped world pre-close cap family "
    "{1,2,50} + default full read (envelope key-sets pinned, "
    "capped==tail slices, mirror-SQL third path, honest "
    "overflow); full-stack close -> same-db/cfg rebuild read "
    "family byte-identical (derived purity across restart); "
    "post-restart new registration -> total 5->6 continuation "
    "with tail slide [omega,delta]->[delta,zeta] and five old "
    "rows frozen; post-restart activity -> zero-cache recompute "
    "(alpha {p3,r2,dn1} first, netflow identity, untouched rows "
    "frozen); third instance == instance-2 final state "
    "byte-identical; pure-read law + hygiene all green. Suite "
    "7/7 first run, double-run byte-identical sha16 "
    "dfe5979260a651bf; RUNNER PASS 219/219 criteria 1870->1877 "
    "controls 7/7 218.0s (qa/reconcile-all-R1992.log); matrix "
    "regen 219/1877 --check byte-identical; census DRIFT-CLEAN "
    "(1483 files); fingerprint CLEAN domains=5; runner profile "
    "re-anchored. fold R530 honored pre-closeout (state 78444B "
    "-> tail-6 window 10523B folded to one 4771B rolling line, "
    "23 tokens mechanically embedded zero-loss, archive "
    "verbatim + preop backup, post==predicted 72787B). R1991 "
    "closeout layout drift (bare-LF + 8-space from a full "
    "json.dumps rewrite, the R1710 disease) caught at the fold "
    "gate and repaired canonically (eol --fix + --fix-indent, "
    "content/json equivalence verified); this round's closeout "
    "is byte-surgical, fixing the disease at the source. "
    "explore open=10 conserved (reseed: stats_board "
    "zero-registration boundary-world cross-restart seed). "
    "Score 2 (runnable/verifiable product artifact)."
)


def json_escape(text):
    return (text
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
            .replace("'", "\\u0027"))


def main():
    # -- state.json byte-surgical append (CRLF + 16-space) ------
    raw = io.open(P_STATE, "rb").read()
    assert raw.count(b'"tick": 1991,') == 1, "tick anchor not unique"
    assert raw.endswith(b"\r\n"), "state must end with CRLF"
    lines = raw.split(b"\r\n")
    assert lines[-1] == b"" and lines[-2] == b"}", \
        "unexpected tail layout"
    assert lines[-3] == b"    ]", "unexpected log closer"
    last_item = lines[-4]
    assert last_item.startswith(b'                "'), \
        "unexpected last log item indent"
    assert not last_item.endswith(b","), \
        "last log item already comma-terminated"
    item1 = ("                \"" + json_escape(L1) + "\",") \
        .encode("utf-8")
    item2 = ("                \"" + json_escape(L2) + "\"") \
        .encode("utf-8")
    body_lines = (lines[:-4] + [last_item + b",", item1, item2]
                  + [b"    ]", b"}", b""])
    out = b"\r\n".join(body_lines)
    out = out.replace(b'"tick": 1991,', b'"tick": 1992,', 1)
    sz = len(out)
    if sz >= 78500:
        print("ABORT: state over the line: %d" % sz)
        return 2
    io.open(P_STATE, "wb").write(out)
    # verify: reparse + content + layout
    st = json.loads(io.open(P_STATE, encoding="utf-8").read())
    assert st["tick"] == 1992 and len(st["log"]) == 17, \
        "surgery verify failed"
    assert st["log"][-2] == L1 and st["log"][-1] == L2, \
        "content verify failed"
    d = io.open(P_STATE, "rb").read()
    assert d.count(b"\n") == d.count(b"\r\n"), "bare LF leaked"
    print("state.json OK: tick=1992 bytes=%d (cap 78500)" % sz)

    # -- heartbeat.txt ------------------------------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + HB + "\r\n")
    print("heartbeat.txt OK: R1992 line appended")

    # -- status-export.json --------------------------------------
    import check_export_consistency as cec  # noqa: E402
    derived, _state, _exp, pat = cec.recompute()
    exp = json.loads(io.open(P_EXPORT, encoding="utf-8").read())
    exp["export_ts"] = datetime.now().astimezone().isoformat(
        timespec="seconds")
    exp["ceo_face"] = {
        "current": CEO_CUR,
        "latest_artifact": CEO_ART,
        "next_milestone": CEO_NEXT,
    }
    results = exp["results"]
    label = pat["tick_row_label"]
    tick_row = ["1992", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2 and r[1] != label]
    new_results = [["R1992", RES]] + rrows[:38] + [tick_row]
    exp["results"] = new_results
    sd = dict(derived)
    sd["method"] = ("machine-derived from state.json log per "
                    "BD-PROP-001 caliber (check_export_consistency"
                    ".recompute)")
    exp["self_drive"] = sd
    io.open(P_EXPORT, "w", encoding="utf-8", newline="").write(
        json.dumps(exp, ensure_ascii=False, indent=2) + "\n")
    print("status-export.json OK: results=%d self_drive window=%s"
          % (len(new_results), sd.get("window")))
    print("R1992 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
