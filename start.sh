#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "🗣️ Qwen3-TTS Launcher"
echo "====================="

# Check nvidia-docker
if ! docker info 2>/dev/null | grep -q "Runtimes.*nvidia"; then
    if ! command -v nvidia-container-toolkit &>/dev/null && ! dpkg -l nvidia-container-toolkit &>/dev/null 2>&1; then
        echo "⚠️  nvidia-container-toolkit not detected, GPU may not work"
    fi
fi

# Auto-select GPU with least memory usage
GPU_ID=$(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits 2>/dev/null | \
         sort -t',' -k2 -n | head -1 | cut -d',' -f1 | tr -d ' ')
if [ -z "$GPU_ID" ]; then
    echo "⚠️  No GPU detected, using CPU"
    GPU_ID=0
else
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader -i "$GPU_ID" 2>/dev/null)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader -i "$GPU_ID" 2>/dev/null)
    echo "🎮 Selected GPU $GPU_ID: $GPU_NAME ($GPU_MEM)"
fi

# Check port
PORT=${PORT:-8766}
if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
    echo "❌ Port $PORT is already in use!"
    exit 1
fi

# Setup .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env from .env.example"
fi
sed -i "s/^NVIDIA_VISIBLE_DEVICES=.*/NVIDIA_VISIBLE_DEVICES=$GPU_ID/" .env

echo "🚀 Starting Qwen3-TTS..."
docker compose up -d --build

echo ""
echo "⏳ Waiting for service..."
for i in $(seq 1 60); do
    if curl -sf http://localhost:$PORT/health >/dev/null 2>&1; then
        echo ""
        echo "✅ Qwen3-TTS is running!"
        echo "   🌐 UI:      http://0.0.0.0:$PORT/ui"
        echo "   📡 API:     http://0.0.0.0:$PORT/docs"
        echo "   ❤️  Health:  http://0.0.0.0:$PORT/health"
        echo "   🎮 GPU:     $GPU_ID"
        exit 0
    fi
    printf "."
    sleep 5
done

echo ""
echo "⚠️  Service may still be starting. Check: docker logs qwen3-tts"
