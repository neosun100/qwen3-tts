# ============================================================================
# Qwen3-TTS v2.0.0 — All-in-One Docker Image
# Models + Dependencies + UI baked in. No external downloads at runtime.
#
# Build: docker build -t neosun/qwen3-tts:2.0.0 .
# Run:   docker run --gpus '"device=0"' -p 8766:8766 neosun/qwen3-tts:2.0.0
# ============================================================================

FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System deps + Python 3.12
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3.12-venv python3.12-dev \
    ffmpeg sox libsndfile1 git curl && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Stage 1: Install Python deps (cached layer) ──
# Pin torch 2.9.1 to use pre-compiled flash-attn wheel (avoids 40+ min build)
COPY pyproject.toml setup.py* setup.cfg* MANIFEST.in ./
COPY qwen_tts/ ./qwen_tts/

RUN pip install --no-cache-dir torch==2.9.1 torchaudio && \
    pip install --no-cache-dir transformers==4.57.3 accelerate==1.12.0 && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir fastapi "uvicorn[standard]" python-multipart

# ── Stage 2: flash-attn via pre-compiled wheel (seconds, not hours) ──
# Wheel: Python 3.12 + CUDA 12 + PyTorch 2.9 + CXX11 ABI True
RUN pip install --no-cache-dir \
    "https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3%2Bcu12torch2.9cxx11abiTRUE-cp312-cp312-linux_x86_64.whl"

# ── Stage 3: Embed all models (all-in-one, ~14GB) ──
COPY models/ /app/models/

# ── Stage 4: Application code (changes frequently, keep last) ──
COPY app.py ui.html ./

ENV QWEN_TTS_MODEL_DIR=/app/models
ENV HF_HUB_OFFLINE=1

EXPOSE 8766

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8766/health || exit 1

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8766"]
