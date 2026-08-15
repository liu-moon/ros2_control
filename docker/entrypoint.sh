#!/bin/bash
set -e

# Bring up the virtual desktop (Xvfb + fluxbox + x11vnc + noVNC), idempotent.
/usr/local/bin/start-vnc.sh

# Source the base ROS2 install.
source /opt/ros/jazzy/setup.bash

# If the workspace has already been built at least once, overlay it too,
# so every shell/exec automatically has your packages on the path.
if [ -f /workspace/install/setup.bash ]; then
    source /workspace/install/setup.bash
fi

exec "$@"
