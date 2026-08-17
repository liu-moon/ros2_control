#!/bin/bash
# Starts a self-contained virtual desktop: Xvfb (virtual X display) + fluxbox
# (window manager) + x11vnc (VNC server) + websockify/noVNC (browser client).
# Idempotent - safe to call every time the container starts.
#
# Background processes are started with setsid so they are not killed by SIGHUP
# when this script exits (the entrypoint runs us, then exec's the user command).
set -e

DISPLAY_NUM=1
RESOLUTION=1920x1080x24
export DISPLAY=:${DISPLAY_NUM}

start_bg() {
    setsid "$@" >/dev/null 2>&1 &
}

if ! pgrep -f "Xvfb :${DISPLAY_NUM}" > /dev/null; then
    rm -f "/tmp/.X11-unix/X${DISPLAY_NUM}" "/tmp/.X${DISPLAY_NUM}-lock"
    start_bg Xvfb :${DISPLAY_NUM} -screen 0 ${RESOLUTION}
    for i in $(seq 1 20); do
        xdpyinfo -display :${DISPLAY_NUM} > /dev/null 2>&1 && break
        sleep 0.5
    done
fi

if ! pgrep -x fluxbox > /dev/null; then
    start_bg fluxbox
fi

if ! pgrep -x x11vnc > /dev/null; then
    start_bg x11vnc -display :${DISPLAY_NUM} -forever -shared -nopw -quiet -rfbport 5900
fi

if ! pgrep -f websockify > /dev/null; then
    start_bg websockify --web=/usr/share/novnc 6080 localhost:5900
fi
