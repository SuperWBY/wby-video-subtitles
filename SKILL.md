---
name: wby-video-subtitles
description: Generate, review, translate, style, preview, and render local video subtitles with WBY terminology correction, bilingual two-line layout, and timed size/color effects. Use for talking-head and screen-recording subtitle work; excludes character and object animation.
metadata:
  version: 1.3.2
---

# WBY Video Subtitles

![WBY Video Subtitles 功能预览](assets/hero.png)

Use this Skill for a local video in any source language supported by the selected transcription backend. Run `doctor` before the first job. Treat `captions.json` as the reviewed source of truth and preserve the original transcription.

## Installation and updates

When asked to install this Skill, complete setup using this procedure before starting a video job:

1. Identify the current client's configured Skill parent directory from its local configuration or documentation. Install the complete repository from `https://github.com/SuperWBY/wby-video-subtitles` into a `wby-video-subtitles` child directory. A Git clone preserves the source for future updates; `scripts/install.py --target PARENT` can copy a downloaded checkout. If the directory cannot be determined or local execution is unavailable, report the missing requirement.
2. For an existing installation, inspect its origin and working-tree changes before updating. Fast-forward a clean checkout from the matching upstream; preserve local edits and resolve conflicting updates explicitly. Do not overwrite a non-Git installation without comparing and preserving its local changes.
3. Create or reuse a dedicated Python virtual environment outside the Skill directory. Install the installed copy's `requirements.txt`. On Apple Silicon, install `mlx-whisper`; for other systems, use `faster-whisper` and a matching model. When creating jobs on that backend, set `config.json` to `backend: faster-whisper` and a compatible model such as `large-v3-turbo`. Keep machine-specific paths outside the distributed Skill.
4. Check FFmpeg for the `ass`/libass filter and `libx264` encoder. Use an available compatible build or install one with the platform package manager. The imageio-ffmpeg fallback must also pass these checks. Use the bundled font, `standard` size preset, and automatic source-language detection for new jobs; preserve existing user settings.
5. Run `scripts/subtitles.py doctor` with the dedicated environment's Python. Inspect package, filter, and font results, then run `scripts/self_test.py`. Verify client discovery separately from file installation. Report the installed path, dependency status, and any client-specific reload step. Model download and real-audio transcription verification are separate from installation; do not report them as tested unless executed.

## Workflow

1. Create one empty job directory per source video with `init`. The job verifies the source hash and refuses stale reuse. Source language defaults to automatic detection; use `--language en`, `fr`, `zh`, or another backend-supported code when explicit control is needed. It uses the bundled Noto Sans CJK SC font and the `standard` size preset unless a machine font, `--font`, or another preset is selected.
2. Set the font, colors, background, position, and this video's `terms` in `config.json`. `terms` guide transcription. Apply corrections only after listening, using `apply-terms` so the original caption file is backed up and the evidence is logged.
3. Run `transcribe`, or use `import-srt` when editable captions already exist. Review terminology and uncertain words against the audio.
4. For bilingual output, translate the reviewed source cues into the requested language, keep names and numbers stable, and import the complete reviewed mapping with `import-translations`. Each language occupies one rendered line; a cue that cannot fit must be split and retimed rather than cropped.
5. For size or color changes tied to speech, create `style-effects.json` with reviewed source timestamps. Use a few explicitly chosen moments; spoken words are context, not automatic commands.
6. Run `prepare`, then preview ordinary, longest, terminology-heavy, bilingual, and styled portions. The renderer preserves text and limits the rendered subtitle to two lines.
7. Render only after the preview is accepted. Full-file decoding checks container health, duration, and audio; it does not prove semantic accuracy, translation accuracy, or sync.

Read [usage](references/usage.en.md) for setup, commands, schemas, and configuration fields. Read [compatibility](references/compatibility.en.md) before describing use in another Agent or operating system. Use [validation](references/validation.en.md) to distinguish tested behavior from planned capability.

## Visible defaults

| Preset | Primary size | Minimum size | Translation line | Use |
|---|---:|---:|---:|---|
| `compact` | 4.0% of frame height | 3.2% | 76% of primary | Dense screen recordings |
| `standard` | 4.5% | 3.5% | 78% | Default talking-head and demo videos |
| `emphasis` | 5.2% | 4.0% | 80% | Sparse, high-impact captions |

The default font is the bundled `Noto Sans CJK SC Regular`, which covers common Latin and CJK use cases. A job can override it with `--font` or `config.json` for Arabic, Devanagari, or any script whose glyphs are missing. Size uses frame height, so `standard` starts near 49 px on a 1080-high frame and 97 px on a 2160-high frame, then shrinks only when needed to preserve the two-line limit.

## Boundaries

- Timed size and color changes are generated from reviewed timestamps during rendering; this is not live speech control.
- The pipeline imports and lays out any target language the configured font can render. The Agent produces the translation draft; the script does not call a translation service, and a person must review meaning.
- No single bundled font covers every writing system. The preflight glyph check reports unsupported characters and requires a suitable replacement font instead of producing missing-glyph boxes.
- Validation has been performed on macOS Apple Silicon. Other clients, operating systems, and transcription backends require separate verification.
- Motion graphics, tracked objects, and character animation are deliberately outside this Skill and are not included in this repository.
