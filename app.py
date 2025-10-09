"""
Streamlit Cloud App Entry Point

This file ensures demo mode is active when deployed to Streamlit Cloud.
It imports and runs the main streamlit_app.py with demo mode forced on.
"""

import os
import sys
from pathlib import Path

# Force demo mode for Streamlit Cloud deployment
os.environ["DEMO_MODE"] = "true"

# Create demo mode marker file
demo_marker = Path("demo_mode")
demo_marker.touch()

# Import and run the main app
try:
    from streamlit_app import main
    
    if __name__ == "__main__":
        main()
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import main app: {e}")
    st.info("Please ensure all required files are present in the repository.")