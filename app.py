import os, io, time, asyncio, logging, base64
from typing import Optional
from contextlib import asynccontextmanager

import torch
import numpy as np
import soundfile as sf
import gradio as gr
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qwen3-tts")

PORT = int(os.getenv("PORT", 8766))
GPU_IDLE_TIMEOUT = int(os.getenv("GPU_IDLE_TIMEOUT", 600))
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
CUDA_DEVICE = os.getenv("CUDA_DEVICE", "cuda:0")

SPEAKERS = ["Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ryan", "Aiden", "Ono_Anna", "Sohee"]
LANGUAGES = ["Auto", "Chinese", "English", "Japanese", "Korean", "German", "French", "Russian", "Portuguese", "Spanish", "Italian"]
MODEL_MAP = {
    "custom_voice": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    "voice_design": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    "voice_clone": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
}

I18N = {
    "en": {"title": "🗣️ Qwen3-TTS", "custom_voice": "Custom Voice", "voice_design": "Voice Design",
           "voice_clone": "Voice Clone", "text": "Text to synthesize", "lang": "Language", "speaker": "Speaker",
           "instruct": "Instruction (optional)", "ref_audio": "Reference Audio", "ref_text": "Reference Text",
           "generate": "🎵 Generate", "advanced": "⚙️ Advanced Settings", "gpu_status": "GPU Status",
           "offload": "🔻 Offload GPU", "refresh": "🔄 Refresh", "xvec": "X-Vector Only Mode",
           "desc_cv": "Generate speech with preset voices. Optionally add instructions to control emotion/style.",
           "desc_vd": "Design a new voice by describing its characteristics in natural language.",
           "desc_vc": "Clone a voice from a reference audio clip and synthesize new content."},
    "zh-CN": {"title": "🗣️ Qwen3-TTS 语音合成", "custom_voice": "自定义语音", "voice_design": "语音设计",
              "voice_clone": "语音克隆", "text": "合成文本", "lang": "语言", "speaker": "说话人",
              "instruct": "指令（可选）", "ref_audio": "参考音频", "ref_text": "参考文本",
              "generate": "🎵 生成", "advanced": "⚙️ 高级设置", "gpu_status": "GPU 状态",
              "offload": "🔻 释放显存", "refresh": "🔄 刷新", "xvec": "仅使用声纹向量",
              "desc_cv": "使用预设声音生成语音，可添加指令控制情感/风格。",
              "desc_vd": "用自然语言描述声音特征来设计新声音。",
              "desc_vc": "从参考音频克隆声音并合成新内容。"},
    "zh-TW": {"title": "🗣️ Qwen3-TTS 語音合成", "custom_voice": "自訂語音", "voice_design": "語音設計",
              "voice_clone": "語音複製", "text": "合成文字", "lang": "語言", "speaker": "說話人",
              "instruct": "指令（選填）", "ref_audio": "參考音訊", "ref_text": "參考文字",
              "generate": "🎵 生成", "advanced": "⚙️ 進階設定", "gpu_status": "GPU 狀態",
              "offload": "🔻 釋放顯存", "refresh": "🔄 重新整理", "xvec": "僅使用聲紋向量",
              "desc_cv": "使用預設聲音生成語音，可添加指令控制情感/風格。",
              "desc_vd": "用自然語言描述聲音特徵來設計新聲音。",
              "desc_vc": "從參考音訊複製聲音並合成新內容。"},
    "ja": {"title": "🗣️ Qwen3-TTS 音声合成", "custom_voice": "カスタム音声", "voice_design": "音声デザイン",
           "voice_clone": "音声クローン", "text": "合成テキスト", "lang": "言語", "speaker": "話者",
           "instruct": "指示（任意）", "ref_audio": "参照音声", "ref_text": "参照テキスト",
           "generate": "🎵 生成", "advanced": "⚙️ 詳細設定", "gpu_status": "GPU状態",
           "offload": "🔻 GPUオフロード", "refresh": "🔄 更新", "xvec": "X-Vectorのみ",
           "desc_cv": "プリセット音声で音声を生成。指示で感情/スタイルを制御可能。",
           "desc_vd": "自然言語で音声特性を記述して新しい音声をデザイン。",
           "desc_vc": "参照音声から音声をクローンし、新しいコンテンツを合成。"},
}


