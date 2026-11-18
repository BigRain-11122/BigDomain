"""Suite for the static panel-log namespace gate that bounds R2955's hole.

Criteria AC-PAN27..AC-PAN29 were pinned in src/os/backlog.md BEFORE this file
and src/sandbox/panel_log_ns_scan.py existed (in-window pre-registration,
disclosed).

Nothing here is read off the scanner's own prose: each criterion builds a
private world on disk, runs the SHIPPED ``scan()`` over it, and requires a named
refusal - then moves the ONE thing under test (the write intent, the binding,
the file name) and requires the same world to pass, so each red is caused by
that thing and not by the fixture or the world.

Usage: python test_panel_log_ns_scan.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OWNER = os.path.join(HERE, "panel.py")
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
    full = os.path.join(root, rel)
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
    # real-bytes red control: the owner's own source, under another name
    with open(OWNER, "r", encoding="utf-8", errors="replace") as handle:
        owner_text = handle.read()
    root = fresh_world("pan29")
    write(root, "panel.py", owner_text)
    same = panel_log_ns_scan.scan(root=root)
    if not same["ok"]:
        bad.append("owner-bytes-refused")
    write(root, "other.py", owner_text)
    moved = panel_log_ns_scan.scan(root=root)
    row = named(moved).get("other.py")
    if moved["ok"]:
        bad.append("renamed-owner-passed")
    elif row is None:
        bad.append("renamed-owner-not-named")
    elif row["code"] != panel_log_ns_scan.FOREIGN_NAME:
        bad.append("renamed-owner-code=" + str(row["code"]))
    report("AC-PAN29", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
