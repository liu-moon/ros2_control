#!/usr/bin/env python3
"""Import a flattened URDF into Blender as a link/joint Empty tree.

Run from Blender (not system Python):

    blender --python scripts/import_urdf.py -- src/urdf_tutorial/blender_export/08-macroed.urdf

Optional:

    blender --python scripts/import_urdf.py -- src/urdf_tutorial/blender_export/08-macroed.urdf --save robot.blend

Each URDF link becomes an Empty; visual geometry is parented to it.
Each URDF joint becomes an Empty between parent and child, locked to the
joint type/axis so you can keyframe wheels, the head, and the gripper.
"""
from __future__ import annotations

import math
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

try:
    import bpy
    from bpy.app.handlers import persistent
    from mathutils import Matrix, Vector
except ImportError:
    sys.exit(
        "Run this script from Blender:\n"
        "  blender --python scripts/import_urdf.py -- path/to/robot.urdf"
    )

Vec3 = Tuple[float, float, float]


def _argv_after_double_dash() -> List[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def parse_vec(text: Optional[str], default: Vec3 = (0.0, 0.0, 0.0)) -> Vec3:
    if not text:
        return default
    parts = [float(p) for p in text.split()]
    if len(parts) != 3:
        raise ValueError(f"expected 3 values, got {text!r}")
    return (parts[0], parts[1], parts[2])


def local_tag(el: ET.Element) -> str:
    return el.tag.split("}")[-1]


def find_child(parent: ET.Element, tag: str) -> Optional[ET.Element]:
    for child in list(parent):
        if local_tag(child) == tag:
            return child
    return None


def find_children(parent: ET.Element, tag: str) -> List[ET.Element]:
    return [child for child in list(parent) if local_tag(child) == tag]


def parse_origin(parent: ET.Element) -> Tuple[Vec3, Vec3]:
    origin = find_child(parent, "origin")
    if origin is None:
        return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    return parse_vec(origin.get("xyz")), parse_vec(origin.get("rpy"))


def rpy_matrix(rpy: Vec3) -> Matrix:
    """URDF RPY: R = Rz(yaw) * Ry(pitch) * Rx(roll)."""
    roll, pitch, yaw = rpy
    cx, sx = math.cos(roll), math.sin(roll)
    cy, sy = math.cos(pitch), math.sin(pitch)
    cz, sz = math.cos(yaw), math.sin(yaw)
    rx = Matrix(((1.0, 0.0, 0.0), (0.0, cx, -sx), (0.0, sx, cx)))
    ry = Matrix(((cy, 0.0, sy), (0.0, 1.0, 0.0), (-sy, 0.0, cy)))
    rz = Matrix(((cz, -sz, 0.0), (sz, cz, 0.0), (0.0, 0.0, 1.0)))
    return rz @ ry @ rx


def origin_matrix(xyz: Vec3, rpy: Vec3) -> Matrix:
    return Matrix.Translation(Vector(xyz)) @ rpy_matrix(rpy).to_4x4()


@dataclass
class Visual:
    xyz: Vec3
    rpy: Vec3
    geom: ET.Element
    material_name: Optional[str] = None
    rgba: Optional[Tuple[float, float, float, float]] = None


@dataclass
class Link:
    name: str
    visuals: List[Visual] = field(default_factory=list)


@dataclass
class Joint:
    name: str
    joint_type: str
    parent: str
    child: str
    xyz: Vec3 = (0.0, 0.0, 0.0)
    rpy: Vec3 = (0.0, 0.0, 0.0)
    axis: Vec3 = (1.0, 0.0, 0.0)
    lower: Optional[float] = None
    upper: Optional[float] = None


@dataclass
class Robot:
    name: str
    links: Dict[str, Link]
    joints: List[Joint]
    materials: Dict[str, Tuple[float, float, float, float]]
    urdf_dir: Path


def parse_rgba(el: Optional[ET.Element]) -> Optional[Tuple[float, float, float, float]]:
    if el is None:
        return None
    color = find_child(el, "color")
    if color is None or not color.get("rgba"):
        return None
    parts = [float(p) for p in color.get("rgba", "").split()]
    if len(parts) != 4:
        return None
    return (parts[0], parts[1], parts[2], parts[3])


def parse_visual(el: ET.Element) -> Optional[Visual]:
    geom = find_child(el, "geometry")
    if geom is None or len(list(geom)) == 0:
        return None
    xyz, rpy = parse_origin(el)
    mat_el = find_child(el, "material")
    material_name = mat_el.get("name") if mat_el is not None else None
    rgba = parse_rgba(mat_el)
    return Visual(
        xyz=xyz,
        rpy=rpy,
        geom=list(geom)[0],
        material_name=material_name or None,
        rgba=rgba,
    )


def parse_urdf(path: Path) -> Robot:
    tree = ET.parse(path)
    root = tree.getroot()
    if local_tag(root) != "robot":
        raise ValueError(f"{path} has no <robot> root")

    materials: Dict[str, Tuple[float, float, float, float]] = {}
    links: Dict[str, Link] = {}
    joints: List[Joint] = []

    for el in list(root):
        tag = local_tag(el)
        if tag == "material":
            name = el.get("name")
            rgba = parse_rgba(el)
            if name and rgba:
                materials[name] = rgba
        elif tag == "link":
            name = el.get("name")
            if not name:
                continue
            link = Link(name=name)
            for vis_el in find_children(el, "visual"):
                visual = parse_visual(vis_el)
                if visual is not None:
                    link.visuals.append(visual)
            links[name] = link
        elif tag == "joint":
            name = el.get("name")
            joint_type = el.get("type", "fixed")
            parent_el = find_child(el, "parent")
            child_el = find_child(el, "child")
            if not name or parent_el is None or child_el is None:
                continue
            xyz, rpy = parse_origin(el)
            axis_el = find_child(el, "axis")
            axis = parse_vec(axis_el.get("xyz") if axis_el is not None else None, (1.0, 0.0, 0.0))
            limit_el = find_child(el, "limit")
            lower = upper = None
            if limit_el is not None:
                if limit_el.get("lower") is not None:
                    lower = float(limit_el.get("lower", "0"))
                if limit_el.get("upper") is not None:
                    upper = float(limit_el.get("upper", "0"))
            joints.append(
                Joint(
                    name=name,
                    joint_type=joint_type,
                    parent=parent_el.get("link", ""),
                    child=child_el.get("link", ""),
                    xyz=xyz,
                    rpy=rpy,
                    axis=axis,
                    lower=lower,
                    upper=upper,
                )
            )

    return Robot(
        name=root.get("name") or path.stem,
        links=links,
        joints=joints,
        materials=materials,
        urdf_dir=path.parent,
    )


def unique_collection(name: str):
    col = bpy.data.collections.new(name)
    scene_col = bpy.context.scene.collection
    try:
        scene_col.children.link(col)
    except RuntimeError:
        pass
    reveal_collection(col)
    return col


def reveal_collection(col) -> None:
    """Make sure a newly created collection is not excluded from the view layer."""
    view_layer = bpy.context.view_layer

    def walk(layer_col):
        if layer_col.collection == col:
            layer_col.exclude = False
            layer_col.hide_viewport = False
            view_layer.active_layer_collection = layer_col
            return True
        for child in layer_col.children:
            if walk(child):
                return True
        return False

    walk(view_layer.layer_collection)
    view_layer.update()


def new_empty(name: str, collection, display_type: str, size: float):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = display_type
    obj.empty_display_size = size
    obj.hide_render = True
    collection.objects.link(obj)
    return obj


def parent_local(child, parent, local: Matrix) -> None:
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Identity(4)
    child.matrix_local = local


def dominant_axis_index(axis: Vec3) -> int:
    return max(range(3), key=lambda i: abs(axis[i]))


def lock_joint(obj, joint: Joint) -> None:
    obj.lock_scale = (True, True, True)
    idx = dominant_axis_index(joint.axis)
    if joint.joint_type in ("revolute", "continuous"):
        obj.lock_location = (True, True, True)
        obj.lock_rotation = tuple(i != idx for i in range(3))
    elif joint.joint_type == "prismatic":
        obj.lock_rotation = (True, True, True)
        obj.lock_location = tuple(i != idx for i in range(3))
    else:
        obj.lock_location = (True, True, True)
        obj.lock_rotation = (True, True, True)
    obj["urdf_type"] = joint.joint_type
    obj["urdf_axis"] = "{:g} {:g} {:g}".format(*joint.axis)
    if joint.lower is not None:
        obj["urdf_lower"] = joint.lower
    if joint.upper is not None:
        obj["urdf_upper"] = joint.upper


def get_or_create_material(
    name: str,
    rgba: Tuple[float, float, float, float],
    cache: Dict[str, object],
):
    if name in cache:
        return cache[name]
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = rgba
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None and "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = rgba
    cache[name] = mat
    return mat


def assign_material(obj, mat) -> None:
    if obj.data is None or mat is None:
        return
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def mesh_from_bmesh(name: str, build_fn):
    import bmesh

    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    build_fn(bm)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return mesh


def shade_smooth(mesh) -> None:
    if not mesh.polygons:
        return
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))


