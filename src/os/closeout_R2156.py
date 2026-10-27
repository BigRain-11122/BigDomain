#!/usr/bin/env python3
"""closeout_R2156.py - one-shot closeout for the adaptive inventory window.

Writes the round narrative + ledger line into src/os/state.json with CRLF
terminators (the canonical layout), refreshes docs/status-export.json from
the real state (F3 law: every value derived, nothing hardcoded) and prints
the resulting counts so the caller can verify them. Idempotent-safe: it
refuses to run twice for the same round.

ASCII-only source; stdlib only; zero network.
"""

import datetime
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, 'src', 'os', 'state.json')
EXPORT = os.path.join(ROOT, 'docs', 'status-export.json')
QUEUE_TECH = os.path.join(ROOT, 'state', 'queue', 'tech.md')
QUEUE_EXPLORE = os.path.join(ROOT, 'state', 'queue', 'explore.md')
QUEUE_MAIN = os.path.join(ROOT, 'state', 'queue', 'main.md')
PROPOSALS = os.path.join(ROOT, 'docs', 'proposals.md')

ROUND = 'R2156'

NARRATIVE = (
    "2026-10-27 R2156 (five-silence scan clean at open: decisions.md 294 "
    "non-empty rows carrying 217 content-addressed tokens with zero new "
    "against the stored baseline; the ledger's three @BigDomain patrol rows "
    "already paid off with zero unreplied; the group orders baseline "
    "unchanged at the 2026-10-26 22:36 dispatch-deck row; benchmarks "
    "refreshed 2026-10-27 inside the seven-day gate; tree clean, no "
    "index.lock; the tech heads below the head stayed gated and the single "
    "explore head is gated on the merchant id) - the P1 canonical rows stay "
    "blocked-on-CEO and the weekly proposal duty is met by BD-PROP-005, so "
    "this window claimed the P2 tech FIFO head, the R2149 seed row, and "
    "registered AC-LTI1..AC-LTI8 in the queue line BEFORE the code (six "
    "anchors zero-occupancy against HEAD rc=1: inventory_scan, "
    "classify_evidence, --with-qa, qa-evidence, test_logs_inventory, "
    "os-logs-inventory; honest notes: the AC-LTI prefix was already "
    "mentioned by the HEAD seed row as a text-only occupancy, and --evidence "
    "is an existing flag on funnel/wire_poc so the new flag is --with-qa). "
    "Product: logs_toolkit.py grows inventory_scan and a multi-root "
    "inventory face - the historical inventory subcommand only ever "
    "scandir'd logs/, so every qa/*.log proof file the rounds produce was "
    "absent from the catalog while the census claimed the whole disk. The "
    "default single-root output stays byte-identical (key set logs_dir / "
    "classes / total_files, same class counts, same protected and prunable "
    "flags) and only multi-root calls add roots / counted_entries / "
    "duplicates; qa/*.log classifies as qa-evidence and everything else in "
    "qa as evidence-other, both protected and never prunable; every file is "
    "counted once per (st_dev, st_ino) so an overlapping root or a "
    "cross-root hard link lands in duplicates instead of inflating the "
    "catalog; a root spec without '=' or a duplicated label exits 2 and a "
    "missing root exits 3, both with zero JSON on stdout so no partial green "
    "reading can leak. One Windows defect found and fixed in this window: "
    "entry.stat() from scandir reports st_dev/st_ino as 0 for every entry on "
    "this build, which collapsed the whole tree into a single inode; the "
    "scan uses os.stat(path), which does carry the real file index and the "
    "hard-link identity. Verification: SUITE PASS 31/31 double-run "
    "byte-identical sha16 729292074a238996 (qa/logs-inventory-R2156-a.log "
    "and -b.log, single-writer utf-8 LF); wired os-logs-inventory(8); the "
    "legacy logs_toolkit suite re-ran 163 checks green (the AC-LT3 inventory "
    "contract is unchanged). Honest gaps: the full battery was launched "
    "through battery_stream and was cancelled with the invoking command "
    "after the shell pipe withheld five minutes of output (no log file was "
    "written, no orphan process survived, no partial evidence exists), so "
    "the battery and the suite-matrix regeneration are NOT run this window "
    "and are the next round's first item; the daily FUNNEL and reconcile "
    "rows were already stamped for 2026-10-27 by earlier windows."
)

LEDGER = (
    "R2156 tokens: local=~70k api=0 api_reason=five-silence scan + adaptive "
    "multi-root inventory product change (inode de-dup + evidence classes) + "
    "31-criteria suite double-run + legacy toolkit regression + wiring + "
    "state/export closeout, zero cloud calls"
)

OUT_ROW = [
    'adaptive multi-root inventory + evidence tree in the catalog '
    '(AC-LTI1..AC-LTI8)',
    'on',
    'R2156: the inventory catalog only ever read logs/, so every qa/*.log '
    'proof file was invisible while the census claimed the whole disk. The '
    'tool now scans a declared root set: the default single-root reading '
    'stays byte-identical, qa/*.log becomes qa-evidence and the rest of qa '
    'becomes evidence-other (both protected, never prunable), every file is '
    'counted once per inode so overlapping roots and hard links land in a '
    'duplicates counter instead of inflating totals, and a bad root spec or '
    'a missing root fails closed with no JSON at all. Growth between two '
    'readings is seen with no cache. One Windows defect fixed in-window: the '
    'scandir-cached stat reports st_dev/st_ino as 0, collapsing the tree '
    'into one inode, so the scan uses os.stat(path). Deliverables: '
    'src/os/logs_toolkit.py, src/os/test_logs_inventory.py. Evidence: SUITE '
    'PASS 31/31 double-run sha16 729292074a238996; legacy toolkit suite 163 '
    'checks green; wired os-logs-inventory(8). Honest gap: the full battery '
    'and the matrix regeneration were not run this window (the launch was '
    'cancelled by the shell pipe with no evidence file and no orphan) and '
    'are the next round first item.',
]

