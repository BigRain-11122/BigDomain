# closeout_R1999.py - R1999 (civic honor competition month-window
# read face) closeout, landed by the 31st-case crashed-round
# takeover session (R1924/R1976/R1990/R1997/R1998 precedent
# family). The predecessor session authored the complete
# closeout payload (closeout_payload_R1999.json) and the takeover
# verification results (takeover_results_R1999.json) before
# crashing; this driver consumes both and lands the remaining
# edits: (1) explore.md claim flip + reseed, (2) state.json
# byte-surgical append (CRLF + 16-space indent preserved, no
# whole-file re-serialization) with the takeover note and the
# post-crash external-face baseline updates (ORD tail 17:0x ->
# 17:2x, GORD table 460 -> 438), (3) tech.md scanner-fix seed row,
# (4) heartbeat line, (5) status-export refresh. Chinese content
# lives in the payload/JSON data; script logic is ASCII.
import io
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_PAYLOAD = os.path.join(HERE, "closeout_payload_R1999.json")
P_RESULTS = os.path.join(HERE, "takeover_results_R1999.json")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

PAY = json.loads(io.open(P_PAYLOAD, encoding="utf-8").read())
RES = json.loads(io.open(P_RESULTS, encoding="utf-8").read())

ORD_NEW_BASE = "2026-10-15 17:2x"
GORD_NEW_ROWS = 438

TAKEOVER_NOTE = (
    u"——31st-case 崩轮接管收口注记：原轮会话完成产品面+全套电池"
    u"〔RUNNER PASS 224/224=qa/reconcile-all-R1999.log L2739·"
    u"VERDICT PASS=L2786〕+fold R534+closeout 载荷后崩于收口落盘前"
    u"〔载荷在盘保全=R1924/R1976/R1990/R1991/R1993/R1994/R1995/"
    u"R1997/R1998 接管先例族〕；接管者亲验=SUITE 复跑 exit=0 归一 "
    u"LF sha256 %(sha)s 锚合原轮双跑〔bytes=%(sbytes)d〕+四电池 "
    u"--check 复跑全绿〔matrix byte-identical %(mbytes)dB+指纹 "
    u"--check exit=0+profile --check exit=0+census 单一已知面方言"
    u"漂移按 R1996/R1998 先例 --update-baseline 合法重锚后 "
    u"DRIFT-CLEAN flags=0〕+takeover follow-up 节就地 append "
    u"VERDICT PASS=qa/reconcile-all-R1999.log 尾；崩轮间隙外景复扫"
    u"=LEDGER/DEC/BENCH/QA 全 PASS·ORD 尾 17:0x→17:2x 新 6 行全 "
    u"MV 域零 BigDomain 执行面=知悉不动作基线更新 17:2x·GORD 表 "
    u"460→438 集团侧自维收缩零 @BigDomain 新行基线同步 438·scan "
    u"ORD 面年份格式解析漂移〔集团台账行迁无年份 MM-DD 格式·"
    u"scanner 读到 2026-09-28 旧行误 FLAG〕如实注·修复单排 tech "
    u"队列〔R1999 接管收账排〕"
) % {
    "sha": RES["suite_sha16"],
    "sbytes": RES["suite_bytes"],
    "mbytes": RES["matrix_bytes"],
}

TOKENS_SUFFIX = (
    " + successor takeover session additional local spend "
    "(post-crash five-silence rescan + suite re-run + four "
    "--check faces + census re-anchor + follow-up append + "
    "closeout edits + directed commit + push), zero cloud calls"
)

HB_SUFFIX = (
    " ; 31st-case crashed-round takeover closeout: successor "
    "session re-verified the suite sha anchor and all four "
    "battery --check faces green (census legally re-anchored "
    "per the R1996/R1998 takeover precedent); post-crash ORD "
    "rescan 17:0x->17:2x, six new rows all MV-domain, zero "
    "BigDomain faces (ack no-action, baseline updated)"
)

