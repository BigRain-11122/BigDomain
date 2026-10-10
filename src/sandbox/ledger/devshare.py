"""Developer revenue-share gradient settlement face (BigDomain
explore-queue row, claimed round R1759; seeds = apidev.py R1700
developer-ecosystem face + incentive.py R600 band-gradient
allocator; criteria AC-DS1..AC-DS7 pre-registered in the explore
queue row before this code existed - honesty law).

Design rulings (recorded in the queue row before the code):

  1. structure reuse, not double-build: the whole gradient
     settlement chain (band walk, per-recipient collar, window
     budget with deterministic pro-rata integer scaling, window
     idempotence) is the IncentiveFace proper - this module
     composes one IncentiveFace instance and delegates every
     settlement to its public API. Zero gradient arithmetic is
     reimplemented here.
  2. window namespace isolation: this face maps every public
     window id to "devshare:" + window_id before delegating, so a
     devshare window and a UGC-incentive window with the same
     caller-facing id never collide in the shared
     incentive_windows idempotence table (cross-face window
     idempotence still holds through the same table).
  3. developer-registry gate: a payout recipient must be a
     registered developer - at least one key row visible through
     the DevKeyFace.dev_board public read face (reference not
     copy: this module never reads api_dev_keys directly). A
     non-developer rejects E_DS_NOT_DEV before any settlement
     movement.
  4. usage attribution intake: settle_from_usage derives each
     developer's contribution units by summing quota_used over
     the dev_board key rows (public read face, same source as the
     R1735 usage tallies), so the share tracks real metered API
     usage.
  5. read face: devshare_windows is a read-only dock (mode=ro
     URI connection, showcase collectibles-dock precedent) over
     the incentive_windows table, filtered to the devshare
     prefix. The method source carries zero write statements.
  6. platform-side posture: settlement actions carry zero
     resident free text, so there is no SecGate point here
     (festival/ads/showroom precedent); any future developer-
     text face wires the SecGate pre-gate first.
  7. every parameter VALUE is [needs-CEO]: the sandbox defaults
     below exist only to make the mechanism testable and ship
     into no config file.

Non-advisory standing note: this face settles platform revenue
shares, it does not price or advise anything; the constructor
refuses an empty disclaimer and every envelope carries it.

Stdlib only. Encoding discipline: this module stays pure ASCII.
Zero UPDATE, zero RNG, zero network imports.
"""

import sqlite3

from incentive import IncentiveFace, payout_for  # noqa: E402
# (structure reuse: the settlement chain is the incentive proper)

E_DS_BAD_ARGS = "E_DS_BAD_ARGS"
E_DS_NO_DISCLAIMER = "E_DS_NO_DISCLAIMER"
E_DS_NOT_DEV = "E_DS_NOT_DEV"
E_DS_NO_USAGE = "E_DS_NO_USAGE"

# Sandbox-only defaults ([needs-CEO] adoption face, AC-DS1).
#   bands : decreasing-marginal per-unit amounts (anti-farm
#           gradient, incentive law carried over).
#   collar: max payout for one developer in one window.
#   budget: max total payout for one window.
DEVSHARE_PARAMS = {
    "bands": [(10, 3), (20, 2), (10 ** 9, 1)],
    "collar": 90,
    "budget": 240,
}

_PREFIX = "devshare:"


