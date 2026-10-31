"""stamp_exempt_append suite (R2307; criteria AC-SAP1..AC-SAP6 were
pre-registered inside the R2294 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: accepting a NEW closed row no longer means hand-editing a
380-entry JSON. The entry is rendered in the declaration's own shape, the
declaration's reader is the authority on whether that shape is accepted, the
live (queue, identity) join is the reviewer's own, three refusals land before
any byte of the real file changes, a dry run predicts the exact post size and
writes nothing, and an executed append is one atomic replace proved by a
read-back with no temp residue.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import queue_done_stamp_exempt as SEX  # noqa: E402
import stamp_exempt_review as SER  # noqa: E402
import stamp_exempt_append as SA  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "stamp_exempt_append.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-stamp-exempt-append"
CLI = os.path.join(BASE, "stamp_exempt_append.py")

PASSES = 0
FAILS = 0

OTHER = {"queue": "explore", "identity": "rowZ#99999999", "declared": "R2280",
         "reason": "fixture: accepted before this window"}


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def declaration_text(entries):
    """A declaration in the pinned on-disk style (one entry per indented line)."""
    lines = ["{", '  "note": "fixture declaration",', '  "exemptions": [']
    body = []
    for entry in entries:
        body.append("    " + json.dumps(entry, ensure_ascii=True,
                                        sort_keys=False))
    lines.append(",\n".join(body))
    lines.append("  ]")
    lines.append("}")
    return "\n".join(lines) + "\n"


def make_world(entries=None, raw=None):
    """A temp root carrying state/queue/stamp_exempt.json."""
    world = tempfile.mkdtemp(prefix="bigdomain-seap-w-")
    folder = os.path.join(world, "state", "queue")
    os.makedirs(folder)
    path = os.path.join(world, SA.DECL_REL)
    if raw is None:
        raw = declaration_text(entries if entries is not None else [OTHER])
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(raw)
    return world


def declared(entries=None):
    """The fixture declaration's entries in dict form."""
    return list(entries if entries is not None else [OTHER])


def live(pairs):
    """Patch the reviewer's join (never a second copy) for one leg."""
    def fake(root):
        return [], pairs
    return fake


def rows(*positions):
    return [{"file": "state/queue/tech.md", "line": pos, "queue": "tech",
             "identity": "rowA#11111111", "seed_round": "R2200"}
            for pos in positions]


def sha(path):
    with io.open(path, "rb") as handle:
        data = handle.read()
    import hashlib
    return hashlib.sha256(data).hexdigest()


def refused(fn):
    """Run fn and hand back its error code, or None when it did not refuse."""
    try:
        fn()
    except SA.StampExemptAppendError as exc:
        return exc.code
    return None


def ac_sap1():
    """The entry is rendered in the declaration's own shape, the reader rules."""
    entry = SA.render_entry("tech", "rowA#11111111", "R2307", "fixture reason")
    keys_ok = (list(entry.keys())
               == ["queue", "identity", "declared", "reason"])
    dated = SA.render_entry("tech", "rowA#11111111", "R2307", "reason",
                            "R2400")
    dated_ok = (list(dated.keys())
                == ["queue", "identity", "declared", "reason", "until"])
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    no_second_shape = ('"exemptions"' not in source
                       and "SEX.read_declaration" in source
                       and "SEX.ENTRY_KEYS" in source)
    world = make_world()
    try:
        text = io.open(os.path.join(world, SA.DECL_REL), encoding="utf-8",
                       newline="").read()
        entries = SA.declaration_entries(text)
        reader_counts = len(entries) == 1
        calls = {"n": 0}
        original = SEX.read_declaration

        def counting(root):
            calls["n"] += 1
            return original(root)

        SEX.read_declaration = counting
        try:
            SA.declaration_entries(text)
            used = calls["n"] >= 1
        finally:
            SEX.read_declaration = original

        def broken(root):
            raise SEX.QueueDoneStampExemptError("E_SEX_BAD_DECL", "broken")

        SEX.read_declaration = broken
        try:
            refused_code = refused(lambda: SA.declaration_entries(text))
        finally:
            SEX.read_declaration = original
        reader_is_authority = refused_code == "E_SEAP_BAD_ENTRY"
    finally:
        shutil.rmtree(world, ignore_errors=True)
    check(keys_ok and dated_ok and no_second_shape and reader_counts
          and used and reader_is_authority, "AC-SAP1")
    return keys_ok, dated_ok, no_second_shape, reader_counts, used, \
        reader_is_authority


