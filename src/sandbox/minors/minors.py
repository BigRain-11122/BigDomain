"""Minor-resident guardian guard face (sandbox, pure stdlib).

Carrier for the minors compliance face of the M1 walkable-slice
milestone (audit P-2026-10-02-02, due 10-09): city-commerce-plan
v0 sec.6 lists the minors face ("subscription / in-app purchase /
live wiring = M1 prerequisite"). Legal anchors (group benchmark
face, wall W11, G slice 2026-10-02):
- <Regulations on the Cyber Protection of Minors> sec.43-44:
  guardian management of minor online time / permissions / spend.
- sec.31: minors prohibited from opening live streams.
- sec.24(3): no automated commercial marketing push to minors.

This module is the GUARD, not the three business faces. The three
production call sites (member subscribe/activate, pay order
creation, liveroom open) are listed in WIRING_POINTS; R939 wired
them as opt-in constructor args (minor_guard=...) with fail-closed
caller-supplied gate inputs (honest note: the pay grant commit
face record_spend and the frontdoor page mount are the declared
row remainder, follow-up).

Fail-closed discipline (mirrors citymodel/scenario.py R850 law):
- Spend limits and time windows are guardian/caller-supplied.
  [needs-CEO]: platform-side default limit VALUES are never
  invented here; an unconfigured limit refuses billing outright.
- No wall clock inside: dates and minute-of-day are caller
  supplied, so identical inputs give byte-identical outputs.
"""

from __future__ import annotations

MINOR_LAW_CITE = (
    "Regulations on the Cyber Protection of Minors "
    "(State Council Decree No.766, 2024-01-01 effective): "
    "sec.43-44 guardian time/permission/spend management; "
    "sec.31 minors live-stream ban; sec.24(3) automated "
    "commercial marketing push ban."
)

# The three M1-prerequisite wiring points (production faces).
WIRING_POINTS = (
    "member: subscribe/activate entry -> check_spend / check_time",
    "pay: order creation entry -> check_spend (minor gate before any billing)",
    "liveroom: open-room entry -> check_live (sec.31 hard ban)",
)


class GuardError(Exception):
    """Fail-closed guard refusal. Refusals never mutate any state."""

    def __init__(self, code, message):
        super(GuardError, self).__init__("%s: %s" % (code, message))
        self.code = code


def _minutes(value):
    if not isinstance(value, int) or isinstance(value, bool):
        raise GuardError("E_MG_PARAM", "time values must be int minutes")
    if value < 0 or value >= 24 * 60:
        raise GuardError("E_MG_PARAM", "minute-of-day out of range 0..1439")
    return value


def _cents(value, name):
    if not isinstance(value, int) or isinstance(value, bool):
        raise GuardError("E_MG_PARAM", "%s must be int cents" % name)
    if value <= 0:
        raise GuardError("E_MG_PARAM", "%s must be positive" % name)
    return value


