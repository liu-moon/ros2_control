# 03 坐标系与 origin（重点）

## 目标

分清 **joint 的 origin** 和 **visual 的 origin**；按 ROS 车体系算出本机每个零件的位置。做完本课再往下。

对照文件：[`src/my_robot_description/urdf/mobile_base.xacro`](../src/my_robot_description/urdf/mobile_base.xacro)

## 笔记

每个 link 都是一个坐标系。joint 的职责之一：说清**子 link 的原点**相对**父 link 的原点**在哪、朝哪。

### ROS 车体系（本机用的）

| 轴 | 方向 |
|---|---|
| X+ | 前方 |
| Y+ | 左方 |
| Z+ | 上方 |

单位：`xyz` 是米，`rpy` 是弧度（roll / pitch / yaw，依次绕 X、Y、Z）。

本机所有 joint 的 `rpy` 都是 `0 0 0`，没有相对旋转，只平移。轮子能转，是关节类型 + axis 的事（05 课），不是 origin 里的 rpy。

### 两种 origin，不要混

| 写在哪 | 相对谁 | 在说什么 |
|---|---|---|
| `<joint>` 里的 `<origin>` | 子 **link 坐标系** 相对 父 **link 坐标系** | 零件装在车的哪个位置 |
| `<visual>` 里的 `<origin>` | 几何形状相对 **本 link 坐标系** | 盒子/圆柱的中心要不要从 link 原点挪开、转一下 |

`robot_state_publisher` 用的是 joint origin，用来发 TF。visual origin 只影响「图画在哪」，不改变 link 坐标系。

若上面这张表还抽象，先忘掉「坐标系」，只用图钉和外壳想：

每个零件（link）都有两样东西：

1. **一枚看不见的图钉**（link 的原点）。上面可以再钉别的零件。
2. **一块外壳**（visual：盒子、圆柱、球）。只是给眼睛看的塑料模型。

`<origin>` 出现两次，因为在回答两个不同的问题：

- **joint 里的 origin**：这枚图钉钉在父零件的哪。
- **visual 里的 origin**：这块外壳相对这枚图钉怎么贴（挪一点、转一下）。

图钉动了，钉在上面的东西会跟着走。只挪外壳，图钉不动。

地上有一个记号，叫 `base_footprint`（贴地的根，没有外壳）。

**步骤 A — joint（钉图钉）**

把写着 `base_link` 的图钉钉在记号正上方 10 cm（一个轮半径）：

```xml
<joint name="base_joint">
    <parent link="base_footprint" />
    <child link="base_link" />
    <origin xyz="0 0 0.1" />
</joint>
```

问的是：车身这枚图钉离地多高。左右轮以后都钉在这枚图钉上，所以轮轴高度由这里决定。

**步骤 B — visual（贴外壳）**

电脑画盒子时，默认把**盒子正中心**贴在图钉上。车身盒子高 20 cm，若中心在图钉上，会有 10 cm 画到图钉下面（穿到轮轴以下）。

所以 visual 说：把盒子再往上贴 10 cm（半高），让盒底对齐图钉、盒子坐在轮轴上面：

```xml
<link name="base_link">
    <visual>
        <box size="0.6 0.4 0.2" />
        <origin xyz="0 0 0.1" />
    </visual>
</link>
```

问的是：外壳相对图钉怎么贴。图钉还在离地 10 cm，没有因为画盒子再升一次。

两处都写 `0.1`，只是数字碰巧一样（轮半径 = 盒子半高），不是同一次移动。

```
        +----------+  盒子顶（离地 20cm）
        |  纸箱外壳 |  B: 外壳中心相对图钉再抬 10cm
        |    ◆     |  ◆ = 盒子中心
        +----------+  盒底 = 图钉
             ●        A: 图钉离地 10cm  ← 这才是 base_link
  地面       ●        base_footprint
```

若只把 visual 改成 `0 0 0`：图钉仍在 10 cm，轮子位置不变，但纸箱会往下画、一半埋到轮轴下面。这就是「只改外壳、不改安装位置」。

**轮子：图钉钉在车侧，外壳转 90 度**

- **joint**：把 `right_wheel_link` 这枚图钉钉在车身图钉的后右方 `(-0.15, -0.225, 0)`。这是「轮子装在哪」。
- **visual**：`xyz="0 0 0"` 表示圆柱中心就贴在这枚图钉上（不再挪）；`rpy` 为 90° 表示把默认竖着的易拉罐转成车轮的样子。这是「外壳怎么转才像轮子」。图钉位置不变。

万向轮：球心贴在图钉上（visual 全 0）；贴地是 joint 把图钉放到车前下方，不是 visual 完成的。

看懂图钉和外壳之后，再把「图钉」读回「link 坐标系」，下面的数字计算就接得上了。

### 本机用到的尺寸

