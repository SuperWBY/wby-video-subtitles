# WBY Video Subtitles

[English](README.md) · **简体中文** · [日本語](README.ja.md)

![WBY Video Subtitles：自适应字号、双语字幕与定时变色](assets/hero.png)

![动态演示：语音变为可编辑字幕，再生成自适应、多语言和定时强调效果](assets/demo.gif)

`WBY Video Subtitles` 是一个不限定源语言的本地 Codex Skill，可以把视频口播或已有字幕转换为可编辑字幕，并完成 ASS/SRT 生成、排版检查、预览和字幕烧录。

它适合重复制作口播和录屏视频：每个源视频使用独立任务目录，拥有自己的样式、术语表和修订记录。

## 从口播到带样式字幕

| 能力 | 它解决什么问题 |
|---|---|
| 自动识别或指定源语言 | 从视频实际口播的语言开始，而不是被固定语言预设限制。 |
| 保持字幕可编辑 | 复核转写、带依据校正术语，并输出可编辑 SRT 和 ASS。 |
| 让双语保持可读 | 将已复核的原文和译文放入两行实测排版，不会静默裁字。 |
| 让重点词被看见 | 按已复核的时间点放大或变色，让关键表达更突出。 |
| 适应真实画布 | 根据视频高度计算字号，只在设定安全下限内缩小。 |

## 功能

- 默认自动识别口播语言，也可以明确指定转写后端支持的源语言代码。
- 将原始转写与人工复核后的 `captions.json` 分开保存。
- 用 `terms` 提示 `Codex`、`Figma`、产品名等专有名词；最终结果仍需复听确认。
- 为每个任务设置字体、字号、文字颜色、描边、背景颜色与透明度、边距和上下位置。
- 根据已复核的时间轴，让字幕在指定口播时刻放大、缩小或变色。
- 在字体支持的任意源语言和目标语言之间导入人工复核译文，以原文一行、译文一行的方式渲染。
- 应用人工确认的术语修正，并自动备份旧稿、记录修改依据。
- 使用真实字体宽度计算排版，最多显示两行；无法安全容纳时直接停止，不会静默删字。
- 输出带版本的 SRT、ASS、预览视频、最终 MP4 和检查报告。

## 内置字体与字号预设

仓库内置以 SIL Open Font License 1.1 发布的 `Noto Sans CJK SC Regular`，可覆盖常见拉丁文字和 CJK 场景。字体选择顺序为：命令行 `--font`、可选的本机配置、内置字体。阿拉伯文、天城文或其他缺少字形的文字需要换用适合的字体；预检会拒绝缺字，而不是输出方框。

| 预设 | 主字号 | 最小字号 | 译文大小 | 建议场景 |
|---|---:|---:|---:|---|
| `compact` | 画面高度的 4.0% | 3.2% | 主字幕的 76% | 信息密集的录屏 |
| `standard` | 4.5% | 3.5% | 78% | 默认口播与演示视频 |
| `emphasis` | 5.2% | 4.0% | 80% | 字少、强调感强的字幕 |

`standard` 在 1080 高画面中约为 49 px，在 2160 高画面中约为 97 px。单条字幕过长时，排版器会在预设下限内缩小；仍无法放进两行时会要求拆句，不会裁掉文字。

## 环境要求

- 推荐 Python 3.12。
- FFmpeg，需要 `ass`/libass 滤镜和 `libx264` 编码器。
- 内置字体，或你有权使用的其他 `.ttf`/`.otf` 字体。
- `requirements.txt` 中的 Python 依赖。
- 转写：Apple Silicon 使用 `mlx-whisper`；其他平台需自行验证合适的 `faster-whisper` 环境。

## 安装为 Codex Skill

将仓库克隆到 Codex Skills 目录：

```sh
git clone https://github.com/SuperWBY/wby-video-subtitles.git ~/.codex/skills/wby-video-subtitles
```

在其他 Agent 中使用时，先确认该客户端文档规定的 Skill 父目录，再运行安装器：

```sh
python3 scripts/install.py --target /absolute/path/to/that-agent/skills
```

安装器会复制完整的自包含目录，并拒绝覆盖已有副本。安装成功不等于目标 Agent 已经发现并执行 Skill；请按照 [兼容性说明](references/compatibility.md) 完成验证。

建立本地虚拟环境并安装依赖：

```sh
python3 -m venv ~/.local/share/wby-video-subtitles/venv
~/.local/share/wby-video-subtitles/venv/bin/python -m pip install -r ~/.codex/skills/wby-video-subtitles/requirements.txt
~/.local/share/wby-video-subtitles/venv/bin/python -m pip install mlx-whisper
```

`mlx-whisper` 是已验证的 Apple Silicon 路径。其他平台应选择并单独验证适用的转写后端。

可选：在 `~/.local/share/wby-video-subtitles/machine.json` 保存仅限本机的配置：

```json
{
  "font_path": "/absolute/path/to/your/subtitle-font.otf",
  "model": "mlx-community/whisper-large-v3-turbo"
}
```

## 快速开始

先设置本机路径：

```sh
PY=~/.local/share/wby-video-subtitles/venv/bin/python
SKILL=~/.codex/skills/wby-video-subtitles/scripts/subtitles.py
```

检查环境并创建任务：

```sh
$PY $SKILL doctor
$PY $SKILL init --video /absolute/path/video.mp4 --job /absolute/path/video-job --language auto --preset standard
```

`--language auto` 会让转写后端识别源语言，也可以指定后端支持的 `en`、`fr`、`zh`、`ja`、`pt` 等代码。可以改用 `--preset compact` 或 `--preset emphasis`。若要覆盖内置字体，添加 `--font /absolute/path/font.otf`。

转写、复核、排版、预览和渲染：

```sh
$PY $SKILL transcribe --job /absolute/path/video-job
# 对照源音频复核 captions.json 后再继续。
$PY $SKILL apply-terms --job /absolute/path/video-job --json /absolute/path/reviewed-corrections.json
$PY $SKILL import-translations --job /absolute/path/video-job --json /absolute/path/reviewed-translations.json
$PY $SKILL prepare --job /absolute/path/video-job
$PY $SKILL preview --job /absolute/path/video-job --start 0 --seconds 8
$PY $SKILL render --job /absolute/path/video-job
```

如果已经有字幕，请创建新的任务目录，并用下面的命令替代 `transcribe`：

```sh
$PY $SKILL import-srt --job /absolute/path/video-job --srt /absolute/path/captions.srt
```

## 输出与检查

每次 `prepare` 都会在 `job/revisions/` 下创建新版本并更新 `latest.json`。旧版本和已经复核的字幕不会被覆盖。

发布视频前，请检查开头、最长字幕、术语密集段、双语段和带样式效果的片段。渲染成功只能证明文件可以解码且存在音轨，不能替代语义、翻译和同步检查。

## 验证

修改字幕流水线后运行：

```sh
PY=~/.local/share/wby-video-subtitles/venv/bin/python
$PY ~/.codex/skills/wby-video-subtitles/scripts/self_test.py
```

更完整的格式、术语修正、双语字幕和时间轴效果说明见 [运行与配置](references/usage.md)。跨 Agent 能力边界见 [兼容性说明](references/compatibility.md)，已完成的实测范围见 [验证记录](references/validation.md)。

## 许可证

代码采用 MIT License，见 [LICENSE](LICENSE)。内置 Noto 字体单独采用 SIL Open Font License 1.1，见 [字体许可证](assets/fonts/LICENSE.txt)。
