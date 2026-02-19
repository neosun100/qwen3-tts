[English](README_DEPLOY.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# 🗣️ Qwen3-TTS 一站式部署

[![Docker](https://img.shields.io/badge/Docker-neosun%2Fqwen3--tts-blue?logo=docker)](https://hub.docker.com/r/neosun/qwen3-tts)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)

基于 [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) 的一站式 Docker 服务，集成 **Web UI + REST API + MCP 服务器**。

## ✨ 功能特性

- 🎤 **自定义语音** — 9 种预设声音，支持指令控制情感/风格
- 🎨 **语音设计** — 用自然语言描述创建全新声音
- 🔊 **语音克隆** — 3 秒参考音频即可克隆声音
- 🌍 **10 种语言** — 中文、英语、日语、韩语、德语、法语、俄语、葡萄牙语、西班牙语、意大利语
- 🖥️ **Gradio UI** — 现代化界面，支持深色模式和多语言（中/英/日/繁体）
- 📡 **FastAPI** — 异步 REST API，Swagger 文档访问 `/docs`
- 🤖 **MCP 服务器** — 支持 AI 助手集成
- 🎮 **GPU 管理** — 自动选择空闲 GPU，懒加载，空闲自动释放

## 🚀 快速开始

### Docker 运行

```bash
docker pull neosun/qwen3-tts:latest

docker run -d --name qwen3-tts \
  --gpus '"device=0"' \
  -p 8766:8766 \
  -v /tmp/qwen3-tts:/tmp/qwen3-tts \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  neosun/qwen3-tts:latest
```

### Docker Compose

```bash
git clone https://github.com/neosun/qwen3-tts.git
cd qwen3-tts
./start.sh  # 自动选择最佳 GPU，构建并启动
```

### 访问地址

| 服务 | 地址 |
|------|------|
| Web 界面 | http://localhost:8766/ui |
| API 文档 | http://localhost:8766/docs |
| 健康检查 | http://localhost:8766/health |

## ⚙️ 配置说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | 8766 | 服务端口 |
| `GPU_IDLE_TIMEOUT` | 600 | 空闲 N 秒后自动释放 GPU |
| `DEFAULT_MODEL` | Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice | 默认模型 |
| `NVIDIA_VISIBLE_DEVICES` | 0 | GPU 设备 ID |
| `CUDA_DEVICE` | cuda:0 | PyTorch 设备 |

## 📡 API 示例

### 自定义语音
```bash
curl -X POST http://localhost:8766/api/tts/custom-voice \
  -H "Content-Type: application/json" \
  -d '{"text":"你好世界","speaker":"Vivian","language":"Chinese"}' \
  -o output.wav
```

### 语音设计
```bash
curl -X POST http://localhost:8766/api/tts/voice-design \
  -H "Content-Type: application/json" \
  -d '{"text":"你好世界","language":"Chinese","instruct":"温柔的年轻女声"}' \
  -o output.wav
```

### 语音克隆
```bash
curl -X POST http://localhost:8766/api/tts/voice-clone \
  -F "text=你好世界" -F "language=Chinese" \
  -F "ref_audio=@reference.wav" -F "ref_text=参考文本" \
  -o output.wav
```

## 🎤 预设声音

| 声音 | 描述 | 母语 |
|------|------|------|
| Vivian | 明亮的年轻女声 | 中文 |
| Serena | 温暖柔和的女声 | 中文 |
| Uncle_Fu | 沉稳低沉的男声 | 中文 |
| Dylan | 北京口音男声 | 中文（北京话）|
| Eric | 四川口音男声 | 中文（四川话）|
| Ryan | 活力男声 | 英语 |
| Aiden | 阳光美式男声 | 英语 |
| Ono_Anna | 活泼日本女声 | 日语 |
| Sohee | 温暖韩国女声 | 韩语 |

## 🤖 MCP 配置

详见 [MCP_GUIDE.md](MCP_GUIDE.md)。

## 🛠️ 技术栈

Qwen3-TTS · FastAPI · Gradio · PyTorch · FlashAttention 2 · CUDA · Docker

## 📄 许可证

Apache-2.0 — 基于阿里巴巴通义团队的 [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun/qwen3-tts&type=Date)](https://star-history.com/#neosun/qwen3-tts)

## 📱 关注公众号

![公众号](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
