#!/usr/bin/env python3
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
import subprocess
import os
import hashlib
import re
import shutil
from functools import wraps
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

app = Flask(__name__)
app.secret_key = 'emino-blog-admin-secret-key-2025'

DEFAULT_PASSWORD_HASH = '28a50563c90c22e9296fcbf5fae2fb6d9229ebab38e2a981db44ded694fd2d27'

BASE_DIR = Path(os.environ.get('EMINO_BLOG_DIR', Path(__file__).resolve().parent))
MAIL_SCRIPT = Path(os.environ.get('EMINO_MAIL_SCRIPT', BASE_DIR / 'scripts' / 'process_maildir.py'))
SYNC_SCRIPT = Path(os.environ.get('EMINO_SYNC_SCRIPT', BASE_DIR / 'scripts' / 'sync_from_github.sh'))
HUGO_BIN = os.environ.get('EMINO_HUGO_BIN', 'hugo')
EMAIL_LOG_PATH = Path(os.environ.get('EMINO_EMAIL_LOG', '/var/log/email_processing.log'))
SYNC_LOG_PATH = Path(os.environ.get('EMINO_SYNC_LOG', '/var/log/github-sync.log'))
POSTS_DIR = Path(os.environ.get('EMINO_POSTS_DIR', BASE_DIR / 'content' / 'posts'))
TRASH_POSTS_DIR = Path(os.environ.get('EMINO_POSTS_TRASH', BASE_DIR / '.admin-trash' / 'posts'))
STATIC_MEDIA_DIR = Path(os.environ.get('EMINO_STATIC_MEDIA_DIR', BASE_DIR / 'static' / 'media'))
GIT_BRANCH = os.environ.get('EMINO_GIT_BRANCH', 'main')
SKIP_GIT = os.environ.get('EMINO_SKIP_GIT') == '1'
ADMIN_PASSWORD_ENV = os.environ.get('EMINO_ADMIN_PASSWORD', '').strip()
ADMIN_PASSWORD_HASH_ENV = os.environ.get('EMINO_ADMIN_PASSWORD_HASH', '').strip().lower()
ADMIN_PASSWORD_HASH_FILE = Path(
    os.environ.get('EMINO_ADMIN_PASSWORD_HASH_FILE', '/etc/emino-blog-admin-password.sha256')
)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def load_password_hash() -> str:
    if ADMIN_PASSWORD_ENV:
        return hashlib.sha256(ADMIN_PASSWORD_ENV.encode('utf-8')).hexdigest()
    if len(ADMIN_PASSWORD_HASH_ENV) == 64:
        return ADMIN_PASSWORD_HASH_ENV
    if ADMIN_PASSWORD_HASH_FILE.exists():
        try:
            candidate = ADMIN_PASSWORD_HASH_FILE.read_text(encoding='utf-8').strip().lower()
            if len(candidate) == 64:
                return candidate
        except Exception:
            pass
    return DEFAULT_PASSWORD_HASH


def verify_password(password: str) -> bool:
    return hashlib.sha256(password.encode('utf-8')).hexdigest() == load_password_hash()


def _parse_post_title(post_path: Path) -> str:
    try:
        with post_path.open('r', encoding='utf-8', errors='ignore') as handle:
            for _ in range(40):
                line = handle.readline()
                if not line:
                    break
                stripped = line.strip()
                m_colon = re.match(r'^\s*title\s*:\s*["\']?(.*?)["\']?\s*$', stripped, flags=re.IGNORECASE)
                if m_colon:
                    return m_colon.group(1).strip() or post_path.stem
                m_equal = re.match(r'^\s*title\s*=\s*["\'](.*?)["\']\s*$', stripped, flags=re.IGNORECASE)
                if m_equal:
                    return m_equal.group(1).strip() or post_path.stem
    except Exception:
        pass
    return post_path.stem


def _parse_front_matter_value(post_path: Path, key: str) -> str:
    patterns = [
        re.compile(rf'^\s*{re.escape(key)}\s*:\s*["\']?(.*?)["\']?\s*$', flags=re.IGNORECASE),
        re.compile(rf'^\s*{re.escape(key)}\s*=\s*["\'](.*?)["\']\s*$', flags=re.IGNORECASE),
    ]
    try:
        with post_path.open('r', encoding='utf-8', errors='ignore') as handle:
            for _ in range(60):
                line = handle.readline()
                if not line:
                    break
                stripped = line.strip()
                for pattern in patterns:
                    match = pattern.match(stripped)
                    if match:
                        return match.group(1).strip()
    except Exception:
        pass
    return ''


