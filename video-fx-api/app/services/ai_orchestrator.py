"""Production-grade AI orchestrator for multi-model video effects.

Uses Gemini and Claude to analyze videos and generate optimized FFmpeg
processing parameters. Falls back to curated presets when API keys
are not configured.
"""

import json
import os
import httpx
from typing import Optional

from app.models.schemas import AIModel, EffectType

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

EFFECT_MODEL_MAP: dict[EffectType, AIModel] = {
    EffectType.MOTION_GRAPHICS: AIModel.CLAUDE,
    EffectType.UPSCALING: AIModel.GEMINI,
    EffectType.STYLE_TRANSFER: AIModel.GEMINI,
    EffectType.COLOR_GRADING: AIModel.GEMINI,
    EffectType.BACKGROUND_REMOVAL: AIModel.GEMINI,
    EffectType.SLOW_MOTION: AIModel.GEMINI,
    EffectType.STABILIZATION: AIModel.GEMINI,
    EffectType.AUTO_CAPTION: AIModel.CLAUDE,
}

# --- Curated production-quality presets ---

COLOR_GRADING_PRESETS: dict[str, dict] = {
    "cinematic_warm": {
        "brightness": 0.02, "contrast": 1.15, "saturation": 0.9,
        "temperature": 0.3, "gamma": 0.95, "vignette": True,
        "vignette_strength": 0.35, "sharpen": 0.5,
    },
    "cinematic_cool": {
        "brightness": -0.02, "contrast": 1.2, "saturation": 0.85,
        "temperature": -0.25, "gamma": 0.9, "vignette": True,
        "vignette_strength": 0.4, "sharpen": 0.3,
    },
    "vibrant": {
        "brightness": 0.05, "contrast": 1.1, "saturation": 1.4,
        "temperature": 0.1, "vibrance": 0.3, "sharpen": 0.6,
    },
    "moody": {
        "brightness": -0.08, "contrast": 1.3, "saturation": 0.7,
        "temperature": -0.15, "gamma": 0.85, "vignette": True,
        "vignette_strength": 0.5,
    },
    "golden_hour": {
        "brightness": 0.06, "contrast": 1.05, "saturation": 1.2,
        "temperature": 0.45, "tint": 0.05, "vibrance": 0.2,
        "vignette": True, "vignette_strength": 0.25,
    },
    "film_emulation": {
        "brightness": 0.03, "contrast": 1.25, "saturation": 0.8,
        "gamma": 1.05, "temperature": 0.15,
        "vignette": True, "vignette_strength": 0.3,
    },
}

STYLE_PRESETS = [
    "cinematic", "vintage", "noir", "warm", "cool", "anime", "bleach", "sunset",
]


def _select_model(effect_type: EffectType, requested: AIModel) -> AIModel:
    if requested != AIModel.AUTO:
        return requested
    return EFFECT_MODEL_MAP.get(effect_type, AIModel.GEMINI)


def _build_ai_prompt(
    effect_type: EffectType, video_info: dict, intensity: float, user_params: dict,
) -> str:
    base = (
        f"You are a professional video colorist / VFX artist. "
        f"Video: {video_info.get('width', 1920)}x{video_info.get('height', 1080)}, "
        f"{video_info.get('fps', 30)}fps, {video_info.get('duration_seconds', 0)}s. "
        f"Intensity: {intensity} (0=subtle, 1=extreme). "
    )
    prompts: dict[EffectType, str] = {
        EffectType.COLOR_GRADING: (
            base + "Return ONLY valid JSON: brightness(-0.3..0.3), contrast(0.5..2), "
            "saturation(0..2.5), temperature(-1..1), tint(-0.5..0.5), gamma(0.5..2), "
            "vibrance(-0.5..0.5), vignette(bool), vignette_strength(0.1..0.8), sharpen(0..2). "
            f"Look: {user_params.get('look', 'cinematic')}."
        ),
        EffectType.UPSCALING: (
            base + "Return ONLY valid JSON: target_width(int), target_height(int), "
            "sharpen(0..2), denoise(0..1)."
        ),
        EffectType.STYLE_TRANSFER: (
            base + f"Choose best style from {STYLE_PRESETS}. "
            f"Return ONLY JSON with key 'style'. User wants: {user_params.get('style', 'cinematic')}."
        ),
        EffectType.SLOW_MOTION: (
            base + "Return ONLY JSON: factor(1.5..8, 2=half speed)."
        ),
        EffectType.STABILIZATION: (
            base + "Return ONLY JSON: shakiness(1-10), smoothing(1-30)."
        ),
        EffectType.AUTO_CAPTION: (
            base + "Return ONLY JSON: text(string), font_size(24-48), "
            "position('bottom'|'top'|'center'), bg_opacity(0.3-0.8). "
            f"Context: {user_params.get('context', 'professional video')}."
        ),
        EffectType.MOTION_GRAPHICS: (
            base + "Return ONLY JSON: type('title'|'lower_third'|'fade'), "
            "title(string), name(string)."
        ),
        EffectType.BACKGROUND_REMOVAL: (
            base + "Return ONLY JSON: blur_background(bool), blur_strength(5-40), "
            "bg_color(hex string)."
        ),
    }
    return prompts.get(effect_type, base + "Generate video effect parameters as JSON.")


