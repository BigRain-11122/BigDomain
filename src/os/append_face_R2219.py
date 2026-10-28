"""Append the R2219 product face to apimarket.py (ASCII, LF, utf-8).

Usage: python src/os/append_face_R2219.py
"""

import io
import os

CODE = u'''

    def api_market_conversion_months(self):
        """Market-wide monthly watch-to-purchase conversion (criteria
        AC-MCV1..AC-MCV8 registered in the R2213 explore seed row
        claimed in R2219 BEFORE this code existed).

        api_watch_conversion answers a LIFETIME funnel over the live
        watch set and api_market_watch_months answers watch flow, so
        whether one month's attention actually turned into sales had
        no face - the core quality-of-demand reading.

        Booking law: a watch books ONLY in the UTC month of its own
        watched_utc. An unwatch is not an event for this face, so a
        withdrawn watch keeps the month it landed in and never
        disappears from history (the honest difference from the live
        set funnel face). A purchase never re-dates the watch month.

        Directional law, identical to api_watch_conversion: converted
        when the buyer's unrefunded purchase on that listing is
        stamped at or after the watch stamp (equal stamps convert at
        zero seconds); pre_owned when the unrefunded purchase predates
        the watch, which can never convert and is excluded from the
        funnel denominator; pending when there is no purchase yet or
        the purchase was refunded (the net law, so a later refund
        lowers that month's rate without moving the month keys).

        Rate and latency: conversion_rate is converted over funnel,
        None when the funnel is empty and never a fabricated zero; the
        average is pooled over every converted watch in scope (not the
        mean of the month means), the median is the middle value or
        the midpoint for an even count, and all four latency fields
        are None when nothing converted.

        The grid is contiguous from the first to the last watch month,
        so a month with no watch still carries an honest zero row.

        No arguments, so no gate to run: pure read, zero row
        mutations and zero token movement."""
        def _secs(earlier, later):
            fmt = "%Y-%m-%dT%H:%M:%SZ"
            start = datetime.datetime.strptime(str(earlier), fmt)
            end = datetime.datetime.strptime(str(later), fmt)
            return int((end - start).total_seconds())

        with self._lock:
            raw = self._conn.execute(
                "SELECT w.watch_id, w.watched_utc, p.purchased_utc,"
                " (SELECT 1 FROM apimarket_refunds f"
                " WHERE f.purchase_id = p.purchase_id)"
                " FROM apimarket_watchlist w"
                " LEFT JOIN apimarket_purchases p"
                " ON p.listing_id = w.listing_id"
                " AND p.buyer_id = w.buyer_id"
                " ORDER BY w.watch_id").fetchall()
            watches = []
            for r in raw:
                purchased = r[2]
                if purchased is None or r[3] is not None:
                    state, seconds = "pending", None
                else:
                    delta = _secs(r[1], purchased)
                    if delta < 0:
                        state, seconds = "pre_owned", None
                    else:
                        state, seconds = "converted", delta
                watches.append({"month": str(r[1])[:7],
                                "state": state, "seconds": seconds})

        def _block(items):
            total = len(items)
            pre_owned = sum(1 for w in items
                            if w["state"] == "pre_owned")
            converted = sorted(w["seconds"] for w in items
                               if w["state"] == "converted")
            funnel = total - pre_owned
            if converted:
                mid = len(converted) // 2
                median = (float(converted[mid]) if len(converted) % 2
                          else (converted[mid - 1]
                                + converted[mid]) / 2.0)
                avg = float(sum(converted)) / len(converted)
                fastest = converted[0]
                slowest = converted[-1]
            else:
                median = None
                avg = None
                fastest = None
                slowest = None
            return {
                "watch_count": total,
                "pre_owned_count": pre_owned,
                "funnel_count": funnel,
                "converted_count": len(converted),
                "pending_count": funnel - len(converted),
                "conversion_rate": (float(len(converted)) / funnel
                                    if funnel else None),
                "avg_convert_seconds": avg,
                "median_convert_seconds": median,
                "fastest_convert_seconds": fastest,
                "slowest_convert_seconds": slowest}

        envelope = _block(watches)
        grid = _contiguous_months(sorted(set(w["month"]
                                             for w in watches)))
        rows = []
        for month in grid:
            row = {"month": month}
            row.update(_block([w for w in watches
                               if w["month"] == month]))
            rows.append(row)
        out = {"month_count": len(rows),
               "first_month": rows[0]["month"] if rows else None,
               "last_month": rows[-1]["month"] if rows else None}
        out.update(envelope)
        out["disclaimer"] = self.disclaimer
        out["months"] = rows
        return out
'''


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "sandbox", "ledger", "apimarket.py")
    data = io.open(path, "rb").read()
    if b"def api_market_conversion_months" in data:
        print("ALREADY-PRESENT")
        return 0
    if b"\r\n" in data:
        print("REFUSED-CRLF")
        return 2
    with io.open(path, "a", encoding="utf-8", newline="") as handle:
        handle.write(CODE)
    print("APPENDED-%d" % len(CODE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())