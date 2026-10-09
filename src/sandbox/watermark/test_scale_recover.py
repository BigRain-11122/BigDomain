"""Scale-family template-alignment recovery experiment for the AIGC
implicit watermark sandbox (BigDomain tech-queue item "watermark
scaling-family template-alignment recovery experiment", direct
successor of the R1680 DCT parameter sweep whose scaling family read
ber=0.5195/0.5000 and was judged negative - no near-survival band
inside the quantization-step x repetition-factor grid; the sweep's
recorded verdict names template alignment (recover.py, W1c
precedent) as the only remaining path for the scaling family).
Pre-registered criteria live in the tech.md R1707 claim row,
registered on disk before this suite was executed.

Pre-registered criteria (tech.md R1707 claim row):

  AC-WSR1 control anchor: default combo (d1=36/d2=20, 256-bit label,
         deterministic make_img image) clean embed -> extract
         roundtrip exact; anchor failure = whole suite FAIL and all
         other readings are not trusted (AC-EX0 mirror).
  AC-WSR2 family reproduction honest negative: 0.5x and 2.0x
         bilinear resizes (same code path and seed image as
         R552/R1680) direct-extract BER measured for both cases;
         degradation confirmed (direct ber >= 0.4); cross-check note
         against the R1680 recorded values 0.5195/0.5000 (tolerance
         0.05, no floating-point equality gate).
  AC-WSR3 downscale recovery: library front door
         recover.estimate_crop_parameters(original=embedded,
         template=half, scale=(1.0, 2.2), search_num=200) template
         alignment (W1c same library same door) -> scale_infer inside
         tolerance band [1.8, 2.2], loc coverage check inside the
         original canvas, recover_crop canvas rebuild -> recovered
         extract BER reading + three-state VERDICT line (RECOVERED
         ber<=0.10 / IMPROVED 0.10<ber<direct / NOT-RECOVERED
         ber>=direct); the verdict line on record = pass, a negative
         verdict is lawful per pre-registration.
  AC-WSR4 upscale recovery: template=double (1280x960),
         scale=(0.3, 0.6) -> scale_infer inside [0.45, 0.55], loc
         coverage check, same three-state verdict line.
  AC-WSR5 comparison surface: per case a DIRECT row and a RECOVERED
         row (direct ber, recovered ber, delta, score, scale_infer,
         loc); 4/4 comparison rows on record, zero silent skip.
  AC-WSR6 determinism: both recovery pipelines re-run in-suite; the
         two runs read bit-identical (ber, score to 6 decimals,
         scale_infer, loc all equal).
  AC-WSR7 hygiene: pure-ASCII source self-scan; real import-statement
         lines carry no network library (R1678 self-hit lesson);
         zero shipped-config change (evidence log carries git
         status; this suite touches no repo file outside qa/ logs).

Usage: python test_scale_recover.py
"""

import os
import shutil
import sys
import tempfile

import cv2
import numpy as np
from blind_watermark import WaterMark
from blind_watermark.recover import estimate_crop_parameters, recover_crop

from test_watermark import ber, extract_bits, label_bits, make_img

SCALE_DOWN = 0.5
SCALE_UP = 2.0
DOWN_SEARCH = (1.0, 2.2)   # expected scale_infer = 2.0 (template=half)
UP_SEARCH = (0.3, 0.6)     # expected scale_infer = 0.5 (template=double)
DOWN_BAND = (1.8, 2.2)
UP_BAND = (0.45, 0.55)
SEARCH_NUM = 200
R1680_DOWN_BER = 0.5195    # recorded reading, cross-check tolerance 0.05
R1680_UP_BER = 0.5000
XCHECK_TOL = 0.05

RESULTS = []
COMPARISON_ROWS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok), evidence))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def resize_bilinear(img, fx):
    # same code path as R552/R1680 scaling family
    return cv2.resize(img, None, fx=fx, fy=fx,
                      interpolation=cv2.INTER_LINEAR)


def verdict_state(rec_ber, dir_ber):
    if rec_ber <= 0.10:
        return "RECOVERED"
    if rec_ber < dir_ber:
        return "IMPROVED"
    return "NOT-RECOVERED"


def run_case(tmp, tag, emb, img_e, bits, nbits, fx, search, band):
    """One scale-family case: reproduce honest negative, then attempt
    template-alignment recovery via the library front door. Returns a
    readings dict; no pass/fail opinion here (criteria judge above).
    """
    scaled = resize_bilinear(img_e, fx)
    tpath = os.path.join(tmp, "scaled_%s.png" % tag)
    cv2.imwrite(tpath, scaled)
    got_direct = extract_bits(tpath, nbits)
    ber_direct = ber(got_direct, bits)

    loc, shape, score, scale_infer = estimate_crop_parameters(
        original_file=emb, template_file=tpath,
        scale=search, search_num=SEARCH_NUM)
    rpath = os.path.join(tmp, "recovered_%s.png" % tag)
    recover_crop(template_file=tpath, output_file_name=rpath,
                 loc=loc, image_o_shape=shape)
    got_rec = extract_bits(rpath, nbits)
    ber_rec = ber(got_rec, bits)

    x1, y1, x2, y2 = [int(v) for v in loc]
    h_o, w_o = int(shape[0]), int(shape[1])
    cover = (0 <= x1 < x2 <= w_o) and (0 <= y1 < y2 <= h_o)
    scale_ok = band[0] <= float(scale_infer) <= band[1]
    verdict = verdict_state(ber_rec, ber_direct)

    COMPARISON_ROWS.append(
        "DIRECT   %s fx=%.2f ber=%.4f" % (tag, fx, ber_direct))
    COMPARISON_ROWS.append(
        "RECOVERED %s ber=%.4f delta=%+.4f score=%.6f scale_infer=%s "
        "loc=(%d,%d,%d,%d) canvas=%dx%d verdict=%s"
        % (tag, ber_rec, ber_rec - ber_direct, float(score),
           scale_infer, x1, y1, x2, y2, w_o, h_o, verdict))

    return {
        "tag": tag, "ber_direct": ber_direct, "ber_rec": ber_rec,
        "score": float(score), "scale_infer": float(scale_infer),
        "loc": (x1, y1, x2, y2), "cover": cover, "scale_ok": scale_ok,
        "verdict": verdict,
    }


