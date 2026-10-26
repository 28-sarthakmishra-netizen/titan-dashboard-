#!/bin/bash
# Double-click this file on a Mac (or run: bash run_dashboard.command) to start the Titan dashboard.
cd "$(dirname "$0")"
echo "Checking / installing required libraries (first time takes 1-2 minutes)..."
python3 -m pip install -r requirements.txt
echo "Starting the Titan dashboard... it will open in your browser."
python3 -m streamlit run app.py --server.headless false
