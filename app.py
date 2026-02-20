import os, io, time, asyncio, logging, json
from typing import Optional, List
from contextlib import asynccontextmanager
from dataclasses import asdict

import torch
import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qwen3-tts")

PORT = int(os.getenv("PORT", 8766))
GPU_IDLE_TIMEOUT = int(os.getenv("GPU_IDLE_TIMEOUT", 600))
CUDA_DEVICE = os.getenv("CUDA_DEVICE", "cuda:0")
OUTPUT_DIR = "/tmp/qwen3-tts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SPEAKERS = ["Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ryan", "Aiden", "Ono_Anna", "Sohee"]
LANGUAGES = ["Auto", "Chinese", "English", "Japanese", "Korean", "German", "French", "Russian", "Portuguese", "Spanish", "Italian"]

_MODEL_DIR = os.getenv("QWEN_TTS_MODEL_DIR", "/app/models")
def _model_path(name):
    local = os.path.join(_MODEL_DIR, name)
    return local if os.path.isdir(local) else f"Qwen/{name}"

MODEL_MAP = {
    "custom_voice": _model_path("Qwen3-TTS-12Hz-1.7B-CustomVoice"),
    "voice_design": _model_path("Qwen3-TTS-12Hz-1.7B-VoiceDesign"),
    "voice_clone": _model_path("Qwen3-TTS-12Hz-1.7B-Base"),
}
TOKENIZER_PATH = _model_path("Qwen3-TTS-Tokenizer-12Hz")

SPEAKER_INFO = {
    "Vivian":   {"desc_en": "Bright, slightly edgy young female", "desc_zh": "明亮、略带锐利的年轻女声", "native": "Chinese", "gender": "Female"},
    "Serena":   {"desc_en": "Warm, gentle young female", "desc_zh": "温暖、柔和的年轻女声", "native": "Chinese", "gender": "Female"},
    "Uncle_Fu": {"desc_en": "Seasoned male, low mellow timbre", "desc_zh": "沉稳低沉的成熟男声", "native": "Chinese", "gender": "Male"},
    "Dylan":    {"desc_en": "Youthful Beijing male, clear natural", "desc_zh": "清朗自然的北京青年男声", "native": "Chinese (Beijing)", "gender": "Male"},
    "Eric":     {"desc_en": "Lively Chengdu male, slightly husky", "desc_zh": "活泼略带沙哑的成都男声", "native": "Chinese (Sichuan)", "gender": "Male"},
    "Ryan":     {"desc_en": "Dynamic male, strong rhythmic drive", "desc_zh": "动感十足、节奏感强的男声", "native": "English", "gender": "Male"},
    "Aiden":    {"desc_en": "Sunny American male, clear midrange", "desc_zh": "阳光美式男声、中频清晰", "native": "English", "gender": "Male"},
    "Ono_Anna": {"desc_en": "Playful Japanese female, light nimble", "desc_zh": "俏皮轻盈的日语女声", "native": "Japanese", "gender": "Female"},
    "Sohee":    {"desc_en": "Warm Korean female, rich emotion", "desc_zh": "温暖富有情感的韩语女声", "native": "Korean", "gender": "Female"},
}

SAMPLE_TEXTS = {
    "Chinese": "其实我真的有发现，我是一个特别善于观察别人情绪的人。",
    "English": "Then by the end of the movie, when Dorothy clicks her heels and says, there's no place like home, I got a little bit teary.",
    "Japanese": "やばい、明日のプレゼン資料まだ完成してない… 助けて！",
    "Korean": "야, 오늘 점심에 뭐 먹을지 생각해 봤어? 근처에 새로 생긴 분식집 어때?",
    "German": "Ich habe heute Morgen einen wunderschönen Sonnenaufgang gesehen.",
    "French": "La vie est belle quand on prend le temps de regarder autour de soi.",
    "Russian": "Сегодня прекрасный день для прогулки в парке.",
    "Portuguese": "A vida é uma jornada, não um destino.",
    "Spanish": "La música es el lenguaje universal de la humanidad.",
    "Italian": "La bellezza salverà il mondo, diceva Dostoevskij.",
}

