# Perfume Scanner

A premium, interactive web application to scan, compare, and track perfume listings across 14 specialty retailers in India in real-time. Featuring a stunning glassmorphic dark interface, dynamic animations, and atomizer audio feedback.

## Project Structure

```text
PerfumeScanner/
├── .github/
│   └── workflows/
│       └── ci.yml            # CI Pipeline (Ruff + Bandit SCA)
├── src/
│   └── perfume_scanner/
│       ├── __init__.py       # Package definition
│       ├── app.py            # Streamlit Red & Black visual front-end
│       ├── comparator.py     # Pricing comparison engine
│       ├── main.py           # Launch script entry point
│       └── scraper.py        # Real-time multi-platform scraper
├── tests/
│   ├── __init__.py
│   └── test_main.py          # Parser and sizing coverage tests
├── pyproject.toml            # Package metadata & tool configs
├── requirements.txt          # Python dependencies list
└── README.md                 # Project documentation
```

## Setup Instructions

### 1. Prerequisites

Ensure you have **Python 3.12** or higher installed.

### 2. Environment Activation

#### Windows (PowerShell)
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1
```

#### Windows (Command Prompt)
```cmd
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate.bat
```

#### Bash (Linux / macOS / Git Bash / WSL)
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

### 3. Install Dependencies

Run the following command to install the required packages:

```bash
pip install -r requirements.txt
```

---

## Running the Application Locally

Start the Streamlit application server by running the launch entry point:

```bash
# Run via python module entry point
python -m perfume_scanner.main
```

Once the server has started, open your web browser and navigate to:
**[http://localhost:8501](http://localhost:8501)**

---

## Running Linting & Security Scans

Verify code compliance and security locally using the same tooling configured in our CI pipeline:

```bash
# Run Ruff Linter
ruff check .

# Run Bandit Security Scan (fails only if high-severity items are found)
bandit -r src/ -lll
```

---

## Running Tests

Run the test suite using Python's built-in unit test runner:

```bash
python -m unittest discover -s tests
```
