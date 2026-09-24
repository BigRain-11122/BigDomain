"""Membership entitlement domain sandbox core (BigDomain P-47-5b).

Implements the pre-registered criteria AC-M1..AC-M16 from
docs/spec/membership-spec.md section 1 (criteria were registered
before this code; honesty law). Stdlib only: tier prices and every
naming/numeric value are [needs-CEO] approval faces (config.json
placeholders, never self-served); the real subscription channel is the
pay piece's virtual payment track, blocked on CEO account-domain
physical items (merchant IDs/keys live only in .env, production).

Docks (referenced products, not copies):
  - lobby sec_gate : member text faces gate (AC-M7; an unwired gate
    refuses startup E_GATE_OFFLINE, fifth piece of the same-origin
    family: lobby AC-S4 / ledger AC-L8 / ugc AC-U2 / pay AC-Y8 /
    member AC-M7)
  - pay PayOrders  : grant-source authenticity (grant_row read face,
    AC-M2) and the birth-cert judgement source (grants_for face,
    AC-M3; lobby E_ENTRANCE_REQUIRED enforcement lives in the lobby
    piece - referenced, never re-implemented)

Two-domain isolation laws (BLUEPRINT 5.4, double insurance):
  - fiat exists only in the pay order domain; this schema carries zero
    fiat-named columns and SQLite refuses any insert naming them
    (AC-M10, same method as pay AC-Y7)
  - credits are service quotas, never tokens: this domain never writes
    any ledger table, carries zero token columns, and has no token verb
    anywhere in its SQL (AC-M11); token rewards flow only through the
    ugc/revenue pipeline (referenced, never re-issued here)

Public-stream zero-double-write (AC-M13): purchase and renewal events
ride the pay.success stream the pay piece already emitted at grant
time; this domain adds NO public event type - every domain change lands
in member_audit rows instead.

Blocked consumption faces stay references, not pre-builds (spec
section 0 honest note): credit execution = BigMoney/Biggame production
lines, resident companion = BigLife line pipeline, building naming
consumption = FluxVerse DevLoop, private rooms/skins = FluxVerse /
visitor-end pieces. This sandbox keeps the quota journal, the voucher
account and the privilege derivation; downstream systems wire at their
own arrival.

Documented implementation deltas beyond the spec section 2 DDL:
  - source_grant_id carries no cross-file FK: the member DB and the pay
    DB are separate SQLite files and SQLite cannot enforce a foreign key
    across files; activation validates the grant through the pay dock
    (AC-M2) and reconcile check 1 re-verifies every row
  - member_credit_events.ref_type narrows to 'activation' /
    'service_ticket' / 'service_refund' (classification keys for the
    conservation identity, reconcile check 2)
  - trg_period_insert: periods are born active only (terminal states
    cannot be born via raw SQL, AC-M12 method)
  - trg_voucher_status: voucher edges unused->used / unused->expired
    enforced at the DB layer (AC-M12 method applied to the voucher
    status machine)
  - v_credit_balance: derived balance view (append-only journal +
    view, machine-checkable conservation, AC-M4)

Encoding discipline: this script stays ASCII; Chinese copy lives in
config.json.

Run (readiness self-check = sandbox serve mode):
    python member.py
    python member.py --config config.json --db data/member.db
"""

import argparse
import datetime
import hashlib
import json
import os
import sqlite3
import sys
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
_PAY = os.path.normpath(os.path.join(BASE, "..", "pay"))
_LEDGER = os.path.normpath(os.path.join(BASE, "..", "ledger"))
for _p in (_LOBBY, _PAY, _LEDGER, BASE):
    # deterministic order after the loop: BASE, _LEDGER, _PAY, _LOBBY -
    # this package's catalog/member/sweep/reconcile win over same-named
    # pay modules, while sec_gate resolves to the lobby product and
    # orders/ledger resolve to the pay/ledger products
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

from sec_gate import ContentRejectedError, GateOfflineError  # lobby product
import catalog                                        # this package
import orders as pay_orders                            # pay product (main wiring)

