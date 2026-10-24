# -*- coding: utf-8 -*-
"""Byte-surgical R2071 state update: repair the R2070 pair left at
8-space indent, bump tick, append the two log items at the 16-space
canonical, and verify JSON semantics differed only by the intended
changes."""
import json
import re

ST = 'src/os/state.json'
raw = open(ST, encoding='utf-8', newline='').read()
before = json.loads(raw)

lines = raw.split('\r\n')
fixed = 0
for idx, line in enumerate(lines):
    if re.match(r'^ {8}"(2026-10-24 R2070 |R2070 tokens: )', line):
        lines[idx] = '        ' + line
        fixed += 1
assert fixed == 2, fixed
mid = '\r\n'.join(lines)
assert json.loads(mid) == before, 'indent repair changed semantics'
assert lines[0] == '{' and lines[1].startswith('    "tick": 2070')

mid = mid.replace('    "tick": 2070,', '    "tick": 2071,', 1)

NARR = (
    "2026-10-24 R2071 (P3 explore-queue FIFO head claim after the tech"
    " heads were judged non-claimable: the docker-compose row is"
    " environment-gated (docker absent, verified on this host), the"
    " member refunded row stays gated on a product read-face need, and"
    " the LN live-mtime row waits for a real flatten event; seed = the"
    " R2044 straddle2 suite) - the statsmonth straddle POST-CLOSURE"
    " RETRACT third-shape window. Five-silence scan clean: decisions.md"
    " zero new content-addressed tokens against the baseline, ledger zero"
    " new @BigDomain rows, group orders baseline unchanged at 2026-10-24"
    " 06:5x, benchmarks refreshed 2026-10-20 (inside 7 days), tree clean,"
    " no index.lock. Claimed the explore row with AC-SMTR1..AC-SMTR7"
    " pre-registered in the queue row BEFORE the suite existed (AC-SMTR"
    " prefix git grep zero-occupancy verified). Delivered"
    " src/sandbox/ledger/test_showcase_statsmonth_straddle3persist.py:"
    " the R2044 ladder grown by one honest step - from the closed-yet-"
    "broken window {2,2,2} one CURRENT-month re-placed exhibit is"
    " retracted again through the real path and the window reads"
    " {2,3,1}, the identity breaking with a NEGATIVE right-hand side"
    " (1 != 2-3 = -1), while the full board keeps holding ({5,3,2}:"
    " 2 == 5-3). The battery pins the whole ladder in one run:"
    " pre-straddle {3,0,3}/{0,0,0} with identity on every row, double"
    " straddle {3,2,1}/{0,2,0} broken, closure {5,2,3}/{2,2,2} broken,"
    " third shape {5,3,2}/{2,3,1} broken, and one further re-place"
    " bounces the window to {3,3,2} (2 != 3-3) - the fourth shape,"
    " pinned honestly in passing. beta-gal is the place-first contrast"
    " whose window identity holds at every step, mu-gal rides every form"
    " as the honest-zero row, the old-month window and its display view"
    " stay byte-frozen through all mutations, view/chronicle/tour follow"
    " the retract-and-return order, an already-displayed re-place probe"
    " refuses with zero rows, a cross-showcase retract refuses with zero"
    " rows, ledger_tx stays 0 end to end, and two full-stack restarts"
    " replay all thirteen forms byte-identically. SUITE PASS 7/7"
    " double-run identical (stdout sha16 272de2e4e6fddf90); wired"
    " ledger-showcase-statsmonth-straddle3-persist (7) into reconcile_all"
    " SUITES; full battery RUNNER PASS 279/279 suites + controls 7/7"
    " 217.5s = qa/reconcile-all-R2071.log; suite-matrix regenerated 279"
    " suites / 2339 criteria, --check byte-identical (27066 bytes)."
    " Honest notes: (a) the R2070 round had left its two log lines at"
    " 8-space indent and this window repaired them to the 16-space"
    " canonical with json semantics verified equal; (b) the tech queue"
    " still stands at 4 open rows, so it was reseeded with one REAL gap"
    " row (the evidence-log newline-dialect family that bit three"
    " consecutive rounds R2068/R2069/R2070) instead of manufactured"
    " seeds; explore open goes 5 -> 4, main open unchanged at 6 (all"
    " blocked on CEO physical items). Score 2.")

TOK = ("R2071 tokens: local=~135k api=0 api_reason=five-silence scan +"
       " post-closure third-shape suite 7/7 double-run + battery 279/279"
       " + matrix regen/check + evidence log + state layout repair +"
       " state/export closeout, zero cloud calls")

tail = '\r\n    ]\r\n}\r\n'
assert mid.endswith(tail), repr(mid[-20:])
body = mid[:-len(tail)]
body = body.rstrip('\r\n')
assert body.endswith('zero cloud calls"'), repr(body[-40:])
body += ',\r\n' + '                ' + json.dumps(NARR, ensure_ascii=False)
body += ',\r\n' + '                ' + json.dumps(TOK, ensure_ascii=False)
out = body + tail
after = json.loads(out)
assert after['tick'] == 2071
assert after['log'][len(before['log'])] == NARR
assert after['log'][len(before['log']) + 1] == TOK
assert len(after['log']) == len(before['log']) + 2
assert [k for k in before
        if k not in ('tick', 'log') and before[k] != after[k]] == []
assert after['last_order'] == before['last_order']
open(ST, 'w', encoding='utf-8', newline='').write(out)
print('state ok tick', after['tick'], 'log n', len(after['log']))