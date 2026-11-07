"""R2534 closeout: prepend the backlog row and stamp the heartbeat."""

import datetime
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))

ROW = (
    '- [x] [done 2026-11-07 R2534] R2534 VERIFICATION window on the battery the '
    'register owed (reconcile-battery-R2533, pre-registered 596 suites / 4552 '
    'criteria, re-measured by importing reconcile_all.SUITES and matched byte '
    'for byte) at a clean tree HEAD abac19ca with no index.lock and the debt '
    'gate reading CLAIM-FIRST. RESULT GREEN ON THE FIRST LEG, measured not '
    'quoted: qa/reconcile-all-R2533.log is 931140B as delivered and 933118B on '
    'disk after the follow-up block, utf-8 bom=False crlf=0 nul=0, closing '
    'RUNNER PASS (596/596 suites green, reconcile controls 7/7, 1196.3s), ZERO '
    'FAIL suite rows, and an independent recount over the 596 PASS rows summing '
    'to EXACTLY 4552 criteria; launched detached and unfiltered through '
    'src/os/battery_stream.py with its stream and its pid in SEPARATE files, '
    'because the R2532 window put the stream into the pid path and that mistake '
    'is now fixed at the launcher rather than only disclosed. FOUR FOLLOW-UP '
    'SECTIONS in the designed order: the dry run read matrix FAIL first by '
    'design at on-disk 57459B against regenerated 57453B with NO byte written '
    'while fingerprint read CLEAN domains=5, profile byte-identical and census '
    'DRIFT-CLEAN; docs/sandbox-suite-matrix.md was then regenerated '
    'stamp-aligned from THIS round own green evidence to 57453B at 596 suites / '
    '4552 criteria with green=596/596 self-describing and --check '
    'byte-identical; the re-run read all four PASS for VERDICT '
    'reconcile-all-R2533 PASS failing=none (APPENDED 1978B eol_ok=True). DEBT: '
    'reconcile-battery-R2533 closed through the shipped debtor at its predicted '
    '163107B -> 163110B (line 264, open 15->14, done 232->233, readback ok) and '
    'product-face-R2534 opened first=yes (163110B -> 163535B) naming the next '
    'window a PRODUCT face on tech line 571 prefix AC-PCNS1; NO successor '
    'battery is owed because no product src byte moved and the registry is '
    'unmoved at 596 / 4552, re-read by import. HONEST: zero product points and '
    'none claimed; the leg went green so no red leg exists to keep and no repair '
    'was needed, stated as this run fact and not as a general safety claim; the '
    'progress polls repeated the same shape three times before being replaced by '
    'a single blocking wait on the evidence file, disclosed because a repeated '
    'identical action is a cost even when it returns new numbers; Docker absent; '
    'the real 19.9 bill and the real msgSecCheck still wait on CEO physical '
    'items; the S4U lane reconcile still needs an ELEVATED shell; board, product '
    'faces and tasks.md untouched.')


def main():
    path = os.path.join(REPO, "src", "os", "backlog.md")
    text = io.open(path, encoding="utf-8", newline="").read()
    if ROW in text:
        print("already appended")
    else:
        eol = "\r\n" if "\r\n" in text else "\n"
        io.open(path, "w", encoding="utf-8", newline="").write(ROW + eol + text)
    head = io.open(path, encoding="utf-8", newline="").readline()
    print("backlog %s"
          % ("OK" if head.startswith("- [x] [done 2026-11-07 R2534]") else
             "FAIL"))
    beat = os.path.join(REPO, "heartbeat.txt")
    body = io.open(beat, encoding="utf-8", newline="").read()
    stamp = datetime.datetime.now().strftime("%H:%M")
    line = ("2026-11-07 %s R2534 verification window: battery green 596/596 at "
            "4552 criteria, four follow-up sections PASS\n" % stamp)
    if line not in body:
        if not body.endswith("\n"):
            body += "\n"
        io.open(beat, "w", encoding="utf-8", newline="").write(body + line)
    print("heartbeat OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())