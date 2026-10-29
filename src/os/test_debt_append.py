"""Debt-append suite (R2251; criteria AC-DEBTA1..AC-DEBTA6 were
pre-registered in state/queue/tech.md as the R2248-a seed BEFORE this
code existed - honesty law).

What this proves: a carried-debt row can be written by a callable that
uses the register's own law, and the writer cannot invent a shape the
reader refuses. The row lands at the end of the Open block, a duplicate
item and a second first=yes are refused before any byte changes, the
write is one atomic replace proved by a read-back equal to the
prediction, and the dry run writes nothing.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import hashlib
import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import debt_append as DA  # noqa: E402
import debt_register as DR  # noqa: E402

EXPECTED_CRITERIA = 6
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-debt-append"

HEADER = ("# debt register\n\nprose that mentions - [ ] a row law\n\n"
          "## Open\n\n")
FOOTER = "\n## Closed\n\n- [x] opened=R2200 | item=old-thing | closed=R2201\n"

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def make_world(body):
    world = tempfile.mkdtemp(prefix="bigdomain-da-")
    state = os.path.join(world, "state")
    os.makedirs(state)
    with io.open(os.path.join(state, "debt.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def digest_tree(world):
    parts = []
    for base, dirs, files in os.walk(world):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(base, name)
            with open(path, "rb") as handle:
                body = handle.read()
            rel = os.path.relpath(path, world).replace(os.sep, "/")
            parts.append("%s %d %s" % (rel, len(body),
                                       hashlib.sha256(body).hexdigest()[:12]))
    return "\n".join(parts)


def register_path(world):
    return os.path.join(world, "state", "debt.md")


def read_bytes(world):
    with open(register_path(world), "rb") as handle:
        return handle.read()


def raise_code(call):
    try:
        call()
    except DA.DebtAppendError as exc:
        return exc.code
    return None


def test_shape():
    """AC-DEBTA1: the row renders in the register format and lands in Open."""
    body = HEADER + ("- [ ] opened=R2240 | item=older | first=no\n")
    world = make_world(body + FOOTER)
    try:
        report = DA.append_row(world, "R2251", "new-debt",
                               "note text", "no", execute=False)
        expected = ("- [ ] opened=R2251 | item=new-debt | "
                    "note=note text | first=no")
        ok = (report["row"] == expected
              and report["wrote"] is False
              and report["read_back_ok"] is None)
        parsed = DR.parse_row(expected[len("- [ ] "):], True)
        ok = ok and parsed["item"] == "new-debt" and parsed["first"] == "no"
        text = read_bytes(world).decode("utf-8")
        ok = ok and text == body + FOOTER
        no_note = DA.build_row("R2251", "bare", "", "no")
        ok = ok and no_note == "- [ ] opened=R2251 | item=bare | first=no"
    finally:
        drop_world(world)
    check(ok, "AC-DEBTA1 append shape")


def test_duplicate():
    """AC-DEBTA2: an item already on the register is refused, nothing written."""
    body = HEADER + ("- [ ] opened=R2240 | item=older | first=no\n")
    world = make_world(body + FOOTER)
    try:
        before = read_bytes(world)
        code_open = raise_code(
            lambda: DA.append_row(world, "R2251", "older", "", "no", True))
        done_body = (body
                     + "- [x] opened=R2200 | item=closed-one | closed=R2201\n")
        world2 = make_world(done_body + FOOTER)
        try:
            code_done = raise_code(
                lambda: DA.append_row(world2, "R2251", "closed-one",
                                      "", "no", True))
            ok = (code_open == "E_DEBTA_DUP"
                  and code_done == "E_DEBTA_DUP"
                  and read_bytes(world) == before
                  and read_bytes(world2)
                  == (done_body + FOOTER).encode("utf-8"))
        finally:
            drop_world(world2)
    finally:
        drop_world(world)
    check(ok, "AC-DEBTA2 duplicate refusal")


def test_first_flag():
    """AC-DEBTA3: a second open first=yes is refused; first=no still lands."""
    body = HEADER + ("- [ ] opened=R2240 | item=older | first=yes\n")
    world = make_world(body + FOOTER)
    try:
        before = read_bytes(world)
        code = raise_code(
            lambda: DA.append_row(world, "R2251", "new-lead", "", "yes", True))
        ok = (code == "E_DEBTA_FIRST" and read_bytes(world) == before)
        report = DA.append_row(world, "R2251", "new-lead", "", "no", True)
        rows = DR.parse(read_bytes(world).decode("utf-8"))
        leads = [r for r in rows if r["state"] == "open" and r["first"] == "yes"]
        ok = (ok and report["wrote"] is True and len(leads) == 1
              and leads[0]["item"] == "older")
    finally:
        drop_world(world)
    check(ok, "AC-DEBTA3 first-flag refusal")


def test_read_back():
    """AC-DEBTA4: the write is read back through the register's own parser."""
    body = HEADER + ("- [ ] opened=R2240 | item=older | first=no\n")
    world = make_world(body + FOOTER)
    try:
        report = DA.append_row(world, "R2251", "new-debt", "why", "no", True)
        live = DR.register(world, "R2251")
        found = [r for r in live["rows"] if r["item"] == "new-debt"]
        ok = (report["read_back_ok"] is True
              and len(found) == 1
              and found[0]["state"] == "open"
              and found[0]["opened"] == "R2251"
              and found[0]["note"] == "why"
              and found[0]["carried"] == 0
              and live["open_count"] == 2)
        order = read_bytes(world).decode("utf-8")
        ok = ok and order.index("older") < order.index("new-debt") \
            < order.index("## Closed")
    finally:
        drop_world(world)
    check(ok, "AC-DEBTA4 read-back through the parser")


