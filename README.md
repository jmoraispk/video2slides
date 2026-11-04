# video2slides

Extract the slides from a presentation video as one PDF.

Run without cloning:

```
uv run https://github.com/jmoraispk/video2slides/raw/main/extract_slides.py talk.mp4
```

[This 9-min talk](https://x.com/victorgu0/status/2117693795076854052) became 14 slides in about 7 s.

## Usage

```
uv run extract_slides.py VIDEO [-i 10] [-t 95] [-q 80] [--png]
```

| Option | Default | Meaning |
|---|---|---|
| `-i`, `--interval` | `10` | Seconds between frame grabs. Higher is faster but can miss short slides. |
| `-t`, `--threshold` | `95` | % of pixels that must match to count as a duplicate. |
| `-q`, `--quality` | `80` | JPEG quality of PDF pages (1–100). `0` = lossless. PNGs stay lossless. |
| `--png` | off | Also save each slide as a lossless PNG. |

Output, next to the video:

```
<video>_slides.pdf                      # all slides, in order (~2 MB vs 11 MB lossless)
<video>_slides/slide_001_00-00-00.png   # with --png; time in the video
<video>_slides/slide_002_00-00-10.png
...
```

<details>
<summary>Dependencies</summary>

Only [uv](https://docs.astral.sh/uv/) is needed. The script declares its dependencies inline (`opencv-python`, `numpy`, `img2pdf`, [PEP 723](https://peps.python.org/pep-0723/)), and `uv run` installs them on the first run.

</details>

<details>
<summary>How deduplication works</summary>

The script grabs a frame every `--interval` seconds. It compares each frame to the last kept slide on a 320 px grayscale copy. Pixels within 12/255 of each other count as equal, which ignores compression noise. A frame is kept when fewer than `--threshold` % of its pixels are equal.

Raise `-t` to 98–99 if slides that only add a bullet get dropped. Lower it if near-duplicates get through.

</details>

<details>
<summary>Example details</summary>

The video was downloaded with the [X Video Downloader](https://chromewebstore.google.com/detail/x-video-downloader/lpkhciegcecmbnojmdhfkcooedminenc) Chrome extension. It is an 8 min 53 s, 1080p, 30 fps MP4 with a webcam overlay.

```
uv run extract_slides.py 2026-11-04-09-33-29.mp4
```

The run kept 14 frames (an intro frame plus 13 slides) and wrote a 14-page PDF. It took ~7 s on a Windows laptop with dependencies already cached.

</details>
