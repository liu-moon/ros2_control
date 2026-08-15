FROM ros:jazzy

# ---- system packages -------------------------------------------------
# ros2_control stack, Gazebo simulation, GUI tools (rviz2/rqt), and dev tools.
# Add more apt packages here as your project grows.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    # ros2_control stack
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-control-msgs \
    # simulation (Gazebo + ROS bridge for Jazzy)
    ros-jazzy-ros-gz \
    ros-jazzy-gz-ros2-control \
    # GUI tools
    ros-jazzy-rviz2 \
    ros-jazzy-rqt \
    ros-jazzy-rqt-common-plugins \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-xacro \
    ros-jazzy-robot-state-publisher \
    x11-apps \
    # virtual desktop (Xvfb + fluxbox + x11vnc + noVNC) -- XQuartz's indirect
    # GLX can't satisfy rviz2/Gazebo's OpenGL context requests, so GUI apps
    # render into this self-contained virtual display instead, viewable at
    # http://localhost:6080 in any browser. Software GL via llvmpipe (part of
    # the mesa packages already pulled in by rviz2/Gazebo).
    xvfb \
    fluxbox \
    x11vnc \
    novnc \
    websockify \
    x11-utils \
    mesa-utils \
    # dev tools
    build-essential \
    git \
    curl \
    vim \
    nano \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

# rosdep may already be initialized in the base image; guard against re-init failing.
RUN if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then rosdep init; fi \
    && rosdep update

# Auto-source ROS (+ the workspace overlay once built) for every interactive
# shell, including `docker compose exec ... bash` which bypasses ENTRYPOINT.
RUN echo '\n# ROS2 environment\nsource /opt/ros/jazzy/setup.bash\nif [ -f /workspace/install/setup.bash ]; then source /workspace/install/setup.bash; fi' >> /etc/bash.bashrc

# ---- non-root user -----------------------------------------------------
# Avoids root-owned files appearing on the host through the src/ bind mount.
# The ros:jazzy base (Ubuntu Noble) already ships a UID/GID 1000 "ubuntu" user
# -- reuse it instead of creating a new one (avoids a GID collision).
ARG USERNAME=ubuntu
RUN mkdir -p /workspace \
    && chown -R ${USERNAME}:${USERNAME} /workspace

COPY --chown=${USERNAME}:${USERNAME} entrypoint.sh /entrypoint.sh
COPY start-vnc.sh /usr/local/bin/start-vnc.sh
RUN chmod +x /entrypoint.sh /usr/local/bin/start-vnc.sh

USER ${USERNAME}
WORKDIR /workspace

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
