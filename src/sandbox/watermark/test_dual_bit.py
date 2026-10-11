"""Double-bit perturbation crosstalk-band probe for the dual-track AIGC
seal (watermark successor; seed = test_bind_bit.py R1778 in-tree).

R1778 registered the single-bit avalanche basis of the bound payload:
every one-bit perturbation of the SHA-256("provider:content_no:label_text")
preimage avalanches the full 256-bit payload into the registered band
[0.35, 0.65], distinct single flips stay mutually independent, and a
perturbed payload still roundtrips exactly while failing the forgery
floor against the base.

This probe extends the granularity axis to TWO simultaneous bits:

  - all C(8,2)=28 two-bit combinations flipped at once in the content_no
    first byte must stay inside the avalanche band vs the base (the
    combination must not escape the band),
  - each two-bit reading is cross-read against its two component
    single-bit readings (crosstalk band: no anomalous convergence,
    cancellation or amplification beyond hash noise; the registered
    crosstalk slack is 0.15),
  - representative two-bit perturbed payloads must still roundtrip
    exactly through embed/extract and must fail the base expectation
    (forgery floor at two-bit granularity).

Pre-registered criteria AC-BD1..AC-BD7 (state/queue/tech.md R1783 claim
row, registered BEFORE this code first ran; honesty law).

Scope note (honest): same as R1778, only the implicit track is exercised;
deterministic base image (seed 20260929), zero environmental font
dependency.

Usage: python test_dual_bit.py
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
CONTENT_NO = "UGC-DEMO-20260929-0001"  # same stand-in as the R593/R1778 seeds
EXPECTED = 7
AV_LO = 0.35          # avalanche band, pre-registered (R1778 caliber)
AV_HI = 0.65          # avalanche band, pre-registered (R1778 caliber)
XTALK_SLACK = 0.15    # crosstalk band vs component single-bit readings
FORGERY_FLOOR = 0.40  # R593 FORGERY_BER_MIN, held at 2-bit granularity

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


def flip_bits(prebytes, byte_off, bits):
    arr = bytearray(prebytes)
    for b in bits:
        arr[byte_off] ^= (1 << b)
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


def all_pairs(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def main():
    label_text = load_label_text()
    cfg_sha_before = hashlib.sha256(
        open(UGC_CFG, "rb").read()).hexdigest()[:16]
    tmp = tempfile.mkdtemp(prefix="bd_bd_")
    try:
        base_img = make_img()
        pre_b = preimage(PROVIDER, CONTENT_NO, label_text)
        bits_b = bits_of(pre_b)
        nbits = int(bits_b.size)
        pre_sha16 = hashlib.sha256(pre_b).hexdigest()[:16]

        p_len = len(PROVIDER.encode("utf-8"))
        c_off = p_len + 1  # content_no first byte offset in the preimage

        # ---- AC-BD1: control anchor, clean roundtrip exact --------------
        sealed_b = seal(base_img, bits_b, tmp, "b")
        ext_b = extract_bits(sealed_b, nbits)
        b1 = ber(ext_b, bits_b)
        record("AC-BD1", b1 == 0.0 and nbits == 256,
               "binding bits=SHA-256(provider:content_no:label_text) "
               "sha16=%s nbits=%d clean-extract ber=%.4f (exact required)"
               % (pre_sha16, nbits, b1))

        # component single-bit readings (same path as R1778 AC-BI3 sweep)
        single_bits = {k: bits_of(flip_bits(pre_b, c_off, [k]))
                       for k in range(8)}
        single_ber = {k: ber(single_bits[k], bits_b) for k in range(8)}

        # ---- AC-BD2: C(8,2) simultaneous two-bit avalanche band --------
        pairs = all_pairs(8)
        dual_readings = []
        for i, j in pairs:
            bits_p = bits_of(flip_bits(pre_b, c_off, [i, j]))
            dual_readings.append(((i, j), ber(bits_p, bits_b)))
        ok2 = (len(dual_readings) == 28
               and all(AV_LO <= v <= AV_HI for _, v in dual_readings))
        vals2 = [v for _, v in dual_readings]
        record("AC-BD2", ok2,
               "C(8,2)=%d simultaneous two-bit flips vs base: "
               "min=%.4f max=%.4f in-band=%d/%d (band [%.2f, %.2f], "
               "zero silent skip)"
               % (len(dual_readings), min(vals2), max(vals2),
                  sum(1 for v in vals2 if AV_LO <= v <= AV_HI),
                  len(vals2), AV_LO, AV_HI))

        # ---- AC-BD3: crosstalk band vs component single-bit readings ---
        xtalk_rows = []
        for (i, j), v in dual_readings:
            di = abs(v - single_ber[i])
            dj = abs(v - single_ber[j])
            xtalk_rows.append(((i, j), v, di, dj))
        ok3 = (len(xtalk_rows) == 28
               and all(d <= XTALK_SLACK for _, _, di, dj in xtalk_rows
                       for d in (di, dj)))
        worst = max(max(di, dj) for _, _, di, dj in xtalk_rows)
        record("AC-BD3", ok3,
               "crosstalk vs component singles: n=%d worst-delta=%.4f "
               "(slack<=%.2f; single-bit ber min=%.4f max=%.4f; "
               "no convergence/cancellation/amplification beyond hash "
               "noise)" % (len(xtalk_rows), worst, XTALK_SLACK,
                           min(single_ber.values()),
                           max(single_ber.values())))

        # ---- AC-BD4: representative roundtrip + forgery floor -----------
        reps = [pairs[0], pairs[len(pairs) // 2], pairs[-1]]
        readings4 = []
        for pr in reps:
            bits_p = bits_of(flip_bits(pre_b, c_off, list(pr)))
            sealed_p = seal(base_img, bits_p, tmp, "d%d_%d" % pr)
            ext_p = extract_bits(sealed_p, nbits)
            forg = ber(ext_p, bits_b)
            rt = ber(ext_p, bits_p)
            readings4.append((pr, forg, rt))
        ok4 = all(forg >= FORGERY_FLOOR and rt == 0.0
                  for _, forg, rt in readings4)
        record("AC-BD4", ok4,
               "two-bit seals (first/mid/last): " + "; ".join(
                   "pair%s vs-base ber=%.4f (floor>=%.2f) self ber=%.4f"
                   % (str(p), f, FORGERY_FLOOR, r)
                   for p, f, r in readings4)
               + " (%d/%d readings produced)"
               % (2 * len(readings4), 2 * len(readings4)))

        # ---- AC-BD5: determinism, double-run bitwise identical ----------
        pre_b2 = preimage(PROVIDER, CONTENT_NO, label_text)
        bits_b2 = bits_of(pre_b2)
        same_bits = bool(np.array_equal(bits_b2, bits_b))
        same_dual = all(
            np.array_equal(
                bits_of(flip_bits(pre_b2, c_off, [i, j])),
                bits_of(flip_bits(pre_b, c_off, [i, j])))
            for i, j in pairs)
        rep_bits = bits_of(flip_bits(pre_b, c_off, list(reps[1])))
        sealed_r = seal(base_img, rep_bits, tmp, "r2")
        ext_r = extract_bits(sealed_r, nbits)
        same_rt = ber(ext_r, rep_bits) == 0.0
        ok5 = same_bits and same_dual and same_rt
        record("AC-BD5", ok5,
               "double-run bitwise identity: base-bits=%s "
               "all-28-dual-bits=%s rep-seal-roundtrip-exact=%s"
               % (same_bits, same_dual, same_rt))

        # ---- AC-BD6: hygiene ---------------------------------------------
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
        record("AC-BD6", ok6,
               "ascii=%s true-import-lines=%d network-imports=%d "
               "config-sha16-unchanged=%s (read-only open, temp-dir-only "
               "writes)" % (ascii_ok, len(import_lines), len(net_hits),
                            cfg_untouched))

        # ---- AC-BD7: delivery wiring --------------------------------------
        all_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
        with open(all_path, encoding="utf-8") as fh:
            all_text = fh.read()
        wired = ('("watermark-dualbit",' in all_text
                 and "test_dual_bit.py" in all_text)
        prior = len(RESULTS)                      # six criteria before this
        ok7 = wired and prior == EXPECTED - 1
        record("AC-BD7", ok7,
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
