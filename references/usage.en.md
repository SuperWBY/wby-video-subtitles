# Usage and configuration

## Environment

Use Python 3.12 with Pillow, fonttools, imageio-ffmpeg, and jieba. Install `mlx-whisper` for transcription on Apple Silicon, or use a separately tested `faster-whisper` setup. FFmpeg must provide the `ass`/libass filter and `libx264` encoder. The `doctor` command reports available packages, filters, default font, and presets.

```sh
python3 -m venv ~/.local/share/wby-video-subtitles/venv
~/.local/share/wby-video-subtitles/venv/bin/python -m pip install pillow fonttools imageio-ffmpeg jieba
~/.local/share/wby-video-subtitles/venv/bin/python -m pip install mlx-whisper
```

The Skill includes `Noto Sans CJK SC Regular` under SIL OFL 1.1. Font priority is `--font`, machine configuration, then the bundled font. Use a suitable replacement font when the source or translation contains a script that the bundled font does not cover.

An optional local file at `~/.local/share/wby-video-subtitles/machine.json` may contain `font_path` and `model`. Keep machine-specific model and custom-font paths out of the repository.

Use the following workflow, where `PY`, `SCRIPT`, `VIDEO`, and `JOB` are explicit local paths:

```text
PY SCRIPT doctor
PY SCRIPT init --video VIDEO --job JOB --language auto --preset standard
PY SCRIPT transcribe --job JOB
# Or import existing captions into a fresh job:
PY SCRIPT import-srt --job JOB --srt SRT
PY SCRIPT apply-terms --job JOB --json REVIEWED_CORRECTIONS
PY SCRIPT import-translations --job JOB --json REVIEWED_TRANSLATIONS
PY SCRIPT prepare --job JOB
PY SCRIPT preview --job JOB --start 0 --seconds 8
PY SCRIPT render --job JOB
```

`--language auto` lets the transcription backend detect the source language. Use an explicit backend-supported code such as `en`, `fr`, `zh`, `ja`, or `pt` when needed. Backend and model support still determine which spoken languages can be transcribed.

Every `prepare` creates a revision under `job/revisions/` and updates `latest.json`. Existing revisions are not overwritten. A configuration change does not affect an existing ASS file until `prepare` is run again.

## Size presets

Font size is based on frame height so landscape, portrait, HD, and 4K videos do not share one fixed pixel size.

| Preset | Primary | Minimum | Translation | Use |
|---|---:|---:|---:|---|
| `compact` | 4.0% | 3.2% | 76% of primary | Dense screen recordings |
| `standard` | 4.5% | 3.5% | 78% | Default talking-head and demo videos |
| `emphasis` | 5.2% | 4.0% | 80% | Sparse, high-impact captions |

The `standard` preset starts near 49 px on a 1080-high frame and 97 px on a 2160-high frame. A long cue may shrink toward the preset minimum. Content that still cannot fit in two lines is rejected and must be split and retimed.

## Configuration fields

| Field | Meaning |
|---|---|
| `font_path` | Font file used for measurement and rendering |
| `style_preset` | Preset recorded when the job was created; rendering uses the ratio fields |
| `font_size_ratio` / `min_font_size_ratio` | Primary and minimum size as a fraction of frame height |
| `text_color` | Primary color as `#RRGGBB` |
| `background_color` / `background_opacity` | Box color and opacity from 0 to 1; 0 disables the box |
| `outline_color` / `outline_px` | Outline color and width; box mode uses the width as padding |
| `margin_x_ratio` / `margin_y_ratio` | Horizontal and vertical safe-area margins |
| `position` | `bottom` or `top` |
| `max_lines` | Fixed at 2 |
| `max_cps` / `min_duration` / `max_duration` | Review warnings; tune for the content language and audience |
| `terms` | Names and terminology used as transcription context and missing-term hints |
| `translation_font_scale` / `translation_color` | Relative size and color of the translated line |
| `backend` / `model` / `language` | Transcription setup and optional source-language code; null means auto-detect |

The background is a rectangular libass subtitle box and does not support rounded speech bubbles.

## Editing captions

`captions.json` is the editable source of truth. Each item contains `start`, `end`, and `text`, plus optional word spans. Back up manual changes and record them in `edits.json`. Do not invent word timestamps after editing text: the script uses word spans only when their text still matches the reviewed caption.

The source-video content hash is checked before every operation. Create a new job when the source video changes. Extracted transcription audio exists only in a temporary directory and is not shared across videos.

## Reviewed terminology correction

`terms` provides transcription context but never forces replacements. After listening to the source, create a reviewed correction file. Every replacement target must already exist in `config.json` under `terms`.

```json
{
  "version": 1,
  "corrections": [{
    "source_cue": 3,
    "from": "Code X",
    "to": "Codex",
    "evidence": "Listened to 00:03.60-00:09.32; the speaker says Codex"
  }]
}
```

`apply-terms` changes one exact occurrence in the selected cue, saves the previous captions under `backups/`, and records the evidence in `edits.json`.

## Bilingual subtitles

Correct and review the source captions first. Then provide exactly one reviewed target-language entry for every source cue:

```json
{
  "version": 1,
  "target_language": "fr",
  "cues": [{
    "source_cue": 1,
    "source_text": "Watch the subtitle grow.",
    "text": "Regardez le sous-titre s'agrandir."
  }]
}
```

The import stores the source-caption hash. If the source changes later, `prepare` refuses the stale translation. Bilingual mode reserves one line for the source and one for the translation. If either line does not fit at the minimum size, split and retime both instead of adding a third line or clipping text.

## Timed size and color effects

Create `style-effects.json` in the job root. Times are absolute seconds in the source video:

```json
{
  "version": 1,
  "effects": [
    {"start": 0.8, "end": 1.8, "font_scale": 1.6, "transition_ms": 120},
    {"start": 2.0, "end": 3.2, "font_scale": 1.0, "text_color": "#FFD400", "transition_ms": 100}
  ]
}
```

`font_scale` accepts 0.5 to 3 and `transition_ms` accepts 0 to 1000. Effects apply to the full subtitle visible during that interval. Review timestamps against the recording and render a preview. This is post-production timing, not live voice control.

## Failure handling

Errors return a non-zero exit status and JSON diagnostics. Use existing SRT when a video has no audio. Select another font when glyph validation fails. Adjust text, width, or size when an unbreakable token cannot fit. Never delete text, truncate output, or mark a partial render as complete.
