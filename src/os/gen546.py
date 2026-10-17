# gen546.py - build the fold R546 rolling-line summary for the
# R2016 closeout-precedent fold. Window = tail-3 (fold R545
# rolling line + R2015 round line + R2015 tokens line): the
# closeout append budget (~2.7KB) exceeds the tail-2 margin, so
# the wider window is required for the gate+reserve check.
# Tokens are mechanically extracted (PAT single-sourced from
# logs_toolkit, zero hand-copying); the summary is written as
# one non-empty utf-8 line. ASCII prints only.
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import logs_toolkit as LT                     # noqa: E402

P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_SUMMARY = os.path.join(HERE, "fold-summary-R546.txt")


def main():
    raw = io.open(P_STATE, "rb").read()
    st = json.loads(raw.decode("utf-8"))
    window = st["log"][-3:]
    winbytes = sum(len(line.encode("utf-8")) for line in window)
    tokens = []
    for line in window:
        for m in LT.PAT.findall(line):
            if m not in tokens:
                tokens.append(m)
    catalog = "|".join(tokens)
    tokcount = len(tokens)
    body = (
        u"2026-10-17 R2016 收账谱滚窗收拢行·fold R546 承 R2016 收账前置裁定兑现"
        u"（本轮收账前 gauge 实测 state 77052B+R2016 round+tokens 收账预算必越"
        u" 78500B 线＝P-2026-09-25-18 第五百四十六刀·开窗序=fold 先于本轮收账"
        u" append（R2015 同位先例）·窗=tail 3：fold R545 滚窗行+R2015 round line"
        u"+R2015 tokens＝3 行 %dB 压 1 滚窗行 kept=0·%d token 全字面嵌零丢失"
        u"（catalog 机械提取零手抄·生成器程序化拼接 gen546·PAT 单源 import"
        u" logs_toolkit）·原文全量保全=archive §R2016 节 3 行 verbatim+preop"
        u" 备份件 logs/state-preop-R2016.bak+git 史）"
        u"——承前滚窗注记：fold R545 滚窗行（承 fold R544 滚窗行〔R2008..R2014"
        u" 谱系〕+R2015 主线接管收口）已折入本行·其 token 域全字面随行（各轮"
        u"详细叙事 live verbatim in archive 对应节）"
        u"——R2015=33rd-case 崩轮接管收口轮详注（showcase stats_board 月份窗"
        u"读面交付：AC-SSM1..SSM7 全过〔套件双跑 sha16 cace415bffe9e141 三方"
        u"恒等·电池 RUNNER PASS 232/232 判据 1976→1983·接管者亲验四电池面〕）"
        u"——R2016 主线见本轮 round line（showcase statsmonth persist 例窗）"
        u"——catalog: %s" % (winbytes, tokcount, catalog)
    )
    if "\n" in body or "\r" in body:
        print("ABORT: summary not single line")
        return 2
    io.open(P_SUMMARY, "w", encoding="utf-8", newline="").write(
        body + "\n")
    print("summary written: bytes=%d tokens=%d winbytes=%d lines=%d"
          % (len(body.encode("utf-8")), tokcount, winbytes,
             len(window)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
