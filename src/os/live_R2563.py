"""R2563 live leg: read REAL probe modules and measure both readers.

Bounded on purpose: an earlier round measured that a whole-tree walk costs
minutes, so this leg reads a named number of real probe_seam modules. Evidence is
written once by this script (utf-8, LF) and then read back; the module and both
faces it extends are hashed before and after so the reading is proved read-only.

It also measures the SAME fixture on BOTH readers, which is the whole point of
the face: a private world where the honest answer is `b` is read through the
predicate face and through this one and both answers are printed.
"""

import hashlib
import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_predicate_scope as PNDB  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope as PNDC  # noqa

EVIDENCE = os.path.join(
    "qa", "probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
          "import-alias-scope-live-R2563.log")
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


def world(files):
    root = tempfile.mkdtemp(prefix="pndc-live-")
    for name, body in files.items():
        with open(os.path.join(root, name), "w", encoding="utf-8",
                  newline="\n") as handle:
            handle.write(body)
    return root


def fixture():
    """The import-alias fixture, measured on BOTH readers."""
    text = ('import helper as h\n'
            'if a1:\n    KEY = h.ATTR\nelse:\n    KEY = h.ATTR\n'
            'for name in hw.NAMES:\n    pass\n')
    root = world({"helper.py": 'ATTR = "b"\n'})
    try:
        line = text.split("\n").index("for name in hw.NAMES:") + 1
        shipped = PNDB.predicate_entry("KEY", text, "module", line, root=root)
        face = PNDC.import_alias_entry("KEY", text, "module", line, root=root)
        return (shipped.get("pred_state"), shipped.get("pred_reason"),
                face.get("state"), face.get("value"), face.get("ia_hop"),
                face.get("ia_chain"))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    mine = os.path.join(BASE, PNDC.__name__ + ".py")
    base = os.path.join(BASE, PNDB.__name__ + ".py")
    before = (digest(mine), digest(base))
    lines = ["LIVE LEG round=R2563 modules=%d limit=%d\n"
             % (len(modules()), LIMIT)]
    totals = {"loops": 0, "ia_resolved": 0, "ia_named": 0,
              "pred_resolved": 0, "pred_named": 0}
    for name in modules():
        path = os.path.join(BASE, name)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        try:
            shipped = PNDB.predicate_report(text, BASE)
            got = PNDC.import_alias_report(text, BASE)
        except Exception as exc:  # a refusal is reported, never swallowed
            lines.append("MODULE %s UNREADABLE %s\n" % (name, exc))
            continue
        pred_resolved = 0
        pred_named = 0
        for loop in shipped["loops"]:
            pred_resolved += len(loop.get("pred_resolved") or [])
            pred_named += len(loop.get("pred_refused") or {})
        ia_resolved = 0
        ia_named = 0
        for loop in got["loops"]:
            ia_resolved += len(loop.get("ia_resolved") or [])
            ia_named += len(loop.get("ia_refused") or {})
        totals["loops"] += len(got["loops"])
        totals["ia_resolved"] += ia_resolved
        totals["ia_named"] += ia_named
        totals["pred_resolved"] += pred_resolved
        totals["pred_named"] += pred_named
        lines.append(
            "MODULE %s loops=%d pred_resolved=%d pred_named=%d "
            "ia_resolved=%d ia_named=%d\n"
            % (name, len(got["loops"]), pred_resolved, pred_named,
               ia_resolved, ia_named))
    after = (digest(mine), digest(base))
    pred_state, pred_reason, state, value, hop, chain = fixture()
    lines.append("FIXTURE import-alias pred=%s/%s face=%s/%s hop=%s chain=%s\n"
                 % (pred_state, pred_reason, state, value, hop, chain))
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
          % (len(landed), landed == body, verdict, totals, before == after))
    return 0 if landed == body and before == after else 2


if __name__ == "__main__":
    sys.exit(main())