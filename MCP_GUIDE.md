# Qwen3-TTS MCP Guide

## Overview

The Qwen3-TTS MCP (Model Context Protocol) server provides programmatic access to all TTS capabilities through MCP-compatible clients (e.g., Claude Desktop, Kiro, Cursor).

## Setup

### Configuration

Add to your MCP client config (e.g., `~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "qwen3-tts": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/Qwen3-TTS",
      "env": {
        "GPU_IDLE_TIMEOUT": "600",
        "CUDA_DEVICE": "cuda:0"
      }
    }
  }
}
```

### Docker Usage

```json
{
  "mcpServers": {
    "qwen3-tts": {
      "command": "docker",
      "args": ["exec", "-i", "qwen3-tts", "python", "mcp_server.py"]
    }
  }
}
```

## Available Tools

### `tts_custom_voice`
Generate speech with a preset voice.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| text | str | required | Text to synthesize |
| speaker | str | "Vivian" | Speaker name |
| language | str | "Auto" | Target language |
| instruct | str | "" | Style instruction |
| temperature | float | 1.0 | Sampling temperature |
| top_k | int | 50 | Top-k sampling |
| top_p | float | 0.9 | Top-p sampling |
| max_new_tokens | int | 2048 | Max generation length |

**Speakers**: Vivian, Serena, Uncle_Fu, Dylan, Eric, Ryan, Aiden, Ono_Anna, Sohee

### `tts_voice_design`
Design a new voice by describing characteristics.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| text | str | required | Text to synthesize |
| instruct | str | required | Voice description |
| language | str | "Auto" | Target language |

### `tts_voice_clone`
Clone a voice from reference audio.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| text | str | required | Text to synthesize |
| ref_audio_path | str | required | Path to reference audio |
| ref_text | str | "" | Transcript of reference |
| language | str | "Auto" | Target language |
| x_vector_only_mode | bool | False | Use speaker embedding only |

### `gpu_status`
Get current GPU and model status. No parameters.

### `gpu_offload`
Free GPU memory by unloading the model. No parameters.

### `list_speakers`
List supported speaker names. No parameters.

### `list_languages`
List supported languages. No parameters.

## Examples

```
# Custom voice
Use tts_custom_voice with text="Hello world", speaker="Ryan", language="English"

# Voice design
Use tts_voice_design with text="你好世界", instruct="温柔的年轻女声", language="Chinese"

# Voice clone
Use tts_voice_clone with text="New content", ref_audio_path="/tmp/ref.wav", ref_text="Original text"

# Check GPU
Use gpu_status

# Free memory
Use gpu_offload
```

## Output Format

All TTS tools return:
```json
{
  "status": "success",
  "file_path": "/tmp/qwen3-tts/output_20260220_012345.wav",
  "sample_rate": 24000,
  "audio_base64": "UklGR..."
}
```

## Difference from API

| Feature | API (REST) | MCP |
|---------|-----------|-----|
| Protocol | HTTP | stdio/SSE |
| Audio output | WAV stream | base64 + file path |
| File upload | multipart form | file path |
| Best for | Web apps | AI assistants |
