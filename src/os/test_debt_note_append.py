"""Debt-note-grow suite (R2600; criteria AC-DRNA1..AC-DRNA6 were
pre-registered in state/queue/tech.md as the R2600 seed BEFORE this code
existed - honesty law).

What this proves: a note segment grows INSIDE the note field and every
other key keeps its place, so a row whose last segment is `first=yes`
stays readable; the writer asks the shipped register parser both before
and after composing and refuses when the composed row would not parse;
refusals write nothing; the write is one atomic replace proved by a
byte read-back, the dry run writes nothing, and the CLI codes are fixed.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import contextlib
import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import debt_note_append as DNA  # noqa: E402
import debt_register as DR  # noqa: E402

EXPECTED_CRITERIA = 6
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-debt-note-append"

HEADER = ("# debt register\n\nprose that mentions - [ ] a row law\n\n"
          "## Open\n\n")
LEAD = ("- [ ] opened=R2596 | item=lead-row | note=first note | first=yes\n")
OTHER = "- [ ] opened=R2590 | item=other-row | first=no\n"
FOOTER = "\n## Closed\n\n- [x] opened=R2200 | item=old | closed=R2201\n"

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
    world = tempfile.mkdtemp(prefix="bigdomain-drna-")
    state = os.path.join(world, "state")
    os.makedirs(state)
    with io.open(os.path.join(state, "debt.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def register_path(world):
    return os.path.join(world, "state", "debt.md")


def read_bytes(world):
    with open(register_path(world), "rb") as handle:
        return handle.read()


def raise_code(call):
    try:
        call()
    except DNA.DebtNoteError as exc:
        return exc.code
    return None


def run_main(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = DNA.main(argv)
    return code, out.getvalue()


def test_note_grows_inside():
    """AC-DRNA1: the text lands in note; first=yes keeps its own segment."""
    world = make_world(HEADER + LEAD + OTHER + FOOTER)
    try:
        # the shipped parser is asked at CALL time: a patched parser moves it
        asked = []
        real = DR.parse

        def counting(text):
            asked.append(len(text))
            return real(text)

        DR.parse = counting
        try:
            report = DNA.append_note(world, "lead-row", "note_x_R2600:",
                                     "note_x_R2600: measured note",
                                     execute=True)
        finally:
            DR.parse = real
        lines = read_bytes(world).decode("utf-8").split("\n")
        line = [l for l in lines if "item=lead-row" in l][0]
        ok = (report["note_grew"] is True
              and report["first_kept"] == "yes"
              and line.endswith("| first=yes")
              and "first=yes ;" not in line
              and "note=first note ; note_x_R2600: measured note" in line)
        # a row with NO note field gains one and still ends on first=
        world2 = make_world(HEADER + OTHER + FOOTER)
        try:
            rep2 = DNA.append_note(world2, "other-row", "m2:", "m2: text",
                                   execute=True)
            lines2 = read_bytes(world2).decode("utf-8").split("\n")
            row2 = [l for l in lines2 if "item=other-row" in l][0]
            ok = (ok and rep2["note_grew"] is False
                  and row2.endswith("| note=m2: text | first=no")
                  and DR.parse(read_bytes(world2).decode("utf-8")))
        finally:
            drop_world(world2)
    finally:
        drop_world(world)
    check(ok and len(asked) >= 2, "AC-DRNA1 note grows inside the note field")


def test_refusals_write_nothing():
    """AC-DRNA2: missing, duplicate, closed and marker rows are all refused."""
    body = HEADER + LEAD + OTHER + FOOTER
    world = make_world(body)
    try:
        before = read_bytes(world)
        codes = {}
        codes["no_row"] = raise_code(
            lambda: DNA.append_note(world, "ghost", "g1:", "g1: x", True))
        codes["marker"] = raise_code(
            lambda: DNA.append_note(world, "lead-row", "first note",
                                    "already there", True))
        codes["shape"] = raise_code(
            lambda: DNA.append_note(world, "lead-row", "p1:", "a|b", True))
        ok = (codes["no_row"] == "E_DRNA_NO_ROW"
              and codes["marker"] == "E_DRNA_MARKER"
              and codes["shape"] == "E_DRNA_BAD_FIELD"
              and read_bytes(world) == before)
        dup = (HEADER + LEAD
               + "- [ ] opened=R2597 | item=lead-row | first=no\n" + FOOTER)
        world2 = make_world(dup)
        try:
            codes["dup"] = raise_code(
                lambda: DNA.append_note(world2, "lead-row", "d1:", "d1: x",
                                        True))
            ok = ok and codes["dup"] == "E_DRNA_DUP_ROW"
        finally:
            drop_world(world2)
        done = (HEADER
                + "- [x] opened=R2596 | item=closed-row | closed=R2597\n"
                + OTHER + FOOTER)
        world3 = make_world(done)
        try:
            codes["closed"] = raise_code(
                lambda: DNA.append_note(world3, "closed-row", "c1:", "c1: x",
                                        True))
            code_world, _ = run_main(["--item", "closed-row", "--marker",
                                      "c1:", "--text", "c1: x",
                                      "--root", world3, "--execute"])
            ok = (ok and codes["closed"] == "E_DRNA_NOT_OPEN"
                  and code_world == 2
                  and read_bytes(world3) == (done).encode("utf-8"))
        finally:
            drop_world(world3)
    finally:
        drop_world(world)
    check(ok, "AC-DRNA2 refusals write nothing")


def test_post_refusal():
    """AC-DRNA3: the shipped law is asked on the composed row and wins."""
    world = make_world(HEADER + LEAD + OTHER + FOOTER)
    try:
        before = read_bytes(world)
        real = DR.parse
        calls = []

        def refuse_second(text):
            calls.append(1)
            if len(calls) > 1:
                raise DR.DebtRegisterError("E_DR_TEST",
                                           "simulated reader refusal")
            return real(text)

        DR.parse = refuse_second
        try:
            code = raise_code(
                lambda: DNA.append_note(world, "lead-row", "x1:", "x1: text",
                                        True))
        finally:
            DR.parse = real
        residue = [n for n in os.listdir(os.path.join(world, "state"))
                   if n.endswith(DNA.TEMP_SUFFIX)]
        ok = (code == "E_DRNA_POST"
              and read_bytes(world) == before
              and residue == [])
    finally:
        drop_world(world)
    check(ok, "AC-DRNA3 composed row must parse through the shipped law")


def test_atomic_and_dry():
    """AC-DRNA4: one atomic replace, byte prediction exact, dry run writes."""
    world = make_world(HEADER + LEAD + OTHER + FOOTER)
    try:
        before = read_bytes(world)
        plan = DNA.append_note(world, "lead-row", "n4:", "n4: text",
                               execute=False)
        dry_ok = (read_bytes(world) == before
                  and plan["wrote"] is False
                  and plan["predicted_bytes"] > plan["before_bytes"])
        report = DNA.append_note(world, "lead-row", "n4:", "n4: text",
                                 execute=True)
        after = read_bytes(world)
        old_lines = before.decode("utf-8").split("\n")
        new_lines = after.decode("utf-8").split("\n")
        hit = [i for i, l in enumerate(old_lines) if "item=lead-row" in l][0]
        others_same = all(a == b for i, (a, b) in enumerate(zip(old_lines,
                                                                new_lines))
                          if i != hit) and len(old_lines) == len(new_lines)
        residue = [n for n in os.listdir(os.path.join(world, "state"))
                   if n.endswith(DNA.TEMP_SUFFIX)]
        ok = (dry_ok and report["wrote"] is True
              and report["read_back_ok"] is True
              and report["before_bytes"] == len(before)
              and others_same and residue == []
              and after.endswith(FOOTER.encode("utf-8")))
    finally:
        drop_world(world)
    check(ok, "AC-DRNA4 atomic write and dry run")


def test_cli():
    """AC-DRNA5: CLI codes, one verdict word, byte-stable JSON."""
    world = make_world(HEADER + LEAD + OTHER + FOOTER)
    try:
        code_zero, out_zero = run_main(
            ["--item", "lead-row", "--marker", "j5:", "--text", "j5: text",
             "--root", world])
        word_ok = (out_zero.startswith("DEBT NOTE item=lead-row ")
                   and out_zero.count("DEBT NOTE") == 1)
        code_json, out_json = run_main(
            ["--item", "lead-row", "--marker", "j5:", "--text", "j5: text",
             "--root", world, "--json"])
        code_json2, out_json2 = run_main(
            ["--item", "lead-row", "--marker", "j5:", "--text", "j5: text",
             "--root", world, "--json"])
        code_two, _ = run_main(["--item", "ghost", "--marker", "k:", "--text",
                                "k: x", "--root", world])
        code_three, _ = run_main(["--item", "lead-row", "--marker", "k:",
                                  "--text", "k: x", "--root",
                                  os.path.join(world, "nope")])
        code_five, _ = run_main(["--bogus"])
        import json as J
        keys = list(J.loads(out_json).keys())
        ok = (code_zero == 0 and word_ok and code_json == 0
              and out_json == out_json2
              and keys == list(DNA.REPORT_KEYS)
              and code_two == 2 and code_three == 3 and code_five == 5
              and read_bytes(world) == (HEADER + LEAD + OTHER
                                        + FOOTER).encode("utf-8"))
    finally:
        drop_world(world)
    check(ok, "AC-DRNA5 CLI codes and pinned JSON")


def test_purity_and_registration():
    """AC-DRNA6: pure ASCII stdlib, no clock, no network, wired."""
    with open(os.path.join(BASE, "debt_note_append.py"), "rb") as handle:
        raw = handle.read()
    raw.decode("ascii")
    source = raw.decode("ascii")
    forbidden = ("import socket", "import urllib", "import http",
                 "import requests", "time.time", "datetime")
    ok = not any(token in source for token in forbidden)
    ok = ok and "import debt_register as DR" in source
    with open(RUNNER, "rb") as handle:
        runner = handle.read().decode("utf-8", "replace")
    ok = ok and LABEL in runner
    check(ok, "AC-DRNA6 purity and registration")


def main():
    test_note_grows_inside()
    test_refusals_write_nothing()
    test_post_refusal()
    test_atomic_and_dry()
    test_cli()
    test_purity_and_registration()
    verdict = "PASS" if FAILS == 0 and PASSES == EXPECTED_CRITERIA else "FAIL"
    print("SUITE %s %d/%d" % (verdict, PASSES, EXPECTED_CRITERIA))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())