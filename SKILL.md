---
name: wby-video-subtitles
description: Generate, review, translate, style, preview, and render local video subtitles with WBY terminology correction, bilingual two-line layout, and timed size/color effects. Use for talking-head and screen-recording subtitle work; excludes character and object animation.
metadata:
  version: 1.1.0
---

# WBY Video Subtitles

Use this Skill for a local video that needs editable Chinese subtitles or subtitle styling. Run `doctor` before the first job. Treat `captions.json` as the reviewed source of truth and preserve the original transcription.

## Workflow

1. Create one empty job directory per source video with `init`. The job verifies the source hash and refuses stale reuse.
2. Set the font, colors, background, position, and this video's `terms` in `config.json`. `terms` guide transcription. Apply corrections only after listening, using `apply-terms` so the original caption file is backed up and the evidence is logged.
3. Run `transcribe`, or use `import-srt` when editable captions already exist. Review terminology and uncertain words against the audio.
4. For bilingual output, translate the reviewed source cues into the requested language, keep names and numbers stable, and import the complete reviewed mapping with `import-translations`. Each language occupies one rendered line; a cue that cannot fit must be split and retimed rather than cropped.
5. For size or color changes tied to speech, create `style-effects.json` with reviewed source timestamps. Use a few explicitly chosen moments; spoken words are context, not automatic commands.
6. Run `prepare`, then preview ordinary, longest, terminology-heavy, bilingual, and styled portions. The renderer preserves text and limits the rendered subtitle to two lines.
7. Render only after the preview is accepted. Full-file decoding checks container health, duration, and audio; it does not prove semantic accuracy, translation accuracy, or sync.

Read [usage](references/usage.md) for setup, commands, schemas, and configuration fields. Read [compatibility](references/compatibility.md) before describing use in another Agent or operating system. Use [validation](references/validation.md) to distinguish tested behavior from planned capability.

## Boundaries

- Timed size and color changes are generated from reviewed timestamps during rendering; this is not live speech control.
- The pipeline imports and lays out any target language the configured font can render. The Agent produces the translation draft; the script does not call a translation service, and a person must review meaning.
- Validation has been performed on macOS Apple Silicon. Other clients, operating systems, and transcription backends require separate verification.
- Motion graphics, tracked objects, and character animation are deliberately outside this Skill and are not included in this repository.
