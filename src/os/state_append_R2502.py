"""R2502 closeout: tick advance, this round's two log lines, decisions baseline.

Writes once through the same in-place law the earlier appenders use: the file
is CRLF with the log array at sixteen spaces, so the new lines are inserted as
JSON-escaped rows before the closing bracket and the tick plus the aux decision
row count are moved with anchored substitutions that must each hit exactly once.
"""

import io
import json
import re
import sys

P = "src/os/state.json"
LINES = [
    "2026-11-07 R2502 PRODUCT window on the tech head the register named (state/queue/tech.md:538 prefix AC-PLR1 patterns_label_readability, criteria AC-PLR1..AC-PLR6 pinned in that row at R2494 BEFORE any code). Five-silence scan at open was clean at HEAD a4393852 (git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, content-addressed decisions diff new=0 over the 85-token baseline with four tokens rotated out of the file, group orders tail unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 inside the seven-day gate). debt_gate read OPEN-NONE (no first=yes row, open=2 both first=no) and queue_head named tech line 538 AC-PLR1 claimable=10, so this window shipped the carried product byte.",
    "2026-11-07 R2502 CLAIM AND SHIP: the seed said suite_matrix_patterns.json labels.stamp_from reads a mis-decoded CJK run while its siblings read proper Chinese and suite_matrix renders every label verbatim into docs/sandbox-suite-matrix.md. MEASURED at open: the patterns file and the artifact are both clean UTF-8 on disk and every label reads CLEAN - the mojibake in the R2494 note was a CONSOLE decoding artifact (PowerShell rendering UTF-8 bytes through the platform code page), not a damaged byte - so the detection is proved on fixtures built from the real file and is not claimed as a live catch. SHIPPED src/os/patterns_label_readability.py plus its suite: reading() asks unicodedata for every non-ASCII codepoint of every string label at CALL time - a broken codepoint (replacement character, unnamed, C-category) or a script bucket that no OTHER label in the same file carries is SUSPECT with its position, its U+XXXX and its Unicode name - punctuation, symbols, separators, digits and marks are shared and never suspect, and nothing here holds a key list or a blessed-script table (the suite proves no label key is spelled in the source). gate() names the first suspect as E_PLR_SUSPECT with the label key and its codepoints, and publish(labels, render) refuses to call the renderer at all on a suspect file while a clean file reaches it untouched.",
    "2026-11-07 R2502 PROOF measured, not quoted: AC-PLR1..AC-PLR6 SUITE PASS 6/6 TWICE with an identical verdict digest plus three adjacent suites green (qa/patterns-label-readability-R2502.log, 4773B, utf-8 LF, legs=2 identical=True fails=0 adjacent=3). The clean-file parity leg drives the REAL suite_matrix.render through publish() and gets docs/sandbox-suite-matrix.md back byte for byte at 55718B. The suspect legs carry the exact codepoints U+04E1,U+FFFD,U+FFFD,U+FFFD,U+FFFD,U+04D4 with indices 0..5 and the law each one broke, and the sibling labels stay CLEAN. LIVE reading of the real patterns file plus a doctored copy landed in qa/patterns-label-readability-live-R2502.log with the shipped file digest unchanged before and after (sha256 head ea5773ac0c11), so the module rewrites nothing.",
    "2026-11-07 R2502 REGISTRY AND BOARD: one runner row os-patterns-label-readability(6), so the registry reads 580 suites / 4456 criteria, recounted by importing reconcile_all.SUITES. docs/sandbox-suite-matrix.md regenerated stamp-aligned from qa/reconcile-all-R2500.log to 55718B at 580 suites / 4456 criteria and --check read byte-identical, its green line honestly reading 578/580 because that evidence predates two rows. FIRST LEG OF THE SUITE WAS RED and is disclosed: AC-PLR3 byte-identity failed at 55613B because adding the registry row moved the registry and the doc had not been restamped - the same row-moves-the-artifact lesson as R2491 - and the fix was the stamp-aligned regeneration at the birth site, not a loosened assertion.",
    "R2502 tokens: local=~30k api=0 api_reason=product window - one pre-registered face shipped with its six criteria, one suite proved twice with three adjacent suites green, one real red leg repaired at its birth site, one registry row recounted by import, one matrix stamp-aligned regeneration checked byte-identical, one live reading of the real tree with the source digest unchanged, one queue row closed through a per-round writer, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    raw = io.open(P, "rb").read()
    text = raw.decode("utf-8")
    tail = "\r\n  ]\r\n}\r\n"
    if not text.endswith(tail):
        print("FAIL state tail %r" % text[-30:])
        return 2
    tick_hits = re.findall(r'^\{\r\n  "tick": (\d+),', text)
    if len(tick_hits) != 1:
        print("FAIL tick anchor hits=%d" % len(tick_hits))
        return 2
    tick = int(tick_hits[0]) + 1
    text = text.replace('{\r\n  "tick": %d,' % int(tick_hits[0]),
                        '{\r\n  "tick": %d,' % tick, 1)
    rows = re.findall(r'\r\n  "last_decision_rows": (\d+),', text)
    if len(rows) != 1:
        print("FAIL last_decision_rows anchor hits=%d" % len(rows))
        return 2
    text = text.replace('"last_decision_rows": %s,' % rows[0],
                        '"last_decision_rows": 144,', 1)
    block = "".join(",\r\n                " + json.dumps(line, ensure_ascii=False)
                    for line in LINES)
    text = text[:-len(tail)] + block + tail
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    state = json.loads(io.open(P, encoding="utf-8").read())
    print("tick=%d loglen=%d last_decision_rows=%s bytes=%d"
          % (state["tick"], len(state["log"]), state.get("last_decision_rows"),
             len(text.encode("utf-8"))))
    return 0 if state["tick"] == tick and len(state["log"]) == 75 + len(LINES) else 1


if __name__ == "__main__":
    sys.exit(main())