INSTRUCT_EXAMPLES = {
    "en": ["Speak with a very sad and tearful voice", "Very happy and excited", "Speaking at an extremely slow pace",
           "Whisper softly", "Speak with authority and confidence", "In a playful, teasing tone"],
    "zh": ["用特别愤怒的语气说", "用特别伤心的语气说", "请特别小声的悄悄说", "用开心愉悦的语气",
           "语速很快地说", "用低沉的声音说"],
}

VOICE_DESIGN_EXAMPLES = [
    {"label": "🎀 Cute Loli (萝莉)", "instruct": "体现撒娇稚嫩的萝莉女声，音调偏高且起伏明显，营造出黏人、做作又刻意卖萌的听觉效果。",
     "text": "哥哥，你回来啦，人家等了你好久好久了，要抱抱！", "lang": "Chinese"},
    {"label": "🎭 Sarcastic Teen", "instruct": "Speak as a sarcastic, assertive teenage girl: crisp enunciation, controlled volume, with vocal emphasis that conveys disdain.",
     "text": "Blah, blah, blah. We're all very fascinated, but we'd like to get paid.", "lang": "English"},
    {"label": "👑 Imperial Drama (宫廷)", "instruct": "展现出悲苦沙哑的声音质感,语速偏慢,情绪浓烈且带有哭腔,以标准普通话缓慢诉说,情感强烈,语调哀怨高亢。",
     "text": "皇上啊！臣妾一片真心可昭日月，为何您竟信那毒妇谗言，将我打入冷宫？", "lang": "Chinese"},
    {"label": "🎙️ Announcer", "instruct": "A bright, agile male voice with a natural upward lift, delivering lines at a brisk, energetic pace. Pitch leans high, volume projects clearly.",
     "text": "Coming up next, the moment you've all been waiting for! Stay tuned, we'll be right back after this break!", "lang": "English"},
    {"label": "😢 Sad Narrator (悲伤)", "instruct": "以极度悲伤、带着明显哭腔的语气，用较小的音量缓缓诉说，语速缓慢，声音颤抖而压抑。",
     "text": "有些事，只要国家需要，就得有人扛起来。我们那一代人，是背着泥土铺路的。", "lang": "Chinese"},
    {"label": "🗣️ Confident Male", "instruct": "gender: Male. pitch: Low. speed: Deliberate pace. volume: Loud. emotion: Commanding. tone: Authoritative. personality: Confident.",
     "text": "Older gentleman, 110, maybe 111 years old, sort of a surly Elvis thing happening with him.", "lang": "English"},
]


