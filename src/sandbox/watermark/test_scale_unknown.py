"""Unknown-scale-factor grid for the scale-family template-alignment
recovery path (BigDomain tech-queue item "watermark scaling-family
unknown-factor extension", direct successor of the R1707 two-probe
experiment whose 0.5x/2.0x probes were both RECOVERED with
windows hinted around the true factor; production threat is an
UNKNOWN arbitrary factor, so this suite sweeps four non-integer
factors {0.7x, 0.85x, 1.1x, 1.5x} through the FULL search domain
(0.3, 2.2) with no per-factor window hint injected. Hit rate inside
the full domain is the production-facing reading; negative verdicts
are lawful per pre-registration.

Pre-registered criteria (tech.md R1725 claim row, registered on
disk before this suite was executed):

  AC-UKF1 control anchor: default combo (d1=36/d2=20, 256-bit
         label, deterministic make_img image) clean embed ->
         extract roundtrip exact; anchor failure = whole suite FAIL
         and all other readings are not trusted (AC-WSR1 mirror).
  AC-UKF2 unknown-factor grid reproduction: four non-integer
         bilinear resizes {0.7x, 0.85x, 1.1x, 1.5x} (INTER_LINEAR,
         same code path and seed-image family as R552/R1680/R1707)
         direct-extract BER measured 4/4, zero silent skip;
         degradation confirmed per case (direct ber >= 0.4, DCT
         block-sync destruction family expectation; no recorded
         baseline for non-integer factors, so no cross-check gate =
         honest first measurement).
  AC-UKF3 full-domain blind recovery: per case library front door
         recover.estimate_crop_parameters(original=embedded,
         template=scaled, scale=(0.3, 2.2), search_num=200) -
         production simulation: the search domain spans all four
         true factors (true scale_infer = 1/fx in {1.4286, 1.1765,
         0.9091, 0.6667}), no per-case window hint injected ->
         scale_infer inside the per-case true-value +/-10% sanity
         band, loc coverage check inside the original canvas,
         recover_crop canvas rebuild -> recovered extract BER.
  AC-UKF4 verdict + hit-rate surface: per case a three-state
         VERDICT line (RECOVERED ber<=0.10 / IMPROVED
         0.10<ber<direct / NOT-RECOVERED ber>=direct), 4/4 on
         record + a HIT-RATE line (n/4 RECOVERED = full-domain
         blind hit-rate reading) + per-case comparison rows
         (DIRECT + RECOVERED: ber, delta, score, scale_infer, loc)
         8/8 rows; negative verdicts lawful per pre-registration.
  AC-UKF5 determinism: whole grid re-run in-suite; per case the
         two runs read bit-identical (ber, score to 6 decimals,
         scale_infer, loc all equal).
  AC-UKF6 hygiene: pure-ASCII source self-scan; real
         import-statement lines carry no network library (R1678
         self-hit lesson); zero shipped-config change; zero
         other-suite source change (reconcile_all SUITES wiring
         line only); suite writes only temp-dir artifacts.
  AC-UKF7 delivery: reconcile_all SUITES wiring
         (watermark-scale-unknown, criteria=6) + RUNNER full
         regression PASS + matrix regen --check byte-identical +
         evidence qa/watermark-scale-unknown-R1725.log + state log
         line + tech.md done note + commit message carries the seed
         (test_scale_recover.py R1707 on record).

Usage: python test_scale_unknown.py
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

# full blind search domain - spans all four true factors, no hint
SEARCH_DOMAIN = (0.3, 2.2)
SEARCH_NUM = 200
BAND_REL = 0.10          # scale_infer sanity band = true +/- 10%
# non-integer unknown-factor grid (production-facing threat model)
GRID = [
    ("down0.7x", 0.7),
    ("down0.85x", 0.85),
    ("up1.1x", 1.1),
    ("up1.5x", 1.5),
]

RESULTS = []
COMPARISON_ROWS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok), evidence))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def resize_bilinear(img, fx):
    # same code path as R552/R1680/R1707 scaling family
    return cv2.resize(img, None, fx=fx, fy=fx,
                      interpolation=cv2.INTER_LINEAR)


def verdict_state(rec_ber, dir_ber):
    if rec_ber <= 0.10:
        return "RECOVERED"
    if rec_ber < dir_ber:
        return "IMPROVED"
    return "NOT-RECOVERED"


def true_scale(fx):
    # template = fx * original -> scale param (original/template) = 1/fx
    return 1.0 / fx


def run_case(tmp, tag, emb, img_e, bits, nbits, fx):
    """One unknown-factor case: honest direct degradation read, then
    full-domain blind template-alignment recovery. Returns a
    readings dict; no pass/fail opinion here (criteria judge above).
    """
    scaled = resize_bilinear(img_e, fx)
    tpath = os.path.join(tmp, "scaled_%s.png" % tag)
    cv2.imwrite(tpath, scaled)
    got_direct = extract_bits(tpath, nbits)
    ber_direct = ber(got_direct, bits)

    loc, shape, score, scale_infer = estimate_crop_parameters(
        original_file=emb, template_file=tpath,
        scale=SEARCH_DOMAIN, search_num=SEARCH_NUM)
    rpath = os.path.join(tmp, "recovered_%s.png" % tag)
    recover_crop(template_file=tpath, output_file_name=rpath,
                 loc=loc, image_o_shape=shape)
    got_rec = extract_bits(rpath, nbits)
    ber_rec = ber(got_rec, bits)

    x1, y1, x2, y2 = [int(v) for v in loc]
    h_o, w_o = int(shape[0]), int(shape[1])
    cover = (0 <= x1 < x2 <= w_o) and (0 <= y1 < y2 <= h_o)
    t = true_scale(fx)
    band = (t * (1.0 - BAND_REL), t * (1.0 + BAND_REL))
    scale_ok = band[0] <= float(scale_infer) <= band[1]
    verdict = verdict_state(ber_rec, ber_direct)

    COMPARISON_ROWS.append(
        "DIRECT   %s fx=%.2f ber=%.4f" % (tag, fx, ber_direct))
    COMPARISON_ROWS.append(
        "RECOVERED %s ber=%.4f delta=%+.4f score=%.6f scale_infer=%s "
        "band=(%.4f,%.4f) true=%.4f loc=(%d,%d,%d,%d) canvas=%dx%d "
        "verdict=%s"
        % (tag, ber_rec, ber_rec - ber_direct, float(score),
           scale_infer, band[0], band[1], t, x1, y1, x2, y2, w_o, h_o,
           verdict))

    return {
        "tag": tag, "fx": fx, "ber_direct": ber_direct, "ber_rec": ber_rec,
        "score": float(score), "scale_infer": float(scale_infer),
        "loc": (x1, y1, x2, y2), "cover": cover, "scale_ok": scale_ok,
        "band": band, "verdict": verdict,
    }


def main():
    tmp = tempfile.mkdtemp(prefix="bd_ukf_")
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
        record("AC-UKF1", ok_embed and exact_clean,
               "control anchor: embed=%s wm_bits=%d clean-roundtrip-"
               "exact=%s" % (ok_embed, nbits, exact_clean))
        if not (ok_embed and exact_clean):
            print("SUITE FAIL (control anchor failed; recovery readings "
                  "not trusted)", flush=True)
            return 1
        img_e = cv2.imread(emb, cv2.IMREAD_COLOR)

        readings = {}
        for tag, fx in GRID:
            readings[tag] = run_case(tmp, tag, emb, img_e, bits, nbits,
                                     fx)

        # AC-UKF2: 4/4 direct reads produced + degradation confirmed
        d_ok = True
        d_ev = []
        for tag, r in readings.items():
            degraded = r["ber_direct"] >= 0.4
            d_ok = d_ok and degraded
            d_ev.append("%s fx=%.2f direct-ber=%.4f degraded=%s"
                        % (tag, r["fx"], r["ber_direct"],
                           "yes" if degraded else "NO"))
        record("AC-UKF2", d_ok,
               "unknown-factor grid reproduction: %s" % "; ".join(d_ev))

        # AC-UKF3: full-domain blind recovery, aggregated criterion
        # (per-case detail lines ride inside the evidence string)
        u3_ok = True
        u3_ev = []
        for tag, _fx in GRID:
            r = readings[tag]
            ok = r["scale_ok"] and r["cover"]
            u3_ok = u3_ok and ok
            u3_ev.append(
                "%s scale_infer=%.4f band=(%.4f,%.4f) true=%.4f "
                "band-ok=%s cover=%s score=%.6f recovered-ber=%.4f "
                "direct-ber=%.4f"
                % (tag, r["scale_infer"], r["band"][0], r["band"][1],
                   true_scale(r["fx"]), r["scale_ok"], r["cover"],
                   r["score"], r["ber_rec"], r["ber_direct"]))
        record("AC-UKF3", u3_ok,
               "full-domain blind recovery: %s" % "; ".join(u3_ev))

        # AC-UKF4: verdict + hit-rate surface on record
        for tag, _fx in GRID:
            r = readings[tag]
            print("  VERDICT %s %s" % (tag, r["verdict"]), flush=True)
        hits = sum(1 for r in readings.values()
                   if r["verdict"] == "RECOVERED")
        print("HIT-RATE %d/4 RECOVERED (full-domain blind search "
              "(%.1f,%.1f) search_num=%d)"
              % (hits, SEARCH_DOMAIN[0], SEARCH_DOMAIN[1], SEARCH_NUM),
              flush=True)
        for row in COMPARISON_ROWS:
            print("  | %s" % row, flush=True)
        v_ok = (len([r for r in readings.values()])
                == 4
                and len(COMPARISON_ROWS) == 8)
        record("AC-UKF4", v_ok,
               "verdict+hit-rate surface: 4/4 VERDICT lines + HIT-RATE "
               "line (%d/4 RECOVERED) + %d/8 comparison rows on record "
               "(negative verdicts lawful per pre-registration)"
               % (hits, len(COMPARISON_ROWS)))

        # AC-UKF5: determinism - re-run whole grid, readings equal
        det_ok = True
        det_ev = []
        for tag, fx in GRID:
            r2 = run_case(tmp, tag + "_det", emb, img_e, bits, nbits,
                          fx)
            r1 = readings[tag]
            same = (r1["ber_direct"] == r2["ber_direct"]
                    and r1["ber_rec"] == r2["ber_rec"]
                    and round(r1["score"], 6) == round(r2["score"], 6)
                    and r1["scale_infer"] == r2["scale_infer"]
                    and r1["loc"] == r2["loc"])
            det_ok = det_ok and same
            det_ev.append("%s rerun-identical=%s" % (tag, same))
        record("AC-UKF5", det_ok,
               "determinism: %s (comparison rows now %d incl. re-run)"
               % ("; ".join(det_ev), len(COMPARISON_ROWS)))

        # AC-UKF6: hygiene self-scan (own source only; no repo writes)
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
        record("AC-UKF6", ascii_ok and not bad_imports,
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
