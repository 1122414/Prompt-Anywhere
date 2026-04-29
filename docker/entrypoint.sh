#!/bin/bash

Xvfb :99 -screen 0 1024x768x24 &

sleep 1

fluxbox &

x11vnc -display :99 -forever -nopw -listen 0.0.0.0 -rfbport 5900 &

websockify --web /usr/share/novnc 6080 localhost:5900 &

cd /app
python -m app.main &

wait
