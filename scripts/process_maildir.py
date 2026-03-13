#!/usr/bin/env python3
"""
Process incoming Maildir messages and turn authorized emails into Hugo posts.
"""

import email
import base64
import html
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from email import policy
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import getaddresses, parseaddr
from html.parser import HTMLParser
from pathlib import Path
from typing import List, Optional, Sequence, Tuple
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlparse


DEFAULT_AUTHORIZED = {
    'emin@nuri.com',
    'emin@emin.de',
    'eminhenri@gmail.com',
    'proud@me.com',
}

BLOG_DIR = Path(os.environ.get('EMINO_BLOG_DIR', '/var/www/emino-blog')).resolve()
MAILDIR_PATH = Path(os.environ.get('EMINO_MAILDIR', '/var/mail/vhosts/emino.app/post')).resolve()
CONTENT_DIR = BLOG_DIR / 'content' / 'posts'
STATIC_MEDIA_DIR = BLOG_DIR / 'static' / 'media'
AUTH_FILE = Path(os.environ.get('EMINO_AUTH_FILE', BLOG_DIR / 'scripts' / 'email_auth.txt')).resolve()
HUGO_BIN = os.environ.get('EMINO_HUGO_BIN', 'hugo')
GIT_BRANCH = os.environ.get('EMINO_GIT_BRANCH', 'main')
SKIP_GIT = os.environ.get('EMINO_SKIP_GIT') == '1'
BASE_URL = os.environ.get('EMINO_BASE_URL', 'https://emino.app').rstrip('/')
NOTIFY_FROM = os.environ.get('EMINO_NOTIFY_FROM', 'post@emino.app')
SENDMAIL_BIN = os.environ.get('EMINO_SENDMAIL', '/usr/sbin/sendmail')
SEND_NOTIFICATIONS = os.environ.get('EMINO_NOTIFY_EMAIL', '1') != '0'
TITLE_MARKER = os.environ.get('EMINO_POST_TITLE_MARKER', 'hope').strip()
REQUIRE_TITLE_MARKER = os.environ.get('EMINO_REQUIRE_TITLE_MARKER', '1') != '0'
TOKEN_FILE = Path(os.environ.get('EMINO_POST_TOKEN_FILE', '/etc/emino-blog-post-token')).resolve()
POST_TOKEN_ENV = os.environ.get('EMINO_POST_TOKEN', '').strip()
POST_TOKEN_MARKER = os.environ.get('EMINO_POST_TOKEN_MARKER', 'POST_TOKEN:')
REQUIRE_POST_TOKEN = os.environ.get('EMINO_REQUIRE_POST_TOKEN', '0') != '0'
REQUIRE_DMARC_PASS = os.environ.get('EMINO_REQUIRE_DMARC_PASS', '0') != '0'
REQUIRE_TO_ADDRESS = os.environ.get('EMINO_REQUIRE_TO_ADDRESS', 'post@emino.app').strip().lower()
BLOCKED_RECEIVED_HOSTS = tuple(
    host.strip().lower()
    for host in os.environ.get('EMINO_BLOCKED_RECEIVED_HOSTS', 'emkei.cz').split(',')
    if host.strip()
)
AUTO_GENERATE_IMAGE = os.environ.get('EMINO_AUTO_GENERATE_IMAGE', '1') != '0'
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', os.environ.get('EMINO_OPENAI_API_KEY', '')).strip()
OPENAI_IMAGE_MODEL = os.environ.get('EMINO_OPENAI_IMAGE_MODEL', 'gpt-image-1').strip()
OPENAI_IMAGE_SIZE = os.environ.get('EMINO_OPENAI_IMAGE_SIZE', '1536x1024').strip()
OPENAI_IMAGE_TIMEOUT = int(os.environ.get('EMINO_OPENAI_IMAGE_TIMEOUT', '90') or '90')
IMAGE_PROMPT_MAX_CHARS = int(os.environ.get('EMINO_IMAGE_PROMPT_MAX_CHARS', '700') or '700')

NEW_DIR = MAILDIR_PATH / 'new'
CUR_DIR = MAILDIR_PATH / 'cur'

