# rerun_R1985b.py - takeover re-run of the full RUNNER with the
# healthy tee dialect (LF-only UTF-8, no BOM - the zero-tee-key
# census exemption law): the runner output is captured in memory
# and written ONCE at completion, so no partial file ever lands
# in qa/ mid-run (the cd7 live-tree census inside the runner sees
# zero new dialect files -> DRIFT-CLEAN -> full green).
# Also LF-normalizes the first-run evidence log (ps-utf16 dialect
# pitfall family R1969/R1976: PS 5.1 Tee-Object writes UTF-16;
# the transcoded CRLF form is pwsh-capture class which is a
# baselined class - only the LF-only form is the exempt tee).
import subprocess
import sys

FIRST = r"qa\reconcile-all-R1985b.log"
OUT2 = r"qa\reconcile-all-R1985b-2.log"


def main():
    # 1. LF-normalize the first-run log (already transcoded UTF-8)
    with open(FIRST, "rb") as fh:
        d = fh.read().decode("utf-8")
    with open(FIRST, "wb") as fh:
        fh.write(d.replace("\r\n", "\n").encode("utf-8"))
    print("b-log LF-normalized bytes=%d" % len(d))

    # 2. full RUNNER re-run, in-memory capture, single final write
    p = subprocess.run([sys.executable, r"src\sandbox\reconcile_all.py"],
                       capture_output=True)
    raw = p.stdout + p.stderr
    with open(OUT2, "wb") as fh:
        fh.write(raw.replace(b"\r\n", b"\n"))
    txt = raw.decode("utf-8", "replace").strip().splitlines()
    print("RUNNER-rc=%d" % p.returncode)
    print("LAST: %s" % (txt[-1] if txt else "<empty>"))
    print("PREV: %s" % (txt[-2] if len(txt) > 1 else "<none>"))
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
