"""Derived-counter-only export refresh (R2071 addendum: the proposal
line moved proposals_total/open before the counter pass)."""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

sys.path.insert(0, HERE)
from check_export_consistency import recompute  # noqa: E402

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()
before = json.loads(text)

derived, _s, _e, _p = recompute()
keys = ("window", "window_days", "log_lines_in_window",
        "idle_fast_mention_lines", "no_pullable_mention_lines",
        "substantive_non_idle_mention_lines", "queue_main_open",
        "queue_tech_open", "queue_explore_open", "proposals_total",
        "proposals_open")
for key in keys:
    value = derived[key]
    if isinstance(value, str):
        pattern = r'"%s": "(?:[^"\\\\]|\\\\.)*"' % key
        repl = '"%s": "%s"' % (key, value)
    else:
        pattern = r'"%s": \d+' % key
        repl = '"%s": %d' % (key, value)
    text, n = re.subn(pattern, repl, text)
    if n < 1:
        sys.exit("FATAL: derived key %s not found" % key)

after = json.loads(text)
assert after["export_ts"] == before["export_ts"]
assert after["ceo_face"] == before["ceo_face"]
assert after["results"] == before["results"]
assert after["self_drive"]["proposals_total"] == \
    derived["proposals_total"]
with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("EXPORT-COUNTERS-OK proposals=%d/%d queues=%d/%d/%d"
      % (derived["proposals_total"], derived["proposals_open"],
         derived["queue_main_open"], derived["queue_tech_open"],
         derived["queue_explore_open"]))