# ── i18n ──
I18N = {
    "en": {
        "title": "🗣️ Qwen3-TTS", "subtitle": "All-in-One Text-to-Speech: Custom Voice · Voice Design · Voice Clone",
        "custom_voice": "🎤 Custom Voice", "voice_design": "🎨 Voice Design", "voice_clone": "🔊 Voice Clone",
        "text": "Text to synthesize", "lang": "Language", "speaker": "Speaker", "instruct": "Instruction (optional)",
        "ref_audio": "Reference Audio (3s+ recommended)", "ref_text": "Reference Text (transcript of ref audio)",
        "generate": "🎵 Generate", "advanced": "⚙️ Advanced Settings", "gpu_status": "GPU Status",
        "offload": "🔻 Offload GPU", "refresh": "🔄 Refresh", "xvec": "X-Vector Only (no ref text needed, lower quality)",
        "status": "Status", "output": "Output Audio", "save_voice": "💾 Save Voice Prompt",
        "load_voice": "📂 Load Voice Prompt", "voice_file": "Voice Prompt File (.pt)",
        "desc_cv": "Generate speech with 9 preset premium voices. Add instructions to control emotion, speed, tone, and style.",
        "desc_vd": "Design a completely new voice by describing its characteristics. Supports acoustic attributes, persona, age, emotion control.",
        "desc_vc": "Clone any voice from a 3-second audio clip. Supports cross-lingual cloning across 10 languages.",
        "sample_text": "📝 Sample Text", "instruct_examples": "💡 Instruction Examples",
        "design_presets": "🎭 Design Presets", "speaker_info": "Speaker Info",
        "disclaimer": "⚠️ AI-generated audio for demo purposes only. Not for impersonation or illegal use.",
    },
    "zh-CN": {
        "title": "🗣️ Qwen3-TTS 语音合成", "subtitle": "一站式语音合成：自定义语音 · 语音设计 · 语音克隆",
        "custom_voice": "🎤 自定义语音", "voice_design": "🎨 语音设计", "voice_clone": "🔊 语音克隆",
        "text": "合成文本", "lang": "语言", "speaker": "说话人", "instruct": "指令（可选）",
        "ref_audio": "参考音频（建议3秒以上）", "ref_text": "参考文本（参考音频的文字内容）",
        "generate": "🎵 生成", "advanced": "⚙️ 高级设置", "gpu_status": "GPU 状态",
        "offload": "🔻 释放显存", "refresh": "🔄 刷新", "xvec": "仅声纹模式（无需参考文本，质量较低）",
        "status": "状态", "output": "输出音频", "save_voice": "💾 保存音色", "load_voice": "📂 加载音色",
        "voice_file": "音色文件 (.pt)",
        "desc_cv": "使用9种预设高品质声音生成语音。可添加指令控制情感、语速、语调和风格。",
        "desc_vd": "用自然语言描述声音特征来设计全新声音。支持声学属性、人设、年龄、情感控制。",
        "desc_vc": "从3秒音频片段克隆任意声音。支持10种语言的跨语言克隆。",
        "sample_text": "📝 示例文本", "instruct_examples": "💡 指令示例",
        "design_presets": "🎭 设计预设", "speaker_info": "说话人信息",
        "disclaimer": "⚠️ AI生成音频仅供演示，禁止用于冒充他人或非法用途。",
    },
    "zh-TW": {
        "title": "🗣️ Qwen3-TTS 語音合成", "subtitle": "一站式語音合成：自訂語音 · 語音設計 · 語音複製",
        "custom_voice": "🎤 自訂語音", "voice_design": "🎨 語音設計", "voice_clone": "🔊 語音複製",
        "text": "合成文字", "lang": "語言", "speaker": "說話人", "instruct": "指令（選填）",
        "ref_audio": "參考音訊（建議3秒以上）", "ref_text": "參考文字（參考音訊的文字內容）",
        "generate": "🎵 生成", "advanced": "⚙️ 進階設定", "gpu_status": "GPU 狀態",
        "offload": "🔻 釋放顯存", "refresh": "🔄 重新整理", "xvec": "僅聲紋模式（無需參考文字，品質較低）",
        "status": "狀態", "output": "輸出音訊", "save_voice": "💾 儲存音色", "load_voice": "📂 載入音色",
        "voice_file": "音色檔案 (.pt)",
        "desc_cv": "使用9種預設高品質聲音生成語音。可添加指令控制情感、語速、語調和風格。",
        "desc_vd": "用自然語言描述聲音特徵來設計全新聲音。支援聲學屬性、人設、年齡、情感控制。",
        "desc_vc": "從3秒音訊片段複製任意聲音。支援10種語言的跨語言複製。",
        "sample_text": "📝 範例文字", "instruct_examples": "💡 指令範例",
        "design_presets": "🎭 設計預設", "speaker_info": "說話人資訊",
        "disclaimer": "⚠️ AI生成音訊僅供演示，禁止用於冒充他人或非法用途。",
    },
    "ja": {
        "title": "🗣️ Qwen3-TTS 音声合成", "subtitle": "オールインワン音声合成：カスタム音声・音声デザイン・音声クローン",
        "custom_voice": "🎤 カスタム音声", "voice_design": "🎨 音声デザイン", "voice_clone": "🔊 音声クローン",
        "text": "合成テキスト", "lang": "言語", "speaker": "話者", "instruct": "指示（任意）",
        "ref_audio": "参照音声（3秒以上推奨）", "ref_text": "参照テキスト（参照音声の書き起こし）",
        "generate": "🎵 生成", "advanced": "⚙️ 詳細設定", "gpu_status": "GPU状態",
        "offload": "🔻 GPUオフロード", "refresh": "🔄 更新", "xvec": "X-Vectorのみ（参照テキスト不要、品質低下）",
        "status": "ステータス", "output": "出力音声", "save_voice": "💾 音色保存", "load_voice": "📂 音色読込",
        "voice_file": "音色ファイル (.pt)",
        "desc_cv": "9種のプリセット音声で音声生成。指示で感情・速度・トーン・スタイルを制御。",
        "desc_vd": "自然言語で音声特性を記述して新しい音声をデザイン。音響属性・ペルソナ・年齢・感情制御対応。",
        "desc_vc": "3秒の音声クリップから音声をクローン。10言語の多言語クローン対応。",
        "sample_text": "📝 サンプルテキスト", "instruct_examples": "💡 指示例",
        "design_presets": "🎭 デザインプリセット", "speaker_info": "話者情報",
        "disclaimer": "⚠️ AI生成音声はデモ目的のみ。なりすましや違法使用は禁止。",
    },
}


