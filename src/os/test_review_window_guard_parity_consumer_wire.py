"""review_window_guard_parity_consumer_wire suite (R2397).

Criteria AC-RWPC1..AC-RWPC6 were pinned inside the R2387 seed row of
state/queue/tech.md BEFORE this module existed.

What this proves: R2387 gave the review-window parity the ability to tell an
informed agreement from a blind one, but nothing that ages entries ever asked
it. This suite pins that the acting path now asks, that a split and a blind
agreement REFUSE there with their own codes, that an informed agreement leaves
the acting path byte for byte what it was, and that no second law was written.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import contextlib
import ast
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import exempt_review as ER  # noqa: E402
import review_window_guard_parity_blind_agreement as RWGB  # noqa: E402
import review_window_guard_parity_consumer_wire as RWPC  # noqa: E402
import review_window_wire as RWW  # noqa: E402
import review_window_wire_argument_guard as RWAG  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "review_window_guard_parity_consumer_wire.py")
PREVIOUS = os.path.join(BASE,
                        "review_window_guard_parity_blind_agreement.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-review-window-guard-parity-consumer-wire"
WIRED_EXPECT = '"test_review_window_guard_parity_consumer_wire.py"), 6),'
REWIND = "E_RWHW_DECL_HISTORY"

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


def row(window, declared_by):
    return {"window": window, "declared_by": declared_by,
            "reason": "pinned window"}


def body(window, rows):
    return {
        "window": window,
        "declared_by": rows[-1]["declared_by"],
        "reason": "pinned so it can only move through a new row",
        "declarations": rows,
    }


def exemption(queue, identity, declared):
    return {"queue": queue, "identity": identity, "declared": declared,
            "reason": "accepted as it stands"}


def make_world(payload=None, raw=None, no_window=False, entries=None):
    """A temp root carrying state/review_window.json and a prefix_exempt."""
    world = tempfile.mkdtemp(prefix="bigdomain-rwpc-")
    if not no_window:
        inner = os.path.join(world, "state")
        os.makedirs(inner)
        text = raw if raw is not None else json.dumps(payload, indent=2)
        with io.open(os.path.join(inner, "review_window.json"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    if entries is not None:
        inner = os.path.join(world, "state", "queue")
        if not os.path.isdir(inner):
            os.makedirs(inner)
        with io.open(os.path.join(inner, "prefix_exempt.json"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps({"exemptions": entries}, indent=2))
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def digest_tree(root):
    digest = hashlib.sha256()
    for base, _dirs, files in os.walk(root):
        for name in sorted(files):
            path = os.path.join(base, name)
            digest.update(os.path.relpath(path, root).encode("utf-8"))
            with io.open(path, "rb") as handle:
                digest.update(handle.read())
    return digest.hexdigest()


def run_main(argv):
    """Call main() in-process so a patched reading can move the answer."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = RWPC.main(argv)
    return code, buf.getvalue()


