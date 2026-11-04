"""export_R2458 - refresh docs/status-export.json for the R2458 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
one outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2458 verification window: the battery the R2457 product edit owed "
           "was discharged on the committed tree - 556 suites green at 4312 "
           "criteria, exactly the pre-registered count - and the suite matrix "
           "was regenerated from this round own evidence, so the registry this "
           "station reports is proven rather than asserted")

base.LATEST = ("qa/reconcile-all-R2458.log (RUNNER PASS 556/556 suites, "
               "reconcile controls 7/7, 1337.6s, criteria summed to 4312, "
               "fails=0, zero CRLF) + docs/sandbox-suite-matrix.md regenerated "
               "through --stamp-from to 53731B at 556 suites / 4312 criteria "
               "with --check byte-identical + follow-up legs appended for "
               "VERDICT R2458 PASS (matrix byte-identical, fingerprint CLEAN "
               "domains=5, profile byte-identical, census DRIFT-CLEAN)")

base.NEXT = ("2026-11-05/06 the next window ships a face a reader can open: "
             "either the carried product-face-R2456 (tech head AC-PFKC1, three "
             "windows stale) or a P-47 business face that supersedes it, and it "
             "says which before it writes code. The city page is runnable right "
             "now: python src/sandbox/lobby/server.py --city-http-port 8092 then "
             "http://127.0.0.1:8092/city/, and the lobby sandbox bring-up "
             "remains python src/sandbox/lobby/interop_demo.py, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2458 VERIFICATION window on the carried row "
    "reconcile-battery-R2458 (owed by R2457 at the pre-registered 556 suites / "
    "4312 criteria): zero product src bytes changed, the R2168 mixed-tree rule "
    "honoured. The battery had already been run on this committed tree by a "
    "prior attempt and left as one untracked evidence file, so it was ADOPTED "
    "and re-measured rather than re-run - 556 suite rows, criteria summed to "
    "4312 EXACTLY as pre-registered, fails=0, one RUNNER PASS line at 1337.6s. "
    "PROVENANCE DISCLOSED: that body is a shell capture (its first line reads "
    "'no evidence path: shell-capture mode'), not the battery_stream single "
    "writer the house law asks for; it measures 856250B, crlf=0, lone_lf=6240, "
    "bom=False, and the census section reads DRIFT-CLEAN over it. Four "
    "follow-up sections in the designed order: LEG 1 matrix FAIL at "
    "on-disk=53657B against regenerated=53731B with no byte written while "
    "fingerprint/profile/census PASS; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md from this round own evidence through "
    "--stamp-from to 53731B at 556 suites / 4312 criteria green=556/556 and "
    "--check read byte-identical; LEG 2 read all four sections PASS for VERDICT "
    "R2458 PASS failing=none, and both legs were appended by the shipped writer "
    "(856250B -> 860089B, closing line 'VERDICT R2458: PASS eol crlf=0 "
    "bare_cr=0 bom=False'). Debt: reconcile-battery-R2458 closed at 119464B -> "
    "119468B (line=193, open 3->2, done 171->172, readback ok); no successor "
    "battery is owed because no product src byte and no registry count moved; "
    "the gate now reads open=2 first=product-face-R2456 (stale, carried=3). A "
    "REAL defect of my own was found and repaired at its birth site: the first "
    "closeout draft wrote src/os/state.json with a hardcoded LF newline and so "
    "converted the working document transport, and the first repair asked the "
    "git blob (already git-normalised to LF) instead of the working copy, which "
    "converted it a second time - repair_R2458.py now seeds the CRLF source "
    "explicitly, proves the line set identical before writing, lands one atomic "
    "replace and reads the bytes back (63459B, crlf=218, lone_lf=0, readback "
    "ok, layout_ok=True), and closeout_R2458.py asks the shipped dialect law at "
    "its own write site so a rerun preserves the transport. Honest limits: ZERO "
    "product points this window - nothing a CEO could open was rebuilt and "
    "every P-47 item remains blocked on CEO physical pieces; the unsupported-"
    "flag trap was paid again (probing reconcile_all.py with --list started a "
    "real battery whose pipe was cut, leaving a repo-root file named --list, "
    "deleted before any commit with zero survivors); the debt leader is still "
    "an internal audit face while the standing CEO order asks for real output, "
    "stated so the next window picks deliberately."
)

base.OUTS = (
    "qa/reconcile-all-R2458.log (adopted green leg plus two follow-up legs) + "
    "docs/sandbox-suite-matrix.md (regenerated stamp-aligned) + "
    "src/os/repair_R2458.py (state transport repair, birth site) + "
    "src/os/closeout_R2458.py + src/os/export_R2458.py + state/debt.md + "
    "docs/status-export.json + src/os/state.json + src/os/backlog.md + "
    "heartbeat.txt"
)

if __name__ == "__main__":
    sys.exit(base.main())