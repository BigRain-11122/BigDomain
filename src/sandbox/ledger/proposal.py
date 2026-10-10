"""Resident proposal co-signature face (BigDomain R1766; canon =
explore-queue proposal line: proposal -> co-signature -> threshold
crossing triggers the collectibles memorial linkage; seed =
R-20260928-bigdomain-belonging-economy.md + collectibles.py R619).

Design verdicts (registered before the code, in the R1766
explore-queue row):

  - posture: the proposal title/body are resident free text, so
    the msgSecCheck pre-gate is mandatory on registration (the
    tmarket AC-TM2 law); a co-signature is a pure signature act
    with no free text, so no gate point exists there (the
    civicpoints earn precedent; a successor signature-note
    surface must wire a SecGate pre-gate first). The memorial
    award is a platform-side act - the honoree (the proposer)
    derives from the registration row, the civic-honor R1755
    posture, so no gate point exists on the award path either.
  - zero-token structure: co-signing is a civic act with no fee
    and zero token movement; the constructor takes NO ledger
    reference at all - the module is structurally unable to
    touch the token domain (the R599 counts-vs-tokens isolation
    law, elevated one step beyond civicpoints: zero ledger
    import, machine-checked in the suite).
  - derived qualification: "qualified" is derived at read time
    as signature_count >= threshold - zero stored state, zero
    UPDATE surface (the showcase display-state precedent).
  - memorial linkage: the crossing signature (exactly the
    threshold-th sign) awards the proposer one memorial
    certificate through the CollectiblesFace.issue_certificate
    public API (reference, never copied; event_ref namespace
    proposal-memorial:<id>); E_CL_DUP is internalized as
    idempotent (a platform pre-award does not double-issue, the
    festival AC-FE5 law). A constructor hasattr structure gate
    refuses an unwired collectibles face (honorcert AC-HC1).
  - caller-supplied parameters: threshold/window/memorial item_id
    are caller-supplied on each registration; production values
    are a [needs-CEO] batch - the shipped config.json is
    untouched.

Domains:

  - proposal registry: platform-registered resident proposals
    with title/body (SecGate pre-gated), a proposer (usr:*), an
    int-tick signature window (inclusive on both edges, the
    ads/venue/festival convention), and a co-signature
    threshold (>= 2);
  - co-signature ledger: append-only sign rows, one per
    (proposal, account) - re-sign rejected, proposer self-sign
    rejected, outside-window rejected (all before any row
    lands);
  - derived qualification + memorial: the crossing signature
    awards the proposer the memorial certificate; qualification
    itself stays a read-time derivation.

Hard laws:

  - append-only: sign/registration rows are INSERT-only; the
    module source carries zero UPDATE statements;
  - independent SQLite file (proposal.db, WAL, single writer) -
    zero collectibles-table direct writes (source-level scan:
    every .execute statement touches only this module's two
    tables), zero ledger-schema touch, so the schema fingerprint
    sentinel stays clean;
  - zero RNG, zero network imports, pure ASCII source.

AIGC labeling: registry rows carry a persistent ai_label (0/1,
DB CHECK) shown on every listing surface; a resident standing
disclaimer is required at construction and rides every envelope
(non-advisory law).

Pre-registered criteria AC-PP1..PP7 live in the R1766
explore-queue row and were written before this code existed
(honesty law).
"""

import datetime
import sqlite3
import threading

E_PP_BAD_ARGS = "E_PP_BAD_ARGS"            # AC-PP1 / AC-PP7
E_PP_DUP_PROPOSAL = "E_PP_DUP_PROPOSAL"    # AC-PP1
E_PP_UNKNOWN_PROPOSAL = "E_PP_UNKNOWN_PROPOSAL"  # AC-PP1 / AC-PP3
E_PP_CONTENT_REJECTED = "E_PP_CONTENT_REJECTED"  # AC-PP2
E_PP_GATE_ERROR = "E_PP_GATE_ERROR"        # AC-PP2 (runtime fault)
E_PP_NO_GATE = "E_PP_NO_GATE"              # AC-PP2 (unwired gate)
E_PP_NO_DISCLAIMER = "E_PP_NO_DISCLAIMER"  # AC-PP6
E_PP_WINDOW = "E_PP_WINDOW"                # AC-PP3
E_PP_DUP_SIGN = "E_PP_DUP_SIGN"            # AC-PP3
E_PP_SELF_SIGN = "E_PP_SELF_SIGN"          # AC-PP3

