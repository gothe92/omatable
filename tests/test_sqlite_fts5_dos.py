#!/usr/bin/env python3
"""
Regression test for security issue #13: FTS5 virtual table with infinite content view.

A hostile SQLite database with an FTS5 virtual table using an infinite recursive-CTE
view as external content must not hang the app:
  - Listing must return instantly (virtual tables show "?" without counting)
  - Manual count must time out with an error (not run forever)
  - Closing must be prompt

This test extracts and exercises only the backend SQLite code, without GUI dependencies.
"""

import os
import re
import sqlite3
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
omatable_path = os.path.join(script_dir, "omatable")


@dataclass
class DockerDbContainer:
    """Minimal container info for SQLite testing."""
    container_id: str
    name: str
    image: str
    engine: str
    running: bool
    status_text: str
    default_db: str
    user: str = ""
    password: str = ""
    host: str = ""
    port: int = 0


class DockerDbBackend:
    """Extracted SQLite backend code for testing (no GUI dependencies)."""

    SQLITE_STEP_LIMIT = 50_000
    SQLITE_TIMEOUT = 5.0

    def __init__(self):
        self._sqlite_conns: List[sqlite3.Connection] = []
        self._sqlite_interrupted = False
        self._sqlite_query_start: float = 0.0

    @staticmethod
    def sqlite_file(path: str) -> DockerDbContainer:
        path = os.path.abspath(path)
        return DockerDbContainer(
            container_id="", name=os.path.basename(path), image="", engine="sqlite",
            running=True, status_text="File", default_db=path,
        )

    @staticmethod
    def _sqlite_cell(v: Any) -> str:
        if v is None:
            return "NULL"
        if isinstance(v, bytes):
            return f"<BLOB {len(v)} bytes>"
        return str(v)

    @staticmethod
    def _sqlite_ident(name: str) -> str:
        return '"' + name.replace('"', '""') + '"'

    def interrupt_sqlite(self):
        """Interrupt all tracked SQLite connections."""
        self._sqlite_interrupted = True
        for conn in list(self._sqlite_conns):
            try:
                conn.interrupt()
            except Exception:
                pass

    def _sqlite_progress_handler(self) -> int:
        """Progress callback: return non-zero to abort the query."""
        if self._sqlite_interrupted:
            return 1
        if self._sqlite_query_start and (time.monotonic() - self._sqlite_query_start) > self.SQLITE_TIMEOUT:
            return 1
        return 0

    def _sqlite_connect(self, path: str) -> sqlite3.Connection:
        """Open a tracked, interruptible SQLite connection with timeout."""
        self._sqlite_query_start = time.monotonic()
        conn = sqlite3.connect(path)
        conn.set_progress_handler(self._sqlite_progress_handler, self.SQLITE_STEP_LIMIT)
        self._sqlite_conns.append(conn)
        return conn

    def _sqlite_close(self, conn: sqlite3.Connection):
        """Close and untrack a SQLite connection."""
        try:
            self._sqlite_conns.remove(conn)
        except ValueError:
            pass
        try:
            conn.close()
        except Exception:
            pass

    def _sqlite_list(self, c: DockerDbContainer) -> Tuple[str, List[str], List[Dict[str, str]], str]:
        self._sqlite_interrupted = False
        conn = self._sqlite_connect(c.default_db)
        try:
            objs = conn.execute(
                "SELECT name, type, sql FROM sqlite_master WHERE type IN ('table', 'view') "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
            items = []
            for name, kind, sql in objs:
                is_virtual = kind == "table" and sql and sql.upper().startswith("CREATE VIRTUAL TABLE")
                if kind == "view" or is_virtual:
                    extra = "view" if kind == "view" else "virtual"
                    items.append({"name": name, "count": "? rows", "extra": extra})
                else:
                    try:
                        n = conn.execute(f"SELECT COUNT(*) FROM {self._sqlite_ident(name)}").fetchone()[0]
                    except sqlite3.OperationalError as e:
                        if "interrupt" in str(e).lower():
                            return (c.name, [c.name], [], "Query interrupted (too slow or app closing)")
                        n = "?"
                    except sqlite3.Error:
                        n = "?"
                    items.append({"name": name, "count": f"{n} rows", "extra": kind})
        except sqlite3.OperationalError as e:
            if "interrupt" in str(e).lower():
                return (c.name, [c.name], [], "Query interrupted (too slow or app closing)")
            return (c.name, [c.name], [], f"SQLite error: {e}")
        except sqlite3.Error as e:
            return (c.name, [c.name], [], f"SQLite error: {e}")
        finally:
            self._sqlite_close(conn)
        n_tables = sum(1 for it in items if it.get("extra") == "table")
        n_views = sum(1 for it in items if it.get("extra") == "view")
        n_virtual = sum(1 for it in items if it.get("extra") == "virtual")
        parts = []
        if n_tables:
            parts.append(f"{n_tables} tables")
        if n_virtual:
            parts.append(f"{n_virtual} virtual")
        if n_views:
            parts.append(f"{n_views} views")
        summary = ", ".join(parts) + f" in `{c.name}`" if parts else f"Empty database `{c.name}`"
        return (c.name, [c.name], items, summary)

    def sqlite_count_item(self, c: DockerDbContainer, name: str) -> Tuple[Optional[int], str]:
        """Count rows of a single table/view with interruption and timeout.
        Returns (count, error_message). count is None on error."""
        self._sqlite_interrupted = False
        conn = self._sqlite_connect(c.default_db)
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {self._sqlite_ident(name)}")
            row = cur.fetchone()
            return (row[0] if row else 0, "")
        except sqlite3.OperationalError as e:
            if "interrupt" in str(e).lower():
                return (None, "Query interrupted (too slow or app closing)")
            return (None, str(e))
        except sqlite3.Error as e:
            return (None, str(e))
        finally:
            self._sqlite_close(conn)

    def list_databases_and_items(
        self, c: DockerDbContainer, selected_db: str = ""
    ) -> Tuple[str, List[str], List[Dict[str, str]], str]:
        """Returns (active_db, databases_list, items_list[{name, count, extra}], summary_text)"""
        if c.engine == "sqlite":
            return self._sqlite_list(c)
        return ("", [], [], "Unsupported engine")


def create_hostile_db(path: str):
    """Create a SQLite DB with an FTS5 virtual table backed by an infinite view."""
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE VIEW v AS "
        "WITH RECURSIVE r(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM r) "
        "SELECT x AS a FROM r"
    )
    conn.execute(
        "CREATE VIRTUAL TABLE f USING fts5(a, content='v', content_rowid='rowid')"
    )
    conn.execute("CREATE TABLE normal_table (id INTEGER PRIMARY KEY, data TEXT)")
    conn.execute("INSERT INTO normal_table VALUES (1, 'test')")
    conn.commit()
    conn.close()


