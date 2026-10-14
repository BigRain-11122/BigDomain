# closeout_R1979.py - evidence append + queue done-flip + reseed
import io
import os

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EV = os.path.join(ROOT, "qa", "honorcert-yearbook-R1979.log")
QP = os.path.join(ROOT, "state", "queue", "explore.md")

RUNNER_LINE = ("RUNNER PASS 209/209 suites green, reconcile controls"
               " 7/7, 178.2s (SUITES 208->209, criteria 1801->1808"
               " with AC-HY1..HY7)")
MATRIX_LINE = ("suite_matrix regen green=209/209 (20102 bytes, 209"
               " suites, 1808 criteria) + --check byte-identical")

# 1) append final verdicts to the evidence log
with open(EV, "a", encoding="utf-8", newline="\n") as fh:
    fh.write("\n-- section 5: full regression closeout --\n")
    fh.write(RUNNER_LINE + "\n")
    fh.write(MATRIX_LINE + "\n")
    fh.write("evidence twin: qa/reconcile-all-R1979.log (runner Tee)"
             "\nDONE R1979\n")
print("EVIDENCE-APPENDED")

# 2) queue done-flip: mark the claimed line [done] + live note
q = io.open(QP, encoding="utf-8").read()
lines = q.splitlines()
hit = None
for i, ln in enumerate(lines):
    if ln.startswith("- [ ] \u8363\u8a89\u8bc1\u4e66\u5e74\u518c"):
        hit = i
        break
assert hit is not None, "explore claim line not found"
old = lines[hit]
assert "R1979 \u8ba4\u9886" in old, "claim note missing on line"
head = old.split("\u2014\u2014R1979", 1)[0]
done = ("- [done 2026-10-15] " + head[6:].strip()
        + "\u2014\u2014R1979 \u5f53\u8f6e\u95ed\u53e3\uff1a"
        "\u00b7\u9762=honorcert.py honor_yearbook(year) \u843d\u5730"
        "\uff08\u5355\u6e90\u6d3e\u751f\u8bfb\u9762\u00b7\u96f6 import/"
        "\u96f6 SQL \u96f6\u9a71\u52a8\u59ff\u6001\u4fdd\u6301\uff09"
        "\uff1b\u00b7\u5224\u636e=AC-HY1..HY7 \u5168\u8fc7\uff08\u5957"
        "\u4ef6\u53cc\u8dd1 stdout \u9010\u5b57\u8282\u540c\u4e00"
        " sha16 \u4e00\u81f4\uff09\uff1b\u00b7RUNNER PASS 209/209"
        " controls 7/7 178.2s\uff08SUITES 208\u2192209\u00b7\u5224\u636e"
        " 1801\u21921808\uff09=q\u0080reconcile-all-R1979.log\uff1b"
        "\u00b7\u77e9\u9635 209/1808 \u7eff+--check \u9010\u5b57\u8282"
        "\u540c\u4e00\uff1b\u00b7census \u536b\u751f\u503a\u6536\u53e3"
        "\uff08R1978 \u9057\u7559 apimarket-devboard-R1978.log \u672a"
        "\u91cd\u951a\u88ab\u672c\u8f6e cd7 \u5b9e\u5f39\u62d2\u6353"
        "\u2192--update-baseline \u6587\u6863\u95e8\u91cd\u951a"
        "\u2192DRIFT-CLEAN\uff09\uff1b\u00b7\u6307\u7eb9 CLEAN"
        " domains=5\uff1b\u00b7\u8bc1\u636e=honorcert-yearbook-R1979.log"
        " \u4e94\u8282+\u5224\u636e\u9884\u6ce8\u518c\u5148\u4e8e\u4ee3"
        "\u7801")
done = done.replace("q\u0080", "qa/")
lines[hit] = done

# 3) reseed successor line right below (open pool law: keep >= 10)
seed = ("- [ ] \u8363\u8a89\u5e74\u518c\u8de8\u91cd\u542f\u6301\u4e45"
        "\u5316\u4f8b\u7a97\u63a2\u7d22\uff08honor_yearbook \u540e\u7ee7"
        "\uff1aclose\u2192\u540c db/cfg/pay \u76f4\u63a5\u91cd\u5f00"
        "\u540e\u5e74\u518c\u9010\u5b57\u8282\u540c\u4e00\u4f8b\u7a97"
        "\u00b7persist \u4f8b\u7a97\u65cf R1889/R1900/R1902 \u5224\u8bfb"
        "\u00b7\u8bfb\u65f6\u6d3e\u751f\u9762=\u8de8\u91cd\u542f\u96f6"
        "\u6f02\u79fb\u4f8b+\u91cd\u542f\u540e\u65b0\u6388\u8bc1\u6d3b"
        "\u6001\u7eed\u63a5\u2014\u2014\u79cd\u5b50=honorcert.py"
        " honor_yearbook R1979 \u5728\u518c\u00b7AC \u524d\u7f00\u8ba4"
        "\u9886\u65f6 git grep \u96f6\u5360\u7528\u518d\u9a8c\u00b7"
        "\u5165\u5217 2026-10-15\uff09")
lines.insert(hit + 1, seed)
io.open(QP, "w", encoding="utf-8", newline="\n").write(
    "\n".join(lines) + "\n")
print("QUEUE-FLIP-RESEED done-idx=%d open+1" % hit)