class GPUManager:
    def __init__(self):
        self.model = None
        self.model_type = None
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
            torch.cuda.empty_cache()

    async def load(self, model_type: str):
        async with self._lock:
            self.last_use = time.time()
            if self.model and self.model_type == model_type:
                return self.model
            self._unload()
            logger.info(f"Loading model: {MODEL_MAP[model_type]}")
            from qwen_tts import Qwen3TTSModel
            self.model = Qwen3TTSModel.from_pretrained(
                MODEL_MAP[model_type], device_map=CUDA_DEVICE,
                dtype=torch.bfloat16, attn_implementation="flash_attention_2",
            )
            self.model_type = model_type
            logger.info("Model loaded")
            return self.model

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
            "idle_seconds": round(time.time() - self.last_use, 1) if self.last_use else None,
            **gpu_info,
        }


gpu = GPUManager()


def wav_bytes(audio: np.ndarray, sr: int) -> bytes:
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    buf.seek(0)
    return buf.getvalue()


def wav_response(audio: np.ndarray, sr: int):
    return StreamingResponse(io.BytesIO(wav_bytes(audio, sr)), media_type="audio/wav",
                             headers={"Content-Disposition": "attachment; filename=output.wav"})


def gen_kwargs(do_sample=True, top_k=50, top_p=0.9, temperature=1.0, repetition_penalty=1.05,
               max_new_tokens=2048, subtalker_top_k=50, subtalker_top_p=0.9, subtalker_temperature=1.0):
    return dict(do_sample=do_sample, top_k=top_k, top_p=top_p, temperature=temperature,
                repetition_penalty=repetition_penalty, max_new_tokens=max_new_tokens,
                subtalker_top_k=subtalker_top_k, subtalker_top_p=subtalker_top_p,
                subtalker_temperature=subtalker_temperature)


# --- FastAPI ---
@asynccontextmanager
async def lifespan(_app):
    await gpu.start()
    yield
    await gpu.stop()

app = FastAPI(title="Qwen3-TTS API", version="1.0.0",
              description="Text-to-Speech: Custom Voice / Voice Design / Voice Clone", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "qwen3-tts"}


@app.get("/api/gpu-status")
async def api_gpu_status():
    return await gpu.status()


@app.post("/api/gpu-offload")
async def api_gpu_offload():
    await gpu.offload()
    return {"message": "GPU offloaded"}


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
    model = await gpu.load("custom_voice")
    wavs, sr = model.generate_custom_voice(
        text=req.text, language=req.language, speaker=req.speaker, instruct=req.instruct or None,
        **gen_kwargs(req.do_sample, req.top_k, req.top_p, req.temperature,
                     req.repetition_penalty, req.max_new_tokens, req.subtalker_top_k,
                     req.subtalker_top_p, req.subtalker_temperature))
    return wav_response(wavs[0], sr)


@app.post("/api/tts/voice-design")
async def api_voice_design(req: VoiceDesignReq):
    model = await gpu.load("voice_design")
    wavs, sr = model.generate_voice_design(
        text=req.text, language=req.language, instruct=req.instruct,
        **gen_kwargs(req.do_sample, req.top_k, req.top_p, req.temperature,
                     req.repetition_penalty, req.max_new_tokens, req.subtalker_top_k,
                     req.subtalker_top_p, req.subtalker_temperature))
    return wav_response(wavs[0], sr)


