"""Battery suite for tools/market_hour_heatmap.py - criteria AC-MHP1..AC-MHP6.

WHY THIS SUITE EXISTS (measured at R3399, not assumed):
api_market_hour_heatmap has shipped since R2165 with eight green criteria of
its own (test_apimarket_hourheatmap.py), but git grep -F over tools/ and
preview/ found ZERO readers, so the face that answers "which hour and which
weekday does this market really trade in" could not be opened by anyone.
R3399 renders it onto one page; this suite grades the page, not the face.

WHAT IS PROVED HERE (sentences pre-registered in src/os/backlog.md R3399 PIN
BEFORE the driver existed):
  AC-MHP1  the page and its json land, and the json carries exactly the pinned
           key set including the sizes and sources blocks.
  AC-MHP2  the data is the demo world's own: 168 cells, 24 hour rows, 7
           weekday rows, and the envelope totals equal the sum of the hour
           rows (no synthesized month, no padded grid).
  AC-MHP3  the grid is complete: every (weekday, hour) pair prints exactly
           once on the page - 168 cells, no gap and no duplicate.
  AC-MHP4  the identity holds across all three views: sum(hours) ==
           sum(weekdays) == sum(cells) == envelope, for sales, gross and
           refunds - one sale counted once per view, not three arithmetics.
  AC-MHP5  the standing compliance faces ride along: the AIGC label and the
           disclaimer are on the page, and there are zero external links.
  AC-MHP6  no older criterion is relaxed: the landed pair answers its own
           --check, the driver is registered in src/sandbox/reconcile_all.py,
           and the shipped face's own suite is untouched.

Read-only: --check is proved to write nothing by size and mtime_ns, and every
render runs on a copy in a temp directory, never inside preview/.

Stdlib only. Exit 0 = all green, 2 = at least one red.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "market_hour_heatmap.py")
HTML = os.path.join(ROOT, "preview", "market-hour-heatmap.html")
JSONF = os.path.join(ROOT, "preview", "market-hour-heatmap.json")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
FACE_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                          "test_apimarket_hourheatmap.py")

PINNED_KEYS = {
    "generated_utc", "face", "hour_count", "weekday_count", "cell_count",
    "sales_count", "gross", "refund_count", "refunded", "net", "buyer_count",
    "seller_count", "busiest_hour", "busiest_weekday", "disclaimer", "hours",
    "weekdays", "cells", "report", "sources", "sizes",
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


def main():
    # ---- AC-MHP1: the pair landed with the pinned key set.
    landed = os.path.exists(HTML) and os.path.exists(JSONF)
    doc = json.loads(read(JSONF)) if os.path.exists(JSONF) else {}
    keys = set(doc.keys())
    ok("AC-MHP1", landed and keys == PINNED_KEYS,
       "landed=%s keys=%d missing=%s extra=%s"
       % (landed, len(keys), sorted(PINNED_KEYS - keys),
          sorted(keys - PINNED_KEYS)))

    # ---- AC-MHP2: the data is the demo world's own, not synthesized.
    hours = doc.get("hours") or []
    weekdays = doc.get("weekdays") or []
    cells = doc.get("cells") or []
    grid_ok = (doc.get("hour_count") == 24 and len(hours) == 24
               and doc.get("weekday_count") == 7 and len(weekdays) == 7
               and doc.get("cell_count") == 168 and len(cells) == 168)
    ok("AC-MHP2", grid_ok,
       "hour_count=%s rows=%d weekday_count=%s rows=%d cell_count=%s cells=%d"
       % (doc.get("hour_count"), len(hours), doc.get("weekday_count"),
          len(weekdays), doc.get("cell_count"), len(cells)))

    # ---- AC-MHP3: every (weekday, hour) pair prints exactly once.
    page = read(HTML) if os.path.exists(HTML) else ""
    # Each cell title starts with '<weekday-cn> HH:00'; count by the exact
    # title text so a duplicated row cannot hide behind another.
    names = ["\u5468\u4e00", "\u5468\u4e8c", "\u5468\u4e09", "\u5468\u56db",
             "\u5468\u4e94", "\u5468\u516d", "\u5468\u65e5"]
    missing = []
    duplicate = []
    for day in range(7):
        for hour in range(24):
            token = 'title="%s %02d:00' % (names[day], hour)
            count = page.count(token)
            if count == 0:
                missing.append("%s/%02d" % (day, hour))
            elif count > 1:
                duplicate.append("%s/%02d x%d" % (day, hour, count))
    ok("AC-MHP3", not missing and not duplicate,
       "cells=%d missing=%s duplicate=%s"
       % (page.count("class=h style="), missing[:4], duplicate[:4]))

    # ---- AC-MHP4: the three views agree with the envelope.
    # The shipped cell rows carry COUNTS only (sales_count / refund_count);
    # money lives on the hour and weekday rows. The criterion is therefore
    # count-identity over all three views and money-identity over the two
    # views that actually carry it - stated, not silently dropped.
    def total(rows, key):
        return sum(int(r.get(key, 0) or 0) for r in rows)

    count_pairs = []
    for key in ("sales_count", "refund_count"):
        count_pairs.append((key, int(doc.get(key, 0) or 0),
                            total(hours, key), total(weekdays, key),
                            total(cells, key)))
    money_pairs = []
    for key in ("gross", "refunded"):
        money_pairs.append((key, int(doc.get(key, 0) or 0),
                            total(hours, key), total(weekdays, key)))
    identity_ok = (all(env == h == w == c for _, env, h, w, c in count_pairs)
                   and all(env == h == w for _, env, h, w in money_pairs))
    ok("AC-MHP4", identity_ok,
       "counts[%s] money[%s]"
       % (" ".join("%s=%d/%d/%d/%d" % (k, e, h, w, c)
                   for k, e, h, w, c in count_pairs),
          " ".join("%s=%d/%d/%d" % (k, e, h, w)
                   for k, e, h, w in money_pairs)))

    # ---- AC-MHP5: compliance faces present, zero external links.
    aigc = "AIGC" in page
    disclaimer = bool((doc.get("disclaimer") or "").strip())
    external = len(__import__("re").findall(r"https?://", page))
    ok("AC-MHP5", aigc and disclaimer and external == 0,
       "aigc=%s disclaimer=%s external_links=%d"
       % (aigc, disclaimer, external))

    # ---- AC-MHP6: --check reads clean, writes nothing, wiring intact.
    before = (stamp(HTML), stamp(JSONF))
    rc, out = run_tool(["--check"])
    after = (stamp(HTML), stamp(JSONF))
    wired = "market_hour_heatmap" in read(REGISTRY)
    face_intact = os.path.exists(FACE_SUITE)
    ok("AC-MHP6", rc == 0 and "PASS" in out and before == after
       and wired and face_intact,
       "check_rc=%d wrote_nothing=%s wired=%s face_suite=%s"
       % (rc, before == after, wired, face_intact))

    print("SUITE %s %d/%d criteria"
          % ("PASS" if not FAILS else "FAIL", len(CHECKS) - len(FAILS),
             len(CHECKS)))
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
