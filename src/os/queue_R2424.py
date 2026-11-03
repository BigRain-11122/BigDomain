"""R2424 board edit: stamp the delivered seed row and seed one measured gap."""
import io
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

OLD_PREFIX = ("- [ ] P2 tech seed (R2422, from this window own measured "
              "receiver-table blind spot): ")

NEW_PREFIX = ("- [x] [done 2026-11-04 R2424] R2424 product window (seed R2422, "
              "the receiver-table comma blind spot): ")

DELIVERED = (
    " DELIVERED R2424: src/os/plain_import_comma_binding.py plus its "
    "six-criteria suite, wired os-plain-import-comma-binding(6) so the "
    "registry reads 540 suites / 4216 criteria. The module asks the SHIPPED "
    "splitter (plain_import_alias_gate.plain_parts) for the parts of a comma "
    "list and asks the SHIPPED receiver table "
    "(export_publish_wire_identity.import_bindings) once for the whole "
    "statement and once per part, printing both answers beside the two "
    "publish-name tables, so a dropped binding is named instead of silently "
    "skipped - measured on `import os, some_wire as publish`: whole-statement "
    "receiver {\"os\": \"os\"}, per-part receiver {\"os\": \"os\", "
    "\"publish\": \"some_wire\"}, dropped=publish, absolute {}, relative {}, "
    "verdict UNBOUND. No splitter, no import pattern and no table is "
    "restated: both are imported at CALL time and the suite proves it by "
    "patching each one and watching the reading move. HONEST CORRECTION of "
    "this window own first draft: the AC-PICB4 assertion said four dropped "
    "bindings across the four fixtures and the measurement read five, because "
    "a three-part list drops BOTH of its alias parts - the assertion was "
    "corrected to the measured number with the reason written beside it and "
    "the pinned AC-PICB4 wording was not touched. SUITE PASS 6/6 twice with "
    "an identical digest plus three adjacent suites green "
    "(qa/plain-import-comma-binding-R2424.log, 1562B, legs=2 identical=True "
    "adjacent=3 fails=0), with five further adjacent suites green when run "
    "directly. LIVE qa/plain-import-comma-binding-live-R2424.log (559B, "
    "class=tee crlf=0) reads the REAL src/os as verdict=EMPTY scanned=1170 "
    "comma_lines=0 - clean today, so the value is the guard and it is NOT "
    "claimed as a live catch - and a fixture in the same log names the "
    "dropped binding and exits 2."
)

SEED = (
    "- [ ] P2 tech seed (R2424, from this window own measured limit): "
    "`src/os/comma_binding_wire.py` - the reading now NAMES the dropped part, "
    "but the table still drops it: MEASURED this window, "
    "export_publish_wire_identity.import_bindings on "
    "`import os, some_wire as publish` answers {\"os\": \"os\"}, so callee_of "
    "on such a line returns module \"\" and the identity reading reports "
    "UNRESOLVED for a publisher that a bare `publish(` call would actually "
    "resolve. Product: the receiver table (or the callee path that asks it) "
    "splits a plain-import statement on its own commas before binding, so a "
    "comma-list publisher resolves instead of reading UNRESOLVED while the "
    "splitter stays owned by one shipped module. Criteria AC-PICBW1..AC-PICBW6 "
    "pre-registered HERE BEFORE any code: AC-PICBW1 the split is answered by "
    "the shipped splitter at CALL time and no import pattern is restated; "
    "AC-PICBW2 a comma-list publisher reads its real module from callee_of "
    "instead of module ''; AC-PICBW3 a single-module statement still resolves "
    "exactly as today, proved byte-identical against HEAD for every "
    "non-comma line; AC-PICBW4 a receiver no import binds still reads "
    "UNRESOLVED rather than being guessed; AC-PICBW5 every pre-existing "
    "refusal code, exit code and printed line of the identity reading is "
    "unchanged, proved against the HEAD module own captured refusal; "
    "AC-PICBW6 pure ASCII, stdlib only, zero network, no clock, own reconcile "
    "label and own suite. Five anchors to re-check zero-occupancy at HEAD "
    "before any code: comma_binding_wire, AC-PICBW, E_PICBW, "
    "os-comma-binding-wire, test_comma_binding_wire."
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