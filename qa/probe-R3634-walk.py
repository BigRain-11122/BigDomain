"""Read-only probe: how many archive walks does one evidence run take?"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "src", "os"))

import fold_carry_census as FCC
import ledger_lines as LL

CALLS = []
REAL = LL.load_archive_windows


def counting(path):
    CALLS.append(os.path.basename(path))
    return REAL(path)


LL.load_archive_windows = counting
paths = LL.archive_files(LL.default_logs_dir(FCC.STATE))
report = FCC.evidence()
LL.load_archive_windows = REAL

per_path = {}
for name in CALLS:
    per_path[name] = per_path.get(name, 0) + 1
print("WALK archives_on_disk=%d" % len(paths))
print("WALK calls_total=%d calls_per_path=%s"
      % (len(CALLS), ",".join("%s:%d" % (k, per_path[k])
                              for k in sorted(per_path))))
print("WALK report frozen=%d law_excused=%d"
      % (len(report["frozen_rounds"]), report["law_excused"]))
