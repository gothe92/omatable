# Changelog

## 1.0.0 — 2026-10-19

First release.

- Browse PostgreSQL, MySQL, MariaDB, Microsoft SQL Server, MongoDB and Redis containers found automatically in Docker.
- Open SQLite files directly. Omatable registers itself as the handler for `.db` / `.sqlite` / `.sqlite3` files.
- Two-pane layout: a sidebar with containers on top (name and engine version only) and an expandable database → table tree below, next to Data, Structure and Query tabs.
- The filter searches every database in the container.
- The query result line shows only the row count and time, or the error.
- Each container keeps its own query; the editor starts empty.
- Full keyboard navigation: type to jump or filter, Enter to open, Esc to go back.
- Data-changing queries (SQL, Redis and MongoDB writes) ask for confirmation and show the full query first.
- The Structure tab is hidden for MongoDB and Redis.
- Right-click menu for Start/Stop, Copy DSN / URL, Terminal Shell, Rescan Docker and Install DB.
- Omarchy design language: theme colors and accent, Hyprland-matched corner rounding, translucent outlines, smooth scrolling.
- Ships as an Omarchy plugin (lazy `overlay`, no background process) or as a plain desktop app via `install.sh`.