_CONTENT_REJECTED_CODE = "E_CONTENT_REJECTED"  # lobby SecGate hit
_CL_DUP_CODE = "E_CL_DUP"                       # collectibles dup award

_SCHEMA = """
CREATE TABLE IF NOT EXISTS proposals (
    proposal_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    proposer TEXT NOT NULL,
    start_tick INTEGER NOT NULL CHECK (start_tick >= 0),
    end_tick INTEGER NOT NULL CHECK (end_tick > start_tick),
    threshold INTEGER NOT NULL CHECK (threshold >= 2),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0,1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS proposal_signs (
    sign_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    at_tick INTEGER NOT NULL CHECK (at_tick >= 0),
    signed_utc TEXT NOT NULL,
    UNIQUE (proposal_id, account_id)
);
"""

_MEMORIAL_PREFIX = "proposal-memorial:"


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class ProposalError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class ProposalFace:
    """Resident proposal co-signature face. Own SQLite file, single
    writer; every mutation runs inside BEGIN IMMEDIATE. The content
    gate (lobby SecGate) and the collectibles face are injected by
    reference, never copied; a missing gate, an empty disclaimer or
    an unwired collectibles face refuses construction - no gate, no
    door. The constructor deliberately takes NO ledger reference:
    the token domain is structurally out of reach."""

    def __init__(self, collectibles, gate, disclaimer, db_path,
                 memorial_item_id="proposal-memorial"):
        if collectibles is None or not callable(
                getattr(collectibles, "issue_certificate", None)):
            raise ProposalError(E_PP_BAD_ARGS,
                                "collectibles face with"
                                " issue_certificate required")
        if not callable(getattr(gate, "check_text", None)):
            raise ProposalError(E_PP_NO_GATE, "content gate required")
        text = str(disclaimer or "").strip()
        if not text:
            raise ProposalError(E_PP_NO_DISCLAIMER,
                                "resident disclaimer required")
        if not str(memorial_item_id or "").strip():
            raise ProposalError(E_PP_BAD_ARGS, "memorial item id required")
        if not str(db_path or "").strip():
            raise ProposalError(E_PP_BAD_ARGS, "db path required")
        self.collectibles = collectibles
        self.gate = gate
        self.disclaimer = text
        self.memorial_item_id = str(memorial_item_id)
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

    def _gate_check(self, text):
        """Run the injected content gate. A wordlist hit maps to
        E_PP_CONTENT_REJECTED; ANY other failure (offline gate,
        runtime fault) maps to E_PP_GATE_ERROR - never a silent
        pass. Zero rows are stored on either path (AC-PP2)."""
        try:
            self.gate.check_text(text)
        except Exception as exc:  # noqa: BLE001 (fail-closed wrap)
            if getattr(exc, "code", None) == _CONTENT_REJECTED_CODE:
                raise ProposalError(E_PP_CONTENT_REJECTED,
                                   getattr(exc, "word", ""))
            raise ProposalError(E_PP_GATE_ERROR, str(exc))

    def _assert_account(self, account_id):
        if not isinstance(account_id, str) or not account_id.startswith(
                "usr:"):
            raise ProposalError(E_PP_BAD_ARGS, "accounts are usr:* only")
        return account_id

    def _load_proposal(self, proposal_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT title, body, proposer, start_tick, end_tick,"
                " threshold, ai_label FROM proposals"
                " WHERE proposal_id = ?", (proposal_id,)).fetchone()
        if row is None:
            raise ProposalError(E_PP_UNKNOWN_PROPOSAL, proposal_id)
        return row

    def _sign_count(self, proposal_id):
        return int(self._conn.execute(
            "SELECT COUNT(*) FROM proposal_signs"
            " WHERE proposal_id = ?", (proposal_id,)).fetchone()[0])

    # -- writer faces ----------------------------------------------------------

    def register_proposal(self, proposal_id, title, body, proposer,
                          start_tick, end_tick, threshold, ai_generated):
        """One registration row per proposal id; title and body pass
        the content gate BEFORE any row lands (fail-closed). The
        window is int-tick inclusive on both edges (the ads/venue
        convention); the threshold must be >= 2 (a petition of one
        is not a petition)."""
        proposal_id = str(proposal_id or "").strip()
        title = str(title or "").strip()
        body = str(body or "").strip()
        if not proposal_id:
            raise ProposalError(E_PP_BAD_ARGS, "proposal id required")
        if not title:
            raise ProposalError(E_PP_BAD_ARGS, "title required")
        if not body:
            raise ProposalError(E_PP_BAD_ARGS, "body required")
        proposer = self._assert_account(proposer)
        if (not isinstance(start_tick, int) or isinstance(start_tick, bool)
                or start_tick < 0):
            raise ProposalError(E_PP_BAD_ARGS,
                                "start tick must be int >= 0")
        if (not isinstance(end_tick, int) or isinstance(end_tick, bool)
                or end_tick <= start_tick):
            raise ProposalError(E_PP_BAD_ARGS,
                                "end tick must be int > start tick")
        if (not isinstance(threshold, int) or isinstance(threshold, bool)
                or threshold < 2):
            raise ProposalError(E_PP_BAD_ARGS,
                                "threshold must be int >= 2")
        if not isinstance(ai_generated, bool):
            raise ProposalError(E_PP_BAD_ARGS, "ai flag must be bool")
        self._gate_check(title)
        self._gate_check(body)
        now = _now_utc()
        with self._lock:
            row = self._conn.execute(
                "SELECT proposal_id FROM proposals"
                " WHERE proposal_id = ?", (proposal_id,)).fetchone()
            if row is not None:
                raise ProposalError(E_PP_DUP_PROPOSAL, proposal_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO proposals (proposal_id, title, body,"
                    " proposer, start_tick, end_tick, threshold,"
                    " ai_label, registered_utc) VALUES (?,?,?,?,?,?,?,?,?)",
                    (proposal_id, title, body, proposer, start_tick,
                     end_tick, threshold, 1 if ai_generated else 0, now))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ProposalError(E_PP_DUP_PROPOSAL, proposal_id)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"proposal_id": proposal_id, "title": title,
                "threshold": threshold,
                "window": [start_tick, end_tick],
                "signature_count": 0, "qualified": False,
                "ai_label": 1 if ai_generated else 0,
                "disclaimer": self.disclaimer}

    def sign_proposal(self, account_id, proposal_id, at_tick):
        """One append-only sign row per (proposal, account). Gate
        order: account shape, proposal known, tick shape, window
        (inclusive both edges), self-sign, duplicate - every
        rejection lands before any row. The crossing signature
        (count becomes exactly the threshold) awards the proposer
        the memorial certificate through the collectibles public
        API; E_CL_DUP internalizes as idempotent (a platform
        pre-award does not double-issue). Co-signing is a pure
        civic act: zero token movement (no ledger reference
        exists in this module at all)."""
        account_id = self._assert_account(account_id)
        proposal_id = str(proposal_id or "").strip()
        if not proposal_id:
            raise ProposalError(E_PP_BAD_ARGS, "proposal id required")
        if (not isinstance(at_tick, int) or isinstance(at_tick, bool)
                or at_tick < 0):
            raise ProposalError(E_PP_BAD_ARGS, "tick must be int >= 0")
        with self._lock:
            reg = self._conn.execute(
                "SELECT proposer, start_tick, end_tick, threshold,"
                " ai_label FROM proposals WHERE proposal_id = ?",
                (proposal_id,)).fetchone()
            if reg is None:
                raise ProposalError(E_PP_UNKNOWN_PROPOSAL, proposal_id)
            proposer, start_tick, end_tick, threshold, ai_label = (
                reg[0], int(reg[1]), int(reg[2]), int(reg[3]), int(reg[4]))
            if at_tick < start_tick or at_tick > end_tick:
                raise ProposalError(
                    E_PP_WINDOW,
                    "tick %d outside [%d,%d]" % (at_tick, start_tick,
                                                 end_tick))
            if account_id == proposer:
                raise ProposalError(E_PP_SELF_SIGN, account_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                dup = self._conn.execute(
                    "SELECT sign_id FROM proposal_signs WHERE"
                    " proposal_id = ? AND account_id = ?",
                    (proposal_id, account_id)).fetchone()
                if dup is not None:
                    raise ProposalError(E_PP_DUP_SIGN, account_id)
                now = _now_utc()
                self._conn.execute(
                    "INSERT INTO proposal_signs (proposal_id,"
                    " account_id, at_tick, signed_utc)"
                    " VALUES (?,?,?,?)",
                    (proposal_id, account_id, at_tick, now))
                count = self._sign_count(proposal_id)
                self._conn.execute("COMMIT")
            except ProposalError:
                self._conn.execute("ROLLBACK")
                raise
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        memorial = None
        if count == threshold:
            memorial = self._award_memorial(proposer, proposal_id)
        return {"proposal_id": proposal_id, "account_id": account_id,
                "signature_count": count, "threshold": threshold,
                "qualified": count >= threshold,
                "memorial": memorial,
                "ai_label": ai_label,
                "disclaimer": self.disclaimer}

    def _award_memorial(self, proposer, proposal_id):
        """Platform-side memorial award on the threshold crossing:
        exactly one certificate for the proposer per proposal
        (event_ref namespace proposal-memorial:<id>). E_CL_DUP is
        internalized as the idempotent 'already' path - a platform
        pre-award must not double-issue and must not fail the civic
        sign record (festival AC-FE5 law). The sign row already
        stands; the memorial is a platform decoration."""
        event_ref = _MEMORIAL_PREFIX + proposal_id
        try:
            self.collectibles.issue_certificate(
                proposer, event_ref, self.memorial_item_id)
            return "issued"
        except Exception as exc:  # noqa: BLE001 (fail-closed wrap)
            if getattr(exc, "code", None) == _CL_DUP_CODE:
                return "already"
            raise

    # -- read faces ------------------------------------------------------------

    def proposal_view(self, proposal_id):
        """Pure-read derivation: signature_count is a COUNT,
        qualified is derived (count >= threshold) with zero cached
        state - a new sign changes the next read (live derivation)."""
        proposal_id = str(proposal_id or "").strip()
        if not proposal_id:
            raise ProposalError(E_PP_BAD_ARGS, "proposal id required")
        with self._lock:
            reg = self._conn.execute(
                "SELECT title, body, proposer, start_tick, end_tick,"
                " threshold, ai_label FROM proposals"
                " WHERE proposal_id = ?", (proposal_id,)).fetchone()
            if reg is None:
                raise ProposalError(E_PP_UNKNOWN_PROPOSAL, proposal_id)
            count = self._sign_count(proposal_id)
            signs = self._conn.execute(
                "SELECT account_id, at_tick, signed_utc FROM"
                " proposal_signs WHERE proposal_id = ?"
                " ORDER BY sign_id", (proposal_id,)).fetchall()
        title, body, proposer, start_tick, end_tick, threshold, ai_label = (
            reg[0], reg[1], reg[2], int(reg[3]), int(reg[4]), int(reg[5]),
            int(reg[6]))
        return {"proposal_id": proposal_id, "title": title, "body": body,
                "proposer": proposer,
                "window": [start_tick, end_tick],
                "threshold": threshold,
                "signature_count": count,
                "qualified": count >= threshold,
                "signers": [{"account_id": r[0], "at_tick": int(r[1]),
                             "signed_utc": r[2]} for r in signs],
                "ai_label": ai_label,
                "disclaimer": self.disclaimer}

    def proposal_board(self):
        with self._lock:
            rows = self._conn.execute(
                "SELECT proposal_id, title, proposer, start_tick,"
                " end_tick, threshold, ai_label FROM proposals"
                " ORDER BY rowid").fetchall()
            counts = dict(self._conn.execute(
                "SELECT proposal_id, COUNT(*) FROM proposal_signs"
                " GROUP BY proposal_id").fetchall())
        board = []
        for r in rows:
            count = int(counts.get(r[0], 0))
            board.append({"proposal_id": r[0], "title": r[1],
                          "proposer": r[2], "window": [int(r[3]), int(r[4])],
                          "threshold": int(r[5]),
                          "signature_count": count,
                          "qualified": count >= int(r[5]),
                          "ai_label": int(r[6])})
        return {"proposals": board, "disclaimer": self.disclaimer}
