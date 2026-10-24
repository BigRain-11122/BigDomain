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
E_AM_ALREADY_LIVE = "E_AM_ALREADY_LIVE"    # AC-AMRL2 (relist on live)
E_AM_PRICE_UNCHANGED = "E_AM_PRICE_UNCHANGED"  # AC-AMPR4
E_AM_METADATA_UNCHANGED = "E_AM_METADATA_UNCHANGED"  # AC-AMME6
E_AM_WATCH_DUP = "E_AM_WATCH_DUP"          # AC-AMWL5
E_AM_NOT_WATCHED = "E_AM_NOT_WATCHED"      # AC-AMWL3
E_AM_SUPPLY_EXHAUSTED = "E_AM_SUPPLY_EXHAUSTED"  # AC-AMSP3
E_AM_UNKNOWN_PURCHASE = "E_AM_UNKNOWN_PURCHASE"  # AC-AMRF2
E_AM_ALREADY_REFUNDED = "E_AM_ALREADY_REFUNDED"  # AC-AMRF4
E_AM_REFUND_UNFUNDABLE = "E_AM_REFUND_UNFUNDABLE"  # AC-AMRF5
E_AM_NOT_REFUNDED = "E_AM_NOT_REFUNDED"      # AC-AMRF7
E_AM_UNKNOWN_RATING = "E_AM_UNKNOWN_RATING"  # AC-AMRP4
E_AM_REPLY_DUP = "E_AM_REPLY_DUP"          # AC-AMRP5
E_AM_BAD_REPLY = "E_AM_BAD_REPLY"          # AC-AMRP3
E_AM_RATING_UNCHANGED = "E_AM_RATING_UNCHANGED"  # AC-AMRV4
E_AM_BAD_UNITS = "E_AM_BAD_UNITS"          # AC-AMRS2 (restock shape)
E_AM_SUPPLY_UNLIMITED = "E_AM_SUPPLY_UNLIMITED"  # AC-AMRS2 (no base)

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
    supply INTEGER,
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
CREATE TABLE IF NOT EXISTS apimarket_rating_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rating_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    previous_stars INTEGER NOT NULL,
    stars INTEGER NOT NULL CHECK (stars IN (1, 2, 3, 4, 5)),
    revised_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS apimarket_delistings (
    delist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    delisted_utc TEXT NOT NULL,
    cycle INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS apimarket_relistings (
    relist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    relisted_utc TEXT NOT NULL,
    cycle INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS apimarket_price_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    token_price INTEGER NOT NULL CHECK (token_price > 0),
    revised_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS apimarket_listing_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    revised_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS apimarket_watchlist (
    watch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id TEXT NOT NULL,
    listing_id INTEGER NOT NULL,
    watched_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS apimarket_unwatchings (
    unwatch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    listing_id INTEGER NOT NULL,
    unwatched_utc TEXT NOT NULL,
    UNIQUE (watch_id)
);
CREATE TABLE IF NOT EXISTS apimarket_rating_replies (
    reply_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rating_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    reply_text TEXT NOT NULL,
    replied_utc TEXT NOT NULL,
    UNIQUE (rating_id)
);
CREATE TABLE IF NOT EXISTS apimarket_refunds (
    refund_id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    dev_account TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    dev_share INTEGER NOT NULL CHECK (dev_share >= 0),
    platform_share INTEGER NOT NULL CHECK (platform_share >= 0),
    refund_tx TEXT NOT NULL,
    refunded_utc TEXT NOT NULL,
    reason TEXT NOT NULL,
    UNIQUE (purchase_id),
    CHECK (dev_share + platform_share = amount)
);
CREATE TABLE IF NOT EXISTS apimarket_supply_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    add_units INTEGER NOT NULL CHECK (add_units > 0),
    restocked_utc TEXT NOT NULL
);
"""


# Discovery sort modes (AC-AMSR2, pre-registered in the R2098
# explore-queue row BEFORE this code existed). The default (None)
# keeps the R2082 ordering - current price ascending, then
# listing_id ascending - so a caller that never passes a sort token
# reads a byte-identical contract.
_SEARCH_SORT_MODES = ("price_asc", "price_desc", "rating", "sales",
                      "newest")


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


def _price_bound(value, name):
    """Positive-integer price bound for the discovery band
    (AC-AMSQ6): None means unbounded, every other form must be a
    real positive int - bool is not an int here."""
    if value is None:
        return None
    if (not isinstance(value, int) or isinstance(value, bool)
            or value <= 0):
        raise ApiMarketError(E_AM_BAD_PRICE, str(value))
    return int(value)


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
        self._ensure_supply_column()
        self._ensure_lifecycle_schema()

    def _ensure_lifecycle_schema(self):
        """Idempotent forward migration for databases written
        before the re-list axis existed (AC-AMRL8). The old
        apimarket_delistings carried UNIQUE(listing_id) - one
        terminal retirement per listing - which the cycle law must
        relax, and SQLite cannot drop a constraint in place, so the
        table is rebuilt once: same rows, same ids, cycle 1. The
        rebuild runs only when the legacy shape is actually
        present, so an already-migrated database is never touched
        and every existing retirement keeps its original stamp."""
        cols = [r[1] for r in self._conn.execute(
            "PRAGMA table_info(apimarket_delistings)").fetchall()]
        row = self._conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table'"
            " AND name = 'apimarket_delistings'").fetchone()
        flat = str(row[0] or "").upper().replace(" ", "") \
            if row is not None else ""
        legacy_unique = "UNIQUE(LISTING_ID)" in flat
        if "cycle" in cols and not legacy_unique:
            return
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "ALTER TABLE apimarket_delistings RENAME TO"
                " apimarket_delistings_legacy")
            self._conn.execute(
                "CREATE TABLE apimarket_delistings ("
                " delist_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " listing_id INTEGER NOT NULL,"
                " dev_account TEXT NOT NULL,"
                " delisted_utc TEXT NOT NULL,"
                " cycle INTEGER NOT NULL DEFAULT 1)")
            cycle_expr = "cycle" if "cycle" in cols else "1"
            self._conn.execute(
                "INSERT INTO apimarket_delistings (delist_id,"
                " listing_id, dev_account, delisted_utc, cycle)"
                " SELECT delist_id, listing_id, dev_account,"
                " delisted_utc, %s FROM apimarket_delistings_legacy"
                " ORDER BY delist_id" % cycle_expr)
            self._conn.execute("DROP TABLE apimarket_delistings_legacy")
            self._conn.execute("COMMIT")
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise

    def _ensure_supply_column(self):
        """Idempotent forward migration for databases written
        before the supply axis existed (AC-AMSP7): the column is
        added only when absent, so old rows keep supply NULL and
        stay infinitely purchasable - the pre-change behaviour is
        preserved byte for byte."""
        cols = [r[1] for r in self._conn.execute(
            "PRAGMA table_info(apimarket_listings)").fetchall()]
        if "supply" not in cols:
            self._conn.execute(
                "ALTER TABLE apimarket_listings ADD COLUMN supply"
                " INTEGER")

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

    def _supply_full(self, listing_id):
        """Complete derived scarcity state of one listing (AC-AMRS1):
        the declared base supply (None = unlimited), the restocked
        units appended after it, the EFFECTIVE supply, the sold
        count read from the immutable purchase rows, the remaining
        units, the sold-out flag and the restock count. Nothing is
        stored twice - the effective supply is base plus the
        append-only restock rows and the remaining count is always
        derived, so a refused purchase can never desync either.
        Caller holds the lock."""
        row = self._conn.execute(
            "SELECT supply FROM apimarket_listings WHERE listing_id = ?",
            (listing_id,)).fetchone()
        base = row[0] if row is not None else None
        # AC-AMRS1: the restock axis is a sum, never a rewrite -
        # the listing row stays immutable and every restock event
        # survives in apimarket_supply_revisions in order.
        totals = self._conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(add_units), 0)"
            " FROM apimarket_supply_revisions"
            " WHERE listing_id = ?", (listing_id,)).fetchone()
        restock_count = int(totals[0])
        restocked = int(totals[1])
        bought = int(self._conn.execute(
            "SELECT COUNT(*) FROM apimarket_purchases"
            " WHERE listing_id = ?", (listing_id,)).fetchone()[0])
        # AC-AMRF6: a refunded unit returns to the shelf, so the
        # shelf count is the NET of immutable purchases and refunds.
        refunded = int(self._conn.execute(
            "SELECT COUNT(*) FROM apimarket_refunds"
            " WHERE listing_id = ?", (listing_id,)).fetchone()[0])
        sold = max(0, bought - refunded)
        if base is None:
            return (None, None, restocked, sold, None, False,
                    restock_count)
        effective = int(base) + restocked
        remaining = max(0, effective - sold)
        return (int(base), effective, restocked, sold, remaining,
                remaining == 0, restock_count)

    def _supply_state(self, listing_id):
        """Derived scarcity tuple (AC-AMSP1/AC-AMRS5): the effective
        supply (None = unlimited), the sold count, the remaining
        units and the sold-out flag. One single seam behind both the
        purchase gate and api_supply, so a restock moves every
        surface at once. Caller holds the lock."""
        _base, effective, _restocked, sold, remaining, sold_out, \
            _count = self._supply_full(listing_id)
        return effective, sold, remaining, sold_out

    # -- supply domain -----------------------------------------------------

    def restock_api(self, dev_account, listing_id, add_units):
        """Seller-side supply replenishment door (pre-registered
        AC-AMRS1..AC-AMRS8 in the R2095 explore-queue row BEFORE
        this code existed). Supply used to be write-once at publish
        time: a listing that sold out was dead forever and the
        seller had to publish a new listing_key, losing the
        purchases, ratings and price history attached to the old
        row. This window adds the replenishment leg as a cycle-safe
        sum: one append-only apimarket_supply_revisions row per
        call, never an UPDATE, so the base declaration and every
        earlier restock survive in order.

        Gate order pinned by AC-AMRS2: account shape first, then
        the listing shape/existence gate, then ownership, then the
        retired state, then the units shape, then the unlimited
        state (a listing published without a supply has no shelf to
        replenish, so it answers E_AM_SUPPLY_UNLIMITED instead of
        inventing one). A refused call writes zero rows and moves
        zero tokens."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            listing = self._require_listing(listing_id)
            if listing[1] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, listing_id))
            if self._delisted_utc(listing_id) is not None:
                raise ApiMarketError(E_AM_DELISTED, str(listing_id))
            if (not isinstance(add_units, int)
                    or isinstance(add_units, bool) or add_units < 1):
                raise ApiMarketError(E_AM_BAD_UNITS, str(add_units))
            (base, _effective, _restocked, _sold, _remaining,
             _sold_out, _count) = self._supply_full(listing_id)
            if base is None:
                raise ApiMarketError(E_AM_SUPPLY_UNLIMITED,
                                     str(listing_id))
            key = self._conn.execute(
                "SELECT listing_key FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()[0]
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_supply_revisions"
                    " (listing_id, dev_account, add_units, restocked_utc)"
                    " VALUES (?,?,?,?)",
                    (listing_id, dev_account, add_units, stamp))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            (base, effective, restocked, _sold, remaining,
             sold_out, count) = self._supply_full(listing_id)
        return {"revision_id": cur.lastrowid,
                "listing_id": listing_id,
                "dev_account": dev_account,
                "listing_key": key,
                "add_units": add_units,
                "base_supply": base,
                "restocked_units": restocked,
                "effective_supply": effective,
                "remaining": remaining,
                "sold_out": sold_out,
                "restock_count": count,
                "restocked_utc": stamp,
                "disclaimer": self.disclaimer}

    # -- listing domain ----------------------------------------------------

    def publish_api(self, dev_account, listing_key, title,
                    description, payload, token_price, ai_generated,
                    supply=None):
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
        # Supply is a pre-lock shape gate (AC-AMSP5): a malformed
        # scarcity declaration is refused before the registry read
        # and before any msgSecCheck call, so a bad supply burns
        # zero gate calls and stores zero rows. None = unlimited.
        if (supply is not None
                and (not isinstance(supply, int) or isinstance(supply, bool)
                     or supply < 1)):
            raise ApiMarketError(E_AM_BAD_ARGS,
                                 "supply must be int >= 1 or None")
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
                    " token_price, ai_label, listed_utc, supply)"
                    " VALUES (?,?,?,?,?,?,?,?,?)",
                    (dev_account, key, t, d, body, token_price,
                     1 if ai_generated else 0, _now_utc(), supply))
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
                "ai_label": 1 if ai_generated else 0,
                "supply": supply}

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

    def _cycle_state(self, listing_id):
        """(cycle, delisted, delisted_utc) of one listing under the
        cycle law (AC-AMRL1). Publishing opens cycle 1; a delisting
        closes the cycle it lands in; a re-listing opens the next
        one. The current cycle is therefore one plus the number of
        append-only re-listing rows, and the listing is retired only
        when a delisting row exists FOR THAT cycle - so a listing
        that was retired and re-listed is live again without any row
        ever being rewritten. Caller holds the lock."""
        opened = self._conn.execute(
            "SELECT MAX(cycle) FROM apimarket_relistings"
            " WHERE listing_id = ?", (listing_id,)).fetchone()[0]
        cycle = 1 if opened is None else int(opened)
        row = self._conn.execute(
            "SELECT delisted_utc FROM apimarket_delistings"
            " WHERE listing_id = ? AND cycle = ?",
            (listing_id, cycle)).fetchone()
        return cycle, row is not None, (None if row is None else row[0])

    def _delisted_utc(self, listing_id):
        """Append-only retirement stamp of one listing's CURRENT
        cycle (None when live). Every read face keeps one seam, so
        the re-list door flips all of them at once. Caller holds
        the lock."""
        return self._cycle_state(listing_id)[2]

    def _current_price(self, listing_id, base_price=None):
        """Newest append-only revision wins; with no revision the
        immutable listing row speaks. Caller holds the lock."""
        row = self._conn.execute(
            "SELECT token_price FROM apimarket_price_revisions"
            " WHERE listing_id = ? ORDER BY revision_id DESC LIMIT 1",
            (listing_id,)).fetchone()
        if row is not None:
            return int(row[0])
        if base_price is not None:
            return int(base_price)
        return int(self._conn.execute(
            "SELECT token_price FROM apimarket_listings"
            " WHERE listing_id = ?", (listing_id,)).fetchone()[0])

    def _price_at_instant(self, listing_id, base_price, instant):
        """Asking price as of one instant (AC-WAL2): the newest
        append-only revision stamped at or before the instant wins,
        ties broken by revision_id; with no such revision the
        immutable base row speaks. A later revision never rewrites
        the price an earlier instant already saw. Caller holds the
        lock."""
        row = self._conn.execute(
            "SELECT token_price FROM apimarket_price_revisions"
            " WHERE listing_id = ? AND revised_utc <= ?"
            " ORDER BY revised_utc DESC, revision_id DESC LIMIT 1",
            (listing_id, instant)).fetchone()
        if row is not None:
            return int(row[0])
        return int(base_price)

    def _revision_stats(self, listing_id):
        """(revision_count, latest revised_utc or None). Caller
        holds the lock."""
        row = self._conn.execute(
            "SELECT COUNT(*), MAX(revision_id)"
            " FROM apimarket_price_revisions WHERE listing_id = ?",
            (listing_id,)).fetchone()
        latest_utc = None
        if row[1] is not None:
            latest_utc = self._conn.execute(
                "SELECT revised_utc FROM apimarket_price_revisions"
                " WHERE revision_id = ?", (row[1],)).fetchone()[0]
        return int(row[0]), latest_utc

    def _metadata_state(self, listing_id, base_title, base_description):
        """(effective_title, effective_description, revision_count,
        latest_revised_utc). The newest append-only metadata
        revision wins; with no revision the immutable listing row
        speaks. Caller holds the lock."""
        row = self._conn.execute(
            "SELECT title, description, revised_utc FROM"
            " apimarket_listing_revisions WHERE listing_id = ?"
            " ORDER BY revision_id DESC LIMIT 1",
            (listing_id,)).fetchone()
        count = int(self._conn.execute(
            "SELECT COUNT(*) FROM apimarket_listing_revisions"
            " WHERE listing_id = ?", (listing_id,)).fetchone()[0])
        if row is None:
            return base_title, base_description, 0, None
        return row[0], row[1], count, row[2]

    def delist_api(self, dev_account, listing_id):
        """Retire one listing (the seller-side door this face never
        had). Gate order pinned by AC-AMD4: account shape first,
        then the listing shape/existence gate, then ownership, then
        the already-retired state. One append-only
        apimarket_delistings row per closed cycle; a repeat answers
        E_AM_ALREADY_DELISTED with zero new rows, so the first
        delisted_utc of that cycle is never rewritten (a re-listed
        listing opens a new cycle and can be retired again -
        AC-AMRL3). Delisting moves zero tokens and deletes nothing:
        purchases and ratings stay on the books, the market board
        just stops offering the row."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            listing = self._require_listing(listing_id)
            if listing[1] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, listing_id))
            cycle, retired, _stamp = self._cycle_state(listing_id)
            if retired:
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
                    " dev_account, delisted_utc, cycle)"
                    " VALUES (?,?,?,?)",
                    (listing_id, dev_account, stamp, cycle))
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

    def relist_api(self, dev_account, listing_id):
        """Seller-side re-listing door: the missing return leg of
        the retirement door (AC-AMRL1/AC-AMRL2, pre-registered in
        the R2089 explore-queue row BEFORE this code existed).
        Retirement was terminal - a seller who fixed a broken
        service or came back after a pause had to publish a new
        listing_key and lose the purchases, ratings and price
        history attached to the old row. This window opens cycle
        N+1 instead: one append-only apimarket_relistings row, no
        row rewritten, and the listing is live again with every
        historical aggregate intact.

        Gate order pinned by AC-AMRL2: account shape first, then
        the listing shape/existence gate, then ownership, then the
        already-live state (a live listing has nothing to re-open,
        so it answers E_AM_ALREADY_LIVE). A refused call writes
        zero rows and moves zero tokens."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            listing = self._require_listing(listing_id)
            if listing[1] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, listing_id))
            cycle, retired, _stamp = self._cycle_state(listing_id)
            if not retired:
                raise ApiMarketError(E_AM_ALREADY_LIVE, str(listing_id))
            key = self._conn.execute(
                "SELECT listing_key FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()[0]
            stamp = _now_utc()
            new_cycle = cycle + 1
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO apimarket_relistings (listing_id,"
                    " dev_account, relisted_utc, cycle)"
                    " VALUES (?,?,?,?)",
                    (listing_id, dev_account, stamp, new_cycle))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"listing_id": listing_id, "dev_account": dev_account,
                "listing_key": key, "cycle": new_cycle,
                "relisted_utc": stamp, "live": True, "already": False,
                "disclaimer": self.disclaimer}

    def revise_price(self, dev_account, listing_id, token_price):
        """Seller-side repricing door (AC-AMPR1..AMPR4): one
        append-only revision row per call, never an UPDATE - the
        listing row stays immutable and every historical asking
        price survives in order. Gate order is pinned by
        AC-AMPR3: account shape first, then the listing
        shape/existence gate, then ownership, then the retired
        state, then the price shape, then the no-op state. A
        same-price call is refused with E_AM_PRICE_UNCHANGED and
        zero new rows; revising back to an older price is legal
        because it is a change against the CURRENT price.
        Repricing moves zero tokens."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            listing = self._require_listing(listing_id)
            if listing[1] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, listing_id))
            if self._delisted_utc(listing_id) is not None:
                raise ApiMarketError(E_AM_DELISTED, str(listing_id))
            if (not isinstance(token_price, int)
                    or isinstance(token_price, bool)
                    or token_price <= 0):
                raise ApiMarketError(E_AM_BAD_PRICE, str(token_price))
            previous = self._current_price(listing_id, listing[2])
            if token_price == previous:
                raise ApiMarketError(E_AM_PRICE_UNCHANGED,
                                     str(token_price))
            key = self._conn.execute(
                "SELECT listing_key FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()[0]
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_price_revisions"
                    " (listing_id, dev_account, token_price,"
                    " revised_utc) VALUES (?,?,?,?)",
                    (listing_id, dev_account, token_price, stamp))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            count, _latest = self._revision_stats(listing_id)
        return {"revision_id": cur.lastrowid,
                "listing_id": listing_id,
                "dev_account": dev_account,
                "listing_key": key,
                "previous_price": previous,
                "token_price": token_price,
                "revision_count": count,
                "revised_utc": stamp,
                "disclaimer": self.disclaimer}

    def edit_listing(self, dev_account, listing_id, title=None,
                     description=None):
        """Seller-side metadata revision door (pre-registered
        AC-AMME1..AMME8 in the R2083 explore-queue row BEFORE this
        code existed).

        publish_api writes the title and the description exactly
        once: after a listing exists there was no legal way to fix
        a typo or improve the copy - republishing collides with
        UNIQUE(dev_account, listing_key) and delisting is
        terminal. Price has revise_price, lifecycle has
        delist_api, metadata had nothing. This face closes it with
        one append-only apimarket_listing_revisions row per change;
        the listing row itself is never rewritten, so the original
        metadata survives as base forever (AC-AMME1).

        Either field may be omitted, in which case the current
        effective value carries into the new revision - every
        revision row stores the full effective pair, so history is
        self-describing (AC-AMME2).

        Gate order is pinned by AC-AMME3, every gate before any
        write: account shape, then listing shape/existence, then
        ownership, then the retired state, then field shape (at
        least one field, non-blank string), then the content gate
        on every supplied field (msgSecCheck pre-gate: a rejected
        edit stores zero rows and leaves the effective metadata
        untouched), then the no-change state. A same-values call
        answers E_AM_METADATA_UNCHANGED with zero new rows;
        revising back to an older value is legal because the
        comparison is against the CURRENT effective pair
        (AC-AMME6). Editing moves zero tokens."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            listing = self._require_listing(listing_id)
            if listing[1] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, listing_id))
            if self._delisted_utc(listing_id) is not None:
                raise ApiMarketError(E_AM_DELISTED, str(listing_id))
            if title is None and description is None:
                raise ApiMarketError(E_AM_BAD_ARGS,
                                     "title or description required")
            if title is not None and (not isinstance(title, str)
                                      or not title.strip()):
                raise ApiMarketError(E_AM_BAD_ARGS, str(title))
            if description is not None and (
                    not isinstance(description, str)
                    or not description.strip()):
                raise ApiMarketError(E_AM_BAD_ARGS, str(description))
            base = self._conn.execute(
                "SELECT listing_key, title, description FROM"
                " apimarket_listings WHERE listing_id = ?",
                (listing_id,)).fetchone()
            cur_title, cur_desc, count, _latest = self._metadata_state(
                listing_id, base[1], base[2])
            new_title = cur_title if title is None else title
            new_desc = cur_desc if description is None else description
            if title is not None:
                self._gate_check(title)   # zero rows on rejection
            if description is not None:
                self._gate_check(description)
            if new_title == cur_title and new_desc == cur_desc:
                raise ApiMarketError(E_AM_METADATA_UNCHANGED,
                                     str(listing_id))
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_listing_revisions"
                    " (listing_id, dev_account, title, description,"
                    " revised_utc) VALUES (?,?,?,?,?)",
                    (listing_id, dev_account, new_title, new_desc,
                     stamp))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"listing_id": listing_id,
                "dev_account": dev_account,
                "listing_key": base[0],
                "revision_id": cur.lastrowid,
                "previous_title": cur_title,
                "previous_description": cur_desc,
                "title": new_title,
                "description": new_desc,
                "metadata_revision_count": count + 1,
                "revised_utc": stamp,
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
            # Supply gate (AC-AMSP3/AC-AMSP4): refused AFTER the
            # buyer-specific gates, so a repeat buyer of the last
            # unit still hears the precise DUP cause, and BEFORE
            # any ledger movement, so a sold-out refusal never
            # spends a token.
            _supply, _sold, remaining, _sold_out = \
                self._supply_state(listing_id)
            if remaining == 0:
                raise ApiMarketError(E_AM_SUPPLY_EXHAUSTED,
                                     "%s/%s" % (buyer_id, listing_id))
            price = self._current_price(listing_id, listing[2])
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

    # -- refund domain -------------------------------------------------------

    def refund_api(self, buyer_id, purchase_id, reason=None):
        """Buyer-side refund door (pre-registered AC-AMRF1..AC-AMRF8
        in the R2088 explore-queue row BEFORE this code existed).

        Every forward door on this market was irreversible: a
        purchase spent tokens and wrote one immutable row, so a
        buyer who received nothing usable had no remedy and a
        seller had no return leg. This window adds the post-sale
        remedy face: one append-only apimarket_refunds row per
        purchase (UNIQUE(purchase_id)), and a four-entry ledger
        reversal that puts buyer, seller and both pools back to
        their pre-purchase balances exactly (integer split law,
        zero rounding).

        Gate order pinned by AC-AMRF3: account shape, then the
        purchase-id shape, then purchase existence, then ownership,
        then the already-refunded state, then the seller-side
        funding check. The funding check exists because the AC-L2
        balance floor is constitutional - the seller leg is
        debited, so a seller who already spent the proceeds cannot
        fund the reversal; that case fails closed with
        E_AM_REFUND_UNFUNDABLE and moves zero tokens rather than
        overdrawing an account (refuse, never chase).

        The ledger ref is derived from the purchase id, never from
        the caller: the ledger's UNIQUE(ref) is a second
        idempotency key behind the market gate, so a double refund
        cannot book twice even if the row gate were bypassed."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        if (not isinstance(purchase_id, int) or isinstance(purchase_id, bool)
                or purchase_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(purchase_id))
        text = "" if reason is None else str(reason).strip()
        with self._lock:
            row = self._conn.execute(
                "SELECT listing_id, buyer_id, price_paid, dev_share,"
                " platform_share FROM apimarket_purchases"
                " WHERE purchase_id = ?", (purchase_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_PURCHASE,
                                     str(purchase_id))
            listing_id = int(row[0])
            if row[1] != buyer_id:
                raise ApiMarketError(E_AM_NOT_BUYER,
                                     "%s/%s" % (buyer_id, purchase_id))
            done = self._conn.execute(
                "SELECT refund_id FROM apimarket_refunds"
                " WHERE purchase_id = ?", (purchase_id,)).fetchone()
            if done is not None:
                raise ApiMarketError(E_AM_ALREADY_REFUNDED,
                                     str(purchase_id))
            listing = self._require_listing(listing_id)
            dev_account = listing[1]
            amount = int(row[2])
            dev_share = int(row[3])
            platform_share = int(row[4])
            # Funding gate (AC-AMRF5): the seller leg is a debit,
            # so the reversal may only be booked when the seller
            # still holds the proceeds. Checked BEFORE any movement
            # so a refusal leaves the ledger byte-identical.
            bal = self.led.balance(dev_account)
            dev_balance = int(bal.get("balance", 0)) if isinstance(
                bal, dict) else int(bal)
            if dev_balance < dev_share:
                raise ApiMarketError(
                    E_AM_REFUND_UNFUNDABLE,
                    "%s needs %d has %d" % (dev_account, dev_share,
                                            dev_balance))
            entries = [(buyer_id, "credit", amount),
                       ("pool:reserve", "debit", amount)]
            if dev_share > 0:
                entries.append((dev_account, "debit", dev_share))
                entries.append(("pool:share", "credit", dev_share))
            ref = "apimarket:refund:%d" % purchase_id
            memo = ("apimarket refund purchase=%d listing=%d buyer=%s"
                    % (purchase_id, listing_id, buyer_id))
            if text:
                memo += " reason=" + text
            refund_tx = self.led.adjust(entries, ref, memo,
                                        ref_type="order")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_refunds (purchase_id,"
                    " listing_id, buyer_id, dev_account, amount,"
                    " dev_share, platform_share, refund_tx,"
                    " refunded_utc, reason) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (purchase_id, listing_id, buyer_id, dev_account,
                     amount, dev_share, platform_share, refund_tx,
                     _now_utc(), text))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ApiMarketError(E_AM_ALREADY_REFUNDED,
                                     str(purchase_id))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"refund_id": cur.lastrowid,
                "purchase_id": purchase_id, "listing_id": listing_id,
                "buyer_id": buyer_id, "dev_account": dev_account,
                "amount": amount, "dev_share": dev_share,
                "platform_share": platform_share,
                "refund_tx": refund_tx,
                "refunded_utc": self._refund_stamp(purchase_id),
                "reason": text, "disclaimer": self.disclaimer}

    def _refund_stamp(self, purchase_id):
        """The stored refund stamp of one purchase (caller holds no
        lock requirement: single row read)."""
        row = self._conn.execute(
            "SELECT refunded_utc FROM apimarket_refunds"
            " WHERE purchase_id = ?", (purchase_id,)).fetchone()
        return None if row is None else row[0]

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

    def reply_to_rating(self, dev_account, rating_id, text):
        """Seller-side response door on one immutable rating
        (AC-AMRP1..AC-AMRP5, pre-registered in the R2093
        explore-queue row BEFORE this code existed): only the
        seller who owns the rated listing may answer, exactly once
        per rating. The pinned gate order is account shape, then
        rating id shape, then reply text shape, then rating
        existence, then ownership, then the duplicate state - every
        refusal is fail-closed with zero rows written. The reply is
        append-only and never rewrites the rating: api_ratings
        aggregates stay byte-identical and zero tokens move."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        if (not isinstance(rating_id, int) or isinstance(rating_id, bool)
                or rating_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(rating_id))
        if not isinstance(text, str):
            raise ApiMarketError(E_AM_BAD_REPLY, "text must be str")
        body = text.strip()
        if (not body or len(body) > 500
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in body)):
            raise ApiMarketError(E_AM_BAD_REPLY, str(text)[:40])
        with self._lock:
            row = self._conn.execute(
                "SELECT listing_id FROM apimarket_ratings"
                " WHERE rating_id = ?", (rating_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_RATING,
                                     str(rating_id))
            listing_id = int(row[0])
            owner = self._conn.execute(
                "SELECT dev_account FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()
            if owner is None or owner[0] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, rating_id))
            dup = self._conn.execute(
                "SELECT reply_id FROM apimarket_rating_replies"
                " WHERE rating_id = ?", (rating_id,)).fetchone()
            if dup is not None:
                raise ApiMarketError(E_AM_REPLY_DUP, str(rating_id))
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_rating_replies"
                    " (rating_id, listing_id, dev_account, reply_text,"
                    " replied_utc) VALUES (?,?,?,?,?)",
                    (rating_id, listing_id, dev_account, body, stamp))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ApiMarketError(E_AM_REPLY_DUP, str(rating_id))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"reply_id": cur.lastrowid, "rating_id": rating_id,
                "listing_id": listing_id, "dev_account": dev_account,
                "reply_text": body, "replied_utc": stamp,
                "disclaimer": self.disclaimer}

    def revise_rating(self, buyer_id, rating_id, stars):
        """Buyer-side rating revision door (pre-registered
        AC-AMRV1..AC-AMRV8 in the R2094 explore-queue row BEFORE
        this code existed).

        The rating face used to be write-once: one immutable stamp
        per (buyer, listing) and E_AM_RATE_DUP forever, so a
        mis-clicked star stayed welded to the seller's reputation -
        the only trust axis on this market with no remedy door
        (refunds, retirement and re-listing all have one). Each
        revision appends one apimarket_rating_revisions row and
        never rewrites the base rating row; the effective star
        value is the newest revision, else the base stamp.

        Gate order pinned by AC-AMRV2: account shape, rating-id
        shape, existence, ownership, star shape, unchanged state.
        Revising back to an earlier value stays legal (the gate
        compares against the EFFECTIVE value, not the base), and a
        same-value revision answers E_AM_RATING_UNCHANGED with
        zero new rows so the first stamp is never rewritten.
        Revising moves zero tokens and does not change
        rating_count - a revision is not a new rating."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        if (not isinstance(rating_id, int) or isinstance(rating_id, bool)
                or rating_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(rating_id))
        with self._lock:
            row = self._conn.execute(
                "SELECT listing_id, buyer_id, stars FROM"
                " apimarket_ratings WHERE rating_id = ?",
                (rating_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_RATING,
                                     str(rating_id))
            if row[1] != buyer_id:
                raise ApiMarketError(E_AM_NOT_BUYER,
                                     "%s/%s" % (buyer_id, rating_id))
            if (not isinstance(stars, int) or isinstance(stars, bool)
                    or stars < 1 or stars > 5):
                raise ApiMarketError(E_AM_BAD_STARS, str(stars))
            listing_id = int(row[0])
            previous = self._effective_stars(rating_id, int(row[2]))
            if stars == previous:
                raise ApiMarketError(E_AM_RATING_UNCHANGED,
                                     "%s/%s" % (rating_id, stars))
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_rating_revisions"
                    " (rating_id, listing_id, buyer_id, previous_stars,"
                    " stars, revised_utc) VALUES (?,?,?,?,?,?)",
                    (rating_id, listing_id, buyer_id, previous, stars,
                     stamp))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"revision_id": cur.lastrowid, "rating_id": rating_id,
                "listing_id": listing_id, "buyer_id": buyer_id,
                "previous_stars": previous, "stars": stars,
                "revised_utc": stamp, "disclaimer": self.disclaimer}

    # -- read faces -----------------------------------------------------------

    def _effective_stars(self, rating_id, base_stars):
        """Effective star value of one rating: the newest
        append-only revision, else the immutable base stamp
        (AC-AMRV5 single seam - every aggregate reads through
        here). Caller holds the lock."""
        row = self._conn.execute(
            "SELECT stars FROM apimarket_rating_revisions"
            " WHERE rating_id = ? ORDER BY revision_id DESC LIMIT 1",
            (rating_id,)).fetchone()
        return int(base_stars) if row is None else int(row[0])

    def _agg_rating(self, listing_id):
        rows = self._conn.execute(
            "SELECT rating_id, stars FROM apimarket_ratings"
            " WHERE listing_id = ?", (listing_id,)).fetchall()
        if not rows:
            return 0, 0.0
        total = sum(self._effective_stars(int(r[0]), int(r[1]))
                    for r in rows)
        return len(rows), float(total) / len(rows)

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
            ref_row = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(amount), 0)"
                " FROM apimarket_refunds WHERE listing_id = ?",
                (listing_id,)).fetchone()
            n_refund = int(ref_row[0])
            refunded_total = int(ref_row[1])
            n_rate, avg = self._agg_rating(listing_id)
            stamp = self._delisted_utc(listing_id)
            current = self._current_price(listing_id, int(row[5]))
            n_rev, latest_rev = self._revision_stats(listing_id)
            eff_title, eff_desc, n_meta, latest_meta = \
                self._metadata_state(listing_id, row[3], row[4])
        return {"listing_id": int(row[0]), "dev_account": row[1],
                "listing_key": row[2], "title": eff_title,
                "description": eff_desc, "token_price": current,
                "base_token_price": int(row[5]),
                "base_title": row[3], "base_description": row[4],
                "metadata_revision_count": n_meta,
                "latest_metadata_revision_utc": latest_meta,
                "revision_count": n_rev,
                "latest_revision_utc": latest_rev,
                "ai_label": int(row[6]), "listed_utc": row[7],
                "purchase_count": int(n_buy), "rating_count": n_rate,
                "rating_avg": avg,
                "refund_count": n_refund,
                "refunded_total": refunded_total,
                "net_purchase_count": int(n_buy) - n_refund,
                "delisted": stamp is not None,
                "delisted_utc": stamp,
                "disclaimer": self.disclaimer}

    def api_listing_lifecycle(self, listing_id):
        """Per-listing lifecycle surface (AC-AMRL5/AC-AMRL6): the
        full retirement/re-listing history as ordered append-only
        events, plus the derived current cycle and live state.
        Before this face the only lifecycle answer was api_view's
        delisted pair - a caller could see that a listing is live
        but never that it had been retired and re-opened twice.
        Pure read: zero rows written, zero token movement."""
        with self._lock:
            listing = self._require_listing(listing_id)
            cycle, retired, stamp = self._cycle_state(listing_id)
            delists = self._conn.execute(
                "SELECT listing_id, delisted_utc, cycle FROM"
                " apimarket_delistings WHERE listing_id = ?"
                " ORDER BY delist_id", (listing_id,)).fetchall()
            relists = self._conn.execute(
                "SELECT listing_id, relisted_utc, cycle FROM"
                " apimarket_relistings WHERE listing_id = ?"
                " ORDER BY relist_id", (listing_id,)).fetchall()
            key = self._conn.execute(
                "SELECT listing_key FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()[0]
        events = [{"event": "delist", "cycle": int(r[2]),
                   "utc": r[1]} for r in delists]
        events += [{"event": "relist", "cycle": int(r[2]),
                    "utc": r[1]} for r in relists]
        # A re-listing row marks the START of its cycle, a delisting
        # row the END of its own, so re-list sorts first within a
        # cycle number and the event stream reads open/close/open.
        events.sort(key=lambda e: (e["cycle"],
                                   0 if e["event"] == "relist" else 1))
        return {"listing_id": int(listing[0]),
                "dev_account": listing[1],
                "listing_key": key,
                "cycle": cycle,
                "live": not retired,
                "delisted": retired,
                "delisted_utc": stamp,
                "delist_count": len(delists),
                "relist_count": len(relists),
                "history": events,
                "disclaimer": self.disclaimer}

    def api_board(self):
        """Whole-market listing surface: every row carries the
        declared AIGC label (presentation-face law, AC-AM6); the
        envelope carries the resident disclaimer. Retired listings
        are excluded from the market board (AC-AMD6) while their
        history stays readable through api_view/api_ratings/
        api_sales. A listing re-listed after retirement is offered
        again (AC-AMRL4): the exclusion is per CURRENT cycle, not
        per listing ever retired. Pure read."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT listing_id, dev_account, listing_key, title,"
                " description, token_price, ai_label"
                " FROM apimarket_listings"
                " WHERE listing_id NOT IN (SELECT d.listing_id FROM"
                " apimarket_delistings d WHERE d.cycle ="
                " COALESCE((SELECT MAX(r.cycle) FROM"
                " apimarket_relistings r WHERE r.listing_id ="
                " d.listing_id), 1))"
                " ORDER BY listing_id").fetchall()
            out = []
            for r in rows:
                n_rate, avg = self._agg_rating(int(r[0]))
                eff_title, _eff_desc, _n_meta, _latest_meta = \
                    self._metadata_state(int(r[0]), r[3], r[4])
                out.append({"listing_id": int(r[0]),
                            "dev_account": r[1], "listing_key": r[2],
                            "title": eff_title,
                            "token_price": self._current_price(
                                int(r[0]), int(r[5])),
                            "ai_label": int(r[6]),
                            "rating_count": n_rate, "rating_avg": avg})
        return {"disclaimer": self.disclaimer, "listings": out}

    def api_ratings(self, listing_id):
        """Per-listing rating surface: immutable per-rater rows
        plus the deterministic aggregate (AC-AM5). Pure read."""
        with self._lock:
            self._require_listing(listing_id)
            rows = self._conn.execute(
                "SELECT rating_id, buyer_id, stars, rated_utc FROM"
                " apimarket_ratings WHERE listing_id = ?"
                " ORDER BY rating_id", (listing_id,)).fetchall()
            n_rate, avg = self._agg_rating(listing_id)
            rows = [{"buyer_id": r[1],
                     "stars": self._effective_stars(int(r[0]), int(r[2])),
                     "rated_utc": r[3]} for r in rows]
        return {"listing_id": listing_id, "rating_count": n_rate,
                "rating_avg": avg, "disclaimer": self.disclaimer,
                "ratings": rows}

    def api_rating_replies(self, listing_id):
        """Per-listing rating conversation surface (AC-AMRP1): one
        row per rating ordered by rating_id, unanswered rows carry
        reply=None so the seller sees what still awaits a voice.
        Retired listings stay readable with their replies
        (AC-AMRP4) and the envelope carries the resident
        non-advisory disclaimer. Pure read: zero row mutations."""
        with self._lock:
            self._require_listing(listing_id)
            rows = self._conn.execute(
                "SELECT r.rating_id, r.buyer_id, r.stars, r.rated_utc,"
                " p.reply_id, p.dev_account, p.reply_text, p.replied_utc"
                " FROM apimarket_ratings r LEFT JOIN"
                " apimarket_rating_replies p ON p.rating_id ="
                " r.rating_id WHERE r.listing_id = ?"
                " ORDER BY r.rating_id", (listing_id,)).fetchall()
            n_rate, _avg = self._agg_rating(listing_id)
            out = []
            for r in rows:
                reply = None
                if r[4] is not None:
                    reply = {"reply_id": int(r[4]),
                             "dev_account": r[5],
                             "reply_text": r[6],
                             "replied_utc": r[7]}
                out.append({"rating_id": int(r[0]), "buyer_id": r[1],
                            "stars": self._effective_stars(
                                int(r[0]), int(r[2])),
                            "rated_utc": r[3],
                            "reply": reply})
            n_reply = sum(1 for r in out if r["reply"] is not None)
        return {"listing_id": listing_id, "rating_count": n_rate,
                "reply_count": n_reply,
                "disclaimer": self.disclaimer, "rows": out}

    def api_rating_history(self, rating_id):
        """Rating revision history surface (AC-AMRV7): the immutable
        base stamp, every append-only revision in order, the
        effective star value and the revision count. Per-rating
        isolation; an unknown rating answers E_AM_UNKNOWN_RATING and
        a bad id answers E_AM_BAD_ARGS before any read. Pure read:
        zero row mutations, zero token movement."""
        if (not isinstance(rating_id, int) or isinstance(rating_id, bool)
                or rating_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(rating_id))
        with self._lock:
            row = self._conn.execute(
                "SELECT listing_id, buyer_id, stars, rated_utc FROM"
                " apimarket_ratings WHERE rating_id = ?",
                (rating_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_RATING,
                                     str(rating_id))
            revs = self._conn.execute(
                "SELECT revision_id, previous_stars, stars, revised_utc"
                " FROM apimarket_rating_revisions WHERE rating_id = ?"
                " ORDER BY revision_id", (rating_id,)).fetchall()
            base = int(row[2])
            effective = (base if not revs else int(revs[-1][2]))
        return {"rating_id": rating_id, "listing_id": int(row[0]),
                "buyer_id": row[1], "base_stars": base,
                "effective_stars": effective,
                "revision_count": len(revs),
                "rated_utc": row[3], "disclaimer": self.disclaimer,
                "revisions": [{"revision_id": int(x[0]),
                               "previous_stars": int(x[1]),
                               "stars": int(x[2]),
                               "revised_utc": x[3]} for x in revs]}

    def api_seller_inbox(self, dev_account):
        """Seller-side unanswered-rating inbox (pre-registered
        AC-AMI1..AC-AMI8 in the R2096 explore-queue claim row BEFORE
        this code existed): the work queue the reply door never had.

        api_rating_replies answers one listing at a time, so a seller
        with N live listings has to open N faces and count the gaps
        by hand. This face merges every rating row across the
        seller's listings and returns ONLY the unanswered ones,
        oldest debt first (rated_utc ascending, then rating_id).
        The envelope keeps the conversation arithmetic - answered +
        unanswered == total - so a reply visibly drains the queue
        without rewriting any row. The star column reads through the
        one effective-value seam, a retired listing keeps its
        unanswered rating (retirement does not erase the seller's
        obligation) and the title is the effective metadata value.
        The account shape gate is prefix-only by the truthful
        R2077/R2078 finding and runs before any read - a prefix-valid
        account with no ratings gets an honest empty inbox. Pure
        read: zero row mutations and zero token movement. The
        envelope carries the resident non-advisory disclaimer."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            totals = self._conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT r.listing_id),"
                " COUNT(p.reply_id) FROM apimarket_ratings r"
                " JOIN apimarket_listings l"
                " ON l.listing_id = r.listing_id"
                " LEFT JOIN apimarket_rating_replies p"
                " ON p.rating_id = r.rating_id"
                " WHERE l.dev_account = ?", (dev_account,)).fetchone()
            rows = self._conn.execute(
                "SELECT r.rating_id, r.listing_id, r.buyer_id,"
                " r.stars, r.rated_utc, l.listing_key, l.title,"
                " l.description FROM apimarket_ratings r"
                " JOIN apimarket_listings l"
                " ON l.listing_id = r.listing_id"
                " LEFT JOIN apimarket_rating_replies p"
                " ON p.rating_id = r.rating_id"
                " WHERE l.dev_account = ? AND p.reply_id IS NULL"
                " ORDER BY r.rated_utc, r.rating_id",
                (dev_account,)).fetchall()
            out = []
            for r in rows:
                listing_id = int(r[1])
                eff_title = self._metadata_state(
                    listing_id, r[6], r[7])[0]
                out.append({"rating_id": int(r[0]),
                            "listing_id": listing_id,
                            "listing_key": r[5],
                            "title": eff_title,
                            "buyer_id": r[2],
                            "stars": self._effective_stars(
                                int(r[0]), int(r[3])),
                            "rated_utc": r[4]})
        total = int(totals[0])
        answered = int(totals[2])
        oldest = out[0]["rated_utc"] if out else None
        return {"dev_account": dev_account,
                "rated_listing_count": int(totals[1]),
                "total_rating_count": total,
                "answered_count": answered,
                "unanswered_count": len(out),
                "oldest_unanswered_utc": oldest,
                "disclaimer": self.disclaimer,
                "rows": out}

    def api_revenue_months(self, dev_account):
        """Seller-side monthly revenue timeline (pre-registered
        AC-REVM1..AC-REVM8 in the R2097 explore-queue row BEFORE this
        code existed).

        Cash basis, pinned deliberately: a sale is booked in the UTC
        month of its purchased_utc, and a refund is booked in the UTC
        month of its refunded_utc - never rewriting the month the
        sale was booked in. A refund that lands in a later month
        therefore produces an honestly negative net there, while the
        original month stays byte-frozen. api_sales answers row by
        row (the caller must bucket it), dev_profile answers lifetime
        totals (no time axis) and api_market_stats answers the whole
        market, so this is the missing per-seller time axis that any
        statement or settlement run needs. Pure read.
        """
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        dev = str(dev_account)
        with self._lock:
            sales = self._conn.execute(
                "SELECT p.price_paid, p.dev_share, p.platform_share,"
                " p.purchased_utc FROM apimarket_purchases p JOIN"
                " apimarket_listings l ON l.listing_id = p.listing_id"
                " WHERE l.dev_account = ?", (dev,)).fetchall()
            refunds = self._conn.execute(
                "SELECT f.amount, f.dev_share, f.platform_share,"
                " f.refunded_utc FROM apimarket_refunds f"
                " WHERE f.dev_account = ?", (dev,)).fetchall()

        buckets = {}

        def bucket(month):
            return buckets.setdefault(
                month, {"month": month, "sales_count": 0, "gross": 0,
                        "refund_count": 0, "refunded": 0,
                        "dev_share": 0, "platform_share": 0,
                        "refunded_dev_share": 0,
                        "refunded_platform_share": 0})

        for price, dev_share, platform_share, stamp in sales:
            b = bucket(str(stamp)[:7])
            b["sales_count"] += 1
            b["gross"] += int(price)
            b["dev_share"] += int(dev_share)
            b["platform_share"] += int(platform_share)
        for amount, dev_share, platform_share, stamp in refunds:
            b = bucket(str(stamp)[:7])
            b["refund_count"] += 1
            b["refunded"] += int(amount)
            b["refunded_dev_share"] += int(dev_share)
            b["refunded_platform_share"] += int(platform_share)

        months = []
        for month in sorted(buckets):
            b = buckets[month]
            months.append({
                "month": month,
                "sales_count": b["sales_count"],
                "gross": b["gross"],
                "refund_count": b["refund_count"],
                "refunded": b["refunded"],
                "net": b["gross"] - b["refunded"],
                "dev_share": b["dev_share"],
                "platform_share": b["platform_share"],
                "dev_share_net": (b["dev_share"]
                                  - b["refunded_dev_share"]),
                "platform_share_net": (b["platform_share"]
                                       - b["refunded_platform_share"]),
            })
        return {"dev_account": dev,
                "month_count": len(months),
                "lifetime_sales_count": sum(
                    m["sales_count"] for m in months),
                "lifetime_gross": sum(m["gross"] for m in months),
                "lifetime_refund_count": sum(
                    m["refund_count"] for m in months),
                "lifetime_refunded": sum(
                    m["refunded"] for m in months),
                "lifetime_net": sum(m["net"] for m in months),
                "disclaimer": self.disclaimer,
                "months": months}

    def api_market_months(self):
        """Market-wide monthly trade timeline (pre-registered
        AC-AMMM1..AC-AMMM8 in the R2099 explore-queue row BEFORE
        this code existed).

        api_revenue_months answers one seller's cash-basis months
        and api_market_stats answers the whole market with lifetime
        aggregates only, so between the two there was no
        market-level time axis: a trend, a month-on-month comparison
        or a monthly settlement view had to walk every seller and
        rebucket the row faces by hand. This face closes that gap on
        the same cash basis law: a sale books in the UTC month of
        purchased_utc, a refund books in the UTC month of
        refunded_utc and never rewrites the month the sale landed
        in, so a refund booked in a later month shows an honestly
        negative net there.

        Participant counts (buyer_count, seller_count,
        listing_count) are purchase-derived only, so a refund-only
        month honestly reports zero participants alongside its
        refund rows. No arguments, so no gate: pure read, zero row
        mutations and zero token movement.
        """
        with self._lock:
            sales = self._conn.execute(
                "SELECT p.buyer_id, p.price_paid, p.dev_share,"
                " p.platform_share, p.purchased_utc, l.dev_account,"
                " p.listing_id FROM apimarket_purchases p JOIN"
                " apimarket_listings l ON"
                " l.listing_id = p.listing_id").fetchall()
            refunds = self._conn.execute(
                "SELECT f.amount, f.dev_share, f.platform_share,"
                " f.refunded_utc FROM apimarket_refunds f").fetchall()

        buckets = {}

        def bucket(month):
            return buckets.setdefault(
                month, {"month": month, "sales_count": 0, "gross": 0,
                        "refund_count": 0, "refunded": 0,
                        "dev_share": 0, "platform_share": 0,
                        "refunded_dev_share": 0,
                        "refunded_platform_share": 0,
                        "buyers": set(), "sellers": set(),
                        "listings": set()})

        for buyer, price, dev_share, platform_share, stamp, dev, \
                listing_id in sales:
            b = bucket(str(stamp)[:7])
            b["sales_count"] += 1
            b["gross"] += int(price)
            b["dev_share"] += int(dev_share)
            b["platform_share"] += int(platform_share)
            b["buyers"].add(buyer)
            b["sellers"].add(dev)
            b["listings"].add(int(listing_id))
        for amount, dev_share, platform_share, stamp in refunds:
            b = bucket(str(stamp)[:7])
            b["refund_count"] += 1
            b["refunded"] += int(amount)
            b["refunded_dev_share"] += int(dev_share)
            b["refunded_platform_share"] += int(platform_share)

        months = []
        for month in sorted(buckets):
            b = buckets[month]
            months.append({
                "month": month,
                "sales_count": b["sales_count"],
                "gross": b["gross"],
                "refund_count": b["refund_count"],
                "refunded": b["refunded"],
                "net": b["gross"] - b["refunded"],
                "dev_share": b["dev_share"],
                "platform_share": b["platform_share"],
                "dev_share_net": (b["dev_share"]
                                  - b["refunded_dev_share"]),
                "platform_share_net": (b["platform_share"]
                                       - b["refunded_platform_share"]),
                "buyer_count": len(b["buyers"]),
                "seller_count": len(b["sellers"]),
                "listing_count": len(b["listings"]),
            })
        return {"month_count": len(months),
                "lifetime_sales_count": sum(
                    m["sales_count"] for m in months),
                "lifetime_gross": sum(m["gross"] for m in months),
                "lifetime_refund_count": sum(
                    m["refund_count"] for m in months),
                "lifetime_refunded": sum(
                    m["refunded"] for m in months),
                "lifetime_net": sum(m["net"] for m in months),
                "lifetime_dev_revenue": sum(
                    m["dev_share_net"] for m in months),
                "lifetime_platform_revenue": sum(
                    m["platform_share_net"] for m in months),
                "disclaimer": self.disclaimer,
                "months": months}

    def api_price_history(self, listing_id):
        """Asking-price history surface (AC-AMPR7): the immutable
        base price plus every append-only revision in order, the
        current price and the revision count. Per-listing
        isolation; a retired listing's history stays readable.
        Pure read."""
        with self._lock:
            listing = self._require_listing(listing_id)
            base = int(listing[2])
            rows = self._conn.execute(
                "SELECT revision_id, dev_account, token_price,"
                " revised_utc FROM apimarket_price_revisions"
                " WHERE listing_id = ? ORDER BY revision_id",
                (listing_id,)).fetchall()
            current = self._current_price(listing_id, base)
            stamp = self._delisted_utc(listing_id)
        return {"listing_id": listing_id, "base_price": base,
                "current_price": current,
                "revision_count": len(rows),
                "delisted": stamp is not None,
                "delisted_utc": stamp,
                "disclaimer": self.disclaimer,
                "revisions": [{"revision_id": int(r[0]),
                               "dev_account": r[1],
                               "token_price": int(r[2]),
                               "revised_utc": r[3]} for r in rows]}

    def api_metadata_history(self, listing_id):
        """Listing metadata history surface (pre-registered
        AC-AMME7 in the R2083 explore-queue row BEFORE this code
        existed): the immutable base title/description plus every
        append-only revision in order, the current effective pair
        and the revision count. Per-listing isolation; a retired
        listing's history stays readable (AC-AMME5). Pure read."""
        with self._lock:
            self._require_listing(listing_id)
            base = self._conn.execute(
                "SELECT title, description FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()
            rows = self._conn.execute(
                "SELECT revision_id, dev_account, title, description,"
                " revised_utc FROM apimarket_listing_revisions"
                " WHERE listing_id = ? ORDER BY revision_id",
                (listing_id,)).fetchall()
            eff_title, eff_desc, count, latest = self._metadata_state(
                listing_id, base[0], base[1])
            stamp = self._delisted_utc(listing_id)
        return {"listing_id": listing_id,
                "base_title": base[0],
                "base_description": base[1],
                "title": eff_title,
                "description": eff_desc,
                "revision_count": count,
                "latest_revision_utc": latest,
                "delisted": stamp is not None,
                "delisted_utc": stamp,
                "disclaimer": self.disclaimer,
                "revisions": [{"revision_id": int(r[0]),
                               "dev_account": r[1],
                               "title": r[2],
                               "description": r[3],
                               "revised_utc": r[4]} for r in rows]}

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
            refs = {}
            for r in self._conn.execute(
                    "SELECT f.purchase_id, f.amount, f.refunded_utc,"
                    " f.refund_tx FROM apimarket_refunds f JOIN"
                    " apimarket_purchases p ON p.purchase_id ="
                    " f.purchase_id JOIN apimarket_listings l ON"
                    " l.listing_id = p.listing_id WHERE"
                    " l.dev_account = ?", (dev_account,)).fetchall():
                refs[int(r[0])] = (int(r[1]), r[2], r[3])
        return {"dev_account": dev_account,
                "disclaimer": self.disclaimer,
                "refunded_count": len(refs),
                "refunded_total": sum(v[0] for v in refs.values()),
                "sales": [{"purchase_id": int(r[0]),
                           "listing_id": int(r[1]),
                           "listing_key": r[2], "buyer_id": r[3],
                           "price_paid": int(r[4]),
                           "dev_share": int(r[5]),
                           "platform_share": int(r[6]),
                           "spend_tx": r[7], "dev_share_tx": r[8],
                           "purchased_utc": r[9],
                           "refunded": int(r[0]) in refs,
                           "refunded_utc": refs.get(
                               int(r[0]), (0, None, None))[1],
                           "refund_tx": refs.get(
                               int(r[0]), (0, None, None))[2]}
                          for r in rows]}

    def api_library(self, buyer_id):
        """Buyer-side purchase library surface (pre-registered
        AC-AML1..AC-AML8 in the R2081 explore-queue row BEFORE this
        code existed): every purchase row of that buyer, ordered by
        purchase_id, joined to its listing metadata, with the live
        asking price, the retirement stamp and this buyer's own
        rating.

        The buyer face is deliberately separate from api_sales: the
        seller view answers "who bought from me and what did I
        earn", this view answers "what did I buy and what do I own
        now". A retired listing stays in the library with its
        delisted flag (purchase history is not destroyed by
        retirement), price_paid is the historical amount actually
        charged while current_price is the live asking price, and
        my_rating is this buyer's own stars only (None before the
        rating) - another buyer's rating never leaks. The account
        shape gate is prefix-only by the truthful R2077/R2078
        finding and runs before any read; a prefix-valid account
        with no purchases gets an honest empty library, not an
        error. Pure read: zero row mutations and zero token
        movement. The envelope carries the resident non-advisory
        disclaimer."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        with self._lock:
            rows = self._conn.execute(
                "SELECT p.purchase_id, p.listing_id, l.listing_key,"
                " l.title, l.dev_account, p.price_paid, p.dev_share,"
                " p.platform_share, p.spend_tx, p.purchased_utc,"
                " l.token_price FROM apimarket_purchases p JOIN"
                " apimarket_listings l ON l.listing_id ="
                " p.listing_id WHERE p.buyer_id = ?"
                " ORDER BY p.purchase_id", (buyer_id,)).fetchall()
            out = []
            total = 0
            refunded_total = 0
            refund_count = 0
            for r in rows:
                listing_id = int(r[1])
                stamp = self._delisted_utc(listing_id)
                rating = self._conn.execute(
                    "SELECT stars FROM apimarket_ratings"
                    " WHERE buyer_id = ? AND listing_id = ?",
                    (buyer_id, listing_id)).fetchone()
                refund = self._conn.execute(
                    "SELECT amount, refunded_utc, refund_tx"
                    " FROM apimarket_refunds WHERE purchase_id = ?",
                    (int(r[0]),)).fetchone()
                total += int(r[5])
                if refund is not None:
                    refund_count += 1
                    refunded_total += int(refund[0])
                out.append({"purchase_id": int(r[0]),
                            "listing_id": listing_id,
                            "listing_key": r[2], "title": r[3],
                            "dev_account": r[4],
                            "price_paid": int(r[5]),
                            "dev_share": int(r[6]),
                            "platform_share": int(r[7]),
                            "spend_tx": r[8],
                            "purchased_utc": r[9],
                            "current_price": self._current_price(
                                listing_id, int(r[10])),
                            "delisted": stamp is not None,
                            "delisted_utc": stamp,
                            "my_rating": (None if rating is None
                                          else int(rating[0])),
                            "refunded": refund is not None,
                            "refunded_utc": (None if refund is None
                                             else refund[1]),
                            "refund_tx": (None if refund is None
                                          else refund[2])})
        return {"buyer_id": buyer_id, "purchase_count": len(out),
                "total_spent": total,
                "refund_count": refund_count,
                "total_refunded": refunded_total,
                "net_spent": total - refunded_total,
                "disclaimer": self.disclaimer,
                "purchases": out}

    def api_refund(self, purchase_id):
        """Refund provenance read face (AC-AMRF7): the eleven-key
        envelope of one append-only refund row. An unknown purchase
        answers E_AM_UNKNOWN_PURCHASE and a live (never refunded)
        purchase answers E_AM_NOT_REFUNDED - an honest absence, not
        an empty envelope. Pure read: zero row mutations, zero
        token movement."""
        if (not isinstance(purchase_id, int) or isinstance(purchase_id, bool)
                or purchase_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(purchase_id))
        with self._lock:
            exists = self._conn.execute(
                "SELECT 1 FROM apimarket_purchases"
                " WHERE purchase_id = ?", (purchase_id,)).fetchone()
            if exists is None:
                raise ApiMarketError(E_AM_UNKNOWN_PURCHASE,
                                     str(purchase_id))
            row = self._conn.execute(
                "SELECT refund_id, purchase_id, listing_id, buyer_id,"
                " dev_account, amount, dev_share, platform_share,"
                " refund_tx, refunded_utc, reason FROM apimarket_refunds"
                " WHERE purchase_id = ?", (purchase_id,)).fetchone()
        if row is None:
            raise ApiMarketError(E_AM_NOT_REFUNDED, str(purchase_id))
        return {"refund_id": int(row[0]), "purchase_id": int(row[1]),
                "listing_id": int(row[2]), "buyer_id": row[3],
                "dev_account": row[4], "amount": int(row[5]),
                "dev_share": int(row[6]),
                "platform_share": int(row[7]),
                "refund_tx": row[8], "refunded_utc": row[9],
                "reason": row[10], "disclaimer": self.disclaimer}

    def _active_watch(self, buyer_id, listing_id):
        """The buyer's live watch row for one listing, or None.
        Active = a watch row with no unwatch row pointing at its
        watch_id (append-only history: an unwatched row is kept,
        never deleted, and a later re-watch writes a NEW row).
        Caller holds the lock."""
        return self._conn.execute(
            "SELECT w.watch_id, w.watched_utc FROM apimarket_watchlist w"
            " WHERE w.buyer_id = ? AND w.listing_id = ? AND NOT EXISTS"
            " (SELECT 1 FROM apimarket_unwatchings u WHERE u.watch_id ="
            " w.watch_id) ORDER BY w.watch_id DESC LIMIT 1",
            (buyer_id, listing_id)).fetchone()

    def watch_api(self, buyer_id, listing_id):
        """Buyer-side watch door (pre-registered AC-AMWL1..AMWL8 in
        the R2086 explore-queue row BEFORE this code existed).

        Every read face on this market answers one narrow question,
        but a resident weighing a purchase had nowhere to keep a
        listing for later - no bookmark, no price-watch, no short
        list. This door closes that pre-purchase intent gap: one
        append-only apimarket_watchlist row per watch call.

        Gate order pinned by AC-AMWL5: account shape first, then
        the listing shape/existence gate, then the retired state,
        then the duplicate state. A retired listing cannot be newly
        watched (E_AM_DELISTED) - but a listing watched BEFORE it
        was retired stays in the watchlist with its stamp, because
        retirement never rewrites history (AC-AMWL4). A repeat
        watch of a live listing answers E_AM_WATCH_DUP with zero
        new rows, so the first watched_utc is never rewritten.
        Watching moves zero tokens.

        There is deliberately no table-level UNIQUE(buyer, listing):
        a re-watch after an unwatch must be able to keep both
        historical rows, so the live-row uniqueness is enforced by
        the gate under the write lock instead (single writer)."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        with self._lock:
            listing = self._require_listing(listing_id)
            if self._delisted_utc(listing_id) is not None:
                raise ApiMarketError(E_AM_DELISTED, str(listing_id))
            if self._active_watch(buyer_id, listing_id) is not None:
                raise ApiMarketError(E_AM_WATCH_DUP,
                                     "%s/%s" % (buyer_id, listing_id))
            key, title = self._conn.execute(
                "SELECT listing_key, title FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_watchlist (buyer_id,"
                    " listing_id, watched_utc) VALUES (?,?,?)",
                    (buyer_id, listing_id, stamp))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"watch_id": cur.lastrowid, "buyer_id": buyer_id,
                "listing_id": int(listing_id), "listing_key": key,
                "title": title,
                "dev_account": listing[1], "watched_utc": stamp,
                "already": False, "disclaimer": self.disclaimer}

    def unwatch_api(self, buyer_id, listing_id):
        """Buyer-side unwatch door (AC-AMWL3): one append-only
        apimarket_unwatchings row pointing at the live watch row.
        The watch row itself is never deleted or updated, so the
        watch history survives; the live set is derived by
        excluding watched rows that have an unwatch row. Gate order
        is pinned: account shape, then listing shape/existence,
        then the not-watched state (E_AM_NOT_WATCHED with zero new
        rows). A retired listing may still be unwatched - removal
        from a personal list is always allowed. Moves zero
        tokens."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        with self._lock:
            listing = self._require_listing(listing_id)
            active = self._active_watch(buyer_id, listing_id)
            if active is None:
                raise ApiMarketError(E_AM_NOT_WATCHED,
                                     "%s/%s" % (buyer_id, listing_id))
            key = self._conn.execute(
                "SELECT listing_key FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()[0]
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_unwatchings (watch_id,"
                    " buyer_id, listing_id, unwatched_utc)"
                    " VALUES (?,?,?,?)",
                    (int(active[0]), buyer_id, int(listing_id), stamp))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ApiMarketError(E_AM_NOT_WATCHED,
                                     "%s/%s" % (buyer_id, listing_id))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"unwatch_id": cur.lastrowid,
                "watch_id": int(active[0]), "buyer_id": buyer_id,
                "listing_id": int(listing_id), "listing_key": key,
                "watched_utc": active[1], "unwatched_utc": stamp,
                "already": False, "disclaimer": self.disclaimer}

    def api_watchlist(self, buyer_id):
        """Buyer-side watchlist read face (AC-AMWL1): the live
        watch rows of one buyer, ordered by watch_id, each joined to
        its listing metadata with the current asking price, the
        retirement stamp and this buyer's own purchase flag.
        Unwatched history rows are excluded from the live view but
        stay on disk. Envelope keys: buyer_id, watch_count,
        disclaimer, watches; watch_count is derived from the rows
        (F3: no hardcoded numbers). The account shape gate runs
        before any read; a prefix-valid account with no watches
        gets an honest empty envelope. Pure read: zero row
        mutations and zero token movement."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        with self._lock:
            rows = self._conn.execute(
                "SELECT w.watch_id, w.listing_id, l.listing_key,"
                " l.title, l.dev_account, l.token_price, w.watched_utc"
                " FROM apimarket_watchlist w JOIN apimarket_listings l"
                " ON l.listing_id = w.listing_id WHERE w.buyer_id = ?"
                " AND NOT EXISTS (SELECT 1 FROM apimarket_unwatchings u"
                " WHERE u.watch_id = w.watch_id)"
                " ORDER BY w.watch_id", (buyer_id,)).fetchall()
            out = []
            for r in rows:
                listing_id = int(r[1])
                owned = self._conn.execute(
                    "SELECT 1 FROM apimarket_purchases WHERE buyer_id = ?"
                    " AND listing_id = ?",
                    (buyer_id, listing_id)).fetchone()
                stamp = self._delisted_utc(listing_id)
                out.append({"watch_id": int(r[0]),
                            "listing_id": listing_id,
                            "listing_key": r[2], "title": r[3],
                            "dev_account": r[4],
                            "current_price": self._current_price(
                                listing_id, int(r[5])),
                            "delisted": stamp is not None,
                            "delisted_utc": stamp,
                            "purchased": owned is not None,
                            "watched_utc": r[6]})
        return {"buyer_id": buyer_id, "watch_count": len(out),
                "disclaimer": self.disclaimer, "watches": out}

    _WATCH_ALERT_RANK = {"delisted": 0, "sold_out": 1,
                         "price_drop": 2, "price_rise": 3}
    _WATCH_ALERT_SEVERITY = {"delisted": "high", "sold_out": "warn",
                             "price_drop": "info", "price_rise": "info"}

    def api_watch_alerts(self, buyer_id):
        """Buyer-side watch alert feed (AC-WAL1..AC-WAL5, criteria
        pre-registered in the R2104 queue row BEFORE this code
        existed). api_watchlist answers what a buyer is watching;
        nothing answered what happened to those watches, so a
        resident had to diff the table by hand. This face derives
        the events from the faces that already exist:

          - price_drop / price_rise against the asking price at the
            watch instant (the newest revision stamped at or before
            watched_utc, base row otherwise - AC-WAL2);
          - sold_out through the one scarcity seam api_supply uses;
          - delisted from the current cycle state.

        A retired listing answers delisted only (its price is moot);
        an equal price is silent (no invented signal); a watch the
        buyer already purchased is settled and silent; an unwatched
        watch row is silent. Severity is pinned per kind and the
        list is a total order on (rank, listing_id). The account
        shape gate runs before any read; a prefix-valid account with
        no watches gets an honest empty envelope. Pure read: zero
        row mutations, zero token movement."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        with self._lock:
            rows = self._conn.execute(
                "SELECT w.watch_id, w.listing_id, l.listing_key,"
                " l.title, l.dev_account, l.token_price, w.watched_utc"
                " FROM apimarket_watchlist w JOIN apimarket_listings l"
                " ON l.listing_id = w.listing_id WHERE w.buyer_id = ?"
                " AND NOT EXISTS (SELECT 1 FROM apimarket_unwatchings u"
                " WHERE u.watch_id = w.watch_id)"
                " ORDER BY w.watch_id", (buyer_id,)).fetchall()
            alerts = []
            for r in rows:
                listing_id = int(r[1])
                owned = self._conn.execute(
                    "SELECT 1 FROM apimarket_purchases WHERE buyer_id = ?"
                    " AND listing_id = ?",
                    (buyer_id, listing_id)).fetchone()
                if owned is not None:
                    continue
                base_price = int(r[5])
                at_watch = self._price_at_instant(
                    listing_id, base_price, r[6])
                current = self._current_price(listing_id, base_price)
                stamp = self._delisted_utc(listing_id)
                _supply, _sold, _remaining, sold_out = \
                    self._supply_state(listing_id)
                kinds = []
                if stamp is not None:
                    kinds.append("delisted")
                else:
                    if sold_out:
                        kinds.append("sold_out")
                    if current < at_watch:
                        kinds.append("price_drop")
                    elif current > at_watch:
                        kinds.append("price_rise")
                for kind in kinds:
                    alerts.append({
                        "watch_id": int(r[0]),
                        "listing_id": listing_id,
                        "listing_key": r[2], "title": r[3],
                        "dev_account": r[4],
                        "kind": kind,
                        "severity": self._WATCH_ALERT_SEVERITY[kind],
                        "price_at_watch": at_watch,
                        "current_price": current,
                        "delta": current - at_watch,
                        "delisted": stamp is not None,
                        "sold_out": sold_out,
                        "watched_utc": r[6]})
            alerts.sort(key=lambda a: (self._WATCH_ALERT_RANK[a["kind"]],
                                       a["listing_id"]))
        return {"buyer_id": buyer_id, "watch_count": len(rows),
                "alert_count": len(alerts),
                "disclaimer": self.disclaimer, "alerts": alerts}

    def api_supply(self, listing_id):
        """Scarcity read face (AC-AMSP1): the declared supply,
        the units sold (derived from the immutable purchase rows),
        the remaining units and the sold-out flag, plus the
        resident disclaimer. A listing published WITHOUT a supply
        keeps the pre-change contract: supply None, remaining
        None, sold_out False - unlimited. Pure read, zero token
        movement."""
        with self._lock:
            self._require_listing(listing_id)
            row = self._conn.execute(
                "SELECT listing_key, dev_account, listed_utc"
                " FROM apimarket_listings WHERE listing_id = ?",
                (listing_id,)).fetchone()
            (base_supply, supply, restocked, sold, remaining,
             sold_out, restock_count) = self._supply_full(listing_id)
        return {"listing_id": int(listing_id),
                "listing_key": row[0],
                "dev_account": row[1],
                "supply": supply, "sold": sold,
                "remaining": remaining, "sold_out": sold_out,
                "base_supply": base_supply,
                "restocked_units": restocked,
                "restock_count": restock_count,
                "listed_utc": row[2],
                "disclaimer": self.disclaimer}

    def api_supply_history(self, listing_id):
        """Per-listing replenishment history (AC-AMRS4): the base
        declaration plus every append-only restock event in
        revision_id order, each carrying the running effective
        supply after that event, and the derived end state. The
        revision_id - not the timestamp - is the ordering
        authority: the clock is second-resolution, so two restocks
        inside one second are legal and still ordered. Pure read:
        zero rows written, zero token movement."""
        if (not isinstance(listing_id, int) or isinstance(listing_id, bool)
                or listing_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(listing_id))
        with self._lock:
            self._require_listing(listing_id)
            row = self._conn.execute(
                "SELECT listing_key, dev_account FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()
            (base_supply, effective, restocked, sold, remaining,
             sold_out, restock_count) = self._supply_full(listing_id)
            rows = self._conn.execute(
                "SELECT revision_id, add_units, restocked_utc"
                " FROM apimarket_supply_revisions"
                " WHERE listing_id = ? ORDER BY revision_id",
                (listing_id,)).fetchall()
        history = []
        running = base_supply
        for revision_id, add_units, stamp in rows:
            if running is not None:
                running = int(running) + int(add_units)
            history.append({"revision_id": int(revision_id),
                            "add_units": int(add_units),
                            "effective_supply": running,
                            "restocked_utc": stamp})
        return {"listing_id": int(listing_id),
                "listing_key": row[0],
                "dev_account": row[1],
                "base_supply": base_supply,
                "restocked_units": restocked,
                "effective_supply": effective,
                "restock_count": restock_count,
                "sold": sold, "remaining": remaining,
                "sold_out": sold_out,
                "history": history,
                "disclaimer": self.disclaimer}

    def api_search(self, keyword=None, dev_account=None, min_price=None,
                   max_price=None, include_delisted=False,
                   limit=None, offset=None, sort=None):
        """Market discovery surface (pre-registered AC-AMSQ1..AMSQ8
        in the R2082 explore-queue row BEFORE this code existed).

        The five existing read faces each answer one narrow
        question (one listing, one seller, one buyer's library,
        the whole board); a resident looking for a usable service
        could only enumerate everything. This face answers "which
        listings match my need": a case-insensitive keyword
        substring over title OR listing_key (description is
        deliberately NOT searched), an optional seller filter, an
        optional price band applied to the CURRENT asking price
        (the newest revision wins, so a repriced listing moves
        bands), and an explicit include_delisted switch (retired
        listings are hidden by default; when included they carry
        their retirement stamp and their revision-derived price).

        Gate order is pinned by AC-AMSQ6 - every gate runs before
        any read: keyword shape, then seller shape, then the price
        band (including the inverted band form), then the
        include_delisted type. Refusals are fail-closed with zero
        side effects. Rows are ordered by current price ascending,
        then listing_id ascending (cheapest first, stable). Pure
        read: zero row mutations and zero token movement. The
        envelope carries the resident non-advisory disclaimer and
        an echo of the normalized criteria.

        Paging axis (pre-registered AC-AMPG1..AMPG8 in the R2084
        explore-queue row BEFORE this code existed): the face used
        to return the whole matching set, so a resident could not
        ask for page N of a growing market, nor learn the total.
        Optional limit (int >= 1) and offset (int >= 0) slice the
        already-ordered rows; total is the pre-page match count,
        count stays len(listings) (the page length), and truncated
        says whether rows remain after this page. Gate order is
        pinned and fail-closed BEFORE any read: keyword, seller,
        price band, include_delisted type, limit shape, offset
        shape. Backward-compatibility law: when NEITHER paging
        parameter is given the envelope and rows stay byte-
        identical to the R2082 contract (the four legacy keys, the
        five legacy criteria keys); the paging keys appear only
        when paging is requested.

        Sort axis (pre-registered AC-AMSR1..AMSR8 in the R2098
        explore-queue row BEFORE this code existed): the row order
        used to be frozen at current-price ascending, so a resident
        who wanted the flagship listing, the best rated, the best
        selling or the newest had to take the whole set and re-sort
        locally - and paging could not express "page N of THAT
        order". Optional sort accepts exactly the five tokens
        price_asc / price_desc / rating / sales / newest (module
        constant _SEARCH_SORT_MODES). Every mode is a total order
        with a listing_id ascending tie-break, so the matched id set
        is identical across modes (order-only axis) and page
        stitching reproduces that mode's full order. rating orders
        by rating_avg desc, then rating_count desc, then id (an
        unrated listing reads 0.0 and sinks); sales orders by the
        NET sold count - purchases minus refunds, floored at zero,
        the same quantity api_supply reports; newest orders by
        listed_utc desc then id. The sort gate runs after the
        keyword / seller / price-band / include_delisted / limit /
        offset gates and before any read, fail-closed. Backward-
        compatibility law: when sort is None the criteria echo
        carries NO sort key, so the envelope and rows stay byte-
        identical to the pre-sort contract; the key appears only
        when a token is given. Pure read: zero row mutations and
        zero token movement."""
        kw = None
        if keyword is not None:
            if not isinstance(keyword, str):
                raise ApiMarketError(E_AM_BAD_ARGS, str(keyword))
            stripped = keyword.strip()
            if not stripped:
                raise ApiMarketError(E_AM_BAD_ARGS, "keyword blank")
            kw = stripped
        if dev_account is not None:
            if (not isinstance(dev_account, str)
                    or not dev_account.startswith("usr:")):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        low = _price_bound(min_price, "min_price")
        high = _price_bound(max_price, "max_price")
        if low is not None and high is not None and low > high:
            raise ApiMarketError(E_AM_BAD_PRICE, "min_price>max_price")
        if not isinstance(include_delisted, bool):
            raise ApiMarketError(E_AM_BAD_ARGS,
                                 "include_delisted must be bool")
        if limit is not None:
            if (isinstance(limit, bool) or not isinstance(limit, int)
                    or limit < 1):
                raise ApiMarketError(E_AM_BAD_ARGS, "bad limit: %r"
                                     % (limit,))
        if offset is not None:
            if (isinstance(offset, bool) or not isinstance(offset, int)
                    or offset < 0):
                raise ApiMarketError(E_AM_BAD_ARGS, "bad offset: %r"
                                     % (offset,))
        # AC-AMSR4: the sort shape gate is the last gate and still
        # runs BEFORE any read - a refused token touches no table.
        if sort is None:
            sort_mode = None
        else:
            if not isinstance(sort, str):
                raise ApiMarketError(E_AM_BAD_ARGS, "bad sort: %r"
                                     % (sort,))
            token = sort.strip()
            if token not in _SEARCH_SORT_MODES:
                raise ApiMarketError(E_AM_BAD_ARGS, "bad sort: %r"
                                     % (sort,))
            sort_mode = token
        needle = None if kw is None else kw.casefold()
        with self._lock:
            rows = self._conn.execute(
                "SELECT listing_id, dev_account, listing_key, title,"
                " description, token_price, ai_label, listed_utc FROM"
                " apimarket_listings ORDER BY listing_id").fetchall()
            out = []
            listed_by = {}
            for r in rows:
                listing_id = int(r[0])
                stamp = self._delisted_utc(listing_id)
                if stamp is not None and not include_delisted:
                    continue
                if dev_account is not None and r[1] != dev_account:
                    continue
                eff_title, _eff_desc, _n_meta, _latest_meta = \
                    self._metadata_state(listing_id, r[3], r[4])
                if needle is not None:
                    hay = (str(eff_title) + "\n" + str(r[2])).casefold()
                    if needle not in hay:
                        continue
                price = self._current_price(listing_id, int(r[5]))
                if low is not None and price < low:
                    continue
                if high is not None and price > high:
                    continue
                n_rate, avg = self._agg_rating(listing_id)
                listed_by[listing_id] = r[7]
                out.append({"listing_id": listing_id,
                            "dev_account": r[1],
                            "listing_key": r[2],
                            "title": eff_title,
                            "token_price": price,
                            "ai_label": int(r[6]),
                            "rating_count": n_rate,
                            "rating_avg": avg,
                            "delisted": stamp is not None,
                            "delisted_utc": stamp})
            # AC-AMSR2: five total orders, each tie-broken by
            # listing_id ascending. The net-sold rank is read through
            # the one scarcity seam so a refund lowers the rank in
            # exactly the same step it lowers api_supply.sold.
            if sort_mode is None or sort_mode == "price_asc":
                out.sort(key=lambda row: (row["token_price"],
                                          row["listing_id"]))
            elif sort_mode == "price_desc":
                out.sort(key=lambda row: row["listing_id"])
                out.sort(key=lambda row: row["token_price"],
                         reverse=True)
            elif sort_mode == "rating":
                out.sort(key=lambda row: row["listing_id"])
                out.sort(key=lambda row: (row["rating_avg"],
                                          row["rating_count"]),
                         reverse=True)
            elif sort_mode == "sales":
                sold_by = {}
                for row in out:
                    _eff, sold, _rem, _so = self._supply_state(
                        row["listing_id"])
                    sold_by[row["listing_id"]] = int(sold)
                out.sort(key=lambda row: row["listing_id"])
                out.sort(key=lambda row: sold_by[row["listing_id"]],
                         reverse=True)
            else:  # newest
                out.sort(key=lambda row: row["listing_id"])
                out.sort(key=lambda row: listed_by[row["listing_id"]],
                         reverse=True)
        total = len(out)
        paged = limit is not None or offset is not None
        start = 0 if offset is None else offset
        page = out[start:] if limit is None else out[start:start + limit]
        # AC-AMSR1: the sort key is echoed only when a token is
        # given, so the pre-sort criteria/env contract stays
        # byte-identical for every caller that never sorts.
        criteria = {"keyword": kw,
                    "dev_account": dev_account,
                    "min_price": low,
                    "max_price": high,
                    "include_delisted": include_delisted}
        if sort_mode is not None:
            criteria["sort"] = sort_mode
        if not paged:
            return {"disclaimer": self.disclaimer,
                    "criteria": criteria,
                    "count": total,
                    "listings": out}
        criteria["limit"] = limit
        criteria["offset"] = offset
        return {"disclaimer": self.disclaimer,
                "criteria": criteria,
                "count": len(page),
                "returned": len(page),
                "total": total,
                "limit": limit,
                "offset": offset,
                "truncated": (start + len(page)) < total,
                "listings": page}

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

    def dev_profile(self, dev_account):
        """Public seller-profile read face (pre-registered
        AC-AMDP1..AC-AMDP8 in the R2085 explore-queue row BEFORE
        this code existed): one developer's own trust face - the
        listing split (live vs retired), the historical sales and
        revenue aggregates, the cross-listing rating aggregate and
        the per-listing breakdown.

        The nine existing read faces each answer one narrow
        question (one listing, the whole board, one listing's
        ratings, one seller's own sales, one buyer's library, the
        search result, the market-wide seller board); none answers
        "who is this seller". This face closes the discovery
        chain: a retired listing stays visible with its delist
        stamp and keeps contributing its historical sales and
        ratings, so retirement never rewrites the trust history.
        The account shape gate is prefix-only by the truthful
        R2077/R2078 finding and runs before any read - a
        prefix-valid account with no listing rows gets an honest
        empty profile (zeros, first_listed_utc None, empty
        listings), never an error. Pure read: zero row mutations
        and zero token movement. The envelope carries the resident
        non-advisory disclaimer."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            listings = self._conn.execute(
                "SELECT listing_id, listing_key, title, token_price,"
                " listed_utc FROM apimarket_listings WHERE"
                " dev_account = ? ORDER BY listing_id",
                (dev_account,)).fetchall()
            rows = []
            live = 0
            retired = 0
            sales_count = 0
            gross = 0
            dev_rev = 0
            plat_rev = 0
            rating_count = 0
            star_sum = 0
            first_listed = None
            for r in listings:
                listing_id = int(r[0])
                stamp = self._delisted_utc(listing_id)
                sale = self._conn.execute(
                    "SELECT COUNT(*), COALESCE(SUM(price_paid), 0),"
                    " COALESCE(SUM(dev_share), 0),"
                    " COALESCE(SUM(platform_share), 0)"
                    " FROM apimarket_purchases WHERE listing_id = ?",
                    (listing_id,)).fetchone()
                rc, ravg = self._agg_rating(listing_id)
                star_rows = self._conn.execute(
                    "SELECT rating_id, stars FROM apimarket_ratings"
                    " WHERE listing_id = ?", (listing_id,)).fetchall()
                stars = sum(self._effective_stars(int(x[0]), int(x[1]))
                            for x in star_rows)
                if stamp is None:
                    live += 1
                else:
                    retired += 1
                sales_count += int(sale[0])
                gross += int(sale[1])
                dev_rev += int(sale[2])
                plat_rev += int(sale[3])
                rating_count += rc
                star_sum += int(stars)
                listed_utc = r[4]
                if first_listed is None or listed_utc < first_listed:
                    first_listed = listed_utc
                rows.append({
                    "listing_id": listing_id,
                    "listing_key": r[1],
                    "title": r[2],
                    "token_price": self._current_price(
                        listing_id, int(r[3])),
                    "delisted": stamp is not None,
                    "delisted_utc": stamp,
                    "sales_count": int(sale[0]),
                    "rating_count": rc,
                    "avg_rating": ravg})
            avg_rating = (0.0 if rating_count == 0
                          else float(star_sum) / rating_count)
        return {"dev_account": dev_account,
                "listing_count": len(rows),
                "live_listing_count": live,
                "retired_listing_count": retired,
                "sales_count": sales_count,
                "gross_sales": gross,
                "dev_revenue": dev_rev,
                "platform_revenue": plat_rev,
                "rating_count": rating_count,
                "avg_rating": avg_rating,
                "first_listed_utc": first_listed,
                "disclaimer": self.disclaimer,
                "listings": rows}

    def api_market_stats(self):
        """Market-wide overview read face (pre-registered
        AC-AMMS1..AC-AMMS8 in the R2090 explore-queue row BEFORE
        this code existed): the whole market in one envelope.

        The ten existing read faces each answer one narrow
        question - one listing (api_view), one listing's ratings,
        price history and metadata history, one seller's trust
        face (dev_profile), the seller board (dev_sales_board),
        one buyer's library (api_library), the whole board
        (api_board), one search page (api_search), one listing's
        supply (api_supply) and its lifecycle. None answers "how
        big is this market": the live vs retired split, how many
        developers and buyers participate, how much volume
        actually settled after refunds, and which share of it
        reached the developers. This face closes the top of the
        reading chain.

        Laws pinned by the suite: partition conservation
        (listing_count == live + retired); trade conservation
        (gross_tokens == net_gross_tokens + refunded_tokens and
        net_gross_tokens == dev_revenue + platform_revenue
        exactly, integer split); retirement only moves the
        partition counters while every historical aggregate stays
        byte-frozen; a refund lowers the net gross and both net
        pools by exactly the refunded amounts while
        purchase_count and buyer_count keep counting the trades
        that did happen; a re-listing puts the listing back on
        the live side without touching history. No arguments, so
        no gate: the face is a pure read with zero row mutations
        and zero token movement, and the envelope carries the
        resident non-advisory disclaimer."""
        with self._lock:
            listings = self._conn.execute(
                "SELECT listing_id FROM apimarket_listings"
                " ORDER BY listing_id").fetchall()
            listing_count = len(listings)
            live = 0
            retired = 0
            price_sum = 0
            for r in listings:
                listing_id = int(r[0])
                if self._delisted_utc(listing_id) is None:
                    live += 1
                    price_sum += self._current_price(listing_id)
                else:
                    retired += 1
            dev_count = int(self._conn.execute(
                "SELECT COUNT(DISTINCT dev_account)"
                " FROM apimarket_listings").fetchone()[0])
            buyer_count = int(self._conn.execute(
                "SELECT COUNT(DISTINCT buyer_id)"
                " FROM apimarket_purchases").fetchone()[0])
            paid = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(price_paid), 0),"
                " COALESCE(SUM(dev_share), 0),"
                " COALESCE(SUM(platform_share), 0)"
                " FROM apimarket_purchases").fetchone()
            back = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(amount), 0),"
                " COALESCE(SUM(dev_share), 0),"
                " COALESCE(SUM(platform_share), 0)"
                " FROM apimarket_refunds").fetchone()
            purchase_count = int(paid[0])
            refund_count = int(back[0])
            gross = int(paid[1])
            refunded = int(back[1])
            avg_price = (float(price_sum) / live) if live else None
        return {"listing_count": listing_count,
                "live_listing_count": live,
                "retired_listing_count": retired,
                "dev_count": dev_count,
                "buyer_count": buyer_count,
                "purchase_count": purchase_count,
                "refund_count": refund_count,
                "net_purchase_count": purchase_count - refund_count,
                "gross_tokens": gross,
                "refunded_tokens": refunded,
                "net_gross_tokens": gross - refunded,
                "dev_revenue": int(paid[2]) - int(back[2]),
                "platform_revenue": int(paid[3]) - int(back[3]),
                "avg_live_price": avg_price,
                "disclaimer": self.disclaimer}

    def api_buyer_profile(self, buyer_id):
        """Buyer-side trust/account face (pre-registered
        AC-AMBY1..AC-AMBY8 in the R2091 explore-queue row BEFORE
        this code existed): the resident's own account in one
        envelope.

        The reading chain had a seller profile (dev_profile), a
        market overview (api_market_stats) and a buyer library
        (api_library) that lists rows, but nothing answered the
        buyer's aggregate question "what has this account spent,
        got back and rated". Aggregates only - the row face stays
        api_library, so this face never duplicates it.

        Laws pinned by the suite: spend conservation (net_spent ==
        gross_spent - refunded_total and purchase_count ==
        net_purchase_count + refund_count); pool conservation
        (dev_paid + platform_paid == net_spent exactly, integer
        split); a refund lowers only the net side while
        purchase_count and listing_count keep counting the trades
        that did happen; rating aggregates come from this buyer's
        own ratings only and are None on an honest empty history;
        watch_count counts every append-only watch row while
        live_watch_count counts the active set (a watch with no
        unwatch row), so an unwatch never erases history; the
        account shape gate is prefix-only and runs before any
        read; a prefix-valid account with no history gets an
        honest zero envelope, not an error. Pure read: zero row
        mutations and zero token movement, and the envelope
        carries the resident non-advisory disclaimer."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        with self._lock:
            paid = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(price_paid), 0),"
                " COALESCE(SUM(dev_share), 0),"
                " COALESCE(SUM(platform_share), 0),"
                " COUNT(DISTINCT listing_id), MIN(purchased_utc),"
                " MAX(purchased_utc) FROM apimarket_purchases"
                " WHERE buyer_id = ?", (buyer_id,)).fetchone()
            back = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(amount), 0),"
                " COALESCE(SUM(dev_share), 0),"
                " COALESCE(SUM(platform_share), 0)"
                " FROM apimarket_refunds WHERE buyer_id = ?",
                (buyer_id,)).fetchone()
            rate = self._conn.execute(
                "SELECT rating_id, stars"
                " FROM apimarket_ratings WHERE buyer_id = ?",
                (buyer_id,)).fetchall()
            rate_count = len(rate)
            rate_sum = sum(self._effective_stars(int(r[0]), int(r[1]))
                           for r in rate)
            watch = self._conn.execute(
                "SELECT COUNT(*) FROM apimarket_watchlist"
                " WHERE buyer_id = ?", (buyer_id,)).fetchone()
            live_watch = self._conn.execute(
                "SELECT COUNT(*) FROM apimarket_watchlist w"
                " WHERE w.buyer_id = ? AND NOT EXISTS"
                " (SELECT 1 FROM apimarket_unwatchings u"
                " WHERE u.watch_id = w.watch_id)",
                (buyer_id,)).fetchone()
            purchase_count = int(paid[0])
            refund_count = int(back[0])
            gross = int(paid[1])
            refunded = int(back[1])
            rating_count = rate_count
        return {"buyer_id": buyer_id,
                "purchase_count": purchase_count,
                "refund_count": refund_count,
                "net_purchase_count": purchase_count - refund_count,
                "listing_count": int(paid[4]),
                "gross_spent": gross,
                "refunded_total": refunded,
                "net_spent": gross - refunded,
                "dev_paid": int(paid[2]) - int(back[2]),
                "platform_paid": int(paid[3]) - int(back[3]),
                "rating_count": rating_count,
                "avg_rating": (float(rate_sum) / rating_count
                               if rating_count else None),
                "watch_count": int(watch[0]),
                "live_watch_count": int(live_watch[0]),
                "first_purchase_utc": paid[5],
                "last_purchase_utc": paid[6],
                "disclaimer": self.disclaimer}

    def api_buyer_months(self, buyer_id):
        """Buyer-side monthly spend timeline (pre-registered
        AC-AMBM1..AC-AMBM8 in the R2100 explore-queue row BEFORE this
        code existed).

        The resident-side mirror of api_revenue_months. The seller
        side had a cash-basis month table, but the buyer side only
        had api_buyer_profile (lifetime aggregates) and api_library
        (rows): nobody answered "what did this account spend in
        October, and what came back", and the difference between the
        month a purchase books in and the month its refund lands in
        was invisible on the row faces. A statement period, a monthly
        budget view or a month-on-month comparison all needed the
        caller to rebucket rows by hand.

        Cash basis is pinned deliberately and symmetrically: a
        purchase is booked in the UTC month of its purchased_utc and
        a refund is booked in the UTC month of its refunded_utc -
        never rewriting the month the purchase landed in. A refund
        that lands in a later month therefore produces an honestly
        negative net there while the original month stays
        byte-frozen. listing_count is purchase-derived only, so a
        refund-only month honestly reports zero listings beside its
        refund row. Only months with activity appear. Pure read:
        zero row mutations and zero token movement.
        """
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        buyer = str(buyer_id)
        with self._lock:
            purchases = self._conn.execute(
                "SELECT p.price_paid, p.dev_share, p.platform_share,"
                " p.purchased_utc, p.listing_id"
                " FROM apimarket_purchases p WHERE p.buyer_id = ?",
                (buyer,)).fetchall()
            refunds = self._conn.execute(
                "SELECT f.amount, f.dev_share, f.platform_share,"
                " f.refunded_utc FROM apimarket_refunds f"
                " WHERE f.buyer_id = ?", (buyer,)).fetchall()

        buckets = {}

        def bucket(month):
            return buckets.setdefault(
                month, {"month": month, "purchase_count": 0,
                        "gross_spent": 0, "refund_count": 0,
                        "refunded": 0, "dev_paid": 0,
                        "platform_paid": 0,
                        "refunded_dev_share": 0,
                        "refunded_platform_share": 0,
                        "listings": set()})

        for price, dev_share, platform_share, stamp, listing_id in \
                purchases:
            b = bucket(str(stamp)[:7])
            b["purchase_count"] += 1
            b["gross_spent"] += int(price)
            b["dev_paid"] += int(dev_share)
            b["platform_paid"] += int(platform_share)
            b["listings"].add(int(listing_id))
        for amount, dev_share, platform_share, stamp in refunds:
            b = bucket(str(stamp)[:7])
            b["refund_count"] += 1
            b["refunded"] += int(amount)
            b["refunded_dev_share"] += int(dev_share)
            b["refunded_platform_share"] += int(platform_share)

        months = []
        for month in sorted(buckets):
            b = buckets[month]
            months.append({
                "month": month,
                "purchase_count": b["purchase_count"],
                "gross_spent": b["gross_spent"],
                "refund_count": b["refund_count"],
                "refunded": b["refunded"],
                "net": b["gross_spent"] - b["refunded"],
                "dev_paid": b["dev_paid"],
                "platform_paid": b["platform_paid"],
                "dev_paid_net": (b["dev_paid"]
                                 - b["refunded_dev_share"]),
                "platform_paid_net": (b["platform_paid"]
                                      - b["refunded_platform_share"]),
                "listing_count": len(b["listings"]),
            })
        return {"buyer_id": buyer,
                "month_count": len(months),
                "lifetime_purchase_count": sum(
                    m["purchase_count"] for m in months),
                "lifetime_gross_spent": sum(
                    m["gross_spent"] for m in months),
                "lifetime_refund_count": sum(
                    m["refund_count"] for m in months),
                "lifetime_refunded": sum(
                    m["refunded"] for m in months),
                "lifetime_net_spent": sum(
                    m["net"] for m in months),
                "lifetime_dev_paid": sum(
                    m["dev_paid_net"] for m in months),
                "lifetime_platform_paid": sum(
                    m["platform_paid_net"] for m in months),
                "disclaimer": self.disclaimer,
                "months": months}
