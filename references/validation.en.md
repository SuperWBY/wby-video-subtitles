# Validation record

## 1.3.2 (2026-09-12)

- Reworked all README pages into one primary visual, one collapsible animated proof, and one three-row capability table so the hero and animation do not compete in the first viewport.
- Repositioned the product as a portable Skill callable by different Agents; Codex remains only an installation example.
- Local relative-link checks pass for all three README pages.

## 1.3.1 (2026-09-12)

- Removed the release-exclusions section from all three README languages and added reader-facing capability tables.
- Created `assets/demo.gif`, a 768x432, 72-frame looping demonstration. Key frames were visually checked for auto detect, English/French bilingual layout, and Spanish timed emphasis.
- Local relative-link checks pass for the three README files, the GIF, and the documentation references.

## 1.3.0 (2026-09-12)

Validated on macOS Apple Silicon with Python 3.12 and FFmpeg:

- Source language defaults to automatic detection and accepts explicit language codes.
- The terminology prompt is language-neutral and contains only reviewed names supplied by the job.
- Regression checks cover source isolation, text preservation, the hard two-line limit, canvas-relative font sizing, timed scale/color tags, bilingual import, terminology-edit backups, bundled font presence, and style presets.
- Skill structure validation passes.
- The global README hero was visually inspected with English source text, an English/French bilingual example, a Spanish emphasis example, and no Chinese-first framing.

The transcription languages actually available still depend on the chosen backend and model. Arabic, Devanagari, and other writing systems not covered by the bundled font require a suitable font and separate rendering verification.

## 1.2.0 and 1.1.0

Earlier validation established the bundled font and presets, plus an actual 3840x2160 eight-second Chinese/French render with audio, two-line layout, 1.6x timed enlargement, and yellow timed text. That sample verified the rendering features, not universal language coverage or live voice control.
