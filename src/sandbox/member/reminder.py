"""Subscribe-message reminder face sandbox (BigDomain membership piece).

Implements pre-registered criterion AC-M17 (membership-spec section 1
table, registered 2026-10-06 BEFORE this code; pre-registration law:
criteria table first, implementation second - spec footer discipline).

Consumes two registered research signals into the membership design:
  W10 (consumer-protection regulation art. 10.2, global-benchmarks
       2026-10-01 entry): auto-renewal type services owe the consumer
       a prominent reminder at TWO timepoints - before the consumer
       accepts the service AND before the renewal date.
  W15 (WeChat subscribe-message official doc, global-benchmarks
       2026-10-06 entry): the reminder channel is user-authorization
       gated - template ids are platform-review approved; wx.
       requestSubscribeMessage grants are one-shot (each send consumes
       one budget unit) or long-term; subscribeMessage.send caps are
       1M/day (no payment capability) or 3M/day (payment enabled).

Honest scope notes (never silently self-served):
  - MVP renewal is MANUAL (spec section 0): the binding face here is
    the single pre-expiry reminder (end - remind_days, window
    end-remind_days <= now < end). The accept-time (first_service)
    timepoint binds only when an auto-renewal state exists; that
    capability stays [pending-verify] at wiring day (AC-MP1 same
    annotation) and is NOT pre-built - the auto_renewal flag below is
    a simulation parameter for criterion verification only.
  - This sandbox simulates the channel locally: zero real API
    touchpoints, zero keys; real wiring belongs to the bootstrap
    window (three-question gate on file).
  - Zero-silent-loss law: a due reminder that cannot go out (budget
    exhausted / daily cap hit) MUST land a skipped_* row - those rows
    ARE the degraded in-app banner queue face. Never silently
    dropped, never faked as sent.
  - Daily caps: official wording is kept in config (1M / 3M); tests
    inject small values to verify enforcement (scaled simulation).

Single-writer discipline:
  - member.db's single writer is member.MemberStore (sweep precedent
    drives it through the store); this module owns its OWN sqlite
    file (member_reminder.db) and is that file's single writer
    (BEGIN IMMEDIATE, house WAL discipline per file).
  - Due-scan reads member_periods through a READ-ONLY connection
    (reads never break the writer discipline; cross-file dock
    precedent documented in member.py header).

Schema (spec section 2.1): member_subscribe_grants (authorization
budget journal, append-only), member_reminder_log (send/skip journal,
append-only; idempotency key = avatar+reason+period_key+day). Column
vocabulary is fiat-free and token-free (AC-M10/M11 same law; this
separate file is covered by test assertions, reconcile check 4 does
not reach across files - documented in spec section 2.1 note).

Known v0.2 sandbox deltas (documented, honest):
  - long-term grants have no revocation face yet: the official change
    event currently only pushes unsubscribe events (W15 note); the
    revocation face lands with real wiring.
  - grant_authorization does not template-gate: granting an
    authorization for a template the user can see is a client flow;
    only sends enforce the approved-registry gate.

Encoding discipline: this script stays ASCII; Chinese copy lives in
config.json.

Run (readiness self-check):
    python reminder.py
    python reminder.py --config config.json --db data/member_reminder.db
"""

import argparse
import json
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
for _p in (BASE,):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

from member import _h, now_utc, parse_iso, add_days  # noqa: E402

# error codes (ASCII)
E_TEMPLATE_NOT_APPROVED = "E_TEMPLATE_NOT_APPROVED"
E_UNKNOWN_TEMPLATE = "E_UNKNOWN_TEMPLATE"
E_BAD_GRANT_TYPE = "E_BAD_GRANT_TYPE"
E_BANNED_TEMPLATE_COPY = "E_BANNED_TEMPLATE_COPY"

# log statuses (rows; the two skipped faces double as banner queue)
ST_SENT = "sent"
ST_SKIP_BUDGET = "skipped_no_budget"
ST_SKIP_CAP = "skipped_daily_cap"

SCHEMA = """
CREATE TABLE IF NOT EXISTS member_subscribe_grants (
  grant_id         TEXT PRIMARY KEY,
  census_avatar_id TEXT NOT NULL,
  template_id      TEXT NOT NULL,
  grant_type       TEXT NOT NULL CHECK (grant_type IN ('once','longterm')),
  ts_utc           TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS member_reminder_log (
  send_id          TEXT PRIMARY KEY,
  census_avatar_id TEXT NOT NULL,
  template_id      TEXT NOT NULL,
  reason           TEXT NOT NULL CHECK (reason IN ('first_service','renewal_due')),
  status           TEXT NOT NULL CHECK (status IN
                   ('sent','skipped_no_budget','skipped_daily_cap')),
  period_key       TEXT,
  ts_utc           TEXT NOT NULL
);
"""


class ConfigRejected(ValueError):
    """Raised when the reminder config violates fail-closed rules."""


