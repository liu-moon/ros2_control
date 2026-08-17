# my_robot_description 分步学习笔记

这套笔记只讲一件事：看懂 [`src/my_robot_description`](../src/my_robot_description) 里的机器人描述。例子全部来自这份源码，不另造一台机器人。

## 怎么用

1. 按 `01` → `08` 的顺序读，不要跳。
2. 每课先读「笔记」，再打开对应源码把提到的行对一遍，最后做「练习题」。
3. 先自己写答案，再对 [`answers.md`](answers.md)。
4. **做完 03 再往下。** 坐标系是后面所有课的基础；03 没算明白，轮子位置和 TF 都会糊。

本仓库的机器人代码不用改。动手题（07）是在 Docker 容器里启动已有 launch，不是改 URDF。

## 课程序列

```
01 XML 够用就停
  → 02 机器人是一棵树
    → 03 坐标系与 origin（重点）
      → 04 visual 只是外观
        → 05 关节类型
          → 06 xacro 写法糖
            → 07 TF 与 launch
              → 08 ros2_control 接口
```

| 课 | 文件 | 对照源码 | 学到什么程度 |
|---|---|---|---|
| 01 | [01_xml.md](01_xml.md) | `mobile_base.xacro` 任意一段 | 会读标签、属性、嵌套 |
| 02 | [02_urdf_tree.md](02_urdf_tree.md) | `mobile_base.xacro` 全部 `<link>` / `<joint>` | 能画出本机的 link 树 |
| 03 | [03_frames_origin.md](03_frames_origin.md) | 每个 `<origin>` | 能算出每个零件相对父坐标系的位置 |
| 04 | [04_visual.md](04_visual.md) | `<visual>` / `<geometry>` / `<material>` | 知道外观和物理不是一回事 |
| 05 | [05_joints.md](05_joints.md) | `type` / `<axis>` | 知道谁锁死、谁能转、绕哪根轴 |
| 06 | [06_xacro.md](06_xacro.md) | `my_robot.urdf.xacro`、property、macro | 能手写宏展开结果 |
| 07 | [07_tf_launch.md](07_tf_launch.md) | `display.launch.py` | 知道运行时谁发布 TF、RViz 看什么 |
| 08 | [08_ros2_control.md](08_ros2_control.md) | `mobile_base.ros2_control.xacro` | 知道关节名如何接到控制接口 |

## 源码地图

```
src/my_robot_description/
├── urdf/
│   ├── my_robot.urdf.xacro              ← 总入口（06）
│   ├── common_properties.xacro          ← 颜色（04）
│   ├── mobile_base.xacro                ← 几何 + 关节（02–05）
│   └── mobile_base.ros2_control.xacro   ← 硬件接口（08）
├── launch/
│   ├── display.launch.py                ← 可视化启动（07）
│   └── display.launch.xml               ← 同上，XML 写法
└── rviz/urdf_config.rviz                ← RViz 预设（07）
```

控制器配置在 [`src/my_robot_bringup/config/my_robot_controllers.yaml`](../src/my_robot_bringup/config/my_robot_controllers.yaml)。08 只点到轮名和半径如何对上，不展开 bringup 全流程。

Gazebo、`<collision>` / `<inertial>`、完整控制器启动，是下一阶段，这套笔记不覆盖。
