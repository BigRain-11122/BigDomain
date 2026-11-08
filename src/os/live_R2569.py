"""Bounded live leg for the R2569 call-target face (same shape as live_R2565).

Reads a handful of real probe modules by TEXT (never the whole tree, never the
audit path), then measures four fixtures in a private temporary world on BOTH
readers so each closed gap is proved rather than asserted. Nothing outside the
temp dir is written.
"""

import hashlib
import io
import os
import sys
import tempfile

sys.path.insert(0, "src/os")
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_from_scope as PNDCE  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_call_target_scope as CT  # noqa

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
    report = CT.call_target_report(text, ROOT)
    if not report["parsed"]:
        continue
    files += 1
    for loop in report["loops"]:
        loops += 1
        resolved += len(loop.get("ct_resolved") or [])
        named += len(loop.get("ct_refused") or [])

after = {name: digest(os.path.join(ROOT, name)) for name in MODULES}
read_only = before == after

lines = [
    "%s BOUNDED-READ files=%d loops=%d ct_resolved=%d ct_named=%d "
    "read_only=%r modules=%d"
    % (CT.LABEL, files, loops, resolved, named, read_only, len(MODULES)),
]

root = tempfile.mkdtemp(prefix="live-pndcf-")
os.makedirs(os.path.join(root, "pkg"))
for rel, body in (
        ("hw3.py", 'ATTR = "b"\n'),
        ("helper.py", 'ATTR = "b"\n'),
        ("pkg/helper.py", 'ATTR = "b"\n'),
        ("nested.py", 'def outer():\n'
                      '    def inner():\n'
                      '        ATTR = "b"\n'
                      '        return ATTR\n'
                      '    return 1\n')):
    path = os.path.join(root, *rel.split("/"))
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)

TAIL = "for name in hw.NAMES:\n    pass\n"
ARMS = ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n")
fixtures = {
    "with-as-attribute": ('class Box:\n'
                          '    def open(self):\n'
                          '        return "hw3"\n'
                          'with Box().open() as m:\n'
                          '    if a1:\n        KEY = m.ATTR\n'
                          '    else:\n        KEY = m.ATTR\n' + TAIL),
    "local-return": ('def open_module():\n'
                     '    m = "hw3"\n'
                     '    return m\n'
                     'with open_module() as md:\n'
                     '    if a1:\n        KEY = md.ATTR\n'
                     '    else:\n        KEY = md.ATTR\n' + TAIL),
    "relative-from": ("from . import helper\n" + ARMS % ("helper.ATTR",
                                                         "helper.ATTR") + TAIL),
    "nested-constant": ("import nested\n" + ARMS % ("nested.ATTR",
                                                    "nested.ATTR") + TAIL),
}
for label in sorted(fixtures):
    text = fixtures[label]
    rows = CT.call_target_report(text, root)["loops"]
    mine = CT.call_target_entry("KEY", text, rows[-1]["scope"],
                                rows[-1]["line"], root=root)
    base = PNDCE.from_scope_entry("KEY", text, rows[-1]["scope"],
                                  rows[-1]["line"], root=root)
    lines.append("%s mine=%s/%s hop=%s base=%s/%s"
                 % (label, mine.get("state"), mine.get("value"),
                    mine.get("ct_hop"), base.get("state"), base.get("reason")))

path = os.path.join(os.getcwd(), "qa",
                    "probe-seam-name-binding-arm-mixed-residual-alias-"
                    "attribute-import-alias-scope-call-target-scope-live-"
                    "R2569.log")
with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
    handle.write("\n".join(lines) + "\n")
with open(path, "rb") as handle:
    data = handle.read()
print("\n".join(lines))
print("BYTES=%d crlf=%d bom=%s"
      % (len(data), data.count(b"\r\n"), data.startswith(b"\xef\xbb\xbf")))