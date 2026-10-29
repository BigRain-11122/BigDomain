# export_R2249.py - refresh docs/status-export.json for R2249 without
# re-serialising unrelated bytes. The self_drive block is taken from the
# checker's own recompute() so the derived face cannot drift from the
# live state, and the three ceo_face lines plus export_ts/do are edited
# line by line.
import json
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_export_consistency as cec  # noqa: E402

EXPORT = os.path.join(ROOT, "docs", "status-export.json")

TS = "2026-10-29T11:20:00+08:00"

DO = ("verification window R2249: full reconcile battery PASS 428/428 plus "
      "controls 7/7 in 1165.7s with 932/932 tmp worlds reclaimed, then matrix "
      "428 suites / 3546 criteria byte-identical, fingerprint CLEAN, profile "
      "PASS, census DRIFT-CLEAN files=2181")

CURRENT = (
    "R2249 驗證輪：R2248 欠下的全量電池在已提交樹（c6784fca）上跑通——"
    "RUNNER PASS 428/428 套件＋控制 7/7（1165.7s，出生站回收 932/932 世界 326.57 MiB），"
    "四段後續全 PASS：矩陣 428 套件／3546 判據逐位元組回讀同一、指紋五域 CLEAN、"
    "runner profile --daily --check PASS、寫手普查重凍結後 DRIFT-CLEAN files=2181 flags=0。"
    "增量實測非推算＝套件 427→428／判據 3538→3546 恰為 R2248 註冊的 os-debt-register(8)。"
    "本輪零產品代碼改動（0 分驗證輪），下一輪回產品面；佇列地板 main 5/5·tech 10/10·explore 10/10 全 MET。"
)

LATEST = (
    "qa/reconcile-all-R2249.log（全量電池 428/428＋四段後續全 PASS，763410B 起於 RUNNER 收尾，單寫者 utf-8 LF）"
    "＋ src/os/battery_followup_R2249.py（矩陣再生／指紋／profile／普查四段單寫者 runner，VERDICT PASS）"
    "＋ docs/sandbox-suite-matrix.md（428 套件／3546 判據，41753B，逐位元組回讀同一）；時間戳 2026-10-29"
)

NEXT = (
    "R2250 回產品面：認領 state/queue 隊頭（tech 10 條／explore 10 條可領），"
    "判據先寫進佇列行再動代碼，錨檢（git grep -F 對 HEAD 零佔用）先行；"
    "同窗不得再跑電池（R2168 混樹律），窗 ≤48h"
)

LAST = "state/debt.md + src/os/battery_followup_R2249.py（R2249，2026-10-29 11:0x）；證據 qa/reconcile-all-R2249.log"

OUT_TITLE = "full reconcile battery and suite-matrix regeneration re-proven on the committed R2248 tree (R2249)"

OUT_BODY = (
    "R2249: the register row that R2248 opened as its own first item is closed on the "
    "committed tree (c6784fca) with zero product code changed. Full reconcile battery "
    "RUNNER PASS 428/428 suites green plus reconcile controls 7/7 in 1165.7s, birth-site "
    "TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0 (qa/reconcile-all-R2249.log, "
    "763410B at RUNNER close, single-writer utf-8 LF through src/os/battery_stream.py). "
    "Four post-battery sections all PASS through src/os/battery_followup_R2249.py: matrix "
    "428 suites / 3546 criteria read back byte-identical (41753B, green=428/428), "
    "fingerprint CLEAN over 5 domains, runner profile --daily --check PASS, writer census "
    "re-frozen then DRIFT-CLEAN files=2181 tee=1652 baselined=529 flags=0, VERDICT PASS. "
    "Deltas measured against R2247 rather than assumed: 427 -> 428 suites and 3538 -> 3546 "
    "criteria are exactly the R2248 os-debt-register suite (8 criteria) joining the "
    "registry, so that suite is now covered by the whole battery and not only by its own "
    "suite plus neighbours. state.json measured at 37423B against the 78500B waterline, so "
    "no fold is due. Honest score: a 0-point verification window."
)

RESULT_BODY = (
    "verification window on the carried first item: full battery RUNNER PASS 428/428 plus "
    "controls 7/7 in 1165.7s, tmp reclaim 932/932 worlds 326.57 MiB, four follow-up "
    "sections all PASS (matrix 428 suites / 3546 criteria byte-identical, fingerprint CLEAN "
    "5 domains, profile PASS, census DRIFT-CLEAN files=2181 flags=0). Zero product code "
    "changed, so a 0-point window; the register row reconcile-battery-and-matrix is closed "
    "and the only open row left is the elevated-shell S4U item; the floors read main 5/5 "
    "tech 10/10 explore 10/10 FLOOR-MET, so R2250 opens on the product face."
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

    # one new outs row directly under the outs array opener
    outs_row = ("    [\n      %s,\n      \"on\",\n      %s\n    ],\n"
                % (json.dumps(OUT_TITLE, ensure_ascii=False),
                   json.dumps(OUT_BODY, ensure_ascii=False)))
    marker = '  "outs": [\n'
    if text.count(marker) != 1:
        raise SystemExit("outs anchor not unique")
    text = text.replace(marker, marker + outs_row, 1)

    # one new results row, then advance the pinned tick row
    results_row = ("    [\n      \"R2249\",\n      %s\n    ],\n"
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
    assert data["self_drive"] == dict(data["self_drive"], **derived)
    with open(EXPORT, "w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("\n", "\r\n"))
    print("EXPORT rows=%d outs=%d tick_row=%s derived=%d bytes=%d"
          % (len(data["results"]), len(data["outs"]), state["tick"],
             len(derived), len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())