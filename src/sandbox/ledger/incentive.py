"""UGC creator incentive gradient allocator over the token ledger
sandbox (BigDomain explore queue #3, claimed round R600).

Allocation-layer design source: docs/spec/incentive-agent-spec.md
(path-2 co-creation revenue share face). Every parameter VALUE there is
[needs-CEO] (AC-IP1 law); this module ships no parameter values into
any config file - the sandbox defaults below exist only to make the
mechanism testable, and adopting real values stays a P1 approval-only
item for CEO.

Mechanism face explored here: for one settlement window, given
per-creator contribution units, compute decreasing-marginal payouts
(banded anti-farm gradient), apply the per-creator window collar,
then the window budget cap with deterministic pro-rata integer
scaling (floor plus ordered remainder distribution - zero rounding
loss), and book each payout as exactly one 'share' tx out of
pool:share via the ledger public API. A settled window is idempotent:
re-settling the same window id is rejected with zero ledger movement.

Domain law (props.py R599 posture): payouts are one-way share grants;
no reverse-conversion verb exists anywhere in this module. Pure
functions are deterministic - no RNG anywhere.

Pre-registered criteria AC-IG1..AC-IG7 live in the R600 backlog row
and were written before this code existed (honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: one idempotence table in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_INC_WINDOW_DUP = "E_INC_WINDOW_DUP"      # AC-IG5
E_INC_EMPTY = "E_INC_EMPTY"
E_INC_BAD_UNITS = "E_INC_BAD_UNITS"
E_INC_BAD_ACCOUNT = "E_INC_BAD_ACCOUNT"   # creators must be usr:*
E_INC_DUP_CREATOR = "E_INC_DUP_CREATOR"
E_INC_BAD_PARAM = "E_INC_BAD_PARAM"

# Sandbox-only defaults ([needs-CEO] adoption face, AC-IG7):
#   bands : list of (band_width, per_unit_amount). Units walk the bands
#           in order; the per-unit amount never increases band over
#           band (decreasing-marginal anti-farm gradient).
#   collar: max payout for one creator in one window.
#   budget: max total payout for one window.
SANDBOX_PARAMS = {
    "bands": [(5, 10), (10, 5), (10 ** 9, 2)],
    "collar": 150,
    "budget": 400,
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS incentive_windows (
    window_id TEXT PRIMARY KEY,
    settled_utc TEXT NOT NULL,
    total_paid INTEGER NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class IncentiveError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


def payout_for(units, params=None):
    """Pure gradient function (AC-IG1). Walks the bands left to right;
    the total is monotone non-decreasing in units and the per-unit
    marginal amount never increases band over band."""
    p = params or SANDBOX_PARAMS
    if not isinstance(units, int) or isinstance(units, bool) or units < 0:
        raise IncentiveError(E_INC_BAD_UNITS, str(units))
    total = 0
    left = units
    for width, per_unit in p["bands"]:
        take = min(left, width)
        total += take * per_unit
        left -= take
        if left <= 0:
            break
    return total


class IncentiveFace:
    """Settlement-window gradient allocator over one Ledger instance.
    Every payout books through the ledger public API (a share entry
    out of pool:share); this face owns no token arithmetic of its
    own."""

    def __init__(self, ledger, params=None):
        self.led = ledger
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
        bands = p.get("bands")
        collar = p.get("collar")
        budget = p.get("budget")
        if (not isinstance(bands, list) or not bands
                or not isinstance(collar, int) or isinstance(collar, bool)
                or collar <= 0
                or not isinstance(budget, int) or isinstance(budget, bool)
                or budget <= 0):
            raise IncentiveError(E_INC_BAD_PARAM)
        prev = None
        for item in bands:
            if (not isinstance(item, (list, tuple)) or len(item) != 2
                    or not isinstance(item[0], int) or item[0] <= 0
                    or not isinstance(item[1], int) or item[1] <= 0
                    or (prev is not None and item[1] > prev)):
                raise IncentiveError(E_INC_BAD_PARAM)
            prev = item[1]

    def close(self):
        with self._lock:
            self._conn.close()

    def _window_seen(self, window_id):
        with self._lock:
            return self._conn.execute(
                "SELECT 1 FROM incentive_windows WHERE window_id = ?",
                (window_id,)).fetchone() is not None

    def settle_window(self, window_id, contributions):
        """Compute and book payouts for one settlement window.
        contributions: ordered list of (creator_account, units).
        Returns the list of (creator_account, amount) actually paid,
        in input order. Re-settling a settled window is rejected
        (AC-IG5) with zero ledger movement."""
        if not window_id or not isinstance(window_id, str):
            raise IncentiveError(E_INC_BAD_PARAM, str(window_id))
        if not contributions:
            raise IncentiveError(E_INC_EMPTY)
        seen = set()
        for account, units in contributions:
            if not isinstance(account, str) or not account.startswith("usr:"):
                raise IncentiveError(E_INC_BAD_ACCOUNT, str(account))
            if (not isinstance(units, int) or isinstance(units, bool)
                    or units <= 0):
                raise IncentiveError(E_INC_BAD_UNITS, str(units))
            if account in seen:
                raise IncentiveError(E_INC_DUP_CREATOR, account)
            seen.add(account)
        if self._window_seen(window_id):
            raise IncentiveError(E_INC_WINDOW_DUP, window_id)  # AC-IG5

        # raw gradient, then the per-creator collar (AC-IG1 + AC-IG2)
        raw = [(account, payout_for(units, self.params))
               for account, units in contributions]
        capped = [(account, min(amount, self.params["collar"]))
                  for account, amount in raw]

        # window budget cap, deterministic pro-rata integer scaling
        # (AC-IG3): floor first, then the remainder is distributed one
        # token at a time in input order - the landing total equals the
        # budget exactly, with zero rounding loss.
        budget = self.params["budget"]
        total = sum(amount for _, amount in capped)
        if total > budget:
            scaled = [(account, (amount * budget) // total)
                      for account, amount in capped]
            remainder = budget - sum(amount for _, amount in scaled)
            idx = 0
            while remainder > 0 and scaled:
                slot = idx % len(scaled)
                account, amount = scaled[slot]
                scaled[slot] = (account, amount + 1)
                remainder -= 1
                idx += 1
            capped = scaled

        # book each payout: exactly one share tx per creator (AC-IG4)
        paid = []
        for account, amount in capped:
            if amount <= 0:
                continue
            ref = "incentive:%s:%s" % (window_id, account)
            self.led.share_from_pool("pool:share", account, amount, ref,
                                     ref_type="settlement",
                                     action="incentive_share")
            paid.append((account, amount))
        total_paid = sum(amount for _, amount in paid)
        with self._lock:
            self._conn.execute(
                "INSERT INTO incentive_windows"
                " (window_id, settled_utc, total_paid) VALUES (?, ?, ?)",
                (window_id, _now_utc(), total_paid))
            self._conn.commit()
        return paid
