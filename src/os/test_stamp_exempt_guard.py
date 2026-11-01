"""stamp_exempt_guard suite (R2346; criteria AC-SEG1..AC-SEG6 were pinned
inside the R2329 tech seed row of state/queue/tech.md BEFORE this code
existed).

What this proves: the acceptance declaration now has ONE write path carrying a
staleness law. A plan pins the digest of the text it read; an execute re-reads
the file and refuses E_SEG_STALE when that digest moved, so a plan built at T0
can no longer revert a concurrent append at T1; the refusal happens before a
byte is written, so the concurrent writer's text survives untouched and no
temp file is left behind; an unchanged digest still completes the one atomic
replace, proved by reading the bytes back. Both writers ask the guard through
the same callable instead of carrying a second copy of the mechanics.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
import os
import re
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import queue_done_stamp as QDS  # noqa: E402 - the gate reader
import queue_done_stamp_exempt as SEX  # noqa: E402
import stamp_exempt_append as SEPA  # noqa: E402
import stamp_exempt_guard as SEG  # noqa: E402
import stamp_exempt_prune as SPR  # noqa: E402
import stamp_exempt_review as SER  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "stamp_exempt_guard.py")
APPEND = os.path.join(BASE, "stamp_exempt_append.py")
PRUNE = os.path.join(BASE, "stamp_exempt_prune.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-stamp-exempt-guard"

PASSES = 0
FAILS = 0

HEADER = {"main": "### main\n\n", "tech": "### tech\n\n",
          "explore": "### explore\n\n"}
ROW_MAIN = "- [x] P2 main item R2210 also carrying no stamp"
ROW_TECH = "- [x] P2 tech item R2200 with no stamp at all"
ROW_EXPLORE = "- [x] P3 explore item R2222 with no stamp either"

PAIR = ("tech", "rowA#11111111")


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def identity_line(text):
    """The identity the gate derives from a row's ASCII excerpt."""
    return SEX.identity_of(text)


def entry(queue, ident, declared="R2280", reason="accepted as it stands",
          until=None):
    row = {"queue": queue, "identity": ident, "declared": declared,
           "reason": reason}
    if until is not None:
        row["until"] = until
    return row


def declaration_text(entries):
    """The shipped declaration layout: one entry per line inside the array."""
    body = ['{', '  "note": "accepted rows",', '  "exemptions": [']
    lines = ["    " + json.dumps(item, ensure_ascii=True, sort_keys=False)
             for item in entries]
    body.append(",\n".join(lines))
    body.append("  ]")
    body.append("}")
    return "\n".join(body) + "\n"