def make_box(name: str, size: Vec3):
    import bmesh

    def build(bm):
        bmesh.ops.create_cube(bm, size=1.0)
        sx, sy, sz = size
        for vert in bm.verts:
            vert.co.x *= sx
            vert.co.y *= sy
            vert.co.z *= sz

    return mesh_from_bmesh(name, build)


def make_cylinder(name: str, radius: float, length: float):
    import bmesh

    def build(bm):
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=32,
            radius1=radius,
            radius2=radius,
            depth=length,
        )

    mesh = mesh_from_bmesh(name, build)
    shade_smooth(mesh)
    return mesh


def make_sphere(name: str, radius: float):
    import bmesh

    def build(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=radius)

    mesh = mesh_from_bmesh(name, build)
    shade_smooth(mesh)
    return mesh


def move_to_collection(obj, collection) -> None:
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    collection.objects.link(obj)


def apply_transforms(obj) -> None:
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.select_set(False)


def join_meshes(meshes: Sequence):
    if not meshes:
        return None
    if len(meshes) == 1:
        return meshes[0]
    bpy.ops.object.select_all(action="DESELECT")
    for mesh_obj in meshes:
        mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    result = bpy.context.active_object
    bpy.ops.object.select_all(action="DESELECT")
    return result


def _collada_float_array(el: Optional[ET.Element]) -> List[float]:
    if el is None or not (el.text or "").strip():
        return []
    return [float(p) for p in el.text.split()]


