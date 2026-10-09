"""UGC template marketplace face over the token ledger sandbox
(BigDomain R1691; canon = explore-queue UGC template marketplace
line: template listing / revenue split / rating three domains;
seed = creator-incentive gradient successor + UGC pipeline design
row. The template payload itself is caller-supplied metadata - the
marketplace models the compliance-bearing trade pipeline, not the
content editor.)

Three domains ride on the P-47-2b token ledger:

  listing  : a creator publishes one template per
            (creator, template_key); the title and the
            description pass the content gate BEFORE any row is
            stored (msgSecCheck pre-gate; sandbox = wordlist mock
            SecGate injected by the caller - the lobby gate
            product is referenced, never copied); the declared
            AIGC label persists on the row.
  split    : each purchase is exactly one spend bound to its tx,
            then exactly one creator share entry out of
            pool:share (the incentive.py per-entry one-share
            structure, reused by reference - not rebuilt); the
            integer split law is floor + input-order remainder
            with zero rounding loss (same law as the settlement
            apportion), enforced structurally by a DB CHECK.
  rating   : only a purchaser of the template may rate it, one
            immutable rating per (buyer, template), stars 1..5;
            the aggregate view is a deterministic pure read.

Pre-registered criteria AC-TM1..AC-TM7 live in the R1691
explore-queue row and were written before this code existed
(honesty law).

Split weights are sandbox-only defaults ([needs-CEO] adoption
face): the production creator/platform ratio and every template
price point are a P1 item for CEO, approval-only. This module
ships no parameter values into any config file.

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: three extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import json
import sqlite3
import threading

E_TM_BAD_ACCOUNT = "E_TM_BAD_ACCOUNT"      # AC-TM1 / AC-TM7
E_TM_BAD_ARGS = "E_TM_BAD_ARGS"            # AC-TM1 / AC-TM5 / AC-TM7
E_TM_BAD_PRICE = "E_TM_BAD_PRICE"          # AC-TM1 / AC-TM7
E_TM_DUP_TEMPLATE = "E_TM_DUP_TEMPLATE"    # AC-TM1
E_TM_CONTENT_REJECTED = "E_TM_CONTENT_REJECTED"  # AC-TM2
E_TM_GATE_ERROR = "E_TM_GATE_ERROR"        # AC-TM2 (runtime fault)
E_TM_NO_GATE = "E_TM_NO_GATE"              # AC-TM2 (unwired gate)
E_TM_NO_DISCLAIMER = "E_TM_NO_DISCLAIMER"  # AC-TM6
E_TM_UNKNOWN_TEMPLATE = "E_TM_UNKNOWN_TEMPLATE"  # AC-TM3
E_TM_PURCHASE_DUP = "E_TM_PURCHASE_DUP"    # AC-TM3
E_TM_SELF_BUY = "E_TM_SELF_BUY"           # AC-TM3
E_TM_BAD_SPLIT = "E_TM_BAD_SPLIT"          # AC-TM4 (param face)
E_TM_NOT_BUYER = "E_TM_NOT_BUYER"          # AC-TM5
E_TM_RATE_DUP = "E_TM_RATE_DUP"           # AC-TM5
E_TM_BAD_STARS = "E_TM_BAD_STARS"          # AC-TM5

_CONTENT_REJECTED_CODE = "E_CONTENT_REJECTED"  # lobby SecGate hit

# Sandbox-only split defaults ([needs-CEO] adoption face, AC-TM4):
# the creator leg is first in apportion order, so the single
# remainder token of the integer law lands on the creator side.
SANDBOX_PARAMS = {
    "creator_weight": 70,
    "platform_weight": 30,
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tmarket_templates (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id TEXT NOT NULL,
    template_key TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    token_price INTEGER NOT NULL CHECK (token_price > 0),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    listed_utc TEXT NOT NULL,
    UNIQUE (creator_id, template_key)
);
CREATE TABLE IF NOT EXISTS tmarket_purchases (
    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    price_paid INTEGER NOT NULL CHECK (price_paid > 0),
    creator_share INTEGER NOT NULL CHECK (creator_share >= 0),
    platform_share INTEGER NOT NULL CHECK (platform_share >= 0),
    spend_tx TEXT NOT NULL,
    creator_share_tx TEXT NOT NULL,
    purchased_utc TEXT NOT NULL,
    UNIQUE (buyer_id, template_id),
    CHECK (creator_share + platform_share = price_paid)
);
CREATE TABLE IF NOT EXISTS tmarket_ratings (
    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    stars INTEGER NOT NULL CHECK (stars IN (1, 2, 3, 4, 5)),
    rated_utc TEXT NOT NULL,
    UNIQUE (buyer_id, template_id)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def split_amount(price, params=None):
    """Pure integer split (AC-TM4): floor for both legs first, then
    the remainder is distributed one token at a time in input order
    (creator first) - the landing total equals the price exactly,
    with zero rounding loss. Deterministic, zero RNG."""
    p = params or SANDBOX_PARAMS
    cw = p["creator_weight"]
    pw = p["platform_weight"]
    total_w = cw + pw
    creator = (price * cw) // total_w
    platform = (price * pw) // total_w
    remainder = price - creator - platform
    if remainder > 0 and cw > 0:
        creator += 1
        remainder -= 1
    platform += remainder
    return creator, platform


class TMarketError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class TMarketFace:
    """UGC template marketplace face over one Ledger instance. Own
    connection and lock into the same DB file; every mutation runs
    inside BEGIN IMMEDIATE. Template/purchase/rating rows are
    immutable once written (zero UPDATE surface). The content gate
    and the disclaimer are injected (dependency injection: the
    lobby SecGate product is referenced, never copied); a missing
    gate or an empty disclaimer refuses construction - no gate, no
    door."""

    def __init__(self, ledger, gate, disclaimer, params=None):
        self.led = ledger
        if gate is None or not callable(getattr(gate, "check_text", None)):
            raise TMarketError(E_TM_NO_GATE, "content gate required")
        self.gate = gate
        text = str(disclaimer or "").strip()
        if not text:
            raise TMarketError(E_TM_NO_DISCLAIMER,
                               "resident disclaimer required")
        self.disclaimer = text
        self.params = dict(params or SANDBOX_PARAMS)
        self._check_params()
        self.db_path = ledger.db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def _check_params(self):
        p = self.params
        for name in ("creator_weight", "platform_weight"):
            weight = p.get(name)
            if (not isinstance(weight, int) or isinstance(weight, bool)
                    or weight < 1):
                raise TMarketError(E_TM_BAD_SPLIT, str(weight))

    def close(self):
        with self._lock:
            self._conn.close()

    # -- gate helpers (fail-closed end to end) ---------------------------

    def _gate_check(self, text):
        """Run the injected content gate. A wordlist hit maps to
        E_TM_CONTENT_REJECTED; ANY other failure (offline gate,
        runtime fault) maps to E_TM_GATE_ERROR - never a silent
        pass. Zero rows are stored on either path (AC-TM2)."""
        try:
            self.gate.check_text(text)
        except Exception as exc:  # noqa: BLE001 (fail-closed wrap)
            if getattr(exc, "code", None) == _CONTENT_REJECTED_CODE:
                raise TMarketError(E_TM_CONTENT_REJECTED,
                                   getattr(exc, "word", ""))
            raise TMarketError(E_TM_GATE_ERROR, str(exc))

    # -- listing domain ----------------------------------------------------

    def publish_template(self, creator_id, template_key, title,
                         description, payload, token_price,
                         ai_generated):
        """List one template: content gate on title AND
        description before any row exists (publish-time refusal);
        exactly one row per (creator, template_key) - a repeat is
        rejected with zero rows (AC-TM1). The declared AIGC label
        persists on the row and every view surfaces it (AC-TM6)."""
        if not str(creator_id or "").startswith("usr:"):
            raise TMarketError(E_TM_BAD_ACCOUNT, creator_id)
        key = str(template_key or "").strip()
        t = str(title or "")
        d = str(description or "")
        if not key:
            raise TMarketError(E_TM_BAD_ARGS, "template key required")
        if not t.strip():
            raise TMarketError(E_TM_BAD_ARGS, "title required")
        if (not isinstance(token_price, int) or isinstance(token_price, bool)
                or token_price <= 0):
            raise TMarketError(E_TM_BAD_PRICE, str(token_price))
        if not isinstance(payload, (dict, list)) or not payload:
            raise TMarketError(E_TM_BAD_ARGS,
                               "template payload required")
        if not isinstance(ai_generated, bool):
            raise TMarketError(E_TM_BAD_ARGS, "ai_generated must be bool")
        body = json.dumps(payload, sort_keys=True)
        with self._lock:
            self._gate_check(t)   # zero rows stored on rejection
            self._gate_check(d)
            row = self._conn.execute(
                "SELECT template_id FROM tmarket_templates"
                " WHERE creator_id = ? AND template_key = ?",
                (creator_id, key)).fetchone()
            if row is not None:
                raise TMarketError(E_TM_DUP_TEMPLATE, key)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO tmarket_templates (creator_id,"
                    " template_key, title, description, payload_json,"
                    " token_price, ai_label, listed_utc)"
                    " VALUES (?,?,?,?,?,?,?,?)",
                    (creator_id, key, t, d, body, token_price,
                     1 if ai_generated else 0, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise TMarketError(E_TM_DUP_TEMPLATE, key)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"template_id": cur.lastrowid, "creator_id": creator_id,
                "template_key": key, "title": t,
                "token_price": token_price,
                "ai_label": 1 if ai_generated else 0}

    def _require_template(self, template_id):
        """Validation + lookup under no lock (caller holds it).
        Returns (template_id, creator_id, token_price)."""
        if (not isinstance(template_id, int) or isinstance(template_id, bool)
                or template_id <= 0):
            raise TMarketError(E_TM_BAD_ARGS, str(template_id))
        row = self._conn.execute(
            "SELECT template_id, creator_id, token_price"
            " FROM tmarket_templates WHERE template_id = ?",
            (template_id,)).fetchone()
        if row is None:
            raise TMarketError(E_TM_UNKNOWN_TEMPLATE, str(template_id))
        return row

    # -- purchase + split domain -------------------------------------------

    def purchase(self, buyer_id, template_id, ref):
        """Buy one template: exactly one spend per (buyer, template)
        bound to its tx; a repeat purchase is rejected BEFORE the
        spend so the balance never moves twice; self-purchase is
        rejected outright (anti-farm); the creator share is one
        share entry out of pool:share with the integer split law
        (AC-TM3/AC-TM4). Returns the full provenance envelope."""
        if not str(buyer_id or "").startswith("usr:"):
            raise TMarketError(E_TM_BAD_ACCOUNT, buyer_id)
        r = str(ref or "").strip()
        if not r:
            raise TMarketError(E_TM_BAD_ARGS, "purchase ref required")
        with self._lock:
            tpl = self._require_template(template_id)
            if tpl[1] == buyer_id:
                raise TMarketError(E_TM_SELF_BUY,
                                   "%s on own template %s"
                                   % (buyer_id, template_id))
            row = self._conn.execute(
                "SELECT purchase_id FROM tmarket_purchases"
                " WHERE buyer_id = ? AND template_id = ?",
                (buyer_id, template_id)).fetchone()
            if row is not None:
                raise TMarketError(E_TM_PURCHASE_DUP,
                                   "%s/%s" % (buyer_id, template_id))
            price = int(tpl[2])
            creator_share, platform_share = split_amount(
                price, self.params)
            self.led.ensure_account(buyer_id,
                                    census_avatar_id=buyer_id[4:])
            spend_tx = self.led.spend(buyer_id, price, r, "order")
            share_tx = ""
            if creator_share > 0:
                share_tx = self.led.share_from_pool(
                    "pool:share", tpl[1], creator_share,
                    "tmarket:share:%s" % spend_tx,
                    ref_type="settlement",
                    action="tmarket_creator_share")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO tmarket_purchases (template_id,"
                    " buyer_id, price_paid, creator_share,"
                    " platform_share, spend_tx, creator_share_tx,"
                    " purchased_utc) VALUES (?,?,?,?,?,?,?,?)",
                    (template_id, buyer_id, price, creator_share,
                     platform_share, spend_tx, share_tx, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise TMarketError(E_TM_PURCHASE_DUP,
                                   "%s/%s" % (buyer_id, template_id))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"purchase_id": cur.lastrowid, "template_id": template_id,
                "buyer_id": buyer_id, "price_paid": price,
                "creator_share": creator_share,
                "platform_share": platform_share,
                "spend_tx": spend_tx, "creator_share_tx": share_tx,
                "disclaimer": self.disclaimer}

    # -- rating domain -------------------------------------------------------

    def rate(self, buyer_id, template_id, stars):
        """Rate a purchased template: purchaser-only fail-closed
        gate, one immutable rating per (buyer, template), stars
        1..5 (AC-TM5). Append-only - a repeat is rejected, never
        updated."""
        if not str(buyer_id or "").startswith("usr:"):
            raise TMarketError(E_TM_BAD_ACCOUNT, buyer_id)
        if (not isinstance(stars, int) or isinstance(stars, bool)
                or stars < 1 or stars > 5):
            raise TMarketError(E_TM_BAD_STARS, str(stars))
        with self._lock:
            self._require_template(template_id)
            bought = self._conn.execute(
                "SELECT purchase_id FROM tmarket_purchases"
                " WHERE buyer_id = ? AND template_id = ?",
                (buyer_id, template_id)).fetchone()
            if bought is None:
                raise TMarketError(E_TM_NOT_BUYER,
                                   "%s/%s" % (buyer_id, template_id))
            row = self._conn.execute(
                "SELECT rating_id FROM tmarket_ratings"
                " WHERE buyer_id = ? AND template_id = ?",
                (buyer_id, template_id)).fetchone()
            if row is not None:
                raise TMarketError(E_TM_RATE_DUP,
                                   "%s/%s" % (buyer_id, template_id))
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO tmarket_ratings (template_id,"
                    " buyer_id, stars, rated_utc) VALUES (?,?,?,?)",
                    (template_id, buyer_id, stars, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise TMarketError(E_TM_RATE_DUP,
                                   "%s/%s" % (buyer_id, template_id))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"rating_id": cur.lastrowid, "template_id": template_id,
                "buyer_id": buyer_id, "stars": stars}

    # -- read faces -----------------------------------------------------------

    def _agg_rating(self, template_id):
        row = self._conn.execute(
            "SELECT COUNT(*), COALESCE(AVG(stars), 0)"
            " FROM tmarket_ratings WHERE template_id = ?",
            (template_id,)).fetchone()
        return int(row[0]), float(row[1])

    def template_view(self, template_id):
        """One listing surface: metadata + declared AIGC label +
        purchase/rating aggregates, envelope carries the resident
        non-advisory disclaimer (AC-TM6). Pure read."""
        with self._lock:
            row = self._conn.execute(
                "SELECT template_id, creator_id, template_key, title,"
                " description, token_price, ai_label, listed_utc"
                " FROM tmarket_templates WHERE template_id = ?",
                (template_id,)).fetchone()
            if row is None:
                raise TMarketError(E_TM_UNKNOWN_TEMPLATE,
                                   str(template_id))
            n_buy = self._conn.execute(
                "SELECT COUNT(*) FROM tmarket_purchases"
                " WHERE template_id = ?", (template_id,)).fetchone()[0]
            n_rate, avg = self._agg_rating(template_id)
        return {"template_id": int(row[0]), "creator_id": row[1],
                "template_key": row[2], "title": row[3],
                "description": row[4], "token_price": int(row[5]),
                "ai_label": int(row[6]), "listed_utc": row[7],
                "purchase_count": int(n_buy), "rating_count": n_rate,
                "rating_avg": avg, "disclaimer": self.disclaimer}

    def market_view(self):
        """Whole-market listing surface: every row carries the
        declared AIGC label (presentation-face law, AC-TM6); the
        envelope carries the resident disclaimer. Pure read."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT template_id, creator_id, template_key, title,"
                " token_price, ai_label FROM tmarket_templates"
                " ORDER BY template_id").fetchall()
            out = []
            for r in rows:
                n_rate, avg = self._agg_rating(int(r[0]))
                out.append({"template_id": int(r[0]),
                            "creator_id": r[1], "template_key": r[2],
                            "title": r[3], "token_price": int(r[4]),
                            "ai_label": int(r[5]),
                            "rating_count": n_rate, "rating_avg": avg})
        return {"disclaimer": self.disclaimer, "templates": out}

    def rating_view(self, template_id):
        """Per-template rating surface: immutable per-rater rows
        plus the deterministic aggregate (AC-TM5). Pure read."""
        with self._lock:
            self._require_template(template_id)
            rows = self._conn.execute(
                "SELECT buyer_id, stars, rated_utc FROM"
                " tmarket_ratings WHERE template_id = ?"
                " ORDER BY rating_id", (template_id,)).fetchall()
            n_rate, avg = self._agg_rating(template_id)
        return {"template_id": template_id, "rating_count": n_rate,
                "rating_avg": avg, "disclaimer": self.disclaimer,
                "ratings": [{"buyer_id": r[0], "stars": int(r[1]),
                             "rated_utc": r[2]} for r in rows]}

    def sales_view(self, creator_id):
        """Per-creator sales ledger view: every purchase row with
        its split amounts and bound txs (provenance, AC-TM4/6).
        Pure read; rows are immutable once written."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT p.purchase_id, p.template_id, t.template_key,"
                " p.buyer_id, p.price_paid, p.creator_share,"
                " p.platform_share, p.spend_tx, p.creator_share_tx,"
                " p.purchased_utc FROM tmarket_purchases p JOIN"
                " tmarket_templates t ON t.template_id ="
                " p.template_id WHERE t.creator_id = ?"
                " ORDER BY p.purchase_id", (creator_id,)).fetchall()
        return {"creator_id": creator_id,
                "disclaimer": self.disclaimer,
                "sales": [{"purchase_id": int(r[0]),
                           "template_id": int(r[1]),
                           "template_key": r[2], "buyer_id": r[3],
                           "price_paid": int(r[4]),
                           "creator_share": int(r[5]),
                           "platform_share": int(r[6]),
                           "spend_tx": r[7],
                           "creator_share_tx": r[8],
                           "purchased_utc": r[9]} for r in rows]}
