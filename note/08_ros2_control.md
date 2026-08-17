# 08 ros2_control 接口

## 目标

看懂 URDF 里的 `<ros2_control>` 块：mock 硬件、command/state interface、关节名必须和 URDF 一致。点到 bringup YAML 里的轮名和半径，不展开完整启动流程。

对照文件：

- [`src/my_robot_description/urdf/mobile_base.ros2_control.xacro`](../src/my_robot_description/urdf/mobile_base.ros2_control.xacro)
- [`src/my_robot_bringup/config/my_robot_controllers.yaml`](../src/my_robot_bringup/config/my_robot_controllers.yaml)（只看轮名、半径、`base_frame`）

## 笔记

前几课描述「机器人长什么样、关节怎么连」。`<ros2_control>` 描述「控制器能读写哪些硬件接口」。它写在 URDF/xacro 里，随 `robot_description` 一起被 `ros2_control` 的 controller_manager 解析。

几何（`mobile_base.xacro`）和接口（`mobile_base.ros2_control.xacro`）分开，由入口 include 拼在一起（06 课）。

### 整块在说什么

```xml
<ros2_control name="MobileBaseHardwareInterface" type="system">
    <hardware>
        <plugin>mock_components/GenericSystem</plugin>
        <param name="calculate_dynamics">true</param>
    </hardware>
    <joint name="base_left_wheel_joint">
        <command_interface name="velocity" />
        <state_interface name="position" />
        <state_interface name="velocity" />
    </joint>
    <joint name="base_right_wheel_joint">
        ...
    </joint>
</ros2_control>
```

分层（先有这个印象即可）：

```
控制器（如 diff_drive_controller）
    ↓ 写 command，读 state
Resource Manager / ros2_control
    ↓
硬件插件（本机是 mock GenericSystem）
```

本课只看最下面：插件是谁、每个关节暴露哪些接口。

### mock 硬件

```xml
<plugin>mock_components/GenericSystem</plugin>
<param name="calculate_dynamics">true</param>
```

没有真电机。`GenericSystem` 在软件里假装有一套执行器：你写速度指令，它按积分更新位置/速度状态（`calculate_dynamics` 为 true 时）。适合在没有车的情况下把控制链路跑通。

换成真机器人时，这里会变成你自己的硬件插件名，**关节名和 interface 名字尽量保持不变**，上面的控制器就不用改。

### command vs state

| 接口 | 方向 | 本机驱动轮 |
|---|---|---|
| `command_interface` | 控制器 → 硬件 | `velocity`（要的轮速，rad/s） |
| `state_interface` | 硬件 → 控制器 | `position`、`velocity`（当前角、角速度） |

差速控制器根据 `cmd_vel` 算出左右轮目标速度，写入 `velocity` command；再读 state 做里程计等。它**不**给轮子写位置指令——轮子是速度控制，不是「转到某角度停住」。

万向轮没有写进 `<ros2_control>`：它是 fixed，没有可控制的关节。

### 名字必须对上

`<joint name="base_left_wheel_joint">` 必须和 URDF 里那个 `continuous` 关节同名。对不上，controller_manager 加载会失败。

bringup 的 YAML 再对一次：

```yaml
left_wheel_names: ["base_left_wheel_joint"]
right_wheel_names: ["base_right_wheel_joint"]
wheel_separation: 0.45
wheel_radius: 0.1
base_frame: "base_footprint"
```

- 轮名 = URDF joint 名 = ros2_control 块里的 joint 名。
- `wheel_radius: 0.1` = xacro 的 `wheel_radius`。
- `wheel_separation: 0.45` = 03 课算的两轮 Y 差 `(base_width + wheel_length)`。
- `base_frame: "base_footprint"` = 02/07 课的根坐标系。

三处（URDF 几何、ros2_control 块、控制器 YAML）是同一台车的三份说明书，数字和名字必须一致。

### 和 07 课 display launch 的差别（概念）

`display.launch.py` 用 `joint_state_publisher_gui` **假装**关节在动，不经过 ros2_control。

真正控制时：`ros2_control_node` 读同一份 `robot_description`（含 `<ros2_control>`），再 spawn `joint_state_broadcaster` 和 `diff_drive_controller`。那时 `/joint_states` 来自 broadcaster，不再来自 gui。

怎么启动那条链路，是下一阶段（bringup）。本课只要能读接口文件、能把名字对到 YAML。

## 对照源码阅读

1. 在 `mobile_base.ros2_control.xacro` 列出：插件名、两个关节、每个关节的 command/state。
2. 在 `mobile_base.xacro` 确认这两个名字确实是 `continuous` 关节。
3. 在 `my_robot_controllers.yaml` 核对 `left_wheel_names`、`right_wheel_names`、`wheel_radius`、`wheel_separation`、`base_frame`。

## 练习题

1. `<ros2_control>` 写在 description 包里，却不是几何。它解决什么问题？

2. `mock_components/GenericSystem` 和真电机插件的差别是什么？为什么教学阶段用 mock？

3. 左右轮各有哪些 command_interface、哪些 state_interface？差速控制为什么 command 用 velocity 而不是 position？

4. 为什么 `caster_wheel_link` 对应的关节没有出现在 ros2_control 块里？

5. 若把 ros2_control 里的关节名写成 `left_wheel_joint`（少了 `base_` 前缀），而 URDF 仍是 `base_left_wheel_joint`，会怎样？

6. YAML 里 `wheel_separation: 0.45` 是怎么从 `mobile_base.xacro` 的 property 算出来的？若只改 YAML 为 `0.4`、不改 URDF，会出现什么概念上的错误？

7. `base_frame: "base_footprint"` 和 02、07 课有什么对应关系？

8. 判断对错：`display.launch.py` 已经加载了 `<ros2_control>` 块，所以启动 display 就等于启动了 diff_drive_controller。

9. 从文件名/包名区分：哪份文件描述外形和关节树？哪份声明硬件接口？哪份配置控制器参数？

10. 下一阶段要学的是什么？（用一句话：把接口接到 controller_manager / spawner / cmd_vel。）