def _collada_source_map(geom: ET.Element) -> Dict[str, Tuple[List[float], int]]:
    sources: Dict[str, Tuple[List[float], int]] = {}
    for source in find_children(geom, "source"):
        src_id = source.get("id")
        if not src_id:
            continue
        array_el = find_child(source, "float_array")
        accessor = None
        technique = find_child(source, "technique_common")
        if technique is not None:
            accessor = find_child(technique, "accessor")
        stride = int(accessor.get("stride", "3")) if accessor is not None else 3
        sources[src_id] = (_collada_float_array(array_el), stride)
    return sources


def _collada_node_scale(root: ET.Element) -> Vec3:
    scale = (1.0, 1.0, 1.0)
    for node in root.iter():
        if local_tag(node) != "node":
            continue
        scale_el = find_child(node, "scale")
        if scale_el is not None and (scale_el.text or "").strip():
            scale = parse_vec(scale_el.text)
    return scale


def _collada_image_path(root: ET.Element, dae_path: Path) -> Optional[Path]:
    for image in root.iter():
        if local_tag(image) != "image":
            continue
        init = find_child(image, "init_from")
        if init is None or not (init.text or "").strip():
            continue
        filename = init.text.strip()
        if filename.lower().endswith("normals.png"):
            continue
        candidate = (dae_path.parent / filename).resolve()
        if candidate.is_file():
            return candidate
    return None


