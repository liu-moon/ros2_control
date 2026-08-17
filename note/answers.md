# 参考答案

先自己做完对应课的练习，再看这一节。答案从简，推理过程以各课笔记为准。

---

## 01 XML

1. 属性名。标签名是 `joint`。
2. 没有实质区别：都是空元素。`/>` 是自闭合写法。
3. `<visual>`。`<origin>` 和 `<geometry>` 是兄弟，不是父子。
4. 末尾 `/` 表示没有子内容、在本标签结束。只写开始标签不写结束标签，XML 不合法。
5. 引用名为 `base_footprint` 的那个 `<link>`。靠 **name 字符串** 对上，不靠文件顺序。
6. 错。树的父子由 joint 的 `parent` / `child` 决定，不由谁写在前面决定。
7. 对几何没有影响，只是启用 `xacro:` 前缀。不必去读那个 URL。
8. 例如：`<joint name="base_joint" type="fixed">`，或 `<joint name="base_right_wheel_joint" type="continuous">`。

---

## 02 机器人是一棵树

1. link 是刚体/坐标系；joint 是两个 link 之间的约束。单独一个 link、零个 joint 可以（退化）；多个 link 必须靠 joint 连成一棵树，否则不是连通的 URDF。
2. `base_footprint`。它从未出现在任何 joint 的 `child` 里，是唯一的根。
3. 三个：`left_wheel_link`（`base_left_wheel_joint`）、`right_wheel_link`（`base_right_wheel_joint`）、`caster_wheel_link`（`base_caster_wheel_joint`）。
4. 作为树仍然可以只有一个根（根变成 `base_link`，`base_footprint` 变成它的子）。语义反了：贴地参考点不再是根，TF 上这段父子颠倒，和导航里 `odom → base_footprint` 的习惯也不再对齐。
5. 它是贴地的根坐标系，给 TF、RViz Fixed Frame、里程计 `base_frame` 用。不必画出来。
6. 错。见 01 第 6 题。
7. link 名：`right_wheel_link`。父 link：`base_link`（通过 `base_right_wheel_joint`）。
8. 没有。轮子都挂在车身上，彼此独立转；连成环或轮连轮会破坏「树」且不符合差速结构。
9. `left_wheel_link` → `base_left_wheel_joint` → `base_link` → `base_joint` → `base_footprint`。

---

## 03 坐标系与 origin

1. joint origin：子 **link 坐标系** 相对父 **link 坐标系**。visual origin：几何形状相对 **本 link 坐标系**。
2. X+ 前，Y+ 左，Z+ 上。右轮 Y 为负，在车的**右侧**。
3. `(0, 0, 0.1)`。这是轮轴离地高度，应等于轮半径，让轮缘贴地；和车身盒子高度 0.2 不是一回事。
4. **不会**改 link 坐标系 / TF。盒子中心落到 `base_link` 原点，一半（0.1 m）画到轮轴以下，看起来车身下沉、可能穿地。
5. X：`-base_length/4 = -0.6/4 = -0.15`。Y：`-(base_width + wheel_length)/2 = -(0.4+0.05)/2 = -0.225`。Z：`0`。
6. `0.45` m。等于 `base_width + wheel_length`（两轮原点的 Y 差）。
7. `base_link` 原点离地 0.1 m，球半径 0.05 m，球心相对 `base_link` 应为 `z = -0.05` 才贴地。Z=0 会离地 0.05 m；Z=-0.1 球心在地面，一半陷入地里。
8. 不是。`rpy="0 0 0"` 只表示零位没有额外旋转；轮子仍靠 `continuous` 关节转。
9. 右轮原点在 `base_footprint` 下是 `(-0.15, -0.225, 0.1)`，触地点再减轮半径的 Z → `(-0.15, -0.225, 0)`。
10. 错。visual origin 不进入 TF。`base_link → right_wheel_link` 只由 joint origin（以及关节角）决定。

---

## 04 visual 只是外观

1. 不影响 TF。影响 RViz RobotModel 的外观。
2. 依次沿 X、Y、Z。`0.6` 是车长（前后，X）。
3. 默认轴线是 **Z**。`<cylinder>` 没有「轴向」属性，只能用 visual 的 `rpy` 把几何转过来。
4. 合理：关节是 `fixed`，球只负责撑住车头、好看，不模拟滚动或偏转。
5. 偏蓝（R=0, G=0, B=0.5）。`1` 是不透明。
6. 名为 `blue` 的材质没有定义，RViz 里可能变成默认色或报材质缺失。
7. 错。没有 collision 也能发 TF。collision 给碰撞/物理用。
8. 在对应轮子的 **link 原点**上（`right_wheel_link` / `left_wheel_link`）。
9. `<collision>` 和 `<inertial>`。

---

## 05 关节类型