# ── GPU Manager ──
class GPUManager:
    def __init__(self):
        self.model = None
        self.model_type = None
        self.tokenizer = None
        self.last_use = 0.0
        self._lock = asyncio.Lock()
        self._task = None

    async def start(self):
        self._task = asyncio.create_task(self._idle_loop())

    async def stop(self):
        if self._task:
            self._task.cancel()

    async def _idle_loop(self):
        while True:
            await asyncio.sleep(30)
            async with self._lock:
                if self.model and time.time() - self.last_use > GPU_IDLE_TIMEOUT:
                    logger.info("Auto-offloading model (idle timeout)")
                    self._unload()

    def _unload(self):
        if self.model:
            del self.model
            self.model = None
            self.model_type = None
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
        torch.cuda.empty_cache()

    async def load(self, model_type: str):
        async with self._lock:
            self.last_use = time.time()
            if self.model and self.model_type == model_type:
                return self.model
            self._unload()
            name = MODEL_MAP[model_type]
            logger.info(f"Loading model: {name}")
            from qwen_tts import Qwen3TTSModel
            self.model = Qwen3TTSModel.from_pretrained(
                name, device_map=CUDA_DEVICE,
                dtype=torch.bfloat16, attn_implementation="flash_attention_2",
            )
            self.model_type = model_type
            logger.info("Model loaded")
            return self.model

    async def load_tokenizer(self):
        async with self._lock:
            self.last_use = time.time()
            if self.tokenizer:
                return self.tokenizer
            from qwen_tts import Qwen3TTSTokenizer
            logger.info(f"Loading tokenizer: {TOKENIZER_PATH}")
            self.tokenizer = Qwen3TTSTokenizer.from_pretrained(TOKENIZER_PATH, device_map=CUDA_DEVICE)
            return self.tokenizer

    async def offload(self):
        async with self._lock:
            self._unload()

    async def status(self):
        gpu_info = {}
        try:
            if torch.cuda.is_available():
                idx = int(CUDA_DEVICE.split(":")[-1]) if ":" in CUDA_DEVICE else 0
                gpu_info = {
                    "gpu_name": torch.cuda.get_device_name(idx),
                    "memory_allocated_mb": round(torch.cuda.memory_allocated(idx) / 1048576),
                    "memory_reserved_mb": round(torch.cuda.memory_reserved(idx) / 1048576),
                }
        except Exception:
            pass
        return {
            "loaded": self.model is not None,
            "model_type": self.model_type,
            "model_name": MODEL_MAP.get(self.model_type, ""),
            "idle_seconds": round(time.time() - self.last_use, 1) if self.last_use else None,
            **gpu_info,
        }


gpu = GPUManager()


# ── Helpers ──
def wav_bytes(audio: np.ndarray, sr: int) -> bytes:
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    buf.seek(0)
    return buf.getvalue()


