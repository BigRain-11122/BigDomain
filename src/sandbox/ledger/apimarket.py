"""Developer API marketplace face over the token ledger sandbox
(BigDomain explore queue, claimed round R1763; canon = the
"API market listing" line: developer service listing / purchase
with revenue split / purchaser-only rating three domains; seed =
tmarket.py listing-idempotence + rating-gate structure reuse and
apidev.py developer registry. The service payload itself is
caller-supplied metadata - the marketplace models the
compliance-bearing trade pipeline, not the endpoint runtime.)

Three domains ride the P-47-2b token ledger:

  listing  : only a registered developer (the DevKeyFace.dev_board
            public read face shows at least one key row -
            referenced, never copied; zero api_dev_keys direct
            reads) may list one service per (dev_account,
            listing_key); the registry gate runs BEFORE the content
            gate, so an off-register publisher never burns a
            msgSecCheck call (cost-saving posture); the title and
            the description pass the content gate BEFORE any row
            is stored (msgSecCheck pre-gate; sandbox = wordlist
            mock SecGate injected by the caller); the declared
            AIGC label persists on the row.
  split    : each purchase is exactly one spend bound to its tx,
            then exactly one developer share entry out of
            pool:share (the incentive.py per-entry one-share
            structure, reused by reference - not rebuilt); the
            integer split law is floor + input-order remainder
            with zero rounding loss (same law as tmarket /
            settlement apportion), enforced structurally by a
            DB CHECK.
  rating   : only a purchaser of the listing may rate it, one
            immutable rating per (buyer, listing), stars 1..5;
            the aggregate view is a deterministic pure read.

Pre-registered criteria AC-AM1..AC-AM7 live in the R1763
explore-queue row and were written before this code existed
(honesty law).

Split weights are sandbox-only defaults ([needs-CEO] adoption
face): the production dev/platform ratio and every listing price
point are a P1 item for CEO, approval-only. This module ships no
parameter values into any config file.

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: independent SQLite file apimarket.db next to the ledger
DB (single writer, same pattern as sec_degraded / notify
precedents; zero ledger schema touch - the fingerprint sentinel
stays CLEAN).
"""

import datetime
import json
import os
import sqlite3
import threading

E_AM_BAD_ACCOUNT = "E_AM_BAD_ACCOUNT"      # AC-AM1 / AC-AM7
E_AM_BAD_ARGS = "E_AM_BAD_ARGS"            # AC-AM1 / AC-AM7
E_AM_BAD_PRICE = "E_AM_BAD_PRICE"          # AC-AM1 / AC-AM7
E_AM_DUP_LISTING = "E_AM_DUP_LISTING"      # AC-AM1
E_AM_NOT_DEV = "E_AM_NOT_DEV"              # AC-AM2 (registry gate)
E_AM_CONTENT_REJECTED = "E_AM_CONTENT_REJECTED"  # AC-AM3
E_AM_GATE_ERROR = "E_AM_GATE_ERROR"        # AC-AM3 (runtime fault)
E_AM_NO_GATE = "E_AM_NO_GATE"              # AC-AM3 (unwired gate)
E_AM_NO_DISCLAIMER = "E_AM_NO_DISCLAIMER"  # AC-AM6
E_AM_UNKNOWN_LISTING = "E_AM_UNKNOWN_LISTING"  # AC-AM1 / AC-AM4
E_AM_PURCHASE_DUP = "E_AM_PURCHASE_DUP"    # AC-AM4
E_AM_SELF_BUY = "E_AM_SELF_BUY"           # AC-AM4
E_AM_BAD_SPLIT = "E_AM_BAD_SPLIT"          # AC-AM4 (param face)
E_AM_NOT_BUYER = "E_AM_NOT_BUYER"          # AC-AM5
E_AM_RATE_DUP = "E_AM_RATE_DUP"           # AC-AM5
E_AM_BAD_STARS = "E_AM_BAD_STARS"         # AC-AM5
E_AM_BAD_WINDOW = "E_AM_BAD_WINDOW"      # R2022 windowed read face
E_AM_DELISTED = "E_AM_DELISTED"           # AC-AMD5 (retired listing)
E_AM_NOT_OWNER = "E_AM_NOT_OWNER"         # AC-AMD2 (ownership gate)
E_AM_ALREADY_DELISTED = "E_AM_ALREADY_DELISTED"  # AC-AMD3

