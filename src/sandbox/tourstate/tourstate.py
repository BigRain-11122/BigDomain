"""M4 visitor-end 3D three-state selection prep face (BigDomain
dispatch item of group mobilization order O-2026-0929-007, round
R602). The order names this company: "visitor-end 3D three-state
selection prep + L1 legitimate-purchase gate report item (the sole
precondition of visitor-end commercialization)".

Canon anchors (reference only, never rebuilt here):
  - three candidate states for the visitor-end 3D presentation:
      dataface       = live data face: census digest 11-field public
                       whitelist + world-state derived fields, zero
                       city-scene rendering - the current M4 spec
                       posture (docs/spec/m4-visitor-end-spec.md
                       sec 1/2, D2 non-game-category mini-program)
      offline_frames = offline-rendered imagery face: stills /
                       panorama / short clips supplied by the
                       BigCompute 3D offline-render batch (order
                       O-2026-0929-007 @BigCompute dispatch,
                       visitor-end approval 10-07)
      realtime3d     = real-time 3D roam face (WebGL measured-pitfall
                       record from the City3D line + D2 category
                       compatibility question, unverified)
  - L1 red line (R-20260929-pivot-bigdomain sec 1): the 48 packs
      circulate as unlicensed resells with zero commercial grant -
      prototype/style validation tolerated, commercial surfaces
      forbidden until the CEO legitimate-purchase gate approves
  - five hard gates per state: G1 license_l1 / G2 category_d2 /
      G3 render_supply / G4 aigc_mark / G5 msgsec_check

Executable contract (design-as-code):
  - build_packet(purchase_approved) returns a deterministic
    decision-prep packet: three states, per-state gate matrix
    evaluated from canon facts only, three pre-registered selection
    questions, and the open CEO decision items; sha256 packet id
    over the canonical payload (idempotent, zero RNG);
  - verify_packet(packet) recomputes the id and re-derives every
    gate status and reason from the packet's own facts - any field
    tamper raises E_TS_TAMPER;
  - the selection itself stays a needs-CEO P1 approval face: this
    module prepares, never decides; all cost anchors stay None
    (collection is a separate research item, never invented here).

Red lines: stdlib only, zero network, zero RNG, zero money
movement, zero pricing constants, pure ASCII source, no config
keys shipped.
Pre-registered criteria: AC-TS1..AC-TS7 = src/os/backlog.md R602
row (written before this module).
"""

import hashlib
import json

E_TS_TAMPER = "E_TS_TAMPER"
E_TS_BAD_INPUT = "E_TS_BAD_INPUT"
SCHEMA = "bigdomain.tourstate/1"

GATE_PASS = "PASS"
GATE_BLOCKED = "BLOCKED"
GATE_TBD = "TBD"

STATES = ("dataface", "offline_frames", "realtime3d")
GATES = ("license_l1", "category_d2", "render_supply",
         "aigc_mark", "msgsec_check")

# canon fact table: which states put 48-pack-derived pixels on the
# visitor-end commercial surface (L1 red line above)
PACK_DERIVED = {"dataface": False, "offline_frames": True,
                "realtime3d": True}

SELECTION_QUESTIONS = (
    "Q1 license: does the state put pack-derived pixels on a "
    "commercial surface before the CEO purchase gate clears?",
    "Q2 category: does the state fit the D2 non-game-category "
    "mini-program carrier?",
    "Q3 supply: is every external dependency deliverable inside "
    "the launch window?",
)

CEO_DECISIONS = (
    {"id": "purchase_gate_l1", "face": "needs-CEO",
     "subject": "48-pack legitimate purchase gate (L1)",
     "cost_anchor": None,
     "cost_note": "price anchors collected by a separate research "
                  "item, never invented here"},
    {"id": "three_state_selection", "face": "needs-CEO",
     "subject": "visitor-end 3D state selection (or phased combo)",
     "cost_anchor": None,
     "cost_note": "gate matrix and questions pre-registered; the "
                  "decision stays CEO-side (P1 approval-only)"},
)

COST_NOTE = "all cost anchors stay needs-CEO, none invented here"


class TourStateError(Exception):
    """Prep-face error with a stable machine code."""

    def __init__(self, code, detail=""):
        super().__init__("%s %s" % (code, detail))
        self.code = code
        self.detail = detail


