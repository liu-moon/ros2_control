# 04 visual 只是外观

## 目标

认识 `box` / `cylinder` / `sphere`，理解圆柱默认轴和轮子 `rpy="${pi/2} 0 0"` 的原因；知道本包没有碰撞和惯性。

对照文件：

- [`src/my_robot_description/urdf/mobile_base.xacro`](../src/my_robot_description/urdf/mobile_base.xacro)
- [`src/my_robot_description/urdf/common_properties.xacro`](../src/my_robot_description/urdf/common_properties.xacro)

## 笔记

`<visual>` 只回答：「在 RViz 里把这块 link 画成什么形状、什么颜色。」它不参与碰撞，也不告诉物理引擎质量。

一个 visual 通常三块：

```xml
<visual>
    <geometry> ... </geometry>   <!-- 形状 -->
    <origin ... />               <!-- 形状相对本 link 怎么放，见 03 -->
    <material name="blue" />     <!-- 颜色 -->
</visual>
```

### 三种几何

| 标签 | 本机用在 | 尺寸含义 |
|---|---|---|
| `<box size="长 宽 高" />` | `base_link` | 沿 X、Y、Z 的边长（米） |
| `<cylinder radius="r" length="l" />` | 左右轮 | 半径 r，轴向长度 l |
| `<sphere radius="r" />` | 万向轮 | 半径 r |

本机具体数值（展开后）：

- 车身盒子：`0.6 0.4 0.2`
- 驱动轮圆柱：半径 `0.1`，长度 `0.05`（轮厚）
- 万向轮球：半径 `0.05`（`wheel_radius / 2`）

默认情况下，形状的**几何中心**落在 visual origin 指定的位置。

### 圆柱默认沿 Z，所以轮子要转 90°

URDF 规定：`cylinder` 的轴线是 **Z 轴**。竖着的圆柱，像易拉罐。

轮子要立着，并且绕 **Y 轴**转（左右轮的转轴沿车宽方向）。因此 visual 里写了：

```xml
<origin xyz="0 0 0" rpy="${pi / 2.0} 0 0" />
```

`rpy` 的第一个数是 roll（绕 X 转）`π/2`。绕 X 转 90° 之后，圆柱原来的 Z 轴转到了 Y 轴方向。`xyz="0 0 0"`：几何中心仍在轮子 link 原点，不平移。

若忘掉这次旋转，RViz 里会看到两个「立着的滚筒」而不是车轮。

这只改**画出来的形状**。轮子真正绕哪根轴转，由 joint 的 `<axis xyz="0 1 0" />` 决定（05 课）。两件事必须一致：看起来像绕 Y 转，关节也绕 Y 转。

### 颜色：material

[`common_properties.xacro`](../src/my_robot_description/urdf/common_properties.xacro) 里定义了两个名字：

```xml
<material name="blue">
    <color rgba="0 0 0.5 1" />
</material>
<material name="grey">
    <color rgba="0.5 0.5 0.5 1" />
</material>
```

`rgba` 四个数：红、绿、蓝、不透明度，范围 0–1。车身引用 `blue`，轮子引用 `grey`。

这些定义能跨文件用，是因为入口 [`my_robot.urdf.xacro`](../src/my_robot_description/urdf/my_robot.urdf.xacro) 先 include 了 `common_properties.xacro`。

### 本包没有的两样东西

`mobile_base.xacro` 里没有：

- `<collision>`：碰撞几何。Gazebo 里碰障碍、物理接触会用到。
- `<inertial>`：质量、质心、惯性矩阵。物理仿真积分动力学时会用到。

所以现在这台车**能在 RViz 里看，还不能当刚体在 Gazebo 里老实滚动**。那是下一阶段。

`base_footprint` 连 visual 都没有：它只当坐标系，不画东西。

## 对照源码阅读

1. 给每个有 visual 的 link 标出：几何类型、尺寸、visual origin、颜色。
2. 看轮子那行 `rpy="${pi / 2.0} 0 0"`，用手比一下：绕 X 转 90° 后，圆柱轴指向哪。
3. 确认 `common_properties.xacro` 的 material 名字和 `mobile_base.xacro` 里的引用一致。

## 练习题

1. `<visual>` 影响 TF 吗？影响 RViz 里 RobotModel 的外观吗？

2. `box` 的 `size="0.6 0.4 0.2"` 三个数分别沿哪根轴？哪个是车长（前后）？

3. URDF 圆柱的默认轴线是哪根轴？为什么轮子 visual 要 `rpy="${pi/2} 0 0"`，而不是改 `cylinder` 的某个「轴向」属性？

4. 万向轮用 `sphere` 而不是 `cylinder`。结合它的关节类型（先看一眼 05：它是 `fixed`），这样简化合理吗？

5. `rgba="0 0 0.5 1"` 是什么颜色？最后一个 `1` 表示什么？

6. 若删除 `common_properties.xacro` 的 include，但 `mobile_base.xacro` 仍写 `<material name="blue" />`，外观上可能出现什么问题？

7. 判断对错：没有 `<collision>` 的 URDF 不能用 `robot_state_publisher` 发布 TF。

8. 轮子 visual 的 origin 是 `xyz="0 0 0"`。结合 03 课，轮子圆柱的几何中心在哪个坐标系的原点上？

9. 本课之后「下一阶段」要补什么，才能拿去 Gazebo 做物理仿真？列出两个 URDF 标签即可。
