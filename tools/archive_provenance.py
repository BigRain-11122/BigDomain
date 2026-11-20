"""Name which ledger archives git actually tracks, without spawning git.

R3091 measured the question the FOLD-CARRY line leaves open: a published
marker line is only as stable as the archive's provenance, and git backs
only ONE of the three archives (November: 137 commits, +5498/-0; September
and October: 0 commits, excluded by the 'logs/' ignore rule). Until now the
only way to read that was 'git ls-files', i.e. a child process - which no
gate here may spawn, and which a reader on a locked tree cannot run.

The repository's own index IS git's definition of "tracked", and the
standard library can read it: the probe for this round parsed the live
index (656872B, 6666 entries) and agreed with 'git ls-files logs' on all
three rows, exactly. So this face reads .git/index and nothing else.

Reader scope (deliberate): DIRC version 2 only. Versions 3 and 4 carry
extension records and path compression; guessing them would be a shape
read this repository refuses. A non-2 index is refused by name instead.

Output is ASCII, one line per archive then a summary:

  ARCHIVE <name> bytes=<n> tracked=yes|no
  PROVENANCE files=<n> tracked=<n> untracked=<n> source=.git/index

Refusals print one 'E_APR_*' line on stderr and write nothing (rc=2):
  E_APR_NO_INDEX   the repository has no .git/index
  E_APR_BAD_INDEX  the file does not start with DIRC / is truncated
  E_APR_VERSION    the index is not version 2
  E_APR_NO_DIR     the requested directory is not there
"""

import json
import os
import sys

NO_INDEX = "E_APR_NO_INDEX"
BAD_INDEX = "E_APR_BAD_INDEX"
BAD_VERSION = "E_APR_VERSION"
NO_DIR = "E_APR_NO_DIR"


class ProvenanceError(Exception):
    """One named refusal; nothing is written when this is raised."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def read_index(path):
    """Return (tracked_paths, stats) for a version-2 DIRC index."""
    if not os.path.isfile(path):
        raise ProvenanceError(NO_INDEX, "no index at %s" % path)
    handle = open(path, "rb")
    try:
        blob = handle.read()
    finally:
        handle.close()
    if len(blob) < 12 or blob[:4] != b"DIRC":
        raise ProvenanceError(BAD_INDEX, "%s is not a DIRC index" % path)
    version = int.from_bytes(blob[4:8], "big")
    count = int.from_bytes(blob[8:12], "big")
    if version != 2:
        raise ProvenanceError(BAD_VERSION,
                              "index version %d is not 2" % version)
    pos = 12
    tracked = set()
    for _ in range(count):
        start = pos
        pos += 62  # 10 stat words + object id + 2 flag bytes
        if pos > len(blob):
            raise ProvenanceError(BAD_INDEX,
                                  "truncated at entry %d" % (len(tracked) + 1))
        end = blob.find(b"\x00", pos)
        if end < 0:
            raise ProvenanceError(BAD_INDEX, "unterminated path")
        tracked.add(blob[pos:end].decode("utf-8", "surrogateescape"))
        length = end - start + 1
        pos = start + length + (8 - length % 8) % 8
    return tracked, {"index_bytes": len(blob), "entries": count}


def archive_rows(repo_root, rel_dir, prefix):
    """One row per file under rel_dir carrying prefix, measured on disk."""
    full = os.path.join(repo_root, rel_dir)
    if not os.path.isdir(full):
        raise ProvenanceError(NO_DIR, "%s is not a directory" % full)
    tracked, stats = read_index(os.path.join(repo_root, ".git", "index"))
    rows = []
    for name in sorted(os.listdir(full)):
        if not name.startswith(prefix):
            continue
        rel = "%s/%s" % (rel_dir.replace("\\", "/"), name)
        rows.append({"file": name,
                     "rel": rel,
                     "bytes": os.path.getsize(os.path.join(full, name)),
                     "tracked": rel in tracked})
    return rows, stats


def format_rows(rows, stats):
    """ASCII, one line per row, then the summary line."""
    lines = ["ARCHIVE %s bytes=%d tracked=%s"
             % (row["file"], row["bytes"],
                "yes" if row["tracked"] else "no") for row in rows]
    hits = sum(1 for row in rows if row["tracked"])
    lines.append("PROVENANCE files=%d tracked=%d untracked=%d source=.git/index"
                 % (len(rows), hits, len(rows) - hits))
    return "\n".join(lines)


def main(argv):
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rel_dir = "logs"
    prefix = "state-log-archive-"
    as_json = False
    args = list(argv[1:])
    while args:
        arg = args.pop(0)
        if arg == "--repo" and args:
            repo = args.pop(0)
        elif arg == "--dir" and args:
            rel_dir = args.pop(0)
        elif arg == "--prefix" and args:
            prefix = args.pop(0)
        elif arg == "--json":
            as_json = True
        else:
            sys.stderr.write("E_APR_BAD_ARGS: unknown argument %r\n" % arg)
            return 2
    try:
        rows, stats = archive_rows(repo, rel_dir, prefix)
    except ProvenanceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc.detail))
        return 2
    if as_json:
        payload = {"source": ".git/index",
                   "index_bytes": stats["index_bytes"],
                   "index_entries": stats["entries"],
                   "archives": rows}
        sys.stdout.write(json.dumps(payload, sort_keys=True) + "\n")
    else:
        sys.stdout.write(format_rows(rows, stats) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
