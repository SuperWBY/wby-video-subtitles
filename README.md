# WBY Video Subtitles

`WBY Video Subtitles` is a local Codex Skill for turning a video into editable Chinese subtitles, then preparing ASS/SRT, checking layout, previewing, and rendering a subtitle-burned video.

It is designed for repeatable talking-head and screen-recording videos: each source video has an independent job, its own style, and its own terminology list.

## What it does

- Transcribes Chinese speech with word timestamps when the selected backend provides them.
- Keeps the raw transcription separate from reviewed `captions.json`.
- Uses `terms` as context for names such as `Codex`, `Figma`, and product terminology; review remains required.
- Lets each job set font, size, text color, outline, background color/transparency, margins, and top/bottom position.
- Measures the selected font and produces subtitle cues of at most two rendered lines. It refuses layouts that cannot fit without silently dropping text.
- Produces versioned SRT, ASS, preview media, a rendered MP4, and a report of warnings and unchecked items.

## Not included in this release

- Motion graphics, tracked objects, and character animation. Those files are intentionally isolated from this repository.
- Live speech-driven subtitle animation. Style changes are configured before rendering.
- Built-in translation or bilingual subtitles. Add a reviewed translation step before importing captions if needed.
- A guarantee that the same setup works in every Agent, client, operating system, or third-party player.

## Requirements

- Python 3.12 recommended.
- FFmpeg with `ass`/libass support and `libx264` for rendering.
- A Chinese-capable `.ttf` or `.otf` font you are permitted to use.
- Python packages from `requirements.txt`.
- For transcription: `mlx-whisper` on Apple Silicon, or an independently tested `faster-whisper` setup.

## Install as a Codex Skill

Clone the repository into your Codex skills directory:

```sh
git clone https://github.com/SuperWBY/wby-video-subtitles.git ~/.codex/skills/wby-video-subtitles
```

Create a local virtual environment and install the base dependencies:

```sh
python3 -m venv ~/.local/share/wby-video-subtitles/venv
~/.local/share/wby-video-subtitles/venv/bin/python -m pip install -r ~/.codex/skills/wby-video-subtitles/requirements.txt
~/.local/share/wby-video-subtitles/venv/bin/python -m pip install mlx-whisper
```

`mlx-whisper` is the verified Apple Silicon route. Do not install it blindly on another platform; use and verify an appropriate backend first.

Optionally save a local-only machine configuration at `~/.local/share/wby-video-subtitles/machine.json`:

```json
{
  "font_path": "/absolute/path/to/your/Chinese-font.otf",
  "model": "mlx-community/whisper-large-v3-turbo"
}
```

## Quick start

Set these two variables for your local paths:

```sh
PY=~/.local/share/wby-video-subtitles/venv/bin/python
SKILL=~/.codex/skills/wby-video-subtitles/scripts/subtitles.py
```

Check the environment and create a new job:

```sh
$PY $SKILL doctor
$PY $SKILL init --video /absolute/path/video.mp4 --job /absolute/path/video-job --font /absolute/path/font.otf
```

Edit `/absolute/path/video-job/config.json` before transcription. Example:

```json
{
  "text_color": "#FFFFFF",
  "background_color": "#0A1D3A",
  "background_opacity": 0.7,
  "position": "bottom",
  "terms": ["Codex", "Figma", "WBY"]
}
```

Then transcribe, review, prepare, preview, and render:

```sh
$PY $SKILL transcribe --job /absolute/path/video-job
# Review captions.json against the source audio before continuing.
$PY $SKILL prepare --job /absolute/path/video-job
$PY $SKILL preview --job /absolute/path/video-job --start 0 --seconds 8
$PY $SKILL render --job /absolute/path/video-job
```

If you already have captions, create a fresh job and replace `transcribe` with:

```sh
$PY $SKILL import-srt --job /absolute/path/video-job --srt /absolute/path/captions.srt
```

## Output and review

Each `prepare` creates a new revision beneath `job/revisions/` and updates `latest.json`. The revision contains `subtitles.srt`, `subtitles.ass`, layout data, and a report. Existing revisions and reviewed captions are never overwritten.

Before publishing a video, inspect previews for the first, longest, and terminology-heavy subtitles. A successful render proves the output decoded with an audio stream; it does not prove transcription meaning, perfect timing, or external SRT player layout.

## Validation

Run the regression checks after changing the pipeline:

```sh
PY=~/.local/share/wby-video-subtitles/venv/bin/python
$PY ~/.codex/skills/wby-video-subtitles/scripts/self_test.py
```

The checks cover source isolation, text preservation, two-line layout, and refusal of unsafe overwrite paths. They do not replace visual and audio review.

## License

MIT. See [LICENSE](LICENSE).
