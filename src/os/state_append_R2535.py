"""R2535 state append: tick 2535, the product window log lines, baseline union.

The shipped state_fold layout reader still does not match the dumped file
(disclosed since R2522), so this appends through a proved load+dump round-trip
instead of reformatting the file.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")

NEW_TOKENS = ["D-20261010-01", "D-20261026-17", "D-20261026-18",
              "D-20261026-21", "D-20261026-27", "D-20261027-10",
              "D-20261027-13", "D-20261027-16", "D-20261031-05"]

LINES = [
    "2026-11-07 R2535 PRODUCT window on the tech head the register named "
    "(product-face-R2534, state/queue/tech.md:571 prefix AC-PCNS1 "
    "probe_seam_nested_subscript_scope, criteria AC-PCNS1..AC-PCNS6 pinned in "
    "that row at R2533 BEFORE any code). Five-silence scan at open: the tree "
    "was clean with no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed decisions diff read NINE "
    "tokens over the stored 165-token baseline but every one of them is an "
    "INLINE REFERENCE inside another row own prose (D-20261010-01, "
    "D-20261026-17, D-20261026-18, D-20261026-21, D-20261026-27, "
    "D-20261027-10, D-20261027-13, D-20261027-16, D-20261031-05), each cited "
    "by a row dated before this window, so all nine are ACKNOWLEDGED with no "
    "execution face and the baseline was advanced by union; group orders tail "
    "unchanged; benchmarks 2026-11-03 inside the seven-day gate. The debt gate "
    "read CLAIM-FIRST item=product-face-R2534 first=1 with no battery owed, "
    "and queue_head named tech line 571 claimable=11 with the floor MET. All "
    "five pinned anchors were re-checked at zero occupancy at HEAD before any "
    "code: every hit was a seed row, a bookkeeping writer or state/debt "
    "prose, never an implementation.",

    "2026-11-07 R2535 SHIPPED src/os/probe_seam_nested_subscript_scope.py "
    "plus its six-criteria suite. ONE shape that read a bare word now "
    "resolves and carries EVERY key: a for-loop whose iterable is a CHAIN of "
    "two or more constant string subscripts on a literal container, in the "
    "module body and in function bodies, but ONLY when the resolved container "
    "holds exactly one element. A missing key, an integer index into a tuple, "
    "a call, a format and a comprehension step are NAMED together with the "
    "HOP that broke (key@hop2, index@hop2, call@hop2, format@hop2, "
    "comprehension@hop1) instead of a bare shape word; a two-element result "
    "is NAMED ambiguous and never resolved to its first element; an index "
    "step is never followed because a position is not a named slot. The "
    "shipped subscript tables and law are asked FIRST and never overwritten "
    "so every earlier answer stands, the local literal table is the module "
    "table shadowed by the function table, the inherited refusal of the "
    "container NAME itself is filtered to for-loop targets so the row speaks "
    "only about loop bindings, and the seam CLASSIFIER is still the shipped "
    "registry single `quiets`.",

    "2026-11-07 R2535 PROOF measured, not quoted: AC-PCNS1..AC-PCNS6 SUITE "
    "PASS 6/6 TWICE with byte-identical output and exit 0 on both legs plus "
    "five adjacent probe suites green (subscript container, container name, "
    "dynamic import, registry, alias expression) "
    "(qa/probe-seam-nested-subscript-scope-R2535.log, 8446B, legs=2 "
    "identical=True fails=0 adjacent=5, landed through the shipped capture "
    "callable). A live leg on the REAL tree reads "
    "SEAMS-NESTED-SUBSCRIPT-COVERED over 1447 probes (3 covered, 177 "
    "out-of-scope, 1267 historical, missing=0) with the module, the base face "
    "and the render digests unchanged across the reading, and on the SAME "
    "fixture this face follows D['a']['b'] while the shipped subscript face "
    "still reads refused=nested, so the closed gap is measured on BOTH readers "
    "(qa/probe-seam-nested-subscript-scope-live-R2535.log, 672B, crlf=0, "
    "bom=False).",

    "2026-11-07 R2535 REGISTRY, MATRIX, BOARD AND DEBT: one runner row "
    "os-probe-seam-nested-subscript-scope(6), so the registry reads 597 "
    "suites / 4558 criteria, recounted by importing reconcile_all.SUITES "
    "rather than trusted. docs/sandbox-suite-matrix.md was regenerated "
    "stamp-aligned from the ELIGIBLE battery leg qa/reconcile-all-R2533.log "
    "to 57572 bytes at 597 suites / 4558 criteria with its green line "
    "honestly reading 596/597, and --check then read byte-identical. The "
    "claimed row 571 was closed through its own per-round writer at predicted "
    "and measured 1721378B (delta 4901) and ONE row was seeded from this "
    "window own MEASURED limit through the same writer: a step that is a NAME "
    "bound to a str constant (`KEY = \"b\"` then `D[\"a\"][KEY]`) is NAMED "
    "with its hop but never resolved, seeded as AC-PNKB1..AC-PNKB6; "
    "queue_floor then read FLOOR-MET 5/5 11/10 10/10 with the new head at "
    "line 573. DEBT through the shipped writers: product-face-R2534 closed "
    "(line 266, open 15->14, done 233->234, 163535B -> 163538B, readback ok), "
    "reconcile-battery-R2535 appended first=yes at the pre-registered "
    "597/4558 (163538B -> 163793B) and product-face-R2535 appended first=no "
    "(163793B -> 164023B), both readback ok; the gate now names that battery "
    "first. BIRTH SITE: the residue declaration had expired at R2535 and two "
    "rounds it carried were no longer live, so the shipped idempotent re-pin "
    "re-read every live round and re-pinned them through R2545 (302 -> 301 "
    "entries, 83490B -> 83066B, dropped R2525 and R2527, readback PINNED), "
    "after which residue_triage --check read R2535 TRIAGED at exit 0.",

    "2026-11-07 R2535 honest disclosures: (a) TWO product points on the "
    "Executive Protocol scale - a runnable CLI with its own suite and a live "
    "reading a maintainer can run - but nothing a CEO could newly open and no "
    "P-47 business surface moved; (b) the defect was MEASURED at R2533 in "
    "that window own legs and re-measured here before shipping, so this is a "
    "repair of a disclosed gap rather than a new discovery; (c) THREE defects "
    "were measured in my own first pass and fixed in the CODE rather than in "
    "the assertions - the reading delegated the helper walk to the wrong "
    "shipped face and died with AttributeError on helper_scope, a function-body "
    "chain could not see a MODULE-level literal container, and a format step "
    "was named call because the label was read off the wrong shipped face; "
    "(d) a fourth fix was report quality rather than correctness: the "
    "inherited refusal of the container NAME itself is now filtered to "
    "for-loop targets so the row no longer publishes noise; (e) DISCLOSED "
    "LIMITS measured this window: a NAME step bound to a str constant is "
    "refused by name rather than resolved (seeded as the next tech row), an "
    "integer index into a tuple is never followed by design, and a helper "
    "that itself nests two keys is a stated gap because the helper walk is the "
    "shipped subscript walk; (f) the registry moved by one row and a shipped "
    "doc moved, so a battery on this committed tree is owed BEFORE any further "
    "product byte; (g) MEASURED DEFECT STILL OPEN from R2522: the shipped "
    "state_fold layout reader no longer matches the state file written with "
    "json.dump, so this window appended through a proved load+dump round-trip "
    "instead of reformatting the file; (h) Docker is absent on this host so no "
    "containerised bring-up of the sandbox faces is claimed; (i) the real 19.9 "
    "debit and the real msgSecCheck still wait on CEO physical items "
    "(merchant id, mini-program appid/secret); (j) tasks.md was not touched, "
    "it is the P-47 canonical board; (k) the S4U lane re-registration needs an "
    "ELEVATED shell and D-20261107-14 has classified it as a ceo-pending "
    "physical item with zero chase.",

    "R2535 tokens: local=~17k api=0 api_reason=product window - five-silence "
    "scan, one content-addressed decisions diff read and nine inline "
    "references judged knowledge-only, one zero-occupancy anchor check on five "
    "anchors, one pre-registered face shipped with its six criteria, one suite "
    "proved twice with identical output plus five adjacent suites, one live "
    "leg on the real tree with the same fixture measured on BOTH readers, one "
    "registry row recounted by import, one stamp-aligned matrix regeneration "
    "from an eligible battery leg checked byte-identical, one expired residue "
    "declaration re-pinned through its idempotent writer, one queue row closed "
    "and one seeded through its writer, three debt rows moved through their "
    "shipped writers, and the state/export/backlog/heartbeat closeout; zero "
    "cloud calls and zero external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2535
    state["log"].extend(LINES)
    base = list(state.get("last_dec_tokens") or [])
    for token in NEW_TOKENS:
        if token not in base:
            base.append(token)
    state["last_dec_tokens"] = base
    state["last_decision_rows"] = 210
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"])
          and back["tick"] == 2535
          and back["log"][-1] == LINES[-1])
    print("state %s tick=%s log=%d tokens=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             len(back["last_dec_tokens"]), os.path.getsize(PATH),
             "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())