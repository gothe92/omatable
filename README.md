# Omatable

A database browser for [Omarchy](https://omarchy.org). Browse your Docker databases, query your data, and open SQLite files. All in one window, with your theme and keyboard shortcuts.

![Omatable browsing a PostgreSQL database](preview.png)

## Features

- **Your containers, ready to browse.** Finds supported Docker databases and reads their connection details from the containers. Works with Docker Compose and Omarchy's database containers.
- **One tree for your data.** Browse databases, tables, views, collections, and Redis keys. See table row counts and sizes before opening them.
- **Browse, inspect, copy.** Sort columns, search loaded rows, inspect JSON and long values, and copy results as JSON or CSV.
- **A query console at hand.** Run SQL, `mongosh`, or `redis-cli` commands. See results, row counts, and timing. Each container remembers its last query.
- **Confirm before writing.** Queries detected as changing data or schema ask for confirmation before running.
- **Container controls.** Start or stop containers, copy connection URLs, or open a database CLI from the sidebar.
- **SQLite included.** Open `.db`, `.sqlite`, and `.sqlite3` files from your file manager or the command line.
- **Made for the keyboard.** Press `Ctrl+P` to jump to a container, database, or table. Type to filter. Press `Enter` to open.
- **Dressed in your theme.** Uses your Omarchy colors, accent, and font, with corners that follow your Hyprland rounding.

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

### Omarchy plugin

```bash
omarchy plugin add https://github.com/gothe92/omatable --enable
```

Then bind it to a key in `~/.config/hypr/bindings.lua`:

```lua
o.bind("SUPER + ALT + SHIFT + D", "Omatable", "omarchy-shell shell summon gothe92.omatable")
```

The plugin opens Omatable through the shell. To open a SQLite file with it:

```bash
omarchy-shell shell summon gothe92.omatable '{"path": "/path/to/app.db"}'
```

Install the desktop app as well if you want the `omatable` command, a launcher entry and "Open with" for SQLite files.

### Desktop app

```bash
git clone https://github.com/gothe92/omatable
cd omatable
./install.sh
```

Launch Omatable with `SUPER + SPACE`, or choose it from "Open with" for SQLite files. To make it your default SQLite app:

```bash
./install.sh --default-sqlite
```

Requires `python-pyqt6`. Browsing containers also requires Docker access.

## Usage

With the desktop app installed:

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
omarchy plugin remove gothe92.omatable
```

Your databases and containers are left untouched.

## License

[MIT](LICENSE)