def main():
    tmp = tempfile.mkdtemp(prefix="bd_wmsr_")
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
        record("AC-WSR1", ok_embed and exact_clean,
               "control anchor: embed=%s wm_bits=%d clean-roundtrip-"
               "exact=%s" % (ok_embed, nbits, exact_clean))
        if not (ok_embed and exact_clean):
            print("SUITE FAIL (control anchor failed; recovery readings "
                  "not trusted)", flush=True)
            return 1
        img_e = cv2.imread(emb, cv2.IMREAD_COLOR)

        cases = {
            "down0.5x": (SCALE_DOWN, DOWN_SEARCH, DOWN_BAND,
                         R1680_DOWN_BER),
            "up2.0x": (SCALE_UP, UP_SEARCH, UP_BAND, R1680_UP_BER),
        }
        readings = {}
        for tag, (fx, search, band, r1680) in cases.items():
            readings[tag] = run_case(tmp, tag, emb, img_e, bits, nbits,
                                     fx, search, band)

        # AC-WSR2: both direct reads produced + degradation confirmed
        # + cross-check note vs R1680 recorded values (tolerance gate)
        d_ok = True
        d_ev = []
        for tag, r in readings.items():
            r1680 = cases[tag][3]
            inside = abs(r["ber_direct"] - r1680) <= XCHECK_TOL
            d_ok = d_ok and r["ber_direct"] >= 0.4 and inside
            d_ev.append("%s direct-ber=%.4f (R1680=%.4f xcheck-tol-%s)"
                        % (tag, r["ber_direct"], r1680,
                           "ok" if inside else "OUT"))
        record("AC-WSR2", d_ok,
               "family reproduction honest negative: %s" % "; ".join(d_ev))

        # AC-WSR3 / AC-WSR4: per-case recovery criteria
        for ac, tag in (("AC-WSR3", "down0.5x"), ("AC-WSR4", "up2.0x")):
            r = readings[tag]
            ok = r["scale_ok"] and r["cover"]
            record(ac, ok,
                   "%s template-alignment: scale_infer=%.4f band-ok=%s "
                   "loc=%s cover=%s score=%.6f recovered-ber=%.4f "
                   "direct-ber=%.4f VERDICT=%s"
                   % (tag, r["scale_infer"], r["scale_ok"], r["loc"],
                      r["cover"], r["score"], r["ber_rec"],
                      r["ber_direct"], r["verdict"]))

        # AC-WSR5: 4/4 comparison rows on record
        for row in COMPARISON_ROWS:
            print("  | %s" % row, flush=True)
        record("AC-WSR5", len(COMPARISON_ROWS) == 4,
               "comparison surface: %d/4 rows on record (2 DIRECT + "
               "2 RECOVERED, zero silent skip)"
               % len(COMPARISON_ROWS))

        # AC-WSR6: determinism - re-run both pipelines, readings equal
        det_ok = True
        det_ev = []
        for tag, (fx, search, band, _r) in cases.items():
            r2 = run_case(tmp, tag + "_det", emb, img_e, bits, nbits,
                          fx, search, band)
            r1 = readings[tag]
            same = (r1["ber_direct"] == r2["ber_direct"]
                    and r1["ber_rec"] == r2["ber_rec"]
                    and round(r1["score"], 6) == round(r2["score"], 6)
                    and r1["scale_infer"] == r2["scale_infer"]
                    and r1["loc"] == r2["loc"])
            det_ok = det_ok and same
            det_ev.append("%s rerun-identical=%s" % (tag, same))
        # determinism re-run adds 2 more comparison rows -> 6 total
        record("AC-WSR6", det_ok,
               "determinism: %s (comparison rows now %d incl. re-run)"
               % ("; ".join(det_ev), len(COMPARISON_ROWS)))

        # AC-WSR7: hygiene self-scan (own source only; no repo writes)
        src = os.path.abspath(__file__)
        with open(src, "rb") as fh:
            raw = fh.read()
        ascii_ok = all(b < 128 for b in raw)
        bad_imports = []
        with open(src, "r", encoding="ascii") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped.startswith("import ") or \
                        stripped.startswith("from "):
                    head = stripped.split()[1].split(".")[0]
                    if head in ("urllib", "requests", "socket", "http",
                                "httpx", "ftplib"):
                        bad_imports.append(head)
        record("AC-WSR7", ascii_ok and not bad_imports,
               "hygiene: source-ascii=%s bad-imports=%s; suite writes "
               "only temp-dir artifacts (zero repo/config touch)"
               % (ascii_ok, bad_imports or "none"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    fails = [ac for ac, ok, _ev in RESULTS if not ok]
    total = len(RESULTS)
    print("SUITE %s (%d/%d criteria pass)"
          % ("PASS" if not fails else "FAIL", total - len(fails), total),
          flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
