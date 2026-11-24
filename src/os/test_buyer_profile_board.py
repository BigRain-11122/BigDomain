"""Battery suite for tools/buyer_profile_board.py - AC-BPFB1..6.

WHY THIS SUITE EXISTS (measured at R3430, not assumed):
api_buyer_profile shipped with its own AC-AMBY1..8 criteria
(src/sandbox/ledger/test_apimarket_buyerprofile.py on disk) but a git grep
over tools/ and preview/ answered rc=1 with zero hits, so the resident's own
question - "what has this account spent, got back, and how did the money
split" - could not be opened by anyone. api_seller_ledger and
api_buyer_ledger print row-level ledgers and no page summed one account.
R3430 renders the market row plus one card per buyer; this suite grades the
page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3430 PIN
BEFORE the driver existed):
  AC-BPFB1 the page and its json land, the json carries exactly the pinned
           payload key set, every buyer block carries the shipped 17-key
           envelope, the market block carries the same envelope minus the
           account identity, buyer_count equals the block count, the report
           points at a file that exists, and the four source fingerprints
           are recorded.
  AC-BPFB2 the data is the shipped face's own: the suite builds its own
           throwaway demo world, enumerates buyers through the shipped board
           and sales faces, reads api_buyer_profile() per buyer, and requires
           the page json's buyers (including the disclaimer) to equal that
           reading item for item - no typed fixture.
  AC-BPFB3 the face's identities hold: net spend is gross minus refunded,
           purchases split into net purchases plus refunds, the two pool
           legs add up to net spend, live watches never exceed watches, a
           zero rating count forces a null average and a positive count
           forces a defined one inside [0,5], the two purchase stamps exist
           exactly when the account has trade and run forward, buyer ids are
           unique and resident-shaped, and the market row is the column sum
           of every buyer with a rating-count-weighted average and honest
           extremes.
  AC-BPFB4 the page reads honestly: one card per buyer marked data-buyer,
           an undefined average printed as the dash with no bar, a measured
           0.0 kept apart from undefined, a non-positive net spend printed as
           a named undefined split with no bar, an empty market named, the
           twelve law sentences present, and no bare None.
  AC-BPFB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer and the not-advice sentence are on the page
           and there are zero external links.
  AC-BPFB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with AC-AMBY arms.

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
TOOL = os.path.join(ROOT, "tools", "buyer_profile_board.py")
HTML = os.path.join(ROOT, "preview", "buyer-profile-board.html")
JSONF = os.path.join(ROOT, "preview", "buyer-profile-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-profile-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_buyerprofile.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-buyer-profile-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope", "buyer_count",
    "buyers", "market", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "buyer_id", "purchase_count", "refund_count", "net_purchase_count",
    "listing_count", "gross_spent", "refunded_total", "net_spent",
    "dev_paid", "platform_paid", "rating_count", "avg_rating",
    "watch_count", "live_watch_count", "first_purchase_utc",
    "last_purchase_utc", "disclaimer",
}
MARKET_KEYS = {key for key in ENVELOPE_KEYS if key != "buyer_id"}

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
    tmp_root = tempfile.mkdtemp(prefix="bpfb-suite-")
    db = os.path.join(tmp_root, "bpfb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        board = dict(am.api_board())
        buyers = set()
        for row in board["listings"]:
            for sale in (am.api_sales(str(row["dev_account"])).get("sales")
                         or []):
                if sale.get("buyer_id"):
                    buyers.add(str(sale["buyer_id"]))
        envelopes = [dict(am.api_buyer_profile(buyer))
                     for buyer in sorted(buyers)]
        return envelopes, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def load_driver():
    spec = importlib.util.spec_from_file_location("bpfb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(left, right, tol=1e-9):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= tol


def account_problems(block, label):
    problems = []
    if int(block["net_spent"]) != (int(block["gross_spent"])
                                   - int(block["refunded_total"])):
        problems.append("%s net_spent" % label)
    if int(block["purchase_count"]) != (int(block["net_purchase_count"])
                                        + int(block["refund_count"])):
        problems.append("%s purchase split" % label)
    if int(block["dev_paid"]) + int(block["platform_paid"]) != int(
            block["net_spent"]):
        problems.append("%s pool legs" % label)
    if int(block["live_watch_count"]) > int(block["watch_count"]):
        problems.append("%s watches" % label)
    ratings = int(block["rating_count"])
    avg = block["avg_rating"]
    if (ratings == 0) != (avg is None):
        problems.append("%s rating nullability" % label)
    if avg is not None and not (0.0 <= float(avg) <= 5.0):
        problems.append("%s rating range" % label)
    first = block["first_purchase_utc"]
    last = block["last_purchase_utc"]
    if int(block["purchase_count"]) == 0:
        if first is not None or last is not None:
            problems.append("%s empty stamps" % label)
    else:
        if first is None or last is None:
            problems.append("%s missing stamps" % label)
        elif str(first) > str(last):
            problems.append("%s stamp order" % label)
    if not str(block["buyer_id"]).startswith("usr:"):
        problems.append("%s account prefix" % label)
    return problems


def empty_envelope():
    return {
        "buyer_id": "usr:probe", "purchase_count": 0, "refund_count": 0,
        "net_purchase_count": 0, "listing_count": 0, "gross_spent": 0,
        "refunded_total": 0, "net_spent": 0, "dev_paid": 0,
        "platform_paid": 0, "rating_count": 0, "avg_rating": None,
        "watch_count": 0, "live_watch_count": 0, "first_purchase_utc": None,
        "last_purchase_utc": None, "disclaimer": "probe disclaimer",
    }


def rated_envelope():
    """A positive-net account with two ratings at 4.0 and 4.5."""
    return {
        "buyer_id": "usr:probe", "purchase_count": 3, "refund_count": 1,
        "net_purchase_count": 2, "listing_count": 2, "gross_spent": 40,
        "refunded_total": 10, "net_spent": 30, "dev_paid": 21,
        "platform_paid": 9, "rating_count": 2, "avg_rating": 4.25,
        "watch_count": 3, "live_watch_count": 1,
        "first_purchase_utc": "2026-08-01T00:00:00Z",
        "last_purchase_utc": "2026-09-01T00:00:00Z",
        "disclaimer": "probe disclaimer",
    }


def zero_avg_envelope():
    """A measured zero rating average, not an undefined one."""
    block = rated_envelope()
    block["rating_count"] = 1
    block["avg_rating"] = 0.0
    return block


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    buyers = doc.get("buyers") or []
    market = doc.get("market") or {}

    # ---- AC-BPFB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelopes_ok = all(set(block.keys()) == ENVELOPE_KEYS for block in buyers)
    market_ok = set(market.keys()) == MARKET_KEYS
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-BPFB1", landed and keys == PAYLOAD_KEYS and envelopes_ok
       and market_ok and sources_ok and bool(buyers)
       and int(doc.get("buyer_count", -1)) == len(buyers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelopes=%s market=%s "
       "sources=%s count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelopes_ok, market_ok, sources_ok,
          len(buyers), int(doc.get("buyer_count", -1)), report_ok))

    # ---- AC-BPFB2: every printed number is the shipped face's own.
    live_buyers, live_disclaimer = live_world()
    same = json.dumps(buyers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in ENVELOPE_KEYS} for block in live_buyers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-BPFB2", same and disc_same and bool(buyers),
       "buyers_same=%s disclaimer_same=%s buyers=%d purchases=%d"
       % (same, disc_same, len(buyers),
          sum(int(b["purchase_count"]) for b in buyers)))

    # ---- AC-BPFB3: the face's identities hold on these envelopes.
    problems = []
    seen = set()
    for block in buyers:
        label = str(block.get("buyer_id"))
        problems.extend(account_problems(block, label))
        if label in seen:
            problems.append("%s duplicated" % label)
        seen.add(label)
    for key in ("purchase_count", "refund_count", "net_purchase_count",
                "listing_count", "gross_spent", "refunded_total",
                "net_spent", "dev_paid", "platform_paid", "rating_count",
                "watch_count", "live_watch_count"):
        want = sum(int(block[key]) for block in buyers)
        if int(market.get(key, -1)) != want:
            problems.append("market %s" % key)
    ratings = sum(int(block["rating_count"]) for block in buyers)
    star_sum = sum(float(block["avg_rating"]) * int(block["rating_count"])
                   for block in buyers if block["avg_rating"] is not None)
    if not close(market.get("avg_rating"),
                 (star_sum / ratings) if ratings else None):
        problems.append("market avg_rating")
    stamps = [block["first_purchase_utc"] for block in buyers
              if block["first_purchase_utc"] is not None]
    if market.get("first_purchase_utc") != (min(stamps) if stamps else None):
        problems.append("market first stamp")
    lasts = [block["last_purchase_utc"] for block in buyers
             if block["last_purchase_utc"] is not None]
    if market.get("last_purchase_utc") != (max(lasts) if lasts else None):
        problems.append("market last stamp")
    ok("AC-BPFB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-BPFB4: honest page face, dashes, zero markers, quiet accounts.
    dash = labels.get("none", "-")
    sections = len(re.findall(r'<div class="?card"? data-buyer="', page))
    positive = sum(1 for b in buyers if int(b["net_spent"]) > 0)
    non_positive = len(buyers) - positive
    bars = page.count("<div class=split>")
    dots = page.count("class=zero-dot")
    measured_zero_avg = sum(1 for b in buyers
                            if b["avg_rating"] is not None
                            and float(b["avg_rating"]) == 0.0)
    no_none = ">None<" not in page
    laws = [labels.get(key, "") for key in
            ("law_count", "law_spend", "law_halves", "law_pool", "law_watch",
             "law_rating", "law_range", "law_stamp", "law_market",
             "law_scope", "law_bar", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    empty_ok = rated_ok = zero_ok = quiet_ok = False
    try:
        driver = load_driver()
        empty_html = driver.build_html(
            [empty_envelope()], driver.market_block([empty_envelope()],
                                                    "probe disclaimer"),
            labels, "2026-01-01 00:00:00Z", "probe disclaimer")
        empty_ok = (labels.get("empty_account", "") in empty_html
                    and "<div class=split>" not in empty_html
                    and ">None<" not in empty_html)
        rated = rated_envelope()
        rated_html = driver.build_html(
            [rated], driver.market_block([rated], "probe disclaimer"),
            labels, "2026-01-01 00:00:00Z", "probe disclaimer")
        rated_ok = (rated_html.count("<div class=split>") == 1
                    and "70.0%" in rated_html
                    and "30.0%" in rated_html
                    and "4.25" in rated_html
                    and ">None<" not in rated_html)
        zero = zero_avg_envelope()
        zero_html = driver.build_html(
            [zero], driver.market_block([zero], "probe disclaimer"),
            labels, "2026-01-01 00:00:00Z", "probe disclaimer")
        avg_cell = ('<tr data-field="10"><td>%s</td><td class=n>%%s</td></tr>'
                    % labels["row_avg"])
        zero_ok = ((avg_cell % "0.00") in zero_html
                   and (avg_cell % dash) not in zero_html
                   and (avg_cell % dash) in empty_html
                   and (avg_cell % "0.00") not in empty_html)
        quiet = driver.build_html(
            [], driver.market_block([], "probe disclaimer"), labels,
            "2026-01-01 00:00:00Z", "probe disclaimer")
        quiet_ok = (labels.get("empty_scope", "") in quiet
                    and ">None<" not in quiet)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-BPFB4", sections == len(buyers) and bars == positive
       and dots == measured_zero_avg and non_positive >= 0 and no_none
       and laws_ok and empty_ok and rated_ok and zero_ok and quiet_ok,
       "sections=%d/%d bars=%d/%d dots=%d/%d non_positive=%d laws=%s "
       "empty_probe=%s rated_probe=%s zero_probe=%s quiet_probe=%s "
       "bare_none=%s"
       % (sections, len(buyers), bars, positive, dots, measured_zero_avg,
          non_positive, laws_ok, empty_ok, rated_ok, zero_ok, quiet_ok,
          not no_none))

    # ---- AC-BPFB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    not_advice = labels.get("law_notadvice", "") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-BPFB5", aigc and on_page and not_advice and external == 0,
       "aigc=%s disclaimer_on_page=%s not_advice=%s external_links=%d"
       % (aigc, on_page, not_advice, external))

    # ---- AC-BPFB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-AMBY" in read(FACE_SUITE)
    ok("AC-BPFB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
