# -*- coding: utf-8 -*-
"""R2188: correct three arithmetic expectations in the new suite.

The seed declares d1=3, d2=2, d4=5, d5=1 tracked units (11, not 13)
and the pre-unlimited net sales total is 5 (d1 two, d2 two, d5 one).
"""
import io

P = "src/sandbox/ledger/test_apimarket_sellersupply.py"
s = io.open(P, encoding="utf-8").read()

REPS = [
    ('and retired_env["total_effective_supply"] == 13',
     'and retired_env["total_effective_supply"] == 11'),
    ('ok4 = (shelf["total_effective_supply"] == 13',
     'ok4 = (shelf["total_effective_supply"] == 11'),
    ('and shelf["total_remaining"] == 13',
     'and shelf["total_remaining"] == 11'),
    ('and steps["d5_sold_out"]["total_sold"] == 6',
     'and steps["d5_sold_out"]["total_sold"] == 5'),
    ('and after_unlimited["total_sold"] == 7',
     'and after_unlimited["total_sold"] == 6'),
]
for old, new in REPS:
    assert s.count(old) == 1, (old, s.count(old))
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("FIX OK")