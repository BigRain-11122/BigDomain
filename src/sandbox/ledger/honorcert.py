"""Annual civic honor certificate grant face (BigDomain R1755; canon =
explore-queue honor-certificate line seeded by the R1754 honor-board
judgment: the honor-certificate linkage is PLATFORM-SIDE - recipients
derive from board order and zero resident free text enters this
module, so no content-gate point exists here (the festival/ads/
showcase-register posture); a successor resident-text surface must
wire a content pre-gate first.

Design verdicts (registered before this code existed):

  - carrier is a PURE ORCHESTRATION face: this module owns no
    storage at all - no database driver, no schema, no SQL of its
    own. Every write happens inside the referenced
    CollectiblesFace.issue_certificate transaction; every read
    derives from the CivicPointsFace.honor_board and
    CollectiblesFace.collection public faces (reference, never a
    second engine);
  - grant semantics: grant_year_honors(year, top_n, item_id) is a
    year-end platform action. The top-N slice derives from the
    honor board's deterministic order (points down, account id up -
    zero RNG, zero time keys, zero insertion-order keys). Each
    honoree receives exactly one certificate through the public
    award verb with event namespace "civic-honor:<year>" and the
    caller's item_id. The one-per-account-per-year law is carried
    by the collectibles domain itself: its duplicate error
    converges here to an "already" skip, so a re-run is fully
    idempotent and a batch interrupted mid-way heals on re-run;
  - read face: honor_certs(year) walks the full board and derives
    each member's certified flag from the collection read face
    (event namespace match). A member awarded in an earlier run
    keeps the certified flag even after the board moves, because
    certificates are permanent (the R619 platform-award zero-token
    precedent).

Params posture: top_n and item_id arrive as method arguments from
the platform caller at grant time; both are [needs-CEO]
submission-surface values and neither lands in the shipped
config.json (zero new keys).

AIGC posture: platform-side award with zero resident text and zero
generation surface; a resident standing disclaimer is required at
construction and rides every envelope (non-advisory law).

Pre-registered criteria AC-HC1..HC7 live in the R1755
explore-queue row and were written before this code existed
(honesty law). Stdlib only; pure ASCII.
"""

E_HC_BAD_ARGS = "E_HC_BAD_ARGS"
E_HC_NO_DISCLAIMER = "E_HC_NO_DISCLAIMER"

_CIVIC_HONOR = "civic-honor:"
_CL_REQUIRED_ATTRS = ("issue_certificate", "collection")


class HonorCertError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class HonorCertFace:
    """Annual honor certificate orchestration face over two public
    faces: the civic honor board (read) and the collectibles award
    domain (write + read). Owns no storage of its own."""

    def __init__(self, civic, collectibles, disclaimer):
        if civic is None or collectibles is None:
            raise HonorCertError(E_HC_BAD_ARGS,
                                 "civic and collectibles faces required")
        if not hasattr(civic, "honor_board"):
            raise HonorCertError(E_HC_BAD_ARGS,
                                 "civic face must expose honor_board")
        for attr in _CL_REQUIRED_ATTRS:
            if not hasattr(collectibles, attr):
                raise HonorCertError(
                    E_HC_BAD_ARGS,
                    "collectibles face must expose " + attr)
        if not str(disclaimer or "").strip():
            raise HonorCertError(E_HC_NO_DISCLAIMER,
                                 "resident disclaimer required")
        self.civic = civic
        self.collectibles = collectibles
        self.disclaimer = str(disclaimer)

    def _assert_year(self, year):
        """Strict 4-ascii-digit year, mirroring the honor-board gate.
        This face owns its own check so every reject happens before
        any referenced call lands (fail-closed front door)."""
        if (not isinstance(year, str) or len(year) != 4
                or not (year.isascii() and year.isdigit())):
            raise HonorCertError(E_HC_BAD_ARGS,
                                 "year must be exactly 4 ascii digits")
        return year

    def grant_year_honors(self, year, top_n, item_id):
        """Year-end platform action: award the board's top-N members
        one certificate each under the civic-honor:<year> event
        namespace. Idempotent by the collectibles duplicate law: an
        account already holding the year certificate counts as
        already and adds zero rows."""
        year = self._assert_year(year)
        if (not isinstance(top_n, int) or isinstance(top_n, bool)
                or top_n < 1):
            raise HonorCertError(E_HC_BAD_ARGS, "top_n must be int >= 1")
        item_id = str(item_id or "").strip()
        if not item_id:
            raise HonorCertError(E_HC_BAD_ARGS, "item id required")
        event_ref = _CIVIC_HONOR + year
        board = self.civic.honor_board(year)["honor_board"]
        honorees = []
        granted = 0
        already = 0
        for entry in board[:top_n]:
            account_id = entry["account_id"]
            status = "granted"
            try:
                self.collectibles.issue_certificate(
                    account_id, event_ref, item_id)
                granted += 1
            except Exception as exc:  # noqa: BLE001 (award surface)
                if getattr(exc, "code", "") != "E_CL_DUP":
                    raise
                status = "already"
                already += 1
            honorees.append({"rank": entry["rank"],
                             "account_id": account_id,
                             "points": entry["points"],
                             "status": status})
        return {"year": year, "top_n": top_n, "item_id": item_id,
                "granted": granted, "already": already,
                "honorees": honorees, "disclaimer": self.disclaimer}

    def honor_certs(self, year):
        """Pure-read derivation: the full honor board with each
        member's certified flag, derived from the collection read
        face (zero direct table reads; a member certified in an
        earlier grant stays certified after the board moves)."""
        year = self._assert_year(year)
        event_ref = _CIVIC_HONOR + year
        board = self.civic.honor_board(year)["honor_board"]
        honors = []
        certified_count = 0
        for entry in board:
            account_id = entry["account_id"]
            held = [cert for cert in self.collectibles.collection(
                account_id)["certificates"]
                if cert["event_ref"] == event_ref]
            certified = len(held) >= 1
            if certified:
                certified_count += 1
            honors.append({"rank": entry["rank"],
                           "account_id": account_id,
                           "points": entry["points"],
                           "certified": certified,
                           "item_id": held[0]["item_id"] if held
                           else None})
        return {"year": year, "honors": honors,
                "certified_count": certified_count,
                "disclaimer": self.disclaimer}
