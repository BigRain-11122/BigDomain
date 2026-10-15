# closeout_R1991.py - R1991 (commit-debt takeover closeout) state,
# heartbeat and export closeout. Round line kept compact by design:
# gauge 76587B + ~1.4KB < 78500B cap, so no fold window is needed
# this round (honest size-conscious closeout). Pure ASCII source;
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
    "2026-10-15 R1991（崩轮接管收口第 27 案=R1990 commit-debt 接管收口"
    "〔R1924/R1988 先例族·R1990 于 12:0x 完成全部 closeout 状态面后崩于 "
    "commit 步〕：接管验证链全绿=套件双跑逐字节同一 sha16 "
    "dca908c94dadfc5a==原轮宣称+矩阵 218/1870 --check+census "
    "DRIFT-CLEAN+指纹 CLEAN+profile 基线 --check〔qa/"
    "takeover-verify-R1990-2.log VERDICT PASS〕→定向 23 文件 commit "
    "fa8f0b3e+push sha 双验 328bab17→fa8f0b3e=R1990 产品面"
    "（stats_board_dual persist AC-SSDP1..7+RUNNER 218/218 保全证据）"
    "全量上链·score 1 commit-debt 收口〔R1924 口径〕——基线后 GORD 积压 "
    "22 行补扫裁定〔R1987 重锚后 ORD 面年式正则对新格式行假阴性·"
    "R1988..R1990 三轮 probe 同盲面·本窗 origin 直读补齐〕：零 "
    "@BigDomain 派工面·回执五笔=O-20261014-2250 巡视舰队令（本司域席位 "
    "LIVE·digest/旗班在役·知悉确认）+O-20261015-1030 Agent 业务法 v1"
    "（P0 发现>P1 创新>P2 审查=本 loop 五静+拉活序天然同构·知悉执法）"
    "+O-20261015-1040 24h 全链贯通审计案 C-20261015-01（本 loop=L0 "
    "执行层被审面·standing by·知悉）+O-20261015-1055 MV 全速+金融 "
    "CPU 排满令（派工面=BigStream/BigMoney/bm-c·本司轻量全本地零冲突·"
    "知悉）+O-20261015-1200 云端 token 严管令=D-20261015-03/"
    "C-20261015-02 立法收口（正典=token-economy v3.0 §十·本司轮账 "
    "api=0 全本地=天然合规·例外面白名单六类备查·知悉）——基线重锚三件="
    "last_order→2026-10-15 12:0x+GORD tbl 459→422（重组缩容·零新增 "
    "BD 行）+DEC rows 266→336+dec tokens +2——explore open=10 守恒"
    "（本轮预算全额用于接管收口·新拉活延下轮）"
)
L2 = (
    "R1991 tokens: local=~350K api=0 api_reason=taken-over commit-debt "
    "closeout round all local (five-silence scan + origin orders "
    "backfill triage + takeover verify battery suite x2 / matrix / "
    "census / fingerprint / profile + directed commit + push + "
    "closeout), zero cloud calls"
)
HB = (
    "2026-10-15 12:2x +08:00 | BigDomain OSLoop alive | tick 1991 | "
    "R1991: R1990 commit-debt takeover closeout (27th case) - orphan "
    "payload verified (suite 7/7 x2 sha16 dca908c94dadfc5a matches "
    "claimed + matrix 218/1870 --check + census DRIFT-CLEAN + "
    "fingerprint CLEAN + profile --check, VERDICT PASS qa/"
    "takeover-verify-R1990-2.log), directed 23-file commit fa8f0b3e "
    "push sha-verified 328bab17->fa8f0b3e; post-baseline GORD "
    "backfill 22 rows triaged zero @BigDomain dispatch faces, 5 "
    "receipts (O-20261014-2250 / O-20261015-1030 / -1040 / -1055 / "
    "-1200 + D-20261015-03); baselines re-anchored (orders 10-15 "
    "12:0x, gord 422, dec 336, tokens +2); explore open=10 conserved "
    "[via BigDomain-OSLoop]"
)
CEO_CUR = (
    "R1991: R1990 commit-debt takeover closeout (27th takeover case). "
    "The crashed round R1990 had finished its whole closeout state "
    "face but died before commit; the taker re-verified the orphan "
    "payload chain (suite 7/7 double-run byte-identical sha16 "
    "dca908c94dadfc5a matching the claimed value, matrix 218/1870 "
    "--check, census DRIFT-CLEAN, fingerprint CLEAN, runner profile "
    "--check; VERDICT PASS qa/takeover-verify-R1990-2.log) and put "
    "the 23-file payload on-chain (commit fa8f0b3e, push "
    "sha-verified): R1990's stats_board_dual cross-restart "
    "persistence product (AC-SSDP1..7, RUNNER 218/218 preserved "
    "green) is fully delivered. Post-baseline group-orders backfill "
    "triage (22 rows, zero BigDomain dispatch faces; receipts: "
    "O-20261014-2250 patrol-fleet domain seat live, O-20261015-1030 "
    "agent business law v1, O-20261015-1040 24h full-chain audit "
    "case C-20261015-01, O-20261015-1055 MV/finance dispatch to "
    "other houses, O-20261015-1200 cloud token strict law "
    "D-20261015-03 - our loop runs all-local api=0, compliant)."
)
CEO_ART = (
    "qa/takeover-verify-R1990-2.log (VERDICT PASS) + commit fa8f0b3e "
    "(23 files: R1990 stats_board_dual persist product on-chain)"
)
CEO_NEXT = (
    "P3 explore FIFO next head: stats_board cap-window cross-restart "
    "persistence seed (reseeded R1990); with the takeover chain "
    "live, next product round within 48h."
)
RES = (
    "R1991: R1990 commit-debt takeover closeout (27th case). Taker "
    "re-verified the orphan payload per R1988 precedent - suite 7/7 "
    "x2 byte-identical sha16 dca908c94dadfc5a (matches claimed), "
    "matrix 218/1870 --check, census DRIFT-CLEAN, fingerprint "
    "CLEAN, profile --check, VERDICT PASS (qa/"
    "takeover-verify-R1990-2.log) - then directed 23-file commit "
    "fa8f0b3e + push sha-verified 328bab17->fa8f0b3e: R1990's "
    "stats_board_dual cross-restart persistence product (AC-SSDP1..7, "
    "RUNNER 218/218 log preserved green) fully on-chain. "
    "Post-baseline GORD backfill (22 rows after the 10-14 16:2x "
    "anchor; ORD-face year-format regex blind spot honestly noted, "
    "origin direct-read filled the gap): zero BigDomain dispatch "
    "faces; five receipts logged (O-20261014-2250, O-20261015-1030, "
    "-1040, -1055, -1200 + D-20261015-03/C-20261015-02 - loop "
    "all-local api=0 compliant, canon token-economy v3.0 s10). "
    "Baselines re-anchored: last_order 2026-10-15 12:0x, GORD tbl "
    "459->422 (reorg shrink, zero new BD rows), DEC rows 266->336, "
    "dec tokens +2. Score 1 (commit-debt closeout, R1924 caliber)."
)


