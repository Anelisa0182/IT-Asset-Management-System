# IT Asset Management System — Portfolio Edition

A Python desktop application for managing and verifying IT assets. Built with **Tkinter**, **SQLite**, **pandas** and **openpyxl**. This repository is a **local demonstration**, intended for learning and portfolio review, using **fictional sample data only**.

## Features

- Login with first-run administrator setup; salted PBKDF2-SHA256 password hashes
- Administrator, IT Officer, Employee and Viewer interface roles
- Employee view restricted to assets linked to the signed-in employee; employee verification checks the account-to-asset link in the database
- Add assets, assign assets, transfer assets and track repairs and returns
- Import and synchronise CSV/XLSX asset registers, with preview and duplicate detection
- Warranty status, straight-line depreciation, useful-life calculations and book-value summaries
- Asset history and audit transactions
- Excel audit report with dashboard, register, duplicate and data-quality worksheets
- Resizable interface, zoom controls and date pickers

## Requirements

- **Python 3.10+** with Tkinter (included with the standard Windows Python installer)
- Windows recommended for the desktop interface; Tkinter also works on many Linux/macOS systems with a graphical display
- Python packages listed in `requirements.txt`

## Run the application

Open a terminal in the extracted project folder:

```bash
python -m pip install -r requirements.txt
python Real_Test.py
```

On Windows, you can alternatively double-click `start_windows.bat` after Python and the dependencies are installed.

At first launch, **create your own administrator account**. There are no pre-set usernames or passwords. Local SQLite files are created automatically under `data/` and are **excluded from Git**.

## Try the fictional demonstration data

1. Create an administrator account and sign in.
2. Copy `demo_data/sample_assets.csv` into the `input/` folder (create `input/` if needed).
3. Select **Import & Synchronise** in the application, review the results and confirm the import.
4. Open **Dashboard / View All**, search for an asset or view its details.
5. Optionally create an **Employee** account using **Manage Users**, then link a demo asset to that account through **Link Assignments**. Sign in as that employee to try **My Assets** and **Verify My Asset**.
6. Select **Export Audit Report** to create an Excel workbook under `output/`.

**Important:** The sample CSV contains invented asset IDs, facilities, suppliers and serial numbers. Never add genuine workplace asset registers, real staff records or account databases to this repository.

## Project structure

```text
IT_Asset_Management_GitHub_Ready/
├── Real_Test.py             # Application entry point, import and reporting logic
├── gui.py                   # Tkinter user interface and login workflow
├── database.py              # SQLite schema, asset operations and authentication
├── requirements.txt         # Third-party Python dependencies
├── start_windows.bat        # Windows launcher
├── demo_data/
│   └── sample_assets.csv    # Fictional import data
├── tests/
│   └── test_application.py  # Automated backend tests
├── SECURITY.md              # Security scope and limitations
├── QA_CHECKLIST.md          # Tests performed and remaining checks
├── README.md
└── .gitignore               # Excludes live data, reports and local secrets
```

The `data/`, `input/` and `output/` folders are created locally when needed and should never be committed with real records.

## Run automated tests

```bash
python -m unittest discover -s tests -v
```

See [QA_CHECKLIST.md](QA_CHECKLIST.md) for the checks completed and remaining limitations. The tests use temporary SQLite databases and fictional records. They do not require a graphical display. A separate Tkinter launch smoke test can be run on a computer with a desktop display.

## Design notes

The program uses a local SQLite database, not a central server. Interface role restrictions are appropriate for demonstrating the workflow, but **do not make a shared or compromised workstation a secure multi-user environment**. Users who can read or modify the SQLite database directly can bypass application-level controls. See [SECURITY.md](SECURITY.md) before using the software beyond a portfolio demo.

Depreciation uses a configurable useful life (five years by default), straight-line calculation and a default residual value of zero. These are demonstration assumptions, not an accounting policy recommendation.

## Public sharing

Publish this portfolio edition only if you have the right to share the underlying source code. Removing workplace data does **not** by itself establish ownership or permission to publish employer-developed software. If permission is unclear, keep the repository private and build an independently written public demo.

## Author

Software Developer — Python desktop applications, data management and IT asset workflows.
