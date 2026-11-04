# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python", "numpy", "img2pdf"]
# ///
"""Extract slides from a video: grab a frame every N seconds, drop near-duplicates.

A grabbed frame is kept only if it differs from the last kept frame, i.e. the
percentage of "equal" pixels is below --threshold. Pixels are compared on a
downscaled grayscale copy, and count as equal when their difference is small,
so video compression noise does not create false new slides.

Usage:
  uv run extract_slides.py VIDEO [--interval 10] [--threshold 95] [--quality 80] [--png]

Output, next to the video:
  <video>_slides.pdf   all slides in order, JPEG-compressed at --quality
  <video>_slides/      lossless PNGs, slide_001_00-01-20.png, ... (only with --png)
"""

import argparse
from pathlib import Path

import cv2
import img2pdf
import numpy as np

COMPARE_WIDTH = 320  # downscale width used for comparison
PIXEL_TOLERANCE = 12  # grayscale diff (0-255) still counted as "equal"


def small_gray(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    small = cv2.resize(frame, (COMPARE_WIDTH, int(h * COMPARE_WIDTH / w)))
    return cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)


def percent_equal(a: np.ndarray, b: np.ndarray) -> float:
    diff = cv2.absdiff(a, b)
    return 100.0 * np.count_nonzero(diff <= PIXEL_TOLERANCE) / diff.size


def timestamp(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 3600:02d}-{s % 3600 // 60:02d}-{s % 60:02d}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("video", type=Path)
    parser.add_argument(
        "-i", "--interval", type=float, default=10.0,
        help="seconds between frame grabs (default: %(default)s)",
    )
    parser.add_argument(
        "-t", "--threshold", type=float, default=95.0,
        help="frames with at least this %% of equal pixels are duplicates "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "-q", "--quality", type=int, default=80,
        help="JPEG quality of PDF pages, 1-100; 0 = lossless PNG pages "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "--png", action="store_true",
        help="also save each slide as a lossless PNG in <video>_slides/",
    )
    args = parser.parse_args()
    if not 0 <= args.quality <= 100:
        parser.error("--quality must be between 0 and 100")

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit(f"Cannot open {args.video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps

    png_dir = args.video.with_name(f"{args.video.stem}_slides")
    if args.png:
        png_dir.mkdir(exist_ok=True)

    page_format = ".png" if args.quality == 0 else ".jpg"
    page_params = [] if args.quality == 0 else [cv2.IMWRITE_JPEG_QUALITY, args.quality]

    last = None
    pages: list[bytes] = []
    t = 0.0
    while t < duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        gray = small_gray(frame)
        if last is None or percent_equal(gray, last) < args.threshold:
            pages.append(cv2.imencode(page_format, frame, page_params)[1].tobytes())
            name = f"slide_{len(pages):03d}_{timestamp(t)}"
            if args.png:
                cv2.imwrite(str(png_dir / f"{name}.png"), frame)
            print(f"[{timestamp(t)}] kept  {name}")
            last = gray
        t += args.interval
    cap.release()

    if not pages:
        raise SystemExit("No frames could be read from the video.")
    pdf_path = png_dir.with_suffix(".pdf")
    pdf_path.write_bytes(img2pdf.convert(pages))
    print(f"{len(pages)} slides saved to {pdf_path}")
    if args.png:
        print(f"PNGs saved to {png_dir}")


if __name__ == "__main__":
    main()
