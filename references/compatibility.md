# 跨 Agent 与平台兼容性

核心能力位于 `scripts/subtitles.py`，不依赖某个 Agent 的专用 API。任何能够读写本地文件并执行 Python/FFmpeg 命令的 Agent，都可以按 README 中的命令调用它。

自动发现方式由客户端决定：Codex 使用 `~/.codex/skills/wby-video-subtitles/`；其他 Agent 应按其官方 Skill 目录规则安装同一仓库，或直接调用脚本。不要因为 CLI 可运行，就宣称某个客户端已经完成了 Skill 自动发现、权限、预览显示和成片验收。

仓库中的 `scripts/install.py --target TARGET_SKILLS_DIRECTORY` 可把同一 Skill 复制到用户明确提供的其他 Agent Skill 父目录。安装器拒绝覆盖已有目录；更新已有副本时应使用该副本原来的 Git remote，避免覆盖本地修改。

当前实机验证范围是 macOS Apple Silicon、本地 Codex、Python 3.12 和 MLX 转写路径。Claude Code、WorkBuddy、豆包普通聊天、Windows、Linux 与 faster-whisper 均需分别执行：结构发现、doctor、导入或转写、prepare、preview、render 和人工画面/同步检查。只有对应检查完成后，才能把该客户端或平台列为已验证。
