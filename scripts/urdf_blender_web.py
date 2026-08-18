#!/usr/bin/env python3
"""Local web UI for exporting URDF/XACRO and opening it in Blender.

    python3 scripts/urdf_blender_web.py

Then open http://127.0.0.1:8765 (the script tries to open a browser itself).
Bound to localhost only — it runs the export/import helpers on this machine.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import webbrowser
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
EXPORT_SCRIPT = ROOT / "scripts" / "export_urdf_for_blender.sh"
IMPORT_SCRIPT = ROOT / "scripts" / "import_urdf.py"
DEFAULT_PORT = 8765
MESH_EXTS = {".dae", ".stl", ".obj", ".glb", ".gltf"}
_XACRO_MACRO_BLOCK = re.compile(
    r"<xacro:macro\b[^>]*>.*?</xacro:macro>",
    re.DOTALL,
)
_XACRO_INSTANTIATE = re.compile(
    r"<xacro:(?!include|macro|property|arg|if|unless|insert_block)\w+"
)
BLENDER_CANDIDATES = (
    Path("/Applications/Blender.app/Contents/MacOS/Blender"),
    Path("/usr/bin/blender"),
    Path("/usr/local/bin/blender"),
)

PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>URDF / meshes → Blender</title>
  <style>
    :root {
      --bg: #0f1419;
      --panel: #1a222c;
      --line: #2a3542;
      --text: #e7eef6;
      --muted: #8b9aab;
      --accent: #3d9cf0;
      --accent-dim: #1d4f7a;
      --ok: #3ecf8e;
      --warn: #e6b84d;
      --bad: #e06c75;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    main {
      max-width: 880px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    h1 { font-size: 1.5rem; font-weight: 650; margin: 0 0 6px; }
    .lead { color: var(--muted); margin: 0 0 24px; }
    .status {
      display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 24px;
    }
    .chip {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 999px;
      padding: 4px 12px;
      font-size: 13px;
      color: var(--muted);
    }
    .chip.ok { color: var(--ok); border-color: #245c43; }
    .chip.bad { color: var(--bad); border-color: #6b2e34; }
    label { display: block; color: var(--muted); font-size: 13px; margin-bottom: 6px; }
    select, button, pre {
      width: 100%;
      border-radius: 10px;
      border: 1px solid var(--line);
    }
    select {
      background: var(--panel);
      color: var(--text);
      padding: 10px 12px;
      font-size: 15px;
    }
    .meta {
      margin: 10px 0 20px;
      color: var(--muted);
      font-size: 13px;
      min-height: 1.5em;
    }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
    button {
      width: auto;
      flex: 1 1 180px;
      padding: 12px 16px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      background: var(--panel);
      color: var(--text);
    }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #061018;
    }
    button:disabled { opacity: 0.5; cursor: wait; }
    button:hover:not(:disabled) { filter: brightness(1.08); }
    pre {
      background: #0b0f13;
      color: #c9d6e3;
      padding: 14px 16px;
      min-height: 180px;
      max-height: 360px;
      overflow: auto;
      white-space: pre-wrap;
      font-size: 12.5px;
    }
    .hint { color: var(--muted); font-size: 13px; margin-top: 16px; }
  </style>
</head>
<body>
<main>
  <h1>URDF / meshes → Blender</h1>
  <p class="lead">选整机或零件库，点按钮即可。不用记命令。</p>
  <div class="status" id="status"></div>
  <label for="model">模型</label>
  <select id="model"></select>
  <div class="meta" id="meta"></div>
  <div class="actions">
    <button class="primary" id="btn-open">导出并打开 Blender</button>
    <button id="btn-export">只导出</button>
    <button id="btn-blend">打开已有 .blend</button>
  </div>
  <label>日志</label>
  <pre id="log">选好模型后点上面的按钮。</pre>
  <p class="hint">Blender 会在本机弹出窗口。若场景里只有立方体，先完全退出 Blender 再点一次「导出并打开 Blender」。零件库导出不需要 Docker。</p>
</main>
<script>
const $ = (id) => document.getElementById(id);
const logEl = $("log");
let models = [];

function log(text) {
  logEl.textContent = text || "(无输出)";
  logEl.scrollTop = logEl.scrollHeight;
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

function selected() {
  return models.find((m) => m.path === $("model").value);
}

function renderStatus(info) {
  const chips = [];
  chips.push(`<span class="chip ${info.docker ? "ok" : "bad"}">Docker ${info.docker ? "已运行" : "未运行"}</span>`);
  chips.push(`<span class="chip ${info.blender ? "ok" : "bad"}">Blender ${info.blender ? "已找到" : "未找到"}</span>`);
  $("status").innerHTML = chips.join("");
}

function kindLabel(m) {
  if (m.kind === "meshes") return "零件库（.dae），不经 Docker";
  if (m.kind === "xacro") return "XACRO，导出时会在 Docker 里展平";
  return "纯 URDF";
}

function optionLabel(m) {
  const prefix = m.kind === "meshes" ? "[零件]" : m.kind === "xacro" ? "[XACRO]" : "[URDF]";
  return prefix + " " + m.path;
}

function renderMeta() {
  const m = selected();
  if (!m) { $("meta").textContent = ""; return; }
  const bits = [kindLabel(m)];
  bits.push(m.exported ? "已有导出文件" : "尚未导出");
  bits.push(m.blend ? "已有 .blend" : "还没有 .blend");
  $("meta").textContent = bits.join(" · ");
  $("btn-blend").disabled = !m.blend;
}

function renderModels() {
  const sel = $("model");
  const prev = sel.value;
  sel.innerHTML = models.map((m) =>
    `<option value="${m.path}">${optionLabel(m)}</option>`
  ).join("");
  const prefer = prev
    || models.find((m) => m.path.includes("robomaster_ep"))?.path
    || models.find((m) => m.path.includes("08-macroed"))?.path;
  if (prefer && models.some((m) => m.path === prefer)) sel.value = prefer;
  renderMeta();
}

async function refresh() {
  const info = await api("/api/status");
  models = info.models;
  renderStatus(info);
  renderModels();
}

async function run(action) {
  const m = selected();
  if (!m) return;
  const buttons = document.querySelectorAll("button");
  buttons.forEach((b) => b.disabled = true);
  log("进行中…");
  try {
    const data = await api("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: m.path, action }),
    });
    log(data.log || "完成");
    await refresh();
  } catch (err) {
    log("出错：\n" + err.message);
  } finally {
    buttons.forEach((b) => b.disabled = false);
    renderMeta();
  }
}

$("model").addEventListener("change", renderMeta);
$("btn-open").addEventListener("click", () => run("open"));
$("btn-export").addEventListener("click", () => run("export"));
$("btn-blend").addEventListener("click", () => run("blend"));
refresh().catch((err) => log("无法连接本地服务：\n" + err.message));
</script>
</body>
</html>
"""


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def find_blender() -> Path | None:
    env = os.environ.get("BLENDER")
    if env:
        candidate = Path(env)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    which = shutil.which("blender")
    if which:
        return Path(which)
    for candidate in BLENDER_CANDIDATES:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def docker_running() -> bool:
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--status", "running", "--services"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and "ros2_control" in result.stdout.split()


