# 运行与配置

## 环境

使用 Python 3.12，安装 pillow、fonttools、imageio-ffmpeg、jieba。使用转写再安装 mlx-whisper（Apple Silicon）或 faster-whisper（CPU 路径，未在本包跨系统实测）。FFmpeg 需要 ass/libass 滤镜和 libx264 编码器。doctor 输出可用包和滤镜。

先检查 `~/.local/share/wby-video-subtitles/venv/bin/python`（Windows 为相应 Scripts/python.exe），没有则在该位置建立 venv 并安装上述依赖。安装转写模型可能需要网络与磁盘空间，不把首次下载时间算为转写性能。Skill 源目录由 Agent 当前发现位置确定，不能写死作者的桌面路径。

```sh
python3 -m venv ~/.local/share/wby-video-subtitles/venv
~/.local/share/wby-video-subtitles/venv/bin/python -m pip install pillow fonttools imageio-ffmpeg jieba
# Apple Silicon 转写
~/.local/share/wby-video-subtitles/venv/bin/python -m pip install mlx-whisper
```

Skill 内置 SIL OFL 1.1 授权的 `Noto Sans CJK SC Regular`。字体选择顺序为命令行 `--font`、本机配置、内置字体。本机可选配置：`~/.local/share/wby-video-subtitles/machine.json` 包含 `font_path`、`model`。模型可以是本地模型目录或所选后端支持的模型名。只在本机保存模型与自定义字体绝对路径，不自动从未知站点下载字体。

以下用 PY 代表实际 Python 路径、SCRIPT 代表 skill/scripts/subtitles.py；实际执行时传递独立 argv 或正确 shell 引号。JOB 是当前视频目录内的新工作目录。

```text
PY SCRIPT doctor
PY SCRIPT init --video VIDEO --job JOB --language auto --preset standard
PY SCRIPT transcribe --job JOB
# 或导入已有字幕（不能在已有 captions.json 的 job 再导入）
PY SCRIPT import-srt --job JOB --srt SRT
PY SCRIPT apply-terms --job JOB --json REVIEWED_CORRECTIONS
PY SCRIPT import-translations --job JOB --json REVIEWED_TRANSLATIONS
PY SCRIPT prepare --job JOB
PY SCRIPT preview --job JOB --start 0 --seconds 8
PY SCRIPT render --job JOB
```

每次 prepare 保存新 revisions 子目录并更新 latest.json，后续 preview/render 使用该版本。相同版本输出存在会拒绝覆盖；修改参数后重新 prepare。配置改变但未 prepare，不会自动影响已有 ASS。

## 配置字段

`init` 提供三个字号预设。字号按画面高度计算，避免横屏、竖屏和 4K 使用同一固定像素值：

| 预设 | 主字号 | 最小字号 | 译文相对字号 | 适用场景 |
|---|---:|---:|---:|---|
| compact | 4.0% | 3.2% | 76% | 信息密集的录屏 |
| standard | 4.5% | 3.5% | 78% | 默认口播与演示 |
| emphasis | 5.2% | 4.0% | 80% | 字少、强调感强的画面 |

`standard` 在 1080 高画面约为 49 px，在 2160 高画面约为 97 px。过长字幕会在最小字号范围内逐级缩小；仍放不下时停止并要求拆句，不会裁字。

