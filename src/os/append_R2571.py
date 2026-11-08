"""R2571 closeout append: prove the byte-exact round-trip, then mutate."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-08 R2571 PRODUCT window on the tech head the register named "
    "(product-face-R2570, state/queue/tech.md:605 prefix AC-PNDCG1, criteria "
    "AC-PNDCG1..AC-PNDCG6 pinned in that row at R2569 BEFORE any code). "
    "Five-silence at open: git status EMPTY at HEAD b2534a3d with no "
    "index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the "
    "content-addressed decisions diff read new=0 over the stored baseline "
    "(273 rows, 161 tokens), the group orders tail unchanged at 2026-11-08 "
    "12:06 (OB-20261108-120628-589), benchmarks 2026-11-03 inside the "
    "seven-day gate. The debt gate read CLAIM-FIRST item=product-face-R2570 "
    "with no battery owed, queue_head named line 605 claimable=11 with the "
    "floor MET at main 5/5 tech 11/10 explore 10/10, and all five pinned "
    "anchors were re-checked at zero occupancy at HEAD before any code: every "
    "hit was a seed row, a bookkeeping writer, state or debt prose, never an "
    "implementation.",
    "2026-11-08 R2571 SHIPPED src/os/probe_seam_name_binding_arm_mixed_"
    "residual_alias_attribute_import_alias_scope_two_level_scope.py plus its "
    "six-criteria suite. The four gaps MEASURED at R2569 were re-measured "
    "before any code (src/os/limits_two_level_R2571.py) and are now closed: "
    "a level-bearing `from .. import helper` resolves against the parent "
    "package once an anchor is known - the module own source path, or this "
    "text matched to a file under the root - and stays refused at the shipped "
    "attr-base-local word when no anchor exists; a with-as call on a method "
    "defined in ANOTHER module resolves when that method returns a module "
    "name and is NAMED attr-cross-call otherwise; a class-body constant "
    "resolves through its class path; and a relative FROM-imported NAME is "
    "refused with its own word attr-relative-from-name instead of being "
    "published as a local. The shipped call-target reading is asked FIRST and "
    "every key it published is carried unchanged on every row. PROOF measured "
    "not quoted: AC-PNDCG1..AC-PNDCG6 SUITE PASS 6/6 on the first run and 6/6 "
    "TWICE with identical output plus five adjacent probe suites green through "
    "the shipped capture callable "
    "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-two-level-scope-R2571.log, 5543B, legs=2, identical=True, "
    "adjacent=5, fails=0); a BOUNDED live leg reads files=6 loops=151 "
    "tl_resolved=0 tl_named=0 read_only=True over six real probe modules and "
    "measures FOUR fixtures on BOTH readers - two-level ok/b here against "
    "refused/attr-base-local:helper there, cross-module ok/b against "
    "refused/attr-call-target:m.ATTR, class-body ok/b against "
    "refused/attr-from-import:cls.K.ATTR, and relative-name "
    "refused/attr-relative-from-name:K.ATTR against refused/attr-base-local:K "
    "(qa/...-two-level-scope-live-R2571.log, 378B, utf-8, crlf=0, bom=False). "
    "The live leg reading tl_resolved=0 is honest: the six real probe modules "
    "carry no two-level, cross-module or class-body shape, so this face only "
    "speaks where its own fixtures are.",
    "2026-11-08 R2571 REGISTRY AND DOCUMENT: 614/4660 -> 615/4666 by exactly "
    "one row, recounted by importing reconcile_all.SUITES rather than trusted "
    "(615 unique names, 615 unique paths). The matrix dry check read FAIL "
    "(stale) BEFORE any byte was written, then docs/sandbox-suite-matrix.md "
    "was regenerated from the eligible R2569 battery leg through "
    "src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R2569.log "
    "--stamp-from docs/sandbox-suite-matrix.md to 60475 bytes at 615 suites / "
    "4666 criteria with its green line honestly reading 614/615, and --check "
    "then read byte-identical at rc=0.",
    "2026-11-08 R2571 BOARD AND DEBT: the claimed row 605 was closed through "
    "src/os/queue_close_R2571.py at its predicted and measured 1796391B with "
    "its DISCHARGED note, and ONE row was seeded from this window own MEASURED "
    "limits through the same script: an inherited class-body constant reads "
    "attr-class-constant, an absolute FROM-imported CLASS read as K.ATTR reads "
    "attr-base-local:K, a cross-module with-as call whose method returns "
    "self.NAME reads attr-cross-call, and a receiver bound by a FROM-import "
    "alias reads attr-cross-call - seeded as AC-PNDCH1..AC-PNDCH6; queue_head "
    "then read the new head at line 607 prefix AC-PNDCH1 claimable=11 and "
    "queue_floor read FLOOR-MET main=5/5 tech=11/10 explore=10/10. DEBT "
    "through the shipped writers: product-face-R2570 closed (line 316, open "
    "28->27, done 270->271, 178793B -> 178796B, readback ok), "
    "reconcile-battery-R2571 appended first=yes at the pre-registered 615/4666 "
    "(178796B -> 179074B) and product-face-R2571 appended first=no (179074B -> "
    "179391B), both readback ok, so the gate now names that battery first. "
    "RESIDUE: R2571 was declared through the shipped batch writer (321 -> 322 "
    "entries, 87129B -> 87369B, until R2578) and the check then read TRIAGED "
    "321/321 with untriaged=0; ONE entry still reads UNMATCHED (R2569, "
    "declared DELIVERED at that round, live=-), which is the same inherited "
    "declaration drift the R2568 repin drops and is NOT repaired by hand here.",
    "R2571 tokens: local=~26k api=0 api_reason=product window - five-silence "
    "scan with decisions and orders actually read, one debt gate read, one "
    "queue head and floor read, one zero-occupancy anchor check on five "
    "anchors, one limits script measuring eleven shapes through the shipped "
    "entry, one pre-registered face shipped with its six criteria, one suite "
    "green 6/6 on the first run and twice through the shipped capture callable "
    "plus five adjacent suites, one bounded live leg measuring four fixtures "
    "on BOTH readers, one registry row recounted by import, one designed "
    "matrix FAIL followed by a stamp-aligned regeneration checked "
    "byte-identical, one board row closed and one seeded through their "
    "writers, three debt rows moved through their shipped writers, one "
    "residue batch declaration, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
]


def dump(state):
    return json.dumps(state, ensure_ascii=False, indent=1)


def main():
    raw = open(PATH, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    proved = dump(state)
    if proved.encode("utf-8") != raw:
        raise SystemExit("E_ROUNDTRIP: dump differs from disk (%d vs %d bytes)"
                         % (len(proved.encode("utf-8")), len(raw)))
    before = len(state["log"])
    state["tick"] = int(state["tick"]) + 1
    state["log"].extend(LINES)
    out = dump(state).encode("utf-8")
    with open(PATH, "wb") as handle:
        handle.write(out)
    print("ROUNDTRIP-OK bytes=%d tick=%d log=%d->%d after=%d"
          % (len(raw), state["tick"], before, len(state["log"]), len(out)))


if __name__ == "__main__":
    main()