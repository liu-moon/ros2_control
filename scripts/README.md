# 把 URDF / XACRO 导入 Blender

ROS 2 跑在 **Docker** 里，Blender 跑在 **macOS 本机**。Blender 读不懂 `.xacro`，也不认识 `package://` 网格路径，所以要先在容器里展平模型，再在本机导入。

```
.urdf.xacro  --(export)-->  blender_export/*.urdf + meshes/  --(import)-->  Blender 场景
```

默认示例是官方教程里的 R2D2 风格机器人：[`src/urdf_tutorial/urdf/08-macroed.urdf.xacro`](../src/urdf_tutorial/urdf/08-macroed.urdf.xacro)。`01`–`07` 的纯 URDF 用同一套命令即可。

## 1. 导出（本机，仓库根目录）

需要 Docker 容器在跑（`docker compose up -d`）。脚本会在容器里调用 `xacro`，把 `package://` 改成相对路径，并复制 mesh / 贴图。

```bash
# 默认：08-macroed.urdf.xacro
./scripts/export_urdf_for_blender.sh

# 指定文件
./scripts/export_urdf_for_blender.sh src/urdf_tutorial/urdf/08-macroed.urdf.xacro
./scripts/export_urdf_for_blender.sh src/urdf_tutorial/urdf/01-myfirst.urdf
```

输出在源文件所在包下的 `blender_export/`（已加入 `.gitignore`）：

```
src/urdf_tutorial/blender_export/08-macroed.urdf
src/urdf_tutorial/blender_export/meshes/l_finger.dae
src/urdf_tutorial/blender_export/meshes/l_finger_color.png
...
```

如果已经在容器里，也可以直接跑同一条脚本（容器内有 `xacro` 时不会再调 Docker）。

## 2. 导入 Blender

用 **Blender 自带的 Python** 跑导入脚本，不要用系统 `python3`。macOS 上可执行文件一般是：

`/Applications/Blender.app/Contents/MacOS/Blender`

先关掉已打开的 Blender，再在仓库根目录执行：

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  --python scripts/import_urdf.py -- \
  src/urdf_tutorial/blender_export/08-macroed.urdf
```

图形界面导入成功后，会顺带存一份 `.blend`（和 URDF 同名）。下次可以直接打开，不必再导一次：

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  src/urdf_tutorial/blender_export/08-macroed.blend
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
  src/urdf_tutorial/blender_export/08-macroed.urdf \
  --save /tmp/robot.blend
```

终端里应看到类似：

```
Importing 'macroed': 16 links, 15 joints
Created 48 objects (16 meshes) in collection 'macroed'.
```

## 导入后的场景

Outliner 里会出现名为机器人名的集合（例如 `macroed`），结构就是 URDF 树：

- 每个 **link** → 一个 Empty，视觉几何挂在它下面（`base_link`、`head`、`left_leg` …）
- 每个 **joint** → 夹在父子 link 之间的 Empty，显示为坐标轴箭头
  - `revolute` / `continuous`：只放开对应旋转轴
  - `prismatic`：只放开对应平移轴
  - `fixed`：全部锁定
- 单位是米，Z 向上，和 ROS 一致
- 夹爪 `.dae` 按 RViz 的方式读取（忽略 Collada 的 `Y_UP` 旋转，只保留缩放）

选中这些 Empty 就能摆姿势、插关键帧：

| 物体 | 动作 |
| --- | --- |
| `head_swivel` | 绕 Z 转头 |
| `left_front_wheel_joint` 等四个轮关节 | 绕 Y 转轮子 |
| `gripper_extension` | 沿 X 伸缩夹爪杆 |
| `left_gripper_joint` / `right_gripper_joint` | 夹爪开合（上限约 0.548 rad） |

关节物体上还有自定义属性 `urdf_type`、`urdf_axis`，以及有限制时的 `urdf_lower` / `urdf_upper`。

## 拍教学视频时

脚本只负责把模型摆对，打灯和成片在 Blender 里做：

- 加地面（棋盘格便于看出尺度）、三点光或 HDRI
- 相机对准机器人中心 Empty，做一圈轨道动画
- 建议关键帧：头转一圈、四轮转动、夹爪伸缩、手指开合
- 讲 xacro 时，可把 `01-myfirst.urdf` 到 `08-macroed` 依次导入，对比手写 URDF 和 macro 展开后的同一棵树

## 常见问题

**3D 视图里只有默认立方体**  
`blender --python` 会在默认场景加载之前跑脚本，导入结果可能被启动文件清掉。请先彻底退出 Blender（Command+Q）再重新跑导入命令；或直接打开生成的 `.blend`。导入成功后 Outliner 里应有 `macroed` 集合，而不只是 Camera / Cube / Light。若集合在但看不见模型，把鼠标放在 3D 窗口按 `Home`。

**夹爪朝向和 RViz 不一致**  
导入器按 RViz 处理 Collada：保留节点缩放，不按 `<up_axis>Y_UP</up_axis>` 再转 90°。请确认用的是当前仓库里的 `scripts/import_urdf.py`，并重新导出、导入。

**改了 xacro 但 Blender 没变**  
先再跑一遍 `export_urdf_for_blender.sh`，再重新导入（或删掉旧的 `.blend` 后导入）。`blender_export/` 是生成物，不要手改里面的 URDF。
