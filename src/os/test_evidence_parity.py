"""The evidence-parity reader as a battery suite (AC-EVP1..AC-EVP6).

Runs the reader entirely against temp fixtures, so a verdict is proven by the
text it was given rather than by the live pile it happens to read. Criteria
AC-EVP1..AC-EVP6 were pinned in state/queue/tech.md as the R2261 seed row
BEFORE src/os/evidence_parity.py existed.

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
MODULE = os.path.join(BASE, "evidence_parity.py")
RUNNER = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")

sys.path.insert(0, BASE)
import evidence_parity as ep  # noqa: E402

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print("PASS %s %s" % (name, detail))
    else:
        FAIL += 1
        print("FAIL %s %s" % (name, detail))


FULL = '''"""A legacy copy that does the whole ritual."""

import hashlib
import subprocess
import sys

LEGS = 2
ADJACENT = ["a.py", "b.py"]


def _run(path):
    return subprocess.run([sys.executable, path])


def _write(path, text):
    data = text.replace("\\r\\n", "\\n").encode("utf-8")
    with open(path, "wb") as handle:
        handle.write(data)


def _criteria(body):
    lines = [ln for ln in body.splitlines() if ln.startswith("PASS ")]
    return hashlib.sha256("\\n".join(lines).encode("utf-8")).hexdigest()[:16]


def _live():
    return subprocess.run([sys.executable, "x.py", "--check"])


def main():
    for suffix in ("a", "b"):
        _run("suite.py")
    print("SUITE %s" % _criteria(""))
    print("LIVE gate")
    return 0
'''

PARTIAL = '''import hashlib


def _criteria(body):
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def main():
    for suffix in ("a", "b"):
        pass
    return 0
'''

EMPTY = '''"""Nothing but a docstring."""

VALUE = 1
'''


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


def digests(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    return len(raw), hashlib.sha256(raw).hexdigest()[:16]


def main():
    world = tempfile.mkdtemp(prefix="evp-")
    try:
        full = write(os.path.join(world, "full.py"), FULL)
        write(os.path.join(world, "partial.py"), PARTIAL)
        write(os.path.join(world, "empty.py"), EMPTY)

        report = ep.check(world, "full.py")

        # AC-EVP1 - the five leg names in the pinned order, every one judged.
        names = [leg["name"] for leg in report["legs"]]
        check("AC-EVP1", tuple(names) == ep.LEGS
              and len(report["legs"]) == 5
              and all(leg["verdict"] in ep.VERDICTS for leg in report["legs"]),
              "legs=%s verdicts=%s"
              % (",".join(names),
                 ",".join(leg["verdict"] for leg in report["legs"])))

        # AC-EVP2 - PRESENT needs marker AND shape; MISSING when none; else
        # DIFFERENT. Proven on three fixtures, never on the live pile.
        empty_report = ep.check(world, "empty.py")
        partial_report = ep.check(world, "partial.py")
        by_name = dict((leg["name"], leg["verdict"])
                       for leg in partial_report["legs"])
        present_ok = (report["verdict"] == "ALL-PRESENT"
                      and report["counts"]["PRESENT"] == 5)
        missing_ok = (empty_report["counts"]["MISSING"] == 5
                      and empty_report["verdict"] == "PARITY-DEBT")
        different_ok = (by_name["criteria-digest"] == "DIFFERENT"
                        and by_name["two-legs"] == "DIFFERENT"
                        and by_name["adjacent-batch"] == "MISSING")
        check("AC-EVP2", present_ok and missing_ok and different_ok,
              "present=%d missing=%d partial(digest=%s two-legs=%s "
              "adjacent=%s)"
              % (report["counts"]["PRESENT"],
                 empty_report["counts"]["MISSING"], by_name["criteria-digest"],
                 by_name["two-legs"], by_name["adjacent-batch"]))

        # AC-EVP3 - read-only: bytes identical, directory listing unchanged.
        before = digests(full)
        listing_before = sorted(os.listdir(world))
        again = ep.check(world, "full.py")
        after = digests(full)
        check("AC-EVP3", before == after
              and listing_before == sorted(os.listdir(world))
              and again["sha16"] == report["sha16"],
              "before=%d/%s after=%d/%s"
              % (before[0], before[1], after[0], after[1]))

        # AC-EVP4 - absent and unreadable fail closed, zero legs invented.
        absent = None
        try:
            ep.check(world, "nope.py")
        except ep.ParityError as exc:
            absent = (exc.code, )
        binary = os.path.join(world, "binary.py")
        with open(binary, "wb") as handle:
            handle.write(b"\xff\xfe\x00bad")
        broken = None
        try:
            ep.check(world, "binary.py")
        except ep.ParityError as exc:
            broken = exc.code
        check("AC-EVP4", absent == ("E_EVP_NO_SCRIPT",)
              and broken == "E_EVP_UNREADABLE",
              "absent=%r unreadable=%r" % (absent, broken))

        # AC-EVP5 - CLI codes plus the per-leg pile counts, unreadable kept
        # apart from the readable rows instead of aborting the pile.
        cli = subprocess.run([sys.executable, MODULE, "--script", full],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        clean_text = cli.stdout.decode("utf-8", "replace")
        dirty = subprocess.run([sys.executable, MODULE, "--script",
                                os.path.join(world, "partial.py")],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        blank = subprocess.run([sys.executable, MODULE, "--script",
                                os.path.join(world, "nope.py")],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        badflags = subprocess.run([sys.executable, MODULE, "--bogus"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        pile = ep.scan(world, ".", "*.py")
        legs = pile["leg_counts"]
        readable = pile["scripts"] - len(pile["unreadable"])
        counted = all(sum(legs[name].values()) == readable
                      for name in ep.LEGS)
        check("AC-EVP5", cli.returncode == 0
              and "verdict=ALL-PRESENT" in clean_text
              and dirty.returncode == 2 and blank.returncode == 3
              and badflags.returncode == 5
              and counted and pile["scripts"] == 4
              and len(pile["unreadable"]) == 1
              and "LEG two-legs" in ep.render_scan(pile),
              "rc=%d/%d/%d/%d pile scripts=%d readable=%d unreadable=%d "
              "all_present=%d"
              % (cli.returncode, dirty.returncode, blank.returncode,
                 badflags.returncode, pile["scripts"], readable,
                 len(pile["unreadable"]), len(pile["all_present"])))

        # AC-EVP6 - purity plus its own reconcile label.
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
        wired = ('"os-evidence-parity"' in runner_text
                 and "test_evidence_parity.py" in runner_text)
        check("AC-EVP6", ascii_ok and not (set(imports) & forbidden) and wired,
              "ascii=%r imports=%s wired=%r"
              % (ascii_ok, ",".join(imports), wired))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAIL == 0 else "FAIL", PASS, PASS + FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())