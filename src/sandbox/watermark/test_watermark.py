"""Acceptance suite for the AIGC implicit watermark capability sandbox
(BigDomain P-47-3c; task source = P-2026-09-26-08 OSS first-window
adoption of guofei9987/blind_watermark, MIT; OH evidence chain at
docs/oss-harvest/OH-20260926-bigdomain.md).

Pre-registered criteria (backlog line / tasks.md P-47-3c), asserted
here in mechanical form; each criterion prints PASS/FAIL with
evidence and the process exits non-zero on any FAIL:

  AC-W1  capability: blind_watermark imports from the local pip
         install; a 256-bit label (SHA-256 of a fixed string) is
         embedded into a deterministic 640x480 test image and
         extracted in a temp dir:
           W1a clean embed -> extract roundtrip, exact
           W1b robustness case 1 (compression): JPEG re-save
                quality=90 -> extract exact
           W1c robustness case 2 (crop): central crop keep=85% ->
                direct extract degrades (honest negative recorded),
                library recover.py template-match locate + canvas
                rebuild -> extract exact
  AC-W2  dual-track design note: explicit-track anchors live in the
         ugc sandbox (config.json compliance.ai_label_text +
         pipeline.py ai_label draft field; actual line numbers are
         reported as evidence), and this implicit track is
         documented in docs/spec/implicit-watermark-verify.md with
         the production-wiring-deferred (bootstrap) note.
  AC-W3  OH five-gate evidence chain anchors: the OH slice file
         carries the candidate URL + MIT + five-gate table rows
         1..5, and the adoption registry row references the P-47-3c
         landing point.

AC-W4 (delivery carriers: backlog done line + state log line +
commit message containing P-2026-09-26-08) is satisfied by the
claiming round itself, not by this suite.

Usage: python test_watermark.py
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
from blind_watermark.recover import estimate_crop_parameters, recover_crop

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(BASE, "..", "..", ".."))
DOC = os.path.join(ROOT, "docs", "spec", "implicit-watermark-verify.md")
OH = os.path.join(ROOT, "docs", "oss-harvest", "OH-20260926-bigdomain.md")
REG = os.path.join(ROOT, "docs", "oss-harvest", "README.md")
UGC_CFG = os.path.join(ROOT, "src", "sandbox", "ugc", "config.json")
UGC_PIPE = os.path.join(ROOT, "src", "sandbox", "ugc", "pipeline.py")

LABEL = "BigDomain-AIGC-implicit-label-v1"
JPEG_Q = 90       # robustness case 1, locked at calibration (probe)
CROP_KEEP = 0.85  # robustness case 2, locked at calibration (probe)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def label_bits():
    digest = hashlib.sha256(LABEL.encode("utf-8")).digest()
    return np.unpackbits(np.frombuffer(digest, dtype=np.uint8))


def make_img():
    rng = np.random.default_rng(20260926)
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


def ber(got, want):
    return float(np.mean(got != want))


def main():
    tmp = tempfile.mkdtemp(prefix="bd_wm_")
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
        exact = bool(np.array_equal(extract_bits(emb, nbits), bits)) \
            if ok_embed else False
        record("AC-W1a", ok_embed and exact,
               "local pip import ok; embed=%s wm_bits=%d clean-roundtrip"
               "-exact=%s" % (ok_embed, nbits, exact))

        img_e = cv2.imread(emb, cv2.IMREAD_COLOR) if ok_embed else None
        jpg = os.path.join(tmp, "embedded_q%d.jpg" % JPEG_Q)
        ok_write = img_e is not None and cv2.imwrite(
            jpg, img_e, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_Q])
        got = extract_bits(jpg, nbits) if ok_write else None
        record("AC-W1b",
               ok_write and bool(np.array_equal(got, bits)),
               "compression case: jpeg-resave q=%d write=%s exact=%s ber=%.4f"
               % (JPEG_Q, ok_write,
                  bool(np.array_equal(got, bits)) if got is not None else False,
                  ber(got, bits) if got is not None else 1.0))

        h, w = img_e.shape[:2]
        ch, cw = int(h * CROP_KEEP), int(w * CROP_KEEP)
        y0, x0 = (h - ch) // 2, (w - cw) // 2
        crop = os.path.join(tmp, "crop_%d.png" % int(CROP_KEEP * 100))
        cv2.imwrite(crop, img_e[y0:y0 + ch, x0:x0 + cw])
        got_direct = extract_bits(crop, nbits)
        direct_degrades = not np.array_equal(got_direct, bits)
        loc, shape, score, _scale = estimate_crop_parameters(
            original_file=emb, template_file=crop,
            scale=(1, 1), search_num=1)
        rec = os.path.join(tmp, "recovered.png")
        recover_crop(template_file=crop, output_file_name=rec,
                     loc=loc, image_o_shape=shape)
        got_rec = extract_bits(rec, nbits)
        record("AC-W1c", direct_degrades and bool(np.array_equal(got_rec,
                                                                 bits)),
               "crop case: keep=%.2f direct-extract-exact=%s (ber=%.4f, "
               "honest negative) -> recover.py locate-score=%.3f loc=%s "
               "recovered-extract-exact=%s"
               % (CROP_KEEP, not direct_degrades, ber(got_direct, bits),
                  float(score), tuple(int(v) for v in loc),
                  bool(np.array_equal(got_rec, bits))))

        with open(UGC_CFG, "r", encoding="utf-8") as fh:
            cfg_text = fh.read()
        cfg = json.loads(cfg_text)
        explicit_label = (cfg.get("compliance") or {}).get("ai_label_text", "")
        cfg_line = next((i + 1 for i, ln in enumerate(cfg_text.splitlines())
                         if '"ai_label_text"' in ln), -1)
        with open(UGC_PIPE, "r", encoding="utf-8") as fh:
            pipe_text = fh.read()
        pipe_line = next((i + 1 for i, ln in enumerate(pipe_text.splitlines())
                          if '"ai_label"' in ln), -1)
        with open(DOC, "r", encoding="utf-8") as fh:
            doc_text = fh.read()
        ok = (isinstance(explicit_label, str) and explicit_label != ""
              and cfg_line > 0 and pipe_line > 0
              and "AC-W2" in doc_text and "bootstrap" in doc_text)
        record("AC-W2", ok,
               "explicit track: ugc config.json L%d ai_label_text set=%s +"
               " pipeline.py L%d ai_label draft field; implicit track doc"
               " present=%s with dual-track + bootstrap-deferred note"
               % (cfg_line, explicit_label != "", pipe_line,
                  os.path.exists(DOC)))

        with open(OH, "r", encoding="utf-8") as fh:
            oh_text = fh.read()
        with open(REG, "r", encoding="utf-8") as fh:
            reg_text = fh.read()
        gates = all(("| %d " % n) in oh_text for n in range(1, 6))
        cand_mit = ("guofei9987/blind_watermark" in oh_text
                    and "MIT" in oh_text)
        reg_row = ("P-47-3c" in reg_text and "blind_watermark" in reg_text)
        record("AC-W3", gates and cand_mit and reg_row,
               "OH five-gate rows 1..5=%s candidate+MIT=%s registry "
               "P-47-3c adoption row=%s"
               % (gates, cand_mit, reg_row))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    fails = [ac for ac, ok in RESULTS if not ok]
    total = len(RESULTS)
    print("SUITE %s (%d/%d criteria pass)" % ("PASS" if not fails else "FAIL",
                                              total - len(fails), total), flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
