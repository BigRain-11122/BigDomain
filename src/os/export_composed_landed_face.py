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
# R2643 (AC-EDWW1..AC-EDWW6): four more landing shapes MEASURED at R2638 with
# src/os/limits_export_composed_landed_next_R2638.py and re-measured here
# before any byte of this extension was written. Each used to ride on a word
# that named only half of what it saw: a BOM landing whose BODY disagreed with
# the composed text still read BOM-LANDING (delta=6 invisible in the word), a
# BOM landing carrying MIXED separators read BOM-LANDING with the transport
# surviving only as a field, a UTF-16LE BOM read COMPOSED-MISMATCH at delta=14,
# and a TRUNCATED two byte BOM prefix read COMPOSED-MISMATCH at delta=2.
WORD_BOM_BODY_MISMATCH = "BOM-BODY-MISMATCH"
WORD_BOM_TRANSPORT_MIXED = "BOM-TRANSPORT-MIXED"
WORD_UTF16_BOM = "UTF16-BOM-LANDING"
WORD_BOM_TRUNCATED = "BOM-TRUNCATED"
# R2646 second wave (AC-EDWX1..AC-EDWX6 pinned at R2643 in
# state/queue/tech.md:661 BEFORE this code existed). Three shapes rode on a
# word that named only half of what the landing carried, MEASURED at R2643
# with src/os/limits_export_composed_landed_next_R2643.py and re-measured by
# this window before any byte was written:
#   TRANSPORT-MIXED bom=0 - a TRUNCATED BOM prefix over a MIXED body lost the
#                           truncation fact because the truncated law needed a
#                           clean body;
#   UTF16-BOM-LANDING     - a UTF-16 marker with NO body was indistinguishable
#                           from a whole UTF-16 landing;
#   BOM-LANDING delta=0   - a BOM-ONLY landing against empty text read clean.
WORD_BOM_TRUNCATED_MIXED = "BOM-TRUNCATED-MIXED"
WORD_UTF16_BOM_MARKER_ONLY = "UTF16-BOM-MARKER-ONLY"
WORD_BOM_EMPTY_PAYLOAD = "BOM-EMPTY-PAYLOAD"
# R2649 third wave (AC-EDWY1..AC-EDWY6 pinned at R2646 in
# state/queue/tech.md:662 BEFORE this code existed). Four shapes still rode on
# a word that named only half of what the landing carried, MEASURED at R2646
# with src/os/limits_export_composed_landed_next_R2646.py and re-measured by
# this window before any byte was written (qa/limits-export-composed-landed-
# third-wave-before-R2649.log, 881B):
#   TRANSPORT-MIXED bom=0       - a TRUNCATED prefix over a MIXED body that is
#                                 NOT the composed text lost the cut fact,
#                                 because the cut law needed byte equality;
#   BOM-EMPTY-PAYLOAD           - against a NON-EMPTY text it carried
#                                 composed=None, so the comparison vanished;
#   BOM-TRUNCATED delta=2       - a prefix with NO body behind it read as a
#                                 plain truncation against empty text;
#   BOM-BODY-MISMATCH delta=-10 - two markers on one landing were named only
#                                 as a body gap.
WORD_BOM_TRUNCATED_MIXED_GAP = "BOM-TRUNCATED-MIXED-GAP"
WORD_BOM_CUT_NO_BODY = "BOM-CUT-NO-BODY"
WORD_BOM_DOUBLE_MARKER = "BOM-DOUBLE-MARKER"
# R2653 fourth wave (AC-EDWZ1..AC-EDWZ6 pinned at R2649 in
# state/queue/tech.md:663 BEFORE this code existed). Three shapes still rode on
# a word that described the landing only partly, MEASURED at R2649 with
# src/os/limits_export_composed_landed_next_R2649.py and re-measured by this
# window before any byte was written (qa/limits-export-composed-landed-fourth-
# wave-before-R2653.log, 778B):
#   UTF16-BOM-LANDING disk=3   - a UTF-16 marker with ONE byte behind it read
#                                as a whole landing, so an odd remnant (a body
#                                that cannot be a whole UTF-16 payload) was
#                                indistinguishable from a complete one;
#   UTF16-BOM-LANDING composed=None - the same remnant against a NON-EMPTY
#                                text carried no count at all, so nothing said
#                                what it had been measured against;
#   BOM-DOUBLE-MARKER disk=8 composed=None delta=None - two markers with a
#                                BODY behind them named both markers and then
#                                described the body with no field at all.
WORD_UTF16_BOM_SHORT_BODY = "UTF16-BOM-SHORT-BODY"
# R2657 fifth wave (AC-EDXA1..AC-EDXA6 pinned at R2653 in
# state/queue/tech.md:664 BEFORE this code existed). Two shapes still rode on a
# word that decided nothing, MEASURED at R2653 and re-measured by this window
# before any byte was written (qa/limits-export-composed-landed-fifth-wave-
# before-R2657.log, 1236B):
#   UTF16-BOM-LANDING disk=26 - a whole UTF-16LE landing that AGREES with the
#                               composed text and one that DISAGREES read the
#                               SAME word with composed=None, so agreement was
#                               never decided for a UTF-16 landing;
#   BOM-DOUBLE-MARKER body=1  - an ODD body behind two markers was described by
#                               its count only, never as short, although a
#                               UTF-16 body is an even number of bytes.
WORD_UTF16_BOM_BODY_GAP = "UTF16-BOM-BODY-GAP"