def test_atomic():
    """AC-DEBTA5: one atomic replace, no residue, byte prediction exact."""
    body = HEADER + ("- [ ] opened=R2240 | item=older | first=no\n")
    world = make_world(body + FOOTER)
    try:
        before = read_bytes(world)
        report = DA.append_row(world, "R2251", "new-debt", "", "no", True)
        after = read_bytes(world)
        residue = [n for n in os.listdir(os.path.join(world, "state"))
                   if n.endswith(DA.TEMP_SUFFIX)]
        ok = (report["predicted_bytes"] == len(after)
              and report["before_bytes"] == len(before)
              and report["predicted_bytes"] > report["before_bytes"]
              and after.endswith(FOOTER.encode("utf-8"))
              and residue == [])
        again = DA.append_row(world, "R2251", "other", "", "no", False)
        ok = ok and again["before_bytes"] == len(after)
    finally:
        drop_world(world)
    check(ok, "AC-DEBTA5 atomic write")


def test_purity():
    """AC-DEBTA6: the dry run writes nothing, and the source stays pure."""
    body = HEADER + ("- [ ] opened=R2240 | item=older | first=no\n")
    world = make_world(body + FOOTER)
    try:
        before = digest_tree(world)
        DA.append_row(world, "R2251", "new-debt", "n", "no", execute=False)
        ok = digest_tree(world) == before
        path = os.path.join(BASE, "debt_append.py")
        with open(path, "rb") as handle:
            raw = handle.read()
        raw.decode("ascii")
        source = raw.decode("ascii")
        forbidden = ("import socket", "import urllib", "import http",
                     "import requests", "time.time", "datetime")
        ok = ok and not any(token in source for token in forbidden)
        ok = ok and "import debt_register as DR" in source
        with open(RUNNER, "rb") as handle:
            runner = handle.read().decode("utf-8", "replace")
        ok = ok and LABEL in runner
    finally:
        drop_world(world)
    check(ok, "AC-DEBTA6 purity of the dry run")


def main():
    test_shape()
    test_duplicate()
    test_first_flag()
    test_read_back()
    test_atomic()
    test_purity()
    total = PASSES + FAILS
    verdict = "PASS" if FAILS == 0 and PASSES == EXPECTED_CRITERIA else "FAIL"
    print("SUITE %s %d/%d" % (verdict, PASSES, EXPECTED_CRITERIA))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())