def main():
    st = json.loads(io.open(P_STATE, encoding="utf-8").read())
    if st["tick"] != 1990:
        print("ABORT: unexpected tick=%s" % st["tick"])
        return 2
    st["tick"] = 1991
    st["last_order"] = "2026-10-15 12:0x"
    st["last_decision_rows"] = 336
    st["last_gord_tbl_rows"] = 422
    toks = st["last_dec_tokens"]
    for tkn in ("D-20261015-03", "C-20261015-02"):
        if tkn not in toks:
            st["last_dec_tokens"] = toks + "," + tkn
            toks = st["last_dec_tokens"]
    st["log"].append(L1)
    st["log"].append(L2)
    body = json.dumps(st, ensure_ascii=False, indent=4) + "\n"
    sz = len(body.encode("utf-8"))
    if sz >= 78500:
        print("ABORT: state over the line: %d" % sz)
        return 2
    io.open(P_STATE, "w", encoding="utf-8", newline="").write(body)
    print("state.json OK: tick=1991 bytes=%d (cap 78500)" % sz)

    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + HB + "\r\n")
    print("heartbeat.txt OK: R1991 line appended")

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
    tick_row = ["1991", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2 and r[1] != label]
    new_results = [["R1991", RES]] + rrows[:38] + [tick_row]
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
    print("R1991 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
