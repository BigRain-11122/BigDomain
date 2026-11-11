# export_composed_landed_face.py - prove the composed text and the landed bytes
# are the SAME payload, not merely the same length on the writer side.
# Criteria AC-EDWT1..AC-EDWT6 were pre-registered in state/queue/tech.md:658
# (the R2596 seed row) BEFORE this file existed.
#
# Why this exists: the shipped verdict compares the byte count the QUEUE FACE
# reported against os.path.getsize(EXPORT). Because that count is already the
# payload the writer landed, the two agree by construction and a gap between
# the COMPOSED text and what reached disk can never be named. MEASURED at
# R2637 with src/os/limits_export_composed_landed_R2637.py: a CRLF target lands
# three bytes more than the composed LF text for a three line document, and
# the shipped classify() still answers PASS with the gap invisible.
#
# Two laws keep this face honest:
#   * the transport is read FROM THE LANDED BYTES (AC-EDWT3), never from the
#     composed text - the writer is the only owner of what it landed;
#   * the composed length is NORMALISED into that transport before the compare
#     (AC-EDWT2), so a legal CRLF landing is never called a defect.
#
# The account is a READER: one open, one read, no write, exactly one verdict
# word (AC-EDWT4). A caller whose transport flips under it cannot get half an
# answer because there is no second read to disagree with the first.

import io

LABEL = "export-composed-landed-face"

TRANSPORT_LF = "lf"
TRANSPORT_CRLF = "crlf"
TRANSPORT_MIXED = "mixed"

WORD_PASS = "PASS"
WORD_COMPOSED_MISMATCH = "COMPOSED-MISMATCH"
# R2638 (AC-EDWV1..AC-EDWV6): three landing shapes that used to ride on
# COMPOSED-MISMATCH now carry their own word, decided in a pinned order so a
# landing can never earn two: EMPTY first (there is no transport to read),
# then BOM (a byte-level marker on the payload), then MIXED (a transport fact),
# and only then the composed/landed compare.
WORD_EMPTY_LANDING = "EMPTY-LANDING"
WORD_BOM_LANDING = "BOM-LANDING"
WORD_TRANSPORT_MIXED = "TRANSPORT-MIXED"

BOM = b"\xef\xbb\xbf"

EXIT_OK = 0
EXIT_MISMATCH = 2


def read_transport(raw):
    """The transport of the LANDED bytes: lf, crlf, or mixed.

    A payload with no newline at all is single-line and both dialects agree,
    so it reads lf. A payload carrying both separators is MIXED and is named
    as such rather than being silently normalised to one of them.
    """
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    if crlf and lf:
        return TRANSPORT_MIXED
    if crlf:
        return TRANSPORT_CRLF
    return TRANSPORT_LF


def composed_bytes(text, transport):
    """The composed text measured in the transport the LANDING used.

    The text is first folded to bare LF, so a caller that already hands CRLF
    is not charged for the CR twice (MEASURED at R2637: a CRLF caller against a
    CRLF landing read 18 composed against 15 landed before this fold). A CRLF
    landing then adds one byte per newline; anything else keeps the folded
    text as composed. MIXED is not normalised - it is answered with its own
    name by the caller rather than guessed at here.
    """
    folded = text.replace("\r\n", "\n")
    if transport == TRANSPORT_CRLF:
        return len(folded.replace("\n", "\r\n").encode("utf-8"))
    return len(folded.encode("utf-8"))


def account(path, text):
    """One read of the landed bytes, one normalised compare, one verdict word.

    Returns the word beside the pair it was decided on, so a caller can print
    both counts rather than assert one. The shapes are asked in ONE pinned
    order (AC-EDWV4): an EMPTY landing first, a BOM landing second, a MIXED
    transport third, and the composed/landed compare last, so no landing can
    earn two words.
    """
    with io.open(path, "rb") as handle:
        raw = handle.read()
    transport_default = TRANSPORT_LF
    if not raw:
        return {
            "word": WORD_EMPTY_LANDING,
            "transport": transport_default,
            "composed": None,
            "disk": 0,
            "delta": None,
            "bom": 0,
        }
    bom = len(BOM) if raw.startswith(BOM) else 0
    body = raw[bom:]
    transport = read_transport(body)
    if bom:
        composed = composed_bytes(text, transport)
        return {
            "word": WORD_BOM_LANDING,
            "transport": transport,
            "composed": composed,
            "disk": len(raw),
            "delta": len(body) - composed,
            "bom": bom,
        }
    if transport == TRANSPORT_MIXED:
        return {
            "word": WORD_TRANSPORT_MIXED,
            "transport": transport,
            "composed": None,
            "disk": len(raw),
            "delta": None,
            "bom": 0,
        }
    disk = len(raw)
    composed = composed_bytes(text, transport)
    word = WORD_PASS if composed == disk else WORD_COMPOSED_MISMATCH
    return {
        "word": word,
        "transport": transport,
        "composed": composed,
        "disk": disk,
        "delta": disk - composed,
        "bom": 0,
    }


def render(report):
    """One ASCII line naming the word and, when it differs, BOTH counts."""
    if report["word"] == WORD_PASS:
        return "COMPOSED-LANDED PASS transport=%s bytes=%d" % (
            report["transport"], report["disk"])
    if report.get("bom"):
        return ("COMPOSED-LANDED %s transport=%s bom=%d composed=%s disk=%d"
                " delta=%s") % (
            report["word"], report["transport"], report["bom"],
            report["composed"], report["disk"], report["delta"])
    if report["composed"] is None:
        return "COMPOSED-LANDED %s transport=%s disk=%d" % (
            report["word"], report["transport"], report["disk"])
    return "COMPOSED-LANDED %s transport=%s composed=%d disk=%d delta=%d" % (
        report["word"], report["transport"], report["composed"],
        report["disk"], report["delta"])


def main(argv):
    """--check PATH --text-file TEXT, both required; exit 2 on a mismatch."""
    path = None
    text_path = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            index += 1
            if index >= len(argv):
                print("E_CLF_BAD_ARGS: --check needs a path")
                return 5
            path = argv[index]
        elif arg == "--text-file":
            index += 1
            if index >= len(argv):
                print("E_CLF_BAD_ARGS: --text-file needs a path")
                return 5
            text_path = argv[index]
        else:
            print("E_CLF_BAD_ARGS: unknown flag %s" % arg)
            return 5
        index += 1
    if path is None or text_path is None:
        print("E_CLF_BAD_ARGS: --check and --text-file are both required")
        return 5
    with io.open(text_path, encoding="utf-8", newline="") as handle:
        text = handle.read()
    report = account(path, text)
    print(render(report))
    return EXIT_OK if report["word"] == WORD_PASS else EXIT_MISMATCH


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
