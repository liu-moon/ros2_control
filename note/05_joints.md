# 05 关节类型

## 目标

分清本机用到的 `fixed` 和 `continuous`；看懂 `<axis xyz="0 1 0" />`；知道万向轮写成 fixed 是教学简化。

对照文件：[`src/my_robot_description/urdf/mobile_base.xacro`](../src/my_robot_description/urdf/mobile_base.xacro)

## 笔记

joint 的 `type` 决定子 link 相对父 link **还剩几个自由度**。origin 决定「零位时装在哪」，type + axis 决定「还能怎么动」。

### 本机用到的两种

**`fixed`：完全锁死**

子相对父的位姿永远等于 origin，没有可动关节值。

本机两处：

- `base_joint`：`base_footprint` → `base_link`。车身相对地面参考点的高度固定。
- `base_caster_wheel_joint`：车身 → 万向轮。球永远钉在车前下方。

fixed 关节**不需要** `<axis>`，也没有 `/joint_states` 里的角度。TF 一旦由 URDF 算出就不变。

**`continuous`：绕一根轴无限转**

适合车轮：没有角度限位。本机两处：

- `base_left_wheel_joint`
- `base_right_wheel_joint`

必须写转轴：

```xml
<axis xyz="0 1 0" />
```

这是在**子 link 坐标系**（也等价于零位时的关节坐标系）里给出的方向：绕 Y 轴转。和 04 课把圆柱转到沿 Y 一致。

`xyz="0 1 0"` 是单位方向，不是位移。写成 `0 1 0` 或 `0 2 0` 在方向上相同（规范写法用单位向量）。

### 常见类型对照（本机没用，但读文档会碰到）

| type | 自由度 | 典型用途 |
|---|---|---|
| `fixed` | 0 | 焊死、传感器支架、本机的 footprint 和万向轮 |
| `continuous` | 绕轴无限转 | 本机驱动轮 |
| `revolute` | 绕轴转，有上下限 | 机械臂关节 |
| `prismatic` | 沿轴平移 | 升降机构 |

### 万向轮为什么是 fixed

真车上的脚轮会绕竖直轴偏转，还会自转。这里用一个**固定的球**代替：

- 几何上撑住车头，RViz 里能看见。
- 没有偏转关节，也没有滚动关节。
- mock 控制和差速控制器只认左右驱动轮（08 课），不管这个球。

这是教学简化，不是真实脚轮模型。

### 和 `/joint_states` 的关系（07 课会再串起来）

只有**可动**关节会出现在 `/joint_states` 里。`display.launch.py` 用 `joint_state_publisher_gui` 给你两个滑条，对应左右轮。拖滑条，轮子在 RViz 里转；万向轮和车身相对 footprint 不会动。

### 转轴和外观必须一致

- visual：圆柱绕 X 转 90°，轴线沿 Y（04）
- joint：`<axis xyz="0 1 0" />`，绕 Y 转（本课）

若 axis 写成 `0 0 1`，滑条拖动时轮子会像陀螺一样平转，和画出来的轮面垂直——那就是轴写错了。

## 对照源码阅读

1. 四个 joint 各标上 type。
2. 找出唯一出现 `<axis>` 的两处，确认都是 `0 1 0`。
3. 想一下：若给 caster 也改成 `continuous` 且 axis 为 `0 0 1`，语义上变成了什么（不必改代码）。

## 练习题

1. `fixed` 和 `continuous` 各还剩几个运动自由度？

2. 本机哪两个关节是 `continuous`？它们的 `<axis>` 是什么？绕车体的哪根轴转？

3. 为什么 `base_joint` 没有 `<axis>` 标签？

4. 差速底盘的驱动轮用 `continuous` 而不是 `revolute`，主要图什么？

5. 万向轮写成 `fixed` + `sphere`，丢掉了真实脚轮的哪两种运动？

6. 若把左右轮的 axis 都改成 `xyz="1 0 0"`（绕 X），RViz 里拖滑条时，轮子会怎么转？和车轮前进方向一致吗？

7. 判断对错：`fixed` 关节的 child 仍然会作为 TF 里的一个 frame 出现。

8. `/joint_states` 里预期会出现哪些关节名？哪些不会出现？

9. origin 的 `rpy="0 0 0"` 和 axis `0 1 0` 分别回答哪两个问题：「零位朝哪」还是「还能绕哪转」？
