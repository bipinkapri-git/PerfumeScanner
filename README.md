# Perfume Scanner

A Python-based application for scanning and identifying perfumes.

## Project Structure

```text
PerfumeScanner/
├── .git/                 # Git repository configuration
├── .gitignore            # Files ignored by Git
├── pyproject.toml        # PEP 621 packaging metadata
├── requirements.txt      # Project development dependencies
├── README.md             # Project documentation
├── src/
│   └── perfume_scanner/
│       ├── __init__.py   # Package initialization
│       └── main.py       # Main entry point and scanner logic
└── tests/
    ├── __init__.py       # Test suite initialization
    └── test_main.py      # Unit tests for main scanner logic
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher installed on your machine.

### 2. Local Environment Setup

Initialize a Python virtual environment to keep dependencies isolated:

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate virtual environment (Windows CMD)
.venv\Scripts\activate.bat

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate
```

### 3. Install Dependencies

Install the project in editable mode with development dependencies:

```powershell
pip install -r requirements.txt
```

This will automatically load settings from `pyproject.toml` and configure the command-line entry point `perfume-scanner`.

## Running the Application

After activating the environment, you can run the entry point script directly:

```powershell
python src/perfume_scanner/main.py
```

Or, if installed via `pip`, run the command-line shortcut:

```powershell
perfume-scanner
```

## Running Tests

Execute the unit tests using Python's built-in `unittest` runner:

```powershell
python -m unittest discover -s tests
```
