"""Main entry point for Perfume Scanner."""

import os
import sys
import streamlit.web.cli as stcli


def main() -> None:
    """Starts the Streamlit web application programmatically."""
    # Find the path of the app.py file relative to this main.py file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "app.py")
    
    # Configure arguments to invoke Streamlit's main runner
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
