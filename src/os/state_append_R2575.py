import io
import json
import os

STATE = os.path.join("src", "os", "state.json")

LINES = [
    "2026-11-08 R2575 PRODUCT window on the debt gate head the register names "
    "(product-face-R2574, state/queue/tech.md:609 prefix AC-PNDCI1, criteria "
    "pinned there at R2573 BEFORE any code). Five-silence at open: git status "
    "EMPTY at HEAD dd1c17a1 with no index.lock, zero unreplied @BigDomain "
    "transfer rows in cph4/evolution-ledger.md (the 31 BigDomain mentions are "
    "audit prose and were read rather than counted), the content-addressed "
    "decisions scan read new=0 over the stored baseline, and the group orders "
    "tail held last_tok=2026-11-08 18:03 (OB-20261108-180341-868, an "
    "@BigMoney re-dispatch, knowledge-only for this company; the 06:0x and "
    "12:06 rows are @BigCompute and @BigMoney), benchmarks 2026-11-03 inside "
    "the seven-day gate. Debt gate read CLAIM-FIRST product-face-R2574 "
    "first=1 and queue_head named tech line 609 claimable=11 with the floor "
    "MET at 5/5 11/10 10/10.",
    "2026-11-08 R2575 SHIPPED "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_class_source_scope.py plus its six-criteria suite: a base "
    "class imported from ANOTHER module in the same root now resolves through "
    "the subclass path, cycle-guarded by (module, path) and bounded at depth "
    "8, so a two-hop cross base resolves and a base cycle returns the subclass "
    "own value instead of recursing; a method returning an inherited class "
    "attribute through self is re-read through that cross table; a "
    "module-level value bound by a call returning a class attribute resolves "
    "as a with-as receiver and names the hop with-as-module-value; and a "
    "class-constant alias resolves to the same literal to a fixpoint, "
    "including a two-step chain, while an alias cycle resolves nothing and "
    "does not hang. The shipped class-base face is asked FIRST and never "
    "overwritten, the shipped relative-FROM-name refusal is carried byte for "
    "byte, and the seam classifier is still the shipped registry single "
    "`quiets`.",
    "2026-11-08 R2575 PROOF: AC-PNDCI1..AC-PNDCI6 SUITE PASS 6/6 TWICE with "
    "byte-identical output plus five adjacent probe suites green through the "
    "shipped capture callable "
    "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-class-source-scope-R2575.log, 6834B, legs=2 "
    "identical=True adjacent=5 fails=0). A BOUNDED live leg on the REAL tree "
    "reads SEAMS-CLASS-SOURCE-COVERED over 178 loops in 7 probe modules with "
    "cs_resolved=0 cs_named=0 and read_only=True, and measures FOUR fixtures "
    "on BOTH readers: cross-module-base ok/b here against "
    "refused/attr-class-base-constant:cls.K.ATTR there, self-cross-base ok/b "
    "against refused/attr-cross-call:m.ATTR, module-value ok/b against "
    "refused/attr-with-as:m.ATTR, and class-alias ok/b against "
    "refused/attr-class-base-constant:cls.K.OTHER "
    "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-class-source-scope-live-R2575.log, 387B, bom=False crlf=0 "
    "lf=5, landed through the shipped single writer).",
    "2026-11-08 R2575 ONE SEED CLAIM CORRECTED AGAINST MEASUREMENT rather than "
    "repeated and disclosed: the seed row named a method returning a BASE-class "
    "attribute through self as still open, but the shipped class-base face "
    "already merges a SAME-module base and measured ok/b at HEAD through "
    "src/os/limits_class_base_R2573.py plus a re-measurement on the current "
    "tree, so this face carries that answer and re-reads only the CROSS-module "
    "base shape. TWO defects were measured in my own first pass and fixed in "
    "the CODE: the with-as cross-reader refused a receiver chain that names its "
    "module when the loop text is synthetic and has no file of its own, because "
    "a module guard was applied before the receiver was resolved, and that "
    "guard now applies only to a bare-name call. The registry moved by ONE row "
    "to 617 suites / 4678 criteria, recounted by importing reconcile_all.SUITES "
    "rather than trusted (617 unique names, 617 unique paths); "
    "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the "
    "eligible R2573-retry battery leg through --stamp-from the existing "
    "document to 60982 bytes at 617 suites / 4678 criteria with its green line "
    "honestly reading 616/617 and --check byte-identical at rc=0, after the "
    "dry run failed first by design and wrote no byte. The eligible battery "
    "leg on disk is qa/reconcile-all-R2573-retry.log because the R2574 window "
    "re-ran its battery into that path, named here rather than smoothed.",
    "2026-11-08 R2575 BOARD AND DEBT: row 609 was closed through "
    "queue_close_R2575.py at its predicted and measured 1805831B (delta 4396, "
    "readback ok) with a DISCHARGED note carrying the measured facts above, "
    "and ONE row was seeded from this window own measured limit (AC-PNCS1.."
    "AC-PNCS6: a module-level alias chain and a module-level function "
    "returning a class attribute both refuse as with-as, and a class alias to "
    "a FROM-imported constant refuses as class-source-constant), head now "
    "line 611, floor FLOOR-MET. product-face-R2574 was closed through the "
    "shipped debtor (line 322, open 30->29, done 274->275, readback ok), "
    "reconcile-battery-R2574 was opened first=yes through the shipped appender "
    "at 181058B -> 181436B so the next window owes that battery BEFORE any "
    "product byte, and product-face-R2575 was opened first=no "
    "(181436B -> 181815B); the gate now reads CLAIM-FIRST "
    "reconcile-battery-R2574 first=1 open=31.",
    "2026-11-08 R2575 honest disclosures: (a) ONE product point: a real reader "
    "with six criteria and both evidence legs, and nothing a CEO could newly "
    "open; (b) the seed claim about self-through-a-base was wrong and is "
    "corrected here against measurement instead of being counted as a gap "
    "closed; (c) a cross-module base is followed only through classes that "
    "exist as module files in the same root, so a class supplied by an "
    "installed package is not read; (d) an alias is resolved only inside a "
    "class body, so a module-level alias of a call is the seeded next row; "
    "(e) the helper walk still follows the shipped container-name walk; (f) "
    "Docker is absent on this host so no containerised sandbox bring-up is "
    "claimed; (g) the real 19.9 debit and the real msgSecCheck still wait on "
    "CEO physical items (merchant id, mini-program appid/secret); (h) the S4U "
    "lane re-registration still needs an ELEVATED shell; (i) tasks.md was not "
    "touched, it is the P-47 canonical board.",
    "R2575 tokens: local=~13k api=0 api_reason=product window - five-silence "
    "scan with the decisions, orders and ledger faces actually read, one "
    "limit re-measured on the current tree before any code, one module plus "
    "one six-criteria suite shipped, two own defects measured and repaired at "
    "their birth site, two suite legs plus five adjacent suites through the "
    "shipped capture, one bounded live leg on the real tree through the "
    "shipped single writer, one registry row wired and recounted by import, "
    "one designed matrix FAIL then one stamp-aligned regeneration checked "
    "byte-identical, one board row closed with one seeded, one debt row closed "
    "and two opened through their shipped writers, and the "
    "state/export/heartbeat closeout; zero cloud calls and zero external API "
    "touches",
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
    ok = (got["tick"] == 2575 and len(got["log"]) == len(data["log"])
          and got["log"][-1].startswith("R2575 tokens:"))
    print("state tick=%s log=%d before=%dB after=%dB ok=%r"
          % (got["tick"], len(got["log"]), before, len(back.encode("utf-8")),
             ok))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())