# closeout_R2261.py - one-shot closeout writer for the R2261 window.
# Bumps the state.json tick and appends the three R2261 log items, marks the
# claimed tech row done with this round's stamp, closes the debt register row
# that led this window and opens its successor, seeds one real gap row (the
# claim drops tech below its floor), and prepends the backlog lines. ASCII
# source; every write is a single writer with a read-back assertion.
import io
import json
import sys

sys.path.insert(0, 'src/os')
import state_fold as sf
import state_io as sio

STATE = 'src/os/state.json'
TECH = 'state/queue/tech.md'
DEBT = 'state/debt.md'
BACKLOG = 'src/os/backlog.md'

L1 = (
    "2026-10-29 R2261 (five-silence scan clean at open: tree clean with an empty git status --short "
    "and no index.lock; the queue gauge read main 5/5 tech 10/10 explore 10/10 FLOOR-MET with tech 11 "
    "open of which 1 gated and explore 10 open; decisions.md carries 289 non-empty rows and 194 "
    "content-addressed D/C/O/T/XL tokens against the stored 194-token superset baseline with ZERO "
    "additions, so zero domain action; the group ledger carries the same three @BigDomain patrol rows "
    "already paid off, none numbered, so zero unreplied handoffs; the group orders tail is unchanged at "
    "the 2026-10-29 02:1x CEO-PROXY event round R2.48 already consumed in R2226; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate) - the P1 canonical rows stay blocked-on-CEO, the weekly "
    "proposal duty is met by BD-PROP-005, and the debt register named exactly one first=yes row "
    "(product-face-R2261, opened by R2260), so this window took the product face on the top deliverable "
    "tech row: the R2259 seed src/os/evidence_capture.py. RESULT: the per-round evidence ritual is now "
    "one callable instead of an eighty-ninth hand-typed copy. capture(root, round, suite, adjacent, "
    "evidence) runs the suite twice, digests only the PASS/FAIL lines (so wall clock cannot fake a "
    "difference), and refuses BEFORE writing anything when a leg is red, when the two legs disagree on "
    "their criterion lines (E_EVC_DRIFT) or when an adjacent suite is red (naming it); the adjacent "
    "batch keeps its declared order with each suite own SUITE line; the body lands once as utf-8 LF "
    "through a single writer with the read-back proved byte-identical and a second write to the same "
    "path refused (E_EVC_EXISTS, file untouched); every refusal carries its own code (NO_SUITE/BADDIR "
    "3, EXISTS 4, BAD_ROUND/BAD_ARGS 5). Criteria AC-EVC1..AC-EVC6 were pinned in the queue row BEFORE "
    "the code; anchor check at HEAD 2026-10-29: os-evidence-capture / test_evidence_capture / E_EVC "
    "git grep -F zero-occupancy rc=1, while evidence_capture / AC-EVC hit only six TEXT files (the "
    "seed row, the R2248 backlog row, state.json, status-export.json, state/debt.md and a prose "
    "mention in closeout_R2259.py) - disclosed text occupancy, zero code occupancy. Evidence: this "
    "window's own evidence was produced BY the new callable rather than by a fresh copy of the ritual "
    "- EVIDENCE CAPTURE round=R2261 legs=2 identical=True adjacent=5 fails=0 verdict=CAPTURED "
    "(qa/evidence-capture-R2261.log, 1886B, single writer utf-8 LF through src/os/evidence_R2261.py, "
    "never a shell redirection) plus a live CLI run on test_queue_floor.py rc=0 writing "
    "qa/evidence-cli-R2261.log; the new suite itself was SUITE PASS 6/6 on its first run with no "
    "criterion relaxed. Honest disclosure: the AC-EVC6 census counts 91 files / 326455 bytes in "
    "src/os/evidence_R*.py, and that count includes the thin evidence_R2261.py driver written this "
    "window; the callable is 9509B, so the pile it replaces is about 34x wider. Honest score: one "
    "product face with its own suite, so 2 points. Queue ordering disclosed: rows 41 (docker absent on "
    "this machine), 54 (standing maintenance line), 85 (product-gated) and 88 (AC-LN1..LN8 already "
    "delivered at R1727) are not deliverable faces, so the top deliverable row was claimed. Marking it "
    "done drops tech claimable to 9 against the floor of 10, so one real gap row was seeded in this "
    "window (evidence_parity, AC-EVP1..AC-EVP6 pre-registered, five anchors git grep -F rc=1) and the "
    "gauge closed FLOOR-MET main 5/5 tech 10/10 explore 10/10. The full reconcile battery and the "
    "suite-matrix regeneration carry to R2262 (the R2168 mixed-tree rule) and are registered first=yes.")

L2 = (
    "R2261 tokens: local=~20k api=0 api_reason=product window on the debt register first item - one "
    "new os module with its six pre-registered criteria, one thin driver that uses the new callable to "
    "produce this window's own evidence, two live CLI readings, one runner entry, one seeded gap row, "
    "and the queue/backlog/debt/state/export closeout; zero cloud calls and zero external API touches; "
    "the battery and the matrix regeneration carry to R2262")