# error codes (ASCII)
E_NO_BINDING = "E_NO_BINDING"                    # AC-M3 (AC-L11/AC-Y13 family)
E_BAD_GRANT_SOURCE = "E_BAD_GRANT_SOURCE"        # AC-M2
E_NO_ACTIVE_PERIOD = "E_NO_ACTIVE_PERIOD"        # AC-M6/AC-M16
E_TIER_REQUIRED = "E_TIER_REQUIRED"              # AC-M6
E_PERIOD_EXPIRED = "E_PERIOD_EXPIRED"            # AC-M4 consume face
E_NO_CREDITS = "E_NO_CREDITS"                    # AC-M4
E_REFUND_EXCEEDS = "E_REFUND_EXCEEDS"            # refund cap (spec 3 note)
E_VOUCHER_USED = "E_VOUCHER_USED"                # AC-M16
E_BAD_STATE = "E_BAD_STATE"
E_CONTENT_REJECTED = "E_CONTENT_REJECTED"        # AC-M7 (sec_gate same origin)
E_BAD_TRANSITION = "E_BAD_TRANSITION"            # AC-M12 (trigger)


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(ts):
    return datetime.datetime.strptime(str(ts), "%Y-%m-%dT%H:%M:%SZ")


def add_days(ts, days):
    return (parse_iso(ts) + datetime.timedelta(days=int(days))
            ).strftime("%Y-%m-%dT%H:%M:%SZ")


def _h(*parts):
    """Content-addressed id over the given canonical parts."""
    return hashlib.sha256("|".join(str(p) for p in parts)
                          .encode("utf-8")).hexdigest()[:16]


def compute_period_id(avatar, product_key, period_no):
    return _h("period", avatar, product_key, int(period_no))


def compute_voucher_id(avatar, period_id, voucher_type):
    return _h("voucher", avatar, period_id, voucher_type)


class MemberError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


_SCHEMA = """
CREATE TABLE IF NOT EXISTS member_periods (
  period_id        TEXT PRIMARY KEY,
  census_avatar_id TEXT NOT NULL,
  product_id       TEXT NOT NULL,
  tier             TEXT NOT NULL,
  period_no        INTEGER NOT NULL,
  start_utc        TEXT NOT NULL,
  end_utc          TEXT NOT NULL,
  status           TEXT NOT NULL DEFAULT 'active'
                   CHECK (status IN ('active','expired')),
  source_grant_id  TEXT NOT NULL UNIQUE
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_periods_line
  ON member_periods (census_avatar_id, product_id, period_no);
CREATE TABLE IF NOT EXISTS member_credit_events (
  event_id         TEXT PRIMARY KEY,
  census_avatar_id TEXT NOT NULL,
  period_id        TEXT NOT NULL REFERENCES member_periods(period_id),
  delta            INTEGER NOT NULL CHECK (delta <> 0),
  reason           TEXT NOT NULL CHECK (reason IN ('grant','consume','expire')),
  ref              TEXT,
  ref_type         TEXT,
  ts_utc           TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS member_vouchers (
  voucher_id       TEXT PRIMARY KEY,
  census_avatar_id TEXT NOT NULL,
  period_id        TEXT NOT NULL REFERENCES member_periods(period_id),
  voucher_type     TEXT NOT NULL,
  demand_text      TEXT,
  status           TEXT NOT NULL DEFAULT 'unused'
                   CHECK (status IN ('unused','used','expired')),
  consumed_utc     TEXT,
  UNIQUE (census_avatar_id, period_id, voucher_type)
);
CREATE TABLE IF NOT EXISTS member_audit (
  audit_id         TEXT PRIMARY KEY,
  census_avatar_id TEXT NOT NULL,
  kind             TEXT NOT NULL CHECK (kind IN ('period','expire','credits','voucher')),
  detail           TEXT NOT NULL,
  ts_utc           TEXT NOT NULL
);
"""

_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS trg_period_insert
BEFORE INSERT ON member_periods
WHEN NEW.status <> 'active'
BEGIN
  SELECT RAISE(ABORT, 'E_BAD_TRANSITION');
END;
CREATE TRIGGER IF NOT EXISTS trg_period_status
BEFORE UPDATE OF status ON member_periods
WHEN NEW.status <> OLD.status
BEGIN
  SELECT RAISE(ABORT, 'E_BAD_TRANSITION')
   WHERE NOT (OLD.status = 'active' AND NEW.status = 'expired');
END;
CREATE TRIGGER IF NOT EXISTS trg_credit_balance
AFTER INSERT ON member_credit_events
BEGIN
  SELECT RAISE(ABORT, 'E_NEGATIVE_CREDITS')
   WHERE (SELECT COALESCE(SUM(delta), 0) FROM member_credit_events
           WHERE census_avatar_id = NEW.census_avatar_id
             AND period_id = NEW.period_id) < 0;