async def _call_gemini(prompt: str) -> Optional[dict]:
    if not GEMINI_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 512},
                },
            )
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                return _extract_json(text)
    except Exception:
        pass
    return None


async def _call_claude(prompt: str) -> Optional[dict]:
    if not CLAUDE_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                CLAUDE_API_URL,
                headers={
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 512,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            if resp.status_code == 200:
                text = resp.json()["content"][0]["text"]
                return _extract_json(text)
    except Exception:
        pass
    return None


def _extract_json(text: str) -> Optional[dict]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


def _get_curated_params(
    effect_type: EffectType, intensity: float, user_params: dict,
) -> dict:
    """Curated production-quality parameters when AI is unavailable."""
    if effect_type == EffectType.COLOR_GRADING:
        look = user_params.get("look", "cinematic_warm")
        preset = COLOR_GRADING_PRESETS.get(look, COLOR_GRADING_PRESETS["cinematic_warm"])
        scaled: dict = {}
        for key, val in preset.items():
            if isinstance(val, float):
                if key in ("brightness", "temperature", "tint", "vibrance"):
                    scaled[key] = val * intensity * 2
                elif key in ("contrast", "saturation", "gamma"):
                    scaled[key] = 1.0 + (val - 1.0) * intensity * 2
                elif key in ("sharpen", "vignette_strength"):
                    scaled[key] = val * intensity * 2
                else:
                    scaled[key] = val
            else:
                scaled[key] = val
        return scaled

    if effect_type == EffectType.UPSCALING:
        scale = 1.5 + intensity
        return {
            "target_width": int(user_params.get("width", 1920) * scale),
            "target_height": int(user_params.get("height", 1080) * scale),
            "sharpen": 0.5 + intensity,
            "denoise": intensity * 0.3,
        }

    if effect_type == EffectType.STYLE_TRANSFER:
        style = user_params.get("style", "cinematic")
        return {"style": style if style in STYLE_PRESETS else "cinematic"}

    if effect_type == EffectType.SLOW_MOTION:
        return {"factor": round(1.5 + intensity * 3.5, 1)}

    if effect_type == EffectType.STABILIZATION:
        return {
            "shakiness": max(1, int(5 + intensity * 5)),
            "smoothing": max(1, int(10 + intensity * 20)),
        }

    if effect_type == EffectType.AUTO_CAPTION:
        return {
            "text": user_params.get("text", "Professional Video Content"),
            "font_size": int(28 + intensity * 20),
            "position": user_params.get("position", "bottom"),
            "bg_opacity": 0.4 + intensity * 0.3,
        }

    if effect_type == EffectType.MOTION_GRAPHICS:
        return {
            "type": user_params.get("type", "title"),
            "title": user_params.get("title", "VideoFX AI"),
            "name": user_params.get("name", "Creator"),
        }

    if effect_type == EffectType.BACKGROUND_REMOVAL:
        return {
            "blur_background": user_params.get("blur_background", True),
            "blur_strength": int(10 + intensity * 30),
            "bg_color": user_params.get("bg_color", "black"),
        }

    return {}


async def generate_effect_params(
    effect_type: EffectType,
    ai_model: AIModel,
    video_info: dict,
    intensity: float,
    user_params: dict,
) -> dict:
    """Generate production-quality effect parameters using AI or curated presets."""
    selected_model = _select_model(effect_type, ai_model)
    prompt = _build_ai_prompt(effect_type, video_info, intensity, user_params)

    ai_params: Optional[dict] = None
    if selected_model == AIModel.GEMINI:
        ai_params = await _call_gemini(prompt)
        if ai_params is None and CLAUDE_API_KEY:
            ai_params = await _call_claude(prompt)
    else:
        ai_params = await _call_claude(prompt)
        if ai_params is None and GEMINI_API_KEY:
            ai_params = await _call_gemini(prompt)

    if ai_params:
        merged = {**ai_params, **user_params}
        return {"params": merged, "model_used": selected_model.value, "ai_enhanced": True}

    curated = _get_curated_params(effect_type, intensity, user_params)
    return {"params": curated, "model_used": "curated_preset", "ai_enhanced": False}
