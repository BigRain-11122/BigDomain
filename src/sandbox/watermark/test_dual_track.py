"""Dual-track AIGC labeling capability suite (BigDomain explore-queue item
"AIGC label dual-track deepening"; compliance anchors = the A-grade crawled
labeling chain in docs/global-benchmarks.md sec 1: labeling-measures art.4
explicit five-form positions + art.5 implicit file metadata [synthesis
attribute + provider code + content number, digital watermark encouraged]
+ art.10 malicious-removal ban + deep-synthesis provisions art.16/17/18 +
mandatory national standard GB 45438-2025, all effective/in force).

Pre-registered criteria AC-DT1..AC-DT6 (src/os/backlog.md R593 claim row,
registered BEFORE this code first ran; honesty law). Track map:

  explicit track  : ai_label text rendered as a visible bottom-right
                    badge; single source = src/sandbox/ugc/config.json
                    compliance.ai_label_text, read at run time, zero copy;
  implicit track  : 256-bit blind watermark (P-47-3c capability, pip
                    blind_watermark, MIT), bits = SHA-256 of
                    "provider:content_no:ai_label_text" so the hidden
                    payload is cryptographically bound to the visible
                    label and the art.5 metadata triple;
  metadata track  : PNG tEXt chunk "AIGC-Attr" carrying the receipt JSON
                    (art.5 triple), written as the final container-layer
                    seal AFTER the watermark embed (pixel-domain last
                    transform must precede container finalization).

STANDIN notes (v3.py precedent; production wiring = bootstrap):
  - badge rendering uses a local system CJK font; production = bundled
    server-side font asset;
  - content_no is a fixed demo stand-in; production = the UGC adoption
    receipt evt_id;
  - badge text height >= 24px is a sandbox-chosen parameter, NOT a
    GB 45438 ratio citation (full standard text = uncrawled M-item).

Usage: python test_dual_track.py
Exit : 0 all PASS, 1 any FAIL.
"""

import hashlib
import json
import os
import sys
import tempfile

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from PIL import PngImagePlugin
from blind_watermark import WaterMark

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(BASE, "..", "..", ".."))
UGC_CFG = os.path.join(ROOT, "src", "sandbox", "ugc", "config.json")

PROVIDER = "BigDomain"
CONTENT_NO = "UGC-DEMO-20260929-0001"  # stand-in; production = evt_id
WRONG_NO = "UGC-DEMO-20260929-9999"    # forgery-case stand-in
JPEG_Q = 90                           # compression case, W1b precedent
MIN_TEXT_H = 24                       # sandbox param, not a GB citation
BADGE_MIN_DIFF = 10.0                 # mean-abs-diff badge region vs clean
TAMPER_BER_MAX = 0.05                 # pre-registered tamper threshold
FORGERY_BER_MIN = 0.40                # pre-registered forgery floor

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\Deng.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]

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


def binding_bits(provider, content_no, label_text):
    digest = hashlib.sha256(
        ("%s:%s:%s" % (provider, content_no, label_text)).encode("utf-8")
    ).digest()
    return np.unpackbits(np.frombuffer(digest, dtype=np.uint8)).astype(int)


def extract_bits(path, nbits):
    bwm = WaterMark(password_wm=1, password_img=1, mode="common")
    got = bwm.extract(filename=path, wm_shape=[nbits], mode="bit")
    return np.asarray(got).astype(int).clip(0, 1)


def make_img():
    rng = np.random.default_rng(20260929)
    h, w = 480, 640
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, :, 0] = np.tile(np.linspace(0, 255, w, dtype=np.uint8), (h, 1))
    img[:, :, 1] = rng.integers(0, 256, (h, w), dtype=np.uint8)
    img[:, :, 2] = 128
    return img


def pick_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, MIN_TEXT_H + 8), path
            except Exception:
                continue
    return None, None


