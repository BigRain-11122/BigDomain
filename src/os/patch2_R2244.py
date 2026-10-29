"""R2244 correction pass 2: the backlog one-liner and the export escapes.

The export stores non-ASCII values as \\uXXXX escapes, so the first pass
missed the Chinese CEO-face lines; this pass replaces them through
json.dumps(..., ensure_ascii=True) so the escaped form matches exactly.
"""

import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

BACKLOG_OLD = ("one line `QUEUE FLOOR main=1/5 tech=7/10 explore=5/10 "
               "verdict=FLOOR-DEBT shortfall=12` plus one line per queue")
BACKLOG_NEW = ("one line `QUEUE FLOOR main=5/5 tech=6/10 explore=5/10 "
               "verdict=FLOOR-DEBT shortfall=9` plus one line per queue")

CURRENT_OLD = (
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

CURRENT_NEW = (
    "R2244 產品輪：隊列地板（main ≥5 / tech ≥10 / explore ≥10）過去靠窗內 "
    "手數 grep，缺口總在隊列餓死之後才被發現、於是整窗預算只能拿去補種。"
    "本輪交付 src/os/queue_floor.py 只讀量規：一行讀出 "
    "main=5/5 tech=6/10 explore=5/10 verdict=FLOOR-DEBT shortfall=9，"
    "每隊一行明細；行律=列首 `- [ ]` 且方框後需空白（`- [ ]text` 不算行，"
    "首跑套件抓到的是實作、已按預註冊意圖收緊而非放寬判據）；"
    "八種門控標記（[needs-CEO]/blocked on CEO/gated on 等）照報但永不計入可認領，"
    "所以純門控隊列讀成欠債而不是存量；空隊列=誠實零（缺口等於整個地板），"
    "缺檔=缺失並退 3；CLI 0 達標 / 2 缺口或壞旗標 / 3 缺檔，--json 五鍵穩定。"
    "本輪零雲端呼叫、零外部 API 觸點。"
    "誠實勘誤：首度量規把 main 指到正典 tasks.md（2 條開項），而本屋主線實為 "
    "state/queue/main.md（6 條，導出核對器同樣從此重算），"
    "故首讀誤報 main=1/5、缺口 12；收尾時 check_export_consistency 抓出落差，"
    "QUEUE_PATHS 已改、套件夾具與其獨立重算同步改指，上列數字為改後重測值。"
)

NEXT_OLD = (
    "下一窗（48 小時內，R2245）：①在本提交樹跑全量對賬電池＋套件矩陣再生"
    "（本窗 25 分鐘預算被產品面佔滿，照 R2168 混樹律不在電池窗內改產品碼）；"
    "②按本輪量規讀出的缺口 12（main 4 / tech 3 / explore 5）補真種子到地板"
    "並認領最上真活項"
)

NEXT_NEW = (
    "下一窗（48 小時內，R2245）：①在本提交樹跑全量對賬電池＋套件矩陣再生"
    "（本窗 25 分鐘預算被產品面佔滿，照 R2168 混樹律不在電池窗內改產品碼）；"
    "②按本輪量規讀出的缺口 9（tech 4 / explore 5 / main 0）補真種子到地板"
    "並認領最上真活項"
)

RESULT_OLD = (
    "product window on the P2 tech head (R2240 a seed): the floors are now a "
    "reading - QUEUE FLOOR main=1/5 tech=7/10 explore=5/10 verdict=FLOOR-DEBT "
    "shortfall=12 on the live tree; SUITE PASS 8/8 double-run byte-identical "
    "(sha16 8D4D43DB92838EA2), wired os-queue-floor(8), five adjacent os suites "
    "green; criteria AC-QF1..6 pre-registered in the seed before the code with "
    "AC-QF7 and AC-QF8 added in the same window and disclosed. Honest debt: the "
    "full reconcile battery and the suite-matrix regeneration are the next "
    "window's first item, and the measured floor shortfall of 12 is the next "
    "seeding duty."
)

RESULT_NEW = (
    "product window on the P2 tech head (R2240 a seed): the floors are now a "
    "reading - QUEUE FLOOR main=5/5 tech=6/10 explore=5/10 verdict=FLOOR-DEBT "
    "shortfall=9 on the live tree; SUITE PASS 8/8 double-run byte-identical "
    "(sha16 8D4D43DB92838EA2), wired os-queue-floor(8), five adjacent os suites "
    "green; criteria AC-QF1..6 pre-registered in the seed before the code with "
    "AC-QF7 and AC-QF8 added in the same window and disclosed. Disclosed "
    "correction: the first reading of this window pointed main at the canonical "
    "tasks.md board (2 open rows) instead of the self-drive queue "
    "state/queue/main.md (6 open, the file the export checker recomputes from), "
    "so it reported main=1/5 shortfall=12; check_export_consistency caught the "
    "mismatch at closeout, QUEUE_PATHS and the suite fixtures were repointed and "
    "the reading above is the re-measured one. Honest debt: the full reconcile "
    "battery and the suite-matrix regeneration are the next window's first item, "
    "and the measured floor shortfall of 9 (tech 4, explore 5) is the next "
    "seeding duty."
)


def swap_escaped(text, old, new):
    old_esc = json.dumps(old, ensure_ascii=True)
    new_esc = json.dumps(new, ensure_ascii=True)
    if text.count(old_esc) != 1:
        print("WARN escaped form not unique: %d for %r"
              % (text.count(old_esc), old[:40]))
        return text, False
    return text.replace(old_esc, new_esc, 1), True


def main():
    with io.open(BACKLOG, "r", encoding="utf-8") as handle:
        text = handle.read()
    if text.count(BACKLOG_OLD) == 1:
        text = text.replace(BACKLOG_OLD, BACKLOG_NEW, 1)
        with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        print("BACKLOG patched")
    else:
        print("BACKLOG skipped count=%d" % text.count(BACKLOG_OLD))

    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        exp = handle.read()
    done = []
    for label, old, new in (("ceo_face.current", CURRENT_OLD, CURRENT_NEW),
                            ("ceo_face.next_milestone", NEXT_OLD, NEXT_NEW),
                            ("results[0][1]", RESULT_OLD, RESULT_NEW)):
        exp, ok = swap_escaped(exp, old, new)
        done.append((label, ok))
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(exp)
    parsed = json.loads(exp)
    print("EXPORT applied=%r" % (done,))
    print("EXPORT current_has_9=%r result_has_9=%r"
          % ("shortfall=9" in parsed["ceo_face"]["current"],
             "shortfall=9" in parsed["results"][0][1]))
    left = [m.group(0) for m in re.finditer(r"main=1/5|shortfall=12", exp)]
    print("EXPORT stale_hits=%d" % len(left))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())