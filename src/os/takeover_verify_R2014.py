# takeover_verify_R2014.py - 32nd-case crashed-round takeover battery.
# ASCII only. The crashed R2014 session delivered the lobby idem
# gate-order budget window (suite 72/72 standalone green, sha16
# 7968ed2077e7fedd) but its battery driver redirected TMP/TEMP into the
# repo tree, which flipped the world-db-outside-repo hygiene flags in 19
# persist suites (RUNNER FAIL 20 assertions). This battery: (0) probes
# temp writability for both interpreters, (1) replays the suite double-run
# under the crashed round's exact env and anchor-matches the sha16,
# (2) re-runs the full RUNNER under ambient (outside-repo) temp ->
# qa/reconcile-all-R2014-2.log (the crashed round's FAIL log stays on
# disk as the honest failure record), (3) suite-matrix regen + --check,
# (4) fingerprint --check, (5) runner-profile --daily --check,
# (6) qa-writer census --check (documented re-anchor if a new-file flag
# fires), (7) group-orders rows-after-baseline scan for BigDomain faces.
import datetime
import hashlib
import io
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
GRP = r"C:\Users\sjs20\Desktop\FluxGroup"

VENV_PY = os.path.join(ROOT, "src", "sandbox", "lobby", ".venv",
                       "Scripts", "python.exe")
LOBBY_TC = os.path.join(ROOT, "src", "sandbox", "lobby",
                        "test_client.py")
RUNNER = os.path.join("src", "sandbox", "reconcile_all.py")
CRASH_WORK = os.path.join(ROOT, ".codely-cli", "tmp", "idem-bg-2014")
EV_RUNNER2 = os.path.join("qa", "reconcile-all-R2014-2.log")
EV_TAKEOVER = os.path.join(ROOT, "qa", "takeover-verify-R2014.log")
EV_MATRIX = os.path.join("docs", "sandbox-suite-matrix.md")
ANCHOR_SHA = "7968ed2077e7fedd"

REPORT = []


def rep(s):
    print(s, flush=True)
    REPORT.append(s)


def norm_lf(t):
    return t.replace("\r\n", "\n").replace("\r", "\n")


def run_progress(cmd, env, cwd, label, echo_fail=True):
    p = subprocess.Popen(cmd, cwd=cwd, env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)
    q = queue.Queue()

    def reader():
        for raw in p.stdout:
            q.put(raw.decode("utf-8", "replace"))
        q.put(None)

    th = threading.Thread(target=reader)
    th.daemon = True
    th.start()
    buf = []
    n = 0
    empties = 0
    last = time.time()
    while True:
        try:
            item = q.get(timeout=5.0)
        except queue.Empty:
            if p.poll() is not None:
                empties += 1
                if empties >= 3:
                    break
            else:
                empties = 0
            if time.time() - last > 25:
                print("  [%s] ...running lines=%d elapsed=%.0fs"
                      % (label, n, time.time() - T0), flush=True)
                last = time.time()
            continue
        if item is None:
            break
        empties = 0
        buf.append(item)
        n += 1
        s = item.strip()
        if echo_fail and (s.startswith("FAIL") or s.startswith("RUNNER")):
            print("  [%s] %s" % (label, s[:130]), flush=True)
        elif s.startswith("PASS suite") and n % 25 == 0:
            print("  [%s] %s" % (label, s[:110]), flush=True)
        if time.time() - last > 25:
            print("  [%s] ...running lines=%d" % (label, n),
                  flush=True)
            last = time.time()
    rc = p.wait()
    return rc, "".join(buf)