def _post_slug(post_path: Path) -> str:
    slug = _parse_front_matter_value(post_path, 'slug')
    if slug:
        return slug.strip('/')

    image_value = _parse_front_matter_value(post_path, 'image')
    if image_value:
        match = re.search(r'/media/([^/]+)/', image_value)
        if match:
            return match.group(1)

    return re.sub(r'^\d{4}-\d{2}-\d{2}-\d{6}-', '', post_path.stem)


def list_posts(limit: int = 200):
    if not POSTS_DIR.exists():
        return []

    posts = []
    for post_path in sorted(POSTS_DIR.glob('*.md'), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = post_path.stat()
        posts.append({
            'path': str(post_path.relative_to(POSTS_DIR)),
            'title': _parse_post_title(post_path),
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'size_kb': round(stat.st_size / 1024, 1),
        })
        if len(posts) >= max(1, min(limit, 1000)):
            break
    return posts


def resolve_post_path(raw_path: str) -> Path:
    if not raw_path:
        raise ValueError('Missing post path')

    rel = Path(raw_path.strip())
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Invalid post path')
    if rel.suffix.lower() != '.md':
        raise ValueError('Only .md posts can be modified')

    posts_root = POSTS_DIR.resolve()
    resolved = (posts_root / rel).resolve()
    if posts_root not in resolved.parents:
        raise ValueError('Invalid post path')
    return resolved


def run_hugo_build(timeout_sec: int = 120):
    try:
        result = subprocess.run(
            [HUGO_BIN, '--minify', '--cleanDestinationDir'],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            cwd=BASE_DIR,
        )
    except Exception as e:
        return False, str(e)

    output = (result.stdout or '') + (result.stderr or '')
    if not output.strip():
        output = 'Hugo build finished.'
    return result.returncode == 0, output


def run_git_publish(commit_message: str, add_paths) -> Tuple[bool, str]:
    if SKIP_GIT:
        return True, 'EMINO_SKIP_GIT=1, skipping git commit/push.'

    try:
        subprocess.run(['git', 'add', '-A', *add_paths], cwd=BASE_DIR, check=True)
        staged = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        if not staged.stdout.strip():
            return True, 'No staged git changes to commit.'

        subprocess.run(['git', 'commit', '-m', commit_message], cwd=BASE_DIR, check=True)
        subprocess.run(['git', 'push', 'origin', GIT_BRANCH], cwd=BASE_DIR, check=True)
        return True, f'Committed and pushed: {commit_message}'
    except Exception as exc:
        return False, str(exc)

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Emino Blog Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 1000px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
            text-align: center;
        }
        .button-group {
            display: flex;
            flex-direction: column;
            gap: 20px;
            margin-bottom: 30px;
        }
        .btn {
            padding: 15px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn:hover {
            background: #764ba2;
            transform: translateY(-2px);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .output {
            background: #f5f5f5;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 14px;
            white-space: pre-wrap;
            display: none;
        }
        .output.show {
            display: block;
        }
        .stats {
            background: #e8f4f8;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .loading {
            display: none;
            text-align: center;
            color: #667eea;
        }
        .loading.show {
            display: block;
        }
        .logout {
            text-align: center;
            margin-top: 20px;
        }
        .logout a {
            color: #667eea;
            text-decoration: none;
        }
        .password-form {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .password-form input {
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
        }
        .password-form input:focus {
            outline: none;
            border-color: #667eea;
        }
        .error {
            color: #e74c3c;
            text-align: center;
            margin-top: 10px;
        }
        .post-manager {
            margin-top: 20px;
            padding: 20px;
            border-radius: 12px;
            background: #f8f9fb;
        }
        .post-manager h2 {
            margin-bottom: 10px;
            color: #333;
        }
        .post-toolbar {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .post-toolbar input {
            flex: 1;
            min-width: 220px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        .posts-list {
            max-height: 240px;
            overflow-y: auto;
            background: white;
            border: 1px solid #e1e1e1;
            border-radius: 10px;
        }
        .post-row {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 12px;
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }
        .post-row:last-child {
            border-bottom: none;
        }
        .post-title {
            font-weight: 600;
            margin-bottom: 4px;
            color: #1f2937;
        }
        .post-meta {
            color: #6b7280;
            font-size: 12px;
        }
        .post-actions {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .btn-small {
            padding: 8px 12px;
            font-size: 13px;
            border-radius: 8px;
        }
        .btn-secondary {
            background: #4b5563;
        }
        .btn-danger {
            background: #dc2626;
        }
        .btn-danger:hover {
            background: #b91c1c;
        }
        .editor {
            margin-top: 16px;
            background: white;
            border-radius: 10px;
            border: 1px solid #e1e1e1;
            padding: 14px;
        }
        .editor h3 {
            margin-bottom: 8px;
        }
        .editor-meta {
            margin-bottom: 10px;
            color: #4b5563;
            font-family: monospace;
            font-size: 12px;
            word-break: break-all;
        }
        .editor textarea {
            width: 100%;
            min-height: 320px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-family: monospace;
            font-size: 13px;
            padding: 10px;
            resize: vertical;
        }
        .editor-actions {
            display: flex;
            gap: 10px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        .muted {
            color: #6b7280;
            font-size: 13px;
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        {% if not logged_in %}
        <h1>🔐 Admin Login</h1>
        <form class="password-form" method="POST" action="/admin/login">
            <input type="password" name="password" placeholder="Enter password" required>
            <button type="submit" class="btn">Login</button>
        </form>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        {% else %}
        <h1>📊 Emino Blog Admin</h1>
        
        <div class="stats">
            <div class="stat-item">
                <strong>Status:</strong>
                <span id="status">Loading...</span>
            </div>
            <div class="stat-item">
                <strong>Last Email Check:</strong>
                <span id="last-email">Loading...</span>
            </div>
            <div class="stat-item">
                <strong>Last GitHub Sync:</strong>
                <span id="last-sync">Loading...</span>
            </div>
        </div>
        
        <div class="button-group">
            <button class="btn" onclick="checkEmails()">
                📧 Check Emails & Create Posts
            </button>
            <button class="btn" onclick="syncGitHub()">
                🔄 Sync from GitHub
            </button>
            <button class="btn" onclick="rebuildSite()">
                🏗️ Rebuild Hugo Site
            </button>
            <button class="btn" onclick="viewLogs()">
                📋 View Recent Logs
            </button>
        </div>
        
        <div class="loading">
            <p>⏳ Processing...</p>
        </div>

        <div class="post-manager">
            <h2>Posts</h2>
            <p class="muted">Edit, save, or delete posts. Delete moves files to admin trash and rebuilds site.</p>
            <div class="post-toolbar">
                <input id="post-search" type="text" placeholder="Search by title or filename..." oninput="filterPosts()">
                <button class="btn btn-secondary btn-small" onclick="loadPosts()">Refresh Posts</button>
            </div>
            <div class="posts-list" id="posts-list">Loading posts...</div>

            <div class="editor">
                <h3>Post Editor</h3>
                <div class="editor-meta" id="editor-path">No post selected</div>
                <textarea id="post-editor" placeholder="Select a post above to edit"></textarea>
                <div class="editor-actions">
                    <button class="btn btn-small" onclick="saveCurrentPost()">Save Post</button>
                    <button class="btn btn-danger btn-small" onclick="deleteCurrentPost()">Delete Post</button>
                </div>
            </div>
        </div>

        <div class="output" id="output"></div>
        
        <div class="logout">
            <a href="/admin/logout">Logout</a>
        </div>
        
        <script>
            let allPosts = [];
            let currentPostPath = "";

            function showOutput(text) {
                const output = document.getElementById("output");
                output.textContent = text;
                output.classList.add("show");
            }
            
            function setLoading(loading) {
                document.querySelector(".loading").classList.toggle("show", loading);
                document.querySelectorAll(".btn").forEach(btn => btn.disabled = loading);
            }
            
            async function checkEmails() {
                setLoading(true);
                try {
                    const response = await fetch("/admin/check-emails", { method: "POST" });
                    const data = await response.json();
                    showOutput(data.output);
                    updateStats();
                } catch (error) {
                    showOutput("Error: " + error.message);
                }
                setLoading(false);
            }
            
            async function syncGitHub() {
                setLoading(true);
                try {
                    const response = await fetch("/admin/sync-github", { method: "POST" });
                    const data = await response.json();
                    showOutput(data.output);
                    updateStats();
                } catch (error) {
                    showOutput("Error: " + error.message);
                }
                setLoading(false);
            }
            
            async function rebuildSite() {
                setLoading(true);
                try {
                    const response = await fetch("/admin/rebuild", { method: "POST" });
                    const data = await response.json();
                    showOutput(data.output);
                } catch (error) {
                    showOutput("Error: " + error.message);
                }
                setLoading(false);
            }
            
            async function viewLogs() {
                setLoading(true);
                try {
                    const response = await fetch("/admin/logs");
                    const data = await response.json();
                    showOutput(data.logs);
                } catch (error) {
                    showOutput("Error: " + error.message);
                }
                setLoading(false);
            }
            
            function escapeHtml(value) {
                return (value || "").replace(/[&<>"']/g, function(ch) {
                    return ({
                        "&": "&amp;",
                        "<": "&lt;",
                        ">": "&gt;",
                        '"': "&quot;",
                        "'": "&#39;"
                    })[ch];
                });
            }

            function renderPosts(posts) {
                const list = document.getElementById("posts-list");
                if (!posts.length) {
                    list.innerHTML = '<div class="post-row"><div>No posts found.</div></div>';
                    return;
                }

                list.innerHTML = posts.map(post => {
                    const title = escapeHtml(post.title || post.path);
                    const path = escapeHtml(post.path);
                    const modified = escapeHtml(post.modified || "");
                    const size = escapeHtml(String(post.size_kb || 0));
                    const encodedPath = encodeURIComponent(post.path);
                    return `
                        <div class="post-row">
                            <div>
                                <div class="post-title">${title}</div>
                                <div class="post-meta">${path} | ${modified} | ${size} KB</div>
                            </div>
                            <div class="post-actions">
                                <button class="btn btn-small" onclick="openPost(decodeURIComponent('${encodedPath}'))">Edit</button>
                                <button class="btn btn-danger btn-small" onclick="deletePost(decodeURIComponent('${encodedPath}'))">Delete</button>
                            </div>
                        </div>
                    `;
                }).join("");
            }

            function filterPosts() {
                const query = document.getElementById("post-search").value.toLowerCase().trim();
                if (!query) {
                    renderPosts(allPosts);
                    return;
                }
                const filtered = allPosts.filter(post =>
                    (post.title || "").toLowerCase().includes(query) ||
                    (post.path || "").toLowerCase().includes(query)
                );
                renderPosts(filtered);
            }

            async function loadPosts() {
                setLoading(true);
                try {
                    const response = await fetch("/admin/posts");
                    const data = await response.json();
                    allPosts = data.posts || [];
                    filterPosts();
                } catch (error) {
                    showOutput("Failed to load posts: " + error.message);
                }
                setLoading(false);
            }

            async function openPost(path) {
                setLoading(true);
                try {
                    const response = await fetch("/admin/post?path=" + encodeURIComponent(path));
                    const data = await response.json();
                    if (!response.ok || !data.success) {
                        throw new Error(data.output || "Failed to load post");
                    }
                    currentPostPath = data.path;
                    document.getElementById("editor-path").textContent = data.path;
                    document.getElementById("post-editor").value = data.content || "";
                } catch (error) {
                    showOutput("Failed to open post: " + error.message);
                }
                setLoading(false);
            }

            async function saveCurrentPost() {
                if (!currentPostPath) {
                    showOutput("Select a post first.");
                    return;
                }
                setLoading(true);
                try {
                    const response = await fetch("/admin/save-post", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            path: currentPostPath,
                            content: document.getElementById("post-editor").value,
                            rebuild: true
                        })
                    });
                    const data = await response.json();
                    showOutput(data.output || "Saved.");
                    await loadPosts();
                } catch (error) {
                    showOutput("Failed to save post: " + error.message);
                }
                setLoading(false);
            }

            async function deletePost(path) {
                if (!confirm("Delete this post? It will be moved to admin trash.")) {
                    return;
                }
                setLoading(true);
                try {
                    const response = await fetch("/admin/delete-post", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ path: path, rebuild: true })
                    });
                    const data = await response.json();
                    showOutput(data.output || "Deleted.");
                    if (currentPostPath === path) {
                        currentPostPath = "";
                        document.getElementById("editor-path").textContent = "No post selected";
                        document.getElementById("post-editor").value = "";
                    }
                    await loadPosts();
                } catch (error) {
                    showOutput("Failed to delete post: " + error.message);
                }
                setLoading(false);
            }

            function deleteCurrentPost() {
                if (!currentPostPath) {
                    showOutput("Select a post first.");
                    return;
                }
                deletePost(currentPostPath);
            }

            async function updateStats() {
                try {
                    const response = await fetch("/admin/stats");
                    const data = await response.json();
                    document.getElementById("status").textContent = data.status;
                    document.getElementById("last-email").textContent = data.last_email;
                    document.getElementById("last-sync").textContent = data.last_sync;
                } catch (error) {
                    console.error("Failed to update stats", error);
                }
            }
            
            // Update stats on load
            updateStats();
            // Load posts on page load
            loadPosts();
            // Auto-update every 30 seconds
            setInterval(updateStats, 30000);
        </script>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/admin')
def admin():
    return render_template_string(ADMIN_TEMPLATE, logged_in='logged_in' in session)

@app.route('/admin/login', methods=['POST'])
def login():
    password = request.form.get('password', '')
    if verify_password(password):
        session['logged_in'] = True
        return redirect('/admin')
    return render_template_string(ADMIN_TEMPLATE, logged_in=False, error='Invalid password')

@app.route('/admin/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/admin')

@app.route('/admin/check-emails', methods=['POST'])
@login_required
def check_emails():
    try:
        result = subprocess.run(
            ['python3', str(MAIL_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=BASE_DIR
        )
        output = result.stdout + result.stderr
        return jsonify({'success': True, 'output': output})
    except Exception as e:
        return jsonify({'success': False, 'output': str(e)})

@app.route('/admin/sync-github', methods=['POST'])
@login_required
def sync_github():
    try:
        result = subprocess.run(
            [str(SYNC_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=90,
            cwd=BASE_DIR
        )
        output = result.stdout + result.stderr
        return jsonify({'success': True, 'output': output})
    except Exception as e:
        return jsonify({'success': False, 'output': str(e)})

@app.route('/admin/rebuild', methods=['POST'])
@login_required
def rebuild():
    ok, output = run_hugo_build(timeout_sec=120)
    return jsonify({'success': ok, 'output': output})


@app.route('/admin/posts')
@login_required
def posts():
    limit_raw = request.args.get('limit', '200')
    try:
        limit = int(limit_raw)
    except ValueError:
        limit = 200
    return jsonify({'posts': list_posts(limit=limit)})


@app.route('/admin/post')
@login_required
def get_post():
    try:
        raw_path = request.args.get('path', '')
        post_path = resolve_post_path(raw_path)
        if not post_path.exists():
            return jsonify({'success': False, 'output': 'Post not found'}), 404
        content = post_path.read_text(encoding='utf-8', errors='ignore')
        return jsonify({'success': True, 'path': str(post_path.relative_to(POSTS_DIR)), 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'output': str(e)}), 400


@app.route('/admin/save-post', methods=['POST'])
@login_required
def save_post():
    try:
        payload = request.get_json(silent=True) or {}
        raw_path = payload.get('path', '')
        content = payload.get('content')
        rebuild_after = payload.get('rebuild', True)

        if not isinstance(content, str):
            return jsonify({'success': False, 'output': 'Missing or invalid post content'}), 400

        post_path = resolve_post_path(raw_path)
        if not post_path.exists():
            return jsonify({'success': False, 'output': 'Post not found'}), 404

        post_path.write_text(content, encoding='utf-8')
        output_lines = [f'Saved {post_path.relative_to(BASE_DIR)}']

        if rebuild_after:
            ok, build_output = run_hugo_build(timeout_sec=120)
            output_lines.append('\nHugo rebuild:')
            output_lines.append(build_output)
            if not ok:
                return jsonify({'success': False, 'output': '\n'.join(output_lines)})
            git_ok, git_output = run_git_publish(
                f'Admin edit post: {_parse_post_title(post_path)}',
                ['content/posts', 'public', 'static/media'],
            )
            output_lines.append('\nGit publish:')
            output_lines.append(git_output)
            return jsonify({'success': ok and git_ok, 'output': '\n'.join(output_lines)})

        return jsonify({'success': True, 'output': '\n'.join(output_lines)})
    except Exception as e:
        return jsonify({'success': False, 'output': str(e)}), 400


@app.route('/admin/delete-post', methods=['POST'])
@login_required
def delete_post():
    try:
        payload = request.get_json(silent=True) or {}
        raw_path = payload.get('path', '')
        rebuild_after = payload.get('rebuild', True)

        post_path = resolve_post_path(raw_path)
        if not post_path.exists():
            return jsonify({'success': False, 'output': 'Post not found'}), 404

        media_slug = _post_slug(post_path)
        media_dir = STATIC_MEDIA_DIR / media_slug if media_slug else None
        TRASH_POSTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        destination = TRASH_POSTS_DIR / f'{post_path.stem}.deleted.{timestamp}{post_path.suffix}'
        index = 1
        while destination.exists():
            destination = TRASH_POSTS_DIR / f'{post_path.stem}.deleted.{timestamp}.{index}{post_path.suffix}'
            index += 1

        post_path.rename(destination)
        output_lines = [
            f'Moved {post_path.relative_to(BASE_DIR)}',
            f'Trash: {destination.relative_to(BASE_DIR)}',
        ]
        if media_dir and media_dir.exists():
            shutil.rmtree(media_dir)
            output_lines.append(f'Removed {media_dir.relative_to(BASE_DIR)}')

        if rebuild_after:
            ok, build_output = run_hugo_build(timeout_sec=120)
            output_lines.append('\nHugo rebuild:')
            output_lines.append(build_output)
            if not ok:
                return jsonify({'success': False, 'output': '\n'.join(output_lines)})
            git_ok, git_output = run_git_publish(
                f'Admin delete post: {_parse_post_title(destination)}',
                ['content/posts', 'public', 'static/media'],
            )
            output_lines.append('\nGit publish:')
            output_lines.append(git_output)
            return jsonify({'success': ok and git_ok, 'output': '\n'.join(output_lines)})

        return jsonify({'success': True, 'output': '\n'.join(output_lines)})
    except Exception as e:
        return jsonify({'success': False, 'output': str(e)}), 400

@app.route('/admin/logs')
@login_required
def logs():
    try:
        logs = []
        log_files = [
            EMAIL_LOG_PATH,
            SYNC_LOG_PATH
        ]
        for log_file in log_files:
            if log_file.exists():
                result = subprocess.run(
                    ['tail', '-n', '20', str(log_file)],
                    capture_output=True,
                    text=True
                )
                logs.append(f"--- {log_file} ---\n{result.stdout}\n")
        return jsonify({'logs': '\n'.join(logs)})
    except Exception as e:
        return jsonify({'logs': str(e)})

@app.route('/admin/stats')
@login_required
def stats():
    try:
        # Get last email check
        if EMAIL_LOG_PATH.exists():
            email_log = subprocess.run(
                ['tail', '-n', '1', str(EMAIL_LOG_PATH)],
                capture_output=True,
                text=True
            ).stdout.strip()
        else:
            email_log = ''
        
        # Get last GitHub sync
        if SYNC_LOG_PATH.exists():
            sync_log = subprocess.run(
                ['tail', '-n', '1', str(SYNC_LOG_PATH)],
                capture_output=True,
                text=True
            ).stdout.strip()
        else:
            sync_log = ''
        
        return jsonify({
            'status': 'All systems running',
            'last_email': email_log[:50] if email_log else 'No recent activity',
            'last_sync': sync_log[:50] if sync_log else 'No recent activity'
        })
    except Exception as e:
        return jsonify({
            'status': 'Error checking status',
            'last_email': 'Unknown',
            'last_sync': 'Unknown'
        })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
