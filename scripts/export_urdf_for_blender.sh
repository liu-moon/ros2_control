#!/usr/bin/env bash
# Flatten a URDF/XACRO for Blender: expand xacro, rewrite package:// mesh
# URIs to relative paths, and copy mesh + texture files next to the URDF.
#
# Run from the host (repo root or anywhere). Requires docker compose unless
# this script is already running inside the ROS container.
#
# Usage:
#   ./scripts/export_urdf_for_blender.sh
#   ./scripts/export_urdf_for_blender.sh src/urdf_tutorial/urdf/08-macroed.urdf.xacro
#   ./scripts/export_urdf_for_blender.sh src/urdf_tutorial/urdf/01-myfirst.urdf
#
# Output (default):
#   src/urdf_tutorial/blender_export/<name>.urdf
#   src/urdf_tutorial/blender_export/meshes/...
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

INPUT_REL="${1:-src/urdf_tutorial/urdf/08-macroed.urdf.xacro}"
if [[ "$INPUT_REL" = /* ]]; then
  INPUT_ABS="$INPUT_REL"
else
  INPUT_ABS="$ROOT/$INPUT_REL"
fi

if [[ ! -f "$INPUT_ABS" ]]; then
  echo "error: input file not found: $INPUT_ABS" >&2
  exit 1
fi

# src/urdf_tutorial/urdf/08-macroed.urdf.xacro -> 08-macroed.urdf
BASENAME="$(basename "$INPUT_ABS")"
STEM="${BASENAME%.xacro}"
STEM="${STEM%.urdf}"
OUTPUT_DIR="$(dirname "$INPUT_ABS")/../blender_export"
OUTPUT_DIR="$(cd "$(dirname "$OUTPUT_DIR")" && pwd)/$(basename "$OUTPUT_DIR")"
mkdir -p "$OUTPUT_DIR"
OUTPUT_URDF="$OUTPUT_DIR/${STEM}.urdf"

# Host path under src/ <-> container path under /workspace/src/
to_container_path() {
  local abs="$1"
  local rel="${abs#"$ROOT/"}"
  echo "/workspace/$rel"
}

run_xacro() {
  local in_abs="$1"
  local out_abs="$2"
  if command -v xacro >/dev/null 2>&1; then
    # Already in a ROS environment (container shell, or sourced host).
    # Use -o so xacro warnings go to stderr instead of corrupting the URDF.
    xacro "$in_abs" -o "$out_abs"
    return
  fi
  if ! command -v docker >/dev/null 2>&1; then
    echo "error: xacro not on PATH and docker is not available." >&2
    echo "Start the ROS container and re-run, or exec into it first." >&2
    exit 1
  fi
  if ! docker compose ps --status running --services 2>/dev/null | grep -qx ros2_control; then
    echo "Starting ros2_control container..."
    docker compose up -d
  fi
  local in_c out_c
  in_c="$(to_container_path "$in_abs")"
  out_c="$(to_container_path "$out_abs")"
  docker compose exec -T ros2_control bash -lc \
    "source /opt/ros/jazzy/setup.bash && xacro '$in_c' -o '$out_c'"
}

echo "Flattening: $INPUT_ABS"
if [[ "$INPUT_ABS" == *.xacro ]]; then
  run_xacro "$INPUT_ABS" "$OUTPUT_URDF"
else
  cp "$INPUT_ABS" "$OUTPUT_URDF"
fi

python3 - "$ROOT" "$OUTPUT_URDF" "$OUTPUT_DIR" <<'PY'
"""Rewrite package:// mesh URIs and copy mesh/texture files next to the URDF."""
from __future__ import annotations

import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(sys.argv[1])
urdf_path = Path(sys.argv[2])
export_dir = Path(sys.argv[3])
src_root = root / "src"

PACKAGE_URI = re.compile(r"^package://([^/]+)/(.+)$")
TEXTURE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def package_share_dirs() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for pkg_xml in src_root.rglob("package.xml"):
        try:
            tree = ET.parse(pkg_xml)
        except ET.ParseError:
            continue
        name_el = tree.getroot().find("name")
        if name_el is None or not (name_el.text or "").strip():
            continue
        found[name_el.text.strip()] = pkg_xml.parent
    return found


def iter_mesh_filenames(urdf_text: str) -> list[str]:
    names: list[str] = []
    try:
        tree = ET.fromstring(urdf_text)
    except ET.ParseError as exc:
        raise SystemExit(f"error: exported URDF is not valid XML: {exc}") from exc
    for el in tree.iter():
        tag = el.tag.split("}")[-1]
        if tag == "mesh" and el.get("filename"):
            names.append(el.get("filename", ""))
    return names


def copy_with_siblings(src_file: Path, dest_file: Path) -> None:
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_file, dest_file)
    for sibling in src_file.parent.iterdir():
        if not sibling.is_file():
            continue
        if sibling.suffix.lower() not in TEXTURE_EXTS:
            continue
        shutil.copy2(sibling, dest_file.parent / sibling.name)


packages = package_share_dirs()
text = urdf_path.read_text(encoding="utf-8")
replacements: dict[str, str] = {}

for filename in dict.fromkeys(iter_mesh_filenames(text)):
    match = PACKAGE_URI.match(filename)
    if not match:
        continue
    pkg, rel = match.group(1), match.group(2)
    pkg_dir = packages.get(pkg)
    if pkg_dir is None:
        print(f"warning: cannot resolve package://{pkg}/ (not under src/)", file=sys.stderr)
        continue
    src_file = pkg_dir / rel
    if not src_file.is_file():
        print(f"warning: mesh not found: {src_file}", file=sys.stderr)
        continue
    dest_rel = Path(rel)
    dest_file = export_dir / dest_rel
    copy_with_siblings(src_file, dest_file)
    replacements[filename] = dest_rel.as_posix()
    print(f"Copied mesh: {dest_rel.as_posix()}")

for old, new in replacements.items():
    text = text.replace(old, new)

urdf_path.write_text(text, encoding="utf-8")
print(f"Wrote URDF: {urdf_path}")
PY

echo
echo "Next: import into Blender with"
echo "  blender --python scripts/import_urdf.py -- $OUTPUT_URDF"
