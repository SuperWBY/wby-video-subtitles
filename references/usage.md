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

本机可选配置：`~/.local/share/wby-video-subtitles/machine.json` 包含 `font_path`、`model`。模型可以是本地模型目录或所选后端支持的模型名。只在本机保存绝对路径；分发包不包含用户模型/字体/凭据。字体请使用用户已有且允许使用的 TTF/OTF，不自动从未知站点下载。

以下用 PY 代表实际 Python 路径、SCRIPT 代表 skill/scripts/subtitles.py；实际执行时传递独立 argv 或正确 shell 引号。JOB 是当前视频目录内的新工作目录。

```text
PY SCRIPT doctor
PY SCRIPT init --video VIDEO --job JOB --font FONT
PY SCRIPT transcribe --job JOB
# 或导入已有字幕（不能在已有 captions.json 的 job 再导入）
PY SCRIPT import-srt --job JOB --srt SRT
PY SCRIPT prepare --job JOB
PY SCRIPT preview --job JOB --start 0 --seconds 8
PY SCRIPT render --job JOB
```

每次 prepare 保存新 revisions 子目录并更新 latest.json，后续 preview/render 使用该版本。相同版本输出存在会拒绝覆盖；修改参数后重新 prepare。配置改变但未 prepare，不会自动影响已有 ASS。

## 配置字段

| 字段 | 含义 |
|---|---|
| font_path | 字体文件绝对路径；使用该字体测量与渲染 |
| font_size_ratio | 字号与画面高度之比，默认 0.045；“大一点”可先提高约 10% 看预览 |
| min_font_size_ratio | 局部适配下限，默认 0.035，不得大于字号 |
| text_color | #RRGGBB，如 #FFFFFF |
| background_color / background_opacity | 背景颜色及 0–1 不透明度；0 关闭框背景 |
| outline_color / outline_px | 关闭背景时的描边色/宽度；开启背景时宽度作为边框尺寸 |
| margin_x_ratio / margin_y_ratio | 画面两侧及上下边距比例 |
| position | bottom 或 top |
| max_lines | 固定 2，不允许改成 3 |
| max_cps / min_duration / max_duration | 阅读速度及停留时间告警阈值；非行业通用标准 |
| terms | 本期术语字符串数组，用于转写提示和缺失提示，不自动替换 |
| backend / model / language | mlx 或 faster-whisper；模型名需与后端匹配；语言默认 zh |

背景是 libass 的矩形字幕背景，不支持圆角气泡。V0.1 把最终音频转为 AAC，不承诺原音轨逐字节相同。

## 编辑已有字幕

captions.json 是可编辑主稿，每项有 start/end/text，可选 words。修改前备份，并在 edits.json 记录变化。编辑 text 后不要伪造 word 时间；脚本只在词文本与主稿相符时使用。未拆分字幕保留段时间，拆分且无词时间时按字符比例估计并告警。

源视频内容变化必须新建 job；脚本每次核验内容哈希。原音轨只在转写阶段提取到临时目录，不存在跨视频音频缓存。

## 故障处理

错误返回非零退出码和 JSON error。无音轨可导入现成字幕；缺字先选择覆盖所需字符的字体；孤立超长词无法适配时调整宽度、字号或用户认可的分词位置。不要静默删字、截断或把失败视频标成完成。

prepare 报告只提供初步疑点。要查具体片段可用 preview 指定其 start，生成 PNG 和视频。首次新样式先出样片，后续明确授权的同样式批处理无需重复问。
