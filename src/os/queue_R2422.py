"""R2422 board edit: stamp the delivered seed row and seed one measured gap."""
import io
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

OLD_PREFIX = "- [ ] P2 tech seed (R2420, from this window own measured SCOPE limit): "

NEW_PREFIX = (
    "- [x] [done 2026-11-04 R2422] R2422 product window (seed R2420, the "
    "from-import gate own measured SCOPE limit): "
)

DELIVERED = (
    " DELIVERED R2422: src/os/plain_import_alias_gate.py plus its "
    "six-criteria suite, wired os-plain-import-alias-gate(6). One reading asks "
    "the receiver, absolute and relative tables at CALL time per plain-import "
    "line that binds the local name publish, prints all three answers side by "
    "side, and names every such line UNBOUND because neither publish-name "
    "table reads a plain import at all - measured, not assumed. AC-PIAG4 own "
    "wording was CORRECTED by that measurement: the word CLEAN is unreachable "
    "for this gate, so the vocabulary is ASYMMETRIC and EMPTY and the proof is "
    "the stronger one (every file carrying such a line is named). SUITE PASS "
    "6/6 twice with an identical criterion digest plus three adjacent suites "
    "green (qa/plain-import-alias-gate-R2422.log, two legs, 12 PASS lines), "
    "registry 539 suites / 4210 criteria. LIVE qa/"
    "plain-import-alias-gate-live-R2422.log reads the REAL src/os as "
    "verdict=EMPTY scanned=1161 files_with_imports=0, independently "
    "cross-checked at the same moment: zero plain imports bind publish while "
    "929 plain alias imports exist, so the gate fires the moment one uses that "
    "spelling. Second measured defect found by the fixtures and disclosed: for "
    "the comma-list spelling the receiver table itself reads only the LEADING "
    "module, so it binds nothing either."
)

SEED = (
    "- [ ] P2 tech seed (R2422, from this window own measured receiver-table "
    "blind spot): `src/os/plain_import_comma_binding.py` - the receiver table "
    "(export_publish_wire_identity.import_bindings) matches plain imports with "
    "an ANCHORED single-module pattern, so MEASURED at R2422 on a fixture, "
    "`import os, some_wire as publish` binds {\"os\": \"os\"} and publishes "
    "nothing about the second module: a comma-separated statement is read as "
    "its first module only, which means a bare `publish(` call on such a line "
    "can never resolve and the alias asymmetry is invisible even to the "
    "receiver side. Product: one reading that splits a plain-import statement "
    "on its own commas BEFORE the table is asked, so every module of the "
    "statement is bound and the receiver answer names which module the local "
    "name came from. Criteria AC-PICB1..AC-PICB6 pre-registered HERE BEFORE "
    "any code: AC-PICB1 the receiver table is asked at CALL time on the split "
    "parts and no import pattern is restated; AC-PICB2 "
    "`import os, some_wire as publish` binds publish to some_wire on the "
    "receiver side while both publish-name tables still answer {}, so the "
    "line reads UNBOUND and not silently skipped; AC-PICB3 a comma list whose "
    "second part does not bind publish counts exactly the parts that do; "
    "AC-PICB4 no file reads the gate empty word while a comma-list line binds "
    "publish unbound; AC-PICB5 CLI 0/2/3/5 with a byte-stable --json; "
    "AC-PICB6 writes nothing, reads no clock, ASCII, stdlib only, plus its own "
    "reconcile label and its own suite file."
)


def main():
    with io.open(TECH, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(eol)
    target = None
    for index, line in enumerate(lines):
        if line.startswith(OLD_PREFIX):
            target = index
            break
    if target is None:
        raise SystemExit("seed row not found")
    lines[target] = NEW_PREFIX + lines[target][len(OLD_PREFIX):] + DELIVERED
    lines.insert(target + 1, SEED)
    out = eol.join(lines)
    with io.open(TECH, "w", encoding="utf-8", newline="") as handle:
        handle.write(out)
    print("tech rows stamped=%d seeded=%d bytes=%d eol=%r"
          % (target + 1, target + 2, len(out.encode("utf-8")), eol))


if __name__ == "__main__":
    main()