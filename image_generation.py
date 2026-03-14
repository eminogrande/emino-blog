#!/usr/bin/env python3

import base64
import io
import json
import os
import re
from pathlib import Path
from typing import Callable, Optional, Tuple
from urllib import error as urllib_error
from urllib import request as urllib_request

try:
    from PIL import Image, ImageOps
except Exception:
    Image = None
    ImageOps = None

DEFAULT_IMAGE_API_BASE_URL = 'https://api.routstr.com/v1'
DEFAULT_IMAGE_MODEL = 'google/gemini-3.1-flash-image-preview'
DEFAULT_IMAGE_API_KEY_FILE = '/etc/emino-blog-image-api-key'


def _log(logger: Optional[Callable[[str], None]], message: str) -> None:
    if logger:
        logger(message)


def load_image_api_key() -> str:
    for env_name in ('EMINO_IMAGE_API_KEY', 'ROUTSTR_API_KEY', 'OPENROUTER_API_KEY'):
        candidate = os.environ.get(env_name, '').strip()
        if candidate:
            return candidate

    key_file = Path(os.environ.get('EMINO_IMAGE_API_KEY_FILE', DEFAULT_IMAGE_API_KEY_FILE))
    if key_file.exists():
        try:
            candidate = key_file.read_text(encoding='utf-8').strip()
        except Exception:
            return ''
        if candidate:
            return candidate
    return ''


def load_image_model() -> str:
    model = os.environ.get('EMINO_IMAGE_MODEL', DEFAULT_IMAGE_MODEL).strip() or DEFAULT_IMAGE_MODEL
    if '/' not in model and model.startswith('gemini-'):
        return f'google/{model}'
    return model


def load_image_api_base_url() -> str:
    value = os.environ.get('EMINO_IMAGE_API_BASE_URL', os.environ.get('ROUTSTR_API_BASE_URL', DEFAULT_IMAGE_API_BASE_URL))
    return value.rstrip('/')


def load_image_http_referer() -> str:
    return (
        os.environ.get('EMINO_IMAGE_HTTP_REFERER', '').strip()
        or os.environ.get('EMINO_BASE_URL', '').strip()
        or 'https://emino.app'
    )


def load_image_app_title() -> str:
    return os.environ.get('EMINO_IMAGE_APP_TITLE', '').strip() or 'Emino Blog'


def load_image_user_agent() -> str:
    return (
        os.environ.get('EMINO_IMAGE_USER_AGENT', '').strip()
        or 'Mozilla/5.0 (compatible; EminoBlog/1.0; +https://emino.app)'
    )


def load_image_timeout() -> int:
    raw = os.environ.get('EMINO_IMAGE_TIMEOUT', os.environ.get('EMINO_OPENAI_IMAGE_TIMEOUT', '120')).strip()
    try:
        return max(10, int(raw or '120'))
    except ValueError:
        return 120


def load_image_quality() -> int:
    raw = os.environ.get('EMINO_IMAGE_QUALITY', '80').strip()
    try:
        return min(95, max(40, int(raw or '80')))
    except ValueError:
        return 80


def load_image_max_width() -> int:
    raw = os.environ.get('EMINO_IMAGE_MAX_WIDTH', '1600').strip()
    try:
        return min(2400, max(640, int(raw or '1600')))
    except ValueError:
        return 1600


def load_image_max_height() -> int:
    raw = os.environ.get('EMINO_IMAGE_MAX_HEIGHT', '1200').strip()
    try:
        return min(2400, max(640, int(raw or '1200')))
    except ValueError:
        return 1200


def load_image_output_format() -> str:
    value = os.environ.get('EMINO_IMAGE_OUTPUT_FORMAT', 'webp').strip().lower()
    if value in {'jpeg', 'jpg'}:
        return 'jpeg'
    return 'webp'


def load_image_prompt_max_chars() -> int:
    raw = os.environ.get('EMINO_IMAGE_PROMPT_MAX_CHARS', '700').strip()
    try:
        return max(120, int(raw or '700'))
    except ValueError:
        return 700