END;
CREATE TRIGGER IF NOT EXISTS trg_voucher_status
BEFORE UPDATE OF status ON member_vouchers
WHEN NEW.status <> OLD.status
BEGIN
  SELECT RAISE(ABORT, 'E_BAD_TRANSITION')
   WHERE NOT ((OLD.status = 'unused' AND NEW.status = 'used')
           OR (OLD.status = 'unused' AND NEW.status = 'expired'));
END;
CREATE VIEW IF NOT EXISTS v_credit_balance AS
SELECT census_avatar_id, period_id, COALESCE(SUM(delta), 0) AS balance
  FROM member_credit_events
 GROUP BY census_avatar_id, period_id;
"""


class MemberStore:
    """Single-writer member domain: one connection guarded by one lock;
    every write opens with BEGIN IMMEDIATE (SQLite WAL discipline).
    Underscore-prefixed query helpers are lock-free: the CALLER holds
    the lock (un-nested acquisition would deadlock, plain Lock)."""

    def __init__(self, config, db_path, pay):
        self.catalog = catalog.Catalog.from_config(config)  # AC-M1 refusal
        if pay is None:
            raise GateOfflineError("pay dock is mandatory (AC-M2 grant source)")
        self.pay = pay
        self.db_path = db_path
        parent = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(parent, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA + "\n" + _TRIGGERS)

    def close(self):
        with self._lock:
            self._conn.close()

    # ---- compliance face (every response) -------------------------------

    def _face(self, out):
        """Server-authoritative compliance fields: the AI marker (0 = this
        face presents no AI copy; faces that do override to 1, AC-M8) and
        the resident non-advisory disclaimer (AC-M9)."""
        out["ai_generated"] = 0
        out["disclaimer"] = self.catalog.disclaimer
        out["persistent"] = True
        return out

    # ---- audit + journal helpers (caller holds the lock) -------------------

    def _audit(self, avatar, kind, detail, audit_id, ts=None):
        self._conn.execute(
            "INSERT OR IGNORE INTO member_audit (audit_id, census_avatar_id,"
            " kind, detail, ts_utc) VALUES (?,?,?,?,?)",
            (audit_id, avatar, kind, detail, ts or now_utc()))

    def _credit_event(self, avatar, period_id, delta, reason,
                      ref=None, ref_type=None, ts=None):
        """Append one journal row with a deterministic content-addressed
        id (seq = journal length for the period, single writer)."""
        seq = self._conn.execute(
            "SELECT COUNT(*) FROM member_credit_events WHERE period_id = ?",
            (period_id,)).fetchone()[0]
        event_id = _h("credit", period_id, reason, int(delta),
                      ref or "", ref_type or "", int(seq))
        self._conn.execute(
            "INSERT INTO member_credit_events (event_id, census_avatar_id,"
            " period_id, delta, reason, ref, ref_type, ts_utc)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (event_id, avatar, period_id, int(delta), reason,
             ref or None, ref_type or None, ts or now_utc()))
        self._audit(avatar, "credits",
                    "event=%s reason=%s delta=%d period=%s"
                    % (event_id, reason, int(delta), period_id),
                    _h("audit", "credits", event_id), ts)
        return event_id

    def _active_rows(self, avatar):
        """Active periods, soonest-expiring first (quota draw order).
        Lock-free: caller holds the lock."""
        rows = self._conn.execute(
            "SELECT period_id, tier, period_no, start_utc, end_utc FROM"
            " member_periods WHERE census_avatar_id = ? AND status = 'active'"
            " ORDER BY end_utc ASC", (avatar,)).fetchall()
        return [{"period_id": r[0], "tier": r[1], "period_no": r[2],
                 "start_utc": r[3], "end_utc": r[4]} for r in rows]

    def _balance_of(self, period_id):
        return int(self._conn.execute(
            "SELECT COALESCE(SUM(delta), 0) FROM member_credit_events"
            " WHERE period_id = ?", (period_id,)).fetchone()[0])

    def _period_face_row(self, period_id, product, avatar, idempotent):
        """Lock-free: caller holds the lock."""
        row = self._conn.execute(
            "SELECT tier, period_no, start_utc, end_utc, status FROM"
            " member_periods WHERE period_id = ?", (period_id,)).fetchone()
        return {"census_avatar_id": avatar, "period_id": period_id,
                "product": product, "tier": row[0], "period_no": row[1],
                "start_utc": row[2], "end_utc": row[3], "status": row[4],
                "credits_balance": self._balance_of(period_id),
                "idempotent": bool(idempotent)}

    def _latest_voucher(self, avatar, voucher_type, status=None):
        """Lock-free: caller holds the lock."""
        sql = ("SELECT voucher_id, status, demand_text FROM member_vouchers"
               " WHERE census_avatar_id = ? AND voucher_type = ?")
        args = [avatar, str(voucher_type)]
        if status is not None:
            sql += " AND status = ?"
            args.append(status)
        # insertion order, not id-hash order: content-addressed ids do
        # not sort chronologically (takeover fix; the hash-ordered pick
        # could return an older period's voucher and shadow the newest)
        sql += " ORDER BY rowid DESC LIMIT 1"
        return self._conn.execute(sql, args).fetchone()

    # ---- activation (AC-M2/M3/M16 dock face) ------------------------------

    def activate(self, grant_id, census_avatar_id, client_hints=None):
        """Activate one real pay grant: tier products open a period (+ the
        monthly credit grant + voucher rows for voucher tiers), every
        paid product stamps the permanent birth-cert marker. Client hints
        are ignored (AC-M5 server authority)."""
        if isinstance(client_hints, dict):
            pass  # server authority only: nothing is ever read from here
        avatar = str(census_avatar_id or "").strip()
        if not avatar:
            raise MemberError(E_NO_BINDING, "census avatar binding required (AC-M3)")
        grant = self.pay.grant_row(str(grant_id or ""))
        if grant is None:
            raise MemberError(E_BAD_GRANT_SOURCE,
                              "unknown grant id (AC-M2): %s" % grant_id)
        if grant["census_avatar_id"] != avatar:
            raise MemberError(E_BAD_GRANT_SOURCE,
                              "grant belongs to another avatar (AC-M2)")
        entitlement = str(grant["entitlement"])
        tier = self.catalog.products.get(entitlement)
        ts = now_utc()
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            committed = False
            try:
                # birth cert: permanent from the FIRST paid activation
                # (C0; the entrance judgement itself derives from the pay
                # grants face, which never expires - AC-M3)
                self._audit(avatar, "period",
                            "birth_cert avatar=%s grant=%s" % (avatar, grant_id),
                            _h("audit", "birth", avatar), ts)
                if tier is None:
                    # paid product outside the tier matrix (e.g. the
                    # compute pack): birth-cert-only activation
                    self._conn.execute("COMMIT")
                    committed = True
                    result = self._face({
                        "census_avatar_id": avatar, "product": entitlement,
                        "tier": None, "birth_cert": True, "permanent": True,
                        "idempotent": False,
                    })
                else:
                    existing = self._conn.execute(
                        "SELECT period_id FROM member_periods"
                        " WHERE source_grant_id = ?", (str(grant_id),)).fetchone()
                    if existing is not None:
                        # same grant twice = same period, zero re-issue (AC-M2)
                        self._conn.execute("COMMIT")
                        committed = True
                        result = self._face(self._period_face_row(
                            existing[0], entitlement, avatar, True))
                    else:
                        line = self._conn.execute(
                            "SELECT COUNT(*) FROM member_periods"
                            " WHERE census_avatar_id = ? AND product_id = ?",
                            (avatar, entitlement)).fetchone()[0]
                        period_no = int(line) + 1
                        active_end = self._conn.execute(
                            "SELECT end_utc FROM member_periods"
                            " WHERE census_avatar_id = ? AND product_id = ?"
                            " AND status = 'active' ORDER BY period_no DESC"
                            " LIMIT 1", (avatar, entitlement)).fetchone()
                        # stacking law: start = max(now, active end) - a
                        # lapsed-but-unswept active line must never start
                        # the renewal in the past (takeover fix)
                        start = (max(ts, active_end[0])
                                 if active_end is not None else ts)
                        end = add_days(start, tier.period_days)
                        period_id = compute_period_id(avatar, entitlement,
                                                      period_no)
                        self._conn.execute(
                            "INSERT INTO member_periods (period_id,"
                            " census_avatar_id, product_id, tier, period_no,"
                            " start_utc, end_utc, status, source_grant_id)"
                            " VALUES (?,?,?,?,?,?,?,?,?)",
                            (period_id, avatar, entitlement, tier.key,
                             period_no, start, end, "active", str(grant_id)))
                        self._credit_event(avatar, period_id,
                                           tier.monthly_credits, "grant",
                                           None, "activation", ts)
                        vouchers_opened = []
                        for vtype, priv in sorted(self.catalog.vouchers.items()):
                            if priv in tier.privileges:
                                vid = compute_voucher_id(avatar, period_id, vtype)
                                cur = self._conn.execute(
                                    "INSERT OR IGNORE INTO member_vouchers"
                                    " (voucher_id, census_avatar_id, period_id,"
                                    " voucher_type, status) VALUES (?,?,?,?,?)",
                                    (vid, avatar, period_id, vtype, "unused"))
                                if cur.rowcount:
                                    vouchers_opened.append(vtype)
                                    self._audit(avatar, "voucher",
                                                "voucher=%s opened type=%s"
                                                % (vid, vtype),
                                                _h("audit", "voucher-open", vid),
                                                ts)
                        self._audit(avatar, "period",
                                    "period=%s opened tier=%s grant=%s"
                                    % (period_id, tier.key, grant_id),
                                    _h("audit", "period", period_id), ts)
                        self._conn.execute("COMMIT")
                        committed = True
                        result = self._face(self._period_face_row(
                            period_id, entitlement, avatar, False))
                        result["vouchers_opened"] = vouchers_opened
            except BaseException:
                if not committed:
                    self._conn.execute("ROLLBACK")
                raise
        return result

    # ---- birth cert face (AC-M3) -------------------------------------------

    def birth_cert_face(self, census_avatar_id):
        """Permanent entrance qualification (C0): derives from the pay
        grants face - the lobby E_ENTRANCE_REQUIRED judgement source -
        which never expires; member expiry can never revoke it."""
        avatar = str(census_avatar_id or "").strip()
        grants = self.pay.grants_for(avatar)
        items = grants.get("items") or []
        with self._lock:
            row = self._conn.execute(
                "SELECT audit_id FROM member_audit WHERE audit_id = ?",
                (_h("audit", "birth", avatar),)).fetchone()
            marker = row[0] if row else None
        return self._face({
            "census_avatar_id": avatar,
            "birth_cert": bool(items), "permanent": True,
            "first_granted_utc": items[0]["granted_utc"] if items else None,
            "member_domain_marker": bool(marker),
            "judgement_source": "pay.grants_for (lobby E_ENTRANCE_REQUIRED face)",
        })

    # ---- privilege faces (AC-M5/M6/M8) --------------------------------------

    def privileges_for(self, census_avatar_id, client_hints=None):
        """Server-derived privilege set from the active periods' tiers;
        client-claimed tiers/privileges are ignored (AC-M5)."""
        if isinstance(client_hints, dict):
            pass  # zero client authority
        avatar = str(census_avatar_id or "").strip()
        with self._lock:
            periods = self._active_rows(avatar)
        tiers = []
        privileges = []
        for period in periods:
            tier = self.catalog.tiers[period["tier"]]
            if tier.key not in tiers:
                tiers.append(tier.key)
            for priv in tier.privileges:
                if priv not in privileges:
                    privileges.append(priv)
        return self._face({
            "census_avatar_id": avatar, "active": bool(periods),
            "tiers": tiers, "privileges": privileges, "periods": periods,
        })

    def has_privilege(self, census_avatar_id, privilege, client_hints=None):
        if isinstance(client_hints, dict):
            pass  # zero client authority
        if str(privilege) not in catalog.KNOWN_PRIVILEGES:
            raise MemberError(E_BAD_STATE, "unknown privilege key: %s" % privilege)
        avatar = str(census_avatar_id or "").strip()
        with self._lock:
            periods = self._active_rows(avatar)
        if not periods:
            raise MemberError(E_NO_ACTIVE_PERIOD,
                              "no active membership period (AC-M6)")
        granting = None
        for period in periods:
            if str(privilege) in self.catalog.tiers[period["tier"]].privileges:
                granting = period
                break
        if granting is None:
            raise MemberError(E_TIER_REQUIRED,
                              "privilege %s not in active tiers %s (AC-M6)"
                              % (privilege, sorted(p["tier"] for p in periods)))
        return self._face({"census_avatar_id": avatar, "granted": True,
                           "privilege": str(privilege), "tier": granting["tier"],
                           "period_id": granting["period_id"]})

    def companion_face(self, census_avatar_id, client_hints=None):
        """AI-produced presentation face stub: the resident companion
        lines dock at the BigLife pipeline (blocked consumption face,
        referenced not pre-built). The AI marker stays server authority
        and every presentation of this face carries the label (AC-M8)."""
        hints = dict(client_hints or {})
        hints.pop("ai_generated", None)  # forgery ignored (AC-M8)
        self.has_privilege(census_avatar_id, "resident_companion")
        out = self._face({
            "census_avatar_id": str(census_avatar_id or "").strip(),
            "face": "resident_companion",
            "dock": "BigLife line pipeline (referenced; blocked face)",
        })
        out["ai_generated"] = 1  # this face presents AI-produced copy
        out["ai_label"] = self.catalog.ai_label
        return out

    # ---- credits faces (AC-M4) -----------------------------------------------

    def balance_face(self, census_avatar_id):
        avatar = str(census_avatar_id or "").strip()
        with self._lock:
            rows = self._conn.execute(
                "SELECT p.period_id, p.tier, p.status, p.start_utc, p.end_utc"
                " FROM member_periods p WHERE p.census_avatar_id = ?"
                " ORDER BY p.period_no", (avatar,)).fetchall()
            periods = [{"period_id": r[0], "tier": r[1], "status": r[2],
                        "start_utc": r[3], "end_utc": r[4],
                        "balance": self._balance_of(r[0])} for r in rows]
        return self._face({"census_avatar_id": avatar, "periods": periods,
                           "carryover": False,
                           "carryover_note":
                               "unused credits forfeit at period end"
                               " ([needs-CEO] default: no carryover)"})

    def consume_credits(self, census_avatar_id, count, ref=None, ref_type=None):
        """Draw service credits across active periods, soonest-expiring
        first (quota semantics). Refusal families: no active period =
        E_PERIOD_EXPIRED; balance short = E_NO_CREDITS, zero writes and
        the balance is untouched."""
        try:
            count = int(count)
        except (TypeError, ValueError):
            raise MemberError(E_BAD_STATE, "count not an int") from None
        if count <= 0:
            raise MemberError(E_BAD_STATE, "count must be positive")
        avatar = str(census_avatar_id or "").strip()
        with self._lock:
            periods = self._conn.execute(
                "SELECT period_id FROM member_periods"
                " WHERE census_avatar_id = ? AND status = 'active'"
                " ORDER BY end_utc ASC", (avatar,)).fetchall()
            if not periods:
                raise MemberError(E_PERIOD_EXPIRED,
                                  "no active membership period (AC-M4)")
            balances = {p[0]: self._balance_of(p[0]) for p in periods}
            total = sum(balances.values())
            if total < count:
                raise MemberError(E_NO_CREDITS,
                                  "balance=%d want=%d (AC-M4)" % (total, count))
            remaining = count
            draws = []
            self._conn.execute("BEGIN IMMEDIATE")
            committed = False
            try:
                for period_id, in periods:
                    if remaining <= 0:
                        break
                    take = min(int(balances[period_id]), remaining)
                    if take <= 0:
                        continue
                    self._credit_event(avatar, period_id, -take, "consume",
                                       ref, ref_type)
                    draws.append({"period_id": period_id, "taken": take})
                    remaining -= take
                self._conn.execute("COMMIT")
                committed = True
            except BaseException:
                if not committed:
                    self._conn.execute("ROLLBACK")
                raise
        return self._face({"census_avatar_id": avatar, "draws": draws,
                           "consumed": count,
                           "balance_total_after": total - count})

    def refund_credits(self, census_avatar_id, count, period_id,
                       ref=None, ref_type=None):
        """Failed-service credit backfill (spec section 3: reserve first,
        execute later, refund the failure with an audit row). Cap:
        refunds can never exceed what the period actually consumed."""
        try:
            count = int(count)
        except (TypeError, ValueError):
            raise MemberError(E_BAD_STATE, "count not an int") from None
        if count <= 0:
            raise MemberError(E_BAD_STATE, "count must be positive")
        avatar = str(census_avatar_id or "").strip()
        with self._lock:
            row = self._conn.execute(
                "SELECT census_avatar_id, status FROM member_periods"
                " WHERE period_id = ?", (str(period_id),)).fetchone()
            if row is None or row[0] != avatar:
                raise MemberError(E_BAD_STATE, "unknown period")
            if row[1] != "active":
                raise MemberError(E_PERIOD_EXPIRED,
                                  "period no longer active (AC-M4)")
            consumed = -self._conn.execute(
                "SELECT COALESCE(SUM(delta), 0) FROM member_credit_events"
                " WHERE period_id = ? AND reason = 'consume'",
                (str(period_id),)).fetchone()[0]
            refunded = self._conn.execute(
                "SELECT COALESCE(SUM(delta), 0) FROM member_credit_events"
                " WHERE period_id = ? AND reason = 'grant'"
                " AND ref_type = 'service_refund'",
                (str(period_id),)).fetchone()[0]
            if refunded + count > consumed:
                raise MemberError(E_REFUND_EXCEEDS,
                                  "refunded+%d > consumed %d"
                                  % (count, consumed))
            self._conn.execute("BEGIN IMMEDIATE")
            committed = False
            try:
                self._credit_event(avatar, str(period_id), count, "grant",
                                   ref, "service_refund")
                self._conn.execute("COMMIT")
                committed = True
                balance = self._balance_of(str(period_id))
            except BaseException:
                if not committed:
                    self._conn.execute("ROLLBACK")
                raise
        return self._face({"census_avatar_id": avatar, "period_id": period_id,
                           "refunded": count, "balance_after": int(balance)})

    # ---- expiry sweep (AC-M12) ----------------------------------------------

    def sweep_expired(self, now=None):
        """Expire past-due active periods (end_utc + grace days): the
        one-way status flip is trigger-enforced, remaining credits are
        forfeited as expire rows (no carryover by default - honest
        presentation, never a silent balance), unused vouchers expire
        with one audit row each, one expire audit per period. Idempotent:
        a re-run finds nothing past due and writes nothing."""
        ts = str(now or now_utc())
        expired = 0
        with self._lock:
            rows = self._conn.execute(
                "SELECT period_id, census_avatar_id, tier, end_utc FROM"
                " member_periods WHERE status = 'active'").fetchall()
            for period_id, avatar, tier_key, end_utc in rows:
                tier = self.catalog.tiers.get(str(tier_key))
                grace = tier.grace_days if tier is not None else 0
                if add_days(end_utc, grace) > ts:
                    continue  # ISO strings compare chronologically
                self._conn.execute("BEGIN IMMEDIATE")
                committed = False
                try:
                    self._conn.execute(
                        "UPDATE member_periods SET status = 'expired'"
                        " WHERE period_id = ?", (period_id,))
                    balance = self._balance_of(period_id)
                    if balance > 0:
                        self._credit_event(avatar, period_id, -balance,
                                           "expire", None, None, ts)
                    vouchers = self._conn.execute(
                        "SELECT voucher_id FROM member_vouchers"
                        " WHERE period_id = ? AND status = 'unused'",
                        (period_id,)).fetchall()
                    for voucher_id, in vouchers:
                        self._conn.execute(
                            "UPDATE member_vouchers SET status = 'expired'"
                            " WHERE voucher_id = ?", (voucher_id,))
                        self._audit(avatar, "voucher",
                                     "voucher=%s expired with period"
                                     % voucher_id,
                                     _h("audit", "voucher-expire",
                                        voucher_id), ts)
                    self._audit(avatar, "expire",
                                "period=%s expired credits_forfeited=%d"
                                % (period_id, balance),
                                _h("audit", "expire", period_id), ts)
                    self._conn.execute("COMMIT")
                    committed = True
                    expired += 1
                except BaseException:
                    if not committed:
                        self._conn.execute("ROLLBACK")
                    raise
        return expired

    # ---- voucher faces (AC-M16/M7) -------------------------------------------

    def set_voucher_text(self, census_avatar_id, voucher_type, text,
                         client_hints=None):
        """Member text input face (AC-M7): the naming demand passes the
        content gate BEFORE anything is written - a gate hit means zero
        writes, zero open vouchers."""
        if isinstance(client_hints, dict):
            pass  # zero client authority
        if str(voucher_type) not in self.catalog.vouchers:
            raise MemberError(E_BAD_STATE, "unknown voucher type")
        avatar = str(census_avatar_id or "").strip()
        demand = str(text or "")
        if not demand.strip():
            raise MemberError(E_BAD_STATE, "voucher text empty")
        try:
            self.catalog.gate.check_text(demand)  # gate 1 + gate 2
        except ContentRejectedError as exc:
            raise MemberError(E_CONTENT_REJECTED,
                              "gate %d wordlist hit (AC-M7)" % exc.gate) from None
        with self._lock:
            row = self._latest_voucher(avatar, voucher_type, "unused")
            if row is None:
                if not self._active_rows(avatar):
                    raise MemberError(E_NO_ACTIVE_PERIOD,
                                      "no active membership period (AC-M16)")
                raise MemberError(E_TIER_REQUIRED,
                                  "active tiers carry no voucher privilege"
                                  " (AC-M16)")
            voucher_id, _status, existing_text = row
            if existing_text:
                raise MemberError(E_BAD_STATE, "voucher text already set")
            self._conn.execute("BEGIN IMMEDIATE")
            committed = False
            try:
                self._conn.execute(
                    "UPDATE member_vouchers SET demand_text = ?"
                    " WHERE voucher_id = ?", (demand, voucher_id))
                self._audit(avatar, "voucher",
                            "voucher=%s text-set" % voucher_id,
                            _h("audit", "voucher-text", voucher_id))
                self._conn.execute("COMMIT")
                committed = True
            except BaseException:
                if not committed:
                    self._conn.execute("ROLLBACK")
                raise
        return self._face({"census_avatar_id": avatar,
                          "voucher_id": voucher_id,
                          "voucher_type": str(voucher_type),
                          "status": "unused", "demand_text_set": True})

    def use_voucher(self, census_avatar_id, voucher_type):
        """Consumption dock stub for the FluxVerse DevLoop naming face
        (blocked consumption face, referenced not pre-built): marks the
        voucher used; re-use is refused."""
        if str(voucher_type) not in self.catalog.vouchers:
            raise MemberError(E_BAD_STATE, "unknown voucher type")
        avatar = str(census_avatar_id or "").strip()
        with self._lock:
            row = self._latest_voucher(avatar, voucher_type)
            if row is None:
                raise MemberError(E_NO_ACTIVE_PERIOD,
                                  "no voucher on any period (AC-M16)")
            voucher_id, status, _text = row
            if status == "used":
                raise MemberError(E_VOUCHER_USED, "voucher already used")
            if status == "expired":
                raise MemberError(E_VOUCHER_USED,
                                  "voucher expired with its period")
            ts = now_utc()
            self._conn.execute("BEGIN IMMEDIATE")
            committed = False
            try:
                self._conn.execute(
                    "UPDATE member_vouchers SET status = 'used',"
                    " consumed_utc = ? WHERE voucher_id = ?", (ts, voucher_id))
                self._audit(avatar, "voucher", "voucher=%s used" % voucher_id,
                            _h("audit", "voucher-used", voucher_id), ts)
                self._conn.execute("COMMIT")
                committed = True
            except BaseException:
                if not committed:
                    self._conn.execute("ROLLBACK")
                raise
        return self._face({"census_avatar_id": avatar,
                          "voucher_id": voucher_id,
                          "voucher_type": str(voucher_type),
                          "status": "used", "consumed_utc": ts})


def main():
    parser = argparse.ArgumentParser(
        description="BigDomain sandbox member entitlement domain (P-47-5b)"
                    " readiness self-check")
    parser.add_argument("--config", default=os.path.join(BASE, "config.json"))
    parser.add_argument("--db", default=os.path.join(BASE, "data", "member.db"))
    parser.add_argument("--pay-config",
                        default=os.path.join(_PAY, "config.json"))
    parser.add_argument("--pay-db", default=os.path.join(_PAY, "data", "pay.db"))
    parser.add_argument("--events-db",
                        default=os.path.join(_PAY, "data", "events.db"))
    parser.add_argument("--ledger-db",
                        default=os.path.join(_LEDGER, "data", "ledger.db"))
    parser.add_argument("--ledger-config",
                        default=os.path.join(_LEDGER, "config.json"))
    args = parser.parse_args()
    store = None
    pay = None
    led = None
    events = None
    try:
        with open(args.config, encoding="utf-8") as handle:
            cfg = json.load(handle)
        with open(args.pay_config, encoding="utf-8") as handle:
            pay_cfg = json.load(handle)
        with open(args.ledger_config, encoding="utf-8") as handle:
            led_cfg = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print("E_GATE_OFFLINE: config unreadable: %s" % exc, file=sys.stderr)
        return 2
    try:
        import store as lobby_store  # lobby product (dance already ran)
        from ledger import Ledger    # ledger product
        events = lobby_store.EventStore(args.events_db)
        led = Ledger(args.ledger_db, led_cfg)
        pay = pay_orders.PayOrders(pay_cfg, args.pay_db, events, led)
        store = MemberStore(cfg, args.db, pay)
        print("member store ready: tiers=%d products=%d vouchers=%d gate=ok"
              " db=%s" % (len(store.catalog.tiers), len(store.catalog.products),
                          len(store.catalog.vouchers), args.db), flush=True)
        return 0
    except GateOfflineError as exc:
        print(str(exc), file=sys.stderr)  # serve refusal, same family
        return 2
    finally:
        if store is not None:
            store.close()
        if pay is not None:
            pay.close()
        if led is not None:
            led.close()
        if events is not None:
            events.close()


if __name__ == "__main__":
    sys.exit(main())