def canonical(obj):
    """Deterministic JSON text: sorted keys, tight separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def digest(payload):
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def evaluate_gate(state, gate, purchase_approved):
    """Deterministic gate evaluation from canon facts only."""
    if state not in PACK_DERIVED:
        raise TourStateError(E_TS_BAD_INPUT, "unknown state %s" % state)
    if gate not in GATES:
        raise TourStateError(E_TS_BAD_INPUT, "unknown gate %s" % gate)
    pack = PACK_DERIVED[state]
    if gate == "license_l1":
        if pack and not purchase_approved:
            return (GATE_BLOCKED, "48-pack license: zero commercial "
                    "grant, needs-CEO purchase gate")
        if pack:
            return (GATE_PASS, "purchase gate approved (hypothetical "
                    "leg; receipts re-verified at bootstrap)")
        return (GATE_PASS, "zero pack-derived pixels")
    if gate == "category_d2":
        if state == "realtime3d":
            return (GATE_TBD, "real-time 3D inside the D2 "
                    "non-game-category mini-program: category "
                    "compatibility unverified, needs a web check")
        return (GATE_PASS, "static/data pages fit the D2 "
                "non-game-category mini-program")
    if gate == "render_supply":
        if state == "offline_frames":
            return (GATE_TBD, "BigCompute offline-render batch "
                    "supply line active, visitor-end approval 10-07")
        if state == "realtime3d":
            return (GATE_TBD, "physical carrier rides the FluxVerse "
                    "M4 schedule; WebGL pitfall record on file")
        return (GATE_PASS, "city snapshot data feed already spec'd "
                "(m4-visitor-end-spec sec 2)")
    if gate == "aigc_mark":
        if state == "realtime3d":
            return (GATE_TBD, "in-frame AIGC mark overlay for "
                    "real-time renders: design pending")
        return (GATE_PASS, "AIGC mark face carried by m4 spec sec 4 "
                "(labeling-measures 2025-09-01 anchor)")
    # gate == "msgsec_check"
    return (GATE_PASS, "user-visible text faces ride the "
            "ugc-pipeline IF-8 single-source gate")


def state_verdict(gate_statuses):
    """ready_now = all PASS; not_ready = any TBD; gated = only
    BLOCKED gates remain (P1 approval face)."""
    if all(s == GATE_PASS for s in gate_statuses):
        return "ready_now"
    if any(s == GATE_TBD for s in gate_statuses):
        return "not_ready"
    return "gated"


def build_packet(purchase_approved=False):
    """Build the deterministic three-state decision-prep packet."""
    if not isinstance(purchase_approved, bool):
        raise TourStateError(E_TS_BAD_INPUT,
                            "purchase_approved must be a bool")
    states = []
    for sid in STATES:
        gates = {}
        for gid in GATES:
            status, reason = evaluate_gate(sid, gid, purchase_approved)
            gates[gid] = {"status": status, "reason": reason}
        verdict = state_verdict([gates[g]["status"] for g in GATES])
        states.append({"id": sid,
                       "pack_derived": PACK_DERIVED[sid],
                       "gates": gates,
                       "verdict": verdict})
    packet = {
        "schema": SCHEMA,
        "purchase_approved": purchase_approved,
        "states": states,
        "selection_questions": list(SELECTION_QUESTIONS),
        "ceo_decisions": [dict(item) for item in CEO_DECISIONS],
        "cost_note": COST_NOTE,
    }
    packet["packet_id"] = digest(canonical(packet))
    return packet


def verify_packet(packet):
    """Recompute the id and re-derive every gate from the packet's
    own facts; any drift raises E_TS_TAMPER."""
    if not isinstance(packet, dict) or "packet_id" not in packet:
        raise TourStateError(E_TS_BAD_INPUT, "not a prep packet")
    stored_id = packet["packet_id"]
    payload = {key: value for key, value in packet.items()
               if key != "packet_id"}
    if digest(canonical(payload)) != stored_id:
        raise TourStateError(E_TS_TAMPER, "packet_id mismatch")
    approved = payload.get("purchase_approved")
    if not isinstance(approved, bool):
        raise TourStateError(E_TS_TAMPER, "purchase_approved not bool")
    states = payload.get("states")
    if not isinstance(states, list) or len(states) != len(STATES):
        raise TourStateError(E_TS_TAMPER, "states not three")
    for index, st in enumerate(states):
        if not isinstance(st, dict) or st.get("id") != STATES[index]:
            raise TourStateError(E_TS_TAMPER, "state order drift")
        if st.get("pack_derived") is not PACK_DERIVED[st["id"]]:
            raise TourStateError(E_TS_TAMPER, "pack_derived drift")
        gates = st.get("gates")
        if not isinstance(gates, dict) or set(gates) != set(GATES):
            raise TourStateError(E_TS_TAMPER, "gate set drift")
        for gid in GATES:
            status, reason = evaluate_gate(st["id"], gid, approved)
            gate = gates[gid]
            if (gate.get("status") != status
                    or gate.get("reason") != reason):
                raise TourStateError(E_TS_TAMPER,
                                     "gate drift at %s/%s"
                                     % (st["id"], gid))
        verdict = state_verdict([gates[g]["status"] for g in GATES])
        if st.get("verdict") != verdict:
            raise TourStateError(E_TS_TAMPER, "verdict drift")
    return True
