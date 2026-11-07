"""Wire one registry row for the annotated-constant face (R2525)."""

import io
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "sandbox", "reconcile_all.py")

ANCHOR = ('    ("os-probe-seam-local-constant-scope",\n'
          '     os.path.join("..", "os",\n'
          '                  "test_probe_seam_local_constant_scope.py"), 6),\n')

ADD = ('    # R2525 - a probe that declares its module name in an ANNOTATED\n'
       '    # assignment, a walrus binding or a for-loop target of one str\n'
       '    # literal reads COVERED instead of OUT-OF-SCOPE, and one more\n'
       '    # attribute hop on a module-level constant tree is followed when\n'
       '    # the probe own imports name the module; a name computed at run\n'
       '    # time is named and never evaluated (591 -> 592 suites, 4522 ->\n'
       '    # 4528 criteria).\n'
       '    ("os-probe-seam-annotated-constant-scope",\n'
       '     os.path.join("..", "os",\n'
       '                  "test_probe_seam_annotated_constant_scope.py"), 6),\n')


def main():
    with io.open(PATH, encoding="utf-8", newline="") as handle:
        text = handle.read()
    target = os.path.abspath(PATH)
    if ADD in text:
        print("ALREADY-WIRED %s" % target)
        return 0
    if ANCHOR not in text:
        print("FAIL anchor missing in %s" % target)
        return 2
    text = text.replace(ANCHOR, ANCHOR + ADD, 1)
    with io.open(PATH, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("WIRED %s bytes=%d" % (target, len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())