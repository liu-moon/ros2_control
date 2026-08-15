# ros2_control — Dockerized dev environment (ROS 2 Jazzy)

This repo separates **environment** (Docker image: ROS 2 Jazzy + ros2_control +
Gazebo + rviz2/rqt + dev tools) from **source** (`src/`, bind-mounted, edited on
the host and built with `colcon` inside the container).

## One-time host setup (macOS)

GUI apps (rviz2, rqt, Gazebo) need an X server on the Mac since Docker Desktop
does not forward a display or GPU into Linux containers by default.

1. Install XQuartz: `brew install --cask xquartz`
2. Open XQuartz → Preferences → Security → check **"Allow connections from
   network clients"**
3. Fully quit and restart XQuartz for the setting to take effect
4. Every time XQuartz (re)starts, allow local connections:
   ```
   xhost + 127.0.0.1
   ```

> Rendering runs in software (no GPU passthrough on macOS), so Gazebo/rviz2 will
> be usable but not fast. If that becomes a problem, a VNC/noVNC-based container
> desktop is a good next step — not set up here yet.

## Build

```
docker compose build
```

## Run

```
docker compose up -d
docker compose exec ros2_control bash
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
- `xeyes` — should pop up a window on your Mac desktop, confirming X11 forwarding
  works, before trying rviz2/Gazebo
