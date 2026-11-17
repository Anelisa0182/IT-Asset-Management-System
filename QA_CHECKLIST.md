# Portfolio Edition — Quality Assurance Checklist

Review date: 2026-11-17

## Checks completed in an isolated test environment

| Area | Result |
|---|---|
| All three Python files compile and parse successfully | PASS |
| Application module imports resolve with pandas and openpyxl installed | PASS |
| Fresh database initialization and administrator bootstrap | PASS |
| Password verification, wrong-password rejection and account deactivation | PASS |
| Administrator-only user creation, activation and password reset checks | PASS |
| Employee can see and verify only assets linked to their account in tested workflows | PASS |
| CSV import, preview, duplicate handling and synchronisation | PASS |
| Re-import preserves IT-managed fields such as condition and assignment | PASS |
| Asset assignment, transfer, repair and return transactions | PASS |
| Useful-life depreciation and warranty calculations | PASS |
| Excel audit workbook generation (eight worksheets) | PASS |
| Formula-like imported text is not written as an Excel cell formula | PASS |
| Tkinter first-run setup and existing-user login dialogs launch (virtual display) | PASS |
| GUI employee visibility and logout cleanup (virtual display) | PASS |
| Main `python Real_Test.py` entry point launches and remains open (virtual display) | PASS |
| `.gitignore` excludes local databases, input registers and output reports | PASS |
| Static scan found no obvious hardcoded passwords, external API keys or network imports | PASS (limited static scan) |

Automated backend test command:

```bash
python -m unittest discover -s tests -v
```

Seven automated backend test cases passed in the build environment. Tkinter was additionally smoke-tested using a virtual graphical display.

## Still recommended before publication or production use

- Manually run through all screens on the target Windows machine and take screenshots with fictional data.
- Confirm that you are permitted to publish the underlying source code.
- Run a professional security review before handling genuine employee or asset information.
- Treat this as a **local portfolio demonstration**, not a production-grade multi-user system. SQLite files can be accessed outside the GUI by someone with file-system access; the application has no independent server authorization boundary.
- Validate report layouts with the target version of Microsoft Excel and test import files from the intended source system.

No live workplace data or real user credentials were used in these checks.
