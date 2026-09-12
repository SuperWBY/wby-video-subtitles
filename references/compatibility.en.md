# Cross-Agent and platform compatibility

The core pipeline lives in `scripts/subtitles.py` and does not require an Agent-specific API. An Agent that can read and write local files and execute Python and FFmpeg can call the documented commands.

Skill discovery remains client-specific. Codex uses `~/.codex/skills/wby-video-subtitles/`. For another Agent, follow that client's documented Skill-directory convention or invoke the script directly. A successful CLI run does not prove that a client supports automatic discovery, permissions, media preview, or final-video review.

`scripts/install.py --target TARGET_SKILLS_DIRECTORY` copies the same self-contained Skill into an explicitly chosen parent directory and refuses to overwrite an existing copy. Update an existing copy from its original Git remote so local changes are not silently replaced.

The verified environment is macOS on Apple Silicon, local Codex, Python 3.12, and the MLX transcription path. Claude Code, WorkBuddy, Doubao, Windows, Linux, and `faster-whisper` require their own discovery, `doctor`, import or transcription, `prepare`, preview, render, and human visual/sync checks before being described as verified.

Language coverage has two separate constraints:

- The selected Whisper backend and model must support the spoken source language.
- The selected font must contain every source and translation glyph.

The bundled font is a practical default for common Latin and CJK scripts. It is not a claim of complete Unicode coverage. Use `--font` or `font_path` for other writing systems.