def gen_kwargs(do_sample=True, top_k=50, top_p=0.9, temperature=1.0, repetition_penalty=1.05,
               max_new_tokens=2048, subtalker_top_k=50, subtalker_top_p=0.9, subtalker_temperature=1.0):
    return dict(do_sample=do_sample, top_k=top_k, top_p=top_p, temperature=temperature,
                repetition_penalty=repetition_penalty, max_new_tokens=max_new_tokens,
                subtalker_top_k=subtalker_top_k, subtalker_top_p=subtalker_top_p,
                subtalker_temperature=subtalker_temperature)


def normalize_audio(wav):
    x = np.asarray(wav, dtype=np.float32)
    if x.ndim > 1:
        x = np.mean(x, axis=-1)
    m = np.max(np.abs(x)) if x.size else 0.0
    if m > 1.0 + 1e-6:
        x = x / (m + 1e-12)
    return np.clip(x, -1.0, 1.0).astype(np.float32)


def timed_wav_response(audio, sr, t_load, t_gen, filename="output.wav"):
    """Return WAV StreamingResponse with timing headers."""
    audio_dur = len(audio) / sr
    return StreamingResponse(
        io.BytesIO(wav_bytes(audio, sr)), media_type="audio/wav",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Time-Load": f"{t_load:.3f}", "X-Time-Gen": f"{t_gen:.3f}",
            "X-Time-Total": f"{t_load + t_gen:.3f}", "X-Audio-Duration": f"{audio_dur:.3f}",
        })


# ── FastAPI ──
@asynccontextmanager
async def lifespan(_app):
    await gpu.start()
    yield
    await gpu.stop()

