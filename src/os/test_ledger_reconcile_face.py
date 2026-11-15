"""Battery suite for tools/ledger_reconcile_face.py - the ledger self-check face.

AC-LRC1..AC-LRC6 belong to the tool and were pinned in src/os/backlog.md at
R2794, BEFORE the tool existed. R2794 closed with an explicit debt: the face had
no row in src/sandbox/reconcile_all.py, so its six criteria were guarded only by
the tool grading itself. This suite is that row; AC-LRB1..AC-LRB8 (the guard
shape) were pinned at R2795, again BEFORE this file existed.

Scope, stated honestly: build_doc() runs the SHIPPED src/sandbox/ledger/
reconcile.py on TEMP COPIES of the book, so this suite really executes the gate
- twice against the landed pair (clean, then with module paths pointed at a
tampered private copy). It does NOT assert byte-identity between two renders:
R2794 measured that it cannot hold, because the shipped ledger API mints random
tx ids. Determinism is therefore asserted on the values the page derives, not
on ids it no longer carries. Narrowed before the code, not after a failure.

Every check is read-only against the repo: the private world lives under the
system temp dir and is removed before the run ends, and the live ledger.db is
stat-compared before and after.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import importlib.util
import json
import os
import re
import shutil
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "ledger_reconcile_face.py")
OUT_HTML = os.path.join(ROOT, "preview", "ledger-reconcile-face.html")
OUT_JSON = os.path.join(ROOT, "preview", "ledger-reconcile-face.json")
LIVE_DB = os.path.join(ROOT, "src", "sandbox", "ledger", "ledger.db")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
NAME = "os-ledger-reconcile-face"

FAILS = []
CHECKS = []


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print("  | PASS %s %s" % (name, detail))
    else:
        FAILS.append(name)
        print("  | FAIL %s %s" % (name, detail))


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def stat_sig(path):
    if not os.path.exists(path):
        return None
    return (os.path.getsize(path), os.path.getmtime(path))


def load_tool():
    spec = importlib.util.spec_from_file_location("lrc_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ascii_only(path):
    try:
        read_bytes(path).decode("ascii")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def main():
    before = {
        "html": stat_sig(OUT_HTML),
        "json": stat_sig(OUT_JSON),
        "db": stat_sig(LIVE_DB),
        "wal": stat_sig(LIVE_DB + "-wal"),
        "shm": stat_sig(LIVE_DB + "-shm"),
    }
    tool = load_tool()

    # AC-LRB1 - the landed pair exists, decodes, and carries three blocks.
    have = os.path.exists(OUT_HTML) and os.path.exists(OUT_JSON)
    payload = None
    html_text = ""
    if have:
        try:
            html_text = read_bytes(OUT_HTML).decode("utf-8")
            payload = json.loads(read_bytes(OUT_JSON).decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:  # noqa: BLE001
            print("  ! pair unreadable: %s" % exc)
            payload = None
    doc = payload if isinstance(payload, dict) else {}
    real = doc.get("real") or {}
    counts = doc.get("counts") or {}
    rows = real.get("checks") or []
    blocks = all(isinstance(doc.get(key), dict)
                 for key in ("real", "seeded", "control", "counts"))
    ok("AC-LRB1",
       have and bool(doc) and blocks and bool(rows)
       and counts.get("checks") == len(rows),
       "rows=%d announced=%s blocks=%s html=%dB"
       % (len(rows), counts.get("checks"), blocks, len(html_text.encode("utf-8"))))

    # AC-LRB2 - the shipped gate passes on the repo pair and writes nothing.
    findings = tool.check()
    after_gate = (stat_sig(OUT_HTML), stat_sig(OUT_JSON))
    untouched = after_gate == (before["html"], before["json"])
    ok("AC-LRB2", have and not findings and untouched,
       "rc=%d findings=%d untouched=%s"
       % (0 if not findings else 2, len(findings), untouched))

    # AC-LRB3 - no test path opens the repository book.
    live_same = (stat_sig(LIVE_DB) == before["db"]
                 and stat_sig(LIVE_DB + "-wal") == before["wal"]
                 and stat_sig(LIVE_DB + "-shm") == before["shm"])
    ok("AC-LRB3", have and live_same,
       "db=%s wal=%s shm=%s"
       % (stat_sig(LIVE_DB) == before["db"],
          stat_sig(LIVE_DB + "-wal") == before["wal"],
          stat_sig(LIVE_DB + "-shm") == before["shm"]))

    # AC-LRB4 - counts recomputed, verdicts equal the tool's own rc mapping.
    map_pairs = [
        (real.get("verdict"), tool.verdict_of(real.get("rc"))),
        ((doc.get("seeded") or {}).get("run", {}).get("verdict"),
         tool.verdict_of((doc.get("seeded") or {}).get("run", {}).get("rc"))),
    ]
    fail_count = len([c for c in rows if c.get("verdict") == "FAIL"])
    ok("AC-LRB4", have and all(a == b for a, b in map_pairs)
       and counts.get("real_fail") == fail_count,
       "real=%s seeded=%s fails=%d announced=%s"
       % (map_pairs[0][0], map_pairs[1][0], fail_count,
          counts.get("real_fail")))

    # AC-LRB5 - the empty-book disclosure is derived, not written down.
    entries = (doc.get("stats") or {}).get("entries")
    empty_flag = counts.get("real_empty")
    disclosed = (not empty_flag) or (tool.L["empty"] in html_text)
    ok("AC-LRB5", have and entries is not None
       and empty_flag == (entries == 0) and bool(disclosed),
       "entries=%s empty=%s disclosed=%s" % (entries, empty_flag, bool(disclosed)))

    # AC-LRB6 - the tampered-copy run really went red and named what flipped.
    control = doc.get("control") or {}
    run = control.get("run") or {}
    flipped = control.get("flipped") or []
    known = set(c.get("name") for c in rows)
    ok("AC-LRB6",
       have and run.get("rc") not in (None, 0) and bool(flipped)
       and all(name in known for name in flipped),
       "control_rc=%s flipped=%d known=%s"
       % (run.get("rc"), len(flipped), all(n in known for n in flipped)))

    # AC-LRB7 - a private copy with one altered field reddens the gate.
    world = tempfile.mkdtemp(prefix="lrb-")
    try:
        temp_json = os.path.join(world, "face.json")
        temp_html = os.path.join(world, "face.html")
        with open(temp_html, "wb") as handle:
            handle.write(html_text.encode("utf-8"))
        tampered = json.loads(json.dumps(doc))
        if tampered.get("real", {}).get("checks"):
            first = tampered["real"]["checks"][0]
            first["name"] = str(first.get("name", "")) + "-x"
        with open(temp_json, "wb") as handle:
            handle.write(json.dumps(tampered, ensure_ascii=False,
                                    indent=2).encode("utf-8"))
        keep = (tool.HTML, tool.JSON)
        tool.HTML, tool.JSON = temp_html, temp_json
        try:
            tfindings = tool.check()
        finally:
            tool.HTML, tool.JSON = keep
        pair_same = (stat_sig(OUT_HTML) == before["html"]
                     and stat_sig(OUT_JSON) == before["json"])
        ok("AC-LRB7", have and bool(tfindings) and pair_same,
           "findings=%d pair_same=%s" % (len(tfindings), pair_same))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    # AC-LRB8 - ASCII sources, stdlib only, exactly one registry row at eight.
    registry = ""
    if os.path.exists(REGISTRY):
        registry = read_bytes(REGISTRY).decode("utf-8", "replace")
    row = re.findall(
        r'\("' + re.escape(NAME) + r'",\s*os\.path\.join\([^)]*\),\s*(\d+)\)',
        registry)
    ok("AC-LRB8", ascii_only(TOOL) and ascii_only(os.path.abspath(__file__))
       and row == ["8"],
       "tool_ascii=%s suite_ascii=%s rows=%s"
       % (ascii_only(TOOL), ascii_only(os.path.abspath(__file__)), row))

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
