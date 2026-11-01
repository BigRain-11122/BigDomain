"""stamp_exempt_seed_guard_wire suite (R2361; criteria AC-SGS1..AC-SGS6 were
pinned inside the R2346 tech seed row of state/queue/tech.md:403 BEFORE this
code existed).

What this proves: the THIRD writer of state/queue/stamp_exempt.json now asks
the pinned-text guard instead of writing straight through one io.open(path,
"w"). A seed plan pins the digest and byte count of the declaration it read and
names them in its report; an execute hands that pinned reading to
stamp_exempt_guard.commit, which refuses E_SEG_STALE before a byte when another
writer moved the declaration in between, leaving the concurrent bytes untouched
and no temp residue; an unchanged digest still completes one atomic replace,
proved by reading the exact rendered bytes back. The wire carries no second
temp-write or replace path, and a dry run is the default.

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

import queue_done_stamp_exempt as SX  # noqa: E402
import stamp_exempt_guard as SEG  # noqa: E402
import stamp_exempt_seed_guard_wire as WIRE  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "stamp_exempt_seed_guard_wire.py")
SEEDER = os.path.join(BASE, "stamp_exempt_seed_R2280.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-stamp-exempt-seed-guard-wire"

PASSES = 0
FAILS = 0

HEADER = {"main": "### main\n\n", "tech": "### tech\n\n",
          "explore": "### explore\n\n"}
ROW_MAIN = "- [x] P2 main item R2210 also carrying no stamp"
ROW_TECH = "- [x] P2 tech item R2200 with no stamp at all"
ROW_EXPLORE = "- [x] P3 explore item R2222 with no stamp either"


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def declaration_text(entries):
    body = ['{', '  "note": "accepted rows",', '  "exemptions": [']
    lines = ["    " + json.dumps(item, ensure_ascii=True, sort_keys=False)
             for item in entries]
    body.append(",\n".join(lines))
    body.append("  ]")
    body.append("}")
    return "\n".join(body) + "\n"


def seeded_body(entries):
    """The same rendered layout the seed generator produces."""
    return declaration_text(entries)


def entry(queue, ident, declared="R2280", reason="closed before the law"):
    return {"queue": queue, "identity": ident, "declared": declared,
            "reason": reason}


def make_world(entries):
    rows = {"main": ROW_MAIN, "tech": ROW_TECH, "explore": ROW_EXPLORE}
    world = tempfile.mkdtemp(prefix="bigdomain-sgsw-")
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


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def residues(directory):
    return sorted(name for name in os.listdir(directory)
                  if name.endswith(WIRE.TEMP_SUFFIX))


# AC-SGS1: the guard surface is imported, execute flows straight through it,
# and this module carries no second temp-write or replace path.
def ac_sgs1():
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    imported = ("import stamp_exempt_guard as SEG" in source)
    no_second = ("os.replace(" not in source
                 and "io.open(temp" not in source
                 and "import tempfile" not in source)
    with io.open(SEEDER, "r", encoding="utf-8") as handle:
        seeder = handle.read()
    seeder_routes = ("stamp_exempt_seed_guard_wire as SEGW" in seeder
                     and "SEGW.execute(" in seeder
                     and 'io.open(path, "w"' not in seeder)
    world = make_world([entry("tech", "other#22222222")])
    report = WIRE.plan(decl_path(world), seeded_body([entry("tech", "rowA#333")]))
    seen = {}

    def recorder(path, pinned, payload, temp_suffix, codes=None):
        seen["path"] = path
        seen["pinned"] = pinned
        seen["payload"] = payload
        seen["suffix"] = temp_suffix
        return {"wrote": True, "read_back_ok": True, "before_bytes": 1,
                "after_bytes": len(payload), "digest_before": pinned["digest"],
                "digest_after": SEG.digest(payload)}

    original = SEG.commit
    SEG.commit = recorder
    try:
        merged = WIRE.execute(report)
    finally:
        SEG.commit = original
    flowed = (seen.get("path") == decl_path(world)
              and seen.get("suffix") == WIRE.TEMP_SUFFIX
              and seen.get("payload") == report["payload"]
              and merged.get("replaced_digest") == report["pinned"]["digest"])
    check(imported and no_second and seeder_routes and flowed,
          "AC-SGS1 guard imported, execute flows through SEG.commit, no second "
          "write path, and the seed generator routes through the wire")


# AC-SGS2: a plan pins the reading it saw and names it in its report.
def ac_sgs2():
    before = declaration_text([entry("tech", "rowA#11111111")])
    world = make_world([entry("tech", "rowA#11111111")])
    path = decl_path(world)
    report = WIRE.plan(path, seeded_body([entry("tech", "rowA#11111111"),
                                          entry("main", "rowB#22222222")]))
    pinned = report.get("pinned") or {}
    expect = SEG.pin(before)
    names = (pinned.get("digest") == expect["digest"]
             and pinned.get("bytes") == expect["bytes"]
             and report.get("before_bytes") == expect["bytes"]
             and len(pinned.get("digest") or "") == SEG.DIGEST_LEN)
    unchanged = read_bytes(path) == before.encode("utf-8")
    check(names and unchanged and report.get("dry_run") is True,
          "AC-SGS2 the plan pins the digest and byte count it read and names "
          "them, and plans nothing lost")


# AC-SGS3: a declaration that moved between plan and execute is refused before
# any byte, the concurrent bytes survive, and no temp residue is left.
def ac_sgs3():
    world = make_world([entry("tech", "rowA#11111111")])
    path = decl_path(world)
    report = WIRE.plan(path, seeded_body([entry("tech", "rowA#11111111")]))
    concurrent = declaration_text([entry("tech", "rowA#11111111"),
                                   entry("main", "late#99999999")])
    write_text(path, concurrent)
    code = None
    try:
        WIRE.execute(report)
    except SEG.StampGuardError as exc:
        code = exc.code
    survivor = read_bytes(path) == concurrent.encode("utf-8")
    clean = residues(os.path.dirname(path)) == []
    check(code == SEG.STALE_CODE and survivor and clean,
          "AC-SGS3 E_SEG_STALE before any byte, the concurrent declaration "
          "survives untouched and leaves no temp residue")


# AC-SGS4: an unchanged digest still writes once and proves it by read-back.
def ac_sgs4():
    world = make_world([entry("tech", "rowA#11111111")])
    path = decl_path(world)
    body = seeded_body([entry("tech", "rowA#11111111"),
                        entry("main", "rowB#22222222")])
    report = WIRE.plan(path, body)
    done = WIRE.execute(report)
    on_disk = read_bytes(path)
    exact = on_disk == body.encode("utf-8")
    proved = (done.get("wrote") is True and done.get("read_back_ok") is True
              and done.get("digest_after") == SEG.digest(body.encode("utf-8"))
              and done.get("after_bytes") == len(body.encode("utf-8"))
              and done.get("entries_after") == 2
              and done.get("replaced_digest") == report["pinned"]["digest"])
    clean = residues(os.path.dirname(path)) == []
    check(exact and proved and clean,
          "AC-SGS4 unchanged digest writes once, read-back carries the exact "
          "rendered bytes, entry and byte counts named")


# AC-SGS5: dry run stays the default, and the plan names what it would replace.
def ac_sgs5():
    world = make_world([entry("tech", "rowA#11111111")])
    path = decl_path(world)
    before = read_bytes(path)
    default_plan = WIRE.plan(path, seeded_body([entry("main", "n#1")]))
    default_dry = default_plan.get("dry_run") is True
    untouched = read_bytes(path) == before
    named = (default_plan.get("entries_before") == 1
             and default_plan.get("entries_after") == 1
             and isinstance(default_plan.get("before_bytes"), int)
             and isinstance(default_plan.get("after_bytes"), int))
    gate, root_plan, done = WIRE.plan_for_root(world, execute_it=False)
    root_dry = done is None and read_bytes(path) == before
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    label = WIRE.one_line(root_plan)
    speaks = label.startswith(WIRE.LABEL) and "dry=yes" in label
    check(default_dry and untouched and named and root_dry and speaks,
          "AC-SGS5 dry run is the default, the plan names entries and byte "
          "counts, and plan_for_root writes nothing without --execute")


# AC-SGS6: purity, its own reconcile label, and one runner entry carrying the
# six criteria this suite just counted.
def ac_sgs6():
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    try:
        source.encode("ascii")
        ascii_ok = True
    except UnicodeEncodeError:
        ascii_ok = False
    imports = set(re.findall(r"^(?:import|from)\s+([A-Za-z_][\w.]*)",
                             source, re.M))
    imports_ok = imports <= {"io", "json", "os", "sys", "stamp_exempt_guard"}
    banned = ("time.time", "datetime", "urllib", "requests", "socket",
              "subprocess")
    no_clock = not any(token in source for token in banned)
    label = WIRE.one_line({"wrote": True, "read_back_ok": True,
                           "before_bytes": 10, "after_bytes": 12,
                           "entries_before": 1, "entries_after": 2,
                           "replaced_digest": "AAAA", "digest_after": "BBBB"})
    label_ok = label.startswith(WIRE.LABEL) and "AAAA" in label
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner = handle.read()
    wired = ('"%s"' % LABEL) in runner and (
        "test_stamp_exempt_seed_guard_wire.py" in runner)
    check(ascii_ok and imports_ok and no_clock and label_ok and wired,
          "AC-SGS6 pure ASCII, stdlib only, zero network, no clock, its own "
          "reconcile label and one runner entry")


def main():
    print("SUITE stamp_exempt_seed_guard_wire (R2361) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    ac_sgs1()
    ac_sgs2()
    ac_sgs3()
    ac_sgs4()
    ac_sgs5()
    ac_sgs6()
    print("SUITE RESULT passes=%d fails=%d criteria=%d"
          % (PASSES, FAILS, EXPECTED_CRITERIA), flush=True)
    return 0 if FAILS == 0 else 2


if __name__ == "__main__":
    sys.exit(main())