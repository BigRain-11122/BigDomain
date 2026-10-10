"""Payment-state notification face sandbox (BigDomain pay piece).

Pre-registered criteria AC-PN1..AC-PN7 (state/queue/tech.md R1706
claim line, registered 2026-10-10 BEFORE this code; pre-registration
law: criteria line first, implementation second).
R1740 revocation extension (AC-VR1..VR7, state/queue/tech.md R1740
claim line, registered BEFORE this code): W15 user-side unsubscribe
is an append-only cutoff event - live-only budget semantics, the
whole (avatar, template) subscription dies (longterm + remaining
once units), re-subscribe cycle re-arms via post-cutoff grants.

Consumes the registered research signals into the pay design:
  W15 (WeChat subscribe-message official doc, global-benchmarks
       2026-10-06 entry): the notify channel is user-authorization
       gated - template ids are platform-review approved (CEO
       account-domain physical item, [needs-CEO]); grants are one-shot
       (each send consumes one budget unit) or long-term; daily send
       cap for payment-enabled miniprograms is 3M/day.
  W10 (consumer-protection regulation art. 10, global-benchmarks
       2026-10-01 entry): payment-state changes the consumer paid for
       owe a prominent notice - the two binding timepoints here are
       the grant moment (payment success) and the refund close.

Honest scope notes (never silently self-served):
  - Real template ids do NOT exist yet (CEO physical item): the
    shipped default registry carries placeholder templates with
    approved=0, so every send attempt fails closed with
    E_TEMPLATE_NOT_APPROVED and zero rows - the sandbox presents the
    real pending state instead of faking a channel. Tests approve a
    template through their own config copy (shipped config.json stays
    byte-stable).
  - This sandbox simulates the channel locally: zero real API
    touchpoints, zero keys; real wiring belongs to the bootstrap
    window (three-question gate on file).
  - Auto-wiring into orders.py (_grant / refund-close points) is a
    successor line, not this round (R1681->R1701 wiring precedent):
    callers drive the two event faces explicitly.

Single-writer discipline (member reminder precedent):
  - pay.db's single writer is orders.PayOrders; this module owns its
    OWN sqlite file (pay_notify.db) and is that file's single writer
    (BEGIN IMMEDIATE per write).
  - Order/grant state reads dock to pay.db through a READ-ONLY
    connection (reads never break the writer discipline).

Refund disambiguation: 'closed' is reachable both by timeout
(created/pending -> closed, no grant ever happened) and by refund
close (granted -> closed). The refund face accepts ONLY the latter:
a closed order WITH a pay_grants row is a refund; a closed order
without one is a timeout close and gets no refund notice (zero rows,
fail-closed).

Encoding discipline: this script stays ASCII; Chinese copy lives in
config.json.

Run (readiness self-check):
    python notify.py
    python notify.py --config config.json --db data/pay_notify.db
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

# error codes (ASCII)
E_TEMPLATE_NOT_APPROVED = "E_TEMPLATE_NOT_APPROVED"
E_PN_UNKNOWN_TEMPLATE = "E_PN_UNKNOWN_TEMPLATE"
E_PN_BAD_GRANT_TYPE = "E_PN_BAD_GRANT_TYPE"
E_PN_BAD_STATE = "E_PN_BAD_STATE"
E_PN_UNKNOWN_ORDER = "E_PN_UNKNOWN_ORDER"
E_PN_NO_DISCLAIMER = "E_PN_NO_DISCLAIMER"
E_PN_NO_PAY_DB = "E_PN_NO_PAY_DB"
E_PN_BAD_CONFIG = "E_PN_BAD_CONFIG"

# log statuses (rows; the two skipped faces double as banner queue)
ST_SENT = "sent"
ST_SKIP_BUDGET = "skipped_no_budget"
ST_SKIP_CAP = "skipped_daily_cap"

# shipped default registry: honest pending state - the real template
# ids are CEO physical items and do not exist yet (approved=0), so
# every send fails closed until they arrive and get config-approved.
_DEFAULT_TEMPLATES = {
    "tpl_pay_success_pending_ceo": {
        "approved": False,
        "copy": ("payment success notice template - placeholder, real "
                 "template id is a CEO account-domain physical item"),
    },
    "tpl_refund_pending_ceo": {
        "approved": False,
        "copy": ("refund notice template - placeholder, real template "
                 "id is a CEO account-domain physical item"),
    },
}
_DEFAULT_CAP = 3000000  # W15 official payment-enabled tier (3M/day)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pay_notify_grants (
  grant_id         TEXT PRIMARY KEY,
  census_avatar_id TEXT NOT NULL,
  template_id      TEXT NOT NULL,
  grant_type       TEXT NOT NULL CHECK (grant_type IN ('once','longterm')),
  ts_utc           TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pay_notify_revokes (
  revoke_id        TEXT PRIMARY KEY,
  census_avatar_id TEXT NOT NULL,
  template_id      TEXT NOT NULL,
  ts_utc           TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pay_notify_log (
  send_id          TEXT PRIMARY KEY,
  census_avatar_id TEXT NOT NULL,
  order_id         TEXT NOT NULL,
  template_id      TEXT NOT NULL,
  reason           TEXT NOT NULL CHECK (reason IN ('payment_success','refund')),
  status           TEXT NOT NULL CHECK (status IN
                   ('sent','skipped_no_budget','skipped_daily_cap')),
  ts_utc           TEXT NOT NULL,
  UNIQUE (order_id, reason)
);
"""


