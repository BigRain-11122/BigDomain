"""Sister-city cross-city visit face over the token ledger +
settlement protocol sandbox (BigDomain R1696; canon = explore-queue
sister-city cross-city visit line: cross-city economy = visit
passes + cross-city commercial-district exposure, and the
cross-city settlement protocol is the settlement.py manifest face
referenced through its public API, never rebuilt here; seed =
BLUEPRINT section 12 group double-helix inter-city face).

Three domains ride on the P-47-2b token ledger:

  twins   : a platform-registered sister-city pairing spans an
            integer-tick window (the ads/venue schedule-window
            convention, inclusive on both edges, end strictly after
            start), carrying the visit-pass price, the cross-city
            exposure price and the pair-wide exposure slot count.
            Platform-side registry: no resident-authored text
            enters this module (the festival/ads platform-side
            posture - registration and purchases carry no free
            text, so no content gate is wired here; any future
            resident-text face built on this engine wires the
            SecGate pre-gate first). The declared AIGC label
            persists on the registry row and every view surfaces
            it.
  visits  : a resident buys the cross-city visit pass only while
            the twin window covers the purchase tick - one tick
            outside refuses fail-closed with zero charge
            (E_SC_WINDOW). Gates all BEFORE the spend: a same
            (buyer, ref) replay refuses (E_SC_DUP_PASS) and a
            second pass per (account, pair) refuses
            (E_SC_PASS_EXISTS - one visit pass per resident per
            pairing). Accepted = exactly one spend bound to its
            tx; the price paid is an immutable copy of the
            registered pass price.
  exposure: a home-city merchant books one cross-city district
            exposure line in the same window - the window gate,
            the same (merchant, ref) replay gate and the pair-wide
            slot cap all reject BEFORE the spend (zero charge,
            E_SC_EXPOSURE_FULL when every slot is taken); the
            accepted booking is exactly one spend bound to its tx.

settlement: the twin window's cross-city revenue (visit passes +
            exposure bookings, integer fen, zero rounding) settles
            through the SettlementFace public API (build_manifest
            + verify_manifest - the settlement protocol is
            referenced, this module builds zero second engine).
            One manifest per (pair, period), hash-chained by the
            protocol, persisted locally for audit with UNIQUE
            (pair, period) - a repeat settle refuses
            (E_SC_SETTLED). Parties and weights are caller-supplied
            sandbox parameters: production split ratios are a P1
            approval face ([needs-CEO]) and are never encoded here.

Rows are immutable once written (zero UPDATE surface: window,
replay, one-pass and slot enforcement read COUNT faces, they never
mutate counters). Counts stay counts and tokens stay tokens: the
only token-domain touch in this module is the one spend per
accepted purchase/booking.

Pre-registered criteria AC-SC1..AC-SC7 live in the R1696
explore-queue row and were written before this code existed
(honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: four extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

import settlement as ST                 # referenced protocol, not copied

E_SC_BAD_ARGS = "E_SC_BAD_ARGS"             # AC-SC2/AC-SC7
E_SC_BAD_ACCOUNT = "E_SC_BAD_ACCOUNT"       # AC-SC7
E_SC_BAD_PRICE = "E_SC_BAD_PRICE"           # AC-SC1/AC-SC7
E_SC_BAD_TWIN = "E_SC_BAD_TWIN"             # AC-SC1/AC-SC7
E_SC_DUP_TWIN = "E_SC_DUP_TWIN"             # AC-SC1
E_SC_UNKNOWN_TWIN = "E_SC_UNKNOWN_TWIN"     # AC-SC2/AC-SC6
E_SC_WINDOW = "E_SC_WINDOW"                 # AC-SC2/AC-SC3 (window gate)
E_SC_DUP_PASS = "E_SC_DUP_PASS"             # AC-SC2 (ref replay)
E_SC_PASS_EXISTS = "E_SC_PASS_EXISTS"       # AC-SC2 (one pass per pair)
E_SC_DUP_EXPOSURE = "E_SC_DUP_EXPOSURE"     # AC-SC3 (ref replay)
E_SC_EXPOSURE_FULL = "E_SC_EXPOSURE_FULL"   # AC-SC3 (slot cap)
E_SC_SETTLED = "E_SC_SETTLED"               # AC-SC4 (period idempotent)
E_SC_BAD_PARTIES = "E_SC_BAD_PARTIES"       # AC-SC4/AC-SC7
E_SC_NO_DISCLAIMER = "E_SC_NO_DISCLAIMER"   # AC-SC5

_SCHEMA = """
CREATE TABLE IF NOT EXISTS twin_registry (
    pair_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair_key TEXT NOT NULL UNIQUE,
    home_city TEXT NOT NULL,
    sister_city TEXT NOT NULL,
    start_window INTEGER NOT NULL CHECK (start_window >= 0),
    end_window INTEGER NOT NULL CHECK (end_window > start_window),
    pass_price INTEGER NOT NULL CHECK (pass_price > 0),
    exposure_price INTEGER NOT NULL CHECK (exposure_price > 0),
    exposure_slots INTEGER NOT NULL CHECK (exposure_slots >= 1),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS twin_passes (
    pass_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    purchase_ref TEXT NOT NULL,
    price_paid INTEGER NOT NULL CHECK (price_paid > 0),
    spend_tx TEXT NOT NULL,
    pass_window INTEGER NOT NULL CHECK (pass_window >= 0),
    purchased_utc TEXT NOT NULL,
    UNIQUE (buyer_id, purchase_ref),
    UNIQUE (buyer_id, pair_id)
);
CREATE TABLE IF NOT EXISTS twin_exposures (
    exposure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair_id INTEGER NOT NULL,
    merchant_id TEXT NOT NULL,
    booking_ref TEXT NOT NULL,
    price_paid INTEGER NOT NULL CHECK (price_paid > 0),
    spend_tx TEXT NOT NULL,
    exposure_window INTEGER NOT NULL CHECK (exposure_window >= 0),
    booked_utc TEXT NOT NULL,
    UNIQUE (merchant_id, booking_ref)
);
CREATE TABLE IF NOT EXISTS twin_settlements (
    settle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair_id INTEGER NOT NULL,
    period TEXT NOT NULL,
    manifest_id TEXT NOT NULL,
    total_cent INTEGER NOT NULL CHECK (total_cent >= 0),
    manifest_json TEXT NOT NULL,
    settled_utc TEXT NOT NULL,
    UNIQUE (pair_id, period)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


class SisterCityError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class SisterCityFace:
    """Sister-city cross-city visit face over one Ledger. Own
    connection and lock for the twin tables; the cross-city
    settlement protocol is the settlement.SettlementFace public API
    held by reference (this module builds zero second engine). Every
    mutation runs inside BEGIN IMMEDIATE; rows are immutable once
    written. An empty disclaimer refuses construction - no
    disclaimer, no door."""

    def __init__(self, ledger, disclaimer):
        self.led = ledger
        text = str(disclaimer or "").strip()
        if not text:
            raise SisterCityError(E_SC_NO_DISCLAIMER,
                                  "resident disclaimer required")
        self.disclaimer = text
        self.db_path = ledger.db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        # the referenced settlement protocol engine (public API only)
        self.settlement = ST.SettlementFace()

    def close(self):
        with self._lock:
            self._conn.close()

    # -- twin registry domain ------------------------------------------------

    def register_twin(self, pair_key, home_city, sister_city,
                      start_window, end_window, pass_price,
                      exposure_price, exposure_slots, ai_generated):
        """Register one sister-city pairing: an integer-tick window
        (the ads/venue schedule convention, end strictly after
        start), a visit-pass price, a cross-city exposure price and
        the pair-wide exposure slot count. Exactly one row per
        pair_key - a repeat is rejected with zero rows (AC-SC1).
        The declared AIGC label persists on the row and every view
        surfaces it (AC-SC5)."""
        key = str(pair_key or "").strip()
        home = str(home_city or "").strip()
        sister = str(sister_city or "").strip()
        if not key:
            raise SisterCityError(E_SC_BAD_TWIN, "pair key required")
        if not home:
            raise SisterCityError(E_SC_BAD_TWIN, "home city required")
        if not sister:
            raise SisterCityError(E_SC_BAD_TWIN, "sister city required")
        if home == sister:
            raise SisterCityError(E_SC_BAD_TWIN,
                                  "home and sister must differ")
        if not _is_int(start_window) or start_window < 0:
            raise SisterCityError(E_SC_BAD_TWIN,
                                  "start_window must be int >= 0")
        if not _is_int(end_window) or end_window <= start_window:
            raise SisterCityError(E_SC_BAD_TWIN,
                                  "end_window must be > start_window")
        if not _is_int(pass_price) or pass_price <= 0:
            raise SisterCityError(E_SC_BAD_PRICE, str(pass_price))
        if not _is_int(exposure_price) or exposure_price <= 0:
            raise SisterCityError(E_SC_BAD_PRICE, str(exposure_price))
        if not _is_int(exposure_slots) or exposure_slots < 1:
            raise SisterCityError(E_SC_BAD_TWIN,
                                  "exposure_slots must be int >= 1")
        if not isinstance(ai_generated, bool):
            raise SisterCityError(E_SC_BAD_TWIN,
                                  "ai_generated must be bool")
        label = 1 if ai_generated else 0
        with self._lock:
            row = self._conn.execute(
                "SELECT pair_id FROM twin_registry WHERE pair_key = ?",
                (key,)).fetchone()
            if row is not None:
                raise SisterCityError(E_SC_DUP_TWIN, key)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO twin_registry (pair_key, home_city,"
                    " sister_city, start_window, end_window,"
                    " pass_price, exposure_price, exposure_slots,"
                    " ai_label, registered_utc)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (key, home, sister, start_window, end_window,
                     pass_price, exposure_price, exposure_slots, label,
                     _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise SisterCityError(E_SC_DUP_TWIN, key)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"pair_id": cur.lastrowid, "pair_key": key,
                "home_city": home, "sister_city": sister,
                "start_window": start_window, "end_window": end_window,
                "pass_price": pass_price,
                "exposure_price": exposure_price,
                "exposure_slots": exposure_slots, "ai_label": label}

    def _require_twin(self, pair_id):
        """Validation + lookup under no lock (caller holds it).
        Returns the full registry row."""
        if not _is_int(pair_id) or pair_id <= 0:
            raise SisterCityError(E_SC_BAD_ARGS, str(pair_id))
        row = self._conn.execute(
            "SELECT pair_id, pair_key, home_city, sister_city,"
            " start_window, end_window, pass_price, exposure_price,"
            " exposure_slots, ai_label FROM twin_registry"
            " WHERE pair_id = ?", (pair_id,)).fetchone()
        if row is None:
            raise SisterCityError(E_SC_UNKNOWN_TWIN, str(pair_id))
        return row

    def _window_gate(self, twin, at_window):
        """The ads/venue coverage gate: both edges inclusive, one
        tick outside refuses fail-closed with zero charge."""
        t_start, t_end = int(twin[4]), int(twin[5])
        if not (t_start <= at_window <= t_end):
            raise SisterCityError(
                E_SC_WINDOW, "%s: tick %d outside %d..%d"
                % (twin[1], at_window, t_start, t_end))

    # -- visit-pass domain -----------------------------------------------------

    def buy_visit_pass(self, buyer_id, pair_id, at_window, ref):
        """Buy the cross-city visit pass at one window tick. The
        twin window must cover the tick - both edges inclusive -
        and one tick outside refuses with zero charge (AC-SC2);
        the same-(buyer, ref) replay gate and the one-pass-per-
        (account, pair) gate both reject BEFORE the spend so a
        rejected buy never charges. Exactly one spend per pass,
        bound to its tx. Returns the provenance envelope with the
        declared AIGC label and the resident disclaimer (AC-SC5)."""
        if not str(buyer_id or "").startswith("usr:"):
            raise SisterCityError(E_SC_BAD_ACCOUNT, buyer_id)
        r = str(ref or "").strip()
        if not r:
            raise SisterCityError(E_SC_BAD_ARGS, "purchase ref required")
        if not _is_int(at_window) or at_window < 0:
            raise SisterCityError(E_SC_BAD_ARGS,
                                  "at_window must be int >= 0")
        with self._lock:
            twin = self._require_twin(pair_id)
            self._window_gate(twin, at_window)
            price = int(twin[6])
            row = self._conn.execute(
                "SELECT pass_id FROM twin_passes WHERE buyer_id = ?"
                " AND purchase_ref = ?", (buyer_id, r)).fetchone()
            if row is not None:
                raise SisterCityError(E_SC_DUP_PASS,
                                      "%s/%s" % (buyer_id, r))
            row = self._conn.execute(
                "SELECT pass_id FROM twin_passes WHERE buyer_id = ?"
                " AND pair_id = ?", (buyer_id, pair_id)).fetchone()
            if row is not None:
                raise SisterCityError(E_SC_PASS_EXISTS,
                                      "%s already holds a pass on %s"
                                      % (buyer_id, twin[1]))
            self.led.ensure_account(buyer_id,
                                    census_avatar_id=buyer_id[4:])
            spend_tx = self.led.spend(buyer_id, price, r, "order")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO twin_passes (pair_id, buyer_id,"
                    " purchase_ref, price_paid, spend_tx, pass_window,"
                    " purchased_utc) VALUES (?,?,?,?,?,?,?)",
                    (pair_id, buyer_id, r, price, spend_tx, at_window,
                     _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise SisterCityError(E_SC_DUP_PASS,
                                      "%s/%s" % (buyer_id, r))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"pass_id": cur.lastrowid, "pair_id": pair_id,
                "pair_key": twin[1], "buyer_id": buyer_id,
                "price_paid": price, "spend_tx": spend_tx,
                "pass_window": at_window, "ai_label": int(twin[9]),
                "disclaimer": self.disclaimer}

    # -- cross-city exposure domain --------------------------------------------

    def book_exposure(self, merchant_id, pair_id, at_window, ref):
        """Book one cross-city commercial-district exposure line
        for a home-city merchant inside the twin window: the window
        gate, the same (merchant, ref) replay gate and the pair-wide
        slot cap all reject BEFORE the spend - a rejected booking
        never charges (AC-SC3). Accepted = exactly one spend bound
        to its tx. Platform-side posture: no resident text enters
        this module."""
        if not str(merchant_id or "").startswith("usr:"):
            raise SisterCityError(E_SC_BAD_ACCOUNT, merchant_id)
        r = str(ref or "").strip()
        if not r:
            raise SisterCityError(E_SC_BAD_ARGS, "booking ref required")
        if not _is_int(at_window) or at_window < 0:
            raise SisterCityError(E_SC_BAD_ARGS,
                                  "at_window must be int >= 0")
        with self._lock:
            twin = self._require_twin(pair_id)
            self._window_gate(twin, at_window)
            slots = int(twin[8])
            price = int(twin[7])
            row = self._conn.execute(
                "SELECT exposure_id FROM twin_exposures"
                " WHERE merchant_id = ? AND booking_ref = ?",
                (merchant_id, r)).fetchone()
            if row is not None:
                raise SisterCityError(E_SC_DUP_EXPOSURE,
                                      "%s/%s" % (merchant_id, r))
            n_booked = self._conn.execute(
                "SELECT COUNT(*) FROM twin_exposures WHERE pair_id = ?",
                (pair_id,)).fetchone()[0]
            if n_booked >= slots:
                raise SisterCityError(
                    E_SC_EXPOSURE_FULL,
                    "%s exposure slots %d full" % (twin[1], slots))
            self.led.ensure_account(merchant_id,
                                    census_avatar_id=merchant_id[4:])
            spend_tx = self.led.spend(merchant_id, price, r, "order")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO twin_exposures (pair_id, merchant_id,"
                    " booking_ref, price_paid, spend_tx,"
                    " exposure_window, booked_utc)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (pair_id, merchant_id, r, price, spend_tx,
                     at_window, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise SisterCityError(E_SC_DUP_EXPOSURE,
                                      "%s/%s" % (merchant_id, r))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"exposure_id": cur.lastrowid, "pair_id": pair_id,
                "pair_key": twin[1], "merchant_id": merchant_id,
                "price_paid": price, "spend_tx": spend_tx,
                "exposure_window": at_window,
                "ai_label": int(twin[9]),
                "disclaimer": self.disclaimer}

    # -- cross-city settlement domain (referenced protocol) --------------------

    def _window_sales_rows(self, pair_id):
        """Gather the twin window's cross-city revenue rows: every
        visit-pass sale and every exposure booking, as integer-cent
        sales rows in the settlement manifest shape. Pure read."""
        passes = self._conn.execute(
            "SELECT price_paid FROM twin_passes WHERE pair_id = ?",
            (pair_id,)).fetchall()
        exposures = self._conn.execute(
            "SELECT price_paid FROM twin_exposures WHERE pair_id = ?",
            (pair_id,)).fetchall()
        return [{"amount_cent": int(r[0])} for r in passes + exposures]

    def settle_twin_window(self, pair_id, period, parties, weights):
        """Settle the twin window's cross-city revenue through the
        referenced SettlementFace public API: build_manifest
        (hash-chained, integer split, zero rounding loss) then
        verify_manifest on the returned manifest - the reference
        face end to end (AC-SC4). One manifest per (pair, period):
        a repeat settle refuses with zero rows. The manifest id is
        persisted locally for audit. Parties and weights are
        caller-supplied sandbox parameters - production split
        ratios are a P1 approval face ([needs-CEO])."""
        if not isinstance(period, str) or not str(period).strip():
            raise SisterCityError(E_SC_BAD_ARGS, "period required")
        period = str(period).strip()
        if not isinstance(parties, (list, tuple)) or not parties \
                or len(set(parties)) != len(parties):
            raise SisterCityError(E_SC_BAD_PARTIES,
                                  "parties must be a non-empty list"
                                  " of unique names")
        if not isinstance(weights, dict) or not weights:
            raise SisterCityError(E_SC_BAD_PARTIES,
                                  "weights must be a non-empty dict")
        parties = list(parties)
        with self._lock:
            twin = self._require_twin(pair_id)
            row = self._conn.execute(
                "SELECT settle_id FROM twin_settlements"
                " WHERE pair_id = ? AND period = ?",
                (pair_id, period)).fetchone()
            if row is not None:
                raise SisterCityError(E_SC_SETTLED,
                                      "%s/%s already settled"
                                      % (twin[1], period))
            sales_rows = self._window_sales_rows(pair_id)
            total = sum(int(r["amount_cent"]) for r in sales_rows)
            namespaced = "twin:%d/%s" % (pair_id, period)
            manifest = self.settlement.build_manifest(
                namespaced, sales_rows, [], parties,
                {name: weights.get(name) for name in parties})
            if not self.settlement.verify_manifest(
                    manifest, sales_rows, []):
                raise SisterCityError(E_SC_BAD_PARTIES,
                                      "manifest verify failed")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO twin_settlements (pair_id, period,"
                    " manifest_id, total_cent, manifest_json,"
                    " settled_utc) VALUES (?,?,?,?,?,?)",
                    (pair_id, period, manifest["id"], total,
                     ST.canonical(manifest), _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise SisterCityError(E_SC_SETTLED,
                                      "%s/%s already settled"
                                      % (twin[1], period))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        out = dict(manifest)
        out["pair_id"] = pair_id
        out["pair_key"] = twin[1]
        out["window_period"] = period
        out["sales_rows"] = len(sales_rows)
        out["disclaimer"] = self.disclaimer
        out["ai_label"] = int(twin[9])
        return out

    # -- read faces ---------------------------------------------------------------

    def twin_view(self, pair_id):
        """One pairing surface: window, prices, slot count,
        declared AIGC label, pass/exposure/participant counts; the
        envelope carries the resident non-advisory disclaimer
        (AC-SC5/AC-SC6). Pure read."""
        with self._lock:
            row = self._conn.execute(
                "SELECT pair_id, pair_key, home_city, sister_city,"
                " start_window, end_window, pass_price,"
                " exposure_price, exposure_slots, ai_label,"
                " registered_utc FROM twin_registry"
                " WHERE pair_id = ?", (pair_id,)).fetchone()
            if row is None:
                raise SisterCityError(E_SC_UNKNOWN_TWIN, str(pair_id))
            n_pass, n_people = self._conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT buyer_id) FROM"
                " twin_passes WHERE pair_id = ?", (pair_id,)).fetchone()
            n_exp, n_merchants = self._conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT merchant_id) FROM"
                " twin_exposures WHERE pair_id = ?",
                (pair_id,)).fetchone()
        return {"pair_id": int(row[0]), "pair_key": row[1],
                "home_city": row[2], "sister_city": row[3],
                "start_window": int(row[4]), "end_window": int(row[5]),
                "pass_price": int(row[6]),
                "exposure_price": int(row[7]),
                "exposure_slots": int(row[8]), "ai_label": int(row[9]),
                "registered_utc": row[10],
                "pass_count": int(n_pass),
                "pass_holder_count": int(n_people),
                "exposure_count": int(n_exp),
                "merchant_count": int(n_merchants),
                "disclaimer": self.disclaimer}

    def active_twins(self, at_window):
        """Schedule-window listing face: every pairing whose window
        covers at_window (inclusive on both edges - the ads/venue
        coverage convention), each row carrying its declared AIGC
        label; the envelope carries the resident disclaimer
        (AC-SC5/AC-SC6). Pure read, zero token movement."""
        if not _is_int(at_window) or at_window < 0:
            raise SisterCityError(E_SC_BAD_ARGS,
                                  "at_window must be int >= 0")
        with self._lock:
            rows = self._conn.execute(
                "SELECT pair_id, pair_key, home_city, sister_city,"
                " start_window, end_window, pass_price,"
                " exposure_price, ai_label FROM twin_registry"
                " WHERE start_window <= ? AND end_window >= ?"
                " ORDER BY pair_id", (at_window, at_window)).fetchall()
        return {"at_window": at_window,
                "disclaimer": self.disclaimer,
                "twins": [{"pair_id": int(r[0]), "pair_key": r[1],
                           "home_city": r[2], "sister_city": r[3],
                           "start_window": int(r[4]),
                           "end_window": int(r[5]),
                           "pass_price": int(r[6]),
                           "exposure_price": int(r[7]),
                           "ai_label": int(r[8])} for r in rows]}

    def twin_board(self, pair_id):
        """Per-pairing audit board: every visit-pass row and every
        exposure row with its buyer/merchant, immutable price copy,
        bound spend tx and window tick - the audit trail of the
        cross-city economy (AC-SC6). Pure read."""
        with self._lock:
            self._require_twin(pair_id)
            passes = self._conn.execute(
                "SELECT pass_id, buyer_id, price_paid, spend_tx,"
                " pass_window, purchased_utc FROM twin_passes"
                " WHERE pair_id = ? ORDER BY pass_id",
                (pair_id,)).fetchall()
            exposures = self._conn.execute(
                "SELECT exposure_id, merchant_id, price_paid,"
                " spend_tx, exposure_window, booked_utc FROM"
                " twin_exposures WHERE pair_id = ?"
                " ORDER BY exposure_id", (pair_id,)).fetchall()
        return {"pair_id": pair_id, "disclaimer": self.disclaimer,
                "passes": [{"pass_id": int(r[0]), "buyer_id": r[1],
                            "price_paid": int(r[2]), "spend_tx": r[3],
                            "pass_window": int(r[4]),
                            "purchased_utc": r[5]} for r in passes],
                "exposures": [{"exposure_id": int(r[0]),
                               "merchant_id": r[1],
                               "price_paid": int(r[2]),
                               "spend_tx": r[3],
                               "exposure_window": int(r[4]),
                               "booked_utc": r[5]} for r in exposures]}
