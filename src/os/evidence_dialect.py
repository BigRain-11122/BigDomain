"""The evidence-file dialect law, in ONE place (R2926, AC-EVB1..AC-EVB5).

Why this module exists: until R2926 the dialect rule lived inside
src/os/qa_writer_census.py, which imports reconcile_all (the shipped SUITES
registry) at module level. That is a fine dependency for a census probe and a
bad one for a commit hook: the hook must answer "is this staged evidence file
in the healthy dialect" without loading the whole registry.

So the rule moved here, verbatim, and the census now DELEGATES to it. There is
still exactly one classification law (the R2901/R2905/R2906 lesson: a rule
typed in two places drifts in one of them).

The rule itself is unchanged and pre-registered at R1836 (AC-SL3):

  * BOM utf-16le/utf-16be            -> ps-utf16     (PS 5.1 `>` family)
  * no BOM + any NUL byte present    -> nul-bytes    (BOM-less UTF-16; this
                                                      branch runs BEFORE the
                                                      EOL branches - R2808)
  * no BOM + crlf==0 + strict utf-8  -> tee          (healthy dialect)
  * no BOM + crlf-dominant + utf-8 FAILS -> cmd-raw  (raw cp936 family)
  * no BOM + crlf-dominant + utf-8 OK    -> pwsh-capture
  * anything else                    -> other        (honest catch-all)

`tee` is the only healthy class. Everything else is a named debt class.

The label column is NOT part of the rule (R2926 measurement): SHELL_CAPTURE_LABEL
marks one writer family, not a dialect - on the shipped tree 410 labeled files
classify tee and 579 of the 590 baselined debt files carry no label. label_absent
is a census column; the refusal is the class.

Stdlib only, ASCII source, zero network, zero shell, writes nothing.
"""

import os

HEALTHY = "tee"
CLASSES = ("tee", "cmd-raw", "pwsh-capture", "ps-utf16", "nul-bytes",
           "other")
BASELINE_CLASSES = ("cmd-raw", "pwsh-capture", "ps-utf16", "nul-bytes",
                    "other")

BOM_UTF8 = b"\xef\xbb\xbf"
BOM_16LE = b"\xff\xfe"
BOM_16BE = b"\xfe\xff"


def bom_of(raw):
    """Name the BOM, if any (AC-QD family). This module is a LEAF: no
    import of the sandbox registry, so the commit gate can ask it before
    anything else in the tree is loadable.

    R2926: `qa_decode_probe._bom_of` was the single source of this
    answer; it now imports THIS function, so the count of the rule is
    still one and the dependency points at the leaf rather than away
    from it.
    """
    if raw.startswith(BOM_16LE):
        return "utf-16le"
    if raw.startswith(BOM_16BE):
        return "utf-16be"
    if raw.startswith(BOM_UTF8):
        return "utf-8-sig"
    return "utf-8"  # presumed (no BOM on disk) - the R1836 census column


def classify_bytes(raw, label=None, counts=True):
    """Classify one evidence blob. `label` is the ASCII label bytes to look
    for on the first physical line (None = do not read the label column).

    Returns a row dict; every number is measured, never fabricated.

    R3099 (AC-WCB11): `counts=False` is the drift-facing cut of the SAME law.
    The class is decided by short-circuit membership tests (`b"\\r\\n" not in
    raw` returns at the first hit instead of scanning the whole blob), so the
    two count passes are paid only by a file that actually carries CRLF. A
    row built this way leaves `crlf` and `bare_lf` at -1, meaning NOT
    MEASURED - it never writes a zero it did not read - and may only be
    consumed for `class` (and `label`, `utf8`, `bom`, `bytes`). Measured at
    R3099 over the live 4112-file corpus: 496.5ms -> 318.5ms for identical
    classes on every file.
    """
    row = {"bytes": len(raw), "bom": bom_of(raw),
           "crlf": 0 if counts else -1, "bare_lf": 0 if counts else -1,
           "utf8": False, "label": False, "class": "other"}
    try:
        raw.decode("utf-8", "strict")
        row["utf8"] = True
    except UnicodeDecodeError:
        row["utf8"] = False
    if label is not None:
        first = raw.split(b"\n", 1)[0]
        if first.endswith(b"\r"):
            first = first[:-1]
        row["label"] = (first == label)
    if row["bom"] in ("utf-16le", "utf-16be"):
        row["class"] = "ps-utf16"
    elif row["bom"] == "utf-8-sig":
        row["class"] = "other"
    elif b"\x00" in raw:
        row["class"] = "nul-bytes"
    elif b"\r\n" not in raw:
        row["class"] = "tee" if row["utf8"] else "other"
    else:
        crlf = raw.count(b"\r\n")
        crlf_dominant = crlf > raw.count(b"\n") - crlf
        row["class"] = ("pwsh-capture" if row["utf8"] else "cmd-raw") \
            if crlf_dominant else "other"
    if counts:
        row["crlf"] = raw.count(b"\r\n")
        row["bare_lf"] = raw.count(b"\n") - row["crlf"]
    return row