def _h(*parts):
    return hashlib.sha256("|".join(str(p) for p in parts)
                          .encode("utf-8")).hexdigest()[:16]


def now_utc():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ConfigRejected(ValueError):
    """Raised when the notify config violates fail-closed rules."""


class TemplateNotApproved(ValueError):
    """Raised when a send names an unapproved template (zero rows)."""


class PayNotifyFace(object):
    """Single writer of pay_notify.db (payment-state notify face)."""

    def __init__(self, config, db_path, pay_db=None):
        if not isinstance(config, dict):
            raise ConfigRejected("%s: config not loaded" % E_PN_BAD_CONFIG)
        comp = config.get("compliance") or {}
        self.disclaimer = str(comp.get("disclaimer", ""))
        if not self.disclaimer:
            raise ConfigRejected(
                "%s: compliance.disclaimer missing" % E_PN_NO_DISCLAIMER)
        self.ai_service = 1  # fixed, server-authoritative (AC-Y9 family)
        cfg = config.get("notify") or {}
        try:
            self.cap = int(cfg.get("daily_send_cap", _DEFAULT_CAP))
        except (TypeError, ValueError):
            raise ConfigRejected("%s: daily_send_cap invalid"
                                 % E_PN_BAD_CONFIG) from None
        if self.cap <= 0:
            raise ConfigRejected("%s: daily_send_cap must be positive"
                                 % E_PN_BAD_CONFIG)
        banned = set(config.get("copy_ban_words", []) or [])
        banned |= set((config.get("gate", {}) or {}).get(
            "forbidden_words", []) or [])
        templates = cfg.get("templates") or _DEFAULT_TEMPLATES
        if not templates:
            raise ConfigRejected("%s: template registry must not be empty"
                                 % E_PN_BAD_CONFIG)
        self.templates = {}
        for tid, row in templates.items():
            copy = str((row or {}).get("copy", ""))
            if not copy:
                raise ConfigRejected("%s: template %r empty copy"
                                     % (E_PN_BAD_CONFIG, tid))
            hit = next((w for w in banned if w and w in copy), None)
            if hit:
                raise ConfigRejected(
                    "%s: template %r copy contains banned word %r"
                    % (E_PN_BAD_CONFIG, tid, hit))
            self.templates[tid] = {"approved": bool((row or {}).get("approved")),
                                   "copy": copy}
        self.reason_templates = dict(cfg.get("reason_templates", {}) or {})
        fallback = sorted(self.templates)[0]
        for reason in ("payment_success", "refund"):
            self.reason_templates.setdefault(reason, fallback)
        self.pay_db = pay_db
        if self.pay_db and not os.path.exists(self.pay_db):
            raise ConfigRejected("%s: pay db not found: %s"
                                 % (E_PN_NO_PAY_DB, self.pay_db))
        self.db_path = db_path
        parent = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(parent, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.isolation_level = None
        # DDL rides one explicit BEGIN IMMEDIATE as separate statements
        # (executescript would auto-commit the open transaction)
        self._exec("BEGIN IMMEDIATE")
        for stmt in _SCHEMA.split(";"):
            if stmt.strip():
                self.conn.execute(stmt)
        self._exec("COMMIT")

    # ---------------- low-level helpers ----------------

    def _exec(self, sql, args=()):
        return self.conn.execute(sql, args)

    def _one(self, sql, args=()):
        row = self._exec(sql, args).fetchone()
        return row[0] if row else None

    def close(self):
        self.conn.close()

    def _face(self, out):
        """Compliance faces: fixed server-authoritative ai_service
        marker + resident disclaimer (AC-Y9/Y10 same family)."""
        out["ai_service"] = self.ai_service
        out["disclaimer"] = self.disclaimer
        return out

    # ---------------- pay.db read-only dock ----------------

    def _order_state(self, order_id):
        """Dock to pay.db read-only: returns (avatar, status,
        has_grant) or None when the order is unknown."""
        if not self.pay_db:
            raise ValueError("%s: pay db required" % E_PN_NO_PAY_DB)
        ro = sqlite3.connect("file:%s?mode=ro" % self.pay_db, uri=True)
        try:
            row = ro.execute(
                "SELECT census_avatar_id, status FROM pay_orders"
                " WHERE order_id=?", (str(order_id),)).fetchone()
            if row is None:
                return None
            avatar, status = row
            granted = ro.execute(
                "SELECT COUNT(*) FROM pay_grants WHERE order_id=?",
                (str(order_id),)).fetchone()[0]
            return str(avatar), str(status), int(granted) > 0
        finally:
            ro.close()

    # ---------------- authorization budget (W15) ----------------

    def grant_authorization(self, avatar, template_id, grant_type,
                            now=None):
        if template_id not in self.templates:
            raise ValueError("%s: %s" % (E_PN_UNKNOWN_TEMPLATE, template_id))
        if grant_type not in ("once", "longterm"):
            raise ValueError("%s: %s" % (E_PN_BAD_GRANT_TYPE, grant_type))
        ts = now or now_utc()
        # same-second re-accept (W15 once-type accumulation, or any two
        # grants for one avatar+template+type inside one second) is a
        # legitimate flow: the hash salt carries a deterministic attempt
        # suffix so the grant id never collides (append-only, no RNG;
        # discovered by the R1719 authorize suite first run).
        attempt = 0
        while True:
            salt = ts if attempt == 0 else "%s#%d" % (ts, attempt)
            gid = _h("pngrant", avatar, template_id, grant_type, salt)
            try:
                self._exec("BEGIN IMMEDIATE")
                self._exec(
                    "INSERT INTO pay_notify_grants"
                    " (grant_id, census_avatar_id, template_id, grant_type, ts_utc)"
                    " VALUES (?,?,?,?,?)",
                    (gid, avatar, template_id, grant_type, ts))
                self._exec("COMMIT")
                return gid
            except sqlite3.IntegrityError:
                self._exec("ROLLBACK")
                attempt += 1
                if attempt > 64:
                    raise

    def _budget(self, avatar, template_id):
        """Live-authorization budget (R1740 revocation semantics): the
        latest revoke event for (avatar, template) is a cutoff - grant
        rows and consumed sends at or before the cutoff are dead, only
        post-cutoff rows count. Same-second grant-after-revoke lands on
        the dead side (conservative fail-closed: a re-subscribe never
        over-sends; production re-subscribes are human-paced - honest
        note, pre-registered as ruling 2 in the tech.md claim line)."""
        cutoff = self._latest_revoke_ts(avatar, template_id)
        if cutoff is None:
            once = self._one(
                "SELECT COUNT(*) FROM pay_notify_grants"
                " WHERE census_avatar_id=? AND template_id=?"
                " AND grant_type='once'", (avatar, template_id))
            longterm = self._one(
                "SELECT COUNT(*) FROM pay_notify_grants"
                " WHERE census_avatar_id=? AND template_id=?"
                " AND grant_type='longterm'", (avatar, template_id))
            consumed = self._one(
                "SELECT COUNT(*) FROM pay_notify_log"
                " WHERE census_avatar_id=? AND template_id=?"
                " AND status='sent'", (avatar, template_id))
        else:
            once = self._one(
                "SELECT COUNT(*) FROM pay_notify_grants"
                " WHERE census_avatar_id=? AND template_id=?"
                " AND grant_type='once' AND ts_utc>?",
                (avatar, template_id, cutoff))
            longterm = self._one(
                "SELECT COUNT(*) FROM pay_notify_grants"
                " WHERE census_avatar_id=? AND template_id=?"
                " AND grant_type='longterm' AND ts_utc>?",
                (avatar, template_id, cutoff))
            consumed = self._one(
                "SELECT COUNT(*) FROM pay_notify_log"
                " WHERE census_avatar_id=? AND template_id=?"
                " AND status='sent' AND ts_utc>?",
                (avatar, template_id, cutoff))
        return int(once or 0), int(longterm or 0), int(consumed or 0)

    def _latest_revoke_ts(self, avatar, template_id):
        return self._one(
            "SELECT MAX(ts_utc) FROM pay_notify_revokes"
            " WHERE census_avatar_id=? AND template_id=?",
            (avatar, template_id))

    def revoke_authorization(self, avatar, template_id, now=None):
        """W15 user-side unsubscribe report (R1740): the user turned
        the template subscription off on the WeChat settings side.
        Ruling 1: the kill is the WHOLE (avatar, template)
        subscription - longterm and remaining once units both die
        (the user said stop; pre-revoke sent rows stay immutable
        history). A revoke row is appended only when live budget
        exists to kill; otherwise honest nothing_to_revoke with zero
        rows (decline-needs-no-row principle, R1719 same source) -
        an immediate re-revoke is therefore a zero-row no-op."""
        if template_id not in self.templates:
            raise ValueError("%s: %s" % (E_PN_UNKNOWN_TEMPLATE, template_id))
        ts = now or now_utc()
        once, longterm, consumed = self._budget(avatar, template_id)
        if longterm <= 0 and once - consumed <= 0:
            return self._face({"status": "nothing_to_revoke",
                               "revoke_id": None,
                               "template_id": template_id,
                               "ts_utc": ts,
                               "budget": self.budget_face(avatar,
                                                          template_id)})
        attempt = 0
        while True:
            salt = ts if attempt == 0 else "%s#%d" % (ts, attempt)
            rid = _h("pnrevoke", avatar, template_id, salt)
            try:
                self._exec("BEGIN IMMEDIATE")
                self._exec(
                    "INSERT INTO pay_notify_revokes"
                    " (revoke_id, census_avatar_id, template_id, ts_utc)"
                    " VALUES (?,?,?,?)",
                    (rid, avatar, template_id, ts))
                self._exec("COMMIT")
                break
            except sqlite3.IntegrityError:
                self._exec("ROLLBACK")
                attempt += 1
                if attempt > 64:
                    raise
        return self._face({"status": "revoked", "revoke_id": rid,
                           "template_id": template_id, "ts_utc": ts,
                           "budget": self.budget_face(avatar,
                                                      template_id)})

    # ---------------- send attempt (enforcement order) ----------------

    def _attempt(self, avatar, order_id, reason, now=None):
        template_id = self.reason_templates[reason]
        row_tpl = self.templates.get(template_id)
        if row_tpl is None:
            raise ValueError("%s: %s" % (E_PN_UNKNOWN_TEMPLATE, template_id))
        if not row_tpl["approved"]:
            # zero rows, zero sends: an unapproved template must never
            # touch the log (AC-PN5 template-review gate first)
            raise TemplateNotApproved(
                "%s: %s" % (E_TEMPLATE_NOT_APPROVED, template_id))
        ts = now or now_utc()
        day = str(ts)[:10]
        self._exec("BEGIN IMMEDIATE")
        try:
            dup = self._one(
                "SELECT send_id FROM pay_notify_log"
                " WHERE order_id=? AND reason=?", (order_id, reason))
            if dup:
                self._exec("COMMIT")
                return {"status": "already_logged", "send_id": dup,
                        "template_id": template_id, "reason": reason}
            sent_today = int(self._one(
                "SELECT COUNT(*) FROM pay_notify_log"
                " WHERE status='sent' AND substr(ts_utc,1,10)=?",
                (day,)) or 0)
            once, longterm, consumed = self._budget(avatar, template_id)
            if sent_today >= self.cap:
                status = ST_SKIP_CAP
            elif longterm > 0 or once - consumed > 0:
                status = ST_SENT
            else:
                status = ST_SKIP_BUDGET
            sid = _h("pnsend", avatar, order_id, reason, ts)
            self._exec(
                "INSERT INTO pay_notify_log"
                " (send_id, census_avatar_id, order_id, template_id,"
                "  reason, status, ts_utc) VALUES (?,?,?,?,?,?,?)",
                (sid, avatar, order_id, template_id, reason, status, ts))
            self._exec("COMMIT")
        except Exception:
            self._exec("ROLLBACK")
            raise
        return {"status": status, "send_id": sid,
                "template_id": template_id, "reason": reason}

    # ---------------- event faces (dual timepoints) ----------------

    def notify_payment_success(self, order_id, now=None):
        """Payment-success timepoint: fires for a granted order."""
        state = self._order_state(order_id)
        if state is None:
            raise ValueError("%s: %s" % (E_PN_UNKNOWN_ORDER, order_id))
        avatar, status, _ = state
        if status != "granted":
            raise ValueError("%s: payment_success needs granted, got %s"
                             % (E_PN_BAD_STATE, status))
        return self._face(self._attempt(avatar, str(order_id),
                                        "payment_success", now=now))

    def notify_refund(self, order_id, now=None):
        """Refund timepoint: fires only for a refund close (closed
        order WITH a grant row); timeout closes have no grant and no
        notice (zero rows, fail-closed)."""
        state = self._order_state(order_id)
        if state is None:
            raise ValueError("%s: %s" % (E_PN_UNKNOWN_ORDER, order_id))
        avatar, status, has_grant = state
        if status != "closed" or not has_grant:
            raise ValueError(
                "%s: refund needs closed-with-grant, got %s"
                % (E_PN_BAD_STATE, status))
        return self._face(self._attempt(avatar, str(order_id),
                                        "refund", now=now))

    # ---------------- read faces ----------------

    def budget_face(self, avatar, template_id):
        """Public read: W15 authorization budget for one avatar and
        template (popup-suppression view; R1719 authorize face dock).
        Reuses _budget - pure read, zero behavior drift elsewhere.
        Key set stays exactly {once, longterm, consumed} (live-only
        semantics internalized, R1740 ruling 3: zero key drift for
        existing consumers)."""
        once, longterm, consumed = self._budget(avatar, template_id)
        return {"once": once, "longterm": longterm, "consumed": consumed}

    def authorization_state(self, avatar, template_id):
        """Revocation-aware read face (R1740): live budget + revoked
        flag + cutoff provenance. revoked = a cutoff exists and zero
        live grants remain after it - an exhausted once set with no
        revoke is NOT revoked (honest state distinction, AC-VR5).
        Plain read face, budget_face family (no compliance wrapper)."""
        once, longterm, consumed = self._budget(avatar, template_id)
        cutoff = self._latest_revoke_ts(avatar, template_id)
        return {"avatar": avatar, "template_id": template_id,
                "once": once, "longterm": longterm, "consumed": consumed,
                "remaining_once": once - consumed,
                "revoked": cutoff is not None and (once + longterm) == 0,
                "revoke_ts": cutoff}

    def banner_queue(self):
        """Degraded in-app fallback queue = all skipped_* rows."""
        return self._exec(
            "SELECT send_id, census_avatar_id, order_id, reason, status,"
            " ts_utc FROM pay_notify_log WHERE status LIKE 'skipped_%'"
            " ORDER BY ts_utc").fetchall()

    def event_coverage(self, order_id):
        """Which event kinds have rows for one order (audit read)."""
        return {r[0] for r in self._exec(
            "SELECT DISTINCT reason FROM pay_notify_log"
            " WHERE order_id=?", (str(order_id),)).fetchall()}

    def log_rows(self):
        return self._exec(
            "SELECT send_id, census_avatar_id, order_id, reason, status,"
            " ts_utc FROM pay_notify_log ORDER BY ts_utc").fetchall()


def main():
    parser = argparse.ArgumentParser(
        description="payment-state notification sandbox (readiness check)")
    parser.add_argument("--config", default=os.path.join(BASE, "config.json"))
    parser.add_argument("--db", default=os.path.join(
        BASE, "data", "pay_notify.db"))
    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as handle:
        config = json.load(handle)
    face = PayNotifyFace(config, args.db)
    approved = sorted(t for t, r in face.templates.items() if r["approved"])
    face.close()
    print("READY approved_templates=%s daily_cap=%d"
          % (approved, face.cap))
    return 0


if __name__ == "__main__":
    sys.exit(main())
