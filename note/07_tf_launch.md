# 07 TF 与 launch

## 目标

串起运行时数据流：xacro → `robot_description` → `robot_state_publisher` → TF；知道 `/joint_states` 从哪来；解释 RViz Fixed Frame 为什么是 `base_footprint`。

对照文件：

- [`src/my_robot_description/launch/display.launch.py`](../src/my_robot_description/launch/display.launch.py)
- [`src/my_robot_description/launch/display.launch.xml`](../src/my_robot_description/launch/display.launch.xml)
- [`src/my_robot_description/rviz/urdf_config.rviz`](../src/my_robot_description/rviz/urdf_config.rviz)（扫一眼即可）

## 笔记

前几课写的是**静态文件**。要在 RViz 里看到会转的轮子，需要三个节点。

### 数据流

```
my_robot.urdf.xacro
        │  xacro 命令展开
        ▼
robot_description 参数（一整份 URDF 字符串）
        │
        ▼
robot_state_publisher
        ├── 发布 TF：fixed 关节立刻有；可动关节要等 joint_states
        └── 发布 /robot_description（给 RViz RobotModel 用）
                ▲
                │
joint_state_publisher_gui ──► /joint_states（左右轮角度）
                │
                ▼
             rviz2（读 TF + /robot_description）
```

- **没有** `/joint_states` 时，可动关节的 TF 不更新（或停在 0）。fixed 关节仍在。
- RViz 的 RobotModel 显示插件订的是话题 `/robot_description`，不是直接读磁盘上的 xacro。

### Python launch 在干什么

```python
urdf_path = os.path.join(get_package_share_path('my_robot_description'),
                         'urdf', 'my_robot.urdf.xacro')
robot_description = ParameterValue(Command(['xacro ', urdf_path]), value_type=str)

Node(package="robot_state_publisher", executable="robot_state_publisher",
     parameters=[{'robot_description': robot_description}])
Node(package="joint_state_publisher_gui", executable="joint_state_publisher_gui")
Node(package="rviz2", executable="rviz2",
     arguments=['-d', rviz_config_path])
```

要点：

- `get_package_share_path` 找到**安装后的** `share/my_robot_description`，所以要先 `colcon build` 并 `source install/setup.bash`。只改源码没编译时，launch 可能还在用旧文件。
- `Command(['xacro ', urdf_path])`：启动时跑一遍 xacro，结果当参数传入。
- `joint_state_publisher_gui` 弹出滑条窗口，给每个可动关节一个角度。
- `rviz2 -d urdf_config.rviz` 加载预设：Grid、RobotModel、TF，Fixed Frame 已设为 `base_footprint`。

XML 版 `display.launch.xml` 做同一件事：`$(command 'xacro $(var urdf_path)')`。会一种即可，另一种当对照。

### 为什么 Fixed Frame 是 `base_footprint`

RViz 必须选一个坐标系当「世界画布」。选 `base_footprint`：

- 它在地面，网格和车的投影对齐。
- 车身、轮子都是它的后代，整棵树都能画出来。

若误选 `left_wheel_link`，整个机器人会绕着左轮原点摆，网格关系很难看。选一个不存在的 frame，RobotModel 会报错、什么都不画。

### TF 树和 URDF 树是同一棵

02 课画的 parent/child，运行时就是 TF 树：

```
base_footprint
  └── base_link
        ├── left_wheel_link
        ├── right_wheel_link
        └── caster_wheel_link
```

RViz 的 TF 显示插件可以打开坐标轴，对照 03 课算的 origin。

### 可选动手（容器内）

假设已经 `colcon build && source /workspace/install/setup.bash`，浏览器 VNC 已连上：

```bash
ros2 launch my_robot_description display.launch.py
```

然后：拖 `joint_state_publisher_gui` 的滑条，看左右轮是否绕 Y 转；在 RViz 里打开 TF，核对五个 frame。

这一步不是必须；看懂 launch 代码就算完成本课。后面接真控制器时，`/joint_states` 会改由 `joint_state_broadcaster` 发布，gui 就不再用了。

## 对照源码阅读

1. 在 `display.launch.py` 标出：xacro 路径、三个 Node、RViz 配置路径。
2. 对比 `display.launch.xml`，找出与 Python 版一一对应的三块。
3. 打开 `urdf_config.rviz`，搜 `Fixed Frame` 和 `base_footprint`。

## 练习题

1. `robot_state_publisher` 的输入有哪两样？（一个是参数/话题里的模型，一个是关节状态。）

2. `/robot_description` 和磁盘上的 `my_robot.urdf.xacro` 是什么关系？RViz 读哪一个？

3. 为什么 launch 里要用 `Command(['xacro ', urdf_path])`，而不是直接把 xacro 文件路径当 `robot_description`？

4. `joint_state_publisher_gui` 不启动时，fixed 关节的 TF 还有吗？左右轮还能在 RViz 里被拖着转吗？

5. Fixed Frame 选 `base_footprint` 而不是 `base_link`，视觉上差在哪？（结合 03：两者差一个轮半径的高度。）

6. `get_package_share_path('my_robot_description')` 找到的是 `src/` 还是 install 后的 `share/`？改了 xacro 却没 `colcon build`，launch 可能读到哪份文件？

7. Python launch 和 XML launch 功能是否相同？列出 XML 里对应 `robot_state_publisher` 的那几行在干什么。

8. 判断对错：RViz 的 TF 插件自己根据 URDF 算坐标变换，不需要 `robot_state_publisher`。

9. 用一两句话画出：拖动 gui 滑条之后，到 RViz 里轮子转动，中间经过哪些话题/节点。
