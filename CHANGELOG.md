# Changelog

## 1.0.1 — 2026-10-20

### Security

- Database names in psql now always use quoted conninfo syntax (`dbname='…'`), preventing a malicious database name containing `=` from being parsed as a connection string.
- mongosh terminal no longer accepts a positional database argument; the database is selected from the environment inside the script.
- Icon temp files are now written to `$XDG_RUNTIME_DIR/omatable` with secure permissions (0700/0600, O_NOFOLLOW) instead of predictable paths in `/tmp`.

### Fixed

- Database loads that are already running are no longer restarted on every keystroke or finished load, eliminating redundant parallel queries that delayed the table the user wanted to open.

### Documentation

- Added a demo video to the README.
- Added `docs/security-lessons.md` documenting all security issues found during marketplace review.

## 1.0.0 — 2026-10-19

First release.

- Finds PostgreSQL, MySQL, MariaDB, SQL Server, MongoDB and Redis containers automatically, credentials included.
- Opens SQLite files from "Open with"; `install.sh --default-sqlite` makes it the default app for them.
- Database tree with a filter that searches across every database in a container, and a table overview for each database.
- Data grid with sorting, row search, cell inspector, and JSON / CSV copy.
- Query console with per-container history, row counts and timing.
- Asks for confirmation before any query that changes data.
- Container controls: start/stop, copy connection URL, and open the native CLI.
- Full keyboard navigation, with `Ctrl+P` to jump straight to any container, database or table.
- Follows the current Omarchy theme, font and corner rounding.
- Installs as an Omarchy plugin or as a standalone desktop app.
