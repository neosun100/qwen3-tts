import os, io, time, base64, logging
from pathlib import Path

import torch
import numpy as np
import soundfile as sf
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qwen3-tts-mcp")

GPU_IDLE_TIMEOUT = int(os.getenv("GPU_IDLE_TIMEOUT", 600))
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
CUDA_DEVICE = os.getenv("CUDA_DEVICE", "cuda:0")
OUTPUT_DIR = Path("/tmp/qwen3-tts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_MAP = {
    "custom_voice": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    "voice_design": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    "voice_clone": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
}
SPEAKERS = ["Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ryan", "Aiden", "Ono_Anna", "Sohee"]
LANGUAGES = ["Auto", "Chinese", "English", "Japanese", "Korean", "German", "French", "Russian", "Portuguese", "Spanish", "Italian"]

_model = None
_model_type = None
_last_use = 0.0


def _unload():
    global _model, _model_type
    if _model:
        del _model
        _model = None
        _model_type = None
        torch.cuda.empty_cache()


def _load(model_type: str):
    global _model, _model_type, _last_use
    _last_use = time.time()
    if _model and _model_type == model_type:
        return _model
    _unload()
    logger.info(f"Loading {MODEL_MAP[model_type]}")
    from qwen_tts import Qwen3TTSModel
    _model = Qwen3TTSModel.from_pretrained(
        MODEL_MAP[model_type], device_map=CUDA_DEVICE,
        dtype=torch.bfloat16, attn_implementation="flash_attention_2",
    )
    _model_type = model_type
    return _model


def _save_wav(audio: np.ndarray, sr: int) -> str:
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"output_{ts}.wav"
    sf.write(str(path), audio, sr)
    return str(path)


def _audio_b64(audio: np.ndarray, sr: int) -> str:
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    return base64.b64encode(buf.getvalue()).decode()


def _gen_kw(do_sample=True, top_k=50, top_p=0.9, temperature=1.0, repetition_penalty=1.05,
            max_new_tokens=2048, subtalker_top_k=50, subtalker_top_p=0.9, subtalker_temperature=1.0):
    return dict(do_sample=do_sample, top_k=top_k, top_p=top_p, temperature=temperature,
                repetition_penalty=repetition_penalty, max_new_tokens=max_new_tokens,
                subtalker_top_k=subtalker_top_k, subtalker_top_p=subtalker_top_p,
                subtalker_temperature=subtalker_temperature)


mcp = FastMCP("qwen3-tts")


@mcp.tool()
def tts_custom_voice(
    text: str, speaker: str = "Vivian", language: str = "Auto", instruct: str = "",
    do_sample: bool = True, top_k: int = 50, top_p: float = 0.9, temperature: float = 1.0,
    repetition_penalty: float = 1.05, max_new_tokens: int = 2048,
    subtalker_top_k: int = 50, subtalker_top_p: float = 0.9, subtalker_temperature: float = 1.0,
) -> dict:
    """Generate speech with a preset voice. Speakers: Vivian, Serena, Uncle_Fu, Dylan, Eric, Ryan, Aiden, Ono_Anna, Sohee."""
    try:
        m = _load("custom_voice")
        wavs, sr = m.generate_custom_voice(text=text, language=language, speaker=speaker,
                                           instruct=instruct or None,
                                           **_gen_kw(do_sample, top_k, top_p, temperature,
                                                     repetition_penalty, max_new_tokens,
                                                     subtalker_top_k, subtalker_top_p, subtalker_temperature))
        path = _save_wav(wavs[0], sr)
        return {"status": "success", "file_path": path, "sample_rate": sr,
                "audio_base64": _audio_b64(wavs[0], sr)}
    except Exception as e:
        _unload()
        return {"status": "error", "error": str(e)}


@mcp.tool()
def tts_voice_design(
    text: str, instruct: str, language: str = "Auto",
    do_sample: bool = True, top_k: int = 50, top_p: float = 0.9, temperature: float = 1.0,
    repetition_penalty: float = 1.05, max_new_tokens: int = 2048,
    subtalker_top_k: int = 50, subtalker_top_p: float = 0.9, subtalker_temperature: float = 1.0,
) -> dict:
    """Design a new voice by describing characteristics in natural language, then generate speech."""
    try:
        m = _load("voice_design")
        wavs, sr = m.generate_voice_design(text=text, language=language, instruct=instruct,
                                           **_gen_kw(do_sample, top_k, top_p, temperature,
                                                     repetition_penalty, max_new_tokens,
                                                     subtalker_top_k, subtalker_top_p, subtalker_temperature))
        path = _save_wav(wavs[0], sr)
        return {"status": "success", "file_path": path, "sample_rate": sr,
                "audio_base64": _audio_b64(wavs[0], sr)}
    except Exception as e:
        _unload()
        return {"status": "error", "error": str(e)}


@mcp.tool()
def tts_voice_clone(
    text: str, ref_audio_path: str, ref_text: str = "", language: str = "Auto",
    x_vector_only_mode: bool = False,
    do_sample: bool = True, top_k: int = 50, top_p: float = 0.9, temperature: float = 1.0,
    repetition_penalty: float = 1.05, max_new_tokens: int = 2048,
    subtalker_top_k: int = 50, subtalker_top_p: float = 0.9, subtalker_temperature: float = 1.0,
) -> dict:
    """Clone a voice from reference audio and synthesize new content."""
    try:
        m = _load("voice_clone")
        wavs, sr = m.generate_voice_clone(
            text=text, language=language, ref_audio=ref_audio_path,
            ref_text=ref_text or None, x_vector_only_mode=x_vector_only_mode,
            **_gen_kw(do_sample, top_k, top_p, temperature, repetition_penalty,
                      max_new_tokens, subtalker_top_k, subtalker_top_p, subtalker_temperature))
        path = _save_wav(wavs[0], sr)
        return {"status": "success", "file_path": path, "sample_rate": sr,
                "audio_base64": _audio_b64(wavs[0], sr)}
    except Exception as e:
        _unload()
        return {"status": "error", "error": str(e)}


@mcp.tool()
def gpu_status() -> dict:
    """Get current GPU and model status."""
    info = {"loaded": _model is not None, "model_type": _model_type}
    if _last_use:
        info["idle_seconds"] = round(time.time() - _last_use, 1)
    try:
        if torch.cuda.is_available():
            idx = int(CUDA_DEVICE.split(":")[-1]) if ":" in CUDA_DEVICE else 0
            info["gpu_name"] = torch.cuda.get_device_name(idx)
            info["memory_allocated_mb"] = round(torch.cuda.memory_allocated(idx) / 1048576)
    except Exception:
        pass
    return info


@mcp.tool()
def gpu_offload() -> dict:
    """Offload model from GPU to free VRAM."""
    _unload()
    return {"status": "success", "message": "GPU offloaded"}


@mcp.tool()
def list_speakers() -> list:
    """List all supported speaker names for CustomVoice model."""
    return SPEAKERS


@mcp.tool()
def list_languages() -> list:
    """List all supported languages."""
    return LANGUAGES


if __name__ == "__main__":
    mcp.run()