_CONTENT_REJECTED_CODE = "E_CONTENT_REJECTED"  # lobby SecGate hit

# Sandbox-only split defaults ([needs-CEO] adoption face, AC-AM4):
# the developer leg is first in apportion order, so the single
# remainder token of the integer law lands on the developer side.
SANDBOX_PARAMS = {
    "dev_weight": 70,
    "platform_weight": 30,
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS apimarket_listings (
    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dev_account TEXT NOT NULL,
    listing_key TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    token_price INTEGER NOT NULL CHECK (token_price > 0),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    listed_utc TEXT NOT NULL,
    UNIQUE (dev_account, listing_key)
);
CREATE TABLE IF NOT EXISTS apimarket_purchases (
    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    price_paid INTEGER NOT NULL CHECK (price_paid > 0),
    dev_share INTEGER NOT NULL CHECK (dev_share >= 0),
    platform_share INTEGER NOT NULL CHECK (platform_share >= 0),
    spend_tx TEXT NOT NULL,
    dev_share_tx TEXT NOT NULL,
    purchased_utc TEXT NOT NULL,
    UNIQUE (buyer_id, listing_id),
    CHECK (dev_share + platform_share = price_paid)
);
CREATE TABLE IF NOT EXISTS apimarket_ratings (
    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    stars INTEGER NOT NULL CHECK (stars IN (1, 2, 3, 4, 5)),
    rated_utc TEXT NOT NULL,
    UNIQUE (buyer_id, listing_id)
);
CREATE TABLE IF NOT EXISTS apimarket_delistings (
    delist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    delisted_utc TEXT NOT NULL,
    UNIQUE (listing_id)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _assert_month(window):
    """Strict calendar-month validation for the YYYY-MM window
    (the civicpoints _assert_month law, windowed-read family
    R1996/R1997/R1999/R2015): strptime alone is lenient about
    zero padding and silently swallows trailing garbage
    patterns, so the parse is round-tripped and must reproduce
    the input verbatim."""
    if not isinstance(window, str):
        raise ApiMarketError(E_AM_BAD_WINDOW, "window must be a string")
    try:
        parsed = datetime.datetime.strptime(window, "%Y-%m")
    except ValueError:
        raise ApiMarketError(E_AM_BAD_WINDOW, "bad window: " + window)
    if parsed.strftime("%Y-%m") != window:
        raise ApiMarketError(E_AM_BAD_WINDOW, "bad window: " + window)
    return window


def split_amount(price, params=None):
    """Pure integer split (AC-AM4): floor for both legs first, then
    the remainder is distributed one token at a time in input
    order (developer first) - the landing total equals the price
    exactly, with zero rounding loss. Deterministic, zero RNG."""
    p = params or SANDBOX_PARAMS
    dw = p["dev_weight"]
    pw = p["platform_weight"]
    total_w = dw + pw
    dev = (price * dw) // total_w
    platform = (price * pw) // total_w
    remainder = price - dev - platform
    if remainder > 0 and dw > 0:
        dev += 1
        remainder -= 1
    platform += remainder
    return dev, platform


class ApiMarketError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class APIMarketFace:
    """Developer API marketplace face. Own independent SQLite file
    (single writer); every market mutation runs inside BEGIN
    IMMEDIATE. Listing/purchase/rating rows are immutable once
    written (zero UPDATE surface). Ledger movement only through
    the Ledger public API (spend / share_from_pool). The content
    gate, the developer-key face and the disclaimer are injected
    (dependency injection: the lobby SecGate and DevKeyFace
    products are referenced, never copied); a missing gate or an
    empty disclaimer refuses construction - no gate, no door."""

    def __init__(self, ledger, devkeys, gate, disclaimer, params=None):
        if ledger is None:
            raise ApiMarketError(E_AM_BAD_ARGS, "ledger face required")
        self.led = ledger
        if devkeys is None or not hasattr(devkeys, "dev_board"):
            raise ApiMarketError(E_AM_BAD_ARGS, "devkeys face must"
                                 " expose dev_board")
        self.devkeys = devkeys
        if gate is None or not callable(getattr(gate, "check_text", None)):
            raise ApiMarketError(E_AM_NO_GATE, "content gate required")
        self.gate = gate
        text = str(disclaimer or "").strip()
        if not text:
            raise ApiMarketError(E_AM_NO_DISCLAIMER,
                                 "resident disclaimer required")
        self.disclaimer = text
        self.params = dict(params or SANDBOX_PARAMS)
        self._check_params()
        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(ledger.db_path)),
            "apimarket.db")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                      isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def _check_params(self):
        p = self.params
        for name in ("dev_weight", "platform_weight"):
            weight = p.get(name)
            if (not isinstance(weight, int) or isinstance(weight, bool)
                    or weight < 1):
                raise ApiMarketError(E_AM_BAD_SPLIT, str(weight))

    def close(self):
        with self._lock:
            self._conn.close()

    # -- gate helpers (fail-closed end to end) ---------------------------

    def _gate_check(self, text):
        """Run the injected content gate. A wordlist hit maps to
        E_AM_CONTENT_REJECTED; ANY other failure (offline gate,
        runtime fault) maps to E_AM_GATE_ERROR - never a silent
        pass. Zero rows are stored on either path (AC-AM3)."""
        try:
            self.gate.check_text(text)
        except Exception as exc:  # noqa: BLE001 (fail-closed wrap)
            if getattr(exc, "code", None) == _CONTENT_REJECTED_CODE:
                raise ApiMarketError(E_AM_CONTENT_REJECTED,
                                     getattr(exc, "word", ""))
            raise ApiMarketError(E_AM_GATE_ERROR, str(exc))

    def _is_registered_dev(self, dev_account):
        """Registry gate through the apidev public read face
        (AC-AM2): a developer is in-register when the board shows
        at least one key row. Zero direct api_dev_keys reads."""
        board = self.devkeys.dev_board(dev_account)
        return len(board.get("keys", [])) > 0

    # -- listing domain ----------------------------------------------------

    def publish_api(self, dev_account, listing_key, title,
                    description, payload, token_price, ai_generated):
        """List one developer service: the registry gate runs
        first (off-register publishers never reach the content
        gate, so no msgSecCheck call is burned - AC-AM2), then
        the content gate on title AND description before any row
        exists (publish-time refusal), then exactly one row per
        (dev_account, listing_key) - a repeat is rejected with
        zero rows (AC-AM1). The declared AIGC label persists on
        the row and every listing surface shows it (AC-AM6)."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        key = str(listing_key or "").strip()
        t = str(title or "")
        d = str(description or "")
        if not key:
            raise ApiMarketError(E_AM_BAD_ARGS, "listing key required")
        if not t.strip():
            raise ApiMarketError(E_AM_BAD_ARGS, "title required")
        if (not isinstance(token_price, int) or isinstance(token_price, bool)
                or token_price <= 0):
            raise ApiMarketError(E_AM_BAD_PRICE, str(token_price))
        if not isinstance(payload, (dict, list)) or not payload:
            raise ApiMarketError(E_AM_BAD_ARGS,
                                 "service payload required")
        if not isinstance(ai_generated, bool):
            raise ApiMarketError(E_AM_BAD_ARGS, "ai_generated must be bool")
        body = json.dumps(payload, sort_keys=True)
        with self._lock:
            if not self._is_registered_dev(dev_account):
                raise ApiMarketError(E_AM_NOT_DEV, dev_account)
            self._gate_check(t)   # zero rows stored on rejection
            self._gate_check(d)
            row = self._conn.execute(
                "SELECT listing_id FROM apimarket_listings"
                " WHERE dev_account = ? AND listing_key = ?",
                (dev_account, key)).fetchone()
            if row is not None:
                raise ApiMarketError(E_AM_DUP_LISTING, key)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_listings (dev_account,"
                    " listing_key, title, description, payload_json,"
                    " token_price, ai_label, listed_utc)"
                    " VALUES (?,?,?,?,?,?,?,?)",
                    (dev_account, key, t, d, body, token_price,
                     1 if ai_generated else 0, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ApiMarketError(E_AM_DUP_LISTING, key)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"listing_id": cur.lastrowid, "dev_account": dev_account,
                "listing_key": key, "title": t,
                "token_price": token_price,
                "ai_label": 1 if ai_generated else 0}

    def _require_listing(self, listing_id):
        """Validation + lookup under no lock (caller holds it).
        Returns (listing_id, dev_account, token_price)."""
        if (not isinstance(listing_id, int) or isinstance(listing_id, bool)
                or listing_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(listing_id))
        row = self._conn.execute(
            "SELECT listing_id, dev_account, token_price"
            " FROM apimarket_listings WHERE listing_id = ?",
            (listing_id,)).fetchone()
        if row is None:
            raise ApiMarketError(E_AM_UNKNOWN_LISTING, str(listing_id))
        return row

    def _delisted_utc(self, listing_id):
        """Append-only delisting stamp of one listing (None when
        still live). Caller holds the lock."""
        row = self._conn.execute(
            "SELECT delisted_utc FROM apimarket_delistings"
            " WHERE listing_id = ?", (listing_id,)).fetchone()
        return None if row is None else row[0]

    def delist_api(self, dev_account, listing_id):
        """Retire one listing (the seller-side door this face never
        had). Gate order pinned by AC-AMD4: account shape first,
        then the listing shape/existence gate, then ownership, then
        the already-retired state. Exactly one append-only
        apimarket_delistings row per listing (UNIQUE listing_id);
        a repeat answers E_AM_ALREADY_DELISTED with zero new rows,
        so the first delisted_utc is never rewritten. Delisting
        moves zero tokens and deletes nothing: purchases and
        ratings stay on the books, the market board just stops
        offering the row."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            listing = self._require_listing(listing_id)
            if listing[1] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, listing_id))
            if self._delisted_utc(listing_id) is not None:
                raise ApiMarketError(E_AM_ALREADY_DELISTED,
                                     str(listing_id))
            key = self._conn.execute(
                "SELECT listing_key FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()[0]
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO apimarket_delistings (listing_id,"
                    " dev_account, delisted_utc) VALUES (?,?,?)",
                    (listing_id, dev_account, stamp))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ApiMarketError(E_AM_ALREADY_DELISTED,
                                     str(listing_id))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"listing_id": listing_id, "dev_account": dev_account,
                "listing_key": key, "delisted": True,
                "delisted_utc": stamp, "already": False,
                "disclaimer": self.disclaimer}

    # -- purchase + split domain -------------------------------------------

    def purchase_api(self, buyer_id, listing_id, ref):
        """Buy one listed service: exactly one spend per (buyer,
        listing) bound to its tx; a repeat purchase is rejected
        BEFORE the spend so the balance never moves twice;
        self-purchase is rejected outright (anti-farm); the
        developer share is one share entry out of pool:share with
        the integer split law (AC-AM4). Buyers are ordinary usr:*
        residents - the developer gate is a listing-side face only
        (AC-AM2 structure note). Returns the provenance envelope
        with the resident disclaimer (AC-AM6)."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        r = str(ref or "").strip()
        if not r:
            raise ApiMarketError(E_AM_BAD_ARGS, "purchase ref required")
        with self._lock:
            listing = self._require_listing(listing_id)
            if self._delisted_utc(listing_id) is not None:
                raise ApiMarketError(E_AM_DELISTED, str(listing_id))
            if listing[1] == buyer_id:
                raise ApiMarketError(E_AM_SELF_BUY,
                                     "%s on own listing %s"
                                     % (buyer_id, listing_id))
            row = self._conn.execute(
                "SELECT purchase_id FROM apimarket_purchases"
                " WHERE buyer_id = ? AND listing_id = ?",
                (buyer_id, listing_id)).fetchone()
            if row is not None:
                raise ApiMarketError(E_AM_PURCHASE_DUP,
                                     "%s/%s" % (buyer_id, listing_id))
            price = int(listing[2])
            dev_share, platform_share = split_amount(
                price, self.params)
            self.led.ensure_account(buyer_id,
                                    census_avatar_id=buyer_id[4:])
            spend_tx = self.led.spend(buyer_id, price, r, "order")
            share_tx = ""
            if dev_share > 0:
                share_tx = self.led.share_from_pool(
                    "pool:share", listing[1], dev_share,
                    "apimarket:share:%s" % spend_tx,
                    ref_type="settlement",
                    action="apimarket_dev_share")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_purchases (listing_id,"
                    " buyer_id, price_paid, dev_share, platform_share,"
                    " spend_tx, dev_share_tx, purchased_utc)"
                    " VALUES (?,?,?,?,?,?,?,?)",
                    (listing_id, buyer_id, price, dev_share,
                     platform_share, spend_tx, share_tx, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ApiMarketError(E_AM_PURCHASE_DUP,
                                     "%s/%s" % (buyer_id, listing_id))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"purchase_id": cur.lastrowid, "listing_id": listing_id,
                "buyer_id": buyer_id, "price_paid": price,
                "dev_share": dev_share, "platform_share": platform_share,
                "spend_tx": spend_tx, "dev_share_tx": share_tx,
                "disclaimer": self.disclaimer}

    # -- rating domain -------------------------------------------------------

    def rate_api(self, buyer_id, listing_id, stars):
        """Rate a purchased listing: purchaser-only fail-closed
        gate, one immutable rating per (buyer, listing), stars
        1..5 (AC-AM5). Append-only - a repeat is rejected, never
        updated."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        if (not isinstance(stars, int) or isinstance(stars, bool)
                or stars < 1 or stars > 5):
            raise ApiMarketError(E_AM_BAD_STARS, str(stars))
        with self._lock:
            self._require_listing(listing_id)
            bought = self._conn.execute(
                "SELECT purchase_id FROM apimarket_purchases"
                " WHERE buyer_id = ? AND listing_id = ?",
                (buyer_id, listing_id)).fetchone()
            if bought is None:
                raise ApiMarketError(E_AM_NOT_BUYER,
                                     "%s/%s" % (buyer_id, listing_id))
            row = self._conn.execute(
                "SELECT rating_id FROM apimarket_ratings"
                " WHERE buyer_id = ? AND listing_id = ?",
                (buyer_id, listing_id)).fetchone()
            if row is not None:
                raise ApiMarketError(E_AM_RATE_DUP,
                                     "%s/%s" % (buyer_id, listing_id))
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_ratings (listing_id,"
                    " buyer_id, stars, rated_utc) VALUES (?,?,?,?)",
                    (listing_id, buyer_id, stars, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ApiMarketError(E_AM_RATE_DUP,
                                     "%s/%s" % (buyer_id, listing_id))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"rating_id": cur.lastrowid, "listing_id": listing_id,
                "buyer_id": buyer_id, "stars": stars}

    # -- read faces -----------------------------------------------------------

    def _agg_rating(self, listing_id):
        row = self._conn.execute(
            "SELECT COUNT(*), COALESCE(AVG(stars), 0)"
            " FROM apimarket_ratings WHERE listing_id = ?",
            (listing_id,)).fetchone()
        return int(row[0]), float(row[1])

    def api_view(self, listing_id):
        """One listing surface: metadata + declared AIGC label +
        purchase/rating aggregates, envelope carries the resident
        non-advisory disclaimer (AC-AM6). Pure read."""
        with self._lock:
            row = self._conn.execute(
                "SELECT listing_id, dev_account, listing_key, title,"
                " description, token_price, ai_label, listed_utc"
                " FROM apimarket_listings WHERE listing_id = ?",
                (listing_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_LISTING,
                                     str(listing_id))
            n_buy = self._conn.execute(
                "SELECT COUNT(*) FROM apimarket_purchases"
                " WHERE listing_id = ?", (listing_id,)).fetchone()[0]
            n_rate, avg = self._agg_rating(listing_id)
            stamp = self._delisted_utc(listing_id)
        return {"listing_id": int(row[0]), "dev_account": row[1],
                "listing_key": row[2], "title": row[3],
                "description": row[4], "token_price": int(row[5]),
                "ai_label": int(row[6]), "listed_utc": row[7],
                "purchase_count": int(n_buy), "rating_count": n_rate,
                "rating_avg": avg,
                "delisted": stamp is not None,
                "delisted_utc": stamp,
                "disclaimer": self.disclaimer}

    def api_board(self):
        """Whole-market listing surface: every row carries the
        declared AIGC label (presentation-face law, AC-AM6); the
        envelope carries the resident disclaimer. Retired listings
        are excluded from the market board (AC-AMD6) while their
        history stays readable through api_view/api_ratings/
        api_sales. Pure read."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT listing_id, dev_account, listing_key, title,"
                " token_price, ai_label FROM apimarket_listings"
                " WHERE listing_id NOT IN (SELECT listing_id FROM"
                " apimarket_delistings)"
                " ORDER BY listing_id").fetchall()
            out = []
            for r in rows:
                n_rate, avg = self._agg_rating(int(r[0]))
                out.append({"listing_id": int(r[0]),
                            "dev_account": r[1], "listing_key": r[2],
                            "title": r[3], "token_price": int(r[4]),
                            "ai_label": int(r[5]),
                            "rating_count": n_rate, "rating_avg": avg})
        return {"disclaimer": self.disclaimer, "listings": out}

    def api_ratings(self, listing_id):
        """Per-listing rating surface: immutable per-rater rows
        plus the deterministic aggregate (AC-AM5). Pure read."""
        with self._lock:
            self._require_listing(listing_id)
            rows = self._conn.execute(
                "SELECT buyer_id, stars, rated_utc FROM"
                " apimarket_ratings WHERE listing_id = ?"
                " ORDER BY rating_id", (listing_id,)).fetchall()
            n_rate, avg = self._agg_rating(listing_id)
        return {"listing_id": listing_id, "rating_count": n_rate,
                "rating_avg": avg, "disclaimer": self.disclaimer,
                "ratings": [{"buyer_id": r[0], "stars": int(r[1]),
                             "rated_utc": r[2]} for r in rows]}

    def api_sales(self, dev_account):
        """Per-developer sales ledger view: every purchase row of
        that developer's listings with its split amounts and bound
        txs (provenance, AC-AM4/AM6). Pure read; rows are
        immutable once written."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT p.purchase_id, p.listing_id, l.listing_key,"
                " p.buyer_id, p.price_paid, p.dev_share,"
                " p.platform_share, p.spend_tx, p.dev_share_tx,"
                " p.purchased_utc FROM apimarket_purchases p JOIN"
                " apimarket_listings l ON l.listing_id ="
                " p.listing_id WHERE l.dev_account = ?"
                " ORDER BY p.purchase_id", (dev_account,)).fetchall()
        return {"dev_account": dev_account,
                "disclaimer": self.disclaimer,
                "sales": [{"purchase_id": int(r[0]),
                           "listing_id": int(r[1]),
                           "listing_key": r[2], "buyer_id": r[3],
                           "price_paid": int(r[4]),
                           "dev_share": int(r[5]),
                           "platform_share": int(r[6]),
                           "spend_tx": r[7], "dev_share_tx": r[8],
                           "purchased_utc": r[9]} for r in rows]}

    def dev_sales_board(self, window=None):
        """Developer-level sales / revenue aggregation board
        (pre-registered AC-AMB1..AC-AMB7 in the R1978
        explore-queue row; the month-window read face
        AC-AMW1..AMW7 in the R2022 claim row - both written
        before this code existed).

        Row-set authority = the listing side: every distinct
        dev_account holding at least one listing row gets
        exactly one board row - a listed-but-unsold developer
        stays visible with an honest zero row (dormant
        participants are not hidden), and an account with zero
        listings never appears. Deterministic order:
        dev_revenue DESC, then purchase_count DESC, then
        dev_account ASC. Per-row conservation gross ==
        dev + platform holds structurally (integer split law).
        Pure read: zero row mutations on every table. The
        envelope carries the resident non-advisory disclaimer.

        Month window (windowed-read family, record-time law):
        an explicit strict YYYY-MM window slices BOTH row
        families by their own record time - listing_count by
        the listed_utc prefix, the purchase aggregates by the
        purchased_utc prefix - while the row set stays the
        dense ever-listed developer set (a developer with no
        in-window activity keeps an honest zero row; a
        listing's registration month never decides which
        month its sales land in). The window gate runs before
        any read (fail-closed, dedicated code). Envelope is
        additive: the default call keeps exactly the two
        envelope keys; an explicit window adds the window
        echo key."""
        if window is not None:
            window = _assert_month(window)   # gate before any read
        with self._lock:
            if window is None:
                rows = self._conn.execute(
                    "SELECT l.dev_account, COUNT(DISTINCT"
                    " l.listing_id) AS listing_count,"
                    " COALESCE(SUM(p.price_paid), 0) AS gross,"
                    " COALESCE(SUM(p.dev_share), 0) AS dev_rev,"
                    " COALESCE(SUM(p.platform_share), 0) AS plat_rev,"
                    " COUNT(p.purchase_id) AS purchases"
                    " FROM apimarket_listings l LEFT JOIN"
                    " apimarket_purchases p ON p.listing_id ="
                    " l.listing_id GROUP BY l.dev_account").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT l.dev_account, COUNT(DISTINCT CASE"
                    " WHEN substr(l.listed_utc, 1, 7) = ? THEN"
                    " l.listing_id END) AS listing_count,"
                    " COALESCE(SUM(CASE WHEN substr(p.purchased_utc,"
                    " 1, 7) = ? THEN p.price_paid END), 0) AS gross,"
                    " COALESCE(SUM(CASE WHEN substr(p.purchased_utc,"
                    " 1, 7) = ? THEN p.dev_share END), 0) AS dev_rev,"
                    " COALESCE(SUM(CASE WHEN substr(p.purchased_utc,"
                    " 1, 7) = ? THEN p.platform_share END), 0)"
                    " AS plat_rev, COUNT(CASE WHEN"
                    " substr(p.purchased_utc, 1, 7) = ? THEN"
                    " p.purchase_id END) AS purchases"
                    " FROM apimarket_listings l LEFT JOIN"
                    " apimarket_purchases p ON p.listing_id ="
                    " l.listing_id GROUP BY l.dev_account",
                    (window, window, window, window, window)).fetchall()
            board = []
            for r in rows:
                board.append({
                    "dev_account": r[0],
                    "listing_count": int(r[1]),
                    "purchase_count": int(r[5]),
                    "gross_revenue": int(r[2]),
                    "dev_revenue": int(r[3]),
                    "platform_revenue": int(r[4])})
            board.sort(key=lambda row: (-row["dev_revenue"],
                                       -row["purchase_count"],
                                       row["dev_account"]))
        env = {"disclaimer": self.disclaimer, "board": board}
        if window is not None:
            env["window"] = window
        return env