def blender_export_dir(source: Path) -> Path:
    if source.is_dir():
        return (source.parent / "blender_export").resolve()
    return (source.parent / ".." / "blender_export").resolve()


def export_artifact(source: Path) -> Path:
    if source.is_dir():
        return blender_export_dir(source) / "meshes_manifest.json"
    stem = source.name.removesuffix(".xacro").removesuffix(".urdf")
    return blender_export_dir(source) / f"{stem}.urdf"


def blend_path_for(source: Path) -> Path:
    if source.is_dir():
        return blender_export_dir(source) / "meshes.blend"
    return export_artifact(source).with_suffix(".blend")


def import_path_for(source: Path) -> Path:
    if source.is_dir():
        return blender_export_dir(source) / "meshes"
    return export_artifact(source)


def is_mesh_dir(path: Path) -> bool:
    if not path.is_dir() or path.name != "meshes":
        return False
    try:
        return any(child.is_file() and child.suffix.lower() in MESH_EXTS for child in path.iterdir())
    except OSError:
        return False


def is_complete_robot(path: Path) -> bool:
    """Skip xacro fragments that only define macros (arm.urdf.xacro, etc.)."""
    if not path.name.endswith(".xacro"):
        return True
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    defines_macros = "<xacro:macro" in text
    stripped = text
    previous = None
    while previous != stripped:
        previous = stripped
        stripped = _XACRO_MACRO_BLOCK.sub("", stripped)
    instantiates = bool(_XACRO_INSTANTIATE.search(stripped))
    if defines_macros and not instantiates:
        return False
    return True


