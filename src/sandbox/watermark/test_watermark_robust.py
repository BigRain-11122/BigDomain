"""Robustness extension suite for the AIGC implicit watermark sandbox
(BigDomain tech-queue item "blind_watermark robustness extension three
cases", direct successor of the P-47-3c acceptance suite in
test_watermark.py; pre-registered criteria live in the backlog R552
row, registered on disk before this suite was executed).

Pre-registered criteria (backlog R552 row):

  AC-EX0 control anchor: same 256-bit label embed -> clean extract
         roundtrip exact; if this anchor fails the whole suite is FAIL
         and perturbation-case readings are not trusted.
  AC-EX1 scaling family: bilinear resize 0.5x and 2.0x, one case each;
         every case records exact bool + BER (negative verdict lawful).
  AC-EX2 salt-pepper family: density 5%, one case; same standard.
  AC-EX3 double re-compression family: JPEG q=90 -> reopen -> JPEG
         q=90 again, one case; same standard.
  AC-EX4 honest-record surface: every perturbation case carries its
         BER on its own evidence line (zero silent skip); suite exit 0
         iff AC-EX0 exact AND all 4 perturbation instances produced a
         measurement (non-exact extraction = honest negative, lawful
         per pre-registration, does not fail the suite).

Usage: python test_watermark_robust.py
"""

import os
import shutil
import sys
import tempfile

import cv2
import numpy as np
from blind_watermark import WaterMark

from test_watermark import JPEG_Q, ber, extract_bits, label_bits, make_img

SCALE_DOWN = 0.5
SCALE_UP = 2.0
SP_DENSITY = 0.05
SEED = 20260929

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok), evidence))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def salt_pepper(img, density, rng):
    out = img.copy()
    m = rng.random(img.shape[:2])
    out[m < density / 2.0] = 0
    out[m > 1.0 - density / 2.0] = 255
    return out


def jpeg_resave(img, path, quality):
    return cv2.imwrite(path, img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])


def perturb_case(ac, img_e, bits, nbits, path, writer):
    """Run one perturbation instance, extract, record exact + BER.

    PASS criterion per pre-registration = a measurement was produced
    (write ok + extraction attempted); non-exact extraction is an
    honest negative recorded with its BER on the same line.
    """
    ok_write = writer(img_e)
    got = extract_bits(path, nbits) if ok_write else None
    exact = got is not None and bool(np.array_equal(got, bits))
    ev_ber = ber(got, bits) if got is not None else 1.0
    record(ac, ok_write and got is not None,
           "write=%s extract-exact=%s ber=%.4f%s"
           % (ok_write, exact, ev_ber,
              "" if exact else " (honest negative, lawful per AC-EX4)"))
    return ok_write and got is not None


def main():
    tmp = tempfile.mkdtemp(prefix="bd_wmrx_")
    try:
        bits = label_bits().astype(int)
        nbits = int(bits.size)
        orig = os.path.join(tmp, "orig.png")
        emb = os.path.join(tmp, "embedded.png")
        cv2.imwrite(orig, make_img())

        bwm = WaterMark(password_wm=1, password_img=1, mode="common")
        bwm.read_img(orig)
        bwm.read_wm(bits, mode="bit")
        bwm.embed(emb)
        ok_embed = os.path.exists(emb) and os.path.getsize(emb) > 0
        exact_clean = ok_embed and bool(
            np.array_equal(extract_bits(emb, nbits), bits))
        record("AC-EX0", ok_embed and exact_clean,
               "control anchor: embed=%s wm_bits=%d clean-roundtrip-"
               "exact=%s" % (ok_embed, nbits, exact_clean))
        if not (ok_embed and exact_clean):
            print("SUITE FAIL (control anchor failed; perturbation "
                  "readings not trusted)", flush=True)
            return 1

        img_e = cv2.imread(emb, cv2.IMREAD_COLOR)
        measured = []

        # AC-EX1 scaling family: 0.5x and 2.0x bilinear, one case each
        for tag, fx in (("down0.5x", SCALE_DOWN), ("up2.0x", SCALE_UP)):
            path = os.path.join(tmp, "resized_%s.png" % tag)

            def w(img, path=path, fx=fx):
                r = cv2.resize(img, None, fx=fx, fy=fx,
                               interpolation=cv2.INTER_LINEAR)
                return cv2.imwrite(path, r)

            measured.append(perturb_case(
                "AC-EX1-%s" % tag, img_e, bits, nbits, path, w))

        # AC-EX2 salt-pepper family: density 5%
        rng = np.random.default_rng(SEED)
        path = os.path.join(tmp, "saltpepper_d5.png")

        def w2(img, path=path, rng=rng):
            return cv2.imwrite(path, salt_pepper(img, SP_DENSITY, rng))

        measured.append(perturb_case(
            "AC-EX2-d5", img_e, bits, nbits, path, w2))

        # AC-EX3 double re-compression family: q90 -> reopen -> q90
        jpg1 = os.path.join(tmp, "pass1_q%d.jpg" % JPEG_Q)
        jpg2 = os.path.join(tmp, "pass2_q%d.jpg" % JPEG_Q)

        def w3(img, jpg1=jpg1, jpg2=jpg2):
            if not jpeg_resave(img, jpg1, JPEG_Q):
                return False
            mid = cv2.imread(jpg1, cv2.IMREAD_COLOR)
            if mid is None:
                return False
            return jpeg_resave(mid, jpg2, JPEG_Q)

        measured.append(perturb_case(
            "AC-EX3-q90x2", img_e, bits, nbits, jpg2, w3))

        case_evidence = [ev for ac, ok, ev in RESULTS if ac != "AC-EX0"]
        ber_labeled = all("ber=" in ev for ev in case_evidence)
        record("AC-EX4",
               all(measured) and ber_labeled and len(case_evidence) == 4,
               "measured=%d/4 ber-on-every-case-line=%s zero-silent-skip "
               "(non-exact verdicts lawful per pre-registration)"
               % (sum(1 for m in measured if m), ber_labeled))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    fails = [ac for ac, ok, _ in RESULTS if not ok]
    total = len(RESULTS)
    print("SUITE %s (%d/%d criteria pass)"
          % ("PASS" if not fails else "FAIL", total - len(fails), total),
          flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