def make_world(entries):
    """A temp root carrying three queue files and one declaration."""
    rows = {"main": ROW_MAIN, "tech": ROW_TECH, "explore": ROW_EXPLORE}
    world = tempfile.mkdtemp(prefix="bigdomain-seg-")
    inner = os.path.join(world, "state", "queue")
    os.makedirs(inner)
    for name, body in rows.items():
        with io.open(os.path.join(inner, "%s.md" % name), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(HEADER[name] + body + "\n")
    with io.open(os.path.join(inner, "stamp_exempt.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(declaration_text(entries))
    return world


def decl_path(world):
    return os.path.join(world, "state", "queue", "stamp_exempt.json")


def read_bytes(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def append_world():
    """One declaration holding a single unrelated accepted entry."""
    return make_world([entry("tech", "other#22222222", declared="R2280")])


def prune_world():
    """One matching entry, one ghost, one expired - the shipped prune fixture."""
    ident_tech = SEX.identity_of(QDS.excerpt(ROW_TECH))
    ident_explore = SEX.identity_of(QDS.excerpt(ROW_EXPLORE))
    return make_world([entry("tech", ident_tech),
                       entry("main", "ghost#deadbeef", declared="R2270"),
                       entry("explore", ident_explore, declared="R2200",
                             until="R2210")])


def fake_join(pairs):
    """Patch the reviewer join only - the writer imports it, never re-derives."""
    def fake(root):
        return [], pairs
    return fake


def live_pairs_for(positions):
    rows = [{"file": "state/queue/tech.md", "line": pos, "queue": "tech",
             "identity": PAIR[1], "seed_round": "R2200"} for pos in positions]
    return {PAIR: rows}


def tree_digests(world):
    """Every file under the world with its digest, for a whole-tree comparison."""
    out = {}
    for dirpath, _dirs, files in os.walk(world):
        for name in files:
            full = os.path.join(dirpath, name)
            with io.open(full, "rb") as handle:
                out[os.path.relpath(full, world)] = SEG.digest(handle.read())
    return out


def temp_residue(folder):
    return sorted(name for name in os.listdir(folder)
                  if name.endswith(".seap-tmp") or name.endswith(".sepr-tmp"))


def refusal(module_class, fn):
    """Run fn and hand back the error code, or None when it did not refuse."""
    try:
        fn()
    except module_class as exc:
        return exc.code
    return None


# AC-SEG1: a plan pins the digest of the text it read, in BOTH writers, and
# that pin moves when the text (or the file) moves - a pin, not a constant.
def ac_seg1():
    world = append_world()
    path = decl_path(world)
    text = read_text(path)
    expected = SEG.pin(text)
    original = SER.live_pairs
    SER.live_pairs = fake_join(live_pairs_for([11]))
    try:
        appended = SEPA.append(world, "tech", PAIR[1], "R2346",
                               "closed after R2280 with a young stamp")
        planned = SPR.plan(world, 2346)
    finally:
        SER.live_pairs = original
    both = (appended.get("source_digest") == expected["digest"]
            and appended.get("source_bytes") == expected["bytes"]
            and planned.get("source_digest") == expected["digest"]
            and planned.get("source_bytes") == expected["bytes"])
    moved = SEG.pin(text + " ")
    pin_moves = (moved["digest"] != expected["digest"]
                 and moved["bytes"] == expected["bytes"] + 1)
    other = SEG.read_pin(decl_path(prune_world()))
    per_file = other["digest"] != expected["digest"]
    check(both and pin_moves and per_file,
          "AC-SEG1 both plans pin the digest and byte count of the text they "
          "read, and a moved text or a different file moves the pin")


# AC-SEG2: an execute re-reads and refuses E_SEG_STALE when the digest moved
# between the plan and the write - proved through the writer by handing it a
# plan pinned at T0 after another writer touched the file at T1, and then
# straight at the guard.
def ac_seg2():
    world = append_world()
    path = decl_path(world)
    text = read_text(path)
    rendered = SEPA.render_entry("tech", PAIR[1], "R2346", "fixture reason")
    planned, post = SEPA.plan(text, rendered, live_pairs_for([11]))
    concurrent = text + "\n"
    write_text(path, concurrent)
    original = SEPA.plan
    SEPA.plan = lambda t, e, p: (planned, post)
    try:
        code = refusal(SEPA.StampExemptAppendError,
                       lambda: SEPA.append(world, "tech", PAIR[1], "R2346",
                                           "fixture reason", execute=True))
    finally:
        SEPA.plan = original
    stale_pin = SEG.pin(read_text(path))
    write_text(path, read_text(path) + "\n")
    direct = refusal(SEG.StampGuardError,
                     lambda: SEG.commit(path, stale_pin, b"{}\n",
                                        SEPA.TEMP_SUFFIX))
    no_pin = refusal(SEG.StampGuardError,
                     lambda: SEG.commit(path, {}, b"{}\n", SEPA.TEMP_SUFFIX))
    check(code == SEG.STALE_CODE and direct == SEG.STALE_CODE
          and no_pin == SEG.STALE_CODE,
          "AC-SEG2 a moved digest refuses E_SEG_STALE through the writer and "
          "through the guard, and an unpinned commit refuses rather than "
          "writing blind")


# AC-SEG3: the refusal leaves the concurrent writer's bytes untouched and no
# temp file behind, because the digest is checked before anything is created.
def ac_seg3():
    world = append_world()
    path = decl_path(world)
    text = read_text(path)
    rendered = SEPA.render_entry("tech", PAIR[1], "R2346", "fixture reason")
    planned, post = SEPA.plan(text, rendered, live_pairs_for([11]))
    concurrent = text + "\n"
    write_text(path, concurrent)
    before_tree = tree_digests(world)
    before = read_bytes(path)
    original = SEPA.plan
    SEPA.plan = lambda t, e, p: (planned, post)
    try:
        refusal(SEPA.StampExemptAppendError,
                lambda: SEPA.append(world, "tech", PAIR[1], "R2346",
                                    "fixture reason", execute=True))
    finally:
        SEPA.plan = original
    after = read_bytes(path)
    residue = temp_residue(os.path.dirname(path))
    tree_same = before_tree == tree_digests(world)
    check(before == after and after.decode("utf-8") == concurrent
          and residue == [] and tree_same,
          "AC-SEG3 the stale refusal keeps the concurrent writer's bytes "
          "byte-identical, leaves the rest of the tree untouched and leaves "
          "no temp residue")


# AC-SEG4: an unchanged digest still completes the ONE atomic replace, proved
# by reading the bytes back - and the same holds through the guard directly.
def ac_seg4():
    world = append_world()
    path = decl_path(world)
    original = SER.live_pairs
    SER.live_pairs = fake_join(live_pairs_for([11]))
    try:
        report = SEPA.append(world, "tech", PAIR[1], "R2346",
                             "fixture reason", execute=True)
    finally:
        SER.live_pairs = original
    data = read_bytes(path)
    entries = SEPA.declaration_entries(data.decode("utf-8"))
    wrote_ok = (report["wrote"] is True and report["read_back_ok"] is True
                and report["predicted_bytes"] == len(data)
                and entries[-1]["identity"] == PAIR[1]
                and temp_residue(os.path.dirname(path)) == [])
    direct_path = decl_path(append_world())
    pinned = SEG.read_pin(direct_path)
    payload = b"replaced by the guard\n"
    guard = SEG.commit(direct_path, pinned, payload, SEPA.TEMP_SUFFIX)
    direct_ok = (guard["wrote"] and guard["read_back_ok"]
                 and read_bytes(direct_path) == payload
                 and guard["digest_after"] == SEG.digest(payload)
                 and guard["before_bytes"] == pinned["bytes"]
                 and guard["digest_before"] == pinned["digest"])
    check(wrote_ok and direct_ok,
          "AC-SEG4 an unchanged digest completes one atomic replace, proved by "
          "read-back, with no temp residue")


# AC-SEG5: both writers ask the guard through ONE shared callable - module
# identity, no second copy of the write mechanics in either, and both routed
# through the same function object when executed for real.
def ac_seg5():
    identity_ok = (SEPA.SEG is SEG and SPR.SEG is SEG
                   and SEPA.SEG.commit is SPR.SEG.commit)
    sources = {}
    for name, path in (("append", APPEND), ("prune", PRUNE)):
        with io.open(path, "r", encoding="utf-8") as handle:
            body = handle.read()
        # prose may name the mechanism; a CODE replace call may not survive
        code = "\n".join(line for line in body.split("\n")
                         if not line.lstrip().startswith("#"))
        sources[name] = code
    no_copy = all("os.replace(" not in body for body in sources.values())
    both_call = all("SEG.commit(" in body for body in sources.values())
    calls = {"append": 0, "prune": 0}
    real = SEG.commit

    def counting(kind, *args, **kwargs):
        calls[kind] += 1
        return real(*args, **kwargs)

    try:
        world = append_world()
        original = SER.live_pairs
        SER.live_pairs = fake_join(live_pairs_for([11]))
        SEG.commit = lambda *a, **k: counting("append", *a, **k)
        try:
            SEPA.append(world, "tech", PAIR[1], "R2346", "fixture reason",
                        execute=True)
        finally:
            SER.live_pairs = original
        SEG.commit = lambda *a, **k: counting("prune", *a, **k)
        pruned = SPR.plan(prune_world(), 2346, execute=True)
    finally:
        SEG.commit = real
    routed = (calls["append"] == 1 and calls["prune"] == 1
              and pruned["wrote"] is True)
    check(identity_ok and no_copy and both_call and routed,
          "AC-SEG5 both writers share one guard callable: same function "
          "object, no copied os.replace, and an executed append and an "
          "executed prune each route through it")


# AC-SEG6: purity, its own reconcile label, and one runner entry carrying the
# six criteria this suite just counted.
def ac_seg6():
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    try:
        source.encode("ascii")
        ascii_ok = True
    except UnicodeEncodeError:
        ascii_ok = False
    imports = set(re.findall(r"^(?:import|from)\s+([A-Za-z_][\w.]*)",
                             source, re.M))
    imports_ok = imports <= {"hashlib", "io", "os"}
    banned = ("time.time", "datetime", "urllib", "requests", "socket",
              "subprocess")
    no_clock = not any(token in source for token in banned)
    label = SEG.one_line({"wrote": True, "read_back_ok": True,
                          "before_bytes": 10, "after_bytes": 12,
                          "digest_before": "AAAA", "digest_after": "BBBB"})
    label_ok = label.startswith("STAMP EXEMPT GUARD") and "AAAA->BBBB" in label
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner = handle.read()
    wired = ('"%s"' % LABEL) in runner and "test_stamp_exempt_guard.py" in runner
    check(ascii_ok and imports_ok and no_clock and label_ok and wired,
          "AC-SEG6 pure ASCII, stdlib only, zero network, no clock, its own "
          "reconcile label and one runner entry")


def main():
    print("SUITE stamp_exempt_guard (R2346) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    ac_seg1()
    ac_seg2()
    ac_seg3()
    ac_seg4()
    ac_seg5()
    ac_seg6()
    print("SUITE RESULT passes=%d fails=%d criteria=%d"
          % (PASSES, FAILS, EXPECTED_CRITERIA), flush=True)
    return 0 if FAILS == 0 else 2


if __name__ == "__main__":
    sys.exit(main())