class EvidenceDecodeError(Exception):
    """A blob no known writer family decodes (R2928, AC-EVR2).

    Refusing by name is the honest face: returning gb18030 mojibake for bytes
    that were never cp936 would look like a successful read to every consumer.
    """


def _decode_lenient(raw, enc, allow_tail=False):
    """(text, tail_bytes, damaged) or (None, b'', False).

    R2928 measured 2 of the 119 baselined ps-utf16 files as odd-length, each a
    utf-16le body with ONE stray byte appended (board-R935.log 1705B,
    lobby-roomboard-R1773.log 7077B) - a truncated writer, not corruption of the
    text. Dropping that byte and NAMING it in the returned row is the honest
    read: decoding with errors="replace" would hide the loss inside U+FFFD, and
    refusing the whole file would call 1704 readable bytes unusable.
    """
    try:
        return raw.decode(enc), b"", False
    except UnicodeDecodeError:
        pass
    if allow_tail and len(raw) % 2 == 1:
        try:
            return raw[:-1].decode(enc), raw[-1:], True
        except UnicodeDecodeError:
            pass
    return None, b"", False


def read_text(raw):
    """Read one evidence blob, whatever dialect it was written in (R2928).

    Why this exists: 590 files on this tree are baselined as non-tee debt and
    only 148 of them are actually unreadable to a plain utf-8 reader. Rewriting
    those bytes would rewrite the objects 16 shipped sha256 citations name, so
    the debt is made USABLE instead: one read face, no writes, endianness and
    codepage NAMED in the row it returns.

    Returns {"text", "encoding", "assumed", "damaged", "tail_hex"}. `assumed`
    is True when the answer rests on a guess the bytes cannot verify (BOM-less
    utf-16 endianness, a cp936 body); `damaged` is True when a stray trailing
    byte had to be named and dropped (see _decode_lenient).
    """
    row = {"text": None, "encoding": "", "assumed": False,
           "damaged": False, "tail_hex": ""}

    def done(enc, assumed, text, tail, damaged):
        row.update({"text": text, "encoding": enc, "assumed": assumed,
                    "damaged": damaged, "tail_hex": tail.hex()})
        return row

    if raw.startswith(BOM_16LE):
        text, tail, damaged = _decode_lenient(raw, "utf-16", True)
        if text is None:
            raise EvidenceDecodeError("utf-16le BOM: body does not decode")
        return done("utf-16le", False, text, tail, damaged)
    if raw.startswith(BOM_16BE):
        text, tail, damaged = _decode_lenient(raw, "utf-16", True)
        if text is None:
            raise EvidenceDecodeError("utf-16be BOM: body does not decode")
        return done("utf-16be", False, text, tail, damaged)
    body = raw
    utf8_bom = raw.startswith(BOM_UTF8)
    if utf8_bom:
        body = raw[len(BOM_UTF8):]
    if b"\x00" in body:
        # NUL is never legitimate in an evidence log (R2807), even behind a
        # utf-8 BOM: R2928 measured 3 such files (honorcert-R1755,
        # load-S8b-R550, reorg-R1731) and a utf-8 arm would have returned
        # 2520 / 1685 / 36 NULs as "text". The body is utf-16; name the guess.
        for enc, name in (("utf-16-le", "utf-16le"), ("utf-16-be", "utf-16be")):
            text, tail, damaged = _decode_lenient(body, enc, True)
            if text is None or "\x00" in text:
                continue
            return done(name, True, text, tail, damaged)
        raise EvidenceDecodeError("nul-bytes: no utf-16 arm decodes cleanly")
    if utf8_bom:
        try:
            return done("utf-8", False, body.decode("utf-8"), b"", False)
        except UnicodeDecodeError:
            raise EvidenceDecodeError("utf-8 BOM: body does not decode")
    try:
        return done("utf-8", False, raw.decode("utf-8"), b"", False)
    except UnicodeDecodeError:
        pass
    text, _tail, _damaged = _decode_lenient(raw, "gb18030")
    if text is not None:
        return done("gb18030", True, text, b"", False)
    raise EvidenceDecodeError("no known family decodes this blob")


def plain_unusable(raw):
    """Would a naive consumer lose this file? (R2928, AC-EVR3)

    A plain utf-8 read loses a blob in TWO ways, and the second is the R2807
    trap: the decode can raise, or it can "succeed" and hand back NUL-riddled
    text, which is BOM-less utf-16 read as utf-8. Measuring only the raise
    would have called 14 of the 15 nul-bytes files usable.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return "\x00" in text


def label_coverage(rows):
    """Split classified rows by the label column.

    Returns {"labeled": n, "unlabeled": n, "labeled_names": [...]}. The
    shipped census publishes this for the baselined debt so a reader can see
    whether the self-announcing writer covers it - measured at R2926: 11 of
    590, which is why label absence cannot be a refusal.
    """
    labeled = []
    unlabeled = 0
    for name, row in rows:
        if row["label"]:
            labeled.append(name)
        else:
            unlabeled += 1
    return {"labeled": len(labeled), "unlabeled": unlabeled,
            "labeled_names": sorted(labeled)}