@app.post("/api/tts/voice-clone")
async def api_voice_clone(
    text: str = Form(...), language: str = Form("Auto"), ref_text: str = Form(""),
    x_vector_only_mode: bool = Form(False), do_sample: bool = Form(True),
    top_k: int = Form(50), top_p: float = Form(0.9), temperature: float = Form(1.0),
    repetition_penalty: float = Form(1.05), max_new_tokens: int = Form(2048),
    subtalker_top_k: int = Form(50), subtalker_top_p: float = Form(0.9),
    subtalker_temperature: float = Form(1.0), ref_audio: UploadFile = File(...),
):
    content = await ref_audio.read()
    audio_np, audio_sr = sf.read(io.BytesIO(content), dtype="float32")
    if audio_np.ndim > 1:
        audio_np = np.mean(audio_np, axis=-1)
    model = await gpu.load("voice_clone")
    wavs, sr = model.generate_voice_clone(
        text=text, language=language, ref_audio=(audio_np.astype(np.float32), audio_sr),
        ref_text=ref_text or None, x_vector_only_mode=x_vector_only_mode,
        **gen_kwargs(do_sample, top_k, top_p, temperature, repetition_penalty,
                     max_new_tokens, subtalker_top_k, subtalker_top_p, subtalker_temperature))
    return wav_response(wavs[0], sr)


@app.get("/api/speakers")
async def api_speakers():
    return {"speakers": SPEAKERS}


@app.get("/api/languages")
async def api_languages():
    return {"languages": LANGUAGES}


