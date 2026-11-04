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
  uv run extract_slides.py VIDEO [--interval 10] [--threshold 95] [--output-dir DIR]

Output: DIR/slide_001_00-01-20.png, ... (default DIR: <video name>_slides next
to the video), plus all slides joined into DIR.pdf (e.g. <video name>_slides.pdf).
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
    parser.add_argument("-o", "--output-dir", type=Path, default=None)
    args = parser.parse_args()

    out_dir = args.output_dir or args.video.with_name(f"{args.video.stem}_slides")
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit(f"Cannot open {args.video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps

    last = None
    kept = 0
    slide_paths: list[Path] = []
    t = 0.0
    while t < duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        gray = small_gray(frame)
        if last is None or percent_equal(gray, last) < args.threshold:
            kept += 1
            path = out_dir / f"slide_{kept:03d}_{timestamp(t)}.png"
            cv2.imwrite(str(path), frame)
            slide_paths.append(path)
            print(f"[{timestamp(t)}] kept  -> {path.name}")
            last = gray
        t += args.interval

    cap.release()
    print(f"{kept} slides saved to {out_dir}")

    if slide_paths:
        pdf_path = out_dir.with_suffix(".pdf")
        pdf_path.write_bytes(img2pdf.convert([str(p) for p in slide_paths]))
        print(f"PDF saved to {pdf_path}")


if __name__ == "__main__":
    main()
