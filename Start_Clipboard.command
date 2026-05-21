#!/bin/bash

echo "Starting Universal Clipboard Server..."

# 1. Navigate to the exact folder where this script is saved
cd "$(dirname "$0")"

# 2. Start a background timer that waits 2 seconds, then opens the web browser
(sleep 2 && open "http://localhost:5000") &

# 3. Start the Python server! (Macs use 'python3' instead of 'python')
# This keeps the terminal window busy. Closing the window kills the server.
python3 app.py