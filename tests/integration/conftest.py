"""
Test configuration for integration tests.
"""
import os
import sys
from pathlib import Path

# Add the src directory to the Python path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Ensure environment variables are set for testing
# These should point to your actual MongoDB instance
if "MONGODB_URI" not in os.environ:
    # Default to localhost MongoDB - adjust if needed
    os.environ["MONGODB_URI"] = "mongodb://localhost:27017"

if "MONGODB_DATABASE" not in os.environ:
    # Use your configured database name
    os.environ["MONGODB_DATABASE"] = "polyagent_sessions"
