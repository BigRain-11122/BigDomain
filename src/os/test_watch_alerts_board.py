"""Battery suite for tools/watch_alerts_board.py - AC-WALB1..6.

WHY THIS SUITE EXISTS (measured at R3434, not assumed):
api_watchlist answers what a resident is watching and api_watch_alerts answers
what happened to those watches (a price moved, a shelf sold out, a listing was
retired), but a git grep over tools/ and preview/ answered zero hits, so "what
happened to the things I watch" could only be asked of a shell. R3434 renders
one summary table and one card per buyer; this suite grades the page, not the
face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3434 PIN
BEFORE the driver existed):
  AC-WALB1 the page and its json land, the json carries exactly the pinned
           payload key set, every buyer block carries the shipped 5-key
           envelope, every alert row the shipped 13 keys, buyer_count equals
           the block count, the report points at a file that exists, and the
           four source fingerprints are recorded.
  AC-WALB2 the data is the shipped face's own: the suite builds its own
           throwaway world (factory demo plus the driver's shipped-door watch
           fixture), enumerates buyers, reads api_watch_alerts() per buyer, and
           requires the page json's buyers (including every row and the
           disclaimer) to equal that reading item for item - no typed fixture.
  AC-WALB3 the face's identities hold: alert_count is the row count,
           watch_count is not smaller than alert_count and equals the live
           watchlist count, every kind is one of the four, severity is pinned
           per kind, delta is current minus at-watch, a drop is negative and a
           rise is positive, only a retired row carries the retired flag, an
           already purchased watch is silent, and rows run in the pinned
           (kind rank, listing_id) order.
  AC-WALB4 the page reads honestly: one card per buyer marked data-buyer,
           every row marked data-kind and data-listing, a named badge per
           kind, a dash wherever the face publishes None, no bare None, and
           both the empty-buyer and four-kind shapes render.
  AC-WALB5 the standing compliance faces ride along: the AIGC label, the
           face's own disclaimer and the not-advice sentence are on the page,
           with zero external links.
  AC-WALB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, the
           producer row is recorded for the json pair, and the shipped face's
           own suite is still on disk with AC-WAL arms.

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
TOOL = os.path.join(ROOT, "tools", "watch_alerts_board.py")
HTML = os.path.join(ROOT, "preview", "watch-alerts-board.html")
JSONF = os.path.join(ROOT, "preview", "watch-alerts-board.json")
COPY = os.path.join(ROOT, "preview", "watch-alerts-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
INDEXER = os.path.join(ROOT, "tools", "deliverable_index.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_watchalerts.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-watch-alerts-board"
PAIR = "watch-alerts-board.json"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "board_face", "scope", "buyer_count",
    "buyers", "disclaimer", "report", "sources", "sizes",
}
ENVELOPE_KEYS = {
    "buyer_id", "watch_count", "alert_count", "disclaimer", "alerts",
}
ROW_KEYS = {
    "watch_id", "listing_id", "listing_key", "title", "dev_account",
    "kind", "severity", "price_at_watch", "current_price", "delta",
    "delisted", "sold_out", "watched_utc",
}
KIND_RANK = {"delisted": 0, "sold_out": 1, "price_drop": 2, "price_rise": 3}
KIND_SEVERITY = {"delisted": "high", "sold_out": "warn",
                 "price_drop": "info", "price_rise": "info"}

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


def load_driver():
    spec = importlib.util.spec_from_file_location("walb_board_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_world():
    """The shipped face's own reading over the suite's throwaway world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    driver = load_driver()
    tmp_root = tempfile.mkdtemp(prefix="walb-suite-")
    db = os.path.join(tmp_root, "walb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        driver.seed_watches(am)
        board = dict(am.api_board())
        buyers = driver.buyer_ids(board, am)
        envelopes = [dict(am.api_watch_alerts(buyer)) for buyer in buyers]
        watches = [dict(am.api_watchlist(buyer)) for buyer in buyers]
        return envelopes, watches, board["disclaimer"]
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def envelope_problems(block, watchlist, label):
    problems = []
    rows = list(block["alerts"])
    if int(block["alert_count"]) != len(rows):
        problems.append("%s alert_count" % label)
    if int(block["watch_count"]) < int(block["alert_count"]):
        problems.append("%s watch_count" % label)
    if int(watchlist["watch_count"]) != int(block["watch_count"]):
        problems.append("%s watchlist count" % label)
    purchased = {int(w["listing_id"]) for w in watchlist["watches"]
                 if w.get("purchased")}
    for row in rows:
        name = "%s/%s" % (label, row["listing_id"])
        kind = str(row["kind"])
        if kind not in KIND_RANK:
            problems.append("%s unknown kind %s" % (name, kind))
            continue
        if str(row["severity"]) != KIND_SEVERITY[kind]:
            problems.append("%s severity" % name)
        if int(row["delta"]) != int(row["current_price"]) - int(
                row["price_at_watch"]):
            problems.append("%s delta" % name)
        if kind == "price_drop" and int(row["delta"]) >= 0:
            problems.append("%s drop sign" % name)
        if kind == "price_rise" and int(row["delta"]) <= 0:
            problems.append("%s rise sign" % name)
        if kind == "delisted" and not bool(row["delisted"]):
            problems.append("%s retired flag" % name)
        if kind != "delisted" and bool(row["delisted"]):
            problems.append("%s live kind retired" % name)
        if int(row["listing_id"]) in purchased:
            problems.append("%s purchased" % name)
        if not str(row["listing_key"] or "").strip():
            problems.append("%s empty key" % name)
        if not str(row["dev_account"] or "").startswith("usr:"):
            problems.append("%s seller" % name)
        if not str(row["watched_utc"] or "").strip():
            problems.append("%s watched" % name)
    order = [(KIND_RANK.get(str(r["kind"]), 9), int(r["listing_id"]))
             for r in rows]
    if order != sorted(order):
        problems.append("%s row order" % label)
    return problems


def row_of(watch_id, listing, key, title, who, kind, severity, at_watch,
           current, watched):
    return {"watch_id": watch_id, "listing_id": listing, "listing_key": key,
            "title": title, "dev_account": who, "kind": kind,
            "severity": severity, "price_at_watch": at_watch,
            "current_price": current, "delta": current - at_watch,
            "delisted": kind == "delisted", "sold_out": kind == "sold_out",
            "watched_utc": watched}


def probe_envelope():
    rows = [
        row_of(1, 1, "alpha", "Alpha API", "usr:dana", "delisted", "high",
               9, 9, "2026-01-01T00:00:00Z"),
        row_of(2, 2, "beta", "Beta API", "usr:dana", "sold_out", "warn",
               5, 5, "2026-01-02T00:00:00Z"),
        row_of(3, 3, "gamma", "Gamma API", "usr:frank", "price_drop", "info",
               8, 6, "2026-01-03T00:00:00Z"),
        row_of(4, 4, "delta", "Delta API", "usr:frank", "price_rise", "info",
               2, 4, "2026-01-04T00:00:00Z"),
    ]
    return {
        "buyer_id": "usr:probe", "watch_count": 5, "alert_count": 4,
        "alerts": rows, "disclaimer": "probe disclaimer",
    }


def empty_envelope():
    return {
        "buyer_id": "usr:empty", "watch_count": 0, "alert_count": 0,
        "alerts": [], "disclaimer": "probe disclaimer",
    }


def watchlist_of(count, purchased=()):
    watches = [{"listing_id": 90 + i, "purchased": i in purchased}
               for i in range(count)]
    return {"buyer_id": "usr:probe", "watch_count": count,
            "watches": watches, "disclaimer": "probe disclaimer"}


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    buyers = doc.get("buyers") or []

    # ---- AC-WALB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    envelopes_ok = all(set(block.keys()) == ENVELOPE_KEYS for block in buyers)
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for block in buyers for row in (block.get("alerts") or []))
    report_ok = bool(doc.get("report")) and os.path.exists(
        os.path.join(ROOT, str(doc.get("report"))))
    sources_ok = set((doc.get("sources") or {}).keys()) == {
        "driver", "copy", "apimarket", "report"}
    ok("AC-WALB1", landed and keys == PAYLOAD_KEYS and envelopes_ok and rows_ok
       and sources_ok and bool(buyers)
       and int(doc.get("buyer_count", -1)) == len(buyers) and report_ok,
       "landed=%s keys=%d missing=%s extra=%s envelopes=%s rows=%s sources=%s "
       "count=%d/%d report=%s"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), envelopes_ok, rows_ok, sources_ok,
          len(buyers), int(doc.get("buyer_count", -1)), report_ok))

    # ---- AC-WALB2: every printed number is the shipped face's own.
    live_buyers, live_watches, live_disclaimer = live_world()
    same = json.dumps(buyers, sort_keys=True) == json.dumps(
        [{key: block[key] for key in ENVELOPE_KEYS} for block in live_buyers],
        sort_keys=True)
    disc_same = (doc.get("disclaimer") == live_disclaimer)
    ok("AC-WALB2", same and disc_same and bool(buyers),
       "buyers_same=%s disclaimer_same=%s buyers=%d alerts=%d kinds=%d"
       % (same, disc_same, len(buyers),
          sum(int(b["alert_count"]) for b in buyers),
          len({str(r["kind"]) for b in buyers for r in b["alerts"]})))

    # ---- AC-WALB3: the face's identities hold on these envelopes.
    problems = []
    for block, watch in zip(buyers, live_watches):
        problems.extend(envelope_problems(block, watch,
                                         str(block.get("buyer_id"))))
    ok("AC-WALB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-WALB4: honest page face, badges, dashes, quiet empty scope.
    dash = labels.get("none", "-")
    sections = len(re.findall(r'<div class="?card"? data-buyer="', page))
    rows_marked = len(re.findall(r'data-kind="[a-z_]+"', page))
    listings_marked = len(re.findall(r'data-listing="\d+"', page))
    landed_rows = sum(len(b["alerts"]) for b in buyers)
    landed_kinds = {str(r["kind"]) for b in buyers for r in b["alerts"]}
    laws = [labels.get(key, "") for key in
            ("law_count", "law_watches", "law_kinds", "law_severity",
             "law_delta", "law_order", "law_retired", "law_purchased",
             "law_silent", "law_scope", "law_notadvice")]
    laws_ok = all(line and line in page for line in laws)
    badges_ok = all(("badge " + kind.replace("_", "-")) in page
                    for kind in landed_kinds)
    no_none = ">None<" not in page
    empty_ok = probe_ok = False
    try:
        driver = load_driver()
        empty_html = driver.build_html([empty_envelope()], labels,
                                       "2026-01-01 00:00:00Z",
                                       "probe disclaimer")
        empty_ok = (labels.get("empty_buyer", "") in empty_html
                    and ">None<" not in empty_html)
        probe_html = driver.build_html([probe_envelope()], labels,
                                       "2026-01-01 00:00:00Z",
                                       "probe disclaimer")
        probe_ok = (
            len(re.findall(r'data-kind="[a-z_]+"', probe_html)) == 4
            and len(re.findall(r'data-listing="\d+"', probe_html)) == 4
            and all(("badge " + kind.replace("_", "-")) in probe_html
                    for kind in KIND_RANK)
            and ">None<" not in probe_html
            and labels.get("kpi_net_delta", "") in probe_html)
    except Exception as exc:  # noqa: BLE001
        print("NOTE render probe raised %s: %s"
              % (type(exc).__name__, exc))
    ok("AC-WALB4", sections == len(buyers) and rows_marked == landed_rows
       and listings_marked == landed_rows and no_none and laws_ok
       and badges_ok and empty_ok and probe_ok,
       "sections=%d/%d rows_marked=%d/%d listings=%d/%d laws=%s badges=%s "
       "empty_probe=%s kind_probe=%s bare_none=%s"
       % (sections, len(buyers), rows_marked, landed_rows, listings_marked,
          landed_rows, laws_ok, badges_ok, empty_ok, probe_ok, not no_none))

    # ---- AC-WALB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    not_advice = labels.get("law_notadvice", "") in page
    external = len(re.findall(r"https?://", page))
    ok("AC-WALB5", aigc and on_page and not_advice and external == 0,
       "aigc=%s disclaimer_on_page=%s not_advice=%s external_links=%d"
       % (aigc, on_page, not_advice, external))

    # ---- AC-WALB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r'\),\s*(\d+)\)', registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    pair_row = ('"%s": "tools/watch_alerts_board.py"' % PAIR) in read(INDEXER)
    face_ok = os.path.exists(FACE_SUITE) and "AC-WAL" in read(FACE_SUITE)
    ok("AC-WALB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and pair_row and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d pair_row=%s face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, pair_row, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
