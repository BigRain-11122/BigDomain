"""Trading-hall value-added expedite privileges face over the token
ledger sandbox (BigDomain R620; canon = BLUEPRINT sec-4 hall
value-added line, C3/C7 price rows; claimed from the explore-lane
top row under the zero-idle night order O-2026-0929-027).

Four purchasable expedite products ride on the P-47-2b token ledger,
one priority credit per purchase, each bound to exactly one token
spend:

  kind 'submit_expedite'  : jumps jobs whose subject is 'idea:*'
  kind 'backtest_expedite': jumps jobs whose subject is 'backtest:*'
  kind 'demo_queuejump'   : jumps jobs whose subject is 'demo:*'
  kind 'resident_dialogue'  : jumps jobs whose subject is 'talk:*'

Mechanism (pre-registered criteria AC-XP1..AC-XP7 live in the R620
backlog row and were written before this code existed; honesty law):
a two-tier priority queue.

  - purchase is idempotent on the caller ref: a repeated ref returns
    the existing credit with no second charge (AC-XP1).
  - submit enqueues a hall job. Without expedite_kind it is a normal
    job (no gate, no token). With expedite_kind the call consumes
    exactly one unconsumed credit of the matching kind - the kind
    must match the subject domain (AC-XP4) - and the job joins the
    expedited tier, which ranks ahead of every normal job; inside
    each tier jobs stay FIFO by submission order (AC-XP5).
  - a consumed credit is consumed once and carries the job it
    jumped (AC-XP6).

Counts stay counts and tokens stay tokens (props posture): the only
token-domain touch is the purchase spend; consumption is pure
bookkeeping. The single UPDATE surface in this module is the
consumption marking on credit rows; no verb moves a credit between
accounts and no ownership column is ever rewritten.

Prices are caller-supplied in the sandbox; the production price
points (canon anchors 9.9 / 9.9 / 49.9 / 4.9 yuan tiers) and any
launch gating are a P1 item for CEO, approval-only ([needs-CEO]).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: two extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_EXP_BAD_ACCOUNT = "E_EXP_BAD_ACCOUNT"      # AC-XP7
E_EXP_BAD_KIND = "E_EXP_BAD_KIND"            # AC-XP4 / AC-XP7
E_EXP_BAD_AMOUNT = "E_EXP_BAD_AMOUNT"         # AC-XP7
E_EXP_BAD_REF = "E_EXP_BAD_REF"               # AC-XP7
E_EXP_BAD_SUBJECT = "E_EXP_BAD_SUBJECT"       # AC-XP7
E_EXP_NO_CREDIT = "E_EXP_NO_CREDIT"           # AC-XP3 / AC-XP6
E_EXP_KIND_MISMATCH = "E_EXP_KIND_MISMATCH"   # AC-XP4

KIND_SUBJECT = {
    "submit_expedite": "idea:",
    "backtest_expedite": "backtest:",
    "demo_queuejump": "demo:",
    "resident_dialogue": "talk:",
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS expedite_credits (
    credit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN
        ('submit_expedite','backtest_expedite','demo_queuejump',
         'resident_dialogue')),
    purchase_ref TEXT NOT NULL UNIQUE,
    token_price INTEGER NOT NULL CHECK (token_price > 0),
    bound_spend_tx TEXT NOT NULL,
    purchased_utc TEXT NOT NULL,
    consumed_utc TEXT,
    consumed_job INTEGER
);
CREATE TABLE IF NOT EXISTS expedite_jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    expedited INTEGER NOT NULL DEFAULT 0 CHECK (expedited IN (0,1)),
    base_seq INTEGER NOT NULL UNIQUE,
    used_credit INTEGER,
    submitted_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class ExpediteError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class ExpediteFace:
    """Expedite-privilege face over one Ledger instance. Own
    connection and lock into the same DB file; every mutation runs
    inside BEGIN IMMEDIATE."""

    def __init__(self, ledger):
        self.led = ledger
        self.db_path = ledger.db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                      isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- writer faces -------------------------------------------------------

    def purchase(self, account_id, kind, token_price, ref):
        """Idempotent purchase face: one token spend (the only
        token-domain touch) buys one priority credit. A repeated
        purchase ref returns the existing credit with no second
        charge; a fresh ref spends once and binds its real tx."""
        if not account_id.startswith("usr:"):
            raise ExpediteError(E_EXP_BAD_ACCOUNT, account_id)
        kind = str(kind or "").strip()
        if kind not in KIND_SUBJECT:
            raise ExpediteError(E_EXP_BAD_KIND, kind)
        if (not isinstance(token_price, int) or isinstance(token_price, bool)
                or token_price <= 0):
            raise ExpediteError(E_EXP_BAD_AMOUNT, str(token_price))
        ref = str(ref or "").strip()
        if not ref:
            raise ExpediteError(E_EXP_BAD_REF, "purchase ref required")
        with self._lock:
            row = self._conn.execute(
                "SELECT credit_id, kind, token_price, bound_spend_tx,"
                " consumed_utc FROM expedite_credits WHERE purchase_ref = ?",
                (ref,)).fetchone()
            if row is not None:
                return {"credit_id": int(row[0]), "kind": row[1],
                        "token_price": int(row[2]), "spend_tx": row[3],
                        "consumed": row[4] is not None,
                        "idempotent": True}
            self.led.ensure_account(account_id,
                                    census_avatar_id=account_id[4:])
            spend_tx = self.led.spend(account_id, token_price, ref, "order")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO expedite_credits (account_id, kind,"
                    " purchase_ref, token_price, bound_spend_tx,"
                    " purchased_utc) VALUES (?,?,?,?,?,?)",
                    (account_id, kind, ref, token_price, spend_tx,
                     _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ExpediteError(E_EXP_BAD_REF, ref)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"credit_id": cur.lastrowid, "kind": kind,
                "token_price": token_price, "spend_tx": spend_tx,
                "consumed": False, "idempotent": False}

    def submit(self, account_id, subject, expedite_kind=None):
        """Hall queue submit face. Without expedite_kind the job joins
        the normal tier (no gate, no token). With expedite_kind the
        kind must match the subject domain and the account must own
        an unconsumed credit of that kind; the credit is consumed
        inside the same transaction that inserts the job, so a failed
        jump leaves zero rows. Returns the job's live queue
        position (1-based; expedited tier first)."""
        if not account_id.startswith("usr:"):
            raise ExpediteError(E_EXP_BAD_ACCOUNT, account_id)
        subject = str(subject or "").strip()
        if not subject:
            raise ExpediteError(E_EXP_BAD_SUBJECT, "subject required")
        kind = None
        if expedite_kind is not None:
            kind = str(expedite_kind or "").strip()
            if kind not in KIND_SUBJECT:
                raise ExpediteError(E_EXP_BAD_KIND, kind)
            if not subject.startswith(KIND_SUBJECT[kind]):
                raise ExpediteError(
                    E_EXP_KIND_MISMATCH,
                    "%s cannot jump %s" % (kind, subject))
        self.led.ensure_account(account_id, census_avatar_id=account_id[4:])
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                used_credit = None
                expedited = 0
                if kind is not None:
                    row = self._conn.execute(
                        "SELECT credit_id FROM expedite_credits"
                        " WHERE account_id = ? AND kind = ?"
                        " AND consumed_utc IS NULL"
                        " ORDER BY credit_id LIMIT 1",
                        (account_id, kind)).fetchone()
                    if row is None:
                        self._conn.execute("ROLLBACK")
                        raise ExpediteError(E_EXP_NO_CREDIT, kind)
                    used_credit = int(row[0])
                    expedited = 1
                seq_row = self._conn.execute(
                    "SELECT COALESCE(MAX(base_seq), 0) FROM"
                    " expedite_jobs").fetchone()
                base_seq = int(seq_row[0]) + 1
                cur = self._conn.execute(
                    "INSERT INTO expedite_jobs (account_id, subject,"
                    " expedited, base_seq, used_credit, submitted_utc)"
                    " VALUES (?,?,?,?,?,?)",
                    (account_id, subject, expedited, base_seq, used_credit,
                     _now_utc()))
                if used_credit is not None:
                    hit = self._conn.execute(
                        "UPDATE expedite_credits SET consumed_utc = ?,"
                        " consumed_job = ? WHERE credit_id = ?"
                        " AND consumed_utc IS NULL",
                        (_now_utc(), cur.lastrowid, used_credit))
                    if hit.rowcount != 1:
                        self._conn.execute("ROLLBACK")
                        raise ExpediteError(E_EXP_NO_CREDIT, kind)
                ahead = self._conn.execute(
                    "SELECT COUNT(*) FROM expedite_jobs WHERE"
                    " (expedited = 1 AND base_seq < ?)"
                    " OR (expedited = 0 AND ? = 0 AND base_seq < ?)",
                    (base_seq, expedited, base_seq)).fetchone()
                position = int(ahead[0]) + 1
                self._conn.execute("COMMIT")
            except ExpediteError:
                raise
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"job_id": cur.lastrowid, "subject": subject,
                "expedited": bool(expedited), "used_credit": used_credit,
                "base_seq": base_seq, "position": position}

    # -- read faces -----------------------------------------------------------

    def queue_snapshot(self):
        """Deterministic hall view: the expedited tier first (FIFO by
        submission seq), then the normal tier (FIFO); positions are
        1-based."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT job_id, account_id, subject, expedited, base_seq,"
                " used_credit FROM expedite_jobs"
                " ORDER BY expedited DESC, base_seq ASC").fetchall()
        jobs = []
        for pos, r in enumerate(rows, 1):
            jobs.append({"position": pos, "job_id": int(r[0]),
                         "account_id": r[1], "subject": r[2],
                         "expedited": bool(r[3]), "base_seq": int(r[4]),
                         "used_credit": r[5]})
        return {"jobs": jobs}

    def credits_view(self, account_id):
        """Per-account credit view: kind, purchase ref, bound spend
        tx and consumption state (with the job it jumped when
        consumed)."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT credit_id, kind, purchase_ref, token_price,"
                " bound_spend_tx, consumed_utc, consumed_job"
                " FROM expedite_credits WHERE account_id = ?"
                " ORDER BY credit_id", (account_id,)).fetchall()
        return {"account_id": account_id,
                "credits": [{"credit_id": int(r[0]), "kind": r[1],
                             "purchase_ref": r[2], "token_price": int(r[3]),
                             "spend_tx": r[4], "consumed": r[5] is not None,
                             "consumed_job": r[6]} for r in rows]}
