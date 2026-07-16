# Environment Setup

Follow these steps to set up the development environment for Perfume Scanner:

## 1. Prerequisites
- Python 3.8 or higher installed.

## 2. Create a Virtual Environment
Run the following command to create a virtual environment named `.venv`:
```
python -m virtualenv .venv
```

## 3. Activate the Virtual Environment
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Windows (CMD):** `.venv\Scripts\activate.bat`
- **macOS/Linux:** `source .venv/bin/activate`

## 4. Install Dependencies
Install the required packages using the `requirements.txt` file located in this directory:
```
pip install -r environment/requirements.txt
```
