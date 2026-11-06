"""R2491 one-off: independent recount over the retry battery's own rows."""

import io
import re

PATH = "qa/reconcile-all-R2491-retry.log"
raw = io.open(PATH, "rb").read()
text = raw.decode("utf-8")
rows = [line for line in text.splitlines() if line.startswith("PASS suite ")]
fails = [line for line in text.splitlines() if line.startswith("FAIL suite")]
total = 0
counted = 0
for line in rows:
    match = re.search(r"criteria=(\d+)", line)
    if match:
        total += int(match.group(1))
        counted += 1
print("bytes=%d bom=%s crlf=%d lone_cr=%d" % (
    len(raw), raw[:3] == b"\xef\xbb\xbf", raw.count(b"\r\n"),
    raw.count(b"\r") - raw.count(b"\r\n")))
print("pass_rows=%d counted=%d criteria_sum=%d fail_rows=%d" % (
    len(rows), counted, total, len(fails)))
print("closing=%s" % text.splitlines()[-1])