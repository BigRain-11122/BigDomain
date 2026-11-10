"""R2606 state append: tick + round log, as a SURGICAL text edit.

MEASURED before writing: this file's log items carry a legacy 16-space indent
and the whole file is CRLF, so a json.dumps round-trip is NOT byte-stable for
it (it rewrites every log item to a 2-space indent). This writer therefore
never re-dumps the file: it bumps the tick on its own line and appends the new
items inside the log array, leaving every existing byte where it was. Both
edits are verified by parsing the result and comparing the untouched prefix
and suffix.
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

LINES = [
    "2026-11-10 R2606 PRODUCT window on the queue head the debt gate named"
    " (product-face-R2605, state/queue/tech.md:638 prefix AC-EDMD1, criteria"
    " AC-EDMD1..AC-EDMD6 pinned there at R2604 BEFORE any code). Five readings"
    " at open: git status EMPTY at HEAD 39d98836 equal to origin/main with no"
    " index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the"
    " content-addressed D-/C- scan read 63 file tokens against the stored"
    " baseline with new=0 over 109 rows, the group orders tail unchanged at the"
    " 2026-11-09 00:59 BigStream row, benchmarks 2026-11-03 exactly seven days"
    " old and therefore inside the gate. debt_gate read CLAIM-FIRST"
    " product-face-R2605 first=1 open=39; queue_head named tech line 638 prefix"
    " AC-EDMD1 claimable=15 and queue_floor read FLOOR-MET 5/5 15/10 10/10.",

    "2026-11-10 R2606 THE FOUR LIMITS WERE RE-MEASURED BEFORE ANY CODE by"
    " re-running src/os/limits_suite_matrix_reconcile_shape_next_R2604.py and"
    " every one matched the row: an '=' separator read shape=(6, None) so a"
    " broken separator fell through to a content word, a header with no"
    " separator row read shape=(6, None) as well, --ceiling 0 returned nothing"
    " with decoded=0 bounded=True, and a title carried twice read the first"
    " table (6, 6).",

    "2026-11-10 R2606 SHIPPED src/os/suite_matrix_reconcile.py extended in"
    " place plus src/os/test_suite_matrix_reconcile_shape.py:"
    " is_separator_row accepts any single repeated punctuation character, an"
    " absent separator row refuses as SEPARATOR-MISSING with its own code, a"
    " ceiling below one candidate refuses as CEILING-STARVED on BOTH the read"
    " and the compose path, and a repeated matrix title refuses as"
    " TITLE-REPEATED naming the count; every R2604 and R2602 answer survives on"
    " the same fixtures. PROOF: AC-EDMD1..AC-EDMD6 SUITE PASS 6/6 TWICE"
    " identical through the shipped capture"
    " (qa/suite-matrix-reconcile-shape-R2606.log, 1972B, digest"
    " 4921D77253FAC1B3, adjacent=3, fails=0) plus a read-only live leg reading"
    " DOC-CURRENT at 638/638 rows and 4804 criteria"
    " (qa/suite-matrix-reconcile-shape-live-R2606.log). REGISTRY 637/4798 ->"
    " 638/4804 by exactly one row recounted by import;"
    " docs/sandbox-suite-matrix.md was regenerated through this face own --write"
    " to 65137B at 638 rows and --check then read byte-identical. ONE OWN"
    " defect was caught and repaired: the criterion printer was indented, so"
    " the first capture digested the EMPTY string (E3B0C442...), and the marker"
    " now starts the line so the digest is real. BOARD: row 638 was closed"
    " through src/os/queue_close_R2606.py at its predicted and measured"
    " 1874592B -> 1878809B and ONE row was seeded as AC-EDME1..AC-EDME6 from"
    " FOUR limits MEASURED this window; head now line 640 and queue_floor read"
    " FLOOR-MET. DEBT: product-face-R2605 closed at 195841B -> 195844B (open"
    " 39->38, done 299->300) and reconcile-battery-R2606 opened first=yes at"
    " the pre-registered 638/4804 (195844B -> 196037B), both readback ok, so"
    " the gate now names that battery first and the next window owes it BEFORE"
    " any further product byte.",

    "R2606 honest disclosures: (a) TWO product points on the Executive"
    " Protocol scale - a runnable face with its own six-criteria suite and a"
    " live document a maintainer can open - but NOTHING a CEO could newly open"
    " was built and no P-47 business surface moved, so every P-47 item still"
    " waits on CEO physical pieces (merchant id, mini-program appid/secret);"
    " (b) the four gaps were MEASURED at R2604 and re-measured here BEFORE any"
    " code, so this is a repair of a disclosed gap rather than a new"
    " discovery; (c) my own first capture digested the empty string and that is"
    " named above rather than hidden; (d) a title inside a fenced code block"
    " and a title carrying trailing spaces are still counted as extra titles"
    " and are seeded as AC-EDME2/AC-EDME3 rather than fixed here; (e) Docker"
    " is absent on this host so no containerised bring-up is claimed; (f)"
    " tasks.md was not touched, it is the P-47 canonical board; (g)"
    " BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell"
    " (carried ceo-pending physical item loop-s4u-reconcile).",

    "R2606 tokens: local=~22k api=0 api_reason=product window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face actually read, one debt gate plus queue"
    " head and floor read, one re-measure of four limits before any code, one"
    " face extension and one new six-criteria suite, two capture legs plus"
    " three adjacent suites, one live leg on the real tree, one registry row"
    " recounted by import, one document regenerated through the face own write,"
    " one board row closed and one seeded, two debt rows moved through their"
    " shipped writers, one limits script measuring the next row, and the"
    " state/export closeout; zero cloud calls and zero external API touches",
]

ITEM_INDENT = " " * 16
LOG_TAIL = "\r\n ]\r\n}"


def build(raw):
    """Return (new_text, tick_before) or raise ValueError with a code."""
    tick_line = '"tick": '
    start = raw.index(tick_line)
    end = raw.index(",", start)
    tick_before = int(raw[start + len(tick_line):end])
    new_text = (raw[:start + len(tick_line)] + str(tick_before + 1)
                + raw[end:])
    if not new_text.endswith(LOG_TAIL):
        raise ValueError("E_R2606_LOG_TAIL")
    head = new_text[:-len(LOG_TAIL)]
    items = "".join(",\r\n" + ITEM_INDENT
                    + json.dumps(line, ensure_ascii=False) for line in LINES)
    return head + items + LOG_TAIL, tick_before


def main():
    raw = open(STATE, "rb").read().decode("utf-8")
    try:
        text, tick_before = build(raw)
    except ValueError as exc:
        print(exc)
        return 3
    data = json.loads(text)
    ok = data["tick"] == tick_before + 1 \
        and data["log"][-len(LINES):] == LINES \
        and len(data["log"]) == len(json.loads(raw)["log"]) + len(LINES) \
        and text.startswith(raw[:raw.index('"tick": ')])
    if not ok:
        print("E_R2606_VERIFY")
        return 3
    if "--execute" not in sys.argv:
        print("PLAN tick=%d -> %d log_lines=%d bytes %d -> %d"
              % (tick_before, tick_before + 1, len(data["log"]),
                 len(raw.encode("utf-8")), len(text.encode("utf-8"))))
        return 0
    with open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    back = json.loads(open(STATE, "rb").read().decode("utf-8"))
    same = back["tick"] == tick_before + 1 and back["log"][-1] == LINES[-1] \
        and len(back["log"]) == len(data["log"])
    print("WROTE tick=%d log_lines=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), os.path.getsize(STATE), same))
    return 0 if same else 5


if __name__ == "__main__":
    sys.exit(main())