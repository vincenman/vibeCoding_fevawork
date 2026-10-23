"""OpenRouter multimodal OCR client."""

import base64

import httpx

from app.config import settings


async def ocr_png_bytes(png_bytes: bytes, model: str, prompt: str) -> str:
    if not settings.openrouter_api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY in environment")

    b64 = base64.b64encode(png_bytes).decode()
    data_url = f"data:image/png;base64,{b64}"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
    }

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    return (data["choices"][0]["message"]["content"] or "").strip()


async def ocr_image_file(image_path: str, model: str, prompt: str) -> str:
    from pathlib import Path

    png_bytes = Path(image_path).read_bytes()
    return await ocr_png_bytes(png_bytes, model=model, prompt=prompt)
