"""R2805 closeout - append the round's log lines and bump the tick.

Surgical text edit: the file is re-serialised nowhere, so every existing byte
(including the exact newline dialect and the 158 log entries already on record)
survives unchanged. JSON validity is proven by parsing the result before the
write, and the write goes through a tmp file plus os.replace.
"""
import io
import json
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state.json')
TICK_FROM = '"tick": 2804'
TICK_TO = '"tick": 2805'

LINES = [
    "2026-11-16 R2805 PRODUCT: the CEO \"latest artifact\" line was naming a "
    "census of open work instead of a face anyone can open. MEASURED at open on "
    "the final tree: export_round --check read VERDICT PASS tick=R2804 while "
    "ceo_face.latest_artifact read preview/ceo-blockers.html (8453B) + "
    "preview/ceo-blockers.json (6754B), an open-work blocker board, and the "
    "newest REAL product face - first-yuan-chain at 11-15 22:24:19 - sat fourth "
    "behind three meta pages (ceo-blockers 00:53:40, face-sweep 00:53:40, "
    "battery-shard-report 00:52:41). Root cause read in src/os/export_round.py: "
    "newest_pair() chose the newest html+json pair on disk with no notion of "
    "WHAT the pair was, so anything a window rendered could take the slot. FIX "
    "AT THE BIRTH SITE: BOARD_PAGES = (ceo-blockers, face-sweep, "
    "battery-shard-report, index) is now the single definition of a meta page, "
    "newest_artifact() returns the newest pair outside that set together with "
    "the board pairs it actually passed over, and the face publishes "
    "board_pages_skipped and newest_pair_on_disk_is_board so the exclusion is "
    "auditable rather than silent. When every pair on disk is a meta page the "
    "line STATES that fact instead of naming one. AC-EXPW7..AC-EXPW10 were "
    "pinned in src/os/backlog.md and committed as 9b05c132 BEFORE this code.",
    "R2805 MEASURED AFTER, ON THE REAL TREE: the line now reads "
    "preview/first-yuan-chain.html (3078B) + preview/first-yuan-chain.json "
    "(4159B), with board_pages_skipped naming all three meta pairs and "
    "newest_pair_on_disk_is_board=True. src/os/test_export_round.py grew from 24 "
    "to 32 checks and reads SUITE PASS 32/32; the new blocks drive three "
    "controlled private worlds (board-on-top, product-on-top, board-only) whose "
    "mtimes are set by the test rather than inherited from the tree, plus three "
    "tamper cases, and each control reddens only its own criterion: a face "
    "naming ceo-blockers turns AC-EXPW7 red, an emptied skipped audit turns "
    "AC-EXPW9 red, and restoring the derived face reads clean again. Registry "
    "row os-export-round 6 -> 10 criteria, recounted BY IMPORT at 690 suites / "
    "5154 criteria / 690 unique names / 690 unique paths; the matrix was "
    "regenerated to 72776B with the shipped generator (src/sandbox/suite_matrix.py "
    "--evidence qa/reconcile-all-R2739.log) and honestly reports green=675/690.",
    "R2805 honest disclosures: (a) this is a REPAIR on a CEO-visible surface, not "
    "a new product face - a buyer still receives nothing new this window and "
    "every P-47 business item still waits on the same physical pieces; (b) "
    "src/os/suite_matrix_reconcile.py --check reads CEILING-STARVED rc=3 on this "
    "tree AND on the HEAD copy of the matrix doc (measured by writing HEAD's doc "
    "to tmp/ and re-running with --doc), so it is a PRE-EXISTING red caused by no "
    "recent full battery leg inside the 64-file walk - carried, not fixed, and "
    "one more reason the full battery is owed; (c) the matrix stamp evidence is "
    "still R2739, which is why the document reports 675/690 green instead of "
    "claiming this window's registry; (d) the 17 tool faces still without "
    "battery rows and the three untickable CEO rows in ship-checklist are "
    "untouched; (e) state.json remains far over the 78500B waterline, so the "
    "round-aligned fold stays owed; (f) the dead per-round export hook "
    "src/os/export_R2431.py stays owed; (g) BigDomain-OSLoop still reads "
    "InteractiveToken and needs an elevated shell for its S4U re-registration.",
    "R2805 tokens: local=~40k api=0 api_reason=one five-silence scan with a "
    "content-addressed decisions diff, one root-cause read of the export hook, "
    "one birth-site change under four pre-pinned criteria, one suite extended by "
    "eight checks over five controlled private worlds, one registry row bump "
    "recounted by import, one matrix regeneration plus a HEAD-copy control that "
    "proved the matrix red is pre-existing, and the state/board/export closeout; "
    "zero cloud calls and zero external API touches",
]


def main():
    with io.open(P, 'r', encoding='utf-8', newline='') as f:
        s = f.read()
    nl = '\r\n' if '\r\n' in s else '\n'
    anchor = '"log": [' + nl
    if s.count(anchor) != 1:
        raise SystemExit('E_ANCHOR expected exactly 1 log anchor')
    start = s.index(anchor) + len(anchor)
    k = start
    while k < len(s) and s[k] == ' ':
        k += 1
    indent = s[start:k]
    # append at the TAIL of the log array: the array is chronological and the
    # reader takes the newest entry as the last one, so inserting after the
    # opening bracket would record this round as the oldest on file.
    close = nl + '  ],' + nl + '  "tick":'
    if s.count(close) != 1:
        raise SystemExit('E_CLOSE expected exactly 1 log close')
    head = s[:s.index(close)]
    if not head.rstrip().endswith(','):
        head = head.rstrip() + ','
    entries = [json.dumps(line, ensure_ascii=False) for line in LINES]
    block = ','.join([nl + indent + e for e in entries])
    s = head + block + close + s[s.index(close) + len(close):]
    if s.count(TICK_FROM) != 1:
        raise SystemExit('E_TICK expected exactly 1 tick slot')
    s = s.replace(TICK_FROM, TICK_TO, 1)
    data = json.loads(s)
    assert data['tick'] == 2805, data['tick']
    assert data['log'][-1].startswith('R2805 tokens:'), data['log'][-1][:20]
    assert data['log'][-4].startswith('2026-11-16 R2805 PRODUCT'), \
        data['log'][-4][:30]
    tmp = P + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
        f.write(s)
    os.replace(tmp, P)
    print('OK tick=%s log=%d bytes=%d nl=%s'
          % (data['tick'], len(data['log']), len(s.encode('utf-8')),
             'crlf' if nl == '\r\n' else 'lf'))


if __name__ == '__main__':
    main()
