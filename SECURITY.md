# Security notes — Portfolio Edition

This repository is a **demonstration desktop application**, not a production security-certified asset register.

## What the demonstration implements

- Passwords are salted and hashed using PBKDF2-HMAC-SHA256 (not stored as plaintext).
- The first account is created locally by the operator; no default credentials are included.
- The GUI shows employee-linked assets only to the signed-in employee and restricts privileged controls by role.
- Employee verification validates the asset-to-user link at the database layer.
- User creation, activation and administrator password resets require an active administrator identity passed by the GUI, except first-run bootstrap.
- SQL values are generally parameterized; exported text is escaped to prevent formula-like spreadsheet values being treated as formulas.
- `.gitignore` excludes runtime databases, imported registers, generated reports and typical secret files.

## Important limitations

- SQLite is **not encrypted at rest**. Anyone with unrestricted access to the computer or database file can inspect or modify records, including user accounts.
- The program is a **local desktop app**. It does not provide server-enforced sessions, centrally managed permissions or a tamper-resistant audit trail. Passing a user ID to a backend function is not equivalent to a server-authenticated request.
- Not all backend asset-management functions independently enforce roles; the GUI provides the main access checks.
- No account lockout/rate limiting, password recovery service, automatic updates or independent penetration test is included.
- Do not use real staff details, credentials, real serial numbers, confidential asset inventories or employer information in public demonstrations.
- The bundled tests cover selected functionality and security-sensitive paths, not every possible workflow or operating-system configuration.



