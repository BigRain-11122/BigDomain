"""R2428 board edit: stamp the delivered seed row and seed one measured gap."""
import io
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

OLD_PREFIX = ("- [ ] P2 tech seed (R2426, from this window own measured "
              "limit): ")

NEW_PREFIX = ("- [x] [done 2026-11-04 R2428] R2428 product window (seed "
              "R2426): ")

DELIVERED = (
    " DELIVERED R2428: src/os/comma_binding_consumer_wire.py plus its "
    "six-criteria suite, wired os-comma-binding-consumer-wire(6) so the "
    "registry measures 542 suites / 4228 criteria. The identity path now "
    "consumes the comma-aware table through ONE seam: "
    "export_publish_wire_identity.audit_script asks "
    "comma_binding_consumer_wire.wire_audit_script at CALL time, which hands a "
    "file with NO comma list to export_publish_from_import_law.classify_script "
    "unchanged (so those rows are byte for byte what they were) and a file "
    "WITH one to the same law's classify_line over "
    "comma_binding_wire.bindings - so the split, the import grammar and the "
    "spelling law each keep exactly one owner and none is restated. MEASURED "
    "LIVE, not a plan: on one fixture the HEAD identity module reads "
    "verdict=UNRESOLVED rc=2 naming comma_pub.py:7 module=(unbound) while the "
    "shipped reader reads verdict=WIRE rc=0 naming "
    "module=closeout_export_parity_wire; on the REAL src/os both read WIRE "
    "11/11 with 22 no_publish over 1180 scripts, unchanged. SUITE PASS 6/6 "
    "twice with an identical digest plus three adjacent suites green "
    "(qa/comma-binding-consumer-wire-R2428.log, 1594B, legs=2 identical=True "
    "adjacent=3 fails=0); live capture "
    "qa/comma-binding-consumer-wire-live-R2428.log (2763B). One earlier "
    "assertion was re-anchored at its birth site with the reason written "
    "beside it: AC-PICBW5 claimed whole-FILE byte equality between the "
    "identity module and its HEAD copy, which would have forbidden the very "
    "consumer this seed asked for; it now proves the refusal codes, exit codes "
    "and printed lines plus the unchanged row key set, which is what that "
    "criterion actually words. Zero cloud calls."
)

SEED = (
    "- [ ] P2 tech seed (R2428, from this window own measured limit): "
    "`src/os/comma_binding_sibling_faces.py` - the consumer reached the "
    "identity face, but the OTHER shipped faces still ask their own tables: "
    "MEASURED this window on the same comma-list fixture, "
    "export_publish_from_import_law --check reads verdict=UNRESOLVED rc=2 "
    "(comma_pub.py:6 receiver=CEPW module=(unbound)) and "
    "publish_relative_package_identity --check reads the same UNRESOLVED, "
    "while export_publish_wire_identity now reads WIRE. Product: the two "
    "sibling audit faces consume the comma-aware table through the same one "
    "seam, so one spelling cannot read WIRE on one face and UNRESOLVED on "
    "another, while every non-comma row stays byte for byte. Criteria "
    "AC-PICBS1..AC-PICBS6 pre-registered HERE BEFORE any code: AC-PICBS1 both "
    "faces ask the shipped consumer at CALL time and restate no split, proved "
    "by patching the table and watching both rows move; AC-PICBS2 the same "
    "comma-list fixture reads WIRE on every face that resolves publishers; "
    "AC-PICBS3 a script without a comma list keeps every key of every row "
    "byte-identical against HEAD on both faces; AC-PICBS4 a receiver no import "
    "binds still reads UNRESOLVED on both faces rather than being guessed; "
    "AC-PICBS5 every pre-existing refusal code, exit code and printed line of "
    "both CLIs is unchanged, proved against their HEAD copies; AC-PICBS6 pure "
    "ASCII, stdlib only, zero network, no clock, own reconcile label and own "
    "suite. Five anchors to re-check zero-occupancy at HEAD before any code: "
    "comma_binding_sibling_faces, AC-PICBS, E_PICBS, "
    "os-comma-binding-sibling-faces, test_comma_binding_sibling_faces."
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