def render_badge(img_bgr, label_text):
    """Render the explicit-track badge into the bottom-right corner.

    Returns (badged_bgr, box(x0,y0,x1,y1), text_h, font_path) or
    (None, None, 0, None) when no CJK font is available.
    """
    font, font_path = pick_font()
    if font is None:
        return None, None, 0, None
    pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    w, h = pil.size
    probe = ImageDraw.Draw(pil)
    tb = probe.textbbox((0, 0), label_text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    pad = 10
    bw, bh = tw + 2 * pad, th + 2 * pad
    x0, y0 = w - bw - 8, h - bh - 8
    box = (int(x0), int(y0), int(x0 + bw), int(y0 + bh))
    overlay = Image.new("RGBA", pil.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle(box, fill=(0, 0, 0, 170))
    d.text((x0 + pad - tb[0], y0 + pad - tb[1]), label_text,
           font=font, fill=(255, 255, 255, 255))
    out = Image.alpha_composite(pil, overlay).convert("RGB")
    badged = cv2.cvtColor(np.asarray(out), cv2.COLOR_RGB2BGR)
    return badged, box, int(th), font_path


def main():
    label_text = load_label_text()
    tmp = tempfile.mkdtemp(prefix="bd_dt_")
    try:
        # ---- stage 0: clean generated image (deterministic) ----
        clean = make_img()
        h, w = clean.shape[:2]

        # ---- stage 1: explicit track = visible ai_label badge ----
        badged, box, text_h, font_path = render_badge(clean, label_text)
        font_ok = badged is not None
        record("AC-DT2-pre", bool(font_ok and label_text),
               "explicit label from ugc config, len=%d font=%s"
               % (len(label_text), os.path.basename(font_path)
                  if font_path else "NONE"))

        if not font_ok:
            print("SUITE FAIL: no CJK font available, explicit track cannot render")
            return 1
        x0, y0, x1, y1 = box
        region_diff = float(np.mean(np.abs(
            badged[y0:y1, x0:x1].astype(int) - clean[y0:y1, x0:x1].astype(int))))
        in_br = (y0 >= h // 2) and (x0 >= w // 2)
        record("AC-DT2", in_br and region_diff > BADGE_MIN_DIFF
               and text_h >= MIN_TEXT_H,
               "badge box=%s bottom-right=%s region-mean-abs-diff=%.1f "
               "text-h=%dpx (param>=%d)" % (box, in_br, region_diff, text_h,
                                            MIN_TEXT_H))

        # ---- stage 2: implicit track = binding watermark (pixel-domain
        #      last transform, embedded BEFORE container finalization) ----
        bits = binding_bits(PROVIDER, CONTENT_NO, label_text)
        nbits = int(bits.size)
        bits_sha = hashlib.sha256(
            ("%s:%s:%s" % (PROVIDER, CONTENT_NO, label_text)).encode("utf-8")
        ).hexdigest()[:16]
        badged_path = os.path.join(tmp, "badged.png")
        cv2.imwrite(badged_path, badged)
        sealed_pixels = os.path.join(tmp, "sealed_pixels.png")
        bwm = WaterMark(password_wm=1, password_img=1, mode="common")
        bwm.read_img(badged_path)
        bwm.read_wm(bits, mode="bit")
        bwm.embed(sealed_pixels)

        # ---- stage 3: metadata track = PNG tEXt receipt (art.5 triple),
        #      container-layer final seal on the sealed file ----
        receipt = {
            "provider": PROVIDER,
            "content_no": CONTENT_NO,
            "label_text": label_text,
            "badge_box": list(box),
            "wm_bits_sha16": bits_sha,
            "tracks": "explicit+metadata+implicit",
        }
        receipt_json = json.dumps(receipt, ensure_ascii=True, sort_keys=True)
        meta = PngImagePlugin.PngInfo()
        meta.add_text("AIGC-Attr", receipt_json)
        final_path = os.path.join(tmp, "sealed_final.png")
        sealed_pil = Image.open(sealed_pixels).convert("RGB")
        sealed_pil.save(final_path, "PNG", pnginfo=meta)
        reloaded = Image.open(final_path)
        got_meta = str(getattr(reloaded, "text", {}).get("AIGC-Attr", ""))
        meta_exact = got_meta == receipt_json
        receipt_sha = hashlib.sha256(receipt_json.encode("utf-8")).hexdigest()[:16]
        record("AC-DT1", meta_exact and sealed_pil.size == (w, h),
               "seal order badge->watermark(pixel-last)->tEXt(container-last); "
               "AIGC-Attr roundtrip exact=%s receipt-sha16=%s "
               "triple=(provider,content_no,label_text)"
               % (meta_exact, receipt_sha))

        # ---- AC-DT3: clean extraction from the final sealed file ----
        got = extract_bits(final_path, nbits)
        b3 = ber(got, bits)
        record("AC-DT3", b3 == 0.0,
               "binding bits=SHA-256(provider:content_no:ai_label_text) "
               "sha16=%s nbits=%d clean-extract ber=%.4f (exact required)"
               % (bits_sha, nbits, b3))

        # ---- AC-DT4: strip-explicit tamper case (badge region restored to
        #      clean pixels = label removal, art.10/art.18 ban scenario) ----
        tampered = cv2.imread(final_path, cv2.IMREAD_COLOR)
        tampered[y0:y1, x0:x1] = clean[y0:y1, x0:x1]
        tampered_path = os.path.join(tmp, "label_stripped.png")
        cv2.imwrite(tampered_path, tampered)
        b4 = ber(extract_bits(tampered_path, nbits), bits)
        record("AC-DT4", b4 <= TAMPER_BER_MAX,
               "label-strip region-restore case: implicit extract ber=%.4f "
               "(pre-registered threshold <= %.2f = provenance survives)"
               % (b4, TAMPER_BER_MAX))

        # ---- AC-DT5: forgery cross-check (wrong content_no expectation
        #      must NOT match the sealed content) ----
        wrong_bits = binding_bits(PROVIDER, WRONG_NO, label_text)
        b5 = ber(got, wrong_bits)
        record("AC-DT5", b5 >= FORGERY_BER_MIN,
               "forgery case: wrong-content_no expectation ber=%.4f "
               "(floor >= %.2f = correctly non-matching)" % (b5, FORGERY_BER_MIN))

        # ---- AC-DT6: compression pipeline case + suite discipline ----
        final_pixels = cv2.imread(final_path, cv2.IMREAD_COLOR)
        jpg_path = os.path.join(tmp, "sealed_q%d.jpg" % JPEG_Q)
        cv2.imwrite(jpg_path, final_pixels, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_Q])
        b6 = ber(extract_bits(jpg_path, nbits), bits)
        with open(os.path.abspath(__file__), "rb") as f:
            src_bytes = f.read()
        ascii_ok = all(b < 128 for b in src_bytes)
        record("AC-DT6", b6 == 0.0 and ascii_ok,
               "JPEG q%d re-save extract ber=%.4f (W1b-precedent exact "
               "required); suite source pure-ascii=%s"
               % (JPEG_Q, b6, ascii_ok))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s: %d/%d PASS%s" % (
        "FAIL" if fails else "PASS", len(RESULTS) - len(fails), len(RESULTS),
        (" failed=" + ",".join(fails)) if fails else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
