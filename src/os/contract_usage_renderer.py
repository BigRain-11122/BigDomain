"""contract_usage_renderer (R2373; criteria AC-CUR1..AC-CUR6 were pinned
inside the R2366 tech seed row of state/queue/tech.md:419 BEFORE this code).

Why this exists: two CLIs answered a usage question from the SAME runner
contract through two different formatters. runner_arg_guard.usage_text renders

    usage: reconcile_all.py [evidence_log_path]
    known flags: (none)

and battery_followup_help_wire renders a second block whose house line reads

    house contract: reconcile_all.py [evidence_log_path] flags=(none)

Both texts are already published and must not change (AC-CUR2), but the
vocabulary behind them - which keys a contract must carry, how a flag list is
spelled, and the honest "(none)" for an empty set - had two owners. A third
tool would have made three. This module is the ONE owner of that vocabulary.

Two LINE SHAPES live here and nowhere else, because the two published texts
genuinely differ:

    block()  - the two-line form the guard shows (lead "usage:")
    inline() - the one-line form the wire shows (lead "house contract:")

The format strings below are the only ones in the tree for this shape: the
guard writes none and the wire writes none, so a change here moves both CLIs
(AC-CUR1). A contract that lost a key refuses with its own code instead of
rendering a partial block (AC-CUR3), and an empty flag set reads the honest
"(none)" in both shapes (AC-CUR4).

Stdlib only, ASCII source, zero network, no clock, read-only: this module
formats a mapping and touches nothing else.
"""

KEYS = ("name", "positional_label", "known_flags")

USAGE_LEAD = "usage:"
FLAGS_LEAD = "known flags:"
HOUSE_LEAD = "house contract:"
NONE = "(none)"

E_CUR_CONTRACT = "E_CUR_CONTRACT"
E_CUR_MISSING = "E_CUR_CONTRACT_MISSING_"
E_CUR_BAD_FLAGS = "E_CUR_CONTRACT_BAD_KNOWN_FLAGS"


class ContractUsageError(Exception):
    """A contract that cannot be rendered honestly."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def fields(contract):
    """The three keys this renderer reads, validated once, for both shapes."""
    if not isinstance(contract, dict):
        raise ContractUsageError(E_CUR_CONTRACT, "contract is not a mapping")
    for key in KEYS:
        if key not in contract:
            raise ContractUsageError(E_CUR_MISSING + key.upper(), key)
    flags = contract["known_flags"]
    if isinstance(flags, str) or not isinstance(flags, (list, tuple)):
        raise ContractUsageError(E_CUR_BAD_FLAGS, type(flags).__name__)
    return str(contract["name"]), str(contract["positional_label"]), \
        tuple(flags)


def flag_text(contract):
    """One spelling for a flag set, so the empty case has one owner."""
    _name, _pos, flags = fields(contract)
    return " ".join(flags) if flags else NONE


def block(contract, lead=USAGE_LEAD, flags_lead=FLAGS_LEAD):
    """The two-line shape: '<lead> NAME [POS]' then '<flags_lead> FLAGS'."""
    name, pos, _flags = fields(contract)
    return "%s %s [%s]\n%s %s" % (lead, name, pos, flags_lead,
                                  flag_text(contract))


def inline(contract, lead=HOUSE_LEAD):
    """The one-line shape: '<lead> NAME [POS] flags=FLAGS'."""
    name, pos, _flags = fields(contract)
    return "%s %s [%s] flags=%s" % (lead, name, pos, flag_text(contract))