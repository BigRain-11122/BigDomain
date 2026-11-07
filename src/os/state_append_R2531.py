"""R2531 state append: the product window on the AC-PCAF1 face."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-07 R2531 PRODUCT window on the tech head the register named "
    "(product-face-R2530, state/queue/tech.md:567 prefix AC-PCAF1, criteria "
    "AC-PCAF1..AC-PCAF6 pinned in that row at R2529 BEFORE any code). Five-"
    "silence scan at open: the tree was clean and no index.lock was present, "
    "zero new @BigDomain rows in cph4/evolution-ledger.md, and the content-"
    "addressed decisions scan read FIVE new tokens over the stored 160-token "
    "baseline (D-20261107-18..22) - all five were read and judged NOT this "
    "company execution face (a quant intake batch, a finance-lane host "
    "migration, a machine-roster drift repair, a BigCompute three-way "
    "dispatch and a reflection-journal closure), so this window KNOWS of them "
    "and does not act, with the numbers referenced in this line as the "
    "delivery law requires; group orders tail unchanged, benchmarks 2026-11-03 "
    "inside the seven-day gate. Debt gate read CLAIM-FIRST "
    "item=product-face-R2530 first=1, so no battery was owed before product "
    "bytes. CLAIM: MEASURED at R2529 that a for-loop over a NAME bound to a "
    "container reads {} for the target and names NO shape at all, even though "
    "the container itself is in the table, that the same shape one attribute "
    "hop out is equally silent, and that a two-element container reads nothing "
    "where the honest answer is ambiguous. SHIPPED "
    "src/os/probe_seam_for_container_name.py plus its six-criteria suite: a "
    "for-loop whose iterable is a NAME, an attribute chain into a same-root "
    "module, or a container literal resolves ONLY when that container holds "
    "exactly one element and carries the chain it took on the row; a "
    "multi-element container is NAMED ambiguous and never resolved to its "
    "first element, an empty container is NAMED empty, a str iterable is "
    "NAMED string, and a call, a format, a comprehension, an arithmetic "
    "expression, a subscript container and a broken chain hop are NAMED with "
    "the hop. The shipped tables are asked FIRST and never overwritten and "
    "the seam classifier is still the shipped registry single quiets. PROOF: "
    "AC-PCAF1..AC-PCAF6 SUITE PASS 6/6 TWICE with byte-identical output, exit "
    "0 on both legs, plus five adjacent probe suites green (alias expression, "
    "annotated constant, local constant, dynamic import, registry) "
    "(qa/probe-seam-for-container-name-R2531.log, 26014B, bom=False crlf=0 "
    "nul=0, legs=2 identical=True fails=0 adjacent=5), and a live leg on the "
    "REAL tree reading SEAMS-CONTAINER-COVERED over 1431 probes (3 covered, "
    "175 out-of-scope, 1253 historical, missing=0) with the module and render "
    "digests unchanged. REGISTRY 594/4540 -> 595/4546 by exactly one row "
    "os-probe-seam-for-container-name(6), recounted by importing "
    "reconcile_all.SUITES; docs/sandbox-suite-matrix.md regenerated stamp-"
    "aligned from the eligible battery leg qa/reconcile-all-R2530-retry.log to "
    "57362 bytes at 595 suites / 4546 criteria with green=594/595 "
    "self-describing and --check byte-identical. DEBT through the shipped "
    "writers: product-face-R2530 closed (line 260, open 13->12, done 229->230, "
    "160679B -> 160682B, readback ok), reconcile-battery-R2531 opened first=yes "
    "(160682B -> 161285B, readback ok) at the pre-registered 595 suites / 4546 "
    "criteria so the next window owes ONE battery on this committed tree "
    "BEFORE any further product byte, and product-face-R2531 opened first=no "
    "(161285B -> 161675B, readback ok) naming tech line 569 prefix AC-PCSC1. "
    "BOARD: the AC-PCAF1 row was closed through queue_close_R2531.py (line "
    "566, predicted 1712081B = measured 1712081B, delta 4710, readback ok) and "
    "ONE row seeded from this window own measured limit with AC-PCSC1..AC-PCSC6 "
    "pre-registered and five anchors re-checked at zero occupancy, so "
    "queue_floor reads FLOOR-MET 5/5 11/10 10/10 and the head is line 569.",

    "2026-11-07 R2531 honest disclosures: (a) ONE product point on the "
    "Executive Protocol scale - a shipped reading with its own suite and CLI "
    "that a maintainer can run, but nothing a CEO could newly open; no "
    "business surface moved; (b) THREE defects were measured in my own first "
    "pass and fixed in the CODE rather than in the assertions: a bare string "
    "iterable fell through to shape instead of string, an ast.Call naming "
    "format read as call, and the two shipped producers publish container "
    "elements in DIFFERENT representations (raw strings from the alias face "
    "_tree_of, nested (type, value) trees from the annotated face "
    "_module_trees) so my first element reader copied a nested pair into the "
    "table; the reader now accepts both laws and refuses a nested container "
    "by name; (c) ONE assertion was corrected against measurement, not "
    "loosened to fit a claim: the read-only criterion world had to exclude "
    "the deliberately partial helper, because a helper that omits a seam "
    "legitimately reads MISSING-SEAM; (d) the first evidence capture carried "
    "273 CRLF because the subprocess stdout already held them - the bytes "
    "were normalised to LF and the shipped writer census then read "
    "DRIFT-CLEAN flags=0 rather than being committed red; (e) the walk shape "
    "is written in this module rather than injected into the shipped alias "
    "face, because parameterising a shipped module would owe a battery in the "
    "same window - the seam CLASSIFIER is still the registry single quiets; "
    "(f) the matrix green line honestly reads 594/595 because the new suite is "
    "not in the battery leg it was stamped from; (g) a container reached "
    "through a constant subscript, and a multi-target for-loop, are still not "
    "read - both named as the seeded row; (h) Docker is absent on this host, "
    "the real 19.9 debit and the real msgSecCheck still wait on CEO physical "
    "items, and the S4U lane reconcile still needs an elevated shell; (i) "
    "tasks.md was not touched, it is the P-47 canonical board.",

    "R2531 tokens: local=~13k api=0 api_reason=product window - five-silence "
    "scan, one debt gate read, one pre-registered face shipped with its six "
    "criteria, one suite proved twice with identical output plus five "
    "adjacent suites, one live leg on the real tree with both digests "
    "unchanged, one evidence capture normalised to LF and cleared by the "
    "shipped writer census, one registry row recounted by import, one "
    "stamp-aligned matrix regeneration checked byte-identical, one queue row "
    "closed and one seeded through their shipped writers, three debt rows "
    "moved through their shipped writers, and the state/export/backlog/"
    "heartbeat closeout; zero cloud calls and zero external API touches",
]

NEW_DEC_TOKENS = [
    "D-20261107-18",
    "D-20261107-19",
    "D-20261107-20",
    "D-20261107-21",
    "D-20261107-22",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2531
    state["log"].extend(LINES)
    tokens = list(state.get("last_dec_tokens") or [])
    for token in NEW_DEC_TOKENS:
        if token not in tokens:
            tokens.append(token)
    state["last_dec_tokens"] = tokens
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"])
          and back["tick"] == 2531
          and back["log"][-1] == LINES[-1]
          and all(token in back["last_dec_tokens"]
                  for token in NEW_DEC_TOKENS))
    print("state %s tick=%s log=%d tokens=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             len(back["last_dec_tokens"]), os.path.getsize(PATH),
             "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())