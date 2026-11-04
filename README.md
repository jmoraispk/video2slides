# video2slides

Turn a recorded talk or presentation video into a deduplicated set of slide images plus a single PDF.

The approach is deliberately simple: grab one frame every N seconds, and keep it only if it differs enough from the last slide kept.

## Usage

Requires [uv](https://docs.astral.sh/uv/). The dependencies (`opencv-python`, `numpy`, `img2pdf`) are declared inline in the script ([PEP 723](https://peps.python.org/pep-0723/)), so `uv run` installs them on the fly. No virtualenv or `pip install` needed.

```
uv run extract_slides.py VIDEO [--interval 10] [--threshold 95] [--output-dir DIR]
```

| Option | Default | Meaning |
|---|---|---|
| `-i`, `--interval` | `10` | Seconds between frame grabs. Longer is faster, but slides shown for less than this can be missed. |
| `-t`, `--threshold` | `95` | A frame is a duplicate if at least this % of its pixels equal the last kept slide. Raise it (98–99) if incremental bullet reveals get dropped; lower it if near-duplicates get through. |
| `-o`, `--output-dir` | `<video name>_slides` | Folder for the PNGs. The PDF is written as `<output-dir>.pdf`. |

Output:

- `<video name>_slides/slide_001_00-00-00.png`, `slide_002_00-00-10.png`, ... (the time in each name is the timestamp in the video)
- `<video name>_slides.pdf`: all slides joined in order, at full quality

### How deduplication works

Each grabbed frame is downscaled to 320 px wide and converted to grayscale. A pixel counts as "equal" if its grayscale value is within 12 (out of 255) of the same pixel in the last kept slide, so video compression noise doesn't create false new slides. If the share of equal pixels is below `--threshold`, the frame is saved as a new slide.

## Example

Tested on [this talk by Victor Gu on X](https://x.com/victorgu0/status/2117693795076854052), downloaded with the [X Video Downloader](https://chromewebstore.google.com/detail/x-video-downloader/lpkhciegcecmbnojmdhfkcooedminenc) Chrome extension: an 8 min 53 s, 1920×1080, 30 fps MP4 of a talk with slides and a webcam overlay.

```
uv run extract_slides.py 2026-11-04-09-33-29.mp4
```

Result: 14 frames kept (an intro frame before the slides start, plus 13 distinct slides) and a 14-page PDF. The run took **about 7 seconds** on a Windows laptop once the dependencies were cached. The first run also downloads OpenCV and NumPy (~55 MB).
