---
name: wby-video-subtitles
description: Generate, review, lay out, preview, and render Chinese video subtitles with WBY settings for terminology, colors, backgrounds, and a hard two-line limit. Use for local video subtitle work; excludes motion graphics and character animation.
metadata:
  version: 1.0.0
---

# WBY Video Subtitles

Use this Skill for a local video that needs editable Chinese subtitles or subtitle styling. Run `doctor` before the first job. Treat `captions.json` as the reviewed source of truth and preserve the original transcription.

## Workflow

1. Create one empty job directory per source video with `init`. The job verifies the source hash and refuses stale reuse.
2. Set the font, colors, background, position, and this video's `terms` in `config.json`. `terms` are transcription context and review hints, never unreviewed global replacements.
3. Run `transcribe`, or use `import-srt` when editable captions already exist. Review terminology and uncertain words against the audio before `prepare`.
4. Run `prepare`, then preview ordinary, longest, and terminology-heavy portions. The renderer preserves text and limits the rendered subtitle to two lines.
5. Render only after the preview is accepted. Full-file decoding checks container health, duration, and audio; it does not prove semantic accuracy or sync.

Read [usage](references/usage.md) for setup, commands, and configuration fields.

## Boundaries

- Subtitle styling is configured per job; it is not controlled live by spoken commands.
- The included pipeline supports Chinese transcription and editable SRT/ASS output. Translation and multilingual dual subtitles require a separately chosen translation step and human review; they are not implemented by this release.
- Validation has been performed on macOS Apple Silicon. Other clients, operating systems, and transcription backends require separate verification.
- Motion graphics, tracked objects, and character animation are deliberately outside this Skill and are not included in this repository.