class DevShareError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class DevShareFace:
    """Developer revenue-share settlement over one Ledger + one
    DevKeyFace, composed onto one IncentiveFace (structure reuse
    not double-build). All token movement happens inside the
    delegated IncentiveFace settlement (one share tx per
    developer out of pool:share through the ledger public API)."""

    def __init__(self, ledger, devkeys, disclaimer=None, params=None):
        if ledger is None or devkeys is None:
            raise DevShareError(E_DS_BAD_ARGS, "ledger and devkeys"
                                " faces are required")
        if not hasattr(devkeys, "dev_board"):
            raise DevShareError(E_DS_BAD_ARGS, "devkeys face must"
                                " expose dev_board")
        text = str(disclaimer or "").strip()
        if not text:
            raise DevShareError(E_DS_NO_DISCLAIMER, "disclaimer required")
        self.led = ledger
        self.devkeys = devkeys
        self.disclaimer = text
        self.params = dict(params or DEVSHARE_PARAMS)
        # structure reuse: the gradient settlement chain is the
        # IncentiveFace proper (AC-DS3); this face adds the
        # developer-ecosystem layers on top of it.
        self._incentive = IncentiveFace(ledger, self.params)
        self._dock = sqlite3.connect(
            "file:%s?mode=ro" % ledger.db_path, uri=True)

    def close(self):
        self._dock.close()
        self._incentive.close()

    # -- internal helpers ------------------------------------------

    def _is_registered_dev(self, dev_account):
        """Registry gate through the apidev public read face
        (AC-DS2): a developer is in-register when the board shows
        at least one key row. Zero direct api_dev_keys reads."""
        board = self.devkeys.dev_board(dev_account)
        return len(board.get("keys", [])) > 0

    def _settle(self, window_id, contributions):
        """Namespace-isolated delegation (AC-DS4): the public
        window id maps onto the devshare prefix before the
        incentive settlement, so UGC windows and devshare windows
        never collide in the shared idempotence table."""
        if not window_id or not isinstance(window_id, str):
            raise DevShareError(E_DS_BAD_ARGS, "window_id must be a"
                                " non-empty string")
        return self._incentive.settle_window(
            _PREFIX + window_id, list(contributions))

    # -- public faces ----------------------------------------------

    def settle_window(self, window_id, contributions):
        """Settle one window from explicit per-developer
        contributions (ordered list of (dev_account, units)).
        Every recipient passes the developer-registry gate first
        (AC-DS2); the gradient settlement itself is the incentive
        chain (AC-DS3); re-settling a settled window rejects
        through the shared idempotence table (AC-DS4) with zero
        ledger movement. Returns {window_id, paid, disclaimer}
        where paid is the ordered (dev_account, amount) list. An
        empty contribution list mirrors the incentive posture
        (E_INC_EMPTY out of the delegated face, zero movement)."""
        for account, _units in contributions:
            if not self._is_registered_dev(account):
                raise DevShareError(E_DS_NOT_DEV, str(account))
        paid = self._settle(window_id, contributions)
        return {"window_id": window_id, "paid": paid,
                "disclaimer": self.disclaimer}

    def settle_from_usage(self, window_id, dev_accounts):
        """Settle one window with contribution units derived from
        the developer boards' real quota usage (AC-DS5): each
        developer's units = sum of quota_used over their key rows
        (public read face, zero direct table reads). Developers
        with zero usage drop out of the list; an all-zero board
        rejects E_DS_NO_USAGE (nothing to settle, zero movement).
        The input order is the caller's contribution order."""
        if not dev_accounts or not isinstance(dev_accounts, (list, tuple)):
            raise DevShareError(E_DS_BAD_ARGS, "dev_accounts list"
                                " required")
        contributions = []
        for account in dev_accounts:
            board = self.devkeys.dev_board(account)
            units = sum(int(key.get("quota_used", 0))
                        for key in board.get("keys", []))
            if units > 0:
                contributions.append((account, units))
        if not contributions:
            raise DevShareError(E_DS_NO_USAGE, "no metered usage to"
                                " settle")
        paid = self._settle(window_id, contributions)
        return {"window_id": window_id, "paid": paid,
                "disclaimer": self.disclaimer}

    def devshare_windows(self):
        """Settled-window history read (AC-DS6): a read-only dock
        over the shared incentive_windows table filtered to the
        devshare prefix. The method stays a pure SELECT (the
        acceptance suite machine-checks this method's source for
        write statements); an empty history reads as an honest
        empty list. Envelope keys are exactly {windows,
        disclaimer}."""
        rows = self._dock.execute(
            "SELECT window_id, total_paid, settled_utc FROM"
            " incentive_windows WHERE window_id LIKE ?"
            " ORDER BY settled_utc, window_id",
            (_PREFIX + "%",)).fetchall()
        windows = [{"window_id": row[0][len(_PREFIX):],
                    "total_paid": int(row[1]),
                    "settled_utc": row[2]} for row in rows]
        return {"windows": windows, "disclaimer": self.disclaimer}


# Law exports for the acceptance suite (cross-checks read the
# incentive pure function through this module's import surface).
_GRADIENT_REF = payout_for
