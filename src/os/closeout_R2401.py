# closeout_R2401.py - backlog row, queue stamp, gap seed, state tick and log,
# export refresh, heartbeat. Every state log item lands THROUGH the new guard
# door, so this window own ledger line is the first one written under it.
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import ledger_line_shape_guard as LLSG  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
BACKLOG = os.path.join(BASE, "backlog.md")
HEART = os.path.join(REPO, "heartbeat.txt")

ROUND_LINE = (
    "2026-11-03 R2401 product window (five-silence scan clean at open: empty "
    "git status at HEAD db7c7d1a, no .git/index.lock; LEDGER @BigDomain "
    "unreplied=0; DEC rows=140 tokens=92 new=0; the group orders tail is the "
    "2026-11-02 11:04 model-policy baseline already acknowledged as "
    "non-execution, though docs/orders.md at the group root currently carries "
    "unresolved merge-conflict markers from another company lane - read-only "
    "for this company, recorded here and not touched; benchmarks refreshed "
    "2026-11-02 inside the seven-day gate; floor FLOOR-MET main 5/5 tech "
    "10/10 explore 10/10; debt gate CLAIM-FIRST item=reconcile-battery-R2394 "
    "carried=7 stale=yes). The product-first law took the window: R2394 was "
    "verification-only and R2395..R2400 were product faces that left the "
    "battery row standing, so the reader was followed. PRODUCT: claimed "
    "state/queue/tech.md:470 prefix AC-LLSG1 (ledger_line_shape_guard), whose "
    "AC-LLSG1..AC-LLSG6 were pinned INSIDE that row at R2393 BEFORE any code, "
    "after a fresh anchor check at HEAD (all five anchors hit only the queue "
    "row, prose copies in .codely-cli auto-saves and state files - zero "
    "executable occupancy)."
)

FACE_LINE = (
    "2026-11-03 R2401 product face, what shipped: SHIPPED "
    "src/os/ledger_line_shape_guard.py plus its six-criteria suite. The "
    "ledger law is LEDGER_PREFIX_RE = ^R(\\d{3,5}) tokens: and "
    "parse_ledger_line refuses a line that breaks the pinned shape, but "
    "NOTHING asked it at the WRITE path: the R2392 closeout appended "
    "\"2026-11-02 R2392 tokens: ...\" with a date prefix, round 2392 then "
    "read rounds_without_ledger, and four ledger suites plus the census went "
    "red on a tree nobody had edited. One door now asks the shipped law "
    "(imported at CALL time, so patching the law moves every verdict), "
    "refuses a date-prefixed candidate with E_LLSG_DATE_PREFIX naming the "
    "prefix itself, takes round/local/api from the law own parse rather than "
    "a second number grammar, writes no byte on a refusal, and reports the "
    "exact predicted post size on a dry run before a single byte is written. "
    "This window own ledger line is the FIRST line that lands through it."
)

EVID_LINE = (
    "2026-11-03 R2401 evidence and board: SUITE PASS 6/6 twice with an "
    "identical criterion digest plus three adjacent suites green "
    "(qa/ledger-line-shape-guard-R2401.log, 1522B, legs=2 identical=True "
    "adjacent=3 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), and the three adjacent ledger suites were "
    "re-run directly and all green (ledger-lines 8/8, ledger-closeout 8/8, "
    "ledger-baseline 8/8). LIVE, not a plan: "
    "qa/ledger-line-shape-guard-live-R2401.log (516B, one utf-8 LF writer, "
    "src/os/live_R2401.py) reads the REAL 76494B state with 74 log items and "
    "26 ledger items, the last real ledger line R2400 as verdict=ACCEPTED "
    "local=30000 api=0, the R2392 date-prefixed candidate as verdict=REFUSED "
    "code=E_LLSG_DATE_PREFIX token=2026-11-02, a dry run over the real file "
    "predicting 77174 bytes with wrote=no, a byte-stable --json over the "
    "eight pinned keys, and the module digest 8017c190e91917fc unchanged "
    "before and after. WIRED into src/sandbox/reconcile_all.py as "
    "os-ledger-line-shape-guard(6), so the registry reads 527 suites / 4138 "
    "criteria. Tech row 470 stamped [done 2026-11-03 R2401] and one REAL "
    "measured gap row seeded (ledger_line_shape_writer_sweep, "
    "AC-LLSW1..AC-LLSW6 pre-registered in that row): MEASURED this window, "
    "231 non-test src/os/*.py files emit a ledger line and none of them "
    "routes through the door."
)

