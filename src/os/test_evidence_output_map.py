"""The evidence-output map as a battery suite (AC-EOM1..AC-EOM6).

Runs the reader entirely against temp fixtures, so every verdict is proven by
the text it was given rather than by the live pile it happens to read. Criteria
AC-EOM1..AC-EOM6 were pinned in state/queue/tech.md as the R2282 seed row
BEFORE src/os/evidence_output_map.py existed.

One PASS/FAIL line per criterion, with the sub-assertions carried in the
detail so a failure still names what broke. ASCII, stdlib only, zero network,
no writes outside the temp world.
"""

import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
MODULE = os.path.join(BASE, "evidence_output_map.py")
RUNNER = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")

sys.path.insert(0, BASE)
import evidence_output_map as eom  # noqa: E402

PASS = 0
FAIL = 0

WRITER = '''"""A legacy copy that writes one evidence file."""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))


def main():
    target = os.path.join(ROOT, "qa", "%s")
    with io.open(target, "wb") as handle:
        handle.write(b"x")
    return 0
'''

TEMPLATE = '''"""A legacy copy that writes a per-round family."""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))


def main():
    target = os.path.join(ROOT, "qa", "family-%%s-R%%s.log")
    with io.open(target, "wb") as handle:
        handle.write(b"x")
    return 0
'''

EMPTY = '''"""Nothing but a docstring."""

VALUE = 1
'''


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print("PASS %s %s" % (name, detail))
    else:
        FAIL += 1
        print("FAIL %s %s" % (name, detail))


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


