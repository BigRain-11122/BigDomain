"""Developer free-trial tier face over the developer-key registry
(BigDomain R1768; canon = the explore-queue "developer free-trial
quota" line: the zero-fee trial window + the upgrade-conversion
gate; seeds = the apidev.py R1700 quota ring, read as a variant,
and the member tier-grant structure for the conversion record).

Design verdicts (registered before the code, in the R1768
explore-queue row):

  - carrier: FreeTrialFace rides its own independent SQLite file
    (free_trial.db next to the devkeys DB, single writer, the
    apimarket R1763 pattern; zero ledger schema touch so the
    schema fingerprint sentinel stays clean). The constructor
    takes NO ledger at all - the free tier is structurally
    free: with no ledger injected there is no code path that
    could move a token (zero-fee self-evidence at the
    structure level).
  - registry gate: only an in-register developer may hold a
    trial - the DevKeyFace.dev_board public read face must show
    at least one key row (referenced, never copied; zero
    api_dev_keys direct reads, the apimarket AC-AM2 law); an
    off-register developer is refused E_FT_NOT_DEV before any
    row exists.
  - quota ring variant: free calls are counted as immutable rows
    (COUNT face, never a mutated counter - the apidev ring-2
    law), and the trial window is a LIFETIME window that never
    resets - the explicit variant judgement against the apidev
    monthly ring: a trial is a one-shot cap, not a recurring
    free tier.
  - upgrade-conversion gate, two states: at cap exhaustion the
    call refuses E_FT_QUOTA with an upgrade hint in the error
    detail (the conversion gate fires), and a converted
    developer loses the free tier for good (E_FT_CONVERTED,
    fail-closed). The conversion row follows the member
    tier-grant structure reference: one enrollment per
    (developer, plan) - conversion is the trial's terminal
    state; the real paid path is the existing apidev/metered
    buy_credits face (referenced, not rebuilt).
  - caller-supplied parameters: the trial cap is a per-plan
    registry value; production caps and the target-tier pricing
    are a [needs-CEO] batch - the shipped config.json is
    untouched.

Domains:

  - plan registry: platform-registered free-trial plans with a
    per-developer call cap; the declared AIGC label persists on
    the row and every view surface shows it.
  - trial grant + free calls: one grant per (developer, plan);
    free calls append immutable rows inside the lifetime trial
    window - every gate (registry, grant, conversion, replay,
    quota) rejects BEFORE any row, so a rejected call leaves
    zero rows and, by structure, zero token movement.
  - upgrade conversion: one terminal conversion row per
    (developer, plan) with the target tier key and its
    provenance timestamp; after it the free calls on that plan
    close fail-closed.

Hard laws:

  - append-only: plan/grant/call/conversion rows are INSERT
    only; the module source carries zero mutation statements
    for its own tables (quota enforcement reads COUNT faces, it
    never mutates counters);
  - zero dice, zero network imports, pure ASCII source; the face
    holds no ledger reference at all - counts stay counts and
    the token domain is structurally unreachable.

AIGC labeling: registry rows carry a persistent ai_label (0/1,
DB CHECK) shown on every listing surface; a resident standing
disclaimer is required at construction and rides every envelope
(non-advisory law).

Pre-registered criteria AC-FT1..AC-FT7 live in the R1768
explore-queue row and were written before this code existed
(honesty law).
"""

import datetime
import os
import re
import sqlite3
import threading

E_FT_BAD_ARGS = "E_FT_BAD_ARGS"               # AC-FT1..AC-FT7
E_FT_BAD_ACCOUNT = "E_FT_BAD_ACCOUNT"         # AC-FT2..AC-FT4
E_FT_BAD_PLAN = "E_FT_BAD_PLAN"               # AC-FT1
E_FT_DUP_PLAN = "E_FT_DUP_PLAN"               # AC-FT1
E_FT_UNKNOWN_PLAN = "E_FT_UNKNOWN_PLAN"       # AC-FT1/AC-FT6
E_FT_NOT_DEV = "E_FT_NOT_DEV"                 # AC-FT2..AC-FT4
E_FT_DUP_GRANT = "E_FT_DUP_GRANT"             # AC-FT2
E_FT_NO_TRIAL = "E_FT_NO_TRIAL"               # AC-FT3/AC-FT4
E_FT_DUP = "E_FT_DUP"                         # AC-FT3
E_FT_QUOTA = "E_FT_QUOTA"                     # AC-FT3
E_FT_CONVERTED = "E_FT_CONVERTED"             # AC-FT3/AC-FT4
E_FT_DUP_CONVERT = "E_FT_DUP_CONVERT"         # AC-FT4
E_FT_NO_DISCLAIMER = "E_FT_NO_DISCLAIMER"     # AC-FT5