DISC_LINE = (
    "2026-11-03 R2401 honest disclosures: (a) three first-run reds were this "
    "window own code and fixtures, named rather than hidden: the fake law "
    "fixture carried no code/detail attributes so the module own unpacking "
    "raised AttributeError, the CLI mapped an unreadable state to exit 5 "
    "where AC-LLSG5 pins exit 3 (a real defect in _fail, fixed with an "
    "explicit code argument), and the suite stdlib check read the "
    "call-time `import ledger_lines` as a non-stdlib import until the "
    "expected set named it - no criterion was widened. (b) The door is not "
    "yet the tree only write path: 231 per-round writers still append "
    "directly, measured above and seeded as ledger_line_shape_writer_sweep, "
    "so this window proves the door works and that it is reachable, not that "
    "every line goes through it. (c) The 527/4138 registry figure is a "
    "WIRING count read off the SUITES AST with this window suite added; no "
    "battery walked the tree this window, so the carried row "
    "reconcile-battery-R2394 stays OPEN with that target. (d) tasks.md was "
    "left untouched: it is the P-47 canonical board and carries no row for "
    "this tech slice."
)

SELF_HEAL = (
    "2026-11-03 R2401 self-heal check: BigDomain-OSLoop is still registered "
    "with LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal but needs an elevated shell, and this "
    "session is unelevated, so the task definition was left untouched "
    "(hundred-and-fifty-sixth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md)."
)

TOKENS = (
    "R2401 tokens: local=~24k api=0 api_reason=product window - one door and "
    "its six-criteria suite written to criteria pinned eight rounds earlier, "
    "the shipped ledger law asked at CALL time rather than restated, one "
    "refusal path that names the date prefix the law cannot name itself, one "
    "verified append that predicts its post size, one registry wiring line, "
    "one two-leg evidence capture with three adjacent suites plus three "
    "adjacent suites re-run directly, one read-only live capture on the real "
    "state, one board stamp and one 231-file measured gap row seeded, and "
    "every log item of this closeout landed through the new door; zero cloud "
    "calls and zero external API touches when append mode is used"
)

GAP_ROW = (
    "- [ ] P2 tech seed (R2401, from this window own measured scope edge): "
    "`src/os/ledger_line_shape_writer_sweep.py` - the door now refuses a bad "
    "ledger line before it lands, but the tree carries 231 non-test "
    "src/os/*.py writers that emit a ledger line (closeout_R*.py and "
    "friends) and NONE of them calls it: measured this window by scanning "
    "every non-test .py for the literal 'tokens: local='. So the guard "
    "protects the line somebody writes through it and nothing else. Product: "
    "publish the writer set, name the ones on the current closeout path and "
    "report which of them already ask the door. Criteria AC-LLSW1..AC-LLSW6 "
    "pre-registered HERE BEFORE any code: AC-LLSW1 the acceptance law is "
    "asked of ledger_line_shape_guard at CALL time and a patched guard moves "
    "the verdict; AC-LLSW2 every writer is derived from the source rather "
    "than a hand-written list, and a writer that already asks the door reads "
    "GUARDED; AC-LLSW3 a writer that composes a ledger line string literal "
    "without asserting its shape reads UNGUARDED with the literal quoted; "
    "AC-LLSW4 the sweep is read-only and writes no byte anywhere; AC-LLSW5 "
    "CLI exits 0/2/3/5 with a byte-stable --json over pinned keys; AC-LLSW6 "
    "pure ASCII, stdlib only, no clock, no network, plus its own reconcile "
    "label. Anchors zero-occupancy at HEAD 2026-11-03: "
    "ledger_line_shape_writer_sweep, AC-LLSW, E_LLSW, "
    "os-ledger-line-shape-writer-sweep, test_ledger_line_shape_writer_sweep."
)

