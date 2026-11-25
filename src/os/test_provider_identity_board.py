"""Battery suite for tools/provider_identity_board.py - AC-PIDB1..6.

WHY THIS SUITE EXISTS (measured at R3457, not assumed):
api_provider_identity shipped the per-developer real-name face - the
registration flag, the published provider name, the unified social credit code,
the registration stamp and whether disclosure is complete - but a search over
tools/, preview/ and src/os answered zero readers for its name. R3457 renders
the shipped envelopes on one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (criteria fixed in this round's window before the first
render; the src/os/backlog.md R3457 PIN row landed with the driver and says
so):
  AC-PIDB1 the pair lands, the json carries exactly the pinned nine-key
          payload set, the market block exactly the nine derived keys, every
          developer entry the pinned eight keys, the report points at a file
          that exists and the four source fingerprints are present.
  AC-PIDB2 the data is the shipped face's own: the suite builds its own
          throwaway world through the shipped issue_key, publish_api,
          register_provider and revise_provider doors under its own pinned
          clock, re-reads every developer through api_provider_identity (with
          the shelf stamps re-read through api_view) and requires the page
          json to equal that reading item for item, disclaimer included.
  AC-PIDB3 the face identities hold and the driver refuses a broken one: the
          registration flag, the disclosure flag, the counts, the rate, the
          stamps, the distinct credit codes, the trim and length bounds and
          the oldest-undisclosed tie-break all hold - and a forged developer
          plus a forged market rate are refused by name.
  AC-PIDB4 the page reads honestly: one marked card per developer, the dash
          where an identity is absent, no bare None or null, the 80-character
          clip caption on the page, both disclosure badges reachable on landed
          rows, and the empty sentence reachable both as a landed undisclosed
          developer and in an in-memory probe.
  AC-PIDB5 the standing compliance faces ride along: the AIGC label, the
          face's own disclaimer verbatim, the non-advice sentence, zero
          external links and no script tags.
  AC-PIDB6 no older criterion is relaxed: the landed pair answers its own
          --check, --check writes nothing, the driver is registered in
          src/sandbox/reconcile_all.py with this suite's DECLARED count, and
          the face is still exercised by its shipped suite on disk.

Read-only over the repository: the provenance world is built in a temp dir and
the empty probe renders in memory, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import importlib.util
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "provider_identity_board.py")
HTML = os.path.join(ROOT, "preview", "provider-identity-board.html")
JSONF = os.path.join(ROOT, "preview", "provider-identity-board.json")
COPY = os.path.join(ROOT, "preview", "provider-identity-board-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_provideridentity.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-provider-identity-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "scope", "market", "developers",
    "disclaimer", "report", "sources", "sizes",
}
MARKET_KEYS = {
    "developer_count", "registered_count", "undisclosed_count",
    "disclosure_rate", "earliest_registered_utc", "latest_registered_utc",
    "oldest_undisclosed_dev", "oldest_undisclosed_listed_utc",
    "distinct_credit_code_count",
}
DEV_KEYS = {"dev_account", "registered", "provider_name", "credit_code",
            "registered_utc", "disclosure_ok", "listing_count",
            "earliest_listed_utc"}

CHECKS = ["AC-PIDB1", "AC-PIDB2", "AC-PIDB3", "AC-PIDB4", "AC-PIDB5",
          "AC-PIDB6"]
FAILS = []


def ok(name, cond, detail):
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


def load_driver():
    spec = importlib.util.spec_from_file_location("pid_driver", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_world(driver):
    """The suite's own stack, every row through a shipped door."""
    import apimarket as A
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="pid-suite-")
    db = os.path.join(tmp_root, "suite.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = driver._clock
        driver.build_world(am, dk)
        stats = driver._shelf_stats(am)
        rows = []
        for dev in sorted(stats):
            envelope = dict(am.api_provider_identity(dev))
            row = {"dev_account": dev}
            for name in DEV_KEYS:
                if name == "dev_account":
                    continue
                if name in ("listing_count", "earliest_listed_utc"):
                    row[name] = stats[dev][name]
                else:
                    row[name] = envelope[name]
            rows.append(row)
        sellers = sorted(stats)
    finally:
        A._now_utc = orig_now
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return rows, sellers


def same(left, right):
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(
        right, sort_keys=True, default=str)


def main():
    if not os.path.exists(TOOL):
        print("FAIL AC-PIDB1 driver missing")
        return 2
    driver = load_driver()
    labels = json.loads(read(COPY))
    page = json.loads(read(JSONF))
    doc = read(HTML)

    entries = page.get("developers") or []
    market = page.get("market") or {}

    # ---- AC-PIDB1 contract ------------------------------------------------
    missing_payload = sorted(PAYLOAD_KEYS - set(page))
    extra_payload = sorted(set(page) - PAYLOAD_KEYS)
    report_path = os.path.join(ROOT, page.get("report") or "")
    sources = page.get("sources") or {}
    sizes = page.get("sizes") or {}
    dev_shape = all(set(entry) == DEV_KEYS for entry in entries)
    ok("AC-PIDB1",
       not missing_payload and not extra_payload
       and set(market) == MARKET_KEYS and dev_shape
       and os.path.exists(report_path)
       and sorted(sources) == ["apimarket", "copy", "driver", "report"]
       and sizes.get("html") == os.path.getsize(HTML)
       and sizes.get("json") == os.path.getsize(JSONF)
       and page.get("face") == "api_provider_identity",
       "payload_missing=%r payload_extra=%r developers=%d dev_shape=%r "
       "report=True sources=True"
       % (missing_payload, extra_payload, len(entries), dev_shape))

    # ---- AC-PIDB2 the data is the shipped face's own ----------------------
    live, live_sellers = live_world(driver)
    live_market = driver.derive_market(live)
    same_all = same(live, entries)
    same_words = page.get("disclaimer") == driver.read_empty().get("disclaimer")
    same_market = same(live_market, market)
    same_order = ([entry["dev_account"] for entry in entries]
                  == [row["dev_account"] for row in live])
    ok("AC-PIDB2",
       same_all and same_words and same_market and same_order,
       "developer_same=%r disclaimer_same=%r market_same=%r order_same=%r "
       "developers=%d" % (same_all, same_words, same_market, same_order,
                          len(live)))

    # ---- AC-PIDB3 laws, plus forged rows refused by name ------------------
    bare = driver.read_empty()
    driver_problems = driver.check_laws(live, live_market, bare)
    forged = json.loads(json.dumps(live, default=str))
    for row in forged:
        if not row["registered"]:
            row["provider_name"] = "forged identity"
            row["disclosure_ok"] = True
            break
    forged_market = json.loads(json.dumps(live_market, default=str))
    forged_market["disclosure_rate"] = float(
        forged_market.get("disclosure_rate") or 0.0) + 0.25
    forged_problems = driver.check_laws(forged, forged_market, bare)
    registered_ok = True
    undisclosed_ok = True
    oldest_dev = None
    oldest_stamp = None
    for row in live:
        complete = all(row[name] is not None
                       for name in ("provider_name", "credit_code",
                                    "registered_utc"))
        if bool(row["registered"]) != complete:
            registered_ok = False
        if bool(row["disclosure_ok"]) != bool(row["registered"]):
            registered_ok = False
        if not row["registered"]:
            if any(row[name] is not None
                   for name in ("provider_name", "credit_code",
                                "registered_utc")):
                undisclosed_ok = False
            if row["earliest_listed_utc"] and (
                    oldest_stamp is None
                    or row["earliest_listed_utc"] < oldest_stamp
                    or (row["earliest_listed_utc"] == oldest_stamp
                        and row["dev_account"] < oldest_dev)):
                oldest_dev = row["dev_account"]
                oldest_stamp = row["earliest_listed_utc"]
    ok("AC-PIDB3",
       not driver_problems and len(forged_problems) >= 2 and registered_ok
       and undisclosed_ok and market["oldest_undisclosed_dev"] == oldest_dev
       and market["oldest_undisclosed_listed_utc"] == oldest_stamp
       and int(market["registered_count"]) + int(
           market["undisclosed_count"]) == len(live)
       and bare.get("registered") is False
       and bare.get("disclosure_ok") is False,
       "driver_problems=%d forged_problems=%d registered=%r undisclosed=%r "
       "oldest=%r" % (len(driver_problems), len(forged_problems),
                      registered_ok, undisclosed_ok, oldest_dev))

    # ---- AC-PIDB4 the page reads honestly ---------------------------------
    dash = labels["none"]
    dev_marked = all(('data-dev="%s"' % entry["dev_account"]) in doc
                     for entry in entries)
    bare_none = "None" in doc or "null" in doc
    caption = labels["clip_caption"] in doc
    disclosed_badge = labels["badge_disclosed"] in doc
    undisclosed_badge = labels["badge_undisclosed"] in doc
    silent = sum(1 for entry in live if not entry["registered"])
    empty_landed = doc.count(labels["empty"]) == silent
    probe_market = {"developer_count": 0, "registered_count": 0,
                    "undisclosed_count": 0, "disclosure_rate": None,
                    "earliest_registered_utc": None,
                    "latest_registered_utc": None,
                    "oldest_undisclosed_dev": None,
                    "oldest_undisclosed_listed_utc": None,
                    "distinct_credit_code_count": 0}
    empty_html = driver.build_html([], probe_market, labels,
                                   "2026-11-25 00:00:00Z", "x")
    empty_probe = (labels["kpi_devs"] in empty_html
                   and dash in empty_html
                   and all(cell in empty_html
                           for cell in (labels["kpi_registered"],
                                        labels["kpi_undisclosed"],
                                        labels["kpi_rate"])))
    ok("AC-PIDB4",
       dev_marked and not bare_none and caption and disclosed_badge
       and undisclosed_badge and empty_landed and empty_probe,
       "dev_marked=%r no_bare_none=%r caption=%r disclosed=%r "
       "undisclosed=%r empty_landed=%r empty_probe=%r"
       % (dev_marked, not bare_none, caption, disclosed_badge,
          undisclosed_badge, empty_landed, empty_probe))

    # ---- AC-PIDB5 compliance ----------------------------------------------
    disclaimer = page.get("disclaimer") or ""
    aigc = "AIGC" in doc
    verbatim = bool(disclaimer) and disclaimer in doc
    notadvice = labels["law_notadvice"] in doc
    zero_links = "http://" not in doc and "https://" not in doc
    no_script = "<script" not in doc.lower()
    ok("AC-PIDB5", aigc and verbatim and notadvice and zero_links and no_script,
       "aigc=%r disclaimer_verbatim=%r notadvice=%r zero_links=%r "
       "no_script=%r" % (aigc, verbatim, notadvice, zero_links, no_script))

    # ---- AC-PIDB6 no older criterion is relaxed ---------------------------
    before = (stamp(HTML), stamp(JSONF), stamp(COPY))
    import subprocess
    proc = subprocess.run([sys.executable, TOOL, "--check"], cwd=ROOT,
                          capture_output=True, text=True)
    after = (stamp(HTML), stamp(JSONF), stamp(COPY))
    registry = read(REGISTRY)
    registered = ('"%s"' % ROW) in registry
    row_block = registry.split('"%s"' % ROW, 1)[-1][:200]
    declared = ("%d)" % DECLARED) in row_block
    face_suite = os.path.exists(FACE_SUITE)
    face_ac = "AC-AMPI3" in read(FACE_SUITE) if face_suite else False
    ok("AC-PIDB6",
       proc.returncode == 0 and "CHECK PASS" in proc.stdout
       and before == after and registered and declared and face_suite
       and face_ac,
       "readonly=%r check_rc=%d registered=%r declared_hit=%r face_suite=%r"
       % (before == after, proc.returncode, registered, declared, face_suite))

    print("SUITE %s %d/%d declared=%d row=%s"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED, ROW))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.path.insert(0, LEDGER_DIR)
    sys.exit(main())
