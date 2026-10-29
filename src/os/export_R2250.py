# export_R2250.py - refresh docs/status-export.json for R2250 without
# re-serialising unrelated bytes. The self_drive block is taken from the
# checker's own recompute() so the derived face cannot drift from the live
# state, and the three ceo_face lines plus export_ts/do are edited line by
# line. New in R2250: ceo_face publishes next_milestone_due, so the
# freshness gate judges the 48h window instead of reporting it unknown.
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_export_consistency as cec  # noqa: E402

EXPORT = os.path.join(ROOT, "docs", "status-export.json")

TS = "2026-10-29T11:45:00+08:00"
DUE = "2026-10-30T11:45:00+08:00"

DO = ("product window R2250: the CEO-visible face gets its time axis judged "
      "(24h age gate, 48h milestone window, honest unknown when no due stamp "
      "is published), suite 6/6 double-run byte-identical, five adjacent os "
      "suites green, consistency checker re-run green")

CURRENT = (
    "R2250 產品輪：CEO 可見面補上「時間」這條軸。原本 docs/status-export.json 只被檢查形狀與派生"
    "（三行非空、export_ts 可解析、self_drive 重算、tick 行），於是「形狀完美但已是兩天前的面」和"
    "「里程碑報到三週後」都算綠。新件 src/os/export_freshness.py 只判時間：導出面齡對 24h 新鮮閘、"
    "公告里程碑對 48h 窗，時鐘由調用方注入故可重現；四種判決窮盡（FRESH／STALE-FACE／"
    "STALE-WINDOW／UNVERIFIABLE-WINDOW），未公布到期戳記一律報「不可判定」而非假綠（exit 4）；"
    "無 UTC 偏移的時間戳直接拒絕（E_EXP_BAD_TS）而非假設本地時區。形狀與派生仍歸 "
    "check_export_consistency，故非重複造輪——改動後一致性檢查重跑 exit 0。本窗導出面開始公布 "
    "next_milestone_due，閘因此由「不可判定」轉為 FRESH。"
)

LATEST = (
    "src/os/export_freshness.py（時間閘本體，四判決＋時鐘注入＋到期戳記未知不假綠）＋ "
    "src/os/test_export_freshness.py（AC-EXP1..AC-EXP6 判據套件 6/6）＋ "
    "qa/export-freshness-R2250-a.log / -b.log（單寫者 utf-8 LF 雙跑，466B 各，判據行 sha16 "
    "6B9DC44593508471 逐位元組同一）＋ qa/regression-R2250.log（五鄰套件全綠）；時間戳 2026-10-29 "
    "11:4x"
)

NEXT = (
    "R2251 先還驗證債：在已提交樹上跑全量電池＋矩陣再生（state/debt.md 已登記 first=yes；"
    "R2168 混樹律＝電池窗內不改產品代碼），預計套件 428→429、判據 3546→3552（＝本窗 "
    "os-export-freshness(6) 入冊，須以實測對位不得沿用推算）；窗 ≤48h"
)

LAST = ("src/os/export_freshness.py + qa/export-freshness-R2250-a.log（R2250，2026-10-29 11:4x）；"
        "證據雙跑同一 sha16 6B9DC44593508471")

OUT_TITLE = ("export freshness gate: the CEO-visible face is now judged on time "
             "as well as shape (R2250)")

OUT_BODY = (
    "R2250: docs/status-export.json is the only surface the CEO reads, and the "
    "round book requires three lines with the next milestone inside 48h, but every "
    "existing check was about shape and derivation - a perfectly shaped face two "
    "days old passed, and so did a milestone announced three weeks out. "
    "src/os/export_freshness.py measures only the missing axis: the age of the face "
    "against a 24h freshness gate and the announced milestone against a 48h window, "
    "with the clock injected by the caller so a reading is reproducible and testable. "
    "Verdicts are four and exhaustive (FRESH / STALE-FACE / STALE-WINDOW / "
    "UNVERIFIABLE-WINDOW); a face that publishes no next_milestone_due reads as an "
    "honest unknown on its own exit code (4) rather than as a fabricated pass, and a "
    "stamp without a UTC offset is refused (E_EXP_BAD_TS) instead of being assumed "
    "local, because the face is written by different writers across the day. Shape "
    "and derivation stay with check_export_consistency, which was re-run green after "
    "the change, so this window added no second wheel. Evidence: SUITE PASS 6/6 "
    "double-run byte-identical criterion sha16 6B9DC44593508471 "
    "(qa/export-freshness-R2250-a.log / -b.log, 466B each, single writer utf-8 LF), five "
    "adjacent os suites green (qa/regression-R2250.log, 4878B), wired "
    "os-export-freshness(6). The live reading at the R2249 face was "
    "verdict=UNVERIFIABLE-WINDOW age=0.3h; this window's refresh publishes "
    "next_milestone_due so the gate now reads FRESH."
)