def import_collada_mesh(path: Path, collection, name: str) -> Optional[object]:
    """Parse a simple triangle COLLADA file. Blender 5+ no longer ships Collada I/O."""
    tree = ET.parse(path)
    root = tree.getroot()
    sx, sy, sz = _collada_node_scale(root)

    geom = None
    for el in root.iter():
        if local_tag(el) == "geometry":
            geom = find_child(el, "mesh")
            if geom is not None:
                break
    if geom is None:
        print(f"warning: no <mesh> in {path}")
        return None

    sources = _collada_source_map(geom)
    vertices_el = find_child(geom, "vertices")
    position_id = None
    if vertices_el is not None:
        for inp in find_children(vertices_el, "input"):
            if inp.get("semantic") == "POSITION":
                position_id = (inp.get("source") or "").lstrip("#")
                break
    if not position_id or position_id not in sources:
        print(f"warning: no POSITION source in {path}")
        return None
    pos_data, pos_stride = sources[position_id]
    # Keep authored XYZ (plus node scale). RViz drops Collada <up_axis>
    # rotation, so converting Y_UP → Z_UP would roll these gripper meshes.
    positions = [
        (pos_data[i] * sx, pos_data[i + 1] * sy, pos_data[i + 2] * sz)
        for i in range(0, len(pos_data) - 2, pos_stride)
    ]

    triangles = find_child(geom, "triangles")
    if triangles is None:
        print(f"warning: no <triangles> in {path}")
        return None
    inputs = find_children(triangles, "input")
    max_offset = 0
    vertex_offset = 0
    tex_offset = None
    tex_id = None
    for inp in inputs:
        offset = int(inp.get("offset", "0"))
        max_offset = max(max_offset, offset)
        semantic = inp.get("semantic")
        if semantic == "VERTEX":
            vertex_offset = offset
        elif semantic == "TEXCOORD" and tex_offset is None:
            tex_offset = offset
            tex_id = (inp.get("source") or "").lstrip("#")
    stride = max_offset + 1
    raw = [int(p) for p in (find_child(triangles, "p").text or "").split()]
    faces: List[Tuple[int, int, int]] = []
    face_uvs: List[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]] = []
    tex_data, tex_stride = sources.get(tex_id or "", ([], 2))

    def uv_at(index: int) -> Tuple[float, float]:
        if not tex_data:
            return (0.0, 0.0)
        base = index * tex_stride
        if base + 1 >= len(tex_data):
            return (0.0, 0.0)
        return (tex_data[base], tex_data[base + 1])

    for i in range(0, len(raw), stride * 3):
        corner = raw[i : i + stride * 3]
        if len(corner) < stride * 3:
            break
        i0 = corner[vertex_offset]
        i1 = corner[stride + vertex_offset]
        i2 = corner[2 * stride + vertex_offset]
        faces.append((i0, i1, i2))
        if tex_offset is None:
            face_uvs.append(((0.0, 0.0), (0.0, 0.0), (0.0, 0.0)))
        else:
            face_uvs.append(
                (
                    uv_at(corner[tex_offset]),
                    uv_at(corner[stride + tex_offset]),
                    uv_at(corner[2 * stride + tex_offset]),
                )
            )

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(positions, [], faces)
    mesh.validate()
    mesh.update()
    if tex_data:
        uv_layer = mesh.uv_layers.new(name="UVMap")
        for loop_index, uv in enumerate(uv for triple in face_uvs for uv in triple):
            if loop_index < len(uv_layer.data):
                uv_layer.data[loop_index].uv = uv
    shade_smooth(mesh)

    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    image_path = _collada_image_path(root, path)
    if image_path is not None:
        mat = bpy.data.materials.new(f"{name}_tex")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(image_path))
        if bsdf is not None:
            links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        assign_material(obj, mat)
    return obj