def slugify_fragment(value: str) -> str:
    cleaned = re.sub(r'[^a-z0-9]+', '-', (value or '').lower())
    cleaned = re.sub(r'-{2,}', '-', cleaned).strip('-')
    return cleaned or 'generated-image'


def build_image_prompt(title: str, body_text: str = '', extra_prompt: str = '') -> str:
    clean_body = re.sub(r'\s+', ' ', body_text or '').strip()
    clean_prompt = re.sub(r'\s+', ' ', extra_prompt or '').strip()
    excerpt = clean_body[:load_image_prompt_max_chars()]

    parts = [
        'Create a photorealistic editorial cover photo for a personal blog post.',
        'It must look like a real photograph captured with a professional camera.',
        'Use natural lighting, believable textures, realistic depth of field, subtle imperfections, and documentary-level realism.',
        'Avoid illustration, painting, CGI, 3D render, surreal anatomy, waxy skin, and obvious AI artifacts.',
        'No words, letters, logos, captions, or watermarks in the image.',
        'Use a cinematic but natural composition with a warm, hopeful emotional tone.',
        'Landscape orientation, magazine-quality composition, visually strong but grounded in reality.',
        f'Title: {title or "Untitled Post"}.',
    ]
    if excerpt:
        parts.append(f'Post summary: {excerpt}.')
    if clean_prompt:
        parts.append(f'Additional art direction: {clean_prompt}.')
    return ' '.join(parts)


def _resample_filter():
    if not Image:
        return None
    resampling = getattr(Image, 'Resampling', None)
    if resampling is not None:
        return resampling.LANCZOS
    return Image.LANCZOS


def optimize_image_bytes(
    image_bytes: bytes,
    extension: str,
    logger: Optional[Callable[[str], None]] = None,
) -> Tuple[bytes, str]:
    if not Image:
        return image_bytes, extension

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            if ImageOps is not None:
                image = ImageOps.exif_transpose(image)

            if image.mode not in {'RGB', 'L'}:
                if 'A' in image.getbands():
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.getchannel('A'))
                    image = background
                else:
                    image = image.convert('RGB')
            elif image.mode == 'L':
                image = image.convert('RGB')

            image.thumbnail((load_image_max_width(), load_image_max_height()), _resample_filter())

            output = io.BytesIO()
            output_format = load_image_output_format()
            if output_format == 'jpeg':
                image.save(
                    output,
                    format='JPEG',
                    quality=load_image_quality(),
                    optimize=True,
                    progressive=True,
                )
                new_extension = '.jpg'
            else:
                image.save(
                    output,
                    format='WEBP',
                    quality=load_image_quality(),
                    method=6,
                )
                new_extension = '.webp'

            optimized = output.getvalue()
            _log(logger, f'Optimized image from {len(image_bytes) // 1024} KB to {len(optimized) // 1024} KB as {new_extension}.')
            return optimized, new_extension
    except Exception as exc:
        _log(logger, f'Image optimization failed, keeping original asset: {exc}')
        return image_bytes, extension


