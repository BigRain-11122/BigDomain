"""R2578 closeout: prepend the backlog done row and append the heartbeat line."""
import datetime
import io
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"

LINE = (
    "- [x] [done 2026-11-08 R2578] R2578 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2577, pre-registered 618 suites / 4684 criteria at R2577). Target re-measured by import "
    "BEFORE the launch: 618 suites / 4684 criteria / 618 unique names / 618 unique paths, byte for byte the registered "
    "number. GREEN ON THE FIRST LEG measured not quoted: qa/reconcile-all-R2577.log 1045040B at delivery and 1048942B "
    "after two identical follow-up blocks, utf-8 bom=False crlf=0 lone_cr=0 nul=0, 8038 lines, RUNNER PASS (618/618 "
    "suites green, reconcile controls 7/7, 1542.2s), ZERO FAIL suite rows, 618 unique suite names, and an independent "
    "recount over their criteria fields summing to EXACTLY 4684; launched detached through src/os/battery_stream.py "
    "with its stream and pid in separate files and never a shell redirection into qa/. FOLLOW-UP in the designed order: "
    "designed matrix FAIL first (on-disk 61209B vs regenerated 61204B, no byte written) with fingerprint CLEAN domains=5, "
    "profile byte-identical and census DRIFT-CLEAN, then stamp-aligned regeneration from THIS round own green evidence to "
    "61204B at 618/4684 with green honestly 618/618 self-describing, --check byte-identical at rc=0, and four sections "
    "PASS for VERDICT R2578 PASS failing=none (APPENDED 1951B eol_ok=True). DEBT: reconcile-battery-R2577 closed at its "
    "predicted and measured 182931B -> 182934B (line 326, open 32->31, done 277->278, readback ok) and "
    "product-face-R2578 opened first=yes 182934B -> 183511B naming tech line 613 prefix AC-PNMA1; NO successor battery "
    "owed (registry unmoved at 618/4684, no product byte). FOLD: state.json 80690B -> 71457B over log items 4..10 "
    "(complete R2568 and R2569 blocks) with tokens=7 ok=True, archive VERIFIED, FOLD-CLEAR margin 7043. EXPORT: 394415B "
    "at tick 2578, queue=CURRENT, check_export_consistency pass=21 fail=0 VERDICT PASS. HONEST: zero product points, "
    "nothing a CEO could open was built; I ran the follow-up write leg TWICE to capture its exit code, so the evidence "
    "carries two identical 1951B blocks rather than one (disclosed, neither edited by hand)."
)

HEARTBEAT = (
    " R2578 verification: the owed full battery on the committed tree went GREEN on the FIRST leg at the pre-registered "
    "618 suites / 4684 criteria (1542.2s, zero FAIL rows, 618 unique names, independent recount exactly 4684), the matrix "
    "doc was restamped from this round own green evidence to 61204B with --check byte-identical, and the four follow-up "
    "sections read PASS; debt: battery R2577 closed and product-face-R2578 opened first=yes naming tech line 613 "
    "AC-PNMA1; state folded 80690B -> 71457B (FOLD-CLEAR 7043)."
)


def main():
    bp = os.path.join(ROOT, "src", "os", "backlog.md")
    raw = io.open(bp, "rb").read().decode("utf-8")
    io.open(bp, "wb").write((LINE + "\n" + raw).encode("utf-8"))
    print("backlog %d -> %d bytes" % (len(raw.encode("utf-8")), len((LINE + "\n" + raw).encode("utf-8"))))

    hb = os.path.join(ROOT, "heartbeat.txt")
    h = io.open(hb, "rb").read().decode("utf-8")
    if not h.endswith("\n"):
        h += "\n"
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M+08:00")
    io.open(hb, "wb").write((h + now + HEARTBEAT + "\n").encode("utf-8"))
    print("heartbeat appended at %s" % now)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())