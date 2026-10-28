# -*- coding: utf-8 -*-
"""R2188 product insert: APIMarketFace.api_seller_supply.

Criteria AC-SSUP1..AC-SSUP8 were written into the R2178 10/10
explore-queue row BEFORE this code existed.
"""
import io

P = "src/sandbox/ledger/apimarket.py"
s = io.open(P, encoding="utf-8").read()

ANCHOR = ('                "history": history,\n'
          '                "disclaimer": self.disclaimer}\n'
          "\n"
          "    def api_search(")
assert s.count(ANCHOR) == 1, s.count(ANCHOR)

METHOD = '''                "history": history,
                "disclaimer": self.disclaimer}

    def api_seller_supply(self, dev_account, low_stock_threshold=1):
        """Seller-side supply rollup (criteria AC-SSUP1..AC-SSUP8
        pre-registered in the R2178 10/10 explore-queue row BEFORE
        this code existed).

        api_supply and api_supply_history answer ONE listing, and
        api_seller_todo answers one duty row, so a seller holding N
        listings had to open api_supply N times to learn how much
        stock the shop actually carries. This face rolls the shop up:
        how many listings are live, how many units are declared, how
        many are sold out, and how many sit at or below a low-stock
        threshold.

        Row authority is the listing table (every listing the seller
        ever published, retired ones included, ordered by
        listing_id), so an empty shelf is an honest zero row set.
        Every scarcity quantity rides the single _supply_full seam
        that api_supply, api_supply_history and the purchase gate
        already trust, so a purchase, a refund or a restock moves
        this face in the same step it moves the per-listing faces -
        no second bookkeeping copy exists.

        A listing published WITHOUT a supply is unlimited: its
        supply and remaining are None, sold_out and low_stock are
        False, and it is excluded from the two supply totals while
        its sold count still counts (the sale really happened).
        Retired listings keep their row and every historical figure;
        re-listing flips only the delisted flag.

        low_stock_threshold defaults to 1 and counts a tracked
        listing whose remaining units are at or below it; threshold 0
        therefore counts only sold-out shelves. The account shape
        gate runs before the threshold gate, and both run before any
        read. Pure read: zero row mutations, zero token movement.
        """
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        if (isinstance(low_stock_threshold, bool)
                or not isinstance(low_stock_threshold, int)
                or low_stock_threshold < 0):
            raise ApiMarketError(E_AM_BAD_ARGS,
                                 "threshold=%r"
                                 % (low_stock_threshold,))
        threshold = int(low_stock_threshold)
        with self._lock:
            listing_rows = self._conn.execute(
                "SELECT listing_id, listing_key FROM apimarket_listings"
                " WHERE dev_account = ? ORDER BY listing_id",
                (dev_account,)).fetchall()
            rows = []
            live = 0
            retired = 0
            tracked = 0
            unlimited = 0
            sold_out_count = 0
            low_stock_count = 0
            total_effective = 0
            total_sold = 0
            total_remaining = 0
            total_restocked = 0
            total_restock_count = 0
            for listing_id, listing_key in listing_rows:
                _cycle, delisted, _stamp = self._cycle_state(listing_id)
                (base_supply, effective, restocked, sold, remaining,
                 sold_out, restock_count) = self._supply_full(listing_id)
                if delisted:
                    retired += 1
                else:
                    live += 1
                total_sold += sold
                total_restocked += restocked
                total_restock_count += restock_count
                if effective is None:
                    unlimited += 1
                    low_stock = False
                    sold_out = False
                else:
                    tracked += 1
                    total_effective += int(effective)
                    total_remaining += int(remaining or 0)
                    if sold_out:
                        sold_out_count += 1
                    low_stock = bool(remaining is not None
                                     and int(remaining) <= threshold)
                    if low_stock:
                        low_stock_count += 1
                rows.append(
                    {"listing_id": int(listing_id),
                     "listing_key": listing_key,
                     "delisted": bool(delisted),
                     "supply": effective,
                     "base_supply": base_supply,
                     "restocked_units": restocked,
                     "restock_count": restock_count,
                     "sold": sold,
                     "remaining": remaining,
                     "sold_out": bool(sold_out),
                     "low_stock": low_stock})
        return {"dev_account": str(dev_account),
                "listing_count": len(rows),
                "live_listing_count": live,
                "retired_listing_count": retired,
                "tracked_listing_count": tracked,
                "unlimited_listing_count": unlimited,
                "sold_out_listing_count": sold_out_count,
                "low_stock_listing_count": low_stock_count,
                "total_effective_supply":
                    total_effective if tracked else None,
                "total_sold": total_sold,
                "total_remaining": total_remaining if tracked else None,
                "total_restocked_units": total_restocked,
                "total_restock_count": total_restock_count,
                "low_stock_threshold": threshold,
                "disclaimer": self.disclaimer,
                "listings": rows}

    def api_search('''

s = s.replace(ANCHOR, METHOD)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("PRODUCT INSERT OK")