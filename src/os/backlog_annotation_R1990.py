# backlog_annotation_R1990.py - append the R1990 radar-review
# note to the backlog radar standing row (P-2026-10-04-01/02):
# the two window-7 OH candidate lists were reviewed, zero
# @BigDomain strong-fit items, zero claim legal (R1154/R1155
# precedent). Verify-then-write, single anchor, pure ASCII
# source; CJK note inline below rides the data-file exemption
# as a backlog.md md edit (backlog is a md board, CJK allowed).
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
P_BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

ANCHOR = "下窗清单 10-14 21:40 到达续候〕"

NOTE = ("〔R1990 注记：窗 7 新到候选清单两件过目毕="
        "OH-20261013-biglife.md（10-14 10:59 落库·BigLife 第三窗"
        "切片 1·tenacity 自采窗）+OH-20261014-fluxverse.md"
        "（10-14 16:01 落库·城市线切片·程序化城市/URP 性能/NPC/"
        "天气四轴）——零 @BigDomain 强契合件=零认领合法"
        "（R1154/R1155 先例口径·biglife 片内 BigDomain 命中=台账"
        "修复注记非候选·fluxverse 片 BigDomain-hits=0·收益透镜照"
        "判两片均非商业化/增长域契合）·下窗清单到达续候〕")


def main():
    raw = io.open(P_BACKLOG, encoding="utf-8", newline="").read()
    if raw.count(ANCHOR) != 1:
        print("ABORT: anchor count=%d" % raw.count(ANCHOR))
        return 2
    if "R1990 注记" in raw:
        print("ABORT: note already present")
        return 2
    idx = raw.index(ANCHOR) + len(ANCHOR)
    raw2 = raw[:idx] + NOTE + raw[idx:]
    io.open(P_BACKLOG, "w", encoding="utf-8", newline="").write(raw2)
    print("BACKLOG-OK: R1990 radar review note appended")
    return 0


if __name__ == "__main__":
    sys.exit(main())