RESULT_ROW = [
    ROUND,
    'R2156: five-silence scan clean at open (294 decision rows / 217 '
    'content-addressed tokens with zero new, three ledger patrol rows '
    'already paid, group orders baseline unchanged at the 2026-10-26 22:36 '
    'deck row, benchmarks fresh today, clean tree, no index.lock). The P2 '
    'tech head was claimable, so AC-LTI1..AC-LTI8 were registered in the '
    'queue line before the code: the adaptive inventory window. Product: '
    'multi-root inventory with an inode de-duplication law, evidence '
    'classes that retention can never select, default byte identity for the '
    'historical single-root contract, fail-closed root gates, and an '
    'uncached growth reading. Verification: SUITE PASS 31/31 double-run '
    'byte-identical sha16 729292074a238996, legacy logs_toolkit suite 163 '
    'checks green, wired os-logs-inventory(8). Battery and matrix regen NOT '
    'run (launch cancelled by the shell pipe; no evidence, no orphan) - the '
    'next round first item.',
]


def read_text(path):
    with io.open(path, encoding='utf-8') as f:
        return f.read()


def count_open(path):
    if not os.path.exists(path):
        return 0
    return len(re.findall(r'^- \[ \]', read_text(path), re.M))


def proposals_counts():
    if not os.path.exists(PROPOSALS):
        return 0, 0
    txt = read_text(PROPOSALS)
    total = len(set(re.findall(r'BD-PROP-\d+', txt)))
    closed = len(re.findall(r'BD-PROP-\d+[^\n]*\b(?:CLOSED|RETIRED|判负)\b', txt))
    return total, max(total - closed, 0)


def main():
    with io.open(STATE, encoding='utf-8') as f:
        state = json.load(f)
    if any(line.startswith('2026-10-27 R2156 (') for line in state['log']):
        print('already closed out for ' + ROUND)
        return 1
    state['tick'] = int(state.get('tick', 0)) + 1
    state['log'].append(NARRATIVE)
    state['log'].append(LEDGER)
    with io.open(STATE, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(json.dumps(state, ensure_ascii=False, indent=2) + '\n')

    now = datetime.datetime.now()
    window_start = (now.date() - datetime.timedelta(days=6)).isoformat()
    window_lines = [ln for ln in state['log']
                    if re.match(r'^\d{4}-\d{2}-\d{2}', ln) and ln[:10] >= window_start]
    props_total, props_open = proposals_counts()

    with io.open(EXPORT, encoding='utf-8') as f:
        export = json.load(f)
    export['export_ts'] = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
    cur_do = export.get('do', '')
    if ROUND not in cur_do:
        export['do'] = ROUND + ' closeout: ' + cur_do if cur_do else ROUND
    export['ceo_face'] = {
        'current': 'R2156 adaptive inventory window: building the evidence '
                   'tree into the log catalog (product change + suite green)',
        'latest_artifact': 'qa/logs-inventory-R2156-a.log / -b.log '
                           '(SUITE PASS 31/31, sha16 729292074a238996, '
                           'written 2026-10-27)',
        'next_milestone': 'next round first item: full reconcile battery + '
                          'suite-matrix regeneration over the new wiring '
                          '(within 48h)',
    }
    export['outs'] = [OUT_ROW] + [row for row in export.get('outs', [])
                                  if row[0] != OUT_ROW[0]][:7]
    export['results'] = [RESULT_ROW] + [row for row in export.get('results', [])
                                       if row[0] != ROUND][:7]
    export['self_drive'] = {
        'window': window_start + '..' + now.date().isoformat(),
        'window_days': 7,
        'log_lines_in_window': len(window_lines),
        'idle_fast_mention_lines': sum(1 for ln in window_lines if 'idle-fast' in ln),
        'no_pullable_mention_lines': sum(1 for ln in window_lines if 'no-pullable' in ln),
        'substantive_non_idle_mention_lines': sum(
            1 for ln in window_lines
            if 'idle-fast' not in ln and 'no-pullable' not in ln),
        'proposals_total': props_total,
        'proposals_open': props_open,
        'queue_main_open': count_open(QUEUE_MAIN),
        'queue_tech_open': count_open(QUEUE_TECH),
        'queue_explore_open': count_open(QUEUE_EXPLORE),
    }
    with io.open(EXPORT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(export, ensure_ascii=False, indent=2) + '\n')
    print('tick=%d log_lines=%d window_lines=%d tech_open=%d explore_open=%d'
          % (state['tick'], len(state['log']), len(window_lines),
             export['self_drive']['queue_tech_open'],
             export['self_drive']['queue_explore_open']))
    return 0


if __name__ == '__main__':
    sys.exit(main())