import hashlib
import io
import os
import sys
import tempfile

sys.path.insert(0, "src/os")
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope as PNDC
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_from_scope as FSC

ROOT = os.path.join(os.getcwd(), "src", "os")
MODULES = [
    "probe_seam_registry.py",
    "probe_seam_forwarding_scope.py",
    "probe_seam_lazy_scope.py",
    "probe_seam_dynamic_import_scope.py",
    "probe_seam_constant_binding_scope.py",
    "probe_seam_local_constant_scope.py",
]


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


before = {name: digest(os.path.join(ROOT, name)) for name in MODULES}

resolved = 0
named = 0
loops = 0
files = 0
for name in MODULES:
    path = os.path.join(ROOT, name)
    with io.open(path, encoding="utf-8") as handle:
        text = handle.read()
    report = FSC.from_scope_report(text, ROOT)
    if not report["parsed"]:
        continue
    files += 1
    for loop in report["loops"]:
        loops += 1
        resolved += len(loop.get("from_resolved") or [])
        named += len(loop.get("from_refused") or [])

after = {name: digest(os.path.join(ROOT, name)) for name in MODULES}
read_only = before == after

lines = [
    "%s BOUNDED-READ files=%d loops=%d from_resolved=%d from_named=%d "
    "read_only=%r modules=%d"
    % (FSC.LABEL, files, loops, resolved, named, read_only, len(MODULES)),
]

root = tempfile.mkdtemp(prefix="live-pndce-")
os.makedirs(os.path.join(root, "pkg"))
for rel, body in (("pkg/helper.py", 'ATTR = "b"\n'),
                  ("hw3.py", 'ATTR = "b"\n')):
    path = os.path.join(root, *rel.split("/"))
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)

TAIL = "for name in hw.NAMES:\n    pass\n"
fixtures = {
    "from-import": "from pkg import helper\nif a1:\n    KEY = helper.ATTR\n"
                   "else:\n    KEY = helper.ATTR\n" + TAIL,
    "with-as-call": 'def open_module():\n    return "hw3"\n'
                    "with open_module() as m:\n"
                    "    if a1:\n        KEY = m.ATTR\n"
                    "    else:\n        KEY = m.ATTR\n" + TAIL,
}
for label in sorted(fixtures):
    text = fixtures[label]
    rows = FSC.from_scope_report(text, root)["loops"]
    mine = FSC.from_scope_entry("KEY", text, rows[-1]["scope"],
                                rows[-1]["line"], root=root)
    base = PNDC.import_alias_entry("KEY", text, rows[-1]["scope"],
                                   rows[-1]["line"], root=root)
    lines.append("%s mine=%s/%s base=%s/%s"
                 % (label, mine.get("state"), mine.get("value"),
                    base.get("ia_state") or "-",
                    base.get("ia_reason") or base.get("reason") or "-"))

path = os.path.join(os.getcwd(), "qa",
                    "probe-seam-name-binding-arm-mixed-residual-alias-"
                    "attribute-import-alias-scope-from-scope-live-R2565.log")
with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
    handle.write("\n".join(lines) + "\n")
with open(path, "rb") as handle:
    data = handle.read()
print("\n".join(lines))
print("BYTES=%d crlf=%d bom=%s"
      % (len(data), data.count(b"\r\n"), data.startswith(b"\xef\xbb\xbf")))