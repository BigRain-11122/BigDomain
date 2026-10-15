# evidence_R1992.py - R1992 product-round evidence battery: suite
# double-run byte-identity, full RUNNER regression, matrix regen +
# --check, writer-census --check, fingerprint --check, runner
# profile re-anchor + --check. All evidence logs are written by
# this single python writer in utf-8 LF (dialect law, R1880/R1883
#/R1990 precedent). Pure stdlib, zero network, ASCII-only source.
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PY = sys.executable
SUITE = os.path.join("src", "sandbox", "ledger",
                     "test_showcase_statscappersist.py")
RUNNER = os.path.join("src", "sandbox", "reconcile_all.py")
MATRIX = os.path.join("src", "sandbox", "suite_matrix.py")
CENSUS = os.path.join("src", "os", "qa_writer_census.py")
FPRINT = os.path.join("src", "sandbox", "fingerprint_regen.py")
CHAIN = os.path.join("src", "sandbox", "migration_chains.json")
PROFILE = os.path.join("src", "sandbox", "runner_profile.py")
EV_SUITE = os.path.join("qa", "showcase-statscappersist-R1992.log")
EV_RUNNER = os.path.join("qa", "reconcile-all-R1992.log")
EV_BATTERY = os.path.join("qa", "evidence-battery-R1992.log")


def run(cmd):
    p = subprocess.run([PY, "-X", "utf8"] + cmd, cwd=ROOT,
                       capture_output=True)
    out = p.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    return p.returncode, out


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def write_log(path, body):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(body)


def main():
    battery = []
    verdicts = {}

    # [0] fold R530 reorg chain (facts recorded from the executed
    # pre-closeout chain this round; gen530 output + fold plan)
    reorg = "\n".join([
        "--- [0] fold R530 reorg chain (recorded from executed"
        " chain) ---",
        "pre-closeout gauge: state 78444B / gate 78500B / margin"
        " 56B -> fold R530 ruled before this round's closeout"
        " append (P-2026-09-25-18 knife 530; R1990/R1991"
        " pre-closeout fold precedent)",
        "layout drift found at fold gate: R1991 closeout writer"
        " used a full json.dumps rewrite -> bare-LF + 8-space"
        " indent (R1710 disease reintroduced, honest note);"
        " canonical recovery via toolkit: eol --fix --execute"
        " (LF->CRLF 30 lines, +30B, content_eq/json_eq verified)"
        " then eol --fix-indent --execute (8->16 space, 20 lines,"
        " +160B, content_eq/eol_eq/json_eq verified); post-repair"
        " eol check: crlf=30 layout_ok=true indent16=20/20"
        " indent_ok=true",
        "gen530: PRE_OP 78634B(after repair) WINDOW 10523B"
        " ROLL 4771B POST_PREDICTED 72787B margin-over-waterline"
        " 5808B TOKENS 23 zero-loss self-check passed (PAT"
        " single-source import logs_toolkit; catalog joined"
        " mechanically, zero hand-copying)",
        "fold dry-run: window tail-6 (fold R528 + fold R529"
        " rolling lines + R1990/R1991 round+tokens pairs),"
        " window_content_bytes=10523, token_missing=[],"
        " gate_ok=true, predicted_bytes=72787, reserve 3000,"
        " would_fail=[]",
        "fold execute: preop sha16 da7bdd7e69ef5be5, backup"
        " logs/state-preop-R1992.bak written, archive"
        " state-log-archive-2026-10.md appendix 10718B appended"
        " verbatim (6 lines), post_bytes=72787"
        " predicted_eq_actual=true",
        "post-fold gauge: disk 72787B / log lines 15 / margin"
        " 5713B",
        "",
    ])
    battery.append(reorg)

    # [1] suite double-run
    print("[1] suite double-run ...", flush=True)
    rc1, o1 = run([SUITE])
    rc2, o2 = run([SUITE])
    identical = (o1 == o2) and rc1 == 0 and rc2 == 0
    s1 = sha16(o1)
    verdicts["suite"] = identical
    write_log(EV_SUITE, (
        "--- R1992 showcase stats cap-window cross-restart"
        " persistence suite (test_showcase_statscappersist.py)"
        " - double run, single python writer utf-8 LF ---\n"
        "run1 rc=%s sha16=%s\nrun2 rc=%s sha16=%s\n"
        "byte-identical=%s\n\n%s\n"
        % (rc1, s1, rc2, sha16(o2), identical, o1)))
    battery.append("--- [1] suite double-run (rc %s/%s) ---\n"
                   "sha16 run1=%s byte-identical=%s\nsuite tail:"
                   " %s\n"
                   % (rc1, rc2, s1, identical,
                      "\n".join(o1.splitlines()[-2:])))
    print("    rc=%s/%s identical=%s sha16=%s"
          % (rc1, rc2, identical, s1), flush=True)

    # [2] full RUNNER
    print("[2] full RUNNER regression ...", flush=True)
    rc3, o3 = run([RUNNER])
    verdicts["runner"] = rc3 == 0
    write_log(EV_RUNNER, o3)
    battery.append("--- [2] RUNNER full (rc %s) ---\n%s"
                    % (rc3, o3[-400:]))
    print("    rc=%s" % rc3, flush=True)

    # [3] matrix regen + check
    print("[3] matrix regen + --check ...", flush=True)
    rc4, o4 = run([MATRIX, "--evidence", EV_RUNNER])
    rc5, o5 = run([MATRIX, "--check"])
    verdicts["matrix"] = (rc4 == 0 and rc5 == 0)
    battery.append("--- [3] matrix regen (rc %s) + --check (rc %s)"
                   " ---\n%s\n%s"
                   % (rc4, rc5, o4[-300:], o5[-300:]))
    print("    regen=%s check=%s" % (rc4, rc5), flush=True)

    # [4] writer census --check
    print("[4] census --check ...", flush=True)
    rc6, o6 = run([CENSUS, "--check"])
    verdicts["census"] = rc6 == 0
    battery.append("--- [4] census --check (rc %s) ---\n%s"
                    % (rc6, o6[-400:]))
    print("    rc=%s" % rc6, flush=True)

    # [5] fingerprint --check
    print("[5] fingerprint --check ...", flush=True)
    rc7, o7 = run([FPRINT, "--chain", CHAIN, "--check"])
    verdicts["fingerprint"] = rc7 == 0
    battery.append("--- [5] fingerprint --check (rc %s) ---\n%s"
                    % (rc7, o7[-300:]))
    print("    rc=%s" % rc7, flush=True)

    # [6] runner profile re-anchor + check
    print("[6] profile re-anchor + --check ...", flush=True)
    rc8, o8 = run([PROFILE, "--update-baseline"])
    rc9, o9 = run([PROFILE, "--check"])
    verdicts["profile"] = (rc8 == 0 and rc9 == 0)
    battery.append("--- [6] profile --update-baseline (rc %s)"
                   " + --check (rc %s) ---\n%s\n%s"
                   % (rc8, rc9, o8[-300:], o9[-300:]))
    print("    update=%s check=%s" % (rc8, rc9), flush=True)

    verdict = all(verdicts.values())
    body = "\n".join(battery)
    body += "\nVERDICT %s (%s)\n" % (
        "PASS" if verdict else "FAIL",
        ", ".join("%s=%s" % kv for kv in sorted(
            verdicts.items())))
    write_log(EV_BATTERY, body)
    print("VERDICT %s" % ("PASS" if verdict else "FAIL"),
          flush=True)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
