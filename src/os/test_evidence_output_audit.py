"""The evidence-output audit as a battery suite (AC-EOA1..AC-EOA6).

Runs the audit entirely against temp fixtures, so every verdict is proven by
the files it was given rather than by the live pile it happens to read.
Criteria AC-EOA1..AC-EOA6 were pinned in state/queue/tech.md as the R2296 seed
row BEFORE src/os/evidence_output_audit.py existed.

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
MODULE = os.path.join(BASE, "evidence_output_audit.py")
RUNNER = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")

sys.path.insert(0, BASE)
import evidence_output_audit as eoa  # noqa: E402
import evidence_output_map as eom  # noqa: E402

PASS = 0
FAIL = 0

WRITER = '''"""A legacy copy that writes one named evidence file."""

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
    target = os.path.join(ROOT, "qa", "%s")
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
    world = tempfile.mkdtemp(prefix="eoa-")
    clean_world = tempfile.mkdtemp(prefix="eoa-clean-")
    try:
        qa_dir = os.path.join(world, "qa")
        os.mkdir(qa_dir)
        clean_qa = os.path.join(clean_world, "qa")
        os.mkdir(clean_qa)

        write(os.path.join(world, "evidence_R9001.py"),
              WRITER % "present-R9001.log")
        write(os.path.join(world, "evidence_R9002.py"),
              WRITER % "gone-R9002.log")
        write(os.path.join(world, "evidence_R9003.py"),
              TEMPLATE % "family-%s-R9003.log")
        write(os.path.join(world, "evidence_R9004.py"), EMPTY)
        write(os.path.join(world, "evidence_R9005.py"),
              TEMPLATE % "never-%s-R9005.log")
        write(os.path.join(world, "evidence_R9006.py"),
              WRITER % "shared-R9006.log")
        write(os.path.join(qa_dir, "present-R9001.log"), "x")
        write(os.path.join(qa_dir, "family-01-R9003.log"), "x")
        write(os.path.join(qa_dir, "family-02-R9003.log"), "x")

        write(os.path.join(clean_world, "evidence_R9007.py"),
              WRITER % "present-R9007.log")
        write(os.path.join(clean_qa, "present-R9007.log"), "x")

        report = eoa.audit(world, ".", "qa", "evidence_R*.py")
        rows = dict((row["script"].split("evidence_")[-1], row)
                    for row in report["rows"])

        # AC-EOA1 - the declaration law is the MAP's, not a second copy, and a
        # patched map flows straight through this audit.
        original = eom.declarations
        injected = {}
        try:
            def patched(text):
                return [{"path": "qa/injected-R9999.log", "line": 42}]
            eom.declarations = patched
            perturbed = eoa.audit(clean_world, ".", "qa", "evidence_R*.py")
            injected = dict((item["path"], item) for item in
                            perturbed["absent"])
        finally:
            eom.declarations = original
        with open(MODULE, "rb") as handle:
            source = handle.read().decode("ascii", "replace")
        check("AC-EOA1", "evidence_output_map as eom" in source
              and "eom.declarations" not in source
              and "eom.build" in source
              and "qa/injected-R9999.log" in injected
              and injected["qa/injected-R9999.log"]["line"] == 42,
              "patched_absent=%s imports_map=%r"
              % (",".join(sorted(injected)),
                 "evidence_output_map as eom" in source))

        # AC-EOA2 - every declared literal carries EXISTS or ABSENT and the
        # counts reconcile with the declared total.
        literal_verdicts = []
        for row in report["rows"]:
            for item in row["declarations"]:
                if eom.is_literal(item["path"]):
                    literal_verdicts.append(item["verdict"])
        absolute = os.path.join(qa_dir, "present-R9001.log")
        position = os.path.join(qa_dir, "gone-R9002.log")
        check("AC-EOA2", set(literal_verdicts) <= {"EXISTS", "ABSENT"}
              and report["absent_total"] == 2
              and [item["path"] for item in report["absent"]]
              == ["qa/gone-R9002.log", "qa/shared-R9006.log"]
              and report["exists_total"]
              == sum(row["exists"] for row in report["rows"])
              and report["exists_total"] + report["absent_total"]
              == len(literal_verdicts)
              and os.path.isfile(absolute) and not os.path.isfile(position),
              "literals=%d exists=%d absent=%d"
              % (len(literal_verdicts), report["exists_total"],
                 report["absent_total"]))

        # AC-EOA3 - a template reads FAMILY-HIT with its match count or
        # FAMILY-NONE with zero, never rounded to EXISTS.
        families = dict((item["path"], item) for item in report["families"])
        check("AC-EOA3", families.get("qa/family-%s-R9003.log", {})
              .get("verdict") == "FAMILY-HIT"
              and families["qa/family-%s-R9003.log"]["matches"] == 2
              and families.get("qa/never-%s-R9005.log", {})
              .get("verdict") == "FAMILY-NONE"
              and families["qa/never-%s-R9005.log"]["matches"] == 0
              and report["family_hit_total"] == 1
              and report["family_none_total"] == 1,
              "hit=%d none=%d"
              % (report["family_hit_total"], report["family_none_total"]))

        # AC-EOA4 - a script with no resolvable declaration reads STALE and is
        # listed, while a clean pile reads CLEAN.
        stale = dict((item["script"].split("evidence_")[-1], item["reason"])
                     for item in report["stale"])
        clean_report = eoa.audit(clean_world, ".", "qa", "evidence_R*.py")
        check("AC-EOA4", stale.get("R9004.py") == "NO-DECLARATION"
              and stale.get("R9002.py") == "ALL-UNRESOLVED"
              and stale.get("R9005.py") == "ALL-UNRESOLVED"
              and stale.get("R9006.py") == "ALL-UNRESOLVED"
              and report["stale_total"] == 4
              and clean_report["verdict"] == "CLEAN"
              and clean_report["stale_total"] == 0
              and clean_report["absent_total"] == 0
              and rows["R9001.py"]["status"] == "OK",
              "stale=%s clean=%s"
              % (",".join(sorted(stale)), clean_report["verdict"]))

        # AC-EOA5 - read-only: pile and evidence listing digest identically
        # before and after; CLI codes; byte-stable --json.
        before = [digests(os.path.join(world, name))
                  for name in sorted(os.listdir(world)) if name.endswith(".py")]
        qa_before = [(name, digests(os.path.join(qa_dir, name)))
                     for name in sorted(os.listdir(qa_dir))]
        again = eoa.audit(world, ".", "qa", "evidence_R*.py")
        after = [digests(os.path.join(world, name))
                 for name in sorted(os.listdir(world)) if name.endswith(".py")]
        qa_after = [(name, digests(os.path.join(qa_dir, name)))
                    for name in sorted(os.listdir(qa_dir))]
        clean_cli = subprocess.run(
            [sys.executable, MODULE, "--dir", clean_world, "--qa", clean_qa],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dirty_cli = subprocess.run(
            [sys.executable, MODULE, "--dir", world, "--qa", qa_dir],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        missing_cli = subprocess.run(
            [sys.executable, MODULE, "--dir", os.path.join(world, "nope"),
             "--qa", qa_dir], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        noqa_cli = subprocess.run(
            [sys.executable, MODULE, "--dir", world, "--qa",
             os.path.join(world, "noqa")],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        badflags = subprocess.run([sys.executable, MODULE, "--bogus"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        first = subprocess.run(
            [sys.executable, MODULE, "--dir", world, "--qa", qa_dir, "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        second = subprocess.run(
            [sys.executable, MODULE, "--dir", world, "--qa", qa_dir, "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        body = first.stdout.decode("utf-8", "replace")
        clean_text = clean_cli.stdout.decode("utf-8", "replace")
        check("AC-EOA5", before == after and qa_before == qa_after
              and clean_cli.returncode == 0
              and "verdict=CLEAN" in clean_text
              and dirty_cli.returncode == 2
              and missing_cli.returncode == 3
              and noqa_cli.returncode == 3
              and badflags.returncode == 5
              and first.stdout == second.stdout
              and body.startswith("{\"dir\":")
              and "\"absent_total\"" in body
              and "\"stale_total\"" in body
              and again["verdict"] == report["verdict"],
              "rc=%d/%d/%d/%d/%d stable=%r"
              % (clean_cli.returncode, dirty_cli.returncode,
                 missing_cli.returncode, noqa_cli.returncode,
                 badflags.returncode, first.stdout == second.stdout))

        # AC-EOA6 - purity plus its own reconcile label.
        with open(MODULE, "rb") as handle:
            raw = handle.read()
        ascii_ok = all(byte < 128 for byte in raw)
        text = raw.decode("ascii")
        imports = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("import "):
                imports.append(line[7:].split()[0].split(".")[0])
            elif line.startswith("from "):
                imports.append(line[5:].split()[0].split(".")[0])
        forbidden = {"socket", "urllib", "http", "requests", "ftplib",
                     "time", "datetime", "glob"}
        with open(RUNNER, "rb") as handle:
            runner_text = handle.read().decode("utf-8", "replace")
        wired = ('"os-evidence-output-audit"' in runner_text
                 and "test_evidence_output_audit.py" in runner_text)
        check("AC-EOA6", ascii_ok and not (set(imports) & forbidden)
              and "time." not in text and wired,
              "ascii=%r imports=%s wired=%r"
              % (ascii_ok, ",".join(imports), wired))
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(clean_world, ignore_errors=True)

    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAIL == 0 else "FAIL", PASS, PASS + FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())