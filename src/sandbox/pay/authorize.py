"""W15 subscribe-message authorization report face (sandbox).

Pre-registered criteria AC-AZ1..AC-AZ7 (state/queue/tech.md R1719
claim line, registered 2026-10-10 BEFORE this code; honesty law:
criteria line first, implementation second).
R1740 revocation extension (AC-VR6, state/queue/tech.md R1740 claim
line, registered BEFORE this code): revoke() report face + state()
read dock - writes still only through the notify face.

Bearer decision (R1719 proposal): the authorization report face
lives in the pay domain (AuthorizeFace wrapping a caller-built
PayNotifyFace), NOT as a lobby-server forwarded frame. Rationale:
  - The W15 authorization must key to census_avatar_id: the R1718
    wiring's send path reads the avatar from pay.db orders, so
    budget keyed to anything else is dead budget.
  - Lobby client actors are ephemeral (anon-/res- uuid): a
    lobby-sent grant would write budget rows no order can ever
    consume, and a client-supplied avatar field would be a
    forgeable identity (server-authoritative field family).
  - In production the popup fires inside the pay gesture
    (wx.requestSubscribeMessage shares the tap with payment), so
    the pay domain is the faithful adjacency; the caller holding
    the census-avatar context drives the report (same as every
    other pay/member face).

W15 semantics carried:
  - once = one send unit; each fresh accept accumulates another
    unit (re-accept is legitimate); longterm = always-keep-choice.
  - Popup suppression: once a longterm grant exists for an avatar
    and template, a re-report is a no-op (the popup no longer
    shows) - status already_longterm, zero new rows.
  - A decline needs no row: absence of authorization IS the
    no-budget state (sends then land skipped_no_budget).
  - Unapproved templates never reach a popup in production, so
    they fail closed here: zero grant rows until the real
    template ids arrive (CEO account-domain physical item).

Single-writer discipline: pay_notify.db's single writer stays
PayNotifyFace; this module writes ONLY through
notify.grant_authorization and reads ONLY through the face.

Idempotency: request_id replays are absorbed by an in-memory TTL
cache (lobby idem_seen precedent, AC-S8e) so a client retry never
double-grants; restart survival is out of sandbox scope (honest
note - a post-restart replay re-grants one fresh once unit at
most, longterm stays gate-idempotent).

Run (readiness self-check): python authorize.py
"""

import argparse
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import notify as N  # noqa: E402  single source of codes/templates

E_AZ_BAD_ARGS = "E_AZ_BAD_ARGS"

_DEFAULT_TTL = 300.0
_DEFAULT_CAP = 4096


