"""R2468 closeout: backlog row and heartbeat row (one-off, idempotent)."""
import io
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
BEAT = os.path.join(ROOT, "heartbeat.txt")

ROW = (
    "- [x] [done 2026-11-05 R2468] R2468 VERIFICATION window on the debt the "
    "R2467 business window left behind (reconcile-battery-R2467, pre-registered "
    "at 561 suites / 4342 criteria): zero product code changed, the R2168 "
    "mixed-tree rule honoured. Five-silence scan at open was clean at HEAD "
    "660d794d, and the content-addressed decisions diff named five new tokens "
    "D-20261105-12..16, ALL judged KNOWLEDGE-ONLY (group mtime patrol, group "
    "task-health table, group merge-driver ruling, bm-m lane handover, biggame "
    "NO-REPO verdict) with the baseline widened by exactly those five. The "
    "battery ran FIRST on the committed tree and read RUNNER PASS on the FIRST "
    "leg - 561/561 suites green, controls 7/7, 1205.5s, criteria total 4342 "
    "EXACTLY as pre-registered (qa/reconcile-all-R2468.log, 859447B, one utf-8 "
    "LF single writer through the shipped stream, crlf=0 lone_cr=0 bom=False), "
    "TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0. Four follow-up "
    "sections produced the designed order: dry-run read VERDICT FAIL "
    "failing=matrix at on-disk=54146B against regenerated=54116B with no byte "
    "written, suite_matrix regenerated docs/sandbox-suite-matrix.md from this "
    "round own green evidence through --evidence plus --stamp-from, --check "
    "read byte-identical at 54116B / 561 suites / 4342 criteria, and the write "
    "leg read VERDICT R2468 PASS failing=none (fingerprint CLEAN 5 domains, "
    "profile byte-identical, census DRIFT-CLEAN, APPENDED 1950B eol_ok=True). "
    "Debt: reconcile-battery-R2467 closed through the shipped debt_close at its "
    "predicted 121381B -> 121385B (line=198, open 3->2, done 176->177, readback "
    "ok); NO successor battery was registered because this window changed no "
    "product src byte and the registry is unmoved at 561/4342. Zero product "
    "points claimed; disclosed that the --help probe on reconcile_all.py "
    "started a real suite run and left a 5-byte file named '--help' in the repo "
    "root (deleted before any commit, tree read clean), that the window ran far "
    "past its 25-minute budget (one 1207.5s battery plus two follow-up legs), "
    "that Docker is absent so the compose bring-up of the sandbox faces stays "
    "unproved, that the real msgSecCheck and the real 19.9 debit still wait on "
    "CEO physical items, and that tasks.md was not touched as it is the P-47 "
    "canonical board. Gate now reads CLAIM-FIRST product-face-R2456 carried=13 "
    "stale, so the next window should ship a BUSINESS face and name the "
    "supersession rather than serving the gate blindly."
)

BEAT_LINE = (
    "R2468 verification window | 2026-11-05 | battery green 561/561 at the "
    "pre-registered 4342 criteria on the first leg, four follow-up sections to "
    "VERDICT R2468 PASS, matrix restamped 54116B byte-identical | "
    "reconcile-battery-R2467 CLOSED, no successor owed | five group decisions "
    "judged knowledge-only | zero product points | fold not due 74673B"
)


def main():
    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "R2468 VERIFICATION window" not in text:
        newline = "\r\n" if "\r\n" in text else "\n"
        text = ROW + newline + text
        tmp = BACKLOG + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp, BACKLOG)
        print("backlog row prepended")
    else:
        print("backlog row already present")

    with io.open(BEAT, "r", encoding="utf-8", newline="") as handle:
        beat = handle.read()
    if BEAT_LINE not in beat:
        newline = "\r\n" if "\r\n" in beat else "\n"
        if not beat.endswith(("\n", "\r")):
            beat += newline
        beat += BEAT_LINE + newline
        tmp = BEAT + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
            handle.write(beat)
        os.replace(tmp, BEAT)
        print("heartbeat row appended")
    else:
        print("heartbeat row already present")


if __name__ == "__main__":
    main()