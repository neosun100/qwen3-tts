[English](README_DEPLOY.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# 🗣️ Qwen3-TTS All-in-One

[![Docker](https://img.shields.io/badge/Docker-neosun%2Fqwen3--tts-blue?logo=docker)](https://hub.docker.com/r/neosun/qwen3-tts)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)

All-in-one Docker service for [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) with **Web UI + REST API + MCP Server**.

## ✨ Features

- 🎤 **Custom Voice** — 9 preset speakers with instruction-based style control
- 🎨 **Voice Design** — Create new voices from natural language descriptions
- 🔊 **Voice Clone** — Clone any voice from a 3-second audio clip
- 🌍 **10 Languages** — Chinese, English, Japanese, Korean, German, French, Russian, Portuguese, Spanish, Italian
- 🖥️ **Gradio UI** — Modern web interface with dark mode and i18n (en/zh-CN/zh-TW/ja)
- 📡 **FastAPI** — Async REST API with Swagger docs at `/docs`
- 🤖 **MCP Server** — Model Context Protocol for AI assistant integration
- 🎮 **GPU Management** — Auto-select idle GPU, lazy loading, auto-offload

## 🚀 Quick Start

### Docker Run

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
./start.sh  # Auto-selects best GPU, builds & starts
```

### Access

| Service | URL |
|---------|-----|
| Web UI | http://localhost:8766/ui |
| API Docs | http://localhost:8766/docs |
| Health | http://localhost:8766/health |

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8766 | Service port |
| `GPU_IDLE_TIMEOUT` | 600 | Auto-offload after N seconds idle |
| `DEFAULT_MODEL` | Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice | Default model |
| `NVIDIA_VISIBLE_DEVICES` | 0 | GPU device ID |
| `CUDA_DEVICE` | cuda:0 | PyTorch device |

## 📡 API Examples

### Custom Voice
```bash
curl -X POST http://localhost:8766/api/tts/custom-voice \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","speaker":"Ryan","language":"English"}' \
  -o output.wav
```

### Voice Design
```bash
curl -X POST http://localhost:8766/api/tts/voice-design \
  -H "Content-Type: application/json" \
  -d '{"text":"你好世界","language":"Chinese","instruct":"温柔的年轻女声"}' \
  -o output.wav
```

### Voice Clone
```bash
curl -X POST http://localhost:8766/api/tts/voice-clone \
  -F "text=Hello world" -F "language=English" \
  -F "ref_audio=@reference.wav" -F "ref_text=Original transcript" \
  -o output.wav
```

## 🎤 Speakers

| Speaker | Description | Native Language |
|---------|-------------|-----------------|
| Vivian | Bright young female | Chinese |
| Serena | Warm gentle female | Chinese |
| Uncle_Fu | Seasoned low male | Chinese |
| Dylan | Beijing male | Chinese (Beijing) |
| Eric | Sichuan male | Chinese (Sichuan) |
| Ryan | Dynamic male | English |
| Aiden | Sunny American male | English |
| Ono_Anna | Playful Japanese female | Japanese |
| Sohee | Warm Korean female | Korean |

## 🤖 MCP Setup

See [MCP_GUIDE.md](MCP_GUIDE.md) for MCP server configuration.

## 🛠️ Tech Stack

Qwen3-TTS · FastAPI · Gradio · PyTorch · FlashAttention 2 · CUDA · Docker

## 📄 License

Apache-2.0 — Based on [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) by Alibaba Qwen Team.

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun/qwen3-tts&type=Date)](https://star-history.com/#neosun/qwen3-tts)

## 📱 关注公众号

![公众号](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