# --- Gradio UI ---
def build_ui():
    def t(key, lang="en"):
        return I18N.get(lang, I18N["en"]).get(key, key)

    def _adv():
        do_sample = gr.Checkbox(value=True, label="do_sample")
        top_k = gr.Slider(1, 200, 50, step=1, label="top_k")
        top_p = gr.Slider(0.0, 1.0, 0.9, step=0.05, label="top_p")
        temp = gr.Slider(0.1, 2.0, 1.0, step=0.05, label="temperature")
        rep = gr.Slider(1.0, 2.0, 1.05, step=0.05, label="repetition_penalty")
        mnt = gr.Slider(256, 4096, 2048, step=128, label="max_new_tokens")
        stk = gr.Slider(1, 200, 50, step=1, label="subtalker_top_k")
        stp = gr.Slider(0.0, 1.0, 0.9, step=0.05, label="subtalker_top_p")
        stt = gr.Slider(0.1, 2.0, 1.0, step=0.05, label="subtalker_temperature")
        return [do_sample, top_k, top_p, temp, rep, mnt, stk, stp, stt]

    async def run_cv(text, lang, speaker, instruct, *adv):
        if not text:
            raise gr.Error("Please enter text")
        m = await gpu.load("custom_voice")
        kw = gen_kwargs(*adv)
        wavs, sr = m.generate_custom_voice(text=text, language=lang, speaker=speaker,
                                           instruct=instruct or None, **kw)
        return (sr, wavs[0])

    async def run_vd(text, lang, instruct, *adv):
        if not text:
            raise gr.Error("Please enter text")
        if not instruct:
            raise gr.Error("Please enter voice description")
        m = await gpu.load("voice_design")
        kw = gen_kwargs(*adv)
        wavs, sr = m.generate_voice_design(text=text, language=lang, instruct=instruct, **kw)
        return (sr, wavs[0])

    async def run_vc(text, lang, ref_audio, ref_text, xvec, *adv):
        if not text:
            raise gr.Error("Please enter text")
        if ref_audio is None:
            raise gr.Error("Please upload reference audio")
        audio_sr, audio_np = ref_audio
        audio_np = np.asarray(audio_np, dtype=np.float32)
        if audio_np.ndim > 1:
            audio_np = np.mean(audio_np, axis=-1)
        # normalize int to float
        if np.issubdtype(audio_np.dtype, np.integer) or np.max(np.abs(audio_np)) > 1.5:
            audio_np = audio_np / max(np.max(np.abs(audio_np)), 1e-8)
        m = await gpu.load("voice_clone")
        kw = gen_kwargs(*adv)
        wavs, sr = m.generate_voice_clone(
            text=text, language=lang, ref_audio=(audio_np, audio_sr),
            ref_text=ref_text or None, x_vector_only_mode=xvec, **kw)
        return (sr, wavs[0])

    async def gpu_st():
        s = await gpu.status()
        lines = [f"Loaded: {'✅ ' + (s['model_type'] or '') if s['loaded'] else '❌ No model'}"]
        if s.get("memory_allocated_mb"):
            lines.append(f"VRAM: {s['memory_allocated_mb']}MB allocated / {s['memory_reserved_mb']}MB reserved")
        if s.get("idle_seconds") is not None:
            lines.append(f"Idle: {s['idle_seconds']}s")
        return "\n".join(lines)

    async def gpu_off():
        await gpu.offload()
        return "✅ GPU offloaded"

    css = """
    .gradio-container { max-width: 1200px !important; }
    footer { display: none !important; }
    """

    with gr.Blocks(title="Qwen3-TTS", theme=gr.themes.Soft(), css=css) as demo:
        gr.Markdown("# 🗣️ Qwen3-TTS\nText-to-Speech: Custom Voice / Voice Design / Voice Clone")

        with gr.Row():
            ui_lang = gr.Dropdown(["en", "zh-CN", "zh-TW", "ja"], value="en", label="🌐 UI Language", scale=1)
            gpu_box = gr.Textbox(label="GPU Status", interactive=False, scale=3)
            gr.Button("🔄", scale=0, min_width=50).click(gpu_st, outputs=gpu_box)
            gr.Button("🔻 Offload", scale=0, min_width=80).click(gpu_off, outputs=gpu_box)

        with gr.Tabs():
            # --- Custom Voice ---
            with gr.Tab("🎤 Custom Voice"):
                gr.Markdown("Generate speech with preset voices. Add instructions to control emotion/style.")
                with gr.Row():
                    with gr.Column():
                        cv_text = gr.Textbox(label="Text", lines=3, placeholder="Enter text...")
                        cv_lang = gr.Dropdown(LANGUAGES, value="Auto", label="Language")
                        cv_spk = gr.Dropdown(SPEAKERS, value="Vivian", label="Speaker")
                        cv_inst = gr.Textbox(label="Instruction", placeholder="e.g. 用愤怒的语气说")
                        with gr.Accordion("⚙️ Advanced", open=False):
                            cv_adv = _adv()
                        cv_btn = gr.Button("🎵 Generate", variant="primary")
                    with gr.Column():
                        cv_out = gr.Audio(label="Output")
                cv_btn.click(run_cv, [cv_text, cv_lang, cv_spk, cv_inst] + cv_adv, cv_out)

            # --- Voice Design ---
            with gr.Tab("🎨 Voice Design"):
                gr.Markdown("Design a new voice by describing its characteristics in natural language.")
                with gr.Row():
                    with gr.Column():
                        vd_text = gr.Textbox(label="Text", lines=3, placeholder="Enter text...")
                        vd_lang = gr.Dropdown(LANGUAGES, value="Auto", label="Language")
                        vd_inst = gr.Textbox(label="Voice Description", lines=2,
                                             placeholder="e.g. 体现撒娇稚嫩的萝莉女声")
                        with gr.Accordion("⚙️ Advanced", open=False):
                            vd_adv = _adv()
                        vd_btn = gr.Button("🎵 Generate", variant="primary")
                    with gr.Column():
                        vd_out = gr.Audio(label="Output")
                vd_btn.click(run_vd, [vd_text, vd_lang, vd_inst] + vd_adv, vd_out)

            # --- Voice Clone ---
            with gr.Tab("🔊 Voice Clone"):
                gr.Markdown("Clone a voice from a reference audio clip and synthesize new content.")
                with gr.Row():
                    with gr.Column():
                        vc_text = gr.Textbox(label="Text", lines=3, placeholder="Enter text...")
                        vc_lang = gr.Dropdown(LANGUAGES, value="Auto", label="Language")
                        vc_ref = gr.Audio(label="Reference Audio", type="numpy")
                        vc_rtext = gr.Textbox(label="Reference Text", placeholder="Transcript of reference audio...")
                        vc_xvec = gr.Checkbox(label="X-Vector Only Mode", value=False)
                        with gr.Accordion("⚙️ Advanced", open=False):
                            vc_adv = _adv()
                        vc_btn = gr.Button("🎵 Generate", variant="primary")
                    with gr.Column():
                        vc_out = gr.Audio(label="Output")
                vc_btn.click(run_vc, [vc_text, vc_lang, vc_ref, vc_rtext, vc_xvec] + vc_adv, vc_out)

        demo.load(gpu_st, outputs=gpu_box)
    return demo


gradio_app = build_ui()
app = gr.mount_gradio_app(app, gradio_app, path="/ui")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=PORT)