def test_listing_fast():
    """Opening/listing must return instantly, not hang on virtual table count.
    
    The key security property is that listing a DB with a hostile virtual table
    completes quickly, without scanning the infinite content view.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        create_hostile_db(db_path)
        backend = DockerDbBackend()
        container = backend.sqlite_file(db_path)

        t0 = time.monotonic()
        active_db, dbs, items, summary = backend.list_databases_and_items(container)
        elapsed = time.monotonic() - t0

        assert elapsed < 2.0, f"Listing took {elapsed:.2f}s, expected < 2s"

        view_item = next((it for it in items if it["name"] == "v"), None)
        assert view_item is not None, "View 'v' not found in listing"
        assert view_item["count"] == "? rows", f"View should show '? rows', got {view_item['count']}"
        assert view_item["extra"] == "view", f"View extra should be 'view', got {view_item['extra']}"

        fts_item = next((it for it in items if it["name"] == "f"), None)
        assert fts_item is not None, "FTS5 table 'f' not found in listing"
        assert fts_item["count"] == "? rows", f"FTS5 table should show '? rows', got {fts_item['count']}"
        assert fts_item["extra"] == "virtual", f"FTS5 extra should be 'virtual', got {fts_item['extra']}"

        normal_item = next((it for it in items if it["name"] == "normal_table"), None)
        assert normal_item is not None, "normal_table not found in listing"
        assert "1 rows" == normal_item["count"], f"normal_table should show '1 rows', got {normal_item['count']}"
        assert normal_item["extra"] == "table", f"normal_table extra should be 'table', got {normal_item['extra']}"

        print(f"  Listing completed in {elapsed:.3f}s")
        print(f"  View 'v': {view_item}")
        print(f"  FTS5 'f': {fts_item}")
        print(f"  normal_table: {normal_item}")
        print(f"  Summary: {summary}")
        print("PASS: test_listing_fast")

    finally:
        os.unlink(db_path)


def test_manual_count_fts5():
    """Manual count of FTS5 table must complete quickly (not scan content view).
    
    FTS5 COUNT(*) returns 0 because the table is empty (no FTS index entries).
    The key security property is that it doesn't hang by scanning the content view.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        create_hostile_db(db_path)
        backend = DockerDbBackend()
        container = backend.sqlite_file(db_path)

        t0 = time.monotonic()
        count, err = backend.sqlite_count_item(container, "f")
        elapsed = time.monotonic() - t0

        assert elapsed < 2.0, f"FTS5 count took {elapsed:.2f}s, should complete quickly without scanning content"

        if err:
            print(f"  FTS5 count returned error in {elapsed:.3f}s: {err}")
        else:
            print(f"  FTS5 count returned {count} in {elapsed:.3f}s (didn't scan content)")
        print("PASS: test_manual_count_fts5")

    finally:
        os.unlink(db_path)


