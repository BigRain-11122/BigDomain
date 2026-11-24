"""Battery suite for tools/market_daily_board.py - criteria AC-MDB1..6.

WHY THIS SUITE EXISTS (measured at R3408, not assumed):
api_market_daily has shipped with eight green criteria of its own
(test_apimarket_marketdaily.py, AC-MDL) but the R3408 census re-measured the six
faces the R3407 board named as candidates and found ZERO readers under tools/ and
preview/ for every one of them, api_market_daily included. Every other time axis
stops short of a calendar date, so the daily settlement sheet an operator reads -
what did the market do on one day, which day was the busiest - could not be
opened by anyone. R3408 renders it onto one page; this suite grades the page,
not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3408 PIN
BEFORE the driver existed):
  AC-MDB1 the page and its json land, the json carries exactly the pinned
           payload key set including the sizes and sources blocks, and every day
           row carries the shipped thirteen-key row set.
  AC-MDB2 the data is the shipped face's own: the suite builds its own throwaway
           demo world, reads api_market_daily() there, and requires the page
           json's sixteen envelope fields and the whole days table to equal that
           reading item for item plus the disclaimer verbatim - no typed
           fixture, no synthesized series.
  AC-MDB3 the face's identities hold: days are sorted and consecutive, the day
           count is the row count, active plus zero days is the day count, every
           lifetime figure re-derives as the sum of its column, each row's net
           re-derives from its gross and refunded, a zero-trade day carries only
           zeros, and the active-day average re-derives with None on an honest
           empty.
  AC-MDB4 the page reads honestly: one table row per day, the zero-trade days
           appear as honest zero rows rather than vanishing, the busiest day and
           the lowest active day are named in their own section rather than
           buried in the table, an undefined average prints the no-value mark,
           and no bare None reaches the page.
  AC-MDB5 the standing compliance faces ride along: the AIGC label and the
           face's own disclaimer are on the page, with zero external links.
  AC-MDB6 no older criterion is relaxed: the landed pair answers its own
           --check, --check writes nothing, the driver is registered in
           src/sandbox/reconcile_all.py with this suite's DECLARED count, and
           the shipped face's own suite is still on disk with its AC-MDL arms.

Read-only over the repository: the provenance world is built in a temp dir and
every re-render writes into a temp dir, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "market_daily_board.py")
HTML = os.path.join(ROOT, "preview", "market-daily.html")
JSONF = os.path.join(ROOT, "preview", "market-daily.json")
COPY = os.path.join(ROOT, "preview", "market-daily-copy.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_marketdaily.py")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
ROW = "os-market-daily-board"

DECLARED = 6

PAYLOAD_KEYS = {
    "generated_utc", "face", "day_count", "active_day_count",
    "zero_day_count", "window_start", "window_end", "lifetime_sales_count",
    "lifetime_gross", "lifetime_refund_count", "lifetime_refunded",
    "lifetime_net", "lifetime_dev_revenue", "lifetime_platform_revenue",
    "busiest_day", "quietest_active_day", "avg_net_per_active_day", "days",
    "disclaimer", "report", "sources", "sizes",
}
ROW_KEYS = {
    "day", "sales_count", "gross", "refund_count", "refunded", "net",
    "dev_share", "platform_share", "dev_share_net", "platform_share_net",
    "buyer_count", "seller_count", "listing_count",
}
COMPARE = (
    "day_count", "active_day_count", "zero_day_count", "window_start",
    "window_end", "lifetime_sales_count", "lifetime_gross",
    "lifetime_refund_count", "lifetime_refunded", "lifetime_net",
    "lifetime_dev_revenue", "lifetime_platform_revenue", "busiest_day",
    "quietest_active_day", "avg_net_per_active_day", "days",
)
ZERO_FIELDS = (
    "sales_count", "gross", "refund_count", "refunded", "net", "dev_share",
    "platform_share", "dev_share_net", "platform_share_net", "buyer_count",
    "seller_count", "listing_count",
)

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


def face_reading():
    """One envelope read from the shipped face over a private demo world."""
    sys.path.insert(0, LEDGER_DIR)
    import apimarket_report as R
    tmp_root = tempfile.mkdtemp(prefix="mdb-suite-")
    db = os.path.join(tmp_root, "mdb.db")
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        return dict(am.api_market_daily())
    finally:
        for obj in (am, dk, mtr, led):
            try:
                obj.close()
            except Exception:
                pass


def identity_problems(doc):
    problems = []
    rows = doc["days"]
    day_count = int(doc["day_count"])
    active = int(doc["active_day_count"])
    zero = int(doc["zero_day_count"])
    if day_count != len(rows):
        problems.append("day_count")
    if active + zero != day_count:
        problems.append("active_plus_zero")
    days = [r["day"] for r in rows]
    if days != sorted(days):
        problems.append("not_sorted")
    try:
        parsed = [datetime.date.fromisoformat(d) for d in days]
    except (TypeError, ValueError):
        problems.append("bad_day_format")
        parsed = []
    if parsed:
        gaps = [(a, b) for a, b in zip(parsed, parsed[1:])
                if (b - a).days != 1]
        if gaps:
            problems.append("not_contiguous")
        if doc["window_start"] != days[0]:
            problems.append("window_start")
        if doc["window_end"] != days[-1]:
            problems.append("window_end")
    sums = {
        "sales_count": 0, "gross": 0, "refund_count": 0, "refunded": 0,
        "net": 0, "dev_share_net": 0, "platform_share_net": 0,
    }
    active_rows = []
    zero_rows = 0
    for row in rows:
        for key in sums:
            sums[key] += int(row[key])
        if int(row["net"]) != int(row["gross"]) - int(row["refunded"]):
            problems.append("%s net" % row["day"])
        if not (row["sales_count"] or row["refund_count"]):
            zero_rows += 1
            if any(int(row[key]) != 0 for key in ZERO_FIELDS):
                problems.append("%s zero_row" % row["day"])
        else:
            active_rows.append(row)
    if sums["sales_count"] != int(doc["lifetime_sales_count"]):
        problems.append("lifetime_sales_count")
    if sums["gross"] != int(doc["lifetime_gross"]):
        problems.append("lifetime_gross")
    if sums["refund_count"] != int(doc["lifetime_refund_count"]):
        problems.append("lifetime_refund_count")
    if sums["refunded"] != int(doc["lifetime_refunded"]):
        problems.append("lifetime_refunded")
    if sums["net"] != int(doc["lifetime_net"]):
        problems.append("lifetime_net")
    if sums["dev_share_net"] != int(doc["lifetime_dev_revenue"]):
        problems.append("lifetime_dev_revenue")
    if sums["platform_share_net"] != int(doc["lifetime_platform_revenue"]):
        problems.append("lifetime_platform_revenue")
    if zero_rows != zero:
        problems.append("zero_day_count")
    if len(active_rows) != active:
        problems.append("active_day_count")
    want_avg = (round(float(doc["lifetime_net"]) / len(active_rows), 2)
                if active_rows else None)
    if doc["avg_net_per_active_day"] != want_avg:
        problems.append("avg_net_per_active_day")
    if active_rows:
        want_busiest = min(active_rows,
                           key=lambda r: (-int(r["net"]), r["day"]))["day"]
        want_quietest = min(active_rows,
                            key=lambda r: (int(r["net"]), r["day"]))["day"]
        if doc["busiest_day"] != want_busiest:
            problems.append("busiest_day")
        if doc["quietest_active_day"] != want_quietest:
            problems.append("quietest_active_day")
    elif (doc["busiest_day"] is not None
          or doc["quietest_active_day"] is not None):
        problems.append("extremes_on_empty")
    return problems


def section(page, start_label, stop_label):
    """Slice the card between two headings, or '' when either is missing."""
    first = page.find(start_label)
    if first < 0:
        return ""
    second = page.find("<h2>", first + len(start_label))
    return page[first:] if second < 0 else page[first:second]


def main():
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    page = read(HTML) if os.path.exists(HTML) else ""
    labels = json.loads(read(COPY)) if os.path.exists(COPY) else {}
    rows = doc.get("days") or []

    # ---- AC-MDB1: the pair landed with exactly the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    keys = set(doc.keys())
    row_keys_ok = all(set(row.keys()) == ROW_KEYS for row in rows)
    ok("AC-MDB1", landed and keys == PAYLOAD_KEYS and row_keys_ok
       and int(doc.get("day_count", -1)) == len(rows),
       "landed=%s keys=%d missing=%s extra=%s row_keys=%s rows=%d"
       % (landed, len(keys), sorted(PAYLOAD_KEYS - keys),
          sorted(keys - PAYLOAD_KEYS), row_keys_ok, len(rows)))

    # ---- AC-MDB2: every printed number is the shipped face's own.
    live = face_reading()
    diffs = [key for key in COMPARE
             if json.dumps(doc.get(key), sort_keys=True)
             != json.dumps(live.get(key), sort_keys=True)]
    disc_same = doc.get("disclaimer") == live.get("disclaimer")
    ok("AC-MDB2", not diffs and disc_same and bool(rows),
       "diffs=%s disclaimer_same=%s rows=%d"
       % (diffs[:4], disc_same, len(rows)))

    # ---- AC-MDB3: the face's identities hold on this envelope.
    problems = identity_problems(doc) if rows else ["no rows"]
    ok("AC-MDB3", not problems,
       "problems=%s" % (problems[:4] if problems else []))

    # ---- AC-MDB4: honest page face, zero days visible, extremes in their own
    # section, no bare None.
    none = labels.get("none", "-")
    mark = ">%s<" % none
    table = section(page, labels.get("sec_days", ""),
                    labels.get("sec_extremes", ""))
    extremes = section(page, labels.get("sec_extremes", ""),
                       labels.get("sec_laws", ""))
    page_rows = table.count("<tr class=")
    zero_on_page = table.count('class="zero"')
    stand_in = ">None<" in page
    avg_needs_mark = doc.get("avg_net_per_active_day") is None
    mark_ok = (mark in page) if avg_needs_mark else True
    extremes_heading = labels.get("sec_extremes", "") in page
    busiest_named = (str(doc.get("busiest_day")) in extremes
                     if doc.get("busiest_day") is not None else True)
    quietest_named = (str(doc.get("quietest_active_day")) in extremes
                      if doc.get("quietest_active_day") is not None else True)
    ok("AC-MDB4", page_rows == len(rows)
       and zero_on_page == int(doc.get("zero_day_count") or 0)
       and not stand_in and mark_ok and extremes_heading
       and busiest_named and quietest_named,
       "rows=%d/%d zero_rows=%d/%d stand_in_none=%s mark=%s extremes=%s/%s/%s"
       % (page_rows, len(rows), zero_on_page,
          int(doc.get("zero_day_count") or 0), stand_in, mark_ok,
          extremes_heading, busiest_named, quietest_named))

    # ---- AC-MDB5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disc = (doc.get("disclaimer") or "").strip()
    on_page = bool(disc) and disc in page
    external = len(re.findall(r"https?://", page))
    ok("AC-MDB5", aigc and on_page and external == 0,
       "aigc=%s disclaimer_on_page=%s external_links=%d"
       % (aigc, on_page, external))

    # ---- AC-MDB6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    registry = read(REGISTRY)
    idx = registry.find('("' + ROW + '",')
    wired_count = 0
    if idx >= 0:
        count_match = re.search(r"\),\s*(\d+)\)", registry[idx:idx + 400])
        wired_count = int(count_match.group(1)) if count_match else 0
    face_ok = os.path.exists(FACE_SUITE) and "AC-MDL" in read(FACE_SUITE)
    ok("AC-MDB6", rc == 0 and "PASS" in out and before == after
       and wired_count == DECLARED and face_ok,
       "check_rc=%d wrote_nothing=%s wired=%d/%d face_suite=%s"
       % (rc, before == after, wired_count, DECLARED, face_ok))

    print("SUITE %s %d/%d criteria declared=%d"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS), DECLARED))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
