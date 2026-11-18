"""Anti-decay assertion: one plan() call hands every plan key a distinct port.

WHY THIS MODULE EXISTS

start_all.plan() walks PLAN_KEYS once per call and asks free_port for a port for
every key that was not given an explicit override. free_port binds a loopback
ephemeral socket, reads the number the OS handed back, and refuses any number
already in the run's used-set - which is what keeps two keys in ONE call from
sharing a port. That refusal is the whole mechanism, and until this round
nothing pinned it: the suite R2977 added measures the face->port-key MAPPING
(AC-KOC11 arm 4) and deliberately passes a fully explicit override map, so the
allocator itself was never exercised by a criterion. An edit that made
free_port stop consulting its used-set - or a plan() rewritten to ask for ports
before the set is filled - would have passed every existing suite.

R2979 measured the live tree before pinning this (tmp/probe_R2979.py): ten keys,
ten distinct ports, 64480..64489 on this box, and a stuck-socket stand-in with
used={7000} raising E_NO_FREE_PORT while the same stand-in with an empty set
returned 7000. So today there is no live defect - this round buys a red line,
not a repair.

WHAT THIS IS, AND WHAT IT IS NOT

This is an ANTI-DECAY ASSERTION, not a security boundary. It binds no socket,
reads no request path, grants nothing and refuses nothing at run time; plan()
does not import it and never consults it. Its only job is to make "two keys got
one port" a red criterion on the day an edit produces it.

TWO FACES ARE OUT OF THE ALLOCATOR PREDICATE'S RANGE, NAMED NOT IMPLIED

port_plan_coverage judges a port MAP. It cannot know where the numbers came
from, so an allocator that ignores its used-set is refused only by the suite arm
that wires such a stand-in in (AC-STL13), not by the predicate alone.

R2980 answers the OVERRIDE face separately, because plan() treats explicit
overrides differently from auto-assigned ports: an override is written into the
ports map and added to the used-set, but overrides are never compared with each
OTHER. Measured before this round was pinned (R2979 probe): plan({"ws": 7000,
"city": 7000}) returns 7000 for both keys. So a caller naming one number twice
is refused nowhere; it fails later and loudly, when the second process cannot
bind (E_NOT_UP).

THE DECISION IS CRITERION-FIRST, ZERO RUN-TIME CHANGE

Making plan() raise on a colliding override map would change the command line
surface (single-key --ws-port/--hub-port overrides are the normal shape) and
needs the whole call face measured first. So this round ships a PREDICATE and
lets the battery go red on the edit; plan() keeps its present behaviour, named
here rather than presented as a repair.

A SECOND FACE MEASURED THIS ROUND: plan() iterates PLAN_KEYS and calls
overrides.get(key), so a key the override map carries but the plan does not
("wss" for "ws") is dropped without a word - the launcher allocates a fresh
port and never mentions the typo. override_coverage names such keys as
`unknown` instead of reading healthy on the keys it kept.

The suite that pins all of this lives in test_start_all.py as
AC-STL12..AC-STL15.

Usage (pure, stdlib only, no clock, no network, no shell):

    from plan_ports import port_plan_coverage, duplicate_ports
    verdict = port_plan_coverage(start_all.plan("127.0.0.1"),
                                 start_all.PLAN_KEYS)

    from plan_ports import override_coverage
    spelled = override_coverage({"ws": 7000, "hub": 7001},
                                start_all.PLAN_KEYS)
"""


def duplicate_ports(ports, keys=None):
    """The ports carried by more than one key, with the keys named.

    ``keys`` defaults to every key the mapping has; a caller that wants one
    plan's keys judges exactly those. The answer is a sorted tuple of
    (port, keys) pairs with keys sorted too, so a three-way collision names all
    three rather than folding into a boolean. Values are compared as ints,
    because the launcher stores ints and a stringified port that compares
    unequal to its own number would hide the very collision judged here.
    """
    mapping = dict(ports)
    keys = tuple(sorted(mapping)) if keys is None else tuple(keys)
    carried = {}
    for key in keys:
        carried.setdefault(int(mapping[key]), []).append(key)
    return tuple(sorted((port, tuple(sorted(names)))
                        for port, names in carried.items()
                        if len(names) > 1))


def port_plan_coverage(ports, keys=None):
    """The verdict for port uniqueness: ok plus the facts behind it.

    ``ok`` is True exactly when every requested key is present and no port is
    carried by two of them. ``missing`` names requested keys the mapping does
    not have, because a plan that silently dropped a key would otherwise read
    healthy on the keys it kept. ``duplicates`` names each colliding port with
    its keys - the only part of a failure a reader can act on. A one-key or
    empty plan is healthy by construction: the failure this predicate exists
    for needs at least two keys pointing at one port.
    """
    mapping = dict(ports)
    keys = tuple(sorted(mapping)) if keys is None else tuple(keys)
    missing = tuple(sorted(key for key in keys if key not in mapping))
    present = tuple(key for key in keys if key in mapping)
    duplicates = duplicate_ports(mapping, present)
    values = [int(mapping[key]) for key in present]
    return {
        "ok": not missing and not duplicates,
        "keys": tuple(sorted(keys)),
        "count": len(present),
        "distinct": len(set(values)),
        "missing": missing,
        "duplicates": duplicates,
    }


def override_collisions(overrides):
    """The ports carried by more than one override key, with the keys named.

    Values are compared as ints because plan() stores int(given); a stringified
    "7000" and an int 7000 are the same number to the launcher and must be the
    same number here, or the predicate would read healthy on the very pair the
    launcher hands one port. The answer is a sorted tuple of (port, keys) with
    keys sorted, so a three-way collision names all three.
    """
    carried = {}
    for key in sorted(overrides):
        try:
            port = int(overrides[key])
        except (TypeError, ValueError):
            continue
        carried.setdefault(port, []).append(key)
    return tuple(sorted((port, tuple(sorted(names)))
                        for port, names in carried.items()
                        if len(names) > 1))


def override_coverage(overrides, plan_keys=None):
    """The verdict for an override map: ok plus the facts behind it.

    A map is healthy when every key it names is a plan key, every value is a
    number, and no two keys name the same number. ``unknown`` names keys the
    plan does not carry - plan() drops those in silence, so a typo would
    otherwise read healthy while the launcher allocated a fresh port.
    ``bad`` names values that cannot be read as a port, which plan() would hit
    as a TypeError later rather than here.
    """
    mapping = dict(overrides)
    keys = tuple(sorted(mapping))
    unknown = ()
    if plan_keys is not None:
        plan_keys = tuple(plan_keys)
        unknown = tuple(key for key in keys if key not in plan_keys)
    bad = []
    for key in keys:
        try:
            int(mapping[key])
        except (TypeError, ValueError):
            bad.append(key)
    duplicates = override_collisions(mapping)
    values = []
    for key in keys:
        if key in bad:
            continue
        values.append(int(mapping[key]))
    return {
        "ok": not unknown and not duplicates and not bad,
        "keys": keys,
        "count": len(keys),
        "distinct": len(set(values)),
        "unknown": unknown,
        "bad": tuple(bad),
        "duplicates": duplicates,
    }
