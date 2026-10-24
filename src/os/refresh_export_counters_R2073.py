"""Re-apply the derived counters to the export face (counter-only
refresh, no new results row). Pure ASCII source."""

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

json.loads(text)
with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("COUNTERS-OK " + " ".join(
    "%s=%r" % (k, derived[k]) for k in keys))