1. `fixed`：0。`continuous`：1（绕轴无限转动）。
2. `base_left_wheel_joint`、`base_right_wheel_joint`。`<axis xyz="0 1 0" />`，绕车体 **Y** 轴。
3. `fixed` 不能动，没有转轴。
4. 车轮可以一直转，没有角度上下限（`revolute` 需要 limit）。
5. 绕竖直轴的偏转，以及绕轮轴的滚动。
6. 绕 X 转（前后翻）。不是「滚动着往前走」的那根轴，和差速前进方向不一致。
7. 对。fixed 的 child 仍是 TF 里的一个 frame，只是变换恒定。
8. 会出现：`base_left_wheel_joint`、`base_right_wheel_joint`。不会出现：`base_joint`、`base_caster_wheel_joint`。
9. `rpy` 回答零位「子坐标系朝哪」；`axis` 回答还能「绕哪根轴转」。

---

## 06 xacro

1. 预处理，不是另一种描述格式。展开后的 URDF 给 `robot_state_publisher`、RViz、`ros2_control` 用。
2. 把颜色、几何、控制接口拆开维护；入口只负责组装。
3. 至少三处：驱动轮 `<cylinder radius>`、`base_joint` 的 Z、万向轮半径（以及它的 joint Z，同源）。只改圆柱半径、不改 `base_joint` 的 Z，轮子会看起来更大/更小，但轴高度不变，轮缘会陷入地面或离地。
4. `right_wheel_link`。
5. 左右轮 joint 的 origin 不同（Y 一正一负）。若用宏生成关节，至少还要 `prefix` 以及 origin（或 Y 的符号/坐标）。
6. 约 `1.5708`。出现在**轮子 visual** 的 origin 里，不是 joint 的 origin。
7. 以入口为准：`name="my_robot"`。被 include 的文件里的 `<robot>` 只当容器，名字不覆盖入口。
8. 错。URDF 解析器不算 `${}`；必须先跑 `xacro`。
9. `xacro /workspace/src/my_robot_description/urdf/my_robot.urdf.xacro`

---

## 07 TF 与 launch

1. 模型：`robot_description`（展开后的 URDF）。关节状态：`/joint_states`。
2. 参数/话题里的字符串是 xacro **展开后**的 URDF。RViz RobotModel 订 `/robot_description`，不直接读磁盘上的 `.xacro`。
3. `robot_description` 必须是合法 URDF XML，不能把带 `${}` / macro 的模板原样塞进去。
4. fixed 关节的 TF 仍在。没有 gui 就没有人发左右轮的 `/joint_states`（除非别的节点发），轮子不会被滑条带动。
5. 两者差 `0.1` m 高度。Fixed Frame 用 `base_footprint` 时网格在地面；用 `base_link` 时「世界」在轮轴高度，车看起来会陷进网格或网格齐轴。
6. 找的是 install 后的 `share/`，不是直接读 `src/`。改了 xacro 却没 `colcon build`（且没改 install 布局），launch 可能仍用旧的已安装副本。
7. 功能相同。XML 里那几行：对 `robot_state_publisher` 设置参数 `robot_description`，值为 `xacro` 命令的输出。
8. 错。TF 由 `robot_state_publisher` 根据 URDF + `/joint_states` 发布；RViz 只订阅 TF。
9. 滑条 → `joint_state_publisher_gui` 发 `/joint_states` → `robot_state_publisher` 更新轮子 TF → RViz 按 TF 画轮子。

---

## 08 ros2_control 接口

1. 声明硬件（或 mock）暴露哪些 command/state 接口，供控制器读写。不是画外形。
2. mock 在软件里假装电机、积分出状态；真插件才读写真实驱动器。教学阶段没有车也能把链路跑通。
3. command：`velocity`。state：`position`、`velocity`。差速控制的是左右轮转速，不是「转到某绝对角停住」。
4. 对应关节是 `fixed`，不可控，差速控制器也不用它。
5. 名字对不上，controller_manager / 硬件资源申领会失败（找不到该关节的接口）。
6. `(base_width + wheel_length) = 0.4 + 0.05 = 0.45`。只改 YAML 等于告诉控制器「轮距是 0.4」，和模型上的 0.45 不一致，转弯/里程计会算错，外观还是旧轮距。
7. `base_footprint` 是 URDF/TF 树的根，也是 RViz Fixed Frame；控制器把车体坐标系设成同一个名字，里程计 TF 才接得上。
8. 错。display launch 只起 rsp + gui + RViz，没有 `ros2_control_node`，也不会加载 `diff_drive_controller`。`<ros2_control>` 块随 URDF 进了 `robot_description`，但没有 manager 去解析它、跑控制器。
9. 外形和关节树：`mobile_base.xacro`（入口拼进去）。硬件接口：`mobile_base.ros2_control.xacro`。控制器参数：`my_robot_controllers.yaml`。
10. 把这些接口接到 `controller_manager`、用 spawner 拉起 `joint_state_broadcaster` / `diff_drive_controller`，再用 `cmd_vel` 开车。
