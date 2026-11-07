"""R2533 state append: the product window on the AC-PCSC1 face."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-07 R2533 PRODUCT window on the tech head the register named "
    "(product-face-R2532, state/queue/tech.md:569 prefix AC-PCSC1, criteria "
    "AC-PCSC1..AC-PCSC6 pinned in that row at R2531 BEFORE any code). Opened "
    "directly on the gate read CLAIM-FIRST product-face-R2532 first=1 with a "
    "clean tree at HEAD b040a3e3, no index.lock, decisions new=0 over the "
    "stored baseline and zero unreplied @BigDomain ledger rows (the same "
    "session chain that read them minutes earlier in R2532, re-read here "
    "rather than assumed); benchmarks 2026-11-03 inside the seven-day gate. "
    "CLAIM: MEASURED at R2531 that a for-loop over a constant SUBSCRIPT of a "
    "container name reads refused=subscript and is never followed even when "
    "the dict and its tuple are both in the table, and that a multi-target "
    "loop is not read and named NOWHERE. SHIPPED "
    "src/os/probe_seam_subscript_container_scope.py plus its six-criteria "
    "suite: a subscript one constant key deep on a NAME container or on a "
    "same-root module chain resolves ONLY when the result holds exactly one "
    "element and carries the chain WITH its key; a two-element result is NAMED "
    "ambiguous, a missing key is NAMED with the key and the container, a "
    "non-literal key is NAMED key and never guessed, a broken hop is NAMED "
    "with the hop, a call base and a comprehension are NAMED and never "
    "evaluated, and a MULTI-TARGET loop is now NAMED multi-target:a,b instead "
    "of being ignored. The shipped container-name tables and law are asked "
    "FIRST and never overwritten and the seam classifier is still the shipped "
    "registry single quiets. PROOF: AC-PCSC1..AC-PCSC6 SUITE PASS 6/6 TWICE "
    "with byte-identical output, exit 0 on both legs, plus five adjacent probe "
    "suites green (container name, alias expression, annotated constant, "
    "dynamic import, registry) "
    "(qa/probe-seam-subscript-container-scope-R2533.log, 28328B, bom=False "
    "crlf=0, legs=2 identical=True fails=0 adjacent=5), and a live leg on the "
    "REAL tree reading SEAMS-SUBSCRIPT-COVERED over 1437 probes (3 covered, "
    "176 out-of-scope, 1258 historical, missing=0) with the module, the base "
    "face and the render digests all unchanged. REGISTRY 595/4546 -> 596/4552 "
    "by exactly one row os-probe-seam-subscript-container-scope(6), recounted "
    "by importing reconcile_all.SUITES; docs/sandbox-suite-matrix.md "
    "regenerated stamp-aligned from the eligible battery leg "
    "qa/reconcile-all-R2532.log to 57459 bytes at 596 suites / 4552 criteria "
    "with green=595/596 self-describing and --check byte-identical (the note in "
    "the board row first read 57386 and was corrected to the measured 57459 in "
    "the same window rather than left standing). DEBT through the shipped "
    "writers: product-face-R2532 closed (line 263, open 14->13, done 231->232, "
    "162181B -> 162184B, readback ok), reconcile-battery-R2533 opened first=yes "
    "(162184B -> 162795B, readback ok) at the pre-registered 596 suites / 4552 "
    "criteria so the next window owes ONE battery on this committed tree BEFORE "
    "any further product byte, and product-face-R2533 opened first=no "
    "(162795B -> 163107B, readback ok) naming tech line 571 prefix AC-PCNS1. "
    "BOARD: the AC-PCSC1 row was closed through queue_close_R2533.py (line 568, "
    "predicted 1716477B = measured 1716477B, delta 4396, readback ok) and ONE "
    "row seeded from this window own measured limit with AC-PCNS1..AC-PCNS6 "
    "pre-registered and five anchors re-checked at zero occupancy, so "
    "queue_floor reads FLOOR-MET 5/5 11/10 10/10 and the head is line 571.",

    "2026-11-07 R2533 honest disclosures: (a) ONE product point on the "
    "Executive Protocol scale - a shipped reading with its own suite and CLI "
    "that a maintainer can run, but nothing a CEO could newly open; no business "
    "surface moved; (b) TWO defects were measured in my own first pass and "
    "fixed in the CODE rather than in the assertions: a dict of TUPLES is not "
    "in the shipped tables at all because those tables refuse a nested "
    "container, so the subscript base had to be read off the literal the source "
    "declares, and my first key label printed ... for a bare name instead of "
    "the name, which hid which key broke; (c) ONE assertion was corrected "
    "against measurement, not loosened: a format call iterable is NAMED format "
    "by the shipped law rather than string; (d) the board row DISCHARGED note "
    "was written with a predicted matrix byte count of 57386 and the measured "
    "document is 57459, so the number was corrected in place in the same window "
    "and the correction is disclosed here rather than buried; (e) the helper "
    "walk is the shipped container-name walk, so a helper that itself binds its "
    "import through a subscript is a stated gap in the module docstring; (f) a "
    "two-key chain (a dict of dicts) and a key followed by an index are still "
    "refused as nested and name no hop - measured this window and seeded as the "
    "next row; (g) Docker is absent on this host, the real 19.9 debit and the "
    "real msgSecCheck still wait on CEO physical items, and the S4U lane "
    "reconcile still needs an elevated shell; (h) tasks.md was not touched.",

    "R2533 tokens: local=~14k api=0 api_reason=product window - one debt gate "
    "read, one tree and HEAD check, one content-addressed decisions scan "
    "reading new=0, one pre-registered face shipped with its six criteria, one "
    "suite proved twice with identical output plus five adjacent suites, one "
    "limit measurement that became the next seed row, one live leg on the real "
    "tree with three digests unchanged, one evidence capture normalised to LF "
    "at capture time and cleared by the shipped writer census, one registry row "
    "recounted by import, one stamp-aligned matrix regeneration checked "
    "byte-identical with its byte count corrected in the board note, one queue "
    "row closed and one seeded through their shipped writers, three debt rows "
    "moved through their shipped writers, and the state/export/backlog/"
    "heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2533
    state["log"].extend(LINES)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"])
          and back["tick"] == 2533
          and back["log"][-1] == LINES[-1])
    print("state %s tick=%s log=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             os.path.getsize(PATH), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())