ALLOWED_TAGS = {
    'p', 'br', 'div', 'span', 'strong', 'em', 'b', 'i', 'u',
    'ul', 'ol', 'li', 'blockquote', 'pre', 'code', 'hr',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
}
BLOCK_TAGS = {
    'p', 'div', 'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'thead', 'tbody', 'tr',
}
SELF_CLOSING = {'br', 'hr', 'img'}
URL_ATTRS = {'href', 'src'}
GLOBAL_ATTRS = {'title'}
ALLOWED_ATTRS = {
    'a': {'href', 'title', 'target', 'rel'},
    'img': {'src', 'alt', 'title'},
    'td': {'colspan', 'rowspan'},
    'th': {'colspan', 'rowspan'},
}


class HTMLToText(HTMLParser):
    """Very small helper to turn HTML into readable text without extra deps."""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {'br', 'div', 'p', 'li'}:
            self._chunks.append('\n')

    def handle_endtag(self, tag):
        if tag in {'div', 'p', 'li'}:
            self._chunks.append('\n')

    def handle_data(self, data):
        if data:
            self._chunks.append(data)

    def get_text(self) -> str:
        text = ''.join(self._chunks)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def log(message: str) -> None:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {message}')


def load_authorized_senders() -> Sequence[str]:
    if not AUTH_FILE.exists():
        return sorted(DEFAULT_AUTHORIZED)

    senders = set()
    for raw_line in AUTH_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        senders.add(line.lower())
    return sorted(senders) or sorted(DEFAULT_AUTHORIZED)


def title_marker_regex(marker: str):
    escaped = re.escape(marker)
    return re.compile(rf'(?<![a-z0-9]){escaped}(?![a-z0-9])', flags=re.IGNORECASE)


def decode_header_value(raw_value: str) -> str:
    if not raw_value:
        return 'Untitled Post'
    try:
        return str(make_header(decode_header(raw_value)))
    except Exception:
        return raw_value


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    value = re.sub(r'-{2,}', '-', value).strip('-')
    return value or 'email-post'


def _safe_url(value: str) -> str:
    if not value:
        return ''
    parsed = urlparse(value)
    if parsed.scheme in {'http', 'https', 'mailto', ''}:
        return value
    if parsed.scheme == 'data' and value.startswith('data:image/'):
        return value
    return ''