class TemplateNotApproved(ValueError):
    """Raised when a send names an unapproved template (zero rows)."""


class ReminderFace(object):
    """Single writer of member_reminder.db (W10/W15 reminder face)."""

    def __init__(self, config, db_path, member_db=None):
        cfg = (config or {}).get("reminder", {})
        self.days = int(cfg.get("remind_days_before", 3))
        if self.days <= 0:
            raise ConfigRejected("remind_days_before must be positive")
        self.cap = int(cfg.get("daily_send_cap_default", 1000000))
        if self.cap <= 0:
            raise ConfigRejected("daily_send_cap must be positive")
        templates = cfg.get("templates", {}) or {}
        if not templates:
            raise ConfigRejected("template registry must not be empty")
        banned = set(config.get("copy_ban_words", []) or [])
        banned |= set((config.get("gate", {}) or {}).get(
            "forbidden_words", []) or [])
        self.templates = {}
        for tid, row in templates.items():
            copy = str(row.get("copy", ""))
            if not copy:
                raise ConfigRejected("template %r: empty copy" % tid)
            hit = next((w for w in banned if w and w in copy), None)
            if hit:
                raise ConfigRejected(
                    "%s: template %r copy contains banned word %r"
                    % (E_BANNED_TEMPLATE_COPY, tid, hit))
            self.templates[tid] = {"approved": bool(row.get("approved")),
                                   "copy": copy}
        self.reason_templates = dict(cfg.get("reason_templates", {}) or {})
        approved = [t for t, r in self.templates.items() if r["approved"]]
        if not approved:
            raise ConfigRejected("no approved template in registry")
        for reason in ("renewal_due", "first_service"):
            self.reason_templates.setdefault(reason, approved[0])
        self.member_db = member_db
        self.db_path = db_path
        fresh = not os.path.exists(db_path)
        self.conn = sqlite3.connect(db_path)
        self.conn.isolation_level = None
        # executescript would auto-commit the open transaction, so the
        # DDL rides one explicit BEGIN IMMEDIATE as separate statements
        self._exec("BEGIN IMMEDIATE")
        for stmt in SCHEMA.split(";"):
            if stmt.strip():
                self.conn.execute(stmt)
        self._exec("COMMIT")
        self.fresh = fresh

    # ---------------- low-level helpers ----------------

    def _exec(self, sql, args=()):
        return self.conn.execute(sql, args)

    def _one(self, sql, args=()):
        row = self._exec(sql, args).fetchone()
        return row[0] if row else None

    def close(self):
        self.conn.close()

    # ---------------- authorization budget ----------------

    def grant_authorization(self, avatar, template_id, grant_type,
                            now=None):
        if template_id not in self.templates:
            raise ValueError("%s: %s" % (E_UNKNOWN_TEMPLATE, template_id))
        if grant_type not in ("once", "longterm"):
            raise ValueError("%s: %s" % (E_BAD_GRANT_TYPE, grant_type))
        ts = now or now_utc()
        gid = _h("subgrant", avatar, template_id, grant_type, ts)
        self._exec("BEGIN IMMEDIATE")
        self._exec(
            "INSERT INTO member_subscribe_grants"
            " (grant_id, census_avatar_id, template_id, grant_type, ts_utc)"
            " VALUES (?,?,?,?,?)", (gid, avatar, template_id, grant_type, ts))
        self._exec("COMMIT")
        return gid

    def _budget_rows(self, avatar, template_id):
        once = self._one(
            "SELECT COUNT(*) FROM member_subscribe_grants"
            " WHERE census_avatar_id=? AND template_id=? AND grant_type='once'",
            (avatar, template_id))
        longterm = self._one(
            "SELECT COUNT(*) FROM member_subscribe_grants"
            " WHERE census_avatar_id=? AND template_id=?"
            " AND grant_type='longterm'", (avatar, template_id))
        consumed = self._one(
            "SELECT COUNT(*) FROM member_reminder_log"
            " WHERE census_avatar_id=? AND template_id=? AND status='sent'",
            (avatar, template_id))
        return int(once or 0), int(longterm or 0), int(consumed or 0)

    # ---------------- send attempt (enforcement order) ----------------

    def attempt(self, avatar, template_id, reason, now=None, period_key=None):
        row_tpl = self.templates.get(template_id)
        if row_tpl is None:
            raise ValueError("%s: %s" % (E_UNKNOWN_TEMPLATE, template_id))
        if not row_tpl["approved"]:
            # zero rows, zero sends: an unapproved template must never
            # touch the log (AC-M17 template-review gate)
            raise TemplateNotApproved(
                "%s: %s" % (E_TEMPLATE_NOT_APPROVED, template_id))
        ts = now or now_utc()
        day = str(ts)[:10]
        self._exec("BEGIN IMMEDIATE")
        try:
            dup = self._one(
                "SELECT send_id FROM member_reminder_log"
                " WHERE census_avatar_id=? AND reason=?"
                " AND COALESCE(period_key,'')=COALESCE(?,'')"
                " AND substr(ts_utc,1,10)=?",
                (avatar, reason, period_key, day))
            if dup:
                self._exec("COMMIT")
                return {"status": "already_logged", "send_id": dup,
                        "template_id": template_id, "reason": reason}
            sent_today = int(self._one(
                "SELECT COUNT(*) FROM member_reminder_log"
                " WHERE status='sent' AND substr(ts_utc,1,10)=?",
                (day,)) or 0)
            once, longterm, consumed = self._budget_rows(avatar, template_id)
            if sent_today >= self.cap:
                status = ST_SKIP_CAP
            elif longterm > 0 or once - consumed > 0:
                status = ST_SENT
            else:
                status = ST_SKIP_BUDGET
            sid = _h("remsend", avatar, template_id, reason, period_key, ts)
            self._exec(
                "INSERT INTO member_reminder_log"
                " (send_id, census_avatar_id, template_id, reason, status,"
                "  period_key, ts_utc) VALUES (?,?,?,?,?,?,?)",
                (sid, avatar, template_id, reason, status, period_key, ts))
            self._exec("COMMIT")
        except Exception:
            self._exec("ROLLBACK")
            raise
        return {"status": status, "send_id": sid, "template_id": template_id,
                "reason": reason}

    # ---------------- W10 timepoints ----------------

    def on_accept(self, avatar, template_id=None, now=None,
                  auto_renewal=False):
        """Timepoint 1 (before the consumer accepts the service).

        Binds ONLY in the auto-renewal state (W10 art. 10.2); the MVP
        manual-renewal face has no such obligation and honestly returns
        not_required_mvp with ZERO rows (no fake activity).
        """
        if not auto_renewal:
            return {"status": "not_required_mvp"}
        template_id = template_id or self.reason_templates["first_service"]
        return self.attempt(avatar, template_id, "first_service", now=now)

    def scan(self, now=None, auto_renewal=False):
        """Timepoint 2 (before the renewal date) due-scan.

        Reads active periods from member.db through a read-only
        connection; due window = end-remind_days <= now < end. Every
        due period yields exactly one attempt (idempotent per day).
        auto_renewal is a simulation flag only (real capability stays
        [pending-verify]; scan itself always runs the renewal-due
        timepoint, which is the MVP binding face).
        """
        if not self.member_db:
            raise ValueError("member_db path required for scan")
        ts = now or now_utc()
        ro = sqlite3.connect("file:%s?mode=ro" % self.member_db, uri=True)
        try:
            rows = ro.execute(
                "SELECT period_id, census_avatar_id, end_utc"
                " FROM member_periods WHERE status='active'").fetchall()
        finally:
            ro.close()
        due = []
        for period_id, avatar, end_utc in rows:
            window_start = add_days(end_utc, -self.days)
            if (parse_iso(window_start) <= parse_iso(ts)
                    < parse_iso(end_utc)):
                due.append((period_id, avatar))
        results = []
        for period_id, avatar in due:
            template_id = self.reason_templates["renewal_due"]
            results.append(self.attempt(
                avatar, template_id, "renewal_due", now=ts,
                period_key=period_id))
        return results

    # ---------------- read faces ----------------

    def banner_queue(self):
        """Degraded in-app fallback queue = all skipped_* rows."""
        return self._exec(
            "SELECT send_id, census_avatar_id, reason, status, ts_utc"
            " FROM member_reminder_log WHERE status LIKE 'skipped_%'"
            " ORDER BY ts_utc").fetchall()

    def dual_timepoint_coverage(self, avatar):
        """W10 dual-timepoint coverage face (which reasons have rows)."""
        return {r[0] for r in self._exec(
            "SELECT DISTINCT reason FROM member_reminder_log"
            " WHERE census_avatar_id=?", (avatar,)).fetchall()}

    def daily_sent_count(self, now=None):
        day = str(now or now_utc())[:10]
        return int(self._one(
            "SELECT COUNT(*) FROM member_reminder_log"
            " WHERE status='sent' AND substr(ts_utc,1,10)=?", (day,)) or 0)


def main():
    parser = argparse.ArgumentParser(
        description="membership subscribe-message reminder sandbox")
    parser.add_argument("--config", default=os.path.join(BASE, "config.json"))
    parser.add_argument("--db", default=os.path.join(
        BASE, "data", "member_reminder.db"))
    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as handle:
        config = json.load(handle)
    os.makedirs(os.path.dirname(os.path.abspath(args.db)), exist_ok=True)
    face = ReminderFace(config, args.db)
    approved = sorted(t for t, r in face.templates.items() if r["approved"])
    face.close()
    print("READY templates=%s remind_days=%d daily_cap=%d"
          % (approved, face.days, face.cap))


if __name__ == "__main__":
    main()
