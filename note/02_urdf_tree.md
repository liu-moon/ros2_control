# 02 机器人是一棵树

## 目标

能画出本机全部 link 和 joint 组成的树，说清 `parent` / `child` 的方向，解释为什么 `base_footprint` 是空 link。

对照文件：[`src/my_robot_description/urdf/mobile_base.xacro`](../src/my_robot_description/urdf/mobile_base.xacro)

## 笔记

URDF 描述的不是一张网，而是一棵**树**：

- **link**：一块刚体（或一个坐标系）。车身、轮子都是 link。
- **joint**：两个 link 之间的约束。它指定谁是父、谁是子、子相对父怎么放、能动什么。

每个 joint 恰好连一对：

```xml
<joint name="base_joint" type="fixed">
    <parent link="base_footprint" />
    <child link="base_link" />
    ...
</joint>
```

读法：`base_footprint` 是父，`base_link` 是子。树的箭头从父指向子。

规则：

- 整棵树只有一个根（没有父关节的那个 link）。
- 一个 link 可以有多个子关节，但不能有两个父关节。
- joint 用**名字**引用 link，所以文件里可以先写完所有 link 再写 joint。

### 本机的树

`mobile_base.xacro` 里实际有这些 link（宏展开后）：

| link | 怎么来的 |
|---|---|
| `base_footprint` | 直接写的空 link |
| `base_link` | 直接写的车身 |
| `right_wheel_link` | `xacro:wheel_link prefix="right"` |
| `left_wheel_link` | `xacro:wheel_link prefix="left"` |
| `caster_wheel_link` | 直接写的万向轮 |

关节：

| joint | parent | child | type |
|---|---|---|---|
| `base_joint` | `base_footprint` | `base_link` | fixed |
| `base_right_wheel_joint` | `base_link` | `right_wheel_link` | continuous |
| `base_left_wheel_joint` | `base_link` | `left_wheel_link` | continuous |
| `base_caster_wheel_joint` | `base_link` | `caster_wheel_link` | fixed |

画出来：

```
base_footprint          ← 根，贴地参考点
 └── base_joint (fixed)
      └── base_link     ← 车身
           ├── base_left_wheel_joint (continuous)  → left_wheel_link
           ├── base_right_wheel_joint (continuous) → right_wheel_link
           └── base_caster_wheel_joint (fixed)     → caster_wheel_link
```

驱动轮在车身后部两侧，万向轮在前部中间。下一课用 origin 把这句话变成数字。

### 为什么要一个空的 `base_footprint`

```xml
<link name="base_footprint" />
```

它没有 `<visual>`，在 RViz 里几乎看不见，但作为**根坐标系**很有用：

- 原点在地面、位于机器人投影的中心附近。
- `base_link` 通过 `base_joint` 被抬高一个轮半径，这样轮子才贴地、车身才离地。
- RViz 的 Fixed Frame 选 `base_footprint`，模型不会「埋进地里」。导航、里程计也常用它当车体参考（08 课会看到 `base_frame: "base_footprint"`）。

约定：`base_footprint` 在地面，`base_link` 在底盘上。两者用 fixed 关节连着，相对位置永远不变。

### 先定义、再连接

文件结构是「所有 link → 所有 joint」，不是「写一个零件立刻写它的关节」。读的时候不要按行号当树，要按 joint 的 parent/child 重建树。

## 对照源码阅读

打开 `mobile_base.xacro`：

1. 列出全部 `<link name="...">`（记住宏会生成 `right_wheel_link` 和 `left_wheel_link`）。
2. 对每个 `<joint>` 填一张三列表：名字、parent、child。
3. 在纸上画出上面那棵树，检查是否只有一个根、有没有 link 被两个 joint 同时当 child。

## 练习题

1. link 和 joint 的职责各是什么？能不能只有 link 没有 joint？

2. 根据源码，本机 URDF 树的根 link 是谁？你怎么判断的？

3. `base_link` 有几个子 link？分别通过哪个 joint 连上去？

4. 若把 `base_joint` 的 parent/child 对调，写成 parent=`base_link`、child=`base_footprint`，树还合法吗？语义上会发生什么？

5. 为什么 `base_footprint` 可以没有任何 `<visual>`，仍然必须存在？

6. 判断对错：文件里先出现的 link 一定是父 link。

7. `xacro:wheel_link prefix="right"` 展开后，生成的 link 名字是什么？它在树里的父 link 是谁？

8. 本机有没有「轮子连轮子」这种关节？为什么差速底盘通常不会这样连？

9. 用一句话描述：从 `left_wheel_link` 走到根，路径上经过哪些 joint？
