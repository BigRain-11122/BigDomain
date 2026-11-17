"""journey demo face suite (R2877; criteria AC-JDN1..AC-JDN6 were pinned in
state/queue/tech.md as the R2840-b seed row BEFORE this code existed).

What this proves: tools/journey_demo.py walks the 19.9 CNY journey end to end
and, until now, its pass line was read only by a human - a regression inside
the walk would surface as a shorter log rather than a red leg. This suite
re-derives the face's step order from the shipped spec, re-reads every step
artefact from disk, re-does the money arithmetic in integer cents, drives the
abort paths in a private world, and leaves the tracked preview pair byte- and
mtime-identical.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
TOOL = os.path.join(REPO, "tools", "journey_demo.py")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
PAY = os.path.join(REPO, "preview", "payment-gate-report.json")
LABEL = "os-journey-demo-face"
EXPECTED_CRITERIA = 6

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s %s" % (label, ""), flush=True)
    else:
        FAILS += 1
        print("FAIL %s %s" % (label, ""), flush=True)


def sig(path):
    if not os.path.exists(path):
        return ("absent", 0)
    with open(path, "rb") as handle:
        value = hashlib.sha256(handle.read()).hexdigest()
    return (value, os.stat(path).st_mtime_ns)


def load_tool():
    spec = importlib.util.spec_from_file_location("journey_demo_probe", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sized_doc(jd, preview):
    """Build a doc the way the tool does, against an explicit preview dir."""
    spec_text = jd.read_text(jd.SPEC)
    return jd.build_doc({"html": 0, "json": 0}, jd.sha256_text(spec_text),
                        len(spec_text.encode("utf-8")))


def patch_world(jd, world):
    saved = (jd.PREVIEW, jd.OUT_HTML, jd.OUT_JSON)
    jd.PREVIEW = world
    jd.OUT_HTML = os.path.join(world, "journey-19.9.html")
    jd.OUT_JSON = os.path.join(world, "journey-19.9.json")
    return saved


def restore_world(jd, saved):
    jd.PREVIEW, jd.OUT_HTML, jd.OUT_JSON = saved


def run_main(jd, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = jd.main(argv)
    return code, buf.getvalue()


def main():
    real_html = os.path.join(REPO, "preview", "journey-19.9.html")
    real_json = os.path.join(REPO, "preview", "journey-19.9.json")
    before = {p: sig(p) for p in (real_html, real_json)}

    jd = load_tool()
    title, header, spec_steps, compliance = jd.parse_spec()
    spec_ids = [cells[0].split()[0] for cells in spec_steps]
    steps = jd.build_steps(spec_steps)
    step_ids = [step["id"] for step in steps]

    # AC-JDN1 step order pinned: the spec table, the parsed rows and the built
    # steps agree on JV-1..JV-8 in that order, the carrier table covers exactly
    # those ids, and build_steps FOLLOWS the rows it is given rather than
    # sorting them (proved by feeding the rows reversed).
    expected_ids = ["JV-%d" % index for index in range(1, 9)]
    reversed_ids = [step["id"] for step in jd.build_steps(list(reversed(spec_steps)))]
    check(
        spec_ids == expected_ids and step_ids == expected_ids
        and sorted(jd.CARRIER_BY_STEP) == sorted(expected_ids)
        and reversed_ids == list(reversed(expected_ids))
        and len(steps) == 8 and bool(title) and len(header) > 1,
        "AC-JDN1 step order pinned: spec=%s built=%s carriers=%d reversed_follows=%s"
        % (spec_ids == expected_ids, step_ids == expected_ids,
           len(jd.CARRIER_BY_STEP), reversed_ids == list(reversed(expected_ids))),
    )

    # AC-JDN2 each step artefact exists: every carrier a step names is either on
    # disk with the byte count and mtime the face published, or honestly read as
    # MISSING - a green cannot be manufactured from an absent file.
    present, absent, drift = [], [], []
    for step in steps:
        stem = step["carrier"]
        path = os.path.join(jd.PREVIEW, stem + ".json")
        fresh = jd.carrier_state(stem)
        if os.path.exists(path):
            present.append(stem)
            if fresh.get("bytes") != os.path.getsize(path) or not fresh.get("mtime_utc"):
                drift.append(stem)
            if step["verdict"] != fresh.get("verdict") or step["ok"] is not fresh.get("ok"):
                drift.append(stem + ":verdict")
        else:
            absent.append(stem)
            if fresh.get("verdict") != "MISSING" or fresh.get("ok") is not False:
                drift.append(stem + ":not-missing")
    check(
        not drift and len(set(present) | set(absent)) >= 5,
        "AC-JDN2 step artefacts: present=%d %s absent=%d %s drift=%s"
        % (len(set(present)), sorted(set(present)), len(set(absent)),
           sorted(set(absent)) or "none", drift or "none"),
    )

    # AC-JDN3 money arithmetic re-derived: the carrier prices are integer cents,
    # the 19.9 pack is exactly 1990, the yuan figure is re-derived from cents by
    # integer division, and the tool carries no float money path at all.
    prices = {}
    if os.path.exists(PAY):
        with io.open(PAY, "r", encoding="utf-8") as handle:
            pay_doc = json.load(handle)
        prices = {row.get("id"): row.get("price_cent")
                  for row in pay_doc.get("products", []) if isinstance(row, dict)}
    ints_only = bool(prices) and all(
        isinstance(value, int) and not isinstance(value, bool) and value > 0
        for value in prices.values())
    cents = prices.get("pack_compute_19_9")
    yuan, fen = (cents // 100, cents % 100) if isinstance(cents, int) else (None, None)
    ladder = [prices.get("pack_compute_19_9"), prices.get("tier_patron_30d")]
    ladder_ok = all(isinstance(v, int) for v in ladder) and 1990 in ladder and 2990 in ladder
    with io.open(TOOL, "r", encoding="utf-8", errors="replace") as handle:
        tool_src = handle.read()
    no_float = "float(" not in tool_src and "round(" not in tool_src
    check(
        ints_only and cents == 1990 and (yuan, fen) == (19, 90)
        and ladder_ok and no_float,
        "AC-JDN3 money re-derived: products=%d int_cents=%s pack=%s yuan=%s.%02d ladder=%s float_path=%s"
        % (len(prices), ints_only, cents, yuan, fen or 0, ladder_ok, not no_float),
    )

    # AC-JDN4 abort paths reported: in an empty world every step reads MISSING
    # and the face still renders; a declared blocked_on list reaches the page.
    world = tempfile.mkdtemp(prefix="bigdomain-jdn-")
    try:
        saved = patch_world(jd, world)
        try:
            empty_doc = sized_doc(jd, world)
            empty_page = jd.render_html(empty_doc)
            with io.open(os.path.join(world, "payment-gate-report.json"), "w",
                         encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps({"blocked_on": ["CEO physical item: jdn probe"]},
                                        ensure_ascii=False))
            blocked_doc = sized_doc(jd, world)
            blocked_page = jd.render_html(blocked_doc)
        finally:
            restore_world(jd, saved)
    finally:
        shutil.rmtree(world, ignore_errors=True)
    # Two defects were repaired here at the birth site after the first honest
    # read: (1) "and empty_doc['steps']" returned the LIST of step dicts rather
    # than a bool, so the %s label printed every Chinese step string and the
    # suite died on a GBK console (UnicodeEncodeError on U+00A5) instead of
    # reporting a verdict - a bool() fixes the value AND keeps the line ASCII;
    # (2) an empty world legitimately reddens the tool's own AC-JNY8 (carriers
    # absent), so AC-JDN5 must populate its private world with the real carriers
    # before asserting that publish-then-check agrees.
    empty_all_missing = bool(empty_doc["steps"]) and all(
        step["verdict"] == "MISSING" and step["ok"] is False
        for step in empty_doc["steps"])
    no_false_green = all(step["ok"] is not True for step in empty_doc["steps"])
    check(
        empty_all_missing and no_false_green and "JV-8" in empty_page
        and blocked_doc["blocked_on"] == ["CEO physical item: jdn probe"]
        and "CEO physical item: jdn probe" in blocked_page
        and empty_doc["blocked_on"] == [],
        "AC-JDN4 abort paths: empty_world steps=%d all_missing=%s page_kept=%s blocked_on_surfaced=%s"
        % (len(empty_doc["steps"]), empty_all_missing, "JV-8" in empty_page,
           "CEO physical item: jdn probe" in blocked_page),
    )

    # AC-JDN5 purity: --check authors nothing on the real tree (bytes and mtime
    # identical), and a publish-then-check inside a private world leaves that
    # world's pair identical too.
    real_code, real_text = run_main(jd, ["--check"])
    mid = {p: sig(p) for p in (real_html, real_json)}
    world2 = tempfile.mkdtemp(prefix="bigdomain-jdn2-")
    try:
        # The private world must contain the real carriers, otherwise the tool
        # is RIGHT to refuse a green (AC-JNY8 reads every carrier as absent) and
        # the leg would be asserting a green the product must not give.
        for _stem in sorted(jd.CARRIER_BY_STEP.values()):
            _source = os.path.join(REPO, "preview", _stem + ".json")
            if os.path.exists(_source):
                shutil.copy2(_source, os.path.join(world2, _stem + ".json"))
        saved = patch_world(jd, world2)
        try:
            write_code, _write_text = run_main(jd, [])
            published = {p: sig(p) for p in (jd.OUT_HTML, jd.OUT_JSON)}
            check_code, _check_text = run_main(jd, ["--check"])
            rechecked = {p: sig(p) for p in (jd.OUT_HTML, jd.OUT_JSON)}
        finally:
            restore_world(jd, saved)
    finally:
        shutil.rmtree(world2, ignore_errors=True)
    after = {p: sig(p) for p in (real_html, real_json)}
    check(
        real_code == 0 and "VERDICT PASS" in real_text
        and mid == before and after == before
        and write_code == 0 and len(published) == 2 and check_code == 0
        and rechecked == published,
        "AC-JDN5 purity: real --check rc=%d pair_unchanged=%s temp publish rc=%d recheck rc=%d stable=%s"
        % (real_code, after == before, write_code, check_code, rechecked == published),
    )

    # AC-JDN6 wiring: registered in the battery with six criteria and named in
    # the matrix, so this face cannot lose its guard without a red leg.
    wired = False
    with io.open(RUNNER, "r", encoding="utf-8", errors="replace") as handle:
        wired = ('"test_journey_demo.py"), %d),' % EXPECTED_CRITERIA) in handle.read()
    in_matrix = False
    if os.path.exists(MATRIX):
        with io.open(MATRIX, "r", encoding="utf-8", errors="replace") as handle:
            in_matrix = LABEL in handle.read()
    check(wired and in_matrix,
          "AC-JDN6 wiring: %s registered with %d criteria and named in the matrix"
          % (LABEL, EXPECTED_CRITERIA))

    print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL", PASSES, PASSES + FAILS),
          flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