class AuthorizeFace(object):
    """W15 authorization report face (wraps a PayNotifyFace)."""

    def __init__(self, notify, ttl_seconds=None, max_keys=None):
        if notify is None:
            raise ValueError("%s: notify face required" % E_AZ_BAD_ARGS)
        if not hasattr(notify, "grant_authorization"):
            raise ValueError("%s: not a notify face" % E_AZ_BAD_ARGS)
        self.notify = notify
        self.ttl = float(ttl_seconds if ttl_seconds is not None
                         else _DEFAULT_TTL)
        self.cap = int(max_keys if max_keys is not None else _DEFAULT_CAP)
        self._seen = {}  # request_id -> (receipt, expires_at monotonic)

    # ---- idempotent replay cache (lobby idem_seen precedent) ----

    def _prune(self, now):
        if self._seen:
            stale = [k for k, v in self._seen.items() if v[1] <= now]
            for k in stale:
                del self._seen[k]

    def _request_key(self, request_id):
        if not isinstance(request_id, str):
            return None
        rid = request_id.strip()
        return rid[:64] if rid else None

    # ---- gates + report ----

    def authorize(self, avatar, template_id, grant_type, request_id=None):
        # gate A: identity (caller-owned census avatar, non-empty)
        if not isinstance(avatar, str) or not avatar.strip():
            raise ValueError("%s: avatar required" % E_AZ_BAD_ARGS)
        avatar = avatar.strip()
        # gate B: template registered + review-approved (fail-closed
        # honest pending: unapproved templates never reach a popup)
        row = self.notify.templates.get(template_id)
        if row is None:
            raise ValueError("%s: %s" % (N.E_PN_UNKNOWN_TEMPLATE,
                                         template_id))
        if not row["approved"]:
            raise N.TemplateNotApproved(
                "%s: %s" % (N.E_TEMPLATE_NOT_APPROVED, template_id))
        # gate C: grant type (W15 once / longterm)
        if grant_type not in ("once", "longterm"):
            raise ValueError("%s: %s" % (N.E_PN_BAD_GRANT_TYPE,
                                         grant_type))
        # gate D: idempotent replay (client retry never double-grants)
        rid = self._request_key(request_id)
        now = time.monotonic()
        if rid is not None:
            self._prune(now)
            hit = self._seen.get(rid)
            if hit is not None:
                receipt = dict(hit[0])
                receipt["status"] = "already_granted"
                return receipt
        # gate E: popup suppression - an existing longterm grant for
        # this avatar+template makes a re-report a zero-row no-op
        budget = self.notify.budget_face(avatar, template_id)
        if grant_type == "longterm" and budget["longterm"] > 0:
            return {"status": "already_longterm", "grant_id": None,
                    "template_id": template_id,
                    "grant_type": grant_type, "budget": budget}
        # grant: write goes ONLY through the notify face (single
        # writer of pay_notify.db)
        gid = self.notify.grant_authorization(avatar, template_id,
                                              grant_type)
        receipt = {"status": "granted", "grant_id": gid,
                  "template_id": template_id, "grant_type": grant_type,
                  "budget": self.notify.budget_face(avatar, template_id)}
        if rid is not None:
            self._seen[rid] = (dict(receipt), now + self.ttl)
            while len(self._seen) > self.cap:  # FIFO evict, insertion order
                del self._seen[next(iter(self._seen))]
        return receipt

    # ---- read faces ----

    def budget(self, avatar, template_id):
        """Popup-suppression read: what the caller should show."""
        return self.notify.budget_face(avatar, template_id)

    def revoke(self, avatar, template_id):
        """W15 revocation report face (R1740, AC-VR6): the user turned
        the template subscription off on the WeChat settings side
        (dead budget - longterm AND remaining once units). Gates:
        identity -> template registered. Template approval is
        deliberately NOT gated here: a stop action must never fail
        closed on the review state (honest asymmetry - grants fail
        closed on unapproved, revocations proceed). Writes go only
        through the notify face (single-writer discipline)."""
        if not isinstance(avatar, str) or not avatar.strip():
            raise ValueError("%s: avatar required" % E_AZ_BAD_ARGS)
        avatar = avatar.strip()
        if template_id not in self.notify.templates:
            raise ValueError("%s: %s" % (N.E_PN_UNKNOWN_TEMPLATE,
                                        template_id))
        return self.notify.revoke_authorization(avatar, template_id)

    def state(self, avatar, template_id):
        """Revocation-aware read dock (R1740): authorization_state."""
        return self.notify.authorization_state(avatar, template_id)

    def close(self):
        """No-op: the notify face is caller-built and caller-owned
        (R1718 ownership contract); this face owns no resources."""
        self._seen.clear()


def main():
    parser = argparse.ArgumentParser(
        description="W15 authorization report face (readiness check)")
    parser.add_argument("--config", default=os.path.join(BASE, "config.json"))
    parser.add_argument("--db", default=os.path.join(
        BASE, "data", "pay_notify.db"))
    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as handle:
        config = json.load(handle)
    notify = N.PayNotifyFace(config, args.db)
    face = AuthorizeFace(notify)
    approved = sorted(t for t, r in notify.templates.items()
                      if r["approved"])
    face.close()
    notify.close()
    print("READY approved_templates=%s idem_ttl=%gs idem_cap=%d"
          % (approved, face.ttl, face.cap))
    return 0


if __name__ == "__main__":
    sys.exit(main())
