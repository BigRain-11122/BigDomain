"""own_usage_block_renderer (R2383; criteria AC-OUB1..AC-OUB6 were pinned
inside the R2373 tech seed row of state/queue/tech.md:429 BEFORE this code).

Why this exists: R2373 collapsed the IMPORTED runner contract to one owner
(contract_usage_renderer), but a tool's OWN argument block still had none.
Measured at HEAD before this window:

    runner_arg_guard.guard_usage()   returned a hand-written literal
    battery_followup_help_wire.usage_text()  composed its own flag line from
                                     format strings inside that module

so a third tool describing ITS OWN flags had to copy one of those two shapes.
This module is the ONE owner of that own-block vocabulary: the lead, the
continuation indent, the derived metavar, the positional marker and the
honest "(none)" for an empty own-flag set.

Both published texts are already on disk and must not change (AC-OUB2), so
this module reproduces them exactly:

    usage: runner_arg_guard.py [--json] [--] <runner argv ...>
           runner_arg_guard.py --guard-help

    usage: battery_followup.py --evidence EVIDENCE --label LABEL --root ROOT
    --round ROUND --dry-run --json [--help]

The metavar is DERIVED from the option key (own_usage_block_renderer specs
carry the parser's own table), so a placeholder cannot drift from the table;
a value flag with no metavar renders as the bare flag rather than a partial
line (AC-OUB3), and a tool with no own flags reads "(none)" (AC-OUB4).

Stdlib only, ASCII source, zero network, no clock, read-only: this module
formats a mapping and touches nothing else.
"""

LEAD = "usage:"
CONTINUATION = "       "
NONE = "(none)"
POSITIONAL_MARK = "[--]"

E_OUB_SPEC = "E_OUB_BAD_SPEC"
E_OUB_TABLE = "E_OUB_BAD_TABLE"


class OwnUsageError(Exception):
    """A spec that cannot be rendered honestly."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _spec(spec):
    if not isinstance(spec, dict):
        raise OwnUsageError(E_OUB_SPEC, type(spec).__name__)
    name = spec.get("name")
    if not isinstance(name, str) or not name:
        raise OwnUsageError(E_OUB_SPEC, "name")
    return spec, name


def _sequence(value, key):
    """A flag / line table as an ordered tuple, or its own refusal."""
    if value is None:
        return ()
    if isinstance(value, dict):
        return tuple(str(item) for item in sorted(value))
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    raise OwnUsageError(E_OUB_TABLE, "%s is %s" % (key, type(value).__name__))


def _takes(value):
    """The value-flag table as (flag, metavar-source) pairs in flag order."""
    if value is None:
        return ()
    if not isinstance(value, dict):
        raise OwnUsageError(E_OUB_TABLE, "takes is %s" % type(value).__name__)
    return tuple((str(flag), value[flag]) for flag in sorted(value))


def parts(spec):
    """The token list of ONE own-block head, in the published order.

    AC-OUB2 forces TWO flag spellings to stay alive, because the two published
    texts genuinely differ: the guard brackets its own flags (`[--json]`) and
    the wire does not (`--json`). The spelling is a spec field, so the shape is
    still owned here and a third tool declares which of the two it publishes.
    """
    _spec(spec)
    brackets = bool(spec.get("brackets"))
    tokens = []

    def spell(text):
        return "[%s]" % text if brackets else text

    for flag, metavar in _takes(spec.get("takes")):
        text = str(metavar).upper() if metavar else ""
        tokens.append(spell("%s %s" % (flag, text) if text else flag))
    for flag in _sequence(spec.get("flags"), "flags"):
        tokens.append(spell(flag))
    positional = spec.get("positional")
    if positional:
        tokens.append(POSITIONAL_MARK)
        tokens.append(str(positional))
    help_flag = spec.get("help")
    if help_flag:
        tokens.append(str(help_flag))
    return tuple(tokens)


def head(spec):
    """The '<lead> NAME ...' line, or the honest '(none)' when there is none."""
    _spec(spec)
    name = spec["name"]
    tokens = parts(spec)
    tail = (" " + " ".join(tokens)) if tokens else (" " + NONE)
    return "%s %s%s" % (LEAD, name, tail)


def block(spec):
    """The whole own block: head, continuation lines, then the prose lines."""
    _spec(spec)
    lines = [head(spec)]
    for line in _sequence(spec.get("extra"), "extra"):
        lines.append(CONTINUATION + line)
    lines.extend(_sequence(spec.get("prose"), "prose"))
    return "\n".join(lines)