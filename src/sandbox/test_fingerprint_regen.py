"""Fingerprint-regen acceptance suite (R1713; criteria AC-BF1..AC-BF7
were pre-registered in state/queue/tech.md before the CLI code existed -
honesty law). Exit 0 = all green. Stdlib only, ASCII source, zero network."""

import json
import os
import re
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(BASE, "fingerprint_regen.py")
CHAINS = os.path.join(BASE, "migration_chains.json")
TRIO = (os.path.join("src", "sandbox", "schema_migrate.py"),
        os.path.join("src", "sandbox", "migration_chains.json"),
        os.path.join("src", "sandbox", "test_schema_migrate.py"))

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def run_cli(chain, *actions):
    proc = subprocess.run(
        [sys.executable, CLI, "--chain", chain] + list(actions),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300, cwd=BASE)
    return proc.returncode, (proc.stdout or "").strip()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def copy_chains(tmp):
    dst = os.path.join(tmp, "chains.json")
    with open(dst, "wb") as handle:
        handle.write(read_bytes(CHAINS))
    return dst


def load_chain(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save_chain(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main():
    tmp = tempfile.mkdtemp(prefix="fpregen-suite-")
    try:
        # AC-BF1: CLI face + live check + read-only discipline
        proc = subprocess.run(
            [sys.executable, CLI, "--help"], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60, cwd=BASE)
        check(proc.returncode == 0 and "--update" in (proc.stdout or ""),
              "AC-BF1 CLI face: --help exits 0 and documents --update")

        before = read_bytes(CHAINS)
        code, out = run_cli(CHAINS, "--check")
        check(code == 0 and "verdict CLEAN domains=5" in out,
              "AC-BF2 live check on shipped chains: exit 0 + CLEAN domains=5")
        pass_rows = [ln for ln in out.splitlines()
                     if ln.startswith("PASS domain=")]
        check(len(pass_rows) == 5,
              "AC-BF2 per-domain rows: exactly five PASS domain= lines")
        check("R1676 cross-validation" in out,
              "AC-BF5 cross-validation annotation present in PASS rows")
        check(read_bytes(CHAINS) == before,
              "AC-BF1 --check is read-only: shipped chains bytes unchanged")

        # AC-BF5: determinism (double run, byte-identical stdout)
        code2, out2 = run_cli(CHAINS, "--check")
        check(code2 == 0 and out2 == out,
              "AC-BF5 determinism: double --check stdout byte-identical")

        # AC-BF3: drift injection (one domain's column signature altered)
        drifted = copy_chains(tmp)
        data = load_chain(drifted)
        tbl = sorted(data["domains"]["ledger"]["baseline"]["fingerprint"]
                     ["tables"])[0]
        sig = data["domains"]["ledger"]["baseline"]["fingerprint"]["tables"][tbl][0]
        sig[1] = str(sig[1]) + "_drifted"
        save_chain(drifted, data)
        code, out = run_cli(drifted, "--check")
        others = [ln for ln in out.splitlines() if ln.startswith("PASS domain=")]
        check(code == 2 and "FAIL domain=ledger" in out
              and "E_BASELINE_MISMATCH" in out and len(others) == 4,
              "AC-BF3 drift detection: exit 2 + ledger FAIL + other four "
              "domains still reported PASS")

        # AC-BF4a: --update heals the drifted copy, then --check goes clean
        code, out = run_cli(drifted, "--update")
        check(code == 0 and "post-check CLEAN domains=5" in out,
              "AC-BF4 --update on drifted copy: exit 0 + post-check CLEAN")
        code, out = run_cli(drifted, "--check")
        check(code == 0 and "verdict CLEAN domains=5" in out,
              "AC-BF4 re-freeze closes the loop: post-update --check exit 0")

        # AC-BF4b: --update on an undrifted copy is a byte-identical no-op
        undrifted = copy_chains(tmp)
        before = read_bytes(undrifted)
        code, out = run_cli(undrifted, "--update")
        check(code == 0 and "no-op" in out and read_bytes(undrifted) == before,
              "AC-BF4 undrifted --update: no-op verdict + zero byte drift")

        # AC-BF4c: --update refuses chains that carry steps
        stepped = copy_chains(tmp)
        data = load_chain(stepped)
        data["domains"]["ugc"]["steps"] = [
            {"version": 2, "name": "probe", "ops": [
                {"kind": "sql",
                 "sql": "CREATE TABLE t_probe (a INTEGER)"}]}]
        save_chain(stepped, data)
        before = read_bytes(stepped)
        code, out = run_cli(stepped, "--update")
        check(code == 2 and "E_REGEN_STEPS_PRESENT" in out
              and read_bytes(stepped) == before,
              "AC-BF4 steps-present refusal: exit 2 + zero disk mutation")

        # AC-BF2b: chain domain without constructor wiring fails closed
        ghost = copy_chains(tmp)
        data = load_chain(ghost)
        data["domains"]["ghost"] = {
            "baseline": {"fingerprint": {"tables": {}, "triggers": [],
                                         "views": [], "indexes": []}},
            "steps": []}
        save_chain(ghost, data)
        code, out = run_cli(ghost, "--check")
        check(code == 2 and "E_REGEN_NO_WIRING" in out
              and "FAIL domain=ghost" in out,
              "AC-BF2 self-assembled domain set: wiring gap FAILs "
              "fail-closed instead of silent skip")

        # AC-BF2c: malformed chain file propagates the structural refusal
        malformed = os.path.join(tmp, "malformed.json")
        with open(malformed, "w", encoding="utf-8") as handle:
            handle.write('{"domains": {"x": {"baseline": {}, "steps": []}}}')
        code, out = run_cli(malformed, "--check")
        check(code == 2 and "E_CHAIN_FORMAT" in out,
              "AC-BF2 malformed chain: read_chains refusal propagates "
              "exit 2 (E_CHAIN_FORMAT)")

        # AC-BF6: hygiene faces
        raw = read_bytes(CLI)
        check(all(b < 128 for b in raw),
              "AC-BF6 hygiene: fingerprint_regen.py source is pure ASCII")
        import_lines = [ln.strip() for ln in raw.decode("ascii").splitlines()
                        if re.match(r"^\s*(import|from)\s", ln)]
        check(not [ln for ln in import_lines
                   if re.search(r"\b(urllib|requests|socket|http)\b", ln)],
              "AC-BF6 hygiene: real import lines carry zero network libs")
        proc = subprocess.run(
            ["git", "status", "--short", "--"] + list(TRIO),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60, cwd=os.path.dirname(os.path.dirname(BASE)))
        check(proc.returncode == 0 and not (proc.stdout or "").strip(),
              "AC-BF6 hygiene: shipped trio (schema_migrate.py / "
              "migration_chains.json / test_schema_migrate.py) untouched")
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    print("SUITE PASS %d/%d" % (PASSES, PASSES + FAILS))
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