RESULT_BODY = (
    "product window on the P2 tech head: the export face's time axis as a reading - "
    "24h age gate, 48h milestone window, honest unknown on a missing due stamp, "
    "refused naive stamps, four exhaustive verdicts, injected clock, CLI 0/2/3/4/5 and "
    "a pinned --json key order, wired into the runner and proved by a byte-identical "
    "double run plus five adjacent suites; the battery and the matrix regeneration are "
    "the R2251 first item and are registered in state/debt.md"
)


def replace_line(text, key, value):
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines)
            if line.strip().startswith(json.dumps(key) + ": ")]
    if len(hits) != 1:
        raise SystemExit("line anchor not unique: %s (%d)" % (key, len(hits)))
    line = lines[hits[0]]
    indent = line[:len(line) - len(line.lstrip())]
    tail_comma = line.rstrip().endswith(",")
    lines[hits[0]] = (indent + json.dumps(key) + ": "
                      + json.dumps(value, ensure_ascii=False)
                      + ("," if tail_comma else ""))
    return "\n".join(lines)


def main():
    with open(EXPORT, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    if raw.count("\r\n") != raw.count("\n"):
        raise SystemExit("mixed line endings - refusing to edit")
    text = raw.replace("\r\n", "\n")
    derived, state, export, pat = cec.recompute()

    text = replace_line(text, "export_ts", TS)
    text = replace_line(text, "do", DO)
    for key, value in (("current", CURRENT), ("latest_artifact", LATEST),
                       ("next_milestone", NEXT), ("last_artifact", LAST)):
        text = replace_line(text, key, value)

    # publish the due stamp right after the milestone line
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines)
            if line.strip().startswith('"next_milestone": ')]
    if len(hits) != 1:
        raise SystemExit("next_milestone anchor not unique (%d)" % len(hits))
    anchor = lines[hits[0]]
    indent = anchor[:len(anchor) - len(anchor.lstrip())]
    if not anchor.rstrip().endswith(","):
        lines[hits[0]] = anchor.rstrip() + ","
    lines.insert(hits[0] + 1, indent + '"next_milestone_due": '
                 + json.dumps(DUE, ensure_ascii=False) + ",")
    text = "\n".join(lines)

    outs_row = ("    [\n      %s,\n      \"on\",\n      %s\n    ],\n"
                % (json.dumps(OUT_TITLE, ensure_ascii=False),
                   json.dumps(OUT_BODY, ensure_ascii=False)))
    marker = '  "outs": [\n'
    if text.count(marker) != 1:
        raise SystemExit("outs anchor not unique")
    text = text.replace(marker, marker + outs_row, 1)

    results_row = ("    [\n      \"R2250\",\n      %s\n    ],\n"
                   % json.dumps(RESULT_BODY, ensure_ascii=False))
    marker = '  "results": [\n'
    if text.count(marker) != 1:
        raise SystemExit("results anchor not unique")
    text = text.replace(marker, marker + results_row, 1)

    label = pat["tick_row_label"]
    needle = '      "%s",\n      "%s"\n' % (str(state["tick"] - 1), label)
    if text.count(needle) != 1:
        raise SystemExit("tick row anchor not unique (%d)" % text.count(needle))
    text = text.replace(needle, '      "%d",\n      "%s"\n'
                        % (state["tick"], label), 1)

    for key, want in sorted(derived.items()):
        text = replace_line(text, key, want)

    data = json.loads(text)
    assert data["export_ts"] == TS
    assert data["ceo_face"]["next_milestone_due"] == DUE
    assert data["self_drive"] == dict(data["self_drive"], **derived)
    with open(EXPORT, "w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("\n", "\r\n"))
    print("EXPORT rows=%d outs=%d tick_row=%s derived=%d bytes=%d"
          % (len(data["results"]), len(data["outs"]), state["tick"],
             len(derived), len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())