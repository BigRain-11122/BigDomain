import hashlib
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(BASE, "state", "queue", "tech.md")


def names_free(needles):
    """Every anchor must be zero-occupancy under src/ and qa/."""
    hits = {}
    for needle in needles:
        found = []
        for tree in (os.path.join(BASE, "src"), os.path.join(BASE, "qa")):
            for root, dirs, files in os.walk(tree):
                for name in files:
                    path = os.path.join(root, name)
                    try:
                        with io.open(path, "r", encoding="utf-8",
                                     errors="ignore") as handle:
                            text = handle.read()
                    except (IOError, OSError):
                        continue
                    rel = os.path.relpath(path, BASE).replace(os.sep, "/")
                    if rel == "src/os/board_R2402.py":
                        continue
                    if needle in text:
                        found.append(os.path.relpath(path, BASE))
        hits[needle] = found
    return hits


SEED_A = (
    " - [ ] P2 tech seed (R2402, from this window own measured limit): "
    "`src/os/publish_relative_package_identity.py` - the relative binding now "
    "NAMES the relative module text but nothing can place it: this law reads a "
    "file on its own, so `from . import publish` is reported RELATIVE at exit 2 "
    "even when the file IS the wire module inside its own package. MEASURED "
    "this window on a fixture: the same file spelled `from "
    "closeout_export_parity_wire import publish` reads WIRE at exit 0, while the "
    "relative spelling stays RELATIVE. Product: a caller-DECLARED package joins "
    "the relative text (`.` -> package, `.wire` -> package.wire) and the call "
    "then resolves WIRE/FOREIGN like an absolute one, with the declaration "
    "refused by name when it cannot be joined. Criteria AC-PRPI1..AC-PRPI6 "
    "pre-registered HERE BEFORE any code: AC-PRPI1 a declared package resolves "
    "`.M` to `package.M`; AC-PRPI2 `.` resolves to the package itself; AC-PRPI3 "
    "no package keeps today's RELATIVE reading byte for byte; AC-PRPI4 a "
    "declaration that cannot be joined refuses naming it, never guessing an "
    "absolute module; AC-PRPI5 CLI 0/2/3/5 with a byte-stable --json; AC-PRPI6 "
    "writes nothing, reads no clock, ASCII, stdlib only, plus its own reconcile "
    "label and its own suite file.\n"
)

SEED_B = (
    " - [ ] P2 tech seed (R2402, from this window own measured asymmetry): "
    "`src/os/relative_import_alias_gate.py` - the two binding tables answer "
    "different alias questions and nothing says which is intended: MEASURED "
    "this window, the ABSOLUTE table (the parent law) binds the local alias of "
    "ANY imported name (`from some_wire import other as publish` binds "
    "publish), while the RELATIVE table binds only when the imported name IS "
    "`publish`, so `from .wire import other as publish` binds nothing and the "
    "call reads bare/UNRESOLVED. Product: one reading names the asymmetry per "
    "file with both spellings side by side, so the next window decides instead "
    "of inheriting whichever side it looked at last. Criteria "
    "AC-RIAG1..AC-RIAG6 pre-registered HERE BEFORE any code: AC-RIAG1 the two "
    "tables are asked at CALL time and neither is restated; AC-RIAG2 a "
    "renamed-import fixture reads bound on the absolute side and unbound on the "
    "relative side, both printed; AC-RIAG3 a matching-import fixture reads "
    "bound on both; AC-RIAG4 no file reads CLEAN while the two tables disagree; "
    "AC-RIAG5 CLI 0/2/3/5 with a byte-stable --json; AC-RIAG6 writes nothing, "
    "reads no clock, ASCII, stdlib only, plus its own reconcile label and its "
    "own suite file.\n"
)

anchors = ("publish_relative_package_identity", "AC-PRPI", "E_PRPI",
           "os-publish-relative-package-identity",
           "test_publish_relative_package_identity",
           "relative_import_alias_gate", "AC-RIAG", "E_RIAG",
           "os-relative-import-alias-gate", "test_relative_import_alias_gate")
hits = names_free(anchors)
occupied = {name: where for name, where in hits.items() if where}
if occupied:
    sys.stderr.write("E_SEED_OCCUPIED %r\n" % (occupied,))
    sys.exit(2)

with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
    text = handle.read()
raw_before = len(text.encode("utf-8"))

lines = text.splitlines(True)
target = None
for index, line in enumerate(lines):
    if line.startswith("- [ ] P2 tech seed (R2400, from this window own "
                        "measured gap): `src/os/"
                        "relative_import_publish_binding.py`"):
        target = index
        break
if target is None:
    sys.stderr.write("E_SEED_ROW_NOT_FOUND\n")
    sys.exit(3)

lines[target] = lines[target].replace(
    "- [ ] P2 tech seed (R2400", "- [x] [done 2026-11-03 R2402] P2 tech seed "
    "(R2400", 1)

if not lines[-1].endswith("\n"):
    lines[-1] = lines[-1] + "\n"
lines.append(SEED_A.replace("\n - [ ]", "- [ ]", 1))
lines.append("\n")
lines.append(SEED_B.replace("\n - [ ]", "- [ ]", 1))

body = "".join(lines)
with io.open(PATH, "w", encoding="utf-8", newline="") as handle:
    handle.write(body)

after = io.open(PATH, "r", encoding="utf-8", newline="").read()
ok = ("- [x] [done 2026-11-03 R2402] P2 tech seed (R2400" in after
      and "AC-PRPI1..AC-PRPI6" in after and "AC-RIAG1..AC-RIAG6" in after
      and after.count("- [ ] P2 tech seed") == text.count("- [ ] P2 tech seed") + 1)
print("BOARD staged_rows=1 seeded=2 bytes %d -> %d anchors_free=%d ok=%s"
      % (raw_before, len(after.encode("utf-8")), len(anchors), ok))
print("sha16 before=%s after=%s"
      % (hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
         hashlib.sha256(after.encode("utf-8")).hexdigest()[:16]))
sys.exit(0 if ok else 1)