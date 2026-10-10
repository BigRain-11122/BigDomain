"""Binding-bit independence probe for the dual-track AIGC seal
(watermark successor; seed = test_dual_track.py R593 in-tree).

The dual-track seal binds the implicit 256-bit blind-watermark payload to
SHA-256("provider:content_no:ai_label_text"), so the hidden payload is
cryptographically tied to the visible label and the art.5 metadata triple.
R593 registered a forgery floor (FORGERY_BER_MIN=0.40) on a wholesale
wrong-content_no case; this probe registers the measured basis of that
floor at single-bit granularity:

  - a one-bit perturbation of the bound preimage must avalanche the whole
    payload away from the base (registered band [0.35, 0.65]),
  - distinct one-bit perturbations must stay mutually independent
    (pairwise band),
  - a perturbed payload must still roundtrip exactly through the
    embed/extract pipeline, while its seal must NOT match the base
    expectation (forgery floor at the finest granularity).

Pre-registered criteria AC-BI1..AC-BI7 (state/queue/tech.md R1778 claim
row, registered BEFORE this code first ran; honesty law).

Scope note (honest): the explicit badge/font path is NOT exercised here;
the binding semantics under test live entirely in the implicit track, so
the suite embeds into the same deterministic base image as R593 (seed
20260929, standalone re-implementation) with zero environmental font
dependency.

Usage: python test_bind_bit.py
Exit : 0 all PASS, 2 any FAIL / criteria drift.
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile

import cv2
import numpy as np
from blind_watermark import WaterMark

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(BASE, "..", "..", ".."))
UGC_CFG = os.path.join(ROOT, "src", "sandbox", "ugc", "config.json")

PROVIDER = "BigDomain"
CONTENT_NO = "UGC-DEMO-20260929-0001"  # same stand-in as the R593 seed
EXPECTED = 7
AV_LO = 0.35          # avalanche band, pre-registered
AV_HI = 0.65          # avalanche band, pre-registered
FORGERY_FLOOR = 0.40  # R593 FORGERY_BER_MIN, held at 1-bit granularity

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def ber(got, want):
    a = np.asarray(got).astype(int).clip(0, 1)
    b = np.asarray(want).astype(int).clip(0, 1)
    return float(np.mean(a != b))


def load_label_text():
    with open(UGC_CFG, encoding="utf-8") as f:
        cfg = json.load(f)
    return str(cfg["compliance"]["ai_label_text"])


def preimage(provider, content_no, label_text):
    return ("%s:%s:%s" % (provider, content_no, label_text)
            ).encode("utf-8")


def bits_of(prebytes):
    digest = hashlib.sha256(prebytes).digest()
    return np.unpackbits(np.frombuffer(digest, dtype=np.uint8)).astype(int)


def flip_bit(prebytes, byte_off, bit):
    arr = bytearray(prebytes)
    arr[byte_off] ^= (1 << bit)
    return bytes(arr)


def make_img():
    rng = np.random.default_rng(20260929)
    h, w = 480, 640
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, :, 0] = np.tile(np.linspace(0, 255, w, dtype=np.uint8), (h, 1))
    img[:, :, 1] = rng.integers(0, 256, (h, w), dtype=np.uint8)
    img[:, :, 2] = 128
    return img


def extract_bits(path, nbits):
    bwm = WaterMark(password_wm=1, password_img=1, mode="common")
    got = bwm.extract(filename=path, wm_shape=[nbits], mode="bit")
    return np.asarray(got).astype(int).clip(0, 1)


def seal(base_img, bits, tmp, name):
    """Write a fresh deterministic copy, embed the payload, return path."""
    src = os.path.join(tmp, "base_%s.png" % name)
    out = os.path.join(tmp, "sealed_%s.png" % name)
    cv2.imwrite(src, base_img)
    bwm = WaterMark(password_wm=1, password_img=1, mode="common")
    bwm.read_img(src)
    bwm.read_wm(bits, mode="bit")
    bwm.embed(out)
    return out


def main():
    label_text = load_label_text()
    cfg_sha_before = hashlib.sha256(
        open(UGC_CFG, "rb").read()).hexdigest()[:16]
    tmp = tempfile.mkdtemp(prefix="bd_bi_")
    try:
        base_img = make_img()
        pre_b = preimage(PROVIDER, CONTENT_NO, label_text)
        bits_b = bits_of(pre_b)
        nbits = int(bits_b.size)
        pre_sha16 = hashlib.sha256(pre_b).hexdigest()[:16]

        # track byte ranges inside the joined preimage
        p_len = len(PROVIDER.encode("utf-8"))
        c_len = len(CONTENT_NO.encode("utf-8"))
        track_off = {
            "provider": 0,
            "content_no": p_len + 1,
            "label": p_len + 1 + c_len + 1,
        }

        # ---- AC-BI1: control anchor, clean roundtrip exact --------------
        sealed_b = seal(base_img, bits_b, tmp, "b")
        ext_b = extract_bits(sealed_b, nbits)
        b1 = ber(ext_b, bits_b)
        record("AC-BI1", b1 == 0.0 and nbits == 256,
               "binding bits=SHA-256(provider:content_no:label_text) "
               "sha16=%s nbits=%d clean-extract ber=%.4f (exact required)"
               % (pre_sha16, nbits, b1))

        # ---- AC-BI2: one-bit perturbation per track, avalanche band ------
        track_payloads = {}
        readings2 = []
        for name in ("provider", "content_no", "label"):
            pre_p = flip_bit(pre_b, track_off[name], 0)
            bits_p = bits_of(pre_p)
            track_payloads[name] = bits_p
            readings2.append((name, ber(bits_p, bits_b)))
        ok2 = all(AV_LO <= v <= AV_HI for _, v in readings2)
        record("AC-BI2", ok2,
               "1-bit preimage flip per track vs base: "
               + "; ".join("%s ber=%.4f" % (n, v) for n, v in readings2)
               + " (band [%.2f, %.2f], %d/%d produced)"
               % (AV_LO, AV_HI, len(readings2), len(readings2)))

        # ---- AC-BI3: bit-position sweep + pairwise independence ---------
        sweep = [bits_of(flip_bit(pre_b, track_off["content_no"], k))
                 for k in range(8)]
        base_readings = [ber(p, bits_b) for p in sweep]
        pair_readings = []
        for i in range(8):
            for j in range(i + 1, 8):
                pair_readings.append(ber(sweep[i], sweep[j]))
        all_band = ([AV_LO <= v <= AV_HI for v in base_readings]
                    + [AV_LO <= v <= AV_HI for v in pair_readings])
        ok3 = (len(base_readings) == 8 and len(pair_readings) == 28
               and all(all_band))
        record("AC-BI3", ok3,
               "content_no first byte 8-bit sweep: vs-base n=%d "
               "min=%.4f max=%.4f; pairwise n=%d min=%.4f max=%.4f; "
               "all-in-band=%d/%d (zero silent skip)"
               % (len(base_readings), min(base_readings),
                  max(base_readings), len(pair_readings),
                  min(pair_readings), max(pair_readings),
                  sum(all_band), len(all_band)))

        # ---- AC-BI4: extract-side forgery floor + exact roundtrip -------
        readings4 = []
        for name in ("provider", "content_no", "label"):
            bits_p = track_payloads[name]
            sealed_p = seal(base_img, bits_p, tmp, name)
            ext_p = extract_bits(sealed_p, nbits)
            forg = ber(ext_p, bits_b)
            rt = ber(ext_p, bits_p)
            readings4.append((name, forg, rt))
        ok4 = all(forg >= FORGERY_FLOOR and rt == 0.0
                  for _, forg, rt in readings4)
        record("AC-BI4", ok4,
               "perturbed seals: " + "; ".join(
                   "%s vs-base ber=%.4f (floor>=%.2f) self ber=%.4f"
                   % (n, f, FORGERY_FLOOR, r) for n, f, r in readings4)
               + " (%d/%d readings produced)"
               % (2 * len(readings4), 2 * len(readings4)))

        # ---- AC-BI5: determinism, double-run bitwise identical -----------
        pre_b2 = preimage(PROVIDER, CONTENT_NO, label_text)
        bits_b2 = bits_of(pre_b2)
        sealed_b2 = seal(base_img, bits_b2, tmp, "b2")
        ext_b2 = extract_bits(sealed_b2, nbits)
        sealed_pp = seal(base_img, track_payloads["provider"], tmp, "p2")
        ext_pp = extract_bits(sealed_pp, nbits)
        same_bits = bool(np.array_equal(bits_b2, bits_b))
        same_base = bool(np.array_equal(ext_b2, ext_b))
        same_pert = bool(np.array_equal(ext_pp, extract_bits(
            os.path.join(tmp, "sealed_provider.png"), nbits)))
        ok5 = same_bits and same_base and same_pert
        record("AC-BI5", ok5,
               "double-run bitwise identity: bits=%s base-extract=%s "
               "provider-perturbed-extract=%s" % (same_bits, same_base,
                                                  same_pert))

        # ---- AC-BI6: hygiene ----------------------------------------------
        with open(os.path.abspath(__file__), "rb") as f:
            src_bytes = f.read()
        ascii_ok = all(b < 128 for b in src_bytes)
        import_lines = [ln.strip() for ln in src_bytes.decode("ascii"
                        ).splitlines()
                        if ln.strip().startswith("import ")
                        or ln.strip().startswith("from ")]
        net_hits = [ln for ln in import_lines
                    if any(w in ln for w in
                           ("urllib", "requests", "socket", "http"))]
        cfg_sha_after = hashlib.sha256(
            open(UGC_CFG, "rb").read()).hexdigest()[:16]
        cfg_untouched = cfg_sha_before == cfg_sha_after
        ok6 = ascii_ok and len(net_hits) == 0 and cfg_untouched
        record("AC-BI6", ok6,
               "ascii=%s true-import-lines=%d network-imports=%d "
               "config-sha16-unchanged=%s (read-only open, temp-dir-only "
               "writes)" % (ascii_ok, len(import_lines), len(net_hits),
                            cfg_untouched))

        # ---- AC-BI7: delivery wiring --------------------------------------
        all_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
        with open(all_path, encoding="utf-8") as fh:
            all_text = fh.read()
        wired = ('("watermark-bindbit",' in all_text
                 and "test_bind_bit.py" in all_text)
        prior = len(RESULTS)                      # six criteria before this
        ok7 = wired and prior == EXPECTED - 1
        record("AC-BI7", ok7,
               "suites-registry-line=%s prior-criteria=%d expected=%d"
               % (wired, prior, EXPECTED))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if len(RESULTS) != EXPECTED:
        print("SUITE FAIL: criteria drift %d != %d"
              % (len(RESULTS), EXPECTED))
        return 2
    failed = [ac for ac, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL: %s" % ",".join(failed))
        return 2
    print("SUITE PASS: %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
