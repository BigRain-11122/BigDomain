"""R2561 live leg: read the REAL probe modules and measure both readers.

Bounded on purpose: an earlier round measured that a whole-tree walk costs
minutes, so this leg reads a named list of real probe_seam modules. Evidence is
written once by this script (utf-8, LF) and then read back; the module and its
base face are hashed before and after so the reading is proved read-only.
"""

import hashlib
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_base as PNDA  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_predicate_scope as P  # noqa

EVIDENCE = os.path.join(
    "qa", "probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
          "predicate-live-R2561.log")
LIMIT = 5


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def modules():
    names = []
    for name in sorted(os.listdir(BASE)):
        if name.startswith("probe_seam") and name.endswith(".py"):
            names.append(name)
    return names[:LIMIT]


def main():
    mine = os.path.join(BASE, P.__name__ + ".py")
    base = os.path.join(BASE, PNDA.__name__ + ".py")
    before = (digest(mine), digest(base))
    lines = ["LIVE LEG round=R2561 modules=%d limit=%d\n"
             % (len(modules()), LIMIT)]
    totals = {"loops": 0, "attr_resolved": 0, "attr_named": 0,
              "pred_resolved": 0, "pred_named": 0}
    for name in modules():
        path = os.path.join(BASE, name)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        try:
            shipped = PNDA.attribute_report(text, BASE)
            got = P.predicate_report(text, BASE)
        except Exception as exc:  # a refusal is reported, never swallowed
            lines.append("MODULE %s UNREADABLE %s\n" % (name, exc))
            continue
        attr_resolved = 0
        attr_named = 0
        for loop in shipped["loops"]:
            attr_resolved += len(loop.get("attr_resolved") or [])
            attr_named += len(loop.get("attr_refused") or {})
        pred_resolved = 0
        pred_named = 0
        for loop in got["loops"]:
            pred_resolved += len(loop.get("pred_resolved") or [])
            pred_named += len(loop.get("pred_refused") or {})
        totals["loops"] += len(got["loops"])
        totals["attr_resolved"] += attr_resolved
        totals["attr_named"] += attr_named
        totals["pred_resolved"] += pred_resolved
        totals["pred_named"] += pred_named
        lines.append(
            "MODULE %s loops=%d base_resolved=%d base_named=%d "
            "pred_resolved=%d pred_named=%d\n"
            % (name, len(got["loops"]), attr_resolved, attr_named,
               pred_resolved, pred_named))
    after = (digest(mine), digest(base))
    unreadable = sum(1 for line in lines if "UNREADABLE" in line)
    verdict = ("BOUNDED-READ-CLEAN" if unreadable == 0
               else "BOUNDED-READ-DIRTY")
    lines.append("READONLY mine=%s base=%s\n"
                 % ("yes" if before[0] == after[0] else "no",
                    "yes" if before[1] == after[1] else "no"))
    lines.append("TOTALS %s\n"
                 % " ".join("%s=%s" % (key, totals[key])
                            for key in sorted(totals)))
    lines.append("VERDICT %s modules=%d unreadable=%d note=%s\n"
                 % (verdict, len(modules()), unreadable,
                    "the whole-tree audit was NOT run: an earlier round "
                    "measured it costing minutes, so this leg is bounded"))
    path = os.path.join(ROOT, EVIDENCE)
    body = "".join(lines).encode("utf-8")
    with open(path, "wb") as handle:
        handle.write(body)
    landed = io.open(path, "rb").read()
    print("LIVE bytes=%d identical=%s verdict=%s totals=%s readonly=%s"
          % (len(landed), landed == body, verdict, totals,
             before == after))
    return 0 if landed == body and before == after else 2


if __name__ == "__main__":
    sys.exit(main())