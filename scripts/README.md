# 把 URDF / XACRO / meshes 导入 Blender

ROS 2 跑在 **Docker** 里，Blender 跑在 **macOS 本机**。不想记命令时，用本机网页即可。

## 网页操作（推荐）

在仓库根目录：

```bash
python3 scripts/urdf_blender_web.py
```

浏览器会打开 **http://127.0.0.1:8765**。选一个模型，点 **导出并打开 Blender**。服务只监听本机。

下拉里有两类：

- `[XACRO]` / `[URDF]`：完整机器人（例如 `robomaster_ep.urdf.xacro`）。展开 xacro 需要 Docker 容器在跑（`docker compose up -d`）。
- `[零件]`：包里的 `meshes/` 目录（例如 RoboMaster 的 `.dae`）。只拷文件，不需要 Docker。

只定义 macro、不能单独展开的碎片（如 `arm.urdf.xacro`）不会出现在列表里，请用 `robomaster_ep` / `robomaster_s1` 这类完整机器人。

本机需要已安装 Blender。

下面是同样流程的命令行写法。

## 为什么要两步

```
.urdf.xacro  --(export)-->  blender_export/*.urdf + meshes/  --(import)-->  Blender 整机
meshes/      --(export)-->  blender_export/meshes + manifest  --(import)-->  Blender 零件库
```

默认示例若仓库里还有官方教程，是 R2D2 风格机器人：[`src/urdf_tutorial/urdf/08-macroed.urdf.xacro`](../src/urdf_tutorial/urdf/08-macroed.urdf.xacro)。RoboMaster 用：

```bash
./scripts/export_urdf_for_blender.sh src/robomaster_ros/robomaster_description/urdf/robomaster_ep.urdf.xacro
./scripts/export_urdf_for_blender.sh src/robomaster_ros/robomaster_description/meshes
```

## 1. 导出（本机，仓库根目录）

导出 **xacro** 需要 Docker 容器在跑（`docker compose up -d`）。脚本会在容器里调用 `xacro`，把 `package://` 改成相对路径，并复制 URDF 引用到的 mesh / 贴图。

导出 **meshes 目录** 只在本机拷贝 `.dae` / `.stl` / `.obj` 和贴图，写 `meshes_manifest.json`。

```bash
# 默认：08-macroed.urdf.xacro（若该文件还在）
./scripts/export_urdf_for_blender.sh

# 指定完整机器人
./scripts/export_urdf_for_blender.sh src/urdf_tutorial/urdf/08-macroed.urdf.xacro
./scripts/export_urdf_for_blender.sh src/robomaster_ros/robomaster_description/urdf/robomaster_ep.urdf.xacro
./scripts/export_urdf_for_blender.sh src/robomaster_ros/robomaster_description/urdf/robomaster_s1.urdf.xacro

# 零件库
./scripts/export_urdf_for_blender.sh src/robomaster_ros/robomaster_description/meshes
```

输出在源文件所在包下的 `blender_export/`（已加入 `.gitignore`）：

```
src/robomaster_ros/robomaster_description/blender_export/robomaster_ep.urdf
src/robomaster_ros/robomaster_description/blender_export/meshes/...
src/robomaster_ros/robomaster_description/blender_export/meshes_manifest.json
```

如果已经在容器里，也可以直接跑同一条脚本（容器内有 `xacro` 时不会再调 Docker）。

## 2. 导入 Blender

用 **Blender 自带的 Python** 跑导入脚本，不要用系统 `python3`。macOS 上可执行文件一般是：

`/Applications/Blender.app/Contents/MacOS/Blender`

先关掉已打开的 Blender，再在仓库根目录执行：

```bash
# 整机
/Applications/Blender.app/Contents/MacOS/Blender \
  --python scripts/import_urdf.py -- \
  src/robomaster_ros/robomaster_description/blender_export/robomaster_ep.urdf

# 零件库（网格排列，避免堆在原点）
/Applications/Blender.app/Contents/MacOS/Blender \
  --python scripts/import_urdf.py -- \
  src/robomaster_ros/robomaster_description/blender_export/meshes
```

图形界面导入成功后，会顺带存一份 `.blend`（整机和 URDF 同名，零件库为 `meshes.blend`）。下次可以直接打开，不必再导一次：

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  src/robomaster_ros/robomaster_description/blender_export/robomaster_ep.blend
```

指定保存路径：

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  --python scripts/import_urdf.py -- \
  src/urdf_tutorial/blender_export/08-macroed.urdf \
  --save /tmp/robot.blend
```