CEO_SUFFIX = (
    " Delivered via 31st-case crashed-round takeover closeout: "
    "the successor session re-verified the suite sha anchor and "
    "all four battery --check faces green (census legally "
    "re-anchored per the R1996/R1998 takeover precedent) before "
    "landing the closeout edits; post-crash external rescan "
    "found ORD tail 17:0x -> 17:2x with six new rows all "
    "MV-domain, zero BigDomain faces (ack no-action, baseline "
    "updated)."
)

RES_SUFFIX = (
    " 31st-case crashed-round takeover closeout by the successor "
    "session: suite re-run sha16 %(sha)s anchored byte-for-byte "
    "to the original double-run (bytes=%(sbytes)d); matrix "
    "--check byte-identical %(mbytes)dB; fingerprint --check "
    "green; profile --check green; census single-known-file "
    "dialect drift legally re-anchored (--update-baseline, "
    "R1996/R1998 precedent) then DRIFT-CLEAN flags=0; takeover "
    "follow-up section + VERDICT appended in place to the "
    "battery log. Post-crash external rescan: LEDGER/DEC/BENCH/"
    "QA PASS; ORD tail 17:0x -> 17:2x with six new rows all "
    "MV-domain (zero BigDomain faces, ack no-action, baseline "
    "updated); GORD table 460 -> 438 group-side maintenance "
    "shrink (zero new @BigDomain rows, baseline synced); scan "
    "ORD-face year-format parser drift noted honestly, fix "
    "seeded to the tech queue."
) % {
    "sha": RES["suite_sha16"],
    "sbytes": RES["suite_bytes"],
    "mbytes": RES["matrix_bytes"],
}

TECH_ROW = (
    u"- [ ] scan_five_still ORD 面年份格式解析漂移修复（集团 "
    u"orders.md 台账行已迁 `| 10-15 HH:MMx |` 无年份格式·scanner "
    u"ORD 面年份 regex 读到 2026-09-28 旧行误报 FLAG〔2026-10-15 "
    u"R1999 崩轮接管复扫实锚·人工判读 ORD 实况=17:0x→17:2x 新 6 行"
    u"全 MV 域零 BigDomain 面=知悉不动作〕·修复面=行格式双态兼容"
    u"（带年份/无年份）+基线方向比对·载体 tools/skills/"
    u"bigdomain-loop-scan/scripts/scan_five_still.ps1+src/os/"
    u"scan_five_still.py 双源核对——种子=R1999 接管收账排 tech）"
)


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def json_escape(text):
    return (text
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
            .replace("'", "\\u0027"))


