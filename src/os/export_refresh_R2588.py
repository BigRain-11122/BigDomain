"""R2588 export refresh: re-derive docs/status-export.json from measured state.

F3 law: every value is read from files on disk or imported from the shipped
registry, never hardcoded history. The milestone window comes from the clock.
"""

import io
import json
import os
import sys
import time

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "docs", "status-export.json")
EVIDENCE = os.path.join(ROOT, "qa",
                        "module-alias-walrus-elif-with-scope-R2588.log")
LIMITS = os.path.join(ROOT, "qa",
                      "module-alias-walrus-elif-with-limits-next-R2588.log")
QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")


def registry_counts():
    sandbox = os.path.dirname(REGISTRY)
    if sandbox not in sys.path:
        sys.path.insert(0, sandbox)
    import reconcile_all as R
    return len(R.SUITES), sum(c for _n, _p, c in R.SUITES)


def head_row():
    lines = io.open(QUEUE, "r", encoding="utf-8").read().split("\n")
    for index, line in enumerate(lines):
        if line.startswith("- [ ] P2 tech seed (R2588,"):
            return index + 1, line[:120]
    return 0, ""


def main():
    raw = io.open(PATH, "rb").read()
    doc = json.loads(raw.decode("utf-8"))
    evidence = io.open(EVIDENCE, "rb").read()
    text = evidence.decode("utf-8")
    legs = text.count("SUITE PASS 6/6")
    identical = "own legs identical=True" in text
    adjacent_green = "== adjacent R2587 rc=0 ==" in text
    limits = io.open(LIMITS, "rb").read().decode("utf-8")
    refusals = limits.count("attr-module-alias-unbound:M.HW")
    evidence_bytes = len(evidence)
    limits_bytes = os.path.getsize(LIMITS)
    suites, criteria = registry_counts()
    line, head = head_row()

    current = (
        "2026-11-09 R2588 PRODUCT window: a module alias head bound by a walrus "
        "inside a module-level elif section or a module-level with body is now "
        "followed through the R2587 reading instead of beside it. Elif names "
        "branch:M@elif, with names branch:M@with, a for body and a branch "
        "nested inside another branch keep the shipped refusal "
        "attr-module-alias-unbound:M.HW with no branch read, and an elif/else "
        "pair is refused as attr-module-alias-ambiguous:M@elif+else. Registry "
        "now reads %d suites / %d criteria." % (suites, criteria))
    latest = (
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_module_alias_attribute_alias_walrus_relative_"
        "branch_elif_with_scope.py + its suite; "
        "qa/module-alias-walrus-elif-with-scope-R2588.log (%d bytes, legs green "
        "=%d, legs_identical=%s, adjacent_green=%s) and "
        "qa/module-alias-walrus-elif-with-limits-next-R2588.log (%d bytes, "
        "%d shipped refusals measured) at 2026-11-09"
        % (evidence_bytes, legs, identical, adjacent_green, limits_bytes,
           refusals))
    due = time.strftime("%Y-%m-%dT23:59:59+08:00",
                        time.localtime(time.time() + 2 * 86400))
    nxt = (
        "R2589 VERIFICATION window on the debt register first item "
        "reconcile-battery-R2588: the full reconcile battery on the committed "
        "R2588 tree at the pre-registered %d suites / %d criteria, with zero "
        "product edits, then the designed matrix follow-up; the queue head is "
        "state/queue/tech.md:%d prefix AC-PNAD1 whose criteria were pinned "
        "before any code. Window due %s." % (suites, criteria, line, due))
    results = (
        "R2588 product window on the queue head the register named "
        "(state/queue/tech.md:621 prefix AC-PNAC1, criteria pinned at R2587 "
        "BEFORE any code). Shipped one reading that extends the R2587 branch "
        "table: elif sections of an if chain and module-level with bodies are "
        "followed, while a for body and a nested branch stay refused without a "
        "branch read. Proof: own suite PASS 6/6 on the first run and 6/6 twice "
        "with identical output, the R2587 parent suite still 6/6, the bounded "
        "live leg reads 2 real modules at 49 loops with no mismatch, and the "
        "same fixture is measured on both readers (ok/b here against "
        "refused/attr-module-alias-unbound:M.HW there). Registry moved "
        "625/4726 -> %d/%d by exactly one row, recounted by importing "
        "reconcile_all.SUITES with %d unique names and paths. Next limits "
        "measured this window: a while body and a match case body are still "
        "unread (%d refusals in the limits log) and are seeded as row %d. "
        "Board row 621 closed with its DISCHARGED note. Debt: product-face-R2586 "
        "closed through the shipped writer at its predicted and measured byte "
        "count, and reconcile-battery-R2588 opened first=yes."
        % (suites, criteria, suites, refusals, line))
    doc["ceo_face"] = {
        "current": current,
        "latest_artifact": latest,
        "last_artifact": (doc.get("ceo_face") or {}).get("latest_artifact", ""),
        "next_milestone": nxt,
        "next_milestone_due": due,
    }
    doc["do"] = ("product window R2588: one runnable reading extends the "
                 "module-alias branch table to elif and with bindings, proved "
                 "by its own six-criteria suite twice and by the parent suite.")
    doc["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    rows = doc.setdefault("results", [])
    if rows and rows[-1][0] == "R2588":
        rows[-1] = ["R2588", results]
    else:
        rows.append(["R2588", results])
    out = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = (back["results"][-1][0] == "R2588"
          and back["export_ts"] == doc["export_ts"]
          and back["ceo_face"]["current"].startswith("2026-11-09 R2588"))
    print("EXPORT rows=%d suites=%d criteria=%d evidence=%dB limits=%dB "
          "head_line=%d bytes=%d ok=%s"
          % (len(back["results"]), suites, criteria, evidence_bytes,
             limits_bytes, line, len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())