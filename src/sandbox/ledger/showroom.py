"""Enterprise-showroom SaaS package face over the venue + ads
sandbox products (BigDomain R1695; canon = explore-queue
enterprise-showroom SaaS row: the annual enterprise showroom
package bundles three components - an exclusive showroom
storefront lease + a share of the QUANT giant-screen carousel
rotation + a stop on the city visitor-tour circuits - riding the
B3 schedule-window structure (R622 ads face / R605 venue face,
both referenced, never copied).

Compliance first (the Advertising Law Article-56 self-check the
canon row requires): the platform books showcase space for
commercial enterprises, so the platform stands in the
ad-publisher posture of Article 56 - joint liability for
false ads on life/health goods, knew-or-should-have-known
liability for the rest. Three structural consequences, all
inside this face: (1) enterprise advertiser qualification
verification (business license / advertiser identity) is a
bootstrap-window verification gate, [needs-CEO]; (2) zero
resident- or enterprise-authored text enters this module (the
festival/ads/collectibles platform-side posture - package
registration is platform copy and a subscription carries only
an account, a package key and a purchase reference, so no
content gate is wired here; any future enterprise-content face
built on this engine wires the SecGate pre-gate first, the
companion/tmarket posture); (3) the resident non-advisory
disclaimer rides every envelope, refusing construction when
empty.

Three domains ride on the P-47-2b token ledger:

  packages: a platform-registered annual showroom package
            declares the two fee rails (lease term x per-window
            price, rotation windows x per-window price) and the
            tour-circuit count. Exactly one row per package key;
            the declared AIGC label persists and every view
            surfaces it. An optional package-wide subscriber cap
            (None = uncapped) is the SaaS scarcity gate.
  bundle  : one subscription grants the bundle through the
            PUBLIC APIs of the two referenced products - the
            lease component goes through VenueFace
            .lease_storefront (the per-enterprise showroom unit
            showroom:<pkg>:<ent>, auto-registered, exclusive)
            and the rotation component goes through AdsFace.book
            (the quant_screen_carousel slot on the package's
            declared screen). Each component is exactly one
            spend bound to its tx (the venue/ads products ARE
            the fee rails, the identity/ads precedent); the
            annual package cost is the sum of the two declared
            component fees. Every gate (replay, active-contract,
            subscriber cap, rotation-slot pre-read) rejects
            BEFORE the first spend so a rejected subscription
            never charges; the module writes zero rows into the
            venue/ads tables (no second engine).
  tours   : the visitor-tour component is local: each contract
            gets exactly one stop per circuit 1..N with a
            deterministic position (subscription order inside
            the package). Zero token movement - the stop rides
            the bundle the two spends already paid for.

Rows are immutable once written (zero UPDATE surface: cap and
pre-read enforcement are COUNT/SELECT faces). Counts stay counts
and tokens stay tokens.

Every production parameter value (lease prices, rotation prices,
subscriber caps, tour-circuit counts) is a P1 item for CEO,
approval-only ([needs-CEO]). No config keys are added by this
module.

Pre-registered criteria AC-SR1..AC-SR7 live in the R1695
explore-queue row and were written before this code existed
(honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: two extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_SR_BAD_ARGS = "E_SR_BAD_ARGS"               # AC-SR3 / AC-SR5 / AC-SR7
E_SR_BAD_ACCOUNT = "E_SR_BAD_ACCOUNT"          # AC-SR7
E_SR_BAD_PKG = "E_SR_BAD_PKG"                  # AC-SR1
E_SR_DUP_PKG = "E_SR_DUP_PKG"                  # AC-SR1
E_SR_UNKNOWN_PKG = "E_SR_UNKNOWN_PKG"           # AC-SR3 / AC-SR7
E_SR_DUP_SUB = "E_SR_DUP_SUB"                  # AC-SR3 (ref replay)
E_SR_ACTIVE_CONTRACT = "E_SR_ACTIVE_CONTRACT"   # AC-SR3 (overlap gate)
E_SR_SOLD_OUT = "E_SR_SOLD_OUT"               # AC-SR4 (subscriber cap)
E_SR_ROTATION_FULL = "E_SR_ROTATION_FULL"       # AC-SR4 (pre-read gate)
E_SR_ROTATION_UNIT = "E_SR_ROTATION_UNIT"       # AC-SR4 (unit wiring)
E_SR_NO_DISCLAIMER = "E_SR_NO_DISCLAIMER"      # AC-SR6
E_SR_NO_VENUE = "E_SR_NO_VENUE"                # AC-SR6 (wiring gate)
E_SR_NO_ADS = "E_SR_NO_ADS"                    # AC-SR6 (wiring gate)
E_SR_UNKNOWN_CONTRACT = "E_SR_UNKNOWN_CONTRACT"  # AC-SR7

_SCHEMA = """
CREATE TABLE IF NOT EXISTS showroom_packages (
    pkg_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pkg_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    lease_term_windows INTEGER NOT NULL CHECK (lease_term_windows >= 1),
    lease_price_per_window INTEGER NOT NULL
        CHECK (lease_price_per_window > 0),
    rotation_unit TEXT NOT NULL,
    rotation_windows INTEGER NOT NULL CHECK (rotation_windows >= 1),
    rotation_price_per_window INTEGER NOT NULL
        CHECK (rotation_price_per_window > 0),
    tour_circuits INTEGER NOT NULL CHECK (tour_circuits >= 1),
    subscriber_cap INTEGER CHECK (subscriber_cap IS NULL
                                  OR subscriber_cap >= 1),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS showroom_contracts (
    contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pkg_id INTEGER NOT NULL,
    enterprise_id TEXT NOT NULL,
    contract_ref TEXT NOT NULL,
    start_tick INTEGER NOT NULL CHECK (start_tick >= 0),
    lease_end_tick INTEGER NOT NULL CHECK (lease_end_tick >= start_tick),
    lease_unit TEXT NOT NULL,
    rotation_unit TEXT NOT NULL,
    lease_fee INTEGER NOT NULL CHECK (lease_fee > 0),
    rotation_fee INTEGER NOT NULL CHECK (rotation_fee > 0),
    lease_spend_tx TEXT NOT NULL,
    rotation_spend_tx TEXT NOT NULL,
    subscribed_utc TEXT NOT NULL,
    UNIQUE (enterprise_id, contract_ref)
);
CREATE TABLE IF NOT EXISTS showroom_tour_stops (
    stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    pkg_id INTEGER NOT NULL,
    circuit_no INTEGER NOT NULL CHECK (circuit_no >= 1),
    stop_position INTEGER NOT NULL CHECK (stop_position >= 1),
    created_utc TEXT NOT NULL,
    UNIQUE (contract_id, circuit_no)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


class ShowroomError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class ShowroomFace:
    """Enterprise-showroom SaaS face over one Ledger, one VenueFace
    and one AdsFace sharing the same DB file. Own connection and
    lock for the package/contract/tour tables; the two bundle
    components are granted ONLY through the venue/ads public APIs
    (reference law - never a second venue or ads engine here);
    cross-product reads (rotation capacity, carousel occupancy)
    are plain SQL reads, the ads-face precedent. Every gate
    rejects before the first spend; rows are immutable once
    written. A missing venue/ads face or an empty disclaimer
    refuses construction - no rails, no door; no disclaimer, no
    door."""

    def __init__(self, ledger, venue, ads, disclaimer):
        self.led = ledger
        if (venue is None or not callable(
                getattr(venue, "lease_storefront", None))
                or getattr(venue, "db_path", None) != ledger.db_path):
            raise ShowroomError(E_SR_NO_VENUE, "venue face required")
        if (ads is None or not callable(getattr(ads, "book", None))
                or not callable(getattr(ads, "carousel_lineup", None))
                or getattr(getattr(ads, "ven", None), "db_path", None)
                != ledger.db_path):
            raise ShowroomError(E_SR_NO_ADS, "ads face required")
        self.ven = venue
        self.adz = ads
        text = str(disclaimer or "").strip()
        if not text:
            raise ShowroomError(E_SR_NO_DISCLAIMER,
                                "resident disclaimer required")
        self.disclaimer = text
        self.db_path = ledger.db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- package registry domain --------------------------------------------

    def register_package(self, pkg_key, title, lease_term_windows,
                         lease_price_per_window, rotation_unit,
                         rotation_windows, rotation_price_per_window,
                         tour_circuits, ai_generated, subscriber_cap=None):
        """Register one annual showroom package: the two declared fee
        rails (lease term x price, rotation windows x price), the
        tour-circuit count and an optional package-wide subscriber
        cap (None = uncapped). Exactly one row per pkg_key - a
        repeat is rejected with zero rows (AC-SR1). The declared
        AIGC label persists on the row and every view surfaces it
        (AC-SR6)."""
        key = str(pkg_key or "").strip()
        if not key:
            raise ShowroomError(E_SR_BAD_PKG, "package key required")
        if not str(title or "").strip():
            raise ShowroomError(E_SR_BAD_PKG, "title required")
        if not _is_int(lease_term_windows) or lease_term_windows < 1:
            raise ShowroomError(E_SR_BAD_PKG,
                                "lease_term_windows must be int >= 1")
        if (not _is_int(lease_price_per_window)
                or lease_price_per_window <= 0):
            raise ShowroomError(E_SR_BAD_PKG, str(lease_price_per_window))
        unit = str(rotation_unit or "").strip()
        if not unit:
            raise ShowroomError(E_SR_BAD_PKG, "rotation_unit required")
        if not _is_int(rotation_windows) or rotation_windows < 1:
            raise ShowroomError(E_SR_BAD_PKG,
                                "rotation_windows must be int >= 1")
        if (not _is_int(rotation_price_per_window)
                or rotation_price_per_window <= 0):
            raise ShowroomError(E_SR_BAD_PKG,
                                str(rotation_price_per_window))
        if not _is_int(tour_circuits) or tour_circuits < 1:
            raise ShowroomError(E_SR_BAD_PKG,
                                "tour_circuits must be int >= 1")
        if (subscriber_cap is not None
                and (not _is_int(subscriber_cap) or subscriber_cap < 1)):
            raise ShowroomError(E_SR_BAD_PKG,
                                "subscriber_cap must be int >= 1 or None")
        if not isinstance(ai_generated, bool):
            raise ShowroomError(E_SR_BAD_PKG, "ai_generated must be bool")
        label = 1 if ai_generated else 0
        with self._lock:
            row = self._conn.execute(
                "SELECT pkg_id FROM showroom_packages WHERE pkg_key = ?",
                (key,)).fetchone()
            if row is not None:
                raise ShowroomError(E_SR_DUP_PKG, key)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO showroom_packages (pkg_key, title,"
                    " lease_term_windows, lease_price_per_window,"
                    " rotation_unit, rotation_windows,"
                    " rotation_price_per_window, tour_circuits,"
                    " subscriber_cap, ai_label, registered_utc)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (key, str(title), lease_term_windows,
                     lease_price_per_window, unit, rotation_windows,
                     rotation_price_per_window, tour_circuits,
                     subscriber_cap, label, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ShowroomError(E_SR_DUP_PKG, key)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"pkg_id": cur.lastrowid, "pkg_key": key,
                "title": str(title),
                "lease_term_windows": lease_term_windows,
                "lease_price_per_window": lease_price_per_window,
                "rotation_unit": unit,
                "rotation_windows": rotation_windows,
                "rotation_price_per_window": rotation_price_per_window,
                "tour_circuits": tour_circuits,
                "subscriber_cap": subscriber_cap, "ai_label": label}

    def _require_pkg(self, pkg_id):
        """Validation + lookup under no lock (caller holds it).
        Returns the full package row."""
        if not _is_int(pkg_id) or pkg_id <= 0:
            raise ShowroomError(E_SR_BAD_ARGS, str(pkg_id))
        row = self._conn.execute(
            "SELECT pkg_id, pkg_key, lease_term_windows,"
            " lease_price_per_window, rotation_unit, rotation_windows,"
            " rotation_price_per_window, tour_circuits, subscriber_cap,"
            " ai_label FROM showroom_packages WHERE pkg_id = ?",
            (pkg_id,)).fetchone()
        if row is None:
            raise ShowroomError(E_SR_UNKNOWN_PKG, str(pkg_id))
        return row

    # -- bundle domain ---------------------------------------------------------

    def _rotation_slot_free(self, unit, start_tick, end_tick):
        """Cross-product READ (the ads-face precedent for reading the
        shared occupancy table): the rotation unit must be registered
        as a quant_screen_carousel and its capacity must exceed the
        bookings still effective inside the window. A terminated
        booking stops counting from terminated_tick + 1 (the venue
        effective-end semantics). Returns capacity when a slot is
        free; raises E_SR_ROTATION_FULL / E_SR_ROTATION_UNIT
        otherwise. Pure read, zero token movement."""
        row = self._conn.execute(
            "SELECT ad_kind, capacity FROM ad_units WHERE unit_id = ?",
            (unit,)).fetchone()
        if row is None or row[0] != "quant_screen_carousel":
            raise ShowroomError(E_SR_ROTATION_UNIT, unit)
        capacity = int(row[1])
        occ = self._conn.execute(
            "SELECT start_tick, end_tick, terminated_tick"
            " FROM venue_occupancy WHERE kind = 'venue' AND unit_id = ?",
            (unit,)).fetchall()
        active = 0
        for r_start, r_end, r_term in occ:
            eff = r_end if r_term is None else min(r_end, r_term)
            if eff >= start_tick and r_start <= end_tick:
                active += 1
        if active >= capacity:
            raise ShowroomError(E_SR_ROTATION_FULL,
                                "%s: %d/%d slots taken in window"
                                % (unit, active, capacity))
        return capacity

    def subscribe_enterprise(self, enterprise_id, pkg_key, start_tick, ref):
        """Subscribe one enterprise to the annual showroom package:
        the bundle is granted through the venue and ads public APIs
        - the lease component books the per-enterprise showroom
        storefront (one spend) and the rotation component books the
        package's carousel slot (one spend) - then the contract row
        binds both spend txs and the tour stops are laid out (one
        stop per circuit, zero token movement). Every gate (replay,
        active-contract overlap, subscriber cap, rotation-slot
        pre-read) rejects BEFORE the first spend, so a rejected
        subscription never charges (AC-SR2/3/4). Returns the full
        provenance envelope with the declared AIGC label and the
        resident disclaimer (AC-SR6)."""
        if not str(enterprise_id or "").startswith("usr:"):
            raise ShowroomError(E_SR_BAD_ACCOUNT, enterprise_id)
        key = str(pkg_key or "").strip()
        if not key:
            raise ShowroomError(E_SR_BAD_ARGS, "pkg_key required")
        r = str(ref or "").strip()
        if not r:
            raise ShowroomError(E_SR_BAD_ARGS, "subscription ref required")
        if not _is_int(start_tick) or start_tick < 0:
            raise ShowroomError(E_SR_BAD_ARGS, "start_tick must be"
                                                   " int >= 0")
        with self._lock:
            prow = self._conn.execute(
                "SELECT pkg_id, lease_term_windows,"
                " lease_price_per_window, rotation_unit,"
                " rotation_windows, rotation_price_per_window,"
                " tour_circuits, subscriber_cap, ai_label"
                " FROM showroom_packages WHERE pkg_key = ?",
                (key,)).fetchone()
            if prow is None:
                raise ShowroomError(E_SR_UNKNOWN_PKG, key)
            (pkg_id, term, lease_price, rot_unit, rot_windows,
             rot_price, circuits, cap, ai_label) = prow
            term, lease_price = int(term), int(lease_price)
            rot_windows, rot_price = int(rot_windows), int(rot_price)
            circuits = int(circuits)
            lease_end = start_tick + term - 1
            dup = self._conn.execute(
                "SELECT contract_id FROM showroom_contracts"
                " WHERE enterprise_id = ? AND contract_ref = ?",
                (enterprise_id, r)).fetchone()
            if dup is not None:
                raise ShowroomError(E_SR_DUP_SUB,
                                    "%s/%s" % (enterprise_id, r))
            overlap = self._conn.execute(
                "SELECT COUNT(*) FROM showroom_contracts"
                " WHERE pkg_id = ? AND enterprise_id = ?"
                " AND start_tick <= ? AND lease_end_tick >= ?",
                (pkg_id, enterprise_id, lease_end, start_tick)
                ).fetchone()[0]
            if overlap:
                raise ShowroomError(
                    E_SR_ACTIVE_CONTRACT,
                    "%s already holds an overlapping contract on %s"
                    % (enterprise_id, key))
            if cap is not None:
                n_all = self._conn.execute(
                    "SELECT COUNT(*) FROM showroom_contracts"
                    " WHERE pkg_id = ?", (pkg_id,)).fetchone()[0]
                if n_all >= int(cap):
                    raise ShowroomError(E_SR_SOLD_OUT,
                                        "%s cap %d reached"
                                        % (key, cap))
            self._rotation_slot_free(rot_unit, start_tick,
                                      start_tick + rot_windows - 1)
        lease_unit = "showroom:%s:%s" % (key, enterprise_id)
        lease = self.ven.lease_storefront(enterprise_id, lease_unit,
                                          start_tick, term, lease_price,
                                          r + ":lease")
        rot = self.adz.book(enterprise_id, rot_unit, start_tick,
                            rot_windows, rot_price, r + ":ads")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO showroom_contracts (pkg_id,"
                    " enterprise_id, contract_ref, start_tick,"
                    " lease_end_tick, lease_unit, rotation_unit,"
                    " lease_fee, rotation_fee, lease_spend_tx,"
                    " rotation_spend_tx, subscribed_utc)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (pkg_id, enterprise_id, r, start_tick, lease_end,
                     lease_unit, rot_unit, lease["fee"], rot["fee"],
                     lease["spend_tx_id"], rot["spend_tx"], _now_utc()))
                contract_id = cur.lastrowid
                for circuit_no in range(1, circuits + 1):
                    position = self._conn.execute(
                        "SELECT COUNT(*) FROM showroom_tour_stops"
                        " WHERE pkg_id = ? AND circuit_no = ?",
                        (pkg_id, circuit_no)).fetchone()[0] + 1
                    self._conn.execute(
                        "INSERT INTO showroom_tour_stops (contract_id,"
                        " pkg_id, circuit_no, stop_position,"
                        " created_utc) VALUES (?,?,?,?,?)",
                        (contract_id, pkg_id, circuit_no, position,
                         _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ShowroomError(E_SR_DUP_SUB,
                                    "%s/%s" % (enterprise_id, r))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"contract_id": contract_id, "pkg_id": pkg_id,
                "pkg_key": key, "enterprise_id": enterprise_id,
                "contract_ref": r, "start_tick": start_tick,
                "lease_end_tick": lease_end, "lease_unit": lease_unit,
                "rotation_unit": rot_unit,
                "lease_fee": lease["fee"], "rotation_fee": rot["fee"],
                "lease_spend_tx": lease["spend_tx_id"],
                "rotation_spend_tx": rot["spend_tx"],
                "tour_circuits": circuits, "ai_label": int(ai_label),
                "disclaimer": self.disclaimer}

    # -- read faces -----------------------------------------------------------

    def package_view(self, pkg_id):
        """One package surface: the two declared fee rails, the
        tour-circuit count, the optional cap, the declared AIGC
        label and the contract counts; the envelope carries the
        resident non-advisory disclaimer (AC-SR6). Pure read."""
        if not _is_int(pkg_id) or pkg_id <= 0:
            raise ShowroomError(E_SR_BAD_ARGS, str(pkg_id))
        with self._lock:
            row = self._conn.execute(
                "SELECT pkg_id, pkg_key, title, lease_term_windows,"
                " lease_price_per_window, rotation_unit,"
                " rotation_windows, rotation_price_per_window,"
                " tour_circuits, subscriber_cap, ai_label,"
                " registered_utc FROM showroom_packages"
                " WHERE pkg_id = ?", (pkg_id,)).fetchone()
            if row is None:
                raise ShowroomError(E_SR_UNKNOWN_PKG, str(pkg_id))
            n_contracts, n_ent = self._conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT enterprise_id)"
                " FROM showroom_contracts WHERE pkg_id = ?",
                (pkg_id,)).fetchone()
        return {"pkg_id": int(row[0]), "pkg_key": row[1], "title": row[2],
                "lease_term_windows": int(row[3]),
                "lease_price_per_window": int(row[4]),
                "rotation_unit": row[5],
                "rotation_windows": int(row[6]),
                "rotation_price_per_window": int(row[7]),
                "tour_circuits": int(row[8]),
                "subscriber_cap": None if row[9] is None else int(row[9]),
                "ai_label": int(row[10]), "registered_utc": row[11],
                "contract_count": int(n_contracts),
                "enterprise_count": int(n_ent),
                "disclaimer": self.disclaimer}

    def showroom_lineup(self, pkg_id, at_tick):
        """Who-is-showing face: the package's contracts whose lease
        window covers at_tick (both edges inclusive), each row
        carrying its spans and declared AIGC label; the envelope
        carries the resident disclaimer (AC-SR6). Pure read, zero
        token movement."""
        if not _is_int(at_tick) or at_tick < 0:
            raise ShowroomError(E_SR_BAD_ARGS, "at_tick must be int >= 0")
        with self._lock:
            self._require_pkg(pkg_id)
            rows = self._conn.execute(
                "SELECT c.contract_id, c.enterprise_id, c.contract_ref,"
                " c.start_tick, c.lease_end_tick, c.lease_spend_tx,"
                " c.rotation_spend_tx, p.ai_label"
                " FROM showroom_contracts c JOIN showroom_packages p"
                " ON p.pkg_id = c.pkg_id"
                " WHERE c.pkg_id = ? AND c.start_tick <= ?"
                " AND c.lease_end_tick >= ? ORDER BY c.contract_id",
                (pkg_id, at_tick, at_tick)).fetchall()
        return {"pkg_id": pkg_id, "at_tick": at_tick,
                "disclaimer": self.disclaimer,
                "contracts": [{"contract_id": int(r[0]),
                               "enterprise_id": r[1],
                               "contract_ref": r[2],
                               "start_tick": int(r[3]),
                               "lease_end_tick": int(r[4]),
                               "lease_spend_tx": r[5],
                               "rotation_spend_tx": r[6],
                               "ai_label": int(r[7])} for r in rows]}

    def tour_itinerary(self, pkg_id, circuit_no):
        """Visitor-tour itinerary of one package circuit: the stops
        in deterministic position order (subscription order), each
        with its enterprise and contract reference (AC-SR5). Pure
        read, zero token movement."""
        if not _is_int(circuit_no) or circuit_no < 1:
            raise ShowroomError(E_SR_BAD_ARGS,
                                "circuit_no must be int >= 1")
        with self._lock:
            pkg = self._require_pkg(pkg_id)
            if circuit_no > int(pkg[7]):
                raise ShowroomError(E_SR_BAD_ARGS,
                                    "circuit_no %d beyond tour_circuits %d"
                                    % (circuit_no, int(pkg[7])))
            rows = self._conn.execute(
                "SELECT s.stop_position, c.enterprise_id, c.contract_ref,"
                " s.contract_id FROM showroom_tour_stops s"
                " JOIN showroom_contracts c"
                " ON c.contract_id = s.contract_id"
                " WHERE s.pkg_id = ? AND s.circuit_no = ?"
                " ORDER BY s.stop_position", (pkg_id, circuit_no)
                ).fetchall()
        return {"pkg_id": pkg_id, "circuit_no": circuit_no,
                "disclaimer": self.disclaimer,
                "stops": [{"stop_position": int(r[0]),
                           "enterprise_id": r[1], "contract_ref": r[2],
                           "contract_id": int(r[3])} for r in rows]}

    def contract_view(self, contract_id):
        """One contract's full provenance: both bound spend txs
        (the two fee rails), the spans, the tour stops and the
        declared AIGC label; the envelope carries the resident
        disclaimer (AC-SR6). Pure read."""
        if not _is_int(contract_id) or contract_id <= 0:
            raise ShowroomError(E_SR_BAD_ARGS, str(contract_id))
        with self._lock:
            row = self._conn.execute(
                "SELECT c.contract_id, c.pkg_id, c.enterprise_id,"
                " c.contract_ref, c.start_tick, c.lease_end_tick,"
                " c.lease_unit, c.rotation_unit, c.lease_fee,"
                " c.rotation_fee, c.lease_spend_tx, c.rotation_spend_tx,"
                " p.ai_label FROM showroom_contracts c"
                " JOIN showroom_packages p ON p.pkg_id = c.pkg_id"
                " WHERE c.contract_id = ?", (contract_id,)).fetchone()
            if row is None:
                raise ShowroomError(E_SR_UNKNOWN_CONTRACT,
                                    str(contract_id))
            stops = self._conn.execute(
                "SELECT circuit_no, stop_position FROM"
                " showroom_tour_stops WHERE contract_id = ?"
                " ORDER BY circuit_no", (contract_id,)).fetchall()
        return {"contract_id": int(row[0]), "pkg_id": int(row[1]),
                "enterprise_id": row[2], "contract_ref": row[3],
                "start_tick": int(row[4]), "lease_end_tick": int(row[5]),
                "lease_unit": row[6], "rotation_unit": row[7],
                "lease_fee": int(row[8]), "rotation_fee": int(row[9]),
                "lease_spend_tx": row[10],
                "rotation_spend_tx": row[11], "ai_label": int(row[12]),
                "tour_stops": [{"circuit_no": int(s[0]),
                                "stop_position": int(s[1])}
                               for s in stops],
                "disclaimer": self.disclaimer}
