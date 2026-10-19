# Omatable

Browse and query the databases in your Docker containers, plus any SQLite file, from one fast, keyboard-friendly window that feels at home on [Omarchy](https://omarchy.org).

![Omatable browsing a PostgreSQL database](preview.png)

## Features

- **Zero setup.** Omatable finds every PostgreSQL, MySQL, MariaDB, SQL Server, MongoDB and Redis container on your machine, including ones started with `docker compose` or `omarchy-install-docker-dbs`. It reads ports and credentials from the container itself. No connection strings to type, no database clients to install.
- **Everything in one tree.** Each container lists its databases, and each database opens to show its tables, collections or keys. Select a database to get an overview of its tables with row counts and sizes, then open one with `Enter` or a double-click. The filter searches across all of them at once.
- **A data grid that keeps up.** Sort any column, search through the loaded rows, inspect long or JSON values in a cell, and copy results as JSON or CSV.
- **Query console.** Write SQL, `mongosh` or `redis-cli` commands and see the results right away, with the row count and timing. Every container remembers its own query.
- **Safe by default.** Before a query that inserts, updates, deletes, creates or drops anything, Omatable shows it to you once more and asks for confirmation.
- **Container controls.** Right-click a container to start or stop it, copy its connection URL, or open its native CLI (`psql`, `mysql`, `sqlcmd`, `mongosh`, `redis-cli`) in a terminal.
- **SQLite files.** Open any `.db`, `.sqlite` or `.sqlite3` file in Omatable from "Open with", or make it the default so a double-click does it.
- **Keyboard first.** Press `Ctrl+P` to jump to any container, database or table by name. Type in the sidebar to filter tables, and open them with `Enter`. You never need the mouse.
- **Native to Omarchy.** Omatable uses your current theme's colors, accent and font, and matches your Hyprland corner rounding.

## Screenshots

| | |
|---|---|
| ![PostgreSQL: stars table](screenshots/postgresql.png) | ![MySQL: exoplanets table](screenshots/mysql.png) |
| ![SQL Server: query console](screenshots/mssql.png) | ![MongoDB: missions collection](screenshots/mongodb.png) |
| ![SQLite: table structure](screenshots/sqlite.png) | |

## Supported databases

| Engine | Browse | Query with | CLI |
|---|---|---|---|
| PostgreSQL | databases, tables, views | SQL | `psql` |
| MySQL / MariaDB | databases, tables | SQL | `mysql` / `mariadb` |
| Microsoft SQL Server | databases, tables | T-SQL | `sqlcmd` |
| MongoDB | databases, collections | `mongosh` | `mongosh` |
| Redis | databases 0–5, keys with type and TTL | `redis-cli` commands | `redis-cli` |
| SQLite (files) | tables, views | SQL | `sqlite3` |

## Install

**As an Omarchy plugin:**

```bash
omarchy plugin add https://github.com/gothe92/omatable --enable
```

Then bind it to a key in `~/.config/hypr/bindings.lua`:

```lua
o.bind("SUPER + ALT + SHIFT + D", "Omatable", "omarchy-shell shell summon andras.omatable")
```

**As a desktop app:**

```bash
git clone https://github.com/gothe92/omatable && cd omatable && ./install.sh
```

This adds Omatable to the app launcher (`SUPER + SPACE`) and to "Open with" for SQLite files. To also make it the default app for SQLite files:

```bash
./install.sh --default-sqlite
```

Omatable needs `python-pyqt6`. For containers it also needs `docker`, and your user must be able to run it.

## Usage

```bash
omatable                    # browse your Docker databases
omatable my-postgres        # start with a specific container selected
omatable path/to/app.db     # open a SQLite file
```

Each launch opens a new window, and Omatable stops running when you close it.

### Keyboard

| Key | Action |
|---|---|
| `Ctrl+P` | Go to a container, database or table |
| Type a name | Jump to a container, or filter tables |
| `Enter` / `→` | Open the selected container, database or table |
| `Esc` / `←` | Clear the filter or go back one level |
| `Ctrl+Enter` / `F5` | Run the query |
| `Ctrl+F` | Focus the filter |
| `/` | Search inside the loaded rows |
| `Alt+1` / `Alt+2` / `Alt+3` | Data / Structure / Query tab |
| `Ctrl+R` | Rescan Docker, or reload the SQLite file |
| `Ctrl+T` | Open the database CLI in a terminal |
| `Ctrl+Shift+C` | Copy the connection URL |
| `Ctrl+Q` | Close the window |

## Uninstall

```bash
./install.sh --uninstall
omarchy plugin remove andras.omatable
```

Uninstalling removes only Omatable itself. Your databases and containers stay exactly as they are.

## License

[MIT](LICENSE)