| 字段 | 含义 |
|---|---|
| font_path | 字体文件路径；默认内置 Noto Sans CJK SC Regular，可用 `--font` 或配置覆盖 |
| style_preset | 创建 job 时使用的 compact / standard / emphasis 记录；后续实际渲染以各比例字段为准 |
| font_size_ratio | 字号与画面高度之比，默认 0.045；“大一点”可先提高约 10% 看预览 |
| min_font_size_ratio | 局部适配下限，默认 0.035，不得大于字号 |
| text_color | #RRGGBB，如 #FFFFFF |
| background_color / background_opacity | 背景颜色及 0–1 不透明度；0 关闭框背景 |
| outline_color / outline_px | 关闭背景时的描边色/宽度；开启背景时宽度作为边框尺寸 |
| margin_x_ratio / margin_y_ratio | 画面两侧及上下边距比例 |
| position | bottom 或 top |
| max_lines | 固定 2，不允许改成 3 |
| max_cps / min_duration / max_duration | 阅读速度及停留时间告警阈值；默认 max_cps 为 17，但不同语言需要自行调整，不是行业通用标准 |
| terms | 本期术语字符串数组，用于转写提示和缺失提示，不自动替换 |
| translation_font_scale / translation_color | 双语第二行相对字号（0.5–1）和颜色 |
| backend / model / language | mlx 或 faster-whisper；模型名需与后端匹配；源语言默认自动识别，也可用后端支持的 en、fr、zh、ja、pt 等代码明确指定 |

背景是 libass 的矩形字幕背景，不支持圆角气泡。V0.1 把最终音频转为 AAC，不承诺原音轨逐字节相同。

## 编辑已有字幕

captions.json 是可编辑主稿，每项有 start/end/text，可选 words。修改前备份，并在 edits.json 记录变化。编辑 text 后不要伪造 word 时间；脚本只在词文本与主稿相符时使用。未拆分字幕保留段时间，拆分且无词时间时按字符比例估计并告警。

源视频内容变化必须新建 job；脚本每次核验内容哈希。原音轨只在转写阶段提取到临时目录，不存在跨视频音频缓存。

## 故障处理

错误返回非零退出码和 JSON error。无音轨可导入现成字幕；缺字先选择覆盖所需字符的字体；孤立超长词无法适配时调整宽度、字号或用户认可的分词位置。不要静默删字、截断或把失败视频标成完成。

prepare 报告只提供初步疑点。要查具体片段可用 preview 指定其 start，生成 PNG 和视频。首次新样式先出样片，后续明确授权的同样式批处理无需重复问。

## 术语校正

`terms` 会进入转写提示，但不会强行替换近音词。复听后创建校正文件；目标词必须已经列入 `config.json` 的 `terms`：

```json
{
  "version": 1,
  "corrections": [{
    "source_cue": 3,
    "from": "飞个马",
    "to": "Figma",
    "evidence": "复听 00:03.60–00:09.32，口播明确为 Figma"
  }]
}
```

`apply-terms` 只替换指定字幕中唯一匹配的文字，先在 `backups/` 保存旧稿，再把依据写入 `edits.json`。它不是自动语义纠错。

## 双语字幕

先校正原文，再为每条源字幕生成并复核一条目标语言翻译。输入文件必须覆盖所有源字幕：

```json
{
  "version": 1,
  "target_language": "fr",
  "cues": [{
    "source_cue": 1,
    "source_text": "看字幕，变大。",
    "text": "Regardez les sous-titres s'agrandir."
  }]
}
```

导入时保存源字幕哈希；之后若原文发生变化，`prepare` 会拒绝继续。双语模式固定原文一行、译文一行。任一行在最小字号仍放不下时会报错，必须人工拆句和重新定时，不会压成第三行或裁字。

## 按口播制作字号和颜色效果

在 job 根目录创建 `style-effects.json`。时间是源视频的绝对秒数：

```json
{
  "version": 1,
  "effects": [
    {"start": 0.8, "end": 1.8, "font_scale": 1.6, "transition_ms": 120},
    {"start": 2.0, "end": 3.2, "font_scale": 1.0, "text_color": "#FFD400", "transition_ms": 100}
  ]
}
```

`font_scale` 范围是 0.5–3，`transition_ms` 范围是 0–1000。效果作用于该时间内显示的整条字幕，可在字幕显示期间开始或结束。先对照口播和源视频确定时间，再生成局部预览；这不是录制时的实时语音控制。
