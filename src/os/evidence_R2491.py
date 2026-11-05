"""evidence_R2491 - the live leg for the corpus-scope face.

Writes ONE utf-8 LF evidence file: the real-tree reading, then the exact
defect the R2440 seed measured (a publisher read from a SUBDIRECTORY while the
package sits at the tree top), then the same reading with the caller-declared
extra name merged, then a UTF-8-LF dialect proof of its own bytes.
"""

import io
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODULE = os.path.join("src", "os", "relative_module_corpus_scope.py")
OUT = os.path.join(ROOT, "qa", "relative-module-corpus-scope-live-R2491.log")

HEAD = ('import queue_floor_export_face as QFE\n'
        'import os\n\n'
        'EXPORT = os.path.join("docs", "status-export.json")\n\n\n'
        'def publish(data):\n'
        '    QFE.apply(data, ".")\n')
BODY = '    return publish(".", EXPORT, text="{}")\n'


def write(path, text):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def run(argv):
    done = subprocess.run([sys.executable, MODULE] + argv, cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (done.returncode, done.stdout.decode("utf-8", "replace"),
            done.stderr.decode("utf-8", "replace"))


def main():
    lines = []

    code, out, err = run(["--check", "--root", os.path.join("src", "os"),
                          "--package", "src.os"])
    lines.append("LEG 1 real tree root=src/os package=src.os rc=%d" % code)
    lines.append("  " + out.strip())
    if err.strip():
        lines.append("  stderr=" + err.strip())

    # The seed's own defect: the publisher lives in scripts/ while the package
    # mypkg/ sits at the tree top, and the reading is asked with root=scripts.
    world = tempfile.mkdtemp(prefix="rmsc-live-")
    write(os.path.join(world, "mypkg", "__init__.py"), "")
    write(os.path.join(world, "mypkg", "wire.py"), "")
    write(os.path.join(world, "scripts", "rel_pub.py"),
          "from .wire import publish\n" + HEAD + BODY)
    narrow_root = os.path.join(world, "scripts")

    code_before, out_before, _ = run(["--check", "--root", narrow_root,
                                      "--package", "mypkg",
                                      "--wire", "mypkg.wire"])
    lines.append("")
    lines.append("LEG 2 scope limit root=%s package=mypkg rc=%d"
                 % (narrow_root, code_before))
    for row in out_before.strip().splitlines():
        lines.append("  " + row)

    code_after, out_after, _ = run(["--check", "--root", narrow_root,
                                    "--package", "mypkg",
                                    "--wire", "mypkg.wire",
                                    "--extra", "mypkg.wire"])
    lines.append("")
    lines.append("LEG 3 same root + declared extra rc=%d" % code_after)
    for row in out_after.strip().splitlines():
        lines.append("  " + row)

    code_wide, out_wide, _ = run(["--check", "--root", world,
                                  "--package", "mypkg",
                                  "--wire", "mypkg.wire"])
    lines.append("")
    lines.append("LEG 4 whole tree root (package is a sibling of scripts/) "
                 "rc=%d" % code_wide)
    for row in out_wide.strip().splitlines():
        lines.append("  " + row)

    body = "\n".join(lines) + "\n"
    payload = body.encode("utf-8")
    with io.open(OUT, "wb") as handle:
        handle.write(payload)
    back = io.open(OUT, "rb").read()
    print("LIVE rel-module-corpus-scope-R2491 bytes=%d crlf=%d lone_cr=%d "
          "bom=%s leg2_rc=%d leg3_rc=%d leg4_rc=%d"
          % (len(back), back.count(b"\r\n"),
             back.count(b"\r") - back.count(b"\r\n"),
             back[:3] == b"\xef\xbb\xbf", code_before, code_after, code_wide))


if __name__ == "__main__":
    main()