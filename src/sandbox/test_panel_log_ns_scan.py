"""Suite for the static panel-log namespace gate that bounds R2955's hole.

Criteria AC-PAN27..AC-PAN29 were pinned in src/os/backlog.md BEFORE this file
and src/sandbox/panel_log_ns_scan.py existed (in-window pre-registration,
disclosed); AC-PAN35..AC-PAN36 were pinned the same way before R2959's change,
which moved the exemption key off the basename and onto the path relative to
the scanned root.

Nothing here is read off the scanner's own prose: each criterion builds a
private world on disk, runs the SHIPPED ``scan()`` over it, and requires a named
refusal - then moves the ONE thing under test (the write intent, the binding,
the file name, the file's PATH) and requires the same world to pass, so each
red is caused by that thing and not by the fixture or the world.

Usage: python test_panel_log_ns_scan.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OWNER = os.path.join(HERE, "panel.py")
JUDGE = os.path.join(HERE, "panel_log_ns_scan.py")
WORLD = os.path.join(REPO, "logs", "panel-log-ns-suite")

sys.path.insert(0, HERE)
import panel_log_ns_scan  # noqa: E402

RESULTS = []

WRITE_FIXTURE = (
    "import os\n"
    "\n"
    "def leak(root):\n"
    "    path = os.path.join(root, \"bigdomain-panel-child-x.txt\")\n"
    "    with open(path, \"w\") as handle:\n"
    "        handle.write(\"x\")\n"
)

READ_FIXTURE = (
    "import os\n"
    "\n"
    "def look(root):\n"
    "    path = os.path.join(root, \"bigdomain-panel-child-x.txt\")\n"
    "    with open(path, \"r\") as handle:\n"
    "        return handle.read()\n"
)

MODE_FIXTURE = (
    "import os\n"
    "\n"
    "def leak(root, mode):\n"
    "    path = os.path.join(root, \"bigdomain-panel-child-x.txt\")\n"
    "    with open(path, mode) as handle:\n"
    "        handle.write(\"x\")\n"
)


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def fresh_world(name):
    path = os.path.join(WORLD, name)
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)
    return path


def write(root, rel, text):
    full = os.path.join(root, rel.replace("/", os.sep))
    parent = os.path.dirname(full)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(full, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return full


def named(verdict):
    return dict((row["path"], row) for row in verdict["refused"])


def main():
    # ---- AC-PAN27: only the write intent reddens this world ---------------
    bad = []
    root = fresh_world("pan27")
    write(root, "fixture.py", WRITE_FIXTURE)
    loud = panel_log_ns_scan.scan(root=root)
    if loud["ok"]:
        bad.append("write-open-passed")
    row = named(loud).get("fixture.py")
    if row is None:
        bad.append("fixture-not-named")
    else:
        if row["code"] != panel_log_ns_scan.FOREIGN_WRITE:
            bad.append("wrong-code=" + str(row["code"]))
        if row["line"] != 5:
            bad.append("wrong-line=" + str(row["line"]))
        if row["kind"] != panel_log_ns_scan.KIND_WRITE:
            bad.append("wrong-kind=" + row["kind"])
    write(root, "fixture.py", READ_FIXTURE)
    quiet = panel_log_ns_scan.scan(root=root)
    if not quiet["ok"]:
        bad.append("read-open-refused=%s"
                   % ",".join(r["path"] for r in quiet["refused"]))
    if quiet["sites"]:
        bad.append("read-open-counted-as-site=%d" % quiet["sites"])
    write(root, "fixture.py", MODE_FIXTURE)
    unknown = panel_log_ns_scan.scan(root=root)
    if unknown["ok"]:
        bad.append("non-literal-mode-passed")
    report("AC-PAN27", bool(bad), ",".join(bad))

    # ---- AC-PAN28: the binding is the licence, so it is refused too ------
    bad = []
    root = fresh_world("pan28")
    write(root, "steal.py", "LOG_STEM = \"bigdomain-panel-child-\"\n")
    loud = panel_log_ns_scan.scan(root=root)
    row = named(loud).get("steal.py")
    if row is None:
        bad.append("binding-not-named")
    else:
        if row["code"] != panel_log_ns_scan.FOREIGN_NAME:
            bad.append("wrong-code=" + str(row["code"]))
        if row["kind"] != panel_log_ns_scan.KIND_NAME:
            bad.append("wrong-kind=" + row["kind"])
        if row["detail"] != "binding":
            bad.append("wrong-detail=" + row["detail"])
    write(root, "steal.py", "LOG_STEM = \"other-panel-\"\n")
    quiet = panel_log_ns_scan.scan(root=root)
    if not quiet["ok"]:
        bad.append("harmless-binding-refused")
    write(root, "borrow.py", "import panel\n\nPATH = panel.LOG_STEM\n")
    borrow = panel_log_ns_scan.scan(root=root)
    row = named(borrow).get("borrow.py")
    if borrow["ok"]:
        bad.append("borrow-passed")
    elif row is None:
        bad.append("borrow-not-named")
    elif row["code"] != panel_log_ns_scan.FOREIGN_NAME:
        bad.append("borrow-wrong-code=" + str(row["code"]))
    report("AC-PAN28", bool(bad), ",".join(bad))

    # ---- AC-PAN29: shipped tree clean, exemptions measured --------------
    bad = []
    shipped = panel_log_ns_scan.scan()
    if not shipped["ok"]:
        bad.append("shipped-tree-refused=%s"
                   % ",".join(r["path"] for r in shipped["refused"]))
    if shipped["modules"] < 100:
        bad.append("shipped-scan-too-small=%d" % shipped["modules"])
    whys = shipped["by_why"]
    if whys.get("owner", 0) < 1:
        bad.append("owner-not-counted")
    if whys.get("fixture", 0) < 1:
        bad.append("fixture-not-counted")
    if whys.get("judge", 0) != 1:
        bad.append("judge-count=%d" % whys.get("judge", 0))
    paths = set(row["path"].replace(os.sep, "/") for row in shipped["exempt"])
    if not any(p.endswith("sandbox/panel.py") for p in paths):
        bad.append("owner-path-missing")
    if not any(os.path.basename(p).startswith("test_") for p in paths):
        bad.append("fixture-path-missing")
    # real-bytes red control: the owner's own source, at the owner's own PATH
    with open(OWNER, "r", encoding="utf-8", errors="replace") as handle:
        owner_text = handle.read()
    root = fresh_world("pan29")
    write(root, "sandbox/panel.py", owner_text)
    same = panel_log_ns_scan.scan(root=root)
    if not same["ok"]:
        bad.append("owner-bytes-refused")
    write(root, "sandbox/other.py", owner_text)
    moved = panel_log_ns_scan.scan(root=root)
    row = named(moved).get("sandbox/other.py")
    if moved["ok"]:
        bad.append("renamed-owner-passed")
    elif row is None:
        bad.append("renamed-owner-not-named")
    elif row["code"] not in (panel_log_ns_scan.FOREIGN_NAME,
                             panel_log_ns_scan.FOREIGN_WRITE):
        bad.append("renamed-owner-code=" + str(row["code"]))
    report("AC-PAN29", bool(bad), ",".join(bad))

    # ---- AC-PAN35: the exemption is the PATH, not the basename ------------
    bad = []
    root = fresh_world("pan35a")
    write(root, "sandbox/panel.py", owner_text)
    owner_world = panel_log_ns_scan.scan(root=root)
    if not owner_world["ok"]:
        bad.append("owner-path-refused=%s"
                   % ",".join(r["path"] for r in owner_world["refused"]))
    if owner_world["by_why"].get("owner", 0) != 1:
        bad.append("owner-not-exempt=%d" % owner_world["by_why"].get("owner", 0))
    # the SAME bytes at the root of the tree: a same-name module elsewhere
    write(root, "panel.py", owner_text)
    shallow = panel_log_ns_scan.scan(root=root)
    row = named(shallow).get("panel.py")
    if shallow["ok"]:
        bad.append("root-panel-passed")
    elif row is None:
        bad.append("root-panel-not-named")
    elif row["code"] not in (panel_log_ns_scan.FOREIGN_NAME,
                             panel_log_ns_scan.FOREIGN_WRITE):
        bad.append("root-panel-code=" + str(row["code"]))
    # and one level deeper: pkg/sandbox/panel.py is not sandbox/panel.py
    write(root, "pkg/sandbox/panel.py", owner_text)
    deep = panel_log_ns_scan.scan(root=root)
    if "pkg/sandbox/panel.py" not in named(deep):
        bad.append("nested-owner-path-not-named")
    # fixtures: the same stem-carrying module inside and outside sandbox/
    root = fresh_world("pan35b")
    binding = "LOG_STEM = \"bigdomain-panel-child-\"\n"
    write(root, "sandbox/test_world.py", binding)
    inside = panel_log_ns_scan.scan(root=root)
    if not inside["ok"]:
        bad.append("sandbox-fixture-refused=%s"
                   % ",".join(r["path"] for r in inside["refused"]))
    if inside["by_why"].get("fixture", 0) != 1:
        bad.append("sandbox-fixture-not-counted=%d"
                   % inside["by_why"].get("fixture", 0))
    write(root, "test_world.py", binding)
    outside = panel_log_ns_scan.scan(root=root)
    row = named(outside).get("test_world.py")
    if outside["ok"]:
        bad.append("root-test-module-passed")
    elif row is None or row["code"] != panel_log_ns_scan.FOREIGN_NAME:
        bad.append("root-test-module-unnamed")
    write(root, "sandbox/sub/test_world.py", binding)
    buried = panel_log_ns_scan.scan(root=root)
    if "sandbox/sub/test_world.py" not in named(buried):
        bad.append("buried-test-module-not-named")
    report("AC-PAN35", bool(bad), ",".join(bad))

    # ---- AC-PAN36: the judge is a path too, and the tree stays portable ---
    bad = []
    with open(JUDGE, "r", encoding="utf-8", errors="replace") as handle:
        judge_text = handle.read()
    root = fresh_world("pan36")
    write(root, "sandbox/panel_log_ns_scan.py", judge_text)
    judge_world = panel_log_ns_scan.scan(root=root)
    if not judge_world["ok"]:
        bad.append("judge-path-refused=%s"
                   % ",".join(r["path"] for r in judge_world["refused"]))
    if judge_world["by_why"].get("judge", 0) != 1:
        bad.append("judge-not-exempt=%d" % judge_world["by_why"].get("judge", 0))
    exempt_paths = [row["path"].replace(os.sep, "/")
                    for row in judge_world["exempt"]]
    if exempt_paths != ["sandbox/panel_log_ns_scan.py"]:
        bad.append("judge-paths=%s" % ",".join(exempt_paths))
    if judge_world["root"] != root:
        bad.append("root-not-reported")
    write(root, "panel_log_ns_scan.py", judge_text)
    write(root, "sandbox/other.py", judge_text)
    moved = panel_log_ns_scan.scan(root=root)
    for rel in ("panel_log_ns_scan.py", "sandbox/other.py"):
        row = named(moved).get(rel)
        if moved["ok"]:
            bad.append("copied-judge-passed")
            break
        if row is None:
            bad.append("copied-judge-not-named=" + rel)
    shipped = panel_log_ns_scan.scan()
    if not shipped["ok"]:
        bad.append("shipped-tree-refused")
    whys = shipped["by_why"]
    if whys.get("owner", 0) != 1 or whys.get("judge", 0) != 1:
        bad.append("shipped-owner-judge=%s" % whys)
    if whys.get("fixture", 0) < 1:
        bad.append("shipped-fixtures=%s" % whys)
    if len(shipped["exempt"]) != sum(whys.values()):
        bad.append("exempt-count-mismatch=%d/%d"
                   % (len(shipped["exempt"]), sum(whys.values())))
    stray = [row["path"] for row in shipped["exempt"]
             if not row["path"].replace(os.sep, "/").startswith("sandbox/")]
    if stray:
        bad.append("exempt-outside-sandbox=%s" % ",".join(stray))
    report("AC-PAN36", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