def main():
    # ---------- 1. explore.md claim flip + reseed ---------------
    raw = io.open(P_EXPLORE, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    norm = raw.replace("\r\n", "\n") if crlf else raw
    lines = norm.split("\n")
    marker = u"- [ ] " + PAY["claim_anchor"]
    idx = [i for i, ln in enumerate(lines)
           if ln.startswith(marker)]
    if len(idx) != 1:
        die("explore claim rows found=%d" % len(idx))
    i = idx[0]
    lines[i] = (u"- [x] " + lines[i][6:]
                + PAY["claim_done_note"])
    lines.insert(i + 1, PAY["reseed_row"])
    out_exp = "\n".join(lines)
    if crlf:
        out_exp = out_exp.replace("\n", "\r\n")
    if out_exp.count(u"〔done 2026-10-15 R1999〕") != 1:
        die("explore done-note count=%d"
            % out_exp.count(u"〔done 2026-10-15 R1999〕"))
    if out_exp.count(u"R1999 收账补种") != 1:
        die("explore reseed count=%d"
            % out_exp.count(u"R1999 收账补种"))
    io.open(P_EXPLORE, "w", encoding="utf-8",
            newline="").write(out_exp)
    print("explore.md OK: claim flipped done + reseed landed")

    # ---------- 2. tech.md scanner-fix seed row -----------------
    raw_t = io.open(P_TECH, encoding="utf-8", newline="").read()
    if TECH_ROW in raw_t:
        die("tech seed row already present")
    crlf_t = "\r\n" in raw_t
    sep = "\r\n" if crlf_t else "\n"
    if not raw_t.endswith("\n"):
        raw_t += sep
    out_t = raw_t + TECH_ROW + sep
    io.open(P_TECH, "w", encoding="utf-8",
            newline="").write(out_t)
    print("tech.md OK: scanner-fix seed row appended")

    # ---------- 3. state.json byte-surgical append --------------
    l1 = PAY["state_round_line"] + TAKEOVER_NOTE
    l2 = PAY["state_tokens_line"] + TOKENS_SUFFIX
    raw_s = io.open(P_STATE, "rb").read()
    if raw_s.count(b'"tick": 1998,') != 1:
        die("tick anchor not unique")
    if not raw_s.endswith(b"\r\n"):
        die("state must end with CRLF")
    blines = raw_s.split(b"\r\n")
    if blines[-1] != b"" or blines[-2] != b"}":
        die("unexpected tail layout")
    if blines[-3] != b"    ]":
        die("unexpected log closer")
    last_item = blines[-4]
    if not last_item.startswith(b'                "'):
        die("unexpected last log item indent")
    if last_item.endswith(b","):
        die("last log item already comma-terminated")
    if raw_s.count(b'"last_order": "2026-10-15 17:0x"') != 1:
        die("last_order anchor not unique")
    if raw_s.count(b'"last_gord_tbl_rows": 460') != 1:
        die("gord rows anchor not unique")
    item1 = ("                \""
             + json_escape(l1) + "\",").encode("utf-8")
    item2 = ("                \""
             + json_escape(l2) + "\"").encode("utf-8")
    body = (blines[:-4] + [last_item + b",", item1, item2]
            + [b"    ]", b"}", b""])
    out_s = b"\r\n".join(body)
    out_s = out_s.replace(b'"tick": 1998,',
                         b'"tick": 1999,', 1)
    out_s = out_s.replace(
        b'"last_order": "2026-10-15 17:0x"',
        b'"last_order": "' + ORD_NEW_BASE.encode("ascii")
        + b'"', 1)
    out_s = out_s.replace(
        b'"last_gord_tbl_rows": 460',
        b'"last_gord_tbl_rows": %d' % GORD_NEW_ROWS, 1)
    sz = len(out_s)
    if sz >= 78500:
        die("state over the line: %d" % sz)
    io.open(P_STATE, "wb").write(out_s)
    st = json.loads(io.open(P_STATE, encoding="utf-8").read())
    if st["tick"] != 1999:
        die("surgery verify failed (tick)")
    if st["log"][-2] != l1 or st["log"][-1] != l2:
        die("content verify failed")
    if st["last_order"] != ORD_NEW_BASE:
        die("last_order verify failed")
    if st["last_gord_tbl_rows"] != GORD_NEW_ROWS:
        die("gord rows verify failed")
    d = io.open(P_STATE, "rb").read()
    if d.count(b"\n") != d.count(b"\r\n"):
        die("bare LF leaked")
    print("state.json OK: tick=1999 bytes=%d (cap 78500)"
          % sz)

    # ---------- 4. heartbeat.txt ---------------------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
    hline = stamp + PAY["hb_body"] + HB_SUFFIX + "\r\n"
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + hline)
    print("heartbeat.txt OK: R1999 line appended")

    # ---------- 5. status-export.json ----------------------------
    import check_export_consistency as cec  # noqa: E402
    derived, _state, _exp, pat = cec.recompute()
    exp = json.loads(io.open(P_EXPORT, encoding="utf-8").read())
    exp["export_ts"] = now.astimezone().isoformat(
        timespec="seconds")
    exp["ceo_face"] = {
        "current": PAY["ceo_current"] + CEO_SUFFIX,
        "latest_artifact": PAY["ceo_latest"],
        "next_milestone": PAY["ceo_next"],
    }
    results = exp["results"]
    label = pat["tick_row_label"]
    tick_row = ["1999", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2
             and r[1] != label]
    new_results = (
        [["R1999", PAY["export_results_line_r1999"]
          + RES_SUFFIX]]
        + rrows[:38] + [tick_row])
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
    print("R1999 TAKEOVER CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