def digests(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    return len(raw), hashlib.sha256(raw).hexdigest()[:16]


def main():
    world = tempfile.mkdtemp(prefix="eom-")
    clean_world = tempfile.mkdtemp(prefix="eom-clean-")
    try:
        write(os.path.join(world, "evidence_R9001.py"),
              WRITER % "shared-R9001.log")
        write(os.path.join(world, "evidence_R9002.py"),
              WRITER % "shared-R9001.log")
        write(os.path.join(world, "evidence_R9003.py"), TEMPLATE)
        write(os.path.join(world, "evidence_R9004.py"), EMPTY)
        citations = write(os.path.join(world, "citations.md"),
                          "round cites qa/shared-R9001.log and "
                          "qa/cited-R9005.log\n")
        clean = write(os.path.join(clean_world, "evidence_R9004.py"), EMPTY)

        report = eom.build(world, ".", "evidence_R*.py", citations)
        by_script = dict((row["script"], row) for row in report["rows"])

        # AC-EOM1 - one row per file, a row with no declaration reads NONE.
        none_row = [row for row in report["rows"]
                    if row["script"].endswith("evidence_R9004.py")][0]
        check("AC-EOM1", report["scripts"] == 4
              and len(report["rows"]) == 4
              and len(set(row["script"] for row in report["rows"])) == 4
              and none_row["verdict"] == "NONE"
              and none_row["count"] == 0
              and len(none_row["declared"]) == 0,
              "scripts=%d rows=%d none_verdict=%s"
              % (report["scripts"], len(report["rows"]),
                 none_row["verdict"]))

        # AC-EOM2 - a shared path is a collision naming both scripts and the
        # line each declaration sits on; the counts reconcile.
        collision = report["collisions"][0] if report["collisions"] else None
        names = [owner["script"] for owner in collision["scripts"]] \
            if collision else []
        lines = [owner["line"] for owner in collision["scripts"]] \
            if collision else []
        template_row = [row for row in report["rows"]
                        if row["script"].endswith("evidence_R9003.py")][0]
        sum_rows = sum(row["count"] for row in report["rows"])
        check("AC-EOM2", collision is not None
              and collision["path"] == "qa/shared-R9001.log"
              and len(names) == 2 and all(line > 0 for line in lines)
              and report["collision_total"] == 1
              and report["declared_total"] == sum_rows
              and template_row["count"] == 1,
              "path=%s scripts=%s lines=%s declared_total=%d sum_rows=%d "
              "template=%d"
              % (collision["path"] if collision else "-", ",".join(names),
                 ",".join(str(line) for line in lines),
                 report["declared_total"], sum_rows, template_row["count"]))

        # AC-EOM3 - the declared-but-absent set names cited outputs no script
        # declares, and an empty citation set reads CLEAN instead of failing.
        clean_report = eom.build(clean_world, ".", "evidence_R*.py", None)
        absent_paths = [item["path"] for item in report["absent"]]
        check("AC-EOM3", absent_paths == ["qa/cited-R9005.log"]
              and report["absent_total"] == 1
              and clean_report["verdict"] == "CLEAN"
              and clean_report["absent_total"] == 0
              and clean_report["collision_total"] == 0,
              "absent=%s clean_verdict=%s"
              % (",".join(absent_paths), clean_report["verdict"]))

        # AC-EOM4 - read-only: pile bytes and the directory listing unchanged.
        before = [digests(os.path.join(world, name))
                  for name in sorted(os.listdir(world)) if name.endswith(".py")]
        listing = sorted(os.listdir(world))
        again = eom.build(world, ".", "evidence_R*.py", citations)
        after = [digests(os.path.join(world, name))
                 for name in sorted(os.listdir(world)) if name.endswith(".py")]
        check("AC-EOM4", before == after and listing == sorted(os.listdir(world))
              and again["declared_total"] == report["declared_total"]
              and eom.declarations(EMPTY) == [],
              "files=%d unchanged=%r"
              % (len(before), before == after))

        # AC-EOM5 - CLI codes plus a byte-stable --json over the pinned keys.
        clean_cli = subprocess.run(
            [sys.executable, MODULE, "--dir", clean_world],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dirty_cli = subprocess.run(
            [sys.executable, MODULE, "--dir", world, "--citations", citations],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        missing_cli = subprocess.run(
            [sys.executable, MODULE, "--dir", os.path.join(world, "nope")],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        badflags = subprocess.run([sys.executable, MODULE, "--bogus"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        first = subprocess.run(
            [sys.executable, MODULE, "--dir", world, "--citations", citations,
             "--json"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        second = subprocess.run(
            [sys.executable, MODULE, "--dir", world, "--citations", citations,
             "--json"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        body = first.stdout.decode("utf-8", "replace")
        clean_text = clean_cli.stdout.decode("utf-8", "replace")
        check("AC-EOM5", clean_cli.returncode == 0
              and "verdict=CLEAN" in clean_text
              and dirty_cli.returncode == 2
              and missing_cli.returncode == 3
              and badflags.returncode == 5
              and first.stdout == second.stdout
              and body.startswith("{\"dir\":")
              and "\"collision_total\"" in body
              and "\"absent_total\"" in body,
              "rc=%d/%d/%d/%d json_stable=%r"
              % (clean_cli.returncode, dirty_cli.returncode,
                 missing_cli.returncode, badflags.returncode,
                 first.stdout == second.stdout))

        # AC-EOM6 - purity plus its own reconcile label.
        with open(MODULE, "rb") as handle:
            raw = handle.read()
        ascii_ok = all(byte < 128 for byte in raw)
        imports = []
        for line in raw.decode("ascii").splitlines():
            line = line.strip()
            if line.startswith("import "):
                imports.append(line[7:].split()[0].split(".")[0])
            elif line.startswith("from "):
                imports.append(line[5:].split()[0].split(".")[0])
        forbidden = {"socket", "urllib", "http", "requests", "ftplib"}
        with open(RUNNER, "rb") as handle:
            runner_text = handle.read().decode("utf-8", "replace")
        wired = ('"os-evidence-output-map"' in runner_text
                 and "test_evidence_output_map.py" in runner_text)
        check("AC-EOM6", ascii_ok and not (set(imports) & forbidden) and wired,
              "ascii=%r imports=%s wired=%r"
              % (ascii_ok, ",".join(imports), wired))
        del by_script
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(clean_world, ignore_errors=True)

    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAIL == 0 else "FAIL", PASS, PASS + FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())