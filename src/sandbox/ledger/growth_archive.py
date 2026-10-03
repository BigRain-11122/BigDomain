"""Resident growth-archive subscription face over the token
ledger sandbox (BigDomain R1017; canon = BLUEPRINT sec-4 C2-tier
new subscription line adopted by C-20260927-01 as the first item
of the adoption order; product definition =
docs/spec/price-canon-amendment-spec.md sec-2 - this company's
own presentation face; the N2 supply seam is the BigLife
behavior-event feed over the existing IF-7 / IF-10 seams, zero
new API: the sandbox stands in with a deterministic probe
supply ingested through an explicit supply face, production
wiring is a bootstrap-period item).

Product shape (spec sec-2): a monthly subscription granting a
read-only resident archive page with four sections - the
year-ring timeline, the month's dialogue digest, the city-story
monthly report, and birthday/event memorial pages. Boundary:
read-only presentation only; point-to-point custom dialogue is
the existing C7 price line and is NOT rebuilt here; archive
content must derive from real behavior events - fabrication is
impossible by structure: every view path only SELECTs the
supply-events table and no view takes a content parameter at
all.

Mechanism (pre-registered criteria AC-GA1..AC-GA7 live in the
R1017 backlog row and were written before this code existed;
honesty law):

  - supply gate: only residents with ingested behavior events
    are subscribable; an unknown resident is rejected with zero
    charge; a duplicate event id is rejected with zero rows
    (AC-GA2).
  - subscribe: exactly one spend bound to its tx; a repeated
    subscription of the same (account, resident, month) is
    rejected BEFORE the spend so the balance never moves twice;
    another month is a separate legal purchase (AC-GA3).
  - access gate is fail-closed: the archive page without an
    entitlement for that exact month window is rejected with
    zero charge (AC-GA4).
  - archive_page and the read views are pure reads: zero token
    movement (AC-GA4).
  - compliance strings are runtime verbatim from the ledger
    config, zero literals: the derived city-story rows carry the
    AIGC label (config token.ai_label_text); every page render
    carries the persistent non-advisory disclaimer (config
    token.disclaimer); the price note is config params_status
    verbatim - the 9.9 yuan/month anchor and launch gating stay
    with the CEO, approval-only ([needs-CEO]); the N2 face is a
    read-only archive with no user-input channel, so the
    msgSecCheck gate is a boundary note - any future user-input
    memorial-request face routes through the ugc pipeline IF-8
    single-source gate (reference, no rebuild) (AC-GA5).
  - hard law (AC-GA6): bad args are all rejected with zero side
    effects; the module stays pure ASCII; zero UPDATE surface
    (subscription rows immutable, event rows append-only); the
    only token touchpoints are ensure_account and the one spend
    inside subscribe.

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: two extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import json
import re
import sqlite3
import threading

E_GA_BAD_ACCOUNT = "E_GA_BAD_ACCOUNT"   # AC-GA3 / AC-GA6
E_GA_BAD_ARGS = "E_GA_BAD_ARGS"          # AC-GA2 / AC-GA6
E_GA_BAD_PRICE = "E_GA_BAD_PRICE"        # AC-GA3 / AC-GA6
E_GA_BAD_MONTH = "E_GA_BAD_MONTH"        # AC-GA3 / AC-GA4 / AC-GA6
E_GA_UNKNOWN = "E_GA_UNKNOWN"            # AC-GA2
E_GA_DUP = "E_GA_DUP"                    # AC-GA3
E_GA_DUP_EVENT = "E_GA_DUP_EVENT"        # AC-GA2
E_GA_BAD_EVENT = "E_GA_BAD_EVENT"        # AC-GA2
E_GA_DENIED = "E_GA_DENIED"              # AC-GA4

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ga_resident_events (
    event_id TEXT PRIMARY KEY,
    resident_id TEXT NOT NULL,
    event_kind TEXT NOT NULL CHECK (event_kind IN
        ('year_ring','dialogue','city_story','memorial')),
    occurred_utc TEXT NOT NULL,
    content_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ga_subscriptions (
    sub_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    resident_id TEXT NOT NULL,
    sub_month TEXT NOT NULL,
    token_price INTEGER NOT NULL CHECK (token_price > 0),
    bound_spend_tx TEXT NOT NULL,
    subscribed_utc TEXT NOT NULL,
    UNIQUE (account_id, resident_id, sub_month)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class GrowthArchiveError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class GrowthArchiveFace:
    """Monthly resident-archive subscription face over one
    Ledger instance. Own connection and lock into the same DB
    file; every mutation runs inside BEGIN IMMEDIATE. Event rows
    are append-only supply facts; subscription rows are immutable
    once written (zero UPDATE surface)."""

    def __init__(self, ledger):
        self.led = ledger
        self.db_path = ledger.db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                      isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        tok = (ledger.config or {}).get("token") or {}
        self._ai_label = str(tok.get("ai_label_text", ""))
        self._disclaimer = str(tok.get("disclaimer", ""))
        self._price_note = str((ledger.config or {}).get("params_status", ""))

    def close(self):
        with self._lock:
            self._conn.close()

    # -- supply face (production = BigLife behavior feed) ---------------

    def ingest_supply_event(self, event_id, resident_id, event_kind,
                            occurred_utc, content):
        """Deterministic behavior-event supply face. The sandbox
        probe stands in for the BigLife IF-7/IF-10 feed; the face
        validates shape only and never invents content. A
        duplicate event id is rejected with zero rows."""
        eid = str(event_id or "").strip()
        rid = str(resident_id or "").strip()
        kind = str(event_kind or "").strip()
        ts = str(occurred_utc or "").strip()
        if not eid or not rid:
            raise GrowthArchiveError(E_GA_BAD_EVENT, "id/resident required")
        if kind not in ("year_ring", "dialogue", "city_story", "memorial"):
            raise GrowthArchiveError(E_GA_BAD_EVENT, kind)
        if not ts:
            raise GrowthArchiveError(E_GA_BAD_EVENT, "timestamp required")
        if not isinstance(content, (dict, list)) or not content:
            raise GrowthArchiveError(E_GA_BAD_EVENT,
                                     "behavior payload required")
        payload = json.dumps(content, sort_keys=True)
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM ga_resident_events WHERE event_id = ?",
                (eid,)).fetchone()
            if row is not None:
                raise GrowthArchiveError(E_GA_DUP_EVENT, eid)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO ga_resident_events (event_id, resident_id,"
                    " event_kind, occurred_utc, content_json)"
                    " VALUES (?,?,?,?,?)",
                    (eid, rid, kind, ts, payload))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise GrowthArchiveError(E_GA_DUP_EVENT, eid)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"event_id": eid, "resident_id": rid, "event_kind": kind,
                "ingested": True}

    def _require_resident(self, resident_id):
        rid = str(resident_id or "").strip()
        if not rid:
            raise GrowthArchiveError(E_GA_BAD_ARGS, "resident id required")
        row = self._conn.execute(
            "SELECT 1 FROM ga_resident_events WHERE resident_id = ?"
            " LIMIT 1", (rid,)).fetchone()
        if row is None:
            raise GrowthArchiveError(E_GA_UNKNOWN, rid)
        return rid

    # -- subscription face ------------------------------------------------

    @staticmethod
    def _check_price(token_price):
        if (not isinstance(token_price, int) or isinstance(token_price, bool)
                or token_price <= 0):
            raise GrowthArchiveError(E_GA_BAD_PRICE, str(token_price))

    def subscribe(self, account_id, resident_id, sub_month, token_price,
                  ref):
        """One monthly archive subscription = exactly one spend
        bound to its tx; a repeated subscription of the same
        (account, resident, month) is rejected BEFORE the spend,
        so the balance never moves twice; another month is a
        separate legal purchase."""
        if not str(account_id or "").startswith("usr:"):
            raise GrowthArchiveError(E_GA_BAD_ACCOUNT, account_id)
        month = str(sub_month or "").strip()
        if not _MONTH_RE.match(month):
            raise GrowthArchiveError(E_GA_BAD_MONTH, month)
        self._check_price(token_price)
        ref = str(ref or "").strip()
        if not ref:
            raise GrowthArchiveError(E_GA_BAD_ARGS, "purchase ref required")
        with self._lock:
            rid = self._require_resident(resident_id)
            row = self._conn.execute(
                "SELECT sub_id FROM ga_subscriptions WHERE account_id = ?"
                " AND resident_id = ? AND sub_month = ?",
                (account_id, rid, month)).fetchone()
            if row is not None:
                raise GrowthArchiveError(E_GA_DUP,
                                        "%s/%s/%s" % (account_id, rid,
                                                      month))
            self.led.ensure_account(account_id,
                                     census_avatar_id=account_id[4:])
            spend_tx = self.led.spend(account_id, token_price, ref,
                                      "order")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO ga_subscriptions (account_id, resident_id,"
                    " sub_month, token_price, bound_spend_tx,"
                    " subscribed_utc) VALUES (?,?,?,?,?,?)",
                    (account_id, rid, month, token_price, spend_tx,
                     _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise GrowthArchiveError(E_GA_DUP,
                                        "%s/%s/%s" % (account_id, rid,
                                                      month))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"sub_id": cur.lastrowid, "account_id": account_id,
                "resident_id": rid, "sub_month": month,
                "token_price": token_price, "spend_tx": spend_tx}

    # -- read faces -------------------------------------------------------

    def _require_entitlement(self, account_id, rid, month):
        row = self._conn.execute(
            "SELECT bound_spend_tx FROM ga_subscriptions"
            " WHERE account_id = ? AND resident_id = ? AND sub_month = ?",
            (account_id, rid, month)).fetchone()
        if row is None:
            raise GrowthArchiveError(E_GA_DENIED,
                                     "%s on %s/%s" % (account_id, rid,
                                                      month))
        return row[0]

    @staticmethod
    def _month_window(occurred_utc, month):
        return str(occurred_utc or "").startswith(month)

    def archive_page(self, account_id, resident_id, at_month):
        """Read-only resident archive page. Fail-closed: without
        a subscription for that exact month window the call is
        rejected with zero charge. Every rendered item derives
        from the supply-events table only (structural
        no-fabrication); the derived city-story rows carry the
        AIGC label; the persistent disclaimer rides on every
        page. Zero token movement."""
        rid = str(resident_id or "").strip()
        if not rid:
            raise GrowthArchiveError(E_GA_BAD_ARGS, "resident id required")
        month = str(at_month or "").strip()
        if not _MONTH_RE.match(month):
            raise GrowthArchiveError(E_GA_BAD_MONTH, month)
        with self._lock:
            if self._conn.execute(
                    "SELECT 1 FROM ga_resident_events WHERE resident_id = ?"
                    " LIMIT 1", (rid,)).fetchone() is None:
                raise GrowthArchiveError(E_GA_UNKNOWN, rid)
            tx = self._require_entitlement(account_id, rid, month)
            rows = self._conn.execute(
                "SELECT event_id, event_kind, occurred_utc, content_json"
                " FROM ga_resident_events WHERE resident_id = ?"
                " ORDER BY occurred_utc, event_id", (rid,)).fetchall()
        year_ring, dialogue, city_story, memorial = [], [], [], []
        for eid, kind, ts, payload in rows:
            item = {"event_id": eid, "occurred_utc": ts,
                    "content": json.loads(payload)}
            if kind == "year_ring":
                year_ring.append(item)
            elif kind == "dialogue":
                if self._month_window(ts, month):
                    dialogue.append(item)
            elif kind == "city_story":
                if self._month_window(ts, month):
                    city_story.append(dict(item, ai_generated=True,
                                           ai_label=self._ai_label))
            else:
                memorial.append(item)
        return {"resident_id": rid, "month": month, "tx": tx,
                "year_ring": year_ring, "dialogue_digest": dialogue,
                "city_story_monthly": city_story,
                "memorial_pages": memorial,
                "disclaimer": self._disclaimer,
                "price_note": self._price_note}

    def subscriptions_view(self, account_id):
        """Per-account subscription view: resident, month, price,
        bound spend tx (provenance) - subscription rows are
        immutable."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT sub_id, resident_id, sub_month, token_price,"
                " bound_spend_tx FROM ga_subscriptions"
                " WHERE account_id = ? ORDER BY sub_id",
                (account_id,)).fetchall()
        return {"account_id": account_id,
                "subscriptions": [{"sub_id": int(r[0]),
                                  "resident_id": r[1], "sub_month": r[2],
                                  "token_price": int(r[3]),
                                  "spend_tx": r[4]} for r in rows]}

    def residents_view(self):
        """Supply census read view: resident ids with event
        counts, derived from the events table only."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT resident_id, COUNT(*) FROM ga_resident_events"
                " GROUP BY resident_id ORDER BY resident_id").fetchall()
        return {"residents": [{"resident_id": r[0], "events": int(r[1])}
                              for r in rows]}

    def compliance_view(self):
        """Runtime-derived compliance block, verbatim from the
        ledger config (zero literals in this module)."""
        return {"ai_label": self._ai_label,
                "disclaimer": self._disclaimer,
                "price_note": self._price_note}
