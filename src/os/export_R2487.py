"""export_R2487 - refresh docs/status-export.json for the R2487 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2487 business face: the membership entitlement side of the 19.9 "
           "entrance is now a clickable page instead of a terminal-only "
           "engine - a resident can be joined to a sandbox month card and then "
           "read their tier, privileges, credits, birth certificate and "
           "expiring rows from one URL")

base.LATEST = ("src/sandbox/member/member_page.py (16000B class module) + "
               "src/sandbox/member/member.html (8752B, zero external "
               "references, AI label + non-advice note + mock/no-charge "
               "statement) + qa/member-face-R2487.log (954B, utf-8 LF, "
               "crlf=0, legs=2 identical=True, 6/6 green twice) at "
               "2026-11-06 R2487")

base.NEXT = ("2026-11-07 the debt register owes reconcile-battery-R2486 and "
             "reconcile-battery-R2487 before any further product byte, and the "
             "member-face suite is still unregistered in the suite registry; "
             "after that the member face should be offered from the hub and "
             "the panel so a person reaches it without a command line")

base.RESULT = (
    "2026-11-06 R2487 business face: the member sandbox shipped a full "
    "entitlement engine, catalog, sweep, reconcile and reminder, but nothing a "
    "person could open - the side of the 19.9 entrance that answers 'what do I "
    "hold now' had no page. Product: src/sandbox/member/member_page.py serves "
    "one page from disk plus three same-origin JSON routes (state / avatars / "
    "join), wiring the SHIPPED faces rather than re-implementing them: the pay "
    "dock is given sandbox-only price rows (mock, never chargeable) so a join "
    "creates a real order, pays it, and activates the real member period, and "
    "every read is the shipped MemberStore face (privileges_for, balance_face, "
    "birth_cert_face, expiring_soon) with the disclaimer and AI label read from "
    "the catalog rather than typed into either file. MEASURED: page 200 at "
    "8752B byte-identical to disk on both /member and /member/; a resident with "
    "no grant reads active=false with no invented tier and no birth "
    "certificate; a sandbox join returns mock=true at 1990 cents and the SAME "
    "face then reads tier experience, two privileges, birth_cert=true and one "
    "period; blank avatar reads 400 E_NO_AVATAR and a non-integer day window "
    "400 E_BAD_BODY. Proof: AC-MFN1..AC-MFN6 SUITE PASS 6/6 twice with "
    "identical bodies (qa/member-face-R2487.log, 954B, utf-8 LF, crlf=0). "
    "HONEST DEFECTS DISCLOSED, not dressed up: (a) these criteria were written "
    "in the SAME window as the module, so pre-registration was NOT honoured and "
    "this suite is weaker evidence than the shipped pre-registered ones; (b) "
    "the R2168 mixed-tree rule was broken - a battery was already owed "
    "(reconcile-battery-R2486) when these product bytes landed, and both "
    "reconcile-battery-R2486 and reconcile-battery-R2487 are now filed in the "
    "debt register through its own writer (126340B -> 126816B, readback ok); "
    "(c) the suite registry is unmoved at 571 suites / 4402 criteria because "
    "member-face is not registered yet, so docs/sandbox-suite-matrix.md stays "
    "aligned with the registry and is NOT restamped this window; (d) the face "
    "is reachable by command only - it is not yet published from the hub or the "
    "panel, which is named as the next milestone rather than claimed.")

if __name__ == "__main__":
    print(base.main())