```xml
<xacro:property name="base_length" value="0.6" />
<xacro:property name="base_width" value="0.4" />
<xacro:property name="base_height" value="0.2" />
<xacro:property name="wheel_radius" value="0.1" />
<xacro:property name="wheel_length" value="0.05" />
```

车身盒子：长 0.6（X）、宽 0.4（Y）、高 0.2（Z）。轮半径 0.1，轮厚 0.05。

### 把每个数字算出来

**1. `base_joint`：把车身抬离地面**

```xml
<origin xyz="0 0 ${wheel_radius}" rpy="0 0 0"/>
```

`wheel_radius = 0.1` → `(0, 0, 0.1)`。

`base_footprint` 在地面。`base_link` 原点在它正上方 0.1 m，大约在左右轮轴高度。这样轮子半径 0.1 时，轮缘贴地。

**2. `base_link` 的 visual origin：盒子中心上移**

```xml
<origin xyz="0 0 ${base_height / 2.0}" rpy="0 0 0" />
```

`base_height / 2 = 0.1` → `(0, 0, 0.1)`。

URDF 的 `box` 默认中心在「当前坐标系原点」。若 visual origin 为 0，盒子会一半在 `base_link` 原点下面（伸进轮轴以下）。上移半高后，盒子底面与 `base_link` 原点齐平，车身坐在轮轴高度之上。

注意：这是 **visual** origin，`base_link` 坐标系本身仍在 `base_joint` 放的那个位置，没有因为画盒子而再抬一次。

**3. 右轮 joint**

```xml
<origin xyz="${-base_length / 4.0} ${-(base_width + wheel_length) / 2.0} 0" ... />
```

- X：`-0.6 / 4 = -0.15` → 车身后方（驱动轮在后）
- Y：`-(0.4 + 0.05) / 2 = -0.225` → 右侧（Y- 是右）
- Z：`0` → 与 `base_link` 原点同高，即离地 0.1 m，等于轮半径

所以右轮原点：`(-0.15, -0.225, 0)`，相对 `base_link`。

**4. 左轮 joint**

X、Z 相同，Y 取反：`(-0.15, +0.225, 0)`。轮距（两轮原点的 Y 差）是 `0.45` m。08 课控制器 YAML 里的 `wheel_separation: 0.45` 就是这个数：`(base_width + wheel_length) = 0.45`。

**5. 万向轮 joint**

```xml
<origin xyz="${base_length / 3.0} 0 ${-wheel_radius / 2.0}" ... />
```

- X：`0.6 / 3 = 0.2` → 前方
- Y：`0` → 中线
- Z：`-0.1 / 2 = -0.05`

万向轮球体半径是 `wheel_radius / 2 = 0.05`。把它的原点放在 `base_link` 下方 0.05 m，球心离地 `0.1 - 0.05 = 0.05` m，正好等于球半径，所以也贴地。

### 侧视示意（单位 m，不按比例）

```
        Z
        ^
        |     +------ 车身盒子 0.6 x 0.2 ------+
        |     |  visual 中心 z=0.1 相对 base_link
        |     +--------------------------------+
        |           base_link 原点 ●  (离地 0.1)
 地 ----+----- 后轮 ● (-0.15)          万向轮 ● (0.2, z=-0.05)
 面     |     base_footprint 原点
        +---------------- X (前)
```

俯视：后轴左右轮 Y=±0.225，前万向轮在中线 X=0.2。

## 对照源码阅读

对着 `mobile_base.xacro` 每个 `<origin>` 问三句：

1. 它在 joint 里还是 visual 里？
2. 相对哪个坐标系？
3. 把 `${...}` 算成三个数字。

建议在纸上画俯视图和侧视图，标出五个 link 原点。

## 练习题

1. joint origin 和 visual origin 各描述哪两个坐标系之间的关系？

2. 本机 X+、Y+、Z+ 分别指向哪？右轮的 Y 是负数，说明它在车的哪一侧？

3. 算出 `base_joint` 的 origin（三个数字）。它为什么等于轮半径，而不是车身高度？

4. 若把 `base_link` 的 visual origin 改成 `xyz="0 0 0"`，link 坐标系会不会下降？RViz 里盒子看起来会怎样？

5. 写出右轮 joint origin 的计算过程，得到 `(-0.15, -0.225, 0)`。

6. 两驱动轮原点的 Y 坐标差是多少？它和 `base_width`、`wheel_length` 是什么关系？

7. 万向轮球体半径是 0.05 m。为什么 joint 的 Z 是 `-0.05` 而不是 `0` 或 `-0.1`？不这么放的话，球会离地还是陷入地面？

8. 本机所有 joint 的 `rpy` 都是 `0 0 0`。这是否表示轮子不能转？

9. `base_footprint` 原点到右轮触地点（轮子最低点），在 `base_footprint` 坐标系下的 xyz 大约是多少？（提示：先变到 `base_link`，再减一个轮半径的 Z。）

10. 判断对错：改 visual 的 origin 会改变 `/tf` 里 `base_link` → `right_wheel_link` 的变换。
