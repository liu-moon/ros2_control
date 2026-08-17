# ros2_control — Dockerized dev environment (ROS 2 Jazzy)

This repo separates **environment** (Docker image: ROS 2 Jazzy + ros2_control +
Gazebo + rviz2/rqt + dev tools) from **source** (`src/`, bind-mounted, edited on
the host and built with `colcon` inside the container).

## GUI apps (rviz2, rqt, Gazebo)

GUI apps run on a self-contained virtual desktop *inside* the container (Xvfb +
fluxbox + x11vnc + noVNC), viewable in any browser — no host X server needed.

> We tried XQuartz's X11 forwarding first, but its indirect GLX implementation
> can't satisfy the OpenGL context rviz2/Gazebo request (`BadValue` /
> `X_GLXCreateNewContext` errors) — a known dead end on macOS. The container
> now renders with Mesa's software rasterizer (llvmpipe) into its own virtual
> display instead, which is what actually works reliably.

1. `docker compose up -d` (the entrypoint starts the virtual desktop automatically)
2. Open **http://localhost:6080/vnc.html** in a browser, click **Connect**
3. Run GUI apps from a container shell (`docker compose exec ros2_control bash`)
   — their windows appear in that browser tab

No password is set on the VNC server; the port is bound to `127.0.0.1` only,
so it's not reachable outside your machine.

## Run (use the prebuilt image)

The image is published as `liumoon710/ros2:jazzy-dev`. Pull it and start — no local `docker compose build` needed:

```
docker pull liumoon710/ros2:jazzy-dev
docker compose up -d
docker compose exec ros2_control bash
```

## Build (only if you change the Dockerfile)

```
docker compose build
```

## Inside the container

```
cd /workspace
colcon build
source install/setup.bash
```

Put your ROS 2 packages under `src/` on the host — they show up at
`/workspace/src` in the container immediately, no rebuild needed. Only rebuild
the image (`docker compose build`) when you add new system/apt dependencies to
`docker/Dockerfile`.

## Verify the setup

- `ros2 pkg list | grep ros2_control` — confirms the ros2_control packages installed
- `xeyes` — with http://localhost:6080/vnc.html open and connected, run this in
  a container shell; a window should appear in the browser tab, confirming the
  virtual display works, before trying rviz2/Gazebo

## URDF → Blender

To flatten a URDF/XACRO and import it into Blender on the host (for tutorial
videos), run `python3 scripts/urdf_blender_web.py` and open
http://127.0.0.1:8765 — or see [scripts/README.md](scripts/README.md).
