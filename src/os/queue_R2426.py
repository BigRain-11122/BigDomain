"""R2426 board edit: stamp the delivered seed row and seed one measured gap."""
import io
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

OLD_PREFIX = ("- [ ] P2 tech seed (R2424, from this window own measured "
              "limit): ")

NEW_PREFIX = ("- [x] [done 2026-11-04 R2426] R2426 product window (seed "
              "R2424): ")

DELIVERED = (
    " DELIVERED R2426: src/os/comma_binding_wire.py plus its six-criteria "
    "suite, wired os-comma-binding-wire(6) so the registry reads 541 suites / "
    "4222 criteria. ONE seam is closed and no law is added: the parts of a "
    "comma list come from the SHIPPED splitter "
    "(plain_import_comma_binding.parts_of), the per-part question from the "
    "SHIPPED composition (part_statement), the receiver table from "
    "export_publish_wire_identity.import_bindings and the callee law from that "
    "same module own callee_of - all asked at CALL time, so there is still "
    "exactly one import table and one publish-call law in the tree, and the "
    "suite proves it by patching the splitter and the table and watching the "
    "row move. MEASURED: `import os, some_wire as wiremod` + "
    "`wiremod.publish(...)` reads table_module \"\" (UNRESOLVED) through "
    "import_bindings and wire_module some_wire (BOUND) through this wire, "
    "resolved=1 unresolved=0 at exit 0. HONEST CORRECTION of the seed premise, "
    "measured before any code: the seed spelling `import os, some_wire as "
    "publish` with a BARE `publish(` call cannot be resolved by callee_of at "
    "all, because that law reads ATTRIBUTE calls; the real defect shape is the "
    "house alias receiver (`import os, closeout_export_parity_wire as CEPW` "
    "then `CEPW.publish(...)`), so this wire re-reads EVERY comma list and the "
    "module header says why instead of repeating the seed. SUITE PASS 6/6 "
    "twice with an identical digest plus three adjacent suites green "
    "(qa/comma-binding-wire-R2426.log, 1626B, legs=2 identical=True "
    "adjacent=3 fails=0). LIVE qa/comma-binding-wire-live-R2426.log reads the "
    "REAL src/os as verdict=EMPTY scanned=1175 compared=1173 parity=1167 "
    "comma_files=6 comma_lines=6 resolved=0 unresolved=0 - six comma lists "
    "exist but none binds a publisher, so the value today is the guard and it "
    "is NOT claimed as a live catch - while a fixture in the same log reads "
    "RESOLVED with table_module=(unbound) beside wire_module=some_wire. The "
    "same log measures the gap seeded below: the identity face on that same "
    "fixture still answers EMPTY publishers=0, because nothing consumes this "
    "wire yet."
)

SEED = (
    "- [ ] P2 tech seed (R2426, from this window own measured limit): "
    "`src/os/comma_binding_consumer_wire.py` - the wire RESOLVES a comma-list "
    "publisher, but no shipped reading asks it: MEASURED this window on one "
    "fixture, the new wire reads RESOLVED receiver=wiremod "
    "wire_module=some_wire while export_publish_wire_identity on the very same "
    "tree still answers EMPTY publishers=0, because that reading asks its own "
    "import_bindings and export_publish_from_import_law.classify_script still "
    "reports a receiver it cannot bind as UNRESOLVED, i.e. the fix exists but "
    "is on no face an operator reads. Product: the identity path consumes the "
    "comma-aware table, so a comma-list publisher is named WIRE or FOREIGN "
    "with its module instead of UNRESOLVED, while every script without a comma "
    "list keeps the row it has today byte for byte. Criteria AC-PICBC1.."
    "AC-PICBC6 pre-registered HERE BEFORE any code: AC-PICBC1 the consumer "
    "asks comma_binding_wire.bindings at CALL time and restates no split, "
    "proved by patching the wire and watching the identity row move; AC-PICBC2 "
    "a comma-list publisher on the identity path reads WIRE (or FOREIGN when "
    "the module is not the wire) with the module named, instead of UNRESOLVED "
    "or NO-PUBLISH; AC-PICBC3 a script with no comma list keeps its identity "
    "row byte-identical, proved by comparing every key of every row against "
    "HEAD; AC-PICBC4 a receiver no import binds still reads UNRESOLVED rather "
    "than being guessed; AC-PICBC5 every pre-existing refusal code, exit code "
    "and printed line of the identity CLI is unchanged, proved against the "
    "HEAD module own captured refusal; AC-PICBC6 pure ASCII, stdlib only, zero "
    "network, no clock, own reconcile label and own suite. Five anchors to "
    "re-check zero-occupancy at HEAD before any code: "
    "comma_binding_consumer_wire, AC-PICBC, E_PICBC, "
    "os-comma-binding-consumer-wire, test_comma_binding_consumer_wire."
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