def import_mesh_file(path: Path, collection) -> Optional[object]:
    if not path.is_file():
        print(f"warning: mesh file not found: {path}")
        return None
    before = set(bpy.data.objects)
    suffix = path.suffix.lower()
    try:
        if suffix == ".dae":
            parsed = import_collada_mesh(path, collection, path.stem)
            if parsed is not None:
                return parsed
            bpy.ops.wm.collada_import(filepath=str(path))
        elif suffix == ".stl":
            try:
                bpy.ops.wm.stl_import(filepath=str(path))
            except AttributeError:
                bpy.ops.import_mesh.stl(filepath=str(path))
        elif suffix == ".obj":
            try:
                bpy.ops.wm.obj_import(filepath=str(path))
            except AttributeError:
                bpy.ops.import_scene.obj(filepath=str(path))
        elif suffix in {".glb", ".gltf"}:
            bpy.ops.import_scene.gltf(filepath=str(path))
        else:
            print(f"warning: unsupported mesh type {suffix}: {path}")
            return None
    except Exception as exc:  # pylint: disable=broad-except
        print(f"warning: failed to import {path}: {exc}")
        return None

    imported = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in imported if obj.type == "MESH"]
    extras = [obj for obj in imported if obj.type != "MESH"]
    for extra in extras:
        bpy.data.objects.remove(extra, do_unlink=True)
    joined = join_meshes(meshes)
    if joined is None:
        return None
    move_to_collection(joined, collection)
    apply_transforms(joined)
    return joined


def resolve_mesh_path(filename: str, urdf_dir: Path) -> Path:
    if filename.startswith("package://"):
        # Defensive: export script should have rewritten these already.
        rel = filename.split("://", 1)[1]
        parts = rel.split("/", 1)
        rel = parts[1] if len(parts) == 2 else rel
        return (urdf_dir / rel).resolve()
    if filename.startswith("file://"):
        return Path(filename[7:])
    path = Path(filename)
    if path.is_absolute():
        return path
    return (urdf_dir / path).resolve()


def create_geometry(name: str, geom: ET.Element, robot: Robot, collection):
    kind = local_tag(geom)
    if kind == "box":
        size = parse_vec(geom.get("size"), (1.0, 1.0, 1.0))
        mesh = make_box(name, size)
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        return obj
    if kind == "cylinder":
        radius = float(geom.get("radius", "1"))
        length = float(geom.get("length", "1"))
        mesh = make_cylinder(name, radius, length)
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        return obj
    if kind == "sphere":
        radius = float(geom.get("radius", "1"))
        mesh = make_sphere(name, radius)
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        return obj
    if kind == "mesh":
        filename = geom.get("filename")
        if not filename:
            return None
        imported = import_mesh_file(resolve_mesh_path(filename, robot.urdf_dir), collection)
        if imported is None:
            return None
        imported.name = name
        scale = geom.get("scale")
        if scale:
            imported.scale = parse_vec(scale, (1.0, 1.0, 1.0))
            apply_transforms(imported)
        return imported
    print(f"warning: unsupported geometry <{kind}> on {name}")
    return None


def create_visuals(link: Link, link_obj, robot: Robot, collection, mat_cache) -> None:
    for i, visual in enumerate(link.visuals):
        suffix = "" if len(link.visuals) == 1 else f"_{i}"
        name = f"{link.name}_visual{suffix}"
        obj = create_geometry(name, visual.geom, robot, collection)
        if obj is None:
            continue
        parent_local(obj, link_obj, origin_matrix(visual.xyz, visual.rpy))
        rgba = visual.rgba
        mat_name = visual.material_name
        if rgba is None and mat_name and mat_name in robot.materials:
            rgba = robot.materials[mat_name]
        if rgba is not None:
            material = get_or_create_material(mat_name or name, rgba, mat_cache)
            assign_material(obj, material)


def configure_scene() -> None:
    units = bpy.context.scene.unit_settings
    units.system = "METRIC"
    units.scale_length = 1.0
    cube = bpy.data.objects.get("Cube")
    if cube is not None and cube.type == "MESH":
        bpy.data.objects.remove(cube, do_unlink=True)


