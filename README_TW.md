[English](README_DEPLOY.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# 🗣️ Qwen3-TTS 一站式部署

[![Docker](https://img.shields.io/badge/Docker-neosun%2Fqwen3--tts-blue?logo=docker)](https://hub.docker.com/r/neosun/qwen3-tts)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)

基於 [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) 的一站式 Docker 服務，整合 **Web UI + REST API + MCP 伺服器**。

## ✨ 功能特色

- 🎤 **自訂語音** — 9 種預設聲音，支援指令控制情感/風格
- 🎨 **語音設計** — 用自然語言描述創建全新聲音
- 🔊 **語音複製** — 3 秒參考音訊即可複製聲音
- 🌍 **10 種語言** — 中文、英語、日語、韓語、德語、法語、俄語、葡萄牙語、西班牙語、義大利語
- 🖥️ **Gradio UI** — 現代化介面，支援深色模式和多語言
- 📡 **FastAPI** — 非同步 REST API，Swagger 文件於 `/docs`
- 🤖 **MCP 伺服器** — 支援 AI 助手整合
- 🎮 **GPU 管理** — 自動選擇閒置 GPU，延遲載入，閒置自動釋放

## 🚀 快速開始

```bash
docker pull neosun/qwen3-tts:latest

docker run -d --name qwen3-tts \
  --gpus '"device=0"' \
  -p 8766:8766 \
  -v /tmp/qwen3-tts:/tmp/qwen3-tts \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  neosun/qwen3-tts:latest
```

### 存取位址

| 服務 | 位址 |
|------|------|
| Web 介面 | http://localhost:8766/ui |
| API 文件 | http://localhost:8766/docs |
| 健康檢查 | http://localhost:8766/health |

## ⚙️ 設定說明

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `PORT` | 8766 | 服務埠 |
| `GPU_IDLE_TIMEOUT` | 600 | 閒置 N 秒後自動釋放 GPU |
| `NVIDIA_VISIBLE_DEVICES` | 0 | GPU 裝置 ID |

## 📡 API 範例

```bash
# 自訂語音
curl -X POST http://localhost:8766/api/tts/custom-voice \
  -H "Content-Type: application/json" \
  -d '{"text":"你好世界","speaker":"Vivian","language":"Chinese"}' -o output.wav

# 語音設計
curl -X POST http://localhost:8766/api/tts/voice-design \
  -H "Content-Type: application/json" \
  -d '{"text":"你好世界","language":"Chinese","instruct":"溫柔的年輕女聲"}' -o output.wav

# 語音複製
curl -X POST http://localhost:8766/api/tts/voice-clone \
  -F "text=你好世界" -F "ref_audio=@reference.wav" -F "ref_text=參考文字" -o output.wav
```

## 🤖 MCP 設定

詳見 [MCP_GUIDE.md](MCP_GUIDE.md)。

## 📄 授權

Apache-2.0 — 基於阿里巴巴通義團隊的 [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun/qwen3-tts&type=Date)](https://star-history.com/#neosun/qwen3-tts)

## 📱 關注公眾號

![公眾號](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
