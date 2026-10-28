"""R2181: insert the seller-cohort face into apimarket.py.

Criteria AC-MSC1..AC-MSC8 were written into the explore-queue row by
prereg_R2181.py BEFORE this insertion ran (honesty law).
"""

import io
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET = os.path.join(BASE, "src", "sandbox", "ledger", "apimarket.py")

METHOD = '''    def api_market_seller_cohort(self):
        """Market-wide monthly seller cohort (new versus returning).

        Criteria AC-MSC1..AC-MSC8 were registered in the R2178 seed row
        of the explore queue BEFORE this code existed (honesty law: the
        AC-MSC prefix, this face name, the suite name and the
        ledger-apimarket-sellercohort runner label were all git-grep
        zero-occupancy against HEAD 2026-10-28, rc=1).

        The buyer side already carries a cohort face and a retention
        matrix, but the seller side only had a lifetime view
        (api_repeat_purchase) and a running total (dev_sales_board), so
        "are the sellers who first listed in January still listing in
        March" was unreadable. This face pins the seller cohort on the
        two stored event sources only: one listing event per row of
        apimarket_listings at its listed_utc, and one re-listing event
        per row of apimarket_relistings at its relisted_utc. No wall
        clock, no derived cycle table.

        A seller's cohort month is the earliest month across their whole
        event history, so a re-listing event whose stamp is earlier than
        the listing stamp still moves the origin (disclosed, never a
        silent clamp). Retirement and being sold out are NOT events: the
        face answers who is still putting supply on the shelf, so only
        listing and re-listing entries enter the queue. A month with no
        events never appears as a zero row.

        No arguments, so no gate: pure read, zero row mutations and zero
        token movement.
        """
        with self._lock:
            listed = self._conn.execute(
                "SELECT dev_account, listed_utc FROM apimarket_listings"
            ).fetchall()
            relisted = self._conn.execute(
                "SELECT dev_account, relisted_utc FROM apimarket_relistings"
            ).fetchall()

        events = [(row[0], str(row[1])[:7], 0) for row in listed]
        events.extend((row[0], str(row[1])[:7], 1) for row in relisted)

        first = {}
        stamps = {}
        for dev, month, _flag in events:
            if dev not in first or month < first[dev]:
                first[dev] = month
            stamps.setdefault(dev, set()).add(month)

        per = {}
        for dev, month, flag in events:
            bucket = per.setdefault(month, {"sellers": set(),
                                            "events": 0,
                                            "relist": 0})
            bucket["sellers"].add(dev)
            bucket["events"] += 1
            bucket["relist"] += flag

        out = []
        for month in sorted(per):
            bucket = per[month]
            sellers = len(bucket["sellers"])
            new_sellers = sum(1 for dev in bucket["sellers"]
                              if first[dev] == month)
            new_events = sum(1 for dev, stamp_month, _flag in events
                             if stamp_month == month
                             and first[dev] == month)
            out.append({
                "month": month,
                "seller_count": sellers,
                "new_seller_count": new_sellers,
                "returning_seller_count": sellers - new_sellers,
                "listing_event_count": bucket["events"],
                "relisting_event_count": bucket["relist"],
                "new_event_count": new_events,
                "returning_event_count": bucket["events"] - new_events,
                "avg_events_per_seller": (bucket["events"]
                                          / float(sellers)),
            })

        seller_count = len(first)
        repeat = sum(1 for months in stamps.values() if len(months) > 1)
        relisting_sellers = len(set(
            dev for dev, _month, flag in events if flag))
        return {"month_count": len(out),
                "seller_count": seller_count,
                "listing_event_count": sum(
                    row["listing_event_count"] for row in out),
                "relisting_event_count": sum(
                    row["relisting_event_count"] for row in out),
                "relisting_seller_count": relisting_sellers,
                "repeat_seller_count": repeat,
                "repeat_rate": ((repeat / float(seller_count))
                                if seller_count else None),
                "returning_event_count": sum(
                    row["returning_event_count"] for row in out),
                "first_month": out[0]["month"] if out else None,
                "last_month": out[-1]["month"] if out else None,
                "disclaimer": self.disclaimer,
                "months": out}

'''


def main():
    text = io.open(TARGET, encoding="utf-8").read()
    anchor = "    def api_market_buyer_retention(self):"
    assert text.count(anchor) == 1, "anchor not unique"
    assert "api_market_seller_cohort" not in text, "face already present"
    text = text.replace(anchor, METHOD + anchor)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("inserted api_market_seller_cohort before the retention face")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())