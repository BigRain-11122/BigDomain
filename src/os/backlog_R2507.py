"""R2507 backlog + heartbeat closeout.

Marks the carried R2507 row done, inserts the next carried row (the battery the
register owes this window), and appends one heartbeat row in the file's own
transport (UTF-16LE with CRLF, as the shipped file already carries). ASCII
source, stdlib only, no network, no clock.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")

OLD_HEAD = "- [ ] [carried 2026-11-07 R2506] R2507 first item:"
DONE_HEAD = "- [x] [done 2026-11-07 R2507] [was carried 2026-11-07 R2506]"

CARRIED = (
    "- [ ] [carried 2026-11-07 R2507] R2508 first item: THE BATTERY ON THE "
    "COMMITTED TREE, zero product edits until green (the R2168 mixed-tree "
    "rule), pre-registered at 583 suites / 4474 criteria - exactly what this "
    "window measured by importing reconcile_all.SUITES after wiring one row - "
    "and any larger delta must be named rather than swept. Run the full "
    "reconcile battery with an empty git status before the run, launch it "
    "detached and unfiltered through src/os/battery_stream.py (the "
    "filtering-pipe trap has cost earlier windows their whole run), keep the "
    "red leg if it goes red, then the four follow-up sections through "
    "src/os/battery_followup.py (its matrix section FAILS first on a stale doc "
    "by design and must NOT rewrite it; regenerate with "
    "src/sandbox/suite_matrix.py after, stamp-aligned from this round own "
    "green evidence). On green go back to the product face the queue head "
    "names - re-read it with `python src/os/queue_head.py --head tech`, which "
    "this window left at state/queue/tech.md:547 prefix AC-EVNM1 "
    "evidence_name_text_coverage (the artifact also prints the evidence file "
    "NAME and the coverage probe hands the render a constant there, measured "
    "this window: a copy of the real evidence named with U+FFFD rendered into "
    "the document with the codepoint carried while the reading still read "
    "publishable=True, qa/adtr-evidence-name-live-R2507.log) - ship ONE face "
    "with its pre-registered suite, refill the tech floor if claiming drops "
    "claimable below 10, and commit BEFORE any battery. NOTE measured many "
    "times: a commit that moves the queue must also re-derive "
    "docs/status-export.json and land its queue block through "
    "queue_export_gate_wire --execute, otherwise the next battery reads the "
    "queue face STALE. Also open and needing an ELEVATED shell: "
    "BigDomain-OSLoop exists but its Principal.LogonType still reads "
    "InteractiveToken, which the 2026-09-29 machine law forbids for every lane "
    "task (carried as the stale row loop-s4u-reconcile)."
)

HEARTBEAT = ("2507 tick 2507 product face: artifact disk-text readability "
             "shipped and wired, suite 6/6 twice, registry 583/4474, matrix "
             "restamped 56095B, live leg CLEAN over 1226 strings\r\n")


def main():
    text = io.open(BACKLOG, encoding="utf-8").read()
    if text.count(OLD_HEAD) != 1:
        print("FAIL backlog anchor: %d" % text.count(OLD_HEAD))
        return 2
    head_done = text.replace(OLD_HEAD, DONE_HEAD, 1)
    payload = head_done.replace("\n", CARRIED + "\n", 1)
    with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(BACKLOG, encoding="utf-8").read().split("\n")
    ok = (back[0].startswith("- [x] [done 2026-11-07 R2507]")
          and back[1].startswith("- [ ] [carried 2026-11-07 R2507] R2508"))
    print("backlog %s head=%r carried=%r"
          % ("OK" if ok else "FAIL", back[0][:40], back[1][:40]))

    raw = open(HEARTBEAT, "rb").read()
    beat = raw.decode("utf-16")
    if "tick 2507" in beat:
        print("NOOP heartbeat already carries tick 2507")
        return 0 if ok else 2
    beat = beat + HEARTBEAT
    with open(HEARTBEAT, "wb") as handle:
        handle.write(beat.encode("utf-16"))
    again = open(HEARTBEAT, "rb").read().decode("utf-16")
    hb_ok = again.rstrip().endswith("1226 strings")
    print("heartbeat %s bytes=%d"
          % ("OK" if hb_ok else "FAIL", len(open(HEARTBEAT,
                                                 "rb").read())))
    return 0 if (ok and hb_ok) else 2


if __name__ == "__main__":
    sys.exit(main())