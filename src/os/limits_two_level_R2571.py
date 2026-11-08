"""Measure, on one private world, the four shapes this R2571 face was seeded
on and the shapes it still leaves open.

Every shape runs through the shipped entry so the reading is measured rather
than assumed. Writes nothing outside a temp dir, and prints one machine line of
facts so the board row can quote measured numbers instead of prose.
"""

import io
import os
import shutil
import sys
import tempfile

sys.path.insert(0, "src/os")
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_two_level_scope as TL  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_call_target_scope as CT  # noqa

TAIL = "for name in hw.NAMES:\n    pass\n"


def world(files):
    root = tempfile.mkdtemp(prefix="lim-pndcg-")
    for name, body in files.items():
        path = os.path.join(root, *name.split("/"))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def arms(binding):
    return ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n"
            % (binding, binding))


def entry(text, root, name="KEY", src=None):
    mine = TL.two_level_report(text, root, src)["loops"]
    theirs = CT.call_target_report(text, root)["loops"]
    if not mine:
        return {}, {}
    return (TL.two_level_entry(name, text, mine[-1]["scope"],
                               mine[-1]["line"], root=root, src_path=src),
            CT.call_target_entry(name, text, theirs[-1]["scope"],
                                 theirs[-1]["line"], root=root) if theirs
            else {})


def show(label, mine, theirs):
    print("%-24s mine=%s/%s hop=%s reason=%s | shipped=%s/%s %s"
          % (label, mine.get("state"), mine.get("value"),
             mine.get("tl_hop"), mine.get("reason"),
             theirs.get("state"), theirs.get("value"),
             theirs.get("reason")))


FLAT = {"hw3.py": 'ATTR = "b"\n', "helper.py": 'ATTR = "b"\n'}

# 1: two-level relative WITH an anchor (module text on disk under pkg/sub/).
body = ("from .. import helper\n" + arms("helper.ATTR") + TAIL)
root = world(dict(FLAT, **{"pkg/helper.py": 'ATTR = "b"\n',
                           "pkg/sub/mod.py": body}))
show("two-level-anchored", *entry(body, root, src=os.path.join(
    root, "pkg", "sub", "mod.py")))
shutil.rmtree(root, ignore_errors=True)

# 1b: two-level relative with NO anchor (the R2569 limit, must stay refused).
root = world(dict(FLAT))
show("two-level-no-anchor", *entry(body, root))
shutil.rmtree(root, ignore_errors=True)

# 2: with-as call on a method defined in ANOTHER module.
root = world({"hw3.py": 'ATTR = "b"\n',
              "mk.py": 'class Box:\n    def open(self):\n'
                       '        n = "hw3"\n        return n\n'})
body2 = ('import mk\nwith mk.Box().open() as m:\n'
         '    if a1:\n        KEY = m.ATTR\n'
         '    else:\n        KEY = m.ATTR\n' + TAIL)
show("cross-module-method", *entry(body2, root))
shutil.rmtree(root, ignore_errors=True)

# 2b: the same call returning something that is not a module.
root = world({"hw3.py": 'ATTR = "b"\n',
              "mk.py": 'class Box:\n    def open(self):\n'
                       '        return 1\n'})
body2b = ('import mk\nwith mk.Box().open() as m:\n'
          '    if a1:\n        KEY = m.ATTR\n'
          '    else:\n        KEY = m.ATTR\n' + TAIL)
show("cross-module-nonmodule", *entry(body2b, root))
shutil.rmtree(root, ignore_errors=True)

# 3: class-body constant through its class path.
root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
show("class-body", *entry("import cls\n" + arms("cls.K.ATTR") + TAIL, root))
shutil.rmtree(root, ignore_errors=True)

# 4: relative FROM-import of a NAME is refused with its own word.
root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
show("relative-from-name", *entry("from .cls import K\n"
                                  + arms("K.ATTR") + TAIL, root))
shutil.rmtree(root, ignore_errors=True)

# --- shapes this face still leaves open, measured for the next seed ---------
# 5: a level-3 relative import (two directories up).
body3 = ("from ... import helper\n" + arms("helper.ATTR") + TAIL)
root = world({"helper.py": 'ATTR = "b"\n',
              "pkg/pkg2/sub/mod.py": body3})
show("three-level", *entry(body3, root, src=os.path.join(
    root, "pkg", "pkg2", "sub", "mod.py")))
shutil.rmtree(root, ignore_errors=True)

# 6: `from . import cls` then cls.K.ATTR (the class path hangs off the module).
root = world({"pkg/pkg2/cls.py": 'class K:\n    ATTR = "b"\n',
              "pkg/pkg2/sub/mod.py": "from . import cls\n"
              + arms("cls.K.ATTR") + TAIL})
show("module-then-class", *entry("from . import cls\n"
                                 + arms("cls.K.ATTR") + TAIL, root,
                                 src=os.path.join(root, "pkg", "pkg2",
                                                  "sub", "mod.py")))
shutil.rmtree(root, ignore_errors=True)

# 7: a class-body constant inherited from a base class in the same module.
root = world({"cls.py": 'class Base:\n    ATTR = "b"\n\nclass K(Base):\n'
                        '    pass\n'})
show("inherited-class-attr", *entry("import cls\n" + arms("cls.K.ATTR")
                                    + TAIL, root))
shutil.rmtree(root, ignore_errors=True)

# 8: a with-as cross-module call whose method returns through a class attr.
root = world({"hw3.py": 'ATTR = "b"\n',
              "mk.py": 'class Box:\n    NAME = "hw3"\n'
                       '    def open(self):\n        return self.NAME\n'})
show("cross-call-self-attr", *entry(body2, root))
shutil.rmtree(root, ignore_errors=True)

# 9: a two-level relative import of a NAME rather than a module.
root = world({"pkg/cls.py": 'class K:\n    ATTR = "b"\n',
              "pkg/sub/mod.py": "from ..cls import K\n" + arms("K.ATTR")
              + TAIL})
show("two-level-from-name", *entry("from ..cls import K\n"
                                   + arms("K.ATTR") + TAIL, root,
                                   src=os.path.join(root, "pkg", "sub",
                                                    "mod.py")))
shutil.rmtree(root, ignore_errors=True)