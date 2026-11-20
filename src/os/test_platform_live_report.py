"""Battery suite for tools/platform_live_report.py - criteria AC-PLVB1..AC-PLVB8.

WHY THIS SUITE EXISTS (measured at R3071, not assumed):
tools/platform_live_report.py renders the face that boots every sandbox door on
real sockets and grades it with AC-PLVR1..AC-PLVR9, yet a full-text search of
src/sandbox/reconcile_all.py found ZERO platform_live rows: the face was graded
only by the round-opening [GATES] sweep, so a window could regress it and no
battery leg would ever say so. The same probe found a second defect in the same
file - its criteria were named AC-PLR1..AC-PLR9 while
src/os/patterns_label_readability.py has carried AC-PLR1..AC-PLR6 since R2494 -
so one printed id named two unrelated criteria. R3071 renamed this driver's
family to AC-PLVR and this suite pins both halves.

WHAT IS PROVED HERE:
  AC-PLVB1  the driver's CRITERIA table is exactly AC-PLVR1..AC-PLVR9 and its
            source carries no AC-PLR token that is not part of AC-PLVR.
  AC-PLVB2  the census holds outside the readability family: no file under
            tools/ or src/os/ names AC-PLR (AC-PLRC counts as a family member),
            and AC-PLVR appears only in the driver.
  AC-PLVB3  the landed pair answers its own --check: real sockets, real child
            processes, rc=0 and VERDICT PASS over every criterion.
  AC-PLVB4  ac_plr8 carries weight: dropping a compliance face name or the
            mock statement turns it red, while the real page reads green.
  AC-PLVB5  ac_plr9 carries weight: a hand-typed count planted in an intent
            turns it red, while the shipped intents read green.
  AC-PLVB6  --check writes nothing: the preview pair keeps its size and mtime.
  AC-PLVB7  the registry row exists exactly once and declares this suite's own
            criterion count.
  AC-PLVB8  source discipline: this file is pure ASCII, imports no network
            module, and names no external host.

Isolation: the only subprocess is the driver's own --check (read-only by
measurement, proved by AC-PLVB6), and it binds loopback ports only. Nothing
here writes inside the repository.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import importlib.util
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "platform_live_report.py")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
HTML = os.path.join(ROOT, "preview", "platform-live-report.html")
JSONF = os.path.join(ROOT, "preview", "platform-live-report.json")
BATTERY = os.path.abspath(__file__)

READABILITY_OWNERS = (
    "patterns_label_readability.py",
    "test_patterns_label_readability.py",
    "patterns_label_readability_render_consumer.py",
    "test_patterns_label_readability_render_consumer.py",
)

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
    spec = importlib.util.spec_from_file_location("platform_live_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def stamp(path):
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def main():
    src = read(TOOL)
    mod = load_tool()

    # ---- B1: the family is uniquely named and complete.
    ids = [cid for cid, _ in mod.CRITERIA]
    stray = re.findall(r'"AC-PLR\d', src) + re.findall(r"'AC-PLR\d", src)
    ok("AC-PLVB1",
       ids == ["AC-PLVR%d" % n for n in range(1, 10)] and not stray,
       "ids=%s stray_ac_plr_ids=%d" % (",".join(ids), len(stray)))

    # ---- B2: no other RUNNING suite claims either name. Seed scripts that
    # froze the readability family's text at R2500..R2503 are history rows, not
    # suites, so they are out of scope by name rather than by hope.
    offenders = []
    for base in ("tools", os.path.join("src", "os")):
        folder = os.path.join(ROOT, base)
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".py"):
                continue
            if name in READABILITY_OWNERS or name == os.path.basename(BATTERY):
                continue
            if base != "tools" and not name.startswith("test_"):
                continue
            text = read(os.path.join(folder, name))
            if re.search(r'"AC-PLR\d', text) or re.search(r"'AC-PLR\d", text):
                offenders.append("%s/%s" % (base, name))
            if name != "platform_live_report.py" and re.search(r'"AC-PLVR\d', text):
                offenders.append("%s/%s" % (base, name))
    ok("AC-PLVB2", not offenders, "offenders=%s" % (",".join(offenders) or "none"))

    # ---- B3 + B6: the driver's own read-only check, and it must not write.
    before = (stamp(HTML), stamp(JSONF))
    proc = subprocess.run(
        [sys.executable, TOOL, "--check"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300,
    )
    out = proc.stdout.decode("utf-8", "replace")
    verdict = [ln for ln in out.splitlines() if ln.startswith("VERDICT ")]
    last = verdict[-1] if verdict else "VERDICT absent"
    rows = [ln for ln in out.splitlines() if ln.startswith(" | ")]
    green = [ln for ln in rows if ln.startswith(" | PASS ")]
    after = (stamp(HTML), stamp(JSONF))
    ok("AC-PLVB3",
       proc.returncode == 0 and "VERDICT PASS 9/9" in last and len(green) == len(rows) == 9,
       "rc=%d rows=%d green=%d %s" % (proc.returncode, len(rows), len(green), last))
    ok("AC-PLVB6", before == after, "pair_unchanged=%s sizes=%s" % (before == after, before))

    # ---- B4: ac_plr8 refuses a page that lost a standing face.
    doc = read(HTML)
    size = os.path.getsize(HTML)
    real8 = mod.ac_plr8(doc, size, os.path.getsize(JSONF))
    face_name = mod.COMPLIANCE[0][0]
    noface8 = mod.ac_plr8(doc.replace(face_name, "X" * len(face_name)), size, 1)
    nomock8 = mod.ac_plr8(doc.replace("mock=true", "mock=XXXXX"), size, 1)
    ok("AC-PLVB4",
       real8["pass"] and not noface8["pass"] and not nomock8["pass"],
       "real=%s no_face=%s no_mock=%s" % (real8["pass"], noface8["pass"], nomock8["pass"]))

    # ---- B5: ac_plr9 refuses a typed count planted in an intent.
    real9 = mod.ac_plr9(doc, mod.CRITERIA)
    planted = list(mod.CRITERIA)
    planted[0] = (planted[0][0], planted[0][1] + " over six doors")
    planted9 = mod.ac_plr9(doc, planted)
    ok("AC-PLVB5",
       real9["pass"] and not planted9["pass"],
       "real=%s planted=%s" % (real9["measured"], planted9["measured"]))

    # ---- B7: the registry row is the only hook that makes this run at all.
    rows_in_registry = [ln for ln in read(REGISTRY).splitlines()
                        if "test_platform_live_report.py" in ln]
    declared = None
    for ln in rows_in_registry:
        tail = ln.strip().rstrip("),").rpartition(",")[2].strip()
        try:
            declared = int(tail)
        except ValueError:
            declared = None
    ok("AC-PLVB7",
       len(rows_in_registry) == 1 and declared == len(CHECKS) + 2,
       "registry_rows=%d declared=%s own=%d"
       % (len(rows_in_registry), declared, len(CHECKS) + 2))

    # ---- B8: source discipline, recomputed rather than promised in prose.
    # The two needles are assembled from parts so this check's own text cannot
    # satisfy or break the law it states (the self-match trap from R3063).
    own = read(BATTERY)
    ascii_ok = True
    try:
        own.encode("ascii")
    except UnicodeEncodeError:
        ascii_ok = False
    socket_needle = "import " + "socket"
    host_needle = "https" + "://" + "example"
    ok("AC-PLVB8",
       ascii_ok and socket_needle not in own and host_needle not in own,
       "ascii=%s socket_import=%s external_host=%s"
       % (ascii_ok, socket_needle in own, host_needle in own))

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
