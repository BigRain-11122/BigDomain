"""one-off measurement for R2501 seeds: the difference law's order blindness."""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_closeout_gate_parity as ECGP  # noqa: E402

left = json.dumps({"x": 1, "y": 2}, indent=2) + "\n"
right = json.dumps({"y": 2, "x": 1}, indent=2) + "\n"
print("LEFT=%r" % left)
print("ORDER-ONLY DIFFERENCE READS -> %r" % ECGP.first_difference(left, right))
print("A REAL VALUE DIFFERENCE READS -> %r"
      % ECGP.first_difference(left, json.dumps({"x": 1, "y": 3}, indent=2) + "\n"))