def import_robot(robot: Robot):
    configure_scene()
    collection = unique_collection(robot.name)
    mat_cache: Dict[str, object] = {}
    for name, rgba in robot.materials.items():
        get_or_create_material(name, rgba, mat_cache)

    robot_root = new_empty(robot.name, collection, "PLAIN_AXES", 0.12)
    robot_root["urdf_robot"] = robot.name

    link_objects = {}
    for link in robot.links.values():
        link_obj = new_empty(link.name, collection, "PLAIN_AXES", 0.04)
        link_obj["urdf_link"] = link.name
        link_objects[link.name] = link_obj
        create_visuals(link, link_obj, robot, collection, mat_cache)

    child_links = {joint.child for joint in robot.joints}
    for joint in robot.joints:
        parent_obj = link_objects.get(joint.parent)
        child_obj = link_objects.get(joint.child)
        if parent_obj is None or child_obj is None:
            print(f"warning: joint {joint.name} references a missing link")
            continue
        joint_obj = new_empty(joint.name, collection, "ARROWS", 0.06)
        parent_local(joint_obj, parent_obj, origin_matrix(joint.xyz, joint.rpy))
        lock_joint(joint_obj, joint)
        parent_local(child_obj, joint_obj, Matrix.Identity(4))

    for name, link_obj in link_objects.items():
        if name not in child_links:
            parent_local(link_obj, robot_root, Matrix.Identity(4))

    reveal_collection(collection)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in collection.objects:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = robot_root
    frame_view()
    meshes = [obj for obj in collection.objects if obj.type == "MESH"]
    print(
        f"Created {len(collection.objects)} objects ({len(meshes)} meshes) "
        f"in collection '{collection.name}'."
    )
    return robot_root


def frame_view() -> None:
    """Point the 3D viewport at the robot without relying on view operators."""
    wm = bpy.context.window_manager
    if wm is None:
        return
    from mathutils import Euler

    for window in wm.windows:
        screen = window.screen
        if screen is None:
            continue
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            if space is None or space.type != "VIEW_3D":
                continue
            space.clip_start = 0.01
            space.clip_end = 100.0
            space.shading.type = "SOLID"
            space.shading.show_xray = False
            r3d = space.region_3d
            if r3d is not None:
                r3d.view_perspective = "PERSP"
                r3d.view_location = (0.0, 0.0, 0.2)
                r3d.view_distance = 3.0
                r3d.view_rotation = Euler(
                    (math.radians(70.0), 0.0, math.radians(55.0))
                ).to_quaternion()
            return


def parse_cli(args: List[str]) -> Tuple[Path, Optional[Path]]:
    urdf: Optional[Path] = None
    save: Optional[Path] = None
    i = 0
    while i < len(args):
        if args[i] == "--save":
            if i + 1 >= len(args):
                sys.exit("error: --save needs a .blend path")
            save = Path(args[i + 1])
            i += 2
            continue
        if args[i].startswith("-"):
            sys.exit(f"error: unknown option {args[i]}")
        urdf = Path(args[i])
        i += 1
    if urdf is None:
        sys.exit(
            "Usage: blender --python scripts/import_urdf.py -- <robot.urdf> [--save out.blend]"
        )
    return urdf, save


def main() -> None:
    urdf_path, save_path = parse_cli(_argv_after_double_dash())
    if not urdf_path.is_file():
        sys.exit(f"error: URDF not found: {urdf_path}")
    robot = parse_urdf(urdf_path)
    print(
        f"Importing '{robot.name}': {len(robot.links)} links, {len(robot.joints)} joints"
    )
    import_robot(robot)
    print(
        f"Robot is in Outliner collection '{robot.name}'. "
        "Select head_swivel / *_wheel_joint / gripper_extension to pose it."
    )
    if save_path is None and not bpy.app.background:
        save_path = urdf_path.with_suffix(".blend")
    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(save_path.resolve()))
        print(f"Saved {save_path}")


def _scene_has_robot() -> bool:
    return any(obj.get("urdf_robot") for obj in bpy.data.objects)


def _run_import_if_needed() -> None:
    if _scene_has_robot():
        return
    try:
        bpy.app.handlers.load_post.remove(_on_load)
    except ValueError:
        pass
    main()


@persistent
def _on_load(_dummy) -> None:
    # Startup.blend just loaded and wiped any earlier import — run again.
    _run_import_if_needed()


def _on_timer():
    _run_import_if_needed()
    return None


if __name__ == "__main__":
    if bpy.app.background:
        main()
    else:
        # --python runs before startup.blend. A short timer can import too early
        # and then get wiped; load_post is the real hook. Keep a late timer only
        # for the case where Blender is already fully open (no load_post).
        bpy.app.handlers.load_post.append(_on_load)
        bpy.app.timers.register(_on_timer, first_interval=0.5)
