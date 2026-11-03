# closeout_R2409.py - the R2409 closeout: tick, log items, the CEO-visible
# export face and the heartbeat, proved by read-back.
# Stdlib only, ASCII source, zero network, no clock in the reading (the stamps
# are the caller's own strings, passed in, so this file never guesses a time).

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

STAMP = "2026-11-03T09:20:00+08:00"

ITEMS = [
    "2026-11-03 R2409 product window (five-silence scan clean at open: empty "
    "git status at HEAD f76f3f74, no .git/index.lock; LEDGER @BigDomain "
    "addressed rows=0 unreplied=0; DEC rows=148 tokens=97 new=0 against the "
    "stored baseline; the local orders table tail is the 2026-10-26 batch "
    "already acknowledged and the group orders tail is the 2026-11-02 "
    "voicebank/CPU work, neither of which dispatches this company; benchmarks "
    "refreshed 2026-11-02 inside the seven-day gate; floor FLOOR-MET main 5/5 "
    "tech 10/10 explore 10/10). The debt gate named product-face-R2409 and "
    "R2408 had already run the battery green on this tree, so the "
    "product-first law took the window. PRODUCT: claimed state/queue/tech.md:479 "
    "prefix AC-LDWS1 (library_declaration_dialect_sweep), whose AC-LDWS1.."
    "AC-LDWS6 were pinned INSIDE that row at R2406 BEFORE any code, after a "
    "fresh anchor check at HEAD (all five anchors hit only prose and state "
    "files - zero executable occupancy).",

    "2026-11-03 R2409 product face, what shipped: SHIPPED "
    "src/os/library_declaration_dialect_sweep.py plus its six-criteria suite. "
    "The reading is derived from the SOURCE by AST, not by a whitelist: a "
    "DECLARATION writer really CALLS json.dumps and os.replace, works in place "
    "beside its target (the house TEMP_SUFFIX idiom) and names the JSON "
    "declaration it lands; a GENERAL module composes and replaces something "
    "else and is reported without being debt; a per-round one-off script is "
    "HISTORICAL by its round suffix. WIRED: gate_decl_append, gate_decl_retire, "
    "orphan_promotion_ledger and retire_accept now derive the bytes they land "
    "from declaration_writer_dialect_preservation.encode asked at CALL time, so "
    "an LF declaration keeps exactly today's bytes and a CRLF declaration keeps "
    "its transport instead of being converted by whichever writer ran.",

    "2026-11-03 R2409 evidence and board: SUITE PASS 6/6 twice with an "
    "identical criterion digest plus four adjacent suites green "
    "(qa/library-declaration-dialect-sweep-R2409.log, 1394B, legs=2 "
    "identical=True adjacent=4 fails=0), wired "
    "os-library-declaration-dialect-sweep(6) so the registry reads 532 suites "
    "/ 4174 criteria. LIVE, not a plan: "
    "qa/library-declaration-dialect-sweep-live-R2409.log reads the REAL tree as "
    "scanned=1012 declaration=5 routed=5 general=16 historical=143 "
    "verdict=SWEEP-CLEAN, and a CRLF COPY of the real one-entry gates "
    "declaration keeps CRLF through a real append (entries 1->2, lone_lf=0, "
    "lone_cr=0, read_back=True) with the module digest 26dcc58a93be8e0a "
    "unchanged. Tech row 479 stamped [done 2026-11-03 R2409] and one REAL "
    "measured gap row seeded (general_writer_dialect_audit, AC-GWDA1.."
    "AC-GWDA6 pre-registered in that row) so the floor reads FLOOR-MET.",

    "2026-11-03 R2409 honest disclosures: (a) the seed row said FIVE library "
    "writers and named retire_apply, but measured this window retire_apply "
    "only READS src/os/state.json and its one os.replace moves a quarantine "
    "file, so it is GENERAL and is not a writer of a declaration; the fifth "
    "routed writer is the R2406 re-render residue_triage_repin, which asks "
    "repin_dialect_preservation - a seam that itself asks the shared law. (b) "
    "The first version of the sweep read string constants as behaviour and "
    "classified ITSELF as a declaration writer because its own text names "
    "os.replace and TEMP_SUFFIX; it was replaced by an AST reading of real "
    "calls and real imports before any evidence was captured, and that "
    "self-match is named rather than silently fixed. (c) retire_accept's "
    "existing AC-RAC6 pins the module's TOP-LEVEL import set, so the shared law "
    "is imported inside payload_bytes, the same call-time idiom R2406 used. (d) "
    "The ADJACENT retire_accept suite went RED on that criterion when the "
    "import moved to module level, and the repair was the import placement, "
    "never the criterion. (e) NO battery ran this window: 532 suites / 4174 "
    "criteria is a WIRING count (531/4162 from R2406 plus this window +1 suite "
    "/ +6 criteria) and reconcile-battery-R2409 is OPEN with that target. (f) "
    "tasks.md was left untouched: it is the P-47 canonical board and carries no "
    "row for this tech slice.",

    "2026-11-03 R2409 self-heal check: BigDomain-OSLoop is still registered "
    "with LogonType=InteractiveToken, which the 2026-09-29 machine law forbids "
    "for every lane task; src/os/register_loop_task.ps1 passes an explicit S4U "
    "principal but needs an elevated shell and this session is unelevated, so "
    "the task definition was left untouched (hundred-and-sixty-fourth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).",

    "R2409 tokens: local=~26k api=0 api_reason=product window - one "
    "source-derived sweep and its six-criteria suite written to criteria pinned "
    "three rounds earlier, four library writers rerouted through the shared "
    "payload derivation at one call site each, one AST reading that replaced a "
    "self-matching string scan, one registry wiring line, one two-leg evidence "
    "capture with four adjacent suites, one read-only live capture over the real "
    "tree with a CRLF copy proving the transport on a real append, one board "
    "stamp with one measured gap row seeded, the debt row closed and the "
    "successor battery opened through the shipped CLIs, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]


class CloseoutError(Exception):
    pass


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_bytes(path, data):
    temp = path + ".r2409.tmp"
    with io.open(temp, "wb") as handle:
        handle.write(data)
    os.replace(temp, path)
    with io.open(path, "rb") as handle:
        back = handle.read()
    if back != data:
        raise CloseoutError("read-back disagrees for %s" % path)


def close_state():
    text = read_text(STATE)
    if "\r\n" not in text:
        raise CloseoutError("state.json is not CRLF")
    old_tick = '"tick": 2408,'
    if text.count(old_tick) != 1:
        raise CloseoutError("tick 2408 not found exactly once")
    text = text.replace(old_tick, '"tick": 2409,')
    marker = '"<CR>\r\n  ]\r\n}'
    marker = '"' + "\r\n  ]\r\n}"
    if text.count(marker) != 1:
        raise CloseoutError("log tail not found exactly once")
    pad = " " * 16
    block = ",".join("\r\n" + pad + json.dumps(item, ensure_ascii=True)
                     for item in ITEMS)
    # the marker carries the LAST item's closing quote; it must be put back
    text = text.replace(marker, '"' + "," + block + "\r\n  ]\r\n}")
    payload = json.loads(text)
    if payload["tick"] != 2409 or len(payload["log"]) < len(ITEMS) + 1:
        raise CloseoutError("state payload did not move as planned")
    write_bytes(STATE, text.encode("utf-8"))
    return len(text.encode("utf-8"))


def close_export():
    text = read_text(EXPORT)
    payload = json.loads(text)
    face = payload.get("ceo_face", {})
    current = ("R2409 product: the library declaration dialect sweep shipped "
               "with all five declaration writers routed and the real tree "
               "reading SWEEP-CLEAN")
    latest = ("qa/library-declaration-dialect-sweep-R2409.log + "
              "qa/library-declaration-dialect-sweep-live-R2409.log + "
              "src/os/library_declaration_dialect_sweep.py")
    payload["export_ts"] = STAMP
    payload["do"] = current
    face["current"] = current
    face["latest_artifact"] = latest
    face["last_artifact"] = latest
    face["next_milestone"] = ("battery on the committed R2409 tree at 532 "
                              "suites / 4174 criteria (debt row "
                              "reconcile-battery-R2409)")
    face["next_milestone_due"] = "2026-11-04T23:00:00+08:00"
    face["updated_at"] = STAMP
    payload["ceo_face"] = face
    out = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    write_bytes(EXPORT, out.encode("utf-8"))
    return len(out.encode("utf-8"))


def close_heartbeat():
    text = read_text(HEARTBEAT)
    line = "2026-11-03 09:20 R2409 product: library_declaration_dialect_sweep " \
           "shipped, real tree SWEEP-CLEAN 5/5 routed, registry 532/4174\n"
    if not text.endswith("\n"):
        text += "\n"
    out = text + line
    write_bytes(HEARTBEAT, out.encode("utf-8"))
    return len(out.encode("utf-8"))


def main():
    try:
        state_bytes = close_state()
        export_bytes = close_export()
        beat_bytes = close_heartbeat()
    except (CloseoutError, IOError, OSError, ValueError) as exc:
        sys.stdout.write("CLOSEOUT R2409 FAILED: %s\n" % exc)
        return 1
    sys.stdout.write("CLOSEOUT R2409 tick=2409 items=%d state=%dB export=%dB "
                     "heartbeat=%dB\n"
                     % (len(ITEMS), state_bytes, export_bytes, beat_bytes))
    return 0


if __name__ == "__main__":
    sys.exit(main())