# hb_fix_R2017.py - same-round heartbeat row format repair
# (scan_five_still [HB] parser expects "tick N" in the last
# row per standing law R532; the R2016-onward row format
# dropped the "| BigDomain OSLoop alive | tick N |" segment,
# leaving a standing FLAG). Edit-in-place of the row appended
# by THIS round only (same-round fix, R2015 precedent
# family); CRLF layout preserved byte-exact elsewhere.
import io

P = "heartbeat.txt"
OLD = u"2026-10-17 20:2x +08:00R2017:"
NEW = (u"2026-10-17 20:2x +08:00 | BigDomain OSLoop alive"
       u" | tick 2017 | R2017:")

raw = io.open(P, encoding="utf-8", newline="").read()
assert raw.count(OLD) == 1, "anchor not unique: %d" % raw.count(OLD)
fixed = raw.replace(OLD, NEW, 1)
assert fixed != raw
io.open(P, "w", encoding="utf-8", newline="").write(fixed)
print("hb row fixed: tick token restored (R2017 row)")
