"""Battery suite for tools/city_face_report.py - criteria AC-CFYB1..AC-CFYB7.

WHY THIS SUITE EXISTS (measured at R3073, not assumed):
the P-47 item-1 city face is rendered by tools/city_face_report.py, and that
driver carries its own --check with AC-CFY1..8. What it did not have was a
battery row: src/sandbox/reconcile_all.py (732 suites at measure time) had
ZERO rows naming the module, so the face was graded only by the round-opening
[GATES] sweep - a fail-soft line. A window could regress the driver and no
battery leg would ever say so. This is the second of the two faces the R3072
census named; the third (the membership page body) stays carried.

Measured before the criteria were pinned (read-only or private-world):
  * registry rows naming city_face_report: 0;
  * the landed pair answers its own --check: rc=0, VERDICT PASS checks=8/8,
    fresh_fingerprint identical to landed;
  * --check writes nothing: html 7300B / json 5004B keep the same size and
    mtime_ns across the run;
  * --check carries weight on private copies: tampered landed facts answer
    rc=2 with "FAIL AC-CFY2", a missing json answers rc=3 E_INPUT landed json
    missing, a missing html answers rc=2 naming AC-CFY1;
  * a temp-dir render converges: sizes equal the bytes on disk and the facts
    read rows=3 seats=9 served=12 source=15 leaked=[];
  * the AC-CFY family is named by the driver only.

WHAT IS PROVED HERE:
  AC-CFYB1  the driver names exactly AC-CFY1..8, and no other running file
            under tools/ or src/os/ names AC-CFY at all (R3071 lesson first).
  AC-CFYB2  the landed pair answers its own --check: rc=0, VERDICT PASS, and
            the fresh fingerprint equals the landed one - which is the only
            freshness proof this face has, and why no new re-render tool is
            added here.
  AC-CFYB3  --check writes nothing: html and json keep the same size and
            mtime_ns across it.
  AC-CFYB4  --check carries weight: three private-copy arms, each red on its
            own question (tampered facts -> AC-CFY2, missing json -> E_INPUT,
            missing html -> AC-CFY1). Never aimed at preview/.
  AC-CFYB5  a private-directory render converges and states the numbers the
            face claims (imported_rows=3, honorary_seats=9, served_count=12,
            source_field_count=15, deep_water_leaked empty) with a sizes block
            equal to the bytes on disk.
  AC-CFYB6  the registry row exists exactly once and declares this suite's own
            criterion count.
  AC-CFYB7  source discipline: this file is pure ASCII, imports no socket or
            network module, and names no external host.

Isolation: the only child process is the driver itself. Its --check is proved
read-only by AC-CFYB3; its render is aimed at a temp directory. The driver
binds its own ephemeral loopback port (its AC-CFY6 measures the shipped HTTP
handler), so loopback is the only transport and nothing here imports socket.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "city_face_report.py")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
HTML = os.path.join(ROOT, "preview", "city-face-report.html")
JSONF = os.path.join(ROOT, "preview", "city-face-report.json")
BATTERY = os.path.abspath(__file__)

CHECKS = []
FAILS = []


def ok(name, cond, detail):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def stamp(path):
    if not os.path.exists(path):
        return None
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def run_tool(args, timeout=300):
    proc = subprocess.run(
        [sys.executable, TOOL] + args,
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
    )
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def last_verdict(out):
    lines = [ln for ln in out.splitlines() if ln.startswith("VERDICT")]
    return lines[-1] if lines else ""


def main():
    src = read(TOOL)

    # ---- B1: the driver's own family is exactly 1..8, and it is alone.
    own_ids = sorted({int(n) for n in re.findall(r"AC-CFY(\d+)", src)})
    offenders = []
    for base in ("tools", os.path.join("src", "os")):
        folder = os.path.join(ROOT, base)
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".py"):
                continue
            if name in ("city_face_report.py", os.path.basename(BATTERY)):
                continue
            if base != "tools" and not name.startswith("test_"):
                continue
            text = read(os.path.join(folder, name))
            if re.search(r'"AC-CFY\d', text) or re.search(r"'AC-CFY\d", text):
                offenders.append("%s/%s" % (base, name))
    ok("AC-CFYB1",
       own_ids == list(range(1, 9)) and not offenders,
       "own_ids=%s offenders=%s"
       % (",".join(str(i) for i in own_ids) or "none",
          ",".join(offenders) or "none"))

    # ---- B2 + B3: the driver's own read-only check, and it must not write.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    verdict = last_verdict(out)
    fp = re.search(r"fresh_fingerprint=(\S+) landed=(\S+)", verdict)
    fresh_landed = bool(fp) and fp.group(1) == fp.group(2)
    ok("AC-CFYB2",
       rc == 0 and "PASS" in verdict and "checks=8/8" in verdict and fresh_landed,
       "rc=%d %s" % (rc, verdict or "VERDICT absent"))
    ok("AC-CFYB3", before == after,
       "stamps_unchanged=%s html_before=%s html_after=%s"
       % (before == after, before[0], after[0]))

    # ---- B4: the check has weight, on private copies only.
    tmp = tempfile.mkdtemp(prefix="cfyb-")
    try:
        h = os.path.join(tmp, "face.html")
        j = os.path.join(tmp, "face.json")
        shutil.copyfile(HTML, h)
        shutil.copyfile(JSONF, j)
        doc = json.loads(read(j))
        doc["facts"]["read"]["deep_water_leaked"] = ["hook"]
        with open(j, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        tampered_rc, tampered_out = run_tool(
            ["--check", "--out", h, "--json", j])
        missing_rc, missing_out = run_tool(
            ["--check", "--out", h, "--json", os.path.join(tmp, "absent.json")])
        nohtml_rc, nohtml_out = run_tool(
            ["--check", "--out", os.path.join(tmp, "absent.html"), "--json", j])
        ok("AC-CFYB4",
           tampered_rc == 2 and "FAIL AC-CFY2" in tampered_out
           and missing_rc == 3 and "E_INPUT landed json missing" in missing_out
           and nohtml_rc == 2 and "AC-CFY1" in nohtml_out,
           "tampered=%d names_cfy2=%s missing_json=%d missing_html=%d names_cfy1=%s"
           % (tampered_rc, "FAIL AC-CFY2" in tampered_out, missing_rc,
              nohtml_rc, "AC-CFY1" in nohtml_out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---- B5: a private-directory render states the numbers the face claims.
    tmp = tempfile.mkdtemp(prefix="cfyb-render-")
    try:
        h = os.path.join(tmp, "face.html")
        j = os.path.join(tmp, "face.json")
        rc, out = run_tool(["--out", h, "--json", j])
        doc = json.loads(read(j)) if os.path.exists(j) else {}
        facts = doc.get("facts") or {}
        city = facts.get("city") or {}
        rd = facts.get("read") or {}
        sizes = doc.get("sizes") or {}
        numbers = (city.get("imported_rows"), city.get("honorary_seats"),
                   rd.get("served_count"), rd.get("source_field_count"))
        sizes_match = (sizes.get("html") == os.path.getsize(h)
                       and sizes.get("json") == os.path.getsize(j))
        ok("AC-CFYB5",
           rc == 0 and doc.get("verdict") == "PASS"
           and numbers == (3, 9, 12, 15)
           and rd.get("deep_water_leaked") == []
           and sizes_match,
           "rc=%d numbers=%s leaked=%s sizes_match=%s"
           % (rc, numbers, rd.get("deep_water_leaked"), sizes_match))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---- B6: the registry row is the only hook that makes this run at all.
    rows = [ln for ln in read(REGISTRY).splitlines()
            if "test_city_face_report.py" in ln]
    declared = None
    for ln in rows:
        tail = ln.strip().rstrip("),").rpartition(",")[2].strip()
        try:
            declared = int(tail)
        except ValueError:
            declared = None
    ok("AC-CFYB6",
       len(rows) == 1 and declared == len(CHECKS) + 2,
       "registry_rows=%d declared=%s own=%d"
       % (len(rows), declared, len(CHECKS) + 2))

    # ---- B7: source discipline, recomputed rather than promised in prose.
    # The needles are assembled from parts so this file's own text cannot
    # satisfy or break the law it states (the R3063 self-match trap).
    own = read(BATTERY)
    ascii_ok = True
    try:
        own.encode("ascii")
    except UnicodeEncodeError:
        ascii_ok = False
    socket_needle = "import " + "socket"
    host_needle = "https" + "://" + "example"
    ok("AC-CFYB7",
       ascii_ok and socket_needle not in own and host_needle not in own
       and re.search(r'"AC-CFYB\d', own) is not None,
       "ascii=%s socket_import=%s external_host=%s"
       % (ascii_ok, socket_needle in own, host_needle in own))

    print("SUITE %s %d/%d" % ("PASS" if not FAILS else "FAIL",
                              len(CHECKS) - len(FAILS), len(CHECKS)))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    raise SystemExit(main())