L3 = (
    "R2261 self-heal check: BigDomain-OSLoop is registered and its principal still reads "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; "
    "src/os/register_loop_task.ps1 already passes an explicit S4U principal and needs an elevated "
    "shell to apply it, and this session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window (twenty-ninth consecutive "
    "disclosure, registered as the stale row loop-s4u-reconcile in state/debt.md).")

SEED = (
    "- [ ] P2 tech seed (R2261, from this window own AC-EVC6 census): `src/os/evidence_parity.py` - the "
    "callable exists but the ninety-odd legacy per-round evidence scripts cannot be retired on a hunch: "
    "each one has to be proven to do exactly the five ritual legs the callable does (two legs of the same "
    "suite, a digest over its criterion lines, a single-writer utf-8 LF body, an ordered adjacent batch "
    "with its own SUITE lines, and a live gate line) and nothing else it silently relied on. One "
    "read-only reader that takes a legacy script path and classifies each ritual leg PRESENT / MISSING / "
    "DIFFERENT by static analysis, so retirement becomes one script at a time with evidence instead of a "
    "bulk delete. Criteria prefix AC-EVP1..AC-EVP6 pre-registered HERE BEFORE any code (AC-EVP1 the five "
    "leg names are returned in the pinned order and every one carries a verdict; AC-EVP2 a leg is PRESENT "
    "only on a positive marker match, MISSING when nothing matches, DIFFERENT when the marker exists but "
    "the shape differs; AC-EVP3 the reader is read-only - zero writes and the script bytes before and "
    "after are identical; AC-EVP4 an unreadable or absent script fails closed with its own code and zero "
    "fabricated legs; AC-EVP5 CLI exits 0 only when every leg is PRESENT, 2 when any leg is MISSING or "
    "DIFFERENT, 5 on bad flags, 3 on unreadable input, and the reading over the live pile is reported "
    "with a per-leg count; AC-EVP6 purity plus its own reconcile label). Anchor check at HEAD 2026-10-29: "
    "`evidence_parity`, `AC-EVP`, `E_EVP`, `os-evidence-parity`, `test_evidence_parity` were git grep -F "
    "zero-occupancy rc=1.")

NEW_DEBT = (
    "- [ ] opened=R2261 | item=reconcile-battery-R2262 | note=R2261 shipped src/os code "
    "(evidence_capture.py, test_evidence_capture.py, evidence_R2261.py) plus a new runner entry that no "
    "full battery has covered, so the next window runs the full reconcile battery and the suite-matrix "
    "regeneration on the committed tree (the R2168 mixed-tree rule: no product edit in a battery "
    "window). The floors read main 5/5 tech 10/10 explore 10/10 at the R2261 closeout, so the seeded "
    "row evidence_parity is the next product face if the battery is already clean. | first=yes")

CLOSED_DEBT = (
    "- [x] opened=R2260 | item=product-face-R2261 | closed=R2261 | note=discharged at R2261: the "
    "register named it first=yes, the floors read main 5/5 tech 10/10 explore 10/10 at open, rows 41 "
    "(docker absent), 54 (standing maintenance line), 85 (product-gated) and 88 (already delivered at "
    "R1727) were not deliverable faces, so the top deliverable row was claimed - src/os/evidence_capture.py "
    "shipped with AC-EVC1..AC-EVC6 pre-registered in the queue row before the code, SUITE PASS 6/6 on "
    "the first run, and this window's own evidence written by the new callable (EVIDENCE CAPTURE "
    "round=R2261 legs=2 identical=True adjacent=5 fails=0). The claim dropped tech claimable to 9 "
    "against its floor of 10, so one real gap row (evidence_parity) was seeded in the same window and "
    "the gauge closed FLOOR-MET. The battery and the matrix regeneration carry to R2262 and are "
    "registered first=yes. | first=no")

BACKLOG_NEW = [
    ("- [x] [done 2026-10-29 R2261] P2 tech claim (the debt register first=yes row product-face-R2261; "
     "seed = the R2259 evidence_capture row; criteria AC-EVC1..AC-EVC6 were pinned INSIDE that queue row "
     "BEFORE the code, anchor check at HEAD 2026-10-29: os-evidence-capture / test_evidence_capture / "
     "E_EVC zero-occupancy rc=1 while evidence_capture / AC-EVC hit only text - disclosed). Delivered "
     "src/os/evidence_capture.py - the per-round evidence ritual as one callable: two legs of the same "
     "suite, a digest over the PASS/FAIL lines only, a single-writer utf-8 LF body with a read-back "
     "proof and a refused second write, an ordered adjacent batch with each SUITE line, and refusals "
     "before anything is written. Evidence: SUITE PASS 6/6 first run (qa/evidence-capture-R2261.log, "
     "1886B, single writer utf-8 LF), five adjacent os suites green inside that same capture, a live "
     "CLI run on test_queue_floor.py rc=0 (qa/evidence-cli-R2261.log), wired os-evidence-capture(6); "
     "the census measured 91 legacy scripts / 326455B against the 9509B callable. The battery and the "
     "matrix regeneration carry to R2262 (the R2168 mixed-tree rule)."),
    ("- [x] [done 2026-10-29 R2261] the queue floor duty caused by this claim: marking the tech row "
     "done dropped claimable tech to 9 against the floor of 10, so one real gap row was seeded in the "
     "same window (evidence_parity, criteria AC-EVP1..AC-EVP6 pre-registered, five anchors git grep -F "
     "zero-occupancy rc=1) and the gauge closed FLOOR-MET main 5/5 tech 10/10 explore 10/10."),
]


