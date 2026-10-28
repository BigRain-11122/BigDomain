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

# Refund-propensity prior weight, in purchases, applied to the market
# rate by the shrinkage form of api_buyer_refund_propensity (AC-RFP4).
_RFP_SMOOTH = 10

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
E_AM_BAD_STAMP = "E_AM_BAD_STAMP"        # AC-MHH3 hour heatmap parse
E_AM_DELISTED = "E_AM_DELISTED"           # AC-AMD5 (retired listing)
E_AM_NOT_OWNER = "E_AM_NOT_OWNER"         # AC-AMD2 (ownership gate)
E_AM_ALREADY_DELISTED = "E_AM_ALREADY_DELISTED"  # AC-AMD3
E_AM_ALREADY_LIVE = "E_AM_ALREADY_LIVE"    # AC-AMRL2 (relist on live)
E_AM_PRICE_UNCHANGED = "E_AM_PRICE_UNCHANGED"  # AC-AMPR4
E_AM_METADATA_UNCHANGED = "E_AM_METADATA_UNCHANGED"  # AC-AMME6
E_AM_WATCH_DUP = "E_AM_WATCH_DUP"          # AC-AMWL5
E_AM_NOT_WATCHED = "E_AM_NOT_WATCHED"      # AC-AMWL3
E_AM_NOT_PARTY = "E_AM_NOT_PARTY"          # AC-AMPD2 (dossier viewer gate)
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
E_AM_BAD_QUESTION = "E_AM_BAD_QUESTION"      # AC-AMQA2 (question shape)
E_AM_UNKNOWN_QUESTION = "E_AM_UNKNOWN_QUESTION"  # AC-AMQA3
E_AM_ALREADY_ANSWERED = "E_AM_ALREADY_ANSWERED"  # AC-AMQA3
E_AM_BAD_PROVIDER = "E_AM_BAD_PROVIDER"    # AC-AMPI2 (name/credit shape)
E_AM_PROVIDER_DUP = "E_AM_PROVIDER_DUP"    # AC-AMPI2 (one per dev)
E_AM_BAD_DECISION = "E_AM_BAD_DECISION"    # AC-AMPI5 (approve/refuse only)
E_AM_BAD_REASON = "E_AM_BAD_REASON"        # AC-AMPI5 (refusal needs reason)
E_AM_ALREADY_REVIEWED = "E_AM_ALREADY_REVIEWED"  # AC-AMPI5
E_AM_CLAIM_DUP = "E_AM_CLAIM_DUP"          # AC-AMCL4 (one claim per buy)
E_AM_BAD_CLAIM = "E_AM_BAD_CLAIM"          # AC-AMCL3 (claim text shape)
E_AM_UNKNOWN_CLAIM = "E_AM_UNKNOWN_CLAIM"  # AC-AMCR3 (no such claim)
E_AM_BAD_RESPONSE = "E_AM_BAD_RESPONSE"    # AC-AMCR3 (answer shape)
E_AM_CLAIM_ANSWERED = "E_AM_CLAIM_ANSWERED"  # AC-AMCR4 (one answer)
E_AM_CLAIM_WITHDRAWN = "E_AM_CLAIM_WITHDRAWN"  # AC-AMCW4 (one withdrawal)
E_AM_BAD_NOTE = "E_AM_BAD_NOTE"            # AC-AMCN3 (note shape)
E_AM_CLAIM_NOTE_DUP = "E_AM_CLAIM_NOTE_DUP"  # AC-AMCN4 (one note)
E_AM_ALREADY_RESUBMITTED = "E_AM_ALREADY_RESUBMITTED"  # AC-AMRC2
E_AM_REVIEW_PENDING = "E_AM_REVIEW_PENDING"  # AC-AMRC2 (no verdict yet)
E_AM_REVIEW_APPROVED = "E_AM_REVIEW_APPROVED"  # AC-AMRC2 (already live)
E_AM_PROVIDER_UNREGISTERED = "E_AM_PROVIDER_UNREGISTERED"  # AC-AMPV2
E_AM_PROVIDER_UNCHANGED = "E_AM_PROVIDER_UNCHANGED"  # AC-AMPV3
E_AM_UNKNOWN_REPLY = "E_AM_UNKNOWN_REPLY"      # AC-AMRY2 (no such reply)
E_AM_REPLY_UNCHANGED = "E_AM_REPLY_UNCHANGED"  # AC-AMRY3 (same text)
E_AM_UNKNOWN_ANSWER = "E_AM_UNKNOWN_ANSWER"    # AC-AMAW2 (no such answer)
E_AM_ANSWER_UNCHANGED = "E_AM_ANSWER_UNCHANGED"  # AC-AMAW2 (same text)
E_AM_CATEGORY_UNCHANGED = "E_AM_CATEGORY_UNCHANGED"  # AC-AMCG1 (same bucket)

_CONTENT_REJECTED_CODE = "E_CONTENT_REJECTED"  # lobby SecGate hit

# Provider identity field caps (AC-AMPV2): the disclosure name and
# the unified social credit code are both published verbatim, so one
# shared shape keeps the registration door and the revision door from
# diverging.
_PROVIDER_NAME_MAX = 120
_PROVIDER_CODE_MAX = 64