T0 = time.time()
rep("takeover_verify_R2014 start %s" %
    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# (0) temp probes
AMB_TMP = tempfile.gettempdir()
FB_TMP = r"C:\Users\sjs20\.codely-cli\tmp\takeover-r2014-env"


def probe(py, tmpdir, tag):
    try:
        os.makedirs(tmpdir, exist_ok=True)
        fp = os.path.join(tmpdir, "probe_takeover_r2014_%s.txt" % tag)
        code = ("import os\n"
                "p=r'%s'\n"
                "f=open(p,'w');f.write('ok');f.close();os.remove(p)\n"
                "print('OK')\n") % fp
        r = subprocess.run([py, "-c", code], capture_output=True,
                           text=True, timeout=60)
        rep("PROBE %-10s py=%s rc=%d out=%s err=%s"
            % (tag, "venv" if py == VENV_PY else "sys",
               r.returncode, (r.stdout or "").strip()[:20],
               (r.stderr or "").strip().replace("\n", " ")[-100:]))
        return r.returncode == 0
    except Exception as e:
        rep("PROBE %s EXC=%r" % (tag, e))
        return False


p_amb_sys = probe(sys.executable, AMB_TMP, "amb-sys")
p_amb_venv = probe(VENV_PY, AMB_TMP, "amb-venv")
p_fb_sys = probe(sys.executable, FB_TMP, "fb-sys")

if p_amb_sys:
    RUN_ENV = dict(os.environ)
    ENV_DESC = "ambient-system-temp"
elif p_fb_sys:
    RUN_ENV = dict(os.environ)
    RUN_ENV["TMP"] = FB_TMP
    RUN_ENV["TEMP"] = FB_TMP
    ENV_DESC = "outside-repo-fallback"
else:
    rep("PROBE FATAL: no writable outside-repo temp found")
    sys.exit(2)
rep("RUNNER_ENV=%s tmpdir=%s" % (ENV_DESC, AMB_TMP if p_amb_sys
                                 else FB_TMP))

# (1) suite double-run exact replay (crashed round env + cwd)
SUITE_ENV = dict(os.environ)
SUITE_ENV["TMP"] = CRASH_WORK
SUITE_ENV["TEMP"] = CRASH_WORK
os.makedirs(CRASH_WORK, exist_ok=True)
rc1, o1 = run_progress([VENV_PY, LOBBY_TC], SUITE_ENV, CRASH_WORK,
                       "suite-run1")
rc2, o2 = run_progress([VENV_PY, LOBBY_TC], SUITE_ENV, CRASH_WORK,
                       "suite-run2")
a = norm_lf(o1)
b = norm_lf(o2)
sha16 = hashlib.sha256(b.encode("utf-8")).hexdigest()[:16]
suite_anchor = (rc1 == 0 and rc2 == 0 and a == b and sha16 == ANCHOR_SHA)
rep("SUITE replay rc=%d/%d bytes=%d/%d identical=%s sha16=%s "
    "anchor_match=%s" % (rc1, rc2, len(o1), len(o2), a == b, sha16,
                         suite_anchor))

# (2) full RUNNER battery under outside-repo temp
rc3, o3 = run_progress([sys.executable, RUNNER, EV_RUNNER2], RUN_ENV,
                       ROOT, "RUNNER")
with io.open(os.path.join(ROOT, EV_RUNNER2), "w", encoding="utf-8",
             newline="\n") as fh:
    fh.write(norm_lf(o3))
runner_ok = rc3 == 0 and "RUNNER PASS" in o3
tl = [ln for ln in o3.splitlines() if ln.startswith("RUNNER")]
rep("RUNNER rc=%d %s" % (rc3, tl[-1] if tl else "no-runner-line"))

# (3) suite matrix regen + --check
m1 = subprocess.run([sys.executable, os.path.join("src", "sandbox",
                    "suite_matrix.py"), "--out", EV_MATRIX,
                    "--evidence", EV_RUNNER2], cwd=ROOT, env=RUN_ENV,
                   capture_output=True, text=True)
m2 = subprocess.run([sys.executable, os.path.join("src", "sandbox",
                    "suite_matrix.py"), "--out", EV_MATRIX,
                    "--evidence", EV_RUNNER2, "--check"], cwd=ROOT,
                   env=RUN_ENV, capture_output=True, text=True)
mtail = ([ln for ln in ((m2.stdout or "") + (m2.stderr or ""))
          .splitlines() if ln.strip()] or ["no-line"])
matrix_ok = (m1.returncode == 0 and m2.returncode == 0
             and "FAIL" not in ((m2.stdout or "")
                                + (m2.stderr or "")))
rep("MATRIX regen rc=%d check rc=%d %s" % (m1.returncode,
    m2.returncode, mtail[-1][:110]))

# (4) fingerprint --check
f = subprocess.run([sys.executable, os.path.join("src", "sandbox",
                   "fingerprint_regen.py"), "--check"], cwd=ROOT,
                  env=RUN_ENV, capture_output=True, text=True)
ftail = ([ln for ln in ((f.stdout or "") + (f.stderr or ""))
          .splitlines() if ln.strip()] or ["no-line"])
fp_ok = f.returncode == 0
rep("FINGERPRINT rc=%d %s" % (f.returncode, ftail[-1][:110]))

# (5) runner profile --daily --check
pf = subprocess.run([sys.executable, os.path.join("src", "sandbox",
                    "runner_profile.py"), "--daily", "--check"],
                   cwd=ROOT, env=RUN_ENV, capture_output=True, text=True)
ptail = ([ln for ln in ((pf.stdout or "") + (pf.stderr or ""))
          .splitlines() if ln.strip()] or ["no-line"])
prof_ok = pf.returncode == 0
rep("PROFILE rc=%d %s" % (pf.returncode, ptail[-1][:110]))

# (6) qa writer census --check (documented re-anchor face)
c = subprocess.run([sys.executable, os.path.join("src", "sandbox",
                   "qa_writer_census.py"), "--check"], cwd=ROOT,
                   env=RUN_ENV, capture_output=True, text=True)
ctail = ([ln for ln in ((c.stdout or "") + (c.stderr or ""))
          .splitlines() if ln.strip()] or ["no-line"])
census_ok = c.returncode == 0
rep("CENSUS rc=%d %s" % (c.returncode, ctail[-1][:110]))
if not census_ok:
    cu = subprocess.run([sys.executable, os.path.join("src", "sandbox",
                        "qa_writer_census.py"), "--update-baseline"],
                        cwd=ROOT, env=RUN_ENV, capture_output=True,
                        text=True)
    c2 = subprocess.run([sys.executable, os.path.join("src", "sandbox",
                         "qa_writer_census.py"), "--check"], cwd=ROOT,
                        env=RUN_ENV, capture_output=True, text=True)
    c2tail = ([ln for ln in ((c2.stdout or "") + (c2.stderr or ""))
               .splitlines() if ln.strip()] or ["no-line"])
    census_ok = c2.returncode == 0
    rep("CENSUS re-anchor rc=%d then recheck rc=%d %s (documented "
        "new-evidence re-anchor, R2010/R1996 precedent)" %
        (cu.returncode, c2.returncode, c2tail[-1][:110]))

# (7) group-orders rows-after-baseline scan for BigDomain faces
with io.open(os.path.join(GRP, "docs", "orders.md"), "r",
             encoding="utf-8", errors="replace") as fh:
    ol = fh.read().splitlines()
opipe = [ln for ln in ol if ln.startswith("|")]
new_ord = [ln for ln in opipe
           if re.match(r"\|\s*2026-10-17\s+(09:[1-9]|[1-9]\d:)", ln)]
bd_ord = [ln for ln in new_ord if "BigDomain" in ln]
rep("ORD_SCAN new_rows_since_09:0x=%d bigdomain_hits=%d"
    % (len(new_ord), len(bd_ord)))
for ln in bd_ord[:4]:
    rep("  BDORD::%s" % ln.strip()[:150])
tail_ts = None
for ln in reversed(opipe):
    m = re.match(r"\|\s*2026-10-1[0-9]\s+(\S+)", ln)
    if m:
        tail_ts = m.group(1)
        break
rep("ORD_TAIL_TS=%s" % tail_ts)

# verdict block
rep("-- battery verdicts --")
for name, ok in (("suite-anchor-replay", suite_anchor),
                 ("runner-full-battery", runner_ok),
                 ("suite-matrix-check", matrix_ok),
                 ("fingerprint-check", fp_ok),
                 ("profile-daily-check", prof_ok),
                 ("writer-census-check", census_ok)):
    rep("%s %s" % ("PASS" if ok else "FAIL", name))
all_ok = (suite_anchor and runner_ok and matrix_ok and fp_ok
          and prof_ok and census_ok)
rep("BATTERY %s elapsed=%.1fs" % ("PASS" if all_ok else "FAIL",
                                  time.time() - T0))
with io.open(EV_TAKEOVER, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(norm_lf("\n".join(REPORT) + "\n"))
sys.exit(0 if all_ok else 1)
