"""Citizen civic-behavior points face (BigDomain R1752; canon =
explore-queue civic-points line: civic behavior points inside the
counts-vs-tokens isolation law, public-welfare compliance judged
first, points-redeem-entitlements built on the props-domain
adjacency verdict).

Public-welfare compliance verdict (registered before the code):

  - points are earned-only: there is no fiat or token entrance -
    the only source is a platform-registered civic behavior
    performed by a resident (this is the public-welfare dividing
    line against the props token-spend purchase path);
  - no back-flow and no transfer: no verb converts points back
    into tokens or fiat, and no verb moves points between
    accounts (the collectibles no-circulation law is inherited);
  - props-domain check-first verdict: the props.py grant path is
    token-spend-bound (its purchase verb books one ledger spend),
    which is structurally unusable for a points redemption - so
    this module builds its own civic_grants grant table (structure
    referenced, token path never copied).

Domains:

  - behavior registry: a platform-registered civic behavior with
    a fixed point value and a per-account daily earn limit
    (anti-farming cap, window = the calendar day of the event);
  - earn ledger: append-only earn rows, idempotent on
    (account, behavior, event_ref), the registered point value
    copied immutably onto each row;
  - reward registry: platform-registered redeemable entitlements,
    kind 'cosmetic' (one grant per account) or 'count' (stackable
    credit grants);
  - redemption: fail-closed gate order (unknown reward, derived
    balance, cosmetic-already-granted), then exactly one redeem
    row plus one grant row; balance is derived at read time as
    earned minus redeemed (zero UPDATE surface).

Hard laws:

  - counts-vs-tokens isolation (R599 law, elevated form): the
    constructor takes NO ledger reference at all - the module is
    structurally unable to touch the token domain; the suite
    proves ledger_tx count constant across every operation;
  - append-only: earn/redeem/grant rows are INSERT-only; the
    module source carries zero UPDATE statements;
  - zero RNG, zero network, shipped config.json untouched.

Platform posture: behavior/reward registration and earn attestation
are platform-side facts with no resident free text (the
festival/ads/showcase-register posture); no SecGate point exists
here; a successor resident-text surface must wire a SecGate
pre-gate first.

AIGC labeling: registry rows carry a persistent ai_label (0/1,
DB CHECK) shown on every listing surface; a resident standing
disclaimer is required at construction and rides every envelope
(non-advisory law).

Storage: one separate SQLite file (civic.db, WAL, single writer)
- zero ledger-schema touch, so the schema fingerprint sentinel
stays clean. Stdlib only; pure ASCII.

Pre-registered criteria AC-CV1..CV7 live in the R1752
explore-queue row and were written before this code existed
(honesty law).
"""

import datetime
import sqlite3
import threading

E_CV_BAD_ARGS = "E_CV_BAD_ARGS"
E_CV_DUP_BEHAVIOR = "E_CV_DUP_BEHAVIOR"
E_CV_UNKNOWN_BEHAVIOR = "E_CV_UNKNOWN_BEHAVIOR"
E_CV_DUP_EARN = "E_CV_DUP_EARN"
E_CV_DAY_LIMIT = "E_CV_DAY_LIMIT"
E_CV_DUP_REWARD = "E_CV_DUP_REWARD"
E_CV_UNKNOWN_REWARD = "E_CV_UNKNOWN_REWARD"
E_CV_DUP_GRANT = "E_CV_DUP_GRANT"
E_CV_INSUFFICIENT = "E_CV_INSUFFICIENT"
E_CV_NO_DISCLAIMER = "E_CV_NO_DISCLAIMER"

