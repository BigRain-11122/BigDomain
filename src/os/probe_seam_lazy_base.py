"""Lazy base-row plumbing shared by the probe-seam entry chain.

An entry used to ask its parent TWICE: once untended, for the base_* counter-
factual, and once patched, for the shipped answer. Depth d therefore cost about
2**d parent entries - R2866 measured 258 live entry calls for one 6-criterion
fixture and a single deep row cost 245.4s.

The counterfactual has no consumer on the hot path: every upper entry reads
only state / value / reason / ma_chain / branch_reads from the row it gets, and
never its parent base_* keys. So the untended walk is made LAZY here - it runs
at most once, and only when someone actually reads a base key.

Removal, not hiding: a plain module-level helper would still run twice per
level and only change what a source counter sees, which AC-FO1 forbids and
R2871 refused. The proof is the seconds (AC-LZ4) plus the equality (AC-LZ2),
not the counter.

The dict(got) trap R2871 named is handled in LazyRow itself: a row built FROM
another LazyRow inherits that row pending producers, so the bottom-most base key
still answers at the top of the chain instead of silently disappearing.

Pure ASCII, stdlib only, no clock, zero network.
"""


class Once(object):
    """Run a producer at most once and hand back the same value."""

    def __init__(self, producer):
        self._producer = producer
        self._done = False
        self._value = None

    def __call__(self):
        if not self._done:
            self._value = self._producer()
            self._done = True
        return self._value


class LazyRow(dict):
    """A row whose base_* keys are produced only when they are read.

    A plain dict copy would drop another LazyRow pending keys - the trap R2871
    wrote down - so __init__ carries them forward instead.
    """

    def __init__(self, source=None):
        dict.__init__(self)
        self._pending = {}
        if source is not None:
            dict.update(self, source)
            if isinstance(source, LazyRow):
                self._pending.update(source._pending)

    def defer(self, key, producer):
        """Register `key` to be produced by `producer` on first read."""
        self._pending[key] = producer

    def _fill(self, key):
        producer = self._pending.pop(key, None)
        if producer is None:
            raise KeyError(key)
        value = producer()
        dict.__setitem__(self, key, value)
        return value

    def __missing__(self, key):
        if key in self._pending:
            return self._fill(key)
        raise KeyError(key)

    def get(self, key, default=None):
        if dict.__contains__(self, key):
            return dict.__getitem__(self, key)
        if key in self._pending:
            return self._fill(key)
        return default

    def __contains__(self, key):
        return dict.__contains__(self, key) or key in self._pending

    def copy(self):
        return LazyRow(self)


def pending_keys(row):
    """The base keys a row can still answer, for evidence and tests."""
    if not isinstance(row, LazyRow):
        return []
    return sorted(row._pending)
