# rehearse.py - BigDomain release-gate packaging rehearsal (R606).
# Mechanics rehearsal per group cph4/release-gate.md v1.0 (read-only reference).
# REHEARSAL != GATE-PASS: gate 3 (CEO explicit approval) is NOT exercised here;
# the bootstrap door in src/os/backlog.md stays unchecked.
# Gate 1 whitelist law: the product tree = files EXPLICITLY listed in ALLOW_LIST.
# There is NO exclude-list logic anywhere in this script.
# Group tools (Tools/release-scan.ps1, Tools/secret-scan.ps1) are referenced
# read-only per the cross-repo rule; secret-scan writes its report only to the
# group-level gitignored tool face (.codely-cli/secret-scan/), R420 precedent.
# Pre-registered acceptance criteria: AC-RG1..AC-RG6 (src/os/backlog.md R606 row).
# Pure ASCII (encoding law). Deterministic: zero RNG, rerun-stable verdicts.

import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]   # .../domain/BigDomain
GROUP = REPO.parent.parent                  # .../FluxGroup
RELEASE_SCAN = GROUP / "Tools" / "release-scan.ps1"
SECRET_SCAN = GROUP / "Tools" / "secret-scan.ps1"
STAGE_ROOT = REPO / ".codely-cli" / "tmp" / "releasegate-R606"
PKG = STAGE_ROOT / "pkg"
PKG_INJ = STAGE_ROOT / "pkg-injected"
QA_LOG = REPO / "qa" / "release-gate-R606.log"

# gate 1 whitelist: ONLY these faces may enter the product tree.
# image / compose faces = bootstrap-window real artifacts, honestly noted.
ALLOW_LIST = [
    ("src/sandbox/lobby/city_data/world-public.json",
     "world-public/world-public.json"),
    ("src/sandbox/lobby/city_data/citizens-light.jsonl",
     "world-public/citizens-light.jsonl"),
]

# seven-ban mirror of Tools/release-scan.ps1 (independent second口径, AC-RG5)
BANNED_NAMES = {".git", ".env", "__pycache__", ".codely-cli", "CODELY.md",
                "HQ-FEEDBACK.md", "evolution-ledger.md", "orders.md",
                "backlog.md", "state.json", "BLUEPRINT.md"}
BANNED_KEYWORDS = ("id_rsa", ".ppk", "secret", "passwords")
BANNED_DIRS = {"research", "spec"}
SECRET_RES = [re.compile(p) for p in
              ("BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY", "AKIA[0-9A-Z]{16}",
               "ghp_[A-Za-z0-9]{20,}", "sk-[A-Za-z0-9]{20,}")]
PATH_RES = [re.compile(re.escape(p)) for p in
            ("C:\\Users\\", "/home/", "/Users/")]

LINES = []


def log(line):
    LINES.append(line)
    print(line)


def fail(msg):
    log("FAIL " + msg)
    return False