class MinorGuardFace(object):
    """Guardian guard face: minors-only scope, adults pass through."""

    def __init__(self):
        # resident_id -> {"minor": bool, "guardian": str|None}
        self._residents = {}
        # resident_id -> {"windows": [(s,e)], "single_cent": int,
        #                 "daily_cent": int}
        self._limits = {}
        # (resident_id, date) -> {"spent_cent": int, "events": [str]}
        self._day_ledger = {}

    # -- registration ------------------------------------------------

    def register_resident(self, resident_id, is_minor, guardian_id=None):
        if not isinstance(resident_id, str) or not resident_id:
            raise GuardError("E_MG_PARAM", "resident_id must be non-empty str")
        if resident_id in self._residents:
            raise GuardError("E_MG_DUP", "resident already registered")
        if not isinstance(is_minor, bool):
            raise GuardError("E_MG_PARAM", "is_minor must be bool")
        if is_minor:
            if not isinstance(guardian_id, str) or not guardian_id:
                raise GuardError(
                    "E_MG_GUARDIAN",
                    "minor resident requires a guardian binding (sec.43)")
            self._residents[resident_id] = {
                "minor": True, "guardian": guardian_id}
        else:
            self._residents[resident_id] = {
                "minor": False, "guardian": None}
        return dict(self._residents[resident_id])

    # -- guardian limit configuration --------------------------------

    def set_guardian_limits(self, guardian_id, resident_id,
                            allowed_windows=None, single_cent=None,
                            daily_cent=None):
        r = self._residents.get(resident_id)
        if r is None:
            raise GuardError("E_MG_UNKNOWN", "resident not registered")
        if not r["minor"]:
            raise GuardError(
                "E_MG_NOT_MINOR",
                "guardian limits apply to minors only (adult pass-through)")
        if r["guardian"] != guardian_id:
            raise GuardError(
                "E_MG_GUARDIAN",
                "only the bound guardian may configure limits (sec.44)")
        wins = []
        for w in (allowed_windows or []):
            if not isinstance(w, (tuple, list)) or len(w) != 2:
                raise GuardError(
                    "E_MG_PARAM", "window must be (start_min, end_min)")
            s, e = _minutes(w[0]), _minutes(w[1])
            if s >= e:
                raise GuardError(
                    "E_MG_PARAM", "window start must be before end")
            wins.append((s, e))
        lim = {"windows": tuple(wins), "single_cent": None,
               "daily_cent": None}
        if single_cent is not None:
            lim["single_cent"] = _cents(single_cent, "single_cent")
        if daily_cent is not None:
            lim["daily_cent"] = _cents(daily_cent, "daily_cent")
        if (lim["single_cent"] is None) != (lim["daily_cent"] is None):
            raise GuardError(
                "E_MG_PARAM",
                "spend limits must set single and daily together")
        self._limits[resident_id] = lim
        return {"resident_id": resident_id,
                "windows": ["%04d-%04d" % (s, e) for s, e in wins],
                "single_cent": lim["single_cent"],
                "daily_cent": lim["daily_cent"]}

    def _minor_limit(self, resident_id):
        r = self._residents[resident_id]
        if not r["minor"]:
            return None
        lim = self._limits.get(resident_id)
        if lim is None:
            raise GuardError(
                "E_MG_NO_LIMIT",
                "minor has no guardian limits configured: fail-closed, "
                "refuse billing until guardian configures (sec.43-44; "
                "limit values [needs-CEO], never defaulted)")
        return lim

    # -- gates (read-only checks; refusals mutate nothing) ------------

    def check_time(self, resident_id, now_min, date):
        r = self._residents.get(resident_id)
        if r is None:
            raise GuardError("E_MG_UNKNOWN", "resident not registered")
        if not r["minor"]:
            return {"allowed": True, "scope": "adult"}
        lim = self._minor_limit(resident_id)
        n = _minutes(now_min)
        for s, e in lim["windows"]:
            if s <= n < e:
                return {"allowed": True, "scope": "minor",
                        "window": "%04d-%04d" % (s, e)}
        raise GuardError(
            "E_MG_TIME",
            "minor outside guardian time windows (sec.43)")

    def check_spend(self, resident_id, amount_cent, date):
        r = self._residents.get(resident_id)
        if r is None:
            raise GuardError("E_MG_UNKNOWN", "resident not registered")
        amt = _cents(amount_cent, "amount_cent")
        if not isinstance(date, str) or not date:
            raise GuardError("E_MG_PARAM", "date must be non-empty str")
        if not r["minor"]:
            return {"allowed": True, "scope": "adult"}
        lim = self._minor_limit(resident_id)
        if lim["single_cent"] is None:
            # Limits configured but spend face absent: time-only config.
            # Spend stays fail-closed for minors in that state.
            raise GuardError(
                "E_MG_NO_LIMIT",
                "minor spend refused: guardian configured no spend "
                "limits (fail-closed; [needs-CEO] values)")
        key = (resident_id, date)
        spent = self._day_ledger.get(key, {}).get("spent_cent", 0)
        if amt > lim["single_cent"]:
            raise GuardError(
                "E_MG_SPEND_SINGLE",
                "minor single-purchase limit exceeded (sec.44)")
        if spent + amt > lim["daily_cent"]:
            raise GuardError(
                "E_MG_SPEND_DAILY",
                "minor daily spend limit exceeded (sec.44)")
        return {"allowed": True, "scope": "minor",
                "spent_before_cent": spent,
                "spent_after_cent": spent + amt}

    def record_spend(self, resident_id, amount_cent, date, ref):
        """Commit one spend AFTER check_spend passed (idempotent-ref)."""
        r = self._residents[resident_id]
        if not r["minor"]:
            raise GuardError(
                "E_MG_NOT_MINOR", "record_spend is the minors ledger face")
        amt = _cents(amount_cent, "amount_cent")
        if not isinstance(ref, str) or not ref:
            raise GuardError("E_MG_PARAM", "ref must be non-empty str")
        self.check_spend(resident_id, amt, date)  # re-gate before commit
        key = (resident_id, date)
        day = self._day_ledger.setdefault(
            key, {"spent_cent": 0, "events": []})
        day["spent_cent"] += amt
        day["events"].append(ref)
        return {"resident_id": resident_id, "date": date, "ref": ref,
                "spent_cent": day["spent_cent"]}

    def check_live(self, resident_id):
        r = self._residents.get(resident_id)
        if r is None:
            raise GuardError("E_MG_UNKNOWN", "resident not registered")
        if r["minor"]:
            raise GuardError(
                "E_MG_LIVE_BAN",
                "minor live-stream opening prohibited (sec.31)")
        return {"allowed": True, "scope": "adult"}

    def check_marketing(self, resident_id):
        r = self._residents.get(resident_id)
        if r is None:
            raise GuardError("E_MG_UNKNOWN", "resident not registered")
        if r["minor"]:
            raise GuardError(
                "E_MG_MARKETING_BAN",
                "automated commercial marketing push to minor "
                "prohibited (sec.24(3))")
        return {"allowed": True, "scope": "adult"}

    # -- read faces ---------------------------------------------------

    def day_readout(self, resident_id, date):
        day = self._day_ledger.get((resident_id, date),
                                   {"spent_cent": 0, "events": []})
        return {"resident_id": resident_id, "date": date,
                "spent_cent": day["spent_cent"],
                "events": list(day["events"])}

    def residents_readout(self):
        return {rid: dict(rec) for rid, rec in self._residents.items()}


