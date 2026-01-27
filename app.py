# Entry point for Streamlit Cloud deployment
# This file redirects to the main application

import sys
import os

# Add the App directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AI-Resume-Analyzer', 'App'))

# Change working directory to App folder so relative paths work
os.chdir(os.path.join(os.path.dirname(__file__), 'AI-Resume-Analyzer', 'App'))

# Import and run the main app
from App import run

if __name__ == "__main__":
    run()
