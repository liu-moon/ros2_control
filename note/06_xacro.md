# 06 xacro 写法糖

## 目标

看懂 `property`、`${}`、`macro`、`include`；能手写 `wheel_link` 宏展开后的两个 `<link>`。记住：运行时用的仍是普通 URDF。

对照文件：

- [`src/my_robot_description/urdf/my_robot.urdf.xacro`](../src/my_robot_description/urdf/my_robot.urdf.xacro)
- [`src/my_robot_description/urdf/mobile_base.xacro`](../src/my_robot_description/urdf/mobile_base.xacro)
- [`src/my_robot_description/urdf/common_properties.xacro`](../src/my_robot_description/urdf/common_properties.xacro)
- [`src/my_robot_description/urdf/mobile_base.ros2_control.xacro`](../src/my_robot_description/urdf/mobile_base.ros2_control.xacro)

## 笔记

Xacro（XML Macros）是 URDF 的预处理层。你编辑 `.xacro`，`xacro` 命令把它展开成一份没有 `xacro:*` 标签的 URDF。`robot_state_publisher`、RViz、`ros2_control` 吃的是展开结果。

### 总入口：include 拼文件

```xml
<robot name="my_robot" xmlns:xacro="http://www.ros.org/wiki/xacro">
    <xacro:include filename="common_properties.xacro" />
    <xacro:include filename="mobile_base.xacro" />
    <xacro:include filename="mobile_base.ros2_control.xacro" />
</robot>
```

三份文件各自也有 `<robot>` 根。include 时，xacro 把**内部内容**拼进入口的 `<robot name="my_robot">`。拆文件是为了：颜色、几何、控制接口分开维护。

`xmlns:xacro="..."` 打开 `xacro:` 前缀。没有它，`<xacro:property>` 只是非法/未知 XML。

### property：命名尺寸

```xml
<xacro:property name="base_length" value="0.6" />
```

后面用 `${base_length}` 引用，也可以算：

```xml
${base_height / 2.0}
${-(base_width + wheel_length) / 2.0}
${pi / 2.0}
```

`pi` 是 xacro 内置常量。展开后这些表达式变成普通数字，URDF 里不会留下 `${}`。

改轮半径：只改 `wheel_radius` 一处。但要想清楚哪些地方用了它（`base_joint` 的 Z、万向轮半径和 Z、圆柱半径）。尺寸是耦合的，这正是用变量的原因。

### macro：重复零件

```xml
<xacro:macro name="wheel_link" params="prefix">
    <link name="${prefix}_wheel_link">
        ...
    </link>
</xacro:macro>

<xacro:wheel_link prefix="right" />
<xacro:wheel_link prefix="left" />
```

`params="prefix"` 声明参数。调用时 `prefix="right"` 会把宏体里的 `${prefix}` 换成 `right`。

展开后应得到两个完整 link（几何相同、名字不同）：

```xml
<link name="right_wheel_link">
    <visual>
        <geometry>
            <cylinder radius="0.1" length="0.05" />
        </geometry>
        <origin xyz="0 0 0" rpy="1.5707... 0 0" />
        <material name="grey" />
    </visual>
</link>

<link name="left_wheel_link">
    <!-- 除了 name，其余相同 -->
</link>
```

`rpy` 里的 `pi/2` 会变成约 `1.5708`。宏**只生成了 link**，左右轮的 joint 仍是下面分开写的——因为 origin 的 Y 符号相反，用宏也可以，但作者选择只复用 link 几何。

### 和纯 URDF 的关系

| 你写的 | 展开后 |
|---|---|
| `xacro:property` / `xacro:macro` / `xacro:include` | 消失 |
| `${...}` | 数字或字符串 |
| `<link>` / `<joint>` / `<ros2_control>` | 原样保留（表达式已算完） |

自己看展开结果（在已 source 的容器里）：

```bash
xacro /workspace/src/my_robot_description/urdf/my_robot.urdf.xacro
```

输出里应能搜到 `right_wheel_link`、`left_wheel_link`，不应再有 `xacro:macro`。

## 对照源码阅读

1. 从 `my_robot.urdf.xacro` 列出三个 include 各自贡献什么。
2. 在 `mobile_base.xacro` 圈出所有 `${...}`，确认每个变量都有对应 property（或 `pi`）。
3. 不看电脑，在纸上写出 `prefix="left"` 展开后的整个 `<link>`。

## 练习题

1. xacro 是另一种机器人描述格式，还是 URDF 的预处理？运行时谁消费展开结果？

2. 入口文件为什么几乎没有几何，只做 include？

3. `wheel_radius` 在 `mobile_base.xacro` 里至少用在哪三处？若只改圆柱半径、不改 `base_joint` 的 Z，模型会怎样？

4. 手写：`xacro:wheel_link prefix="right"` 展开后，`<link>` 的 `name` 是什么？

5. 宏生成了左右轮的 **link**，但没有生成它们的 **joint**。关节为什么要分开写？若也用宏生成关节，参数里至少还需要什么？

6. `${pi / 2.0}` 展开后大概是什么数？它出现在 joint 里还是 visual 里？

7. `common_properties.xacro` 里的 `<robot>` 没有 `name="my_robot"`。include 之后，最终机器人的名字以谁为准？

8. 判断对错：不跑 `xacro`、直接把 `.xacro` 文件内容塞给 `robot_state_publisher`，`${base_length}` 也能被 URDF 解析器算出来。

9. 写一条命令，把本机入口 xacro 打印成 URDF（路径按容器内 `/workspace/...` 写即可）。
