#!/bin/bash
python script.py &
# Keep the web service alive to satisfy Render's port check
while true; do echo "alive"; sleep 60; done