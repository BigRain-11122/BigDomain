import io

P = "state/queue/tech.md"
text = io.open(P, encoding="utf-8", newline="").read()
lines = text.split("\n")
target = None
for i, line in enumerate(lines):
    if line.startswith("- [ ] P2 tech seed (R2440, from this window own measured "
                        "limit): src/os/relative_module_corpus_scope.py"):
        target = i
        break
assert target is not None, "row not found"

lines[target] = lines[target].replace(
    "- [ ] P2 tech seed (R2440,",
    "- [x] [done 2026-11-06 R2491] P2 tech seed (R2440,", 1)

discharged = (
    "  DISCHARGED R2491 (line 525, AC-RMSC1..AC-RMSC6, pinned at R2440 BEFORE "
    "any code): src/os/relative_module_corpus_scope.py plus "
    "src/os/test_relative_module_corpus_scope.py shipped. Every MISSING-MODULE "
    "row now carries the scope it was judged against - scope_root (the root as "
    "given) and scope_corpus (the merged corpus size) - and caller-declared "
    "--extra names are merged ON TOP of the measured tree, never replacing it. "
    "The corpus is ONE root-wide walk asked once per check (proved: the walk "
    "counter reads 1 and the module never imports the R2440 face), so a module "
    "the tree carries under another top-level package is present - proved on a "
    "fixture whose publisher sits in scripts/ while the package sits in mypkg/, "
    "where a scoped walk reads MISSING and the real walk reads WIRE. The join "
    "and the WIRE/FOREIGN word stay publish_relative_package_identity own at "
    "CALL time: an extra makes a module PRESENT and cannot invent a wire "
    "(merged reading FOREIGN == the parent's own). MEASURED on the real tree: "
    "root=src/os package=src.os verdict=WIRE corpus=1402 scanned=1400 "
    "publishers=11 wire=11 relative=0 missing=0, and the seed's own defect "
    "reproduced live end to end - a scripts/ root reads MISSING-MODULE with "
    "scope printed, --extra clears it, and the whole-tree root clears it too "
    "(qa/relative-module-corpus-scope-live-R2491.log, 1666B utf-8 LF, "
    "crlf=0). Proof: AC-RMSC1..AC-RMSC6 SUITE PASS 6/6 TWICE with identical "
    "verdicts plus three adjacent suites green "
    "(qa/relative-module-corpus-scope-R2491.log, 1413B, legs=2 identical=True). "
    "Registry 573/4414 -> 574/4420 by exactly one row "
    "os-relative-module-corpus-scope(6); matrix restamped stamp-aligned from "
    "qa/reconcile-all-R2490.log to 55073B at 574/4420 with --check "
    "byte-identical, its green line honestly reading 573/574."
)
lines.insert(target + 1, discharged)

io.open(P, "w", encoding="utf-8", newline="").write("\n".join(lines))
print("tech row closed at line %d" % (target + 1))