app = FastAPI(title="Qwen3-TTS API", version="2.0.0",
              description="All-in-One TTS: Custom Voice / Voice Design / Voice Clone / Tokenizer", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
                   expose_headers=["X-Time-Load","X-Time-Gen","X-Time-Total","X-Audio-Duration",
                                   "X-Sample-Rate","X-Audio-Format","X-Audio-Channels"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "qwen3-tts", "version": "2.0.0"}


@app.get("/api/gpu-status")
async def api_gpu_status():
    return await gpu.status()


@app.post("/api/gpu-offload")
async def api_gpu_offload():
    await gpu.offload()
    return {"message": "GPU offloaded"}


@app.get("/api/speakers")
async def api_speakers():
    return {"speakers": SPEAKERS, "details": SPEAKER_INFO}


@app.get("/api/languages")
async def api_languages():
    return {"languages": LANGUAGES}


@app.get("/api/models")
async def api_models():
    return {"models": MODEL_MAP, "current": gpu.model_type}


@app.get("/api/sample-texts")
async def api_sample_texts():
    return SAMPLE_TEXTS


class CustomVoiceReq(BaseModel):
    text: str
    language: str = "Auto"
    speaker: str = "Vivian"
    instruct: str = ""
    do_sample: bool = True
    top_k: int = 50
    top_p: float = 0.9
    temperature: float = 1.0
    repetition_penalty: float = 1.05
    max_new_tokens: int = 2048
    subtalker_top_k: int = 50
    subtalker_top_p: float = 0.9
    subtalker_temperature: float = 1.0


class VoiceDesignReq(BaseModel):
    text: str
    language: str = "Auto"
    instruct: str = ""
    do_sample: bool = True
    top_k: int = 50
    top_p: float = 0.9
    temperature: float = 1.0
    repetition_penalty: float = 1.05
    max_new_tokens: int = 2048
    subtalker_top_k: int = 50
    subtalker_top_p: float = 0.9
    subtalker_temperature: float = 1.0


@app.post("/api/tts/custom-voice")
async def api_custom_voice(req: CustomVoiceReq):
    try:
        t0 = time.time()
        model = await gpu.load("custom_voice")
        t_load = time.time() - t0
        t1 = time.time()
        wavs, sr = model.generate_custom_voice(
            text=req.text, language=req.language, speaker=req.speaker, instruct=req.instruct or None,
            **gen_kwargs(req.do_sample, req.top_k, req.top_p, req.temperature,
                         req.repetition_penalty, req.max_new_tokens, req.subtalker_top_k,
                         req.subtalker_top_p, req.subtalker_temperature))
        t_gen = time.time() - t1
        return timed_wav_response(wavs[0], sr, t_load, t_gen, f"cv_{req.speaker}_{req.language}.wav")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("custom-voice error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts/voice-design")
async def api_voice_design(req: VoiceDesignReq):
    try:
        t0 = time.time()
        model = await gpu.load("voice_design")
        t_load = time.time() - t0
        t1 = time.time()
        wavs, sr = model.generate_voice_design(
            text=req.text, language=req.language, instruct=req.instruct,
            **gen_kwargs(req.do_sample, req.top_k, req.top_p, req.temperature,
                         req.repetition_penalty, req.max_new_tokens, req.subtalker_top_k,
                         req.subtalker_top_p, req.subtalker_temperature))
        t_gen = time.time() - t1
        return timed_wav_response(wavs[0], sr, t_load, t_gen, f"vd_{req.language}.wav")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("voice-design error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts/voice-clone")
async def api_voice_clone(
    text: str = Form(...), language: str = Form("Auto"), ref_text: str = Form(""),
    x_vector_only_mode: bool = Form(False), do_sample: bool = Form(True),
    top_k: int = Form(50), top_p: float = Form(0.9), temperature: float = Form(1.0),
    repetition_penalty: float = Form(1.05), max_new_tokens: int = Form(2048),
    subtalker_top_k: int = Form(50), subtalker_top_p: float = Form(0.9),
    subtalker_temperature: float = Form(1.0), ref_audio: UploadFile = File(...),
):
    try:
        content = await ref_audio.read()
        audio_np, audio_sr = sf.read(io.BytesIO(content), dtype="float32")
        audio_np = normalize_audio(audio_np)
        t0 = time.time()
        model = await gpu.load("voice_clone")
        t_load = time.time() - t0
        t1 = time.time()
        wavs, sr = model.generate_voice_clone(
            text=text, language=language, ref_audio=(audio_np, audio_sr),
            ref_text=ref_text or None, x_vector_only_mode=x_vector_only_mode,
            **gen_kwargs(do_sample, top_k, top_p, temperature, repetition_penalty,
                         max_new_tokens, subtalker_top_k, subtalker_top_p, subtalker_temperature))
        t_gen = time.time() - t1
        return timed_wav_response(wavs[0], sr, t_load, t_gen, "vc_clone.wav")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("voice-clone error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice-prompt/save")
async def api_save_voice_prompt(
    ref_text: str = Form(""), x_vector_only_mode: bool = Form(False),
    ref_audio: UploadFile = File(...),
):
    """Save a reusable voice clone prompt from reference audio."""
    try:
        content = await ref_audio.read()
        audio_np, audio_sr = sf.read(io.BytesIO(content), dtype="float32")
        audio_np = normalize_audio(audio_np)
        model = await gpu.load("voice_clone")
        items = model.create_voice_clone_prompt(
            ref_audio=(audio_np, audio_sr),
            ref_text=ref_text.strip() or None,
            x_vector_only_mode=x_vector_only_mode,
        )
        payload = {"items": [asdict(it) for it in items]}
        ts = time.strftime("%Y%m%d_%H%M%S")
        buf = io.BytesIO()
        torch.save(payload, buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/octet-stream",
                                 headers={"Content-Disposition": f"attachment; filename=voice_prompt_{ts}.pt"})
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("save-voice-prompt error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts/voice-clone-from-prompt")
async def api_voice_clone_from_prompt(
    text: str = Form(...), language: str = Form("Auto"),
    do_sample: bool = Form(True), top_k: int = Form(50), top_p: float = Form(0.9),
    temperature: float = Form(1.0), repetition_penalty: float = Form(1.05),
    max_new_tokens: int = Form(2048), subtalker_top_k: int = Form(50),
    subtalker_top_p: float = Form(0.9), subtalker_temperature: float = Form(1.0),
    voice_prompt: UploadFile = File(...),
):
    """Generate speech using a previously saved voice prompt file."""
    try:
        from qwen_tts import VoiceClonePromptItem
        content = await voice_prompt.read()
        payload = torch.load(io.BytesIO(content), map_location="cpu", weights_only=True)
        items = []
        for d in payload["items"]:
            ref_code = d.get("ref_code")
            if ref_code is not None and not torch.is_tensor(ref_code):
                ref_code = torch.tensor(ref_code)
            ref_spk = d["ref_spk_embedding"]
            if not torch.is_tensor(ref_spk):
                ref_spk = torch.tensor(ref_spk)
            items.append(VoiceClonePromptItem(
                ref_code=ref_code, ref_spk_embedding=ref_spk,
                x_vector_only_mode=bool(d.get("x_vector_only_mode", False)),
                icl_mode=bool(d.get("icl_mode", True)),
                ref_text=d.get("ref_text"),
            ))
        t0 = time.time()
        model = await gpu.load("voice_clone")
        t_load = time.time() - t0
        t1 = time.time()
        wavs, sr = model.generate_voice_clone(
            text=text, language=language, voice_clone_prompt=items,
            **gen_kwargs(do_sample, top_k, top_p, temperature, repetition_penalty,
                         max_new_tokens, subtalker_top_k, subtalker_top_p, subtalker_temperature))
        t_gen = time.time() - t1
        return timed_wav_response(wavs[0], sr, t_load, t_gen, "vc_from_prompt.wav")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("voice-clone-from-prompt error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tokenizer/encode")
async def api_tokenizer_encode(ref_audio: UploadFile = File(...)):
    """Encode audio to speech tokens using Qwen3-TTS-Tokenizer-12Hz."""
    try:
        content = await ref_audio.read()
        audio_np, audio_sr = sf.read(io.BytesIO(content), dtype="float32")
        audio_np = normalize_audio(audio_np)
        tokenizer = await gpu.load_tokenizer()
        enc = tokenizer.encode(audio_np, sr=audio_sr)
        codes = enc.audio_codes[0].cpu().tolist()
        return {"codes": codes, "num_frames": len(codes)}
    except Exception as e:
        logger.exception("tokenizer-encode error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tokenizer/decode")
async def api_tokenizer_decode(codes: List[List[int]]):
    """Decode speech tokens back to audio."""
    try:
        tokenizer = await gpu.load_tokenizer()
        code_tensor = torch.tensor(codes).unsqueeze(0)
        wavs, sr = tokenizer.decode({"audio_codes": code_tensor})
        audio_dur = len(wavs[0]) / sr
        return StreamingResponse(
            io.BytesIO(wav_bytes(wavs[0], sr)), media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=decoded.wav",
                     "X-Audio-Duration": f"{audio_dur:.3f}"})
    except Exception as e:
        logger.exception("tokenizer-decode error")
        raise HTTPException(status_code=500, detail=str(e))


