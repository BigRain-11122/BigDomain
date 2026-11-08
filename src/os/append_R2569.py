"""R2569 closeout append: prove the byte-exact round-trip, then mutate."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-08 R2569 PRODUCT window on the tech head the register named "
    "(product-face-R2568, state/queue/tech.md:603 prefix AC-PNDCF1, criteria "
    "AC-PNDCF1..AC-PNDCF6 pinned in that row at R2565 BEFORE any code). "
    "Five-silence at open: git status EMPTY at HEAD 2818b80c with no "
    "index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, and the "
    "debt gate read CLAIM-FIRST item=product-face-R2568 with no battery owed "
    "because R2568 moved no product src byte. queue_head named line 603 "
    "claimable=11 with the floor MET, and all five pinned anchors were "
    "re-checked at zero occupancy at HEAD before any code: every hit was a "
    "seed row, a bookkeeping writer, state or debt prose, never an "
    "implementation.",
    "2026-11-08 R2569 SHIPPED "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_call_target_scope.py plus its six-criteria suite. The four "
    "gaps MEASURED at R2565 were re-measured before any code and are now "
    "closed: a with-as context that is a call on an ATTRIBUTE resolves when "
    "that method returns a module name and is NAMED attr-call-target "
    "otherwise; a function returning its module name through a LOCAL "
    "resolves; a one-level relative `from . import helper` resolves against "
    "the package own directory and is never a local; and a constant that only "
    "a NESTED function binds is NAMED attr-nested-constant instead of being "
    "resolved, which RETIRES the over-resolution the shipped faces carried. "
    "The shipped from-scope reading is asked FIRST and every key it published "
    "is carried unchanged on every row. PROOF measured not quoted: "
    "AC-PNDCF1..AC-PNDCF6 SUITE PASS 6/6 on the first run and 6/6 TWICE with "
    "identical output plus five adjacent probe suites green through the "
    "shipped capture callable "
    "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-call-target-scope-R2569.log, 5580B, legs=2, identical=True, "
    "adjacent=5, fails=0); a BOUNDED live leg reads files=6 loops=123 "
    "ct_resolved=0 ct_named=134 read_only=True over real probe modules and "
    "measures FOUR fixtures on BOTH readers - with-as-attribute ok/b here "
    "against refused/attr-with-as:m.ATTR there, local-return ok/b against "
    "refused/attr-with-as:md.ATTR, relative-from ok/b against "
    "refused/attr-base-local:helper, nested-constant refused/"
    "attr-nested-constant against ok there "
    "(qa/...-call-target-scope-live-R2569.log, 486B, utf-8, crlf=0, "
    "bom=False). REGISTRY 613/4654 -> 614/4660 by exactly one row, recounted "
    "by importing reconcile_all.SUITES rather than trusted (614 unique names, "
    "614 unique paths); docs/sandbox-suite-matrix.md was regenerated from the "
    "eligible R2568 green leg to 60266 bytes at 614 suites / 4660 criteria "
    "with its green line honestly reading 613/614 (this round own suite is not "
    "in that battery leg) and --check then read byte-identical at rc=0.",
    "2026-11-08 R2569 BOARD AND DEBT: the claimed row 603 was closed through "
    "src/os/queue_close_R2569.py at its predicted and measured 1791830B with "
    "its DISCHARGED note, and ONE row was seeded from this window own MEASURED "
    "limits through src/os/limits_call_target_R2569.py against one private "
    "world where the honest answer is b: a two-level `from .. import helper` "
    "reads attr-base-local:helper, a with-as call on a method defined in "
    "ANOTHER module reads attr-call-target:m.ATTR because the call-target "
    "table is built from the same source text only, a class-body constant read "
    "as cls.K.ATTR reads attr-from-import:cls.K.ATTR because no reading walks "
    "a class body, and `from .cls import K` reads attr-base-local:K - seeded "
    "as AC-PNDCG1..AC-PNDCG6; queue_head then read the new head at line 605 "
    "prefix AC-PNDCG1 claimable=11 and queue_floor read FLOOR-MET main=5/5 "
    "tech=11/10 explore=10/10. DEBT through the shipped writers: "
    "product-face-R2568 closed (line 313, open 27->26, done 268->269, "
    "177887B -> 177890B, readback ok), reconcile-battery-R2569 appended "
    "first=yes at the pre-registered 614/4660 (177890B -> 178210B) and "
    "product-face-R2569 appended first=no (178210B -> 178457B), both readback "
    "ok, so the gate now names that battery first. RESIDUE: the R2568 repin "
    "had dropped R2559 as unmatched and it is live again, so both R2559 and "
    "R2569 were declared through the shipped batch writer (319 -> 321 "
    "entries, 86505B -> 87129B, until R2578) and the check then read TRIAGED "
    "321/321 with untriaged=0.",
    "R2569 tokens: local=~20k api=0 api_reason=product window - five-silence "
    "scan, one debt gate read naming the product face, one queue head and "
    "floor read, one zero-occupancy anchor check on five anchors, one "
    "pre-registered face shipped with its six criteria, one suite green 6/6 on "
    "the first run and twice through the shipped capture callable plus five "
    "adjacent suites, one bounded live leg with four fixtures measured on BOTH "
    "readers, five limit shapes measured and four seeded as the next row, one "
    "registry row recounted by import, one stamp-aligned matrix regeneration "
    "checked byte-identical, one board row closed and one seeded through their "
    "writers, three debt rows moved through their shipped writers, one "
    "residue batch declared for two rounds, and the state/export/backlog/"
    "heartbeat closeout; zero cloud calls and zero external API touches",
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
    state["last_decision_rows"] = 273
    out = dump(state).encode("utf-8")
    with open(PATH, "wb") as handle:
        handle.write(out)
    print("ROUNDTRIP-OK bytes=%d tick=%d log=%d->%d after=%d"
          % (len(raw), state["tick"], before, len(state["log"]), len(out)))


if __name__ == "__main__":
    main()