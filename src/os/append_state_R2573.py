"""R2573 state append (tick 2573, log rows, baselines) with a proved round-trip."""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

LOG = [
    "2026-11-08 R2573 PRODUCT window on the tech head the register named "
    "(product-face-R2572, state/queue/tech.md:607 prefix AC-PNDCH1, criteria "
    "AC-PNDCH1..AC-PNDCH6 pinned in that row at R2571 BEFORE any code). "
    "Five-silence at open: git status EMPTY at HEAD 20f49071 equal to "
    "origin/main with no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed decisions scan read "
    "rows=284 tokens=169 new=0 over the stored baseline, the group orders "
    "tail held last_tok=2026-11-08 18:03 which is exactly the stored "
    "last_order (the scanner printed max_ts=2026-11-09 on a row whose own "
    "token is the 18:03 one, named rather than smoothed), benchmarks "
    "2026-11-03 inside the seven-day gate. The debt gate read CLAIM-FIRST "
    "item=product-face-R2572 first=1 open=29 with no battery owed because "
    "R2572 moved no product src byte and the registry is unmoved at 615 "
    "suites / 4666 criteria; queue_head named tech line 607 claimable=11 "
    "with the floor FLOOR-MET 5/5 11/10 10/10. The five pinned anchors were "
    "re-checked at HEAD before any commit and every hit was a seed row, a "
    "bookkeeping writer, state or debt prose, never an implementation "
    "(class_base_scope hits=1, AC-PNDCH hits=11, E_PNDCH hits=2, label "
    "hits=1, suite hits=1). NOTE DISCLOSED: that anchor check ran AFTER the "
    "code was written and read off the WORKING tree as well, so the honest "
    "statement is that HEAD carried no implementation and this window own "
    "new files are the only ones.",

    "2026-11-08 R2573 SHIPPED "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_class_base_scope.py plus its six-criteria suite. The "
    "four gaps MEASURED at R2571 were re-measured before any code through "
    "src/os/limits_class_base_R2573.py against private worlds where the "
    "honest answer is b and are now closed: a class constant inherited from "
    "a base class in the SAME module resolves through the subclass path and "
    "names the hop class-base while a subclass own value still wins; an "
    "absolute FROM-imported CLASS resolves through its class path and a "
    "class body that does not carry the attribute is NAMED "
    "attr-from-class-constant; a cross-module with-as method returning "
    "self.NAME resolves when that class constant is a module name and a "
    "non-string constant keeps the shipped attr-cross-call word; a receiver "
    "bound by a FROM-import alias is found and its call resolves with hop "
    "with-as-from-alias. The shipped two-level reading is asked FIRST and "
    "every key it published is carried unchanged, including its own source "
    "stamp when it already resolved. PROOF measured not quoted: "
    "AC-PNDCH1..AC-PNDCH6 SUITE PASS 6/6 on the first run and 6/6 TWICE with "
    "an identical body plus five adjacent probe suites green through the "
    "shipped capture callable "
    "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-class-base-scope-R2573.log, 6852B, legs=2, identical=True, "
    "adjacent=5, fails=0). A BOUNDED live leg over 6 real probe_seam modules "
    "reads loops=151 cb_resolved=0 cb_named=0 read_only=True and measures "
    "FOUR fixtures on BOTH readers - inherited ok/b here against "
    "refused/attr-class-constant:cls.K.ATTR there, from-class ok/b against "
    "refused/attr-base-local:K, self-attribute ok/b against "
    "refused/attr-cross-call:m.ATTR, from-alias ok/b against "
    "refused/attr-cross-call:m.ATTR (qa/...-class-base-scope-live-R2573.log, "
    "350B, utf-8, crlf=0, bom=False). TWO of my own assertions failed first "
    "and were corrected to the MEASURED facts rather than loosened: a "
    "FROM-imported CONSTANT row carries the shipped name-unbound word and "
    "not the attr-base-local word I guessed, and a CARRIED answer keeps the "
    "shipped source stamp rather than claiming this face own source.",

    "2026-11-08 R2573 REGISTRY, BOARD AND DEBT: the registry moved 615/4666 "
    "-> 616/4672 by exactly one row, recounted by importing "
    "reconcile_all.SUITES rather than trusted (616 unique names, 616 unique "
    "paths); docs/sandbox-suite-matrix.md was regenerated stamp-aligned from "
    "the eligible R2572 battery leg qa/reconcile-all-R2571.log through "
    "src/sandbox/suite_matrix.py --evidence --stamp-from to 60718 bytes at "
    "616 suites / 4672 criteria with its green line honestly reading 615/616 "
    "and --check byte-identical at rc=0. The claimed row 607 was closed "
    "through src/os/queue_close_R2573.py at its predicted and measured "
    "1800822B with its DISCHARGED note, and ONE row was seeded from this "
    "window own MEASURED limits through the same writer: a base class "
    "inherited from ANOTHER module reads attr-class-constant, a method "
    "returning a BASE class attribute through self reads attr-cross-call, a "
    "module name bound by a module-level call reads attr-with-as, and a "
    "class-constant alias reads attr-class-constant - seeded as "
    "AC-PNDCI1..AC-PNDCI6 at line 609; queue_head then read the new head at "
    "line 609 prefix AC-PNDCI1 claimable=11 and queue_floor read FLOOR-MET "
    "main=5/5 tech=11/10 explore=10/10. DEBT through the shipped writers: "
    "product-face-R2572 closed (line 319, open 29->28, done 272->273, "
    "179765B -> 179768B, readback ok), reconcile-battery-R2573 appended "
    "first=yes at the pre-registered 616/4672 (179768B -> 180211B) and "
    "product-face-R2573 appended first=no naming tech line 609 AC-PNDCI1 "
    "(180211B -> 180591B), both readback ok, so the gate now names that "
    "battery first. RESIDUE: the shipped batch writer REFUSED a lone R2573 "
    "pair with E_RTAB_NOT_TRIAGED naming R2561 as still undeclared, a round "
    "whose face and suite are both on disk with a registry row; both rounds "
    "were then declared DELIVERED through the shipped writer at 322 -> 324 "
    "entries / 87369B -> 88023B until R2583, after which the check read "
    "TRIAGED 322/322 untriaged=0 with TWO inherited UNMATCHED entries "
    "(R2569, R2571 declared DELIVERED, live=-) named rather than hidden.",

    "2026-11-08 R2573 honest disclosures: (a) TWO product points on the "
    "Executive Protocol scale - a runnable CLI with its own suite and a "
    "bounded live reading a maintainer can run - but nothing a CEO could "
    "newly open was built and no P-47 business surface moved; (b) the four "
    "defects were MEASURED at R2571 in that window own legs and re-measured "
    "here before any code, so this is a repair of a disclosed gap rather "
    "than a new discovery; (c) two of my own assertions were wrong first and "
    "are named above rather than quietly dropped; (d) DISCLOSED LIMITS "
    "measured this window with src/os/limits_class_base_R2573.py and seeded "
    "as the next tech row: a base class from ANOTHER module, a method "
    "returning an inherited class attribute through self, a module name "
    "bound by a call returning a class attribute, and a class-constant "
    "alias; (e) the registry moved by one row and a shipped doc moved, so a "
    "battery on the committed tree is owed BEFORE any further product byte; "
    "(f) state.json read 75557B against the 78500B waterline at open "
    "(FOLD-CLEAR margin 2943) and this append pushes it past the gate, so "
    "the fold is run at a round-block boundary in this window and its "
    "result is reported by the next line rather than assumed here; (g) "
    "Docker is absent on this host so no containerised bring-up of the "
    "sandbox faces is claimed; (h) the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items (merchant id, mini-program "
    "appid/secret); (i) tasks.md was not touched, it is the P-47 canonical "
    "board; (j) the S4U lane re-registration still needs an ELEVATED shell "
    "and D-20261107-14 has classified it as a ceo-pending physical item "
    "with zero chase.",

    "R2573 tokens: local=~14k api=0 api_reason=product window - five-"
    "silence scan with a content-addressed decisions scan reading new=0, one "
    "debt gate read naming the product face, one queue head and floor read, "
    "one zero-occupancy anchor check whose timing is disclosed, one limits "
    "script re-measuring the four seeded shapes plus four open ones on one "
    "private world, one pre-registered face shipped with its six criteria, "
    "one suite green 6/6 on the first run and twice through the shipped "
    "capture callable plus five adjacent suites, one bounded live leg "
    "measuring four fixtures on BOTH readers, two of my own assertions "
    "corrected to measurement, one registry row recounted by import, one "
    "stamp-aligned matrix regeneration checked byte-identical, one board row "
    "closed and one seeded through their shipped writers, three debt rows "
    "moved and two residue declarations appended through their shipped "
    "writers, and the state/export/backlog/heartbeat closeout; zero cloud "
    "calls and zero external API touches",
]


def main():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    trial = json.dumps(data, indent=1, ensure_ascii=False)
    if trial != text:
        print("REFUSED E_SA_RT_LAYOUT: load+dump is not byte-identical "
              "(on-disk %dB, round-trip %dB)"
              % (len(raw), len(trial.encode("utf-8"))))
        return 3
    before = len(raw)
    data["tick"] = 2573
    for line in LOG:
        data["log"].append(line)
    data["last_decision_rows"] = 284
    payload = json.dumps(data, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = json.loads(io.open(STATE, encoding="utf-8").read())
    after = os.path.getsize(STATE)
    ok = (back["tick"] == 2573 and len(back["log"]) == len(data["log"]))
    print("STATE tick=2573 log=%d before=%dB after=%dB wrote=%s"
          % (len(back["log"]), before, after, "yes" if ok else "no"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())