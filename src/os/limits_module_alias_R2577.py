"""R2577 measured limits for the NEXT tech seed.

Three shapes this face does NOT read, measured on private worlds where the
honest answer is the literal `b`:

  (1) a module-level alias chain whose FINAL link is an ATTRIBUTE naming a
      module (`BASE = consts.HW` then `REG = BASE`);
  (2) a module-level function returning a NAME bound to a class attribute
      (`def make(): return REG2` with `REG2 = Box.NAME`);
  (3) a with-as context that is a CALL on an alias chain name
      (`with mk.REG() as m`).

One-off; deleted before the commit, its reading lands in qa/ only.
Exit 0 when every shape reads exactly the refused answer this file predicts.
"""

import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_chain_scope as MA  # noqa

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
TAIL = "for name in hw.NAMES:\n    pass\n"
WITH_ATTR = ("with mk.REG as m:\n    if a1:\n        KEY = m.ATTR\n"
             "    else:\n        KEY = m.ATTR\n")
WITH_CALL = ("with mk.REG() as m:\n    if a1:\n        KEY = m.ATTR\n"
             "    else:\n        KEY = m.ATTR\n")


def world(files):
    root = tempfile.mkdtemp(prefix="pnpcs-lim-")
    for name, body in files.items():
        path = os.path.join(root, name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def reading(text, root):
    rows = MA.module_alias_report(text, root, None)["loops"]
    loop = rows[-1]
    return MA.module_alias_entry("KEY", text, loop["scope"], loop["line"],
                                 root=root, src_path=None)


def measure(files, text):
    root = world(files)
    try:
        return reading(text, root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    fails = 0

    got = measure({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                   "mk.py": "import consts\nBASE = consts.HW\nREG = BASE\n"},
                  "import mk\n" + WITH_ATTR + TAIL)
    ok = (got.get("ma_state") != MA.STATE_OK
          and got.get("reason") == "attr-with-as:m.ATTR")
    print("%s limit1 attribute-final chain refused=%s/%s"
          % ("PASS" if ok else "FAIL", got.get("ma_state"),
             got.get("reason")))
    fails += 0 if ok else 1

    got = measure({"hw.py": HW,
                   "mk.py": ('class Box:\n    NAME = "hw"\n'
                             'REG2 = Box.NAME\n'
                             'def make():\n    return REG2\n'
                             'REG = make()\n')},
                  "import mk\n" + WITH_ATTR + TAIL)
    ok = (got.get("ma_state") != MA.STATE_OK
          and got.get("reason") == "attr-with-as:m.ATTR")
    print("%s limit2 function returning a NAME refused=%s/%s"
          % ("PASS" if ok else "FAIL", got.get("ma_state"),
             got.get("reason")))
    fails += 0 if ok else 1

    got = measure({"hw.py": HW,
                   "mk.py": ('class Box:\n    NAME = "hw"\n'
                             '    def open(self):\n        return self.NAME\n'
                             'FIRST = Box().open()\nREG = FIRST\n')},
                  "import mk\n" + WITH_CALL + TAIL)
    ok = (got.get("ma_state") != MA.STATE_OK
          and got.get("reason") == "attr-cross-call:m.ATTR")
    print("%s limit3 call-context on an alias chain refused=%s/%s"
          % ("PASS" if ok else "FAIL", got.get("ma_state"),
             got.get("reason")))
    fails += 0 if ok else 1

    print("LIMITS fails=%d" % fails)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())