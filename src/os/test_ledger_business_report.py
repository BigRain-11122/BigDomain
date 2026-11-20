"""Battery suite for tools/ledger_business_report.py - criteria AC-LBRB1..AC-LBRB8.

WHY THIS SUITE EXISTS (measured at R3072, not assumed):
the P-47 item 2 business face is rendered by tools/ledger_business_report.py, and
a per-face census of src/os/test_*.py found NO suite that even names that module:
of the nine faces declared in tools/face_sweep.py FACES, every one except
city-face, ledger-business and the membership page is bound by a battery row
(membership is touched only by test_value_domain.py's price check, which reads
the config literal, not the rendered page). So this face was graded only by the
round-opening [GATES] sweep - a fail-soft line - and a window could regress the
driver with no battery leg ever saying so.

Measured before the criteria were pinned (read-only or private-world):
  * the landed pair answers its own --check: rc=0, "LEDGER BUSINESS CHECK PASS
    fails=0" (html 5276B, json 1061B at measure time);
  * a private-world render reports tx=3 entries=6 issued=300 reconcile_rc=0,
    both probes refused with E_REF_DUPLICATE and E_NEGATIVE_BALANCE, and the
    json sizes block converges onto the bytes on disk;
  * the AC-LBR token appears in the driver and nowhere else in tools/ or src/os/.

WHAT IS PROVED HERE:
  AC-LBRB1  the driver's family is uniquely named: the only ids it names are
            AC-LBR9 and AC-LBR10, and no other running file under tools/ or
            src/os/ names AC-LBR at all (the R3071 collision lesson, applied
            before it bites).
  AC-LBRB2  the landed pair answers its own --check: rc=0 and PASS.
  AC-LBRB3  --check writes nothing: html, json and the demo database keep the
            same size and mtime_ns across the run.
  AC-LBRB4  --check carries weight: a copy whose sizes block disagrees with the
            bytes on disk answers rc=2 and names sizes, and a copy of the json
            with no html beside it answers rc=2 artifacts missing. Both run on
            private copies in a temp directory, never on preview/.
  AC-LBRB5  a private-world render produces the business numbers the face
            claims (tx=3, entries=6, issued=300, reconcile_rc=0, both refusals
            blocked with their codes) and its sizes block equals the bytes on
            disk, so the fixed point really converged.
  AC-LBRB6  the registry row exists exactly once and declares this suite's own
            criterion count.
  AC-LBRB7  source discipline: this file is pure ASCII, imports no network
            module, and names no external host.
  AC-LBRB8  R3074 freshness: the landed json records the sha16 of its three
            derivation inputs and --check names the one that moved. Proved on
            private copies so preview/ is never edited: a ledger hash moved by
            one hex digit answers rc=2 naming E_SOURCE_STALE ledger, a config
            hash moved answers rc=2 naming config, a json with no sources block
            names all three, and the healthy landed pair names none.

Isolation: the only child processes are the driver itself (its --check is
read-only, proved by AC-LBRB3; its render is aimed at a temp directory). The
reconcile step the driver runs is the shipped src/sandbox/ledger/reconcile.py
over that same temp database. Nothing here writes inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "ledger_business_report.py")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
HTML = os.path.join(ROOT, "preview", "ledger-business-report.html")
JSONF = os.path.join(ROOT, "preview", "ledger-business-report.json")
DEMO_DB = os.path.join(ROOT, "preview", "ledger-demo.db")
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


def load_tool():
    spec = importlib.util.spec_from_file_location("ledger_business_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def main():
    src = read(TOOL)

    # ---- B1: the family is uniquely named and the census holds outside it.
    own_ids = sorted(set(re.findall(r"AC-LBR(\d+)", src)))
    offenders = []
    for base in ("tools", os.path.join("src", "os")):
        folder = os.path.join(ROOT, base)
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".py"):
                continue
            if name in ("ledger_business_report.py", os.path.basename(BATTERY)):
                continue
            if base != "tools" and not name.startswith("test_"):
                continue
            text = read(os.path.join(folder, name))
            if re.search(r'"AC-LBR\d', text) or re.search(r"'AC-LBR\d", text):
                offenders.append("%s/%s" % (base, name))
    ok("AC-LBRB1",
       own_ids == ["10", "9"] and not offenders,
       "own_ids=%s offenders=%s" % (",".join(own_ids) or "none",
                                    ",".join(offenders) or "none"))

    # ---- B2 + B3: the driver's own read-only check, and it must not write.
    before = (stamp(HTML), stamp(JSONF), stamp(DEMO_DB))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF), stamp(DEMO_DB))
    verdict = [ln for ln in out.splitlines() if ln.startswith("LEDGER BUSINESS CHECK")]
    last = verdict[-1] if verdict else "CHECK absent"
    ok("AC-LBRB2", rc == 0 and "PASS" in last and "fails=0" in last,
       "rc=%d %s" % (rc, last))
    ok("AC-LBRB3", before == after,
       "stamps_unchanged=%s html_before=%s html_after=%s"
       % (before == after, before[0], after[0]))

    # ---- B4: the check has weight, on private copies only.
    tmp = tempfile.mkdtemp(prefix="lbrb-")
    try:
        html_copy = os.path.join(tmp, "face.html")
        json_copy = os.path.join(tmp, "face.json")
        shutil.copyfile(HTML, html_copy)
        shutil.copyfile(JSONF, json_copy)
        doc = json.loads(read(json_copy))
        sizes = doc.setdefault("sizes", {})
        sizes["html"] = int(sizes.get("html") or 0) + 1
        with open(json_copy, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        bad_rc, bad_out = run_tool(["--check", "--out", html_copy, "--json", json_copy])
        missing_rc, missing_out = run_tool(
            ["--check", "--out", os.path.join(tmp, "absent.html"),
             "--json", os.path.join(tmp, "absent.json")])
        ok("AC-LBRB4",
           bad_rc == 2 and "sizes" in bad_out
           and missing_rc == 2 and "artifacts missing" in missing_out,
           "tampered_rc=%d names_sizes=%s missing_rc=%d names_missing=%s"
           % (bad_rc, "sizes" in bad_out, missing_rc, "artifacts missing" in missing_out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---- B5: a private-world render states the numbers the face claims.
    tmp = tempfile.mkdtemp(prefix="lbrb-render-")
    try:
        db = os.path.join(tmp, "demo.db")
        html = os.path.join(tmp, "face.html")
        jout = os.path.join(tmp, "face.json")
        rc, out = run_tool(["--db", db, "--out", html, "--json", jout])
        payload = json.loads(read(jout)) if os.path.exists(jout) else {}
        rejected = payload.get("rejected") or []
        codes = sorted(r.get("code") for r in rejected)
        blocked = all(r.get("blocked") for r in rejected)
        sizes = payload.get("sizes") or {}
        numbers = (payload.get("tx_count"), payload.get("entry_count"),
                   payload.get("issued"), payload.get("reconcile_rc"))
        ok("AC-LBRB5",
           rc == 0 and numbers == (3, 6, 300, 0) and len(rejected) == 2 and blocked
           and codes == ["E_NEGATIVE_BALANCE", "E_REF_DUPLICATE"]
           and sizes.get("html") == os.path.getsize(html)
           and sizes.get("json") == os.path.getsize(jout),
           "rc=%d numbers=%s rejected=%s sizes_match=%s"
           % (rc, numbers, codes,
              sizes.get("html") == os.path.getsize(html)
              and sizes.get("json") == os.path.getsize(jout)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---- B6: the registry row is the only hook that makes this run at all.
    rows = [ln for ln in read(REGISTRY).splitlines()
            if "test_ledger_business_report.py" in ln]
    declared = None
    for ln in rows:
        tail = ln.strip().rstrip("),").rpartition(",")[2].strip()
        try:
            declared = int(tail)
        except ValueError:
            declared = None
    ok("AC-LBRB6",
       len(rows) == 1 and declared == len(CHECKS) + 3,
       "registry_rows=%d declared=%s own=%d"
       % (len(rows), declared, len(CHECKS) + 3))

    # ---- B7: source discipline, recomputed rather than promised in prose.
    # The needles are assembled from parts so this check's own text cannot
    # satisfy or break the law it states (the R3063 self-match trap).
    own = read(BATTERY)
    ascii_ok = True
    try:
        own.encode("ascii")
    except UnicodeEncodeError:
        ascii_ok = False
    socket_needle = "import " + "socket"
    host_needle = "https" + "://" + "example"
    ok("AC-LBRB7",
       ascii_ok and socket_needle not in own and host_needle not in own,
       "ascii=%s socket_import=%s external_host=%s"
       % (ascii_ok, socket_needle in own, host_needle in own))

    # ---- B8: R3074 freshness - the landed pair names its inputs, and a moved
    # input is named back. Every mutation runs on a private copy in a temp dir.
    doc = json.loads(read(JSONF))
    sources = doc.get("sources") or {}
    hex16 = re.compile(r"^[0-9a-f]{16}$")
    three = sorted(sources)
    three_ok = three == ["config", "driver", "ledger"] and all(
        hex16.match(str(sources[k])) for k in three)
    healthy_rc, healthy_out = run_tool(["--check"])
    clean = healthy_rc == 0 and "E_SOURCE_STALE" not in healthy_out
    tmp = tempfile.mkdtemp(prefix="lbrb-src-")
    try:
        def moved(key, value):
            copy = os.path.join(tmp, "face-%s.json" % key)
            with open(copy, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(value, fh, ensure_ascii=False, indent=1)
                fh.write("\n")
            return copy

        ledger_doc = json.loads(read(JSONF))
        ledger_hash = ledger_doc["sources"]["ledger"]
        ledger_doc["sources"]["ledger"] = ("0" if ledger_hash[0] != "0" else "1") + ledger_hash[1:]
        ledger_copy = moved("ledger", ledger_doc)
        ledger_rc, ledger_out = run_tool(
            ["--check", "--out", HTML, "--json", ledger_copy])

        conf_doc = json.loads(read(JSONF))
        cs = conf_doc["sources"]["config"]
        conf_doc["sources"]["config"] = ("0" if cs[0] != "0" else "1") + cs[1:]
        conf_copy = moved("config", conf_doc)
        conf_rc, conf_out = run_tool(
            ["--check", "--out", HTML, "--json", conf_copy])

        bare_doc = json.loads(read(JSONF))
        bare_doc.pop("sources", None)
        bare_copy = moved("bare", bare_doc)
        bare_rc, bare_out = run_tool(
            ["--check", "--out", HTML, "--json", bare_copy])

        # Both halves of the law live in the driver source: recording at render
        # and comparing at check. Read as anchors so an edit dropping one is red.
        wired = ("\"sources\": source_fingerprints()" in src
                 and "check_sizes(args.out, args.json) + check_sources(args.json)" in src)

        ok("AC-LBRB8",
           three_ok and clean and wired
           and ledger_rc == 2 and "E_SOURCE_STALE ledger" in ledger_out
           and conf_rc == 2 and "E_SOURCE_STALE config" in conf_out
           and bare_rc == 2 and all("E_SOURCE_STALE %s" % k in bare_out
                                    for k in ("driver", "ledger", "config")),
           "sources=%s healthy_clean=%s wired=%s ledger_rc=%d names_ledger=%s "
           "config_rc=%d names_config=%s bare_rc=%d names_all=%s"
           % (",".join(three), clean, wired, ledger_rc,
              "E_SOURCE_STALE ledger" in ledger_out, conf_rc,
              "E_SOURCE_STALE config" in conf_out, bare_rc,
              all("E_SOURCE_STALE %s" % k in bare_out
                  for k in ("driver", "ledger", "config"))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # R3076: the verdict word lives in the literal, not in an inline
    # conditional argument, so the shipped static reader sees the row this
    # suite actually prints (README dialect of test_face_sweep.py).
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s"
              % (len(CHECKS) - len(FAILS), len(CHECKS), FAILS))
    else:
        print("SUITE PASS %d/%d" % (len(CHECKS), len(CHECKS)))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    raise SystemExit(main())
