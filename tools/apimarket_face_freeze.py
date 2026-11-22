"""Pin the 13 apimarket report faces that have no reproducible generator.

WHY THIS EXISTS (R3289, criteria AC-AMF1..AC-AMF6, registered in
src/os/backlog.md BEFORE this file):

`src/sandbox/ledger/apimarket_report.py` renders one page per `--out`.
Seventeen `preview/apimarket-report-*.html` faces sit on disk. Four of
them have a dedicated preview generator under `src/os/` (refunds,
questions, buyerquestions, selleranswers). The other thirteen were
rendered ad hoc from the per-feature test worlds (each test builds its
own temp sqlite database) and nothing on disk names their paths, so no
script can re-create them.

A re-render today would emit REPORT_SCHEMA 17, and nine of those
thirteen carry older schemas (2,3,4,5,9,10,14,15). A derived render can
therefore NEVER equal the pinned bytes: the only honest check is a
freeze, not a re-derivation. Editing the pages would also erase the one
record of which schema revision produced each face.

So this tool records bytes + sha256 + schema_version per face in one
manifest and refuses DRIFT by name. It does not make the faces
reproducible and does not claim to: a freeze makes silent drift visible,
nothing more. A later round may still decide to rebuild them at schema
17 (destroying the historical snapshots) or retire them.

AC-AMF1 coverage   every preview/apimarket-report-*.html is listed
                   exactly once, either as a frozen face or as an
                   excluded generator-backed face; an unlisted page is
                   red, so the family cannot grow silently.
AC-AMF2 pin        each frozen face's html bytes and sha256 equal the
                   disk bytes; when a json sibling is recorded, its
                   bytes and sha256 must match too.
AC-AMF3 schema     the recorded schema_version equals the sibling json's
                   schema_version (null when no sibling), so a re-render
                   at a different schema is named rather than absorbed.
AC-AMF4 grave      a frozen face whose html is gone from disk is red -
                   the manifest may not keep a claim about a missing page.
AC-AMF5 exclusion  every excluded face names a producer script that is
                   on disk and is a preview_*.py generator; an exclusion
                   with no proof is red.
AC-AMF6 degenerate an empty or short manifest is red (13 frozen faces,
                   schema 1), so a blank manifest cannot PASS.

Usage:
    python tools/apimarket_face_freeze.py --write
    python tools/apimarket_face_freeze.py --check
    python tools/apimarket_face_freeze.py --check --preview DIR --out FILE

--write touches only the manifest. --check reads only and exits 2 on any
failure. ASCII source.
"""

import argparse
import hashlib
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(ROOT, "preview")
MANIFEST = os.path.join(ROOT, "state", "apimarket-face-freeze.json")

MANIFEST_SCHEMA = 1

# Frozen in the order the board named them. These are historical
# snapshots rendered at schema 2..17; no script on disk names their
# paths, so their bytes are the only record.
FROZEN = (
    "activity", "attention", "buyers", "claims", "claims-demo", "csv",
    "demand", "dossiers", "duty", "json", "quality", "slowanswer",
    "workbench",
)

# Generator-backed faces, each with the preview script that re-renders
# it. Excluding them is a claim about disk facts, so AC-AMF5 reads the
# producer path back.
EXCLUDED = (
    ("buyerquestions", "src/os/preview_R2119.py"),
    ("questions", "src/os/preview_R2118.py"),
    ("refunds", "src/os/preview_R2111.py"),
    ("selleranswers", "src/os/preview_R2120.py"),
)

WHY = ("13 faces were rendered ad hoc from per-feature temp databases;"
       " the generator is at REPORT_SCHEMA 17 and 9 of them carry older"
       " schemas, so a fresh render can never equal these bytes."
       " Pinned, not reproducible: this makes drift visible, nothing more.")


