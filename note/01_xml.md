# 01 XML 够用就停

## 目标

会读 URDF / xacro 里出现的 XML：标签、属性、嵌套、自闭合、注释。不学 Schema、DTD、命名空间理论。

对照文件：[`src/my_robot_description/urdf/mobile_base.xacro`](../src/my_robot_description/urdf/mobile_base.xacro)

## 笔记

URDF 碰巧用 XML 来写。XML 在这里只是「带名字的括号」：把结构 nested 起来，把小信息挂在属性上。

### 标签成对出现

```xml
<link name="base_link">
    ...
</link>
```

- `<link>` 是开始标签，`</link>` 是结束标签。
- 中间可以再放别的标签，这叫**嵌套**。
- 标签名大小写敏感，URDF 里都是小写。

### 属性写在开始标签里

```xml
<link name="base_link">
```

`name="base_link"` 是属性：名字叫 `name`，值是字符串 `base_link`。一个标签可以有多个属性：

```xml
<joint name="base_joint" type="fixed">
```

这里有两个属性：`name` 和 `type`。

### 自闭合标签

没有子内容时，可以写成一个标签，末尾加 `/`：

```xml
<link name="base_footprint" />
```

等价于 `<link name="base_footprint"></link>`。本机的 `base_footprint` 就是空的：没有 visual、没有子标签。

另一处常见自闭合：

```xml
<box size="${base_length} ${base_width} ${base_height}" />
<axis xyz="0 1 0" />
```

### 嵌套表达「谁属于谁」

```xml
<link name="base_link">
    <visual>
        <geometry>
            <box size="..." />
        </geometry>
        <origin xyz="0 0 0.1" rpy="0 0 0" />
        <material name="blue" />
    </visual>
</link>
```

读法：`box` 属于 `geometry`，`geometry` / `origin` / `material` 属于 `visual`，`visual` 属于 `link`。

**父子关系看缩进（以及真正的嵌套），不看谁写在文件前面。** 本文件里所有 `<link>` 先写完，再写 `<joint>`，但关节仍然能连到前面定义的 link——因为关节用 `parent` / `child` 属性按**名字**引用，不是靠文件顺序。

### 注释

```xml
<!-- 这是注释，展开后不会变成机器人的一部分 -->
```

### 文件头两行在说什么

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
```

- 第一行：这是 XML 文件。
- `<robot>` 是整份 URDF 的根标签，所有 link / joint 都在它里面。
- `xmlns:xacro="..."` 表示「下面可以用 `xacro:` 开头的标签」。06 课再讲 xacro。现在看到 `<xacro:property>` 就把它当成「特殊标签」即可。

### 文本内容 vs 属性

两种放数据的方式你都会见到：

| 写法 | 例子 | 数据在哪 |
|---|---|---|
| 属性 | `<joint name="base_joint" type="fixed">` | 标签头上 |
| 子标签 | `<parent link="base_footprint" />` | 嵌套进去 |

URDF 混用这两种，没有统一风格。读的时候问自己：这个信息是属性，还是子标签？

## 对照源码阅读

打开 `mobile_base.xacro`，完成这三件事：

1. 找出根标签 `<robot>` 和它的结束标签 `</robot>`。
2. 数一数有几个 `<link>`、几个 `<joint>`（宏调用 `xacro:wheel_link` 也算将要生成 link，先记下有两次调用）。
3. 任选一个 `<joint>`，指出它的属性有哪些、子标签有哪些。

## 练习题

1. 下面这段里，`type` 是标签名还是属性名？
   ```xml
   <joint name="base_joint" type="fixed">
   ```

2. `<link name="base_footprint" />` 和 `<link name="base_footprint"></link>` 有没有区别？

3. 在下面这段中，`<origin>` 的直接父标签是谁？
   ```xml
   <link name="base_link">
       <visual>
           <geometry>
               <box size="0.6 0.4 0.2" />
           </geometry>
           <origin xyz="0 0 0.1" rpy="0 0 0" />
       </visual>
   </link>
   ```

4. `<box size="0.6 0.4 0.2" />` 为什么末尾有 `/`？如果写成 `<box size="0.6 0.4 0.2">` 却不写 `</box>`，行不行？

5. `mobile_base.xacro` 里 `<parent link="base_footprint" />` 的 `link` 是属性。它引用的是哪个标签？靠什么对上号的——文件顺序，还是名字？

6. 判断对错：XML 里标签写在文件前面的，就是树里的父节点。

7. `xmlns:xacro="http://www.ros.org/wiki/xacro"` 对 URDF 几何本身有没有影响？你现在需要理解这个 URL 指向的网页内容吗？

8. 从 `mobile_base.xacro` 里抄出一个同时带**两个属性**的开始标签（不含 xacro）。