BOM = b"\xef\xbb\xbf"
# A strict PREFIX of the UTF-8 BOM, one or two bytes: the shape a writer lands
# when it is cut off mid-marker. A prefix is only called truncated when the
# REST of the payload really is the composed text (AC-EDWW4), so a legitimate
# three byte UTF-8 character that happens to start with 0xef is not accused.
BOM_PREFIXES = (b"\xef", b"\xef\xbb")
# UTF-16 markers in both byte orders: these are NOT UTF-8 BOMs and comparing
# their length against a UTF-8 composed text can only invent a delta.
UTF16_BOMS = (b"\xff\xfe", b"\xfe\xff")

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
    # R2646 pinned order (AC-EDWX1..AC-EDWX6 pinned at R2643 BEFORE this code),
    # still so no landing can ever earn two words: EMPTY (above), UTF-16 BOM
    # MARKER-ONLY before a whole UTF-16 landing, BOM-ONLY before any BOM body
    # judgement, TRUNCATED BOM (a MIXED body named as BOTH facts), BOM (mixed /
    # body gap / clean), MIXED, then the composed/landed compare.
    for mark in UTF16_BOMS:
        if raw.startswith(mark):
            body16 = raw[len(mark):]
            if not body16:
                # AC-EDWX2: a marker with nothing behind it is not a landing.
                return {
                    "word": WORD_UTF16_BOM_MARKER_ONLY,
                    "transport": TRANSPORT_LF,
                    "composed": None,
                    "disk": len(raw),
                    "delta": None,
                    "bom": len(mark),
                    "bom_kind": "utf16-empty",
                }
            if len(body16) % 2:
                # AC-EDWZ1: a UTF-16 body is an even number of bytes, so an
                # ODD remnant cannot be a whole landing and is not called one.
                # AC-EDWZ2: when the composed text is not empty the count the
                # remnant was measured against is carried - the whole landing
                # it would have been, marker included, in its own byte order -
                # rather than an unqualified word.
                folded16 = text.replace("\r\n", "\n").encode("utf-8")
                expected = None
                if folded16:
                    codec = ("utf-16-le" if mark == b"\xff\xfe"
                             else "utf-16-be")
                    expected = len(mark) + len(
                        text.replace("\r\n", "\n").encode(codec))
                return {
                    "word": WORD_UTF16_BOM_SHORT_BODY,
                    "transport": read_transport(body16),
                    "composed": expected,
                    "disk": len(raw),
                    "delta": (len(raw) - expected) if expected else None,
                    "bom": len(mark),
                    "bom_kind": "utf16-short",
                    "body": len(body16),
                }
            # AC-EDXA1/AC-EDXA2: a whole UTF-16 landing is COMPARED with the
            # composed text in its own byte order, so an agreeing one is named
            # apart from a disagreeing one and both counts are published. The
            # compare is done on the body bytes the marker own codec produces,
            # never on the UTF-8 length. AC-EDXA4 is why the fallback exists:
            # a body that is merely SHORTER, or longer without carrying the
            # composed text as its head, is not a judgement this face can make
            # from bytes alone, so it keeps the historical whole-landing word
            # with no count instead of inventing a delta.
            codec = ("utf-16-le" if mark == b"\xff\xfe" else "utf-16-be")
            folded16 = text.replace("\r\n", "\n").encode(codec)
            expected = len(mark) + len(folded16)
            if len(body16) == len(folded16):
                return {
                    "word": WORD_UTF16_BOM,
                    "transport": read_transport(body16),
                    "composed": expected,
                    "disk": len(raw),
                    "delta": 0,
                    "bom": len(mark),
                    "bom_kind": "utf16",
                    "agrees": True,
                }
            if len(body16) > len(folded16) and body16[:len(folded16)] == folded16:
                return {
                    "word": WORD_UTF16_BOM_BODY_GAP,
                    "transport": read_transport(body16),
                    "composed": expected,
                    "disk": len(raw),
                    "delta": len(raw) - expected,
                    "bom": len(mark),
                    "bom_kind": "utf16-gap",
                    "agrees": False,
                }
            return {
                "word": WORD_UTF16_BOM,
                "transport": read_transport(body16),
                "composed": None,
                "disk": len(raw),
                "delta": None,
                "bom": len(mark),
                "bom_kind": "utf16",
            }
    if raw.startswith(BOM) and raw[len(BOM):len(BOM) + 2] in UTF16_BOMS:
        # AC-EDWY4: two markers on one landing are named as BOTH markers
        # instead of being judged as a body gap of the first one.
        # AC-EDWZ3: whatever sits BEHIND both markers is described by its own
        # fields (its size and the transport it carries), so the body is no
        # longer an invisible remainder under a marker count.
        behind = raw[len(BOM) + 2:]
        # AC-EDXA3: a UTF-16 body is an even number of bytes, so an ODD body
        # behind both markers is a remnant. The WORD stays BOM-DOUBLE-MARKER
        # because AC-EDWZ3 own fixture (a three byte body) must keep its answer
        # (AC-EDXA5), so the short fact is published as its own field and its
        # own rendered token rather than by replacing a word a parent pinned.
        return {
            "word": WORD_BOM_DOUBLE_MARKER,
            "transport": TRANSPORT_LF,
            "composed": None,
            "disk": len(raw),
            "delta": None,
            "bom": len(BOM) + 2,
            "bom_kind": "utf8+utf16",
            "body": len(behind),
            "body_transport": read_transport(behind),
            "body_short": bool(len(behind) % 2),
        }
    if raw == BOM:
        # AC-EDWX3: a BOM with no payload names the empty payload instead of
        # reading a clean BOM landing at delta=0. AC-EDWY2: when the composed
        # text is NOT empty the count it was measured against is carried, so
        # the empty payload is a claim with a comparison behind it rather than
        # an unqualified word.
        folded_only = text.replace("\r\n", "\n").encode("utf-8")
        return {
            "word": WORD_BOM_EMPTY_PAYLOAD,
            "transport": TRANSPORT_LF,
            "composed": len(folded_only) if folded_only else None,
            "disk": len(raw),
            "delta": (len(raw) - len(folded_only)) if folded_only else None,
            "bom": len(BOM),
            "bom_kind": "utf8-empty",
        }
    if not raw.startswith(BOM):
        # The LONGEST matching strict prefix is the one that gets judged: a two
        # byte cut must not be measured as a one byte cut (MEASURED at R2643,
        # the first suite run read the two byte world as COMPOSED-MISMATCH
        # because the shortest prefix won and its body was one byte too long).
        matches = [p for p in BOM_PREFIXES if raw.startswith(p)]
        if matches:
            prefix = max(matches, key=len)
            cut = raw[len(prefix):]
            cut_transport = read_transport(cut)
            folded = text.replace("\r\n", "\n").encode("utf-8")
            if not cut:
                # AC-EDWY3: a strict prefix with NOTHING behind it is not a
                # truncation of any text - there is no body to have lost.
                return {
                    "word": WORD_BOM_CUT_NO_BODY,
                    "transport": cut_transport,
                    "composed": len(folded) if folded else None,
                    "disk": len(raw),
                    "delta": (len(raw) - len(folded)) if folded else None,
                    "bom": len(prefix),
                    "bom_kind": "utf8-cut-only",
                }
            if cut_transport == TRANSPORT_MIXED:
                # AC-EDWX1: the truncation and the transport are named in ONE
                # word, and only when the body is the composed text up to its
                # separators, so a legitimate 0xef-leading payload is not
                # accused of being a cut marker.
                cut_folded = cut.replace(b"\r\n", b"\n")
                if cut_folded == folded:
                    return {
                        "word": WORD_BOM_TRUNCATED_MIXED,
                        "transport": cut_transport,
                        "composed": len(folded),
                        "disk": len(raw),
                        "delta": len(raw) - len(folded),
                        "bom": len(prefix),
                        "bom_kind": "utf8-truncated",
                    }
                if folded and cut_folded.startswith(folded):
                    # AC-EDWY1: the cut is real (the composed text is the HEAD
                    # of the body) but bytes follow it, so the gap is named
                    # with the transport instead of the cut fact being dropped.
                    return {
                        "word": WORD_BOM_TRUNCATED_MIXED_GAP,
                        "transport": cut_transport,
                        "composed": len(folded),
                        "disk": len(raw),
                        "delta": len(raw) - len(folded),
                        "bom": len(prefix),
                        "bom_kind": "utf8-truncated-gap",
                    }
            else:
                cut_composed = composed_bytes(text, cut_transport)
                if cut_transport == TRANSPORT_CRLF:
                    expected = folded.replace(b"\n", b"\r\n")
                else:
                    expected = folded
                if len(cut) == cut_composed and cut == expected:
                    return {
                        "word": WORD_BOM_TRUNCATED,
                        "transport": cut_transport,
                        "composed": cut_composed,
                        "disk": len(raw),
                        "delta": len(raw) - cut_composed,
                        "bom": len(prefix),
                        "bom_kind": "utf8-truncated",
                    }
    bom = len(BOM) if raw.startswith(BOM) else 0
    body = raw[bom:]
    transport = read_transport(body)
    if bom:
        if transport == TRANSPORT_MIXED:
            return {
                "word": WORD_BOM_TRANSPORT_MIXED,
                "transport": transport,
                "composed": None,
                "disk": len(raw),
                "delta": None,
                "bom": bom,
                "bom_kind": "utf8",
            }
        composed = composed_bytes(text, transport)
        delta = len(body) - composed
        return {
            "word": WORD_BOM_LANDING if delta == 0 else WORD_BOM_BODY_MISMATCH,
            "transport": transport,
            "composed": composed,
            "disk": len(raw),
            "delta": delta,
            "bom": bom,
            "bom_kind": "utf8",
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
        kind = report.get("bom_kind")
        suffix = "" if kind in (None, "utf8") else " kind=%s" % kind
        if report.get("body") is not None:
            suffix += " body=%d body_transport=%s" % (
                report["body"], report.get("body_transport"))
        if report.get("body_short"):
            # AC-EDXA3: the short fact is rendered beside the body count, so a
            # reader sees BOTH that it sits behind two markers and that the
            # remainder cannot be a whole UTF-16 payload.
            suffix += " body_short=1"
        return ("COMPOSED-LANDED %s transport=%s bom=%d composed=%s disk=%d"
                " delta=%s%s") % (
            report["word"], report["transport"], report["bom"],
            report["composed"], report["disk"], report["delta"], suffix)
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
