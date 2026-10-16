# fix_comma_R2008.py - one-byte surgical fix: the closeout
# append missed the comma between the fold R540 rolling line
# and the R2008 round line (R2006/R2007 same-pit precedent
# family: fix_comma_R2006.py / fix_comma_R2007.py).
# ASCII only.
import io
import json

P = r"src\os\state.json"

b = io.open(P, "rb").read()
anchor = (b'T-DOUBLE"\r\n                '
          b'"2026-10-17 R2008')
assert b.count(anchor) == 1, "anchor count %d" % b.count(anchor)
fixed = b.replace(
    anchor,
    b'T-DOUBLE",\r\n                "2026-10-17 R2008')
io.open(P, "wb").write(fixed)

st = json.loads(io.open(P, encoding="utf-8").read())
print("JSON OK tick=%d log=%d bytes=%d"
      % (st["tick"], len(st["log"]), len(fixed)))
print("last3 heads:",
      [l[:16].encode("ascii", "replace").decode("ascii")
       for l in st["log"][-3:]])
