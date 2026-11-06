"""R2492 registry wiring: one row, os-relative-package-presence-refusal(6)."""
import io

P = "src/sandbox/reconcile_all.py"
OLD = ('    ("os-relative-module-corpus-scope",\n'
       '     os.path.join("..", "os", "test_relative_module_corpus_scope.py"), 6),\n')
NEW = OLD + (
    "    # R2492: the corpus scope face measures the tree root-wide, but nothing\n"
    "    # asked whether the DECLARED package is carried by it, so --package\n"
    "    # nosuchpkg joined every relative import onto a package that does not\n"
    "    # exist and published a declaration typo as N broken imports. A\n"
    "    # declaration with no module at or under it now refuses ONCE as\n"
    "    # E_RMPP_NO_PACKAGE, naming the declaration and the corpus searched, and\n"
    "    # no per-import MISSING-MODULE row is invented. A carried package keeps\n"
    "    # the parent reading byte for byte. (AC-RMPP1..AC-RMPP6 pinned in\n"
    "    # state/queue/tech.md as the R2440 seed row BEFORE the code.)\n"
    '    ("os-relative-package-presence-refusal",\n'
    '     os.path.join("..", "os", "test_relative_package_presence_refusal.py"), 6),\n')

text = io.open(P, encoding="utf-8", newline="").read()
assert text.count(OLD) == 1, text.count(OLD)
io.open(P, "w", encoding="utf-8", newline="").write(text.replace(OLD, NEW))
print("wired")