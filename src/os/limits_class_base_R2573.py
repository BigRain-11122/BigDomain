"""Measure, on one private world, the four shapes the R2573 face was seeded on
and the shapes it still leaves open.

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
    root = tempfile.mkdtemp(prefix="lim-pndch-")
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
    print("%-26s twolevel=%s/%s hop=%s reason=%s | shipped=%s/%s %s"
          % (label, mine.get("state"), mine.get("value"),
             mine.get("tl_hop"), mine.get("reason"),
             theirs.get("state"), theirs.get("value"),
             theirs.get("reason")))


# 1: a class-body constant inherited from a base class in the same module.
root = world({"cls.py": 'class Base:\n    ATTR = "b"\n\nclass K(Base):\n'
                        '    pass\n'})
show("inherited-class-attr", *entry("import cls\n" + arms("cls.K.ATTR")
                                    + TAIL, root))
shutil.rmtree(root, ignore_errors=True)

# 2: an absolute FROM-imported CLASS read as K.ATTR.
root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
show("absolute-from-class", *entry("from cls import K\n" + arms("K.ATTR")
                                   + TAIL, root))
shutil.rmtree(root, ignore_errors=True)

# 3: a with-as cross-module call whose method returns through a class attr.
body2 = ('import mk\nwith mk.Box().open() as m:\n'
         '    if a1:\n        KEY = m.ATTR\n'
         '    else:\n        KEY = m.ATTR\n' + TAIL)
root = world({"hw3.py": 'ATTR = "b"\n',
              "mk.py": 'class Box:\n    NAME = "hw3"\n'
                       '    def open(self):\n        return self.NAME\n'})
show("cross-call-self-attr", *entry(body2, root))
shutil.rmtree(root, ignore_errors=True)

# 4: a receiver bound by a FROM-import alias.
body4 = ('from pkg import mk as m2\nwith m2.Box().open() as m:\n'
         '    if a1:\n        KEY = m.ATTR\n'
         '    else:\n        KEY = m.ATTR\n' + TAIL)
root = world({"hw3.py": 'ATTR = "b"\n',
              "pkg/mk.py": 'class Box:\n    NAME = "hw3"\n'
                           '    def open(self):\n        return self.NAME\n'})
show("from-alias-receiver", *entry(body4, root))
shutil.rmtree(root, ignore_errors=True)

# --- shapes this face still leaves open, measured for the next seed ---------
# 5: a base class inherited from ANOTHER module.
root = world({"base.py": 'class Base:\n    ATTR = "b"\n',
              "cls.py": "from base import Base\n\nclass K(Base):\n    pass\n"})
show("cross-module-base", *entry("import cls\n" + arms("cls.K.ATTR")
                                 + TAIL, root))
shutil.rmtree(root, ignore_errors=True)

# 6: a method returning a class attribute of a BASE class through self.
root = world({"hw3.py": 'ATTR = "b"\n',
              "mk.py": 'class Base:\n    NAME = "hw3"\n\nclass Box(Base):\n'
                       '    def open(self):\n        return self.NAME\n'})
show("self-base-attr", *entry(body2, root))
shutil.rmtree(root, ignore_errors=True)

# 7: a receiver bound by a class attribute that is a module name.
root = world({"hw3.py": 'ATTR = "b"\n',
              "mk.py": 'class Box:\n    NAME = "hw3"\n'
                       '    def open(self):\n        return self.NAME\n',
              "reg.py": 'from mk import Box\nREG = Box().open()\n'})
body7 = ('import reg\nwith reg.REG as m:\n'
         '    if a1:\n        KEY = m.ATTR\n'
         '    else:\n        KEY = m.ATTR\n' + TAIL)
show("class-attr-module", *entry(body7, root))
shutil.rmtree(root, ignore_errors=True)

# 8: a class attribute that is an alias of another class constant.
root = world({"cls.py": 'class Base:\n    ATTR = "b"\n\nclass K(Base):\n'
                        '    OTHER = ATTR\n'})
show("class-alias-attr", *entry("import cls\n" + arms("cls.K.OTHER")
                                + TAIL, root))
shutil.rmtree(root, ignore_errors=True)