# ── Streaming TTS endpoints (PCM raw audio) ──
def _pcm_stream(audio: np.ndarray, sr: int, chunk_duration: float = 0.25):
    """Yield raw PCM s16le chunks for transfer-chunked playback."""
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
    chunk_bytes = int(sr * chunk_duration) * 2
    for i in range(0, len(pcm), chunk_bytes):
        yield pcm[i:i + chunk_bytes]


@app.post("/api/tts/custom-voice/stream")
async def api_custom_voice_stream(req: CustomVoiceReq):
    """Streaming custom voice TTS — returns raw PCM s16le audio chunks."""
    try:
        model = await gpu.load("custom_voice")
        wavs, sr = model.generate_custom_voice(
            text=req.text, language=req.language, speaker=req.speaker,
            instruct=req.instruct or None,
            **gen_kwargs(req.do_sample, req.top_k, req.top_p, req.temperature,
                         req.repetition_penalty, req.max_new_tokens, req.subtalker_top_k,
                         req.subtalker_top_p, req.subtalker_temperature))
        return StreamingResponse(
            _pcm_stream(wavs[0], sr),
            media_type=f"audio/pcm;rate={sr};encoding=signed-int;bits=16",
            headers={"X-Sample-Rate": str(sr), "X-Audio-Format": "pcm_s16le", "X-Audio-Channels": "1"})
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("custom-voice-stream error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts/voice-design/stream")
async def api_voice_design_stream(req: VoiceDesignReq):
    """Streaming voice design TTS — returns raw PCM s16le audio chunks."""
    try:
        model = await gpu.load("voice_design")
        wavs, sr = model.generate_voice_design(
            text=req.text, language=req.language, instruct=req.instruct,
            **gen_kwargs(req.do_sample, req.top_k, req.top_p, req.temperature,
                         req.repetition_penalty, req.max_new_tokens, req.subtalker_top_k,
                         req.subtalker_top_p, req.subtalker_temperature))
        return StreamingResponse(
            _pcm_stream(wavs[0], sr),
            media_type=f"audio/pcm;rate={sr};encoding=signed-int;bits=16",
            headers={"X-Sample-Rate": str(sr), "X-Audio-Format": "pcm_s16le", "X-Audio-Channels": "1"})
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("voice-design-stream error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts/voice-clone/stream")
async def api_voice_clone_stream(
    text: str = Form(...), language: str = Form("Auto"), ref_text: str = Form(""),
    x_vector_only_mode: bool = Form(False), do_sample: bool = Form(True),
    top_k: int = Form(50), top_p: float = Form(0.9), temperature: float = Form(1.0),
    repetition_penalty: float = Form(1.05), max_new_tokens: int = Form(2048),
    subtalker_top_k: int = Form(50), subtalker_top_p: float = Form(0.9),
    subtalker_temperature: float = Form(1.0), ref_audio: UploadFile = File(...),
):
    """Streaming voice clone TTS — returns raw PCM s16le audio chunks."""
    try:
        content = await ref_audio.read()
        audio_np, audio_sr = sf.read(io.BytesIO(content), dtype="float32")
        audio_np = normalize_audio(audio_np)
        model = await gpu.load("voice_clone")
        wavs, sr = model.generate_voice_clone(
            text=text, language=language, ref_audio=(audio_np, audio_sr),
            ref_text=ref_text or None, x_vector_only_mode=x_vector_only_mode,
            **gen_kwargs(do_sample, top_k, top_p, temperature, repetition_penalty,
                         max_new_tokens, subtalker_top_k, subtalker_top_p, subtalker_temperature))
        return StreamingResponse(
            _pcm_stream(wavs[0], sr),
            media_type=f"audio/pcm;rate={sr};encoding=signed-int;bits=16",
            headers={"X-Sample-Rate": str(sr), "X-Audio-Format": "pcm_s16le", "X-Audio-Channels": "1"})
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("voice-clone-stream error")
        raise HTTPException(status_code=500, detail=str(e))