def refusal(call):
    try:
        call()
    except RWPC.ReviewWindowParityConsumerError as exc:
        return exc.code, exc.detail
    return None, None


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def main():
    worlds = []
    saved_blind = RWGB.check
    try:
        clean = make_world(body(20, [row(20, "R2300")]),
                           entries=[exemption("tech", "seed-a", "R2290")])
        moved = make_world(body(20, [row(10, "R2300"), row(20, "R2310")]))
        blind = make_world(raw="{not json")
        worlds.extend([clean, moved, blind])

        # ---- AC-RWPC1: the shipped reading is asked at CALL time ---------
        source = read_text(MODULE)
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        clean_found = RWPC.reading(clean)
        base_clean = RWGB.check(clean)
        patched_seen = []

        def patched_check(root, round_text=None):
            patched_seen.append((root, round_text))
            raise RuntimeError("reading is patched")

        RWGB.check = patched_check
        try:
            patched_found = RWPC.reading(clean, "R2397")
        finally:
            RWGB.check = saved_blind
        restored = RWPC.reading(clean)
        check(clean_found["verdict"] == RWPC.VERDICT_CLEAN
              and clean_found["parity"] == base_clean["verdict"]
              and clean_found["window"] == base_clean["declared_window"]
              and clean_found["code"] is None
              and patched_seen
              and patched_seen[0] == (clean, "R2397")
              and patched_found["verdict"] == RWPC.VERDICT_UNKNOWN
              and patched_found["code"] == RWPC.UNREADABLE_CODE
              and restored == clean_found
              and "RWGB.check(" in source
              and tuple(imported) == ("json", "os", "sys",
                                  "review_window_guard_parity_blind"
                                  "_agreement")
              and '.get("declared_by")' not in source,
              "AC-RWPC1 the consumer asks RWGB.check at call time - a patched "
              "reading moves its verdict to UNKNOWN, the same call is restored "
              "byte-identically, the module imports nothing but that one law, "
              "and no second rewind comparison or declared_by read lives here")

        # ---- AC-RWPC2: a split refuses naming BOTH faces -----------------
        def split_reading(root, round_text=None):
            return {"verdict": RWGB.VERDICT_DISAGREES,
                    "ignorance": RWGB.IGNORANCE_NONE,
                    "declared": "REFUSED",
                    "declared_code": REWIND,
                    "declared_window": None,
                    "argument": "ARGUMENT-CLEAN",
                    "argument_code": None,
                    "agrees": False}

        RWGB.check = split_reading
        try:
            split_found = RWPC.reading(clean)
            split_code, split_detail = refusal(lambda: RWPC.guard(clean))
            code_split, out_split = run_main(["--check", "--root", clean])
        finally:
            RWGB.check = saved_blind
        check(split_found["verdict"] == RWPC.VERDICT_SPLIT
              and split_found["code"] == RWPC.SPLIT_CODE
              and split_code == "E_RWPC_SPLIT"
              and REWIND in split_detail
              and "ARGUMENT-CLEAN" in split_detail
              and code_split == 2
              and "E_RWPC_SPLIT" in out_split
              and "verdict=WINDOW-SPLIT" in out_split,
              "AC-RWPC2 a split refuses with its own E_RWPC_SPLIT naming both "
              "faces' codes, and the CLI exits 2 where the clean world exits 0")

        # ---- AC-RWPC3: a blind agreement refuses, with a DIFFERENT word ---
        blind_found = RWPC.reading(blind)
        blind_code, blind_detail = refusal(lambda: RWPC.guard(blind))
        code_blind, out_blind = run_main(["--check", "--root", blind])
        one_side = make_world(raw="{also not json")
        worlds.append(one_side)

        def declared_blind(root, round_text=None):
            return {"verdict": RWGB.VERDICT_UNKNOWN,
                    "ignorance": RWGB.IGNORANCE_BOTH,
                    "declared": "REFUSED",
                    "declared_code": "E_RWW_UNREADABLE",
                    "declared_window": None,
                    "argument": RWGB.unknown_word(),
                    "argument_code": "E_RWW_UNREADABLE",
                    "agrees": False}

        RWGB.check = declared_blind
        try:
            both_found = RWPC.reading(one_side)
        finally:
            RWGB.check = saved_blind
        check(blind_found["verdict"] == RWPC.VERDICT_UNKNOWN
              and blind_found["code"] == RWPC.UNKNOWN_CODE
              and blind_code == "E_RWPC_UNKNOWN"
              and "ignorance=" in blind_detail
              and blind_code != split_code
              and RWPC.VERDICT_UNKNOWN != RWPC.VERDICT_SPLIT
              and "PARITY-UNKNOWN" not in blind_code
              and "ignorance=both" in both_found["detail"]
              and code_blind == 2
              and "E_RWPC_UNKNOWN" in out_blind,
              "AC-RWPC3 a blind agreement refuses with E_RWPC_UNKNOWN - a "
              "different word from the split's - naming the ignorant side(s) "
              "it measured, and the CLI exits 2")

        # ---- AC-RWPC4: an informed agreement changes NOTHING ---------------
        before_digest = digest_tree(clean)
        guarded_window = RWW.declared_window(clean, "R2397")
        guarded_report = ER.audit(clean, "R2397", window_source="declaration")
        saved_guard = RWPC.guard

        def no_guard(root, round_text=None):
            return None

        RWPC.guard = no_guard
        try:
            plain_window = RWW.declared_window(clean, "R2397")
            plain_report = ER.audit(clean, "R2397",
                                    window_source="declaration")
        finally:
            RWPC.guard = saved_guard
        after_digest = digest_tree(clean)
        check(guarded_window == plain_window == 20
              and ER.one_line(guarded_report) == ER.one_line(plain_report)
              and ER.render_json(guarded_report) == ER.render_json(plain_report)
              and guarded_report["window"] == 20
              and before_digest == after_digest,
              "AC-RWPC4 on an informed agreement the acting path is byte "
              "identical with the guard installed and with it patched out - "
              "window 20 either way, the same rendered and JSON report, and an "
              "unchanged tree digest")

        # ---- AC-RWPC5: codes and keys extend, shipped words unrenamed ------
        json_one = run_main(["--check", "--root", clean, "--json"])
        json_two = run_main(["--check", "--root", clean, "--json"])
        keys = tuple(json.loads(json_one[1]).keys())
        code_root, _ = run_main(["--check", "--root",
                                 os.path.join(clean, "nope")])
        code_flag, _ = run_main(["--check", "--nope"])
        code_missing, out_missing = run_main(["--root", clean])
        shipped_suffixes = ("_UNREADABLE", "_BAD_SHAPE")
        check(json_one[0] == 0 and json_one == json_two
              and keys == RWPC.REPORT_KEYS
              and code_root == 3
              and code_flag == 5
              and code_missing == 5
              and RWPC.SPLIT_CODE == "E_RWPC_SPLIT"
              and RWPC.UNKNOWN_CODE == "E_RWPC_UNKNOWN"
              and all(RWPC.SPLIT_CODE != RWPC.GUARD_PREFIX + suffix
                      for suffix in shipped_suffixes)
              and RWPC.VERDICT_CLEAN == "WINDOW-CLEAN"
              and RWPC.VERDICT_SPLIT == "WINDOW-SPLIT"
              and RWPC.VERDICT_UNKNOWN == "WINDOW-UNKNOWN"
              and RWGB.IGNORANCE_NONE == "none",
              "AC-RWPC5 the report carries this face's pinned key order and is "
              "byte-stable across runs, the CLI keeps 0/2/3/5, and the new "
              "codes and verdicts are additions that rename none of the shipped "
              "words (ignorance vocabulary still read from its owner)")

        # ---- AC-RWPC6: pure, wired, ASCII, stdlib only --------------------
        runner_text = read_text(RUNNER)
        raw = open(MODULE, "rb").read()
        pure = ("import json" in source and "import os" in source
                and "import sys" in source
                and "socket" not in source
                and "urllib" not in source
                and "requests" not in source
                and "time." not in source
                and "datetime" not in source)
        check(raw == raw.decode("ascii").encode("ascii")
              and pure
              and WIRED_EXPECT in runner_text
              and LABEL in runner_text
              and os.path.exists(MODULE)
              and os.path.exists(PREVIOUS)
              and RWPC.REPORT_KEYS[0] == "verdict",
              "AC-RWPC6 the module is pure ASCII, stdlib only, imports no "
              "network and reads no clock, and its reconcile label %s is "
              "wired for six criteria" % LABEL)
    finally:
        RWGB.check = saved_blind
        for world in worlds:
            drop_world(world)

    print("SUITE %s criteria=%d pass=%d fail=%d"
          % (LABEL, EXPECTED_CRITERIA, PASSES, FAILS))
    if FAILS:
        print("SUITE FAIL")
        return 1
    print("SUITE PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())