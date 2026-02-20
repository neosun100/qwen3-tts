# 【一键部署系列】｜19｜TTS｜Qwen3-TTS-Docker   阿里通义千问语音合成，9种音色+10种语言+3大模式，All-in-One Docker一行命令拉起

![Qwen3-TTS Logo](https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-TTS-Repo/qwen3_tts_logo.png)

>微信公众号：**[AI健自习室]**  
>关注Crypto与LLM技术、关注`AI-StudyLab`。问题或建议，请公众号留言。

>[!info] **项目信息**  
>• **GitHub**: https://github.com/neosun100/Qwen3-TTS  
>• **最新版本**: v2.0.0 (2026-02-20)  
>• **Docker镜像**: `neosun/qwen3-tts:2.0.0`  
>• **Star支持**: ⭐ 给项目一个Star吧！

> **一句话概括这个项目：**  
> 🗣️ 阿里 Qwen3-TTS 的**生产级 Docker 封装**——4 个模型（14GB）全部烘焙进一个 Docker 镜像，`docker pull` 一行拉取，`docker run` 一行启动。9 种预设音色、10 种语言、3 大合成模式（自定义语音 / 语音设计 / 语音克隆），配备暗色主题 Web UI + 完整 REST API + Swagger 文档。  
> 没有 Gradio，没有运行时下载，没有 40 分钟的 flash-attn 编译。**开箱即用。**

---

## 🤔 为什么要做这个项目？

先回答一个最核心的问题：**Qwen3-TTS 官方仓库已经有了，为什么还需要这个项目？**