# ── HTML UI ──
_UI_TEMPLATE = None

def _get_ui_html():
    global _UI_TEMPLATE
    if _UI_TEMPLATE is None:
        import pathlib
        tmpl_path = pathlib.Path(__file__).parent / "ui.html"
        raw = tmpl_path.read_text(encoding="utf-8")
        replacements = {
            "{{SPEAKERS_JSON}}": json.dumps(SPEAKERS),
            "{{LANGUAGES_JSON}}": json.dumps(LANGUAGES),
            "{{SPEAKER_INFO_JSON}}": json.dumps(SPEAKER_INFO, ensure_ascii=False),
            "{{SAMPLE_TEXTS_JSON}}": json.dumps(SAMPLE_TEXTS, ensure_ascii=False),
            "{{INSTRUCT_EXAMPLES_JSON}}": json.dumps(INSTRUCT_EXAMPLES, ensure_ascii=False),
            "{{VOICE_DESIGN_EXAMPLES_JSON}}": json.dumps(VOICE_DESIGN_EXAMPLES, ensure_ascii=False),
            "{{I18N_JSON}}": json.dumps(I18N, ensure_ascii=False),
        }
        for k, v in replacements.items():
            raw = raw.replace(k, v)
        _UI_TEMPLATE = raw
    return _UI_TEMPLATE


@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
async def ui_page():
    return HTMLResponse(_get_ui_html())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=PORT)