def read(path):
    return io.open(path, 'rb').read().decode('utf-8')


def write(path, text, crlf=False):
    body = text.replace('\r\n', '\n')
    if crlf:
        body = body.replace('\n', '\r\n')
    io.open(path, 'wb').write(body.encode('utf-8'))
    back = io.open(path, 'rb').read().decode('utf-8')
    assert back == body, path
    return len(body.encode('utf-8'))


def do_state():
    text = read(STATE)
    lines = text.split('\r\n')
    if lines[1] != '  "tick": 2260,':
        print('UNEXPECTED tick line: %r' % lines[1])
        return 2
    lines[1] = '  "tick": 2261,'
    close = len(lines) - 2
    if lines[close].strip() != ']':
        print('UNEXPECTED close line: %r' % lines[close])
        return 2
    if lines[close - 1].rstrip().endswith(','):
        print('UNEXPECTED trailing comma on last item')
        return 2
    lines[close - 1] = lines[close - 1] + ','
    items = [sf.ITEM_PREFIX + json.dumps(s, ensure_ascii=True)
             for s in (L1, L2, L3)]
    new = [item + ',' for item in items[:-1]] + [items[-1]]
    lines[close:close] = new
    out = '\r\n'.join(lines)
    data = json.loads(out)
    if data['tick'] != 2261:
        print('VERIFY FAIL tick=%r' % data['tick'])
        return 2
    before = len(data['log'])
    size = write(STATE, out, crlf=True)
    print('state.json bytes=%d log items=%d (was %d)'
          % (size, before, before - 3))
    print(sio.report(STATE))
    return 0


def do_tech():
    text = read(TECH)
    old_head = ('- [ ] P2 tech seed (R2259, from this window own evidence workflow): '
                '`src/os/evidence_capture.py`')
    if text.count(old_head) != 1:
        print('UNEXPECTED tech row head count=%d' % text.count(old_head))
        return 2
    text = text.replace(
        old_head,
        '- [x] [done 2026-10-29 R2261] P2 tech claim (R2259 seed): '
        '`src/os/evidence_capture.py`')
    # stamp the delivered face onto the same row
    anchor = ('AC-EVC6 purity = pure-ASCII source, stdlib only, zero network '
              'imports, and the legacy per-round scripts are proven byte-wider '
              'than the callable before any of them is retired (retirement is '
              'a separate window with i')
    if text.count(anchor) != 1:
        print('UNEXPECTED tech row tail count=%d' % text.count(anchor))
        return 2
    tail_start = text.index(anchor)
    line_end = text.index('\n', tail_start)
    delivered = (' DELIVERED R2261: SUITE PASS 6/6 on the first run '
                 '(qa/evidence-capture-R2261.log, 1886B, single writer utf-8 '
                 'LF), five adjacent os suites green inside the same capture, '
                 'a live CLI run on test_queue_floor.py rc=0 '
                 '(qa/evidence-cli-R2261.log), wired os-evidence-capture(6); '
                 'this window own evidence was produced BY the new callable, '
                 'and the census measured 91 legacy scripts / 326455B against '
                 'the 9509B callable (the count includes the thin '
                 'evidence_R2261.py driver, disclosed).')
    text = text[:line_end] + delivered + text[line_end:]
    text = text.rstrip('\n') + '\n\n' + SEED + '\n'
    size = write(TECH, text)
    print('tech.md bytes=%d seed_appended=%r' % (size, 'evidence_parity' in text))
    return 0


def do_debt():
    text = read(DEBT)
    lines = text.split('\n')
    target = None
    for index, line in enumerate(lines):
        if line.startswith('- [ ] opened=R2260 | item=product-face-R2261'):
            target = index
            break
    if target is None:
        print('UNEXPECTED debt row not found')
        return 2
    lines[target] = CLOSED_DEBT
    lines.insert(target + 1, '')
    lines.insert(target + 2, NEW_DEBT)
    out = '\n'.join(lines)
    size = write(DEBT, out)
    print('debt.md bytes=%d' % size)
    return 0


def do_backlog():
    text = read(BACKLOG)
    if text.startswith('- [x] [done 2026-10-29 R2261]'):
        print('backlog already carries the R2261 lines')
        return 2
    out = '\n'.join(BACKLOG_NEW) + '\n' + text
    size = write(BACKLOG, out)
    print('backlog.md bytes=%d' % size)
    return 0


def main():
    for step in (do_state, do_tech, do_debt, do_backlog):
        code = step()
        if code != 0:
            print('STOPPED at %s rc=%d' % (step.__name__, code))
            return code
    return 0


if __name__ == '__main__':
    sys.exit(main())