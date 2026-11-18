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

Usage (pure, stdlib only, no clock, no network, no shell):

    from face_coverage import coverage, unowned_startable
    verdict = coverage(panel.FACE_IDS, start_all.FACE_KEYS)

The suite that pins this lives in test_kill_on_close.py as AC-KOC9..AC-KOC10.
"""


def unowned_startable(startable, owned):
    """The faces a panel may start that the launcher does not serve.

    Order and repetition in the inputs carry no meaning here: both are read as
    sets, so a face named twice is one face (duplication is not a coverage
    failure) and the answer is a sorted tuple, which is stable across runs and
    therefore comparable byte for byte in evidence.
    """
    return tuple(sorted(set(startable) - set(owned)))


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