def ac_sap2():
    """No live row, duplicate pair, ambiguous pair: each refused, no bytes."""
    pair = ("tech", "rowA#11111111")
    world = make_world()
    dup_world = make_world([{"queue": "tech",
                             "identity": "rowA#11111111",
                             "declared": "R2307",
                             "reason": "already here"}])
    path = os.path.join(world, SA.DECL_REL)
    dup_path = os.path.join(dup_world, SA.DECL_REL)
    try:
        before = sha(path)
        dup_before = sha(dup_path)
        original = SER.live_pairs
        SER.live_pairs = live({})
        try:
            no_row = refused(lambda: SA.append(world, "tech", pair[1],
                                              "R2307", "reason",
                                              execute=True))
        finally:
            SER.live_pairs = original
        after_no_row = sha(path)
        SER.live_pairs = live({pair: rows(11)})
        try:
            dup = refused(lambda: SA.append(dup_world, "tech", pair[1],
                                            "R2307", "reason", execute=True))
        finally:
            SER.live_pairs = original
        dup_after = sha(dup_path)
        SER.live_pairs = live({pair: rows(11, 12)})
        try:
            ambiguous = refused(lambda: SA.append(world, "tech", pair[1],
                                                 "R2307", "reason",
                                                 execute=True))
        finally:
            SER.live_pairs = original
        after_ambiguous = sha(path)
        no_residue = not any(name.endswith(SA.TEMP_SUFFIX)
                             for name in os.listdir(os.path.dirname(path)))
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(dup_world, ignore_errors=True)
    ok = (no_row == "E_SEAP_NO_ROW" and dup == "E_SEAP_DUP"
          and ambiguous == "E_SEAP_AMBIGUOUS" and before == after_no_row
          and before == after_ambiguous and dup_before == dup_after
          and no_residue)
    check(ok, "AC-SAP2")
    return no_row, dup, ambiguous, before == after_no_row, \
        dup_before == dup_after, no_residue


def ac_sap3():
    """Dry run by default: prediction in the report, zero bytes on disk."""
    pair = ("tech", "rowA#11111111")
    world = make_world()
    path = os.path.join(world, SA.DECL_REL)
    original = SER.live_pairs
    SER.live_pairs = live({pair: rows(11)})
    try:
        before = sha(path)
        size_before = os.path.getsize(path)
        report = SA.append(world, "tech", pair[1], "R2307", "reason")
        after = sha(path)
        dry_ok = (report["wrote"] is False and report["read_back_ok"] is None
                  and report["before_bytes"] == size_before
                  and report["entry_count_before"] == 1
                  and report["entry_count_after"] == 2
                  and report["entry_index"] == 2
                  and report["predicted_bytes"] > size_before
                  and before == after)
        executed = SA.append(world, "tech", pair[1], "R2307", "reason",
                             execute=True)
        predicted_matched = os.path.getsize(path) == report["predicted_bytes"]
        executed_ok = (executed["wrote"] is True
                       and executed["read_back_ok"] is True
                       and executed["predicted_bytes"]
                       == report["predicted_bytes"])
    finally:
        SER.live_pairs = original
        shutil.rmtree(world, ignore_errors=True)
    check(dry_ok and predicted_matched and executed_ok, "AC-SAP3")
    return dry_ok, predicted_matched, executed_ok


