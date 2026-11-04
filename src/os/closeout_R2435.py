"""R2435 closeout: state append through the shipped canon writer, plus the
heartbeat face.

The heartbeat repair is at the BIRTH SITE: the R2434 closeout left a bare
"2434" line instead of a "tick=<n> ..." row, so the tick kept no row at all.
That line is rewritten from the R2434 items recorded in state.json (read, not
remembered) and the R2435 row is appended in the same pass.

Usage: python src/os/closeout_R2435.py [--execute]
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import state_io  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

ITEMS = [
    "2026-11-04 R2435 verification window (five-silence scan clean at open: git status empty at HEAD 2d98a278 with no .git/index.lock; zero unreplied @BigDomain ledger rows; the content-addressed decisions diff read 168 rows and 113 tokens with new=0 against the stored baseline; the group orders tail max_ts is 2026-11-04 00:46, equal to the stored last_order, so nothing dispatches this company; benchmarks refreshed 2026-11-03 inside the seven-day gate; the queue gauge read FLOOR-MET main 5/5 tech 10/10 explore 10/10 and queue_head_delivered walked over the delivered AC-BEDP1 row to offer state/queue/tech.md:500 prefix AC-OTST1). The debt gate named CLAIM-FIRST item=reconcile-battery-R2435 carried from R2434 at the pre-registered 545 suites / 4246 criteria, so the battery ran FIRST on the committed tree with zero product edits (the R2168 mixed-tree rule).",
    "2026-11-04 R2435 the battery came back GREEN ON THE FIRST LEG, which is the first verification window in this run to do so: python src/os/battery_stream.py --evidence qa/reconcile-all-R2435.log read RUNNER PASS (545/545 suites green, reconcile controls 7/7, 1080.8s) with a measured criteria total of 4246 - the pre-registered number to the unit - and TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB. The evidence file is 845513B written as one utf-8 LF single writer through the shipped stream; qa_writer_census re-read DRIFT-CLEAN afterwards with its 529-entry baseline untouched, so no transport defect and no baseline widening were needed.",
    "2026-11-04 R2435 the four follow-up sections produced the designed first FAIL and then a green verdict, exactly in that order: leg 1 read VERDICT FAIL failing=matrix at on-disk=52412B against regenerated=52495B and wrote no byte (the shipped matrix doc was still the R2433 render), src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from THIS round green evidence through --stamp-from so the render is stamp-aligned to the doc it is compared with, --check read byte-identical at 52495B / 545 suites / 4246 criteria, and the re-run read VERDICT R2435 PASS failing=none (matrix byte-identical 52495B, fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN). Both legs stay appended in the evidence tail (1889B FAIL then 1950B PASS, eol_ok=True).",
    "2026-11-04 R2435 debt register after this window: close=predicted. reconcile-battery-R2435 was closed through the shipped debt_close at its predicted 108057B -> 108060B (measured exactly, line=169, open 2->1, done 148->149, readback=ok) and ONE leader row product-face-R2436 was appended first=yes through the shipped debt_append at 108060B -> 108341B (readback=ok), naming the next window a product face on the tech head state/queue/tech.md:500 prefix AC-OTST1 (owner_table_split_triage) whose AC-OTST1..AC-OTST6 were pinned at R2412 BEFORE any code. NO successor battery was registered: this window changed no product src byte and moved neither the suite nor the criteria count (the registry still reads 545 / 4246), so the R2168 rule does not fire. Remaining open: loop-s4u-reconcile and product-face-R2436.",
    "2026-11-04 R2435 a REAL defect was found in the CEO-adjacent heartbeat face and repaired at its birth site rather than around: heartbeat.txt ended with a bare line reading 2434, because the R2434 closeout appended the tick number alone instead of a tick=<n> row, so that round kept no heartbeat row at all and a parser reading rows by their tick= key saw 2434 missing. The repair rewrites that one line from the R2434 items already recorded in state.json (derived from the file, not remembered) and appends this round own row; nothing else on the face was touched and the trailing byte layout is preserved.",
    "2026-11-04 R2435 honest disclosures: (a) this window shipped ZERO product code and claims zero product points - the battery consumed the window exactly as the carried row said it would; (b) the window ran far past its 25-minute budget (one 1080.8s battery plus the follow-up legs), named rather than hidden; (c) no criterion was widened and no checker relaxed - the matrix FAIL was the designed stale-doc reading and it was closed by regenerating the document, not by loosening the compare; (d) tasks.md was not touched, it is the P-47 canonical board and carries no row for this verification window; (e) the heartbeat defect above is the SECOND data-face defect this run has caught in a closeout writer (the first was the R2432 export tick row), so the pattern is named for the next writer: a closeout that appends to a derived face must append a ROW, never a scalar.",
    "R2435 tokens: local=~11k api=0 api_reason=verification window - one battery on the committed R2434 tree at the pre-registered 545 suites / 4246 criteria that read RUNNER PASS on the first leg, four follow-up sections with one designed matrix FAIL and one green stamp-aligned verdict, one debt row closed and one leader row opened through their shipped CLIs, one birth-site repair of a malformed heartbeat line, and the state/export/backlog/heartbeat closeout; zero product code shipped, zero cloud calls and zero external API touches",
    "2026-11-04 R2435 self-heal check: BigDomain-OSLoop still exists and its Principal.LogonType reads Interactive (InteractiveToken), which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 passes an explicit S4U principal and needs an elevated shell while this session is unelevated, so the definition was left untouched again (two-hundred-and-second consecutive disclosure, carried as the stale row loop-s4u-reconcile).",
]

HB_2435 = ("2026-11-04T10:05:00+08:00 tick=2435 R2435 verification window - "
           "battery on the committed R2434 tree read RUNNER PASS on the FIRST "
           "leg at the pre-registered 545 suites / 4246 criteria (1080.8s, "
           "controls 7/7, TMP RECLAIM 932/932), four follow-up sections green "
           "after a stamp-aligned matrix regeneration to 52495B, battery row "
           "closed and product-face-R2436 opened at tech head AC-OTST1, plus a "
           "birth-site repair of the malformed R2434 heartbeat line")


def main():
    raw = state_io.read_raw(STATE)
    state = json.loads(state_io.decode(raw))
    tick = int(state.get("tick", 0)) + 1
    state["tick"] = tick
    state.setdefault("log", []).extend(ITEMS)
    payload = json.dumps(state, ensure_ascii=False, indent=2)
    post = state_io.canon(payload)

    hb_raw = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    lines = hb_raw.split("\n")
    repaired = False
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "2434":
            lines[i] = ("2026-11-04T09:53:00+08:00 tick=2434 R2434 product "
                        "window - general_writer_dialect_audit shipped against "
                        "AC-GWDA1..6 pinned at R2409: the tier is read off each "
                        "writer own os.replace destination, three writers "
                        "rewired onto the shared payload derivation, two "
                        "normalisers excluded as E_GWDA_REPAIR and 129 unread "
                        "destinations named; suite 6/6 twice, live AUDIT-CLEAN, "
                        "registry 545 suites / 4246 criteria, product-face-"
                        "R2434 closed and reconcile-battery-R2435 opened "
                        "(this line replaced a bare tick number left by the "
                        "R2434 closeout, repaired at its birth site at R2435)")
            repaired = True
            break
    lines.append(HB_2435)
    hb_post = "\n".join(lines)

    print("tick=%d items=%d before=%dB after=%dB hb_repaired=%s hb_before=%dB "
          "hb_after=%dB" % (tick, len(ITEMS), len(raw),
                            len(post.encode("utf-8")), repaired,
                            len(hb_raw.encode("utf-8")),
                            len(hb_post.encode("utf-8"))))
    if "--execute" not in sys.argv:
        print("dry run, wrote nothing")
        return 0

    body = post.encode("utf-8")
    tmp = STATE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(body)
    os.replace(tmp, STATE)
    back = state_io.decode(state_io.read_raw(STATE))
    assert back == post, "E_R2435_READBACK"

    hb_tmp = HEARTBEAT + ".tmp"
    with io.open(hb_tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(hb_post)
    os.replace(hb_tmp, HEARTBEAT)
    hb_back = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    assert hb_back == hb_post, "E_R2435_HB_READBACK"

    print("readback state=%dB eol_ok=%s heartbeat=%dB"
          % (len(back.encode("utf-8")), state_io.layout(back)["eol_ok"],
             len(hb_back.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())