def model_entry(source: Path, kind: str) -> dict:
    exported = export_artifact(source)
    blend = blend_path_for(source)
    return {
        "path": repo_rel(source),
        "kind": kind,
        "exported": exported.is_file(),
        "exported_path": repo_rel(exported) if exported.is_file() else None,
        "blend": blend.is_file(),
        "blend_path": repo_rel(blend) if blend.is_file() else None,
    }


def list_models() -> list[dict]:
    models = []
    src = ROOT / "src"
    if not src.is_dir():
        return models
    for path in sorted(src.rglob("*")):
        if "blender_export" in path.parts:
            continue
        if path.is_dir() and is_mesh_dir(path):
            models.append(model_entry(path, "meshes"))
            continue
        if not path.is_file():
            continue
        if path.suffix == ".urdf" and not path.name.endswith(".xacro"):
            models.append(model_entry(path, "urdf"))
            continue
        if not path.name.endswith(".urdf.xacro"):
            continue
        if not is_complete_robot(path):
            continue
        models.append(model_entry(path, "xacro"))
    return models


def safe_source(rel: str) -> Path:
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        raise ValueError("invalid path")
    path = (ROOT / rel).resolve()
    src_root = (ROOT / "src").resolve()
    if src_root not in path.parents and path != src_root:
        raise ValueError("path must be under src/")
    if "blender_export" in path.parts:
        raise ValueError("pick a source URDF/XACRO or meshes folder, not blender_export")
    if path.is_dir():
        if not is_mesh_dir(path):
            raise ValueError("directory is not a meshes folder")
        return path
    if path.suffix not in {".urdf", ".xacro"} or not path.is_file():
        raise ValueError("not a URDF/XACRO file")
    return path


def run_export(source: Path) -> str:
    result = subprocess.run(
        ["bash", str(EXPORT_SCRIPT), repo_rel(source)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    text = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        raise RuntimeError(text.strip() or f"export failed ({result.returncode})")
    return text.strip()


def spawn_blender(args: list[str]) -> None:
    blender = find_blender()
    if blender is None:
        raise RuntimeError(
            "找不到 Blender。请安装到 /Applications/Blender.app，"
            "或把可执行文件放到 PATH，或设置环境变量 BLENDER。"
        )
    subprocess.Popen(
        [str(blender), *args],
        cwd=ROOT,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def handle_run(payload: dict) -> dict:
    source = safe_source(payload.get("path", ""))
    action = payload.get("action")
    blend = blend_path_for(source)
    imported = import_path_for(source)

    if action == "export":
        log = run_export(source)
        return {"ok": True, "log": log}

    if action == "open":
        log = run_export(source)
        spawn_blender(
            ["--python", str(IMPORT_SCRIPT), "--", str(imported)]
        )
        if source.is_dir():
            log += "\n\n已启动 Blender 导入零件库。稍等窗口出现；Outliner 里应有 meshes 集合。"
        else:
            log += "\n\n已启动 Blender 导入。稍等窗口出现；Outliner 里应有机器人集合。"
        return {"ok": True, "log": log}

    if action == "blend":
        if not blend.is_file():
            raise RuntimeError("还没有 .blend。请先点「导出并打开 Blender」。")
        spawn_blender([str(blend)])
        return {"ok": True, "log": f"正在打开 {repo_rel(blend)}"}

    raise ValueError("unknown action")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict | str, content_type: str = "application/json") -> None:
        data = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
        raw = data.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._send(200, PAGE, "text/html")
            return
        if path == "/api/status":
            blender = find_blender()
            self._send(
                200,
                {
                    "docker": docker_running(),
                    "blender": str(blender) if blender else None,
                    "models": list_models(),
                },
            )
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid JSON"})
            return
        if path != "/api/run":
            self._send(404, {"error": "not found"})
            return
        try:
            self._send(200, handle_run(payload))
        except (ValueError, RuntimeError) as exc:
            self._send(400, {"error": str(exc), "log": str(exc)})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    parser = argparse.ArgumentParser(description="Local URDF / meshes → Blender web UI")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not EXPORT_SCRIPT.is_file():
        sys.exit(f"missing {EXPORT_SCRIPT}")

    host = "127.0.0.1"
    httpd = ThreadingHTTPServer((host, args.port), Handler)
    url = f"http://{host}:{args.port}/"
    print(f"URDF / meshes → Blender UI: {url}", flush=True)
    print("按 Ctrl+C 停止。只监听本机，不会暴露到局域网。", flush=True)
    if not args.no_browser:
        threading.Timer(0.4, partial(webbrowser.open, url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        httpd.server_close()


if __name__ == "__main__":
    main()
