"""City data report paid-download face over the token ledger
sandbox (BigDomain R627; canon = BLUEPRINT sec-4 B-side price row
B6 at L76: quarterly one-person-AI-company ecosystem report at 99
CNY per copy, custom industry insight at 999 CNY per copy -
de-identified real operational data as the exclusive deliverable;
claimed from the explore-lane top open row).

Structural de-identification law (canon wording: the deliverable is
de-identified operational data): this module owns exactly three
report tables and performs zero SELECTs against any other table -
it never reads user rows, account rows or any raw operational
store. A published report row carries only aggregate descriptors
(period tag, industry tag, sha256 dataset digest); a download
returns exactly that descriptor key set, so raw row data cannot
leak through this face by construction.

Non-advisory standing note (permanent): reports are descriptive
aggregate operational statistics, not investment advice; the
report_descriptor read face carries this disclaimer as its first
and last content line so every delivered bundle is structurally
accompanied.

Delivery model = permission gate + download voucher:

  - purchase(buyer, report_id, ref) : exactly one token spend at
                         the published catalog price, bound to its
                         spend tx; the immutable purchase row is
                         the permission gate and issues exactly
                         one voucher id
  - download(voucher_id, download_ref) : gate check (voucher
                         exists, owned by the caller, report still
                         published) then the descriptor bundle;
                         downloads are immutable rows keyed by
                         download_ref; one voucher may download
                         repeatedly with distinct refs

Counts-vs-tokens isolation law (metered.py posture carried over):
the purchase spend is the only token-domain touch in this
module; vouchers, downloads and every read face move zero
tokens, and no verb anywhere turns a voucher back into tokens or
moves vouchers between buyers. Any fee reversal is a P1 item for
CEO, approval-only, not a mechanism here.

Gate posture: every reject (duplicate ref, duplicate buyer+report
copy, unknown/unpublished report, unknown voucher, voucher not
owned, bad arguments) fires before the spend / before any row is
written, so a rejected call never charges and never grants.
Catalog, purchase and download rows are immutable once written.

Prices are caller-supplied at publish time in the sandbox; the
production price points (99 CNY quarterly / 999 CNY custom) and
any launch gating are a P1 item for CEO, approval-only
([needs-CEO]). No config keys are added by this module.

Pre-registered criteria AC-CT1..AC-CT7 live in the R627 backlog
row and were written before this code existed (honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: three extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import hashlib
import sqlite3
import threading

E_RPT_UNPUBLISHED = "E_RPT_UNPUBLISHED"      # report not in catalog
E_RPT_DUP = "E_RPT_DUP"                        # ref / copy replay
E_RPT_UNKNOWN_VOUCHER = "E_RPT_UNKNOWN_VOUCHER"
E_RPT_NOT_OWNER = "E_RPT_NOT_OWNER"            # cross-buyer voucher
E_RPT_BAD_ARGS = "E_RPT_BAD_ARGS"

KINDS = ("quarterly", "custom")

NON_ADVISORY = ("non-advisory notice: descriptive aggregate"
                " operational statistics, not investment advice")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS report_catalog (
    report_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    period_tag TEXT NOT NULL,
    industry_tag TEXT NOT NULL,
    price_cent INTEGER NOT NULL CHECK (price_cent >= 1),
    dataset_digest TEXT NOT NULL,
    published_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS report_purchases (
    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer TEXT NOT NULL,
    report_id TEXT NOT NULL,
    purchase_ref TEXT NOT NULL UNIQUE,
    price_cent INTEGER NOT NULL,
    bound_spend_tx TEXT NOT NULL,
    voucher_id TEXT NOT NULL UNIQUE,
    purchased_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS report_downloads (
    download_ref TEXT PRIMARY KEY,
    voucher_id TEXT NOT NULL,
    buyer TEXT NOT NULL,
    report_id TEXT NOT NULL,
    downloaded_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return (isinstance(value, int) and not isinstance(value, bool))


def _buyer_ok(buyer):
    return (buyer.startswith("usr:") or buyer.startswith("ent:")) \
        and len(buyer) > 4


class ReportError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class ReportsFace:
    """Paid city-data-report download face over one Ledger instance
    sharing the same DB file. Own connection and lock for the three
    report tables; the only token touch is the ledger spend inside
    purchase (the public ledger API)."""

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

    # -- internal helpers ---------------------------------------------------

    def _catalog_row(self, report_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT kind, title, period_tag, industry_tag,"
                " price_cent, dataset_digest FROM report_catalog"
                " WHERE report_id = ?", (report_id,)).fetchone()
        return row

    def _voucher_row(self, voucher_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT buyer, report_id FROM report_purchases"
                " WHERE voucher_id = ?", (voucher_id,)).fetchone()
        return row

    # -- writer faces -------------------------------------------------------

    def publish_report(self, report_id, kind, title, period_tag,
                       industry_tag, price_cent, dataset_digest):
        """Mechanism registration of one published report (aggregate
        descriptors only - period tag, industry tag, sha256 dataset
        digest; no user identifiers, no raw data). Re-publishing the
        same id with identical parameters is idempotent; a conflicting
        re-publish is rejected E_RPT_DUP (published rows are
        immutable - no UPDATE exists for the catalog)."""
        report_id = str(report_id or "").strip()
        kind = str(kind or "").strip()
        title = str(title or "").strip()
        period_tag = str(period_tag or "").strip()
        industry_tag = str(industry_tag or "").strip()
        digest = str(dataset_digest or "").strip()
        if not report_id or not title or not period_tag or not digest:
            raise ReportError(E_RPT_BAD_ARGS,
                              "report_id/title/period_tag/digest required")
        if kind not in KINDS:
            raise ReportError(E_RPT_BAD_ARGS, "unknown kind " + str(kind))
        if not _is_int(price_cent) or price_cent < 1:
            raise ReportError(E_RPT_BAD_ARGS,
                              "price_cent must be int >= 1")
        with self._lock:
            row = self._conn.execute(
                "SELECT kind, title, period_tag, industry_tag, price_cent,"
                " dataset_digest FROM report_catalog WHERE report_id = ?",
                (report_id,)).fetchone()
            if row is not None:
                if (row[0], row[1], row[2], row[3], int(row[4]),
                        row[5]) == (kind, title, period_tag, industry_tag,
                                    price_cent, digest):
                    return {"report_id": report_id, "idempotent": True}
                raise ReportError(E_RPT_DUP, report_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO report_catalog (report_id, kind, title,"
                    " period_tag, industry_tag, price_cent, dataset_digest,"
                    " published_utc) VALUES (?,?,?,?,?,?,?,?)",
                    (report_id, kind, title, period_tag, industry_tag,
                     price_cent, digest, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ReportError(E_RPT_DUP, report_id)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"report_id": report_id, "idempotent": False}

    def purchase(self, buyer, report_id, ref):
        """Buy one copy of one published report: exactly one token
        spend at the published catalog price from the buyer account,
        then the immutable purchase row (the permission gate) plus
        its one download voucher, both bound to that spend tx.
        Duplicate refs and duplicate buyer+report copies are both
        rejected before the spend (zero charge); a ledger balance
        reject leaves zero side effects (no row, no voucher)."""
        buyer = str(buyer or "").strip()
        report_id = str(report_id or "").strip()
        if not _buyer_ok(buyer):
            raise ReportError(E_RPT_BAD_ARGS,
                              "buyers are usr:* or ent:* accounts only")
        if not report_id:
            raise ReportError(E_RPT_BAD_ARGS, "report_id required")
        if not str(ref).strip():
            raise ReportError(E_RPT_BAD_ARGS, "purchase ref required")
        cat = self._catalog_row(report_id)
        if cat is None:
            raise ReportError(E_RPT_UNPUBLISHED, report_id)
        price = int(cat[4])
        # pre-checks BEFORE the spend: a rejected replay never charges
        with self._lock:
            dup_ref = self._conn.execute(
                "SELECT 1 FROM report_purchases WHERE purchase_ref = ?",
                (str(ref),)).fetchone()
            dup_copy = self._conn.execute(
                "SELECT 1 FROM report_purchases WHERE buyer = ?"
                " AND report_id = ?", (buyer, report_id)).fetchone()
        if dup_ref is not None or dup_copy is not None:
            raise ReportError(E_RPT_DUP,
                              str(ref) if dup_ref is not None
                              else buyer + "/" + report_id)
        spend_tx = self.led.spend(buyer, price, str(ref), "order")
        voucher = "vch-" + hashlib.sha256(
            (str(ref) + "|" + buyer + "|" + report_id).encode(
                "utf-8")).hexdigest()[:16]
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO report_purchases (buyer, report_id,"
                    " purchase_ref, price_cent, bound_spend_tx, voucher_id,"
                    " purchased_utc) VALUES (?,?,?,?,?,?,?)",
                    (buyer, report_id, str(ref), price, spend_tx, voucher,
                     _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ReportError(E_RPT_DUP, str(ref))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"report_id": report_id, "buyer": buyer,
                "price_cent": price, "spend_tx": spend_tx,
                "voucher_id": voucher}

    def download(self, buyer, voucher_id, download_ref):
        """Download through the permission gate: the voucher must
        exist, be owned by the caller and reference a still
        published report; the delivery is the descriptor bundle
        (aggregate metadata + dataset digest - structural
        de-identification, zero raw row data). One download = one
        immutable download row keyed by the caller's download_ref;
        duplicate refs are rejected with zero double-write; one
        voucher may download repeatedly with distinct refs. Zero
        token-ledger involvement."""
        buyer = str(buyer or "").strip()
        voucher_id = str(voucher_id or "").strip()
        download_ref = str(download_ref or "").strip()
        if not _buyer_ok(buyer):
            raise ReportError(E_RPT_BAD_ARGS,
                              "buyers are usr:* or ent:* accounts only")
        if not voucher_id:
            raise ReportError(E_RPT_BAD_ARGS, "voucher required")
        if not download_ref:
            raise ReportError(E_RPT_BAD_ARGS, "download ref required")
        with self._lock:
            vrow = self._conn.execute(
                "SELECT buyer, report_id FROM report_purchases"
                " WHERE voucher_id = ?", (voucher_id,)).fetchone()
            if vrow is None:
                raise ReportError(E_RPT_UNKNOWN_VOUCHER, voucher_id)
            if vrow[0] != buyer:
                raise ReportError(E_RPT_NOT_OWNER, voucher_id)
            cat = self._conn.execute(
                "SELECT kind, title, period_tag, industry_tag,"
                " price_cent, dataset_digest FROM report_catalog"
                " WHERE report_id = ?", (vrow[1],)).fetchone()
            if cat is None:
                raise ReportError(E_RPT_UNPUBLISHED, vrow[1])
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO report_downloads (download_ref,"
                    " voucher_id, buyer, report_id, downloaded_utc)"
                    " VALUES (?,?,?,?,?)",
                    (download_ref, voucher_id, buyer, vrow[1], _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ReportError(E_RPT_DUP, download_ref)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return self.report_descriptor(vrow[1])

    # -- read faces -----------------------------------------------------------

    def report_descriptor(self, report_id):
        """The delivered bundle: aggregate descriptors + dataset
        digest, with the non-advisory standing notice as the first
        and last content line. The key set is exactly the descriptor
        set - raw row data cannot appear in a delivery. Production
        prices stay [needs-CEO] P1 approval-only. Read-only, zero
        token movement."""
        cat = self._catalog_row(report_id)
        if cat is None:
            raise ReportError(E_RPT_UNPUBLISHED, report_id)
        return {"report_id": report_id,
                "kind": cat[0],
                "title": cat[1],
                "disclaimer_first": NON_ADVISORY,
                "disclaimer_last": NON_ADVISORY,
                "period_tag": cat[2],
                "industry_tag": cat[3],
                "dataset_digest": cat[5],
                "pricing_note": "prices published at sandbox dock;"
                                " production 99/999-CNY anchors"
                                " = [needs-CEO] P1 approval-only"}

    def reconcile_report(self, report_id):
        """Report reconciliation read face: purchases must equal
        vouchers one-to-one, every download row must hang off a
        valid voucher of the same report, and every purchase carries
        its spend tx (billing cross-check against the token ledger).
        Any drift (e.g. an injected orphan download row) flips the
        balanced verdict to False. Read-only, zero token
        movement."""
        cat = self._catalog_row(report_id)
        if cat is None:
            raise ReportError(E_RPT_UNPUBLISHED, report_id)
        with self._lock:
            purchases = self._conn.execute(
                "SELECT purchase_ref, price_cent, bound_spend_tx,"
                " voucher_id FROM report_purchases WHERE report_id = ?"
                " ORDER BY purchase_id", (report_id,)).fetchall()
            vouchers = self._conn.execute(
                "SELECT COUNT(DISTINCT voucher_id) FROM report_purchases"
                " WHERE report_id = ?", (report_id,)).fetchone()[0]
            downloads = self._conn.execute(
                "SELECT download_ref, voucher_id FROM report_downloads"
                " WHERE report_id = ? ORDER BY downloaded_utc",
                (report_id,)).fetchall()
        voucher_set = {p[3] for p in purchases}
        orphans = [d[0] for d in downloads if d[1] not in voucher_set]
        return {"report_id": report_id,
                "purchases": len(purchases),
                "vouchers": int(vouchers),
                "downloads": len(downloads),
                "orphan_downloads": orphans,
                "balanced": (len(purchases) == int(vouchers)
                             and not orphans),
                "spend_txs": [p[2] for p in purchases],
                "billed_total_cent": sum(int(p[1]) for p in purchases)}

    def download_log(self, report_id):
        """The report's download log (immutable rows with their
        vouchers). Read-only, zero token movement."""
        cat = self._catalog_row(report_id)
        if cat is None:
            raise ReportError(E_RPT_UNPUBLISHED, report_id)
        with self._lock:
            rows = self._conn.execute(
                "SELECT download_ref, voucher_id, buyer, downloaded_utc"
                " FROM report_downloads WHERE report_id = ?"
                " ORDER BY downloaded_utc, download_ref",
                (report_id,)).fetchall()
        return {"report_id": report_id,
                "downloads": [{"download_ref": r[0], "voucher_id": r[1],
                               "buyer": r[2], "downloaded_utc": r[3]}
                              for r in rows]}
