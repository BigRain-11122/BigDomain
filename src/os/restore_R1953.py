"""R1953 prep: restore the crashed [1] evidence section to disk
(normalized LF) before the closeout re-run. The first takeover
driver attempt appended its addendum + a hardcoded-PASS ruling to
the file even though its steps failed (dialect-timing chain);
this restore truncates the file back to the crashed round's [1]
content (CRLF->LF normalized per the R1884 capture law), so the
re-run appends onto the honest base. Pure ASCII, stdlib only."""

import io
import os

P = os.path.join("qa", "sistercity-persist-R1953.log")
raw = io.open(P, "rb").read().decode("utf-8")
marker = "\n--- [7] takeover addendum"
i = raw.find(marker)
assert i > 0, "addendum marker not found"
head = raw[:i]
assert head.rstrip().endswith("verdict PASS"), "head tail mismatch"
assert "\r" not in head, "CR in restored head"
assert head.count("PASS AC-SCP") == 7, "seven AC lines expected"
assert "SUITE PASS 7/7" in head, "suite pass line expected"
io.open(P, "wb").write(head.encode("utf-8"))
print("restored: %d bytes, ends with verdict PASS, pure LF"
      % len(head.encode("utf-8")))
