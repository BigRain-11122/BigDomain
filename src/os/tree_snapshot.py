"""tree_snapshot - leave the tracked tree exactly as the caller found it.

WHY THIS EXISTS: docs/status-export.json's latest_artifact is derived by
export_round from the NEWEST preview/X.html + X.json pair on disk, ordered by
mtime. Measured at R2875 in the real tree: setting one tracked non-board pair's
mtime forward flips `export_round.py --check` from VERDICT PASS to
"VERDICT FAIL 1 / AC-EXPW1 latest_artifact is not the newest product pair on
disk", and restoring the recorded st_atime_ns/st_mtime_ns flips it back. So any
fixture that re-renders a tracked pair MOVES the world another suite measures:
the two suites are green alone and order-dependent together.

The law this module makes cheap: a battery may LOOK at the tracked tree, so it
must leave it as it found it - bytes AND mtime. `restored(paths)` records
(path -> bytes, atime_ns, mtime_ns) at entry and writes them back at exit,
including on the exception path, re-raising the body's own exception unchanged.

Two choices are deliberate and were scored in src/os/backlog.md at R2875:
  * bytes are restored too, not only mtime - a suite that leaves a tracked file
    changed also leaves `git status` dirty, which is how this loop decides
    whether another actor is writing the repository;
  * the alternative "the shard re-derives the face as its closing step" is
    rejected: greening a face by writing the document it measures cannot tell a
    stale face from a fresh one.

It stores what it finds. It reads no wall clock and touches no network.
"""
import io
import os
import sys

__all__ = ['Snapshot', 'restored']


def _read_bytes(path):
    with open(path, 'rb') as handle:
        return handle.read()


class Snapshot(object):
    """Record paths at entry, restore bytes and mtime at exit.

    Absent paths are recorded as absent and are NEVER created by restore, so a
    fixture cannot smuggle a file into the tracked tree by way of a cleanup.
    """

    def __init__(self, paths):
        self.paths = [os.fspath(p) for p in paths]
        self._saved = []
        self.changed = []
        self.absent = []
        self.removed = []

    def __enter__(self):
        for path in self.paths:
            if os.path.isfile(path):
                st = os.stat(path)
                self._saved.append((path, _read_bytes(path),
                                    st.st_atime_ns, st.st_mtime_ns))
            else:
                self.absent.append(path)
        return self

    def restore(self):
        """Put every recorded file back; report which ones had moved.

        A path that was ABSENT at entry and exists now was created by the body,
        so it is removed: leaving it behind is the same side effect as leaving
        changed bytes, and it would make `git status` dirty for the next actor.
        """
        for path, data, atime_ns, mtime_ns in self._saved:
            now = _read_bytes(path) if os.path.isfile(path) else None
            if now != data:
                self.changed.append(path)
                with open(path, 'wb') as handle:
                    handle.write(data)
            os.utime(path, ns=(atime_ns, mtime_ns))
        for path in self.absent:
            if os.path.isfile(path):
                os.remove(path)
                self.removed.append(path)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.restore()
        return False


def restored(paths):
    """Context manager form: `with restored([p]) as snap: ...`."""
    return Snapshot(paths)


def main(argv):
    if '--self-check' not in argv:
        sys.stderr.write('usage: tree_snapshot.py --self-check\n')
        return 2
    import tempfile
    here = None
    try:
        fd, here = tempfile.mkstemp(prefix='tsnap-self-')
        os.close(fd)
        with io.open(here, 'wb') as handle:
            handle.write(b'payload\n')
        os.utime(here, ns=(1000000000, 2000000000))
        with restored([here]) as snap:
            with io.open(here, 'wb') as handle:
                handle.write(b'changed\n')
            os.utime(here, ns=(3000000000, 4000000000))
        st = os.stat(here)
        data = _read_bytes(here)
        ok = (data == b'payload\n' and st.st_mtime_ns == 2000000000
              and st.st_atime_ns == 1000000000 and snap.changed == [here])
        sys.stdout.write('%s bytes_restored=%s mtime_restored=%s\n'
                         % ('VERDICT PASS' if ok else 'VERDICT FAIL',
                            data == b'payload\n',
                            st.st_mtime_ns == 2000000000))
        return 0 if ok else 2
    finally:
        if here and os.path.isfile(here):
            os.remove(here)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
