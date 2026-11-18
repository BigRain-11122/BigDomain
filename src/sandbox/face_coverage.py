"""Anti-decay assertion: every face the panel can start is one the launcher owns.

WHY THIS MODULE EXISTS

R2975 measured the shipped chain honestly: with a real launcher serving, every
face the control panel could start answered 409 E_PANEL_OWNED_BY_LAUNCHER, no
panel child was ever born, and therefore the shipped tree has no grandchild
process to be reached or missed by the launcher's kill-on-close job. That
result, however, rests on two constants agreeing:

    panel.FACE_IDS      the five faces the panel may start
    start_all.FACE_KEYS the eight faces the launcher serves and declares owned

The measured difference was empty, and NOTHING pinned it. Both files could be
edited independently and every existing suite would stay green: the launcher
would simply stop declaring a face it never served, and the panel would gain a
startable face under a serving launcher - which is precisely the shape R2975
concluded could not occur on this tree. A guarantee that decays silently when
an unrelated constant is edited is not a guarantee, it is a coincidence with a
green suite beside it.

WHAT THIS IS, AND WHAT IT IS NOT

This is an ANTI-DECAY ASSERTION, not a security boundary. It grants nothing,
refuses nothing at run time, and no request path consults it. It does not
authenticate, authorise, rate-limit or gate anything, and a caller that ignores
its verdict loses no protection it ever had. Its only job is to make the
relation itself a red line on the day it breaks, so the failure reads
"panel can start X, the launcher does not own X" instead of a route returning
an unexpected status code.

THE RELATION IS ONE-DIRECTIONAL

The launcher owning MORE faces than the panel can start is normal and expected
(today: city, gate and panel are served but not startable). Only a startable
face the launcher does not own is a failure, so the verdict is computed as a
set difference in that one direction and never as an equality of the two sets.

THE SECOND HOP HAS TWO HALVES, AND R2976 PINNED ONLY ONE

R2976 asserted that every owned face has a port key drawn from the plan:
FACE_PORT_KEY covers FACE_KEYS exactly, and every value is a PLAN_KEYS item.
What that leaves unpinned is that the keys are DISTINCT. Two faces mapped to
the same plan key are still "covered" by that assertion, while the launcher's
plan() issues one port per plan key - so both faces would be handed the same
port, the first start would win it, and the second would fail with E_NOT_UP.
That is a loud failure and not a silent misroute, which is why this round
closes it as a predicted-red line rather than a security repair: today's map
happens to be distinct (measured: eight faces, eight distinct keys), and
nothing stops an ordinary edit from making it collide.

This is still the same anti-decay assertion and still NOT a security boundary.
It binds no socket, reads no request path, grants and refuses nothing at run
time; a caller that ignores it loses no protection it ever had. The difference
it makes is which failure is visible: "two faces want one socket" instead of a
launcher log line saying E_NOT_UP on a face nobody was editing.

Usage (pure, stdlib only, no clock, no network, no shell):

    from face_coverage import coverage, unowned_startable, port_coverage
    verdict = coverage(panel.FACE_IDS, start_all.FACE_KEYS)
    ports = port_coverage(start_all.FACE_PORT_KEY)

The suite that pins this lives in test_kill_on_close.py as AC-KOC9..AC-KOC12.
"""


def unowned_startable(startable, owned):
    """The faces a panel may start that the launcher does not serve.

    Order and repetition in the inputs carry no meaning here: both are read as
    sets, so a face named twice is one face (duplication is not a coverage
    failure) and the answer is a sorted tuple, which is stable across runs and
    therefore comparable byte for byte in evidence.
    """
    return tuple(sorted(set(startable) - set(owned)))


def shared_port_keys(face_port_key):
    """The plan keys carried by more than one face, with the faces named.

    Input is read as a mapping of face -> plan key, exactly the shape the
    launcher publishes. The answer is a sorted tuple of (plan key, faces)
    pairs, faces sorted too, so a three-way collision names all three rather
    than folding into a boolean. An empty answer means no key is shared,
    which is the healthy state; one face per key is not required to be
    unique in name, only its key is.
    """
    carried = {}
    for face, key in dict(face_port_key).items():
        carried.setdefault(key, []).append(face)
    return tuple(sorted((key, tuple(sorted(faces)))
                        for key, faces in carried.items()
                        if len(faces) > 1))


def port_coverage(face_port_key):
    """The verdict for port-key uniqueness: ok plus the facts behind it.

    ``ok`` is True exactly when no plan key is carried by two faces.
    ``faces`` names every face the mapping covers and ``shared`` names each
    colliding key with its faces, because "which pair collides" is the only
    part of a failure a reader can act on. A mapping that covers one face, or
    none, is healthy by construction; the failure this predicate exists for
    needs at least two faces pointing at one port.
    """
    shared = shared_port_keys(face_port_key)
    return {
        "ok": not shared,
        "faces": tuple(sorted(dict(face_port_key))),
        "shared": shared,
    }


def coverage(startable, owned):
    """The verdict object: ok plus the three sets it was derived from.

    ``ok`` is True exactly when no startable face is unowned. ``unowned`` names
    every offender individually rather than folding them into the boolean,
    because "which constant broke" is the only part of a failure that a reader
    can act on.
    """
    unowned = unowned_startable(startable, owned)
    return {
        "ok": not unowned,
        "startable": tuple(sorted(set(startable))),
        "owned": tuple(sorted(set(owned))),
        "unowned": unowned,
    }
