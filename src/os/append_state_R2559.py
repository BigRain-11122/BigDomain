"""R2559 state append (tick, log rows, baselines) with a proved round-trip.

The shipped state_fold layout reader still refuses a json.dump layout (open
since R2522), so this writer PROVES a load+dump round-trip is byte-identical
before it mutates anything, and refuses when it is not.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

LOG = [
    "2026-11-08 R2559 PRODUCT window on the tech head the register named "
    "(product-face-R2558, state/queue/tech.md:595 prefix AC-PNDA1 "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_base, "
    "criteria AC-PNDA1..AC-PNDA6 pinned in that row at R2557 BEFORE any "
    "code). Five-silence at open: git status EMPTY at HEAD 4e416ef0 with no "
    "index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the "
    "content-addressed decisions diff read new=0 over the stored baseline at "
    "a measured 72 rows / 48 file tokens, the group orders tail unchanged at "
    "2026-11-08 00:04 (OB-20261108-000400-425, already judged knowledge-only "
    "at R2543), benchmarks 2026-11-03 inside the seven-day gate. The debt "
    "gate read CLAIM-FIRST item=product-face-R2558 first=1 with no battery "
    "owed, queue_head named tech line 595 claimable=12 with the floor MET, "
    "and all five pinned anchors were re-checked at zero occupancy at HEAD "
    "before any code: no module and no suite existed.",

    "2026-11-08 R2559 SHIPPED "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_base.py "
    "plus its six-criteria suite. MEASURED at R2557 on the alias-position "
    "face own reader and re-measured here BEFORE shipping: an attribute whose "
    "BASE is a function parameter or a local read attr-not-imported so the "
    "module check could not tell a parameter from a module the probe forgot "
    "to import, a dotted `pkg.mod.ATTR` hop read attr-deep because the join "
    "used only the first segment, and a helper constant declared by a walrus "
    "or inside a function body read attr-missing / attr-non-constant because "
    "only module-level plain and annotated assignments were read. The face "
    "asks the shipped position answer FIRST and carries every key it already "
    "published on every row, then re-reads only an attribute refusal: a "
    "parameter or local base is NAMED attr-base-local:<base>, a genuinely "
    "absent module keeps attr-not-imported:<text>, a dotted path is joined "
    "on its FULL path and resolves when the file is on disk, and a walrus or "
    "function-level helper constant resolves while two values read "
    "name-mixed. Nothing is imported and nothing is evaluated.",

    "2026-11-08 R2559 PROOF measured, not quoted: AC-PNDA1..AC-PNDA6 SUITE "
    "PASS 6/6 TWICE with identical output plus five adjacent probe suites "
    "green (qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
    "base-R2559.log, 5326B, landed through the shipped capture callable, "
    "legs=2 identical=True adjacent=5 fails=0). A BOUNDED live leg over 8 "
    "real probe_seam modules reads covered_probes=0 attribute_loops=0 "
    "attr_resolved=0 attr_named=0 - every one of those probes is "
    "OUT-OF-SCOPE, so the verdict is honest but weak and is stated rather "
    "than dressed up - and the SAME fixtures are measured on BOTH readers: "
    "the parameter-rooted fixture reads attr-base-local:node here against "
    "attr-not-imported:node.value there, and the dotted fixture reads ok/b "
    "here against attr-deep:pkg.mod.ATTR there "
    "(qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-base-"
    "live-R2559.log, 473B, utf-8, crlf=0, bom=False). REGISTRY 608/4624 -> "
    "609/4630 by exactly one row, recounted by importing reconcile_all.SUITES "
    "rather than trusted (609 unique names, 609 unique paths). "
    "docs/sandbox-suite-matrix.md was regenerated from the eligible battery "
    "leg qa/reconcile-all-R2558.log to 59255 bytes at 609 suites / 4630 "
    "criteria with its green line honestly reading 608/609 (this round own "
    "suite is not in that battery leg) and --check then read byte-identical "
    "at rc=0.",

    "2026-11-08 R2559 BOARD AND DEBT: the claimed row 595 was closed through "
    "src/os/queue_close_R2559.py at its predicted and measured 1772455B with "
    "its DISCHARGED note, and ONE row was seeded from this window own "
    "MEASURED limits (src/os/limits_attribute_base_R2559.py, four shapes run "
    "against one private world): a WALRUS attribute alias produces state=None "
    "with NO reason at all, a SUBSCRIPT base is published as "
    "attr-not-imported:?.ATTR where the base text is a question mark, a "
    "package own __init__ constant reads attr-missing because the hop asks "
    "for <mod>.py, and a with-as helper binding reads attr-missing - seeded "
    "as AC-PNDB1..AC-PNDB6; queue_head then read the new head at line 597 "
    "prefix AC-PNDB1 and queue_floor read FLOOR-MET main=5/5 tech=12/10 "
    "explore=10/10. DEBT through the shipped writers: product-face-R2558 "
    "closed (line 299, open 23->22, done 258->259, 174373B -> 174376B, "
    "readback ok), reconcile-battery-R2559 appended first=yes at the "
    "pre-registered 609/4630 (174376B -> 174507B) and product-face-R2559 "
    "appended first=no (174507B -> 174628B), both readback ok, so the gate "
    "now names that battery first. The round was declared through the "
    "shipped residue batch writer after a dry run at 301 -> 302 entries / "
    "83083B -> 83288B until R2569, after which residue_triage --check read "
    "TRIAGED with untriaged=0 at rc=0.",

    "2026-11-08 R2559 honest disclosures: (a) TWO product points on the "
    "Executive Protocol scale - a runnable CLI with its own suite and a "
    "bounded live reading a maintainer can run - but nothing a CEO could "
    "newly open and no P-47 business surface moved; (b) the defect was "
    "MEASURED at R2557 in that window own legs and re-measured here before "
    "shipping, so this is a repair of a disclosed gap rather than a new "
    "discovery; (c) THREE of my own first-pass defects were found by RUNNING "
    "rather than by review: the AC-PNDA6 stdlib assertion refused the "
    "legitimate import of the shipped reader this face EXTENDS (the "
    "assertion now names that one module explicitly instead of being "
    "widened), the registry row was first written with the suite filename "
    "split across two source lines so the suite saw zero wiring and the "
    "filename was put on one line rather than the counter loosened, and the "
    "live leg first called the WHOLE-TREE audit which produced no output "
    "until it was stopped, so the leg was rewritten BOUNDED to 8 modules "
    "and both readings are named here; (d) DISCLOSED LIMITS measured this "
    "window and seeded as the next tech row: a walrus attribute alias is not "
    "recorded at all, a subscript or call base is published as a question "
    "mark, a package own __init__ is never joined, and a with-as helper "
    "binding is not read; (e) the registry moved by one row and a shipped "
    "doc moved, so a battery on this committed tree is owed BEFORE any "
    "further product byte; (f) MEASURED DEFECT STILL OPEN from R2522: the "
    "shipped state_fold layout reader refuses this file, so this append used "
    "a PROVED load+dump round-trip instead of reformatting it; (g) Docker is "
    "absent on this host so no containerised bring-up is claimed; (h) the "
    "real 19.9 debit and the real msgSecCheck still wait on CEO physical "
    "items (merchant id, mini-program appid/secret); (i) tasks.md was not "
    "touched, it is the P-47 canonical board; (j) the S4U lane "
    "re-registration still needs an ELEVATED shell and remains a "
    "ceo-pending physical item with zero chase.",

    "R2559 tokens: local=~15k api=0 api_reason=product window - five-silence "
    "scan, one content-addressed decisions scan reading new=0, one "
    "zero-occupancy anchor check on five anchors, one pre-registered face "
    "shipped with its six criteria, one suite proved twice through the "
    "shipped capture callable plus five adjacent suites, one bounded live "
    "leg on the real tree with the same fixtures measured on BOTH readers, "
    "one registry row recounted by import, one matrix regeneration from an "
    "eligible battery leg checked byte-identical, one board row closed and "
    "one seeded through their shipped writers, three debt rows moved through "
    "their shipped writers, one residue declaration appended through its "
    "shipped batch writer, and the state/export/backlog/heartbeat closeout; "
    "zero cloud calls and zero external API touches",
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
    data["tick"] = 2559
    for line in LOG:
        data["log"].append(line)
    data["last_decision_rows"] = 72
    if "D-20261108-08" not in data["last_dec_tokens"]:
        data["last_dec_tokens"].append("D-20261108-08")
    payload = json.dumps(data, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = json.loads(io.open(STATE, encoding="utf-8").read())
    after = os.path.getsize(STATE)
    ok = (back["tick"] == 2559 and len(back["log"]) == len(data["log"]))
    print("STATE tick=2559 log=%d before=%dB after=%dB wrote=%s"
          % (len(back["log"]), before, after, "yes" if ok else "no"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())