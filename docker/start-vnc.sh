#!/bin/bash
# Starts a self-contained virtual desktop: Xvfb (virtual X display) + fluxbox
# (window manager) + x11vnc (VNC server) + websockify/noVNC (browser client).
# Idempotent - safe to call every time the container starts.
set -e

DISPLAY_NUM=1
RESOLUTION=1280x800x24
export DISPLAY=:${DISPLAY_NUM}

if ! pgrep -f "Xvfb :${DISPLAY_NUM}" > /dev/null; then
    Xvfb :${DISPLAY_NUM} -screen 0 ${RESOLUTION} &
    for i in $(seq 1 20); do
        xdpyinfo -display :${DISPLAY_NUM} > /dev/null 2>&1 && break
        sleep 0.5
    done
fi

if ! pgrep -x fluxbox > /dev/null; then
    fluxbox > /dev/null 2>&1 &
fi

if ! pgrep -x x11vnc > /dev/null; then
    x11vnc -display :${DISPLAY_NUM} -forever -shared -nopw -quiet > /dev/null 2>&1 &
fi

if ! pgrep -f websockify > /dev/null; then
    websockify --web=/usr/share/novnc 6080 localhost:5900 > /dev/null 2>&1 &
fi