_WINDOW_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])\Z")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trial_plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    trial_cap INTEGER NOT NULL CHECK (trial_cap >= 1),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS trial_grants (
    grant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    granted_utc TEXT NOT NULL,
    UNIQUE (dev_account, plan_id)
);
CREATE TABLE IF NOT EXISTS trial_calls (
    call_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    kind TEXT NOT NULL,
    call_ref TEXT NOT NULL,
    engine_ref TEXT NOT NULL,
    called_utc TEXT NOT NULL,
    UNIQUE (dev_account, plan_id, call_ref)
);
CREATE TABLE IF NOT EXISTS trial_conversions (
    conversion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    dev_account TEXT NOT NULL,
    tier_key TEXT NOT NULL,
    converted_utc TEXT NOT NULL,
    UNIQUE (dev_account, plan_id)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


class TrialError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class FreeTrialFace:
    """Developer free-trial tier face. Own independent SQLite
    file (single writer); every mutation runs inside BEGIN
    IMMEDIATE. Plan/grant/call/conversion rows are immutable
    once written (zero mutation surface for the own tables).
    The developer-key face is injected (dependency injection:
    the DevKeyFace product is referenced, never copied); a
    missing face or an empty disclaimer refuses construction -
    no registry, no door; no disclaimer, no door. No ledger is
    injected at all: the free tier is structurally free."""

    def __init__(self, devkeys, disclaimer):
        if devkeys is None or not hasattr(devkeys, "dev_board"):
            raise TrialError(E_FT_BAD_ARGS,
                             "devkeys face must expose dev_board")
        self.devkeys = devkeys
        text = str(disclaimer or "").strip()
        if not text:
            raise TrialError(E_FT_NO_DISCLAIMER,
                             "resident disclaimer required")
        self.disclaimer = text
        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(devkeys.db_path)),
            "free_trial.db")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- registry gate (fail-closed, before any row) -----------------------

    def _in_register(self, dev_account):
        """A developer is in-register when the DevKeyFace.dev_board
        public read face shows at least one key row (referenced,
        never copied; zero api_dev_keys direct reads - the apimarket
        AC-AM2 law)."""
        board = self.devkeys.dev_board(dev_account)
        return len(board.get("keys", [])) > 0

    def _require_account(self, dev_account):
        if not str(dev_account or "").startswith("usr:"):
            raise TrialError(E_FT_BAD_ACCOUNT, dev_account)
        return str(dev_account)

    # -- plan registry domain ----------------------------------------------

    def register_trial_plan(self, plan_key, title, trial_cap,
                            ai_generated):
        """Register one free-trial plan: a per-developer call cap.
        Exactly one row per plan_key - a repeat is rejected with
        zero rows (AC-FT1). The declared AIGC label persists on
        the row and every view surfaces it (AC-FT5)."""
        key = str(plan_key or "").strip()
        if not key:
            raise TrialError(E_FT_BAD_PLAN, "plan key required")
        if not str(title or "").strip():
            raise TrialError(E_FT_BAD_PLAN, "title required")
        if not _is_int(trial_cap) or trial_cap < 1:
            raise TrialError(E_FT_BAD_PLAN, str(trial_cap))
        if not isinstance(ai_generated, bool):
            raise TrialError(E_FT_BAD_PLAN, "ai_generated must be bool")
        label = 1 if ai_generated else 0
        with self._lock:
            row = self._conn.execute(
                "SELECT plan_id FROM trial_plans WHERE plan_key = ?",
                (key,)).fetchone()
            if row is not None:
                raise TrialError(E_FT_DUP_PLAN, key)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO trial_plans (plan_key, title,"
                    " trial_cap, ai_label, registered_utc)"
                    " VALUES (?,?,?,?,?)",
                    (key, str(title), trial_cap, label, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise TrialError(E_FT_DUP_PLAN, key)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"plan_id": cur.lastrowid, "plan_key": key,
                "title": str(title), "trial_cap": trial_cap,
                "ai_label": label, "disclaimer": self.disclaimer}

    def _require_plan(self, plan_id):
        """Validation + lookup (caller holds the lock). Returns the
        full plan row."""
        if not _is_int(plan_id) or plan_id <= 0:
            raise TrialError(E_FT_BAD_ARGS, str(plan_id))
        row = self._conn.execute(
            "SELECT plan_id, plan_key, title, trial_cap, ai_label"
            " FROM trial_plans WHERE plan_id = ?", (plan_id,)).fetchone()
        if row is None:
            raise TrialError(E_FT_UNKNOWN_PLAN, str(plan_id))
        return row

    # -- trial grant domain ---------------------------------------------------

    def grant_trial(self, dev_account, plan_id):
        """Grant one free trial to a developer on a plan: the
        registry gate runs first (an off-register developer is
        refused E_FT_NOT_DEV before any row - zero rows), the plan
        must be known, and one grant exists per (developer, plan)
        - a replay is rejected with zero rows (AC-FT2). Zero fee,
        zero token movement - structural: this face holds no
        ledger reference at all."""
        who = self._require_account(dev_account)
        with self._lock:
            if not self._in_register(who):
                raise TrialError(E_FT_NOT_DEV, who)
            plan = self._require_plan(plan_id)
            p_key, cap = plan[1], int(plan[3])
            row = self._conn.execute(
                "SELECT grant_id FROM trial_grants"
                " WHERE dev_account = ? AND plan_id = ?",
                (who, plan_id)).fetchone()
            if row is not None:
                raise TrialError(E_FT_DUP_GRANT,
                                 "%s on %s" % (who, p_key))
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO trial_grants (plan_id, dev_account,"
                    " granted_utc) VALUES (?,?,?)",
                    (plan_id, who, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise TrialError(E_FT_DUP_GRANT,
                                 "%s on %s" % (who, p_key))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"grant_id": cur.lastrowid, "plan_id": plan_id,
                "plan_key": p_key, "dev_account": who,
                "trial_cap": cap, "ai_label": int(plan[4]),
                "disclaimer": self.disclaimer}

    # -- free-call domain (zero-fee trial window) ---------------------------

    def trial_call(self, dev_account, plan_id, kind, call_ref,
                   engine_ref):
        """Spend one free-trial call. Gate order (every reject
        leaves zero rows - AC-FT3): account shape, registry gate,
        plan known, grant exists (no grant, no free call -
        fail-closed E_FT_NO_TRIAL), converted gate (an upgraded
        developer has lost the free tier for good -
        E_FT_CONVERTED), replay gate (one call per (dev, plan,
        call_ref)), then the quota ring: when the immutable call
        rows for this (dev, plan) already cover the trial cap,
        call number cap+1 is refused E_FT_QUOTA with the upgrade
        hint - the conversion gate firing at exhaustion. A pass
        appends exactly one immutable call row (engine_ref stored
        as-is - engine provenance, the apidev ring-3 convention).
        The trial window is a lifetime window: the count never
        resets (the variant judgement against the apidev monthly
        ring). Zero fee, zero token movement - structural."""
        who = self._require_account(dev_account)
        k = str(kind or "").strip()
        if not k:
            raise TrialError(E_FT_BAD_ARGS, "kind required")
        r = str(call_ref or "").strip()
        if not r:
            raise TrialError(E_FT_BAD_ARGS, "call ref required")
        eng = str(engine_ref or "").strip()
        if not eng:
            raise TrialError(E_FT_BAD_ARGS, "engine ref required")
        with self._lock:
            if not self._in_register(who):
                raise TrialError(E_FT_NOT_DEV, who)
            plan = self._require_plan(plan_id)
            p_key, cap, label = plan[1], int(plan[3]), int(plan[4])
            row = self._conn.execute(
                "SELECT grant_id FROM trial_grants"
                " WHERE dev_account = ? AND plan_id = ?",
                (who, plan_id)).fetchone()
            if row is None:
                raise TrialError(E_FT_NO_TRIAL,
                                 "%s holds no trial on %s"
                                 % (who, p_key))
            conv = self._conn.execute(
                "SELECT tier_key FROM trial_conversions"
                " WHERE dev_account = ? AND plan_id = ?",
                (who, plan_id)).fetchone()
            if conv is not None:
                raise TrialError(E_FT_CONVERTED,
                                 "%s already upgraded to %s - the"
                                 " free tier on %s is closed"
                                 % (who, conv[0], p_key))
            row = self._conn.execute(
                "SELECT call_id FROM trial_calls"
                " WHERE dev_account = ? AND plan_id = ?"
                " AND call_ref = ?", (who, plan_id, r)).fetchone()
            if row is not None:
                raise TrialError(E_FT_DUP,
                                 "%s/%s/%s" % (who, p_key, r))
            used = self._conn.execute(
                "SELECT COUNT(*) FROM trial_calls"
                " WHERE dev_account = ? AND plan_id = ?",
                (who, plan_id)).fetchone()[0]
            if used >= cap:
                raise TrialError(E_FT_QUOTA,
                                 "%s trial cap %d reached on %s -"
                                 " upgrade to continue"
                                 % (who, cap, p_key))
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO trial_calls (plan_id, dev_account,"
                    " kind, call_ref, engine_ref, called_utc)"
                    " VALUES (?,?,?,?,?,?)",
                    (plan_id, who, k, r, eng, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise TrialError(E_FT_DUP,
                                 "%s/%s/%s" % (who, p_key, r))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"call_id": cur.lastrowid, "plan_id": plan_id,
                "plan_key": p_key, "dev_account": who, "kind": k,
                "call_ref": r, "engine_ref": eng,
                "calls_used": used + 1, "trial_cap": cap,
                "ai_label": label, "disclaimer": self.disclaimer}

    # -- upgrade-conversion domain ------------------------------------------

    def convert_upgrade(self, dev_account, plan_id, tier_key):
        """Register the upgrade conversion: the trial's terminal
        state. Gate order (AC-FT4): account shape, target tier
        key non-empty, registry gate, plan known, grant exists
        (no trial, nothing to convert - E_FT_NO_TRIAL), then one
        conversion per (dev, plan) - a replay is rejected
        E_FT_DUP_CONVERT with zero rows (the member
        tier-grant structure reference: one enrollment per
        member per tier). A pass appends exactly one immutable
        conversion row with the target tier key and its
        provenance timestamp; after it the free calls on this
        plan close fail-closed. Conversion moves zero tokens -
        the real paid path is the existing apidev/metered
        buy_credits face (referenced, not rebuilt); production
        target-tier pricing is a [needs-CEO] batch."""
        who = self._require_account(dev_account)
        tier = str(tier_key or "").strip()
        if not tier:
            raise TrialError(E_FT_BAD_ARGS, "tier key required")
        with self._lock:
            if not self._in_register(who):
                raise TrialError(E_FT_NOT_DEV, who)
            plan = self._require_plan(plan_id)
            p_key = plan[1]
            row = self._conn.execute(
                "SELECT grant_id FROM trial_grants"
                " WHERE dev_account = ? AND plan_id = ?",
                (who, plan_id)).fetchone()
            if row is None:
                raise TrialError(E_FT_NO_TRIAL,
                                 "%s holds no trial on %s"
                                 % (who, p_key))
            row = self._conn.execute(
                "SELECT conversion_id FROM trial_conversions"
                " WHERE dev_account = ? AND plan_id = ?",
                (who, plan_id)).fetchone()
            if row is not None:
                raise TrialError(E_FT_DUP_CONVERT,
                                 "%s on %s" % (who, p_key))
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO trial_conversions (plan_id,"
                    " dev_account, tier_key, converted_utc)"
                    " VALUES (?,?,?,?)",
                    (plan_id, who, tier, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise TrialError(E_FT_DUP_CONVERT,
                                 "%s on %s" % (who, p_key))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"conversion_id": cur.lastrowid, "plan_id": plan_id,
                "plan_key": p_key, "dev_account": who,
                "tier_key": tier, "ai_label": int(plan[4]),
                "disclaimer": self.disclaimer}

    # -- read faces (pure reads, COUNT-derived, zero cached state) -----------

    def trial_view(self, dev_account, plan_id):
        """One developer's trial state on one plan: granted or not,
        the immutable call count, the remaining allowance (COUNT
        faces, zero cached counters), the conversion state and its
        target tier (AC-FT6). The envelope carries the declared
        AIGC label and the resident disclaimer (AC-FT5). Pure
        read."""
        who = self._require_account(dev_account)
        with self._lock:
            plan = self._require_plan(plan_id)
            p_key, cap, label = plan[1], int(plan[3]), int(plan[4])
            grant = self._conn.execute(
                "SELECT grant_id, granted_utc FROM trial_grants"
                " WHERE dev_account = ? AND plan_id = ?",
                (who, plan_id)).fetchone()
            used = self._conn.execute(
                "SELECT COUNT(*) FROM trial_calls"
                " WHERE dev_account = ? AND plan_id = ?",
                (who, plan_id)).fetchone()[0]
            conv = self._conn.execute(
                "SELECT tier_key, converted_utc FROM"
                " trial_conversions WHERE dev_account = ?"
                " AND plan_id = ?", (who, plan_id)).fetchone()
        return {"dev_account": who, "plan_id": plan_id,
                "plan_key": p_key, "trial_cap": cap,
                "granted": grant is not None,
                "granted_utc": None if grant is None else grant[1],
                "calls_used": int(used),
                "calls_remaining": max(0, cap - int(used)),
                "converted": conv is not None,
                "tier_key": None if conv is None else conv[0],
                "converted_utc": None if conv is None else conv[1],
                "ai_label": label, "disclaimer": self.disclaimer}

    def plan_view(self, plan_id):
        """One plan surface: registry row plus grant/call/
        conversion counts (AC-FT6). Pure read."""
        with self._lock:
            plan = self._require_plan(plan_id)
            row = self._conn.execute(
                "SELECT plan_id, plan_key, title, trial_cap,"
                " ai_label, registered_utc FROM trial_plans"
                " WHERE plan_id = ?", (plan_id,)).fetchone()
            grants = self._conn.execute(
                "SELECT COUNT(*) FROM trial_grants"
                " WHERE plan_id = ?", (plan_id,)).fetchone()[0]
            calls = self._conn.execute(
                "SELECT COUNT(*) FROM trial_calls"
                " WHERE plan_id = ?", (plan_id,)).fetchone()[0]
            convs = self._conn.execute(
                "SELECT COUNT(*) FROM trial_conversions"
                " WHERE plan_id = ?", (plan_id,)).fetchone()[0]
        return {"plan_id": int(row[0]), "plan_key": row[1],
                "title": row[2], "trial_cap": int(row[3]),
                "ai_label": int(row[4]), "registered_utc": row[5],
                "grant_count": int(grants), "call_count": int(calls),
                "conversion_count": int(convs),
                "disclaimer": self.disclaimer}

    def plan_board(self):
        """Full plan registry board in registry order, every row
        carrying its declared AIGC label (AC-FT6). Pure read."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT plan_id, plan_key, title, trial_cap,"
                " ai_label, registered_utc FROM trial_plans"
                " ORDER BY plan_id").fetchall()
        return {"plans": [{"plan_id": int(r[0]), "plan_key": r[1],
                           "title": r[2], "trial_cap": int(r[3]),
                           "ai_label": int(r[4]),
                           "registered_utc": r[5]} for r in rows],
                "disclaimer": self.disclaimer}

    def trials_board(self, plan_id):
        """Per-plan grant audit trail: every grant row in grant
        order (AC-FT6). Pure read."""
        with self._lock:
            self._require_plan(plan_id)
            rows = self._conn.execute(
                "SELECT grant_id, dev_account, granted_utc FROM"
                " trial_grants WHERE plan_id = ?"
                " ORDER BY grant_id", (plan_id,)).fetchall()
        return {"plan_id": plan_id, "disclaimer": self.disclaimer,
                "grants": [{"grant_id": int(r[0]),
                            "dev_account": r[1],
                            "granted_utc": r[2]} for r in rows]}

    def conversions_board(self, plan_id):
        """Per-plan conversion audit trail: every terminal
        conversion row with its target tier and provenance
        timestamp (AC-FT6). Pure read."""
        with self._lock:
            self._require_plan(plan_id)
            rows = self._conn.execute(
                "SELECT conversion_id, dev_account, tier_key,"
                " converted_utc FROM trial_conversions"
                " WHERE plan_id = ? ORDER BY conversion_id",
                (plan_id,)).fetchall()
        return {"plan_id": plan_id, "disclaimer": self.disclaimer,
                "conversions": [{"conversion_id": int(r[0]),
                                 "dev_account": r[1],
                                 "tier_key": r[2],
                                 "converted_utc": r[3]}
                                for r in rows]}

    def conversion_funnel_board(self, window=None):
        """Plan-level conversion-funnel board (R1788 explore
        queue row; the seed = this face's R1768 registry): one
        row per registered plan carrying the grant count, the
        terminal-conversion count, the derived active-trial
        count and the conversion rate. Every aggregate is a
        row count over immutable rows at read time (the
        conversion gate is itself a conversion-row count - the
        registered verdict); zero cached counters, zero stored
        state. active = granted minus converted, structurally
        non-negative (the conversion gate requires a grant row
        first); rate = round(converted / granted, 4) with the
        zero-grant guard defaulting to 0.0. Rows walk in
        plan_key ascending order - a unique key, so the board
        is deterministic with zero dice and zero insertion-order
        keys. The declared AIGC label persists on every row and
        the envelope carries the resident disclaimer. Pure
        read.

        Window parameterization (R1793 tech-queue row, the
        R1730/R1732/R1735/R1784 family law): window=None is
        the full-window default with zero drift against the
        prior single-arg behavior; an explicit "YYYY-MM" month
        window filters granted by granted_utc and converted by
        converted_utc (record-time columns, each row family on
        its own provenance stamp - the seed verdict). In a
        windowed read active_trials switches to the
        end-of-window snapshot: grants whose grant month is at
        or before the window minus conversions whose conversion
        month is at or before the window - the conversion gate
        forces month(grant) <= month(conversion), so the
        subtraction keeps the structurally-non-negative
        registered verdict across windows; the in-window net
        flow (granted_w - converted_w, which may go negative
        when an earlier grant converts inside this window) is
        deliberately NOT surfaced under this field name. The
        conversion rate stays the window-filtered ratio under
        the same zero-grant guard. The explicit-window envelope
        adds one "window" key (additive); the default envelope
        is byte-identical to the prior shape. A malformed
        window fails closed E_FT_BAD_ARGS before any read
        (zero side effects)."""
        w = None
        if window is not None:
            w = str(window)
            if not _WINDOW_RE.match(w):
                raise TrialError(E_FT_BAD_ARGS,
                                 "window must be YYYY-MM: %r"
                                 % (window,))
        with self._lock:
            plans = self._conn.execute(
                "SELECT plan_id, plan_key, title, ai_label FROM"
                " trial_plans ORDER BY plan_key").fetchall()
            rows = []
            for plan_id, p_key, title, label in plans:
                if w is None:
                    granted = self._conn.execute(
                        "SELECT COUNT(*) FROM trial_grants"
                        " WHERE plan_id = ?",
                        (plan_id,)).fetchone()[0]
                    converted = self._conn.execute(
                        "SELECT COUNT(*) FROM trial_conversions"
                        " WHERE plan_id = ?",
                        (plan_id,)).fetchone()[0]
                    active = int(granted) - int(converted)
                else:
                    granted = self._conn.execute(
                        "SELECT COUNT(*) FROM trial_grants"
                        " WHERE plan_id = ?"
                        " AND substr(granted_utc, 1, 7) = ?",
                        (plan_id, w)).fetchone()[0]
                    converted = self._conn.execute(
                        "SELECT COUNT(*) FROM trial_conversions"
                        " WHERE plan_id = ?"
                        " AND substr(converted_utc, 1, 7) = ?",
                        (plan_id, w)).fetchone()[0]
                    g_cum = self._conn.execute(
                        "SELECT COUNT(*) FROM trial_grants"
                        " WHERE plan_id = ?"
                        " AND substr(granted_utc, 1, 7) <= ?",
                        (plan_id, w)).fetchone()[0]
                    c_cum = self._conn.execute(
                        "SELECT COUNT(*) FROM trial_conversions"
                        " WHERE plan_id = ?"
                        " AND substr(converted_utc, 1, 7) <= ?",
                        (plan_id, w)).fetchone()[0]
                    active = int(g_cum) - int(c_cum)
                rate = (round(converted / granted, 4)
                        if granted > 0 else 0.0)
                rows.append({"plan_id": int(plan_id),
                             "plan_key": p_key, "title": title,
                             "ai_label": int(label),
                             "granted": int(granted),
                             "converted": int(converted),
                             "active_trials": int(active),
                             "conversion_rate": rate})
        env = {"conversion_funnel_board": rows}
        if w is not None:
            env["window"] = w
        env["disclaimer"] = self.disclaimer
        return env

    def calls_by_month(self, window=None):
        """Free-trial call volume by calendar month (R1793
        tech-queue follow-up row; the seed = the trial_calls
        table itself): a pure-read aggregation over immutable
        call rows with one dict cell per observed month key
        holding the call count - the global by-month profile
        the per-plan lifetime counters (plan_view / trial_view)
        never surface. Aggregation walks
        substr(called_utc, 1, 7) - the record-time column is
        the row's own provenance stamp on this immutable table
        (single event family, single column - the R1793 grant
        /conversion pair used two record-time columns because
        two row families were filtered; this face has one).
        Month keys ascend in query order (a unique group key,
        so the dict is deterministic with zero dice and zero
        insertion-order keys); a zero-call world is the honest
        empty mapping with total 0 - no phantom months.

        Window parameterization (the R1730/R1732/R1735/R1784
        family law): window=None keeps the full-window
        aggregate; an explicit "YYYY-MM" month window keeps
        only that month's cell (an empty mapping when the
        month holds zero rows). A malformed window fails
        closed E_FT_BAD_ARGS before any read. Every count is
        derived at read time over immutable rows: zero cached
        counters, zero stored state. The explicit-window
        envelope adds one "window" key (additive); the
        default envelope is byte-identical in shape. Pure
        read."""
        w = None
        if window is not None:
            w = str(window)
            if not _WINDOW_RE.match(w):
                raise TrialError(E_FT_BAD_ARGS,
                                 "window must be YYYY-MM: %r"
                                 % (window,))
        with self._lock:
            if w is None:
                rows = self._conn.execute(
                    "SELECT substr(called_utc, 1, 7), COUNT(*)"
                    " FROM trial_calls"
                    " GROUP BY substr(called_utc, 1, 7)"
                    " ORDER BY substr(called_utc, 1, 7)").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT substr(called_utc, 1, 7), COUNT(*)"
                    " FROM trial_calls"
                    " WHERE substr(called_utc, 1, 7) = ?"
                    " GROUP BY substr(called_utc, 1, 7)"
                    " ORDER BY substr(called_utc, 1, 7)",
                    (w,)).fetchall()
            by_month = {str(r[0]): int(r[1]) for r in rows}
            total = sum(by_month.values())
        env = {"calls_by_month": by_month, "total": total}
        if w is not None:
            env["window"] = w
        env["disclaimer"] = self.disclaimer
        return env

    def calls_by_kind(self, window=None):
        """Free-trial call volume by usage kind (R1828
        tech-queue follow-up row; the seed = the calls_by_month
        face): a pure-read aggregation over immutable call rows
        with one dict cell per observed kind key holding the
        call count - the global "which kind, how many" profile
        the per-month profile (calls_by_month) never surfaces.
        kind is a free TEXT domain with no CHECK constraint
        (trial_calls.kind), so aggregation walks whatever values
        are observed: keys ascend in query order (a unique
        group key, so the dict is deterministic with zero dice
        and zero insertion-order surprises), and an observed
        kind outside the registered usage tally domain is NOT
        hidden - it surfaces in ascending order and counts
        toward total (the face never hides data, the R1776
        AC-CHM3 law; the same free-domain ruling the apidev
        usage_kind_tally face already carries). A zero-call
        world is the honest empty mapping with total 0 - no
        phantom kinds.

        Window parameterization (the R1730/R1732/R1735/R1784/
        R1793 family law): window=None keeps the full-window
        aggregate; an explicit "YYYY-MM" month window filters
        rows by their called_utc record-time stamp first, then
        aggregates kinds over the surviving rows (a row-filter
        window, orthogonal to the calls_by_month cell window).
        A malformed window fails closed E_FT_BAD_ARGS before
        any read. Every count is derived at read time over
        immutable rows: zero cached counters, zero stored
        state. The explicit-window envelope adds one "window"
        key (additive); the default envelope is byte-identical
        in shape. Pure read."""
        w = None
        if window is not None:
            w = str(window)
            if not _WINDOW_RE.match(w):
                raise TrialError(E_FT_BAD_ARGS,
                                 "window must be YYYY-MM: %r"
                                 % (window,))
        with self._lock:
            if w is None:
                rows = self._conn.execute(
                    "SELECT kind, COUNT(*)"
                    " FROM trial_calls"
                    " GROUP BY kind"
                    " ORDER BY kind").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT kind, COUNT(*)"
                    " FROM trial_calls"
                    " WHERE substr(called_utc, 1, 7) = ?"
                    " GROUP BY kind"
                    " ORDER BY kind",
                    (w,)).fetchall()
            by_kind = {str(r[0]): int(r[1]) for r in rows}
            total = sum(by_kind.values())
        env = {"calls_by_kind": by_kind, "total": total}
        if w is not None:
            env["window"] = w
        env["disclaimer"] = self.disclaimer
        return env

    def calls_by_plan(self, window=None):
        """Free-trial call volume by plan (R1830 tech-queue
        follow-up row; the seed = the calls_by_kind R1829
        face): a pure-read aggregation over immutable call rows
        with one dict cell per observed plan_id holding the
        call count - the global "which plan, how many" profile
        the per-kind profile (calls_by_kind) never surfaces.
        plan_id is a structured INTEGER domain
        (trial_calls.plan_id, no CHECK, no FK), so the keys are
        integers walking in ascending query order (a unique
        group key, zero dice and zero insertion-order
        surprises). An observed plan_id outside the
        trial_plans registry - an orphan row only direct
        injection can produce, since the live call gate
        requires a registered plan and a grant first - is NOT
        hidden: it surfaces in ascending integer order and
        counts toward total (the face never hides data, the
        R1776 AC-CHM3 law; the AC-CBK5 ruling). A zero-call
        world is the honest empty mapping with total 0 - no
        phantom plans.

        Window parameterization (the R1730/R1732/R1735/R1784/
        R1793 family law): window=None keeps the full-window
        aggregate; an explicit "YYYY-MM" month window filters
        rows by their called_utc record-time stamp first, then
        aggregates plans over the surviving rows (a row-filter
        window, orthogonal to the calls_by_month cell window).
        A malformed window fails closed E_FT_BAD_ARGS before
        any read. Every count is derived at read time over
        immutable rows: zero cached counters, zero stored
        state. The explicit-window envelope adds one "window"
        key (additive); the default envelope is byte-identical
        in shape. Pure read."""
        w = None
        if window is not None:
            w = str(window)
            if not _WINDOW_RE.match(w):
                raise TrialError(E_FT_BAD_ARGS,
                                 "window must be YYYY-MM: %r"
                                 % (window,))
        with self._lock:
            if w is None:
                rows = self._conn.execute(
                    "SELECT plan_id, COUNT(*)"
                    " FROM trial_calls"
                    " GROUP BY plan_id"
                    " ORDER BY plan_id").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT plan_id, COUNT(*)"
                    " FROM trial_calls"
                    " WHERE substr(called_utc, 1, 7) = ?"
                    " GROUP BY plan_id"
                    " ORDER BY plan_id",
                    (w,)).fetchall()
            by_plan = {int(r[0]): int(r[1]) for r in rows}
            total = sum(by_plan.values())
        env = {"calls_by_plan": by_plan, "total": total}
        if w is not None:
            env["window"] = w
        env["disclaimer"] = self.disclaimer
        return env

    def calls_by_engine(self, window=None):
        """Free-trial call volume by engine (R1831
        tech-queue follow-up row; the seed = the calls_by_kind
        R1829 face): a pure-read aggregation over immutable call
        rows with one dict cell per observed engine_ref stamp
        holding the call count - the global "which engine, how
        many" profile the kind, plan and month profiles never
        surface. engine_ref is a free TEXT domain
        (trial_calls.engine_ref), the engine attribution stamp
        (the apidev ring-3 convention: a live call always
        carries a non-empty stamp), so aggregation walks
        whatever values are observed: keys ascend in query
        order (a unique group key, so the dict is deterministic
        with zero dice and zero insertion-order surprises), and
        an observed stamp outside the live-call gate's stamp
        set - only direct injection can produce one - is NOT
        hidden: it surfaces in ascending order and counts
        toward total (the face never hides data, the R1776
        AC-CHM3 law; the AC-CBK5 free-domain ruling). A
        zero-call world is the honest empty mapping with total
        0 - no phantom engines.

        Window parameterization (the R1730/R1732/R1735/R1784/
        R1793 family law): window=None keeps the full-window
        aggregate; an explicit "YYYY-MM" month window filters
        rows by their called_utc record-time stamp first, then
        aggregates engine stamps over the surviving rows (a
        row-filter window, orthogonal to the calls_by_month
        cell window). A malformed window fails closed
        E_FT_BAD_ARGS before any read. Every count is derived
        at read time over immutable rows: zero cached
        counters, zero stored state. The explicit-window
        envelope adds one "window" key (additive); the default
        envelope is byte-identical in shape. Pure read."""
        w = None
        if window is not None:
            w = str(window)
            if not _WINDOW_RE.match(w):
                raise TrialError(E_FT_BAD_ARGS,
                                 "window must be YYYY-MM: %r"
                                 % (window,))
        with self._lock:
            if w is None:
                rows = self._conn.execute(
                    "SELECT engine_ref, COUNT(*)"
                    " FROM trial_calls"
                    " GROUP BY engine_ref"
                    " ORDER BY engine_ref").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT engine_ref, COUNT(*)"
                    " FROM trial_calls"
                    " WHERE substr(called_utc, 1, 7) = ?"
                    " GROUP BY engine_ref"
                    " ORDER BY engine_ref",
                    (w,)).fetchall()
            by_engine = {str(r[0]): int(r[1]) for r in rows}
            total = sum(by_engine.values())
        env = {"calls_by_engine": by_engine, "total": total}
        if w is not None:
            env["window"] = w
        env["disclaimer"] = self.disclaimer
        return env

    def calls_by_account(self, window=None):
        """Free-trial call volume by developer account (R1837
        tech-queue follow-up row; the seed = the calls_by_engine
        R1831 face): a pure-read aggregation over immutable call
        rows with one dict cell per observed dev_account stamp
        holding the call count - the global "which developer,
        how many" profile the month, kind, plan and engine
        profiles never surface. dev_account is the developer
        account stamp (trial_calls.dev_account TEXT; the live
        call gate always stamps an in-register "usr:"-shaped
        account - grant first, then call - so the observed
        account set of a live-only world is a superset of the
        grant set), so aggregation walks whatever values are
        observed: keys ascend in query order (a unique group
        key, so the dict is deterministic with zero dice and
        zero insertion-order surprises), and an observed stamp
        outside the live-call gate's account set - a history
        fixture account or an outright non-"usr:"-shaped stamp,
        only direct injection can produce either - is NOT
        hidden: it surfaces in ascending order and counts
        toward total (the face never hides data, the R1776
        AC-CHM3 law; the AC-CBE5 free-domain ruling). A
        zero-call world is the honest empty mapping with total
        0 - no phantom accounts.

        Window parameterization (the R1730/R1732/R1735/R1784/
        R1793 family law): window=None keeps the full-window
        aggregate; an explicit "YYYY-MM" month window filters
        rows by their called_utc record-time stamp first, then
        aggregates account stamps over the surviving rows (a
        row-filter window, orthogonal to the calls_by_month
        cell window). A malformed window fails closed
        E_FT_BAD_ARGS before any read. Every count is derived
        at read time over immutable rows: zero cached
        counters, zero stored state. The explicit-window
        envelope adds one "window" key (additive); the default
        envelope is byte-identical in shape. Pure read."""
        w = None
        if window is not None:
            w = str(window)
            if not _WINDOW_RE.match(w):
                raise TrialError(E_FT_BAD_ARGS,
                                 "window must be YYYY-MM: %r"
                                 % (window,))
        with self._lock:
            if w is None:
                rows = self._conn.execute(
                    "SELECT dev_account, COUNT(*)"
                    " FROM trial_calls"
                    " GROUP BY dev_account"
                    " ORDER BY dev_account").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT dev_account, COUNT(*)"
                    " FROM trial_calls"
                    " WHERE substr(called_utc, 1, 7) = ?"
                    " GROUP BY dev_account"
                    " ORDER BY dev_account",
                    (w,)).fetchall()
            by_account = {str(r[0]): int(r[1]) for r in rows}
            total = sum(by_account.values())
        env = {"calls_by_account": by_account, "total": total}
        if w is not None:
            env["window"] = w
        env["disclaimer"] = self.disclaimer
        return env

    def cap_usage_board(self, window=None):
        """Per-grant cap-distance profile board (R1842
        tech-queue claim row; the seed = the calls_by_account
        R1837 face plus the cap_usage seed text): one row per
        trial grant joined to its plan registry values, carrying
        the lifetime call count and the remaining cap distance -
        the "who is close to the cap" conversion-gate proximity
        profile the month, kind, plan, engine and account
        single-axis call profiles never surface. calls_used is
        the lifetime count of immutable call rows stamped with
        the same (dev_account, plan_id) pair, and remaining is
        the plain arithmetic trial_cap minus calls_used: in a
        live-only world every remaining value is at least 1 by
        structure (the live call gate refuses once the count
        reaches the cap), so a negative remaining - only
        directly injected extra call rows can produce one - is
        NOT hidden: the row surfaces in ascending order and
        counts toward total (the face never hides data, the
        R1776 AC-CHM3 law; the R1838 dm_precheck injection
        convention). A zero-grant world is the honest empty
        board with total 0 - no phantom grants. Converted
        developers keep their grant rows here: the conversion
        records are a separate register (conversions_board) and
        never merge into this board; a grant row does not
        vanish at conversion, so its cap distance stays
        readable. The row is a grant-times-plan-registry join:
        an orphan grant row (no registry plan - only direct
        injection can produce one, the live grant gate checks
        the registry first) falls outside the join domain and
        does not surface here; the raw grant census stays
        visible on the plan and trials listing faces.

        Window parameterization (the R1730/R1732/R1735/R1784/
        R1793 family law, with the count-domain verdict
        registered in the R1842 claim row): window=None keeps
        every grant row on the board; an explicit "YYYY-MM"
        month window filters GRANT rows by their granted_utc
        record-time stamp - the surviving grant rows still
        carry LIFETIME calls_used and remaining values (the
        count domain is never sliced by the window: "who is
        close to the cap" is a property of the grant's whole
        life, not of the month's net flow - the seed's
        count-domain-not-sliced honesty note). A malformed
        window fails closed E_FT_BAD_ARGS before any read.
        Every count is derived at read time over immutable
        rows: zero cached counters, zero stored state. The
        explicit-window envelope adds one "window" key
        (additive); the default envelope is byte-identical in
        shape. Rows order by (dev_account, plan_id) ascending -
        a unique grant key pair, so the board is deterministic
        with zero dice and zero insertion-order surprises.
        The persistent ai_label rides every row (the AIGC
        labeling law: every view surface shows it). Pure
        read."""
        w = None
        if window is not None:
            w = str(window)
            if not _WINDOW_RE.match(w):
                raise TrialError(E_FT_BAD_ARGS,
                                 "window must be YYYY-MM: %r"
                                 % (window,))
        with self._lock:
            if w is None:
                rows = self._conn.execute(
                    "SELECT g.dev_account, g.plan_id,"
                    " p.plan_key, p.title, p.trial_cap,"
                    " g.granted_utc, p.ai_label,"
                    " (SELECT COUNT(*) FROM trial_calls c"
                    " WHERE c.dev_account = g.dev_account"
                    " AND c.plan_id = g.plan_id)"
                    " FROM trial_grants g"
                    " JOIN trial_plans p ON p.plan_id = g.plan_id"
                    " ORDER BY g.dev_account, g.plan_id").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT g.dev_account, g.plan_id,"
                    " p.plan_key, p.title, p.trial_cap,"
                    " g.granted_utc, p.ai_label,"
                    " (SELECT COUNT(*) FROM trial_calls c"
                    " WHERE c.dev_account = g.dev_account"
                    " AND c.plan_id = g.plan_id)"
                    " FROM trial_grants g"
                    " JOIN trial_plans p ON p.plan_id = g.plan_id"
                    " WHERE substr(g.granted_utc, 1, 7) = ?"
                    " ORDER BY g.dev_account, g.plan_id",
                    (w,)).fetchall()
            board = []
            for r in rows:
                used = int(r[7])
                cap = int(r[4])
                board.append({
                    "dev_account": str(r[0]),
                    "plan_id": int(r[1]),
                    "plan_key": str(r[2]),
                    "title": str(r[3]),
                    "trial_cap": cap,
                    "calls_used": used,
                    "remaining": cap - used,
                    "granted_utc": str(r[5]),
                    "ai_label": int(r[6]),
                })
            total = len(board)
        env = {"cap_usage_board": board, "total": total}
        if w is not None:
            env["window"] = w
        env["disclaimer"] = self.disclaimer
        return env