def sha256(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def face_paths(preview, slug):
    return (os.path.join(preview, "apimarket-report-%s.html" % slug),
            os.path.join(preview, "apimarket-report-%s.json" % slug))


def json_schema(path):
    """Read schema_version from the sibling json; None when absent.

    A json that cannot be parsed is not silently treated as absent: the
    caller records the raw error so a corrupt sibling cannot hide."""
    if not os.path.isfile(path):
        return None, "absent"
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            doc = json.loads(handle.read())
    except (OSError, ValueError) as exc:
        return None, "unreadable: %s" % exc
    if not isinstance(doc, dict):
        return None, "not an object"
    return doc.get("schema_version"), "ok"


def build_manifest(preview):
    faces = []
    problems = []
    for slug in FROZEN:
        html_path, json_path = face_paths(preview, slug)
        if not os.path.isfile(html_path):
            problems.append("E_AMF4 no html for frozen face %r (%s)"
                            % (slug, html_path))
            continue
        has_json = os.path.isfile(json_path)
        schema, note = json_schema(json_path)
        if note.startswith("unreadable") or note == "not an object":
            problems.append("E_AMF3 sibling json %r is %s" % (slug, note))
        faces.append({
            "slug": slug,
            "html": os.path.relpath(html_path, ROOT).replace("\\", "/"),
            "html_bytes": os.path.getsize(html_path),
            "html_sha256": sha256(html_path),
            "json": (os.path.relpath(json_path, ROOT).replace("\\", "/")
                     if has_json else None),
            "json_bytes": os.path.getsize(json_path) if has_json else None,
            "json_sha256": sha256(json_path) if has_json else None,
            "schema_version": schema,
        })
    excluded = []
    for slug, producer in EXCLUDED:
        excluded.append({"slug": slug, "producer": producer})
    doc = {
        "manifest_schema": MANIFEST_SCHEMA,
        "tool": "tools/apimarket_face_freeze.py",
        "why": WHY,
        "faces": faces,
        "excluded_generator_backed": excluded,
    }
    return doc, problems


def write_manifest(path, doc):
    payload = json.dumps(doc, sort_keys=True, indent=1,
                         ensure_ascii=True) + "\n"
    out_dir = os.path.dirname(os.path.abspath(path))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    os.replace(tmp, path)
    return len(payload.encode("utf-8"))


def check(preview, path):
    fails = []

    def red(code, detail):
        fails.append("%s %s" % (code, detail))

    if not os.path.isfile(path):
        red("E_AMF0", "manifest missing: %s" % path)
        return fails
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            doc = json.loads(handle.read())
    except (OSError, ValueError) as exc:
        red("E_AMF0", "manifest unreadable: %s" % exc)
        return fails
    if not isinstance(doc, dict):
        red("E_AMF0", "manifest is not an object")
        return fails

    faces = doc.get("faces") or []
    excluded = doc.get("excluded_generator_backed") or []

    # AC-AMF6 degenerate
    if doc.get("manifest_schema") != MANIFEST_SCHEMA:
        red("E_AMF6", "manifest_schema=%r expected %d"
            % (doc.get("manifest_schema"), MANIFEST_SCHEMA))
    slugs = [f.get("slug") for f in faces if isinstance(f, dict)]
    if len(slugs) != len(FROZEN):
        red("E_AMF6", "frozen faces=%d expected %d"
            % (len(slugs), len(FROZEN)))
    if sorted(slugs) != sorted(FROZEN):
        red("E_AMF6", "frozen slug set drifted: %s"
            % ",".join(str(s) for s in slugs))
    if [f.get("slug") for f in excluded if isinstance(f, dict)] != [
            slug for slug, _p in EXCLUDED]:
        red("E_AMF6", "excluded slug set drifted")

    # AC-AMF1 coverage
    listed = set(slugs) | set(e.get("slug") for e in excluded
                              if isinstance(e, dict))
    on_disk = set()
    for name in os.listdir(preview):
        if (name.startswith("apimarket-report-")
                and name.endswith(".html")):
            on_disk.add(name[len("apimarket-report-"):-len(".html")])
    for slug in sorted(on_disk - listed):
        red("E_AMF1", "unlisted page apimarket-report-%s.html" % slug)

    for face in faces:
        if not isinstance(face, dict):
            red("E_AMF6", "face entry is not an object")
            continue
        slug = face.get("slug")
        html_path, json_path = face_paths(preview, slug)

        # AC-AMF4 grave / AC-AMF2 pin
        if not os.path.isfile(html_path):
            red("E_AMF4", "frozen face %r has no html on disk" % slug)
            continue
        disk_bytes = os.path.getsize(html_path)
        if face.get("html_bytes") != disk_bytes:
            red("E_AMF2", "%r html bytes recorded=%r disk=%d"
                % (slug, face.get("html_bytes"), disk_bytes))
        if face.get("html_sha256") != sha256(html_path):
            red("E_AMF2", "%r html sha256 drifted" % slug)
        recorded_json = face.get("json")
        if recorded_json:
            if not os.path.isfile(json_path):
                red("E_AMF2", "%r sibling json missing on disk" % slug)
            else:
                if face.get("json_bytes") != os.path.getsize(json_path):
                    red("E_AMF2", "%r json bytes recorded=%r disk=%d"
                        % (slug, face.get("json_bytes"),
                           os.path.getsize(json_path)))
                if face.get("json_sha256") != sha256(json_path):
                    red("E_AMF2", "%r json sha256 drifted" % slug)
        elif os.path.isfile(json_path):
            red("E_AMF1", "%r sibling json appeared but is not recorded"
                % slug)

        # AC-AMF3 schema
        schema, note = json_schema(json_path)
        if recorded_json and (note.startswith("unreadable")
                              or note == "not an object"):
            red("E_AMF3", "%r sibling json is %s" % (slug, note))
        elif face.get("schema_version") != schema:
            red("E_AMF3", "%r schema recorded=%r disk=%r"
                % (slug, face.get("schema_version"), schema))

    # AC-AMF5 exclusion proof
    for entry in excluded:
        if not isinstance(entry, dict):
            red("E_AMF6", "excluded entry is not an object")
            continue
        slug = entry.get("slug")
        producer = entry.get("producer") or ""
        producer_path = os.path.join(ROOT, producer.replace("/", os.sep))
        if not os.path.isfile(producer_path):
            red("E_AMF5", "%r producer not on disk: %r" % (slug, producer))
        elif not os.path.basename(producer).startswith("preview_"):
            red("E_AMF5", "%r producer is not a preview_*.py generator: %r"
                % (slug, producer))
    return fails


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="apimarket_face_freeze.py",
        description="Pin the apimarket report faces that have no"
                    " reproducible generator (AC-AMF1..6).")
    parser.add_argument("--write", action="store_true",
                        help="record bytes+sha256+schema of the frozen faces")
    parser.add_argument("--check", action="store_true",
                        help="read-only drift verdict against the manifest")
    parser.add_argument("--preview", default=PREVIEW,
                        help="preview directory (default: preview/)")
    parser.add_argument("--out", default=MANIFEST,
                        help="manifest path (default:"
                             " state/apimarket-face-freeze.json)")
    args = parser.parse_args(argv)
    if args.write == args.check:
        sys.stderr.write("pass exactly one of --write / --check\n")
        return 2
    if args.write:
        doc, problems = build_manifest(args.preview)
        for line in problems:
            print("FAIL %s" % line)
        if problems:
            print("APIMARKET FACE FREEZE WRITE FAIL fails=%d"
                  % len(problems))
            return 2
        size = write_manifest(args.out, doc)
        print("APIMARKET FACE FREEZE WROTE path=%s bytes=%d faces=%d"
              " excluded=%d" % (args.out, size, len(doc["faces"]),
                                len(doc["excluded_generator_backed"])))
        return 0
    fails = check(args.preview, args.out)
    if fails:
        for line in fails:
            print("FAIL %s" % line)
        print("APIMARKET FACE FREEZE CHECK FAIL fails=%d" % len(fails))
        return 2
    with io.open(args.out, "r", encoding="utf-8") as handle:
        doc = json.loads(handle.read())
    print("APIMARKET FACE FREEZE CHECK PASS fails=0 frozen=%d excluded=%d"
          " schema=%d"
          % (len(doc.get("faces") or []),
             len(doc.get("excluded_generator_backed") or []),
             MANIFEST_SCHEMA))
    return 0


if __name__ == "__main__":
    sys.exit(main())
