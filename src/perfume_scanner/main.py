"""Main entry point for Perfume Scanner."""

import os
import runpy
import sys

import streamlit as st


def main() -> None:
    """Starts the Streamlit web application programmatically."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "app.py")

    # If already running inside Streamlit runtime (e.g. Streamlit Cloud)
    if st.runtime.exists():
        runpy.run_path(app_path, run_name="__main__")
        return

    import streamlit.web.cli as stcli

    # Configure arguments to invoke Streamlit's main runner
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
