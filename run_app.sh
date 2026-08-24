#!/usr/bin/env bash
# Launch the NFL Legends Benefits Brain Streamlit app
cd "$(dirname "$0")"
echo "Starting NFL Legends Benefits Brain..."
echo "Open the URL shown below in your browser."
echo ""
exec streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
