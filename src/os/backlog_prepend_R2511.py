"""R2511 backlog prepend: mark the R2511 item discharged and carry the next one.

Reads src/os/backlog.md as UTF-8 LF, replaces the carried R2511 line marker,
appends its discharge bracket, and prepends the R2512 item. ASCII source.
"""
import io
import sys

P = "src/os/backlog.md"
OLD_MARK = "- [ ] [carried 2026-11-07 R2510] R2511 first item:"
NEW_MARK = "- [x] [done 2026-11-07 R2511] R2511 first item:"

DISCHARGE = (
    " [DISCHARGED at R2511: src/os/stamp_text_coverage.py plus its suite "
    "shipped and suite_matrix.render asks it one statement after the "
    "evidence-name seam at both the check path and the generate path, "
    "refusing at exit 4 with FAIL stamp-text naming the piece and the value "
    "and opening no artifact byte. AC-STPT1..AC-STPT6 SUITE PASS 6/6 TWICE "
    "identical plus three adjacent readability suites green "
    "(qa/stamp-text-coverage-R2511.log legs=2 identical=True fails=0 "
    "adjacent=3 digest 52ADD8ADF4C4F5A3) and a live leg on the REAL tree "
    "reading CLEAN with a doctored stamp and a doctored stamp_from each "
    "refused and both digests unchanged "
    "(qa/stamp-text-coverage-live-R2511.log). The first suite run was RED on "
    "two real counts and both were repaired at the birth site: the committed "
    "matrix doc still carried 584 registry rows against the new 585 "
    "(regenerated stamp-aligned at 56263B over 585 suites / 4486 criteria "
    "with --check byte-identical) and this module docstring named the borrow "
    "path literally, which AC-STPT4 caught (reworded). "
    "artifact_disk_text_readability and evidence_name_text_coverage also "
    "learned to read the new seam off the module instead of freezing the "
    "seam names they shipped with. Registry moved 584/4480 -> 585/4486 by "
    "exactly one row. Queue row 549 closed and one seed pinned from this "
    "window own birth-site repair (probe_seam_registry, head line 551 prefix "
    "AC-PSMR1) refilling the floor to claimable=10. Debt: product-face-R2510 "
    "closed, reconcile-battery-R2511 opened first=yes at 585/4486, "
    "product-face-R2511 opened first=no.]"
)

NEW_ITEM = (
    "- [ ] [carried 2026-11-07 R2511] R2512 first item: THE BATTERY ON THE "
    "COMMITTED TREE, zero product edits until green (the R2168 mixed-tree "
    "rule), pre-registered at 585 suites / 4486 criteria - exactly what R2511 "
    "registered when it moved the registry by one row - and any larger delta "
    "must be named rather than swept. Run the full battery with an empty git "
    "status before the run, launch it detached and unfiltered through "
    "src/os/battery_stream.py (the filtering-pipe trap has cost earlier "
    "windows their whole run), keep the red leg if it goes red, then the four "
    "follow-up sections through src/os/battery_followup.py (its matrix "
    "section FAILS first on a stale doc by design and must NOT rewrite it; "
    "regenerate with src/sandbox/suite_matrix.py after, stamp-aligned from "
    "this round own green evidence). On green go back to the product face the "
    "register names next - re-read it with `python src/os/queue_head.py "
    "--head tech`, which R2511 left at state/queue/tech.md:551 prefix "
    "AC-PSMR1 probe_seam_registry: two shipped probes had to be hand-repaired "
    "in the same window that wired the fifth guard seam, so a reading that "
    "derives the seam set from the module and names any probe that falls "
    "behind is the next face. NOTE measured many times: a commit that moves "
    "the queue must also re-derive docs/status-export.json and land its queue "
    "block through queue_export_gate_wire --execute, otherwise the next "
    "battery reads the queue face STALE. Also open and needing an ELEVATED "
    "shell: BigDomain-OSLoop exists but its Principal.LogonType still reads "
    "InteractiveToken, which the 2026-09-29 machine law forbids for every "
    "lane task (carried as the stale row loop-s4u-reconcile).\n"
)

raw = io.open(P, "rb").read()
text = raw.decode("utf-8")
if raw.count(b"\r\n"):
    print("FAIL crlf present")
    sys.exit(2)
count = text.count(OLD_MARK)
if count != 1:
    print("FAIL marker hits=%d" % count)
    sys.exit(2)
lines = text.split("\n")
hit = None
for index, line in enumerate(lines):
    if line.startswith(OLD_MARK):
        hit = index
        break
lines[hit] = NEW_MARK + lines[hit][len(OLD_MARK):] + DISCHARGE
lines.insert(hit, NEW_ITEM.rstrip("\n"))
out = "\n".join(lines)
io.open(P, "w", encoding="utf-8", newline="").write(out)
after = io.open(P, "rb").read()
print("ok lines=%d bytes=%d crlf=%d marker_left=%d"
      % (len(lines), len(after), after.count(b"\r\n"),
         after.decode("utf-8").count(OLD_MARK)))
sys.exit(0 if after.count(b"\r\n") == 0 else 1)