# WBY Video Subtitles

**English** · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

![WBY Video Subtitles: adaptive size, bilingual subtitles, and timed color](assets/hero.png)

`WBY Video Subtitles` is a language-neutral local Codex Skill for turning speech or existing captions into editable subtitles, then preparing ASS/SRT, checking layout, previewing, and rendering a subtitle-burned video.

It is designed for repeatable talking-head and screen-recording videos: each source video has an independent job, its own style, and its own terminology list.

## What it does

- Automatically detects the spoken language by default, or accepts an explicit backend-supported source language code.
- Keeps the raw transcription separate from reviewed `captions.json`.
- Uses `terms` as context for names such as `Codex`, `Figma`, and product terminology; review remains required.
- Lets each job set font, size, text color, outline, background color/transparency, margins, and top/bottom position.
- Applies reviewed timeline effects that enlarge, shrink, or recolor the displayed subtitle during selected spoken moments.
- Imports a reviewed translation between any source and target languages supported by the selected font, then renders source and translation as exactly two lines.
- Applies reviewed terminology corrections with a backup and edit log.
- Measures the selected font and produces subtitle cues of at most two rendered lines. It refuses layouts that cannot fit without silently dropping text.
- Produces versioned SRT, ASS, preview media, a rendered MP4, and a report of warnings and unchecked items.

## Built-in font and size presets

The repository includes `Noto Sans CJK SC Regular` under the SIL Open Font License 1.1. It provides a practical default for common Latin and CJK scripts without a machine-specific path. Font selection follows this order: `--font`, the optional machine configuration, then the bundled font. For Arabic, Devanagari, or another script with missing glyphs, choose an appropriate font; preflight validation refuses unsupported characters instead of rendering boxes.

| Preset | Primary size | Minimum size | Translation line | Recommended use |
|---|---:|---:|---:|---|
| `compact` | 4.0% of frame height | 3.2% | 76% of primary | Dense screen recordings |
| `standard` | 4.5% | 3.5% | 78% | Default talking-head and demo videos |
| `emphasis` | 5.2% | 4.0% | 80% | Sparse, high-impact captions |

`standard` starts near 49 px on a 1080-high frame and 97 px on a 2160-high frame. The renderer can shrink individual cues toward the preset minimum when needed; it still refuses content that cannot fit in two lines without dropping text.

## Not included in this release

- Motion graphics, tracked objects, and character animation. Those files are intentionally isolated from this repository.
- Live speech control. Timed style changes are prepared from the recorded video's timestamps.
- Automatic translation API calls. The Agent drafts translations and the user reviews them before import.
- A guarantee that the same setup works in every Agent, client, operating system, or third-party player.

## Requirements

- Python 3.12 recommended.
- FFmpeg with `ass`/libass support and `libx264` for rendering.
- The bundled font, or another `.ttf`/`.otf` font you are permitted to use.
- Python packages from `requirements.txt`.
- For transcription: `mlx-whisper` on Apple Silicon, or an independently tested `faster-whisper` setup.

## Install as a Codex Skill

Clone the repository into your Codex skills directory:

```sh
git clone https://github.com/SuperWBY/wby-video-subtitles.git ~/.codex/skills/wby-video-subtitles
```

For another Agent, find that client's documented Skill parent directory, then run the repository's installer with that explicit path:

```sh
python3 scripts/install.py --target /absolute/path/to/that-agent/skills
```

This installs the same self-contained folder and refuses to overwrite an existing copy. Installation alone does not prove that the target Agent discovered or executed the Skill; run the validation flow described in [references/compatibility.md](references/compatibility.md).

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
  "font_path": "/absolute/path/to/your/subtitle-font.otf",
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
$PY $SKILL init --video /absolute/path/video.mp4 --job /absolute/path/video-job --language auto --preset standard
```

`--language auto` lets the transcription backend detect the source language. Use a backend-supported code such as `en`, `fr`, `zh`, `ja`, or `pt` to specify it. Use `--preset compact` or `--preset emphasis` for another built-in size profile. Add `--font /absolute/path/font.otf` to override the bundled font.

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
$PY $SKILL apply-terms --job /absolute/path/video-job --json /absolute/path/reviewed-corrections.json
$PY $SKILL import-translations --job /absolute/path/video-job --json /absolute/path/reviewed-translations.json
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

Detailed schemas for terminology corrections, bilingual subtitles, and timed style effects are in the [English usage guide](references/usage.en.md). Cross-Agent claims and installation boundaries are explained in [compatibility](references/compatibility.en.md). Recorded test evidence is in [validation](references/validation.en.md).

## License

The code is MIT licensed; see [LICENSE](LICENSE). The bundled Noto font is licensed separately under the SIL Open Font License 1.1; see [assets/fonts/LICENSE.txt](assets/fonts/LICENSE.txt).