COMPLIANCE_HEADER = (
    "== Minor Guardian Guard Face (sandbox v0.1) ==\n"
    "[needs-CEO]: platform default limit VALUES are never invented "
    "here; unconfigured guardian limits refuse billing (fail-closed).\n"
    "NON-INVESTMENT-ADVISORY: this face gates service quotas and "
    "platform features only; nothing here is investment advice.\n"
    "AI-GENERATED LABEL: output of deterministic code; every "
    "presentation surface carrying this report keeps the AIGC label "
    "face (BLUEPRINT sec.5 compliance chain).\n"
    "LAW: %s\n" % MINOR_LAW_CITE
)


def render_report(face, resident_ids, date):
    """Deterministic ASCII readout; same inputs -> byte-identical."""
    lines = [COMPLIANCE_HEADER.rstrip("\n")]
    lines.append("wiring_points (production faces, follow-up row):")
    for wp in WIRING_POINTS:
        lines.append("  - %s" % wp)
    for rid in resident_ids:
        rec = face.residents_readout().get(rid)
        if rec is None:
            lines.append("resident %s: <unregistered>" % rid)
            continue
        scope = "minor(guardian=%s)" % rec["guardian"] if rec["minor"] \
            else "adult"
        day = face.day_readout(rid, date)
        lines.append("resident %s: scope=%s date=%s spent_cent=%d "
                     "events=%s"
                     % (rid, scope, date, day["spent_cent"],
                        ",".join(day["events"]) or "-"))
    return "\n".join(lines) + "\n"
