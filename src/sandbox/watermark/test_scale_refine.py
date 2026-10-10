"""Search-refinement experiment for the R1725 IMPROVED case: the
0.7x downscale probe whose direct-extract BER (0.4883) was improved
to 0.2891 by full-domain blind template-alignment recovery, but did
not reach the 0.10 near-survival band. This suite measures whether
the two refinement levers named in the tech-queue seed can push that
case into the band: (a) search_num expansion {500, 1000} on the full
domain, and (b) a two-round window-narrowing pass (round 1 coarse
estimate, round 2 re-estimate inside est1*0.98..est1*1.02 at
search_num=1000). The residual after exact scale_infer hit is
attributed to 0.7x downscale interpolation information loss, so a
NOT-IMPROVED verdict is an expected lawful outcome per
pre-registration (the reading itself is the deliverable).

Pre-registered criteria (tech.md R1747 claim row, registered on
disk before this suite was executed):

  AC-UKR1 control anchor + baseline reproduction: default combo
         clean embed -> extract exact (anchor failure = whole suite
         FAIL, other readings not trusted; AC-WSR1/UKF1 mirror) and
         the 0.7x baseline reproduced - direct BER + R1725-path
         recovery (search=200, full domain) fully measured with a
         cross-verification note against the in-book values
         (direct 0.4883 / recovered 0.2891); no float-equality gate
         (honest re-measurement).
  AC-UKR2 search_num expansion grid: levels {500, 1000} on the full
         domain (0.3, 2.2) against the SAME 0.7x template - per
         level scale_infer/loc/score + recover_crop recovered BER,
         2/2 readings produced, zero silent skip.
  AC-UKR3 two-round window narrowing: round 1 = baseline estimate
         est1; round 2 = re-estimate inside (est1*0.98, est1*1.02)
         at search_num=1000 -> est2 inside the true-value +/-10%
         band + loc coverage check + recovered BER reading.
  AC-UKR4 verdict surface: four paths (baseline-repro / search500 /
         search1000 / two-round) each carry a three-state VERDICT
         (REFINED-RECOVERED ber<=0.10 / IMPROVED 0.10<ber<baseline
         / NOT-IMPROVED ber>=baseline) + best-path naming line +
         final verdict line (can 0.7x refinement reach the 0.10
         band) - negative verdicts lawful per pre-registration.
  AC-UKR5 determinism: all four paths re-run in-suite; per path the
         two runs read bit-identical (ber, score to 6 decimals,
         scale_infer, loc).
  AC-UKR6 hygiene: pure-ASCII source self-scan; real import lines
         carry no network library (R1678 self-hit lesson); zero
         shipped-config change; zero other-suite source change
         (reconcile_all SUITES wiring line only); suite writes only
         temp-dir artifacts.

Delivery vehicle (AC-UKR7, not a record() criterion): reconcile_all
SUITES wiring (watermark-scale-refine, criteria=6) + RUNNER full
regression PASS + matrix regen --check byte-identical + evidence
qa/watermark-scale-refine-R1747.log + implicit-watermark-verify.md
production-tuning note + state log line + tech.md done note +
commit message carries the seed (test_scale_unknown.py R1725).

Usage: python test_scale_refine.py
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

# R1725 in-book reference readings for the 0.7x case (cross-check
# note only - no float-equality gate; honest re-measurement)
INBOOK_DIRECT_BER = 0.4883
INBOOK_RECOVERED_BER = 0.2891

SEARCH_DOMAIN = (0.3, 2.2)   # full blind domain, same as R1725
BASELINE_SEARCH_NUM = 200
EXPAND_GRID = (500, 1000)
BAND_REL = 0.10              # est2 sanity band = true value +/- 10%
TRUE_SCALE = 1.0 / 0.7        # 1.428571... (template = 0.7x original)
FX = 0.7

RESULTS = []
COMPARISON_ROWS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok), evidence))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def refine_verdict(rec_ber, base_ber):
    if rec_ber <= 0.10:
        return "REFINED-RECOVERED"
    if rec_ber < base_ber:
        return "IMPROVED"
    return "NOT-IMPROVED"


def estimate_and_recover(emb, tpath, rpath, nbits, bits,
                         scale_window, search_num):
    """One estimate+recover path. Returns a readings dict."""
    loc, shape, score, scale_infer = estimate_crop_parameters(
        original_file=emb, template_file=tpath,
        scale=scale_window, search_num=search_num)
    recover_crop(template_file=tpath, output_file_name=rpath, loc=loc,
                 image_o_shape=shape)
    got = extract_bits(rpath, nbits)
    x1, y1, x2, y2 = [int(v) for v in loc]
    h_o, w_o = int(shape[0]), int(shape[1])
    cover = (0 <= x1 < x2 <= w_o) and (0 <= y1 < y2 <= h_o)
    return {
        "ber": ber(got, bits), "score": float(score),
        "scale_infer": float(scale_infer), "loc": (x1, y1, x2, y2),
        "cover": cover,
    }


def main():
    tmp = tempfile.mkdtemp(prefix="bd_ukr_")
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

        # one shared 0.7x template for every path (same code path and
        # seed-image family as R552/R1680/R1707/R1725)
        img_e = cv2.imread(emb, cv2.IMREAD_COLOR)
        scaled = cv2.resize(img_e, None, fx=FX, fy=FX,
                            interpolation=cv2.INTER_LINEAR)
        tpath = os.path.join(tmp, "scaled_0p7x.png")
        cv2.imwrite(tpath, scaled)
        ber_direct = ber(extract_bits(tpath, nbits), bits)

        if not (ok_embed and exact_clean):
            record("AC-UKR1", False,
                   "control anchor failed: embed=%s clean-exact=%s "
                   "(recovery readings not trusted)"
                   % (ok_embed, exact_clean))
            print("SUITE FAIL (control anchor failed)", flush=True)
            return 1

        # --- path 1: baseline reproduction (R1725 path) -----------
        rpath = os.path.join(tmp, "rec_baseline200.png")
        base = estimate_and_recover(emb, tpath, rpath, nbits, bits,
                                    SEARCH_DOMAIN, BASELINE_SEARCH_NUM)
        record("AC-UKR1", True,
               "control anchor: clean-roundtrip-exact=%s wm_bits=%d; "
               "baseline repro: direct-ber=%.4f (in-book %.4f) "
               "recovered-ber=%.4f (in-book %.4f) scale_infer=%.4f "
               "true=%.4f - cross-check note, no float-equality gate"
               % (exact_clean, nbits, ber_direct, INBOOK_DIRECT_BER,
                  base["ber"], INBOOK_RECOVERED_BER,
                  base["scale_infer"], TRUE_SCALE))

        # --- path 2/3: search_num expansion grid -------------------
        grid = {}
        for n in EXPAND_GRID:
            rpath = os.path.join(tmp, "rec_search%d.png" % n)
            grid[n] = estimate_and_recover(
                emb, tpath, rpath, nbits, bits, SEARCH_DOMAIN, n)
        g_ok = all(n in grid for n in EXPAND_GRID)
        g_ev = []
        for n in EXPAND_GRID:
            r = grid[n]
            g_ev.append(
                "search%d: ber=%.4f scale_infer=%.4f score=%.6f "
                "loc=%s cover=%s"
                % (n, r["ber"], r["scale_infer"], r["score"],
                   r["loc"], r["cover"]))
        record("AC-UKR2", g_ok,
               "search_num expansion grid: %s" % "; ".join(g_ev))

        # --- path 4: two-round window narrowing --------------------
        est1 = base["scale_infer"]
        window2 = (est1 * 0.98, est1 * 1.02)
        rpath = os.path.join(tmp, "rec_tworound.png")
        two = estimate_and_recover(emb, tpath, rpath, nbits, bits,
                                   window2, 1000)
        band = (TRUE_SCALE * (1.0 - BAND_REL),
                TRUE_SCALE * (1.0 + BAND_REL))
        est2_band_ok = band[0] <= two["scale_infer"] <= band[1]
        record("AC-UKR3", est2_band_ok and two["cover"],
               "two-round: est1=%.4f window2=(%.4f,%.4f) est2=%.4f "
               "band=(%.4f,%.4f) band-ok=%s cover=%s ber=%.4f "
               "score=%.6f"
               % (est1, window2[0], window2[1], two["scale_infer"],
                  band[0], band[1], est2_band_ok, two["cover"],
                  two["ber"], two["score"]))

        # --- AC-UKR4: verdict surface ------------------------------
        paths = {
            "baseline-repro": base,
            "search500": grid[500],
            "search1000": grid[1000],
            "two-round": two,
        }
        base_ber = base["ber"]
        for tag, r in paths.items():
            v = refine_verdict(r["ber"], base_ber)
            r["verdict"] = v
            print("  VERDICT %s %s (ber=%.4f baseline=%.4f)"
                  % (tag, v, r["ber"], base_ber), flush=True)
            COMPARISON_ROWS.append(
                "%s ber=%.4f verdict=%s scale_infer=%.4f score=%.6f "
                "loc=%s" % (tag, r["ber"], v, r["scale_infer"],
                            r["score"], r["loc"]))
        best_tag = min(paths, key=lambda t: paths[t]["ber"])
        best = paths[best_tag]
        reached = best["ber"] <= 0.10
        print("BEST-PATH %s ber=%.4f verdict=%s"
              % (best_tag, best["ber"], best["verdict"]), flush=True)
        print("FINAL-VERDICT 0.7x refinement reached 0.10 band: %s"
              % ("YES" if reached else "NO"), flush=True)
        for row in COMPARISON_ROWS:
            print("  | %s" % row, flush=True)
        v_ok = (len(paths) == 4
                and all("verdict" in r for r in paths.values())
                and len(COMPARISON_ROWS) == 4)
        record("AC-UKR4", v_ok,
               "verdict surface: 4/4 VERDICT lines + best-path=%s "
               "(ber=%.4f) + final=%s (negative lawful per "
               "pre-registration)"
               % (best_tag, best["ber"],
                  "REACHED" if reached else "not-reached"))

        # --- AC-UKR5: determinism ---------------------------------
        rerun = {
            "baseline-repro": estimate_and_recover(
                emb, tpath, os.path.join(tmp, "det_base.png"),
                nbits, bits, SEARCH_DOMAIN, BASELINE_SEARCH_NUM),
            "search500": estimate_and_recover(
                emb, tpath, os.path.join(tmp, "det_500.png"),
                nbits, bits, SEARCH_DOMAIN, 500),
            "search1000": estimate_and_recover(
                emb, tpath, os.path.join(tmp, "det_1000.png"),
                nbits, bits, SEARCH_DOMAIN, 1000),
            "two-round": estimate_and_recover(
                emb, tpath, os.path.join(tmp, "det_two.png"),
                nbits, bits, window2, 1000),
        }
        det_ok = True
        det_ev = []
        for tag, r1 in paths.items():
            r2 = rerun[tag]
            same = (r1["ber"] == r2["ber"]
                    and round(r1["score"], 6) == round(r2["score"], 6)
                    and r1["scale_infer"] == r2["scale_infer"]
                    and r1["loc"] == r2["loc"])
            det_ok = det_ok and same
            det_ev.append("%s rerun-identical=%s" % (tag, same))
        record("AC-UKR5", det_ok,
               "determinism: %s" % "; ".join(det_ev))

        # --- AC-UKR6: hygiene --------------------------------------
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
        record("AC-UKR6", ascii_ok and not bad_imports,
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
