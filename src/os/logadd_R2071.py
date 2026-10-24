# -*- coding: utf-8 -*-
"""Fold the in-window self-drive proposal into the R2071 state log
(surgical, anchored on the LAST occurrence because R2070 closes with
the same sentence)."""
import json

ST = 'src/os/state.json'
raw = open(ST, encoding='utf-8', newline='').read()
before = json.loads(raw)

old_tail = " blocked on CEO physical items). Score 2."
new_tail = (" blocked on CEO physical items). The window also carried the"
            " weekly self-drive proposal BD-PROP-005 (a change-scoped"
            " battery with its three-question criteria, pilot window"
            " 10-25..10-31), so the proposal quota for the closing window"
            " is cleared. Score 2.")
pos = raw.rfind(old_tail)
assert pos > 0
raw = raw[:pos] + new_tail + raw[pos + len(old_tail):]

old_tok = ("+ evidence log + state layout repair + state/export"
           " closeout, zero cloud calls")
new_tok = ("+ evidence log + state layout repair + proposal BD-PROP-005"
           " + state/export closeout, zero cloud calls")
pos2 = raw.rfind(old_tok)
assert pos2 > 0
raw = raw[:pos2] + new_tok + raw[pos2 + len(old_tok):]

after = json.loads(raw)
assert after['tick'] == before['tick'] == 2071
assert len(after['log']) == len(before['log'])
assert 'BD-PROP-005' in after['log'][-2]
assert 'BD-PROP-005' in after['log'][-1]
assert after['log'][-3] == before['log'][-3]
open(ST, 'w', encoding='utf-8', newline='').write(raw)
print('state log addendum folded')