def sha256(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def walk_rel(root):
    out = set()
    for p in sorted(root.rglob("*")):
        out.add(p.relative_to(root).as_posix())
    return out


def build_pkg():
    if STAGE_ROOT.exists():
        shutil.rmtree(STAGE_ROOT)
    PKG.mkdir(parents=True)
    for src_rel, dst_rel in ALLOW_LIST:
        src = REPO / src_rel
        dst = PKG / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    staged = {p for p in walk_rel(PKG) if (PKG / p).is_file()}
    expect = {dst for _, dst in ALLOW_LIST}
    if staged != expect:
        return fail("AC-RG1 product tree != allow-list: extra=%s missing=%s"
                    % (sorted(staged - expect), sorted(expect - staged)))
    log("AC-RG1 PASS whitelist build: staged files == explicit allow-list (%d files)"
        % len(expect))
    return True


def purity_sweep(root, label):
    findings = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.name in BANNED_NAMES:
            findings.append("BANNED-NAME: " + rel)
        for kw in BANNED_KEYWORDS:
            if kw in p.name:
                findings.append("BANNED-KEYWORD(%s): %s" % (kw, rel))
                break
        if p.is_dir():
            if p.name in BANNED_DIRS:
                findings.append("INTERNAL-DIR: " + rel)
            continue
        if p.suffix.lower() not in (".json", ".jsonl", ".md", ".txt", ".yml",
                                    ".yaml", ".cfg", ".ini", ".py", ".ps1"):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for rex in SECRET_RES:
            if rex.search(text):
                findings.append("SECRET(%s): %s" % (rex.pattern, rel))
                break
        for rex in PATH_RES:
            if rex.search(text):
                findings.append("PATH-LEAK(%s): %s" % (rex.pattern, rel))
                break
    if findings:
        log("AC-RG5 FAIL " + label + " purity sweep findings:")
        for f in findings:
            log("  " + f)
        return False
    log("AC-RG5 PASS " + label + " metadata check: no .git face / no secret "
        "pattern / no local path leak (independent sweep, second judgment)")
    return True


def run_ps(script, extra):
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", str(script)] + extra
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def gate_clean_scan():
    rc, out = run_ps(RELEASE_SCAN, ["-Path", str(PKG)])
    for ln in out.strip().splitlines():
        log("  [release-scan] " + ln)
    if rc == 0 and "release-scan: PASS" in out:
        log("AC-RG2 PASS clean-tree release-scan: exit 0 PASS")
        return True
    return fail("AC-RG2 clean-tree release-scan exit=%d" % rc)


def inject_and_rescan():
    if PKG_INJ.exists():
        shutil.rmtree(PKG_INJ)
    shutil.copytree(PKG, PKG_INJ)
    (PKG_INJ / "orders.md").write_text(
        "# internal ledger face (injected rehearsal fixture)\n"
        "- sample internal order line\n", encoding="ascii")
    (PKG_INJ / "key.txt").write_text(
        "# injected rehearsal fixture: documented AWS sample key + key block\n"
        "aws_access_key_id = AKIAIOSFODNN7EXAMPLE\n"
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA rehearsal\n"
        "-----END RSA PRIVATE KEY-----\n", encoding="ascii")
    (PKG_INJ / "notes.md").write_text(
        "# injected rehearsal fixture: local path leak\n"
        "built on machine: C:\\Users\\sjs20\\Desktop\\FluxGroup\\domain\\BigDomain\n",
        encoding="ascii")
    rc, out = run_ps(RELEASE_SCAN, ["-Path", str(PKG_INJ)])
    for ln in out.strip().splitlines():
        log("  [release-scan/injected] " + ln)
    if rc != 2:
        return fail("AC-RG3 injected-tree release-scan exit=%d (expected 2)" % rc)
    classes = {"BANNED-NAME": 0, "SECRET(": 0, "PATH-LEAK": 0}
    for ln in out.splitlines():
        s = ln.strip()
        for k in classes:
            if k in s:
                classes[k] += 1
    if classes["BANNED-NAME"] < 1 or classes["SECRET("] < 1 or classes["PATH-LEAK"] < 1:
        return fail("AC-RG3 injected-tree findings incomplete: %s" % classes)
    log("AC-RG3 PASS injection rehearsal: exit 2 FAIL, all three finding "
        "classes enumerated: BANNED-NAME=%d SECRET=%d PATH-LEAK=%d"
        % (classes["BANNED-NAME"], classes["SECRET("], classes["PATH-LEAK"]))
    return True


def gate_secret_scan():
    rc, out = run_ps(SECRET_SCAN, ["-Days", "1"])
    tail = out.strip().splitlines()[-6:]
    for ln in tail:
        log("  [secret-scan] " + ln)
    if rc == 0:
        log("AC-RG4 PASS secret-scan -Days 1: exit 0, P0=0 "
            "(group-wide recent commits; report -> group gitignored tool face, R420 precedent)")
        return True
    return fail("AC-RG4 secret-scan exit=%d (P0 hits or error, see group report)" % rc)


def main():
    ok = True
    log("BigDomain release-gate packaging rehearsal R606")
    log("ts=" + datetime.now().astimezone().isoformat(timespec="seconds"))
    log("repo=" + REPO.name + "  group tools (read-only ref):")
    for t in (RELEASE_SCAN, SECRET_SCAN):
        log("  %s sha256=%s" % (t.name, sha256(t)))
    log("REHEARSAL != GATE-PASS: gate 3 (CEO explicit approval) NOT exercised; "
        "bootstrap door stays unchecked. Image/compose faces = bootstrap-window real artifacts.")
    ok = build_pkg() and ok
    ok = purity_sweep(PKG, "staged") and ok
    ok = gate_clean_scan() and ok
    ok = inject_and_rescan() and ok
    ok = gate_secret_scan() and ok
    log("VERDICT " + ("PASS" if ok else "FAIL") +
        " (rehearsal of gate mechanics only; real package gate run happens at bootstrap)")
    QA_LOG.write_text("\n".join(LINES) + "\n", encoding="ascii")
    print("evidence log -> %s" % QA_LOG)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