如果你试过直接部署 [Qwen3-TTS 官方仓库](https://github.com/QwenLM/Qwen3-TTS)，你一定经历过这些痛苦：

| 😩 官方仓库的痛点 | ✅ 本项目的解决方案 |
|---|---|
| 需要手动下载 4 个模型（14GB），经常断线 | **All-in-One 镜像**，模型全部内嵌，零下载 |
| 默认 UI 是 Gradio，定制性差 | **纯 HTML/JS 暗色主题 UI**，现代、美观、响应式 |
| `flash-attn` 编译 40+ 分钟，经常失败 | **预编译 wheel**，6 秒安装 |
| 没有 REST API，只能通过 Gradio 交互 | **18 个 REST API 端点** + Swagger 文档 |
| 没有性能指标，不知道生成花了多久 | **实时性能面板**：加载/生成/总耗时/RTF |
| 没有 GPU 管理，显存一直占着 | **自动空闲卸载** + 手动释放按钮 |
| 没有 Docker 支持 | **docker-compose.yml** + **start.sh** 一键启动 |

> 💡 **一句话总结**：官方仓库是"实验室 Demo"，这个项目是"生产级部署方案"。

---

## 📸 先看效果

眼见为实。先看看 UI 长什么样：

### 🎤 Custom Voice — 自定义语音

![Custom Voice](https://raw.githubusercontent.com/neosun100/qwen3-tts/main/screenshots/01-main-custom-voice.png)

左侧是 **9 位说话人卡片**（含性别、语言、声音描述），右侧是合成面板。选择说话人、输入文本、可选添加情感指令（如"用悲伤的语气说"），点击生成即可。底部实时显示**性能指标**：模型加载时间、生成时间、音频时长、RTF。

### 🎨 Voice Design — 语音设计

![Voice Design](https://raw.githubusercontent.com/neosun100/qwen3-tts/main/screenshots/02-voice-design.png)

这是最有创意的模式——**用自然语言描述你想要的声音**。比如"体现撒娇稚嫩的萝莉女声，音调偏高且起伏明显"，模型会凭空创造出一个全新的声音。内置 6 个快速预设：萝莉、毒舌少女、宫廷剧、播音员、悲伤旁白、自信男声。

### 🔊 Voice Clone — 语音克隆

![Voice Clone](https://raw.githubusercontent.com/neosun100/qwen3-tts/main/screenshots/03-voice-clone.png)

上传一段 **3 秒以上的参考音频**，模型就能克隆这个声音，用它来朗读任何文本。支持跨语言克隆——用中文参考音频生成英文语音，反之亦然。还支持**保存/加载音色文件**（`.pt`），一次克隆，反复使用。

---

## 🚀 30 秒部署：3 种方式任选

### 方式一：Docker Hub 直接拉取（推荐）

```bash
# 拉取 All-in-One 镜像（~30GB，含全部模型）
docker pull neosun/qwen3-tts:2.0.0

# 一行启动
docker run -d --name qwen3-tts \
  --gpus '"device=0"' \
  -p 8766:8766 \
  neosun/qwen3-tts:2.0.0
```

打开浏览器访问 **http://localhost:8766** 即可。

### 方式二：Docker Compose

```bash
git clone https://github.com/neosun100/Qwen3-TTS.git
cd Qwen3-TTS

# 设置 GPU（改成你的 GPU 编号）
echo "NVIDIA_VISIBLE_DEVICES=0" > .env

docker compose up -d
```

### 方式三：一键脚本（自动选 GPU）

```bash
git clone https://github.com/neosun100/Qwen3-TTS.git
cd Qwen3-TTS
bash start.sh
```

`start.sh` 会自动检测显存最空闲的 GPU、检查端口冲突、创建配置文件，然后启动容器。

> 📌 **启动后的 3 个入口**：
>
> | 地址 | 用途 |
> |---|---|
> | `http://localhost:8766` | 🌐 Web UI |
> | `http://localhost:8766/docs` | 📡 Swagger API 文档 |
> | `http://localhost:8766/health` | ❤️ 健康检查 |

---

## 🧠 3 大合成模式，覆盖所有场景

### 模式对比一览

| 维度 | 🎤 Custom Voice | 🎨 Voice Design | 🔊 Voice Clone |
|------|-----------------|------------------|-----------------|
| **核心能力** | 9 种预设高品质音色 | 用文字描述创造新声音 | 3 秒音频克隆任意声音 |
| **适用场景** | 有声书、播客、客服 | 角色配音、创意内容 | 个性化语音、声音复刻 |
| **情感控制** | ✅ 指令控制 | ✅ 描述控制 | ❌ 跟随参考音频 |
| **所需输入** | 文本 + 说话人 + 指令 | 文本 + 声音描述 | 文本 + 参考音频 |
| **使用模型** | CustomVoice (4.3GB) | VoiceDesign (4.3GB) | Base (4.3GB) |

### 9 位说话人档案

| 说话人 | 性别 | 母语 | 声音特点 |
|--------|------|------|----------|
| 🎙️ Vivian | 女 | 中文 | 明亮、略带锐利的年轻女声 |
| 🎙️ Serena | 女 | 中文 | 温暖、柔和的年轻女声 |
| 🎙️ Uncle_Fu | 男 | 中文 | 沉稳低沉的成熟男声 |
| 🎙️ Dylan | 男 | 中文（北京） | 清朗自然的北京青年男声 |
| 🎙️ Eric | 男 | 中文（四川） | 活泼略带沙哑的成都男声 |
| 🎙️ Ryan | 男 | 英文 | 动感十足、节奏感强的男声 |
| 🎙️ Aiden | 男 | 英文 | 阳光美式男声、中频清晰 |
| 🎙️ Ono_Anna | 女 | 日文 | 俏皮轻盈的日语女声 |
| 🎙️ Sohee | 女 | 韩文 | 温暖富有情感的韩语女声 |

### 10 种语言支持

中文、英文、日文、韩文、德文、法文、俄文、葡萄牙文、西班牙文、意大利文。

> 💡 **跨语言能力**：你可以让日语说话人 Ono_Anna 说中文，或者让中文说话人 Vivian 说英文。模型会保持音色特征的同时切换语言。

---

## 📡 完整 REST API：18 个端点，Swagger 一目了然

这不只是一个 Web UI 项目——它有**完整的 REST API**，可以直接集成到你的业务系统中。

### API 调用示例

**Custom Voice（自定义语音）：**

```bash
curl -X POST http://localhost:8766/api/tts/custom-voice \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，欢迎使用通义千问语音合成系统。",
    "language": "Chinese",
    "speaker": "Vivian",
    "instruct": "用温柔的语气说"
  }' -o output.wav
```

**Voice Design（语音设计）：**

```bash
curl -X POST http://localhost:8766/api/tts/voice-design \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world!",
    "language": "English",
    "instruct": "Young female voice, cheerful and bright"
  }' -o output.wav
```

**Voice Clone（语音克隆）：**

```bash
curl -X POST http://localhost:8766/api/tts/voice-clone \
  -F "text=用克隆的声音说这段话" \
  -F "language=Chinese" \
  -F "ref_text=这是参考音频的文字内容" \
  -F "ref_audio=@reference.wav" \
  -o output.wav
```

### 全部 18 个端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/speakers` | 说话人列表（含详情） |
| GET | `/api/languages` | 支持的语言列表 |
| GET | `/api/models` | 可用模型列表 |
| GET | `/api/gpu-status` | GPU 显存和模型状态 |
| GET | `/api/sample-texts` | 各语言示例文本 |
| POST | `/api/gpu-offload` | 手动释放 GPU 显存 |
| POST | `/api/tts/custom-voice` | 自定义语音合成 |
| POST | `/api/tts/voice-design` | 语音设计合成 |
| POST | `/api/tts/voice-clone` | 语音克隆合成 |
| POST | `/api/tts/voice-clone-from-prompt` | 从保存的音色文件合成 |
| POST | `/api/voice-prompt/save` | 保存克隆音色（.pt） |
| POST | `/api/tts/custom-voice/stream` | PCM 流式自定义语音 |
| POST | `/api/tts/voice-design/stream` | PCM 流式语音设计 |
| POST | `/api/tts/voice-clone/stream` | PCM 流式语音克隆 |
| POST | `/api/tokenizer/encode` | 音频编码为 token |
| POST | `/api/tokenizer/decode` | token 解码为音频 |

### 性能监控 Headers

每个 TTS 端点都会返回计时 Headers，方便监控和调优：

| Header | 含义 |
|---|---|
| `X-Time-Load` | 模型加载耗时（秒） |
| `X-Time-Gen` | 音频生成耗时（秒） |
| `X-Time-Total` | 总处理耗时（秒） |
| `X-Audio-Duration` | 生成音频时长（秒） |

> 📌 **实测数据**（NVIDIA L40S GPU）：  
> - 模型首次加载：~5 秒  
> - 模型已缓存时：0 秒（直接复用）  
> - 英文短句生成：~5-10 秒  
> - RTF（实时率）：约 2x（即生成 1 秒音频需要 2 秒计算）

---

## ⚡ 关于流式输出：一个必须说清楚的事

这是很多人关心的问题，我们必须**坦诚说明**。

### 结论先行：Qwen3-TTS 目前不支持真正的流式音频输出

这不是我们项目的限制，而是**模型本身的限制**。官方 Qwen 团队在 [GitHub Issue #10](https://github.com/QwenLM/Qwen3-TTS/issues/10) 中明确回复：

> *"Streaming inference is supported at the model architecture level. Currently, our qwen-tts package primarily focuses on enabling quick demos... For streaming capabilities, ongoing development will be mainly driven by the **vLLM-Omni** community."*

翻译一下：**模型架构支持流式，但官方 SDK 不支持。真正的流式要等 vLLM-Omni 社区实现。**

### 那我们的 `/stream` 端点是什么？

我们的 `/stream` 端点采用的是**"生成后分块传输"**策略：

```
┌─────────────────────────────────────────────┐
│  标准模式：  生成完整音频 → 一次性返回 WAV    │
│  流式模式：  生成完整音频 → 分块传输 PCM      │
│                                              │
│  ⚠️ 两种模式的 TTFB（首字节时间）相同         │
│  ✅ 流式模式支持 Web Audio API 渐进式播放     │
└─────────────────────────────────────────────┘
```

### 真正的流式什么时候能实现？

关注这两个项目：

| 项目 | 状态 | 说明 |
|------|------|------|
| [vLLM-Omni](https://github.com/vllm-project/vllm-omni) | 🔄 开发中 | 官方推荐路径，等待 [RFC #938](https://github.com/vllm-project/vllm/issues/938) |
| [dffdeeq/Qwen3-TTS-streaming](https://github.com/dffdeeq/Qwen3-TTS-streaming) | 🧪 实验性 | 社区 fork，每 8 token 发射一次音频 chunk |

> 💡 **我们的态度**：不夸大、不隐瞒。当 vLLM-Omni 的流式支持成熟后，我们会第一时间集成。

---

## 🔬 Dockerfile 技术解析：flash-attn 从 40 分钟到 6 秒

这是整个项目中**最值得分享的工程经验**。

### 问题：flash-attn 编译是出了名的慢

`flash-attn`（FlashAttention 2）是当前最高效的注意力计算实现，Qwen3-TTS 依赖它来加速推理。但从源码编译 flash-attn 需要：

- CUDA 开发头文件（`nvidia/cuda:*-devel` 镜像）
- `ninja` 并行编译工具
- 大量 RAM（96GB+ 推荐）
- **40-60 分钟**编译时间
- 还经常因为版本不匹配而失败（成功率约 70%）

### 解决方案：预编译 wheel 文件

FlashAttention 团队在 [GitHub Releases](https://github.com/Dao-AILab/flash-attention/releases) 提供了预编译的 `.whl` 文件。关键是**精确匹配版本**：

```
flash_attn-2.8.3+cu12torch2.9cxx11abiTRUE-cp312-cp312-linux_x86_64.whl
                 ^^^^ ^^^^^^^^ ^^^^^^^^^^^  ^^^^
                 CUDA  PyTorch  C++ ABI     Python
```

我们的 Dockerfile 中只需一行：

```dockerfile
# 6 秒完成安装（而不是 40 分钟编译）
RUN pip install --no-cache-dir \
    "https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3%2Bcu12torch2.9cxx11abiTRUE-cp312-cp312-linux_x86_64.whl"
```

### 构建时间对比

| 方案 | flash-attn 安装时间 | 成功率 |
|------|---------------------|--------|
| 源码编译 `pip install flash-attn` | 40-60 分钟 | ~70% |
| 加 ninja `MAX_JOBS=4 pip install flash-attn` | 15-30 分钟 | ~85% |
| **预编译 wheel（本项目方案）** | **6 秒** | **100%** |

### 为什么固定 PyTorch 2.9.1？

因为截至发稿，flash-attn 官方 releases 最高只提供到 `torch2.9` 的预编译 wheel。PyTorch 2.10 虽然已发布，但没有对应的 flash-attn wheel。所以我们在 Dockerfile 中固定：

```dockerfile
RUN pip install --no-cache-dir torch==2.9.1 torchaudio && \
    pip install --no-cache-dir transformers==4.57.3 accelerate==1.12.0
```

> 📌 **经验总结**：选择预编译 wheel 时，必须同时匹配 4 个维度——Python 版本、CUDA 版本、PyTorch 版本、C++ ABI。任何一个不匹配都会导致运行时错误。

---

## 🏗️ 技术架构全景

### 项目结构

```
Qwen3-TTS/
├── app.py              ← FastAPI 后端（661 行，纯 Python，无 Gradio）
├── ui.html             ← 前端 UI（769 行，纯 HTML/CSS/JS）
├── Dockerfile          ← All-in-One 构建（预编译 flash-attn）
├── docker-compose.yml  ← 一键编排
├── start.sh            ← 智能启动脚本（自动选 GPU）
├── pyproject.toml      ← Python 包配置
├── qwen_tts/           ← Qwen3-TTS 核心推理代码
└── models/             ← 4 个模型（构建时嵌入镜像）
    ├── Qwen3-TTS-12Hz-1.7B-CustomVoice/  (4.3GB)
    ├── Qwen3-TTS-12Hz-1.7B-VoiceDesign/  (4.3GB)
    ├── Qwen3-TTS-12Hz-1.7B-Base/         (4.3GB)
    └── Qwen3-TTS-Tokenizer-12Hz/         (651MB)
```

### 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **基础镜像** | `nvidia/cuda:12.4.1-devel-ubuntu22.04` | CUDA 12.4 开发环境 |
| **运行时** | Python 3.12 + PyTorch 2.9.1 | 固定版本确保兼容 |
| **加速** | FlashAttention 2 (v2.8.3) | 预编译 wheel，6 秒安装 |
| **推理** | `torch.bfloat16` + `flash_attention_2` | 半精度 + 高效注意力 |
| **后端** | FastAPI + Uvicorn | 异步高性能 Web 框架 |
| **前端** | 纯 HTML/CSS/JS | 零依赖，暗色主题，响应式 |
| **容器** | Docker + docker-compose | 一键部署，GPU 直通 |

### GPU 管理机制

这是一个值得展开说的设计。Qwen3-TTS 有 3 个模型（CustomVoice / VoiceDesign / Base），但通常只需要加载一个。我们实现了**智能 GPU 管理**：

```
用户请求 Custom Voice
    ↓
检查当前加载的模型
    ├── 已加载 CustomVoice → 直接使用（0 秒）
    ├── 已加载其他模型 → 卸载旧模型 → 加载新模型（~5 秒）
    └── 未加载任何模型 → 加载新模型（~5 秒）
    ↓
生成音频 → 返回结果
    ↓
空闲 10 分钟后 → 自动卸载，释放显存
```

- **最低显存需求**：6GB（一次只加载一个模型）
- **推荐显存**：8GB+
- **空闲超时**：默认 600 秒（可通过 `GPU_IDLE_TIMEOUT` 配置）
- **手动释放**：UI 上有 "🔻 Offload" 按钮，或调用 `POST /api/gpu-offload`

---

## 🌍 多语言 UI：4 种界面语言

UI 支持一键切换 4 种界面语言：

| 语言 | 切换方式 |
|------|----------|
| 🇺🇸 English | 右上角下拉选择 |
| 🇨🇳 简体中文 | 右上角下拉选择 |
| 🇹🇼 繁體中文 | 右上角下拉选择 |
| 🇯🇵 日本語 | 右上角下拉选择 |

所有按钮、标签、描述文字、状态提示都会跟随切换。i18n 数据在后端 Python 中定义，通过模板注入前端，无需额外请求。

---

## 🔧 配置参数

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `PORT` | `8766` | 服务端口 |
| `NVIDIA_VISIBLE_DEVICES` | `0` | GPU 设备编号 |
| `CUDA_DEVICE` | `cuda:0` | PyTorch 设备（容器内始终为 `cuda:0`） |
| `GPU_IDLE_TIMEOUT` | `600` | 空闲自动卸载时间（秒） |
| `QWEN_TTS_MODEL_DIR` | `/app/models` | 模型目录路径 |
| `HF_HUB_OFFLINE` | `1` | 禁用 HuggingFace 在线下载 |

---

## ⚠️ 坦诚说说不足之处

任何项目都有局限性，我们不回避：

### 1. 镜像体积大（~30GB）

4 个模型加起来 14GB，加上 PyTorch + CUDA 运行时，最终镜像约 30GB。首次 `docker pull` 需要一些耐心。但好处是**一次拉取，永久使用**，不会在运行时突然开始下载模型。

### 2. 不支持真正的流式输出

如前所述，这是模型层面的限制，不是我们能解决的。`/stream` 端点提供的是"分块传输"而非"增量生成"。

### 3. 不支持 CPU / Apple Silicon

当前 Docker 镜像基于 NVIDIA CUDA，**必须有 NVIDIA GPU**。如果你用的是 Mac 或没有 GPU 的机器，需要等待后续适配（或参考官方仓库的 CPU 模式）。

### 4. 单并发

当前架构是单模型单请求。如果有多个用户同时请求，会排队等待。对于生产级高并发场景，建议部署多个容器实例做负载均衡。

### 5. 生成速度

RTF 约 2x（生成 1 秒音频需要 2 秒计算），对于长文本来说等待时间较长。这是 1.7B 参数模型的固有特性，不是部署层面能优化的。

> 💡 **我们的原则**：把优点说清楚，也把不足说清楚。让你在部署前就知道会遇到什么。

---

## 🏗️ 想自己构建？完整指南

如果你不想用 Docker Hub 的预构建镜像，可以自己从源码构建：

```bash
# 1. 克隆项目
git clone https://github.com/neosun100/Qwen3-TTS.git
cd Qwen3-TTS

# 2. 下载模型（~14GB，需要一些时间）
pip install -U "huggingface_hub[cli]"
mkdir -p models
huggingface-cli download Qwen/Qwen3-TTS-Tokenizer-12Hz \
  --local-dir ./models/Qwen3-TTS-Tokenizer-12Hz
huggingface-cli download Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice \
  --local-dir ./models/Qwen3-TTS-12Hz-1.7B-CustomVoice
huggingface-cli download Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign \
  --local-dir ./models/Qwen3-TTS-12Hz-1.7B-VoiceDesign
huggingface-cli download Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --local-dir ./models/Qwen3-TTS-12Hz-1.7B-Base

# 3. 构建镜像（约 2 分钟，flash-attn 只需 6 秒）
docker build -t neosun/qwen3-tts:2.0.0 .

# 4. 启动
docker run -d --name qwen3-tts \
  --gpus '"device=0"' \
  -p 8766:8766 \
  neosun/qwen3-tts:2.0.0
```

> 📌 **注意**：模型文件不在 Git 仓库中（`.gitignore` 排除了 `models/` 目录），需要单独下载。这是因为 14GB 的模型不适合放在 Git 里。

---

## 📊 项目数据一览

| 指标 | 数值 |
|------|------|
| Docker 镜像大小 | ~30GB |
| 内嵌模型总大小 | ~14GB（4 个模型） |
| 后端代码 | 661 行 Python |
| 前端代码 | 769 行 HTML/CSS/JS |
| API 端点数 | 18 个 |
| 支持语言 | 10 种 |
| 预设说话人 | 9 位 |
| UI 界面语言 | 4 种 |
| flash-attn 安装时间 | 6 秒 |
| Docker 构建时间 | ~2 分钟 |
| 最低 GPU 显存 | 6GB |
| Python 版本 | 3.12 |
| PyTorch 版本 | 2.9.1 |
| CUDA 版本 | 12.8 |

---

## 🔮 下一步计划

- 🔄 **集成 vLLM-Omni 流式**：当 vLLM-Omni 的 TTS 流式支持成熟后，第一时间集成
- 🍎 **Apple Silicon 支持**：MPS 后端适配，让 Mac 用户也能用
- 📱 **移动端优化**：更好的触屏交互体验
- 🔊 **批量合成 API**：支持一次请求合成多段文本
- 📊 **性能基准测试**：不同 GPU 上的详细性能数据

---

## 📚 参考资料

1. [Qwen3-TTS-Docker GitHub](https://github.com/neosun100/Qwen3-TTS)
2. [Qwen3-TTS 官方仓库](https://github.com/QwenLM/Qwen3-TTS)
3. [Docker Hub 镜像](https://hub.docker.com/r/neosun/qwen3-tts)
4. [FlashAttention 官方 Releases](https://github.com/Dao-AILab/flash-attention/releases)
5. [Qwen3-TTS 论文](https://arxiv.org/abs/2601.15621)
6. [vLLM-Omni（流式推理）](https://github.com/vllm-project/vllm-omni)
7. [Qwen3-TTS 流式实验 Fork](https://github.com/dffdeeq/Qwen3-TTS-streaming)

---

💬 **互动时间**：

**你最想用 Qwen3-TTS 做什么？**
- 🎙️ 有声书 / 播客自动配音？
- 🎮 游戏角色语音生成？
- 🔊 克隆自己的声音做个性化助手？
- 🌍 跨语言内容本地化？

**欢迎在评论区留言讨论！**  
如果觉得有帮助，别忘了：
- 👍 点个"在看"
- 🔁 分享给需要 TTS 的朋友
- ⭐ 去 [GitHub](https://github.com/neosun100/Qwen3-TTS) 给个 Star 支持一下

---

![扫码_搜索联合传播样式-标准色版](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)

👆 **扫码关注【AI健自习室】**

🔥 每天分享AI干货、技术教程、实战案例  
🚀 第一时间获取一键部署系列更新通知

---

#### 引用链接

`[1]` Qwen3-TTS-Docker GitHub: *https://github.com/neosun100/Qwen3-TTS*  
`[2]` Qwen3-TTS 官方仓库: *https://github.com/QwenLM/Qwen3-TTS*  
`[3]` Docker Hub: *https://hub.docker.com/r/neosun/qwen3-tts*  
`[4]` FlashAttention Releases: *https://github.com/Dao-AILab/flash-attention/releases*  
`[5]` Qwen3-TTS 论文: *https://arxiv.org/abs/2601.15621*  
`[6]` vLLM-Omni: *https://github.com/vllm-project/vllm-omni*  
