"""City digital collectibles face over the token ledger sandbox
(BigDomain R619; canon = BLUEPRINT sec-4 C-end item 6, the emotional
stickiness layer; lane restock under night order O-2026-0929-027 and
assurance order O-2026-0929-030 item-2).

Three collectible domains ride on the P-47-2b token ledger:

  - kind 'certificate' : memorial certificate awarded by the platform
    when a co-creation lands (e.g. a building completion). Zero token
    involvement; provenance = the creation event ref; one per account
    per event; permanent.
  - kind 'card'        : limited annual resident co-branded card.
    Claim is free but gated on a non-empty membership proof
    (caller-supplied, same posture as the liveroom risk-control
    reference; the real check wires to the member face at bootstrap).
    Deterministic numbering 1..cap in claim order, cap locked at the
    first claim of an edition; one card per account per edition.
  - kind 'replay'      : chronicle highlight replay right, purchased
    with exactly one token spend bound to its tx, permanent.

Hard law (canon wording: pure internal circulation, ownership never
changes hands between accounts, permanent imprint): this module
encodes the never-changes-hands posture at code level. No verb moves a
collectible between accounts, and the ownership columns of the
collectibles rows are never touched after grant (the only UPDATE in
this module is the edition issue counter). Any future face that lets
owners swap or hand off collectibles is a P1 item for CEO,
approval-only.

Counts stay counts and tokens stay tokens (props posture extended):
awarding and claiming never book a token tx; the replay purchase is
the single token-domain touch, one spend per right.

Pre-registered criteria AC-CL1..AC-CL7 live in the R619 backlog row
and were written before this code existed (honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: two extra tables in the same SQLite DB (WAL, single writer,
same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_CL_DUP = "E_CL_DUP"                      # AC-CL1 / AC-CL2 / AC-CL3
E_CL_BAD_REF = "E_CL_BAD_REF"              # AC-CL7
E_CL_BAD_AMOUNT = "E_CL_BAD_AMOUNT"        # AC-CL7
E_CL_BAD_EDITION = "E_CL_BAD_EDITION"      # AC-CL7
E_CL_MEMBERSHIP_REQUIRED = "E_CL_MEMBERSHIP_REQUIRED"  # AC-CL3
E_CL_SOLD_OUT = "E_CL_SOLD_OUT"            # AC-CL3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS collectibles (
    cl_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('certificate','card','replay')),
    item_id TEXT NOT NULL,
    event_ref TEXT NOT NULL,
    edition TEXT,
    card_no INTEGER,
    bound_spend_tx TEXT NOT NULL DEFAULT '',
    granted_utc TEXT NOT NULL,
    UNIQUE (account_id, kind, event_ref)
);
CREATE TABLE IF NOT EXISTS cl_editions (
    edition TEXT PRIMARY KEY,
    cap INTEGER NOT NULL CHECK (cap >= 1),
    issued INTEGER NOT NULL DEFAULT 0 CHECK (issued >= 0)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class CollectiblesError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class CollectiblesFace:
    """Collectibles face over one Ledger instance. Own connection and
    lock into the same DB file; every mutation runs inside BEGIN
    IMMEDIATE."""

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

    def issue_certificate(self, account_id, event_ref, item_id):
        """Platform award face: a memorial certificate bound to one
        creation event. Zero token-ledger involvement (the award is
        earned by the creation itself, not bought); duplicate award
        for the same account+event is rejected with zero rows added.
        The certificate is permanent: no verb consumes or expires it."""
        event_ref = str(event_ref).strip()
        if not event_ref:
            raise CollectiblesError(E_CL_BAD_REF, "event ref required")
        if not str(item_id).strip():
            raise CollectiblesError(E_CL_BAD_REF, "item id required")
        if not account_id.startswith("usr:"):
            raise CollectiblesError(E_CL_BAD_REF,
                                    "certificates are usr:* only")
        with self._lock:
            row = self._conn.execute(
                "SELECT cl_id FROM collectibles"
                " WHERE account_id = ? AND kind = 'certificate'"
                " AND event_ref = ?",
                (account_id, event_ref)).fetchone()
            if row is not None:
                raise CollectiblesError(E_CL_DUP, event_ref)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO collectibles (account_id, kind, item_id,"
                    " event_ref, edition, card_no, bound_spend_tx,"
                    " granted_utc) VALUES (?,?,?,?,?,?,?,?)",
                    (account_id, "certificate", str(item_id), event_ref,
                     None, None, "", _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise CollectiblesError(E_CL_DUP, event_ref)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"cl_id": cur.lastrowid, "kind": "certificate",
                "event_ref": event_ref, "item_id": str(item_id)}

    def claim_card(self, account_id, edition, item_id, cap, membership_proof):
        """Limited-edition claim face: free but gated on a non-empty
        membership proof (real check = member face at bootstrap; here
        the caller supplies the proof, liveroom risk-ref posture).
        Numbering is deterministic (claim order), the cap locks at the
        first claim of an edition, and a sold-out edition rejects with
        the counter untouched."""
        edition = str(edition).strip()
        if not edition:
            raise CollectiblesError(E_CL_BAD_EDITION, "edition required")
        if not str(item_id).strip():
            raise CollectiblesError(E_CL_BAD_REF, "item id required")
        if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:
            raise CollectiblesError(E_CL_BAD_EDITION, "cap must be >= 1")
        if not str(membership_proof or "").strip():
            raise CollectiblesError(E_CL_MEMBERSHIP_REQUIRED,
                                    "active member proof required")
        if not account_id.startswith("usr:"):
            raise CollectiblesError(E_CL_BAD_REF, "claims are usr:* only")
        with self._lock:
            row = self._conn.execute(
                "SELECT cl_id FROM collectibles"
                " WHERE account_id = ? AND kind = 'card'"
                " AND event_ref = ?",
                (account_id, edition)).fetchone()
            if row is not None:
                raise CollectiblesError(E_CL_DUP, edition)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT OR IGNORE INTO cl_editions (edition, cap,"
                    " issued) VALUES (?,?,0)", (edition, cap))
                ed = self._conn.execute(
                    "SELECT cap, issued FROM cl_editions WHERE edition = ?",
                    (edition,)).fetchone()
                ed_cap, issued = int(ed[0]), int(ed[1])
                if issued >= ed_cap:
                    self._conn.execute("ROLLBACK")
                    raise CollectiblesError(E_CL_SOLD_OUT,
                                            "%s %d/%d" % (edition, issued,
                                                          ed_cap))
                card_no = issued + 1
                cur = self._conn.execute(
                    "INSERT INTO collectibles (account_id, kind, item_id,"
                    " event_ref, edition, card_no, bound_spend_tx,"
                    " granted_utc) VALUES (?,?,?,?,?,?,?,?)",
                    (account_id, "card", str(item_id), edition, edition,
                     card_no, "", _now_utc()))
                self._conn.execute(
                    "UPDATE cl_editions SET issued = ? WHERE edition = ?",
                    (card_no, edition))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise CollectiblesError(E_CL_DUP, edition)
            except CollectiblesError:
                raise
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"cl_id": cur.lastrowid, "kind": "card", "edition": edition,
                "card_no": card_no, "cap": ed_cap}

    def buy_replay_right(self, account_id, event_ref, token_price, ref):
        """Purchase face for a chronicle highlight replay right: one
        token spend (the only token-domain touch in this module), the
        right is permanent, and a duplicate purchase is rejected BEFORE
        the spend so a rejected buy never charges."""
        event_ref = str(event_ref).strip()
        if not event_ref:
            raise CollectiblesError(E_CL_BAD_REF, "event ref required")
        if (not isinstance(token_price, int) or isinstance(token_price, bool)
                or token_price <= 0):
            raise CollectiblesError(E_CL_BAD_AMOUNT, str(token_price))
        if not str(ref).strip():
            raise CollectiblesError(E_CL_BAD_REF, "purchase ref required")
        if not account_id.startswith("usr:"):
            raise CollectiblesError(E_CL_BAD_REF, "purchases are usr:* only")
        with self._lock:
            row = self._conn.execute(
                "SELECT cl_id FROM collectibles"
                " WHERE account_id = ? AND kind = 'replay'"
                " AND event_ref = ?",
                (account_id, event_ref)).fetchone()
            if row is not None:
                raise CollectiblesError(E_CL_DUP, event_ref)
        self.led.ensure_account(account_id, census_avatar_id=account_id[4:])
        spend_tx = self.led.spend(account_id, token_price, str(ref), "order")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO collectibles (account_id, kind, item_id,"
                    " event_ref, edition, card_no, bound_spend_tx,"
                    " granted_utc) VALUES (?,?,?,?,?,?,?,?)",
                    (account_id, "replay", "replay:" + event_ref, event_ref,
                     None, None, spend_tx, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise CollectiblesError(E_CL_DUP, event_ref)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"spend_tx_id": spend_tx, "kind": "replay",
                "event_ref": event_ref}

    # -- read faces -----------------------------------------------------------

    def collection(self, account_id):
        """Per-account collection view: awarded certificates, numbered
        cards, purchased replay rights, each row carrying its
        provenance (event ref for awards and claims, spend tx for
        purchases)."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT kind, item_id, event_ref, edition, card_no,"
                " bound_spend_tx FROM collectibles WHERE account_id = ?"
                " ORDER BY cl_id", (account_id,)).fetchall()
        certificates = [{"item_id": r[1], "event_ref": r[2]}
                        for r in rows if r[0] == "certificate"]
        cards = [{"item_id": r[1], "edition": r[3], "card_no": int(r[4])}
                 for r in rows if r[0] == "card"]
        replays = [{"event_ref": r[2], "spend_tx": r[5]}
                   for r in rows if r[0] == "replay"]
        return {"account_id": account_id, "certificates": certificates,
                "cards": cards, "replays": replays}

    def edition_status(self, edition):
        """Read-only edition counter view (numbered claims vs cap)."""
        with self._lock:
            row = self._conn.execute(
                "SELECT cap, issued FROM cl_editions WHERE edition = ?",
                (edition,)).fetchone()
        if row is None:
            return {"edition": edition, "cap": None, "issued": 0}
        return {"edition": edition, "cap": int(row[0]), "issued": int(row[1])}