后台导入（不弹窗口）：

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/import_urdf.py -- \
  src/robomaster_ros/robomaster_description/blender_export/meshes \
  --save /tmp/parts.blend
```

终端里应看到类似：

```
Importing 'robomaster_ep': … links, … joints
Created … objects (… meshes) in collection 'robomaster_ep'.
```

或：

```
Importing parts from …/blender_export/meshes
Created … objects (… meshes) in collection 'robomaster_description_meshes'.
```

## 导入后的场景

### 整机

Outliner 里会出现名为机器人名的集合，结构就是 URDF 树：

- 每个 **link** → 一个 Empty，视觉几何挂在它下面
- 每个 **joint** → 夹在父子 link 之间的 Empty，显示为坐标轴箭头
  - `revolute` / `continuous`：只放开对应旋转轴
  - `prismatic`：只放开对应平移轴
  - `fixed`：全部锁定
- 单位是米，Z 向上，和 ROS 一致
- `.dae` 按 RViz 的方式读取（忽略 Collada 的 `Y_UP` 旋转，只保留缩放）
- 没有贴图的零件会用 Collada 里的 phong 漫反射颜色（底盘、LED）

选中这些 Empty 就能摆姿势、插关键帧。关节物体上还有自定义属性 `urdf_type`、`urdf_axis`，以及有限制时的 `urdf_lower` / `urdf_upper`。

教程机器人（若还在）常用关节：

| 物体 | 动作 |
| --- | --- |
| `head_swivel` | 绕 Z 转头 |
| `left_front_wheel_joint` 等四个轮关节 | 绕 Y 转轮子 |
| `gripper_extension` | 沿 X 伸缩夹爪杆 |
| `left_gripper_joint` / `right_gripper_joint` | 夹爪开合（上限约 0.548 rad） |

### 零件库

Outliner 里是 `robomaster_description_meshes` 这类集合：每个 `.dae` 一个物体，按包围盒在 XY 平面排开，方便单独看 chassis、夹爪、云台等零件。这不是装配好的机器人，不能按关节摆姿势。

## 拍教学视频时

脚本只负责把模型摆对，打灯和成片在 Blender 里做：

- 加地面（棋盘格便于看出尺度）、三点光或 HDRI
- 相机对准机器人中心 Empty，做一圈轨道动画
- 建议关键帧：头转一圈、四轮转动、夹爪伸缩、手指开合
- 讲 xacro 时，可把简单 URDF 和完整机器依次导入，对比手写 URDF 和 macro 展开后的同一棵树

## 常见问题

**3D 视图里只有默认立方体**  
`blender --python` 会在默认场景加载之前跑脚本，导入结果可能被启动文件清掉。请先彻底退出 Blender（Command+Q）再重新跑导入命令；或直接打开生成的 `.blend`。导入成功后 Outliner 里应有机器人或零件集合，而不只是 Camera / Cube / Light。若集合在但看不见模型，把鼠标放在 3D 窗口按 `Home`。

**夹爪朝向和 RViz 不一致**  
导入器按 RViz 处理 Collada：保留节点缩放，不按 `<up_axis>Y_UP</up_axis>` 再转 90°。请确认用的是当前仓库里的 `scripts/import_urdf.py`，并重新导出、导入。

**改了 xacro 但 Blender 没变**  
先再跑一遍 `export_urdf_for_blender.sh`，再重新导入（或删掉旧的 `.blend` 后导入）。`blender_export/` 是生成物，不要手改里面的 URDF。

**整机看起来缺轮子、机械臂发黑或「有洞」**  
导入器以前只读每个 `.dae` 的第一组三角形，轮子会少一大块胎面；URDF 里的纯色材质还会盖掉 Collada 贴图。请用当前的 `scripts/import_urdf.py` **重新**「导出并打开 Blender」（先完全退出旧窗口）。要完整装配关系，请选 `robomaster_ep`（底盘+机械臂+夹爪）或 `robomaster_s1`（底盘+云台），不要打开旧的 `camera.blend` / `gimbal.blend`。

**想单独导出 `arm.urdf.xacro`**  
那是 macro 碎片，展开后没有 link。请导出 `robomaster_ep.urdf.xacro` / `robomaster_s1.urdf.xacro`，或把 `meshes/` 当零件库导入。