def ac_sap4():
    """Execute: one atomic replace, read-back proof, no residue, history kept."""
    pair = ("tech", "rowA#11111111")
    world = make_world()
    path = os.path.join(world, SA.DECL_REL)
    original = SER.live_pairs
    SER.live_pairs = live({pair: rows(11)})
    try:
        text = io.open(path, encoding="utf-8", newline="").read()
        marker = text.rfind("\n  ]")
        report = SA.append(world, "tech", pair[1], "R2307",
                           "closed after R2280 with a young stamp",
                           execute=True)
        raw = io.open(path, "rb").read()
        post = raw.decode("utf-8")
        entries = SA.declaration_entries(post)
        prefix_kept = post.startswith(text[:marker])
        last_ok = (entries[-1].get("queue") == "tech"
                   and entries[-1].get("identity") == "rowA#11111111"
                   and entries[-1].get("declared") == "R2307"
                   and entries[-1].get("reason")
                   == "closed after R2280 with a young stamp"
                   and entries[-1].get("until") is None)
        first_kept = entries[0].get("queue") == OTHER["queue"] and \
            entries[0].get("identity") == OTHER["identity"]
        no_residue = not any(name.endswith(SA.TEMP_SUFFIX)
                            for name in os.listdir(os.path.dirname(path)))
        counted = (len(entries) == 2 and report["entry_count_after"] == 2)
        one_replace = report["wrote"] is True and report["read_back_ok"] is True
    finally:
        SER.live_pairs = original
        shutil.rmtree(world, ignore_errors=True)
    ok = (prefix_kept and last_ok and first_kept and no_residue and counted
          and one_replace)
    check(ok, "AC-SAP4")
    return prefix_kept, last_ok, first_kept, no_residue, counted, one_replace


def ac_sap5():
    """A refused call writes nothing, and the CLI refuses the same way."""
    pair = ("tech", "rowA#11111111")
    world = make_world()
    path = os.path.join(world, SA.DECL_REL)
    original = SER.live_pairs
    SER.live_pairs = live({})
    try:
        before = sha(path)
        code = refused(lambda: SA.append(world, "tech", pair[1], "R2307",
                                         "reason", execute=True))
        after = sha(path)
        unchanged = before == after
    finally:
        SER.live_pairs = original
    missing = refused(
        lambda: SA.append(os.path.join(world, "nowhere"), "tech", pair[1],
                          "R2307", "reason"))
    cli_bad = subprocess.run([sys.executable, CLI, "--queue", "tech"],
                             capture_output=True)
    cli_missing = subprocess.run([sys.executable, CLI, "--root", world,
                                  "--queue", "tech", "--identity", pair[1],
                                  "--declared", "R2307", "--reason", "r"],
                                 capture_output=True)
    shutil.rmtree(world, ignore_errors=True)
    # The real world is unpinned for the CLI leg, so the refusal comes from the
    # reader rather than from the patched join; either way nothing is written.
    ok = (code == "E_SEAP_NO_ROW" and unchanged
          and missing == "E_SEAP_UNPINNED" and cli_bad.returncode == 5
          and cli_missing.returncode in (2, 3))
    check(ok, "AC-SAP5")
    return code, unchanged, missing, cli_bad.returncode, cli_missing.returncode


def ac_sap6():
    """Purity: ASCII, stdlib plus the two house imports, no clock, wired."""
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    try:
        source.encode("ascii")
        ascii_ok = True
    except UnicodeEncodeError:
        ascii_ok = False
    imports = set(re.findall(r"^(?:import|from)\s+([A-Za-z_][\w.]*)",
                             source, re.M))
    allowed = {"io", "json", "os", "shutil", "sys", "tempfile",
               "queue_done_stamp_exempt", "stamp_exempt_review"}
    imports_ok = imports <= allowed
    banned = ("time.time", "datetime", "urllib", "requests", "socket",
              "subprocess")
    no_clock = not any(token in source for token in banned)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner = handle.read()
    wired = ('"%s"' % LABEL) in runner
    check(ascii_ok and imports_ok and no_clock and wired, "AC-SAP6")
    return ascii_ok, imports_ok, no_clock, wired


def main():
    print("SUITE stamp_exempt_append (R2307) criteria=%d" % EXPECTED_CRITERIA,
          flush=True)
    ac_sap1()
    ac_sap2()
    ac_sap3()
    ac_sap4()
    ac_sap5()
    ac_sap6()
    print("SUITE RESULT passes=%d fails=%d criteria=%d"
          % (PASSES, FAILS, EXPECTED_CRITERIA), flush=True)
    return 0 if FAILS == 0 else 2


if __name__ == "__main__":
    sys.exit(main())