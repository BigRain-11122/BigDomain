"""R2391 closeout: state tick, the log block, the export face, backlog row and
heartbeat. One writer per file, each with a read-back. ASCII source; Chinese
stays in the data files it already lives in.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

TS = "2026-11-02T21:40:00+08:00"

WINDOW = (
    "R2391 product window (five-silence scan clean at open: empty git status at "
    "HEAD 434807d9, no .git/index.lock; LEDGER atbd_lines=0 unreplied_groups=0; "
    "DEC rows=131 tokens=86 new=0; the group orders tail still the 2026-11-02 "
    "11:04 model-policy baseline already acknowledged as non-execution; "
    "benchmarks refreshed 2026-11-02 inside the seven-day gate; floor "
    "FLOOR-MET main 5/5 tech 10/10 explore 10/10). The debt gate was DEAD at "
    "open and that was this window first finding - see the repair line. "
    "PRODUCT: claimed state/queue/tech.md:447 prefix AC-EPWI1 "
    "(export_publish_wire_identity), criteria pinned in that row at R2384 "
    "BEFORE any code, anchors re-checked at HEAD. SHIPPED "
    "src/os/export_publish_wire_identity.py plus its suite: R2384 named every "
    "script on the CURRENT publishing path that writes the export itself and "
    "read any `.publish(..., EXPORT, ...)` as the proven route, but never asked "
    "WHICH module the callee resolves to, so a script could hand the export to "
    "another publisher and still read CLEAN while never touching the wire that "
    "proves the bytes. One reading now resolves the callee through the file own "
    "import lines into WIRE / FOREIGN (both named) / UNRESOLVED (the import and "
    "the call disagree) / NO-PUBLISH, with the routed-publish test itself asked "
    "of export_publish_path_guard at call time so there is no second publish "
    "law; string and comment spans are tokenised away first, because a publish "
    "spelling inside prose or a fixture literal is not a call. SUITE 9 "
    "assertions green twice with an identical criterion digest 0010BFA86E461093 "
    "plus two adjacent suites green (qa/export-publish-wire-identity-R2391.log, "
    "legs=2 identical=True adjacent=2 fails=0), wired "
    "os-export-publish-wire-identity(6). LIVE, not a plan: "
    "qa/export-publish-wire-identity-live-R2391.log reads src/os as "
    "verdict=WIRE code=0 scanned=1046 publishers=11 wire=11 foreign=(none) "
    "unresolved=(none) no_publish=11, a foreign fixture as verdict=FOREIGN "
    "code=2 naming module=some_other_module, and the module digest unchanged "
    "before and after. Board: row 447 stamped done and one REAL measured gap "
    "row seeded (export_publish_from_import_law, AC-EPBW1..AC-EPBW6 "
    "pre-registered in that row, five anchors zero-occupancy at HEAD).")

REPAIR = (
    "R2391 register repair, measured not guessed: state/debt.md line 160 "
    "carried a free-prose note that began with a column-0 `- [ ]`, which the "
    "register row law counts as a ROW - and it carried no pipe keys at all - so "
    "debt_register refused the whole file with E_DR_BAD_KEY and debt_gate had "
    "answered E_DGT_BAD_KEY instead of CLAIM-FIRST since R2390 closeout, i.e. "
    "the gate that is supposed to name the carried item could not name "
    "anything. Repaired at the birth site rather than by loosening the reader: "
    "the row now reads opened=R2390 | item=fold-due-R2391 | first=no | note=... "
    "(85843B -> 85855B) and the register re-reads open=4 done=115 "
    "first=reconcile-battery-R2387 stale=3 verdict=DEBT-STALE with the gate "
    "answering CLAIM-FIRST item=reconcile-battery-R2387 carried=4. The carried "
    "battery was NOT run this window: the product-first law took the face, and "
    "the row stays OPEN with its measured successor target (this window adds "
    "one suite of six criteria on top of the R2390 tree).")

DISCLOSE = (
    "R2391 honest disclosures: (a) two of this window own suite legs were RED "
    "on their first run and both reds were this window own fixtures, never the "
    "module: AC-EPWI1b asserted an empty call list for an off-path fixture that "
    "legitimately carries one routed publish, and AC-EPWI2b used a "
    "`from wire import publish` + bare `publish(...)` fixture, which the "
    "guard's `.publish(` law does not accept as a routed publish at all - the "
    "leg was rewritten to the plain-import attribute form, the substance was "
    "not widened, and the bare form is now the SEEDED GAP "
    "(export_publish_from_import_law) instead of a quiet hole. (b) The live "
    "reading was RED against the real tree before the token mask went in: "
    "closeout_R2384.py line 86 spells `.publish(..., EXPORT, ...)` inside a "
    "docstring paragraph and line 287 inside an embedded fixture script, and "
    "both read UNRESOLVED - the honest reading was that prose is not a call, so "
    "code_only() blanks STRING and COMMENT token spans before the scan with line "
    "numbers preserved, and a new suite leg pins it (AC-EPWI3b). (c) The "
    "reading is line based: a callee reached through a dict lookup, a getattr or "
    "a call chain reads UNRESOLVED rather than being called clean, stated in the "
    "module. (d) No battery ran this window, so the register row "
    "reconcile-battery-R2387 stays OPEN and nothing is claimed about the whole "
    "registry. (e) tasks.md was left untouched: it is the P-47 canonical board "
    "and carries no row for this tech slice. (f) The window ran past its "
    "25-minute budget, stated plainly; the product face was shipped rather than "
    "deferred because the tree was clean at open.")

SELF_HEAL = (
    "R2391 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal but needs an elevated shell, and this session is unelevated, "
    "so the task definition was left untouched "
    "(hundred-and-forty-sixth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).")

TOKENS = (
    "R2391 tokens: local=~22k api=0 api_reason=product-plus-repair window - one "
    "callee-resolution module and its six-criteria suite written to criteria "
    "pinned seven rounds earlier, one token mask added after the live tree "
    "proved prose was being read as code, one registry wiring line, one two-leg "
    "evidence capture with two adjacent suites, one three-step live capture "
    "through a single utf-8 LF writer, one board stamp and one measured gap row "
    "seeded, one dead-register repair that brings the debt gate back to life, "
    "and the state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches")

BACKLOG = (
    "- [x] R2391 [done 2026-11-02] export_publish_wire_identity - "
    "state/queue/tech.md:447 AC-EPWI1..AC-EPWI6 delivered: the R2384 guard read "
    "any `.publish(..., EXPORT, ...)` as the proven route without asking which "
    "module the callee resolves to, so a script could hand the export to another "
    "publisher and still read CLEAN. One reading resolves each routed publish "
    "through the file own import lines into WIRE / FOREIGN / UNRESOLVED / "
    "NO-PUBLISH, asks the guard for the routed-publish law at call time, and "
    "blanks string and comment spans first so prose is not a call; live, src/os "
    "reads WIRE over 11 publishers and a foreign fixture reads FOREIGN naming "
    "its module. One measured gap seeded (export_publish_from_import_law). The "
    "window also repaired a dead register row that had disabled the debt gate "
    "since R2390 closeout (E_DR_BAD_KEY); no battery ran, so the carried row "
    "stays open.\n"
)


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_atomic(path, text):
    tmp = path + ".part"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(tmp, path)


def main():
    state = read_json(P_STATE)
    if not any(str(item).startswith("R2391 product window")
               for item in state.get("log", [])):
        state["tick"] = 2391
        state.setdefault("log", [])
        state["log"].extend([WINDOW, REPAIR, DISCLOSE, SELF_HEAL, TOKENS])
        write_atomic(P_STATE,
                     json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    back = read_json(P_STATE)
    if back.get("tick") != 2391 or len(back["log"]) != len(state["log"]):
        print("REFUSE state read-back moved")
        return 1

    export = read_json(P_EXPORT)
    export["export_ts"] = TS
    export["do"] = WINDOW
    face = export.get("ceo_face") or {}
    face["current"] = (
        "R2391: a script can no longer look routed while publishing through some "
        "other module - every publish on the current export path is resolved to "
        "the module it really calls, and prose is no longer read as a call.")
    face["latest_artifact"] = (
        "src/os/export_publish_wire_identity.py plus its six-criteria suite "
        "(qa/export-publish-wire-identity-R2391.log, "
        "qa/export-publish-wire-identity-live-R2391.log)")
    face["last_artifact"] = face.get("latest_artifact")
    face["updated_at"] = TS
    face["next_milestone"] = (
        "export_publish_from_import_law: the one publish law learns the "
        "from-import binding, so a bare imported publish() call is read instead "
        "of silently counting as no publish at all")
    face["next_milestone_due"] = "2026-11-03"
    export["ceo_face"] = face
    outs = export.get("outs") or []
    if face["latest_artifact"] not in outs:
        outs.insert(0, face["latest_artifact"])
    export["outs"] = outs[:12]
    results = export.get("results") or []
    if not any(row[:2] == ["2391", WINDOW] for row in results if row):
        results.insert(0, ["2391", WINDOW])
    export["results"] = results[:12]
    label = "OSLoop \u6267\u884c tick"
    for row in export["results"]:
        if isinstance(row, list) and len(row) >= 2 and row[1] == label:
            row[0] = str(back.get("tick"))
    write_atomic(P_EXPORT, json.dumps(export, ensure_ascii=False, indent=2) + "\n")
    face_back = read_json(P_EXPORT).get("ceo_face", {})
    if face_back.get("latest_artifact") != face["latest_artifact"]:
        print("REFUSE export read-back moved")
        return 1

    backlog = read_text(P_BACKLOG)
    if "R2391 [done 2026-11-02]" not in backlog:
        write_atomic(P_BACKLOG, BACKLOG + backlog)

    write_atomic(P_HEART, TS + " R2391 export_publish_wire_identity shipped; "
                          "live src/os reads WIRE over 11 publishers; dead "
                          "register row repaired; battery carried OPEN\n")

    with io.open(P_STATE, "rb") as handle:
        state_bytes = len(handle.read())
    with io.open(P_EXPORT, "rb") as handle:
        export_bytes = len(handle.read())
    print("CLOSEOUT R2391 state=%dB export=%dB log=%d"
          % (state_bytes, export_bytes, len(back["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())