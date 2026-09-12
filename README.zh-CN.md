# WBY Video Subtitles

[English](README.md) · **简体中文** · [日本語](README.ja.md)

![WBY Video Subtitles：自适应字号、双语字幕与定时变色](assets/hero.png)

`WBY Video Subtitles` 是一个不限定源语言、可被不同 Agent 调用的本地 Skill，可以把视频口播或已有字幕转换为可编辑字幕，并完成 ASS/SRT 生成、排版检查、预览和字幕烧录。

它适合重复制作口播和录屏视频：每个源视频使用独立任务目录，拥有自己的样式、术语表和修订记录。

## 一套流程，三个可见结果

| 能力 | 它解决什么问题 |
|---|---|
| 自适应字号 | 依据选定字体与实际画布测量，在两行安全区内完成排版。 |
| 多语言双语 | 自动识别或指定源语言，再将复核后的原文和译文置入两行实测排版。 |
| 定时强调 | 按复核后的时间点放大或变色，让关键表达更突出。 |

<details>
<summary>查看动态演示</summary>

<img src="assets/demo.gif" alt="动态演示：语音变为可编辑字幕，再生成自适应、多语言和定时强调效果" width="768">

</details>

流程会将原始转写与人工复核后的 `captions.json` 分开保存，带依据记录术语修正，并输出带版本的 SRT、ASS、预览、最终 MP4 与检查报告。两行无法安全容纳的文本会停止并要求处理，不会静默裁字。

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

## 安装这个 Skill

先确认你所使用 Agent 文档规定的 Skill 目录，再克隆仓库到该目录，或使用仓库内安装器传入该目录。仓库保持自包含，安装器也不会覆盖已有副本。

### Codex 示例

将仓库克隆到 Codex 配置的 Skill 目录：

```sh
git clone https://github.com/SuperWBY/wby-video-subtitles.git ~/.codex/skills/wby-video-subtitles
```

在其他 Agent 中使用时，先确认该客户端文档规定的 Skill 父目录，再运行安装器：

```sh
python3 scripts/install.py --target /absolute/path/to/that-agent/skills
```

安装成功不等于目标 Agent 已经发现并执行 Skill；请按照 [英文兼容性说明](references/compatibility.en.md) 完成验证。

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
