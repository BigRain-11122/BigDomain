"""Live capture for R2404 (read-only on the real tree).

Proves the operator-walked face changed on THIS tree: a bare evidence name that
measuredly lives in qa now resolves, where the pre-fix join to the root missed
it. Nothing here writes anything but its own log.
"""

import hashlib
import io
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import followup_bare_evidence_face as FBEF  # noqa: E402

MODULE = os.path.join(BASE, "followup_bare_evidence_face.py")
LOG = "qa/followup-bare-evidence-face-live-R2404.log"
BARE = "reconcile-all-R2394-retry.log"
CLI = os.path.join(BASE, "followup_bare_evidence_face.py")


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


def run(argv):
    proc = subprocess.Popen([sys.executable, CLI] + argv,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace").strip(), \
        err.decode("utf-8", "replace").strip()


def main():
    before = digest(MODULE)
    lines = ["LIVE R2404 followup bare evidence face on the real tree"]

    report = FBEF.placement(BARE, REPO)
    old_join = os.path.join(REPO, BARE)
    lines.append("  bare=%s pile=%s argument=%s exists=%s verdict=%s"
                 % (report["evidence"], report["pile"] or "-",
                    report["argument"] or "-",
                    "yes" if report["exists"] else "no",
                    report["verdict"]))
    lines.append("  OLD-JOIN root/%s exists=%s  (this is the MISSING EVIDENCE "
                 "the operator used to see at exit 3)"
                 % (BARE, "yes" if os.path.isfile(old_join) else "no"))

    with_dir = "qa/" + BARE
    carried = FBEF.placement(with_dir, REPO)
    lines.append("  with-dir=%s argument=%s exists=%s unchanged=%s"
                 % (carried["evidence"], carried["argument"],
                    "yes" if carried["exists"] else "no",
                    "yes" if carried["argument"] == with_dir else "no"))

    rc_ok, out_ok, _ = run(["--check", BARE, "--root", REPO])
    lines.append("  CLI ok rc=%d" % rc_ok)
    lines.extend("    " + line for line in out_ok.splitlines())

    rc_abs, out_abs, _ = run(["--check", "no-such-evidence-R2404.log",
                              "--root", REPO])
    lines.append("  CLI refused rc=%d" % rc_abs)
    lines.extend("    " + line for line in out_abs.splitlines())

    rc_bad, out_bad, _ = run(["--check", BARE, "--nope", "--root", REPO])
    lines.append("  CLI bad flag rc=%d line=%s" % (rc_bad, out_bad.splitlines()[0]
                                                   if out_bad else "-"))

    world = tempfile.mkdtemp(prefix="bigdomain-fbef-live-")
    deep = os.path.join(world, "qa", "rounds")
    os.makedirs(deep)
    with io.open(os.path.join(deep, "deep-R9001.log"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write("SECTION matrix PASS detail\nVERDICT R9001 PASS\n")
    deep_report = FBEF.placement("deep-R9001.log", world)
    lines.append("  deep-pile file-exists=%s verdict=%s code=%s"
                 % ("yes" if os.path.isfile(os.path.join(
                     deep, "deep-R9001.log")) else "no",
                    deep_report["verdict"], deep_report["code"] or "-"))
    import shutil
    shutil.rmtree(world, ignore_errors=True)

    after = digest(MODULE)
    lines.append("  module digest before=%s after=%s" % (before, after))

    text = "\n".join(lines) + "\n"
    with io.open(os.path.join(REPO, LOG), "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write(text)
    raw = io.open(os.path.join(REPO, LOG), "rb").read()
    print("LIVE-CAPTURED %s bytes=%d crlf=%d bare_cr=%d digest_stable=%s"
          % (LOG, len(raw), raw.count(b"\r\n"),
             raw.count(b"\r") - raw.count(b"\r\n"), before == after))
    return 0


if __name__ == "__main__":
    sys.exit(main())