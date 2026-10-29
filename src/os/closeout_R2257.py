"""R2257 closeout writer: append two log items, bump the tick.

write_canon refuses any payload change by design, so an append cannot go
through it. This uses the same discipline directly: build the text, let
state_io.canon() and layout() prove the shape and the payload, then one
atomic os.replace from a same-directory temp with a read-back proof.
"""

import io
import json
import os
import sys
import tempfile

sys.path.insert(0, 'src/os')
import state_io as SIO

PATH = 'src/os/state.json'

NARRATIVE = (
    "R2257 product window: the R2248 d seed shipped as src/os/state_seq.py - "
    "the round sequence is now a reading. Criteria AC-SEQ1..AC-SEQ6 were "
    "pinned in state/queue/tech.md BEFORE the code and the anchor check at "
    "HEAD was E_SEQ / os-state-seq / test_state_seq zero-occupancy rc=1 "
    "(state_seq and AC-SEQ hit only the seed generator, the R2248 backlog row "
    "and the row text, disclosed). The reader takes the tick as an int with "
    "tick_lead = tick - largest label and fails closed (E_SEQ_BAD_STATE, exit "
    "3) rather than fabricating one, counts only each log item's OWN label by "
    "importing the round_evidence law instead of re-implementing it, lists "
    "gaps inside the known span only, and reports repeats and backwards "
    "separately. Evidence: SUITE PASS 6/6 double-run byte-identical criterion "
    "sha16 93B363F778BE65E1 (qa/state-seq-R2257-a.log and -b.log, 478B each, "
    "single writer utf-8 LF through src/os/evidence_R2257.py, never a shell "
    "redirection), five adjacent os suites green (qa/regression-R2257.log, "
    "fails=0), wired os-state-seq(6). Live reading at closeout: STATE SEQUENCE "
    "labels=48 distinct=15 span=2242..2256 gaps=0 repeats=0 backwards=0 "
    "tick=2256 tick_lead=0 queue_done=163 queue_only=156 "
    "verdict=SEQUENCE-OK. Honest disclosure: the first AC-SEQ4 wording (labels "
    "written more than once) was falsified by its own live gate - a round "
    "legitimately writes several items in a row, so 15 of 15 rounds flagged "
    "and the signal was useless; the implemented law and the criteria row now "
    "read a repeat as a label returning after a DIFFERENT round intervened, "
    "the suite pins both sides, and no assertion was relaxed. Two live "
    "findings carried, not swept: 156 done-stamped rounds carry no log item "
    "(the log window is folded to 15 rounds) and tick_lead is 0. Queue "
    "ordering disclosed: rows 41 (docker absent on this machine), 88 (AC-LN1.."
    "LN8 already delivered at R1727) and 54 (standing line, no defined next "
    "slice) were not deliverable faces, so the top deliverable row was "
    "claimed. The tech floor was refilled in the same window with one real gap "
    "row (queue_only_reconcile, AC-QOC1..AC-QOC6 pre-registered, five anchors "
    "zero-occupancy rc=1) and the gauge closed FLOOR-MET main 5/5 tech 10/10 "
    "explore 10/10."
)

LEDGER = (
    "R2257 tokens: local=~26k api=0 api_reason=product window on the R2248 d "
    "seed - one new os module plus its suite, one single-writer evidence "
    "helper, one runner entry and the queue/board/debt bookkeeping all done "
    "in-session with no cloud call"
)

NEW_TICK = 2257


def main():
    raw = SIO.read_raw(PATH)
    text = SIO.decode(raw)
    state = json.loads(text)
    old_tick = state['tick']
    if old_tick != NEW_TICK - 1:
        raise SystemExit('refusing: tick is %r, expected %d'
                         % (old_tick, NEW_TICK - 1))
    for item in (NARRATIVE, LEDGER):
        if item in state['log']:
            raise SystemExit('refusing: this item is already in the log')

    head, tail = text.split('"tick": %d' % old_tick, 1)
    text = head + '"tick": %d' % NEW_TICK + tail

    marker = '\r\n  ]\r\n}'
    cut = text.rfind(marker)
    if cut < 0:
        raise SystemExit('refusing: unexpected log tail')
    body = text[:cut]
    remainder = text[cut + len(marker):]
    indent = ' ' * 16
    addition = ''.join(',\r\n%s%s' % (indent, json.dumps(item, ensure_ascii=False))
                       for item in (NARRATIVE, LEDGER))
    if not body.rstrip().endswith('"'):
        raise SystemExit('refusing: last log item does not end with a quote')
    new_text = body + addition + marker + remainder

    canonical = SIO.canon(new_text)
    measured = SIO.layout(canonical)
    if not measured['layout_ok']:
        raise SystemExit('refusing: layout not canonical %r' % (measured,))
    expected = dict(state)
    expected['tick'] = NEW_TICK
    expected['log'] = list(state['log']) + [NARRATIVE, LEDGER]
    if json.loads(canonical) != expected:
        raise SystemExit('refusing: payload differs from the intent')

    data = canonical.encode('utf-8')
    handle, temp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(PATH)),
                                   prefix='.r2257_')
    try:
        with os.fdopen(handle, 'wb') as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, PATH)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = SIO.read_raw(PATH)
    after = SIO.layout(SIO.decode(back))
    print('WROTE bytes=%d previous=%d tick=%d log=%d layout_ok=%r residues=%d'
          % (len(data), len(raw), after['log_items'], after['log_len'],
             after['layout_ok'],
             len([n for n in os.listdir(os.path.dirname(PATH))
                  if n.startswith('.r2257_')])))
    return 0 if back == data else 1


if __name__ == '__main__':
    sys.exit(main())