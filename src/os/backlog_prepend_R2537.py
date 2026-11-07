"""R2537 backlog prepend: one done row, proved by read-back.

Idempotent: refuses to prepend twice. Writes once through one atomic replace
and keeps the file LF (it is LF today and must stay LF).
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "backlog.md")

DONE = (
    "- [x] [done 2026-11-07 R2537] R2537 PRODUCT window on the tech head the "
    "register named (product-face-R2536, state/queue/tech.md:573 prefix "
    "AC-PNKB1 probe_seam_nested_key_binding_scope, criteria AC-PNKB1..AC-PNKB6 "
    "pinned there at R2535 BEFORE any code). Five-silence scan clean at HEAD "
    "4197d87b (git status empty, no index.lock, zero @BigDomain ledger rows, "
    "content-addressed decisions diff new=0 over the stored baseline at a "
    "measured 147 file tokens in 115 rows, group orders tail unchanged, "
    "benchmarks 2026-11-03 inside the seven-day gate); the debt gate read "
    "CLAIM-FIRST product-face-R2536 with no battery owed, queue line 573 was "
    "claimable=11 with the floor MET, and all five pinned anchors were "
    "re-checked at zero occupancy by git grep before any code. SHIPPED "
    "src/os/probe_seam_nested_key_binding_scope.py plus its six-criteria "
    "suite: a for-loop step that is a NAME bound to a string constant now "
    "resolves at CALL time in the module body and in function bodies and the "
    "chain carries BOTH the key value and the binding label "
    "(D['a'][KEY='b']); an annotated binding, a walrus step and a "
    "walrus-bound name resolve too; a twice-bound name is NAMED "
    "ambiguous@hopN and never resolved to either value; a name bound to a "
    "call, a format or a comprehension is NAMED at its hop and nothing is "
    "ever evaluated; a two-element result stays ambiguous. The shipped "
    "nested-subscript law is asked FIRST and never overwritten and the seam "
    "classifier is still the shipped registry single quiets. PROOF: "
    "AC-PNKB1..AC-PNKB6 SUITE PASS 6/6 TWICE with a byte-identical digest plus "
    "five adjacent probe suites green "
    "(qa/probe-seam-nested-key-binding-scope-R2537.log, 9107B, legs=2 "
    "identical=True fails=0 adjacent=5), and a live leg on the REAL tree "
    "reads SEAMS-NESTED-KEY-COVERED over 1457 probes (3 covered, 179 "
    "out-of-scope, 1275 historical, missing=0) with three digests unchanged "
    "and the SAME fixture followed here while the shipped nested face still "
    "reads refused=key@hop2 "
    "(qa/probe-seam-nested-key-binding-scope-live-R2537.log, 618B, class=tee). "
    "REGISTRY 597/4558 -> 598/4564 by exactly one row, recounted by importing "
    "reconcile_all.SUITES; docs/sandbox-suite-matrix.md restamped "
    "stamp-aligned from the eligible battery leg qa/reconcile-all-R2536.log "
    "to 57696 bytes with green=597/598 self-describing and --check "
    "byte-identical after a designed dry-run FAIL that wrote no byte. BOARD: "
    "row 573 closed at its predicted and measured 1726133B and one row seeded "
    "from this window own measured limit (the binding reader walks the whole "
    "source, so a name bound in two sibling function bodies merges into one "
    "ambiguous table) as AC-PNSB1..AC-PNSB6. DEBT: product-face-R2536 closed "
    "through its writer, reconcile-battery-R2537 opened first=yes at 598/4564 "
    "so the next window owes that battery BEFORE any further product byte, "
    "product-face-R2537 opened first=no; the residue declaration was appended "
    "through its batch writer (301 -> 302 entries, until R2547) and reads "
    "TRIAGED. HONEST: two product points on the Executive Protocol scale but "
    "nothing a CEO could newly open; three defects were measured in this "
    "window own first pass and fixed in the CODE rather than in the "
    "assertions, and one fixture was corrected against measurement rather "
    "than the code loosened; the state_fold layout reader is still broken "
    "(disclosed since R2522) so the state append used a proved load+dump "
    "round-trip; Docker is absent on this host, the real 19.9 debit and the "
    "real msgSecCheck still wait on CEO physical items, and tasks.md was "
    "untouched.")


def main():
    raw = open(PATH, "rb").read()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    if "R2537 PRODUCT window" in text:
        print("NOOP already prepended")
        return 0
    before = len(raw)
    payload = DONE + eol + text
    predicted = len(payload.encode("utf-8"))
    print("backlog before=%d predicted=%d delta=%d"
          % (before, predicted, predicted - before))
    with io.open(PATH, "wb") as handle:
        handle.write(payload.encode("utf-8"))
    back_raw = open(PATH, "rb").read()
    back = back_raw.decode("utf-8").split(eol)
    ok = (len(back_raw) == predicted
          and back[0].startswith("- [x] [done 2026-11-07 R2537]"))
    print("backlog %s measured=%d readback=%s"
          % ("OK" if ok else "FAIL", len(back_raw), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())