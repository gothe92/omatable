# Omatable — rules for changing this code

Omatable is listed in the Omarchy plugin marketplace, and maintainers review every
commit there for security. These rules come from that review. Follow them for any
code that starts a process.

## Secrets never go in process arguments

Arguments are visible to every user on the machine through `ps`. Passwords, tokens
and connection strings that contain a password must never appear in an argv list,
whether ours, `docker`'s, or a CLI's inside the container.

- Pass credentials through the environment. For `docker exec`, give only the
  variable name (`-e PGPASSWORD`) and put the value in the docker CLI's own
  environment. `DockerDbBackend._secret_flags()` and `secret_env()` already do
  this, and `run_docker()` supplies the values. Use them.
- Never write `-e NAME=value` with a secret, or `-p <password>`, `--password=…`,
  or `mongodb://user:pass@…` as an argument.
- mongosh authenticates inside its script from `process.env`
  (`MONGO_AUTH_JS`), never with `-u/-p`.
- Never show a password on screen: use `display_url`, not `connection_url`, in
  messages. `connection_url` is only for the explicit Copy URL action.

## User-written text never goes in process arguments either

Anything the user types or pastes can hold a secret, for example
`ALTER USER … PASSWORD '…'` or an `INSERT` with a token. That covers query editor
contents, Redis commands and Mongo scripts.

- Send it to the CLI on **stdin**: `run_docker(..., stdin=text)` adds `docker exec -i`.
  MySQL/MariaDB, `psql` (with `-v ON_ERROR_STOP=1` so errors still exit non-zero),
  `redis-cli` (one command per line) and `sqlcmd` (end with `GO`) all read stdin.
- If stdin isn't possible, use an environment variable (`/proc/<pid>/environ` is
  readable only by the same user), as the Mongo console does with `OMATABLE_QUERY`.
- Never use `psql -c <query>`, `mysql -e <query>`, `sqlcmd -Q <query>`, or
  `redis-cli <words…>` for user text. `-e`/`-Q` are fine only for fixed SQL that
  Omatable itself builds and that contains no user input.

## No shell interpolation

- Start processes with an argument list, never with `bash -c` / `sh -c` built from
  values. This applies to the terminal launcher in `open_interactive_terminal()`.
- When a fixed script really needs `sh -c` inside a container, the script must be
  a constant. Pass every variable part (key names, database names, user input) as
  an environment variable and quote it in the script (`"$OMATABLE_KEY"`).
- Treat names that come from a database (tables, keys, collections, databases) as
  untrusted data. They can contain `$(…)`, quotes and `;`.
- `json.dumps()` is not shell quoting. Don't use it to build shell commands, and
  don't embed values in mongosh/JS source either; pass them via `process.env`.
- User console input for Redis is split with `shlex` and passed as arguments, not
  `eval`'d.
- SQL identifiers go through the engine's quoting helpers (backticks / double
  quotes / brackets with the closing character doubled). Values never get
  concatenated into SQL that runs unattended.

## No privilege escalation

Never call `sudo`, `pkexec` or similar. Omatable uses the user's own Docker access.
If Docker isn't reachable, report why in the status bar (`docker_error`).

## User configuration

Don't change the user's configuration without explicit consent. For example,
`install.sh` sets the default SQLite app only with `--default-sqlite`.

## Before committing

- `omarchy plugin validate .` must pass.
- Check that no secret appears in spawned argv. Wrap `subprocess.run` / `Popen` in a
  test and search the joined argv for each container's password, and for a
  marker string placed in a console query.
- Run any new process-spawning code against a key or table named
  `$(touch /tmp/pwned)` and confirm the file is not created.
- After a fix requested in the marketplace issue, reply there with the full commit
  SHA linked to the commit, plus a compare link from the previously reviewed commit.
