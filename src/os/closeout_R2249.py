# closeout_R2249.py - append this window's three closeout lines to
# state.json by surgical insertion, preserving the canonical layout
# exactly (no BOM, CRLF, log items at the 16-space canon). Nothing is
# re-serialised, so no unrelated byte can move.
import io
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")
HEART = os.path.join(ROOT, "heartbeat.txt")
INDENT = " " * 16

NARRATIVE = (
    "2026-10-29 R2249 (five-silence scan clean at open: decisions.md carries "
    "283 non-empty rows and 190 content-addressed D/C tokens with ZERO "
    "additions against the stored 190-token baseline - the only two "
    "unbaselined tokens in the file are O-20261012-23 and O-20261026-07, "
    "order numbers quoted inside existing D- rows rather than decisions, and "
    "the baseline is deliberately kept a superset so a later-restored token "
    "cannot masquerade as new; the group ledger carries the same three "
    "@BigDomain patrol rows already paid off, none numbered, so zero unreplied "
    "handoffs; the group orders tail is unchanged at the 2026-10-29 02:1x "
    "CEO-PROXY event round R2.48 already consumed in R2226; benchmarks "
    "refreshed 2026-10-29 inside the seven-day gate; tree clean, no "
    "index.lock) - the P1 canonical rows stay blocked-on-CEO, the weekly "
    "proposal duty is met by BD-PROP-005, and the queue gauge read "
    "main=5/5 tech=10/10 explore=10/10 verdict=FLOOR-MET at open, so this "
    "window took the first item the register named instead of opening a new "
    "product face. VERIFICATION RESULT on the committed R2248 tree (commit "
    "c6784fca, the R2168 mixed-tree rule: no product code changes inside the "
    "battery window): full reconcile battery RUNNER PASS 428/428 suites green "
    "plus reconcile controls 7/7 in 1165.7s with birth-site TMP RECLAIM "
    "932/932 worlds, 326.57 MiB, busy=0 failed=0 (qa/reconcile-all-R2249.log, "
    "763410B at RUNNER close, single-writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection). The four "
    "post-battery sections then all PASS through the new single-writer helper "
    "src/os/battery_followup_R2249.py (same shape as R2247, only the evidence "
    "path and label changed): matrix regenerated and read back byte-identical "
    "at 428 suites / 3546 criteria (docs/sandbox-suite-matrix.md, 41753B, "
    "green=428/428), fingerprint chain CLEAN over 5 domains, runner profile "
    "--daily --check PASS, writer census re-frozen then DRIFT-CLEAN files=2181 "
    "tee=1652 baselined=529 disappeared=0 flags=0, closing on VERDICT PASS. "
    "DELTAS measured against the R2247 battery, not assumed: suites 427 -> 428 "
    "and criteria 3538 -> 3546 are exactly the R2248 os-debt-register suite "
    "joining the registry with its eight criteria, so the register the last "
    "window shipped is now covered by the whole battery rather than only by "
    "its own suite plus neighbours. State fold measured, not assumed: "
    "state.json sits at 37423B against the 78500B waterline, so no fold is due. "
    "Register closed honestly: state/debt.md row reconcile-battery-and-matrix "
    "closed at R2249, leaving open=1 (loop-s4u-reconcile, which still needs an "
    "elevated shell). Honest score: zero product code changed and zero new "
    "apimarket face, so this is a 0-point verification window that only buys "
    "back the debt - the next window opens on the product face (canonical P1 "
    "rows remain blocked-on-CEO, queues carry ten claimable rows each)."
)

TOKENS = (
    "R2249 tokens: local=~20k api=0 api_reason=verification window on the "
    "carried first item - one streamed full battery, one new four-section "
    "follow-up helper, one register row closed, and the state/export/backlog "
    "closeout; zero cloud calls and zero external API touches; no product code "
    "changed (the R2168 mixed-tree rule)"
)

SELF_HEAL = (
    "R2249 self-heal check: BigDomain-OSLoop exists and is Running, but its "
    "principal still reads LogonType=InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "already passes an explicit S4U principal and needs an elevated shell to "
    "apply it; this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (nineteenth consecutive disclosure, registered as the "
    "stale row loop-s4u-reconcile in state/debt.md)."
)


def main():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    state = json.loads(raw)
    old_tick = state["tick"]
    old_len = len(state["log"])

    anchor = "\r\n  ]\r\n}\r\n"
    if not raw.endswith(anchor):
        print("UNEXPECTED TAIL - refusing to write")
        return 2
    head = raw[:-len(anchor)]
    tick_old = '"tick": %d,' % old_tick
    if head.count(tick_old) != 1:
        print("TICK ANCHOR NOT UNIQUE - refusing to write")
        return 2
    head = head.replace(tick_old, '"tick": %d,' % (old_tick + 1), 1)
    items = "".join(",\r\n%s%s" % (INDENT, json.dumps(text, ensure_ascii=False))
                    for text in (NARRATIVE, TOKENS, SELF_HEAL))
    out = head + items + anchor
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(out)

    check = json.loads(io.open(STATE, "r", encoding="utf-8").read())
    assert check["tick"] == old_tick + 1
    assert check["log"][-3:] == [NARRATIVE, TOKENS, SELF_HEAL]
    assert len(check["log"]) == old_len + 3
    for key in check:
        if key not in ("tick", "log"):
            assert check[key] == state[key], key
    text = io.open(STATE, "r", encoding="utf-8", newline="").read()
    assert text.count("\r\n") > 0 and text.count("\n") == text.count("\r\n")
    print("STATE tick %d -> %d log=%d -> %d bytes=%d crlf_only=True"
          % (old_tick, check["tick"], old_len, len(check["log"]),
             os.path.getsize(STATE)))

    line = ("%d tick 2026-10-29 R2249 verification window: reconcile battery "
            "PASS 428/428 green + controls 7/7 in 1165.7s, tmp reclaim 932/932 "
            "worlds 326.57 MiB, matrix 428 suites / 3546 criteria "
            "byte-identical, fingerprint CLEAN, profile PASS, census "
            "DRIFT-CLEAN files=2181; register row closed\n" % check["tick"])
    with io.open(HEART, "a", encoding="utf-8", newline="") as handle:
        handle.write(line.replace("\n", "\r\n"))
    print("HEARTBEAT %d" % check["tick"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())