DISCHARGED = (
    "DISCHARGED R2401 (line 470, AC-LLSG1..AC-LLSG6): "
    "src/os/ledger_line_shape_guard.py plus its suite shipped against the "
    "criteria pinned at R2393. A candidate line is asked of "
    "ledger_lines.parse_ledger_line at CALL time, a date prefix is refused "
    "with E_LLSG_DATE_PREFIX naming it, round/local/api come from the law "
    "own parse, a refusal writes no byte, a dry run predicts the exact post "
    "size, and the CLI keeps exits 0/2/3/5 with a byte-stable --json. Live "
    "on the real tree: the R2400 ledger line ACCEPTED, the R2392 date "
    "prefix REFUSED, dry run 76494B -> 77174B with wrote=no, module digest "
    "unchanged. Registry 527 suites / 4138 criteria (wiring count). This "
    "window own ledger line is the first one that landed through the door; "
    "the 231 per-round writers that still bypass it are seeded as "
    "ledger_line_shape_writer_sweep."
)


def read(path):
    return io.open(path, "r", encoding="utf-8", newline="").read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def main():
    # 1. queue: stamp row 470, add the DISCHARGED block after it, seed gap row.
    queue = read(QUEUE)
    needle = "- [ ] P2 tech seed (R2393, from this window own measured seam): `src/os/ledger_line_shape_guard.py`"
    stamped_needle = "- [x] [done 2026-11-03 R2401] P2 tech seed (R2393, from this window own measured seam): `src/os/ledger_line_shape_guard.py`"
    if queue.count(stamped_needle) == 1:
        print("QUEUE row already stamped")
    else:
        if queue.count(needle) != 1:
            raise SystemExit("E_QUEUE_ROW: %d" % queue.count(needle))
        queue = queue.replace(needle, stamped_needle, 1)
        lines = queue.split("\n")
        out = []
        stamped = False
        for line in lines:
            out.append(line)
            if line.startswith(stamped_needle):
                out.append("")
                out.append(DISCHARGED)
                stamped = True
        if not stamped:
            raise SystemExit("E_QUEUE_STAMP")
        queue = "\n".join(out)
    if "ledger_line_shape_writer_sweep" not in queue:
        queue = queue.rstrip("\n") + "\n\n" + GAP_ROW + "\n"
    write(QUEUE, queue)
    print("QUEUE stamped and gap row seeded")

    # 2. backlog row on top
    backlog = read(BACKLOG)
    row = ("- [x] R2401 product window: ledger_line_shape_guard - the ledger "
           "law asked at the WRITE path (AC-LLSG1..AC-LLSG6, pinned at R2393), "
           "date prefix refused by name, refusal writes no byte, dry run "
           "predicts the post size, own ledger line landed through the door, "
           "registry 527 suites / 4138 criteria\n")
    if not backlog.startswith("- [x] R2401"):
        write(BACKLOG, row + backlog)
        print("BACKLOG row added")

    # 3. state: tick + log items, each through the guard door
    text = read(STATE)
    try:
        report = state_io.layout(text)
        layout_ok = bool(report.get("layout_ok", True))
    except Exception:
        layout_ok = True
    if not layout_ok:
        state_io.fix(STATE, execute=True)
        print("STATE layout canonicalised")
    before = os.path.getsize(STATE)
    for item in (ROUND_LINE, FACE_LINE, EVID_LINE, DISC_LINE, SELF_HEAL, TOKENS):
        verdict = LLSG.append_ledger_line(STATE, item, execute=True)
        if verdict["verdict"] != "ACCEPTED" or verdict["wrote"] != "yes":
            raise SystemExit("E_STATE_APPEND: %r" % verdict)
    text = read(STATE)
    if text.count('"tick": 2400') == 1:
        text = text.replace('"tick": 2400', '"tick": 2401', 1)
    elif text.count('"tick": 2401') != 1:
        raise SystemExit("E_TICK_ANCHOR")
    write(STATE, text)
    payload = json.loads(read(STATE))
    after = os.path.getsize(STATE)
    print("STATE tick=%d log_items=%d bytes=%d -> %d"
          % (payload["tick"], len(payload["log"]), before, after))

    # 4. heartbeat
    with io.open(HEART, "a", encoding="utf-8", newline="\n") as handle:
        handle.write("2026-11-03 R2401 product window: ledger_line_shape_guard "
                     "shipped, registry 527/4138, state tick 2401\n")
    print("HEARTBEAT appended")
    return 0


if __name__ == "__main__":
    sys.exit(main())