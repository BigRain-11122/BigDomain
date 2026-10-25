"""R2119 closeout: state tick/log, backlog + explore-queue done flips.
Pure ASCII source; Chinese strings only in the data written to the
json/md files."""

import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")

ROUND = (
 "R2119 (five-silence scan clean: the decisions.md v2 watermark reports"
 " MOVED on the commit only while the content-addressed token set and"
 " every line of text are identical to the recorded blob (new-only set"
 " EMPTY, 252 UTF-8 lines, newest token still D-20261025-08 acknowledged"
 " in R2114) - the drifted blob_bytes/sha256 fields were re-recorded from"
 " HEAD 5373b7d9 this window; ledger zero new @BigDomain transfer rows;"
 " group orders baseline unchanged at 2026-10-24 12:17; benchmarks"
 " refreshed 2026-10-24 inside 7 days; tree clean, no index.lock; both"
 " daily standing rows for 2026-10-25 were already stamped by R2105 so"
 " neither was re-run; all four tech heads stayed gated - docker host"
 " absent, logs toolkit standing maintenance, member refunded schema"
 " window product-gated, live-mtime row waiting on a real event - and the"
 " single open explore row stays gated on the merchant id) - so this"
 " window seeded and claimed a fresh P3 row with AC-AMBQ1..AC-AMBQ8"
 " pre-registered BEFORE the code existed (the AC-AMBQ prefix,"
 " api_buyer_questions, ledger-apimarket-buyerquestions and"
 " MY_QUESTIONS_EMPTY anchors were all git grep -F zero-occupancy"
 " anchored 2026-10-25, rc=1) - the buyer-side question history. Product:"
 " api_buyer_questions merges every question of one buyer into a single"
 " time line across listings - eight-key envelope, ten-key rows, total"
 " order on (asked_utc, question_id), open and answered rows side by side,"
 " counts that always close (answered + unanswered == question_count),"
 " oldest_open_utc from the first open row, the title read through the one"
 " metadata revision seam, retired shelves keeping their history, strict"
 " buyer isolation (a seller account gets its own honest empty), a"
 " fail-closed account gate with zero table/token movement, and three"
 " restarts byte-identical. Consumer: every buyer block in"
 " apimarket_report.collect() gains a questions key read fresh, the page"
 " renders a my-questions table with a real empty state, and"
 " REPORT_SCHEMA moves 11 -> 12 additively (the envelope is still exactly"
 " schema_version/report/attention and every earlier block keeps its"
 " value; a legacy report dict degrades to the honest empty state)."
 " Suite src/sandbox/ledger/test_apimarket_buyerquestions.py SUITE 8/8"
 " double-run criterion lines byte-identical sha16 b8fac883087334de"
 " (qa/apimarket-buyerquestions-R2119.log + -run2, 879B each, utf-8 LF"
 " pure ASCII); wired ledger-apimarket-buyerquestions (8); battery RUNNER"
 " PASS 324/324 suites plus controls 7/7 in 1008.5s"
 " (qa/reconcile-all-R2119.log); matrix regenerated 324 suites / 2700"
 " criteria and --check byte-identical; census DRIFT-CLEAN; preview"
 " artifacts preview/apimarket-report-buyerquestions.html (18121B sha256"
 " bd375970052a6781) and .json (30303B, schema 12, sha256"
 " c86157d24bc9d3d4). Three honest disclosures: (a) the FIRST battery run"
 " failed 320/324 - three older report suites froze the buyer key tuple to"
 " equality (demand AC-AMDS2, refundregister AC-AMRR5, buyerhistory"
 " AC-AMBD5) and the additive questions key broke them, so each now proves"
 " the older keys are still all present instead of freezing the full set"
 " (birth-station repair, never loosened past the additive law), and one"
 " census finding was the new evidence files missing from the baseline;"
 " the matrix was regenerated and the census baseline updated BEFORE the"
 " second run, which is the green run quoted above; (b) an accidental"
 " `reconcile_all.py --help` probe wrote a stray file literally named"
 " `--help` in the repo root - deleted in-window and never staged; (c) the"
 " runner profile baseline was re-anchored per the R2044 precedent because"
 " the battery grew by one suite. Also refreshed the decisions watermark"
 " v2 record to HEAD 5373b7d9 (144258 bytes, sha256 cbc8d872) since the"
 " stored bytes/sha were stale.")

TOKENS = ("R2119 tokens: local=~95k api=0 api_reason=five-silence scan +"
          " buyer-side question history product change (read face + report"
          " consumer + my-questions table + schema 11->12 additive) +"
          " suite 8/8 double-run + three birth-station key-set repairs +"
          " battery 324/324 + matrix regen/check + census baseline +"
          " preview artifacts + watermark re-record + state/export"
          " closeout, zero cloud calls")

DONE_NOTE = ("[done 2026-10-25 R2119]（判据 AC-AMBQ1..AC-AMBQ8 预注册先于代码·"
             "四锚 git grep -F 零占用 rc=1·套件 8/8 双跑判据行同一 sha16 "
             "b8fac883087334de=qa/apimarket-buyerquestions-R2119.log+-run2·"
             "电池 RUNNER PASS 324/324 suites+controls 7/7 1008.5s="
             "qa/reconcile-all-R2119.log·矩阵 324 suites/2700 criteria "
             "--check byte-identical·census DRIFT-CLEAN·呈看件 "
             "preview/apimarket-report-buyerquestions.html sha256 "
             "bd375970052a6781·三处出生站键集断言放宽为包含式+矩阵/基线先更新"
             "后再跑电池全绿）")


def flip(path, marker, note):
    lines = io.open(path, encoding="utf-8").read().splitlines(True)
    out = []
    hit = False
    for line in lines:
        if not hit and line.startswith("- [ ] " + marker):
            line = "- [x] " + line[len("- [ ] "):]
            hit = True
            stripped = line.rstrip("\n")
            line = stripped + " " + note + "\n"
        out.append(line)
    io.open(path, "w", encoding="utf-8", newline="\n").write("".join(out))
    return hit


def main():
    state = json.load(io.open(STATE, encoding="utf-8"))
    state["tick"] = int(state.get("tick", 0)) + 1
    state["last_decision_rows"] = 252
    state.setdefault("log", []).append(ROUND)
    state["log"].append(TOKENS)
    io.open(STATE, "w", encoding="utf-8", newline="\n").write(
        json.dumps(state, ensure_ascii=False, indent=1) + "\n")

    b = flip(BACKLOG, "P3 explore \u961f\u5934\u8ba4\u9886\uff08R2119",
             DONE_NOTE)
    e = flip(EXPLORE, "P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4"
                      "\u9886\uff08R2119\uff09", DONE_NOTE)
    print("tick=%d backlog_flip=%r explore_flip=%r"
          % (state["tick"], b, e))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())