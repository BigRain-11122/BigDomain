"""Entitlement catalog for the membership sandbox (BigDomain P-47-5b).

Single source of truth for the tier matrix (AC-M1): tier keys, monthly
credit quotas, privilege sets, period/grace days, tier copy, the
entitlement->tier product map and the voucher-type directory. Everything
numeric or naming-shaped stays a [needs-CEO] config placeholder (values
are CEO approval faces, never self-served).

Catalog.load refuses the whole startup (E_GATE_OFFLINE serve-refusal
family, same method as lobby AC-S4 / ugc AC-U2 / pay AC-Y8) on the five
bad-config families from AC-M1:
  1 missing/empty tier matrix        4 missing tier copy
  2 monthly credits not a positive int 5 missing resident disclaimer
  3 unknown privilege key
plus fail-closed banned-copy tiers (AC-M15: a tier whose copy carries a
banned marketing word never opens) and an unwired content gate (AC-M7,
fifth same-origin piece).

Encoding discipline: this script stays ASCII; all Chinese copy and
wordlists live in config.json.
"""

import os
import sys

_BASE = os.path.dirname(os.path.abspath(__file__))
_LOBBY = os.path.normpath(os.path.join(_BASE, "..", "lobby"))
for _p in (_LOBBY,):
    # idempotent: importable both standalone and after member.py's dance
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

from sec_gate import GateOfflineError, SecGate  # lobby gate product

# Known privilege keys (the closed vocabulary tiers may grant; a config
# naming anything else is a bad config, AC-M1 family 3).
KNOWN_PRIVILEGES = (
    "basic_badge",              # experience: base identity badge
    "emoji_pack_standard",      # experience: standard lobby emoji pack
    "chat_highlight",           # mayor: lobby envelope highlight field
    "resident_companion",       # mayor: BigLife companion line dock (blocked face)
    "building_naming_voucher",  # mayor: 1/month building naming voucher
    "priority_queue",           # cocreator: queue priority position (not advice)
    "cocreation_priority",      # cocreator: ugc intake sort weight (never bypass review)
    "private_room",             # cocreator: FluxVerse/visitor-end room (blocked face)
    "skin_free",                # cocreator: skin pool access (blocked face)
)


class Tier:
    __slots__ = ("key", "monthly_credits", "period_days", "grace_days",
                 "privileges", "copy")

    def __init__(self, key, monthly_credits, period_days, grace_days,
                 privileges, copy):
        self.key = key
        self.monthly_credits = monthly_credits
        self.period_days = period_days
        self.grace_days = grace_days
        self.privileges = privileges
        self.copy = copy


class Catalog:
    """Validated config. Construction IS the validation (fail closed)."""

    def __init__(self, gate, disclaimer, ai_label, ban_words, tiers,
                 products, vouchers):
        self.gate = gate
        self.disclaimer = disclaimer
        self.ai_label = ai_label
        self.ban_words = ban_words
        self.tiers = tiers            # tier key -> Tier
        self.products = products      # entitlement key -> Tier
        self.vouchers = vouchers      # voucher type -> privilege key

    @classmethod
    def from_config(cls, config):
        if not isinstance(config, dict):
            raise GateOfflineError("config not loaded")
        gate = SecGate.from_config(config)  # AC-M7: no gate = no serve
        comp = config.get("compliance") or {}
        disclaimer = str(comp.get("disclaimer", ""))
        if not disclaimer:
            raise GateOfflineError("compliance.disclaimer missing (AC-M9 resident face)")
        ai_label = str(comp.get("ai_label", ""))
        if not ai_label:
            raise GateOfflineError("compliance.ai_label missing (AC-M8 AI marker face)")
        bans = [str(w) for w in (config.get("copy_ban_words") or []) if str(w)]
        if not bans:
            raise GateOfflineError("copy_ban_words missing or empty (AC-M15)")
        tiers_cfg = config.get("tiers")
        if not isinstance(tiers_cfg, dict) or not tiers_cfg:
            raise GateOfflineError("tiers matrix missing or empty (AC-M1)")
        tiers = {}
        for key, spec in tiers_cfg.items():
            if not isinstance(spec, dict):
                raise GateOfflineError("tier %s malformed (AC-M1)" % key)
            try:
                monthly = int(spec.get("monthly_credits", 0))
                days = int(spec.get("period_days", 0))
                grace = int(spec.get("grace_days", 0))
            except (TypeError, ValueError):
                raise GateOfflineError(
                    "tier %s non-integer numeric fields (AC-M1)" % key) from None
            if monthly <= 0:
                raise GateOfflineError(
                    "tier %s monthly_credits not a positive int (AC-M1)" % key)
            if days <= 0:
                raise GateOfflineError("tier %s period_days not positive" % key)
            if grace < 0:
                raise GateOfflineError("tier %s grace_days negative" % key)
            privs = spec.get("privileges")
            if not isinstance(privs, list) or not privs:
                raise GateOfflineError("tier %s privileges missing (AC-M1)" % key)
            for priv in privs:
                if str(priv) not in KNOWN_PRIVILEGES:
                    raise GateOfflineError(
                        "tier %s unknown privilege key %s (AC-M1)" % (key, priv))
            copy = str(spec.get("copy", ""))
            if not copy:
                raise GateOfflineError("tier %s copy missing (AC-M1)" % key)
            hit = next((w for w in bans if w and w in copy), None)
            if hit is not None:
                # AC-M15: banned marketing copy = the whole config is
                # refused, the tier never opens (fail closed)
                raise GateOfflineError(
                    "tier %s copy banned (AC-M15): %s" % (key, hit))
            tiers[str(key)] = Tier(str(key), monthly, days, grace,
                                   [str(p) for p in privs], copy)
        products_cfg = config.get("products")
        if not isinstance(products_cfg, dict) or not products_cfg:
            raise GateOfflineError("products entitlement map missing (AC-M1)")
        products = {}
        for ent, spec in products_cfg.items():
            if not isinstance(spec, dict):
                raise GateOfflineError("product %s malformed (AC-M1)" % ent)
            tier_key = str(spec.get("tier", ""))
            if tier_key not in tiers:
                raise GateOfflineError(
                    "product %s maps to unknown tier %s (AC-M1)" % (ent, tier_key))
            products[str(ent)] = tiers[tier_key]
        vouchers_cfg = config.get("vouchers") or {}
        if not isinstance(vouchers_cfg, dict):
            raise GateOfflineError("vouchers section malformed (AC-M16)")
        vouchers = {}
        for vtype, spec in vouchers_cfg.items():
            if not isinstance(spec, dict):
                raise GateOfflineError("voucher %s malformed (AC-M16)" % vtype)
            priv = str(spec.get("privilege", ""))
            if priv not in KNOWN_PRIVILEGES:
                raise GateOfflineError(
                    "voucher %s unknown privilege %s (AC-M1)" % (vtype, priv))
            vouchers[str(vtype)] = priv
        return cls(gate, disclaimer, ai_label, bans, tiers, products, vouchers)