# Category declaration cap: the publish door and the revision door
# share one bound so the two shape gates can never diverge (the
# 40-char literal used to live inline in publish_api).
_CATEGORY_MAX = 40

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
    category TEXT,
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
CREATE TABLE IF NOT EXISTS apimarket_category_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    previous_category TEXT,
    category TEXT,
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
CREATE TABLE IF NOT EXISTS apimarket_reply_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reply_id INTEGER NOT NULL,
    rating_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    previous_text TEXT NOT NULL,
    reply_text TEXT NOT NULL,
    revised_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS apimarket_answer_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    answer_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    previous_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    revised_utc TEXT NOT NULL
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
CREATE TABLE IF NOT EXISTS apimarket_questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    asked_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS apimarket_answers (
    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    answered_utc TEXT NOT NULL,
    UNIQUE (question_id)
);
CREATE TABLE IF NOT EXISTS apimarket_providers (
    provider_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dev_account TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    credit_code TEXT NOT NULL,
    registered_utc TEXT NOT NULL,
    UNIQUE (dev_account)
);
CREATE TABLE IF NOT EXISTS apimarket_provider_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dev_account TEXT NOT NULL,
    previous_provider_name TEXT NOT NULL,
    previous_credit_code TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    credit_code TEXT NOT NULL,
    revised_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS apimarket_reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('approve', 'refuse')),
    reason TEXT NOT NULL,
    reviewed_utc TEXT NOT NULL,
    cycle INTEGER NOT NULL DEFAULT 1,
    UNIQUE (listing_id, cycle)
);
CREATE TABLE IF NOT EXISTS apimarket_review_resubmits (
    resubmit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    cycle INTEGER NOT NULL,
    note TEXT NOT NULL,
    resubmitted_utc TEXT NOT NULL,
    UNIQUE (listing_id, cycle)
);
CREATE TABLE IF NOT EXISTS apimarket_claims (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    dev_account TEXT NOT NULL,
    price_paid INTEGER NOT NULL,
    claim_text TEXT NOT NULL,
    opened_utc TEXT NOT NULL,
    UNIQUE (purchase_id)
);
CREATE TABLE IF NOT EXISTS apimarket_claim_responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    response_text TEXT NOT NULL,
    replied_utc TEXT NOT NULL,
    UNIQUE (claim_id)
);
CREATE TABLE IF NOT EXISTS apimarket_claim_withdrawals (
    claim_id INTEGER PRIMARY KEY,
    buyer_id TEXT NOT NULL,
    withdrawn_utc TEXT NOT NULL,
    UNIQUE (claim_id)
);
CREATE TABLE IF NOT EXISTS apimarket_claim_notes (
    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    note_text TEXT NOT NULL,
    noted_utc TEXT NOT NULL,
    UNIQUE (claim_id)
);
"""


# Discovery sort modes (AC-AMSR2, pre-registered in the R2098
# explore-queue row BEFORE this code existed). The default (None)
# keeps the R2082 ordering - current price ascending, then
# listing_id ascending - so a caller that never passes a sort token
# reads a byte-identical contract.
_SEARCH_SORT_MODES = ("price_asc", "price_desc", "rating", "sales",
                      "newest")

# Public activity feed kinds. The tuple order IS the same-second
# tie-break rank (AC-AMF2, pre-registered in the R2107 queue row
# BEFORE this code existed).
_WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _stamp_hour_weekday(stamp):
    """UTC hour-of-day and weekday index (Mon=0) of one stored
    instant (AC-MHH3). Strict round-trip parse on the same law
    _assert_instant uses, so no lenient strptime form can shift a
    trade into a neighbouring bucket."""
    text = str(stamp)
    try:
        parsed = datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ApiMarketError(E_AM_BAD_STAMP, "bad stamp: " + text)
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != text:
        raise ApiMarketError(E_AM_BAD_STAMP, "bad stamp: " + text)
    return parsed.weekday(), parsed.hour


_FEED_KINDS = ("published", "relisted", "price_revised",
               "metadata_revised", "restocked", "purchased",
               "rated", "rating_revised", "rating_replied",
               "refunded", "delisted")
_FEED_KIND_RANK = {k: i for i, k in enumerate(_FEED_KINDS)}


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


def _assert_day(day):
    """Strict calendar-day validation for the YYYY-MM-DD window
    (AC-MDL6): the same round-trip law _assert_month uses, so a
    zero-unpadded, trailing-garbage or impossible date (2026-02-30)
    cannot silently shift a trade into a neighbouring day."""
    if not isinstance(day, str):
        raise ApiMarketError(E_AM_BAD_WINDOW, "day must be a string")
    try:
        parsed = datetime.datetime.strptime(day, "%Y-%m-%d")
    except ValueError:
        raise ApiMarketError(E_AM_BAD_WINDOW, "bad day: " + day)
    if parsed.strftime("%Y-%m-%d") != day:
        raise ApiMarketError(E_AM_BAD_WINDOW, "bad day: " + day)
    return day


def _day_sequence(first, last):
    """Every UTC calendar day from first to last inclusive, both ends
    already validated (AC-MDL4): the honest zero days inside an
    activity extent belong to the answer, they are not a gap."""
    cursor = datetime.datetime.strptime(first, "%Y-%m-%d").date()
    limit = datetime.datetime.strptime(last, "%Y-%m-%d").date()
    out = []
    while cursor <= limit:
        out.append(cursor.isoformat())
        cursor += datetime.timedelta(days=1)
    return out


def _refund_latency_seconds(purchased_utc, refunded_utc):
    """Elapsed seconds between the two stored stamps of one refund
    (AC-RFLT2). Both are strict UTC instants written by this module's
    own doors, so parsing them is the whole derivation - never a wall
    clock - and a leg that never happened is the caller's None, never
    a zero."""
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    start = datetime.datetime.strptime(str(purchased_utc), fmt)
    end = datetime.datetime.strptime(str(refunded_utc), fmt)
    return int((end - start).total_seconds())


# Latency bands, lower inclusive and upper exclusive, so a stamp on a
# boundary belongs to the UPPER band and the bands stay exhaustive
# without overlap (AC-RFLT3).
_REFUND_LATENCY_BANDS = (
    ("0-1h", 0, 3600),
    ("1-6h", 3600, 21600),
    ("6-24h", 21600, 86400),
    ("1-3d", 86400, 259200),
    ("3-7d", 259200, 604800),
    ("7d+", 604800, None),
)


def _assert_instant(value, label):
    """Strict UTC instant shape for the feed window (AC-AMF3): the
    same round-trip law _assert_month uses, so zero padding and
    trailing garbage cannot slip through. None is handled by the
    caller; every other form must be a real string."""
    if not isinstance(value, str):
        raise ApiMarketError(E_AM_BAD_WINDOW, label + " must be a string")
    try:
        parsed = datetime.datetime.strptime(
            value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ApiMarketError(E_AM_BAD_WINDOW, "bad " + label + ": " + value)
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ApiMarketError(E_AM_BAD_WINDOW, "bad " + label + ": " + value)
    return value


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


def _month_end(month):
    """Last second of one UTC calendar month, as a stored instant
    (AC-CPM2): the point-in-time sample of the category price trend.
    The month is validated on the same round-trip law _assert_month
    uses, so a malformed key can never silently sample a neighbouring
    month."""
    clean = _assert_month(month)
    parsed = datetime.datetime.strptime(clean, "%Y-%m")
    if parsed.month == 12:
        following = datetime.datetime(parsed.year + 1, 1, 1)
    else:
        following = datetime.datetime(parsed.year, parsed.month + 1, 1)
    last = following - datetime.timedelta(seconds=1)
    return last.strftime("%Y-%m-%dT%H:%M:%SZ")


def _contiguous_months(months):
    """Inclusive contiguous month list between the first and the last
    key (AC-CPM2): a month with no event at all still gets its sample,
    so an honest zero row is visible instead of silently absent."""
    if not months:
        return []
    first = datetime.datetime.strptime(_assert_month(months[0]), "%Y-%m")
    last = datetime.datetime.strptime(_assert_month(months[-1]), "%Y-%m")
    out = []
    year, month = first.year, first.month
    while (year, month) <= (last.year, last.month):
        out.append("%04d-%02d" % (year, month))
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    return out


def percentile(sorted_values, q):
    """Linear-interpolation percentile (AC-MPP3): the position on the
    ascending sample list is pos = (n - 1) * q and the value is
    interpolated between the two neighbouring samples. With one
    sample there is nothing to interpolate, so every quantile is that
    sample. Deterministic, zero RNG, no third-party dependency."""
    n = len(sorted_values)
    if n == 0:
        return None
    pos = (n - 1) * q
    lo = int(pos)
    hi = lo + 1 if pos > lo else lo
    if hi >= n:
        return float(sorted_values[n - 1])
    frac = pos - lo
    low = float(sorted_values[lo])
    if not frac:
        return low
    return low + (float(sorted_values[hi]) - low) * frac


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
        self._ensure_category_column()
        self._ensure_lifecycle_schema()
        self._ensure_review_cycle_schema()

    def _ensure_review_cycle_schema(self):
        """Idempotent forward migration for databases written
        before the review-cycle axis existed (AC-AMRC7). The old
        apimarket_reviews carried UNIQUE(listing_id) - one terminal
        verdict per listing - which the cycle law must relax, and
        SQLite cannot drop a constraint in place, so the table is
        rebuilt once: same rows, same ids, cycle 1. The rebuild runs
        only when the legacy shape is actually present, so an
        already-migrated database is never touched and every
        existing verdict keeps its original stamp."""
        cols = [r[1] for r in self._conn.execute(
            "PRAGMA table_info(apimarket_reviews)").fetchall()]
        row = self._conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table'"
            " AND name = 'apimarket_reviews'").fetchone()
        flat = str(row[0] or "").upper().replace(" ", "") \
            if row is not None else ""
        legacy_unique = "UNIQUE(LISTING_ID)" in flat
        if "cycle" in cols and not legacy_unique:
            return
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "ALTER TABLE apimarket_reviews RENAME TO"
                " apimarket_reviews_legacy")
            self._conn.execute(
                "CREATE TABLE apimarket_reviews ("
                " review_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " listing_id INTEGER NOT NULL,"
                " decision TEXT NOT NULL CHECK"
                " (decision IN ('approve','refuse')),"
                " reason TEXT NOT NULL,"
                " reviewed_utc TEXT NOT NULL,"
                " cycle INTEGER NOT NULL DEFAULT 1,"
                " UNIQUE (listing_id, cycle))")
            cycle_expr = "cycle" if "cycle" in cols else "1"
            self._conn.execute(
                "INSERT INTO apimarket_reviews (review_id,"
                " listing_id, decision, reason, reviewed_utc,"
                " cycle) SELECT review_id, listing_id, decision,"
                " reason, reviewed_utc, %s FROM"
                " apimarket_reviews_legacy ORDER BY review_id"
                % cycle_expr)
            self._conn.execute("DROP TABLE apimarket_reviews_legacy")
            self._conn.execute("COMMIT")
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise

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

    def _ensure_category_column(self):
        """Idempotent forward migration for databases written
        before the category axis existed (AC-AMCT8): the column is
        added only when absent, so old rows keep category NULL and
        stay listed, searchable and purchasable - the pre-change
        behaviour is preserved - while the directory face reports
        them honestly in its uncategorized bucket."""
        cols = [r[1] for r in self._conn.execute(
            "PRAGMA table_info(apimarket_listings)").fetchall()]
        if "category" not in cols:
            self._conn.execute(
                "ALTER TABLE apimarket_listings ADD COLUMN category"
                " TEXT")

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
                    supply=None, category=None):
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
        # Category is the same kind of pre-lock shape gate
        # (AC-AMCT1): a malformed taxonomy declaration is refused
        # before the registry read and before any msgSecCheck call,
        # so a bad category burns zero gate calls and stores zero
        # rows. None = uncategorized.
        if category is None:
            cat = None
        else:
            if not isinstance(category, str):
                raise ApiMarketError(E_AM_BAD_ARGS,
                                     "category must be str or None")
            cat = category.strip()
            if not cat:
                raise ApiMarketError(E_AM_BAD_ARGS, "category blank")
            if len(cat) > _CATEGORY_MAX:
                raise ApiMarketError(E_AM_BAD_ARGS,
                                     "category too long")
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
                    " token_price, ai_label, listed_utc, supply,"
                    " category)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (dev_account, key, t, d, body, token_price,
                     1 if ai_generated else 0, _now_utc(), supply,
                     cat))
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
                "supply": supply, "category": cat}

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

    def _review_cycle(self, listing_id):
        """Current review cycle of one listing (AC-AMRC1). Cycle 1
        is the publish-time submission; every seller resubmit after
        a refusal opens the next one, so the current cycle is the
        highest append-only resubmit row (or 1). Caller holds the
        lock."""
        row = self._conn.execute(
            "SELECT MAX(cycle) FROM apimarket_review_resubmits"
            " WHERE listing_id = ?", (listing_id,)).fetchone()[0]
        return 1 if row is None else int(row)

    def _current_review(self, listing_id):
        """(decision, reason, reviewed_utc) of one listing's CURRENT
        review cycle, or None while that cycle is still pending
        (AC-AMRC5). One seam keeps api_public_listings, the operator
        queue and the seller status face from drifting. Caller holds
        the lock."""
        return self._conn.execute(
            "SELECT decision, reason, reviewed_utc FROM"
            " apimarket_reviews WHERE listing_id = ? AND cycle = ?",
            (listing_id, self._review_cycle(listing_id))).fetchone()

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

    def _category_state(self, listing_id, base_category):
        """(effective_category, revision_count, latest_revised_utc).
        The newest append-only category revision wins; with no
        revision the declaration made at publish time speaks. This
        is the ONE seam every category reader goes through, so a
        revision moves the catalog, the demand face, the discovery
        filter and the competitive bucket in exactly one step.
        Caller holds the lock."""
        row = self._conn.execute(
            "SELECT category, revised_utc FROM"
            " apimarket_category_revisions WHERE listing_id = ?"
            " ORDER BY revision_id DESC LIMIT 1",
            (listing_id,)).fetchone()
        count = int(self._conn.execute(
            "SELECT COUNT(*) FROM apimarket_category_revisions"
            " WHERE listing_id = ?", (listing_id,)).fetchone()[0])
        if row is None:
            return base_category, 0, None
        return row[0], count, row[1]

    def _effective_category(self, listing_id):
        """Effective category of one listing (no revision stats).
        Caller holds the lock."""
        base = self._conn.execute(
            "SELECT category FROM apimarket_listings"
            " WHERE listing_id = ?", (listing_id,)).fetchone()
        if base is None:
            raise ApiMarketError(E_AM_UNKNOWN_LISTING, str(listing_id))
        return self._category_state(listing_id, base[0])[0]

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

    def revise_category(self, dev_account, listing_id, category=None):
        """Seller-side category revision door (criteria
        AC-AMCG1..AC-AMCG8 pre-registered in the R2147 explore-queue
        row BEFORE this code existed).

        publish_api declares a category exactly once and that
        declaration was the last write-once declaration on the
        listing row with no remedy leg: edit_listing repairs title
        and description only, revise_price and revise_category's
        siblings each have their own revision table, but a seller
        who filed a service under the wrong bucket was stuck with
        it forever. The miscategorisation then poisoned four read
        faces at once - the catalog directory, the demand face,
        the discovery category filter and the competitive bucket -
        because every one of them read the stored declaration.

        This face adds one append-only apimarket_category_revisions
        row per change; the listing row is never rewritten, so the
        original declaration survives as base forever (AC-AMCG1).
        Passing None re-files the listing into the honest
        uncategorized bucket, which is a legal move and not a
        deletion.

        Gate order is pinned by AC-AMCG2, every gate before any
        write: account shape, listing shape/existence, ownership,
        the retired state, category shape (None or a non-blank
        string within the publish cap), then the no-change state. A
        same-bucket call answers E_AM_CATEGORY_UNCHANGED with zero
        new rows while revising back to an earlier bucket stays
        legal, because the comparison is against the CURRENT
        effective bucket (AC-AMCG4). Revising moves zero tokens and
        touches no purchase, rating or refund row."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            listing = self._require_listing(listing_id)
            if listing[1] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, listing_id))
            if self._delisted_utc(listing_id) is not None:
                raise ApiMarketError(E_AM_DELISTED, str(listing_id))
            if category is None:
                new_cat = None
            else:
                if not isinstance(category, str):
                    raise ApiMarketError(E_AM_BAD_ARGS,
                                         "category must be str or None")
                new_cat = category.strip()
                if not new_cat:
                    raise ApiMarketError(E_AM_BAD_ARGS,
                                         "category blank")
                if len(new_cat) > _CATEGORY_MAX:
                    raise ApiMarketError(E_AM_BAD_ARGS,
                                         "category too long")
            base = self._conn.execute(
                "SELECT listing_key, category FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()
            cur_cat, count, _latest = self._category_state(
                listing_id, base[1])
            if new_cat == cur_cat:
                raise ApiMarketError(E_AM_CATEGORY_UNCHANGED,
                                     str(listing_id))
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_category_revisions"
                    " (listing_id, dev_account, previous_category,"
                    " category, revised_utc) VALUES (?,?,?,?,?)",
                    (listing_id, dev_account, cur_cat, new_cat, stamp))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"listing_id": listing_id,
                "dev_account": dev_account,
                "listing_key": base[0],
                "revision_id": cur.lastrowid,
                "previous_category": cur_cat,
                "category": new_cat,
                "category_revision_count": count + 1,
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

    def revise_reply(self, dev_account, reply_id, text):
        """Seller-side reply revision door (pre-registered
        AC-AMRY1..AC-AMRY8 in the R2143 explore-queue claim row
        BEFORE this code existed).

        The reply face was write-once: one immutable row per rating
        behind UNIQUE(rating_id) and E_AM_REPLY_DUP forever. Once
        R2094 let the buyer revise the stars, a seller who answered
        "glad it worked" under five stars stayed welded to that
        sentence when the same rating became one star - the last
        write-once axis on the trust face without a remedy door
        (price, metadata, supply, rating and provider identity all
        grew one). Each revision appends one
        apimarket_reply_revisions row and never rewrites the base
        reply; the effective text is the newest revision, else the
        base stamp.

        Gate order pinned by AC-AMRY2: account shape, reply-id
        shape, text shape, existence, ownership, unchanged state.
        The unchanged gate compares against the EFFECTIVE text, so
        revising back to an earlier wording stays legal while a
        same-text revision answers E_AM_REPLY_UNCHANGED with zero
        new rows (the first stamp is never rewritten). A retired
        listing keeps its reply leg revisable - retirement freezes
        the shelf, not the duty to answer (AC-AMRY4). Revising
        moves zero tokens and touches no star value: rating
        aggregates stay byte-identical (AC-AMRY7)."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        if (not isinstance(reply_id, int) or isinstance(reply_id, bool)
                or reply_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(reply_id))
        if not isinstance(text, str):
            raise ApiMarketError(E_AM_BAD_REPLY, "text must be str")
        body = text.strip()
        if (not body or len(body) > 500
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in body)):
            raise ApiMarketError(E_AM_BAD_REPLY, str(text)[:40])
        with self._lock:
            row = self._conn.execute(
                "SELECT rating_id, listing_id, dev_account, reply_text"
                " FROM apimarket_rating_replies WHERE reply_id = ?",
                (reply_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_REPLY,
                                     str(reply_id))
            if row[2] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, reply_id))
            rating_id = int(row[0])
            listing_id = int(row[1])
            previous = self._effective_reply(reply_id, row[3])
            if body == previous:
                raise ApiMarketError(E_AM_REPLY_UNCHANGED,
                                     "%s/%s" % (reply_id, body[:40]))
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_reply_revisions"
                    " (reply_id, rating_id, listing_id, dev_account,"
                    " previous_text, reply_text, revised_utc)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (reply_id, rating_id, listing_id, dev_account,
                     previous, body, stamp))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"revision_id": cur.lastrowid, "reply_id": reply_id,
                "rating_id": rating_id, "listing_id": listing_id,
                "dev_account": dev_account,
                "previous_text": previous, "reply_text": body,
                "revised_utc": stamp, "disclaimer": self.disclaimer}

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

    def _effective_reply(self, reply_id, base_text):
        """Effective reply text of one rating reply: the newest
        append-only revision, else the immutable base stamp
        (AC-AMRY4 single seam). Caller holds the lock."""
        row = self._conn.execute(
            "SELECT reply_text FROM apimarket_reply_revisions"
            " WHERE reply_id = ? ORDER BY revision_id DESC LIMIT 1",
            (reply_id,)).fetchone()
        return base_text if row is None else row[0]

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
                " description, token_price, ai_label, listed_utc,"
                " category"
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
            eff_cat, n_cat_rev, latest_cat = self._category_state(
                listing_id, row[8])
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
                "category": eff_cat,
                "base_category": row[8],
                "category_revision_count": n_cat_rev,
                "latest_category_revision_utc": latest_cat,
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
            # R2110 additive key: rating_id is the ONLY handle that
            # api_rating_history accepts, and no listing-wide face
            # exposed it before (it surfaced only through the seller
            # inbox, and only for unanswered rows), so the history face
            # was unreachable from any aggregate read. Existing keys
            # keep their values.
            rows = [{"rating_id": int(r[0]), "buyer_id": r[1],
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
                             "reply_text": self._effective_reply(
                                 int(r[4]), r[6]),
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

    def api_reply_history(self, reply_id):
        """Reply revision history surface (AC-AMRY5): the immutable
        base wording, every append-only revision in order, the
        effective text and the revision count, alongside the star
        value the reply currently answers (the buyer may have
        revised it since). An unknown reply answers
        E_AM_UNKNOWN_REPLY and a bad id answers E_AM_BAD_ARGS before
        any read. Pure read: zero row mutations, zero tokens."""
        if (not isinstance(reply_id, int) or isinstance(reply_id, bool)
                or reply_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(reply_id))
        with self._lock:
            row = self._conn.execute(
                "SELECT rating_id, listing_id, dev_account, reply_text,"
                " replied_utc FROM apimarket_rating_replies"
                " WHERE reply_id = ?", (reply_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_REPLY,
                                     str(reply_id))
            rating_id = int(row[0])
            rated = self._conn.execute(
                "SELECT buyer_id, stars FROM apimarket_ratings"
                " WHERE rating_id = ?", (rating_id,)).fetchone()
            revs = self._conn.execute(
                "SELECT revision_id, previous_text, reply_text,"
                " revised_utc FROM apimarket_reply_revisions"
                " WHERE reply_id = ? ORDER BY revision_id",
                (reply_id,)).fetchall()
            base = row[3]
            effective = base if not revs else revs[-1][2]
            stars = (0 if rated is None
                     else self._effective_stars(rating_id,
                                                int(rated[1])))
            buyer = "" if rated is None else rated[0]
        return {"reply_id": reply_id, "rating_id": rating_id,
                "listing_id": int(row[1]), "dev_account": row[2],
                "buyer_id": buyer, "stars": stars,
                "effective_text": effective, "base_text": base,
                "revision_count": len(revs),
                "latest_revised_utc": (None if not revs
                                       else revs[-1][3]),
                "disclaimer": self.disclaimer,
                "revisions": [{"revision_id": int(x[0]),
                               "previous_text": x[1],
                               "reply_text": x[2],
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

    def api_market_hour_heatmap(self):
        """Market activity-by-time heatmap (pre-registered
        AC-MHH1..AC-MHH8 in the R2165 explore-queue row BEFORE this
        code existed).

        Every time axis the market had was a month: api_market_months
        sums the whole market per UTC month, api_revenue_months one
        seller's cash months, api_buyer_months one resident's months
        and api_category_refund_months one category's refund months,
        while api_market_feed is an event list. Nothing answered the
        far coarser-grained operating question - which hour of the
        day and which weekday the market actually trades in - so a
        seller picking a publish or repricing moment, or an operator
        sizing support cover, had no face at all.

        The row authority is the same append-only trade pair the
        monthly face uses, on the same cash-basis law: a sale books
        in the UTC hour/weekday of purchased_utc and a refund books
        in the hour/weekday of refunded_utc, never rewriting the
        bucket the sale landed in. The grid is always complete (24
        hour rows, 7 weekday rows, 168 cells) so an honest zero row
        is visible instead of absent. No arguments, so no gate: pure
        read, zero row mutations and zero token movement.
        """
        with self._lock:
            sales = self._conn.execute(
                "SELECT p.buyer_id, p.price_paid, p.purchased_utc,"
                " l.dev_account FROM apimarket_purchases p JOIN"
                " apimarket_listings l ON"
                " l.listing_id = p.listing_id").fetchall()
            refunds = self._conn.execute(
                "SELECT f.amount, f.refunded_utc"
                " FROM apimarket_refunds f").fetchall()

        hours = [{"hour": hour, "sales_count": 0, "gross": 0,
                  "refund_count": 0, "refunded": 0,
                  "buyers": set(), "sellers": set()}
                 for hour in range(24)]
        weekdays = [{"weekday": day,
                     "weekday_name": _WEEKDAY_NAMES[day],
                     "sales_count": 0, "gross": 0,
                     "refund_count": 0, "refunded": 0,
                     "buyers": set(), "sellers": set()}
                    for day in range(7)]
        cells = [[{"sales_count": 0, "refund_count": 0}
                  for _hour in range(24)] for _day in range(7)]
        lifetime_buyers = set()
        lifetime_sellers = set()

        for buyer, price, stamp, dev in sales:
            day, hour = _stamp_hour_weekday(stamp)
            for bucket in (hours[hour], weekdays[day]):
                bucket["sales_count"] += 1
                bucket["gross"] += int(price)
                bucket["buyers"].add(buyer)
                bucket["sellers"].add(dev)
            cells[day][hour]["sales_count"] += 1
            lifetime_buyers.add(buyer)
            lifetime_sellers.add(dev)
        for amount, stamp in refunds:
            day, hour = _stamp_hour_weekday(stamp)
            for bucket in (hours[hour], weekdays[day]):
                bucket["refund_count"] += 1
                bucket["refunded"] += int(amount)
            cells[day][hour]["refund_count"] += 1

        hour_rows = [{"hour": b["hour"],
                      "sales_count": b["sales_count"],
                      "gross": b["gross"],
                      "refund_count": b["refund_count"],
                      "refunded": b["refunded"],
                      "net": b["gross"] - b["refunded"],
                      "buyer_count": len(b["buyers"]),
                      "seller_count": len(b["sellers"])}
                     for b in hours]
        weekday_rows = [{"weekday": b["weekday"],
                         "weekday_name": b["weekday_name"],
                         "sales_count": b["sales_count"],
                         "gross": b["gross"],
                         "refund_count": b["refund_count"],
                         "refunded": b["refunded"],
                         "net": b["gross"] - b["refunded"],
                         "buyer_count": len(b["buyers"]),
                         "seller_count": len(b["sellers"])}
                        for b in weekdays]
        cell_rows = [{"weekday": day, "hour": hour,
                      "sales_count": cells[day][hour]["sales_count"],
                      "refund_count": cells[day][hour]["refund_count"]}
                     for day in range(7) for hour in range(24)]

        gross = sum(r["gross"] for r in hour_rows)
        refunded = sum(r["refunded"] for r in hour_rows)
        sales_count = sum(r["sales_count"] for r in hour_rows)
        busiest_hour = None
        busiest_weekday = None
        for row in hour_rows:
            if busiest_hour is None or (
                    row["sales_count"], row["gross"], -row["hour"]) > (
                    busiest_hour["sales_count"], busiest_hour["gross"],
                    -busiest_hour["hour"]):
                busiest_hour = row
        for row in weekday_rows:
            if busiest_weekday is None or (
                    row["sales_count"], row["gross"],
                    -row["weekday"]) > (
                    busiest_weekday["sales_count"],
                    busiest_weekday["gross"],
                    -busiest_weekday["weekday"]):
                busiest_weekday = row
        if sales_count == 0:
            busiest_hour = None
            busiest_weekday = None

        return {"hour_count": len(hour_rows),
                "weekday_count": len(weekday_rows),
                "cell_count": len(cell_rows),
                "sales_count": sales_count,
                "gross": gross,
                "refund_count": sum(
                    r["refund_count"] for r in hour_rows),
                "refunded": refunded,
                "net": gross - refunded,
                "buyer_count": len(lifetime_buyers),
                "seller_count": len(lifetime_sellers),
                "busiest_hour": (None if busiest_hour is None
                                 else busiest_hour["hour"]),
                "busiest_weekday": (None if busiest_weekday is None
                                    else busiest_weekday["weekday"]),
                "disclaimer": self.disclaimer,
                "hours": hour_rows,
                "weekdays": weekday_rows,
                "cells": cell_rows}

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

    def api_category_history(self, listing_id):
        """Category history surface (pre-registered AC-AMCG5 in the
        R2147 explore-queue row BEFORE this code existed): the
        declaration made at publish time plus every append-only
        revision in order, the CURRENT effective bucket and the
        revision count, so a seller and an operator can both read
        how a listing moved between buckets. Per-listing isolation;
        a retired listing's history stays readable. Pure read."""
        with self._lock:
            self._require_listing(listing_id)
            base = self._conn.execute(
                "SELECT category FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()
            rows = self._conn.execute(
                "SELECT revision_id, dev_account, previous_category,"
                " category, revised_utc FROM apimarket_category_revisions"
                " WHERE listing_id = ? ORDER BY revision_id",
                (listing_id,)).fetchall()
            eff_cat, count, latest = self._category_state(
                listing_id, base[0])
            stamp = self._delisted_utc(listing_id)
        return {"listing_id": listing_id,
                "base_category": base[0],
                "category": eff_cat,
                "revision_count": count,
                "latest_revision_utc": latest,
                "delisted": stamp is not None,
                "delisted_utc": stamp,
                "disclaimer": self.disclaimer,
                "revisions": [{"revision_id": int(r[0]),
                               "dev_account": r[1],
                               "previous_category": r[2],
                               "category": r[3],
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

    _WATCH_BUDGET_BUCKETS = ("purchased", "delisted", "sold_out",
                             "buyable")

    def api_watch_budget(self, buyer_id):
        """Buyer-side watchlist budget face (AC-WBG1..AC-WBG8,
        criteria pre-registered in the R2178 explore-queue seed row
        BEFORE this code existed).

        api_watchlist answers which rows a resident is watching and
        api_watch_alerts answers what happened to them; neither
        answered the question every buyer actually asks before a
        purchase decision - "what would it cost me to take the whole
        watchlist". This face rolls the live watches into a budget
        reading.

        One bucket per live watch row in a pinned precedence
        (AC-WBG2): purchased first (already bought, so no potential
        spend), then delisted, then sold_out, then buyable - a
        delisted row never double-reports as sold out. The four
        bucket counts sum to watch_count (partition conservation).

        Spend authority is the buyable bucket only: the total is the
        sum of those rows' current asking prices (AC-WBG3), min/max
        are the extremes of that same bucket with a listing_id
        tie-break, and avg is the total over buyable_count, which is
        None rather than a fabricated zero when the bucket is empty.

        savings_from_drops sums max(0, price_at_watch - current) over
        the buyable rows only, so a rise elsewhere never nets a
        genuine drop down (AC-WBG4); dropped_count is the number of
        buyable rows whose price fell. A row in another bucket still
        reports its own saved figure but contributes nothing to the
        envelope.

        Rows are a total order on (current_price, listing_id). The
        account shape gate is prefix-only and runs before any read; a
        prefix-valid account with no watches gets an honest empty
        envelope. Pure read: zero row mutations, zero token
        movement."""
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
            counts = dict((b, 0) for b in self._WATCH_BUDGET_BUCKETS)
            for r in rows:
                listing_id = int(r[1])
                base_price = int(r[5])
                owned = self._conn.execute(
                    "SELECT 1 FROM apimarket_purchases WHERE buyer_id = ?"
                    " AND listing_id = ?",
                    (buyer_id, listing_id)).fetchone()
                stamp = self._delisted_utc(listing_id)
                _supply, _sold, _remaining, sold_out = \
                    self._supply_state(listing_id)
                current = self._current_price(listing_id, base_price)
                at_watch = self._price_at_instant(
                    listing_id, base_price, r[6])
                if owned is not None:
                    bucket = "purchased"
                elif stamp is not None:
                    bucket = "delisted"
                elif sold_out:
                    bucket = "sold_out"
                else:
                    bucket = "buyable"
                counts[bucket] += 1
                out.append({"watch_id": int(r[0]),
                            "listing_id": listing_id,
                            "listing_key": r[2], "title": r[3],
                            "dev_account": r[4], "bucket": bucket,
                            "current_price": current,
                            "price_at_watch": at_watch,
                            "saved": max(0, at_watch - current),
                            "watched_utc": r[6]})
        out.sort(key=lambda w: (w["current_price"], w["listing_id"]))
        buyable = [w for w in out if w["bucket"] == "buyable"]
        total = sum(w["current_price"] for w in buyable)
        dropped = [w for w in buyable if w["saved"] > 0]
        return {"buyer_id": buyer_id, "watch_count": len(out),
                "buyable_count": counts["buyable"],
                "purchased_count": counts["purchased"],
                "delisted_count": counts["delisted"],
                "sold_out_count": counts["sold_out"],
                "total_potential_spend": total,
                "avg_potential_price": (
                    None if not buyable else total / float(len(buyable))),
                "min_potential_price": (
                    None if not buyable else buyable[0]["current_price"]),
                "max_potential_price": (
                    None if not buyable else buyable[-1]["current_price"]),
                "savings_from_drops": sum(w["saved"] for w in dropped),
                "dropped_count": len(dropped),
                "disclaimer": self.disclaimer, "watches": out}

    def api_listing_demand(self, dev_account):
        """Seller-side demand read face (pre-registered
        AC-AMDM1..AC-AMDM8 in the R2112 explore-queue claim row
        BEFORE this code existed): the demand signal the seller
        never had.

        The watch surface is buyer-side only - api_watchlist takes a
        buyer_id, and api_view / dev_profile / api_supply carry no
        watch count - so a seller could not answer "how many
        residents are watching this listing, and did watching turn
        into a sale". That is the first-hand signal for pricing and
        restocking decisions, and the gap every listing page shows
        before its first purchase.

        Every listing of the seller becomes a row, including a
        listing with zero watchers and a retired one (retirement
        does not erase demand). watcher_count counts LIVE watches
        only: a watch row with no append-only unwatch row. The
        conversion law is net, matching the scarcity seam - a watch
        converts when that buyer holds a purchase of this listing
        that has not been refunded - so a refund returns the buyer
        to pending rather than leaving a permanent fake conversion.
        derived fields: title through the one effective-metadata seam
        and current_price through the one current-price seam.

        The account shape gate is prefix-only (the truthful
        R2077/R2078 finding) and runs before any read; a prefix-valid
        account with no listings gets an honest empty envelope. Rows
        are a total order on (-watcher_count, listing_id) so the
        hottest shelf is always first and ties are stable. Pure read:
        zero row mutations and zero token movement. The envelope
        carries the resident non-advisory disclaimer."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            listings = self._conn.execute(
                "SELECT listing_id, listing_key, title, description,"
                " token_price FROM apimarket_listings"
                " WHERE dev_account = ? ORDER BY listing_id",
                (dev_account,)).fetchall()
            rows = []
            for r in listings:
                listing_id = int(r[0])
                demand = self._conn.execute(
                    "SELECT COUNT(*),"
                    " COALESCE(SUM(CASE WHEN EXISTS (SELECT 1"
                    " FROM apimarket_purchases p"
                    " WHERE p.listing_id = w.listing_id"
                    " AND p.buyer_id = w.buyer_id"
                    " AND NOT EXISTS (SELECT 1 FROM"
                    " apimarket_refunds f WHERE f.purchase_id ="
                    " p.purchase_id)) THEN 1 ELSE 0 END), 0),"
                    " MIN(w.watched_utc), MAX(w.watched_utc)"
                    " FROM apimarket_watchlist w"
                    " WHERE w.listing_id = ?"
                    " AND NOT EXISTS (SELECT 1 FROM"
                    " apimarket_unwatchings u"
                    " WHERE u.watch_id = w.watch_id)",
                    (listing_id,)).fetchone()
                watchers = int(demand[0])
                converted = int(demand[1])
                delisted, delisted_utc = self._cycle_state(listing_id)[1:]
                title = self._metadata_state(listing_id, r[2], r[3])[0]
                rows.append({
                    "listing_id": listing_id,
                    "listing_key": r[1],
                    "title": title,
                    "delisted": delisted,
                    "delisted_utc": delisted_utc,
                    "current_price": self._current_price(
                        listing_id, r[4]),
                    "watcher_count": watchers,
                    "converted_count": converted,
                    "pending_count": watchers - converted,
                    "oldest_watch_utc": demand[2],
                    "newest_watch_utc": demand[3]})
            rows.sort(key=lambda x: (-x["watcher_count"],
                                     x["listing_id"]))
        return {"dev_account": dev_account,
                "listing_count": len(rows),
                "total_watchers": sum(x["watcher_count"] for x in rows),
                "converted_count": sum(x["converted_count"]
                                       for x in rows),
                "pending_count": sum(x["pending_count"] for x in rows),
                "disclaimer": self.disclaimer,
                "rows": rows}

    def api_watch_conversion(self, dev_account=None,
                             include_uncategorized=True):
        """Watch-to-purchase conversion funnel (criteria AC-WCV1..
        AC-WCV8 pre-registered in the R2149 explore seed claimed in
        R2162, criteria landed in that claim row BEFORE this code
        existed).

        api_listing_demand (R2112) counts watchers and converts per
        listing, but it answers counts only: no conversion RATE, no
        latency, no market-wide or seller-wide aggregate - and its
        conversion predicate asks only whether the buyer holds an
        unrefunded purchase, ignoring ORDER, so a purchase that
        happened BEFORE the watch is counted as a conversion and
        manufactures a fake funnel forever.

        This face pins the directional law. A live watch (a watch
        row with no append-only unwatch row, the same authority as
        api_listing_demand) resolves to exactly one state:

          - converted: the buyer's unrefunded purchase is stamped at
            or after the watch stamp (equal stamps convert with zero
            seconds);
          - pre_owned: the unrefunded purchase predates the watch (or
            the buyer already owned it), which can never convert and
            is therefore excluded from the funnel denominator;
          - pending: no purchase yet, or the purchase was refunded
            (the net law: a refund returns the buyer to pending).

        Latency is derived ONLY from the two stored stamps - never a
        wall clock - so it is an integer and cannot be negative by
        construction. avg is pooled over every converted watch (not
        the mean of the per-category means) and the median is the
        middle value, or the midpoint for an even count; all four
        latency fields are None when nothing converted.

        Rows take the WATCH side: a category holding no watched
        listing never appears even when the market lists there, the
        order is category ascending with the honest uncategorized
        bucket last, and the six counters add up to the envelope.
        Conversion RATE is deliberately not additive: the envelope
        rate is the pooled rate, not the mean of the row rates.

        Scope: no dev_account = the operator's market-wide view, a
        dev_account narrows to that seller's listings with strict
        isolation. Gates run before any read: the usr: prefix
        account shape and the bool-only include_uncategorized
        (fail-closed E_AM_BAD_ACCOUNT / E_AM_BAD_ARGS). Retirement
        neither clears a watch nor a conversion. Pure read: zero row
        mutations, zero token movement, and the envelope carries the
        resident non-advisory disclaimer."""

        def _seconds(earlier, later):
            fmt = "%Y-%m-%dT%H:%M:%SZ"
            start = datetime.datetime.strptime(str(earlier), fmt)
            end = datetime.datetime.strptime(str(later), fmt)
            return int((end - start).total_seconds())

        if dev_account is not None:
            if not str(dev_account or "").startswith("usr:"):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        if not isinstance(include_uncategorized, bool):
            raise ApiMarketError(E_AM_BAD_ARGS,
                                 "include_uncategorized must be a bool")
        sql = ("SELECT w.watch_id, w.listing_id, w.watched_utc,"
               " p.purchased_utc,"
               " (SELECT 1 FROM apimarket_refunds f"
               " WHERE f.purchase_id = p.purchase_id)"
               " FROM apimarket_watchlist w"
               " JOIN apimarket_listings l"
               " ON l.listing_id = w.listing_id"
               " LEFT JOIN apimarket_purchases p"
               " ON p.listing_id = w.listing_id"
               " AND p.buyer_id = w.buyer_id"
               " WHERE NOT EXISTS (SELECT 1 FROM apimarket_unwatchings u"
               " WHERE u.watch_id = w.watch_id)")
        args = ()
        if dev_account is not None:
            sql += " AND l.dev_account = ?"
            args = (str(dev_account),)
        sql += " ORDER BY w.watch_id"
        with self._lock:
            raw = self._conn.execute(sql, args).fetchall()
            watches = []
            for r in raw:
                category = self._effective_category(int(r[1]))
                if category is None and not include_uncategorized:
                    continue
                purchased = r[3]
                refunded = r[4] is not None
                if purchased is None or refunded:
                    state, seconds = "pending", None
                else:
                    delta = _seconds(r[2], purchased)
                    if delta < 0:
                        state, seconds = "pre_owned", None
                    else:
                        state, seconds = "converted", delta
                watches.append({"category": category, "state": state,
                                "seconds": seconds,
                                "watched_utc": r[2]})

        def _block(items):
            total = len(items)
            pre_owned = sum(1 for w in items
                            if w["state"] == "pre_owned")
            converted = [w["seconds"] for w in items
                         if w["state"] == "converted"]
            funnel = total - pre_owned
            pending = [w["watched_utc"] for w in items
                       if w["state"] == "pending"]
            if converted:
                ordered = sorted(converted)
                mid = len(ordered) // 2
                median = (float(ordered[mid]) if len(ordered) % 2
                          else (ordered[mid - 1] + ordered[mid]) / 2.0)
                avg = float(sum(ordered)) / len(ordered)
            else:
                ordered = []
                median = None
                avg = None
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
                "fastest_convert_seconds": (ordered[0] if ordered
                                            else None),
                "slowest_convert_seconds": (ordered[-1] if ordered
                                            else None),
                "oldest_pending_watch_utc": (min(pending) if pending
                                            else None)}

        envelope = _block(watches)
        rows = []
        categories = sorted(set(w["category"] for w in watches),
                            key=lambda c: (c is None, c))
        for category in categories:
            row = {"category": category}
            row.update(_block([w for w in watches
                               if w["category"] == category]))
            rows.append(row)
        out = {"dev_account": dev_account,
               "include_uncategorized": include_uncategorized,
               "disclaimer": self.disclaimer}
        out.update(envelope)
        out["categories"] = rows
        return out

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
                   limit=None, offset=None, sort=None, category=None,
                   in_stock=None):
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
        zero token movement.

        Availability axis (pre-registered AC-AMAV1..AC-AMAV8 in the
        R2142 explore-queue row BEFORE this code existed): the face
        could filter by category, order by five modes and page, but
        nothing answered "show me only what I can still buy" - a
        sold-out listing and a buyable one were byte-identical here,
        so a buyer had to read every row and call api_supply per
        listing. Optional in_stock (bool only) keeps the buyable
        rows (True) or the sold-out rows (False, the seller's
        restock queue) through the one scarcity seam
        (_supply_state), so a purchase, a refund and a restock move
        a listing across the filter in exactly the step they move
        api_supply.sold_out. The gate runs after the category gate
        and before the paging/sort gates, fail-closed BEFORE any
        read. Backward-compatibility law: when in_stock is None the
        criteria echo carries NO in_stock key and the envelope and
        rows stay byte-identical to the pre-change contract; row
        keys never change."""
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
        # AC-AMCT3/AC-AMCT6: the category shape gate runs after the
        # include_delisted gate and before the paging/sort gates,
        # always BEFORE any read, so a refused taxonomy touches no
        # table. Matching is exact on the trimmed declaration (no
        # case folding - documented honestly in the queue row).
        if category is None:
            cat = None
        else:
            if not isinstance(category, str):
                raise ApiMarketError(E_AM_BAD_ARGS,
                                     "bad category: %r" % (category,))
            cat = category.strip()
            if not cat:
                raise ApiMarketError(E_AM_BAD_ARGS, "category blank")
        # AC-AMAV2: the availability gate is a bool-only shape gate
        # that runs after the category gate and BEFORE the paging
        # and sort gates, always before any read.
        if in_stock is None:
            stock = None
        else:
            if not isinstance(in_stock, bool):
                raise ApiMarketError(E_AM_BAD_ARGS,
                                     "bad in_stock: %r" % (in_stock,))
            stock = in_stock
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
                " description, token_price, ai_label, listed_utc,"
                " category FROM"
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
                # AC-AMCG6: the category filter and the row value
                # both read the one effective-bucket seam, so a
                # revision moves discovery in the same step it moves
                # the catalog and the demand face.
                eff_cat = self._category_state(listing_id, r[8])[0]
                if cat is not None and (eff_cat or "") != cat:
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
                # AC-AMAV3: availability is read through the one
                # scarcity seam, so the filter and api_supply always
                # agree on which rows are buyable.
                if stock is not None:
                    _eff, _sold, _rem, sold_out = \
                        self._supply_state(listing_id)
                    buyable = not sold_out
                    if buyable != stock:
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
                            "category": eff_cat,
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
        # AC-AMCT2: the category key is echoed only when a filter is
        # given, so a caller that never filters keeps the pre-change
        # criteria contract byte for byte.
        if cat is not None:
            criteria["category"] = cat
        # AC-AMAV1: the availability key is echoed only when the
        # filter is given, so a caller that never filters keeps the
        # pre-change criteria contract byte for byte.
        if stock is not None:
            criteria["in_stock"] = stock
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

    def api_categories(self):
        """Category directory (pre-registered AC-AMCT1..AC-AMCT8 in
        the R2132 explore-queue row BEFORE this code existed): the
        marketplace had no notion of a product category, so a buyer
        could only guess keywords and an operator could not answer
        "what is this market made of". This face answers it: one row
        per declared category with partition counts and the live
        price band, plus an honest uncategorized bucket so the
        conservation law holds on every world (including the ones
        written before the axis existed). Prices are the CURRENT
        asking price (a repricing moves the band in the same step
        it moves api_search); retirement moves the partition
        counters only, and a re-listed listing returns to live.
        Rows are ordered by category ascending; the bucket is exact
        on the stored declaration (trimmed at publish time, no case
        folding). Pure read: zero row mutations, zero token
        movement."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT listing_id, token_price, category FROM"
                " apimarket_listings ORDER BY listing_id").fetchall()
            groups = {}
            uncategorized = 0
            for r in rows:
                lid = int(r[0])
                # AC-AMCG6: one effective-bucket seam for every
                # category reader, so the directory re-buckets a
                # listing the moment its category is revised.
                cat = self._category_state(lid, r[2])[0]
                if cat is None:
                    uncategorized += 1
                    continue
                g = groups.get(cat)
                if g is None:
                    g = {"category": cat, "listing_count": 0,
                         "live_listing_count": 0,
                         "retired_listing_count": 0,
                         "_prices": []}
                    groups[cat] = g
                g["listing_count"] += 1
                if self._delisted_utc(lid) is None:
                    g["live_listing_count"] += 1
                    g["_prices"].append(
                        self._current_price(lid, int(r[1])))
                else:
                    g["retired_listing_count"] += 1
            out = []
            for cat in sorted(groups):
                g = groups[cat]
                prices = g.pop("_prices")
                g["min_live_price"] = min(prices) if prices else None
                g["max_live_price"] = max(prices) if prices else None
                out.append(g)
        return {"category_count": len(out),
                "listing_count": len(rows),
                "uncategorized_count": uncategorized,
                "disclaimer": self.disclaimer,
                "categories": out}

    def api_category_demand(self, include_uncategorized=True):
        """Per-category demand face (criteria AC-AMCD1..AC-AMCD8
        pre-registered in the R2141 explore-queue row BEFORE this
        code existed).

        api_categories answers the SUPPLY side of one category (how
        many listings, at what asking price); nothing answered which
        categories actually SELL. api_market_stats aggregates the whole
        market, api_listing_demand one listing, dev_sales_board one
        seller and api_market_months one month, so a seller choosing
        what to build and an operator setting prices had no category
        reading at all.

        Row authority is the listing side: every declared category
        holding at least one listing row gets exactly one row (a
        listed-but-unsold category stays visible with honest zero trade
        columns), plus the honest uncategorized bucket for rows written
        before the axis existed (category None). Order is category
        ascending with the bucket last.

        Laws pinned by the suite: partition conservation per row and
        globally; trade conservation per row (gross == net_gross +
        refunded, net_purchase == purchase - refund) and cross-face
        identity with api_market_stats on the default call; buyer_count
        is a distinct count WITHIN each category (the same buyer
        legitimately counts once per category) while the envelope
        buyer_count is the distinct count over the included rows;
        retirement and re-listing only move the partition counters
        while every historical aggregate stays byte-frozen; a refund
        lowers the net side of the refunded listing's category only and
        leaves purchase_count and buyer_count intact; avg_net_price is
        net_gross_tokens / net_purchase_count, None when nothing
        settled.

        Gate: include_uncategorized must be a bool and is checked before
        any read (fail-closed E_AM_BAD_ARGS). Pure read: zero row
        mutations, zero token movement, and the envelope carries the
        resident non-advisory disclaimer."""
        if not isinstance(include_uncategorized, bool):
            raise ApiMarketError(E_AM_BAD_ARGS,
                                 str(include_uncategorized))
        with self._lock:
            listings = self._conn.execute(
                "SELECT listing_id, category FROM apimarket_listings"
                " ORDER BY listing_id").fetchall()
            purchases = self._conn.execute(
                "SELECT listing_id, buyer_id, price_paid"
                " FROM apimarket_purchases").fetchall()
            refunds = self._conn.execute(
                "SELECT p.listing_id, f.amount"
                " FROM apimarket_refunds f"
                " JOIN apimarket_purchases p"
                " ON p.purchase_id = f.purchase_id").fetchall()
            groups = {}
            # AC-AMCG6: demand buckets read the one effective-bucket
            # seam, so trade aggregates follow a revised category in
            # the same step as the catalog and discovery faces.
            owner = {int(r[0]): self._category_state(int(r[0]), r[1])[0]
                     for r in listings}
            for r in listings:
                cat = owner[int(r[0])]
                g = groups.get(cat)
                if g is None:
                    g = {"listing_count": 0, "live": 0, "retired": 0,
                         "purchase_count": 0, "refund_count": 0,
                         "gross": 0, "refunded": 0, "buyers": set()}
                    groups[cat] = g
                g["listing_count"] += 1
                if self._delisted_utc(int(r[0])) is None:
                    g["live"] += 1
                else:
                    g["retired"] += 1
            for r in purchases:
                g = groups.get(owner.get(int(r[0])))
                if g is None:
                    continue
                g["purchase_count"] += 1
                g["gross"] += int(r[2])
                g["buyers"].add(r[1])
            for r in refunds:
                g = groups.get(owner.get(int(r[0])))
                if g is None:
                    continue
                g["refund_count"] += 1
                g["refunded"] += int(r[1])
        order = sorted([c for c in groups if c is not None])
        if None in groups:
            order.append(None)
        rows = []
        buyers = set()
        for cat in order:
            if cat is None and not include_uncategorized:
                continue
            g = groups[cat]
            net_purchase = g["purchase_count"] - g["refund_count"]
            net_gross = g["gross"] - g["refunded"]
            rows.append({
                "category": cat,
                "listing_count": g["listing_count"],
                "live_listing_count": g["live"],
                "retired_listing_count": g["retired"],
                "purchase_count": g["purchase_count"],
                "buyer_count": len(g["buyers"]),
                "refund_count": g["refund_count"],
                "net_purchase_count": net_purchase,
                "gross_tokens": g["gross"],
                "refunded_tokens": g["refunded"],
                "net_gross_tokens": net_gross,
                "avg_net_price": (float(net_gross) / net_purchase
                                  if net_purchase else None)})
            buyers |= g["buyers"]
        return {"category_count": len(rows),
                "listing_count": sum(r["listing_count"] for r in rows),
                "live_listing_count": sum(
                    r["live_listing_count"] for r in rows),
                "retired_listing_count": sum(
                    r["retired_listing_count"] for r in rows),
                "purchase_count": sum(
                    r["purchase_count"] for r in rows),
                "buyer_count": len(buyers),
                "refund_count": sum(r["refund_count"] for r in rows),
                "net_purchase_count": sum(
                    r["net_purchase_count"] for r in rows),
                "gross_tokens": sum(r["gross_tokens"] for r in rows),
                "refunded_tokens": sum(
                    r["refunded_tokens"] for r in rows),
                "net_gross_tokens": sum(
                    r["net_gross_tokens"] for r in rows),
                "categories": rows,
                "disclaimer": self.disclaimer}

    def api_buyer_category_spend(self, buyer_id,
                                 include_uncategorized=True):
        """Buyer-side spend broken down by category (criteria
        AC-BCS1..AC-BCS8 pre-registered in the R2149 explore-queue row
        BEFORE this code existed).

        The buyer side had a time axis (api_buyer_months), a lifetime
        aggregate (api_buyer_profile), a row face (api_library) and two
        statements (api_buyer_ledger, api_refund_register), and the
        market side had a per-category demand face (api_category_demand)
        - but nobody answered the resident's own question "where did my
        money go": which categories I actually buy, how much of it came
        back, and which seller took the biggest share. A budget review,
        a category cap or a spending comparison all needed the caller to
        pull the library, resolve each listing's category and rebucket
        by hand.

        Row authority here is the PURCHASE side, not the listing side: a
        buyer sees exactly the categories it bought in, so a category
        with listings and zero purchases of this buyer stays absent
        (unlike api_category_demand, which is listing-side). The honest
        uncategorized bucket is last; order is category ascending.

        Laws pinned by the suite: strict buyer isolation; buckets come
        from the one effective-category seam, so revise_category moves
        the buyer's spend bucket in the same step as the catalog and
        demand faces (cross-face identity with api_category_demand on
        the purchase side); trade conservation per row (gross_spent ==
        net_spent + refunded_tokens, net_purchase_count ==
        purchase_count - refund_count, dev_paid + platform_paid ==
        gross_spent); the envelope totals equal api_buyer_months'
        lifetime cash-basis figures on the default call; listing_count is
        purchase-derived (a refund never removes the listing from the
        count) while seller_count is a distinct count within the row and
        over the envelope; avg_net_price is net_spent / net_purchase,
        None when nothing settled. Gate: account shape then the bool
        switch, both before any read (fail-closed E_AM_BAD_ACCOUNT /
        E_AM_BAD_ARGS). Pure read: zero row mutations, zero token
        movement."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        if not isinstance(include_uncategorized, bool):
            raise ApiMarketError(E_AM_BAD_ARGS,
                                 str(include_uncategorized))
        buyer = str(buyer_id)
        with self._lock:
            listings = self._conn.execute(
                "SELECT listing_id, category, dev_account"
                " FROM apimarket_listings").fetchall()
            purchases = self._conn.execute(
                "SELECT p.purchase_id, p.listing_id, p.price_paid,"
                " p.dev_share, p.platform_share"
                " FROM apimarket_purchases p WHERE p.buyer_id = ?",
                (buyer,)).fetchall()
            refunds = self._conn.execute(
                "SELECT f.purchase_id, f.amount, f.dev_share,"
                " f.platform_share FROM apimarket_refunds f"
                " JOIN apimarket_purchases p"
                " ON p.purchase_id = f.purchase_id"
                " WHERE p.buyer_id = ?", (buyer,)).fetchall()
            cat_of = {}
            seller_of = {}
            for r in listings:
                lid = int(r[0])
                cat_of[lid] = self._category_state(lid, r[1])[0]
                seller_of[lid] = r[2]
            groups = {}

            def row_for(cat):
                g = groups.get(cat)
                if g is None:
                    g = {"purchase_count": 0, "refund_count": 0,
                         "gross": 0, "refunded": 0, "dev_paid": 0,
                         "platform_paid": 0, "refund_dev": 0,
                         "refund_platform": 0, "listings": set(),
                         "sellers": set()}
                    groups[cat] = g
                return g

            bought = {}
            for pid, lid, price, dshare, pshare in purchases:
                lid = int(lid)
                bought[int(pid)] = lid
                g = row_for(cat_of.get(lid))
                g["purchase_count"] += 1
                g["gross"] += int(price)
                g["dev_paid"] += int(dshare)
                g["platform_paid"] += int(pshare)
                g["listings"].add(lid)
                if seller_of.get(lid) is not None:
                    g["sellers"].add(seller_of[lid])
            for pid, amount, dshare, pshare in refunds:
                lid = bought.get(int(pid))
                if lid is None:
                    continue
                g = row_for(cat_of.get(lid))
                g["refund_count"] += 1
                g["refunded"] += int(amount)
                g["refund_dev"] += int(dshare)
                g["refund_platform"] += int(pshare)
        order = sorted([c for c in groups if c is not None])
        if None in groups:
            order.append(None)
        rows = []
        listings_total = set()
        sellers_total = set()
        for cat in order:
            if cat is None and not include_uncategorized:
                continue
            g = groups[cat]
            net_purchase = g["purchase_count"] - g["refund_count"]
            net_spent = g["gross"] - g["refunded"]
            rows.append({
                "category": cat,
                "purchase_count": g["purchase_count"],
                "refund_count": g["refund_count"],
                "net_purchase_count": net_purchase,
                "gross_spent": g["gross"],
                "refunded_tokens": g["refunded"],
                "net_spent": net_spent,
                "dev_paid": g["dev_paid"],
                "platform_paid": g["platform_paid"],
                "dev_paid_net": g["dev_paid"] - g["refund_dev"],
                "platform_paid_net": (g["platform_paid"]
                                      - g["refund_platform"]),
                "listing_count": len(g["listings"]),
                "seller_count": len(g["sellers"]),
                "avg_net_price": (float(net_spent) / net_purchase
                                  if net_purchase else None)})
            listings_total |= g["listings"]
            sellers_total |= g["sellers"]
        return {"buyer_id": buyer,
                "category_count": len(rows),
                "purchase_count": sum(
                    r["purchase_count"] for r in rows),
                "refund_count": sum(r["refund_count"] for r in rows),
                "net_purchase_count": sum(
                    r["net_purchase_count"] for r in rows),
                "gross_spent": sum(r["gross_spent"] for r in rows),
                "refunded_tokens": sum(
                    r["refunded_tokens"] for r in rows),
                "net_spent": sum(r["net_spent"] for r in rows),
                "dev_paid_net": sum(r["dev_paid_net"] for r in rows),
                "platform_paid_net": sum(
                    r["platform_paid_net"] for r in rows),
                "listing_count": len(listings_total),
                "seller_count": len(sellers_total),
                "categories": rows,
                "disclaimer": self.disclaimer}

    def api_buyer_seller_spend(self, buyer_id):
        """Buyer-side spend broken down by seller (criteria
        AC-BSS1..AC-BSS8 pre-registered in the R2158 explore-queue row
        BEFORE this code existed).

        The category axis (api_buyer_category_spend) answers "where did
        my money go", but inside one category the seller composition
        stayed unanswered: how many different sellers did this resident
        actually pay, which one took the largest share, and is the
        resident bound to a single counterparty? The face is derived
        from purchases joined to listings - no new table.

        Row authority is the PURCHASE side: a seller this buyer never
        bought from stays absent even when the seller has live stock
        (the mirror of api_category_demand's listing-side authority).
        The order is a TOTAL order (-net_spent, -gross_spent,
        dev_account) so rank is a position in it, never a dense rank.

        Laws pinned by the suite: trade conservation per row
        (gross_spent == net_spent + refunded_tokens, net_purchase_count
        == purchase_count - refund_count, dev_paid + platform_paid ==
        gross_spent, dev_paid_net + platform_paid_net == net_spent);
        envelope totals are the row sums and its six cash figures equal
        api_buyer_category_spend's default call on the same world;
        net_share is net_spent / total net spend and becomes None for
        every row when the total is not positive; a refund lowers the
        net side only and never removes a purchase, a listing or the
        seller from the board; category_count is a distinct count over
        the one effective-category seam, so revise_category moves it in
        the same step as the catalog and category faces. Gate: account
        shape before any read (fail-closed E_AM_BAD_ACCOUNT). Pure read:
        zero row mutations, zero token movement."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        buyer = str(buyer_id)
        with self._lock:
            listings = self._conn.execute(
                "SELECT listing_id, category, dev_account"
                " FROM apimarket_listings").fetchall()
            purchases = self._conn.execute(
                "SELECT p.purchase_id, p.listing_id, p.price_paid,"
                " p.dev_share, p.platform_share"
                " FROM apimarket_purchases p WHERE p.buyer_id = ?",
                (buyer,)).fetchall()
            refunds = self._conn.execute(
                "SELECT f.purchase_id, f.amount, f.dev_share,"
                " f.platform_share FROM apimarket_refunds f"
                " JOIN apimarket_purchases p"
                " ON p.purchase_id = f.purchase_id"
                " WHERE p.buyer_id = ?", (buyer,)).fetchall()
            cat_of = {}
            seller_of = {}
            for r in listings:
                lid = int(r[0])
                cat_of[lid] = self._category_state(lid, r[1])[0]
                seller_of[lid] = r[2]
            groups = {}

            def row_for(dev):
                g = groups.get(dev)
                if g is None:
                    g = {"purchase_count": 0, "refund_count": 0,
                         "gross": 0, "refunded": 0, "dev_paid": 0,
                         "platform_paid": 0, "refund_dev": 0,
                         "refund_platform": 0, "listings": set(),
                         "categories": set()}
                    groups[dev] = g
                return g

            bought = {}
            for pid, lid, price, dshare, pshare in purchases:
                lid = int(lid)
                bought[int(pid)] = lid
                dev = seller_of.get(lid)
                g = row_for(dev)
                g["purchase_count"] += 1
                g["gross"] += int(price)
                g["dev_paid"] += int(dshare)
                g["platform_paid"] += int(pshare)
                g["listings"].add(lid)
                g["categories"].add(cat_of.get(lid))
            for pid, amount, dshare, pshare in refunds:
                lid = bought.get(int(pid))
                if lid is None:
                    continue
                g = row_for(seller_of.get(lid))
                g["refund_count"] += 1
                g["refunded"] += int(amount)
                g["refund_dev"] += int(dshare)
                g["refund_platform"] += int(pshare)
        net_by_dev = {}
        for dev, g in groups.items():
            net_by_dev[dev] = g["gross"] - g["refunded"]
        order = sorted(net_by_dev,
                       key=lambda d: (-net_by_dev[d],
                                      -groups[d]["gross"], str(d)))
        total_net = sum(net_by_dev.values())
        rows = []
        listings_total = set()
        for idx, dev in enumerate(order, 1):
            g = groups[dev]
            net_purchase = g["purchase_count"] - g["refund_count"]
            net_spent = net_by_dev[dev]
            rows.append({
                "dev_account": dev,
                "rank": idx,
                "purchase_count": g["purchase_count"],
                "refund_count": g["refund_count"],
                "net_purchase_count": net_purchase,
                "gross_spent": g["gross"],
                "refunded_tokens": g["refunded"],
                "net_spent": net_spent,
                "dev_paid": g["dev_paid"],
                "platform_paid": g["platform_paid"],
                "dev_paid_net": g["dev_paid"] - g["refund_dev"],
                "platform_paid_net": (g["platform_paid"]
                                      - g["refund_platform"]),
                "listing_count": len(g["listings"]),
                "category_count": len(g["categories"]),
                "avg_net_spend": (float(net_spent) / net_purchase
                                  if net_purchase else None),
                "net_share": (float(net_spent) / total_net
                              if total_net > 0 else None)})
            listings_total |= g["listings"]
        return {"buyer_id": buyer,
                "seller_count": len(rows),
                "purchase_count": sum(
                    r["purchase_count"] for r in rows),
                "refund_count": sum(r["refund_count"] for r in rows),
                "net_purchase_count": sum(
                    r["net_purchase_count"] for r in rows),
                "gross_spent": sum(r["gross_spent"] for r in rows),
                "refunded_tokens": sum(
                    r["refunded_tokens"] for r in rows),
                "net_spent": sum(r["net_spent"] for r in rows),
                "dev_paid": sum(r["dev_paid"] for r in rows),
                "platform_paid": sum(
                    r["platform_paid"] for r in rows),
                "dev_paid_net": sum(r["dev_paid_net"] for r in rows),
                "platform_paid_net": sum(
                    r["platform_paid_net"] for r in rows),
                "listing_count": len(listings_total),
                "sellers": rows,
                "disclaimer": self.disclaimer}

    def api_repeat_purchase(self, dev_account=None):
        """Repeat-purchase structure of one seller, or of the whole
        market (criteria AC-RPT1..AC-RPT8 pre-registered in the R2161
        explore-queue row BEFORE this code existed).

        Every existing read face stops short of the retention
        question. The library gives rows, the buyer profile gives
        lifetime aggregates, the seller profile gives gross totals and
        the category demand face gives volumes - none of them answers
        "does the same resident come back and buy a second time". This
        face counts buyers and their purchases inside one scope (a
        seller, or the whole market when dev_account is None) and
        derives the repeat structure from those counts.

        Laws pinned by the suite: the counting authority is NET
        purchases - a refunded purchase counts neither in the numerator
        nor in the denominator, so a buyer whose only purchase was
        refunded disappears entirely instead of being misread as a
        one-time buyer; a buyer is a repeat buyer when she holds two or
        more net purchases inside the scope; repeat_purchase_count is
        purchase_count minus buyer_count (every purchase beyond a
        buyer's first); repeat_rate is the share of buyers who came
        back and is None when there are no buyers; category rows ride
        the one effective-category seam, are ordered with the honest
        uncategorized bucket last, and take PURCHASE-side authority
        (a category with stock but zero purchases stays absent). The
        scope laws differ honestly: one purchase from each of two
        sellers is a repeat for the market and not a repeat for either
        seller, and both readings are correct. Pure read: zero row
        mutations, zero token movement."""
        if dev_account is not None:
            if not str(dev_account).startswith("usr:"):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        scope = None if dev_account is None else str(dev_account)
        with self._lock:
            listings = self._conn.execute(
                "SELECT listing_id, category, dev_account"
                " FROM apimarket_listings").fetchall()
            purchases = self._conn.execute(
                "SELECT purchase_id, listing_id, buyer_id"
                " FROM apimarket_purchases").fetchall()
            refunded = set(int(r[0]) for r in self._conn.execute(
                "SELECT purchase_id FROM apimarket_refunds"))
            cat_of = {}
            seller_of = {}
            for r in listings:
                lid = int(r[0])
                cat_of[lid] = self._category_state(lid, r[1])[0]
                seller_of[lid] = r[2]
            per_buyer = {}
            per_cat = {}
            for pid, lid, buyer in purchases:
                if int(pid) in refunded:
                    continue
                lid = int(lid)
                if scope is not None and seller_of.get(lid) != scope:
                    continue
                per_buyer[buyer] = per_buyer.get(buyer, 0) + 1
                cat = cat_of.get(lid)
                bucket = per_cat.get(cat)
                if bucket is None:
                    bucket = {}
                    per_cat[cat] = bucket
                bucket[buyer] = bucket.get(buyer, 0) + 1

        def summarise(counts):
            buyers = len(counts)
            bought = sum(counts.values())
            repeat = sum(1 for n in counts.values() if n >= 2)
            return {"buyer_count": buyers,
                    "repeat_buyer_count": repeat,
                    "one_time_buyer_count": buyers - repeat,
                    "repeat_rate": (float(repeat) / buyers
                                    if buyers else None),
                    "purchase_count": bought,
                    "repeat_purchase_count": bought - buyers,
                    "avg_purchases_per_buyer": (float(bought) / buyers
                                                if buyers else None)}

        top = None
        top_n = 0
        for buyer in sorted(per_buyer):
            n = per_buyer[buyer]
            if n >= 2 and n > top_n:
                top = buyer
                top_n = n
        categories = []
        for cat in sorted(per_cat,
                          key=lambda c: (c is None, c or "")):
            row = {"category": cat}
            row.update(summarise(per_cat[cat]))
            categories.append(row)
        env = {"dev_account": scope}
        env.update(summarise(per_buyer))
        env["max_purchases"] = max(per_buyer.values()) if per_buyer else 0
        env["top_repeat_buyer"] = top
        env["categories"] = categories
        env["disclaimer"] = self.disclaimer
        return env

    def api_category_refund_months(self, include_uncategorized=True):
        """Category-by-month refund timeline (criteria AC-CRM1..AC-CRM8
        pre-registered in the R2149 explore-queue row BEFORE this code
        existed).

        Three faces sit next to the question this one answers and none
        of them answers it: api_category_demand sums a category over
        its whole life, api_market_months sums the whole market per
        month and api_refund_register lists refunds one by one, so
        "is THIS category's refund load abnormal THIS month" - the
        question a seller asks before committing to a line of
        business - had to be rebuilt by hand from three joins.

        Laws pinned by the suite: cash basis - a sale books in the
        UTC month of purchased_utc and a refund books in the UTC month
        of refunded_utc, and a refund never rewrites the month its
        sale landed in, so a refund landing later shows an honestly
        negative net in its own month and the sale month stays
        untouched; refund authority is the refund register joined to
        its purchase, so a refund-only month reports zero trade_count
        next to a positive refund_count instead of inventing a sale;
        category ownership rides the one effective-category seam
        (_category_state), so a revise_category moves both gross and
        refunded in one step and a revert restores byte-identically;
        refund_rate is refunded/gross and is None - never a fake zero
        - when the month or the category settled nothing; months are
        ordered ascending (YYYY-MM compares as a string), categories
        ascending with the honest uncategorized bucket last.

        Gate: include_uncategorized must be a bool and is checked
        before any read (fail-closed E_AM_BAD_ARGS); excluding the
        bucket removes those rows from every figure rather than
        dropping them into a category. Pure read: zero row mutations,
        zero token movement, repeated calls byte-identical."""
        if not isinstance(include_uncategorized, bool):
            raise ApiMarketError(E_AM_BAD_ARGS,
                                 str(include_uncategorized))
        with self._lock:
            listings = self._conn.execute(
                "SELECT listing_id, category"
                " FROM apimarket_listings").fetchall()
            sales = self._conn.execute(
                "SELECT listing_id, price_paid, purchased_utc"
                " FROM apimarket_purchases").fetchall()
            refunds = self._conn.execute(
                "SELECT p.listing_id, f.amount, f.refunded_utc"
                " FROM apimarket_refunds f"
                " JOIN apimarket_purchases p"
                " ON p.purchase_id = f.purchase_id").fetchall()
            owner = {int(r[0]): self._category_state(int(r[0]), r[1])[0]
                     for r in listings}
        cats = {}

        def cat_bucket(cat):
            b = cats.get(cat)
            if b is None:
                b = {"gross": 0, "refund_count": 0, "refunded": 0,
                     "trade_count": 0, "months": {}}
                cats[cat] = b
            return b

        def month_bucket(b, month):
            m = b["months"].get(month)
            if m is None:
                m = {"month": month, "gross": 0, "refund_count": 0,
                     "refunded": 0, "trade_count": 0}
                b["months"][month] = m
            return m

        for listing_id, price, stamp in sales:
            cat = owner.get(int(listing_id))
            if cat is None and not include_uncategorized:
                continue
            b = cat_bucket(cat)
            gross = int(price)
            b["gross"] += gross
            b["trade_count"] += 1
            m = month_bucket(b, str(stamp)[:7])
            m["gross"] += gross
            m["trade_count"] += 1
        for listing_id, amount, stamp in refunds:
            cat = owner.get(int(listing_id))
            if cat is None and not include_uncategorized:
                continue
            b = cat_bucket(cat)
            refunded = int(amount)
            b["refunded"] += refunded
            b["refund_count"] += 1
            m = month_bucket(b, str(stamp)[:7])
            m["refunded"] += refunded
            m["refund_count"] += 1

        def rate(gross, refunded):
            return (float(refunded) / gross) if gross > 0 else None

        rows = []
        for cat in sorted(cats, key=lambda c: (c is None, c or "")):
            b = cats[cat]
            months = []
            for month in sorted(b["months"]):
                m = b["months"][month]
                months.append({
                    "month": month,
                    "gross": m["gross"],
                    "refund_count": m["refund_count"],
                    "refunded": m["refunded"],
                    "net": m["gross"] - m["refunded"],
                    "refund_rate": rate(m["gross"], m["refunded"])})
            rows.append({
                "category": cat,
                "gross": b["gross"],
                "refund_count": b["refund_count"],
                "refunded": b["refunded"],
                "net": b["gross"] - b["refunded"],
                "refund_rate": rate(b["gross"], b["refunded"]),
                "trade_count": b["trade_count"],
                "months": months})

        totals = {}
        for b in cats.values():
            for month, m in b["months"].items():
                t = totals.get(month)
                if t is None:
                    t = {"gross": 0, "refund_count": 0, "refunded": 0,
                         "trade_count": 0}
                    totals[month] = t
                t["gross"] += m["gross"]
                t["refund_count"] += m["refund_count"]
                t["refunded"] += m["refunded"]
                t["trade_count"] += m["trade_count"]
        worst_month = None
        worst_rate = None
        for month in sorted(totals):
            r = rate(totals[month]["gross"], totals[month]["refunded"])
            if r is None:
                continue
            if worst_rate is None or r > worst_rate:
                worst_month = month
                worst_rate = r
        top_month = None
        top_refunded = 0
        for month in sorted(totals):
            if totals[month]["refunded"] > top_refunded:
                top_month = month
                top_refunded = totals[month]["refunded"]
        env = {
            "include_uncategorized": include_uncategorized,
            "category_count": len(rows),
            "month_count": len(totals),
            "trade_count": sum(b["trade_count"] for b in cats.values()),
            "gross": sum(b["gross"] for b in cats.values()),
            "refund_count": sum(b["refund_count"] for b in cats.values()),
            "refunded": sum(b["refunded"] for b in cats.values()),
        }
        env["net"] = env["gross"] - env["refunded"]
        env["refund_rate"] = rate(env["gross"], env["refunded"])
        env["worst_refund_month"] = worst_month
        env["worst_refund_rate"] = worst_rate
        env["top_refund_month"] = top_month
        env["categories"] = rows
        env["disclaimer"] = self.disclaimer
        return env

    def api_listing_position(self, listing_id, limit=None):
        """Competitive standing of one listing inside its own
        category (criteria AC-AMPOS1..AC-AMPOS8 pre-registered in
        the R2144 explore-queue row BEFORE this code existed).

        The catalog face answers what a category is made of and the
        demand face answers whether it sells, but nothing answered
        the seller's own question: "where do I stand against the
        people I am actually competing with". This face ranks one
        listing inside its own category bucket on the three axes a
        buyer weighs - asking price, net sales and effective rating
        - and returns the bucket slice so the rank is auditable
        rather than asserted.

        Laws pinned by the suite: ranks are POSITIONS in a total
        order (never dense ranks), so ties are broken by listing_id
        ascending and two equal prices still get distinct ranks;
        price and rating ride their one seam (_current_price and
        _agg_rating) so a repricing or a rating revision moves the
        rank in the same step it moves every other read face; net
        sales rides the scarcity seam (_supply_full) so a refund
        lowers a rank without touching a listing row; the bucket is
        the stored category declaration exactly, with the
        uncategorized listings forming their own bucket (no cross
        bucket permeation); retired listings stay in their bucket
        and keep their ranks (history is not erased) while the
        live/retired partition is reported; the bucket is ordered
        by (current_price, listing_id) ascending and an optional
        limit keeps the CHEAPEST head while category_size keeps
        reporting the full bucket. Pure read: zero row mutations,
        zero token movement."""
        if (not isinstance(listing_id, int) or isinstance(listing_id, bool)
                or listing_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(listing_id))
        with self._lock:
            self._require_listing(listing_id)
            if limit is not None:
                if (not isinstance(limit, int) or isinstance(limit, bool)
                        or limit < 1):
                    raise ApiMarketError(E_AM_BAD_ARGS, str(limit))
            head = self._conn.execute(
                "SELECT listing_id, dev_account, listing_key, title,"
                " description, token_price, category"
                " FROM apimarket_listings WHERE listing_id = ?",
                (listing_id,)).fetchone()
            # AC-AMCG6: the competitive bucket is the EFFECTIVE
            # bucket, so a revised listing competes in its new
            # category and leaves the old one in the same step.
            category = self._category_state(listing_id, head[6])[0]
            rows = self._conn.execute(
                "SELECT listing_id, dev_account, listing_key,"
                " title, description, token_price, category"
                " FROM apimarket_listings ORDER BY listing_id").fetchall()
            rows = [r for r in rows
                    if self._category_state(int(r[0]), r[6])[0]
                    == category]
            members = []
            for r in rows:
                lid = int(r[0])
                stamp = self._delisted_utc(lid)
                eff_title, _eff_desc, _n_meta, _latest = \
                    self._metadata_state(lid, r[3], r[4])
                n_rate, avg = self._agg_rating(lid)
                members.append({
                    "listing_id": lid,
                    "dev_account": r[1],
                    "listing_key": r[2],
                    "title": eff_title,
                    "current_price": int(self._current_price(
                        lid, int(r[5]))),
                    "net_sales": int(self._supply_full(lid)[3]),
                    "rating_count": n_rate,
                    "rating_avg": avg,
                    "live": stamp is None,
                    "delisted_utc": stamp})
            by_price = sorted(
                members, key=lambda m: (m["current_price"],
                                        m["listing_id"]))
            by_sales = sorted(
                members, key=lambda m: (-m["net_sales"],
                                        m["listing_id"]))
            by_rating = sorted(
                members, key=lambda m: (-m["rating_avg"],
                                        -m["rating_count"],
                                        m["listing_id"]))
            price_rank = {}; sales_rank = {}; rating_rank = {}
            for index, m in enumerate(by_price):
                price_rank[m["listing_id"]] = index + 1
            for index, m in enumerate(by_sales):
                sales_rank[m["listing_id"]] = index + 1
            for index, m in enumerate(by_rating):
                rating_rank[m["listing_id"]] = index + 1
            me = [m for m in members
                  if m["listing_id"] == int(listing_id)][0]
            cheaper = len([m for m in members
                           if m["current_price"] < me["current_price"]])
            pricier = len([m for m in members
                           if m["current_price"] > me["current_price"]])
            prices = [m["current_price"] for m in members]
            rivals = by_price if limit is None else by_price[:limit]
            rivals = [dict(m) for m in rivals]
        return {"listing_id": me["listing_id"],
                "listing_key": head[2],
                "title": me["title"],
                "dev_account": head[1],
                "category": category,
                "live": me["live"],
                "delisted_utc": me["delisted_utc"],
                "current_price": me["current_price"],
                "net_sales": me["net_sales"],
                "rating_count": me["rating_count"],
                "rating_avg": me["rating_avg"],
                "price_rank": price_rank[me["listing_id"]],
                "sales_rank": sales_rank[me["listing_id"]],
                "rating_rank": rating_rank[me["listing_id"]],
                "cheaper_count": cheaper,
                "pricier_count": pricier,
                "category_size": len(members),
                "category_live_count": len(
                    [m for m in members if m["live"]]),
                "category_retired_count": len(
                    [m for m in members if not m["live"]]),
                "category_min_price": min(prices),
                "category_max_price": max(prices),
                "rivals": rivals,
                "returned": len(rivals),
                "truncated": len(rivals) < len(members),
                "disclaimer": self.disclaimer}

    def api_similar_listings(self, listing_id, limit=None,
                             include_delisted=False):
        """Nearest-neighbour discovery face (criteria
        AC-AMSI1..AC-AMSI8 pre-registered in the R2148
        explore-queue row BEFORE this code existed).

        Every other discovery door makes the caller state the
        criteria first: api_search wants a keyword, a seller, a
        price band or a category, api_categories describes what a
        bucket is made of, api_category_demand asks whether it
        sells and api_listing_position ranks one listing inside its
        bucket. Nothing answered the buyer's most natural follow-up
        after opening one listing - "what else is like this one" -
        so a caller had to read the listing, harvest its category
        and price, then rebuild the same neighbour set by hand and
        sort it themselves.

        This face pins the definition of "similar" the market never
        had: the candidate set is the listing's EFFECTIVE category
        bucket minus the head, ordered by asking-price distance from
        the head, then price, then listing_id, so the order is a
        total order and two equally distant neighbours never swap
        between calls. Price rides current price, rating rides the
        effective stars and net sales ride the scarcity seam, so a
        repricing, a rating revision, a refund or a restock moves
        the neighbour set in the same step it moves every other read
        face - and no listing row is ever rewritten. An
        uncategorized head only recruits uncategorized listings
        (zero cross-bucket permeation) and a retired head stays
        readable so history is not erased. Pure read: zero row
        mutations, zero token movement."""
        if (not isinstance(listing_id, int) or isinstance(listing_id, bool)
                or listing_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(listing_id))
        with self._lock:
            self._require_listing(listing_id)
            if limit is not None:
                if (not isinstance(limit, int) or isinstance(limit, bool)
                        or limit < 1):
                    raise ApiMarketError(E_AM_BAD_ARGS, str(limit))
            if not isinstance(include_delisted, bool):
                raise ApiMarketError(E_AM_BAD_ARGS,
                                     str(include_delisted))
            head = self._conn.execute(
                "SELECT listing_id, dev_account, listing_key, title,"
                " description, token_price, category"
                " FROM apimarket_listings WHERE listing_id = ?",
                (listing_id,)).fetchone()
            category = self._category_state(listing_id, head[6])[0]
            head_price = int(self._current_price(listing_id,
                                                int(head[5])))
            head_stamp = self._delisted_utc(listing_id)
            rows = self._conn.execute(
                "SELECT listing_id, dev_account, listing_key,"
                " title, description, token_price, category"
                " FROM apimarket_listings ORDER BY listing_id").fetchall()
            candidates = []
            for r in rows:
                lid = int(r[0])
                if lid == int(listing_id):
                    continue
                if self._category_state(lid, r[6])[0] != category:
                    continue
                stamp = self._delisted_utc(lid)
                if stamp is not None and not include_delisted:
                    continue
                price = int(self._current_price(lid, int(r[5])))
                eff_title, _eff_desc, _n_meta, _latest = \
                    self._metadata_state(lid, r[3], r[4])
                n_rate, avg = self._agg_rating(lid)
                candidates.append({
                    "listing_id": lid,
                    "dev_account": r[1],
                    "listing_key": r[2],
                    "title": eff_title,
                    "current_price": price,
                    "price_delta": price - head_price,
                    "abs_price_delta": abs(price - head_price),
                    "rating_count": n_rate,
                    "rating_avg": avg,
                    "net_sales": int(self._supply_full(lid)[3]),
                    "live": stamp is None,
                    "delisted_utc": stamp})
            candidates.sort(key=lambda m: (m["abs_price_delta"],
                                           m["current_price"],
                                           m["listing_id"]))
            total = len(candidates)
            picked = candidates if limit is None else candidates[:limit]
            picked = [dict(m) for m in picked]
        return {"listing_id": int(listing_id),
                "category": category,
                "live": head_stamp is None,
                "delisted_utc": head_stamp,
                "current_price": head_price,
                "include_delisted": include_delisted,
                "limit": limit,
                "total": total,
                "returned": len(picked),
                "truncated": len(picked) < total,
                "rows": picked,
                "disclaimer": self.disclaimer}

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

    def api_market_feed(self, since_utc=None, until_utc=None,
                        kinds=None, limit=None, listing_id=None,
                        dev_account=None):
        """Market-wide public activity feed (criteria AC-AMF1..AC-AMF8
        pre-registered in the R2107 explore-queue row BEFORE this
        code existed).

        Every read face answers a question about the market's current
        state; nothing answered "what just happened here". Eleven
        append-only event families already exist in separate tables,
        so a resident or an operator had to open eleven faces and
        merge the timeline by hand. This face merges them into one
        chronologically ordered stream:

          - published / delisted / relisted from the lifecycle rows
            (the current listing title and seller are joined in);
          - price_revised and metadata_revised (the revised title
            rides in detail) and restocked (units);
          - purchased (price_paid, no buyer identity) and refunded
            (amount plus reason);
          - rated and rating_revised (stars plus previous_stars) and
            rating_replied (reply text).

        The window is half-open [since_utc, until_utc), both bounds
        optional; the order is ascending (event_utc, kind_rank,
        ref_id) with the module-fixed kind rank, so a same-second
        batch has one stable answer. kinds narrows the family and is
        normalized to the pinned rank order. limit keeps the NEWEST
        N events (the tail of the ordered stream) and returns them
        ascending; total is always the pre-truncation count.

        listing_id (AC-AMFL1..AC-AMFL8, pre-registered in the R2113
        explore-queue row BEFORE this code existed) narrows the same
        stream to one shelf, so an operator looking at one listing can
        answer "what happened to this one" without opening the seven
        per-listing history faces and merging them by hand. It composes
        with every earlier axis; a shape-valid id the market does not
        hold answers an honest empty feed, because the feed is a stream
        filter rather than an entity lookup (api_view is that entity
        face).

        dev_account (AC-AMSF1..AC-AMSF8, pre-registered in the R2139
        explore-queue row BEFORE this code existed) narrows the same
        stream to the shelves ONE seller owns, so a seller holding N
        listings can read a single timeline of their own market events
        instead of calling the per-listing filter N times and merging
        the answers by hand. All eleven event families already carry
        the seller of record through their listing row, so the filter
        is a stream predicate and nothing is joined twice. A
        shape-valid account that owns no listing answers an honest
        empty feed; the key is echoed in the envelope ONLY when a
        filter is given, so a caller that never filters keeps the
        R2107 contract byte-identical.

        Gate order is pinned by AC-AMF6 and extended by AC-AMFL2 and
        AC-AMSF2 - window shape, inverted window, kinds shape, limit
        shape, listing shape, then seller shape - and every gate runs
        BEFORE any read,
        fail-closed with zero side effects. The row shape
        is a fixed thirteen keys with None for fields that do not
        apply to a kind, and no buyer identity is exposed (the feed
        is public). Pure read: zero row mutations, zero token
        movement."""
        if since_utc is not None:
            _assert_instant(since_utc, "since_utc")
        if until_utc is not None:
            _assert_instant(until_utc, "until_utc")
        if (since_utc is not None and until_utc is not None
                and since_utc > until_utc):
            raise ApiMarketError(E_AM_BAD_WINDOW, "since_utc>until_utc")
        wanted = None
        if kinds is not None:
            if (isinstance(kinds, str)
                    or not isinstance(kinds, (list, tuple))):
                raise ApiMarketError(E_AM_BAD_ARGS, "bad kinds")
            tokens = []
            for token in kinds:
                if (not isinstance(token, str)
                        or token not in _FEED_KIND_RANK):
                    raise ApiMarketError(E_AM_BAD_ARGS,
                                         "bad kind: %r" % (token,))
                if token not in tokens:
                    tokens.append(token)
            if not tokens:
                raise ApiMarketError(E_AM_BAD_ARGS, "kinds empty")
            wanted = tuple(sorted(tokens, key=_FEED_KIND_RANK.get))
        if limit is not None:
            if (isinstance(limit, bool) or not isinstance(limit, int)
                    or limit < 1):
                raise ApiMarketError(E_AM_BAD_ARGS,
                                     "bad limit: %r" % (limit,))
        only = None
        if listing_id is not None:
            if (isinstance(listing_id, bool)
                    or not isinstance(listing_id, int)
                    or listing_id < 1):
                raise ApiMarketError(E_AM_BAD_ARGS,
                                     "bad listing_id: %r"
                                     % (listing_id,))
            only = int(listing_id)
        dev = None
        if dev_account is not None:
            if not str(dev_account or "").startswith("usr:"):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, str(dev_account))
            dev = str(dev_account)
        with self._lock:
            listings = {}
            for r in self._conn.execute(
                    "SELECT listing_id, listing_key, title, dev_account,"
                    " token_price, listed_utc FROM apimarket_listings"):
                listings[int(r[0])] = (r[1], r[2], r[3], int(r[4]), r[5])
            events = []

            def add(kind, stamp, ref, listing_id, **extra):
                if wanted is not None and kind not in wanted:
                    return
                if only is not None and only != int(listing_id):
                    return
                base = listings.get(int(listing_id))
                if base is None:
                    return
                if dev is not None and base[2] != dev:
                    return
                if since_utc is not None and stamp < since_utc:
                    return
                if until_utc is not None and stamp >= until_utc:
                    return
                row = {"kind": kind, "event_utc": stamp,
                       "ref_id": int(ref), "listing_id": int(listing_id),
                       "listing_key": base[0], "title": base[1],
                       "dev_account": base[2], "token_price": None,
                       "stars": None, "previous_stars": None,
                       "amount": None, "units": None, "detail": None}
                row.update(extra)
                events.append(row)

            for lid, base in listings.items():
                add("published", base[4], lid, lid,
                    token_price=base[3])
            for r in self._conn.execute(
                    "SELECT revision_id, listing_id, token_price,"
                    " revised_utc FROM apimarket_price_revisions"):
                add("price_revised", r[3], r[0], r[1],
                    token_price=int(r[2]))
            for r in self._conn.execute(
                    "SELECT revision_id, listing_id, title, revised_utc"
                    " FROM apimarket_listing_revisions"):
                add("metadata_revised", r[3], r[0], r[1], detail=r[2])
            for r in self._conn.execute(
                    "SELECT revision_id, listing_id, add_units,"
                    " restocked_utc FROM apimarket_supply_revisions"):
                add("restocked", r[3], r[0], r[1], units=int(r[2]))
            for r in self._conn.execute(
                    "SELECT purchase_id, listing_id, price_paid,"
                    " purchased_utc FROM apimarket_purchases"):
                add("purchased", r[3], r[0], r[1],
                    token_price=int(r[2]))
            for r in self._conn.execute(
                    "SELECT rating_id, listing_id, stars, rated_utc"
                    " FROM apimarket_ratings"):
                add("rated", r[3], r[0], r[1], stars=int(r[2]))
            for r in self._conn.execute(
                    "SELECT revision_id, listing_id, previous_stars,"
                    " stars, revised_utc FROM apimarket_rating_revisions"):
                add("rating_revised", r[4], r[0], r[1],
                    previous_stars=int(r[2]), stars=int(r[3]))
            for r in self._conn.execute(
                    "SELECT reply_id, listing_id, reply_text, replied_utc"
                    " FROM apimarket_rating_replies"):
                add("rating_replied", r[3], r[0], r[1], detail=r[2])
            for r in self._conn.execute(
                    "SELECT refund_id, listing_id, amount, reason,"
                    " refunded_utc FROM apimarket_refunds"):
                add("refunded", r[4], r[0], r[1], amount=int(r[2]),
                    detail=r[3])
            for r in self._conn.execute(
                    "SELECT delist_id, listing_id, delisted_utc"
                    " FROM apimarket_delistings"):
                add("delisted", r[2], r[0], r[1])
            for r in self._conn.execute(
                    "SELECT relist_id, listing_id, relisted_utc"
                    " FROM apimarket_relistings"):
                add("relisted", r[2], r[0], r[1])
            events.sort(key=lambda e: (e["event_utc"],
                                       _FEED_KIND_RANK[e["kind"]],
                                       e["ref_id"]))
            total = len(events)
            shown = events
            if limit is not None and total > limit:
                shown = events[-limit:]
        env = {"kinds": (list(wanted) if wanted is not None
                         else list(_FEED_KINDS)),
               "since_utc": since_utc,
               "until_utc": until_utc,
               "listing_id": only,
               "limit": limit,
               "total": total,
               "returned": len(shown),
               "truncated": total > len(shown),
               "disclaimer": self.disclaimer}
        if dev is not None:
            env["dev_account"] = dev
        env["events"] = shown
        return env

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

    def api_market_price_percentiles(self, include_delisted=False):
        """Market-wide asking-price distribution (criteria
        AC-MPP1..AC-MPP8 pre-registered in the R2160 explore-queue
        claim row BEFORE this code existed).

        Gap: api_categories answers only the per-bucket min/max band,
        api_listing_position answers one listing's rank inside its own
        bucket and api_market_stats carries a single avg_live_price.
        Nowhere could a seller learn where its asking price sits in the
        market distribution, and an operator had no pricing benchmark -
        the quartiles, the median, the ninetieth percentile and the
        spread were absent.

        Scope: LIVE listings by default; a retired listing enters only
        when include_delisted is True, and its historical price is then
        read through the same price seam (a retirement never rewrites
        the asking price). This is an ASKING-PRICE face, not a
        turnover face: purchases, refunds and ratings never move the
        distribution, while revise_price moves it in one step.

        Percentiles are the linear-interpolation method pinned by
        AC-MPP3 - position pos = (n - 1) * q on the ascending sample
        list, interpolated between the two neighbouring samples, with
        one sample covering every quantile. Rows are one per effective
        category bucket (the uncategorized bucket last, mirroring
        api_categories) so the global envelope is exactly the
        aggregate of its rows: listing_count == live + retired == the
        sum over rows, the global minimum is the smallest row minimum
        and the global maximum the largest row maximum.

        Gate: include_delisted must be a real bool, fail-closed with
        E_AM_BAD_ARGS before any read. Pure read: zero row mutations,
        zero token movement; the envelope carries the resident
        non-advisory disclaimer."""
        if not isinstance(include_delisted, bool):
            raise ApiMarketError(E_AM_BAD_ARGS, include_delisted)
        with self._lock:
            listings = self._conn.execute(
                "SELECT listing_id, token_price, category FROM"
                " apimarket_listings ORDER BY listing_id").fetchall()
            buckets = {}
            all_prices = []
            live_total = 0
            retired_total = 0
            for r in listings:
                listing_id = int(r[0])
                retired = self._delisted_utc(listing_id) is not None
                if retired and not include_delisted:
                    continue
                price = int(self._current_price(listing_id, int(r[1])))
                cat = self._category_state(listing_id, r[2])[0]
                b = buckets.get(cat)
                if b is None:
                    b = {"category": cat, "live": 0, "retired": 0,
                         "prices": []}
                    buckets[cat] = b
                if retired:
                    b["retired"] += 1
                    retired_total += 1
                else:
                    b["live"] += 1
                    live_total += 1
                b["prices"].append(price)
                all_prices.append(price)
            rows = []
            ordered = sorted(c for c in buckets if c is not None)
            if None in buckets:
                ordered.append(None)
            for cat in ordered:
                b = buckets[cat]
                vals = sorted(b["prices"])
                rows.append({
                    "category": cat,
                    "listing_count": len(vals),
                    "live_listing_count": b["live"],
                    "retired_listing_count": b["retired"],
                    "min_price": vals[0],
                    "max_price": vals[-1],
                    "mean_price": float(sum(vals)) / len(vals),
                    "p50_price": percentile(vals, 0.5)})
        vals = sorted(all_prices)
        return {"listing_count": len(vals),
                "live_listing_count": live_total,
                "retired_listing_count": retired_total,
                "min_price": vals[0] if vals else None,
                "max_price": vals[-1] if vals else None,
                "p25_price": percentile(vals, 0.25),
                "p50_price": percentile(vals, 0.5),
                "p75_price": percentile(vals, 0.75),
                "p90_price": percentile(vals, 0.9),
                "mean_price": (float(sum(vals)) / len(vals)
                               if vals else None),
                "spread": (vals[-1] - vals[0]) if vals else None,
                "category_count": len(rows),
                "categories": rows,
                "disclaimer": self.disclaimer}

    def api_market_ticket_size(self, dev_account=None,
                               include_refunded=False):
        """Achieved ticket-size distribution (criteria
        AC-MTS1..AC-MTS8 pre-registered in the R2184 explore-queue
        claim row BEFORE this code existed; the AC-MTS prefix,
        ledger-apimarket-ticketsize, p90_ticket and _ticket_sample
        were git-grep zero-occupancy against HEAD 2026-10-28, rc=1).

        Gap: api_market_price_percentiles quantiles the ASKING price
        of what is still on the shelf, api_listing_position ranks one
        listing inside its bucket, api_market_daily and the month
        faces carry cash totals and api_repeat_purchase counts
        buyers. Nothing answered what a sale actually COSTS in this
        market, so in a world where prices are revised the asking
        p50 and the achieved p50 are different quantities and an
        operator had no turnover benchmark at all.

        Authority: one ticket per apimarket_purchases row, valued at
        its own immutable price_paid - revise_price and delist_api
        never rewrite a historical ticket. The default scope is NET:
        a refunded purchase leaves the sample (a refund is not
        revenue), and include_refunded=True puts it back, which is
        what makes the two calls line up exactly with
        api_market_stats on both axes (see the docstring block on
        conservation below). Ticket counts therefore read sale_count
        rather than ticket_count: ticket_count is already the
        eventtickets face's own key and this face does not borrow it.

        Conservation: rows are one per effective category bucket (the
        uncategorized bucket last, mirroring api_categories) and the
        envelope is exactly the aggregate of its rows - sale_count,
        gross_tokens and refunded_tokens each sum over rows. Scope
        law: dev_account None is the whole market (scope ==
        'market'); a seller scope (scope == 'seller') carries strict
        isolation, and a single-seller world makes the two reads
        identical apart from the scope/dev_account pair.

        Percentiles reuse the AC-MPP3 linear-interpolation law
        through the same module-level percentile() seam, so the two
        distribution faces can never drift apart. Gate order is
        pinned: the seller account shape first (fail-closed
        E_AM_BAD_ACCOUNT), then the include_refunded bool gate
        (fail-closed E_AM_BAD_ARGS), both before any read. Pure read:
        zero row mutations, zero token movement."""
        if dev_account is not None:
            if not str(dev_account or "").startswith("usr:"):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        if not isinstance(include_refunded, bool):
            raise ApiMarketError(E_AM_BAD_ARGS, include_refunded)
        with self._lock:
            sql = ("SELECT p.listing_id, p.price_paid, l.dev_account,"
                   " l.category, f.purchase_id"
                   " FROM apimarket_purchases p"
                   " JOIN apimarket_listings l"
                   " ON l.listing_id = p.listing_id"
                   " LEFT JOIN apimarket_refunds f"
                   " ON f.purchase_id = p.purchase_id")
            args = ()
            if dev_account is not None:
                sql += " WHERE l.dev_account = ?"
                args = (dev_account,)
            sql += " ORDER BY p.purchase_id"
            rows_in = self._conn.execute(sql, args).fetchall()
            buckets = {}
            all_tickets = []
            refunded_total = 0
            gross_total = 0
            for r in rows_in:
                listing_id = int(r[0])
                price = int(r[1])
                refunded = r[4] is not None
                if refunded and not include_refunded:
                    continue
                cat = self._category_state(listing_id, r[3])[0]
                b = buckets.get(cat)
                if b is None:
                    b = {"category": cat, "tickets": [],
                         "refunded_count": 0, "gross": 0,
                         "refunded": 0}
                    buckets[cat] = b
                b["tickets"].append(price)
                b["gross"] += price
                gross_total += price
                if refunded:
                    b["refunded_count"] += 1
                    b["refunded"] += price
                    refunded_total += price
                all_tickets.append(price)
            rows = []
            ordered = sorted(c for c in buckets if c is not None)
            if None in buckets:
                ordered.append(None)
            for cat in ordered:
                b = buckets[cat]
                vals = sorted(b["tickets"])
                rows.append({
                    "category": cat,
                    "sale_count": len(vals),
                    "refunded_sale_count": b["refunded_count"],
                    "gross_tokens": b["gross"],
                    "refunded_tokens": b["refunded"],
                    "net_gross_tokens": b["gross"] - b["refunded"],
                    "min_ticket": vals[0],
                    "max_ticket": vals[-1],
                    "mean_ticket": float(sum(vals)) / len(vals),
                    "p50_ticket": percentile(vals, 0.5)})
        vals = sorted(all_tickets)
        return {"scope": ("market" if dev_account is None else "seller"),
                "dev_account": dev_account,
                "include_refunded": include_refunded,
                "sale_count": len(vals),
                "refunded_sale_count": sum(
                    row["refunded_sale_count"] for row in rows),
                "gross_tokens": gross_total,
                "refunded_tokens": refunded_total,
                "net_gross_tokens": gross_total - refunded_total,
                "min_ticket": vals[0] if vals else None,
                "p25_ticket": percentile(vals, 0.25),
                "p50_ticket": percentile(vals, 0.5),
                "p75_ticket": percentile(vals, 0.75),
                "p90_ticket": percentile(vals, 0.9),
                "max_ticket": vals[-1] if vals else None,
                "mean_ticket": (float(sum(vals)) / len(vals)
                                if vals else None),
                "spread": (vals[-1] - vals[0]) if vals else None,
                "category_count": len(rows),
                "categories": rows,
                "disclaimer": self.disclaimer}

    def api_buyer_rating_pattern(self, buyer_id):
        """Buyer star-giving tendency (criteria AC-BRP1..AC-BRP8
        pre-registered in the R2164 explore-queue row BEFORE this code
        existed).

        api_buyer_profile answers only rating_count and an average, so
        the question "is this resident consistently harsh or generous,
        is it stricter than the market, and how did the stars spread"
        had no face. This is an aggregate face - the row face stays
        api_ratings / api_rating_history, so nothing is duplicated.

        Laws pinned by the suite: distribution conservation (the five
        buckets sum to rating_count and to harsh+neutral+generous),
        star_sum from the buckets, avg as star_sum/count with None on
        an honest empty, min/max as measured extremes, and the three
        ratios None rather than a fake zero where nothing was rated.
        Every star value reads through the one effective-stars seam, so
        revise_rating moves the whole envelope in one step and a revert
        restores it byte for byte, while revision_count and
        revised_rating_count keep the history. Counts come from this
        buyer's own ratings only - the single declared exception is
        market_avg_stars, which is the whole market by design - and
        delisting, relisting or a refund never removes a rating.
        tendency_delta is avg - market_avg and None when either side is
        absent, negative meaning harsher than the market.
        purchase_count counts every purchase including refunded ones,
        and rating_coverage is rating_count/purchase_count (None with
        zero purchases). Gate: prefix-only account shape before any read
        (fail-closed E_AM_BAD_ACCOUNT); a prefix-valid unknown account
        gets an honest zero envelope. Pure read: zero row mutations,
        zero token movement."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        buyer = str(buyer_id)
        with self._lock:
            mine = self._conn.execute(
                "SELECT rating_id, listing_id, stars"
                " FROM apimarket_ratings WHERE buyer_id = ?",
                (buyer,)).fetchall()
            revs = self._conn.execute(
                "SELECT r.rating_id, COUNT(*) FROM"
                " apimarket_rating_revisions r"
                " JOIN apimarket_ratings g"
                " ON g.rating_id = r.rating_id"
                " WHERE g.buyer_id = ? GROUP BY r.rating_id",
                (buyer,)).fetchall()
            market = self._conn.execute(
                "SELECT rating_id, stars FROM apimarket_ratings"
            ).fetchall()
            bought = self._conn.execute(
                "SELECT COUNT(*) FROM apimarket_purchases"
                " WHERE buyer_id = ?", (buyer,)).fetchone()
        buckets = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        star_sum = 0
        low = None
        high = None
        listings = set()
        for rid, lid, base in mine:
            stars = self._effective_stars(int(rid), int(base))
            buckets[str(stars)] += 1
            star_sum += stars
            listings.add(int(lid))
            if low is None or stars < low:
                low = stars
            if high is None or stars > high:
                high = stars
        count = len(mine)
        market_sum = 0
        for rid, base in market:
            market_sum += self._effective_stars(int(rid), int(base))
        market_avg = (float(market_sum) / len(market)
                      if market else None)
        avg = (float(star_sum) / count) if count else None
        harsh = buckets["1"] + buckets["2"]
        neutral = buckets["3"]
        generous = buckets["4"] + buckets["5"]
        purchases = int(bought[0]) if bought else 0
        delta = None
        if avg is not None and market_avg is not None:
            delta = avg - market_avg
        return {
            "buyer_id": buyer,
            "rating_count": count,
            "listing_count": len(listings),
            "revision_count": sum(int(r[1]) for r in revs),
            "revised_rating_count": len(revs),
            "star_sum": star_sum,
            "avg_stars": avg,
            "min_stars": low,
            "max_stars": high,
            "harsh_count": harsh,
            "neutral_count": neutral,
            "generous_count": generous,
            "harsh_ratio": (float(harsh) / count if count else None),
            "generous_ratio": (float(generous) / count
                               if count else None),
            "market_avg_stars": market_avg,
            "tendency_delta": delta,
            "purchase_count": purchases,
            "rating_coverage": (float(count) / purchases
                                if purchases else None),
            "star_distribution": dict(
                (k, buckets[k]) for k in sorted(buckets)),
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

    def api_refund_register(self, since_utc=None, until_utc=None,
                            dev_account=None, listing_id=None):
        """Market-wide refund register (criteria AC-AMRR1..AC-AMRR8
        pre-registered in the R2111 explore-queue row BEFORE this code
        existed).

        Refunds were reachable only one purchase at a time
        (api_refund(purchase_id)) or one buyer at a time (the R2110
        buyer history block). Nothing answered the operator's question
        "what came back this month across the whole market, which
        seller absorbed the most, and where does it sit per listing",
        so every settlement reconciliation merged those two views by
        hand. This face reads the append-only apimarket_refunds rows
        once and answers it in one envelope: the filtered rows plus
        three groupings over exactly the same rows (by UTC month of
        refunded_utc, by developer, and the rows themselves).

        The window is half-open [since_utc, until_utc) on the stored
        refunded_utc stamp, both bounds optional; dev_account and
        listing_id narrow the same row set. Groupings are derived, not
        cached: months ascending by month, by_dev ascending by account,
        rows ascending by (refunded_utc, refund_id), so a same-second
        batch has one stable answer. Money is never recomputed - every
        amount, dev_share and platform_share is the stored value, and
        dev_share + platform_share == amount holds per stored row
        (table CHECK), so the totals conserve exactly.

        Gate order is pinned by AC-AMRR6 - window shapes, inverted
        window, dev_account shape, listing_id shape - and every gate
        runs BEFORE any read, fail-closed with zero side effects. Pure
        read: zero row mutations and zero token movement. The envelope
        carries the resident non-advisory disclaimer."""
        if since_utc is not None:
            _assert_instant(since_utc, "since_utc")
        if until_utc is not None:
            _assert_instant(until_utc, "until_utc")
        if (since_utc is not None and until_utc is not None
                and since_utc > until_utc):
            raise ApiMarketError(E_AM_BAD_WINDOW, "since_utc>until_utc")
        if dev_account is not None:
            if not isinstance(dev_account, str) or not dev_account:
                raise ApiMarketError(E_AM_BAD_ARGS,
                                     "bad dev_account: %r" % (dev_account,))
        if listing_id is not None:
            if (isinstance(listing_id, bool)
                    or not isinstance(listing_id, int)
                    or listing_id <= 0):
                raise ApiMarketError(E_AM_BAD_ARGS, str(listing_id))
        sql = ("SELECT f.refund_id, f.purchase_id, f.listing_id,"
               " f.buyer_id, f.dev_account, f.amount, f.dev_share,"
               " f.platform_share, f.refund_tx, f.refunded_utc,"
               " f.reason, l.listing_key, l.title"
               " FROM apimarket_refunds f"
               " LEFT JOIN apimarket_listings l"
               " ON l.listing_id = f.listing_id")
        clauses = []
        args = []
        if since_utc is not None:
            clauses.append("f.refunded_utc >= ?")
            args.append(since_utc)
        if until_utc is not None:
            clauses.append("f.refunded_utc < ?")
            args.append(until_utc)
        if dev_account is not None:
            clauses.append("f.dev_account = ?")
            args.append(dev_account)
        if listing_id is not None:
            clauses.append("f.listing_id = ?")
            args.append(int(listing_id))
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY f.refunded_utc, f.refund_id"
        with self._lock:
            rows = self._conn.execute(sql, tuple(args)).fetchall()
        refunds = []
        months = []
        by_dev = []
        month_index = {}
        dev_index = {}
        amount_total = 0
        dev_total = 0
        plat_total = 0
        for r in rows:
            amount = int(r[5])
            dev_share = int(r[6])
            platform_share = int(r[7])
            stamp = r[9]
            month = stamp[:7]
            refunds.append({
                "refund_id": int(r[0]),
                "purchase_id": int(r[1]),
                "listing_id": int(r[2]),
                "listing_key": r[11],
                "title": r[12],
                "buyer_id": r[3],
                "dev_account": r[4],
                "amount": amount,
                "dev_share": dev_share,
                "platform_share": platform_share,
                "refund_tx": r[8],
                "refunded_utc": stamp,
                "reason": r[10]})
            for table, index, key in ((months, month_index, month),
                                      (by_dev, dev_index, r[4])):
                bucket = index.get(key)
                if bucket is None:
                    if table is months:
                        bucket = {"month": key, "refund_count": 0,
                                  "amount": 0, "dev_share": 0,
                                  "platform_share": 0}
                    else:
                        bucket = {"dev_account": key,
                                  "refund_count": 0, "amount": 0,
                                  "dev_share": 0,
                                  "platform_share": 0}
                    index[key] = bucket
                    table.append(bucket)
                bucket["refund_count"] += 1
                bucket["amount"] += amount
                bucket["dev_share"] += dev_share
                bucket["platform_share"] += platform_share
            amount_total += amount
            dev_total += dev_share
            plat_total += platform_share
        months.sort(key=lambda row: row["month"])
        by_dev.sort(key=lambda row: row["dev_account"])
        return {"kind": "api_refund_register",
                "since_utc": since_utc,
                "until_utc": until_utc,
                "dev_account": dev_account,
                "listing_id": listing_id,
                "refund_count": len(refunds),
                "amount": amount_total,
                "dev_share": dev_total,
                "platform_share": plat_total,
                "months": months,
                "by_dev": by_dev,
                "refunds": refunds,
                "disclaimer": self.disclaimer}

    def api_buyer_todo(self, buyer_id):
        """Buyer-side rating-debt queue (criteria AC-AMBT1..AC-AMBT8
        pre-registered in the R2105 explore-queue row BEFORE this code
        existed): the work queue the rating door never had.

        api_library shows every purchase with its own stars, and
        api_buyer_profile counts the ratings, but a resident holding
        twenty purchases still has to page through the library and
        eyeball which rows carry a None. The seller side got that
        queue in R2096 (api_seller_inbox); this is its buyer-side
        mirror: only the purchases still awaiting a rating, oldest
        debt first (purchased_utc ascending, then purchase_id).

        Duplicate-free by construction, pinned by AC-AMBT3: the
        purchase gate already forbids a second purchase of the same
        listing (E_AM_PURCHASE_DUP), and one rating settles a listing,
        so the queue can never carry the same listing twice - a
        rejected repeat purchase leaves the queue byte-identical.

        Per-purchase-row state is disjoint with pinned precedence
        rated > refunded > pending, so
        rated_count + refunded_count + pending_count == purchase_count
        for every account (AC-AMBT6). A refunded purchase leaves the
        queue (the transaction was reversed) but a refunded row whose
        listing still carries this buyer's stars counts as rated,
        because a rating is the settlement act that actually happened.
        Truthful note: rate_api itself still accepts a rating on a
        refunded purchase, so this face is a prompt, never a gate.

        Retirement does not erase the debt: a delisted listing keeps
        its pending row with delisted=True and its live asking price
        read through the one current-price seam (AC-AMBT5). The
        account shape gate is prefix-only by the truthful R2077/R2078
        finding and runs before any read; a prefix-valid account with
        no purchases gets an honest empty queue. Pure read: zero row
        mutations and zero token movement. The envelope carries the
        resident non-advisory disclaimer."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        with self._lock:
            rows = self._conn.execute(
                "SELECT p.purchase_id, p.listing_id, l.listing_key,"
                " l.title, l.dev_account, p.price_paid,"
                " p.purchased_utc, l.token_price"
                " FROM apimarket_purchases p JOIN apimarket_listings l"
                " ON l.listing_id = p.listing_id"
                " WHERE p.buyer_id = ?"
                " ORDER BY p.purchased_utc, p.purchase_id",
                (buyer_id,)).fetchall()
            rated = 0
            refunded = 0
            pending_rows = 0
            pending = []
            for r in rows:
                listing_id = int(r[1])
                stars = self._conn.execute(
                    "SELECT stars FROM apimarket_ratings"
                    " WHERE buyer_id = ? AND listing_id = ?",
                    (buyer_id, listing_id)).fetchone()
                if stars is not None:
                    rated += 1
                    continue
                back = self._conn.execute(
                    "SELECT refund_id FROM apimarket_refunds"
                    " WHERE purchase_id = ?", (int(r[0]),)).fetchone()
                if back is not None:
                    refunded += 1
                    continue
                pending_rows += 1
                stamp = self._delisted_utc(listing_id)
                pending.append({
                    "purchase_id": int(r[0]),
                    "listing_id": listing_id,
                    "listing_key": r[2],
                    "title": r[3],
                    "dev_account": r[4],
                    "price_paid": int(r[5]),
                    "purchased_utc": r[6],
                    "delisted": stamp is not None,
                    "current_price": self._current_price(
                        listing_id, int(r[7]))})
        return {"buyer_id": buyer_id,
                "purchase_count": len(rows),
                "rated_count": rated,
                "refunded_count": refunded,
                "pending_count": pending_rows,
                "disclaimer": self.disclaimer,
                "pending": pending}

    def api_buyer_claim_todo(self, buyer_id):
        """Buyer-side post-sale decision queue (criteria
        AC-AMBC1..AC-AMBC8 pre-registered in the R2140 explore-queue
        row BEFORE this code existed).

        R2129 gave the buyer a claim door, R2130 the seller one
        answer, R2131 a withdrawal and R2137 a follow-up note, so the
        thread became two-way - but the ball only ever changed hands
        silently. R2138 had to state its own rule out loud: an
        answered claim with no follow-up stays out of the SELLER
        queue "because the ball is with the buyer". Nothing told the
        buyer that the ball had arrived. api_claims lists the row
        with status answered, api_claim_thread opens one claim, and
        neither is a queue, so a buyer holding several claims had to
        read every row and decide by hand which ones await a
        decision.

        This face is the buyer-side mirror of api_seller_todo,
        restricted to the one claim family that is genuinely a BUYER
        duty. States are disjoint with pinned precedence
        refunded > withdrawn > disputed > needs_decision > waiting
        (AC-AMBC2): refunded and withdrawn are settled; disputed
        means the buyer already pushed back and the ball is with the
        seller; needs_decision means the seller answered and no
        follow-up exists yet; waiting means no answer has landed.
        Only needs_decision rows enter the queue, and every claim
        lands in exactly one of the five counters, so
        claim_count == needs_decision + waiting + disputed +
        refunded + withdrawn.

        The rows are pushed, never stored: an answer fills the queue,
        a follow-up or a refund drains it, and no claim row, answer
        row, note row or refund row is ever rewritten. Ordering is
        (opened_utc, claim_id) ascending so the oldest debt is
        always first, and oldest_waiting_utc reports how long the
        buyer's longest unanswered claim has waited. A retired
        listing keeps its answered claim, and price_paid is the
        stored purchase amount, not the listing's current asking
        price. The account shape gate is prefix-only per the
        R2077/R2078 finding and runs before any read; a prefix-valid
        account with no claims gets an honest empty envelope. Pure
        read: zero row mutations and zero token movement."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        sql = ("SELECT c.claim_id, c.purchase_id, c.listing_id,"
               " c.price_paid, c.claim_text, c.opened_utc,"
               " c.dev_account, l.title, r.response_text, r.replied_utc,"
               " w.withdrawn_utc, f.refund_id, n.note_id"
               " FROM apimarket_claims c"
               " LEFT JOIN apimarket_listings l"
               " ON l.listing_id = c.listing_id"
               " LEFT JOIN apimarket_claim_responses r"
               " ON r.claim_id = c.claim_id"
               " LEFT JOIN apimarket_claim_withdrawals w"
               " ON w.claim_id = c.claim_id"
               " LEFT JOIN apimarket_refunds f"
               " ON f.purchase_id = c.purchase_id"
               " LEFT JOIN apimarket_claim_notes n"
               " ON n.claim_id = c.claim_id"
               " WHERE c.buyer_id = ?"
               " ORDER BY c.opened_utc, c.claim_id")
        with self._lock:
            rows = self._conn.execute(sql, (buyer_id,)).fetchall()
        base = []
        for r in rows:
            if r[11] is not None:
                state = "refunded"
            elif r[10] is not None:
                state = "withdrawn"
            elif r[12] is not None:
                state = "disputed"
            elif r[8] is not None:
                state = "needs_decision"
            else:
                state = "waiting"
            base.append((r, state))
        queue = []
        oldest_waiting = None
        for r, state in base:
            if state == "waiting":
                if oldest_waiting is None or r[5] < oldest_waiting:
                    oldest_waiting = r[5]
                continue
            if state != "needs_decision":
                continue
            queue.append({
                "claim_id": int(r[0]),
                "purchase_id": int(r[1]),
                "listing_id": int(r[2]),
                "listing_title": r[7],
                "dev_account": r[6],
                "price_paid": int(r[3]),
                "claim_text": r[4],
                "opened_utc": r[5],
                "response_text": r[8],
                "responded_utc": r[9]})
        counts = {}
        for _r, state in base:
            counts[state] = counts.get(state, 0) + 1
        return {"buyer_id": buyer_id,
                "claim_count": len(base),
                "needs_decision_count": len(queue),
                "waiting_count": counts.get("waiting", 0),
                "disputed_count": counts.get("disputed", 0),
                "refunded_count": counts.get("refunded", 0),
                "withdrawn_count": counts.get("withdrawn", 0),
                "oldest_needs_decision_utc":
                    queue[0]["opened_utc"] if queue else None,
                "oldest_waiting_utc": oldest_waiting,
                "disclaimer": self.disclaimer,
                "claims": queue}

    def api_seller_todo(self, dev_account):
        """Seller-side unified duty queue (criteria AC-AMTD1..AC-AMTD8
        pre-registered in the R2138 explore-queue row BEFORE this code
        existed).

        Every seller obligation already had its own face -
        api_seller_inbox carries unanswered ratings, api_seller_questions
        unanswered questions, api_claims the claim queue the seller has to
        filter by hand, and the R2137 disputed state lived only inside one
        claim thread. So a seller holding N listings had to open four
        faces and merge them by hand to answer "what do I owe right now,
        and how long has the oldest one waited". The buyer side got that
        merged queue in R2105 (api_buyer_todo); this is its seller mirror.

        Four families, pinned by AC-AMTD2:
          rating          an unanswered rating on any listing of the seller
          question        an unanswered question on any listing
          claim_open      a claim nobody has answered yet
          claim_disputed  a claim the seller answered AND the buyer then
                          restated (a follow-up note exists) - the state
                          R2137 introduced, which no queue could see
        Claim status is derived at read time through the same precedence
        api_claims uses (refunded > withdrawn > answered > open), so a
        refund or a withdrawal silently drains the queue without
        rewriting any row and never adds one.

        Ordering is (since_utc, kind_rank, ref_id) ascending with a pinned
        kind rank rating < question < claim_open < claim_disputed, so the
        oldest debt is always first and a same-second batch has one stable
        answer. Retirement does not erase a debt. The account shape gate is
        prefix-only by the truthful R2077/R2078 finding and runs before
        any read; a prefix-valid account with no debt gets an honest empty
        envelope. Pure read: zero row mutations and zero token movement.
        The envelope carries the resident non-advisory disclaimer."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        kind_rank = {"rating": 0, "question": 1,
                     "claim_open": 2, "claim_disputed": 3}
        with self._lock:
            ratings = self._conn.execute(
                "SELECT r.rating_id, r.listing_id, l.listing_key,"
                " l.title, r.buyer_id, r.rated_utc"
                " FROM apimarket_ratings r"
                " JOIN apimarket_listings l ON l.listing_id = r.listing_id"
                " LEFT JOIN apimarket_rating_replies p"
                " ON p.rating_id = r.rating_id"
                " WHERE l.dev_account = ? AND p.reply_id IS NULL",
                (dev_account,)).fetchall()
            questions = self._conn.execute(
                "SELECT q.question_id, q.listing_id, l.listing_key,"
                " l.title, q.buyer_id, q.asked_utc, q.question_text"
                " FROM apimarket_questions q"
                " JOIN apimarket_listings l ON l.listing_id = q.listing_id"
                " LEFT JOIN apimarket_answers a"
                " ON a.question_id = q.question_id"
                " WHERE l.dev_account = ? AND a.answer_id IS NULL",
                (dev_account,)).fetchall()
            claims = self._conn.execute(
                "SELECT c.claim_id, c.listing_id, l.listing_key, l.title,"
                " c.buyer_id, c.claim_text, c.opened_utc, f.refund_id,"
                " w.withdrawn_utc, r.response_id, n.noted_utc,"
                " n.note_text"
                " FROM apimarket_claims c"
                " JOIN apimarket_listings l ON l.listing_id = c.listing_id"
                " LEFT JOIN apimarket_refunds f"
                " ON f.purchase_id = c.purchase_id"
                " LEFT JOIN apimarket_claim_responses r"
                " ON r.claim_id = c.claim_id"
                " LEFT JOIN apimarket_claim_withdrawals w"
                " ON w.claim_id = c.claim_id"
                " LEFT JOIN apimarket_claim_notes n"
                " ON n.claim_id = c.claim_id"
                " WHERE c.dev_account = ?",
                (dev_account,)).fetchall()
        rows = []
        for r in ratings:
            rows.append({"kind": "rating",
                         "ref_id": int(r[0]),
                         "listing_id": int(r[1]),
                         "listing_key": r[2],
                         "listing_title": r[3],
                         "counterparty": r[4],
                         "since_utc": r[5],
                         "detail": None})
        for q in questions:
            rows.append({"kind": "question",
                         "ref_id": int(q[0]),
                         "listing_id": int(q[1]),
                         "listing_key": q[2],
                         "listing_title": q[3],
                         "counterparty": q[4],
                         "since_utc": q[5],
                         "detail": q[6]})
        for c in claims:
            # AC-AMTD3: refunded and withdrawn claims are closed and
            # never enter the queue; an answered claim with no follow-up
            # note is waiting on the buyer, not on the seller.
            if c[7] is not None or c[8] is not None:
                continue
            if c[9] is None:
                rows.append({"kind": "claim_open",
                             "ref_id": int(c[0]),
                             "listing_id": int(c[1]),
                             "listing_key": c[2],
                             "listing_title": c[3],
                             "counterparty": c[4],
                             "since_utc": c[6],
                             "detail": c[5]})
            elif c[10] is not None:
                rows.append({"kind": "claim_disputed",
                             "ref_id": int(c[0]),
                             "listing_id": int(c[1]),
                             "listing_key": c[2],
                             "listing_title": c[3],
                             "counterparty": c[4],
                             "since_utc": c[10],
                             "detail": c[11]})
        rows.sort(key=lambda x: (x["since_utc"],
                                 kind_rank[x["kind"]],
                                 x["ref_id"]))
        rating_count = sum(1 for x in rows if x["kind"] == "rating")
        question_count = sum(1 for x in rows if x["kind"] == "question")
        claim_open_count = sum(1 for x in rows if x["kind"] == "claim_open")
        claim_disputed_count = sum(1 for x in rows
                                   if x["kind"] == "claim_disputed")
        return {"dev_account": dev_account,
                "total_count": len(rows),
                "rating_count": rating_count,
                "question_count": question_count,
                "claim_open_count": claim_open_count,
                "claim_disputed_count": claim_disputed_count,
                "listing_count": len({x["listing_id"] for x in rows}),
                "oldest_utc": rows[0]["since_utc"] if rows else None,
                "oldest_kind": rows[0]["kind"] if rows else None,
                "rows": rows,
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

    def api_refund_exposure(self, dev_account=None):
        """Seller-side refund exposure (criteria AC-RPX1..AC-RPX8
        pre-registered in the R2115 explore-queue row BEFORE this code
        existed).

        refund_api fails closed with E_AM_REFUND_UNFUNDABLE when the
        seller has already spent the proceeds (the AC-L2 balance floor
        is constitutional), but no face warned anyone that the money to
        fund the reversal was gone. The seller could not answer "how
        much of my balance is already spoken for by refunds I may have
        to pay back", and the operator could not answer "which seller
        would break a refund today". This face derives that exposure
        from rows that already exist: the unrefunded purchases' stored
        dev_share is the maximum the seller can be asked to return, and
        the live ledger balance says how much of it is actually
        fundable.

        Liability is never recomputed from a price: it is the stored
        dev_share of every purchase that has no refund row, so a
        repricing or a metadata edit moves it by nothing. A refund
        removes exactly its own dev_share from the liability and lowers
        the seller balance by the same amount, so the shortfall can only
        move through other activity - which the suite pins. Retirement
        does not erase the obligation: a retired listing keeps its open
        purchases in the exposure exactly as it keeps them in
        api_supply.

        The row set authority is the listing table (every distinct
        dev_account that owns a listing appears, zero-sale sellers
        included) - dense, never a hardcoded roster. A seller with no
        ledger account reports balance 0 with balance_known False
        rather than raising: the honest reading is "no funds on the
        books". Gate order is pinned by AC-RPX6 (dev_account shape
        before any read, prefix-only by the truthful R2077/R2078
        finding). Pure read: zero row mutations and zero token
        movement. The envelope carries the resident non-advisory
        disclaimer."""
        if dev_account is not None:
            if not str(dev_account or "").startswith("usr:"):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            if dev_account is None:
                owner_rows = self._conn.execute(
                    "SELECT DISTINCT dev_account"
                    " FROM apimarket_listings"
                    " ORDER BY dev_account").fetchall()
                sellers = [str(r[0]) for r in owner_rows]
            else:
                owner_rows = self._conn.execute(
                    "SELECT DISTINCT dev_account"
                    " FROM apimarket_listings"
                    " WHERE dev_account = ?", (str(dev_account),)
                ).fetchall()
                sellers = [str(r[0]) for r in owner_rows]
            rows = []
            for dev in sellers:
                listing_count = int(self._conn.execute(
                    "SELECT COUNT(*) FROM apimarket_listings"
                    " WHERE dev_account = ?", (dev,)).fetchone()[0])
                open_rows = self._conn.execute(
                    "SELECT COUNT(*), COALESCE(SUM(p.dev_share), 0)"
                    " FROM apimarket_purchases p"
                    " JOIN apimarket_listings l"
                    " ON l.listing_id = p.listing_id"
                    " LEFT JOIN apimarket_refunds f"
                    " ON f.purchase_id = p.purchase_id"
                    " WHERE l.dev_account = ? AND f.refund_id IS NULL",
                    (dev,)).fetchone()
                refunded_count = int(self._conn.execute(
                    "SELECT COUNT(*) FROM apimarket_refunds"
                    " WHERE dev_account = ?", (dev,)).fetchone()[0])
                balance, known = self._seller_balance(dev)
                liability = int(open_rows[1])
                shortfall = liability - balance
                if shortfall < 0:
                    shortfall = 0
                rows.append({
                    "dev_account": dev,
                    "listing_count": listing_count,
                    "open_purchases": int(open_rows[0]),
                    "refunded_purchases": refunded_count,
                    "refundable_liability": liability,
                    "balance": balance,
                    "balance_known": known,
                    "shortfall": shortfall,
                    "covered": shortfall == 0,
                })
        return {"dev_account": dev_account,
                "seller_count": len(rows),
                "total_liability": sum(r["refundable_liability"]
                                       for r in rows),
                "total_shortfall": sum(r["shortfall"] for r in rows),
                "at_risk_count": sum(1 for r in rows
                                     if r["shortfall"] > 0),
                "disclaimer": self.disclaimer,
                "rows": rows}

    def api_seller_quality(self, dev_account=None):
        """Seller-side rating quality scorecard (criteria
        AC-AMQL1..AC-AMQL8 pre-registered in the R2117 explore-queue
        row BEFORE this code existed).

        The reputation surface was scattered across three faces:
        dev_profile carries a cross-listing average with no shape,
        api_seller_inbox carries only the unanswered rows, and
        api_ratings / api_rating_replies open one listing at a time.
        So no face answered "what shape is my reputation, which shelf
        drags it, and what share of ratings has a reply" - a seller
        with N listings had to open N faces and merge by hand, and an
        operator could not see which live shelf is being dragged down
        by low ratings.

        This face merges them once: a five-bucket star distribution,
        the average through the one effective-value seam (a rating
        revision moves exactly one bucket and never re-derives from
        the original stamp), reply coverage, and one quality row per
        listing. Retirement does not erase the record (a retired
        shelf keeps its rows and its ratings) but low_rated_count
        counts live shelves only - a shelf nobody can buy no longer
        costs a buyer anything. The row set authority is the listing
        table (dense: every listing the seller owns appears, with a
        zero-rating row for shelves nobody rated yet), ordered by
        listing_id.

        The account shape gate is prefix-only by the truthful
        R2077/R2078 finding and runs before any read - a prefix-valid
        account with no listings gets an honest empty envelope. Pure
        read: zero row mutations and zero token movement. The
        envelope carries the resident non-advisory disclaimer."""
        if dev_account is not None:
            if not str(dev_account or "").startswith("usr:"):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            if dev_account is None:
                owner_rows = self._conn.execute(
                    "SELECT DISTINCT dev_account"
                    " FROM apimarket_listings"
                    " ORDER BY dev_account").fetchall()
            else:
                owner_rows = self._conn.execute(
                    "SELECT DISTINCT dev_account"
                    " FROM apimarket_listings"
                    " WHERE dev_account = ?", (str(dev_account),)
                ).fetchall()
            sellers = [str(r[0]) for r in owner_rows]
            rows = []
            for dev in sellers:
                listing_rows = self._conn.execute(
                    "SELECT listing_id, listing_key, title, description"
                    " FROM apimarket_listings WHERE dev_account = ?"
                    " ORDER BY listing_id", (dev,)).fetchall()
                for lr in listing_rows:
                    listing_id = int(lr[0])
                    title = self._metadata_state(
                        listing_id, lr[2], lr[3])[0]
                    retired = self._cycle_state(listing_id)[1]
                    ratings = self._conn.execute(
                        "SELECT r.rating_id, r.stars,"
                        " (SELECT COUNT(*) FROM"
                        "  apimarket_rating_replies p"
                        "  WHERE p.rating_id = r.rating_id)"
                        " FROM apimarket_ratings r"
                        " WHERE r.listing_id = ?"
                        " ORDER BY r.rating_id", (listing_id,)).fetchall()
                    buckets = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
                    star_total = 0
                    answered = 0
                    lowest = None
                    for rating in ratings:
                        stars = self._effective_stars(
                            int(rating[0]), int(rating[1]))
                        key = str(stars)
                        buckets[key] = buckets.get(key, 0) + 1
                        star_total += stars
                        if int(rating[2]) > 0:
                            answered += 1
                        if lowest is None or stars < lowest:
                            lowest = stars
                    count = len(ratings)
                    rows.append({
                        "listing_id": listing_id,
                        "listing_key": lr[1],
                        "title": title,
                        "retired": bool(retired),
                        "rating_count": count,
                        "rating_avg": (float(star_total) / count
                                       if count else 0.0),
                        "unanswered_count": count - answered,
                        "reply_count": answered,
                        "lowest_stars": lowest,
                        "star_distribution": dict(
                            (k, buckets[k]) for k in sorted(buckets)),
                    })
        total_count = sum(r["rating_count"] for r in rows)
        total_replies = sum(r["reply_count"] for r in rows)
        distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for row in rows:
            for key in distribution:
                distribution[key] = (distribution[key]
                                     + row["star_distribution"].get(key, 0))
        star_sum = sum(int(k) * distribution[k] for k in distribution)
        low_rated = sum(
            1 for r in rows
            if not r["retired"] and r["rating_count"] >= 2
            and r["rating_avg"] <= 2.5)
        return {"dev_account": dev_account,
                "seller_count": len(sellers),
                "listing_count": len(rows),
                "rating_count": total_count,
                "reply_count": total_replies,
                "unanswered_count": total_count - total_replies,
                "reply_coverage": (round(float(total_replies)
                                         / total_count, 4)
                                   if total_count else None),
                "rating_avg": (float(star_sum) / total_count
                               if total_count else 0.0),
                "star_distribution": distribution,
                "low_rated_count": low_rated,
                "disclaimer": self.disclaimer,
                "rows": rows}

    def _seller_balance(self, dev_account):
        """Live ledger balance for a seller, honest about absence.

        apimarket owns its own sqlite file, so the balance can only be
        read through the ledger face (reference, never a second
        bookkeeping copy). An account the ledger never saw is not an
        error here - it is a zero balance with balance_known False."""
        try:
            bal = self.led.balance(dev_account)
        except Exception:
            return 0, False
        if not isinstance(bal, dict):
            return 0, False
        try:
            return int(bal.get("balance", 0)), True
        except (TypeError, ValueError):
            return 0, False

    def api_seller_ledger(self, dev_account, limit=None):
        """Seller settlement statement (criteria AC-AMLG1..AC-AMLG8
        pre-registered in the R2126 explore-queue row BEFORE this code
        existed).

        The market answers a seller's gross rows (api_sales), monthly
        cash (api_revenue_months), lifetime aggregates (dev_profile,
        api_market_stats) and refund exposure (api_refund_exposure), but
        no face answered the two questions a seller actually asks:
        "how much money do I have right now" and "which ledger entries
        produced it". ledger.bill is the only face that renders
        per-account entries, and it had zero product consumers.

        This face joins the live account balance (single seam:
        _seller_balance, the same helper refund_api and
        api_refund_exposure already trust; no second bookkeeping copy)
        with that account's entries, newest first. Limit truncates the
        OLDEST tail, so the most recent movement is always visible; a
        limit above the cap clamps instead of rejecting, while a
        non-int / bool / sub-one limit fails closed. An account the
        ledger never saw is not an error: balance 0 with balance_known
        False and an empty statement. Pure read: zero row mutations and
        zero token movement. The envelope carries the resident
        non-advisory disclaimer."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        if limit is None:
            limit = 50
        else:
            if (isinstance(limit, bool) or not isinstance(limit, int)
                    or limit < 1):
                raise ApiMarketError(E_AM_BAD_ARGS, "limit=%r" % (limit,))
            if limit > 500:
                limit = 500
        balance, known = self._seller_balance(dev_account)
        entries = []
        try:
            bill = self.led.bill(dev_account, limit)
        except Exception:
            bill = None
        if isinstance(bill, dict):
            raw = bill.get("items")
            if isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    try:
                        amount = int(item.get("amount", 0))
                    except (TypeError, ValueError):
                        amount = 0
                    row = {
                        "tx_id": str(item.get("tx_id", "")),
                        "ts_utc": item.get("ts_utc"),
                        "type": item.get("type"),
                        "action": item.get("action"),
                        "ref": item.get("ref"),
                        "ref_type": item.get("ref_type"),
                        "direction": item.get("direction"),
                        "amount": amount,
                        "memo": item.get("memo"),
                        "source_ai": bool(item.get("source_ai")),
                    }
                    if item.get("source_ai") and "ai_label" in item:
                        row["ai_label"] = item.get("ai_label")
                    entries.append(row)
        credit_total = sum(e["amount"] for e in entries
                           if e["direction"] == "credit")
        debit_total = sum(e["amount"] for e in entries
                          if e["direction"] == "debit")
        return {"dev_account": str(dev_account),
                "balance": balance,
                "balance_known": known,
                "entry_count": len(entries),
                "credit_total": credit_total,
                "debit_total": debit_total,
                "net": credit_total - debit_total,
                "limit": limit,
                "disclaimer": self.disclaimer,
                "entries": entries}

    def api_buyer_ledger(self, buyer_id, limit=None):
        """Buyer settlement statement (criteria AC-AMLGB1..AC-AMLGB8
        pre-registered in the R2128 explore-queue row BEFORE this code
        existed).

        R2126 gave the seller a statement; the buyer side still had no
        face answering "how much money do I have right now and which
        ledger entries produced it". A buyer carries row faces
        (api_library), cash months (api_buyer_months) and lifetime
        aggregates (api_buyer_profile), yet the ledger movements a
        purchase debits and a refund credits had zero product
        consumers. The seam is the same one the seller statement
        trusts - _seller_balance reads any usr: account - so no second
        bookkeeping copy exists. Limit truncates the OLDEST tail (the
        newest movement stays visible), an over-cap limit clamps, and a
        non-int / bool / sub-one limit fails closed. An account the
        ledger never saw is not an error: balance 0 with
        balance_known False and an empty statement. Pure read: zero
        row mutations and zero token movement."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        if limit is None:
            limit = 50
        else:
            if (isinstance(limit, bool) or not isinstance(limit, int)
                    or limit < 1):
                raise ApiMarketError(E_AM_BAD_ARGS, "limit=%r" % (limit,))
            if limit > 500:
                limit = 500
        balance, known = self._seller_balance(buyer_id)
        entries = []
        try:
            bill = self.led.bill(buyer_id, limit)
        except Exception:
            bill = None
        if isinstance(bill, dict):
            raw = bill.get("items")
            if isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    try:
                        amount = int(item.get("amount", 0))
                    except (TypeError, ValueError):
                        amount = 0
                    row = {
                        "tx_id": str(item.get("tx_id", "")),
                        "ts_utc": item.get("ts_utc"),
                        "type": item.get("type"),
                        "action": item.get("action"),
                        "ref": item.get("ref"),
                        "ref_type": item.get("ref_type"),
                        "direction": item.get("direction"),
                        "amount": amount,
                        "memo": item.get("memo"),
                        "source_ai": bool(item.get("source_ai")),
                    }
                    if item.get("source_ai") and "ai_label" in item:
                        row["ai_label"] = item.get("ai_label")
                    entries.append(row)
        credit_total = sum(e["amount"] for e in entries
                           if e["direction"] == "credit")
        debit_total = sum(e["amount"] for e in entries
                          if e["direction"] == "debit")
        return {"buyer_id": str(buyer_id),
                "balance": balance,
                "balance_known": known,
                "entry_count": len(entries),
                "credit_total": credit_total,
                "debit_total": debit_total,
                "net": credit_total - debit_total,
                "limit": limit,
                "disclaimer": self.disclaimer,
                "entries": entries}

    # -- pre-purchase Q&A (R2118) ---------------------------------------------

    def ask_question(self, buyer_id, listing_id, text):
        """Buyer-side pre-purchase question door (AC-AMQA1/AC-AMQA2,
        pre-registered in the R2118 explore-queue row BEFORE this
        code existed).

        Every trust face on this market is post-purchase: ratings,
        rating revisions, seller replies, refunds and the seller
        inbox all require a sale first, so a resident deciding
        whether to buy had no way to ask the seller anything and a
        seller's answer could never be seen by the next buyer. One
        append-only question row per call - the text is stored
        verbatim (stripped) and never rewritten.

        Gate order pinned by AC-AMQA2: account shape, listing-id
        shape, listing existence, retired state, then text shape
        (empty, over 500 chars, or carrying control characters).
        Every refusal is fail-closed with zero rows written."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        if (not isinstance(listing_id, int) or isinstance(listing_id, bool)
                or listing_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(listing_id))
        with self._lock:
            row = self._require_listing(listing_id)
            if self._delisted_utc(listing_id) is not None:
                raise ApiMarketError(E_AM_DELISTED, str(listing_id))
            if not isinstance(text, str):
                raise ApiMarketError(E_AM_BAD_QUESTION,
                                     "text must be str")
            body = text.strip()
            if (not body or len(body) > 500
                    or any(ord(ch) < 32 or ord(ch) == 127
                           for ch in body)):
                raise ApiMarketError(E_AM_BAD_QUESTION, str(text)[:40])
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_questions (listing_id,"
                    " buyer_id, question_text, asked_utc)"
                    " VALUES (?,?,?,?)",
                    (listing_id, buyer_id, body, stamp))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"question_id": cur.lastrowid, "listing_id": listing_id,
                "dev_account": str(row[1]), "buyer_id": buyer_id,
                "question_text": body, "asked_utc": stamp,
                "answered": False, "disclaimer": self.disclaimer}

    def answer_question(self, dev_account, question_id, text):
        """Seller-side answer door on one question (AC-AMQA3).

        Exactly one append-only answer per question and only the
        seller who owns the questioned listing may write it. The
        first stamp is never rewritten: a second answer answers
        E_AM_ALREADY_ANSWERED with zero new rows, and the question
        row itself is never touched.

        Gate order pinned by AC-AMQA3: account shape, question-id
        shape, answer text shape, question existence, ownership,
        already-answered state."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        if (not isinstance(question_id, int) or isinstance(question_id, bool)
                or question_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(question_id))
        if not isinstance(text, str):
            raise ApiMarketError(E_AM_BAD_REPLY, "text must be str")
        body = text.strip()
        if (not body or len(body) > 500
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in body)):
            raise ApiMarketError(E_AM_BAD_REPLY, str(text)[:40])
        with self._lock:
            row = self._conn.execute(
                "SELECT listing_id FROM apimarket_questions"
                " WHERE question_id = ?", (question_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_QUESTION,
                                     str(question_id))
            listing_id = int(row[0])
            owner = self._conn.execute(
                "SELECT dev_account FROM apimarket_listings"
                " WHERE listing_id = ?", (listing_id,)).fetchone()
            if owner is None or owner[0] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, question_id))
            dup = self._conn.execute(
                "SELECT answer_id FROM apimarket_answers"
                " WHERE question_id = ?", (question_id,)).fetchone()
            if dup is not None:
                raise ApiMarketError(E_AM_ALREADY_ANSWERED,
                                     str(question_id))
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_answers (question_id,"
                    " listing_id, dev_account, answer_text, answered_utc)"
                    " VALUES (?,?,?,?,?)",
                    (question_id, listing_id, dev_account, body, stamp))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ApiMarketError(E_AM_ALREADY_ANSWERED,
                                     str(question_id))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"answer_id": cur.lastrowid, "question_id": question_id,
                "listing_id": listing_id, "dev_account": dev_account,
                "answer_text": body, "answered_utc": stamp,
                "disclaimer": self.disclaimer}

    def api_listing_qna(self, listing_id):
        """Public Q&A thread of one listing (AC-AMQA4).

        Ten-key envelope with eight-key rows, ordered as a total
        order on (asked_utc, question_id) so a double run is
        byte-identical and the oldest question is always first. A
        retired listing keeps its whole thread readable - retirement
        hides the shelf from the board, it never erases what buyers
        and the seller already said. Pure read: zero row mutations
        and zero token movement."""
        if (not isinstance(listing_id, int) or isinstance(listing_id, bool)
                or listing_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(listing_id))
        with self._lock:
            row = self._require_listing(listing_id)
            listing_key = self._conn.execute(
                "SELECT listing_key, title, description"
                " FROM apimarket_listings WHERE listing_id = ?",
                (listing_id,)).fetchone()
            title = self._metadata_state(
                listing_id, listing_key[1], listing_key[2])[0]
            retired = self._delisted_utc(listing_id) is not None
            raw = self._conn.execute(
                "SELECT q.question_id, q.buyer_id, q.question_text,"
                " q.asked_utc, a.answer_text, a.answered_utc,"
                " a.dev_account, a.answer_id"
                " FROM apimarket_questions q"
                " LEFT JOIN apimarket_answers a"
                " ON a.question_id = q.question_id"
                " WHERE q.listing_id = ?"
                " ORDER BY q.asked_utc, q.question_id",
                (listing_id,)).fetchall()
            questions = [{
                "question_id": int(r[0]),
                "buyer_id": r[1],
                "question_text": r[2],
                "asked_utc": r[3],
                "answered": r[4] is not None,
                "answer_text": (None if r[4] is None
                                else self._effective_answer(int(r[7]),
                                                            r[4])),
                "answered_utc": r[5],
                "dev_account": r[6],
            } for r in raw]
        answered = sum(1 for q in questions if q["answered"])
        oldest = None
        for q in questions:
            if not q["answered"]:
                oldest = q["asked_utc"]
                break
        return {"listing_id": listing_id,
                "listing_key": listing_key[0],
                "title": title,
                "retired": bool(retired),
                "question_count": len(questions),
                "answered_count": answered,
                "unanswered_count": len(questions) - answered,
                "oldest_unanswered_utc": oldest,
                "disclaimer": self.disclaimer,
                "questions": questions}

    def api_seller_questions(self, dev_account):
        """Seller-side unanswered-question queue (AC-AMQA5).

        The mirror of api_seller_inbox for the pre-purchase side:
        api_listing_qna opens one shelf at a time, so a seller with
        N listings had to open N threads and count the gaps by
        hand. This face merges every listing of the seller and
        returns ONLY the questions still waiting, oldest debt
        first, so answering one drains the queue without rewriting
        any row. Retired shelves keep their debt (the answer is
        still owed to the buyer). Strict seller isolation; a
        prefix-valid account with no listings gets an honest empty
        envelope. Pure read, zero token movement."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            listing_rows = self._conn.execute(
                "SELECT listing_id, listing_key, title, description"
                " FROM apimarket_listings WHERE dev_account = ?"
                " ORDER BY listing_id", (dev_account,)).fetchall()
            totals = self._conn.execute(
                "SELECT COUNT(*), SUM(CASE WHEN a.answer_id IS NOT NULL"
                " THEN 1 ELSE 0 END)"
                " FROM apimarket_questions q"
                " JOIN apimarket_listings l ON l.listing_id = q.listing_id"
                " LEFT JOIN apimarket_answers a"
                " ON a.question_id = q.question_id"
                " WHERE l.dev_account = ?", (dev_account,)).fetchone()
            total = int(totals[0] or 0)
            answered = int(totals[1] or 0)
            raw = self._conn.execute(
                "SELECT q.question_id, q.listing_id, l.listing_key,"
                " l.title, l.description, q.buyer_id,"
                " q.question_text, q.asked_utc"
                " FROM apimarket_questions q"
                " JOIN apimarket_listings l ON l.listing_id = q.listing_id"
                " LEFT JOIN apimarket_answers a"
                " ON a.question_id = q.question_id"
                " WHERE l.dev_account = ? AND a.answer_id IS NULL"
                " ORDER BY q.asked_utc, q.question_id",
                (dev_account,)).fetchall()
            rows = []
            for r in raw:
                rows.append({
                    "question_id": int(r[0]),
                    "listing_id": int(r[1]),
                    "listing_key": r[2],
                    "title": self._metadata_state(
                        int(r[1]), r[3], r[4])[0],
                    "buyer_id": r[5],
                    "question_text": r[6],
                    "asked_utc": r[7],
                })
        return {"dev_account": dev_account,
                "listing_count": len(listing_rows),
                "total_question_count": total,
                "answered_count": answered,
                "unanswered_count": total - answered,
                "oldest_unanswered_utc": (rows[0]["asked_utc"]
                                          if rows else None),
                "disclaimer": self.disclaimer,
                "rows": rows}

    def api_buyer_questions(self, buyer_id):
        """Buyer-side question history across every listing
        (AC-AMBQ1..AC-AMBQ5, pre-registered in the R2119 explore-queue
        row BEFORE this code existed).

        R2118 opened the pre-purchase Q&A doors, but the asking side
        could only read one thread at a time (api_listing_qna) while
        the answering side already had a merged queue
        (api_seller_questions). A resident who asked on N listings had
        to open N threads and merge by hand to answer "what did I ask,
        what is still open, what did the seller say back".

        This face merges every question of one buyer into a single time
        line (total order on asked_utc then question_id): open and
        answered rows live side by side, the title is read through the
        one metadata revision seam, and a retired listing keeps its
        history readable. Strict buyer isolation; a prefix-valid
        account with no questions gets an honest empty envelope. Pure
        read: zero row mutations and zero token movement."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        with self._lock:
            raw = self._conn.execute(
                "SELECT q.question_id, q.listing_id, l.listing_key,"
                " l.title, l.description, l.dev_account,"
                " q.question_text, q.asked_utc,"
                " a.answer_text, a.answered_utc, a.answer_id"
                " FROM apimarket_questions q"
                " JOIN apimarket_listings l ON l.listing_id = q.listing_id"
                " LEFT JOIN apimarket_answers a"
                " ON a.question_id = q.question_id"
                " WHERE q.buyer_id = ?"
                " ORDER BY q.asked_utc, q.question_id",
                (buyer_id,)).fetchall()
            rows = []
            listings = set()
            for r in raw:
                listings.add(int(r[1]))
                rows.append({
                    "question_id": int(r[0]),
                    "listing_id": int(r[1]),
                    "listing_key": r[2],
                    "title": self._metadata_state(
                        int(r[1]), r[3], r[4])[0],
                    "dev_account": r[5],
                    "question_text": r[6],
                    "asked_utc": r[7],
                    "answered": r[8] is not None,
                    "answer_text": (None if r[8] is None
                                    else self._effective_answer(
                                        int(r[10]), r[8])),
                    "answered_utc": r[9],
                })
        answered = sum(1 for row in rows if row["answered"])
        oldest_open = None
        for row in rows:
            if not row["answered"]:
                oldest_open = row["asked_utc"]
                break
        return {"buyer_id": buyer_id,
                "listing_count": len(listings),
                "question_count": len(rows),
                "answered_count": answered,
                "unanswered_count": len(rows) - answered,
                "oldest_open_utc": oldest_open,
                "disclaimer": self.disclaimer,
                "rows": rows}

    def api_seller_answers(self, dev_account):
        """Seller-side answered-question ledger across every listing
        (AC-AMSA1..AC-AMSA8, pre-registered in the R2120 explore-queue
        row BEFORE this code existed).

        api_seller_questions only proves the OPEN debt: its rows carry
        unanswered questions and the answered side is a single number.
        api_listing_qna opens one shelf at a time, so a seller who has
        answered on N listings had to open N threads and merge by hand
        to answer "what did I answer, what did I say, how long did each
        buyer wait". This face merges every ANSWERED question of one
        seller into a single time line (total order on answered_utc
        then question_id), reports the service-level latency in whole
        seconds (fastest / slowest / mean), reads the title through the
        one metadata revision seam, and keeps a retired listing's
        history readable. Strict seller isolation; a prefix-valid
        account with no answers gets an honest empty envelope. Pure
        read: zero row mutations and zero token movement."""

        def _seconds(earlier, later):
            fmt = "%Y-%m-%dT%H:%M:%SZ"
            start = datetime.datetime.strptime(str(earlier), fmt)
            end = datetime.datetime.strptime(str(later), fmt)
            return int((end - start).total_seconds())

        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            listing_rows = self._conn.execute(
                "SELECT listing_id FROM apimarket_listings"
                " WHERE dev_account = ? ORDER BY listing_id",
                (dev_account,)).fetchall()
            raw = self._conn.execute(
                "SELECT q.question_id, a.answer_id, q.listing_id,"
                " l.listing_key, l.title, l.description, q.buyer_id,"
                " q.question_text, q.asked_utc, a.answer_text,"
                " a.answered_utc"
                " FROM apimarket_answers a"
                " JOIN apimarket_questions q"
                " ON q.question_id = a.question_id"
                " JOIN apimarket_listings l ON l.listing_id = q.listing_id"
                " WHERE l.dev_account = ?"
                " ORDER BY a.answered_utc, q.question_id",
                (dev_account,)).fetchall()
            rows = []
            for r in raw:
                rows.append({
                    "question_id": int(r[0]),
                    "answer_id": int(r[1]),
                    "listing_id": int(r[2]),
                    "listing_key": r[3],
                    "title": self._metadata_state(
                        int(r[2]), r[4], r[5])[0],
                    "buyer_id": r[6],
                    "question_text": r[7],
                    "asked_utc": r[8],
                    "answer_text": self._effective_answer(int(r[1]), r[9]),
                    "answered_utc": r[10],
                    "response_seconds": _seconds(r[8], r[10]),
                })
            buyers = {row["buyer_id"] for row in rows}
            latencies = [row["response_seconds"] for row in rows]
        count = len(rows)
        return {"dev_account": dev_account,
                "listing_count": len(listing_rows),
                "answered_count": count,
                "buyer_count": len(buyers),
                "first_answered_utc": (rows[0]["answered_utc"]
                                       if rows else None),
                "latest_answered_utc": (rows[-1]["answered_utc"]
                                        if rows else None),
                "fastest_seconds": min(latencies) if latencies else None,
                "slowest_seconds": max(latencies) if latencies else None,
                "mean_seconds": ((sum(latencies) // count)
                                 if count else None),
                "disclaimer": self.disclaimer,
                "rows": rows}

    def revise_answer(self, dev_account, answer_id, text):
        """Seller-side answer revision door (pre-registered
        AC-AMAW1..AC-AMAW8 in the R2145 explore-queue claim row
        BEFORE this code existed).

        The answer face was write-once: one immutable row per
        question behind UNIQUE(question_id) and E_AM_ALREADY_ANSWERED
        forever, so an answer that named a stock level or a delivery
        window stayed welded to the shelf after the stock moved or
        the listing was repriced. Every other write-once axis grew a
        remedy door (price R2079, metadata R2083, supply R2095,
        rating R2094, reply R2143, provider identity R2136), which
        made the answer the last one without. Each revision appends
        one apimarket_answer_revisions row and never rewrites the
        base answer; the effective text is the newest revision, else
        the base stamp.

        Gate order pinned by AC-AMAW2: account shape, answer-id
        shape, text shape, existence, ownership, unchanged state.
        The unchanged gate compares against the EFFECTIVE text, so
        revising back to an earlier wording stays legal while a
        same-text revision answers E_AM_ANSWER_UNCHANGED with zero
        new rows. A retired listing keeps its answer leg revisable -
        retirement freezes the shelf, not the duty to answer
        (AC-AMAW4). Revising moves zero tokens and changes no
        answered/unanswered counter: a revision is not a new answer
        (AC-AMAW6)."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        if (not isinstance(answer_id, int) or isinstance(answer_id, bool)
                or answer_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(answer_id))
        if not isinstance(text, str):
            raise ApiMarketError(E_AM_BAD_REPLY, "text must be str")
        body = text.strip()
        if (not body or len(body) > 500
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in body)):
            raise ApiMarketError(E_AM_BAD_REPLY, str(text)[:40])
        with self._lock:
            row = self._conn.execute(
                "SELECT question_id, listing_id, dev_account,"
                " answer_text FROM apimarket_answers"
                " WHERE answer_id = ?", (answer_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_ANSWER,
                                     str(answer_id))
            if row[2] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, answer_id))
            question_id = int(row[0])
            listing_id = int(row[1])
            previous = self._effective_answer(answer_id, row[3])
            if body == previous:
                raise ApiMarketError(E_AM_ANSWER_UNCHANGED,
                                     "%s/%s" % (answer_id, body[:40]))
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_answer_revisions"
                    " (answer_id, question_id, listing_id, dev_account,"
                    " previous_text, answer_text, revised_utc)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (answer_id, question_id, listing_id, dev_account,
                     previous, body, stamp))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"revision_id": cur.lastrowid, "answer_id": answer_id,
                "question_id": question_id, "listing_id": listing_id,
                "dev_account": dev_account,
                "previous_text": previous, "answer_text": body,
                "revised_utc": stamp, "disclaimer": self.disclaimer}

    def _effective_answer(self, answer_id, base_text):
        """Effective answer text: the newest append-only revision,
        else the immutable base stamp (AC-AMAW3 single seam for
        api_listing_qna, api_buyer_questions and api_seller_answers).
        Caller holds the lock."""
        row = self._conn.execute(
            "SELECT answer_text FROM apimarket_answer_revisions"
            " WHERE answer_id = ? ORDER BY revision_id DESC LIMIT 1",
            (answer_id,)).fetchone()
        return base_text if row is None else row[0]

    def api_answer_history(self, answer_id):
        """Answer revision history surface (AC-AMAW5): the immutable
        base wording, every append-only revision in order, the
        effective text and the revision count, alongside the question
        the answer belongs to. An unknown answer answers
        E_AM_UNKNOWN_ANSWER and a bad id answers E_AM_BAD_ARGS before
        any read. Pure read: zero row mutations, zero tokens."""
        if (not isinstance(answer_id, int) or isinstance(answer_id, bool)
                or answer_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(answer_id))
        with self._lock:
            row = self._conn.execute(
                "SELECT question_id, listing_id, dev_account,"
                " answer_text, answered_utc FROM apimarket_answers"
                " WHERE answer_id = ?", (answer_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_ANSWER,
                                     str(answer_id))
            question_id = int(row[0])
            question = self._conn.execute(
                "SELECT buyer_id, question_text FROM apimarket_questions"
                " WHERE question_id = ?", (question_id,)).fetchone()
            revs = self._conn.execute(
                "SELECT revision_id, previous_text, answer_text,"
                " revised_utc FROM apimarket_answer_revisions"
                " WHERE answer_id = ? ORDER BY revision_id",
                (answer_id,)).fetchall()
            base = row[3]
            effective = base if not revs else revs[-1][2]
            buyer = "" if question is None else question[0]
            asked = "" if question is None else question[1]
        return {"answer_id": answer_id, "question_id": question_id,
                "listing_id": int(row[1]), "dev_account": row[2],
                "buyer_id": buyer, "question_text": asked,
                "effective_text": effective, "base_text": base,
                "revision_count": len(revs),
                "latest_revised_utc": (None if not revs
                                       else revs[-1][3]),
                "disclaimer": self.disclaimer,
                "revisions": [{"revision_id": int(x[0]),
                               "previous_text": x[1],
                               "answer_text": x[2],
                               "revised_utc": x[3]} for x in revs]}

    def _provider_state(self, dev_account):
        """Effective provider identity (AC-AMPV4) - one seam for the
        identity read face, the public display layer and the revision
        door. The base provider row is append-only, so the effective
        pair is the base pair overlaid by the NEWEST revision row;
        with zero revisions this returns exactly the base values, so
        every pre-existing caller keeps its byte-identical output.
        Callers hold the write lock."""
        row = self._conn.execute(
            "SELECT provider_name, credit_code, registered_utc"
            " FROM apimarket_providers WHERE dev_account = ?",
            (dev_account,)).fetchone()
        if row is None:
            return None
        rev = self._conn.execute(
            "SELECT provider_name, credit_code, revised_utc"
            " FROM apimarket_provider_revisions WHERE dev_account = ?"
            " ORDER BY revision_id DESC LIMIT 1",
            (dev_account,)).fetchone()
        count = self._conn.execute(
            "SELECT COUNT(*) FROM apimarket_provider_revisions"
            " WHERE dev_account = ?", (dev_account,)).fetchone()[0]
        return {"base_provider_name": row[0],
                "base_credit_code": row[1],
                "registered_utc": row[2],
                "provider_name": rev[0] if rev is not None else row[0],
                "credit_code": rev[1] if rev is not None else row[1],
                "revision_count": int(count),
                "latest_revised_utc": (rev[2] if rev is not None
                                       else None)}

    def revise_provider(self, dev_account, provider_name=None,
                        credit_code=None):
        """Provider identity revision door (AC-AMPV1..AC-AMPV3,
        pre-registered in the R2136 explore-queue row BEFORE this code
        existed).

        register_provider was write-once per developer: one row behind
        UNIQUE(dev_account) with no update and no delete surface, while
        the unified social credit code is the disclosure field the
        public layer publishes verbatim. A single wrong character at
        registration was therefore a permanent mis-disclosure with no
        remedy - the same dead end that price (R2079), metadata
        (R2083), supply (R2095) and rating (R2094) each had before
        their revision leg landed.

        This is that leg: exactly one append-only
        apimarket_provider_revisions row per call, the base provider
        row never rewritten. Omitted fields carry the current
        effective value into the row, so every row stores the full
        effective pair. Gate order pinned by AC-AMPV2: account shape,
        registration existence, field shape, then no-change judged
        against the effective value (so a revise-back to an earlier
        value is legal while an identical consecutive call is
        refused). Every refusal writes zero rows and moves zero
        tokens."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            state = self._provider_state(dev_account)
            if state is None:
                raise ApiMarketError(E_AM_PROVIDER_UNREGISTERED,
                                     dev_account)
            name = None
            if provider_name is not None:
                if not isinstance(provider_name, str):
                    raise ApiMarketError(E_AM_BAD_PROVIDER,
                                         "provider name shape")
                name = provider_name.strip()
                if not name or len(name) > _PROVIDER_NAME_MAX:
                    raise ApiMarketError(E_AM_BAD_PROVIDER,
                                         "provider name shape")
            code = None
            if credit_code is not None:
                if not isinstance(credit_code, str):
                    raise ApiMarketError(E_AM_BAD_PROVIDER,
                                         "credit code shape")
                code = credit_code.strip()
                if not code or len(code) > _PROVIDER_CODE_MAX:
                    raise ApiMarketError(E_AM_BAD_PROVIDER,
                                         "credit code shape")
            if name is None and code is None:
                raise ApiMarketError(E_AM_BAD_PROVIDER,
                                     "no field to revise")
            new_name = state["provider_name"] if name is None else name
            new_code = state["credit_code"] if code is None else code
            if (new_name == state["provider_name"]
                    and new_code == state["credit_code"]):
                raise ApiMarketError(E_AM_PROVIDER_UNCHANGED,
                                     dev_account)
            stamp = _now_utc()
            cur = self._conn.execute(
                "INSERT INTO apimarket_provider_revisions"
                " (dev_account, previous_provider_name,"
                " previous_credit_code, provider_name, credit_code,"
                " revised_utc) VALUES (?,?,?,?,?,?)",
                (dev_account, state["provider_name"],
                 state["credit_code"], new_name, new_code, stamp))
            revision_id = cur.lastrowid
        return {"revision_id": revision_id, "dev_account": dev_account,
                "previous_provider_name": state["provider_name"],
                "previous_credit_code": state["credit_code"],
                "provider_name": new_name, "credit_code": new_code,
                "revised_utc": stamp}

    def register_provider(self, dev_account, provider_name, credit_code):
        """Real-name provider registration for the distribution-duty
        face (AC-AMPI1..AC-AMPI2, pre-registered in the R2124
        explore-queue row BEFORE this code existed).

        The marketplace has always identified a seller by a bare
        dev_account string, so nothing answered "who is behind this
        shelf". This is the append-only real-name layer: exactly one
        row per developer, name and unified social credit code held
        trimmed and non-empty, no update and no delete surface. Gate
        order is account shape, name shape, credit shape, registry
        (the existing dev-key read face), then duplicate - so a
        refusal stores zero rows. Registration moves no tokens."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        name = str(provider_name or "").strip()
        if not name or len(name) > _PROVIDER_NAME_MAX:
            raise ApiMarketError(E_AM_BAD_PROVIDER, "provider name required")
        code = str(credit_code or "").strip()
        if not code or len(code) > _PROVIDER_CODE_MAX:
            raise ApiMarketError(E_AM_BAD_PROVIDER, "credit code required")
        with self._lock:
            if not self._is_registered_dev(dev_account):
                raise ApiMarketError(E_AM_NOT_DEV, dev_account)
            row = self._conn.execute(
                "SELECT provider_id FROM apimarket_providers"
                " WHERE dev_account = ?", (dev_account,)).fetchone()
            if row is not None:
                raise ApiMarketError(E_AM_PROVIDER_DUP, dev_account)
            stamp = _now_utc()
            self._conn.execute(
                "INSERT INTO apimarket_providers"
                " (dev_account, provider_name, credit_code,"
                " registered_utc) VALUES (?, ?, ?, ?)",
                (dev_account, name, code, stamp))
        return {"dev_account": dev_account, "provider_name": name,
                "credit_code": code, "registered_utc": stamp}

    def api_provider_identity(self, dev_account):
        """Provider identity read face (AC-AMPI3). A registered
        developer gets the four registered fields; an in-shape
        account with no registration gets an honest empty envelope
        instead of an error (a provider who has not registered yet
        is a normal state, not a fault). Pure read."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            state = self._provider_state(dev_account)
        if state is None:
            return {"dev_account": dev_account, "registered": False,
                    "provider_name": None, "credit_code": None,
                    "registered_utc": None, "disclosure_ok": False,
                    "disclaimer": self.disclaimer}
        return {"dev_account": dev_account, "registered": True,
                "provider_name": state["provider_name"],
                "credit_code": state["credit_code"],
                "registered_utc": state["registered_utc"],
                "disclosure_ok": True,
                "disclaimer": self.disclaimer}

    def api_provider_history(self, dev_account):
        """Provider identity history (AC-AMPV5) - the return leg the
        registration door never had: which identity is published right
        now, what it was registered as, and every revision in order.
        An in-shape account with no registration gets an honest empty
        envelope (a provider who has not registered yet is a normal
        state, not a fault). Pure read."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            state = self._provider_state(dev_account)
            if state is None:
                return {"dev_account": dev_account, "registered": False,
                        "provider_name": None, "credit_code": None,
                        "base_provider_name": None,
                        "base_credit_code": None, "registered_utc": None,
                        "revision_count": 0,
                        "latest_revised_utc": None, "revisions": [],
                        "disclaimer": self.disclaimer}
            rows = self._conn.execute(
                "SELECT revision_id, previous_provider_name,"
                " previous_credit_code, provider_name, credit_code,"
                " revised_utc FROM apimarket_provider_revisions"
                " WHERE dev_account = ? ORDER BY revision_id",
                (dev_account,)).fetchall()
        return {"dev_account": dev_account, "registered": True,
                "provider_name": state["provider_name"],
                "credit_code": state["credit_code"],
                "base_provider_name": state["base_provider_name"],
                "base_credit_code": state["base_credit_code"],
                "registered_utc": state["registered_utc"],
                "revision_count": state["revision_count"],
                "latest_revised_utc": state["latest_revised_utc"],
                "disclaimer": self.disclaimer,
                "revisions": [
                    {"revision_id": r[0],
                     "previous_provider_name": r[1],
                     "previous_credit_code": r[2],
                     "provider_name": r[3],
                     "credit_code": r[4],
                     "revised_utc": r[5]} for r in rows]}

    def api_public_listings(self):
        """Public display layer (AC-AMPI4) - the face an outside
        reader would see: one row per LIVE listing carrying the
        registered provider name and unified social credit code, the
        AIGC label, the current price, and the review state. An
        unregistered provider is shown honestly (null identity plus
        disclosure_ok false) rather than hidden. Review state is
        pending (no review row), approved or refused, and only a
        refusal carries its reason. Ordered by listing_id. Pure
        read."""
        live_sql = (
            "SELECT l.listing_id, l.dev_account, l.listing_key,"
            " l.title, l.description, l.token_price, l.ai_label,"
            " l.listed_utc FROM apimarket_listings l"
            " WHERE l.listing_id NOT IN (SELECT d.listing_id FROM"
            " apimarket_delistings d WHERE d.cycle ="
            " COALESCE((SELECT MAX(r.cycle) FROM"
            " apimarket_relistings r WHERE r.listing_id ="
            " d.listing_id), 1)) ORDER BY l.listing_id")
        with self._lock:
            rows = self._conn.execute(live_sql).fetchall()
            out = []
            for r in rows:
                listing_id = int(r[0])
                prov = self._provider_state(r[1])
                rev = self._current_review(listing_id)
                eff_title = self._metadata_state(
                    listing_id, r[3], r[4])[0]
                out.append({
                    "listing_id": listing_id,
                    "dev_account": r[1],
                    "listing_key": r[2],
                    "title": eff_title,
                    "token_price": self._current_price(
                        listing_id, int(r[5])),
                    "ai_label": int(r[6]),
                    "listed_utc": r[7],
                    "provider_name": (prov["provider_name"]
                                      if prov is not None else None),
                    "credit_code": (prov["credit_code"]
                                    if prov is not None else None),
                    "disclosure_ok": prov is not None,
                    "review_state": ({"approve": "approved",
                                      "refuse": "refused"}[rev[0]]
                                     if rev else "pending"),
                    "review_reason": (rev[1] if rev
                                      and rev[0] == "refuse" else None),
                    "reviewed_utc": (rev[2] if rev else None),
                })
        registered = [x for x in out if x["disclosure_ok"]]
        pending = [x for x in out if x["review_state"] == "pending"]
        return {"listing_count": len(out),
                "disclosure_ok_count": len(registered),
                "review_pending_count": len(pending),
                "disclaimer": self.disclaimer,
                "listings": out}

    def review_listing(self, listing_id, decision, reason=""):
        """Listing review gate (AC-AMPI5) - the platform side of the
        distribution duty: approve or refuse one live or retired
        listing with exactly one append-only row. A refusal must say
        why (a silent refusal is useless to the seller and to any
        later appeal); a repeat decision on the same listing is
        refused with zero new rows. No token moves here."""
        if decision not in ("approve", "refuse"):
            raise ApiMarketError(E_AM_BAD_DECISION, str(decision))
        text = str(reason or "").strip()
        if decision == "refuse" and not text:
            raise ApiMarketError(E_AM_BAD_REASON, str(listing_id))
        with self._lock:
            self._require_listing(listing_id)
            cycle = self._review_cycle(listing_id)
            row = self._conn.execute(
                "SELECT review_id FROM apimarket_reviews"
                " WHERE listing_id = ? AND cycle = ?",
                (listing_id, cycle)).fetchone()
            if row is not None:
                raise ApiMarketError(E_AM_ALREADY_REVIEWED,
                                     str(listing_id))
            stamp = _now_utc()
            self._conn.execute(
                "INSERT INTO apimarket_reviews"
                " (listing_id, decision, reason, reviewed_utc, cycle)"
                " VALUES (?, ?, ?, ?, ?)",
                (listing_id, decision, text, stamp, cycle))
        return {"listing_id": listing_id, "decision": decision,
                "reason": text, "reviewed_utc": stamp,
                "review_cycle": cycle}

    def resubmit_listing(self, dev_account, listing_id, note=""):
        """Seller-side re-submission door after a refusal (criteria
        AC-AMRC1..AC-AMRC8 pre-registered in the R2133 explore-queue
        row BEFORE this code existed).

        Before this door a refusal was terminal: apimarket_reviews
        carried UNIQUE(listing_id) and review_listing refused a
        repeat verdict, so a seller who fixed the description or
        supplied the missing qualification had to publish a brand
        new listing_key and lose that listing's purchases, ratings,
        repricing history and metadata history. This is the same
        dead end the retirement door had before the re-list cycle
        law (AC-AMRL1), so it is closed the same way: a refusal
        ends its cycle, a resubmission opens the next one, and the
        current verdict is the row of the current cycle.

        Gate order pinned by AC-AMRC2: account shape, listing
        shape/existence, ownership, the retired state, the current
        cycle's verdict (pending or approved cannot be
        resubmitted), then the duplicate resubmission. Every
        refusal writes zero rows and moves zero tokens."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        text = str(note or "").strip()
        with self._lock:
            listing = self._require_listing(listing_id)
            if listing[1] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, listing_id))
            _cycle, retired, _stamp = self._cycle_state(listing_id)
            if retired:
                raise ApiMarketError(E_AM_DELISTED, str(listing_id))
            cycle = self._review_cycle(listing_id)
            row = self._conn.execute(
                "SELECT decision FROM apimarket_reviews"
                " WHERE listing_id = ? AND cycle = ?",
                (listing_id, cycle)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_REVIEW_PENDING,
                                     str(listing_id))
            if row[0] != "refuse":
                raise ApiMarketError(E_AM_REVIEW_APPROVED,
                                     str(listing_id))
            dup = self._conn.execute(
                "SELECT resubmit_id FROM apimarket_review_resubmits"
                " WHERE listing_id = ? AND cycle = ?",
                (listing_id, cycle + 1)).fetchone()
            if dup is not None:
                raise ApiMarketError(E_AM_ALREADY_RESUBMITTED,
                                     str(listing_id))
            stamp = _now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO apimarket_review_resubmits"
                    " (listing_id, dev_account, cycle, note,"
                    " resubmitted_utc) VALUES (?,?,?,?,?)",
                    (listing_id, dev_account, cycle + 1, text, stamp))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            new_cycle = cycle + 1
        return {"listing_id": listing_id, "dev_account": dev_account,
                "cycle": new_cycle, "note": text,
                "state": "pending", "resubmitted_utc": stamp,
                "disclaimer": self.disclaimer}

    def api_seller_reviews(self, dev_account):
        """Seller-side review status face (AC-AMRC6). The operator
        had api_review_queue and the outside reader had
        api_public_listings, but a seller could not answer "which of
        my listings are waiting, which were refused and why". One
        row per listing of that seller (retired rows included, with
        the retirement flag), carrying the CURRENT review cycle and
        its verdict. Pure read: zero rows written, zero token
        movement."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        with self._lock:
            rows = self._conn.execute(
                "SELECT listing_id, listing_key, title, description,"
                " token_price FROM apimarket_listings"
                " WHERE dev_account = ? ORDER BY listing_id",
                (dev_account,)).fetchall()
            out = []
            for r in rows:
                listing_id = int(r[0])
                _c, retired, _s = self._cycle_state(listing_id)
                cycle = self._review_cycle(listing_id)
                rev = self._conn.execute(
                    "SELECT decision, reason, reviewed_utc FROM"
                    " apimarket_reviews WHERE listing_id = ?"
                    " AND cycle = ?", (listing_id, cycle)).fetchone()
                n_resub = self._conn.execute(
                    "SELECT COUNT(*) FROM"
                    " apimarket_review_resubmits WHERE listing_id = ?",
                    (listing_id,)).fetchone()[0]
                out.append({
                    "listing_id": listing_id,
                    "listing_key": r[1],
                    "title": self._metadata_state(
                        listing_id, r[2], r[3])[0],
                    "token_price": self._current_price(
                        listing_id, int(r[4])),
                    "delisted": retired,
                    "review_cycle": cycle,
                    "review_state": ({"approve": "approved",
                                      "refuse": "refused"}[rev[0]]
                                     if rev else "pending"),
                    "review_reason": (rev[1] if rev
                                      and rev[0] == "refuse" else None),
                    "reviewed_utc": (rev[2] if rev else None),
                    "resubmit_count": int(n_resub),
                })
        states = [x["review_state"] for x in out]
        return {"dev_account": dev_account,
                "listing_count": len(out),
                "pending_count": states.count("pending"),
                "approved_count": states.count("approved"),
                "refused_count": states.count("refused"),
                "resubmit_count": sum(x["resubmit_count"] for x in out),
                "disclaimer": self.disclaimer,
                "rows": out}

    def api_review_queue(self):
        """Unreviewed live listings, oldest first (AC-AMPI6). The
        operator's work queue for the review face: retired shelves
        are absent, and the pending count equals the public face's
        pending set so the two cannot drift. Pure read."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT l.listing_id, l.dev_account, l.listing_key,"
                " l.title, l.description, l.token_price, l.listed_utc"
                " FROM apimarket_listings l"
                " WHERE l.listing_id NOT IN (SELECT rv.listing_id FROM"
                " apimarket_reviews rv WHERE rv.cycle = COALESCE("
                "(SELECT MAX(rs.cycle) FROM"
                " apimarket_review_resubmits rs WHERE rs.listing_id ="
                " rv.listing_id), 1))"
                " AND l.listing_id NOT IN (SELECT d.listing_id FROM"
                " apimarket_delistings d WHERE d.cycle ="
                " COALESCE((SELECT MAX(r.cycle) FROM"
                " apimarket_relistings r WHERE r.listing_id ="
                " d.listing_id), 1))"
                " ORDER BY l.listed_utc, l.listing_id").fetchall()
            out = []
            for r in rows:
                listing_id = int(r[0])
                out.append({
                    "listing_id": listing_id,
                    "dev_account": r[1],
                    "listing_key": r[2],
                    "title": self._metadata_state(
                        listing_id, r[3], r[4])[0],
                    "token_price": self._current_price(
                        listing_id, int(r[5])),
                    "listed_utc": r[6],
                })
        return {"pending_count": len(out),
                "disclaimer": self.disclaimer,
                "rows": out}

    # -- post-sale claim domain ---------------------------------------------

    def open_claim(self, buyer_id, purchase_id, claim_text):
        """Buyer-side post-sale claim door (criteria AC-AMCL1..AC-AMCL8
        pre-registered in the R2129 explore-queue row BEFORE this code
        existed).

        The refund door fails closed when the seller already spent the
        proceeds (E_AM_REFUND_UNFUNDABLE, refuse-never-chase), and after
        that refusal the product had no surface at all: the buyer could
        not lodge the complaint anywhere and the seller had no queue of
        disputed purchases. This door writes exactly one append-only
        apimarket_claims row per purchase (UNIQUE on purchase_id) and
        stores the disputed price_paid with it, so a later repricing
        cannot rewrite the amount under dispute.

        Gate order pinned by AC-AMCL3: buyer account shape, purchase-id
        shape, claim text shape, purchase existence, ownership, the
        already-refunded state, then the duplicate claim. Every refusal
        writes zero rows and moves zero tokens.

        Status is never stored: a claim is open until a refund row
        exists for its purchase, at which point every read face reports
        refunded with zero rewriting (AC-AMCL2)."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        if (not isinstance(purchase_id, int) or isinstance(purchase_id, bool)
                or purchase_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(purchase_id))
        text = claim_text.strip() if isinstance(claim_text, str) else None
        if not text or len(text) > 500:
            raise ApiMarketError(E_AM_BAD_CLAIM,
                                 str(claim_text)[:40])
        with self._lock:
            row = self._conn.execute(
                "SELECT listing_id, buyer_id, price_paid"
                " FROM apimarket_purchases WHERE purchase_id = ?",
                (purchase_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_PURCHASE,
                                     str(purchase_id))
            listing_id = int(row[0])
            if row[1] != buyer_id:
                raise ApiMarketError(E_AM_NOT_BUYER,
                                     "%s/%s" % (buyer_id, purchase_id))
            if self._refund_stamp(purchase_id) is not None:
                raise ApiMarketError(E_AM_ALREADY_REFUNDED,
                                     str(purchase_id))
            seen = self._conn.execute(
                "SELECT claim_id FROM apimarket_claims"
                " WHERE purchase_id = ?", (purchase_id,)).fetchone()
            if seen is not None:
                raise ApiMarketError(E_AM_CLAIM_DUP, str(purchase_id))
            dev_account = self._require_listing(listing_id)[1]
            stamp = _now_utc()
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_claims (purchase_id,"
                    " listing_id, buyer_id, dev_account, price_paid,"
                    " claim_text, opened_utc) VALUES (?,?,?,?,?,?,?)",
                    (purchase_id, listing_id, buyer_id, dev_account,
                     int(row[2]), text, stamp))
            except sqlite3.IntegrityError:
                raise ApiMarketError(E_AM_CLAIM_DUP, str(purchase_id))
        return {"claim_id": cur.lastrowid, "purchase_id": purchase_id,
                "listing_id": listing_id, "buyer_id": buyer_id,
                "dev_account": dev_account, "price_paid": int(row[2]),
                "claim_text": text, "opened_utc": stamp,
                "status": "open", "disclaimer": self.disclaimer}

    def respond_claim(self, dev_account, claim_id, response_text):
        """Seller-side answer door for a post-sale claim (criteria
        AC-AMCR1..AC-AMCR8 pre-registered in the R2130 explore-queue row
        BEFORE this code existed).

        R2129 gave the buyer a claim door and both sides a queue, but the
        seller had no way to say anything: the only reply in the product
        was a refund, which fails closed when the proceeds are already
        spent. This door writes exactly one append-only
        apimarket_claim_responses row per claim (UNIQUE on claim_id) and
        never rewrites the claim or the response row, so an answer is
        evidence, not a status flag.

        Gate order pinned by AC-AMCR3: seller account shape, claim-id
        shape, response text shape, claim existence, ownership, the
        already-refunded state, then the duplicate answer. Every refusal
        writes zero rows and moves zero tokens. A refund landing after an
        answer still wins the derived status (refunded > answered >
        open)."""
        if not str(dev_account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        if (not isinstance(claim_id, int) or isinstance(claim_id, bool)
                or claim_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(claim_id))
        text = (response_text.strip()
                if isinstance(response_text, str) else None)
        if not text or len(text) > 500:
            raise ApiMarketError(E_AM_BAD_RESPONSE,
                                 str(response_text)[:40])
        with self._lock:
            row = self._conn.execute(
                "SELECT dev_account, purchase_id, listing_id"
                " FROM apimarket_claims WHERE claim_id = ?",
                (claim_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_CLAIM, str(claim_id))
            if row[0] != dev_account:
                raise ApiMarketError(E_AM_NOT_OWNER,
                                     "%s/%s" % (dev_account, claim_id))
            if self._refund_stamp(int(row[1])) is not None:
                raise ApiMarketError(E_AM_ALREADY_REFUNDED,
                                     str(claim_id))
            seen = self._conn.execute(
                "SELECT response_id FROM apimarket_claim_responses"
                " WHERE claim_id = ?", (claim_id,)).fetchone()
            if seen is not None:
                raise ApiMarketError(E_AM_CLAIM_ANSWERED, str(claim_id))
            stamp = _now_utc()
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_claim_responses (claim_id,"
                    " dev_account, response_text, replied_utc)"
                    " VALUES (?,?,?,?)",
                    (claim_id, dev_account, text, stamp))
            except sqlite3.IntegrityError:
                raise ApiMarketError(E_AM_CLAIM_ANSWERED, str(claim_id))
        return {"response_id": cur.lastrowid, "claim_id": claim_id,
                "purchase_id": int(row[1]),
                "listing_id": int(row[2]), "dev_account": dev_account,
                "response_text": text, "replied_utc": stamp,
                "status": "answered", "disclaimer": self.disclaimer}

    def withdraw_claim(self, buyer_id, claim_id):
        """Buyer-side withdrawal door that closes a post-sale claim
        (criteria AC-AMCW1..AC-AMCW8 pre-registered in the R2131
        explore-queue row BEFORE this code existed).

        After the R2129 claim door and the R2130 answer door the chain
        still had no closing act: a claim opened by mistake, settled
        off-platform, or fixed privately stayed open (or answered)
        forever and kept polluting the seller queue and the market-wide
        queue. A refund was the only way out, and the refund door fails
        closed once the seller spent the proceeds. This door writes
        exactly one append-only apimarket_claim_withdrawals row per
        claim (UNIQUE on claim_id) and never rewrites the claim or the
        seller answer, so a withdrawal is evidence, not a status flag.

        Gate order pinned by AC-AMCW3: buyer account shape, claim-id
        shape, claim existence, ownership (the claim's own buyer), the
        already-refunded state, then the duplicate withdrawal. Every
        refusal writes zero rows and moves zero tokens. A refund landing
        after a withdrawal still wins the derived status
        (refunded > withdrawn > answered > open)."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        if (not isinstance(claim_id, int) or isinstance(claim_id, bool)
                or claim_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(claim_id))
        with self._lock:
            row = self._conn.execute(
                "SELECT buyer_id, purchase_id, listing_id, dev_account,"
                " price_paid, claim_text, opened_utc"
                " FROM apimarket_claims WHERE claim_id = ?",
                (claim_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_CLAIM, str(claim_id))
            if row[0] != buyer_id:
                raise ApiMarketError(E_AM_NOT_BUYER,
                                     "%s/%s" % (buyer_id, claim_id))
            if self._refund_stamp(int(row[1])) is not None:
                raise ApiMarketError(E_AM_ALREADY_REFUNDED,
                                     str(claim_id))
            seen = self._conn.execute(
                "SELECT claim_id FROM apimarket_claim_withdrawals"
                " WHERE claim_id = ?", (claim_id,)).fetchone()
            if seen is not None:
                raise ApiMarketError(E_AM_CLAIM_WITHDRAWN, str(claim_id))
            stamp = _now_utc()
            try:
                self._conn.execute(
                    "INSERT INTO apimarket_claim_withdrawals (claim_id,"
                    " buyer_id, withdrawn_utc) VALUES (?,?,?)",
                    (claim_id, buyer_id, stamp))
            except sqlite3.IntegrityError:
                raise ApiMarketError(E_AM_CLAIM_WITHDRAWN, str(claim_id))
        return {"claim_id": claim_id, "purchase_id": int(row[1]),
                "listing_id": int(row[2]), "buyer_id": buyer_id,
                "dev_account": row[3], "price_paid": int(row[4]),
                "claim_text": row[5], "opened_utc": row[6],
                "withdrawn_utc": stamp, "status": "withdrawn",
                "disclaimer": self.disclaimer}

    def add_claim_note(self, buyer_id, claim_id, note_text):
        """Buyer follow-up on a post-sale claim (criteria
        AC-AMCN1..AC-AMCN8 pre-registered in the R2137 explore-queue row
        BEFORE this code existed).

        R2129 gave the buyer a claim door, R2130 the seller one answer
        and R2131 a withdrawal, so the thread stayed one-way: after the
        seller answered, a buyer who did not accept that answer had only
        two exits - withdraw (give up) or wait for a refund the seller
        may never issue - and neither side could tell an accepted answer
        from a disputed one. This door writes exactly one append-only
        apimarket_claim_notes row per claim (UNIQUE on claim_id) and
        never rewrites the claim, the answer, the withdrawal or the
        refund, so a follow-up is evidence, not a status flag.

        Gate order pinned by AC-AMCN3: buyer account shape, claim-id
        shape, note text shape, claim existence, ownership (the claim's
        own buyer), the already-refunded state, the withdrawn state,
        then the duplicate note. Every refusal writes zero rows and
        moves zero tokens."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        if (not isinstance(claim_id, int) or isinstance(claim_id, bool)
                or claim_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(claim_id))
        text = (note_text.strip() if isinstance(note_text, str) else None)
        if not text or len(text) > 500:
            raise ApiMarketError(E_AM_BAD_NOTE, str(note_text)[:40])
        with self._lock:
            row = self._conn.execute(
                "SELECT buyer_id, purchase_id, listing_id, dev_account"
                " FROM apimarket_claims WHERE claim_id = ?",
                (claim_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_CLAIM, str(claim_id))
            if row[0] != buyer_id:
                raise ApiMarketError(E_AM_NOT_BUYER,
                                     "%s/%s" % (buyer_id, claim_id))
            if self._refund_stamp(int(row[1])) is not None:
                raise ApiMarketError(E_AM_ALREADY_REFUNDED, str(claim_id))
            gone = self._conn.execute(
                "SELECT claim_id FROM apimarket_claim_withdrawals"
                " WHERE claim_id = ?", (claim_id,)).fetchone()
            if gone is not None:
                raise ApiMarketError(E_AM_CLAIM_WITHDRAWN, str(claim_id))
            seen = self._conn.execute(
                "SELECT note_id FROM apimarket_claim_notes"
                " WHERE claim_id = ?", (claim_id,)).fetchone()
            if seen is not None:
                raise ApiMarketError(E_AM_CLAIM_NOTE_DUP, str(claim_id))
            stamp = _now_utc()
            try:
                cur = self._conn.execute(
                    "INSERT INTO apimarket_claim_notes (claim_id,"
                    " buyer_id, note_text, noted_utc) VALUES (?,?,?,?)",
                    (claim_id, buyer_id, text, stamp))
            except sqlite3.IntegrityError:
                raise ApiMarketError(E_AM_CLAIM_NOTE_DUP, str(claim_id))
        return {"note_id": cur.lastrowid, "claim_id": claim_id,
                "purchase_id": int(row[1]),
                "listing_id": int(row[2]), "buyer_id": buyer_id,
                "dev_account": row[3], "note_text": text,
                "noted_utc": stamp, "status": "noted",
                "disclaimer": self.disclaimer}

    def api_claim_thread(self, claim_id, account):
        """One claim's whole conversation (criteria AC-AMCN1..AC-AMCN8
        pre-registered in the R2137 explore-queue row BEFORE this code
        existed).

        The claim queue answers "what is still owed" but each row is one
        snapshot; the buyer and the seller had no single face reading
        the order of acts inside one claim (opened, answered,
        followed-up, withdrawn, refunded) and no signal separating a
        seller answer the buyer accepted from one the buyer pushed back
        on. This face returns the enumerated event stream, ordered by
        stamp and then by a pinned same-second rank
        (opened < answered < note < withdrawn < refunded), plus the
        disputed flag (a follow-up exists and the claim is neither
        refunded nor withdrawn).

        Party gating: only the claim's own buyer and the claim's own
        seller may read it (viewer_role buyer/seller); any other account
        is refused with E_AM_NOT_PARTY before the stream is built. Gate
        order: account shape, claim-id shape, existence, party. Pure
        read: zero row mutations, zero token movement."""
        if not str(account or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, account)
        if (not isinstance(claim_id, int) or isinstance(claim_id, bool)
                or claim_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(claim_id))
        with self._lock:
            row = self._conn.execute(
                "SELECT c.purchase_id, c.listing_id, c.buyer_id,"
                " c.dev_account, c.price_paid, c.claim_text,"
                " c.opened_utc, l.title"
                " FROM apimarket_claims c"
                " LEFT JOIN apimarket_listings l"
                " ON l.listing_id = c.listing_id"
                " WHERE c.claim_id = ?", (claim_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_CLAIM, str(claim_id))
            if account == row[2]:
                role = "buyer"
            elif account == row[3]:
                role = "seller"
            else:
                raise ApiMarketError(E_AM_NOT_PARTY,
                                     "%s/%s" % (account, claim_id))
            answered = self._conn.execute(
                "SELECT response_text, replied_utc"
                " FROM apimarket_claim_responses WHERE claim_id = ?",
                (claim_id,)).fetchone()
            note = self._conn.execute(
                "SELECT note_text, noted_utc"
                " FROM apimarket_claim_notes WHERE claim_id = ?",
                (claim_id,)).fetchone()
            gone = self._conn.execute(
                "SELECT withdrawn_utc FROM apimarket_claim_withdrawals"
                " WHERE claim_id = ?", (claim_id,)).fetchone()
            refund = self._conn.execute(
                "SELECT refund_id, refunded_utc FROM apimarket_refunds"
                " WHERE purchase_id = ?", (int(row[0]),)).fetchone()
        refunded = refund is not None
        withdrawn = gone is not None
        if refunded:
            status = "refunded"
        elif withdrawn:
            status = "withdrawn"
        elif answered is not None:
            status = "answered"
        else:
            status = "open"
        events = [{"kind": "opened", "utc": row[6],
                   "actor": row[2], "text": row[5], "rank": 0}]
        if answered is not None:
            events.append({"kind": "answered", "utc": answered[1],
                           "actor": row[3], "text": answered[0],
                           "rank": 1})
        if note is not None:
            events.append({"kind": "note", "utc": note[1],
                           "actor": row[2], "text": note[0],
                           "rank": 2})
        if withdrawn:
            events.append({"kind": "withdrawn", "utc": gone[0],
                           "actor": row[2], "text": None, "rank": 3})
        if refunded:
            events.append({"kind": "refunded", "utc": refund[1],
                           "actor": "market", "text": None, "rank": 4})
        events.sort(key=lambda e: (e["utc"], e["rank"]))
        return {"claim_id": claim_id, "purchase_id": int(row[0]),
                "listing_id": int(row[1]),
                "listing_title": row[7], "buyer_id": row[2],
                "dev_account": row[3], "viewer_role": role,
                "price_paid": int(row[4]), "claim_text": row[5],
                "opened_utc": row[6], "status": status,
                "disputed": bool(note is not None
                                 and status in ("open", "answered")),
                "event_count": len(events), "events": events,
                "disclaimer": self.disclaimer}

    def api_claims(self, buyer_id=None, dev_account=None):
        """Post-sale claim queue (AC-AMCL5/AC-AMCL6) - one read face for
        the three views the market needs: the buyer's own claims, a
        seller's claims across every listing, and the operator's
        market-wide queue. The rows are the same append-only set; only
        the filter differs, and both filters may be combined (AND).

        Ordering is (opened_utc, claim_id) ascending, so the oldest debt
        is always first and a same-second batch has one stable answer.
        status / refund_id / refunded_utc / withdrawn_utc are derived at
        read time from the refund table and the seller answers are joined
        from apimarket_claim_responses (AC-AMCR2 / AC-AMCW2: refunded
        beats withdrawn beats answered beats open) - neither the claim
        row, the response row nor the withdrawal row is ever rewritten,
        and a refund landing later flips the status without touching any
        of them. price_paid is the stored purchase amount (the disputed
        face), not the listing's current asking price. Pure read: zero
        row mutations, zero token movement. A retired listing keeps its
        claims."""
        if buyer_id is not None and not str(buyer_id or "").startswith(
                "usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        if dev_account is not None:
            if not isinstance(dev_account, str) or not dev_account:
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        sql = ("SELECT c.claim_id, c.purchase_id, c.listing_id,"
               " c.buyer_id, c.dev_account, c.price_paid, c.claim_text,"
               " c.opened_utc, l.title, f.refund_id, f.refunded_utc,"
               " r.response_id, r.response_text, r.replied_utc,"
               " w.withdrawn_utc"
               " FROM apimarket_claims c"
               " LEFT JOIN apimarket_listings l"
               " ON l.listing_id = c.listing_id"
               " LEFT JOIN apimarket_refunds f"
               " ON f.purchase_id = c.purchase_id"
               " LEFT JOIN apimarket_claim_responses r"
               " ON r.claim_id = c.claim_id"
               " LEFT JOIN apimarket_claim_withdrawals w"
               " ON w.claim_id = c.claim_id")
        clauses = []
        args = []
        if buyer_id is not None:
            clauses.append("c.buyer_id = ?")
            args.append(buyer_id)
        if dev_account is not None:
            clauses.append("c.dev_account = ?")
            args.append(dev_account)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY c.opened_utc, c.claim_id"
        with self._lock:
            rows = self._conn.execute(sql, tuple(args)).fetchall()
        out = []
        for r in rows:
            refunded = r[9] is not None
            if refunded:
                status = "refunded"
            elif r[14] is not None:
                status = "withdrawn"
            elif r[11] is not None:
                status = "answered"
            else:
                status = "open"
            out.append({"claim_id": int(r[0]),
                        "purchase_id": int(r[1]),
                        "listing_id": int(r[2]),
                        "listing_title": r[8],
                        "dev_account": r[4],
                        "buyer_id": r[3],
                        "price_paid": int(r[5]),
                        "claim_text": r[6],
                        "opened_utc": r[7],
                        "status": status,
                        "refund_id": r[9],
                        "refunded_utc": r[10],
                        "response_id": r[11],
                        "response_text": r[12],
                        "responded_utc": r[13],
                        "withdrawn_utc": r[14]})
        refunded_count = sum(1 for x in out if x["status"] == "refunded")
        answered_count = sum(1 for x in out if x["status"] == "answered")
        withdrawn_count = sum(1 for x in out if x["status"] == "withdrawn")
        return {"buyer_id": buyer_id, "dev_account": dev_account,
                "claim_count": len(out),
                "open_count": (len(out) - refunded_count
                               - answered_count - withdrawn_count),
                "answered_count": answered_count,
                "refunded_count": refunded_count,
                "withdrawn_count": withdrawn_count,
                "disclaimer": self.disclaimer,
                "claims": out}

    def api_claim_latency(self, dev_account=None):
        """Seller-side claim response latency scorecard (criteria
        AC-CLT1..AC-CLT8 pre-registered in the R2149 explore-queue
        claim row BEFORE this code existed).

        The claim chain grew one door per round - open (R2129),
        respond (R2130), withdraw (R2131), note (R2137) - and the
        question and answer faces already scored their waiting time
        (api_seller_answers reports fastest/slowest/mean seconds), but
        the claim chain never produced a latency figure at all:
        api_seller_todo lists only the unanswered rows, api_claims
        carries status columns, api_claim_thread opens one thread. So
        nobody could answer "does this seller answer within a day, or
        does it sit on claims", which is the historical half of the
        same service question the todo queue answers for the present.

        This face reports, per claim, every leg of the chain as a
        duration measured from the claim's own opened_utc: the seller
        response, the buyer follow-up note, the withdrawal and the
        refund. Durations are derived ONLY from two stored stamps -
        never from a wall clock - and a leg that never happened is
        None rather than zero, so an unanswered claim can never look
        fast. A negative duration cannot arise: every action row
        references a claim that already exists, so its stamp is
        necessarily later.

        Status follows the same seam as api_claims (refunded beats
        withdrawn beats answered beats open), so a later refund adds
        refund_seconds without rewriting the response leg, and an
        answered-then-withdrawn claim keeps both stamps and both
        durations.

        The account gate is the usr: prefix gate of the seller
        scorecard family (api_seller_quality), which is the truthful
        one here because every claim's dev_account comes from a
        listing owned by a usr: account; the default None is the
        operator's market-wide view. Strict seller isolation; a
        prefix-valid account with no claims gets an honest empty
        envelope. Pure read: zero row mutations, zero token movement.
        The envelope carries the resident non-advisory disclaimer."""

        def _elapsed(earlier, later):
            if later is None:
                return None
            fmt = "%Y-%m-%dT%H:%M:%SZ"
            start = datetime.datetime.strptime(str(earlier), fmt)
            end = datetime.datetime.strptime(str(later), fmt)
            return int((end - start).total_seconds())

        if dev_account is not None:
            if not str(dev_account or "").startswith("usr:"):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)
        sql = ("SELECT c.claim_id, c.purchase_id, c.listing_id,"
               " c.buyer_id, c.dev_account, c.price_paid, c.opened_utc,"
               " f.refunded_utc, w.withdrawn_utc, r.replied_utc,"
               " n.noted_utc"
               " FROM apimarket_claims c"
               " LEFT JOIN apimarket_refunds f"
               " ON f.purchase_id = c.purchase_id"
               " LEFT JOIN apimarket_claim_responses r"
               " ON r.claim_id = c.claim_id"
               " LEFT JOIN apimarket_claim_withdrawals w"
               " ON w.claim_id = c.claim_id"
               " LEFT JOIN apimarket_claim_notes n"
               " ON n.claim_id = c.claim_id")
        args = ()
        if dev_account is not None:
            sql += " WHERE c.dev_account = ?"
            args = (str(dev_account),)
        sql += " ORDER BY c.opened_utc, c.claim_id"
        with self._lock:
            raw = self._conn.execute(sql, args).fetchall()
        claims = []
        for r in raw:
            opened = r[6]
            responded = r[9]
            refunded = r[7]
            withdrawn = r[8]
            noted = r[10]
            if refunded is not None:
                status = "refunded"
            elif withdrawn is not None:
                status = "withdrawn"
            elif responded is not None:
                status = "answered"
            else:
                status = "open"
            claims.append({
                "claim_id": int(r[0]),
                "purchase_id": int(r[1]),
                "listing_id": int(r[2]),
                "buyer_id": r[3],
                "dev_account": r[4],
                "price_paid": int(r[5]),
                "opened_utc": opened,
                "status": status,
                "responded_utc": responded,
                "response_seconds": _elapsed(opened, responded),
                "noted_utc": noted,
                "note_seconds": _elapsed(opened, noted),
                "withdrawn_utc": withdrawn,
                "withdraw_seconds": _elapsed(opened, withdrawn),
                "refunded_utc": refunded,
                "refund_seconds": _elapsed(opened, refunded),
            })
        latencies = sorted(c["response_seconds"] for c in claims
                           if c["response_seconds"] is not None)
        count = len(claims)
        answered = len(latencies)
        if latencies:
            mid = len(latencies) // 2
            median = (float(latencies[mid]) if len(latencies) % 2
                      else (latencies[mid - 1] + latencies[mid]) / 2.0)
            avg = float(sum(latencies)) / answered
        else:
            median = None
            avg = None
        stamps = [c["responded_utc"] for c in claims
                  if c["responded_utc"] is not None]
        return {"dev_account": dev_account,
                "claim_count": count,
                "answered_count": answered,
                "unanswered_count": count - answered,
                "response_coverage": (round(float(answered) / count, 4)
                                      if count else None),
                "avg_response_seconds": avg,
                "median_response_seconds": median,
                "fastest_seconds": (latencies[0] if latencies else None),
                "slowest_seconds": (latencies[-1] if latencies else None),
                "latest_response_utc": max(stamps) if stamps else None,
                "disclaimer": self.disclaimer,
                "claims": claims}

    def api_purchase_dossier(self, purchase_id, account):
        """One purchase's whole story (criteria AC-AMPD1..AC-AMPD8
        pre-registered in the R2135 explore-queue row BEFORE this code
        existed).

        Every face on this market answers one corner of a trade:
        api_library lists a buyer's purchases, api_refund returns one
        refund row, api_claims returns the claim queue, api_seller_ledger
        and api_buyer_ledger return the cash movements. Nobody answered
        "what actually happened to THIS purchase" - so a support ticket
        or a settlement dispute had to be assembled by hand from four
        faces. This face is that assembly, read-only.

        The viewer must be a party: the buyer of record answers
        viewer_role "buyer", the seller of record answers "seller", and
        they see the identical dossier apart from that one key; anybody
        else is refused with E_AM_NOT_PARTY before a single row is read
        beyond the purchase lookup (AC-AMPD2).

        Gate order pinned by AC-AMPD6: purchase-id shape, then account
        shape, then purchase existence, then party membership. The
        account gate is a plain non-empty-string gate because this face
        serves two different roles (the buyer faces use the usr: prefix,
        the developer faces use the registry), so a prefix rule here
        would be a lie about one of them.

        The three nested blocks are honest absences, never empty shells:
        refund is None until a refund row exists, rating is None until
        this buyer rates, claim is None until a claim is opened
        (AC-AMPD3). claim.status uses the api_claims precedence
        (refunded beats withdrawn beats answered beats open) and is
        recomputed here from the same append-only tables, so a refund
        landing later flips it without rewriting anything (AC-AMPD4).

        ticket_state is the single-word summary of the same evidence,
        with the pinned precedence refunded > withdrawn > answered >
        open > rated > settled (AC-AMPD5). Pure read: zero row
        mutations, zero token movement, and a retired listing keeps its
        dossier with its stamp while price_paid stays the historical
        amount charged (AC-AMPD7)."""
        if (not isinstance(purchase_id, int) or isinstance(purchase_id, bool)
                or purchase_id <= 0):
            raise ApiMarketError(E_AM_BAD_ARGS, str(purchase_id))
        if not isinstance(account, str) or not account.strip():
            raise ApiMarketError(E_AM_BAD_ACCOUNT, account)
        with self._lock:
            row = self._conn.execute(
                "SELECT p.purchase_id, p.listing_id, l.listing_key,"
                " l.title, l.category, p.buyer_id, l.dev_account,"
                " p.price_paid, p.dev_share, p.platform_share,"
                " p.spend_tx, p.purchased_utc, l.token_price"
                " FROM apimarket_purchases p JOIN apimarket_listings l"
                " ON l.listing_id = p.listing_id"
                " WHERE p.purchase_id = ?", (purchase_id,)).fetchone()
            if row is None:
                raise ApiMarketError(E_AM_UNKNOWN_PURCHASE,
                                     str(purchase_id))
            listing_id = int(row[1])
            buyer_id = row[5]
            dev_account = row[6]
            if account == buyer_id:
                role = "buyer"
            elif account == dev_account:
                role = "seller"
            else:
                raise ApiMarketError(E_AM_NOT_PARTY, account)
            stamp = self._delisted_utc(listing_id)
            effective_category = self._category_state(
                listing_id, row[4])[0]
            current = self._current_price(listing_id, int(row[12]))
            refund_row = self._conn.execute(
                "SELECT refund_id, amount, dev_share, platform_share,"
                " refund_tx, refunded_utc, reason FROM apimarket_refunds"
                " WHERE purchase_id = ?", (purchase_id,)).fetchone()
            rating_row = self._conn.execute(
                "SELECT rating_id, stars FROM apimarket_ratings"
                " WHERE buyer_id = ? AND listing_id = ?",
                (buyer_id, listing_id)).fetchone()
            claim_row = self._conn.execute(
                "SELECT c.claim_id, c.claim_text, c.opened_utc,"
                " r.refund_id, r.refunded_utc, a.response_id,"
                " a.response_text, a.replied_utc, w.withdrawn_utc"
                " FROM apimarket_claims c"
                " LEFT JOIN apimarket_refunds r"
                " ON r.purchase_id = c.purchase_id"
                " LEFT JOIN apimarket_claim_responses a"
                " ON a.claim_id = c.claim_id"
                " LEFT JOIN apimarket_claim_withdrawals w"
                " ON w.claim_id = c.claim_id"
                " WHERE c.purchase_id = ?", (purchase_id,)).fetchone()
            refund = None
            if refund_row is not None:
                refund = {"refund_id": int(refund_row[0]),
                          "amount": int(refund_row[1]),
                          "dev_share": int(refund_row[2]),
                          "platform_share": int(refund_row[3]),
                          "refund_tx": refund_row[4],
                          "refunded_utc": refund_row[5],
                          "reason": refund_row[6]}
            rating = None
            if rating_row is not None:
                rating_id = int(rating_row[0])
                revisions = self._conn.execute(
                    "SELECT COUNT(*), MAX(revised_utc)"
                    " FROM apimarket_rating_revisions WHERE rating_id = ?",
                    (rating_id,)).fetchone()
                rating = {"rating_id": rating_id,
                          "stars": self._effective_stars(
                              rating_id, int(rating_row[1])),
                          "revision_count": int(revisions[0]),
                          "revised_utc": revisions[1]}
            claim = None
            claim_status = None
            if claim_row is not None:
                if claim_row[3] is not None:
                    claim_status = "refunded"
                elif claim_row[8] is not None:
                    claim_status = "withdrawn"
                elif claim_row[5] is not None:
                    claim_status = "answered"
                else:
                    claim_status = "open"
                claim = {"claim_id": int(claim_row[0]),
                         "claim_text": claim_row[1],
                         "opened_utc": claim_row[2],
                         "status": claim_status,
                         "refund_id": claim_row[3],
                         "refunded_utc": claim_row[4],
                         "response_id": claim_row[5],
                         "response_text": claim_row[6],
                         "responded_utc": claim_row[7],
                         "withdrawn_utc": claim_row[8]}
            if refund is not None:
                ticket_state = "refunded"
            elif claim_status == "withdrawn":
                ticket_state = "withdrawn"
            elif claim_status == "answered":
                ticket_state = "answered"
            elif claim_status == "open":
                ticket_state = "open"
            elif rating is not None:
                ticket_state = "rated"
            else:
                ticket_state = "settled"
        return {"purchase_id": int(row[0]),
                "listing_id": listing_id,
                "listing_key": row[2],
                "title": row[3],
                "category": effective_category,
                "buyer_id": buyer_id,
                "dev_account": dev_account,
                "viewer_role": role,
                "price_paid": int(row[7]),
                "dev_share": int(row[8]),
                "platform_share": int(row[9]),
                "spend_tx": row[10],
                "purchased_utc": row[11],
                "current_price": current,
                "delisted": stamp is not None,
                "delisted_utc": stamp,
                "refund": refund,
                "rating": rating,
                "claim": claim,
                "ticket_state": ticket_state,
                "disclaimer": self.disclaimer}

    def api_buyer_refund_propensity(self, buyer_id):
        """Buyer refund propensity normalised against the buyer's own
        purchase base and the market (criteria AC-RFP1..AC-RFP8
        pre-registered in the R2166 explore-queue seed row BEFORE this
        code existed).

        api_buyer_profile gives lifetime refunded amount and refund
        count, api_refund_register lists rows and api_refund_exposure
        is the seller-side shortfall; none of them normalises refunds
        by how much this resident actually bought, so a buyer with one
        refund out of three purchases and a buyer with one out of
        thirty read the same refund_count, and there was no market
        benchmark to compare either against.

        Laws pinned by the suite: the denominator is the whole purchase
        base including refunded purchases (a refund is one per purchase
        behind UNIQUE(purchase_id), so refund_count never exceeds
        purchase_count and the rate lives in [0,1]); the amount axis is
        refunded_tokens/gross_spent with None rather than a fake zero;
        the market benchmark is the same count ratio over the whole
        market; the observed rate delta is raw minus market and None
        when either side is absent; and the smoothed rate is the
        shrinkage form (x + K*m)/(n + K), which means the deviation
        from the market is scaled by exactly n/(n+K) - a one-purchase
        history cannot read as more dangerous than a long one merely
        because of its size. Refund authority is the append-only
        apimarket_refunds table joined to purchases, so a later refund
        moves the numbers in the same step it moves the profile, while
        delisting or relisting never touches them. Gate: prefix-only
        account shape before any read (fail-closed E_AM_BAD_ACCOUNT); a
        prefix-valid account with no history gets an honest zero
        envelope. Pure read: zero row mutations, zero token movement."""
        if not str(buyer_id or "").startswith("usr:"):
            raise ApiMarketError(E_AM_BAD_ACCOUNT, buyer_id)
        buyer = str(buyer_id)
        with self._lock:
            mine = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(price_paid), 0)"
                " FROM apimarket_purchases WHERE buyer_id = ?",
                (buyer,)).fetchone()
            back = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(amount), 0)"
                " FROM apimarket_refunds WHERE buyer_id = ?",
                (buyer,)).fetchone()
            market = self._conn.execute(
                "SELECT COUNT(*) FROM apimarket_purchases").fetchone()
            market_back = self._conn.execute(
                "SELECT COUNT(*) FROM apimarket_refunds").fetchone()
        purchases = int(mine[0])
        refunds = int(back[0])
        gross = int(mine[1])
        refunded = int(back[1])
        market_purchases = int(market[0])
        market_refunds = int(market_back[0])
        rate = (float(refunds) / purchases) if purchases else None
        amount_rate = (float(refunded) / gross) if gross else None
        market_rate = (float(market_refunds) / market_purchases
                       if market_purchases else None)
        delta = None
        if rate is not None and market_rate is not None:
            delta = rate - market_rate
        smoothed = None
        if purchases and market_rate is not None:
            k = _RFP_SMOOTH
            smoothed = ((refunds + k * market_rate) / (purchases + k))
        return {
            "buyer_id": buyer,
            "purchase_count": purchases,
            "refund_count": refunds,
            "non_refunded_purchase_count": purchases - refunds,
            "gross_spent": gross,
            "refunded_tokens": refunded,
            "net_spent": gross - refunded,
            "refund_rate": rate,
            "refund_amount_rate": amount_rate,
            "market_purchase_count": market_purchases,
            "market_refund_count": market_refunds,
            "market_refund_rate": market_rate,
            "refund_rate_delta": delta,
            "smoothing_strength": _RFP_SMOOTH,
            "smoothed_refund_rate": smoothed,
            "disclaimer": self.disclaimer}

    def api_listing_velocity(self, dev_account=None):
        """Listing shelf-to-sale velocity (criteria AC-LV1..AC-LV8
        pre-registered in the R2169 explore claim row BEFORE this
        code existed; the R2166 seed asked for it, the anchors AC-LV,
        first_sale_utc, category_avg_seconds, shelf_opened_utc,
        sold_count, unsold_count and market_avg_seconds were all
        git-grep zero-occupancy against HEAD 2026-10-28, rc=1, and
        opened_utc was already taken 23 times by the claim chain, so
        the start key yields to shelf_opened_utc).

        The market answers event rows (api_market_feed), one trade
        end to end (api_purchase_dossier), the cash month
        (api_revenue_months) and the repricing history
        (api_price_history) - but nothing ever answered "how long
        did this shelf sit before it sold". Without that, a seller
        cannot tell a high price from a bad description from a dead
        category.

        The start stamp follows the cycle law (R2089). Publishing
        opens cycle 1; a re-listing opens the next one. For the
        first qualifying sale the shelf opened at the LATEST
        re-listing stamp at or before that sale, or at the immutable
        listed_utc when there is none - so a sale inside cycle 3 is
        measured from the cycle 3 opening, and a re-listing that
        happens AFTER the sale can never move the measured elapsed
        time.

        The sale authority is net: only a purchase with no
        append-only refund row is a candidate, and the first sale is
        the earliest stamp among them. A listing whose only purchase
        was refunded is therefore honestly UNSOLD (elapsed None,
        never zero), and an unsold row never enters an aggregate -
        the seed's explicit law that an unsold shelf must not drag
        the mean toward zero.

        elapsed_seconds is an integer derived only from the two
        stored stamps, never a wall clock, and non-negative by
        construction - except one disclosed boundary: a fixture
        whose purchase stamp predates every opening stamp is
        measured from the original listed_utc and clamped at zero
        rather than reported as a negative duration.

        Aggregates are over the SCOPED sold rows: avg is the pooled
        mean, median is the middle value (or the midpoint of the two
        middles), fastest and slowest pick the extremes with
        listing_id ascending as the tie-break for both, and all four
        are None when nothing sold in scope.

        category_avg_seconds and market_avg_seconds are deliberately
        NOT scoped: both are pooled over the WHOLE market, so a
        seller reading its own rows still has a comparable
        benchmark. That asymmetry is disclosed rather than hidden.
        Category buckets ride the one effective-category seam
        (_category_state), so revise_category moves a row and its
        bucket average in one step.

        Gates run before any read: the usr: prefix account shape
        (fail-closed E_AM_BAD_ACCOUNT), and the bare usr: prefix
        reads honestly empty. Retirement after the sale keeps the
        historical elapsed and only flips the delisted flag. Pure
        read: zero row mutations, zero token movement, and the
        envelope carries the resident non-advisory disclaimer."""
        if dev_account is not None:
            if not str(dev_account or "").startswith("usr:"):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)

        fmt = "%Y-%m-%dT%H:%M:%SZ"

        def _secs(earlier, later):
            start = datetime.datetime.strptime(str(earlier), fmt)
            end = datetime.datetime.strptime(str(later), fmt)
            return int((end - start).total_seconds())

        def _mean(values):
            if not values:
                return None
            return float(sum(values)) / len(values)

        def _median(values):
            if not values:
                return None
            ordered = sorted(values)
            mid = len(ordered) // 2
            if len(ordered) % 2:
                return float(ordered[mid])
            return (float(ordered[mid - 1]) + ordered[mid]) / 2.0

        with self._lock:
            def _first_net_sale(listing_id):
                row = self._conn.execute(
                    "SELECT MIN(p.purchased_utc) FROM"
                    " apimarket_purchases p WHERE p.listing_id = ?"
                    " AND NOT EXISTS (SELECT 1 FROM apimarket_refunds f"
                    " WHERE f.purchase_id = p.purchase_id)",
                    (listing_id,)).fetchone()
                if row is None or row[0] is None:
                    return None
                return row[0]

            def _shelf_opened_utc(listing_id, listed_utc, sale_utc):
                row = self._conn.execute(
                    "SELECT MAX(relisted_utc) FROM apimarket_relistings"
                    " WHERE listing_id = ? AND relisted_utc <= ?",
                    (listing_id, sale_utc)).fetchone()
                if row is not None and row[0] is not None:
                    return row[0]
                return listed_utc

            # The market pool is measured once, over every listing,
            # so the benchmark stays comparable under a seller scope.
            market_elapsed = []
            by_category = {}
            for m in self._conn.execute(
                    "SELECT listing_id, listed_utc FROM apimarket_listings"
                    " ORDER BY listing_id").fetchall():
                market_id = int(m[0])
                market_first = _first_net_sale(market_id)
                if market_first is None:
                    continue
                market_open = _shelf_opened_utc(market_id, m[1],
                                                market_first)
                elapsed = max(0, _secs(market_open, market_first))
                market_elapsed.append(elapsed)
                bucket = self._effective_category(market_id)
                by_category.setdefault(bucket, []).append(elapsed)

            sql = ("SELECT listing_id, listing_key, title, description,"
                   " token_price, listed_utc FROM apimarket_listings")
            args = ()
            if dev_account is not None:
                sql += " WHERE dev_account = ?"
                args = (dev_account,)
            sql += " ORDER BY listing_id"
            listings = self._conn.execute(sql, args).fetchall()

            rows = []
            scoped_elapsed = []
            for r in listings:
                listing_id = int(r[0])
                first = _first_net_sale(listing_id)
                delisted = self._cycle_state(listing_id)[1]
                bucket = self._effective_category(listing_id)
                if first is None:
                    rows.append({
                        "listing_id": listing_id,
                        "listing_key": r[1],
                        "title": self._metadata_state(
                            listing_id, r[2], r[3])[0],
                        "category": bucket,
                        "delisted": delisted,
                        "current_price": self._current_price(
                            listing_id, r[4]),
                        "shelf_opened_utc": None,
                        "first_sale_utc": None,
                        "elapsed_seconds": None,
                        "category_avg_seconds": _mean(
                            by_category.get(bucket, [])),
                        "unsold": True})
                    continue
                opened = _shelf_opened_utc(listing_id, r[5], first)
                elapsed = max(0, _secs(opened, first))
                scoped_elapsed.append(elapsed)
                rows.append({
                    "listing_id": listing_id,
                    "listing_key": r[1],
                    "title": self._metadata_state(
                        listing_id, r[2], r[3])[0],
                    "category": bucket,
                    "delisted": delisted,
                    "current_price": self._current_price(
                        listing_id, r[4]),
                    "shelf_opened_utc": opened,
                    "first_sale_utc": first,
                    "elapsed_seconds": elapsed,
                    "category_avg_seconds": _mean(
                        by_category.get(bucket, [])),
                    "unsold": False})
            rows.sort(key=lambda x: (
                x["unsold"],
                0 if x["elapsed_seconds"] is None
                else x["elapsed_seconds"],
                x["listing_id"]))

            sold = [x for x in rows if not x["unsold"]]
            fastest = None
            slowest = None
            fastest_id = None
            slowest_id = None
            if sold:
                fastest = min(x["elapsed_seconds"] for x in sold)
                slowest = max(x["elapsed_seconds"] for x in sold)
                fastest_id = min(x["listing_id"] for x in sold
                                 if x["elapsed_seconds"] == fastest)
                slowest_id = min(x["listing_id"] for x in sold
                                 if x["elapsed_seconds"] == slowest)

        return {
            "dev_account": dev_account,
            "listing_count": len(rows),
            "sold_count": len(sold),
            "unsold_count": len(rows) - len(sold),
            "avg_seconds": _mean(scoped_elapsed),
            "median_seconds": _median(scoped_elapsed),
            "fastest_seconds": fastest,
            "slowest_seconds": slowest,
            "fastest_listing_id": fastest_id,
            "slowest_listing_id": slowest_id,
            "market_avg_seconds": _mean(market_elapsed),
            "disclaimer": self.disclaimer,
            "rows": rows}

    def api_relist_gap(self, dev_account=None):
        """Retirement to re-listing gap (criteria AC-ARG1..AC-ARG8
        pre-registered in the R2180 explore claim row BEFORE this code
        existed; the AC-ARG prefix, api_relist_gap,
        test_apimarket_relistgap and ledger-apimarket-relistgap were
        all git-grep zero-occupancy against HEAD 2026-10-28, rc=1).

        api_listing_lifecycle answers the raw event stream,
        api_listing_velocity answers shelf-to-sale and the position /
        similarity faces answer the live set - so "how long was this
        shelf off the market before it came back" had no face, and a
        seller that repairs a service in a day read identically to one
        that abandons it for a quarter.

        Pairing law: a delisting row in cycle c pairs only with the
        re-listing row that OPENS cycle c+1 (the earliest such stamp),
        so one row is one closed retirement cycle. A delisting row with
        no return row whose own cycle is the current cycle is a gap
        still running: it is reported as a pending row with no duration
        (never zero) and never enters an aggregate. An orphan
        delisting row (older cycle, no return) is skipped rather than
        fabricated.

        gap_seconds is an integer derived only from the two stored
        stamps, never a wall clock, and clamped at zero for the
        disclosed out-of-order boundary.

        Aggregates cover completed gaps only: avg is the pooled mean,
        median is the middle value (or the midpoint of the two
        middles), fastest and slowest pick the extremes with
        listing_id ascending then from_cycle ascending as the
        tie-break, and all four are None when nothing closed in scope.
        market_avg_seconds is deliberately NOT scoped - it pools every
        completed gap in the whole market so a seller reading its own
        rows still has a comparable benchmark; that asymmetry is
        disclosed rather than hidden.

        Category buckets ride the one effective-category seam
        (_effective_category), so revise_category moves a row and its
        bucket in one step.

        Gates run before any read: the usr: prefix account shape
        (fail-closed E_AM_BAD_ACCOUNT), and the bare usr: prefix reads
        honestly empty. Pure read: zero row mutations, zero token
        movement, and the envelope carries the resident non-advisory
        disclaimer."""
        if dev_account is not None:
            if not str(dev_account or "").startswith("usr:"):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)

        fmt = "%Y-%m-%dT%H:%M:%SZ"

        def _secs(earlier, later):
            start = datetime.datetime.strptime(str(earlier), fmt)
            end = datetime.datetime.strptime(str(later), fmt)
            return int((end - start).total_seconds())

        def _mean(values):
            if not values:
                return None
            return float(sum(values)) / len(values)

        def _median(values):
            if not values:
                return None
            ordered = sorted(values)
            mid = len(ordered) // 2
            if len(ordered) % 2:
                return float(ordered[mid])
            return (float(ordered[mid - 1]) + ordered[mid]) / 2.0

        with self._lock:
            owners = {}
            for r in self._conn.execute(
                    "SELECT listing_id, dev_account, listing_key FROM"
                    " apimarket_listings ORDER BY listing_id").fetchall():
                owners[int(r[0])] = (r[1], r[2])

            def _gaps_of(listing_id):
                """Completed and pending gap rows of one listing, in
                the pairing law. Caller holds the lock."""
                out = []
                current = self._cycle_state(listing_id)[0]
                delists = self._conn.execute(
                    "SELECT cycle, delisted_utc FROM apimarket_delistings"
                    " WHERE listing_id = ? ORDER BY delist_id",
                    (listing_id,)).fetchall()
                for cycle, stamp in delists:
                    cycle = int(cycle)
                    back = self._conn.execute(
                        "SELECT MIN(relisted_utc) FROM"
                        " apimarket_relistings WHERE listing_id = ?"
                        " AND cycle = ?", (listing_id, cycle + 1)
                    ).fetchone()
                    returned = None if back is None else back[0]
                    if returned is not None:
                        out.append({
                            "listing_id": listing_id,
                            "listing_key": owners[listing_id][1],
                            "category": self._effective_category(
                                listing_id),
                            "from_cycle": cycle,
                            "to_cycle": cycle + 1,
                            "delisted_utc": stamp,
                            "relisted_utc": returned,
                            "gap_seconds": max(0, _secs(stamp, returned)),
                            "pending": False})
                    elif cycle == current:
                        out.append({
                            "listing_id": listing_id,
                            "listing_key": owners[listing_id][1],
                            "category": self._effective_category(
                                listing_id),
                            "from_cycle": cycle,
                            "to_cycle": None,
                            "delisted_utc": stamp,
                            "relisted_utc": None,
                            "gap_seconds": None,
                            "pending": True})
                return out

            market_completed = []
            market_rows = []
            for listing_id in sorted(owners):
                rows_of = _gaps_of(listing_id)
                for row in rows_of:
                    if not row["pending"]:
                        market_completed.append(row["gap_seconds"])
                market_rows += rows_of

            if dev_account is None:
                scoped_rows = market_rows
            else:
                scoped_rows = [row for row in market_rows
                               if owners[row["listing_id"]][0] == dev_account]

            completed = [row for row in scoped_rows if not row["pending"]]
            pending = [row for row in scoped_rows if row["pending"]]
            # Slowest responsiveness on top; ties by listing then cycle.
            completed.sort(key=lambda x: (-x["gap_seconds"],
                                          x["listing_id"],
                                          x["from_cycle"]))
            pending.sort(key=lambda x: (x["delisted_utc"], x["listing_id"]))
            scoped = [row["gap_seconds"] for row in completed]
            listing_count = len(set(row["listing_id"]
                                    for row in scoped_rows))

            fastest = None
            slowest = None
            fastest_id = None
            slowest_id = None
            if scoped:
                fastest = min(scoped)
                slowest = max(scoped)
                fastest_row = min(
                    (r for r in completed
                     if r["gap_seconds"] == fastest),
                    key=lambda r: (r["listing_id"], r["from_cycle"]))
                slowest_row = min(
                    (r for r in completed
                     if r["gap_seconds"] == slowest),
                    key=lambda r: (r["listing_id"], r["from_cycle"]))
                fastest_id = fastest_row["listing_id"]
                slowest_id = slowest_row["listing_id"]

        return {
            "dev_account": dev_account,
            "listing_count": listing_count,
            "gap_count": len(completed),
            "pending_count": len(pending),
            "avg_seconds": _mean(scoped),
            "median_seconds": _median(scoped),
            "fastest_seconds": fastest,
            "slowest_seconds": slowest,
            "fastest_listing_id": fastest_id,
            "slowest_listing_id": slowest_id,
            "market_avg_seconds": _mean(market_completed),
            "rows": completed + pending,
            "disclaimer": self.disclaimer}

    def api_seller_concentration(self, dev_account=None):
        """Seller-side buyer concentration face (criteria
        AC-SBC1..AC-SBC8 pre-registered in the R2170 explore claim
        row BEFORE this code existed; the AC-SBC prefix,
        api_seller_concentration, pareto_buyer_count, herfindahl,
        test_apimarket_concentration and ledger-apimarket-concentration
        were all git-grep zero-occupancy against HEAD 2026-10-28,
        rc=1).

        The seller side already counts repeat purchases
        (api_repeat_purchase), quality (api_seller_quality), balances
        (api_seller_ledger) and gross volume (dev_sales_board); the
        buyer side has its mirror image (api_buyer_seller_spend). None
        of them answers the seller's own existential question: "how
        many residents is my net revenue hanging on, how much of it
        rides on the single biggest one, and what happens if that one
        leaves". Retention counts events, not money weight; a sales
        board totals money, not distribution.

        Everything is derived from purchases x refunds x listings - no
        new table. The row authority is the PURCHASE side: a resident
        the seller never sold to stays absent even when the seller has
        live stock. Revenue authority is NET: a buyer whose only
        purchase was refunded stays on the roll (the purchase happened)
        but contributes zero weight, so a fully refunded buyer is never
        silently deleted and never inflates a share.

        Derived figures: share is the buyer's net revenue over the
        scoped net total (None when that total is zero, never a fake
        zero); cumulative_share walks the pinned order and reaches
        exactly 1.0 on the last row; top1_share is the head row and
        top3_share sums the first three (an honest two-row scope sums
        two, it is not padded); herfindahl is the sum of squared shares
        times 10000 computed from the exact fractions and rounded to
        two places, so one buyer reads 10000.0 and n equal buyers read
        10000/n; pareto_buyer_count is the smallest k whose cumulative
        net reaches 80% of the total, decided on integers (cum*5 >=
        total*4) so a boundary buyer that lands exactly on 80% is
        counted.

        Scope law: dev_account None is the whole market
        (scope == 'market', market_herfindahl None - the face never
        benchmarks itself against itself); a seller scope carries the
        market-wide herfindahl as a comparable benchmark, computed by
        the same law, so it can be checked against the unscoped call.

        Gates run before any read: the usr: prefix account shape
        (fail-closed E_AM_BAD_ACCOUNT), and the bare usr: prefix reads
        honestly empty. Pure read: zero row mutations, zero token
        movement."""
        if dev_account is not None:
            if not str(dev_account or "").startswith("usr:"):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)

        def _concentration(scope):
            sql = ("SELECT p.buyer_id, COUNT(p.purchase_id),"
                   " SUM(p.price_paid),"
                   " SUM(CASE WHEN f.purchase_id IS NULL"
                   " THEN 0 ELSE 1 END),"
                   " SUM(CASE WHEN f.purchase_id IS NULL"
                   " THEN 0 ELSE f.amount END)"
                   " FROM apimarket_purchases p"
                   " JOIN apimarket_listings l"
                   " ON l.listing_id = p.listing_id"
                   " LEFT JOIN apimarket_refunds f"
                   " ON f.purchase_id = p.purchase_id")
            args = ()
            if scope is not None:
                sql += " WHERE l.dev_account = ?"
                args = (scope,)
            sql += " GROUP BY p.buyer_id ORDER BY p.buyer_id"
            buyers = []
            for r in self._conn.execute(sql, args).fetchall():
                purchases = int(r[1])
                refunds = int(r[3] or 0)
                gross = int(r[2] or 0)
                refunded = int(r[4] or 0)
                buyers.append({
                    "buyer_id": r[0],
                    "purchase_count": purchases,
                    "refund_count": refunds,
                    "net_purchase_count": purchases - refunds,
                    "gross_revenue": gross,
                    "refunded_tokens": refunded,
                    "net_revenue": gross - refunded})
            buyers.sort(key=lambda x: (-x["net_revenue"], x["buyer_id"]))
            total_gross = sum(b["gross_revenue"] for b in buyers)
            total_refunded = sum(b["refunded_tokens"] for b in buyers)
            total_net = total_gross - total_refunded
            squares = []
            running = 0
            for index, b in enumerate(buyers, 1):
                running += b["net_revenue"]
                if total_net > 0:
                    exact = float(b["net_revenue"]) / total_net
                    b["share"] = round(exact, 6)
                    b["cumulative_share"] = round(
                        float(running) / total_net, 6)
                    squares.append(exact * exact)
                else:
                    b["share"] = None
                    b["cumulative_share"] = None
                b["rank"] = index
            pareto = None
            if total_net > 0:
                running = 0
                for index, b in enumerate(buyers, 1):
                    running += b["net_revenue"]
                    if running * 5 >= total_net * 4:
                        pareto = index
                        break
            herfindahl = (round(sum(squares) * 10000, 2)
                          if total_net > 0 else None)
            shares = ([b["share"] for b in buyers]
                      if total_net > 0 else [])
            return {
                "purchase_count": sum(b["purchase_count"]
                                      for b in buyers),
                "refund_count": sum(b["refund_count"] for b in buyers),
                "buyer_count": len(buyers),
                "refunded_buyers": sum(
                    1 for b in buyers if b["refund_count"] > 0),
                "gross_revenue": total_gross,
                "refunded_tokens": total_refunded,
                "net_revenue": total_net,
                "top1_share": shares[0] if shares else None,
                "top3_share": (round(sum(shares[:3]), 6)
                               if shares else None),
                "herfindahl": herfindahl,
                "pareto_buyer_count": pareto,
                "buyers": buyers}

        with self._lock:
            if dev_account is None:
                core = _concentration(None)
                market_herfindahl = None
                scope = "market"
            else:
                core = _concentration(dev_account)
                market_herfindahl = _concentration(None)["herfindahl"]
                scope = "seller"

        return {
            "dev_account": dev_account,
            "purchase_count": core["purchase_count"],
            "refund_count": core["refund_count"],
            "buyer_count": core["buyer_count"],
            "refunded_buyers": core["refunded_buyers"],
            "gross_revenue": core["gross_revenue"],
            "refunded_tokens": core["refunded_tokens"],
            "net_revenue": core["net_revenue"],
            "top1_share": core["top1_share"],
            "top3_share": core["top3_share"],
            "herfindahl": core["herfindahl"],
            "pareto_buyer_count": core["pareto_buyer_count"],
            "market_herfindahl": market_herfindahl,
            "scope": scope,
            "disclaimer": self.disclaimer,
            "buyers": core["buyers"]}

    def api_price_volatility(self, dev_account=None):
        """Seller repricing-discipline face (criteria AC-PVC1..AC-PVC8
        pre-registered in the R2171 explore claim row BEFORE this code
        existed; the AC-PVC prefix, api_price_volatility,
        test_apimarket_pricevolatility, ledger-apimarket-pricevolatility,
        avg_reprice_pct and repricing_sellers were all git-grep
        zero-occupancy against HEAD 2026-10-28, rc=1).

        Every existing price face is a snapshot cross-section:
        api_price_history answers one listing, api_listing_position
        ranks one listing inside its category,
        api_market_price_percentiles describes the live asking prices and
        api_listing_velocity measures shelf life. None of them answers
        the seller's own operating question: how often do I reprice, by
        how much, up or down, and is my repricing magnitude sane next to
        the market. Repricing is the seller's only high-frequency
        action and it was invisible on the time axis.

        Everything is derived from apimarket_price_revisions x
        apimarket_listings - no new table. The row authority is the
        REPRICING side, deliberately the mirror of api_board /
        api_categories: a listing that has live stock but was never
        repriced does NOT appear, so repriced_listing_count equals the
        row count and listing_count is the honest denominator.

        Magnitude law: every step percentage is
        round((new - previous) / previous * 100, 2) where previous is the
        base price or the prior revision in revision_id order - derived
        only from two stored prices, never from a wall clock, never a
        rewrite of history. The row total_pct is base to current by the
        same law. A same-price revision is refused at the write side
        (E_AM_PRICE_UNCHANGED), so every step is strictly up or strictly
        down and revision_count == up_count + down_count holds per row.

        Aggregation is POOLED over every step (not a mean of row means):
        avg_reprice_pct is the arithmetic mean of all steps,
        median_reprice_pct takes the odd middle or the even midpoint,
        max_reprice_pct keeps the sign of the largest absolute step, and
        net_direction_pct is the signed sum of every step. With zero
        steps all of them are None, never a fabricated 0.0.

        Scope law: dev_account None is the whole market (scope ==
        'market', market_avg_reprice_pct None - the face never benchmarks
        itself against itself); a seller scope carries the market-wide
        pooled average as a comparable benchmark computed by the same
        law, so it can be checked against the unscoped call, and sellers
        never leak into each other.

        Gates run before any read (fail-closed E_AM_BAD_ACCOUNT on the
        usr: prefix shape); the bare usr: prefix reads honestly empty.
        Pure read: zero row mutations, zero token movement."""
        if dev_account is not None:
            if not str(dev_account or "").startswith("usr:"):
                raise ApiMarketError(E_AM_BAD_ACCOUNT, dev_account)

        def _volatility(scope):
            sql = ("SELECT listing_id, listing_key, title, description,"
                   " token_price FROM apimarket_listings")
            args = ()
            if scope is not None:
                sql += " WHERE dev_account = ?"
                args = (scope,)
            sql += " ORDER BY listing_id"
            listings = self._conn.execute(sql, args).fetchall()
            rows = []
            steps = []
            for r in listings:
                listing_id = int(r[0])
                base = int(r[4])
                revisions = self._conn.execute(
                    "SELECT token_price FROM apimarket_price_revisions"
                    " WHERE listing_id = ? ORDER BY revision_id",
                    (listing_id,)).fetchall()
                if not revisions:
                    continue
                local = []
                previous = base
                up = 0
                down = 0
                for rev in revisions:
                    price = int(rev[0])
                    local.append(round(
                        (price - previous) * 100.0 / previous, 2))
                    if price > previous:
                        up += 1
                    elif price < previous:
                        down += 1
                    previous = price
                current = previous
                title, _desc, _count, _latest = self._metadata_state(
                    listing_id, r[2], r[3])
                steps.extend(local)
                rows.append({
                    "listing_id": listing_id,
                    "listing_key": r[1],
                    "title": title,
                    "revision_count": len(local),
                    "up_count": up,
                    "down_count": down,
                    "base_price": base,
                    "current_price": current,
                    "total_pct": round(
                        (current - base) * 100.0 / base, 2)})
            rows.sort(key=lambda x: (-x["revision_count"],
                                    -abs(x["total_pct"]),
                                    x["listing_id"]))
            ordered = sorted(steps)
            count = len(ordered)
            if count:
                avg = round(sum(ordered) / count, 2)
                if count % 2:
                    median = ordered[count // 2]
                else:
                    middle = count // 2
                    median = round((ordered[middle - 1]
                                    + ordered[middle]) / 2.0, 2)
                peak = max(ordered, key=lambda x: (abs(x), -x))
                net = round(sum(ordered), 2)
            else:
                avg = None
                median = None
                peak = None
                net = None
            return {
                "listing_count": len(listings),
                "repriced_listing_count": len(rows),
                "revision_count": count,
                "up_count": sum(1 for x in steps if x > 0),
                "down_count": sum(1 for x in steps if x < 0),
                "net_direction_pct": net,
                "avg_reprice_pct": avg,
                "median_reprice_pct": median,
                "max_reprice_pct": peak,
                "most_repriced_listing": (rows[0]["listing_id"]
                                          if rows else None),
                "rows": rows}

        with self._lock:
            if dev_account is None:
                core = _volatility(None)
                market_avg = None
                scope = "market"
            else:
                core = _volatility(dev_account)
                market_avg = _volatility(None)["avg_reprice_pct"]
                scope = "seller"

        return {
            "dev_account": dev_account,
            "scope": scope,
            "listing_count": core["listing_count"],
            "repriced_listing_count": core["repriced_listing_count"],
            "revision_count": core["revision_count"],
            "up_count": core["up_count"],
            "down_count": core["down_count"],
            "net_direction_pct": core["net_direction_pct"],
            "avg_reprice_pct": core["avg_reprice_pct"],
            "median_reprice_pct": core["median_reprice_pct"],
            "max_reprice_pct": core["max_reprice_pct"],
            "market_avg_reprice_pct": market_avg,
            "most_repriced_listing": core["most_repriced_listing"],
            "disclaimer": self.disclaimer,
            "rows": core["rows"]}

    def api_market_buyer_cohort(self):
        """Market-wide monthly buyer cohort (new versus returning).

        Criteria AC-MBC1..AC-MBC8 were registered in the R2173
        explore-queue row BEFORE this code existed (honesty law: the
        AC-MBC prefix, this face name, new_buyer_count,
        returning_buyer_count, the suite name and the runner label
        were all git-grep zero-occupancy against HEAD 2026-10-28,
        rc=1).

        api_market_months carries money and participant counts but
        cannot separate a first-time buyer from a resident who came
        back, and api_repeat_purchase answers the lifetime question
        only, so the month-by-month cohort was unreadable. This face
        pins it on the one net authority: a refunded purchase is not
        a purchase, so a refund removes that buyer from the month and,
        when that month was their earliest, moves their cohort origin
        to the next month they actually paid in. A month whose every
        purchase was refunded disappears rather than showing a zero
        row - the honest asymmetry against the cash-basis months face,
        which keeps a refund-only month.

        No arguments, so no gate: pure read, zero row mutations and
        zero token movement.
        """
        with self._lock:
            rows = self._conn.execute(
                "SELECT p.buyer_id, p.price_paid, p.purchased_utc"
                " FROM apimarket_purchases p WHERE NOT EXISTS"
                " (SELECT 1 FROM apimarket_refunds f WHERE"
                " f.purchase_id = p.purchase_id)").fetchall()

        first = {}
        months = {}
        for buyer, price, stamp in rows:
            month = str(stamp)[:7]
            if buyer not in first or month < first[buyer]:
                first[buyer] = month
            b = months.setdefault(month, {"buyers": set(),
                                          "purchase_count": 0,
                                          "gross": 0})
            b["buyers"].add(buyer)
            b["purchase_count"] += 1
            b["gross"] += int(price)

        activity = {}
        for buyer, price, stamp in rows:
            activity.setdefault(buyer, set()).add(str(stamp)[:7])
        repeat_buyer_count = sum(1 for stamps in activity.values()
                                 if len(stamps) > 1)

        out = []
        for month in sorted(months):
            b = months[month]
            new_purchases = 0
            for buyer, price, stamp in rows:
                if str(stamp)[:7] == month and first[buyer] == month:
                    new_purchases += 1
            new_buyer_count = sum(1 for buyer in b["buyers"]
                                  if first[buyer] == month)
            buyers = len(b["buyers"])
            out.append({
                "month": month,
                "purchase_count": b["purchase_count"],
                "gross": b["gross"],
                "buyer_count": buyers,
                "new_buyer_count": new_buyer_count,
                "returning_buyer_count": buyers - new_buyer_count,
                "new_purchase_count": new_purchases,
                "returning_purchase_count": (b["purchase_count"]
                                             - new_purchases),
                "avg_purchases_per_buyer": (b["purchase_count"]
                                            / float(buyers)),
            })

        purchase_count = sum(row["purchase_count"] for row in out)
        buyer_count = len(activity)
        return {"month_count": len(out),
                "purchase_count": purchase_count,
                "gross": sum(row["gross"] for row in out),
                "buyer_count": buyer_count,
                "repeat_buyer_count": repeat_buyer_count,
                "repeat_rate": ((repeat_buyer_count / float(buyer_count))
                                if buyer_count else None),
                "returning_purchase_count": sum(
                    row["returning_purchase_count"] for row in out),
                "first_month": out[0]["month"] if out else None,
                "last_month": out[-1]["month"] if out else None,
                "disclaimer": self.disclaimer,
                "months": out}

    def api_market_seller_cohort(self):
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

    def api_market_buyer_retention(self):
        """Market-wide monthly buyer retention matrix.

        Criteria AC-BRT1..AC-BRT8 were registered in the R2175
        explore-queue row BEFORE this code existed (honesty law: the
        AC-BRT prefix, this face name, cohort_month, retention_rate,
        cumulative_retention, the suite name and the runner label were
        all git-grep zero-occupancy against HEAD 2026-10-28, rc=1).

        The cohort face answers how many buyers in a month were new
        versus returning and the repeat face answers the lifetime
        question, but neither follows a first-purchase cohort forward
        through later months, so "do the residents who arrived in
        January still buy in March" was unreadable. This face pins the
        matrix on the same net authority the cohort face uses: a
        refunded purchase is not a purchase, so a refund removes that
        month from the buyer activity and, when it was the buyer
        earliest month, moves the cohort origin forward. A buyer whose
        every purchase was refunded disappears entirely instead of
        showing a zero row.

        Every cohort gets a contiguous cell grid from its own month to
        the last active month in the world, so offset 0 is always the
        whole cohort (rate 1.0) and the cumulative column never
        decreases. No arguments, so no gate: pure read, zero row
        mutations and zero token movement.
        """
        with self._lock:
            rows = self._conn.execute(
                "SELECT p.buyer_id, p.price_paid, p.purchased_utc"
                " FROM apimarket_purchases p WHERE NOT EXISTS"
                " (SELECT 1 FROM apimarket_refunds f WHERE"
                " f.purchase_id = p.purchase_id)").fetchall()

        activity = {}
        for buyer, price, stamp in rows:
            month = str(stamp)[:7]
            slot = activity.setdefault(buyer, {}).setdefault(
                month, [0, 0])
            slot[0] += 1
            slot[1] += int(price)

        origin = {buyer: min(months)
                  for buyer, months in activity.items()}

        def index_of(month):
            year, part = month.split("-")
            return int(year) * 12 + (int(part) - 1)

        def name_of(index):
            return "%04d-%02d" % (index // 12, index % 12 + 1)

        months_seen = sorted(set(month for months in activity.values()
                                 for month in months))
        last_index = index_of(months_seen[-1]) if months_seen else None

        cohorts = []
        retained_total = 0
        for month in sorted(set(origin.values())):
            members = sorted(b for b in origin if origin[b] == month)
            size = len(members)
            gross = sum(activity[b][month][1] for b in members)
            cells = []
            cumulative = set()
            start = index_of(month)
            for offset in range(0, last_index - start + 1):
                name = name_of(start + offset)
                hits = set(b for b in members if name in activity[b])
                cumulative |= hits
                cells.append({
                    "offset": offset,
                    "month": name,
                    "retained_buyer_count": len(hits),
                    "retention_rate": len(hits) / float(size),
                    "cumulative_retained_buyer_count": len(cumulative),
                    "cumulative_retention_rate": (len(cumulative)
                                                  / float(size)),
                })
            later = sum(1 for b in members
                        if any(m > month for m in activity[b]))
            retained_total += later
            cohorts.append({
                "cohort_month": month,
                "cohort_size": size,
                "cohort_gross": gross,
                "retained_buyer_count": later,
                "retention_rate": later / float(size),
                "max_offset": cells[-1]["offset"],
                "cells": cells,
            })

        buyer_count = len(activity)
        return {
            "cohort_count": len(cohorts),
            "buyer_count": buyer_count,
            "purchase_count": sum(slot[0] for months in
                                  activity.values()
                                  for slot in months.values()),
            "gross": sum(slot[1] for months in activity.values()
                         for slot in months.values()),
            "month_count": len(months_seen),
            "first_cohort": (cohorts[0]["cohort_month"]
                             if cohorts else None),
            "last_cohort": (cohorts[-1]["cohort_month"]
                            if cohorts else None),
            "max_offset": (max(row["max_offset"] for row in cohorts)
                           if cohorts else None),
            "retained_buyer_count": retained_total,
            "retention_rate": ((retained_total / float(buyer_count))
                               if buyer_count else None),
            "disclaimer": self.disclaimer,
            "cohorts": cohorts,
        }

    # -- point-in-time catalog helpers (AC-CPM3..AC-CPM5, R2176) ------

    def _alive_at_instant(self, listing_id, listed_utc, instant):
        """(alive) of one listing at one instant under the cycle law
        generalized on the time axis (AC-CPM5).

        Cycle 1 opens at the publish stamp, every append-only
        re-listing row opens its own cycle at its stamp, and a cycle is
        closed by the delisting row FOR THAT cycle. A listing is live
        at an instant when at least one cycle was already open there
        and had not yet been answered by its own delisting row - so a
        listing retired and later re-listed is honestly absent in
        between and present again afterwards, while no row is ever
        rewritten. Caller holds the lock."""
        cycles = [(1, str(listed_utc))]
        for relisted_utc, cycle in self._conn.execute(
                "SELECT relisted_utc, cycle FROM apimarket_relistings"
                " WHERE listing_id = ? ORDER BY relist_id",
                (listing_id,)).fetchall():
            cycles.append((int(cycle), str(relisted_utc)))
        closed = {}
        for cycle, delisted_utc in self._conn.execute(
                "SELECT cycle, delisted_utc FROM apimarket_delistings"
                " WHERE listing_id = ? ORDER BY delist_id",
                (listing_id,)).fetchall():
            closed.setdefault(int(cycle), str(delisted_utc))
        for cycle, opened_utc in cycles:
            if opened_utc > instant:
                continue
            shut = closed.get(cycle)
            if shut is None or shut > instant:
                return True
        return False

    def _category_at_instant(self, listing_id, base_category, instant):
        """Effective category as of one instant (AC-CPM4): the newest
        append-only category revision stamped at or before the instant
        wins, ties broken by revision_id; with no such revision the
        declaration made at publish time speaks. A later revision never
        rewrites the bucket an earlier instant already saw. This is the
        time-axis sibling of _category_state. Caller holds the lock."""
        row = self._conn.execute(
            "SELECT category FROM apimarket_category_revisions"
            " WHERE listing_id = ? AND revised_utc <= ?"
            " ORDER BY revised_utc DESC, revision_id DESC LIMIT 1",
            (listing_id, instant)).fetchone()
        if row is not None:
            return row[0]
        return base_category

    def _supply_at_instant(self, listing_id, base_supply, instant):
        """(effective, sold, remaining, sold_out) of one listing at one
        instant, derived only from stored stamps (AC-CSM4).

        A purchase counts once its own stamp is at or before the
        instant and a refund hands its unit back to the shelf from the
        refund stamp on - the same net law _supply_full applies, only
        restricted to the stamps the instant has already seen, so no
        later sale can ever leak backwards into an earlier month end.
        A restock adds only from its own stamp on. A listing with no
        declared base supply is unlimited: effective and remaining are
        None and it can never be sold out (the same honest asymmetry
        _supply_full reports). Caller holds the lock."""
        bought = int(self._conn.execute(
            "SELECT COUNT(*) FROM apimarket_purchases"
            " WHERE listing_id = ? AND purchased_utc <= ?",
            (listing_id, instant)).fetchone()[0])
        refunded = int(self._conn.execute(
            "SELECT COUNT(*) FROM apimarket_refunds"
            " WHERE listing_id = ? AND refunded_utc <= ?",
            (listing_id, instant)).fetchone()[0])
        sold = max(0, bought - refunded)
        if base_supply is None:
            return (None, sold, None, False)
        restocked = int(self._conn.execute(
            "SELECT COALESCE(SUM(add_units), 0)"
            " FROM apimarket_supply_revisions"
            " WHERE listing_id = ? AND restocked_utc <= ?",
            (listing_id, instant)).fetchone()[0])
        effective = int(base_supply) + restocked
        remaining = max(0, effective - sold)
        return (effective, sold, remaining, remaining == 0)

    def api_category_supply_months(self, include_uncategorized=True):
        """Per-category monthly SUPPLY trend (criteria AC-CSM1..AC-CSM8
        pre-registered in the R2182 explore-queue row BEFORE this code
        existed).

        Every other catalog face is a snapshot: api_categories reports
        the current live/retired split and price band, api_listing_
        position one shelf against its rivals, and the demand faces
        answer lifetime turnover. api_category_price_months answers
        how the ASKING PRICE moved, never how much of the category was
        actually still on sale - so "is this category shrinking or
        expanding" had to be inferred from prices and trades. The
        material for a rebuild sat on the append-only books (publish
        stamps with the declared base supply, restocks, purchases,
        refunds, delistings and re-listings), but no face read them as
        a supply timeline.

        Sampling law: one observation per UTC month, taken at that
        month's LAST second, exactly as api_category_price_months does.
        Liveness comes from _alive_at_instant (the cycle law
        generalized on the time axis), the bucket from
        _category_at_instant, and the shelf arithmetic from
        _supply_at_instant, so a restock or a sale stamped in the last
        second of a month counts there and one at the next month's
        first second does not.

        The window is contiguous from the first event month to the
        last, where the supply-side events are publish stamps,
        restocks, category revisions, delistings and re-listings, so a
        month with no event still appears as an honest zero row. Price
        revisions are deliberately NOT events here: they move no unit,
        which is why this window may differ from the price face's own
        and is disclosed.

        Rows are the listing side: a listing is present at a month end
        only when a cycle was open there. Each month splits its live
        listings into in-stock, sold-out and unlimited shelves and
        reports the units still buyable, so conservation holds three
        ways (month == sum of cells, live == in-stock + sold-out +
        unlimited, and remaining_units only ever counts finite
        shelves). Category cells are ordered ascending with the
        uncategorized bucket last; include_uncategorized=False removes
        that bucket from cells and from both aggregates.

        Gate: include_uncategorized must be a real bool, fail-closed
        with E_AM_BAD_ARGS before any read. Pure read: zero row
        mutations and zero token movement."""
        if not isinstance(include_uncategorized, bool):
            raise ApiMarketError(E_AM_BAD_ARGS, include_uncategorized)
        with self._lock:
            listings = self._conn.execute(
                "SELECT listing_id, supply, category, listed_utc"
                " FROM apimarket_listings ORDER BY listing_id"
            ).fetchall()
            events = set()
            for row in listings:
                events.add(str(row[3])[:7])
            for table, column in (
                    ("apimarket_supply_revisions", "restocked_utc"),
                    ("apimarket_category_revisions", "revised_utc"),
                    ("apimarket_delistings", "delisted_utc"),
                    ("apimarket_relistings", "relisted_utc")):
                for stamp, in self._conn.execute(
                        "SELECT " + column + " FROM " + table
                ).fetchall():
                    events.add(str(stamp)[:7])
            months = _contiguous_months(sorted(events))
            sampled = {}
            seen = set()
            for listing_id, base_supply, base_category, listed_utc \
                    in listings:
                listing_id = int(listing_id)
                for month in months:
                    as_of = _month_end(month)
                    if not self._alive_at_instant(
                            listing_id, listed_utc, as_of):
                        continue
                    bucket = self._category_at_instant(
                        listing_id, base_category, as_of)
                    if bucket is None and not include_uncategorized:
                        continue
                    _effective, _sold, remaining, sold_out = \
                        self._supply_at_instant(
                            listing_id, base_supply, as_of)
                    slot = sampled.setdefault(month, {})
                    slot.setdefault(bucket, []).append(
                        (remaining, sold_out))
                    seen.add(listing_id)

        rows = []
        categories_seen = set()
        for month in months:
            slot = sampled.get(month, {})
            ordered = sorted(c for c in slot if c is not None)
            if None in slot:
                ordered.append(None)
            cells = []
            month_live = 0
            month_in_stock = 0
            month_sold_out = 0
            month_unlimited = 0
            month_remaining = 0
            for bucket in ordered:
                values = slot[bucket]
                unlimited = sum(1 for remaining, _out in values
                                if remaining is None)
                in_stock = sum(1 for remaining, out in values
                               if remaining is not None and not out)
                sold_out = sum(1 for remaining, out in values
                               if remaining is not None and out)
                remaining_units = sum(r for r, _out in values
                                      if r is not None)
                cells.append({
                    "category": bucket,
                    "live_listing_count": len(values),
                    "in_stock_listing_count": in_stock,
                    "sold_out_listing_count": sold_out,
                    "unlimited_listing_count": unlimited,
                    "remaining_units": remaining_units,
                })
                categories_seen.add(bucket)
                month_live += len(values)
                month_in_stock += in_stock
                month_sold_out += sold_out
                month_unlimited += unlimited
                month_remaining += remaining_units
            rows.append({
                "month": month,
                "as_of": _month_end(month),
                "live_listing_count": month_live,
                "category_count": len(cells),
                "in_stock_listing_count": month_in_stock,
                "sold_out_listing_count": month_sold_out,
                "unlimited_listing_count": month_unlimited,
                "remaining_units": month_remaining,
                "categories": cells,
            })
        peak_month = None
        peak_count = None
        for row in rows:
            if peak_month is None \
                    or row["live_listing_count"] > peak_count:
                peak_month = row["month"]
                peak_count = row["live_listing_count"]
        month_over_month_change = None
        if len(rows) >= 2:
            month_over_month_change = (
                rows[-1]["live_listing_count"]
                - rows[-2]["live_listing_count"])
        return {
            "month_count": len(rows),
            "first_month": rows[0]["month"] if rows else None,
            "last_month": rows[-1]["month"] if rows else None,
            "listing_count": len(seen),
            "category_count": len(categories_seen),
            "peak_month": peak_month,
            "peak_live_listing_count": peak_count,
            "month_over_month_change": month_over_month_change,
            "disclaimer": self.disclaimer,
            "months": rows,
        }

    def api_category_price_months(self, include_uncategorized=True):
        """Per-category monthly asking-price trend (criteria
        AC-CPM1..AC-CPM8 pre-registered in the R2176 explore-queue row
        BEFORE this code existed).

        Both asking-price faces are snapshots of the current state:
        api_market_price_percentiles gives one distribution and
        api_categories one min/max band per bucket. The time axis the
        market already had answers turnover (api_market_months,
        api_category_demand, api_category_refund_months), never the
        question "how did each category's asking price move from month
        to month". The material for a point-in-time rebuild was already
        on the append-only books - publish stamps, price revisions,
        category revisions, delistings and re-listings - but no face
        read them as a timeline.

        Sampling law: one observation per UTC month, taken at that
        month's LAST second (as_of). For every listing the price comes
        from _price_at_instant and the bucket from
        _category_at_instant, and liveness from _alive_at_instant, so a
        revision stamped in the last second of a month counts there
        while one stamped at the next month's first second does not.
        The window is contiguous from the first event month to the last
        event month, so a month with no event at all still appears with
        honest zeros instead of vanishing.

        Row authority is the listing side. Order is category ascending
        with the uncategorized bucket last; with
        include_uncategorized=False that bucket leaves both the rows and
        the month/global aggregates. Prices are integers off the ledger,
        percentiles use the pinned linear-interpolation helper, and
        p50_change is this month's median minus the previous month's
        (None when either side is absent, so a zero month honestly
        breaks the series rather than reporting a fake jump).

        Gate: include_uncategorized must be a real bool, fail-closed
        with E_AM_BAD_ARGS before any read. Pure read: zero row
        mutations and zero token movement."""
        if not isinstance(include_uncategorized, bool):
            raise ApiMarketError(E_AM_BAD_ARGS, include_uncategorized)
        with self._lock:
            listings = self._conn.execute(
                "SELECT listing_id, token_price, category, listed_utc"
                " FROM apimarket_listings ORDER BY listing_id"
            ).fetchall()
            events = set()
            for row in listings:
                events.add(str(row[3])[:7])
            for table, column in (
                    ("apimarket_price_revisions", "revised_utc"),
                    ("apimarket_category_revisions", "revised_utc"),
                    ("apimarket_delistings", "delisted_utc"),
                    ("apimarket_relistings", "relisted_utc")):
                for stamp, in self._conn.execute(
                        "SELECT " + column + " FROM " + table
                ).fetchall():
                    events.add(str(stamp)[:7])
            months = _contiguous_months(sorted(events))
            sampled = {}
            seen = set()
            for listing_id, base_price, base_category, listed_utc \
                    in listings:
                listing_id = int(listing_id)
                for month in months:
                    as_of = _month_end(month)
                    if not self._alive_at_instant(
                            listing_id, listed_utc, as_of):
                        continue
                    price = self._price_at_instant(
                        listing_id, int(base_price), as_of)
                    bucket = self._category_at_instant(
                        listing_id, base_category, as_of)
                    if bucket is None and not include_uncategorized:
                        continue
                    slot = sampled.setdefault(month, {})
                    slot.setdefault(bucket, []).append(price)
                    seen.add(listing_id)

        rows = []
        previous_median = None
        categories_seen = set()
        for month in months:
            slot = sampled.get(month, {})
            ordered = sorted(c for c in slot if c is not None)
            if None in slot:
                ordered.append(None)
            prices = sorted(p for values in slot.values()
                            for p in values)
            cells = []
            for bucket in ordered:
                values = sorted(slot[bucket])
                cells.append({
                    "category": bucket,
                    "live_listing_count": len(values),
                    "min_price": values[0],
                    "max_price": values[-1],
                    "p50_price": percentile(values, 0.5),
                })
                categories_seen.add(bucket)
            median = percentile(prices, 0.5)
            rows.append({
                "month": month,
                "as_of": _month_end(month),
                "live_listing_count": len(prices),
                "category_count": len(cells),
                "min_price": prices[0] if prices else None,
                "max_price": prices[-1] if prices else None,
                "p25_price": percentile(prices, 0.25),
                "p50_price": median,
                "p75_price": percentile(prices, 0.75),
                "mean_price": ((float(sum(prices)) / len(prices))
                               if prices else None),
                "p50_change": ((median - previous_median)
                               if median is not None
                               and previous_median is not None else None),
                "categories": cells,
            })
            previous_median = median
        return {
            "month_count": len(rows),
            "first_month": rows[0]["month"] if rows else None,
            "last_month": rows[-1]["month"] if rows else None,
            "listing_count": len(seen),
            "category_count": len(categories_seen),
            "disclaimer": self.disclaimer,
            "months": rows,
        }

    def api_market_daily(self, start_day=None, end_day=None):
        """Market-wide CALENDAR-DAY trade timeline (pre-registered
        AC-MDL1..AC-MDL8 in the R2178 explore-queue row BEFORE this
        code existed).

        Every existing time axis stops short of a date: api_market_
        months answers one UTC month, api_market_hour_heatmap answers
        an hour-of-day x weekday slot aggregated across the whole
        history, api_market_buyer_retention answers cohort month
        cells, and api_market_feed answers event rows. So the daily
        settlement sheet an operator actually reads - "what did the
        market do on 2026-09-15, and which calendar day was the
        busiest" - had no face, and answering it meant pulling every
        purchase row and bucketing by hand.

        Same cash-basis law as api_market_months, one granularity
        finer: a sale books on the UTC day of purchased_utc, a refund
        books on the UTC day of refunded_utc and never rewrites the
        day the sale landed in, so a refund-day row honestly carries
        a negative net beside zero participants.

        The series is CONTIGUOUS over the activity extent: every day
        from the first to the last activity day is present, and a day
        with no trade at all appears as an honest zero row instead of
        vanishing. Optional start_day / end_day (YYYY-MM-DD, inclusive)
        clip the same grid; a window holding no activity answers an
        honest empty envelope rather than a fabricated row set. The
        envelope lifetime_* figures are the WINDOW totals (equal to
        the whole history on a default call), so rows and envelope
        can never disagree.

        busiest_day is the active day with the highest net (ties to
        the earliest day), quietest_active_day the active day with the
        lowest net (ties to the earliest), and avg_net_per_active_day
        the mean net over active days only - a zero day is not a
        business day and never drags that mean down. Pure read: zero
        row mutations, zero token movement.
        """
        start = None if start_day is None else _assert_day(start_day)
        end = None if end_day is None else _assert_day(end_day)
        if start is not None and end is not None and start > end:
            raise ApiMarketError(
                E_AM_BAD_WINDOW,
                "window inverted: " + start + " > " + end)
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

        def bucket(day):
            return buckets.setdefault(
                day, {"sales_count": 0, "gross": 0,
                      "refund_count": 0, "refunded": 0,
                      "dev_share": 0, "platform_share": 0,
                      "refunded_dev_share": 0,
                      "refunded_platform_share": 0,
                      "buyers": set(), "sellers": set(),
                      "listings": set()})

        for buyer, price, dev_share, platform_share, stamp, dev, \
                listing_id in sales:
            b = bucket(str(stamp)[:10])
            b["sales_count"] += 1
            b["gross"] += int(price)
            b["dev_share"] += int(dev_share)
            b["platform_share"] += int(platform_share)
            b["buyers"].add(buyer)
            b["sellers"].add(dev)
            b["listings"].add(int(listing_id))
        for amount, dev_share, platform_share, stamp in refunds:
            b = bucket(str(stamp)[:10])
            b["refund_count"] += 1
            b["refunded"] += int(amount)
            b["refunded_dev_share"] += int(dev_share)
            b["refunded_platform_share"] += int(platform_share)

        active = sorted(buckets)
        first = last = None
        if active:
            first = active[0] if start is None else max(start, active[0])
            last = active[-1] if end is None else min(end, active[-1])

        days = []
        if first is not None and first <= last:
            for day in _day_sequence(first, last):
                b = buckets.get(day)
                if b is None:
                    days.append({
                        "day": day, "sales_count": 0, "gross": 0,
                        "refund_count": 0, "refunded": 0, "net": 0,
                        "dev_share": 0, "platform_share": 0,
                        "dev_share_net": 0, "platform_share_net": 0,
                        "buyer_count": 0, "seller_count": 0,
                        "listing_count": 0})
                    continue
                days.append({
                    "day": day,
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

        active_rows = [r for r in days
                       if r["sales_count"] or r["refund_count"]]
        busiest = None
        quietest = None
        if active_rows:
            busiest = min(active_rows,
                          key=lambda r: (-r["net"], r["day"]))["day"]
            quietest = min(active_rows,
                           key=lambda r: (r["net"], r["day"]))["day"]
        lifetime_net = sum(r["net"] for r in days)
        return {
            "day_count": len(days),
            "active_day_count": len(active_rows),
            "zero_day_count": len(days) - len(active_rows),
            "window_start": days[0]["day"] if days else None,
            "window_end": days[-1]["day"] if days else None,
            "lifetime_sales_count": sum(r["sales_count"] for r in days),
            "lifetime_gross": sum(r["gross"] for r in days),
            "lifetime_refund_count": sum(r["refund_count"]
                                         for r in days),
            "lifetime_refunded": sum(r["refunded"] for r in days),
            "lifetime_net": lifetime_net,
            "lifetime_dev_revenue": sum(r["dev_share_net"]
                                        for r in days),
            "lifetime_platform_revenue": sum(r["platform_share_net"]
                                             for r in days),
            "busiest_day": busiest,
            "quietest_active_day": quietest,
            "avg_net_per_active_day": (
                round(float(lifetime_net) / len(active_rows), 2)
                if active_rows else None),
            "disclaimer": self.disclaimer,
            "days": days,
        }

    def api_refund_latency(self):
        """Market-wide refund latency distribution (criteria
        AC-RFLT1..AC-RFLT8 pre-registered in the R2179 explore-queue
        claim row BEFORE this code existed).

        The refund family - propensity, register, exposure and
        category_refund_months - answers money and headcount only, so
        "how long from the sale to the money coming back" had no face
        at all. A slow settlement, a backlogged after-sales desk and a
        healthy refund therefore read identically, and a seller
        planning cash flow could not see the payback period.

        Every latency here is derived ONLY from two stored stamps of
        the SAME purchase: purchased_utc and refunded_utc. Nothing
        reads a wall clock, an unrefunded purchase contributes no
        latency at all (unrefunded_count keeps it visible instead of
        pretending it took zero seconds), and a leg that happened is
        always at or after its purchase.

        The distribution is reported as a six-band partition (lower
        bound inclusive, upper exclusive, so a boundary stamp belongs
        to the upper band and the bands stay exhaustive and disjoint),
        five aggregates over refunded rows only - average, median,
        nearest-rank p90, fastest and slowest - plus two named
        crossings (the refunds that landed on the same UTC date as the
        sale, and the ones that took a week or more). The monthly leg
        buckets a refund by the month it LANDED and runs contiguously
        from the first to the last refund month, so a month with no
        refund is an honest zero row with None statistics rather than
        a gap. Pure read, no arguments: zero row mutations and zero
        token movement. The envelope carries the resident non-advisory
        disclaimer."""
        with self._lock:
            raw = self._conn.execute(
                "SELECT f.refunded_utc, f.amount,"
                " p.purchased_utc, p.price_paid"
                " FROM apimarket_refunds f JOIN apimarket_purchases p"
                " ON p.purchase_id = f.purchase_id"
                " ORDER BY f.refund_id").fetchall()
            purchase_count = int(self._conn.execute(
                "SELECT COUNT(*) FROM apimarket_purchases"
            ).fetchone()[0])

        latencies = []
        amounts = []
        same_day = 0
        month_cells = {}
        for refunded_utc, amount, purchased_utc, price_paid in raw:
            seconds = _refund_latency_seconds(purchased_utc,
                                             refunded_utc)
            latencies.append(seconds)
            amounts.append(int(amount))
            if str(refunded_utc)[:10] == str(purchased_utc)[:10]:
                same_day += 1
            month = str(refunded_utc)[:7]
            cell = month_cells.setdefault(month, [])
            cell.append(seconds)

        ordered = sorted(latencies)
        refund_count = len(ordered)
        month_names = sorted(month_cells)
        months = []
        if month_names:
            for month in _contiguous_months(month_names):
                values = sorted(month_cells.get(month, []))
                if values:
                    mid = len(values) // 2
                    median = (float(values[mid]) if len(values) % 2
                              else (values[mid - 1] + values[mid]) / 2.0)
                    months.append({
                        "month": month,
                        "refund_count": len(values),
                        "median_refund_seconds": median,
                        "avg_refund_seconds": round(
                            float(sum(values)) / len(values), 2),
                        "slowest_seconds": values[-1]})
                else:
                    months.append({
                        "month": month,
                        "refund_count": 0,
                        "median_refund_seconds": None,
                        "avg_refund_seconds": None,
                        "slowest_seconds": None})

        pairs = list(zip(latencies, amounts))
        bands = []
        for label, lower, upper in _REFUND_LATENCY_BANDS:
            in_band = [p for p in pairs
                       if p[0] >= lower and (upper is None
                                             or p[0] < upper)]
            bands.append({
                "band": label,
                "lower_seconds": lower,
                "upper_seconds": upper,
                "refund_count": len(in_band),
                "refunded": sum(p[1] for p in in_band)})

        if ordered:
            mid = len(ordered) // 2
            median = (float(ordered[mid]) if len(ordered) % 2
                      else (ordered[mid - 1] + ordered[mid]) / 2.0)
            avg = round(float(sum(ordered)) / len(ordered), 2)
            rank = int(-(-len(ordered) * 9 // 10))
            p90 = ordered[rank - 1]
        else:
            median = None
            avg = None
            p90 = None
        over_week = len([s for s in ordered if s >= 604800])
        return {
            "purchase_count": purchase_count,
            "refund_count": refund_count,
            "unrefunded_count": purchase_count - refund_count,
            "refund_rate": (round(float(refund_count) / purchase_count, 4)
                            if purchase_count else None),
            "avg_refund_seconds": avg,
            "median_refund_seconds": median,
            "p90_refund_seconds": p90,
            "fastest_seconds": ordered[0] if ordered else None,
            "slowest_seconds": ordered[-1] if ordered else None,
            "same_day_count": same_day,
            "over_week_count": over_week,
            "month_count": len(months),
            "bands": bands,
            "months": months,
            "disclaimer": self.disclaimer,
        }
