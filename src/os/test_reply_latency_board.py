"""Battery suite for tools/reply_latency_board.py - AC-RRLB1..6.

WHY THIS SUITE EXISTS (measured at R3425, not assumed):
api_rating_reply_latency shipped with its own AC-RRL1..8 criteria
(src/sandbox/ledger/test_apimarket_ratingreplylatency.py on disk) but a git
grep over tools/ and preview/ answered rc=1 with zero hits, so the seller's own
question - "how long did a rating sit before I answered it, and what is still
owed" - could not be opened by anyone. The seller quality scorecard (R3401)
reads the star shape and the seller monthly rating page reads a month
histogram; neither shows the waiting time or the unanswered queue. R3425
renders one market section plus one section per seller on one page; this suite
grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3425 PIN
BEFORE the driver existed):
  AC-RRLB1 the page and its json land, the json carries exactly the pinned
           payload key set, the market block and every seller block carry the
           shipped 13-key envelope, every rating row carries the shipped 13
           keys, seller_count equals the block count, the report points at a
           file that exists, and the four source fingerprints are recorded.
  AC-RRLB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates sellers through the shipped board
           face, reads api_rating_reply_latency() once for the market and once
           per seller, and requires the page json's market and sellers
           (including every rating row and the disclaimer) to equal that
           reading item for item - no typed fixture.
  AC-RRLB3 the face's identities hold: rating count equals the row count, the
           replied count equals the rows that carry a latency, the owed count
           is the difference, the coverage recomputes and is None rather than a
           fabricated zero when the denominator is zero, the mean and the
           exact odd/even median recompute over answered rows only, the two
           extremes recompute, the two stamps recompute (latest reply from
           answered rows, oldest owed from pending rows), every row's replied
           flag agrees with both its reply stamp and its reply id, an answered
           row's latency recomputes from the two stored stamps, the rows keep
           the face's own order (answered slowest first, then pending by rated
           stamp), and the market envelope carries no seller account.
  AC-RRLB4 the page reads honestly: one market section and one marked section
           per seller, an undefined latency, coverage or median printed as the
           dash instead of a zero, every owed rating carrying the named pending
           badge, no bare None, a latency bar the page calls a width and not a
           share - absent on every owed row of this world and proved by two
           in-memory probes: an empty scope printing the dash and the explicit
           empty sentence, and an answered envelope printing its seconds and
           its bar.
  AC-RRLB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-RRLB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with AC-RRL arms.

Read-only over the repository: the provenance world is built in a temp dir and
the probes render in memory, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "reply_latency_board.py")
HTML = os.path.join(ROOT, "preview", "reply-latency-board.html")
JSONF = os.path.join(ROOT, "preview", "reply-latency-board.json")
COPY = os.path.join(ROOT, "preview", "reply-latency-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_ratingreplylatency.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-reply-latency-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "source_face", "scope",
    "seller_count", "market", "sellers", "disclaimer", "report", "sources",
    "sizes",
}
ENVELOPE_KEYS = {
    "dev_account", "rating_count", "replied_count", "unreplied_count",
    "reply_coverage", "avg_seconds", "median_seconds", "fastest_seconds",
    "slowest_seconds", "latest_reply_utc", "oldest_unreplied_utc",
    "rows", "disclaimer",
}
ROW_KEYS = {
    "rating_id", "listing_id", "listing_key", "title", "dev_account",
    "buyer_id", "stars", "rated_utc", "replied", "reply_id", "replied_utc",
    "reply_text", "latency_seconds",
}

CHECKS = []
FAILS = []


def ok(name, cond, detail):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def stamp(path):
    if not os.path.exists(path):
        return None
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def run_tool(args, cwd=ROOT):
    proc = subprocess.run(
        [sys.executable, TOOL] + args, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def live_world():
    """The shipped face's own reading over the suite's throwaway demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="rrlb-suite-")
    db = os.path.join(tmp_root, "rrlb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        sellers = sorted({str(row["dev_account"]) for row in board["listings"]})
        market = dict(am.api_rating_reply_latency())
        scoped = [dict(am.api_rating_reply_latency(seller))
                  for seller in sellers]
        return market, scoped, market["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("rrlb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def elapsed(rated, replied):
    if replied is None:
        return None
    import datetime
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return int((datetime.datetime.strptime(str(replied), fmt)
                - datetime.datetime.strptime(str(rated), fmt)).total_seconds())


def want_median(values):
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def order_of(row):
    if row["latency_seconds"] is not None:
        return (0, -int(row["latency_seconds"]), int(row["rating_id"]))
    return (1, str(row["rated_utc"]), int(row["rating_id"]))


def envelope_problems(envelope, label):
    problems = []
    rows = envelope["rows"]
    count = int(envelope["rating_count"])
    answered = [row for row in rows if row["latency_seconds"] is not None]
    pending = [row for row in rows if row["latency_seconds"] is None]
    replied = int(envelope["replied_count"])
    if count != len(rows):
        problems.append("%s count != rows" % label)
    if replied != len(answered):
        problems.append("%s replied != answered" % label)
    if int(envelope["unreplied_count"]) != count - replied:
        problems.append("%s owed != count - replied" % label)
    want_coverage = round(float(replied) / count, 4) if count else None
    if not close(envelope["reply_coverage"], want_coverage):
        problems.append("%s coverage" % label)
    latencies = [int(row["latency_seconds"]) for row in answered]
    for key, want in (
            ("fastest_seconds", min(latencies) if latencies else None),
            ("slowest_seconds", max(latencies) if latencies else None),
            ("avg_seconds", float(sum(latencies)) / len(latencies)
             if latencies else None),
            ("median_seconds", want_median(latencies))):
        if not close(envelope[key], want):
            problems.append("%s %s" % (label, key))
    stamps = [str(row["replied_utc"]) for row in answered]
    owed = [str(row["rated_utc"]) for row in pending]
    if envelope["latest_reply_utc"] != (max(stamps) if stamps else None):
        problems.append("%s latest stamp" % label)
    if envelope["oldest_unreplied_utc"] != (min(owed) if owed else None):
        problems.append("%s oldest owed" % label)
    for row in rows:
        tag = "%s/%s" % (label, row["rating_id"])
        if bool(row["replied"]) != (row["replied_utc"] is not None):
            problems.append("%s flag vs stamp" % tag)
        if bool(row["replied"]) != (row["reply_id"] is not None):
            problems.append("%s flag vs reply_id" % tag)
        if row["replied"] and row["latency_seconds"] is None:
            problems.append("%s answered without latency" % tag)
        if not row["replied"] and row["latency_seconds"] is not None:
            problems.append("%s pending with latency" % tag)
        if row["replied"] and int(row["latency_seconds"]) != elapsed(
                row["rated_utc"], row["replied_utc"]):
            problems.append("%s latency recompute" % tag)
    if [order_of(row) for row in rows] != sorted(order_of(row) for row in rows):
        problems.append("%s row order" % label)
    return problems


def zero_envelope(dev_account=None):
    return {
        "dev_account": dev_account, "rating_count": 0, "replied_count": 0,
        "unreplied_count": 0, "reply_coverage": None, "avg_seconds": None,
        "median_seconds": None, "fastest_seconds": None,
        "slowest_seconds": None, "latest_reply_utc": None,
        "oldest_unreplied_utc": None, "rows": [],
        "disclaimer": "probe disclaimer",
    }


def answered_envelope():
    """A probe envelope carrying two answered rows and one owed row."""
    rows = [
        {"rating_id": 1, "listing_id": 1, "listing_key": "aaa",
         "title": "Probe A", "dev_account": "usr:probe", "buyer_id": "usr:b1",
         "stars": 5, "rated_utc": "2026-01-01T00:00:00Z", "replied": True,
         "reply_id": 1, "replied_utc": "2026-01-01T01:00:00Z",
         "reply_text": "thanks", "latency_seconds": 7200},
        {"rating_id": 2, "listing_id": 2, "listing_key": "bbb",
         "title": "Probe B", "dev_account": "usr:probe", "buyer_id": "usr:b2",
         "stars": 4, "rated_utc": "2026-01-01T00:00:00Z", "replied": True,
         "reply_id": 2, "replied_utc": "2026-01-01T01:00:00Z",
         "reply_text": "noted", "latency_seconds": 3600},
        {"rating_id": 3, "listing_id": 3, "listing_key": "ccc",
         "title": "Probe C", "dev_account": "usr:probe", "buyer_id": "usr:b3",
         "stars": 3, "rated_utc": "2026-01-01T00:00:00Z", "replied": False,
         "reply_id": None, "replied_utc": None, "reply_text": None,
         "latency_seconds": None},
    ]
    return {
        "dev_account": None, "rating_count": 3, "replied_count": 2,
        "unreplied_count": 1, "reply_coverage": 0.6667, "avg_seconds": 5400.0,
        "median_seconds": 5400.0, "fastest_seconds": 3600,
        "slowest_seconds": 7200, "latest_reply_utc": "2026-01-01T01:00:00Z",
        "oldest_unreplied_utc": "2026-01-01T00:00:00Z", "rows": rows,
        "disclaimer": "probe disclaimer",
    }


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    market = doc.get("market") or {}
    sellers = doc.get("sellers") or []
    all_rows = list(market.get("rows") or []) + [
        row for block in sellers for row in (block.get("rows") or [])]

    # ---- AC-RRLB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelopes_ok = (set(market.keys()) == ENVELOPE_KEYS
                    and all(set(block.keys()) == ENVELOPE_KEYS
                            for block in sellers))
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in all_rows)
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-RRLB1", landed and keys == PAYLOAD_KEYS and envelopes_ok and rows_ok
       and sources_ok and bool(sellers)
       and int(doc.get("seller_count", -1)) == len(sellers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelopes=%s rows=%s "
       "sources=%s count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelopes_ok, rows_ok, sources_ok,
          len(sellers), int(doc.get("seller_count", -1)), report_ok))

    # ---- AC-RRLB2: every printed number is the shipped face's own.
    live_market, live_sellers, live_disclaimer = live_world()
    market_same = json.dumps(market, sort_keys=True) == json.dumps(
        {key: live_market[key] for key in ENVELOPE_KEYS}, sort_keys=True)
    sellers_same = json.dumps(sellers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in ENVELOPE_KEYS} for block in live_sellers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    live_rows = len(live_market["rows"]) + sum(
        len(block["rows"]) for block in live_sellers)
    ok("AC-RRLB2", market_same and sellers_same and disc_same and bool(sellers),
       "market_same=%s sellers_same=%s disclaimer_same=%s sellers=%d rows=%d"
       % (market_same, sellers_same, disc_same, len(sellers), live_rows))

    # ---- AC-RRLB3: the face's identities hold on these envelopes.
    problems = envelope_problems(market, "market") if market else ["no market"]
    if market:
        if market.get("dev_account") is not None:
            problems.append("market dev_account")
    for block in sellers:
        name = str(block["dev_account"])
        problems.extend(envelope_problems(block, name))
        if not name.startswith("usr:"):
            problems.append("%s account" % name)
    ok("AC-RRLB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-RRLB4: honest page face, dashes, width bar, two probes.
    dash = labels.get("none", "-")
    sellers_marked = all(('data-seller="%s"' % block["dev_account"]) in page
                         for block in sellers)
    rows_marked = all(('data-rating="%s"' % row["rating_id"]) in page
                      for row in all_rows)
    owed = [row for row in all_rows if not row["replied"]]
    owed_badges = page.count(labels.get("badge_pending", "")) >= len(owed) > 0
    landed_bars = page.count("<div class=bar>")
    answered_landed = sum(1 for row in all_rows
                          if row["latency_seconds"] is not None)
    bars_honest = landed_bars == answered_landed
    no_none = ">None<" not in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_split", "law_coverage", "law_avg", "law_median",
             "law_extremes", "law_stamps", "law_row", "law_order", "law_scope",
             "law_bar", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    zero_ok = answered_ok = False
    try:
        driver = load_driver()
        zero_html = driver.build_html(zero_envelope(), [], labels,
                                      "2026-01-01 00:00:00Z",
                                      "probe disclaimer")
        zero_ok = (zero_html.count("<div class=bar>") == 0
                   and ">None<" not in zero_html
                   and dash in zero_html
                   and labels.get("empty_scope", "") in zero_html)
        answered_html = driver.build_html(answered_envelope(), [], labels,
                                          "2026-01-01 00:00:00Z",
                                          "probe disclaimer")
        answered_ok = (answered_html.count("<div class=bar>") == 2
                       and "3600" in answered_html
                       and "7200" in answered_html
                       and ">None<" not in answered_html
                       and labels.get("badge_replied", "") in answered_html
                       and labels.get("badge_pending", "") in answered_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-RRLB4", sellers_marked and rows_marked and owed_badges
       and bars_honest and no_none and laws_ok and zero_ok and answered_ok,
       "sellers=%s rows=%s owed_badges=%s bars=%d/%d laws=%s zero_probe=%s "
       "answered_probe=%s bare_none=%s"
       % (sellers_marked, rows_marked, owed_badges, landed_bars,
          answered_landed, laws_ok, zero_ok, answered_ok, not no_none))

    # ---- AC-RRLB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-RRLB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-RRLB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-RRL" in read(FACE_SUITE)
    ok("AC-RRLB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
