# run_mcp_inspector.py
# This file sits in the project root directory.

# Ensure 'src' is treated correctly (Poetry often handles this,
# but adding explicitly can sometimes help tools that access the directory directly)

# For example, when running the Model Context Protocol inspector tool via the command:
# poetry run mcp dev src/chesspal_mcp_engine/main.py
# it fails with the error:
# ImportError: attempted relative import with no known parent package
# This files allows the workaround of:
# poetry run mcp dev run_mcp_inspector.py


# Import the app object using its absolute path
# This import is required by mcp dev, even though it's not used directly in this file
from chesspal_mcp_engine.main import app  # noqa: F401

# No need for more code here. `mcp dev` just needs to be able to import `app` from this file.