class HTMLSanitizer(HTMLParser):
    """Lightweight HTML sanitizer that keeps formatting but strips unsafe tags/attrs."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: List[str] = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in BLOCK_TAGS:
            self._parts.append('\n')
        if t not in ALLOWED_TAGS:
            return
        cleaned = []
        allowed = ALLOWED_ATTRS.get(t, set()) | GLOBAL_ATTRS
        for k, v in attrs:
            attr = k.lower()
            if attr not in allowed or v is None:
                continue
            val = v
            if attr in URL_ATTRS:
                val = _safe_url(val)
                if not val:
                    continue
            cleaned.append(f'{attr}="{html.escape(val, quote=True)}"')
        attr_text = f" {' '.join(cleaned)}" if cleaned else ''
        if t in SELF_CLOSING:
            self._parts.append(f'<{t}{attr_text}>')
            return
        self._parts.append(f'<{t}{attr_text}>')

    def handle_endtag(self, tag):
        t = tag.lower()
        if t not in ALLOWED_TAGS or t in SELF_CLOSING:
            return
        self._parts.append(f'</{t}>')
        if t in BLOCK_TAGS:
            self._parts.append('\n')

    def handle_data(self, data):
        if data:
            self._parts.append(html.escape(data))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def get_html(self) -> str:
        combined = ''.join(self._parts)
        combined = re.sub(r'\n{3,}', '\n\n', combined)
        return combined.strip()


def sanitize_html(value: str) -> str:
    parser = HTMLSanitizer()
    parser.feed(value)
    return parser.get_html()


def extract_body(message: EmailMessage) -> Tuple[str, str]:
    # Prefer HTML; keep sanitized HTML if present, otherwise fall back to text/markdown.
    html_part = message.get_body(preferencelist=('html',))
    if html_part:
        raw_html = html_part.get_content()
        sanitized = sanitize_html(raw_html)
        if sanitized:
            return sanitized, 'html'
        # If sanitization empties content, fall back to plaintext below.

    text_part = message.get_body(preferencelist=('plain',))
    if text_part:
        return text_part.get_content().strip(), 'markdown'

    payload = message.get_payload(decode=True)
    if isinstance(payload, bytes):
        return payload.decode('utf-8', errors='ignore').strip(), 'markdown'
    if isinstance(payload, str):
        return payload.strip(), 'markdown'
    return '', 'markdown'


def save_images(message: EmailMessage, slug: str) -> List[Path]:
    saved = []
    index = 1
    for part in message.iter_attachments():
        if part.get_content_maintype() != 'image':
            continue
        data = part.get_payload(decode=True)
        if not data:
            continue

        filename = part.get_filename()
        if filename:
            try:
                filename = str(make_header(decode_header(filename)))
            except Exception:
                pass
        if not filename:
            extension = part.get_content_subtype() or 'jpg'
            filename = f'image-{index}.{extension}'

        filename = re.sub(r'[^A-Za-z0-9._-]', '_', filename)
        dest_dir = STATIC_MEDIA_DIR / slug
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename
        dest_path.write_bytes(data)
        saved.append(dest_path)
        index += 1

    return saved


def _wrap_title_lines(subject: str, max_len: int = 34, max_lines: int = 3) -> List[str]:
    words = subject.strip().split()
    if not words:
        return ['Untitled Post']

    lines: List[str] = []
    current: List[str] = []
    for word in words:
        candidate = ' '.join(current + [word]).strip()
        if len(candidate) <= max_len:
            current.append(word)
            continue
        if current:
            lines.append(' '.join(current))
            if len(lines) >= max_lines:
                break
        current = [word[:max_len]]

    if len(lines) < max_lines and current:
        lines.append(' '.join(current))

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if words and len(' '.join(words)) > len(' '.join(lines)):
        lines[-1] = (lines[-1][: max(3, max_len - 3)] + '...').rstrip()

    return lines or ['Untitled Post']


def has_title_marker(subject: str, marker: str) -> bool:
    if not marker:
        return True
    return bool(title_marker_regex(marker).search(subject or ''))


def strip_title_marker(subject: str, marker: str) -> str:
    if not subject or not marker:
        return subject

    cleaned = title_marker_regex(marker).sub(' ', subject)
    cleaned = re.sub(r'\s*[-:|/]+\s*', ' ', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned.strip(" \t-:|/[](){}")


def generate_fallback_image(slug: str, subject: str) -> Optional[Path]:
    """Create a deterministic SVG cover image for posts without image attachments."""
    try:
        digest = hashlib.sha256(slug.encode('utf-8')).hexdigest()
        color_a = f'#{digest[0:6]}'
        color_b = f'#{digest[6:12]}'
        lines = _wrap_title_lines(subject)

        line_nodes = []
        y = 330
        for line in lines:
            safe_line = html.escape(line)
            line_nodes.append(
                f'<text x="80" y="{y}" fill="white" font-size="44" font-weight="700" '
                f'font-family="-apple-system, Segoe UI, Roboto, Arial, sans-serif">{safe_line}</text>'
            )
            y += 58

        safe_slug = html.escape(slug)
        safe_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{color_a}" />
    <stop offset="100%" stop-color="{color_b}" />
  </linearGradient>
</defs>
<rect width="1600" height="900" fill="url(#bg)"/>
<rect x="60" y="60" width="1480" height="780" rx="28" fill="rgba(0,0,0,0.22)" />
<text x="80" y="155" fill="white" font-size="28" font-weight="600" font-family="-apple-system, Segoe UI, Roboto, Arial, sans-serif">emino.app</text>
{"".join(line_nodes)}
<text x="80" y="810" fill="rgba(255,255,255,0.9)" font-size="24" font-family="-apple-system, Segoe UI, Roboto, Arial, sans-serif">Auto-generated cover · {safe_date}</text>
<text x="1520" y="810" fill="rgba(255,255,255,0.65)" font-size="18" text-anchor="end" font-family="-apple-system, Segoe UI, Roboto, Arial, sans-serif">{safe_slug}</text>
</svg>
'''
        dest_dir = STATIC_MEDIA_DIR / slug
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / 'cover.svg'
        dest.write_text(svg, encoding='utf-8')
        return dest
    except Exception as exc:
        log(f'Failed to generate fallback image: {exc}')
        return None


def build_image_prompt(subject: str, body: str, body_format: str) -> str:
    body_text = html_to_text(body) if body_format == 'html' else body
    body_text = re.sub(r'\s+', ' ', body_text or '').strip()
    excerpt = body_text[:IMAGE_PROMPT_MAX_CHARS]
    parts = [
        'Create a striking editorial cover illustration for a personal blog post.',
        'No words, letters, logos, or watermarks in the image.',
        'Use a cinematic but warm style with a hopeful tone.',
        f'Title: {subject}.',
    ]
    if excerpt:
        parts.append(f'Post summary: {excerpt}.')
    return ' '.join(parts)


def generate_ai_image(slug: str, subject: str, body: str, body_format: str) -> Optional[Path]:
    if not OPENAI_API_KEY:
        return None

    payload = {
        'model': OPENAI_IMAGE_MODEL,
        'prompt': build_image_prompt(subject, body, body_format),
        'size': OPENAI_IMAGE_SIZE,
    }
    request = urllib_request.Request(
        'https://api.openai.com/v1/images/generations',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib_request.urlopen(request, timeout=OPENAI_IMAGE_TIMEOUT) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib_error.HTTPError as exc:
        details = exc.read().decode('utf-8', errors='ignore').strip()
        log(f'AI image generation failed ({exc.code}): {details[:240]}')
        return None
    except Exception as exc:
        log(f'AI image generation failed: {exc}')
        return None

    image_items = data.get('data') or []
    if not image_items:
        log('AI image generation returned no images.')
        return None

    image_item = image_items[0]
    image_bytes = b''
    if image_item.get('b64_json'):
        try:
            image_bytes = base64.b64decode(image_item['b64_json'])
        except Exception as exc:
            log(f'Failed to decode AI image payload: {exc}')
            return None
    elif image_item.get('url'):
        try:
            with urllib_request.urlopen(image_item['url'], timeout=OPENAI_IMAGE_TIMEOUT) as response:
                image_bytes = response.read()
        except Exception as exc:
            log(f'Failed to download AI image: {exc}')
            return None

    if not image_bytes:
        log('AI image generation returned an empty image payload.')
        return None

    dest_dir = STATIC_MEDIA_DIR / slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / 'cover.png'
    dest.write_bytes(image_bytes)
    return dest


def compose_post(
    subject: str,
    slug: str,
    body: str,
    body_format: str,
    sender: str,
    images: List[Path],
    draft: bool,
) -> str:
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    safe_subject = subject.replace('"', "'")
    markup_value = "html" if body_format == "html" else "markdown"
    body_format_value = body_format if body_format in {"html", "markdown"} else "markdown"
    image_line = ''
    if images:
        image_line = f'image = "/media/{slug}/{images[0].name}"\n'
    front_matter = (
        f'+++\n'
        f'title = "{safe_subject}"\n'
        f'date = {timestamp}\n'
        f'draft = {"true" if draft else "false"}\n'
        f'tags = ["email-post"]\n'
        f'categories = ["blog"]\n'
        f'slug = "{slug}"\n'
        f'markup = "{markup_value}"\n'
        f'body_format = "{body_format_value}"\n'
        f'{image_line}'
        f'+++\n'
    )

    sections: List[str] = []
    if body:
        sections.append(body.strip())
    if images:
        if body_format == 'html':
            image_markup = [
                f'<p><img src="/media/{slug}/{img.name}" alt="{html.escape(img.stem)}"></p>' for img in images
            ]
            sections.append('\n'.join(image_markup))
        else:
            image_markdown = [
                f'![{img.stem}](/media/{slug}/{img.name})' for img in images
            ]
            sections.append('\n\n'.join(image_markdown))

    if body_format == 'html':
        sections.append(f'<hr><p><em>Post created via email from {html.escape(sender)}</em></p>')
    else:
        sections.append(f'---\n*Post created via email from {sender}*')
    return front_matter + '\n\n' + '\n\n'.join(section for section in sections if section).strip() + '\n'


def move_to_cur(message_path: Path) -> None:
    destination = CUR_DIR / message_path.name
    try:
        message_path.rename(destination)
    except Exception:
        CUR_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(message_path), str(destination))


def load_post_token() -> str:
    if POST_TOKEN_ENV:
        return POST_TOKEN_ENV
    if TOKEN_FILE.exists():
        try:
            return TOKEN_FILE.read_text(encoding='utf-8').strip()
        except Exception as exc:
            log(f'Failed to read token file {TOKEN_FILE}: {exc}')
    return ''


def token_marker(token: str) -> str:
    return f'{POST_TOKEN_MARKER}{token}'


def has_post_token(subject: str, body: str, token: str) -> bool:
    marker = token_marker(token)
    return marker in subject or marker in body


def strip_post_token(value: str, token: str) -> str:
    marker = token_marker(token)
    if not value:
        return value
    cleaned = value.replace(marker, '').strip()
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned


def html_to_text(value: str) -> str:
    parser = HTMLToText()
    parser.feed(value)
    return parser.get_text()


def recipient_allowed(message: EmailMessage) -> bool:
    if not REQUIRE_TO_ADDRESS:
        return True

    raw_headers: List[str] = []
    for name in ('X-Original-To', 'Delivered-To', 'To', 'Cc'):
        raw_headers.extend(message.get_all(name, []))

    for _, address in getaddresses(raw_headers):
        if address and address.lower() == REQUIRE_TO_ADDRESS:
            return True
    return False


def authentication_results_pass(message: EmailMessage) -> bool:
    auth_headers = [h.lower() for h in message.get_all('Authentication-Results', []) if h]
    if not auth_headers:
        return False

    combined = ' ; '.join(auth_headers)
    dmarc_pass = 'dmarc=pass' in combined
    spf_pass = 'spf=pass' in combined
    dkim_pass = 'dkim=pass' in combined
    return dmarc_pass and (spf_pass or dkim_pass)


def blocked_received_host(message: EmailMessage) -> Optional[str]:
    if not BLOCKED_RECEIVED_HOSTS:
        return None
    for received in message.get_all('Received', []):
        lowered = received.lower()
        for host in BLOCKED_RECEIVED_HOSTS:
            if host in lowered:
                return host
    return None


def rebuild_site() -> bool:
    log('Rebuilding site with Hugo...')
    try:
        subprocess.run(
            [HUGO_BIN, '--minify', '--cleanDestinationDir'],
            cwd=BLOG_DIR,
            check=True,
        )
        log('Hugo build complete.')
        return True
    except FileNotFoundError:
        log('Hugo binary not found on PATH.')
    except subprocess.CalledProcessError as exc:
        log(f'Hugo build failed: {exc}')
    return False


def send_notification(recipient: str, title: str, slug: str) -> None:
    if not SEND_NOTIFICATIONS or not recipient:
        return
    try:
        url = f'{BASE_URL}/posts/{slug.strip("/")}/'
        msg = EmailMessage()
        msg['Subject'] = f'[Emino Blog] Published: {title}'
        msg['From'] = NOTIFY_FROM
        msg['To'] = recipient
        msg.set_content(
            f'Hi,\n\nYour email titled "{title}" was published successfully.\n'
            f'You can view it here: {url}\n\n'
            'Karibu,\nEmino Blog'
        )
        subprocess.run(
            [SENDMAIL_BIN, '-t', '-i'],
            input=msg.as_bytes(),
            check=True,
        )
        log(f'Sent notification to {recipient}')
    except FileNotFoundError:
        log('sendmail binary not found; notification skipped.')
    except subprocess.CalledProcessError as exc:
        log(f'Failed to send notification: {exc}')


def git_sync(titles: Sequence[str], include_public: bool = True) -> None:
    if SKIP_GIT:
        log('EMINO_SKIP_GIT=1, skipping git add/commit/push.')
        return
    try:
        add_paths = ['content/posts']
        if include_public:
            add_paths.append('public')
        if STATIC_MEDIA_DIR.exists():
            add_paths.append('static/media')

        subprocess.run(['git', 'add', '-A', *add_paths], cwd=BLOG_DIR, check=True)
        staged = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            cwd=BLOG_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        if not staged.stdout.strip():
            log('No git changes to commit.')
            return

        commit_message = 'Email post: ' + '; '.join(titles)
        subprocess.run(['git', 'commit', '-m', commit_message], cwd=BLOG_DIR, check=True)
        subprocess.run(['git', 'push', 'origin', GIT_BRANCH], cwd=BLOG_DIR, check=True)
        log('Committed and pushed email post(s) to GitHub.')
    except FileNotFoundError:
        log('git not available, skipping push.')
    except subprocess.CalledProcessError as exc:
        log(f'Git command failed: {exc}')


def process_maildir() -> Tuple[Sequence[str], Sequence[str]]:
    if not NEW_DIR.exists():
        log(f'Maildir path not found: {NEW_DIR}')
        return [], []

    messages = sorted(p for p in NEW_DIR.iterdir() if p.is_file())
    if not messages:
        log('No new emails found.')
        return [], []

    authorized = set(load_authorized_senders())
    log(f'Authorized senders: {", ".join(sorted(authorized))}')

    if REQUIRE_TITLE_MARKER and not TITLE_MARKER:
        log('EMINO_REQUIRE_TITLE_MARKER=1 but no EMINO_POST_TITLE_MARKER is configured; refusing to publish.')
        return [], []

    post_token = load_post_token() if REQUIRE_POST_TOKEN else ''
    if REQUIRE_POST_TOKEN and not post_token:
        log(f'EMINO_REQUIRE_POST_TOKEN=1 but no token configured at {TOKEN_FILE}; refusing to publish.')
        return [], []

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    created_titles: List[str] = []
    published_titles: List[str] = []

    for message_path in messages:
        log(f'Processing {message_path.name}...')
        try:
            with message_path.open('rb') as handle:
                message = email.message_from_binary_file(handle, policy=policy.default)
        except Exception as exc:
            log(f'Failed to parse {message_path.name}: {exc}')
            move_to_cur(message_path)
            continue

        if not recipient_allowed(message):
            log(f'Skipping message not addressed to required recipient: {REQUIRE_TO_ADDRESS}')
            move_to_cur(message_path)
            continue

        blocked_host = blocked_received_host(message)
        if blocked_host:
            log(f'Skipping message relayed via blocked host: {blocked_host}')
            move_to_cur(message_path)
            continue

        sender = parseaddr(message.get('From', ''))[1].lower()
        if not sender or sender not in authorized:
            log(f'Skipping unauthorized sender: {sender or "unknown"}')
            move_to_cur(message_path)
            continue

        if REQUIRE_DMARC_PASS and not authentication_results_pass(message):
            log(f'Skipping sender failing Authentication-Results checks: {sender}')
            move_to_cur(message_path)
            continue

        subject = decode_header_value(message.get('Subject', 'Untitled Post')).strip() or 'Untitled Post'
        body, body_format = extract_body(message)

        title_has_marker = has_title_marker(subject, TITLE_MARKER) if TITLE_MARKER else False
        publish_now = title_has_marker or not REQUIRE_TITLE_MARKER
        if title_has_marker:
            subject = strip_title_marker(subject, TITLE_MARKER).strip() or 'Untitled Post'

        token_body = html_to_text(body) if body_format == 'html' else body
        if REQUIRE_POST_TOKEN and post_token:
            if not has_post_token(subject, token_body, post_token):
                log('Skipping message without valid post token marker.')
                move_to_cur(message_path)
                continue
            subject = strip_post_token(subject, post_token).strip() or 'Untitled Post'
            body = strip_post_token(body, post_token)

        slug = slugify(subject)[:60]
        images = save_images(message, slug)
        if not images and AUTO_GENERATE_IMAGE:
            generated = generate_ai_image(slug, subject, body, body_format)
            if generated:
                images = [generated]
                log(f'Generated AI image {generated.relative_to(BLOG_DIR)}')
            else:
                generated = generate_fallback_image(slug, subject)
                if generated:
                    images = [generated]
                    log(f'Generated fallback image {generated.relative_to(BLOG_DIR)}')

        if not body and not images:
            log(f'Email "{subject}" has no content, skipping.')
            move_to_cur(message_path)
            continue

        timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        filename = f'{timestamp}-{slug}.md'
        post_path = CONTENT_DIR / filename

        post_content = compose_post(subject, slug, body, body_format, sender, images, draft=not publish_now)
        post_path.write_text(post_content, encoding='utf-8')
        if publish_now:
            log(f'Created published post {post_path.relative_to(BLOG_DIR)}')
            published_titles.append(subject)
        else:
            log(f'Created draft post awaiting admin approval: {post_path.relative_to(BLOG_DIR)}')

        created_titles.append(subject)
        move_to_cur(message_path)
        if publish_now:
            send_notification(sender, subject, slug)

    return created_titles, published_titles


def main() -> None:
    log(f'=== Email Check at {datetime.now().isoformat()} ===')
    created, published = process_maildir()
    if not created:
        return

    if published:
        if rebuild_site():
            git_sync(created, include_public=True)
    else:
        git_sync(created, include_public=False)
    log(f'Processed {len(created)} email(s).')


if __name__ == '__main__':
    main()
