# see - GLM 视觉桥接

让不支持多模态的模型通过 GLM-4.1V-Thinking-Flash 查看和分析图片。
支持 Windows / macOS / Linux，零第三方依赖。

> 完整文档见 [README.md](./README.md)。

## 触发条件

当用户要求你：
- 查看、识别、分析、描述一张或多张图片
- 从截图中提取文字或报错信息
- 比较两张或多张图片的差异
- 解读图表、流程图、架构图等视觉内容
- 回复中包含图片文件路径（.png / .jpg / .jpeg / .gif / .webp / .bmp）

**请使用此 Skill。**

## 使用方式

> **`$SEE_DIR` 是占位符**：AI 执行时应自行解析为 Skill 根目录的绝对路径；
> **手动执行时请替换为实际路径**，例如：
> `C:/Users/<你的用户名>/.zcode/skills/see-glm`（用户级 skill）或 `<克隆仓库路径>`。

先确定脚本绝对路径 `SEE_DIR`（Skill 根目录），然后调用 Python 主入口（跨平台）：

```
# 单图分析
python3 $SEE_DIR/scripts/see.py /path/to/image.png

# 带自定义问题
python3 $SEE_DIR/scripts/see.py /path/to/image.png --task "这张图里有什么问题？"

# 多图并行分析
python3 $SEE_DIR/scripts/see.py a.png b.png c.png

# 多图联合理解（放进同一次请求）
python3 $SEE_DIR/scripts/see.py --together a.png b.png --task "比较两张图的差异"

# 指定输出文件
python3 $SEE_DIR/scripts/see.py /path/to/image.png -o /path/to/result.md
```

macOS / Linux 也可通过 bash 包装调用（内部调用 see.py）：

```bash
bash $SEE_DIR/scripts/see.sh /path/to/image.png
```

Windows 若 `python3` 不在 PATH，请改用 `python`；路径可用正斜杠格式
（如 `C:/Users/me/Desktop/screenshot.png`）。

## 参数说明

| 参数 | 用途 |
|------|------|
| `图片路径/URL` | 必填，支持本地文件和 HTTPS URL |
| `--task "问题"` | 可选，自定义提问，原样发送给视觉模型 |
| `--together` | 可选，多图联合理解模式，所有图进入同一次请求 |
| `--jobs N` | 可选，并行模式下并发数，默认 3 |
| `--model NAME` | 可选，临时覆盖模型（默认 GLM-4.1V-Thinking-Flash） |
| `-o FILE` | 可选，指定结果输出文件路径 |
| `--onboard` | 可选，快捷启动配置流程 |

## 输出格式

成功后 stdout 只输出一行：

```
output_path=/absolute/path/result.md
```

结果 Markdown 包含：
- 实际使用的模型
- 分析模式（单图/并行/联合）
- 视觉模型的完整回复（含思维链和结论）

## 安装与配置

首次使用前需要配置 API Key（脚本会引导）：

```
python3 $SEE_DIR/scripts/onboard.py
```

查看当前配置状态：

```
python3 $SEE_DIR/scripts/onboard.py --status
```

也可在 see.py 中直接使用 `--onboard` 快捷配置：

```
python3 $SEE_DIR/scripts/see.py --onboard
```

Windows 若 `python3` 不在 PATH，请改用 `python`。

## 配置文件位置

- **Windows**: `%APPDATA%\see-glm\config.env`（通常是 `C:\Users\用户名\AppData\Roaming\see-glm\config.env`）
- **macOS / Linux**: `~/.config/see-glm/config.env`

API Key 不会写入项目仓库，也支持环境变量 `GLM_API_KEY` 配置。

## 注意事项

- 支持 PNG / JPG / JPEG / GIF / WebP / BMP 格式
- 图片以 base64 原图发送，不预先压缩或缩放
- 如果用户没有配置 API Key，脚本会提示先运行 onboard
- 不要直接拖拽或粘贴图片附件，请先将图片保存到本地再发送文件路径
- Windows 路径可以用 `C:/Users/...` 正斜杠格式
- 零第三方依赖，仅需 Python 3 标准库
