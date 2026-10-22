# Security lessons

Every security problem found in Omatable so far: in the Omarchy marketplace
review ([omacom/omarchy-plugin-marketplace#12231](https://github.com/omacom/omarchy-plugin-marketplace/issues/12231)),
by its automated baseline, or by our own audits. For each one: what went wrong, why
it matters, how it was fixed, and how to check it stays fixed.

Read this before changing code that starts a process, builds a command, writes a
file, or shows connection details. The short rules are in [`AGENTS.md`](../AGENTS.md).

---

## 1. Passwords in `docker exec` arguments

- **Found by:** marketplace maintainer, at `c050849`. Fixed in `73511b9`.
- **What:** `docker exec -e PGPASSWORD=secret …`, `-e MYSQL_PWD=…`, `-e SQLCMDPASSWORD=…`,
  `-e REDISCLI_AUTH=…`, and `mongosh -u user -p secret`.
- **Why it's bad:** process arguments are world-readable through `ps` and
  `/proc/<pid>/cmdline`, so any local user could read every database password.
- **Fix:** `secret_env()` and `_secret_flags()` pass only `-e NAME`, and `run_docker()` puts the
  value in the docker CLI's own environment. mongosh logs in inside its script from
  `process.env` (`MONGO_AUTH_JS`).
- **Check:** wrap `subprocess.run` / `Popen` in a test, run every engine, and assert that
  no container password appears in any joined argv.

## 2. Values interpolated into a shell in the terminal launcher

- **Found by:** marketplace maintainer, at `c050849`. Fixed in `73511b9`.
- **What:** `open_interactive_terminal()` built a string and ran `bash -lc "<cmd>"`, quoting
  user, password and database names with `json.dumps`.
- **Why it's bad:** JSON quoting isn't shell quoting. Inside double quotes `$(…)` and
  backticks still run, so a crafted name could execute commands.
- **Fix:** pass a fixed argv list straight to `xdg-terminal-exec`, with no shell at all.
  Credentials go through the environment. `uwsm-app` keeps that environment, which
  was verified.
- **Check:** the terminal argv contains no `bash`, `sh` or `-c` and no secret.

## 3. Redis key names spliced into `sh -c`

- **Found by:** our audit. Fixed in `73511b9`.
- **What:** fetching a key ran `sh -c` with `k=<json.dumps(key)>` in the script.
- **Why it's bad:** key names are database data that anyone with write access can set.
  A key named `$(touch /tmp/pwned)` really did run inside the container.
- **Fix:** the script is a constant, and the key arrives as `OMATABLE_KEY` in the environment
  and is used as `"$OMATABLE_KEY"`.
- **Check:** create that key, open it in Omatable, and confirm `/tmp/pwned` does not exist in
  the container.

## 4. Other values embedded in code (`eval`, JS source)

- **Found by:** our audit. Fixed in `73511b9`.
- **What:** the Redis console ran `eval "redis-cli … $REDIS_CMD"`. The Mongo scripts
  embedded database and collection names and the console query in the JS source.
- **Why it's bad:** it's the same class of bug as #2 and #3, where data can become code.
- **Fix:** no `eval`. Mongo reads names and the query from `process.env`
  (`OMATABLE_DB`, `OMATABLE_COLL`, `OMATABLE_QUERY`).

## 5. User-written query text in process arguments

- **Found by:** marketplace maintainer, at `c6b9e91`. Fixed in `24da165`.
- **What:** the query console sent the editor contents as `mysql -e`, `psql -c`,
  `sqlcmd -Q` or as `redis-cli` words.
- **Why it's bad:** queries can hold secrets, such as `ALTER USER … PASSWORD '…'` or an
  `INSERT` of a token, and they ended up readable through `/proc/<pid>/cmdline`.
- **Fix:** `run_docker(..., stdin=text)` adds `docker exec -i` and writes the text to the CLI's
  stdin. psql uses `-v ON_ERROR_STOP=1` so failures still exit non-zero, and sqlcmd
  batches end with `GO`.
- **Check:** run a query containing a marker string on every engine and assert the marker
  appears in no argv.

## 6. Database names read as a connection string by `psql`

- **Found by:** our audit, after #5. Fixed in `4c3536a`.
- **What:** `psql -d <name>`. psql treats a `-d` value containing `=` as a conninfo string.
- **Why it's bad:** database names are server data. A database named
  `dbname=coffee_roastery` really made psql connect to `coffee_roastery`, and a name
  with `host=…` would connect to another server and send the password there.
- **Fix:** `_pg_dbname()` always passes `dbname='<escaped>'`.
- **Check:** create databases named `dbname=coffee_roastery` and `o'brien`, each with a
  marker table, and confirm Omatable lists each one's own table.

## 7. Database name as mongosh's positional argument

- **Found by:** our audit. Fixed in `4c3536a`.
- **What:** the terminal ran `mongosh <dbname>`. The positional argument is a connection
  address, not just a database name.
- **Fix:** connect with no positional argument, then select the database in the script
  with `db = db.getSiblingDB(process.env.OMATABLE_DB)`.

## 8. Fixed file names in the shared `/tmp`

- **Found by:** our audit. Fixed in `4c3536a`.
- **What:** the arrow icons were written to `/tmp/omatable-chevron-<uid>.svg`.
- **Why it's bad:** another local user can create or replace a guessable file in `/tmp`
  first, either a symlink pointing at one of our files or a file whose content they
  control. Kernel protections (`fs.protected_symlinks`, `fs.protected_regular`) reduce
  this risk but shouldn't be relied on.
- **Fix:** `private_dir()` uses `$XDG_RUNTIME_DIR/omatable` (mode 0700, checked to be ours and
  not a symlink) or a fresh `mkdtemp()`. `write_private_file()` opens with `O_NOFOLLOW`
  and mode 0600. Theme colors that go into the SVG must be strict hex values.

## 9. Passwords shown on screen

- **Found by:** our audit. Fixed in `73511b9`.
- **What:** the status bar showed `connection_url`, including the password, on connect and
  after Copy URL.
- **Why it's bad:** it's visible to anyone looking at the screen, in screen shares and in
  screenshots, including the ones in this repo.
- **Fix:** messages use `display_url` (`user:•••@`). The full URL goes only to the clipboard,
  on explicit request.

## 10. `sudo` fallback for Docker

- **Found by:** marketplace security baseline (`privilege` capability). Fixed in `c050849`.
- **What:** when `docker info` failed, Omatable retried every command as `sudo -n docker`.
- **Why it's bad:** a plugin shouldn't cross a privilege boundary on its own.
- **Fix:** Omatable only uses the user's own Docker access, and `docker_error` explains in the
  status bar why Docker isn't reachable.

## 11. Changing user configuration without asking

- **Found by:** marketplace submission checklist. Fixed in `dfe4ba9`.
- **What:** `install.sh` always ran `xdg-mime default omatable.desktop` for SQLite files and
  replaced the user's existing default app.
- **Fix:** a plain install only adds Omatable to "Open with". `--default-sqlite` opts in.
  Uninstall removes only Omatable's own entries.

## 12. SQLite view auto-count with infinite recursive CTE hangs the app

- **Found by:** marketplace reviewer (HANCORE-linux), at `ba8b622`. Fixed in this commit.
- **What:** `_sqlite_list()` ran `SELECT COUNT(*)` on every table and view automatically.
  A malicious DB with a view built on an infinite recursive CTE (e.g.
  `CREATE VIEW evil AS WITH RECURSIVE r(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM r) SELECT x FROM r`)
  would make the worker run forever; `closeEvent` waited on the worker, so the app hung.
- **Why it's bad:** denial of service—opening a crafted SQLite file freezes the UI with no
  way to cancel, and closing the window doesn't help.
- **Fix:** views are no longer auto-counted; they show "?" and can be counted on demand via
  context menu. All SQLite queries now use a progress handler with a VM-step limit
  (`SQLITE_STEP_LIMIT`), which interrupts long-running queries. `closeEvent` calls
  `backend.interrupt_sqlite()` before waiting, and terminates workers that don't finish
  within 2 seconds.
- **Check:** create `evil.db` with
  `CREATE VIEW evil AS WITH RECURSIVE r(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM r) SELECT x FROM r;`
  and open it. The view must show "?", not spin, and closing the window must be instant.
  Selecting the view and running a query that reads it must fail within seconds, not hang.

## 13. FTS5 virtual table with infinite content view bypassed the progress handler

- **Found by:** marketplace reviewer (static review), at `2bf6638`. Fixed in this commit.
- **What:** `_sqlite_list()` used a raw `sqlite3.connect()` without the progress handler,
  and auto-counted virtual tables (FTS3/4/5, rtree, any module) as if they were ordinary
  tables. An FTS5 virtual table with an infinite recursive-CTE view as external content
  (e.g. `CREATE VIRTUAL TABLE f USING fts5(a, content='v', content_rowid='rowid')` where
  `v` is `CREATE VIEW v AS WITH RECURSIVE r(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM r) SELECT x AS a FROM r`)
  made `COUNT(*)` run forever because SQLite forwards non-MATCH scans to the content view.
- **Why it's bad:** same denial of service as #12, but bypassing the fix by using an
  untracked connection and exploiting virtual table content forwarding.
- **Fix:** all SQLite connections now go through `_sqlite_connect()`, which installs the
  progress handler and timeout. Virtual tables (detected by `sql` starting with
  `CREATE VIRTUAL TABLE`) are no longer auto-counted; they show "?" like views and can be
  counted on demand via context menu.
- **Check:** run `tests/test_sqlite_fts5_dos.py`. Opening/listing must return instantly,
  manual count must time out with an error, and closing must be prompt.

---

## Review checklist for new code

Ask these for every change that spawns a process, writes a file, or displays data:

1. **Arguments:** could any argv element hold a secret or user-written text? Then use the
   environment (`-e NAME` plus the value in the env) or stdin.
2. **Shell:** is a shell parsing anything built from a variable? Use an argv list instead.
   If a container script is unavoidable, keep it constant and pass data via env, quoted
   as `"$VAR"`.
3. **Untrusted data:** names from a database (databases, tables, keys, collections) are
   attacker-controlled. Could one be read as an option (`-…`), a connection string
   (`=`, `://`, `host:port`), shell syntax (`$(…)`, quotes, `;`) or code (JS/SQL)?
4. **Files:** never use a fixed name in a shared directory. Use `private_dir()` and
   `write_private_file()`.
5. **Screen:** use `display_url`, never print a password.
6. **Privilege and config:** no `sudo`/`pkexec`, and no change to user configuration
   without an explicit flag or prompt.

Regression probes worth keeping: a Redis key `$(touch /tmp/pwned)`, a Postgres database
named `dbname=<other db>`, a query `SELECT '<marker>'`, and an argv spy that searches
for passwords and the marker.
