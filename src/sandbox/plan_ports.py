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

TWO FACES ARE OUT OF THIS PREDICATE'S RANGE, NAMED RATHER THAN IMPLIED

The predicate judges a port MAP. It cannot know where the numbers came from, so
an allocator that ignores its used-set is refused only by the suite arm that
wires such a stand-in in (AC-STL13), not by the predicate alone. And explicit
overrides are added to the used-set but never compared with EACH OTHER - the
probe measured plan({"ws": 7000, "city": 7000}) reading 7000 twice - so an
override collision is a live gap this module names and does not close.

The suite that pins this lives in test_start_all.py as AC-STL12..AC-STL13.

Usage (pure, stdlib only, no clock, no network, no shell):

    from plan_ports import port_plan_coverage, duplicate_ports
    verdict = port_plan_coverage(start_all.plan("127.0.0.1"),
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
