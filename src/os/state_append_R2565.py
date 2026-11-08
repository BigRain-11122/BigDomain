import io
import json
import os

STATE = os.path.join("src", "os", "state.json")

LINES = [
    "2026-11-08 R2565 PRODUCT window on the tech head the register named "
    "(product-face-R2564, state/queue/tech.md:601 prefix AC-PNDCE1 "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_from_scope, criteria AC-PNDCE1..AC-PNDCE6 pinned in that row at "
    "R2563 BEFORE any code). Five-silence at open: git status EMPTY at HEAD "
    "78bc78ff with no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed decisions diff read new=0 "
    "over the stored baseline at 164 tokens, the group orders tail unchanged "
    "at 2026-11-08 12:06 (OB-20261108-120628-589, already judged "
    "knowledge-only), benchmarks 2026-11-03 inside the seven-day gate. The "
    "debt gate read CLAIM-FIRST item=product-face-R2564 first=1 with no "
    "battery owed, queue_head named tech line 601 claimable=12 with the floor "
    "MET at 5/5 12/10 10/10, and all five pinned anchors were re-checked at "
    "zero occupancy at HEAD before any code: every hit was a seed row, a "
    "bookkeeping writer or state/debt prose, never an implementation. "
    "RE-MEASURED the three shapes through src/os/limits_import_alias_"
    "residual_R2563.py BEFORE any code: from-import-module refused "
    "attr-base-local:helper, function-body-constant refused "
    "attr-plain-import:helper.ATTR, with-as-call refused attr-with-as:m.ATTR, "
    "while reexport-alias and walrus-constant already read ok/b.",
    "2026-11-08 R2565 SHIPPED src/os/probe_seam_name_binding_arm_mixed_"
    "residual_alias_attribute_import_alias_scope_from_scope.py plus its "
    "six-criteria suite. The face asks the shipped import-alias reading FIRST "
    "and carries every key it published unchanged, then re-reads only a "
    "refusal: a module bound by `from pkg import helper`, plain or aliased, is "
    "taken as a MODULE base and resolved through pkg/helper.py instead of "
    "being called a local; a helper constant declared only inside a function "
    "body resolves to its literal when that function returns it and is NAMED "
    "attr-function-constant when it does not; a `with call() as NAME` binding "
    "whose call returns a module name resolves while a call returning anything "
    "else keeps the shipped attr-with-as word; a plain import base re-reads "
    "through the same extended module reading so a function-level constant is "
    "reached there too. Nothing is imported and nothing is evaluated. PROOF "
    "measured not quoted: AC-PNDCE1..AC-PNDCE6 SUITE PASS 6/6 TWICE with an "
    "identical digest plus five adjacent probe suites green "
    "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-from-scope-R2565.log, 5397B, legs=2 identical=True "
    "adjacent=5 fails=0) landed through the shipped capture callable; a "
    "BOUNDED live leg over 6 real probe_seam modules reads loops=123 "
    "from_resolved=0 from_named=0 with read_only=True, and the SAME fixtures "
    "are measured on BOTH readers - the from-import fixture reads ok/b here "
    "against attr-base-local:helper there, and the with-as-call fixture reads "
    "ok/b here against refused/attr-with-as:m.ATTR there "
    "(qa/...-live-R2565.log, 285B, crlf=0, bom=False). REGISTRY 611/4642 -> "
    "612/4648 by exactly one row, recounted by importing reconcile_all.SUITES "
    "rather than trusted (612 unique names, 612 unique paths), and "
    "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the "
    "eligible R2564 battery leg to 59929 bytes at 612 suites / 4648 criteria "
    "with its green line honestly reading 611/612 and --check byte-identical "
    "at rc=0 after a designed --check FAIL.",
    "2026-11-08 R2565 BOARD AND DEBT: the claimed row 601 was closed through "
    "src/os/queue_close_R2565.py at its predicted and measured 1785857B with "
    "its DISCHARGED note and ONE row was seeded from this window own MEASURED "
    "limit - src/os/limits_from_scope_R2565.py, four shapes against one "
    "private world - as AC-PNDCF1..AC-PNDCF6; queue_head then read the new "
    "head at line 603 prefix AC-PNDCF1 claimable=12 and the floor MET. DEBT "
    "through the shipped writers: product-face-R2564 closed (line 308, "
    "176429B -> 176432B, open 26->25, done 264->265, readback ok), "
    "reconcile-battery-R2565 appended first=yes at the pre-registered 612/4648 "
    "(176432B -> 176653B) and product-face-R2565 appended first=no naming "
    "tech line 603 AC-PNDCF1 (176653B -> 176975B), both readback ok, so the "
    "gate now names that battery first. RESIDUE: this round own declaration "
    "was written through the shipped batch writer at its predicted 304 -> 305 "
    "entries / 83730B -> 83927B until R2575, after which residue_triage "
    "--check read R2565 TRIAGED with untriaged=0.",
    "2026-11-08 R2565 honest disclosures: (a) TWO product points on the "
    "Executive Protocol scale - a runnable CLI with its own suite and a "
    "bounded live reading a maintainer can run - but nothing a CEO could "
    "newly open was built and no P-47 business surface moved; (b) the defect "
    "was MEASURED at R2563 in that window own legs and re-measured here before "
    "any code, so this is a repair of a disclosed gap rather than a new "
    "discovery; (c) FOUR of my own first-pass defects were found by RUNNING "
    "rather than by review and are named rather than hidden: the suite arms "
    "helper omitted the loop tail so three criteria read on an empty report, "
    "the face returned early for a PLAIN import base so the function-level "
    "constant was never re-read, the hop composition published "
    "with-as-call/direct where the house shape is a bare with-as-call, and "
    "base_from_hop was never carried at all; every one was fixed in the code "
    "or the carrier, none by loosening a criterion; (d) ONE assertion was "
    "corrected against measurement instead of the code: the shipped "
    "import-alias layer is SILENT (state None, no reason) for a from-import "
    "alias while its generic reason reads attr-base-local:h, so the criterion "
    "now asserts both measured facts instead of my guess; (e) DISCLOSED LIMITS "
    "measured this window with src/os/limits_from_scope_R2565.py and seeded as "
    "the next tech row: a with-as call on an ATTRIBUTE or a class method is "
    "never resolved, a call returning its module name through a LOCAL variable "
    "is never resolved, a relative `from . import helper` stays a local, and a "
    "constant bound only inside a NESTED function IS resolved - an "
    "over-resolution; (f) the registry moved by one row and a shipped doc "
    "moved, so a battery on this committed tree is owed BEFORE any further "
    "product byte; (g) MEASURED DEFECT STILL OPEN from R2522: state.json reads "
    "far past the 78500B waterline so state_fold --check reads FOLD-DUE and "
    "the shipped tool ships only a --check face, so this append used a PROVED "
    "load+dump round-trip; (h) Docker is absent on this host so no "
    "containerised bring-up is claimed; (i) the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items (merchant id, mini-program "
    "appid/secret); (j) tasks.md was not touched, it is the P-47 canonical "
    "board; (k) the stored last_decision_rows field still reads 273 against a "
    "measured 164 row tokens and was NOT rewritten this window, disclosed "
    "rather than silently reset; (l) the S4U lane re-registration still needs "
    "an ELEVATED shell and remains a ceo-pending physical item with zero "
    "chase.",
    "R2565 tokens: local=~13k api=0 api_reason=product window - five-silence "
    "scan, one content-addressed decisions scan reading new=0, one re-measure "
    "of the three limits before any code, one zero-occupancy anchor check on "
    "five anchors, one pre-registered face shipped with its six criteria, one "
    "suite proved twice through the shipped capture callable plus five "
    "adjacent suites, one bounded live leg with the same fixtures measured on "
    "BOTH readers, four limits measured and seeded as the next row, one "
    "registry row recounted by import, one stamp-aligned matrix regeneration "
    "checked byte-identical, one board row closed and one seeded through their "
    "shipped writers, three debt rows moved and one residue declaration "
    "appended through their shipped writers, and the state/export/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
]


def main():
    raw = io.open(STATE, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    roundtrip = json.dumps(data, indent=1, ensure_ascii=False)
    if roundtrip.encode("utf-8") != raw:
        print("REFUSED E_STATE_ROUNDTRIP: json round-trip is not byte-identical")
        return 3
    before = len(raw)
    data["tick"] = int(data["tick"]) + 1
    for line in LINES:
        data["log"].append(line)
    payload = json.dumps(data, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(STATE, encoding="utf-8").read()
    got = json.loads(back)
    ok = (got["tick"] == 2565 and len(got["log"]) == len(data["log"])
          and got["log"][-1].startswith("R2565 tokens:"))
    print("state tick=%s log=%d before=%dB after=%dB ok=%r"
          % (got["tick"], len(got["log"]), before, len(back.encode("utf-8")),
             ok))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())