def _decode_data_url(data_url: str) -> Tuple[bytes, str]:
    match = re.match(r'^data:(image/[^;]+);base64,(.+)$', data_url, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError('Unsupported image data URL')
    mime_type = match.group(1).lower()
    payload = base64.b64decode(match.group(2))
    return payload, _extension_for_mime(mime_type)


def _extension_for_mime(mime_type: str) -> str:
    mapping = {
        'image/png': '.png',
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/webp': '.webp',
        'image/gif': '.gif',
        'image/svg+xml': '.svg',
    }
    return mapping.get((mime_type or '').lower(), '.png')


def _download_image(url: str, timeout: int) -> Tuple[bytes, str]:
    with urllib_request.urlopen(url, timeout=timeout) as response:
        content_type = response.headers.get_content_type()
        return response.read(), _extension_for_mime(content_type)


def _extract_from_choice_images(payload: dict, timeout: int) -> Optional[Tuple[bytes, str]]:
    choices = payload.get('choices') or []
    if not choices:
        return None

    message = (choices[0] or {}).get('message') or {}
    image_items = message.get('images') or []
    for item in image_items:
        if not isinstance(item, dict):
            continue

        raw_base64 = item.get('b64_json') or item.get('data')
        if isinstance(raw_base64, str) and raw_base64.strip():
            try:
                return base64.b64decode(raw_base64), '.png'
            except Exception as exc:
                raise ValueError(f'Failed to decode base64 image payload: {exc}') from exc

        image_url = item.get('image_url')
        if isinstance(image_url, dict):
            image_url = image_url.get('url', '')
        elif not isinstance(image_url, str):
            image_url = ''

        if not image_url:
            image_url = item.get('url', '')

        if isinstance(image_url, str) and image_url.startswith('data:image/'):
            return _decode_data_url(image_url)
        if isinstance(image_url, str) and image_url.startswith(('http://', 'https://')):
            return _download_image(image_url, timeout)

    return None


def _extract_openai_style(payload: dict, timeout: int) -> Optional[Tuple[bytes, str]]:
    image_items = payload.get('data') or []
    if not image_items:
        return None

    item = image_items[0] or {}
    raw_base64 = item.get('b64_json')
    if isinstance(raw_base64, str) and raw_base64.strip():
        try:
            return base64.b64decode(raw_base64), '.png'
        except Exception as exc:
            raise ValueError(f'Failed to decode base64 image payload: {exc}') from exc

    image_url = item.get('url', '')
    if isinstance(image_url, str) and image_url.startswith('data:image/'):
        return _decode_data_url(image_url)
    if isinstance(image_url, str) and image_url.startswith(('http://', 'https://')):
        return _download_image(image_url, timeout)
    return None


def generate_image_bytes(prompt: str, logger: Optional[Callable[[str], None]] = None) -> Optional[Tuple[bytes, str]]:
    api_key = load_image_api_key()
    if not api_key:
        _log(logger, 'No image API key configured. Set EMINO_IMAGE_API_KEY or EMINO_IMAGE_API_KEY_FILE.')
        return None

    payload = {
        'model': load_image_model(),
        'modalities': ['text', 'image'],
        'messages': [{'role': 'user', 'content': prompt}],
    }
    request = urllib_request.Request(
        f'{load_image_api_base_url()}/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': load_image_http_referer(),
            'User-Agent': load_image_user_agent(),
            'X-Title': load_image_app_title(),
        },
        method='POST',
    )
    timeout = load_image_timeout()

    try:
        with urllib_request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib_error.HTTPError as exc:
        details = exc.read().decode('utf-8', errors='ignore').strip()
        _log(logger, f'Image generation failed ({exc.code}): {details[:240]}')
        return None
    except Exception as exc:
        _log(logger, f'Image generation failed: {exc}')
        return None

    try:
        extracted = _extract_from_choice_images(data, timeout) or _extract_openai_style(data, timeout)
    except Exception as exc:
        _log(logger, f'Failed to parse generated image response: {exc}')
        return None

    if not extracted:
        _log(logger, 'Image generation returned no images.')
        return None
    return extracted


def generate_image_asset(
    static_media_dir: Path,
    slug: str,
    prompt: str,
    *,
    filename_stem: str = 'cover',
    logger: Optional[Callable[[str], None]] = None,
) -> Optional[Path]:
    generated = generate_image_bytes(prompt, logger=logger)
    if not generated:
        return None

    image_bytes, extension = generated
    image_bytes, extension = optimize_image_bytes(image_bytes, extension, logger=logger)
    safe_slug = slug.strip('/').strip() or 'generated-image'
    safe_slug = '/'.join(slugify_fragment(part) for part in safe_slug.split('/') if part.strip())
    dest_dir = static_media_dir / safe_slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f'{slugify_fragment(filename_stem)}{extension}'
    dest.write_bytes(image_bytes)
    return dest
