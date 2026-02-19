[English](README_DEPLOY.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# 🗣️ Qwen3-TTS オールインワン

[![Docker](https://img.shields.io/badge/Docker-neosun%2Fqwen3--tts-blue?logo=docker)](https://hub.docker.com/r/neosun/qwen3-tts)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)

[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) ベースのオールインワン Docker サービス。**Web UI + REST API + MCP サーバー**を統合。

## ✨ 機能

- 🎤 **カスタム音声** — 9種のプリセット音声、指示による感情/スタイル制御
- 🎨 **音声デザイン** — 自然言語で新しい音声を作成
- 🔊 **音声クローン** — 3秒の参照音声から音声をクローン
- 🌍 **10言語対応** — 中国語、英語、日本語、韓国語、ドイツ語、フランス語、ロシア語、ポルトガル語、スペイン語、イタリア語
- 🖥️ **Gradio UI** — ダークモード・多言語対応のモダンUI
- 📡 **FastAPI** — 非同期REST API、Swaggerドキュメント `/docs`
- 🤖 **MCPサーバー** — AIアシスタント統合対応
- 🎮 **GPU管理** — アイドルGPU自動選択、遅延ロード、自動オフロード

## 🚀 クイックスタート

```bash
docker pull neosun/qwen3-tts:latest

docker run -d --name qwen3-tts \
  --gpus '"device=0"' \
  -p 8766:8766 \
  -v /tmp/qwen3-tts:/tmp/qwen3-tts \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  neosun/qwen3-tts:latest
```

### アクセス

| サービス | URL |
|----------|-----|
| Web UI | http://localhost:8766/ui |
| APIドキュメント | http://localhost:8766/docs |
| ヘルスチェック | http://localhost:8766/health |

## 📡 API例

```bash
# カスタム音声
curl -X POST http://localhost:8766/api/tts/custom-voice \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは","speaker":"Ono_Anna","language":"Japanese"}' -o output.wav

# 音声デザイン
curl -X POST http://localhost:8766/api/tts/voice-design \
  -H "Content-Type: application/json" \
  -d '{"text":"こんにちは","language":"Japanese","instruct":"明るい若い女性の声"}' -o output.wav

# 音声クローン
curl -X POST http://localhost:8766/api/tts/voice-clone \
  -F "text=こんにちは" -F "ref_audio=@reference.wav" -F "ref_text=参照テキスト" -o output.wav
```

## 🤖 MCP設定

[MCP_GUIDE.md](MCP_GUIDE.md) を参照してください。

## 📄 ライセンス

Apache-2.0 — Alibaba Qwenチームの [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) に基づく。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun/qwen3-tts&type=Date)](https://star-history.com/#neosun/qwen3-tts)

## 📱 公式アカウント

![公式アカウント](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
