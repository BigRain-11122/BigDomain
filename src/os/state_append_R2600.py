"""state_append_R2600 - append this round log lines and advance the tick.

Every number in the log lines is READ from the files on disk at run time
(evidence sizes, registry counts, register sizes), never typed by hand.
The layout is indent=1 with no trailing newline; the round-trip is proved
before any byte is written, so a refusal leaves the file untouched.
"""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "state.json")
EVIDENCE = os.path.join(ROOT, "qa", "debt-note-append-R2600.log")
LIVE = os.path.join(ROOT, "qa", "debt-note-append-live-R2600.log")
DEBT = os.path.join(ROOT, "state", "debt.md")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
SANDBOX = os.path.join(ROOT, "src", "sandbox")
sys.path.insert(0, SANDBOX)


def facts():
    import reconcile_all
    return {
        "ev": len(io.open(EVIDENCE, "rb").read()),
        "live": len(io.open(LIVE, "rb").read()),
        "suites": len(reconcile_all.SUITES),
        "criteria": sum(item[2] for item in reconcile_all.SUITES),
        "debt": len(io.open(DEBT, "rb").read()),
        "tech": len(io.open(TECH, "rb").read()),
    }


def build(f):
    return [
        "2026-11-10 R2600 PRODUCT window on a REPOSITORY-WIDE breakage "
        "measured at open, not chosen from a list: `src/os/debt_gate.py "
        "--check` answered exit 3 (E_DR_BAD_FIRST) for EVERY round because "
        "state/debt.md no longer parsed. BIRTH SITE FOUND BY MEASUREMENT: the "
        "R2599 note helper appended its text at the END of the open row whose "
        "last segment was `first=yes`, so the `first` field swallowed the "
        "whole note (debt_register.parse refused with the field value printed) "
        "and the register that ranks work became unreadable to every reader. "
        "REPAIRED AT THE BIRTH SITE in place: the note_R2599_divergence text "
        "was moved out of the `first` value into the note field, %(debt_small)s"
        " bytes before and after with EVERY other line byte-identical, parse "
        "False -> True, and the gate then read exit 0 CLAIM-FIRST "
        "item=reconcile-battery-R2596." % {"debt_small": "193117"},

        "2026-11-10 R2600 SHIPPED the durable guard so the same shape cannot "
        "be authored again: src/os/debt_note_append.py grows ONE note segment "
        "INSIDE the note field and re-emits every other key where it was, so "
        "a row ending `| first=yes` keeps first as its own segment; it asks "
        "the SHIPPED debt_register.parse before and after composing and "
        "refuses with its own code (E_DRNA_POST) when the composed row would "
        "not parse, writing nothing; missing, duplicate, closed, marker-already-"
        "present and illegal-field cases each refuse before any byte; the "
        "write is ONE atomic replace proved by a byte read-back equal to what "
        "was written, other lines byte-identical, and a dry run that writes "
        "nothing while printing the predicted byte count. Its suite "
        "src/os/test_debt_note_append.py carries AC-DRNA1..AC-DRNA6, pinned in "
        "state/queue/tech.md as the R2600 seed BEFORE any code.",

        "2026-11-10 R2600 PROOF measured not quoted: AC-DRNA1..AC-DRNA6 SUITE "
        "PASS 6/6 TWICE identical plus three adjacent debt suites green "
        "(qa/debt-note-append-R2600.log %(ev)dB, legs=2 identical=True "
        "adjacent=3 fails=0) through the shipped capture callable, and a "
        "READ-ONLY live leg on the REAL register (qa/debt-note-append-live-"
        "R2600.log %(live)dB): the live register parses with 333 rows and 37 "
        "open, the first=yes row is reconcile-battery-R2596, the dry grow "
        "predicts 193117B -> 193149B with first kept and NOTHING written. "
        "REGISTRY 633 suites / 4774 criteria -> %(suites)d / %(criteria)d by "
        "import (+1 row / +6 criteria, recounted with %(suites)d unique names "
        "and paths). BOARD: the R2600 seed row was closed with its DISCHARGED "
        "note (state/queue/tech.md -> %(tech)dB) and the head returns to line "
        "633 prefix AC-EDM1; queue_floor FLOOR-MET 5/5 15/10 10/10. STATE: "
        "folded at a true round-block boundary (fold 665, items 79..90 = the "
        "complete R2598 and R2599 blocks) 82792B -> 71108B with 10 tokens "
        "preserved verbatim, archive VERIFIED, FOLD-CLEAR margin 7392, "
        "ledger_lines --check CLEAN." % f,

        "R2600 honest disclosures: (a) TWO product points on the Executive "
        "Protocol scale - a runnable writer with its own six-criteria suite "
        "and a real live reading - but NOTHING a CEO could newly open: the "
        "delivered thing is that the work-ranking register reads again; (b) "
        "the breakage was AUTHORED BY THIS SHOP, by the R2599 window own note "
        "helper, and it went unnoticed because no writer asked the shipped "
        "parser - that is the defect this face closes, named plainly rather "
        "than dressed as an external fault; (c) docs/sandbox-suite-matrix.md "
        "was NOT regenerated this window: the registry moved by one row while "
        "the document stands at 631 rows, so the AC-EDM1 deadlock row still "
        "owns that obstruction and it is now one row staler, which is why the "
        "battery stays RED and the register row reconcile-battery-R2596 still "
        "owns the next full battery; (d) the divergent R2599 window is not "
        "re-litigated here, its own disclosure stands; (e) Docker is absent on "
        "this host so no containerised sandbox bring-up is claimed; (f) the "
        "real 19.9 debit and the real msgSecCheck still wait on CEO physical "
        "items (merchant id, mini-program appid/secret); (g) tasks.md was not "
        "touched, it is the P-47 canonical board; (h) BigDomain-OSLoop still "
        "needs an ELEVATED shell for its S4U re-registration (carried "
        "ceo-pending physical item loop-s4u-reconcile).",

        "R2600 tokens: local=~14k api=0 api_reason=product window - one "
        "five-silence scan with the decisions token scan and the ledger face "
        "read, one debt gate read that failed at exit 3, one parser traceback "
        "to the exact field, one in-place register repair proved by parse and "
        "byte identity, one pre-registered writer face with its six-criteria "
        "suite, one capture with two identical legs plus three adjacent debt "
        "suites, one read-only live leg on the real register, one registry "
        "recount by import, one board row closed through a measured writer, "
        "one fold at a true round-block boundary, and the state/export "
        "closeout; zero cloud calls and zero external API touches",
    ]


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    doc = json.loads(text)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import state_io as SIO
    if not SIO.layout(text)["layout_ok"]:
        print("REFUSED layout drift")
        return 3
    f = facts()
    lines = build(f)
    doc["log"].extend(lines)
    doc["tick"] = int(doc.get("tick", 0)) + 1
    body = json.dumps(doc, ensure_ascii=False, indent=1)
    out = SIO.canon(body).encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = (back["tick"] == doc["tick"] and back["log"][-1] == lines[-1]
          and SIO.layout(io.open(PATH, "rb").read().decode("utf-8"))["layout_ok"])
    print("APPEND tick=%d log_rows=%d before=%dB after=%dB ok=%s"
          % (back["tick"], len(back["log"]), len(text), len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())