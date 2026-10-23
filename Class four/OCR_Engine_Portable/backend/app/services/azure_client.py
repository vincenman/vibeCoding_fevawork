"""Azure OpenAI vision OCR — adapted from OCR_minimal_Azure_v4.ipynb."""

import base64

from openai import AzureOpenAI

from app.config import settings


def _get_client() -> AzureOpenAI:
    if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
        raise RuntimeError(
            "Missing AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT in environment"
        )
    return AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_endpoint_normalized,
        api_version=settings.azure_openai_api_version,
    )


def ocr_png_bytes(png_bytes: bytes, model: str, prompt: str) -> str:
    """Send one page image to Azure OpenAI vision and return extracted text."""
    client = _get_client()
    b64 = base64.b64encode(png_bytes).decode()
    data_url = f"data:image/png;base64,{b64}"

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def ocr_image_file(image_path: str, model: str, prompt: str) -> str:
    """OCR a standalone image file by reading and encoding it."""
    from pathlib import Path

    path = Path(image_path)
    png_bytes = path.read_bytes()
    return ocr_png_bytes(png_bytes, model=model, prompt=prompt)
