# closeout_R2256.py - R2256 closeout: append the round log lines and
# advance the tick, preserving the file's existing layout byte for byte
# apart from the new items. Pure stdlib, pure ASCII source.
import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-10-29 R2256 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; the queue gauge read main "
    "5/5 tech 10/10 explore 10/10 FLOOR-MET with tech 11 open of which 1 "
    "gated and explore 10 open; decisions.md carries 289 non-empty rows and "
    "187 content-addressed D/C tokens against the stored 194-token superset "
    "baseline with ZERO additions - the seven apparent losses are the known "
    "group-side rotation and truncation artefacts (D-20261006-05, "
    "D-20261007-04, D-20261007-05, D-20261008-05, O-20261012-2330, "
    "O-20261026-0735, T-20261026-01..03) and the baseline stays a superset "
    "so a later-restored token cannot masquerade as a new decision - hence "
    "zero domain action; the group ledger carries the same three @BigDomain "
    "patrol rows already paid off, none numbered, so zero unreplied "
    "handoffs; the group orders tail is unchanged at the 2026-10-29 02:1x "
    "CEO-PROXY event round R2.48 already consumed in R2226; benchmarks "
    "refreshed 2026-10-29 inside the seven-day gate) - the P1 canonical rows "
    "stay blocked-on-CEO and the weekly proposal duty is met by BD-PROP-005, "
    "and the debt register named exactly one first=yes row "
    "(reconcile-battery-R2256, opened by R2255), so this window took the "
    "verification debt instead of opening a new product face: R2255 shipped "
    "src/os code and wired a new suite that no full battery had covered, and "
    "the R2168 mixed-tree rule forbids product edits inside a battery "
    "window. RESULT on the committed tree: full reconcile battery RUNNER "
    "PASS 432/432 suites green plus reconcile controls 7/7 in 852.6s with "
    "birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2256.log, 765306B at RUNNER close, single-writer "
    "utf-8 LF through src/os/battery_stream.py, never a shell redirection), "
    "expected criteria total=3570. Four post-battery sections then all PASS "
    "through the new single-writer helper src/os/battery_followup_R2256.py "
    "(same shape as R2254, only the evidence path and the round label "
    "changed): matrix regenerated to 432 suites / 3570 criteria and read "
    "back byte-identical (docs/sandbox-suite-matrix.md, 42046B, "
    "green=432/432), fingerprint chain CLEAN over 5 domains, runner profile "
    "--daily --check PASS byte-identical, writer census re-frozen then "
    "DRIFT-CLEAN files=2196 tee=1667 baselined=529 disappeared=0 flags=0, "
    "closing on VERDICT PASS. The measured deltas against R2254 (431 suites "
    "/ 3564 criteria) are +1 suite and +6 criteria, exactly the R2255 "
    "os-round-evidence suite joining the registry, so the newest slice is "
    "now covered by the whole battery and not only by its own suite plus "
    "neighbours. Honest score: zero product code changed and zero new "
    "apimarket face, so this is a 0-point verification window that only buys "
    "back the debt; the register row was closed and the successor "
    "product-face-R2257 opened as first=yes. state.json measures 63418B "
    "against the 78500B waterline (verdict FOLD-CLEAR), so no fold was due.",

    "R2256 tokens: local=~11k api=0 api_reason=verification window on the "
    "debt register first item - one streamed full battery with the "
    "birth-site tmp reclaim inside its own window, one new four-section "
    "follow-up helper, one register row closed with its successor opened, "
    "and the backlog/state/export closeout; zero cloud calls and zero "
    "external API touches; no product code changed (the R2168 mixed-tree "
    "rule)",

    "R2256 self-heal check: BigDomain-OSLoop exists and its State reads "
    "Running, but its principal still reads LogonType=Interactive (not "
    "S4U), which the 2026-09-29 machine law forbids for every lane task; "
    "src/os/register_loop_task.ps1 already passes an explicit S4U principal "
    "and needs an elevated shell to apply it, and this session runs "
    "unelevated, so the definition of the loop hosting this window was left "
    "untouched. Open local-lane item for an elevated window (twenty-fifth "
    "consecutive disclosure, registered as the stale row loop-s4u-reconcile "
    "in state/debt.md).",
]

TICK = 2256


def main():
    raw = open(PATH, "rb").read()
    text = raw.decode("utf-8-sig")
    crlf = "\r\n" in text
    nl = "\r\n" if crlf else "\n"
    antes = json.loads(text)
    if len(antes["log"]) == 0:
        print("E_CLOSE_EMPTY_LOG")
        return 3
    # locate the log array close: the last item line then the closing bracket
    marker = nl + "  ]"
    idx = text.rfind(marker)
    if idx < 0:
        print("E_CLOSE_NO_LOG_CLOSE")
        return 3
    prefix = text[:idx]
    suffix = text[idx:]
    item_indent = " " * 16
    chunk = ""
    for line in LINES:
        chunk += "," + nl + item_indent + json.dumps(line, ensure_ascii=False)
    new_text = prefix + chunk + suffix
    new_text = new_text.replace('"tick": %d' % antes["tick"],
                                '"tick": %d' % TICK, 1)
    despues = json.loads(new_text)
    if despues["tick"] != TICK:
        print("E_CLOSE_TICK")
        return 3
    if len(despues["log"]) != len(antes["log"]) + len(LINES):
        print("E_CLOSE_LOG_LEN")
        return 3
    if despues["log"][:-len(LINES)] != antes["log"]:
        print("E_CLOSE_LOG_PREFIX")
        return 3
    for key in antes:
        if key in ("tick", "log"):
            continue
        if despues[key] != antes[key]:
            print("E_CLOSE_KEY_MOVED %s" % key)
            return 3
    with io.open(PATH, "wb") as handle:
        handle.write(new_text.encode("utf-8"))
    print("CLOSEOUT OK tick=%d log=%d bytes=%d crlf=%s"
          % (TICK, len(despues["log"]),
             len(new_text.encode("utf-8")), crlf))
    return 0


if __name__ == "__main__":
    sys.exit(main())