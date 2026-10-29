"""R2244 status-export patch: three-line CEO face + prepended outs/results.

Targeted string surgery so the rest of the export keeps its bytes.
"""

import datetime
import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

now = datetime.datetime.now().replace(microsecond=0).isoformat()

DO = ("product window R2244: the standing-line queue floors became a "
      "reading instead of a mid-window discovery")

CURRENT = (
    "R2244 產品輪：隊列地板（main ≥5 / tech ≥10 / explore ≥10）過去靠窗內 "
    "手數 grep，缺口總在隊列餓死之後才被發現、於是整窗預算只能拿去補種。"
    "本輪交付 src/os/queue_floor.py 只讀量規：一行讀出 "
    "main=1/5 tech=7/10 explore=5/10 verdict=FLOOR-DEBT shortfall=12，"
    "每隊一行明細；行律=列首 `- [ ]` 且方框後需空白（`- [ ]text` 不算行，"
    "首跑套件抓到的是實作、已按預註冊意圖收緊而非放寬判據）；"
    "八種門控標記（[needs-CEO]/blocked on CEO/gated on 等）照報但永不計入可認領，"
    "所以純門控隊列讀成欠債而不是存量；空隊列=誠實零（缺口等於整個地板），"
    "缺檔=缺失並退 3；CLI 0 達標 / 2 缺口或壞旗標 / 3 缺檔，--json 五鍵穩定。"
    "本輪零雲端呼叫、零外部 API 觸點。"
)

LATEST = (
    "src/os/queue_floor.py（只讀隊列地板量規，一行讀數）"
    "+ src/os/test_queue_floor.py（SUITE PASS 8/8 雙跑逐位元組同一，"
    "qa/queue-floor-R2244-a.log 與 -b.log，各 762 位元組，單寫者 utf-8 LF）"
    "+ 接線 os-queue-floor(8)（src/sandbox/reconcile_all.py）；"
    "時間戳 2026-10-29"
)

NEXT = (
    "下一窗（48 小時內，R2245）：①在本提交樹跑全量對賬電池＋套件矩陣再生"
    "（本窗 25 分鐘預算被產品面佔滿，照 R2168 混樹律不在電池窗內改產品碼）；"
    "②按本輪量規讀出的缺口 12（main 4 / tech 3 / explore 5）補真種子到地板"
    "並認領最上真活項"
)

OUT = (
    "queue floor gauge (queue_floor.py) - floors measured instead of discovered",
    "on",
    ("R2244: the standing-line floors (main >= 5, tech >= 10, explore >= 10) "
     "were enforced by eyeballing a grep count mid-window, so a shortfall was "
     "discovered only after the queue had already starved. src/os/queue_floor.py "
     "reads the three queue files and prints one line - QUEUE FLOOR main=1/5 "
     "tech=7/10 explore=5/10 verdict=FLOOR-DEBT shortfall=12 - plus one line per "
     "queue. The row law is column-0 anchored '- [ ]' requiring a space or end "
     "after the box (the first suite run caught '- [ ]text' being counted and the "
     "implementation was tightened to the pre-registered intent, never the "
     "criterion widened). Eight gate marker forms are reported as gated and never "
     "counted as claimable, so a queue of pure gates reads as debt. An empty queue "
     "is an honest zero (shortfall == the whole floor); a missing queue file reads "
     "MISSING with exit 3. CLI exits 0 met / 2 short or bad flags / 3 missing and "
     "--json carries the five pinned report keys byte-stably. Evidence: SUITE PASS "
     "8/8 double-run byte-identical criterion sha16 8D4D43DB92838EA2 (762B per leg, "
     "single writer utf-8 LF by src/os/evidence_R2244.py), wired os-queue-floor(8), "
     "five adjacent os suites green (qa/regression-R2244.log, fails=0).")
)

RESULT = (
    "R2244",
    ("product window on the P2 tech head (R2240 a seed): the floors are now a "
     "reading - QUEUE FLOOR main=1/5 tech=7/10 explore=5/10 verdict=FLOOR-DEBT "
     "shortfall=12 on the live tree; SUITE PASS 8/8 double-run byte-identical "
     "(sha16 8D4D43DB92838EA2), wired os-queue-floor(8), five adjacent os suites "
     "green; criteria AC-QF1..6 pre-registered in the seed before the code with "
     "AC-QF7 and AC-QF8 added in the same window and disclosed. Honest debt: the "
     "full reconcile battery and the suite-matrix regeneration are the next "
     "window's first item, and the measured floor shortfall of 12 is the next "
     "seeding duty.")
)


def main():
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        text = handle.read()
    before = json.loads(text)

    import re
    text = re.sub(r'"export_ts": "[^"]*"',
                  lambda match: '"export_ts": %s' % json.dumps(now),
                  text, count=1)
    text = re.sub(r'"do": "[^"]*"',
                  lambda match: '"do": %s' % json.dumps(DO), text,
                  count=1)

    for key, value in (("current", CURRENT), ("latest_artifact", LATEST),
                       ("next_milestone", NEXT)):
        pattern = r'"%s": "[^"]*"' % key
        if len(re.findall(pattern, text)) != 1:
            raise SystemExit("E_ANCHOR: %s is not unique" % key)
        text = re.sub(pattern,
                      lambda match, k=key, v=value: '"%s": %s'
                      % (k, json.dumps(v)), text, count=1)

    outs_head = '"outs": [\n'
    if text.count(outs_head) != 1:
        raise SystemExit("E_ANCHOR: outs head")
    outs_block = ("%s    %s,\n" % (outs_head,
                                   json.dumps(list(OUT), ensure_ascii=False,
                                              indent=0).replace("\n", "\n    ")))
    text = text.replace(outs_head, outs_block, 1)

    results_head = '"results": [\n'
    if text.count(results_head) != 1:
        raise SystemExit("E_ANCHOR: results head")
    res_block = ("%s    %s,\n" % (results_head,
                                  json.dumps(list(RESULT), ensure_ascii=False,
                                             indent=0).replace("\n", "\n    ")))
    text = text.replace(results_head, res_block, 1)

    after = json.loads(text)
    if after["export_ts"] != now or after["ceo_face"]["current"] != CURRENT:
        raise SystemExit("E_VERIFY: patch did not land")
    if after["outs"][0][0] != OUT[0] or after["results"][0][0] != "R2244":
        raise SystemExit("E_VERIFY: prepend did not land")
    after["self_drive"]["queue_main_open"] = 2
    after["self_drive"]["queue_tech_open"] = 7
    after["self_drive"]["queue_explore_open"] = 5
    after["self_drive"]["log_lines_in_window"] = 3
    after["self_drive"]["substantive_non_idle_mention_lines"] = 3

    # rewrite only the self_drive numbers, keeping every other byte
    for key, value in (("queue_main_open", 2), ("queue_tech_open", 7),
                       ("queue_explore_open", 5),
                       ("log_lines_in_window", 3),
                       ("substantive_non_idle_mention_lines", 3)):
        pattern = r'"%s": \d+' % key
        if len(re.findall(pattern, text)) != 1:
            raise SystemExit("E_ANCHOR: self_drive %s" % key)
        text = re.sub(pattern,
                      lambda match, k=key, v=value: '"%s": %d' % (k, v),
                      text, count=1)

    final = json.loads(text)
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("EXPORT ts=%s bytes=%d" % (final["export_ts"],
                                     len(text.encode("utf-8"))))
    print("OUTS %d -> %d" % (len(before["outs"]), len(final["outs"])))
    print("RESULTS %d -> %d" % (len(before["results"]),
                                len(final["results"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())