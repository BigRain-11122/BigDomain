"""R2550 closeout append: a verification window.

The shipped state_fold layout reader still refuses this file and state_fold.py
offers ONLY a --check face, so the append is a PROVED load+dump round-trip:
the bytes are read, decoded, re-encoded and compared byte for byte BEFORE any
mutation, and only then are the tick and the log rows written.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-08 R2550 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2549, pre-registered 604 suites / 4600 criteria). The "
    "battery itself was LAUNCHED BY THE PREVIOUS R2550 ATTEMPT, which died before "
    "closeout and left qa/reconcile-all-R2550.log untracked at 991607B; this window "
    "measured it rather than quoting it, did not re-run it, and landed it. MEASURED: "
    "green leg closing RUNNER PASS at 604/604 suites, reconcile controls 7/7, 1416.6s, "
    "zero FAIL suite rows, utf-8 bom=False crlf=0 lone_cr=0 nul=0, and an INDEPENDENT "
    "recount over the 604 PASS suite rows via its own criteria field summing to EXACTLY "
    "4600 with 7 PASS reconcile control rows. FOUR FOLLOW-UP SECTIONS in the designed "
    "order: dry run read SECTION matrix FAIL at on-disk 58526B against regenerated "
    "58521B with no byte written while fingerprint read CLEAN domains=5, profile read "
    "byte-identical and census read DRIFT-CLEAN; docs/sandbox-suite-matrix.md was then "
    "regenerated stamp-aligned from THIS round own green evidence through suite_matrix "
    "--stamp-from to 58521B at 604 suites / 4600 criteria with green=604/604 "
    "self-describing and --check read byte-identical at rc=0, after which all four PASS "
    "for VERDICT R2550 PASS failing=none (APPENDED 1950B eol_ok=True, file now "
    "993557B). DEBT: reconcile-battery-R2549 closed through the shipped debtor at its "
    "predicted and measured 170770B -> 170773B (line 287, open 21->20, done 248->249, "
    "readback ok); NO successor battery is owed because no product src byte moved and "
    "the registry is unmoved at 604 suites / 4600 criteria; product-face-R2550 appended "
    "first=yes (170773B -> 171254B, readback ok) naming the next window a PRODUCT face "
    "on the tech head state/queue/tech.md:587 prefix AC-PNDP1 "
    "probe_seam_name_binding_nested_arm_mixed_scope, criteria AC-PNDP1..AC-PNDP6 pinned "
    "in that row at R2549 BEFORE any code. FIVE-SILENCE at open: zero @BigDomain rows "
    "in cph4/evolution-ledger.md, the content-addressed decisions diff read new=0 over "
    "the stored 182-token baseline at a measured 46 file tokens / 42 rows, the group "
    "orders tail was unchanged at 2026-11-08 00:04, benchmarks 2026-11-03 inside the "
    "seven-day gate, and git status carried only this round own untracked battery log "
    "plus a stray root file literally named --help (13859B, written 05:35:33 by the "
    "interrupted window shell redirection) which this window DELETED as junk. "
    "queue_head named tech line 587 claimable=12 with the floor MET.",

    "2026-11-08 R2550 honest disclosures: (a) ZERO product points on the Executive "
    "Protocol scale - the battery is infrastructure and nothing a CEO could newly open "
    "or click was built; (b) the 1416.6s battery was run by the PRIOR interrupted "
    "window and this window only measured and landed its output, so the round consumed "
    "closeout time rather than battery time, which is disclosed rather than presented as "
    "a fresh run; (c) the round overshot its 25-minute budget on the follow-up pair and "
    "the measurement pass; (d) the matrix is byte-honest at 604/604 because this leg was "
    "fully green, unlike the R2549 regeneration whose green line read 603/604; (e) "
    "state.json reads 205706B against the 78500B waterline so the fold stays an owed "
    "obligation and the shipped tool still offers only a --check face; (f) the "
    "state_fold layout defect from R2522 is still open, so this append used a proved "
    "load+dump round-trip compared byte for byte before mutation; (g) five stale "
    "product-face rows (R2511/R2513/R2515/R2517/R2522) still overstate outstanding work "
    "and were disclosed rather than hand-closed; (h) Docker is absent, so nothing was "
    "containerised and no sandbox service was started; (i) the real 19.9 debit and the "
    "real msgSecCheck still wait on CEO physical items (merchant id, mini-program "
    "appid/secret); (j) tasks.md was not touched, it is the P-47 canonical board.",

    "R2550 tokens: local=~9k api=0 api_reason=verification window - one five-silence "
    "scan, one content-addressed decisions diff reading new=0, one debt gate read, one "
    "queue head read, one evidence encoding plus recount measurement, one four-section "
    "follow-up dry run, one stamp-aligned matrix regeneration and one byte check, one "
    "four-section follow-up landed with its verdict appended, one debt close and one "
    "debt append through their shipped writers, and the state/export/backlog/heartbeat "
    "closeout plus one junk file deletion; zero cloud calls and zero external API "
    "touches",
]


def main():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    replay = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    if replay.encode("utf-8") != raw:
        print("REFUSED E_APP_ROUNDTRIP: dump does not reproduce the file")
        return 3
    state["tick"] = 2550
    state["last_decision_rows"] = 42
    state["log"].extend(LINES)
    out = (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    tmp = STATE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(out)
    os.replace(tmp, STATE)
    back = open(STATE, "rb").read()
    print("APPENDED before=%dB after=%dB tick=%d log=%d readback=%s"
          % (len(raw), len(back), state["tick"], len(state["log"]),
             "ok" if back == out else "MISMATCH"))
    return 0


if __name__ == "__main__":
    sys.exit(main())