REWARD_KINDS = ("cosmetic", "count")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS civic_behaviors (
    behavior_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    points_per_event INTEGER NOT NULL CHECK (points_per_event >= 1),
    daily_limit INTEGER NOT NULL CHECK (daily_limit >= 1),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0,1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS civic_earns (
    earn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    behavior_id TEXT NOT NULL,
    at_day TEXT NOT NULL,
    event_ref TEXT NOT NULL,
    points INTEGER NOT NULL CHECK (points >= 1),
    earned_utc TEXT NOT NULL,
    UNIQUE (account_id, behavior_id, event_ref)
);
CREATE TABLE IF NOT EXISTS civic_rewards (
    reward_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    cost_points INTEGER NOT NULL CHECK (cost_points >= 1),
    kind TEXT NOT NULL CHECK (kind IN ('cosmetic','count')),
    grant_count INTEGER NOT NULL CHECK (grant_count >= 1),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0,1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS civic_redeems (
    redeem_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    reward_id TEXT NOT NULL,
    cost_points INTEGER NOT NULL CHECK (cost_points >= 1),
    redeemed_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS civic_grants (
    grant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    reward_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('cosmetic','count')),
    count_credits INTEGER NOT NULL CHECK (count_credits >= 1),
    granted_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class CivicError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class CivicPointsFace:
    """Citizen civic points face. Own SQLite file, single writer.
    Constructor deliberately takes NO ledger reference: the token
    domain is structurally out of reach (counts-vs-tokens
    isolation law, R599 elevated)."""

    def __init__(self, disclaimer, db_path):
        if not str(disclaimer or "").strip():
            raise CivicError(E_CV_NO_DISCLAIMER,
                             "resident disclaimer required")
        self.disclaimer = str(disclaimer)
        if not str(db_path or "").strip():
            raise CivicError(E_CV_BAD_ARGS, "db path required")
        self.db_path = str(db_path)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- internal helpers ----------------------------------------------------

    def _assert_account(self, account_id):
        if not isinstance(account_id, str) or not account_id.startswith(
                "usr:"):
            raise CivicError(E_CV_BAD_ARGS, "accounts are usr:* only")
        return account_id

    def _assert_day(self, at_day):
        """Strict calendar-day validation: strptime alone is lenient
        about zero padding ('2026-10-1' parses), so the parse is
        round-tripped and must reproduce the input verbatim."""
        if not isinstance(at_day, str):
            raise CivicError(E_CV_BAD_ARGS, "at_day must be a string")
        try:
            parsed = datetime.datetime.strptime(at_day, "%Y-%m-%d")
        except ValueError:
            raise CivicError(E_CV_BAD_ARGS, "bad at_day: " + at_day)
        if parsed.strftime("%Y-%m-%d") != at_day:
            raise CivicError(E_CV_BAD_ARGS, "bad at_day: " + at_day)
        return at_day

    def _load_behavior(self, behavior_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT title, points_per_event, daily_limit, ai_label,"
                " registered_utc FROM civic_behaviors"
                " WHERE behavior_id = ?", (behavior_id,)).fetchone()
        if row is None:
            raise CivicError(E_CV_UNKNOWN_BEHAVIOR, behavior_id)
        return row

    def _derived_balance(self, account_id):
        earned = self._conn.execute(
            "SELECT COALESCE(SUM(points), 0) FROM civic_earns"
            " WHERE account_id = ?", (account_id,)).fetchone()[0]
        redeemed = self._conn.execute(
            "SELECT COALESCE(SUM(cost_points), 0) FROM civic_redeems"
            " WHERE account_id = ?", (account_id,)).fetchone()[0]
        return int(earned), int(redeemed)

    # -- writer faces ----------------------------------------------------------

    def register_behavior(self, behavior_id, title, points_per_event,
                           daily_limit, ai_generated):
        behavior_id = str(behavior_id or "").strip()
        title = str(title or "").strip()
        if not behavior_id:
            raise CivicError(E_CV_BAD_ARGS, "behavior id required")
        if not title:
            raise CivicError(E_CV_BAD_ARGS, "title required")
        if (not isinstance(points_per_event, int)
                or isinstance(points_per_event, bool)
                or points_per_event < 1):
            raise CivicError(E_CV_BAD_ARGS,
                             "points per event must be int >= 1")
        if (not isinstance(daily_limit, int) or isinstance(daily_limit, bool)
                or daily_limit < 1):
            raise CivicError(E_CV_BAD_ARGS,
                             "daily limit must be int >= 1")
        if not isinstance(ai_generated, bool):
            raise CivicError(E_CV_BAD_ARGS, "ai flag must be bool")
        now = _now_utc()
        with self._lock:
            row = self._conn.execute(
                "SELECT behavior_id FROM civic_behaviors"
                " WHERE behavior_id = ?", (behavior_id,)).fetchone()
            if row is not None:
                raise CivicError(E_CV_DUP_BEHAVIOR, behavior_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO civic_behaviors (behavior_id, title,"
                    " points_per_event, daily_limit, ai_label,"
                    " registered_utc) VALUES (?,?,?,?,?,?)",
                    (behavior_id, title, points_per_event, daily_limit,
                     1 if ai_generated else 0, now))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise CivicError(E_CV_DUP_BEHAVIOR, behavior_id)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"behavior_id": behavior_id, "title": title,
                "points_per_event": points_per_event,
                "daily_limit": daily_limit,
                "ai_label": 1 if ai_generated else 0,
                "disclaimer": self.disclaimer}

    def earn_civic(self, account_id, behavior_id, at_day, event_ref):
        """One append-only earn row per (account, behavior, event_ref);
        the daily cap gates before any row lands; the registered
        point value is copied immutably onto the row."""
        account_id = self._assert_account(account_id)
        behavior_id = str(behavior_id or "").strip()
        if not behavior_id:
            raise CivicError(E_CV_BAD_ARGS, "behavior id required")
        at_day = self._assert_day(at_day)
        event_ref = str(event_ref or "").strip()
        if not event_ref:
            raise CivicError(E_CV_BAD_ARGS, "event ref required")
        reg = self._load_behavior(behavior_id)
        points_per_event, daily_limit, ai_label = (
            int(reg[1]), int(reg[2]), int(reg[3]))
        now = _now_utc()
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                dup = self._conn.execute(
                    "SELECT earn_id FROM civic_earns WHERE"
                    " account_id = ? AND behavior_id = ? AND"
                    " event_ref = ?",
                    (account_id, behavior_id, event_ref)).fetchone()
                if dup is not None:
                    raise CivicError(E_CV_DUP_EARN, event_ref)
                day_count = self._conn.execute(
                    "SELECT COUNT(*) FROM civic_earns WHERE"
                    " account_id = ? AND behavior_id = ? AND at_day = ?",
                    (account_id, behavior_id, at_day)).fetchone()[0]
                if int(day_count) >= daily_limit:
                    raise CivicError(
                        E_CV_DAY_LIMIT,
                        "%d of %d on %s" % (int(day_count), daily_limit,
                                            at_day))
                self._conn.execute(
                    "INSERT INTO civic_earns (account_id, behavior_id,"
                    " at_day, event_ref, points, earned_utc)"
                    " VALUES (?,?,?,?,?,?)",
                    (account_id, behavior_id, at_day, event_ref,
                     points_per_event, now))
                earned, redeemed = self._derived_balance(account_id)
                self._conn.execute("COMMIT")
            except CivicError:
                self._conn.execute("ROLLBACK")
                raise
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"behavior_id": behavior_id, "event_ref": event_ref,
                "points_earned": points_per_event,
                "balance": earned - redeemed,
                "ai_label": ai_label,
                "disclaimer": self.disclaimer}

    def register_reward(self, reward_id, title, cost_points, kind,
                        grant_count, ai_generated):
        reward_id = str(reward_id or "").strip()
        title = str(title or "").strip()
        if not reward_id:
            raise CivicError(E_CV_BAD_ARGS, "reward id required")
        if not title:
            raise CivicError(E_CV_BAD_ARGS, "title required")
        if (not isinstance(cost_points, int) or isinstance(cost_points, bool)
                or cost_points < 1):
            raise CivicError(E_CV_BAD_ARGS, "cost must be int >= 1")
        if kind not in REWARD_KINDS:
            raise CivicError(E_CV_BAD_ARGS, "kind must be cosmetic/count")
        if not isinstance(grant_count, int) or isinstance(grant_count, bool):
            raise CivicError(E_CV_BAD_ARGS, "grant count must be int")
        if kind == "cosmetic" and grant_count != 1:
            raise CivicError(E_CV_BAD_ARGS,
                             "cosmetic grants are exactly one")
        if kind == "count" and grant_count < 1:
            raise CivicError(E_CV_BAD_ARGS, "count grants need >= 1")
        if not isinstance(ai_generated, bool):
            raise CivicError(E_CV_BAD_ARGS, "ai flag must be bool")
        now = _now_utc()
        with self._lock:
            row = self._conn.execute(
                "SELECT reward_id FROM civic_rewards"
                " WHERE reward_id = ?", (reward_id,)).fetchone()
            if row is not None:
                raise CivicError(E_CV_DUP_REWARD, reward_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO civic_rewards (reward_id, title,"
                    " cost_points, kind, grant_count, ai_label,"
                    " registered_utc) VALUES (?,?,?,?,?,?,?)",
                    (reward_id, title, cost_points, kind, grant_count,
                     1 if ai_generated else 0, now))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise CivicError(E_CV_DUP_REWARD, reward_id)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"reward_id": reward_id, "title": title,
                "cost_points": cost_points, "kind": kind,
                "grant_count": grant_count,
                "ai_label": 1 if ai_generated else 0,
                "disclaimer": self.disclaimer}

    def redeem_reward(self, account_id, reward_id):
        """Fail-closed gate order: unknown reward, derived balance,
        cosmetic-already-granted - then exactly one redeem row plus
        one grant row inside one transaction."""
        account_id = self._assert_account(account_id)
        reward_id = str(reward_id or "").strip()
        if not reward_id:
            raise CivicError(E_CV_BAD_ARGS, "reward id required")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                reg = self._conn.execute(
                    "SELECT title, cost_points, kind, grant_count,"
                    " ai_label FROM civic_rewards WHERE reward_id = ?",
                    (reward_id,)).fetchone()
                if reg is None:
                    raise CivicError(E_CV_UNKNOWN_REWARD, reward_id)
                title, cost, kind, grant_count, ai_label = (
                    reg[0], int(reg[1]), reg[2], int(reg[3]), int(reg[4]))
                earned, redeemed = self._derived_balance(account_id)
                if earned - redeemed < cost:
                    raise CivicError(
                        E_CV_INSUFFICIENT,
                        "balance %d < cost %d" % (earned - redeemed, cost))
                if kind == "cosmetic":
                    held = self._conn.execute(
                        "SELECT grant_id FROM civic_grants WHERE"
                        " account_id = ? AND reward_id = ?",
                        (account_id, reward_id)).fetchone()
                    if held is not None:
                        raise CivicError(E_CV_DUP_GRANT, reward_id)
                now = _now_utc()
                self._conn.execute(
                    "INSERT INTO civic_redeems (account_id, reward_id,"
                    " cost_points, redeemed_utc) VALUES (?,?,?,?)",
                    (account_id, reward_id, cost, now))
                self._conn.execute(
                    "INSERT INTO civic_grants (account_id, reward_id,"
                    " kind, count_credits, granted_utc)"
                    " VALUES (?,?,?,?,?)",
                    (account_id, reward_id, kind,
                     1 if kind == "cosmetic" else grant_count, now))
                earned2, redeemed2 = self._derived_balance(account_id)
                self._conn.execute("COMMIT")
            except CivicError:
                self._conn.execute("ROLLBACK")
                raise
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"reward_id": reward_id, "title": title,
                "cost_points": cost, "kind": kind,
                "granted": 1 if kind == "cosmetic" else grant_count,
                "balance": earned2 - redeemed2,
                "ai_label": ai_label,
                "disclaimer": self.disclaimer}

    # -- read faces ------------------------------------------------------------

    def points_view(self, account_id):
        account_id = self._assert_account(account_id)
        with self._lock:
            earned, redeemed = self._derived_balance(account_id)
            grants = self._conn.execute(
                "SELECT reward_id, kind, count_credits, granted_utc"
                " FROM civic_grants WHERE account_id = ?"
                " ORDER BY grant_id", (account_id,)).fetchall()
            events = self._conn.execute(
                "SELECT behavior_id, at_day, event_ref, points FROM"
                " civic_earns WHERE account_id = ? ORDER BY earn_id",
                (account_id,)).fetchall()
        return {"account_id": account_id, "earned_total": earned,
                "redeemed_total": redeemed, "balance": earned - redeemed,
                "earn_events": [{"behavior_id": r[0], "at_day": r[1],
                                 "event_ref": r[2], "points": int(r[3])}
                                for r in events],
                "grants": [{"reward_id": r[0], "kind": r[1],
                            "count_credits": int(r[2]),
                            "granted_utc": r[3]} for r in grants],
                "disclaimer": self.disclaimer}

    def behavior_board(self):
        with self._lock:
            rows = self._conn.execute(
                "SELECT behavior_id, title, points_per_event,"
                " daily_limit, ai_label, registered_utc FROM"
                " civic_behaviors ORDER BY rowid").fetchall()
        board = [{"behavior_id": r[0], "title": r[1],
                  "points_per_event": int(r[2]), "daily_limit": int(r[3]),
                  "ai_label": int(r[4]), "registered_utc": r[5]}
                 for r in rows]
        return {"behaviors": board, "disclaimer": self.disclaimer}

    def reward_board(self):
        with self._lock:
            rows = self._conn.execute(
                "SELECT reward_id, title, cost_points, kind,"
                " grant_count, ai_label, registered_utc FROM"
                " civic_rewards ORDER BY rowid").fetchall()
        board = [{"reward_id": r[0], "title": r[1],
                  "cost_points": int(r[2]), "kind": r[3],
                  "grant_count": int(r[4]), "ai_label": int(r[5]),
                  "registered_utc": r[6]} for r in rows]
        return {"rewards": board, "disclaimer": self.disclaimer}