def test_view_count_timeout():
    """Manual count of infinite view must also time out."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        create_hostile_db(db_path)
        backend = DockerDbBackend()
        container = backend.sqlite_file(db_path)

        t0 = time.monotonic()
        count, err = backend.sqlite_count_item(container, "v")
        elapsed = time.monotonic() - t0

        timeout_limit = backend.SQLITE_TIMEOUT + 2.0
        assert elapsed < timeout_limit, f"Count took {elapsed:.2f}s, expected < {timeout_limit}s (should timeout)"

        assert count is None, f"Count should be None on timeout, got {count}"
        assert "interrupt" in err.lower() or "too slow" in err.lower(), \
            f"Error should mention interrupt/timeout, got: {err}"

        print(f"  View count timed out in {elapsed:.3f}s with error: {err}")
        print("PASS: test_view_count_timeout")

    finally:
        os.unlink(db_path)


def test_summary_format():
    """Summary should correctly distinguish tables, virtual tables, and views.
    
    FTS5 creates internal shadow tables (f_content, f_data, f_config, f_docsize, f_idx)
    which are ordinary tables. The summary should show:
    - Our normal_table + FTS5 shadow tables as "tables"
    - The FTS5 table 'f' as "virtual"
    - The view 'v' as "view"
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        create_hostile_db(db_path)
        backend = DockerDbBackend()
        container = backend.sqlite_file(db_path)

        active_db, dbs, items, summary = backend.list_databases_and_items(container)

        assert "tables" in summary, f"Summary should mention tables, got: {summary}"
        assert "1 virtual" in summary, f"Summary should mention '1 virtual', got: {summary}"
        assert "1 views" in summary, f"Summary should mention '1 views', got: {summary}"

        virtuals = [it for it in items if it.get("extra") == "virtual"]
        views = [it for it in items if it.get("extra") == "view"]
        tables = [it for it in items if it.get("extra") == "table"]

        assert len(virtuals) == 1, f"Should have 1 virtual table, got {len(virtuals)}"
        assert virtuals[0]["name"] == "f", f"Virtual table should be 'f', got {virtuals[0]['name']}"
        assert len(views) == 1, f"Should have 1 view, got {len(views)}"
        assert views[0]["name"] == "v", f"View should be 'v', got {views[0]['name']}"
        assert "normal_table" in [t["name"] for t in tables], "normal_table should be in tables"

        print(f"  Summary: {summary}")
        print(f"  Virtual tables: {[v['name'] for v in virtuals]}")
        print(f"  Views: {[v['name'] for v in views]}")
        print(f"  Tables: {[t['name'] for t in tables]}")
        print("PASS: test_summary_format")

    finally:
        os.unlink(db_path)


def test_no_untracked_connections():
    """Verify all SQLite connections go through the tracked helper."""
    import re

    omatable_src_path = os.path.join(script_dir, "omatable")
    with open(omatable_src_path, "r") as f:
        source = f.read()

    pattern = r"sqlite3\.connect\("
    matches = list(re.finditer(pattern, source))

    for m in matches:
        start = source.rfind("\n", 0, m.start()) + 1
        end = source.find("\n", m.end())
        line = source[start:end].strip()
        context_start = max(0, source.rfind("def ", 0, m.start()))
        context_end = source.find("(", context_start)
        func_name = source[context_start:context_end]

        if "_sqlite_connect" not in func_name:
            print(f"  WARNING: Found sqlite3.connect outside _sqlite_connect: {line}")
            print(f"           in function: {func_name}")
            assert False, f"Untracked sqlite3.connect found in {func_name}"

    print(f"  Found {len(matches)} sqlite3.connect call(s), all in _sqlite_connect")
    print("PASS: test_no_untracked_connections")


if __name__ == "__main__":
    print("=" * 60)
    print("SQLite FTS5 DoS Regression Tests")
    print("=" * 60)
    print()

    tests = [
        ("Listing performance", test_listing_fast),
        ("FTS5 count (no hang)", test_manual_count_fts5),
        ("View count timeout", test_view_count_timeout),
        ("Summary format", test_summary_format),
        ("No untracked connections", test_no_untracked_connections),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
